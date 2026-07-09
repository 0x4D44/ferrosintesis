"""percussion.py — the orchestral percussion engine of *The Burning
Meridian*: taiko-style tom patterns, military snare, cymbal swells,
timpani figures (ch12 is PITCHED timpani, program 47 — it takes real
roots, not GM percussion notes).
"""

from __future__ import annotations

import engine as en
from engine import lerp

K, SN = 36, 38
TOM_LO, TOM_MID, TOM_HI = 41, 43, 45
CRASH, CRASH2, RIDE, SPLASH = 49, 57, 51, 55


def taiko(sc: en.Score, t0: float, bars: int, bar_beats: float,
          energy: int = 1) -> None:
    """The war floor.  energy 1: kick pulses; 2: + toms answering;
    3: + military snare stream and tom 16th pairs."""
    base = 62 + 10 * energy
    for bar in range(bars):
        t = t0 + bar_beats * bar
        sc.hit(K, t, base + 8)
        sc.hit(K, t + bar_beats * 0.5, base - 6)
        if energy >= 2:
            sc.hit(TOM_LO, t + 1.0, base - 4, jt=2)
            sc.hit(TOM_LO, t + 1.5, base - 12, jt=2)
            sc.hit(TOM_MID, t + bar_beats - 1.0, base - 8, jt=2)
            if bar % 2 == 1:
                sc.hit(TOM_HI, t + bar_beats - 0.5, base - 10, jt=2)
        if energy >= 3:
            b = 0.0
            while b < bar_beats - 1e-9:
                v = base - (16 if b % 1.0 == 0.0 else 30)
                sc.hit(SN, t + b, v, jt=1, jv=3)
                b += 0.25
            sc.hit(TOM_LO, t + 2.0, base, jt=1)
            sc.hit(TOM_LO, t + 2.25, base - 10, jt=1)


def snare_build(sc, t0, t1, v0, v1, step=0.25):
    b = t0
    while b < t1 - 1e-9:
        sc.hit(SN, b, int(lerp(v0, v1, (b - t0) / (t1 - t0))), jt=2, jv=3)
        b += step


def cymbal_swell(sc, t0, t1, v0=30, v1=70):
    """Suspended-cymbal crescendo: quiet ride strokes densifying."""
    b = t0
    while b < t1 - 1e-9:
        x = (b - t0) / (t1 - t0)
        sc.hit(RIDE, b, int(lerp(v0, v1, x)), jt=2, jv=3)
        b += lerp(0.5, 0.25, x)
    sc.hit(CRASH, t1, v1 + 24, jv=2)


def timp_hit(sc, ch, pitch, beat, vel, ring=2.0):
    sc.note(ch, pitch, beat, ring, vel, jt=2, jv=3)


def timp_roll(sc, ch, pitch, t0, t1, v0, v1, step=0.125):
    b = t0
    while b < t1 - 1e-9:
        sc.note(ch, pitch, b, step * 1.5,
                int(lerp(v0, v1, (b - t0) / (t1 - t0))), jt=1, jv=3)
        b += step
