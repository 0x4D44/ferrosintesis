# ferrosintesis-samples-headroom

Embedded **CC BY 4.0** Headroom/Intimate Piano (Bengt Nilsson, a Yamaha C3 grand)
attack/body samples — a warm, intimate close-mic grand that voices a **GM 0
Acoustic Grand alternate** (bank select CC0=4) in
[ferrosintesis](https://github.com/0x4D44/ferrosintesis).

9 pitch zones (C2–C6) × 3 dynamics (pp/mf/f) × 2 round robins = 54 mono 16-bit
44.1 kHz WAVs, embedded via `include_bytes!`. Consumers normally reach this crate
through `ferrosintesis`. Provenance and processing: see `PROVENANCE.md`.

**Licence: CC BY 4.0 — attribution is required.** `NOTICE` credits Bengt Nilsson
and retains the instrument name, as the licence and the author's terms require.

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=headroom`
(needs `ffmpeg` on PATH for the FLAC decode).
