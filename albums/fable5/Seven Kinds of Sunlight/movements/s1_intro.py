"""s1_intro — "Intro" (beats 0-32, 4/4, D).

The riff (COUNTER_A) alone with its filter opening, the glockenspiel
picking out its strong slots, then the band falls in at 16: groove,
driving bass, pad swell, clean guitar stabs, and a piano octave pickup
into the 7/8 verse.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
from engine import lerp, n

MODE = m.MODE
T0, T1 = 0.0, 32.0


def build(sc):
    ca = m.counter_a()

    # the riff, filter opening across the whole intro
    sc.cc(cd.CH_ARP, 74, 25, 0.0)
    en.cc_curve(sc, cd.CH_ARP, 74, [(0.0, 25), (30.0, 95)], step=2.0)
    for deg, s, dur in ca:
        v = int(lerp(56, 68, s / 32.0)) + (6 if s % 2.0 == 0.0 else 0)
        sc.note(cd.CH_ARP, en.pitch(n("D4"), MODE, deg), s, dur * 0.9, v,
                jt=2, jv=3)
    for deg, s, dur in ca:
        if s >= 8.0 and s % 2.0 == 0.0:
            sc.note(cd.CH_GLOCK, en.pitch(n("D5"), MODE, deg), s, dur,
                    54, jt=2, jv=3)

    # drums: hat whisper, a cascade fill, then the groove
    b = 8.0
    while b < 14.0:
        sc.hit(dr.HH, b, 36 + int(4 * (b - 8.0)), jt=2, jv=3)
        b += 0.25
    dr.fill(sc, 14.0, 2.0, "cascade", vel=78)
    sc.hit(dr.CRASH, 16.0, 88, jv=2)
    dr.groove_44(sc, 16.0, 4, energy=2, fill_every=4)

    # bass + guitar from the drop
    for bar in range(4):
        t = 16.0 + 4.0 * bar
        root = m.CHORUS_GROUND[bar % 8]
        for deg, s, dur in m.chorus_bass(root):
            sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, deg), t + s,
                    dur * 0.92, 76 + (4 if s == 0.0 else 0), jt=1, jv=2)
        p = en.pitch(n("D3"), MODE, root)
        for beat in (0.5, 1.5, 2.5, 3.5):
            sc.note(cd.CH_GTR, p, t + beat, 0.35, 58, jt=2, jv=3)
            sc.note(cd.CH_GTR, p + 7, t + beat, 0.35, 50, jt=2, jv=3)

    # pad swell under the drop; piano octave pickup into the verse
    chords = [en.triad(n("D3"), MODE, m.CHORUS_GROUND[bar % 8])
              for bar in range(4)]
    en.pad_block(sc, cd.CH_PAD, 16.0, chords, span=4.0, size=4,
                 lo=n("G2"), hi=n("G4"), vel=46)
    en.at_curve(sc, cd.CH_PAD, [(16.0, 0), (24.0, 75), (31.0, 10)],
                step=0.5)
    for i, beat in enumerate((28.0, 29.0, 30.0, 31.0)):
        p = en.pitch(n("D4"), MODE, (1, 5, 6, 8)[i])
        sc.note(cd.CH_PIANO, p, beat, 0.9, 58 + 2 * i, jt=2)
        sc.note(cd.CH_PIANO, p + 12, beat, 0.9, 52 + 2 * i, jt=2)
