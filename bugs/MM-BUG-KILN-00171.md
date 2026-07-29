# MM-BUG-KILN-00171 — Long-held rotating-phasor oscillators drift in amplitude

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** DSP / oscillator stability
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, promoted from the 2026-07-18 scratchpad observation by GPT-5.6 Codex)

## Observation

`D:\language\midi-music\crates\ferrosintesis\src\dsp.rs:31` implements `Sine`
as a two-dimensional `f32` rotation. `Sine::next` multiplies the current phasor
by the rounded `(cos(w), sin(w))` coefficient on every tick but never
renormalizes the phasor.

The coefficient therefore has a fixed magnitude slightly different from one.
The oscillator magnitude follows that bias systematically rather than as a
random walk. The 2026-07-25 measurement recorded amplitude movement of
+0.022 dB after 200,000 ticks, +0.089 dB after 800,000 ticks, and +0.397 dB
after 3.2 million ticks. The movement scales roughly fourfold when the tick
count scales fourfold.

**Expected.** A constant-frequency `Sine` remains at unit magnitude for an
arbitrarily long held note.

**Actual.** Its magnitude drifts monotonically until the oscillator is rebuilt
or `set_freq` replaces the rounded rotation coefficient. All current uses are
per-note voices, control-rate LFOs, or bounded loops, so normal catalogue
exposure is low. The generic player and realtime path can still hold a foreign
MIDI note for many minutes; the prior measurement projects roughly 8 dB of
inter-partial spread on a ten-minute additive drone.

The existing `dsp.rs:sine_stays_bounded` test runs for only one second. It
cannot see the accumulated error and passes on the drifting implementation.

## Fix

Renormalize the phasor occasionally, with an interval chosen to bound long-hold
error without putting a square root in every sample. Add a regression that
runs long enough to fail the current implementation and bounds both magnitude
and frequency. Because `Sine` feeds many voices, run the repository's required
render-diff inventory before marking the bug Fixed.

## Notes

This was promoted instead of fixed during scratchpad triage because the code
change is tiny but its blast radius is synth-wide. The interval and acceptable
bit movement need deliberate calibration.
