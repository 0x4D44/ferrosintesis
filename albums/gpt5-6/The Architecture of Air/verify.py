"""Musical, routing, and serialized-MIDI oracles for the organ showcase."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import tempfile

import engine as en


ORGAN = 0


def _notes(score: en.Score) -> list[tuple[int, float, float, int, int]]:
    spans: list[tuple[int, float, float, int, int]] = []
    for channel, events in score.events.items():
        pending: dict[int, list[tuple[float, int]]] = defaultdict(list)
        for tick, priority, data in sorted(events, key=lambda event: (event[0], event[1], event[2])):
            status = data[0] & 0xF0
            pitch = data[1] if len(data) > 1 else -1
            beat = tick / en.PPQ
            if status == 0x90 and data[2] > 0:
                pending[pitch].append((beat, data[2]))
            elif status in (0x80, 0x90) and pending[pitch]:
                start, velocity = pending[pitch].pop(0)
                spans.append((channel, start, beat, pitch, velocity))
    return sorted(spans)


def _ccs(score: en.Score, channel: int, controller: int) -> list[tuple[float, int, int]]:
    return sorted(
        (tick / en.PPQ, priority, data[2])
        for tick, priority, data in score.events.get(channel, [])
        if (data[0] & 0xF0) == 0xB0 and data[1] == controller
    )


def _active_cc(score: en.Score, channel: int, controller: int, beat: float) -> int | None:
    value = None
    for event_beat, _priority, event_value in _ccs(score, channel, controller):
        if event_beat > beat:
            break
        value = event_value
    return value


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, pos


def _serialized_channel_events(data: bytes, channel: int) -> list[tuple[int, int, int, int]]:
    """Return (tick, status-nibble, data1, data2) in actual stream order."""
    header_length = int.from_bytes(data[4:8], "big")
    track_count = int.from_bytes(data[10:12], "big")
    pos = 8 + header_length
    found: list[tuple[int, int, int, int]] = []
    for _ in range(track_count):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("missing MTrk chunk")
        length = int.from_bytes(data[pos + 4:pos + 8], "big")
        track = data[pos + 8:pos + 8 + length]
        pos += 8 + length
        cursor = 0
        tick = 0
        running: int | None = None
        while cursor < len(track):
            delta, cursor = _read_vlq(track, cursor)
            tick += delta
            first = track[cursor]
            if first >= 0x80:
                status = first
                cursor += 1
                if status < 0xF0:
                    running = status
            elif running is not None:
                status = running
            else:
                raise ValueError("running status without prior status")
            if status == 0xFF:
                cursor += 1
                size, cursor = _read_vlq(track, cursor)
                cursor += size
                continue
            if status in (0xF0, 0xF7):
                size, cursor = _read_vlq(track, cursor)
                cursor += size
                continue
            kind = status & 0xF0
            count = 1 if kind in (0xC0, 0xD0) else 2
            payload = list(track[cursor:cursor + count])
            cursor += count
            if status & 0x0F == channel:
                found.append((tick, kind, payload[0], payload[1] if count == 2 else 0))
    return found


def check_structure(spec: en.TrackSpec, score: en.Score) -> list[str]:
    failures: list[str] = []
    notes = _notes(score)
    seconds = score.duration_seconds()
    if not spec.duration_window[0] <= seconds <= spec.duration_window[1]:
        failures.append(f"duration {seconds:.1f}s outside {spec.duration_window}")
    if len(notes) < 250:
        failures.append(f"only {len(notes)} note-ons; want >= 250")
    if len({channel for channel, *_rest in notes}) < 4:
        failures.append("fewer than four sounding channels")
    if len(score.markers) != 9:
        failures.append(f"{len(score.markers)} section markers; want 9")
    if len(score.tempos) < 8 or len(score.timesigs) < 8:
        failures.append("tempo/meter map does not articulate every major section")
    return failures


def check_default_organ_route(score: en.Score, midi: bytes) -> list[str]:
    failures: list[str] = []
    bank = _ccs(score, ORGAN, 0)
    if not bank:
        failures.append("organ has no explicit CC0=0 default-bank select")
    if any(value != 0 for _beat, _priority, value in bank):
        failures.append(f"organ selects a nonzero legacy bank: {bank}")
    if any(priority != 0 for _beat, priority, _value in bank):
        failures.append(f"organ CC0 does not have serialization priority 0: {bank}")

    events = _serialized_channel_events(midi, ORGAN)
    bank_index = next((i for i, event in enumerate(events)
                       if event[1] == 0xB0 and event[2:] == (0, 0)), None)
    program_index = next((i for i, event in enumerate(events)
                          if event[1] == 0xC0 and event[2] == 19), None)
    note_index = next((i for i, event in enumerate(events)
                       if event[1] == 0x90 and event[3] > 0), None)
    if bank_index is None or program_index is None or note_index is None:
        failures.append("serialized organ stream lacks CC0=0, GM19, or a note-on")
    elif not bank_index < program_index < note_index:
        failures.append(
            f"serialized route order is bank={bank_index}, program={program_index}, note={note_index}"
        )
    return failures


def check_registers(score: en.Score) -> list[str]:
    failures: list[str] = []
    organ = [note for note in _notes(score) if note[0] == ORGAN]
    exposed = [note for note in organ if note[3] == 36 and note[1] <= 0.01 and note[2] >= 7.5]
    if not exposed:
        failures.append("opening lacks the isolated, held MIDI36 32-foot pedal")
    if sum(1 for note in organ if note[3] <= 36) < 12:
        failures.append("pedal register is underused")
    if sum(1 for note in organ if 48 <= note[3] <= 72) < 120:
        failures.append("principal/manual register is underused")
    if sum(1 for note in organ if note[3] >= 84) < 24:
        failures.append("high mixture register is underused")
    pitches = [note[3] for note in organ]
    if max(pitches) - min(pitches) < 64:
        failures.append(f"organ span is only {max(pitches) - min(pitches)} semitones")
    return failures


def check_wind_and_tremulant(score: en.Score) -> list[str]:
    failures: list[str] = []
    organ = [note for note in _notes(score) if note[0] == ORGAN]
    active = lambda beat: [note for note in organ if note[1] <= beat < note[2]]
    if len(active(256.0)) < 10:
        failures.append(f"wind-load window has only {len(active(256.0))} active organ notes")
    if len(active(263.0)) != 1:
        failures.append(f"wind-recovery window has {len(active(263.0))} active notes; want 1")

    held = {36, 48, 55, 60, 64}
    for beat, expected in ((185.0, 0), (208.0, 112)):
        sounding = {note[3] for note in active(beat)}
        if not held <= sounding:
            failures.append(f"tremulant comparison at beat {beat:g} lacks held chord {sorted(held)}")
        if _active_cc(score, ORGAN, 1, beat) != expected:
            failures.append(
                f"CC1 at beat {beat:g} is {_active_cc(score, ORGAN, 1, beat)}, want {expected}"
            )
    values = [value for _beat, _priority, value in _ccs(score, ORGAN, 1)]
    if not values or min(values) != 0 or max(values) < 100:
        failures.append("CC1 does not span tremulant off through a strong plateau")
    return failures


def check_cathedral_mix(score: en.Score) -> list[str]:
    failures: list[str] = []
    organ_notes = [note for note in _notes(score) if note[0] == ORGAN]
    all_notes = _notes(score)
    if len(organ_notes) / max(1, len(all_notes)) < 0.82:
        failures.append(f"organ owns only {len(organ_notes)}/{len(all_notes)} notes")
    pans = [value for _beat, _priority, value in _ccs(score, ORGAN, 10)]
    if not pans or set(pans) != {64}:
        failures.append(f"organ pan is not fixed at center: {sorted(set(pans))}")
    sends = [value for _beat, _priority, value in _ccs(score, ORGAN, 91)]
    if not sends or max(sends) < 105:
        failures.append("organ never drives the dedicated cathedral room strongly")
    for controller in (93, 94):
        values = [value for _beat, _priority, value in _ccs(score, ORGAN, controller)]
        if not values or any(values):
            failures.append(f"organ CC{controller} must stay authored at zero: {values}")
    bends = [data for _tick, _priority, data in score.events.get(ORGAN, [])
             if (data[0] & 0xF0) == 0xE0 and (data[1] != 0 or data[2] != 64)]
    if bends:
        failures.append("organ uses non-centre pitch bend")
    return failures


def check_arc_and_tail(score: en.Score) -> list[str]:
    failures: list[str] = []
    notes = _notes(score)
    windows = ((0, 40), (40, 104), (104, 176), (176, 240),
               (240, 336), (336, 416), (416, 480))
    energies = [sum(velocity for _ch, on, _off, _pitch, velocity in notes
                    if start <= on < end) for start, end in windows]
    if energies[-1] != max(energies):
        failures.append(f"full-organ section is not the global velocity-sum maximum: {energies}")
    if energies[-1] < energies[0] * 3:
        failures.append(f"climax does not sufficiently exceed the foundation: {energies}")
    last_off = max((off for _ch, _on, off, _pitch, _velocity in notes), default=0.0)
    if last_off > 480.01:
        failures.append(f"a note rings to beat {last_off:.2f}; room-only tail must start at 480")
    if score.last_beat - last_off < 30:
        failures.append(f"only {score.last_beat - last_off:.1f} beats remain for room decay")
    final = [note for note in notes if note[0] == ORGAN and note[1] == 456.0]
    if len(final) < 12 or 36 not in {note[3] for note in final}:
        failures.append("final cadence is not the twelve-note plenum with MIDI36 pedal")
    return failures


def check_hygiene(score: en.Score, midi: bytes) -> list[str]:
    failures: list[str] = []
    notes = _notes(score)
    for channel, start, end, pitch, _velocity in notes:
        if not 24 <= pitch <= 108:
            failures.append(f"ch{channel} pitch {pitch} at {start:.2f} is outside 24..108")
        if end <= start:
            failures.append(f"ch{channel} pitch {pitch} has nonpositive duration")
    by_key: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for channel, start, end, pitch, _velocity in notes:
        by_key[(channel, pitch)].append((start, end))
    for key, spans in by_key.items():
        spans.sort()
        if any(next_start < end - 1e-6 for (_start, end), (next_start, _next_end)
               in zip(spans, spans[1:])):
            failures.append(f"same-pitch overlap remains on ch{key[0]} pitch {key[1]}")

    en.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid", dir=en.BUILD_DIR) as handle:
        handle.write(midi)
        path = Path(handle.name)
    info = en.parse_midi(path)
    path.unlink(missing_ok=True)
    if info["division"] != en.PPQ:
        failures.append(f"serialized PPQ is {info['division']}, want {en.PPQ}")
    if info["notes"] != len(notes):
        failures.append(f"serialized MIDI has {info['notes']} notes, score has {len(notes)}")
    if 19 not in {program for _tick, channel, program in info["programs"] if channel == ORGAN}:
        failures.append("serialized MIDI lacks GM19 on the organ channel")
    return failures[:12]


def run_all(spec: en.TrackSpec, score: en.Score, midi: bytes):
    return [
        ("structure and duration", check_structure(spec, score)),
        ("default cathedral routing", check_default_organ_route(score, midi)),
        ("pedal/principal/mixture registers", check_registers(score)),
        ("wind chest and tremulant", check_wind_and_tremulant(score)),
        ("natural cathedral mix", check_cathedral_mix(score)),
        ("dramatic arc and room tail", check_arc_and_tail(score)),
        ("MIDI hygiene and serialization", check_hygiene(score, midi)),
    ]
