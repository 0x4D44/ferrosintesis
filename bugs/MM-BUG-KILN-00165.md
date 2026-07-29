# MM-BUG-KILN-00165 — Steinway logical aliases duplicate half of packaged and decoded PCM

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** Steinway sample package / memory and package size
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260728T224716Z-p56232-n275068800-c1 branch=task/bug-MM-BUG-KILN-00165-run-fix-20260728T224716Z-p56232-n275068800-c1 code=1b3a172 gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green)

## Observation

Read-only SHA-256 grouping of crates/ferrosintesis-samples-vcsl-steinway/samples found only 27 unique payloads among 54 files. For each of the nine zones, pp_rr2, mf, and f_rr2 are byte-identical, while mf_rr2 and f are byte-identical. This follows from tools/ferrosintesis-samples/prepare.py:701-709, where six logical dynamic/round-robin cells map to three upstream velocity layers.

Expected: the documented logical aliases preserve their names and musical behavior without storing and decoding duplicate PCM.

Actual: crates/ferrosintesis-samples-vcsl-steinway/src/lib.rs:12-229 embeds all 54 physical WAVs. The 27 redundant files add exactly 3,592,296 packaged bytes. crates/ferrosintesis/src/sampler.rs:1249-1349 constructs six independent decoded banks; prewarm reaches all six at crates/ferrosintesis/src/sampler.rs:3168-3181, retaining approximately 7,182,216 redundant decoded PCM bytes and repeating conversion work. Final release-executable linker deduplication was not measured in this read-only pass and is unverified.

Concrete fix: retain exact logical names through explicit aliases to 27 canonical payloads, share decoded Zone storage between aliased banks, and add a source-derived oracle that permits only declared duplicate aliases. Coordinate the class fix with open MM-BUG-KILN-00162, the Kawai sibling.

Estimated effort: Medium.

## Fix

Code commit `1b3a172`. Packages 27 unique WAVs, preserves all 54 logical names
through an explicit `ALIASES` manifest, shares the aliased decoded banks, and
adds the duplicate-payload rejection oracle.

## Notes

### Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Re-ran the recorded SHA-256 grouping of
`crates/ferrosintesis-samples-vcsl-steinway/samples`: 27 files, 27 unique
payloads, zero duplicate groups (was 54 files with only 27 unique). Packaged
bytes 3,592,296 -- exactly the redundancy the bug measured, removed.

Exact-name compatibility holds: `FILE_COUNT` 27 + `ALIASES` 27 =
`LOGICAL_FILE_COUNT` 54.

Decoded duplication is gone: `steinwayb_mf()` and `steinwayb_f_rr2()` both
return `steinwayb_pp_rr2()`, and `steinwayb_f()` returns `steinwayb_mf_rr2()`,
so the nine-zone bank now builds three decoded tables instead of six.

Same root-table hazard checked as on the Kawai sibling: pre-fix roots are
identical within each aliased group (`pp_rr2`/`mf`/`f_rr2` all
65.79/92.40/131.27/185.91/262.92/372.55/526.49/740.67/1049.34; `mf_rr2`/`f` both
65.67/92.39/131.39/185.95/262.84/372.49/526.67/743.63/1049.46), so the render is
unchanged.

Adversarial check: copying `steinwayb_C2_pp.wav` over `steinwayb_C3_pp.wav`
makes `aliases_resolve_without_duplicate_physical_payloads` fail with
`undeclared duplicate payloads`. Sample restored byte-identical.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
