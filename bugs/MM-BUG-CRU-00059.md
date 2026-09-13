# MM-BUG-CRU-00059 — Parent README still says five of these ten attribution banks, and the NOTICE count oracle only reads numbers before three phrases

- **State:** Fixed
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
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:13:52Z, deltic:auto role=fix run=fix-20260913T200524Z-659a531d branch=task/bug-MM-BUG-CRU-00059-run-fix-20260913T200524Z-659a531d code=6475418989789eea7c88d1a2b828f06be19a5e59 gate=manual)

## Observation

Split at independent verification of MM-BUG-CRUCIBLE-00038 (2026-09-13, trunk 8b6a6f86). Fix d975f7bb removed stale counts from NOTICE, licensing.rs and lib.rs, and the derived set is 9 attribution-bearing banks. crates/ferrosintesis/README.md:252 still says 'five of these ten' above a table that now has 9 rows. The new oracle notice_attribution_count_oracle_rejects_stale_count only checks a number immediately before three fixed phrases: a NOTICE edited to say 'index of ten attribution-bearing crates' after those phrases stayed green. Expected: no stale count anywhere in the shipped attribution prose, and an oracle that rejects any number disagreeing with the derived set.

## Fix

<unfixed — raised only>

## Notes
