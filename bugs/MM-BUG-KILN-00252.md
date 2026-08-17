# MM-BUG-KILN-00252 — FLAC migration tool can leave a partial mixed bank after a late failure

- **State:** Open
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
- **State history:** Open (2026-08-17T01:05:27Z, raised via `deltic bugs new`)

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

## Notes

Per-bank regeneration defects such as `MM-BUG-KILN-00229` and
`MM-BUG-KILN-00245` do not cover the shared migration tool's contradictory
whole-run safety contract.
