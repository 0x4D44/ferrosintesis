# MM-BUG-KILN-00146 — GM42 cello keys 74/76 lock an octave up at high bow force, and the wolf gate's seeds could not see it

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** voices / BowedString
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260726T233602Z-p9812-n603751900-c22 branch=task/bug-MM-BUG-KILN-00146-run-fix-20260726T233602Z-p9812-n603751900-c22 code=67e6a15b8c57714dcade55d7769cc5e239b8d1f4 gate=focused+render-diff model=codex@xhigh) → Closed (2026-07-27, deltic:auto role=verify run=verify-20260727T160401Z-p9812-n403774100-c90 verified_fix_run=fix-20260726T233602Z-p9812-n603751900-c22 verdict=close model=claude)

## Observation

Two coupled defects, both pre-existing, both fixed on the branch below but NOT independently verified — raised so the two-eyes rule applies rather than self-closing them.

**1. The defect.** `BowedString` GM 42 (cello) loses its fundamental at keys 74 (D5) and 76 (E5) whenever the per-note bow force draws near the top of its range, locking an octave up at +1203 cents with the level down ~60%. Bow force is drawn per note from 2.2-2.9, so this hits roughly one note in eight at those pitches — the top two tones of the cello's range.

Root cause: bowing hard in a SHORT loop drives the waveguide off its fundamental. Same failure family as the known 46-50 wolf band (MM-BUG-KILN-00012), at the other end of the register.

**2. Why nobody saw it.** `bowed_string_wolf_band_holds_fundamental` asserts that 'every per-note seed must settle onto the requested fundamental', using seeds 7/17/23. All three are small, and `Rng::new` (crates/ferrosintesis/src/dsp.rs) seeds xorshift32 raw — its first output from a small seed is ~= -1.0, so `u = white()*0.5+0.5` ~= 0.0 and bow force collapses onto 2.2003..2.2010 out of 2.2-2.9. The gate tested ONE bow force three times, on the single axis this waveguide fails on.

The engine is unaffected: melodic notes use `0x9E37 ^ (index * 2654435761)`, a Knuth-hashed stream whose outputs are well spread, so real playback genuinely varies bow force. The gates were weaker than production, not stricter.

**Fix on branch** `task/20260726-TSK-HUM-spike-bowedstring-in-fiddle-register-key`: a bow-force ceiling over the cello's top few semitones (its `beta` cannot move — 0.140 is what holds its own 46-50 band), plus five per-program register gates (`bowed_string_{violin,viola,cello,contrabass,fiddle}_holds_register`) that use the engine's seed formula and let `slope` draw naturally, and `calibrate_register_gate_catches_the_known_wolf` which asserts each lever fails when removed.

**To verify independently:** check out the branch and run `cargo test -p ferrosintesis --release bowed_string_cello_holds_register`; then revert the `slope_hi`/`slope_hi_key`/`top_key` fields on the CELLO voicing in `string_voicing` (crates/ferrosintesis/src/voices.rs) to no-ceiling and confirm it fails at keys 74 and 76.

## Fix

Current trunk already carries both behavioral stabilizers: the cello's top-register
bow-force ceiling and MM-BUG-KILN-00029's joint bow-speed/pressure map. This fix makes
the register oracle follow that shipping path instead of copying a stale seed formula:

- `engine::note_voice_seed` is now the single source of truth for melodic note seeds.
- The register seed set proves its raw first draw reaches hard bow force before the
  low-string playable-region map intentionally converges high-velocity pressure to 2.60.
- Cello and contrabass register gates walk velocities 32/64/96/127 across their full
  compasses. Violin, viola and fiddle retain their register-only velocity-100 scope.
- The calibration oracle reconstructs the excluded high-speed/high-force corner and
  proves the pitch oracle still detects the original failure family.

### Fix summary (2026-07-27, deltic:auto run=fix-20260726T233602Z-p9812-n603751900-c22 code=67e6a15b8c57714dcade55d7769cc5e239b8d1f4 gate=focused+render-diff)

Agent-reported summary: Fixed MM-BUG-KILN-00146 by tying every BowedString register oracle to the engine's actual melodic note-seed helper and exercising the low-string velocity-dependent control map. Current trunk's cello force ceiling and MM-BUG-KILN-00029 joint controls already remove the shipping octave-lock corner, so this branch preserves the voicing byte-for-byte while repairing the stale coverage. All five register gates, the known-wolf calibration, both clippy configurations, and the full catalog render comparison are green.

Root cause: GM42 cello uses a short BowedString waveguide loop that can mode-lock onto the octave at the high-speed/high-force corner. The previous wolf-band test used small literal seeds that collapsed force to the bottom of its range, while the later register oracle copied a stale seed formula and only tested velocity 100. Subsequent MM-BUG-KILN-00029 controls made that one-velocity seed assertion additionally misleading by intentionally converging every high-velocity low-string draw to stable force 2.60.

Changed:
- crates/ferrosintesis/src/engine.rs: added the crate-visible `note_voice_seed` source of truth and reused the common Knuth step without changing generated seed bits.
- crates/ferrosintesis/src/voices.rs: switched BowedString tests to the engine seed helper, separated raw seed-span coverage from post-control pressure, and exercised GM42/43 across four velocities.
- scratchpad.md: parked the separately discovered GM40/41/110 velocity-127 octave locks for independent triage.

Tests:
- `$null | deltic timeout 600 cargo test -p ferrosintesis --release holds_register -- --nocapture` (five passed).
- `$null | deltic timeout 600 cargo test -p ferrosintesis --release calibrate_register_gate_catches_the_known_wolf -- --nocapture` (passed).
- `$null | deltic timeout 300 cargo clippy -p ferrosintesis --all-targets -- -D warnings` (passed).
- `$null | deltic timeout 300 cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings` (passed).
- `python tools/render-diff/render_diff.py --baseline D:\worktrees\midi-music\BASELINE-00146\target\release\ferrosintesis.exe --new .\target\release\ferrosintesis.exe --program 42 --rate 8000 --jobs 6`: 0 changed, 73 expected same, 0 contamination, 51 expected not-reached because production behavior is intentionally bit-identical.
- The same render diff with `--glob "demos/**/*.mid"`: 0 changed, 14 expected same, 0 contamination, 3 expected not-reached.

Left alone:
- Cargo.toml
- Cargo.lock

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T160401Z-p9812-n403774100-c90 verified_fix_run=fix-20260726T233602Z-p9812-n603751900-c22 verdict=close)

Verifier note: GM42 keys 74/76 hold their fundamental at every reachable bow force on this trunk; the register gates now seed from engine::note_voice_seed and are proven non-vacuous; all repo gates green. — Trunk 0e86ca0. (1) Symptom: ran map_bowedstring_bow_force_ceiling --ignored (forces v.slope directly, bypassing both stabilizers) - GM42 keys 48-101 report max_slope_ok '>=2.90 (full range)' for every key except 90/91 (2.65/2.40), which sit above the cello register (top_key 76) and are the documented beta-0.140 violin-family dead notes; the bug's keys 74 and 76 take the whole 2.20-2.95 sweep within 15 cen...

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
