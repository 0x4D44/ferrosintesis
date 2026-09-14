# MM-BUG-CRU-00063 — LaVoice realtime scratch probe is dead code without embedded samples, failing the no-default-features clippy gate

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / realtime voice test probes
- **Raised:** 2026-09-13T19:23:18Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T212319Z-ed9103c7
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00063-run-verify-20260914T212319Z-ed9103c7
- **Owner base:** 66d79b5442ca7d81cd7826c4a28fd8edc0a81b97
- **Owner fingerprint:** sha256:3358966524f5dbdbeeee6fa179ea167db55d33a0ebff2e36f71fa89f87fb29c9
- **Owner since:** 2026-09-14T21:23:19Z
- **Owner until:** 2026-09-14T23:23:19Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:18Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:33:32Z, deltic:auto role=fix run=fix-20260913T202323Z-571c2f55 branch=task/bug-MM-BUG-CRU-00063-run-fix-20260913T202323Z-571c2f55 code=b6a69875d28dc2ba2d1cd748e54aac2f511f484d gate=manual)

## Observation

Split at independent verification of MM-BUG-KILN-00216 (2026-09-13, trunk 8b6a6f86). Fix 1bb5b439 added the #[cfg(test)] trait method Voice::realtime_scratch_capacity_for_test (crates/ferrosintesis/src/voices.rs:108). Its only callers are in the sampler tests module gated all(test, feature = "embedded-samples"). So cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings fails with 'method realtime_scratch_capacity_for_test is never used' (rustc/clippy 1.95.0). That clippy run is a required integration gate step. Expected: gate the probe on the same feature as its callers. The inline-scratch fix itself is correct.

## Fix

<unfixed — raised only>

## Notes
