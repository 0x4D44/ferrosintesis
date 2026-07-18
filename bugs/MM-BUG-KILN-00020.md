# MM-BUG-KILN-00020 — The perceptual anti-clone oracle silently vanishes under --no-default-features

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** testutil
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-19, c58e791 — a no-default-features test run now fails explicitly because the required samples-on perceptual oracle is unavailable; the default samples-on oracle remains green.)

## Observation

`mod perceptual_distinctness` is gated `#[cfg(all(test, feature =
"embedded-samples"))]` (`crates/ferrosintesis/src/testutil.rs:~1569`).
`embedded-samples` is the default, but a `cargo test --no-default-features` run
drops the whole module and passes green with **zero** perceptual-clone coverage
and no signal that the gate is absent. A contributor or CI running samples-off
gets a false all-clear.

## Fix

c58e791 adds perceptual_distinctness_requires_embedded_samples under the
samples-off test configuration. Before the fix, the focused no-default-features
command exited successfully after running zero tests. It now runs one deliberate
failure whose message explains that perceptual anti-clone coverage requires the
default embedded-samples feature and tells the caller to rerun without
--no-default-features.

The default-feature BAR_FULL negative-control test remains green, proving the
samples-on perceptual module still compiles and runs normally.

## Notes

- Cheap; protects the value of MM-BUG-KILN-00006's oracle work from silent bypass.
