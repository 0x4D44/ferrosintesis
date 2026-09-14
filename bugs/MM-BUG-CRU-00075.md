# MM-BUG-CRU-00075 — Render-profile gate rejects numeric literals in CLI unit tests

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis render-profile test gate
- **Raised:** 2026-09-13T23:02:32Z
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
- **State history:** Open (2026-09-13T23:02:32Z, raised via `deltic bugs new --land`) -> Fixed (2026-09-13T23:13:39Z, deltic:auto role=fix run=fix-20260913T230358Z-a0d5d160 branch=task/bug-MM-BUG-CRU-00075-run-fix-20260913T230358Z-a0d5d160 code=e677afe443e6034c930ab8e70f0d3ba71e351d41 gate=manual) -> Closed (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: render_profile tests pass; restoring the inline literals reproduces the 500_000 source-scan failure)

## Observation

cargo test -p ferrosintesis --lib render_profile::tests fails deterministically because the guard scans crates/ferrosintesis-cli/src/main.rs and flags the 500_000, 5.0, 99_999.0, and 60.0 literals in the landed clamp-warning unit test. The failure is pre-existing on origin/main and unrelated to the current CLI input-error fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `e677afe4`) by an agent other than the fixer.

**Original observation.** All eight `render_profile::tests` pass in `cargo test --workspace --all-targets --locked` and in the no-default run.

**Fails-before (method B).** Restoring the literal `with_*` arguments in `reports_each_changed_option_against_the_effective_value` fails `the_shipping_entry_points_derive_the_profile_rather_than_restating_it`: 'crates/ferrosintesis-cli/src/main.rs passes the literal `500_000` to `with_sample_rate`'. Restored.

**Root cause check.** The guard is right and the literals were out-of-range test inputs, not a second statement of a library default. Naming them as consts cost the clamp test nothing: its expected warning strings still pin 500000, 5, 99999 and the 60 s echo.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
