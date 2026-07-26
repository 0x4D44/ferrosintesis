# MM-BUG-KILN-00133 — Held GM0 treble notes rebound ~3-4 dB through the engine with the LA sample layer

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synthesis / engine
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** Through the ENGINE, a held GM0 treble note still falls into a trough and swells back, even though the voice-level crossfade that MM-BUG-KILN-00130 fixed is now flat. The effect needs the LA sample layer: it disappears under `--no-samples`.

**Measured on this tree** (fix `248de62` present), release CLI, `--wet 0` to remove reverb, one held note per render so the -18 LUFS normalization cancels, 50 ms RMS windows, max rebound after the 150 ms attack budget - the same statistic `b1_upright_handoff_does_not_rebound` uses:

```
 key   sampled   model-only   delta
  36    +0.28      +0.17      +0.11
  48    -0.34      -0.38      +0.04
  60    -0.31      -0.75      +0.45
  66    +0.31      -0.65      +0.95
  72    +4.00      -0.34      +4.34
  78    +3.04      -0.11      +3.15
  84    +2.88      -0.03      +2.91
```

Bass and mid are clean. From about key 72 up, the sampled render rebounds 2.9-4.0 dB while the model-only render of the same note stays monotone within 0.4 dB. At key 72 the trough sits at 250 ms and the recovery peaks at 350 ms.

**Why this is not MM-BUG-KILN-00130.** That bug is scoped to the voice-level crossfade and its recorded repro is `voices::make(0, key, 100, 44100.0, 5, true)`. On this tree that path is fixed: forcing `b1_upright_handoff_does_not_rebound` to print its measurement shows key 72 rebounding **0.14 dB** at voice level, against the ~9 dB the bug recorded and a 1.5 dB bar. Its title and its CLI claim are both about BASS notes, and key 36 end-to-end is now +0.28 dB. So the fix did its job; this is a different layer (engine, not voice) in a different register (treble).

**Suspected mechanism, NOT confirmed.** `EngineCore` builds `Sympathetic::piano(sr)` unconditionally at `crates/ferrosintesis/src/engine.rs:2138` - unlike the guitar and sitar resonators there is no `piano_symp_on` knob to switch it off, so I could not isolate it by toggling. A resonator excited by the sample layer's brighter onset would build over ~100 ms and could produce exactly this shape, and the `--no-samples` contrast is consistent with that. It is a hypothesis from the measurements plus a read of the construction site; I did not instrument the resonator, and the channel strip and bus glue were not ruled out.

**Expected.** A held piano note decays monotonically from the hammer at every key, through the engine as well as at voice level.

**Actual.** Keys from about 72 up rebound 2.9-4.0 dB through the engine.

**Reproduce.**
```
ferrosintesis <held-GM0-key-72.mid> --wet 0 -o a.wav
ferrosintesis <held-GM0-key-72.mid> --wet 0 --no-samples -o b.wav
```
then compare 50 ms RMS windows over the first 700 ms. The rebound is present in `a.wav` and absent in `b.wav`.

**Provenance.** Split out of MM-BUG-KILN-00130 during its independent two-eyes verification. Filed rather than folded into that bug because the fixed layer and the affected layer differ, and because 00130's oracle measures the voice and therefore cannot see this.

**Fix direction.** First confirm the mechanism - the cheapest step is a temporary `piano_symp_on` switch (or a direct probe of the resonator's contribution) to establish whether the sympathetic path is responsible. If it is, the question is whether the resonator is being driven too hard by the sampled onset's spectrum in the treble. Whatever the cause, the regression belongs at the ENGINE level, since `b1_upright_handoff_does_not_rebound` is voice-level by construction and stays green throughout.

## Fix

<unfixed — raised only>

## Notes
