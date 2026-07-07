#!/usr/bin/env python3
"""build.py — render or verify *Winter Guests* (two tracks).

    python build.py            rebuild both parts + album_manifest.json
    python build.py --verify   rebuild both Scores in memory, re-parse the
                               written MIDI files, and run EVERY oracle
                               (material + verify.py) over both parts;
                               prints a pass/fail table and exits nonzero
                               on any failure.

The per-part seeds are fixed so a rebuild is byte-identical and --verify
can reason about the same Scores that produced the files on disk.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "Winter Guests"
SEEDS = {1: 20260707, 2: 20260708}
PART_MODULES = {1: movements.PART1_MODULES, 2: movements.PART2_MODULES}
COMMENT = ("A two-part instrumental in the Mike Oldfield idiom with two "
           "guest sorties - ABBA's cold sequenced arpeggios and stacked "
           "choruses, and the Crash Test Dummies' low wordless hum. "
           "One theme, three guises. "
           "Composed and rendered by Claude Fable 5.")

# Documented seam carry-overs (roadmap section 4) go here as per-part
# (ch, lo_beat, hi_beat) note-START exemptions for check_movement_bounds.
# The named seams (pad across 256, pad+bell across 884) are sustains that
# START inside their movement, so none is needed yet.
BOUNDS_WHITELISTS: dict[int, list[tuple[int, float, float]]] = {1: [], 2: []}


def _clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score(part: conductor.Part) -> tuple[en.Score, list]:
    """Build one part's full Score; returns (score, per-movement spans).

    Runs part.setup then each of the part's movement modules in order,
    recording the note-ons every module wrote so
    verify.check_movement_bounds can hold each one to its own beat range.
    """
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


def build_album() -> None:
    tracks = []
    for part in conductor.PARTS:
        sc, _spans = build_score(part)
        path = en.MIDI_DIR / part.file
        sc.write(path, part.title, COMMENT)
        # Report the FILE's integrated duration (write() appends a 2-beat
        # end-of-track pad), not just the last musical beat — so the
        # manifest matches what a player reports.
        secs = en.parse_midi(path)["seconds"]
        movement_map = [
            {"name": name,
             "start_beat": t0, "end_beat": t1,
             "start_seconds": round(sc.seconds_at(t0), 2),
             "end_seconds": round(sc.seconds_at(t1), 2),
             "time": _clock(sc.seconds_at(t0))}
            for name, t0, t1 in part.MOVEMENTS]
        tracks.append({
            "number": part.number,
            "title": part.title,
            "file": f"midi/{part.file}",
            "duration_seconds": round(secs, 2),
            "duration_minutes": round(secs / 60, 2),
            "movements": movement_map,
        })
        print(f"{part.number:02d}. {part.title}: {_clock(secs)}  "
              f"-> {path.name}")
        for entry in movement_map:
            print(f"    {entry['time']:>6}  {entry['name']}")
    total = sum(t["duration_seconds"] for t in tracks)
    manifest = {
        "album": ALBUM,
        "artist": "Claude Fable 5",
        "style": "two-part instrumental in the Mike Oldfield idiom with "
                 "ABBA (The Visitors, Super Trouper) and Crash Test "
                 "Dummies (Mmm Mmm Mmm Mmm) guest movements",
        "track_count": len(tracks),
        "total_duration_seconds": round(total, 2),
        "total_duration_minutes": round(total / 60, 2),
        "tracks": tracks,
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total: {total / 60:.2f} minutes")


def verify_album() -> None:
    parts_data = []
    for part in conductor.PARTS:
        sc, spans = build_score(part)
        path = en.MIDI_DIR / part.file
        if not path.exists():
            raise SystemExit(f"ERROR: {path} missing - run "
                             f"`python build.py` first")
        info = en.parse_midi(path)
        print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
              f"{info['tracks']} tracks, {info['notes']} notes, "
              f"{info['tempo_events']} tempo events, "
              f"{info['keysigs']} keysigs, {info['lyrics']} lyrics")
        parts_data.append((part, sc, info, spans))
    print()

    results = verify.run_all(parts_data,
                             bounds_whitelists=BOUNDS_WHITELISTS)
    failed = 0
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<28} {status}")
        for msg in fails:
            print(f"    - {msg}")
        failed += len(fails)
    print()
    if failed:
        print(f"RESULT: FAIL - {failed} failure(s) across "
              f"{sum(1 for _n, f in results if f)} check(s)")
        raise SystemExit(1)
    print("RESULT: PASS - all oracles green")


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify_album()
    elif not sys.argv[1:]:
        build_album()
    else:
        raise SystemExit("usage: python build.py [--verify]")
