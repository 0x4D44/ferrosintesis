"""material.py — the recurring musical material of *The Signal Fire*.

Everything is written as scale DEGREES (see engine.pitch) so the same figure
can be recast in any mode or key: the riff is A dorian in Ignition, D dorian
in the Lattice, A dorian under the Climb and A ionian in Ascension.

The piece's DNA is small on purpose:

  RIFF        one bass riff with a fixed degree skeleton, in three rhythmic
              guises (funk 4/4 sixteenths, 10/8 additive, augmented 16-beat)
  THEME_A     "The Signal"  — 32-beat singing arch (5 up to 11, back to 1)
  THEME_B     "The Flare"   — 16-beat syncopated call-and-response
  THEME_C     "The Watch"   — 32-beat minim chorale, low register
  LATTICE     the 10/8 riff split into three interlocking guitar lines

The three themes are composed over the same four-bar ground

    Am | G | Am | G        (i - bVII, degrees {1,3,5} / {7,2,4})

with a CHORD TONE on every bar-start downbeat, so any pair (and all three)
can be stacked in counterpoint — the finale depends on it.  When stacking
themes at different speeds, use the SAME augmentation factor for every
stacked theme so the checked downbeat alignment is preserved.

`verify_material()` proves all of this numerically; `build.py --verify`
calls it.  If a change breaks the oracle, fix the material, never the test.
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# The Riff.  Skeleton (consecutive duplicates collapsed): 1 8 7 5 6 4 5 0 1
# (0 is the flat-seventh below the tonic — G below A in A dorian.)
# ---------------------------------------------------------------------------

# 4/4 funk guise (one bar).  Main hits only; ghosts listed separately.
RIFF_FUNK = [
    (1, 0.0, 0.5), (1, 0.5, 0.25), (8, 0.75, 0.5),
    (7, 1.5, 0.5),
    (5, 2.0, 0.25), (6, 2.25, 0.25), (4, 2.5, 0.5),
    (5, 3.0, 0.25), (0, 3.25, 0.25), (1, 3.5, 0.25),
]
# Ghost sixteenths (played ~30 velocity below the main hits).
RIFF_FUNK_GHOSTS = [(1, 1.25, 0.25), (1, 3.75, 0.25)]

# 10/8 additive guise (one 5-beat cycle, quaver = 0.5, grouped 3+3+2+2).
RIFF_10 = [
    (1, 0.0, 0.5), (1, 0.5, 0.5), (8, 1.0, 0.5),      # 3
    (7, 1.5, 0.5), (5, 2.0, 0.5), (6, 2.5, 0.5),      # 3
    (4, 3.0, 0.5), (5, 3.5, 0.5),                     # 2
    (0, 4.0, 0.5), (1, 4.5, 0.5),                     # 2
]
RIFF_10_ACCENTS = (0, 3, 6, 8)          # quaver indices starting each group
RIFF_10_CROSS = (0, 2, 4, 7)            # cross-accent guise (2+2+3+3)
CYCLE_10 = 5.0                          # beats per 10/8 cycle

# Augmented guise (16 beats, half-time under the Ascension peal).
RIFF_AUG = [
    (1, 0, 3), (8, 3, 1), (7, 4, 2), (5, 6, 2),
    (6, 8, 2), (4, 10, 2), (5, 12, 1), (0, 13, 1), (1, 14, 2),
]


def riff_skeleton(notes: list[tuple[int, float, float]]) -> list[int]:
    """Degree sequence with consecutive duplicates collapsed."""
    out: list[int] = []
    for deg, _s, _d in sorted(notes, key=lambda x: x[1]):
        if not out or out[-1] != deg:
            out.append(deg)
    return out


# ---------------------------------------------------------------------------
# The ground: four bars, Am | G | Am | G.  Chord tones by bar index.
# ---------------------------------------------------------------------------

GROUND_BARS = 4
GROUND_BEATS = 16.0
CHORD_TONES = ({1, 3, 5}, {7, 2, 4})    # index bar % 2: Am-bar, G-bar


def chord_tones_at(beat: float) -> set[int]:
    bar = int(beat // 4) % 2
    return CHORD_TONES[bar]


# ---------------------------------------------------------------------------
# THEME_A — "The Signal".  32 beats.  A singing arch: opens on the fifth,
# climbs to the high fourth (degree 11) in bar 6, falls home to 1.
# ---------------------------------------------------------------------------

THEME_A = [
    (5, 0, 3), (3, 3, 1),
    (4, 4, 2), (2, 6, 2),
    (3, 8, 2), (5, 10, 1), (6, 11, 1),
    (7, 12, 2.5), (6, 14.5, 0.5), (7, 15, 1),
    (8, 16, 2), (9, 18, 1), (10, 19, 1),
    (11, 20, 3), (9, 23, 1),
    (10, 24, 1.5), (8, 25.5, 0.5), (7, 26, 1), (5, 27, 1),
    (4, 28, 1.5), (2, 29.5, 0.5), (1, 30, 2),
]
THEME_A_FRAG = THEME_A[:4]              # bars 1-2 — the "calling" fragment

# ---------------------------------------------------------------------------
# THEME_B — "The Flare".  16 beats.  Syncopated quaver cells: call (Am),
# response (G), call again reaching the octave, cadence figure.
# ---------------------------------------------------------------------------

THEME_B = [
    (1, 0, 0.5), (3, 0.5, 0.5), (5, 1, 0.75), (5, 1.75, 0.25),
    (6, 2, 0.5), (5, 2.5, 0.5), (3, 3, 1),
    (2, 4, 0.5), (4, 4.5, 0.5), (7, 5, 0.75), (4, 5.75, 0.25),
    (5, 6, 0.5), (4, 6.5, 0.5), (2, 7, 1),
    (1, 8, 0.5), (3, 8.5, 0.5), (5, 9, 0.75), (8, 9.75, 0.25),
    (7, 10, 0.5), (6, 10.5, 0.5), (5, 11, 1),
    (4, 12, 0.5), (6, 12.5, 0.5), (9, 13, 0.75), (7, 13.75, 0.25),
    (8, 14, 0.5), (7, 14.5, 0.25), (5, 14.75, 0.25), (4, 15, 0.5), (2, 15.5, 0.5),
]

# ---------------------------------------------------------------------------
# THEME_C — "The Watch".  32 beats.  A minim chorale in the 1..7 register,
# stepwise, built to sit UNDER either other theme.
# ---------------------------------------------------------------------------

THEME_C = [
    (1, 0, 3), (2, 3, 1),
    (4, 4, 2), (2, 6, 2),
    (5, 8, 4),
    (2, 12, 2), (4, 14, 2),
    (3, 16, 4),
    (4, 20, 2), (5, 22, 2),
    (5, 24, 2), (4, 26, 1), (2, 27, 1),
    (2, 28, 3), (1, 31, 1),
]

# ---------------------------------------------------------------------------
# The Lattice — the 10/8 riff dissolved into three interlocking guitars.
# Together the three lines play RIFF_10 verbatim; alone, each is a sparse
# ringing figure (sustain through the gaps, gate ~2.5 quavers).
# ---------------------------------------------------------------------------

LATTICE_SPLIT = ((0, 3, 6), (1, 4, 8), (2, 5, 7, 9))   # quaver indices


def lattice_line(which: int) -> list[tuple[int, float, float]]:
    """Line `which` (0..2): its quavers of RIFF_10, sustained to ~2.5 quavers
    (clipped at the cycle end so cycles can loop cleanly)."""
    picks = LATTICE_SPLIT[which]
    out = []
    for i in picks:
        deg, start, _ = RIFF_10[i]
        out.append((deg, start, min(1.25, CYCLE_10 - start)))
    return out


# ---------------------------------------------------------------------------
# Verification oracle — proves the material's structural promises.
# ---------------------------------------------------------------------------

_ALLOWED = {0, 3, 4, 5, 7, 8, 9}        # downbeat intervals mod 12


def _sounding_at(theme: list[tuple[int, float, float]], beat: float,
                 length: float) -> int | None:
    """Degree sounding at `beat` (theme looped over `length` beats)."""
    b = beat % length
    for deg, start, dur in theme:
        if start <= b < start + dur:
            return deg
    return None


def _downbeat_degrees(theme, length):
    """(beat, degree) at every bar-start downbeat 0,4,8,...,28 (looped)."""
    return [(bt, _sounding_at(theme, bt, length))
            for bt in range(0, int(GROUND_BEATS * 2), 4)]


def verify_material() -> list[str]:
    """Return a list of failures (empty == all good)."""
    fails: list[str] = []

    # 1. Riff skeleton identity across the three guises + the lattice.
    skel = riff_skeleton(RIFF_10)
    for name, notes in (("RIFF_FUNK", RIFF_FUNK), ("RIFF_AUG", RIFF_AUG)):
        if riff_skeleton(notes) != skel:
            fails.append(f"{name} skeleton {riff_skeleton(notes)} != {skel}")
    combined = sorted(
        (nt for w in range(3) for nt in
         ((RIFF_10[i][0], RIFF_10[i][1], RIFF_10[i][2])
          for i in LATTICE_SPLIT[w])),
        key=lambda x: x[1])
    if [x[:2] for x in combined] != [x[:2] for x in sorted(RIFF_10, key=lambda x: x[1])]:
        fails.append("lattice lines do not recombine into RIFF_10")

    # 2. Every theme has a chord tone on every bar-start downbeat.
    themes = {"THEME_A": (THEME_A, 32.0), "THEME_B": (THEME_B, 16.0),
              "THEME_C": (THEME_C, 32.0)}
    for name, (theme, length) in themes.items():
        for bt, deg in _downbeat_degrees(theme, length):
            if deg is None:
                fails.append(f"{name}: nothing sounding at downbeat {bt}")
            elif ((deg - 1) % 7) + 1 not in chord_tones_at(float(bt)) and \
                    deg % 7 not in {d % 7 for d in chord_tones_at(float(bt))}:
                fails.append(f"{name}: degree {deg} at downbeat {bt} "
                             f"is not a chord tone")

    # 3. Pairwise downbeat intervals are consonant; no parallel unisons.
    mode = "dorian"
    names = list(themes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, la = themes[names[i]]
            b, lb = themes[names[j]]
            prev = None
            for bt in range(0, int(GROUND_BEATS * 2), 4):
                da = _sounding_at(a, float(bt), la)
                db = _sounding_at(b, float(bt), lb)
                if da is None or db is None:
                    continue
                iv = abs(en.deg_semis(mode, da) - en.deg_semis(mode, db)) % 12
                if iv not in _ALLOWED:
                    fails.append(f"{names[i]}+{names[j]}: interval {iv} "
                                 f"at downbeat {bt}")
                if iv == 0 and prev == 0:
                    fails.append(f"{names[i]}+{names[j]}: parallel unison "
                                 f"into downbeat {bt}")
                prev = iv

    # 3b. The finale realizes the stack in A IONIAN (Ascension pairs
    # THEME_A on bells with THEME_C on strings/choir, both augmented x2 —
    # equal augmentation preserves this 1:1 downbeat alignment).  Re-check
    # that pair's downbeat intervals in ionian so a theme edit can't break
    # the finale while the dorian check still passes.  (THEME_B is answered
    # BETWEEN bell phrases in M5, never stacked on downbeats, so only the
    # A+C pair carries an ionian promise.)
    prev = None
    for bt in range(0, int(GROUND_BEATS * 2), 4):
        da = _sounding_at(THEME_A, float(bt), 32.0)
        dc = _sounding_at(THEME_C, float(bt), 32.0)
        if da is None or dc is None:
            continue
        iv = abs(en.deg_semis("ionian", da) - en.deg_semis("ionian", dc)) % 12
        if iv not in _ALLOWED:
            fails.append(f"THEME_A+THEME_C (ionian finale): interval {iv} "
                         f"at downbeat {bt}")
        if iv == 0 and prev == 0:
            fails.append(f"THEME_A+THEME_C (ionian finale): parallel unison "
                         f"into downbeat {bt}")
        prev = iv

    # 4. Register promises (so stacked themes never cross).
    if max(d for d, _, _ in THEME_C) > 7:
        fails.append("THEME_C leaves the 1..7 register")
    if max(d for d, _, _ in THEME_B) > 9:
        fails.append("THEME_B leaves the 1..9 register")
    if max(d for d, _, _ in THEME_A) != 11:
        fails.append("THEME_A peak is not degree 11")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass")
