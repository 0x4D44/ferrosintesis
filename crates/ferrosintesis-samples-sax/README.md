# ferrosintesis-samples-sax

Embedded **CC BY 4.0** saxophone samples for [`ferrosintesis`](../ferrosintesis) —
the LA sample layer for the GM 64-67 saxophones (soprano, alto, tenor, baritone).

74 mono 16-bit 44.1 kHz WAVs (per sax: ~9-10 pitch zones × soft/loud), embedded via
`include_bytes!`. Source recordings are the **MTG "good-sounds" solo-saxophone**
dataset (Universitat Pompeu Fabra), packaged as the "MTG Solo Saxophones" SFZ by
kinwie — see [`NOTICE`](NOTICE) for the required attribution and
[`PROVENANCE.md`](PROVENANCE.md) for the full source, licence, and processing chain.

This crate is **CC BY 4.0**, not CC0 — it lives in its own package so the
`ferrosintesis-samples-core` bank stays pure CC0. `ferrosintesis` pulls it in behind
the default `embedded-samples` feature; a `--no-default-features` build renders the
saxophones from the modeled reed voice alone and does not link this crate.

Public API: `get(name: &str) -> Option<&'static [u8]>` and `FILE_COUNT`.

Regenerate with `python tools/ferrosintesis-samples/prepare.py --sax-only` (needs
`ffmpeg`).
