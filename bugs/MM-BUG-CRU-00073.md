# MM-BUG-CRU-00073 — drumkit2 audio oracle's per-bank duration table is hand-maintained beside BANKS, so dropping a bank stays green

- **State:** Closed
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
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:59:42Z, deltic:auto role=fix run=fix-20260913T215412Z-ac79c27b branch=task/bug-MM-BUG-CRU-00073-run-fix-20260913T215412Z-ac79c27b code=361044ea9be21a5888d359f33e2917833ed24f41 gate=manual) -> Closed (2026-09-14T21:41:42Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the duration oracle now iterates BANKS; dropping splash from the bounds table fails both drumkit2 duration tests)

## Observation

Residual found at independent verification of MM-BUG-KILN-00203 (2026-09-13, trunk 8b6a6f86). Fix ba9b3ff2 makes decoded_banks_are_valid_audio (crates/ferrosintesis-samples-drumkit2) check CRASH, SPLASH and CHINA with duration, a 0.85-0.92 peak band and an RMS floor, and its controls reject silent and impulse-only takes. But the per-bank duration table is written by hand next to BANKS, and nothing requires it to cover every BANKS entry: removing SPLASH from the table leaves decoded_banks_are_valid_audio green. That is the same omission class the bug was raised for. Expected: derive the checked set from BANKS, or assert the table covers every BANKS entry.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `361044ea`) by an agent other than the fixer.

**Original observation.** The recorded mutation was removing SPLASH from the per-bank duration table. `decoded_banks_are_valid_audio` now loops over `BANKS` and looks bounds up by name, and `duration_bounds_cover_every_registered_bank_once` checks the table and `BANKS` cover each other exactly. Both pass in `cargo test --workspace --all-targets --locked`.

**Fails-before (method B).** Deleting the `("splash", 1.5, 2.25)` row fails both tests with 'splash has no duration bounds'. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
