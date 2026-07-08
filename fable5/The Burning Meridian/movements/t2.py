"""t2 — *Lanterns on the Water* (A aeolian, 88, 3/4 throughout).

The elegy.  Harp arpeggios are the water; the machine-verified
fiddle/flute duet floats over it, swaps voices, is taken up by the
whole orchestra, and goes out lantern by lantern.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
import percussion as pc
from engine import lerp, n

MODE = m.MODE
BASE = n("A2")                  # A aeolian root base
HARP_LADDER = (0, 4, 7, 9, 7, 4)
TIMP_A = n("A1")


def _harp_bar(sc, t, root, vel):
    for i, step in enumerate(HARP_LADDER):
        sc.note(cd.CH_HARP, en.pitch(BASE, MODE, root + step),
                t + i * 0.5, 0.7, vel - (3 if i % 2 else 0), jt=3, jv=3)


def _harp_bars(sc, t0, bars, vel0, vel1, every=1):
    for bar in range(0, bars, every):
        t = t0 + 3.0 * bar
        root = m.LAMENT_GROUND[bar % 4]
        _harp_bar(sc, t, root, int(lerp(vel0, vel1, bar / max(1, bars - 1))))


def _duet(sc, t0, vel_a, vel_b, swap=False, cello=False):
    cha = cd.CH_FLUTE if swap else cd.CH_FIDDLE
    chb = cd.CH_FIDDLE if swap else cd.CH_FLUTE
    en.line(sc, cha, t0, n("A4"), MODE, m.ELEGY_A, vel_a,
            vel_end=vel_a + 5, gate=1.02, jt=3, jv=2)
    en.line(sc, chb, t0, n("A4"), MODE, m.ELEGY_B, vel_b,
            vel_end=vel_b + 4, gate=0.97, jt=3, jv=2)
    for k in (0.0, 12.0):
        en.cc_curve(sc, cd.CH_FIDDLE, 1,
                    [(t0 + k + 2.0, 0), (t0 + k + 8.0, 65),
                     (t0 + k + 11.5, 0)], step=0.25)
    if cello:
        en.line(sc, cd.CH_CELLO, t0, n("A3"), MODE, m.ELEGY_B, 52,
                gate=0.97, jt=3, jv=2)


def lanterns(sc):
    _harp_bars(sc, 0.0, 12, 44, 54)
    sc.cc(cd.CH_STRINGS, 11, 0, 5.0)
    for t, ps in ((6.0, (n("A2"), n("E3"))), (18.0, (n("A2"), n("C4"))),
                  (27.0, (n("E3"), n("A3")))):
        for i, p in enumerate(ps):
            sc.note(cd.CH_STRINGS, p, t, 9.0, 44 - i * 2, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(5.0, 0), (20.0, 55), (34.0, 40)],
                  step=1.0)
    for i, p in enumerate((n("A2"), n("E3"), n("A3"), n("B3"))):
        sc.note(cd.CH_PAD, p, 0.0, 35.5, 38 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(0.0, 0), (18.0, 60), (34.0, 5)],
                step=0.5)
    # the fiddle lights the first lantern
    sc.cc(cd.CH_FIDDLE, 68, 127, 29.5)
    en.line(sc, cd.CH_FIDDLE, 30.0, n("A4"), MODE,
            [(5, 0, 2.0), (6, 2.0, 1.0), (5, 3.0, 3.0)], 50, gate=1.02,
            jt=3, jv=2)
    sc.cc(cd.CH_FIDDLE, 68, 0, 34.8)
    en.cc_curve(sc, cd.CH_FIDDLE, 1, [(31.0, 0), (34.0, 55), (35.5, 0)],
                step=0.25)


def duet(sc):
    t0 = 36.0
    _harp_bars(sc, t0, 32, 48, 56)
    # ONE legato span for the whole duet section (per-statement
    # toggles collided with the lantern pickup's pedal-up)
    sc.cc(cd.CH_FIDDLE, 68, 127, 35.5)
    sc.cc(cd.CH_FIDDLE, 68, 0, 131.5)
    _duet(sc, 36.0, 58, 52)
    _duet(sc, 60.0, 62, 55)
    _duet(sc, 84.0, 60, 54, swap=True)
    _duet(sc, 108.0, 64, 57, cello=True)
    for k in range(4):                             # piano pools
        t = t0 + 24.0 * k
        en.sustain(sc, cd.CH_PIANO, t + 0.2, t + 22.0)
        for i, deg in enumerate((1, 5, 8, 10)):
            sc.note(cd.CH_PIANO, en.pitch(n("A2"), MODE, deg),
                    t + 1.0 + i * 3.0, 4.0, 44, jt=3, jv=2)
    chords = [en.triad(n("A2"), MODE, m.LAMENT_GROUND[b % 4])
              for b in range(16)]
    en.pad_block(sc, cd.CH_STRINGS, t0 + 48.0, chords, span=3.0, size=3,
                 lo=n("E2"), hi=n("E4"), vel=44, vel_end=52)


def swell(sc):
    t0, bars = 132.0, 28
    _harp_bars(sc, t0, bars, 56, 62)
    # the orchestra takes the duet
    for st, va in ((132.0, 66), (156.0, 72)):
        en.line(sc, cd.CH_STRINGS, st, n("A3"), MODE, m.ELEGY_A, va,
                vel_end=va + 6, gate=1.0, jt=4, jv=2)
        en.line(sc, cd.CH_CHOIR1, st, n("A3"), MODE, m.ELEGY_B, va - 8,
                gate=0.97, jt=4, jv=2)
    en.vowel_curve(sc, cd.CH_CHOIR1, [(130.0, 40), (170.0, 95)], step=4.0)
    # the peak: duet + descant fiddle an octave up + horns underneath
    for st in (180.0, 192.0):
        en.line(sc, cd.CH_STRINGS, st, n("A3"), MODE,
                m.ELEGY_A[:8], 76, gate=1.0, jt=4, jv=2)
        en.line(sc, cd.CH_CHOIR1, st, n("A3"), MODE, m.ELEGY_B[:5],
                68, gate=0.97, jt=4, jv=2)
        en.line(sc, cd.CH_FIDDLE, st, n("A5"), MODE, m.ELEGY_A[:8], 70,
                gate=1.0, jt=3, jv=2)
    for bar in range(16, bars):
        t = t0 + 3.0 * bar
        root = m.LAMENT_GROUND[bar % 4]
        for i, p in enumerate(en.triad(n("A2"), MODE, root)):
            sc.note(cd.CH_HORN1, p, t, 2.9, 54 - i * 2, jt=3, jv=2)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_A, 176.0, 179.5, 36, 70)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_A, 208.0, 214.0, 40, 76)
    sc.hit(pc.CRASH, 180.0, 84, jv=2)
    sc.note(cd.CH_BELL, n("A3"), 180.0, 6.0, 60, jt=1, jv=2)
    sc.note(cd.CH_BELL, n("A3"), 204.0, 6.0, 56, jt=2, jv=2)
    for t in (138.0, 162.0, 186.0):
        en.at_curve(sc, cd.CH_CHOIR1, [(t, 5), (t + 9.0, 80),
                                       (t + 17.0, 10)], step=0.5)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 40.0, 70), (214.0, 10)],
                step=0.5)
    for i, p in enumerate((n("A2"), n("E3"), n("A3"), n("C4"))):
        sc.note(cd.CH_PAD, p, t0, 83.0, 44 - i, jt=3, jv=2)


def ashfall(sc):
    t0 = 216.0
    _harp_bars(sc, t0, 24, 50, 38, every=2)
    sc.cc(cd.CH_FIDDLE, 68, 127, t0 + 3.5)
    en.line(sc, cd.CH_FIDDLE, t0 + 4.0, n("A4"), MODE, m.ELEGY_A[-6:],
            52, vel_end=46, gate=1.05, jt=3, jv=2)
    sc.cc(cd.CH_FIDDLE, 68, 0, t0 + 14.0)
    en.cc_curve(sc, cd.CH_FIDDLE, 1, [(t0 + 6.0, 0), (t0 + 10.0, 55),
                                      (t0 + 13.0, 0)], step=0.25)
    en.line(sc, cd.CH_FLUTE, t0 + 20.0, n("A4"), MODE, m.ELEGY_B[-4:],
            46, vel_end=40, gate=0.95, jt=3, jv=2)
    en.echo_throw(sc, cd.CH_FLUTE, t0 + 20.0, base=10, peak=64,
                  release=3.0)
    for i, p in enumerate((n("A2"), n("E3"), n("A3"))):
        sc.note(cd.CH_PAD, p, t0, 68.0, 40 - i * 2, jt=3, jv=2)
    en.cc_curve(sc, cd.CH_PAD, 74, [(252.0, 95), (282.0, 26)], step=2.0)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (240.0, 45), (280.0, 0)],
                step=0.5)
    en.vowel_curve(sc, cd.CH_CHOIR1, [(t0 + 8.0, 35), (268.0, 5)],
                   step=4.0)
    sc.note(cd.CH_CHOIR1, n("A3"), t0 + 8.0, 44.0, 38, jt=4, jv=2)
    sc.note(cd.CH_CHOIR1, n("E4"), t0 + 8.0, 44.0, 34, jt=4, jv=2)
    en.sustain(sc, cd.CH_PIANO, 255.9, 285.0)
    for i, deg in enumerate((1, 5, 8)):
        sc.note(cd.CH_PIANO, en.pitch(n("A2"), MODE, deg),
                256.0 + i * 4.0, 6.0, 40 - i * 2, jt=3, jv=2)
    sc.note(cd.CH_BELL, n("A3"), 276.0, 10.0, 44, jt=2, jv=2)
    sc.note(cd.CH_STRINGS, n("A2"), 264.0, 22.0, 36, jt=3, jv=2)
    sc.note(cd.CH_STRINGS, n("E3"), 264.0, 22.0, 33, jt=3, jv=2)
