# ferrosintesis-samples-vcsl-kawai

Embedded **CC0** VCSL "Grand Piano, Kawai" attack/body samples — a darker, rounder
vintage grand that voices the **GM 1 Bright Acoustic Piano default** (no CC0
select needed) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

8 pitch zones (C2–C6) × 3 dynamics (pp/mf/f) × 2 round robins = 48 logical
sample names backed by 32 unique mono 16-bit 44.1 kHz WAVs. The 16 names that
reuse an upstream velocity layer resolve through the packaged `ALIASES` manifest,
so each payload is embedded and decoded once. Consumers normally reach this crate
through `ferrosintesis`. Provenance and processing (including the VCSL octave-label
trap) are in `PROVENANCE.md`. Licence: CC0 1.0 (public domain); `NOTICE` carries a
courtesy credit to VCSL / Sam Gossner.

Regenerate the WAVs with `python3 tools/ferrosintesis-samples/prepare.py --only=kawai`.
