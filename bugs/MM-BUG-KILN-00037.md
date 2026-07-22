# MM-BUG-KILN-00037 — GM31 guitar harmonics is a frequency-only retune: renders as a plain pluck, not a flageolet

- **State:** Open
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
  instrument-audition review; "sounds just like plucking" — Arthur's ear, code-confirmed)

## Observation

GM31 (guitar harmonics / flageolet) "sounds just like plucking" — it does not read as a
touched harmonic (the glassy near-sine of a string node), just an ordinary pluck pitched up.

## Root cause

The flageolet is a **FREQUENCY-ONLY retune**: `crates/ferrosintesis/src/voices.rs:3901`
(`let harm = if p.harmonic { 2.0 } else { 3.0 }`) multiplies the Karplus-Strong loop to
2f/3f, but the excitation stays the standard broadband filtered-noise pluck burst
(`voices.rs:~3934`) and the `HARMONIC` preset (`voices.rs:2985`) sets no spectral thinning.
A real touched harmonic damps the fundamental and nearly all partials, leaving a near-sine
at the node — that thinning is absent, so it renders as a normal pluck an octave/twelfth up.

## Fix direction

Thin the flageolet excitation toward a near-sine (drop the fundamental + most partials, or
narrow the excitation band) rather than only retuning the loop. Level trim is moot until
the timbre is fixed (the retune shifts level/decay anyway). Related: scratchpad.md:192-193
documents the 2f/3f mapping but not this timbre defect; MM-BUG-KILN-00006 (no timbre oracle).
