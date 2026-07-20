# MM-REQ-KILN-00022 — GM 85 (Lead 6, voice) must have a vocal formant character

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

GM program 85 ("Lead 6 (voice)") must shape its spectrum with vocal formants so it
reads as a voice-like lead, not another filtered saw.

## Notes

- "Lost" requirement: deferred "to reqs" in the `voices.rs` LeadSpec comment
  block; never filed.
- The machinery exists in-repo: `StackFilter::Formant` (the vowel formant bank) is
  already the default on choir-pad 91 and answers CC70 elsewhere — routing it
  under a lead envelope is the work.
- Oracle sketch: formant-peak presence (e.g. energy concentration near the bank's
  F1/F2) on GM 85 vs the plain-saw leads.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate": defining
  character unimplemented).
