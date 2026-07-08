"""verify.py — structural oracles for *Heliopause* (two parts).

The Jarre-specific requirements: the sequencer's filter must actually
MOVE (CC74/71 inventories per movement), leads glide (portamento
paired and off at the seams), The Drop's theremin may widen its bend
range to 12 only inside its window, sudden drops are real (mean
velocity of Drop/Eclipse below their surrounding peaks), and Part
Two's polymeter/detune voices are present.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ
CH = conductor

EXPECTED_TRACKS = 17
GM_PERCUSSION = set(range(35, 82))
MAX_GAP_BEATS = 1.0
_REPORT_CAP = 8

NOTE_RANGES = {
    CH.CH_EP:       (33, 100),
    CH.CH_PAD:      (33, 96),
    CH.CH_SEQ:      (45, 100),
    CH.CH_BASS:     (26, 62),
    CH.CH_LEAD:     (52, 96),
    CH.CH_STRINGS:  (33, 96),
    CH.CH_CHOIR:    (45, 90),
    CH.CH_THEREMIN: (55, 100),
    CH.CH_CRYSTAL:  (57, 108),
    CH.CH_SEQ2:     (57, 108),
    CH.CH_ORGAN:    (40, 88),
    CH.CH_GLOCK:    (60, 108),
    CH.CH_NYLON:    (45, 88),
    CH.CH_FLUTE:    (55, 100),
    CH.CH_BELL:     (45, 92),
}

PART_CONFIG = {
    1: dict(
        duration=(280.0, 320.0),
        timesig_grid=[(0.0, 4, 4), (192.0, 3, 4), (264.0, 4, 4)],
        keysig_grid=[(0.0, 0, 1)],
        min_tempo_events=4,
        cc_inventory=[
            (CH.CH_SEQ, 74,  48.0, 192.0, 10, "rise",
             "M2 sequencer filter opening"),
            (CH.CH_SEQ, 71,  48.0, 192.0,  6, None,
             "M2 sequencer resonance ride"),
            (CH.CH_PAD, 74,   0.0,  48.0,  6, None,
             "M1 pad wind (CC74 LFO)"),
            (CH.CH_ORGAN, 1, 344.0, 420.0,  6, "rise",
             "M5 organ Leslie spin-up"),
            (CH.CH_SEQ, 74, 488.0, 552.0,  4, "fall",
             "M6 sequencer filter closing"),
        ],
        vowel_sections=[(CH.CH_CHOIR, 144.0, 192.0, "hum"),
                        (CH.CH_CHOIR, 280.0, 344.0, "chorus")],
        portamento=[(CH.CH_LEAD, 112.0, 192.0, 194.0),
                    (CH.CH_THEREMIN, 264.0, 344.0, 346.0),
                    (CH.CH_BASS, 264.0, 344.0, 346.0),
                    (CH.CH_LEAD, 344.0, 488.0, 490.0)],
        rpn_windows=[(CH.CH_THEREMIN, 264.0, 346.0, 12.0)],
        rpn_reset_by={CH.CH_THEREMIN: 346.0},
        fine_tune_expect=[],
        bend_recenter=[192.0, 264.0, 346.0, 488.0, 552.0],
        aftertouch_min=[(CH.CH_PAD, 30), (CH.CH_CHOIR, 30)],
        vel_chain=["Solar Wind", "The Sequencer", "Two Suns"],
        quieter_than_peak=["Mirror Waltz", "The Drop", "Dissolve"],
        density_peak="Two Suns",
    ),
    2: dict(
        duration=(215.0, 250.0),
        timesig_grid=[(0.0, 4, 4), (36.0, 6, 8), (180.0, 4, 4),
                      (228.0, 6, 8), (276.0, 4, 4)],
        keysig_grid=[(0.0, 0, 1)],
        min_tempo_events=4,
        cc_inventory=[
            (CH.CH_SEQ, 74,  36.0, 180.0, 10, None,
             "M2 sequencer wah motion"),
            (CH.CH_SEQ, 74,   0.0,  36.0,  6, "rise",
             "M1 ignition sweep"),
            (CH.CH_ORGAN, 1, 276.0, 340.0,  6, "rise",
             "M5 organ Leslie spin-up"),
            (CH.CH_SEQ, 74, 404.0, 460.0,  4, "fall",
             "M6 filter closing"),
            (CH.CH_SEQ, 71, 276.0, 404.0,  6, None,
             "M5 resonance ride"),
        ],
        vowel_sections=[(CH.CH_CHOIR, 228.0, 276.0, "chorus")],
        portamento=[(CH.CH_LEAD, 36.0, 180.0, 182.0),
                    (CH.CH_LEAD, 228.0, 276.0, 278.0),
                    (CH.CH_BASS, 404.0, 460.0, 460.0)],
        rpn_windows=[],
        rpn_reset_by={},
        fine_tune_expect=[(CH.CH_SEQ2, 274.0, 284.0, 3.0, 9.0)],
        bend_recenter=[36.0, 180.0, 228.0, 276.0, 404.0, 460.0],
        aftertouch_min=[(CH.CH_PAD, 30), (CH.CH_CHOIR, 30)],
        vel_chain=["Eclipse", "Slipstream", "Perihelion"],
        quieter_than_peak=["Afterimage"],
        density_peak="Perihelion",
    ),
}


def _cc_events(sc, ch, num, lo=0.0, hi=1e12):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0xB0 and d[1] == num:
            b = tick / PPQ
            if lo - 1e-9 <= b <= hi + 1e-9:
                out.append((b, d[2]))
    return sorted(out)


def _bend_fracs(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0xE0:
            out.append((tick / PPQ, ((d[1] | (d[2] << 7)) - 8192) / 8192.0))
    return sorted(out)


def _at_events(sc, ch):
    return sorted((tick / PPQ, d[1]) for tick, _p, d in
                  sc.events.get(ch, []) if (d[0] & 0xF0) == 0xD0)


def _rpn_state(sc, ch):
    evs = sorted((t, d[1], d[2]) for t, _p, d in sc.events.get(ch, [])
                 if (d[0] & 0xF0) == 0xB0 and d[1] in (101, 100, 6))
    sel = [127, 127]
    ranges = [(-1e12, 2.0)]
    tunes = []
    problems = []
    for tick, num, val in evs:
        b = tick / PPQ
        if num == 101:
            sel[0] = val
        elif num == 100:
            sel[1] = val
        elif sel == [0, 0]:
            ranges.append((b, float(val)))
        elif sel == [0, 1]:
            tunes.append((b, (val - 64) * 100.0 / 64.0))
        elif sel == [127, 127]:
            problems.append(f"ch{ch} CC6 at {b:.2f} with RPN null")
        else:
            problems.append(f"ch{ch} CC6 at {b:.2f} with unknown RPN")
    if evs and sel != [127, 127]:
        problems.append(f"ch{ch} RPN left open")
    return ranges, tunes, problems


def _range_at(ranges, beat):
    cur = ranges[0][1]
    for b, r in ranges:
        if b > beat + 1e-9:
            break
        cur = r
    return cur


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []),
                              key=lambda e: (e[0], e[1])):
        st = d[0] & 0xF0
        if st == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append((tick / PPQ, d[2]))
        elif st == 0x80 or (st == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                on, vel = q.pop(0)
                out.append((on, tick / PPQ, d[1], vel))
    return sorted(out)


def _all_notes(sc):
    return [(ch, on, off, p, v) for ch in sc.events
            for on, off, p, v in _note_spans(sc, ch)]


def _cap(f):
    return f[:_REPORT_CAP] + ([f"... and {len(f) - _REPORT_CAP} more"]
                              if len(f) > _REPORT_CAP else [])


def check_structure(part, sc, info):
    cfg = PART_CONFIG[part.number]
    fails = []
    lo, hi = cfg["duration"]
    if not lo <= info["seconds"] <= hi:
        fails.append(f"check_structure: {info['seconds']:.1f}s outside "
                     f"[{lo:.0f},{hi:.0f}]")
    if info["tracks"] != EXPECTED_TRACKS:
        fails.append(f"check_structure: {info['tracks']} tracks")
    if info["tempo_events"] < cfg["min_tempo_events"]:
        fails.append("check_structure: too few tempo events")
    if sorted(sc.timesigs) != sorted(cfg["timesig_grid"]):
        fails.append(f"check_structure: timesig grid {sorted(sc.timesigs)}"
                     f" != {cfg['timesig_grid']}")
    if sorted(sc.keysigs) != sorted(cfg["keysig_grid"]):
        fails.append("check_structure: keysig grid mismatch")
    if len(sc.markers) < len(part.MOVEMENTS):
        fails.append("check_structure: missing markers")
    return fails


def check_material():
    return [f"check_material: {msg}" for msg in material.verify_material()]


def check_cc_inventory(part, sc):
    fails = []
    for ch, num, lo, hi, mn, trend, label in \
            PART_CONFIG[part.number]["cc_inventory"]:
        evs = _cc_events(sc, ch, num, lo, hi)
        if len(evs) < mn:
            fails.append(f"check_cc_inventory: {label}: {len(evs)} < {mn}")
            continue
        if trend == "rise" and evs[-1][1] < evs[0][1] + 20:
            fails.append(f"check_cc_inventory: {label}: no rise")
        elif trend == "fall" and evs[-1][1] > evs[0][1] - 20:
            fails.append(f"check_cc_inventory: {label}: no fall")
    return _cap(fails)


def check_vowels(part, sc):
    fails = []
    for ch, lo, hi, kind in PART_CONFIG[part.number]["vowel_sections"]:
        vals = [v for _b, v in _cc_events(sc, ch, 70, lo, hi)]
        prior = _cc_events(sc, ch, 70, 0.0, lo - 1e-9)
        if prior:
            vals.append(prior[-1][1])
        if not vals:
            fails.append(f"check_vowels: ch{ch} no CC70 in "
                         f"[{lo:.0f},{hi:.0f}]")
        elif kind == "hum" and min(vals) > 10:
            fails.append(f"check_vowels: ch{ch} hum min {min(vals)} > 10")
        elif kind == "chorus" and max(vals) < 80:
            fails.append(f"check_vowels: ch{ch} chorus max {max(vals)} "
                         f"< 80")
    return _cap(fails)


def check_pedals(part, sc):
    fails = []
    for ch in sorted(sc.events):
        for num, label in ((64, "sustain"), (66, "sostenuto"),
                           (67, "una corda"), (68, "legato")):
            state = False
            for b, v in _cc_events(sc, ch, num):
                on = v >= 64
                if on == state:
                    fails.append(f"check_pedals: ch{ch} CC{num} {label} "
                                 f"at {b:.2f}")
                    break
                state = on
            else:
                if state:
                    fails.append(f"check_pedals: ch{ch} CC{num} {label} "
                                 f"left DOWN")
    return _cap(fails)


def check_portamento(part, sc):
    fails = []
    for ch, lo, hi, deadline in PART_CONFIG[part.number]["portamento"]:
        if not _cc_events(sc, ch, 5, lo, hi):
            fails.append(f"check_portamento: ch{ch} no CC5 in "
                         f"[{lo:.0f},{hi:.0f}]")
        if not any(v >= 64 for _b, v in _cc_events(sc, ch, 65, lo, hi)):
            fails.append(f"check_portamento: ch{ch} CC65 never ON in "
                         f"[{lo:.0f},{hi:.0f}]")
        upto = _cc_events(sc, ch, 65, 0.0, deadline)
        if upto and upto[-1][1] >= 64:
            fails.append(f"check_portamento: ch{ch} ON at {deadline:.0f}")
    return _cap(fails)


def check_aftertouch(part, sc):
    fails = []
    for ch, mn in PART_CONFIG[part.number]["aftertouch_min"]:
        if len(_at_events(sc, ch)) < mn:
            fails.append(f"check_aftertouch: ch{ch} < {mn} events")
    return fails


def check_rpn(part, sc):
    cfg = PART_CONFIG[part.number]
    fails = []
    tunes_by = {}
    for ch in sorted(sc.events):
        ranges, tunes, problems = _rpn_state(sc, ch)
        tunes_by[ch] = tunes
        fails += [f"check_rpn: {p}" for p in problems]
        for b, r in ranges[1:]:
            if not 1.0 <= r <= 24.0:
                fails.append(f"check_rpn: ch{ch} range {r:.0f} insane")
            elif r > 2.0 and not any(
                    w == ch and lo - 1e-6 <= b <= hi + 1e-6 and r <= wr
                    for w, lo, hi, wr in cfg["rpn_windows"]):
                fails.append(f"check_rpn: ch{ch} range {r:.0f} at "
                             f"{b:.2f} outside windows")
        dl = cfg["rpn_reset_by"].get(ch)
        if dl is not None and len(ranges) > 1 \
                and abs(_range_at(ranges, dl) - 2.0) > 1e-9:
            fails.append(f"check_rpn: ch{ch} not reset by {dl:.0f}")
    for ch, lo, hi, clo, chi in cfg["fine_tune_expect"]:
        if not [1 for b, c in tunes_by.get(ch, [])
                if lo <= b <= hi and clo <= c <= chi]:
            fails.append(f"check_rpn: ch{ch} missing fine-tune in "
                         f"[{lo:.0f},{hi:.0f}]")
    return _cap(fails)


def check_bend_hygiene(part, sc):
    cfg = PART_CONFIG[part.number]
    fails = []
    for ch in sorted(sc.events):
        bends = _bend_fracs(sc, ch)
        if not bends:
            continue
        ranges, _t, _p = _rpn_state(sc, ch)
        for b, frac in bends:
            r = _range_at(ranges, b)
            s = frac * r
            if abs(s) > r + 1e-6:
                fails.append(f"check_bend_hygiene: ch{ch} {s:+.2f} at "
                             f"{b:.2f} exceeds {r:.0f}")
            elif abs(s) > 2.0 + 1e-6 and r <= 2.0 + 1e-9:
                fails.append(f"check_bend_hygiene: ch{ch} {s:+.2f} at "
                             f"{b:.2f} with default range")
        for rb in cfg["bend_recenter"]:
            frac = 0.0
            for b, f in bends:
                if b > rb + 1e-6:
                    break
                frac = f
            if abs(frac * _range_at(ranges, rb)) >= 0.01:
                fails.append(f"check_bend_hygiene: ch{ch} not recentred "
                             f"at {rb:.0f}")
    return _cap(fails)


def check_ranges(part, sc):
    fails = []
    for ch in sorted(sc.events):
        for on, _off, p, _v in _note_spans(sc, ch):
            if ch == CH.CH_DRUMS:
                if p not in GM_PERCUSSION:
                    fails.append(f"check_ranges: drum {p} at {on:.2f}")
            else:
                lo, hi = NOTE_RANGES.get(ch, (0, 127))
                if not lo <= p <= hi:
                    fails.append(f"check_ranges: ch{ch} note {p} at "
                                 f"{on:.2f} outside [{lo},{hi}]")
    return _cap(fails)


def check_dynamics(part, sc):
    cfg = PART_CONFIG[part.number]
    fails = []
    stats = {}
    notes = _all_notes(sc)
    for name, t0, t1 in part.MOVEMENTS:
        vels = [v for _c, on, _off, _p, v in notes if t0 <= on < t1]
        if not vels:
            fails.append(f"check_dynamics: no notes in '{name}'")
            continue
        stats[name] = (sum(vels) / len(vels), len(vels) / (t1 - t0))
    if len(stats) == len(part.MOVEMENTS):
        chain = [(nm, stats[nm][0]) for nm in cfg["vel_chain"]]
        for (na, va), (nb, vb) in zip(chain, chain[1:]):
            if va >= vb:
                fails.append(f"check_dynamics: '{na}' ({va:.1f}) >= "
                             f"'{nb}' ({vb:.1f})")
        peak = stats[cfg["density_peak"]][0]
        for nm in cfg["quieter_than_peak"]:
            if stats[nm][0] >= peak:
                fails.append(f"check_dynamics: '{nm}' "
                             f"({stats[nm][0]:.1f}) >= peak ({peak:.1f})")
        densest = max(stats, key=lambda nm: stats[nm][1])
        if densest != cfg["density_peak"]:
            fails.append(f"check_dynamics: density peaks in '{densest}'")
    return _cap(fails)


def check_gaps(part, sc):
    spans = sorted((on, off) for _c, on, off, _p, _v in _all_notes(sc))
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > MAX_GAP_BEATS:
            fails.append(f"check_gaps: silence {horizon:.2f} -> {on:.2f}")
        horizon = max(horizon, off)
    return _cap(fails)


def check_bounds(part, spans, whitelist=()):
    fails = []
    for name, t0, t1, notes in spans:
        for ch, b in notes:
            if t0 - 0.05 <= b < t1:
                continue
            if any(w == ch and lo - 1e-6 <= b <= hi + 1e-6
                   for w, lo, hi in whitelist):
                continue
            fails.append(f"check_bounds: '{name}' ch{ch} at {b:.2f}")
    return _cap(fails)


def run_all(parts_data, bounds_whitelists=None):
    bounds_whitelists = bounds_whitelists or {}
    results = [("check_material", check_material())]
    for part, sc, info, spans in parts_data:
        tag = f"P{part.number}"
        results += [
            (f"{tag}:check_structure", check_structure(part, sc, info)),
            (f"{tag}:check_cc_inventory", check_cc_inventory(part, sc)),
            (f"{tag}:check_vowels", check_vowels(part, sc)),
            (f"{tag}:check_pedals", check_pedals(part, sc)),
            (f"{tag}:check_portamento", check_portamento(part, sc)),
            (f"{tag}:check_aftertouch", check_aftertouch(part, sc)),
            (f"{tag}:check_rpn", check_rpn(part, sc)),
            (f"{tag}:check_bend_hygiene", check_bend_hygiene(part, sc)),
            (f"{tag}:check_ranges", check_ranges(part, sc)),
            (f"{tag}:check_dynamics", check_dynamics(part, sc)),
            (f"{tag}:check_gaps", check_gaps(part, sc)),
            (f"{tag}:check_bounds", check_bounds(
                part, spans, bounds_whitelists.get(part.number, ()))),
        ]
    return results
