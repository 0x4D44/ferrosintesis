# ferrosintesis-samples-musescore

Embedded **MIT-licensed** instrument-onset samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis), extracted from the
MuseScore "MS Basic" soundfont (MuseScore_General / FluidR3Mono lineage).

Each WAV is a mono 16-bit 44.1 kHz attack transient; the synth plays it as a note's
onset and crossfades into the modeled sustain (LA synthesis). Consumers normally
access this crate through `ferrosintesis`, not directly.

## Contents

| Prefix | GM | Instrument |
|--------|----|-----------|
| `sitar_*` | 104 | Sitar (pluck + jawari buzz onset) |
| `panflute_*` | 75 | Pan flute (breath onset) |
| `bottle_*` | 76 | Blown bottle (breath onset) |
| `shakuhachi_*` | 77 | Shakuhachi (breath onset) |

(Pipes 75/76/77 land here as their unit completes.)

The GM 7 clavinet from the same soundfont ships separately in
`ferrosintesis-samples-clavinet` (it is a full decaying note, not an onset).

## License

**MIT** — attribution (the FluidR3 / MuseScore_General copyright notices) must
travel with the samples; see `NOTICE`. Source pin (commit SHA + SHA-256) and the
regeneration recipe live in `tools/ferrosintesis-samples/README.md`.
