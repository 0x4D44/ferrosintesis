# MM-BUG-CRU-00068 — Freesound and Eastman source intakes copy into the shared vsco2ce_src temp directory with no lock or per-run path

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent source isolation
- **Raised:** 2026-09-13T19:26:11Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T212631Z-c8f1d4e4
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00068-run-verify-20260914T212631Z-c8f1d4e4
- **Owner base:** 4b4ec88e3b6e87d61b23a13b423de57e9aed5a07
- **Owner fingerprint:** sha256:0a4a543d39c5da69241666a1b315ef2535cdfcdd1abf2d4304e707c764ce3d69
- **Owner since:** 2026-09-14T21:26:31Z
- **Owner until:** 2026-09-14T23:26:31Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:45:03Z, deltic:auto role=fix run=fix-20260913T212430Z-44a85e6e branch=task/bug-MM-BUG-CRU-00068-run-fix-20260913T212430Z-44a85e6e code=d44a74e37c6fec84052d83eac7bb713962f44ea7 gate=manual)

## Observation

Residual found at independent verification of MM-BUG-CRU-00049 (2026-09-13, trunk 8b6a6f86), by reading the code. The mandolin fix (0179cee7) removed its shared staging copy, but ensure_freesound_sources (tools/ferrosintesis-samples/prepare.py:1739) and ensure_eastman_sources (prepare.py:1758) still shutil.copyfile committed sources into the host-global vsco2ce_src temp directory under fixed names, with no lock and no per-run directory. Two concurrent --only=rhodes/dulcimer/musicbox/bottle/eastpick/eastpluck regenerations can therefore read each other's copies, the same defect shape CRU-00049 fixed for mandolin. Expected: bakes read committed sources directly or from a per-run private directory.

## Fix

<unfixed — raised only>

## Notes
