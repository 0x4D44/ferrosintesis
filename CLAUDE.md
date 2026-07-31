# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`midi-music` is a collection of **generative instrumental albums**, produced by
language models and committed as reproducible source. It holds
two kinds of code that meet at the MIDI file:

1. **Composition engines** — per-album **Python** (standard-library only, except
   `albums/opus4-8/`, which needs `mido` — see its `requirements.txt`) that emit
   `.mid` files. One engine per album; the album *is* the code plus its rendered MIDI.
2. **ferrosintesis** — a Rust MIDI-to-WAV synthesizer with no third-party Rust
   code dependencies (`crates/ferrosintesis/`) that renders those MIDIs to
   audio. Default builds also embed first-party asset crates containing recorded
   material under separate licences. It accepts GM files beyond the catalog but
   does not claim universal conformance or reference-module timbre.

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
`tools/ferrosintesis-samples/`. `samples/` (repo root) is the store of **our own
instrument recordings** — the performance masters we own outright, kept as Opus
plus the pre-cut per-zone sources the bake consumes; it is **source, not output**,
and distinct from the baked banks inside the asset crates (see `samples/README.md`
for the per-instrument convention). Store bulky take masters as 160 kbps Opus; decoded
roots re-slice within 0.75 cents. Any text evidence pinned by SHA-256 must carry
`-text` in `.gitattributes`, and its hash must come from the committed tree rather
than a filtered working copy. `demos/` holds synth test pieces; `wrk_docs/`
holds design and review docs; `wrk_journals/` is the engineer's log.

## Commands

> **Run every build/render below from a task worktree — never the main clone**
> (`D:\language\ferrosintesis` on the Windows boxes, `~/language/ferrosintesis`
> elsewhere). An album's own `python3 build.py` (run from an album
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
python3 build.py            # regenerate the .mid (+ album_manifest.json)
python3 build.py --verify   # rebuild in memory, re-parse the written MIDI, run the oracle table
```
`python3`, not `python`: macOS and most Debian/WSL hosts ship only the suffixed name,
and the fleet's Windows boxes carry both.

No third-party deps — a bare `python3` is enough — **except `albums/opus4-8/`**, whose
`engine.py` writes MIDI through `mido`; install it with
`python3 -m pip install -r requirements.txt` from that album directory. It is the only
album in the repo that needs anything off-stdlib. Seeds are fixed, so a rebuild is
byte-identical and `--verify` reasons about the same Score that produced the file.
(`--verify` covers all fable5 + gpt5 albums; VIGIL's builder only rebuilds. Some
fable5 albums also add `--check` for in-memory-only oracles, safe to run while composing.)

**Always run bare `python3 build.py` FIRST, then `--verify`.** Neither `--verify` nor
`--track N --verify` writes the `.mid` — they run the oracles on the in-memory Score and
re-parse the *existing* file, so after editing a movement they report green on music the
committed MIDI does not contain. The order is: edit → `build.py` (writes) → `--verify` →
render → analyze; confirm with `cmp` on the `.mid` when it matters.

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

No third-party Rust code dependencies; `[profile.release]` uses LTO. The default
`embedded-samples` Cargo feature compiles the first-party asset crates into the
final binary; `default-features = false` builds the modeled-only synth without
downloading them.
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
- `sampler.rs` — the **LA-synthesis** layer: public-domain / permissively
  licensed PCM recordings (supplied by the first-party `ferrosintesis-samples-*`
  asset crates — onset banks, sustain loops, whole-voice instruments, and the
  sampled drum kit) crossfaded into modeled instrument bodies and sustains. The
  per-crate inventory lives in `tools/ferrosintesis-samples/README.md` — trust
  it, not counts quoted here. `LaVoice` velocity layers encode timbre, not level;
  its `vel_amp` law owns loudness.
- `reverb.rs`, `wav.rs` — Freeverb hall plus the cathedral feedback-delay network;
  16-bit PCM writer with TPDF dither.
- `testutil.rs` — pitch (Goertzel), RMS, click-detection helpers for the audio oracles.

**ferrosintesis routes every GM melodic program number, but many programs share a
family engine and support is not a GM-conformance claim.** As of v0.10 the
orchestral middle is filled: **brass 56–63** and **reeds 64–71** are now
modelled voices (v0.9), joining the
orchestra hit 55, strings 48–51 and choir 52–54. GM sound effects 121–127 are dedicated
voices since 2026.07.14 (sustained seashore/helicopter/applause/breath textures that follow
key hold; telephone/bird/gunshot one-shots); fret noise 120 plays a sampled finger-slide
round-robin by default since 2026.07.24 (owner-recorded Eastman E1D, CC0; the toneless
squeak burst is now the `--no-samples` fallback). Album engines keep a program
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

**The synth accepts GM files beyond the repository catalog — never cull a feature
just because no in-repo album uses it.** Compatibility beyond the catalog does
not imply universal GM conformance or reference-module timbre, but "nothing under
`albums/` authors this" is **not** evidence that a voice, kit, controller path or
GM program is dead. The selectable channel-10 kits (PC 24 `Synth`,
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

Three things make that inventory lie, and each has already cost a session — so do an event
census of your own change FIRST and read the inventory as *confirmation* of it. **The baseline
must be the commit you rebased ONTO**, not a fresh `origin/main` build: in this multi-agent repo
local `origin/main` drifts mid-session under concurrent fetch, so a newer-tip baseline reports
the trunk delta as false contamination — rebase onto the current tip, `git worktree add BASELINE
<that commit>`, and re-check `git rev-parse origin/main` right before building. **Check the
baseline binary's mtime**: a build wrapped in a bad path never runs cargo, and a stale binary
left by an earlier session reports the whole catalogue as contamination. **`ALBUMS` covers
`demos/`**, so a catalogue-wide diff is never "albums only". And `tools/render-diff/render_diff.py`
classifies by touched GM program / drum key, so a non-voice change (a send or
controller-semantics fix) run with no `--program`/`--key` flags reports **every** moved track as
contamination. Explain the NON-diffs too — a file carrying the changed pattern that did *not*
move usually pins down exactly why.

ferrosintesis is versioned (`crates/ferrosintesis/Cargo.toml` holds the current
number — trust it, not versions quoted in docs). This is a **release-only** workspace:
ordinary integrations do not bump versions; a deliberate release task does. The
`ferrosintesis` `0.0.0` crates.io package is a code-free name-reservation stub; real
library releases start at `0.21.56`. Its public API is designed for the semver promise it carries:
`Options`/`RealtimeOptions` are sealed (private fields — construct
with `Options::default()` + the `with_*` builders, read with the accessors), and the error
enums plus every data-carrying variant are `#[non_exhaustive]`. Adding a render knob or an
error variant is therefore a minor bump, not a major one — keep it that way. Publish order is
forced by the `=0.1.0` pins, and there are **25 sample crates**, not two: publish the 24
independent ones in any order, then `-drumkit2` (the only crate that depends on another,
`-drumkit`), then `ferrosintesis`, and finally `ferrosintesis-cli`. Derive the order from
the manifests rather than trusting a list here — that is what this sentence got wrong before.
The CLI ships because the library has no `[[bin]]`: `cargo install ferrosintesis` installs
nothing, `cargo install ferrosintesis-cli` installs the `ferrosintesis` renderer.
`render-catalog` and `amp-lab` remain `publish = false`.

Every crate declares **`rust-version = "1.87"`** — that declaration is what turns clippy's
`incompatible_msrv` lint on, so keep it. An MSRV is only real once a toolchain at that
version has compiled it: prove it with `cargo +1.87 check --workspace`, not by grepping for
the newest std API. No `--exclude` is needed any more: `amp-lab` (the dev-only egui GUI,
`publish = false`, whose `image` dep declares `rust-version = 1.88`) left the workspace on
2026.07.26 and is now its own workspace root, like `fuzz/`. Every shipped crate compiles on
1.87.

That move is load-bearing for more than the MSRV. **Cargo resolves the ENTIRE workspace
graph before it honours `-p` or `--exclude`**, so while `amp-lab` was a member its ~200-crate
registry tree was a hard prerequisite of every build here — on a box without crates.io even
`cargo build --offline -p ferrosintesis-cli` died on `no matching package named 'eframe'`.
`default-members` does **not** fix that (it selects what to *build*, not what to *resolve*;
measured both ways). With it excised, the root workspace's dependency closure is 100%
first-party path crates — zero `source =` lines in `Cargo.lock` — which is what lets a fresh
clone build the synth and render the whole catalogue with **no network at all** (samples are
`include_bytes!`, and there is no `build.rs` anywhere). Keep it that way: adding a registry
dependency to any shipped crate forfeits the offline build. The cost is that the root
`cargo build --release`, `fmt --all`, and the integration gate no longer reach `amp-lab`, so
run its checks from inside `crates/amp-lab/` when you touch it — or after changing the
realtime API it rides.

**Keep every dependency on ONE line** — a multi-line inline table is
invalid TOML 1.0, and cargo 1.87 refuses the manifest outright where newer cargo accepts it.
(That rule is now enforced by `sampler`-adjacent oracle `manifest.rs`; it used to be only a
comment, and the MSRV was quietly broken for ten days — MM-BUG-KILN-00067.)

### Hand-maintained lists are the recurring defect here — derive them

Three separate lists drifted the same way, and in each case the *reported* bug was the
newest missing entry rather than the gap: the licensing guide named 5 of 10
attribution-bearing sample banks (KILN-00060), `sampler::prewarm()` reached 24 of 80 banks
(KILN-00059), and per-crate provenance tables had fallen behind their own `samples/`
directories (KILN-00069). Each list grew one entry per feature change, and nobody re-read
the whole.

**So when a bug reports "X is missing from list L", enumerate all of L before fixing.** The
reported item is evidence the list is unmaintained, not a spec of the work.

Three oracles now derive these sets instead of trusting a list, and are the pattern to copy:

- `crates/ferrosintesis/src/licensing.rs` — derives the attribution-bearing banks from the
  `embedded-samples` feature list plus each bank's own `license` field, then requires the
  README table, the parent `NOTICE`, and each crate's packaged `NOTICE` to cover them. It
  reads the feature list as *text* rather than via `cfg!(feature = …)`, so it still asserts
  under `--no-default-features`.
- `crates/ferrosintesis/src/manifest.rs` — scans every workspace manifest for inline tables
  that TOML 1.0 forbids. A *text* check on purpose: the fleet's current toolchain parses
  the broken form happily, so no build can catch it.
- `crates/ferrosintesis/src/sampler.rs` — `prewarm_leaves_no_bank_uninitialized` counts
  bank initialisations through the `bank!` macro and proves none happen after `prewarm()`;
  `every_public_bank_accessor_is_exercised` source-scans so a new accessor cannot land
  outside that sweep. **Two oracles, because one is not enough** — without the second, a
  new bank silently shrinks what the first covers while it keeps passing.

The shared trick: assert against something *derived from the source*, never against a
second hand-written list. A guard that is itself hand-maintained inherits the defect.

**But a derived oracle is only as good as its enumeration predicate, and the predicate
is itself an assumption.** All three above were written on 2026.07.24 and all three were
holed the same day by an adversarial review that tried to *defeat* them rather than
confirm them:

- the licensing oracles assert `contains(crate_name)`, so they pass on a README and
  NOTICE gutted to a bare list of crate names — mentioned is not credited (KILN-00071);
- `manifest.rs` models basic strings but not TOML literal strings, so its five self-tests
  all used `"` and never exercised `'` (KILN-00072);
- the prewarm scan keys off `pub fn *_bank`, which misses private bank fns, public fns
  not named `*_bank`, and caches not built by `bank!` at all — four realtime caches sit
  outside it (KILN-00073).

So: **write the adversarial document that *should* fail your oracle, and check that it
does.** "Derived from the source" is not a guarantee — `pub fn *_bank` was a
hand-maintained assumption wearing a source-scan's clothing. The cheapest way to find
this is a fresh-context reviewer briefed to refute rather than confirm; that is what
caught all three.

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

For album-scale composition, run composers serially and feed each a compact pattern
digest. Parallel composer fan-outs exceed the shared work window before they land
durable tracks.

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
| `engine.py` (+ `conductor.py` / `material.py` / `movements/`) | composition engine, stdlib-only (`opus4-8` excepted: needs `mido`) |
| `build.py` | entry point: rebuild / `--verify` / `--check` |
| `verify.py`, `analyze.py` | structural oracles (MIDI) and audio oracles (render) |
| `midi/NN - Title.mid` | rendered MIDI, **committed**, reproducible |
| `listening/<artist>/<album>/NN - Title.opus` | tagged listening copy — **git-ignored build output**, produced by `cargo run --release -p render-catalog` (-18 LUFS, -1 dBTP, R128 tags) |
| `album_manifest.json` | machine-readable metadata (tracks, durations, movement map) |
| `ALBUM.md`, `README.md` | human track notes + regenerate/verify instructions |

`.gitignore` drops `.wav` and `.opus` (both reproducible build output) **except** the
WAVs under `crates/ferrosintesis-samples-*/samples/` — the synth's embedded sample bank,
which is **source, not output** — and everything under the repo-root `samples/` store,
which holds our own first-party instrument recordings and their per-zone bake sources.
Never treat either as regenerable: the masters are performances that cannot be re-derived.
A **new** sample crate's WAVs stay ignored until you add its own
`!crates/<crate>/samples/*.wav` line — otherwise `git add <crate>` commits the crate
*without* its samples and it fails to build from a clean checkout; confirm with
`git ls-files <crate>/samples` after committing. Commit an album as one atomic bundle (sources + `.mid` +
manifest and docs); the `.opus` renders are **not** committed — regenerate them with
`cargo run --release -p render-catalog`.

## Before you start

- Read `lessons_learnt.md` — it holds hard-won, non-obvious gotchas specific to this repo
  (oracle design pitfalls, the mono-collapse pan-Haas interaction, zero-crossing pitch
  counters lying, canaries in golden fixtures, subagent output-format failures on big
  generative tasks). Add a dated one-liner when you learn something durable (cap 20).
- The full worktree-first git / integration / version-bump doctrine is in your
  `~/.claude/CLAUDE.md` and is not repeated here.
