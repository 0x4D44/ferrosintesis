# MM-BUG-KILN-00053 — GM49 Slow Strings does not swell at low keys: the SawStack `strings()` MODEL's low-register envelope falls (body/onset ~0.76-0.79) where both references rise

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-23
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00053-run-fix-20260727T030201Z-p9812-n539021900-c39-code-1785122329048
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) while fixing MM-BUG-KILN-00046 — the sampler-seam half of the same symptom; this is the model-envelope half) → Blocked (2026-07-26, GPT-5.6 Codex on KILN-Windows — the required low-register envelope revoicing needs Arthur to choose the audible swell depth and timing against the two references) → Open (2026-07-26, Arthur approved a reference-like low-register amplitude swell, tapering into the existing key-55 anchor) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T030201Z-p9812-n539021900-c39 branch=task/bug-MM-BUG-KILN-00053-run-fix-20260727T030201Z-p9812-n539021900-c39 code=60491c9d5b04 gate=cargo model=codex@xhigh)

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

## Fix

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T030201Z-p9812-n539021900-c39 code=60491c9d5b04 gate=cargo)

Agent-reported summary: Fixed MM-BUG-KILN-00053 by giving GM49 Slow Strings a real low-register amplitude swell in the model path. The new regression fails on the pre-fix tree with key 48 model body/onset around 1.06 and full sampled body/onset around 0.91. After the fix, key 48 model body/onset is 2.11 at velocity 72 and 2.04 at velocity 110, with key 52 tapering between key 48 and the unchanged key 55 anchor. The GM49 low-key LA sample taper now follows the same swell depth so the full sampled voice rises instead of flattening the model swell. Existing string LA seam, pitch, audibility, and swell-preservation tests remain green.

Root cause: GM49 reused the generic SawStack ADSR whose overshooting attack reaches full level early and then settles toward sustain; in the low saw-stack register this put too much RMS into the 0-0.4 s onset window, so the 0.8-1.2 s body was not sufficiently louder, and the old low-key sample taper then masked the corrected swell.

Changed:
- crates/ferrosintesis/src/voices.rs: added an inert-by-default SawStack amplitude swell and applied a curved low-key GM49 ramp below key 55
- crates/ferrosintesis/src/voices.rs: reduced only GM49 low-key string sample seam gain along the same swell-depth curve
- crates/ferrosintesis/src/sampler.rs: restored the la_strings_slow_swell_not_inverted regression and updated stale KILN-00046 comments

Tests:
- $null | cargo test -p ferrosintesis la_strings_slow_swell_not_inverted -- --nocapture
- $null | cargo test -p ferrosintesis la_strings -- --nocapture
- $null | cargo test -p ferrosintesis slow_strings_variation_has_longer_attack_than_base -- --nocapture
- $null | cargo test -p ferrosintesis sawstack_family_signatures_are_stable -- --nocapture
- git diff --check

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

### Decision and implementation contract — 2026-07-26

Arthur approved this target:

- At key 48, the 0.8–1.2 s body should be **+6 to +8 dB** above the
  0–0.4 s onset (RMS ratio approximately 2.0–2.5), at velocities 72 and 110.
- The body should arrive around **1.0 s**. Avoid a delayed step or an attack so
  slow that the note still feels absent at 1.2 s.
- Taper the additional low-register swell smoothly through key 52 into key
  55's existing mild rise. Treat key 55 as the unchanged transition anchor.
- Both model-only and full sampled GM49 must rise in the same direction after
  the MM-BUG-KILN-00046 sampler-seam correction.

Implement the swell in the model's amplitude-envelope path. First pin down why
the low-frequency oscillator/filter interaction defeats the current
`vel_attack(0.45, vel)` shape; do not simulate a swell by brightening the filter
while level still falls. Keep GM48 Strings and the existing mid/high GM49
envelope unchanged.

Extend `la_strings_slow_swell_not_inverted` to cover keys 48, 52, and 55 at
velocities 72 and 110, across seeds 5, 21, and 99. The oracle must check the
approved key-48 band, a smooth register taper without a key-52 discontinuity,
the preserved key-55 anchor, and consistent model-only/full-voice direction.
Also retain sample/model seam parity, determinism, finite output, and existing
strings-family controls.

After focused tests pass, run the required full catalog render diff and create
body-level-matched trunk-versus-candidate A/B renders for the audition matrix.
Land the implementation as **Fixed**, not Closed, for independent verification
and final perceptual sign-off.
