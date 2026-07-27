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

The canonical packaged inventory is [`PROVENANCE.md`](PROVENANCE.md). It lists
every shipped WAV family, file count, instrument, source pin or owner-recorded
source, licence, and regeneration note for this crate.

All sources are CC0 1.0 / public-domain dedications — no attribution is legally
required. The repository tooling and source recordings used to bake the packaged
WAVs live under `tools/ferrosintesis-samples/` and `samples/`, but consumers and
auditors should treat packaged `PROVENANCE.md` as the public inventory authority.
