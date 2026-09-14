# MM-BUG-CRU-00063 — LaVoice realtime scratch probe is dead code without embedded samples, failing the no-default-features clippy gate

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / realtime voice test probes
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
- **State history:** Open (2026-09-13T19:23:18Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:33:32Z, deltic:auto role=fix run=fix-20260913T202323Z-571c2f55 branch=task/bug-MM-BUG-CRU-00063-run-fix-20260913T202323Z-571c2f55 code=b6a69875d28dc2ba2d1cd748e54aac2f511f484d gate=manual) -> Closed (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: both clippy gates clean; reverting the probe to cfg(test) reproduces the never-used error at voices.rs:108)

## Observation

Split at independent verification of MM-BUG-KILN-00216 (2026-09-13, trunk 8b6a6f86). Fix 1bb5b439 added the #[cfg(test)] trait method Voice::realtime_scratch_capacity_for_test (crates/ferrosintesis/src/voices.rs:108). Its only callers are in the sampler tests module gated all(test, feature = "embedded-samples"). So cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings fails with 'method realtime_scratch_capacity_for_test is never used' (rustc/clippy 1.95.0). That clippy run is a required integration gate step. Expected: gate the probe on the same feature as its callers. The inline-scratch fix itself is correct.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `b6a69875`) by an agent other than the fixer.

**Original observation.** `cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings` exits 0. The default-feature workspace clippy also exits 0, so the probe still compiles where its sampler-test callers do.

**Fails-before (method B).** Reverting both `#[cfg(all(test, feature = "embedded-samples"))]` attributes (`voices.rs:107`, `sampler.rs:4112`) to `#[cfg(test)]` makes the no-default clippy fail with 'method `realtime_scratch_capacity_for_test` is never used' at `voices.rs:108`. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
