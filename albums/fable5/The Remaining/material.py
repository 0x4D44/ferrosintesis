"""material.py — the shared musical DNA of *The Remaining*.

Everything that recurs across tracks lives HERE as data, and every claim the
album makes about that data is proven numerically by verify_material() —
written BEFORE the music, composed-to-pass (the repo method).  Track modules
import these objects; cross-track recurrences are recomputed from THIS file,
never re-typed.

The through-lines (HLD: "wrk_docs/2026.07.18 - HLD - The Remaining album
(five elegies).md"):

- THE GROUND      Dm - Bb - F - C (aeolian roots [1,6,3,7]), one bar each,
                  with a pinned suspension over every chord resolving DOWN
                  by step on beat 2 (the Richter sigh).  T5's turning swaps
                  in THE MAJOR GROUND, D - A - Bm - G (ionian [1,5,6,4]),
                  whose suspensions resolve UP by step (the sigh inverts).
- THE VIGIL THEME six notes, 8 beats, contour 5-4-3-4-3-2.  Degree 1 is
                  absent: every statement in tracks 1-4 ends on degree 2,
                  the "waiting tone".  Only T5's final statement may append
                  ARRIVAL — the album's one degree-1 ending, in D major.
- THE FIGURE      the departure ostinato: 8 contiguous quavers of broken
                  chord spanning a tenth, peak on quaver 3.  After T1's
                  departure it loses HOLES = {3, 6} (the peak among them);
                  T4 replays the same holed figure; T5 III fills the holes.
- DEPARTED_LINE   the interrupted violin II phrase: 12 notes, 16 beats, one
                  fourth-leap crest.  T1 plays exactly the first
                  INTERRUPT_AFTER = 7 notes, then the voice is silent; T5
                  states all 12 verbatim — the phrase finally finished.
- THE STATIC LANE T3's woodblock morse: "REMEMBER US", standard timing.
- SEATING         the album pan plan (string quartet seated left to right).
"""

from __future__ import annotations

import engine as en

MODE_MINOR = "aeolian"
MODE_MAJOR = "ionian"

# ---------------------------------------------------------------------------
# THE GROUND.  Roots as 1-based mode degrees; suspensions as (sus, res)
# semitone offsets above each chord's ROOT.  The minor sighs fall (4-3 on Dm,
# 9-8 on Bb, 4-3 on F, 4-3 on C); the major sighs rise by step to the third.
# ---------------------------------------------------------------------------

GROUND_DEGREES: list[int] = [1, 6, 3, 7]          # D, Bb, F, C in D aeolian
SUSPENSIONS: list[tuple[int, int]] = [(5, 3), (2, 0), (5, 4), (5, 4)]

MAJOR_GROUND_DEGREES: list[int] = [1, 5, 6, 4]    # D, A, Bm, G in D ionian
MAJOR_SUSPENSIONS: list[tuple[int, int]] = [(2, 4), (2, 4), (2, 3), (2, 4)]


def ground_roots(base: int, major: bool = False) -> list[int]:
    """The four ground roots above `base` (the tonic pitch); the composer
    re-octaves them for register."""
    degrees = MAJOR_GROUND_DEGREES if major else GROUND_DEGREES
    mode = MODE_MAJOR if major else MODE_MINOR
    return [en.pitch(base, mode, d) for d in degrees]


def ground_triad(base: int, index: int, major: bool = False,
                 size: int = 3) -> list[int]:
    """Diatonic triad for ground chord `index` (0..3)."""
    degrees = MAJOR_GROUND_DEGREES if major else GROUND_DEGREES
    mode = MODE_MAJOR if major else MODE_MINOR
    return en.triad(base, mode, degrees[index], size=size)


# ---------------------------------------------------------------------------
# THE VIGIL THEME.  (onset_beats, dur_beats, mode_degree); 8 beats total,
# contiguous.  THEME_END_DEG is the waiting tone; ARRIVAL is the single
# degree-1 ending T5 appends (A-G-F#-G-F#-E-D in the major recast).
# ---------------------------------------------------------------------------

THEME: list[tuple[float, float, int]] = [
    (0.0, 1.0, 5), (1.0, 1.0, 4), (2.0, 2.0, 3),
    (4.0, 1.0, 4), (5.0, 1.0, 3), (6.0, 2.0, 2),
]
THEME_LEN: float = 8.0
THEME_END_DEG: int = 2
ARRIVAL: tuple[float, float, int] = (8.0, 4.0, 1)
INVERT_AXIS: int = 3          # diatonic inversion axis (degree space)


def invert_deg(d: int, axis: int = INVERT_AXIS) -> int:
    """Diatonic (degree-space) inversion about `axis`."""
    return 2 * axis - d


def theme_notes(stretch: float = 1.0, invert_axis: int | None = None,
                arrival: bool = False) -> list[tuple[float, float, int]]:
    """The theme as (onset, dur, degree), optionally time-stretched,
    diatonically inverted, and/or with the ARRIVAL note appended."""
    notes = list(THEME) + ([ARRIVAL] if arrival else [])
    out = []
    for on, du, d in notes:
        deg = d if invert_axis is None else invert_deg(d, invert_axis)
        out.append((on * stretch, du * stretch, deg))
    return out


def play_theme(sc: en.Score, ch: int, t0: float, base: int,
               mode: str = MODE_MINOR, stretch: float = 1.0,
               vel: int = 80, vel_end: int | None = None, gate: float = 1.0,
               jt: int = 0, jv: int = 3, invert_axis: int | None = None,
               arrival: bool = False) -> float:
    """Play the theme; returns the end beat.  jt defaults to 0 so
    oracle-pinned statements stay tick-exact."""
    notes = theme_notes(stretch, invert_axis, arrival)
    total = max(on + du for on, du, _d in notes)
    for on, du, deg in notes:
        v = vel
        if vel_end is not None and total > 0:
            v = round(en.lerp(vel, vel_end, on / total))
        sc.note(ch, en.pitch(base, mode, deg), t0 + on, du * gate, v,
                jt=jt, jv=jv)
    return t0 + total


# ---------------------------------------------------------------------------
# THE FIGURE (the departure ostinato).  Eight contiguous quavers per 4/4
# bar; broken chord over the local root spanning a tenth, peak on quaver 3.
# HOLES is the post-departure erosion: those quaver indices are simply not
# played (the peak is among them; the root always survives).
# ---------------------------------------------------------------------------

FIGURE_PEAK_INDEX: int = 3
HOLES: frozenset[int] = frozenset({3, 6})


def figure_offsets(minor: bool = True) -> list[int]:
    """Semitone offsets above the chord root for the 8 quavers."""
    tenth = 15 if minor else 16
    return [0, 7, 12, tenth, 12, 7, 12, 7]


def play_figure(sc: en.Score, ch: int, t0: float, root: int,
                minor: bool = True, vel: int = 60,
                vel_end: int | None = None, dur: float = 0.45,
                holes: frozenset[int] = frozenset(),
                jt: int = 0, jv: int = 2) -> float:
    """One bar of the figure at beat t0 (quavers in `holes` omitted);
    returns t0 + 4.0."""
    offs = figure_offsets(minor)
    for i, off in enumerate(offs):
        if i in holes:
            continue
        v = vel
        if vel_end is not None:
            v = round(en.lerp(vel, vel_end, i / 7.0))
        sc.note(ch, root + off, t0 + 0.5 * i, dur, v, jt=jt, jv=jv)
    return t0 + 4.0


# ---------------------------------------------------------------------------
# THE DEPARTED LINE.  (onset, dur, degree) — 12 notes, 16 beats,
# contiguous, stepwise but for one fourth-leap onto the crest (degree 8).
# T1 plays notes [0:INTERRUPT_AFTER] and no more — the interruption lands
# just past the crest, mid-descent; T5 plays all 12 verbatim.
# ---------------------------------------------------------------------------

DEPARTED_LINE: list[tuple[float, float, int]] = [
    (0.0, 2.0, 3), (2.0, 1.0, 4), (3.0, 1.0, 5), (4.0, 2.0, 6),
    (6.0, 1.0, 5), (7.0, 1.0, 8), (8.0, 2.0, 7), (10.0, 1.0, 6),
    (11.0, 1.0, 5), (12.0, 1.5, 4), (13.5, 0.5, 3), (14.0, 2.0, 5),
]
DEPARTED_LEN: float = 16.0
INTERRUPT_AFTER: int = 7


def departed_notes(count: int | None = None) -> list[tuple[float, float, int]]:
    return list(DEPARTED_LINE[:count])


def play_departed(sc: en.Score, ch: int, t0: float, base: int,
                  mode: str = MODE_MINOR, count: int | None = None,
                  vel: int = 78, gate: float = 1.0,
                  jt: int = 0, jv: int = 3) -> float:
    """Play the first `count` notes (None = all 12); returns the end beat
    of the LAST PLAYED note."""
    notes = departed_notes(count)
    for on, du, deg in notes:
        sc.note(ch, en.pitch(base, mode, deg), t0 + on, du * gate, vel,
                jt=jt, jv=jv)
    last_on, last_du, _d = notes[-1]
    return t0 + last_on + last_du


# ---------------------------------------------------------------------------
# THE STATIC LANE.  Standard Morse timing: dit = 1 unit on, dah = 3 on,
# 1 off between symbols, 3 off between letters, 7 off between words.
# ---------------------------------------------------------------------------

MORSE_TABLE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
}

MORSE_TEXT = "REMEMBER US"


def morse_rhythm(text: str, unit: float = 0.25) -> list[tuple[float, float]]:
    """(onset, dur) pairs, in beats, for `text` in standard Morse timing."""
    out: list[tuple[float, float]] = []
    t = 0.0
    for wi, word in enumerate(text.upper().split()):
        if wi:
            t += 7 * unit
        for li, letter in enumerate(word):
            if li:
                t += 3 * unit
            for si, sym in enumerate(MORSE_TABLE[letter]):
                if si:
                    t += unit
                dur = unit if sym == "." else 3 * unit
                out.append((t, dur))
                t += dur
    return out


# ---------------------------------------------------------------------------
# SEATING — the album pan plan.  A track's channels sit at their seat
# (single CC10 at setup; verify.py's check_pan holds CENTERED_CHANNELS to
# 64).  Only an explicitly-named shimmer channel may autopan.
# ---------------------------------------------------------------------------

SEATING: dict[str, int] = {
    "piano": 64, "violin1": 44, "violin2": 54, "viola": 74, "cello": 84,
    "bass": 64, "choir": 64, "celesta": 70, "harp": 48, "bells": 58,
    "timpani": 64, "organ": 64, "pad": 64,
}


# ---------------------------------------------------------------------------
# verify_material — every claim above, proven numerically.
# ---------------------------------------------------------------------------

def _triad_third(mode: str, degree: int) -> int:
    return en.deg_semis(mode, degree + 2) - en.deg_semis(mode, degree)


def verify_material() -> list[str]:
    fails: list[str] = []
    minor_pcs = {s % 12 for s in en.MODES[MODE_MINOR]}
    major_pcs = {s % 12 for s in en.MODES[MODE_MAJOR]}

    # --- the grounds ---
    if [en.deg_semis(MODE_MINOR, d) % 12 for d in GROUND_DEGREES] != \
            [0, 8, 3, 10]:
        fails.append("minor ground roots are not D, Bb, F, C")
    if [en.deg_semis(MODE_MAJOR, d) % 12 for d in MAJOR_GROUND_DEGREES] != \
            [0, 7, 9, 5]:
        fails.append("major ground roots are not D, A, B, G")
    for name, degs, sus, mode, pcs, direction in (
            ("minor", GROUND_DEGREES, SUSPENSIONS, MODE_MINOR, minor_pcs, -1),
            ("major", MAJOR_GROUND_DEGREES, MAJOR_SUSPENSIONS, MODE_MAJOR,
             major_pcs, +1)):
        if len(sus) != len(degs):
            fails.append(f"{name} ground: {len(sus)} suspensions for "
                         f"{len(degs)} chords")
            continue
        for i, (d, (s, r)) in enumerate(zip(degs, sus)):
            third = _triad_third(mode, d)
            step = (r - s) * direction
            if step not in (1, 2):
                fails.append(f"{name} chord {i}: sigh {s}->{r} must "
                             f"{'rise' if direction > 0 else 'fall'} by step")
            if direction < 0 and r not in (0, third):
                fails.append(f"{name} chord {i}: resolution {r} must land "
                             f"on the root or third (third={third})")
            if direction > 0 and r != third:
                fails.append(f"{name} chord {i}: rising sigh must land on "
                             f"the third (third={third}, got {r})")
            root_pc = en.deg_semis(mode, d) % 12
            for off in (s, r):
                if (root_pc + off) % 12 not in pcs:
                    fails.append(f"{name} chord {i}: offset {off} is not "
                                 f"diatonic")

    # --- the theme ---
    degs = [d for _on, _du, d in THEME]
    if degs != [5, 4, 3, 4, 3, 2]:
        fails.append(f"theme contour {degs} != [5,4,3,4,3,2]")
    if 1 in degs:
        fails.append("degree 1 must be absent from the theme (withheld)")
    if degs[-1] != THEME_END_DEG:
        fails.append("theme must end on the waiting tone (degree 2)")
    horizon = 0.0
    for on, du, _d in THEME:
        if abs(on - horizon) > 1e-9:
            fails.append(f"theme not contiguous at beat {on}")
        horizon = on + du
    if horizon != THEME_LEN:
        fails.append(f"theme length {horizon} != {THEME_LEN}")
    if THEME[-1][1] < 2.0:
        fails.append("the waiting tone must be held (>= 2 beats)")
    if ARRIVAL != (THEME_LEN, 4.0, 1):
        fails.append("ARRIVAL must be a held degree-1 at the theme's end")
    if [invert_deg(d) for d in degs] != [1, 2, 3, 2, 3, 4]:
        fails.append("diatonic inversion about degree 3 is wrong")
    for d in (1, 2, 5, 8):
        if invert_deg(invert_deg(d)) != d:
            fails.append(f"invert_deg not an involution at {d}")
    if invert_deg(INVERT_AXIS) != INVERT_AXIS:
        fails.append("inversion must fix its own axis")
    got = theme_notes(stretch=2.0, arrival=True)
    if len(got) != 7 or got[-1][2] != 1 or got[-1][0] != 16.0:
        fails.append("theme_notes(stretch=2, arrival=True) malformed")

    # --- the figure ---
    for minor in (True, False):
        offs = figure_offsets(minor)
        if len(offs) != 8 or offs[0] != 0:
            fails.append("figure must be 8 quavers starting on the root")
        peak = max(offs)
        if peak != (15 if minor else 16):
            fails.append(f"figure span {peak} is not a tenth")
        if offs.index(peak) != FIGURE_PEAK_INDEX or \
                offs.count(peak) != 1:
            fails.append("figure peak must be unique, on quaver 3")
        pcs = minor_pcs if minor else major_pcs
        for off in offs:
            if off % 12 not in pcs:
                fails.append(f"figure offset {off} not diatonic")
    if figure_offsets(True)[:3] != figure_offsets(False)[:3]:
        fails.append("figure quality must only change the tenth")
    if not (HOLES < set(range(8))):
        fails.append("HOLES must be a proper subset of the 8 quavers")
    if len(HOLES) != 2 or FIGURE_PEAK_INDEX not in HOLES or 0 in HOLES:
        fails.append("HOLES must take exactly 2 quavers, including the "
                     "peak, never the root")

    # --- the departed line ---
    if len(DEPARTED_LINE) != 12:
        fails.append(f"departed line has {len(DEPARTED_LINE)} notes, "
                     f"want 12")
    horizon = 0.0
    for on, du, _d in DEPARTED_LINE:
        if abs(on - horizon) > 1e-9:
            fails.append(f"departed line not contiguous at beat {on}")
        horizon = on + du
    if horizon != DEPARTED_LEN:
        fails.append(f"departed line length {horizon} != {DEPARTED_LEN}")
    ddegs = [d for _on, _du, d in DEPARTED_LINE]
    crest = max(ddegs)
    if crest != 8 or ddegs.count(crest) != 1:
        fails.append("departed line needs a unique degree-8 crest")
    leaps = [abs(b - a) for a, b in zip(ddegs, ddegs[1:]) if abs(b - a) > 1]
    if sorted(leaps) != [2, 3]:
        fails.append(f"departed line: want exactly one third and one "
                     f"fourth-leap (got jumps {leaps})")
    if ddegs.index(crest) >= INTERRUPT_AFTER:
        fails.append("the interruption must land AFTER the crest")
    if not 0 < INTERRUPT_AFTER < len(DEPARTED_LINE):
        fails.append("INTERRUPT_AFTER must split the line properly")
    if 1 in ddegs:
        fails.append("degree 1 must be absent from the departed line too")

    # --- morse ---
    for chx in MORSE_TEXT:
        if chx != " " and chx not in MORSE_TABLE:
            fails.append(f"morse: no code for {chx!r}")
    if morse_rhythm("E", 0.25) != [(0.0, 0.25)]:
        fails.append("morse: E must be a single dit")
    if morse_rhythm("T", 0.25) != [(0.0, 0.75)]:
        fails.append("morse: T must be a single dah")
    if len(morse_rhythm(MORSE_TEXT)) != 23:
        fails.append(f"REMEMBER US has {len(morse_rhythm(MORSE_TEXT))} "
                     f"symbols, want 23")

    # --- seating ---
    for name, pan in SEATING.items():
        if not 0 <= pan <= 127:
            fails.append(f"seat {name} pan {pan} out of range")
    s = SEATING
    if not (s["violin1"] < s["violin2"] < 64 < s["viola"] < s["cello"]):
        fails.append("the quartet must be seated left to right")
    for name in ("piano", "bass", "choir", "organ", "timpani", "pad"):
        if s[name] != 64:
            fails.append(f"seat {name} must be centered")

    return fails
