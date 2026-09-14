# MM-BUG-CRU-00073 — drumkit2 audio oracle's per-bank duration table is hand-maintained beside BANKS, so dropping a bank stays green

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample assets / drumkit2 audio validation
- **Raised:** 2026-09-13T19:32:32Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213146Z-3c576c54
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00073-run-verify-20260914T213146Z-3c576c54
- **Owner base:** 1ffad60d0cbf1ff603e8eb863ce317afb570b0b2
- **Owner fingerprint:** sha256:346dc53d7a90a8c3c4ad8274b833342a040feead29fe7d7c828fbedf63727708
- **Owner since:** 2026-09-14T21:31:46Z
- **Owner until:** 2026-09-14T23:31:46Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:59:42Z, deltic:auto role=fix run=fix-20260913T215412Z-ac79c27b branch=task/bug-MM-BUG-CRU-00073-run-fix-20260913T215412Z-ac79c27b code=361044ea9be21a5888d359f33e2917833ed24f41 gate=manual)

## Observation

Residual found at independent verification of MM-BUG-KILN-00203 (2026-09-13, trunk 8b6a6f86). Fix ba9b3ff2 makes decoded_banks_are_valid_audio (crates/ferrosintesis-samples-drumkit2) check CRASH, SPLASH and CHINA with duration, a 0.85-0.92 peak band and an RMS floor, and its controls reject silent and impulse-only takes. But the per-bank duration table is written by hand next to BANKS, and nothing requires it to cover every BANKS entry: removing SPLASH from the table leaves decoded_banks_are_valid_audio green. That is the same omission class the bug was raised for. Expected: derive the checked set from BANKS, or assert the table covers every BANKS entry.

## Fix

<unfixed — raised only>

## Notes
