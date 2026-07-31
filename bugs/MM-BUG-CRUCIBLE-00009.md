# MM-BUG-CRUCIBLE-00009 — Catalog discovery drops filesystem errors and can silently omit inputs

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / discovery
- **Raised:** 2026-07-31
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260731T223018Z-p26036-n683158100-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00009-run-fix-20260731T223018Z-p26036-n683158100-c1
- **Owner base:** 763a2a987a873525b7d2e369870f25df3ef2fd3b
- **Owner fingerprint:** -
- **Owner since:** 2026-07-31T22:30:18Z
- **Owner until:** 2026-08-01T00:30:18Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review)

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

## Notes

Static review only. The pass did not execute the application or tests.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
