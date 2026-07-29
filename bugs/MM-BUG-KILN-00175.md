# MM-BUG-KILN-00175 — Companion drum-kit inventory test never compares packaged WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drum-kit2 inventory
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260729T142237Z-p72360-n516310600-c1 branch=task/bug-MM-BUG-KILN-00175-run-fix-20260729T142237Z-p72360-n516310600-c1 code=8ce254b4b5591ef78d297a8a55dbaa4360cf931d gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `9de9152`; regression proven to fail without the fix; confirmed independently by dropping a real unembedded WAV into the packaged `samples/` directory, which the oracle failed by name; repo gates green)

## Observation

The test named `inventory_matches_packaged_wavs` says it compares the generated
embedded table with the packaged directory, but it never reads `samples/`.

At
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\crates\ferrosintesis-samples-drumkit2\src\lib.rs:352`,
the test compares `SAMPLES.len()` with the hand-updated `FILE_COUNT`, deduplicates
names already in `SAMPLES`, and checks only those embedded byte slices. A new WAV
under `samples/` is invisible to every assertion there. The sibling core crate's
test reads the directory and compares exact names at
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\crates\ferrosintesis-samples-drumkit\src\lib.rs:878`.

Static adversarial case:

1. Extend the Python output plan and provenance with an accent bank and generate
   its WAVs.
2. Omit the documented Rust table-regeneration step.

The Python plan-vs-directory test remains green because both changed together.
The repo-wide provenance check remains green once the new family/count is
documented. This crate's test remains green because its `SAMPLES` and
`FILE_COUNT` stayed internally consistent. Cargo still packages the added WAVs
through `samples/**`, but `get`, `pcm`, and `BANKS` cannot reach them.

Expected: this test compares the exact `samples/*.wav` filename set with
`SAMPLES`.

Actual: it proves only that the generated Rust table is internally consistent.
The current 48 directory names and 48 table names do match; this is a confirmed
oracle defect, not a claim of current asset drift.

## Fix

Mirror the sibling crate's filesystem-derived test: enumerate and sort
`samples/*.wav`, compare the exact names and count with `SAMPLES`, and retain the
duplicate/table checks.

Add an adversarial fixture or mutation that adds an unembedded packaged WAV and
proves the oracle fails by name.

## Notes

No existing bug covers the companion crate's false inventory oracle. Estimated
effort: Small.
