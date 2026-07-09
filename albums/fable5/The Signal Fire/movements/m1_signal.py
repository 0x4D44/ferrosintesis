"""m1_signal — Movement 1 "Signal" (beats 0-176, A aeolian -> dorian, pp->mp).

The beacon in the dark, layers terraced in one at a time:

  beat 0    ch1 sweep pad — Am9/Em/G pools in 16-beat pad_block spans;
            CC74 opens 30->100 across the whole movement (the filter-opening
            that starts the piece), CC11 breathing per chord.
  beat 16   ch0 piano pools — pedalled broken-chord arpeggios (CC64 down per
            8-beat pool, up at the change), sparse, vel 30-50.
  beat 34   ch2 crystal — single notes on degrees {1,5,9}, CC94 echo throw
            on each phrase-final note, slow CC10 autopan drift.
  beat 44   ch3 fretless — the RIFF skeleton in augmentation (4 beats per
            tone), bend_ramp slide into every note from -1.5 semis,
            recentred after each slide.  First statement aeolian (F natural),
            second (beat 100) dorian.
  beat 64   ch14 whistle — THEME_A complete, far away (CC11 40->70),
            delayed vibrato on every note >= 2 beats, echo throw on the
            final note.
  beat 96   the light changes: F# (dorian 6) admitted for the first time —
            the pad voicing blooms Am9 -> Am6, the piano pools brighten
            (Am6, G6, D major), CC74/CC11 lift.
  beat 120  ch9 woodblock taps Morse "CQ CQ CQ" (vel ~32, done by ~139.6).
  beat 160  ignition: kick heartbeat 160/164/168 then 172/174 (vel 60->90),
            bass shifts to short rising pickups, pad CC11 dips to 50.

Seam OUT: one Am pad chord (ch1) struck at 172 sustains ~10 beats across
into M2; nothing else rings past ~178.  All bends recentred by 176.
CC91 stays at the conductor defaults (this movement IS the far distance).
"""

from __future__ import annotations

import math

import conductor as cn
import engine as en
import material as mat
from engine import n

AEO, DOR = "aeolian", "dorian"

A2, A3, A4 = n("A2"), n("A3"), n("A4")     # 45, 57, 69

# The riff skeleton [1, 8, 7, 5, 6, 4, 5, 0, 1], straight from the material.
SKELETON = tuple(mat.riff_skeleton(mat.RIFF_10))


def _pc(mode: str, degs, base: int = A3) -> list[int]:
    """Chord pitch list from degrees (pad_block matches by pitch class)."""
    return [en.pitch(base, mode, d) for d in degs]


# ---------------------------------------------------------------------------
# ch1 — the sweep-pad bed and the CC74 filter opening
# ---------------------------------------------------------------------------

def _pad(sc: en.Score) -> None:
    ch = cn.CH_PAD
    am9 = _pc(AEO, (1, 3, 5, 9))       # A C E B
    em = _pc(AEO, (5, 7, 9))           # E G B
    em7 = _pc(AEO, (5, 7, 9, 11))      # E G B D
    g = _pc(AEO, (7, 9, 11))           # G B D
    am6 = _pc(DOR, (1, 3, 5, 6))       # A C E F#  — the beat-96 bloom
    g6 = _pc(DOR, (7, 9, 11, 12))      # G B D E
    d9 = _pc(DOR, (4, 6, 8, 12))       # D F# A E

    # Ten 16-beat spans, 0-160; the F# enters exactly at 96.
    chords = [am9, am9, em, g, am9, em7, am6, g6, d9, am6]
    en.pad_block(sc, ch, 0.0, chords, 16.0, size=4, lo=52, hi=76,
                 vel=40, vel_end=46)
    # 160-172: thinned Am while the heartbeat starts.
    en.pad_block(sc, ch, 160.0, [_pc(AEO, (1, 3, 5))], 12.0, size=3,
                 lo=52, hi=71, vel=40, legato=0.0)
    # Seam chord: Am struck at 172, ringing ~10 beats into M2.
    for p, v in ((A3, 45), (n("C4"), 43), (n("E4"), 43), (A4, 41)):
        sc.note(ch, p, 172.0, 10.0, v, jt=3, jv=2)

    # The filter opening — breakpoints every 16 beats, a lift at 96.
    en.cc_curve(sc, ch, 74, [
        (0.0, 30), (16.0, 34), (32.0, 39), (48.0, 44), (64.0, 50),
        (80.0, 56), (96.0, 68), (112.0, 76), (128.0, 84), (144.0, 91),
        (160.0, 96), (175.5, 100),
    ], step=0.5)

    # CC11 breathing per chord; the widest breath at the beat-96 bloom;
    # dip to 50 under the 160-176 heartbeat.
    peaks = (66, 68, 70, 68, 72, 70, 76, 72, 75, 74)
    pts: list[tuple[float, int]] = []
    for k, pk in enumerate(peaks):
        s = 16.0 * k
        pts += [(s, 56), (s + 9.0, pk)]
    pts += [(160.0, 50), (173.0, 50), (175.5, 54)]
    en.expr_curve(sc, ch, pts, step=1.0)


# ---------------------------------------------------------------------------
# ch0 — pedalled piano pools (CC64 down per 8-beat harmony, up at changes)
# ---------------------------------------------------------------------------

_UP6 = (0.0, 1.25, 2.5, 3.75, 5.0, 6.25)
_UP5 = (0.0, 1.5, 3.0, 4.5, 6.0)
_SP4 = (0.5, 2.0, 4.0, 6.0)

# (start, mode, degrees-from-A2, note times, vel first -> last)
_POOLS = [
    (16.0, AEO, (1, 5, 8, 10, 12, 15), _UP6, 34, 44),      # Am
    (24.0, AEO, (1, 8, 10, 15), _SP4, 33, 40),
    (32.0, AEO, (5, 9, 12, 14, 16), _UP5, 35, 45),         # Em
    (40.0, AEO, (5, 12, 14, 19), _SP4, 33, 40),
    (48.0, AEO, (7, 11, 14, 16, 18, 21), _UP6, 36, 46),    # G
    (56.0, AEO, (7, 14, 16, 21), _SP4, 34, 41),
    (64.0, AEO, (1, 5, 8, 10, 12, 15), _UP6, 36, 46),      # Am (theme in)
    (72.0, AEO, (1, 8, 12, 15), _SP4, 33, 40),
    # 80-96 the piano rests — pad, crystal and fretless hold the pool.
    (96.0, DOR, (1, 5, 8, 10, 13, 15), _UP6, 40, 50),      # Am6: first F#
    (104.0, DOR, (1, 6, 8, 13, 15), _UP5, 37, 45),
    (112.0, DOR, (7, 11, 14, 16, 18, 21), _UP6, 37, 46),   # G
    (120.0, DOR, (7, 14, 18, 21), _SP4, 33, 40),           # thin, under Morse
    (128.0, DOR, (4, 8, 11, 13, 15, 18), _UP6, 38, 48),    # D major light
    (136.0, DOR, (4, 11, 13, 18), _SP4, 36, 43),
    (144.0, DOR, (1, 5, 8, 10, 13, 15), _UP6, 38, 47),     # Am6 home
]


def _piano(sc: en.Score) -> None:
    ch = cn.CH_PIANO
    for t, mode, degs, times, v0, v1 in _POOLS:
        en.sustain(sc, ch, t, t + 7.9)
        last = max(1, len(times) - 1)
        for i, (d, tt) in enumerate(zip(degs, times)):
            v = int(round(en.lerp(v0, v1, i / last)))
            sc.note(ch, en.pitch(A2, mode, d), t + tt, 2.4, v, jt=6, jv=4)


# ---------------------------------------------------------------------------
# ch2 — crystal echo-sparks on degrees {1, 5, 9}
# ---------------------------------------------------------------------------

# (start, degree order, spacing, +octave, velocity)
_SPARKS = [
    (34.0, (1, 5, 9), 2.0, 0, 34),
    (46.0, (5, 9, 1), 1.5, 0, 36),
    (58.0, (9, 5, 1), 1.75, 0, 35),
    (70.0, (1, 9, 5), 1.5, 1, 36),
    (86.0, (1, 5, 9, 5), 1.25, 0, 37),
    (96.5, (9, 1, 5), 1.5, 1, 40),         # sparkle on the F# bloom
    (110.0, (5, 1, 9), 2.0, 0, 37),
    (126.0, (1, 5, 9), 1.5, 1, 38),
    (142.0, (9, 5, 1), 1.25, 0, 40),
    (152.0, (1, 5, 9), 1.0, 1, 42),
]


def _crystal(sc: en.Score) -> None:
    ch = cn.CH_CRYSTAL
    sc.cc(ch, 94, 20, 30.0)                       # echo-send baseline
    en.autopan(sc, ch, 32.0, 136.0, lo=52, hi=100, period_beats=44, step=1.0)
    for t, order, gap, octv, vel in _SPARKS:
        for i, d in enumerate(order):
            last = i == len(order) - 1
            dur = 3.0 if last else gap * 0.9
            v = vel + (4 if last else 0) - (3 if i == 1 else 0)
            sc.note(ch, en.pitch(A4, AEO, d) + 12 * octv, t + i * gap,
                    dur, v, jt=5, jv=3)
        en.echo_throw(sc, ch, t + (len(order) - 1) * gap,
                      base=20, peak=90, release=2.5)


# ---------------------------------------------------------------------------
# ch3 — fretless: the riff skeleton in augmentation, slid into
# ---------------------------------------------------------------------------

def _fretless(sc: en.Score) -> None:
    ch = cn.CH_BASS
    # Two statements, 4 beats per skeleton tone: aeolian (F natural) at 44,
    # dorian (F#) at 100 — the same line, relit.
    for t0, mode, v0, v1 in ((44.0, AEO, 44, 52), (100.0, DOR, 48, 56)):
        span = len(SKELETON) - 1
        for i, d in enumerate(SKELETON):
            b = t0 + 4.0 * i
            v = int(round(v0 + (v1 - v0) * math.sin(math.pi * i / span)))
            en.bend_ramp(sc, ch, b, b + 0.35, -1.5, 0.0, steps=10)
            sc.note(ch, en.pitch(A2, mode, d), b, 3.2, v, jt=2, jv=3)
    # 160-176: short pickups growing under the heartbeat (no bends).
    pickups = [
        (162.5, 5, 46), (163.5, 0, 48),
        (166.5, 0, 50), (167.5, 1, 52),
        (170.5, 5, 55), (171.5, 0, 57),
        (173.5, 0, 58), (175.0, 1, 60), (175.5, 8, 62),
    ]
    for b, d, v in pickups:
        sc.note(ch, en.pitch(A2, DOR, d), b, 0.4, v, jt=2, jv=2)


# ---------------------------------------------------------------------------
# ch14 — whistle: THEME_A complete at 64, far away
# ---------------------------------------------------------------------------

def _whistle(sc: en.Score) -> None:
    ch = cn.CH_WINDS
    t = 64.0
    for d, start, dur in mat.THEME_A:
        v = int(round(46 + 12 * math.sin(math.pi * start / 32.0)))
        sc.note(ch, en.pitch(A4, AEO, d), t + start, dur * 0.94, v,
                jt=6, jv=3)
        if dur >= 2.0:
            en.vibrato(sc, ch, t + start, dur * 0.94, depth=0.28,
                       cycles_per_beat=1.4, delay=0.5)
    en.expr_curve(sc, ch, [(63.5, 40), (84.0, 62), (92.0, 70), (96.5, 56)],
                  step=1.0)
    en.echo_throw(sc, ch, t + 30.0, base=25, peak=85, release=3.0)


# ---------------------------------------------------------------------------
# ch9 — the Morse beacon and the ignition heartbeat
# ---------------------------------------------------------------------------

def _beacon(sc: en.Score) -> None:
    # "CQ CQ CQ" = 98 units; at unit 0.25 quarter-beats... unit 0.2 ends
    # the call at 120 + 19.6 = 139.6, inside the ~140 window.
    en.morse(sc, "CQ CQ CQ", 120.0, unit=0.2, drum=76, vel=32)


def _ignition(sc: en.Score) -> None:
    for b, v in ((160.0, 60), (164.0, 68), (168.0, 76),
                 (172.0, 84), (174.0, 90)):
        sc.hit(36, b, v, jt=1, jv=2)


def build(sc: en.Score) -> None:
    _pad(sc)
    _piano(sc)
    _crystal(sc)
    _fretless(sc)
    _whistle(sc)
    _beacon(sc)
    _ignition(sc)
