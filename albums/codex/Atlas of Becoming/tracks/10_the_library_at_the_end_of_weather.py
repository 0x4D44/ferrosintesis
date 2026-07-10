"""The Library at the End of Weather — chamber counterpoint opens into storm."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 46  # Bb2
SUBJECT = [0, 2, 5, 4, 1, 6, 3, 7]
ANSWER = [4, 6, 2, 5, 3, 1, 7, 4]
PROGRESSION = [0, 3, 5, 1, 4, 6, 2, 5]


def _subject(sc: en.Score, ch: int, start: float, mode: str, transpose: int,
             octave: int, vel: int, step: float = 0.5, reverse: bool = False) -> None:
    degrees = list(reversed(SUBJECT)) if reverse else SUBJECT
    for i, degree in enumerate(degrees):
        sc.note(ch, en.pitch(ROOT, mode, degree + transpose, octave), start + i * step,
                step * (1.45 if i in (2, 7) else 0.82), vel + (8 if i == 0 else 0),
                jt=1, jv=2)


def _page_flutter(sc: en.Score, start: float, beats: float, energy: int) -> None:
    for i in range(int(beats / 0.25)):
        beat = start + i * 0.25
        degree = [0, 1, 3, 6, 4, 2, 7, 5, 8, 4, 9, 6][i % 12]
        ch = (5, 6, 7)[i % 3]
        sc.note(ch, en.pitch(ROOT + 12, "lydian", degree, 1 + (i // 24) % 2), beat,
                0.16, energy + (10 if i % 12 == 0 else 0), jt=1, jv=2)


def _weather_ostinato(sc: en.Score, start: float, beats: float, vel: int) -> None:
    degrees = [0, 4, 1, 5, 2, 6, 3, 7, 5, 1, 4, 2, 6, 3, 8, 4]
    for i in range(int(beats / 0.25)):
        beat = start + i * 0.25
        degree = degrees[i % len(degrees)]
        sc.note(1, en.pitch(ROOT, "dorian", degree, 1), beat, 0.21,
                vel + (11 if i % 8 == 0 else 0), jt=1, jv=2)
        if i % 2 == 0:
            sc.note(2, en.pitch(ROOT, "dorian", degree + 2, 0), beat + 0.08, 0.36,
                    vel - 10, jt=1, jv=2)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "reading-room piano", 0, 92, 64, 51, 7, 9),
        (1, "first violin", 40, 94, 38, 59, 11, 6),
        (2, "second violin and viola", 41, 88, 90, 61, 10, 6),
        (3, "catalogue cello", 42, 94, 64, 56, 8, 3),
        (4, "dust bassoon", 70, 87, 58, 61, 6, 12),
        (5, "paper birds flute", 73, 91, 79, 67, 16, 22),
        (6, "margin clarinet", 71, 87, 45, 61, 9, 16),
        (7, "shelf harp", 46, 89, 27, 67, 13, 20),
        (8, "impossible stacks", 48, 79, 64, 78, 25, 10),
        (10, "weather horns", 60, 101, 64, 55, 7, 5),
        (11, "window choir", 52, 75, 64, 81, 28, 14),
        (9, "roof and rain", None, 109, 64, 34, 0, 0),
    ])

    c.section(sc, 0, "The Catalogue Breathes", 84, (4, 4))
    c.section(sc, 64, "Rain Writes on the Windows", 96, (5, 4))
    c.section(sc, 128, "The Missing Folio", 72, (3, 4))
    c.section(sc, 192, "Pages Learn the Air", 108, (7, 8))
    c.section(sc, 256, "Storm in Every Aisle", 126, (6, 8))
    c.section(sc, 320, "Readers Hold the Roof", 92, (4, 4))
    c.section(sc, 384, "Birds Carry the Index", 78, (5, 4))
    c.section(sc, 424, "One Lamp After Weather", 60, (3, 4))

    # A dry chamber exposition: one subject, then three answers at widening registers.
    for entry, (ch, start, tr, octv, rev) in enumerate(((3, 0, 0, 0, False),
                                                        (2, 8, 4, 1, False),
                                                        (1, 16, 1, 1, True),
                                                        (4, 24, -2, 1, False))):
        for repeat in range(5):
            _subject(sc, ch, start + repeat * 8.0, "minor", tr + repeat % 2,
                     octv, 53 + entry * 7 + repeat * 2, reverse=rev)
    c.chord_cycle(sc, 0, ROOT, "minor", PROGRESSION, 0, 16, 4.0, 39, gate=0.97)
    c.bass_pattern(sc, 3, ROOT - 12, "minor", PROGRESSION, 32, 8, 4.0, 53,
                   anticipation=False)
    for beat in range(0, 64, 8):
        sc.hit(51, beat + 7.5, 31)

    # Rain is pointillist percussion around a strict five-beat contrapuntal tread.
    c.flowing_arp(sc, 7, ROOT + 12, "dorian", PROGRESSION, 64, 13, 5.0, 0.5, 54)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 64, 13, 5.0, 66)
    for i in range(128):
        beat = 64 + i * 0.5
        sc.hit(42 if i % 4 else 44, beat, 35 + (i % 9) * 3, 0.06)
        if i % 5 == 0:
            sc.hit(37, beat + 0.25, 44 + i // 8)
    for start in range(64, 128, 10):
        _subject(sc, 1, start, "dorian", 0, 1, 67)
        _subject(sc, 2, start + 2.5, "dorian", 4, 0, 59, reverse=True)
    c.chord_cycle(sc, 8, ROOT, "dorian", PROGRESSION, 64, 13, 5.0, 31, gate=1.03)

    # A low-density search: isolated folio fragments move between desks.
    c.chord_cycle(sc, 11, ROOT, "minor", [0, 4, 1, 5], 128, 21, 3.0, 26, gate=1.05)
    c.flowing_arp(sc, 0, ROOT + 12, "minor", [0, 4, 1, 5], 128, 21, 3.0, 1.0, 42)
    c.bass_pattern(sc, 3, ROOT - 12, "minor", [0, 4, 1, 5], 128, 21, 3.0, 48,
                   anticipation=False)
    for i, start in enumerate(range(132, 192, 6)):
        _subject(sc, (4, 6, 5)[i % 3], start, "minor", (0, 3, -1)[i % 3],
                 1 + (i % 4 == 3), 43 + i * 2, step=0.375, reverse=i % 2 == 1)
    c.expression_arc(sc, 11, 128, 192, 24, 59, 32)

    # Pages become birds: hocketed flute, clarinet, and harp lift off the bar line.
    _page_flutter(sc, 192, 64, 64)
    c.hocket(sc, (5, 6, 7), ROOT + 12, "lydian", [0, 2, 5, 9, 7, 4, 11, 8],
             192, 64, 0.5, 72, octave=1)
    c.chord_cycle(sc, 8, ROOT, "lydian", PROGRESSION, 192, 16, 4.0, 38, gate=1.04)
    c.bass_pattern(sc, 3, ROOT - 12, "lydian", PROGRESSION, 192, 16, 4.0, 70)
    c.drum_groove(sc, 208, 12, 4.0, 62, subdivision=0.5, toms=True)
    en.autopan(sc, 7, 192, 64, 38, 90, 12)

    # The storm arrives in the string figuration; centered stacks keep the weather mono-safe.
    _weather_ostinato(sc, 256, 64, 81)
    c.flowing_arp(sc, 7, ROOT + 12, "dorian", PROGRESSION, 256, 16, 4.0, 0.25, 70)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 256, 16, 4.0, 91)
    c.chord_cycle(sc, 8, ROOT, "dorian", PROGRESSION, 256, 16, 4.0, 49, gate=1.02)
    c.drum_groove(sc, 256, 16, 4.0, 103, subdivision=0.25, toms=True)
    c.brass_hits(sc, (10,), ROOT, "dorian", PROGRESSION, 272, 12, 4.0, 99)
    _page_flutter(sc, 280, 40, 76)

    # Readers answer the storm with a broad augmentation of the opening subject.
    c.chord_cycle(sc, 8, ROOT, "major", PROGRESSION, 320, 16, 4.0, 52, gate=1.03)
    c.chord_cycle(sc, 11, ROOT, "major", PROGRESSION, 320, 16, 4.0, 39, gate=1.04)
    c.bass_pattern(sc, 3, ROOT - 12, "major", PROGRESSION, 320, 16, 4.0, 83)
    c.drum_groove(sc, 320, 16, 4.0, 86, subdivision=0.5, toms=True)
    for entry, ch in enumerate((3, 2, 1, 4, 5, 6)):
        for repeat in range(4):
            _subject(sc, ch, 320 + entry * 2 + repeat * 14, "major", entry - 2,
                     0 + (ch in (1, 5, 6)), 62 + entry * 5, step=0.75,
                     reverse=entry % 2 == 1)
    c.brass_hits(sc, (10,), ROOT, "major", PROGRESSION, 344, 10, 4.0, 84)

    # Weather recedes. Bird calls carry catalogue fragments beyond the building.
    c.chord_cycle(sc, 8, ROOT, "lydian", [0, 5, 3, 1], 384, 8, 5.0, 34, gate=1.05)
    c.flowing_arp(sc, 7, ROOT + 12, "lydian", [0, 5, 3, 1], 384, 8, 5.0, 0.5, 49)
    c.bass_pattern(sc, 3, ROOT - 12, "lydian", [0, 5, 3, 1], 384, 8, 5.0, 55,
                   anticipation=False)
    for i, start in enumerate(range(384, 424, 4)):
        _subject(sc, (5, 6)[i % 2], start, "lydian", (i * 3) % 7, 2,
                 53 + i * 2, step=0.375, reverse=i % 3 == 2)
    for beat in range(384, 424, 5):
        sc.hit(51, beat, 38)

    # One lamp: opening voices return as slow, incomplete phrases around centered strings.
    c.chord_cycle(sc, 0, ROOT, "major", [0, 4, 5, 0], 424, 8, 3.0, 34, gate=1.05)
    c.chord_cycle(sc, 8, ROOT, "major", [0, 4, 5, 0], 424, 8, 3.0, 25, gate=1.06)
    for i, start in enumerate((424, 430, 436, 442)):
        _subject(sc, (3, 2, 1, 5)[i], start, "major", (0, 4, 1, 0)[i],
                 (0, 1, 1, 2)[i], 42 + i * 3, step=0.75, reverse=i == 2)
    for ch in (0, 1, 2, 3, 5, 8, 11):
        c.expression_arc(sc, ch, 424, 448, 31, 54, 22)

    c.feature(sc, "pages become contrapuntal birds", 5, 192, 424, {73}, min_notes=100)
    c.feature(sc, "chamber subject withstands weather", 1, 16, 447, {40}, min_notes=120,
              monophonic=True)
    c.feature(sc, "centered weather orchestra", 8, 64, 448, {48}, min_notes=80)
