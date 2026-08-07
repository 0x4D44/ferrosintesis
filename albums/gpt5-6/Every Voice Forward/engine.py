#!/usr/bin/env python3
"""Deterministic, standard-library MIDI engine for *Every Voice Forward*.

The writer deliberately emits explicit Standard MIDI File events rather than relying
on a third-party MIDI package.  The album can therefore be rebuilt with a bare
Python 3 installation, while the richer local validation may optionally use mido.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import math
import random
import struct
from typing import Callable, Iterable, Iterator, Sequence

PPQ = 480
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"
BUILD_DIR = ALBUM_ROOT / "build"
REFERENCE_DIR = BUILD_DIR / "reference"


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def tick(beat: float) -> int:
    return max(0, int(round(beat * PPQ)))


def beat_from_tick(value: int) -> float:
    return value / PPQ


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
    for _ in range(5):
        if pos >= len(data):
            raise ValueError("truncated variable-length quantity")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos
    raise ValueError("overlong variable-length quantity")


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

GM_PROGRAMS: tuple[str, ...] = (
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba", "Xylophone",
    "Tubular Bells", "Dulcimer", "Drawbar Organ", "Percussive Organ", "Rock Organ",
    "Church Organ", "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
    "Distortion Guitar", "Guitar Harmonics", "Acoustic Bass", "Electric Bass (finger)",
    "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1",
    "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings",
    "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1", "String Ensemble 2",
    "Synth Strings 1", "Synth Strings 2", "Choir Aahs", "Voice Oohs", "Synth Voice",
    "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
    "Brass Section", "Synth Brass 1", "Synth Brass 2", "Soprano Sax", "Alto Sax", "Tenor Sax",
    "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute",
    "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom",
    "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise", "Breath Noise", "Seashore",
    "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot",
)

GM_DRUMS: dict[int, str] = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick", 38: "Acoustic Snare",
    39: "Hand Clap", 40: "Electric Snare", 41: "Low Floor Tom", 42: "Closed Hi-Hat",
    43: "High Floor Tom", 44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1", 50: "High Tom",
    51: "Ride Cymbal 1", 52: "Chinese Cymbal", 53: "Ride Bell", 54: "Tambourine",
    55: "Splash Cymbal", 56: "Cowbell", 57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo", 61: "Low Bongo", 62: "Mute Hi Conga",
    63: "Open Hi Conga", 64: "Low Conga", 65: "High Timbale", 66: "Low Timbale",
    67: "High Agogo", 68: "Low Agogo", 69: "Cabasa", 70: "Maracas", 71: "Short Whistle",
    72: "Long Whistle", 73: "Short Guiro", 74: "Long Guiro", 75: "Claves",
    76: "Hi Wood Block", 77: "Low Wood Block", 78: "Mute Cuica", 79: "Open Cuica",
    80: "Mute Triangle", 81: "Open Triangle",
}


def pitch(root: int, mode: str, degree: int, octave: int = 0) -> int:
    scale = SCALES[mode]
    octaves, index = divmod(degree, len(scale))
    return root + scale[index] + 12 * (octaves + octave)


def chord(root: int, mode: str, degree: int, size: int = 4, octave: int = 0) -> list[int]:
    return [pitch(root, mode, degree + 2 * i, octave) for i in range(size)]


def invert(notes: Sequence[int], inversion: int = 0) -> list[int]:
    result = sorted(int(n) for n in notes)
    for _ in range(max(0, inversion)):
        result.append(result.pop(0) + 12)
    return result


def transpose(notes: Iterable[int], semitones: int) -> list[int]:
    return [int(n) + semitones for n in notes]


def fit_range(note: int, low: int, high: int) -> int:
    while note < low:
        note += 12
    while note > high:
        note -= 12
    return int(clamp(note, 0, 127))


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
    style: str
    concept: str
    program_range: tuple[int, int] | None = None
    duration_window: tuple[float, float] = (180.0, 420.0)
    min_notes: int = 900
    min_channels: int = 12
    min_markers: int = 7
    tags: tuple[str, ...] = ()


@dataclass
class Event:
    event_tick: int
    priority: int
    data: bytes
    serial: int


@dataclass
class Score:
    seed: int
    title: str
    initial_tempo: float
    nominal_beats: float
    rng: random.Random = field(init=False)
    events: dict[int, list[Event]] = field(default_factory=dict)
    names: dict[int, str] = field(default_factory=dict)
    tempos: list[tuple[float, float]] = field(default_factory=list)
    timesigs: list[tuple[float, int, int]] = field(default_factory=list)
    keysigs: list[tuple[float, int, bool]] = field(default_factory=list)
    markers: list[tuple[float, str]] = field(default_factory=list)
    lyrics: list[tuple[float, str]] = field(default_factory=list)
    annotations: dict[str, list[tuple[float, object]]] = field(default_factory=lambda: defaultdict(list))
    last_beat: float = 0.0
    _serial: int = 0

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.tempos = [(0.0, self.initial_tempo)]
        self.last_beat = self.nominal_beats

    def _append(self, ch: int, beat: float, priority: int, data: bytes) -> None:
        if not 0 <= ch <= 15:
            raise ValueError(f"invalid MIDI channel {ch}")
        self._serial += 1
        self.events.setdefault(ch, []).append(Event(tick(beat), priority, data, self._serial))

    def annotate(self, kind: str, beat: float, payload: object) -> None:
        self.annotations[kind].append((beat, payload))

    def channel(
        self,
        ch: int,
        name: str,
        program: int | None = 0,
        volume: int = 100,
        pan: int = 64,
        expression: int = 127,
        reverb: int = 48,
        chorus: int = 0,
        echo: int = 0,
        bank_msb: int = 0,
        bank_lsb: int = 0,
        beat: float = 0.0,
    ) -> None:
        self.names[ch] = name
        self.events.setdefault(ch, [])
        self.bank(ch, bank_msb, bank_lsb, beat)
        if program is not None:
            # Both Bank Select bytes precede Program Change, including for the
            # Ferrosintesis LSB variations (mandolin / Hollow Release).
            self.program(ch, program, beat + 2 / PPQ)
        self.cc(ch, 7, volume, beat)
        self.cc(ch, 10, pan, beat)
        self.cc(ch, 11, expression, beat)
        self.cc(ch, 91, reverb, beat)
        self.cc(ch, 93, chorus, beat)
        self.cc(ch, 94, echo, beat)

    def bank(self, ch: int, msb: int = 0, lsb: int = 0, beat: float = 0.0) -> None:
        self.cc(ch, 0, msb, beat, priority=20)
        self.cc(ch, 32, lsb, beat + 1 / PPQ, priority=20)
        self.annotate("bank", beat, (ch, msb, lsb))

    def program(self, ch: int, program: int, beat: float) -> None:
        self._append(ch, beat, 30, bytes([0xC0 | ch, int(clamp(program, 0, 127))]))
        self.annotate("program", beat, (ch, int(program)))

    def set_patch(self, ch: int, program: int, beat: float, bank_msb: int = 0, bank_lsb: int = 0) -> None:
        # Install the patch just ahead of the musical downbeat.  Note starts are
        # deliberately humanised by a few ticks, so configuring at exactly `beat`
        # can let an early-jittered note speak through the outgoing program.  An
        # eighth-beat lead is inaudible as a transition but makes patch ownership
        # deterministic even after humanisation.
        setup = max(0.0, beat - 0.125)
        self.all_notes_off(ch, setup)
        self.bank(ch, bank_msb, bank_lsb, setup + 1 / PPQ)
        self.program(ch, program, setup + 3 / PPQ)

    def cc(self, ch: int, number: int, value: int, beat: float, priority: int = 22) -> None:
        self._append(
            ch,
            beat,
            priority,
            bytes([0xB0 | ch, int(clamp(number, 0, 127)), int(clamp(value, 0, 127))]),
        )

    def aftertouch(self, ch: int, value: int, beat: float) -> None:
        self._append(ch, beat, 24, bytes([0xD0 | ch, int(clamp(value, 0, 127))]))

    def poly_aftertouch(self, ch: int, note: int, value: int, beat: float) -> None:
        self._append(
            ch,
            beat,
            24,
            bytes([0xA0 | ch, int(clamp(note, 0, 127)), int(clamp(value, 0, 127))]),
        )

    def bend(self, ch: int, semitones: float, beat: float, range_semitones: float = 2.0) -> None:
        raw = bend_raw(semitones, range_semitones)
        self._append(ch, beat, 23, bytes([0xE0 | ch, raw & 0x7F, (raw >> 7) & 0x7F]))

    def rpn(self, ch: int, number: int, msb: int, beat: float, lsb: int = 0) -> None:
        # Interleave successive messages by one tick so engines that apply events in
        # source order cannot accidentally collapse the transaction.
        base = tick(beat)
        sequence = ((101, (number >> 7) & 0x7F), (100, number & 0x7F), (6, msb), (38, lsb),
                    (101, 127), (100, 127))
        for i, (num, val) in enumerate(sequence):
            self._serial += 1
            data = bytes([0xB0 | ch, num, val & 0x7F])
            self.events.setdefault(ch, []).append(Event(base + i, 22, data, self._serial))
        self.annotate("rpn", beat, (ch, number, msb, lsb))

    def bend_range(self, ch: int, semitones: int, beat: float = 0.0, cents: int = 0) -> None:
        self.rpn(ch, 0, semitones, beat, cents)

    def fine_tune(self, ch: int, cents: float, beat: float = 0.0) -> None:
        # RPN 1: 14-bit value, centre 8192, full span nominally ±100 cents.
        raw = int(round(clamp(8192 + cents / 100.0 * 8192, 0, 16383)))
        self.rpn(ch, 1, (raw >> 7) & 0x7F, beat, raw & 0x7F)

    def note(
        self,
        ch: int,
        note: int,
        beat: float,
        duration: float,
        velocity: int,
        jt: int = 2,
        jv: int = 3,
        tag: str | None = None,
    ) -> None:
        note = int(clamp(round(note), 0, 127))
        velocity = int(clamp(round(velocity + self.rng.randint(-jv, jv)), 1, 127))
        on = tick(beat)
        if jt and beat > 0.05:
            on = max(0, on + self.rng.randint(-jt, jt))
        off = max(on + PPQ // 32, tick(beat + max(0.03, duration)))
        self._serial += 1
        self.events.setdefault(ch, []).append(Event(on, 40, bytes([0x90 | ch, note, velocity]), self._serial))
        self._serial += 1
        self.events.setdefault(ch, []).append(Event(off, 10, bytes([0x80 | ch, note, 0]), self._serial))
        self.last_beat = max(self.last_beat, beat + duration)
        if tag:
            self.annotate("note_tag", beat, (tag, ch, note, duration))

    def notes(
        self,
        ch: int,
        notes: Iterable[int],
        beat: float,
        duration: float,
        velocity: int,
        spread: float = 0.0,
        tag: str | None = None,
    ) -> None:
        for i, note in enumerate(notes):
            offset = spread * i
            self.note(ch, note, beat + offset, max(0.04, duration - offset), velocity - i, jt=1, jv=2, tag=tag)

    def hit(self, key: int, beat: float, velocity: int, duration: float = 0.12, ch: int = 9) -> None:
        self.note(ch, key, beat, duration, velocity, jt=1, jv=4)
        self.annotate("drum", beat, (ch, key))

    def all_notes_off(self, ch: int, beat: float) -> None:
        self.cc(ch, 123, 0, beat, priority=5)

    def all_sound_off(self, ch: int, beat: float) -> None:
        self.cc(ch, 120, 0, beat, priority=4)

    def reset_all_controllers(self, ch: int, beat: float) -> None:
        self.cc(ch, 121, 0, beat, priority=6)

    def reset_controls(self, ch: int, beat: float) -> None:
        self.bend(ch, 0.0, beat)
        for number, value in (
            (1, 0), (2, 127), (5, 0), (11, 127), (64, 0), (65, 0), (66, 0), (67, 0),
            (68, 0), (70, 64), (71, 64), (74, 127), (84, 0), (91, 32), (93, 0), (94, 0),
        ):
            self.cc(ch, number, value, beat)
        self.aftertouch(ch, 0, beat)
        self.cc(ch, 101, 127, beat + 1 / PPQ)
        self.cc(ch, 100, 127, beat + 2 / PPQ)

    def sysex(self, payload: bytes | Sequence[int], beat: float, ch_track: int = 0) -> None:
        body = bytes(int(v) & 0x7F for v in payload)
        data = bytes([0xF0]) + _vlq(len(body) + 1) + body + bytes([0xF7])
        self._append(ch_track, beat, 1, data)
        self.annotate("sysex", beat, body)

    def gm_reset(self, beat: float = 0.0) -> None:
        self.sysex((0x7E, 0x7F, 0x09, 0x01), beat)

    def xg_reset(self, beat: float = 0.0) -> None:
        self.sysex((0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00), beat)

    def gs_reset(self, beat: float = 0.0) -> None:
        address_data = [0x40, 0x00, 0x7F, 0x00]
        checksum = (-sum(address_data)) & 0x7F
        self.sysex((0x41, 0x10, 0x42, 0x12, *address_data, checksum), beat)

    @staticmethod
    def _gs_block_for_channel(ch: int) -> int:
        if ch == 9:
            nibble = 0
        elif 0 <= ch <= 8:
            nibble = ch + 1
        elif 10 <= ch <= 15:
            nibble = ch
        else:
            raise ValueError(f"invalid channel for GS part: {ch}")
        return 0x10 | nibble

    def gs_drum_mode(self, ch: int, on: bool, beat: float, map_number: int = 1) -> None:
        block = self._gs_block_for_channel(ch)
        value = int(clamp(map_number if on else 0, 0, 2))
        address_data = [0x40, block, 0x15, value]
        checksum = (-sum(address_data)) & 0x7F
        self.sysex((0x41, 0x10, 0x42, 0x12, *address_data, checksum), beat)
        self.annotate("gs_drum_mode", beat, (ch, on, value))

    def xg_effect(self, address_low: int, data: int | Sequence[int], beat: float = 0.0) -> None:
        values = [data] if isinstance(data, int) else list(data)
        if len(values) not in (1, 2):
            raise ValueError("Ferrosintesis models one- and two-byte XG Effect1 parameters")
        self.sysex((0x43, 0x10, 0x4C, 0x02, 0x01, address_low, *values), beat)

    def xg_hall1(self, beat: float = 0.0) -> None:
        self.xg_effect(0x00, (0x01, 0x00), beat)

    def xg_chorus1(self, beat: float = 0.0) -> None:
        self.xg_effect(0x20, (0x41, 0x00), beat)

    def xg_amp_sim(self, ch: int, drive: int, dry_wet: int, beat: float = 0.0) -> None:
        # Effect1 variation block: Amp Simulator, insertion connection, target part.
        self.xg_effect(0x40, (0x4B, 0x11), beat)
        self.xg_effect(0x42, (0x00, int(clamp(drive, 0, 127))), beat + 1 / PPQ)
        self.xg_effect(0x54, (0x00, int(clamp(dry_wet, 1, 127))), beat + 2 / PPQ)
        self.xg_effect(0x5A, (0x00,), beat + 3 / PPQ)
        self.xg_effect(0x5B, (ch,), beat + 4 / PPQ)
        self.annotate("xg_amp_sim", beat, (ch, drive, dry_wet))

    def marker(self, beat: float, text: str) -> None:
        self.markers.append((beat, text))

    def lyric(self, beat: float, text: str) -> None:
        self.lyrics.append((beat, text))

    def tempo(self, beat: float, bpm: float) -> None:
        self.tempos.append((beat, bpm))

    def timesig(self, beat: float, numerator: int, denominator: int) -> None:
        if denominator <= 0 or denominator & (denominator - 1):
            raise ValueError("MIDI time-signature denominator must be a power of two")
        self.timesigs.append((beat, numerator, denominator))

    def keysig(self, beat: float, sharps: int, minor: bool = False) -> None:
        self.keysigs.append((beat, int(clamp(sharps, -7, 7)), bool(minor)))

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
        """Clamp overlapping repetitions of the same key on the same channel.

        This prevents a note-off belonging to the old note from killing a freshly
        retriggered note.  Simultaneous duplicate starts are collapsed to the louder
        event, preserving an intentionally layered chord on different keys.
        """
        for ch, events in self.events.items():
            starts: dict[int, list[int]] = defaultdict(list)
            ends: dict[int, list[int]] = defaultdict(list)
            for index, event in enumerate(events):
                if len(event.data) < 3:
                    continue
                kind = event.data[0] & 0xF0
                if kind == 0x90 and event.data[2] > 0:
                    starts[event.data[1]].append(index)
                elif kind == 0x80 or (kind == 0x90 and event.data[2] == 0):
                    ends[event.data[1]].append(index)

            remove: set[int] = set()
            for key, note_starts in starts.items():
                note_ends = ends.get(key, [])
                if len(note_starts) != len(note_ends):
                    continue

                # note() appends each on/off pair together. Pair by authoring order
                # before sorting by sounding time, so crossed durations stay attached
                # to the note call that created them.
                note_starts.sort(key=lambda index: events[index].serial)
                note_ends.sort(key=lambda index: events[index].serial)
                pairs = list(zip(note_starts, note_ends))
                pairs.sort(key=lambda pair: (
                    events[pair[0]].event_tick,
                    events[pair[0]].serial,
                ))

                kept: list[tuple[int, int]] = []
                for pair in pairs:
                    if kept and events[kept[-1][0]].event_tick == events[pair[0]].event_tick:
                        old_pair = kept[-1]
                        old_velocity = events[old_pair[0]].data[2]
                        new_velocity = events[pair[0]].data[2]
                        if new_velocity >= old_velocity:
                            remove.update(old_pair)
                            kept[-1] = pair
                        else:
                            remove.update(pair)
                    else:
                        kept.append(pair)

                for (_start, end), (next_start, _next_end) in zip(kept, kept[1:]):
                    next_tick = events[next_start].event_tick
                    if events[end].event_tick > next_tick:
                        events[end].event_tick = next_tick

            if remove:
                self.events[ch] = [event for i, event in enumerate(events) if i not in remove]

    def to_bytes(self, title: str | None = None, comment: str = "") -> bytes:
        self._resolve_overlaps()
        title = title or self.title
        end_tick = tick(self.last_beat) + 2 * PPQ

        def meta(kind: int, payload: bytes) -> bytes:
            return bytes([0xFF, kind]) + _vlq(len(payload)) + payload

        conductor: list[Event] = [Event(0, 0, meta(0x03, title.encode("utf-8")), 0)]
        if comment:
            conductor.append(Event(0, 0, meta(0x01, comment.encode("utf-8")), 1))
        for beat, numerator, denominator in sorted(self.timesigs):
            payload = bytes([numerator & 0xFF, denominator.bit_length() - 1, 24, 8])
            conductor.append(Event(tick(beat), 1, meta(0x58, payload), self._serial + 1))
        for beat, sharps, minor in sorted(self.keysigs):
            payload = struct.pack("bb", sharps, 1 if minor else 0)
            conductor.append(Event(tick(beat), 1, meta(0x59, payload), self._serial + 1))
        for beat, bpm in sorted(self.tempos):
            mpq = int(round(60_000_000 / bpm))
            conductor.append(Event(tick(beat), 2, meta(0x51, mpq.to_bytes(3, "big")), self._serial + 1))
        for beat, text in sorted(self.markers):
            conductor.append(Event(tick(beat), 3, meta(0x06, text.encode("utf-8")), self._serial + 1))
        for beat, text in sorted(self.lyrics):
            conductor.append(Event(tick(beat), 3, meta(0x05, text.encode("utf-8")), self._serial + 1))

        def chunk(events: list[Event], name: str | None) -> bytes:
            body = bytearray()
            if name:
                body += _vlq(0) + meta(0x03, name.encode("utf-8"))
            last = 0
            for event in sorted(events, key=lambda e: (e.event_tick, e.priority, e.serial, e.data)):
                if event.event_tick < last:
                    raise ValueError("MIDI events are out of order")
                body += _vlq(event.event_tick - last) + event.data
                last = event.event_tick
            body += _vlq(max(0, end_tick - last)) + b"\xFF\x2F\x00"
            return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

        chunks = [chunk(conductor, None)]
        for ch in sorted(self.events):
            chunks.append(chunk(self.events[ch], self.names.get(ch, f"Channel {ch + 1}")))
        return b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks)


# ---------------------------------------------------------------------------
# Expressive helpers


def cc_curve(sc: Score, ch: int, number: int, points: Sequence[tuple[float, int]], step: float = 0.5) -> None:
    points = sorted(points)
    for (b0, v0), (b1, v1) in zip(points, points[1:]):
        beat = b0
        while beat < b1 - 1e-9:
            phase = (beat - b0) / max(1e-9, b1 - b0)
            sc.cc(ch, number, int(round(lerp(v0, v1, phase))), beat)
            beat += step
    sc.cc(ch, number, points[-1][1], points[-1][0])


def aftertouch_curve(sc: Score, ch: int, points: Sequence[tuple[float, int]], step: float = 0.5) -> None:
    points = sorted(points)
    for (b0, v0), (b1, v1) in zip(points, points[1:]):
        beat = b0
        while beat < b1 - 1e-9:
            t = (beat - b0) / max(1e-9, b1 - b0)
            sc.aftertouch(ch, int(round(lerp(v0, v1, t))), beat)
            beat += step
    sc.aftertouch(ch, points[-1][1], points[-1][0])


def bend_curve(
    sc: Score,
    ch: int,
    points: Sequence[tuple[float, float]],
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
    phase_offset: float = 0.0,
) -> None:
    offset = 0.0
    while offset <= duration + 1e-9:
        phase = math.sin(2.0 * math.pi * (offset / period + phase_offset))
        value = int(round((lo + hi) * 0.5 + (hi - lo) * 0.5 * phase))
        sc.cc(ch, 10, value, start + offset)
        offset += step
    sc.cc(ch, 10, 64, start + duration)


def expression_pump(
    sc: Score,
    ch: int,
    start: float,
    duration: float,
    low: int = 68,
    high: int = 116,
    beat_step: float = 1.0,
) -> None:
    beat = start
    while beat < start + duration - 1e-9:
        sc.cc(ch, 11, low, beat)
        sc.cc(ch, 11, high, beat + min(0.28, beat_step * 0.35))
        beat += beat_step


def tremolo_cc(
    sc: Score,
    ch: int,
    number: int,
    start: float,
    duration: float,
    lo: int,
    hi: int,
    period: float,
    step: float = 0.25,
) -> None:
    offset = 0.0
    while offset <= duration + 1e-9:
        wave = 0.5 + 0.5 * math.sin(2 * math.pi * offset / period)
        sc.cc(ch, number, int(round(lerp(lo, hi, wave))), start + offset)
        offset += step


def arpeggio(
    sc: Score,
    ch: int,
    notes: Sequence[int],
    start: float,
    duration: float,
    step: float,
    velocity: int,
    order: Sequence[int] = (0, 1, 2, 1, 3, 2, 1, 2),
    gate: float = 0.84,
    octave_cycle: Sequence[int] = (0,),
    tag: str | None = None,
) -> None:
    count = int(round(duration / step))
    for i in range(count):
        base = notes[order[i % len(order)] % len(notes)]
        note = base + 12 * octave_cycle[i % len(octave_cycle)]
        accent = 9 if i % max(1, int(round(4.0 / step))) == 0 else 0
        sc.note(ch, note, start + i * step, step * gate, velocity + accent, jt=1, jv=2, tag=tag)


def pad(sc: Score, ch: int, notes: Sequence[int], start: float, duration: float, velocity: int, tag: str | None = None) -> None:
    for i, note in enumerate(notes):
        delay = i * 0.012
        sc.note(ch, note, start + delay, max(0.05, duration - delay), velocity - 2 * i, jt=1, jv=2, tag=tag)


def strum(
    sc: Score,
    ch: int,
    notes: Sequence[int],
    start: float,
    duration: float,
    velocity: int,
    direction: int = 1,
    spread: float = 0.025,
    tag: str | None = None,
) -> None:
    ordered = sorted(notes, reverse=direction < 0)
    for i, note in enumerate(ordered):
        offset = i * spread
        sc.note(ch, note, start + offset, max(0.05, duration - offset), velocity - i * 2, jt=1, jv=2, tag=tag)


def motif(
    sc: Score,
    ch: int,
    pitches: Sequence[int],
    start: float,
    step: float,
    velocity: int,
    gate: float = 0.86,
    repeats: int = 1,
    transpose_each: int = 0,
    tag: str | None = None,
) -> None:
    for repeat in range(repeats):
        for i, note in enumerate(pitches):
            accent = 8 if i == 0 else 0
            sc.note(
                ch,
                note + repeat * transpose_each,
                start + (repeat * len(pitches) + i) * step,
                step * gate,
                velocity + accent,
                jt=1,
                jv=2,
                tag=tag,
            )


def bass_pattern(
    sc: Score,
    ch: int,
    root: int,
    start: float,
    bars: int,
    progression: Sequence[int],
    velocity: int = 88,
    syncopated: bool = True,
    tag: str | None = None,
) -> None:
    pattern = ((0.0, 0, 0.72), (1.5, 7, 0.34), (2.0, 12, 0.72), (3.25, 7, 0.46)) if syncopated else (
        (0.0, 0, 0.84), (1.0, 7, 0.84), (2.0, 12, 0.84), (3.0, 7, 0.84)
    )
    for bar in range(bars):
        chord_root = root + progression[bar % len(progression)]
        for offset, interval, duration in pattern:
            sc.note(ch, chord_root + interval, start + bar * 4 + offset, duration, velocity, jt=1, jv=3, tag=tag)


def four_on_floor(
    sc: Score,
    start: float,
    bars: int,
    energy: float = 1.0,
    hats: bool = True,
    claps: bool = True,
    ride: bool = False,
    ch: int = 9,
) -> None:
    for bar in range(bars):
        b = start + bar * 4
        for beat_index in range(4):
            sc.hit(36, b + beat_index, int(86 + 22 * energy + (5 if beat_index == 0 else 0)), ch=ch)
        sc.hit(38, b + 1, int(88 + 20 * energy), ch=ch)
        sc.hit(38, b + 3, int(92 + 20 * energy), ch=ch)
        if claps:
            sc.hit(39, b + 1, int(62 + 16 * energy), ch=ch)
            sc.hit(39, b + 3, int(68 + 16 * energy), ch=ch)
        if hats:
            for eighth in range(8):
                key = 46 if eighth == 7 and bar % 4 == 3 else 42
                velocity = int((58 if eighth % 2 else 72) + 13 * energy)
                sc.hit(key, b + eighth * 0.5, velocity, duration=0.1, ch=ch)
        if ride and bar >= bars // 2:
            for q in range(4):
                sc.hit(51, b + q, int(62 + 14 * energy), duration=0.18, ch=ch)
        if bar % 8 == 7:
            for i, key in enumerate((45, 47, 48, 50)):
                sc.hit(key, b + 3.0 + i * 0.25, int(78 + i * 6 + energy * 8), ch=ch)
            sc.hit(49 if bar % 16 == 15 else 55, b + 3.875, int(95 + energy * 15), ch=ch)


def breakbeat(sc: Score, start: float, bars: int, energy: float = 1.0, ch: int = 9) -> None:
    kicks = (0.0, 0.75, 2.0, 2.75)
    snares = (1.0, 3.0)
    for bar in range(bars):
        base = start + bar * 4
        for off in kicks:
            if not (bar % 4 == 2 and off == 0.75):
                sc.hit(36, base + off, int(84 + energy * 24), ch=ch)
        for off in snares:
            sc.hit(38, base + off, int(88 + energy * 25), ch=ch)
        for step in range(16):
            if step % 4 != 0:
                sc.hit(42, base + step * 0.25, int(45 + (step % 4) * 7 + energy * 10), duration=0.07, ch=ch)
        if bar % 4 == 3:
            for i, key in enumerate((41, 43, 45, 47, 48, 50)):
                sc.hit(key, base + 2.5 + i * 0.25, int(72 + i * 6), ch=ch)


def percussion_parade(sc: Score, start: float, ch: int = 9, second_ch: int | None = None) -> None:
    """Use every GM percussion key 35..81 in an eight-bar musical parade."""
    keys = list(range(35, 82))
    # Core groove remains intelligible while the uncommon colors enter as fills.
    four_on_floor(sc, start, 8, energy=0.9, hats=False, claps=False, ride=False, ch=ch)
    for index, key in enumerate(keys):
        target = second_ch if second_ch is not None and key >= 60 else ch
        bar = index // 6
        slot = index % 6
        beat = start + bar * 4 + (0.25, 0.75, 1.5, 2.25, 3.0, 3.5)[slot]
        velocity = 72 + (index * 11) % 38
        sc.hit(key, beat, velocity, duration=0.16 if key < 49 else 0.28, ch=target)
    sc.hit(49, start + 31.75, 122, duration=0.5, ch=ch)
    sc.annotate("percussion_parade", start, tuple(keys))


# ---------------------------------------------------------------------------
# A dependency-free parser used by the composition oracles.


def iter_midi_events(data: bytes) -> Iterator[dict[str, object]]:
    if data[:4] != b"MThd" or len(data) < 14:
        raise ValueError("not a Standard MIDI File")
    header_length, fmt, track_count, division = struct.unpack(">IHHH", data[4:14])
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported")
    pos = 8 + header_length
    yield {"type": "header", "format": fmt, "track_count": track_count, "division": division}
    serial = 0
    for track_index in range(track_count):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError(f"missing MTrk for track {track_index}")
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
                    raise ValueError("running status without prior channel status")
                status = running
            else:
                pos += 1
                if status < 0xF0:
                    running = status
            serial += 1
            base = {"track": track_index, "tick": current, "serial": serial}
            if status == 0xFF:
                kind = data[pos]
                pos += 1
                size, pos = _read_vlq(data, pos)
                payload = data[pos:pos + size]
                pos += size
                yield {**base, "type": "meta", "meta_type": kind, "data": payload}
                continue
            if status in (0xF0, 0xF7):
                size, pos = _read_vlq(data, pos)
                payload = data[pos:pos + size]
                pos += size
                if payload.endswith(b"\xF7"):
                    payload = payload[:-1]
                yield {**base, "type": "sysex", "status": status, "data": payload}
                continue
            kind = status & 0xF0
            ch = status & 0x0F
            if kind in (0xC0, 0xD0):
                d1 = data[pos]
                pos += 1
                event_type = "program" if kind == 0xC0 else "aftertouch"
                yield {**base, "type": event_type, "channel": ch, "value": d1}
            else:
                d1, d2 = data[pos], data[pos + 1]
                pos += 2
                names = {
                    0x80: "note_off", 0x90: "note_on", 0xA0: "poly_aftertouch",
                    0xB0: "cc", 0xE0: "bend",
                }
                event_type = names.get(kind, "channel")
                if event_type == "note_on" and d2 == 0:
                    event_type = "note_off"
                event = {**base, "type": event_type, "channel": ch, "data1": d1, "data2": d2}
                if event_type == "cc":
                    event.update(number=d1, value=d2)
                elif event_type in ("note_on", "note_off"):
                    event.update(note=d1, velocity=d2)
                elif event_type == "poly_aftertouch":
                    event.update(note=d1, value=d2)
                elif event_type == "bend":
                    event.update(value=(d2 << 7) | d1)
                yield event
        if pos != end:
            raise ValueError("MTrk boundary mismatch")


def analyze_midi_bytes(data: bytes) -> dict[str, object]:
    events = list(iter_midi_events(data))
    header = events[0]
    # Type-1 tracks are simultaneous timelines.  `iter_midi_events` yields one
    # complete track at a time for simple parsing, so merge them here before
    # interpreting global reset/SysEx state (notably GS rhythm-part changes).
    timeline = sorted(events[1:], key=lambda event: (int(event["tick"]), int(event["serial"])))
    division = int(header["division"])
    tempo_events: list[tuple[int, int]] = []
    markers: list[tuple[int, str]] = []
    timesigs: list[tuple[int, int, int]] = []
    programs: list[tuple[int, int, int]] = []
    program_notes: dict[int, int] = defaultdict(int)
    program_ticks: dict[int, int] = defaultdict(int)
    controllers: dict[int, int] = defaultdict(int)
    controller_channels: dict[int, set[int]] = defaultdict(set)
    controller_values: dict[int, set[int]] = defaultdict(set)
    channels: set[int] = set()
    drum_notes: set[int] = set()
    sysex: list[bytes] = []
    aftertouch = 0
    poly_aftertouch = 0
    bends = 0
    note_count = 0
    end_tick = 0
    current_program = [0] * 16
    bank_msb = [0] * 16
    bank_lsb = [0] * 16
    drum_mode = [False] * 16
    drum_mode[9] = True
    active: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    # CC120/CC123 terminate sounding notes immediately, but well-formed SMFs still
    # contain their later physical Note Off messages.  Remember how many such offs
    # are expected so the structural oracle does not mislabel them as unmatched.
    suppressed_note_offs: dict[tuple[int, int], int] = defaultdict(int)
    stuck: list[tuple[int, int, int]] = []
    program_change_while_active: list[tuple[int, int, int]] = []
    overlapping_note_ons: list[tuple[int, int, int]] = []
    banked_programs: set[tuple[int, int, int]] = set()

    def parse_gs_drum(payload: bytes) -> tuple[int, bool] | None:
        if (len(payload) == 9 and payload[0] == 0x41 and
                payload[2:5] == bytes([0x42, 0x12, 0x40]) and payload[6] == 0x15):
            block = payload[5] & 0x0F
            ch = 9 if block == 0 else block - 1 if block <= 9 else block
            return ch, payload[7] != 0
        return None

    for event in timeline:
        end_tick = max(end_tick, int(event["tick"]))
        event_type = event["type"]
        if event_type == "meta":
            kind = int(event["meta_type"])
            payload = bytes(event["data"])
            if kind == 0x51 and len(payload) == 3:
                tempo_events.append((int(event["tick"]), int.from_bytes(payload, "big")))
            elif kind == 0x06:
                markers.append((int(event["tick"]), payload.decode("utf-8", "replace")))
            elif kind == 0x58 and len(payload) >= 2:
                timesigs.append((int(event["tick"]), payload[0], 1 << payload[1]))
            continue
        if event_type == "sysex":
            payload = bytes(event["data"])
            sysex.append(payload)
            gs = parse_gs_drum(payload)
            if gs:
                drum_mode[gs[0]] = gs[1]
            if payload[:4] == b"\x7e\x7f\x09\x01":
                current_program = [0] * 16
                bank_msb = [0] * 16
                bank_lsb = [0] * 16
                drum_mode = [False] * 16
                drum_mode[9] = True
            elif (len(payload) == 9 and payload[0] == 0x41 and
                  payload[2:8] == bytes([0x42, 0x12, 0x40, 0x00, 0x7F, 0x00])):
                drum_mode = [False] * 16
                drum_mode[9] = True
            continue
        if "channel" in event:
            channels.add(int(event["channel"]))
        if event_type == "program":
            ch = int(event["channel"])
            if any(active[(ch, key)] for key in range(128)):
                program_change_while_active.append((int(event["tick"]), ch, int(event["value"])))
            current_program[ch] = int(event["value"])
            programs.append((int(event["tick"]), ch, int(event["value"])))
            banked_programs.add((bank_msb[ch], bank_lsb[ch], current_program[ch]))
        elif event_type == "cc":
            ch = int(event["channel"])
            number = int(event["number"])
            value = int(event["value"])
            controllers[number] += 1
            controller_channels[number].add(ch)
            controller_values[number].add(value)
            if number == 0:
                bank_msb[ch] = value
                if value == 127:
                    drum_mode[ch] = True
            elif number == 32:
                bank_lsb[ch] = value
            elif number in (120, 123):
                clear_tick = int(event["tick"])
                for key in range(128):
                    entries = active[(ch, key)]
                    for start, program in entries:
                        if program >= 0:
                            program_ticks[program] += max(0, clear_tick - start)
                    suppressed_note_offs[(ch, key)] += len(entries)
                    entries.clear()
        elif event_type == "note_on":
            ch = int(event["channel"])
            key = int(event["note"])
            note_count += 1
            if active[(ch, key)]:
                overlapping_note_ons.append((int(event["tick"]), ch, key))
            is_drum = ch == 9 or drum_mode[ch] or bank_msb[ch] == 127
            if is_drum:
                drum_notes.add(key)
                active[(ch, key)].append((int(event["tick"]), -1))
            else:
                program = current_program[ch]
                program_notes[program] += 1
                active[(ch, key)].append((int(event["tick"]), program))
                banked_programs.add((bank_msb[ch], bank_lsb[ch], program))
        elif event_type == "note_off":
            ch = int(event["channel"])
            key = int(event["note"])
            if active[(ch, key)]:
                start, program = active[(ch, key)].pop(0)
                if program >= 0:
                    program_ticks[program] += max(0, int(event["tick"]) - start)
            elif suppressed_note_offs[(ch, key)] > 0:
                suppressed_note_offs[(ch, key)] -= 1
            else:
                stuck.append((int(event["tick"]), ch, key))
        elif event_type == "bend":
            bends += 1
        elif event_type == "aftertouch":
            aftertouch += 1
        elif event_type == "poly_aftertouch":
            poly_aftertouch += 1

    unclosed: list[tuple[int, int, int]] = []
    for (ch, key), entries in active.items():
        for start, _program in entries:
            unclosed.append((start, ch, key))

    tempo_events = sorted(tempo_events) or [(0, 500_000)]
    seconds = _seconds_from_ticks(end_tick, tempo_events, division)
    return {
        "format": header["format"],
        "tracks": header["track_count"],
        "division": division,
        "events": len(events) - 1,
        "notes": note_count,
        "channels": sorted(channels),
        "tempo_events": tempo_events,
        "markers": markers,
        "timesigs": timesigs,
        "controllers": dict(sorted(controllers.items())),
        "controller_channels": {key: sorted(value) for key, value in controller_channels.items()},
        "controller_values": {key: sorted(value) for key, value in controller_values.items()},
        "program_events": programs,
        "program_notes": dict(sorted(program_notes.items())),
        "program_beats": {p: round(ticks / division, 3) for p, ticks in sorted(program_ticks.items())},
        "heard_programs": sorted(p for p, count in program_notes.items() if count > 0),
        "banked_programs": sorted(banked_programs),
        "drum_notes": sorted(drum_notes),
        "bends": bends,
        "aftertouch": aftertouch,
        "poly_aftertouch": poly_aftertouch,
        "sysex": sysex,
        "seconds": seconds,
        "end_tick": end_tick,
        "unmatched_note_offs": stuck,
        "unclosed_notes": unclosed,
        "overlapping_note_ons": overlapping_note_ons,
        "program_change_while_active": program_change_while_active,
    }


def analyze_midi(path: Path) -> dict[str, object]:
    return analyze_midi_bytes(path.read_bytes())


def _seconds_from_ticks(ticks: int, tempos: Sequence[tuple[int, int]], division: int) -> float:
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
