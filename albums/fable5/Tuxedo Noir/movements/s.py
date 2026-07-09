"""s — the seven sections of *Tuxedo Noir* (E aeolian, swung 128).

Swing is composed, not implied: every 8th pair in the vamp, ride and
comping is written long-short 2:1 (the SW constant from material.py).
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

MODE = m.MODE
SW = m.SW
BASS_BASE = n("E1")             # 28; the vamp sits E1-E2
THEME_BASE = n("E4")            # 64
E = n("E2")


def _fold(root):
    return root - 7 if root >= 5 else root


# ---------------------------------------------------------------------------
# drums
# ---------------------------------------------------------------------------

def _swing_ride(sc, t0, bars, energy=1, brushes=False):
    base = 56 + 8 * energy
    for bar in range(bars):
        t = t0 + 4.0 * bar
        for beat in range(4):
            b = t + beat
            sc.hit(51, b, base - (4 if beat % 2 == 0 else 10), jt=2,
                   jv=3)
            if beat % 2 == 1:
                sc.hit(51, b + SW, base - 18, jt=2, jv=3)
                sc.hit(37, b, base - 8, jt=2)
                sc.hit(44, b, base - 22, jt=2)
        sc.hit(36, t, base - 10)
        sc.hit(36, t + 2.0, base - 16)
        if brushes:
            for s in range(8):
                sc.hit(38, t + s * 0.5 + (SW - 0.5 if s % 2 else 0.0),
                       26 + (4 if s % 4 == 0 else 0), jt=2, jv=3)
        if energy >= 2 and bar % 4 == 3:
            for i, drum in enumerate((45, 43, 41)):
                sc.hit(drum, t + 3.0 + i * (1.0 / 3.0), base + 2 + 2 * i,
                       jt=2)


def _chase_drums(sc, t0, bars, energy=3):
    base = 62 + 8 * energy
    for bar in range(bars):
        t = t0 + 3.5 * bar
        sc.hit(36, t, base + 8)
        sc.hit(36, t + 1.0, base - 14)
        sc.hit(36, t + 2.5, base - 4)
        sc.hit(38, t + 1.5, base + 4)
        for s in range(7):
            accent = s * 0.5 in (0.0, 1.5, 2.5)
            sc.hit(42, t + s * 0.5, base - (10 if accent else 26), jt=2,
                   jv=3)
        if bar % 4 == 3:
            sc.hit(38, t + 3.0, base - 2, jt=1)
            sc.hit(45, t + 3.25, base + 2, jt=1)


def _bongos(sc, t0, bars):
    for bar in range(bars):
        t = t0 + 6.0 * bar
        for b, drum, v in ((0.0, 60, 52), (1.0, 61, 44), (1.5, 61, 40),
                           (2.5, 60, 48), (3.0, 61, 44), (4.0, 60, 50),
                           (5.0, 61, 42), (5.5, 60, 46)):
            sc.hit(drum, t + b, v, jt=2, jv=3)


# ---------------------------------------------------------------------------
# shared figures
# ---------------------------------------------------------------------------

def _vamp_bars(sc, t0, bars, vel0, vel1):
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = _fold(m.VAMP_GROUND[bar % 4]) + 7    # E2 region
        vel = int(lerp(vel0, vel1, bar / max(1, bars - 1)))
        for deg, s, dur in m.vamp(root):
            sc.note(cd.CH_BASS, en.pitch(BASS_BASE, MODE, deg), t + s,
                    dur * 0.95, vel + (5 if s == 0.0 else 0), jt=1, jv=2)


def _comp(sc, t0, bars, vel):
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.VAMP_GROUND[bar % 4]
        pitches = [en.pitch(n("E3"), MODE, root + s) for s in (0, 2, 4, 8)]
        for beat in (1.0, 3.0):
            for j, p in enumerate(pitches):
                sc.note(cd.CH_COMP, p, t + beat + SW, 0.28, vel - j * 2,
                        jt=2, jv=3)


def _theme(sc, t0, vel, octave=0, fall=True):
    ch = cd.CH_TWANG
    en.line(sc, ch, t0, THEME_BASE + 12 * octave, MODE, m.THEME, vel,
            vel_end=vel + 5, gate=0.95, jt=3, jv=2)
    en.cc_curve(sc, ch, 1, [(t0 + 8.0, 0), (t0 + 11.0, 60),
                            (t0 + 14.0, 0)], step=0.25)
    en.echo_throw(sc, ch, t0 + 2.0, base=25, peak=90, release=2.5)
    en.echo_throw(sc, ch, t0 + 12.0, base=25, peak=85, release=2.5)
    if fall:
        end = t0 + 15.6
        en.bend_ramp(sc, ch, end, end + 0.4, 0.0, -1.8, steps=6)
        sc.bend(ch, end + 0.9, 0.0)


def _stab_hits(sc, t0, vel, line=None):
    """The built horn section speaking the stab line (organ + saw +
    a triad punch under the long hits)."""
    line = m.STAB_LINE if line is None else line
    for deg, s, dur in line:
        p = en.pitch(n("E3"), MODE, deg)
        sc.note(cd.CH_ORG, p, t0 + s, dur * 0.9, vel, jt=1, jv=2)
        sc.note(cd.CH_SAW, p + 12, t0 + s, dur * 0.9, vel - 14, jt=1,
                jv=2)
        if dur >= 1.5:
            bar = int((s % 16.0) // 4.0)
            root = m.VAMP_GROUND[bar]
            for j, q in enumerate(en.triad(n("E3"), MODE, root)[:2]):
                sc.note(cd.CH_ORG, q, t0 + s, 0.5, vel - 8 - j * 3,
                        jt=1, jv=2)


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

def cold_open(sc):
    for i, p in enumerate((n("E3"), n("G3"), n("B3"), n("F#4"))):
        sc.note(cd.CH_VIBES, p, 0.0, 7.0, 52 - i * 2, jt=3, jv=2)
        sc.note(cd.CH_VIBES, p, 8.0, 7.0, 56 - i * 2, jt=3, jv=2)
    en.sustain(sc, cd.CH_PIANO, 0.1, 15.0)
    sc.note(cd.CH_PIANO, n("E1"), 0.0, 7.5, 54, jt=2, jv=2)
    sc.note(cd.CH_PIANO, n("E2"), 0.0, 7.5, 48, jt=2, jv=2)
    sc.note(cd.CH_PIANO, n("E1"), 8.0, 7.0, 58, jt=2, jv=2)
    sc.note(cd.CH_PIANO, n("B1"), 8.0, 7.0, 50, jt=2, jv=2)
    for beat in (2.0, 6.0, 10.0, 14.0):
        sc.hit(37, beat, 36, jt=2)
        sc.hit(51, beat + 1.0, 32, jt=2)
    for t, deg in ((5.0, 9), (13.0, 8)):
        sc.note(cd.CH_CELESTA, en.pitch(n("E5"), MODE, deg), t, 2.0, 46,
                jt=3, jv=3)
        en.echo_throw(sc, cd.CH_CELESTA, t, base=15, peak=72,
                      release=2.0)
    sc.note(cd.CH_BELL, n("E3"), 12.0, 4.0, 46, jt=2, jv=2)
    for i, p in enumerate((n("E2"), n("B2"), n("E3"))):
        sc.note(cd.CH_PAD, p, 0.0, 15.5, 38 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(0.0, 0), (8.0, 60), (15.0, 5)],
                step=0.5)


def the_vamp(sc):
    t0, bars = 16.0, 20
    _vamp_bars(sc, t0, bars, 68, 78)
    _swing_ride(sc, t0, bars, energy=1)
    _comp(sc, t0, bars, 52)
    for bar in range(0, bars, 2):                  # piano noir dyads
        t = t0 + 4.0 * bar
        root = m.VAMP_GROUND[bar % 4]
        p = en.pitch(n("E2"), MODE, root)
        sc.note(cd.CH_PIANO, p, t, 1.5, 50, jt=2, jv=2)
        sc.note(cd.CH_PIANO, p + 7, t, 1.5, 44, jt=2, jv=2)
    _theme(sc, 48.0, 72)
    _theme(sc, 64.0, 76)
    for t, deg in ((62.0, 9), (78.0, 12)):
        sc.note(cd.CH_CELESTA, en.pitch(n("E5"), MODE, deg), t, 1.5, 48,
                jt=3, jv=3)
        en.echo_throw(sc, cd.CH_CELESTA, t, base=15, peak=70,
                      release=2.0)
    sc.cc(cd.CH_STRINGS, 11, 0, 79.0)
    for i, p in enumerate((n("E3"), n("G3"), n("B3"))):
        sc.note(cd.CH_STRINGS, p, 80.0, 15.5, 48 - i * 2, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(80.0, 0), (90.0, 65), (95.0, 40)],
                  step=1.0)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (56.0, 55), (94.0, 10)],
                step=0.5)
    for i, p in enumerate((n("E2"), n("B2"))):
        sc.note(cd.CH_PAD, p, t0, 79.0, 36 - i, jt=3, jv=2)


def stabs(sc):
    t0, bars = 96.0, 12
    sc.hit(49, t0, 88, jv=2)
    sc.note(cd.CH_BELL, n("E3"), t0, 4.0, 58, jt=0, jv=2)
    _vamp_bars(sc, t0, bars, 76, 82)
    _swing_ride(sc, t0, bars, energy=2)
    _comp(sc, t0, bars, 56)
    en.fine_tune(sc, cd.CH_SAW, 5.0, 94.0)
    _stab_hits(sc, 96.0, 78)
    _stab_hits(sc, 112.0, 82)
    _theme(sc, 112.0, 78, octave=0)
    _stab_hits(sc, 128.0, 84)
    _theme(sc, 128.0, 80, fall=False)   # a fall here would cross the seam
    sc.note(cd.CH_BELL, n("E3"), 128.0, 4.0, 56, jt=2, jv=2)
    b = 140.0
    while b < 143.9:
        sc.hit(38, b, int(lerp(34, 76, (b - 140.0) / 4.0)), jt=2, jv=3)
        b += 0.25


def velvet(sc):
    t0, bars = 144.0, 10                           # 12/8: 6 beats a bar
    _bongos(sc, t0, bars)
    for bar in range(bars):                        # vibes water
        t = t0 + 6.0 * bar
        root = m.VAMP_GROUND[bar % 4]
        for i, step in enumerate((0, 4, 7, 9, 7, 4)):
            sc.note(cd.CH_VIBES, en.pitch(n("E3"), MODE, root + step),
                    t + i * 1.0, 1.4, 48 - (2 if i % 2 else 0), jt=3,
                    jv=3)
        p = en.pitch(n("E1") + 12, MODE, _fold(root) + 7)
        sc.note(cd.CH_BASS, p, t, 4.0, 58, jt=2, jv=2)
        sc.note(cd.CH_BASS, p + 7, t + 4.0, 1.8, 50, jt=2, jv=2)
    en.sustain(sc, cd.CH_PIANO, t0 + 0.2, t0 + 28.0)
    en.sustain(sc, cd.CH_PIANO, t0 + 30.0, t0 + 58.0)
    for k in range(4):
        t = t0 + 15.0 * k
        sc.note(cd.CH_PIANO, n("E2"), t + 0.5, 5.0, 42, jt=3, jv=2)
    flute_theme = [(d, s * 0.75, dur * 0.75) for d, s, dur in m.THEME]
    en.line(sc, cd.CH_FLUTE, 150.0, n("E4"), MODE, flute_theme, 58,
            vel_end=64, gate=0.95, jt=3, jv=2)
    en.echo_throw(sc, cd.CH_FLUTE, 154.0, base=15, peak=78, release=2.5)
    en.portamento_on(sc, cd.CH_FIDDLE, 166.0, time_cc=68)
    for beat, deg, dur in ((168.0, 5, 4.0), (174.0, 6, 3.0),
                           (178.0, 3, 4.0), (184.0, 5, 5.0),
                           (190.0, 2, 4.0), (196.0, 1, 6.0)):
        sc.note(cd.CH_FIDDLE, en.pitch(n("E4"), MODE, deg), beat, dur,
                54, jt=3, jv=2)
        en.cc_curve(sc, cd.CH_FIDDLE, 1,
                    [(beat + 0.5, 0), (beat + dur * 0.7, 60),
                     (beat + dur, 0)], step=0.25)
    en.portamento_off(sc, cd.CH_FIDDLE, 203.0)
    for i, p in enumerate((n("E2"), n("B2"), n("G3"))):
        sc.note(cd.CH_STRINGS, p, t0 + 12.0, 46.0, 40 - i, jt=3, jv=2)
    for t, deg in ((160.0, 12), (176.0, 9), (192.0, 10)):
        sc.note(cd.CH_CELESTA, en.pitch(n("E5"), MODE, deg), t, 2.5, 44,
                jt=3, jv=3)
        en.echo_throw(sc, cd.CH_CELESTA, t, base=12, peak=68,
                      release=2.5)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 30.0, 50), (200.0, 5)],
                step=0.5)
    for i, p in enumerate((n("E2"), n("B2"))):
        sc.note(cd.CH_PAD, p, t0, 59.0, 34 - i, jt=3, jv=2)


def the_chase(sc):
    t0, bars = 204.0, 20
    sc.hit(49, t0, 96, jv=2)
    for bar in range(bars):
        t = t0 + 3.5 * bar
        root = _fold(m.CHASE_GROUND[bar % 4]) + 7
        vel = int(lerp(78, 86, bar / (bars - 1)))
        for deg, s, dur in m.CHASE_CELL:
            sc.note(cd.CH_BASS, en.pitch(BASS_BASE, MODE, root + deg),
                    t + s, dur * 0.9, vel + (4 if s == 0.0 else 0),
                    jt=1, jv=2)
        p = en.pitch(n("E3"), MODE, m.CHASE_GROUND[bar % 4])
        for s in range(7):                         # palm-mute chug
            sc.note(cd.CH_COMP, p, t + s * 0.5, 0.4,
                    64 if s in (0, 3, 5) else 52, jt=2, jv=3)
    _chase_drums(sc, t0, bars)
    for k, t in enumerate((204.0, 218.0, 232.0, 246.0, 260.0)):
        for j, p in enumerate(en.triad(n("E3"), MODE, 1)):
            sc.note(cd.CH_ORG, p, t, 0.5, 76 - j * 3, jt=1, jv=2)
            sc.note(cd.CH_SAW, p + 12, t, 0.5, 64 - j * 3, jt=1, jv=2)
    for st in (211.0, 239.0):
        en.run(sc, cd.CH_SOLO, st, n("E4"), MODE,
               [1, 3, 4, 5, 7, 8], 0.25, 68, 84, legato=True)
    en.line(sc, cd.CH_SOLO, 253.0, n("E4"), MODE,
            [(8, 0, 1.0), (7, 1.0, 0.5), (5, 1.5, 1.0), (4, 2.5, 0.5),
             (5, 3.0, 2.0)], 78, gate=0.95, jt=2, jv=2)
    en.cc_curve(sc, cd.CH_SOLO, 1, [(256.5, 0), (257.5, 70), (258.2, 0)],
                step=0.25)
    b = 270.5
    while b < 273.9:
        sc.hit(38, b, int(lerp(40, 88, (b - 270.5) / 3.5)), jt=1, jv=3)
        b += 0.25
    sc.note(cd.CH_STRINGS, n("E3"), t0, 68.0, 46, jt=3, jv=2)
    sc.note(cd.CH_STRINGS, n("B3"), t0 + 35.0, 33.0, 44, jt=3, jv=2)


def showdown(sc):
    t0, bars = 274.0, 20
    sc.hit(49, t0, 100, jv=2)
    sc.note(cd.CH_BELL, n("E3"), t0, 5.0, 64, jt=0, jv=2)
    _vamp_bars(sc, t0, bars, 82, 88)
    _swing_ride(sc, t0, bars, energy=3)
    _comp(sc, t0, bars, 60)
    # showdown shimmer: swung vibes 8ths + piano push octaves (the
    # densest fabric of the piece, as the dynamics oracle requires)
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.VAMP_GROUND[bar % 4]
        p = en.pitch(n("E4"), MODE, root)
        for beat in range(4):
            sc.note(cd.CH_VIBES, p, t + beat, 0.4, 52, jt=2, jv=3)
            sc.note(cd.CH_VIBES, p + 7, t + beat + SW, 0.3, 44, jt=2,
                    jv=3)
        for beat in (1.0 + SW, 3.0 + SW):
            q = en.pitch(n("E3"), MODE, root)
            sc.note(cd.CH_PIANO, q, t + beat, 0.3, 56, jt=2, jv=3)
            sc.note(cd.CH_PIANO, q + 12, t + beat, 0.3, 50, jt=2, jv=3)
    # the verified pair, twice
    _theme(sc, 282.0, 84)
    _stab_hits(sc, 282.0, 84)
    _theme(sc, 298.0, 86)
    _stab_hits(sc, 298.0, 86)
    # the held breath: one bar, bass ringing alone
    sc.note(cd.CH_BASS, n("E2"), 314.0, 3.8, 70, jt=1, jv=2)
    sc.hit(49, 318.0, 96, jv=2)
    # the dive: RPN 12, minus seven, while the band vamps on
    en.bend_range(sc, cd.CH_SOLO, 12, 316.0)
    _theme(sc, 318.0, 88)
    _stab_hits(sc, 318.0, 88)
    en.line(sc, cd.CH_CHOIR, 318.0, n("E3"), MODE, m.STAB_LINE, 60,
            gate=0.97, jt=4, jv=2)
    en.vowel(sc, cd.CH_CHOIR, 95, 316.5)
    en.at_curve(sc, cd.CH_CHOIR, [(318.0, 10), (326.0, 80),
                                  (333.5, 10)], step=0.5)
    sc.note(cd.CH_SOLO, n("E5"), 330.0, 3.0, 90, jt=1, jv=2)
    en.cc_curve(sc, cd.CH_SOLO, 1, [(330.5, 0), (331.5, 80),
                                    (332.0, 0)], step=0.25)
    en.bend_ramp(sc, cd.CH_SOLO, 332.0, 333.6, 0.0,
                 2.0 * -7.0 / 12.0, steps=14)
    sc.bend(cd.CH_SOLO, 334.4, 0.0)
    en.bend_range(sc, cd.CH_SOLO, 2, 336.0)
    # final build
    for i, p in enumerate((n("E3"), n("G3"), n("B3"), n("E4"))):
        sc.note(cd.CH_STRINGS, p, 334.0, 19.0, 58 - i * 2, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(334.0, 40), (352.0, 88)],
                  step=1.0)
    b = 346.0
    while b < 353.9:
        sc.hit(38, b, int(lerp(44, 96, (b - 346.0) / 8.0)), jt=2, jv=3)
        b += 0.25
    for t in (350.0, 351.0, 352.0, 353.0):
        sc.hit(36, t, 90, jt=1)


def last_cigarette(sc):
    t0 = 354.0
    sc.hit(49, t0, 92, jv=2)
    for i, p in enumerate((n("E3"), n("G3"), n("B3"), n("F#4"))):
        sc.note(cd.CH_VIBES, p, t0, 10.0, 52 - i * 2, jt=3, jv=2)
    half_theme = [(d, s * 2.0, dur * 2.0) for d, s, dur in m.THEME[:4]]
    en.line(sc, cd.CH_TWANG, t0 + 2.0, n("E4"), MODE, half_theme, 60,
            vel_end=54, gate=0.95, jt=3, jv=2)
    en.echo_throw(sc, cd.CH_TWANG, t0 + 4.0, base=18, peak=80,
                  release=3.0)
    en.bend_ramp(sc, cd.CH_TWANG, t0 + 12.6, t0 + 13.4, 0.0, -1.5,
                 steps=6)
    sc.bend(cd.CH_TWANG, t0 + 14.0, 0.0)
    for t, deg in ((t0 + 6.0, 9), (t0 + 14.0, 8)):
        sc.note(cd.CH_CELESTA, en.pitch(n("E5"), MODE, deg), t, 2.5, 42,
                jt=3, jv=3)
        en.echo_throw(sc, cd.CH_CELESTA, t, base=10, peak=64,
                      release=3.0)
    for beat in (t0 + 2.0, t0 + 6.0, t0 + 10.0):
        sc.hit(37, beat, 32, jt=2)
        sc.hit(51, beat + 1.0, 28, jt=2)
    sc.note(cd.CH_BASS, n("E2"), t0 + 2.0, 8.0, 56, jt=2, jv=2)
    sc.note(cd.CH_BASS, n("E1"), t0 + 12.0, 13.8, 50, jt=2, jv=2)
    sc.note(cd.CH_CELESTA, en.pitch(n("E5"), MODE, 5), t0 + 23.0, 2.5,
            38, jt=3, jv=2)
    # THE chord: E minor-major-9, rung out by everyone
    T = t0 + 26.0                                  # 380
    sc.hit(49, T, 84, jv=2)
    en.sustain(sc, cd.CH_PIANO, T - 0.1, T + 11.0)
    for i, p in enumerate(m.MINMAJ9):
        sc.note(cd.CH_PIANO, p, T, 10.0, 58 - i * 3, jt=1, jv=2)
        if p >= 52:
            sc.note(cd.CH_VIBES, p, T, 10.0, 50 - i * 2, jt=1, jv=2)
    for i, p in enumerate(m.MINMAJ9[1:4]):
        sc.note(cd.CH_STRINGS, p, T, 10.0, 44 - i * 2, jt=2, jv=2)
    sc.note(cd.CH_BELL, n("E3"), T, 10.0, 54, jt=1, jv=2)
    sc.note(cd.CH_BASS, n("E1"), T, 8.0, 54, jt=1, jv=2)
    sc.hit(37, T + 4.0, 26, jt=2)
