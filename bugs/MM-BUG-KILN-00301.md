# MM-BUG-KILN-00301 — Integration gate never runs example tests and never builds the CLI's advertised --no-default-features config, leaving its only unit test vacuous

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:56:22Z
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
- **State history:** Open (2026-08-17T22:56:22Z, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-09-13T23:15:40Z, deltic:auto role=fix run=fix-20260913T224848Z-329ad481 branch=task/bug-MM-BUG-KILN-00301-run-fix-20260913T224848Z-329ad481 code=f5d6035931c5539eb98842641645c72e96597ccb gate=manual) -> Open (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the new gate steps are right and load-bearing, but the added CLI no-default test step fails the gate's own no_default_gate_is_paired_with_embedded_sample_coverage oracle (unclassified cargo test step, left 4 right 6))

## Observation

Two gaps in the gate's target/feature matrix, one root: what the gate runs does not match
what `ferrosintesis-cli` ships.

**1 — five example tests never execute.** `.deltic-integrate.toml:58` and `:70` run
`cargo test --workspace --locked`. No `--all-targets`. Measured during review:
`cargo test -p ferrosintesis-cli` runs **16** tests across three binaries;
`cargo test -p ferrosintesis-cli --all-targets` runs **21**. The extra five are the
`#[cfg(test)] mod tests` block in `crates/ferrosintesis-cli/examples/calmeter.rs:212-254` —
`read_wav_rejects_a_one_hz_meter_input`, `read_wav_accepts_the_lowest_supported_rate`, and
the three `onset_blocks_*` tests. None of them run in the gate.

`calmeter.rs:120` documents `onset_blocks` as "Pure — unit-tested below". Under the repo's
actual gate that sentence is false. The tests are good — they encode the warm-up/tail block
geometry that CLAUDE.md's own calibration notes call expensive to get wrong — and they are
dead weight where it counts.

Note the gate *does* pass `--all-targets` to clippy (`.deltic-integrate.toml:55`, `:67`), so
the example binaries are still compiled and linted. Whether clippy also type-checks the
`#[cfg(test)]` module (cargo builds examples with `test = false` by default) was **not**
measured — do not assume the block is even compiling today.

**2 — the CLI's `--no-default-features` build is never gated, so its only unit test asserts
nothing.** `crates/ferrosintesis-cli/src/main.rs:191-200` is:

```rust
assert_eq!(
    ferrosintesis::embedded_samples_available(),
    cfg!(feature = "embedded-samples")
);
```

The library side is `cfg!(feature = "embedded-samples")` too
(`crates/ferrosintesis/src/lib.rs:88`). Under default features both sides are `true`, so
under every command in `.deltic-integrate.toml` this is `assert_eq!(true, true)` — it cannot
distinguish a correctly-forwarded feature from a broken one. The false arm was exercised
during review with `cargo test -p ferrosintesis-cli --no-default-features` (it passes), but
the gate runs `--no-default-features` for **`-p ferrosintesis` only**
(`.deltic-integrate.toml:56-57`, `:68-69`) — never for the CLI, even though
`crates/ferrosintesis-cli/README.md:52` advertises
`cargo install ferrosintesis-cli --no-default-features` as a shipped configuration.

This is precisely CLAUDE.md's "a test that has never failed proves nothing".

**Expected.** The gate runs the tests that exist, and covers both feature configurations the
CLI's README offers users.

**Actual.** Neither.

## Fix

<unfixed — raised only>

1. Add `--all-targets` to the `cargo test --workspace --locked` steps
   (`.deltic-integrate.toml:58` and `:70`). Check the runtime cost before landing — it is
   the reason to measure rather than assume.
2. Add `{ program = "cargo", args = ["test", "-p", "ferrosintesis-cli",
   "--no-default-features", "--locked"] }` alongside the existing `-p ferrosintesis`
   `--no-default-features` steps, and the matching clippy step.
3. **Watch out for feature unification on the workspace-wide form.**
   `crates/render-catalog/Cargo.toml:15` depends on `ferrosintesis` with default features
   on, so under a `--workspace --no-default-features` build cargo can turn
   `embedded-samples` back on in the library while the CLI's own `cfg!` stays false — the
   forwarding test would then fail for a reason unrelated to forwarding. This is why step 2
   uses `-p ferrosintesis-cli`, not a workspace-wide flag. (Manifest evidence; the
   combination was not built — it pulls all 24 asset crates.)
4. Prove step 2 is worth having: break the forwarding deliberately (point the CLI's
   `embedded-samples` feature at nothing), confirm the new step goes red, restore.

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `f5d60359`) by an agent other than the fixer. **Reopened.**

**What the fix gets right.** Both gaps in the observation are closed. `cargo test --workspace --all-targets --locked` now runs the five `calmeter` example tests, and all pass (the `read_wav_*` temp-name race did not fire in this run). The new `-p ferrosintesis-cli --no-default-features` test step is load-bearing: with the CLI's `ferrosintesis` dependency switched to default features, that step fails `embedded_samples_feature_is_forwarded_to_the_library` (left true, right false), while the default-feature CLI test stays green. The new CLI no-default clippy step passes.

**Why reopened.** This fix turned the gate red. `cargo test -p ferrosintesis --no-default-features --locked` fails `testutil::no_default_gate_is_paired_with_embedded_sample_coverage` at `testutil.rs:1886`: 'unclassified cargo test step in the gate', left 4, right 6. The oracle sorts `cargo test` steps into a `--workspace` bucket and a `--no-default-features` bucket matched on the exact token `"ferrosintesis"`. The two new `"ferrosintesis-cli"` steps fit neither, and the oracle's own comment says a new configuration must be taught to it. Pinned by method A: the oracle's predicate passes on `f5d60359^:.deltic-integrate.toml` (2 + 2 of 4 steps) and fails on `f5d60359` (2 + 2 of 6).

**To close.** Teach the oracle the CLI modeled-only bucket (one step per gate array) and keep its every-step-classified assertion, so the gate's `cargo test -p ferrosintesis --no-default-features` step is green again.

## Notes

- Raised by an autonomous read-only code-review pass. The 16-vs-21 test counts are measured;
  the gate commands are read from `.deltic-integrate.toml:53-72`; the vacuity of the
  forwarding test follows from both sides being `cfg!` on the same feature.
- Filed against `crates/ferrosintesis-cli` because that is the crate losing coverage, though
  the edit lands in `.deltic-integrate.toml` at the repo root.
- Fixing (1) will start running the five calmeter tests for the first time. Expect them to
  need attention on first contact — `calmeter.rs:181-183` builds its temp path from
  `process::id()` and a nanosecond nonce with **no** discriminating label, unlike every
  sibling helper (`output.rs:88`, `tests/output_safety.rs:15`), so the two `read_wav_*`
  tests race for one filename when run in parallel. That is tracked separately as test debt.
