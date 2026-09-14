# MM-BUG-CRU-00065 — Bake-inventory source-scan oracle pins the pre-grouping main() loop text, so the correct KILN-00207 refactor turned cargo test red

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / sample-bake inventory oracle
- **Raised:** 2026-09-13T19:23:43Z
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
- **State history:** Open (2026-09-13T19:23:43Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:53:01Z, deltic:auto role=fix run=fix-20260913T204241Z-ad8a5da9 branch=task/bug-MM-BUG-CRU-00065-run-fix-20260913T204241Z-ad8a5da9 code=8c68e218f1e6df052ebc08b0a7f00a2a27d22fde gate=manual) -> Closed (2026-09-14T21:41:42Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the structural oracle passes on the grouped main() and goes red both when reverted to the old text and when prepare.py drops the grouped validation)

## Observation

Split at independent verification of MM-BUG-KILN-00207 (and its bearing on KILN-00182/00191), 2026-09-13, trunk 8b6a6f86. inventory::tests::every_generated_bake_output_family_is_inventory_validated (crates/ferrosintesis/src/inventory.rs:1238) requires prepare.py main() to contain the literal text '_validate_generated_output_inventory(family, expected)' and 'for family, expected in sorted(_family_output_sets().items()):'. Fix 2c65490f (KILN-00207) correctly regrouped validation by destination package via _family_output_groups(), removing both strings, without updating the oracle. cargo test -p ferrosintesis fails under both feature sets: 'main must validate every SELECTED family's packaged output — derived from the source tables — before using any of those tables'. Restoring the pre-2c65490f loop turns the oracle green and the two bass regressions red, pinning the cause. The behaviour is intact: SelectedFamilyPreflightTest passes on HEAD. Expected: the oracle recognises the grouped form, ideally without exact-text matching, with its adversarial self-tests re-checked.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `8c68e218`) by an agent other than the fixer.

**Original observation.** `inventory::tests::every_generated_bake_output_family_is_inventory_validated` passes under both feature sets (no-default and workspace runs). The fix's new self-tests `validation_order_oracle_accepts_a_multiline_grouped_call` and `validation_order_oracle_ignores_comment_and_string_mentions` also pass.

**Fails-before (method B).** Restoring the two exact-text requirements (`_validate_generated_output_inventory(family, expected)` and `for family, expected in sorted(_family_output_sets().items()):`) fails the test on the current `prepare.py` with the recorded message: 'main must validate every SELECTED family's packaged output — derived from the source tables — before using any of those tables'. Restored.

**Adversarial check (the oracle still guards).** With the fixed oracle in place, deleting the grouped `_family_output_groups()` validation loop from `prepare.py` `main()` turns the same test red with the same message. So the oracle stopped matching one spelling without going vacuous. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
