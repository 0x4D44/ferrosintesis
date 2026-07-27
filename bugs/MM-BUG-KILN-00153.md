# MM-BUG-KILN-00153 — Banjo regeneration deletes the bank before replacement is ready

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** banjo sample generation / reliability
- **Raised:** 2026-07-27
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
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The standalone banjo generator removes the complete tracked bank
before it proves that a valid replacement bank exists.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\banjo_extract.py:174`
unlinks every `banjo_*.wav`. Lines 177–186 then generate files sequentially, and
`write_wav16()` at lines 128–134 writes directly to each final path. A process
termination, disk error, or write exception after deletion leaves a missing or
partial tracked bank.

The output plan is also data-derived: lines 171–172 select whatever zones pass
the current decoder/QC thresholds, while line 188 only prints the count. Nothing
requires the documented exact set of 24 note names before deletion or
publication.

**Expected.** A failed or incomplete regeneration preserves the previously valid
bank. Only a complete, validated 24-file plan becomes visible at final paths.

**Actual.** Destructive deletion happens first, and no exact output-plan guard
runs.

**Concrete fix.** Generate every output in a sibling staging directory, validate
the exact 24 filenames and WAV contracts, then publish with atomic per-file
replacement. Do not unlink the old bank until the complete staged plan is ready.
Add injected-write-failure and missing-zone regressions that prove the old bank
survives.

## Fix

<unfixed — raised only>

## Notes

This is recoverable from Git and normal compilation fails if a required
`include_bytes!` target is missing, so severity is Low. It is a standalone-script
residual of the failure-atomicity class fixed for the shared writer in
MM-BUG-KILN-00063. Open MM-BUG-KILN-00145 overlaps only on the missing
output-inventory oracle; it does not cover the destructive publication path.
