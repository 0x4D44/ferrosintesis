# MM-BUG-KILN-00161 — Kawai package provenance maps two zones to wrong upstream labels

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample package / provenance
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T213933Z-p12724-n661330200-c1 branch=task/bug-MM-BUG-KILN-00161-run-fix-20260728T213933Z-p12724-n661330200-c1 code=b95a70f5e45d9729acab3756a4febc1eed2e4f4a gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green)

## Observation

Static reproduction: compare `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\PROVENANCE.md:38` with `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:723`. The packaged table says sounding A2 comes from source label A0 and sounding A3 comes from A1. The generator actually maps A2 to A1 and A#3 to A#2. The embedded filenames at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:13` and measured roots at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\sampler.rs:1373` corroborate the generator. This misidentifies the upstream source for 12 of 48 published WAVs; runtime audio and CC0 licensing are unaffected. Expected: packaged provenance exactly describes the source mapping used to bake every zone. Actual: two hand-transcribed rows contradict the generator from their original commit. Concrete fix: correct the rows to A2 -> A1 and A#3 -> A#2, then add a source-derived oracle comparing the packaged mapping with `_KAWAI_ZONE_LABEL`, including an intentionally wrong-row negative control.

## Fix

Code commit `b95a70f`. Corrected the two stale rows in the packaged Kawai
Selection table (`crates/ferrosintesis-samples-vcsl-kawai/PROVENANCE.md`) to
`A2 <- A1` and `A#3 <- A#2`, and added `KawaiProvenanceMappingTest` in
`tools/ferrosintesis-samples/test_prepare.py`. The oracle parses the packaged
Selection table and compares it with `prepare._KAWAI_ZONE_LABEL` (source-derived,
not a second hand-written list), with a wrong-row negative control.

## Notes

### Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Re-ran the recorded static comparison. All eight rows of the packaged Selection
table now match `prepare._KAWAI_ZONE_LABEL` exactly (C2<-C1, A2<-A1, C3<-C2,
A#3<-A#2, C4<-C3, A#4<-A#3, C5<-C4, C6<-C5); the reported `A2 <- A0` and
`A3 <- A1` rows are gone.

Fails-before proven: restoring the pre-fix blob (`git show b95a70f^:...`) over
the packaged `PROVENANCE.md` makes
`KawaiProvenanceMappingTest::test_packaged_selection_matches_the_bake_mapping`
fail on the A2/A#4 rows; the trunk file passes. Working tree restored
byte-identical afterwards.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
