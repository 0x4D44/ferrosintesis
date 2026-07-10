"""Carry the Lantern — an original continuous suite in eight linked rooms."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 48  # C3
LANTERN = [(0, 0.0, 0.45), (2, 0.5, 0.45), (5, 1.0, 0.9), (3, 2.0, 0.45), (7, 2.5, 1.15)]
PROGRESSION = [0, 5, 3, 6, 0, 4, 1, 5]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "room piano", 0, 101, 64, 38, 7, 7),
        (1, "clipped guitar", 28, 98, 34, 29, 7, 9),
        (2, "answer guitar", 30, 94, 94, 33, 10, 12),
        (3, "patient bass", 33, 107, 64, 20, 0, 0),
        (4, "lantern strings", 48, 88, 64, 66, 21, 6),
        (5, "night organ", 18, 82, 64, 61, 18, 22),
        (6, "humane choir", 52, 76, 64, 78, 25, 14),
        (7, "first road guitar", 29, 98, 24, 31, 8, 10),
        (8, "second road guitar", 26, 94, 104, 35, 9, 12),
        (10, "brass threshold", 60, 96, 64, 51, 8, 5),
        (11, "window flute", 73, 85, 70, 64, 15, 20),
        (9, "suite drums", None, 112, 64, 30, 0, 0),
    ])

    c.section(sc, 0, "I. Accounts in the Rain", 104, (4, 4))
    c.section(sc, 80, "II. Copper Engine", 132, (7, 8))
    c.section(sc, 152, "III. Blue Window", 82, (6, 8))
    c.section(sc, 216, "IV. Small Sun Parade", 118, (4, 4))
    c.section(sc, 288, "V. The Drums Disagree", 148, (5, 4))
    c.section(sc, 352, "VI. Three Roads at Once", 156, (12, 8))
    c.section(sc, 448, "VII. Lanterns Returning", 126, (4, 4))
    c.section(sc, 544, "VIII. The Common Chord", 112, (3, 4))
    c.section(sc, 592, "Coda. Leave One Light", 76, (4, 4))
    sc.tempo(632, 58)

    # I — a close piano song. The lantern cell is stated without a singer.
    c.chord_cycle(sc, 0, ROOT, "major", PROGRESSION, 0, 20, 4.0, 59, gate=0.93)
    c.flowing_arp(sc, 0, ROOT + 12, "major", PROGRESSION, 0, 20, 4.0, 0.5, 53)
    c.bass_pattern(sc, 3, ROOT - 12, "major", PROGRESSION, 0, 20, 4.0, 60)
    c.sequence_motif(sc, 11, ROOT + 12, "major", LANTERN, 8, 8, 8.0, 55, 76, (0, 4, 5, 2))
    c.chord_cycle(sc, 4, ROOT, "major", PROGRESSION, 32, 12, 4.0, 37, gate=1.03)
    c.drum_groove(sc, 48, 8, 4.0, 61, subdivision=1.0)
    sc.sustain(0, 0, 79.5)

    # II — guitar drive; the last piano cadence becomes the first clipped riff.
    c.hocket(sc, (1, 2), ROOT + 12, "mixolydian", [0, 2, 5, 3, 7, 5, 4, 1], 80, 72, 0.25, 78)
    c.flowing_arp(sc, 0, ROOT + 12, "mixolydian", PROGRESSION, 80, 18, 4.0, 0.5, 67)
    c.bass_pattern(sc, 3, ROOT - 12, "mixolydian", PROGRESSION, 80, 18, 4.0, 83)
    c.drum_groove(sc, 80, 18, 4.0, 91, subdivision=0.25, toms=True)
    c.brass_hits(sc, (10,), ROOT, "mixolydian", PROGRESSION, 112, 10, 4.0, 83)
    c.sequence_motif(sc, 1, ROOT + 12, "mixolydian", LANTERN, 88, 7, 9.0, 70, 94, (0, 2, 5, 7))
    en.wah(sc, 2, 96, 48, 43, 104, 0.5)

    # III — nocturnal interlude: the pulse falls away but the same cell remains.
    c.chord_cycle(sc, 5, ROOT, "dorian", [0, 3, 5, 1], 152, 16, 4.0, 39, gate=1.05)
    c.chord_cycle(sc, 6, ROOT, "dorian", [0, 3, 5, 1], 152, 16, 4.0, 31, gate=1.06)
    c.flowing_arp(sc, 0, ROOT + 12, "dorian", [0, 3, 5, 1], 152, 16, 4.0, 1.0, 44)
    c.sequence_motif(sc, 11, ROOT + 24, "dorian", LANTERN, 156, 6, 10.0, 43, 64, (0, -2, 3, 0))
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", [0, 3, 5, 1], 168, 12, 4.0, 51, anticipation=False)
    for beat in range(160, 216, 8):
        sc.hit(51, beat, 42)
        sc.hit(42, beat + 5.5, 35)
    c.expression_arc(sc, 5, 152, 216, 28, 72, 41)

    # IV — a bright, compact parade; callbacks are harmonised rather than copied.
    c.flowing_arp(sc, 0, ROOT + 12, "major", [0, 4, 5, 3], 216, 18, 4.0, 0.25, 68)
    c.hocket(sc, (1, 2, 11), ROOT + 12, "major", [0, 2, 5, 4, 7, 9, 5, 3], 216, 72, 0.5, 72)
    c.bass_pattern(sc, 3, ROOT - 12, "major", [0, 4, 5, 3], 216, 18, 4.0, 80)
    c.drum_groove(sc, 216, 18, 4.0, 84, subdivision=0.5, toms=True)
    c.chord_cycle(sc, 4, ROOT, "major", [0, 4, 5, 3], 216, 18, 4.0, 47, gate=1.01)
    c.sequence_motif(sc, 10, ROOT, "major", LANTERN, 232, 6, 8.0, 67, 87, (0, 4, 5, 7))

    # V — a drum feature with pitched fragments tossed across the kit.
    c.bass_pattern(sc, 3, ROOT - 12, "minor", [0, 1, 3, 6], 288, 13, 5.0, 88)
    c.hocket(sc, (0, 1, 2), ROOT + 12, "minor", [0, 5, 3, 1, 7], 288, 64, 1.0, 66)
    for bar in range(13):
        b = 288 + bar * 5.0
        sc.hit(36, b, 106)
        sc.hit(38, b + 2.0, 103)
        sc.hit(36, b + 3.5, 95)
        for k in range(10):
            sc.hit(42 if k % 3 else 46, b + k * 0.5, 67 + (k % 4) * 5)
        if bar % 2:
            for k, key in enumerate((41, 43, 45, 47, 48, 50)):
                sc.hit(key, b + 3.5 + k * 0.25, 86 + k * 4)
    c.brass_hits(sc, (10,), ROOT, "minor", [0, 1, 3, 6], 308, 8, 5.0, 91)

    # VI — three independent guitar roads, then increasingly shared cadences.
    road_a = [0, 2, 5, 7, 5, 3, 2, 0]
    road_b = [7, 5, 4, 2, 0, 2, 3, 5]
    road_c = [3, 4, 6, 8, 7, 5, 4, 2]
    for i in range(192):
        beat = 352 + i * 0.5
        phrase = (i // 24) % 4
        sc.note(7, en.pitch(ROOT + 12, "dorian", road_a[i % 8] + phrase), beat, 0.38, 82 + (i % 8 == 0) * 12, jt=1, jv=2)
        sc.note(8, en.pitch(ROOT + 12, "dorian", road_b[(i + 3) % 8] - phrase), beat + 0.16, 0.34, 77, jt=1, jv=2)
        sc.note(2, en.pitch(ROOT + 12, "dorian", road_c[(i + 5) % 8]), beat + 0.32, 0.31, 74, jt=1, jv=2)
    c.chord_cycle(sc, 4, ROOT, "dorian", PROGRESSION, 352, 24, 4.0, 54, gate=1.02)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 352, 24, 4.0, 94)
    c.drum_groove(sc, 352, 24, 4.0, 101, subdivision=0.25, toms=True)
    for start in (376, 400, 424):
        c.sequence_motif(sc, 10, ROOT, "dorian", LANTERN, start, 2, 8.0, 82, 108, (0, 5))

    # VII — material from every earlier room returns in a single broad key-space.
    c.flowing_arp(sc, 0, ROOT + 12, "mixolydian", PROGRESSION, 448, 24, 4.0, 0.25, 76)
    c.hocket(sc, (1, 2, 7, 8), ROOT + 12, "mixolydian", [0, 2, 5, 3, 7, 9, 8, 4], 448, 96, 0.25, 84)
    c.bass_pattern(sc, 3, ROOT - 12, "mixolydian", PROGRESSION, 448, 24, 4.0, 90)
    c.chord_cycle(sc, 4, ROOT, "mixolydian", PROGRESSION, 448, 24, 4.0, 55, gate=1.02)
    c.drum_groove(sc, 448, 24, 4.0, 96, subdivision=0.25, toms=True)
    c.brass_hits(sc, (10,), ROOT, "mixolydian", PROGRESSION, 472, 18, 4.0, 96)
    c.sequence_motif(sc, 11, ROOT + 24, "mixolydian", LANTERN, 456, 10, 8.0, 72, 105, (0, 4, 5, 7))

    # VIII — a communal 3/4 refrain, then a deliberately brief and humane coda.
    c.chord_cycle(sc, 6, ROOT, "major", [0, 5, 3, 4], 544, 16, 3.0, 44, gate=1.04)
    c.flowing_arp(sc, 0, ROOT + 12, "major", [0, 5, 3, 4], 544, 16, 3.0, 0.5, 61)
    c.bass_pattern(sc, 3, ROOT - 12, "major", [0, 5, 3, 4], 544, 16, 3.0, 72)
    c.drum_groove(sc, 544, 16, 3.0, 75, subdivision=0.5)
    c.sequence_motif(sc, 11, ROOT + 12, "major", LANTERN, 548, 5, 8.0, 59, 78, (0, 3, 5, 0))
    c.chord_cycle(sc, 0, ROOT, "major", [0, 4, 5, 0], 592, 12, 4.0, 52, gate=1.04)
    c.chord_cycle(sc, 6, ROOT, "major", [0, 4, 5, 0], 592, 12, 4.0, 35, gate=1.05)
    c.sequence_motif(sc, 11, ROOT + 12, "major", LANTERN, 596, 4, 8.0, 52, 64, (0, -2, 0, 0))
    for ch in (0, 4, 5, 6, 11):
        c.expression_arc(sc, ch, 592, 640, 45, 75, 38)

    c.feature(sc, "lantern cell through every room", 11, 8, 628, {73}, min_notes=30)
    c.feature(sc, "three-road contrapuntal guitars", 7, 352, 448, {29}, min_notes=120, monophonic=True)
