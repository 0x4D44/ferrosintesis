# MM-BUG-CRUCIBLE-00035 — Inherited drumkit PCM probe marker bypasses pristine-process test isolation

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / core drum-kit cache regression
- **Raised:** 2026-08-15T13:48:05Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T160555Z-p45968-n192851000-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00035-run-fix-20260815T160555Z-p45968-n192851000-c1
- **Owner base:** 2d9a2bab0e1bb69a28dd6e0f64a1342850399e39
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T16:05:55Z
- **Owner until:** 2026-08-15T18:05:55Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-15T13:48:05Z, raised via `deltic bugs new`)

## Observation

The new cold-cache regression decides whether it is running in its pristine
child process solely from the presence of the environment variable
`FERRO_DRUMKIT_PCM_MISS_PROBE` at
`D:\worktrees\ferrosintesis\20260815-REV-MM-CDX@CRUCIBLE-code-review-142946\crates\ferrosintesis-samples-drumkit\src\lib.rs:986`.

If that variable is already present in the caller or CI environment, the outer
test skips the re-exec at lines 990-1005 and runs its cold-cache assertions in
the shared libtest process. Other tests initialize the same process-global
`PCM_CACHE` at lines 878-895 and 938-970. Depending on scheduling, the assertion
at line 1007 can therefore see a warm cache and fail even though the miss path
is correct.

Expected: the regression always evaluates cold-cache behavior in a fresh child
process, independently of inherited environment and parallel test order.

Actual: any inherited value for the private probe variable selects child mode
and defeats that isolation. This was confirmed from the control flow; the test
was not run because the review pass is static and read-only.

## Fix

Replace environment-presence recursion with a separate ignored child test. Have
the outer test re-exec the current test binary with the child's exact name and
`--ignored`, then require evidence that exactly that child ran before accepting
its status. Keep the cold-cache assertions only in the child.

## Notes

Introduced by `44fcdf32251fc3c34ee5b708c033f894dd8b7074`, which fixed
`MM-BUG-CRUCIBLE-00023`. The production miss-path fix is correct; this record is
only about the regression's process isolation. The companion
`ferrosintesis-samples-drumkit2` test uses the same environment-presence shape,
so the fixer should enumerate and repair both instances.

Estimated effort: Small.
