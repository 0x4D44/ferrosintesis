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
- **Attempts:** fix=0, doubt=1, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T091113Z-p9812-n303128100-c63 branch=task/bug-MM-BUG-KILN-00153-run-fix-20260727T091113Z-p9812-n303128100-c63 code=2f0e6ee818b19768449e426e0b86131fed4c4afb gate=python model=codex@xhigh) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T183302Z-p9812-n667926500-c113 verified_fix_run=fix-20260727T091113Z-p9812-n303128100-c63 verdict=doubt reason=symptom-is-gone-and-the-root-cause-is-properly-addressed-and-all-5-cargo-gate-st model=claude)

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

Banjo extraction now writes into a sibling staging directory and derives the
exact expected 24-file inventory from both the sample crate and sampler table.
It validates every staged file as non-empty mono 16-bit PCM at 44.1 kHz before
publishing anything.

Publication backs up the current bank, atomically replaces each file, and rolls
the complete bank back if any replacement or obsolete-file removal fails.
Obsolete files are removed only after all expected replacements succeed.

Root cause: generation and publication were interleaved. The script deleted the
current bank before proving that the selected zones formed a complete, valid
replacement.

Regression coverage:

- `test_banjo_extract.py`: 3/3 passed, including a missing-zone rejection,
  injected fifth-replacement failure with byte-for-byte rollback, and the
  successful replacement/removal path.
- Full Python discovery under `tools/ferrosintesis-samples`: 93/93 passed.
- `python -m py_compile tools/ferrosintesis-samples/banjo_extract.py
  tools/ferrosintesis-samples/test_banjo_extract.py`: passed.

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T183302Z-p9812-n667926500-c113 verified_fix_run=fix-20260727T091113Z-p9812-n303128100-c63 verdict=doubt)

Verifier note: Symptom is gone and the root cause is properly addressed, and all 5 cargo gate steps are green - but this sandbox denies every 'python <args>' call, so I could not observe the regression test or the python gate step actually passing; needs one command run by someone with python permission. — Ledger: bugs/MM-BUG-KILN-00153.md. (1) ORIGINAL OBSERVATION REPRODUCED then confirmed gone: 'git show 4da2b26^:tools/ferrosintesis-samples/banjo_extract.py' shows main() ran `for f in OUT.glob("banjo_*.wav"): f.unlink()` BEFORE generation and then write_wav16() straight to final paths, with no output-plan ...

## Notes

This is recoverable from Git and normal compilation fails if a required
`include_bytes!` target is missing, so severity is Low. It is a standalone-script
residual of the failure-atomicity class fixed for the shared writer in
MM-BUG-KILN-00063. Open MM-BUG-KILN-00145 overlaps only on the missing
output-inventory oracle; it does not cover the destructive publication path.
