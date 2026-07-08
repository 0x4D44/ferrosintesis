"""p1 — the six movements of *Heliopause, Part One* (A aeolian, 116).

The Oxygène grammar: everything breathes.  The sequencer's filter
never sits still, the pads swell on aftertouch, the lead glides on
portamento and blooms into wheel vibrato, transitions are wind and
whoosh, and the big moments arrive by SUBTRACTION — The Drop cuts the
whole machine to let a theremin sing.
"""

from __future__ import annotations

import math

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

MODE = m.MODE
BASS_BASE = n("A1")             # 33
LEAD_BASE = n("A4")             # 69
SEQ_BASE = n("A3")              # 57
PAD_VOICES = [n("A2"), n("E3"), n("A3"), n("C4"), n("B4")]  # Am(add9)


# ---------------------------------------------------------------------------
# shared textures
# ---------------------------------------------------------------------------

def _seq_bars(sc, t0, bars, roots, vel0, vel1, slots=16, ch=None):
    ch = cd.CH_SEQ if ch is None else ch
    for bar in range(bars):
        beat = 4.0 if slots == 16 else 3.0
        t = t0 + beat * bar
        root = roots[bar % len(roots)]
        vel = int(lerp(vel0, vel1, bar / max(1, bars - 1)))
        for deg, s, dur in m.seq_cell(root, slots):
            v = vel + (6 if s == 0.0 else 0)
            sc.note(ch, en.pitch(SEQ_BASE, MODE, deg), t + s, dur * 0.9,
                    v, jt=1, jv=2)


def _bass_bars(sc, t0, bars, roots, vel):
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = roots[bar % len(roots)]
        for deg, s, dur in m.bass_pulse(root):
            sc.note(cd.CH_BASS, en.pitch(BASS_BASE, MODE, deg), t + s,
                    dur * 0.9, vel + (4 if s == 0.0 else 0), jt=1, jv=2)


def _theme(sc, ch, t0, theme, vel, base=None, octave=0, glide=True,
           echo=True):
    base = LEAD_BASE if base is None else base
    if glide:
        en.portamento_on(sc, ch, t0 - 1.5, time_cc=52)
    en.line(sc, ch, t0, base + 12 * octave, MODE, theme, vel,
            vel_end=vel + 6, gate=1.0 if glide else 0.95, jt=3, jv=2)
    longest = max(theme, key=lambda x: x[2])
    h0 = t0 + longest[1]
    en.cc_curve(sc, ch, 1, [(h0, 0), (h0 + longest[2] * 0.7, 70),
                            (h0 + longest[2], 0)], step=0.25)
    if echo:
        en.echo_throw(sc, ch, h0, base=18, peak=85, release=2.5)


def _electro(sc, t0, bars, energy, fill_every=8):
    """The electro floor: four kicks, electro snare, 16th hats."""
    base = 66 + 8 * energy
    for bar in range(bars):
        t = t0 + 4.0 * bar
        fill_bar = fill_every and bar % fill_every == fill_every - 1
        for k in range(4):
            sc.hit(36, t + k, base + (6 if k == 0 else -6))
        for beat in (1.0, 3.0):
            sc.hit(38, t + beat, base + 2)
            if energy >= 2:
                sc.hit(39, t + beat, base - 26)
        span = 3.0 if fill_bar else 4.0
        for s in range(int(span * 4)):
            v = base - (14 if s % 4 == 0 else 30 if s % 2 else 22)
            sc.hit(42, t + s * 0.25, v, jt=2, jv=3)
        if fill_bar:
            for i, drum in enumerate((50, 47, 45, 41)):
                sc.hit(drum, t + 3.0 + i * 0.25, base + 4 + 2 * i, jt=2)
        elif energy >= 2 and bar % 2 == 1:
            sc.hit(46, t + 3.75, base - 18, jt=2)


# ---------------------------------------------------------------------------
# I. Solar Wind (0-48)
# ---------------------------------------------------------------------------

def solar_wind(sc):
    ch = cd.CH_PAD
    for k in range(3):
        t = k * 16.0
        for i, p in enumerate(PAD_VOICES):
            sc.note(ch, p, t, 15.7, 40 + 2 * k - i, jt=4, jv=2)
        en.at_curve(sc, ch, [(t, 0), (t + 8.0, 85), (t + 15.5, 0)],
                    step=0.5)
    en.wah(sc, ch, 0.0, 46.0, lo=28, hi=88, cycles_per_beat=1 / 24.0,
           step=0.5)

    sc.cc(cd.CH_STRINGS, 11, 0, 15.0)
    sc.note(cd.CH_STRINGS, n("A2"), 16.0, 30.0, 44, jt=3, jv=2)
    sc.note(cd.CH_STRINGS, n("E3"), 16.0, 30.0, 41, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(16.0, 0), (32.0, 62), (46.0, 20)],
                  step=1.0)

    for t, deg in ((6.0, 5), (14.0, 3), (22.0, 8), (30.0, 7), (38.0, 10)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 2.5,
                int(lerp(40, 50, t / 40.0)), jt=4, jv=3)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=15, peak=78, release=2.5)

    sc.note(cd.CH_BELL, n("A3"), 8.0, 6.0, 46, jt=0, jv=2)
    sc.note(cd.CH_BELL, n("A3"), 32.0, 6.0, 52, jt=2, jv=2)

    en.line(sc, cd.CH_FLUTE, 24.0, n("A4"), MODE, m.THEME_A[:3], 46,
            gate=0.95, jt=4, jv=2)
    en.echo_throw(sc, cd.CH_FLUTE, 24.0, base=15, peak=70, release=2.0)

    beat = 32.0
    while beat < 44.0:
        sc.hit(36, beat, int(lerp(46, 56, (beat - 32.0) / 12.0)), jv=2)
        sc.hit(36, beat + 1.5, 40, jv=2)
        beat += 4.0
    b = 44.0
    while b < 47.9:
        sc.hit(38, b, int(lerp(28, 66, (b - 44.0) / 4.0)), jt=2, jv=3)
        b += 0.25
    en.vowel_curve(sc, cd.CH_CHOIR, [(40.0, 15), (47.0, 70)], step=1.0)
    sc.note(cd.CH_CHOIR, n("A3"), 40.0, 7.5, 46, jt=3, jv=2)
    sc.note(cd.CH_CHOIR, n("E4"), 40.0, 7.5, 42, jt=3, jv=2)
    for i in range(6):                             # the cell fades in
        sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE,
                                    1 + m.SEQ_LADDER[i % 8]),
                44.0 + i * 0.5, 0.4, int(lerp(30, 52, i / 5.0)), jt=2)


# ---------------------------------------------------------------------------
# II. The Sequencer (48-192)
# ---------------------------------------------------------------------------

def the_sequencer(sc):
    t0, bars = 48.0, 36
    _seq_bars(sc, t0, bars, m.GROUND_A, 56, 70)
    en.cc_curve(sc, cd.CH_SEQ, 74, [(48.0, 30), (160.0, 100)], step=4.0)
    en.cc_curve(sc, cd.CH_SEQ, 71, [(48.0, 45), (140.0, 85), (190.0, 60)],
                step=4.0)
    en.autopan(sc, cd.CH_SEQ, t0, 142.0, lo=50, hi=98, period_beats=16.0,
               step=0.25)

    _bass_bars(sc, 64.0, 32, m.GROUND_A, 74)
    _electro(sc, 80.0, 28, energy=1, fill_every=8)

    for bar in range(12, 36, 2):                   # glass chords
        t = t0 + 4.0 * bar
        root = m.GROUND_A[bar % 4]
        for i, p in enumerate(en.triad(n("A3"), MODE, root)):
            sc.note(cd.CH_EP, p, t, 3.5, 52 - i * 2, jt=3, jv=2)

    chords = [en.triad(n("A2"), MODE, m.GROUND_A[b % 4])
              for b in range(16, 36)]
    en.pad_block(sc, cd.CH_PAD, t0 + 64.0, chords, span=4.0, size=3,
                 lo=n("E2"), hi=n("E4"), vel=42)

    _theme(sc, cd.CH_LEAD, 128.0, m.THEME_A, 72)
    _theme(sc, cd.CH_LEAD, 160.0, m.THEME_A, 76)
    en.portamento_off(sc, cd.CH_LEAD, 190.0)
    for deg, s, dur in m.THEME_A:                  # glock halo, 1st stmt
        sc.note(cd.CH_GLOCK, en.pitch(n("A5"), MODE, deg), 128.0 + s,
                dur * 0.8, 48, jt=3, jv=3)
    # the statement-two tail falls away
    en.bend_ramp(sc, cd.CH_LEAD, 175.3, 175.9, 0.0, -2.0, steps=8)
    sc.bend(cd.CH_LEAD, 176.4, 0.0)

    en.vowel(sc, cd.CH_CHOIR, 8, 143.0)
    en.vowel_curve(sc, cd.CH_CHOIR, [(144.0, 8), (188.0, 45)], step=4.0)
    for t in range(144, 192, 16):
        sc.note(cd.CH_CHOIR, n("A3"), float(t), 15.5, 44, jt=4, jv=2)
        sc.note(cd.CH_CHOIR, n("E4"), float(t), 15.5, 40, jt=4, jv=2)
        en.at_curve(sc, cd.CH_CHOIR, [(t, 0), (t + 8.0, 70),
                                      (t + 15.0, 5)], step=0.5)


# ---------------------------------------------------------------------------
# III. Mirror Waltz (192-264) — 3/4
# ---------------------------------------------------------------------------

def mirror_waltz(sc):
    t0, bars = 192.0, 24
    roots = m.GROUND_LIFT
    sc.note(cd.CH_BELL, n("A3"), t0, 5.0, 54, jt=0, jv=2)
    for bar in range(bars):
        t = t0 + 3.0 * bar
        root = roots[bar % 4]
        for deg, s, dur in m.WALTZ_CELL:           # nylon figure
            sc.note(cd.CH_NYLON, en.pitch(n("A3"), MODE, root + deg),
                    t + s, dur * 0.9, 56 + (4 if s == 0.0 else 0),
                    jt=3, jv=3)
        p0 = en.pitch(n("A2"), MODE, root)         # EP oom-pah-pah
        sc.note(cd.CH_EP, p0, t, 0.9, 52, jt=2, jv=2)
        for beat in (1.0, 2.0):
            for i, p in enumerate(en.triad(n("A3"), MODE, root)[:2]):
                sc.note(cd.CH_EP, p, t + beat, 0.8, 44 - i * 2, jt=2,
                        jv=2)
        sc.hit(36, t, 52)
        sc.hit(37, t + 1.0, 38, jt=2)
        sc.hit(37, t + 2.0, 36, jt=2)
        if bar % 4 == 3:
            sc.hit(42, t + 2.5, 34, jt=2)
        sc.note(cd.CH_STRINGS, p0 + 12, t, 2.9, 40, jt=3, jv=2)
    waltz_b = [(d, s * 0.75, dur * 0.75) for d, s, dur in m.THEME_B]
    for st in (204.0, 228.0, 252.0):
        en.line(sc, cd.CH_FLUTE, st, n("A4"), MODE, waltz_b, 58,
                vel_end=64, gate=0.95, jt=3, jv=2)
        en.echo_throw(sc, cd.CH_FLUTE, st + 2.0, base=15, peak=78,
                      release=2.0)
    for t, deg in ((198.0, 8), (222.0, 10), (246.0, 12)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 2.0, 46,
                jt=3, jv=3)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=15, peak=72, release=2.0)


# ---------------------------------------------------------------------------
# IV. The Drop (264-344)
# ---------------------------------------------------------------------------

def the_drop(sc):
    t0 = 264.0
    for k in range(5):                             # pads, 8-beat harmony
        t = t0 + 16.0 * k
        root = m.GROUND_A[k % 4]
        for i, p in enumerate(en.voice_lead(
                en.triad(n("A2"), MODE, root), None, 4, n("E2"), n("A4"))):
            sc.note(cd.CH_PAD, p, t, 15.7, 44 - i, jt=4, jv=2)
        en.at_curve(sc, cd.CH_PAD, [(t, 0), (t + 8.0, 80), (t + 15.5, 0)],
                    step=0.5)

    # the theremin: RPN 12, whole-tone-scale-wide sighs
    ch = cd.CH_THEREMIN
    en.bend_range(sc, ch, 12, 266.0)
    en.portamento_on(sc, ch, 268.0, time_cc=76)
    sc.cc(ch, 11, 20, 268.0)
    notes = [(270.0, 69, 10.0), (282.0, 72, 8.0), (292.0, 67, 10.0),
             (304.0, 69, 12.0), (318.0, 74, 10.0), (330.0, 69, 10.0)]
    for beat, p, dur in notes:
        sc.note(ch, p, beat, dur, 56, jt=3, jv=2)
        en.expr_curve(sc, ch, [(beat, 20), (beat + dur * 0.6, 78),
                               (beat + dur, 24)], step=0.5)
    for t0b, t1b, s0, s1 in ((272.0, 276.0, 0.0, 5.0),
                             (277.0, 279.5, 5.0, 0.0),
                             (294.0, 298.0, 0.0, -4.0),
                             (299.0, 301.5, -4.0, 0.0),
                             (320.0, 324.0, 0.0, 5.0),
                             (325.0, 327.5, 5.0, 0.0)):
        en.bend_ramp(sc, ch, t0b, t1b, 2 * s0 / 12.0, 2 * s1 / 12.0,
                     steps=14)
    sc.bend(ch, 340.0, 0.0)
    en.portamento_off(sc, ch, 341.0)
    en.bend_range(sc, ch, 2, 343.0)

    ch = cd.CH_BASS
    en.portamento_on(sc, ch, 266.0, time_cc=68)
    for beat, deg, dur in ((268.0, 1, 12.0), (284.0, 0, 12.0),
                           (300.0, -1, 12.0), (316.0, 0, 12.0),
                           (332.0, 1, 10.0)):
        sc.note(ch, en.pitch(n("A1") + 12, MODE, deg), beat, dur, 52,
                jt=2, jv=2)
    en.portamento_off(sc, ch, 343.0)

    en.vowel_curve(sc, cd.CH_CHOIR, [(266.0, 10), (300.0, 88),
                                     (338.0, 30)], step=2.0)
    for t in (272.0, 296.0, 320.0):
        sc.note(cd.CH_CHOIR, n("C4"), t, 20.0, 46, jt=4, jv=2)
        sc.note(cd.CH_CHOIR, n("E4"), t, 20.0, 42, jt=4, jv=2)
        en.at_curve(sc, cd.CH_CHOIR, [(t, 0), (t + 10.0, 65),
                                      (t + 19.5, 0)], step=0.5)

    for t, deg in ((280.0, 5), (302.0, 3), (326.0, 8)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 2.5, 42,
                jt=4, jv=3)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=12, peak=70, release=3.0)

    beat = 296.0
    while beat < 336.0:
        sc.hit(36, beat, 48, jv=2)
        sc.hit(36, beat + 1.5, 38, jv=2)
        beat += 4.0
    b = 336.0
    while b < 343.9:
        sc.hit(38, b, int(lerp(30, 78, (b - 336.0) / 8.0)), jt=2, jv=3)
        b += 0.25
    en.cc_curve(sc, cd.CH_SEQ, 74, [(336.0, 25), (343.5, 100)], step=0.5)
    for i in range(10):
        sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE,
                                    1 + m.SEQ_LADDER[i % 8]),
                338.0 + i * 0.5, 0.4, int(lerp(40, 64, i / 9.0)), jt=2)


# ---------------------------------------------------------------------------
# V. Two Suns (344-488)
# ---------------------------------------------------------------------------

def two_suns(sc):
    t0, bars = 344.0, 36
    sc.hit(49, t0, 96, jv=2)
    sc.note(cd.CH_BELL, n("A3"), t0, 6.0, 62, jt=0, jv=2)
    _seq_bars(sc, t0, bars, m.GROUND_LIFT, 62, 72)
    sc.cc(cd.CH_SEQ, 74, 100, t0 - 0.1)
    en.autopan(sc, cd.CH_SEQ, t0, 142.0, lo=50, hi=98, period_beats=12.0,
               step=0.25)
    for bar in range(8, bars):                     # the 3-vs-4 shimmer
        t = t0 + 4.0 * bar
        root = m.GROUND_LIFT[bar % 4]
        for deg, s, dur in m.seq_cell(root, 12):
            sc.note(cd.CH_SEQ2, en.pitch(SEQ_BASE + 12, MODE, deg),
                    t + s * (4.0 / 3.0), dur * 1.2, 56, jt=1, jv=2)

    _bass_bars(sc, t0, bars, m.GROUND_LIFT, 80)
    for bar in range(3, bars, 4):                  # legato run turns
        t = t0 + 4.0 * bar + 2.0
        root = m.GROUND_LIFT[bar % 4]
        en.run(sc, cd.CH_BASS, t, BASS_BASE, MODE,
               [root, root + 2, root + 4, root + 5, root + 7], 0.4,
               72, 86, legato=True)

    _electro(sc, t0, bars, energy=2, fill_every=4)

    chords = [en.triad(n("A2"), MODE, m.GROUND_LIFT[b % 4])
              for b in range(bars)]
    en.pad_block(sc, cd.CH_PAD, t0, chords, span=4.0, size=4,
                 lo=n("E2"), hi=n("E4"), vel=46)
    en.pad_block(sc, cd.CH_ORGAN, t0, chords, span=4.0, size=3,
                 lo=n("A2"), hi=n("A4"), vel=48)
    en.leslie(sc, cd.CH_ORGAN, 346.0, 410.0, 8, 127)
    en.cc_curve(sc, cd.CH_ORGAN, 1, [(452.0, 127), (482.0, 40)], step=2.0)

    for bar in range(0, bars, 2):
        t = t0 + 4.0 * bar
        root = m.GROUND_LIFT[bar % 4]
        for i, p in enumerate(en.triad(n("A3"), MODE, root)):
            sc.note(cd.CH_EP, p, t + 1.5, 0.5, 58 - i * 2, jt=2, jv=2)
            sc.note(cd.CH_EP, p, t + 3.5, 0.5, 54 - i * 2, jt=2, jv=2)

    # theme statements: A alone, B alone, then the certified pair
    _theme(sc, cd.CH_LEAD, 376.0, m.THEME_A, 76)
    _theme(sc, cd.CH_LEAD, 392.0, m.THEME_A, 78)
    en.line(sc, cd.CH_FLUTE, 408.0, n("A4"), MODE, m.THEME_B, 66,
            vel_end=72, gate=0.95, jt=3, jv=2)
    en.line(sc, cd.CH_FLUTE, 424.0, n("A4"), MODE, m.THEME_B, 70,
            vel_end=74, gate=0.95, jt=3, jv=2)
    _theme(sc, cd.CH_LEAD, 440.0, m.THEME_A, 82)
    _theme(sc, cd.CH_LEAD, 456.0, m.THEME_A, 84)
    en.portamento_off(sc, cd.CH_LEAD, 486.0)
    for st in (440.0, 456.0):
        en.line(sc, cd.CH_FLUTE, st, n("A4"), MODE, m.THEME_B, 72,
                gate=0.95, jt=3, jv=2)
        en.line(sc, cd.CH_CHOIR, st, n("A3"), MODE, m.THEME_B, 60,
                gate=0.97, jt=4, jv=2)
        for deg, s, dur in m.THEME_A:
            sc.note(cd.CH_GLOCK, en.pitch(n("A5"), MODE, deg), st + s,
                    dur * 0.8, 54, jt=3, jv=3)
    en.vowel(sc, cd.CH_CHOIR, 85, 438.0)
    for t in (440.0, 456.0):
        en.at_curve(sc, cd.CH_CHOIR, [(t, 10), (t + 8.0, 85),
                                      (t + 15.5, 15)], step=0.5)

    for k in range(9):
        t = t0 + 16.0 * k
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, 1 + 2 * (k % 3)),
                t, 2.0, 56, jt=3, jv=3)


# ---------------------------------------------------------------------------
# VI. Dissolve (488-552)
# ---------------------------------------------------------------------------

def dissolve(sc):
    t0 = 488.0
    for bar in range(0, 12, 2):                    # the cell, thinning
        t = t0 + 4.0 * bar
        root = m.GROUND_A[bar % 4]
        for deg, s, dur in m.seq_cell(root, 16)[:8]:
            sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE, deg), t + s,
                    dur * 0.9, int(lerp(58, 40, bar / 11.0)), jt=2, jv=2)
    en.cc_curve(sc, cd.CH_SEQ, 74, [(488.0, 100), (540.0, 25)], step=4.0)

    for k in range(4):
        t = t0 + 16.0 * k
        for i, p in enumerate(PAD_VOICES):
            sc.note(cd.CH_PAD, p, t, 15.5, 42 - k * 2 - i, jt=4, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 20.0, 55), (548.0, 0)],
                step=0.5)

    beat = t0
    while beat < 536.0:
        sc.hit(36, beat, int(lerp(52, 34, (beat - t0) / 48.0)), jv=2)
        if beat + 1.5 < 536.0:
            sc.hit(36, beat + 1.5, int(lerp(42, 26, (beat - t0) / 48.0)),
                   jv=2)
        beat += 4.0

    en.portamento_on(sc, cd.CH_LEAD, 514.0, time_cc=55)
    en.line(sc, cd.CH_LEAD, 516.0, n("A4"), MODE, m.THEME_A[:4], 56,
            gate=1.0, jt=3, jv=2)
    en.bend_ramp(sc, cd.CH_LEAD, 523.4, 524.2, 0.0, -2.0, steps=8)
    sc.bend(cd.CH_LEAD, 524.8, 0.0)
    en.portamento_off(sc, cd.CH_LEAD, 526.0)
    en.echo_throw(sc, cd.CH_LEAD, 520.0, base=12, peak=80, release=3.0)

    en.vowel_curve(sc, cd.CH_CHOIR, [(500.0, 45), (536.0, 5)], step=4.0)
    sc.note(cd.CH_CHOIR, n("A3"), 500.0, 30.0, 40, jt=4, jv=2)
    sc.note(cd.CH_CHOIR, n("E4"), 500.0, 30.0, 36, jt=4, jv=2)

    for t, deg, v in ((508.0, 8, 44), (524.0, 5, 40), (536.0, 1, 36)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 3.0, v,
                jt=4, jv=2)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=10, peak=66, release=3.0)

    sc.note(cd.CH_BELL, n("A3"), 540.0, 8.0, 48, jt=2, jv=2)
    en.sustain(sc, cd.CH_EP, 543.9, 551.0)
    for i, p in enumerate((n("A2"), n("E3"), n("A3"), n("B3"), n("C4"))):
        sc.note(cd.CH_EP, p, 544.0, 6.5, 46 - i * 2, jt=2, jv=2)
    sc.note(cd.CH_STRINGS, n("A2"), 540.0, 10.0, 38, jt=3, jv=2)
