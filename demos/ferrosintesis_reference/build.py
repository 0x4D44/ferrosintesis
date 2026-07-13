#!/usr/bin/env python3
"""Build or verify the ferrosintesis reference audition.

    python build.py            # write midi/*.mid + album_manifest.json
    python build.py --verify   # rebuild in memory, compare to disk, run oracles
    python build.py --verify --track N
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import engine as en
import programs as pr
import tracks
import verify

ALBUM = "ferrosintesis Reference Audition"
ARTIST = "ferrosintesis"
COMMENT = (
    "A reference audition: every distinct ferrosintesis voice, drum voice, controller "
    "and alt-bank voicing, one at a time, dry and flat, so each can be heard and "
    "identified. A tool, not a record."
)


def clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def lyrics_for(spec: en.TrackSpec, sc: en.Score) -> str:
    """A scrubbable index for the track, embedded as the opus LYRICS tag by
    render_opus.py. Built from the score's markers, so it can never drift from the
    audio. For the melodic tracks, an appendix lists the aliases folded into a
    canonical slot (rendered once, cross-referenced rather than duplicated)."""
    lines = [f"{ALBUM} - {spec.title}", ""]
    for beat, text in sorted(sc.markers):
        lines.append(f"{clock(sc.seconds_at(beat))}  {text}")
    if spec.number in tracks.MELODIC:
        lo, hi = tracks.MELODIC[spec.number]
        aliased = [(p, c) for p, c in pr.alias_index() if lo <= p <= hi]
        if aliased:
            lines += ["", "Aliases (render identically once dry; auditioned as their canonical voice):"]
            for p, canon in aliased:
                lines.append(f"  GM {p:03d} {pr.GM_NAMES[p]} = GM {canon:03d} {pr.GM_NAMES[canon]}")
    return "\n".join(lines) + "\n"


def selected_specs(track_number: int | None) -> list[en.TrackSpec]:
    specs = list(tracks.SPECS)
    if track_number is not None:
        specs = [s for s in specs if s.number == track_number]
        if not specs:
            raise SystemExit(f"unknown track {track_number}")
    return specs


def build_score(spec: en.TrackSpec) -> en.Score:
    # No trailing reset_controls: each slot resets itself, and the showcase's reset
    # sends CC74=127, which would instantiate the wah filter (engine.rs:1286).
    sc = en.Score(spec.seed, spec.title, spec.tempo, spec.beats)
    sc.timesig(0.0, 4, 4)
    spec.builder(sc)
    return sc


def build_outputs(track_number: int | None = None):
    built = []
    payloads: dict[str, bytes] = {}
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
        }
        built.append({"spec": spec, "score": sc, "track": info})
        payloads[spec.filename] = data
        payloads[f"lyrics/{Path(spec.filename).stem}.txt"] = lyrics_for(spec, sc).encode("utf-8")
    manifest = {
        "album": ALBUM,
        "artist": ARTIST,
        "style": "Dry one-at-a-time audition of every ferrosintesis voice and effect",
        "track_count": len(built),
        "total_duration_seconds": round(sum(b["track"]["duration_seconds"] for b in built), 2),
        "total_duration_minutes": round(sum(b["track"]["duration_seconds"] for b in built) / 60.0, 2),
        "tracks": [b["track"] for b in built],
    }
    payloads["album_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return built, manifest, payloads


def write_outputs() -> None:
    built, _manifest, payloads = build_outputs()
    en.MIDI_DIR.mkdir(parents=True, exist_ok=True)
    (en.ALBUM_ROOT / "lyrics").mkdir(parents=True, exist_ok=True)
    for b in built:
        spec = b["spec"]
        path = en.MIDI_DIR / spec.filename
        path.write_bytes(payloads[spec.filename])
        stem = Path(spec.filename).stem
        (en.ALBUM_ROOT / "lyrics" / f"{stem}.txt").write_bytes(payloads[f"lyrics/{stem}.txt"])
        print(f"{spec.number:02d}. {spec.title}: {clock(b['track']['duration_seconds'])} -> {path}")
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
        stem = Path(spec.filename).stem
        lyric_path = en.ALBUM_ROOT / "lyrics" / f"{stem}.txt"
        expected_lyric = payloads[f"lyrics/{stem}.txt"].decode("utf-8")
        if not lyric_path.exists():
            failures.append(f"{lyric_path} missing; run python build.py first")
        # read_text (not read_bytes) so a CRLF checkout under core.autocrlf=true still
        # matches the LF the generator writes - a text sidecar's line endings are not
        # a meaningful staleness signal, and the manifest check below is normalised too.
        elif lyric_path.read_text(encoding="utf-8") != expected_lyric:
            failures.append(f"{lyric_path} is stale; rebuild before verifying")
    if track_number is None:
        manifest_path = en.ALBUM_ROOT / "album_manifest.json"
        if not manifest_path.exists():
            failures.append(f"{manifest_path} missing; run python build.py first")
        elif manifest_path.read_text(encoding="utf-8") != payloads["album_manifest.json"].decode("utf-8"):
            failures.append(f"{manifest_path} is stale; rebuild before verifying")
    results = verify.run_all([(b["spec"], b["score"]) for b in built], suite=(track_number is None))
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<32} {status}")
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
