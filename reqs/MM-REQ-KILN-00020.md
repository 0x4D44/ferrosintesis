# MM-REQ-KILN-00020 — GM 87 (Lead 8, bass+lead) must carry its sub-octave bass layer

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

GM program 87 ("Lead 8 (bass + lead)") must layer the bass its GM name promises: a
sub-octave (−12 semitone) component under the lead voice, audible on a plain held
note. Today it is a darker 2-oscillator saw with no sub layer.

## Notes

- "Lost" requirement: the LeadSpec table defers it — "87 bass+lead* — darker saw
  this pass (sub octave deferred)" (`crates/ferrosintesis/src/voices.rs`, grep
  "bass\+lead") — with a "deferred to reqs" note that never produced a req.
- (83,87) is the tightest anti-clone margin in the synth-lead family (0.1071 vs
  BAR_FULL 0.075 per `testutil.rs`); the sub layer would widen it for free.
- The envelope-locked sub-oscillator pattern already exists in the Pluck basses
  (GM 32–39) — reuse the idea, not necessarily the code.
- Oracle sketch: f0/2 energy present and envelope-locked on GM 87, absent on
  GM 80–86; (83,87) margin widens.
- Surfaced by the 2026-07-20 GM instrument sweep; one of the two "weak"-rated
  melodic programs.
