# MM-BUG-KILN-00041 — GM126 Applause is a monochromatic 2.4–3.1 kHz sizzle (two fixed bandpasses + over-density), not resolvable claps

- **State:** Fixed
- **Priority:** Could
- **Severity:** Medium
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL instrument-audition review; "terrible" — Arthur's ear, code-confirmed) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — replaced the fixed 360-event/s sizzle with sparse, per-clap broadband resonators and corrected the +9.13 dB calibration residual)

## Observation

GM126 (Applause) sounds "terrible" — a harsh continuous band-limited sizzle rather than a
crowd of resolvable claps. It is also ~9 dB hot (M-CAL residual +9.13).

## Root cause

`SfxApplause` (`crates/ferrosintesis/src/voices.rs:624`): **every** clap grain runs one of
just **two FIXED narrow bandpasses** — clap1 2400 Hz Q0.8, clap2 3100 Hz Q0.9
(`voices.rs:640-641`) — so the crowd is a monochromatic 2.4–3.1 kHz sizzle with no per-clap
spectral variation and no low-mid body (real claps are broadband transients with 200 Hz–1 kHz
body). At ~360 claps/s (gate1 150 Hz + gate2 210 Hz, `voices.rs:638-639`) with ~8–10 ms grain
decay (t60 0.010/0.008), grains overlap into continuous band-limited noise rather than
resolvable claps. Timing is NOT the fault — `GrainGate` is a stochastic Poisson gate
(`crates/ferrosintesis/src/dsp.rs:761`), not a periodic buzz. The defect is spectral (two
fixed high bands, no body) plus over-density. The 1.30× amp (`voices.rs:643`) also makes it
~9 dB hot.

## Fix direction

Randomize each clap's bandpass centre across a broad band (~0.8–4 kHz) and add low-mid body
instead of the two fixed 2.4/3.1 kHz filters; and/or thin the ~360 claps/s so individual
claps resolve. Separately drop the 1.30× amp (the +9.13 residual confirms it is also ~9 dB
hot) — but the harsh synthetic spectrum is the primary complaint, not the level.

## Resolution — 2026-07-25

GM126 now runs four independent clap streams totaling 84 events/s. Each fresh
event chooses a new logarithmic low-mid body centre from 250–1,000 Hz and a new
upper snap centre from 800–4,000 Hz. Broad, paired resonators replace the two
fixed 2.4/3.1 kHz filters, so the crowd varies from clap to clap without losing
the existing stochastic timing or held-note envelope.

The obsolete 1.30 output gain is gone. A 0.71 calibration trim places the
redesigned voice on the M-CAL target after the density and spectrum changes.
`GrainGate` now exposes a crate-private fresh-event flag while preserving the
existing one-draw `next()` behavior for every other consumer.

## Verification — 2026-07-25

- The fail-first regression measured body/presence `0.249` on the old voice and
  failed its `0.45` floor. The fixed voice measures `0.640`, with an
  air/presence ratio of `0.604` and 5 ms envelope coefficient of variation
  `0.895`; this proves broadband energy and resolvable pulses.
- Equal-velocity held RMS falls from `0.356×` piano to `0.124×`, a 9.2 dB
  correction matching the recorded +9.13 dB residual.
- The GM126 focused tests and the sample-rate-independent `GrainGate` test pass.
- `$null | cargo test -p ferrosintesis --locked`: 722 unit tests and 4 doc
  tests passed; 27 diagnostics ignored.
- `$null | cargo test -p ferrosintesis --no-default-features --locked`: 621
  unit tests and 4 doc tests passed; 22 diagnostics ignored.
- Strict workspace clippy and model-only clippy pass with all targets and
  warnings denied. Formatting and `git diff --check` pass.
- Fresh release binaries from exact baseline `bca9671`, full 124-MIDI inventory
  at 11.025 kHz: 124 byte-identical and zero contamination. No catalog MIDI
  selects GM126, so the focused oracle supplies the reachability evidence.
