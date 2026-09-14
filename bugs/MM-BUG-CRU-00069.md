# MM-BUG-CRU-00069 — Honky-tonk bake decodes to fixed intermediates in the shared honkytonk_fb temp directory

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent cache isolation
- **Raised:** 2026-09-13T19:26:11Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213601Z-139210ca
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00069-run-verify-20260914T213601Z-139210ca
- **Owner base:** 9977b9e498e8170c136d90b28260e9cf2d601891
- **Owner fingerprint:** sha256:5be59716993484d79f39fe3d731dbdc865696eac5c8cecc11ce313722710adec
- **Owner since:** 2026-09-14T21:36:01Z
- **Owner until:** 2026-09-14T23:36:01Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:39:08Z, deltic:auto role=fix run=fix-20260913T213306Z-f78d849d branch=task/bug-MM-BUG-CRU-00069-run-fix-20260913T213306Z-f78d849d code=d3cd6cd2ad352c761c2c52a094e21a5f010395ff gate=manual)

## Observation

Residual found at independent verification of MM-BUG-KILN-00261 (2026-09-13, trunk 8b6a6f86), by reading the code. The onset fix (9170b41b) moved MuseScore onset decode intermediates into per-run staging, but _bake_honkytonk (tools/ferrosintesis-samples/prepare.py:5543-5546) still decodes to the fixed name htsrc_<note>.wav inside the host-global gettempdir()/honkytonk_fb and reads it back immediately. Two concurrent honky-tonk regenerations can read each other's decoded WAV. The MuseScore-grand sibling is tracked separately as MM-BUG-KILN-00256. Expected: per-run private decode intermediates, as the clavinet and onset bakes now use.

## Fix

<unfixed — raised only>

## Notes
