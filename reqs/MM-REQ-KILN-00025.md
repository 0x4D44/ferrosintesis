# MM-REQ-KILN-00025 — GM 109 bagpipe chanter zones must cover the FreePats bank

- **State:** Satisfied
- **Priority:** Should
- **Area:** sampler / samples pipeline
- **Raised:** 2026-07-20
- **Implemented-by:** integrated 32eb8aa+27db13d (branch task/20260721-DEV-HUM-bagpipe-zones-rr2-loop-drift; sampler.rs chanter()/chanter_rr2() + prepare.py BAGPIPE_SOURCES + -orchestral 157→166 files)
- **Satisfied-by:** sampler::tests::bagpipe_chanter_zone_coverage, sampler::tests::bagpipe_chanter_rr2_and_drift_decorrelate, sampler::tests::looped_sustain_banks_are_loopable
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
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Implemented (2026-07-21, integrated 32eb8aa; render-diff 124 unchanged) → Satisfied (2026-07-25, verified)

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

### Outcome note (2026-07-21)

Filled to **10 of 13** pitches + a 5-take RR2 bank — every take that meets the
−14 dB wrap gate. **D#5, E5 and F5 are UNLOOPABLE in BOTH takes** (best wrap
−12.6 / −5.3 / +1.3 dB for `_31`; −10.4 / −6.2 / −13.0 for `_32`): the takes
carry internal level/timbre drift no window inside `BAGPIPE_LOOP_S` dodges.
Kept out rather than weakening the gate; do not re-hunt without a better
source. Worst remaining gap D5→F#5 (~1.9-semitone max repitch, down from ~2.5).
