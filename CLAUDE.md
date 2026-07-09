# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`midi-music` is a collection of **original, generative instrumental albums**, each
composed by a different language model and committed as reproducible source. It holds
two kinds of code that meet at the MIDI file:

1. **Composition engines** — per-album **Python** (standard-library only) that emit
   `.mid` files. One engine per album; the album *is* the code plus its rendered MIDI.
2. **hollowsynth** — a **zero-dependency Rust** MIDI-to-WAV synthesizer
   (`fable5/hollowsynth/`) that renders those MIDIs to audio. It is voiced for the
   *fable5* (Mike-Oldfield-idiom) albums but plays any GM file as a faithful player.

The pipeline is: `engine.py` → committed `.mid` → **hollowsynth** → `.wav` →
`ropusenc` → committed `.opus`. Committed `.mid` (every album) plus committed `.opus`
(most albums — VIGIL, RIVERWAKE and *The Long Turning* ship MIDI-only) let anyone
listen without a toolchain; `.wav` is a disposable intermediate.

## Layout

Top level = **one directory per model** (`fable5/`, `opus4-8/`, `gpt5-5/`,
`gpt5-3-spark/`), each holding one or more albums. An album lives either at the
model-dir root or in a named subfolder. `demos/` holds synth test pieces; `wrk_docs/`
design + review docs; `wrk_journals/` engineer's log; `tmp_v09_hld/` is scratch design
work for the in-flight hollowsynth v0.9.

## Commands

### hollowsynth (Rust) — from `fable5/hollowsynth/`
```
cargo build --release                 # the render binary (target/release/hollowsynth)
cargo test                            # 94 tests (numeric audio oracles — this box has no ears)
cargo test <name>                     # a single test by name
cargo clippy --all-targets            # fleet gate is -D warnings
cargo fmt
./target/release/hollowsynth in.mid -o out.wav          # render
./target/release/hollowsynth in.mid --solo 11 -o s.wav  # one channel (verification stem)
./target/release/hollowsynth in.mid --no-samples ...    # disable the LA sample layer
```
Run tests with stdin closed (`$null | cargo test …` in PowerShell,
`cargo test … </dev/null` in bash) — the harness otherwise hangs a stdin-reading test.

### Composition engines (Python) — from inside an **album** directory
```
python build.py            # regenerate the .mid (+ album_manifest.json)
python build.py --verify   # rebuild in memory, re-parse the written MIDI, run the oracle table
```
No third-party deps — a bare `python3` is enough. Seeds are fixed, so a rebuild is
byte-identical and `--verify` reasons about the same Score that produced the file.
(`--verify` covers all fable5 + gpt5 albums; VIGIL's builder only rebuilds. Some
fable5 albums also add `--check` for in-memory-only oracles, safe to run while composing.)

### Rendering audio — from the **repo root**
```
python render_opus.py                       # render every album's MIDI → tagged .opus (parallel)
python render_opus.py --album "Winter Guests"
```
Requires a built `hollowsynth` (see above) and `ropusenc` on PATH (from the sibling
`ropus` repo). Album metadata (title/artist/genre) lives in `ALBUMS` in `render_opus.py`.

## hollowsynth architecture

Zero external dependencies; `[profile.release]` uses LTO. Module map (`src/`):

- `midi.rs` — GM file parser → tempo map, events, markers.
- `engine.rs` — the render loop and the **mix**: channel strips (CC7/11/10/64/74/91/93/94),
  hall reverb, chorus + echo buses, piano sympathetic resonance, bus-glue compression.
  Bus levels are named constants here.
- `voices.rs` — the instrument **models** (Pluck/Karplus-Strong, Modal, Organ, SawStack,
  Lead, Wind, Bowed). Instrument voicing constants live at the top.
- `drums.rs` — parametric GM channel-10 percussion.
- `dsp.rs` — filters, oscillators, shared DSP primitives.
- `sampler.rs` — the **LA-synthesis** layer: short public-domain PCM attack transients
  (embedded in the binary) crossfaded into the modeled sustain for piano/fiddle/flute.
- `reverb.rs`, `wav.rs` — Freeverb tank; 16-bit PCM writer with TPDF dither.
- `testutil.rs` — pitch (Goertzel), RMS, click-detection helpers for the audio oracles.

**hollowsynth does not model every GM program**, but as of v0.9 the orchestral middle is
filled: **brass 56–63** and **reeds 64–71** are now modelled voices (v0.9), joining the
orchestra hit 55, strings 48–51 and choir 52–54. A few ranges are still curated fallbacks
(e.g. GM sound-effects 120–127 render as toneless noise). Album engines keep a program
whitelist and verify nothing strays into an unintended range. Read the family/GM-program
table in `fable5/hollowsynth/README.md` before assuming a program will sound right.

**The "authored channel" invariant — new synth features must stay opt-in.** Every added
CC feature (CC1 vibrato/Leslie, CC64/68/74, CC70 vowels, RPN, aftertouch…) engages only
once a channel *authors* it; a channel that never sends it renders exactly as before. This
keeps already-committed albums frozen while the synth grows. **Prove it**: build a baseline
binary in a throwaway `git worktree add <path> HEAD`, render a prior album with both
binaries, and `cmp` for byte-identity. Do this for any voices.rs/engine.rs change.

hollowsynth is versioned (`Cargo.toml`, currently 0.8.2); a shipped-code change needs one
version bump per integrated task.

## Composition-engine architecture

Every album is a self-contained Python bundle that shares one design philosophy but comes
in two structural shapes.

**The shared engine** (`engine.py`, copied per album and locally evolved) is a
standard-library toolkit for long-form MIDI: a `Score` collecting per-channel note/CC/
program events plus a conductor lane (tempo map, time signatures, markers); modal
scale-degree arithmetic (`pitch`, `triad`, `voice_lead`, `line`, `pad_block`, `arp`);
expression/controller helpers (`cc_curve`, `vibrato`, `wah`, `leslie`, `vowel`, `bend_range`,
`portamento_on/off`, `aftertouch`, `morse`); and `write_midi` / `parse_midi`. Times are in
beats (float quarter-notes); humanisation is seeded, so builds are reproducible.

**Oracle-first composition is the core method here.** `verify.py` encodes the piece's
musical requirements as machine-checkable oracles (counterpoint consonance, dynamic-arc
contours, program whitelists, pan discipline, intro-fidelity, bend hygiene), and the music
is *composed to pass them* — write the oracle before the music. `analyze.py` mirrors key
oracles against the **rendered audio** (RMS/pitch), because presence in the MIDI is not
audibility in the render. `build.py --verify` prints a pass/fail oracle table and exits
nonzero on any failure; treat green oracles as the definition of done for an album.

Two shapes:
- **Older `tracks/` shape** (`opus4-8/`, `gpt5-5/`, `gpt5-3-spark/`) — `engine.py` +
  `build.py` + `tracks/NN_title.py`. Described in
  `wrk_docs/2026.06.26 - HLD - repository layout and album conventions.md`.
- **Newer `movements/` shape** (all `fable5/` albums) — adds `conductor.py` (global
  skeleton: channel map, tempo/meter/marker grid), `material.py` (reusable musical
  gestures), `movements/mN_*.py` (one module per movement, each citing the HLD section it
  implements), and `analyze.py` (audio-side oracles).

## Album anatomy (committed artifacts)

| Path | Role |
|------|------|
| `engine.py` (+ `conductor.py` / `material.py` / `movements/`) | composition engine, stdlib-only |
| `build.py` | entry point: rebuild / `--verify` / `--check` |
| `verify.py`, `analyze.py` | structural oracles (MIDI) and audio oracles (render) |
| `midi/NN - Title.mid` | rendered MIDI, **committed**, reproducible |
| `audio/NN - Title.opus` | tagged listening copy, **committed for most albums** (via `render_opus.py`; three long albums ship MIDI-only) |
| `album_manifest.json` | machine-readable metadata (tracks, durations, movement map) |
| `ALBUM.md`, `README.md` | human track notes + regenerate/verify instructions |

`.gitignore` drops `.wav` (reproducible) **except** `fable5/hollowsynth/samples/*.wav` —
those are the synth's attack-transient sample bank, which is **source, not output**. Never
treat them as regenerable. Commit an album as one atomic bundle (sources + `.mid` +
manifest + docs); render/commit `.opus` separately.

## Before you start

- Read `lessons_learnt.md` — it holds hard-won, non-obvious gotchas specific to this repo
  (oracle design pitfalls, the mono-collapse pan-Haas interaction, zero-crossing pitch
  counters lying, canaries in golden fixtures, subagent output-format failures on big
  generative tasks). Add a dated one-liner when you learn something durable (cap 20).
- The full worktree-first git / integration / version-bump doctrine is in your
  `~/.claude/CLAUDE.md` and is not repeated here.
