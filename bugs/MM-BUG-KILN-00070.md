# MM-BUG-KILN-00070 — The --no-default-features build is ungated: six dead-code warnings and vanishing oracles

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** build / test coverage
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 (1M) while fixing
  KILN-00059; reproduced)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). All seven dead items feature-gated, and the
  modeled-only clippy added to `.deltic-integrate.toml` so it cannot rot again. The matching
  TEST step is NOT added and is split to MM-BUG-KILN-00090: 31 tests fail in that
  configuration and each needs classifying. Evidence under "Fix landed" below. Awaits
  independent two-eyes closure.)

## Observation

**Symptom.** The modeled-only build — `--no-default-features`, the configuration the
README offers to anyone who does not want the embedded samples — is not covered by any
gate, and has silently accumulated dead code.

**Repro** (from a worktree root):

```
$ cargo clippy -p ferrosintesis --no-default-features --all-targets -- -D warnings
error: constant `CLAVINET_LEVEL` is never used
  --> crates\ferrosintesis\src\sampler.rs:4062:7
error: could not compile `ferrosintesis` (lib test) due to 7 previous errors
```

Six distinct items, all unreachable without `embedded-samples`:
`CLAVINET_LEVEL`, `CLAVINET_RELEASE_T60`, `bagpipe_song`, `bp_opts`, `hit_onset`,
`ncc_max`, `warp_ncc`.

**Expected.** `--no-default-features` is a supported, documented configuration
(`crates/ferrosintesis/README.md`, "Feature flags"; `Cargo.toml` `default =
["embedded-samples"]`). It should build warning-clean like the default configuration.

**Actual.** It does not, and nothing notices, because
`.deltic-integrate.toml`'s gate and fallback both run only the default feature set:

```
{ program = "cargo", args = ["clippy", "--workspace", "--exclude", "amp-lab", "--all-targets", "--locked", "--", "-D", "warnings"] }
```

**Why this matters beyond tidiness.** The same blind spot hides *missing test coverage*.
`crates/ferrosintesis/src/sampler.rs`'s test module is
`#[cfg(all(test, feature = "embedded-samples"))]`, so every oracle in it evaporates
under `--no-default-features` — nothing proves the modeled-only synth still renders. That
is the same failure mode as **MM-BUG-KILN-00020** ("the perceptual anti-clone oracle
silently vanishes under `--no-default-features`"), which is still Open. 00020 is one
instance; this bug is the structural cause — the configuration is never built or tested,
so nobody finds out.

## Fix

Two parts, and the second is the one that matters:

1. Remove or correctly `cfg`-gate the six dead items so the configuration is
   warning-clean.
2. **Add the configuration to the gate**, otherwise part 1 rots again within weeks. A
   `--no-default-features` clippy+test step in `.deltic-integrate.toml`'s `workspace`
   component is the obvious move. Weigh the cost: it is a second full compile of the
   crate per integration on an already slow gate, so it may belong in the fallback, or
   as a `check` rather than a full `test`.

Consider also auditing which oracles legitimately require samples and which are gated
that way only by inheritance from the enclosing module — the second group should move to
a module that compiles in both configurations, which would partly address KILN-00020.

## Fix landed (2026-07-24)

**Part 1 — the configuration is warning-clean.** Seven dead items, not six: the bug's list
plus `ncc_windows`, a test helper added the same day by the MM-BUG-KILN-00086 fix — which
is itself the evidence for the bug's central claim, since it accumulated within hours of
the bug being filed.

Each is **feature-gated, not deleted** — `CLAVINET_LEVEL` / `CLAVINET_RELEASE_T60`
(`sampler.rs`), and the test helpers `ncc_max`, `hit_onset`, `warp_ncc`, `bp_opts`,
`bagpipe_song` (`engine.rs`), `ncc_windows` (`voices.rs`). The compiler validates the
gating in BOTH directions: a wrong gate fails the default build, a missing one fails the
modeled-only build.

Two further failures in the same run were tests THIS session had added
(`a_routing_change_inside_the_tremolo_window_spawns_the_new_voice`,
`the_mandolin_strike_phase_is_bank_scoped_and_survives_a_retrigger`). Both assert
sampled-bank routing, so both are now feature-gated with their reason recorded.

**Part 2 — the gate, for clippy.** `.deltic-integrate.toml` gains
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
in both the `workspace` component gate and the fallback. One crate, no asset crates to
compile (2.4 s here), so the cost is small. This is what stops part 1 rotting: the
default-feature clippy structurally CANNOT see this code, because it is compiled out.

**Part 2 is deliberately incomplete, and this is the honest part.** The matching
`cargo test --no-default-features` step is NOT added, because it would be red on arrival:
that suite is **536 passed, 31 failed**. The configuration had never been run, so nothing
distinguishes a test that legitimately needs the samples (`fx_o7_rain_96_real_recording_bed`)
from one exposing a real modeled-only defect (`solo_mutes_other_channels`,
`rpn_bend_range_and_fine_tune`, `cc74_brightness_filter` read as configuration-independent
controller behaviour). Mass-gating them to make the step green would convert a red into
silent breakage — the exact failure mode this bug and MM-BUG-KILN-00020 are about. Split
to **MM-BUG-KILN-00090** with the full list, the classification criteria, and a concrete
first finding: one failure was not an assertion but a PANIC in the modeled-only
`embedded_wav` stub, raised because the test set `samples: true` — a modeled-only build
arguably should treat that as "no samples available" (`crate::embedded_samples_available()`
already exists) rather than panicking inside a voice constructor. The `.deltic-integrate.toml`
comment records why the test step is absent and points at 00090, so the gap is visible to
the next reader rather than looking like an oversight.

**Verification.** `cargo clippy -p ferrosintesis --no-default-features --all-targets
--locked -- -D warnings` clean (was 10 errors across lib and lib-test); the default
workspace clippy still clean; `cargo fmt --check` clean; default suite 659 passed / 0
failed / 26 ignored (+4 doc-tests) — unchanged count, so the two gated tests still run
where they are meaningful.

## Notes

- Found while fixing KILN-00059. The KILN-00059 change was verified clean in this
  configuration (its `BANK_INITS` static does not appear in the warning list); every
  item above pre-dates it and lives in code that change did not touch.
- Reproduced, not inferred. No attempt was made to fix it under KILN-00059, whose scope
  was the prewarm list.
