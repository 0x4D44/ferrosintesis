# Lantern Year

A ten-track album by Claude Fable 5 — ten nights at a lighthouse across one
year, each about five minutes long and each in its own idiom. Concept and
track notes live in `ALBUM.md`.

## Layout

The album uses the **federated movements shape**: `conductor.py` holds the
`Part` class and the ten-track registry; each track module
`movements/tNN_<stem>.py` is self-contained — its `Part` grid (movements,
tempo map, meters, key signatures, channels), its movement builders, its
verification config, its structural `oracles()` and its render-side
`audio_checks()`. The shared musical DNA (the BEAM cell, the keeper's HYMN,
the LAMP, their detectors and the album-wide oracles) lives in `material.py`,
self-proven by `verify_material()`; recurrences are always recomputed from
there, never re-typed. `COMPOSER-NOTES.md` is the contract the ten track
composers worked from (module shape, synth palette, trip-wires, the ten
briefs). `engine.py`, `build.py`, `verify.py` and `analyze.py` are the
Slipstream copies, mechanics unchanged.

## Rebuild and verify (stdlib Python only)

```
python3 build.py                     # rebuild all 10 MIDIs + album_manifest.json
python3 build.py --track N           # rebuild one track
python3 build.py --verify            # every oracle over every track (exit != 0 on failure)
python3 build.py --track N --verify  # one track's oracles (the composing loop)
python3 build.py --track N --check   # in-memory oracles only, no file I/O
```

Run bare `build.py` first, then `--verify`: `--verify` never writes the
`.mid`. Seeds are fixed per track (in `conductor.REGISTRY`), so rebuilds are
byte-identical and `--verify` reasons about the same Scores that produced
the committed files.

## Render and analyze (audio oracles)

```
cargo build --release -p ferrosintesis-cli      # from the repo root
bash render_all.sh                              # all 10 tracks -> audio/*.wav (parallel)
python3 analyze.py                              # generic + per-track audio oracles
python3 analyze.py --track N                    # one track
```

`audio/` and `*.wav` are disposable intermediates (gitignored). The audio
oracles assert the headline claims on the *rendered* signal — peaks and
hushes in dB, mono compatibility (≤ 2 dB summed loss), click safety — because
presence in the MIDI is not audibility in the render.

## Listening copies

From the repo root, with `ropusenc` on PATH:

```
cargo run --release -p render-catalog -- --album "Lantern Year"
```

writes tagged `.opus` files to `listening/Claude Fable 5/Lantern Year/`.
