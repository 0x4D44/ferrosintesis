# Provenance — ferrosintesis-samples-fretnoise

## Packaged family inventory

| Family | Files |
|--------|------:|
| `fretnoise_*` | 12 |

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

### Committed-source checksums

SHA-256 pins for both performance archives and all twelve selected lossless cuts.
The provenance oracle discovers these recursively from the repo-root `samples/`
store and requires every digest to remain in packaged provenance.

| Source file | SHA-256 |
|-------------|---------|
| `samples/fret-noise-eastman-e1d/DR0000_0203.opus` | `ffe279cbc65f7a15aefc2d7bac4be192576c632e5051bee52372a4d709c00a1d` |
| `samples/fret-noise-eastman-e1d/DR0000_0204.opus` | `73996b144151e8af59729d78465563eeb122ef6ff96d8a7f272642e627f773b4` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr01.wav` | `a79c4f5b4299dcf1767db3c6597966450be2a068d6140ef59bd1aaad20f5350b` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr02.wav` | `b62eb9d8d631f9291da8224fda0ab2e386919daa7b15516067eb00e442670ac5` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr03.wav` | `258aad687b59406349fc1b9cc266adfef5d1322d9ee5c47f1ec868f13c754216` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr04.wav` | `5666b8dea83fd452a894877d60226292a50633fc8600ca3ca61d4a5d801fe79e` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr05.wav` | `ed37190e96ee95a80412ea73e8f340039495f66adbbe484188b31597fa7016c1` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr06.wav` | `4c5f8a760d6e47fa538469554a2bb5d23ceb78665a1959ac0c2c400a34a4468b` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr07.wav` | `1c22d60d3d153f326286c094c3fa534d42667fc95f36a8fb74317c337d46a789` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr08.wav` | `373543fc8310319adf8a9ad974f883b3c0d28fb6b8ef8cb4806a151e917b9490` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr09.wav` | `f2860bbb45f201c8b9abdd7bebd5463946b012ebf9cfffcbff1f2ad08147f170` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr10.wav` | `067db61ba9ad7962aec14fccc66fed0d77a94736541774239ec0558a44f5a6f3` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr11.wav` | `48c6bb3c7f1068251e92e46e86a69d2ae957ab368ce0467a7917d0909be2d63f` |
| `samples/fret-noise-eastman-e1d/cuts/fret_rr12.wav` | `3c3139b11a18b4c5a1b784f065b0398b9493e8eea0d3cef7a5192417b8fecbb5` |

## Licence

**CC0-1.0.** A public-domain dedication by the repo owner of his own performance. No
attribution is required, so this crate has no `NOTICE` and is exempt from the
attribution-guide oracles in `ferrosintesis::licensing`.

## Bake

`tools/ferrosintesis-samples/fretnoise_bake.py` converts the committed 48 kHz/24-bit
`cuts/` to this crate's embedded format: resample to 44.1 kHz (band-limited FFT method),
loudness-equalise each take's body RMS to a common target so the round-robin does not
jump in level, TPDF-dither to 16-bit mono.

Byte identity is scoped to the canonical bake environment: 64-bit CPython
3.14.3 on Windows x86-64 with NumPy 2.4.4, installed from
`tools/ferrosintesis-samples/requirements-fretnoise-bake.txt`. NumPy does not
promise cross-version random streams, and this package does not claim
cross-platform FFT identity. `BAKE-SHA256` pins every output; the bake's
`--verify` mode regenerates all twelve files in memory and checks both generated
and committed hashes without writing. The observed canonical re-bake matches all
twelve pins.

The embedded WAVs are **16-bit mono 44.1 kHz** (the format
`sampler::parse_wav` requires). Total embedded size ≈ 1.0 MiB. Independent
acoustic-tolerance oracles in `ferrosintesis::voices` guard the sampled GM120
level, rasp spectrum, pitch independence, and one-shot lifetime even when a
future canonical environment is deliberately changed and the hashes are
reviewed.

## Why sampled

The modeled GM 120 (a band-passed white-noise burst) measured ~12 dB quieter than the
Roland SC-55mkII and Yamaha S-YXG50 references relative to their own steel guitar, an
octave-wide hiss (≈ 48 % of energy above 4 kHz versus ≈ 3 % on the references), and had
no low-mid body (MM-BUG-KILN-00040). These recordings supply real winding rasp with the
correct centre band (~2 kHz), narrow bandwidth, and body. The modeled burst is retained
as the `--no-samples` / modeled-only fallback.
