# amp-lab

Twiddle the driven-guitar amp knobs live, over a looping backing track, to decide
what GM29/GM30 should default to (MM-REQ-KILN-00028 Part B).

```
cd crates/amp-lab
cargo run --release
```

It is **its own workspace**, not a member of the repo's — see the note in
`Cargo.toml`. Build it from this directory; `cargo test --workspace` at the repo
root neither builds nor needs it.

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
  the `engine.py` calls and raw NRPN an album would author.

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
| `assets/backing.mid` | the 8-bar loop, regenerate with `crates/amp-lab/tools/make_backing_loop.py` |

The threading split is the load-bearing part: `RealtimeSynth` buffers `write_byte`
for the next `render_add`, so it must be owned by one thread. Sharing it with a
repainting UI behind a `Mutex` is the standard way to get dropouts, so the UI only
ever pushes into the ring.

## The backing loop

8 bars, 104 bpm, A minor. Rhythm guitar (GM30 main) on ch0, **lead guitar (GM29
lead) on ch1 — the knobs act on this one**, bass on ch2, drums on ch9.
Regenerate with `python crates/amp-lab/tools/make_backing_loop.py` from the repo root.
