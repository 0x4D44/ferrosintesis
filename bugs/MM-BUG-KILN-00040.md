# MM-BUG-KILN-00040 — GM120 Guitar Fret Noise is pinned near-silent (~18 dB under the SC-55 reference)

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL
  instrument-audition review; effectively inaudible vs SC-55, code-confirmed) → Fixed
  (2026-07-24, `1780465`+`30e6877`, GM 120 given a sampled finger-slide voice; awaiting
  two-eyes verification)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

GM120 (Guitar Fret Noise) is effectively **silent** in the reference audition — measured
~18 dB under the SC-55 for the same event. `CLAUDE.md` documents 120 as the remaining
intentional "toneless squeak transient", but the audition shows it inaudible where the
reference is clearly present.

## Root cause

`SfxNoise` for 120 uses gain **0.09** (`crates/ferrosintesis/src/voices.rs:174`) with a
~0.12 s decay — a deliberately short, quiet noise transient (`voices.rs:220` frames it as
such). The model shape is fine; it is pinned near-silent. This is a **level** issue, not
timbre, and the PROGRAM_TRIM table cannot touch it: 120 is in the never-trim SoundFX class,
and −18 dB exceeds the ±6 dB clamp anyway.

## Fix direction

Raise the SfxNoise 120 voice gain (and/or lengthen the decay) so the squeak is audible at a
level comparable to the reference. A voice-level fix, not a strip trim. Low priority (a niche
SFX voice, no in-repo album authors it), but the audition makes the gap plain.

## Resolution (2026-07-24)

A three-engine audition (ferrosintesis vs a cycle-accurate Roland SC-55mkII and Yamaha
S-YXG50, via `mdmidiemu`) confirmed the gap was **not level alone** — the original
root-cause note understated it. Measured on the loudest bare event, the modeled burst was:
level −23 dB under a steel-guitar chord (references −11.6 / −10.9), centroid ~3.8 kHz with
~37 % of energy above 4 kHz (references ~1.7–2.0 kHz, ~2 %), and ~60 ms long (references
~230–340 ms). It read as a distant click, not a squeak — so a gain bump alone would have
made a *louder* wrong sound.

Fixed by giving GM 120 a real sampled voice instead: Arthur recorded finger-slide noise on
his Eastman E1D (all strings damped), and 12 takes were baked into a new CC0 crate
`ferrosintesis-samples-fretnoise` and played as a round-robin one-shot
(`sampler::sampled_fret_noise` / `FretNoiseOneShot`), behind `if samples`. `--no-samples`
and modeled-only builds keep the `SfxNoise` burst. `FRETNOISE_LEVEL = 0.23` was calibrated
so the slide sits −11.2 dB under the steel guitar; the rendered character now lands between
the two references on every axis (centroid 1784 Hz, 1.3 % > 4 kHz, 220 ms decay).

**Regression** (all render `samples = true`, in `voices.rs`):
`gm120_sampled_beats_the_modeled_burst_level` (differential vs the modeled control),
`gm120_sampled_is_a_narrowband_rasp_not_a_hiss` (band + centroid), plus one-shot-while-held,
pitch-independence, and round-robin-variety oracles. The existing modeled oracle
(`gm120_fret_squeak_is_a_quiet_toneless_one_shot`, renders `samples = false`) is unchanged
and still green. Render-diff (`--program 120`): the two GM120 demo tracks change, zero
albums, zero contamination.

Commits `1780465` (crate + bake) and `30e6877` (voice + dispatch + oracles). Awaiting
two-eyes verification before Closed.
