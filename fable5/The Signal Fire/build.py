#!/usr/bin/env python3
"""build.py — render or verify *The Signal Fire*.

    python build.py            rebuild the track + album_manifest.json
    python build.py --verify   rebuild the Score in memory, re-parse the
                               written MIDI, and run EVERY oracle
                               (material + verify.py); prints a pass/fail
                               table and exits nonzero on any failure.

The seed is fixed so a rebuild is byte-identical and --verify can reason
about the same Score that produced the file on disk.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "The Signal Fire"
TITLE = "The Signal Fire"
TRACK_FILE = "01 - The Signal Fire.mid"
SEED = 20260706
COMMENT = ("A single continuous 17-minute instrumental in the Mike Oldfield "
           "idiom: ambient pools igniting into a funk engine, a 10/8 guitar "
           "lattice, the long climb, ascension. "
           "Composed and rendered by Claude Fable 5.")

# Documented seam carry-overs (roadmap section 4) would be added here as
# (ch, lo_beat, hi_beat) note-START exemptions for check_movement_bounds.
# The named seams (pad over 176, strings over 800, pad+bell over 1584/1592)
# are all sustains that START inside their movement, so none is needed yet.
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def _clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score() -> tuple[en.Score, list]:
    """Build the full Score; returns (score, per-movement note spans).

    Runs conductor.setup then each movement module in order, recording the
    note-ons every module wrote so verify.check_movement_bounds can hold
    each one to its own beat range.
    """
    sc = en.Score(SEED)
    conductor.setup(sc)
    spans = []
    for module, (name, t0, t1) in zip(movements.MODULES, conductor.MOVEMENTS):
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
    sc, _spans = build_score()
    path = en.MIDI_DIR / TRACK_FILE
    sc.write(path, TITLE, COMMENT)
    secs = sc.duration_seconds()
    movement_map = [
        {"name": name,
         "start_beat": t0, "end_beat": t1,
         "start_seconds": round(sc.seconds_at(t0), 2),
         "end_seconds": round(sc.seconds_at(t1), 2),
         "time": _clock(sc.seconds_at(t0))}
        for name, t0, t1 in conductor.MOVEMENTS]
    manifest = {
        "album": ALBUM,
        "artist": "Claude Fable 5",
        "style": "single continuous instrumental epic after Mike Oldfield "
                 "(Incantations, The Songs of Distant Earth, Tubular Bells "
                 "III, Guitars)",
        "track_count": 1,
        "total_duration_seconds": round(secs, 2),
        "total_duration_minutes": round(secs / 60, 2),
        "tracks": [{
            "number": 1,
            "title": TITLE,
            "file": f"midi/{TRACK_FILE}",
            "duration_seconds": round(secs, 2),
            "duration_minutes": round(secs / 60, 2),
            "movements": movement_map,
        }],
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"01. {TITLE}: {_clock(secs)}  -> {path.name}")
    for entry in movement_map:
        print(f"    {entry['time']:>6}  {entry['name']}")


def verify_album() -> None:
    sc, spans = build_score()
    path = en.MIDI_DIR / TRACK_FILE
    if not path.exists():
        raise SystemExit(f"ERROR: {path} missing - run `python build.py` first")
    info = en.parse_midi(path)
    print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
          f"{info['tracks']} tracks, {info['notes']} notes, "
          f"{info['tempo_events']} tempo events\n")

    results = verify.run_all(sc, info, spans,
                             bounds_whitelist=BOUNDS_WHITELIST)
    failed = 0
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<24} {status}")
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
