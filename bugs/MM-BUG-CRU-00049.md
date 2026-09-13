# MM-BUG-CRU-00049 — Concurrent mandolin regenerations race the shared source staging directory

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** mandolin sample generation / concurrent source isolation
- **Raised:** 2026-08-20T12:21:19Z
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
- **State history:** Open (2026-08-20T12:21:19Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:06:45Z, deltic:auto role=fix run=fix-20260913T145951Z-e4d049c6 branch=task/bug-MM-BUG-CRU-00049-run-fix-20260913T145951Z-e4d049c6 code=0179cee76f348d6e4e84096a2891082b7687a05f gate=manual) -> Closed (2026-09-13, independently verified by Codex: mandolin source reads bypass shared staging and remain isolated; no residual gap)

## Observation

Every normal `prepare.py --only=mandolin` run uses the host-global source directory
`tempfile.gettempdir()/vsco2ce_src/VSCO_REV` at
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-124001\tools\ferrosintesis-samples\prepare.py:5719-5720`.
`ensure_mandolin_sources()` at `prepare.py:1681-1686` copies each committed source into
fixed names there with `shutil.copyfile`, without a lock, per-run directory, temporary
file, or atomic replacement. The generic loop immediately opens those shared paths at
`prepare.py:5904` and `:5911-5913`.

Two worktrees can therefore overlap a copy and read. Even identical revisions can see a
temporarily truncated WAV because `copyfile` replaces the destination in place. Different
revisions can consume a peer worktree's complete or partial source and publish a bank
derived from the wrong branch. The current file-count, container, and aggregate-size
checks do not bind the output to the invoking worktree's committed sources.

Expected: concurrent documented mandolin regenerations are isolated or serialized.
Actual: they mutate and read the same fixed source paths with no concurrency guard. Open
`MM-BUG-KILN-00221`, `00256`, and `00261` cover distinct MuseScore intermediate paths;
none covers this owner-recorded mandolin intake. Static review only; no concurrent run,
generator, test, build, decoder, package, app, render, or exploratory harness ran.
Estimated effort: Small-Medium.

## Fix

Fixed by `0179cee76f348d6e4e84096a2891082b7687a05f`. `ensure_mandolin_sources` now returns
the committed source directory, and the bake reads those immutable files directly instead of
copying them into the host-global temporary source directory.

### Verification summary (2026-09-13 — Codex)

`$null | deltic timeout 300 python -m unittest
test_prepare.MandolinConcurrentSourceTest` passed the two-process overlap regression. Each
worker consumed its own source bytes and completed without touching the peer's source.

For the required mutation check, I temporarily restored the old shared-copy implementation.
The same regression failed with `A: consumed another process's mandolin source`. I restored
the direct-source implementation and verified its source diff is empty.

The complete sample-tooling gate on this fix set ran 264 tests with one unrelated
Steinway alias-manifest failure and an existing unclosed-file `ResourceWarning`. The shared
publication/source helpers also have separate records for ffmpeg presence and bank
atomicity; those do not duplicate this mandolin source-isolation defect.

## Notes
