# MM-REQ-KILN-00021 — GM 84 (Lead 5, charang) must have its distortion character

- **State:** Draft
- **Priority:** Could
- **Area:** voices / synth leads
- **Raised:** 2026-07-20
- **Implemented-by:** —
- **Satisfied-by:** —
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
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5)

## Statement

GM program 84 ("Lead 5 (charang)") must carry the driven/distorted edge that
defines the charang patch, not render as another clean saw variant.

## Notes

- "Lost" requirement: bespoke per-program DSP for leads 84–87 was deferred "to
  reqs" in a `voices.rs` comment near the LeadSpec table; no req was ever filed.
- The repo already owns a Drive insert (guitar v2, used by GM 29/30) that could
  supply the nonlinearity — plumbing, not new DSP.
- Oracle sketch: harmonic-distortion ratio (odd-harmonic energy above the saw
  baseline) on GM 84 vs GM 80/81.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate": defining
  character unimplemented).
