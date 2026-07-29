# MM-BUG-KILN-00179 — The MM-BUG-KILN-00176 periodicity oracle has no positive control, so nothing preserves its ability to see the artifact

- **State:** Open
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high)

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

<unfixed — raised only>

## Notes
