#!/usr/bin/env python3
"""Machine-checkable composition and Ferrosintesis coverage oracles.

These checks deliberately go beyond "the file parses".  They pin the suite's
musical contract: every GM program must actually receive notes, every GM drum key
must sound, expressive controls must carry non-default gestures, and the finale's
four themes must genuinely overlap rather than merely appear somewhere in the
file.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence

import engine as en


@dataclass(frozen=True)
class BuiltTrack:
    spec: en.TrackSpec
    score: en.Score
    payload: bytes
    analysis: dict[str, object]


BASE_SYSEX = {
    "GM System On": bytes.fromhex("7e7f0901"),
    "GS Reset": bytes.fromhex("4110421240007f0041"),
    "XG System On": bytes.fromhex("43104c00007e00"),
    "XG Hall 1": bytes.fromhex("43104c0201000100"),
    "XG Chorus 1": bytes.fromhex("43104c0201204100"),
}


def _controller_values(analysis: dict[str, object], number: int) -> set[int]:
    values = analysis["controller_values"]
    assert isinstance(values, dict)
    return set(values.get(number, []))


def _sysex_set(analysis: dict[str, object]) -> set[bytes]:
    return {bytes(item) for item in analysis["sysex"]}


def _require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition:
        problems.append(message)


def check_track(built: BuiltTrack) -> list[str]:
    spec, score, analysis = built.spec, built.score, built.analysis
    problems: list[str] = []

    _require(analysis["format"] == 1, "must be a type-1 Standard MIDI File", problems)
    _require(analysis["division"] == en.PPQ, f"must use PPQ {en.PPQ}", problems)
    _require(len(analysis["channels"]) >= spec.min_channels,
             f"uses {len(analysis['channels'])} channels; expected at least {spec.min_channels}", problems)
    _require(analysis["notes"] >= spec.min_notes,
             f"has {analysis['notes']} notes; expected at least {spec.min_notes}", problems)
    _require(len(analysis["markers"]) >= spec.min_markers,
             f"has {len(analysis['markers'])} markers; expected at least {spec.min_markers}", problems)
    lo_s, hi_s = spec.duration_window
    _require(lo_s <= analysis["seconds"] <= hi_s,
             f"duration {analysis['seconds']:.2f}s outside {lo_s:.1f}..{hi_s:.1f}s", problems)
    _require(not analysis["unclosed_notes"],
             f"contains {len(analysis['unclosed_notes'])} unclosed note(s)", problems)
    _require(not analysis["unmatched_note_offs"],
             f"contains {len(analysis['unmatched_note_offs'])} unmatched note-off(s)", problems)
    _require(not analysis["overlapping_note_ons"],
             f"contains {len(analysis['overlapping_note_ons'])} same-pitch overlap(s)", problems)
    _require(not analysis["program_change_while_active"],
             f"contains {len(analysis['program_change_while_active'])} patch changes while notes are active", problems)

    sysex = _sysex_set(analysis)
    for name, payload in BASE_SYSEX.items():
        _require(payload in sysex, f"missing {name} SysEx", problems)

    if spec.program_range is not None:
        first, last = spec.program_range
        target = set(range(first, last + 1))
        heard = set(analysis["heard_programs"])
        missing = sorted(target - heard)
        _require(not missing, f"target GM programs never heard: {missing}", problems)
        counts = analysis["program_notes"]
        beats = analysis["program_beats"]
        assert isinstance(counts, dict) and isinstance(beats, dict)
        minimum_notes = 4 if first >= 96 else 24
        minimum_beats = 1.0 if first >= 96 else 8.0
        thin = [(program, counts.get(program, 0)) for program in sorted(target)
                if counts.get(program, 0) < minimum_notes]
        brief = [(program, beats.get(program, 0.0)) for program in sorted(target)
                 if beats.get(program, 0.0) < minimum_beats]
        _require(not thin, f"programs below {minimum_notes} note-ons: {thin}", problems)
        _require(not brief, f"programs below {minimum_beats:g} sounding beats: {brief}", problems)

    # Track-specific musical/performance promises.
    if spec.number == 1:
        _require(any(v >= 64 for v in _controller_values(analysis, 64)), "sustain pedal never opens", problems)
        _require(any(v >= 64 for v in _controller_values(analysis, 66)), "sostenuto never opens", problems)
        _require(any(v >= 64 for v in _controller_values(analysis, 67)), "soft pedal never opens", problems)
        _require(any(v >= 64 for v in _controller_values(analysis, 65)), "portamento switch never opens", problems)
        _require(analysis["bends"] >= 100, "guitar launch needs at least 100 bend events", problems)
        _require(bytes.fromhex("43104c0201404b11") in sysex, "missing XG amp-simulator insertion", problems)
        _require(any(payload[1] == 0 for _, payload in score.annotations.get("rpn", [])),
                 "missing authored RPN 0 bend range", problems)

    elif spec.number == 2:
        vowels = _controller_values(analysis, 70)
        _require({0, 42, 84, 127}.issubset(vowels), "choir does not traverse all four vowel anchors", problems)
        _require(analysis["aftertouch"] >= 1000, "string/brass pressure arc is too sparse", problems)
        _require(analysis["poly_aftertouch"] >= 8, "missing polyphonic pressure accents", problems)
        _require(any(payload[1] == 1 for _, payload in score.annotations.get("rpn", [])),
                 "missing RPN 1 fine-tune ensemble spread", problems)

    elif spec.number == 3:
        _require((int(260 * en.PPQ), 7, 8) in analysis["timesigs"], "missing 7/8 launch section", problems)
        _require(any(v >= 64 for v in _controller_values(analysis, 65)), "lead portamento never switches on", problems)
        _require(any(v > 0 for v in _controller_values(analysis, 84)), "portamento source CC84 is never authored", problems)
        _require(min(_controller_values(analysis, 74)) <= 30 and max(_controller_values(analysis, 74)) >= 124,
                 "pad brightness sweep does not span the intended horizon", problems)
        _require(min(_controller_values(analysis, 71)) <= 30 and max(_controller_values(analysis, 71)) >= 100,
                 "resonance sweep is too narrow", problems)
        _require(analysis["bends"] >= 250, "portamento/bend choreography is too sparse", problems)

    elif spec.number == 4:
        _require(set(analysis["drum_notes"]) == set(range(35, 82)),
                 f"percussion parade must cover GM keys 35..81; got {analysis['drum_notes']}", problems)
        gs_on = bytes.fromhex("411042124019150111")
        gs_off = bytes.fromhex("411042124019150012")
        _require(gs_on in sysex and gs_off in sysex, "missing GS second-rhythm-part on/off pair", problems)
        banked = set(tuple(item) for item in analysis["banked_programs"])
        _require((0, 96, 25) in banked, "owner-recorded mandolin variation never sounds", problems)
        _require((1, 0, 109) in banked, "modeled alternate bagpipe never sounds", problems)
        _require(score.annotations.get("percussion_parade"), "percussion parade annotation missing", problems)

    elif spec.number == 5:
        banked = set(tuple(item) for item in analysis["banked_programs"])
        for patch, name in (
            ((2, 0, 19), "cathedral organ"),
            ((0, 96, 25), "mandolin variation"),
            ((0, 19, 99), "Hollow Release pad"),
        ):
            _require(patch in banked, f"{name} banked patch never sounds", problems)
        _require((int(260 * en.PPQ), 7, 8) in analysis["timesigs"], "missing finale 7/8 ascent", problems)
        _require(any(beat == 568 and sharps == 5 and not minor for beat, sharps, minor in score.keysigs),
                 "missing B-major finale lift", problems)
        tags: dict[str, list[float]] = defaultdict(list)
        for beat, payload in score.annotations.get("note_tag", []):
            tags[str(payload[0])].append(beat)
        four = [tags[name] for name in ("A-counterpoint", "B-counterpoint", "C-counterpoint", "D-counterpoint")]
        _require(all(len(beats) >= 90 for beats in four), "one or more finale themes is under-populated", problems)
        if all(four):
            common_start = max(min(beats) for beats in four)
            common_end = min(max(beats) for beats in four)
            _require(common_end > common_start + 48,
                     "four finale themes do not overlap for a sustained contrapuntal span", problems)
        _require(bytes.fromhex("43104c0201404b11") in sysex, "missing finale XG amp-simulator insertion", problems)
        _require(analysis["aftertouch"] >= 400, "finale pressure choreography is too sparse", problems)

    return problems


def check_suite(built_tracks: Sequence[BuiltTrack]) -> list[str]:
    problems: list[str] = []
    analyses = [item.analysis for item in built_tracks]
    heard = set().union(*(set(a["heard_programs"]) for a in analyses))
    missing_programs = sorted(set(range(128)) - heard)
    _require(not missing_programs, f"suite never sounds GM programs: {missing_programs}", problems)

    all_drums = set().union(*(set(a["drum_notes"]) for a in analyses))
    _require(set(range(35, 82)).issubset(all_drums),
             f"suite misses GM percussion keys: {sorted(set(range(35, 82)) - all_drums)}", problems)

    value_union: dict[int, set[int]] = defaultdict(set)
    for analysis in analyses:
        for number, values in analysis["controller_values"].items():
            value_union[int(number)].update(int(v) for v in values)

    expressive_contract = {
        1: lambda values: max(values, default=0) >= 100,
        2: lambda values: min(values, default=127) <= 60 and max(values, default=0) >= 120,
        5: lambda values: max(values, default=0) >= 80,
        11: lambda values: min(values, default=127) <= 35 and max(values, default=0) >= 120,
        64: lambda values: max(values, default=0) >= 100,
        65: lambda values: 0 in values and 127 in values,
        66: lambda values: 0 in values and 127 in values,
        67: lambda values: 0 in values and 127 in values,
        68: lambda values: 0 in values and 127 in values,
        70: lambda values: {0, 42, 84, 127}.issubset(values),
        71: lambda values: min(values, default=127) <= 30 and max(values, default=0) >= 100,
        74: lambda values: min(values, default=127) <= 24 and max(values, default=0) >= 127,
        84: lambda values: max(values, default=0) >= 64,
        91: lambda values: max(values, default=0) >= 90,
        93: lambda values: max(values, default=0) >= 90,
        94: lambda values: max(values, default=0) >= 75,
    }
    for cc, predicate in expressive_contract.items():
        _require(predicate(value_union[cc]), f"suite does not meaningfully exercise CC{cc}", problems)

    total_bends = sum(int(a["bends"]) for a in analyses)
    total_aftertouch = sum(int(a["aftertouch"]) for a in analyses)
    total_poly = sum(int(a["poly_aftertouch"]) for a in analyses)
    _require(total_bends >= 1000, f"only {total_bends} pitch-bend events", problems)
    _require(total_aftertouch >= 2000, f"only {total_aftertouch} channel-pressure events", problems)
    _require(total_poly >= 12, f"only {total_poly} poly-pressure events", problems)

    banked = set().union(*(set(tuple(item) for item in a["banked_programs"]) for a in analyses))
    for patch in ((2, 0, 19), (0, 96, 25), (0, 19, 99), (1, 0, 109)):
        _require(patch in banked, f"suite never sounds banked patch {patch}", problems)

    rpn_numbers = {int(payload[1]) for item in built_tracks
                   for _, payload in item.score.annotations.get("rpn", [])}
    _require({0, 1}.issubset(rpn_numbers), "suite must exercise RPN 0 bend range and RPN 1 fine tune", problems)

    return problems


def run_all(built_tracks: Sequence[BuiltTrack]) -> list[tuple[str, list[str]]]:
    results = [(item.spec.title, check_track(item)) for item in built_tracks]
    results.append(("ALBUM · every voice / controller coverage", check_suite(built_tracks)))
    return results
