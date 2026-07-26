# MM-BUG-KILN-00037 — GM31 guitar harmonics is a frequency-only retune: renders as a plain pluck, not a flageolet

- **State:** Fixed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL instrument-audition review; "sounds just like plucking" — Arthur's ear, code-confirmed) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — node-filtered excitation leaves GM31's retuned loop with a spectrally thin flageolet ring)

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

## Fix

The existing random pluck burst now supplies only the phase for GM31's loop
seed. `flageolet_excitation()` projects that displacement onto one cycle of the
sounding 2f/3f harmonic and removes float-residue DC. The existing separate
touch click remains, so the onset still articulates while the circulating
string rings near-sinusoidally. All non-GM31 presets retain their exact legacy
or Shaped excitation path and random draw sequence.

## Verification

- The fail-first end-to-end oracle measured the old GM31 ring's h2–h8 energy
  20.6 dB above its sounding harmonic at key 52.
- The corrected h2–h8/h1 ratios are -30.6 dB at key 52 (2f side) and -35.6 dB
  at key 64 (3f side). The sounding harmonic carries 0.891 and 0.584 of total
  ring energy respectively, and the explicit non-silence clauses pass.
- The existing fundamental-suppression, sounding-pitch, and bent-pitch clauses
  pass unchanged.
- The complete default suite passed (726 tests, 27 ignored), the complete
  model-only suite passed (625 tests, 22 ignored), and both doc-test sets passed
  (4 tests each).
- Strict workspace clippy passed with default and no-default features;
  formatting and `git diff --check` passed.
- The exact-base 124-MIDI render inventory at 11.025 kHz found no catalog piece
  that sounds GM31: all 124 stayed byte-identical, with zero contamination and
  zero missed paths.

Related: `scratchpad.md:192-193` documents the 2f/3f mapping; MM-BUG-KILN-00006
tracks the wider timbre-oracle problem.
