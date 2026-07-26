# MM-BUG-KILN-00113 — Core provenance assigns the upright bank to the wrong GM program

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** core sample package / provenance
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-core/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — corrected the shipped VSCO upright mapping to zero-based GM 0) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: `crates/ferrosintesis-samples-core/PROVENANCE.md:12` now reads "Upright piano (GM 0) onsets", consistent with the zero-based convention its violin GM40 and flute GM73 neighbours already used, and with `make_uncorrected(0)` dispatching to `sampler::piano_bank` while zero-based GM 1 continues to reach the separate VCSL Kawai bank. The false asset-to-program mapping a package auditor would have read is gone. The derived provenance inventory oracle passes for all packaged families.)

## Observation

**Symptom.** The package-facing table at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis-samples-core\PROVENANCE.md:12`
identifies `piano_*` as “Upright piano (GM 1) onsets”.

This table uses the synthesizer's zero-based program numbering: the next rows
correctly call violin GM40 and flute GM73, matching their runtime arms. Under
that convention the piano row is wrong. Current dispatch assigns the VSCO
upright `piano_bank` to program 0 at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\voices.rs:12962-12976`.
Program 1 uses the separate VCSL Kawai bank at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\voices.rs:12978-12992`.

**Expected.** Packaged provenance identifies the bank's current consumer as
GM0 Acoustic Grand, consistently with the other zero-based rows.

**Actual.** It identifies the bank as GM1 Bright Acoustic, whose runtime uses a
different package. This does not change audio, but it gives published-package
auditors and maintainers a false asset-to-program mapping.

## Fix

Change the row to “Upright piano, GM0 default onsets”, or remove the mutable GM
routing label and describe only the source instrument if provenance is not
intended to track consumer dispatch.

Estimated effort: Trivial.

## Resolution — 2026-07-26

The packaged provenance now identifies `piano_*` as the upright piano onset
bank for zero-based GM 0. This matches `make_uncorrected(0)`, which dispatches
to `sampler::piano_bank`; zero-based GM 1 continues to dispatch to the separate
VCSL Kawai bank.

## Verification — 2026-07-26

- The focused provenance inventory oracle passed for all packaged sample
  families and their documented file counts.
- `cargo package --list --allow-dirty` for
  `ferrosintesis-samples-core` includes the corrected `PROVENANCE.md`.
- Formatting and `git diff --check` passed.

## Notes

No external registry archive was inspected. The confirmed defect is in the
package-facing `PROVENANCE.md` that the manifest includes; no claim is made
about whether this exact revision has already been published.
