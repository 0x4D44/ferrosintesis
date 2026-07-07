#!/usr/bin/env python3
"""build.py — render or verify *The Ninth Bell* (one track).

    python build.py            rebuild the track + album_manifest.json
    python build.py --verify   rebuild the Score in memory, re-parse the
                               written MIDI, and run EVERY oracle
                               (material + verify.py); prints a pass/fail
                               table and exits nonzero on any failure.
    python build.py --check    in-memory oracles only (no file written or
                               read) — safe to run concurrently while
                               composing movements.

The seed is fixed so a rebuild is byte-identical and --verify reasons
about the same Score that produced the file on disk.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "The Ninth Bell"
TITLE = "The Ninth Bell"
FILE = "01 - The Ninth Bell.mid"
SEED = 20260708
COMMENT = ("A Gabriel-Knight-idiom gothic orchestral piece: the loved "
           "string-chord gesture opens it, one dramatic spring compressed "
           "twice - build, hit, void, rebuild, fracture - and nine bells, "
           "the ninth a lone A. Composed and rendered by Claude Fable 5.")

# Documented seam carry-overs as (ch, lo_beat, hi_beat) note-START
# exemptions for check_movement_bounds.  None needed so far.
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def _clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score() -> tuple[en.Score, list]:
    """Build the full Score; returns (score, per-movement note spans)."""
    sc = en.Score(SEED)
    conductor.setup(sc)
    spans = []
    for module, (name, t0, t1) in zip(movements.MODULES,
                                      conductor.MOVEMENTS):
        before = {ch: len(ev) for ch, ev in sc.events.items()}
        module.build(sc)
        notes = []
        for ch, ev in sc.events.items():
            for tick, _prio, data in ev[before.get(ch, 0):]:
                if (data[0] & 0xF0) == 0x90 and data[2] > 0:
                    notes.append((ch, tick / en.PPQ))
        spans.append((name, t0, t1, notes))
    return sc, spans


def _print_results(results) -> int:
    failed = 0
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<28} {status}")
        for msg in fails:
            print(f"    - {msg}")
        failed += len(fails)
    print()
    if failed:
        print(f"RESULT: FAIL - {failed} failure(s)")
        return 1
    print("RESULT: PASS - all oracles green")
    return 0


def build_album() -> None:
    sc, _spans = build_score()
    path = en.MIDI_DIR / FILE
    sc.write(path, TITLE, COMMENT)
    secs = en.parse_midi(path)["seconds"]
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
        "style": "Gothic orchestral drama in the Gabriel Knight idiom: "
                 "strings, choir, church organ, tubular bells, timpani",
        "track_count": 1,
        "total_duration_seconds": round(secs, 2),
        "total_duration_minutes": round(secs / 60, 2),
        "tracks": [{
            "number": 1,
            "title": TITLE,
            "file": f"midi/{FILE}",
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


def verify_album(in_memory_only: bool = False) -> None:
    sc, spans = build_score()
    info = None
    if not in_memory_only:
        path = en.MIDI_DIR / FILE
        if not path.exists():
            raise SystemExit(f"ERROR: {path} missing - run "
                             f"`python build.py` first")
        info = en.parse_midi(path)
        print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
              f"{info['tracks']} tracks, {info['notes']} notes, "
              f"{info['tempo_events']} tempo events")
        print()
    results = verify.run_all(sc, info, spans,
                             bounds_whitelist=BOUNDS_WHITELIST)
    if _print_results(results):
        raise SystemExit(1)


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify_album()
    elif sys.argv[1:] == ["--check"]:
        verify_album(in_memory_only=True)
    elif not sys.argv[1:]:
        build_album()
    else:
        raise SystemExit("usage: python build.py [--verify | --check]")
