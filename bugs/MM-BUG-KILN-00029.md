# MM-BUG-KILN-00029 — voice models turn over near full velocity: GM42/43 bowed strings DROP up to 1.6 dB from v110 to v127, and GM4's pickup bark peaks at v≈105

- **State:** Fixed
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
- **State history:** Open (2026-07-20, raised by Claude Opus 4.8 during the velocity-law alignment to k=2; found by the new `velocity_law` oracles, confirmed by Fable 5 which measured the EP sweep independently) → Blocked (2026-07-25, Codex GPT-5.6-Sol; the diagnosed bowed-waveguide normalization and separate GM4 pickup-shaper retune both require Arthur's ear validation before a safe voicing change) → Open (2026-07-26, unblocked by Arthur; approved monotonic GM42/43 loudness with stable bow character and a non-decreasing, plateau-permitted GM4 bark curve; focused prior-art constraints recorded below) → Fixed (2026-07-27, Codex GPT-5.6; recovered the scheduler-held branch, rejected its one-dimensional bow-speed clamp, and completed the approved joint control map plus bounded normalization; code=52d998be6339 gate=focused+render-diff)

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

## Decision and focused prior-art research (2026-07-26)

Arthur approved the following product targets, so candidate audition is no longer a blocker:

- **GM42/43:** MIDI velocity owns rendered loudness. Raw output must be monotonic through
  v127 and meet the existing square-law oracle within ±0.25, without hiding chaotic
  over-bowing or introducing a register cliff. Bow nonlinearity may continue to shape
  articulation and spectrum.
- **GM4:** its 2.82·f0 bark must be non-decreasing across
  v60/75/90/105/120/127. A gentle plateau above v≈105 is acceptable; a decline is not.
  Preserve the existing forte floor, onset-to-sustain bloom, DC, GM4/GM5 distinctness, and
  aggregate-level guards.
- Representative before/after renders remain useful verification evidence, but the measurable
  targets above are sufficient for an autonomous fixer to proceed.

### Prior art and resulting constraints

1. **Map into a playable region before normalizing output.** Serafin and Smith measured the
   joint bow-force, bow-speed, and bow-position region that produces stable Helmholtz motion,
   then used those measured limits in a real-time synthesizer; they report that this made the
   model significantly more robust. They also found that attack trajectories change the
   playable region. This rules out another one-dimensional `max_vel` clamp. First sweep this
   model's `(key, velocity, slope, max_vel)` space and map each program/register into a stable
   region, including a suitable attack trajectory.
   Source: [Influence of Attack Parameters on the Playability of a Virtual Bowed String
   Instrument](https://quod.lib.umich.edu/cgi/p/pod/dod-idx/influence-of-attack-parameters-on-the-playability.pdf?c=icmc%3Bidno%3Dbbp2372.2000.218%3Bformat%3Dpdf)
   (ICMC 2000).

2. **Keep the physical controls independent.** STK's reference waveguide exposes bow pressure,
   position, and velocity independently; its nonlinear junction uses bow/string differential
   velocity, while the output has a separate fixed body gain. That supports jointly retuning
   `slope` and `max_vel` rather than asking one velocity scalar to supply timbre, stability,
   and GM loudness simultaneously.
   Sources: [STK `Bowed.cpp`](https://github.com/thestk/stk/blob/master/src/Bowed.cpp) and
   [STK `Bowed.h`](https://github.com/thestk/stk/blob/master/include/Bowed.h).

3. **Do not meter away an unstable source.** Energy-consistent/passive bowed-string schemes
   are established precisely because the nonlinear contact can destabilize a numerical model.
   Replacing this waveguide with an implicit/modal solver is out of scope, but an output
   follower must not make the loudness test pass while the underlying limit cycle remains
   chaotic. Add a period-to-period stability oracle (or equivalent Helmholtz-motion
   classifier) alongside the loudness oracle.
   Source: [Efficient Simulation of the Bowed String in Modal
   Form](https://www.dafx.de/paper-archive/2022/papers/DAFx20in22_paper_14.pdf)
   (DAFx 2022).

4. **Use normalization only for residual level variation.** If the stable control map still
   leaves register-dependent limit-cycle amplitude, use a slow, bounded follower derived from
   the existing `amp_follow`. Measure the intrinsic post-body signal before `self.amp`, and
   let the existing `vel_amp` output path set the target loudness. Bound gain and its slew so
   the bow catch, natural sustain movement, and release are not flattened or pumped.

5. **Retain GM4's nonlinear pickup, but do not drive a `tanh` blindly.** Measured Rhodes models
   derive pickup voltage from the time derivative of position-dependent magnetic flux, and
   measurements show that the pickup turns near-sinusoidal tine motion into a more complex
   waveform. Separate work also identifies pickup intermodulation as a source of important
   modes. Therefore keep the pickup colour, but retune the relation between the upstream
   2.82·f0 tine partial and pickup drive so increasing strike velocity cannot compress that
   partial faster than it grows. A full electromagnetic solver is not required for this bug.
   Sources: [Real-time Physical Model of a Wurlitzer and Rhodes Electric
   Piano](https://www.dafx17.eca.ed.ac.uk/papers/DAFx17_paper_79.pdf)
   (DAFx 2017) and [The Rhodes electric piano: analysis and simulation of the inharmonic
   overtones](https://doi.org/10.1121/10.0002002) (JASA 2020).

### Autonomous implementation and regression brief

1. Sweep both bowed programs across their playable compass. At minimum include the diagnosed
   keys 36/48/50/55/60/67, compass boundaries, and velocities
   96/105/110/115/120/127. Classify the source motion as well as measuring level.
2. Jointly map `max_vel` and `slope` by program/register/velocity into the measured stable
   region. Do not repeat the rejected flat bow-speed clamp.
3. Add bounded residual normalization only if the stable map cannot satisfy the square-law
   level oracle. Compare adjacent-key steps against the pre-fix baseline and add no new
   register step greater than 1 dB beyond that baseline.
4. For GM4, tune the 2.82·f0 partial/pickup-drive relationship and restore a full non-decreasing
   bark assertion over v60/75/90/105/120/127. A plateau passes; deleting or bypassing
   `PickupShaper` does not.
5. Preserve all existing voice-character, velocity-law, DC, anti-alias, and deterministic
   render guards. Land the fix with failing-before/passing-after regression coverage and leave
   the bug `Fixed` for independent verification.

## Fix

### Fix summary (2026-07-27, Codex GPT-5.6, code=52d998be6339, gate=focused+render-diff)

GM42/43 now move bow speed and force together through a measured stable region. A slow
80 ms post-body meter applies only a bounded 0.60–1.70 residual gain after the sampled bow
catch hands over, leaving MIDI velocity's existing square-law output gain in charge of
loudness. GM4 keeps its nonlinear pickup, but its drive rises gently enough that the
2.82·f0 bark no longer falls after v105.

The scheduler-held implementation used the already-rejected near-flat bow-speed clamp. Its
single-seed level test passed while a multi-seed motion audit still found contrabass octave
locks. That patch was not landed. The replacement jointly maps bow speed and pressure,
retains the cello's high-register pressure ceiling, and verifies source motion independently
of output normalization.

Evidence:

- Full-compass calibration: 78 keys × 10 velocities × 4 engine-realistic seeds; zero
  unstable draws, zero velocity drops, and worst fitted `|k−2| = 0.042`.
- Full adjacent-key comparison at six high velocities and four seeds: worst new step over
  baseline `+0.66 dB`; worst candidate step `0.77 dB`, both below the 1 dB limit.
- Permanent source-motion, monotonic-level, square-law, register-cliff, GM4 bark, DC,
  identity, and existing whole-register gates pass with default and no-default features.
- GM4 bark/h1 is non-decreasing (`v60 0.0555`, `v90 0.0672`, `v120 0.0735`);
  GM4/GM5 onset, sustain, and distinctness guards remain green.
- Default and modeled-only focused tests pass; both focused Clippy configurations pass
  with warnings denied.
- Catalogue render diff against branch point `1927c2b`: albums `68 changed / 56 same`,
  demos `7 changed / 10 same`; zero contamination and zero not-reached tracks.
- Three-run reference-track render time: baseline `4.173 s`, candidate `4.182 s`
  (`1.002×`).
- Loudness-matched A/B renders are in
  `C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00029`.

Changed:

- `crates/ferrosintesis/src/voices.rs`: joint low-string bow controls, bounded residual
  normalization, GM4 pickup-drive retune, and motion/register calibration guards.
- `crates/ferrosintesis/src/velocity_law.rs`: removed the GM42/43 exemption and added the
  multi-seed monotonic/square-law regression.

Left alone:

- No crate version bump; this repository advances versions only during a deliberate release.
- No unrelated voice, album source, or generated listening asset.
