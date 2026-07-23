# Provenance — ferrosintesis-samples-mandolin

`mandolin_*.wav` — owner-recorded mandolin pluck onsets, recorded by the repository owner on
**2026-07-23** on his own instrument, dedicated **CC0 1.0 Universal** (public domain). The owner
holds the recording and grants it to the public domain; no third-party licence applies.

## Source

One continuous take, `DR0000_0198.wav` (24-bit / 48 kHz stereo, 2:45, 47.4 MB), three passes
over the same ten fretboard positions at three dynamics — normal, soft, then hard. Where a note
was fluffed it was played again, the later take being the keeper. The raw take is not committed
(47 MB, owner-personal); the trimmed per-note source cuts in
`tools/ferrosintesis-samples/mandolin-src/` are the committed input, and `samples/*.wav` here is
the baked output.

## Positions

Ten zones, three hand positions, chosen so that no two coincide in pitch (the courses are a
fifth apart and the frets a semitone, so open/5th and 10th/12th never collide):

| Zone | Course / fret | Nominal | Measured root |
|------|---------------|---------|---------------|
| G3   | G open        | 196.00  | 195.53 Hz |
| C4   | G 5th         | 261.63  | 266.09 Hz |
| D4   | D open        | 293.66  | 291.60 Hz |
| G4   | D 5th         | 392.00  | 394.41 Hz |
| A4   | A open        | 440.00  | 439.13 Hz |
| D5   | A 5th         | 587.33  | 594.01 Hz |
| E5   | E open        | 659.26  | 659.52 Hz |
| A5   | E 5th         | 880.00  | 885.35 Hz |
| D6   | E 10th        | 1174.66 | 1184.33 Hz |
| E6   | E 12th        | 1318.51 | 1328.33 Hz |

Roots are **measured, not nominal**. The instrument's open strings are in tune (−12 to +1
cents) but its fretted notes run sharp — up to **+29 cents at the 5th fret on the thickest
course** — which is normal fretting-pressure/action behaviour on a short-scale instrument.
`LaVoice` repitches from the measured root, so the bank plays in tune regardless.

## Layers

Two dynamic layers, `_p` and `_f`, split at the repo-wide `vel >= 80` threshold.

The take also contained a third, "normal", pass. It was **measured and dropped**: its spectral
centroid was indistinguishable from the hard pass (6/10 sign consistency across the ten zones,
median shift +0.09 harmonics — a coin flip), so a third layer would have cost ~1.1 MiB in a
size-capped crate for no timbral information. The soft/loud split is weaker than one would like
(8/10 sign consistency, median +0.56 harmonics, sign test p≈0.055) but is consistent and in the
direction physics predicts.

There are **no round robins**: one take per zone per layer. This is the bank's main limitation —
a mandolin's signature technique is tremolo at 12–16 strokes/second, which is the worst case for
a single repeated sample. The engine's onset variation masks some of it.

## Processing (one-time, deterministic)

1. Locate each note in the take by onset detection; identify its pitch by a matched harmonic
   comb with a **sub-harmonic veto**. The veto is load-bearing: five of the ten zones form
   octave pairs (G3/G4, D4/D5, A4/A5, D5/D6, E5/E6), and a mandolin's low fundamentals are weak
   because a small body radiates them poorly, so a bare comb scores the octave *above* higher.
2. For each zone and layer, keep the **last credible** take. "Credible" excludes events more
   than 18 dB below the pass's typical note level (fret squeak, pick handling) and, when
   re-anchoring to a fast re-pluck, anything more than 12 dB below the original attack.
3. Re-anchor past sub-refractory re-plucks. Two soft takes (G3, G4) contained a fluff followed
   by the real note 0.17–0.23 s later — faster than the onset detector's 0.28 s refractory, so
   invisible to it. Without this the zone would double-strike on every note.
4. Repair isolated clipping: 13 single full-scale samples were cubic-interpolated. Four genuine
   clipped runs (up to 6 consecutive samples) were left untouched — they fall in takes that
   later retakes superseded.
5. Downmix to mono, resample 48 kHz → 44.1 kHz (64-tap Blackman-windowed sinc, cutoff at the
   output Nyquist), dither to 16-bit (TPDF). **No normalisation** at this stage: the two layers
   must keep their recorded level relationship until the bake deliberately discards it.
6. `prepare.py` then trims to onset, keeps 0.9 s, applies the squared fade-out, peak-normalises
   to 0.9 and measures the root — the same chain every other onset bank goes through.

## Known weak point

`mandolin_A5_p.wav` carries a low-level handling noise ~0.77 s in, about 19 dB below the note's
own peak and inside the region the bake's squared fade-out attenuates. It is the quietest take
in the bank (−28 dBFS) and had no usable alternative in its pass. Re-record this zone first if
the bank is ever revisited.
