# MM-BUG-CRUCIBLE-00015 — amp-lab documentation targets a workspace that no longer exists

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / documentation
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T054807Z-p71432-n418791500-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00015-run-fix-20260801T054807Z-p71432-n418791500-c1
- **Owner base:** 9ec128131c77cb3301786fc8889d4ffaa078430c
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T05:48:07Z
- **Owner until:** 2026-08-01T07:48:07Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`)

## Observation

The advertised amp-lab commands are stale after the crate became a standalone workspace.
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\README.md:7`
says to run, lint, and test `-p amp-lab` from the root; lines 10-15 call it a root
workspace member and claim the integration gate excludes it. Root
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\Cargo.toml:32`
excludes the crate entirely, while
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\Cargo.toml:19`
declares its own workspace. The generator docstring at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\tools\make_backing_loop.py:15`
also says to run `python tools/make_backing_loop.py` from the root, where that path does
not exist.

Expected: copy-paste commands enter the standalone workspace or use `--manifest-path`,
and the gate description matches reality. Actual: four Cargo instructions and the
generator instruction misdirect maintainers. Daily reports noted this drift, but no
tracked bug or requirement covered it. Commands were not executed in this static pass.

## Fix

Document `cd crates/amp-lab` followed by local `cargo run --release`, `cargo clippy
--all-targets -- -D warnings`, and `cargo test`, or equivalent `--manifest-path`
commands. Correct the membership/gate explanation and the generator's root-relative path.

## Notes

Confirmed by the correctness and maintainability lenses and the devil's advocate.
