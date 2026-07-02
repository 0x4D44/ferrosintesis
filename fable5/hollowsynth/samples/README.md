# Attack-transient sample bank

Seventeen short (0.63 s) mono 16-bit 44.1 kHz WAVs, embedded into the
binary via `include_bytes!` and used by `src/sampler.rs` for LA-style
synthesis: each supplies the first ~200 ms of a note (the bow bite, the
breath chiff), then crossfades into the modeled sustain.

- `violin_*_f.wav` / `violin_*_p.wav` — solo violin arco, forte / piano
  (selected by note velocity), 6 pitch zones each
- `flute_*.wav` — flute sustain onsets, 5 pitch zones

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
