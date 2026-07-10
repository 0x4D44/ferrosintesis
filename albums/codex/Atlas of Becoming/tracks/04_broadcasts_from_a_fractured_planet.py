"""Broadcasts from a Fractured Planet — pulses contend, mourn, and align."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 46  # Bb2
MODE = "dorian"
COMMON_SIGNAL = [
    (0, 0.0, 0.45), (3, 0.75, 0.45), (2, 1.5, 0.7),
    (5, 2.5, 0.45), (4, 3.0, 0.8),
]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "public-room piano", 3, 94, 64, 48, 8, 8),
        (1, "shortwave marimba", 12, 88, 34, 42, 7, 21),
        (2, "common strings", 48, 88, 64, 72, 20, 5),
        (3, "earth bass", 43, 101, 64, 30, 2, 0),
        (4, "warning trumpet", 56, 97, 48, 50, 6, 9),
        (5, "witness oboe", 68, 93, 76, 62, 10, 16),
        (6, "gathering choir", 52, 82, 64, 80, 26, 10),
        (7, "border clarinet", 71, 90, 88, 56, 9, 16),
        (8, "distant flute", 73, 87, 40, 65, 12, 23),
        (10, "assembly horn", 60, 96, 64, 57, 7, 5),
        (9, "fractured clocks", None, 106, 64, 38, 0, 0),
    ])

    c.section(sc, 0, "Many Clocks at Dawn", meter=(3, 4))
    c.section(sc, 48, "Crossed Frequencies", 104, (4, 4))
    c.section(sc, 112, "Seven Unequal Windows", 96, (7, 8))
    c.section(sc, 182, "Names Without Headlines", 72, (5, 4))
    c.section(sc, 242, "Hands Find the Same Pulse", 108, (4, 4))
    c.section(sc, 322, "Common Ground, Moving", 116, (6, 8))
    c.section(sc, 370, "A Signal Still Fragile", 84, (3, 4))

    progression = [0, 5, 2, 6, 3, 1, 4, 0]

    # Three pulses share the room but do not yet share an accent grid.
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 0, 16, 3.0, 38, gate=0.98)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 0, 16, 3.0, 58,
                   anticipation=False)
    c.sequence_motif(sc, 5, ROOT + 24, MODE, COMMON_SIGNAL, 3, 6, 7.5,
                     48, 68, (0, 3, 1, 4))
    c.hocket(sc, (1, 7, 8), ROOT + 24, MODE,
             [0, 3, 2, 5, 4, 1, 6, 2, 7], 0, 48, 0.75, 56)
    for bar in range(16):
        b = bar * 3.0
        sc.hit(37, b, 54 + (bar % 4) * 3)
        sc.hit(42, b + 1.0, 44)
        sc.hit(42, b + 2.25, 50)

    # Dense competing broadcasts: one part groups four, another groups three.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 48, 16, 4.0, 0.5, 64)
    c.hocket(sc, (1, 7, 8), ROOT + 24, "phrygian",
             [0, 1, 4, 2, 6, 3, 7, 5, 2, 8, 4, 1], 48, 64, 0.25, 70)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 48, 16, 4.0, 47, gate=0.94)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 48, 16, 4.0, 73)
    c.drum_groove(sc, 48, 16, 4.0, 79, subdivision=0.5, toms=True)
    c.sequence_motif(sc, 4, ROOT + 12, "phrygian", COMMON_SIGNAL, 52, 8, 8,
                     68, 89, (0, 1, -1, 3))
    c.sequence_motif(sc, 5, ROOT + 24, MODE, COMMON_SIGNAL, 56, 7, 8,
                     62, 85, (0, 3, 4, 2))

    # The seven-beat panel keeps interrupting itself; the common signal persists.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 112, 20, 3.5, 0.5, 68)
    c.hocket(sc, (1, 7, 8), ROOT + 24, "chromatic",
             [0, 3, 7, 2, 8, 5, 1, 9, 4, 6], 112, 70, 0.25, 75)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 112, 20, 3.5, 50, gate=0.92)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 112, 20, 3.5, 78)
    c.drum_groove(sc, 112, 20, 3.5, 84, subdivision=0.5, toms=True)
    c.sequence_motif(sc, 4, ROOT + 12, "phrygian", COMMON_SIGNAL, 119, 8, 8.5,
                     74, 98, (0, 1, 4, -1))
    c.sequence_motif(sc, 5, ROOT + 24, MODE, COMMON_SIGNAL, 116, 8, 8.5,
                     67, 92, (0, 2, 5, 3))
    c.brass_hits(sc, (10,), ROOT, MODE, progression, 140, 10, 3.5, 82)

    # Grief is deliberately spacious: no drum groove, only a distant pulse.
    c.chord_cycle(sc, 2, ROOT, "minor", [0, 3, 5, 1], 182, 12, 5.0, 32,
                  gate=1.01)
    c.chord_cycle(sc, 6, ROOT + 12, "minor", [0, 3, 5, 1], 182, 12, 5.0, 31,
                  gate=1.02)
    c.bass_pattern(sc, 3, ROOT - 12, "minor", [0, 3, 5, 1], 182, 12, 5.0,
                   52, anticipation=False)
    c.sequence_motif(sc, 5, ROOT + 24, "minor", COMMON_SIGNAL, 187, 6, 10,
                     43, 61, (0, -2, 0, 3))
    c.sequence_motif(sc, 8, ROOT + 24, "minor", COMMON_SIGNAL, 192, 5, 10,
                     37, 52, (-3, 0, 1, -1))
    for i in range(12):
        sc.hit(36, 182 + i * 5.0, 43 + (i % 3) * 2)
        if i in (3, 7, 11):
            sc.hit(49, 182 + i * 5.0 + 4.5, 52)

    # A common beat is discovered by accumulation, not imposed at once.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 242, 20, 4.0, 0.5, 70)
    c.hocket(sc, (1, 7, 8), ROOT + 24, MODE,
             [0, 3, 2, 5, 4, 7, 6, 4], 242, 80, 0.5, 72)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 242, 20, 4.0, 54, gate=0.98)
    c.chord_cycle(sc, 6, ROOT + 12, MODE, progression, 258, 16, 4.0, 47,
                  gate=0.99)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 242, 20, 4.0, 83)
    c.drum_groove(sc, 242, 20, 4.0, 87, subdivision=0.5, toms=True)
    c.sequence_motif(sc, 5, ROOT + 24, MODE, COMMON_SIGNAL, 246, 10, 8,
                     68, 96, (0, 3, 5, 2))
    c.brass_hits(sc, (4, 10), ROOT, MODE, progression, 274, 12, 4.0, 87)

    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 322, 16, 3.0, 0.5, 78)
    c.hocket(sc, (1, 7, 8), ROOT + 24, MODE,
             [0, 2, 3, 5, 7, 6], 322, 48, 0.25, 82)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 322, 16, 3.0, 61, gate=0.98)
    c.chord_cycle(sc, 6, ROOT + 12, MODE, progression, 322, 16, 3.0, 55,
                  gate=0.99)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 322, 16, 3.0, 91)
    c.drum_groove(sc, 322, 16, 3.0, 94, subdivision=0.25, toms=True)
    c.sequence_motif(sc, 5, ROOT + 24, MODE, COMMON_SIGNAL, 325, 8, 6,
                     80, 105, (0, 4, 2, 6))
    c.brass_hits(sc, (4, 10), ROOT, MODE, progression, 334, 12, 3.0, 96)

    # The final alignment is quiet enough to remain vulnerable.
    c.chord_cycle(sc, 2, ROOT, "major", [0, 4, 5, 3], 370, 10, 3.0, 38,
                  gate=1.01)
    c.chord_cycle(sc, 6, ROOT + 12, "major", [0, 4, 5, 3], 370, 10, 3.0,
                  34, gate=1.02)
    c.bass_pattern(sc, 3, ROOT - 12, "major", [0, 4, 5, 3], 370, 10, 3.0,
                   58, anticipation=False)
    c.sequence_motif(sc, 5, ROOT + 24, "major", COMMON_SIGNAL, 370, 4, 7.5,
                     54, 68, (0, 2, 0, -1))
    for i in range(10):
        sc.hit(37, 370 + i * 3.0, 45 + i)

    for ch in (2, 5, 6, 10):
        c.expression_arc(sc, ch, 242, 399, 42, 111, 59)
    en.cc_curve(sc, 5, 1, [(0, 4), (112, 42), (182, 18), (322, 84), (400, 25)], 1.0)
    c.feature(sc, "five-note common signal", 5, 3, 400, {68}, min_notes=35)

