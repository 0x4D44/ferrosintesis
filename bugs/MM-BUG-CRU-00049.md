# MM-BUG-CRU-00049 — Concurrent mandolin regenerations race the shared source staging directory

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** mandolin sample generation / concurrent source isolation
- **Raised:** 2026-08-20T12:21:19Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T200250Z-ee0f9e55
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00049-run-verify-20260913T200250Z-ee0f9e55
- **Owner base:** dac45daaaf96b8adf9b28f10ed5fdb498bd83e8d
- **Owner fingerprint:** sha256:f94fc027f206ed5202a441a1dc4dbb77d9110df5cc12f65eecbefe4dafaefc28
- **Owner since:** 2026-09-13T20:02:50Z
- **Owner until:** 2026-09-13T22:02:50Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-20T12:21:19Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:06:45Z, deltic:auto role=fix run=fix-20260913T145951Z-e4d049c6 branch=task/bug-MM-BUG-CRU-00049-run-fix-20260913T145951Z-e4d049c6 code=0179cee76f348d6e4e84096a2891082b7687a05f gate=manual)

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

<unfixed — raised only>

Prefer reading the committed mandolin sources directly. If a copy is required, use a
process-unique staging directory or a lock plus atomic publication. Add a two-process
regression with different source bytes and a forced overlap between copy and read; neither
run may fail or consume the peer's source.

## Notes
