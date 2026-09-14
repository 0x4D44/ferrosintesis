# MM-BUG-CRU-00074 — Origin trunk quality gates fail on inventory tests and Clippy warnings

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** quality-gates
- **Raised:** 2026-09-13T20:58:35Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T212426Z-15a82fb8
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00074-run-verify-20260914T212426Z-15a82fb8
- **Owner base:** 639cce275e553800a1a78504f5205433020dcbbe
- **Owner fingerprint:** sha256:2776a1dc6a4694155a6f5ff285f039a1dc425bf66ef8360264e23466b6f20ca6
- **Owner since:** 2026-09-14T21:24:26Z
- **Owner until:** 2026-09-14T23:24:26Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T20:58:35Z, raised via `deltic bugs new --land`) -> Fixed (2026-09-13T22:19:37Z, deltic:auto role=fix run=fix-20260913T221324Z-fccede5e branch=task/bug-MM-BUG-CRU-00074-run-fix-20260913T221324Z-fccede5e code=5a370050e32d31e5663cbe50b34633c28f1bc07c gate=manual)

## Observation

Observed on origin/main during MM-BUG-CRU-00060 verification: cargo test --workspace fails inventory::tests::every_public_sample_inventory_surface_is_complete_or_delegated and inventory::tests::every_generated_bake_output_family_is_inventory_validated; cargo clippy --workspace --all-targets -- -D warnings fails archive_boundary.rs:562 manual_pattern_char_comparison, midi.rs:1068 manual_repeat_n, parse_robustness.rs:175 manual_repeat_n, and payload.rs:434 filter_next. These are outside the current fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

## Notes
