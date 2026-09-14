# MM-BUG-KILN-00229 — Fret-noise regeneration can publish a partial mixed bank after a late write failure

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** fret-noise sample generation / failure atomicity
- **Raised:** 2026-08-16T16:53:19Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T214025Z-2eb751a6
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00229-run-verify-20260914T214025Z-2eb751a6
- **Owner base:** 0df2e3542d5ef3aa9cdbbdaf2328bd4875f7bda4
- **Owner fingerprint:** sha256:f59aa7f3f817b3ff975818146f03f6b66cf080da2a70326dff99b799070aaa28
- **Owner since:** 2026-09-14T21:40:25Z
- **Owner until:** 2026-09-14T23:40:25Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T16:53:19Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T05:41:55Z, deltic:auto role=fix run=fix-20260913T053018Z-56ab7513 branch=task/bug-MM-BUG-KILN-00229-run-fix-20260913T053018Z-56ab7513 code=b30f9fc89a0488fcd825b7ad71312de48789700a gate=manual) -> Open (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: the code fix works, but reverting main() to its direct-to-out_dir loop leaves all seven committed tests green, so the regression does not cover the fix) -> Fixed (2026-09-13T22:05:46Z, deltic:auto role=fix run=fix-20260913T220044Z-d005d852 branch=task/bug-MM-BUG-KILN-00229-run-fix-20260913T220044Z-d005d852 code=e71819f98707814bbcbe536c2a37d8cea3ad6ab5 gate=manual)

## Observation

`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\tools\ferrosintesis-samples\fretnoise_bake.py:299` generates the complete bank in memory and validates every generated payload against its pin before writing. That protects failures during source reading and transformation.

Publication is still non-transactional. At
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\tools\ferrosintesis-samples\fretnoise_bake.py:324`, the script loops over twelve final tracked paths and calls `Path.write_bytes` directly. Each call truncates its destination before the write completes. A disk-full error, interruption, or process termination can therefore truncate the current file; a later failure after earlier successful writes can leave a new prefix beside an old suffix during an intentional re-pinned bake.

**Static reproduction.** Start a deliberately changed, correctly re-pinned bake
and inject a write failure after one or more final paths have been replaced. The
completed prefix remains new and the untouched suffix remains old. Injecting the
failure inside one `write_bytes` call can also leave that destination partial.

**Expected.** A failed regeneration preserves the complete previous tracked bank.

**Actual.** Atomicity is per Python call at best, not per file or bank. Git makes
recovery possible and a successful deterministic rerun repairs the bank, so the
impact is Low. This review did not inject the destructive failure; the write
window follows directly from the final-path write sequence.

## Fix

Unfixed. Write all twelve outputs into an empty sibling staging directory,
validate exact inventory, hashes, and WAV structure there, then publish the bank
with backups and rollback if any replacement fails. Add negative controls for a
late staged write failure and a late final replacement failure; both must leave
every pre-existing destination byte-identical.

## Notes

Closed `MM-BUG-KILN-00063` fixed direct WAV writes in the shared
`prepare.py::write_wav_mono` helper. This custom NumPy bake does not use that
helper and retained its own direct-write path, so the defect is not a duplicate.

### Verification (reopen) (2026-09-13, Claude Opus 5, independent)

Checked on trunk `8b6a6f86` (fix `b30f9fc8`) by an agent other than the fixer.

**The code fix works.** A scratch scenario ran `fretnoise_bake.main()` in a temp repo against the real cuts and pins with a fake old bank: a late encode failure (7th file) and a late replacement failure (7th swap) both leave the old bank byte-identical on HEAD, and the same scenario on reversed `main()` changes 7 files.

**Why reopened (stop rule).** Reverting the root-cause hunk, `main()` encoding straight into `out_dir` instead of staging and publishing, leaves all 7 `FretNoiseBakeTests` green. No committed test drives `main()` in write mode, and `test_late_staged_write_failure_leaves_published_bank_unchanged` writes to a staging directory separate from `out_dir`, so it passes by construction. Only removing rollback from `publish_fretnoise_bank` reddens a test.

**Needed to close.** A regression that drives `main()` (or its publish path) with a late encode or replacement failure and asserts the previous bank is byte-identical.
