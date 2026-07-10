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
- `trumpet_*_{p,f}.wav`, `mutetpt_*_{p,f}.wav` (straight mute — its own
  bank, the mute identity is attack-critical), `trombone_*_{p,f}.wav`,
  `tuba_*_{p,f}.wav`, `horn_*_{p,f}.wav` — brass sustain onsets for
  GM 56–61, 5–6 pitch zones × 2 dynamic layers (VSCO v1 → p, v3 → f;
  the horn's top D4 zone exists only as v1 at the pinned rev and is
  reused for both layers), ~0.63 s. GM 61 (section) layers the trumpet
  bank at reduced gain over its scattered modeled players.
- `oboe_*_{p,f}.wav`, `bassoon_*_{p,f}.wav`, `clarinet_*_{p,f}.wav` — reed
  sustain onsets for GM 68–71, 6 pitch zones × 2 dynamic layers (VSCO
  v1 → p, v3 → f; the bassoon has only v1/v2 at the pinned rev, so
  v2 → f), ~0.63 s. GM 69 (english horn) reuses the oboe bank repitched
  down; the saxes 64–67 stay pure model (no sax in VSCO 2 CE).
- `nylon_*.wav` — nylon (classical) guitar pluck onsets for GM 24, 7 pitch
  zones E2–E5 (~6-semitone spacing; B2 stands in for the source's missing
  A#2), kept 0.9 s so the sample carries the pick transient and early body
  resonance while the Karplus-Strong string keeps the bendable decay. The
  source has one take per note — no velocity layers, no round robins. GM 25
  (steel) stays pure model: no clean CC0 steel-string source yet (the
  FreePats FSS Steel-String set is GPL-with-exception).
- `drum_sus_cymb1_*`, `drum_crash1_*`, `drum_kick_*`, `drum_snare2_*`
  — unpitched drum-hit overlays for the default kit: crash/suspended cymbal
  attacks kept to ~2.2 s, kick/snare attacks kept to ~0.46 s. The modeled drum
  voice remains the sustain/body layer.

## Provenance & license

Trimmed from **VSCO 2 Community Edition** (Versilian Studios /
sgossner, <https://github.com/sgossner/VSCO-2-CE>), released under
**CC0 1.0 / public domain**. The generator pins source downloads to VSCO commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`. No attribution required; given
anyway with thanks.

The `nylon_*` bank is trimmed from the **FreePats project "Spanish classical
guitar"** sound bank, version 2019-06-18, by roberto@zenvoid.org
(<https://freepats.zenvoid.org/Guitar/acoustic-guitar.html>), released under
the **Creative Commons CC0 1.0 Universal public domain dedication** (stated on
the set page and in the archive's `readme.txt`; the full legal text ships in
the archive as `cc0.txt`). The generator pins the exact versioned archive
`https://freepats.zenvoid.org/Guitar/SpanishClassicalGuitar/SpanishClassicalGuitar-SFZ-20190618.7z`
by SHA-256
`ef2fb7de0cc0ab561c4ebc28494f3fc2962596e4f32f16d6c96b8a385c7c098b`
(verified before extraction). Extraction shells out to 7-Zip
(`7z x -y -o<dir> <archive>`) — the archive uses an LZMA filter chain that
bsdtar/GNU tar cannot decode; no Python dependency is added.

## Regenerating

`prepare.py` (pure stdlib) downloads the source sustains and rebuilds the
bank: onset detection, trim, fades, peak normalization, and an
autocorrelation pitch measurement (octave-safe, parabolic-refined). It
prints each zone's root frequency — those values are hardcoded in
`src/sampler.rs` and must be updated if the bank changes. Downloads are cached
under the system temp directory by VSCO revision and fetched atomically so an
interrupted run cannot leave a partial final cache file.

```powershell
python prepare.py
```
