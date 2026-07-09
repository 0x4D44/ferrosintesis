# The Ninth Bell

A single continuous ~5:46 orchestral piece in the **Gabriel Knight: Sins
of the Fathers** title-music idiom — Robert Holmes' dark-cathedral gothic
drama. It grows out of the string-chord gesture from
`demos/orchestral_demo.py` (channel 0) that Arthur asked to build on: the
piece opens with those chords **verbatim**, then compresses one dramatic
spring twice — a build into a hit on the wrong chord, a drop into an eerie
void, and a larger rebuild into the true climax and its second betrayal.

- File: `midi/01 - The Ninth Bell.mid` (5:46)
- Key: A aeolian, 4/4, 101 bars. Eight movements with MIDI markers; timed
  map in `album_manifest.json`; per-movement notes in `ALBUM.md`.
- Design: `wrk_docs/2026.07.07 - HLD - The Ninth Bell.md`
- Listen via [ferrosintesis](../../../crates/ferrosintesis/README.md) **v0.8** or the
  committed `audio/01 - The Ninth Bell.opus`.

## The shape (what Arthur asked for)

> *"It feels like it goes somewhere dramatic and builds and drops —
> something like the intro to Gabriel Knight."*

The dynamic arc, measured on the render (dB RMS per section):

```
  The Veil  Processional  Ascent   ⇣HIT⇣   Void   Rising Tide  ⇡CLIMAX⇡  Embers
   −42.7       −31.4       −25.0    ·····   −60.1     −28.7      −18.5    −47.1
   swell ───── theme ───── build ─▶ slam ─▶ CLIFF ─▶ rebuild ─▶  peak  ─▶ die
```

The void sits **35 dB below** the ascent that precedes it — a genuine
cliff, not a fade — and the climax is the loudest thing in the piece. A
**feint drop** at bar 62 (−11 dB below its neighbour) re-arms the listener
before the real climax lands.

## The nine bells

Eight tubular-bell tolls frame the sections; the ninth — a single tonic A,
the resolution the theme withholds for six minutes — is the piece's final
note. The bell figure is the theme's own rising-sixth cell, inverted.

## Regenerate / verify

```powershell
python build.py            # rebuild the MIDI + album_manifest.json
python build.py --verify   # rebuild in memory, re-parse the .mid, run every oracle
python build.py --check    # in-memory oracles only (no file I/O)
```

`--verify` runs thirteen structural oracles (`verify.py` +
`material.verify_material`), all written **before** the music: intro
fidelity against the demo gesture, a program whitelist (nothing in GM
55–71, which the synth version used for this album could not voice), the
nine-bell ledger, the two scored silences, the build/drop **dynamic-arc
contour**, and pan/bend hygiene. If a change breaks an oracle, fix the
music — never the test.

Render-side (audio) verification of the arc, the reverb-tail silences,
mono compatibility and clicks:

```powershell
python analyze.py "audio/01 - The Ninth Bell.wav"
```

This is original material using Gabriel-Knight-vocabulary gestures; it
quotes no existing piece.
