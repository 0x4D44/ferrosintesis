#!/usr/bin/env python3
"""Deterministic standard-library MIDI engine for *Atlas of Becoming*."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import math
import random
import struct

PPQ = 480
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"
BUILD_DIR = ALBUM_ROOT / "build"
WAV_DIR = BUILD_DIR / "wav"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def tick(beat: float) -> int:
    return max(0, int(round(beat * PPQ)))


def _vlq(n: int) -> bytes:
    n = max(0, int(n))
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    val = 0
    while True:
        b = data[pos]
        pos += 1
        val = (val << 7) | (b & 0x7F)
        if not (b & 0x80):
            return val, pos


def bend_raw(semis: float, range_semis: float = 2.0) -> int:
    return int(round(clamp(8192 + (semis / range_semis) * 8192, 0, 16383)))


def note_name(n: int) -> str:
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return f"{names[n % 12]}{n // 12 - 1}"


SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "harmonic": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "pent": [0, 3, 5, 7, 10],
    "whole": [0, 2, 4, 6, 8, 10],
    "chromatic": list(range(12)),
}


def pitch(root: int, mode: str, degree: int, octave: int = 0) -> int:
    scale = SCALES[mode]
    q, r = divmod(degree, len(scale))
    return root + 12 * (q + octave) + scale[r]


def chord(root: int, mode: str, degree: int, size: int = 3, octave: int = 0) -> list[int]:
    return [pitch(root, mode, degree + step * 2, octave) for step in range(size)]


@dataclass
class Feature:
    name: str
    ch: int
    start: float
    end: float
    programs: set[int] = field(default_factory=set)
    tier: str = "A"
    min_notes: int = 1
    ccs: dict[int, tuple[int, int]] = field(default_factory=dict)
    bend: tuple[float, float] | None = None
    aftertouch: tuple[int, int] | None = None
    monophonic: bool = False
    drum_kit: bool = False


@dataclass
class AudioCheck:
    name: str
    kind: str
    start: float
    end: float
    ref_start: float | None = None
    ref_end: float | None = None
    threshold: float = 1.0


@dataclass
class TrackSpec:
    number: int
    title: str
    filename: str
    seed: int
    tempo: float
    beats: float
    builder: object
    style: str
    duration_window: tuple[float, float]
    concept: str = ""
    min_notes: int = 300
    min_channels: int = 6
    min_markers: int = 4
    min_tempo_events: int = 2
    min_meter_events: int = 1
    tags: tuple[str, ...] = ()


class Score:
    """Event collector. Channel 9 is GM percussion."""

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
        self.features: list[Feature] = []
        self.audio_checks: list[AudioCheck] = []

    def channel(
        self,
        ch: int,
        name: str,
        program: int | None = 0,
        volume: int = 100,
        pan: int = 64,
        reverb: int = 50,
        chorus: int = 0,
        echo: int = 0,
        beat: float = 0.0,
    ) -> None:
        self.names[ch] = name
        self.events.setdefault(ch, [])
        if ch != 9 and program is not None:
            self.program(ch, program, beat)
        self.cc(ch, 7, volume, beat)
        self.cc(ch, 10, pan, beat)
        self.cc(ch, 91, reverb, beat)
        self.cc(ch, 93, chorus, beat)
        self.cc(ch, 94, echo, beat)

    def program(self, ch: int, prog: int, beat: float) -> None:
        self.events.setdefault(ch, []).append((tick(beat), 1, bytes([0xC0 | ch, prog & 0x7F])))

    def cc(self, ch: int, num: int, val: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (tick(beat), 2, bytes([0xB0 | ch, num & 0x7F, int(clamp(val, 0, 127))]))
        )

    def aftertouch(self, ch: int, val: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (tick(beat), 2, bytes([0xD0 | ch, int(clamp(val, 0, 127))]))
        )

    def bend(self, ch: int, semis: float, beat: float, range_semis: float = 2.0) -> None:
        raw = bend_raw(semis, range_semis)
        self.events.setdefault(ch, []).append(
            (tick(beat), 2, bytes([0xE0 | ch, raw & 0x7F, (raw >> 7) & 0x7F]))
        )

    def note(
        self,
        ch: int,
        p: int,
        beat: float,
        dur: float,
        vel: int,
        jt: int = 3,
        jv: int = 4,
    ) -> None:
        p = int(clamp(round(p), 0, 127))
        vel = int(clamp(round(vel + self.rng.randint(-jv, jv)), 1, 127))
        on = tick(beat)
        if jt and beat > 0.05:
            on = max(0, on + self.rng.randint(-jt, jt))
        off = max(on + PPQ // 32, tick(beat + max(0.03, dur)))
        ev = self.events.setdefault(ch, [])
        ev.append((on, 5, bytes([0x90 | ch, p, vel])))
        ev.append((off, 4, bytes([0x80 | ch, p, 0])))
        self.last_beat = max(self.last_beat, beat + dur)

    def hit(self, key: int, beat: float, vel: int, dur: float = 0.12) -> None:
        self.note(9, key, beat, dur, vel, jt=2, jv=5)

    def marker(self, beat: float, text: str) -> None:
        self.markers.append((beat, text))

    def timesig(self, beat: float, num: int, den: int) -> None:
        self.timesigs.append((beat, num, den))

    def tempo(self, beat: float, bpm: float) -> None:
        self.tempos.append((beat, bpm))

    def feature(self, feature: Feature) -> None:
        self.features.append(feature)

    def audio_check(self, check: AudioCheck) -> None:
        self.audio_checks.append(check)

    def reset_controls(self, ch: int, beat: float) -> None:
        self.bend(ch, 0.0, beat)
        for num, val in [(64, 0), (65, 0), (66, 0), (67, 0), (68, 0), (70, 0), (71, 0), (74, 127)]:
            self.cc(ch, num, val, beat)
        self.aftertouch(ch, 0, beat)
        self.cc(ch, 101, 127, beat)
        self.cc(ch, 100, 127, beat + 0.002)

    def rpn(self, ch: int, number: int, msb: int, beat: float, lsb: int = 0) -> None:
        base = tick(beat)
        vals = [(101, 0), (100, number), (6, msb), (38, lsb), (101, 127), (100, 127)]
        for i, (num, val) in enumerate(vals):
            self.events.setdefault(ch, []).append(
                (base + i, 2, bytes([0xB0 | ch, num & 0x7F, int(clamp(val, 0, 127))]))
            )

    def bend_range(self, ch: int, semis: int, beat: float) -> None:
        self.rpn(ch, 0, int(semis), beat)

    def fine_tune(self, ch: int, cents: float, beat: float) -> None:
        self.rpn(ch, 1, int(round(64 + cents * 64 / 100)), beat)

    def sustain(self, ch: int, start: float, end: float) -> None:
        self.cc(ch, 64, 127, start)
        self.cc(ch, 64, 0, end)

    def sostenuto(self, ch: int, start: float, end: float) -> None:
        self.cc(ch, 66, 127, start)
        self.cc(ch, 66, 0, end)

    def soft_pedal(self, ch: int, start: float, end: float) -> None:
        self.cc(ch, 67, 127, start)
        self.cc(ch, 67, 0, end)

    def portamento_on(self, ch: int, beat: float, time_cc: int = 72) -> None:
        self.cc(ch, 5, time_cc, beat)
        self.cc(ch, 65, 127, beat + 0.002)

    def portamento_off(self, ch: int, beat: float) -> None:
        self.cc(ch, 65, 0, beat)

    def seconds_at(self, beat: float) -> float:
        tempos = sorted(self.tempos)
        total = 0.0
        cursor = 0.0
        bpm = tempos[0][1] if tempos else 120.0
        for tb, tbpm in tempos:
            if tb >= beat:
                break
            total += (tb - cursor) * 60.0 / bpm
            cursor = tb
            bpm = tbpm
        return total + (beat - cursor) * 60.0 / bpm

    def duration_seconds(self) -> float:
        return self.seconds_at(self.last_beat)

    def _resolve_overlaps(self) -> None:
        for ch, ev in self.events.items():
            on_ticks: dict[int, list[int]] = {}
            off_idxs: dict[int, list[int]] = {}
            for i, (tk, _prio, data) in enumerate(ev):
                status = data[0] & 0xF0
                if status == 0x90 and data[2] > 0:
                    on_ticks.setdefault(data[1], []).append(tk)
                elif status == 0x80 or (status == 0x90 and data[2] == 0):
                    off_idxs.setdefault(data[1], []).append(i)
            for p, ons in on_ticks.items():
                idxs = off_idxs.get(p, [])
                if len(idxs) != len(ons):
                    continue
                ons.sort()
                idxs.sort(key=lambda i: ev[i][0])
                offs = [ev[i][0] for i in idxs]
                for k in range(len(ons) - 1):
                    if offs[k] > ons[k + 1]:
                        offs[k] = ons[k + 1]
                for i, tk in zip(idxs, offs):
                    if ev[i][0] != tk:
                        ev[i] = (tk, ev[i][1], ev[i][2])

    def to_bytes(self, title: str | None = None, comment: str = "") -> bytes:
        self._resolve_overlaps()
        end_tick = tick(self.last_beat) + 2 * PPQ
        title = title or self.title

        def meta(kind: int, payload: bytes) -> bytes:
            return bytes([0xFF, kind]) + _vlq(len(payload)) + payload

        cond: list[tuple[int, int, bytes]] = [(0, 0, meta(0x03, title.encode("ascii", "replace")))]
        if comment:
            cond.append((0, 0, meta(0x01, comment.encode("ascii", "replace"))))
        for beat, num, den in sorted(self.timesigs):
            cond.append((tick(beat), 1, meta(0x58, bytes([num, den.bit_length() - 1, 24, 8]))))
        for beat, bpm in sorted(self.tempos):
            mpq = int(round(60_000_000 / bpm))
            cond.append((tick(beat), 2, meta(0x51, mpq.to_bytes(3, "big"))))
        for beat, text in sorted(self.markers):
            cond.append((tick(beat), 3, meta(0x06, text.encode("ascii", "replace"))))
        for beat, text in sorted(self.lyrics):
            cond.append((tick(beat), 3, meta(0x05, text.encode("ascii", "replace"))))

        def chunk(events: list[tuple[int, int, bytes]], name: str | None) -> bytes:
            body = bytearray()
            if name is not None:
                body += _vlq(0) + meta(0x03, name.encode("ascii", "replace"))
            last = 0
            for tk, prio, data in sorted(events, key=lambda e: (e[0], e[1], e[2])):
                if tk < last:
                    raise ValueError("events are out of order")
                body += _vlq(tk - last) + data
                last = tk
            body += _vlq(max(0, end_tick - last)) + b"\xFF\x2F\x00"
            return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

        chunks = [chunk(cond, None)]
        for ch in sorted(self.events):
            chunks.append(chunk(self.events[ch], self.names.get(ch, f"ch{ch}")))
        return b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks)

    def write(self, path: Path, title: str | None = None, comment: str = "") -> bytes:
        data = self.to_bytes(title, comment)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data


def cc_curve(sc: Score, ch: int, num: int, points: list[tuple[float, int]], step: float = 0.5) -> None:
    pts = sorted(points)
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        b = b0
        while b < b1 - 1e-9:
            t = (b - b0) / max(1e-9, b1 - b0)
            sc.cc(ch, num, int(round(lerp(v0, v1, t))), b)
            b += step
    sc.cc(ch, num, pts[-1][1], pts[-1][0])


def at_curve(sc: Score, ch: int, points: list[tuple[float, int]], step: float = 0.5) -> None:
    pts = sorted(points)
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        b = b0
        while b < b1 - 1e-9:
            t = (b - b0) / max(1e-9, b1 - b0)
            sc.aftertouch(ch, int(round(lerp(v0, v1, t))), b)
            b += step
    sc.aftertouch(ch, pts[-1][1], pts[-1][0])


def bend_curve(
    sc: Score,
    ch: int,
    points: list[tuple[float, float]],
    step: float = 0.125,
    range_semis: float = 2.0,
) -> None:
    pts = sorted(points)
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        b = b0
        while b < b1 - 1e-9:
            t = (b - b0) / max(1e-9, b1 - b0)
            sc.bend(ch, lerp(v0, v1, t), b, range_semis=range_semis)
            b += step
    sc.bend(ch, pts[-1][1], pts[-1][0], range_semis=range_semis)


def wah(sc: Score, ch: int, start: float, dur: float, lo: int = 28, hi: int = 118, step: float = 0.25) -> None:
    b = 0.0
    while b <= dur + 1e-9:
        phase = math.sin(2.0 * math.pi * b / 2.0)
        sc.cc(ch, 74, int(round((lo + hi) / 2 + (hi - lo) / 2 * phase)), start + b)
        b += step


def autopan(sc: Score, ch: int, start: float, dur: float, lo: int = 28, hi: int = 100, period: float = 8.0) -> None:
    b = 0.0
    while b <= dur + 1e-9:
        phase = math.sin(2.0 * math.pi * b / period)
        sc.cc(ch, 10, int(round((lo + hi) / 2 + (hi - lo) / 2 * phase)), start + b)
        b += 0.5


def echo_throw(sc: Score, ch: int, beat: float, peak: int = 100, base: int = 18) -> None:
    cc_curve(sc, ch, 94, [(beat, peak), (beat + 2.0, base)], step=0.25)


def riff(
    sc: Score,
    ch: int,
    root: int,
    mode: str,
    degrees: list[int],
    start: float,
    step: float,
    vel0: int,
    vel1: int,
    reps: int = 1,
    dur_mul: float = 0.9,
    octave: int = 0,
) -> None:
    seq = degrees * reps
    for i, deg in enumerate(seq):
        t = start + i * step
        v = int(round(lerp(vel0, vel1, i / max(1, len(seq) - 1))))
        sc.note(ch, pitch(root, mode, deg, octave), t, step * dur_mul, v, jt=1, jv=2)


def arpeggio(
    sc: Score,
    ch: int,
    notes: list[int],
    start: float,
    beats: float,
    step: float,
    vel: int,
    gate: float = 1.1,
) -> None:
    count = int(beats / step)
    for i in range(count):
        sc.note(ch, notes[i % len(notes)], start + i * step, step * gate, vel + (10 if i % 8 == 0 else 0), jt=2)


def pad(sc: Score, ch: int, notes: list[int], start: float, dur: float, vel: int) -> None:
    for i, n in enumerate(notes):
        sc.note(ch, n, start + i * 0.015, dur - i * 0.015, vel - i * 2, jt=2, jv=2)


def drum_drive(sc: Score, start: float, bars: int, beat_unit: float = 4.0, energy: int = 92) -> None:
    for bar in range(bars):
        b = start + bar * beat_unit
        sc.hit(36, b, energy + 8)
        sc.hit(38, b + beat_unit / 2, energy + 4)
        sc.hit(42, b + beat_unit * 0.25, energy - 8)
        sc.hit(42, b + beat_unit * 0.75, energy - 6)
        if bar % 2 == 1:
            sc.hit(49, b + beat_unit - 0.25, energy + 10)
        for k in range(0, int(beat_unit * 2)):
            key = 46 if k % 4 == 3 else 42
            sc.hit(key, b + k * 0.5, energy - 16 + (6 if k % 4 == 0 else 0), dur=0.08)


def parse_midi(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path} is not a MIDI file")
    hdr_len, fmt, tracks, division = struct.unpack(">IHHH", data[4:14])
    pos = 8 + hdr_len
    note_ons = 0
    tempos: list[tuple[int, int]] = []
    end_tick = 0
    channels: set[int] = set()
    programs: list[tuple[int, int, int]] = []
    ccs: dict[int, int] = {}
    bends = 0
    aftertouch = 0
    for _ in range(tracks):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("missing track chunk")
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        pos += 8
        end = pos + length
        tk = 0
        running = None
        while pos < end:
            delta, pos = _read_vlq(data, pos)
            tk += delta
            status = data[pos]
            if status < 0x80:
                if running is None:
                    raise ValueError("running status without previous status")
                status = running
            else:
                pos += 1
                running = status if status < 0xF0 else running
            if status == 0xFF:
                kind = data[pos]
                pos += 1
                ln, pos = _read_vlq(data, pos)
                payload = data[pos:pos + ln]
                pos += ln
                if kind == 0x51 and len(payload) == 3:
                    tempos.append((tk, int.from_bytes(payload, "big")))
                elif kind == 0x2F:
                    end_tick = max(end_tick, tk)
            elif status in (0xF0, 0xF7):
                ln, pos = _read_vlq(data, pos)
                pos += ln
            else:
                hi = status & 0xF0
                ch = status & 0x0F
                channels.add(ch)
                if hi in (0xC0, 0xD0):
                    d1 = data[pos]
                    pos += 1
                    if hi == 0xC0:
                        programs.append((tk, ch, d1))
                    else:
                        aftertouch += 1
                else:
                    d1, d2 = data[pos], data[pos + 1]
                    pos += 2
                    if hi == 0x90 and d2 > 0:
                        note_ons += 1
                    elif hi == 0xB0:
                        ccs[d1] = ccs.get(d1, 0) + 1
                    elif hi == 0xE0:
                        bends += 1
                end_tick = max(end_tick, tk)
    tempos = tempos or [(0, 500000)]
    seconds = _seconds_from_ticks(end_tick, tempos, division)
    return {
        "format": fmt,
        "tracks": tracks,
        "division": division,
        "notes": note_ons,
        "channels": sorted(channels),
        "programs": programs,
        "cc_counts": ccs,
        "bend_events": bends,
        "aftertouch_events": aftertouch,
        "tempo_events": len(tempos),
        "duration_ticks": end_tick,
        "seconds": seconds,
    }


def _seconds_from_ticks(tk: int, tempos: list[tuple[int, int]], division: int) -> float:
    tempos = sorted(tempos)
    total = 0.0
    cursor = 0
    mpq = tempos[0][1]
    for tt, new_mpq in tempos:
        if tt >= tk:
            break
        total += (tt - cursor) * mpq / 1_000_000 / division
        cursor = tt
        mpq = new_mpq
    return total + (tk - cursor) * mpq / 1_000_000 / division


def write_json(path: Path, data: object) -> bytes:
    payload = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload
