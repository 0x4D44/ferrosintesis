#!/usr/bin/env python3
"""bass_demo.py — an isolated bass demo, low register, all bass programs.

Answers "deeper, punchier, XG-style": every line sits in a real 4-string
LOW octave (E1=28 .. E2=40, low E is 41 Hz) so you can judge fundamental
weight and punch.  Cycles the bass voices so you can A/B them:
  1  fingered   (GM 33)  — root/fifth/octave groove + hammer-ons (CC68) + slide
  2  picked     (GM 34)  — driving 8ths, brighter plectrum attack
  3  fretless   (GM 35)  — lyrical, with slides (pitch bend) + vibrato "mwah"
  4  slap        (GM 36) — low thumb + popped octaves + ghost notes
  5  synth bass  (GM 39) — the deep punchy XG-style synth voice (sub + sweep)
A minimal kick+hat backbone gives the punch some context.  Bass only,
otherwise — no guitar on top.

Run:  python demos/bass_demo.py   ->  demos/bass_demo.mid
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "fable5" / "The Signal Fire"))
from engine import Score, bend_ramp, vibrato  # noqa: E402

BPM = 92
sc = Score(seed=828)
sc.tempo(0.0, BPM)
sc.timesig(0.0, 4, 4)
sc.channel(3, "bass", program=33, volume=104, pan=64, reverb=14)
sc.channel(9, "drums")

E1, G1, A1, B1, C2, D2, E2 = 28, 31, 33, 35, 36, 38, 40


def kickhat(t0, bars, snare=False):
    for b in range(bars):
        base = t0 + b * 4
        sc.hit(36, base + 0.0, 106); sc.hit(36, base + 1.5, 92); sc.hit(36, base + 2.5, 98)
        for k in range(8):
            sc.hit(42, base + k * 0.5, 62 + (12 if k % 2 == 0 else 0))
        if snare:
            sc.hit(38, base + 1.0, 96); sc.hit(38, base + 3.0, 100)


def groove(root, t0, bars, vel=104, pat=(0, 0, 7, 0, 12, 0, 7, 0)):
    for b in range(bars):
        for k, iv in enumerate(pat):
            sc.note(3, root + iv, t0 + b * 4 + k * 0.5, 0.42,
                    vel + (6 if k % 2 == 0 else 0), jt=2, jv=4)


# 1. FINGERED (0-16): deep groove, a CC68 hammer-on, a slide into the last note
sc.marker(0.0, "1. Fingered (GM 33)")
kickhat(0.0, 4, snare=True)
groove(E1, 0.0, 1); groove(E1, 4.0, 1, pat=(0, 0, 7, 0, 3, 5, 7, 0))
groove(A1, 8.0, 1); groove(G1, 12.0, 1)
sc.cc(3, 68, 127, 6.4)                      # legato: hammer-on / pull-off
sc.note(3, E1, 6.5, 0.25, 96); sc.note(3, G1, 6.75, 0.25, 92); sc.note(3, B1, 7.0, 0.5, 96)
sc.cc(3, 68, 0, 7.6)
bend_ramp(sc, 3, 15.0, 15.5, -2.0, 0.0, steps=10)   # slide up a whole step into the turn
sc.note(3, E1, 15.0, 1.0, 100)

# 2. PICKED (16-32): driving eighths, brighter attack
sc.marker(16.0, "2. Picked (GM 34)")
sc.program(3, 34, 15.99)
kickhat(16.0, 4, snare=True)
for b, root in enumerate([E1, E1, C2, D2]):
    for k in range(8):
        iv = [0, 0, 0, 7, 0, 0, 12, 7][k]
        sc.note(3, root + iv, 16.0 + b * 4 + k * 0.5, 0.4, 100 + (8 if k % 2 == 0 else 0), jt=2, jv=4)

# 3. FRETLESS (32-48): lyrical, slides + vibrato mwah
sc.marker(32.0, "3. Fretless (GM 35)")
sc.program(3, 35, 31.99)
kickhat(32.0, 4)
frl = [(E1, 0.0, 2.0), (G1, 2.0, 1.0), (A1, 3.0, 3.0),
       (C2, 6.0, 1.0), (B1, 7.0, 1.0), (A1, 8.0, 4.0),
       (E1, 12.0, 2.0), (D2, 14.0, 2.0)]
for p, s, d in frl:
    sc.note(3, p, 32.0 + s, d * 0.98, 96, jt=2, jv=3)
bend_ramp(sc, 3, 34.6, 35.0, -2.0, 0.0, steps=12)   # slide up into A1
vibrato(sc, 3, 36.0, 3.0, depth=0.3, cycles_per_beat=1.2, delay=0.5)   # mwah on the held A1
vibrato(sc, 3, 41.0, 3.0, depth=0.35, cycles_per_beat=1.3, delay=0.4)  # mwah on the long A1
bend_ramp(sc, 3, 46.0, 46.5, 0.0, -2.0, steps=10)   # sink into D2
sc.bend(3, 47.9, 0.0)

# 4. SLAP (48-64): low thumb + popped octaves + ghost notes
sc.marker(48.0, "4. Slap (GM 36)")
sc.program(3, 36, 47.99)
kickhat(48.0, 4, snare=True)
for b, root in enumerate([E1, E1, A1, G1]):
    seq = [(root, 100), (root + 24, 112), (root, 40), (root + 7, 96),   # thumb, pop, ghost, thumb
           (root, 100), (root + 19, 108), (root, 40), (root + 12, 100)]
    for k, (p, v) in enumerate(seq):
        sc.note(3, p, 48.0 + b * 4 + k * 0.5, 0.34, v, jt=2, jv=5)

# 5. SYNTH BASS 2 (64-80): the XG-style deep punchy synth voice
sc.marker(64.0, "5. Synth bass GM 39 (deep + punchy, XG-style)")
sc.program(3, 39, 63.99)
kickhat(64.0, 4, snare=True)
for b, root in enumerate([E1, E1, G1, E1]):
    pat = [(0, 110), (0, 96), (12, 104), (0, 96), (0, 108), (10, 100), (12, 104), (7, 98)]
    for k, (iv, v) in enumerate(pat):
        sc.note(3, root + iv, 64.0 + b * 4 + k * 0.5, 0.44, v, jt=1, jv=3)
# a filter-opening accent via velocity + a slide on the last bar
bend_ramp(sc, 3, 78.5, 79.0, -1.0, 0.0, steps=8)

# tag: low E1 landing
sc.note(3, E1, 80.0, 3.0, 108)
sc.hit(36, 80.0, 110); sc.hit(49, 80.0, 96)

out = REPO / "demos" / "bass_demo.mid"
sc.write(out, "hollowsynth bass demo (deep, all programs)",
         "fingered/pick/fretless/slap/synth bass, low register, XG-style intent")
print(f"wrote {out}  ({sc.duration_seconds():.1f}s, last beat {sc.last_beat:.1f})")
