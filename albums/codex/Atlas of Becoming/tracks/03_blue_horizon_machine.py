"""Blue Horizon Machine — an original aquatic pageant and precision finale."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 48  # C3
MODE = "lydian"
HORIZON = [
    (0, 0.0, 0.45), (2, 0.5, 0.45), (5, 1.0, 0.9),
    (4, 2.0, 0.45), (7, 2.5, 0.45), (9, 3.0, 0.9),
]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "pearl piano", 0, 96, 64, 48, 12, 8),
        (1, "spray marimba", 12, 91, 31, 42, 10, 18),
        (2, "open-water strings", 48, 92, 64, 70, 22, 6),
        (3, "deep-current bass", 43, 104, 64, 30, 3, 0),
        (4, "horizon flute", 73, 96, 76, 62, 15, 18),
        (5, "sunlit choir", 52, 83, 64, 78, 27, 12),
        (6, "pageant trumpets", 56, 101, 55, 50, 7, 5),
        (7, "brass horizon", 60, 98, 64, 56, 10, 5),
        (8, "glass celesta", 8, 88, 93, 50, 16, 24),
        (10, "silver piccolo", 72, 84, 43, 58, 12, 20),
        (9, "oceanic percussion", None, 110, 64, 42, 0, 0),
    ])

    c.section(sc, 0, "Prism Wake", meter=(7, 8))
    c.section(sc, 56, "The Water Learns to Dance", 128, (4, 4))
    c.section(sc, 120, "Procession of Bright Creatures", 132, (12, 8))
    c.section(sc, 192, "Blue Held Breath", 94, (5, 4))
    c.section(sc, 232, "Horizon Engine", 136, (4, 4))
    c.section(sc, 336, "Seven-Fold Spray", 144, (7, 8))
    c.section(sc, 392, "Sun on Every Wave", 112, (4, 4))

    progression = [0, 4, 1, 5, 2, 6, 3, 4]

    # Faceted light on a nearly empty surface: glass speaks before the pageant.
    c.flowing_arp(sc, 8, ROOT + 24, MODE, progression, 0, 16, 3.5, 0.5, 49)
    c.sequence_motif(sc, 4, ROOT + 24, MODE, HORIZON, 3.5, 7, 7.0,
                     54, 72, (0, 2, 4, 1), octave=0)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 0, 16, 3.5, 39,
                  gate=0.98)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 28, 8, 3.5, 57,
                   anticipation=False)
    for bar in range(8):
        sc.hit(81, bar * 7.0, 50 + bar * 3)
        sc.hit(53, bar * 7.0 + 3.0, 46 + bar * 3)

    # Exact four-square machinery arrives, with transient hockets above it.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 56, 16, 4.0, 0.25, 65)
    c.hocket(sc, (1, 8, 10), ROOT + 24, MODE,
             [0, 2, 5, 4, 7, 9, 11, 7], 56, 64, 0.25, 69)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 56, 16, 4.0, 49, gate=0.96)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 56, 16, 4.0, 74)
    c.drum_groove(sc, 56, 16, 4.0, 82, subdivision=0.25, toms=True)
    c.sequence_motif(sc, 4, ROOT + 24, MODE, HORIZON, 60, 8, 8.0,
                     66, 88, (0, 4, 2, 5))
    c.brass_hits(sc, (6, 7), ROOT, MODE, progression, 88, 8, 4.0, 80)

    # A broad 12/8 parade: choir and strings provide the centred scenic bed.
    c.chord_cycle(sc, 5, ROOT + 12, MODE, progression, 120, 12, 6.0, 50,
                  gate=0.99)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 120, 12, 6.0, 57, gate=0.97)
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 120, 12, 6.0, 0.5, 72)
    c.hocket(sc, (1, 8, 10), ROOT + 24, MODE,
             [0, 4, 2, 6, 5, 9, 7, 11, 9, 5, 4, 2],
             120, 72, 0.5, 76)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 120, 12, 6.0, 80)
    c.drum_groove(sc, 120, 12, 6.0, 88, subdivision=0.5, toms=True)
    c.sequence_motif(sc, 4, ROOT + 24, MODE, HORIZON, 126, 8, 9.0,
                     75, 96, (0, 2, 5, 7))
    c.brass_hits(sc, (6, 7), ROOT, MODE, progression, 144, 8, 6.0, 88)

    # The machinery vanishes. Five-beat breaths leave isolated droplets.
    c.chord_cycle(sc, 5, ROOT + 12, "major", [0, 5, 3, 4], 192, 8, 5.0,
                  33, gate=1.02)
    c.chord_cycle(sc, 2, ROOT, "major", [0, 5, 3, 4], 192, 8, 5.0,
                  31, gate=1.01)
    c.sequence_motif(sc, 4, ROOT + 24, "major", HORIZON, 197, 4, 10.0,
                     42, 58, (0, -1, 2, 0))
    for i in range(10):
        p = en.pitch(ROOT + 24, "major", [0, 4, 2, 5, 1][i % 5])
        sc.note(8, p, 193 + i * 3.75, 0.7, 38 + i * 2, jt=1, jv=2)

    # The horizon engine assembles every earlier layer into a rising pageant.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 232, 26, 4.0, 0.25, 78)
    c.hocket(sc, (1, 8, 10), ROOT + 24, MODE,
             [0, 2, 5, 9, 7, 4, 11, 9], 232, 104, 0.25, 82)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 232, 26, 4.0, 61, gate=0.98)
    c.chord_cycle(sc, 5, ROOT + 12, MODE, progression, 248, 22, 4.0, 54,
                  gate=0.99)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 232, 26, 4.0, 90)
    c.drum_groove(sc, 232, 26, 4.0, 98, subdivision=0.25, toms=True)
    c.sequence_motif(sc, 4, ROOT + 24, MODE, HORIZON, 236, 13, 8.0,
                     82, 108, (0, 4, 5, 7))
    c.brass_hits(sc, (6, 7), ROOT, MODE, progression, 248, 22, 4.0, 96)

    # Seven-beat wavelets keep the finale buoyant rather than square.
    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 336, 16, 3.5, 0.25, 88)
    c.hocket(sc, (1, 8, 10), ROOT + 24, MODE,
             [0, 5, 2, 7, 4, 9, 11], 336, 56, 0.25, 91)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 336, 16, 3.5, 68, gate=0.96)
    c.chord_cycle(sc, 5, ROOT + 12, MODE, progression, 336, 16, 3.5, 60,
                  gate=0.98)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 336, 16, 3.5, 96)
    c.drum_groove(sc, 336, 16, 3.5, 104, subdivision=0.25, toms=True)
    c.brass_hits(sc, (6, 7), ROOT, MODE, progression, 350, 12, 3.5, 106)
    c.sequence_motif(sc, 4, ROOT + 24, MODE, HORIZON, 340, 7, 7.0,
                     91, 116, (0, 5, 7, 9))

    c.chord_cycle(sc, 2, ROOT, "major", [0, 4, 5, 0], 392, 6, 4.0, 66,
                  gate=1.02)
    c.chord_cycle(sc, 5, ROOT + 12, "major", [0, 4, 5, 0], 392, 6, 4.0,
                  61, gate=1.02)
    c.flowing_arp(sc, 8, ROOT + 24, "major", [0, 4, 5, 0], 392, 6, 4.0,
                  0.5, 73)
    c.bass_pattern(sc, 3, ROOT - 12, "major", [0, 4, 5, 0], 392, 6, 4.0,
                   88, anticipation=False)
    c.sequence_motif(sc, 4, ROOT + 24, "major", HORIZON, 392, 3, 8.0,
                     88, 104, (0, 4, 0))
    c.brass_hits(sc, (6, 7), ROOT, "major", [0, 4, 5, 0], 400, 4, 4.0, 100)
    for beat, key, vel in ((408, 49, 116), (412, 57, 112), (415.5, 49, 122)):
        sc.hit(key, beat, vel)

    for ch in (2, 4, 5, 6, 7):
        c.expression_arc(sc, ch, 232, 415, 50, 120, 72)
    en.cc_curve(sc, 4, 1, [(0, 4), (120, 38), (232, 72), (391, 112), (416, 30)], 1.0)
    c.feature(sc, "blue-horizon six-note call", 4, 3.5, 416, {73}, min_notes=40)

