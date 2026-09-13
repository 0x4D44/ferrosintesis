# MM-BUG-CRU-00075 — Render-profile gate rejects numeric literals in CLI unit tests

- **State:** Fixed
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
- **State history:** Open (2026-09-13T23:02:32Z, raised via `deltic bugs new --land`) -> Fixed (2026-09-13T23:13:39Z, deltic:auto role=fix run=fix-20260913T230358Z-a0d5d160 branch=task/bug-MM-BUG-CRU-00075-run-fix-20260913T230358Z-a0d5d160 code=e677afe443e6034c930ab8e70f0d3ba71e351d41 gate=manual)

## Observation

cargo test -p ferrosintesis --lib render_profile::tests fails deterministically because the guard scans crates/ferrosintesis-cli/src/main.rs and flags the 500_000, 5.0, 99_999.0, and 60.0 literals in the landed clamp-warning unit test. The failure is pre-existing on origin/main and unrelated to the current CLI input-error fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

## Notes
