# ferrosintesis-cli

Command-line MIDI-to-WAV renderer for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis) — a General MIDI
synthesizer with no SoundFont, no runtime asset loading, and no third-party code
dependencies.

The binary is called `ferrosintesis` (this crate exists because the library of that
name has no `[[bin]]`).

```
cargo install ferrosintesis-cli
ferrosintesis song.mid -o song.wav
```

Rendering is offline and deterministic: same input, same build, same bytes. There is
no realtime device access and no network or filesystem lookup for instruments — the
sample banks are compiled in.

## Usage

```
ferrosintesis <input.mid> [-o out.wav] [--rate N] [--wet X] [--delay MS] [--tail S]
                          [--no-samples] [--solo CH[,CH...]] [--lufs LUFS]
                          [--tp-ceiling dBTP] [--peak-normalize] [-q]
```

| Flag | Meaning |
|---|---|
| `-o <out.wav>` | Output path (default: the input with a `.wav` extension). |
| `--rate N` | Sample rate in Hz. |
| `--wet X` | Reverb send, 0.0–1.0. |
| `--delay MS` | Echo time; the default is derived from the file's tempo. |
| `--tail S` | Seconds of reverb tail rendered past the last note-off. |
| `--no-samples` | Disable the sampled layer and render the modelled voices only. |
| `--solo CH[,CH...]` | Render only these **0-based** channels — the usual way to check one instrument in isolation. |
| `--lufs LUFS` | Loudness target (default −18 LUFS, BS.1770-4). |
| `--tp-ceiling dBTP` | True-peak ceiling (default −1 dBTP). |
| `--peak-normalize` | Use legacy per-track peak normalization (−1 dBFS) instead of loudness normalization. |
| `-q` | Quiet; suppress progress output. |

By default the render is loudness-normalized to −18 LUFS with a −1 dBTP true-peak
limit. `--peak-normalize` selects the older per-track behaviour.

## Building without the embedded samples

The default build compiles in the sample banks. To build the modelled-only synth:

```
cargo install ferrosintesis-cli --no-default-features
```

That is a genuinely different instrument for some GM programs, not merely a smaller
one — see the library's README for which programs have a sampled layer.

## License

MIT OR Apache-2.0, at your option. The embedded audio shipped by the library's asset
crates carries its own terms; see the library's `NOTICE`.
