# MM-REQ-KILN-00034 — The guitar note-off thump should be driven by the recorded body knocks, not modelled

- **State:** Draft
- **Priority:** Could
- **Area:** ferrosintesis / guitar voice (LA sample layer)
- **Raised:** 2026-07-25
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-25, promoted from `scratchpad.md` by the scratchpad-review pass; parked 2026.07.24 when the GM120 fret-noise change was deliberately kept focused)

## Statement

The guitar's note-off `stop_thump` should be voiced from the owner-recorded
soundboard/side knocks captured in the GM120 fret-noise session, rather than from a
synthetic burst, so that damping a string sounds like a hand on a real instrument.

## Notes

Eight clean body-knock (tap) takes were recorded alongside the fret-slide bank —
soundboard and side knocks in `samples/fret-noise-eastman-e1d/DR0000_0204.opus`
(taps at roughly 26 / 56 / 60 / 61 s, and more). They were deliberately parked:
Arthur's steer was to keep the fret-noise change focused, and the bank's own
`README.md` records the reservation — "the taps are reserved for a future note-off
`stop_thump` job, not this bank". `cuts/` holds only the twelve `fret_rr01..12.wav`
slide cuts; no tap has been cut yet.

The material is owner-recorded and CC0, so there is no licensing question — this is
the same provenance as the shipped fret-noise bank.

`stop_thump` today is fully modelled: `voices.rs` declares the field and builds it
as a synthetic `Burst` through a 250 Hz lowpass with a 0.12 s decay. No sample layer
touches that path.

Two reasons this is `heavy` and not a quick job:

- It is a multi-step build — cut the taps, extend or add an asset crate, bake,
  wire the voice, add oracles — and a new sample crate needs its own
  `!crates/<crate>/samples/*.wav` gitignore line or it commits without its samples
  and fails from a clean checkout.
- The thump level is an ear call (existing presets span 0.3–2.2), and this is a
  default-on timbre change under the repo's synth-change policy, so it needs the
  full render-diff inventory across every guitar-bearing album plus Arthur's
  audition.
