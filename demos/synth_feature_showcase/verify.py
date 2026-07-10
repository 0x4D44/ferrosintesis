"""Structural MIDI oracles for the ferrosintesis feature showcase."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import tempfile

import engine as en

REQUIRED_PROGRAMS = (
    {0}
    | set(range(4, 15))
    | set(range(16, 24))
    | set(range(24, 40))
    | set(range(40, 56))
    | set(range(56, 88))
    | set(range(88, 104))
    | set(range(104, 112))
    | set(range(120, 128))
)
REQUIRED_CCS = {0, 1, 5, 6, 7, 10, 11, 38, 64, 65, 66, 67, 68, 70, 71, 74, 91, 93, 94, 100, 101}
STICKY_RESETS = {64: 0, 65: 0, 66: 0, 67: 0, 68: 0, 71: 0, 74: 127}


def run_all(spec_scores: list[tuple[en.TrackSpec, en.Score]], suite: bool = True):
    results = []
    for spec, sc in spec_scores:
        prefix = f"{spec.number:02d} {spec.title}"
        results.append((f"{prefix} structure", check_structure(spec, sc)))
        results.append((f"{prefix} features", check_features(sc)))
        results.append((f"{prefix} organ banks", check_organ_banks(sc)))
        results.append((f"{prefix} resets", check_resets(spec, sc)))
        results.append((f"{prefix} stereo", check_stereo(sc)))
        results.append((f"{prefix} arc", check_arc(spec, sc)))
    if suite:
        scores = [sc for _spec, sc in spec_scores]
        results.append(("suite program coverage", check_suite_programs(scores)))
        results.append(("suite controller coverage", check_suite_controllers(scores)))
    return results


def check_structure(spec: en.TrackSpec, sc: en.Score) -> list[str]:
    fails = []
    secs = sc.duration_seconds()
    if not spec.duration_window[0] <= secs <= spec.duration_window[1]:
        fails.append(f"duration {secs:.1f}s outside {spec.duration_window}")
    if not sc.features:
        fails.append("track has no declared feature spans")
    note_count = sum(
        1
        for ev in sc.events.values()
        for _tk, _prio, data in ev
        if (data[0] & 0xF0) == 0x90 and data[2] > 0
    )
    if note_count < 240:
        fails.append(f"only {note_count} notes; not enough arrangement density")
    data = sc.to_bytes(spec.title)
    en.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    tmp_handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mid", dir=en.BUILD_DIR)
    tmp = Path(tmp_handle.name)
    tmp_handle.write(data)
    tmp_handle.close()
    info = en.parse_midi(tmp)
    try:
        tmp.unlink()
    except OSError:
        pass
    if info["division"] != en.PPQ:
        fails.append(f"PPQ {info['division']}, want {en.PPQ}")
    if info["tracks"] != len(sc.events) + 1:
        fails.append(f"{info['tracks']} MIDI tracks, want {len(sc.events) + 1}")
    if info["notes"] != note_count:
        fails.append(f"parsed {info['notes']} notes, Score has {note_count}")
    return fails


def check_features(sc: en.Score) -> list[str]:
    fails = []
    for f in sc.features:
        notes = [
            (on, off, p, v, active_program(sc, f.ch, on))
            for on, off, p, v in note_spans(sc, f.ch)
            if f.start - 1e-6 <= on <= f.end + 1e-6
        ]
        if len(notes) < f.min_notes:
            fails.append(f"{f.name}: {len(notes)} notes, want >= {f.min_notes}")
        if f.programs:
            seen = {prog for *_rest, prog in notes if prog is not None}
            missing = f.programs - seen
            if missing:
                fails.append(f"{f.name}: missing sounding programs {sorted(missing)}")
        for cc, (lo, hi) in f.ccs.items():
            vals = [v for b, v in cc_events(sc, f.ch, cc) if f.start - 1e-6 <= b <= f.end + 1e-6]
            if not vals:
                fails.append(f"{f.name}: no CC{cc} events in feature span")
            elif min(vals) > lo or max(vals) < hi:
                fails.append(f"{f.name}: CC{cc} range {min(vals)}..{max(vals)}, want <= {lo} and >= {hi}")
        if f.bend is not None:
            vals = [v for b, v in bend_events(sc, f.ch) if f.start - 1e-6 <= b <= f.end + 1e-6]
            if not vals:
                fails.append(f"{f.name}: no bend events")
            elif min(vals) > f.bend[0] or max(vals) < f.bend[1]:
                fails.append(f"{f.name}: bend range {min(vals):.2f}..{max(vals):.2f}, want {f.bend}")
        if f.aftertouch is not None:
            vals = [v for b, v in aftertouch_events(sc, f.ch) if f.start - 1e-6 <= b <= f.end + 1e-6]
            if not vals:
                fails.append(f"{f.name}: no aftertouch")
            elif min(vals) > f.aftertouch[0] or max(vals) < f.aftertouch[1]:
                fails.append(f"{f.name}: aftertouch {min(vals)}..{max(vals)}, want {f.aftertouch}")
        if f.monophonic:
            by_tick = defaultdict(int)
            for tk, _prio, data in sc.events.get(f.ch, []):
                beat = tk / en.PPQ
                if f.start - 1e-6 <= beat <= f.end + 1e-6 and (data[0] & 0xF0) == 0x90 and data[2] > 0:
                    by_tick[tk] += 1
            if any(count > 1 for count in by_tick.values()):
                fails.append(f"{f.name}: monophonic feature has chord note-ons")
        if f.drum_kit:
            hits = [n for n in note_spans(sc, 9) if f.start <= n[0] <= f.end]
            if not hits:
                fails.append(f"{f.name}: missing drum hits")
    return fails


def check_organ_banks(sc: en.Score) -> list[str]:
    """Track 2 must demonstrate default GM19, legacy GM19, then reset."""
    bank_events = []
    for ch, events in sc.events.items():
        for tk, prio, data in events:
            if (data[0] & 0xF0) == 0xB0 and data[1] == 0:
                bank_events.append((tk, prio, ch, data[2]))
    if not bank_events:
        return []
    ordered = sorted(bank_events)
    vals = [v for _tk, _prio, _ch, v in ordered]
    fails = []
    if not any(vals[i:i + 3] == [0, 1, 0] for i in range(len(vals) - 2)):
        fails.append(f"organ bank sequence {vals}, want default→legacy→default")
    bad_prio = [(tk, ch, val, prio) for tk, prio, ch, val in ordered if prio != 0]
    if bad_prio:
        fails.append(f"CC0 must serialize at priority 0: {bad_prio}")
    return fails


def check_resets(spec: en.TrackSpec, sc: en.Score) -> list[str]:
    fails = []
    for ch, progs in programs_by_channel(sc).items():
        for beat, _prog in progs:
            if beat <= 0.01:
                continue
            if not has_reset_near(sc, ch, beat):
                fails.append(f"ch{ch} program change at {beat:.2f} lacks reset before reuse")
    end = spec.beats - 0.25
    for ch in sc.events:
        if not has_reset_near(sc, ch, end, window=0.35):
            fails.append(f"ch{ch} lacks final sticky-control reset")
    return fails


def check_stereo(sc: en.Score) -> list[str]:
    fails = []
    for ch in sc.events:
        for on, off, _p, _v in note_spans(sc, ch):
            if off - on < 3.0 or ch == 9:
                continue
            pan = active_cc(sc, ch, 10, on)
            if pan is not None and (pan < 44 or pan > 84):
                fails.append(f"ch{ch} sustained note {on:.1f}-{off:.1f} has off-centre pan {pan}")
                if len(fails) >= 8:
                    return fails
    pan_events = sum(len(cc_events(sc, ch, 10)) for ch in sc.events)
    echo_events = sum(len(cc_events(sc, ch, 94)) for ch in sc.events)
    chorus_events = sum(len(cc_events(sc, ch, 93)) for ch in sc.events)
    if pan_events < 16:
        fails.append(f"only {pan_events} pan events")
    if echo_events < 6:
        fails.append(f"only {echo_events} echo-send events")
    if chorus_events < 6:
        fails.append(f"only {chorus_events} chorus-send events")
    return fails


def check_arc(spec: en.TrackSpec, sc: en.Score) -> list[str]:
    vals = [0, 0, 0, 0]
    for ch in sc.events:
        for on, _off, _p, vel in note_spans(sc, ch):
            idx = min(3, int(on / max(1e-9, spec.beats) * 4))
            vals[idx] += vel
    fails = []
    if max(vals) != vals[2] and max(vals) != vals[3]:
        fails.append(f"climax not in back half: quarter velocity sums {vals}")
    if vals[1] <= vals[0] * 0.85:
        fails.append(f"build does not rise enough: {vals}")
    if max(vals) < vals[0] * 1.35:
        fails.append(f"climax too close to intro: {vals}")
    return fails


def check_suite_programs(scores: list[en.Score]) -> list[str]:
    seen = set()
    for sc in scores:
        for ch in sc.events:
            if ch == 9:
                continue
            seen.update(prog for _b, prog in program_events(sc, ch))
    missing = REQUIRED_PROGRAMS - seen
    return [f"missing programs {sorted(missing)}"] if missing else []


def check_suite_controllers(scores: list[en.Score]) -> list[str]:
    seen_cc = set()
    bends = 0
    ats = 0
    for sc in scores:
        for ch in sc.events:
            for cc in REQUIRED_CCS:
                if cc_events(sc, ch, cc):
                    seen_cc.add(cc)
            bends += len(bend_events(sc, ch))
            ats += len(aftertouch_events(sc, ch))
    fails = []
    missing = REQUIRED_CCS - seen_cc
    if missing:
        fails.append(f"missing CCs {sorted(missing)}")
    if bends < 12:
        fails.append(f"only {bends} pitch-bend events")
    if ats < 8:
        fails.append(f"only {ats} aftertouch events")
    return fails


def note_spans(sc: en.Score, ch: int):
    pending: dict[int, list[tuple[float, int]]] = defaultdict(list)
    out = []
    for tk, prio, data in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1], e[2])):
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending[data[1]].append((tk / en.PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            if pending[data[1]]:
                on, vel = pending[data[1]].pop(0)
                out.append((on, tk / en.PPQ, data[1], vel))
    return out


def program_events(sc: en.Score, ch: int):
    return sorted(
        (tk / en.PPQ, data[1])
        for tk, _prio, data in sc.events.get(ch, [])
        if (data[0] & 0xF0) == 0xC0
    )


def programs_by_channel(sc: en.Score):
    return {ch: program_events(sc, ch) for ch in sc.events if program_events(sc, ch)}


def cc_events(sc: en.Score, ch: int, cc: int):
    return sorted(
        (tk / en.PPQ, data[2])
        for tk, _prio, data in sc.events.get(ch, [])
        if (data[0] & 0xF0) == 0xB0 and data[1] == cc
    )


def bend_events(sc: en.Score, ch: int):
    out = []
    for tk, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tk / en.PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def aftertouch_events(sc: en.Score, ch: int):
    return sorted(
        (tk / en.PPQ, data[1])
        for tk, _prio, data in sc.events.get(ch, [])
        if (data[0] & 0xF0) == 0xD0
    )


def active_program(sc: en.Score, ch: int, beat: float) -> int | None:
    current = None
    for b, prog in program_events(sc, ch):
        if b <= beat + 1e-9:
            current = prog
        else:
            break
    return current


def active_cc(sc: en.Score, ch: int, cc: int, beat: float) -> int | None:
    current = None
    for b, val in cc_events(sc, ch, cc):
        if b <= beat + 1e-9:
            current = val
        else:
            break
    return current


def has_reset_near(sc: en.Score, ch: int, beat: float, window: float = 0.5) -> bool:
    lo = beat - window
    bend_ok = any(abs(v) < 0.01 and lo <= b <= beat + 1e-6 for b, v in bend_events(sc, ch))
    at_ok = any(v == 0 and lo <= b <= beat + 1e-6 for b, v in aftertouch_events(sc, ch))
    cc_ok = True
    for cc, want in STICKY_RESETS.items():
        vals = [v for b, v in cc_events(sc, ch, cc) if lo <= b <= beat + 1e-6]
        if want not in vals:
            cc_ok = False
            break
    return bend_ok and at_ok and cc_ok
