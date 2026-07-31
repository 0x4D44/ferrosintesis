# MM-BUG-CRUCIBLE-00011 — Encoder subprocesses can hang the catalog indefinitely

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / encoder process control
- **Raised:** 2026-07-31
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260731T225122Z-p12404-n037798400-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00011-run-fix-20260731T225122Z-p12404-n037798400-c1
- **Owner base:** 46b928b33d112360a9bf4e4129466d547e13f85d
- **Owner fingerprint:** -
- **Owner since:** 2026-07-31T22:51:22Z
- **Owner until:** 2026-08-01T00:51:22Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review)

## Observation

Both encoder subprocess calls wait without a deadline:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\crates\render-catalog\src\main.rs:761`
  blocks on the preflight `ropusenc --version` call.
- `main.rs:714` blocks each render worker on the per-track encode.
- `main.rs:829-868` cannot leave the scoped thread block until every worker joins.

A stuck preflight process prevents discovery from starting. A stuck track encode
retains its large temporary WAV, occupies a worker forever, and prevents the
entire command from producing its final status even after other workers finish.

**Expected:** an unresponsive external encoder becomes a bounded, named failure
and owned child processes are reaped.

**Actual:** there is no deadline or cancellation path, so either subprocess can
hold the catalog indefinitely.

## Fix

Spawn the child explicitly, enforce a documented generous or duration-aware
deadline, and on expiry kill then wait for the child before returning a failed
outcome. Use the same bounded helper for preflight and per-track encoding.

Add a fake encoder that never exits and inject a short test deadline. Assert a
bounded nonzero result, child reaping, and temporary-WAV cleanup.

## Notes

Static review only. The pass did not execute the application or tests. The exact
production timeout policy needs care because legitimate tracks vary in duration;
that affects the fix design, not the existence of the unbounded wait.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
