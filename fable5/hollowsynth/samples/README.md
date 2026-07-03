# Attack-transient sample bank

Mono 16-bit 44.1 kHz WAVs, embedded into the binary via `include_bytes!`
and used by `src/sampler.rs` for LA-style synthesis: each supplies the
onset of a note (the hammer strike, the bow bite, the breath chiff), then
crossfades into the modeled sustain.

- `piano_*_{pp,mf,f}.wav` and `piano_*_{pp,mf,f}_rr2.wav` — upright piano
  strikes, 9 pitch zones (C2–C6) × 3 dynamic layers × **2 round robins**
  (picked by the note's random seed, so repeated notes don't sound
  cloned). Kept much longer (1.8 s) than the other families — the piano
  has no expressive sustain to preserve, so the real recording carries
  most of the note and the model only supplies the long tail.
- `violin_*_f.wav` / `violin_*_p.wav` — solo violin arco, forte / piano
  (selected by note velocity), 6 pitch zones each, ~0.63 s
- `flute_*.wav` — flute sustain onsets, 5 pitch zones, ~0.63 s

## Provenance & license

Trimmed from **VSCO 2 Community Edition** (Versilian Studios /
sgossner, <https://github.com/sgossner/VSCO-2-CE>), released under
**CC0 1.0 / public domain**. No attribution required; given anyway with
thanks.

## Regenerating

`prepare.py` (pure stdlib) downloads the source sustains and rebuilds the
bank: onset detection, trim, fades, peak normalization, and an
autocorrelation pitch measurement (octave-safe, parabolic-refined). It
prints each zone's root frequency — those values are hardcoded in
`src/sampler.rs` and must be updated if the bank changes.

```powershell
python prepare.py
```
