# ferrosintesis-samples-musescore-grand

Embedded **MIT** MuseScore_General "Grand Piano" samples (MF velocity tier) — a
warm-to-neutral GM grand that voices the **GM 1 Bright Acoustic Piano
alternate** (CC0=2) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

A **dense single-velocity multisample** (one sample per distinct sampled pitch,
C2–C6+) of mono 16-bit 44.1 kHz FLACs, embedded via `include_bytes!` and returned
as raw FLAC bytes by `get`. Dynamics come from the LA blend + model, not the sample
layer (see `PROVENANCE.md`).

The exact case-sensitive lookup keys are `musescoregrand_A2.flac`,
`musescoregrand_A3.flac`, `musescoregrand_A4.flac`, `musescoregrand_B1.flac`,
`musescoregrand_B2.flac`, `musescoregrand_B3.flac`, `musescoregrand_B4.flac`,
`musescoregrand_B5.flac`, `musescoregrand_C#6.flac`, `musescoregrand_C3.flac`,
`musescoregrand_C4.flac`, `musescoregrand_C5.flac`, `musescoregrand_D#6.flac`,
`musescoregrand_D2.flac`, `musescoregrand_D3.flac`, `musescoregrand_D4.flac`,
`musescoregrand_E2.flac`, `musescoregrand_E3.flac`, `musescoregrand_E4.flac`,
`musescoregrand_E5.flac`, `musescoregrand_G#5.flac`, `musescoregrand_G2.flac`,
`musescoregrand_G3.flac`, `musescoregrand_G4.flac`, and `musescoregrand_G5.flac`.

**Licence: MIT.** `NOTICE` retains the S. Christian Collins / FluidR3 copyright and
acknowledgement notices.

The complete scoped regeneration workflow is
`python3 tools/ferrosintesis-samples/prepare.py --only=musescoregrand`; it rebuilds
this bank and publishes verified FLAC outputs (needs `ffmpeg` on PATH for the Ogg
decode and FLAC publication).
