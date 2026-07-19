# MM-BUG-KILN-00020 — The perceptual anti-clone oracle silently vanishes under --no-default-features

- **State:** Closed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-19, c58e791 — a no-default-features test run now fails explicitly because the required samples-on perceptual oracle is unavailable; the default samples-on oracle remains green.); Closed (2026-07-19, verified by Claude Opus 4.8 (1M context) - independent two-eyes (fixer Codex GPT-5); cargo test -p ferrosintesis --no-default-features now FAILS loudly on perceptual_distinctness_requires_embedded_samples, while the default suite 548/0 keeps the samples-on perceptual module green)

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

### Verification summary (Claude Opus 4.8 (1M context), 2026-07-19)

Independent two-eyes on a worktree off origin/main (0cc8e7f, contains fix 18664a3, rebased from c58e791; verifier is not the fixer, Codex GPT-5). `cargo test -p ferrosintesis --no-default-features` now FAILS loudly on the deliberate guard `perceptual_distinctness_requires_embedded_samples` (panic at testutil.rs:1549: 'perceptual anti-clone coverage requires the default embedded-samples feature') - the silent zero-perceptual-coverage all-clear no longer reproduces. The default `cargo test --workspace` suite (548/0) keeps the full samples-on perceptual module green. NOTE (not a residual of this fix): the samples-off run also surfaces three pre-existing, unrelated failures - gm0_grand_and_gm1_upright_are_distinct_instruments, keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice, and wd_o10_routing_sample_policy_and_lifecycle - all positive sample-engagement controls that hard-code samples=true and cannot pass with the sample bank compiled out; they touch none of this batch's code.

## Notes

- Cheap; protects the value of MM-BUG-KILN-00006's oracle work from silent bypass.
