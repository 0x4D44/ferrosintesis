from __future__ import annotations

import engine as en


def setup_band(
    sc: en.Score,
    channels: list[tuple[int, str, int | None, int, int, int, int, int]],
) -> None:
    """Set up (channel, name, program, volume, pan, reverb, chorus, echo)."""
    for ch, name, program, volume, pan, reverb, chorus, echo in channels:
        sc.channel(ch, name, program, volume, pan, reverb, chorus, echo)


def section(
    sc: en.Score,
    beat: float,
    name: str,
    bpm: float | None = None,
    meter: tuple[int, int] | None = None,
) -> None:
    sc.marker(beat, name)
    if bpm is not None:
        sc.tempo(beat, bpm)
    if meter is not None:
        sc.timesig(beat, *meter)


def voiced_chord(root: int, mode: str, degree: int, octave: int = 0, size: int = 4) -> list[int]:
    """Diatonic chord with a close middle and open fifth/root foundation."""
    tones = en.chord(root, mode, degree, size=size, octave=octave)
    if len(tones) >= 4:
        tones[-1] += 12
    return tones


def chord_cycle(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    vel: int,
    octave: int = 0,
    size: int = 4,
    gate: float = 0.94,
) -> None:
    for bar in range(bars):
        notes = voiced_chord(root, mode, degrees[bar % len(degrees)], octave, size)
        en.pad(sc, ch, notes, start + bar * beats_per_bar, beats_per_bar * gate, vel + (bar % 4) * 2)


def bass_pattern(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    vel: int,
    octave: int = 0,
    anticipation: bool = True,
) -> None:
    for bar in range(bars):
        deg = degrees[bar % len(degrees)]
        nxt = degrees[(bar + 1) % len(degrees)]
        b = start + bar * beats_per_bar
        p = en.pitch(root, mode, deg, octave)
        fifth = en.pitch(root, mode, deg + 4, octave)
        sc.note(ch, p, b, beats_per_bar * 0.44, vel + 7, jt=2, jv=3)
        sc.note(ch, fifth, b + beats_per_bar * 0.5, beats_per_bar * 0.28, vel, jt=2, jv=3)
        if anticipation:
            sc.note(ch, en.pitch(root, mode, nxt, octave), b + beats_per_bar * 0.84,
                    beats_per_bar * 0.12, vel - 4, jt=1, jv=2)


def motif(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    cells: list[tuple[int, float, float]],
    start: float,
    vel: int,
    transpose: int = 0,
    octave: int = 0,
    stretch: float = 1.0,
    gate: float = 0.9,
) -> None:
    for degree, offset, duration in cells:
        sc.note(ch, en.pitch(root, mode, degree + transpose, octave),
                start + offset * stretch, duration * stretch * gate, vel,
                jt=2, jv=3)


def sequence_motif(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    cells: list[tuple[int, float, float]],
    start: float,
    entries: int,
    entry_span: float,
    vel0: int,
    vel1: int,
    transpositions: tuple[int, ...] = (0, 3, 4, 0),
    octave: int = 0,
) -> None:
    for i in range(entries):
        motif(sc, ch, root, mode, cells, start + i * entry_span,
              int(en.lerp(vel0, vel1, i / max(1, entries - 1))),
              transpose=transpositions[i % len(transpositions)], octave=octave)


def flowing_arp(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    step: float,
    vel: int,
    octave: int = 0,
) -> None:
    for bar in range(bars):
        notes = voiced_chord(root, mode, degrees[bar % len(degrees)], octave, 4)
        order = [0, 1, 2, 1, 3, 2, 1, 2]
        count = int(beats_per_bar / step)
        for i in range(count):
            p = notes[order[i % len(order)] % len(notes)]
            accent = 10 if i == 0 else (4 if i % 4 == 0 else 0)
            sc.note(ch, p, start + bar * beats_per_bar + i * step,
                    step * 0.88, vel + accent, jt=1, jv=3)


def hocket(
    sc: en.Score,
    channels: tuple[int, ...],
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    beats: float,
    step: float,
    vel: int,
    octave: int = 0,
) -> None:
    count = int(beats / step)
    for i in range(count):
        ch = channels[i % len(channels)]
        p = en.pitch(root, mode, degrees[i % len(degrees)], octave + (i // len(degrees)) % 2)
        sc.note(ch, p, start + i * step, step * 0.72, vel + (10 if i % 8 == 0 else 0), jt=1, jv=2)


def drum_groove(
    sc: en.Score,
    start: float,
    bars: int,
    beats_per_bar: float = 4.0,
    energy: int = 84,
    subdivision: float = 0.5,
    toms: bool = False,
) -> None:
    for bar in range(bars):
        b = start + bar * beats_per_bar
        sc.hit(36, b, energy + 12)
        if beats_per_bar >= 3:
            sc.hit(38, b + beats_per_bar * 0.5, energy + 8)
        count = max(1, int(beats_per_bar / subdivision))
        for i in range(count):
            key = 46 if i == count - 1 and bar % 4 == 3 else 42
            sc.hit(key, b + i * subdivision, energy - 18 + (6 if i % 2 == 0 else 0), 0.08)
        if toms and bar % 4 == 3:
            for i, key in enumerate((45, 47, 48, 50)):
                sc.hit(key, b + beats_per_bar - 1.0 + i * 0.25, energy + i * 3)
        elif bar % 8 == 7:
            sc.hit(49, b + beats_per_bar - 0.15, energy + 16)


def cinematic_drums(
    sc: en.Score,
    start: float,
    bars: int,
    beats_per_bar: float,
    energy: int,
) -> None:
    for bar in range(bars):
        b = start + bar * beats_per_bar
        sc.hit(36, b, energy + 14)
        sc.hit(41 if bar % 2 == 0 else 43, b + beats_per_bar * 0.5, energy + 4)
        if bar % 2:
            sc.hit(49, b + beats_per_bar - 0.12, energy + 18)
        if bar % 4 == 3:
            for i, key in enumerate((45, 47, 48, 50)):
                sc.hit(key, b + beats_per_bar - 1.0 + i * 0.25, energy + i * 4)


def brass_hits(
    sc: en.Score,
    channels: tuple[int, ...],
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    vel: int,
) -> None:
    for bar in range(bars):
        b = start + bar * beats_per_bar
        chord = voiced_chord(root, mode, degrees[bar % len(degrees)], 0, 3)
        for k, ch in enumerate(channels):
            for j, p in enumerate(chord):
                sc.note(ch, p + (12 if k else 0), b, beats_per_bar * 0.34,
                        vel - j * 3 - k * 4, jt=2, jv=3)


def expression_arc(sc: en.Score, ch: int, start: float, end: float,
                   lo: int = 48, peak: int = 112, finish: int = 68) -> None:
    mid = start + (end - start) * 0.68
    en.cc_curve(sc, ch, 11, [(start, lo), (mid, peak), (end, finish)], step=0.5)


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
