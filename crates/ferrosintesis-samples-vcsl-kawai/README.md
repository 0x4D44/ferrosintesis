# ferrosintesis-samples-vcsl-kawai

Embedded **CC0** VCSL "Grand Piano, Kawai" attack/body samples — a darker, rounder
vintage grand that voices a **GM 0 Acoustic Grand alternate** (CC0 bank 2) in
[ferrosintesis](https://github.com/0x4D44/ferrosintesis).

8 pitch zones (C2–C6) × 3 dynamics (pp/mf/f) × 2 round robins = 48 mono 16-bit
44.1 kHz WAVs, embedded via `include_bytes!`. Consumers normally reach this crate
through `ferrosintesis`. Provenance and processing (including the VCSL octave-label
trap) are in `PROVENANCE.md`. Licence: CC0 1.0 (public domain); `NOTICE` carries a
courtesy credit to VCSL / Sam Gossner.

Regenerate the WAVs with `python tools/ferrosintesis-samples/prepare.py --only=kawai`.
