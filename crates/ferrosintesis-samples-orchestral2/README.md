# ferrosintesis-samples-orchestral2

Embedded **CC0 1.0** instrument-onset samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This is the second CC0
onset crate: the original `ferrosintesis-samples-orchestral` is at the crates.io
per-crate size cap, so newer CC0 families land here.

Each WAV is a mono 16-bit 44.1 kHz attack transient trimmed by
`tools/ferrosintesis-samples/prepare.py`; the synth plays it as the onset of a note
and crossfades into the modeled sustain (LA synthesis). Consumers normally access
this crate through `ferrosintesis`, not directly.

## Contents & provenance

| Prefix | GM | Source | License |
|--------|----|--------|---------|
| `harp_*` | 46 | [VCSL](https://github.com/sgossner/VCSL) "Concert Harp" | CC0 1.0 |
| `timpani_*` | 47 | VCSL "Timpani 2" (struck) | CC0 1.0 |
| `recorder_*` | 74 | VCSL Baroque recorders (alto + soprano) | CC0 1.0 |
| `ocarina_*` | 79 | VCSL "Ocarina, Typical" | CC0 1.0 |
| `banjo_*` | 105 | [sfzinstruments/ganjo](https://github.com/sfzinstruments/ganjo) 6-string guitar-banjo | CC0 1.0 |

All sources are CC0 1.0 / public-domain dedications — no attribution is legally
required. Full provenance, source pins (commit SHAs) and the regeneration recipe
live in `tools/ferrosintesis-samples/README.md`.
