# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`midi-music` is a collection of **original, generative instrumental albums**, each
composed by a different language model and committed as reproducible source. It holds
two kinds of code that meet at the MIDI file:

1. **Composition engines** — per-album **Python** (standard-library only) that emit
   `.mid` files. One engine per album; the album *is* the code plus its rendered MIDI.
2. **ferrosintesis** — a Rust MIDI-to-WAV synthesizer with **zero third-party
   code dependencies**
   (`crates/ferrosintesis/`) that renders those MIDIs to audio. It is voiced for the
   *fable5* (Mike-Oldfield-idiom) albums but plays any GM file as a faithful player.

The pipeline is: `engine.py` → committed `.mid` → **ferrosintesis** → `.wav` →
`ropusenc` → committed `listening/*.opus`. Committed `.mid` (every album) plus
committed `.opus` (most albums — VIGIL, RIVERWAKE and *The Long Turning* ship
MIDI-only) let anyone listen without a toolchain; `.wav` is a disposable
intermediate.

## Layout

`albums/` = **one directory per model** (`fable5/`, `opus4-8/`, `gpt5-5/`,
`gpt5-3-spark/`), each holding one or more albums. An album lives either at the
model-dir root or in a named subfolder. `listening/` holds tagged `.opus` listening
copies grouped by artist and album for drag-and-drop playback.
`crates/ferrosintesis/` is the synth library; `crates/ferrosintesis-cli/` is the
offline WAV renderer. `crates/ferrosintesis-samples-{core,orchestral}/` are the two
default embedded asset crates; their generator and full provenance live under
`tools/ferrosintesis-samples/`. `demos/` holds synth test pieces; `wrk_docs/` holds
design and review docs; `wrk_journals/` is the engineer's log.

## Commands

> **Run every build/render below from a task worktree — never the main clone
> `D:\language\midi-music`.** These commands write into the working tree:
> `render_opus.py` **rewrites committed `listening/*.opus` in place**, `build.py`
> rewrites `.mid` / `album_manifest.json`, and `cargo` emits `.wav` / `target/`.
> Run in the main clone they dirty the sacred trunk-holder (violating
> worktree-first) and block its `git pull --ff-only`. The git guards protect the
> *ref*, not the working tree — nothing stops a Python/cargo run from soiling it.
> "From the repo root" below therefore means **the worktree's root**, not the
> main clone.

### ferrosintesis (Rust) — from the repo root
```
cargo build --release -p ferrosintesis-cli  # target/release/ferrosintesis
cargo test --workspace                     # numeric audio oracles — this box has no ears
cargo test <name>                     # a single test by name
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt
./target/release/ferrosintesis in.mid -o out.wav          # render
./target/release/ferrosintesis in.mid --solo 11 -o s.wav  # one channel (verification stem)
./target/release/ferrosintesis in.mid --no-samples ...    # disable the LA sample layer
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
python render_opus.py                       # render every album's MIDI → listening/*.opus
python render_opus.py --album "Winter Guests"
```
Requires a built `ferrosintesis` CLI (see above) and `ropusenc` on PATH (from the sibling
`ropus` repo). Album metadata (title/artist/genre) lives in `ALBUMS` in `render_opus.py`.

## ferrosintesis architecture

Zero third-party code dependencies; `[profile.release]` uses LTO. The default
`embedded-samples` Cargo feature compiles the two asset crates into the final binary;
`default-features = false` builds the modeled-only synth without downloading them.
Module map (`src/`):

- `midi.rs` — GM file parser → tempo map, events, markers.
- `engine.rs` — the render loop and the **mix**: channel strips (CC7/11/10/64/74/91/93/94),
  hall and cathedral reverbs, chorus + echo buses, piano sympathetic resonance,
  bus-glue compression.
  Bus levels are named constants here.
- `voices.rs` — the instrument **models** (Pluck/Karplus-Strong, Modal, drawbar Organ,
  CathedralOrgan, SawStack, Lead, Wind, Bowed). Instrument voicing constants live at the top.
- `drums.rs` — parametric GM channel-10 percussion.
- `dsp.rs` — filters, oscillators, shared DSP primitives.
- `sampler.rs` — the **LA-synthesis** layer: 202 public-domain PCM attack transients
  (16.68 MiB source, supplied by two default embedded asset crates) crossfaded into
  modeled instrument bodies and sustains.
- `reverb.rs`, `wav.rs` — Freeverb hall plus the cathedral feedback-delay network;
  16-bit PCM writer with TPDF dither.
- `testutil.rs` — pitch (Goertzel), RMS, click-detection helpers for the audio oracles.

**ferrosintesis does not model every GM program**, but as of v0.10 the orchestral middle is
filled: **brass 56–63** and **reeds 64–71** are now modelled voices (v0.9), joining the
orchestra hit 55, strings 48–51 and choir 52–54. A few ranges are still curated fallbacks
(e.g. GM sound-effects 120–127 render as toneless noise). Album engines keep a program
whitelist and verify nothing strays into an unintended range. Read the family/GM-program
table in `crates/ferrosintesis/README.md` before assuming a program will sound right.

**Synth-change policy — controller features are opt-in; timbre improvements are
default-on with a diff-driven asset refresh.** Two regimes:
- **Controller/CC features** (CC1 vibrato/Leslie, CC64/68/74, CC70 vowels, CC2 breath,
  CC0 alt-bank select, RPN, aftertouch…) engage only once a channel *authors* them; a
  channel that never sends one renders exactly as before. That's correct MIDI
  semantics, not conservatism — an unauthored controller must be inert.
- **Instrument/timbre improvements** (better voices, new sample layers, kit upgrades)
  become the **default sound** — committed albums are not frozen in older, worse
  renderings. The obligation is to refresh, not to freeze: re-render and re-commit
  the affected `listening/*.opus` assets in the same task, so the published audio
  never silently lags the synth.

**Either way, run the render-diff inventory** for any voices.rs/engine.rs/drums.rs/
sampler.rs change: build a baseline binary in a throwaway `git worktree add <path> HEAD`,
render every album MIDI in `render_opus.py::ALBUMS` with both binaries, and `cmp`.
It is a **report, not a pass/fail gate**: expected diffs define exactly which
listening assets to refresh; *unexpected* diffs (a brass change altering a piano-only
album, DC on silent channels) are bugs — investigate before committing. For a pure
controller feature, any diff at all is a bug.

ferrosintesis is versioned (`Cargo.toml`, currently 0.14.2); a shipped-code change needs one
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
- **Older `tracks/` shape** (`albums/opus4-8/`, `albums/gpt5-5/`, `albums/gpt5-3-spark/`) — `engine.py` +
  `build.py` + `tracks/NN_title.py`. Described in
  `wrk_docs/2026.06.26 - HLD - repository layout and album conventions.md`.
- **Newer `movements/` shape** (all `albums/fable5/` albums) — adds `conductor.py` (global
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
| `listening/<artist>/<album>/NN - Title.opus` | tagged listening copy, **committed for most albums** (via `render_opus.py`; three long albums ship MIDI-only) |
| `album_manifest.json` | machine-readable metadata (tracks, durations, movement map) |
| `ALBUM.md`, `README.md` | human track notes + regenerate/verify instructions |

`.gitignore` drops `.wav` (reproducible) **except** the files under
`crates/ferrosintesis-samples-{core,orchestral}/samples/` — those 202 WAVs are the
synth's 16.68 MiB attack-transient bank, which is **source, not output**. Never treat
them as regenerable. Commit an album as one atomic bundle (sources + `.mid` + manifest
and docs); render/commit `listening/*.opus` separately.

## Before you start

- Read `lessons_learnt.md` — it holds hard-won, non-obvious gotchas specific to this repo
  (oracle design pitfalls, the mono-collapse pan-Haas interaction, zero-crossing pitch
  counters lying, canaries in golden fixtures, subagent output-format failures on big
  generative tasks). Add a dated one-liner when you learn something durable (cap 20).
- The full worktree-first git / integration / version-bump doctrine is in your
  `~/.claude/CLAUDE.md` and is not repeated here.
