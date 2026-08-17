# ferrosintesis-samples-core

Compile-time sample payload for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This crate embeds 69
mono, 16-bit, 44.1 kHz WAV attack transients:

- 52 upright-piano strikes: nine pitch zones and three dynamics; 25 cells have
  two round robins, while quiet C2 and G2 are explicitly single-take because the
  pinned source has no second recording;
- 12 solo-violin arco onsets: six pitch zones at piano and forte;
- 5 flute onsets across the instrument's range.

`ferrosintesis` uses these recordings for the onset of a note, then crossfades
into its modeled sustain. Cargo retrieves this package at build time and
`include_bytes!` places the selected WAV data in the final binary. There is no
runtime filesystem or network access.

The small public API exists for `ferrosintesis`:

```rust
assert_eq!(ferrosintesis_samples_core::FILE_COUNT, 69);
let wav = ferrosintesis_samples_core::get("flute_A4.wav").unwrap();
assert_eq!(&wav[..4], b"RIFF");
```

`PIANO_SINGLE_TAKE_CELLS` reports the two exceptions. For compatibility,
`get("piano_C2_pp_rr2.wav")` and `get("piano_G2_pp_rr2.wav")` still resolve to
their single takes; they are aliases, not additional embedded files.

## Provenance and license

Every recording in this package was trimmed from
[VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE) by Versilian
Studios / sgossner, released under the CC0 1.0 Universal public-domain
dedication. Source downloads are pinned to repository commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`.

The repository's
[`tools/ferrosintesis-samples/prepare.py`](https://github.com/0x4D44/ferrosintesis/blob/main/tools/ferrosintesis-samples/prepare.py)
performs onset detection, trimming, fades, peak normalization, and conversion
to mono 16-bit 44.1 kHz WAV. The piano transients retain about 1.8 seconds; the
violin and flute transients retain about 0.63 seconds.

The packaged samples and this package are dedicated to the public domain under
CC0-1.0. The full legal text is in `LICENSE-CC0`. Attribution is not required
and is included here with thanks.
