# Eastman E1D fret-noise — first-party source recordings

Purpose-recorded **fret / finger-slide noise** on Arthur's own **Eastman E1D**
dreadnought steel-string, recorded 2026-07-24. The source for the sampled **GM 120
(Guitar Fret Noise)** round-robin bank in ferrosintesis, replacing the modeled
white-noise burst as the default (the burst stays the `--no-samples` fallback).

Same guitar and strings as the GM 25 steel banks (`../acoustic-guitar-eastman-e1d/`),
recorded the day after and **not** re-strung between, so the fret noise sits in the
same tonal world as the guitar it accompanies.

- **`DR0000_0203.opus`** — slides take: all six strings damped at the nut, fret-hand
  position shifts up and down the neck. The primary source (18 of the bank's samples
  were auditioned from here).
- **`DR0000_0204.opus`** — slides + body taps: more slides, plus soundboard/side knocks
  (the taps are reserved for a future note-off `stop_thump` job, not this bank).

## Recording

| | |
|---|---|
| Instrument | Eastman E1D dreadnought, steel strings (same set as the GM 25 banks) |
| Performer | Arthur |
| Master format | 48 kHz · 24-bit · stereo |
| Technique | all strings damped hard at the nut; fret-hand slides on the wound courses |
| Levels | 0203 peak −3.8 dBFS, floor ~−44 dBFS; 0204 peaks +3.0 dBFS (spoken slate clips — that region is not sampled) |
| Licence | **CC0-1.0** (public-domain dedication by the repo owner) |

Kept as Opus (160 kbps, music mode) as the in-repo performance archive; Arthur holds
the 48 kHz/24-bit lossless masters. The **`cuts/`** directory holds the 12 selected
one-shot sources as committed 24-bit/48 kHz lossless WAV — these are the authoritative
re-bake input (same rationale as the guitar's `zones/`), so the embedded bank is
reproducible offline with no ffmpeg dependency.

## Why a purpose-made take (and not the July guitar masters)

The July guitar recordings (`../acoustic-guitar-eastman-e1d/`) contain **no** usable
fret squeak: a chromatic walk of discrete plucked notes has the fretting hand *placing
and lifting*, not sliding, and the one detectable slide sat 12 dB under a ringing note.
The measured GM 120 defect was threefold — the modeled burst is ~12 dB quieter than the
Roland SC-55mkII / Yamaha S-YXG50 references (relative to their own steel guitar), an
octave-wide hiss (48 % of energy above 4 kHz vs ~3 %), and has no low-mid body. This
session was recorded specifically to beat all three axes with real winding rasp.

## Cut map (the 12 selected one-shots)

Selected from 42 clean slide candidates for rasp character (peak third-octave band
1–3 kHz, ≤ 20 % energy above 4 kHz, low-mid within ~30 dB of peak — i.e. body, not a
ringing note) and spread across duration/brightness so the round-robin does not
machine-gun. Cut at the local envelope minimum before each onset with an 8 ms fade-in /
12–30 ms fade-out (the takes are wall-to-wall, so there is no silence to cut from —
same constraint as the guitar). Metrics are of the source event:

| cut | source | at | dur s | peak dBFS | peak band | >4 kHz | 125 Hz vs pk |
|-----|--------|-----|-------|-----------|-----------|--------|--------------|
| fret_rr01 | 0203 |  4.55 s | 0.79 | −6.4  | 2000 Hz | 12.5 % | −24.7 dB |
| fret_rr02 | 0203 |  7.84 s | 1.18 | −6.7  | 2000 Hz |  6.2 % | −21.8 dB |
| fret_rr03 | 0203 |  9.82 s | 0.36 | −6.8  | 1600 Hz |  4.8 % | −27.1 dB |
| fret_rr04 | 0203 | 11.62 s | 1.70 | −6.1  | 2000 Hz |  8.1 % | −30.1 dB |
| fret_rr05 | 0203 | 15.21 s | 0.88 | −7.9  | 1000 Hz |  4.5 % | −20.0 dB |
| fret_rr06 | 0203 | 17.15 s | 0.43 | −4.6  | 2000 Hz |  5.3 % | −24.1 dB |
| fret_rr07 | 0203 | 22.96 s | 0.53 | −8.7  | 2000 Hz |  4.8 % | −28.3 dB |
| fret_rr08 | 0203 | 24.57 s | 1.20 | −8.8  | 2000 Hz |  6.6 % | −16.6 dB |
| fret_rr09 | 0204 |  9.03 s | 1.44 | −8.6  | 1600 Hz |  3.1 % | −25.0 dB |
| fret_rr10 | 0204 | 11.11 s | 0.45 | −10.7 | 2000 Hz |  4.9 % | −19.5 dB |
| fret_rr11 | 0204 | 12.12 s | 0.36 | −13.6 | 1600 Hz | 11.4 % | −22.4 dB |
| fret_rr12 | 0204 | 32.45 s | 0.54 | −12.4 | 2000 Hz |  4.9 % | −23.6 dB |

Set median: peak band 2000 Hz, 5.1 % above 4 kHz, low-mid −23.8 dB — on the SC-55 /
S-YXG50 targets (≈ 2000–2500 Hz, ~3 %, ~−26 dB) and far from the modeled burst it
replaces (3150 Hz, 48 %, −44 dB).

## Re-baking

`tools/ferrosintesis-samples/fretnoise_bake.py` converts these `cuts/` (48 kHz/24-bit)
to the embedded crate's 16-bit mono 44.1 kHz format (resample, loudness-equalise across
the round-robin set, TPDF-dither). Output lands in
`crates/ferrosintesis-samples-fretnoise/samples/`.
