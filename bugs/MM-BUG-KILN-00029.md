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
- **State history:** Open (2026-07-20, raised by Claude Opus 4.8 during the velocity-law alignment to k=2; found by the new `velocity_law` oracles, confirmed by Fable 5 which measured the EP sweep independently) → Blocked (2026-07-25, Codex GPT-5.6-Sol; the diagnosed bowed-waveguide normalization and separate GM4 pickup-shaper retune both require Arthur's ear validation before a safe voicing change)

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

## Investigation note (2026-07-21 — diagnosed, then deferred to a dedicated ears-in-loop session)

Deferred by Arthur to prioritise the M-CAL instrument-balance work. Not a blocker for it:
M-CAL's velocity guard already excludes GM42/43, so they simply stay un-trimmed (and flagged
by the self-retiring guard) until this is fixed.

**GM42/43 is a waveguide STABILITY problem, not a smooth turnover.** At high bow speed the
stick-slip limit cycle enters an over-bowed **chaotic** regime in register- AND
velocity-specific pockets. Measured on the unfixed model (`melodic_level` = `make()` max
momentary LUFS, `SEED` fixed, samples on):

- GM42 key60: v110 −5.16 → v115 **−9.60** → v120 −2.70 → v127 **−7.14** — ±4 dB across
  *adjacent* velocities, i.e. chaotic, not a monotone dip. `slope` (bow force) is fixed per
  seed across velocity, so the swing is the deterministic waveguide going unstable, not RNG.
- Onset ~v105–110, i.e. `max_vel ≈ 0.19–0.20` where `max_vel = 0.03 + 0.22·vel_ctrl(vel)`
  (`voices.rs` BowedString::new). Lower strings over-bow at a lower bow speed than the mid
  register (longer wavelength / more inertia), so the onset is register-dependent.

**A bow-speed clamp is necessary but NOT sufficient.** `vel_ctrl(vel).min(0.65)` made keys
48/55/60/67 cleanly monotonic through v127, but chaotic pockets survived on other keys (GM42
key50 still craters −4.7 dB at v127; key36 wobbled), and tightening the clamp over-darkens the
whole instrument (a ~4 dB level discontinuity opened between key45 and key50). A robust fix
likely needs **output-amplitude normalization** — decouple rendered level from the chaotic
intrinsic limit-cycle amplitude so the clean `amp ∝ vel_amp` gain owns loudness; the model
already carries an `amp_follow` output follower to build on — PLUS register tuning, and MUST be
ear-validated (this box has none).

**GM4 is a separate, smaller issue.** Its LEVEL is monotonic at every key through v127 — only
the *bark* (h1) timbre measure turns over past v≈105 (the `PickupShaper` tanh, `voices.rs`,
compressing the tine faster than the mode table grows it). No level fix needed; the bark tweak
is independent of the bowed-string work.

Exit condition and the self-retiring guards (`excluded_programs_still_reproduce_their_defect`,
the `every_gm_program_follows_the_square_law` exclusion) are unchanged.

## Blocker (2026-07-25)

The current diagnosis already refuted the unattended low-risk fix: a bow-speed clamp removes
some chaotic pockets but leaves others and creates an audible register discontinuity. The
remaining bowed-string path is output-amplitude normalization plus register tuning, which
changes the instrument's response and must be judged by ear. GM4 is a separate timbre retune
of the pickup nonlinearity and has the same listening requirement.

Unblock when Arthur can audition candidate GM42/43 normalization across the documented key
and velocity grid, and separately approve a GM4 bark curve through v127. The existing
self-retiring velocity-law guards provide the machine exit conditions after those voicing
targets are chosen.
