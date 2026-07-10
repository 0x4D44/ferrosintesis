"""t09_wirewalker — Track 9 "Wirewalker" of *Through Lines*.

Disc 2, 'Lines of Flight' — Fine Line II: the slackline (HLD section 3,
T9).  The literal fine line: one solo fiddle — the walker — crosses a
huge registral void in cycles of material.WALKER_THEME, its ambitus
clamped to a perfect fifth (A3..E4: the wire) until the final section.
THE REGISTER GAP: until the platform chord at beat 230, no other
channel may sound anywhere in [C3, C5) — the contrabass depth lies far
below (<= B2), the high-strings halo and music-box glints far above
(>= E5/C6-region); the walker is the ONLY thing on the wire, and lives
entirely INSIDE the void.

Meter: alternating 5/8 + 6/8 bars (each phrase re-balances: swell
through the five, settle through the six), with EXACTLY ONE 4/8 bar —
the mid-piece stumble at beat 145.5, where the walker drops the last
two steps of the cycle (theme truncated to nine notes), the bass lurches
into a Bb2/A2 minor-second crunch, the glints cluster F7/E7, the tempo
sags to 52, and the walker's deepest pitch-bend wobble falls away — all
recovered with grace within the next cycle.  Wobbles: hand-drawn bend
excursions that ALWAYS return within 2% of centre within one beat.

The far platform (movement V, beat 230): the void finally fills — a warm
pad chord spanning the forbidden register (A3/E4/A4), blooming into an
A-major picardy at beat 241 (C#4 enters, harp strums across the void)
as the walker rests, then climbs an A-major scale off the wire — the
one place the P5 clamp opens — arriving on a long held A4 at 250.5.

Written oracle-first (the repo method): every headline claim above is a
falsifiable oracle below, composed-to-pass — casting; the meter lane
(strict 5/8+6/8 alternation, contiguous bar grid, exactly one 4/8, at
the stumble beat, in the middle third); walker theme fidelity RECOMPUTED
from material.py (43 cycles, the stumble cycle truncated to 9 notes,
then the ascent); the walker's onset schedule and the 5/8-bar phrase
alignment; the P5 ambitus until the platform; the register gap and its
FLIP (movement V *requires* mid-register content); wobble recovery
(<= 1 beat, >= 10 wobbles, the deepest is the lurch and it lives in the
stumble bar); the stumble's cross-register dissonance and its
confinement; the walker's dynamic arc (per-movement velocity means rise
to IV, fall away in V).  audio_checks mirrors the headline render
claims: the stumble accent, the picardy filling the void (Goertzel at
C#4 = 277.18 Hz, a pitch class the walker never sounds before beat
241), the crescendo arc, and the final fade.  No material.py Morse or
FABLE quote is assigned to T9 (the HLD gives it the walker theme, which
T10 recalls).

All randomness (wobble placement/depth) comes from a random.Random
seeded from SEED, constructed inside the function that uses it —
rebuilds are byte-identical.
"""

from __future__ import annotations

import math
import random

import conductor
import engine as en
import material

NUMBER = 9
TITLE = 'Wirewalker'
FILE = '09 - Wirewalker.mid'
SEED = 20260909

COMMENT = ("Fine Line II: a solo fiddle crosses a registral void on a "
           "perfect-fifth wire, in alternating 5/8+6/8; one 4/8 stumble "
           "bar mid-piece, recovered with grace; the far platform fills "
           "the forbidden middle register with a warm picardy chord.")

# ---------------------------------------------------------------------------
# The wire.
# ---------------------------------------------------------------------------

CH_WALKER, CH_BASS, CH_HALO, CH_SPARK, CH_PAD, CH_HARP = 0, 1, 2, 3, 4, 5

ROOT = 57                    # A3: degree 1 of the wire (A aeolian)
GAP_LO, GAP_HI = 48, 72      # the forbidden register [C3, C5)
END = 285.0

CYCLE = 5.5                  # one 5/8 bar (2.5) + one 6/8 bar (3.0)
N_CYCLES = 43                # walker cycles, k = 0..42, first at beat 5.5
STUMBLE_CYCLE = 25           # the cycle whose 6/8 bar collapses to 4/8
STUMBLE_NOTES = 9            # the stumble cycle drops the last two steps
STUMBLE_PAIR = 143.0         # the stumble cycle's 5/8 bar
STUMBLE_BAR = 145.5          # THE 4/8 bar (the only one)
STUMBLE_END = 147.5

PLATFORM = 230.0             # movement V: the gap check flips here
BLOOM = 241.0                # the picardy third enters
ARRIVAL = 250.5              # the walker's held A4
ASCENT_T0 = 243.5            # the climb off the wire begins

MOVS: list[tuple[str, float, float]] = [
    ("I. First Steps", 0.0, 66.0),
    ("II. Mid-Span", 66.0, 132.0),
    ("III. The Stumble", 132.0, 164.0),
    ("IV. Second Wind", 164.0, 230.0),
    ("V. The Far Platform", 230.0, 285.0),
]

# The walker's velocity world: per-movement bases (dynamic-arc oracle)
# plus an 11-step phrase contour peaking on the far reach (degree 5).
PHRASE = (0, 1, 2, 1, 0, 2, 3, 4, 3, 2, 1)


def _cycle_start(k: int) -> float:
    """Cycle k's 5/8 downbeat: 5.5(k+1), one beat earlier after the
    stumble cycle's 4/8 bar swallowed two eighths."""
    return CYCLE * (k + 1) - (1.0 if k > STUMBLE_CYCLE else 0.0)


def _cycle_vel(k: int) -> float:
    if k <= 10:                       # I  — tentative
        return en.lerp(48.0, 56.0, k / 10)
    if k <= 22:                       # II — settling in
        return en.lerp(62.0, 68.0, (k - 11) / 11)
    if k <= 28:                       # III — tension (25 handled apart)
        return en.lerp(68.0, 74.0, (k - 23) / 5)
    if k <= 40:                       # IV — second wind (the peak)
        return en.lerp(76.0, 84.0, (k - 29) / 11)
    return 60.0 if k == 41 else 58.0  # V  — the last quiet steps


def _breath_bias(k: int) -> int:
    if k <= 10:
        return -6                     # I breathes shallow: thin first steps
    if k <= 22:
        return 4
    if k <= 28:
        return 8
    if k <= 40:
        return 16                     # IV breathes deep: the second wind
    return 2


def _bar_grid() -> list[tuple[float, int, int]]:
    """The full per-bar time-signature lane: 5/8+6/8 pairs, one 4/8."""
    bars: list[tuple[float, int, int]] = []
    t = 0.0
    while t < STUMBLE_PAIR - 1e-9:
        bars.append((t, 5, 8))
        bars.append((t + 2.5, 6, 8))
        t += CYCLE
    bars.append((STUMBLE_PAIR, 5, 8))
    bars.append((STUMBLE_BAR, 4, 8))
    t = STUMBLE_END
    while t < END - 1e-9:
        bars.append((t, 5, 8))
        bars.append((t + 2.5, 6, 8))
        t += CYCLE
    return bars


def _pair_starts() -> list[float]:
    return [b for b, num, _den in _bar_grid() if num == 5]


def _ascent_pitches() -> list[int]:
    """The climb off the wire: one A-major scale, A3 up to A4."""
    return [en.pitch(ROOT, "ionian", d) for d in range(1, 9)]


# ---------------------------------------------------------------------------
# Wobbles — bend excursions that always recover.  Depth is in semitones
# (frac = semis/2 at the synth's +/-2 range); every non-lurch wobble
# stays under frac 0.145, the lurch alone reaches 0.225.
# ---------------------------------------------------------------------------

WOBBLE_CYCLES = (12, 15, 18, 21, 24, 27, 30, 32, 35, 38, 40)
_WOBBLE_SHAPE = ((0.0, 0.0), (0.135, 0.7), (0.27, 1.0), (0.405, 0.5),
                 (0.54, -0.25), (0.675, -0.08), (0.81, 0.0))
LURCH_DEPTH = -0.45          # semitones: the stumble's falling lean


def _wobble_plan() -> list[tuple[float, float]]:
    """(start_beat, depth_semis) for every wobble, lurch last.
    Deterministic: fresh SEED-derived Random inside the function."""
    rng = random.Random(SEED * 7919 + 11)
    plan: list[tuple[float, float]] = []
    for k in WOBBLE_CYCLES:
        off = rng.choice((1.0, 1.5, 2.0, 2.5, 3.0))
        depth = rng.uniform(0.16, 0.27) * rng.choice((1.0, -1.0))
        plan.append((_cycle_start(k) + off, depth))
    plan.append((STUMBLE_BAR, LURCH_DEPTH))
    return plan


# ---------------------------------------------------------------------------
# PART — grid, tempo, channels.
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVS,
    tempo_map=[
        (0.0, 60.0),         # cautious first steps
        (66.0, 64.0),        # mid-span confidence
        (132.0, 63.0),       # the wire tightens
        (143.0, 61.0),
        (145.5, 52.0),       # the stumble: time stretches
        (147.5, 58.0),       # grace: gathering again
        (153.0, 64.0),       # recovered
        (164.0, 67.0),       # second wind
        (230.0, 62.0),       # the platform in sight
        (241.0, 58.0),       # the bloom
        (263.5, 54.0),
        (274.0, 50.0),       # final fade
    ],
    time_signatures=_bar_grid(),
    keysigs=[(0.0, 0, 1),    # A minor
             (BLOOM, 3, 0)],  # A major: the picardy
    channels=[
        (CH_WALKER, "the walker - fiddle", 110, 105, 64, 45),
        (CH_BASS, "the depth - contrabass", 43, 100, 64, 40),
        (CH_HALO, "the halo - high strings", 49, 85, 64, 70),
        (CH_SPARK, "the glints - music box", 10, 80, 64, 75),
        (CH_PAD, "the platform - warm pad", 89, 95, 64, 60),
        (CH_HARP, "the platform - harp", 46, 90, 74, 55),
    ],
    extra_markers=[
        (5.5, "the walker steps on"),
        (STUMBLE_BAR, "the stumble"),
        (BLOOM, "the picardy blooms"),
        (ARRIVAL, "arrival - A4"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {10, 43, 46, 49, 89, 110}
CENTERED_CHANNELS: set[int] = {CH_WALKER, CH_BASS, CH_HALO, CH_PAD}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_WALKER: (57, 69),     # the wire (A3..E4), + the ascent to A4
    CH_BASS: (36, 47),       # far below the gap, floored at C2
    CH_HALO: (76, 96),       # far above the gap
    CH_SPARK: (84, 108),     # farther still
    CH_PAD: (57, 76),        # the platform chord (movement V only)
    CH_HARP: (48, 81),       # across the void (movement V only)
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (276.0, 282.0)   # measured 278.8 s
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

CASTING = {CH_WALKER: 110, CH_BASS: 43, CH_HALO: 49,
           CH_SPARK: 10, CH_PAD: 89, CH_HARP: 46}


# ---------------------------------------------------------------------------
# Oracle helpers.
# ---------------------------------------------------------------------------

def _ons(sc: en.Score, ch: int) -> list[tuple[float, int, int]]:
    """(beat, pitch, vel) of every note-on, sorted."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick / en.PPQ, data[1], data[2]))
    return sorted(out)


def _spans(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """(on, off, pitch, vel) with FIFO on/off pairing, sorted."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick / en.PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick / en.PPQ, data[1], vel))
    return sorted(out)


def _bends(sc: en.Score, ch: int) -> list[tuple[float, float]]:
    """(beat, bend fraction of full range), sorted."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / en.PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _ic1_overlaps(spans) -> list[tuple[float, float]]:
    """Time windows where two notes a minor second apart (mod 12) sound
    simultaneously (> 0.05 beats of overlap)."""
    out = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a_on, a_off, a_p, _ = spans[i]
            b_on, b_off, b_p, _ = spans[j]
            if (a_p - b_p) % 12 in (1, 11):
                lo, hi = max(a_on, b_on), min(a_off, b_off)
                if hi - lo > 0.05:
                    out.append((lo, hi))
    return out


def _tempo_at(sc: en.Score, beat: float) -> float:
    bpm = sorted(sc.tempos)[0][1]
    for b, v in sorted(sc.tempos):
        if b <= beat:
            bpm = v
        else:
            break
    return bpm


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the builders; the music is composed to pass.
# ---------------------------------------------------------------------------

def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []
    walker = _ons(sc, CH_WALKER)

    # --- casting: fixed programs, no drums, no mid-track changes ----------
    fails: list[str] = []
    part_progs = {ch: prog for ch, _n, prog, _v, _p, _r in PART.CHANNELS}
    if part_progs != CASTING:
        fails.append(f"channel programs {part_progs} != {CASTING}")
    for ch, want in CASTING.items():
        progs = [(tick / en.PPQ, data[1]) for tick, _prio, data
                 in sc.events.get(ch, []) if (data[0] & 0xF0) == 0xC0]
        if progs != [(0.0, want)]:
            fails.append(f"ch{ch} program events {progs} != [(0.0, {want})]")
    if any((data[0] & 0xF0) == 0x90 and data[2] > 0
           for _t, _p, data in sc.events.get(9, [])):
        fails.append("channel 10 percussion must stay silent - no net")
    results.append(("casting", fails))

    # --- meter_lane: 5/8+6/8 alternation, one 4/8, contiguous, mid --------
    fails = []
    ts = sorted(sc.timesigs)
    if not ts or ts[0] != (0.0, 5, 8):
        fails.append(f"grid must open with 5/8 at beat 0, got {ts[:1]}")
    fours = [b for b, num, _d in ts if num == 4]
    if len(fours) != 1:
        fails.append(f"{len(fours)} 4/8 bars, want exactly 1")
    else:
        if abs(fours[0] - STUMBLE_BAR) > 1e-6:
            fails.append(f"the 4/8 bar sits at {fours[0]}, want "
                         f"{STUMBLE_BAR} (the stumble)")
        if not END / 3 <= fours[0] <= 2 * END / 3:
            fails.append(f"the 4/8 bar at {fours[0]} is not mid-piece")
    expect = 0.0
    for idx, (b, num, den) in enumerate(ts):
        if den != 8:
            fails.append(f"bar {idx} denominator {den} != 8")
            break
        if abs(b - expect) > 1e-6:
            fails.append(f"bar {idx} at {b} breaks the contiguous grid "
                         f"(expected {expect})")
            break
        if idx % 2 == 0 and num != 5:
            fails.append(f"bar {idx} is {num}/8, alternation wants 5/8")
            break
        if idx % 2 == 1 and num not in (4, 6):
            fails.append(f"bar {idx} is {num}/8, alternation wants 6/8 "
                         f"(or the one 4/8)")
            break
        expect = b + num * 0.5
    else:
        if abs(expect - END) > 1e-6:
            fails.append(f"bar grid ends at {expect}, want {END}")
    results.append(("meter_lane", fails))

    # --- walker_theme_fidelity: recomputed from material.py ---------------
    fails = []
    theme = [en.deg_semis(material.WALKER_MODE, d)
             for d in material.WALKER_THEME]
    if max(theme) - min(theme) > 7:
        fails.append("material walker theme exceeds a P5")
    if abs(len(theme) * material.WALKER_STEP - CYCLE) > 1e-9:
        fails.append("material cycle length disagrees with the 5/8+6/8 "
                     "pair")
    want: list[int] = []
    for k in range(N_CYCLES):
        seq = theme[:STUMBLE_NOTES] if k == STUMBLE_CYCLE else theme
        want.extend(ROOT + s for s in seq)
    ascent = _ascent_pitches()
    if any(b <= a for a, b in zip(ascent, ascent[1:])):
        fails.append("the ascent must be strictly ascending")
    want.extend(ascent)
    got = [p for _b, p, _v in walker]
    if len(got) != len(want):
        fails.append(f"walker plays {len(got)} notes, want {len(want)} "
                     f"(43 cycles, one truncated to 9, + 8 ascent)")
    else:
        bad = [i for i, (g, w) in enumerate(zip(got, want)) if g != w]
        if bad:
            fails.append(f"walker pitch diverges from the material theme "
                         f"at note {bad[0]} (got {got[bad[0]]}, want "
                         f"{want[bad[0]]})")
    results.append(("walker_theme_fidelity", fails))

    # --- walker_schedule: eighth-step cycles on the 5/8 downbeats ---------
    fails = []
    want_on: list[float] = []
    for k in range(N_CYCLES):
        cs = CYCLE * (k + 1) - (1.0 if k > STUMBLE_CYCLE else 0.0)
        cnt = STUMBLE_NOTES if k == STUMBLE_CYCLE else len(
            material.WALKER_THEME)
        want_on.extend(cs + material.WALKER_STEP * i for i in range(cnt))
    want_on.extend(ASCENT_T0 + float(i) for i in range(7))
    want_on.append(ARRIVAL)
    if len(walker) == len(want_on):
        for i, ((b, _p, _v), w) in enumerate(zip(walker, want_on)):
            if abs(b - w) > 0.035:
                fails.append(f"walker note {i} at beat {b:.3f}, "
                             f"schedule wants {w:.3f}")
                break
    else:
        fails.append("note count wrong (see walker_theme_fidelity)")
    five_starts = {round(b, 6) for b, num, _d in sc.timesigs if num == 5}
    for k in range(N_CYCLES):
        if round(_cycle_start(k), 6) not in five_starts:
            fails.append(f"cycle {k} does not start on a 5/8 downbeat")
    held = [s for s in _spans(sc, CH_WALKER)
            if abs(s[0] - ARRIVAL) <= 0.035]
    if not held:
        fails.append("no held arrival note at beat 250.5")
    else:
        on, off, p, _v = held[-1]
        if p != 69:
            fails.append(f"arrival pitch {p} != 69 (A4)")
        if not 266.0 <= off <= 270.0:
            fails.append(f"arrival hold ends at {off:.1f}, want 266..270")
    if walker and abs(walker[-1][0] - ARRIVAL) > 0.035:
        fails.append("the held A4 must be the walker's final note")
    results.append(("walker_schedule", fails))

    # --- walker_ambitus: a P5 until the platform, then the octave ---------
    fails = []
    pre = [p for b, p, _v in walker if b < PLATFORM - 0.1]
    post = [p for b, p, _v in walker if b >= PLATFORM - 0.1]
    if pre:
        if min(pre) < 57 or max(pre) > 64:
            fails.append(f"pre-platform walker range [{min(pre)},"
                         f"{max(pre)}] leaves the wire [57,64]")
        if max(pre) - min(pre) > 7:
            fails.append(f"pre-platform ambitus {max(pre) - min(pre)} "
                         f"exceeds a P5")
    else:
        fails.append("walker never walks before the platform")
    if post:
        if min(post) < 57 or max(post) > 69:
            fails.append(f"final-section walker range [{min(post)},"
                         f"{max(post)}] outside [57,69]")
        if max(post) != 69:
            fails.append("the freedom is never used: no A4 in the final "
                         "section")
    else:
        fails.append("walker absent from the final section")
    results.append(("walker_ambitus", fails))

    # --- register_gap: NOTHING else in [C3, C5) until the platform;
    #     the walker lives entirely inside the void ------------------------
    fails = []
    for ch in (CH_BASS, CH_HALO, CH_SPARK, CH_PAD, CH_HARP):
        for b, p, _v in _ons(sc, ch):
            if b < PLATFORM - 0.1 and GAP_LO <= p < GAP_HI:
                fails.append(f"ch{ch} pitch {p} at beat {b:.1f} invades "
                             f"the void before the platform chord")
    for b, p, _v in walker:
        if not GAP_LO <= p < GAP_HI:
            fails.append(f"walker pitch {p} at {b:.1f} strays outside "
                         f"the void [C3, C5)")
    results.append(("register_gap", fails))

    # --- platform_fill: the gap check FLIPS — movement V must fill it -----
    fails = []
    pad = _ons(sc, CH_PAD)
    if not pad:
        fails.append("the platform pad never sounds")
    else:
        if abs(pad[0][0] - PLATFORM) > 0.02:
            fails.append(f"platform chord at {pad[0][0]:.2f}, want "
                         f"{PLATFORM}")
        chord0 = {p for b, p, _v in pad if abs(b - PLATFORM) <= 0.02}
        if not {57, 64} <= chord0:
            fails.append(f"opening platform chord {sorted(chord0)} must "
                         f"contain A3+E4 (57, 64)")
        if len([p for p in chord0 if GAP_LO <= p < GAP_HI]) < 2:
            fails.append("platform chord must span the forbidden register")
        if not any(abs(b - BLOOM) <= 0.02 and p == 61 for b, p, _v in pad):
            fails.append("no C#4 pad onset at beat 241: the picardy "
                         "never blooms")
    mid_notes = [(b, off, p) for ch in (CH_BASS, CH_HALO, CH_SPARK,
                                        CH_PAD, CH_HARP)
                 for b, off, p, _v in _spans(sc, ch)
                 if b >= PLATFORM - 0.1 and GAP_LO <= p < GAP_HI]
    if len({p for _b, _o, p in mid_notes}) < 3:
        fails.append("movement V must fill the void with >= 3 distinct "
                     "mid-register pitches")
    if not mid_notes or max(off for _b, off, _p in mid_notes) < 280.0:
        fails.append("mid-register warmth must sustain to beat >= 280")
    sounding = {p % 12 for b, off, p in mid_notes if b <= 281.0 <= off}
    if not {9, 1, 4} <= sounding:
        fails.append(f"pitch classes sounding at beat 281 {sorted(sounding)}"
                     f" must contain the A-major triad {{9, 1, 4}}")
    results.append(("platform_fill", fails))

    # --- wobble_recovery: every bend back within 2% within one beat -------
    fails = []
    fr = _bends(sc, CH_WALKER)
    dep = None
    n_wob = 0
    worst, worst_beat = 0.0, None
    for b, f in fr:
        if abs(f) > worst:
            worst, worst_beat = abs(f), b
        if dep is None and abs(f) > 0.02:
            dep = b
            n_wob += 1
        elif dep is not None and abs(f) <= 0.02:
            if b - dep > 1.0 + 1e-6:
                fails.append(f"wobble at {dep:.2f} takes {b - dep:.2f} "
                             f"beats to recentre (> 1)")
            dep = None
    if dep is not None:
        fails.append(f"wobble at {dep:.2f} never recentres")
    if n_wob < 10:
        fails.append(f"only {n_wob} wobbles: the walk is too steady "
                     f"(want >= 10)")
    if worst_beat is None or not 0.15 <= worst <= 0.35:
        fails.append(f"deepest wobble {worst:.3f} of range outside "
                     f"[0.15, 0.35]")
    elif not STUMBLE_PAIR <= worst_beat <= STUMBLE_END:
        fails.append(f"deepest wobble at {worst_beat:.2f} is not the "
                     f"stumble lurch")
    off_lurch = [abs(f) for b, f in fr
                 if not STUMBLE_PAIR - 0.1 <= b <= STUMBLE_END + 0.1]
    if off_lurch and max(off_lurch) > 0.146:
        fails.append(f"a non-lurch wobble reaches {max(off_lurch):.3f} "
                     f"(cap 0.146): the lurch must stand alone")
    if any(b >= 229.0 for b, _f in fr):
        fails.append("no wobbles allowed on the platform approach "
                     "(beat >= 229)")
    for ch in (CH_BASS, CH_HALO, CH_SPARK, CH_PAD, CH_HARP):
        if _bends(sc, ch):
            fails.append(f"ch{ch} bends: only the walker wobbles")
    results.append(("wobble_recovery", fails))

    # --- stumble_lurch: cross-register dissonance, confined, graced -------
    fails = []
    bass_ic = _ic1_overlaps(_spans(sc, CH_BASS))
    if not any(abs(lo - STUMBLE_BAR) <= 0.2 for lo, _hi in bass_ic):
        fails.append("no bass minor-second crunch at the stumble bar")
    for lo, hi in bass_ic:
        if not STUMBLE_PAIR - 0.1 <= lo and hi <= STUMBLE_END + 0.1:
            fails.append(f"bass dissonance at [{lo:.1f},{hi:.1f}] outside "
                         f"the stumble cycle")
    spark_at = {p for b, p, _v in _ons(sc, CH_SPARK)
                if STUMBLE_BAR - 0.2 <= b <= STUMBLE_BAR + 0.2}
    if not {100, 101} <= spark_at:
        fails.append(f"stumble glint cluster {sorted(spark_at)} must "
                     f"contain E7+F7 (100, 101)")
    spark_ic = _ic1_overlaps(_spans(sc, CH_SPARK))
    if not spark_ic:
        fails.append("the glints never cluster at the stumble")
    for lo, hi in spark_ic:
        if not STUMBLE_PAIR - 0.1 <= lo and hi <= STUMBLE_END + 0.1:
            fails.append(f"glint dissonance at [{lo:.1f},{hi:.1f}] "
                         f"outside the stumble cycle")
    halo_ic = _ic1_overlaps(_spans(sc, CH_HALO))
    if not any(hi - lo >= 4.0 for lo, hi in halo_ic):
        fails.append("the halo never tightens (want an E6/F6 rub >= 4 "
                     "beats in III)")
    for lo, hi in halo_ic:
        if not 132.0 - 0.1 <= lo and hi <= 164.0:
            fails.append(f"halo dissonance at [{lo:.1f},{hi:.1f}] outside "
                         f"movement III")
    sag = _tempo_at(sc, STUMBLE_BAR + 0.1)
    if sag > _tempo_at(sc, STUMBLE_PAIR + 0.1) - 6:
        fails.append("tempo does not sag at the stumble")
    if sag > _tempo_at(sc, STUMBLE_END + 0.1) - 5:
        fails.append("tempo does not pick back up after the stumble")
    if _tempo_at(sc, 153.5) < sag + 10:
        fails.append("the recovery never regains its stride")
    results.append(("stumble_lurch", fails))

    # --- dynamic_arc: per-movement walker velocity means -------------------
    fails = []
    means: list[float] = []
    for _name, t0, t1 in MOVS:
        vels = [v for b, _p, v in walker if t0 - 0.05 <= b < t1 - 0.05]
        means.append(sum(vels) / len(vels) if vels else 0.0)
    m1, m2, m3, m4, m5 = means
    if not m1 + 2 <= m2:
        fails.append(f"I -> II does not rise ({m1:.1f} -> {m2:.1f})")
    if not m2 + 2 <= m3:
        fails.append(f"II -> III does not rise ({m2:.1f} -> {m3:.1f})")
    if not m3 + 2 <= m4:
        fails.append(f"III -> IV does not rise ({m3:.1f} -> {m4:.1f})")
    if max(means) != m4:
        fails.append(f"movement IV must be the dynamic peak {means}")
    if not m5 <= m4 - 5:
        fails.append(f"V does not settle ({m4:.1f} -> {m5:.1f})")
    results.append(("dynamic_arc", fails))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/09 - Wirewalker.wav exists.
# ---------------------------------------------------------------------------

def _goertzel(ctx, beat0: float, beat1: float, freq: float) -> float:
    """Normalized mono amplitude at `freq` over [beat0, beat1)."""
    i0, i1 = ctx.bar_window(beat0, beat1)
    i0, i1 = max(0, i0), min(len(ctx.l), i1)
    if i1 <= i0:
        return 0.0
    w = 2.0 * math.pi * freq / ctx.sample_rate
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for i in range(i0, i1):
        s0 = (ctx.l[i] + ctx.r[i]) * 0.5 + coeff * s1 - s2
        s2, s1 = s1, s0
    power = s1 * s1 + s2 * s2 - coeff * s1 * s2
    return max(0.0, power) ** 0.5 / (i1 - i0)


def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    def _rms_db(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    # 1. The stumble lands: the 4/8 bar out-hits the preceding cycle.
    fails: list[str] = []
    hit = _rms_db(STUMBLE_BAR, STUMBLE_END)
    before = _rms_db(137.5, STUMBLE_PAIR)
    if hit < before + 0.7:
        fails.append(f"stumble bar {hit:.1f} dB vs {before:.1f} dB before "
                     f"(want >= +0.7)")
    checks.append(("audio_stumble_accent", fails))

    # 2. The picardy fills the void: C#4 (277.18 Hz) is a pitch class the
    #    piece never sounds before beat 241; after the bloom it must ring.
    fails = []
    csharp = 440.0 * 2.0 ** ((61 - 69) / 12.0)
    g_pre = _goertzel(ctx, 88.0, 102.0, csharp)
    g_post = _goertzel(ctx, 244.0, 258.0, csharp)
    if g_post <= 0:
        fails.append("no C#4 energy after the bloom")
    elif g_pre > 0:
        rise = 20.0 * math.log10(g_post / g_pre)
        if rise < 8.0:
            fails.append(f"C#4 rises only {rise:.1f} dB at the platform "
                         f"(want >= 8)")
    checks.append(("audio_picardy_fills_void", fails))

    # 3. The crescendo arc: second wind clearly above the first steps.
    fails = []
    lo, hi = _rms_db(11.0, 33.0), _rms_db(186.0, 208.0)
    if hi < lo + 2.0:
        fails.append(f"IV {hi:.1f} dB vs I {lo:.1f} dB (want >= +2)")
    checks.append(("audio_crescendo_arc", fails))

    # 4. The final fade: the last bars sink well below the arrival.
    fails = []
    tail, arrive = _rms_db(275.0, 284.0), _rms_db(244.0, 258.0)
    if tail > arrive - 4.0:
        fails.append(f"tail {tail:.1f} dB vs arrival {arrive:.1f} dB "
                     f"(want <= -4)")
    checks.append(("audio_final_fade", fails))

    return checks


# ---------------------------------------------------------------------------
# The texture plans — pure functions of the constants above.
# ---------------------------------------------------------------------------

def _texture_plan() -> list[tuple[float, int, int, float, float, int, int]]:
    """(beat, ch, pitch, dur, vel, jt, jv) for every non-spark note
    outside the walker's cycles (bass, halo, pad, harp, walker ascent)."""
    ev: list[tuple[float, int, int, float, float, int, int]] = []
    pairs = _pair_starts()

    # -- the depth: contrabass, far below the void -------------------------
    for p, at in enumerate(pairs):
        if p <= 11:                            # I — root/fifth rocking
            v = en.lerp(40.0, 47.0, p / 11)
            ev.append((at, CH_BASS, 45, 2.4, v, 3, 2))
            ev.append((at + 2.5, CH_BASS, 40, 2.9, v - 2, 3, 2))
        elif p <= 23:                          # II — the lament descent
            root = (45, 43, 41, 40)[(p - 12) % 4]
            second = {45: 40, 43: 38, 41: 36, 40: 40}[root]
            v = en.lerp(50.0, 56.0, (p - 12) / 11)
            ev.append((at, CH_BASS, root, 2.4, v, 3, 2))
            ev.append((at + 2.5, CH_BASS, second, 2.9, v - 2, 3, 2))
        elif p == 24:                          # III — pedal
            ev.append((at, CH_BASS, 40, 2.4, 56, 3, 2))
            ev.append((at + 2.5, CH_BASS, 40, 2.9, 54, 3, 2))
        elif p == 25:                          # III — the semitone grind
            ev.append((at, CH_BASS, 41, 2.4, 58, 3, 2))
            ev.append((at + 2.5, CH_BASS, 40, 2.9, 58, 3, 2))
        elif p == 26:                          # III — the LURCH
            ev.append((at, CH_BASS, 41, 2.4, 62, 3, 2))
            ev.append((STUMBLE_BAR, CH_BASS, 46, 1.9, 80, 2, 2))
            ev.append((STUMBLE_BAR, CH_BASS, 45, 1.9, 78, 2, 2))
        elif p <= 29:                          # III — grace
            v = {27: 56, 28: 54, 29: 52}[p]
            ev.append((at, CH_BASS, 45, 2.4, v, 3, 2))
            ev.append((at + 2.5, CH_BASS, 40, 2.9, v - 2, 3, 2))
        elif p <= 41:                          # IV — walking
            v = en.lerp(64.0, 74.0, (p - 30) / 11)
            ev.append((at, CH_BASS, 45, 2.4, v, 3, 2))
            ev.append((at + 2.5, CH_BASS, 43, 1.4, v - 2, 3, 2))
            ev.append((at + 4.0, CH_BASS, 40, 1.4, v - 1, 3, 2))
        else:                                  # V — pedal, fading
            v = en.lerp(40.0, 24.0, (p - 42) / 9)
            ev.append((at, CH_BASS, 45, 5.0 if p == 51 else 5.4, v, 3, 2))

    # -- the halo: high strings, far above ---------------------------------
    halo: list[tuple[float, int, float, float]] = []
    for i, b in enumerate((66.0, 77.0, 88.0, 99.0, 110.0, 121.0)):
        halo.append((b, 81, 10.9, 38.0 + 1.5 * i))
    for i, b in enumerate((99.0, 110.0, 121.0)):
        halo.append((b, 88, 10.9, 36.0 + 2.0 * i))
    halo += [(132.0, 88, 10.9, 48.0), (143.0, 88, 4.4, 52.0),
             (147.5, 88, 10.9, 50.0), (158.5, 88, 5.4, 48.0),
             (137.5, 89, 5.4, 44.0), (143.0, 89, 9.9, 46.0)]
    for m in range(6):
        b = 164.0 + 11.0 * m
        v = en.lerp(52.0, 64.0, m / 5)
        halo += [(b, 81, 10.9, v), (b, 88, 10.9, v - 2)]
    for i, b in enumerate((186.0, 197.0, 208.0, 219.0)):
        halo.append((b, 84, 10.9, 50.0 + 2.5 * i))
    halo += [(230.0, 81, 10.9, 46.0), (230.0, 88, 10.9, 44.0),
             (241.0, 81, 20.9, 50.0), (241.0, 88, 20.9, 47.0),
             (241.0, 85, 20.9, 47.0),
             (262.0, 81, 21.0, 27.0), (262.0, 88, 21.0, 25.0),
             (262.0, 85, 21.0, 25.0)]
    ev.extend((b, CH_HALO, pch, d, v, 4, 2) for b, pch, d, v in halo)

    # -- the platform pad: the void fills ----------------------------------
    for pch in (57, 64, 69):                   # open fifths first: safe
        ev.append((PLATFORM, CH_PAD, pch, 10.9, 46, 0, 2))
    for pch in (57, 61, 64, 69, 76):           # then the picardy warmth
        ev.append((BLOOM, CH_PAD, pch, 20.9, 58, 0, 2))
        ev.append((262.0, CH_PAD, pch, 21.0, 30, 0, 2))

    # -- the harp: strums and arps across the healed void ------------------
    for i, pch in enumerate((52, 57, 61, 64, 69, 73, 76)):
        ev.append((BLOOM + 0.06 * i, CH_HARP, pch, 4.0 - 0.06 * i,
                   54 - i, 2, 2))
    for t, v in ((246.5, 50), (252.0, 46), (257.5, 42), (263.0, 30),
                 (268.5, 26), (274.0, 22)):
        for i, pch in enumerate((57, 61, 64, 69, 73, 76)):
            ev.append((t + 0.25 * i, CH_HARP, pch, 0.6, v - i, 3, 2))
    for i, pch in enumerate((69, 73, 76)):
        ev.append((279.5 + 0.5 * i, CH_HARP, pch, 1.2, 18 - 2 * i, 3, 2))

    # -- the walker's ascent: off the wire, up the A-major scale -----------
    scale = _ascent_pitches()
    for i in range(7):
        ev.append((ASCENT_T0 + float(i), CH_WALKER, scale[i], 0.95,
                   en.lerp(62.0, 72.0, i / 6), 3, 2))
    ev.append((ARRIVAL, CH_WALKER, scale[7], 17.5, 74, 2, 2))
    return ev


def _spark_plan() -> list[tuple[float, int, float, float, int]]:
    """(beat, pitch, dur, vel, pan) — the music-box glints, panned
    transients (the only width source; every bed stays centred)."""
    ev: list[tuple[float, int, float, float, int]] = []
    side = (44, 84)
    for j, p in enumerate((0, 2, 4, 6, 8, 10)):            # I: distant
        ev.append((5.5 * p, 93 if j % 2 == 0 else 100, 1.2, 34.0,
                   side[j % 2]))
    for j in range(12):                                     # II
        at = 66.0 + 5.5 * j
        ev.append((at + 2.5, (93, 91, 95, 100)[j % 4], 1.0,
                   en.lerp(38.0, 44.0, j / 11), side[j % 2]))
    ev += [(132.0, 95, 1.0, 46.0, 44), (134.5, 95, 1.0, 48.0, 84),
           (137.5, 95, 1.0, 50.0, 44), (140.0, 95, 1.0, 52.0, 84),
           (STUMBLE_BAR, 101, 1.5, 64.0, 44),               # the cluster
           (STUMBLE_BAR + 0.05, 100, 1.5, 60.0, 84),
           (150.0, 93, 1.0, 40.0, 64), (155.5, 93, 1.0, 36.0, 44),
           (161.0, 93, 1.0, 32.0, 84)]
    pit1 = (93, 96, 95, 100, 91, 96)
    pit2 = (100, 93, 96, 91, 95, 93)
    for j in range(12):                                     # IV
        at = 164.0 + 5.5 * j
        v = en.lerp(44.0, 50.0, j / 11)
        ev.append((at + 1.0, pit1[j % 6], 0.8, v, side[j % 2]))
        ev.append((at + 4.0, pit2[j % 6], 0.8, v - 3, side[(j + 1) % 2]))
    ev += [(230.0, 93, 1.2, 40.0, 44), (235.5, 100, 1.2, 38.0, 84),
           (243.5, 97, 1.0, 44.0, 84),
           (ARRIVAL, 93, 1.5, 56.0, 64),                    # arrival echo
           (257.5, 100, 1.0, 40.0, 44), (263.0, 97, 1.0, 28.0, 84),
           (268.5, 93, 1.0, 24.0, 44), (274.0, 97, 1.0, 19.0, 84),
           (279.5, 93, 1.0, 15.0, 64)]
    return ev


def _cc_plans() -> dict[float, list[tuple[int, int, list, float]]]:
    """Movement-keyed CC envelopes: (ch, cc, points, step)."""
    return {
        66.0: [(CH_HALO, 11, [(66.0, 50), (99.0, 62), (131.5, 58)], 1.0)],
        132.0: [(CH_HALO, 11, [(132.0, 64), (145.5, 74), (153.0, 60),
                               (163.5, 58)], 1.0)],
        164.0: [(CH_HALO, 11, [(164.0, 68), (219.0, 82),
                               (229.5, 72)], 1.0)],
        230.0: [
            # the depth recedes: contrabass velocity is nearly level-flat
            # in the render, so the fade is authored as expression
            (CH_BASS, 11, [(230.0, 127), (256.0, 116), (263.0, 80),
                           (270.0, 48), (277.0, 30), (283.0, 18)], 1.0),
            (CH_HALO, 11, [(230.0, 64), (241.0, 78), (258.0, 62),
                           (262.0, 48), (283.0, 16)], 1.0),
            (CH_PAD, 11, [(230.0, 60), (241.0, 90), (252.0, 82),
                          (262.0, 54), (272.0, 32), (283.0, 14)], 1.0),
            (CH_WALKER, 11, [(241.5, 60), (243.5, 72), (250.5, 96),
                             (256.0, 92), (263.0, 70), (267.5, 40)], 0.75),
            # vibrato blooms on the held A4 (CC1: fiddle vibrato depth)
            (CH_WALKER, 1, [(251.0, 0), (254.0, 34), (260.0, 48),
                            (265.5, 26), (267.8, 0)], 0.5),
        ],
    }


# ---------------------------------------------------------------------------
# Builders — one per movement, all writing from the shared plans.
# ---------------------------------------------------------------------------

def _write_cycle(sc: en.Score, k: int, cs: float) -> None:
    seq = (material.WALKER_THEME[:STUMBLE_NOTES] if k == STUMBLE_CYCLE
           else material.WALKER_THEME)
    for i, deg in enumerate(seq):
        p = en.pitch(ROOT, material.WALKER_MODE, deg)
        v = 76.0 + i if k == STUMBLE_CYCLE else _cycle_vel(k) + PHRASE[i]
        sc.note(CH_WALKER, p, cs + material.WALKER_STEP * i, 0.46, v,
                jt=4, jv=3)
    # each phrase re-balances: swell through the 5, settle through the 6
    if k == STUMBLE_CYCLE:
        pts = [(cs, 88), (cs + 2.3, 96), (cs + 2.6, 100), (cs + 4.3, 78)]
    else:
        b = _breath_bias(k)
        pts = [(cs, 74 + b), (cs + 2.0, 90 + b), (cs + 2.5, 82 + b),
               (cs + 5.3, 70 + b)]
    en.cc_curve(sc, CH_WALKER, 11, pts, step=0.75)


def _wobble(sc: en.Score, t0: float, depth: float) -> None:
    for dt, m in _WOBBLE_SHAPE:
        sc.bend(CH_WALKER, t0 + dt, depth * m)


def _movement_builder(t0: float, t1: float):
    def build(sc: en.Score) -> None:
        for k in range(N_CYCLES):
            cs = _cycle_start(k)
            if t0 <= cs < t1:
                _write_cycle(sc, k, cs)
        for b, depth in _wobble_plan():
            if t0 <= b < t1:
                _wobble(sc, b, depth)
        for b, ch, pch, dur, vel, jt, jv in _texture_plan():
            if t0 <= b < t1:
                sc.note(ch, pch, b, dur, vel, jt=jt, jv=jv)
        for b, pch, dur, vel, pan in _spark_plan():
            if t0 <= b < t1:
                sc.cc(CH_SPARK, 10, pan, max(0.0, b - 0.02))
                sc.note(CH_SPARK, pch, b, dur, vel, jt=3, jv=3)
        for ch, num, pts, step in _cc_plans().get(t0, []):
            en.cc_curve(sc, ch, num, pts, step=step)
    return build


BUILDERS: list = [_movement_builder(t0, t1) for _name, t0, t1 in MOVS]
