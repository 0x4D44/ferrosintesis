"""One Cell, Many Skies — a four-note organism becomes an orchestra."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 50  # D3
MODE = "dorian"
CELL = [(0, 0.0, 0.65), (2, 1.0, 0.4), (1, 1.5, 0.65), (4, 2.5, 1.0)]


def cell(sc: en.Score, ch: int, start: float, vel: int, *, root: int = ROOT,
         mode: str = MODE, transpose: int = 0, octave: int = 0,
         stretch: float = 1.0, reverse: bool = False) -> None:
    material = list(reversed(CELL)) if reverse else CELL
    for i, (degree, offset, duration) in enumerate(material):
        placed = offset if not reverse else i * 0.75
        sc.note(ch, en.pitch(root, mode, degree + transpose, octave),
                start + placed * stretch, duration * stretch * 0.9, vel,
                jt=2, jv=3)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "first-breath flute", 73, 94, 72, 66, 14, 16),
        (1, "dividing clarinet", 71, 91, 43, 58, 10, 12),
        (2, "cambrian marimba", 12, 89, 91, 43, 8, 17),
        (3, "rooted contrabass", 43, 100, 64, 30, 2, 0),
        (4, "branching strings", 48, 91, 64, 72, 22, 6),
        (5, "wing-bone oboe", 68, 93, 78, 62, 9, 14),
        (6, "ecology choir", 52, 81, 64, 82, 27, 10),
        (7, "migration horn", 60, 96, 64, 58, 8, 6),
        (8, "tidal harp", 46, 90, 36, 62, 14, 18),
        (10, "high-canopy piccolo", 72, 84, 94, 60, 11, 20),
        (11, "deep-time cello", 42, 93, 64, 65, 16, 5),
        (9, "rhythmic life", None, 106, 64, 40, 0, 0),
    ])

    c.section(sc, 0, "One Breath in the Dark", meter=(4, 4))
    c.section(sc, 32, "Division", 78, (3, 4))
    c.section(sc, 80, "Mutation Finds a Shore", 88, (4, 4))
    c.section(sc, 144, "Counterpoint Learns to Swim", 98, (7, 8))
    c.section(sc, 200, "Rhythmic Life", 108, (5, 4))
    c.section(sc, 280, "An Ecology of Air", 116, (4, 4))
    c.section(sc, 360, "Migration Under Six Moons", 92, (6, 8))
    c.section(sc, 420, "The Cell Remembers", 72, (4, 4))

    progression = [0, 3, 5, 2, 6, 4, 1, 0]

    # Monody: the cell appears unchanged, with silence as its first habitat.
    for i in range(4):
        cell(sc, 0, 2 + i * 8, 48 + i * 5, stretch=1.35)
    for i, beat in enumerate((0, 8, 16, 24)):
        sc.note(3, en.pitch(ROOT - 12, MODE, [0, 0, 3, 5][i]), beat,
                6.5, 36 + i * 4, jt=1, jv=2)

    # Division: unison becomes echo, inversion, and a simple harmonic field.
    for i in range(8):
        t = 32 + i * 6.0
        cell(sc, 0, t, 57 + i, transpose=(0, 1, 0, 2)[i % 4])
        cell(sc, 1, t + 1.5, 49 + i, transpose=(0, -1, 2, 1)[i % 4],
             reverse=i % 2 == 1)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 32, 16, 3.0, 34, gate=0.97)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 32, 16, 3.0, 52,
                   anticipation=False)

    # Mutation changes register and rhythm while retaining all four intervals.
    c.flowing_arp(sc, 8, ROOT + 12, MODE, progression, 80, 16, 4.0, 0.5, 54)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 80, 16, 4.0, 42, gate=0.96)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 80, 16, 4.0, 62)
    for i in range(16):
        t = 80 + i * 4.0
        cell(sc, (0, 1, 5, 2)[i % 4], t, 61 + i,
             transpose=(0, 2, -1, 4)[i % 4], octave=1 if i % 5 == 4 else 0,
             stretch=(1.0, 0.75, 1.25)[i % 3], reverse=i % 4 == 2)
    c.drum_groove(sc, 112, 8, 4.0, 64, subdivision=0.5, toms=False)

    # Overlapping entries form the first self-sustaining contrapuntal habitat.
    c.flowing_arp(sc, 8, ROOT + 12, MODE, progression, 144, 16, 3.5, 0.5, 61)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 144, 16, 3.5, 47, gate=0.94)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 144, 16, 3.5, 69)
    c.drum_groove(sc, 144, 16, 3.5, 73, subdivision=0.5, toms=True)
    for i in range(16):
        t = 144 + i * 3.5
        cell(sc, 0, t, 66 + i, transpose=(0, 3, 1, 5)[i % 4])
        cell(sc, 1, t + 0.875, 60 + i, transpose=(4, 1, 5, 2)[i % 4],
             reverse=True)
        if i % 2 == 0:
            cell(sc, 5, t + 1.75, 58 + i, transpose=(2, 5, 3, 6)[i % 4],
                 stretch=0.75)

    # Percussion and short attacks make the organism mobile.
    c.flowing_arp(sc, 8, ROOT + 12, MODE, progression, 200, 16, 5.0, 0.5, 69)
    c.hocket(sc, (1, 2, 5, 10), ROOT + 24, MODE,
             [0, 2, 1, 4, 3, 6, 5, 8, 7, 4], 200, 80, 0.25, 74)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 200, 16, 5.0, 53, gate=0.96)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 200, 16, 5.0, 79)
    c.drum_groove(sc, 200, 16, 5.0, 86, subdivision=0.25, toms=True)
    for i in range(16):
        cell(sc, (0, 1, 5, 7)[i % 4], 200 + i * 5.0, 72 + i,
             transpose=(0, 2, 4, 1)[i % 4], stretch=0.75 if i % 2 else 1.0)

    # Full ecology: independent strata retain the same genetic interval sequence.
    c.flowing_arp(sc, 8, ROOT + 12, MODE, progression, 280, 20, 4.0, 0.25, 76)
    c.hocket(sc, (1, 2, 5, 10), ROOT + 24, MODE,
             [0, 2, 1, 4, 6, 5, 8, 7], 280, 80, 0.25, 82)
    c.chord_cycle(sc, 4, ROOT, MODE, progression, 280, 20, 4.0, 61, gate=0.98)
    c.chord_cycle(sc, 6, ROOT + 12, MODE, progression, 296, 16, 4.0, 50,
                  gate=0.99)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, progression, 280, 20, 4.0, 89)
    c.drum_groove(sc, 280, 20, 4.0, 96, subdivision=0.25, toms=True)
    c.brass_hits(sc, (7,), ROOT, MODE, progression, 296, 16, 4.0, 88)
    for i in range(20):
        t = 280 + i * 4.0
        cell(sc, 0, t, 80 + i, transpose=(0, 3, 5, 2)[i % 4])
        if i % 2 == 0:
            cell(sc, 11, t + 1.0, 68 + i, transpose=(-7, -4, -2, -5)[i % 4],
                 stretch=1.25)

    # Migration thins the ecosystem into calls moving over a centred string bed.
    c.chord_cycle(sc, 4, ROOT, "mixolydian", progression, 360, 20, 3.0, 51,
                  gate=0.99)
    c.chord_cycle(sc, 6, ROOT + 12, "mixolydian", progression, 360, 20, 3.0,
                  43, gate=1.0)
    c.bass_pattern(sc, 3, ROOT - 12, "mixolydian", progression, 360, 20, 3.0,
                   70, anticipation=False)
    c.hocket(sc, (0, 1, 5, 10), ROOT + 24, "mixolydian",
             [0, 2, 1, 4, 7, 5], 360, 60, 0.5, 70)
    for i in range(10):
        cell(sc, 0 if i % 2 == 0 else 5, 360 + i * 6.0, 68 + i * 2,
             mode="mixolydian", transpose=(0, 4, 2, 5)[i % 4], stretch=1.25)
    c.drum_groove(sc, 360, 20, 3.0, 72, subdivision=0.5, toms=False)

    # The coda removes every mutation until only the original cell remains.
    c.chord_cycle(sc, 4, ROOT, MODE, [0, 5, 3, 0], 420, 9, 4.0, 35,
                  gate=1.02)
    c.chord_cycle(sc, 6, ROOT + 12, MODE, [0, 5, 3, 0], 420, 9, 4.0, 30,
                  gate=1.02)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, [0, 5, 3, 0], 420, 9, 4.0, 49,
                   anticipation=False)
    for i in range(5):
        cell(sc, 0, 421 + i * 7.0, 61 - i * 4, stretch=1.25 + i * 0.12)
    cell(sc, 0, 451, 42, stretch=1.4)

    for ch in (0, 4, 6, 7, 11):
        c.expression_arc(sc, ch, 200, 419, 41, 116, 55)
    en.cc_curve(sc, 0, 1, [(0, 3), (144, 28), (280, 76), (360, 45), (456, 8)], 1.0)
    c.feature(sc, "four-note ancestral cell", 0, 2, 456, {73}, min_notes=40)

