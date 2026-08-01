# amp-lab

Twiddle the driven-guitar amp knobs live, over a looping backing track, to decide
what GM29/GM30 should default to (MM-REQ-KILN-00028 Part B).

```
cd crates/amp-lab
cargo run --release
```

It is a **standalone workspace**, deliberately outside the root workspace because
egui + cpal add roughly 200 crates that no shipped crate needs. Root Cargo commands
and the integration gate therefore do not reach it. When you touch the lab, run its
checks from `crates/amp-lab/`:

```
cargo fmt
cargo clippy --all-targets -- -D warnings
cargo test
```

## What it does

- **Six sliders** — Drive, Tone, Tightness, Body, Presence, Cab Tone — acting on a
  driven guitar while an 8-bar rock loop plays.
- **Program / bank switches**: GM29 vs GM30, main vs lead bank. All four rigs.
- **Solo guitar** to hear it bare, or leave it in the mix. Judge both: bass and
  drums occupy exactly the bands the cabinet knobs move, so a rig judged solo gets
  judged wrong.
- **A/B slots** — store two settings and flip between them. Ears cannot compare
  against a 30-second-old memory; this is the single most useful control here.
- **Copy settings** — the tool's actual output. Puts the rig on the clipboard as
  `Score.cc` / `Score.program` calls against the album engines' real API, with
  `SC`/`CH`/`BEAT` left as placeholders to fill in, plus a raw NRPN summary for
  hand transcription. All six knobs are written, so pasting it *sets* the rig
  rather than nudging whatever the channel already carried.
  `amp::tests::export_snippet_reproduces_the_rig_bytes` reads the snippet back as
  MIDI and requires it to equal the bytes the live audition sends, so this promise
  is checked rather than asserted (MM-BUG-KILN-00077).

## Why it talks MIDI

Every control is emitted as the exact byte sequence a `.mid` would contain — a
knob is `CC99 0x30 / CC98 <idx> / CC6 <val>`, a program switch is `0xCn`. So a
setting found here **reproduces itself exactly** when authored into an album, and
the lab cannot silently drift from the shipped path. It also means the tool needs
no ferrosintesis API of its own.

## Layout

| file | role |
|---|---|
| `src/main.rs` | egui UI, rig state, export |
| `src/audio.rs` | cpal stream; the audio thread owns the synth and sequencer |
| `src/ring.rs` | lock-free SPSC command ring (UI → audio) |
| `src/seq.rs` | minimal SMF reader + frame-accurate loop playback |
| `assets/backing.mid` | the 8-bar loop, regenerate with `python3 tools/make_backing_loop.py` |

The threading split is the load-bearing part: `RealtimeSynth` buffers `write_byte`
for the next `render_add`, so it must be owned by one thread. Sharing it with a
repainting UI behind a `Mutex` is the standard way to get dropouts, so the UI only
ever pushes into the ring.

## The backing loop

8 bars, 104 bpm, A minor. Rhythm guitar (GM30 main) on ch0, **lead guitar (GM29
lead) on ch1 — the knobs act on this one**, bass on ch2, drums on ch9.
Regenerate from `crates/amp-lab/` with `python3 tools/make_backing_loop.py`.
