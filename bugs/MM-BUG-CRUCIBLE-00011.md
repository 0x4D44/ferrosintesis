# MM-BUG-CRUCIBLE-00011 — Encoder subprocesses can hang the catalog indefinitely

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / encoder process control
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review) -> Fixed (2026-07-31T23:01:01Z, deltic:auto role=fix run=fix-20260731T225122Z-p12404-n037798400-c1 branch=task/bug-MM-BUG-CRUCIBLE-00011-run-fix-20260731T225122Z-p12404-n037798400-c1 code=cc0c78d6186412819e8614b39620356abe0d1719 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 789baed; fixer was Codex GPT-5.6-Sol)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `789baed` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-8-11`.

**Both unbounded waits are gone.** `output_with_timeout` spawns the child
explicitly, polls `try_wait`, and on expiry kills *then* waits before reporting.
Both call sites use it: preflight (`PREFLIGHT_TIMEOUT` 10 s) and the per-track
encode (`ENCODE_TIMEOUT` 30 min, sized against real track length). Returning the
reaped `Output` inside `TimedOut` is what proves the child was reaped rather than
detached.

**Fails-before proved by reverting only the fix.** Replacing the polling loop with
the pre-fix unbounded `wait_with_output()` (tests untouched) made
`hanging_fake_encoder_is_bounded_reaped_and_drops_temp_wav` hang: it produced no
result inside a 90 s external bound and had to be killed. Restoring `main.rs`
(md5 `336c0617…`) made the same test pass in ~1 s, asserting the child started,
was killed and reaped, the message names the label and limit, elapsed < 5 s, and
the temporary WAV was removed.

**Gates.** `cargo test -p render-catalog` green (21 pass, 1 ignored helper, plus
5 overlap tests); `cargo clippy -p render-catalog --all-targets -- -D warnings`
clean; `cargo fmt --all -- --check` clean.

The exact production timeout policy flagged in the Notes below is settled by the
two documented constants above; no residual split.

## Notes

Static review only. The pass did not execute the application or tests. The exact
production timeout policy needs care because legitimate tracks vary in duration;
that affects the fix design, not the existence of the unbounded wait.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
