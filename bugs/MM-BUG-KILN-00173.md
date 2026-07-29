# MM-BUG-KILN-00173 — Concurrent drum-kit regenerations race fixed shared-cache temporary files

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / drum-kit cache
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260729T140318Z-p42048-n751314100-c1 branch=task/bug-MM-BUG-KILN-00173-run-fix-20260729T140318Z-p42048-n751314100-c1 code=c0a74497bf12a494bdc6173afba399726e2bed5a gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `9de9152`; regression proven to fail without the fix -- the pre-fix `fetch` shares one `.part` path (1 staging path, not 2) and its failing writer destroys the successful writer's entry (2 errors, not 1); repo gates green)

## Observation

Every worktree on one host shares the revision-keyed drum source cache at
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\prepare_drumkit.py:370`.
Concurrent regenerations use the same final and temporary names inside it.

The imported `fetch()` helper uses one fixed `<path>.part`, deletes an existing
part, downloads, then replaces the final path at
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\prepare.py:1250`.
The FLAC decoder independently uses one fixed `<path>.part.wav` and the same
delete/write/replace sequence at
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\prepare_drumkit.py:207`.

Static reproduction: start the documented drum-kit regeneration concurrently in
two worktrees while the shared cache is cold.

Expected: identical concurrent regenerations safely share, serialize, or build
independent cache entries.

Actual: either process can delete, replace, or clean up the other process's
active temporary path. At minimum this can fail one regeneration. Depending on
platform file-sharing behavior, it can also promote or consume a partial entry.
The fixed names are the defect; current committed package files are not evidence
for or against this race. No concurrent run was executed during this review.

## Fix

Use process-unique temporary files followed by atomic replacement. Add per-entry
locking if the platform needs it, and revalidate the winner after a concurrent
replace. Never delete another process's temporary path.

Add a two-writer regression for both the download and decoded-WAV cache paths,
plus a failure cleanup check that proves one writer cannot remove the other's
work.

## Notes

Kept separate from `MM-BUG-KILN-00172`: cache authentication and concurrent
publication have different triggers and fixes. Estimated effort: Small–Medium.
