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

(timpani, recorder, ocarina and banjo land here as their units complete.)

All sources are CC0 1.0 / public-domain dedications — no attribution is legally
required. Full provenance, source pins (commit SHAs) and the regeneration recipe
live in `tools/ferrosintesis-samples/README.md`.
