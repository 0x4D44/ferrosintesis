# ferrosintesis-samples-musescore

Embedded **MIT-licensed** instrument-onset samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis), extracted from the
MuseScore "MS Basic" soundfont (MuseScore_General / FluidR3Mono lineage).

Each sample is a mono 16-bit 44.1 kHz attack transient stored as FLAC and returned
by `get` as raw FLAC bytes; the synth plays it as a note's onset and crossfades
into the modeled sustain (LA synthesis). Consumers normally access this crate
through `ferrosintesis`, not directly.

## Lookup keys

`get` accepts these exact, case-sensitive filenames:

- `bottle_C6.flac`
- `brasssection_F2.flac`, `brasssection_C3.flac`, `brasssection_F#3.flac`,
  `brasssection_A#3.flac`, `brasssection_C4.flac`, `brasssection_F4.flac`,
  `brasssection_A4.flac`, `brasssection_C5.flac`, `brasssection_F5.flac`,
  `brasssection_C6.flac`
- `celesta_F#3.flac`, `celesta_C4.flac`, `celesta_F#4.flac`, `celesta_C5.flac`,
  `celesta_F#5.flac`, `celesta_C6.flac`, `celesta_F#6.flac`, `celesta_C7.flac`
- `panflute_C4.flac`, `panflute_C5.flac`, `panflute_C6.flac`, `panflute_C7.flac`,
  `panflute_F#3.flac`, `panflute_F#4.flac`, `panflute_F#5.flac`, `panflute_F#6.flac`
- `shakuhachi_C5.flac`
- `sitar_C4.flac`, `sitar_C5.flac`, `sitar_C6.flac`, `sitar_E3.flac`,
  `sitar_E4.flac`, `sitar_E5.flac`, `sitar_G3.flac`, `sitar_G6.flac`

## Contents

| Prefix | GM | Instrument |
|--------|----|-----------|
| `brasssection_*` | 61 | Brass section (ensemble onset + early body), 10 zones |
| `sitar_*` | 104 | Sitar (pluck + jawari buzz onset) |
| `celesta_*` | 8 | Celesta (struck-bar onset), 8 zones |
| `panflute_*` | 75 | Pan flute (breath onset) |
| `bottle_*` | 76 | Blown bottle (breath onset) |
| `shakuhachi_*` | 77 | Shakuhachi (breath onset) |

The GM 7 clavinet from the same soundfont ships separately in
`ferrosintesis-samples-clavinet` (it is a full decaying note, not an onset).

## License

**MIT** — attribution (the FluidR3 / MuseScore_General copyright notices) must
travel with the samples; see `NOTICE`. Source pin (commit SHA + SHA-256), scoped
inventory, and the regeneration recipe live in this crate's `PROVENANCE.md`.
