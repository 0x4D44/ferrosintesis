# MM-BUG-CRU-00073 — drumkit2 audio oracle's per-bank duration table is hand-maintained beside BANKS, so dropping a bank stays green

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample assets / drumkit2 audio validation
- **Raised:** 2026-09-13T19:32:32Z
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
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual found at independent verification of MM-BUG-KILN-00203 (2026-09-13, trunk 8b6a6f86). Fix ba9b3ff2 makes decoded_banks_are_valid_audio (crates/ferrosintesis-samples-drumkit2) check CRASH, SPLASH and CHINA with duration, a 0.85-0.92 peak band and an RMS floor, and its controls reject silent and impulse-only takes. But the per-bank duration table is written by hand next to BANKS, and nothing requires it to cover every BANKS entry: removing SPLASH from the table leaves decoded_banks_are_valid_audio green. That is the same omission class the bug was raised for. Expected: derive the checked set from BANKS, or assert the table covers every BANKS entry.

## Fix

<unfixed — raised only>

## Notes
