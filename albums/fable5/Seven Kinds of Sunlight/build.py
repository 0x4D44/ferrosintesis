#!/usr/bin/env python3
"""build.py — render or verify *Seven Kinds of Sunlight* (one track).

    python build.py            rebuild the track + album_manifest.json
    python build.py --verify   rebuild the Score in memory, re-parse the
                               written MIDI, and run EVERY oracle.

The seed is fixed so a rebuild is byte-identical.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "Seven Kinds of Sunlight"
TITLE = "Seven Kinds of Sunlight"
FILE = "01 - Seven Kinds of Sunlight.mid"
SEED = 20260708
COMMENT = ("An upbeat, through-written song: verse / pre-chorus / chorus "
           "/ middle-eight in 7/8, 6/8, 4/4 and 5/4, a three-voice "
           "machine-verified chorus counterpoint, a verse canon, and a "
           "gear-change finale. Composed and rendered by Claude Fable 5.")

BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def _clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score() -> tuple[en.Score, list]:
    sc = en.Score(SEED)
    conductor.setup(sc)
    spans = []
    for module, (name, t0, t1) in zip(movements.MODULES,
                                      conductor.MODULE_SPANS):
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
    path = en.MIDI_DIR / FILE
    sc.write(path, TITLE, COMMENT)
    secs = en.parse_midi(path)["seconds"]
    section_map = [
        {"name": name,
         "start_beat": t0, "end_beat": t1,
         "start_seconds": round(sc.seconds_at(t0), 2),
         "end_seconds": round(sc.seconds_at(t1), 2),
         "time": _clock(sc.seconds_at(t0))}
        for name, t0, t1 in conductor.SECTIONS]
    manifest = {
        "album": ALBUM,
        "artist": "Claude Fable 5",
        "style": "upbeat odd-meter pop-prog song: 7/8 verses, 6/8 "
                 "pre-choruses, 5/4 middle-eight, three-voice chorus "
                 "counterpoint, driving bass, drum fills",
        "track_count": 1,
        "total_duration_seconds": round(secs, 2),
        "total_duration_minutes": round(secs / 60, 2),
        "tracks": [{
            "number": 1,
            "title": TITLE,
            "file": f"midi/{FILE}",
            "duration_seconds": round(secs, 2),
            "duration_minutes": round(secs / 60, 2),
            "sections": section_map,
        }],
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"01. {TITLE}: {_clock(secs)}  -> {path.name}")
    for entry in section_map:
        print(f"    {entry['time']:>6}  {entry['name']}")


def verify_album() -> None:
    sc, spans = build_score()
    path = en.MIDI_DIR / FILE
    if not path.exists():
        raise SystemExit(f"ERROR: {path} missing - run "
                         f"`python build.py` first")
    info = en.parse_midi(path)
    print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
          f"{info['tracks']} tracks, {info['notes']} notes, "
          f"{info['tempo_events']} tempo events, "
          f"{info['keysigs']} keysigs, {info['lyrics']} lyrics")
    print()
    results = verify.run_all(sc, info, spans,
                             bounds_whitelist=BOUNDS_WHITELIST)
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
        raise SystemExit(1)
    print("RESULT: PASS - all oracles green")


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify_album()
    elif not sys.argv[1:]:
        build_album()
    else:
        raise SystemExit("usage: python build.py [--verify]")
