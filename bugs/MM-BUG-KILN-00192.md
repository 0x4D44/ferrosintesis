# MM-BUG-KILN-00192 — Published orchestral2 provenance misidentifies the viola source as solo

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / orchestral2 viola provenance
- **Raised:** 2026-08-13T22:54:31Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-13T22:54:31Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The published inventory at
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:30` describes
`viola_*` as "Solo viola (GM 41) arco onsets." The actual pinned source is the
VSCO-2 Community Edition **Viola Section** `susvib` bank:
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\tools\ferrosintesis-samples\prepare.py:310` explicitly says VSCO has no
solo viola and uses its section as a proxy. The shipped assets are routed to the
solo-viola GM program, but they are not recordings of a solo violist.

Expected: packaged provenance identifies both the target route and the actual
recording source. Actual: the instrument column turns the target GM identity
into a false source identity, so a standalone package auditor cannot tell that
the samples contain an ensemble proxy. Change the row to state "Viola Section
proxy for GM 41 solo viola" and name the exact VSCO source path/layer. Extend
the provenance/source agreement guard with a negative control that restores
the misleading solo-source wording. Static review only; no audio was run.

## Fix

<unfixed — raised only>

## Notes

The source choice itself is intentional and previously fixed the GM 40/41
near-identity defect. This bug concerns published provenance accuracy only.
