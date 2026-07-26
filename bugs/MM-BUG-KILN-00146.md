# MM-BUG-KILN-00146 — GM42 cello keys 74/76 lock an octave up at high bow force, and the wolf gate's seeds could not see it

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** voices / BowedString
- **Raised:** 2026-07-26
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260726T233602Z-p9812-n603751900-c22
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00146-run-fix-20260726T233602Z-p9812-n603751900-c22
- **Owner base:** 69aa1d4b5574466d07590ad9fba538dbdf5e7493
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T23:36:02Z
- **Owner until:** 2026-07-27T00:21:02Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high)

## Observation

Two coupled defects, both pre-existing, both fixed on the branch below but NOT independently verified — raised so the two-eyes rule applies rather than self-closing them.

**1. The defect.** `BowedString` GM 42 (cello) loses its fundamental at keys 74 (D5) and 76 (E5) whenever the per-note bow force draws near the top of its range, locking an octave up at +1203 cents with the level down ~60%. Bow force is drawn per note from 2.2-2.9, so this hits roughly one note in eight at those pitches — the top two tones of the cello's range.

Root cause: bowing hard in a SHORT loop drives the waveguide off its fundamental. Same failure family as the known 46-50 wolf band (MM-BUG-KILN-00012), at the other end of the register.

**2. Why nobody saw it.** `bowed_string_wolf_band_holds_fundamental` asserts that 'every per-note seed must settle onto the requested fundamental', using seeds 7/17/23. All three are small, and `Rng::new` (crates/ferrosintesis/src/dsp.rs) seeds xorshift32 raw — its first output from a small seed is ~= -1.0, so `u = white()*0.5+0.5` ~= 0.0 and bow force collapses onto 2.2003..2.2010 out of 2.2-2.9. The gate tested ONE bow force three times, on the single axis this waveguide fails on.

The engine is unaffected: it hands out `0xBA60 ^ (index * 2654435761)` (crates/ferrosintesis/src/engine.rs:2207), a Knuth hash whose outputs are well spread, so real playback genuinely varies bow force. The gates were weaker than production, not stricter.

**Fix on branch** `task/20260726-TSK-HUM-spike-bowedstring-in-fiddle-register-key`: a bow-force ceiling over the cello's top few semitones (its `beta` cannot move — 0.140 is what holds its own 46-50 band), plus five per-program register gates (`bowed_string_{violin,viola,cello,contrabass,fiddle}_holds_register`) that use the engine's seed formula and let `slope` draw naturally, and `calibrate_register_gate_catches_the_known_wolf` which asserts each lever fails when removed.

**To verify independently:** check out the branch and run `cargo test -p ferrosintesis --release bowed_string_cello_holds_register`; then revert the `slope_hi`/`slope_hi_key`/`top_key` fields on the CELLO voicing in `string_voicing` (crates/ferrosintesis/src/voices.rs) to no-ceiling and confirm it fails at keys 74 and 76.

## Fix

<unfixed — raised only>

## Notes

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260726T232502Z-p9812-n299435500-c21 outcome=no_work)

Agent-reported summary: MM-BUG-KILN-00146 is already fixed in the current tree by the BowedString cello bow-force ceiling and the register regression tests in voices.rs. I reproduced the original observation by temporarily disabling the cello ceiling and running the focused cello register regression; it failed on GM42 keys 74 and 76 at about +1203 cents, matching the ledger. Restoring the ceiling made the same focused regression pass. The existing calibration test also passes and proves the register oracle still detects an un-ceiled high-force cello failure. No bug ledger, Cargo manifest, lockfile, journal, scratchpad, or lessons file was edited.

Root cause: GM42 cello uses a short BowedString waveguide loop; at the top of the register, a high per-note bow-force draw can drive the loop onto the octave mode instead of the requested fundamental. The old wolf-band gate used small literal seeds 7/17/23, and raw xorshift32 maps their first draw near -1, so the test repeatedly exercised only the minimum bow force while production engine seeds cover the high

Changed:
- No durable source/test edit was needed in this pass; the current tree already contains the cello bow-force ceiling and BowedString register gates in crates/ferr
- Wrote .deltic-run-summary.json only.

Tests:
- Expected failure after temporary no-ceiling edit: cargo test -p ferrosintesis --release bowed_string_cello_holds_register -- --nocapture (failed on GM42 keys 74
- Focused regression: cargo test -p ferrosintesis --release bowed_string_cello_holds_register (passed).
- Calibration support: cargo test -p ferrosintesis --release calibrate_register_gate_catches_the_known_wolf (passed).
- Measurement support: cargo test -p ferrosintesis --release map_bowedstring_bow_force_ceiling -- --ignored --nocapture (passed).

Left alone:
- bugs/
- Cargo.toml
