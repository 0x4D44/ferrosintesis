# MM-REQ-KILN-00155 — Sample-family package ownership must be source-derived and checked

- **State:** Draft
- **Priority:** Could
- **Area:** sample generation / package routing
- **Raised:** 2026-07-27
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-27, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The system must derive and check that every generated sample family routes to
the sample crate that owns that family on disk.

## Notes

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\prepare.py:1135`
maintains `FAMILY_PACKAGE` by hand. `sample_output_path()` defaults an unknown
family to the original, already size-capped
`ferrosintesis-samples-orchestral` crate. Deleting or misspelling a mapping can
therefore publish a regenerated family into the wrong crate.

The apparently broad route test at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\test_prepare.py:84`
derives inputs from three legacy source maps and accepts only the core and
original orchestral destinations. It exercises none of
`ferrosintesis-samples-orchestral2`'s 14 families or most modern dedicated
sample crates.

Current routing is correct; this is durable debt, not a current defect. A
suitable Gate-1 oracle should derive family ownership from packaged
`samples/*.wav` directories, require every family to have exactly one owning
crate, and compare that ownership with `sample_output_path()`. Include a
negative control that deletes or misspells a route and proves the oracle names
the misrouted family.

Proposed priority: Could. Proposed flow: light. Estimated effort: Small–Medium
(2–4 hours).
