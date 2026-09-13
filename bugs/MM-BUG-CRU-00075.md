# MM-BUG-CRU-00075 — Render-profile gate rejects numeric literals in CLI unit tests

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis render-profile test gate
- **Raised:** 2026-09-13T23:02:32Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T230358Z-a0d5d160
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00075-run-fix-20260913T230358Z-a0d5d160
- **Owner base:** 6001dd38c24c24a4e62ea18e9c4ca2b3118523a4
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T23:03:58Z
- **Owner until:** 2026-09-14T01:03:58Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T23:02:32Z, raised via `deltic bugs new --land`)

## Observation

cargo test -p ferrosintesis --lib render_profile::tests fails deterministically because the guard scans crates/ferrosintesis-cli/src/main.rs and flags the 500_000, 5.0, 99_999.0, and 60.0 literals in the landed clamp-warning unit test. The failure is pre-existing on origin/main and unrelated to the current CLI input-error fix.

Evidence fingerprint: `trunk-red:v1:ferrosintesis`


## Fix

<unfixed — raised only>

## Notes
