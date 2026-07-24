# Provenance — ferrosintesis-samples-ccby

Two real recordings from Freesound, each **CC BY 4.0** (per-sound license confirmed in each
pack's bundled `_readme_and_license.txt` — all sounds "Attribution 4.0", no exceptions):

| GM | Instrument | Source | Author | Pack |
|----|-----------|--------|--------|------|
| 4 | Electric piano (Rhodes tine) | "C_S Fender Rhodes Mark II" | tim.kahn | Freesound **3957** |
| 15 | Hammered dulcimer | "Multi-sampled Hammered Dulcimer" | iternetcone | Freesound **19445** |

**Freesound gates downloads behind a login**, so these cannot be auto-fetched. The decoded +
trimmed source notes are committed under `tools/ferrosintesis-samples/freesound-src/` (the
same "committed source" pattern as `gong-src/`), and `prepare.py --only=rhodes,dulcimer`
bakes onsets from them (trim to onset, measure root near the note label, mono 16-bit 44.1 kHz).

To fully regenerate from scratch: download packs 3957 (Rhodes) + 19445 (dulcimer) from
Freesound (login required), re-decode/trim the chosen notes into `freesound-src/`, then run
`prepare.py`. The `jRhodes` set was rejected — its sample bytes are CC-BY-**NC** (see the
round-3 voice-quality HLD); tim.kahn's pack is plain CC-BY and safe for a published crate.

## Committed-source checksums

SHA-256 of each committed source WAV under
`tools/ferrosintesis-samples/freesound-src/`. Previously this file carried pack IDs
only, while `prepare.py` claimed it recorded "exact pack IDs/SHAs"
(MM-BUG-KILN-00069 item 5).

| Source file | SHA-256 |
|-------------|---------|
| `dulcimer_A4.wav` | `a04c3c1a5df39b65ebc6d21ab3a8ae26b6ddfe35c14a396b7b1843a97fa41f01` |
| `dulcimer_B4.wav` | `d1fdf14840f16cfc3e9a344935d44d51344180ae68c7e449b430c03fede0e12c` |
| `dulcimer_C#4.wav` | `bd995c208e02db163e2ad7f1070ddbabfc79b5c8be75c62a67b6df178a762708` |
| `dulcimer_C5.wav` | `6824d88fad4516148033846b250b0b3a69384a485de9d5af035641ca6372d193` |
| `dulcimer_D4.wav` | `8599d6f33a1c6aafeb5b1209377c9dfa2f312ca908b0105dfdee144a6dcceb34` |
| `dulcimer_D5.wav` | `55457ea0ca800637836fa9bda2e590868c38930fa0b95234e8b942764bf5cea0` |
| `dulcimer_E4.wav` | `eded99dae7e216fd9c880667a139d5f1ffe71b5aa4ecbf9ea75e8be96fd54da8` |
| `dulcimer_F#4.wav` | `bc1a5069452e2eafefd89901877076e2f0b0f4d58c239e8f577fc7942d4f1ccc` |
| `dulcimer_G4.wav` | `1ef71079711b9413c3594c873d81917c0ce5729fa0e90e6976d6f7deec2ba899` |
| `rhodes_A#1.wav` | `7ab3757a24651fede3cdd8ff28237d14f6bb1d41f2cb8f3d2141585e3a2ede2d` |
| `rhodes_A#5.wav` | `5fd2951a2a4f65c7655658d7fc01297e0e27ab86c0149594f5775cab0488fa1b` |
| `rhodes_C#2.wav` | `d2871ba71516932091d51a7b8cff0ba3946789cd6129978be8691f6bf72bdff7` |
| `rhodes_C#3.wav` | `82549501587118638c72fa136a54336688e5d5e8850a7901cd9a289f9cf8a8de` |
| `rhodes_C#6.wav` | `c082deaea73339800277b08e4c28150e5e87c7e636235e64bb370fec5e6f3ada` |
| `rhodes_D#5.wav` | `3271b6889f1604eb09dde2dc395cb75ad4e4111a4d8bd0083421541421b1f435` |
| `rhodes_E1.wav` | `1b2c7a3dadaf23ebfa681bf14ee2933983f7487bc8c62587796a5ff152028256` |
| `rhodes_E2.wav` | `9c03ff8383b7c1e027066f862c4b05959a9cca6b6cc545747ce13c47eedbf359` |
| `rhodes_E5.wav` | `9150e1a2ac6d5b148b74965690828b20e0038a7cac742587f2e7bc09a2dc08e3` |
| `rhodes_G#2.wav` | `7fc33a0f36a6168b815ca229b9b85759f1d903a7e423461496baabb44cc76eae` |
| `rhodes_G#5.wav` | `af3a1da6689861828ae079b58e199f2c4f87b966159641983432e824030f67aa` |
