# MM-BUG-KILN-00252 — FLAC migration tool can leave a partial mixed bank after a late failure

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample tooling / FLAC conversion failure atomicity
- **Raised:** 2026-08-17T01:05:27Z
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
- **State history:** Open (2026-08-17T01:05:27Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:41:15Z, deltic:auto role=fix run=fix-20260913T162556Z-e0d0d513 branch=task/bug-MM-BUG-KILN-00252-run-fix-20260913T162556Z-e0d0d513 code=6723398953435e8e0d86a93113fa9b9ce8f9fc23 gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: main-level late encode and publish failures leave both banks byte-identical; in-place conversion and rollback reversals redden their tests)

## Observation

`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\tools\ferrosintesis-samples\to_flac.py:19-24`
promises that a mismatch aborts the whole run with nothing deleted. The conversion
loop at `to_flac.py:153-177` instead encodes and verifies one file, then immediately
deletes that source WAV before attempting later files. If a later encoder,
verification, process, interruption, or filesystem failure occurs, earlier files
have become FLAC while later files remain WAV; an encoder failure can also leave a
partial destination.

Expected: a failed conversion preserves the complete prior bank. Actual: the
committed migration tool can leave a partial mixed bank despite its stated safety
contract. The current tree has no eligible non-skipped WAV bank awaiting
conversion, so this is a latent tooling defect rather than evidence of present
asset corruption. Concrete fix: stage every output for one bank, verify the full
set and exact inventory, then publish the complete bank as a unit; clean incomplete
staging on failure and add a late-failure negative control. Static review only;
the tool was not run.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `67233989`) by an agent other than the fixer.

**Original observation re-run.** A scratch scenario ran `to_flac.main()` over two 3-WAV banks: a late encode failure (5th encode) returns rc=1 with nothing changed, and a late publication failure (second bank's 2nd swap) returns rc=1 and also rolls back the first, already-published bank.

**Fails-before (method B).** Restoring in-place encode-and-delete in `_stage_bank` fails `test_late_encode_failure...` on the snapshot; making `_rollback_bank` return immediately fails `test_late_publish_failure_restores_every_file`. Restored; all 4 `ToFlacBankPublicationTest` regressions pass on HEAD.

**Coverage note.** The cross-bank ordering in `main()` is correct but untested: publishing each bank inside the staging loop keeps all 4 tests green. Logged in `scratchpad.md`.

## Notes

Per-bank regeneration defects such as `MM-BUG-KILN-00229` and
`MM-BUG-KILN-00245` do not cover the shared migration tool's contradictory
whole-run safety contract.
