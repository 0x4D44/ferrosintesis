from __future__ import annotations

import engine as en


def switch(sc: en.Score, ch: int, prog: int, beat: float) -> None:
    if beat > 0.1:
        sc.reset_controls(ch, beat - 0.18)
    sc.program(ch, prog, beat)


def pulse_chords(
    sc: en.Score,
    ch: int,
    chords: list[list[int]],
    start: float,
    bars: int,
    vel: int,
    span: float = 4.0,
    gate: float = 0.85,
) -> None:
    for i in range(bars):
        notes = chords[i % len(chords)]
        for j, n in enumerate(notes):
            sc.note(ch, n, start + i * span + j * 0.01, span * gate, vel - j * 3, jt=2, jv=2)


def octave_riff(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    start: float,
    beats: float,
    vel: int,
    step: float = 0.5,
    octave: int = 0,
) -> None:
    degrees = [0, 0, 3, 4, 5, 4, 3, 7, 0, 2, 3, 5, 7, 5, 3, 2]
    count = int(beats / step)
    for i in range(count):
        deg = degrees[i % len(degrees)]
        accent = 14 if i % 8 == 0 else 0
        p = en.pitch(root, mode, deg, octave)
        sc.note(ch, p, start + i * step, step * 0.82, vel + accent, jt=1, jv=2)
        if i % 4 == 0:
            sc.note(ch, p + 12, start + i * step, step * 0.72, vel - 8 + accent, jt=1, jv=2)


def climb_line(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    start: float,
    beats: float,
    vel0: int,
    vel1: int,
    step: float = 0.5,
) -> None:
    degrees = [0, 2, 3, 5, 7, 9, 10, 12, 14, 12, 10, 9, 7, 5, 3, 2]
    count = int(beats / step)
    for i in range(count):
        deg = degrees[i % len(degrees)] + (i // len(degrees))
        v = int(en.lerp(vel0, vel1, i / max(1, count - 1)))
        sc.note(ch, en.pitch(root, mode, deg), start + i * step, step * 0.95, v, jt=2, jv=3)


def feature(
    sc: en.Score,
    name: str,
    ch: int,
    start: float,
    end: float,
    programs,
    **kwargs,
) -> None:
    sc.feature(en.Feature(name=name, ch=ch, start=start, end=end, programs=set(programs), **kwargs))
