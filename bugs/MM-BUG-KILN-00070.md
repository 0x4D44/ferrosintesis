# MM-BUG-KILN-00070 — The --no-default-features build is ungated: six dead-code warnings and vanishing oracles

- **State:** Open
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

## Notes

- Found while fixing KILN-00059. The KILN-00059 change was verified clean in this
  configuration (its `BANK_INITS` static does not appear in the warning list); every
  item above pre-dates it and lives in code that change did not touch.
- Reproduced, not inferred. No attempt was made to fix it under KILN-00059, whose scope
  was the prewarm list.
