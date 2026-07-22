# MM-BUG-KILN-00041 — GM126 Applause is a monochromatic 2.4–3.1 kHz sizzle (two fixed bandpasses + over-density), not resolvable claps

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL
  instrument-audition review; "terrible" — Arthur's ear, code-confirmed)

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
