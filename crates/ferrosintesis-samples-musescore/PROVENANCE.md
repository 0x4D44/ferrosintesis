# Provenance - ferrosintesis-samples-musescore

Every recording this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=brasssection,sitar,panflute,bottle,shakuhachi,celesta` from the repository
root.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `brasssection_*` | 10 | Brass section (GM 61) onset + early body | MuseScore "MS Basic" SF3 | MIT |
| `sitar_*` | 8 | Sitar (GM 104) onsets | MuseScore "MS Basic" SF3 | MIT |
| `panflute_*` | 8 | Pan flute (GM 75) onsets | MuseScore "MS Basic" SF3 | MIT |
| `bottle_*` | 1 | Blown bottle (GM 76) onset - retired, superseded by `ferrosintesis-samples-bottle` | MuseScore "MS Basic" SF3 | MIT |
| `shakuhachi_*` | 1 | Shakuhachi (GM 77) onset | MuseScore "MS Basic" SF3 | MIT |
| `celesta_*` | 8 | Celesta (GM 8) onsets | MuseScore "MS Basic" SF3 | MIT |

**Source pin.** MuseScore `MS Basic.sf3`, revision `d307a2bd899f15bf650efc3c2891211af5cb78b5`
(<https://raw.githubusercontent.com/musescore/MuseScore/d307a2bd899f15bf650efc3c2891211af5cb78b5/share/sound/MS%20Basic.sf3>),
SHA-256 `5ea2375e8bd7d8e71def1036978c1621e85b66934169b6a2744b27b9b3c2d99c`.

**Licence.** MIT, **not** CC0 - this crate is deliberately separate from the CC0 banks so
those stay pure CC0. The MIT permission notice and the retained upstream acknowledgement
set (FluidR3 by Frank Wen; FluidR3Mono by Michael Cowgill; MuseScore_General adaptation
by S. Christian Collins; Temple Blocks by Ethan Winer; Drumline Cymbals by Michael
Schorsch) are reproduced in this crate's `NOTICE`, which must travel with any binary
distribution.

The GM 8 celesta was previously absent from this file, the README and the crate
description even though `src/lib.rs` documented it (MM-BUG-KILN-00069 item 1).
