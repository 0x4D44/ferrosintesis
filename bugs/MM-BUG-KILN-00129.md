# MM-BUG-KILN-00129 — Gong provenance claims a velocity crossfade that does not exist

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** gong sample-bank provenance
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-gong/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T084844Z-p17868-n593068000-c1 branch=task/bug-MM-BUG-KILN-00129-run-fix-20260726T084844Z-p17868-n593068000-c1 code=901b103ae0cf1b1d4970f38eb5d243bafc9daa1f gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (635 passed) and `test --workspace --exclude amp-lab --locked` (741 passed) - 1479 tests, 0 failures. Original observation re-run at source, on both halves. The false claim is gone: `crates/ferrosintesis-samples-gong/PROVENANCE.md` no longer says `GongOneShot` "velocity-crossfades between soft and loud" - it now states that the voice "selects exactly one recording: soft through velocity 83, loud at velocity 84 and above", and preserves the comb-filter rationale the fix direction asked to keep. The shipped behaviour is unchanged and is what the new wording describes: `GONG_LOUD_VEL` is still 84 (`sampler.rs:4675`) and `gong_layer` (`:4693`) is a hard switch returning one slice or the other, with no summing anywhere on the path. The requested boundary regression exists as `gong_provenance_describes_the_shipped_velocity_boundary`, and its instrument is well chosen: the two `ptr::eq` clauses assert the returned slice is pointer-identical to an original take, which a crossfade could not satisfy (it would have to produce a blended buffer), so it proves "exactly one recording" rather than merely checking wording. I proved it is non-vacuous by REINTRODUCING the defect - replacing the corrected sentences with the original "velocity-crossfades between soft and loud" turned it red ("gong provenance must name the shipped hard-switch boundary"). Restored; `git status --porcelain` clean. CLOSED WITH A RESIDUAL SPLIT OUT AS MM-BUG-KILN-00132. The oracle's documentation clause pins the boundary as the LITERAL string "hard switch at velocity 84" while the shipped boundary lives in `GONG_LOUD_VEL`, so the two can drift apart again - which is this bug's own defect class and what its fix direction ("so the corrected statement remains true") set out to prevent. I demonstrated it rather than inferring it: setting `GONG_LOUD_VEL` to 90 and leaving the provenance untouched left the test GREEN with the packaged document describing a boundary the synth no longer uses. Constant restored. It is a residual rather than a persistence - the reported wording defect is fixed and the guard does catch the reported symptom - and the remedy is the pattern this repo already uses at `altbank.rs:1342`, `format!("CC0={slot}")` from the shipped value. Recorded in full on 00132.)

## Observation

`crates/ferrosintesis-samples-gong/PROVENANCE.md:95-98` says
`GongOneShot` “velocity-crossfades between soft and loud.”

The shipping implementation deliberately does something else:

- `crates/ferrosintesis/src/sampler.rs:4650-4654` documents a hard switch at
  velocity 84 because summing the two recordings would comb-filter;
- `crates/ferrosintesis/src/sampler.rs:4688-4694` selects only the loud slice
  at velocities 84 and above, and only the soft slice below 84.

**Expected.** Packaged provenance must describe the layer-selection behavior
that the synth actually ships.

**Actual.** It describes a blend across velocity when the signal path contains
no crossfade. The implementation is internally consistent and is not reported
as an audio defect; the defect is the false packaged design statement.

No application or audio test ran in this read-only review.

## Fix

Change the provenance wording to state that velocity selects the soft or loud
take with a hard switch at velocity 84. Preserve the comb-filter rationale from
the implementation. Add the 83/84 boundary to the adjacent sampler oracle so the
corrected statement remains true.

Estimated effort: Extra small for the documentation correction; Small including
the boundary regression.

## Notes

No matching bug or requirement was found in the current ledgers.
