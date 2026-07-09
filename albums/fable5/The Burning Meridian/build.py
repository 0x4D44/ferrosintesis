#!/usr/bin/env python3
"""build.py — render or verify *The Burning Meridian* (three tracks).

    python build.py            rebuild both parts + album_manifest.json
    python build.py --verify   rebuild in memory, re-parse the files,
                               run every oracle.

Fixed per-part seeds: rebuilds are byte-identical.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "The Burning Meridian"
SEEDS = {1: 20260711, 2: 20260712, 3: 20260713}
PART_MODULES = movements.PART_MODULES
COMMENT = ("An orchestral film-epic instrumental. One horn theme binds "
           "the album; the brass is a built section (organ + saw stack) "
           "because the synth version used for this album did not yet "
           "model brass. "
           "Composed and rendered by Claude Fable 5.")


def _clock(secs):
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score(part):
    sc = en.Score(SEEDS[part.number])
    part.setup(sc)
    spans = []
    for module, (name, t0, t1) in zip(PART_MODULES[part.number],
                                      part.MOVEMENTS):
        before = {ch: len(ev) for ch, ev in sc.events.items()}
        module.build(sc)
        notes = []
        for ch, ev in sc.events.items():
            for tick, _prio, data in ev[before.get(ch, 0):]:
                if (data[0] & 0xF0) == 0x90 and data[2] > 0:
                    notes.append((ch, tick / en.PPQ))
        spans.append((name, t0, t1, notes))
    return sc, spans


def build_album():
    tracks = []
    for part in conductor.PARTS:
        sc, _spans = build_score(part)
        path = en.MIDI_DIR / part.file
        sc.write(path, part.title, COMMENT)
        secs = en.parse_midi(path)["seconds"]
        movement_map = [
            {"name": name, "start_beat": t0, "end_beat": t1,
             "start_seconds": round(sc.seconds_at(t0), 2),
             "end_seconds": round(sc.seconds_at(t1), 2),
             "time": _clock(sc.seconds_at(t0))}
            for name, t0, t1 in part.MOVEMENTS]
        tracks.append({
            "number": part.number, "title": part.title,
            "file": f"midi/{part.file}",
            "duration_seconds": round(secs, 2),
            "duration_minutes": round(secs / 60, 2),
            "movements": movement_map,
        })
        print(f"{part.number:02d}. {part.title}: {_clock(secs)}")
        for entry in movement_map:
            print(f"    {entry['time']:>6}  {entry['name']}")
    total = sum(t["duration_seconds"] for t in tracks)
    manifest = {
        "album": ALBUM, "artist": "Claude Fable 5",
        "style": "orchestral film-epic instrumentals: 12/8 war build, 3/4 "
                 "elegy, 5/4 battle with a machine-verified theme stack "
                 "and a turn to the major",
        "track_count": len(tracks),
        "total_duration_seconds": round(total, 2),
        "total_duration_minutes": round(total / 60, 2),
        "tracks": tracks,
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total: {total / 60:.2f} minutes")


def verify_album():
    parts_data = []
    for part in conductor.PARTS:
        sc, spans = build_score(part)
        path = en.MIDI_DIR / part.file
        if not path.exists():
            raise SystemExit(f"ERROR: {path} missing")
        info = en.parse_midi(path)
        print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
              f"{info['tracks']} tracks, {info['notes']} notes")
        parts_data.append((part, sc, info, spans))
    print()
    results = verify.run_all(parts_data)
    failed = 0
    for name, fails in results:
        print(f"{name:<28} {'PASS' if not fails else 'FAIL'}")
        for msg in fails:
            print(f"    - {msg}")
        failed += len(fails)
    print()
    if failed:
        print(f"RESULT: FAIL - {failed} failure(s)")
        raise SystemExit(1)
    print("RESULT: PASS - all oracles green")


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify_album()
    elif not sys.argv[1:]:
        build_album()
    else:
        raise SystemExit("usage: python build.py [--verify]")
