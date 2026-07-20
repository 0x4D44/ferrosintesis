# MM-REQ-KILN-00023 — GM 93 (Pad 6, metallic) must be inharmonic

- **State:** Draft
- **Priority:** Could
- **Area:** voices / synth pads
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

GM program 93 ("Pad 6 (metallic)") must carry genuinely inharmonic partials — a
metallic clang, not the harmonic stack it renders today.

## Notes

- "Lost" requirement: the code and the Stage-2 journal both flag the
  harmonic-clang limit and promise "a separate req" (grep "metallic" in
  `crates/ferrosintesis/src/voices.rs`); the req was never filed.
- The Modal partial-bank machinery (bells, tubular bells' hand-tuned ≈2:3:4.2
  ratios) shows how to put an inharmonic table under a pad-shaped envelope.
- Oracle sketch: partial-frequency ratios deviate from integer multiples by a
  floor (inharmonicity measure), on GM 93 only within 88–95.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate").
