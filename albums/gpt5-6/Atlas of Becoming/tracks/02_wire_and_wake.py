"""Wire and Wake — an original high-wire propulsion piece."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 45  # A2
MODE = "phrygian"
CELL = [(0, 0, 0.35), (1, 0.5, 0.35), (4, 1.0, 0.7), (3, 2.0, 0.35), (7, 2.5, 0.9)]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "struck piano", 1, 101, 64, 30, 8, 4),
        (1, "wire guitar", 28, 96, 34, 34, 9, 10),
        (2, "wake guitar", 30, 92, 94, 38, 12, 14),
        (3, "running bass", 34, 108, 64, 18, 0, 0),
        (4, "knife strings", 44, 94, 64, 54, 16, 5),
        (5, "brass rail", 61, 101, 64, 44, 8, 4),
        (6, "reed flare", 65, 91, 70, 52, 12, 18),
        (7, "air synth", 81, 90, 58, 54, 28, 22),
        (9, "kinetic kit", None, 112, 64, 28, 0, 0),
    ])
    c.section(sc, 0, "The Cable Takes Weight", meter=(5, 4))
    c.section(sc, 100, "Wake Engine", 144, (4, 4))
    c.section(sc, 220, "Eleven-Step Crossing", 150, (11, 8))
    c.section(sc, 330, "Release the Line", 158, (4, 4))
    c.section(sc, 402, "White Water Coda", 116, (4, 4))
    progression = [0, 1, 5, 3, 0, 6, 1, 4]

    c.hocket(sc, (0, 1, 2), ROOT + 12, MODE, [0, 1, 4, 3, 7, 4, 1, 6], 0, 100, 0.5, 64)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 0, 20, 5.0, 72)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 0, 20, 5.0, 44, gate=0.92)
    c.drum_groove(sc, 20, 16, 5.0, 74, subdivision=0.5, toms=True)
    c.sequence_motif(sc, 6, ROOT + 24, MODE, CELL, 15, 8, 10, 55, 78, (0, 4, 1, 6))

    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 100, 30, 4.0, 0.25, 72)
    c.hocket(sc, (1, 2), ROOT + 12, MODE, [0, 4, 1, 7, 3, 8, 4, 10], 100, 120, 0.25, 76)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 100, 30, 4.0, 84)
    c.drum_groove(sc, 100, 30, 4.0, 91, subdivision=0.25, toms=True)
    c.brass_hits(sc, (5,), ROOT, MODE, progression, 132, 22, 4.0, 88)
    c.sequence_motif(sc, 6, ROOT + 24, MODE, CELL, 116, 12, 8, 70, 98, (0, 1, 4, 7))
    en.wah(sc, 2, 132, 80, 36, 110, 0.5)

    c.hocket(sc, (0, 1, 2, 6), ROOT + 12, "locrian", [0, 1, 3, 6, 4, 8, 7, 2, 10, 4, 1], 220, 110, 0.25, 83)
    c.bass_pattern(sc, 3, ROOT - 12, "locrian", [0, 3, 1, 5], 220, 20, 5.5, 88)
    c.drum_groove(sc, 220, 20, 5.5, 94, subdivision=0.5, toms=True)
    c.chord_cycle(sc, 4, ROOT, "locrian", [0, 3, 1, 5], 220, 20, 5.5, 56, gate=0.9)
    c.sequence_motif(sc, 7, ROOT + 24, "locrian", CELL, 242, 8, 11, 66, 92, (0, 3, 6, 1))

    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 330, 18, 4.0, 0.25, 88)
    c.hocket(sc, (1, 2, 6), ROOT + 12, MODE, [0, 1, 4, 7, 8, 7, 4, 3], 330, 72, 0.25, 94)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 330, 18, 4.0, 96)
    c.drum_groove(sc, 330, 18, 4.0, 103, subdivision=0.25, toms=True)
    c.brass_hits(sc, (5,), ROOT, MODE, progression, 346, 14, 4.0, 103)
    c.sequence_motif(sc, 6, ROOT + 24, MODE, CELL, 338, 8, 8, 91, 116, (0, 4, 7, 8))
    en.cc_curve(sc, 4, 11, [(330, 66), (382, 122), (401, 74)], 0.5)

    c.chord_cycle(sc, 4, ROOT, "dorian", [0, 5, 3, 0], 402, 9, 4.0, 42, gate=1.04)
    c.sequence_motif(sc, 6, ROOT + 24, "dorian", CELL, 402, 4, 8, 54, 68, (0, 4, 0, -2))
    c.flowing_arp(sc, 7, ROOT + 12, "dorian", [0, 5, 3, 0], 402, 9, 4.0, 0.5, 50)
    c.feature(sc, "cable five-note cell", 6, 15, 434, {65}, min_notes=25)

