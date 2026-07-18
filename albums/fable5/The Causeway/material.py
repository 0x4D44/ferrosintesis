"""material.py — the shared musical DNA of *The Causeway*.

Everything that recurs across tracks lives HERE as data, and every claim the
album makes about that data is proven numerically by verify_material() —
written BEFORE the music, composed-to-pass (the repo method).  Track modules
import these objects; cross-track recurrences are recomputed from THIS file,
never re-typed.

The through-lines (HLD: "wrk_docs/2026.07.18 - HLD - The Causeway album
(five crossings).md"):

- ISLAND          the ABBA pole: ten notes, 8 beats, repeated-note head,
                  off-beat pushes, stepwise fall, hanging on degree 2.  A
                  passing interior tonic is allowed; ENDING on the tonic is
                  banned in tracks 1-4.
- MAINLAND        the McCartney pole: ten notes, 8 beats, one rising
                  major-sixth leap (its only leap), a sighing fall, settling
                  on degree 6.
- CONVERGENCE     (island tonic, mainland tonic) per track; the pitch-class
                  distance walks 6, 4, 3, 2, 0 across the album.  The themes
                  may never OVERLAP in time until track 5 (T3 escalates to
                  call-and-answer: adjacent within 2 beats, still disjoint).
- FUSION          T5 only: the mainland's leap planted inside the island's
                  incantation, degree 2 demoted to a passing note, landing
                  held on degree 1 — the album's only theme-family tonic
                  ending.
- HOOKS[1..5]     the hook ledger: one transposition-invariant riff cell per
                  track (own track >= 6 statements; T5 III restates 1..4 —
                  the side-two medley).
- MORSE_WORDS     the tide-table: NEAP WAIT TURN EBB HOME, rotating timbre.
- tide_breath()   the shared tempo swell (the water); two pinned still
                  points live in T4 II and T5 II-III.
- SHORE_PANS      the narrowing strait: island channels left, mainland
                  right, seats converging with the keys.
- TOLLS           the bell buoy: track N ends with exactly N tolls.
- VOWEL_CAPS      the winter's mouth: choir CC70 ceiling per track; T5 must
                  REACH >= VOWEL_FLOOR_T5.
- Cadence law     tracks 1-4 cadence modally (iv-i, v-i, bVII-i; leading
                  tone banned); T5 ends IV-I plagal with the Picardy third.
"""

from __future__ import annotations

import math

import engine as en

MODE_MINOR = "aeolian"
MODE_MAJOR = "ionian"

PPQ = en.PPQ


def _pc(name: str) -> int:
    """Pitch-class number of a note name ('Bb' -> 10)."""
    return en.n(f"{name}4") % 12


# ---------------------------------------------------------------------------
# THE TWO SHORE THEMES and THE FUSION PHRASE.
# (onset_beats, dur_beats, mode_degree); 8 beats each, contiguous.
# ---------------------------------------------------------------------------

ISLAND: list[tuple[float, float, int]] = [
    (0.0, 0.5, 5), (0.5, 0.5, 5), (1.0, 1.5, 5), (2.5, 0.5, 4),
    (3.0, 1.0, 3), (4.0, 0.5, 4), (4.5, 0.5, 5), (5.0, 1.0, 3),
    (6.0, 0.5, 1), (6.5, 1.5, 2),
]
ISLAND_LEN: float = 8.0
ISLAND_END_DEG: int = 2          # the hang — never the tonic in T1-T4
ISLAND_FIRST_DEG: int = 5        # implied tonic = first pitch - 7 semis

MAINLAND: list[tuple[float, float, int]] = [
    (0.0, 1.0, 1), (1.0, 1.5, 6), (2.5, 0.5, 5), (3.0, 0.5, 4),
    (3.5, 0.5, 3), (4.0, 1.0, 4), (5.0, 0.5, 3), (5.5, 0.5, 4),
    (6.0, 0.5, 5), (6.5, 1.5, 6),
]
MAINLAND_LEN: float = 8.0
MAINLAND_END_DEG: int = 6        # the settle — the ache unreleased
MAINLAND_FIRST_DEG: int = 1      # implied tonic = first pitch

FUSION: list[tuple[float, float, int]] = [
    (0.0, 1.0, 1), (1.0, 0.5, 6), (1.5, 0.5, 6), (2.0, 1.0, 6),
    (3.0, 1.0, 5), (4.0, 1.0, 4), (5.0, 0.5, 3), (5.5, 0.5, 2),
    (6.0, 2.0, 1),
]
FUSION_LEN: float = 8.0


def theme_cell(theme: list[tuple[float, float, int]],
               mode: str) -> list[tuple[float, float, int]]:
    """(onset, dur, semitones-relative-to-first-note) for a degree table."""
    semis = [en.deg_semis(mode, d) for _on, _du, d in theme]
    return [(on, du, s - semis[0])
            for (on, du, _d), s in zip(theme, semis)]


ISLAND_CELL = None   # filled below, after theme_cell is defined
MAINLAND_CELL = None
FUSION_CELL = None


def _play_degrees(sc: en.Score, ch: int, t0: float, base: int, mode: str,
                  notes: list[tuple[float, float, int]], stretch: float,
                  vel: int, vel_end: int | None, gate: float,
                  jt: int, jv: int) -> float:
    total = max(on + du for on, du, _d in notes) * stretch
    for on, du, deg in notes:
        v = vel
        if vel_end is not None and total > 0:
            v = round(en.lerp(vel, vel_end, (on * stretch) / total))
        sc.note(ch, en.pitch(base, mode, deg), t0 + on * stretch,
                du * stretch * gate, v, jt=jt, jv=jv)
    return t0 + total


def play_island(sc: en.Score, ch: int, t0: float, base: int,
                stretch: float = 1.0, vel: int = 76,
                vel_end: int | None = None, gate: float = 1.0,
                jt: int = 0, jv: int = 3, count: int | None = None) -> float:
    """State the ISLAND theme (aeolian) above tonic pitch `base`; jt=0 so
    every statement is oracle-findable.  `count` limits to a prefix (T4's
    reaching device is MAINLAND-side; island prefixes are for fragments that
    must NOT register as statements — fewer than 10 notes never match)."""
    notes = ISLAND if count is None else ISLAND[:count]
    return _play_degrees(sc, ch, t0, base, MODE_MINOR, notes, stretch,
                         vel, vel_end, gate, jt, jv)


def play_mainland(sc: en.Score, ch: int, t0: float, base: int,
                  stretch: float = 1.0, vel: int = 78,
                  vel_end: int | None = None, gate: float = 1.0,
                  jt: int = 0, jv: int = 3,
                  count: int | None = None) -> float:
    """State the MAINLAND theme (ionian) above tonic pitch `base`.
    T4's reaching statements use count=4, 7, 9."""
    notes = MAINLAND if count is None else MAINLAND[:count]
    return _play_degrees(sc, ch, t0, base, MODE_MAJOR, notes, stretch,
                         vel, vel_end, gate, jt, jv)


def play_fusion(sc: en.Score, ch: int, t0: float, base: int,
                stretch: float = 1.0, vel: int = 80,
                vel_end: int | None = None, gate: float = 1.0,
                jt: int = 0, jv: int = 3) -> float:
    """T5 only: the fusion phrase (ionian), the album's tonic landing."""
    return _play_degrees(sc, ch, t0, base, MODE_MAJOR, FUSION, stretch,
                         vel, vel_end, gate, jt, jv)


# ---------------------------------------------------------------------------
# THE CONVERGENCE.  (island tonic, mainland tonic) pitch-class names per
# track; the distance walks 6, 4, 3, 2, 0.
# ---------------------------------------------------------------------------

CONVERGENCE: dict[int, tuple[str, str]] = {
    1: ("E", "Bb"), 2: ("E", "C"), 3: ("A", "C"), 4: ("A", "G"),
    5: ("D", "D"),
}


def convergence_pcs(track: int) -> tuple[int, int]:
    isl, main = CONVERGENCE[track]
    return _pc(isl), _pc(main)


def pc_distance(a: int, b: int) -> int:
    d = abs(a - b) % 12
    return min(d, 12 - d)


def island_tonic_pc(first_pitch: int) -> int:
    return (first_pitch - en.deg_semis(MODE_MINOR, ISLAND_FIRST_DEG)) % 12


def mainland_tonic_pc(first_pitch: int) -> int:
    return (first_pitch - en.deg_semis(MODE_MAJOR, MAINLAND_FIRST_DEG)) % 12


# ---------------------------------------------------------------------------
# THE HOOK LEDGER.  (onset, dur, semitones-relative-to-first-note); rests
# allowed (cells are not necessarily contiguous), <= 4 beats, 3-6 notes.
# Own track states its hook >= 6 times; T5 III restates HOOKS[1..4].
# ---------------------------------------------------------------------------

HOOKS: dict[int, list[tuple[float, float, int]]] = {
    1: [(0.0, 0.5, 0), (0.5, 0.5, 0), (1.0, 0.5, -2), (1.5, 0.5, -5)],
    2: [(0.0, 0.5, 0), (0.75, 0.25, 3), (1.0, 0.5, 5), (1.5, 0.5, 7),
        (2.5, 0.5, 5), (3.0, 1.0, 3)],
    3: [(0.0, 0.5, 0), (0.5, 0.5, 3), (1.0, 0.5, 7)],
    4: [(0.0, 0.25, 0), (0.25, 0.25, 7), (0.5, 0.25, 14), (0.75, 0.25, 15)],
    5: [(0.0, 1.0, 0), (1.0, 1.0, 2), (2.0, 0.5, 4), (2.5, 1.5, 7)],
}

HOOK_NAMES: dict[int, str] = {
    1: "the heartbeat", 2: "the ferry riff", 3: "the lattice",
    4: "the ice-arp", 5: "the pump call",
}


def play_hook(sc: en.Score, ch: int, t0: float, first_pitch: int, n: int,
              stretch: float = 1.0, vel: int = 82,
              vel_end: int | None = None, gate: float = 0.95,
              jt: int = 0, jv: int = 2) -> float:
    """State HOOKS[n] with its first note on `first_pitch`; returns the end
    beat.  jt=0 ALWAYS — every statement is oracle-findable."""
    cell = HOOKS[n]
    total = max(on + du for on, du, _s in cell) * stretch
    for on, du, semis in cell:
        v = vel
        if vel_end is not None and total > 0:
            v = round(en.lerp(vel, vel_end, (on * stretch) / total))
        sc.note(ch, first_pitch + semis, t0 + on * stretch,
                du * stretch * gate, v, jt=jt, jv=jv)
    return t0 + total


# ---------------------------------------------------------------------------
# STATEMENT SEARCH.  Transposition-invariant, uniform-stretch-invariant
# matching of a cell against a channel's note-on stream.  A statement is a
# CONSECUTIVE run of note-ons whose pitch deltas equal the cell's and whose
# onsets sit at the cell's fractional positions (tolerance FRAC_TOL) —
# which is why statement channels must stay monophonic while stating.
# ---------------------------------------------------------------------------

FRAC_TOL = 0.04


def note_ons(sc: en.Score, ch: int) -> list[tuple[int, int, int]]:
    """Sorted (tick, pitch, vel) note-ons of a channel."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def find_statements(ons: list[tuple[int, int, int]],
                    cell: list[tuple[float, float, int]],
                    ) -> list[tuple[float, int, float]]:
    """All matches of `cell` in a note-on stream.

    Returns [(start_beat, first_pitch, stretch)] where stretch is in beats
    of score time per beat of cell time.  Matches consecutive runs only.
    """
    m = len(cell)
    if m < 2:
        raise ValueError("cell too short")
    rel = [s - cell[0][2] for _on, _du, s in cell]
    span = cell[-1][0] - cell[0][0]
    fracs = [(on - cell[0][0]) / span for on, _du, _s in cell]
    out = []
    for i in range(len(ons) - m + 1):
        run = ons[i:i + m]
        if any(run[k][1] - run[0][1] != rel[k] for k in range(m)):
            continue
        tspan = run[-1][0] - run[0][0]
        if tspan <= 0:
            continue
        if any(abs((run[k][0] - run[0][0]) / tspan - fracs[k]) > FRAC_TOL
               for k in range(m)):
            continue
        out.append((run[0][0] / PPQ, run[0][1], (tspan / PPQ) / span))
    return out


def theme_statements(sc: en.Score, which: str,
                     channels=None) -> list[tuple[int, float, float, int]]:
    """Find every ISLAND / MAINLAND / FUSION statement in a Score.

    Returns [(ch, start_beat, end_beat, first_pitch)]; end_beat covers the
    final note's duration at the detected stretch.
    """
    theme, mode = {
        "island": (ISLAND, MODE_MINOR),
        "mainland": (MAINLAND, MODE_MAJOR),
        "fusion": (FUSION, MODE_MAJOR),
    }[which]
    cell = theme_cell(theme, mode)
    total = max(on + du for on, du, _s in cell)
    out = []
    for ch in sorted(sc.events) if channels is None else sorted(channels):
        for start, first, stretch in find_statements(note_ons(sc, ch), cell):
            out.append((ch, start, start + total * stretch, first))
    return sorted(out, key=lambda s: s[1])


def overlapping_pairs(spans_a, spans_b, eps: float = 1e-6):
    """Pairs from two [(ch, t0, t1, p)] lists that overlap in time."""
    out = []
    for a in spans_a:
        for b in spans_b:
            if a[1] < b[2] - eps and b[1] < a[2] - eps:
                out.append((a, b))
    return out


# ---------------------------------------------------------------------------
# THE MORSE TIDE-TABLE.  Standard timing: dit = 1 unit on, dah = 3 on,
# 1 off between symbols, 3 off between letters, 7 off between words.
# ---------------------------------------------------------------------------

MORSE_TABLE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
}

MORSE_WORDS: dict[int, str] = {
    1: "NEAP", 2: "WAIT", 3: "TURN", 4: "EBB", 5: "HOME",
}

# The rotating timbre: GM program of each track's morse lane (the module
# assigns the channel; ch9 woodblock uses the GM percussion key instead).
MORSE_PROGRAMS: dict[int, int] = {1: 8, 2: 115, 3: 28, 4: 108, 5: 14}


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


def play_morse(sc: en.Score, ch: int, t0: float, track: int, pitch: int,
               unit: float = 0.25, vel: int = 52, gate: float = 0.9) -> float:
    """Tap the track's tide-word once on a single pitch; returns end beat."""
    end = t0
    for on, du in morse_rhythm(MORSE_WORDS[track], unit):
        sc.note(ch, pitch, t0 + on, du * gate, vel, jt=0, jv=2)
        end = t0 + on + du
    return end


# ---------------------------------------------------------------------------
# THE TIDE-BREATH.  The shared tempo swell: a cosine dip of `depth` bpm per
# `period` beats, sampled at quarter-period points.  Deterministic; modules
# build their movement maps from it.  The two pinned still points (T4 II
# exactly one tempo event; T5 II-III wiggle <= 1 bpm) are track law.
# ---------------------------------------------------------------------------

TIDE_DEPTH_RANGE: tuple[float, float] = (3.0, 6.0)


def tide_breath(base_bpm: float, t0: float, t1: float,
                period: float = 32.0, depth: float = 4.0,
                ) -> list[tuple[float, float]]:
    """[(beat, bpm)] swelling base -> base-depth -> base per period."""
    lo, hi = TIDE_DEPTH_RANGE
    if not lo <= depth <= hi:
        raise ValueError(f"tide depth {depth} outside {TIDE_DEPTH_RANGE}")
    out = []
    step = period / 4.0
    i = 0
    while True:
        t = t0 + i * step
        if t >= t1 - 1e-9:
            break
        frac = (i % 4) / 4.0
        bpm = base_bpm - depth * (0.5 - 0.5 * math.cos(2 * math.pi * frac))
        out.append((t, round(bpm, 2)))
        i += 1
    return out


# ---------------------------------------------------------------------------
# THE NARROWING STRAIT, THE TOLLS, THE VOWEL CLOCK.
# ---------------------------------------------------------------------------

SHORE_PANS: dict[int, tuple[int, int]] = {
    1: (40, 88), 2: (44, 84), 3: (50, 78), 4: (54, 74), 5: (60, 68),
}

TOLLS: dict[int, int] = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
TOLL_SPACING: tuple[float, float] = (1.5, 4.0)   # beats between tolls

VOWEL_CAPS: dict[int, int] = {1: 40, 2: 50, 3: 75, 4: 55, 5: 127}
VOWEL_FLOOR_T5: int = 80


def play_tolls(sc: en.Score, ch: int, t0: float, track: int, pitch: int,
               spacing: float = 2.5, widen: float = 0.0, vel: int = 74,
               dur: float = 3.5) -> float:
    """The bell buoy: exactly TOLLS[track] strikes; returns the last onset."""
    lo, hi = TOLL_SPACING
    t = t0
    last = t0
    for i in range(TOLLS[track]):
        sc.note(ch, pitch, t, dur, max(30, vel - 4 * i), jt=0, jv=2)
        last = t
        gap = spacing + widen * i
        if not lo - 1e-9 <= gap <= hi + 1e-9:
            raise ValueError(f"toll gap {gap} outside {TOLL_SPACING}")
        t += gap
    return last


# ---------------------------------------------------------------------------
# THE WITHHELD CADENCE.  Tracks 1-4 cadence modally: the bass approaches
# the tonic downbeat from iv, v or bVII (pc offsets 5, 7, 10) and the
# leading tone is BANNED across the cadence window on every channel.
# T5's final cadence is IV-I plagal with the Picardy third — checked by
# T5's own oracle.
# ---------------------------------------------------------------------------

ALLOWED_APPROACH_OFFSETS: frozenset[int] = frozenset({5, 7, 10})
LEADING_TONE_BANNED_TRACKS: frozenset[int] = frozenset({1, 2, 3, 4})


def cadence_failures(sc: en.Score, bass_ch: int, lo: float, hi: float,
                     downbeat: float, tonic_pc: int) -> list[str]:
    """Check one cadence window [lo, hi] resolving at `downbeat`:
    the bass lands on the tonic pc at the downbeat (+-0.1 beat), its last
    prior note is an allowed modal approach, and NO channel sounds the
    leading tone (tonic-1 pc) anywhere inside the window."""
    fails = []
    ons = note_ons(sc, bass_ch)
    landing = [p for t, p, _v in ons
               if abs(t / PPQ - downbeat) <= 0.1]
    if not landing or all(p % 12 != tonic_pc for p in landing):
        fails.append(f"cadence at {downbeat}: bass does not land on "
                     f"pc {tonic_pc}")
    prior = [p for t, p, _v in ons if lo - 1e-6 <= t / PPQ < downbeat - 0.1]
    if prior:
        approach = (prior[-1] % 12 - tonic_pc) % 12
        if approach not in ALLOWED_APPROACH_OFFSETS | {0}:
            fails.append(f"cadence at {downbeat}: bass approach pc offset "
                         f"{approach} not modal (want iv/v/bVII/tonic)")
    else:
        fails.append(f"cadence at {downbeat}: no bass approach in window")
    leading = (tonic_pc - 1) % 12
    for ch in sorted(sc.events):
        if ch == 9:
            continue        # GM drum KEYS are not pitch classes
        for t, p, _v in note_ons(sc, ch):
            if lo - 1e-6 <= t / PPQ <= hi + 1e-6 and p % 12 == leading:
                fails.append(f"cadence window [{lo},{hi}]: leading tone "
                             f"pc {leading} on ch{ch} at beat {t / PPQ:.2f}")
                break
    return fails


# ---------------------------------------------------------------------------
# verify_material — every claim above, proven numerically.
# ---------------------------------------------------------------------------

def _contiguous(notes, want_len):
    fails = []
    horizon = 0.0
    for on, du, _d in notes:
        if abs(on - horizon) > 1e-9:
            fails.append(f"not contiguous at beat {on}")
        horizon = on + du
    if abs(horizon - want_len) > 1e-9:
        fails.append(f"length {horizon} != {want_len}")
    return fails


def verify_material() -> list[str]:
    fails: list[str] = []
    global ISLAND_CELL, MAINLAND_CELL, FUSION_CELL
    ISLAND_CELL = theme_cell(ISLAND, MODE_MINOR)
    MAINLAND_CELL = theme_cell(MAINLAND, MODE_MAJOR)
    FUSION_CELL = theme_cell(FUSION, MODE_MAJOR)

    # --- the island theme ---
    degs = [d for _on, _du, d in ISLAND]
    if len(ISLAND) != 10:
        fails.append("island: want 10 notes")
    fails += [f"island: {m}" for m in _contiguous(ISLAND, ISLAND_LEN)]
    if degs[:3] != [5, 5, 5]:
        fails.append("island: the incantation head must repeat degree 5 x3")
    if degs[-1] != ISLAND_END_DEG:
        fails.append("island: must hang on degree 2")
    if ISLAND[-1][1] < 1.5:
        fails.append("island: the hang must be held (>= 1.5 beats)")
    if max(abs(b - a) for a, b in zip(degs, degs[1:])) > 2:
        fails.append("island: no leap larger than a third")
    if not any(abs(on % 1.0 - 0.5) < 1e-9 for on, _du, _d in ISLAND):
        fails.append("island: needs off-beat pushes")

    # --- the mainland theme ---
    mdegs = [d for _on, _du, d in MAINLAND]
    if len(MAINLAND) != 10:
        fails.append("mainland: want 10 notes")
    fails += [f"mainland: {m}" for m in _contiguous(MAINLAND, MAINLAND_LEN)]
    leaps = [(a, b) for a, b in zip(mdegs, mdegs[1:]) if abs(b - a) > 1]
    if len(leaps) != 1 or leaps[0] != (1, 6):
        fails.append(f"mainland: want exactly one leap, 1->6 (got {leaps})")
    leap_semis = en.deg_semis(MODE_MAJOR, 6) - en.deg_semis(MODE_MAJOR, 1)
    if leap_semis != 9:
        fails.append("mainland: the leap must be a major sixth")
    if mdegs[-1] != MAINLAND_END_DEG:
        fails.append("mainland: must settle on degree 6")
    if MAINLAND[-1][1] < 1.5:
        fails.append("mainland: the settle must be held (>= 1.5 beats)")
    if 7 in mdegs:
        fails.append("mainland: the leading tone is not in the tune")

    # --- the fusion phrase ---
    fdegs = [d for _on, _du, d in FUSION]
    if len(FUSION) != 9:
        fails.append("fusion: want 9 notes")
    fails += [f"fusion: {m}" for m in _contiguous(FUSION, FUSION_LEN)]
    if (fdegs[0], fdegs[1]) != (1, 6):
        fails.append("fusion: must open with the mainland leap 1->6")
    if fdegs[1:4] != [6, 6, 6]:
        fails.append("fusion: must carry the island incantation (6 x3)")
    if fdegs[3:] != [6, 5, 4, 3, 2, 1]:
        fails.append("fusion: must fall stepwise to the tonic")
    if fdegs[-1] != 1 or FUSION[-1][1] < 2.0:
        fails.append("fusion: must LAND on degree 1, held >= 2 beats")
    if fdegs.count(1) != 2:
        fails.append("fusion: degree 1 exactly at the ends")

    # --- convergence ---
    want = [6, 4, 3, 2, 0]
    got = [pc_distance(*convergence_pcs(t)) for t in (1, 2, 3, 4, 5)]
    if got != want:
        fails.append(f"convergence distances {got} != {want}")
    if CONVERGENCE[5] != ("D", "D"):
        fails.append("track 5 must converge on D")
    if island_tonic_pc(en.n("B4")) != _pc("E"):
        fails.append("island tonic inference broken (B start -> E minor)")
    if mainland_tonic_pc(en.n("C4")) != _pc("C"):
        fails.append("mainland tonic inference broken")

    # --- the hook ledger ---
    for n, cell in sorted(HOOKS.items()):
        if not 3 <= len(cell) <= 6:
            fails.append(f"hook {n}: want 3-6 notes")
        if cell[0][0] != 0.0 or cell[0][2] != 0:
            fails.append(f"hook {n}: must start at (0, .., 0)")
        span = max(on + du for on, du, _s in cell)
        if span > 4.0:
            fails.append(f"hook {n}: cell longer than a bar ({span})")
        if any(b[0] <= a[0] for a, b in zip(cell, cell[1:])):
            fails.append(f"hook {n}: onsets must strictly rise")
    if not (HOOKS[1][-1][2] < 0 <= HOOKS[5][-1][2]):
        fails.append("hook 1 must fall; hook 5 must rise")
    if HOOKS[5][-1][2] != 7 or [s for _o, _d, s in HOOKS[5]] != [0, 2, 4, 7]:
        fails.append("hook 5 must climb 1-2-3-5")
    if max(s for _o, _d, s in HOOKS[4]) != 15:
        fails.append("hook 4 needs its minor-9th glint (span 15)")
    if not any(abs(on - 0.75) < 1e-9 for on, _du, _s in HOOKS[2]):
        fails.append("hook 2 needs its and-of-1 syncopation (onset 0.75)")
    if len(HOOKS[3]) != 3:
        fails.append("hook 3 is the 3-quaver lattice cell")

    # --- statement search: round-trips and no-false-positive claims ---
    sc = en.Score(1)
    play_island(sc, 0, 8.0, en.n("E4"))
    play_mainland(sc, 1, 24.0, en.n("C4"))
    play_fusion(sc, 2, 40.0, en.n("D4"))
    for n in HOOKS:
        play_hook(sc, 3, 56.0 + 8.0 * n, en.n("A4"), n)
    isl = theme_statements(sc, "island")
    if len(isl) != 1 or isl[0][0] != 0 or abs(isl[0][1] - 8.0) > 1e-6:
        fails.append(f"island round-trip failed ({isl})")
    elif island_tonic_pc(isl[0][3]) != _pc("E"):
        fails.append("island round-trip tonic wrong")
    mnl = theme_statements(sc, "mainland")
    if len(mnl) != 1 or mnl[0][0] != 1:
        fails.append(f"mainland round-trip failed ({mnl})")
    elif mainland_tonic_pc(mnl[0][3]) != _pc("C"):
        fails.append("mainland round-trip tonic wrong")
    fus = theme_statements(sc, "fusion")
    if len(fus) != 1 or fus[0][0] != 2:
        fails.append(f"fusion round-trip failed ({fus})")
    for n in HOOKS:
        hits = [(ch, s) for ch in sorted(sc.events)
                for s in find_statements(note_ons(sc, ch), HOOKS[n])]
        own = [(ch, s) for ch, s in hits if ch == 3]
        if len(own) != 1:
            fails.append(f"hook {n} round-trip failed ({len(own)} hits)")
        if any(ch in (0, 1, 2) for ch, _s in hits):
            fails.append(f"hook {n} false-positives inside a theme")
    # An augmented statement still registers (stretch invariance).
    sc2 = en.Score(2)
    play_island(sc2, 0, 0.0, en.n("A4"), stretch=2.0)
    aug = theme_statements(sc2, "island")
    if len(aug) != 1 or abs(aug[0][2] - 16.0) > 1e-6:
        fails.append("augmented island statement not found")
    # A 9-note island prefix must NOT register.
    sc3 = en.Score(3)
    play_island(sc3, 0, 0.0, en.n("E4"), count=9)
    if theme_statements(sc3, "island"):
        fails.append("a 9-note island prefix must not match")

    # --- overlap machinery ---
    a = [(0, 0.0, 8.0, 60)]
    b = [(1, 7.9, 15.9, 60)]
    c = [(1, 8.1, 16.1, 60)]
    if not overlapping_pairs(a, b):
        fails.append("overlapping_pairs misses a real overlap")
    if overlapping_pairs(a, c):
        fails.append("overlapping_pairs false-positive on disjoint spans")

    # --- morse ---
    for track, word in sorted(MORSE_WORDS.items()):
        for chx in word:
            if chx not in MORSE_TABLE:
                fails.append(f"morse: no code for {chx!r}")
    if morse_rhythm("E", 0.25) != [(0.0, 0.25)]:
        fails.append("morse: E must be a single dit")
    if morse_rhythm("T", 0.25) != [(0.0, 0.75)]:
        fails.append("morse: T must be a single dah")
    counts = {t: len(morse_rhythm(w)) for t, w in MORSE_WORDS.items()}
    if counts != {1: 9, 2: 8, 3: 9, 4: 9, 5: 10}:
        fails.append(f"morse symbol counts drifted: {counts}")
    if sorted(MORSE_PROGRAMS) != [1, 2, 3, 4, 5] or \
            len(set(MORSE_PROGRAMS.values())) != 5:
        fails.append("the morse timbre must rotate (5 distinct programs)")

    # --- tide breath ---
    tb = tide_breath(76.0, 0.0, 64.0, period=32.0, depth=4.0)
    if len(tb) != 8 or tb[0] != (0.0, 76.0):
        fails.append("tide_breath: want 8 events over two periods")
    vals = sorted({bpm for _t, bpm in tb})
    if len(vals) < 3 or abs((vals[-1] - vals[0]) - 4.0) > 1e-6:
        fails.append("tide_breath: swell depth wrong")
    if tb != tide_breath(76.0, 0.0, 64.0, period=32.0, depth=4.0):
        fails.append("tide_breath must be deterministic")

    # --- the narrowing strait ---
    widths = []
    for t in (1, 2, 3, 4, 5):
        isl_pan, main_pan = SHORE_PANS[t]
        if not 0 <= isl_pan < 64 < main_pan <= 127:
            fails.append(f"track {t}: island must sit left, mainland right")
        widths.append(main_pan - isl_pan)
    if widths != sorted(widths, reverse=True) or len(set(widths)) != 5:
        fails.append("the strait must strictly narrow across the album")

    # --- the tolls ---
    if TOLLS != {n: n for n in range(1, 6)}:
        fails.append("track N must toll N times")
    sc4 = en.Score(4)
    if abs(play_tolls(sc4, 0, 10.0, 3, 62) - 15.0) > 1e-9 or \
            len(note_ons(sc4, 0)) != 3:
        fails.append("play_tolls emits the wrong bell count/spacing")

    # --- the vowel clock ---
    if sorted(VOWEL_CAPS) != [1, 2, 3, 4, 5]:
        fails.append("vowel caps must cover all five tracks")
    if not (VOWEL_CAPS[1] < VOWEL_CAPS[2] <= VOWEL_CAPS[3] and
            VOWEL_CAPS[4] < VOWEL_CAPS[3] <= VOWEL_CAPS[5]):
        fails.append("vowel clock shape: rise to T3, dip at T4, open at T5")
    if VOWEL_FLOOR_T5 <= VOWEL_CAPS[4]:
        fails.append("T5 must open beyond T4's ceiling")

    # --- cadence law ---
    if ALLOWED_APPROACH_OFFSETS != {5, 7, 10}:
        fails.append("modal approaches are iv, v, bVII only")
    if LEADING_TONE_BANNED_TRACKS != {1, 2, 3, 4}:
        fails.append("the leading tone is banned exactly in tracks 1-4")
    sc5 = en.Score(5)
    sc5.note(0, en.n("A2"), 0.0, 1.0, 70, jt=0)     # v of D
    sc5.note(0, en.n("D2"), 1.0, 2.0, 70, jt=0)     # lands the tonic
    if cadence_failures(sc5, 0, 0.0, 3.0, 1.0, _pc("D")):
        fails.append("cadence_failures rejects a legal v-i")
    sc6 = en.Score(6)
    sc6.note(0, en.n("A2"), 0.0, 1.0, 70, jt=0)
    sc6.note(0, en.n("D2"), 1.0, 2.0, 70, jt=0)
    sc6.note(1, en.n("C#4"), 0.5, 0.5, 70, jt=0)    # the banned leading tone
    if not cadence_failures(sc6, 0, 0.0, 3.0, 1.0, _pc("D")):
        fails.append("cadence_failures misses a leading tone")

    return fails
