"""m6_afterglow — Movement 6 "Afterglow" (beats 1592-1678, A ionian, rit.).

The intimate bookend.  The conductor's tempo map does the slowing
(112 -> 96 -> 80 -> 66); this module just writes beats.  Layers leave as
they arrived in M1 — one at a time:

  beat 1592   ch1 sweep pad (prog back to 95) — A-add9 pools moving I-V-IV
              in 4-beat voice-led steps, settling to a bare A-E open fifth
              at 1652 that rings to the end.  CC74 CLOSES 100->25 across
              the movement (the mirror of M1's opening) and CC11 fades to
              20 by 1676.  CC91 back out to 75 on every channel used here.
  beat 1594   ch3 fretless (prog 35 again) — slide tones on 1 and 5 only,
              bend_ramp in from -1.5 semis, recentred after every slide
              (and left recentred at the final boundary).
  beat 1596   ch8 nylon — THEME_A complete and intimate: vel ~50-61 arch,
              gate 0.9, jt=8 rubato; the last note rings 8 beats.
  beat 1604   ch7 steel — fingerpicked 4-note broken chords beneath, one
              chord per 2 bars (E, D, E, A, D, A — simple I/IV/V), quiet
              (vel ~40-50, under the nylon), thinning to a last low
              arpeggio at 1644.
  beat 1628   ch0 piano — three pedalled pool chords (A, D, bare A), very
              quiet, CC64 down/up balanced around each.
  beat 1630   ch14 whistle (prog 78 again) — echoes THEME_A's final phrase
              (its last six notes, augmented x1.5) once the nylon has
              finished; echo throw on its final note.
  beat 1650   ch9 woodblock — Morse "K" at vel <=30: "go ahead" — the M1
              beacon's "CQ CQ CQ" finally answered.
  beat 1664   ch15 — ONE tubular bell on A3, vel 70, rings to the end.
  beat 1667   ch2 crystal (prog back to 98) — three high-A pings with echo
              throws, the last at 1674.5.

Nothing starts after 1676; only the pad fifth, the bell, the last crystal
ping and the nylon/bass tails sustain to 1678 (the engine adds two beats
of end-pad, the renderer a 6 s tail).
"""

from __future__ import annotations

import math

import conductor as cn
import engine as en
import material as mat
from engine import n

ION = "ionian"

T0, T1 = 1592.0, 1678.0
A2, A3, A4 = n("A2"), n("A3"), n("A4")     # 45, 57, 69

MY_CHANNELS = (cn.CH_PIANO, cn.CH_PAD, cn.CH_CRYSTAL, cn.CH_BASS,
               cn.CH_STEEL, cn.CH_NYLON, cn.CH_DRUMS, cn.CH_WINDS,
               cn.CH_BELLS)


def _controllers(sc: en.Score) -> None:
    """CC91 back out to 75 (far again) + CC11 baselines at the seam."""
    for ch in MY_CHANNELS:
        sc.cc(ch, 91, 75, T0)
    for ch, v in ((cn.CH_PIANO, 90), (cn.CH_CRYSTAL, 86), (cn.CH_BASS, 96),
                  (cn.CH_STEEL, 90), (cn.CH_NYLON, 96), (cn.CH_BELLS, 96)):
        sc.cc(ch, 11, v, T0)


# ---------------------------------------------------------------------------
# ch1 — the sweep pad bookend: CC74 closing, CC11 fading, the bare fifth
# ---------------------------------------------------------------------------

def _pad(sc: en.Score) -> None:
    ch = cn.CH_PAD

    def pc(degs) -> list[int]:
        return [en.pitch(A3, ION, d) for d in degs]

    a9 = pc((1, 2, 3, 5))          # A B C# E
    e9 = pc((5, 6, 7, 9))          # E F# G# B
    d9 = pc((4, 5, 6, 8))          # D E F# A
    # One 4-beat step per bar, tied where the harmony holds; the plan
    # follows the steel's I-V-IV timeline under the nylon theme.
    chords = ([a9] * 3 + [e9] * 2 + [d9] * 2 + [e9] * 2
              + [a9] * 2 + [d9] * 2 + [a9] * 2)          # 1592-1652
    en.pad_block(sc, ch, T0, chords, 4.0, size=4, lo=50, hi=76,
                 vel=52, vel_end=46)
    # The bare A-E open fifth, struck 1652, ringing to the very end.
    for p, v in ((A2, 49), (n("E3"), 47), (A3, 45)):
        sc.note(ch, p, 1652.0, 26.0, v, jt=3, jv=2)

    # The filter CLOSING — the mirror of M1's 30->100 opening.
    en.cc_curve(sc, ch, 74, [
        (T0, 100), (1608.0, 88), (1624.0, 74), (1640.0, 58),
        (1656.0, 42), (1668.0, 32), (1676.0, 25),
    ], step=0.5)
    # CC11 fade to ~20 by 1676.
    en.expr_curve(sc, ch, [
        (T0, 86), (1604.0, 82), (1616.0, 76), (1628.0, 68),
        (1640.0, 56), (1652.0, 44), (1664.0, 30), (1676.0, 20),
    ], step=1.0)


# ---------------------------------------------------------------------------
# ch8 — nylon: THEME_A complete, intimate, rubato
# ---------------------------------------------------------------------------

def _nylon(sc: en.Score) -> None:
    ch = cn.CH_NYLON
    t = 1596.0
    last = len(mat.THEME_A) - 1
    for i, (d, s, dur) in enumerate(mat.THEME_A):
        v = int(round(50 + 11 * math.sin(math.pi * s / 31.0)))
        if i == last:
            sc.note(ch, en.pitch(A3, ION, d), t + s, 8.0, 52, jt=8, jv=3)
        else:
            sc.note(ch, en.pitch(A3, ION, d), t + s, dur * 0.9, v,
                    jt=8, jv=3)
    # One long breath: rise into the degree-11 peak (bar 6), ease away.
    en.expr_curve(sc, ch, [
        (1595.5, 88), (1606.0, 96), (1616.0, 102), (1622.0, 94),
        (1630.0, 86),
    ], step=1.0)


# ---------------------------------------------------------------------------
# ch7 — steel: fingerpicked broken chords beneath, one per two bars
# ---------------------------------------------------------------------------

_A_CHORD = (n("A2"), n("E3"), n("A3"), n("C#4"))
_E_CHORD = (n("E2"), n("B2"), n("E3"), n("G#3"))
_D_CHORD = (n("D3"), n("F#3"), n("A3"), n("D4"))

# (chord start, voicing, base velocity) — E D E under the theme's middle,
# A at its resolution, a plagal D, home to A.
_STEEL_PLAN = [
    (1604.0, _E_CHORD, 48), (1612.0, _D_CHORD, 48), (1620.0, _E_CHORD, 47),
    (1628.0, _A_CHORD, 46), (1636.0, _D_CHORD, 44),
]
_PICK_T = (0.0, 0.5, 1.5, 2.5, 4.0, 4.5, 5.5, 6.5)
_PICK_I = (0, 2, 1, 3, 0, 2, 3, 1)


def _steel(sc: en.Score) -> None:
    ch = cn.CH_STEEL
    for t, voicing, base in _STEEL_PLAN:
        for tt, idx in zip(_PICK_T, _PICK_I):
            v = base + (3 if tt in (0.0, 4.0) else 0) - (2 if idx == 3 else 0)
            sc.note(ch, voicing[idx], t + tt, 1.8, v, jt=6, jv=3)
    # Final low A arpeggio, slower and sparser, done before the Morse "K".
    for tt, idx, v in ((0.0, 0, 46), (1.0, 1, 43), (2.0, 2, 41), (3.5, 1, 39)):
        sc.note(ch, _A_CHORD[idx], 1644.0 + tt, 2.6, v, jt=6, jv=3)


# ---------------------------------------------------------------------------
# ch3 — fretless: slide tones on 1 and 5, recentred after every slide
# ---------------------------------------------------------------------------

# (beat, pitch, dur, vel) — roots and fifths only (A and E).
_SLIDES = [
    (1594.0, A2, 9.0, 51),
    (1604.0, n("E2"), 7.0, 51),
    (1612.0, A2, 7.0, 53),          # fifth of the D chord
    (1620.0, n("E3"), 7.0, 55),
    (1628.0, A2, 11.0, 55),
    (1644.0, n("E3"), 6.0, 52),
    (1652.0, A2, 16.0, 49),         # the last word; rings to 1668
]


def _fretless(sc: en.Score) -> None:
    ch = cn.CH_BASS
    for b, p, dur, v in _SLIDES:
        en.bend_ramp(sc, ch, b, b + 0.5, -1.5, 0.0, steps=10)
        sc.note(ch, p, b, dur, v, jt=2, jv=3)
    # bend_ramp ends every slide at exactly 0.0 — the boundary at 1678
    # sees the channel recentred.


# ---------------------------------------------------------------------------
# ch0 — three pedalled pool chords, very quiet
# ---------------------------------------------------------------------------

# (start, ionian degrees from A2, note offsets, vel first -> last, pedal len)
_POOLS = [
    (1628.0, (1, 5, 9, 10, 12, 15), (0.0, 1.25, 2.5, 3.75, 5.0, 6.25),
     44, 54, 7.9),                                         # A add9
    (1638.0, (4, 8, 11, 13, 15), (0.0, 1.5, 3.0, 4.5, 6.0),
     42, 51, 7.5),                                         # D major
    (1658.0, (1, 5, 8, 12, 15), (0.0, 1.75, 3.5, 5.25, 7.0),
     44, 52, 9.5),                                         # bare A pool
]


def _piano(sc: en.Score) -> None:
    ch = cn.CH_PIANO
    for t, degs, times, v0, v1, pedal in _POOLS:
        en.sustain(sc, ch, t, t + pedal)
        span = max(1, len(times) - 1)
        for i, (d, tt) in enumerate(zip(degs, times)):
            v = int(round(en.lerp(v0, v1, i / span)))
            sc.note(ch, en.pitch(A2, ION, d), t + tt, 2.6, v, jt=6, jv=4)


# ---------------------------------------------------------------------------
# ch14 — whistle: THEME_A's final phrase, once the nylon has finished
# ---------------------------------------------------------------------------

# Last six notes of THEME_A, rebased and augmented x1.5 for the ritardando.
_TAIL = [(d, (s - 25.5) * 1.5, dur * 1.5) for d, s, dur in mat.THEME_A[-6:]]
_TAIL_VELS = (52, 54, 56, 58, 50, 54)


def _whistle(sc: en.Score) -> None:
    ch = cn.CH_WINDS
    t = 1630.0
    for (d, s, dur), v in zip(_TAIL, _TAIL_VELS):
        sc.note(ch, en.pitch(A4, ION, d), t + s, dur * 0.92, v, jt=7, jv=3)
        if dur >= 1.5:
            en.vibrato(sc, ch, t + s, dur * 0.92, depth=0.25,
                       cycles_per_beat=1.1, delay=0.6)
    en.expr_curve(sc, ch, [(1629.5, 52), (1633.0, 74), (1637.0, 80),
                           (1639.8, 54)], step=0.5)
    en.echo_throw(sc, ch, t + 6.75, base=25, peak=85, release=2.5)


# ---------------------------------------------------------------------------
# ch9 — the answer: Morse "K" ("go ahead"), quieter than M1's call
# ---------------------------------------------------------------------------

def _beacon(sc: en.Score) -> None:
    en.morse(sc, "K", 1650.0, unit=0.2, drum=76, vel=27)


# ---------------------------------------------------------------------------
# ch15 + ch2 — one bell, three crystal pings, and out
# ---------------------------------------------------------------------------

def _finale(sc: en.Score) -> None:
    sc.note(cn.CH_BELLS, A3, 1664.0, 14.0, 70, jt=2, jv=2)
    ch = cn.CH_CRYSTAL
    sc.cc(ch, 94, 30, T0)
    for b, p, dur, v, peak in ((1667.0, 81, 3.0, 53, 70),
                               (1671.0, 93, 3.0, 51, 78),
                               (1674.5, 81, 3.4, 56, 88)):
        sc.note(ch, p, b, dur, v, jt=4, jv=2)
        en.echo_throw(sc, ch, b, base=30, peak=peak, release=1.4)


def build(sc: en.Score) -> None:
    _controllers(sc)
    _pad(sc)
    _fretless(sc)
    _nylon(sc)
    _steel(sc)
    _piano(sc)
    _whistle(sc)
    _beacon(sc)
    _finale(sc)
