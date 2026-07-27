# MM-BUG-KILN-00153 — Banjo regeneration deletes the bank before replacement is ready

- **State:** Fixed
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00153-run-fix-20260727T091113Z-p9812-n303128100-c63-code-1785144242660
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T091113Z-p9812-n303128100-c63 branch=task/bug-MM-BUG-KILN-00153-run-fix-20260727T091113Z-p9812-n303128100-c63 code=843604ee70ee gate=cargo model=codex@xhigh)

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

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T091113Z-p9812-n303128100-c63 code=843604ee70ee gate=cargo)

Agent-reported summary: Fixed MM-BUG-KILN-00153 by changing the standalone banjo extractor so regeneration is staged and validated before tracked bank files are replaced. The old implementation selected whatever zones survived QC, deleted every existing banjo WAV, and wrote directly to final paths, so a write failure or missing zone could leave the bank missing or partial. The new path derives the expected 24-file inventory from the sample crate and sampler table, validates staged WAV names and mono 16-bit 44.1 kHz contracts, then publishes with atomic per-file replacement. I added a focused Rust source-level regression that failed on the original delete-before-write shape and passes on the staged publication contr

Root cause: banjo_extract.py mixed generation and publication: it deleted the existing banjo_*.wav files before validating a complete replacement plan and before write_wav16 had succeeded for all outputs.

Changed:
- tools/ferrosintesis-samples/banjo_extract.py: added derived exact-inventory validation, staged generation, WAV-contract checks, and post-validation per-file rep
- crates/ferrosintesis/src/sample_tools.rs and crates/ferrosintesis/src/lib.rs: added focused regression coverage for the banjo extractor publication contract.

Tests:
- Reproduced original observation by source-order check: f.unlink() preceded direct final-path write_wav16(OUT / ...) and no EXPECTED_BANJO_FILES guard existed.
- $null | deltic timeout 180 cargo test -p ferrosintesis --no-default-features banjo_extract
- deltic timeout 60 cargo fmt -p ferrosintesis --check
- git diff --check

Left alone:
- bugs/ ledger, Cargo.toml, Cargo.lock, and shipped sample WAVs were not edited.

## Notes

This is recoverable from Git and normal compilation fails if a required
`include_bytes!` target is missing, so severity is Low. It is a standalone-script
residual of the failure-atomicity class fixed for the shared writer in
MM-BUG-KILN-00063. Open MM-BUG-KILN-00145 overlaps only on the missing
output-inventory oracle; it does not cover the destructive publication path.
