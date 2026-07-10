"""Letters to a Future Ocean -- luminous messages sent beyond living memory."""

from __future__ import annotations

import engine as en
from . import common as c


ROOT = 50  # D3
MODE = "lydian"
LETTER = [(0, 0.0, 0.7), (2, 0.9, 0.55), (6, 1.7, 1.2), (5, 3.2, 0.6), (3, 4.1, 0.7), (1, 5.2, 1.5)]
PROGRESSION = [0, 4, 1, 5, 2, 6, 3, 4]


def _letter(sc: en.Score, ch: int, start: float, root: int, mode: str, vel: int, stretch: float = 1.0) -> None:
    for degree, offset, dur in LETTER:
        sc.note(ch, en.pitch(root, mode, degree), start + offset * stretch, dur * stretch, vel, jt=3, jv=3)


def _memory_wave(
    sc: en.Score,
    start: float,
    beats: float,
    span: float,
    mode: str,
    vel: int,
    high_tide: bool = False,
) -> None:
    bars = int(beats / span)
    c.flowing_arp(sc, 1, ROOT + 12, mode, PROGRESSION, start, bars, span, 0.5, vel)
    for bar in range(bars):
        b = start + bar * span
        degree = PROGRESSION[bar % len(PROGRESSION)]
        chord = c.voiced_chord(ROOT, mode, degree, 0, 4)
        for i, note in enumerate(chord):
            # Strings arrive like the broad back of a wave, never off-centre.
            sc.note(5, note, b + 0.18 * i, span * 0.82, vel - 18 - i * 2, jt=3, jv=2)
        sc.note(6, en.pitch(ROOT - 12, mode, degree), b, span * 0.78, vel - 8, jt=2, jv=2)
        if high_tide and bar % 2 == 0:
            for i, note in enumerate(chord[1:]):
                sc.note(7, note + 12, b + 0.5 + i * 0.05, span * 0.66, vel - 28 - i * 2, jt=4, jv=2)


def _wind_reply(sc: en.Score, start: float, beats: float, mode: str, vel: int) -> None:
    degrees = [0, 2, 6, 5, 3, 1, -1, 1, 4, 2, 0, -2]
    for i in range(int(beats / 1.5)):
        ch = (2, 3, 4)[i % 3]
        root = ROOT + 12 + (5 if ch == 3 else (0 if ch == 2 else -3))
        degree = degrees[i % len(degrees)]
        sc.note(ch, en.pitch(root, mode, degree), start + i * 1.5, 1.05, vel + (7 if i % 8 == 0 else 0), jt=4, jv=4)


def _storm(sc: en.Score, start: float, beats: float) -> None:
    """The one violent paragraph: rain hockets around a stubborn salutation."""
    c.hocket(sc, (0, 1, 8, 2, 3, 4), ROOT + 12, "melodic_minor",
             [0, 2, 6, 5, 8, 4, 1, 7, 3, 9, 5, 2], start, beats, 0.25, 78)
    c.bass_pattern(sc, 6, ROOT - 12, "melodic_minor", [0, 5, 1, 6, 2], start, int(beats / 5), 5.0, 78)
    c.brass_hits(sc, (10,), ROOT, "melodic_minor", [0, 5, 1, 6], start, int(beats / 5), 5.0, 79)
    c.cinematic_drums(sc, start, int(beats / 5), 5.0, 82)
    for beat in (start, start + 15, start + 30, start + 45):
        _letter(sc, 2, beat, ROOT + 12, "melodic_minor", 84, 0.72)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "ink piano", 0, 88, 64, 62, 8, 10),
        (1, "tide harp", 46, 91, 54, 72, 10, 15),
        (2, "addressing flute", 73, 89, 70, 68, 15, 16),
        (3, "reply oboe", 68, 84, 58, 62, 8, 10),
        (4, "salt clarinet", 71, 86, 72, 58, 8, 8),
        (5, "memory strings", 48, 82, 64, 78, 25, 10),
        (6, "deep current cello", 42, 91, 64, 66, 10, 5),
        (7, "future choir", 52, 74, 64, 88, 30, 12),
        (8, "phosphor bells", 98, 79, 46, 75, 18, 24),
        (10, "storm horn", 60, 88, 64, 62, 8, 6),
        (9, "weather", None, 98, 64, 55, 0, 0),
    ])

    c.section(sc, 0, "Dear Water Not Yet Born", meter=(3, 4))
    c.section(sc, 60, "Postscript in Starlight", 62, (6, 8))
    c.section(sc, 120, "Archives of Rain", 68, (4, 4))
    c.section(sc, 192, "The Storm Reads Us", 78, (5, 4))
    c.section(sc, 252, "Ink Runs Clear", 60, (3, 2))
    c.section(sc, 312, "Future Shore", 56, (3, 4))
    c.section(sc, 360, "Last Address", 48, (4, 4))

    _memory_wave(sc, 0, 60, 3.0, MODE, 49)
    _wind_reply(sc, 6, 50, MODE, 53)
    _letter(sc, 2, 0, ROOT + 12, MODE, 58)
    _letter(sc, 3, 30, ROOT + 17, MODE, 54, 1.08)
    for beat, degree in ((0, 0), (15, 4), (30, 1), (45, 5)):
        sc.note(0, en.pitch(ROOT, MODE, degree), beat, 4.5, 42, jt=3, jv=2)

    _memory_wave(sc, 60, 60, 6.0, MODE, 54, high_tide=True)
    _wind_reply(sc, 60, 60, MODE, 59)
    c.flowing_arp(sc, 8, ROOT + 24, MODE, [0, 4, 1, 5], 60, 10, 6.0, 1.0, 40)
    _letter(sc, 2, 72, ROOT + 12, MODE, 63)
    _letter(sc, 4, 102, ROOT + 9, MODE, 57, 0.92)

    _memory_wave(sc, 120, 72, 4.0, "mixolydian", 58, high_tide=True)
    _wind_reply(sc, 120, 72, "mixolydian", 65)
    c.flowing_arp(sc, 0, ROOT, "mixolydian", PROGRESSION, 120, 18, 4.0, 1.0, 50)
    _letter(sc, 2, 132, ROOT + 12, "mixolydian", 68, 0.9)
    _letter(sc, 3, 168, ROOT + 17, "mixolydian", 64, 1.12)

    _storm(sc, 192, 60)
    en.wah(sc, 8, 192, 60, 34, 116, 0.5)
    en.cc_curve(sc, 5, 11, [(192, 58), (222, 120), (248, 84), (252, 42)], 0.5)
    en.cc_curve(sc, 7, 11, [(192, 34), (232, 102), (252, 26)], 0.5)

    _memory_wave(sc, 252, 60, 6.0, MODE, 43, high_tide=True)
    _wind_reply(sc, 264, 42, MODE, 52)
    c.flowing_arp(sc, 0, ROOT, MODE, [0, 3, 4, 1], 252, 10, 6.0, 1.0, 42)
    _letter(sc, 2, 276, ROOT + 12, MODE, 59, 1.3)

    _memory_wave(sc, 312, 48, 3.0, MODE, 38, high_tide=True)
    _wind_reply(sc, 318, 36, MODE, 46)
    _letter(sc, 4, 330, ROOT + 9, MODE, 51, 1.45)
    for beat, degree in ((312, 0), (324, 5), (336, 3), (348, 1)):
        chord = c.voiced_chord(ROOT, MODE, degree, 0, 4)
        en.pad(sc, 7, [n + 12 for n in chord[1:]], beat, 10.0, 30)

    # The last letter has almost no accompaniment; its final pitch is deliberately unanswered.
    c.flowing_arp(sc, 1, ROOT + 12, MODE, [0, 4, 1, 0], 360, 6, 4.0, 1.0, 31)
    _letter(sc, 2, 360, ROOT + 12, MODE, 46, 1.6)
    _letter(sc, 3, 372, ROOT + 17, MODE, 37, 1.35)
    for beat, degree in ((360, 0), (368, 4), (376, 1)):
        sc.note(6, en.pitch(ROOT - 12, MODE, degree), beat, 6.5, 34, jt=3, jv=2)
    sc.note(8, en.pitch(ROOT + 24, MODE, 6), 382, 1.4, 28, jt=1, jv=1)

    for ch, lo, peak, end in (
        (0, 31, 97, 35), (1, 35, 104, 30), (2, 38, 112, 42), (3, 34, 102, 38),
        (4, 30, 98, 35), (5, 28, 106, 32), (6, 38, 100, 36), (7, 22, 96, 28),
    ):
        c.expression_arc(sc, ch, 0, 383, lo, peak, end)
    en.cc_curve(sc, 2, 1, [(0, 8), (120, 28), (232, 92), (312, 38), (383, 12)], 1.0)
    en.cc_curve(sc, 8, 94, [(0, 12), (120, 32), (222, 92), (252, 26), (383, 58)], 1.0)
    c.feature(sc, "six-note salutation carried between centuries", 2, 0, 383, {73}, min_notes=35)
