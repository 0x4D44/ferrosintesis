# MM-BUG-KILN-00056 — Six album MIDI writers lack the _resolve_overlaps() write-time clamp: 10,398 same-pitch overlaps are committed (8,426 in Riverwake), ambiguous on kill-newest GM synths

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** albums
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass; scope corrected from the original "Hollow Hill only / if regenerated" to the measured 6-writer, committed-today reality) → Fixed (2026-07-25, Codex GPT-5.6-Sol; back-ported positional overlap clamps to all six lagging writer lineages, regenerated their committed MIDI, and added a catalog-wide serialized-MIDI oracle)

## Observation

**Symptom.** Six album MIDI writers lack the `_resolve_overlaps()` write-time clamp that the
other sixteen have, so their **committed** `.mid` files contain same-pitch overlapping notes.
ferrosintesis renders them correctly (it matches note-offs oldest-first), but a conforming
kill-newest GM synth would chop the re-strike, making the committed source — the repo's
declared source of truth per `CLAUDE.md` — ambiguous on a foreign player.

**Measured (read-only stdlib SMF scan of every committed album `.mid`).** The published
10,398 count covers every channel: 10,030 pitched-channel overlaps plus 368 channel-10
percussion overlaps. By writer lineage that lacks the clamp:

| Writer | Committed overlaps |
|---|---|
| `albums/opus4-8/amarok/midi/Riverwake.mid` | **8,426** (~1 note in 8 of its 64,199) |
| `albums/gpt5-3-spark/engine.py` (12 files) | 538 |
| `albums/gpt5-5/Hours After Rain/engine.py` (12 files) | 386 |
| `albums/fable5/Hollow Hill/engine.py` (2 files) | 580 |
| `albums/opus4-8/engine.py` (10 files) | 220 |
| `albums/gpt5-5/The Long Turning/engine.py` | 203 |
| `albums/fable5/the_iron_tide.py` (standalone) | 45 |
| **Total** | **10,398** |

**Decisive cross-check.** All 16 writers that *have* the clamp report exactly 0 overlaps and
0 imbalanced pitches; the nonzero set is *exactly* the 6 that lack it. Clamp presence fully
predicts committed-MIDI cleanliness.

**The clamp, and how it's wired (present writer):** `albums/fable5/The Signal Fire/engine.py:212`
defines `_resolve_overlaps()` and calls it as the first statement of `write()` (`:241-242`);
gpt5-6 engines wire the same into `to_bytes()`. It clamps each earlier note-off back to the
next note-on on the same (channel, pitch). **Absent writer:** `albums/fable5/Hollow Hill/engine.py:203`
`write()` has no such call anywhere in the file.

**Why it renders fine locally:** `crates/ferrosintesis/src/engine.rs:2652` matches note-offs
with `.find()` over the push-ordered `active` list (oldest-first, `engine.rs:2253`), so the
re-strike keeps its full length here; a kill-newest synth retires the newer voice instead.

**Expected.** Every committed album `.mid` is unambiguous on a conforming GM player.

**Reproduce.** Positional-pairing scan (k-th sorted note-on ↔ k-th sorted note-off per
track/channel/pitch) over `albums/**/*.mid`; the 16-zero / 6-nonzero split reproduces exactly.

## Fix

Back-ported the existing positional-pair clamp to all six stale writer lineages:

- `albums/fable5/Hollow Hill/engine.py`
- `albums/fable5/the_iron_tide.py`
- `albums/gpt5-3-spark/engine.py`
- `albums/gpt5-5/Hours After Rain/engine.py`
- `albums/gpt5-5/The Long Turning/engine.py`
- `albums/opus4-8/engine.py` (shared by Vigil and Riverwake)

Each writer now sorts note-ons and note-offs independently per `(channel, pitch)`, pairs
them positionally, and moves an earlier note-off to the next note-on when they overlap.
Unbalanced pitches remain untouched instead of manufacturing false pairs. Equal-tick
note-offs retain lower sort priority than their re-strike.

Regenerated all 41 outputs owned by those writers. Thirty-nine committed MIDI files changed;
the two already-clean Vigil files remained byte-identical. The catalog-wide regression oracle
in `crates/render-catalog/tests/album_midi_overlaps.rs` parses every committed album SMF,
including running status, and hard-fails on a positional-pair overlap. It reproduces the
10,398 pre-fix count and reports zero after regeneration.

All four album verifiers pass, the Vigil builder validates all 12 tracks, and the new global
oracle passes. A bounded 11.025 kHz pre/post render inventory covered all 39 changed MIDI
sources: 38 changed audibly. `albums/opus4-8/midi/07 - Snow.mid` is byte-changed but renders
identically because its sole repaired overlap is a percussion note-off, which ferrosintesis
does not voice. Every unchanged album MIDI is byte-identical, so no unrelated source can
contaminate this MIDI-only fix.

## Notes

- **Do not frame this as a Hollow Hill bug** (the original claim did). Hollow Hill is 580 of
  10,398 (5.6%); **Riverwake alone is 81%**. If exactly one file is fixed, it is Riverwake.
- **Root cause is fork drift, not a per-album mistake.** `_resolve_overlaps()` landed
  2026-07-06 (commit `6f499a2`); each album owns a locally-copied `engine.py`, so it
  propagated only to lineages copied/touched after that date. The six laggards are the
  pre-`6f499a2` forks.
- **Include the standalone `albums/fable5/the_iron_tide.py`** — its own `Score` class, missed
  by any grep restricted to `engine.py`.
- **Back-porting the clamp CHANGES the ferrosintesis render (measured).** With oldest-first
  matching an overlapping pair, the old file sounds its full
  intended length; clamping truncates the earlier note back to the later note-on — up to
  7,683 ticks (16 beats) in Hollow Hill's worst case, across ~8,000 notes in Riverwake.
  The completed inventory found audible changes in 38 of 39 changed files; the only
  audio-identical file changed a percussion note-off.
- **The clamp is not a total fix:** it cannot repair two note-ons at an identical tick
  (clamping yields a zero-length note). Several already-clamped albums carry a handful (Tuxedo
  Noir: 14). Don't claim it guarantees a fully unambiguous file.
- **Regression guard:** `albums/opus4-8/engine.py:463` (`analyze()`) already *detected*
  same-pitch overlaps and prints them (`:506-507`) as a non-gating advisory — it has been
  reporting this defect to anyone who ran it. The new catalog-wide hard oracle uses positional
  pairing per (track, channel, pitch), not a sequential pending-note queue: a queue manufactures
  phantom overlaps from a single unbalanced note (369 false positives in Sub Rosa during this
  investigation; Sub Rosa is actually clean).
- **Not a duplicate of `MM-BUG-KILN-00027`** (that is the `--solo 8` Hollow Hill *render-hang*,
  a synth-path perf defect, unrelated to the Python engine).
