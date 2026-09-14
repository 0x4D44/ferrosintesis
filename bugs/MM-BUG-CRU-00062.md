# MM-BUG-CRU-00062 — GM76 lazy-fallback regression test assumes embedded samples, failing cargo test --no-default-features

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / GM76 voice tests
- **Raised:** 2026-09-13T19:23:17Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T212205Z-aa36c457
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00062-run-verify-20260914T212205Z-aa36c457
- **Owner base:** 415d57e330a9d3c558f1a7c4bf73105d20ef58fc
- **Owner fingerprint:** sha256:f4ef40672f932a38a5e4784baffcc093cc544826601b0e97501d39950e137134
- **Owner since:** 2026-09-14T21:22:05Z
- **Owner until:** 2026-09-14T23:22:05Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:17Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:22:06Z, deltic:auto role=fix run=fix-20260913T201032Z-feadacb0 branch=task/bug-MM-BUG-CRU-00062-run-fix-20260913T201032Z-feadacb0 code=28a82cbdea5d7f57ef044f537fc4469f3cbd59a8 gate=manual)

## Observation

Split at independent verification of MM-BUG-KILN-00213 (2026-09-13, trunk 8b6a6f86). Fix 97c2083e added voices::tests::gm76_model_fallback_is_constructed_only_when_selected (crates/ferrosintesis/src/voices.rs ~15272). Its first case asserts a sampled GM76 note builds the modeled fallback zero times, but the test is not gated on feature embedded-samples. In a modeled-only build the sampled path returns None, so the fallback is correctly built once and cargo test -p ferrosintesis --no-default-features --locked fails: 'sampled GM76 must not build its fallback', left 1, right 0. That command is a required integration gate step. Expected: gate the sampled case on embedded-samples (or expect 1 without it). The voice code itself is correct.

## Fix

<unfixed — raised only>

## Notes
