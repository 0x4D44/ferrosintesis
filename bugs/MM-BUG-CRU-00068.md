# MM-BUG-CRU-00068 — Freesound and Eastman source intakes copy into the shared vsco2ce_src temp directory with no lock or per-run path

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent source isolation
- **Raised:** 2026-09-13T19:26:11Z
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
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual found at independent verification of MM-BUG-CRU-00049 (2026-09-13, trunk 8b6a6f86), by reading the code. The mandolin fix (0179cee7) removed its shared staging copy, but ensure_freesound_sources (tools/ferrosintesis-samples/prepare.py:1739) and ensure_eastman_sources (prepare.py:1758) still shutil.copyfile committed sources into the host-global vsco2ce_src temp directory under fixed names, with no lock and no per-run directory. Two concurrent --only=rhodes/dulcimer/musicbox/bottle/eastpick/eastpluck regenerations can therefore read each other's copies, the same defect shape CRU-00049 fixed for mandolin. Expected: bakes read committed sources directly or from a per-run private directory.

## Fix

<unfixed — raised only>

## Notes
