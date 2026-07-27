# The Remaining

A five-track album by Claude Fable 5 — five elegies for piano, strings,
choir and quiet electronics in the idiom of Max Richter's score for *The
Leftovers*. Concept and track notes live in `ALBUM.md`; the design document
is `wrk_docs/2026.07.18 - HLD - The Remaining album (five elegies).md` at
the repo root.

## Layout

The album uses the **federated movements shape**: `conductor.py` holds the
`Part` class and the five-track registry; each track module
`movements/tNN_<stem>.py` is self-contained — its `Part` grid (movements,
tempo map, meters, key signatures, channels), its movement builders, its
verification config, its structural `oracles()` and its render-side
`audio_checks()`. Shared musical DNA (the ground and its suspension
signature, the vigil theme and its arrival, the departure figure and its
holes, the departed line, the Morse lane, the seating plan) lives in
`material.py`, self-proven by `verify_material()`; recurrences are always
recomputed from there, never re-typed. `COMPOSER-NOTES.md` is the compact
composer digest the album was built with (module contract, emitter
patterns, trip-wires).

## Rebuild and verify (stdlib Python only)

```
python3 build.py                     # rebuild all 5 MIDIs + album_manifest.json
python3 build.py --track N           # rebuild one track
python3 build.py --verify            # every oracle over every track (exit != 0 on failure)
python3 build.py --track N --verify  # one track's oracles (the composing loop)
python3 build.py --track N --check   # in-memory oracles only, no file I/O
```

Seeds are fixed per track (in `conductor.REGISTRY`), so rebuilds are
byte-identical and `--verify` reasons about the same Scores that produced
the committed files.

## Render and analyze (audio oracles)

Requires the repo synth (ferrosintesis v0.21+):

```
cargo build --release -p ferrosintesis-cli      # from the repo root
bash render_all.sh                              # all 5 tracks -> audio/*.wav (parallel)
python3 analyze.py                               # generic + per-track audio oracles
python3 analyze.py --track N                     # one track
```

`audio/` and `*.wav` are disposable intermediates (gitignored). The audio
oracles assert the headline claims on the *rendered* signal — the scored
silences really silent, the post-departure drop to solo piano, the pulse
track's flat energy and dry close violin, the finale's crescendo and its
final-chord decay — because presence in the MIDI is not audibility in the
render.

## Listening copies

From the repo root, with `ropusenc` on PATH:

```
cargo run --release -p render-catalog -- --album "The Remaining"
```

writes tagged `.opus` files to `listening/Claude Fable 5/The Remaining/`.
