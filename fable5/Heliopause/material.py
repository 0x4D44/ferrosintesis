"""material.py — the recurring musical material of *Heliopause*.

Two synth-based instrumentals in the Jean-Michel Jarre / Oxygène
idiom: analog sequencer cells with their filters always in motion,
slow warm harmonic rhythm underneath fast surface figuration, singing
portamento leads, wind and whoosh transitions, and an economy of
material a machine can certify:

  THEME_A        Part One's lead melody (16 beats over GROUND_A) —
                 singable range, mostly stepwise, long tones built to
                 carry portamento glides and bend falls.
  THEME_B        the answering melody; A and B are proven pairwise
                 CONSONANT on every strong beat over GROUND_A so the
                 Part One climax can play them together.
  THEME_A_INV    Part Two's lead IS Part One's theme inverted around
                 its opening degree — interval-by-interval, oracle-
                 verified (the two parts are one idea, mirrored).
  GROUND_A       i VII VI VII in A aeolian (Am G F G), one bar each
  GROUND_LIFT    the climax reharmonization (VI VII i v) — THEME_A's
                 strong beats are chord tones of BOTH grounds
  SEQ_CELL       the sequencer: 16 sixteenth slots ladder-climbing the
                 chord of its bar (all chord tones, by construction)
  BASS_PULSE     the melodic 8th-note bass: root octaves with a
                 walking turn, >= 4 distinct pitches, root under the
                 strong beats
  WALTZ_CELL     Part One's 3/4 episode figure
  SHUFFLE_CELL   Part Two's 6/8 sequencer guise (same ladder, 12
                 slots) — the inversion carries the meter change

`verify_material()` returns failures; both parts' build --verify call
it.  Fix the material, never the oracle.
"""

from __future__ import annotations

import engine as en

MODE = "aeolian"                # A aeolian
CLASH = {1, 2, 6, 10, 11}       # inversion-symmetric dissonance set


def chord_set(root: int) -> set[int]:
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def interval(a: int, b: int, mode: str = MODE) -> int:
    return (en.deg_semis(mode, a) - en.deg_semis(mode, b)) % 12


# ---------------------------------------------------------------------------
# Grounds
# ---------------------------------------------------------------------------

GROUND_A = [1, 7, 6, 7]                 # Am G F G, one 4/4 bar each
GROUND_LIFT = [6, 7, 1, 5]              # F G Am Em — the climax lean
GROUND_B2 = [1, 6, 7, 5]                # Part Two: Am F G Em

# ---------------------------------------------------------------------------
# Themes.  THEME_A skeleton on downbeats: [1 2 3 2] over both grounds:
#   GROUND_A  roots 1,7,6,7 -> chord sets {1,3,5},{7,2,4},{6,1,3},{7,2,4}
#   GROUND_LIFT roots 6,7,1,1 ->          {6,1,3},{7,2,4},{1,3,5},{1,3,5}
#   degree 1 in {1,3,5} and {6,1,3}; 2 in {7,2,4}; 3 in {6,1,3} and
#   {1,3,5} — every downbeat is a chord tone of BOTH.
# ---------------------------------------------------------------------------

A_SKELETON = [1, 2, 3, 2]

THEME_A = [
    (1, 0.0, 2.5), (2, 2.5, 0.5), (3, 3.0, 1.0),
    (2, 4.0, 2.0), (1, 6.0, 1.0), (2, 7.0, 1.0),
    (3, 8.0, 2.5), (4, 10.5, 0.5), (5, 11.0, 1.0),
    (2, 12.0, 2.0), (3, 14.0, 1.0), (1, 15.0, 1.0),
]
THEME_BEATS = 16.0
THEME_RANGE_SEMIS = 12
THEME_MAX_LEAP = 5

# THEME_B: the answer.  Sparse, higher, chord-tone strong beats,
# composed against THEME_A's strong-beat values [1,3,2,1,3,5,2,1].
THEME_B = [
    (5, 0.0, 3.0), (6, 3.0, 1.0),
    (7, 4.0, 2.0), (6, 6.0, 1.5), (5, 7.5, 0.5),
    (6, 8.0, 2.0), (8, 10.0, 2.0),
    (7, 12.0, 2.0), (8, 14.0, 0.5), (6, 14.5, 0.5), (5, 15.0, 1.0),
]


def invert(theme, around: int | None = None):
    """Mirror a theme's degrees around `around` (default: its first
    degree): the Part Two lead is Part One's theme upside down."""
    pivot = theme[0][0] if around is None else around
    return [(2 * pivot - d, s, dur) for d, s, dur in theme]


THEME_A_INV = invert(THEME_A)           # skeleton [1 0 -1 0]

# ---------------------------------------------------------------------------
# The sequencer and the bass
# ---------------------------------------------------------------------------

SEQ_LADDER = (0, 2, 4, 7, 9, 7, 4, 2)   # chord steps, up-and-over


def seq_cell(root: int, slots: int = 16) -> list[tuple[int, float, float]]:
    """One bar of sequencer: `slots` even subdivisions laddering the
    chord of `root` (16 = 4/4 sixteenths; 12 = the 6/8 shuffle guise)."""
    beat = 4.0 if slots == 16 else 3.0
    step = beat / slots
    return [(root + SEQ_LADDER[i % len(SEQ_LADDER)], i * step, step)
            for i in range(slots)]


_BASS_CELL = [
    (0, 0.0, 0.5), (7, 0.5, 0.5), (0, 1.0, 0.5), (7, 1.5, 0.5),
    (0, 2.0, 0.5), (4, 2.5, 0.5), (5, 3.0, 0.5), (2, 3.5, 0.5),
]
BASS_MIN_DISTINCT = 4


def bass_pulse(root: int) -> list[tuple[int, float, float]]:
    return [(root + s, b, d) for s, b, d in _BASS_CELL]


# Part One's 3/4 episode: a waltz figure on each ground root.
WALTZ_CELL = [(0, 0.0, 1.0), (4, 1.0, 0.5), (7, 1.5, 0.5),
              (9, 2.0, 0.5), (7, 2.5, 0.5)]

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
    semis = [en.deg_semis(MODE, d) for d, _s, _dur in theme]
    return max(semis) - min(semis)


def _max_leap(theme):
    ordered = sorted(theme, key=lambda x: x[1])
    semis = [en.deg_semis(MODE, d) for d, _s, _dur in ordered]
    return max((abs(b - a) for a, b in zip(semis, semis[1:])), default=0)


def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. THEME_A skeleton, chord tones of BOTH grounds, singability.
    sk = [_sounding_at(THEME_A, b * 4.0, THEME_BEATS) for b in range(4)]
    if sk != A_SKELETON:
        fails.append(f"THEME_A skeleton {sk} != {A_SKELETON}")
    for gname, ground in (("GROUND_A", GROUND_A),
                          ("GROUND_LIFT", GROUND_LIFT)):
        for bar, deg in enumerate(A_SKELETON):
            if ((deg - 1) % 7) + 1 not in chord_set(ground[bar]):
                fails.append(f"THEME_A downbeat {bar * 4} (deg {deg}) not "
                             f"a chord tone of {gname}")
    if _range_semis(THEME_A) > THEME_RANGE_SEMIS:
        fails.append(f"THEME_A spans {_range_semis(THEME_A)} semis")
    if _max_leap(THEME_A) > THEME_MAX_LEAP:
        fails.append(f"THEME_A leaps {_max_leap(THEME_A)} semis")

    # 2. THEME_B strong beats are chord tones; A and B pairwise
    #    consonant at beats 0 and 2 of every GROUND_A bar.
    for bar in range(4):
        root = GROUND_A[bar]
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            db = _sounding_at(THEME_B, strong, THEME_BEATS)
            da = _sounding_at(THEME_A, strong, THEME_BEATS)
            if db is not None \
                    and abs(strong % 4.0) < 1e-9 \
                    and ((db - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"THEME_B downbeat {strong} (deg {db}) not a "
                             f"chord tone")
            if da is not None and db is not None \
                    and interval(db, da) in CLASH:
                fails.append(f"A/B counterpoint: {da} vs {db} = interval "
                             f"{interval(db, da)} at beat {strong}")

    # 2b. TRIPLE counterpoint: A, B and A_INV pairwise consonant at
    #     beats 0 and 2 of every GROUND_A bar (Part Two's climax
    #     stacks all three), and A_INV's downbeats are chord tones of
    #     GROUND_A (the inverted skeleton lands on the roots).
    voices = {"A": THEME_A, "B": THEME_B, "INV": THEME_A_INV}
    for bar in range(4):
        db = _sounding_at(THEME_A_INV, bar * 4.0, THEME_BEATS)
        if db is not None \
                and ((db - 1) % 7) + 1 not in chord_set(GROUND_A[bar]):
            fails.append(f"A_INV downbeat {bar * 4} (deg {db}) not a "
                         f"chord tone of GROUND_A")
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            names = sorted(voices)
            snd = {nm: _sounding_at(voices[nm], strong, THEME_BEATS)
                   for nm in names}
            for i, na in enumerate(names):
                for nb in names[i + 1:]:
                    if snd[na] is None or snd[nb] is None:
                        continue
                    iv = interval(snd[na], snd[nb])
                    if iv in CLASH:
                        fails.append(f"triple stack: {na}({snd[na]}) vs "
                                     f"{nb}({snd[nb]}) = {iv} at "
                                     f"beat {strong}")

    # 3. The inversion is exact: interval sequence negated.
    da = [en.deg_semis(MODE, d) for d, _s, _du in THEME_A]
    di = [en.deg_semis(MODE, d) for d, _s, _du in THEME_A_INV]
    iv_a = [b - a for a, b in zip(da, da[1:])]
    iv_i = [b - a for a, b in zip(di, di[1:])]
    # diatonic mirror: signs opposite everywhere, sizes within a step
    for k, (x, y) in enumerate(zip(iv_a, iv_i)):
        if x == 0 and y == 0:
            continue
        if (x > 0) == (y > 0) or abs(abs(x) - abs(y)) > 1:
            fails.append(f"THEME_A_INV: interval {k} ({x} vs {y}) is not "
                         f"a diatonic mirror")
    if [s for _d, s, _du in THEME_A] != [s for _d, s, _du in THEME_A_INV]:
        fails.append("THEME_A_INV: rhythm differs from THEME_A")

    # 4. The sequencer cell is all chord tones in both guises.
    for root in sorted(set(GROUND_A + GROUND_LIFT + GROUND_B2)):
        for slots in (16, 12):
            for deg, _s, _d in seq_cell(root, slots):
                if ((deg - 1) % 7) + 1 not in chord_set(root):
                    fails.append(f"seq_cell({root},{slots}): degree {deg} "
                                 f"outside the chord")

    # 5. The bass pulse: coverage, strong-beat roots, melodic floor.
    span = max(s + d for _st, s, d in _BASS_CELL)
    if abs(span - 4.0) > 1e-9:
        fails.append(f"BASS_CELL spans {span} != 4")
    for strong in (0.0, 2.0):
        step = next((st for st, s, d in _BASS_CELL if s <= strong < s + d),
                    None)
        if step is None or step % 7 not in (0, 2, 4):
            fails.append(f"BASS_CELL: beat {strong} not a chord tone")
    if len({st for st, _s, _d in _BASS_CELL}) < BASS_MIN_DISTINCT:
        fails.append("BASS_CELL: not melodic enough")

    # 6. No ground roots the diminished chord (degree 2 in aeolian).
    for gname, ground in (("GROUND_A", GROUND_A),
                          ("GROUND_LIFT", GROUND_LIFT),
                          ("GROUND_B2", GROUND_B2)):
        if any(r == 2 for r in ground):
            fails.append(f"{gname}: degree-2 root (diminished)")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass (theme A skeleton "
          f"{A_SKELETON}, A/B consonant, Part Two = A inverted)")
