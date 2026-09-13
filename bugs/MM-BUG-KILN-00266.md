# MM-BUG-KILN-00266 — Concurrent B1 regenerations race host-global decode and slice intermediates

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** B1 sample generation / concurrent intermediate isolation
- **Raised:** 2026-08-17T05:30:43Z
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
- **State history:** Open (2026-08-17T05:30:43Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T16:56:01Z, deltic:auto role=fix run=fix-20260913T164454Z-969ec757 branch=task/bug-MM-BUG-KILN-00266-run-fix-20260913T164454Z-969ec757 code=f6d5522ba626330ab5455e46d982b8667cb922ad gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: restoring the shared b1_upright directory fails the two-process B1 isolation test)

## Observation

Static review found that every documented B1 regeneration uses the same host-global system-temp directory. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-061026\tools\ferrosintesis-samples\prepare.py:5723` chooses `tempfile.gettempdir()/b1_upright`, while `_slice_b1_sources` at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-061026\tools\ferrosintesis-samples\prepare.py:4848` rewrites fixed `DR0000_0195.wav`, `DR0000_0200.wav`, `slices/` outputs, and manifest names. There is no lock or per-run directory, and the slicer is explicitly invoked with `--no-hash`.

Two worktrees running `python3 tools/ferrosintesis-samples/prepare.py --only=b1upright` concurrently can therefore read an intermediate while the peer truncates or replaces it. At minimum one run can fail spuriously; across different revisions a run can consume the peer's complete decoded take, slice, or manifest and publish a structurally valid bank derived from the wrong source revision. Name/count, RIFF/tail, and aggregate-size checks do not authenticate these intermediates.

Expected: concurrent B1 regenerations use isolated intermediates or serialize access to authenticated immutable intermediates. Actual: all worktrees mutate the same fixed decode and slice paths.

Concrete fix: create a process-unique temporary decode/slice directory for each B1 bake and remove it in `finally`, or add a robust lock plus authenticated immutable cache publication. Add a two-process regression that overlaps decode, slicing, and manifest reads and proves neither run consumes the other's files. Analogous cache-race bugs `MM-BUG-KILN-00221`, `00256`, and `00261` cover other helpers, not B1. Static review only; no generator, test, app, render, or concurrent repro ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `f6d5522b`) by an agent other than the fixer.

`B1ConcurrentPreparationTest` runs two `main(--only=b1upright)` processes with a barrier between decode and manifest/WAV reads; on HEAD they get distinct private directories, neither is the old shared `b1_upright`, and both are removed afterwards.

**Fails-before (method B).** Restoring `b1_src = gettempdir()/b1_upright` fails `test_two_b1_selection_processes_isolate_and_clean_intermediates` ("B1 bake used the old shared directory"). Restored; passes on HEAD.

## Notes
