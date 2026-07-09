from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import math
import random
import struct
import sys
from typing import Iterable


PPQ = 480
BEATS_PER_BAR = 4
PITCH_BEND_CENTER = 8192
ALBUM_TITLE = "The Spark"
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"
TRACKS_DIR = ALBUM_ROOT / "tracks"


NOTE_BASE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}

MODES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "aeolian_bright": [0, 2, 3, 5, 7, 8, 11],
}

DEGREES = {
    "i": 0,
    "bII": 1,
    "II": 2,
    "III": 3,
    "iv": 5,
    "IV": 5,
    "v": 7,
    "V": 7,
    "VI": 8,
    "VII": 10,
}

QUALITIES = {
    "min": [0, 3, 7],
    "min7": [0, 3, 7, 10],
    "min9": [0, 3, 7, 10, 14],
    "maj": [0, 4, 7],
    "maj7": [0, 4, 7, 11],
    "add9": [0, 4, 7, 14],
    "sus2": [0, 2, 7, 12],
    "sus4": [0, 5, 7, 10],
    "dim": [0, 3, 6, 9],
    "open5": [0, 7, 12],
}

KEY_SIGNATURES = {
    "C": (0, 0),
    "G": (1, 0),
    "D": (2, 0),
    "A": (3, 0),
    "E": (4, 0),
    "B": (5, 0),
    "F#": (6, 0),
    "F": (-1, 0),
    "Bb": (-2, 0),
    "Eb": (-3, 0),
    "Ab": (-4, 0),
    "Db": (-5, 0),
    "Gb": (-6, 0),
    "Am": (0, 1),
    "Em": (1, 1),
    "Bm": (2, 1),
    "F#m": (3, 1),
    "C#m": (4, 1),
    "G#m": (5, 1),
    "D#m": (6, 1),
    "Dm": (-1, 1),
    "Gm": (-2, 1),
    "Cm": (-3, 1),
    "Fm": (-4, 1),
    "Bbm": (-5, 1),
    "Ebm": (-6, 1),
}


def note_pc(name: str) -> int:
    return NOTE_BASE[name]


def slug(title: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in title).strip("_").replace("__", "_")


def beat_to_tick(beat: float) -> int:
    return int(round(beat * PPQ))


def bar_beat(bar: int, beat: float = 0.0) -> float:
    return bar * BEATS_PER_BAR + beat


def vlq(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative MIDI delta")
    buffer = value & 0x7F
    value >>= 7
    while value:
        buffer <<= 8
        buffer |= (value & 0x7F) | 0x80
        value >>= 7
    out = bytearray()
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(out)


@dataclass(order=True)
class Event:
    tick: int
    priority: int
    data: bytes = field(compare=False)


class MidiTrack:
    def __init__(self, name: str) -> None:
        self.name = name
        self.events: list[Event] = []
        self.meta_text(0, 0x03, name)

    def add(self, tick: int, data: bytes, priority: int = 10) -> None:
        self.events.append(Event(max(0, tick), priority, data))

    def meta(self, tick: int, meta_type: int, payload: bytes, priority: int = 0) -> None:
        self.add(tick, bytes([0xFF, meta_type]) + vlq(len(payload)) + payload, priority)

    def meta_text(self, tick: int, meta_type: int, text: str, priority: int = 0) -> None:
        self.meta(tick, meta_type, text.encode("utf-8"), priority)

    def program(self, channel: int, program: int) -> None:
        self.add(0, bytes([0xC0 | channel, program]), priority=1)

    def cc(self, channel: int, controller: int, value: int, beat: float) -> None:
        self.add(beat_to_tick(beat), bytes([0xB0 | channel, controller, max(0, min(127, value))]), priority=2)

    def pitch_bend(self, channel: int, value: int, beat: float) -> None:
        self.add(
            beat_to_tick(beat),
            bytes([0xE0 | channel, value & 0x7F, (value >> 7) & 0x7F]),
            priority=2,
        )

    def channel_pressure(self, channel: int, value: int, beat: float) -> None:
        self.add(beat_to_tick(beat), bytes([0xD0 | channel, max(0, min(127, value))]), priority=2)

    def note(
        self,
        channel: int,
        pitch: int,
        start: float,
        duration: float,
        velocity: int,
        end_tick: int,
        jitter: int = 0,
        rng: random.Random | None = None,
    ) -> None:
        start_tick = beat_to_tick(start)
        stop_tick = beat_to_tick(start + duration)
        if jitter and rng is not None:
            offset = rng.randint(-jitter, jitter)
            start_tick = max(0, start_tick + offset)
            stop_tick = max(start_tick + 1, stop_tick + offset + rng.randint(-jitter, jitter))
        stop_tick = min(stop_tick, end_tick)
        if start_tick >= stop_tick:
            return
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, velocity))
        self.add(start_tick, bytes([0x90 | channel, pitch, velocity]), priority=5)
        self.add(stop_tick, bytes([0x80 | channel, pitch, 0]), priority=4)

    def render(self, end_tick: int) -> bytes:
        events = sorted(self.events)
        body = bytearray()
        last = 0
        for event in events:
            if event.tick > end_tick:
                continue
            body += vlq(event.tick - last)
            body += event.data
            last = event.tick
        body += vlq(max(0, end_tick - last))
        body += b"\xFF\x2F\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + body


def set_pitch_bend_range(track: MidiTrack, channel: int, semitones: int, cents: int = 0, beat: float = 0) -> None:
    track.cc(channel, 101, 0, beat)
    track.cc(channel, 100, 0, beat)
    track.cc(channel, 6, max(0, min(127, semitones)), beat)
    track.cc(channel, 38, max(0, min(127, cents)), beat)
    track.cc(channel, 101, 127, beat)
    track.cc(channel, 100, 127, beat)


@dataclass(frozen=True)
class SongSpec:
    number: int
    title: str
    mood: str
    role: str
    key: str
    mode: str
    bars: int
    tempo_map: tuple[tuple[int, float], ...]
    progression: tuple[str, ...]
    intensity: tuple[tuple[int, float], ...]
    pulse: int
    melody_style: str
    energy: float
    percussion: bool = False
    celesta: bool = True
    low_pulse: bool = False
    low_string_floor: int = 36
    low_string_pan: int = 64

    @property
    def filename(self) -> str:
        return f"{self.number:02d} - {self.title}.mid"


SONGS = [
    SongSpec(
        1,
        "The Quiet Before Dawn",
        "quiet, still, expectant",
        "A room-temperature hush with soft piano harmonics and distant bowed strings.",
        "E",
        "minor",
        72,
        ((0, 56), (16, 60), (40, 58), (60, 54)),
        ("i:min9", "VII:sus4", "III:add9", "VI:maj7", "i:min9", "iv:min7", "VII:sus4", "i:open5"),
        ((0, 0.18), (16, 0.28), (40, 0.40), (60, 0.24), (72, 0.16)),
        4,
        "falling",
        0.24,
        percussion=False,
        celesta=True,
        low_pulse=False,
    ),
    SongSpec(
        2,
        "Windowlit Water",
        "quiet, contemplative, slow-building",
        "Paper reflections over soft piano, then a patient pulse of strings beneath.",
        "D",
        "dorian",
        84,
        ((0, 66), (24, 70), (52, 74), (74, 66)),
        ("i:min7", "VII:maj", "VI:maj7", "iv:min7", "i:min7", "III:add9", "VII:sus4", "V:sus4"),
        ((0, 0.22), (24, 0.36), (52, 0.54), (74, 0.34), (84, 0.24)),
        6,
        "remembering",
        0.44,
        percussion=False,
        low_pulse=False,
    ),
    SongSpec(
        3,
        "Letters in Winter Ink",
        "tender, wounded, and restrained",
        "A three-note lament repeated through glassy chords and long cello sighs.",
        "G",
        "minor",
        94,
        ((0, 58), (24, 62), (56, 66), (80, 58)),
        ("i:min9", "iv:min7", "VI:maj7", "III:add9", "bII:maj7", "VI:maj7", "iv:min7", "V:sus4"),
        ((0, 0.20), (24, 0.40), (56, 0.66), (80, 0.30), (94, 0.20)),
        5,
        "lament",
        0.28,
    ),
    SongSpec(
        4,
        "First Alarm",
        "urgent, tense, investigative",
        "A nervous pulse rises under staccato bass and fractured piano runs.",
        "C",
        "harmonic_minor",
        100,
        ((0, 92), (24, 104), (56, 118), (84, 102)),
        ("i:min", "V:sus4", "VI:maj7", "iv:min7", "i:min", "VII:maj", "V:sus4", "i:open5"),
        ((0, 0.40), (24, 0.62), (56, 0.88), (84, 0.58), (100, 0.36)),
        13,
        "angular",
        0.74,
        percussion=True,
        low_pulse=True,
    ),
    SongSpec(
        5,
        "A City of Small Fires",
        "restless, urban, intimate",
        "Piano and strings circle in an anxious dance across muted harmonies.",
        "F",
        "minor",
        88,
        ((0, 72), (24, 78), (52, 86), (80, 80)),
        ("i:min7", "III:maj7", "VII:sus4", "VI:maj7", "iv:min7", "i:min7", "bII:maj7", "V:sus4"),
        ((0, 0.30), (24, 0.50), (52, 0.70), (80, 0.46), (88, 0.30)),
        10,
        "angular",
        0.34,
        percussion=True,
        low_pulse=True,
    ),
    SongSpec(
        6,
        "Mercy of the Rail Line",
        "propulsive, searching, relentless",
        "Low percussion and repeated harmonic cells carry the album into a kinetic state.",
        "E",
        "phrygian",
        110,
        ((0, 98), (24, 108), (56, 122), (92, 112)),
        ("i:min7", "bII:maj7", "VII:maj", "VI:maj7", "i:min7", "iv:min7", "bII:maj7", "V:sus4"),
        ((0, 0.46), (24, 0.74), (56, 0.98), (92, 0.64), (110, 0.42)),
        15,
        "urgent",
        0.88,
        percussion=True,
        low_pulse=True,
    ),
    SongSpec(
        7,
        "Midnight Engine",
        "luminous, patient, turning inward",
        "A bright center where the pulse stays calm and the harmony opens.",
        "D",
        "minor",
        88,
        ((0, 78), (20, 84), (44, 92), (64, 102), (80, 96)),
        ("i:min9", "VI:maj7", "III:add9", "VII:sus4", "i:min9", "IV:add9", "VII:sus4", "VI:maj7"),
        ((0, 0.28), (20, 0.44), (44, 0.56), (64, 0.70), (80, 0.48), (88, 0.30)),
        7,
        "falling",
        0.52,
        percussion=True,
        low_pulse=True,
    ),
    SongSpec(
        8,
        "A Door You Didn't Hear Close",
        "quiet but dramatic, haunted",
        "The momentum slips backward, then gathers grief through deep cello echoes.",
        "A",
        "minor",
        102,
        ((0, 68), (28, 64), (58, 60), (84, 56)),
        ("i:min9", "VI:maj7", "III:add9", "bII:maj7", "iv:min7", "VI:maj7", "V:sus4", "i:open5"),
        ((0, 0.24), (28, 0.36), (58, 0.40), (84, 0.30), (102, 0.22)),
        6,
        "lament",
        0.42,
        percussion=False,
        low_pulse=True,
    ),
    SongSpec(
        9,
        "The Big Arc Begins",
        "urgent, sweeping, resilient",
        "The album re-accelerates with a wide pulse and more open harmony.",
        "F",
        "dorian",
        112,
        ((0, 106), (28, 118), (64, 132), (96, 120)),
        ("i:min7", "IV:add9", "VII:sus4", "III:maj7", "i:min7", "VI:maj7", "IV:add9", "V:sus4"),
        ((0, 0.44), (28, 0.66), (64, 0.92), (96, 0.60), (112, 0.36)),
        14,
        "rising",
        0.88,
        percussion=True,
        low_pulse=True,
    ),
    SongSpec(
        10,
        "Lightning Over Stone",
        "fast, brilliant, triumphant",
        "A large emotional crest: percussion, cello, and celesta ignite the mid-album peak.",
        "E",
        "phrygian",
        120,
        ((0, 110), (24, 124), (56, 150), (92, 138), (108, 128)),
        ("i:min7", "bII:maj7", "VII:maj", "VI:maj7", "i:min7", "iv:min", "bII:maj7", "V:sus4"),
        ((0, 0.50), (24, 0.78), (56, 1.00), (92, 0.86), (108, 0.65), (120, 0.42)),
        16,
        "urgent",
        0.99,
        low_pulse=True,
        percussion=True,
    ),
    SongSpec(
        11,
        "Chamber of Witness",
        "massive, cathartic, expansive",
        "A final expansion before quiet; the emotional weight lands with layered strings and tolling piano.",
        "D",
        "minor",
        120,
        ((0, 84), (24, 96), (56, 112), (92, 104), (108, 92)),
        ("i:min9", "bII:maj7", "VI:maj7", "iv:min7", "i:min7", "VII:sus4", "VI:maj7", "V:sus4"),
        ((0, 0.38), (24, 0.66), (56, 0.95), (92, 0.78), (108, 0.50), (120, 0.28)),
        10,
        "lament",
        0.95,
        percussion=False,
        celesta=False,
        low_pulse=True,
    ),
    SongSpec(
        12,
        "After the Spark, You Return",
        "quiet, reflective, unresolved",
        "A calm close with gentle fragments returning, now carrying the scar of the journey.",
        "G",
        "minor",
        88,
        ((0, 58), (24, 56), (56, 60), (72, 52)),
        ("i:min9", "VI:maj7", "III:add9", "VII:sus4", "i:min9", "iv:min7", "VI:maj7", "i:open5"),
        ((0, 0.20), (24, 0.34), (56, 0.38), (72, 0.22), (88, 0.14)),
        4,
        "falling",
        0.18,
        percussion=False,
        low_pulse=False,
    ),
]


def microseconds_per_quarter(bpm: float) -> int:
    return int(round(60_000_000 / bpm))


def spec_duration_seconds(spec: SongSpec) -> float:
    total = 0.0
    for index, (start_bar, bpm) in enumerate(spec.tempo_map):
        end_bar = spec.tempo_map[index + 1][0] if index + 1 < len(spec.tempo_map) else spec.bars
        total += (end_bar - start_bar) * BEATS_PER_BAR * 60 / bpm
    return total


def interpolate(points: tuple[tuple[int, float], ...], bar: int) -> float:
    if bar <= points[0][0]:
        return points[0][1]
    for index in range(len(points) - 1):
        left_bar, left_value = points[index]
        right_bar, right_value = points[index + 1]
        if left_bar <= bar <= right_bar:
            ratio = (bar - left_bar) / max(1, right_bar - left_bar)
            return left_value + (right_value - left_value) * ratio
    return points[-1][1]


def scale_pitch(spec: SongSpec, degree: int, octave: int, accidental: int = 0) -> int:
    scale = MODES[spec.mode]
    octave_shift, index = divmod(degree, len(scale))
    return 12 * (octave + octave_shift + 1) + note_pc(spec.key) + scale[index] + accidental


def chord_tones(spec: SongSpec, chord_token: str) -> dict[str, list[int] | int | str]:
    degree_name, quality = chord_token.split(":")
    root_pc = (note_pc(spec.key) + DEGREES[degree_name]) % 12
    intervals = QUALITIES[quality]
    bass = 12 * (1 + 1) + root_pc
    low = [12 * (2 + 1) + root_pc + interval for interval in intervals[:3]]
    pad = [12 * (3 + 1) + root_pc + interval for interval in intervals[:4]]
    arp = [12 * (4 + 1) + root_pc + interval for interval in intervals]
    arp += [pitch + 12 for pitch in arp[: max(2, len(arp) // 2)]]
    return {"name": chord_token, "bass": bass, "low": low, "pad": pad, "arp": sorted(arp)}


def setup_expression(
    track: MidiTrack, channel: int, spec: SongSpec, volume: int, pan: int, apply_modulation: bool = True
) -> None:
    track.cc(channel, 7, volume, 0)
    track.cc(channel, 10, pan, 0)
    track.cc(channel, 91, 58, 0)
    for bar in range(spec.bars):
        intensity = interpolate(spec.intensity, bar)
        wave = math.sin((bar / 7.5) * math.pi) * 9
        value = int(42 + intensity * 52 + wave)
        track.cc(channel, 11, max(24, min(110, value)), bar_beat(bar))
        if apply_modulation:
            modulation = int(24 + intensity * 64 + (math.sin(bar * 0.42) * 10))
            resonance = int(18 + intensity * 58 + (math.cos(bar * 0.31) * 12))
            brightness = int(28 + intensity * 56 + (math.sin((bar + 0.9) * 0.37) * 9))
            track.cc(channel, 1, max(0, min(127, modulation)), bar_beat(bar))
            track.cc(channel, 71, max(6, min(127, resonance)), bar_beat(bar))
            track.cc(channel, 74, max(16, min(126, brightness)), bar_beat(bar))
            if bar % 4 == 0:
                track.channel_pressure(channel, max(22, min(96, int(34 + intensity * 56))), bar_beat(bar))
        if bar % 2 == 0:
            track.cc(channel, 11, max(24, min(112, value + 8)), bar_beat(bar, 2.0))


def apply_subtle_pitch_bend(track: MidiTrack, channel: int, spec: SongSpec, bar: int, phase: float = 0.0, width: int = 176) -> None:
    intensity = interpolate(spec.intensity, bar)
    wave = math.sin((bar / 5.5) + phase) * width * (0.25 + 0.75 * intensity)
    track.pitch_bend(channel, int(PITCH_BEND_CENTER + wave), bar_beat(bar))


def low_string_pitch(spec: SongSpec, bass: int) -> int:
    pitch = int(bass) - 12
    while pitch < spec.low_string_floor:
        pitch += 12
    return pitch


def add_piano(track: MidiTrack, spec: SongSpec, rng: random.Random, end_tick: int) -> None:
    track.program(0, 0)
    set_pitch_bend_range(track, 0, 2, 0, 0)
    setup_expression(track, 0, spec, 90, 54)
    for bar in range(spec.bars):
        apply_subtle_pitch_bend(track, 0, spec, bar, phase=0.12, width=196)
        intensity = interpolate(spec.intensity, bar)
        chord = chord_tones(spec, spec.progression[bar % len(spec.progression)])
        start = bar_beat(bar)
        coda = bar >= spec.bars - 8
        density = spec.pulse
        if bar < 8:
            density = max(2, density // 2)
        if coda:
            density = max(2, density // 3)
        if spec.melody_style == "lament" and density > 6 and bar % 2 == 1:
            density = max(4, density - 2)

        sustain_end = 1.85 if density >= 12 else 3.86
        track.cc(0, 64, 95 if density < 12 else 55, start)
        track.cc(0, 64, 0, start + sustain_end)

        bass_vel = int(31 + intensity * 39 + spec.energy * 10)
        track.note(0, int(chord["bass"]), start, 3.55 if not coda else 7.2, bass_vel, end_tick, jitter=4, rng=rng)
        if density >= 12 or bar % 2 == 0:
            track.note(0, int(chord["bass"]) + 12, start + 2.0, 1.35, bass_vel - 8, end_tick, jitter=4, rng=rng)

        arp = list(chord["arp"])
        step_width = BEATS_PER_BAR / density
        note_len = min(0.54, max(0.16, step_width * 0.78))
        for step in range(density):
            if bar < 3 and step not in (0, density // 2):
                continue
            beat = step * step_width
            accent = 12 if step % max(1, density // 4) == 0 else 0
            pitch = arp[(step + bar) % len(arp)]
            if spec.melody_style in ("urgent", "angular") and step % 8 in (5, 6, 7):
                pitch += 12
            if spec.melody_style == "falling" and step > density * 0.65:
                pitch -= 12
            shimmer = math.sin((bar * 0.9 + step) * 1.3) * 6
            velocity = int(30 + intensity * 45 + spec.energy * 18 + accent + shimmer)
            track.note(0, pitch, start + beat, note_len, velocity, end_tick, jitter=5, rng=rng)

        if intensity > 0.68 and bar % 4 in (2, 3):
            high = max(arp) + (12 if spec.energy > 0.7 else 0)
            track.note(0, high, start + 3.0, 0.72, int(42 + intensity * 44), end_tick, jitter=3, rng=rng)


MOTIFS = {
    "falling": [(5, 0.0, 0.80), (4, 0.92, 0.44), (2, 1.52, 0.78), (1, 2.48, 0.46), (0, 3.05, 0.84)],
    "urgent": [(0, 0.0, 0.42), (2, 0.5, 0.34), (3, 0.92, 0.36), (5, 1.34, 0.40), (6, 2.0, 0.46), (5, 2.58, 0.36), (3, 3.08, 0.48)],
    "lament": [(4, 0.0, 1.12), (3, 1.36, 0.52), (1, 2.02, 0.82), (0, 3.02, 0.86)],
    "remembering": [(2, 0.0, 0.92), (4, 1.16, 0.56), (5, 1.92, 0.78), (3, 3.00, 0.72)],
    "angular": [(0, 0.0, 0.46), (4, 0.62, 0.38), (1, 1.18, 0.42), (5, 2.0, 0.50), (3, 2.78, 0.46)],
    "rising": [(0, 0.0, 0.46), (1, 0.58, 0.36), (3, 1.04, 0.42), (5, 1.72, 0.56), (7, 2.56, 0.80)],
}


def add_phrase(
    track: MidiTrack,
    channel: int,
    spec: SongSpec,
    rng: random.Random,
    end_tick: int,
    bar: int,
    phrase_index: int,
    octave: int,
    velocity_offset: int,
) -> None:
    motif = MOTIFS[spec.melody_style]
    intensity = interpolate(spec.intensity, bar)
    for step_index, (degree, offset, duration) in enumerate(motif):
        accidental = -1 if spec.melody_style == "lament" and step_index == len(motif) - 1 and phrase_index % 2 else 0
        pitch = scale_pitch(spec, degree + phrase_index % 3, octave, accidental)
        if spec.melody_style == "falling" and phrase_index % 4 == 3:
            pitch -= 12
        velocity = int(42 + intensity * 42 + velocity_offset)
        track.note(channel, pitch, bar_beat(bar, offset), duration, velocity, end_tick, jitter=7, rng=rng)


def add_strings(
    cello: MidiTrack,
    viola: MidiTrack,
    violin: MidiTrack,
    ensemble: MidiTrack,
    basses: MidiTrack,
    spec: SongSpec,
    rng: random.Random,
    end_tick: int,
) -> None:
    cello.program(1, 42)
    viola.program(2, 41)
    violin.program(3, 40)
    ensemble.program(4, 48)
    basses.program(5, 43)
    set_pitch_bend_range(cello, 1, 2, 0, 0)
    set_pitch_bend_range(viola, 2, 2, 0, 0)
    set_pitch_bend_range(violin, 3, 2, 0, 0)
    set_pitch_bend_range(ensemble, 4, 2, 0, 0)
    set_pitch_bend_range(basses, 5, 2, 0, 0)
    setup_expression(cello, 1, spec, 78, 42)
    setup_expression(viola, 2, spec, 70, 62)
    setup_expression(violin, 3, spec, 70, 78)
    setup_expression(ensemble, 4, spec, 62, 58)
    setup_expression(basses, 5, spec, 72, spec.low_string_pan)

    for bar in range(4, spec.bars):
        apply_subtle_pitch_bend(cello, 1, spec, bar, phase=0.2, width=190)
        apply_subtle_pitch_bend(viola, 2, spec, bar, phase=0.5, width=130)
        apply_subtle_pitch_bend(violin, 3, spec, bar, phase=0.8, width=160)
        apply_subtle_pitch_bend(basses, 5, spec, bar, phase=1.4, width=82)
        if bar % 2 == 0:
            apply_subtle_pitch_bend(ensemble, 4, spec, bar, phase=1.1, width=98)
        intensity = interpolate(spec.intensity, bar)
        chord = chord_tones(spec, spec.progression[bar % len(spec.progression)])
        bass_pitch = low_string_pitch(spec, int(chord["bass"]))
        if spec.low_pulse and intensity > 0.58:
            for beat in (0.0, 1.5, 2.0, 3.5):
                basses.note(5, bass_pitch, bar_beat(bar, beat), 0.72, int(26 + intensity * 42), end_tick, jitter=5, rng=rng)
        elif bar % 2 == 0:
            basses.note(5, bass_pitch, bar_beat(bar), 7.5, int(24 + intensity * 34), end_tick, jitter=7, rng=rng)

        if bar % 2 == 0:
            pad = list(chord["pad"])
            duration = 7.55
            base_velocity = int(25 + intensity * 42)
            for index, pitch in enumerate(pad[:4]):
                ensemble.note(4, pitch, bar_beat(bar, 0.16 * index), duration - 0.16 * index, base_velocity + index * 3, end_tick, jitter=8, rng=rng)
        if intensity > 0.62 and bar % 4 in (1, 3):
            viola.note(2, list(chord["pad"])[2] + 12, bar_beat(bar, 1.0), 2.55, int(34 + intensity * 42), end_tick, jitter=6, rng=rng)
        if intensity > 0.78 and bar % 2 == 1:
            violin.note(3, list(chord["pad"])[-1] + 12, bar_beat(bar, 2.0), 1.62, int(42 + intensity * 42), end_tick, jitter=5, rng=rng)

    phrase_bars = range(8, max(9, spec.bars - 10), 4)
    for phrase_index, bar in enumerate(phrase_bars):
        position = bar / spec.bars
        if position < 0.34:
            add_phrase(cello, 1, spec, rng, end_tick, bar, phrase_index, 3, -3)
        elif position < 0.68:
            add_phrase(violin, 3, spec, rng, end_tick, bar, phrase_index, 4, 4)
        else:
            add_phrase(viola, 2, spec, rng, end_tick, bar, phrase_index, 3, -5)
            if interpolate(spec.intensity, bar) > 0.62:
                add_phrase(cello, 1, spec, rng, end_tick, bar, phrase_index + 1, 3, -8)

    final_chord = chord_tones(spec, spec.progression[-1])
    final_bar = max(0, spec.bars - 4)
    for index, pitch in enumerate(list(final_chord["pad"])[:4]):
        ensemble.note(4, pitch, bar_beat(final_bar, index * 0.24), 15.3 - index * 0.24, 25 + index * 4, end_tick, jitter=2, rng=rng)
    cello.note(1, int(final_chord["bass"]) + 12, bar_beat(final_bar), 15.2, 34, end_tick, jitter=2, rng=rng)
    basses.note(5, low_string_pitch(spec, int(final_chord["bass"])), bar_beat(final_bar), 15.2, 28, end_tick, jitter=2, rng=rng)


def add_celesta(track: MidiTrack, spec: SongSpec, rng: random.Random, end_tick: int) -> None:
    track.program(6, 8)
    set_pitch_bend_range(track, 6, 2, 0, 0)
    setup_expression(track, 6, spec, 44, 86)
    for bar in range(0, spec.bars, 8):
        apply_subtle_pitch_bend(track, 6, spec, bar, phase=0.03, width=94)
    if not spec.celesta:
        return
    candidate_bars = list(range(max(8, spec.bars // 3), spec.bars - 6, 6))
    if spec.energy < 0.30:
        candidate_bars = list(range(12, spec.bars - 8, 8))
    for phrase_index, bar in enumerate(candidate_bars):
        apply_subtle_pitch_bend(track, 6, spec, bar, phase=0.15, width=94)
        chord = chord_tones(spec, spec.progression[bar % len(spec.progression)])
        arp = list(chord["arp"])
        intensity = interpolate(spec.intensity, bar)
        for index, pitch in enumerate((arp[1] + 12, arp[3 % len(arp)] + 12, arp[-1])):
            velocity = int(20 + intensity * 24 - index * 2)
            track.note(6, pitch, bar_beat(bar, 0.5 + index * 1.0), 1.8, velocity, end_tick, jitter=4, rng=rng)
        if phrase_index % 3 == 2:
            track.note(6, max(arp) + 12, bar_beat(bar + 1, 3.0), 1.6, int(24 + intensity * 18), end_tick, jitter=3, rng=rng)


def add_percussion(track: MidiTrack, spec: SongSpec, rng: random.Random, end_tick: int) -> None:
    if not spec.percussion:
        return
    setup_expression(track, 9, spec, 64, 54, apply_modulation=False)
    for bar in range(8, spec.bars - 4):
        intensity = interpolate(spec.intensity, bar)
        if intensity < 0.46 and bar % 4:
            continue
        strong = int(30 + intensity * 58)
        track.note(9, 36, bar_beat(bar), 0.20, strong, end_tick, jitter=2, rng=rng)
        if spec.energy > 0.75 or bar % 2 == 0:
            track.note(9, 41, bar_beat(bar, 2.0), 0.18, strong - 8, end_tick, jitter=2, rng=rng)
        if intensity > 0.82 and bar % 8 == 0:
            track.note(9, 49, bar_beat(bar), 1.2, min(100, strong + 10), end_tick, jitter=2, rng=rng)


def conductor_track(spec: SongSpec, end_tick: int) -> MidiTrack:
    track = MidiTrack("Conductor")
    track.meta_text(0, 0x01, f"{ALBUM_TITLE} - {spec.number:02d}. {spec.title}")
    track.meta_text(0, 0x01, f"Mood: {spec.mood}")
    track.meta(0, 0x58, bytes([4, 2, 24, 8]))
    key_name = f"{spec.key}m" if "minor" in spec.mode or spec.mode in ("dorian", "phrygian") else spec.key
    sharps, minor = KEY_SIGNATURES.get(key_name, (0, 1))
    track.meta(0, 0x59, bytes([(sharps + 256) % 256, minor]))
    for bar, bpm in spec.tempo_map:
        track.meta(beat_to_tick(bar_beat(bar)), 0x51, microseconds_per_quarter(bpm).to_bytes(3, "big"))
        track.meta_text(beat_to_tick(bar_beat(bar)), 0x06, f"bar {bar + 1}: {bpm:g} bpm")
    track.meta_text(0, 0x06, "opening")
    track.meta_text(beat_to_tick(bar_beat(spec.bars // 3)), 0x06, "development")
    track.meta_text(beat_to_tick(bar_beat((spec.bars * 2) // 3)), 0x06, "turn")
    track.meta_text(beat_to_tick(bar_beat(max(0, spec.bars - 8))), 0x06, "coda")
    track.meta(end_tick, 0x01, b"end", priority=99)
    return track


def build_song(spec: SongSpec) -> list[MidiTrack]:
    if spec.tempo_map[0][0] != 0:
        raise ValueError(f"{spec.title}: tempo map must start at bar 0")
    rng = random.Random(20260624 + spec.number * 101)
    end_tick = beat_to_tick(spec.bars * BEATS_PER_BAR)
    tracks = [
        conductor_track(spec, end_tick),
        MidiTrack("Piano"),
        MidiTrack("Cello"),
        MidiTrack("Viola"),
        MidiTrack("Violin"),
        MidiTrack("String ensemble"),
        MidiTrack("Low strings"),
        MidiTrack("Celesta echoes"),
    ]
    if spec.percussion:
        tracks.append(MidiTrack("Low percussion"))

    add_piano(tracks[1], spec, rng, end_tick)
    add_strings(tracks[2], tracks[3], tracks[4], tracks[5], tracks[6], spec, rng, end_tick)
    add_celesta(tracks[7], spec, rng, end_tick)
    if spec.percussion:
        add_percussion(tracks[8], spec, rng, end_tick)

    for track in tracks[1:]:
        track.meta(end_tick, 0x01, b"end", priority=99)
    return tracks


def write_midi(path: Path, tracks: list[MidiTrack], bars: int) -> None:
    end_tick = beat_to_tick(bars * BEATS_PER_BAR)
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    path.write_bytes(header + b"".join(track.render(end_tick) for track in tracks))


def write_album_notes(manifest: dict[str, object]) -> None:
    lines = [
        f"# {ALBUM_TITLE}",
        "",
        "Original cinematic-minimalist MIDI album for piano, strings, celesta, and sparse low percussion.",
        "The album is an emotional journey through rapid motion, slow grief, kinetic pressure, introspection, and tragedy.",
        "",
        "This is original material using broad film-music and contemporary-classical vocabulary; it is not a direct imitation of any living composer or existing score.",
        "",
        "## Tracklist",
        "",
    ]
    for track in manifest["tracks"]:  # type: ignore[index]
        lines.append(
            f"{track['number']:02d}. {track['title']} - {track['duration_seconds']:.1f}s - {track['mood']}"
        )
        lines.append(f"    - File: `{track['file']}`")
        lines.append(f"    - Role: {track['role']}")
    lines += [
        "",
        "Regenerate the album from this directory with:",
        "",
        "```powershell",
        "python .\\build.py",
        "```",
        "",
        "Verify the generated MIDI files with:",
        "",
        "```powershell",
        "python .\\build.py --verify",
        "```",
        "",
    ]
    (ALBUM_ROOT / "ALBUM.md").write_text("\n".join(lines), encoding="utf-8")


def generate_track(number: int) -> tuple[Path, int]:
    MIDI_DIR.mkdir(exist_ok=True)
    spec = next((song for song in SONGS if song.number == number), None)
    if spec is None:
        raise ValueError(f"unknown track number: {number}")
    path = MIDI_DIR / spec.filename
    tracks = build_song(spec)
    write_midi(path, tracks, spec.bars)
    print(f"{spec.number:02d}. {spec.title}: {spec_duration_seconds(spec):.1f}s -> {path.name}")
    return path, len(tracks)


def generate_album() -> None:
    MIDI_DIR.mkdir(exist_ok=True)
    TRACKS_DIR.mkdir(exist_ok=True)
    manifest_tracks = []
    for spec in SONGS:
        _path, midi_track_count = generate_track(spec.number)
        manifest_tracks.append(
            {
                "number": spec.number,
                "title": spec.title,
                "file": f"midi/{spec.filename}",
                "mood": spec.mood,
                "role": spec.role,
                "key": spec.key,
                "mode": spec.mode,
                "bars": spec.bars,
                "tempo_map": [{"bar": bar, "bpm": bpm} for bar, bpm in spec.tempo_map],
                "duration_seconds": round(spec_duration_seconds(spec), 3),
                "duration_minutes": round(spec_duration_seconds(spec) / 60, 3),
                "midi_tracks": midi_track_count,
            }
        )
    manifest = {
        "album": ALBUM_TITLE,
        "track_count": len(SONGS),
        "total_duration_seconds": round(sum(spec_duration_seconds(spec) for spec in SONGS), 3),
        "total_duration_minutes": round(sum(spec_duration_seconds(spec) for spec in SONGS) / 60, 3),
        "tracks": manifest_tracks,
    }
    (ALBUM_ROOT / "album_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_album_notes(manifest)
    print(f"Total duration: {manifest['total_duration_minutes']:.2f} minutes")


def read_vlq(buf: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = buf[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, pos


def parse_midi(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path.name}: missing MThd header")
    header_len = int.from_bytes(data[4:8], "big")
    fmt = int.from_bytes(data[8:10], "big")
    track_count = int.from_bytes(data[10:12], "big")
    division = int.from_bytes(data[12:14], "big")
    pos = 8 + header_len
    tempos: list[tuple[int, int]] = []
    names: list[str] = []
    note_on = 0
    track_metrics: list[dict[str, object]] = []
    max_tick = 0
    for track_index in range(track_count):
        if data[pos : pos + 4] != b"MTrk":
            raise ValueError(f"{path.name}: missing MTrk at track {track_index}")
        size = int.from_bytes(data[pos + 4 : pos + 8], "big")
        pos += 8
        end = pos + size
        tick = 0
        running: int | None = None
        name = f"track {track_index + 1}"
        cc_counts: dict[int, int] = {}
        pitch_bend_events = 0
        channel_pressure_events = 0
        track_note_on = 0
        while pos < end:
            delta, pos = read_vlq(data, pos)
            tick += delta
            status = data[pos]
            if status >= 0x80:
                pos += 1
                if status < 0xF0:
                    running = status
            else:
                if running is None:
                    raise ValueError(f"{path.name}: running status without prior status")
                status = running
            if status == 0xFF:
                meta_type = data[pos]
                pos += 1
                length, pos = read_vlq(data, pos)
                payload = data[pos : pos + length]
                pos += length
                if meta_type == 0x03:
                    name = payload.decode("utf-8", errors="replace")
                elif meta_type == 0x51:
                    tempos.append((tick, int.from_bytes(payload, "big")))
            elif status in (0xF0, 0xF7):
                length, pos = read_vlq(data, pos)
                pos += length
            else:
                kind = status & 0xF0
                payload_length = 1 if kind in (0xC0, 0xD0) else 2
                payload = data[pos : pos + payload_length]
                pos += payload_length
                if kind == 0x90 and len(payload) == 2 and payload[1] > 0:
                    note_on += 1
                    track_note_on += 1
                elif kind == 0xB0 and len(payload) == 2:
                    controller = payload[0]
                    cc_counts[controller] = cc_counts.get(controller, 0) + 1
                elif kind == 0xE0:
                    pitch_bend_events += 1
                elif kind == 0xD0:
                    channel_pressure_events += 1
            max_tick = max(max_tick, tick)
        names.append(name)
        track_metrics.append(
            {
                "name": name,
                "cc_counts": cc_counts,
                "pitch_bend_events": pitch_bend_events,
                "channel_pressure_events": channel_pressure_events,
                "note_on_events": track_note_on,
            }
        )
    if pos != len(data):
        raise ValueError(f"{path.name}: trailing bytes after final track")
    if not tempos:
        raise ValueError(f"{path.name}: no tempo events")
    tempos.sort()
    seconds = 0.0
    for index, (tick, mpq) in enumerate(tempos):
        next_tick = tempos[index + 1][0] if index + 1 < len(tempos) else max_tick
        seconds += (next_tick - tick) / division * (mpq / 1_000_000)
    return {
        "format": fmt,
        "track_count": track_count,
        "division": division,
        "names": names,
        "tempo_events": len(tempos),
        "note_on_events": note_on,
        "tracks": track_metrics,
        "max_tick": max_tick,
        "duration_seconds": seconds,
    }


def verify_album() -> None:
    manifest_path = ALBUM_ROOT / "album_manifest.json"
    if not manifest_path.exists():
        raise SystemExit("album_manifest.json does not exist; run build.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    midi_files = sorted(MIDI_DIR.glob("[0-9][0-9] - *.mid"))
    if len(midi_files) != 12:
        errors.append(f"expected 12 MIDI files, found {len(midi_files)}")
    if manifest.get("track_count") != 12:
        errors.append(f"manifest track_count is {manifest.get('track_count')}, expected 12")
    total_seconds = 0.0
    for spec in SONGS:
        path = MIDI_DIR / spec.filename
        if not path.exists():
            errors.append(f"missing {spec.filename}")
            continue
        info = parse_midi(path)
        duration = float(info["duration_seconds"])
        total_seconds += duration
        expected = spec_duration_seconds(spec)
        if info["format"] != 1:
            errors.append(f"{spec.filename}: expected format 1, found {info['format']}")
        if info["division"] != PPQ:
            errors.append(f"{spec.filename}: expected PPQ {PPQ}, found {info['division']}")
        if abs(duration - expected) > 0.05:
            errors.append(f"{spec.filename}: duration {duration:.3f}s != expected {expected:.3f}s")
        if int(info["track_count"]) < 8:
            errors.append(f"{spec.filename}: too few tracks ({info['track_count']})")
        if int(info["note_on_events"]) < 250:
            errors.append(f"{spec.filename}: too few note-on events ({info['note_on_events']})")
        tracks = info["tracks"]  # type: ignore[assignment]
        track_names = {
            entry["name"]: entry for entry in tracks if isinstance(entry, dict) and "name" in entry
        }  # type: ignore[var-annotated]
        required_track_names = (
            "Piano",
            "Cello",
            "Viola",
            "Violin",
            "String ensemble",
            "Low strings",
            "Celesta echoes",
        )
        for track_name in required_track_names:
            track_info = track_names.get(track_name)
            if track_info is None:
                errors.append(f"{spec.filename}: missing track '{track_name}' in MIDI")
                continue
            cc_counts = track_info.get("cc_counts", {})  # type: ignore[assignment]
            if int(cc_counts.get(1, 0)) < 1:
                errors.append(f"{spec.filename}: '{track_name}' track has no modulation CC1")
            if int(cc_counts.get(71, 0)) < 1 and int(cc_counts.get(74, 0)) < 1:
                errors.append(f"{spec.filename}: '{track_name}' track has no timbre control (CC71/CC74)")
            if int(track_info.get("pitch_bend_events", 0)) < 1:
                errors.append(f"{spec.filename}: '{track_name}' track has no pitch-bend event")
            if int(track_info.get("channel_pressure_events", 0)) < 1:
                errors.append(f"{spec.filename}: '{track_name}' track has no channel-pressure event")
        print(
            f"{spec.number:02d}. {spec.title}: {duration:.3f}s, "
            f"{info['track_count']} tracks, {info['note_on_events']} notes"
        )
    manifest_total = float(manifest.get("total_duration_seconds", 0.0))
    if abs(total_seconds - manifest_total) > 0.5:
        errors.append(f"total duration {total_seconds:.3f}s != manifest {manifest_total:.3f}s")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"Verified 12 MIDI tracks; total duration {total_seconds / 60:.2f} minutes.")


def main(argv: list[str]) -> None:
    if argv == ["--verify"]:
        verify_album()
        return
    if argv:
        raise SystemExit("usage: python build.py [--verify]")
    generate_album()


if __name__ == "__main__":
    main(sys.argv[1:])

