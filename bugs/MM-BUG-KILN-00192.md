# MM-BUG-KILN-00192 — Published orchestral2 provenance misidentifies the viola source as solo

- **State:** Closed
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
- **State history:** Open (2026-08-13T22:54:31Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-08-15T15:43:36Z, deltic:auto role=fix run=fix-20260815T153519Z-p43376-n739262500-c1 branch=task/bug-MM-BUG-KILN-00192-run-fix-20260815T153519Z-p43376-n739262500-c1 code=a6abb0c gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: viola row now names the VSCO Viola Section susvib proxy, matching prepare.py's pinned source; no guard was added)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `a6abb0c7`) by an agent other than the fixer.

**Original observation re-derived.** The orchestral2 PROVENANCE viola row reads "Viola SECTION `susvib` arco onsets, routed to solo viola (GM 41)". Checked against code: `prepare.py:321,341` fetch `Strings/Viola%20Section/susvib/ViolaEns_susvib_*`, and VSCO has no solo viola, so the row is true.

**Fails-before (method A).** At `a6abb0c7^` the row said "Solo viola (GM 41) arco onsets".

**Coverage gap.** The record asked for a provenance/source agreement guard with a negative control; none was added, so the wording is unguarded. Logged in `scratchpad.md`.

## Notes

The source choice itself is intentional and previously fixed the GM 40/41
near-identity defect. This bug concerns published provenance accuracy only.
