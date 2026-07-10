"""Black Glass Pursuit — an original chromatic orchestral action cue."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 41  # F2
# Semitone intervals, deliberately asymmetric: tension vocabulary, not a quoted riff.
GLASS = [0, 3, 1, 6, 4, 2, 7, 5, 1, 4, -1, 2]
HARMONY = [0, 1, 4, 3, 6, 2, 5, 1]


def _glass_line(sc: en.Score, ch: int, start: float, beats: float, step: float,
                vel: int, octave: int = 0, reverse: bool = False) -> None:
    cell = list(reversed(GLASS)) if reverse else GLASS
    for i in range(int(beats / step)):
        interval = cell[i % len(cell)] + (12 if (i // len(cell)) % 2 else 0)
        sc.note(ch, ROOT + 12 * octave + interval, start + i * step,
                step * 0.64, vel + (13 if i % 12 == 0 else 0), jt=1, jv=2)


def _string_engine(sc: en.Score, start: float, beats: float, step: float, vel: int) -> None:
    pattern = [0, 4, 1, 5, 2, 6, 3, 7, 5, 2, 4, 1, 6, 3, 5, 0]
    for i in range(int(beats / step)):
        degree = pattern[i % len(pattern)] + (i // 32) % 3
        beat = start + i * step
        sc.note(2, en.pitch(ROOT, "harmonic", degree, 1), beat, step * 0.81,
                vel + (12 if i % 8 == 0 else 0), jt=1, jv=2)
        if i % 2 == 0:
            sc.note(3, en.pitch(ROOT - 12, "minor", degree % 7, 0), beat + step * 0.18,
                    step * 1.45, vel - 13, jt=1, jv=2)


def _brass_stabs(sc: en.Score, start: float, beats: float, stride: float, vel: int) -> None:
    b = start
    i = 0
    while b < start + beats - 0.5:
        degree = HARMONY[i % len(HARMONY)]
        notes = en.chord(ROOT, "harmonic", degree, size=3, octave=0)
        for ch, lift in ((5, 12), (6, 0), (10, 12)):
            for p in notes:
                sc.note(ch, p + lift, b, min(0.48, stride * 0.42), vel - (ch == 6) * 7,
                        jt=1, jv=2)
        b += stride
        i += 1


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "black-glass guitar", 28, 103, 37, 24, 6, 7),
        (1, "cold vibraphone", 11, 91, 82, 50, 11, 18),
        (2, "pursuit violins", 48, 99, 64, 48, 10, 3),
        (3, "motor violas", 41, 91, 64, 53, 8, 2),
        (4, "subway bass", 34, 111, 64, 17, 0, 0),
        (5, "razor trumpets", 56, 108, 72, 43, 5, 2),
        (6, "weight horns", 60, 104, 64, 48, 5, 2),
        (7, "smoke clarinet", 71, 88, 48, 56, 8, 12),
        (8, "storm choir", 52, 76, 64, 74, 17, 7),
        (10, "impact trombones", 57, 109, 64, 40, 4, 1),
        (11, "high pursuit guitar", 30, 96, 96, 26, 6, 8),
        (9, "impact battery", None, 117, 64, 26, 0, 0),
    ])

    c.section(sc, 0, "Cold Open: A Name in the Mirror", 168, (4, 4))
    c.section(sc, 72, "Motorcade Under Black Glass", 176, (7, 8))
    c.section(sc, 144, "The Lift Stops Between Floors", 150, (5, 4))
    c.section(sc, 216, "Rooftop Exchange", 184, (4, 4))
    c.section(sc, 288, "False Passport Fugue", 172, (3, 4))
    c.section(sc, 372, "Runway Without Lights", 192, (7, 8))
    c.section(sc, 432, "Afterimage and Detonation", 138, (4, 4))

    # Cold open — isolated guitar and vibraphone expose the original interval cell.
    _glass_line(sc, 0, 0, 32, 0.5, 79, octave=1)
    for i in range(18):
        b = 4 + i * 4.0
        p = ROOT + 24 + GLASS[(i * 5) % len(GLASS)]
        sc.note(1, p, b + 0.75, 1.1, 61 + (i % 4) * 4, jt=2, jv=2)
        sc.note(4, ROOT - 12 + [0, 3, 1, 6][i % 4], b, 1.65, 73, jt=1, jv=2)
    _string_engine(sc, 32, 40, 0.5, 69)
    _brass_stabs(sc, 48, 24, 4.0, 91)
    c.drum_groove(sc, 24, 12, 4.0, 88, subdivision=0.5, toms=True)

    # Motorcade — clipped guitar and strings use different rotations of the same cell.
    _glass_line(sc, 0, 72, 72, 0.25, 86, octave=1)
    _glass_line(sc, 11, 72.125, 72, 0.5, 75, octave=2, reverse=True)
    _string_engine(sc, 72, 72, 0.25, 79)
    c.bass_pattern(sc, 4, ROOT - 12, "harmonic", HARMONY, 72, 18, 4.0, 93)
    c.drum_groove(sc, 72, 18, 4.0, 103, subdivision=0.25, toms=True)
    _brass_stabs(sc, 84, 60, 3.5, 99)
    en.wah(sc, 0, 88, 48, 38, 106, 0.25)

    # Suspended breach — the orchestral machine thins to irregular chamber pulses.
    c.chord_cycle(sc, 8, ROOT, "minor", [0, 1, 4, 2], 144, 14, 5.0, 31, gate=1.03)
    c.bass_pattern(sc, 4, ROOT - 12, "minor", [0, 1, 4, 2], 144, 14, 5.0, 61,
                   anticipation=False)
    for bar in range(14):
        b = 144 + bar * 5.0
        for k, off in enumerate((0.0, 1.5, 3.0, 4.25)):
            p = ROOT + 24 + GLASS[(bar * 4 + k) % len(GLASS)]
            sc.note(7, p, b + off, 0.72, 54 + bar * 2, jt=2, jv=3)
        sc.note(1, ROOT + 36 + GLASS[(bar + 2) % len(GLASS)], b + 2.25, 1.5, 48 + bar * 2)
        sc.hit(41 + bar % 3 * 2, b, 62 + bar * 2)
    _glass_line(sc, 0, 192, 24, 0.5, 68, octave=1, reverse=True)
    en.cc_curve(sc, 8, 11, [(144, 28), (188, 67), (215, 95)], 0.5)

    # Rooftop — a compact chase in square metre, with brass as punctuation.
    _string_engine(sc, 216, 72, 0.25, 88)
    _glass_line(sc, 0, 216, 72, 0.25, 91, octave=1)
    c.hocket(sc, (1, 7, 11), ROOT + 12, "harmonic", [0, 4, 1, 6, 2, 7, 3, 5],
             216, 72, 0.5, 82)
    c.bass_pattern(sc, 4, ROOT - 12, "harmonic", HARMONY, 216, 18, 4.0, 101)
    c.drum_groove(sc, 216, 18, 4.0, 108, subdivision=0.25, toms=True)
    _brass_stabs(sc, 224, 64, 2.0, 105)

    # Fugue — the cell enters low, middle, then high across an unstable waltz grid.
    for entry, (ch, delay, octave, reverse) in enumerate(((3, 0, 0, False), (0, 6, 1, True),
                                                          (2, 12, 2, False), (11, 18, 2, True))):
        _glass_line(sc, ch, 288 + delay, 66, 0.375, 72 + entry * 6, octave, reverse)
    c.chord_cycle(sc, 8, ROOT, "harmonic", HARMONY, 288, 28, 3.0, 42, gate=1.02)
    c.bass_pattern(sc, 4, ROOT - 12, "harmonic", HARMONY, 288, 28, 3.0, 86)
    c.drum_groove(sc, 288, 28, 3.0, 91, subdivision=0.375, toms=True)
    _brass_stabs(sc, 324, 48, 3.0, 96)

    # Runway — maximum velocity and shortest orchestral subdivision.
    _string_engine(sc, 372, 60, 0.25, 94)
    _glass_line(sc, 0, 372, 60, 0.25, 99, octave=1)
    _glass_line(sc, 11, 372.125, 60, 0.25, 91, octave=2, reverse=True)
    c.bass_pattern(sc, 4, ROOT - 12, "harmonic", HARMONY, 372, 15, 4.0, 108)
    c.drum_groove(sc, 372, 15, 4.0, 114, subdivision=0.25, toms=True)
    _brass_stabs(sc, 372, 60, 1.75, 111)
    for b in range(380, 432, 8):
        sc.hit(55, b, 112)
        sc.hit(49, b + 7.75, 119)

    # Afterimage — half-time glass notes gather into one final, non-triumphal impact.
    c.chord_cycle(sc, 8, ROOT, "minor", [0, 3, 1, 5], 432, 12, 4.0, 40, gate=1.05)
    _glass_line(sc, 0, 432, 40, 0.5, 74, octave=1)
    c.flowing_arp(sc, 1, ROOT + 12, "minor", [0, 3, 1, 5], 432, 12, 4.0, 0.5, 60)
    c.bass_pattern(sc, 4, ROOT - 12, "minor", [0, 3, 1, 5], 432, 12, 4.0, 84,
                   anticipation=False)
    c.drum_groove(sc, 432, 10, 4.0, 82, subdivision=0.5, toms=True)
    _brass_stabs(sc, 464, 12, 4.0, 113)
    for ch in (2, 3, 5, 6, 8, 10):
        c.expression_arc(sc, ch, 432, 480, 44, 118, 31)
    sc.hit(36, 476, 124)
    sc.hit(49, 476, 124)
    sc.hit(55, 476, 122)

    c.feature(sc, "original black-glass chromatic cell", 0, 0, 472, {28}, min_notes=180,
              monophonic=True)
    c.feature(sc, "vibraphone afterimage", 1, 4, 476, {11}, min_notes=40)
    c.feature(sc, "full orchestral pursuit engine", 2, 32, 432, {48}, min_notes=300,
              monophonic=True)
