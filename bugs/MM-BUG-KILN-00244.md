# MM-BUG-KILN-00244 — Grand regeneration command leaves the embedded FLAC bank stale

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample crate / deterministic regeneration
- **Raised:** 2026-08-16T22:56:39Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T202121Z-658142c4
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00244-run-verify-20260913T202121Z-658142c4
- **Owner base:** 0521df2a293bac504d030af6575e76739e13d1f8
- **Owner fingerprint:** sha256:64b943e802e75e1efd5a51617db550d20ce9d6a1b9dff2a0bcb2eb34536404fd
- **Owner since:** 2026-09-13T20:21:21Z
- **Owner until:** 2026-09-13T22:21:21Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T22:56:39Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T07:10:46Z, deltic:auto role=fix run=fix-20260913T070407Z-86a459d0 branch=task/bug-MM-BUG-KILN-00244-run-fix-20260913T070407Z-86a459d0 code=ccc86aad gate=manual)

## Observation

The crate documents
`python3 tools/ferrosintesis-samples/prepare.py --only=grand` as the complete scoped
regeneration command at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\crates\ferrosintesis-samples-grand\README.md:19-27`
and `PROVENANCE.md:66-72`. The active crate embeds only `.flac` files, but
`GRAND_SOURCES` still names `.wav` outputs at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\tools\ferrosintesis-samples\prepare.py:681-686`,
and the generic bake writes those WAV names at `prepare.py:5733-5778`.

Following the documented command therefore leaves all 54 embedded FLACs untouched
and writes 54 new WAVs beside them. Runtime continues to consume the stale FLAC
table, while `inventory_matches_packaged_samples` sees 108 sample files against
`FILE_COUNT = 54` and fails. The validator at `prepare.py:5419-5424` inspects only
WAV names, so it cannot reject the stale FLAC half before writing. Expected: the
scoped command replaces the exact final packaged bank that runtime consumes.
Actual: it produces unconsumed assets and leaves the shipped bank stale. Static
review only; the generator was not run.

## Fix

<unfixed — raised only. Make the grand recipe produce verified final FLAC files and
refresh the inventory as one scoped workflow, reject mixed extensions before the
first write, and add a negative control starting from the current FLAC-only tree.>

## Notes

`MM-BUG-KILN-00182` is not a duplicate: it covers obsolete extra WAV names in the
former WAV-owned workflow. This defect was introduced later by the WAV-to-FLAC
migration and leaves the new embedded FLAC bank stale. Open `MM-BUG-KILN-00239`
covers the analogous but independently owned gong workflow.
