"""Clockwork Orchard -- counterpoint learns to breathe beyond the machine."""

from __future__ import annotations

import engine as en
from . import common as c


ROOT = 55  # G3
MODE = "dorian"
SUBJECT = [0, 2, 4, 3, 7, 6, 4, 1, 2, 5, 3, 0]
CLOCK = [0, 4, 1, 5, 2, 6, 3, 7]
PROGRESSION = [0, 3, 5, 1, 4, 2, 6, 4]


def _counterpoint(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    start: float,
    beats: float,
    step: float,
    vel: int,
    rotation: int = 0,
) -> None:
    """A singable line whose entries interlock without duplicating a voice."""
    count = int(beats / step)
    for i in range(count):
        degree = SUBJECT[(i + rotation) % len(SUBJECT)]
        phrase = (i + rotation) // len(SUBJECT)
        octave = (phrase % 3 == 1) - (phrase % 5 == 4)
        accent = 8 if i % len(SUBJECT) == 0 else (3 if i % 3 == 0 else 0)
        sc.note(
            ch,
            en.pitch(root, mode, degree, octave),
            start + i * step,
            step * (0.78 if i % 3 else 1.15),
            vel + accent,
            jt=2,
            jv=3,
        )


def _clock_grid(sc: en.Score, start: float, beats: float, energy: int) -> None:
    """Pitched escapements and kit clicks gradually become the orchard's cage."""
    for i in range(int(beats / 0.25)):
        beat = start + i * 0.25
        ch = 1 if i % 3 else 8
        degree = CLOCK[(i * 3 + i // 13) % len(CLOCK)]
        pitch = en.pitch(ROOT + 24, "whole", degree)
        sc.note(ch, pitch, beat, 0.10 if ch == 8 else 0.18, energy + (9 if i % 13 == 0 else 0), jt=1, jv=2)
        if i % 2 == 0:
            sc.hit(76 if i % 4 else 75, beat + 0.03, energy - 15, 0.06)
        if i % 13 in (0, 8):
            sc.hit(37, beat, energy + 3, 0.07)


def _living_cadence(sc: en.Score, start: float) -> None:
    """The strict subject stretches into irregular, breath-led cadences."""
    offsets = [0.0, 1.4, 2.2, 4.7, 6.1, 9.3, 10.1, 13.8, 16.6, 20.4, 24.9, 29.7, 35.0, 40.0]
    degrees = [0, 2, 4, 3, 7, 6, 4, 1, 5, 3, 2, 0, -2, 0]
    durations = [1.1, 0.6, 2.1, 1.0, 2.8, 0.6, 3.1, 2.0, 2.7, 3.8, 3.4, 4.0, 3.5, 3.8]
    for i, (offset, degree, dur) in enumerate(zip(offsets, degrees, durations)):
        sc.note(4, en.pitch(ROOT + 12, MODE, degree), start + offset, dur, 72 - i // 3, jt=4, jv=3)
        if i in (2, 5, 8, 11):
            sc.note(2, en.pitch(ROOT, MODE, degree - 2), start + offset + 0.38, dur * 0.8, 55, jt=3, jv=2)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "orchard continuo", 6, 94, 64, 42, 6, 4),
        (1, "silver escapement", 11, 88, 60, 30, 10, 10),
        (2, "leaf violin", 40, 91, 64, 58, 14, 4),
        (3, "root cello", 42, 96, 64, 50, 8, 2),
        (4, "breathing flute", 73, 94, 68, 62, 16, 12),
        (5, "bark bassoon", 70, 89, 60, 48, 8, 4),
        (6, "copper clock synth", 80, 88, 80, 35, 20, 14),
        (7, "sap strings", 48, 79, 64, 72, 25, 8),
        (8, "wooden teeth", 115, 88, 58, 24, 4, 8),
        (9, "clockwork kit", None, 103, 64, 28, 0, 0),
    ])

    c.section(sc, 0, "Seed Under Glass", meter=(4, 4))
    c.section(sc, 64, "Gears Find the Branch", 116, (7, 8))
    c.section(sc, 128, "Escapement Canopy", 121, (5, 8))
    c.section(sc, 192, "Iron Pollination", 126, (4, 4))
    c.section(sc, 272, "Sap Against Steel", 108, (3, 4))
    c.section(sc, 336, "Branches Bend Time", 98, (6, 8))
    c.section(sc, 388, "The Living Cadenza", 84, (4, 4))
    sc.tempo(404, 76)
    sc.tempo(416, 64)
    sc.tempo(426, 52)

    # A clean four-voice invention: the subject enters from leaf to root.
    _counterpoint(sc, 4, ROOT + 12, MODE, 0, 64, 0.5, 60)
    _counterpoint(sc, 2, ROOT + 7, MODE, 8, 56, 0.5, 57, 3)
    _counterpoint(sc, 5, ROOT - 5, MODE, 16, 48, 1.0, 52, 6)
    _counterpoint(sc, 3, ROOT - 12, MODE, 24, 40, 1.0, 55, 9)
    c.flowing_arp(sc, 0, ROOT - 12, MODE, PROGRESSION, 0, 16, 4.0, 0.5, 48)
    c.chord_cycle(sc, 7, ROOT - 12, MODE, PROGRESSION, 0, 16, 4.0, 35, gate=0.96)

    # The clock first accompanies the invention, then quantises every gap.
    _counterpoint(sc, 4, ROOT + 12, MODE, 64, 64, 0.5, 66)
    _counterpoint(sc, 2, ROOT + 7, MODE, 67.5, 60.5, 0.5, 63, 4)
    _counterpoint(sc, 3, ROOT - 12, MODE, 71, 57, 1.0, 59, 8)
    c.flowing_arp(sc, 0, ROOT - 12, MODE, PROGRESSION, 64, 18, 3.5, 0.5, 56)
    _clock_grid(sc, 88, 40, 53)
    c.bass_pattern(sc, 5, ROOT - 12, MODE, PROGRESSION, 64, 18, 3.5, 60)

    _clock_grid(sc, 128, 64, 64)
    c.hocket(sc, (0, 6, 1), ROOT, MODE, CLOCK, 128, 64, 0.25, 61)
    _counterpoint(sc, 2, ROOT + 7, MODE, 128, 64, 0.5, 68, 2)
    _counterpoint(sc, 5, ROOT - 5, MODE, 130.5, 61.5, 0.5, 63, 7)
    c.bass_pattern(sc, 3, ROOT - 19, MODE, PROGRESSION, 128, 12, 5.0, 68)
    c.chord_cycle(sc, 7, ROOT - 12, MODE, PROGRESSION, 128, 12, 5.0, 42, gate=0.90)

    _clock_grid(sc, 192, 80, 74)
    c.hocket(sc, (0, 1, 6, 8), ROOT, "harmonic", CLOCK, 192, 80, 0.25, 72)
    _counterpoint(sc, 4, ROOT + 12, "harmonic", 192, 80, 0.5, 75)
    _counterpoint(sc, 2, ROOT + 7, "harmonic", 194, 78, 0.5, 71, 4)
    _counterpoint(sc, 5, ROOT - 5, "harmonic", 196, 76, 0.5, 67, 8)
    c.bass_pattern(sc, 3, ROOT - 19, "harmonic", PROGRESSION, 192, 20, 4.0, 78)
    c.drum_groove(sc, 192, 20, 4.0, 78, subdivision=0.5, toms=True)

    # Organic phrases begin displacing the grid; rests return between attacks.
    _counterpoint(sc, 4, ROOT + 12, MODE, 272, 64, 0.75, 72)
    _counterpoint(sc, 2, ROOT + 7, MODE, 275, 61, 0.75, 66, 5)
    _counterpoint(sc, 3, ROOT - 12, MODE, 278, 58, 1.5, 61, 9)
    c.flowing_arp(sc, 0, ROOT - 12, MODE, PROGRESSION, 272, 21, 3.0, 0.75, 55)
    c.chord_cycle(sc, 7, ROOT - 12, MODE, PROGRESSION, 272, 21, 3.0, 41, gate=0.95)
    _clock_grid(sc, 272, 24, 52)

    _counterpoint(sc, 4, ROOT + 12, "lydian", 336, 52, 1.0, 68)
    _counterpoint(sc, 2, ROOT + 7, "lydian", 340, 48, 1.0, 61, 4)
    c.flowing_arp(sc, 0, ROOT - 12, "lydian", [0, 4, 1, 5], 336, 13, 4.0, 1.0, 48)
    c.chord_cycle(sc, 7, ROOT - 12, "lydian", [0, 4, 1, 5], 336, 13, 4.0, 37, gate=1.02)

    _living_cadence(sc, 388)
    c.chord_cycle(sc, 7, ROOT - 12, "lydian", [0, 4, 1, 0], 388, 11, 4.0, 29, gate=1.02)
    for beat, degree in ((388, 0), (397, 4), (407, 1), (418, -3), (428, 0)):
        sc.note(3, en.pitch(ROOT - 12, "lydian", degree), beat, 3.2, 43, jt=3, jv=2)

    for ch, arc in {
        2: (40, 106, 58), 3: (44, 98, 54), 4: (48, 112, 62),
        5: (38, 101, 52), 7: (30, 92, 40), 6: (35, 105, 28),
    }.items():
        c.expression_arc(sc, ch, 0, 430, *arc)
    en.cc_curve(sc, 1, 11, [(0, 22), (128, 70), (224, 118), (296, 52), (388, 18), (430, 4)], 1.0)
    en.cc_curve(sc, 8, 11, [(0, 0), (96, 42), (224, 116), (296, 46), (388, 0), (430, 0)], 1.0)
    c.feature(sc, "seed subject becomes living cadence", 4, 0, 431, {73}, min_notes=80)
