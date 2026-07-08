"""t1 — *The Muster* (D aeolian, 132; 12/8 from beat 32).

A long gathering: pedal embers, a 12/8 low-string ostinato that never
stops climbing, and the horn theme — stretched to fit the compound
bars (x1.5: its 4/4 downbeats land exactly on the 12/8 bar lines, so
the material oracle's chord-tone proof carries over).
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
import percussion as pc
from engine import lerp, n

MODE = m.MODE
BASE = n("D2")                  # low-string ostinato root base
HORN_BASE = n("D3")
TIMP_D = n("D2")


def _fold(root: int) -> int:
    return root - 7 if root >= 5 else root


def _stretch(theme, factor):
    return [(d, s * factor, dur * factor) for d, s, dur in theme]


HORN_15 = _stretch(m.HORN_THEME, 1.5)          # 24 beats = 4 bars of 12/8


def _horns(sc, t0, vel, theme=None, octave=0):
    theme = HORN_15 if theme is None else theme
    en.line(sc, cd.CH_HORN1, t0, HORN_BASE + 12 * octave, MODE, theme,
            vel, vel_end=vel + 5, gate=0.98, jt=3, jv=2)
    en.line(sc, cd.CH_HORN2, t0, HORN_BASE + 12 + 12 * octave, MODE,
            theme, vel - 10, vel_end=vel - 5, gate=0.98, jt=3, jv=2)


def _ostinato_bars(sc, t0, bars, vel0, vel1):
    for bar in range(bars):
        t = t0 + 6.0 * bar
        root = _fold(m.MUSTER_GROUND[bar % 4])
        vel = int(lerp(vel0, vel1, bar / max(1, bars - 1)))
        for deg, s, dur in m.ostinato(root):
            sc.note(cd.CH_BASSSTR, en.pitch(BASE, MODE, deg), t + s,
                    dur * 0.95, vel + (5 if s == 0.0 else 0), jt=2, jv=3)


def embers(sc):
    en.sustain(sc, cd.CH_PIANO, 0.1, 30.0)
    for t, v in ((0.0, 52), (8.0, 54), (16.0, 58), (24.0, 62)):
        sc.note(cd.CH_PIANO, n("D1"), t, 7.5, v, jt=2, jv=2)
        sc.note(cd.CH_PIANO, n("D2"), t, 7.5, v - 6, jt=2, jv=2)
    for i, p in enumerate((n("D2"), n("A2"), n("D3"), n("F3"))):
        sc.note(cd.CH_PAD, p, 0.0, 31.5, 42 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(0.0, 0), (16.0, 70), (30.0, 10)],
                step=0.5)
    en.vowel(sc, cd.CH_CHOIR1, 0, 7.0)
    sc.note(cd.CH_CHOIR1, n("D3"), 8.0, 22.0, 46, jt=4, jv=2)
    sc.note(cd.CH_CHOIR1, n("A3"), 16.0, 14.0, 44, jt=4, jv=2)
    en.at_curve(sc, cd.CH_CHOIR1, [(8.0, 0), (20.0, 65), (30.0, 5)],
                step=0.5)
    sc.note(cd.CH_CELLO, n("D2"), 12.0, 18.0, 48, jt=3, jv=2)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, 24.0, 31.5, 30, 74)
    pc.snare_build(sc, 28.0, 31.9, 26, 70)


def the_ostinato(sc):
    t0, bars = 32.0, 24
    sc.hit(pc.CRASH, t0, 88, jv=2)
    _ostinato_bars(sc, t0, bars, 58, 76)
    for bar in range(bars):
        t = t0 + 6.0 * bar
        root = _fold(m.MUSTER_GROUND[bar % 4])
        pc.timp_hit(sc, cd.CH_TIMP, en.pitch(TIMP_D, MODE, root), t,
                    int(lerp(58, 80, bar / 23.0)))
        if bar >= 8:
            pc.timp_hit(sc, cd.CH_TIMP, en.pitch(TIMP_D, MODE, root),
                        t + 3.0, 54)
    pc.taiko(sc, t0, 8, 6.0, energy=1)
    pc.taiko(sc, t0 + 48.0, 8, 6.0, energy=2)
    pc.taiko(sc, t0 + 96.0, 8, 6.0, energy=3)
    # horn fragments answer across the hill
    frag = _stretch(m.HORN_THEME[:5], 1.5)
    for st, v in ((56.0, 56), (80.0, 62), (104.0, 68), (128.0, 72)):
        _horns(sc, st, v, theme=frag)
        en.echo_throw(sc, cd.CH_HORN1, st, base=12, peak=60, release=2.0)
    # cello counter-line rising every 8 bars; strings swell above
    for k, st in enumerate((44.0, 92.0, 140.0)):
        en.run(sc, cd.CH_CELLO, st, n("D3"), MODE,
               [1, 2, 3, 4, 5, 6, 7, 8], 0.75, 50 + 6 * k, 62 + 6 * k,
               legato=True)
    chords = [en.triad(n("D3"), MODE, m.MUSTER_GROUND[b % 4])
              for b in range(12)]
    en.pad_block(sc, cd.CH_STRINGS, t0 + 72.0, chords, span=6.0, size=3,
                 lo=n("A2"), hi=n("A4"), vel=52, vel_end=66)
    en.expr_curve(sc, cd.CH_STRINGS, [(104.0, 30), (174.0, 88)], step=2.0)
    en.vowel_curve(sc, cd.CH_CHOIR1, [(104.0, 5), (170.0, 60)], step=4.0)
    for t in range(104, 176, 24):
        sc.note(cd.CH_CHOIR1, n("D3"), float(t), 23.0, 48, jt=4, jv=2)
        sc.note(cd.CH_CHOIR1, n("A3"), float(t), 23.0, 44, jt=4, jv=2)
        en.at_curve(sc, cd.CH_CHOIR1, [(t, 0), (t + 12.0, 70),
                                       (t + 23.0, 10)], step=0.5)
    for t in (128.0, 152.0):
        sc.note(cd.CH_GLOCK, n("D6"), t, 2.0, 52, jt=3, jv=3)
    pc.cymbal_swell(sc, 164.0, 176.0, 26, 66)
    pc.snare_build(sc, 170.0, 175.9, 40, 86)


def the_call(sc):
    t0, bars = 176.0, 30
    sc.hit(pc.CRASH, t0, 100, jv=2)
    sc.note(cd.CH_BELL, n("D4"), t0, 6.0, 66, jt=0, jv=2)
    _ostinato_bars(sc, t0, bars, 72, 82)
    pc.taiko(sc, t0, bars, 6.0, energy=3)
    for bar in range(bars):
        t = t0 + 6.0 * bar
        root = _fold(m.MUSTER_GROUND[bar % 4])
        pc.timp_hit(sc, cd.CH_TIMP, en.pitch(TIMP_D, MODE, root), t, 84)
    en.fine_tune(sc, cd.CH_HORN2, 6.0, 195.0)     # fatten the section
    # three statements, each 4 bars (24 beats), each bigger
    _horns(sc, 200.0, 74)
    _horns(sc, 248.0, 80)
    en.vowel(sc, cd.CH_CHOIR1, 95, 246.0)
    en.line(sc, cd.CH_CHOIR1, 248.0, n("D4"), MODE, HORN_15, 66,
            vel_end=72, gate=0.97, jt=4, jv=2)
    _horns(sc, 296.0, 84)
    en.line(sc, cd.CH_CHOIR1, 296.0, n("D4"), MODE, HORN_15, 72,
            gate=0.97, jt=4, jv=2)
    desc = _stretch(m.descant(m.MUSTER_GROUND), 1.5)
    en.line(sc, cd.CH_FIDDLE, 296.0, n("D4"), MODE, desc, 70,
            vel_end=76, gate=0.96, jt=3, jv=2)
    en.line(sc, cd.CH_FLUTE, 296.0, n("D5"), MODE, desc, 64,
            gate=0.95, jt=3, jv=2)
    en.line(sc, cd.CH_CHOIR2, 296.0, n("D4"), MODE, desc, 60,
            gate=0.97, jt=4, jv=2)
    en.vowel(sc, cd.CH_CHOIR2, 90, 294.0)
    for deg, s, dur in HORN_15:
        sc.note(cd.CH_GLOCK, en.pitch(n("D5"), MODE, deg), 296.0 + s,
                dur * 0.7, 56, jt=3, jv=3)
    for t in (200.0, 248.0, 296.0):
        en.at_curve(sc, cd.CH_CHOIR1, [(t, 10), (t + 12.0, 85),
                                       (t + 23.0, 15)], step=0.5)
    chords = [en.triad(n("D3"), MODE, m.MUSTER_GROUND[b % 4])
              for b in range(bars)]
    en.pad_block(sc, cd.CH_STRINGS, t0, chords, span=6.0, size=4,
                 lo=n("A2"), hi=n("A4"), vel=62, vel_end=72)
    en.pad_block(sc, cd.CH_PAD, t0, chords, span=6.0, size=3,
                 lo=n("D3"), hi=n("D5"), vel=50)
    # apotheosis: the last phrase again, everything, then the cut
    tail = _stretch(m.HORN_THEME[-3:], 1.5)
    off = tail[0][1]
    tail = [(d, s - off, dur) for d, s, dur in tail]
    _horns(sc, 332.0, 86, theme=tail)
    pc.snare_build(sc, 344.0, 351.9, 60, 100)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, 348.0, 355.5, 70, 100)
    sc.hit(pc.CRASH, 352.0, 104, jv=2)
    en.fine_tune(sc, cd.CH_HORN2, 0.0, 354.0)
    for t in (332.0, 344.0):
        sc.note(cd.CH_BELL, n("D4"), t, 5.0, 70, jt=2, jv=2)


def over_the_hill(sc):
    t0 = 356.0
    for i, p in enumerate((n("D2"), n("A2"), n("D3"), n("F3"))):
        sc.note(cd.CH_PAD, p, t0, 58.0, 42 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 24.0, 55), (424.0, 0)],
                step=0.5)
    en.cc_curve(sc, cd.CH_PAD, 74, [(404.0, 95), (424.0, 30)], step=2.0)
    for t in (360.0, 384.0):
        for i, deg in enumerate((1, 3, 5, 8, 9, 8, 5, 3)):
            sc.note(cd.CH_HARP, en.pitch(n("D3"), MODE, deg),
                    t + i * 1.0, 1.4, 46 - (2 if i % 2 else 0), jt=3,
                    jv=3)
    sc.cc(cd.CH_FIDDLE, 68, 127, 363.0)
    en.line(sc, cd.CH_FIDDLE, 364.0, n("D4"), MODE, m.HORN_THEME, 56,
            vel_end=62, gate=1.05, jt=3, jv=2)
    sc.cc(cd.CH_FIDDLE, 68, 0, 381.5)
    en.cc_curve(sc, cd.CH_FIDDLE, 1, [(368.0, 0), (374.0, 70),
                                      (380.0, 0)], step=0.25)
    en.bend_ramp(sc, cd.CH_FIDDLE, 379.2, 379.9, 0.0, -1.5, steps=6)
    sc.bend(cd.CH_FIDDLE, 380.5, 0.0)
    en.echo_throw(sc, cd.CH_FIDDLE, 372.0, base=10, peak=70, release=3.0)
    en.vowel_curve(sc, cd.CH_CHOIR1, [(t0 + 4.0, 40), (416.0, 5)],
                   step=4.0)
    sc.note(cd.CH_CHOIR1, n("D3"), t0 + 4.0, 40.0, 42, jt=4, jv=2)
    sc.note(cd.CH_CHOIR1, n("A3"), t0 + 4.0, 40.0, 38, jt=4, jv=2)
    beat = t0 + 2.0
    while beat < 400.0:
        sc.hit(36, beat, 40, jv=2)
        beat += 8.0
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, 400.0, 403.5, 40, 78)
    # the last hit, ringing out
    sc.hit(pc.CRASH, 404.0, 96, jv=2)
    for ch, ps, v in ((cd.CH_STRINGS, (n("D3"), n("A3"), n("D4")), 66),
                      (cd.CH_HORN1, (n("D3"), n("A3")), 68),
                      (cd.CH_PIANO, (n("D2"), n("D3")), 62)):
        for i, p in enumerate(ps):
            sc.note(ch, p, 404.0, 16.0, v - i * 3, jt=2, jv=2)
    en.sustain(sc, cd.CH_PIANO, 403.9, 421.0)
    sc.note(cd.CH_BELL, n("D4"), 404.0, 10.0, 62, jt=1, jv=2)
    sc.note(cd.CH_BELL, n("D3"), 412.0, 10.0, 44, jt=2, jv=2)
