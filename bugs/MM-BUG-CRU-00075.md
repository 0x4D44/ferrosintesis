# MM-BUG-CRU-00075 — Render-profile gate rejects numeric literals in CLI unit tests

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis render-profile test gate
- **Raised:** 2026-09-13T23:02:32Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T212459Z-33b2354a
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00075-run-verify-20260914T212459Z-33b2354a
- **Owner base:** 145fec85e1b77df0d32c8ed9118a061d83de3993
- **Owner fingerprint:** sha256:ef442c42b4a655a0dbee02a97bf327069729e2eba7e9a9eea84f686c10c3ab4a
- **Owner since:** 2026-09-14T21:24:59Z
- **Owner until:** 2026-09-14T23:24:59Z
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
