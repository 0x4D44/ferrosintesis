# MM-BUG-KILN-00030 — the harpsichord's LA sample onset does not track its vel_sense-compressed model, so at v100 the sustain edges out the quill attack (~12% late bloom)

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
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
  alignment to k=2; caused by this change and diagnosed to the mechanism below) → Blocked
  (2026-07-21, Claude Opus 4.8 — the suggested fix (onset tracks the vel_sense model, `vn²`)
  DOES restore the attack peak but INVERTS the harpsichord's aggregate velocity response,
  failing `exempt_voices_keep_their_documented_velocity_behaviour`; the correct onset law is
  a tuning/ears design extension entangled with MM-BUG-KILN-00029.) → Fixed (2026-07-21,
  Claude Opus 4.8 — a FLOORED onset law `0.50 + 0.50·vel_amp` for vel_sense voices restores
  the quill attack peak across the velocity range AND keeps the velocity response monotone;
  both oracles green, regression test added `427281a`)

## Observation

The k=2 velocity-law work changed the generic LA sample-onset gain law from a floored
`0.35 + 0.65·vel_amp(v)` to bare `vel_amp(v)` (`crates/ferrosintesis/src/sampler.rs`, the
`fx.vel_level` → `vel_gain` site). The design's stated intent (HLD §3.3) is that the
sample onset should **track the wrapped model's law** so the onset/sustain crossfade ratio
stays velocity-invariant. For every voice whose model is now bare `vel_amp`, bare LA onset
tracks correctly.

**The harpsichord (GM6) is the exception.** It is the only voice combining an LA sample
layer with `vel_sense` velocity compression (`vel_sense: 0.15` — a real harpsichord is
nearly velocity-independent). Its model velocity is compressed *before* the square law, so
its effective body gain is not bare `vel_amp`. Bare LA onset therefore does **not** track
it: at v100 the sampled quill onset dropped ~2.3 dB relative to the model body
(old onset gain `0.35 + 0.65·(100/127)^1.6 = 0.805`; new `(100/127)² = 0.620`).

Consequence, measured through `la_level_continuity` (`assert_attack_is_peak`, harpsichord
key 48, v100): the loudest 50 ms window is no longer the first. Attack window max 0.05910;
a later window (0.15–0.20 s) reaches 0.06607 — a ~12 % ("1 dB") late bloom. For an
instrument whose defining timbre is the quill pluck transient, the attack should own the
peak.

## Severity

**Low.** One voice, and only where the attack and a near-attack sustain window are within
~1 dB. The harpsichord is deliberately near-velocity-independent, so the audible stakes are
small. It is filed rather than fixed because the correct fix touches the LA-onset law's
relationship to `vel_sense`, which is a small design extension, not a constant tweak, and
this task's scope is the velocity *law*, not the harpsichord's sample crossfade.

## Current containment

`assert_attack_is_peak` carries a **named, bounded, self-retiring** exception for
`harpsichord-low` (`crates/ferrosintesis/src/sampler.rs`): the bloom must stay in
`[1.02, 1.25)`. If a fix makes the onset track again (bloom ≤ 1.02) the assertion fails and
forces this exception to be deleted; if the interaction worsens (> 1.25) it also fails.

## Exit condition

The harpsichord's LA sample onset tracks its `vel_sense`-compressed model velocity (e.g. the
onset law sees the same compressed velocity the model does), so the quill attack owns the
peak again at every velocity and the `harpsichord-low` exception in `assert_attack_is_peak`
can be removed.

## Provenance

Found while implementing `wrk_docs/2026.07.20 - HLD - velocity law alignment to k=2.md`.
Distinct from MM-BUG-KILN-00029 (voice-model velocity turnover): this is a
sample/model **crossfade** interaction specific to the one `vel_sense` + LA voice, caused by
this change rather than merely exposed by it.

## Fix (2026-07-21, Claude Opus 4.8)

A `vel_sense`-compressed model (only the harpsichord) is near velocity-flat by design, so its
velocity dynamics must be carried by the sampled ONSET, not the body. The onset therefore gets
a **floored law** — `vel_gain = 0.50 + 0.50·vel_amp(vel)` — gated by a new `LaFx.vel_sense_onset`
flag set only at the GM6 wrap site; every other voice keeps bare `vel_amp` byte-for-byte. The
floor lifts the mid/low-velocity attack back above the sustain (fixing the bloom) while the
`vel_amp` term keeps a monotone velocity slope. The self-retiring `harpsichord-low` exception in
`assert_attack_is_peak` was deleted (its exit condition met).

**Calibration.** Swept the floor against both oracles:

| floor | bloom v64 | bloom v100 | velocity monotone? |
|---|---|---|---|
| 0.00 (bare vel_amp, pre-fix) | 1.41 | 1.12 | yes (but blooms) |
| 0.35 | 1.21 | 0.92 | yes |
| **0.50 (chosen)** | **0.99** | **0.86** | **yes** |
| 0.65 | 0.84 | 0.80 | **NO — inverts** |

0.50 is the highest floor that keeps the quill attack the peak across the velocity range
without inverting the (deliberately shallow) velocity response. `vn²` (equivalent to floor
→ near-1 in flatness) was the dead-end that inverted it (see below).

**Rejected dead-end — `vn²` (tracking the model literally, as the exit condition suggested).**
It fixed the bloom (0.743) but INVERTED the velocity response: the loud flat onset exposed the
model's own inverted-in-LUFS behaviour the quiet onset had masked, so v72 rendered LOUDER than
v110 and `exempt_voices_keep_their_documented_velocity_behaviour` failed. The floored law keeps
the onset's `vel_amp` slope, which is what preserves monotonicity.

### Verification

- `sampler::tests::harpsichord_onset_floor_keeps_attack_peak_and_velocity_monotone` (new) —
  attack owns the peak at v64/90/100/120 AND v72-level < v110-level. Confirmed to FAIL on the
  pre-fix tree (v64 bloom) and pass after.
- `sampler::tests::la_level_continuity` (harpsichord-low/-/-high rows now run the normal
  attack-is-peak check, the deleted exception) — green.
- `sampler::tests::exempt_voices_keep_their_documented_velocity_behaviour` — green (velocity
  still monotone, span < 3 dB).
- Confined to `vel_sense_onset` voices = GM6; only one album track (Atlas of Becoming /
  "Clockwork Orchard") uses GM6, so the render-diff touches exactly that one track (a timbre
  improvement per the default-on policy) and nothing else.
