# ferrosintesis-samples-orchestral2

Embedded **CC0 1.0** instrument-onset samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This is the second CC0
onset crate: the original `ferrosintesis-samples-orchestral` is at the crates.io
per-crate size cap, so newer CC0 families land here.

Each non-banjo WAV is a mono 16-bit 44.1 kHz attack transient trimmed by
`tools/ferrosintesis-samples/prepare.py`; the banjo WAVs are extracted by
`tools/ferrosintesis-samples/banjo_extract.py`. The synth plays each WAV as the
onset of a note and crossfades into the modeled sustain (LA synthesis).
Consumers normally access this crate through `ferrosintesis`, not directly.

## Contents & provenance

| Prefix | GM | Source | License |
|--------|----|--------|---------|
| `harp_*` | 46 | [VCSL](https://github.com/sgossner/VCSL) "Concert Harp" | CC0 1.0 |
| `timpani_*` | 47 | VCSL "Timpani 2" (struck) | CC0 1.0 |
| `recorder_*` | 74 | VCSL Baroque recorders (alto + soprano) | CC0 1.0 |
| `ocarina_*` | 79 | VCSL "Ocarina, Typical" | CC0 1.0 |
| `banjo_*` | 105 | Original 5-string bluegrass banjo (open-G gDGBD), close-mic recording by Arthur, 2026-07-23 | CC0 1.0 |

All sources are CC0 1.0 / public-domain dedications — no attribution is legally
required. Full provenance, source pins (commit SHAs / the in-repo `samples/`
recording) and the regeneration recipe live in `tools/ferrosintesis-samples/README.md`.
The banjo REPLACED the earlier CC0 sfzinstruments/ganjo (a 6-string *guitar*-banjo whose
recordings were spectrally dull); its source take is archived at
`samples/banjo/banjo-5string-openG-2026-07-23.opus`.
