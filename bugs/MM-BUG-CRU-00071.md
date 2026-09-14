# MM-BUG-CRU-00071 — Drum-kit publish_staged swaps files one at a time with no rollback

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** drum-kit sample generation / failure atomicity
- **Raised:** 2026-09-13T19:26:12Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213912Z-0f436e15
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00071-run-verify-20260914T213912Z-0f436e15
- **Owner base:** 8c2d0c67e6b82aaed38b1f95f961706b59585182
- **Owner fingerprint:** sha256:68372a3f12f27851eaff233559bdf0d105b72c86634ad85a5cfd421db4d6d9ad
- **Owner since:** 2026-09-14T21:39:12Z
- **Owner until:** 2026-09-14T23:39:12Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:26:12Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:56:01Z, deltic:auto role=fix run=fix-20260913T214837Z-82ee938b branch=task/bug-MM-BUG-CRU-00071-run-fix-20260913T214837Z-82ee938b code=df7b03d4dff0b84d138620d4f15cad89df1c5e6f gate=manual)

## Observation

Residual found at independent verification of MM-BUG-KILN-00283 (2026-09-13, trunk 8b6a6f86), by reading the code. Fix 82e6b571 makes tools prepare_drumkit.py publish FLAC-only banks and reject stale WAVs, but publish_staged moves each staged take into place with os.replace one file at a time and has no rollback. A failure mid-swap leaves a partly published two-package kit (drumkit and drumkit2). No committed test checks that a successful publish writes .flac names either. Expected: whole-kit transactional publication with rollback, like _publish_staged_flac_bank.

## Fix

<unfixed — raised only>

## Notes
