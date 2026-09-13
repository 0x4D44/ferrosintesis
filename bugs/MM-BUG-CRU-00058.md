# MM-BUG-CRU-00058 — Steinway legacy .wav aliases break the alias-dedup oracle, leaving the Python sample-tooling gate red

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** sample tooling / Steinway alias oracle
- **Raised:** 2026-09-13T19:22:42Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T203306Z-f5577e21
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00058-run-verify-20260913T203306Z-f5577e21
- **Owner base:** fc12f9461ec70c97be243d1500ce62e01ee5d051
- **Owner fingerprint:** sha256:f78ae098f7d4eb513b0d28308d9f536ee8c7c991041bb67a2fd90963c6b6c577
- **Owner since:** 2026-09-13T20:33:06Z
- **Owner until:** 2026-09-13T22:33:06Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:08:34Z, deltic:auto role=fix run=fix-20260913T195027Z-a9432425 branch=task/bug-MM-BUG-CRU-00058-run-fix-20260913T195027Z-a9432425 code=a93b59c18d20119e0ddc3491ffc8164163cc2ce1 gate=manual)

## Observation

Split at independent verification of MM-BUG-KILN-00272 (2026-09-13, trunk 8b6a6f86). Fix 8244afb1 appended 27 legacy stem.wav -> stem.flac rows to crates/ferrosintesis-samples-vcsl-steinway ALIASES so pre-migration keys resolve. The existing KILN-00165 oracle SteinwayAliasDeduplicationTest.test_declared_aliases_exactly_cover_repeated_logical_sources (tools/ferrosintesis-samples/test_prepare.py:5992) requires ALIASES to equal exactly the duplicate-velocity aliases derived from the bake source map, so python3 -m unittest discover -s tools/ferrosintesis-samples fails (262 run, 1 failure). Reverting only ALIASES to 8244afb1^ turns that class green. Expected: the two contracts reconciled, e.g. the oracle derives the derived duplicates plus stem.wav -> stem.flac for every packaged file. Actual: the required Python gate is red.

## Fix

<unfixed — raised only>

## Notes
