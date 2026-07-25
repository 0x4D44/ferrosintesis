# Clavinet sample provenance

## Packaged family inventory

| Family | Files |
|--------|------:|
| `clavinet_*` | 11 |

The 11 WAVs in `samples/` are the GM7 clavinet extracted from the **MuseScore
"MS Basic"** soundfont and baked into self-contained decaying notes for
ferrosintesis's default sampled clavinet (GM program 7). They are **MIT-licensed**,
not CC0 — see [`NOTICE`](NOTICE) for the required attribution.

## Source (pinned)

- Repo: [`musescore/MuseScore`](https://github.com/musescore/MuseScore)
- File: `share/sound/MS Basic.sf3`
- Commit: `d307a2bd899f15bf650efc3c2891211af5cb78b5`
- Blob SHA-1: `5be56b2fafa5eee347256cbe0d2fbfacd01702b6`
- SHA-256: `5ea2375e8bd7d8e71def1036978c1621e85b66934169b6a2744b27b9b3c2d99c`
- Size: 51,278,610 bytes

`tools/ferrosintesis-samples/prepare.py` verifies the SHA-256 before use and pins
the commit in `MUSESCORE_REV`.

## Extraction and bake

MS Basic is an **SF3** soundfont: SF2 structure, but each sample is a self-contained
**Ogg-Vorbis** stream stored in the `smpl` chunk (so the SF3 sample-header
`start`/`end` are BYTE offsets delimiting the Ogg, not PCM frame offsets). The
generator:

1. Parses the RIFF `sfbk` and finds the preset at bank 0, preset 7 (`Clavinet`) →
   instrument #148 → its 11 sample zones (tiling MIDI key range 0-108).
2. Slices each zone's Ogg out of `smpl` and decodes it with **ffmpeg** to mono
   44.1 kHz PCM (the same shell-out precedent as the drumkit's FLAC decode).
3. Bakes each into a ~1.6 s decaying note: because the Ogg decode drops ~80-100
   trailing frames (Vorbis padding) — which corrupts the soundfont's short low-note
   loops — the loop is taken **pitch-synchronously** (an exact integer number of
   fundamental periods from the accurate `originalPitch`), crossfaded at the wrap,
   repeated under a register-scaled exponential decay, then faded and normalized.

The 11 zones sound **G1, C2, G2, C3, G3, C4, G4, C5, G5, C6, G6** (the soundfont's
sample *name* octave is one higher than the true `originalPitch` — the true pitch is
used). `nearest`-root selection repitches per key at render time.

The decay `t60` and output level are **ear-tunable** constants in `prepare.py`
(`clavinet_t60`) and `sampler.rs` respectively.
