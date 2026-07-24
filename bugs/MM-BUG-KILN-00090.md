# MM-BUG-KILN-00090 — 31 tests fail under `--no-default-features`, blocking a test gate for the modeled-only build

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** build config / test coverage
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00070 by Claude Opus 4.8 (1M)
  while fixing it — 00070 delivered the clippy half and its gate; this is the residual that
  blocks the matching test step. Measured, not inferred.)

## Observation

**Symptom.** `cargo test -p ferrosintesis --no-default-features` fails: **536 passed, 31
failed**. Nobody knew, because the configuration has never been run by a gate
(MM-BUG-KILN-00070 — now fixed for clippy, which is why this is measurable at all).

```
$ cargo test -p ferrosintesis --no-default-features
test result: FAILED. 536 passed; 31 failed; 21 ignored
```

The 31:

```
engine::tests::cc32_defined_bank_selects_the_variation
engine::tests::cc71_resonance_builds_a_peak
engine::tests::cc74_brightness_filter
engine::tests::fast_same_key_restrikes_shimmer_not_click_train
engine::tests::o_attack_struck_attack_dominates
engine::tests::portamento_glides_from_previous_pitch
engine::tests::rpn_bend_range_and_fine_tune
engine::tests::solo_mutes_other_channels
testutil::distinctness::allowlisted_collapses_are_really_clones
testutil::distinctness::epsilon_is_calibrated_on_the_good_families
testutil::distinctness::every_gm_family_is_free_of_unexpected_clones
testutil::guards::determinism_bit_identical
testutil::guards::gm_routing_pins_voice_kinds
testutil::guards::golden_mix_balance_holds
testutil::perceptual_distinctness_requires_embedded_samples
testutil::pluck_baseline::shaped_g7_mean_parity_and_seed_bound
velocity_law::tests::drums_follow_the_same_law_as_melodic_voices
velocity_law::tests::every_gm_program_follows_the_square_law
velocity_law::tests::exempt_voices_keep_their_documented_velocity_behaviour
velocity_law::tests::looped_recording_voices_keep_their_documented_velocity_behaviour
velocity_law::tests::melodic_voices_follow_the_square_law
voices::tests::every_program_renders_at_every_common_rate
voices::tests::fx_o7_rain_96_real_recording_bed
voices::tests::gm0_grand_and_gm1_upright_are_distinct_instruments
voices::tests::guitar_treble_hold_decay_band
voices::tests::keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice
voices::tests::o_pitch_melodic_programs_model
voices::tests::steel_string_has_pick_sparkle
voices::tests::wd_o10_routing_sample_policy_and_lifecycle
```

(Two further failures — `a_routing_change_inside_the_tremolo_window_spawns_the_new_voice`
and `the_mandolin_strike_phase_is_bank_scoped_and_survives_a_retrigger` — were in the same
run and are already fixed: both assert sampled-bank routing and were feature-gated as part
of 00070.)

**Expected.** `--no-default-features` is a shipped, documented configuration
(`crates/ferrosintesis/README.md`, "Feature flags"). Its test suite should pass, so
`.deltic-integrate.toml` can gate it and keep it passing.

**Actual.** It has never been run, so nothing distinguishes a test that legitimately needs
the samples from a genuine modeled-only defect.

## Root cause — NOT yet established, and that is the work

Each of the 31 needs classifying, and the two categories need opposite treatment:

- **Should be `#[cfg(feature = "embedded-samples")]`** — the test is about the sampled
  configuration. `fx_o7_rain_96_real_recording_bed` (a real-recording bed),
  `perceptual_distinctness_requires_embedded_samples` (says so in its name) and
  `gm_routing_pins_voice_kinds` look like this class.
- **A real modeled-only defect** — the test is configuration-independent and the
  modeled-only synth genuinely misbehaves. `cc74_brightness_filter`,
  `portamento_glides_from_previous_pitch`, `rpn_bend_range_and_fine_tune` and
  `solo_mutes_other_channels` read as controller behaviour that should hold with no
  samples at all. If any of these is real, it is a shipped bug in the modeled-only synth
  and deserves its own entry.

**Do not mass-gate them.** Gating a test that exposes a real defect converts a red into
silent breakage, which is precisely the failure mode MM-BUG-KILN-00020 and 00070 are
about. Classify each, with evidence.

**One concrete finding already in hand.** `a_routing_change_...` did not fail an
assertion — it panicked in `sampler.rs`'s modeled-only `embedded_wav` stub
("sample … requested from a modeled-only ferrosintesis build") because its `CoreOptions`
set `samples: true`. A modeled-only build arguably should treat `samples: true` as "no
samples available" (the engine already has `crate::embedded_samples_available()`, which
`prewarm` consults) rather than panicking inside a voice constructor. Worth settling
while classifying, since it may explain several of the 31.

## Fix

1. Classify all 31 with evidence: feature-dependent (gate it) vs modeled-only defect
   (raise it, fix it).
2. Fix or gate accordingly — never by weakening an assertion.
3. Add `{ program = "cargo", args = ["test", "-p", "ferrosintesis", "--no-default-features", "--locked"] }`
   to `.deltic-integrate.toml`'s `workspace` gate and fallback, next to the
   `--no-default-features` clippy step 00070 added, so it cannot regress.

## Notes

- MM-BUG-KILN-00020 ("the perceptual anti-clone oracle silently vanishes under
  `--no-default-features`") is one instance of the coverage half of this and is still
  Open; expect the two to resolve together.
- Measured on `cargo test -p ferrosintesis --no-default-features` at the 00070 fix branch;
  the count excludes the two tests that fix already gated.
