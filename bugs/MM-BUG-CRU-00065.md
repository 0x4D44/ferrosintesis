# MM-BUG-CRU-00065 — Bake-inventory source-scan oracle pins the pre-grouping main() loop text, so the correct KILN-00207 refactor turned cargo test red

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / sample-bake inventory oracle
- **Raised:** 2026-09-13T19:23:43Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T204241Z-ad8a5da9
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00065-run-fix-20260913T204241Z-ad8a5da9
- **Owner base:** 5c82da9a12b7e426cf76cbc3cadb9185c9a4c1bc
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T20:42:41Z
- **Owner until:** 2026-09-13T22:42:41Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:43Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Split at independent verification of MM-BUG-KILN-00207 (and its bearing on KILN-00182/00191), 2026-09-13, trunk 8b6a6f86. inventory::tests::every_generated_bake_output_family_is_inventory_validated (crates/ferrosintesis/src/inventory.rs:1238) requires prepare.py main() to contain the literal text '_validate_generated_output_inventory(family, expected)' and 'for family, expected in sorted(_family_output_sets().items()):'. Fix 2c65490f (KILN-00207) correctly regrouped validation by destination package via _family_output_groups(), removing both strings, without updating the oracle. cargo test -p ferrosintesis fails under both feature sets: 'main must validate every SELECTED family's packaged output — derived from the source tables — before using any of those tables'. Restoring the pre-2c65490f loop turns the oracle green and the two bass regressions red, pinning the cause. The behaviour is intact: SelectedFamilyPreflightTest passes on HEAD. Expected: the oracle recognises the grouped form, ideally without exact-text matching, with its adversarial self-tests re-checked.

## Fix

<unfixed — raised only>

## Notes
