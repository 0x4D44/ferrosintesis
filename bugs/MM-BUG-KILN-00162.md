# MM-BUG-KILN-00162 — Kawai logical layer aliases duplicate one-third of packaged and decoded PCM

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample package / memory and package size
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T214613Z-p27608-n422372700-c1 branch=task/bug-MM-BUG-KILN-00162-run-fix-20260728T214613Z-p27608-n422372700-c1 code=364ca8f05dd1631ddb290d637a3842be2fc63d91 gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green)

## Observation

Read-only SHA-256 grouping of D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\samples found 16 byte-identical pairs. D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:731 deliberately maps pp RR2 and mf RR1 to source v2, and mf RR2 and f RR2 to source v3, across all eight zones. That musical mapping is valid, but D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:12 embeds every logical name as a separate physical WAV, adding 2,128,768 redundant packaged bytes. D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\sampler.rs:326 parses every entry into a fresh Vec<f32>, and prewarm reaches all six Kawai caches at :3170, retaining 4,256,128 avoidable decoded bytes plus 1,064,032 redundant sample conversions. Expected: logical aliases preserve the documented layer/RR behavior without duplicate physical or decoded payloads. Actual: one-third of the bank is duplicated on disk and in resident decoded memory. Concrete fix: retain exact-name compatibility through declared aliases, canonicalize packaged bytes, share the two duplicate decoded bank pairs, and add a source-derived oracle rejecting undeclared duplicate payloads. Linker constant merging and final release-binary savings remain unverified because this review did not build.

## Fix

Code commit `364ca8f`. Packages 32 unique WAVs and preserves all 48 logical
lookup names through an explicit `ALIASES` manifest, shares the two duplicate
decoded banks in `sampler.rs`, and teaches `gen_crate_lib.py` plus the crate's
own tests to reject undeclared duplicate payloads.

## Notes

### Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Re-ran the recorded SHA-256 grouping of
`crates/ferrosintesis-samples-vcsl-kawai/samples`: 32 files, 32 unique payloads,
zero duplicate groups (was 48 files with 16 byte-identical pairs). Packaged
bytes 4,257,536.

Exact-name compatibility holds: `FILE_COUNT` 32 + `ALIASES` 16 =
`LOGICAL_FILE_COUNT` 48, and `get()` resolves each alias to its canonical
payload.

Decoded duplication is gone: `kawai_mf()` now returns `kawai_pp_rr2()` and
`kawai_f_rr2()` returns `kawai_mf_rr2()`, asserted by `std::ptr::eq` in
`kawai_logical_aliases_share_decoded_banks`, so prewarm no longer builds the two
redundant banks.

Checked for a hazard the bug did not raise: sharing a decoded bank also shares
its zone root table. Compared the pre-fix roots of each aliased pair -- `mf` and
`pp_rr2` both read 65.12/109.50/130.47/231.60/261.05/464.18/521.86/1045.95, and
`f_rr2` and `mf_rr2` both read 65.51/109.95/131.34/233.31/261.90/466.39/522.87/
1046.29. Identical, so the substitution cannot move a rendered sample.

Adversarial check that the new guard is live: copying `kawai_C2_pp.wav` over
`kawai_C3_pp.wav` makes `aliases_resolve_without_duplicate_physical_payloads`
fail with `undeclared duplicate payloads: kawai_C2_pp.wav and kawai_C3_pp.wav`.
Sample restored byte-identical.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
