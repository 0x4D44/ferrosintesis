# MM-BUG-KILN-00053 — GM49 Slow Strings does not swell at low keys: the SawStack `strings()` MODEL's low-register envelope falls (body/onset ~0.76-0.79) where both references rise

- **State:** Blocked
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-23
- **Owner:** Arthur
- **Owner role:** human
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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) while fixing MM-BUG-KILN-00046 — the sampler-seam half of the same symptom; this is the model-envelope half) → Blocked (2026-07-26, GPT-5.6 Codex on KILN-Windows — the required low-register envelope revoicing needs Arthur to choose the audible swell depth and timing against the two references)

## Observation

**Symptom.** GM49 "Slow Strings" should swell — both reference synths rise from note-on
(the SC-55 rises +7.9 dB over the first ~1 s at key 48). ferro reads loudest at note-on
and settles. KILN-00046 fixed the sampler-seam contribution (the sampled section onset was
speaking +1..+6 dB over the model). But isolating the model with `--no-samples` shows the
**model itself does not swell at low keys**:

```
GM49 model-only body/onset (RMS mean 0.8-1.2 s ÷ mean 0-0.4 s), seed 5:
  key 48  vel 72  0.79   vel 110  0.76     <- FALLS (no swell)
  key 55  vel 72  1.18   vel 110  ~1.1
  key 58  vel 72  1.30   vel 110  1.22
  key 68  vel 72  1.27   vel 110  1.20
```

So the model swells in the mid register but not the low. Even with the sampled onset
perfectly level-matched, ferro's GM49 cannot swell at key 48 — the envelope it hands to is
already falling.

**Expected.** A slow-strings patch swells across its whole range, as both references do.

**Actual.** The low register (≤ ~key 52) is flat-to-falling.

**Reproduce.** `cargo test -p ferrosintesis la_strings_slow_swell_not_inverted -- --nocapture`
prints the `model-only` column; compare it against 1.0 at keys 48/55/58/68.

## Root cause

The `strings()` SawStack model (`crates/ferrosintesis/src/voices.rs`, the `48..=49` builder;
`vel_attack(0.45, vel)` slow-section attack) reaches its plateau early and settles at low
keys rather than continuing to build — the mechanism (attack curve vs the ST1 envelope-
brightness ramp interaction at low f0) is not yet pinned. This is the model's own envelope,
independent of the LA sample layer.

## Fix direction

Give `strings()` a genuine low-key swell so body ≥ onset across the range like the
references (lengthen / re-curve the low-register attack, or couple the swell to the ST1
brightness ramp). Needs ears (this box has none) and the render-diff inventory. KILN-00046's
`la_strings_slow_swell_not_inverted` deliberately guards swell-preservation only where the
model already swells (`m > 1.05`); closing this bug extends that guard to the low register.

## Notes

- Found while fixing MM-BUG-KILN-00046 (the sampler-seam level parity). 00046 is the
  sampler half (fixed); this is the model half.
- Low priority: the low strings register is rarely the exposed melodic line, and the fix is
  an ears-in-the-loop voicing change.

## Blocker — 2026-07-26

Blocking owner: **Arthur**. The code already distinguishes GM49 with a 0.45 s
velocity-scaled attack, but the low-register oscillator/filter interaction makes
that envelope settle downward. Lengthening or reshaping the attack can force an
objective rise, yet the honest target is perceptual: too little retains the
defect; too much makes low ensemble notes speak late and weak. The two reference
synths establish direction but not which depth should become ferro's contract.

Unblock with one body-level-matched audition matrix. Hold each note for 1.5 s,
match level on the 0.8–1.2 s body, and compare current model-only GM49, current
full sampled GM49, SC-55, and S-YXG50 for:

- keys **48, 52, and 55**;
- velocities **72 and 110**;
- ferro seeds **5, 21, and 99**.

Return these exact product inputs:

1. Choose the low-key swell target: **gentle** (+1 to +4 dB body/onset),
   **reference-like** (+6 to +9 dB), or a stated custom dB band.
2. Choose when the body should arrive: by **0.8 s**, by **1.2 s**, or a stated
   custom time.
3. Confirm whether key 55's current mild rise should remain the transition
   anchor, or should be revoiced with keys 48/52.
4. Confirm that both model-only and the full sampled voice must meet the same
   directional target after MM-BUG-KILN-00046's seam correction.

Those four answers are enough for a Build pass to select one envelope curve,
extend `la_strings_slow_swell_not_inverted` through the low register, and return
a bounded candidate A/B for final listening. No objective test can choose the
depth and timing without silently making this product decision.
