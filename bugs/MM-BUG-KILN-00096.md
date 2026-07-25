# MM-BUG-KILN-00096 — MIDI parser desyncs on running status after a meta or SysEx event

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** midi
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised via `deltic bugs new` by Claude Opus 5 (1M) @ xhigh
  — found while auditing an abandoned 2026-07-17 branch, `task/20260717-FIX-CDX-fix-smf-running-status-across-meta-event`,
  whose fix never integrated; the defect was still live on trunk `715f8a3`)
  → Fixed (2026-07-25, Claude Opus 5 (1M) @ xhigh; running status latched from channel-voice
  status bytes only; three regressions added; awaiting two-eyes verification)

## Observation

`crates/ferrosintesis/src/midi.rs:parse()` kept ONE `status` variable for both the
running status and the current event's status byte:

```rust
let mut status: u8 = 0;
if c.peek()? >= 0x80 { status = c.u8()?; }
match status { 0xFF => …meta…, 0xF0 | 0xF7 => …sysex…, _ => …channel voice… }
```

A meta event therefore latched `0xFF` (and a SysEx `0xF0`/`0xF7`) as the running
status. The next event that omitted its status byte — legal running status — re-entered
the meta/SysEx arm, where its two data bytes were consumed as a meta `kind` + `len`
pair and `len` further bytes were swallowed. From there the track is desynced: the
parser walks off into event payloads and typically dies with `UnexpectedEof`, or, worse,
silently resynchronises and yields wrong notes.

**Expected:** running status carries the last CHANNEL VOICE status (`0x80..=0xEF`)
across the interleaved meta/SysEx event.
**Actual:** `UnexpectedEof`, or a silently corrupted event stream.

Repro (now the committed regression `running_status_survives_meta_event`), a format-0
track:

```
00 B6 0A 4B          explicit CC10=75 on channel 6
00 FF 59 02 00 00    key-signature meta
00 40 7F             CC64=127 through the preceding running status
```

Pre-fix this returns `Err(UnexpectedEof)`; it should yield two `Cc` events.

**Classification.** SMF 1.0 says meta and SysEx events cancel running status, so a file
that continues it is strictly malformed — but real sequencers emit them, and
ferrosintesis bills itself in `CLAUDE.md` as "a GENERIC GM player … a faithful player of
**any** GM file". Tolerating the file beats desyncing on it; either way, the pre-fix
silent corruption was not a defensible reading of the spec.

**Blast radius: foreign MIDI files only.** All 141 committed `.mid` files under
`albums/`, `demos/` and `test-corpus/` were scanned with an independent Python SMF
walker: **zero** contain a running-status event following a meta or SysEx event, so no
album's parse — and therefore no render — changes. That is the confinement evidence in
place of a render-diff (this is a parser change, not a `voices.rs`/`engine.rs` change).

## Fix

Split the two roles the single variable was serving. `running_status` now latches only
when the explicit byte is channel-voice (`0x80..=0xEF`); a system byte is used for its
own event and never latched:

```rust
let mut running_status: u8 = 0;
let status = if c.peek()? >= 0x80 {
    let explicit = c.u8()?;
    if (0x80..=0xEF).contains(&explicit) { running_status = explicit; }
    explicit
} else {
    running_status
};
```

A track that opens with a data byte still leaves the latch at `0`, which falls to the
catch-all arm and errors cleanly as `BadStatusByte { status: 0 }` — an error, never a
misparse.

### Verification

- **Red before green.** All three new regressions fail on pre-fix trunk with exactly the
  predicted desync (`UnexpectedEof`), and pass after:
  - `running_status_survives_meta_event` — the repro above;
  - `running_status_survives_sysex_event` — same guarantee across a GS SysEx, which the
    2026-07-17 branch did not cover (its `0xF0` arm reads its own length, so a latched
    `0xF0` swallows an arbitrary run of the track);
  - `system_status_never_becomes_the_running_status` — a data byte with no channel
    status ever latched must be `BadStatusByte { status: 0 }`, not a meta misparse.
- All 11 pre-existing `midi::tests` still green (14/14), so no parse behaviour moved for
  well-formed files.
- Confinement scan: 141/141 committed MIDIs unaffected (above).

## Notes

- The abandoned branch `task/20260717-FIX-CDX-fix-smf-running-status-across-meta-event`
  (Codex, 2026-07-17) reached the same core fix and was never integrated — it sat 494
  commits behind. Its commit message cites "MM-BUG-KILN-00005", a pre-conversion ID that
  now belongs to the viola-bank bug; the defect was untracked until this record. That
  branch can be reaped.
- Deliberately NOT a `Debug` derive on `Song`: the third regression matches on the
  `Result` instead, so the public API is unchanged.
