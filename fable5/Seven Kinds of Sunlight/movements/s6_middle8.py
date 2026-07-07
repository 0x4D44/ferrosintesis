"""s6_middle8 — "Middle Eight" (beats 328-368, 5/4 as 3+2).

The turn inward.  Ride-and-side-stick groove, long melodic bass, and
the song's second counterpoint pair: the bright lead (gliding between
tones on portamento) against the flute, the two voices trading places
at the half-bar — certified consonant in material.py.  Piano pools
under the sustain pedal; vibes shimmer across the stereo field.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
from engine import n

MODE = m.MODE
T0, T1 = 328.0, 368.0


def build(sc):
    dr.groove_54(sc, T0, 8, energy=1)
    sc.hit(dr.SPLASH, T0, 62, jv=2)

    # bass: long roots with a stepwise approach into each next bar
    for bar in range(8):
        t = T0 + 5.0 * bar
        root = m.M8_GROUND[bar]
        nxt = m.M8_GROUND[(bar + 1) % 8]
        sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, root), t, 2.9, 58,
                jt=2, jv=2)
        sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, root + 4), t + 3.0,
                0.9, 52, jt=2, jv=2)
        sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, nxt + 1), t + 4.0,
                0.9, 50, jt=2, jv=2)

    # the counterpoint pair: gliding lead vs flute
    en.portamento_on(sc, cd.CH_LEAD, T0 + 1.0, time_cc=72)
    en.line(sc, cd.CH_LEAD, T0, n("D4"), MODE, m.m8_lead(), 58,
            vel_end=64, gate=1.0, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_LEAD, [(T0, 45), (T0 + 20.0, 75),
                                   (T1 - 2.0, 50)], step=1.0)
    en.portamento_off(sc, cd.CH_LEAD, T1 - 2.0)
    en.line(sc, cd.CH_FLUTE, T0, n("D4"), MODE, m.m8_flute(), 56,
            vel_end=62, gate=0.95, jt=3, jv=2)
    for bar in (1, 3, 5, 7):
        h0 = T0 + 5.0 * bar
        en.cc_curve(sc, cd.CH_FLUTE, 1, [(h0, 0), (h0 + 2.0, 55),
                                         (h0 + 4.5, 0)], step=0.25)

    # piano pools (CC64 pairs), pad, guitar picking, vibes shimmer
    for k in range(4):
        t = T0 + 10.0 * k
        en.sustain(sc, cd.CH_PIANO, t + 0.5, t + 9.5)
        root = m.M8_GROUND[2 * k]
        for i, step in enumerate((0, 4, 7, 9, 7, 4)):
            sc.note(cd.CH_PIANO, en.pitch(n("D3"), MODE, root + step),
                    t + 0.5 + i * 1.5, 2.0, 46 - (2 if i % 2 else 0),
                    jt=3, jv=2)
    chords = [en.triad(n("D3"), MODE, m.M8_GROUND[bar]) for bar in range(8)]
    en.pad_block(sc, cd.CH_PAD, T0, chords, span=5.0, size=3,
                 lo=n("G2"), hi=n("D4"), vel=42)
    for bar in range(8):
        t = T0 + 5.0 * bar
        root = m.M8_GROUND[bar]
        for i, step in enumerate((0, 4, 2)):
            sc.note(cd.CH_GTR, en.pitch(n("D4"), MODE, root + step),
                    t + 0.5 + i, 0.9, 44, jt=3, jv=3)
    en.autopan(sc, cd.CH_VIBES, T0, T1 - T0 - 2.0, lo=44, hi=104,
               period_beats=20.0, step=0.5)
    for bar in (0, 2, 4, 6):
        t = T0 + 5.0 * bar + 2.0
        root = m.M8_GROUND[bar]
        for i, step in enumerate((7, 4, 0)):
            sc.note(cd.CH_VIBES, en.pitch(n("D5"), MODE, root + step),
                    t + i * 0.5, 2.5, 48, jt=3, jv=3)

    # strings: low roots swelling toward the solo
    for bar in range(8):
        t = T0 + 5.0 * bar
        p = en.pitch(n("D3"), MODE, m.M8_GROUND[bar])
        sc.note(cd.CH_STRINGS, p, t, 4.8, 44, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(T0, 30), (T1 - 2.0, 80)], step=2.0)
