"""Late for the Ordinary — an original brisk domestic-change-of-scene caper."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 53  # F3
MODE = "major"
ERRAND = [
    (0, 0.0, 0.35), (2, 0.5, 0.35), (4, 1.0, 0.35),
    (3, 1.5, 0.7), (6, 2.5, 0.35), (5, 3.0, 0.8),
]


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "upright piano", 1, 105, 64, 31, 7, 5),
        (1, "walking bass", 32, 104, 64, 22, 2, 0),
        (2, "busy clarinet", 71, 94, 60, 52, 8, 11),
        (3, "window flute", 73, 91, 84, 58, 10, 16),
        (4, "kettle oboe", 68, 90, 72, 57, 8, 12),
        (5, "corner trumpet", 56, 99, 48, 45, 5, 5),
        (6, "stairwell trombone", 57, 96, 64, 48, 5, 4),
        (7, "afternoon strings", 48, 83, 64, 66, 18, 5),
        (8, "clock celesta", 8, 87, 92, 48, 11, 18),
        (10, "shop-door horn", 60, 94, 64, 54, 7, 5),
        (9, "pavement kit", None, 109, 64, 31, 0, 0),
    ])

    c.section(sc, 0, "Shoelaces and Sunlight", meter=(4, 4))
    c.section(sc, 64, "Three Flights Down", 144, (3, 4))
    c.section(sc, 112, "The Street Has Seven Corners", 126, (7, 8))
    c.section(sc, 168, "Everybody Else Is Early", 150, (4, 4))
    c.section(sc, 232, "Queue in Five", 118, (5, 4))
    c.section(sc, 272, "Green Light Fugato", 154, (4, 4))
    c.section(sc, 336, "Tea Before the Clock Notices", 128, (3, 4))

    progression = [0, 5, 1, 4, 2, 6, 3, 4]

    # Piano and bass establish a bright tune with clipped, conversational answers.
    c.flowing_arp(sc, 0, ROOT, MODE, progression, 0, 16, 4.0, 0.5, 69)
    c.bass_pattern(sc, 1, ROOT - 24, MODE, progression, 0, 16, 4.0, 74)
    c.sequence_motif(sc, 2, ROOT + 12, MODE, ERRAND, 4, 8, 8.0,
                     62, 82, (0, 4, 1, 5))
    c.sequence_motif(sc, 3, ROOT + 12, MODE, ERRAND, 8, 7, 8.0,
                     57, 76, (3, 0, 5, 2))
    c.chord_cycle(sc, 7, ROOT, MODE, progression, 16, 12, 4.0, 37, gate=0.91)
    c.drum_groove(sc, 16, 12, 4.0, 75, subdivision=0.5, toms=False)
    for bar in range(16):
        b = bar * 4.0
        sc.note(8, en.pitch(ROOT + 12, MODE, [0, 4, 2, 5][bar % 4]),
                b + 3.5, 0.22, 53 + bar, jt=1, jv=2)

    # Three-beat stairs: each landing shifts the tune to another woodwind.
    c.flowing_arp(sc, 0, ROOT, MODE, progression, 64, 16, 3.0, 0.5, 76)
    c.bass_pattern(sc, 1, ROOT - 24, MODE, progression, 64, 16, 3.0, 82)
    c.hocket(sc, (2, 3, 4), ROOT + 12, MODE,
             [0, 2, 4, 3, 6, 5], 64, 48, 0.25, 72)
    c.sequence_motif(sc, 2, ROOT + 12, MODE, ERRAND, 64, 8, 6.0,
                     70, 90, (0, 3, 5, 1))
    c.drum_groove(sc, 64, 16, 3.0, 82, subdivision=0.25, toms=False)
    c.brass_hits(sc, (5,), ROOT, MODE, progression, 82, 10, 3.0, 78)

    # Seven corners briefly scramble the gait without losing the tune.
    c.flowing_arp(sc, 0, ROOT, "mixolydian", progression, 112, 16, 3.5,
                  0.25, 78)
    c.bass_pattern(sc, 1, ROOT - 24, "mixolydian", progression, 112, 16, 3.5, 85)
    c.hocket(sc, (2, 3, 4, 8), ROOT + 12, "mixolydian",
             [0, 2, 4, 3, 6, 5, 1], 112, 56, 0.25, 79)
    c.sequence_motif(sc, 2, ROOT + 12, "mixolydian", ERRAND, 115.5, 8, 7.0,
                     75, 96, (0, 4, 2, 6))
    c.chord_cycle(sc, 7, ROOT, "mixolydian", progression, 112, 16, 3.5,
                  44, gate=0.92)
    c.drum_groove(sc, 112, 16, 3.5, 89, subdivision=0.25, toms=True)
    c.brass_hits(sc, (5, 6), ROOT, "mixolydian", progression, 133, 10, 3.5, 85)

    # Back on four: brisk counter-lines, horn punctuation, and a fuller piano hand.
    c.flowing_arp(sc, 0, ROOT, MODE, progression, 168, 16, 4.0, 0.25, 84)
    c.bass_pattern(sc, 1, ROOT - 24, MODE, progression, 168, 16, 4.0, 91)
    c.hocket(sc, (2, 3, 4, 8), ROOT + 12, MODE,
             [0, 2, 4, 3, 6, 5, 8, 7], 168, 64, 0.25, 84)
    c.sequence_motif(sc, 2, ROOT + 12, MODE, ERRAND, 168, 8, 8.0,
                     82, 103, (0, 5, 2, 7))
    c.chord_cycle(sc, 7, ROOT, MODE, progression, 168, 16, 4.0, 50, gate=0.93)
    c.drum_groove(sc, 168, 16, 4.0, 96, subdivision=0.25, toms=True)
    c.brass_hits(sc, (5, 6, 10), ROOT, MODE, progression, 184, 12, 4.0, 93)

    # A queue in five lowers the dynamic and lets the bass tease the downbeat.
    c.flowing_arp(sc, 0, ROOT, "dorian", [0, 3, 5, 1], 232, 8, 5.0, 1.0, 61)
    c.bass_pattern(sc, 1, ROOT - 24, "dorian", [0, 3, 5, 1], 232, 8, 5.0, 72)
    c.hocket(sc, (2, 4, 8), ROOT + 12, "dorian",
             [0, 3, 2, 5, 4], 232, 40, 1.0, 63)
    c.sequence_motif(sc, 4, ROOT + 12, "dorian", ERRAND, 237, 4, 10.0,
                     58, 74, (0, -1, 3, 1))
    c.chord_cycle(sc, 7, ROOT, "dorian", [0, 3, 5, 1], 232, 8, 5.0, 36,
                  gate=0.95)
    c.drum_groove(sc, 252, 4, 5.0, 70, subdivision=0.5, toms=False)

    # The main tune enters as a street-corner fugato, one voice every two beats.
    c.flowing_arp(sc, 0, ROOT, MODE, progression, 272, 16, 4.0, 0.25, 88)
    c.bass_pattern(sc, 1, ROOT - 24, MODE, progression, 272, 16, 4.0, 97)
    c.chord_cycle(sc, 7, ROOT, MODE, progression, 272, 16, 4.0, 55, gate=0.95)
    c.drum_groove(sc, 272, 16, 4.0, 103, subdivision=0.25, toms=True)
    for i in range(16):
        t = 272 + i * 4.0
        c.motif(sc, (2, 3, 4)[i % 3], ROOT + 12, MODE, ERRAND, t,
                86 + i, transpose=(0, 4, 1, 5)[i % 4], stretch=0.75)
        if i % 2 == 0:
            c.motif(sc, 5, ROOT, MODE, ERRAND, t + 2.0, 80 + i,
                    transpose=(0, 3, 5, 2)[i % 4], stretch=0.75)
    c.brass_hits(sc, (5, 6, 10), ROOT, MODE, progression, 288, 12, 4.0, 101)

    # Home again: three-beat phrases settle, but the clock keeps a last wink.
    c.flowing_arp(sc, 0, ROOT, MODE, [0, 4, 5, 0], 336, 16, 3.0, 0.5, 68)
    c.bass_pattern(sc, 1, ROOT - 24, MODE, [0, 4, 5, 0], 336, 16, 3.0, 76,
                   anticipation=False)
    c.chord_cycle(sc, 7, ROOT, MODE, [0, 4, 5, 0], 336, 16, 3.0, 42,
                  gate=0.98)
    c.hocket(sc, (2, 3, 4), ROOT + 12, MODE,
             [0, 2, 4, 3, 5, 0], 336, 48, 0.5, 64)
    c.sequence_motif(sc, 2, ROOT + 12, MODE, ERRAND, 336, 6, 8.0,
                     72, 86, (0, 4, 2, 0))
    c.brass_hits(sc, (5, 6), ROOT, MODE, [0, 4, 5, 0], 354, 8, 3.0, 78)
    c.drum_groove(sc, 336, 16, 3.0, 79, subdivision=0.5, toms=False)
    for i in range(16):
        sc.note(8, en.pitch(ROOT + 12, MODE, [0, 4, 2, 5][i % 4]),
                336 + i * 3.0 + 2.5, 0.2, 54 + i, jt=1, jv=2)

    for ch in (0, 2, 3, 5, 6):
        c.expression_arc(sc, ch, 168, 383, 49, 114, 67)
    en.cc_curve(sc, 2, 1, [(0, 5), (112, 34), (272, 76), (336, 38), (384, 12)], 1.0)
    c.feature(sc, "six-note errand tune", 2, 4, 384, {71}, min_notes=40)
