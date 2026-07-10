"""t06_two_rooms — Track 6 "Two Rooms, One Clock" of *Through Lines*.

Disc 1, 'Lines of Descent' — the process-music track (HLD section 3, T6):
Reich-inspired CONTINUOUS phasing, exact where tape loops drifted.  Two
rooms hear the same original 12-note C-lydian mallet figure (period
P = 3.0 beats — one 3/4 bar of sixteenths).  Room A (marimba, panned
left) repeats it with period P: repetition i starts at i*P.  Room B
(vibraphone, panned right) is the same performance heard through a clock
that runs one percent slow: its entire timeline is A's scaled by 1.01,
so repetition i starts at i*P*1.01 and the phase offset grows by exactly
P/100 = 0.03 beats per cycle.  With 101 cycles (i = 0..100) the total
drift at the final cycle is EXACTLY P — B laps A exactly once: the piece
begins in unison, sweeps continuously through echo, canon and hocket,
and re-merges on its last bar.

At the piece's midpoint (beat 153.0) a third, centred channel enters —
the clock itself (celesta).  It plays ONLY onsets coinciding (within 30
ticks) with the accent onsets of A or B: the accents are the figure's
three octave-doubled notes (indices 0/4/7, a 4+3+5 sixteenth clave),
sounded one octave up and deduplicated inside the 30-tick window so a
re-merging accent strikes once.  A quiet centred string bed (C2+G2 open
fifth, the lydian root the figure deliberately omits) grounds the mode.
A slow dynamic arc (velocity 58 -> 92 -> 46, peak at beat 168) spans the
piece; per-16-bar velocity means are oracle-pinned to rise then fall.

ZERO HUMANISATION — this track is the album's precision showpiece.
Every note on every channel is scheduled with jt=0, jv=0: onset ticks
and velocities are exact functions of the schedule formulae below
(oracle `zero_humanisation` proves event-for-event equality), and no
randomness of any kind is used in this module.  The phasing is scheduled
in float beats; the only deviation from the ideal schedule is MIDI tick
rounding (half a tick at PPQ 480), and the oracles account for exactly
that and nothing more.

Written oracle-first (the repo method): every headline claim above is a
falsifiable oracle below — pattern identity, exact schedule, linear
phase growth (every event-derived cycle start pinned to round(i*P*PPQ) /
round(i*P*RATIO*PPQ), the formula typed in the oracle, independent of
the builders' schedule function), lap-exactly-once
(drift == P to the tick), the clock's subset-of-accents rule and
midpoint entry, the rise-then-fall dynamic arc, the lydian collection,
zero humanisation, and the pan discipline.  This track deliberately
quotes no material.py through-line: it is the album's one pure process
piece (the HLD assigns it none).
"""

from __future__ import annotations

import bisect

import conductor
import engine as en

NUMBER = 6
TITLE = 'Two Rooms, One Clock'
FILE = '06 - Two Rooms, One Clock.mid'
SEED = 20260906

COMMENT = ("Continuous Reich-style phasing, exact: room B's timeline is "
           "room A's scaled by 1.01; over 101 three-beat cycles B laps A "
           "exactly once.  Zero humanisation - every onset and velocity "
           "is a pure function of the schedule.")

# ---------------------------------------------------------------------------
# The clock.
# ---------------------------------------------------------------------------

P = 3.0                    # pattern period in beats (one 3/4 bar)
RATIO = 1.01               # room B's clock runs one percent slow
CYCLES = 101               # i = 0..100; drift 0.03*i; lap at i == 100
STEP = P / 12.0            # twelve sixteenths per cycle
END = P * CYCLES + P       # 306.0: room B's final (lapped) cycle ends here
MID = END / 2.0            # 153.0: the clock channel enters here
PEAK = 168.0               # dynamic-arc apex (inside window W3)

# The figure: twelve sixteenths in C lydian, no adjacent repeats (wrap
# included), ambitus a major seventh, six distinct pitches, tonic absent
# (the bed supplies C).  Original material - no Reich pattern is quoted.
FIGURE = [59, 62, 64, 66, 69, 64, 67, 66, 62, 69, 67, 64]
ACCENTS = (0, 4, 7)        # octave-doubled indices: a 4+3+5 clave
ACCENT_BOOST = 14          # accent main note: arc velocity + 14
DOUBLE_DROP = 8            # accent lower octave: accent velocity - 8
NOTE_DUR = 0.22            # room note length (beats, scaled for B)
CLOCK_DUR = 0.45
EPS_TICKS = 30             # the coincidence window (binding: 30 ticks)
DEDUPE_BEATS = EPS_TICKS / en.PPQ
LYDIAN_PCS = {0, 2, 4, 6, 7, 9, 11}

CH_A, CH_B, CH_CLOCK, CH_BED = 0, 1, 2, 3
PAN_A, PAN_B = 16, 112     # decisively panned transient rooms
BED_PITCHES = (36, 43)     # C2 + G2, floored at C2, centred
BED_VEL = 44

MOVS: list[tuple[str, float, float]] = [
    ("I. Same Room", 0.0, 75.0),        # drift 0.00 -> 0.75 (unison, echo)
    ("II. Drifting Apart", 75.0, 150.0),  # drift 0.75 -> 1.50 (canon)
    ("III. Opposite Walls", 150.0, 225.0),  # 1.50 -> 2.25 (hocket; clock)
    ("IV. Coming Round", 225.0, 291.0),   # drift 2.25 -> 2.91
    ("V. One Clock", 291.0, 306.0),       # drift 2.91 -> 3.00: the lap
]


def _tick(beat: float) -> int:
    """Engine tick quantisation (mirrors engine._tick exactly)."""
    return max(0, int(round(beat * en.PPQ)))


# ---------------------------------------------------------------------------
# The schedule — pure functions of the constants above.  Builders write
# exactly these events; oracles hold the written Score to them.
# ---------------------------------------------------------------------------

def _arc_vel(t: float) -> int:
    """The slow dynamic arc: 58 -> 92 at PEAK -> 46 at END."""
    if t <= PEAK:
        return int(round(en.lerp(58.0, 92.0, t / PEAK)))
    return int(round(en.lerp(92.0, 46.0, (t - PEAK) / (END - PEAK))))


def _clock_vel(t: float) -> int:
    return max(44, _arc_vel(t) - 8)


def room_events(room: str) -> list[tuple[float, int, int, float]]:
    """One room's full note list: (onset_beats, pitch, vel, dur).

    Room A's onsets are i*P + k*STEP; room B's are the SAME timeline
    scaled by RATIO, so B's repetition i starts at i*P*RATIO and the
    per-cycle offset delta is the constant P*(RATIO-1) = 0.03 beats.
    Accented indices add the lower octave (the dyad the oracles use to
    find accents in the event stream).
    """
    scale = 1.0 if room == "A" else RATIO
    out: list[tuple[float, int, int, float]] = []
    for i in range(CYCLES):
        for k, p in enumerate(FIGURE):
            t = (i * P + k * STEP) * scale
            v = _arc_vel(t) + (ACCENT_BOOST if k in ACCENTS else 0)
            out.append((t, p, v, NOTE_DUR * scale))
            if k in ACCENTS:
                out.append((t, p - 12, v - DOUBLE_DROP, NOTE_DUR * scale))
    return out


def _accent_onsets() -> list[tuple[float, int]]:
    """(onset, main pitch) of every accent of both rooms, time-sorted."""
    out: list[tuple[float, int]] = []
    for scale in (1.0, RATIO):
        for i in range(CYCLES):
            for k in ACCENTS:
                out.append(((i * P + k * STEP) * scale, FIGURE[k]))
    return sorted(out)


def clock_events() -> list[tuple[float, int]]:
    """The centre channel: every accent of either room from the midpoint
    on, one octave up, deduplicated inside the 30-tick window (so the
    re-merging rooms ring the bell once, not twice)."""
    last: dict[int, float] = {}
    out: list[tuple[float, int]] = []
    for t, main in _accent_onsets():
        if t < MID - 1e-9:
            continue
        bell = main + 12
        prev = last.get(bell)
        if prev is not None and t - prev <= DEDUPE_BEATS + 1e-9:
            continue
        last[bell] = t
        out.append((t, bell))
    return out


def _bed_events() -> list[tuple[float, int, int]]:
    """(onset, pitch, vel): the C2+G2 fifth, re-struck each movement."""
    return [(t0, p, BED_VEL) for _name, t0, _t1 in MOVS
            for p in BED_PITCHES]


# ---------------------------------------------------------------------------
# PART — grid, tempo, channels.
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVS,
    tempo_map=[(0.0, 63.0)],          # metronomic throughout: one clock
    time_signatures=[(0.0, 3, 4)],
    keysigs=[(0.0, 1, 0)],            # one sharp: C lydian's F#
    channels=[
        (CH_A, "room A - marimba", 12, 100, PAN_A, 30),
        (CH_B, "room B - vibraphone", 11, 100, PAN_B, 30),
        (CH_CLOCK, "the clock - celesta", 8, 82, 64, 45),
        (CH_BED, "bed - strings", 48, 92, 64, 55),
    ],
    extra_markers=[(MID, "the clock enters")],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {8, 11, 12, 48}
CENTERED_CHANNELS: set[int] = {CH_CLOCK, CH_BED}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_A: (47, 69),      # figure 59..69 plus accent lower octaves
    CH_B: (47, 69),
    CH_CLOCK: (71, 81),  # the accent pitches, one octave up
    CH_BED: (36, 43),    # C2..G2, floored at C2
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (289.0, 298.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the builders; the music is composed to pass.
# ---------------------------------------------------------------------------

def _note_ons(sc: en.Score, ch: int) -> list[tuple[int, int, int]]:
    """(tick, pitch, vel) of every note-on, sorted by (tick, pitch)."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _onset_groups(ons: list[tuple[int, int, int]]
                  ) -> list[tuple[int, list[tuple[int, int]]]]:
    """Group note-ons by tick: [(tick, [(pitch, vel), ...])]."""
    groups: list[tuple[int, list[tuple[int, int]]]] = []
    for tick, p, v in ons:
        if groups and groups[-1][0] == tick:
            groups[-1][1].append((p, v))
        else:
            groups.append((tick, [(p, v)]))
    return groups


def _expected_notes(ch: int) -> list[tuple[int, int, int]]:
    """The schedule, tick-quantised: what the Score MUST contain."""
    if ch == CH_A:
        evs = [(t, p, v) for t, p, v, _d in room_events("A")]
    elif ch == CH_B:
        evs = [(t, p, v) for t, p, v, _d in room_events("B")]
    elif ch == CH_CLOCK:
        evs = [(t, p, _clock_vel(t)) for t, p in clock_events()]
    else:
        evs = _bed_events()
    return sorted((_tick(t), p, v) for t, p, v in evs)


def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    # --- figure_wellformed: the pattern's own claims -----------------------
    fails: list[str] = []
    if len(FIGURE) != 12:
        fails.append(f"figure has {len(FIGURE)} notes, want 12")
    bad_pcs = {p % 12 for p in FIGURE} - LYDIAN_PCS
    if bad_pcs:
        fails.append(f"figure pitch classes {sorted(bad_pcs)} not C lydian")
    for a, b in zip(FIGURE, FIGURE[1:] + FIGURE[:1]):
        if a == b:
            fails.append(f"figure repeats pitch {a} adjacently (wrap incl.)")
    if max(FIGURE) - min(FIGURE) > 12:
        fails.append("figure ambitus exceeds an octave")
    if len(ACCENTS) != 3 or any(not 0 <= k < 12 for k in ACCENTS):
        fails.append(f"accents {ACCENTS} must be 3 indices inside the figure")
    if abs(12 * STEP - P) > 1e-12:
        fails.append("twelve sixteenths must exactly fill the period")
    results.append(("figure_wellformed", fails))

    ons_a, ons_b = _note_ons(sc, CH_A), _note_ons(sc, CH_B)
    grp_a, grp_b = _onset_groups(ons_a), _onset_groups(ons_b)

    # --- pattern_identity: A and B note-sequence-identical (pitch+order) ---
    fails = []
    for name, ons, grp in (("A", ons_a, grp_a), ("B", ons_b, grp_b)):
        if len(grp) != CYCLES * 12:
            fails.append(f"room {name}: {len(grp)} onsets, want "
                         f"{CYCLES * 12}")
            continue
        mains = [max(p for p, _v in notes) for _t, notes in grp]
        if mains != FIGURE * CYCLES:
            bad = next(i for i, (g, w) in
                       enumerate(zip(mains, FIGURE * CYCLES)) if g != w)
            fails.append(f"room {name}: pitch sequence diverges from the "
                         f"figure at onset {bad}")
        for idx, (tick, notes) in enumerate(grp):
            k = idx % 12
            if k in ACCENTS:
                if len(notes) != 2 or min(p for p, _v in notes) != \
                        max(p for p, _v in notes) - 12:
                    fails.append(f"room {name} onset {idx}: accent must be "
                                 f"an octave dyad")
            elif len(notes) != 1:
                fails.append(f"room {name} onset {idx}: unaccented note "
                             f"must be single")
    if [p for _t, p, _v in ons_a] != [p for _t, p, _v in ons_b]:
        fails.append("rooms A and B are not note-sequence-identical "
                     "(pitch+order)")
    results.append(("pattern_identity", fails))

    # --- phase_schedule_exact: events == the float schedule, tick-exact;
    #     per-cycle offset delta constant to 1e-6 on the float schedule ----
    fails = []
    for name, ch, ons in (("A", CH_A, ons_a), ("B", CH_B, ons_b)):
        want = _expected_notes(ch)
        if ons != want:
            diffs = [i for i, (g, w) in enumerate(zip(ons, want)) if g != w]
            head = diffs[0] if diffs else min(len(ons), len(want))
            fails.append(f"room {name}: events differ from the schedule "
                         f"(first at index {head}, {len(ons)} vs "
                         f"{len(want)} events)")
    # First the FLOAT schedule itself: room_events emits 15 events per
    # cycle (12 notes + 3 accent doublings), so cycle i starts at event
    # 15*i.  The per-cycle offset delta (B minus A, cycle-on-cycle) must
    # be the constant P*(RATIO-1) to 1e-6, starting from zero (unison).
    flo_a = [room_events("A")[15 * i][0] for i in range(CYCLES)]
    flo_b = [room_events("B")[15 * i][0] for i in range(CYCLES)]
    offs = [b - a for a, b in zip(flo_a, flo_b)]
    if abs(offs[0]) > 1e-9:
        fails.append(f"float schedule: cycle 0 offset {offs[0]!r} != 0")
    for i, (d0, d1) in enumerate(zip(offs, offs[1:])):
        if abs((d1 - d0) - P * (RATIO - 1.0)) > 1e-6:
            fails.append(f"float schedule: offset delta at cycle {i} is "
                         f"{d1 - d0:.9f}, not {P * (RATIO - 1.0):.9f} "
                         f"(constant to 1e-6)")
    # Then linear growth is held against the EVENTS, with the ideal-
    # schedule formula typed HERE — deliberately not shared with
    # room_events(), which the builders also call: cycle i of room A
    # must start at round(i*P*PPQ) ticks and of room B at
    # round(i*P*RATIO*PPQ) ticks (+/-1 tick of rounding slack).  Pinning
    # every cycle start to the linear formula pins the per-cycle onset
    # delta constant; any drift wobble beyond tick rounding fails here
    # even if drift stays monotone and the endpoints are exact.
    if len(grp_a) == CYCLES * 12 and len(grp_b) == CYCLES * 12:
        for i in range(CYCLES):
            got_a, want_a = grp_a[i * 12][0], round(i * P * en.PPQ)
            got_b, want_b = grp_b[i * 12][0], round(i * P * RATIO * en.PPQ)
            if abs(got_a - want_a) > 1:
                fails.append(f"room A cycle {i} starts at tick {got_a}, "
                             f"want {want_a} (+/-1): phase not linear")
            if abs(got_b - want_b) > 1:
                fails.append(f"room B cycle {i} starts at tick {got_b}, "
                             f"want {want_b} (+/-1): phase not linear")
    else:
        fails.append("cycle grid wrong (see pattern_identity): linear "
                     "phase growth unverifiable")
    results.append(("phase_schedule_exact", fails))

    # --- lap_exactly_once: total drift == P at the final cycle -------------
    fails = []
    if len(grp_a) == CYCLES * 12 and len(grp_b) == CYCLES * 12:
        starts_a = [grp_a[i * 12][0] for i in range(CYCLES)]
        starts_b = [grp_b[i * 12][0] for i in range(CYCLES)]
        drift = [b - a for a, b in zip(starts_a, starts_b)]
        if drift[0] != 0:
            fails.append(f"cycle 0 drift {drift[0]} ticks, want 0 (unison)")
        if any(y <= x for x, y in zip(drift, drift[1:])):
            fails.append("drift is not strictly increasing cycle-on-cycle")
        if any(d >= P * en.PPQ for d in drift[:-1]):
            fails.append("B laps A before the final cycle")
        if drift[-1] != round(P * en.PPQ):
            fails.append(f"final drift {drift[-1]} ticks != P = "
                         f"{round(P * en.PPQ)} ticks (must lap exactly once)")
    else:
        fails.append("cycle grid wrong; see pattern_identity")
    if abs((CYCLES - 1) * P * (RATIO - 1.0) - P) > 1e-6:
        fails.append("constants inconsistent: (CYCLES-1)*P*(RATIO-1) = "
                     f"{(CYCLES - 1) * P * (RATIO - 1.0):.8f} != P = {P} "
                     "(the schedule cannot lap exactly once)")
    results.append(("lap_exactly_once", fails))

    # --- clock_resultant_subset: every clock onset within 30 ticks of an
    #     accent (event-derived octave dyads) of A or B, pitch +12 ----------
    fails = []
    accents = sorted((t, max(p for p, _v in notes))
                     for grp in (grp_a, grp_b) for t, notes in grp
                     if len(notes) >= 2)
    acc_ticks = [t for t, _p in accents]
    ons_c = _note_ons(sc, CH_CLOCK)
    for tick, p, _v in ons_c:
        i = bisect.bisect_left(acc_ticks, tick - EPS_TICKS)
        ok = False
        while i < len(accents) and accents[i][0] <= tick + EPS_TICKS:
            if accents[i][1] + 12 == p:
                ok = True
                break
            i += 1
        if not ok:
            fails.append(f"clock note {p} at tick {tick} has no matching "
                         f"accent within {EPS_TICKS} ticks")
    results.append(("clock_resultant_subset", fails))

    # --- clock_midpoint_entry ----------------------------------------------
    fails = []
    if not ons_c:
        fails.append("the clock channel never plays")
    else:
        if ons_c[0][0] != _tick(MID):
            fails.append(f"clock enters at tick {ons_c[0][0]}, want "
                         f"{_tick(MID)} (beat {MID})")
        if ons_c[-1][0] < _tick(END - 2 * P):
            fails.append("clock abandons the piece before the lap")
        if any(t < _tick(MID) or t >= _tick(END) for t, _p, _v in ons_c):
            fails.append("clock plays outside [MID, END)")
    results.append(("clock_midpoint_entry", fails))

    # --- dynamic_arc: per-16-bar (48-beat) velocity means rise then fall ---
    fails = []
    edges = [0.0, 48.0, 96.0, 144.0, 192.0, 240.0, 288.0, END]
    means: list[float] = []
    both = ons_a + ons_b
    for lo, hi in zip(edges, edges[1:]):
        vels = [v for t, _p, v in both
                if _tick(lo) <= t < _tick(hi)]
        means.append(sum(vels) / len(vels) if vels else 0.0)
    k = means.index(max(means))
    if k in (0, len(means) - 1):
        fails.append(f"arc peak in window {k}: must be interior")
    for i in range(k):
        if means[i + 1] <= means[i]:
            fails.append(f"window {i}->{i + 1} does not rise "
                         f"({means[i]:.1f} -> {means[i + 1]:.1f})")
    for i in range(k, len(means) - 1):
        if means[i + 1] >= means[i]:
            fails.append(f"window {i}->{i + 1} does not fall "
                         f"({means[i]:.1f} -> {means[i + 1]:.1f})")
    results.append(("dynamic_arc", fails))

    # --- lydian_collection ---------------------------------------------------
    fails = []
    for ch in (CH_A, CH_B, CH_CLOCK):
        bad = sorted({p % 12 for _t, p, _v in _note_ons(sc, ch)}
                     - LYDIAN_PCS)
        if bad:
            fails.append(f"ch{ch} sounds pitch classes {bad} outside "
                         f"C lydian")
    bed_pcs = {p % 12 for _t, p, _v in _note_ons(sc, CH_BED)}
    if not bed_pcs <= {0, 7}:
        fails.append(f"bed pitch classes {sorted(bed_pcs)} != C/G")
    if 0 not in bed_pcs:
        fails.append("bed never sounds the lydian root C")
    results.append(("lydian_collection", fails))

    # --- zero_humanisation: EVERY channel realises the schedule exactly ----
    fails = []
    for ch in (CH_A, CH_B, CH_CLOCK, CH_BED):
        got = _note_ons(sc, ch)
        want = _expected_notes(ch)
        if got != want:
            fails.append(f"ch{ch}: {len(got)} events vs {len(want)} "
                         f"scheduled, or tick/velocity jitter present")
    results.append(("zero_humanisation", fails))

    # --- rooms_hard_panned: A left, B right, transients only ---------------
    fails = []
    for ch, want in ((CH_A, PAN_A), (CH_B, PAN_B)):
        pans = [(tick, data[2]) for tick, _prio, data in sc.events.get(ch, [])
                if (data[0] & 0xF0) == 0xB0 and data[1] == 10]
        if not pans:
            fails.append(f"ch{ch} authors no pan")
        elif any(v != want for _t, v in pans):
            fails.append(f"ch{ch} pan values {sorted({v for _t, v in pans})} "
                         f"!= {want}")
    if not PAN_A <= 20:
        fails.append(f"room A pan {PAN_A} is not hard left (<= 20)")
    if not PAN_B >= 108:
        fails.append(f"room B pan {PAN_B} is not hard right (>= 108)")
    results.append(("rooms_hard_panned", fails))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/06 - ....wav exists.
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    # 1. The dynamic arc must be audible: per-16-bar RMS rises to an
    #    interior peak then falls, with honest tolerances.
    edges = [0.0, 48.0, 96.0, 144.0, 192.0, 240.0, 288.0, END]
    means = []
    for lo, hi in zip(edges, edges[1:]):
        i0, i1 = ctx.bar_window(lo, hi)
        means.append(ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1)))
    fails: list[str] = []
    k = means.index(max(means))
    if k in (0, len(means) - 1):
        fails.append(f"render arc peak in window {k}: must be interior")
    for i in range(k):
        if means[i + 1] < means[i] - 0.8:
            fails.append(f"render rise broken at window {i}->{i + 1} "
                         f"({means[i]:.1f} -> {means[i + 1]:.1f} dB)")
    for i in range(k, len(means) - 1):
        if means[i + 1] > means[i] + 0.8:
            fails.append(f"render fall broken at window {i}->{i + 1} "
                         f"({means[i]:.1f} -> {means[i + 1]:.1f} dB)")
    if means[k] - means[0] < 1.0:
        fails.append(f"render arc rises only {means[k] - means[0]:.2f} dB "
                     f"(want >= 1.0)")
    if means[k] - means[-1] < 2.0:
        fails.append(f"render arc falls only {means[k] - means[-1]:.2f} dB "
                     f"(want >= 2.0)")
    checks.append(("audio_dynamic_arc", fails))

    # 2. Two rooms: the hard-panned mallets must give the first half real
    #    stereo width — side energy within 14 dB of mid energy.
    fails = []
    i0, i1 = ctx.bar_window(0.0, MID)
    i1 = min(i1, len(ctx.l))
    mid_acc = side_acc = 0.0
    n = 0
    for i in range(i0, i1, 4):                    # stride 4: plenty
        m = (ctx.l[i] + ctx.r[i]) / 2.0
        s = (ctx.l[i] - ctx.r[i]) / 2.0
        mid_acc += m * m
        side_acc += s * s
        n += 1
    if n == 0:
        fails.append("no samples in the first half")
    else:
        width_db = (ctx.db((side_acc / n) ** 0.5)
                    - ctx.db((mid_acc / n) ** 0.5))
        if width_db < -14.0:
            fails.append(f"side energy {width_db:.1f} dB below mid "
                         f"(want >= -14): the rooms are not panned apart")
    checks.append(("audio_two_rooms_width", fails))

    return checks


# ---------------------------------------------------------------------------
# Builders — one per movement; each writes exactly the schedule's events
# whose (tick-quantised) onsets fall inside its own beat range.
# ---------------------------------------------------------------------------

def _movement_builder(t0: float, t1: float, first: bool):
    lo, hi = _tick(t0), _tick(t1)

    def build(sc: en.Score) -> None:
        for ch, room in ((CH_A, "A"), (CH_B, "B")):
            for t, p, v, d in room_events(room):
                if lo <= _tick(t) < hi:
                    sc.note(ch, p, t, d, v, jt=0, jv=0)
        for t, p in clock_events():
            if lo <= _tick(t) < hi:
                sc.note(CH_CLOCK, p, t, CLOCK_DUR, _clock_vel(t),
                        jt=0, jv=0)
        for bt, bp, bv in _bed_events():
            if lo <= _tick(bt) < hi:
                sc.note(CH_BED, bp, bt, (t1 - bt) - 0.1, bv, jt=0, jv=0)
        if first:
            # The bed breathes with the arc; CC events are unbounded.
            en.cc_curve(sc, CH_BED, 11,
                        [(0.0, 48), (PEAK, 84), (END, 40)], step=P)

    return build


BUILDERS: list = [_movement_builder(t0, t1, i == 0)
                  for i, (_name, t0, t1) in enumerate(MOVS)]
