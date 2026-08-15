# Provenance — ferrosintesis-samples-ccby

## Packaged family inventory

| Family | Files |
|--------|------:|
| `dulcimer_*` | 9 |
| `rhodes_*` | 11 |

Two real recordings from Freesound, each **CC BY 4.0**. The upstream evidence is **retained in
this repository**: each pack's bundled `_readme_and_license.txt` is committed verbatim under
`tools/ferrosintesis-samples/freesound-src/`, so the licence can be audited offline — without a
Freesound account, and without trusting a mutable upstream page (MM-REQ-KILN-00029).

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

## Retained upstream licence manifests

Freesound bundles a `_readme_and_license.txt` in every pack download. Both are committed here
verbatim, unmodified, as the primary licence evidence. They name the pack, the author, and every
sound in the pack by ID and licence — so they settle both *which* licence applies and *which
version* of it, neither of which is recoverable from a sound page that the author can edit.

| Manifest | Pack | Sounds | Licence tally | SHA-256 |
|----------|------|--------|---------------|---------|
| [`_readme_and_license_3957.txt`](licence-evidence/_readme_and_license_3957.txt) | 3957 (Rhodes, tim.kahn) | 53 | 53/53 "Attribution 4.0" | `5b6e87bc35b225215f90d87fc0e92872851befa7a331514040abf8fd2234a099` |
| [`_readme_and_license_19445.txt`](licence-evidence/_readme_and_license_19445.txt) | 19445 (dulcimer, iternetcone) | 15 | 15/15 "Attribution 4.0" | `5de6b40b93943d6b29634aa0069710069aad6e8a07152d71f3e64e7083a2d36a` |

The tallies are counted from the manifests themselves, and they are what license the "no
exceptions" claim above. Note the licence **version**: pack IDs 3957 and 19445 predate CC BY 4.0,
so a 4.0 declaration is not something you could assume from the pack's age — the manifests state
Attribution 4.0 explicitly for every sound, and that is why this crate declares `CC-BY-4.0`.

## Per-sound identity

Each committed source WAV was renamed to its **measured** pitch before it was first committed
(the upstream note labels were up to a semitone low — see the 2026.07.20 journal), which severed
the link back to the individual Freesound sound. That link is restored here by matching each
committed clip against the decoded pack originals: every row below matched at a normalised
cross-correlation of **1.0000**, with the runner-up never above 0.62.

Note the upstream label is not the sounding pitch. `rhodes_A#1.wav` really is sound 65754, whose
pack label is `a1`; the E-natural files are the ones whose labels were already correct.

| Committed source | Freesound sound | Upstream label | Source page |
|------------------|-----------------|----------------|-------------|
| `rhodes_A#1.wav` | 65754 | `a1` | <https://freesound.org/s/65754/> |
| `rhodes_A#5.wav` | 65650 | `a5` | <https://freesound.org/s/65650/> |
| `rhodes_C#2.wav` | 65717 | `c2` | <https://freesound.org/s/65717/> |
| `rhodes_C#3.wav` | 65718 | `c3` | <https://freesound.org/s/65718/> |
| `rhodes_C#6.wav` | 65653 | `c6` | <https://freesound.org/s/65653/> |
| `rhodes_D#5.wav` | 65655 | `d5` | <https://freesound.org/s/65655/> |
| `rhodes_E1.wav` | 65758 | `e1` | <https://freesound.org/s/65758/> |
| `rhodes_E2.wav` | 65725 | `e2` | <https://freesound.org/s/65725/> |
| `rhodes_E5.wav` | 65659 | `e5` | <https://freesound.org/s/65659/> |
| `rhodes_G#2.wav` | 65729 | `g2` | <https://freesound.org/s/65729/> |
| `rhodes_G#5.wav` | 65663 | `g5` | <https://freesound.org/s/65663/> |
| `dulcimer_A4.wav` | 342914 | `a` | <https://freesound.org/s/342914/> |
| `dulcimer_B4.wav` | 342913 | `b` | <https://freesound.org/s/342913/> |
| `dulcimer_C#4.wav` | 342911 | `c` | <https://freesound.org/s/342911/> |
| `dulcimer_C5.wav` | 342919 | `high-c` | <https://freesound.org/s/342919/> |
| `dulcimer_D4.wav` | 342918 | `d` | <https://freesound.org/s/342918/> |
| `dulcimer_D5.wav` | 342921 | `high-d` | <https://freesound.org/s/342921/> |
| `dulcimer_E4.wav` | 342917 | `e` | <https://freesound.org/s/342917/> |
| `dulcimer_F#4.wav` | 342915 | `f` | <https://freesound.org/s/342915/> |
| `dulcimer_G4.wav` | 342920 | `g` | <https://freesound.org/s/342920/> |

The pack originals are **not** committed — they are 53 + 15 sounds against the 20 we use, and the
manifests already identify them. Re-deriving this table needs the packs; auditing the licence
does not.

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

