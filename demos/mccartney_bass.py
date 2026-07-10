#!/usr/bin/env python3
"""mccartney_bass.py — a warm, muffled, melodic bass (Höfner/McCartney intent).

A melodic pop bassline (not root pedals) in a low-mid register, played
three ways so you can A/B the tone.  Each pass is MUFFLED with CC74 (a
resonant lowpass on the channel — the only in-MIDI 'tone knob'), pushing
energy down out of the bright roundwound register toward a flatwound thud:
  pass 1  picked  (GM 34) + CC74~28   — Höfner is played with a pick
  pass 2  fretless(GM 35) + CC74~30   — the darkest, woodiest plucked voice
  pass 3  synth   (GM 39) + CC74~34   — the most sub-heavy voice today
Light Ringo-ish kick/snare/hat for context; bass is forward.

CC74 can only roll highs OFF — it cannot ADD sub.  The real 'more energy in
the low registers' needs a flatwound PRESET change (see the scratch build).

Run:  python demos/mccartney_bass.py  ->  demos/mccartney_bass.mid
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "fable5" / "The Signal Fire"))
from engine import Score, cc_curve  # noqa: E402

BPM = 104
sc = Score(seed=1964)
sc.tempo(0.0, BPM)
sc.timesig(0.0, 4, 4)
sc.channel(3, "bass", program=34, volume=104, pan=64, reverb=12)
sc.channel(9, "drums")

# A melodic McCartney-style line in D major, low-mid register (D1=26..A2=45).
# (pitch, start_beat, dur) — 8 bars (32 beats).
D1, E1, Fs1, G1, A1, B1, Cs2, D2, E2, Fs2, A2 = 26, 28, 30, 31, 33, 35, 37, 38, 40, 42, 45
LINE = [
    (D1, 0.0, 1.0), (A1, 1.0, 0.5), (D2, 1.5, 0.5), (Fs2, 2.0, 1.0), (A1, 3.0, 1.0),   # I
    (B1, 4.0, 1.0), (Fs1, 5.0, 0.5), (B1, 5.5, 0.5), (D2, 6.0, 1.0), (Cs2, 7.0, 1.0),  # vi
    (G1, 8.0, 1.0), (D2, 9.0, 0.5), (B1, 9.5, 0.5), (G1, 10.0, 1.0), (A1, 11.0, 1.0),  # IV
    (A1, 12.0, 1.0), (E2, 13.0, 0.5), (Cs2, 13.5, 0.5), (A1, 14.0, 1.0), (G1, 15.0, 1.0),  # V
    (D1, 16.0, 1.0), (A1, 17.0, 0.5), (D2, 17.5, 0.5), (Fs2, 18.0, 1.0), (E2, 19.0, 1.0),
    (B1, 20.0, 1.0), (D2, 21.0, 0.5), (Fs2, 21.5, 0.5), (A2, 22.0, 1.5), (Fs2, 23.5, 0.5),
    (G1, 24.0, 1.0), (Fs1, 25.0, 1.0), (E1, 26.0, 1.0), (D1, 27.0, 1.0),
    (A1, 28.0, 1.0), (Cs2, 29.0, 0.5), (E2, 29.5, 0.5), (A1, 30.0, 1.0), (A1, 31.0, 1.0),
]


def beat(t0, bars):
    for b in range(bars):
        base = t0 + b * 4
        sc.hit(36, base + 0.0, 100); sc.hit(36, base + 2.5, 92)
        sc.hit(38, base + 1.0, 92); sc.hit(38, base + 3.0, 96)
        for k in range(8):
            sc.hit(42, base + k * 0.5, 54 + (10 if k % 2 == 0 else 0))


passes = [(34, 28, 0.0), (35, 30, 32.0), (39, 34, 64.0)]  # (program, cc74, t0_beats)
labels = {34: "picked", 35: "fretless", 39: "synth"}
for prog, cc74, t0 in passes:
    sc.marker(t0, f"{labels[prog]} (GM {prog}) muffled CC74={cc74}")
    sc.program(3, prog, max(0.0, t0 - 0.02))
    sc.cc(3, 74, cc74, max(0.0, t0 - 0.01))     # muffle: resonant LP ~600-750 Hz
    beat(t0, 8)
    for p, s, d in LINE:
        sc.note(3, p, t0 + s, d * 0.9, 100, jt=2, jv=4)

END = 96.0
sc.cc(3, 74, 30, END - 0.01)
sc.note(3, 26, END, 3.0, 104)      # low D1 landing
sc.hit(36, END, 108)

out = REPO / "demos" / "mccartney_bass.mid"
sc.write(out, "hollowsynth McCartney-style muffled bass",
         "melodic line, 3 voices, CC74-muffled; picked/fretless/synth")
print(f"wrote {out}  ({sc.duration_seconds():.1f}s, last beat {sc.last_beat:.1f})")
