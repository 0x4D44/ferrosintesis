# MM-BUG-CRUCIBLE-00010 — Nonzero encoder preflight is accepted before expensive catalog synthesis

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / encoder preflight
- **Raised:** 2026-07-31
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260731T224022Z-p70228-n873410000-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00010-run-fix-20260731T224022Z-p70228-n873410000-c1
- **Owner base:** c2ed18905edcb15910edef26d58c26fe39784c41
- **Owner fingerprint:** -
- **Owner since:** 2026-07-31T22:40:22Z
- **Owner until:** 2026-08-01T00:40:22Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review)

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

## Notes

Static review only. The pass did not execute the application or tests.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
