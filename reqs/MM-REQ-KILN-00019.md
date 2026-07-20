# MM-REQ-KILN-00019 — GM 86 (Lead 7, fifths) must render its parallel fifth

- **State:** Implemented
- **Priority:** Should
- **Area:** voices / synth leads
- **Raised:** 2026-07-20
- **Implemented-by:** task/20260720-DEV-HUM-gm86-fifth-gm87-sub-octave @ 7255802 (crates/ferrosintesis/src/voices.rs — LeadSpec.interval + SawStack::push_interval_layer)
- **Satisfied-by:** voices::tests::lead_fifths_sounds_the_parallel_fifth, voices::tests::lead_bass_lead_carries_the_sub_octave, voices::tests::lead_interval_tracks_legato_retune
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
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Implemented (2026-07-20, held branch, oracles red→green; render-diff 2 expected/0 contamination)

## Statement

GM program 86 ("Lead 7 (fifths)") must sound the interval its GM name promises: a
parallel-fifth layer (+7 semitones) over the root, audibly present on a plain held
note. Today it is a plain 2-oscillator saw whose spec differs from GM 81 only by
oscillator count (identical detune 0.006 / cutoff 3000 / q 1.1).

## Notes

- This is a "lost" requirement: the LeadSpec table defers it in a comment — "86
  fifths* — plain saw this pass (parallel fifth deferred)"
  (`crates/ferrosintesis/src/voices.rs`, grep "fifths\*") — with a "deferred to
  reqs" note that never produced a req.
- SawStack already runs N independent detuned layers with per-layer pitch, so a
  fixed +7-semitone layer is the natural mechanism; keep the CC1/CC68 lead
  behaviour intact.
- Oracle sketch: spectral presence of 1.5×f0 (and its harmonics) on a held GM 86
  note, absent on GM 81; plus the anti-clone matrix margin for (81,86) widening.
- Surfaced by the 2026-07-20 GM instrument sweep (15-agent audit); one of only two
  programs rated "weak" across the whole melodic map (the other is GM 87).
