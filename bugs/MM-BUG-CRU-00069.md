# MM-BUG-CRU-00069 — Honky-tonk bake decodes to fixed intermediates in the shared honkytonk_fb temp directory

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent cache isolation
- **Raised:** 2026-09-13T19:26:11Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T213306Z-f78d849d
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00069-run-fix-20260913T213306Z-f78d849d
- **Owner base:** 39d87ecfd8d449621b870612a6355eafe41b094f
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T21:33:06Z
- **Owner until:** 2026-09-13T23:33:06Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual found at independent verification of MM-BUG-KILN-00261 (2026-09-13, trunk 8b6a6f86), by reading the code. The onset fix (9170b41b) moved MuseScore onset decode intermediates into per-run staging, but _bake_honkytonk (tools/ferrosintesis-samples/prepare.py:5543-5546) still decodes to the fixed name htsrc_<note>.wav inside the host-global gettempdir()/honkytonk_fb and reads it back immediately. Two concurrent honky-tonk regenerations can read each other's decoded WAV. The MuseScore-grand sibling is tracked separately as MM-BUG-KILN-00256. Expected: per-run private decode intermediates, as the clavinet and onset bakes now use.

## Fix

<unfixed — raised only>

## Notes
