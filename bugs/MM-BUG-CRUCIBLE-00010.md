# MM-BUG-CRUCIBLE-00010 — Nonzero encoder preflight is accepted before expensive catalog synthesis

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / encoder preflight
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
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review) -> Fixed (2026-07-31T22:50:21Z, deltic:auto role=fix run=fix-20260731T224022Z-p70228-n873410000-c1 branch=task/bug-MM-BUG-CRUCIBLE-00010-run-fix-20260731T224022Z-p70228-n873410000-c1 code=a529c05e6c8f8a3af4a5d93c09c1e5eef6230e74 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 789baed; fixer was Codex GPT-5.6-Sol)

## Observation

`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\crates\render-catalog\src\main.rs:759-763`
checks only whether `ropusenc --version` could be spawned. `Command::output()`
returns `Ok(Output)` for a process that exits nonzero, so a broken or incompatible
encoder passes preflight.

The renderer then creates the full normalized WAV before each real encoder call
at `main.rs:695-721`. A failed outcome does not cancel the queue at
`main.rs:834-859`, so every selected track can pay the full synthesis cost before
the command finally exits nonzero.

**Expected:** a nonzero `ropusenc --version` result stops the run before discovery
or synthesis and reports why the encoder is unusable.

**Actual:** only a spawn failure stops preflight; an explicit failure status is
ignored.

## Fix

Inspect both spawn errors and `Output::status.success()`. On nonzero status, fail
before discovery/rendering and include a bounded stderr tail.

Extract the preflight into a testable helper. Put a fake `ropusenc` first on PATH
that exits nonzero for `--version`, then prove the renderer rejects it without
entering synthesis.

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `789baed` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-8-11`.

**Root cause addressed.** `ropusenc_preflight` now inspects
`Output::status.success()` as well as the spawn result, and `with_encoder_preflight`
runs before `discover`, so a nonzero `--version` aborts ahead of discovery and any
synthesis. The error carries a bounded 200-char stderr tail.

**Fails-before proved by reverting only the fix.** Neutering the added status
check (`if output.status.success()` → `if true`, tests untouched) made
`nonzero_encoder_preflight_stops_before_discovery` fail with "nonzero --version
must fail preflight". Restoring `main.rs` (md5 `336c0617…`) turned it green.
The test drives a real fake encoder first on `PATH` that exits nonzero, and
asserts the discovery closure never ran — matching the recorded expectation.
`encoder_preflight_stderr_uses_a_bounded_tail` covers the tail (including the
multi-byte case).

**Gates.** `cargo test -p render-catalog` green (21 pass, 1 ignored helper, plus
5 overlap tests); `cargo clippy -p render-catalog --all-targets -- -D warnings`
clean; `cargo fmt --all -- --check` clean.

## Notes

Static review only. The pass did not execute the application or tests.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
