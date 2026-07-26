# MM-BUG-KILN-00133 — Held GM0 treble notes rebound ~3-4 dB through the engine with the LA sample layer

- **State:** Fixed
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T103423Z-p51164-n194166100-c1 branch=task/bug-MM-BUG-KILN-00133-run-fix-20260726T103423Z-p51164-n194166100-c1 code=59ed31676b5e1116b6193c8d7433284928a9356e gate=manual) -> Open (2026-07-26, REOPENED (not closed) by Claude Opus 5 @ high, fresh context, during independent two-eyes verification - I raised this bug and did not fix it (fixer: deltic:auto role=fix). The repo gate is green and the fix is a real partial improvement with a correct diagnosis, but THE REPORTED SYMPTOM STILL OCCURS ON THE SHIPPED BUILD, at magnitudes larger than the report. Measured by me on a release binary rebuilt from a verified-clean tree at d5b40fe (`git status --porcelain` empty, the model-seed substitution present at `voices.rs:12769`), using this bug's own method - held GM0 note, `--wet 0`, 50 ms RMS windows, max rebound after the 150 ms attack budget: at velocity 100 keys 85/86/87 rebound **+4.96 / +5.01 / +5.13 dB** and key 96 rebounds +2.82 dB, against the +4.00 dB at key 72 that this bug was filed for; at velocity 50 keys 67/68/69/70 rebound **+7.18 / +7.99 / +7.72 / +7.90 dB**. The three keys the new oracle covers (72/78/84) measure +0.25 / -0.74 / +0.39 dB, i.e. clean. That is persistence of the reported defect rather than a residual, so this keeps its own id per the ledger's reopen rule. WHY THE GUARDS DO NOT SEE IT: the fix pins the model to `B1_MODEL_PHASE_SEED = 5`, and 5 is the seed the pre-existing voice-level oracle already hardcoded (`assert_wrap_seam_seed(..., 5)`, `sampler.rs:7967`) and the seed the new engine test inherits, so production and both oracles now share one draw of the same lottery; the three engine-test keys are keys that this particular draw happens to satisfy. The fix therefore FREEZES one draw rather than removing the cancellation. WHAT THE FIX DID GET RIGHT, and should be kept: its diagnosis supersedes this report's own guess - the mechanism is phase cancellation between a fixed recording and a randomly-phased model, not the sympathetic resonance I hypothesised; the engine-level test is at the right layer and is non-vacuous (reverting the seed substitution turns it red); and it repaired a genuine velocity-law defect, since pre-fix renders had velocity 104 louder than 112. NEW EVIDENCE FOR WHOEVER PICKS THIS UP, from a four-lens adversarial review whose findings I reproduced myself: (1) the residual is a per-key phase lottery - one global seed cannot phase-align the ~26 pitch-shifted zones across 88 keys, so a scalar seed pin cannot close it and the real fix has to make the seam phase-ROBUST (e.g. equal-power or envelope-follower handoff) rather than phase-matched; (2) the fix also removed all per-note variation from the DEFAULT piano - repeated identical GM0 notes are now bit-identical (lag-aligned NCC 1.000000, residual at the -80 dB dither floor; pre-fix 0.498-0.881), velocity does not break the lock (NCC 0.99996+ across a 20-unit velocity span), and the repo's own anti-machine-gun bar (`guitar_onset_variation_presence_and_determinism`, ncc < 0.99) is exactly the bar GM0 now fails, though it loops only programs 24/25; 5,938 of 65,479 GM0 note-ons across 80 of 124 committed album MIDIs are exact same-key/same-velocity repeats within 2 s. Audibility of that cloning was measured, not listened to. (3) The class is wider than GM0-default: with the random model phase still in place, GM8 celesta rebounds +11.3 dB and GM1 Bright Acoustic Grand - the default bright piano - rebounds up to +10.5 dB across seeds, and `la_level_continuity` is pinned to one seed for every program, so it cannot see any of it. Those are other programs and are deliberately NOT filed as separate ids by this verify-only pass; they are recorded here because they show a bank-scoped seed pin is the wrong shape for the fix.) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T122154Z-p47536-n024106500-c1 branch=task/bug-MM-BUG-KILN-00133-run-fix-20260726T122154Z-p47536-n024106500-c1 code=cf7622355c266df5c4d88984c82d11094881d327 gate=manual)

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


## Reopen note - 2026-07-26 (independent two-eyes verification)

The `59ed316` fix is a real partial improvement built on a correct diagnosis, but it does not
resolve this bug. Reopened rather than closed because the reported symptom still reproduces on
the shipped build, larger than reported.

### Measured on the shipped build

Release binary rebuilt from a verified-clean tree at `d5b40fe`. Held GM0 note, `--wet 0`,
50 ms RMS windows, max rebound after the 150 ms attack budget - this bug's own method.
Bar is the fix's own 1.5 dB.

| velocity | key | rebound | |
|---|---|---|---|
| 100 | 72, 78, 84 | +0.25, -0.74, +0.39 dB | the three keys the new oracle covers |
| 100 | 85, 86, 87 | **+4.96, +5.01, +5.13 dB** | worse than the +4.00 dB this bug was filed for |
| 100 | 96 | +2.82 dB | |
| 50 | 67, 68, 69, 70 | **+7.18, +7.99, +7.72, +7.90 dB** | soft sample layer, below the vel-60 split |

### Why both oracles stay green

`B1_MODEL_PHASE_SEED = 5` is the same seed the pre-existing voice-level oracle already hardcoded
(`assert_wrap_seam_seed(..., 5)`, `crates/ferrosintesis/src/sampler.rs:7967`), and the new engine
test inherits it. Production and both guards therefore share ONE draw of the cancellation lottery,
and the engine test's three keys are keys that this draw happens to satisfy. The fix freezes a
draw; it does not remove the cancellation.

### Keep from this attempt

- The diagnosis is right and supersedes this report's own guess: the mechanism is phase
  cancellation between a fixed recording and a randomly-phased model, not sympathetic resonance.
- `sampled_gm0_treble_does_not_rebound_through_the_engine` is at the correct layer and is
  non-vacuous - reverting the seed substitution turns it red.
- It repaired a genuine velocity-law defect: pre-fix, velocity 104 rendered louder than 112.

### What the next attempt needs

1. **Phase-robust, not phase-matched.** One global seed cannot phase-align ~26 pitch-shifted zones
   across 88 keys, so no scalar seed choice closes this. Prefer a handoff whose sum does not depend
   on the phase relationship - equal-power, or an envelope-follower crossfade.
2. **Restore per-note variation.** The fix made repeated identical GM0 notes bit-identical
   (lag-aligned NCC 1.000000, residual at the -80 dB dither floor; pre-fix 0.498-0.881), and a
   20-unit velocity span does not break the lock (NCC 0.99996+). GM0 is the default piano:
   5,938 of 65,479 GM0 note-ons across 80 of 124 committed album MIDIs are exact
   same-key/same-velocity repeats within 2 s. Any variation reintroduced must not re-open the
   cancellation, which is why (1) comes first. Audibility was measured, not listened to.
3. **Oracles that can fail.** Both current guards are seed-pinned to production's seed. A guard for
   this needs to sweep keys and velocities (85-87 and the vel<60 band are the live failures), and
   ideally seeds. The repo's own anti-machine-gun bar
   (`guitar_onset_variation_presence_and_determinism`, `ncc < 0.99`) is the right instrument for
   point 2 but currently loops only programs 24/25.
4. **The class is wider than the GM0 default.** With the random model phase still in place, GM8
   celesta rebounds +11.3 dB and GM1 Bright Acoustic Grand - the default bright piano - rebounds up
   to +10.5 dB across seeds, and `la_level_continuity` is seed-pinned for every program so it cannot
   see any of it. Not filed as separate ids by this verify-only pass; recorded here because it shows
   a bank-scoped seed pin is the wrong shape.
