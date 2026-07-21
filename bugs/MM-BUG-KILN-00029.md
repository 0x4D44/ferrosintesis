# MM-BUG-KILN-00029 — voice models turn over near full velocity: GM42/43 bowed strings DROP up to 1.6 dB from v110 to v127, and GM4's pickup bark peaks at v≈105

- **State:** Blocked
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-20
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
- **State history:** Open (2026-07-20, raised by Claude Opus 4.8 during the velocity-law
  alignment to k=2; found by the new `velocity_law` oracles, confirmed by Fable 5 which
  measured the EP sweep independently) → Blocked (2026-07-21, Claude Opus 4.8 — the bug's own
  analysis establishes this needs the voice models re-voiced, "a different risk class [that]
  re-voices instruments and needs ears plus the render-diff inventory"; not an unattended
  code fix. Well-contained by self-retiring oracle exclusions meanwhile.)

## Observation

Two voices render **non-monotonically in velocity near the top of the range**. Both are
**pre-existing** — they are not caused by the k=2 velocity-law change, which leaves
`v=127` output unchanged by construction (`vel_amp(127) = 1.0` under both the retired
1.6 exponent and the shipped 2.0, and every floor fold preserves full velocity exactly).
The law change **exposed** them: with the correct law the region is measured, and with
the old flat law the middle of the range was over-driven, which masked the turnover.

### Proof the change did not cause or enlarge this (base v398f31c vs branch)

Measured `make()` raw level (max momentary block) at key 60 on the **old** synth
(exponent 1.6, floors present) vs the **new** (k=2), same probe:

| program | v110 | v127 | v110→v127 |
|---|---|---|---|
| GM42 old (1.6) | −4.00 | −7.14 | **drops 3.14 dB** |
| GM42 new (2.0) | −5.54 | −7.14 | **drops 1.60 dB** |
| GM43 old (1.6) | −1.77 | −4.44 | drops 2.67 dB |
| GM43 new (2.0) | −3.33 | −4.44 | drops 1.11 dB |

`v127` is **bit-identical** old vs new (as designed), and the new law *halves* the
reversal — it drives sub-fortissimo less hard, so the model saturates less. The turnover
is therefore pre-existing, and this change **reduces** it; it does not eliminate it, which
is why the exclusion stands until the model is fixed. (GM4's turnover is in the BARK
timbre measure, not the level — its level is monotonic on both builds.)

### GM42 cello / GM43 contrabass — level turns over

Measured through `voices::make(program, key, vel, …)`, samples on, with the
`VEL_LEVEL_EXP` compensation bypassed (max BS.1770 momentary block, 1.2 s window):

| program | v96 | v110 | v127 |
|---|---|---|---|
| GM42 cello, key 60 | −9.67 | −5.54 | **−7.14** (drops 1.60 dB) |
| GM43 contrabass, key 60 | −7.51 | −3.33 | **−4.44** (drops 1.11 dB) |

The square law requires v110 → v127 to **rise 2.49 dB**. So fortissimo on these two
voices sits roughly 4 dB below where the law puts it, and *quieter than mezzo-forte*.

### GM4 electric piano — pickup bark turns over

Bark / h1 measure swept across velocity (measured independently by Fable 5):

| v | 60 | 75 | 90 | 105 | 120 | 127 |
|---|---|---|---|---|---|---|
| bark | 0.0553 | 0.0611 | 0.0652 | **0.0667** | 0.0651 | 0.0635 |

Peaks at v≈105 and falls thereafter. Mechanism: the pickup shaper
`((x·drive + bias).tanh() …)` (`crates/ferrosintesis/src/voices.rs` — `shaper`) has an
operating point of signal × drive. Drive (`0.4 + 1.6·vn`) is unchanged; the signal is
∝ `vel_amp`. Above ~v105 the shaper's compression eats the tine faster than the mode
table grows it.

## Why this is filed rather than fixed

A scalar output-gain exponent — the mechanism the velocity-law task uses to land each
voice's rendered aggregate on k=2 — **cannot correct a curve that turns over**. Applying
one to GM42/43 made fortissimo *worse*, not better. These need the voice models
themselves: gain staging into the nonlinearity, or the nonlinearity's drive law.

That is a different risk class from a level-law change (it re-voices instruments and
needs ears plus the render-diff inventory), so it is deliberately NOT smuggled into the
velocity-law diff.

## Current containment

- GM42/43 are excluded **by name, with the measured evidence in the assertion's face**,
  from `every_gm_program_follows_the_square_law`
  (`crates/ferrosintesis/src/velocity_law.rs`), and carry no `VEL_LEVEL_EXP` entry —
  compensating a turnover makes it worse.
- The exclusion is **self-retiring**: `excluded_programs_still_reproduce_their_defect`
  asserts GM42/43 are STILL off-law, so fixing the model forces the exemption to be
  deleted rather than left rotting as a dead blind spot.
- GM4 is *not* excluded — it passes the aggregate law; only its bark oracle sees the
  turnover.

## Exit condition

Raw (compensation-bypassed) output is **monotonic in velocity through v=127** for GM42,
GM43 and GM4, and GM42/43's aggregate fits the square law within the oracle's ±0.25
tolerance — at which point `excluded_programs_still_reproduce_their_defect` fails and
the exclusions must be removed.

## Provenance

Found while implementing `wrk_docs/2026.07.20 - HLD - velocity law alignment to k=2.md`.
The bowed-string turnover was found by the lead; the EP bark turnover was raised as a
suspected instance of the same class and **confirmed by measurement** by Fable 5, which
also corrected the proposed mechanism (the old 1.6 law drove sub-127 velocities *harder*,
not softer — `x^1.6 > x^2` for `x < 1` — so it masked the turnover by over-saturating the
middle rather than by never reaching the top).

## Blocking note (2026-07-21, Claude Opus 4.8)

Routed Open → Blocked during a bug-drain pass. This is not unattended-fixable code: the bug's
own "Why this is filed rather than fixed" section is definitive — a scalar output-gain
exponent cannot correct a curve that turns over, so it needs the GM42/43 bowed-string and GM4
electric-piano voice **models** re-worked (gain staging into the nonlinearity / the drive
law), which "re-voices instruments and needs ears plus the render-diff inventory" and is "a
different risk class." This box has no ears, so it awaits a maintainer re-voicing decision.
The defect stays honestly contained by the by-name, self-retiring exclusions in
`velocity_law.rs` (`excluded_programs_still_reproduce_their_defect`), so it is not a silent
blind spot. **Missing input to unblock:** Arthur's re-voicing pass + render-diff/ears review.
