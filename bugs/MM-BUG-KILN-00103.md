# MM-BUG-KILN-00103 — GM0 alternate pianos inherit a 0.10 s damper release because one Option argument conflates sample calibration with damper physics

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / piano voicing
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high)

## Observation

Arthur reported the B1 upright (GM0 CC0=5) sounding "a little quiet" on the
Tubular Bells reference render. It is quieter, and the cause is not gain.
`voices::acoustic_grand_with_bank` took a single `release_t60: Option<f32>`
that silently switched FIVE unrelated things at once:
  Some (GM0 default)        None (every alternate, GM1)
  model release  0.45 s     0.10 s  (DEFAULT_PIANO_RELEASE_T60)
  sample release 0.45 s     0.06 s  (DEFAULT_LA_RELEASE_T60)
  sample gain    4.00       0.90    (LA_PIANO)
  sample fade    0.18-0.45  0.18-0.85
  forte trim     yes        no
So selecting a different RECORDING also cut the damper release by 4.5x. A
microphone cannot change damper physics; the coupling is the defect.
Measured at the voice level (no normalization, no BusGlue), B1 vs default GM0:
release tail -5.6 dB at vel 40-70, sustain -2 to -4 dB. B1 is +1.8..+2.2 dB
LOUDER at vel 100-120, but Tubular Bells' piano peaks at velocity 77 and never
reaches that band, so the piece sits entirely in the deficit.
Consistency check: the tail gap is 5.6 dB at vel 40-70 but only 0.7 dB at
vel>=96, because there the default takes GM0_FORTE_LAYER_GAIN (-4.9 dB).
5.6 - 4.9 = 0.7, matching the measurement.
Affects all five GM0 alternates (Salamander, Steinway B, Headroom,
dark-Salamander, B1), not just B1. No committed album is affected: a temporal
scan of all 141 album/demo MIDIs found zero notes played on a GM0 alternate,
confirmed by a byte-identical render-diff.

## Fix

<unfixed — raised only>

## Notes
