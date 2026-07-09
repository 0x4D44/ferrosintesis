"""VII. Full Toll (beats 292-356) — the climax and the second betrayal.

HLD: wrk_docs/2026.07.07 - HLD - The Ninth Bell.md, section 3 (§7).

Bars 74-85 (292-340): the climax ground Am|Dm|Em|E7 x3.  Theme ff on
violin +12, doubled by ch0 strings in octaves over voice-led tutti
chords; the collapsing staircase runs continuously in cello+contrabass;
organ power chords (rotor held fast, CC1 90); piano hammers the theme
in octaves; choir open "ah" (CC70 105); bells peal on every bar
downbeat — toll #8 (ff fall) at 292, fall figures on each Am ground
start, single chord-root tones between; bass drum on every 1, toms
building, crash on each ground start.  CC91 is pulled DOWN to ~60
tutti (the room shrinks — terror is close and dry), bells stay wet-ish
at 80; CC74 full on strings/organ.

Bars 86-88 (340-352): hypermetric compression — the loop shrinks to
Am|Dm|E7; the leap cell sequences 5-10 (340), 6-11 (344), then JAMS at
5-10 again (348): the promised third step never comes and the violin
holds the b6 scream C6 (degree 17) to the barline under wide fast
vibrato while timpani and toms roll and CC91 blooms back up (the
pre-hit push, so the tail flowers into scored silence #2).

Bar 89 (352, "THE FRACTURE (Bb)"): the theme's bar-4 downbeat D sounds
(violin octaves; it is the third of Bb) and the orchestra slams Bb
MAJOR ff — every duration <= 1.2 beats — then EVERYTHING is cut.  No
note-on after the slam; the B-natural (degree 2) never comes.
"""

from __future__ import annotations

import engine as en
import material as mat
from conductor import (CH_BELLS, CH_CBASS, CH_CELLO, CH_CHOIR, CH_DRUMS,
                       CH_ORGAN, CH_PIANO, CH_STRINGS, CH_TIMPANI, CH_VIOLIN)

T0 = 292.0                     # bar 74
FRACTURE = 352.0               # bar 89: the Bb slam, then the cut
SLAM_DUR = 1.15                # every fracture note-off lands by ~353.2

BASE, MODE = mat.TONIC, mat.MODE

BD, TOM_HI, TOM_LO, CRASH_A, CRASH_B = 36, 41, 43, 49, 57


def _p(deg: int) -> int:
    return en.pitch(BASE, MODE, deg)


# Bar grid: three passes of the climax ground, then the compressed loop.
GROUND_BARS: list[tuple[float, str]] = [
    (T0 + 16.0 * p + 4.0 * b, name)
    for p in range(3) for b, name in enumerate(mat.GROUND_CLIMAX)]
COMP_BARS: list[tuple[float, str]] = [(340.0, "Am"), (344.0, "Dm"),
                                      (348.0, "E7")]
ALL_BARS = GROUND_BARS + COMP_BARS

ROOT_DEG = {"Am": 1, "Dm": 4, "Em": 5, "E7": 5}
TIMP_ROOT = {"Am": _p(1) - 12,          # A2
             "Dm": _p(4) - 12,          # D3
             "Em": _p(5) - 24,          # E2
             "E7": _p(5) - 24}          # E2 (dominant pedal under the jam)


def _organ_chord(name: str) -> list[int]:
    """Power chord on the bar's root; E7 gets its chromatic G# (en.n)."""
    root = _p(ROOT_DEG[name]) - 12                  # A2 / D3 / E3
    if name == "E7":
        return [root, en.n("G#3"), root + 7, root + 10]   # E G# B D
    return [root, root + 7, root + 12]


# ---------------------------------------------------------------------------
# Seam state (HLD section 6): every CC this movement relies on, set at T0.
# ---------------------------------------------------------------------------

def _seam_state(sc: en.Score) -> None:
    # CC91 tutti pulled DOWN to ~60 — the room shrinks; bells stay wet-ish.
    for ch in (CH_STRINGS, CH_CELLO, CH_CHOIR, CH_ORGAN, CH_TIMPANI,
               CH_VIOLIN, CH_DRUMS, CH_PIANO, CH_CBASS):
        sc.cc(ch, 91, 60, T0)
    sc.cc(CH_BELLS, 91, 80, T0)
    # CC74 full on strings/organ; organ rotor held fast; choir open "ah".
    sc.cc(CH_STRINGS, 74, 105, T0)
    sc.cc(CH_ORGAN, 74, 105, T0)
    sc.cc(CH_ORGAN, 1, 90, T0)
    en.vowel(sc, CH_CHOIR, 105, T0)
    en.portamento_off(sc, CH_CELLO, T0)   # no glide left over from the sighs
    # CC11 entry state on every channel this movement uses.
    for ch, val in ((CH_STRINGS, 110), (CH_CELLO, 104), (CH_CHOIR, 100),
                    (CH_ORGAN, 108), (CH_BELLS, 122), (CH_TIMPANI, 118),
                    (CH_VIOLIN, 106), (CH_DRUMS, 118), (CH_PIANO, 120),
                    (CH_CBASS, 102)):
        sc.cc(ch, 11, val, T0)


# ---------------------------------------------------------------------------
# The layers
# ---------------------------------------------------------------------------

def _strings(sc: en.Score) -> None:
    """Tutti voice-led chords across all 15 bars + the theme in octaves."""
    chords = [sorted(mat.CHORD_PCS[name]) for _t, name in ALL_BARS]
    en.pad_block(sc, CH_STRINGS, T0, chords, span=4.0, size=4,
                 lo=52, hi=79, vel=96, vel_end=112)
    for i, t in enumerate((292.0, 308.0, 324.0)):
        en.line(sc, CH_STRINGS, t, BASE, MODE, mat.THEME, 96 + 2 * i,
                vel_end=102 + 2 * i, octave=0, gate=0.95)
        en.line(sc, CH_STRINGS, t, BASE, MODE, mat.THEME, 100 + 2 * i,
                vel_end=106 + 2 * i, octave=1, gate=0.95)


def _violin(sc: en.Score) -> None:
    """Theme ff +12 with vibrato blooms; then the leap-cell sequence that
    jams, and the b6 scream held to the fracture."""
    for i, t in enumerate((292.0, 308.0, 324.0)):
        vel = 104 + 4 * i
        en.line(sc, CH_VIOLIN, t, BASE, MODE, mat.THEME, vel,
                vel_end=vel + 6, octave=1, gate=0.97)
        # vibrato blooms on the long notes (the anguish C, the lament A,
        # the hollow bar-4 fall)
        en.vibrato(sc, CH_VIOLIN, t + 1.0, 1.4, depth=0.30,
                   cycles_per_beat=1.6, delay=0.35)
        en.vibrato(sc, CH_VIOLIN, t + 4.0, 1.9, depth=0.35,
                   cycles_per_beat=1.7, delay=0.5)
        en.vibrato(sc, CH_VIOLIN, t + 12.0, 3.8, depth=0.32,
                   cycles_per_beat=1.5, delay=0.6)
    # Compression: 5-10 (340), 6-11 (344), then JAMMED 5-10 (348).
    en.line(sc, CH_VIOLIN, 340.0, BASE, MODE,
            [(5, 0.0, 1.0), (10, 1.0, 1.5)], 110, octave=1, gate=0.96)
    en.vibrato(sc, CH_VIOLIN, 341.0, 1.4, depth=0.30,
               cycles_per_beat=1.9, delay=0.3)
    en.line(sc, CH_VIOLIN, 344.0, BASE, MODE,
            [(6, 0.0, 1.0), (11, 1.0, 1.5)], 113, octave=1, gate=0.96)
    en.vibrato(sc, CH_VIOLIN, 345.0, 1.4, depth=0.30,
               cycles_per_beat=1.9, delay=0.3)
    # The jam: the cell restarts on 5 but the promised 7-12 never comes —
    # it lands back on the b6 (C6, degree 17) and SCREAMS, wide and fast.
    sc.note(CH_VIOLIN, _p(5) + 12, 348.0, 0.95, 114, jt=3)
    sc.note(CH_VIOLIN, _p(17), 349.0, 2.9, 116, jt=2)
    en.vibrato(sc, CH_VIOLIN, 349.0, 2.85, depth=0.45,
               cycles_per_beat=2.4, delay=0.25, step=0.06)
    sc.bend(CH_VIOLIN, 352.1, 0.0)        # recentred before the movement ends


def _low_strings(sc: en.Score) -> None:
    """The collapsing staircase, continuous, cello + contrabass 8vb."""
    for i, t in enumerate((292.0, 308.0, 324.0)):
        en.line(sc, CH_CELLO, t, BASE, MODE, mat.COUNTER, 92 + 3 * i,
                gate=0.96)
        en.line(sc, CH_CBASS, t, BASE, MODE, mat.COUNTER, 86 + 3 * i,
                octave=-1, gate=0.96)
    # Compression keeps only its first three bars (clean over Am|Dm|E7:
    # downbeats 8, 6, 5 are chord tones of all three).
    en.line(sc, CH_CELLO, 340.0, BASE, MODE, mat.COUNTER[:12], 102,
            gate=0.96)
    en.line(sc, CH_CBASS, 340.0, BASE, MODE, mat.COUNTER[:12], 96,
            octave=-1, gate=0.96)


def _organ(sc: en.Score) -> None:
    for i, (t, name) in enumerate(ALL_BARS):
        vel = 100 + i                                # 100 -> 114 across
        for p in _organ_chord(name):
            sc.note(CH_ORGAN, p, t, 3.9, vel, jt=3)


def _choir(sc: en.Score) -> None:
    chords = [sorted(mat.CHORD_PCS[name]) for _t, name in ALL_BARS]
    en.pad_block(sc, CH_CHOIR, T0, chords, span=4.0, size=3,
                 lo=55, hi=76, vel=84, vel_end=100)


def _piano(sc: en.Score) -> None:
    """Theme hammered in octaves; compression turns to driving root 8ths."""
    for i, t in enumerate((292.0, 308.0, 324.0)):
        en.line(sc, CH_PIANO, t, BASE, MODE, mat.THEME, 100 + 3 * i,
                octave=0, gate=0.9)
        en.line(sc, CH_PIANO, t, BASE, MODE, mat.THEME, 96 + 3 * i,
                octave=-1, gate=0.9)
        en.sustain(sc, CH_PIANO, t + 0.05, t + 15.7)
    for j, (t, name) in enumerate(COMP_BARS):
        lo = _p(ROOT_DEG[name]) - 12                 # A2 / D3 / E3
        for k in range(8):
            v = int(en.lerp(102 + 4 * j, 108 + 4 * j, k / 7))
            sc.note(CH_PIANO, lo, t + 0.5 * k, 0.42, v, jt=3)
            sc.note(CH_PIANO, lo + 12, t + 0.5 * k, 0.42, v - 4, jt=3)
        en.sustain(sc, CH_PIANO, t + 0.05, t + 3.7)


def _bells(sc: en.Score) -> None:
    """Toll #8 (ff) then the climax peal: fall figures on the Am ground
    starts, single chord-root tones on the other downbeats.  All note-ons
    inside the ledger's peal window [292, 352]."""
    for t, vel in ((292.0, 112),        # frame toll #8, ff
                   (308.0, 104), (324.0, 108), (340.0, 112)):
        en.line(sc, CH_BELLS, t, BASE, MODE, mat.TOLL_FALL, vel)
    singles = [(296.0, 11, 92), (300.0, 12, 90), (304.0, 5, 88),
               (312.0, 4, 96), (316.0, 12, 94), (320.0, 5, 92),
               (328.0, 11, 100), (332.0, 5, 98), (336.0, 12, 102),
               (344.0, 11, 106), (348.0, 12, 110)]
    for t, deg, vel in singles:
        sc.note(CH_BELLS, _p(deg), t, 3.5, vel, jt=4)


def _tom_fill(sc: en.Score, t: float, n: int, step: float,
              v0: int, v1: int) -> None:
    for i in range(n):
        drum = TOM_LO if i % 2 == 0 else TOM_HI
        sc.hit(drum, t + i * step, int(en.lerp(v0, v1, i / max(1, n - 1))))


def _percussion(sc: en.Score) -> None:
    # Bass drum on beat 1 of every bar, building.
    for k in range(15):
        sc.hit(BD, T0 + 4.0 * k, 100 + k)
    # Crash on each ground start (and the jam gets the second cymbal).
    for t, vel in ((292.0, 114), (308.0, 110), (324.0, 112), (340.0, 116)):
        sc.hit(CRASH_A, t, vel)
    sc.hit(CRASH_B, 348.0, 110)
    # Toms building: sparse eighths, denser each pass, sixteenths at the end.
    _tom_fill(sc, 306.0, 4, 0.5, 76, 90)
    _tom_fill(sc, 314.0, 4, 0.5, 78, 92)
    _tom_fill(sc, 322.0, 4, 0.5, 82, 96)
    _tom_fill(sc, 330.0, 4, 0.5, 84, 100)
    _tom_fill(sc, 338.0, 8, 0.25, 84, 104)
    _tom_fill(sc, 342.0, 4, 0.5, 92, 102)
    _tom_fill(sc, 346.0, 4, 0.5, 96, 106)
    _tom_fill(sc, 350.0, 8, 0.25, 92, 115)
    # Timpani: root ostinato (1 & 3 + quaver pickup) through bar 87 ...
    for i, (t, name) in enumerate(ALL_BARS[:-1]):
        nxt = ALL_BARS[i + 1][1]
        sc.note(CH_TIMPANI, TIMP_ROOT[name], t, 1.4, 96, jt=3)
        sc.note(CH_TIMPANI, TIMP_ROOT[name], t + 2.0, 1.2, 86, jt=3)
        sc.note(CH_TIMPANI, TIMP_ROOT[nxt], t + 3.5, 0.45, 78, jt=3)
    # ... and bar 88 is one long 16th-note roll on the dominant pedal E,
    # cresc. into the fracture.
    for k in range(16):
        sc.note(CH_TIMPANI, TIMP_ROOT["E7"], 348.0 + 0.25 * k, 0.22,
                int(en.lerp(76, 118, k / 15)), jt=2)


def _expression(sc: en.Score) -> None:
    """CC11 arcs (a swell per ground pass, ratcheting up) and the bar-88
    CC91 bloom so the fracture's tail flowers into scored silence #2."""
    en.expr_curve(sc, CH_STRINGS, [(292.0, 110), (300.0, 118), (307.5, 108),
                                   (308.0, 112), (316.0, 122), (323.5, 112),
                                   (324.0, 116), (332.0, 125), (339.5, 116),
                                   (340.0, 118), (348.0, 122), (351.8, 127)])
    en.expr_curve(sc, CH_CHOIR, [(292.0, 100), (306.0, 112), (307.8, 104),
                                 (308.0, 106), (322.0, 118), (323.8, 108),
                                 (324.0, 112), (338.0, 122), (340.0, 116),
                                 (351.8, 127)])
    en.expr_curve(sc, CH_ORGAN, [(292.0, 108), (324.0, 116), (351.8, 124)])
    en.expr_curve(sc, CH_CELLO, [(292.0, 104), (324.0, 112), (351.8, 120)])
    en.expr_curve(sc, CH_CBASS, [(292.0, 102), (340.0, 110), (351.8, 116)])
    en.expr_curve(sc, CH_VIOLIN, [(292.0, 106), (294.0, 118), (301.0, 112),
                                  (306.0, 120), (308.0, 110), (312.0, 121),
                                  (320.0, 115), (324.0, 114), (330.0, 124),
                                  (338.0, 118), (340.0, 117), (342.5, 124),
                                  (344.0, 119), (346.5, 126), (348.0, 118),
                                  (349.5, 124), (351.8, 127)])
    for ch, v0, v1 in ((CH_STRINGS, 60, 127), (CH_CELLO, 60, 118),
                       (CH_CHOIR, 60, 127), (CH_ORGAN, 60, 120),
                       (CH_TIMPANI, 60, 127), (CH_VIOLIN, 60, 122),
                       (CH_PIANO, 60, 118), (CH_CBASS, 60, 115),
                       (CH_BELLS, 80, 127), (CH_DRUMS, 60, 110)):
        en.cc_curve(sc, ch, 91, [(348.0, v0), (351.9, v1)], step=0.5)


def _fracture(sc: en.Score) -> None:
    """Bar 89: the downbeat D sounds — and the orchestra slams Bb MAJOR
    (chromatic, via en.n), one short ff blow, then everything is cut.
    The B-natural never comes."""
    t, d = FRACTURE, SLAM_DUR
    for p in ("Bb3", "D4", "F4", "Bb4", "D5", "F5"):
        sc.note(CH_STRINGS, en.n(p), t, d, 120, jt=2)
    # the theme's bar-4 downbeat D, in octaves (legal: the third of Bb)
    sc.note(CH_VIOLIN, _p(4) + 12, t, d, 121, jt=2)
    sc.note(CH_VIOLIN, _p(4) + 24, t, d, 118, jt=2)
    for p in ("Bb2", "F3"):
        sc.note(CH_CELLO, en.n(p), t, d, 118, jt=2)
    for p in ("Bb2", "F3"):
        sc.note(CH_CBASS, en.n(p), t, d, 118, jt=2)
    for p in ("Bb2", "F3", "Bb3"):
        sc.note(CH_ORGAN, en.n(p), t, d, 117, jt=2)
    for p in ("Bb3", "D4", "F4", "Bb4"):
        sc.note(CH_CHOIR, en.n(p), t, 1.1, 114, jt=2)
    for p in ("Bb1", "Bb2", "Bb3"):
        sc.note(CH_PIANO, en.n(p), t, d, 120, jt=2)
    en.sustain(sc, CH_PIANO, t - 0.05, t + 1.25)
    sc.note(CH_TIMPANI, en.n("Bb2"), t, 1.0, 119, jt=2)
    sc.note(CH_BELLS, en.n("Bb4"), t, d, 118, jt=2)   # inside the peal window
    sc.hit(BD, t, 122)
    sc.hit(CRASH_A, t, 122)
    sc.hit(CRASH_B, t, 118)


# ---------------------------------------------------------------------------

def build(sc: en.Score) -> None:
    _seam_state(sc)
    _strings(sc)
    _violin(sc)
    _low_strings(sc)
    _organ(sc)
    _choir(sc)
    _piano(sc)
    _bells(sc)
    _percussion(sc)
    _expression(sc)
    _fracture(sc)
