# Provenance — ferrosintesis-samples-fretnoise

## Source

Twelve fret-noise (finger-slide) one-shots recorded by the repo owner (Arthur) on his
own **Eastman E1D** dreadnought steel-string acoustic, 2026-07-24, with all six strings
damped hard at the nut so the fret-hand slides on the wound courses produce winding rasp
with no ringing pitch. Same guitar and string set as the GM 25 steel banks
(recorded 2026-07-23, not re-strung between), so the fret noise matches the guitar it
accompanies.

Recorded 48 kHz / 24-bit stereo (two takes, `DR0000_0203` and `DR0000_0204`). The
in-repo performance archive and the 12 selected lossless cuts live under
`samples/fret-noise-eastman-e1d/` in the workspace root; the full recording provenance,
level measurements, and the cut map are in that directory's `README.md`.

## Licence

**CC0-1.0.** A public-domain dedication by the repo owner of his own performance. No
attribution is required, so this crate has no `NOTICE` and is exempt from the
attribution-guide oracles in `ferrosintesis::licensing`.

## Bake

`tools/ferrosintesis-samples/fretnoise_bake.py` converts the committed 48 kHz/24-bit
`cuts/` to this crate's embedded format: resample to 44.1 kHz (band-limited FFT method),
loudness-equalise each take's body RMS to a common target so the round-robin does not
jump in level, TPDF-dither to 16-bit mono. Deterministic — a re-bake is byte-identical.
The embedded WAVs are **16-bit mono 44.1 kHz** (the format `sampler::parse_wav`
requires). Total embedded size ≈ 1.0 MiB.

## Why sampled

The modeled GM 120 (a band-passed white-noise burst) measured ~12 dB quieter than the
Roland SC-55mkII and Yamaha S-YXG50 references relative to their own steel guitar, an
octave-wide hiss (≈ 48 % of energy above 4 kHz versus ≈ 3 % on the references), and had
no low-mid body (MM-BUG-KILN-00040). These recordings supply real winding rasp with the
correct centre band (~2 kHz), narrow bandwidth, and body. The modeled burst is retained
as the `--no-samples` / modeled-only fallback.
