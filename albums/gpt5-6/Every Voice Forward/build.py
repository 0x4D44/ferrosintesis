#!/usr/bin/env python3
"""Build and verify *Every Voice Forward*.

The generator uses only Python's standard library.  MIDI is committed output, but
this source is canonical: a second independent build must reproduce every byte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import engine as en
import tracks
import verify

ALBUM = "Every Voice Forward"
ARTIST = "GPT-5.6"
VERSION = "1.0.0"
COMMENT = (
    "Five original upbeat instrumental compositions written as a Ferrosintesis "
    "showcase: all 128 GM melodic programs, all GM percussion keys 35-81, banked "
    "Ferrosintesis voices, expressive controllers, aftertouch, RPN and modeled SysEx."
)

TRACK_FEATURES: dict[int, tuple[str, ...]] = {
    1: (
        "GM programs 0-31", "sustain", "sostenuto", "soft pedal", "Leslie CC1",
        "portamento", "legato retune", "pitch bends", "resonant filter", "XG amp simulator",
    ),
    2: (
        "GM programs 32-63", "bass orchestra", "fine-tuned string spread", "poly aftertouch",
        "choir vowel morph", "breath", "channel pressure", "brass-up crescendo",
    ),
    3: (
        "GM programs 64-95", "7/8 launch", "RPN bend range", "CC84 portamento source",
        "legato wind slurs", "filter and resonance sweeps", "autopan", "chorus and echo throws",
    ),
    4: (
        "GM programs 96-127", "every GM percussion key 35-81", "GS second rhythm part",
        "mandolin LSB96", "modeled bagpipe alternate", "weather and scene FX", "world ensemble",
    ),
    5: (
        "four simultaneous themes", "7/8 ascent", "B-major key lift", "cathedral organ bank",
        "mandolin variation", "Hollow Release pad", "vowel morph", "fine tune", "XG amp simulator",
    ),
}


def clock(seconds: float) -> str:
    whole = int(round(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


def selected_specs(track_number: int | None = None) -> list[en.TrackSpec]:
    specs = list(tracks.SPECS)
    if track_number is not None:
        specs = [spec for spec in specs if spec.number == track_number]
        if not specs:
            raise SystemExit(f"unknown track {track_number}; choose 1..{len(tracks.SPECS)}")
    return specs


def build_score(spec: en.TrackSpec) -> en.Score:
    score = en.Score(spec.seed, spec.title, spec.tempo, spec.beats)
    spec.builder(score)
    return score


def build_tracks(track_number: int | None = None) -> list[verify.BuiltTrack]:
    built: list[verify.BuiltTrack] = []
    for spec in selected_specs(track_number):
        score = build_score(spec)
        payload = score.to_bytes(spec.title, COMMENT)
        replay = build_score(spec).to_bytes(spec.title, COMMENT)
        if payload != replay:
            raise RuntimeError(f"{spec.title}: deterministic rebuild mismatch")
        analysis = en.analyze_midi_bytes(payload)
        built.append(verify.BuiltTrack(spec, score, payload, analysis))
    return built


def manifest_for(built: list[verify.BuiltTrack]) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for item in built:
        spec, score, analysis = item.spec, item.score, item.analysis
        entry: dict[str, object] = {
            "number": spec.number,
            "title": spec.title,
            "file": f"midi/{spec.filename}",
            "duration_seconds": round(float(analysis["seconds"]), 2),
            "duration_minutes": round(float(analysis["seconds"]) / 60.0, 2),
            "style": spec.style,
            "concept": spec.concept,
            "tags": list(spec.tags),
            "features": list(TRACK_FEATURES[spec.number]),
            "midi": {
                "format": analysis["format"],
                "ppq": analysis["division"],
                "track_chunks": analysis["tracks"],
                "event_count": analysis["events"],
                "note_on_count": analysis["notes"],
                "channels_used": analysis["channels"],
                "marker_count": len(analysis["markers"]),
                "pitch_bend_events": analysis["bends"],
                "channel_pressure_events": analysis["aftertouch"],
                "poly_pressure_events": analysis["poly_aftertouch"],
                "sysex_events": len(analysis["sysex"]),
                "controllers_used": sorted(int(number) for number in analysis["controllers"]),
            },
            "sections": [
                {
                    "name": text,
                    "start_beat": round(tick / en.PPQ, 3),
                    "start_seconds": round(score.seconds_at(tick / en.PPQ), 2),
                    "time": clock(score.seconds_at(tick / en.PPQ)),
                }
                for tick, text in analysis["markers"]
            ],
        }
        if spec.program_range:
            first, last = spec.program_range
            entry["program_coverage"] = {
                "first": first,
                "last": last,
                "first_name": en.GM_PROGRAMS[first],
                "last_name": en.GM_PROGRAMS[last],
                "programs_heard": [p for p in analysis["heard_programs"] if first <= p <= last],
            }
        entries.append(entry)

    total = sum(float(entry["duration_seconds"]) for entry in entries)
    return {
        "album": ALBUM,
        "version": VERSION,
        "artist": ARTIST,
        "year": 2026,
        "originality_note": COMMENT,
        "music_licensing_note": (
            "Music and MIDI are not covered by the repository root MIT/Apache software grant; "
            "choose and record an album-specific music licence before external redistribution."
        ),
        "design_contract": {
            "all_gm_melodic_programs": list(range(128)),
            "all_gm_percussion_keys": list(range(35, 82)),
            "ferrosintesis_banked_voices": [
                {"bank_msb": 2, "bank_lsb": 0, "program": 19, "name": "Cathedral organ"},
                {"bank_msb": 0, "bank_lsb": 96, "program": 25, "name": "Mandolin variation"},
                {"bank_msb": 0, "bank_lsb": 19, "program": 99, "name": "Hollow Release"},
                {"bank_msb": 1, "bank_lsb": 0, "program": 109, "name": "Modeled bagpipe alternate"},
            ],
            "advanced_midi": [
                "CC1 mod / Leslie", "CC2 breath", "CC5 + CC65 + CC84 portamento",
                "CC64 sustain", "CC66 sostenuto", "CC67 soft pedal", "CC68 legato",
                "CC70 vowel morph", "CC71 resonance", "CC74 brightness",
                "CC91 reverb", "CC93 chorus", "CC94 delay", "pitch bend",
                "channel pressure", "polyphonic pressure", "RPN 0 bend range", "RPN 1 fine tune",
                "GM/GS/XG reset", "GS rhythm-part assignment", "XG Hall 1 / Chorus 1 / Amp Simulator",
            ],
        },
        "track_count": len(entries),
        "total_duration_seconds": round(total, 2),
        "total_duration_minutes": round(total / 60.0, 2),
        "tracks": entries,
    }


def generated_payloads(track_number: int | None = None) -> tuple[list[verify.BuiltTrack], dict[str, bytes]]:
    built = build_tracks(track_number)
    payloads = {item.spec.filename: item.payload for item in built}
    if track_number is None:
        manifest = manifest_for(built)
        payloads["album_manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    return built, payloads


def write_outputs(track_number: int | None = None) -> None:
    built, payloads = generated_payloads(track_number)
    en.MIDI_DIR.mkdir(parents=True, exist_ok=True)
    for item in built:
        path = en.MIDI_DIR / item.spec.filename
        path.write_bytes(payloads[item.spec.filename])
        analysis = item.analysis
        print(
            f"{item.spec.number:02d}. {item.spec.title}: {clock(float(analysis['seconds']))}, "
            f"{analysis['notes']:,} notes, {analysis['events']:,} events -> {path}"
        )
    if track_number is None:
        path = en.ALBUM_ROOT / "album_manifest.json"
        path.write_bytes(payloads["album_manifest.json"])
        print(f"Manifest -> {path}")


def verify_outputs(track_number: int | None = None) -> None:
    built, payloads = generated_payloads(track_number)
    failures: list[str] = []

    for item in built:
        path = en.MIDI_DIR / item.spec.filename
        if not path.exists():
            failures.append(f"{path} is missing; run python3 build.py")
        elif path.read_bytes() != payloads[item.spec.filename]:
            failures.append(f"{path} is stale; regenerate it")

    if track_number is None:
        path = en.ALBUM_ROOT / "album_manifest.json"
        if not path.exists():
            failures.append(f"{path} is missing")
        elif path.read_bytes() != payloads["album_manifest.json"]:
            failures.append(f"{path} is stale; regenerate it")

    results = verify.run_all(built)
    for name, problems in results:
        status = "PASS" if not problems else f"FAIL ({len(problems)})"
        print(f"{name:<54} {status}")
        for problem in problems:
            print(f"    - {problem}")
        failures.extend(f"{name}: {problem}" for problem in problems)

    print()
    if failures:
        print(f"RESULT: FAIL — {len(failures)} failure(s)")
        raise SystemExit(1)
    print("RESULT: PASS — deterministic files and all composition oracles are green")


def print_summary(track_number: int | None = None) -> None:
    built = build_tracks(track_number)
    for item in built:
        a = item.analysis
        print(
            f"{item.spec.number:02d}  {item.spec.title:<28} {clock(float(a['seconds'])):>5}  "
            f"notes {a['notes']:>5,}  programs {len(a['heard_programs']):>3}  "
            f"bends {a['bends']:>4}  pressure {a['aftertouch']:>4}"
        )


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="rebuild in memory and run all oracles")
    parser.add_argument("--summary", action="store_true", help="print a compact score summary without writing")
    parser.add_argument("--track", type=int, help="operate on one track number")
    args = parser.parse_args(argv)
    if args.verify:
        verify_outputs(args.track)
    elif args.summary:
        print_summary(args.track)
    else:
        write_outputs(args.track)


if __name__ == "__main__":
    main(sys.argv[1:])
