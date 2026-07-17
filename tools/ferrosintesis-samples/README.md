# Attack-transient sample-bank tooling

This directory also holds `prepare_drumkit.py`, the generator for the
sampled-cymbal bank in `crates/ferrosintesis-samples-drumkit/` (Virtuosity
Drums `mid` mic set + the Big Rusty Drums china, both CC0, pinned by commit
SHA; FLAC decode shells out to ffmpeg at tool time). That bank's inventory
and provenance live in `crates/ferrosintesis-samples-drumkit/PROVENANCE.md`.

The rest of this README covers `prepare.py`: the generator, tests, full
inventory, and provenance for
ferrosintesis's 202 attack transients (16.68 MiB source). The generated mono
16-bit 44.1 kHz WAVs are split between
`crates/ferrosintesis-samples-core/samples/` (piano, violin, flute) and
`crates/ferrosintesis-samples-orchestral/samples/` (all other families). Those
two default asset crates embed the bytes with `include_bytes!`;
`crates/ferrosintesis/src/sampler.rs` uses them for LA-style synthesis. Each WAV
supplies the onset of a note, then crossfades into the modeled body or sustain.

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
- `vlnens_*_{p,f}.wav`, `celens_*_{p,f}.wav` — string-section sustain
  onsets for GM 48–49, 6 pitch zones × 2 dynamic layers each (violin
  section v1 → p, v2 → f; cello section v1 → p, v3 → f; both sections
  sound one octave above their VSCO filename labels — roots are measured,
  not assumed), ~0.63 s. One combined bank per dynamic: the cello zones
  cover the low split and the violin zones the high, so nearest-root
  selection picks the section by register. Synth strings GM 50–51 stay
  pure model (they are *synth* strings), as does the alt orchestral bank.
- `nylon_*.wav` — nylon (classical) guitar pluck onsets for GM 24, 7 pitch
  zones E2–E5 (~6-semitone spacing; B2 stands in for the source's missing
  A#2), kept 0.9 s so the sample carries the pick transient and early body
  resonance while the Karplus-Strong string keeps the bendable decay. The
  source has one take per note — no velocity layers, no round robins. GM 25
  (steel) stays pure model: no clean CC0 steel-string source yet (the
  FreePats FSS Steel-String set is GPL-with-exception).
- `harpsi_*.wav` — harpsichord (GM 6) quill-pluck onsets, 10 pitch zones
  sounding C2–F6 (~6-semitone C/F grid, one take per note: single register
  `Main`, single round robin), kept 0.9 s like the guitars so the sample carries
  the quill transient and early jangle while the Karplus-Strong string keeps the
  slow-damped decay. VCSL's file labels sit ONE OCTAVE BELOW sounding pitch, so
  the bake renames each zone to its sounding pitch and the measured root (not the
  label) lands in the zone table.
- `clavinet_*.wav` — GM 7 clavinet, the DEFAULT sampled voice (11 pitch zones
  sounding G1–G6), extracted from the MuseScore "MS Basic" **SF3** soundfont. Unlike
  the onset-only banks these are FULL decaying notes: each zone's ~0.2 s Ogg body is
  looped **pitch-synchronously** (an exact integer number of `originalPitch` periods,
  because the Ogg decode drops ~80–100 trailing frames and corrupts the soundfont's
  short low-note loops) under a register-scaled exponential decay, then faded — a
  self-contained ~1.6 s clavinet note the `ClavinetSampled` voice repitches per key
  with a fast note-off damp. Output routes to the separate MIT `-clavinet` crate; the
  modeled Pluck stays the `--no-samples` / CC0-alt voice. `t60`/level are ear-tunable.
  **Unlike every other bank here, this one is MIT, not CC0.**
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

The `harpsi_*` bank is trimmed from the **Versilian Community Sample Library
(VCSL)** "Harpsichord, Unk" (Harpsi4) set, a 5-octave FF–f''' harpsichord
(<https://github.com/sgossner/VCSL>), released under the **Creative Commons CC0
1.0 Universal public domain dedication** — the repo's root `LICENSE` is the full
CC0 1.0 legal text (added in commit `c1ea7bcc`), and the README restates it. The
generator pins the source to commit
`c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` and fetches the ten `Sustains` WAVs
directly (24-bit stereo; `read_wav` downmixes to mono). No attribution required;
given anyway with thanks.

The `clavinet_*` bank is extracted from the **MuseScore "MS Basic"** soundfont
(`musescore/MuseScore`, `share/sound/MS Basic.sf3`), released under the **MIT
License** — the ONLY non-CC0 bank here. MIT (and MuseScore's terms) require the
copyright notices to travel with the samples, so they ship in their own
`ferrosintesis-samples-clavinet` crate with a `NOTICE`; the clavinet traces to the
FluidR3Mono lineage (Frank Wen / Michael Cowgill / S. Christian Collins). The
generator pins commit `d307a2bd899f15bf650efc3c2891211af5cb78b5` and verifies the
SF3's SHA-256 (`5ea2375e…3c2d99c`) before use. SF3 stores each sample as a
self-contained Ogg-Vorbis stream in the `smpl` chunk, so extraction slices the
GM 7 preset's zones out by their byte offsets and decodes them with **ffmpeg** (the
same shell-out precedent as `prepare_drumkit.py`'s FLAC decode).

## Regenerating

`prepare.py` (pure stdlib) downloads the source sustains and rebuilds both
package banks: onset detection, trim, fades, peak normalization, and an
autocorrelation pitch measurement (octave-safe, parabolic-refined). It
prints each zone's root frequency — those values are hardcoded in
`crates/ferrosintesis/src/sampler.rs` and must be updated if the bank changes.
Downloads are cached under the system temp directory by VSCO revision and fetched
atomically so an interrupted run cannot leave a partial final cache file. Piano,
violin, and flute output routes to the core package; every other family routes to
the orchestral package.

```powershell
python tools/ferrosintesis-samples/prepare.py
```
