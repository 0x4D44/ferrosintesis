# MM-BUG-CRU-00064 — Clavinet reachable-prefix trim leaves dead constants and trips the banks_parse 20000-frame floor

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / clavinet sample bank
- **Raised:** 2026-09-13T19:23:18Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T210310Z-0232661d
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00064-run-verify-20260913T210310Z-0232661d
- **Owner base:** 61d22b82c43cf9791fc040aec35726bcc7be8855
- **Owner fingerprint:** sha256:7de46bd41119d630c7a5f46f4a97781475ab90b53ed725312985a4bda0277ccf
- **Owner since:** 2026-09-13T21:03:10Z
- **Owner until:** 2026-09-13T23:03:10Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:18Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:50:24Z, deltic:auto role=fix run=fix-20260913T203820Z-89d5ef45 branch=task/bug-MM-BUG-CRU-00064-run-fix-20260913T203820Z-89d5ef45 code=1f36e1dedc24d6cb8920435bc042f7c66375181b gate=manual)

## Observation

Split at independent verification of MM-BUG-KILN-00219 (2026-09-13, trunk 8b6a6f86). Fix 6ee2af43 trimmed all 11 clavinet assets to their 19,849-frame reachable prefix (verified exact prefix, identical loop points, 1,485 bit-identical renders). Two gate failures remain. (1) CLAVINET_RUNTIME_GUARD_FRAMES and CLAVINET_REACH_FRAMES (crates/ferrosintesis/src/sampler.rs:5538, 5540) are cfg(feature = "embedded-samples") but used only by a test, so cargo clippy --workspace --all-targets --locked -- -D warnings fails with dead_code. (2) sampler::tests::banks_parse, whose exhaustive sweep (e0d68e70, MM-BUG-CRUCIBLE-00041) was already on the fix's parent, now fails 'clavinet_bank: zone too short: 19849 (minimum 20000)' in cargo test --workspace. The runtime never reads past frame 17,841, so the generic 20,000 floor, not the trim, is what needs a clavinet exception. Expected: constants gated with their only user, and a derived clavinet floor in banks_parse.

## Fix

<unfixed — raised only>

## Notes
