"""Night Market in Thirteen -- a joyful odd-metre street of many voices."""

from __future__ import annotations

import engine as en
from . import common as c


ROOT = 52  # E3
MODE = "dorian"
THIRTEEN = [0, 2, 4, 7, 5, 3, 8, 6, 4, 1, 5, 2, 0]
CALL = [(0, 0.0, 0.34), (3, 0.5, 0.34), (5, 1.0, 0.8), (2, 2.0, 0.34), (7, 2.5, 0.9)]
PROGRESSION = [0, 3, 5, 1, 4, 6, 2, 5]


def _market_bar(sc: en.Score, start: float, vel: int, mode: str = MODE, turn: int = 0) -> None:
    """One 13/8 bar grouped 3+3+2+3+2, distributed between three stalls."""
    accents = {0, 3, 6, 8, 11}
    for pulse in range(13):
        beat = start + pulse * 0.5
        ch = (1, 2, 7)[(pulse + turn) % 3]
        degree = THIRTEEN[(pulse + turn * 2) % len(THIRTEEN)]
        octave = 1 if pulse in (6, 12) else 0
        sc.note(ch, en.pitch(ROOT + 12, mode, degree, octave), beat, 0.32,
                vel + (11 if pulse in accents else 0), jt=1, jv=3)
        sc.hit(42 if pulse not in accents else 46, beat, vel - 16 + (8 if pulse in accents else 0), 0.07)
        if pulse in accents:
            sc.hit(36 if pulse in (0, 8) else 37, beat + 0.02, vel + 4, 0.08)
        if pulse in (2, 5, 10):
            sc.note(8, en.pitch(ROOT + 24, "pent", degree % 5), beat + 0.25, 0.16, vel - 7, jt=1, jv=2)


def _market_groove(sc: en.Score, start: float, bars: int, vel: int, mode: str = MODE) -> None:
    for bar in range(bars):
        b = start + bar * 6.5
        _market_bar(sc, b, vel + (5 if bar % 4 == 3 else 0), mode, bar % 5)
        degree = PROGRESSION[bar % len(PROGRESSION)]
        for offset, step in ((0.0, 0), (1.5, 4), (3.0, 0), (4.0, 5), (5.5, 2)):
            sc.note(3, en.pitch(ROOT - 12, mode, degree + step), b + offset, 0.42,
                    vel + 5 - int(offset), jt=2, jv=3)
        if bar % 4 == 3:
            sc.hit(49, b + 6.25, vel + 18)


def _vendor_call(sc: en.Score, start: float, vel: int, mode: str = MODE, answer: bool = True) -> None:
    c.motif(sc, 4, ROOT + 12, mode, CALL, start, vel)
    if answer:
        reversed_call = [(degree - 2, offset, duration) for degree, offset, duration in reversed(CALL)]
        # Rebuild offsets so the answer walks forwards while contour walks backwards.
        for i, (degree, _offset, duration) in enumerate(reversed_call):
            sc.note(5, en.pitch(ROOT + 9, mode, degree), start + 3.4 + i * 0.55, duration * 0.8,
                    vel - 7, jt=3, jv=4)
        for i, degree in enumerate((0, 5, 3, 7)):
            sc.note(6, en.pitch(ROOT + 7, mode, degree), start + 6.4 + i * 0.45, 0.33,
                    vel - 11 + i * 2, jt=3, jv=3)


def _solo(sc: en.Score, ch: int, start: float, beats: float, mode: str, vel: int, seed_shift: int) -> None:
    contour = [0, 2, 3, 5, 8, 7, 4, 6, 9, 5, 3, 1, 4, 2, 0, -2]
    steps = [0.25, 0.5, 0.25, 0.75, 0.25, 0.25, 0.5, 0.5]
    beat = start
    i = 0
    while beat < start + beats - 0.3:
        step = steps[(i + seed_shift) % len(steps)]
        degree = contour[(i * 3 + seed_shift) % len(contour)]
        sc.note(ch, en.pitch(ROOT + 12, mode, degree), beat, step * 0.78,
                vel + (10 if i % 13 == 0 else 0), jt=2, jv=5)
        beat += step
        i += 1


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "tea-house piano", 3, 96, 64, 34, 8, 6),
        (1, "lantern marimba", 12, 91, 34, 38, 10, 12),
        (2, "spice xylophone", 13, 86, 92, 30, 5, 8),
        (3, "walking night bass", 32, 103, 64, 22, 2, 0),
        (4, "vendor trumpet", 56, 98, 72, 46, 8, 7),
        (5, "answering alto", 65, 92, 54, 52, 12, 10),
        (6, "alley clarinet", 71, 91, 76, 48, 8, 8),
        (7, "silk-string stall", 107, 88, 42, 42, 10, 11),
        (8, "neon droplets", 81, 84, 90, 40, 18, 22),
        (10, "midnight organ", 16, 80, 64, 58, 16, 8),
        (11, "paper accordion", 21, 87, 62, 48, 8, 6),
        (9, "thirteen baskets", None, 108, 64, 32, 0, 0),
    ])

    c.section(sc, 0, "Lantern Arithmetic", meter=(13, 8))
    c.section(sc, 78, "Vendor Calls Cross", 144, (7, 8))
    c.section(sc, 134, "Pepper-Smoke Solos", 148, (13, 8))
    c.section(sc, 212, "Four-to-the-Floor Courtyard", 132, (4, 4))
    c.section(sc, 284, "Thirteen Returns Laughing", 146, (13, 8))
    c.section(sc, 362, "Last Tram Hocket", 140, (5, 4))
    c.section(sc, 416, "Shutters Sing Goodnight", 118, (3, 4))

    _market_groove(sc, 0, 12, 58)
    for beat in (0, 19.5, 39, 58.5):
        _vendor_call(sc, beat, 62)
    c.chord_cycle(sc, 10, ROOT, MODE, PROGRESSION, 0, 12, 6.5, 37, gate=0.82)
    for beat in range(0, 78, 13):
        sc.note(11, en.pitch(ROOT, MODE, (beat // 13) % 7), beat + 0.75, 1.2, 51, jt=3, jv=3)

    # Seven-eight compresses the market into overlapping cries.
    c.hocket(sc, (1, 2, 7, 8), ROOT + 12, MODE, THIRTEEN, 78, 56, 0.25, 68)
    c.bass_pattern(sc, 3, ROOT - 12, MODE, PROGRESSION, 78, 16, 3.5, 72)
    c.drum_groove(sc, 78, 16, 3.5, 75, subdivision=0.5, toms=True)
    c.chord_cycle(sc, 10, ROOT, MODE, PROGRESSION, 78, 16, 3.5, 42, gate=0.78)
    for beat in (78, 92, 106, 120):
        _vendor_call(sc, beat, 70 + int((beat - 78) / 7))

    _market_groove(sc, 134, 12, 73, "mixolydian")
    _solo(sc, 6, 134, 26, "mixolydian", 72, 1)
    _solo(sc, 5, 160, 26, "mixolydian", 75, 4)
    _solo(sc, 4, 186, 26, "mixolydian", 79, 7)
    c.chord_cycle(sc, 10, ROOT, "mixolydian", PROGRESSION, 134, 12, 6.5, 44, gate=0.84)

    # The courtyard dance is deliberately plain 4/4, but the old 13-note cell rides above it.
    c.octave_riff(sc, 0, ROOT, "mixolydian", 212, 72, 78, step=0.25)
    c.hocket(sc, (1, 2, 7), ROOT + 12, "mixolydian", THIRTEEN, 212, 72, 0.25, 74)
    c.bass_pattern(sc, 3, ROOT - 12, "mixolydian", [0, 5, 3, 4], 212, 18, 4.0, 82)
    c.drum_groove(sc, 212, 18, 4.0, 90, subdivision=0.25, toms=True)
    c.chord_cycle(sc, 10, ROOT, "mixolydian", [0, 5, 3, 4], 212, 18, 4.0, 47, gate=0.72)
    for beat in (220, 236, 252, 268):
        _vendor_call(sc, beat, 81)

    _market_groove(sc, 284, 12, 82)
    _solo(sc, 4, 284, 39, MODE, 84, 3)
    _solo(sc, 6, 323, 39, MODE, 82, 8)
    c.chord_cycle(sc, 10, ROOT, MODE, PROGRESSION, 284, 12, 6.5, 50, gate=0.80)
    for beat in (284, 310, 336):
        _vendor_call(sc, beat, 86)

    c.hocket(sc, (1, 2, 7, 8, 11), ROOT + 12, "pent", THIRTEEN, 362, 54, 0.25, 74)
    c.bass_pattern(sc, 3, ROOT - 12, "pent", [0, 3, 1, 4, 2], 362, 10, 5.0, 78)
    c.drum_groove(sc, 362, 10, 5.0, 81, subdivision=0.5, toms=True)
    _solo(sc, 5, 362, 30, "pent", 76, 5)
    _vendor_call(sc, 396, 73, "pent")

    # Stalls close one by one; the call survives as a five-voice whisper.
    for beat, ch, degree in (
        (416, 4, 0), (419, 5, 3), (422, 6, 5), (425, 11, 2), (428, 4, 7),
        (432, 5, 5), (436, 6, 3), (440, 4, 0),
    ):
        sc.note(ch, en.pitch(ROOT + 12, MODE, degree), beat, 1.3, 46 - int((beat - 416) / 3), jt=3, jv=2)
    for beat, degree in ((416, 0), (424, 4), (432, 1), (440, 0)):
        sc.note(3, en.pitch(ROOT - 12, MODE, degree), beat, 2.2, 42, jt=2, jv=2)
    c.chord_cycle(sc, 10, ROOT, MODE, [0, 4, 1, 0], 416, 8, 3.0, 27, gate=0.88)

    for ch, lo, peak, end in (
        (1, 45, 111, 32), (2, 42, 108, 30), (4, 48, 116, 36), (5, 43, 110, 34),
        (6, 40, 112, 33), (7, 36, 104, 28), (8, 30, 105, 22), (10, 28, 92, 24),
    ):
        c.expression_arc(sc, ch, 0, 441, lo, peak, end)
    en.cc_curve(sc, 4, 1, [(0, 7), (134, 42), (284, 91), (416, 28), (441, 5)], 1.0)
    en.cc_curve(sc, 8, 74, [(0, 74), (134, 108), (212, 126), (362, 82), (441, 46)], 1.0)
    c.feature(sc, "five-note vendor call crossing every district", 4, 0, 441, {56}, min_notes=45)
