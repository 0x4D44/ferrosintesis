# MM-BUG-KILN-00020 — The perceptual anti-clone oracle silently vanishes under --no-default-features

- **State:** Open
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

`mod perceptual_distinctness` is gated `#[cfg(all(test, feature =
"embedded-samples"))]` (`crates/ferrosintesis/src/testutil.rs:~1569`).
`embedded-samples` is the default, but a `cargo test --no-default-features` run
drops the whole module and passes green with **zero** perceptual-clone coverage
and no signal that the gate is absent. A contributor or CI running samples-off
gets a false all-clear.

## Fix

Make the ear-facing anti-clone coverage a hard requirement — either assert
`embedded-samples` is present in a required test, or add a compile-time guard so a
samples-off run fails loudly rather than silently skipping the gate.

## Notes

- Cheap; protects the value of MM-BUG-KILN-00006's oracle work from silent bypass.
