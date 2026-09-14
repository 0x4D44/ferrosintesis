# MM-BUG-CRU-00066 — Five more packaged one-shots start far from silence and pass the continuity sweep

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample assets / onset continuity
- **Raised:** 2026-09-13T19:23:43Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213357Z-6d85e34d
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00066-run-verify-20260914T213357Z-6d85e34d
- **Owner base:** 6be06ad65f71da7a65d8d1c67c3a33b1c08c9fd2
- **Owner fingerprint:** sha256:40e98632f12604babb8c05f766ef15f9c2b8bc05c18efee9f1ffed94f7f3ae81
- **Owner since:** 2026-09-14T21:33:57Z
- **Owner until:** 2026-09-15T00:53:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:43Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:20:32Z, deltic:auto role=fix run=fix-20260913T205331Z-55b12432 branch=task/bug-MM-BUG-CRU-00066-run-fix-20260913T205331Z-55b12432 code=4f4f6d9e30eb903612b828e84352fd56e32830c3 gate=manual)

## Observation

Residual split at independent verification of MM-BUG-KILN-00215 (2026-09-13, trunk 8b6a6f86). The dulcimer fix (24807679) rebaked two assets and added a dulcimer-only frame-zero test, but the general packaged-onset sweep still lets a large attack mask a frame-zero step, as the record itself noted. A decode census of every packaged one-shot (1015 files, clavinet excluded) found frame-zero values far from silence in: headroom_C4_pp (-1235), headroom_F#3_pp (-1087), orchestral steel_E4 (-1402), strings cellosolo_A3_f (+1882), strings cellosolo_C4_f (+1654). All pass the general sweep and none is in any bug record. They end at silence, so they look like one-shots rather than loops. Expected: packaged one-shots enter from silence, and a general frame-zero oracle covers every bank.

## Fix

<unfixed — raised only>

## Notes
