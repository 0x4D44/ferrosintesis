#!/usr/bin/env python3
"""Build or verify the ferrosintesis feature showcase demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import engine as en
import tracks
import verify

ALBUM = "Synth Feature Showcase"
ARTIST = "OpenAI Codex"
COMMENT = (
    "Original fast instrumental MIDI demos written to exercise ferrosintesis "
    "program families, controllers, stereo staging, and accepted future seams."
)


def clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def selected_specs(track_number: int | None = None) -> list[en.TrackSpec]:
    specs = list(tracks.SPECS)
    if track_number is not None:
        specs = [s for s in specs if s.number == track_number]
        if not specs:
            raise SystemExit(f"unknown track {track_number}")
    return specs


def build_score(spec: en.TrackSpec) -> en.Score:
    sc = en.Score(spec.seed, spec.title, spec.tempo, spec.beats)
    sc.timesig(0.0, 4, 4)
    spec.builder(sc)
    for ch in list(sc.events):
        sc.reset_controls(ch, spec.beats - 0.25)
    return sc


def build_outputs(track_number: int | None = None) -> tuple[list[dict], dict, dict[str, bytes]]:
    built = []
    midi_bytes: dict[str, bytes] = {}
    for spec in selected_specs(track_number):
        sc = build_score(spec)
        data = sc.to_bytes(spec.title, COMMENT)
        info = {
            "number": spec.number,
            "title": spec.title,
            "file": f"midi/{spec.filename}",
            "duration_seconds": round(sc.duration_seconds(), 2),
            "duration_minutes": round(sc.duration_seconds() / 60.0, 2),
            "style": spec.style,
            "features": [
                {
                    "name": f.name,
                    "tier": f.tier,
                    "channel": f.ch,
                    "start_beat": f.start,
                    "end_beat": f.end,
                    "start_seconds": round(sc.seconds_at(f.start), 2),
                    "end_seconds": round(sc.seconds_at(f.end), 2),
                    "programs": sorted(f.programs),
                }
                for f in sc.features
            ],
            "audio_checks": [
                {
                    "name": c.name,
                    "kind": c.kind,
                    "start_seconds": round(sc.seconds_at(c.start), 2),
                    "end_seconds": round(sc.seconds_at(c.end), 2),
                    "ref_start_seconds": None if c.ref_start is None else round(sc.seconds_at(c.ref_start), 2),
                    "ref_end_seconds": None if c.ref_end is None else round(sc.seconds_at(c.ref_end), 2),
                    "threshold": c.threshold,
                    "channel": c.channel,
                }
                for c in sc.audio_checks
            ],
        }
        built.append({"spec": spec, "score": sc, "track": info})
        midi_bytes[spec.filename] = data
    manifest = {
        "album": ALBUM,
        "artist": ARTIST,
        "style": "Fast dramatic ferrosintesis instrument and controller demos",
        "track_count": len(built),
        "total_duration_seconds": round(sum(b["track"]["duration_seconds"] for b in built), 2),
        "total_duration_minutes": round(sum(b["track"]["duration_seconds"] for b in built) / 60.0, 2),
        "tracks": [b["track"] for b in built],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return built, manifest, {**midi_bytes, "album_manifest.json": manifest_bytes}


def write_outputs() -> None:
    built, manifest, payloads = build_outputs()
    en.MIDI_DIR.mkdir(parents=True, exist_ok=True)
    for spec in tracks.SPECS:
        path = en.MIDI_DIR / spec.filename
        path.write_bytes(payloads[spec.filename])
        secs = next(b["track"]["duration_seconds"] for b in built if b["spec"].number == spec.number)
        print(f"{spec.number:02d}. {spec.title}: {clock(secs)} -> {path}")
    (en.ALBUM_ROOT / "album_manifest.json").write_bytes(payloads["album_manifest.json"])
    print(f"Manifest -> {en.ALBUM_ROOT / 'album_manifest.json'}")


def verify_outputs(track_number: int | None = None) -> None:
    built, _manifest, payloads = build_outputs(track_number)
    failures: list[str] = []
    for b in built:
        spec = b["spec"]
        path = en.MIDI_DIR / spec.filename
        if not path.exists():
            failures.append(f"{path} missing; run python build.py first")
        elif path.read_bytes() != payloads[spec.filename]:
            failures.append(f"{path} is stale; rebuild before verifying")
    if track_number is None:
        manifest_path = en.ALBUM_ROOT / "album_manifest.json"
        if not manifest_path.exists():
            failures.append(f"{manifest_path} missing; run python build.py first")
        else:
            actual_manifest = manifest_path.read_text(encoding="utf-8")
            expected_manifest = payloads["album_manifest.json"].decode("utf-8")
            if actual_manifest != expected_manifest:
                failures.append(f"{manifest_path} is stale; rebuild before verifying")
    results = verify.run_all([(b["spec"], b["score"]) for b in built], suite=(track_number is None))
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<34} {status}")
        for fail in fails:
            print(f"    - {fail}")
        failures.extend(f"{name}: {fail}" for fail in fails)
    print()
    if failures:
        print(f"RESULT: FAIL - {len(failures)} failure(s)")
        raise SystemExit(1)
    print("RESULT: PASS - all oracles green")


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--track", type=int, default=None)
    args = ap.parse_args(argv)
    if args.verify:
        verify_outputs(args.track)
    elif args.track is not None:
        raise SystemExit("--track is only valid with --verify")
    else:
        write_outputs()


if __name__ == "__main__":
    main(sys.argv[1:])
