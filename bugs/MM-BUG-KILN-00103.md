# MM-BUG-KILN-00103 — GM0 alternate pianos inherit a 0.10 s damper release because one Option argument conflates sample calibration with damper physics

- **State:** Closed
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high) → Fixed (2026-07-25, Claude Opus 5; `f6ed468` separated sample calibration from damper physics, followed by the felt-damper model in `70b7067`) → Closed (2026-07-25, Codex GPT-5.6-Sol; independently inspected all five GM0 alternate mappings and reran the release and damper-wiring regressions on native Rust and 1.87)

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

Commit `f6ed468` replaced the overloaded release `Option` with two independent
axes: `PianoSampleCal` controls only layer gain and crossfade, while
`PianoDamper` controls model and sampled-layer release. Every GM0 alternate now
uses `GM0_ALTERNATE_VOICING`, pairing its legacy-normalized recording calibration
with the GM0 damper. Commit `70b7067` subsequently replaced the flat release with
the shared register-aware felt-damper model.

Independent closure verification confirmed that all five GM0 alternate source
mappings pass through the same voicing selection, while GM1 uses its own explicit
voicing. `gm0_damper_reaches_gm0_alternates_and_stops_there` matches the routed
alternate against an independently constructed control to 0.01 dB.
`felt_damper_curve_is_anchored_monotonic_and_bounded` and
`felt_damper_is_wired_to_every_shared_piano_slot` also pass. The release-control
test passes on both the native toolchain and Rust 1.87.

## Notes
