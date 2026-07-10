# midi-music

**Original instrumental albums composed by language models — five AI composers,
sixteen albums, ~7½ hours of music — committed as reproducible source and rendered
through a custom synthesizer.**

Every note here was composed by a frontier language model writing Python that emits
MIDI. Nothing is sampled from, or quotes, any existing recording — each album is
*original* material written in the vocabulary of an idiom (Mike Oldfield, Jean-Michel
Jarre, Hans Zimmer, Enigma, Max Richter…). The generators, the MIDI they produce, and
(for most albums) the rendered audio are committed, so you can listen with no toolchain
— or regenerate everything from source.

## Listen

Most albums ship committed, tagged `.opus` files under `listening/` (for example
`listening/Claude Fable 5/Hollow Hill/`). Drag that tree into an audio player for
the shareable listening copies, reproducible from the committed MIDI plus the synth.
Three long albums (**VIGIL**, **RIVERWAKE**, and **The Long Turning**) ship as MIDI
only; render them to `.opus` with `render_opus.py` (see
[Reproduce & verify](#reproduce--verify)).

## The music

### Claude Fable 5 — `albums/fable5/`
Ten albums voiced for **ferrosintesis** (this repo's synth) — spanning idioms from Mike
Oldfield long-form to Jean-Michel Jarre, Enigma, Gabriel Knight and film score. These
are the albums the synth is specifically tuned for.

- **Hollow Hill** — *Mike Oldfield*, 26:29 · 2 parts. A two-part epic on a 13/8
  additive ostinato in E dorian that returns across both parts and is recast major for
  the finale, with a roll-call of instruments, ambient pools and a false ending.
- **The Signal Fire** — *Mike Oldfield*, 16:54. One continuous movement crossing four
  corners of the Oldfield catalogue; one bass riff in three rhythmic guises and three
  themes over one ground that stack in counterpoint at the finale (machine-verified).
- **Winter Guests** — *Mike Oldfield*, 18:28 · 2 parts. Oldfield idiom with guest
  movements folding in ABBA and the Crash Test Dummies' wordless baritone hum; one
  Guest theme in three verified guises over an E-minor→E-major arc.
- **The Burning Meridian** — *orchestral film score*, 9:37 · 3 tracks. A 12/8 war
  build, a 3/4 elegy with a verified fiddle/flute duet, and a 5/4 battle whose horn
  theme recurs across two grounds and three meters.
- **Heliopause** — *Jean-Michel Jarre / Oxygène*, 8:33 · 2 parts. Filtered sequencer
  cells and portamento leads; Part Two's lead is a verified inversion of Part One's
  theme, and the finale stacks theme, answer and inversion in triple counterpoint.
- **Sub Rosa** — *Enigma*, 7:35. Gregorian-style chant and pentatonic shakuhachi over
  a 124-bpm groove, a melodic synth-bass hook, whispered original-Latin text, and a
  woodblock tapping SUB ROSA in Morse.
- **The Ninth Bell** — *Gabriel Knight (Robert Holmes)*, 5:47. One 13-note theme
  carries a cello lament, music-box ghost and fortissimo bell-peal through two
  build-and-drop arcs; a ninth lone tonic A is the resolution withheld for six minutes.
- **Seven Kinds of Sunlight** — *odd-meter pop-prog song*, 3:55. Through-written across
  7/8, 6/8, 4/4 and 5/4 with a verified three-voice chorus counterpoint and a
  two-semitone key-lift finale.
- **Tuxedo Noir** — *spy jazz / noir*, 3:05. A swung walking vamp, a twang theme
  against horn stabs, a 12/8 velvet middle, a 7/8 chase and a whammy dive.
- **The Iron Tide** — *Hans Zimmer*, 3:33. A long cinematic build from a low-D piano
  pedal through string ostinato and taiko percussion to a full-voice horn theme
  (at `albums/fable5/`).

### Claude Opus 4.8 — `albums/opus4-8/`
- **VIGIL** — *Max Richter / Philip Glass / Howard Shore*, 53:12 · 12 parts. A
  neo-classical song-cycle for piano and chamber strings tracing one arc from grief to
  a resolution in D major, unified by a falling three-note memory motif.
- **RIVERWAKE** — *Mike Oldfield / Amarok*, 59:50 (one unbroken track, in
  `albums/opus4-8/amarok/`).
  Restless acoustic folk-prog across twelve movements that rarely repeat, keeping two
  of *Amarok*'s jokes: a false ending and a hidden Morse-code message.

### GPT-5.5 — `albums/gpt5-5/`
- **Hours After Rain** — *cinematic-minimalist*, 57:56 · 12 tracks. Piano, strings,
  celesta and sparse low percussion tracing an arc through grief, urban tension,
  introspection and quiet, unresolved release.
- **The Long Turning** — *progressive folk-rock / classical collage*, 60:00 (one
  continuous movement of 20 contrasting three-minute chapters for guitars, bass, organ,
  whistle and bells).

### GPT-5.3 Spark — `albums/gpt5-3-spark/`
- **The Spark** — *cinematic-minimalist*, 57:28 · 12 parts. Piano, strings, celesta and
  low percussion as an arc from quiet introspection through urban pressure and grief to
  a cathartic crest and release.

### GPT-5.6 — `albums/gpt5-6/`
- **Atlas of Becoming** — *cinematic / progressive / orchestral collage*, 61:20 ·
  14 tracks. Aquatic spectacle, the contemporary world, biological evolution, linked
  song-form, the GPT lineage, a fast spy-film pursuit, and five freely chosen worlds.
- **The Architecture of Air** — *cathedral organ / cinematic*, 6:52 · one large-form
  piece. The default GM19 organ moves from exposed 32-foot pedal through principals,
  tremulant, wind-chest load, high mixtures, full organ, and a room-only coda.

## How a track is made

```
engine.py  ─▶  .mid  ─▶  ferrosintesis ─▶ .wav ─▶ ropusenc ─▶ listening/*.opus
(Python)      committed   (Rust synth)   scratch    (Opus)       committed
```

- **Composition engines** are per-album Python using only the standard library — no
  third-party dependencies. A fixed RNG seed makes every rebuild byte-identical.
- **Oracle-first composition** is the method, most fully in the Fable 5 albums: a
  `verify.py` encodes the piece's musical requirements as machine-checkable oracles
  (counterpoint consonance, dynamic-arc contours, program whitelists, intro fidelity),
  and the music is *composed to pass them* — `build.py --verify` runs the table. The
  newest albums add an `analyze.py` that re-checks key oracles against the rendered
  audio, because presence in the MIDI is not audibility in the render.
- **[ferrosintesis](crates/ferrosintesis/README.md)** is a Rust MIDI-to-WAV
  synthesizer with zero third-party code dependencies — modeled instruments
  (not a sample library), with a thin
  LA-synthesis layer that crossfades real attack transients into the modeled sustain.
  It is *voiced* for the Fable 5 albums; the other composers' albums are faithful
  General-MIDI renders through the same engine used as a general player.

## Reproduce & verify

```bash
# Regenerate/verify one album (run inside its directory):
python build.py            # rebuild the .mid + manifest
python build.py --verify   # re-parse the written MIDI and run every oracle

# Build the synth CLI:
cargo build --release -p ferrosintesis-cli
cargo test                 # numeric audio oracles — this machine has no ears

# Render every album's MIDI to tagged .opus (from the repo root):
python render_opus.py      # needs a built ferrosintesis CLI + `ropusenc` on PATH
```

Python is standard-library only, so a bare `python3` is enough. `ropusenc` comes from
the sibling `ropus` project.

## Layout

- **`albums/` holds one directory per composing model** (`fable5/`, `opus4-8/`,
  `gpt5-5/`, `gpt5-3-spark/`, `gpt5-6/`); each holds one or more albums, at the model
  directory root or in a named subfolder.
- **An album** bundles its engine (`engine.py`, and for the newer albums
  `conductor.py` / `material.py` / `movements/`), `build.py`, oracles (`verify.py`,
  `analyze.py`), the committed `midi/`, an `album_manifest.json`, and `README.md` /
  `ALBUM.md` track notes.
- **`listening/`** — tagged `.opus` listening copies, grouped by artist and album for
  drag-and-drop playback. An album may supply exact-stem UTF-8 `lyrics/*.txt`
  sidecars; the renderer embeds them as multiline `LYRICS` listening-guide tags.
- **`crates/ferrosintesis/`** — the Rust synth library, with
  **`crates/ferrosintesis-cli/`** for the WAV-rendering binary.
- **`demos/`** — synth test pieces; **`wrk_docs/`** — design & review notes;
  **`wrk_journals/`** — the engineer's log.

See **[CLAUDE.md](CLAUDE.md)** for the architecture and working conventions in depth.

## Originality

Each album is original material written in the vocabulary of its idiom; none quotes or
samples an existing piece. The per-album `README.md` states this for each one.
