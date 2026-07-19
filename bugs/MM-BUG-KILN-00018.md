# MM-BUG-KILN-00018 — Natural brass (56–61) secondary spectral balance: h2–h5 ~17 dB below real brass's low-mid formant ring

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-19, `5b5d80a` — added onset-preserving, per-preset bell/body radiation for GM56–61 and a five-key SC-55 oracle. The unmuted trumpet/trombone/tuba/section medians were 17–20 dB weak before; after the fix all six natural programs are within 0.5–4.9 dB of their hardware median, while mute's opposite imbalance is corrected and GM62/63 remain inert. All 25 non-ignored brass tests and warning-free clippy pass. Render diff: all 125 catalog tracks rendered; exactly the 38 MIDIs using GM56–61 changed and 87 unrelated tracks remained byte-identical.)

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

Implemented in `5b5d80a`. Each natural preset now owns a measured bell/body
radiation high-pass, crossfaded into the hold after 120 ms so the existing model
and LA layer retain the praised attack. The muted trumpet crossfades from its
original 750 Hz attack transmission to the hardware-calibrated hold and keeps its
nasal identity. Tuba's existing body peaks and radiated low-pass were recalibrated
to restore the ring without breaking the established family brightness order.

`brass_o17_low_mid_formant_ring_matches_sc55` freezes dry velocity-96 SC-55
measurements at keys 48/52/56/60/64. It checks every key and the five-key median
for all six natural programs. `brass_o17_synth_brass_body_eq_is_inert` keeps
GM62/63 outside the correction.

## Notes

- The liveness fix recovered most of the "synthetic" perception; this is the next
  tranche of natural-brass fidelity.
- Higher risk than the liveness change — measure against SC-55 before/after and
  keep synth brass 62/63 untouched.
