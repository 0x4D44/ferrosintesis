# MM-BUG-CRU-00074 — Origin trunk quality gates fail on inventory tests and Clippy warnings

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** quality-gates
- **Raised:** 2026-09-13T20:58:35Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T221324Z-fccede5e
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00074-run-fix-20260913T221324Z-fccede5e
- **Owner base:** 73544919aae8c3a336855296adfc468f709ce714
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T22:13:24Z
- **Owner until:** 2026-09-14T00:13:24Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T20:58:35Z, raised via `deltic bugs new --land`)

## Observation

Observed on origin/main during MM-BUG-CRU-00060 verification: cargo test --workspace fails inventory::tests::every_public_sample_inventory_surface_is_complete_or_delegated and inventory::tests::every_generated_bake_output_family_is_inventory_validated; cargo clippy --workspace --all-targets -- -D warnings fails archive_boundary.rs:562 manual_pattern_char_comparison, midi.rs:1068 manual_repeat_n, parse_robustness.rs:175 manual_repeat_n, and payload.rs:434 filter_next. These are outside the current fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

## Notes
