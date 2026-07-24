"""part_one.py — Hollow Hill, Part One (~14 minutes).

    I.   Dawn            the 13/8 Hill ostinato alone, then layered
    II.  First Light     bass, organ and flute join beneath the figure
    III. The Hill Theme  the tune floats over the odd metre, three statements
    IV.  Interlock       two acoustic guitars in hocket, hand percussion
    V.   Deep Water      the ambient pool — pads, fretless bass, crystal
    VI.  Stormrise       distorted riff, climbing modulations
    VII. The Summoning   instruments called in one by one over a ground bass,
                         crowned by the tubular bells; E major cadence
"""

import engine as en
import material as m
from engine import lerp, n

DORIAN, AEOLIAN, IONIAN, LYDIAN = "dorian", "aeolian", "ionian", "lydian"


def setup(sc):
    sc.channel(0, "Grand Piano", 0, volume=105, pan=54)
    sc.channel(1, "Glockenspiel", 9, volume=85, pan=76, reverb=70)
    sc.channel(2, "Tubular Bells", 14, volume=110, pan=64, reverb=80)
    sc.channel(3, "Bass Guitar", 33, volume=105, pan=64, reverb=25)
    sc.channel(4, "Organ", 19, volume=72, pan=58)
    sc.channel(5, "Strings", 49, volume=80, pan=60, reverb=75)
    sc.channel(6, "Choir", 52, volume=82, pan=68, reverb=80)
    sc.channel(7, "Steel Guitar", 25, volume=92, pan=40)
    sc.channel(8, "Nylon Guitar", 24, volume=92, pan=88)
    sc.channel(9, "Percussion", 0, volume=100)
    sc.channel(10, "Lead Guitar", 27, volume=98, pan=60, reverb=60)
    sc.channel(11, "Flute", 73, volume=88, pan=70, reverb=70)
    sc.channel(12, "Fiddle", 40, volume=90, pan=48, reverb=60)
    sc.channel(13, "Pad", 89, volume=72, pan=64, reverb=95)
    sc.channel(14, "Crystal", 98, volume=70, pan=80, reverb=95)
    sc.channel(15, "Timpani", 47, volume=95, pan=64, reverb=65)


# ---------------------------------------------------------------------------
# I. Dawn — 20 ostinato cycles, the piano waking the hill.
# ---------------------------------------------------------------------------
def dawn(sc, t):
    sc.tempo(t, 92)
    sc.timesig(t, 13, 8)
    sc.marker(t, "I. Dawn")
    E4, E2 = n("E4"), n("E2")
    shifts = [0] * 10 + [0, 0, 2, 2, 0, 0, 3, -1, 0, 0]
    for c, s in enumerate(shifts):
        b = t + c * m.CYCLE
        vel = int(lerp(44, 64, c / len(shifts)))
        m.ostinato_cycle(sc, 0, b, E4, DORIAN, s, vel=vel)
        if 6 <= c < 14:
            m.ostinato_cycle(sc, 1, b, E4, DORIAN, s, vel=40, octave=1,
                             only_accents=True, jv=3)
        elif c >= 14:
            m.ostinato_cycle(sc, 1, b, E4, DORIAN, s, vel=44, octave=1, jv=3)
        if c >= 10:                       # the bass wakes early, already singing
            en.line(sc, 3, b, E2, DORIAN, m.BASS_CALM,
                    int(lerp(50, 68, c / len(shifts))), shift=s, jt=4)
        if c >= 14:                       # nylon guitar picks the accents
            for k, q in enumerate(m.OST_ACCENTS):
                sc.note(8, en.pitch(n("E3"), DORIAN, (1, 5, 8, 5, 3)[k] + s),
                        b + q * 0.5, 0.9, int(lerp(36, 46, c / len(shifts))), jt=5)
        if c >= 12 and c % 4 == 0:
            root = en.pitch(E2, DORIAN, 1 + s)
            sc.note(4, root, b, 4 * m.CYCLE, 38, jt=3)
            sc.note(4, root + 7, b, 4 * m.CYCLE, 34, jt=3)
        if c >= 16:
            sc.note(5, en.pitch(n("E3"), DORIAN, 1 + s), b, m.CYCLE, 30, jt=4)
    span = len(shifts) * m.CYCLE
    en.expr_curve(sc, 4, [(t, 30), (t + span, 80)], step=2)
    en.expr_curve(sc, 5, [(t, 24), (t + span, 60)], step=2)
    return t + span


# ---------------------------------------------------------------------------
# II. First Light — the bass finds its feet; the flute calls the theme.
# ---------------------------------------------------------------------------
def first_light(sc, t):
    sc.marker(t, "II. First Light")
    E4, E2 = n("E4"), n("E2")
    shifts = [0, 0, 2, 2, 0, 0, 3, -1] * 2
    for c, s in enumerate(shifts):
        b = t + c * m.CYCLE
        vel = int(lerp(60, 72, c / len(shifts)))
        m.ostinato_cycle(sc, 0, b, E4, DORIAN, s, vel=vel)
        m.ostinato_cycle(sc, 1, b, E4, DORIAN, s, vel=44, octave=1,
                         only_accents=True, jv=3)
        en.line(sc, 3, b, E2, DORIAN, m.BASS_WALK,
                int(lerp(64, 82, c / 16)), shift=s, jt=4)
        tones = en.triad(n("E3"), DORIAN, 1 + s, 4)   # nylon fingerpicking
        for k in range(13):
            sc.note(8, tones[m.PICK_13[k]], b + k * 0.5, 0.55,
                    int(lerp(46, 58, c / 16)) + (5 if k in m.OST_ACCENTS else 0), jt=5)
        if c % 2 == 0:
            pcs = en.triad(E4, DORIAN, 1 + s)
            en.pad_block(sc, 4, b, [pcs], 2 * m.CYCLE, size=3,
                         lo=52, hi=71, vel=42)
        if c in (4, 12):
            en.line(sc, 11, b, E4, DORIAN, m.THEME_FRAG, 62, octave=1)
        if c >= 8:
            sc.note(5, en.pitch(n("E3"), DORIAN, 1 + s), b, m.CYCLE, 34, jt=4)
    span = len(shifts) * m.CYCLE
    en.expr_curve(sc, 4, [(t, 60), (t + span, 90)], step=2)
    en.expr_curve(sc, 5, [(t, 50), (t + span, 78)], step=2)
    return t + span


# ---------------------------------------------------------------------------
# III. The Hill Theme — three statements over the running figure.
# ---------------------------------------------------------------------------
def hill_theme(sc, t):
    sc.marker(t, "III. The Hill Theme")
    E4, E2 = n("E4"), n("E2")
    harm = [0, 0, 2, 3, -1]
    cycles = 16
    for c in range(cycles):
        s = harm[c % 5]
        b = t + c * m.CYCLE
        grow = c / cycles
        m.ostinato_cycle(sc, 0, b, E4, DORIAN, s, vel=int(lerp(64, 76, grow)))
        m.ostinato_cycle(sc, 1, b, E4, DORIAN, s, vel=46, octave=1,
                         only_accents=(c < 11), jv=3)
        en.line(sc, 3, b, E2, DORIAN, m.BASS_WALK,
                int(lerp(72, 88, grow)), shift=s, jt=4)
        tones = en.triad(n("E3"), DORIAN, 1 + s, 4)   # steel picking joins
        for k in range(13):
            sc.note(7, tones[m.PICK_13[k]], b + k * 0.5, 0.55,
                    int(lerp(50, 64, grow)) + (5 if k in m.OST_ACCENTS else 0), jt=5)
        if c >= 5:
            pcs = en.triad(E4, DORIAN, 1 + s, 4)
            en.pad_block(sc, 5, b, [pcs], m.CYCLE, size=4, lo=55, hi=79,
                         vel=int(lerp(36, 56, grow)))
        if c >= 10:
            root = en.pitch(n("E3"), DORIAN, 1 + s)
            sc.note(6, root, b, m.CYCLE, 44, jt=5)
            sc.note(6, root + 7, b, m.CYCLE, 40, jt=5)
    # statements: guitar, flute (clean guitar in thirds below), then
    # fiddle + guitar in octaves
    en.line(sc, 10, t + 1 * m.CYCLE, E4, DORIAN, m.THEME, 78, vel_end=86)
    en.line(sc, 11, t + 6 * m.CYCLE, E4, DORIAN, m.THEME, 70, vel_end=80, octave=1)
    en.line(sc, 10, t + 6 * m.CYCLE, E4, DORIAN, m.THEME, 60, vel_end=70, shift=-2)
    en.line(sc, 12, t + 11 * m.CYCLE, E4, DORIAN, m.THEME, 82, vel_end=94, octave=1)
    en.line(sc, 10, t + 11 * m.CYCLE, E4, DORIAN, m.THEME, 80, vel_end=90)
    en.expr_curve(sc, 5, [(t, 60), (t + cycles * m.CYCLE, 92)], step=2)
    return t + cycles * m.CYCLE


# ---------------------------------------------------------------------------
# IV. Interlock — two guitars in 16th-note hocket, hand percussion gathering.
# ---------------------------------------------------------------------------
def interlock(sc, t):
    sc.tempo(t, 104)
    sc.timesig(t, 4, 4)
    sc.marker(t, "IV. Interlock")
    sc.program(11, 78, t)          # flute becomes tin whistle
    E3, E4, E2 = n("E3"), n("E4"), n("E2")
    bars = 48
    harm = [0, 0, 2, 2, -1, -1, 3, 3]
    for bar in range(bars):
        s = harm[bar % 8]
        b = t + bar * 4
        grow = bar / bars
        up = en.triad(E3, DORIAN, 1 + s, 4)
        down = list(reversed(en.triad(E4, DORIAN, 1 + s, 4)))
        va = int(lerp(56, 74, grow))
        for k in range(8):                       # guitar A on the quaver grid
            sc.note(7, up[k % 4], b + k * 0.5, 0.45, va + (6 if k % 4 == 0 else 0), jt=4)
        if bar >= 2:                             # guitar B answers off the beat
            for k in range(8):
                sc.note(8, down[k % 4], b + 0.25 + k * 0.5, 0.4, va - 8, jt=4)
        root = en.pitch(E2, DORIAN, 1 + s)
        sc.note(3, root, b, 1.9, int(lerp(62, 80, grow)), jt=4)
        sc.note(3, root, b + 2, 1.4, int(lerp(58, 76, grow)), jt=4)
        if bar % 2 == 1:                  # walking approach into the next bar
            sc.note(3, en.pitch(E2, DORIAN, 5 + s), b + 3, 0.45,
                    int(lerp(54, 72, grow)), jt=4)
            sc.note(3, en.pitch(E2, DORIAN, 6 + s), b + 3.5, 0.45,
                    int(lerp(56, 74, grow)), jt=4)
        # hand percussion, arriving in waves
        if bar >= 4:
            for k in range(8):
                sc.hit(70, b + k * 0.5, 46 if k % 2 == 0 else 30)
        if bar >= 16:
            sc.hit(54, b + 1, 52)
            sc.hit(54, b + 3, 56)
        if bar >= 24:
            for beat, drum, v in ((0, 61, 62), (0.75, 60, 46), (1.5, 61, 50),
                                  (2.25, 60, 46), (3, 61, 58), (3.5, 60, 44)):
                sc.hit(drum, b + beat, v)
        if bar >= 32:
            sc.hit(36, b, 66)
            sc.hit(36, b + 2, 58)
    # whistle and fiddle trade reel fragments across the top
    frag = m.REEL_A[:14]
    for i, start_bar in enumerate((32, 36, 40, 44)):
        ch = 11 if i % 2 == 0 else 12
        en.line(sc, ch, t + start_bar * 4, E4, DORIAN, frag, 74, octave=1, gate=0.9)
    sc.hit(49, t + (bars - 1) * 4 + 3.5, 70)
    return t + bars * 4


# ---------------------------------------------------------------------------
# V. Deep Water — the ambient pool (the Songs-of-Distant-Earth colour).
# ---------------------------------------------------------------------------
def deep_water(sc, t):
    sc.tempo(t, 64)
    sc.marker(t, "V. Deep Water")
    sc.program(3, 35, t)           # fretless bass
    sc.program(4, 95, t)           # sweep pad takes the organ channel
    sc.program(1, 10, t)           # music box takes the glockenspiel channel
    C3, C5 = n("C3"), n("C5")
    bars = 40
    shifts = [0, 1, 5, 4, 0, 1, 2, 4, 0, 1]        # one shift per 4 bars
    chords = [en.triad(C3, LYDIAN, 1 + s, 4) for s in shifts]
    en.pad_block(sc, 13, t, chords, 16.0, size=4, lo=55, hi=81, vel=52)
    for i, s in enumerate(shifts):
        b = t + i * 16
        root = en.pitch(n("C2"), LYDIAN, 1 + s)
        en.line(sc, 3, b, n("C2"), LYDIAN, m.BASS_SLOW, 58, shift=s, jt=4)
        if i % 2 == 0:
            sc.note(4, root + 12, b, 32.0, 40, jt=3)
            sc.note(4, root + 19, b, 32.0, 34, jt=3)
        sc.note(2, en.pitch(n("C4"), LYDIAN, 1 + s), b, 6.0, 34, jt=3)
        if i >= 1:                        # clean guitar, notes left to echo
            for beat, deg in ((0, 8), (3, 10), (6, 12), (9, 10), (12, 9)):
                p = en.pitch(n("C4"), LYDIAN, deg + s)
                sc.note(10, p, b + beat, 2.4, 44, jt=6)
                sc.note(10, p, b + beat + 0.75, 2.0, 28, jt=6)
    for bar in range(bars):
        if bar % 2 == 0:
            s = shifts[bar // 4]
            high = en.triad(C5, LYDIAN, 1 + s, 4)
            en.arp(sc, 14, high, t + bar * 4, 8, 0.5, 36, pattern="updown", gate=2.0)
        if 16 <= bar < 32:
            sc.hit(36, t + bar * 4, 30, jv=2)
            sc.hit(36, t + bar * 4 + 2, 26, jv=2)
        if bar % 4 == 0:
            sc.hit(81, t + bar * 4, 30)
    en.line(sc, 1, t + 8 * 4, C5, LYDIAN, m.BELL, 46, gate=1.5)
    en.line(sc, 1, t + 24 * 4, C5, LYDIAN, m.BELL, 42, gate=1.5)
    en.expr_curve(sc, 13, [(t, 40), (t + 32, 85), (t + 128, 85), (t + bars * 4, 55)], step=2)
    en.expr_curve(sc, 4, [(t, 30), (t + 64, 70), (t + bars * 4, 45)], step=2)
    # a rising ride swell lifts the pool into the storm
    for k in range(8):
        sc.hit(51, t + (bars - 1) * 4 + k * 0.5, int(lerp(20, 62, k / 7)))
    return t + bars * 4


# ---------------------------------------------------------------------------
# VI. Stormrise — the distorted riff climbs E, F#, G, A.
# ---------------------------------------------------------------------------
def stormrise(sc, t):
    sc.tempo(t, 112)
    sc.marker(t, "VI. Stormrise")
    sc.program(10, 30, t)          # distortion guitar
    sc.program(4, 18, t)           # rock organ
    sc.program(5, 48, t)           # full string ensemble
    sc.program(12, 29, t)          # the fiddle picks up an overdriven voice
    sc.program(3, 33, t)
    sc.program(13, 28, t)          # the pad channel becomes a palm-muted guitar
    sc.cc(13, 11, 110, t)
    sc.cc(13, 10, 28, t)           # hard left -- the classic twin-guitar spread
    sc.cc(13, 91, 28, t)           # chugs stay dry and tight
    sc.cc(13, 93, 0, t)
    sc.cc(13, 94, 0, t)
    sc.program(11, 29, t)          # the flute channel becomes a second electric
    sc.cc(11, 10, 100, t)          # hard right, answering the chug guitar
    sc.cc(11, 91, 40, t)
    sc.cc(11, 94, 0, t)            # machine-gun runs would smear in the echo
    sc.cc(4, 11, 100, t)
    sc.tempo(t + 96, 120)
    sc.tempo(t + 160, 126)
    bases = [n("E2")] * 16 + [n("F#2")] * 16 + [n("G2")] * 16 + [n("A2")] * 8
    wail = [(8, 0, 3), (7, 3, 2), (5, 5, 2), (6, 7, 3),
            (5, 10, 2), (4, 12, 2), (3, 14, 2)]
    bars = len(bases)
    for bar in range(bars):
        base = bases[bar]
        b = t + bar * 4
        grow = bar / bars
        if bar % 2 == 0:                              # two-bar riff
            for deg, start, dur in m.RIFF:
                v = int(lerp(88, 104, grow))
                sc.note(10, en.pitch(base + 12, AEOLIAN, deg), b + start, dur * 0.95, v, jt=4)
                sc.note(10, en.pitch(base + 12, AEOLIAN, deg + 4), b + start, dur * 0.95, v - 10, jt=4)
                sc.note(0, en.pitch(base, AEOLIAN, deg), b + start, dur * 0.95, v - 16, jt=4)
            chord = [base + 12, base + 19, base + 24]
            for p in chord:
                sc.note(4, p, b, 7.8, int(lerp(52, 70, grow)), jt=3)
        for k in range(8):                            # driving bass quavers
            deg = 1 if k not in (6, 7) else 0
            sc.note(3, en.pitch(base, AEOLIAN, deg), b + k * 0.5, 0.45,
                    int(lerp(74, 92, grow)), jt=3)
        # driving acoustic strums, Amarok-style
        chord = [en.pitch(base + 12, AEOLIAN, d) for d in (1, 5, 8)]
        for beat, down, acc in ((0.0, True, True), (1.0, True, False),
                                (1.5, False, False), (2.5, False, False),
                                (3.0, True, False), (3.5, False, False)):
            en.strum(sc, 7, chord, b + beat, 0.4,
                     int(lerp(54, 76, grow)) + (8 if acc else 0),
                     spread=0.02, down=down)
        if bar >= 16:                                 # string tremolo layer
            for k in range(8):
                p = en.pitch(base + 24, AEOLIAN, (1, 3, 5)[k % 3])
                sc.note(5, p, b + k * 0.5, 0.5, int(lerp(40, 76, grow)), jt=4)
        # palm-muted chug, 3+3+2 accents — the engine room of the storm
        if 8 <= bar < bars - 1:
            root = en.pitch(base + 12, AEOLIAN, 1)
            for k in range(8):
                acc = 10 if k in (0, 3, 6) else 0
                sc.note(13, root, b + k * 0.5, 0.30,
                        int(lerp(58, 86, grow)) + acc, jt=2, jv=3)
        # rapid fire: doubled semiquaver cells, then sextuplet rips (bar 54+)
        if 32 <= bar < bars - 1:
            cell_a = [1, 2, 3, 5, 3, 2, 1, 2, 3, 5, 6, 5, 3, 2, 1, 2]
            cell_b = [1, 3, 5, 8, 5, 3, 1, 3, 5, 8, 10, 8, 5, 3, 5, 8]
            v0 = int(lerp(74, 96, grow))
            if bar < 54:
                cell = cell_a if bar % 2 == 0 else cell_b
                en.run(sc, 11, b, base + 24, AEOLIAN, cell, 0.25,
                       v0, v0 + 8, octave_double=12)
            else:
                # a sextuplet rip: up-down-up within one octave, not a climb
                # into the stratosphere
                rip = list(range(1, 9)) + list(range(8, 0, -1)) + list(range(1, 9))
                en.run(sc, 11, b, base + 12, AEOLIAN, rip,
                       4.0 / 24.0, 90, 112, octave_double=12)
        # kit
        sc.hit(36, b, 92)
        sc.hit(36, b + 1.5, 78)
        sc.hit(36, b + 2, 88)
        sc.hit(38, b + 1, 96)
        sc.hit(38, b + 3, 98)
        for k in range(8):
            sc.hit(42 if bar < 32 else 51, b + k * 0.5, 58 if k % 2 == 0 else 42)
        if bar % 8 == 0:
            sc.hit(49, b, 100)
        if bar % 8 == 7:                              # tom fill into the next block
            for k, drum in enumerate((45, 45, 43, 43, 41, 41, 38, 38)):
                sc.hit(drum, b + 2 + k * 0.25, 76 + 3 * k)
        if bar % 16 == 15:                            # timpani roll at each climb
            for k in range(16):
                sc.note(15, base - 12 if base - 12 >= 24 else base, b + k * 0.25,
                        0.24, int(lerp(50, 96, k / 15)), jt=2)
    for block in range(1, 4):                         # overdriven wail per block
        base = bases[block * 16 - 8] + 24
        tw = t + (block * 16 - 8) * 4
        en.line(sc, 12, tw, base, AEOLIAN, wail, 84, vel_end=96)
        # scoop into the opening cry, and bend the last note up a whole tone
        sc.bend(12, tw - 0.10, -1.5)
        en.bend_ramp(sc, 12, tw, tw + 0.6, -1.5, 0.0)
        en.bend_ramp(sc, 12, tw + 14.2, tw + 15.2, 0.0, 2.0)
        en.bend_ramp(sc, 12, tw + 15.6, tw + 16.0, 2.0, 0.0)
    # final bar: unison rise and a hard cut
    b = t + (bars - 1) * 4
    for k in range(8):
        p = en.pitch(bases[-1] + 12, AEOLIAN, 1 + k)
        sc.note(10, p, b + k * 0.5, 0.45, 104, jt=3)
        sc.note(0, p - 12, b + k * 0.5, 0.45, 88, jt=3)
        sc.hit(38, b + k * 0.5, 70 + 4 * k)
    sc.hit(49, b + 4, 110)
    sc.note(2, n("E5"), b + 4, 4.0, 90, jt=0)
    sc.cc(13, 11, 0, b + 5)        # the chug guitar bows out with the storm
    return t + bars * 4 + 6        # two beats of held bell, four of silence


# ---------------------------------------------------------------------------
# VII. The Summoning — the roll call, after the old ceremony.
# ---------------------------------------------------------------------------
def summoning(sc, t):
    sc.tempo(t, 100)
    sc.marker(t, "VII. The Summoning")
    sc.program(10, 29, t)          # overdriven lead for the theme
    # XG Mandolin = Steel Guitar (25) + bank LSB 96. GM has no mandolin program,
    # so this used to be a bare steel guitar tremolo'd with 32nd-note repeats;
    # the cell gets the real recorded instrument. Bank select goes BEFORE the
    # Program Change so a hardware player latches it too.
    sc.cc(15, 32, 96, t + 151)
    sc.program(15, 25, t + 152)    # timpani channel doubles as mandolin later
    sc.cc(12, 11, 100, t)
    E2, E3, E4, E5 = n("E2"), n("E3"), n("E4"), n("E5")
    entries = [(0, "the ground"), (8, "... grand piano"), (16, "... glockenspiel"),
               (24, "... reed and pipe organ"), (32, "... two acoustic guitars"),
               (40, "... mandolin"), (48, "... Spanish guitar"),
               (56, "... overdriven guitar"), (64, "... strings and choir"),
               (72, "... plus: TUBULAR BELLS!")]
    for bar_at, label in entries:
        sc.marker(t + bar_at * 4, label)
    sc.program(4, 19, t + 24 * 4)

    for bar in range(88):
        r = m.GROUND_ROOTS[bar % 4]
        b = t + bar * 4
        grow = lerp(0.55, 1.0, bar / 88)
        # the ground itself
        for off, start, dur in m.GROUND_BAR:
            sc.note(3, en.pitch(E2, AEOLIAN, r + off), b + start, dur * 0.95,
                    int(78 * grow) + 14, jt=3)
        # kit
        sc.hit(36, b, int(86 * grow))
        sc.hit(36, b + 2, int(78 * grow))
        sc.hit(38, b + 1, int(84 * grow))
        sc.hit(38, b + 3, int(86 * grow))
        sc.hit(54, b + 1, int(60 * grow))
        sc.hit(54, b + 3, int(62 * grow))
        for k in range(8):
            sc.hit(42, b + k * 0.5, int((56 if k % 2 == 0 else 40) * grow))
        if bar % 8 == 0 and bar > 0:
            sc.hit(49, b, int(96 * grow))
        if bar % 8 == 7:
            for k in range(8):
                sc.hit(38, b + 2 + k * 0.25, int(lerp(56, 92, k / 7) * grow))
        if bar >= 8:       # grand piano
            en.arp(sc, 0, en.triad(E3, AEOLIAN, r, 4) + [en.pitch(E3, AEOLIAN, r + 7)],
                   b, 8, 0.5, int(66 * grow), pattern="updown", gate=1.4)
        if bar >= 16:      # glockenspiel sparkle
            for k, deg in enumerate((r + 7, r + 9, r + 11, r + 14)):
                sc.note(1, en.pitch(E4, AEOLIAN, deg), b + 2 + k * 0.5, 0.6,
                        int(56 * grow), jt=4)
        if bar >= 24:      # organ bed
            en.pad_block(sc, 4, b, [en.triad(E3, AEOLIAN, r, 4)], 4.0,
                         size=3, lo=52, hi=74, vel=int(58 * grow))
        if bar >= 32:      # strummed guitars
            chord = en.triad(E3, AEOLIAN, r, 4) + [en.pitch(E3, AEOLIAN, r + 7)]
            en.strum(sc, 7, chord, b, 1.4, int(70 * grow))
            en.strum(sc, 7, chord, b + 1.5, 0.4, int(56 * grow), down=False)
            en.strum(sc, 7, chord, b + 2, 1.4, int(66 * grow))
            en.strum(sc, 7, chord, b + 3.5, 0.4, int(58 * grow), down=False)
        if 32 <= bar < 48:  # picked nylon
            for k in range(8):
                p = en.triad(E4, AEOLIAN, r, 4)[(0, 2, 1, 3, 2, 1, 3, 2)[k]]
                sc.note(8, p, b + k * 0.5, 0.5, int(58 * grow), jt=4)
        if bar >= 40:      # mandolin tremolo
            top = en.pitch(E5, AEOLIAN, r + 7)
            for k in range(16):
                sc.note(15, top, b + k * 0.25, 0.24, int((52 + (k % 2) * 6) * grow), jt=2)
        if bar >= 48:      # Spanish guitar runs — hammered, not re-picked
            up = bar % 2 == 0
            degs = [r + (k if up else 15 - k) for k in range(16)]
            en.run(sc, 8, b, E3, AEOLIAN, degs, 0.25,
                   int(50 * grow), int(64 * grow), legato=True)
        if bar >= 64:      # strings and choir
            en.pad_block(sc, 5, b, [en.triad(E4, AEOLIAN, r, 4)], 4.0,
                         size=4, lo=57, hi=83, vel=int(64 * grow))
            root = en.pitch(E3, AEOLIAN, r)
            sc.note(6, root + 12, b, 4.0, int(62 * grow), jt=4)
            sc.note(6, root + 19, b, 4.0, int(56 * grow), jt=4)
    # the theme over the ground, twice, from bar 56
    for rep in (56, 64, 72, 80):
        tb = t + rep * 4
        en.line(sc, 10, tb, E4, AEOLIAN, m.THEME, 96, vel_end=104,
                octave=(1 if rep >= 72 else 0))
        # THEME's last event is (1, 29, 3): a long tonic -- bend up into it
        en.bend_ramp(sc, 10, tb + 28.7, tb + 29.3, -1.2, 0.0)
    # the bells — stately rather than clangorous: mid register, room to ring
    en.line(sc, 2, t + 72 * 4, E4, AEOLIAN, m.BELL, 88, gate=1.6)
    en.line(sc, 2, t + 76 * 4, E4, AEOLIAN, m.BELL, 92, gate=1.6)
    for bar in range(80, 88, 2):
        deg = (8, 5, 3, 1)[(bar // 2) % 4]
        sc.note(2, en.pitch(E4, AEOLIAN, deg), t + bar * 4, 7.0, 92, jt=2)
        sc.note(1, en.pitch(E5, AEOLIAN, deg), t + bar * 4, 2.0, 64, jt=2)

    # cadence: the hill in E major
    tc = t + 88 * 4
    sc.marker(tc, "the hilltop (E major)")
    seq = [4, 5, 1, 1, 4, 5, 1, 1]
    for i, d in enumerate(seq):
        b = tc + i * 4
        chord = en.triad(E3, IONIAN, d, 4) + [en.pitch(E3, IONIAN, d + 7)]
        en.strum(sc, 7, chord, b, 3.8, 92)
        en.strum(sc, 8, [p + 12 for p in chord[:4]], b + 0.05, 3.7, 78)
        en.pad_block(sc, 4, b, [en.triad(E3, IONIAN, d, 4)], 4.0, size=3,
                     lo=52, hi=74, vel=74)
        en.pad_block(sc, 5, b, [en.triad(E4, IONIAN, d, 4)], 4.0, size=4,
                     lo=57, hi=83, vel=80)
        root = en.pitch(E2, IONIAN, d)
        sc.note(3, root, b, 3.8, 96, jt=3)
        sc.note(0, root + 12, b, 3.8, 84, jt=3)
        sc.note(0, root + 24, b, 3.8, 78, jt=3)
        sc.note(6, root + 24, b, 4.0, 70, jt=4)
        sc.note(6, root + 31, b, 4.0, 64, jt=4)
        if i % 2 == 0:
            sc.note(2, en.pitch(E4, IONIAN, (8, 5)[(i // 2) % 2]), b, 7.5, 88, jt=2)
        sc.hit(36, b, 96)
        sc.hit(49, b, 84 if i % 2 == 0 else 66)
        sc.hit(38, b + 2, 88)
    sc.cc(15, 32, 0, tc + 27)      # base bank back: this channel is timpani again
    sc.program(15, 47, tc + 28)
    for k in range(16):                    # timpani roll into the final chord
        sc.note(15, n("E2"), tc + 28 + k * 0.25, 0.24, int(lerp(56, 104, k / 15)), jt=2)
    bf = tc + 32
    final = en.triad(E3, IONIAN, 1, 3) + [n("E4"), n("G#4"), n("B4"), n("E5")]
    en.strum(sc, 7, final, bf, 12.0, 100, spread=0.05)
    en.strum(sc, 8, [p + 12 for p in final[:4]], bf + 0.1, 12.0, 84, spread=0.05)
    sc.note(3, n("E1"), bf, 12.0, 100, jt=0)
    sc.note(0, n("E2"), bf, 12.0, 92, jt=0)
    sc.note(2, n("E4"), bf, 10.0, 100, jt=0)
    sc.note(2, n("B4"), bf + 1.0, 9.0, 86, jt=0)
    sc.note(2, n("E5"), bf + 2.0, 10.0, 92, jt=0)
    for ch, hi in ((4, 90), (5, 95), (6, 85), (13, 70)):
        sc.cc(ch, 11, hi, bf)
    en.pad_block(sc, 5, bf, [en.triad(E4, IONIAN, 1, 4)], 12.0, size=4,
                 lo=57, hi=83, vel=84)
    sc.note(6, n("E4"), bf, 12.0, 74, jt=0)
    sc.note(6, n("B4"), bf, 12.0, 68, jt=0)
    sc.note(4, n("E2"), bf, 12.0, 80, jt=0)
    sc.note(4, n("B2"), bf, 12.0, 72, jt=0)
    sc.hit(49, bf, 112)
    sc.hit(36, bf, 104)
    for ch in (4, 5, 6, 13):
        en.expr_curve(sc, ch, [(bf + 4, 92), (bf + 12, 8)], step=0.5)
    return bf + 12


def build(sc):
    setup(sc)
    t = 0.0
    t = dawn(sc, t)
    t = first_light(sc, t)
    t = hill_theme(sc, t)
    t = interlock(sc, t)
    t = deep_water(sc, t)
    t = stormrise(sc, t)
    t = summoning(sc, t)
    sc.marker(t, "end of Part One")
    return t
