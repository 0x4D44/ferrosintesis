# MM-REQ-KILN-00025 — GM 109 bagpipe chanter zones must cover the FreePats bank

- **State:** Draft
- **Priority:** Should
- **Area:** sampler / samples pipeline
- **Raised:** 2026-07-20
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5)

## Statement

The GM 109 bagpipe chanter zone table must bake the usable takes the pinned
FreePats archive actually holds — filling the ~2.5-semitone gaps (A#4, B4, C#5,
D#5, E5, F5, F#5) and adding a second round-robin from the `_32` takes — so
repitch stretch in the chanter register stays small.

## Notes

- Tracked in scratchpad (2026-07-20): the archive holds 26 WAVs (24 chanter + 2
  drones) but `BAGPIPE_SOURCES` bakes only 8
  (`tools/ferrosintesis-samples/prepare.py`, grep `BAGPIPE_SOURCES`; zone table in
  `crates/ferrosintesis/src/sampler.rs`, grep chanter).
- Cheap now: `prepare.py:find_loop` (post the 2026-07-20 wrap-error-scored rework,
  commit d851869) can cut a clean short loop from any steady take.
- Mind the lessons_learnt traps: 24-bit source WAVs (`sw==3`), wrap_error_db
  scoring not value+slope, short loop windows.
- Oracle: the existing `looped_sustain_banks_are_loopable` sweep covers new zones
  automatically; extend the zone-coverage/pitch-integrity assertions to the new
  roots.
- Builds on MM-REQ-KILN-00017 (Implemented — bagpipe as a sampled voice).
