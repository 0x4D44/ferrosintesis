# MM-BUG-CRU-00062 — GM76 lazy-fallback regression test assumes embedded samples, failing cargo test --no-default-features

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / GM76 voice tests
- **Raised:** 2026-09-13T19:23:17Z
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
- **State history:** Open (2026-09-13T19:23:17Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:22:06Z, deltic:auto role=fix run=fix-20260913T201032Z-feadacb0 branch=task/bug-MM-BUG-CRU-00062-run-fix-20260913T201032Z-feadacb0 code=28a82cbdea5d7f57ef044f537fc4469f3cbd59a8 gate=manual) -> Closed (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the GM76 fallback test passes with and without embedded samples; reverting the expectation reproduces the recorded left 1 right 0 failure)

## Observation

Split at independent verification of MM-BUG-KILN-00213 (2026-09-13, trunk 8b6a6f86). Fix 97c2083e added voices::tests::gm76_model_fallback_is_constructed_only_when_selected (crates/ferrosintesis/src/voices.rs ~15272). Its first case asserts a sampled GM76 note builds the modeled fallback zero times, but the test is not gated on feature embedded-samples. In a modeled-only build the sampled path returns None, so the fallback is correctly built once and cargo test -p ferrosintesis --no-default-features --locked fails: 'sampled GM76 must not build its fallback', left 1, right 0. That command is a required integration gate step. Expected: gate the sampled case on embedded-samples (or expect 1 without it). The voice code itself is correct.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `28a82cbd`) by an agent other than the fixer.

**Original observation.** `voices::tests::gm76_model_fallback_is_constructed_only_when_selected` passes in `cargo test -p ferrosintesis --no-default-features --locked` and in `cargo test --workspace --all-targets --locked`. The expectation is now 0 constructions with embedded samples and 1 without, which matches the voice code the observation called correct.

**Fails-before (method B).** Restoring the unconditional `0` makes the modeled-only run fail with the recorded message: 'sampled GM76 must not build its fallback', left 1, right 0. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: the same `cargo test -p ferrosintesis --no-default-features` step fails one other test, `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
