"""Every Door Opens at Once -- a maximalist finale resolving into one quiet room."""

from __future__ import annotations

import engine as en
from . import common as c


ROOT = 48  # C3
HINGE = [(0, 0.0, 0.38), (1, 0.5, 0.38), (4, 1.0, 0.78), (2, 2.0, 0.38), (6, 2.5, 0.38), (5, 3.0, 0.95)]
HINGE_DEGREES = [0, 1, 4, 2, 6, 5]
PROGRESSION = [0, 5, 3, 6, 1, 4, 2, 5]


def _hinge(
    sc: en.Score,
    start: float,
    mode: str,
    vel: int,
    transpose: int = 0,
    stretch: float = 1.0,
    shadow: bool = True,
) -> None:
    c.motif(sc, 4, ROOT + 12, mode, HINGE, start, vel, transpose=transpose, stretch=stretch)
    if shadow:
        for i, (degree, offset, duration) in enumerate(HINGE):
            sc.note(8, en.pitch(ROOT + 24, mode, degree + transpose - 2),
                    start + (offset + 0.22) * stretch, duration * stretch * 0.62,
                    vel - 15 - i, jt=2, jv=3)


def _aquatic_glass(sc: en.Score, start: float, beats: float, vel: int) -> None:
    c.hocket(sc, (1, 12, 13), ROOT + 24, "lydian",
             [0, 2, 6, 4, 7, 5, 3, 9, 6, 2, 5, 1], start, beats, 0.25, vel)
    bars = int(beats / 3.5)
    c.chord_cycle(sc, 2, ROOT, "lydian", PROGRESSION, start, bars, 3.5, vel - 25, gate=0.92)
    c.bass_pattern(sc, 3, ROOT - 12, "lydian", PROGRESSION, start, bars, 3.5, vel - 8)
    for i in range(int(beats / 7)):
        _hinge(sc, start + i * 7, "lydian", vel + 3, transpose=(0, 2, 5, 3)[i % 4], stretch=0.72)


def _evolving_layers(sc: en.Score, start: float, beats: float, vel: int) -> None:
    """A tiny cell accumulates mutation, harmony, memory, then self-questioning gaps."""
    cell = [0, 1, 4, 2]
    stages = (
        ((13,), 1.0),
        ((13, 11), 0.5),
        ((13, 11, 1), 0.5),
        ((13, 11, 1, 12), 0.25),
        ((13, 11, 1, 12, 8), 0.25),
        ((13, 11, 1, 12, 8, 0), 0.25),
    )
    stage_len = beats / len(stages)
    for stage, (channels, step) in enumerate(stages):
        s = start + stage * stage_len
        count = int(stage_len / step)
        for i in range(count):
            ch = channels[i % len(channels)]
            mutation = (stage // 2) + (1 if stage >= 4 and i % 11 == 0 else 0)
            degree = cell[(i + stage) % len(cell)] + mutation
            octave = (i // 16) % 2
            sc.note(ch, en.pitch(ROOT + 12, "dorian", degree, octave), s + i * step,
                    step * (0.76 if stage < 5 else 0.62), vel + stage * 4 + (8 if i % 9 == 0 else 0),
                    jt=2, jv=3)
        _hinge(sc, s, "dorian", vel + stage * 4, transpose=stage % 3, stretch=max(0.55, 1.0 - stage * 0.07))
    c.chord_cycle(sc, 7, ROOT, "dorian", PROGRESSION, start, int(beats / 4.5), 4.5, vel - 29, gate=0.88)


def _linked_rooms(sc: en.Score, start: float, beats: float, vel: int) -> None:
    """Short contrasting rooms share a bass door-tone and hand material forwards."""
    modes = ("minor", "mixolydian", "whole", "dorian")
    room = 17.0
    for index in range(int(beats / room)):
        s = start + index * room
        mode = modes[index % len(modes)]
        degree = PROGRESSION[index % len(PROGRESSION)]
        _hinge(sc, s, mode, vel + index * 3, transpose=degree % 4, stretch=(1.0, 0.75, 1.25, 0.62)[index % 4])
        if index % 4 == 0:
            c.flowing_arp(sc, 0, ROOT, mode, PROGRESSION, s, 4, 4.0, 0.5, vel - 7)
        elif index % 4 == 1:
            c.octave_riff(sc, 11, ROOT, mode, s, 16, vel, step=0.5)
        elif index % 4 == 2:
            c.hocket(sc, (1, 12, 6), ROOT + 12, mode, HINGE_DEGREES, s, 16, 0.25, vel - 2)
        else:
            c.brass_hits(sc, (5, 10), ROOT, mode, PROGRESSION, s, 4, 4.0, vel + 5)
        sc.note(3, en.pitch(ROOT - 12, mode, degree), s, 7.5, vel - 9, jt=2, jv=2)
        sc.note(14, en.pitch(ROOT, mode, degree), s + 8.0, 7.0, vel - 25, jt=3, jv=2)


def _market_thirteen(sc: en.Score, start: float, bars: int, vel: int) -> None:
    accents = {0, 3, 6, 8, 11}
    pattern = [0, 2, 5, 1, 4, 7, 3, 6, 2, 8, 5, 1, 0]
    for bar in range(bars):
        b = start + bar * 6.5
        for pulse in range(13):
            beat = b + pulse * 0.5
            ch = (1, 11, 12, 13)[(pulse + bar) % 4]
            sc.note(ch, en.pitch(ROOT + 12, "dorian", pattern[(pulse + bar) % 13]),
                    beat, 0.32, vel + (10 if pulse in accents else 0), jt=1, jv=3)
            sc.hit(46 if pulse in accents else 42, beat, vel - 17 + (8 if pulse in accents else 0), 0.07)
            if pulse in accents:
                sc.hit(36 if pulse in (0, 8) else 37, beat + 0.02, vel + 2)
        degree = PROGRESSION[bar % len(PROGRESSION)]
        sc.note(3, en.pitch(ROOT - 12, "dorian", degree), b, 2.6, vel + 3, jt=2, jv=2)
        sc.note(3, en.pitch(ROOT - 12, "dorian", degree + 4), b + 3.25, 2.0, vel - 2, jt=2, jv=2)
        if bar % 3 == 0:
            _hinge(sc, b, "dorian", vel + 6, transpose=bar % 4, stretch=0.72)


def _black_tie_pursuit(sc: en.Score, start: float, beats: float, vel: int) -> None:
    """Chromatic spy colour without borrowing any known theme or rhythm."""
    pursuit = [0, 1, 5, 4, 2, 6, 3, 1, 7, 5, 2, 4]
    c.hocket(sc, (5, 10, 6), ROOT + 12, "phrygian", pursuit, start, beats, 0.25, vel)
    c.octave_riff(sc, 11, ROOT, "phrygian", start, beats, vel - 5, step=0.25)
    c.bass_pattern(sc, 3, ROOT - 12, "phrygian", [0, 1, 5, 3], start, int(beats / 2.5), 2.5, vel + 3)
    c.drum_groove(sc, start, int(beats / 2.5), 2.5, vel + 4, subdivision=0.25, toms=True)
    for beat in range(int(start), int(start + beats), 10):
        _hinge(sc, float(beat), "phrygian", vel + 8, transpose=(beat // 10) % 4, stretch=0.55)


def _doorstorm(sc: en.Score, start: float, beats: float, vel: int) -> None:
    """Every prior process runs at once, aligned by the six-note hinge."""
    c.hocket(sc, (0, 1, 6, 8, 11, 12, 13), ROOT + 12, "melodic_minor",
             HINGE_DEGREES + [7, 3, 8, 4, 1], start, beats, 0.125, vel)
    c.bass_pattern(sc, 3, ROOT - 12, "melodic_minor", PROGRESSION, start, 12, 5.5, vel + 3)
    c.chord_cycle(sc, 2, ROOT, "melodic_minor", PROGRESSION, start, 12, 5.5, vel - 20, gate=0.78)
    c.chord_cycle(sc, 7, ROOT + 12, "melodic_minor", PROGRESSION, start, 12, 5.5, vel - 32, gate=0.74)
    c.brass_hits(sc, (5, 10), ROOT, "melodic_minor", PROGRESSION, start, 12, 5.5, vel + 7)
    c.drum_groove(sc, start, 12, 5.5, vel + 5, subdivision=0.25, toms=True)
    for beat in (start, start + 11, start + 22, start + 33, start + 44, start + 55):
        _hinge(sc, beat, "melodic_minor", vel + 11, transpose=int((beat - start) / 11) % 5, stretch=0.48)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "threshold piano", 0, 98, 64, 46, 8, 5),
        (1, "aquatic glass", 12, 88, 38, 58, 14, 18),
        (2, "doorframe strings", 48, 91, 64, 68, 20, 7),
        (3, "foundation bass", 33, 105, 64, 24, 3, 0),
        (4, "hinge flute", 73, 98, 68, 58, 15, 12),
        (5, "spy trumpet", 56, 103, 72, 42, 7, 4),
        (6, "corridor sax", 65, 94, 54, 48, 9, 7),
        (7, "many-room choir", 52, 81, 64, 78, 28, 10),
        (8, "recursive lead", 81, 93, 86, 44, 22, 16),
        (10, "cinema horns", 60, 101, 64, 52, 8, 4),
        (11, "electric latch", 27, 96, 44, 36, 12, 9),
        (12, "wave harp", 46, 88, 56, 66, 14, 16),
        (13, "evolution pluck", 80, 88, 82, 42, 20, 15),
        (14, "memory organ", 19, 78, 64, 60, 18, 6),
        (9, "all-room percussion", None, 112, 64, 32, 0, 0),
    ])

    c.section(sc, 0, "The First Hinge", meter=(5, 4))
    c.section(sc, 60, "Glass Floods the Stair", 116, (7, 8))
    c.section(sc, 116, "Small Cells Learn", 124, (9, 8))
    c.section(sc, 188, "Rooms Remember One Another", 112, (4, 4))
    c.section(sc, 256, "Recursive Lantern Market", 128, (13, 8))
    c.section(sc, 334, "Black-Tie Pursuit", 132, (5, 8))
    c.section(sc, 394, "All Thresholds Answer", 120, (6, 8))
    c.section(sc, 462, "Doorstorm", 126, (11, 8))
    c.section(sc, 528, "One Handle Remains", 84, (3, 4))
    c.section(sc, 560, "The Quiet Hall Beyond", 60, (4, 4))

    # Present the unifying idea naked, then let the whole album grow through it.
    for beat, transpose in ((0, 0), (10, 2), (20, 5), (30, 3), (40, 1), (50, 0)):
        _hinge(sc, beat, "dorian", 55 + transpose * 2, transpose, 1.0, shadow=beat >= 20)
    c.flowing_arp(sc, 0, ROOT, "dorian", PROGRESSION, 0, 12, 5.0, 0.5, 48)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 0, 12, 5.0, 57)
    c.chord_cycle(sc, 14, ROOT, "dorian", PROGRESSION, 0, 12, 5.0, 30, gate=0.88)

    _aquatic_glass(sc, 60, 56, 61)
    c.flowing_arp(sc, 0, ROOT, "lydian", PROGRESSION, 60, 16, 3.5, 0.5, 55)

    _evolving_layers(sc, 116, 72, 54)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 116, 16, 4.5, 66)

    _linked_rooms(sc, 188, 68, 62)
    c.chord_cycle(sc, 2, ROOT, "minor", PROGRESSION, 188, 17, 4.0, 38, gate=0.86)

    _market_thirteen(sc, 256, 12, 70)
    c.chord_cycle(sc, 14, ROOT, "dorian", PROGRESSION, 256, 12, 6.5, 38, gate=0.75)

    _black_tie_pursuit(sc, 334, 60, 79)
    c.brass_hits(sc, (5, 10), ROOT, "phrygian", PROGRESSION, 334, 24, 2.5, 84)

    # Six-eight convergence: glass, cell, market accents, and pursuit brass agree on one cadence.
    c.hocket(sc, (1, 12, 13, 8), ROOT + 12, "dorian", HINGE_DEGREES, 394, 68, 0.25, 76)
    c.octave_riff(sc, 11, ROOT, "dorian", 394, 68, 72, step=0.5)
    c.bass_pattern(sc, 3, ROOT - 12, "dorian", PROGRESSION, 394, 22, 3.0, 78)
    c.chord_cycle(sc, 2, ROOT, "dorian", PROGRESSION, 394, 22, 3.0, 50, gate=0.84)
    c.chord_cycle(sc, 7, ROOT + 12, "dorian", PROGRESSION, 394, 22, 3.0, 34, gate=0.76)
    c.brass_hits(sc, (5, 10), ROOT, "dorian", PROGRESSION, 394, 22, 3.0, 81)
    c.drum_groove(sc, 394, 22, 3.0, 84, subdivision=0.5, toms=True)
    for beat in (394, 406, 418, 430, 442, 454):
        _hinge(sc, beat, "dorian", 85, transpose=int((beat - 394) / 12) % 4, stretch=0.62)

    _doorstorm(sc, 462, 66, 88)

    # Doors close in reverse orchestration order, preserving only the motif's contour.
    c.chord_cycle(sc, 2, ROOT, "lydian", [0, 4, 1, 5, 0], 528, 10, 3.0, 35, gate=0.90)
    c.chord_cycle(sc, 7, ROOT + 12, "lydian", [0, 4, 1, 5, 0], 528, 10, 3.0, 25, gate=0.82)
    for beat, ch, transpose in ((528, 10, 0), (534, 5, 2), (540, 6, 4), (546, 8, 1), (552, 4, 0)):
        for i, degree in enumerate(HINGE_DEGREES):
            sc.note(ch, en.pitch(ROOT + 12, "lydian", degree + transpose), beat + i * 0.5,
                    0.38, 63 - int((beat - 528) / 2), jt=2, jv=2)
    for beat, degree in ((528, 0), (536, 4), (544, 1), (552, 5)):
        sc.note(3, en.pitch(ROOT - 12, "lydian", degree), beat, 4.5, 48, jt=2, jv=2)

    # One flute and one piano share the final hinge at human breathing speed.
    final_offsets = [0.0, 1.8, 3.1, 5.8, 8.0, 11.2]
    for i, (degree, offset) in enumerate(zip(HINGE_DEGREES, final_offsets)):
        sc.note(4, en.pitch(ROOT + 12, "lydian", degree), 560 + offset, 1.2 + i * 0.28,
                43 - i * 2, jt=4, jv=2)
        if i in (0, 2, 5):
            sc.note(0, en.pitch(ROOT, "lydian", degree), 560 + offset + 0.34, 2.4,
                    34 - i, jt=3, jv=2)
    sc.note(3, ROOT - 12, 560, 7.5, 31, jt=2, jv=1)
    sc.note(14, ROOT, 568, 6.8, 22, jt=3, jv=1)

    for ch, lo, peak, end in (
        (0, 38, 112, 24), (1, 34, 108, 16), (2, 30, 114, 20), (3, 42, 116, 25),
        (4, 45, 120, 28), (5, 38, 119, 18), (6, 36, 114, 18), (7, 24, 108, 14),
        (8, 32, 118, 12), (10, 38, 120, 16), (11, 35, 116, 14), (12, 28, 110, 12),
        (13, 30, 115, 10), (14, 20, 92, 12),
    ):
        c.expression_arc(sc, ch, 0, 575, lo, peak, end)
    # The epilogue remains intimate, but a local expression floor keeps its
    # flute/piano exchange audible after the doorstorm's very wide dynamic arc.
    for ch, floor, crest, end in ((0, 44, 54, 38), (3, 46, 55, 40),
                                  (4, 50, 62, 44), (14, 38, 48, 34)):
        en.cc_curve(sc, ch, 11, [(560, floor), (570, crest), (575, end)], 0.5)
    en.cc_curve(sc, 4, 1, [(0, 5), (188, 32), (334, 70), (462, 112), (528, 42), (575, 7)], 1.0)
    en.cc_curve(sc, 8, 74, [(0, 68), (116, 92), (334, 118), (462, 127), (528, 74), (575, 45)], 1.0)
    en.cc_curve(sc, 1, 94, [(0, 10), (60, 52), (256, 38), (462, 86), (528, 24), (575, 8)], 1.0)
    c.feature(sc, "six-note hinge unifies every open door", 4, 0, 575, {73}, min_notes=60)
