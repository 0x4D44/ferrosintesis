#!/usr/bin/env python3
"""build.py — render or verify *Tuxedo Noir* (one track).

    python build.py            rebuild the track + album_manifest.json
    python build.py --verify   rebuild in memory and run every oracle.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import movements
import verify

ALBUM = "Tuxedo Noir"
TITLE = "Tuxedo Noir"
FILE = "01 - Tuxedo Noir.mid"
SEED = 20260714
COMMENT = ("A spy-idiom instrumental: swung walking vamp, twang-guitar "
           "theme against a built horn-stab counterline, a 12/8 velvet "
           "middle, a 7/8 chase, and a minor-major-9 final ring. "
           "Original material; it quotes no existing piece. "
           "Composed and rendered by Claude Fable 5.")


class _Track:
    """Part-shaped shim so verify.run_all can treat the single track
    like the multi-part albums do."""
    number = 1
    MOVEMENTS = conductor.MOVEMENTS


def _clock(secs):
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def build_score():
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


def build_album():
    sc, _spans = build_score()
    path = en.MIDI_DIR / FILE
    sc.write(path, TITLE, COMMENT)
    secs = en.parse_midi(path)["seconds"]
    section_map = [
        {"name": name, "start_beat": t0, "end_beat": t1,
         "start_seconds": round(sc.seconds_at(t0), 2),
         "end_seconds": round(sc.seconds_at(t1), 2),
         "time": _clock(sc.seconds_at(t0))}
        for name, t0, t1 in conductor.MOVEMENTS]
    manifest = {
        "album": ALBUM, "artist": "Claude Fable 5",
        "style": "spy-idiom instrumental: swung vamp, twang theme vs "
                 "horn stabs (verified counterpoint), 12/8 velvet, "
                 "7/8 chase, min-maj9 ring",
        "track_count": 1,
        "total_duration_seconds": round(secs, 2),
        "total_duration_minutes": round(secs / 60, 2),
        "tracks": [{
            "number": 1, "title": TITLE, "file": f"midi/{FILE}",
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


def verify_album():
    sc, spans = build_score()
    path = en.MIDI_DIR / FILE
    if not path.exists():
        raise SystemExit(f"ERROR: {path} missing")
    info = en.parse_midi(path)
    print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
          f"{info['tracks']} tracks, {info['notes']} notes")
    print()
    results = verify.run_all([(_Track(), sc, info, spans)])
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
