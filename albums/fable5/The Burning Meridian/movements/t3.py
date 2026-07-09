"""t3 — *Meridian* (D aeolian -> D MAJOR, 138; 5/4 as 3+2).

The battle.  The 5/4 ostinato is the war footing; the horn theme rides
it stretched x1.25 so its downbeats land on the bar lines (the
material oracle's proof carries).  The elegy is remembered in the 4/4
break, the charge stacks theme + descant in four growing waves with a
near-silent bar before the last, the horns FALL two semitones into the
final grand pause — and then it is morning: the same theme in D major
over bells.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
import percussion as pc
from engine import lerp, n

MODE = m.MODE
BASE = n("D2")
HORN_BASE = n("D3")
TIMP_D = n("D2")


def _fold(root):
    return root - 7 if root >= 5 else root


def _stretch(theme, f):
    return [(d, s * f, dur * f) for d, s, dur in theme]


HORN_125 = _stretch(m.HORN_THEME, 1.25)        # 20 beats = 4 bars of 5/4
DESC_125 = _stretch(m.descant(m.BATTLE_GROUND), 1.25)


def _horns(sc, t0, vel, theme=None, mode=MODE, base_off=0):
    theme = HORN_125 if theme is None else theme
    en.line(sc, cd.CH_HORN1, t0, HORN_BASE + base_off, mode, theme, vel,
            vel_end=vel + 5, gate=0.98, jt=3, jv=2)
    en.line(sc, cd.CH_HORN2, t0, HORN_BASE + 12 + base_off, mode, theme,
            vel - 10, vel_end=vel - 5, gate=0.98, jt=3, jv=2)


def _ost_bars(sc, t0, bars, vel0, vel1):
    for bar in range(bars):
        t = t0 + 5.0 * bar
        root = _fold(m.BATTLE_GROUND[bar % 4])
        vel = int(lerp(vel0, vel1, bar / max(1, bars - 1)))
        for deg, s, dur in m.ost_54(root):
            sc.note(cd.CH_BASSSTR, en.pitch(BASE, MODE, deg), t + s,
                    dur * 0.95, vel + (5 if s == 0.0 else 0), jt=2, jv=3)


def _war_drums(sc, t0, bars, energy):
    base = 66 + 10 * energy
    for bar in range(bars):
        t = t0 + 5.0 * bar
        sc.hit(36, t, base + 8)
        sc.hit(36, t + 3.0, base)
        sc.hit(36, t + 1.5, base - 12)
        sc.hit(pc.TOM_LO, t + 2.0, base - 6, jt=2)
        sc.hit(pc.TOM_LO, t + 2.5, base - 14, jt=2)
        if energy >= 2:
            sc.hit(pc.TOM_MID, t + 4.0, base - 8, jt=2)
            sc.hit(pc.TOM_HI, t + 4.5, base - 12, jt=2)
            b = 0.0
            while b < 5.0 - 1e-9:
                sc.hit(38, t + b, base - (18 if b % 1.0 == 0.0 else 32),
                       jt=1, jv=3)
                b += 0.25
        if energy >= 3 and bar % 4 == 3:
            for i, drum in enumerate((pc.TOM_HI, pc.TOM_MID, pc.TOM_LO,
                                      pc.TOM_LO)):
                sc.hit(drum, t + 4.0 + i * 0.25, base + 4, jt=1)


def _stab(sc, t, vel, root=1):
    for ch, base in ((cd.CH_HORN1, HORN_BASE), (cd.CH_HORN2, n("D4")),
                     (cd.CH_STRINGS, n("D3"))):
        for i, p in enumerate(en.triad(base, MODE, root)):
            sc.note(ch, p, t, 0.6, vel - i * 3, jt=1, jv=2)
    pc.timp_hit(sc, cd.CH_TIMP, en.pitch(TIMP_D, MODE, _fold(root)), t,
                vel + 4)
    sc.hit(pc.CRASH2, t, vel, jv=2)


def war_footing(sc):
    t0, bars = 0.0, 12
    _ost_bars(sc, t0, bars, 62, 74)
    _war_drums(sc, t0, bars, 1)
    _war_drums(sc, t0 + 30.0, 6, 2)
    for bar in range(bars):
        t = 5.0 * bar
        root = _fold(m.BATTLE_GROUND[bar % 4])
        pc.timp_hit(sc, cd.CH_TIMP, en.pitch(TIMP_D, MODE, root), t,
                    int(lerp(62, 80, bar / 11.0)))
    for t in (20.0, 40.0, 50.0):
        _stab(sc, t, 70)
    for i, p in enumerate((n("D2"), n("A2"), n("D3"))):
        sc.note(cd.CH_PAD, p, 0.0, 58.0, 40 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(0.0, 0), (30.0, 70), (58.0, 20)],
                step=0.5)
    en.vowel(sc, cd.CH_CHOIR1, 5, 28.0)
    sc.note(cd.CH_CHOIR1, n("D3"), 30.0, 28.0, 44, jt=4, jv=2)
    pc.snare_build(sc, 55.0, 59.9, 44, 92)


def cavalry(sc):
    t0, bars = 60.0, 20
    sc.hit(pc.CRASH, t0, 100, jv=2)
    _ost_bars(sc, t0, bars, 76, 82)
    _war_drums(sc, t0, bars, 2)
    for bar in range(bars):
        t = t0 + 5.0 * bar
        pc.timp_hit(sc, cd.CH_TIMP,
                    en.pitch(TIMP_D, MODE,
                             _fold(m.BATTLE_GROUND[bar % 4])), t, 82)
    en.fine_tune(sc, cd.CH_HORN2, 6.0, 62.0)
    _horns(sc, 60.0, 74)
    _horns(sc, 90.0, 78)
    _horns(sc, 120.0, 82)
    en.vowel_curve(sc, cd.CH_CHOIR1, [(88.0, 20), (130.0, 90)], step=4.0)
    en.line(sc, cd.CH_CHOIR1, 120.0, n("D4"), MODE, HORN_125, 64,
            vel_end=70, gate=0.97, jt=4, jv=2)
    for k, st in enumerate((80.0, 110.0, 140.0)):
        en.run(sc, cd.CH_CELLO, st, n("D3"), MODE,
               [8, 7, 6, 5, 4, 3, 2, 1], 0.625, 56 + 5 * k, 68 + 5 * k,
               legato=True)
    chords = [en.triad(n("D3"), MODE, m.BATTLE_GROUND[b % 4])
              for b in range(bars)]
    en.pad_block(sc, cd.CH_STRINGS, t0, chords, span=5.0, size=3,
                 lo=n("A2"), hi=n("A4"), vel=56, vel_end=68)
    pc.cymbal_swell(sc, 150.0, 159.0, 30, 72)
    pc.snare_build(sc, 155.0, 159.9, 50, 96)


def the_break(sc):
    t0 = 160.0
    sc.hit(pc.CRASH, t0, 92, jv=2)
    # half-time: the elegy remembered in D shapes
    for bar in range(10):
        t = t0 + 4.0 * bar
        root = m.LAMENT_GROUND[bar % 4]
        for i, step in enumerate((0, 4, 7, 9, 7, 4)):
            sc.note(cd.CH_HARP, en.pitch(n("D3"), MODE, root + step),
                    t + i * 0.5 + 0.5, 0.7, 44, jt=3, jv=3)
        sc.hit(36, t, 52)
        sc.hit(37, t + 2.0, 36, jt=2)
    frag_a = [(d, s * 4.0 / 3.0, dur * 4.0 / 3.0)
              for d, s, dur in m.ELEGY_A[:6]]     # 8 bars' worth in 4/4
    sc.cc(cd.CH_FIDDLE, 68, 127, t0 + 3.5)
    en.line(sc, cd.CH_FIDDLE, t0 + 4.0, n("D4"), MODE, frag_a, 56,
            vel_end=62, gate=1.03, jt=3, jv=2)
    sc.cc(cd.CH_FIDDLE, 68, 0, t0 + 17.0)
    en.cc_curve(sc, cd.CH_FIDDLE, 1, [(t0 + 6.0, 0), (t0 + 11.0, 60),
                                      (t0 + 15.0, 0)], step=0.25)
    frag_b = [(d, s * 4.0 / 3.0, dur * 4.0 / 3.0)
              for d, s, dur in m.ELEGY_B[:4]]
    en.line(sc, cd.CH_FLUTE, t0 + 20.0, n("D4") + 12, MODE, frag_b, 52,
            gate=0.95, jt=3, jv=2)
    # cello portamento sighs under the memory
    en.portamento_on(sc, cd.CH_CELLO, t0 + 5.0, time_cc=66)
    for beat, deg, dur in ((t0 + 6.0, 1, 6.0), (t0 + 14.0, 5, 6.0),
                           (t0 + 22.0, 4, 6.0), (t0 + 30.0, 1, 8.0)):
        sc.note(cd.CH_CELLO, en.pitch(n("D3"), MODE, deg), beat, dur, 50,
                jt=3, jv=2)
    en.portamento_off(sc, cd.CH_CELLO, t0 + 41.0)
    for i, p in enumerate((n("D2"), n("A2"), n("D3"), n("F3"))):
        sc.note(cd.CH_PAD, p, t0, 39.0, 42 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 20.0, 60), (t0 + 38.0, 5)],
                step=0.5)
    pc.snare_build(sc, 196.0, 199.9, 40, 98)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, 196.0, 199.5, 50, 96)


def charge(sc):
    t0, bars = 200.0, 28
    sc.hit(pc.CRASH, t0, 104, jv=2)
    _ost_bars(sc, t0, bars, 78, 86)
    _war_drums(sc, t0, bars, 3)
    for bar in range(bars):
        t = t0 + 5.0 * bar
        pc.timp_hit(sc, cd.CH_TIMP,
                    en.pitch(TIMP_D, MODE,
                             _fold(m.BATTLE_GROUND[bar % 4])), t, 88)
    # four waves; a near-silent bar before the last
    waves = [(220.0, 78, 1), (250.0, 82, 2), (285.0, 86, 3),
             (315.0, 90, 4)]
    en.vowel(sc, cd.CH_CHOIR1, 100, 248.0)
    en.vowel(sc, cd.CH_CHOIR2, 95, 283.0)
    for st, vel, layer in waves:
        _horns(sc, st, vel)
        if layer >= 2:
            en.line(sc, cd.CH_CHOIR1, st, n("D4"), MODE, HORN_125,
                    vel - 14, gate=0.97, jt=4, jv=2)
            en.at_curve(sc, cd.CH_CHOIR1, [(st, 10), (st + 10.0, 85),
                                           (st + 19.5, 15)], step=0.5)
        if layer >= 3:
            en.line(sc, cd.CH_FIDDLE, st, n("D4"), MODE, DESC_125,
                    vel - 12, gate=0.97, jt=3, jv=2)
            en.line(sc, cd.CH_FLUTE, st, n("D5"), MODE, DESC_125,
                    vel - 18, gate=0.95, jt=3, jv=2)
            en.line(sc, cd.CH_CHOIR2, st, n("D4"), MODE, DESC_125,
                    vel - 22, gate=0.97, jt=4, jv=2)
            for deg, s, dur in HORN_125:
                sc.note(cd.CH_GLOCK, en.pitch(n("D5"), MODE, deg),
                        st + s, dur * 0.7, vel - 26, jt=3, jv=3)
        if layer >= 4:
            en.line(sc, cd.CH_STRINGS, st, n("D4"), MODE, HORN_125,
                    vel - 10, gate=0.99, jt=4, jv=2)
            sc.note(cd.CH_BELL, n("D4"), st, 5.0, 74, jt=1, jv=2)
    # the held breath: bar 310-315 nearly empty (timpani only)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, 310.0, 314.5, 30, 100)
    # the horns FALL into the grand pause
    for ch in (cd.CH_HORN1, cd.CH_HORN2):
        en.bend_ramp(sc, ch, 336.5, 338.2, 0.0, -2.0, steps=10)
        sc.bend(ch, 339.2, 0.0)
    en.fine_tune(sc, cd.CH_HORN2, 0.0, 339.5)
    pc.snare_build(sc, 336.0, 339.7, 60, 104)
    sc.hit(pc.CRASH, 339.5, 106, jv=2)


def daybreak(sc):
    t0 = 340.0
    ION = "ionian"
    sc.hit(pc.CRASH, t0, 96, jv=2)
    for t in (t0, t0 + 8.0, t0 + 16.0, t0 + 24.0, t0 + 32.0):
        sc.note(cd.CH_BELL, n("D4"), t, 6.0,
                int(lerp(76, 60, (t - t0) / 32.0)), jt=1, jv=2)
    # the theme in the MAJOR, twice, over a tonic pedal
    _horns(sc, t0 + 4.0, 78, theme=m.HORN_THEME, mode=ION)
    _horns(sc, t0 + 24.0, 74, theme=m.HORN_THEME, mode=ION)
    en.line(sc, cd.CH_STRINGS, t0 + 4.0, n("D4"), ION, m.HORN_THEME, 70,
            gate=0.99, jt=4, jv=2)
    en.line(sc, cd.CH_CHOIR1, t0 + 24.0, n("D4"), ION, m.HORN_THEME, 62,
            gate=0.97, jt=4, jv=2)
    en.vowel(sc, cd.CH_CHOIR1, 100, t0 + 22.0)
    en.at_curve(sc, cd.CH_CHOIR1, [(t0 + 24.0, 10), (t0 + 32.0, 80),
                                   (t0 + 39.0, 10)], step=0.5)
    for deg, s, dur in m.HORN_THEME:
        sc.note(cd.CH_GLOCK, en.pitch(n("D5"), ION, deg), t0 + 4.0 + s,
                dur * 0.7, 60, jt=3, jv=3)
    for i, p in enumerate((n("D2"), n("A2"), n("D3"), n("F#3"))):
        sc.note(cd.CH_PAD, p, t0, 70.0, 46 - i, jt=3, jv=2)
        sc.note(cd.CH_BASSSTR, p, t0, 34.0, 56 - i * 3, jt=3, jv=2)
    beat = t0
    while beat < t0 + 40.0:
        sc.hit(36, beat, 62, jv=2)
        sc.hit(36, beat + 2.0, 48, jv=2)
        beat += 4.0
    pc.timp_hit(sc, cd.CH_TIMP, TIMP_D, t0, 88, ring=4.0)
    pc.timp_hit(sc, cd.CH_TIMP, TIMP_D, t0 + 16.0, 78, ring=4.0)
    # the last chord: D major, everything, rung out
    T = t0 + 48.0                                  # 388
    sc.hit(pc.CRASH, T, 100, jv=2)
    pc.timp_roll(sc, cd.CH_TIMP, TIMP_D, T - 4.0, T - 0.3, 60, 96)
    for ch, base, v in ((cd.CH_STRINGS, n("D3"), 72),
                        (cd.CH_HORN1, n("D3"), 74),
                        (cd.CH_HORN2, n("D4"), 64),
                        (cd.CH_CHOIR1, n("D4"), 66),
                        (cd.CH_PIANO, n("D2"), 64)):
        for i, p in enumerate(en.triad(base, ION, 1)):
            sc.note(ch, p, T, 22.0, v - i * 3, jt=2, jv=2)
    en.sustain(sc, cd.CH_PIANO, T - 0.1, T + 24.0)
    sc.note(cd.CH_BELL, n("D4"), T, 14.0, 78, jt=1, jv=2)
    sc.note(cd.CH_BELL, n("D5"), T + 4.0, 10.0, 58, jt=2, jv=2)
    sc.note(cd.CH_BELL, n("D3"), T + 8.0, 12.0, 52, jt=2, jv=2)
    for i, deg in enumerate((1, 3, 5, 8)):
        sc.note(cd.CH_HARP, en.pitch(n("D3"), ION, deg), T + 0.5 + i * 0.3,
                3.0, 56 - i * 3, jt=2, jv=2)
    en.at_curve(sc, cd.CH_CHOIR1, [(T, 30), (T + 6.0, 90), (T + 20.0, 0)],
                step=0.5)
