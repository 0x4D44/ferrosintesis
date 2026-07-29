# MM-REQ-KILN-00176 — Accent drum-bank descriptors must derive from the regeneration manifest

- **State:** Draft
- **Priority:** Could
- **Area:** sample generation / accent drum-bank descriptors
- **Raised:** 2026-07-29
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-29, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The system must derive or machine-check every accent drum-bank descriptor against
the regeneration manifest: family, owning package, velocity upper bounds,
round-robin count, first sample index, and membership in the public bank registry.

## Notes

`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\prepare_drumkit.py:84`
defines the generated banks and their source-SFZ metadata.
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\crates\ferrosintesis-samples-drumkit2\src\lib.rs:234`
repeats those facts as four independent Rust `Bank` descriptors and a registry.
The current values agree.

The parity oracle at
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\test_prepare_drumkit.py:13`
filters to the core package and checks documentation stems, not the companion
Rust descriptors. Sparse crate tests do not cover every velocity boundary or
registry uniqueness. A future SFZ split, round-robin, package, or ordering change
can therefore leave the Rust selector stale after a successful regeneration.

A suitable Gate-1 oracle should derive the two-package descriptor projection from
the Python manifest and compare it with the Rust definitions. It should include
negative controls for a changed middle velocity bound, a duplicated same-sized
registry bank, and an incorrect first index.

Proposed priority: Could. Proposed flow: light. Estimated effort: Small–Medium.
