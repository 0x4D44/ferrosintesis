"""Musical and structural oracles for *Atlas of Becoming*."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import tempfile

import engine as en

EXPECTED_TAG_COUNTS = {
    "fine-line": 3,
    "world": 1,
    "evolution": 1,
    "day-in-the-life-middle": 1,
    "abbey-road-medley-flow": 1,
    "gpt-history": 1,
    "spy-film-score": 1,
    "free-choice": 5,
}
STICKY_RESETS = {64: 0, 65: 0, 66: 0, 67: 0, 68: 0, 71: 0, 74: 127}


def run_all(spec_scores: list[tuple[en.TrackSpec, en.Score]], suite: bool = True):
    results = []
    for spec, score in spec_scores:
        prefix = f"{spec.number:02d} {spec.title}"
        results.append((f"{prefix} structure", check_structure(spec, score)))
        results.append((f"{prefix} sections", check_sections(spec, score)))
        results.append((f"{prefix} themes", check_features(score)))
        results.append((f"{prefix} expression", check_expression(score)))
        results.append((f"{prefix} hygiene", check_hygiene(spec, score)))
    if suite:
        results.append(("suite brief coverage", check_suite(spec_scores)))
        results.append(("suite palette breadth", check_palette(spec_scores)))
    return results


def note_events(score: en.Score):
    return [
        (tick / en.PPQ, channel, data[1], data[2])
        for channel, events in score.events.items()
        for tick, _priority, data in events
        if (data[0] & 0xF0) == 0x90 and data[2] > 0
    ]


def cc_events(score: en.Score, channel: int, cc: int):
    return sorted(
        (tick / en.PPQ, data[2])
        for tick, _priority, data in score.events.get(channel, [])
        if (data[0] & 0xF0) == 0xB0 and data[1] == cc
    )


def active_cc(score: en.Score, channel: int, cc: int, beat: float) -> int | None:
    value = None
    for event_beat, event_value in cc_events(score, channel, cc):
        if event_beat > beat:
            break
        value = event_value
    return value


def check_structure(spec: en.TrackSpec, score: en.Score) -> list[str]:
    failures: list[str] = []
    notes = note_events(score)
    seconds = score.duration_seconds()
    melodic_channels = {channel for _beat, channel, _pitch, _vel in notes if channel != 9}
    if not spec.duration_window[0] <= seconds <= spec.duration_window[1]:
        failures.append(f"duration {seconds:.1f}s outside {spec.duration_window}")
    if len(notes) < spec.min_notes:
        failures.append(f"only {len(notes)} notes; want >= {spec.min_notes}")
    if len(melodic_channels) < spec.min_channels:
        failures.append(f"only {len(melodic_channels)} melodic channels; want >= {spec.min_channels}")
    if len(score.markers) < spec.min_markers:
        failures.append(f"only {len(score.markers)} named sections; want >= {spec.min_markers}")
    if len(score.tempos) < spec.min_tempo_events:
        failures.append(f"only {len(score.tempos)} tempo events; want >= {spec.min_tempo_events}")
    if len(score.timesigs) < spec.min_meter_events:
        failures.append(f"only {len(score.timesigs)} meter events; want >= {spec.min_meter_events}")
    melodic = [(pitch, vel) for _beat, channel, pitch, vel in notes if channel != 9]
    if melodic and max(p for p, _v in melodic) - min(p for p, _v in melodic) < 30:
        failures.append("pitched arrangement spans less than 30 semitones")
    if melodic and max(v for _p, v in melodic) - min(v for _p, v in melodic) < 24:
        failures.append("velocity palette spans less than 24 levels")

    data = score.to_bytes(spec.title)
    en.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mid", dir=en.BUILD_DIR)
    temp_path = Path(handle.name)
    handle.write(data)
    handle.close()
    info = en.parse_midi(temp_path)
    temp_path.unlink(missing_ok=True)
    if info["division"] != en.PPQ:
        failures.append(f"PPQ {info['division']}, want {en.PPQ}")
    if info["notes"] != len(notes):
        failures.append(f"parsed {info['notes']} notes, Score has {len(notes)}")
    return failures


def check_sections(spec: en.TrackSpec, score: en.Score) -> list[str]:
    failures: list[str] = []
    markers = sorted(score.markers)
    if not markers:
        return ["no section markers"]
    if abs(markers[0][0]) > 1e-6:
        failures.append("first named section does not start at beat 0")
    if any(b < 0 or b >= spec.beats for b, _name in markers):
        failures.append("section marker lies outside the composition")
    if len({name for _beat, name in markers}) != len(markers):
        failures.append("section names are not unique")
    notes = note_events(score)
    densities = []
    for index, (start, _name) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else spec.beats
        if end <= start:
            failures.append("section markers are not strictly increasing")
            continue
        count = sum(1 for beat, _ch, _pitch, _vel in notes if start <= beat < end)
        densities.append(count / (end - start))
    positive = [density for density in densities if density > 0]
    if positive and max(positive) < min(positive) * 1.25:
        failures.append(f"section note densities lack contrast: {[round(v, 2) for v in densities]}")
    return failures


def program_events(score: en.Score, channel: int):
    return sorted(
        (tick / en.PPQ, data[1])
        for tick, _priority, data in score.events.get(channel, [])
        if (data[0] & 0xF0) == 0xC0
    )


def active_program(score: en.Score, channel: int, beat: float) -> int | None:
    program = None
    for event_beat, event_program in program_events(score, channel):
        if event_beat > beat:
            break
        program = event_program
    return program


def check_features(score: en.Score) -> list[str]:
    failures: list[str] = []
    for feature in score.features:
        events = [
            (tick / en.PPQ, data[1])
            for tick, _priority, data in score.events.get(feature.ch, [])
            if (data[0] & 0xF0) == 0x90 and data[2] > 0
            and feature.start <= tick / en.PPQ <= feature.end
        ]
        if len(events) < feature.min_notes:
            failures.append(f"{feature.name}: {len(events)} notes; want >= {feature.min_notes}")
        if feature.programs:
            sounding = {active_program(score, feature.ch, beat) for beat, _pitch in events}
            missing = feature.programs - sounding
            if missing:
                failures.append(f"{feature.name}: missing sounding programs {sorted(missing)}")
        if feature.monophonic:
            by_tick = defaultdict(int)
            for tick, _priority, data in score.events.get(feature.ch, []):
                beat = tick / en.PPQ
                if feature.start <= beat <= feature.end and (data[0] & 0xF0) == 0x90 and data[2] > 0:
                    by_tick[tick] += 1
            if any(count > 1 for count in by_tick.values()):
                failures.append(f"{feature.name}: simultaneous note-ons violate its monophonic declaration")
    return failures


def check_expression(score: en.Score) -> list[str]:
    failures: list[str] = []
    notes = note_events(score)
    expressive = 0
    for channel in score.events:
        expressive += sum(len(cc_events(score, channel, cc)) for cc in (1, 11, 64, 74, 91, 93, 94))
    if expressive < 24:
        failures.append(f"only {expressive} expressive controller events; want >= 24")
    if not score.features:
        failures.append("no recurring theme/feature span declared")
    sustained = defaultdict(list)
    pending: dict[tuple[int, int], list[float]] = defaultdict(list)
    for channel, events in score.events.items():
        for tick, priority, data in sorted(events, key=lambda event: (event[0], event[1], event[2])):
            status = data[0] & 0xF0
            key = (channel, data[1]) if len(data) > 1 else (channel, -1)
            if status == 0x90 and data[2] > 0:
                pending[key].append(tick / en.PPQ)
            elif status == 0x80 and pending[key]:
                start = pending[key].pop(0)
                sustained[channel].append((start, tick / en.PPQ))
    for channel, spans in sustained.items():
        if channel == 9:
            continue
        for start, end in spans:
            if end - start < 3.0:
                continue
            pan = active_cc(score, channel, 10, start)
            if pan is not None and not 44 <= pan <= 84:
                failures.append(f"ch{channel} sustained note at {start:.1f} has off-centre pan {pan}")
                if len(failures) >= 6:
                    return failures
    if len(notes) < 1:
        failures.append("composition is silent")
    return failures


def check_hygiene(spec: en.TrackSpec, score: en.Score) -> list[str]:
    failures: list[str] = []
    notes = note_events(score)
    for beat, channel, pitch, _vel in notes:
        if channel == 9 and not 35 <= pitch <= 81:
            failures.append(f"drum note {pitch} at {beat:.2f} is outside the GM kit")
        if channel != 9 and not 24 <= pitch <= 108:
            failures.append(f"melodic note {pitch} on ch{channel} at {beat:.2f} is outside the musical range")
        if len(failures) >= 8:
            break
    reset_beat = spec.beats - 0.25
    for channel in score.events:
        if channel == 9:
            continue
        for cc, expected in STICKY_RESETS.items():
            nearby = [value for beat, value in cc_events(score, channel, cc) if abs(beat - reset_beat) <= 0.04]
            if not nearby or nearby[-1] != expected:
                failures.append(f"ch{channel} lacks final CC{cc}={expected} reset")
                break
    return failures


def check_suite(spec_scores: list[tuple[en.TrackSpec, en.Score]]) -> list[str]:
    failures: list[str] = []
    specs = [spec for spec, _score in spec_scores]
    if len(specs) != 14:
        failures.append(f"album has {len(specs)} tracks; want 14")
    if [spec.number for spec in specs] != list(range(1, 15)):
        failures.append("track numbers are not exactly 1..14")
    if len({spec.title for spec in specs}) != len(specs):
        failures.append("track titles are not unique")
    counts = {tag: sum(tag in spec.tags for spec in specs) for tag in EXPECTED_TAG_COUNTS}
    for tag, expected in EXPECTED_TAG_COUNTS.items():
        if counts[tag] != expected:
            failures.append(f"tag {tag!r} appears {counts[tag]} times; want {expected}")
    gpt = next((score for spec, score in spec_scores if "gpt-history" in spec.tags), None)
    if gpt is not None and len(gpt.markers) < 12:
        failures.append(f"GPT history has only {len(gpt.markers)} milestone markers; want >= 12")
    medley = next((score for spec, score in spec_scores if "abbey-road-medley-flow" in spec.tags), None)
    if medley is not None and len(medley.markers) < 7:
        failures.append(f"medley has only {len(medley.markers)} linked sections; want >= 7")
    return failures


def check_palette(spec_scores: list[tuple[en.TrackSpec, en.Score]]) -> list[str]:
    programs = set()
    meters = set()
    tempos = set()
    for _spec, score in spec_scores:
        meters.update((num, den) for _beat, num, den in score.timesigs)
        tempos.update(round(bpm) for _beat, bpm in score.tempos)
        for channel, events in score.events.items():
            if channel == 9:
                continue
            programs.update(data[1] for _tick, _priority, data in events if (data[0] & 0xF0) == 0xC0)
    failures = []
    if len(programs) < 28:
        failures.append(f"only {len(programs)} GM programs across the album; want >= 28")
    if len(meters) < 6:
        failures.append(f"only {len(meters)} distinct meters across the album; want >= 6")
    if len(tempos) < 20:
        failures.append(f"only {len(tempos)} distinct tempos across the album; want >= 20")
    return failures
