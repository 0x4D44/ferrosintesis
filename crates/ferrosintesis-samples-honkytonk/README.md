# ferrosintesis-samples-honkytonk

Embedded **CC0** FreePats honky-tonk player-piano samples with a detuned,
jangly, saloon/tack attack. Voices the **GM 3 Honky-tonk Piano default** (no CC0 select needed)
in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

9 pitch zones (C2–C6) × single velocity = mono 16-bit 44.1 kHz FLACs, embedded via
`include_bytes!` and returned as raw FLAC bytes by `get`. Character, not fidelity
(a handheld player-piano capture — see `PROVENANCE.md`).

The exact case-sensitive lookup keys are `honkytonk_C2.flac`, `honkytonk_F2.flac`,
`honkytonk_C3.flac`, `honkytonk_F#3.flac`, `honkytonk_C4.flac`, `honkytonk_F4.flac`,
`honkytonk_C5.flac`, `honkytonk_F#5.flac`, and `honkytonk_C6.flac`.

**Licence: CC0 1.0** (public domain); `NOTICE` carries a courtesy credit to the
FreePats project / Piotr Barcz.

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=honkytonk`
(needs `7z` and `ffmpeg` on PATH).
