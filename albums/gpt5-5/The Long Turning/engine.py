from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import math
import random
import struct
import sys


ALBUM_TITLE = "The Long Turning"
TRACK_TITLE = "The Long Turning"
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"
TRACKS_DIR = ALBUM_ROOT / "tracks"

PPQ = 480
BEATS_PER_BAR = 4
BPM = 120
BARS = 1800
SECTION_BARS = 90
END_TICK = BARS * BEATS_PER_BAR * PPQ
OUTFILE = MIDI_DIR / "01 - The Long Turning.mid"


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
    "ionian": [0, 2, 4, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
}

DEGREES = {
    "I": 0,
    "ii": 2,
    "bII": 1,
    "iii": 4,
    "iv": 5,
    "IV": 5,
    "v": 7,
    "V": 7,
    "vi": 9,
    "bVI": 8,
    "bVII": 10,
}

QUALITIES = {
    "maj": [0, 4, 7],
    "maj7": [0, 4, 7, 11],
    "add9": [0, 4, 7, 14],
    "min": [0, 3, 7],
    "min7": [0, 3, 7, 10],
    "sus2": [0, 2, 7, 12],
    "sus4": [0, 5, 7, 10],
    "open": [0, 7, 12],
}


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
        self.events.append(Event(max(0, min(END_TICK, tick)), priority, data))

    def meta(self, tick: int, meta_type: int, payload: bytes, priority: int = 0) -> None:
        self.add(tick, bytes([0xFF, meta_type]) + vlq(len(payload)) + payload, priority)

    def meta_text(self, tick: int, meta_type: int, text: str, priority: int = 0) -> None:
        self.meta(tick, meta_type, text.encode("utf-8"), priority)

    def program(self, channel: int, program: int) -> None:
        self.add(0, bytes([0xC0 | channel, program]), priority=1)

    def cc(self, channel: int, controller: int, value: int, beat: float) -> None:
        payload = bytes([0xB0 | channel, controller, max(0, min(127, value))])
        self.add(beat_to_tick(beat), payload, priority=2)

    def note(
        self,
        channel: int,
        pitch: int,
        start: float,
        duration: float,
        velocity: int,
        rng: random.Random | None = None,
        jitter: int = 0,
    ) -> None:
        start_tick = beat_to_tick(start)
        stop_tick = beat_to_tick(start + duration)
        if rng is not None and jitter:
            offset = rng.randint(-jitter, jitter)
            start_tick = max(0, start_tick + offset)
            stop_tick = max(start_tick + 1, stop_tick + offset + rng.randint(-jitter, jitter))
        stop_tick = min(stop_tick, END_TICK)
        if start_tick >= stop_tick:
            return
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, velocity))
        self.add(start_tick, bytes([0x90 | channel, pitch, velocity]), priority=5)
        self.add(stop_tick, bytes([0x80 | channel, pitch, 0]), priority=4)

    def resolve_overlaps(self) -> None:
        """Collapse simultaneous duplicate starts, then clamp overlaps."""
        on_indices: dict[tuple[int, int], list[int]] = {}
        off_indices: dict[tuple[int, int], list[int]] = {}
        for index, event in enumerate(self.events):
            status = event.data[0] & 0xF0
            if status not in (0x80, 0x90):
                continue
            key = (event.data[0] & 0x0F, event.data[1])
            if status == 0x90 and event.data[2] > 0:
                on_indices.setdefault(key, []).append(index)
            else:
                off_indices.setdefault(key, []).append(index)
        remove: set[int] = set()
        for key, starts in on_indices.items():
            ends = off_indices.get(key, [])
            if len(ends) != len(starts):
                continue
            starts.sort(key=lambda i: (self.events[i].tick, i))
            ends.sort(key=lambda i: (self.events[i].tick, i))
            kept: list[tuple[int, int]] = []
            for pair in zip(starts, ends):
                if kept and self.events[kept[-1][0]].tick == self.events[pair[0]].tick:
                    remove.update(kept.pop())
                kept.append(pair)
            for (_start, end), (next_start, _next_end) in zip(kept, kept[1:]):
                next_tick = self.events[next_start].tick
                if self.events[end].tick > next_tick:
                    self.events[end].tick = next_tick
        self.events = [
            event for index, event in enumerate(self.events) if index not in remove
        ]

    def render(self) -> bytes:
        self.resolve_overlaps()
        body = bytearray()
        last = 0
        for event in sorted(self.events):
            body += vlq(event.tick - last)
            body += event.data
            last = event.tick
        body += vlq(max(0, END_TICK - last))
        body += b"\xFF\x2F\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + body


@dataclass(frozen=True)
class Section:
    name: str
    key: str
    mode: str
    progression: tuple[str, ...]
    texture: str
    energy: float
    lead: str
    percussion: str


SECTIONS = [
    Section("Opening Clockwork", "D", "mixolydian", ("I:add9", "bVII:maj", "IV:add9", "I:sus4"), "guitar", 0.32, "whistle", "light"),
    Section("Hill Dance", "G", "dorian", ("I:min7", "IV:add9", "bVII:maj", "I:min"), "jig", 0.66, "whistle", "dance"),
    Section("Glass Engine", "A", "dorian", ("I:min7", "bVII:maj", "IV:add9", "v:min7"), "motor", 0.82, "guitar", "drive"),
    Section("Pipe Memory", "E", "aeolian", ("I:min", "bVI:maj7", "bVII:sus4", "I:min7"), "organ", 0.42, "organ", "light"),
    Section("Bright Crossing", "F", "lydian", ("I:add9", "V:sus4", "IV:maj7", "I:add9"), "pastoral", 0.50, "whistle", "none"),
    Section("Ridge Run", "B", "phrygian", ("I:min7", "bII:maj7", "bVII:maj", "I:min"), "rock", 0.92, "electric", "drive"),
    Section("Bell Orchard", "C", "ionian", ("I:add9", "V:sus4", "vi:min7", "IV:maj7"), "bells", 0.48, "bells", "light"),
    Section("Low Tide Machine", "F", "dorian", ("I:min7", "bVII:maj", "IV:add9", "v:min"), "motor", 0.74, "bass", "drive"),
    Section("Green Fuse", "D", "ionian", ("I:add9", "V:sus4", "vi:min7", "IV:add9"), "pastoral", 0.58, "whistle", "dance"),
    Section("Storm Windows", "E", "phrygian", ("I:min7", "bII:maj7", "bVI:maj", "I:min"), "rock", 0.98, "electric", "drive"),
    Section("The Room Turns", "A", "aeolian", ("I:min7", "bVI:maj7", "bVII:sus4", "iv:min7"), "organ", 0.54, "organ", "light"),
    Section("Hammered Sun", "G", "mixolydian", ("I:add9", "bVII:maj", "IV:add9", "V:sus4"), "jig", 0.78, "piano", "dance"),
    Section("Far Radio", "C", "lydian", ("I:maj7", "V:sus4", "IV:maj7", "I:add9"), "bells", 0.36, "bells", "none"),
    Section("Horse Latitudes", "Bb", "dorian", ("I:min7", "IV:add9", "bVII:maj", "I:min"), "guitar", 0.60, "guitar", "light"),
    Section("Broken Relay", "F", "phrygian", ("I:min7", "bII:maj7", "bVII:sus4", "I:min"), "motor", 0.88, "electric", "drive"),
    Section("The Long Green Field", "D", "mixolydian", ("I:add9", "IV:add9", "bVII:maj", "I:sus4"), "pastoral", 0.44, "whistle", "none"),
    Section("Stone Circle Reel", "A", "dorian", ("I:min7", "IV:add9", "bVII:maj", "v:min7"), "jig", 0.86, "whistle", "dance"),
    Section("Tremor Choir", "E", "aeolian", ("I:min", "bVI:maj7", "iv:min7", "bVII:sus4"), "organ", 0.70, "organ", "drive"),
    Section("Return of the Bells", "D", "mixolydian", ("I:add9", "bVII:maj", "IV:add9", "I:open"), "bells", 0.62, "bells", "light"),
    Section("Final Turning", "D", "ionian", ("I:add9", "V:sus4", "IV:maj7", "I:add9"), "guitar", 0.38, "whistle", "none"),
]


def pc(name: str) -> int:
    return NOTE_BASE[name]


def chord_pitches(section: Section, token: str) -> dict[str, list[int] | int]:
    degree, quality = token.split(":")
    root_pc = (pc(section.key) + DEGREES[degree]) % 12
    intervals = QUALITIES[quality]
    bass = 36 + root_pc
    low = [48 + root_pc + iv for iv in intervals[:3]]
    mid = [60 + root_pc + iv for iv in intervals]
    high = [72 + root_pc + iv for iv in intervals]
    return {
        "bass": bass,
        "low": low,
        "mid": mid,
        "high": high,
        "arp": sorted(mid + high[:3]),
    }


def scale_pitch(section: Section, degree: int, octave: int) -> int:
    scale = MODES[section.mode]
    octave_shift, index = divmod(degree, len(scale))
    return 12 * (octave + octave_shift + 1) + pc(section.key) + scale[index]


def section_for_bar(bar: int) -> tuple[int, Section, int]:
    index = min(len(SECTIONS) - 1, bar // SECTION_BARS)
    local = bar - index * SECTION_BARS
    return index, SECTIONS[index], local


def shape(section_index: int, local_bar: int, section: Section) -> float:
    local = local_bar / SECTION_BARS
    long_wave = math.sin((section_index / (len(SECTIONS) - 1)) * math.pi)
    local_wave = math.sin(local * math.pi)
    return max(0.08, min(1.0, section.energy * (0.55 + 0.45 * local_wave) + 0.10 * long_wave))


def setup_tracks() -> dict[str, MidiTrack]:
    tracks = {
        "conductor": MidiTrack("Conductor"),
        "guitar": MidiTrack("Nylon and steel guitars"),
        "electric": MidiTrack("Electric guitar"),
        "piano": MidiTrack("Piano and hammered keys"),
        "bass": MidiTrack("Bass guitar"),
        "organ": MidiTrack("Organ and reed bed"),
        "strings": MidiTrack("Strings"),
        "whistle": MidiTrack("Whistle and flute"),
        "bells": MidiTrack("Bells and tuned percussion"),
        "choir": MidiTrack("Distant choir"),
        "drums": MidiTrack("Percussion"),
    }
    programs = {
        "guitar": (0, 25),
        "electric": (1, 29),
        "piano": (2, 0),
        "bass": (3, 35),
        "organ": (4, 19),
        "strings": (5, 48),
        "whistle": (6, 74),
        "bells": (7, 14),
        "choir": (8, 52),
    }
    for name, (channel, program) in programs.items():
        tracks[name].program(channel, program)
    for name, channel, volume, pan in [
        ("guitar", 0, 84, 46),
        ("electric", 1, 70, 70),
        ("piano", 2, 78, 56),
        ("bass", 3, 82, 42),
        ("organ", 4, 66, 58),
        ("strings", 5, 62, 64),
        ("whistle", 6, 72, 78),
        ("bells", 7, 64, 86),
        ("choir", 8, 48, 60),
        ("drums", 9, 76, 54),
    ]:
        tracks[name].cc(channel, 7, volume, 0)
        tracks[name].cc(channel, 10, pan, 0)
        tracks[name].cc(channel, 91, 46, 0)
    return tracks


def add_conductor(track: MidiTrack) -> None:
    tempo = int(round(60_000_000 / BPM)).to_bytes(3, "big")
    track.meta_text(0, 0x01, f"{ALBUM_TITLE} - single continuous 60-minute movement")
    track.meta(0, 0x51, tempo)
    track.meta(0, 0x58, bytes([4, 2, 24, 8]))
    track.meta(0, 0x59, bytes([2, 1]))
    for index, section in enumerate(SECTIONS):
        bar = index * SECTION_BARS
        tick = beat_to_tick(bar_beat(bar))
        minute = index * 3
        track.meta_text(tick, 0x06, f"{minute:02d}:00 - {section.name}")
    track.meta_text(END_TICK, 0x01, "end", priority=99)


def add_expression(track: MidiTrack, channel: int, bar: int, level: float, offset: float = 0.0) -> None:
    value = int(34 + level * 74 + math.sin((bar + offset) / 5.0) * 6)
    track.cc(channel, 11, max(24, min(112, value)), bar_beat(bar, offset))


def add_guitar(track: MidiTrack, section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    chord = chord_pitches(section, section.progression[local % len(section.progression)])
    arp = list(chord["arp"])
    if section.texture in ("motor", "rock"):
        steps = 16
    elif section.texture == "jig":
        steps = 12
    else:
        steps = 8
    if local < 4:
        steps = max(4, steps // 2)
    step = BEATS_PER_BAR / steps
    add_expression(track, 0, bar, level)
    for i in range(steps):
        beat = i * step
        pitch = arp[(i * 2 + local) % len(arp)]
        if section.texture == "jig" and i % 3 == 2:
            pitch += 12
        if section.texture == "rock" and i % 4 == 3:
            pitch -= 12
        velocity = int(28 + level * 48 + (10 if i % 4 == 0 else 0))
        track.note(0, pitch, bar_beat(bar, beat), max(0.12, step * 0.72), velocity, rng, jitter=3)


def add_bass(track: MidiTrack, section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    chord = chord_pitches(section, section.progression[local % len(section.progression)])
    root = int(chord["bass"])
    add_expression(track, 3, bar, level)
    if section.percussion == "drive":
        pattern = (0.0, 1.0, 2.0, 2.75, 3.5)
    elif section.texture == "jig":
        pattern = (0.0, 1.5, 3.0)
    else:
        pattern = (0.0, 2.0)
    for i, beat in enumerate(pattern):
        pitch = root + (12 if i % 3 == 2 else 0)
        track.note(3, pitch, bar_beat(bar, beat), 0.72, int(34 + level * 46), rng, jitter=4)


def add_pads(tracks: dict[str, MidiTrack], section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    chord = chord_pitches(section, section.progression[local % len(section.progression)])
    if bar % 2 == 0:
        add_expression(tracks["strings"], 5, bar, level)
        for i, pitch in enumerate(list(chord["mid"])[:4]):
            tracks["strings"].note(5, pitch, bar_beat(bar, i * 0.08), 7.7 - i * 0.08, int(22 + level * 42), rng, jitter=6)
    if section.texture in ("organ", "bells", "pastoral") and bar % 4 == 0:
        add_expression(tracks["organ"], 4, bar, level)
        for i, pitch in enumerate(list(chord["low"])):
            tracks["organ"].note(4, pitch, bar_beat(bar, i * 0.15), 15.5 - i * 0.15, int(26 + level * 38), rng, jitter=5)
    if section.texture == "organ" and bar % 8 == 0:
        for i, pitch in enumerate(list(chord["mid"])[:3]):
            tracks["choir"].note(8, pitch + 12, bar_beat(bar, 1 + i * 0.35), 10.0, int(18 + level * 28), rng, jitter=7)


def add_lead(tracks: dict[str, MidiTrack], section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    if local % 8 not in (0, 1, 4, 5):
        return
    motifs = {
        "whistle": [(4, 0.0, 0.55), (5, 0.65, 0.45), (7, 1.15, 0.65), (5, 2.05, 0.55), (4, 2.85, 0.65)],
        "guitar": [(0, 0.0, 0.32), (2, 0.45, 0.32), (4, 0.92, 0.40), (7, 1.55, 0.48), (5, 2.5, 0.55)],
        "electric": [(7, 0.0, 0.45), (5, 0.55, 0.32), (4, 1.0, 0.36), (2, 1.45, 0.42), (7, 2.45, 0.75)],
        "organ": [(2, 0.0, 1.2), (4, 1.35, 0.75), (5, 2.3, 1.1)],
        "bells": [(7, 0.0, 1.6), (9, 1.25, 1.1), (11, 2.5, 1.3)],
        "bass": [(0, 0.0, 0.5), (0, 1.0, 0.5), (2, 1.5, 0.5), (4, 2.5, 0.6)],
        "piano": [(0, 0.0, 0.35), (4, 0.5, 0.35), (7, 1.0, 0.35), (11, 1.5, 0.55), (7, 2.65, 0.55)],
    }
    channel_by_lead = {"whistle": 6, "guitar": 0, "electric": 1, "organ": 4, "bells": 7, "bass": 3, "piano": 2}
    track_by_lead = {
        "whistle": tracks["whistle"],
        "guitar": tracks["guitar"],
        "electric": tracks["electric"],
        "organ": tracks["organ"],
        "bells": tracks["bells"],
        "bass": tracks["bass"],
        "piano": tracks["piano"],
    }
    octave_by_lead = {"whistle": 5, "guitar": 4, "electric": 5, "organ": 4, "bells": 6, "bass": 2, "piano": 5}
    for degree, offset, duration in motifs[section.lead]:
        pitch = scale_pitch(section, degree + (local // 8) % 3, octave_by_lead[section.lead])
        velocity = int(32 + level * 48 + (10 if section.lead == "electric" else 0))
        track_by_lead[section.lead].note(channel_by_lead[section.lead], pitch, bar_beat(bar, offset), duration, velocity, rng, jitter=5)


def add_keys_and_bells(tracks: dict[str, MidiTrack], section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    chord = chord_pitches(section, section.progression[local % len(section.progression)])
    if section.texture in ("bells", "pastoral", "jig") and bar % 4 in (0, 2):
        for i, pitch in enumerate(list(chord["high"])[:3]):
            tracks["bells"].note(7, pitch + 12, bar_beat(bar, 0.5 + i), 1.7, int(24 + level * 30), rng, jitter=3)
    if section.texture in ("motor", "rock", "jig") and bar % 2 == 1:
        for i, pitch in enumerate(list(chord["mid"])[:3]):
            tracks["piano"].note(2, pitch + (12 if i == 2 else 0), bar_beat(bar, i * 0.5), 0.28, int(34 + level * 38), rng, jitter=3)
    if local == 0:
        for i, pitch in enumerate(list(chord["high"])[:4]):
            tracks["bells"].note(7, pitch + 12, bar_beat(bar, i * 0.25), 3.5, int(42 + level * 30), rng, jitter=2)


def add_drums(track: MidiTrack, section: Section, rng: random.Random, bar: int, local: int, level: float) -> None:
    if section.percussion == "none":
        if local % 16 == 0:
            track.note(9, 49, bar_beat(bar), 1.2, int(34 + level * 34), rng, jitter=2)
        return
    add_expression(track, 9, bar, level)
    if section.percussion == "light":
        hits = [(36, 0.0, 0.12, 36), (42, 1.0, 0.08, 26), (38, 2.0, 0.12, 32), (42, 3.0, 0.08, 24)]
    elif section.percussion == "dance":
        hits = [(36, 0.0, 0.10, 48), (42, 0.66, 0.07, 30), (38, 1.33, 0.10, 38), (42, 2.0, 0.07, 32), (36, 2.66, 0.10, 42), (38, 3.33, 0.10, 34)]
    else:
        hits = [(36, 0.0, 0.10, 58), (42, 0.5, 0.06, 32), (38, 1.0, 0.10, 46), (42, 1.5, 0.06, 32), (36, 2.0, 0.10, 54), (42, 2.5, 0.06, 32), (38, 3.0, 0.10, 48), (46, 3.5, 0.05, 30)]
    for pitch, beat, duration, base_velocity in hits:
        track.note(9, pitch, bar_beat(bar, beat), duration, int(base_velocity + level * 40), rng, jitter=2)
    if section.percussion == "drive" and local % 8 == 7:
        for i in range(6):
            track.note(9, 45 + i % 3, bar_beat(bar, 2.5 + i * 0.22), 0.09, int(44 + level * 38), rng, jitter=2)


def compose() -> list[MidiTrack]:
    rng = random.Random(20260624)
    tracks = setup_tracks()
    add_conductor(tracks["conductor"])
    ordered = [
        tracks["conductor"],
        tracks["guitar"],
        tracks["electric"],
        tracks["piano"],
        tracks["bass"],
        tracks["organ"],
        tracks["strings"],
        tracks["whistle"],
        tracks["bells"],
        tracks["choir"],
        tracks["drums"],
    ]
    for bar in range(BARS):
        section_index, section, local = section_for_bar(bar)
        level = shape(section_index, local, section)
        add_guitar(tracks["guitar"], section, rng, bar, local, level)
        add_bass(tracks["bass"], section, rng, bar, local, level)
        add_pads(tracks, section, rng, bar, local, level)
        add_lead(tracks, section, rng, bar, local, level)
        add_keys_and_bells(tracks, section, rng, bar, local, level)
        add_drums(tracks["drums"], section, rng, bar, local, level)
    for track in ordered:
        track.meta_text(END_TICK, 0x01, "end", priority=99)
    return ordered


def write_midi(path: Path, tracks: list[MidiTrack]) -> None:
    path.parent.mkdir(exist_ok=True)
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    path.write_bytes(header + b"".join(track.render() for track in tracks))


def track_manifest(note_count: int, midi_tracks: int) -> dict[str, object]:
    return {
        "album": ALBUM_TITLE,
        "track_count": 1,
        "total_duration_seconds": 3600.0,
        "total_duration_minutes": 60.0,
        "tracks": [
            {
                "number": 1,
                "title": TRACK_TITLE,
                "file": "midi/01 - The Long Turning.mid",
                "mood": "single continuous progressive folk-rock/classical collage",
                "role": "A 60-minute through-composed movement with 20 contrasting three-minute chapters.",
                "bars": BARS,
                "bpm": BPM,
                "duration_seconds": 3600.0,
                "duration_minutes": 60.0,
                "midi_tracks": midi_tracks,
                "note_on_events": note_count,
                "sections": [
                    {
                        "number": index + 1,
                        "start_minute": index * 3,
                        "name": section.name,
                        "key": section.key,
                        "mode": section.mode,
                        "texture": section.texture,
                        "lead": section.lead,
                    }
                    for index, section in enumerate(SECTIONS)
                ],
            }
        ],
    }


def write_docs(manifest: dict[str, object]) -> None:
    readme = """# The Long Turning
### a single 60-minute progressive MIDI movement

One uninterrupted track for guitars, bass, piano, organ, strings, whistle/flute,
bells, distant choir, and percussion. The piece uses a long-form progressive
folk-rock/classical collage vocabulary: recurring guitar cells, abrupt chapter
changes, pastoral whistle themes, organ beds, bell returns, and driving percussion.

This is original material. It is not a direct imitation or continuation of any
living artist's catalog or any existing recording.

## Layout

- `midi/` - the numbered album MIDI file
- `tracks/` - the numbered per-track source entry point
- `engine.py` - shared generator, MIDI writer, manifest writer, and verifier
- `build.py` - rebuilds or verifies the album
- `ALBUM.md` - the creative map and section list
- `album_manifest.json` - machine-readable metadata

## Regenerate / Verify

```powershell
python .\\build.py
python .\\build.py --verify
python .\\tracks\\01_the_long_turning.py
```
"""
    (ALBUM_ROOT / "README.md").write_text(readme, encoding="utf-8")

    sections = manifest["tracks"][0]["sections"]  # type: ignore[index]
    lines = [
        "# The Long Turning",
        "",
        "Original single-track MIDI album: one continuous 60-minute movement.",
        "",
        "The architecture is a 20-part journey with each chapter lasting exactly three minutes.",
        "It draws from broad progressive folk-rock and contemporary-classical materials without copying any existing work.",
        "",
        "## Track",
        "",
        "01. The Long Turning - 3600.0s - single continuous progressive folk-rock/classical collage",
        "    - File: `midi/01 - The Long Turning.mid`",
        "    - Length: 60:00",
        "    - Form: 20 continuous chapters, 90 bars each at 120 BPM",
        "",
        "## Chapters",
        "",
    ]
    for section in sections:  # type: ignore[assignment]
        lines.append(
            f"{section['number']:02d}. {section['start_minute']:02d}:00 - {section['name']} "
            f"({section['key']} {section['mode']}, {section['texture']}, lead {section['lead']})"
        )
    lines += [
        "",
        "## Verification",
        "",
        "```powershell",
        "python .\\build.py --verify",
        "```",
        "",
    ]
    (ALBUM_ROOT / "ALBUM.md").write_text("\n".join(lines), encoding="utf-8")


def generate_track(number: int = 1) -> tuple[Path, int, int]:
    if number != 1:
        raise ValueError("The Long Turning has one track: 1")
    tracks = compose()
    write_midi(OUTFILE, tracks)
    info = parse_midi(OUTFILE)
    manifest = track_manifest(int(info["note_on_events"]), int(info["track_count"]))
    (ALBUM_ROOT / "album_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_docs(manifest)
    print(f"01. {TRACK_TITLE}: {info['duration_seconds']:.3f}s -> {OUTFILE.name}")
    return OUTFILE, int(info["note_on_events"]), int(info["track_count"])


def generate_album() -> None:
    MIDI_DIR.mkdir(exist_ok=True)
    TRACKS_DIR.mkdir(exist_ok=True)
    path, note_count, midi_track_count = generate_track(1)
    print(f"Album: 1 track, 60.00 minutes, {note_count} notes, {midi_track_count} MIDI tracks")
    print(f"Wrote {path}")


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
            max_tick = max(max_tick, tick)
        names.append(name)
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
        "max_tick": max_tick,
        "duration_seconds": seconds,
    }


def verify_album() -> None:
    errors: list[str] = []
    midi_files = sorted(MIDI_DIR.glob("[0-9][0-9] - *.mid"))
    if len(midi_files) != 1:
        errors.append(f"expected 1 numbered MIDI file, found {len(midi_files)}")
    if not OUTFILE.exists():
        errors.append(f"missing {OUTFILE}")
    else:
        info = parse_midi(OUTFILE)
        duration = float(info["duration_seconds"])
        if info["format"] != 1:
            errors.append(f"expected format 1, found {info['format']}")
        if info["division"] != PPQ:
            errors.append(f"expected PPQ {PPQ}, found {info['division']}")
        if abs(duration - 3600.0) > 0.001:
            errors.append(f"duration {duration:.6f}s != 3600.000s")
        if int(info["track_count"]) < 10:
            errors.append(f"expected at least 10 MIDI tracks, found {info['track_count']}")
        if int(info["note_on_events"]) < 40000:
            errors.append(f"expected a dense long-form score, found only {info['note_on_events']} note-on events")
        print(
            f"01. {TRACK_TITLE}: {duration:.3f}s, "
            f"{info['track_count']} MIDI tracks, {info['note_on_events']} notes"
        )
    manifest_path = ALBUM_ROOT / "album_manifest.json"
    if not manifest_path.exists():
        errors.append("missing album_manifest.json")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("track_count") != 1:
            errors.append(f"manifest track_count is {manifest.get('track_count')}, expected 1")
        if abs(float(manifest.get("total_duration_seconds", 0.0)) - 3600.0) > 0.001:
            errors.append("manifest total duration is not 3600.0 seconds")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Verified one 60-minute MIDI track; total duration 60.00 minutes.")


def main(argv: list[str]) -> int:
    if argv == ["--verify"]:
        verify_album()
        return 0
    if argv:
        raise SystemExit("usage: python build.py [--verify]")
    generate_album()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
