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
`ropusenc` → `listening/*.opus`. The committed `.mid` (every album) is the
listenable source of truth; the `.opus` and `.wav` renders are reproducible
**build output** (git-ignored, not committed), regenerated on demand with
`cargo run --release -p render-catalog` (builds the synth, then renders every
album — pure Rust, no Python). Every render
is loudness-normalized to −18 LUFS (BS.1770-4) with a −1 dBTP true-peak limit and
R128 replay-gain tags. There is no committed audio to play directly — you build the
repo to hear it. (History note: the `.opus` files were committed until they had
bloated `.git` past 5.9 GB with re-rendered copies; they were purged and are now
render-on-demand.)

## Layout

`albums/` = **one directory per model** (`fable5/`, `opus4-8/`, `gpt5-5/`,
`gpt5-3-spark/`), each holding one or more albums. An album lives either at the
model-dir root or in a named subfolder. `listening/` holds tagged `.opus` listening
copies grouped by artist and album for drag-and-drop playback — **git-ignored build
output**, produced by `cargo run --release -p render-catalog` (not committed).
`crates/ferrosintesis/` is the synth library; `crates/ferrosintesis-cli/` is the
offline WAV renderer; `crates/render-catalog/` is the catalog renderer (album MIDI →
tagged `.opus`, holding the `ALBUMS` metadata table).
`crates/ferrosintesis-samples-{core,orchestral}/` are the two
default embedded asset crates; their generator and full provenance live under
`tools/ferrosintesis-samples/`. `demos/` holds synth test pieces; `wrk_docs/` holds
design and review docs; `wrk_journals/` is the engineer's log.

## Commands

> **Run every build/render below from a task worktree — never the main clone
> `D:\language\midi-music`.** An album's own `python build.py` (run from an album
> directory) rewrites the **tracked** `.mid` / `album_manifest.json`; run in the main
> clone it dirties the sacred trunk-holder (violating worktree-first) and blocks its
> `git pull --ff-only`. Rendering (`render-catalog`, `cargo`)
> now writes only git-ignored `.opus` / `.wav` / `target/`, so it no longer dirties
> *tracked* state — but it still churns the tree with hundreds of MiB, so keep it in a
> worktree too. The git guards protect the *ref*, not the working tree. "From the repo
> root" below therefore means **the worktree's root**, not the main clone.

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
The `.opus` listening copies are git-ignored build output, regenerated on demand by
`render-catalog` (pure Rust — no Python in the audio pipeline):
```
cargo run --release -p render-catalog                            # render every album
cargo run --release -p render-catalog -- --album "Winter Guests" # render one album
cargo run --release -p render-catalog -- --jobs 4                # limit parallelism
cargo run --release -p render-catalog -- --only-list paths.txt   # surgical refresh
```
It renders each MIDI to a loudness-normalized WAV **in-process** with the ferrosintesis
library, then shells out to `ropusenc` to encode + tag, so it needs a Rust toolchain plus
`ropusenc` on PATH (from the sibling `ropus` repo). Album metadata (title/artist/genre)
lives in the `ALBUMS` table in `crates/render-catalog/src/main.rs`; its synth parameters
are pinned to `ferrosintesis-cli`'s defaults by a parameter-parity test, and its
`ropusenc` argv by goldens captured from the retired `render_opus.py`.

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
- `sampler.rs` — the **LA-synthesis** layer: 218 public-domain PCM recordings
  (17.73 MiB source, supplied by the `-core` and `-orchestral` asset crates; the
  separate `-drumkit` crate adds the 188-file sampled kit) crossfaded into
  modeled instrument bodies and sustains.
- `reverb.rs`, `wav.rs` — Freeverb hall plus the cathedral feedback-delay network;
  16-bit PCM writer with TPDF dither.
- `testutil.rs` — pitch (Goertzel), RMS, click-detection helpers for the audio oracles.

**ferrosintesis does not model every GM program**, but as of v0.10 the orchestral middle is
filled: **brass 56–63** and **reeds 64–71** are now modelled voices (v0.9), joining the
orchestra hit 55, strings 48–51 and choir 52–54. GM sound effects 121–127 are dedicated
voices since 2026.07.14 (sustained seashore/helicopter/applause/breath textures that follow
key hold; telephone/bird/gunshot one-shots); only fret noise 120 remains a toneless
squeak transient. Album engines keep a program
whitelist and verify nothing strays into an unintended range. Read the family/GM-program
table in `crates/ferrosintesis/README.md` before assuming a program will sound right.

**Synth-change policy — controller features are opt-in; timbre improvements are
default-on with a diff-driven asset refresh.** Two regimes:
- **Controller/CC features** (CC1 vibrato/Leslie, CC64/68/74, CC70 vowels, CC2 breath,
  CC0 alt-bank select, RPN, aftertouch…) engage only once a channel *authors* them; a
  channel that never sends one renders exactly as before. That's correct MIDI
  semantics, not conservatism — an unauthored controller must be inert.
- **Instrument/timbre improvements** (better voices, new sample layers, kit upgrades)
  become the **default sound**. Because the `.opus` renders are git-ignored build
  output (produced by `cargo run --release -p render-catalog`), there is no committed
  audio to refresh —
  anyone who renders after your change simply hears the improved synth, and the
  committed album source (the `.mid`) is unaffected.

**The synth is a GENERIC GM player — never cull a feature just because no in-repo album
uses it.** ferrosintesis is *voiced* for the fable5 albums but is a faithful player of **any**
GM file, so "nothing under `albums/` authors this" is **not** evidence that a voice, kit,
controller path or GM program is dead. The selectable channel-10 kits (PC 24 `Synth`,
PC 25 `V1` the original kit, PC 40 `Brush`), GM programs no album happens to reach, and
controller handling are all part of the public instrument — kept for foreign MIDI files and
for future pieces. Judge a feature by whether it is **correct and reachable**, not by an
in-repo usage count; a usage census is a fact about our albums, not about the synth. If you
believe something is genuinely dead, ask Arthur rather than tidying it away.

**Either way, run the render-diff inventory** for any voices.rs/engine.rs/drums.rs/
sampler.rs change: build a baseline binary in a throwaway `git worktree add <path> HEAD`,
render every album MIDI in `render-catalog`'s `ALBUMS` table with both binaries, and `cmp`.
It is a **report, not a pass/fail gate**: expected diffs confirm the change reached
exactly the albums it should; *unexpected* diffs (a brass change altering a piano-only
album, DC on silent channels) are bugs — investigate before committing. For a pure
controller feature, any diff at all is a bug.

ferrosintesis is versioned (`Cargo.toml`, currently 0.17.0); a shipped-code change needs one
version bump per integrated task. The crate is **published to crates.io**, so its public API
carries a semver promise: `Options`/`RealtimeOptions` are sealed (private fields — construct
with `Options::default()` + the `with_*` builders, read with the accessors), and the error
enums plus every data-carrying variant are `#[non_exhaustive]`. Adding a render knob or an
error variant is therefore a minor bump, not a major one — keep it that way. Publish order is
forced by the `=0.1.0` pins: `ferrosintesis-samples-core` → `-orchestral` → `ferrosintesis`.
`ferrosintesis-cli` and `render-catalog` are `publish = false`.

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
| `listening/<artist>/<album>/NN - Title.opus` | tagged listening copy — **git-ignored build output**, produced by `cargo run --release -p render-catalog` (-18 LUFS, -1 dBTP, R128 tags) |
| `album_manifest.json` | machine-readable metadata (tracks, durations, movement map) |
| `ALBUM.md`, `README.md` | human track notes + regenerate/verify instructions |

`.gitignore` drops `.wav` and `.opus` (both reproducible build output) **except** the
WAVs under `crates/ferrosintesis-samples-{core,orchestral}/samples/` — those 218 files
are the synth's 17.73 MiB sample bank, which is **source, not output**. Never
treat them as regenerable. Commit an album as one atomic bundle (sources + `.mid` +
manifest and docs); the `.opus` renders are **not** committed — regenerate them with
`cargo run --release -p render-catalog`.

## Before you start

- Read `lessons_learnt.md` — it holds hard-won, non-obvious gotchas specific to this repo
  (oracle design pitfalls, the mono-collapse pan-Haas interaction, zero-crossing pitch
  counters lying, canaries in golden fixtures, subagent output-format failures on big
  generative tasks). Add a dated one-liner when you learn something durable (cap 20).
- The full worktree-first git / integration / version-bump doctrine is in your
  `~/.claude/CLAUDE.md` and is not repeated here.
