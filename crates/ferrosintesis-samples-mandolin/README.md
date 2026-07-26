# ferrosintesis-samples-mandolin

Embedded **owner-recorded mandolin** pluck onsets for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis) — ten pitch zones spanning G3–E6, in
one dynamic with four ordered round robins per zone, mono 16-bit 44.1 kHz.

General MIDI has **no mandolin program**. GM Level 2, Roland GS and Yamaha XG all place one as a
bank-select variation of the **Steel Guitar**, so this bank is reached at **GM program 25 with
bank-select LSB (CC32) = 96** — the XG cell, alongside the Ukulele already living at nylon
guitar (24) LSB 96. A channel that never sends CC32 plays the ordinary steel guitar, unchanged.

The samples carry the pick attack and the first ~0.9 s; the `Pluck` (Karplus–Strong) model
underneath carries the decay, exactly as the nylon, steel, banjo and sitar banks do.

Recorded by the repository owner (2026) and dedicated **CC0 1.0** (public domain). Zone table,
measured roots, round-robin ordering, recording rationale, processing recipe, and source-cut
checksums are in `PROVENANCE.md`. The full CC0 legal text ships as `LICENSE-CC0`. Consumers
normally reach this crate through `ferrosintesis`.
