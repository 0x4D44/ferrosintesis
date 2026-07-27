# ferrosintesis-samples-honkytonk

Embedded **CC0** FreePats honky-tonk player-piano samples — the **distinctive**
option: a detuned, jangly, saloon/tack attack no properly-tuned grand or upright
can make. Voices the **GM 3 Honky-tonk Piano default** (no CC0 select needed)
in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

9 pitch zones (C2–C6) × single velocity = mono 16-bit 44.1 kHz WAVs, embedded via
`include_bytes!`. Character, not fidelity (a handheld player-piano capture — see
`PROVENANCE.md`).

**Licence: CC0 1.0** (public domain); `NOTICE` carries a courtesy credit to the
FreePats project / Piotr Barcz.

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=honkytonk`
(needs `7z` and `ffmpeg` on PATH).
