#!/usr/bin/env python3
"""guitar_idiom_demo.py — worked example for the guitar idiom helpers
(guitar block two): `strum_seq` (stroke tables with a raked sweep),
`voicing` (playable 6-string chord shapes), and `run(pitches=...)`
(chromatic hammer-on lines over CC68).

  ch0  Steel guitar (GM 25) — a strummed verse: real chord SHAPES
       (E-shape/A-shape barres and open forms via `voicing`) driven by a
       down-down-up-down-up stroke table via `strum_seq`, with muted
       chucks ('x') on the turnaround.
  ch1  Nylon guitar (GM 24) — the same progression fingerpicked (arp),
       then a chromatic hammer-on run via `run(pitches=..., legato=True)`.

The engine import points at The Remaining — the designated seed engine
carrying these helpers (see the 2026.07.18 guitar block two HLD).

Run:  python demos/guitar_idiom_demo.py  ->  demos/guitar_idiom_demo.mid
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "albums" / "fable5" / "The Remaining"))
import engine as E  # noqa: E402
from engine import Score, arp, run, strum_seq, voicing  # noqa: E402

BPM = 96
sc = Score(seed=1207)
sc.tempo(0.0, BPM)
sc.timesig(0.0, 4, 4)

sc.channel(0, "steel", program=25, volume=96, pan=54, reverb=38, chorus=10)
sc.channel(1, "nylon", program=24, volume=92, pan=74, reverb=44)

# A verse progression as PLAYABLE shapes: E  Amaj  C#m(->A-shape)  B7-ish
PROG = [voicing(4, "maj"),          # E major, open E shape
        voicing(9, "maj"),          # A major, open A shape
        voicing(1, "min"),          # C# minor, A-shape barre fret 4
        voicing(11, "7")]           # B7, A-shape barre fret 2

# down-down-up-down-up, long ring on the downbeat (the Big Weather idiom,
# now one table); bar 4 ends in two muted chucks
STROKES = [(0.0, 1.4, 'D', 0), (1.5, 0.9, 'D', -8), (2.5, 0.45, 'U', -12),
           (3.0, 0.9, 'D', -4), (3.5, 0.45, 'U', -10)]
TURN = [(0.0, 1.4, 'D', 0), (1.5, 0.9, 'D', -6), (2.5, 0.45, 'U', -12),
        (3.0, 0.2, 'x', 0), (3.5, 0.2, 'x', 0)]

t = 0.0
for rep in range(2):
    for i, chord in enumerate(PROG):
        table = TURN if (rep == 1 and i == len(PROG) - 1) else STROKES
        strum_seq(sc, 0, chord, t, table, 78, sweep_span=0.10, rake=1.6)
        t += 4.0

# nylon answers: fingerpicked shapes, then a chromatic hammer-on run
t2 = 16.0
for chord in PROG:
    arp(sc, 1, chord[:4], t2, 8, 0.5, 62, pattern="updown")
    t2 += 4.0
# E-minor-ish chromatic climb no scale spells: needs run(pitches=...)
sc.cc(1, 68, 0, t2 - 0.1)
run(sc, 1, t2, 52, "aeolian", [], 0.22, 88, 64,
    legato=True, pitches=[52, 55, 56, 59, 60, 63, 64, 67])

sc.marker(0.0, "guitar idiom demo")
OUT = Path(__file__).with_suffix(".mid")
sc.write(OUT, "guitar idiom demo",
         "strum_seq / voicing / run(pitches=) worked example")
print(f"wrote {OUT}")
