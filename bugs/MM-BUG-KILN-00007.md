# MM-BUG-KILN-00007 — Sample playback (LA layer, drums, gong) pitch-shifts with 2-point linear interpolation: up-pitch aliasing and treble loss

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

The LA sample layer is the synth's realism showpiece, yet its resampler is the
crudest interpolator in the codebase. `LoopVoice::render`
(`crates/ferrosintesis/src/sampler.rs:~1350`, `a + (b - a) * frac`), the
sampled-drum reader (`sampler.rs:~2002`) and the gong reader (`sampler.rs:~2120`)
all use 2-point linear interpolation, at repitch ratios up to 2.0
(`sampler.rs:~1329`).

Linear interpolation at step > 1 (pitching up) both attenuates HF and folds
interpolation images back as aliasing — exactly on the sampled brass/strings/
piano zones that are stretched upward. The proven cubic-Lagrange tap
(`dsp.rs:344`, `DelayLine::tap_cubic`, verified by `cubic_tap_retains_treble_ring`
at `dsp.rs:727`) is deliberately confined to the Karplus-Strong loop by an
explicit "buses keep the linear tap" decision (`dsp.rs:~337`).

## Fix

Replace the linear read in `LoopVoice`/sampled-drum/gong with a 4-point
cubic-Lagrange (or Hermite) resampler — the math already exists in `tap_cubic`,
so this is reuse, not new DSP. It is the single change that lifts *every* sampled
instrument at once. Optionally add a short anti-imaging lowpass (or oversample)
on samples pitched above unison, since even cubic leaves some image when pitching
up.

## Notes

- Touches the sampled render path → gate behind the full render-diff inventory
  (CLAUDE.md); this is a default-on timbre improvement, so expected diffs are on
  every album that uses a sampled program.
- The DSP audit rated this "the single biggest audible upgrade to the sampled
  instruments."
