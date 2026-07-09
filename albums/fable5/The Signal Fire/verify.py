"""verify.py — structural oracles for *The Signal Fire* (roadmap section 6).

Every check operates on the in-memory Score (rebuilt deterministically from
the fixed seed) plus, for check_structure, the engine.parse_midi output of
the written file.  Each returns a list[str] of failures (empty == pass) and
every failure message names its check.

While the movements are still stubs, most checks FAIL — that is correct and
intentional: the oracles describe the finished piece.  The material oracle
(check_material) and the machinery itself must always run clean.

Whitelists:
  * check_bend_hygiene takes (ch, lo_beat, hi_beat) ranges where a channel's
    bend may legitimately sit off-centre at a movement boundary — the ch13
    +6-cent detune segments.  The M4->M5 whole-chord bend needs NO entry:
    the roadmap requires it recentred exactly at 1312.0, and the un-
    whitelisted boundary check enforces that.
  * check_movement_bounds takes (ch, lo_beat, hi_beat) ranges where a note
    may start outside its movement — documented seam carry-overs only.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ

# ---------------------------------------------------------------------------
# Requirement data (roadmap section 6)
# ---------------------------------------------------------------------------

DURATION_WINDOW = (16 * 60.0 + 30.0, 17 * 60.0 + 30.0)   # 16:30 - 17:30
# (The roadmap prose first said "~17:20", but its own tempo map integrates
# to ~16:54 of MIDI; the window brackets the tempo map's true integral.)
EXPECTED_TRACKS = 17                                 # conductor + 16 channels
MIN_MARKERS = 6
MIN_TEMPO_EVENTS = 14
MIN_TIMESIGS = 3

# CC inventory (item 4), data-driven:
# (channel, cc number, lo_beat, hi_beat, min events, trend, description).
# trend: "rise" / "fall" compares the first and last value in the range
# (must differ by >= 20); None means count only.
CC_INVENTORY: list[tuple[int, int, float, float, int, str | None, str]] = [
    (conductor.CH_PAD,   74,    0.0,  176.0,   8, "rise",
     "M1 pad filter opening (CC74 30->100)"),
    (conductor.CH_PAD,   74, 1592.0, 1678.0,   8, "fall",
     "M6 pad filter closing (CC74 100->25)"),
    (conductor.CH_WAH,   74,  176.0,  480.0, 200, None,
     "M2 wah LFO on ch11 (>=200 CC74 events)"),
    (conductor.CH_ORGAN,  1,  176.0,  480.0,  12, None,
     "M2 Hammond Leslie ramps (CC1)"),
    (conductor.CH_ORGAN,  1,  992.0, 1312.0,   8, None,
     "M4 W4/W5 Leslie spin-up (CC1)"),
    (conductor.CH_PIANO, 64,    0.0,  176.0,   2, None,
     "M1 piano pedal washes (CC64)"),
    (conductor.CH_PIANO, 64, 1592.0, 1678.0,   2, None,
     "M6 piano pedal washes (CC64)"),
]

MIN_LEAD_BENDS = 100        # item 4: ch12/ch13 bend events > 100 each

# Bend hygiene (item 5): ch13's intentional detune segments (M4 W3 onward).
BEND_WHITELIST: list[tuple[int, float, float]] = [
    (conductor.CH_DOUBLE, 928.0, 1312.0),
]

# Sensible per-channel note ranges (item 6): ch -> (lo, hi).
NOTE_RANGES: dict[int, tuple[int, int]] = {
    conductor.CH_PIANO:   (21, 108),
    conductor.CH_PAD:     (36, 96),
    conductor.CH_CRYSTAL: (48, 110),
    conductor.CH_BASS:    (24, 69),
    conductor.CH_ORGAN:   (36, 96),
    conductor.CH_STRINGS: (36, 96),
    conductor.CH_CHOIR:   (43, 91),
    conductor.CH_STEEL:   (40, 88),
    conductor.CH_NYLON:   (40, 88),
    conductor.CH_RHYTHM:  (38, 88),
    conductor.CH_WAH:     (40, 92),
    conductor.CH_LEAD:    (40, 96),    # ceiling B6 = 95 in M4-W5
    conductor.CH_DOUBLE:  (40, 96),
    conductor.CH_WINDS:   (55, 105),
    conductor.CH_BELLS:   (45, 100),
}
GM_PERCUSSION = set(range(35, 82))     # the standard GM percussion map

# Dynamics arc (item 7): mean velocity strictly increasing along this chain.
DYNAMICS_ORDER = ["Signal", "Afterglow", "The Lattice", "Ignition",
                  "The Long Climb", "Ascension"]
DENSITY_PEAK = "Ascension"

MAX_GAP_BEATS = 1.0                     # item 8
_REPORT_CAP = 8                         # per-check failure list cap


# ---------------------------------------------------------------------------
# Score introspection helpers
# ---------------------------------------------------------------------------

def _cc_events(sc: en.Score, ch: int, num: int,
               lo: float = 0.0, hi: float = 1e12) -> list[tuple[float, int]]:
    """Sorted (beat, value) of channel `ch` CC `num` events in [lo, hi]."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[2]))
    return sorted(out)


def _bend_events(sc: en.Score, ch: int) -> list[tuple[float, float]]:
    """Sorted (beat, semitones) of channel `ch` pitch-bend events."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / PPQ, (raw - 8192) / 8192.0 * 2.0))
    return sorted(out)


def _note_spans(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """Paired notes on `ch` as sorted (on_beat, off_beat, pitch, velocity)."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out: list[tuple[float, float, int, int]] = []
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
    for pitch, queue in pending.items():        # unmatched (defensive)
        for on, vel in queue:
            out.append((on, on, pitch, vel))
    return sorted(out)


def _all_notes(sc: en.Score) -> list[tuple[int, float, float, int, int]]:
    """(ch, on_beat, off_beat, pitch, velocity) for every note in the score."""
    out = []
    for ch in sc.events:
        for on, off, pitch, vel in _note_spans(sc, ch):
            out.append((ch, on, off, pitch, vel))
    return out


def _cap(fails: list[str]) -> list[str]:
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The checks (roadmap section 6, items 1-9)
# ---------------------------------------------------------------------------

def check_structure(sc: en.Score, info: dict) -> list[str]:
    """Item 1: file parses, duration window, track/marker/tempo/timesig
    counts.  `info` is engine.parse_midi output for the written file."""
    fails = []
    lo, hi = DURATION_WINDOW
    if not lo <= info["seconds"] <= hi:
        fails.append(f"check_structure: duration {info['seconds']:.1f}s "
                     f"outside [{lo:.0f}, {hi:.0f}]s (16:30-17:30)")
    if info["tracks"] != EXPECTED_TRACKS:
        fails.append(f"check_structure: {info['tracks']} MIDI tracks, "
                     f"expected {EXPECTED_TRACKS} (conductor + 16 channels)")
    if info["ppq"] != PPQ:
        fails.append(f"check_structure: PPQ {info['ppq']} != {PPQ}")
    if info["format"] != 1:
        fails.append(f"check_structure: format {info['format']} != 1")
    if len(sc.markers) < MIN_MARKERS:
        fails.append(f"check_structure: {len(sc.markers)} markers, "
                     f"need >= {MIN_MARKERS}")
    if info["tempo_events"] < MIN_TEMPO_EVENTS:
        fails.append(f"check_structure: {info['tempo_events']} tempo events, "
                     f"need >= {MIN_TEMPO_EVENTS}")
    if len(sc.timesigs) < MIN_TIMESIGS:
        fails.append(f"check_structure: {len(sc.timesigs)} time signatures, "
                     f"need >= {MIN_TIMESIGS}")
    return fails


def check_material() -> list[str]:
    """Items 2+3: delegate to the material oracle (counterpoint over the
    ground, riff-skeleton identity, register promises)."""
    return [f"check_material: {msg}" for msg in material.verify_material()]


def check_cc_inventory(sc: en.Score) -> list[str]:
    """Item 4: the data-driven controller inventory + special balances."""
    fails = []
    for ch, num, lo, hi, min_count, trend, label in CC_INVENTORY:
        evs = _cc_events(sc, ch, num, lo, hi)
        if len(evs) < min_count:
            fails.append(f"check_cc_inventory: {label}: {len(evs)} CC{num} "
                         f"events on ch{ch} in [{lo:.0f},{hi:.0f}], "
                         f"need >= {min_count}")
            continue
        if trend == "rise" and evs[-1][1] < evs[0][1] + 20:
            fails.append(f"check_cc_inventory: {label}: no rise "
                         f"({evs[0][1]} -> {evs[-1][1]})")
        elif trend == "fall" and evs[-1][1] > evs[0][1] - 20:
            fails.append(f"check_cc_inventory: {label}: no fall "
                         f"({evs[0][1]} -> {evs[-1][1]})")
    # ch0 sustain pedal: downs must equal ups (no stuck pedal).
    pedal = _cc_events(sc, conductor.CH_PIANO, 64)
    downs = sum(1 for _b, v in pedal if v >= 64)
    ups = len(pedal) - downs
    if downs != ups:
        fails.append(f"check_cc_inventory: ch0 CC64 downs ({downs}) != "
                     f"ups ({ups})")
    # lead + double bend counts.
    for ch in (conductor.CH_LEAD, conductor.CH_DOUBLE):
        count = len(_bend_events(sc, ch))
        if count <= MIN_LEAD_BENDS:
            fails.append(f"check_cc_inventory: ch{ch} has {count} bend "
                         f"events, need > {MIN_LEAD_BENDS}")
    # CC68 legato pedal balanced (on/off alternating) on every channel.
    for ch in sorted(sc.events):
        legato = _cc_events(sc, ch, 68)
        state = False
        for beat, val in legato:
            on = val >= 64
            if on == state:
                fails.append(f"check_cc_inventory: ch{ch} CC68 not "
                             f"alternating at beat {beat:.2f}")
                break
            state = on
        else:
            if state:
                fails.append(f"check_cc_inventory: ch{ch} CC68 left ON "
                             f"after the last legato run")
    return _cap(fails)


def check_bend_hygiene(sc: en.Score,
                       boundaries: list[float] | None = None,
                       whitelist: list[tuple[int, float, float]] | None = None
                       ) -> list[str]:
    """Item 5: |bend| <= 2 semitones everywhere; every channel recentred
    (|s| < 0.01) at each movement boundary, except whitelisted ranges."""
    fails = []
    if boundaries is None:
        boundaries = [t1 for _name, _t0, t1 in conductor.MOVEMENTS]
    if whitelist is None:
        whitelist = BEND_WHITELIST
    for ch in sorted(sc.events):
        bends = _bend_events(sc, ch)
        if not bends:
            continue
        worst = max(bends, key=lambda e: abs(e[1]))
        if abs(worst[1]) > 2.0 + 1e-6:
            fails.append(f"check_bend_hygiene: ch{ch} bend {worst[1]:+.3f} "
                         f"semis at beat {worst[0]:.2f} exceeds +/-2")
        for b in boundaries:
            if any(w_ch == ch and lo - 1e-6 <= b <= hi + 1e-6
                   for w_ch, lo, hi in whitelist):
                continue
            current = 0.0
            for beat, semis in bends:
                if beat > b + 1e-6:
                    break
                current = semis
            if abs(current) >= 0.01:
                fails.append(f"check_bend_hygiene: ch{ch} bend "
                             f"{current:+.3f} semis not recentred at "
                             f"movement boundary {b:.0f}")
    return _cap(fails)


def check_ranges(sc: en.Score) -> list[str]:
    """Item 6: notes stay in sensible per-channel MIDI ranges; ch9 uses
    only standard GM percussion notes."""
    fails = []
    for ch in sorted(sc.events):
        for on, _off, pitch, _vel in _note_spans(sc, ch):
            if ch == conductor.CH_DRUMS:
                if pitch not in GM_PERCUSSION:
                    fails.append(f"check_ranges: ch9 percussion note {pitch} "
                                 f"at beat {on:.2f} outside the GM map "
                                 f"(35-81)")
            else:
                lo, hi = NOTE_RANGES.get(ch, (0, 127))
                if not lo <= pitch <= hi:
                    fails.append(f"check_ranges: ch{ch} note {pitch} at "
                                 f"beat {on:.2f} outside [{lo}, {hi}]")
    return _cap(fails)


def check_dynamics_arc(sc: en.Score) -> list[str]:
    """Item 7: mean velocity per movement ordered M1 < M6 < M3 < M2 < M4 <
    M5; note density (notes/beat) peaks in M5."""
    fails = []
    stats: dict[str, tuple[float, float]] = {}
    notes = _all_notes(sc)
    for name, t0, t1 in conductor.MOVEMENTS:
        vels = [vel for _ch, on, _off, _p, vel in notes if t0 <= on < t1]
        if not vels:
            fails.append(f"check_dynamics_arc: no notes in '{name}' "
                         f"[{t0:.0f}, {t1:.0f})")
            continue
        stats[name] = (sum(vels) / len(vels), len(vels) / (t1 - t0))
    if len(stats) == len(conductor.MOVEMENTS):
        chain = [(name, stats[name][0]) for name in DYNAMICS_ORDER]
        for (na, va), (nb, vb) in zip(chain, chain[1:]):
            if va >= vb:
                fails.append(f"check_dynamics_arc: mean velocity "
                             f"'{na}' ({va:.1f}) >= '{nb}' ({vb:.1f}); "
                             f"required M1 < M6 < M3 < M2 < M4 < M5")
        densest = max(stats, key=lambda nm: stats[nm][1])
        if densest != DENSITY_PEAK:
            fails.append(f"check_dynamics_arc: note density peaks in "
                         f"'{densest}' ({stats[densest][1]:.2f}/beat), "
                         f"must peak in '{DENSITY_PEAK}'")
    return _cap(fails)


def check_gaps(sc: en.Score, max_gap: float = MAX_GAP_BEATS) -> list[str]:
    """Item 8: no all-channel silent gap longer than `max_gap` beats from
    beat 0 to the last note-off."""
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: no notes anywhere - the piece is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            fails.append(f"check_gaps: all channels silent from beat "
                         f"{horizon:.2f} to {on:.2f} "
                         f"({on - horizon:.2f} beats)")
        horizon = max(horizon, off)
    return _cap(fails)


def check_movement_bounds(spans: list[tuple[str, float, float,
                                            list[tuple[int, float]]]],
                          whitelist: list[tuple[int, float, float]] = ()
                          ) -> list[str]:
    """Item 9: every movement module writes note-ons only inside its
    [t0, t1) span.  `spans` is built by build.py: (name, t0, t1,
    [(ch, on_beat), ...]) per module.  `whitelist` lists (ch, lo, hi)
    ranges for documented seam carry-overs.  0.05 beats of slack absorbs
    the humanisation jitter at span starts."""
    fails = []
    for name, t0, t1, notes in spans:
        for ch, beat in notes:
            if t0 - 0.05 <= beat < t1:
                continue
            if any(w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                   for w_ch, lo, hi in whitelist):
                continue
            fails.append(f"check_movement_bounds: '{name}' wrote a ch{ch} "
                         f"note at beat {beat:.2f}, outside "
                         f"[{t0:.0f}, {t1:.0f})")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(sc: en.Score, info: dict,
            spans: list[tuple[str, float, float, list[tuple[int, float]]]],
            bend_whitelist: list[tuple[int, float, float]] | None = None,
            bounds_whitelist: list[tuple[int, float, float]] = ()
            ) -> list[tuple[str, list[str]]]:
    """Run every oracle; returns [(check_name, failures)] in order."""
    return [
        ("check_structure", check_structure(sc, info)),
        ("check_material", check_material()),
        ("check_cc_inventory", check_cc_inventory(sc)),
        ("check_bend_hygiene", check_bend_hygiene(sc,
                                                  whitelist=bend_whitelist)),
        ("check_ranges", check_ranges(sc)),
        ("check_dynamics_arc", check_dynamics_arc(sc)),
        ("check_gaps", check_gaps(sc)),
        ("check_movement_bounds", check_movement_bounds(
            spans, whitelist=bounds_whitelist)),
    ]
