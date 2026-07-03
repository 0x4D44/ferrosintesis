"""part_two.py — Hollow Hill, Part Two (~12.5 minutes).

    I.   Green Morning       pastoral picking, the theme in the major
    II.  The Dance Under the Hill   a 6/8 jig, key lifting D to E
    III. Stone Voices        a phrygian chant over drones and a slow drum
    IV.  The Night Ocean     the second ambient pool (with a hidden message)
    V.   The Return          the 13/8 ostinato reborn in E major — the summit
    VI.  (a false ending)    ...three seconds of silence...
    VII. The Hollow Hill Reel   a fast folk finale that won't sit still
"""

import engine as en
import material as m
from engine import lerp, n

IONIAN, PHRYGIAN = "ionian", "phrygian"


def setup(sc):
    sc.channel(0, "Grand Piano", 0, volume=105, pan=54)
    sc.channel(1, "Glockenspiel", 9, volume=85, pan=76, reverb=70)
    sc.channel(2, "Tubular Bells", 14, volume=110, pan=64, reverb=80)
    sc.channel(3, "Bass Guitar", 33, volume=105, pan=64, reverb=25)
    sc.channel(4, "Organ", 19, volume=72, pan=58)
    sc.channel(5, "Strings", 49, volume=80, pan=60, reverb=75)
    sc.channel(6, "Choir", 52, volume=85, pan=68, reverb=80)
    sc.channel(7, "Steel Guitar", 25, volume=92, pan=40)
    sc.channel(8, "Nylon Guitar", 24, volume=94, pan=88)
    sc.channel(9, "Percussion", 0, volume=100)
    sc.channel(10, "Lead Guitar", 27, volume=98, pan=60, reverb=60)
    sc.channel(11, "Flute", 73, volume=90, pan=70, reverb=70)
    sc.channel(12, "Fiddle", 40, volume=92, pan=48, reverb=60)
    sc.channel(13, "Pad", 89, volume=72, pan=64, reverb=95)
    sc.channel(14, "Harp", 46, volume=82, pan=80, reverb=80)
    sc.channel(15, "Banjo", 105, volume=88, pan=34, reverb=40)


# ---------------------------------------------------------------------------
# I. Green Morning — D major, guitars picking, the theme now smiling.
# ---------------------------------------------------------------------------
def green_morning(sc, t):
    sc.tempo(t, 84)
    sc.timesig(t, 4, 4)
    sc.marker(t, "I. Green Morning")
    D3, D4, D2 = n("D3"), n("D4"), n("D2")
    bars = 48
    harm = [0, 0, 3, 3, 4, 4, 0, 0, 5, 5, 3, 3, 4, 4, 0, 0]
    pick = (0, 1, 2, 3, 2, 1, 3, 2)
    for bar in range(bars):
        s = harm[bar % 16]
        b = t + bar * 4
        grow = bar / bars
        tones = en.triad(D3, IONIAN, 1 + s, 4)
        for k in range(8):
            sc.note(8, tones[pick[k]], b + k * 0.5, 0.55,
                    int(lerp(52, 66, grow)) + (6 if k == 0 else 0), jt=5)
        if bar >= 8:
            sc.note(7, en.pitch(D4, IONIAN, 9 + s), b + 1.5, 0.8, 48, jt=5)
            sc.note(7, en.pitch(D4, IONIAN, 8 + s), b + 3.5, 0.8, 44, jt=5)
        if bar >= 16:
            pattern = m.BASS_MORNING_A if bar % 2 == 0 else m.BASS_MORNING_B
            en.line(sc, 3, b, D2, IONIAN, pattern,
                    int(lerp(58, 74, grow)), shift=s, jt=4)
            en.pad_block(sc, 5, b, [en.triad(D4, IONIAN, 1 + s, 4)], 4.0,
                         size=4, lo=57, hi=79, vel=int(lerp(30, 52, grow)))
        if bar >= 32:
            sc.note(1, en.pitch(n("D5"), IONIAN, 1 + s), b, 1.0, 44, jt=4)
            sc.hit(81, b, 30)
            for k in range(8):
                sc.hit(70, b + k * 0.5, 36 if k % 2 == 0 else 24)
            # clean electric answers, each note with a soft echo
            for beat, deg in ((2.5, 10), (3.5, 9)):
                p = en.pitch(D4, IONIAN, deg + s)
                sc.note(10, p, b + beat, 0.8, 42, jt=5)
                sc.note(10, p, b + beat + 0.75, 0.7, 28, jt=5)
        if bar % 8 == 0 and bar >= 8:      # harp sweep at each turn
            for k in range(15):
                sc.note(14, en.pitch(D3, IONIAN, 1 + s + k), b + k * 0.12,
                        1.8, int(lerp(40, 58, k / 14)), jt=2)
    en.line(sc, 11, t + 8 * 4, D4, IONIAN, m.THEME, 66, vel_end=76, octave=1)
    en.line(sc, 12, t + 24 * 4, D4, IONIAN, m.THEME, 74, vel_end=84)
    en.line(sc, 11, t + 40 * 4, D4, IONIAN, m.THEME, 74, vel_end=84, octave=1)
    en.line(sc, 12, t + 40 * 4, D4, IONIAN, m.THEME, 78, vel_end=88)
    en.expr_curve(sc, 5, [(t, 50), (t + bars * 4, 90)], step=2)
    return t + bars * 4


# ---------------------------------------------------------------------------
# II. The Dance Under the Hill — a jig; halfway through, the key lifts.
# ---------------------------------------------------------------------------
def dance(sc, t):
    sc.tempo(t, 126)
    sc.timesig(t, 6, 8)
    sc.marker(t, "II. The Dance Under the Hill")
    sc.program(11, 78, t)              # tin whistle
    bars = 80
    harm = [0, 0, 3, 4]
    for bar in range(bars):
        lift = 2 if bar >= 48 else 0   # D up to E
        D3, D2 = n("D3") + lift, n("D2") + lift
        s = harm[bar % 4]
        b = t + bar * 3
        grow = bar / bars
        chord = en.triad(D3, IONIAN, 1 + s, 3) + [en.pitch(D3, IONIAN, 8 + s)]
        en.strum(sc, 7, chord, b, 1.3, int(lerp(58, 76, grow)), spread=0.025)
        en.strum(sc, 7, chord, b + 1.5, 1.2, int(lerp(52, 70, grow)),
                 spread=0.025, down=False)
        root = en.pitch(D2, IONIAN, 1 + s)
        sc.note(3, root, b, 1.4, int(lerp(60, 78, grow)), jt=3)
        sc.note(3, root + 7, b + 1.5, 1.3, int(lerp(54, 72, grow)), jt=3)
        # bodhran-ish toms and ticks
        sc.hit(41, b, int(lerp(58, 78, grow)))
        sc.hit(45, b + 1.5, int(lerp(50, 68, grow)))
        for beat in (1.0, 2.0, 2.5):
            sc.hit(43, b + beat, int(lerp(34, 50, grow)))
        if bar >= 16:
            sc.hit(54, b + 1.5, int(lerp(44, 62, grow)))
        if bar >= 32:
            for k in range(6):
                sc.hit(70, b + k * 0.5, 36 if k % 3 == 0 else 24)
        if bar >= 48:
            sc.hit(36, b, int(lerp(66, 82, grow)))
            if bar % 4 == 0:
                sc.hit(49, b, 72)
    # tune statements: fiddle, whistle, then both in thirds; tutti after lift
    D4 = n("D4")
    # 20 strains of 4 bars = exactly 80 bars; the key lifts at rep 12 (bar 48)
    # together with the accompaniment above.
    plan = ((12, m.JIG_A, 0, 0), (12, m.JIG_A, 0, 0),
            (11, m.JIG_B, 0, 1), (11, m.JIG_B, 0, 1),
            (12, m.JIG_A, 2, 0), (12, m.JIG_B, 2, 0),
            (12, m.JIG_A, 2, 0), (12, m.JIG_B, 2, 0),
            (12, m.JIG_A, 2, 0), (12, m.JIG_A, 2, 0),
            (12, m.JIG_B, 2, 0), (12, m.JIG_B, 2, 0),
            (12, m.JIG_A, 2, 0), (12, m.JIG_A, 2, 0),
            (12, m.JIG_B, 2, 0), (12, m.JIG_B, 2, 0),
            (12, m.JIG_A, 2, 0), (12, m.JIG_B, 2, 0),
            (12, m.JIG_A, 2, 0), (12, m.JIG_B, 2, 0))
    for rep, (ch, strain, third, octv) in enumerate(plan):
        b = t + rep * 12               # each strain is 4 bars = 12 beats
        base = D4 + (2 if rep >= 12 else 0)
        vel = int(lerp(72, 92, rep / len(plan)))
        en.line(sc, ch, b, base, IONIAN, strain, vel, octave=octv, gate=0.92)
        if third:                      # companion voice a third above
            other = 11 if ch == 12 else 12
            en.line(sc, other, b, base, IONIAN, strain, vel - 10,
                    shift=third, octave=1, gate=0.9)
        if rep >= 16:                  # glockenspiel joins the last lap
            en.line(sc, 1, b, base, IONIAN,
                    [nt for i, nt in enumerate(strain) if i % 2 == 0],
                    54, octave=1, gate=0.8)
    # full stop: one big hit, then the hill goes quiet
    bend = t + bars * 3
    sc.hit(49, bend - 1.5, 92)
    sc.hit(36, bend - 1.5, 92)
    return bend + 3


# ---------------------------------------------------------------------------
# III. Stone Voices — the chant. Low, patient, a little uncanny.
# ---------------------------------------------------------------------------
def stone_voices(sc, t):
    sc.tempo(t, 96)
    sc.timesig(t, 4, 4)
    sc.marker(t, "III. Stone Voices")
    E3, E2 = n("E3"), n("E2")
    bars = 40
    for blk in range(bars // 4):       # drones in 4-bar breaths
        b = t + blk * 16
        sc.note(3, E2, b, 15.5, 56, jt=3)
        if blk >= 2:
            sc.note(4, E2, b, 15.8, 44, jt=3)
            sc.note(4, E2 + 7, b, 15.8, 38, jt=3)
        if blk >= 6:
            en.pad_block(sc, 5, b, [en.triad(E3, PHRYGIAN, 1, 3)], 16.0,
                         size=3, lo=48, hi=67, vel=44)
    for bar in range(bars):
        b = t + bar * 4
        grow = bar / bars
        if bar >= 4:                   # the heartbeat
            sc.hit(41, b, int(lerp(48, 70, grow)))
            sc.hit(41, b + 2.5, int(lerp(38, 58, grow)))
        if bar >= 16:
            sc.hit(75, b + 1.5, int(lerp(30, 48, grow)))
            sc.hit(75, b + 3.25, int(lerp(26, 42, grow)))
        if bar % 8 == 0:
            sc.hit(81, b, 32)
    # chant statements, organum building up
    en.line(sc, 6, t + 4, E3, PHRYGIAN, m.CHANT, 58, gate=1.02)
    en.line(sc, 6, t + 36, E3, PHRYGIAN, m.CHANT, 62, gate=1.02)
    en.line(sc, 6, t + 36, E3, PHRYGIAN, m.CHANT, 52, shift=4, gate=1.02)
    en.line(sc, 6, t + 68, E3, PHRYGIAN, m.CHANT, 66, gate=1.02)
    en.line(sc, 6, t + 68, E3, PHRYGIAN, m.CHANT, 56, shift=4, gate=1.02)
    en.line(sc, 6, t + 68, E3, PHRYGIAN, m.CHANT, 54, octave=1, gate=1.02)
    en.line(sc, 6, t + 100, E3, PHRYGIAN, m.CHANT, 70, gate=1.02)
    en.line(sc, 6, t + 100, E3, PHRYGIAN, m.CHANT, 60, shift=4, gate=1.02)
    en.line(sc, 6, t + 100, E3, PHRYGIAN, m.CHANT, 58, octave=1, gate=1.02)
    en.line(sc, 0, t + 100, E3, PHRYGIAN, m.CHANT, 54, octave=-1, gate=1.0)
    for bar in (24, 28, 32, 36):       # the bell tolls through the last verses
        sc.note(2, n("E4"), t + bar * 4, 6.0, 72, jt=2)
    en.expr_curve(sc, 6, [(t, 70), (t + 132, 105), (t + bars * 4, 60)], step=2)
    return t + bars * 4


# ---------------------------------------------------------------------------
# IV. The Night Ocean — the second pool; listen for the woodblock.
# ---------------------------------------------------------------------------
def night_ocean(sc, t):
    sc.tempo(t, 60)
    sc.marker(t, "IV. The Night Ocean")
    sc.program(14, 8, t)               # celesta takes the harp channel
    sc.program(1, 98, t)               # crystal takes the glockenspiel channel
    sc.program(3, 35, t)               # fretless bass
    sc.program(4, 95, t)               # sweep pad
    A2, A3, A4 = n("A2"), n("A3"), n("A4")
    bars = 40
    shifts = [0, 3, 5, 4, 0, 3, 5, 4, 0, 4]
    chords = [en.triad(A3, IONIAN, 1 + s, 4) for s in shifts]
    en.pad_block(sc, 13, t, chords, 16.0, size=4, lo=52, hi=78, vel=52)
    for i, s in enumerate(shifts):
        b = t + i * 16
        root = en.pitch(A2 - 12, IONIAN, 1 + s)
        en.line(sc, 3, b, A2 - 12, IONIAN, m.BASS_SLOW, 56, shift=s, jt=4)
        if i % 2 == 0:
            sc.note(4, root + 12, b, 32.0, 38, jt=3)
            sc.note(4, root + 19, b, 32.0, 32, jt=3)
        if 1 <= i < 9:                    # clean guitar arpeggio, left ringing
            tones = en.triad(A3, IONIAN, 1 + s, 4)
            for k, beat in enumerate((0.0, 1.5, 3.0, 4.5)):
                sc.note(10, tones[k] + 12, b + beat, 3.0, 36, jt=6)
        if i >= 4:
            croot = en.pitch(A3, IONIAN, 1 + s)
            sc.note(6, croot, b, 16.0, 40, jt=4)
            sc.note(6, croot + 7, b, 16.0, 36, jt=4)
    for bar in range(bars):
        if bar % 2 == 1:
            s = shifts[bar // 4]
            high = en.triad(n("A5"), IONIAN, 1 + s, 4)
            en.arp(sc, 1, high, t + bar * 4, 6, 0.667, 32, pattern="down", gate=2.2)
        if 16 <= bar < 32:
            sc.hit(36, t + bar * 4, 26, jv=2)
            sc.hit(36, t + bar * 4 + 2, 22, jv=2)
    en.line(sc, 14, t + 8 * 4, A4, IONIAN, m.BELL, 52, gate=1.4)
    en.line(sc, 14, t + 24 * 4, A4, IONIAN, m.BELL, 48, gate=1.4, octave=1)
    # the hidden message, tapped far away on a woodblock
    en.morse(sc, "ARTHUR", t + 20 * 4, unit=0.25, drum=76, vel=34)
    en.expr_curve(sc, 13, [(t, 40), (t + 40, 85), (t + 128, 85), (t + bars * 4, 100)], step=2)
    en.expr_curve(sc, 4, [(t, 30), (t + 64, 65), (t + bars * 4, 90)], step=2)
    sc.note(2, n("E5"), t + bars * 4 - 4, 4.0, 60, jt=0)   # the bell turns us home
    return t + bars * 4


# ---------------------------------------------------------------------------
# V. The Return — the ostinato reborn in E major, and the summit.
# ---------------------------------------------------------------------------
def the_return(sc, t):
    sc.tempo(t, 96)
    sc.timesig(t, 13, 8)
    sc.marker(t, "V. The Return")
    sc.program(1, 9, t)                # glockenspiel back
    sc.program(3, 33, t)
    sc.program(4, 19, t)
    sc.program(10, 29, t)              # overdriven lead
    sc.cc(13, 11, 60, t)
    sc.tempo(t + 16 * m.CYCLE, 100)
    sc.tempo(t + 24 * m.CYCLE, 104)
    E4, E2, E3 = n("E4"), n("E2"), n("E3")
    harm = [0, 0, 3, 3, 0, 0, 5, 4]
    cycles = 32
    for c in range(cycles):
        s = harm[c % 8] if c < 28 else (3, 4, 3, 4)[c % 4]
        b = t + c * m.CYCLE
        grow = c / cycles
        m.ostinato_cycle(sc, 0, b, E4, IONIAN, s, vel=int(lerp(66, 84, grow)))
        if c >= 4:
            m.ostinato_cycle(sc, 1, b, E4, IONIAN, s, vel=int(lerp(42, 58, grow)),
                             octave=1, only_accents=(c < 12), jv=3)
            pattern = m.BASS_CALM if c < 16 else m.BASS_WALK
            en.line(sc, 3, b, E2, IONIAN, pattern,
                    int(lerp(66, 88, grow)), shift=s, jt=3)
        if c >= 8:                     # the 13/8 kit: 3+3+3+2+2
            sc.hit(36, b, int(lerp(72, 92, grow)))
            sc.hit(38, b + 1.5, int(lerp(70, 90, grow)))
            sc.hit(36, b + 3, int(lerp(66, 86, grow)))
            sc.hit(38, b + 4.5, int(lerp(72, 92, grow)))
            sc.hit(36, b + 5.5, int(lerp(60, 80, grow)))
            for k in range(13):
                sc.hit(42, b + k * 0.5, int((52 if k in m.OST_ACCENTS else 36) * (0.7 + 0.3 * grow)))
            chord = en.triad(E3, IONIAN, 1 + s, 4)
            en.strum(sc, 7, chord, b, 1.4, int(lerp(56, 74, grow)), spread=0.025)
            en.strum(sc, 7, chord, b + 3, 1.4, int(lerp(52, 70, grow)), spread=0.025)
            en.strum(sc, 7, chord, b + 4.5, 1.9, int(lerp(52, 70, grow)), spread=0.025)
        if c >= 12:
            en.pad_block(sc, 4, b, [en.triad(E3, IONIAN, 1 + s, 4)], m.CYCLE,
                         size=3, lo=52, hi=74, vel=int(lerp(48, 66, grow)))
        if c >= 16:
            en.pad_block(sc, 5, b, [en.triad(E4, IONIAN, 1 + s, 4)], m.CYCLE,
                         size=4, lo=57, hi=83, vel=int(lerp(50, 72, grow)))
            root = en.pitch(E3, IONIAN, 1 + s)
            sc.note(6, root + 12, b, m.CYCLE, int(lerp(46, 66, grow)), jt=4)
            sc.note(6, root + 19, b, m.CYCLE, int(lerp(42, 62, grow)), jt=4)
        if c >= 24:                    # bells pealing on the cycle downbeats
            deg = (1, 5, 8, 5)[c % 4]
            sc.note(2, en.pitch(n("E5"), IONIAN, deg), b, 4.0, int(lerp(84, 104, grow)), jt=2)
        if c % 8 == 0 and c >= 8:
            sc.hit(49, b, int(lerp(76, 96, grow)))
    tb1 = t + 12 * m.CYCLE
    tb2 = t + 20 * m.CYCLE
    en.line(sc, 10, tb1, E4, IONIAN, m.THEME, 88, vel_end=96)
    en.line(sc, 10, tb2, E4, IONIAN, m.THEME, 94, vel_end=104, octave=1)
    en.line(sc, 12, tb2, E4, IONIAN, m.THEME, 78, vel_end=88)
    en.bend_ramp(sc, 10, tb1 + 28.7, tb1 + 29.3, -1.2, 0.0)
    en.bend_ramp(sc, 10, tb2 + 28.7, tb2 + 29.3, -1.2, 0.0)
    en.expr_curve(sc, 5, [(t, 70), (t + cycles * m.CYCLE, 100)], step=2)

    # a rapid-fire burst as the ground rises into the summit cadence
    tc0 = t + cycles * m.CYCLE
    burst = [1, 3, 5, 8, 5, 3, 1, 3, 5, 8, 10, 8, 5, 8, 10, 12]
    en.run(sc, 10, tc0 - 4.0, E4, IONIAN, burst, 0.25, 90, 114,
           octave_double=12)

    # the summit cadence, then the great chord
    tc = t + cycles * m.CYCLE
    sc.timesig(tc, 4, 4)
    sc.marker(tc, "the summit")
    for i, d in enumerate((4, 5)):
        b = tc + i * 4
        chord = en.triad(E3, IONIAN, d, 4) + [en.pitch(E3, IONIAN, d + 7)]
        en.strum(sc, 7, chord, b, 3.8, 96)
        en.pad_block(sc, 5, b, [en.triad(E4, IONIAN, d, 4)], 4.0, size=4,
                     lo=57, hi=83, vel=84)
        en.pad_block(sc, 4, b, [en.triad(E3, IONIAN, d, 4)], 4.0, size=3,
                     lo=52, hi=74, vel=72)
        root = en.pitch(E2, IONIAN, d)
        sc.note(3, root, b, 3.8, 96, jt=3)
        sc.note(0, root + 12, b, 3.8, 88, jt=3)
        sc.note(2, en.pitch(n("E5"), IONIAN, (8, 9)[i]), b, 4.0, 106, jt=2)
        sc.note(6, root + 24, b, 4.0, 70, jt=4)
        sc.hit(36, b, 98)
        sc.hit(49, b, 88)
        sc.hit(38, b + 2, 90)
    bf = tc + 8
    final = [n("E2"), n("B2"), n("E3"), n("G#3"), n("B3"), n("E4")]
    en.strum(sc, 7, final, bf, 10.0, 102, spread=0.05)
    en.strum(sc, 8, [p + 12 for p in final[2:]], bf + 0.1, 10.0, 86, spread=0.05)
    sc.note(3, n("E1"), bf, 10.0, 100, jt=0)
    sc.note(0, n("E2"), bf, 10.0, 92, jt=0)
    sc.note(2, n("E5"), bf, 9.0, 120, jt=0)
    sc.note(2, n("B5"), bf + 1.0, 8.0, 104, jt=0)
    sc.note(2, n("E6"), bf + 2.0, 8.0, 112, jt=0)
    sc.note(4, n("E2"), bf, 10.0, 78, jt=0)
    sc.note(4, n("B2"), bf, 10.0, 70, jt=0)
    en.pad_block(sc, 5, bf, [en.triad(E4, IONIAN, 1, 4)], 10.0, size=4,
                 lo=57, hi=83, vel=84)
    sc.note(6, n("E4"), bf, 10.0, 74, jt=0)
    sc.note(6, n("B4"), bf, 10.0, 66, jt=0)
    sc.hit(49, bf, 112)
    sc.hit(36, bf, 104)
    for ch in (4, 5, 6):
        en.expr_curve(sc, ch, [(bf + 3, 95), (bf + 10, 5)], step=0.5)
    # ...and then, nothing. (the false ending)
    sc.marker(bf + 10, "(a breath)")
    return bf + 10 + 5.5


# ---------------------------------------------------------------------------
# VII. The Hollow Hill Reel — it was never going to end quietly.
# ---------------------------------------------------------------------------
def reel(sc, t):
    sc.tempo(t, 112)
    sc.timesig(t, 4, 4)
    sc.marker(t, "VII. The Hollow Hill Reel")
    sc.tempo(t + 64, 122)
    sc.tempo(t + 128, 132)
    sc.tempo(t + 176, 138)
    for ch in (4, 5, 6):
        sc.cc(ch, 11, 100, t)
    sc.program(14, 25, t)          # harp channel becomes a tremolo mandolin
    sc.cc(14, 7, 0, t)
    D2, D3, D4 = n("D2"), n("D3"), n("D4")
    bars = 48
    harm = [0, 0, 3, 4]
    for bar in range(bars):
        s = harm[bar % 4]
        b = t + bar * 4
        grow = bar / bars
        # rhythm section: train beat
        sc.hit(36, b, int(lerp(78, 96, grow)))
        sc.hit(38, b + 1, int(lerp(80, 98, grow)))
        sc.hit(36, b + 2, int(lerp(72, 92, grow)))
        sc.hit(38, b + 3, int(lerp(82, 100, grow)))
        for k in range(8):
            sc.hit(42, b + k * 0.5, int(lerp(44, 60, grow)) if k % 2 == 0 else 34)
        if bar % 8 == 0:
            sc.hit(49, b, int(lerp(80, 100, grow)))
        if bar >= 32:
            sc.hit(39, b + 1, int(lerp(60, 80, grow)))
            sc.hit(39, b + 3, int(lerp(60, 80, grow)))
        if bar >= 40:
            for k in range(8):
                sc.hit(54, b + k * 0.5, 44 if k % 2 == 0 else 30)
        # bass walking root and fifth
        root = en.pitch(D2, IONIAN, 1 + s)
        for k, off in enumerate((0, 7, 0, 7)):
            sc.note(3, root + off, b + k, 0.9, int(lerp(70, 88, grow)), jt=3)
        # offbeat strums + picked nylon
        chord = en.triad(D3, IONIAN, 1 + s, 3) + [en.pitch(D3, IONIAN, 8 + s)]
        en.strum(sc, 7, chord, b + 0.5, 0.4, int(lerp(58, 74, grow)), down=False)
        en.strum(sc, 7, chord, b + 1.5, 0.4, int(lerp(58, 74, grow)), down=False)
        en.strum(sc, 7, chord, b + 2.5, 0.4, int(lerp(58, 74, grow)), down=False)
        en.strum(sc, 7, chord, b + 3.5, 0.4, int(lerp(58, 74, grow)), down=False)
        if bar >= 16:                  # banjo rolls
            roll = en.triad(D4, IONIAN, 1 + s, 3) + [en.pitch(D4, IONIAN, 8 + s)]
            for k in range(8):
                sc.note(15, roll[(0, 2, 1, 3, 0, 3, 1, 2)[k]], b + k * 0.5, 0.45,
                        int(lerp(52, 68, grow)), jt=3)
        if bar == 32:
            sc.cc(14, 7, 78, b)
        if bar >= 32:                  # tremolo mandolin: the classic rapid pick
            top = en.pitch(D4, IONIAN, 8 + s)
            for k in range(16):
                sc.note(14, top, b + k * 0.25, 0.23,
                        int(lerp(54, 74, grow)) + (6 if k % 2 == 0 else 0), jt=1, jv=3)
    # the tune: fiddle, whistle, thirds, then everyone
    plan = [(0, 12, m.REEL_A, 0, 0), (4, 12, m.REEL_A, 0, 0),
            (8, 11, m.REEL_B, 0, 1), (12, 11, m.REEL_B, 0, 1),
            (16, 12, m.REEL_A, 2, 0), (20, 12, m.REEL_A, 2, 0),
            (24, 12, m.REEL_B, 2, 0), (28, 12, m.REEL_B, 2, 0),
            (32, 12, m.REEL_A, 2, 0), (36, 12, m.REEL_A, 2, 0),
            (40, 12, m.REEL_B, 2, 0), (44, 12, m.REEL_B, 2, 0)]
    for bar_at, ch, strain, third, octv in plan:
        b = t + bar_at * 4
        vel = int(lerp(76, 96, bar_at / bars))
        en.line(sc, ch, b, D4, IONIAN, strain, vel, octave=octv, gate=0.9)
        if third:
            other = 11 if ch == 12 else 12
            en.line(sc, other, b, D4, IONIAN, strain, vel - 10, shift=2,
                    octave=1, gate=0.88)
        if bar_at >= 32:
            en.line(sc, 1, b, D4, IONIAN,
                    [nt for i, nt in enumerate(strain) if i % 2 == 0],
                    56, octave=1, gate=0.8)
            # the lead guitar hammers the run instead of re-picking every
            # note: overlapping gate + CC68 lets the synth slur note to note
            sc.cc(10, 68, 127, b - 0.05)
            en.line(sc, 10, b, D4, IONIAN, strain, vel - 6, vel_end=vel + 4,
                    gate=1.2)
            sc.cc(10, 68, 0, b + 4.3)
    # the last bar of tune is replaced by the send-off
    bend = t + bars * 4
    rise = [(1, 0, 0.5), (2, 0.5, 0.5), (3, 1, 0.5), (4, 1.5, 0.5),
            (5, 2, 0.5), (6, 2.5, 0.5), (7, 3, 0.5), (8, 3.5, 0.5)]
    for ch, octv in ((12, 0), (11, 1), (10, 0), (15, 0)):
        en.line(sc, ch, bend, D4, IONIAN, rise, 96, octave=octv, gate=0.95)
    for k in range(8):
        sc.hit(38, bend + k * 0.5, 70 + 4 * k)
    bhit = bend + 4
    for i, (d, beat) in enumerate(((4, 0.0), (5, 1.0))):      # G . A .
        chord = en.triad(D3, IONIAN, d, 3) + [en.pitch(D3, IONIAN, d + 7)]
        en.strum(sc, 7, chord, bhit + beat, 0.45, 100)
        sc.note(3, en.pitch(D2, IONIAN, d), bhit + beat, 0.45, 96, jt=2)
        sc.note(12, en.pitch(D4, IONIAN, d + 7), bhit + beat, 0.45, 98, jt=2)
        sc.note(11, en.pitch(D4, IONIAN, d + 7) + 12, bhit + beat, 0.45, 90, jt=2)
        sc.hit(36, bhit + beat, 100)
        sc.hit(38, bhit + beat, 96)
        sc.hit(49, bhit + beat, 80 + 10 * i)
    # ...D!
    bfin = bhit + 2.5
    final = [n("D2"), n("A2"), n("D3"), n("F#3"), n("A3"), n("D4")]
    en.strum(sc, 7, final, bfin, 8.0, 106, spread=0.04)
    en.strum(sc, 8, [p + 12 for p in final[2:]], bfin + 0.05, 8.0, 88, spread=0.04)
    sc.note(3, n("D1"), bfin, 8.0, 102, jt=0)
    sc.note(0, n("D2"), bfin, 8.0, 94, jt=0)
    sc.note(2, n("D5"), bfin, 8.0, 118, jt=0)
    sc.note(2, n("A5"), bfin + 1.0, 7.0, 100, jt=0)
    sc.note(2, n("D6"), bfin + 2.0, 6.0, 110, jt=0)
    sc.hit(49, bfin, 112)
    sc.hit(36, bfin, 106)
    sc.hit(57, bfin + 1.0, 90)
    # the wink: two little woodblock taps as the chord rings away
    sc.hit(76, bfin + 5.0, 52)
    sc.hit(77, bfin + 5.5, 46)
    return bfin + 8


def build(sc):
    setup(sc)
    t = 0.0
    t = green_morning(sc, t)
    t = dance(sc, t)
    t = stone_voices(sc, t)
    t = night_ocean(sc, t)
    t = the_return(sc, t)
    t = reel(sc, t)
    sc.marker(t, "end of Part Two")
    return t
