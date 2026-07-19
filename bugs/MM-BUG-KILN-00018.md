# MM-BUG-KILN-00018 — Natural brass (56–61) secondary spectral balance: h2–h5 ~17 dB below real brass's low-mid formant ring

- **State:** Closed
- **Priority:** Could
- **Severity:** Medium
- **Area:** voices
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-19, `5b5d80a`, repaired by `6220e71` — added onset-preserving, per-preset bell/body radiation for GM56–61 and a five-key SC-55 oracle. The unmuted trumpet/trombone/tuba/section medians were 17–20 dB weak before; after the fix all six natural programs are within 0.5–3.4 dB of their hardware median, while mute's opposite imbalance is corrected and GM62/63 remain inert. The repair preserves the LA handover, sustain levels, fixed-CC11 timbre, and high-register alias margin. All 26 non-ignored brass tests, the LA continuity and class-identity gates, the recaptured GM56 golden, and warning-free clippy pass. Render diff: all 125 catalog tracks rendered; exactly the 38 MIDIs using GM56–61 changed and 87 unrelated tracks remained byte-identical, with zero unexpected or missed tracks.); Closed (2026-07-19, verified by Claude Opus 4.8 (1M context) - independent two-eyes (fixer Codex GPT-5); brass_o17_low_mid_formant_ring_matches_sc55 + brass_o17_synth_brass_body_eq_is_inert green (h2-h5 within SC-55 bands; GM62/63 inert); gates green incl. clippy -D warnings)

## Observation

The round-3 brass "holds synthetic" liveness fix landed (living-breath modulator),
but a deeper spectral-balance miss remains: our h2–h5 are ~17 dB weaker than real
brass's low-mid formant ring (`wrk_docs/2026.07.16 - PLN - voice-quality round 3
... .md`, Brass section — parked behind the liveness fix as "a bigger, riskier
body-EQ change"). This is the residual realism gap for natural brass 56–61 once
the frozen-hold issue is addressed.

## Fix

A body-EQ change in the brass model (`Brass`, `crates/ferrosintesis/src/
voices.rs:~9544`) to lift the h2–h5 low-mid formant ring toward the measured SC-55
target, gated by its own oracle (recalibrated from hardware, not weakened) and the
render-diff inventory.

Implemented in `5b5d80a` and hardened in `6220e71`. Each natural preset owns a
measured bell/body radiation high-pass with level-neutral makeup. Ordinary bodies
settle before the timbre-hold window; tuba waits for its LA handover and applies
its stronger formants only to the hold path. The muted trumpet crossfades from its
original 750 Hz attack transmission to the hardware-calibrated hold and keeps its
nasal identity. The correction tapers above the measured register, preserving the
existing high-note alias margin.

`brass_o17_low_mid_formant_ring_matches_sc55` freezes dry velocity-96 SC-55
measurements at keys 48/52/56/60/64. It checks every key and the five-key median
for all six natural programs. `brass_o17_synth_brass_body_eq_is_inert` keeps
GM62/63 outside the correction.

The focused repair evidence is: 26/26 non-ignored `brass_` tests,
`la_level_continuity`, `non_guitar_la_render_is_pinned`,
`class_identity_ranges_hold`, formatting, diff checks, and warning-free
`cargo clippy -p ferrosintesis --all-targets -- -D warnings`. A detached-trunk
render comparison produced 125/125 files on both sides: 38 natural-brass tracks
changed, 87 unrelated tracks stayed byte-identical, and MIDI program scanning
found zero unexpected, missed, or ambiguous mappings.

### Verification summary (Claude Opus 4.8 (1M context), 2026-07-19)

Independent two-eyes on a worktree off origin/main (0cc8e7f, contains fixes 5b5d80a + 6220e71; verifier is not the fixer, Codex GPT-5). Both regressions passed in the green `cargo test --workspace` suite: `brass_o17_low_mid_formant_ring_matches_sc55` pins h2-h5 at keys 48/52/56/60/64 to frozen SC-55 targets (per-key +/-10 dB, median +/-7 dB) for all six natural programs GM56-61, and `brass_o17_synth_brass_body_eq_is_inert` confirms synth brass GM62/63 acquire no body correction. The ~17 dB low-mid formant-ring deficit no longer reproduces. Gates green: fmt, warning-free clippy -D warnings, release build.

## Notes

- The liveness fix recovered most of the "synthetic" perception; this is the next
  tranche of natural-brass fidelity.
- Higher risk than the liveness change — measure against SC-55 before/after and
  keep synth brass 62/63 untouched.
