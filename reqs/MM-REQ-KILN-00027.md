# MM-REQ-KILN-00027 — Steel-guitar LA layer must hold seam level parity at high keys

- **State:** Draft
- **Priority:** Should
- **Area:** sampler / LA layer
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

The GM 25 steel-string LA wrap must taper its wrap gain per key so the
sample-to-model seam holds level parity across the whole range: at keys ≥ 76 the
sample currently speaks ~12 dB over the now-ringing model at the seam, at every
velocity.

## Notes

- Tracked in scratchpad (~2026-07-18 entry, "steel high-key LA wrap-gain level
  parity"): the measured excess is on the family's flagship bank.
- Precedent in the same wrap: `GUITAR_VEL_LEVEL_EXP` is the velocity-law analogue;
  this is the per-key one. Calibrate against the model's actual high-key output,
  don't hand-tune.
- Oracle: extend `la_level_continuity` (the `assert_wrap_seam` contract in
  `crates/ferrosintesis/src/sampler.rs`) with steel rows at high keys — currently
  the guitar rows don't cover the ≥76 region.
- Render-diff expected on steel-heavy albums; timbre-neutral level change at the
  seam only.
