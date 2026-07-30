# MM-BUG-KILN-00177 — GM67 keys 64-67 still expose the recorded sustain loop: the MM-BUG-KILN-00176 gate was drawn at the reported key, not the measured onset

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** audio / sampled sax sustain
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-30, deltic:auto role=fix run=fix-20260729T223554Z-p5432-n906511000-c1 branch=task/bug-MM-BUG-KILN-00177-run-fix-20260729T223554Z-p5432-n906511000-c1 code=88532550b160f935e7779a18c3381d94960f8c8c gate=manual) -> Closed (2026-07-30, independently verified by claude-opus-5@high on trunk 73ec2f2; fix authored by GPT-5.6, so two-eyes holds)

## Observation

Residual split from MM-BUG-KILN-00176 during its independent two-eyes closure.

MM-BUG-KILN-00176 fixed GM67 loop exposure by enabling multi-slice grain motion at
`crates/ferrosintesis/src/sampler.rs` `sax_loop_voice`, gated on
`program == 67 && key >= 68`. That boundary is the lowest key Arthur happened to
audition (68 and 73), not the key at which the artifact starts.

Measured on trunk 897ff63 (fix present), rendering each note isolated for 1.35 s and
correlating the 8-band log spectral envelope at the selected source-loop period
(the same quantity MM-BUG-KILN-00176's Observation table reports):

| key | vel | zone root Hz | loop ms | raw corr @1x | @2x | grain motion |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 64 | 72 | 335.0 | 57.64 | 0.720 | 0.524 | off |
| 64 | 110 | 334.1 | 66.74 | 0.923 | 0.928 | off |
| 65 | 72 | 335.0 | 54.40 | 0.875 | 0.938 | off |
| 65 | 110 | 334.1 | 62.99 | 0.917 | 0.930 | off |
| 66 | 72 | 335.0 | 51.35 | 0.572 | 0.745 | off |
| 66 | 110 | 334.1 | 59.46 | 0.929 | 0.921 | off |
| 67 | 72 | 421.2 | 84.19 | 0.946 | 0.988 | off |
| 67 | 110 | 420.5 | 58.68 | 0.909 | 0.961 | off |
| 68 | 72 | 421.2 | 79.46 | -0.019 | -0.059 | ON |
| 68 | 110 | 420.5 | 55.38 | -0.230 | 0.220 | ON |
| 69 | 72 | 450.5 | 81.82 | 0.009 | -0.102 | ON |
| 70 | 110 | 448.8 | 75.08 | 0.052 | 0.052 | ON |

The decisive row is key 67. It selects the SAME source zone as key 68 (root 421.2 Hz
at velocity 72, 420.5 Hz at velocity 110) and therefore the same short recorded loop,
yet renders with grain motion off. At 0.946 @1x / 0.988 @2x it is more exposed than
key 68 measured BEFORE the fix (0.932). Keys 64-66 sit at 0.57-0.93.

For scale, MM-BUG-KILN-00176 records the two reference modules (SC-55, S-YXG50)
peaking between 0.036 and 0.220 on this statistic, and the four keys the fix does
treat now peak at 0.220.

**Expected.** The gate reflects where the source loop actually becomes audible,
derived from the zone/loop the key selects, rather than a hand-written key number.

**Actual.** Keys 64-67 keep the single-slice reader while sharing (at key 67,
identically) the loop length that justified fixing key 68.

This is the defect class CLAUDE.md names under "Hand-maintained lists are the
recurring defect here - derive them": the reported key was evidence the boundary was
unexamined, not the specification of the work.

No fix attempted. Deciding the correct boundary needs a per-zone criterion (loop
length against key, or a periodicity probe swept across the reachable band keys
68-81 down through the p/f banks), not a second hand-written constant.

## Fix

`88532550` (GPT-5.6) at `crates/ferrosintesis/src/sampler.rs`:

- `sax_loop_voice` gates grain motion on `program == 67` alone — the `key >= 68`
  hand-written boundary is gone, so the gate no longer encodes a reported key.
- `SAX_GRAIN_MAX_S` 0.13 → 0.09, because longer moving slices preserved a 2x-loop
  correlation near key 67.
- The regression `baritone_sax_hold_does_not_expose_the_source_loop_period`
  (renamed from `..._high_hold_...`) extends from 4 to 12 key/velocity cases,
  covering 64/65/66/67 at both measured velocities.

## Notes

**Independent verification, 2026-07-30, claude-opus-5@high on trunk 73ec2f2**
(worktree `D:\worktrees\midi-music\20260730-TSK-HUM-verify-close-sax-bugs`).
Fix authored by GPT-5.6 — a different actor, so two-eyes holds.

**Original observation replicated exactly.** A probe rendering each note isolated
for 1.35 s and correlating the 8-band log spectral envelope at the selected
source-loop period reproduces the Observation table digit-for-digit on the
single-slice path — the same code path those rows were measured on:

| key/vel | recorded above (@1x, @2x) | single-slice measured now |
| --- | --- | --- |
| 64/72 | 0.720, 0.524 | 0.720, 0.524 |
| 64/110 | 0.923, 0.928 | 0.923, 0.928 |
| 65/72 | 0.875, 0.938 | 0.875, 0.938 |
| 65/110 | 0.917, 0.930 | 0.917, 0.930 |
| 66/72 | 0.572, 0.745 | 0.572, 0.745 |
| 66/110 | 0.929, 0.921 | 0.929, 0.921 |
| 67/72 | 0.946, 0.988 | 0.946, 0.988 |
| 67/110 | 0.909, 0.961 | 0.909, 0.961 |

That pins the probe to the reporter's quantity before judging the fix.

**Symptom is gone.** On the fixed build the production path for those same eight
cases measures (@1x, @2x): 64/72 0.178, 0.150 · 64/110 0.210, 0.075 · 65/72
-0.103, -0.057 · 65/110 -0.095, 0.016 · 66/72 0.176, 0.201 · 66/110 0.247, 0.058
· 67/72 0.221, 0.125 · 67/110 0.248, 0.080. The decisive key-67 row falls from
0.946/0.988 to 0.221/0.125 — into the 0.036–0.220 band the Observation records
for the SC-55 and S-YXG50 reference modules.

**Gate verified directly, not inferred.** Rendering the production voice and an
explicit single-slice voice from the same seed and comparing buffers: keys 64,
65, 66, 67, 68, 69, 70 and 58 all now differ, i.e. grain motion is ON for every
one. Pre-fix, 64–67 were bit-identical to the control.

**Regression genuinely fails before / passes after.** Reverting only the gate to
`program == 67 && key >= 68` fails the test at its first new case: "GM67 key 64
velocity 72: spectral-envelope correlation excess 0.631 exposes the 0.0576s
source loop ... versus single-slice control 0.631". Restored, it passes.

**Root cause addressed, not the symptom.** The bug's own Expected asked that the
gate stop being a hand-written key number. Dropping the key term entirely (rather
than substituting a second constant) does that, and is simpler than the per-zone
criterion the Observation proposed.

**Gates green on the exact tree:** `cargo test --workspace --release` 842 passed
/ 0 failed in `ferrosintesis` plus every sample crate green;
`cargo clippy --workspace --all-targets -- -D warnings` clean;
`cargo fmt --all -- --check` clean.

Verification probes were temporary and are not committed; the tree was restored
to 73ec2f2 and confirmed clean before the gate run.
