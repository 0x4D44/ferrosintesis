# MM-BUG-CRU-00064 — Clavinet reachable-prefix trim leaves dead constants and trips the banks_parse 20000-frame floor

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / clavinet sample bank
- **Raised:** 2026-09-13T19:23:18Z
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
- **State history:** Open (2026-09-13T19:23:18Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:50:24Z, deltic:auto role=fix run=fix-20260913T203820Z-89d5ef45 branch=task/bug-MM-BUG-CRU-00064-run-fix-20260913T203820Z-89d5ef45 code=1f36e1dedc24d6cb8920435bc042f7c66375181b gate=manual) -> Closed (2026-09-14T21:41:42Z, independent verify by Claude Opus 5 on trunk 1d87b00f: workspace clippy clean and banks_parse passes; reverting the cfg and the derived clavinet floor reproduces both recorded failures)

## Observation

Split at independent verification of MM-BUG-KILN-00219 (2026-09-13, trunk 8b6a6f86). Fix 6ee2af43 trimmed all 11 clavinet assets to their 19,849-frame reachable prefix (verified exact prefix, identical loop points, 1,485 bit-identical renders). Two gate failures remain. (1) CLAVINET_RUNTIME_GUARD_FRAMES and CLAVINET_REACH_FRAMES (crates/ferrosintesis/src/sampler.rs:5538, 5540) are cfg(feature = "embedded-samples") but used only by a test, so cargo clippy --workspace --all-targets --locked -- -D warnings fails with dead_code. (2) sampler::tests::banks_parse, whose exhaustive sweep (e0d68e70, MM-BUG-CRUCIBLE-00041) was already on the fix's parent, now fails 'clavinet_bank: zone too short: 19849 (minimum 20000)' in cargo test --workspace. The runtime never reads past frame 17,841, so the generic 20,000 floor, not the trim, is what needs a clavinet exception. Expected: constants gated with their only user, and a derived clavinet floor in banks_parse.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `1f36e1de`) by an agent other than the fixer.

**Original observation.** Both recorded failures are gone. `cargo clippy --workspace --all-targets --locked -- -D warnings` exits 0, and `sampler::tests::banks_parse` passes in `cargo test --workspace --all-targets --locked`.

**Fails-before (method B).** Restoring `#[cfg(feature = "embedded-samples")]` on `CLAVINET_RUNTIME_GUARD_FRAMES` and `CLAVINET_REACH_FRAMES` fails `cargo clippy -p ferrosintesis --lib` with 'constant ... is never used' at `sampler.rs:5538` and `:5540`. Removing the `clavinet_bank` rule fails `banks_parse` with the recorded 'clavinet_bank: zone too short: 19849 (minimum 20000)'. Both restored.

**Root cause check.** The new floor is derived, not hand-picked: `CLAVINET_REACH_FRAMES - 1` = (0.34 s + 0.11 s) x 44 100 + 4 guard frames - 1 = 19 848, just under the 19 849-frame trimmed zones. A trim one frame past the runtime reach would fail it.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
