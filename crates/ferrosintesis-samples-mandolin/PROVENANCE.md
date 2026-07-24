# Provenance — ferrosintesis-samples-mandolin

`mandolin_*.wav` — owner-recorded mandolin pluck onsets, recorded by the repository owner on
**2026-07-24** on his own instrument, dedicated **CC0 1.0 Universal** (public domain). The owner
holds the recording and grants it to the public domain; no third-party licence applies.

## Source

One continuous take, `DR0000_0202.wav` (24-bit / 48 kHz stereo, 2:40, 44.1 MB), **zero clipped
samples**. Ten fretboard positions, four takes each. Where a note was fluffed the owner replayed
all four, so **the last four takes of each note are the keepers**. The raw take is not committed
(44 MB, owner-personal); the trimmed per-note cuts in
`tools/ferrosintesis-samples/mandolin-src/` are the committed input, and `samples/*.wav` here is
the baked output.

A first session (`DR0000_0198`, 2026-07-23) captured three dynamic passes instead. It was
superseded: see "Why round robins and not dynamics" below.

## Positions

Ten zones from three hand positions, chosen so no two coincide in pitch — the courses are a
fifth apart and the frets a semitone, so open/5th and 10th/12th never collide, whereas the 7th
fret would have duplicated the next open string exactly.

| Zone | Course / fret | Nominal | rr1 | rr2 | rr3 | rr4 |
|------|---------------|---------|-----|-----|-----|-----|
| G3 | G open  |  196.00 |  195.57 |  195.74 |  195.84 |  195.61 |
| C4 | G 5th   |  261.63 |  264.95 |  264.82 |  264.59 |  264.64 |
| D4 | D open  |  293.66 |  292.93 |  292.65 |  293.03 |  293.33 |
| G4 | D 5th   |  392.00 |  394.37 |  395.11 |  394.68 |  394.98 |
| A4 | A open  |  440.00 |  440.41 |  439.28 |  440.40 |  439.17 |
| D5 | A 5th   |  587.33 |  591.60 |  591.17 |  591.36 |  590.84 |
| E5 | E open  |  659.26 |  658.52 |  656.88 |  657.51 |  656.93 |
| A5 | E 5th   |  880.00 |  883.17 |  883.72 |  882.60 |  883.22 |
| D6 | E 10th  | 1174.66 | 1182.91 | 1181.88 | 1181.48 | 1181.42 |
| E6 | E 12th  | 1318.51 | 1328.92 | 1328.13 | 1327.97 | 1327.72 |

Roots are **measured, not nominal**. The open strings are in tune (within a few cents) but the
fretted notes run sharp — up to **+22 cents at the 5th fret on the thickest course** — which is
normal fretting-pressure behaviour on a short-scale instrument. `LaVoice` repitches from the
measured root, so the bank plays in tune regardless. Take-to-take spread within a zone is
~2–5 cents: the same note played four times, not four different notes.

## Round robins

**Four takes per zone, one dynamic.** `rr1` is the earliest of the four and the order is
meaningful — the takes were played with alternating pick direction, so cycling them strictly
(never randomly) reproduces a real player's down/up alternation. The engine selects with a
per-`(channel, key)` strike counter, so consecutive strikes of the same key step
0→1→2→3→0… deterministically.

### Why round robins and not dynamics

A mandolin cannot be played at meaningfully different dynamics — the owner's own finding, and
the first session's three-pass recording confirmed it numerically: the loud and normal passes'
spectral centroids were indistinguishable (6/10 sign consistency across the ten zones, median
shift +0.09 harmonics — a coin flip). The soft/loud split was weak but real (8/10, median +0.56
harmonics, sign test p≈0.055). Spending the recording budget on take variety rather than dynamic
layers was therefore the better trade for this instrument.

## Processing (one-time, deterministic)

1. Locate each note by onset detection; identify its pitch by a matched harmonic comb with a
   **sub-harmonic veto** *and* a **missing-fundamental (octave-up) correction**. Both are
   load-bearing here: five of the ten zones are octave pairs, and a small mandolin body barely
   radiates the low G3 fundamental, so its 2nd harmonic dominates and the note reads as G4. The
   plain sub-harmonic veto cannot catch that — there is nothing at f0/2 to detect when the
   fundamental is *missing*. The tell is energy at the candidate's **odd-half-harmonics**
   (1.5× and 2.5× f0), which are the octave-below note's 3rd and 5th harmonics.
2. Per zone, keep the **last four credible** takes. "Credible" excludes anything more than 15 dB
   below that note's own strongest take (fret squeak, handling, quiet fluffs). Each onset's level
   is measured in a window that **ends before the next onset** — a fixed window lets a quiet
   onset absorb a following loud pluck's level and masquerade as a real take.
3. Re-anchor each keeper onto the loudest attack within 0.35 s. The onset detector's 0.176 s
   refractory can hide the real pluck behind a quiet precursor, which would otherwise bury a
   +40 dB attack ~0.17 s inside the sample.
4. Downmix to mono, resample 48 kHz → 44.1 kHz (64-tap Blackman-windowed sinc, cutoff at the
   output Nyquist), dither to 16-bit (TPDF). No normalisation at this stage.
5. `prepare.py --only=mandolin` then trims to onset, keeps 0.9 s, applies the squared fade-out,
   peak-normalises to 0.9 and measures the root — the same chain every other onset bank uses.

Every cut is verified before baking: correct note (scored against its octave neighbours), clean
onset and tail, no second attack inside the 0.9 s keep window, no clipping.
