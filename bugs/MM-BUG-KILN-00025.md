# MM-BUG-KILN-00025 — Renderer panics (index out of bounds) on a MIDI note key ≥ 128; the parser never clamps the note-key data byte

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** midi
- **Raised:** 2026-07-18
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 via overnight code-review pass, deep-review workflow)

## Observation

Rendering a Standard MIDI File whose NoteOn/NoteOff/PolyAftertouch **key data byte
is ≥ 128** panics the public `ferrosintesis::offline::render` path with an
index-out-of-bounds, aborting the process. The crate documents itself as a faithful
player that "plays any GM file" and is published to crates.io, so processing
arbitrary/untrusted MIDI is the intended use — a library consumer or the CLI aborts
on a crafted or merely corrupt file. This is an availability-only defect (a safe Rust
bounds-check panic — no memory unsafety, no UB, no RCE).

**Root cause — the parser masks the channel nibble but not the key.** The SMF reader
reads note-key data bytes raw, with no clamp to the valid 0–127 range:

- `crates/ferrosintesis/src/midi.rs:243` — `let key = c.u8()?;` (NoteOn 0x90)
- `crates/ferrosintesis/src/midi.rs:237` — NoteOff (0x80)
- `crates/ferrosintesis/src/midi.rs:275` — PolyAftertouch (0xA0)

The channel, by contrast, is deliberately masked (`let ch = status & 0x0F;`,
midi.rs:233), with an explicit "can never produce an out-of-range channel" comment at
midi.rs:60-63. The event loop only tests the high bit at *event start*
(midi.rs:174) to detect a status byte; data bytes inside an event are read
unconditionally, so `90 C8 64` parses literally as `NoteOn { ch: 0, key: 200, vel: 100 }`.

**Blast radius — two fixed 128-wide arrays indexed by the raw key** in
`crates/ferrosintesis/src/engine.rs`, both reached from the public render loop
(`offline::render` → `EngineCore::render*` → `handle_event` (engine.rs:1394) →
`note_on` (engine.rs:1434)):

- `key_on_at: Vec<[u64; 128]>` (declared engine.rs:1175) — indexed
  `self.key_on_at[ci][key as usize]` at **engine.rs:1445-1446** for any melodic
  channel (`ch != 9`).
- `drum_rr: [u8; 128]` (declared engine.rs:1168) — indexed `drum_rr[key as usize]`
  at **engine.rs:1548** for channel 10 / GS/XG drum-declared channels.

Index 200 into a length-128 array panics in both.

- **Expected:** a malformed key is clamped or the file rejected with a `MidiError`;
  no panic on any byte stream.
- **Actual:** `index out of bounds: the len is 128 but the index is 200`, process
  aborts (exit 101).

**Reproduced by execution** (deep-review security lens, three-skeptic panel, 3/3
confirmed): a ~30-byte format-0 file with one NoteOn (ch 0, key 200, vel 100) fed
through the shipping `ferrosintesis` binary panics at the `key_on_at` index site.
Independently re-confirmed for this report by reading the parser (unmasked `c.u8()`)
and the two engine index sites.

The parser already guards sibling untrusted-input DoS vectors — `MAX_SONG_SECONDS`
(midi.rs:324-329), and the format/time-division validation (midi.rs:149-154) — so the
missing key clamp is an oversight in an otherwise security-conscious trust boundary,
not a deliberate omission.

## Fix

Clamp at the trust boundary, mirroring the existing channel-nibble masking. Mask the
note-key data byte to 7 bits (`key & 0x7F`) where it is read in `midi.rs`: NoteOn
(~line 243), NoteOff (~line 237), and PolyAftertouch (~line 275). Masking there fixes
**both** engine crash sites at once and keeps every array index in range, with no
change needed downstream.

- Velocity, CC number, and program data bytes are also read raw but are never used as
  array indices (`cc`/`program_change` use `match`/comparison only), so they need no
  change — verify this holds before narrowing the fix.
- Decide clamp-vs-reject: masking (`& 0x7F`) keeps a corrupt file playable (folds
  key 200 → 72); returning `MidiError::UnexpectedEof`/a new variant is stricter.
  Masking matches the existing channel-nibble precedent and the "plays any GM file"
  contract; prefer it unless a stricter policy is wanted.

**Regression test (write first, must fail on trunk):** parse + `render` a file whose
NoteOn key byte is ≥ 128 (e.g. 200) on both a melodic channel and channel 10, and
assert no panic (and, for masking, that the note sounds at `key & 0x7F`).

## Notes

- Found by the overnight code-review pass (`crates/ferrosintesis/` area) via the
  `deep-review` workflow; see `wrk_docs/2026.07.18 - CR - overnight review pass
  (ferrosintesis core).md`.
- The three verify skeptics unanimously corrected the severity from the finder's
  "High" to **Medium**: availability-only, local offline vector, one-line fix,
  caller-mitigable with `catch_unwind`. Kept above Low because of the published
  "plays any GM file" contract and that the parser already guards sibling vectors.
