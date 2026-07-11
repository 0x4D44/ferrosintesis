#!/usr/bin/env python3
"""Build and verify the five original tracks in *Bright Matter*."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import engine as en
import tracks
import verify

ALBUM = "Bright Matter"
ARTIST = "GPT-5.6"
COMMENT = (
    "Five original instrumental compositions built around vi-V-ii-I, dramatic "
    "two-stage builds, contrastive drops, and a four-theme contrapuntal finale."
)


def clock(seconds: float) -> str:
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def selected_specs(track_number: int | None = None) -> list[en.TrackSpec]:
    specs = list(tracks.SPECS)
    if track_number is not None:
        specs = [spec for spec in specs if spec.number == track_number]
        if not specs:
            raise SystemExit(f"unknown track {track_number}")
    return specs


def build_score(spec: en.TrackSpec) -> en.Score:
    score = en.Score(spec.seed, spec.title, spec.tempo, spec.beats)
    spec.builder(score)
    for channel in list(score.events):
        if channel != 9:
            score.reset_controls(channel, spec.beats - 0.15)
    return score


def build_payloads(track_number: int | None = None) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    built: list[dict[str, object]] = []
    midi_payloads: dict[str, bytes] = {}
    for spec in selected_specs(track_number):
        score = build_score(spec)
        payload = score.to_bytes(spec.title, COMMENT)
        # A second independent build must reproduce the same bytes.
        replay = build_score(spec).to_bytes(spec.title, COMMENT)
        if payload != replay:
            raise RuntimeError(f"{spec.title}: deterministic rebuild mismatch")
        seconds = score.duration_seconds()
        entry = {
            "number": spec.number,
            "title": spec.title,
            "file": f"midi/{spec.filename}",
            "duration_seconds": round(seconds, 2),
            "duration_minutes": round(seconds / 60.0, 2),
            "style": spec.style,
            "concept": spec.concept,
            "tags": list(spec.tags),
            "sections": [
                {
                    "name": name,
                    "start_beat": beat,
                    "start_seconds": round(score.seconds_at(beat), 2),
                    "time": clock(score.seconds_at(beat)),
                }
                for beat, name in sorted(score.markers)
            ],
        }
        built.append({"spec": spec, "score": score, "entry": entry})
        midi_payloads[spec.filename] = payload

    if track_number is None:
        manifest = {
            "album": ALBUM,
            "version": "1.0.0",
            "artist": ARTIST,
            "originality_note": COMMENT,
            "signature_progression": "vi - V - ii - I (6 - 5 - 2 - 1)",
            "track_count": len(built),
            "total_duration_seconds": round(sum(item["entry"]["duration_seconds"] for item in built), 2),
            "total_duration_minutes": round(sum(item["entry"]["duration_seconds"] for item in built) / 60.0, 2),
            "tracks": [item["entry"] for item in built],
        }
        midi_payloads["album_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return built, midi_payloads


def write_outputs(track_number: int | None = None) -> None:
    built, payloads = build_payloads(track_number)
    en.MIDI_DIR.mkdir(parents=True, exist_ok=True)
    for item in built:
        spec = item["spec"]
        path = en.MIDI_DIR / spec.filename
        path.write_bytes(payloads[spec.filename])
        print(f"{spec.number:02d}. {spec.title}: {clock(item['entry']['duration_seconds'])} -> {path}")
    if track_number is None:
        path = en.ALBUM_ROOT / "album_manifest.json"
        path.write_bytes(payloads["album_manifest.json"])
        print(f"Manifest -> {path}")


def verify_outputs(track_number: int | None = None) -> None:
    built, payloads = build_payloads(track_number)
    failures: list[str] = []
    for item in built:
        spec = item["spec"]
        score = item["score"]
        path = en.MIDI_DIR / spec.filename
        if not path.exists():
            failures.append(f"{path} missing; run python build.py first")
        elif path.read_bytes() != payloads[spec.filename]:
            failures.append(f"{path} is stale")
        else:
            parsed = en.parse_midi(path)
            if parsed["notes"] < spec.min_notes:
                failures.append(f"{path}: parsed note count {parsed['notes']} below {spec.min_notes}")
            if parsed["marker_events"] < spec.min_markers:
                failures.append(f"{path}: only {parsed['marker_events']} markers")
            if abs(float(parsed["seconds"]) - score.duration_seconds() - 60.0 / spec.tempo * 2.0) > 4.0:
                # SMF end-of-track intentionally carries two beats of release tail.
                failures.append(f"{path}: parsed duration disagrees with score")
    if track_number is None:
        path = en.ALBUM_ROOT / "album_manifest.json"
        if not path.exists():
            failures.append(f"{path} missing")
        elif path.read_bytes() != payloads["album_manifest.json"]:
            failures.append(f"{path} is stale")

    results = verify.run_all([(item["spec"], item["score"]) for item in built])
    for name, problems in results:
        status = "PASS" if not problems else f"FAIL ({len(problems)})"
        print(f"{name:<52} {status}")
        for problem in problems:
            print(f"    - {problem}")
        failures.extend(f"{name}: {problem}" for problem in problems)
    print()
    if failures:
        print(f"RESULT: FAIL - {len(failures)} failure(s)")
        raise SystemExit(1)
    print("RESULT: PASS - all composition oracles green")


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--track", type=int)
    args = parser.parse_args(argv)
    if args.verify:
        verify_outputs(args.track)
    else:
        write_outputs(args.track)


if __name__ == "__main__":
    main(sys.argv[1:])
