"""material.py — the recurring musical material of *Tuxedo Noir*.

A spy-idiom single (E aeolian, swung): a walking minor VAMP in the
bass, a twang-guitar THEME against a STAB counterline (pairwise
consonant on the strong beats, machine-verified), a 7/8 CHASE cell,
and the genre's signature colour — the minor-major-9 chord — saved
for the final ring (its D# lives outside the mode and is written as a
raw MIDI note, once).

This is original material in the spy-score idiom; it quotes no
existing piece.
"""

from __future__ import annotations

import engine as en

MODE = "aeolian"                # E aeolian
CLASH = {1, 2, 6, 10, 11}


def chord_set(root: int) -> set[int]:
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def interval(a: int, b: int) -> int:
    return (en.deg_semis(MODE, a) - en.deg_semis(MODE, b)) % 12


# ---------------------------------------------------------------------------
# Grounds
# ---------------------------------------------------------------------------

VAMP_GROUND = [1, 1, 6, 7]              # Em Em C D — the noir floor
CHASE_GROUND = [1, 7, 6, 7]             # the 7/8 pursuit

# ---------------------------------------------------------------------------
# The vamp: one swung 4/4 bar of walking bass.  Swing is written into
# the cell (long-short 2:1 pairs).  Strong beats carry chord tones;
# five distinct pitches keep it a LINE, not a pedal.
# ---------------------------------------------------------------------------

SW = 2.0 / 3.0                          # the swung long half

VAMP_CELL = [
    (0, 0.0, SW), (0, SW, 1 - SW),
    (2, 1.0, SW), (3, 1.0 + SW, 1 - SW),
    (4, 2.0, SW), (3, 2.0 + SW, 1 - SW),
    (2, 3.0, SW), (1, 3.0 + SW, 1 - SW),
]
VAMP_MIN_DISTINCT = 5


def vamp(root: int) -> list[tuple[int, float, float]]:
    return [(root + s, b, d) for s, b, d in VAMP_CELL]


# The 7/8 chase cell (3+2+2).
CHASE_CELL = [
    (0, 0.0, 0.5), (0, 0.5, 0.5), (2, 1.0, 0.5), (4, 1.5, 0.5),
    (0, 2.0, 0.5), (4, 2.5, 0.5), (7, 3.0, 0.5),
]

# ---------------------------------------------------------------------------
# The theme and the stab counterline (16 beats over VAMP_GROUND).
# Skeleton [5 3 1 2]: sultry fall from the 5th, hanging on the 9th.
# ---------------------------------------------------------------------------

THEME_SKELETON = [5, 3, 1, 2]

THEME = [
    (5, 0.0, 2.0 + SW), (6, 2.0 + SW, 1 - SW), (5, 3.0, 1.0),
    (3, 4.0, 2.0), (4, 6.0, SW), (3, 6.0 + SW, 1 - SW), (2, 7.0, 1.0),
    (1, 8.0, 2.0 + SW), (2, 10.0 + SW, 1 - SW), (3, 11.0, 1.0),
    (2, 12.0, 3.0), (1, 15.0, 1.0),
]
THEME_BEATS = 16.0
THEME_MAX_LEAP = 7

# Stabs: syncopated chord-tone hits; the SOUNDING value at each strong
# beat (0 and 2 per bar) must be consonant with the theme.
STAB_LINE = [
    (3, 0.0, 1.5), (5, 1.5, 0.5), (5, 2.0, 1.5),
    (5, 4.0, 1.5), (7, 5.5, 0.5), (8, 6.0, 1.5),
    (6, 8.0, 1.5), (8, 9.5, 0.5), (8, 10.0, 1.5),
    (7, 12.0, 1.5), (9, 13.5, 0.5), (9, 14.0, 2.0),
]

# The final colour: E minor-major-9, raw MIDI (D#4 = 63 is chromatic).
MINMAJ9 = [40, 52, 55, 59, 63, 66]      # E2 E3 G3 B3 D#4 F#4

# ---------------------------------------------------------------------------
# The oracle
# ---------------------------------------------------------------------------


def _sounding_at(theme, beat, length):
    b = beat % length
    for deg, start, dur in theme:
        if start - 1e-9 <= b < start + dur - 1e-9:
            return deg
    return None


def _max_leap(theme):
    ordered = sorted(theme, key=lambda x: x[1])
    s = [en.deg_semis(MODE, d) for d, _s, _du in ordered]
    return max((abs(b - a) for a, b in zip(s, s[1:])), default=0)


def _check_cell(fails, name, cell, span, strongs, min_distinct):
    got = max(s + d for _st, s, d in cell)
    if abs(got - span) > 1e-9:
        fails.append(f"{name}: spans {got} != {span}")
    horizon = 0.0
    for _st, s, d in sorted(cell, key=lambda x: x[1]):
        if s - horizon > 1e-9:
            fails.append(f"{name}: gap at {horizon}")
            break
        horizon = max(horizon, s + d)
    for strong in strongs:
        step = next((st for st, s, d in cell if s <= strong < s + d),
                    None)
        if step is None or step % 7 not in (0, 2, 4):
            fails.append(f"{name}: beat {strong} step {step} not a "
                         f"chord tone")
    if len({st for st, _s, _d in cell}) < min_distinct:
        fails.append(f"{name}: fewer than {min_distinct} pitches")


def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. Theme skeleton, chord tones, spy-singable.
    sk = [_sounding_at(THEME, b * 4.0, THEME_BEATS) for b in range(4)]
    if sk != THEME_SKELETON:
        fails.append(f"THEME skeleton {sk} != {THEME_SKELETON}")
    for bar, deg in enumerate(THEME_SKELETON):
        if ((deg - 1) % 7) + 1 not in chord_set(VAMP_GROUND[bar]):
            fails.append(f"THEME downbeat {bar * 4} not a chord tone")
    if _max_leap(THEME) > THEME_MAX_LEAP:
        fails.append(f"THEME leaps {_max_leap(THEME)}")

    # 2. Stab line: strong-beat chord tones; pairwise consonant with
    #    the theme at beats 0 and 2 of every bar.
    for bar in range(4):
        root = VAMP_GROUND[bar]
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            ds = _sounding_at(STAB_LINE, strong, THEME_BEATS)
            dt = _sounding_at(THEME, strong, THEME_BEATS)
            if ds is None:
                continue
            if ((ds - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"STAB at {strong} (deg {ds}) not a chord "
                             f"tone")
            if dt is not None and interval(ds, dt) in CLASH:
                fails.append(f"STAB vs THEME clash at {strong} "
                             f"({ds} vs {dt})")

    # 3. Cells: coverage, strong chord tones, melodic floors.
    _check_cell(fails, "VAMP_CELL", VAMP_CELL, 4.0, (0.0, 2.0),
                VAMP_MIN_DISTINCT)
    _check_cell(fails, "CHASE_CELL", CHASE_CELL, 3.5, (0.0, 1.5, 2.5), 4)

    # 4. The vamp is genuinely SWUNG: every on-beat 8th pair is 2:1.
    for st, s, d in VAMP_CELL:
        if abs(s - round(s)) < 1e-9 and abs(d - SW) < 1e-9:
            continue
        if abs((s - SW) - round(s - SW)) < 1e-9 \
                and abs(d - (1 - SW)) < 1e-9:
            continue
        if abs(s - round(s)) < 1e-9 and d >= 1.0 - 1e-9:
            continue
        fails.append(f"VAMP_CELL: ({st},{s},{d}) breaks the 2:1 swing")

    # 5. Grounds root no diminished chord; the min-maj9 spells E-G-B-
    #    D#-F# from an E root.
    for gname, g in (("VAMP_GROUND", VAMP_GROUND),
                     ("CHASE_GROUND", CHASE_GROUND)):
        if any(r == 2 for r in g):
            fails.append(f"{gname}: diminished root")
    pcs = sorted({p % 12 for p in MINMAJ9})
    if pcs != sorted({4, 7, 11, 3, 6}):
        fails.append(f"MINMAJ9 pitch classes {pcs} are not min-maj9 on E")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass (theme "
          f"{THEME_SKELETON}, stabs consonant, vamp swung 2:1)")
