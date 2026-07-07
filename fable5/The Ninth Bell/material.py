"""material.py — the recurring musical material of *The Ninth Bell*.

Everything is written as scale DEGREES of A aeolian (1 = A; degree d and
d+7 are the same tone class; degree 0 is the G below the tonic, engine
convention).  The DNA is deliberately tiny:

  THEME       "the lament" — 13 notes over the 4-bar ground, opening with
              a rising minor 6th (the anguish leap), ending hanging on
              degree 2: the withheld 1 that only the ninth bell answers.
  LEAP_CELL   the theme's opening pair (5, 10) — sequenced in the builds,
              whispered by the music box, stacked in stretto.
  COUNTER     "the collapsing staircase" — a falling 4-note scale entering
              one step lower each bar.  Verifier-clean over BOTH grounds.
  TOLL        the bell figure = the leap cell INVERTED (falling 10..5;
              8..5 where harmony demands; the cadence toll 8, 5, 1).
  TETRACHORD  the bass lament A G F E (degrees 1 0 -1 -2); its final
              F->E step is the phrygian gate into the climax.

Two grounds:

    HOME     Am | F  | C  | G      (i bVI bIII bVII — the demo's loop)
    CLIMAX   Am | Dm | Em | E7     (i iv v V7 — aeolian hardening into
                                    harmonic minor; E7 brings the G#)

THEME and COUNTER carry a chord tone on EVERY bar downbeat of BOTH
grounds; `verify_material()` proves it (and everything above) numerically.
If a change breaks the oracle, fix the material, never the test.
"""

from __future__ import annotations

import engine as en

MODE = "aeolian"
TONIC = en.n("A3")            # degree 1 = A3 unless a part transposes

# ---------------------------------------------------------------------------
# Grounds, as pitch-class sets (semitones mod 12; A=9).  Sets, not degree
# lists, because E7's G# lives outside the aeolian degree lattice.
# ---------------------------------------------------------------------------

PC = {"A": 9, "Bb": 10, "B": 11, "C": 0, "D": 2, "E": 4, "F": 5,
      "G": 7, "G#": 8}

CHORD_PCS = {
    "Am": {PC["A"], PC["C"], PC["E"]},
    "F":  {PC["F"], PC["A"], PC["C"]},
    "C":  {PC["C"], PC["E"], PC["G"]},
    "G":  {PC["G"], PC["B"], PC["D"]},
    "Dm": {PC["D"], PC["F"], PC["A"]},
    "Em": {PC["E"], PC["G"], PC["B"]},
    "E7": {PC["E"], PC["G#"], PC["B"], PC["D"]},
    "E":  {PC["E"], PC["G#"], PC["B"]},
    "Bb": {PC["Bb"], PC["D"], PC["F"]},
}

GROUND_HOME = ["Am", "F", "C", "G"]          # degrees 1 6 3 7
GROUND_HOME_DEGS = [1, 6, 3, 7]
GROUND_CLIMAX = ["Am", "Dm", "Em", "E7"]
GROUND_BEATS = 16.0                          # 4 bars of 4/4

# The two betrayal chords (HLD section 1).
HIT_CHORD = "E"          # hit #1: the dominant slammed as a question mark
FRACTURE_CHORD = "Bb"    # hit #2: the Neapolitan where resolution belonged


def home_triads(size: int = 3) -> list[list[int]]:
    """The demo's chord loop: triads on degrees 1 6 3 7 (base TONIC)."""
    return [en.triad(TONIC, MODE, d, size=size) for d in GROUND_HOME_DEGS]


# ---------------------------------------------------------------------------
# THEME — "the lament".  (degree, start-in-ground-beats, dur-beats).
# Base register A3 (cello); violin states it shift=+7 (or octave=+1).
# ---------------------------------------------------------------------------

THEME: list[tuple[int, float, float]] = [
    # bar 1 (Am): the anguish leap E -> C, sigh back down
    (5, 0.0, 1.0), (10, 1.0, 1.5), (9, 2.5, 0.5), (8, 3.0, 1.0),
    # bar 2 (F): the lament descent A G F onto the chord root
    (8, 4.0, 2.0), (7, 6.0, 1.0), (6, 7.0, 1.0),
    # bar 3 (C): the bell-like turn around G that fails to console
    (7, 8.0, 1.5), (8, 9.5, 0.5), (7, 10.0, 1.0), (5, 11.0, 1.0),
    # bar 4 (G): the hollow fall D -> B; degree 2 hangs, wanting 1
    (4, 12.0, 2.0), (2, 14.0, 2.0),
]

LEAP_CELL: tuple[int, int] = (5, 10)         # the rising minor 6th

# ---------------------------------------------------------------------------
# COUNTERSUBJECT — "the collapsing staircase" (quarters).
# ---------------------------------------------------------------------------

COUNTER: list[tuple[int, float, float]] = [
    (8, 0.0, 1.0), (7, 1.0, 1.0), (6, 2.0, 1.0), (5, 3.0, 1.0),
    (6, 4.0, 1.0), (5, 5.0, 1.0), (4, 6.0, 1.0), (3, 7.0, 1.0),
    (5, 8.0, 1.0), (4, 9.0, 1.0), (3, 10.0, 1.0), (2, 11.0, 1.0),
    (4, 12.0, 1.0), (3, 13.0, 1.0), (2, 14.0, 1.0), (1, 15.0, 1.0),
]

# ---------------------------------------------------------------------------
# TOLL — the bell derives from the theme (judge graft #5).
# ---------------------------------------------------------------------------

TOLL_FALL = [(10, 0.0, 2.0), (5, 2.0, 6.0)]     # the leap cell inverted
TOLL_SIMPLE = [(8, 0.0, 2.0), (5, 2.0, 6.0)]    # where harmony demands
TOLL_CADENCE_DEGS = (8, 5, 1)                   # the ninth bell's figure

# The nine-toll ledger: (beat, kind) — kind is 'fall', 'single-<deg>' or
# 'cadence'.  verify.check_nine_bells holds ch4 to exactly this frame
# (plus the climax peal window).  HLD section 4.
TOLL_LEDGER: list[tuple[float, str]] = [
    (32.0, "fall"),          # 1  Processional opens
    (64.0, "fall"),          # 2  second statement
    (96.0, "fall"),          # 3  First Ascent opens
    (128.0, "single-5"),     # 4  the E-major hit
    (164.0, "single-1"),     # 5  the void's organ creep-in
    (196.0, "fall"),         # 6  Rising Tide opens
    (244.0, "single-5"),     # 7  the feint drop
    (292.0, "fall"),         # 8  climax entry
    (394.0, "cadence"),      # 9  THE NINTH BELL: 8, 5, then the lone A
]
PEAL_WINDOW = (292.0, 352.0)   # climax downbeat peal allowed here only

# ---------------------------------------------------------------------------
# Bass lament tetrachord: A G F E below the tonic register.
# ---------------------------------------------------------------------------

TETRACHORD_DEGS = [1, 0, -1, -2]               # A G F E (engine degrees)
PHRYGIAN_GATE = ("F", "E")                     # bVI -> V, bars 72-73


# ---------------------------------------------------------------------------
# The oracle.  build.py --verify calls this first.
# ---------------------------------------------------------------------------

def _pc_of_degree(deg: int) -> int:
    return en.pitch(TONIC, MODE, deg) % 12


def _downbeat_check(notes, grounds: list[str], what: str) -> list[str]:
    fails = []
    for bar in range(4):
        t = bar * 4.0
        starts = [d for d, s, _dur in notes if abs(s - t) < 1e-9]
        if not starts:
            fails.append(f"{what}: no note starts on downbeat of bar {bar+1}")
            continue
        pc = _pc_of_degree(starts[0])
        for chord in (grounds[bar],):
            if pc not in CHORD_PCS[chord]:
                fails.append(f"{what}: bar {bar+1} downbeat degree "
                             f"{starts[0]} (pc {pc}) not a chord tone of "
                             f"{chord}")
    return fails


def verify_material() -> list[str]:
    """Numeric proof of every claim in this module.  Returns failures."""
    fails: list[str] = []

    # 1. Theme & countersubject downbeats vs BOTH grounds.
    for ground in (GROUND_HOME, GROUND_CLIMAX):
        fails += _downbeat_check(THEME, ground, f"THEME vs {ground}")
        fails += _downbeat_check(COUNTER, ground, f"COUNTER vs {ground}")

    # 2. Durations fill each bar exactly (theme), quarters (counter).
    for name, notes in (("THEME", THEME), ("COUNTER", COUNTER)):
        for bar in range(4):
            tot = sum(dur for _d, s, dur in notes
                      if bar * 4.0 - 1e-9 <= s < (bar + 1) * 4.0 - 1e-9)
            if abs(tot - 4.0) > 1e-9:
                fails.append(f"{name}: bar {bar+1} durations sum {tot} != 4")

    # 3. Theme range and size.
    pitches = [en.pitch(TONIC, MODE, d) for d, _s, _du in THEME]
    if max(pitches) - min(pitches) > 14:
        fails.append(f"THEME range {max(pitches)-min(pitches)} semis > 14")
    if not 8 <= len(THEME) <= 16:
        fails.append(f"THEME has {len(THEME)} notes, want 8-16")

    # 4. The toll is the leap cell inverted; the cadence ends on 1.
    if (TOLL_FALL[0][0], TOLL_FALL[1][0]) != (LEAP_CELL[1], LEAP_CELL[0]):
        fails.append("TOLL_FALL is not the inversion of LEAP_CELL")
    if TOLL_CADENCE_DEGS[-1] != 1:
        fails.append("cadence toll must end on degree 1 (the withheld A)")

    # 5. The theme ends hanging on degree 2 (the withheld resolution).
    if THEME[-1][0] != 2:
        fails.append(f"THEME ends on degree {THEME[-1][0]}, must hang on 2")

    # 6. The betrayal chords contain the melody notes they interrupt:
    #    hit #1 sounds under the theme's opening 5 (E); the fracture holds
    #    the theme's bar-4 downbeat D as its third.
    if _pc_of_degree(5) not in CHORD_PCS[HIT_CHORD]:
        fails.append("hit chord does not contain the theme's entry note E")
    if _pc_of_degree(4) not in CHORD_PCS[FRACTURE_CHORD]:
        fails.append("fracture chord does not hold the theme's downbeat D")

    # 7. Nine tolls, the last a cadence; the peal window sits inside VII.
    if len(TOLL_LEDGER) != 9:
        fails.append(f"toll ledger has {len(TOLL_LEDGER)} entries, want 9")
    if TOLL_LEDGER[-1][1] != "cadence":
        fails.append("the ninth toll must be the cadence")
    return fails
