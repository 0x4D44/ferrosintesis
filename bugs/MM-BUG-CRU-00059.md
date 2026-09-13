# MM-BUG-CRU-00059 — Parent README still says five of these ten attribution banks, and the NOTICE count oracle only reads numbers before three phrases

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** licensing / attribution documentation
- **Raised:** 2026-09-13T19:22:42Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:13:52Z, deltic:auto role=fix run=fix-20260913T200524Z-659a531d branch=task/bug-MM-BUG-CRU-00059-run-fix-20260913T200524Z-659a531d code=6475418989789eea7c88d1a2b828f06be19a5e59 gate=manual) -> Closed (2026-09-13T20:46:48Z, independent verify by Codex run=verify-20260913T204032Z-f2e73c9c: attribution counts are derived and stale compound prose is rejected)

## Observation

Split at independent verification of MM-BUG-CRUCIBLE-00038 (2026-09-13, trunk 8b6a6f86). Fix d975f7bb removed stale counts from NOTICE, licensing.rs and lib.rs, and the derived set is 9 attribution-bearing banks. crates/ferrosintesis/README.md:252 still says 'five of these ten' above a table that now has 9 rows. The new oracle notice_attribution_count_oracle_rejects_stale_count only checks a number immediately before three fixed phrases: a NOTICE edited to say 'index of ten attribution-bearing crates' after those phrases stayed green. Expected: no stale count anywhere in the shipped attribution prose, and an oracle that rejects any number disagreeing with the derived set.

## Fix

`6475418989789eea7c88d1a2b828f06be19a5e59` (`fix(MM-BUG-CRU-00059): derive attribution count checks`)
removes the stale “five of these ten” README prose and generalizes the count oracle to
shipped attribution prose. It scans near the attribution-bearing phrase, while preserving
the three existing NOTICE obligation phrases, and applies the check to both README and NOTICE.

### Verification (closure) (2026-09-13, Codex, independent)

All 16 `licensing::tests::` passed, including `notice_attribution_count_oracle_rejects_stale_count`,
`readme_names_every_attribution_bearing_sample_bank`, and
`parent_notice_is_packaged_and_names_every_attribution_bearing_bank`. `cargo fmt --all -- --check`
also passed.

For a negative control, I removed the new attribution-bearing scan. The hidden-count fixture
then failed as expected: it found 0 mismatches instead of 1. Restoring the scan made all
16 licensing tests pass again with no source diff remaining.

## Notes
