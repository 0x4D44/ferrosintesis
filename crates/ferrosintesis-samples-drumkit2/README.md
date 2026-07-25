# ferrosintesis-samples-drumkit2

The **accent-cymbal** half of the sampled drum kit for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis) — crash, sizzle crash, splash and
an 18" china, mono 16-bit 44.1 kHz, from two CC0 1.0 sources.

This is a **packaging split, not a musical one.** The kit was one crate until it packaged at
15.8 MiB, over the crates.io 10 MiB per-crate limit. Cymbals ring for seconds where drums
ring for fractions of one, so these four banks held about half the bytes; moving exactly
them splits the kit into two balanced ~10.5 MB halves with no change to the audio. A render
against the split crates is byte-identical to one made before it.

The ride, ride bell and hi-hats are cymbals too and stayed in
[`ferrosintesis-samples-drumkit`](https://crates.io/crates/ferrosintesis-samples-drumkit) —
the seam was cut on file size, not on instrument taxonomy. Don't read the crate boundary as
a statement about the kit.

The [`Bank`] descriptor type lives in the core crate and is shared, so a consumer holds one
`&'static Bank` and never has to know which half embedded the bytes; each bank carries a
`BankSource` pointing at its own crate's inventory. `ferrosintesis` depends on both halves
and routes GM channel-10 keys across them transparently — GM 49/57 crash, 52 china, 55
splash land here.

Everything is **CC0 1.0** (public domain): Virtuosity Drums for the crash, sizzle and
splash; Karoryfer Big Rusty Drums for the china. Both pinned by commit SHA, with the
velocity/round-robin maps parsed from the source SFZ files rather than guessed — see
`PROVENANCE.md`. No attribution required. Consumers normally reach this crate through
`ferrosintesis`.

[`Bank`]: https://docs.rs/ferrosintesis-samples-drumkit/latest/ferrosintesis_samples_drumkit/struct.Bank.html
