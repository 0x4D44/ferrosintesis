"""s3_chorus1 — "Chorus 1" + "Turnaround" (beats 112-184, 4/4, D).

The hook at full voice over counter A (pulse synth + glock) and
counter B (strings) — the three-voice counterpoint certified in
material.py — with the driving bass, overdriven power 5ths, and a
rotating fill every fourth bar.  Two bars of the riff turn the song
around into verse 2.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
import parts
from engine import n

MODE = m.MODE


def build(sc):
    parts.chorus(sc, 112.0, semis=0, energy=2, statements=2,
                 descant=False, vocalise=False, organ=False, vibes=False,
                 leslie=False, autopan=False)

    # the turnaround: the riff, two bars, drums leaning forward
    t = 176.0
    sc.hit(dr.CRASH, t, 92, jv=2)                  # land the chorus fill
    ca = [e for e in m.counter_a() if e[1] < 8.0]
    for deg, s, dur in ca:
        sc.note(cd.CH_ARP, en.pitch(n("D4"), MODE, deg), t + s, dur * 0.9,
                66 + (6 if s % 2.0 == 0.0 else 0), jt=2, jv=3)
        if s % 2.0 == 0.0:
            sc.note(cd.CH_GLOCK, en.pitch(n("D5"), MODE, deg), t + s, dur,
                    58, jt=2, jv=3)
    for bar in range(2):
        tb = t + 4.0 * bar
        root = m.CHORUS_GROUND[bar]
        for deg, s, dur in m.chorus_bass(root):
            sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, deg), tb + s,
                    dur * 0.92, 80, jt=1, jv=2)
        for k, beat in enumerate((0.0, 1.0, 2.0, 2.75, 3.5)):
            sc.hit(dr.K, tb + beat, 86 - 6 * (k % 2))
        sc.hit(dr.SN, tb + 1.0, 88)
        sc.hit(dr.SN, tb + 3.0, 88)
        for s in range(8):
            sc.hit(dr.HH, tb + s * 0.5, 62 if s % 2 == 0 else 46, jt=2)
    dr.fill(sc, t + 6.0, 2.0, "kick16", vel=90)
