# ferrosintesis-samples-orchestral

Compile-time sample payload for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis). This crate embeds
158 mono, 16-bit, 44.1 kHz FLAC recordings (attack transients + looped sustains):

- 24 violin/cello ensemble onsets for the GM 48–49 string sections;
- 56 brass onsets for trumpet, muted trumpet, trombone, tuba, and horn;
- 36 reed onsets for oboe, bassoon, and clarinet;
- 10 harpsichord onsets for the GM 6 voice;
- 7 Spanish classical-guitar plucks for the nylon-guitar voice;
- 8 steel-string acoustic-guitar plucks for the GM 25 voice;
- 17 looped bagpipe recordings (2 drones, 15 chanter takes) for the GM 109 voice.

The onset banks supply the attack of a note, then `ferrosintesis` crossfades
them into each voice's modeled sustain. The 17 bagpipe payloads are the
exception: `LoopVoice` plays each whole file as an endless loop, without a
modeled sustain or onset crossfade. Cargo retrieves this package at build time and
`include_bytes!` places the selected FLAC data in the final binary. There is no
runtime filesystem or network access.

The small public API exists for `ferrosintesis`:

```rust
assert_eq!(ferrosintesis_samples_orchestral::FILE_COUNT, 158);
let flac = ferrosintesis_samples_orchestral::get("trumpet_C3_f.flac").unwrap();
assert_eq!(&flac[..4], b"fLaC");
```

## Provenance and license

The 116 string, brass, and reed source WAVs were trimmed from
[VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE) by Versilian
Studios / sgossner, released under the CC0 1.0 Universal public-domain
dedication. Source downloads are pinned to repository commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`.

Eight VSCO drum overlays (crash, suspended cymbal, kick, snare — two round
robins each) used to ship here. They were superseded by the sampled kit in
`ferrosintesis-samples-drumkit`, no `ferrosintesis` code read them, and they
left this package on 2026-07-26. See `PROVENANCE.md` for where they went.

The seven `nylon_*` source WAVs were trimmed from the
[FreePats Spanish classical guitar](https://freepats.zenvoid.org/Guitar/acoustic-guitar.html)
sound bank, version 2019-06-18, by roberto@zenvoid.org. That set is also
released under CC0 1.0 Universal. The generator pins the versioned
`SpanishClassicalGuitar-SFZ-20190618.7z` archive by SHA-256:

```text
ef2fb7de0cc0ab561c4ebc28494f3fc2962596e4f32f16d6c96b8a385c7c098b
```

The eight `steel_*` source WAVs were trimmed from the `026-Acoustic Guitar (steel)`
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

The ten `harpsi_*` source WAVs are from VCSL's "Harpsichord, Unk" (Harpsi4)
bank, a CC0 plucked keyboard. The source is pinned to VCSL revision
`c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e`; the packaged keys use sounding
pitch names after the bake measures each source's real fundamental.

The two `drone_*` and fifteen `chanter_*` source WAVs are looped sustains (not attack
transients) for the GM 109 bagpipe, trimmed from the
[FreePats Bagpipe](https://freepats.zenvoid.org/Ethnic/Bagpipe/) bank (a G-pipe
recorded by Gilles Sadowski), released under CC0 1.0 with the full legal code
bundled as `cc0.txt`. The generator pins the versioned source WAV archive
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
to mono 16-bit 44.1 kHz PCM, then encodes the packaged samples as FLAC.

The packaged samples and this package are dedicated to the public domain under
CC0-1.0. The full legal text is in `LICENSE-CC0`. Attribution is not required
and is included here with thanks.
