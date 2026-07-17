# ferrosintesis-samples-orchestral

Compile-time sample payload for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This crate embeds
147 mono, 16-bit, 44.1 kHz WAV recordings (attack transients + looped sustains):

- 24 violin/cello ensemble onsets for the GM 48–49 string sections;
- 56 brass onsets for trumpet, muted trumpet, trombone, tuba, and horn;
- 36 reed onsets for oboe, bassoon, and clarinet;
- 7 Spanish classical-guitar plucks for the nylon-guitar voice;
- 8 steel-string acoustic-guitar plucks for the GM 25 voice;
- 8 looped bagpipe recordings (2 drones, 6 chanter zones) for the GM 109 voice;
- 8 drum overlays: two round robins each for crash cymbal, suspended cymbal,
  kick, and snare.

`ferrosintesis` uses these recordings for the onset of a note, then crossfades
into its modeled sustain. Cargo retrieves this package at build time and
`include_bytes!` places the selected WAV data in the final binary. There is no
runtime filesystem or network access.

The small public API exists for `ferrosintesis`:

```rust
assert_eq!(ferrosintesis_samples_orchestral::FILE_COUNT, 147);
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

The eight `steel_*` WAVs were trimmed from the `026-Acoustic Guitar (steel)`
instrument of the
[Discord SFZ GM Bank](https://github.com/sfzinstruments/Discord-SFZ-GM-Bank) —
a 2017 Martin HD28 Vintage Series recorded by Jeff Learman, who dedicated it to
the public domain under CC0 in the instrument's own `.sfz` header:

```text
// GM Acoustic Guitar
// 2017 Martin HD28 Vintage Series
// Author: Jeff Learman, for Kinwie's Discord SFZ GM: https://github.com/kinwie/Discord-SFZ-GM-Bank
// License: Creative Commons CC0
```

That header is the dedication, and the bank's README designates the `.sfz` as
the authoritative per-instrument licence location. **The commit pin is
load-bearing, not a convenience:** unlike VSCO 2 CE and FreePats, that
repository is a mixed CC0/CC-BY aggregation with no repo-level `LICENSE`, so
CC0 cannot be inferred repo-wide and only this file's header establishes it.
The generator therefore fetches from a pinned revision and must never track
`master`:

```text
05d5ed8befa042fd9d99a6d159dfc3673d3f8edc
```

The two `drone_*` and six `chanter_*` WAVs are looped sustains (not attack
transients) for the GM 109 bagpipe, trimmed from the
[FreePats Bagpipe](https://freepats.zenvoid.org/Ethnic/Bagpipe/) bank (a G-pipe
recorded by Gilles Sadowski), released under CC0 1.0 with the full legal code
bundled as `cc0.txt`. The generator pins the versioned WAV archive
`Bagpipe-SFZ-20221204.7z` by SHA-256:

```text
6f25f232065ebc51ab9d3b54aaedc8a29e59e454ec31d3f1b4a03b3d04256066
```

The bagpipe path emits a short seamless loop region (the whole file loops via a
modulo wrap at render time) rather than an onset — see `extract_loop` in the
generator.

The repository's
[`tools/ferrosintesis-samples/prepare.py`](https://github.com/0x4D44/ferrosintesis/blob/main/tools/ferrosintesis-samples/prepare.py)
performs onset detection, trimming, fades, peak normalization, and conversion
to mono 16-bit 44.1 kHz WAV.

The packaged WAVs and this package are dedicated to the public domain under
CC0-1.0. The full legal text is in `LICENSE-CC0`. Attribution is not required
and is included here with thanks.
