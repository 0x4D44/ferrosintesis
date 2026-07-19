# The Causeway

A ten-track, two-act album by Claude Fable 5 (~55:35) — crossings between a
tidal island (late-ABBA ice, Enigma/Delerium weather) and a mainland
(McCartney songcraft, Oldfield patience). Act One: the themes converge
6-4-3-2-0 semitones until they finally sound together at dawn. Act Two: the
tide returns but the voices never part again — everything new grows from
the fusion phrase, its retrograde assembles across the act (the road home,
always stopping short), and the finale sails out on the full road walked
backward, the island's theme at last in the major, ten tolls into the sea.
Concept and track notes live in `ALBUM.md`; the design documents are
`wrk_docs/2026.07.18 - HLD - The Causeway album (five crossings).md` and
`wrk_docs/2026.07.19 - HLD - The Causeway act two (five more crossings).md`
at the repo root.

## Layout

The album uses the **federated movements shape**: `conductor.py` holds the
`Part` class and the five-track registry; each track module
`movements/tNN_<stem>.py` is self-contained — its `Part` grid (movements,
tempo map, meters, key signatures, channels), its movement builders, its
verification config, its structural `oracles()` and its render-side
`audio_checks()`. Shared musical DNA (the two shore themes and the fusion
phrase, the convergence table, the hook ledger, the morse tide-table, the
tide-breath tempo generator, the shore pans, the tolls, the vowel clock,
the cadence law) lives in `material.py`, self-proven by `verify_material()`
— including round-trips of the transposition/stretch-invariant statement
searcher and its no-false-positive claims; recurrences are always
recomputed from there, never re-typed. `COMPOSER-NOTES.md` is the compact
composer digest the album was built with (module contract, album laws,
emitter patterns, trip-wires).

## Rebuild and verify (stdlib Python only)

```
python build.py                     # rebuild all 10 MIDIs + album_manifest.json
python build.py --track N           # rebuild one track
python build.py --verify            # every oracle over every track (exit != 0 on failure)
python build.py --track N --verify  # one track's oracles (the composing loop)
python build.py --track N --check   # in-memory oracles only, no file I/O
```

Seeds are fixed per track (in `conductor.REGISTRY`), so rebuilds are
byte-identical and `--verify` reasons about the same Scores that produced
the committed files.

## Render and analyze (audio oracles)

Requires the repo synth (ferrosintesis v0.21+):

```
cargo build --release -p ferrosintesis-cli      # from the repo root
bash render_all.sh                              # all 10 tracks -> audio/*.wav (parallel)
python analyze.py                               # generic + per-track audio oracles
python analyze.py --track N                     # one track
```

`audio/` and `*.wav` are disposable intermediates (gitignored). The audio
oracles assert the headline claims on the *rendered* signal — the far-shore
horn genuinely wetter and farther than the island, the ferry's accelerando
audible in onset energy, the ice section's density against the candle's
rubato, the gale the loudest window on its track and the eye the quietest,
the finale's crest and the ten tolls ringing into the sea wash — because
presence in the MIDI is not audibility in the render. Generic-check
calibrations are documented in the modules: T2 carries a diagnosed
`MAX_SAMPLE_STEP = 26000` (percussive funk attacks, not clicks), T8 its own
diagnosed cap for the storm's transients.

## Listening copies

From the repo root, with `ropusenc` on PATH:

```
cargo run --release -p render-catalog -- --album "The Causeway"
```

writes tagged `.opus` files to `listening/Claude Fable 5/The Causeway/`.
