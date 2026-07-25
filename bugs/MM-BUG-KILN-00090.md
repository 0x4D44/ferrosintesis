# MM-BUG-KILN-00090 — 31 tests fail under `--no-default-features`, blocking a test gate for the modeled-only build

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00070 by Claude Opus 4.8 (1M) while fixing it — 00070 delivered the clippy half and its gate; this is the residual that blocks the matching test step. Measured, not inferred.) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — the exact locked modeled-only suite passes and is now required by both integration gates) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the pre-fix parent reproduced exactly the 3 classified failures; trunk is 614/0)

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

## Resolution — 2026-07-25

The stale 31-test list was reclassified against `origin/main` at `d3ac026`:

- **28 no longer reproduced and remained enabled.** They passed in the modeled-only run,
  which proves they were not hidden by feature gates in this fix.
- **One genuinely sample-dependent coverage case** was the deliberate
  `perceptual_distinctness_requires_embedded_samples` panic. The real perceptual oracle
  remains sample-feature-gated. Its failing sentinel became a positive source oracle that
  requires the integration contract to pair the default-feature workspace suite with the
  modeled-only suite in both fallback and component gates. This preserves
  MM-BUG-KILN-00020's anti-silent-omission invariant without making a supported build fail
  by design.
- **Two velocity-law failures were real modeled-only defects.** The default
  `VEL_LEVEL_EXP` values describe sampled/composite voices, but a no-default build always
  constructs physical models. A compile-time modeled-only calibration now overrides the
  measured GM24, GM56/57/59, and GM64–67 values. GM24 stays capped at the existing 2.350
  anti-papering bound.
- The repaired calibration exposed **two level-sensitive GM24 canaries**. Their default
  baselines remain frozen; the modeled-only expectations carry only the analytic exponent
  delta. Spectral and envelope expectations did not move.

Evidence:

- `$null | cargo test -p ferrosintesis --no-default-features --locked`:
  **612 unit tests + 4 doc tests passed; 22 diagnostic tests ignored**.
- `deltic integrate-config validate --json`: candidate policy valid; AUTO remains off.
- Fresh release binaries from exact baseline `d3ac026` and the fixed branch rendered every
  catalog MIDI at 11.025 kHz: **124 same, 0 changed, 0 contamination**. The default product
  is byte-identical.
- MM-BUG-KILN-00105 remains the separate runtime concern: a default-feature binary that is
  asked not to use samples, or falls outside a sample zone, still chooses compensation by
  program rather than the voice actually built.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before at the **exact pre-fix parent** `d3ac026`:
`cargo test -p ferrosintesis --no-default-features --locked` → **609 passed, 3 failed,
22 ignored**. The three are precisely the ones the Resolution classifies:

- `testutil::perceptual_distinctness_requires_embedded_samples` — the deliberate sentinel panic;
- `velocity_law::tests::melodic_voices_follow_the_square_law` — GM24 key 48 exponent **1.704**
  against a 2.0 ± 0.2 band;
- `velocity_law::tests::every_gm_program_follows_the_square_law` — GM24=**1.72**, GM64=**2.37**,
  GM65=**2.45**, GM66=**2.47**, GM67=**2.41**.

That run independently confirms the "28 no longer reproduced and remained enabled" claim: the
other 28 of the stale list pass at the baseline, so the fix did not hide them behind gates.

Green after on trunk: **614 passed, 0 failed, 22 ignored**, plus 4 doc-tests. (The ledger
records 612 at the fix; the tree has since gained two tests. Higher count, still zero failures.)

The contract half also holds — this bug's whole point was that the configuration must be
gated, not merely green once:

- the modeled-only test step appears in **both** `.deltic-integrate.toml` `fallback` and the
  `workspace` component gate;
- `crates/ferrosintesis/src/testutil.rs:no_default_gate_is_paired_with_embedded_sample_coverage`
  exists and passes, so the pairing cannot silently lapse;
- `deltic integrate-config validate --json` reports the policy valid.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

- MM-BUG-KILN-00020 ("the perceptual anti-clone oracle silently vanishes under
  `--no-default-features`") is the coverage half of this and is Closed. Its required
  samples-on oracle is now pinned through the paired integration-contract test above.
- Measured on `cargo test -p ferrosintesis --no-default-features` at the 00070 fix branch;
  the count excludes the two tests that fix already gated.
