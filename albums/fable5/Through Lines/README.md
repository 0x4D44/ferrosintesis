# Through Lines

A fifteen-track double album (plus a bonus finale reprise, *Three-Sixty-One*) by
Claude Fable 5. Concept, track notes and the
through-line map live in `ALBUM.md`; the design document is
`wrk_docs/2026.07.09 - HLD - Through Lines double album.md` at the repo root.

## Layout

The album uses the **federated movements shape**: `conductor.py` holds the
`Part` class and the track registry (fifteen plus the bonus); each track module
`movements/tNN_<stem>.py` is self-contained — its `Part` grid (movements,
tempo map, meters, key signatures, channels), its movement builders, its
verification config, its structural `oracles()` and its render-side
`audio_checks()`. Shared musical DNA (the FABLE cell, the bridge chorale, the
trilogy motifs, the ledger theme, the Morse lanes) lives in `material.py`,
self-proven by `verify_material()`; cross-track recurrences are always
recomputed from there, never re-typed.

## Rebuild and verify (stdlib Python only)

```
python build.py                     # rebuild all 16 MIDIs + album_manifest.json
python build.py --track N           # rebuild one track
python build.py --verify            # every oracle over every track (exit != 0 on failure)
python build.py --track N --verify  # one track's oracles (the composing loop)
python build.py --track N --check   # in-memory oracles only, no file I/O
```

Seeds are fixed per track (in `conductor.REGISTRY`), so rebuilds are
byte-identical and `--verify` reasons about the same Scores that produced the
committed files.

## Render and analyze (audio oracles)

Requires the repo synth (ferrosintesis **v0.11+** — this album commissioned
its GM 112-119 voices, gong alt-bank and brush kit):

```
cargo build --release -p ferrosintesis-cli      # from the repo root
bash render_all.sh                              # all 16 tracks -> audio/*.wav (parallel)
python analyze.py                               # generic + per-track audio oracles
python analyze.py --track N                     # one track
```

`audio/` and `*.wav` are disposable intermediates (gitignored). The audio
oracles assert the headline claims on the *rendered* signal — dynamics arcs in
dB, scored silences, mono compatibility (≤ 2 dB summed loss), click safety —
because presence in the MIDI is not audibility in the render.

## Listening copies

From the repo root, with `ropusenc` on PATH:

```
python render_opus.py --album "Through Lines"
```

writes tagged `.opus` files to `listening/Claude Fable 5/Through Lines/`.
