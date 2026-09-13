# MM-BUG-CRU-00058 — Steinway legacy .wav aliases break the alias-dedup oracle, leaving the Python sample-tooling gate red

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** sample tooling / Steinway alias oracle
- **Raised:** 2026-09-13T19:22:42Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T195027Z-a9432425
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00058-run-fix-20260913T195027Z-a9432425
- **Owner base:** 4514551f8dccb0c1b9ee5d7c0e9ae2c4df0fd282
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T19:50:27Z
- **Owner until:** 2026-09-13T21:50:27Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Split at independent verification of MM-BUG-KILN-00272 (2026-09-13, trunk 8b6a6f86). Fix 8244afb1 appended 27 legacy stem.wav -> stem.flac rows to crates/ferrosintesis-samples-vcsl-steinway ALIASES so pre-migration keys resolve. The existing KILN-00165 oracle SteinwayAliasDeduplicationTest.test_declared_aliases_exactly_cover_repeated_logical_sources (tools/ferrosintesis-samples/test_prepare.py:5992) requires ALIASES to equal exactly the duplicate-velocity aliases derived from the bake source map, so python3 -m unittest discover -s tools/ferrosintesis-samples fails (262 run, 1 failure). Reverting only ALIASES to 8244afb1^ turns that class green. Expected: the two contracts reconciled, e.g. the oracle derives the derived duplicates plus stem.wav -> stem.flac for every packaged file. Actual: the required Python gate is red.

## Fix

<unfixed — raised only>

## Notes
