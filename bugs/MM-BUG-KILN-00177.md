# MM-BUG-KILN-00177 — GM67 keys 64-67 still expose the recorded sustain loop: the MM-BUG-KILN-00176 gate was drawn at the reported key, not the measured onset

- **State:** Open
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high)

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

<unfixed — raised only>

## Notes
