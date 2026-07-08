"""p2 — the six movements of *Heliopause, Part Two* (A aeolian, 126).

The mirror half: brighter, faster, in 6/8 for most of its run.  The
lead melody is Part One's THEME_A turned upside down (oracle-verified
diatonic mirror); Perihelion stacks the original, its answer and its
inversion — the certified triple counterpoint — over the Part One
ground while two sequencers run 16-against-12.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from movements.p1 import (_seq_bars, _bass_bars, _theme, _electro,
                          BASS_BASE, LEAD_BASE, SEQ_BASE, PAD_VOICES)
from engine import lerp, n

MODE = m.MODE

SLIP_ROOTS = [1, 1, 7, 7, 6, 6, 7, 7]   # the pedal drift, 2 bars a chord


def _shuffle_drums(sc, t0, bars, energy=2, fill_every=16):
    """The 6/8 floor: kick on the compound beats, snare answering."""
    base = 62 + 8 * energy
    for bar in range(bars):
        t = t0 + 3.0 * bar
        fill_bar = fill_every and bar % fill_every == fill_every - 1
        sc.hit(36, t, base + 6)
        sc.hit(36, t + 1.5 if energy < 2 else t + 1.0, base - 12)
        sc.hit(38, t + 1.5, base + 2)
        span = 2.0 if fill_bar else 3.0
        for s in range(int(span * 2)):
            v = base - (12 if s % 3 == 0 else 26)
            sc.hit(42, t + s * 0.5, v, jt=2, jv=3)
        if fill_bar:
            for i, drum in enumerate((50, 47, 45, 41)):
                sc.hit(drum, t + 2.0 + i * 0.25, base + 2 + 2 * i, jt=2)
        elif energy >= 2 and bar % 2 == 1:
            sc.hit(46, t + 2.5, base - 16, jt=2)


def _bass_68(sc, t0, bars, roots, vel):
    cell = [(0, 0.0, 0.5), (7, 0.5, 0.5), (0, 1.0, 0.5), (4, 1.5, 0.5),
            (0, 2.0, 0.5), (7, 2.5, 0.5)]
    for bar in range(bars):
        t = t0 + 3.0 * bar
        root = roots[(bar // 2) % len(roots)] if roots is SLIP_ROOTS \
            else roots[bar % len(roots)]
        for deg, s, dur in cell:
            sc.note(cd.CH_BASS, en.pitch(BASS_BASE, MODE, root + deg),
                    t + s, dur * 0.9, vel + (4 if s == 0.0 else 0),
                    jt=1, jv=2)


# ---------------------------------------------------------------------------
# I. Ignition (0-36)
# ---------------------------------------------------------------------------

def ignition(sc):
    for i, p in enumerate(PAD_VOICES):
        sc.note(cd.CH_PAD, p, 0.0, 35.5, 42 - i, jt=3, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(0.0, 0), (18.0, 80), (34.0, 20)],
                step=0.5)
    en.cc_curve(sc, cd.CH_SEQ, 74, [(8.0, 20), (35.0, 100)], step=1.0)
    for i in range(44):                            # the cell spins up
        b = 8.0 + i * 0.5
        if b >= 35.5:
            break
        deg = 1 + m.SEQ_LADDER[i % 8]
        sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE, deg), b, 0.4,
                int(lerp(36, 66, i / 43.0)), jt=2, jv=2)
    for t, deg in ((6.0, 12), (14.0, 10), (22.0, 12), (28.0, 14)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 0.8, 58,
                jt=2, jv=3)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=15, peak=85, release=1.5)
    b = 16.0
    while b < 35.9:                                # kick accelerando
        step = 1.0 if b < 24.0 else 0.5 if b < 32.0 else 0.25
        sc.hit(36, b, int(lerp(50, 84, (b - 16.0) / 20.0)), jt=1)
        b += step
    sc.note(cd.CH_BASS, n("A1") + 12, 16.0, 19.5, 62, jt=2, jv=2)
    en.expr_curve(sc, cd.CH_STRINGS, [(20.0, 0), (34.0, 70)], step=1.0)
    sc.note(cd.CH_STRINGS, n("A2"), 20.0, 15.5, 50, jt=3, jv=2)
    sc.note(cd.CH_STRINGS, n("E3"), 20.0, 15.5, 46, jt=3, jv=2)


# ---------------------------------------------------------------------------
# II. Slipstream (36-180) — 6/8
# ---------------------------------------------------------------------------

def slipstream(sc):
    t0, bars = 36.0, 48
    sc.hit(49, t0, 94, jv=2)
    for bar in range(bars):
        t = t0 + 3.0 * bar
        root = SLIP_ROOTS[(bar // 2) % 4] if False else \
            SLIP_ROOTS[bar % 8]
        vel = int(lerp(58, 70, bar / (bars - 1)))
        for deg, s, dur in m.seq_cell(root, 12):
            sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE, deg), t + s,
                    dur * 0.9, vel + (6 if s == 0.0 else 0), jt=1, jv=2)
    en.wah(sc, cd.CH_SEQ, t0, 142.0, lo=38, hi=105,
           cycles_per_beat=1 / 12.0, step=0.5)
    en.autopan(sc, cd.CH_SEQ, t0, 142.0, lo=52, hi=96, period_beats=18.0,
               step=0.25)

    _bass_68(sc, t0, bars, SLIP_ROOTS, 74)
    _shuffle_drums(sc, t0 + 12.0, bars - 4, energy=2, fill_every=16)

    for bar in range(0, bars, 2):                  # EP colour
        t = t0 + 3.0 * bar
        root = SLIP_ROOTS[bar % 8]
        for i, p in enumerate(en.triad(n("A3"), MODE, root)):
            sc.note(cd.CH_EP, p, t, 2.8, 48 - i * 2, jt=3, jv=2)

    _theme(sc, cd.CH_LEAD, 72.0, m.THEME_A_INV, 72)
    _theme(sc, cd.CH_LEAD, 120.0, m.THEME_A_INV, 76)
    en.portamento_off(sc, cd.CH_LEAD, 140.0)
    for deg, s, dur in m.THEME_A_INV:
        sc.note(cd.CH_GLOCK, en.pitch(n("A5"), MODE, deg), 120.0 + s,
                dur * 0.8, 50, jt=3, jv=3)
    inv_frag = m.THEME_A_INV[:3]
    for st in (96.0, 144.0):
        en.line(sc, cd.CH_FLUTE, st, n("A4"), MODE, inv_frag, 56,
                gate=0.95, jt=3, jv=2)
        en.echo_throw(sc, cd.CH_FLUTE, st, base=15, peak=75, release=2.0)

    en.expr_curve(sc, cd.CH_STRINGS, [(108.0, 0), (140.0, 60),
                                      (176.0, 72)], step=2.0)
    sc.note(cd.CH_STRINGS, n("A2"), 108.0, 70.0, 46, jt=3, jv=2)
    sc.note(cd.CH_STRINGS, n("E3"), 108.0, 70.0, 42, jt=3, jv=2)
    en.vowel(sc, cd.CH_CHOIR, 40, 143.0)
    sc.note(cd.CH_CHOIR, n("A3"), 144.0, 34.0, 42, jt=4, jv=2)
    sc.note(cd.CH_CHOIR, n("C4"), 144.0, 34.0, 38, jt=4, jv=2)


# ---------------------------------------------------------------------------
# III. Crosswind (180-228) — the 4/4 stomp
# ---------------------------------------------------------------------------

def crosswind(sc):
    t0, bars = 180.0, 12
    sc.hit(49, t0, 98, jv=2)
    _seq_bars(sc, t0, bars, m.GROUND_B2, 66, 74)
    sc.cc(cd.CH_SEQ, 71, 92, t0)
    for bar in range(bars):                        # 12-slot against 16
        t = t0 + 4.0 * bar
        root = m.GROUND_B2[bar % 4]
        for deg, s, dur in m.seq_cell(root, 12):
            sc.note(cd.CH_SEQ2, en.pitch(SEQ_BASE + 12, MODE, deg),
                    t + s * (4.0 / 3.0), dur * 1.2, 58, jt=1, jv=2)
    _bass_bars(sc, t0, bars, m.GROUND_B2, 80)
    _electro(sc, t0, bars, energy=3, fill_every=4)
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.GROUND_B2[bar % 4]
        for i, p in enumerate(en.triad(n("A3"), MODE, root)):
            sc.note(cd.CH_ORGAN, p, t, 0.5, 60 - i * 2, jt=2, jv=2)
            sc.note(cd.CH_ORGAN, p, t + 2.5, 0.4, 54 - i * 2, jt=2, jv=2)
    # the one-beat stop: everything holds its breath, then the crash
    sc.hit(49, 204.0, 100, jv=2)


# ---------------------------------------------------------------------------
# IV. Eclipse (228-276) — 6/8 drop
# ---------------------------------------------------------------------------

def eclipse(sc):
    t0 = 228.0
    for k in range(3):
        t = t0 + 16.0 * k
        for i, p in enumerate(PAD_VOICES):
            sc.note(cd.CH_PAD, p, t, 15.5, 42 - i, jt=4, jv=2)
        en.at_curve(sc, cd.CH_PAD, [(t, 0), (t + 8.0, 78), (t + 15.0, 0)],
                    step=0.5)
    en.vowel_curve(sc, cd.CH_CHOIR, [(t0, 10), (250.0, 85), (272.0, 40)],
                   step=2.0)
    for t in (232.0, 252.0):
        sc.note(cd.CH_CHOIR, n("C4"), t, 18.0, 46, jt=4, jv=2)
        sc.note(cd.CH_CHOIR, n("E4"), t, 18.0, 42, jt=4, jv=2)
        en.at_curve(sc, cd.CH_CHOIR, [(t, 0), (t + 9.0, 70),
                                      (t + 17.5, 0)], step=0.5)
    slow_a = [(d, s * 1.5, dur * 1.5) for d, s, dur in m.THEME_A]
    en.portamento_on(sc, cd.CH_LEAD, 230.0, time_cc=70)
    en.line(sc, cd.CH_LEAD, 232.0, LEAD_BASE, MODE, slow_a, 58,
            vel_end=64, gate=1.0, jt=3, jv=2)
    en.cc_curve(sc, cd.CH_LEAD, 1, [(238.0, 0), (246.0, 75), (254.0, 0)],
                step=0.25)
    en.portamento_off(sc, cd.CH_LEAD, 258.0)
    en.echo_throw(sc, cd.CH_LEAD, 244.0, base=15, peak=82, release=3.0)
    sc.note(cd.CH_BASS, n("A1") + 12, 232.0, 22.0, 48, jt=2, jv=2)
    sc.note(cd.CH_BASS, en.pitch(n("A1") + 12, MODE, 6), 256.0, 14.0, 46,
            jt=2, jv=2)
    beat = 240.0
    while beat < 268.0:
        sc.hit(36, beat, 44, jv=2)
        sc.hit(36, beat + 1.5, 34, jv=2)
        beat += 6.0
    for t, deg in ((242.0, 8), (258.0, 5)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 2.5, 42,
                jt=4, jv=3)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=12, peak=70, release=3.0)
    b = 270.0
    while b < 275.9:
        sc.hit(38, b, int(lerp(28, 80, (b - 270.0) / 6.0)), jt=2, jv=3)
        b += 0.25
    en.cc_curve(sc, cd.CH_SEQ, 74, [(270.0, 25), (275.5, 105)], step=0.5)


# ---------------------------------------------------------------------------
# V. Perihelion (276-404) — the triple stack
# ---------------------------------------------------------------------------

def perihelion(sc):
    t0, bars = 276.0, 32
    sc.hit(49, t0, 100, jv=2)
    sc.note(cd.CH_BELL, n("A3"), t0, 6.0, 64, jt=0, jv=2)
    _seq_bars(sc, t0, bars, m.GROUND_A, 64, 74)
    sc.cc(cd.CH_SEQ, 74, 104, t0 - 0.1)
    en.cc_curve(sc, cd.CH_SEQ, 71, [(276.0, 60), (340.0, 95),
                                    (402.0, 70)], step=4.0)
    en.autopan(sc, cd.CH_SEQ, t0, 126.0, lo=50, hi=98, period_beats=12.0,
               step=0.25)
    en.fine_tune(sc, cd.CH_SEQ2, 6.0, 278.0)
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.GROUND_A[bar % 4]
        for deg, s, dur in m.seq_cell(root, 12):
            sc.note(cd.CH_SEQ2, en.pitch(SEQ_BASE + 12, MODE, deg),
                    t + s * (4.0 / 3.0), dur * 1.2, 58, jt=1, jv=2)
    en.fine_tune(sc, cd.CH_SEQ2, 0.0, 402.0)

    _bass_bars(sc, t0, bars, m.GROUND_A, 82)
    for bar in range(3, bars, 4):
        t = t0 + 4.0 * bar + 2.0
        root = m.GROUND_A[bar % 4]
        en.run(sc, cd.CH_BASS, t, BASS_BASE, MODE,
               [root, root + 2, root + 4, root + 5, root + 7], 0.4,
               74, 88, legato=True)
    _electro(sc, t0, bars, energy=3, fill_every=4)

    chords = [en.triad(n("A2"), MODE, m.GROUND_A[b % 4])
              for b in range(bars)]
    en.pad_block(sc, cd.CH_PAD, t0, chords, span=4.0, size=4,
                 lo=n("E2"), hi=n("E4"), vel=48)
    en.pad_block(sc, cd.CH_ORGAN, t0, chords, span=4.0, size=3,
                 lo=n("A2"), hi=n("A4"), vel=50)
    en.leslie(sc, cd.CH_ORGAN, 278.0, 330.0, 8, 127)
    en.cc_curve(sc, cd.CH_ORGAN, 1, [(380.0, 127), (400.0, 40)], step=2.0)

    # the stack, growing: A+B, A+INV, then ALL THREE twice
    _theme(sc, cd.CH_LEAD, 292.0, m.THEME_A, 76)
    en.line(sc, cd.CH_FLUTE, 292.0, n("A4"), MODE, m.THEME_B, 64,
            gate=0.95, jt=3, jv=2)
    _theme(sc, cd.CH_LEAD, 324.0, m.THEME_A, 78)
    en.line(sc, cd.CH_THEREMIN, 324.0, n("A4") + 12, MODE, m.THEME_A_INV,
            60, gate=0.97, jt=3, jv=2)
    for st in (356.0, 372.0):
        _theme(sc, cd.CH_LEAD, st, m.THEME_A, 84)
        en.line(sc, cd.CH_FLUTE, st, n("A4"), MODE, m.THEME_B, 72,
                gate=0.95, jt=3, jv=2)
        en.line(sc, cd.CH_THEREMIN, st, n("A4") + 12, MODE,
                m.THEME_A_INV, 64, gate=0.97, jt=3, jv=2)
        for deg, s, dur in m.THEME_A_INV:
            sc.note(cd.CH_GLOCK, en.pitch(n("A5"), MODE, deg), st + s,
                    dur * 0.8, 54, jt=3, jv=3)
        en.line(sc, cd.CH_CHOIR, st, n("A3"), MODE, m.THEME_B, 58,
                gate=0.97, jt=4, jv=2)
    en.portamento_off(sc, cd.CH_LEAD, 402.0)
    en.vowel(sc, cd.CH_CHOIR, 85, 354.0)
    for t in (356.0, 372.0):
        en.at_curve(sc, cd.CH_CHOIR, [(t, 10), (t + 8.0, 85),
                                      (t + 15.5, 15)], step=0.5)
    for k in range(8):
        t = t0 + 16.0 * k
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, 1 + 2 * (k % 3)),
                t, 1.5, 58, jt=3, jv=3)


# ---------------------------------------------------------------------------
# VI. Afterimage (404-460)
# ---------------------------------------------------------------------------

def afterimage(sc):
    t0 = 404.0
    for bar in range(0, 10, 2):
        t = t0 + 4.0 * bar
        root = m.GROUND_A[bar % 4]
        for deg, s, dur in m.seq_cell(root, 16)[:8]:
            sc.note(cd.CH_SEQ, en.pitch(SEQ_BASE, MODE, deg), t + s,
                    dur * 0.9, int(lerp(56, 38, bar / 9.0)), jt=2, jv=2)
    en.cc_curve(sc, cd.CH_SEQ, 74, [(404.0, 104), (450.0, 22)], step=4.0)

    for k in range(3):
        t = t0 + 16.0 * k
        for i, p in enumerate(PAD_VOICES):
            sc.note(cd.CH_PAD, p, t, 15.5, 40 - k * 2 - i, jt=4, jv=2)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 16.0, 50), (456.0, 0)],
                step=0.5)

    en.portamento_on(sc, cd.CH_BASS, 424.0, time_cc=66)
    sc.note(cd.CH_BASS, en.pitch(n("A1") + 12, MODE, 5), 426.0, 6.0, 46,
            jt=2, jv=2)
    sc.note(cd.CH_BASS, n("A1") + 12, 434.0, 16.0, 44, jt=2, jv=2)
    en.portamento_off(sc, cd.CH_BASS, 456.0)

    beat = t0 + 4.0
    while beat < 448.0:
        sc.hit(36, beat, int(lerp(46, 30, (beat - t0) / 44.0)), jv=2)
        sc.hit(36, beat + 1.5, int(lerp(36, 24, (beat - t0) / 44.0)),
               jv=2)
        beat += 6.0

    en.vowel_curve(sc, cd.CH_CHOIR, [(416.0, 40), (448.0, 5)], step=4.0)
    sc.note(cd.CH_CHOIR, n("A3"), 416.0, 28.0, 38, jt=4, jv=2)
    sc.note(cd.CH_CHOIR, n("E4"), 416.0, 28.0, 34, jt=4, jv=2)

    for t, deg, v in ((420.0, 8, 44), (436.0, 5, 40), (448.0, 1, 36)):
        sc.note(cd.CH_CRYSTAL, en.pitch(n("A5"), MODE, deg), t, 3.0, v,
                jt=4, jv=2)
        en.echo_throw(sc, cd.CH_CRYSTAL, t, base=10, peak=64, release=3.0)

    sc.note(cd.CH_BELL, n("A3"), 448.0, 8.0, 46, jt=2, jv=2)
    en.sustain(sc, cd.CH_EP, 451.9, 459.0)
    for i, p in enumerate((n("A2"), n("E3"), n("A3"), n("B3"), n("C4"))):
        sc.note(cd.CH_EP, p, 452.0, 6.0, 44 - i * 2, jt=2, jv=2)
    sc.note(cd.CH_STRINGS, n("A2"), 446.0, 12.0, 36, jt=3, jv=2)
