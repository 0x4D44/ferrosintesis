# MM-BUG-KILN-00030 — the harpsichord's LA sample onset does not track its vel_sense-compressed model, so at v100 the sustain edges out the quill attack (~12% late bloom)

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-20, raised by Claude Opus 4.8 during the velocity-law alignment to k=2; caused by this change and diagnosed to the mechanism below) → Fixed (2026-07-25, Claude Opus 5 (1M) @ xhigh, `d1245e9`; shared `vel_sense` onset law and regression coverage landed) → Closed (2026-07-25, independently verified by Codex GPT-5; exact late-bloom observation red on `b736bd7` and green on `da8215c`; full repo gate green)

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

## Fix (2026-07-25)

Both halves of the exit condition met, exactly as written and with `vel_sense` preserved.

**The onset now sees the same compressed velocity the model does.** The compression law was
open-coded in `voices::Pluck::new` only, so `sampler.rs`'s onset gain — whose own comment
claims "ONE velocity-level law, shared with the wrapped model" — could not honour that claim
for the one voice that compresses. It is now a single shared definition, `dsp::vel_sense_norm`
/ `dsp::vel_amp_sensed`, called by both sides; `LaFx::vel_sense` carries the wrapped model's
sensitivity, and GM 6 moves from `LaVoice::wrap` to `wrap_fx` to pass it. `None` (every other
voice) is bit-identical to the previous bare `vel_amp`.

**Confinement.** Every path this change touches is gated on either `LaFx::vel_sense` (set at
the GM 6 wrap site alone) or `VEL_LEVEL_EXP[6]`, so only GM 6 can move. Measured corroboration:
the `--no-samples` body levels are bit-identical to trunk at every probed velocity
(−16.42 / −17.70 / −18.20 / −18.75 / −18.97 / −19.16 / −19.44 dB) *before* the
`VEL_LEVEL_EXP[6]` removal, which is the `vel_sense_norm` refactor proving itself inert.
A census of all 141 committed album/demo MIDIs finds **4** that author GM 6 — `Atlas of
Becoming/11 - Clockwork Orchard`, `demos/ferrosintesis_reference/01`,
`demos/synth_feature_showcase/02` and `/05` — and those are the only renders that may change.
(Note for the record: MM-BUG-KILN-00044 states "no committed album authors GM6"; that was a
grep for the word *harpsichord* in album Python sources, which misses both the demos and
Clockwork Orchard's own program change. The program-change census above supersedes it.)

Deliberately NOT the floored `X + Y·vel_amp` onset the abandoned 2026-07-21 branch
(`origin/claude/bugs-queue-2q-drain-609csu`) used. `dsp::vel_amp`'s doc comment forbids that
shape by name — "Never add a level floor of the form `X + Y·vel_amp(v)`: that is not a power
law at all" — and names compressing velocity before the curve as the sanctioned alternative.
That branch is superseded and can be reaped.

**Result.** `assert_attack_is_peak`'s harpsichord-low bloom falls **1.118 → 0.743**, tripping
the `<= 1.02` side of its own bound, so the named exception is deleted and the harpsichord now
meets the same attack-owns-the-peak rule as every other struck voice.

**This unmasked, and required fixing, half of MM-BUG-KILN-00044.** `VEL_LEVEL_EXP[6] = 1.500`
existed *only* to compensate for this bug — its comment said so: "Its LA sample layer does not
inherit that compression, so the composite over-responds." It billed the whole voice for a
crossfade defect: `(v/127)^-0.5` made the model body 5.02 dB LOUDER at v40 than v127, and
applied even under `--no-samples` where there is no LA layer at all. With the onset tracking,
the compensation had nothing left to compensate, so the entry is removed. Measured at key 60:

| | v40 | v72 | v110 | v127 | span |
|---|---|---|---|---|---|
| body, before | −16.42 | −18.20 | −19.16 | −19.44 | **−3.02 dB** |
| body, after | −21.44 | −20.67 | −19.78 | −19.44 | **+2.00 dB** |
| composite, after | −24.85 | −24.15 | −23.34 | −23.00 | **+1.85 dB** |

Monotone rising, matching the `vn²` law's predicted +1.88 dB, and composite ≈ body — the
velocity-invariant crossfade ratio the LA design intended. The body's +2.42 dBFS peak at v40
is gone too.

**Not weakened, any of them.** The three guards MM-BUG-KILN-00044 warns must be re-decided
together all pass **unmodified**: the `< 3.0` contract and `loud > soft`
(`exempt_voices_keep_their_documented_velocity_behaviour`), the `<= 1.5` body-spread pin in
`keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice`, and the GM6 square-law
exclusion. This change removes a workaround; it relaxes no assertion.

### New guard

`velocity_law::corrected_programs_still_rise_with_velocity` — derived from `VEL_LEVEL_EXP`
itself, so it needs no maintenance: every program the table actually corrects must still get
louder as it is played harder. Verified adversarially — re-introducing `t[6] = 1.500` makes it
fail naming the exact program and margin (`GM6 (e=1.500): v48 -20.45 dB -> v120 -22.89 dB
(-2.44)`), then passes again when removed.

### What this does NOT fix

MM-BUG-KILN-00044's *reference-fidelity* half is untouched and that bug stays open. Both
reference modules give GM6 a near-square-law +6.6/+8.3 dB over v72→v110; ferrosintesis now
gives +0.89 dB (was −0.96). The remaining gap is `vel_sense: 0.15` itself — a deliberate
physical-realism choice, and changing it is a re-voicing needing ears and all three guards
re-decided together. See that bug.

### Independent closure verification (2026-07-25 — Codex GPT-5)

- Applied the fixed `assert_attack_is_peak` rule to pre-fix parent `b736bd7`.
  `la_level_continuity` reproduced the recorded harpsichord-low failure exactly:
  late window `0.06607` exceeded attack `0.05910`. The same test passed on
  post-fix trunk `da8215c`.
- `corrected_programs_still_rise_with_velocity` passed on post-fix trunk. Its
  documented adversarial condition was also checked: reintroducing
  `VEL_LEVEL_EXP[6] = 1.500` made it fail on GM6 with the recorded −2.44 dB
  inversion, then it passed again after removing the temporary change. On the
  complete pre-fix tree this secondary guard passes because the two old defects
  cancel in the sampled composite; the attack oracle above is the red-before
  regression for MM-BUG-KILN-00030.
- Reviewed the root cause: both `Pluck` and `LaVoice` now use the shared sensed
  velocity law, and only GM6 supplies `LaFx::vel_sense`. This directly restores
  velocity-invariant onset/body tracking without changing the physical
  `vel_sense` choice.
- The refreshed repo gate passed on `da8215c`: fmt, workspace clippy,
  modeled-only clippy, and workspace tests. No residual gap remains in this
  bug; the distinct reference-fidelity question remains MM-BUG-KILN-00044.

## Provenance

Found while implementing `wrk_docs/2026.07.20 - HLD - velocity law alignment to k=2.md`.
Distinct from MM-BUG-KILN-00029 (voice-model velocity turnover): this is a
sample/model **crossfade** interaction specific to the one `vel_sense` + LA voice, caused by
this change rather than merely exposed by it.
