# MM-REQ-KILN-00024 — GM 106 shamisen must carry a sawari bridge-buzz

- **State:** Implemented
- **Priority:** Should
- **Area:** voices / ethnic plucks
- **Raised:** 2026-07-20
- **Implemented-by:** integrated 495f85d (branch task/20260720-DEV-HUM-shamisen-sawari-jawari @ ad994e0; crates/ferrosintesis/src/voices.rs SHAMISEN jawari)
- **Satisfied-by:** voices::tests::shamisen_sawari_buzzes_gentler_than_sitar
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
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Implemented (2026-07-21, integrated 495f85d; oracle red→green, render-diff 124 same/0 contamination)

## Statement

GM program 106 (shamisen) must author a sawari — the buzzing bridge contact that
is the instrument's defining identity cue — on its Pluck preset, the way the sitar
already authors its jawari.

## Notes

- The machinery exists and is preset-authored: `JawariSpec` on the Pluck preset
  (grep `JawariSpec` in `crates/ferrosintesis/src/voices.rs`) with the in-loop
  bridge-contact hook; today only SITAR authors it. This is preset data + tuning,
  not new DSP.
- Builds on MM-REQ-KILN-00007 (Implemented — shamisen got its own plucked voice);
  this adds the missing identity cue on top.
- Oracle patterns to mirror: `sitar_jawari_buzz_survives_decay` /
  `sitar_jawari_*_stability`.
- Sawari is gentler and darker than sitar jawari — tune, don't copy, the sitar
  amounts.
- Surfaced by the 2026-07-20 GM instrument sweep (highest-value small item in the
  ethnic family).
