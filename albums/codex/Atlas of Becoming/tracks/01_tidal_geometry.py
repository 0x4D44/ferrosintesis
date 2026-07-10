"""Tidal Geometry — an original aquatic/acrobatic show-opener."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 50  # D3
MODE = "dorian"
PROG = [0, 12, 48, 33, 73, 89, 60]
MOTIF = [(0, 0.0, 0.45), (2, 0.5, 0.45), (5, 1.0, 0.9), (4, 2.0, 0.4), (7, 2.5, 0.8)]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "water piano", 0, 96, 64, 54, 18, 12),
        (1, "glass marimba", 12, 88, 28, 42, 12, 22),
        (2, "tidal strings", 48, 88, 64, 70, 24, 8),
        (3, "current bass", 33, 103, 64, 25, 4, 0),
        (4, "aerial flute", 73, 94, 72, 62, 18, 24),
        (5, "blue pad", 89, 72, 64, 82, 38, 30),
        (6, "horizon horns", 60, 96, 64, 58, 10, 8),
        (9, "water percussion", None, 105, 64, 36, 0, 0),
    ])
    c.section(sc, 0, "Glass Surface", meter=(7, 8))
    c.section(sc, 84, "Underwater Wheel", 118, (7, 8))
    c.section(sc, 168, "Aerial Thread", 126, (4, 4))
    c.section(sc, 264, "Weightless Drop", 86, (4, 4))
    c.section(sc, 304, "Final Arc", 132, (7, 8))
    sc.tempo(352, 140)

    progression = [0, 5, 3, 6, 0, 4, 5, 3]
    c.chord_cycle(sc, 5, ROOT, MODE, progression, 0, 24, 3.5, 42, octave=0, gate=0.97)
    c.flowing_arp(sc, 1, ROOT + 12, MODE, progression, 0, 24, 3.5, 0.5, 48)
    c.sequence_motif(sc, 4, ROOT + 12, MODE, MOTIF, 7, 8, 10.5, 54, 72, (0, 2, 5, 3))
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 42, 12, 3.5, 62, anticipation=False)

    c.flowing_arp(sc, 0, ROOT, MODE, progression, 84, 21, 4.0, 0.25, 62)
    c.hocket(sc, (1, 4), ROOT + 12, MODE, [0, 2, 5, 7, 9, 7, 5, 4], 84, 84, 0.5, 66)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 84, 21, 4.0, 72)
    c.drum_groove(sc, 84, 21, 4.0, 73, subdivision=0.5, toms=True)
    c.expression_arc(sc, 2, 84, 168, 38, 88, 60)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 84, 21, 4.0, 47, gate=1.04)

    c.flowing_arp(sc, 0, ROOT + 12, MODE, progression, 168, 24, 4.0, 0.25, 70)
    c.sequence_motif(sc, 4, ROOT + 12, MODE, MOTIF, 168, 12, 8.0, 72, 94, (0, 5, 3, 7))
    c.sequence_motif(sc, 6, ROOT, MODE, MOTIF, 184, 10, 8.0, 64, 88, (0, 3, 5, 4))
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 168, 24, 4.0, 80)
    c.drum_groove(sc, 168, 24, 4.0, 84, subdivision=0.5, toms=True)
    en.autopan(sc, 1, 168, 80, 38, 90, 14)
    en.cc_curve(sc, 4, 1, [(168, 8), (220, 74), (263, 116)], 1.0)

    c.chord_cycle(sc, 5, ROOT, "minor", [0, 3, 5, 4], 264, 10, 4.0, 34, gate=1.05)
    c.sequence_motif(sc, 4, ROOT + 12, "minor", MOTIF, 268, 4, 8.0, 48, 61, (0, -2, 0, 3))
    c.flowing_arp(sc, 1, ROOT + 12, "minor", [0, 3, 5, 4], 280, 6, 4.0, 1.0, 42)
    c.expression_arc(sc, 5, 264, 304, 28, 74, 52)

    c.hocket(sc, (0, 1, 4), ROOT + 12, MODE, [0, 2, 5, 4, 7, 9, 12, 9], 304, 88, 0.25, 80)
    c.chord_cycle(sc, 2, ROOT, MODE, progression, 304, 25, 3.5, 65, gate=1.03)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 304, 25, 3.5, 88)
    c.drum_groove(sc, 304, 25, 3.5, 96, subdivision=0.5, toms=True)
    c.brass_hits(sc, (6,), ROOT, MODE, progression, 332, 16, 3.5, 90)
    c.sequence_motif(sc, 4, ROOT + 12, MODE, MOTIF, 336, 6, 9.0, 88, 112, (0, 5, 7))
    for ch in (2, 4, 5, 6):
        c.expression_arc(sc, ch, 304, 390, 52, 118, 66)
    c.feature(sc, "rising tide cell", 4, 7, 390, {73}, min_notes=25)

