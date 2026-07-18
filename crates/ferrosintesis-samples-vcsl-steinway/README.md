# ferrosintesis-samples-vcsl-steinway

Embedded **CC0** VCSL "Grand Piano, Steinway B" attack/body samples — a warm,
intimate vintage Steinway that voices a **GM 0 Acoustic Grand alternate** (CC0
bank 1) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis). A tonal
contrast to the default bright Salamander C5 grand.

9 pitch zones (C2–C6) × 3 dynamics (pp/mf/f) × 2 round robins = 54 mono 16-bit
44.1 kHz WAVs, embedded via `include_bytes!`. Consumers normally reach this crate
through `ferrosintesis`. Provenance and processing: see `PROVENANCE.md`. Licence:
CC0 1.0 (public domain); `NOTICE` carries a courtesy credit to VCSL / Sam Gossner.

Regenerate the WAVs with `python tools/ferrosintesis-samples/prepare.py --only=steinwayb`.
