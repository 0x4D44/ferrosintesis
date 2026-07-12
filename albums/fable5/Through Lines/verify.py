"""verify.py — the shared structural-oracle library of *Through Lines*.

Adapted from The Ninth Bell's oracles, but PARAMETERIZED: every check
reads its requirement data from the track module (movements/tNN_*.py)
instead of album-level constants, because each of the fifteen tracks
declares its own grid, palette and discipline.  `run_track(module, sc,
info, spans)` returns [(check_name, failures)]; build.py prefixes the
track tag, prints the table and exits nonzero on any failure.  `info`
may be None (build.py --check): file-dependent checks are then skipped.

The generic disciplines enforced on EVERY track:

  * structure — file duration inside module.DURATION_WINDOW, track
    count (conductor + PART.CHANNELS), file-vs-Score note parity, the
    tempo and key-signature grids, every movement (and extra) marker;
  * programs — every non-drum program (channel setup AND scheduled
    change) inside module.PROGRAM_WHITELIST — the whitelist is the
    single source of truth for what the track may voice;
  * pan — module.CENTERED_CHANNELS emit CC10 64 only;
  * ranges — per-channel note ranges from module.NOTE_RANGES; drums
    inside the GM percussion map 35-81 unless the module lists ch9 in
    NOTE_RANGES explicitly (GM2 keys reach down to 27, so an explicit
    ch9 range is honoured but still clamped to 27-87);
  * gaps — no unscored silence longer than MAX_GAP_BEATS outside
    module.GAP_WHITELIST;
  * overlaps — no same-pitch overlap survives _resolve_overlaps;
  * bend hygiene — every bending channel recentred (+-0.02) at every
    movement boundary, EXCEPT module.BEND_EXEMPT channels (static
    microtuning offsets, e.g. a gamelan tuning), whose bend must
    instead stay CONSTANT within each movement;
  * movement bounds — each builder writes note-ons only inside its own
    movement's beat range (module.BOUNDS_WHITELIST names the
    documented seam carry-overs).

Track-specific oracles live in each module's oracles(sc, info, spans);
a stub returns one honest failure until the track is composed.
"""

from __future__ import annotations

import engine as en

PPQ = en.PPQ
DRUM_CH = 9
GM_PERCUSSION = set(range(35, 82))       # the standard GM percussion map
GM2_PERCUSSION = (27, 87)                # GM2 extends the map downward
MAX_GAP_BEATS = 1.5
_REPORT_CAP = 8


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

def _cc_events(sc, ch, num, lo=0.0, hi=1e12):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[2]))
    return sorted(out)


def _bend_fracs(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _note_spans(sc, ch):
    """[(on_beat, off_beat, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick / PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick / PPQ, data[1], vel))
    for pitch, queue in pending.items():
        for on, vel in queue:
            out.append((on, on, pitch, vel))
    return sorted(out)


def _all_notes(sc):
    out = []
    for ch in sc.events:
        for on, off, pitch, vel in _note_spans(sc, ch):
            out.append((ch, on, off, pitch, vel))
    return out


def _programs(sc, ch):
    return [(tick / PPQ, data[1]) for tick, _prio, data
            in sc.events.get(ch, [])
            if (data[0] & 0xF0) == 0xC0]


def _cap(fails):
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The generic checks (parameterized by the track module)
# ---------------------------------------------------------------------------

def check_structure(module, sc, info):
    part = module.PART
    fails = []
    if info is not None:
        lo, hi = module.DURATION_WINDOW
        if not lo <= info["seconds"] <= hi:
            fails.append(f"duration {info['seconds']:.1f}s outside "
                         f"({lo:.1f}, {hi:.1f})")
        want_tracks = 1 + len(part.CHANNELS)
        if info["tracks"] != want_tracks:
            fails.append(f"{info['tracks']} tracks, want {want_tracks} "
                         f"(conductor + {len(part.CHANNELS)} channels)")
        score_notes = len(_all_notes(sc))
        if info["notes"] != score_notes:
            fails.append(f"file has {info['notes']} notes, Score built "
                         f"{score_notes}")
    if sorted(sc.tempos) != sorted(part.TEMPO_MAP):
        fails.append("tempo map differs from PART.TEMPO_MAP")
    want_keysigs = sorted((b, int(s), 1 if m else 0)
                          for b, s, m in part.KEYSIGS)
    if sorted(sc.keysigs) != want_keysigs:
        fails.append("key signature grid differs from PART.KEYSIGS")
    marker_beats = {b for b, _t in sc.markers}
    for name, t0, _t1 in part.MOVEMENTS:
        if t0 not in marker_beats:
            fails.append(f"missing movement marker '{name}' at beat {t0}")
    for beat, text in part.EXTRA_MARKERS:
        if beat not in marker_beats:
            fails.append(f"missing extra marker '{text}' at beat {beat}")
    return _cap(fails)


def check_programs(module, sc):
    fails = []
    for ch in sorted(sc.events):
        if ch == DRUM_CH:
            continue
        for beat, prog in _programs(sc, ch):
            if prog not in module.PROGRAM_WHITELIST:
                fails.append(f"ch{ch} program {prog} at beat {beat:.1f} "
                             f"not in the track's whitelist")
    return _cap(fails)


def check_bank_select_order(_module, sc):
    """CC0 at a tick must precede Program Change at that same tick."""
    fails = []
    for ch, events in sorted(sc.events.items()):
        by_tick: dict[int, dict[str, list[int]]] = {}
        for tick, priority, data in events:
            status = data[0] & 0xF0
            kind = ("bank" if status == 0xB0 and data[1] == 0 else
                    "program" if status == 0xC0 else None)
            if kind is not None:
                by_tick.setdefault(tick, {"bank": [], "program": []})[kind].append(priority)
        for tick, priorities in by_tick.items():
            if (priorities["bank"] and priorities["program"] and
                    max(priorities["bank"]) >= min(priorities["program"])):
                fails.append(f"ch{ch} tick {tick}: CC0 priority "
                             f"{priorities['bank']} must precede Program Change "
                             f"priority {priorities['program']}")
    return _cap(fails)


def check_pan(module, sc):
    fails = []
    for ch in sorted(module.CENTERED_CHANNELS):
        bad = [(b, v) for b, v in _cc_events(sc, ch, 10) if v != 64]
        if bad:
            fails.append(f"ch{ch} is a centered channel but pans to "
                         f"{bad[:3]} (must stay 64)")
    return _cap(fails)


def check_ranges(module, sc):
    fails = []
    for ch, (lo, hi) in sorted(module.NOTE_RANGES.items()):
        for on, _off, p, _v in _note_spans(sc, ch):
            if not lo <= p <= hi:
                fails.append(f"ch{ch} pitch {p} at beat {on:.1f} outside "
                             f"[{lo},{hi}]")
    if DRUM_CH in module.NOTE_RANGES:
        # An explicit ch9 range was checked above; still clamp to GM2.
        g_lo, g_hi = GM2_PERCUSSION
        for on, _off, p, _v in _note_spans(sc, DRUM_CH):
            if not g_lo <= p <= g_hi:
                fails.append(f"drum note {p} at {on:.1f} outside GM2 "
                             f"percussion [{g_lo},{g_hi}]")
    else:
        for on, _off, p, _v in _note_spans(sc, DRUM_CH):
            if p not in GM_PERCUSSION:
                fails.append(f"drum note {p} at {on:.1f} outside GM range")
    return _cap(fails)


def check_gaps(module, sc, max_gap=MAX_GAP_BEATS):
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: the piece is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            if not any(lo <= horizon and on <= hi
                       for lo, hi in module.GAP_WHITELIST):
                fails.append(f"unscored silence from beat {horizon:.2f} "
                             f"to {on:.2f}")
        horizon = max(horizon, off)
    return _cap(fails)


def check_overlaps(sc):
    sc._resolve_overlaps()
    fails = []
    for ch in sorted(sc.events):
        per_pitch: dict[int, list[tuple[float, float]]] = {}
        for on, off, p, _v in _note_spans(sc, ch):
            per_pitch.setdefault(p, []).append((on, off))
        for p, spans in per_pitch.items():
            spans.sort()
            for (on1, off1), (on2, _off2) in zip(spans, spans[1:]):
                if off1 > on2 + 1e-6:
                    fails.append(f"ch{ch} pitch {p}: note at {on1:.2f} "
                                 f"overlaps re-strike at {on2:.2f}")
    return _cap(fails)


def check_bend_hygiene(module, sc):
    part = module.PART
    fails = []
    boundaries = [t0 for _n, t0, _t1 in part.MOVEMENTS][1:]
    for ch in sorted(sc.events):
        fracs = _bend_fracs(sc, ch)
        if not fracs:
            continue
        if ch in module.BEND_EXEMPT:
            # Static microtuning: the bend may sit off-centre but must
            # not MOVE inside any movement.
            for name, t0, t1 in part.MOVEMENTS:
                vals = [f for b, f in fracs if t0 - 0.05 <= b < t1 - 0.05]
                if vals and max(vals) - min(vals) > 1e-6:
                    fails.append(f"ch{ch} bend moves inside '{name}' "
                                 f"({min(vals):+.3f}..{max(vals):+.3f}); "
                                 f"BEND_EXEMPT channels must hold constant")
            continue
        for t in boundaries:
            state = 0.0
            for b, f in fracs:
                if b > t - 0.05:
                    break
                state = f
            if abs(state) > 0.02:
                fails.append(f"ch{ch} bend not recentred at movement "
                             f"boundary {t} (state {state:+.2f})")
    return _cap(fails)


def check_movement_bounds(spans, whitelist=()):
    fails = []
    for name, t0, t1, notes in spans:
        for ch, beat in notes:
            if t0 - 0.05 <= beat < t1:
                continue
            if any(w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                   for w_ch, lo, hi in whitelist):
                continue
            fails.append(f"'{name}' wrote a ch{ch} note at beat "
                         f"{beat:.2f}, outside [{t0:.0f}, {t1:.0f})")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_track(module, sc, info, spans) -> list[tuple[str, list[str]]]:
    """All generic checks plus the module's own oracles, in table order."""
    results = [
        ("check_structure", check_structure(module, sc, info)),
        ("check_programs", check_programs(module, sc)),
        ("check_bank_select_order", check_bank_select_order(module, sc)),
        ("check_pan", check_pan(module, sc)),
        ("check_ranges", check_ranges(module, sc)),
        ("check_gaps", check_gaps(module, sc)),
        ("check_overlaps", check_overlaps(sc)),
        ("check_bend_hygiene", check_bend_hygiene(module, sc)),
        ("check_movement_bounds", check_movement_bounds(
            spans, whitelist=module.BOUNDS_WHITELIST)),
    ]
    results.extend(module.oracles(sc, info, spans))
    return results
