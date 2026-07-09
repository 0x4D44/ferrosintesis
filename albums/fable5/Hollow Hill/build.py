#!/usr/bin/env python3
"""build.py — render or verify *Hollow Hill*.

    python build.py            rebuild both parts + album_manifest.json
    python build.py --verify   structural check of the rendered MIDI
"""

from __future__ import annotations

import json
import sys

import engine as en
import part_one
import part_two

ALBUM = "Hollow Hill"
TRACKS = [
    (1, "Hollow Hill, Part One", part_one.build, 20260701),
    (2, "Hollow Hill, Part Two", part_two.build, 20260702),
]
COMMENT = ("An instrumental epic in two parts, after the school of Mike Oldfield. "
           "Composed and rendered by Claude Fable 5.")


def midi_path(number: int, title: str):
    return en.MIDI_DIR / f"{number:02d} - {title}.mid"


def build_track(number: int) -> dict:
    num, title, builder, seed = TRACKS[number - 1]
    sc = en.Score(seed)
    builder(sc)
    path = midi_path(num, title)
    sc.write(path, title, COMMENT)
    secs = sc.duration_seconds()
    sections = [{"time": f"{int(sc.seconds_at(b)) // 60}:{int(sc.seconds_at(b)) % 60:02d}",
                 "seconds": round(sc.seconds_at(b), 1), "name": text}
                for b, text in sorted(sc.markers)]
    print(f"{num:02d}. {title}: {int(secs) // 60}:{secs % 60:04.1f}  -> {path.name}")
    return {"number": num, "title": title, "file": f"midi/{path.name}",
            "duration_seconds": round(secs, 2),
            "duration_minutes": round(secs / 60, 2), "sections": sections}


def build_album() -> None:
    infos = [build_track(number) for number, *_ in TRACKS]
    total = sum(i["duration_seconds"] for i in infos)
    manifest = {
        "album": ALBUM,
        "artist": "Claude Fable 5",
        "style": "two-part instrumental epic after Mike Oldfield "
                 "(Tubular Bells I/II/III, Amarok, The Songs of Distant Earth)",
        "track_count": len(infos),
        "total_duration_seconds": round(total, 2),
        "total_duration_minutes": round(total / 60, 2),
        "tracks": infos,
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total: {total / 60:.2f} minutes")


def verify_album() -> None:
    manifest = json.loads((en.ALBUM_ROOT / "album_manifest.json").read_text("utf-8"))
    errors: list[str] = []
    for entry in manifest["tracks"]:
        path = en.ALBUM_ROOT / entry["file"]
        if not path.exists():
            errors.append(f"missing {entry['file']}")
            continue
        info = en.parse_midi(path)
        if info["format"] != 1:
            errors.append(f"{path.name}: format {info['format']}, expected 1")
        if info["ppq"] != en.PPQ:
            errors.append(f"{path.name}: ppq {info['ppq']}, expected {en.PPQ}")
        if info["tracks"] < 12:
            errors.append(f"{path.name}: only {info['tracks']} MIDI tracks")
        if info["notes"] < 3000:
            errors.append(f"{path.name}: only {info['notes']} notes")
        if abs(info["seconds"] - entry["duration_seconds"]) > 3.0:
            errors.append(f"{path.name}: duration {info['seconds']:.1f}s vs "
                          f"manifest {entry['duration_seconds']:.1f}s")
        print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
              f"{info['tracks']} tracks, {info['notes']} notes, "
              f"{info['tempo_events']} tempo events")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        raise SystemExit(1)
    print("Verified OK.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify_album()
    elif not sys.argv[1:]:
        build_album()
    else:
        raise SystemExit("usage: python build.py [--verify]")
