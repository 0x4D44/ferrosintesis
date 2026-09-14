# MM-BUG-CRU-00074 — Origin trunk quality gates fail on inventory tests and Clippy warnings

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** quality-gates
- **Raised:** 2026-09-13T20:58:35Z
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
- **State history:** Open (2026-09-13T20:58:35Z, raised via `deltic bugs new --land`) -> Fixed (2026-09-13T22:19:37Z, deltic:auto role=fix run=fix-20260913T221324Z-fccede5e branch=task/bug-MM-BUG-CRU-00074-run-fix-20260913T221324Z-fccede5e code=5a370050e32d31e5663cbe50b34633c28f1bc07c gate=manual) -> Closed (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: both inventory tests and all four recorded clippy sites are clean; reverting the delegation text and the archive split reproduces the failures)

## Observation

Observed on origin/main during MM-BUG-CRU-00060 verification: cargo test --workspace fails inventory::tests::every_public_sample_inventory_surface_is_complete_or_delegated and inventory::tests::every_generated_bake_output_family_is_inventory_validated; cargo clippy --workspace --all-targets -- -D warnings fails archive_boundary.rs:562 manual_pattern_char_comparison, midi.rs:1068 manual_repeat_n, parse_robustness.rs:175 manual_repeat_n, and payload.rs:434 filter_next. These are outside the current fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `5a370050`) by an agent other than the fixer.

**Original observation.** All six recorded failures are gone. `inventory::tests::every_public_sample_inventory_surface_is_complete_or_delegated` and `every_generated_bake_output_family_is_inventory_validated` pass in both the no-default and workspace runs. `cargo clippy --workspace --all-targets --locked -- -D warnings` exits 0, which covers `archive_boundary.rs:562`, `midi.rs:1068`, `parse_robustness.rs:175` and `payload.rs:434`. Only two of those sites are this commit's work: the repeat_n pair was fixed by `e75867d6` (MM-BUG-CRU-00055), the generated-bake oracle by `8c68e218` (MM-BUG-CRU-00065), and `payload.rs` last changed in `50701436`.

**Fails-before (method B).** Reverting the drumkit and orchestral `Cargo.toml` descriptions and the orchestral README's PROVENANCE pointer fails the public-surface test with three errors: both manifest descriptions 'name no packaged families', and the orchestral README names a partial family list. Separately, restoring the closure-based split in `has_parent_path_component` fails clippy with the manual char comparison lint at `archive_boundary.rs:562`. Both restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
