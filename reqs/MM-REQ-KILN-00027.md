# MM-REQ-KILN-00027 — Steel-guitar LA layer must hold seam level parity at high keys

- **State:** Implemented
- **Priority:** Should
- **Area:** sampler / LA layer
- **Raised:** 2026-07-20
- **Implemented-by:** integrated 6de727e (parity oracle + calibration printer); the underlying fix landed earlier via the pluck-redesign Phase-2 STEEL seam re-baselines + the k=2 velocity law (93fdf53, 0.21.50)
- **Satisfied-by:** sampler::tests::la_steel_high_key_level_parity (0.8–2.2 band, keys 76/79/83 × vel 60/100)
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
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Implemented (2026-07-21, integrated 6de727e — measured healthy, oracle pinned)

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

### Outcome note (2026-07-21)

Measured BEFORE building: the ~12 dB excess this req cites **no longer
exists** — wrapped/model early-RMS at keys 76–90 reads 1.03–1.96 (printer
`print_steel_wrap_level_ratios`), inside nylon's healthy neighbourhood. The
intervening Phase-2 STEEL seam work + k=2 velocity law fixed it. No taper was
added (nothing to fix); the new oracle pins the 0.8–2.2 band so the parity
cannot silently regress. Shoulder note: keys 72–74 at vel 60 read ~2.2 —
outside the oracle's key set (req scope ≥76) but worth knowing if the band is
ever tightened.
