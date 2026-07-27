# Big Weather

A ten-track instrumental rock/pop album by **Claude Fable 5** — builds and
drops as weather fronts; every song a forecast. Track notes live in
`ALBUM.md`; the design doc is
`wrk_docs/2026.07.11 - HLD - Big Weather rockpop album.md` at the repo root.

## Layout

The album uses the federated multi-track shape (the *Through Lines*
convention): `conductor.py` holds the album identity and the track
REGISTRY; each song is a self-contained module `movements/tNN_<stem>.py`
declaring its own section grid (verse / pre-chorus / chorus / middle-8 as
named movements), builders, verification config, and per-track oracles.
`verify.py` adds the album's six song-oracles on top of the generic
checks: duration-weighted section-energy contours (builds and drops as
numbers), late-channel gating (the orchestra arrives as each song builds),
bass melodicity, choir layering, on-target advanced-MIDI feature coverage,
and the wide-voice drum-solo spread checks on the two drum-feature tracks.

## Rebuild and verify

```
python3 build.py                     # rebuild all 10 MIDIs + manifest
python3 build.py --track N           # rebuild one track
python3 build.py --verify            # full structural oracle table
python3 build.py --track N --verify  # one track (the composer's loop)
python3 build.py --track N --check   # in-memory only, safe while composing
```

Seeds are fixed per track, so a rebuild is byte-identical and `--verify`
reasons about the same Scores that produced the committed files.

## Render and analyze (audio oracles)

```
cargo build --release -p ferrosintesis-cli   # from the repo root
bash render_all.sh                           # midi/*.mid -> audio/*.wav
python3 analyze.py                            # audio oracle table
```

`analyze.py` guards against stale renders (a WAV older than its MIDI
fails, not skips), then checks clicks, mono compatibility (<= 2 dB loss),
and each track's own audio oracles (chorus lift, drop re-entry, drum-solo
stereo spread, feature audibility). `audio/` and `*.wav` are gitignored.

## Listening copies

```
python3 render_opus.py --album "Big Weather"   # from the repo root
```

writes tagged listening copies to `listening/Claude Fable 5/Big Weather/`
(requires the built ferrosintesis CLI and `ropusenc` on PATH). Lyric
sidecars under `lyrics/` become the tracks' LYRICS tags.
