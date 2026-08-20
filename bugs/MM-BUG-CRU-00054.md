# MM-BUG-CRU-00054 — Concurrent YDP regenerations race one shared manifest staging file

- **State:** Open
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
- **State history:** Open (2026-08-20T15:51:10Z, raised via `deltic bugs new`)

## Observation

Static code review of the YDP regeneration path.

Observation: every `--only=ydpgrand` run uses the process-shared OS-temp directory `<temp>/ydp_grand` at tools/ferrosintesis-samples/prepare.py:5872-5875. On a cold or invalid cache, ensure_ydp_sf2 rebuilds independently and then write_member_manifest writes through one fixed staging name, `<manifest>.part`, at prepare.py:1601-1618. Two overlapping writers can both open that path, then one renames or truncates it while the peer still expects it. On Unix the second `os.replace(tmp, path)` can see no source after the first renamed it; on Windows a rename can fail while the peer has the staging file open. The result is a failed or needlessly rebuilt regeneration. Identical current pins keep the extracted SF2 content equivalent, so static review did not establish a silent wrong-bank outcome.

Expected: concurrent cold YDP regenerations either share a proven cache safely or complete independently.

Actual: they race one fixed manifest staging file in a shared cache directory.

Concrete fix: write manifests through unique sibling temporary files (`mkstemp`/`NamedTemporaryFile` with same-directory atomic replace), and revalidate the winning manifest/cache after publication or protect the cache rebuild+manifest transaction with a per-cache lock. Add an orchestrated two-writer regression that overlaps manifest writes and requires both callers to succeed with a valid final manifest and no `.part` leftovers.

Static review only. No generator, test, build, app, render, network, or exploratory harness ran. Estimated effort: Small–Medium. MM-BUG-KILN-00205 covers failure-atomic publication of the tracked YDP bank, not this shared-cache race; MM-BUG-CRU-00049 is Mandolin-specific.

## Fix

<unfixed — raised only>

## Notes
