# MM-REQ-KILN-00026 — LoopVoice must carry a slow read-rate drift against the loop-tell

- **State:** Satisfied
- **Priority:** Could
- **Area:** sampler
- **Raised:** 2026-07-20
- **Implemented-by:** integrated 32eb8aa (LoopVoice drift fields + render walk; drones seeded 0x0D20_0E01/02)
- **Satisfied-by:** sampler::tests::bagpipe_chanter_rr2_and_drift_decorrelate (drift clause), voices::tests::bp_o1_bagpipe_chanter_is_constant_amplitude_saxes_keep_dynamics (amplitude unchanged)
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Implemented (2026-07-21, integrated 32eb8aa) → Satisfied (2026-07-25, verified)

## Statement

`LoopVoice` sustains (GM 109 bagpipe chanter/drones) must not present a static
periodic loop-tell: add the SaxLoopVoice-style slow read-rate random walk
(±0.22 %, `SAX_DRIFT_MAX` idiom) — the drift ONLY, no amplitude animation.

## Notes

- Tracked in scratchpad (2026-07-20): now that bagpipe loops are ~65 ms they
  repeat ~15×/s; `SaxLoopVoice` runs the drift explicitly commented "defeats the
  loop-tell" while `LoopVoice` has none
  (`crates/ferrosintesis/src/sampler.rs`, grep `SAX_DRIFT_MAX` /
  `LoopVoice::render`).
- Do NOT add the sax tremolo:
  `bp_o1_bagpipe_chanter_is_constant_amplitude_saxes_keep_dynamics` pins constant
  amplitude, and constant bag pressure is the instrument.
- Oracle sketch: instantaneous read-rate variance > 0 over a long held chanter
  note while the amplitude-constancy oracle stays green.
