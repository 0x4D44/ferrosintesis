# MM-BUG-CRU-00054 — Concurrent YDP regenerations race one shared manifest staging file

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** YDP sample generation / shared cache concurrency
- **Raised:** 2026-08-20T15:51:10Z
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
- **State history:** Open (2026-08-20T15:51:10Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:35:22Z, deltic:auto role=fix run=fix-20260913T152903Z-774f5e0c branch=task/bug-MM-BUG-CRU-00054-run-fix-20260913T152903Z-774f5e0c code=e60b130b978b1a553f033ea50f7b1a8eca11ad5d gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: forced-overlap manifest writers raise PermissionError on reversed code and publish cleanly on HEAD)

## Observation

Static code review of the YDP regeneration path.

Observation: every `--only=ydpgrand` run uses the process-shared OS-temp directory `<temp>/ydp_grand` at tools/ferrosintesis-samples/prepare.py:5872-5875. On a cold or invalid cache, ensure_ydp_sf2 rebuilds independently and then write_member_manifest writes through one fixed staging name, `<manifest>.part`, at prepare.py:1601-1618. Two overlapping writers can both open that path, then one renames or truncates it while the peer still expects it. On Unix the second `os.replace(tmp, path)` can see no source after the first renamed it; on Windows a rename can fail while the peer has the staging file open. The result is a failed or needlessly rebuilt regeneration. Identical current pins keep the extracted SF2 content equivalent, so static review did not establish a silent wrong-bank outcome.

Expected: concurrent cold YDP regenerations either share a proven cache safely or complete independently.

Actual: they race one fixed manifest staging file in a shared cache directory.

Concrete fix: write manifests through unique sibling temporary files (`mkstemp`/`NamedTemporaryFile` with same-directory atomic replace), and revalidate the winning manifest/cache after publication or protect the cache rebuild+manifest transaction with a per-cache lock. Add an orchestrated two-writer regression that overlaps manifest writes and requires both callers to succeed with a valid final manifest and no `.part` leftovers.

Static review only. No generator, test, build, app, render, network, or exploratory harness ran. Estimated effort: Small–Medium. MM-BUG-KILN-00205 covers failure-atomic publication of the tracked YDP bank, not this shared-cache race; MM-BUG-CRU-00049 is Mandolin-specific.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `e60b130b`) by an agent other than the fixer.

**Original observation re-run.** A scratch scenario held writer A's manifest staging file open for 0.5 s while writer B started. On HEAD: no errors, a valid final manifest, no `.part` leftovers. On reversed code: B fails with PermissionError 13.

**Fails-before (method B).** Restoring the fixed `<manifest>.part` name and removing the lock fails `test_two_manifest_writers_publish_without_colliding_staging_files` (1 != 2 distinct staging names). Restored; passes on HEAD. The committed test detects the reversal through staging names rather than an observed collision; the forced-overlap scenario shows the real symptom.

## Notes
