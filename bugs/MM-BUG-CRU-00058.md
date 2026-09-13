# MM-BUG-CRU-00058 — Steinway legacy .wav aliases break the alias-dedup oracle, leaving the Python sample-tooling gate red

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** sample tooling / Steinway alias oracle
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
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:08:34Z, deltic:auto role=fix run=fix-20260913T195027Z-a9432425 branch=task/bug-MM-BUG-CRU-00058-run-fix-20260913T195027Z-a9432425 code=a93b59c18d20119e0ddc3491ffc8164163cc2ce1 gate=manual) -> Closed (2026-09-13T20:36:57Z, independent verify by Codex run=verify-20260913T203306Z-f5577e21: source-derived and legacy aliases are both covered)

## Observation

Split at independent verification of MM-BUG-KILN-00272 (2026-09-13, trunk 8b6a6f86). Fix 8244afb1 appended 27 legacy stem.wav -> stem.flac rows to crates/ferrosintesis-samples-vcsl-steinway ALIASES so pre-migration keys resolve. The existing KILN-00165 oracle SteinwayAliasDeduplicationTest.test_declared_aliases_exactly_cover_repeated_logical_sources (tools/ferrosintesis-samples/test_prepare.py:5992) requires ALIASES to equal exactly the duplicate-velocity aliases derived from the bake source map, so python3 -m unittest discover -s tools/ferrosintesis-samples fails (262 run, 1 failure). Reverting only ALIASES to 8244afb1^ turns that class green. Expected: the two contracts reconciled, e.g. the oracle derives the derived duplicates plus stem.wav -> stem.flac for every packaged file. Actual: the required Python gate is red.

## Fix

`a93b59c18d20119e0ddc3491ffc8164163cc2ce1` (`Fix Steinway alias manifest oracle`) extends the expected
Steinway manifest with one legacy `.wav` alias for every packaged `.flac` file, while
retaining the source-derived duplicate aliases. The oracle now derives both sets from the
canonical source map and the physical package list.

### Verification (closure) (2026-09-13, Codex, independent)

The focused `SteinwayAliasDeduplicationTest` passed all 4 tests. The full documented
`python -m unittest discover -s tools/ferrosintesis-samples` gate passed all 265 tests.

For a negative control, I temporarily returned only the source-derived aliases from
`steinway_packaged_alias_manifest`. The named regression failed with the recorded mismatch:
the committed manifest contained the legacy `.wav` compatibility rows that the old oracle
omitted. Restoring the derived legacy rows made the focused and full suites pass again, with
no remaining source diff.

## Notes
