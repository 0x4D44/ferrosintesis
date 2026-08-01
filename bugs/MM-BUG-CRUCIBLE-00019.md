# MM-BUG-CRUCIBLE-00019 — Warm archive caches ignore selected-member mapping changes

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / archive provenance
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:07:19Z, deltic:auto role=fix run=fix-20260801T055954Z-p97736-n464799300-c1 branch=task/bug-MM-BUG-CRUCIBLE-00019-run-fix-20260801T055954Z-p97736-n464799300-c1 code=f3a86f0072d1fd19e064aad133576e89d53c9026 gate=manual)

## Observation

`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:1378`
accepts an extracted-member cache when its archive SHA-256, destination filenames, and
cached destination hashes match. It never checks the `member_map` values that select the
source paths inside the archive. The manifest written at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:1459`
stores only `{destination: cached hash}`.

Static reproduction: change a value in `FINGERBASS_SOURCES` or
`PICKBASS_SOURCES` at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:239`
to select a different member while retaining the destination filename and archive pin.
A clean cache extracts the new member. A warm cache returns at line 1485 and keeps the
old bytes. The same source tree therefore regenerates different shipped assets depending
on cache history.

Expected: changing the selected archive member invalidates the warm cache. Actual: the
recipe change is invisible to the cache predicate.

This was previously confirmed in
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\wrk_docs\2026.07.27 - CR - 20260727-REV-CLA@KILN-code-review-074202.md:56`,
but that pass could not create bug files. No current bug owns this residual.

## Fix

Version the member manifest and bind each destination to its exact archive-member path
plus content hash, or bind a canonical digest of the complete mapping. Require exact map
equality before warm reuse. Add a regression that warms a cache, changes only one mapping
value, and proves the destination is rebuilt from the newly selected member.

## Notes

Static review only. No generator, application, test, build, render, or exploratory harness
ran. Estimated effort: Small.
