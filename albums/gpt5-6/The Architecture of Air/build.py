#!/usr/bin/env python3
"""Build or verify the single *Architecture of Air* MIDI composition."""

from __future__ import annotations

import argparse
import json
import sys

import composition
import engine as en
import verify


ALBUM = composition.TITLE
ARTIST = "GPT-5.6"
COMMENT = (
    "Original cathedral-organ composition written for the default ferrosintesis "
    "GM19 model: 32-foot pedal, principals, mixtures, shared wind chest, fixed "
    "tremulant, full organ, and a long dedicated-room decay."
)

SPEC = en.TrackSpec(
    1,
    composition.TITLE,
    composition.FILENAME,
    composition.SEED,
    58.0,
    composition.BEATS,
    composition.build,
    "large-form contemporary cathedral organ with sparse choir, bells, and timpani",
    (380.0, 460.0),
)


def clock(seconds: float) -> str:
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def build_score() -> en.Score:
    score = en.Score(SPEC.seed, SPEC.title, SPEC.tempo, SPEC.beats)
    SPEC.builder(score)
    for channel in list(score.events):
        if channel != 9:
            score.reset_controls(channel, SPEC.beats - 0.25)
    return score


def build_payloads() -> tuple[en.Score, bytes, bytes]:
    score = build_score()
    midi = score.to_bytes(SPEC.title, COMMENT)
    seconds = score.duration_seconds()
    manifest = {
        "album": ALBUM,
        "version": "1.0.0",
        "artist": ARTIST,
        "style": SPEC.style,
        "track_count": 1,
        "total_duration_seconds": round(seconds, 2),
        "total_duration_minutes": round(seconds / 60.0, 2),
        "originality_note": "All melodic, harmonic, rhythmic, and formal material is original.",
        "showcase": [
            "velocity-independent pipe sustain and chiff",
            "32-foot pedal energy",
            "principal and high-mixture ranks",
            "same-channel wind-chest load and recovery",
            "fixed 5.5 Hz tremulant",
            "dedicated cathedral room and long decay",
        ],
        "tracks": [{
            "number": 1,
            "title": SPEC.title,
            "file": f"midi/{SPEC.filename}",
            "duration_seconds": round(seconds, 2),
            "duration_minutes": round(seconds / 60.0, 2),
            "style": SPEC.style,
            "sections": [
                {
                    "name": name,
                    "start_beat": beat,
                    "start_seconds": round(score.seconds_at(beat), 3),
                    "time": clock(score.seconds_at(beat)),
                    "tempo_bpm": bpm,
                    "meter": f"{meter[0]}/{meter[1]}",
                }
                for beat, name, bpm, meter in composition.SECTIONS
            ],
            "audio_windows": {
                name: {
                    "start_beat": start,
                    "end_beat": end,
                    "start_seconds": round(score.seconds_at(start), 3),
                    "end_seconds": round(score.seconds_at(end), 3),
                }
                for name, (start, end) in composition.AUDIO_WINDOWS.items()
            },
        }],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return score, midi, manifest_bytes


def write_outputs() -> None:
    score, midi, manifest = build_payloads()
    en.MIDI_DIR.mkdir(parents=True, exist_ok=True)
    midi_path = en.MIDI_DIR / SPEC.filename
    midi_path.write_bytes(midi)
    (en.ALBUM_ROOT / "album_manifest.json").write_bytes(manifest)
    print(f"01. {SPEC.title}: {clock(score.duration_seconds())} -> {midi_path}")
    print(f"Manifest -> {en.ALBUM_ROOT / 'album_manifest.json'}")


def verify_outputs() -> None:
    score, midi, manifest = build_payloads()
    failures: list[str] = []
    midi_path = en.MIDI_DIR / SPEC.filename
    manifest_path = en.ALBUM_ROOT / "album_manifest.json"
    if not midi_path.exists():
        failures.append(f"{midi_path} missing; run python build.py first")
    elif midi_path.read_bytes() != midi:
        failures.append(f"{midi_path} is stale; rebuild before verifying")
    if not manifest_path.exists():
        failures.append(f"{manifest_path} missing; run python build.py first")
    elif manifest_path.read_text(encoding="utf-8") != manifest.decode("utf-8"):
        failures.append(f"{manifest_path} is stale; rebuild before verifying")

    for name, problems in verify.run_all(SPEC, score, midi):
        status = "PASS" if not problems else f"FAIL ({len(problems)})"
        print(f"{name:<36} {status}")
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
    args = parser.parse_args(argv)
    if args.verify:
        verify_outputs()
    else:
        write_outputs()


if __name__ == "__main__":
    main(sys.argv[1:])
