#!/usr/bin/env python3
"""build.py — render or verify *The Remaining* (five tracks).

    python build.py                     rebuild all 5 MIDIs into midi/
                                        + album_manifest.json
    python build.py --track N           rebuild only track N (no manifest
                                        write); prints its movement timing
                                        table
    python build.py --verify            rebuild every Score in memory,
                                        re-parse every written MIDI, run
                                        material.verify_material() once plus
                                        verify.run_track() per track; prints
                                        a pass/fail table and exits nonzero
                                        on any failure
    python build.py --track N --verify  verify ONLY track N (plus the
                                        material check) — the composer's
                                        fast loop
    python build.py --track N --check   in-memory oracles only for track N
                                        (no file written or read) — safe to
                                        run while composing
    python build.py --check             in-memory oracles for all tracks

The grid is FEDERATED (see conductor.py): each movements/tNN_*.py module
declares its own SEED, PART, BUILDERS, verification config and oracles;
this file only iterates conductor.REGISTRY / movements.load_tracks() and applies
the shared machinery.  Per-track seeds are fixed so a rebuild is
byte-identical and --verify reasons about the same Scores that produced
the committed files.
"""

from __future__ import annotations

import json
import sys

import conductor
import engine as en
import material
import movements
import verify

USAGE = "usage: python build.py [--track N] [--verify | --check]"


def _clock(secs: float) -> str:
    return f"{int(secs) // 60}:{int(secs) % 60:02d}"


def _module_for(number: int):
    return movements.load_tracks(only=number)[0]


def _default_comment(module) -> str:
    return (f"Track {module.NUMBER:02d} of '{conductor.ALBUM}', an "
            f"album composed and rendered by {conductor.ARTIST}.")


def build_score(module) -> tuple[en.Score, list]:
    """Build one track's full Score; returns (score, per-movement spans).

    Runs module.PART.setup then each of the module's movement builders in
    order, recording the note-ons each one wrote so
    verify.check_movement_bounds can hold every builder to its own beat
    range.
    """
    if len(module.BUILDERS) != len(module.PART.MOVEMENTS):
        raise SystemExit(f"{module.__name__}: {len(module.BUILDERS)} "
                         f"builders for {len(module.PART.MOVEMENTS)} "
                         f"movements")
    sc = en.Score(module.SEED)
    module.PART.setup(sc)
    spans = []
    for builder, (name, t0, t1) in zip(module.BUILDERS,
                                       module.PART.MOVEMENTS):
        before = {ch: len(ev) for ch, ev in sc.events.items()}
        builder(sc)
        notes = []
        for ch, ev in sc.events.items():
            for tick, _prio, data in ev[before.get(ch, 0):]:
                if (data[0] & 0xF0) == 0x90 and data[2] > 0:
                    notes.append((ch, tick / en.PPQ))
        spans.append((name, t0, t1, notes))
    return sc, spans


def build_track(module) -> dict:
    """Rebuild one track's MIDI file; returns its manifest entry."""
    sc, _spans = build_score(module)
    path = en.MIDI_DIR / module.FILE
    sc.write(path, module.TITLE,
             getattr(module, "COMMENT", _default_comment(module)))
    # Report the FILE's integrated duration (write() appends a 2-beat
    # end-of-track pad), not just the last musical beat — so the manifest
    # matches what a player reports.
    secs = en.parse_midi(path)["seconds"]
    movement_map = [
        {"name": name,
         "start_beat": t0, "end_beat": t1,
         "start_seconds": round(sc.seconds_at(t0), 2),
         "end_seconds": round(sc.seconds_at(t1), 2),
         "time": _clock(sc.seconds_at(t0))}
        for name, t0, t1 in module.PART.MOVEMENTS]
    entry = {
        "number": module.NUMBER,
        "title": module.TITLE,
        "file": f"midi/{module.FILE}",
        "duration_seconds": round(secs, 2),
        "duration_minutes": round(secs / 60, 2),
        "movements": movement_map,
    }
    print(f"{module.NUMBER:02d}. {module.TITLE}: {_clock(secs)}  "
          f"-> {path.name}")
    for row in movement_map:
        print(f"    {row['time']:>6}  {row['name']}")
    return entry


def build_album() -> None:
    tracks = [build_track(module) for module in movements.load_tracks()]
    total = sum(t["duration_seconds"] for t in tracks)
    manifest = {
        "album": conductor.ALBUM,
        "artist": conductor.ARTIST,
        "style": conductor.STYLE,
        "track_count": len(tracks),
        "total_duration_seconds": round(total, 2),
        "total_duration_minutes": round(total / 60, 2),
        "tracks": tracks,
    }
    (en.ALBUM_ROOT / "album_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total: {total / 60:.2f} minutes")


def _print_results(results) -> int:
    failed = 0
    for name, fails in results:
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<32} {status}")
        for msg in fails:
            print(f"    - {msg}")
        failed += len(fails)
    print()
    if failed:
        print(f"RESULT: FAIL - {failed} failure(s) across "
              f"{sum(1 for _n, f in results if f)} check(s)")
        return 1
    print("RESULT: PASS - all oracles green")
    return 0


def verify_tracks(mods, in_memory_only: bool = False) -> None:
    """Run the material oracle once, then every oracle for each module."""
    results: list[tuple[str, list[str]]] = [
        ("material", material.verify_material())]
    for module in mods:
        sc, spans = build_score(module)
        info = None
        if not in_memory_only:
            path = en.MIDI_DIR / module.FILE
            if not path.exists():
                raise SystemExit(f"ERROR: {path} missing - run "
                                 f"`python build.py` first")
            info = en.parse_midi(path)
            print(f"{path.name}: {info['seconds'] / 60:.2f} min, "
                  f"{info['tracks']} tracks, {info['notes']} notes, "
                  f"{info['tempo_events']} tempo events")
        tag = f"T{module.NUMBER:02d}"
        for name, fails in verify.run_track(module, sc, info, spans):
            results.append((f"{tag} {name}", fails))
    print()
    if _print_results(results):
        raise SystemExit(1)


def main(argv: list[str]) -> None:
    args = list(argv)
    track_n = None
    if "--track" in args:
        i = args.index("--track")
        try:
            track_n = int(args[i + 1])
        except (IndexError, ValueError):
            raise SystemExit(USAGE)
        del args[i:i + 2]
    do_verify = args.count("--verify") > 0
    do_check = args.count("--check") > 0
    args = [a for a in args if a not in ("--verify", "--check")]
    if args or (do_verify and do_check):
        raise SystemExit(USAGE)
    mods = (movements.load_tracks() if track_n is None
            else [_module_for(track_n)])
    if do_check:
        verify_tracks(mods, in_memory_only=True)
    elif do_verify:
        verify_tracks(mods)
    elif track_n is None:
        build_album()
    else:
        build_track(mods[0])


if __name__ == "__main__":
    main(sys.argv[1:])
