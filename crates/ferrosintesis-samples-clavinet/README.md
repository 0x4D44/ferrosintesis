# ferrosintesis-samples-clavinet

Embedded **MIT-licensed** clavinet samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis) — the default sampled
voice for GM program 7 (clavinet). Eleven baked, pitch-synchronous decaying notes
(sounding G1–G6), extracted from the MuseScore "MS Basic" soundfont.

You normally do not depend on this crate directly; `ferrosintesis` pulls it in under
its default `embedded-samples` feature. With `--no-samples` (or a channel selecting
the CC0 alt bank, `CC0 != 0`), GM7 falls back to ferrosintesis's fully-modeled
Karplus-Strong clavinet and this crate is not used.

- **License:** MIT. Some sibling banks are CC0, while others use MIT or CC BY;
  see the
  [complete embedded-sample licence inventory](https://github.com/0x4D44/ferrosintesis/blob/main/crates/ferrosintesis/README.md#sample-provenance-and-licensing).
  This bank's attribution obligations are in [`NOTICE`](NOTICE).
- **Provenance & regeneration:** [`PROVENANCE.md`](PROVENANCE.md) — pinned source,
  SHA-256, and the SF3-extraction / bake pipeline in
  `tools/ferrosintesis-samples/prepare.py`.
