# ferrosintesis-samples-musescore-grand

Embedded **MIT** MuseScore_General "Grand Piano" samples (MF velocity tier) — a
warm-to-neutral GM grand that voices a **GM 0 Acoustic Grand alternate** (CC0
bank 4) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

A **dense single-velocity multisample** (one sample per distinct sampled pitch,
C2–C6+) of mono 16-bit 44.1 kHz WAVs, embedded via `include_bytes!`. Dynamics come
from the LA blend + model, not the sample layer (see `PROVENANCE.md`).

**Licence: MIT.** `NOTICE` retains the S. Christian Collins / FluidR3 copyright and
acknowledgement notices.

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=musescoregrand`
(needs `ffmpeg` on PATH for the Ogg decode).
