# MM-BUG-KILN-00129 — Gong provenance claims a velocity crossfade that does not exist

- **State:** Fixed
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-gong/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T084844Z-p17868-n593068000-c1 branch=task/bug-MM-BUG-KILN-00129-run-fix-20260726T084844Z-p17868-n593068000-c1 code=901b103ae0cf1b1d4970f38eb5d243bafc9daa1f gate=manual)

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
