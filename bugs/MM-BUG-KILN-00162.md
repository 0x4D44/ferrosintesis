# MM-BUG-KILN-00162 — Kawai logical layer aliases duplicate one-third of packaged and decoded PCM

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample package / memory and package size
- **Raised:** 2026-07-28
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260728T214613Z-p27608-n422372700-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00162-run-fix-20260728T214613Z-p27608-n422372700-c1
- **Owner base:** c55a1ff0d2e83de3947b2fb478110f3a6ac30c25
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T21:46:13Z
- **Owner until:** 2026-07-28T23:46:13Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Read-only SHA-256 grouping of D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\samples found 16 byte-identical pairs. D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:731 deliberately maps pp RR2 and mf RR1 to source v2, and mf RR2 and f RR2 to source v3, across all eight zones. That musical mapping is valid, but D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:12 embeds every logical name as a separate physical WAV, adding 2,128,768 redundant packaged bytes. D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\sampler.rs:326 parses every entry into a fresh Vec<f32>, and prewarm reaches all six Kawai caches at :3170, retaining 4,256,128 avoidable decoded bytes plus 1,064,032 redundant sample conversions. Expected: logical aliases preserve the documented layer/RR behavior without duplicate physical or decoded payloads. Actual: one-third of the bank is duplicated on disk and in resident decoded memory. Concrete fix: retain exact-name compatibility through declared aliases, canonicalize packaged bytes, share the two duplicate decoded bank pairs, and add a source-derived oracle rejecting undeclared duplicate payloads. Linker constant merging and final release-binary savings remain unverified because this review did not build.

## Fix

<unfixed — raised only>

## Notes
