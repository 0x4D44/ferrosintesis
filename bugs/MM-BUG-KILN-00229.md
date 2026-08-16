# MM-BUG-KILN-00229 — Fret-noise regeneration can publish a partial mixed bank after a late write failure

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** fret-noise sample generation / failure atomicity
- **Raised:** 2026-08-16T16:53:19Z
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
- **State history:** Open (2026-08-16T16:53:19Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

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
