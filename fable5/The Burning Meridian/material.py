"""material.py — the recurring musical material of *The Burning Meridian*.

Three orchestral film-epic instrumentals sharing one HORN THEME (the
"brass" of this orchestra is layered rock organ + saw stack + choir —
hollowsynth has no brass family, so the section is built, not preset).

  HORN_THEME     16 beats, heroic: strong-beat skeleton [1 5 6 5]
                 is a chord tone of BOTH the muster ground and the
                 battle ground — the same call opens track 1 and rides
                 the 5/4 battle of track 3 without changing a note.
  MUSTER_GROUND  i VI III VII in D aeolian (Dm Bb F C)
  BATTLE_GROUND  i i VI VII (5/4 bars) — the war footing
  DESCANT        the theme a diatonic 3rd up, snapped clash-free, for
                 the track-3 stack; ELEGY_A / ELEGY_B are track 2's
                 fiddle-and-flute duet, pairwise consonant at every
                 3/4 barline and midbar.
  OSTINATO       the 12/8 low-string engine (track 1): four groups of
                 three, all chord tones; ost_54 is its 5/4 war guise
                 (3+2), oracle-checked for coverage and chord tones.
  LAMENT_GROUND  track 2: i iv VI VII in A aeolian... transposed view:
                 written as degrees of D aeolian rooted on 5 — kept
                 simple: [1, 4, 6, 7] in A aeolian handled by track 2
                 passing its own base.

`verify_material()` returns failures; build --verify calls it.
"""

from __future__ import annotations

import engine as en

MODE = "aeolian"
CLASH = {1, 2, 6, 10, 11}


def chord_set(root: int) -> set[int]:
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def interval(a: int, b: int) -> int:
    return (en.deg_semis(MODE, a) - en.deg_semis(MODE, b)) % 12


# ---------------------------------------------------------------------------
# The horn theme and its grounds
# ---------------------------------------------------------------------------

MUSTER_GROUND = [1, 6, 3, 7]            # Dm Bb F C (4/4, one bar each)
BATTLE_GROUND = [1, 1, 6, 7]            # the 5/4 war footing
LAMENT_GROUND = [1, 4, 6, 7]            # track 2 (in its own key base)

HORN_SKELETON = [1, 3, 3, 4]

HORN_THEME = [
    (1, 0.0, 1.0), (1, 1.0, 0.5), (2, 1.5, 0.5), (3, 2.0, 1.0),
    (5, 3.0, 1.0),
    (3, 4.0, 2.0), (4, 6.0, 1.0), (5, 7.0, 1.0),
    (3, 8.0, 1.5), (4, 9.5, 0.5), (5, 10.0, 1.0), (6, 11.0, 1.0),
    (4, 12.0, 2.5), (3, 14.5, 0.5), (1, 15.0, 1.0),
]
HORN_BEATS = 16.0
HORN_RANGE = 12
HORN_MAX_LEAP = 7


def shift_steps(theme, steps):
    return [(d + steps, s, dur) for d, s, dur in theme]


def snap_to_chord(voice, ground, bar_beats=4.0):
    import math
    eps = 1e-9
    out = []
    for deg, start, dur in voice:
        bar_start = math.floor(start / bar_beats + eps) * bar_beats
        nxt = math.ceil((start + eps) / bar_beats) * bar_beats
        if abs(start - bar_start) < eps:
            db = bar_start
        elif start < nxt < start + dur - eps:
            db = nxt
        else:
            out.append((deg, start, dur))
            continue
        root = ground[int(db // bar_beats) % len(ground)]
        if interval(deg, root) in CLASH:
            semis = en.deg_semis(MODE, deg)
            best = None
            for k in (0, 2, 4):
                for octv in (-7, 0, 7):
                    cand = root + k + octv
                    d = abs(en.deg_semis(MODE, cand) - semis)
                    if best is None or d < best[0] or (d == best[0]
                                                       and cand > best[1]):
                        best = (d, cand)
            deg = best[1]
        out.append((deg, start, dur))
    return out


def descant(ground, bar_beats=4.0):
    """The theme a 3rd up, snapped at every HALF bar (the stack rides
    the battle's strong beats, so mid-bar tones must be safe too —
    doubling the ground at half the bar length makes the snap check
    beats 0 AND 2 of each real bar)."""
    doubled = [r for r in ground for _ in (0, 1)]
    return snap_to_chord(shift_steps(HORN_THEME, 2), doubled,
                         bar_beats / 2.0)


# ---------------------------------------------------------------------------
# Track 2: the elegy duet (3/4; solo fiddle vs flute)
# ---------------------------------------------------------------------------

# 24 beats = 8 bars of 3/4 over LAMENT_GROUND (2 cycles), strongs at 0
# and 1.5 of each bar; composed to be pairwise consonant there.
ELEGY_A = [
    (5, 0.0, 2.0), (6, 2.0, 1.0),
    (6, 3.0, 1.5), (4, 4.5, 1.5),
    (8, 6.0, 2.0), (7, 8.0, 1.0),
    (7, 9.0, 1.5), (5, 10.5, 1.5),
    (5, 12.0, 2.0), (4, 14.0, 1.0),
    (4, 15.0, 1.5), (6, 16.5, 1.5),
    (6, 18.0, 2.0), (3, 20.0, 1.0),
    (2, 21.0, 1.5), (1, 22.5, 1.5),
]
ELEGY_B = [
    (3, 0.0, 3.0),
    (6, 3.0, 3.0),
    (6, 6.0, 3.0),
    (2, 9.0, 1.5), (0, 10.5, 1.5),
    (3, 12.0, 3.0),
    (1, 15.0, 1.5), (4, 16.5, 1.5),
    (3, 18.0, 3.0),
    (2, 21.0, 1.5), (4, 22.5, 1.5),
]
ELEGY_BEATS = 24.0
ELEGY_BAR = 3.0

# ---------------------------------------------------------------------------
# Ostinati
# ---------------------------------------------------------------------------

# 12/8 low-string engine: one bar = 4 compound beats = 4 groups of 3
# eighths (each 0.5 in quarter-note beats -> bar spans 6.0 beats).
OST_LADDER = (0, 0, 7, 0, 2, 0, 4, 2, 0, 7, 4, 2)


def ostinato(root: int) -> list[tuple[int, float, float]]:
    return [(root + OST_LADDER[i], i * 0.5, 0.5) for i in range(12)]


# 5/4 war guise (3+2): ten eighths.
OST54 = (0, 0, 7, 0, 4, 0, 2, 4, 7, 4)


def ost_54(root: int) -> list[tuple[int, float, float]]:
    return [(root + OST54[i], i * 0.5, 0.5) for i in range(10)]


# ---------------------------------------------------------------------------
# The oracle
# ---------------------------------------------------------------------------


def _sounding_at(theme, beat, length):
    b = beat % length
    for deg, start, dur in theme:
        if start - 1e-9 <= b < start + dur - 1e-9:
            return deg
    return None


def _range_semis(theme):
    s = [en.deg_semis(MODE, d) for d, _s, _du in theme]
    return max(s) - min(s)


def _max_leap(theme):
    ordered = sorted(theme, key=lambda x: x[1])
    s = [en.deg_semis(MODE, d) for d, _s, _du in ordered]
    return max((abs(b - a) for a, b in zip(s, s[1:])), default=0)


def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. Horn skeleton; chord tone of BOTH grounds; heroic but singable.
    sk = [_sounding_at(HORN_THEME, b * 4.0, HORN_BEATS) for b in range(4)]
    if sk != HORN_SKELETON:
        fails.append(f"HORN skeleton {sk} != {HORN_SKELETON}")
    for gname, ground in (("MUSTER_GROUND", MUSTER_GROUND),
                          ("BATTLE_GROUND", BATTLE_GROUND)):
        for bar, deg in enumerate(HORN_SKELETON):
            if ((deg - 1) % 7) + 1 not in chord_set(ground[bar]):
                fails.append(f"HORN downbeat {bar * 4} (deg {deg}) not a "
                             f"chord tone of {gname}")
    if _range_semis(HORN_THEME) > HORN_RANGE:
        fails.append(f"HORN spans {_range_semis(HORN_THEME)}")
    if _max_leap(HORN_THEME) > HORN_MAX_LEAP:
        fails.append(f"HORN leaps {_max_leap(HORN_THEME)}")

    # 2. The snapped descant is clash-free against BATTLE_GROUND roots
    #    and against the theme itself on the strong beats.
    desc = descant(BATTLE_GROUND)
    for bar in range(4):
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            dd = _sounding_at(desc, strong, HORN_BEATS)
            dt = _sounding_at(HORN_THEME, strong, HORN_BEATS)
            if dd is None:
                continue
            if interval(dd, BATTLE_GROUND[bar]) in CLASH:
                fails.append(f"descant vs root: clash at {strong}")
            if dt is not None and interval(dd, dt) in CLASH:
                fails.append(f"descant vs theme: clash at {strong} "
                             f"({dd} vs {dt})")

    # 3. The elegy duet: chord tones at the bar lines, pairwise
    #    consonant at beats 0 and 1.5 of every 3/4 bar.
    for bar in range(8):
        root = LAMENT_GROUND[bar % 4]
        for label, voice in (("ELEGY_A", ELEGY_A), ("ELEGY_B", ELEGY_B)):
            db = _sounding_at(voice, bar * ELEGY_BAR, ELEGY_BEATS)
            if db is not None \
                    and ((db - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"{label} bar {bar}: degree {db} not a "
                             f"chord tone")
        for where in (0.0, 1.5):
            da = _sounding_at(ELEGY_A, bar * ELEGY_BAR + where,
                              ELEGY_BEATS)
            db = _sounding_at(ELEGY_B, bar * ELEGY_BAR + where,
                              ELEGY_BEATS)
            if da is not None and db is not None \
                    and interval(da, db) in CLASH:
                fails.append(f"elegy duet: {da} vs {db} clash at bar "
                             f"{bar} + {where}")
    for label, voice in (("ELEGY_A", ELEGY_A), ("ELEGY_B", ELEGY_B)):
        if _max_leap(voice) > 7:
            fails.append(f"{label} leaps more than a 5th")

    # 4. Ostinati: full coverage, all chord tones.
    for root in sorted(set(MUSTER_GROUND + BATTLE_GROUND)):
        for label, cell, span in (("ostinato", ostinato(root), 6.0),
                                  ("ost_54", ost_54(root), 5.0)):
            got = max(s + d for _dg, s, d in cell)
            if abs(got - span) > 1e-9:
                fails.append(f"{label}({root}) spans {got} != {span}")
            for deg, _s, _d in cell:
                if ((deg - root) % 7) not in (0, 2, 4):
                    fails.append(f"{label}({root}): step {deg - root} "
                                 f"not a chord tone")

    # 5. No diminished roots.
    for gname, ground in (("MUSTER_GROUND", MUSTER_GROUND),
                          ("BATTLE_GROUND", BATTLE_GROUND),
                          ("LAMENT_GROUND", LAMENT_GROUND)):
        if any(r == 2 for r in ground):
            fails.append(f"{gname}: diminished root")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass (horn skeleton "
          f"{HORN_SKELETON} over both grounds; elegy duet consonant)")
