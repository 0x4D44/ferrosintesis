"""The Iron Tide - an original cinematic piece in the Hans Zimmer idiom.

A single-movement build: low D pedal and sparse piano, a string ostinato that
gathers force, taiko-style percussion, low-brass braams at section pillars,
and a horn theme that crests at the climax before a quiet piano coda.

Generate with:  python the_iron_tide.py
Output:         midi/The Iron Tide.mid
"""

from __future__ import annotations

import math
import random
import struct
from dataclasses import dataclass, field
from pathlib import Path

PPQ = 480
BEATS_PER_BAR = 4
BARS = 96
TITLE = "The Iron Tide"
ROOT = Path(__file__).resolve().parent
MIDI_DIR = ROOT / "midi"

# Tempo pillars: (bar, bpm) - steady drive, easing off for the coda.
TEMPO_MAP = ((0, 112.0), (80, 104.0), (88, 92.0), (92, 76.0))

# Intensity arc: (bar, 0..1) - the long Zimmer build.
INTENSITY = ((0, 0.12), (16, 0.32), (40, 0.58), (56, 0.78), (64, 1.0), (78, 0.95), (80, 0.30), (96, 0.08))

# Harmony: one chord per bar, cycling in 4-bar cells. D natural minor.
# Main cell: Dm - Bb - F - C.  Climax cell: Dm - Bb - Gm - Asus4.
D2, F2, G2, A2, BB1, C2 = 38, 41, 43, 45, 34, 36
MAIN_CELL = (
    (D2, (50, 57, 62, 65)),   # Dm: D3 A3 D4 F4
    (BB1, (46, 53, 58, 62)),  # Bb: Bb2 F3 Bb3 D4
    (F2, (41, 48, 53, 57)),   # F:  F2 C3 F3 A3
    (C2, (48, 55, 60, 64)),   # C:  C3 G3 C4 E4
)
CLIMAX_CELL = (
    (D2, (50, 57, 62, 65)),   # Dm
    (BB1, (46, 53, 58, 62)),  # Bb
    (G2, (43, 50, 55, 58)),   # Gm: G2 D3 G3 Bb3
    (A2, (45, 52, 57, 62)),   # Asus4: A2 E3 A3 D4
)

# Horn theme, one 8-bar phrase in D minor: (beat offset within phrase, pitch, duration).
THEME = (
    (0.0, 62, 3.0), (3.0, 65, 1.0),            # D4 . . F4
    (4.0, 64, 2.0), (6.0, 62, 1.0), (7.0, 60, 1.0),   # E4 D4 C4
    (8.0, 62, 4.0),                            # D4 held
    (12.0, 57, 2.0), (14.0, 60, 2.0),          # A3 C4
    (16.0, 62, 3.0), (19.0, 65, 1.0),          # D4 . . F4
    (20.0, 67, 2.0), (22.0, 65, 1.0), (23.0, 64, 1.0),  # G4 F4 E4
    (24.0, 65, 2.0), (26.0, 62, 2.0),          # F4 D4
    (28.0, 60, 2.5), (30.5, 62, 1.5),          # C4 D4
)


def beat_to_tick(beat: float) -> int:
    return int(round(beat * PPQ))


def bar_beat(bar: int, beat: float = 0.0) -> float:
    return bar * BEATS_PER_BAR + beat


def vlq(value: int) -> bytes:
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

    def note(
        self,
        channel: int,
        pitch: int,
        start: float,
        duration: float,
        velocity: int,
        jitter: int = 0,
        rng: random.Random | None = None,
    ) -> None:
        start_tick = beat_to_tick(start)
        stop_tick = beat_to_tick(start + duration)
        if jitter and rng is not None:
            offset = rng.randint(-jitter, jitter)
            start_tick = max(0, start_tick + offset)
            stop_tick = max(start_tick + 1, stop_tick + offset)
        stop_tick = min(stop_tick, END_TICK)
        if start_tick >= stop_tick:
            return
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, velocity))
        self.add(start_tick, bytes([0x90 | channel, pitch, velocity]), priority=5)
        self.add(stop_tick, bytes([0x80 | channel, pitch, 0]), priority=4)

    def resolve_overlaps(self) -> None:
        """Truncate same-channel, same-pitch overlaps before serialization."""
        on_ticks: dict[tuple[int, int], list[int]] = {}
        off_events: dict[tuple[int, int], list[Event]] = {}
        for event in self.events:
            status = event.data[0] & 0xF0
            if status not in (0x80, 0x90):
                continue
            key = (event.data[0] & 0x0F, event.data[1])
            if status == 0x90 and event.data[2] > 0:
                on_ticks.setdefault(key, []).append(event.tick)
            else:
                off_events.setdefault(key, []).append(event)
        for key, starts in on_ticks.items():
            ends = off_events.get(key, [])
            if len(ends) != len(starts):
                continue
            starts.sort()
            ends.sort(key=lambda event: event.tick)
            for start, event in zip(starts[1:], ends):
                if event.tick > start:
                    event.tick = start

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


END_TICK = beat_to_tick(BARS * BEATS_PER_BAR)


def intensity_at(bar: float) -> float:
    if bar <= INTENSITY[0][0]:
        return INTENSITY[0][1]
    for (b0, v0), (b1, v1) in zip(INTENSITY, INTENSITY[1:]):
        if b0 <= bar <= b1:
            return v0 + (v1 - v0) * (bar - b0) / max(1, b1 - b0)
    return INTENSITY[-1][1]


def chord_at(bar: int) -> tuple[int, tuple[int, ...]]:
    cell = CLIMAX_CELL if 56 <= bar < 80 else MAIN_CELL
    return cell[bar % 4]


def setup_expression(track: MidiTrack, channel: int, volume: int, pan: int) -> None:
    track.cc(channel, 7, volume, 0)
    track.cc(channel, 10, pan, 0)
    track.cc(channel, 91, 64, 0)
    for bar in range(BARS):
        swell = math.sin(bar / 6.0) * 6
        value = int(40 + intensity_at(bar) * 60 + swell)
        track.cc(channel, 11, max(24, min(115, value)), bar_beat(bar))


def add_piano(track: MidiTrack, rng: random.Random) -> None:
    track.program(0, 0)
    setup_expression(track, 0, 92, 58)
    for bar in range(BARS):
        level = intensity_at(bar)
        root, triad = chord_at(bar)
        start = bar_beat(bar)
        if bar < 16 or bar >= 80:
            # Sparse tolling figure in the intro and coda.
            if bar % 2 == 0:
                track.note(0, root + 24, start, 3.8, int(38 + level * 30), jitter=4, rng=rng)
                track.note(0, triad[1] + 12, start + 2.0, 1.8, int(30 + level * 26), jitter=4, rng=rng)
            if bar % 4 == 3:
                track.note(0, triad[3] + 12, start + 3.0, 0.9, int(28 + level * 24), jitter=4, rng=rng)
        else:
            # Driving octaves that thicken with the build.
            track.note(0, root + 12, start, 1.9, int(42 + level * 34), jitter=4, rng=rng)
            track.note(0, root + 24, start, 1.9, int(38 + level * 32), jitter=4, rng=rng)
            track.note(0, root + 12, start + 2.0, 1.9, int(38 + level * 30), jitter=4, rng=rng)
            if level > 0.55:
                for step, beat in enumerate((0.5, 1.5, 2.5, 3.5)):
                    pitch = triad[(step + bar) % len(triad)] + 12
                    track.note(0, pitch, start + beat, 0.4, int(34 + level * 30), jitter=5, rng=rng)
    # Final resolution: bare open fifth on D.
    track.note(0, 50, bar_beat(92), 15.5, 44)
    track.note(0, 57, bar_beat(92, 0.1), 15.4, 38)
    track.note(0, 62, bar_beat(92, 0.2), 15.3, 34)


def add_ostinato(track: MidiTrack, rng: random.Random) -> None:
    track.program(1, 48)
    setup_expression(track, 1, 84, 70)
    for bar in range(8, 88):
        level = intensity_at(bar)
        root, triad = chord_at(bar)
        start = bar_beat(bar)
        if level < 0.30:
            steps, cycle = 8, (0, 2)          # gentle eighth-note pulse: root, fifth
        elif level < 0.65:
            steps, cycle = 8, (0, 1, 2, 1)
        else:
            steps, cycle = 16, (0, 1, 2, 3, 2, 1)  # full sixteenth-note churn
        width = BEATS_PER_BAR / steps
        for step in range(steps):
            pitch = triad[cycle[step % len(cycle)] % len(triad)] + 12
            accent = 10 if step % (steps // 4) == 0 else 0
            velocity = int(30 + level * 46 + accent + math.sin(step * 0.8) * 4)
            track.note(1, pitch, start + step * width, width * 0.85, velocity, jitter=3, rng=rng)


def add_low_strings(track: MidiTrack, rng: random.Random) -> None:
    track.program(2, 43)
    setup_expression(track, 2, 88, 64)
    for bar in range(0, 92, 2):
        level = intensity_at(bar)
        root, _ = chord_at(bar)
        # Long pedal tones, breaking into a driving pulse at high intensity.
        if level > 0.7:
            for beat in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0):
                track.note(2, root, bar_beat(bar, beat), 0.85, int(36 + level * 40), jitter=4, rng=rng)
        else:
            track.note(2, root, bar_beat(bar), 7.7, int(30 + level * 36), jitter=5, rng=rng)
    track.note(2, 38, bar_beat(92), 15.5, 40)  # final low D pedal


def add_cello(track: MidiTrack, rng: random.Random) -> None:
    track.program(3, 42)
    setup_expression(track, 3, 80, 50)
    # Rising two-bar sighs that answer the harmony through the mid-build.
    for bar in range(16, 56, 4):
        level = intensity_at(bar)
        root, triad = chord_at(bar)
        track.note(3, root + 12, bar_beat(bar, 0.0), 3.0, int(40 + level * 34), jitter=6, rng=rng)
        track.note(3, triad[1], bar_beat(bar, 3.0), 2.0, int(38 + level * 32), jitter=6, rng=rng)
        track.note(3, triad[2], bar_beat(bar + 1, 1.0), 3.0, int(42 + level * 34), jitter=6, rng=rng)
    # Doubling the horn theme an octave down at the climax.
    for phrase_start in (64, 72):
        for offset, pitch, duration in THEME:
            track.note(3, pitch - 12, bar_beat(phrase_start) + offset, duration * 0.95, int(48 + intensity_at(phrase_start) * 30), jitter=5, rng=rng)


def add_horns(track: MidiTrack, rng: random.Random) -> None:
    track.program(4, 60)
    setup_expression(track, 4, 86, 64)
    # First statement: distant, mid-build.
    for offset, pitch, duration in THEME:
        bar = 40 + offset / BEATS_PER_BAR
        track.note(4, pitch, bar_beat(40) + offset, duration * 0.92, int(40 + intensity_at(bar) * 30), jitter=6, rng=rng)
    # Climax statements: full voice, octave up on the second pass.
    for phrase_start, lift in ((64, 0), (72, 12)):
        for offset, pitch, duration in THEME:
            bar = phrase_start + offset / BEATS_PER_BAR
            velocity = int(56 + intensity_at(bar) * 40)
            track.note(4, pitch + lift, bar_beat(phrase_start) + offset, duration * 0.95, velocity, jitter=5, rng=rng)
            if lift:
                track.note(4, pitch, bar_beat(phrase_start) + offset, duration * 0.95, velocity - 12, jitter=5, rng=rng)


def add_braams(track: MidiTrack, rng: random.Random) -> None:
    track.program(5, 61)
    setup_expression(track, 5, 90, 60)
    # Low-brass pillars marking each section boundary of the build.
    for bar in (16, 32, 40, 48, 56, 64, 72, 78):
        level = intensity_at(bar)
        velocity = int(52 + level * 46)
        length = 3.5 if bar < 64 else 6.0
        track.note(5, 26, bar_beat(bar), length, velocity, jitter=3, rng=rng)      # D1
        track.note(5, 33, bar_beat(bar), length, velocity - 8, jitter=3, rng=rng)  # A1
        track.note(5, 38, bar_beat(bar), length, velocity - 14, jitter=3, rng=rng)  # D2


def add_choir(track: MidiTrack, rng: random.Random) -> None:
    track.program(6, 52)
    setup_expression(track, 6, 66, 78)
    # Choir pad from the second build onward, widest at the climax.
    for bar in range(48, 88, 2):
        level = intensity_at(bar)
        _, triad = chord_at(bar)
        for index, pitch in enumerate(triad[1:]):
            track.note(6, pitch + 24, bar_beat(bar, index * 0.2), 7.6 - index * 0.2, int(24 + level * 34), jitter=8, rng=rng)


def add_percussion(track: MidiTrack, rng: random.Random) -> None:
    setup_expression(track, 9, 96, 54)
    for bar in range(24, 84):
        level = intensity_at(bar)
        if level < 0.40 and bar % 2:
            continue
        strong = int(40 + level * 56)
        start = bar_beat(bar)
        # Taiko-style pattern: heavy downbeats, answering low toms.
        track.note(9, 36, start, 0.2, strong, jitter=2, rng=rng)
        track.note(9, 41, start + 2.0, 0.2, strong - 10, jitter=2, rng=rng)
        if level > 0.55:
            track.note(9, 43, start + 2.5, 0.2, strong - 16, jitter=3, rng=rng)
            track.note(9, 41, start + 3.5, 0.2, strong - 12, jitter=3, rng=rng)
        if level > 0.8:
            track.note(9, 36, start + 1.0, 0.2, strong - 8, jitter=2, rng=rng)
            track.note(9, 43, start + 3.0, 0.2, strong - 14, jitter=3, rng=rng)
        if bar % 8 == 0 and level > 0.5:
            track.note(9, 49, start, 1.5, min(110, strong + 12), jitter=2, rng=rng)
    # Final crash into the coda.
    track.note(9, 49, bar_beat(80), 2.0, 96)
    track.note(9, 36, bar_beat(80), 0.3, 104)


def conductor_track() -> MidiTrack:
    track = MidiTrack("Conductor")
    track.meta_text(0, 0x01, f"{TITLE} - original cinematic piece (Zimmer-style idiom)")
    track.meta(0, 0x58, bytes([4, 2, 24, 8]))
    track.meta(0, 0x59, bytes([(256 - 1) % 256, 1]))  # D minor: one flat
    for bar, bpm in TEMPO_MAP:
        track.meta(beat_to_tick(bar_beat(bar)), 0x51, int(round(60_000_000 / bpm)).to_bytes(3, "big"))
    for bar, label in ((0, "intro"), (16, "first build"), (40, "theme, distant"), (56, "surge"), (64, "climax"), (80, "coda")):
        track.meta_text(beat_to_tick(bar_beat(bar)), 0x06, label)
    return track


def duration_seconds() -> float:
    total = 0.0
    for index, (start_bar, bpm) in enumerate(TEMPO_MAP):
        end_bar = TEMPO_MAP[index + 1][0] if index + 1 < len(TEMPO_MAP) else BARS
        total += (end_bar - start_bar) * BEATS_PER_BAR * 60 / bpm
    return total


def main() -> None:
    rng = random.Random(20260701)
    builders = (
        ("Piano", add_piano),
        ("String ostinato", add_ostinato),
        ("Low strings", add_low_strings),
        ("Cello", add_cello),
        ("Horns", add_horns),
        ("Braams", add_braams),
        ("Choir", add_choir),
        ("Percussion", add_percussion),
    )
    tracks = [conductor_track()]
    for name, builder in builders:
        track = MidiTrack(name)
        builder(track, rng)
        tracks.append(track)

    MIDI_DIR.mkdir(exist_ok=True)
    path = MIDI_DIR / f"{TITLE}.mid"
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    path.write_bytes(header + b"".join(track.render() for track in tracks))
    note_count = sum(1 for track in tracks for event in track.events if event.data[0] & 0xF0 == 0x90 and event.data[2] > 0)
    print(f"{TITLE}: {duration_seconds():.1f}s, {len(tracks)} tracks, {note_count} notes -> {path}")


if __name__ == "__main__":
    main()
