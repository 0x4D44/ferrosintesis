#!/usr/bin/env python3
"""Deterministic, standard-library MIDI engine for *Bright Matter*."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import random
import struct
from typing import Callable

PPQ = 480
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"
WAV_DIR = ALBUM_ROOT / "build" / "wav"


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def tick(beat: float) -> int:
    return max(0, int(round(beat * PPQ)))


def _vlq(value: int) -> bytes:
    value = max(0, int(value))
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(out))


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            return value, pos


SCALES: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "pent_minor": (0, 3, 5, 7, 10),
    "pent_major": (0, 2, 4, 7, 9),
    "chromatic": tuple(range(12)),
}


def pitch(root: int, mode: str, degree: int, octave: int = 0) -> int:
    """Return a MIDI pitch for a zero-based diatonic degree."""
    scale = SCALES[mode]
    octs, index = divmod(degree, len(scale))
    return root + scale[index] + 12 * (octs + octave)


def chord(root: int, mode: str, degree: int, size: int = 4, octave: int = 0) -> list[int]:
    return [pitch(root, mode, degree + 2 * i, octave) for i in range(size)]


def bend_raw(semitones: float, range_semitones: float = 2.0) -> int:
    return int(round(clamp(8192 + semitones / range_semitones * 8192, 0, 16383)))


@dataclass(frozen=True)
class TrackSpec:
    number: int
    title: str
    filename: str
    seed: int
    tempo: float
    beats: float
    builder: Callable[["Score"], None]
    oracle: Callable[["Score"], list[tuple[str, list[str]]]]
    style: str
    concept: str
    duration_window: tuple[float, float]
    min_notes: int = 700
    min_channels: int = 9
    min_markers: int = 7
    min_tempo_events: int = 2
    tags: tuple[str, ...] = ()


class Score:
    """Event collector. MIDI channel 9 is percussion."""

    def __init__(self, seed: int, title: str, tempo: float, beats: float) -> None:
        self.seed = seed
        self.title = title
        self.rng = random.Random(seed)
        self.events: dict[int, list[tuple[int, int, bytes]]] = {}
        self.names: dict[int, str] = {}
        self.tempos: list[tuple[float, float]] = [(0.0, tempo)]
        self.timesigs: list[tuple[float, int, int]] = []
        self.markers: list[tuple[float, str]] = []
        self.lyrics: list[tuple[float, str]] = []
        self.last_beat = beats

    def channel(
        self,
        ch: int,
        name: str,
        program: int | None = 0,
        volume: int = 100,
        pan: int = 64,
        reverb: int = 48,
        chorus: int = 0,
        echo: int = 0,
        bank: int = 0,
        beat: float = 0.0,
    ) -> None:
        if not 0 <= ch <= 15:
            raise ValueError(f"invalid MIDI channel {ch}")
        self.names[ch] = name
        self.events.setdefault(ch, [])
        if bank:
            self.cc(ch, 0, bank, beat)
        if program is not None:
            self.program(ch, program, beat)
        self.cc(ch, 7, volume, beat)
        self.cc(ch, 10, pan, beat)
        self.cc(ch, 91, reverb, beat)
        self.cc(ch, 93, chorus, beat)
        self.cc(ch, 94, echo, beat)

    def program(self, ch: int, program: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (tick(beat), 1, bytes([0xC0 | ch, int(clamp(program, 0, 127))]))
        )

    def cc(self, ch: int, number: int, value: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (
                tick(beat),
                2,
                bytes([0xB0 | ch, int(clamp(number, 0, 127)), int(clamp(value, 0, 127))]),
            )
        )

    def aftertouch(self, ch: int, value: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (tick(beat), 2, bytes([0xD0 | ch, int(clamp(value, 0, 127))]))
        )

    def bend(self, ch: int, semitones: float, beat: float, range_semitones: float = 2.0) -> None:
        raw = bend_raw(semitones, range_semitones)
        self.events.setdefault(ch, []).append(
            (tick(beat), 2, bytes([0xE0 | ch, raw & 0x7F, (raw >> 7) & 0x7F]))
        )

    def rpn(self, ch: int, number: int, msb: int, beat: float, lsb: int = 0) -> None:
        base = tick(beat)
        for i, (num, val) in enumerate(
            ((101, 0), (100, number), (6, msb), (38, lsb), (101, 127), (100, 127))
        ):
            self.events.setdefault(ch, []).append(
                (base + i, 2, bytes([0xB0 | ch, num & 0x7F, val & 0x7F]))
            )

    def bend_range(self, ch: int, semitones: int, beat: float = 0.0) -> None:
        self.rpn(ch, 0, semitones, beat)

    def note(
        self,
        ch: int,
        note: int,
        beat: float,
        duration: float,
        velocity: int,
        jt: int = 2,
        jv: int = 3,
    ) -> None:
        note = int(clamp(round(note), 0, 127))
        velocity = int(clamp(round(velocity + self.rng.randint(-jv, jv)), 1, 127))
        on = tick(beat)
        if jt and beat > 0.05:
            on = max(0, on + self.rng.randint(-jt, jt))
        off = max(on + PPQ // 32, tick(beat + max(0.03, duration)))
        events = self.events.setdefault(ch, [])
        events.append((on, 5, bytes([0x90 | ch, note, velocity])))
        events.append((off, 4, bytes([0x80 | ch, note, 0])))
        self.last_beat = max(self.last_beat, beat + duration)

    def hit(self, key: int, beat: float, velocity: int, duration: float = 0.12) -> None:
        self.note(9, key, beat, duration, velocity, jt=1, jv=4)

    def marker(self, beat: float, text: str) -> None:
        self.markers.append((beat, text))

    def lyric(self, beat: float, text: str) -> None:
        self.lyrics.append((beat, text))

    def tempo(self, beat: float, bpm: float) -> None:
        self.tempos.append((beat, bpm))

    def timesig(self, beat: float, numerator: int, denominator: int) -> None:
        self.timesigs.append((beat, numerator, denominator))

    def reset_controls(self, ch: int, beat: float) -> None:
        self.bend(ch, 0.0, beat)
        for number, value in (
            (1, 0), (5, 0), (11, 127), (64, 0), (65, 0), (68, 0),
            (70, 64), (71, 64), (74, 127), (94, 0),
        ):
            self.cc(ch, number, value, beat)
        self.aftertouch(ch, 0, beat)
        self.cc(ch, 101, 127, beat)
        self.cc(ch, 100, 127, beat + 0.002)

    def seconds_at(self, beat: float) -> float:
        tempos = sorted(self.tempos)
        total = 0.0
        cursor = 0.0
        bpm = tempos[0][1] if tempos else 120.0
        for tempo_beat, next_bpm in tempos:
            if tempo_beat >= beat:
                break
            total += (tempo_beat - cursor) * 60.0 / bpm
            cursor = tempo_beat
            bpm = next_bpm
        return total + (beat - cursor) * 60.0 / bpm

    def duration_seconds(self) -> float:
        return self.seconds_at(self.last_beat)

    def _resolve_overlaps(self) -> None:
        """Shorten same-pitch notes when a repeated note begins before its note-off."""
        for events in self.events.values():
            ons: dict[int, list[int]] = {}
            offs: dict[int, list[int]] = {}
            for index, (event_tick, _priority, data) in enumerate(events):
                kind = data[0] & 0xF0
                if kind == 0x90 and len(data) == 3 and data[2] > 0:
                    ons.setdefault(data[1], []).append(event_tick)
                elif kind == 0x80 or (kind == 0x90 and len(data) == 3 and data[2] == 0):
                    offs.setdefault(data[1], []).append(index)
            for note, starts in ons.items():
                indices = offs.get(note, [])
                if len(indices) != len(starts):
                    continue
                starts.sort()
                indices.sort(key=lambda i: events[i][0])
                end_ticks = [events[i][0] for i in indices]
                for i in range(len(starts) - 1):
                    if end_ticks[i] > starts[i + 1]:
                        end_ticks[i] = starts[i + 1]
                for index, end_tick in zip(indices, end_ticks):
                    old = events[index]
                    events[index] = (end_tick, old[1], old[2])

    def to_bytes(self, title: str | None = None, comment: str = "") -> bytes:
        self._resolve_overlaps()
        title = title or self.title
        end_tick = tick(self.last_beat) + 2 * PPQ

        def meta(kind: int, payload: bytes) -> bytes:
            return bytes([0xFF, kind]) + _vlq(len(payload)) + payload

        conductor: list[tuple[int, int, bytes]] = [
            (0, 0, meta(0x03, title.encode("ascii", "replace")))
        ]
        if comment:
            conductor.append((0, 0, meta(0x01, comment.encode("ascii", "replace"))))
        for beat, numerator, denominator in sorted(self.timesigs):
            conductor.append(
                (tick(beat), 1, meta(0x58, bytes([numerator, denominator.bit_length() - 1, 24, 8])))
            )
        for beat, bpm in sorted(self.tempos):
            mpq = int(round(60_000_000 / bpm))
            conductor.append((tick(beat), 2, meta(0x51, mpq.to_bytes(3, "big"))))
        for beat, text in sorted(self.markers):
            conductor.append((tick(beat), 3, meta(0x06, text.encode("ascii", "replace"))))
        for beat, text in sorted(self.lyrics):
            conductor.append((tick(beat), 3, meta(0x05, text.encode("ascii", "replace"))))

        def chunk(events: list[tuple[int, int, bytes]], name: str | None) -> bytes:
            body = bytearray()
            if name:
                body += _vlq(0) + meta(0x03, name.encode("ascii", "replace"))
            last = 0
            for event_tick, priority, data in sorted(events, key=lambda e: (e[0], e[1], e[2])):
                if event_tick < last:
                    raise ValueError("MIDI events are out of order")
                body += _vlq(event_tick - last) + data
                last = event_tick
            body += _vlq(max(0, end_tick - last)) + b"\xFF\x2F\x00"
            return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

        chunks = [chunk(conductor, None)]
        for ch in sorted(self.events):
            chunks.append(chunk(self.events[ch], self.names.get(ch, f"ch{ch}")))
        return b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks)


def cc_curve(sc: Score, ch: int, number: int, points: list[tuple[float, int]], step: float = 0.5) -> None:
    points = sorted(points)
    for (b0, v0), (b1, v1) in zip(points, points[1:]):
        beat = b0
        while beat < b1 - 1e-9:
            phase = (beat - b0) / max(1e-9, b1 - b0)
            sc.cc(ch, number, int(round(lerp(v0, v1, phase))), beat)
            beat += step
    sc.cc(ch, number, points[-1][1], points[-1][0])


def bend_curve(
    sc: Score,
    ch: int,
    points: list[tuple[float, float]],
    step: float = 0.125,
    range_semitones: float = 2.0,
) -> None:
    points = sorted(points)
    for (b0, v0), (b1, v1) in zip(points, points[1:]):
        beat = b0
        while beat < b1 - 1e-9:
            phase = (beat - b0) / max(1e-9, b1 - b0)
            sc.bend(ch, lerp(v0, v1, phase), beat, range_semitones)
            beat += step
    sc.bend(ch, points[-1][1], points[-1][0], range_semitones)


def autopan(
    sc: Score,
    ch: int,
    start: float,
    duration: float,
    lo: int = 18,
    hi: int = 110,
    period: float = 16.0,
    step: float = 0.5,
) -> None:
    beat = 0.0
    while beat <= duration + 1e-9:
        phase = math.sin(2.0 * math.pi * beat / period)
        value = int(round((lo + hi) * 0.5 + (hi - lo) * 0.5 * phase))
        sc.cc(ch, 10, value, start + beat)
        beat += step
    sc.cc(ch, 10, 64, start + duration)


def expression_pump(
    sc: Score,
    ch: int,
    start: float,
    duration: float,
    low: int = 66,
    high: int = 112,
    beat_step: float = 1.0,
) -> None:
    """Beat-synchronous CC11 dip/recovery: an authored sidechain-like pump."""
    beat = start
    while beat < start + duration - 1e-9:
        sc.cc(ch, 11, low, beat)
        sc.cc(ch, 11, high, beat + min(0.28, beat_step * 0.35))
        beat += beat_step


def arpeggio(
    sc: Score,
    ch: int,
    notes: list[int],
    start: float,
    duration: float,
    step: float,
    velocity: int,
    order: tuple[int, ...] = (0, 1, 2, 1, 3, 2, 1, 2),
    gate: float = 0.84,
) -> None:
    count = int(round(duration / step))
    for i in range(count):
        note = notes[order[i % len(order)] % len(notes)]
        accent = 10 if i % max(1, int(round(4.0 / step))) == 0 else 0
        sc.note(ch, note, start + i * step, step * gate, velocity + accent, jt=1, jv=2)


def pad(sc: Score, ch: int, notes: list[int], start: float, duration: float, velocity: int) -> None:
    for i, note in enumerate(notes):
        delay = i * 0.012
        sc.note(ch, note, start + delay, max(0.05, duration - delay), velocity - 2 * i, jt=1, jv=2)


def parse_midi(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path} is not a MIDI file")
    header_length, fmt, track_count, division = struct.unpack(">IHHH", data[4:14])
    pos = 8 + header_length
    notes = 0
    channels: set[int] = set()
    tempo_events = 0
    marker_events = 0
    ccs: dict[int, int] = {}
    programs: list[tuple[int, int, int]] = []
    bend_events = 0
    end_tick = 0
    tempos: list[tuple[int, int]] = []
    for _ in range(track_count):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("missing MIDI track chunk")
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        pos += 8
        end = pos + length
        current = 0
        running: int | None = None
        while pos < end:
            delta, pos = _read_vlq(data, pos)
            current += delta
            status = data[pos]
            if status < 0x80:
                if running is None:
                    raise ValueError("running status without status byte")
                status = running
            else:
                pos += 1
                if status < 0xF0:
                    running = status
            if status == 0xFF:
                kind = data[pos]
                pos += 1
                size, pos = _read_vlq(data, pos)
                payload = data[pos:pos + size]
                pos += size
                if kind == 0x51 and len(payload) == 3:
                    tempo_events += 1
                    tempos.append((current, int.from_bytes(payload, "big")))
                elif kind == 0x06:
                    marker_events += 1
                end_tick = max(end_tick, current)
            elif status in (0xF0, 0xF7):
                size, pos = _read_vlq(data, pos)
                pos += size
            else:
                kind = status & 0xF0
                ch = status & 0x0F
                channels.add(ch)
                if kind in (0xC0, 0xD0):
                    d1 = data[pos]
                    pos += 1
                    if kind == 0xC0:
                        programs.append((current, ch, d1))
                else:
                    d1, d2 = data[pos], data[pos + 1]
                    pos += 2
                    if kind == 0x90 and d2 > 0:
                        notes += 1
                    elif kind == 0xB0:
                        ccs[d1] = ccs.get(d1, 0) + 1
                    elif kind == 0xE0:
                        bend_events += 1
                end_tick = max(end_tick, current)
    tempos = tempos or [(0, 500_000)]
    seconds = _seconds_from_ticks(end_tick, tempos, division)
    return {
        "format": fmt,
        "tracks": track_count,
        "division": division,
        "notes": notes,
        "channels": sorted(channels),
        "tempo_events": tempo_events,
        "marker_events": marker_events,
        "cc_counts": ccs,
        "programs": programs,
        "bend_events": bend_events,
        "seconds": seconds,
    }


def _seconds_from_ticks(ticks: int, tempos: list[tuple[int, int]], division: int) -> float:
    tempos = sorted(tempos)
    total = 0.0
    cursor = 0
    mpq = tempos[0][1]
    for tempo_tick, next_mpq in tempos:
        if tempo_tick >= ticks:
            break
        total += (tempo_tick - cursor) * mpq / 1_000_000 / division
        cursor = tempo_tick
        mpq = next_mpq
    return total + (ticks - cursor) * mpq / 1_000_000 / division
