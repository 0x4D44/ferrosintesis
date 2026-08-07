#!/usr/bin/env python3
"""Shared melodic and harmonic material for *Every Voice Forward*."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import engine as en


@dataclass(frozen=True)
class Theme:
    name: str
    degrees: tuple[int, ...]
    rhythm: tuple[float, ...]

    def pitches(self, root: int, mode: str = "major", octave: int = 0) -> list[int]:
        return [en.pitch(root, mode, degree, octave) for degree in self.degrees]


# Four hooks, one per family-led track.  They are deliberately distinct in
# contour and rhythm, yet all favour open fourths/sixths so they can coexist in
# the finale without turning into a chromatic thicket.
DAYBREAK = Theme(
    "Daybreak Relay",
    (0, 1, 2, 4, 5, 4, 2, 1),
    (0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
)
ENGINES = Theme(
    "Brighter Engines",
    (0, 2, 4, 5, 4, 2, 1, 0),
    (0.75, 0.25, 0.5, 0.5, 0.75, 0.25, 0.5, 0.5),
)
OPEN_SKY = Theme(
    "Open-Sky Signal",
    (4, 3, 1, 2, 4, 6, 5, 4),
    (0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5),
)
WORLD = Theme(
    "The World in the Chorus",
    (0, 4, 3, 1, 2, 5, 4, 2),
    (0.5, 0.5, 0.75, 0.25, 0.5, 0.5, 0.5, 0.5),
)

THEMES = (DAYBREAK, ENGINES, OPEN_SKY, WORLD)

# Semitone roots relative to each track tonic.  The first progression is the
# familiar I-V-vi-IV lift; the alternates prevent the 20-minute suite from
# sounding like one loop with changing patches.
UPWARD = (0, 7, 9, 5)
WIDE_HORIZON = (0, 4, 5, 9)
SECOND_WIND = (2, 5, 0, 7)
OPEN_DOOR = (9, 5, 0, 7)
LYDIAN_LIFT = (0, 2, 7, 5)


def chord_for_semitone(root: int, semitone: int, quality: str = "major", size: int = 4) -> list[int]:
    intervals = {
        "major": (0, 4, 7, 11, 14),
        "minor": (0, 3, 7, 10, 14),
        "sus2": (0, 2, 7, 12, 14),
        "sus4": (0, 5, 7, 12, 17),
        "power": (0, 7, 12, 19, 24),
    }[quality]
    return [root + semitone + interval for interval in intervals[:size]]


def progression_chords(
    root: int,
    progression: Sequence[int],
    bars: int,
    octave: int = 0,
    qualities: Sequence[str] = ("major", "major", "minor", "major"),
    size: int = 4,
) -> list[list[int]]:
    result: list[list[int]] = []
    for bar in range(bars):
        index = bar % len(progression)
        quality = qualities[index % len(qualities)]
        result.append([n + octave * 12 for n in chord_for_semitone(root, progression[index], quality, size)])
    return result


def voiced(notes: Sequence[int], low: int, high: int, inversion: int = 0, spread: bool = False) -> list[int]:
    result = en.invert(notes, inversion)
    fitted = [en.fit_range(note, low, high) for note in result]
    fitted.sort()
    if spread and len(fitted) >= 4:
        fitted[1] += 12
        fitted.sort()
        while fitted[-1] > high:
            fitted[-1] -= 12
            fitted.sort()
    return fitted


def theme_notes(theme: Theme, root: int, mode: str, low: int, high: int, shift: int = 0) -> list[int]:
    return [en.fit_range(n + shift, low, high) for n in theme.pitches(root, mode)]


def emit_theme(
    sc: en.Score,
    ch: int,
    theme: Theme,
    root: int,
    mode: str,
    start: float,
    velocity: int,
    low: int,
    high: int,
    repeats: int = 1,
    transpose_each: int = 0,
    octave_shift: int = 0,
    tag: str | None = None,
) -> float:
    cursor = start
    base = theme_notes(theme, root, mode, low, high, octave_shift)
    for repeat in range(repeats):
        for index, (note, duration) in enumerate(zip(base, theme.rhythm)):
            accent = 9 if index == 0 else 0
            sc.note(
                ch,
                en.fit_range(note + repeat * transpose_each, low, high),
                cursor,
                duration * 0.86,
                velocity + accent,
                jt=1,
                jv=2,
                tag=tag or theme.name,
            )
            cursor += duration
    return cursor


def emit_countertheme(
    sc: en.Score,
    ch: int,
    theme: Theme,
    root: int,
    start: float,
    velocity: int,
    low: int,
    high: int,
    retrograde: bool = False,
    inversion: bool = False,
    tag: str | None = None,
) -> float:
    degrees = list(theme.degrees)
    rhythm = list(theme.rhythm)
    if retrograde:
        degrees.reverse()
        rhythm.reverse()
    if inversion:
        axis = degrees[0]
        degrees = [axis - (degree - axis) for degree in degrees]
    cursor = start
    for index, (degree, duration) in enumerate(zip(degrees, rhythm)):
        note = en.fit_range(en.pitch(root, "major", degree), low, high)
        sc.note(ch, note, cursor, duration * 0.82, velocity + (7 if index == 0 else 0), jt=1, jv=2,
                tag=tag or f"{theme.name} counter")
        cursor += duration
    return cursor


def circle_transpose(root: int, bar: int, progression: Sequence[int]) -> int:
    return root + progression[bar % len(progression)]


def clamp_notes(notes: Iterable[int], low: int, high: int) -> list[int]:
    return [en.fit_range(note, low, high) for note in notes]
