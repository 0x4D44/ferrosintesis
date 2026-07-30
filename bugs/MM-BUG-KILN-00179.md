# MM-BUG-KILN-00179 — The MM-BUG-KILN-00176 periodicity oracle has no positive control, so nothing preserves its ability to see the artifact

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** oracle design / sampled sax sustain
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-30, deltic:auto role=fix run=fix-20260729T235614Z-p67528-n716300100-c1 branch=task/bug-MM-BUG-KILN-00179-run-fix-20260729T235614Z-p67528-n716300100-c1 code=fcae2c2e88eea43acd4536d882cd163a1e089f6b gate=manual) -> Closed (2026-07-30, independently verified by claude-opus-5@high on trunk 73ec2f2; fix authored by GPT-5.6, so two-eyes holds)

## Observation

Residual split from MM-BUG-KILN-00176 during its independent two-eyes closure.
Surfaced by an adversarial review briefed to defeat the oracle rather than confirm it,
and it survived a refute-by-default verification pass.

`baritone_sax_high_hold_does_not_expose_the_source_loop_period` in
`crates/ferrosintesis/src/sampler.rs` guards the MM-BUG-KILN-00176 fix. Both of its
assertions are UPPER bounds: `exposed < 0.40` and `level_cov < 0.12`. Nothing in the
suite ever renders the single-slice path and requires the metric to EXCEED the bar.

The only evidence the bar discriminates is a hand-written doc comment on the test
itself - "The old single-slice reader produces a 0.962 excess peak" - which no
assertion enforces.

**What was actually proven at closure, and what was not.** Forcing the production
gate off (`program == 67 && key >= 68` -> `false`) made the test fail at its first
case with excess 1.041 (1x 0.963, 2x 1.041), so the oracle DOES discriminate today
and MM-BUG-KILN-00176's regression evidence is sound. But because the assertion panics
on the first case, only key 68 velocity 72 was demonstrated; the other three
(68/110, 73/72, 73/110) are unproven in the test's own excess statistic. Nothing
preserves any of it.

**Concrete vacuity path.** Changing `HARMONICS` from 8 to 1 zeroes the metric
outright: the per-frame mean subtraction makes a single-element shape identically 0,
so both energy terms are 0 and the correlation returns 0.0 at every lag. `exposed`
becomes 0.0 and the test passes forever. Edits to `frame_len` (512), `hop` (64), or
the decoy triple (0.73x / 1.37x / 1.91x) degrade sensitivity the same way, silently.

**Expected.** The oracle proves it can see the artifact before asserting its absence,
in the pattern this repo already uses for this exact oracle class:
`snare_grain_is_aperiodic_and_impulsive_v3` at `crates/ferrosintesis/src/drums.rs`
asserts the positive control exceeds the bar FIRST, then applies a *differential*
bar (`p3 < 0.65 * p2`) precisely because an absolute threshold on such a statistic is
not trustworthy on its own.

**Actual.** No positive control, an absolute bar, and no test asserting that grain
motion engages at all.

The fix is one argument away: `SaxLoopVoice::new(.., grain_motion = false)` is already
constructed from this same test module, so the control can render the identical
key/velocity single-slice and require the metric to exceed the bar - ideally replacing
the absolute 0.40 with a ratio against the measured control.

This is the trap CLAUDE.md documents at length ('write the adversarial document that
*should* fail your oracle, and check that it does') and which lessons_learnt records as
'Prove a metric can SEE your change'. The ledger already carries three instances:
MM-BUG-KILN-00004, 00026 and 00052 were all guards that tested the wrong thing while
passing.

Scope note: this is a guard-durability defect, not a shipped audio defect. The audio
fix it guards was independently verified correct at closure.

## Fix

`fcae2c2e` (GPT-5.6) at `crates/ferrosintesis/src/sampler.rs`, in
`baritone_sax_hold_does_not_expose_the_source_loop_period`:

- Adds the positive control the bug specified, built exactly as the Observation
  predicted it could be — `SaxLoopVoice::new(zone, f0, vel, sr, gain, seed,
  false)` renders the identical key/velocity through the single-slice path with
  the *same seed*, and the metric must exceed the bar: `control_exposed > 0.40`.
- Replaces the absolute `exposed < 0.40` with the differential
  `exposed < 0.65 * control_exposed`, matching the
  `snare_grain_is_aperiodic_and_impulsive_v3` pattern the Observation cites.
- Both assertions run per key/velocity, so all 12 cases carry their own control.
- The unenforced doc-comment claim ("produces a 0.962 excess peak") is gone,
  replaced by a statement of what the control proves.

## Notes

**Independent verification, 2026-07-30, claude-opus-5@high on trunk 73ec2f2**
(worktree `D:\worktrees\midi-music\20260730-TSK-HUM-verify-close-sax-bugs`).
Fix authored by GPT-5.6 — a different actor, so two-eyes holds.

**The exact vacuity path this bug named is closed, proven both directions.** The
Observation's concrete attack was changing `HARMONICS` from 8 to 1, which zeroes
the metric outright so the test passes forever. Both halves measured:

| oracle version | `HARMONICS` 8 → 1 | result |
| --- | --- | --- |
| pre-fix (`190b8c6`, absolute `exposed < 0.40`) | applied | **PASSES** — vacuous, exactly as reported |
| fixed (`fcae2c2`, positive control) | applied | **FAILS** — "GM67 key 64 velocity 72: the single-slice positive control did not expose the 0.0576s source loop (excess 0.000; 1x 0.000, 2x 0.000)" |

The pre-fix run is the counterfactual that matters: it confirms the reported
vacuity was real and not theoretical, so the fix closes a live hole rather than
guarding a hypothetical one. Note the mutant is caught by the *control*
assertion, before the main bar is ever evaluated — the intended mechanism.

**The unproven cases named in the Observation are now proven.** The bug recorded
that only key 68 velocity 72 had been demonstrated, because the old assertion
panicked on the first case. Each of the 12 key/velocity pairs now computes and
asserts its own control, so 68/110, 73/72 and 73/110 — plus the eight cases
MM-BUG-KILN-00177 added — each carry live evidence. Measured single-slice control
values run 0.62–1.20 across the set, all comfortably above the 0.40 control bar.

**The absolute bar is gone, as the Observation asked.** `exposed < 0.65 *
control_exposed` is relative to a value measured in the same run, so the oracle
no longer depends on a hand-tuned threshold surviving unrelated synthesis changes.

**Scope confirmed.** This was a guard-durability defect, not a shipped audio
defect, and the fix is test-only — `git show fcae2c2 --stat` touches only the test
body in `sampler.rs`. No render behaviour changes, so no render-diff inventory is
owed.

**Gates green on the exact tree:** `cargo test --workspace --release` 842 passed
/ 0 failed in `ferrosintesis` plus every sample crate green;
`cargo clippy --workspace --all-targets -- -D warnings` clean;
`cargo fmt --all -- --check` clean.

Verification mutations were temporary and are not committed; the tree was restored
to 73ec2f2 and confirmed clean before the gate run.
