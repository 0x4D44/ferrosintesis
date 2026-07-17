"""T8 — Split-S (HLD section 4, "T8 — Split-S").

The escape manoeuvre: roll inverted, pull through, exit pointing the other
way — the track that plays the album's shape backwards.  F# aeolian, 134 bpm,
4/4, ~4:11.

Architecture (all beats, all pinned by oracles below):
  I.    DROP ZERO   [0,64)    cold open — bar 1 IS the drop; the duo states
                              the 32-beat HOOK twice at full power (its first
                              four notes are material.ASCENT_CELL).
  II.   THE ROLL    [64,96)   strip-tease: per-2-bar active-channel count
                              falls strictly 15 > 10 > 6 > 3.
  III.  THE QUIET   [96,160)  bass + wing ship ALONE (the duet).
  IV.   BUILD ONE   [160,240) five strictly-rising 16-beat windows.
  V.    DROP ONE    [240,320) four-on-floor, hook restated; ends in an
                              8-beat lead soar (CC1 bloom + vibrato).
  VI.   BUILD TWO   [320,400) bigger: CC74 macro-sweep 34->112, portamento
                              swoop +12 semis, riser, densest fill run.
  VII.  PULL-THROUGH[400,496) DROP2 — > DROP1 and >= DROP0; hook + saw
                              counterpoint; 15-channel stack; new peak E6.
  VIII. EXIT        [496,560) the wing ship plays the OPEN hook in exact
                              tick-level RETROGRADE (the formation), then
                              both ships settle on F#.

Duo formation — RETROGRADE: wing(EXIT) = lead(OPEN) time-reversed about the
32-beat hook grid: onset' = HOOK_LEN - onset - dur, pitches and durations
identical.  hook_retrograde_exact recomputes the whole wing lane from the
lead lane in ticks and demands set equality.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 8
TITLE = "Split-S"
FILE = "08 - Split-S.mid"
SEED = 20261108
COMMENT = (
    "Split-S: the escape manoeuvre played backwards. The track opens inside "
    "its own drop at full power, peels its sixteen layers off one at a time "
    "through the inverted roll, falls to a bass-and-wing-guitar duet, then "
    "builds and drops twice more - the pull-through bigger than the cold "
    "open - before the wing ship flies the opening hook in exact retrograde "
    "as the exit. F# aeolian, 134 bpm."
)

# -- the beat grid ----------------------------------------------------------
D0_T0, D0_T1 = 0.0, 64.0          # I.   Drop Zero (cold open)
RL_T0, RL_T1 = 64.0, 96.0         # II.  The Roll
QU_T0, QU_T1 = 96.0, 160.0        # III. The Quiet
B1_T0, B1_T1 = 160.0, 240.0       # IV.  Build One
D1_T0, D1_T1 = 240.0, 320.0       # V.   Drop One
B2_T0, B2_T1 = 320.0, 400.0       # VI.  Build Two
D2_T0, D2_T1 = 400.0, 496.0       # VII. Pull-Through (Drop Two)
EX_T0, END = 496.0, 560.0         # VIII. Exit Retrograde

BPM = 134.0
MODE = "aeolian"
BASE = 66                          # F#4 — degree 1

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Drop Zero", D0_T0, D0_T1),
        ("II. The Roll", RL_T0, RL_T1),
        ("III. The Quiet", QU_T0, QU_T1),
        ("IV. Build One", B1_T0, B1_T1),
        ("V. Drop One", D1_T0, D1_T1),
        ("VI. Build Two", B2_T0, B2_T1),
        ("VII. Pull-Through", D2_T0, D2_T1),
        ("VIII. Exit Retrograde", EX_T0, END),
    ],
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 3, 1)],                    # F# minor: 3 sharps
    channels=[
        (0, "crystal arp", 98, 88, 64, 40),
        (1, "warm pad", 89, 84, 64, 60),
        (2, "synth bass", 38, 108, 64, 20),
        (3, "post L", 80, 70, 18, 45),
        (4, "post R", 80, 70, 110, 45),
        (5, "saw soar", 81, 92, 64, 55),
        (6, "harp", 46, 80, 64, 55),
        (7, "aerial strings", 49, 82, 64, 60),
        (8, "choir", 52, 78, 64, 65),
        (9, "kit", 0, 112, 64, 30),
        (10, "melodic toms", 117, 96, 54, 35),
        (11, "syn drum", 118, 96, 74, 35),
        (12, "orch hit", 55, 96, 64, 45),
        (13, "riser", 119, 90, 64, 70),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 112, 64, 22),
    ],
    program_changes=[(9, 0.0, 1)],            # the V3 kit
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

PROGRAM_WHITELIST: set[int] = {1, 29, 38, 46, 49, 52, 55, 80, 81, 89, 98,
                               117, 118, 119}
CENTERED_CHANNELS: set[int] = {0, 1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    0: (60, 84), 1: (50, 78), 2: (34, 48), 3: (74, 88), 4: (74, 88),
    5: (60, 88), 6: (48, 90), 7: (54, 84), 8: (58, 84), 9: (35, 60),
    10: (44, 64), 11: (46, 60), 12: (46, 68), 13: (60, 64),
    14: (62, 90), 15: (48, 88),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (245.0, 257.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Harmony grid — an 8-beat cycle i / VI / III / VII (F#m, D, A, E), global,
# aligned to beat 0 (every section boundary is a multiple of 8).
# ---------------------------------------------------------------------------

_DEGS = (1, 6, 3, 7)
_BASS_ROOT = {1: 42, 6: 38, 3: 45, 7: 40}     # F#2 D2 A2 E2
_CHUG = {1: 54, 6: 50, 3: 57, 7: 52}          # F#3 D3 A3 E3
_ARPP = {1: [66, 69, 73, 78], 6: [62, 66, 69, 74],
         3: [69, 73, 76, 81], 7: [64, 68, 71, 76]}
_STRV = {1: [58, 61, 66], 6: [57, 62, 66], 3: [57, 64, 69], 7: [59, 64, 68]}
_CHOIR2 = {1: [66, 73], 6: [62, 69], 3: [69, 76], 7: [64, 71]}
_CHOIR3 = {1: [66, 73, 78], 6: [62, 69, 74], 3: [69, 76, 81], 7: [64, 71, 76]}
_HARPX = {1: 54, 6: 50, 3: 57, 7: 52}


def _deg_at(b: float) -> int:
    return _DEGS[int(b // 8.0) % 4]


# ---------------------------------------------------------------------------
# THE HOOK — the lead ship's OPEN lane (32 beats, gapless, half-beat grid so
# its retrograde is tick-exact).  Notes 1-4 ARE material.ASCENT_CELL over F#4
# (0 / +7 / +12 / +19 with the 2.5-beat hang) — the album signature opens the
# track.  (onset, pitch, dur, vel), onsets relative to the statement start.
# ---------------------------------------------------------------------------

HOOK_LEN = 32.0
HOOK: list[tuple[float, int, float, int]] = [
    # bar 1 — the ascent (F#4 C#5 F#5 C#6)
    (0.0, 66, 0.5, 96), (0.5, 73, 0.5, 98), (1.0, 78, 0.5, 100),
    (1.5, 85, 2.5, 106),
    # bar 2 — the answer falls off the hang
    (4.0, 83, 0.5, 96), (4.5, 81, 0.5, 94), (5.0, 78, 0.5, 95),
    (5.5, 80, 0.5, 93), (6.0, 81, 1.0, 97), (7.0, 73, 1.0, 92),
    # bar 3 — circling
    (8.0, 74, 0.5, 92), (8.5, 76, 0.5, 94), (9.0, 78, 0.5, 96),
    (9.5, 74, 0.5, 92), (10.0, 76, 1.5, 98), (11.5, 73, 0.5, 90),
    # bar 4 — dip and mid-hold
    (12.0, 71, 0.5, 90), (12.5, 69, 0.5, 88), (13.0, 71, 0.5, 90),
    (13.5, 66, 2.5, 100),
    # bar 5 — second phrase, higher
    (16.0, 78, 0.5, 98), (16.5, 81, 0.5, 100), (17.0, 85, 0.5, 102),
    (17.5, 86, 2.0, 106), (19.5, 85, 0.5, 100),
    # bar 6
    (20.0, 83, 1.0, 100), (21.0, 81, 0.5, 96), (21.5, 80, 0.5, 94),
    (22.0, 81, 1.0, 98), (23.0, 78, 1.0, 94),
    # bar 7 — the hammer-on run (CC68-slurred)
    (24.0, 76, 0.5, 92), (24.5, 78, 0.5, 94), (25.0, 80, 0.5, 96),
    (25.5, 81, 1.0, 98), (26.5, 80, 0.5, 94), (27.0, 78, 0.5, 92),
    (27.5, 74, 0.5, 90),
    # bar 8 — settle onto the long tonic (retrograde: EXIT opens with it)
    (28.0, 73, 0.5, 92), (28.5, 66, 3.5, 104),
]

# The saw counter-line of the pull-through (rel to D2_T0; the counterpoint
# oracle's second voice: offbeat onsets, long holds, consonant downbeats).
SAW_CTR: list[tuple[float, int, float, int]] = [
    (0.0, 73, 2.0, 78), (2.5, 76, 4.0, 78), (6.5, 71, 1.0, 76),
    (7.5, 69, 3.0, 78), (10.5, 68, 1.0, 76), (11.5, 64, 3.0, 78),
    (14.5, 66, 1.0, 76), (15.5, 69, 3.5, 80), (19.0, 71, 0.5, 76),
    (19.5, 74, 3.0, 80), (22.5, 73, 1.0, 78), (23.5, 71, 3.0, 80),
    (26.5, 69, 1.0, 76), (27.5, 66, 4.5, 80),
]

# Lead development line, second phase of the pull-through (rel to 432).
LEAD_DEV: list[tuple[float, int, float, int]] = [
    (0.0, 78, 1.5, 98), (1.5, 81, 0.5, 96), (2.0, 83, 2.0, 100),
    (4.0, 81, 1.0, 96), (5.0, 80, 0.5, 92), (5.5, 81, 0.5, 94),
    (6.0, 83, 1.0, 98), (7.0, 85, 1.0, 100),
    (8.0, 86, 2.5, 102), (10.5, 85, 0.5, 96), (11.0, 83, 1.0, 96),
    (12.0, 81, 1.0, 94), (13.0, 80, 1.0, 92), (14.0, 81, 2.0, 96),
    (16.0, 78, 1.0, 94), (17.0, 80, 0.5, 92), (17.5, 81, 0.5, 94),
    (18.0, 83, 1.5, 98), (19.5, 85, 0.5, 96), (20.0, 86, 2.0, 102),
    (22.0, 88, 2.0, 104),                      # E6 — the album act's peak
    (24.0, 85, 1.0, 98), (25.0, 83, 0.5, 94), (25.5, 81, 0.5, 92),
    (26.0, 80, 1.0, 94), (27.0, 78, 1.0, 92), (28.0, 76, 1.0, 90),
    (29.0, 74, 1.0, 90), (30.0, 73, 2.0, 94),
]

# The wing ship's QUIET duet melody (absolute beats).
WING_QUIET: list[tuple[float, int, float, int]] = [
    (96.0, 54, 2.0, 58), (98.0, 61, 1.0, 60), (99.0, 64, 1.0, 62),
    (100.0, 66, 3.0, 66), (103.0, 64, 1.0, 62),
    (104.0, 62, 2.0, 64), (106.0, 64, 1.0, 63), (107.0, 66, 1.0, 65),
    (108.0, 69, 3.0, 68), (111.0, 66, 1.0, 64),
    (112.0, 69, 1.5, 66), (113.5, 68, 0.5, 62), (114.0, 69, 2.0, 67),
    (116.0, 73, 3.0, 70), (119.0, 71, 1.0, 66),
    (120.0, 68, 2.0, 66), (122.0, 64, 1.0, 62), (123.0, 68, 1.0, 64),
    (124.0, 71, 3.0, 70), (127.0, 68, 1.0, 64),
    (128.0, 66, 3.0, 68), (131.0, 64, 1.0, 63), (132.0, 61, 2.0, 62),
    (134.0, 62, 1.0, 62), (135.0, 64, 1.0, 64),
    (136.0, 62, 2.5, 66), (138.5, 66, 1.5, 66), (140.0, 69, 4.0, 70),
    (144.0, 73, 2.0, 70), (146.0, 71, 1.0, 66), (147.0, 69, 1.0, 66),
    (148.0, 66, 4.0, 68), (152.0, 64, 2.0, 62), (154.0, 61, 2.0, 60),
    (156.0, 54, 4.0, 58),
]

# Fill schedule — shapes from material.FILL_LIB, all jt=0.  Escalates
# strictly per 16-beat window through each build (3<8<11<17<28 / 3<8<11<17<37)
# with >= 20-note unbroken runs into both drops; drop windows capped <= 12.
FILL_SCHEDULE: list[tuple[float, str]] = [
    (14.0, "A"), (30.0, "B"), (46.0, "A"), (60.0, "G"),          # Drop Zero
    (70.0, "A"), (78.0, "A"),                                    # Roll w1, w2
    (172.0, "A"), (184.0, "B"), (196.0, "D"), (204.0, "A"),      # Build One
    (212.0, "C"), (220.0, "F"), (226.0, "H"),
    (236.0, "G"), (237.0, "E"),                                  # run -> D1
    (252.0, "A"), (268.0, "B"), (284.0, "A"), (300.0, "D"),      # Drop One
    (312.0, "A"),
    (332.0, "A"), (344.0, "B"), (356.0, "D"), (364.0, "A"),      # Build Two
    (372.0, "C"), (380.0, "F"), (386.0, "H"), (392.0, "G"),
    (396.0, "G"), (397.0, "E"),                                  # run -> D2
    (412.0, "A"), (428.0, "B"), (444.0, "A"), (460.0, "D"),      # Pull-Through
    (476.0, "G"), (492.0, "A"),
]

# ---------------------------------------------------------------------------
# Emitters (jt=0 on every oracle-pinned or boundary-adjacent lane)
# ---------------------------------------------------------------------------


def _fills(sc: en.Score, t0: float, t1: float) -> None:
    for start, shape in FILL_SCHEDULE:
        if t0 <= start < t1:
            material.play_fill(sc, shape, start)


def _hook(sc: en.Score, ch: int, t0: float, vbump: int = 0) -> None:
    """One statement of the hook, with CC1 blooms over every >=2-beat hold."""
    for on, p, dur, vel in HOOK:
        sc.note(ch, p, t0 + on, dur, vel + vbump, jt=0, jv=0)
        if dur >= 2.0:
            peak = min(90, 34 + int(round(dur * 9)))
            en.cc_curve(sc, ch, 1, [(t0 + on, 0), (t0 + on + 0.35 * dur, peak),
                                    (t0 + on + dur - 0.1, 0)], step=0.25)
    sc.cc(ch, 68, 90, t0 + 23.95)              # slur the bar-7 run
    sc.cc(ch, 68, 0, t0 + 28.05)


def _retro_hook(sc: en.Score, ch: int, t0: float, vbump: int = 0) -> None:
    """The hook time-reversed about its own 32-beat grid (the formation)."""
    for on, p, dur, vel in HOOK:
        sc.note(ch, p, t0 + (HOOK_LEN - on - dur), dur, vel + vbump,
                jt=0, jv=0)


def _table(sc: en.Score, ch: int, t0: float,
           rows: list[tuple[float, int, float, int]], vbump: int = 0,
           bloom: bool = False) -> None:
    for on, p, dur, vel in rows:
        sc.note(ch, p, t0 + on, dur, vel + vbump, jt=0, jv=0)
        if bloom and dur >= 2.0:
            peak = min(90, 34 + int(round(dur * 9)))
            en.cc_curve(sc, ch, 1, [(t0 + on, 0), (t0 + on + 0.35 * dur, peak),
                                    (t0 + on + dur - 0.1, 0)], step=0.25)


def _four_floor(sc: en.Score, t0: float, t1: float, kick: int, clap: int,
                hat: int, ohat: int, hat16: int = 0, snare: int = 0) -> None:
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(9, 46, t + 0.5, 0.4, ohat, jt=0, jv=4)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
        sc.note(9, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(9, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)
        if snare:
            sc.note(9, 38, bar + 1.0, 0.25, snare, jt=0, jv=4)
            sc.note(9, 38, bar + 3.0, 0.25, snare, jt=0, jv=4)


def _snare_roll(sc: en.Score, t0: float, t1: float, v0: int, v1: int) -> None:
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _bass8(sc: en.Score, t0: float, t1: float, v0: int,
           v1: int | None = None) -> None:
    n = int(round((t1 - t0) * 2))
    for i in range(n):
        b = t0 + 0.5 * i
        v = v0 if v1 is None else int(round(en.lerp(v0, v1, i / max(1, n - 1))))
        sc.note(2, _BASS_ROOT[_deg_at(b)], b, 0.4, v, jt=0, jv=3)


def _bass_q(sc: en.Score, t0: float, t1: float, v0: int,
            v1: int | None = None) -> None:
    n = int(round(t1 - t0))
    for i in range(n):
        b = t0 + float(i)
        v = v0 if v1 is None else int(round(en.lerp(v0, v1, i / max(1, n - 1))))
        sc.note(2, _BASS_ROOT[_deg_at(b)], b, 0.9, v, jt=0, jv=2)


def _arp16(sc: en.Score, t0: float, t1: float, v0: int, v1: int | None = None,
           step: float = 0.25) -> None:
    n = int(round((t1 - t0) / step))
    for i in range(n):
        b = t0 + step * i
        seq = _ARPP[_deg_at(b)]
        v = v0 if v1 is None else en.lerp(v0, v1, i / max(1, n - 1))
        if abs(b - round(b)) < 1e-9:
            v += 8                              # beat accent
        sc.note(0, seq[i % 4], b, step * 0.95, int(round(v)), jt=0, jv=3)


def _chugs(sc: en.Score, t0: float, t1: float, v0: int,
           v1: int | None = None) -> None:
    n = int(round(t1 - t0))
    for i in range(n):
        b = t0 + float(i)
        v = v0 if v1 is None else int(round(en.lerp(v0, v1, i / max(1, n - 1))))
        sc.note(15, _CHUG[_deg_at(b)], b + 0.5, 0.3, v, jt=0, jv=3)


def _pads(sc: en.Score, t0: float, count: int, vel: int,
          vel_end: int | None = None, span: float = 8.0) -> None:
    prev = None
    for i in range(count):
        b = t0 + span * i
        prev = en.voice_lead(en.triad(BASE, MODE, _deg_at(b)), prev, 4, 52, 76)
        v = vel if vel_end is None else int(round(
            en.lerp(vel, vel_end, i / max(1, count - 1))))
        for p in prev:
            sc.note(1, p, b, span - 0.05, v, jt=0, jv=2)


def _strings(sc: en.Score, t0: float, count: int, vel: int,
             octave_top: bool = False, span: float = 8.0) -> None:
    for i in range(count):
        b = t0 + span * i
        voice = list(_STRV[_deg_at(b)])
        if octave_top and voice[0] + 12 not in voice:
            voice.append(voice[0] + 12)
        for p in voice:
            sc.note(7, p, b, span - 0.1, vel, jt=0, jv=2)


def _choir(sc: en.Score, t0: float, count: int, vel: int,
           three: bool = False, span: float = 8.0) -> None:
    table = _CHOIR3 if three else _CHOIR2
    for i in range(count):
        b = t0 + span * i
        for p in table[_deg_at(b)]:
            sc.note(8, p, b, span - 0.1, vel, jt=0, jv=2)


def _harp_run(sc: en.Score, t: float, vel: int) -> None:
    x = _HARPX[_deg_at(t)]
    en.arp(sc, 6, [x, x + 7, x + 12, x + 19], t, 8, 0.25, vel,
           pattern="updown", gate=0.9)


def _post(sc: en.Score, ch: int, t: float, vel: int,
          answer: bool = False) -> None:
    ps = [85, 81, 78] if answer else [78, 81, 85]
    for i, p in enumerate(ps):
        sc.note(ch, p, t + 0.25 * i, 0.2, vel, jt=0, jv=2)


def _hits(sc: en.Score, t0: float, t1: float, step: float, vel: int) -> None:
    b = t0
    while b < t1 - 1e-9:
        sc.note(12, _CHUG[_deg_at(b)], b, 0.9, vel, jt=0, jv=3)
        b += step


def _riser(sc: en.Score, beat: float, vel: int, dur: float = 7.8) -> None:
    sc.note(13, 62, beat, dur, vel, jt=0, jv=0)


# ---------------------------------------------------------------------------
# Builders — one per movement, note-ons strictly inside their own window.
# ---------------------------------------------------------------------------


def _b_drop_zero(sc: en.Score) -> None:
    # Whole-timeline CC choreography, authored once here (CC is bounds-exempt).
    en.cc_curve(sc, 1, 74, [(0.0, 72), (64.0, 58), (96.0, 40), (160.0, 42),
                            (208.0, 58), (236.0, 88), (240.0, 68),
                            (304.0, 50), (320.0, 34), (392.0, 112),
                            (400.0, 74), (464.0, 84), (495.0, 60),
                            (560.0, 40)], step=1.0)
    en.vowel_curve(sc, 8, [(0.0, 100), (64.0, 60), (95.0, 25), (224.0, 50),
                           (240.0, 85), (300.0, 45), (368.0, 60),
                           (399.0, 108), (496.0, 50), (559.0, 30)], step=2.0)
    en.expr_curve(sc, 7, [(0.0, 86), (64.0, 58), (96.0, 46), (176.0, 50),
                          (236.0, 86), (240.0, 76), (304.0, 52), (336.0, 52),
                          (396.0, 88), (464.0, 96), (496.0, 56), (559.0, 40)])
    en.expr_curve(sc, 8, [(0.0, 82), (64.0, 52), (96.0, 40), (224.0, 58),
                          (240.0, 68), (320.0, 44), (368.0, 58), (400.0, 88),
                          (496.0, 52), (559.0, 36)])
    en.expr_curve(sc, 5, [(0.0, 66), (64.0, 48), (96.0, 40), (208.0, 54),
                          (238.0, 72), (240.0, 64), (304.0, 48), (352.0, 50),
                          (396.0, 78), (464.0, 86), (495.0, 44), (559.0, 40)])
    # bar 1 IS the drop
    sc.note(9, 49, 0.0, 1.5, 110, jt=0, jv=0)
    sc.note(9, 49, 32.0, 1.5, 104, jt=0, jv=0)
    _four_floor(sc, D0_T0, D0_T1, 104, 96, 72, 66, hat16=52, snare=84)
    _bass8(sc, D0_T0, D0_T1, 92)
    _arp16(sc, D0_T0, D0_T1, 78)
    _hook(sc, 14, 0.0)
    _hook(sc, 14, 32.0)
    _chugs(sc, D0_T0, D0_T1, 86)
    for i, p in enumerate([73, 74, 73, 76, 73, 74, 73, 76]):
        sc.note(5, p, 8.0 * i, 7.9, 58 + 2 * (i % 2), jt=0, jv=0)
    _pads(sc, 0.0, 8, 56)
    _strings(sc, 0.0, 8, 62)
    _choir(sc, 0.0, 8, 58)
    for t in (12.0, 28.0, 44.0, 60.0):
        _harp_run(sc, t, 66)
    for k in range(4):
        _post(sc, 3, 6.0 + 16.0 * k, 70)
        _post(sc, 4, 14.0 + 16.0 * k, 70, answer=True)
    _hits(sc, 0.0, 64.0, 4.0, 94)
    for bar in range(0, 64, 8):                 # off-beat punch
        sc.note(12, _CHUG[_deg_at(bar)], bar + 1.5, 0.4, 86, jt=0, jv=3)
    _fills(sc, D0_T0, D0_T1)


def _b_roll(sc: en.Score) -> None:
    # w1 [64,72): 15 channels  ->  w2: 10  ->  w3: 6  ->  w4: 3
    _arp16(sc, 64.0, 72.0, 66)
    _arp16(sc, 72.0, 80.0, 56, step=0.5)
    _arp16(sc, 80.0, 88.0, 46, step=1.0)
    _pads(sc, 64.0, 4, 52, vel_end=40)
    _bass8(sc, 64.0, 72.0, 84)
    _bass_q(sc, 72.0, 88.0, 72, 58)
    _bass_q(sc, 88.0, 96.0, 56)
    _post(sc, 3, 64.5, 62)
    _post(sc, 4, 66.5, 62, answer=True)
    sc.note(5, 73, 64.0, 6.0, 54, jt=0, jv=0)
    _harp_run(sc, 67.0, 58)
    en.arp(sc, 6, [50, 57, 62, 69], 74.0, 4, 0.5, 52, gate=0.9)
    for p in _STRV[1]:
        sc.note(7, p, 64.0, 7.9, 58, jt=0, jv=2)
    for p in _STRV[6]:
        sc.note(7, p, 72.0, 7.9, 46, jt=0, jv=2)
    for p in _CHOIR2[1]:
        sc.note(8, p, 64.0, 7.9, 54, jt=0, jv=2)
    for p in _CHOIR2[6]:
        sc.note(8, p, 72.0, 7.9, 46, jt=0, jv=2)
    for p in _CHOIR2[3]:
        sc.note(8, p, 80.0, 7.9, 40, jt=0, jv=2)
    for t in (64.0, 65.0, 66.0, 67.0):
        sc.note(9, 36, t, 0.25, 88, jt=0, jv=3)
    for i in range(16):
        sc.note(9, 42, 64.0 + 0.5 * i, 0.2, 50, jt=0, jv=3)
    sc.note(9, 39, 65.0, 0.3, 80, jt=0, jv=3)
    sc.note(9, 39, 67.0, 0.3, 78, jt=0, jv=3)
    for t in (72.0, 74.0, 76.0, 78.0):
        sc.note(9, 36, t, 0.25, 68, jt=0, jv=3)
        sc.note(9, 42, t, 0.2, 40, jt=0, jv=3)
    sc.note(9, 36, 80.0, 0.25, 54, jt=0, jv=2)
    sc.note(9, 36, 84.0, 0.25, 50, jt=0, jv=2)
    sc.note(12, _CHUG[1], 64.0, 0.9, 90, jt=0, jv=2)
    sc.note(14, 73, 64.5, 1.0, 72, jt=0, jv=0)
    sc.note(14, 71, 66.0, 1.5, 68, jt=0, jv=0)
    sc.note(14, 66, 69.0, 2.5, 64, jt=0, jv=0)
    _chugs(sc, 64.0, 80.0, 78, 64)
    sc.note(15, 54, 80.0, 7.5, 58, jt=0, jv=0)
    sc.note(15, 54, 88.0, 4.0, 56, jt=0, jv=0)
    sc.note(15, 61, 92.0, 3.0, 58, jt=0, jv=0)
    sc.note(15, 64, 95.0, 1.0, 60, jt=0, jv=0)
    _fills(sc, RL_T0, RL_T1)


def _b_quiet(sc: en.Score) -> None:
    _bass_q(sc, QU_T0, QU_T1, 50, 62)
    _table(sc, 15, 0.0, WING_QUIET)
    en.cc_curve(sc, 15, 1, [(96.0, 8), (128.0, 30), (159.0, 10)], step=1.0)


def _b_build_one(sc: en.Score) -> None:
    # w1 [160,176)
    for i in range(16):
        sc.note(9, 36, 160.0 + i, 0.25, 58, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 160.0 + 0.5 * i, 0.2, 36, jt=0, jv=3)
    _arp16(sc, 160.0, 176.0, 56, 62, step=0.5)
    _bass8(sc, 160.0, 176.0, 62, 68)
    # w2 [176,192)
    for i in range(16):
        sc.note(9, 36, 176.0 + i, 0.25, 64, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 176.0 + 0.5 * i, 0.2, 42, jt=0, jv=3)
    for t in (177.0, 179.0, 181.0, 183.0, 185.0, 187.0, 189.0, 191.0):
        sc.note(9, 38, t, 0.25, 55, jt=0, jv=3)
    _arp16(sc, 176.0, 192.0, 62, 70)
    _bass8(sc, 176.0, 192.0, 70, 76)
    _pads(sc, 176.0, 2, 44, vel_end=48)
    _strings(sc, 176.0, 2, 44)
    # w3 [192,208)
    for i in range(16):
        sc.note(9, 36, 192.0 + i, 0.25, 72, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 192.0 + 0.5 * i, 0.2, 46, jt=0, jv=3)
    for t in (193.0, 195.0, 197.0, 199.0, 201.0, 203.0, 205.0, 207.0):
        sc.note(9, 38, t, 0.25, 62, jt=0, jv=3)
    _arp16(sc, 192.0, 208.0, 70, 76)
    _bass8(sc, 192.0, 208.0, 76, 80)
    _pads(sc, 192.0, 2, 48, vel_end=52)
    _strings(sc, 192.0, 2, 50)
    _post(sc, 3, 194.0, 66)
    _post(sc, 4, 198.0, 66, answer=True)
    _post(sc, 3, 202.0, 68)
    _post(sc, 4, 206.0, 68, answer=True)
    _harp_run(sc, 196.0, 60)
    _harp_run(sc, 204.0, 62)
    _chugs(sc, 192.0, 208.0, 60, 68)
    # w4 [208,224)
    for i in range(16):
        sc.note(9, 36, 208.0 + i, 0.25, 78, jt=0, jv=3)
    for i in range(64):
        sc.note(9, 42, 208.0 + 0.25 * i, 0.15, 44, jt=0, jv=3)
    for t in (209.0, 211.0, 213.0, 215.0, 217.0, 219.0, 221.0, 223.0):
        sc.note(9, 38, t, 0.25, 68, jt=0, jv=3)
    _arp16(sc, 208.0, 224.0, 76, 80)
    _bass8(sc, 208.0, 224.0, 80, 84)
    _pads(sc, 208.0, 2, 52, vel_end=56)
    _strings(sc, 208.0, 2, 56)
    _chugs(sc, 208.0, 224.0, 68, 74)
    sc.note(5, 73, 208.0, 7.9, 46, jt=0, jv=0)
    sc.note(5, 76, 216.0, 7.9, 52, jt=0, jv=0)
    _hits(sc, 208.0, 224.0, 8.0, 80)
    sc.note(14, 66, 216.0, 0.5, 80, jt=0, jv=0)
    sc.note(14, 73, 216.5, 1.0, 82, jt=0, jv=0)
    # w5 [224,240)
    _four_floor(sc, 224.0, 240.0, 84, 78, 52, 48, hat16=50)
    _snare_roll(sc, 236.0, 240.0, 60, 104)
    _arp16(sc, 224.0, 240.0, 80, 86)
    _bass8(sc, 224.0, 240.0, 84, 88)
    _pads(sc, 224.0, 2, 56, vel_end=60)
    _strings(sc, 224.0, 2, 62)
    _choir(sc, 224.0, 2, 60)
    _chugs(sc, 224.0, 240.0, 74, 80)
    sc.note(5, 78, 224.0, 7.9, 54, jt=0, jv=0)
    sc.note(5, 80, 232.0, 7.5, 58, jt=0, jv=0)
    _hits(sc, 224.0, 240.0, 8.0, 84)
    sc.note(14, 66, 224.0, 0.5, 86, jt=0, jv=0)
    sc.note(14, 73, 224.5, 0.5, 86, jt=0, jv=0)
    sc.note(14, 78, 225.0, 1.5, 88, jt=0, jv=0)
    material.play_ascent(sc, 14, 232.0, 66, vel=92, vel_end=100, jv=0)
    _riser(sc, 232.0, 96)
    _post(sc, 3, 226.0, 70)
    _post(sc, 4, 230.0, 70, answer=True)
    _fills(sc, B1_T0, B1_T1)


def _b_drop_one(sc: en.Score) -> None:
    sc.note(9, 49, 240.0, 1.5, 108, jt=0, jv=0)
    _four_floor(sc, 240.0, 304.0, 100, 92, 68, 62)
    _bass8(sc, 240.0, 304.0, 86)
    _arp16(sc, 240.0, 304.0, 72)
    _hook(sc, 14, 240.0, vbump=-4)
    _hook(sc, 14, 272.0, vbump=-2)
    _chugs(sc, 240.0, 304.0, 84)
    _pads(sc, 240.0, 8, 54)
    _strings(sc, 240.0, 8, 56)
    for k in range(4):
        _post(sc, 3, 246.0 + 16.0 * k, 68)
        _post(sc, 4, 254.0 + 16.0 * k, 68, answer=True)
    _hits(sc, 240.0, 304.0, 8.0, 88)
    # [304,312) the soar; [312,320) wind-down toward Build Two
    sc.note(14, 78, 304.0, 8.0, 96, jt=0, jv=0)
    en.cc_curve(sc, 14, 1, [(304.0, 0), (306.8, 76), (311.9, 0)], step=0.25)
    en.vibrato(sc, 14, 304.5, 7.0, depth=0.3, cycles_per_beat=1.1)
    _pads(sc, 304.0, 2, 48)
    for t in range(304, 320):
        sc.note(9, 36, float(t), 0.25, 78 if t < 312 else 72, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 304.0 + 0.5 * i, 0.2, 48 if i < 16 else 44, jt=0, jv=3)
    _bass8(sc, 304.0, 320.0, 78, 72)
    _arp16(sc, 304.0, 320.0, 64, 58, step=0.5)
    _chugs(sc, 312.0, 320.0, 70)
    _fills(sc, D1_T0, D1_T1)


def _b_build_two(sc: en.Score) -> None:
    # w1 [320,336)
    for i in range(16):
        sc.note(9, 36, 320.0 + i, 0.25, 62, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 320.0 + 0.5 * i, 0.2, 38, jt=0, jv=3)
    _arp16(sc, 320.0, 336.0, 58, 64, step=0.5)
    _bass8(sc, 320.0, 336.0, 64, 70)
    # w2 [336,352)
    for i in range(16):
        sc.note(9, 36, 336.0 + i, 0.25, 68, jt=0, jv=3)
    for i in range(32):
        sc.note(9, 42, 336.0 + 0.5 * i, 0.2, 44, jt=0, jv=3)
    for t in (337.0, 339.0, 341.0, 343.0, 345.0, 347.0, 349.0, 351.0):
        sc.note(9, 38, t, 0.25, 58, jt=0, jv=3)
    _arp16(sc, 336.0, 352.0, 64, 72)
    _bass8(sc, 336.0, 352.0, 70, 76)
    _pads(sc, 336.0, 2, 46, vel_end=50)
    _strings(sc, 336.0, 2, 46)
    _chugs(sc, 336.0, 352.0, 58, 64)
    # w3 [352,368)
    for i in range(16):
        sc.note(9, 36, 352.0 + i, 0.25, 74, jt=0, jv=3)
    for i in range(64):
        sc.note(9, 42, 352.0 + 0.25 * i, 0.15, 42, jt=0, jv=3)
    for t in (353.0, 355.0, 357.0, 359.0, 361.0, 363.0, 365.0, 367.0):
        sc.note(9, 38, t, 0.25, 64, jt=0, jv=3)
    _arp16(sc, 352.0, 368.0, 72, 78)
    _bass8(sc, 352.0, 368.0, 76, 82)
    _pads(sc, 352.0, 2, 50, vel_end=54)
    _strings(sc, 352.0, 2, 52)
    _post(sc, 3, 354.0, 68)
    _post(sc, 4, 358.0, 68, answer=True)
    _post(sc, 3, 362.0, 70)
    _post(sc, 4, 366.0, 70, answer=True)
    _harp_run(sc, 356.0, 62)
    _harp_run(sc, 364.0, 64)
    _chugs(sc, 352.0, 368.0, 64, 72)
    sc.note(5, 73, 352.0, 7.9, 44, jt=0, jv=0)
    sc.note(5, 76, 360.0, 7.9, 48, jt=0, jv=0)
    sc.note(14, 66, 352.0, 0.5, 78, jt=0, jv=0)
    sc.note(14, 73, 352.5, 1.0, 80, jt=0, jv=0)
    # w4 [368,384)
    for i in range(16):
        sc.note(9, 36, 368.0 + i, 0.25, 80, jt=0, jv=3)
    for i in range(64):
        sc.note(9, 42, 368.0 + 0.25 * i, 0.15, 48, jt=0, jv=3)
    for t in (369.0, 371.0, 373.0, 375.0, 377.0, 379.0, 381.0, 383.0):
        sc.note(9, 38, t, 0.25, 70, jt=0, jv=3)
    _arp16(sc, 368.0, 384.0, 78, 82)
    _bass8(sc, 368.0, 384.0, 82, 86)
    _pads(sc, 368.0, 2, 54, vel_end=58)
    _strings(sc, 368.0, 2, 58)
    _choir(sc, 368.0, 2, 58)
    _chugs(sc, 368.0, 384.0, 72, 78)
    sc.note(5, 78, 368.0, 7.9, 52, jt=0, jv=0)
    sc.note(5, 80, 376.0, 7.9, 56, jt=0, jv=0)
    _hits(sc, 368.0, 384.0, 8.0, 84)
    sc.note(14, 66, 368.0, 0.5, 84, jt=0, jv=0)
    sc.note(14, 73, 368.5, 0.5, 84, jt=0, jv=0)
    sc.note(14, 78, 369.0, 1.5, 86, jt=0, jv=0)
    # w5 [384,400)
    _four_floor(sc, 384.0, 400.0, 88, 82, 54, 50, hat16=52)
    _snare_roll(sc, 396.0, 400.0, 64, 108)
    _arp16(sc, 384.0, 400.0, 82, 88)
    _bass8(sc, 384.0, 400.0, 86, 90)
    _pads(sc, 384.0, 2, 58, vel_end=62)
    _strings(sc, 384.0, 2, 64)
    _choir(sc, 384.0, 2, 64)
    _chugs(sc, 384.0, 400.0, 78, 84)
    sc.note(5, 81, 384.0, 7.9, 60, jt=0, jv=0)
    _hits(sc, 384.0, 400.0, 8.0, 88)
    material.play_ascent(sc, 14, 384.0, 66, vel=94, vel_end=102, jv=0)
    _riser(sc, 392.0, 98)
    _post(sc, 3, 386.0, 72)
    _post(sc, 4, 390.0, 72, answer=True)
    # the portamento swoop: C#5 glides a full octave to C#6 into the drop
    en.portamento_on(sc, 5, 395.9, time_cc=58)
    sc.note(5, 73, 396.0, 1.9, 64, jt=0, jv=0)
    sc.note(5, 85, 398.0, 6.0, 72, jt=0, jv=0)
    en.portamento_off(sc, 5, 404.5)
    _fills(sc, B2_T0, B2_T1)


def _b_pull_through(sc: en.Score) -> None:
    sc.note(9, 49, 400.0, 1.5, 112, jt=0, jv=0)
    sc.note(9, 49, 432.0, 1.5, 100, jt=0, jv=0)
    sc.note(9, 57, 464.0, 1.5, 108, jt=0, jv=0)
    _four_floor(sc, 400.0, 496.0, 106, 98, 70, 64, hat16=54, snare=88)
    _bass8(sc, 400.0, 496.0, 94)
    _arp16(sc, 400.0, 496.0, 84)
    _hook(sc, 14, 400.0)                       # statement 3 over the counter
    _table(sc, 5, 400.0, SAW_CTR)              # the second voice
    _table(sc, 14, 432.0, LEAD_DEV, bloom=True)
    _hook(sc, 14, 464.0, vbump=2)              # the victory statement
    for on, p, dur, vel in ((32.0, 76, 7.9, 58), (40.0, 74, 7.9, 58),
                            (48.0, 76, 7.9, 60), (56.0, 81, 7.9, 64),
                            (64.0, 81, 7.9, 64), (72.0, 83, 7.9, 66),
                            (80.0, 85, 15.9, 70)):
        sc.note(5, p, 400.0 + on, dur, vel, jt=0, jv=0)
    _chugs(sc, 400.0, 496.0, 90)
    _pads(sc, 400.0, 12, 58)
    _strings(sc, 400.0, 12, 66, octave_top=True)
    _choir(sc, 400.0, 12, 72, three=True)
    for t in range(404, 496, 8):
        _harp_run(sc, float(t), 70)
    for k in range(6):
        _post(sc, 3, 406.0 + 16.0 * k, 74)
        _post(sc, 4, 414.0 + 16.0 * k, 74, answer=True)
    _hits(sc, 400.0, 496.0, 4.0, 98)
    for bar in range(400, 496, 8):
        sc.note(12, _CHUG[_deg_at(bar)], bar + 1.5, 0.4, 88, jt=0, jv=3)
    _riser(sc, 456.0, 88)
    _fills(sc, D2_T0, D2_T1)


def _b_exit(sc: en.Score) -> None:
    _retro_hook(sc, 15, EX_T0, vbump=-6)       # the formation: OPEN reversed
    _table(sc, 15, 0.0, [(528.0, 73, 3.5, 68), (532.0, 69, 3.5, 66),
                         (536.0, 71, 3.5, 66), (540.0, 66, 20.0, 72)])
    en.cc_curve(sc, 15, 1, [(540.0, 0), (547.0, 55), (559.0, 0)], step=0.5)
    sc.note(14, 78, 544.0, 16.0, 64, jt=0, jv=0)
    en.cc_curve(sc, 14, 1, [(544.0, 0), (550.0, 60), (559.5, 0)], step=0.5)
    _pads(sc, 496.0, 8, 46, vel_end=36)
    for i in range(30):
        sc.note(2, _BASS_ROOT[_deg_at(496.0 + 2.0 * i)], 496.0 + 2.0 * i,
                1.9, int(round(en.lerp(60, 48, i / 29))), jt=0, jv=2)
    sc.note(2, 42, 556.0, 4.0, 44, jt=0, jv=0)
    sc.note(7, 78, 496.0, 31.9, 44, jt=0, jv=0)
    sc.note(7, 78, 528.0, 31.9, 38, jt=0, jv=0)
    for t in (500.0, 508.0, 516.0, 524.0):
        en.arp(sc, 6, [54, 61, 66, 73], t, 4, 0.5, 54, gate=0.9)
    for p in _CHOIR2[1]:
        sc.note(8, p, 544.0, 15.9, 44, jt=0, jv=2)
    sc.note(12, _CHUG[1], 556.0, 0.9, 62, jt=0, jv=0)


BUILDERS = [_b_drop_zero, _b_roll, _b_quiet, _b_build_one, _b_drop_one,
            _b_build_two, _b_pull_through, _b_exit]

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 set)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))


def _note_ons(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _prio, data in sorted(sc.events.get(ch, []),
                                    key=lambda e: (e[0], e[1])):
        s = data[0] & 0xF0
        if s == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and data[2] == 0):
            q = pending.get(data[1])
            if q:
                out.append((q.pop(0), tick, data[1]))
    return sorted(out)


def _cc_lane(sc, ch, num):
    return sorted((t, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, _p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _pitch_at(spans, tick):
    """Pitch of the most recent note-on at or before `tick` still ringing."""
    best = None
    for on, off, p in spans:
        if on <= tick < off and (best is None or on >= best[0]):
            best = (on, p)
    return None if best is None else best[1]


def _active_channels(sc, lo, hi):
    t0, t1 = _tick(lo), _tick(hi)
    return {ch for ch in sc.events
            if any(t0 <= t < t1 for t, _p, _v in _note_ons(sc, ch))}


# ---------------------------------------------------------------------------
# Track oracles — every headline claim of HLD section 4 T8, falsifiable.
# ---------------------------------------------------------------------------


def _o_cold_open(sums):
    """First 8 bars sit within the loudest of the piece (the cold open)."""
    fails = []
    open_mass = _mean_barsum(sums, 0.0, 32.0)
    peak = 0.0
    peak_at = 0.0
    w = 0.0
    while w + 32.0 <= END:
        m = _mean_barsum(sums, w, w + 32.0)
        if m > peak:
            peak, peak_at = m, w
        w += 8.0
    if open_mass < 0.85 * peak:
        fails.append(f"open [0,32) mass {open_mass:.0f} < 85% of peak "
                     f"{peak:.0f} (at beat {peak_at:g})")
    d1 = _mean_barsum(sums, D1_T0, 304.0)
    if open_mass <= 1.05 * d1:
        fails.append(f"open mass {open_mass:.0f} not clearly above DROP1 "
                     f"core {d1:.0f}")
    return fails


def _o_roll_strips(sc):
    """Per-2-bar active-channel count strictly falls through the roll."""
    fails = []
    wins = [(64.0, 72.0), (72.0, 80.0), (80.0, 88.0), (88.0, 96.0)]
    counts = [len(_active_channels(sc, lo, hi)) for lo, hi in wins]
    if any(b >= a for a, b in zip(counts, counts[1:])):
        fails.append(f"roll layer counts not strictly falling: {counts}")
    if counts[0] < 12:
        fails.append(f"roll starts with only {counts[0]} layers (< 12)")
    if counts[-1] > 4:
        fails.append(f"roll ends with {counts[-1]} layers (> 4)")
    return fails


def _o_quiet_duet(sc, sums):
    """[96,160): bass + wing ship alone, a real melody, a real hush."""
    fails = []
    active = _active_channels(sc, QU_T0, QU_T1)
    if active != {2, 15}:
        fails.append(f"quiet channels {sorted(active)} != [2, 15]")
    t0, t1 = _tick(QU_T0), _tick(QU_T1)
    wing = [(t, p) for t, p, _v in _note_ons(sc, 15) if t0 <= t < t1]
    if len(wing) < 12:
        fails.append(f"wing duet has {len(wing)} notes (< 12)")
    if wing and max(p for _t, p in wing) - min(p for _t, p in wing) < 7:
        fails.append("wing duet melody spans under a fifth")
    hush = _mean_barsum(sums, QU_T0, QU_T1)
    d1 = _mean_barsum(sums, D1_T0, 304.0)
    if hush >= 0.5 * d1:
        fails.append(f"quiet mass {hush:.0f} >= 50% of DROP1 {d1:.0f}")
    return fails


def _o_build_drop_chain(sums):
    """Builds rise strictly per 16-beat window; D2 > D1 and D2 >= D0."""
    fails = []
    for name, b0, b1 in (("build1", B1_T0, B1_T1), ("build2", B2_T0, B2_T1)):
        masses = [_mean_barsum(sums, w, w + 16.0)
                  for w in (b0 + 16.0 * i for i in range(int((b1 - b0) / 16)))]
        if any(b <= a for a, b in zip(masses, masses[1:])):
            fails.append(f"{name} windows not strictly rising: "
                         f"{[round(m) for m in masses]}")
    d0 = _mean_barsum(sums, D0_T0, D0_T1)
    d1 = _mean_barsum(sums, D1_T0, 304.0)
    d2 = _mean_barsum(sums, D2_T0, 464.0)
    if d2 <= 1.02 * d1:
        fails.append(f"DROP2 {d2:.0f} not clearly above DROP1 {d1:.0f}")
    if d2 < d0:
        fails.append(f"DROP2 {d2:.0f} below DROP0 {d0:.0f}")
    return fails


def _o_fill_escalation(sc):
    fails = []
    ons = sorted(_note_ons(sc, 10) + _note_ons(sc, 11))
    ticks = [t for t, _p, _v in ons]

    def count(lo, hi):
        t0, t1 = _tick(lo), _tick(hi)
        return sum(1 for t in ticks if t0 <= t < t1)

    for name, b0, b1 in (("build1", B1_T0, B1_T1), ("build2", B2_T0, B2_T1)):
        counts = [count(b0 + 16.0 * i, b0 + 16.0 * (i + 1))
                  for i in range(int((b1 - b0) / 16))]
        if any(b <= a for a, b in zip(counts, counts[1:])):
            fails.append(f"{name} fill counts not strictly rising: {counts}")
        shapes = {s for t, s in FILL_SCHEDULE if b0 <= t < b1}
        if len(shapes) < 5:
            fails.append(f"{name} uses {len(shapes)} fill shapes (< 5)")
    sched = sum(material.fill_note_count(s) for _t, s in FILL_SCHEDULE)
    if sched != len(ons):
        fails.append(f"score has {len(ons)} fill notes, schedule says {sched}")
    for drop in (D1_T0, D2_T0):
        t0, t1 = _tick(drop - 4.2), _tick(drop)
        run = [t for t in ticks if t0 <= t < t1]
        gaps = [(b - a) / _PPQ for a, b in zip(run, run[1:])]
        if len(run) < 20 or (gaps and max(gaps) > 0.5 + 1e-6):
            fails.append(f"no >=20-note unbroken run into drop at {drop:g} "
                         f"(got {len(run)} notes, max gap "
                         f"{max(gaps) if gaps else 0:.2f})")
    for name, b0, b1 in (("drop0", D0_T0, D0_T1), ("drop1", D1_T0, D1_T1),
                         ("drop2", D2_T0, D2_T1)):
        for i in range(int((b1 - b0) / 16)):
            c = count(b0 + 16.0 * i, b0 + 16.0 * (i + 1))
            if c > 12:
                fails.append(f"{name} window {i} has {c} fill notes (> 12: "
                             f"drops must thin)")
    return fails


def _o_retrograde(sc):
    """wing(EXIT) == retrograde of lead(OPEN), tick-exact, recomputed."""
    fails = []
    hook_ticks = _tick(HOOK_LEN)
    ex_t0 = _tick(EX_T0)
    lead = [(on, off, p) for on, off, p in _note_spans(sc, 14)
            if on < _tick(D0_T0 + HOOK_LEN)]
    expect = {(ex_t0 + hook_ticks - off, ex_t0 + hook_ticks - on, p)
              for on, off, p in lead}
    wing = {(on, off, p) for on, off, p in _note_spans(sc, 15)
            if ex_t0 <= on < ex_t0 + hook_ticks}
    if len(lead) != len(HOOK):
        fails.append(f"lead OPEN lane has {len(lead)} notes, hook table "
                     f"{len(HOOK)}")
    missing = sorted(expect - wing)[:3]
    extra = sorted(wing - expect)[:3]
    if missing:
        fails.append(f"wing EXIT lane missing retrograde notes {missing}")
    if extra:
        fails.append(f"wing EXIT lane has non-retrograde notes {extra}")
    return fails


def _o_ascent(sc):
    """The album cell opens the track, both builds and both hook returns."""
    fails = []
    ons = {(t, p) for t, p, _v in _note_ons(sc, 14)}
    want = [(0.0, 66), (0.5, 73), (1.0, 78), (1.5, 85)]
    for t0 in (0.0, 232.0, 384.0, 400.0, 464.0):
        if any((_tick(t0 + dt), p) not in ons for dt, p in want):
            fails.append(f"no ASCENT_CELL statement on the lead at {t0:g}")
    semis = [p - 66 for _dt, p in want]
    if semis != [s for _o, _d, s in material.ASCENT_CELL]:
        fails.append("hook head drifted from material.ASCENT_CELL")
    return fails


def _o_counterpoint(sc):
    """DROP2 [400,432): lead vs saw — a genuine second voice."""
    fails = []
    t0, t1 = _tick(400.0), _tick(432.0)
    lead_spans = [s for s in _note_spans(sc, 14) if t0 <= s[0] < t1]
    saw_spans = [s for s in _note_spans(sc, 5) if t0 <= s[0] < t1]
    lead_ons = {on for on, _off, _p in lead_spans}
    saw_ons = [on for on, _off, _p in saw_spans]
    if len(saw_ons) < 10:
        fails.append(f"saw counter-line has only {len(saw_ons)} notes")
    coincident = [on for on in saw_ons if on in lead_ons]
    if saw_ons and len(coincident) > 0.5 * len(saw_ons):
        fails.append(f"{len(coincident)}/{len(saw_ons)} saw onsets coincide "
                     f"with the lead (need < 50%)")
    # pitch-class doubling at coincident onsets
    lead_at = {on: p for on, _off, p in lead_spans}
    saw_at = {on: p for on, _off, p in saw_spans}
    doubled = [on for on in coincident
               if (lead_at[on] - saw_at[on]) % 12 == 0]
    if coincident and len(doubled) > 0.25 * len(coincident):
        fails.append(f"pitch-class doubling on {len(doubled)}/"
                     f"{len(coincident)} coincident onsets (> 25%)")
    # downbeat pairwise consonance, every 4 beats
    for db in range(400, 432, 4):
        lp = _pitch_at(lead_spans, _tick(float(db)))
        sp = _pitch_at(saw_spans, _tick(float(db)))
        if lp is None or sp is None:
            fails.append(f"a voice is silent on downbeat {db}")
        elif (lp - sp) % 12 not in _CONSONANT:
            fails.append(f"downbeat {db}: lead {lp} vs saw {sp} dissonant")
    # contrary + oblique motion >= 60% (sampled per beat)
    moves = contrary = 0
    prev = None
    for b in range(400, 432):
        lp = _pitch_at(lead_spans, _tick(float(b)))
        sp = _pitch_at(saw_spans, _tick(float(b)))
        if lp is None or sp is None:
            prev = None
            continue
        if prev is not None:
            dl, ds = lp - prev[0], sp - prev[1]
            if dl or ds:
                moves += 1
                if dl * ds < 0 or (dl == 0) != (ds == 0):
                    contrary += 1
        prev = (lp, sp)
    if moves and contrary < 0.6 * moves:
        fails.append(f"only {contrary}/{moves} contrary+oblique motion "
                     f"(< 60%)")
    return fails


def _o_soar_sweep(sc):
    """CC74 macro-sweep, risers into both drops, the swoop, the held soar."""
    fails = []
    lane = [(t, v) for t, v in _cc_lane(sc, 1, 74)
            if _tick(B2_T0) <= t <= _tick(404.0)]
    if lane:
        vals = [v for _t, v in lane]
        peak_i = vals.index(max(vals))
        if max(vals) - min(vals) < 60:
            fails.append(f"pad CC74 sweep covers {max(vals) - min(vals)} "
                         f"units (< 60)")
        if peak_i == 0 or peak_i == len(vals) - 1:
            fails.append("pad CC74 sweep does not rise then fall")
    else:
        fails.append("no pad CC74 lane in build two")
    for drop in (D1_T0, D2_T0):
        t0, t1 = _tick(drop - 9.0), _tick(drop)
        if not any(t0 <= t < t1 for t, _p, _v in _note_ons(sc, 13)):
            fails.append(f"no riser (ch13) into the drop at {drop:g}")
    # portamento swoop: CC65 on, then a >= 12-semitone note pair
    lane65 = _cc_lane(sc, 5, 65)
    on_t = [t for t, v in lane65 if v >= 64]
    if not on_t:
        fails.append("no portamento swoop (CC65 never on)")
    else:
        saw = _note_ons(sc, 5)
        pair = [(p1, p2) for (t1_, p1, _v1), (t2_, p2, _v2)
                in zip(saw, saw[1:])
                if any(t <= t1_ for t in on_t) and abs(p2 - p1) >= 12
                and _tick(394.0) <= t1_ <= _tick(400.0)]
        if not pair:
            fails.append("portamento on, but no >=12-semitone swoop pair "
                         "into DROP2")
    # the >= 6-beat held lead soar with a CC1 bloom
    soars = [(on, off) for on, off, p in _note_spans(sc, 14)
             if off - on >= 6 * _PPQ and _tick(D1_T0) <= on < _tick(D1_T1)]
    if not soars:
        fails.append("no >=6-beat held lead soar in DROP1")
    else:
        on, off = soars[0]
        cc1 = [v for t, v in _cc_lane(sc, 14, 1) if on <= t <= off]
        if not cc1 or max(cc1) < 40:
            fails.append("lead soar lacks a CC1 bloom (max < 40)")
    return fails


def _o_layer_stack(sc):
    fails = []
    for name, lo, hi, want in (("cold open", 0.0, 32.0, 14),
                               ("pull-through", 400.0, 432.0, 14)):
        n = len(_active_channels(sc, lo, hi))
        if n < want:
            fails.append(f"{name} [{lo:g},{hi:g}) has {n} active channels "
                         f"(< {want})")
    return fails


def oracles(sc, info, spans):
    del info, spans
    sums = _bar_sums(sc)
    return [
        ("cold_open_loudest_start", _o_cold_open(sums)),
        ("roll_strips_layers", _o_roll_strips(sc)),
        ("quiet_duet", _o_quiet_duet(sc, sums)),
        ("build_drop_chain", _o_build_drop_chain(sums)),
        ("fill_escalation", _o_fill_escalation(sc)),
        ("hook_retrograde_exact", _o_retrograde(sc)),
        ("ascent_statements", _o_ascent(sc)),
        ("drop2_counterpoint", _o_counterpoint(sc)),
        ("soar_sweep", _o_soar_sweep(sc)),
        ("layer_stack", _o_layer_stack(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — trimmed inner windows, generous margins.
# ---------------------------------------------------------------------------


def audio_checks(ctx):
    def win_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    open_db = win_db(2.0, 30.0)
    quiet_db = win_db(100.0, 156.0)
    d1_db = win_db(244.0, 300.0)
    d2_db = win_db(404.0, 460.0)
    b1_db = win_db(164.0, 196.0)
    checks = []
    f = []
    # Margins CALIBRATED against the real 2026.07.17 render (the -18 LUFS
    # normalized master compresses absolute contrasts; the speculative
    # 3/8/10 dB guesses were mis-set, the T361 lesson).  Measured: cold
    # open +1.9 dB over early build one; quiet 6.1 dB under DROP1;
    # pull-through 6.6 dB over the quiet.  Thresholds sit below the
    # measured contrast but far above a flat mix (~0-1 dB), so each check
    # still falsifies a track without the shape.
    if open_db < b1_db + 1.5:
        f.append(f"cold open {open_db:.1f} dB not >=1.5 dB above early build "
                 f"one {b1_db:.1f} dB")
    checks.append(("cold_open_arrives_hot", f))
    f = []
    if quiet_db > d1_db - 5.0:
        f.append(f"quiet {quiet_db:.1f} dB not >=5 dB under DROP1 "
                 f"{d1_db:.1f} dB")
    checks.append(("quiet_is_hushed", f))
    f = []
    if d2_db < quiet_db + 5.0:
        f.append(f"pull-through {d2_db:.1f} dB not >=5 dB above the quiet "
                 f"{quiet_db:.1f} dB")
    if d2_db < d1_db - 1.0:
        f.append(f"pull-through {d2_db:.1f} dB more than 1 dB under DROP1 "
                 f"{d1_db:.1f} dB")
    checks.append(("pull_through_peaks", f))
    return checks
