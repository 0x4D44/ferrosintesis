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

ACT TWO (tracks 6-10 — HLD addendum "wrk_docs/2026.07.19 - HLD - The
Causeway act two (five more crossings).md"): the tide returns, the strait
re-opens, but the voices never part again.  Distance 0 on every Act Two
track; overlap REQUIRED, not banned; the leading-tone ban stays scoped to
1-4 and tracks 6/7/9/10 end on the plagal signature (T8 is pinned
unresolved).  All new material grows from THE FUSION PHRASE:

- HOOKS[6..10]    derived from FUSION (per-hook predicates, proven below);
                  hooks 6 and 7 are literal sub-patterns, so Act Two
                  density/medley counts use hook_statements_unnested().
- FUSION_RETRO    the road home — the exact retrograde.  T6-T9 each state
                  only their pinned REACH prefix (RETRO_REACH: 3, 5, 6, 8
                  notes, never further); T10 walks it whole, once, right
                  after a forward statement (the palindrome).
- ISLAND in major play_island(major=True) — banned until T10 (the ice
                  melts last; it still hangs on degree 2).
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


def _retrograde(notes: list[tuple[float, float, int]]
                ) -> list[tuple[float, float, int]]:
    """Exact time-mirror of a contiguous (onset, dur, degree) phrase."""
    total = max(on + du for on, du, _d in notes)
    out = sorted((total - (on + du), du, d) for on, du, d in notes)
    return [(round(on, 6), du, d) for on, du, d in out]


# THE ROAD HOME (Act Two): the fusion phrase walked backward — the held
# tonic, the scale climb, the incantation, home.  T6-T9 state only their
# pinned REACH prefix of it; T10 states it whole, exactly once.
FUSION_RETRO: list[tuple[float, float, int]] = _retrograde(FUSION)
RETRO_REACH: dict[int, int] = {6: 3, 7: 5, 8: 6, 9: 8}


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
                jt: int = 0, jv: int = 3, count: int | None = None,
                major: bool = False) -> float:
    """State the ISLAND theme above tonic pitch `base`; jt=0 so every
    statement is oracle-findable.  `count` limits to a prefix (fragments
    that must NOT register — fewer than 10 notes never match).
    `major=True` is THE MELTING (ionian; still hangs on degree 2) —
    searchable as "island_major", banned before T10."""
    notes = ISLAND if count is None else ISLAND[:count]
    mode = MODE_MAJOR if major else MODE_MINOR
    return _play_degrees(sc, ch, t0, base, mode, notes, stretch,
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
                jt: int = 0, jv: int = 3, retro: bool = False,
                count: int | None = None) -> float:
    """The fusion phrase (ionian).  Act One: forward, T5's landing.
    Act Two: every track states it >= 1; `retro=True` is THE ROAD HOME
    (searchable as "fusion_retro" — T10 only, exactly once), and
    `retro=True, count=N` is the REACH (T6-T9's pinned prefixes — a
    count < 9 never matches the full retro cell)."""
    notes = FUSION_RETRO if retro else FUSION
    if count is not None:
        notes = notes[:count]
        base_on = notes[0][0]
        notes = [(on - base_on, du, d) for on, du, d in notes]
    return _play_degrees(sc, ch, t0, base, MODE_MAJOR, notes, stretch,
                         vel, vel_end, gate, jt, jv)


def retro_prefix_cell(count: int) -> list[tuple[float, float, int]]:
    """The REACH search cell: the first `count` notes of FUSION_RETRO as a
    (onset, dur, rel-semis) cell for find_statements."""
    if not 2 <= count <= len(FUSION_RETRO):
        raise ValueError(f"retro prefix count {count} out of range")
    return theme_cell(FUSION_RETRO[:count], MODE_MAJOR)


# ---------------------------------------------------------------------------
# THE CONVERGENCE.  (island tonic, mainland tonic) pitch-class names per
# track; the distance walks 6, 4, 3, 2, 0.
# ---------------------------------------------------------------------------

CONVERGENCE: dict[int, tuple[str, str]] = {
    1: ("E", "Bb"), 2: ("E", "C"), 3: ("A", "C"), 4: ("A", "G"),
    5: ("D", "D"),
    # Act Two: distance 0 everywhere — the pair travels TOGETHER through
    # D's plagal neighbourhood and comes home to leave.
    6: ("G", "G"), 7: ("C", "C"), 8: ("D", "D"), 9: ("F", "F"),
    10: ("D", "D"),
}
ACT_ONE: tuple[int, ...] = (1, 2, 3, 4, 5)
ACT_TWO: tuple[int, ...] = (6, 7, 8, 9, 10)


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
    # Act Two: every cell derived from THE FUSION PHRASE (per-hook
    # predicates, proven in verify_material).  6 and 7 are literal
    # sub-patterns of the forward fusion (interval + onset fractions);
    # 8 is the pitch-retrograde of its head (own rhythm); 9 is the pitch
    # head of FUSION_RETRO (own rhythm, searcher-disjoint from the retro,
    # the mainland's 4-5-6 run and the island's 3-4-5 run); 10 is the
    # frame (first note, crest, last note lifted an octave).
    6: [(0.0, 1.0, 0), (1.0, 0.5, 9), (1.5, 0.5, 9), (2.0, 1.0, 9)],
    7: [(0.0, 1.0, 0), (1.0, 1.0, -2), (2.0, 0.5, -3), (2.5, 0.5, -5),
        (3.0, 1.0, -7)],
    8: [(0.0, 0.5, 0), (0.5, 0.5, 0), (1.0, 0.5, 0), (1.5, 1.5, -9)],
    9: [(0.0, 0.5, 0), (0.5, 1.5, 2), (2.0, 2.0, 4)],
    10: [(0.0, 1.0, 0), (1.0, 1.5, 9), (2.5, 1.5, 12)],
}

HOOK_NAMES: dict[int, str] = {
    1: "the heartbeat", 2: "the ferry riff", 3: "the lattice",
    4: "the ice-arp", 5: "the pump call",
    6: "the flood bell", 7: "the noon fall", 8: "the gale riff",
    9: "the road-home head", 10: "the sail",
}

# Hooks that are literal sub-patterns of the forward fusion phrase: every
# fusion statement auto-registers them once each, so Act Two density and
# medley oracles count via hook_statements_unnested(), never raw
# find_statements.
FUSION_EMBEDDED_HOOKS: frozenset[int] = frozenset({6, 7})


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
        "island_major": (ISLAND, MODE_MAJOR),
        "mainland": (MAINLAND, MODE_MAJOR),
        "fusion": (FUSION, MODE_MAJOR),
        "fusion_retro": (FUSION_RETRO, MODE_MAJOR),
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


def hook_statements_unnested(sc: en.Score, n: int
                             ) -> list[tuple[int, float, float, int]]:
    """HOOKS[n] hits NOT time-nested inside a same-channel fusion-family
    statement (forward or retro).  Act Two's hooks 6/7 are literal
    sub-patterns of the fusion phrase, so raw find_statements counts every
    fusion statement too — density and medley oracles use THIS."""
    spans = (theme_statements(sc, "fusion") +
             theme_statements(sc, "fusion_retro"))
    cell = HOOKS[n]
    total = max(on + du for on, du, _s in cell)
    out = []
    for ch in sorted(sc.events):
        for start, first, stretch in find_statements(note_ons(sc, ch), cell):
            end = start + total * stretch
            if any(s[0] == ch and s[1] - 1e-6 <= start and
                   end <= s[2] + 1e-6 for s in spans):
                continue
            out.append((ch, start, end, first))
    return sorted(out, key=lambda s: s[1])


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
    6: "FLOOD", 7: "NOON", 8: "GALE", 9: "WANE", 10: "SAIL",
}

# The rotating timbre: GM program of each track's morse lane (the module
# assigns the channel; ch9 woodblock uses the GM percussion key instead).
# Ten distinct programs across the album; T8's GALE is thunder on timpani.
MORSE_PROGRAMS: dict[int, int] = {
    1: 8, 2: 115, 3: 28, 4: 108, 5: 14,
    6: 11, 7: 114, 8: 47, 9: 10, 10: 9,
}


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
    # Act Two: the tide re-opens the strait (widest at the gale, never as
    # wide as the first winter); T10 = the one boat — the two
    # THEME-CARRYING channels share the centre seat, accompaniment gets a
    # symmetric seating plan pinned in the module.
    6: (56, 72), 7: (54, 74), 8: (42, 86), 9: (46, 82), 10: (64, 64),
}

TOLLS: dict[int, int] = {n: n for n in range(1, 11)}
TOLL_SPACING: tuple[float, float] = (1.5, 4.0)   # beats between tolls

VOWEL_CAPS: dict[int, int] = {
    1: 40, 2: 50, 3: 75, 4: 55, 5: 127,
    6: 90, 7: 95, 8: 45, 9: 70, 10: 127,
}
VOWEL_FLOOR_T5: int = 80
VOWEL_FLOOR_T10: int = 100   # the album's fullest voice, machine-comparable

# Act Two cadence law: plagal finals on 6/7/9/10; T8 is pinned UNRESOLVED
# (final bass on the iv, no tonic landing outside the bell-buoy channel).
ACT2_PLAGAL_TRACKS: frozenset[int] = frozenset({6, 7, 9, 10})


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
        if i < TOLLS[track] - 1:      # no phantom gap after the last strike
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


def plagal_final_failures(sc: en.Score, bass_ch: int, downbeat: float,
                          tonic_pc: int, window: float = 8.0) -> list[str]:
    """Act Two's final-cadence law (tracks 6/7/9/10): the bass lands the
    tonic pc at `downbeat` (+-0.1 beat) and its LAST prior note within
    `window` beats is pc offset 5 EXACTLY (the IV).  Deliberately NOT
    built on cadence_failures: no leading-tone ban (Act Two lifted it),
    and no {0, 7, 10} approach tolerance (a v-i or bVII-i final must not
    pass a plagal oracle)."""
    fails = []
    ons = note_ons(sc, bass_ch)
    landing = [p for t, p, _v in ons if abs(t / PPQ - downbeat) <= 0.1]
    if not landing or all(p % 12 != tonic_pc for p in landing):
        fails.append(f"plagal final at {downbeat}: bass does not land "
                     f"pc {tonic_pc}")
    prior = [p for t, p, _v in ons
             if downbeat - window <= t / PPQ < downbeat - 0.1]
    if not prior:
        fails.append(f"plagal final at {downbeat}: no bass approach in "
                     f"the window")
    elif (prior[-1] % 12 - tonic_pc) % 12 != 5:
        fails.append(f"plagal final at {downbeat}: approach pc offset "
                     f"{(prior[-1] % 12 - tonic_pc) % 12} != 5 (the IV)")
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
    got = [pc_distance(*convergence_pcs(t)) for t in ACT_ONE]
    if got != want:
        fails.append(f"act-one convergence distances {got} != {want}")
    if CONVERGENCE[5] != ("D", "D"):
        fails.append("track 5 must converge on D")
    # Act Two: distance 0 everywhere; the pair walks D's plagal
    # neighbourhood and comes home to leave.
    if any(pc_distance(*convergence_pcs(t)) != 0 for t in ACT_TWO):
        fails.append("act-two tracks must keep distance 0")
    if [convergence_pcs(t)[0] for t in ACT_TWO] != [7, 0, 2, 5, 2]:
        fails.append("act-two walk must be G, C, D, F, D")
    if CONVERGENCE[10] != ("D", "D"):
        fails.append("track 10 must leave from D")
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

    # --- Act Two hook derivations (per-hook predicates, as data) ---
    fus_rel = [s - FUSION_CELL[0][2] for _o, _d, s in FUSION_CELL]
    fus_on = [o for o, _d, _s in FUSION_CELL]
    h = {n: ([o for o, _d, _s in HOOKS[n]],
             [s for _o, _d, s in HOOKS[n]]) for n in (6, 7, 8, 9, 10)}
    if h[6][1] != fus_rel[0:4] or h[6][0] != fus_on[0:4]:
        fails.append("hook 6 must be fusion[0:4] verbatim (rels + onsets)")
    want7 = [s - fus_rel[4] for s in fus_rel[4:9]]
    won7 = [o - fus_on[4] for o in fus_on[4:9]]
    if h[7][1] != want7 or h[7][0] != won7:
        fails.append("hook 7 must be fusion[4:9] (rels + onsets)")
    rev = list(reversed(fus_rel[0:4]))
    if h[8][1] != [s - rev[0] for s in rev]:
        fails.append("hook 8 must be the pitch-retrograde of fusion[0:4]")
    retro_cell = theme_cell(FUSION_RETRO, MODE_MAJOR)
    retro_rel = [s - retro_cell[0][2] for _o, _d, s in retro_cell]
    if h[9][1] != retro_rel[0:3]:
        fails.append("hook 9 must be the road-home head (retro rels 0:3)")
    if h[9][0] == [o - retro_cell[0][0] for o, _d, _s in retro_cell[0:3]]:
        fails.append("hook 9's rhythm must DIFFER from the retro head "
                     "(searcher-disjointness is the design)")
    if h[10][1] != [fus_rel[0], max(fus_rel), fus_rel[-1] + 12]:
        fails.append("hook 10 must frame fusion: first, crest, last + 12")

    # --- the retrograde and the reach ---
    rdegs = [d for _on, _du, d in FUSION_RETRO]
    fails += [f"retro: {m}" for m in _contiguous(FUSION_RETRO, FUSION_LEN)]
    if rdegs != [1, 2, 3, 4, 5, 6, 6, 6, 1]:
        fails.append(f"retro degrees {rdegs} wrong")
    if FUSION_RETRO[0] != (0.0, 2.0, 1):
        fails.append("retro must open on the held tonic")
    if sorted(RETRO_REACH) != [6, 7, 8, 9]:
        fails.append("the reach covers tracks 6-9")
    reach_counts = [RETRO_REACH[t] for t in (6, 7, 8, 9)]
    if reach_counts != sorted(set(reach_counts)) or \
            any(not 2 <= c < len(FUSION_RETRO) for c in reach_counts):
        fails.append("the reach must strictly grow and never complete")

    # --- statement search: round-trips and the expected-match matrix ---
    # ch0 island · ch1 mainland · ch2 fusion · ch3 all hooks · ch4 retro ·
    # ch5 island-major · ch6 the longest reach prefix (8 notes).
    sc = en.Score(1)
    play_island(sc, 0, 8.0, en.n("E4"))
    play_mainland(sc, 1, 24.0, en.n("C4"))
    play_fusion(sc, 2, 40.0, en.n("D4"))
    for n in HOOKS:
        play_hook(sc, 3, 56.0 + 8.0 * n, en.n("A4"), n)
    play_fusion(sc, 4, 152.0, en.n("D4"), retro=True)
    play_island(sc, 5, 168.0, en.n("D4"), major=True)
    play_fusion(sc, 6, 184.0, en.n("D4"), retro=True, count=8)
    for which, ch, tonic in (("island", 0, "E"), ("mainland", 1, "C"),
                             ("fusion", 2, "D"), ("fusion_retro", 4, "D"),
                             ("island_major", 5, "D")):
        got = theme_statements(sc, which)
        if [g[0] for g in got] != [ch]:
            fails.append(f"{which} round-trip failed ({got})")
        elif which.startswith("island") and \
                island_tonic_pc(got[0][3]) != _pc(tonic):
            fails.append(f"{which} round-trip tonic wrong")
        elif which == "mainland" and \
                mainland_tonic_pc(got[0][3]) != _pc(tonic):
            fails.append("mainland round-trip tonic wrong")
    # The expected hook-match matrix: exactly one own-channel hit each;
    # hooks 6/7 REQUIRED exactly once inside the forward fusion (the
    # derivation proof); nothing matches inside island / mainland / retro /
    # island-major (8 and 9 are rhythm-saved — that is pinned here).
    for n in HOOKS:
        by_ch: dict[int, int] = {}
        for ch in sorted(sc.events):
            hit = find_statements(note_ons(sc, ch), HOOKS[n])
            if hit:
                by_ch[ch] = len(hit)
        want_fus = 1 if n in FUSION_EMBEDDED_HOOKS else 0
        if by_ch.get(3, 0) != 1:
            fails.append(f"hook {n} round-trip failed ({by_ch})")
        if by_ch.get(2, 0) != want_fus:
            fails.append(f"hook {n}: {by_ch.get(2, 0)} fusion matches, "
                         f"want {want_fus}")
        if any(by_ch.get(ch, 0) for ch in (0, 1, 4, 5)):
            fails.append(f"hook {n} false-positives ({by_ch})")
    # The reach: the pinned prefixes register, and no prefix emission can
    # ever satisfy the full road home.
    if len(find_statements(note_ons(sc, 6), retro_prefix_cell(8))) != 1:
        fails.append("reach round-trip failed (8-prefix not found)")
    if theme_statements(sc, "fusion_retro") and \
            any(g[0] == 6 for g in theme_statements(sc, "fusion_retro")):
        fails.append("a reach prefix must never satisfy the full retro")
    if any(len(find_statements(note_ons(sc, 2), retro_prefix_cell(c)))
           for c in sorted(set(RETRO_REACH.values()))):
        fails.append("reach prefixes must not match inside forward fusion")
    # hook_statements_unnested: the fusion-embedded hooks vanish inside a
    # fusion statement and survive standalone.
    for n in sorted(FUSION_EMBEDDED_HOOKS):
        raw = sum(len(find_statements(note_ons(sc, ch), HOOKS[n]))
                  for ch in sorted(sc.events))
        unn = hook_statements_unnested(sc, n)
        if raw != 2 or len(unn) != 1 or unn[0][0] != 3:
            fails.append(f"unnested filter wrong for hook {n} "
                         f"(raw {raw}, unnested {len(unn)})")
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
    if counts != {1: 9, 2: 8, 3: 9, 4: 9, 5: 10,
                  6: 17, 7: 10, 8: 10, 9: 8, 10: 11}:
        fails.append(f"morse symbol counts drifted: {counts}")
    if sorted(MORSE_PROGRAMS) != list(range(1, 11)) or \
            len(set(MORSE_PROGRAMS.values())) != 10:
        fails.append("the morse timbre must rotate (10 distinct programs)")

    # --- tide breath ---
    tb = tide_breath(76.0, 0.0, 64.0, period=32.0, depth=4.0)
    if len(tb) != 8 or tb[0] != (0.0, 76.0):
        fails.append("tide_breath: want 8 events over two periods")
    vals = sorted({bpm for _t, bpm in tb})
    if len(vals) < 3 or abs((vals[-1] - vals[0]) - 4.0) > 1e-6:
        fails.append("tide_breath: swell depth wrong")
    if tb != tide_breath(76.0, 0.0, 64.0, period=32.0, depth=4.0):
        fails.append("tide_breath must be deterministic")

    # --- the narrowing strait (Act One) ---
    widths = []
    for t in ACT_ONE:
        isl_pan, main_pan = SHORE_PANS[t]
        if not 0 <= isl_pan < 64 < main_pan <= 127:
            fails.append(f"track {t}: island must sit left, mainland right")
        widths.append(main_pan - isl_pan)
    if widths != sorted(widths, reverse=True) or len(set(widths)) != 5:
        fails.append("the strait must strictly narrow across Act One")

    # --- the re-opening strait (Act Two) and the one boat ---
    w2 = []
    for t in (6, 7, 8, 9):
        isl_pan, main_pan = SHORE_PANS[t]
        if not 0 <= isl_pan < 64 < main_pan <= 127:
            fails.append(f"track {t}: island left, mainland right")
        w2.append(main_pan - isl_pan)
    if w2 != [16, 20, 44, 36]:
        fails.append(f"act-two widths {w2} != [16, 20, 44, 36]")
    if max(w2) != SHORE_PANS[8][1] - SHORE_PANS[8][0]:
        fails.append("the gale must be the act's widest water")
    if max(w2) >= widths[0]:
        fails.append("the water is never again as wide as the first winter")
    if SHORE_PANS[10] != (64, 64):
        fails.append("track 10 is one boat: both theme seats at centre")

    # --- the tolls ---
    if TOLLS != {n: n for n in range(1, 11)}:
        fails.append("track N must toll N times, all ten tracks")
    sc4 = en.Score(4)
    if abs(play_tolls(sc4, 0, 10.0, 3, 62) - 15.0) > 1e-9 or \
            len(note_ons(sc4, 0)) != 3:
        fails.append("play_tolls emits the wrong bell count/spacing")
    # T10's widening peal: nine audible gaps, no phantom tenth-gap check.
    sc4b = en.Score(44)
    try:
        play_tolls(sc4b, 0, 0.0, 10, 62, spacing=1.6, widen=0.3)
    except ValueError:
        fails.append("play_tolls phantom last-gap check is back")
    else:
        if len(note_ons(sc4b, 0)) != 10:
            fails.append("play_tolls: ten tolls expected")

    # --- the vowel clock ---
    if sorted(VOWEL_CAPS) != list(range(1, 11)):
        fails.append("vowel caps must cover all ten tracks")
    if not (VOWEL_CAPS[1] < VOWEL_CAPS[2] <= VOWEL_CAPS[3] and
            VOWEL_CAPS[4] < VOWEL_CAPS[3] <= VOWEL_CAPS[5]):
        fails.append("vowel clock shape: rise to T3, dip at T4, open at T5")
    if VOWEL_FLOOR_T5 <= VOWEL_CAPS[4]:
        fails.append("T5 must open beyond T4's ceiling")
    if not VOWEL_CAPS[8] < VOWEL_CAPS[7]:
        fails.append("the gale must seal the mouths again (T8 < T7)")
    if not (VOWEL_FLOOR_T10 > VOWEL_FLOOR_T5 and
            VOWEL_FLOOR_T10 > VOWEL_CAPS[7]):
        fails.append("T10 must open wider than the whole record before it")

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

    # --- Act Two cadence law: the plagal signature ---
    if ACT2_PLAGAL_TRACKS != {6, 7, 9, 10}:
        fails.append("plagal finals are T6/T7/T9/T10; T8 stays unresolved")
    sc7 = en.Score(7)
    sc7.note(0, en.n("G2"), 0.0, 1.0, 70, jt=0)      # the IV of D
    sc7.note(0, en.n("D2"), 1.0, 2.0, 70, jt=0)
    if plagal_final_failures(sc7, 0, 1.0, _pc("D")):
        fails.append("plagal_final_failures rejects a legal IV-I")
    sc8 = en.Score(8)
    sc8.note(0, en.n("A2"), 0.0, 1.0, 70, jt=0)      # v-i must NOT pass
    sc8.note(0, en.n("D2"), 1.0, 2.0, 70, jt=0)
    if not plagal_final_failures(sc8, 0, 1.0, _pc("D")):
        fails.append("plagal_final_failures accepts a v-i (not plagal)")
    sc9 = en.Score(9)
    sc9.note(0, en.n("G2"), 0.0, 1.0, 70, jt=0)
    sc9.note(0, en.n("D2"), 1.0, 2.0, 70, jt=0)
    sc9.note(1, en.n("C#4"), 0.5, 0.5, 70, jt=0)
    if plagal_final_failures(sc9, 0, 1.0, _pc("D")):
        fails.append("plagal_final_failures must NOT ban the leading tone")

    return fails
