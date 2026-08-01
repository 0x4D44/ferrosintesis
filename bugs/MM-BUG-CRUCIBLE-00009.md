# MM-BUG-CRUCIBLE-00009 — Catalog discovery drops filesystem errors and can silently omit inputs

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / discovery
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
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review) -> Fixed (2026-07-31T22:39:18Z, deltic:auto role=fix run=fix-20260731T223018Z-p26036-n683158100-c1 branch=task/bug-MM-BUG-CRUCIBLE-00009-run-fix-20260731T223018Z-p26036-n683158100-c1 code=86e7ecfa6defc03554b65be69d85936337349f58 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 789baed; fixer was Codex GPT-5.6-Sol)

## Observation

Catalog discovery and lyrics validation convert filesystem enumeration failures
into absence:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\crates\render-catalog\src\main.rs:480-487`
  flattens both a failed `read_dir` and failed directory entries.
- `main.rs:492-503` returns silently when a recursive directory cannot be opened
  and flattens failed entries.
- `main.rs:590-599` also flattens failed entries while validating lyrics
  sidecars.

If at least one sibling MIDI remains readable, the per-album scan can still
succeed. The recursive ownership scan can omit the same inaccessible entry, so
the renderer can exit successfully without rendering or reporting that input.
An unreadable orphan lyrics entry can likewise evade the sidecar guard.

**Expected:** an exhaustive catalog renderer fails closed and identifies the path
when it cannot enumerate an album, recursive ownership subtree, or lyrics
directory.

**Actual:** partial enumeration is indistinguishable from a smaller clean input
set.

## Fix

Make `sorted_midis` and `find_midis_recursive` return `Result`, propagate every
directory-open and entry-read error with path context, and replace `flatten()` on
I/O results in lyrics validation with explicit error propagation.

Add a regression through an injected directory-reader seam that yields one valid
entry and one error. Require discovery and sidecar validation to fail rather than
shrink their result. This is more portable than relying on host permission bits.

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `789baed` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-8-11`.

**Root cause addressed at the right layer.** `read_dir` failures and per-entry
failures now surface as `Result` with path context through `sorted_midis`,
`find_midis_recursive` and lyrics-sidecar validation; the three `flatten()` sites
named in the observation are gone. Discovery can no longer shrink silently.

**Fails-before proved by reverting only the fix.** I restored the swallow —
`directory_paths` back to `Ok(read_dir(dir)?.into_iter().flatten().collect())`,
keeping the tests — and both regressions failed:
`discovery_rejects_an_entry_error_after_a_valid_entry` ("entry failure must not
shrink discovery") and `lyrics_validation_rejects_an_entry_error_after_a_valid_entry`.
Restoring `main.rs` (md5 `336c0617…`) turned both green again.

**Gates.** `cargo test -p render-catalog` green (21 pass, 1 ignored helper, plus
5 overlap tests); `cargo clippy -p render-catalog --all-targets -- -D warnings`
clean; `cargo fmt --all -- --check` clean.

## Notes

Static review only. The pass did not execute the application or tests.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
