"""VI. Rising Tide (beats 196-292, bars 50-73) — the long rebuild.

HLD: wrk_docs/2026.07.07 - HLD - The Ninth Bell.md, section 3 (§6),
section 4 (tolls #6 and #7), section 6 (seam ledger).  The tempo
staircase (66/70/74/80) lives in the conductor; this module only
writes beats.

Shape:

  bar 50 (196)    toll #6 (pp fall 10->5) over the ground returning
                  pp on the ch0 pads (CC11 restarts at 50)
  bar 54 (212)    THEME on solo cello — warmer than §2 now, vibrato
                  blooming on the two longest notes
  bar 58 (228)    THEME on violin +12, COUNTER in cello, harp 16th
                  arps on the chord voicings
  bar 62 (244)    THE FEINT DROP: everything cut for one bar to a pp
                  ch0 Am sustain + a single mp E4 bell (toll #7);
                  ch0 CC11 notched to 45, then it recovers
  bars 63-73      the full stack: timpani ostinato (1 & 3 + quaver
                  pickup into 1), organ ground chords under a Leslie
                  spin-up (CC1 20->90 across 248-292), choir mm->ah
                  (CC70 15->105 — the mouth opens), piano low tolling
                  octaves on the chord roots (pedal phrase-wise),
                  contrabass lament tetrachord
  bars 67-70      STRETTO on the leap cell: cello at t, violin at
                  t+2, organ top voice at t+4 — two waves (5-10,
                  then 6-11 a step higher)
  bars 70.5-72    string run() 16th sweeps climbing the scale under
                  CC68 legato (CC68 back to 0 after)
  bars 72-73      PHRYGIAN GATE: F major -> E MAJOR (the chromatic
                  G# built from en.n()); CC91 push 60->127 on
                  bells/choir/timpani across bar 73 (the pre-climax
                  bloom); CC74 arrives at 105, ch0 CC11 at 115

Seam state set at 196 (HLD section 6): CC11 on every sustained
channel used here, CC74=40 on strings+organ (then the ramp to 105),
CC1=20 on organ, CC70=15 on choir, CC65=0 (cello portamento off
after §5's sighs).  Every vibrato recentres its bend before 292.
Peak dynamic ~9/10 — headroom left for §7's climax.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_BELLS, CH_CBASS, CH_CELLO, CH_CHOIR, CH_HARP,
                       CH_ORGAN, CH_PIANO, CH_STRINGS, CH_TIMPANI, CH_VIOLIN)

BASE = material.TONIC
MODE = material.MODE

T0 = 196.0                    # bar 50 — the tide begins
T_THEME_CELLO = 212.0         # bar 54
T_THEME_VIOLIN = 228.0        # bar 58
T_FEINT = 244.0               # bar 62 — the feint drop (toll #7)
T_STACK = 248.0               # bar 63 — the full stack enters
T_STRETTO = 264.0             # bar 67
T_RUNS = 278.0                # bar 70.5 — 16th sweeps
T_GATE_F = 284.0              # bar 72 — F major (bVI)
T_GATE_E = 288.0              # bar 73 — E MAJOR (V, the knife)
T1 = 292.0

# The leap cell as playable figures (theme's own rhythm: quarter + held).
_CELL_1 = [(material.LEAP_CELL[0], 0.0, 1.0),
           (material.LEAP_CELL[1], 1.0, 2.0)]          # 5 -> 10
_CELL_2 = [(material.LEAP_CELL[0] + 1, 0.0, 1.0),
           (material.LEAP_CELL[1] + 1, 1.0, 2.0)]      # 6 -> 11

# Harmony of the full stack, bars 63-73: two home-ground passes, then
# Am | F | E — the lament bass A F E with the phrygian F->E gate.
_E_MAJOR_LOW = [en.n("E2"), en.n("G#2"), en.n("B2")]   # chromatic G#


def _stack_chords() -> list[list[int]]:
    ground = [en.triad(BASE, MODE, d) for d in material.GROUND_HOME_DEGS]
    return (ground + ground +
            [en.triad(BASE, MODE, 1),        # bar 71  Am
             en.triad(BASE, MODE, 6),        # bar 72  F  (bVI)
             _E_MAJOR_LOW])                  # bar 73  E MAJOR (V)


# ---------------------------------------------------------------------------
# Seam state (HLD section 6) — set everything we rely on at beat 196.
# ---------------------------------------------------------------------------

def _seam_state(sc: en.Score) -> None:
    en.portamento_off(sc, CH_CELLO, T0)          # §5's sighs are over
    for ch, val in ((CH_CELLO, 72), (CH_CHOIR, 55), (CH_ORGAN, 65),
                    (CH_VIOLIN, 70), (CH_CBASS, 75)):
        sc.cc(ch, 11, val, T0)                   # ch0's own CC11 curve
    sc.cc(CH_ORGAN, 1, 20, T0)                   # slow rotor until 248
    sc.cc(CH_CHOIR, 70, 15, T0)                  # mouth closed ("mm")


# ---------------------------------------------------------------------------
# The two frame tolls this movement owns (HLD section 4).
# ---------------------------------------------------------------------------

def _tolls(sc: en.Score) -> None:
    # Toll #6 at 196: the falling 10->5 (C5 -> E4), pp — §6 opens.
    en.line(sc, CH_BELLS, T0, BASE, MODE, material.TOLL_FALL, vel=38)
    # Toll #7 at 244: THE FEINT — one lone E4, mp, left ringing.
    en.line(sc, CH_BELLS, T_FEINT, BASE, MODE, [(5, 0.0, 4.0)], vel=56)


# ---------------------------------------------------------------------------
# Bars 50-61: the ground returns pp; the theme climbs back out.
# ---------------------------------------------------------------------------

def _rebuild(sc: en.Score) -> None:
    # Three pp->mp passes of the loved pad gesture (bars 50-61).
    chords = material.home_triads()
    en.pad_block(sc, CH_STRINGS, T0, chords * 3, span=4.0, size=4,
                 lo=52, hi=79, vel=46, vel_end=60)

    # Bar 54: THEME on cello, base register — warmer than §2's dead tone:
    # vibrato blooms on the two longest notes only.
    en.line(sc, CH_CELLO, T_THEME_CELLO, BASE, MODE, material.THEME,
            vel=62, vel_end=72)
    en.vibrato(sc, CH_CELLO, T_THEME_CELLO + 4.0, 1.9, depth=0.20, delay=0.5)
    en.vibrato(sc, CH_CELLO, T_THEME_CELLO + 14.0, 1.9, depth=0.22, delay=0.5)

    # Bar 58: THEME on violin +12, COUNTER in cello, harp 16th arps.
    en.line(sc, CH_VIOLIN, T_THEME_VIOLIN, BASE, MODE, material.THEME,
            vel=70, vel_end=80, octave=1)
    en.vibrato(sc, CH_VIOLIN, T_THEME_VIOLIN + 4.0, 1.9, depth=0.22, delay=0.5)
    en.vibrato(sc, CH_VIOLIN, T_THEME_VIOLIN + 14.0, 1.9, depth=0.25, delay=0.5)
    en.line(sc, CH_CELLO, T_THEME_VIOLIN, BASE, MODE, material.COUNTER,
            vel=58, vel_end=66)
    for k, deg in enumerate(material.GROUND_HOME_DEGS):
        tri = en.triad(BASE + 12, MODE, deg)
        en.arp(sc, CH_HARP, tri + [tri[0] + 12], T_THEME_VIOLIN + 4.0 * k,
               count=16, step=0.25, vel=50, pattern="updown",
               gate=1.0 if k == 3 else 1.25,      # bar 61 releases INTO 244
               accent_every=4, accent=8)


# ---------------------------------------------------------------------------
# Bar 62: THE FEINT DROP — one bar of nothing but a pp Am and the bell.
# ---------------------------------------------------------------------------

def _feint(sc: en.Score) -> None:
    en.pad_block(sc, CH_STRINGS, T_FEINT, [en.triad(BASE, MODE, 1)],
                 span=4.0, size=4, lo=52, hi=79, vel=40)


# ---------------------------------------------------------------------------
# Bars 63-73: the full stack.
# ---------------------------------------------------------------------------

def _full_stack(sc: en.Score) -> None:
    chords = _stack_chords()

    # Organ: ground chords under the Leslie spin-up (CC1 20->90).
    en.pad_block(sc, CH_ORGAN, T_STACK, chords, span=4.0, size=4,
                 lo=45, hi=74, vel=58, vel_end=80)
    en.leslie(sc, CH_ORGAN, T_STACK, T1, 20, 90)

    # Choir: the mouth opens — CC70 morphs mm -> ah across the stack.
    en.pad_block(sc, CH_CHOIR, T_STACK, chords, span=4.0, size=3,
                 lo=55, hi=76, vel=52, vel_end=74)
    en.vowel_curve(sc, CH_CHOIR, [(T_STACK, 15), (T1, 105)], step=0.5)

    # Strings: sustained ground bed bars 63-69 (the sweeps take over
    # from bar 70.5; register kept clear of the stretto lines above 74).
    en.pad_block(sc, CH_STRINGS, T_STACK,
                 [en.triad(BASE, MODE, d) for d in (1, 6, 3, 7, 1, 6, 3)],
                 span=4.0, size=4, lo=52, hi=79, vel=62, vel_end=76)

    # Timpani ostinato: beats 1 & 3 + a quaver pickup INTO the next 1.
    # A throughout (root of Am, third of F at the gate); E under bar 73's
    # E major; the last pickup (291.5, on A) leads into §7's Am downbeat.
    a2, e2 = en.n("A2"), en.n("E2")
    for bar in range(11):
        t = T_STACK + 4.0 * bar
        p = e2 if bar == 10 else a2
        v = int(en.lerp(62, 88, bar / 10))
        sc.note(CH_TIMPANI, p, t, 0.6, v)
        sc.note(CH_TIMPANI, p, t + 2.0, 0.6, v - 6)
        nxt = e2 if bar == 9 else a2             # next bar's tuning
        sc.note(CH_TIMPANI, nxt, t + 3.5, 0.4, v - 8)

    # Piano: low tolling octaves on the chord roots, pedal phrase-wise.
    roots = ("A1", "F1", "C2", "G1", "A1", "F1", "C2", "G1",
             "A1", "F1", "E1")
    for bar, root in enumerate(roots):
        t = T_STACK + 4.0 * bar
        v = int(en.lerp(68, 92, bar / 10))
        lo_p = en.n(root)
        for beat in (0.0, 2.0):
            sc.note(CH_PIANO, lo_p, t + beat, 1.8, v)
            sc.note(CH_PIANO, lo_p + 12, t + beat, 1.8, v - 6)
    for a, b in ((248.0, 263.8), (264.0, 279.8),
                 (280.0, 287.8), (288.0, 291.8)):
        en.sustain(sc, CH_PIANO, a, b)

    # Contrabass: the lament tetrachord (A G F E) twice, then its tail
    # A F E — the bass line whose last F->E step IS the phrygian gate.
    tetra = material.TETRACHORD_DEGS
    walk = ([(d, 4.0 * i, 4.0) for i, d in enumerate(tetra)] +
            [(d, 16.0 + 4.0 * i, 4.0) for i, d in enumerate(tetra)] +
            [(1, 32.0, 4.0), (-1, 36.0, 4.0), (-2, 40.0, 4.0)])
    en.line(sc, CH_CBASS, T_STACK, BASE - 12, MODE, walk, vel=64, vel_end=84)

    # Cello: the collapsing staircase weaves through bars 63-66,
    # then hands itself to the stretto.
    en.line(sc, CH_CELLO, T_STACK, BASE, MODE, material.COUNTER,
            vel=66, vel_end=76)

    # Harp: the 16th tide keeps rising until the string sweeps take over.
    for k in range(8):
        deg = material.GROUND_HOME_DEGS[k % 4]
        tri = en.triad(BASE + 12, MODE, deg)
        en.arp(sc, CH_HARP, tri + [tri[0] + 12], T_STACK + 4.0 * k,
               count=16, step=0.25, vel=int(en.lerp(52, 62, k / 7)),
               pattern="updown", accent_every=4, accent=8)


# ---------------------------------------------------------------------------
# Bars 67-70: STRETTO on the leap cell — cello t, violin t+2, organ t+4.
# ---------------------------------------------------------------------------

def _stretto(sc: en.Score) -> None:
    for wave_t, cell in ((T_STRETTO, _CELL_1), (T_STRETTO + 8.0, _CELL_2)):
        en.line(sc, CH_CELLO, wave_t, BASE, MODE, cell, vel=76)
        en.line(sc, CH_VIOLIN, wave_t + 2.0, BASE, MODE, cell,
                vel=80, octave=1)
        en.line(sc, CH_ORGAN, wave_t + 4.0, BASE, MODE, cell,
                vel=78, octave=1)


# ---------------------------------------------------------------------------
# Bars 70.5-73: the sweeps and the PHRYGIAN GATE (F -> E major).
# ---------------------------------------------------------------------------

def _runs_and_gate(sc: en.Score) -> None:
    # String 16th sweeps under CC68 legato, climbing two octaves in five
    # waves; the F-bar sweep runs F->F, the last lands the A that melts
    # down a semitone onto the violin's G#.
    sc.cc(CH_STRINGS, 68, 127, T_RUNS - 0.15)
    sweeps = (
        (278.0, [1, 2, 3, 4, 5, 6, 7, 8], 58, 74),
        (280.0, [3, 4, 5, 6, 7, 8, 9, 10], 62, 80),
        (282.0, [5, 6, 7, 8, 9, 10, 11, 12], 68, 86),
        (284.0, [6, 7, 8, 9, 10, 11, 12, 13], 72, 92),      # over F
        (286.0, [8, 9, 10, 11, 12, 13, 14, 15], 78, 98),    # into the gate
    )
    for t, degs, v0, v1 in sweeps:
        en.run(sc, CH_STRINGS, t, BASE, MODE, degs, 0.25, v0, v1, gate=1.2)
    sc.cc(CH_STRINGS, 68, 0, T_GATE_E + 0.3)                # legato off after

    # Cello underpins the gate with the tetrachord's tail: A3 F3 E3.
    en.line(sc, CH_CELLO, 280.0, BASE, MODE,
            [(1, 0.0, 4.0), (-1, 4.0, 4.0), (-2, 8.0, 4.0)],
            vel=78, vel_end=88)

    # Violin crowns it: A5 over the F chord melting to the chromatic G#
    # (built from note names — the E-major exception).
    sc.note(CH_VIOLIN, en.n("A5"), T_GATE_F, 3.9, 84)
    en.vibrato(sc, CH_VIOLIN, T_GATE_F, 3.6, depth=0.28, delay=0.8)
    sc.note(CH_VIOLIN, en.n("G#5"), T_GATE_E, 3.9, 88)
    en.vibrato(sc, CH_VIOLIN, T_GATE_E, 3.5, depth=0.30, delay=0.7)

    # Bar 73: the strings slam the E-major bed (voiced 52-79) and hold
    # it into §7's downbeat — the knife laid against the ear.
    for p in (en.n("E3"), en.n("B3"), en.n("E4"),
              en.n("G#4"), en.n("B4"), en.n("E5")):
        sc.note(CH_STRINGS, p, T_GATE_E, 4.2, 88, jt=3)


# ---------------------------------------------------------------------------
# The controller arcs across the whole movement.
# ---------------------------------------------------------------------------

def _cc_arcs(sc: en.Score) -> None:
    # ch0 CC11 staircase 50 -> 115 with the bar-62 feint notch to 45.
    en.expr_curve(sc, CH_STRINGS, [
        (196.0, 50), (211.0, 62), (212.0, 66), (227.0, 74), (228.0, 80),
        (243.0, 84), (244.0, 45), (247.0, 46), (248.0, 62), (263.0, 72),
        (264.0, 80), (279.0, 90), (280.0, 96), (287.0, 104), (288.0, 108),
        (292.0, 115)], step=1.0)

    # Phrase-shaped CC11 on the other sustained voices.
    en.expr_curve(sc, CH_CELLO, [
        (212.0, 70), (218.0, 86), (224.0, 80), (227.5, 72),
        (228.0, 70), (240.0, 78), (243.5, 74), (248.0, 76), (262.0, 84),
        (264.0, 86), (278.0, 92), (280.0, 92), (288.0, 98),
        (291.5, 102)], step=1.0)
    en.expr_curve(sc, CH_VIOLIN, [
        (228.0, 74), (234.0, 90), (238.0, 84), (242.0, 88), (243.5, 80),
        (266.0, 84), (275.0, 90), (284.0, 96), (288.0, 100),
        (291.5, 108)], step=1.0)
    en.expr_curve(sc, CH_ORGAN, [
        (248.0, 70), (270.0, 84), (288.0, 96), (291.5, 102)], step=1.0)
    en.expr_curve(sc, CH_CHOIR, [
        (248.0, 58), (270.0, 74), (288.0, 90), (291.5, 96)], step=1.0)
    en.expr_curve(sc, CH_CBASS, [
        (248.0, 75), (288.0, 90), (291.5, 92)], step=1.0)

    # CC74 opens 40 -> 105 across the whole span (strings + organ);
    # the first breakpoint sets the seam's 40 at 196.
    en.cc_curve(sc, CH_STRINGS, 74, [(T0, 40), (T1, 105)], step=2.0)
    en.cc_curve(sc, CH_ORGAN, 74, [(T0, 40), (T1, 105)], step=2.0)

    # CC91 pre-climax bloom: 60 -> 127 on bells/choir/timpani across
    # bar 73, fully up one breath before §7's peal at 292.
    for ch in (CH_BELLS, CH_CHOIR, CH_TIMPANI):
        en.cc_curve(sc, ch, 91, [(T_GATE_E, 60), (291.5, 127)], step=0.5)


# ---------------------------------------------------------------------------

def build(sc: en.Score) -> None:
    _seam_state(sc)
    _tolls(sc)
    _rebuild(sc)
    _feint(sc)
    _full_stack(sc)
    _stretto(sc)
    _runs_and_gate(sc)
    _cc_arcs(sc)
