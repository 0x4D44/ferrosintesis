from __future__ import annotations

import itertools
import math

import engine as en
import material


def setup_band(
    sc: en.Score,
    channels: list[tuple[int, str, int | None, int, int, int, int, int, int]],
) -> None:
    """Set up (ch, name, program, volume, pan, reverb, chorus, echo, bank)."""
    for ch, name, program, volume, pan, reverb, chorus, echo, bank in channels:
        sc.channel(ch, name, program, volume, pan, reverb, chorus, echo, bank)


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


def _candidate_voicings(base: list[int], lo: int, hi: int) -> list[list[int]]:
    candidates: set[tuple[int, ...]] = set()
    for shifts in itertools.product((-12, 0, 12), repeat=len(base)):
        notes = sorted(n + s for n, s in zip(base, shifts))
        if notes[0] < lo or notes[-1] > hi:
            continue
        if any(b - a < 2 for a, b in zip(notes, notes[1:])):
            continue
        candidates.add(tuple(notes))
    return [list(c) for c in sorted(candidates)]


def voice_led_progression(
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    size: int = 4,
    lo: int = 52,
    hi: int = 81,
) -> list[list[int]]:
    """Choose inversions that minimise total voice movement across a progression."""
    result: list[list[int]] = []
    previous: list[int] | None = None
    for degree in degrees:
        raw = en.chord(root, mode, degree, size=size)
        candidates = _candidate_voicings(raw, lo, hi)
        if not candidates:
            candidates = [raw]
        if previous is None:
            chosen = min(candidates, key=lambda c: (abs(sum(c) / len(c) - (lo + hi) / 2), c))
        else:
            chosen = min(
                candidates,
                key=lambda c: (
                    sum(abs(a - b) for a, b in zip(previous, c)),
                    max(abs(a - b) for a, b in zip(previous, c)),
                    c,
                ),
            )
        result.append(chosen)
        previous = chosen
    return result


def chord_cycle(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    velocity: int,
    size: int = 4,
    lo: int = 52,
    hi: int = 81,
    gate: float = 0.94,
    lift_every: int = 0,
) -> None:
    voicings = voice_led_progression(root, mode, list(degrees), size=size, lo=lo, hi=hi)
    for bar in range(bars):
        notes = list(voicings[bar % len(voicings)])
        if lift_every and bar and bar % lift_every == 0:
            notes[-1] = min(hi, notes[-1] + 12)
        en.pad(sc, ch, notes, start + bar * beats_per_bar, beats_per_bar * gate,
               velocity + (bar % 4) * 2)


def pulse_chords(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    velocity: int,
    pulses: tuple[float, ...] = (0.0, 1.5, 2.5),
    duration: float = 0.42,
    lo: int = 52,
    hi: int = 81,
) -> None:
    voicings = voice_led_progression(root, mode, list(degrees), lo=lo, hi=hi)
    for bar in range(bars):
        base = start + bar * beats_per_bar
        notes = voicings[bar % len(voicings)]
        for p_i, offset in enumerate(pulses):
            if offset >= beats_per_bar:
                continue
            for n_i, note in enumerate(notes):
                sc.note(ch, note, base + offset + 0.008 * n_i, duration,
                        velocity + (8 if p_i == 0 else 0) - 2 * n_i, jt=1, jv=2)


def bass_pattern(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    velocity: int,
    octave: int = -1,
    active: bool = True,
    syncopated: bool = False,
) -> None:
    for bar in range(bars):
        degree = degrees[bar % len(degrees)]
        next_degree = degrees[(bar + 1) % len(degrees)]
        base = start + bar * beats_per_bar
        root_note = en.pitch(root, mode, degree, octave)
        fifth = en.pitch(root, mode, degree + 4, octave)
        if not active:
            sc.note(ch, root_note, base, beats_per_bar * 0.86, velocity, jt=2, jv=2)
            continue
        if syncopated:
            pattern = ((0.0, root_note, 0.42, 8), (0.75, root_note + 12, 0.20, 0),
                       (1.5, fifth, 0.32, -4), (2.25, root_note, 0.42, 2),
                       (3.25, en.pitch(root, mode, next_degree, octave), 0.28, -3))
        else:
            pattern = ((0.0, root_note, 0.58, 8), (1.0, root_note + 12, 0.38, 0),
                       (2.0, fifth, 0.58, -3), (3.0, root_note, 0.38, 2),
                       (3.5, en.pitch(root, mode, next_degree, octave), 0.30, -4))
        for offset, note, duration, delta in pattern:
            if offset < beats_per_bar:
                sc.note(ch, note, base + offset, min(duration, beats_per_bar - offset),
                        velocity + delta, jt=1, jv=3)


def motif(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    cells: tuple[tuple[int, float, float], ...],
    start: float,
    velocity: int,
    transpose: int = 0,
    octave: int = 0,
    stretch: float = 1.0,
    gate: float = 0.90,
    harmony: int | None = None,
) -> None:
    for degree, offset, duration in cells:
        note = en.pitch(root, mode, degree + transpose, octave)
        sc.note(ch, note, start + offset * stretch, duration * stretch * gate,
                velocity, jt=1, jv=3)
        if harmony is not None:
            sc.note(ch, en.pitch(root, mode, degree + transpose + harmony, octave),
                    start + offset * stretch, duration * stretch * gate,
                    velocity - 12, jt=1, jv=2)


def motif_sequence(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    cells: tuple[tuple[int, float, float], ...],
    start: float,
    entries: int,
    span: float,
    velocity0: int,
    velocity1: int,
    transpositions: tuple[int, ...] = (0, 0, 2, -1),
    octave: int = 0,
    harmony: int | None = None,
) -> None:
    for i in range(entries):
        motif(sc, ch, root, mode, cells, start + i * span,
              int(round(en.lerp(velocity0, velocity1, i / max(1, entries - 1)))),
              transpose=transpositions[i % len(transpositions)], octave=octave,
              harmony=harmony)


def flowing_arp(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    beats_per_bar: float,
    step: float,
    velocity: int,
    lo: int = 55,
    hi: int = 91,
    order: tuple[int, ...] = (0, 1, 2, 1, 3, 2, 1, 2),
) -> None:
    voicings = voice_led_progression(root, mode, list(degrees), lo=lo, hi=hi)
    for bar in range(bars):
        en.arpeggio(sc, ch, voicings[bar % len(voicings)],
                    start + bar * beats_per_bar, beats_per_bar, step,
                    velocity + (bar % 4) * 2, order=order)


def orbit_riff(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    start: float,
    end: float,
    velocity: int,
    step: float = 0.25,
    octave_lift_at: float | None = None,
    period: float = 32.0,
) -> None:
    count = int(round((end - start) / step))
    for i in range(count):
        beat = start + i * step
        octave = 1 if octave_lift_at is not None and beat >= octave_lift_at else 0
        degree = material.ORBIT_RIFF[i % len(material.ORBIT_RIFF)]
        sc.note(ch, en.pitch(root, mode, degree, octave), beat, step * 0.72,
                velocity + (9 if i % 4 == 0 else 0), jt=0, jv=2)
    en.autopan(sc, ch, start, end - start, 0, 127, period=period, step=0.5)


def four_floor(
    sc: en.Score,
    start: float,
    bars: int,
    energy: int,
    hats16: bool = False,
    tambourine: bool = False,
    crash_every: int = 8,
) -> None:
    for bar in range(bars):
        base = start + 4.0 * bar
        for beat in range(4):
            sc.hit(36, base + beat, energy + 12)
            sc.hit(42, base + beat, energy - 14)
            sc.hit(46, base + beat + 0.5, energy - 10, 0.18)
            if hats16:
                sc.hit(42, base + beat + 0.25, energy - 24, 0.06)
                sc.hit(42, base + beat + 0.75, energy - 22, 0.06)
            if tambourine:
                sc.hit(54, base + beat + 0.5, energy - 20, 0.10)
        sc.hit(38, base + 1.0, energy + 5)
        sc.hit(38, base + 3.0, energy + 7)
        if crash_every and bar % crash_every == 0:
            sc.hit(49, base, energy + 20, 1.0)


def build_drums(
    sc: en.Score,
    start: float,
    bars: int,
    energy0: int,
    energy1: int,
    final_roll: float = 4.0,
    kick_after: float = 0.45,
) -> None:
    for bar in range(bars):
        phase = bar / max(1, bars - 1)
        energy = int(round(en.lerp(energy0, energy1, phase)))
        base = start + 4.0 * bar
        subdivision = 0.5 if phase < 0.55 else 0.25
        count = int(round(4.0 / subdivision))
        for i in range(count):
            sc.hit(42, base + i * subdivision, energy - 22 + (6 if i % 4 == 0 else 0), 0.07)
        sc.hit(38, base + 1.0, energy - 8)
        sc.hit(38, base + 3.0, energy - 5)
        if phase >= kick_after:
            for b in range(4):
                sc.hit(36, base + b, energy + 6)
        if bar % 4 == 3:
            fill(sc, base, min(3, 1 + bar // max(1, bars // 3)), energy + 6)
    roll_start = start + bars * 4.0 - final_roll
    count = int(round(final_roll / 0.25))
    for i in range(count):
        sc.hit(38, roll_start + 0.25 * i,
               int(round(en.lerp(54, min(124, energy1 + 18), i / max(1, count - 1)))), 0.08)


def half_time(sc: en.Score, start: float, bars: int, energy: int) -> None:
    for bar in range(bars):
        base = start + 4.0 * bar
        sc.hit(36, base, energy + 12)
        sc.hit(38, base + 2.0, energy + 7)
        for i in range(8):
            sc.hit(42 if i % 4 else 44, base + 0.5 * i, energy - 22, 0.08)
        if bar % 4 == 3:
            sc.hit(49, base + 3.75, energy + 15, 0.8)


def fill(sc: en.Score, start: float, shape: int, velocity: int) -> None:
    notes = material.FILL_SHAPES[shape % len(material.FILL_SHAPES)]
    for i, (offset, key) in enumerate(notes):
        sc.hit(key, start + offset, min(127, velocity + i // 3), 0.10)


def melodic_fill(
    sc: en.Score,
    ch: int,
    start: float,
    density: int,
    velocity: int,
    low: int = 45,
) -> None:
    pattern = (0, 5, 9, 12, 7, 3, 10, 14, 12, 7, 5, 0)
    step = 4.0 / density
    for i in range(density):
        sc.note(ch, low + pattern[i % len(pattern)], start + i * step,
                min(0.18, step * 0.75), velocity + min(18, i), jt=0, jv=3)


def riser(sc: en.Score, ch: int, start: float, duration: float, velocity: int) -> None:
    sc.note(ch, 62, start, duration, velocity, jt=0, jv=0)
    en.cc_curve(sc, ch, 11, [(start, 42), (start + duration * 0.7, 96),
                             (start + duration, 127)], step=0.25)


def brass_stabs(
    sc: en.Score,
    channels: tuple[int, ...],
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    velocity: int,
    step_bars: int = 1,
    answer: bool = True,
) -> None:
    voicings = voice_led_progression(root, mode, list(degrees), size=3, lo=55, hi=82)
    for bar in range(0, bars, step_bars):
        beat = start + 4.0 * bar
        notes = voicings[bar % len(voicings)]
        for c_i, ch in enumerate(channels):
            offset = 0.0 if c_i == 0 else (2.0 if answer else 0.0)
            for n_i, note in enumerate(notes):
                sc.note(ch, note + (12 if c_i else 0), beat + offset + 0.01 * n_i,
                        0.55, velocity - 3 * n_i - 4 * c_i, jt=1, jv=3)


def choir_blocks(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    velocity: int,
    vowel0: int = 35,
    vowel1: int = 100,
    octave: int = 0,
) -> None:
    chord_cycle(sc, ch, root, mode, degrees, start, bars, 4.0, velocity,
                size=3, lo=48 + 12 * octave, hi=76 + 12 * octave, gate=0.98)
    en.cc_curve(sc, ch, 70, [(start, vowel0), (start + bars * 2.5, vowel1),
                             (start + bars * 4.0, max(vowel0, vowel1 - 12))], step=1.0)


def sidechain_beds(sc: en.Score, channels: tuple[int, ...], start: float, duration: float,
                   low: int = 68, high: int = 112) -> None:
    for ch in channels:
        en.expression_pump(sc, ch, start, duration, low=low, high=high)


def echo_throw(sc: en.Score, ch: int, beat: float, peak: int = 110, base: int = 8) -> None:
    en.cc_curve(sc, ch, 94, [(beat, peak), (beat + 1.5, base)], step=0.125)


def guitar_bend_phrase(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    start: float,
    degrees: tuple[int, ...],
    velocity: int,
    octave: int = 1,
) -> None:
    sc.bend_range(ch, 2, max(0.0, start - 0.05))
    for i, degree in enumerate(degrees):
        beat = start + 1.0 * i
        note = en.pitch(root, mode, degree, octave)
        sc.note(ch, note, beat, 0.92, velocity + (5 if i % 4 == 3 else 0), jt=1, jv=3)
        if i % 4 == 3:
            en.bend_curve(sc, ch, [(beat, 0.0), (beat + 0.45, 1.0),
                                   (beat + 0.82, 0.0)], step=0.08)
    sc.bend(ch, 0.0, start + len(degrees))


def note_ons(sc: en.Score, ch: int | None = None) -> list[tuple[int, int, int, int]]:
    """Return (tick, channel, pitch, velocity) note-ons."""
    out: list[tuple[int, int, int, int]] = []
    channels = [ch] if ch is not None else sorted(sc.events)
    for channel in channels:
        for event_tick, _priority, data in sc.events.get(channel, []):
            if (data[0] & 0xF0) == 0x90 and len(data) == 3 and data[2] > 0:
                out.append((event_tick, channel, data[1], data[2]))
    return sorted(out)


def cc_lane(sc: en.Score, ch: int, number: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for event_tick, _priority, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and len(data) == 3 and data[1] == number:
            out.append((event_tick, data[2]))
    return sorted(out)


def velocity_sum(sc: en.Score, start: float, end: float, channels: set[int] | None = None) -> int:
    lo, hi = en.tick(start), en.tick(end)
    return sum(v for t, ch, _p, v in note_ons(sc) if lo <= t < hi and (channels is None or ch in channels))


def note_count(sc: en.Score, start: float, end: float, channels: set[int] | None = None) -> int:
    lo, hi = en.tick(start), en.tick(end)
    return sum(1 for t, ch, _p, _v in note_ons(sc) if lo <= t < hi and (channels is None or ch in channels))


def pitches_at(sc: en.Score, ch: int, start: float, end: float) -> list[int]:
    lo, hi = en.tick(start), en.tick(end)
    return [p for t, _ch, p, _v in note_ons(sc, ch) if lo <= t < hi]


def degrees_to_pitches(root: int, mode: str, degrees: tuple[int, ...] | list[int], octave: int = 0) -> list[int]:
    return [en.pitch(root, mode, degree, octave) for degree in degrees]


def full_circle_extrema(lane: list[tuple[int, int]]) -> tuple[int, int]:
    values: list[int] = []
    for _tick, value in lane:
        if not values or value != values[-1]:
            values.append(value)
    maxima = minima = 0
    for a, b, c in zip(values, values[1:], values[2:]):
        if a < b > c and b >= 126:
            maxima += 1
        if a > b < c and b <= 1:
            minima += 1
    return maxima, minima


def bend_lane(sc: en.Score, ch: int) -> list[tuple[int, int]]:
    """Return (tick, 14-bit bend value) for one channel."""
    out: list[tuple[int, int]] = []
    for event_tick, _priority, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0 and len(data) == 3:
            out.append((event_tick, data[1] | (data[2] << 7)))
    return sorted(out)


def program_lane(sc: en.Score, ch: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for event_tick, _priority, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xC0 and len(data) == 2:
            out.append((event_tick, data[1]))
    return sorted(out)


def notes_near(sc: en.Score, ch: int, beat: float, tolerance_ticks: int = 4) -> list[int]:
    target = en.tick(beat)
    return [p for t, _ch, p, _v in note_ons(sc, ch)
            if abs(t - target) <= tolerance_ticks]


def progression_root_failures(
    sc: en.Score,
    ch: int,
    root: int,
    mode: str,
    degrees: tuple[int, ...] | list[int],
    start: float,
    bars: int,
    beats_per_bar: float = 4.0,
    octave: int = -1,
) -> list[str]:
    failures: list[str] = []
    for bar in range(bars):
        degree = degrees[bar % len(degrees)]
        expected = en.pitch(root, mode, degree, octave)
        got = notes_near(sc, ch, start + bar * beats_per_bar)
        if expected not in got:
            failures.append(
                f"bar {bar} at {start + bar * beats_per_bar:g}: "
                f"bass root {expected} absent (got {got[:4]})"
            )
            if len(failures) >= 4:
                break
    return failures


def kick_count(sc: en.Score, start: float, end: float) -> int:
    lo, hi = en.tick(start), en.tick(end)
    return sum(1 for t, _ch, pitch, _vel in note_ons(sc, 9)
               if lo <= t < hi and pitch in (35, 36))


def channel_count(sc: en.Score, start: float, end: float) -> int:
    lo, hi = en.tick(start), en.tick(end)
    return len({ch for t, ch, _p, _v in note_ons(sc) if lo <= t < hi})


def peak_cc(sc: en.Score, ch: int, number: int, default: int = 0) -> int:
    lane = cc_lane(sc, ch, number)
    return max((value for _tick, value in lane), default=default)


def floor_cc(sc: en.Score, ch: int, number: int, default: int = 127) -> int:
    lane = cc_lane(sc, ch, number)
    return min((value for _tick, value in lane), default=default)
