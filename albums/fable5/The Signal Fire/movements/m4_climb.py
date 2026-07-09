"""m4_climb — Movement 4 "The Long Climb" (beats 800-1312, A dorian, 92->112).

THE solo, five waves over the Am | G ground (steel down-down-up strums,
palm-mute root eighths, bass RIFF_FUNK with countermelody fills that grow
wave by wave until the bass is a second melodic voice):

  W1 800-864   lyrical THEME_A statement + paraphrase <= E5, violining
               entries, delayed vibrato, quarter-tone curls on the peaks
  W2 864-928   <= A5: unison bends (ch13 holds the target, ch12 bends a
               whole tone into it), pre-bend-and-release, blue thirds,
               THEME_B cells answering between the bends
  W3 928-992   <= C6: ch13 becomes the +6-cent detune double (hard L/R
               20/108, mirrors ch12 exactly at vel-8), triplet cells, first
               legato run bursts; strings terrace in (roots, CC11 40->70)
  W4 992-1056  <= E6: machine-gun runs vs held wails (CC1 70), choir
               terraces, organ returns with the Leslie ramped to fast,
               clean wah-channel arps, tom fills
  W5 1056-1296 <= B6: legato run chains in four rising 16-bar blocks
               (peaks D5 / F#5 / G6 / B6 — octave-doubled runs from the
               third block), +2 pre-bend wails between the chains;
               mandolin tremolo doubles the strums (1056), flute doubles
               runs 8va (1120), glockenspiel sparkles the peaks (1230)

1296-1310 THE ASCENT: a three-octave climbing 16th run (A2 up to B6) on
ch12+ch13, flute 8va from halfway, glock on the last octave, snare rolling
(drums stop at 1311.75 — the downbeat crash is M5's).  At 1310 both lead
channels strike a G5/D6 dyad and bend it +2 semitones over 1310->1311.9 so
the whole texture slides up into the A-major downbeat; both channels are
recentred exactly at 1312.0 (ch13's detune segment officially ends there).

CC91 eases 55->40 across the movement (each terrace joins the curve at its
entry value); ch12 rides CC94 35 with echo throws at wave ends.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

DOR = "dorian"

T0, T1 = 800.0, 1312.0
W2, W3, W4, W5, ASC = 864.0, 928.0, 992.0, 1056.0, 1296.0
BARS = 128

LEAD_A = n("A3")            # 57 — lead/double degree-1 anchor
BASS_A = n("A1")            # 33 — bass degree-1 anchor
ASC_A = n("A2")             # 45 — the final ascent starts an octave down

# Guitar voicings around A3 (roadmap: 4-5 note strums on 1 and 7).
AM_STRUM = [45, 52, 57, 60, 64]     # A2 E3 A3 C4 E4
G_STRUM = [43, 50, 55, 59, 62]      # G2 D3 G3 B3 D4

# Bass countermelody fills for bars 4/8 of each 8-bar cycle, growing wave
# by wave (approach runs -> octave drops -> 0-1 pivots -> full-bar voice).
FILL_W1 = [(3, 2.0, 0.5), (4, 2.5, 0.5), (5, 3.0, 0.5), (6, 3.5, 0.5)]
FILL_W2 = [(8, 2.0, 0.75), (5, 2.75, 0.25), (6, 3.0, 0.5), (7, 3.5, 0.5)]
FILL_W3 = [(0, 2.0, 0.25), (1, 2.25, 0.25), (0, 2.5, 0.25), (1, 2.75, 0.25),
           (3, 3.0, 0.25), (4, 3.25, 0.25), (5, 3.5, 0.25), (6, 3.75, 0.25)]
FILL_W4 = [(1, 0.0, 0.5), (8, 0.5, 0.5), (7, 1.0, 0.25), (5, 1.25, 0.25),
           (6, 1.5, 0.5), (4, 2.0, 0.5), (5, 2.5, 0.25), (6, 2.75, 0.25),
           (7, 3.0, 0.5), (8, 3.5, 0.5)]
# By wave 5 the fills sing THEME_B's opening cell (octave pivot appended).
FILL_W5 = [(1, 0.0, 0.5), (3, 0.5, 0.5), (5, 1.0, 0.75), (5, 1.75, 0.25),
           (6, 2.0, 0.5), (5, 2.5, 0.5), (3, 3.0, 0.5), (8, 3.5, 0.5)]
# W5 bar-8 countermelody variants (full bars, one per 8-bar cycle) so the
# countermelody keeps growing instead of freezing on one shape.  Vocabulary
# reused from the fills above: octave-drop pivots, a 3-4-5-6 approach run, a
# 0-1 pivot, and a rising run gesturing into the 1296 ascent.
FILL_W5_OCT = [(8, 0.0, 0.5), (1, 0.5, 0.5), (8, 1.0, 0.5), (5, 1.5, 0.5),
               (6, 2.0, 0.5), (5, 2.5, 0.5), (3, 3.0, 0.5), (1, 3.5, 0.5)]
FILL_W5_APP = [(1, 0.0, 0.5), (1, 0.5, 0.5), (3, 1.0, 0.5), (4, 1.5, 0.5),
               (5, 2.0, 0.5), (6, 2.5, 0.5), (5, 3.0, 0.5), (3, 3.5, 0.5)]
FILL_W5_PIV = [(1, 0.0, 0.5), (0, 0.5, 0.5), (1, 1.0, 0.5), (0, 1.5, 0.5),
               (1, 2.0, 0.5), (5, 2.5, 0.5), (1, 3.0, 0.5), (0, 3.5, 0.5)]
FILL_W5_RISE = [(1, 0.0, 0.5), (3, 0.5, 0.5), (5, 1.0, 0.5), (6, 1.5, 0.5),
                (8, 2.0, 0.5), (9, 2.5, 0.5), (10, 3.0, 0.5), (11, 3.5, 0.5)]
W5_FILLS = [FILL_W5, FILL_W5_OCT, FILL_W5_APP, FILL_W5_PIV,
            FILL_W4, FILL_W5, FILL_W5_RISE, FILL_W5_RISE]

# W1 paraphrase of THEME_A's opening arch (stays under A4).
PARA_W1 = [(5, 0, 2), (6, 2, 0.5), (7, 2.5, 0.5), (8, 3, 2.5),
           (7, 5.5, 0.5), (5, 6, 1.5), (3, 7.5, 0.5),
           (4, 8, 1), (6, 9, 1), (7, 10, 2),
           (5, 12, 1), (2, 13, 0.5), (1, 13.5, 2.5)]

# THEME_B's answering cell (beats 4-8) rebased to start at 0.
CELL_B2 = [(d, s - 4.0, du) for d, s, du in m.THEME_B[7:14]]


def _am(i: int) -> bool:
    return i % 2 == 0


def _lp(deg: int) -> int:
    return en.pitch(LEAD_A, DOR, deg)


# ---------------------------------------------------------------------------
# Controllers — distance arc, echo, vibrato depth, expression
# ---------------------------------------------------------------------------
def _controllers(sc):
    # CC91 distance arc 55 -> 40; each terrace joins at its entry value.
    def ease(ch, start):
        v0 = int(round(55.0 - 15.0 * (start - T0) / (T1 - T0)))
        en.cc_curve(sc, ch, 91, [(start, v0), (1311.5, 40)], step=16.0)

    for ch in (cd.CH_BASS, cd.CH_STEEL, cd.CH_DRUMS, cd.CH_RHYTHM,
               cd.CH_LEAD, cd.CH_DOUBLE):
        ease(ch, T0)
    ease(cd.CH_STRINGS, W3)
    for ch in (cd.CH_ORGAN, cd.CH_CHOIR, cd.CH_WAH):
        ease(ch, W4)
    ease(cd.CH_BELLS, W5)
    ease(cd.CH_WINDS, 1120.0)
    ease(cd.CH_CRYSTAL, 1230.0)

    # Lead echo send (delayed-lead 35) and mod-wheel vibrato depth per wave.
    sc.cc(cd.CH_LEAD, 94, 35, T0)
    sc.cc(cd.CH_DOUBLE, 94, 35, W3)
    sc.cc(cd.CH_LEAD, 1, 30, T0)
    sc.cc(cd.CH_LEAD, 1, 42, W2)
    for ch in (cd.CH_LEAD, cd.CH_DOUBLE):
        sc.cc(ch, 1, 55, W3)
        sc.cc(ch, 1, 70, W4)
        sc.cc(ch, 1, 78, W5)
        sc.cc(ch, 1, 88, 1184.0)

    # Lead expression: violining swells (W1/W2 entries) over a slow rise.
    sc.cc(cd.CH_LEAD, 11, 88, T0)
    for t in (807.7, 845.7, 863.6, 903.6):
        en.expr_curve(sc, cd.CH_LEAD, [(t, 12), (t + 1.9, 92)], step=0.2)
    en.expr_curve(sc, cd.CH_LEAD,
                  [(W3, 90), (W5, 96), (ASC, 100), (1310.0, 110)], step=8.0)
    sc.cc(cd.CH_DOUBLE, 11, 90, W2)
    en.expr_curve(sc, cd.CH_DOUBLE,
                  [(W3, 88), (ASC, 96), (1310.0, 106)], step=8.0)

    # The hard L/R double-track split at wave 3 (restored for M5's centre).
    sc.cc(cd.CH_LEAD, 10, 20, W3)
    sc.cc(cd.CH_DOUBLE, 10, 108, W3)
    sc.cc(cd.CH_LEAD, 10, 64, T1)
    sc.cc(cd.CH_DOUBLE, 10, 64, T1)

    # ch13's +6-cent detune segment (whitelisted 928-1312 in verify.py).
    en.detune(sc, cd.CH_DOUBLE, 0.06, W3)


# ---------------------------------------------------------------------------
# The ground: steel strums, palm-mute eighths, RIFF_FUNK bass with fills
# ---------------------------------------------------------------------------
def _ground(sc):
    for i in range(BARS):
        b = T0 + 4 * i
        grow = i / (BARS - 1)
        voice = AM_STRUM if _am(i) else G_STRUM
        v = int(lerp(58, 68, grow))
        # down - down - up per bar
        en.strum(sc, cd.CH_STEEL, voice[:4], b, 1.9, v, down=True)
        en.strum(sc, cd.CH_STEEL, voice[1:4], b + 2.0, 0.95, v - 5, down=True)
        en.strum(sc, cd.CH_STEEL, voice[3:5], b + 3.0, 0.9, v - 8, down=False)
        # palm-mute root: W1 sustained roots (make room for the lead), W2
        # quarter-note chug (mid density), W3+ the full driving eighths.
        root = 45 if _am(i) else 43
        cv = int(lerp(69, 77, grow))
        if b < W2:                          # W1: one sustained root per 2 beats
            for k in range(2):
                sc.note(cd.CH_RHYTHM, root, b + 2.0 * k, 1.85, cv + 2,
                        jt=3, jv=3)
        elif b < W3:                        # W2: quarter-note chug
            for k in range(4):
                acc = 5 if k == 0 else (2 if k == 2 else -2)
                sc.note(cd.CH_RHYTHM, root, b + 1.0 * k, 0.9, cv + acc,
                        jt=3, jv=3)
        else:                               # W3+: full driving eighths
            for k in range(8):
                acc = 5 if k in (0, 4) else (2 if k in (2, 6) else -3)
                sc.note(cd.CH_RHYTHM, root, b + 0.5 * k, 0.23, cv + acc,
                        jt=3, jv=3)


def _bass(sc):
    for i in range(BARS):
        b = T0 + 4 * i
        sh = 0 if _am(i) else -1
        wave = min(4, i // 16)
        vel = int(lerp(86, 97, i / (BARS - 1)))
        pos = i % 8
        if wave == 0:                       # W1: half-time roots for the lead
            if i % 4 == 3:                  # one dominant pickup per 4 bars
                en.line(sc, cd.CH_BASS, b, BASS_A, DOR,
                        [(1, 0.0, 1.85), (1, 2.0, 1.3)], vel, shift=sh,
                        gate=0.92, jt=4)
                sc.note(cd.CH_BASS, en.pitch(BASS_A, DOR, 5), b + 3.5, 0.45,
                        vel, jt=4, jv=4)    # the fifth -> pickup into the A
            else:
                en.line(sc, cd.CH_BASS, b, BASS_A, DOR,
                        [(1, 0.0, 1.85), (1, 2.0, 1.85)], vel, shift=sh,
                        gate=0.92, jt=4)
            continue
        if pos == 7 and wave >= 3:
            if wave == 3:
                fill = FILL_W4
            else:                           # W5: vary the bar-8 countermelody
                fill = W5_FILLS[((i - 71) // 8) % len(W5_FILLS)]
            en.line(sc, cd.CH_BASS, b, BASS_A, DOR, fill, vel + 4,
                    shift=sh, gate=0.9, jt=4)
            continue
        if pos in (3, 7):
            head = [nt for nt in m.RIFF_FUNK if nt[1] < 2.0]
            fill = (FILL_W1, FILL_W2, FILL_W3, FILL_W3, FILL_W3)[wave]
            en.line(sc, cd.CH_BASS, b, BASS_A, DOR, head + fill, vel + 2,
                    shift=sh, gate=0.95, jt=4)
            continue
        en.line(sc, cd.CH_BASS, b, BASS_A, DOR, m.RIFF_FUNK, vel,
                shift=sh, gate=0.95, jt=4)
        if wave >= 2 and pos == 1:
            en.line(sc, cd.CH_BASS, b, BASS_A, DOR, m.RIFF_FUNK_GHOSTS,
                    vel - 30, shift=sh, gate=0.9, jt=4)


# ---------------------------------------------------------------------------
# Drums — assemble wave by wave; the ascent roll stops at 1311.75
# ---------------------------------------------------------------------------
def _drums(sc):
    for i in range(BARS):
        b = T0 + 4 * i
        if b >= ASC:
            break
        wave = min(4, i // 16)
        grow = i / 123.0
        if wave == 0:
            continue                        # W1: the lyrical wave is bare
        if wave == 1:                       # W2: heartbeat kick + soft hats
            sc.hit(36, b, 76)
            sc.hit(36, b + 2, 70)
            sc.hit(42, b + 1, 44)
            sc.hit(42, b + 3, 46)
            continue
        # W3 on: the kit proper
        kv = int(lerp(88, 102, grow))
        sv = int(lerp(86, 102, grow))
        sc.hit(36, b, kv)
        sc.hit(36, b + 2.5, kv - 8)
        if wave == 4:
            sc.hit(36, b + 2, kv - 4)
        sc.hit(38, b + 1, sv)
        fill = (i % 8 == 7)
        if not (fill and wave >= 3):
            sc.hit(38, b + 3, sv + 2)
        if wave == 2:                       # hats on the offbeats
            sc.hit(42, b + 0.5, 46)
            sc.hit(42, b + 1.5, 50)
            sc.hit(42, b + 2.5, 46)
            sc.hit(42, b + 3.5, 52)
            if i % 4 == 2:
                sc.hit(38, b + 1.75, 42)    # ghost
        elif wave == 3:
            for k in range(4):
                sc.hit(42, b + k + 0.5, 48 + (6 if k % 2 else 0))
            sc.hit(46, b + 3.5, 58)
            if fill:                        # tom build into the next cycle
                for j, (drum, vv) in enumerate(
                        ((48, 78), (45, 84), (43, 90), (41, 96))):
                    sc.hit(drum, b + 3.0 + 0.25 * j, vv)
        else:                               # wave 4: drive + block crashes
            sc.hit(42, b + 1.5, 54)
            sc.hit(42, b + 3.5, 56)
            sc.hit(46, b + 2.5, 60)
            if (b - W5) % 64 == 0:
                sc.hit(49, b, 104)
            if fill:
                if i >= 100:                # double-time 16th fills late on
                    for j in range(6):
                        drum = 38 if j % 2 == 0 else (48, 45, 43)[j // 2]
                        sc.hit(drum, b + 2.5 + 0.25 * j,
                               int(lerp(78, 104, j / 5)))
                else:
                    for j, (drum, vv) in enumerate(
                            ((38, 88), (48, 84), (45, 92), (41, 98))):
                        sc.hit(drum, b + 3.0 + 0.25 * j, vv)
    # THE ASCENT: snare roll crescendo + kick quarters; stop at 1311.75.
    for k in range(64):
        sc.hit(38, ASC + 0.25 * k, int(lerp(58, 118, k / 63)), jt=2, jv=3)
    for k in range(16):
        sc.hit(36, ASC + k, int(lerp(96, 116, k / 15)))
    sc.hit(47, 1304.0, 96)
    sc.hit(43, 1308.0, 104)


# ---------------------------------------------------------------------------
# Terraces — strings 928, choir 992, organ 992, wah arps 992, mandolin 1056,
# flute 1120 (inside wave 5), glockenspiel 1230
# ---------------------------------------------------------------------------
def _strings(sc):
    for i in range(32, BARS):
        b = T0 + 4 * i
        root = 57 if _am(i) else 55         # pad roots only (A3 / G3)
        v = int(lerp(50, 60, (i - 32) / 95.0))
        sc.note(cd.CH_STRINGS, root, b, min(4.1, 1311.7 - b), v, jt=3)
        if i >= 64 and i % 4 == 0:
            sc.note(cd.CH_STRINGS, root + 7, b, min(8.1, 1311.7 - b),
                    v - 6, jt=3)
    en.expr_curve(sc, cd.CH_STRINGS, [(W3, 40), (W4, 70)], step=1.0)
    en.expr_curve(sc, cd.CH_STRINGS,
                  [(W5, 72), (1200.0, 80), (ASC, 88), (1311.0, 94)], step=4.0)


def _choir(sc):
    for i in range(48, BARS):
        b = T0 + 4 * i
        root = 69 if _am(i) else 67         # A4 / G4 "mm-ah"
        v = int(lerp(56, 66, (i - 48) / 79.0))
        sc.note(cd.CH_CHOIR, root, b, min(4.15, 1311.7 - b), v, jt=4)
        if i % 4 == 0:
            sc.note(cd.CH_CHOIR, root + 3 if _am(i) else root + 4, b,
                    min(4.15, 1311.7 - b), v - 6, jt=4)
    for k in range(10):                     # breathing swells per 8 bars
        s0 = W4 + 32.0 * k
        en.expr_curve(sc, cd.CH_CHOIR,
                      [(s0, 52), (s0 + 20, 72 + k), (s0 + 31, 58)], step=2.0)


def _organ(sc):
    # Sustained tonic-pedal power fifths; Leslie choreography underneath.
    for i in range(48, BARS, 2):
        b = T0 + 4 * i
        v = int(lerp(72, 82, (i - 48) / 79.0))
        for p, dv in ((45, 0), (52, -4)):   # A2 + E3
            sc.note(cd.CH_ORGAN, p, b, min(8.1, 1311.7 - b), v + dv, jt=3)
    sc.cc(cd.CH_ORGAN, 11, 84, W4)
    en.leslie(sc, cd.CH_ORGAN, W4, 1006.0, 12, 127)      # spin up
    en.leslie(sc, cd.CH_ORGAN, 1022.0, 1030.0, 127, 45)  # settle
    en.leslie(sc, cd.CH_ORGAN, 1052.0, 1064.0, 45, 127)  # fast for the peak


def _wah_arps(sc):
    # ch11 clean arps: eighths in W4 phrases, sixteenths inside wave 5.
    for i in list(range(50, 64, 4)) + list(range(51, 64, 4)):
        b = T0 + 4 * i
        pcs = ([57, 60, 64, 69] if _am(i) else [55, 59, 62, 67])
        en.arp(sc, cd.CH_WAH, pcs, b, 8, 0.5, 66, gate=0.9,
               accent_every=4, accent=8)
    for i in (66, 67, 82, 83):
        b = T0 + 4 * i
        pcs = ([57, 60, 64, 69] if _am(i) else [55, 59, 62, 67])
        en.arp(sc, cd.CH_WAH, pcs, b, 16, 0.25, 68, pattern="updown",
               gate=0.95, accent_every=4, accent=8)


def _mandolin(sc):
    # Tremolo (32nd repeats) doubling the strum downbeats, every 4th bar.
    for i in range(64, 124, 4):
        b = T0 + 4 * i
        p = 64 if _am(i) else 62            # the voicing's top-but-one
        vg = int(lerp(0, 8, (i - 64) / 59.0))
        for k in range(6):
            sc.note(cd.CH_BELLS, p, b + 0.125 * k, 0.12,
                    int(lerp(56, 70, k / 5.0)) + vg, jt=2, jv=3)


def _glock_sparkle(sc):
    # Glockenspiel pings on the plateau peaks (program 9 from beat 1230).
    for b, p in ((1230.0, 88), (1236.0, 86), (1240.0, 88), (1244.0, 91),
                 (1252.75, 95), (1264.0, 93), (1288.0, 95), (1292.0, 90)):
        sc.note(cd.CH_CRYSTAL, p, b, 1.5, 86, jt=3)
        sc.note(cd.CH_CRYSTAL, p + 12, b + 0.02, 1.2, 78, jt=3)


# ---------------------------------------------------------------------------
# Solo helpers
# ---------------------------------------------------------------------------
def _duo_line(sc, t0, notes, vel, gate=0.92, jt=3, octave=0):
    en.line(sc, cd.CH_LEAD, t0, LEAD_A, DOR, notes, vel,
            gate=gate, jt=jt, octave=octave)
    en.line(sc, cd.CH_DOUBLE, t0, LEAD_A, DOR, notes, vel - 8,
            gate=gate, jt=jt, octave=octave)


def _duo_run(sc, t0, degs, spacing, v0, v1, legato=True, octave_double=None):
    en.run(sc, cd.CH_LEAD, t0, LEAD_A, DOR, degs, spacing, v0, v1,
           legato=legato, octave_double=octave_double)
    en.run(sc, cd.CH_DOUBLE, t0, LEAD_A, DOR, degs, spacing, v0 - 8, v1 - 8,
           legato=legato, octave_double=octave_double)
    return t0 + len(degs) * spacing


def _duo_wail(sc, deg, t, dur, vel, depth=0.4):
    p = _lp(deg)
    sc.note(cd.CH_LEAD, p, t, dur, vel, jt=2)
    sc.note(cd.CH_DOUBLE, p, t, dur, vel - 8, jt=2)
    en.vibrato(sc, cd.CH_LEAD, t, dur, depth=depth, delay=0.35)
    en.vibrato(sc, cd.CH_DOUBLE, t, dur, depth=depth * 0.8, delay=0.45,
               center=0.06)


def _duo_prebend(sc, t, deg_top, dur, vel):
    """Both channels pre-bent +2, striking deg_top, releasing a whole tone."""
    p = _lp(deg_top) - 2
    sc.bend(cd.CH_LEAD, t - 0.06, 2.0)
    sc.bend(cd.CH_DOUBLE, t - 0.06, 2.0)
    sc.note(cd.CH_LEAD, p, t, dur, vel, jt=0)
    sc.note(cd.CH_DOUBLE, p, t, dur, vel - 8, jt=0)
    en.bend_ramp(sc, cd.CH_LEAD, t + 0.4, t + 0.9, 2.0, 0.0, steps=8)
    en.bend_ramp(sc, cd.CH_DOUBLE, t + 0.4, t + 0.9, 2.0, 0.06, steps=8)
    en.vibrato(sc, cd.CH_LEAD, t + 1.1, dur - 1.1, depth=0.4, delay=0.1)
    en.vibrato(sc, cd.CH_DOUBLE, t + 1.1, dur - 1.1, depth=0.32, delay=0.15,
               center=0.06)


def _unison_bend(sc, t, deg_target, dur, vel):
    """W2: ch13 holds the target straight; ch12 bends a whole tone into it."""
    p = _lp(deg_target)
    sc.note(cd.CH_DOUBLE, p, t, dur, vel - 8, jt=3)
    sc.note(cd.CH_LEAD, p - 2, t, dur, vel, jt=0)
    en.bend_ramp(sc, cd.CH_LEAD, t + 0.2, t + 0.5, 0.0, 2.0, steps=8)
    en.vibrato(sc, cd.CH_LEAD, t + 1.0, dur - 1.6, depth=0.3,
               cycles_per_beat=1.4, delay=0.2, center=2.0)
    en.bend_ramp(sc, cd.CH_LEAD, t + dur - 0.5, t + dur - 0.1, 2.0, 0.0,
                 steps=6)


def _prebend_release(sc, t, deg_top, dur, vel):
    p = _lp(deg_top) - 2
    sc.bend(cd.CH_LEAD, t - 0.05, 2.0)
    sc.note(cd.CH_LEAD, p, t, dur, vel, jt=0)
    en.bend_ramp(sc, cd.CH_LEAD, t + 0.45, t + 0.95, 2.0, 0.0, steps=8)
    en.vibrato(sc, cd.CH_LEAD, t + 1.2, dur - 1.2, depth=0.3, delay=0.1)


def _blue_third(sc, t, vel):
    sc.note(cd.CH_LEAD, _lp(10), t, 1.5, vel, jt=0)   # C5, the blue third
    en.bend_ramp(sc, cd.CH_LEAD, t + 0.15, t + 0.5, 0.0, 0.5, steps=6)
    en.bend_ramp(sc, cd.CH_LEAD, t + 0.9, t + 1.3, 0.5, 0.0, steps=6)


def _echo(sc, beat):
    en.echo_throw(sc, cd.CH_LEAD, beat, base=35, peak=90)
    if beat >= W3:
        en.echo_throw(sc, cd.CH_DOUBLE, beat, base=35, peak=82)


# ---------------------------------------------------------------------------
# Wave 1 (800-864): THEME_A sung whole, then paraphrased
# ---------------------------------------------------------------------------
def _wave1(sc):
    ch = cd.CH_LEAD
    for deg, s, d in m.THEME_A:
        b = 808.0 + s
        v = int(lerp(78, 90, s / 31.0)) + (4 if deg == 11 else 0)
        sc.note(ch, _lp(deg), b, d * 0.94, v, jt=4)
        if deg == 11:                       # the arch's peak: curl + vibrato
            en.bend_ramp(sc, ch, b + 0.15, b + 0.45, 0.0, 0.42, steps=5)
            en.bend_ramp(sc, ch, b + 0.5, b + 0.8, 0.42, 0.0, steps=5)
            en.vibrato(sc, ch, b, d * 0.94, depth=0.3, delay=1.2)
        elif deg == 8 and s == 16:          # quarter-tone curl on the A
            en.bend_ramp(sc, ch, b + 0.2, b + 0.5, 0.0, 0.4, steps=5)
            en.bend_ramp(sc, ch, b + 0.55, b + 0.85, 0.4, 0.0, steps=5)
        elif d >= 2.0:
            en.vibrato(sc, ch, b, d * 0.94, depth=0.28, delay=0.4)
    # 840-846 breath; the paraphrase answers, dying back toward wave 2
    for deg, s, d in PARA_W1:
        b = 846.0 + s
        v = int(lerp(82, 88, s / 15.0))
        sc.note(ch, _lp(deg), b, d * 0.93, v, jt=4)
        if d >= 2.0:
            en.vibrato(sc, ch, b, d * 0.93, depth=0.26, delay=0.4)
    _echo(sc, 861.0)


# ---------------------------------------------------------------------------
# Wave 2 (864-928): unison bends, pre-bends, blue thirds
# ---------------------------------------------------------------------------
def _wave2(sc):
    _unison_bend(sc, 864.0, 12, 3.5, 94)                 # bend into E5
    en.line(sc, cd.CH_LEAD, 868.0, LEAD_A, DOR, m.THEME_B[:7], 84, gate=0.9)
    en.line(sc, cd.CH_LEAD, 873.0, LEAD_A, DOR, CELL_B2, 86, gate=0.9)
    _blue_third(sc, 877.0, 90)
    en.line(sc, cd.CH_LEAD, 878.5, LEAD_A, DOR,
            [(9, 0, 0.5), (8, 0.5, 0.5), (7, 1.0, 1.0)], 86, gate=0.9)
    _prebend_release(sc, 880.5, 13, 2.5, 92)             # F#5 falling to E5
    _unison_bend(sc, 888.0, 11, 3.0, 92)                 # bend into D5
    en.line(sc, cd.CH_LEAD, 892.0, LEAD_A, DOR, m.THEME_B[:7], 86, gate=0.9)
    en.line(sc, cd.CH_LEAD, 896.0, LEAD_A, DOR,
            [(8, 0, 0.75), (7, 0.75, 0.75), (6, 1.5, 0.75), (5, 2.25, 1.75)],
            88, gate=0.92)
    en.vibrato(sc, cd.CH_LEAD, 898.25, 1.7, depth=0.28, delay=0.3)
    _blue_third(sc, 900.5, 90)
    en.line(sc, cd.CH_LEAD, 903.0, LEAD_A, DOR,
            [(9, 0, 0.25), (10, 0.25, 0.25), (12, 0.5, 0.5)], 92, gate=0.9)
    _unison_bend(sc, 904.0, 15, 4.0, 98)                 # the A5 climax
    en.line(sc, cd.CH_LEAD, 912.0, LEAD_A, DOR,
            [(12, 0, 1), (11, 1, 0.5), (9, 1.5, 0.5), (8, 2, 1.5),
             (7, 3.5, 0.5), (5, 4, 3)], 90, gate=0.94)
    en.vibrato(sc, cd.CH_LEAD, 916.0, 2.8, depth=0.3, delay=0.4)
    _prebend_release(sc, 920.0, 12, 2.0, 94)             # E5 falling to D5
    en.line(sc, cd.CH_LEAD, 923.0, LEAD_A, DOR,
            [(5, 0, 0.5), (7, 0.5, 0.5), (8, 1, 2)], 90, gate=0.92)
    en.vibrato(sc, cd.CH_LEAD, 924.0, 1.9, depth=0.28, delay=0.3)
    _echo(sc, 925.5)


# ---------------------------------------------------------------------------
# Wave 3 (928-992): detune double, triplet cells, first legato bursts
# ---------------------------------------------------------------------------
def _wave3(sc):
    tp = 1.0 / 3.0
    e = _duo_run(sc, 929.0, [8, 7, 5, 6, 5, 3, 5, 4, 2, 1], tp, 86, 94,
                 legato=False)
    _duo_wail(sc, 1, e + 0.05, 1.6, 90, depth=0.3)
    e = _duo_run(sc, 936.0, list(range(1, 12)), 0.25, 88, 98)   # first burst
    _duo_wail(sc, 12, e, 2.25, 96)
    e = _duo_run(sc, 944.0, [5, 6, 7, 7, 8, 9, 9, 10, 11, 11, 12, 13],
                 tp, 88, 96, legato=False)
    _duo_wail(sc, 13, e, 2.0, 94)
    e = _duo_run(sc, 952.0, list(range(3, 15)) + [13, 12, 11, 10], 0.25,
                 90, 100)
    _duo_wail(sc, 8, e, 1.5, 92, depth=0.3)
    _duo_line(sc, 960.0, m.THEME_B[:7], 92, octave=1)
    _duo_line(sc, 964.0, CELL_B2, 92, octave=1)
    e = _duo_run(sc, 968.0, [12, 11, 9, 10, 9, 7, 8, 7, 5, 6, 5, 3],
                 tp, 90, 96, legato=False)
    _duo_wail(sc, 5, e, 1.5, 90, depth=0.3)
    e = _duo_run(sc, 976.0, list(range(1, 16)) + [14, 13, 12, 11, 10], 0.25,
                 90, 100)
    _duo_wail(sc, 10, e, 2.0, 94)
    e = _duo_run(sc, 984.0, list(range(5, 18)), 0.25, 92, 102)
    _duo_wail(sc, 17, e, 3.0, 100, depth=0.45)           # C6 — the ceiling
    _echo(sc, 990.0)


# ---------------------------------------------------------------------------
# Wave 4 (992-1056): machine-gun runs vs held wails
# ---------------------------------------------------------------------------
def _wave4(sc):
    e = _duo_run(sc, 992.0, list(range(1, 13)) + [11, 10, 9, 8], 0.25,
                 92, 102)
    _duo_wail(sc, 12, e, 2.5, 100, depth=0.5)
    e = _duo_run(sc, 1000.0, list(range(5, 17)), 0.25, 94, 102)
    _duo_wail(sc, 16, e, 2.0, 102, depth=0.5)
    e = _duo_run(sc, 1008.0,
                 [1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 7, 8, 9, 10, 11, 12, 13, 14],
                 0.25, 92, 102)
    _duo_wail(sc, 14, e, 2.0, 100)
    _duo_prebend(sc, 1016.0, 12, 2.5, 98)                # E5 wail, falls
    _duo_line(sc, 1019.0, [(11, 0, 1), (12, 1, 1)], 96)
    _duo_wail(sc, 13, 1021.0, 2.5, 98)
    e = _duo_run(sc, 1024.0, list(range(3, 18)), 0.25, 94, 104)
    _duo_wail(sc, 17, e, 2.25, 102)                      # C6 again
    _duo_run(sc, 1031.0, list(range(17, 7, -1)), 0.25, 100, 92)
    _duo_line(sc, 1036.0, [(5, 0, 1.5), (3, 1.5, 0.5), (4, 2, 1), (2, 3, 1)],
              96, octave=1)                              # THEME_A_FRAG 8va
    e = _duo_run(sc, 1040.0, list(range(5, 20)), 0.25, 96, 106)
    _duo_wail(sc, 19, e, 3.25, 104, depth=0.5)           # E6 — the ceiling
    _echo(sc, 1046.5)
    _duo_line(sc, 1048.0,
              [(15, 0, 0.75), (14, 0.75, 0.75), (12, 1.5, 0.75),
               (11, 2.25, 0.75), (9, 3, 1)], 96)
    _duo_wail(sc, 8, 1052.0, 2.5, 92, depth=0.35)


# ---------------------------------------------------------------------------
# Wave 5 (1056-1296): four rising blocks, octave-doubled run chains
# ---------------------------------------------------------------------------
def _w5_block(sc, t, cap, vb, k):
    dbl = 12 if k >= 2 else None            # octave doubling from block 3
    degs = list(range(1, cap + 1)) + [cap - 2, cap - 1, cap]
    e = _duo_run(sc, t, degs, 0.25, vb, vb + 10, octave_double=dbl)
    _duo_wail(sc, cap, e, 2.5, vb + 6, depth=0.5)
    _duo_line(sc, t + 8.0, m.THEME_B[:7], vb - 4, octave=1)
    # t+12..16: breath — the bass countermelody fill answers alone
    _duo_prebend(sc, t + 16.0, cap, 3.0, vb + 6)
    _duo_line(sc, t + 19.5,
              [(cap - 4, 0, 0.75), (cap - 5, 0.75, 0.75), (cap - 6, 1.5, 1.5)],
              vb - 2)
    _duo_line(sc, t + 24.0, CELL_B2, vb - 4, octave=1)
    # t+28..32: breath — the bass sings THEME_B's cell
    e = _duo_run(sc, t + 32.0, list(range(3, cap + 1)), 0.25, vb, vb + 8,
                 octave_double=(12 if k == 3 else None))
    _duo_wail(sc, cap - 1, e, 2.0, vb + 4)
    if k % 2 == 1:
        _duo_prebend(sc, t + 40.0, cap, 2.5, vb + 8)
    else:
        _duo_wail(sc, cap, t + 40.0, 2.5, vb + 8, depth=0.5)
    _echo(sc, t + 42.5)
    if k == 3:                              # short block: breathe into 1296
        return
    e = _duo_run(sc, t + 48.0, list(range(cap - 8, cap + 1)), 0.25,
                 vb - 2, vb + 6)
    _duo_wail(sc, cap, e, 2.0, vb + 6)
    _duo_line(sc, t + 56.0,
              [(8, 0, 0.5), (10, 0.5, 0.5), (11, 1, 0.5), (12, 1.5, 1.5)],
              vb - 2)
    _echo(sc, t + 58.5)
    _duo_run(sc, t + 62.0, [5, 6, 7, 8], 0.25, vb - 6, vb + 2, legato=False)


def _wave5(sc):
    caps = (11, 13, 14, 16)                 # peaks D5 / F#5 / G6 / B6 (top two octave-doubled)
    for k, t in enumerate((1056.0, 1120.0, 1184.0, 1248.0)):
        _w5_block(sc, t, caps[k], 96 + 3 * k, k)
    # flute doubles the mountain runs an octave up from 1120
    for k, t in ((1, 1120.0), (2, 1184.0), (3, 1248.0)):
        cap = caps[k]
        degs = list(range(1, cap + 1)) + [cap - 2, cap - 1, cap]
        en.run(sc, cd.CH_WINDS, t, LEAD_A + 12, DOR, degs, 0.25,
               84 - 8, 94 - 8, legato=False, gate=0.85)


# ---------------------------------------------------------------------------
# The ascent (1296-1312) and the whole-chord bend into Ascension
# ---------------------------------------------------------------------------
def _ascent(sc):
    degs = []
    for k in range(14):                     # A2 climbing to B6, zigzag 16ths
        degs += [1 + 2 * k, 2 + 2 * k, 3 + 2 * k, 4 + 2 * k]
    en.run(sc, cd.CH_LEAD, ASC, ASC_A, DOR, degs, 0.25, 84, 114,
           legato=False, jt=1)
    en.run(sc, cd.CH_DOUBLE, ASC, ASC_A, DOR, degs, 0.25, 76, 106,
           legato=False, jt=1)
    for i, deg in enumerate(degs[28:52]):   # flute joins 8va from halfway
        sc.note(cd.CH_WINDS, en.pitch(ASC_A + 12, DOR, deg),
                1303.0 + 0.25 * i, 0.22, int(lerp(78, 100, i / 23.0)), jt=1)
    for i in range(44, 56, 2):              # glock on the last octave
        sc.note(cd.CH_CRYSTAL, en.pitch(ASC_A + 12, DOR, degs[i]),
                ASC + 0.25 * i, 0.4, int(lerp(84, 100, (i - 44) / 11.0)),
                jt=1)
    # The final G5/D6 dyad, bent +2 semitones into the A-major downbeat.
    for p, v in ((79, 112), (86, 106)):
        sc.note(cd.CH_LEAD, p, 1310.0, 2.0, v, jt=0)
    for p, v in ((67, 104), (74, 100)):
        sc.note(cd.CH_DOUBLE, p, 1310.0, 2.0, v, jt=0)
    en.bend_ramp(sc, cd.CH_LEAD, 1310.0, 1311.9, 0.0, 2.0, steps=20)
    en.bend_ramp(sc, cd.CH_DOUBLE, 1310.0, 1311.9, 0.06, 2.0, steps=20)
    sc.bend(cd.CH_LEAD, 1312.0, 0.0)        # the recentre the oracle checks
    sc.bend(cd.CH_DOUBLE, 1312.0, 0.0)


def build(sc):
    _controllers(sc)
    _ground(sc)
    _bass(sc)
    _drums(sc)
    _strings(sc)
    _choir(sc)
    _organ(sc)
    _wah_arps(sc)
    _mandolin(sc)
    _glock_sparkle(sc)
    _wave1(sc)
    _wave2(sc)
    _wave3(sc)
    _wave4(sc)
    _wave5(sc)
    _ascent(sc)
