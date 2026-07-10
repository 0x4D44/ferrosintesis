# ferrosintesis-samples-orchestral

Compile-time sample payload for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This crate embeds
131 mono, 16-bit, 44.1 kHz WAV attack transients:

- 24 violin/cello ensemble onsets for the GM 48–49 string sections;
- 56 brass onsets for trumpet, muted trumpet, trombone, tuba, and horn;
- 36 reed onsets for oboe, bassoon, and clarinet;
- 7 Spanish classical-guitar plucks for the nylon-guitar voice;
- 8 drum overlays: two round robins each for crash cymbal, suspended cymbal,
  kick, and snare.

`ferrosintesis` uses these recordings for the onset of a note, then crossfades
into its modeled sustain. Cargo retrieves this package at build time and
`include_bytes!` places the selected WAV data in the final binary. There is no
runtime filesystem or network access.

The small public API exists for `ferrosintesis`:

```rust
assert_eq!(ferrosintesis_samples_orchestral::FILE_COUNT, 131);
let wav = ferrosintesis_samples_orchestral::get("trumpet_C3_f.wav").unwrap();
assert_eq!(&wav[..4], b"RIFF");
```

## Provenance and license

The 124 string, brass, reed, and drum WAVs were trimmed from
[VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE) by Versilian
Studios / sgossner, released under the CC0 1.0 Universal public-domain
dedication. Source downloads are pinned to repository commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`.

The seven `nylon_*` WAVs were trimmed from the
[FreePats Spanish classical guitar](https://freepats.zenvoid.org/Guitar/acoustic-guitar.html)
sound bank, version 2019-06-18, by roberto@zenvoid.org. That set is also
released under CC0 1.0 Universal. The generator pins the versioned
`SpanishClassicalGuitar-SFZ-20190618.7z` archive by SHA-256:

```text
ef2fb7de0cc0ab561c4ebc28494f3fc2962596e4f32f16d6c96b8a385c7c098b
```

The repository's
[`tools/ferrosintesis-samples/prepare.py`](https://github.com/0x4D44/midi-music/blob/main/tools/ferrosintesis-samples/prepare.py)
performs onset detection, trimming, fades, peak normalization, and conversion
to mono 16-bit 44.1 kHz WAV.

The packaged WAVs and this package are dedicated to the public domain under
CC0-1.0. The full legal text is in `LICENSE-CC0`. Attribution is not required
and is included here with thanks.
