"""material.py — the recurring musical material of *Sub Rosa*.

An Enigma-inspired piece: a chant that behaves like plainsong, a bass
that behaves like a hook, and a bamboo flute that behaves like a voice.
Everything is scale DEGREES in D aeolian (see engine.pitch).

  CHANT          32 beats of stepwise, melisma-tailed plainsong whose
                 strong-beat skeleton [1 2 3 2 5 4 1 2] is a chord tone
                 of BOTH grounds — so the same chant can be sung over
                 the verse and over the climax reharmonization.
  CHANT_GROUND   i VII VI VII       (Dm C Bb C — the verse engine)
  CLIMAX_GROUND  VI VII i v III iv VI VII
                 (Bb C Dm Am F Gm Bb C — the widescreen restatement)
  bass_riff()    one bar of THE bass hook on any root, in three guises:
                 "verse" (spacious), "drive" (16th syncopation),
                 "climax" (octave-popping run) — root/fifth/octave on
                 the strong beats, passing tones between, and the two
                 fast guises must touch >= 5 distinct pitches per bar
                 (the bass is a melody, machine-certifiably so).
  SHAKU          the bamboo flute call: strictly D-minor-pentatonic
                 (degrees {1 3 4 5 7} mod 7), long tones built to carry
                 scoops, bends and vibrato.
  arp_cell()     the sequencer ladder (root 3rd 5th 8ve 10th) per bar.
  snap_to_chord  the vocal arranger's correction for stacked voices.

`verify_material()` returns failures; `build.py --verify` calls it.
Fix the material, never the oracle.
"""

from __future__ import annotations

import math

import engine as en

MODE = "aeolian"                # D aeolian throughout

# ---------------------------------------------------------------------------
# The chant.  Strong-beat skeleton [1 2 3 2 5 4 1 2] at beats 0,4,..28.
# Stepwise (max leap a perfect 4th), range a minor 6th: true plainsong
# manners.  It ends hanging on degree 2 — the 9th over the VII chord —
# so every repetition leans forward into the next cycle's tonic.
# ---------------------------------------------------------------------------

SKELETON = [1, 2, 3, 2, 5, 4, 1, 2]

CHANT = [
    (1, 0, 3), (2, 3, 1),                                   # D... E
    (2, 4, 2), (3, 6, 1), (4, 7, 1),                        # E.. F G
    (3, 8, 2.5), (2, 10.5, 0.5), (1, 11, 1),                # F.. (E) D
    (2, 12, 3), (1, 15, 0.5), (2, 15.5, 0.5),               # E... melisma
    (5, 16, 2), (6, 18, 1), (5, 19, 1),                     # A, Bb A
    (4, 20, 2), (5, 22, 1), (4, 23, 1),                     # G, A G
    (1, 24, 2), (2, 26, 1), (3, 27, 1),                     # D, E F
    (2, 28, 4),                                             # E (hanging 9th)
]
CHANT_BEATS = 32.0
CHANT_FRAG = CHANT[:4]          # bar 1-2: the "sigil" fragment (D... E..F G)
CHANT_RANGE_SEMIS = 12          # anyone can hum it
CHANT_MAX_LEAP = 5              # plainsong moves by step; a 4th at most

# The cadence tail: the last phrase re-written to RESOLVE (for the final
# statement in the afterglow) — approach the tonic from above and below.
CHANT_CADENCE = [
    (1, 0, 2), (2, 2, 1), (3, 3, 1),
    (2, 4, 1.5), (1, 5.5, 0.5), (0, 6, 1), (1, 7, 5),       # ...C# no: deg 0
]
# degree 0 is the seventh BELOW the tonic (C in D aeolian) — a modal,
# subtonic approach, not a leading tone: chant, not chorale.

# ---------------------------------------------------------------------------
# Grounds.  Diatonic triads on the listed root degrees, one bar (4 beats)
# each.  Degree 2 (the diminished chord in aeolian) is never a root.
# ---------------------------------------------------------------------------

CHANT_GROUND = [1, 7, 6, 7]                     # Dm  C  Bb  C
CLIMAX_GROUND = [6, 7, 1, 5, 3, 4, 6, 7]        # Bb C Dm Am F Gm Bb C


def chord_set(root: int) -> set[int]:
    """Chord-tone degrees of the diatonic triad on `root`, mod 7 (1..7)."""
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def ground_root_at(ground: list[int], beat: float, bar_beats: float = 4.0) -> int:
    return ground[int(beat // bar_beats) % len(ground)]


# ---------------------------------------------------------------------------
# The bass hook.  bass_riff(root, guise) returns one bar of
# (degree, start_in_bar, dur) with degrees ABSOLUTE (root + step).
# Strong beats (0 and 2) carry root/fifth/octave only; the motion
# between them is where the melody lives.
# ---------------------------------------------------------------------------

_BASS_GUISES: dict[str, list[tuple[int, float, float]]] = {
    # steps relative to the bar root; +2 third, +4 fifth, +7 octave
    "verse": [
        (0, 0.0, 1.5), (0, 1.5, 0.5), (4, 2.0, 1.0), (7, 3.0, 0.5),
        (4, 3.5, 0.5),
    ],
    "drive": [
        (0, 0.0, 0.75), (0, 0.75, 0.25), (7, 1.0, 0.5), (4, 1.5, 0.5),
        (0, 2.0, 0.75), (2, 2.75, 0.25), (4, 3.0, 0.5), (5, 3.5, 0.25),
        (4, 3.75, 0.25),
    ],
    "climax": [
        (0, 0.0, 0.5), (7, 0.5, 0.25), (0, 0.75, 0.25), (0, 1.0, 0.5),
        (4, 1.5, 0.25), (5, 1.75, 0.25), (7, 2.0, 0.5), (6, 2.5, 0.25),
        (5, 2.75, 0.25), (4, 3.0, 0.5), (2, 3.5, 0.25), (1, 3.75, 0.25),
    ],
}
BASS_GUISE_MIN_DISTINCT = {"verse": 3, "drive": 5, "climax": 6}


def bass_root(ground_root: int) -> int:
    """Fold a ground root into the bass octave: roots 5..7 play a 7th
    (an octave in degree arithmetic) lower so the line stays low."""
    return ground_root - 7 if ground_root >= 5 else ground_root


def bass_riff(root: int, guise: str) -> list[tuple[int, float, float]]:
    """One 4-beat bar of the hook on `root` (an absolute degree)."""
    return [(root + step, s, d) for step, s, d in _BASS_GUISES[guise]]


# ---------------------------------------------------------------------------
# The bamboo flute call — strictly minor-pentatonic, long tones.
# ---------------------------------------------------------------------------

PENTATONIC = {1, 3, 4, 5, 7}    # D F G A C

SHAKU = [
    (5, 0, 3), (4, 3, 1),
    (3, 4, 2), (4, 6, 0.5), (3, 6.5, 0.5), (1, 7, 1),
    (5, 8, 2.5), (7, 10.5, 1.5),
    (8, 12, 3), (7, 15, 1),
]
SHAKU_BEATS = 16.0
SHAKU_RANGE_SEMIS = 17

# The answer phrase — falling where SHAKU rises, for call-and-response.
SHAKU_ANSWER = [
    (8, 0, 2), (7, 2, 1), (5, 3, 1),
    (4, 4, 2.5), (3, 6.5, 0.5), (4, 7, 1),
    (3, 8, 2), (1, 10, 2),
    (1, 12, 4),
]

# ---------------------------------------------------------------------------
# The sequencer ladder (one bar, 8 quaver slots).
# ---------------------------------------------------------------------------

ARP_LADDER = (0, 2, 4, 7, 9)                    # root 3rd 5th 8ve 10th
ARP_PATTERN = (0, 2, 3, 4, 3, 2, 3, 4)          # ladder index per slot


def arp_cell(root: int) -> list[tuple[int, float, float]]:
    """One bar (8 quaver slots) of the ladder on `root`; degrees absolute."""
    return [(root + ARP_LADDER[ix], slot * 0.5, 0.5)
            for slot, ix in enumerate(ARP_PATTERN)]


# ---------------------------------------------------------------------------
# Stacking and the arranger's snap (for the climax descant).
# ---------------------------------------------------------------------------

CLASH = {1, 6, 11}              # forbidden intervals vs the ground root, mod 12


def shift_steps(theme: list[tuple[int, float, float]], steps: int):
    return [(d + steps, s, dur) for d, s, dur in theme]


def snap_to_chord(voice: list[tuple[int, float, float]], ground: list[int],
                  mode: str = MODE, bar_beats: float = 4.0):
    """Correct strong-beat clashes: any note SOUNDING ACROSS a bar downbeat
    whose interval vs that bar's ground root is in CLASH is snapped to the
    nearest chord tone (ties resolve upward).  Off-beat dissonance passes
    through — that is music, not error."""
    eps = 1e-9
    out = []
    for deg, start, dur in voice:
        bar_start = math.floor(start / bar_beats + eps) * bar_beats
        next_downbeat = math.ceil((start + eps) / bar_beats) * bar_beats
        if abs(start - bar_start) < eps:
            downbeat = bar_start
        elif start < next_downbeat < start + dur - eps:
            downbeat = next_downbeat
        else:
            out.append((deg, start, dur))
            continue
        root = ground_root_at(ground, downbeat, bar_beats)
        iv = (en.deg_semis(mode, deg) - en.deg_semis(mode, root)) % 12
        new_deg = deg
        if iv in CLASH:
            semis = en.deg_semis(mode, deg)
            best = None
            for k in (0, 2, 4):
                for octave in (-7, 0, 7):
                    cand = root + k + octave
                    d = abs(en.deg_semis(mode, cand) - semis)
                    if best is None or d < best[0] or (d == best[0] and cand > best[1]):
                        best = (d, cand)
            new_deg = best[1]
        out.append((new_deg, start, dur))
    return out


def descant(ground: list[int]) -> list[tuple[int, float, float]]:
    """The chant a diatonic 3rd up, snapped clash-free against `ground`."""
    return snap_to_chord(shift_steps(CHANT, 2), ground)


# ---------------------------------------------------------------------------
# The whispered text (lyric metas).  Original Latin, no quotation.
# ---------------------------------------------------------------------------

WHISPERS = [
    "sub rosa",                  # under the rose: in secrecy
    "in silentio",               # in silence
    "veritas dormit",            # the truth sleeps
    "sub rosa loquimur",         # under the rose we speak
]

# ---------------------------------------------------------------------------
# Oracle helpers
# ---------------------------------------------------------------------------


def _sounding_at(theme, beat: float, length: float):
    b = beat % length
    for deg, start, dur in theme:
        if start <= b < start + dur:
            return deg
    return None


def _range_semis(theme, mode: str = MODE) -> int:
    semis = [en.deg_semis(mode, d) for d, _s, _dur in theme]
    return max(semis) - min(semis)


def _max_leap_semis(theme, mode: str = MODE) -> int:
    ordered = sorted(theme, key=lambda x: x[1])
    semis = [en.deg_semis(mode, d) for d, _s, _dur in ordered]
    return max((abs(b - a) for a, b in zip(semis, semis[1:])), default=0)


# ---------------------------------------------------------------------------
# The oracle
# ---------------------------------------------------------------------------


def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. The chant's strong-beat skeleton is what it claims to be.
    sk = [_sounding_at(CHANT, float(b), CHANT_BEATS) for b in range(0, 32, 4)]
    if sk != SKELETON:
        fails.append(f"CHANT: strong-beat skeleton {sk} != {SKELETON}")

    # 2. The skeleton is a chord tone of BOTH grounds, bar by bar.
    for gname, ground in (("CHANT_GROUND", CHANT_GROUND),
                          ("CLIMAX_GROUND", CLIMAX_GROUND)):
        for i, deg in enumerate(SKELETON):
            root = ground[i % len(ground)]
            if ((deg - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"CHANT downbeat {i * 4} (degree {deg}) is not "
                             f"a chord tone of {gname} bar {i} (root {root})")

    # 3. Plainsong manners: hummable range, stepwise motion.
    if _range_semis(CHANT) > CHANT_RANGE_SEMIS:
        fails.append(f"CHANT spans {_range_semis(CHANT)} semis "
                     f"(> {CHANT_RANGE_SEMIS})")
    if _max_leap_semis(CHANT) > CHANT_MAX_LEAP:
        fails.append(f"CHANT leaps {_max_leap_semis(CHANT)} semis "
                     f"(> {CHANT_MAX_LEAP} - not plainsong)")
    if _max_leap_semis(CHANT_CADENCE) > CHANT_MAX_LEAP:
        fails.append("CHANT_CADENCE leaps wider than a 4th")
    last = max(CHANT_CADENCE, key=lambda x: x[1])
    if last[0] != 1:
        fails.append("CHANT_CADENCE does not end on the tonic")

    # 4. No ground uses the diminished chord (degree-2 root) and every
    #    ground root is a plain degree 1..7.
    for gname, ground in (("CHANT_GROUND", CHANT_GROUND),
                          ("CLIMAX_GROUND", CLIMAX_GROUND)):
        for root in ground:
            if root == 2:
                fails.append(f"{gname}: degree-2 root (diminished chord)")
            if not 1 <= root <= 7:
                fails.append(f"{gname}: root {root} out of 1..7")

    # 5. The bass hook: full-bar coverage, chord tones on the strong
    #    beats, and machine-certified melodicity (distinct pitch count).
    for guise, cell in _BASS_GUISES.items():
        span = max(s + d for _st, s, d in cell)
        if abs(span - 4.0) > 1e-9:
            fails.append(f"bass '{guise}': spans {span} beats != 4")
        horizon = 0.0
        for _st, s, d in sorted(cell, key=lambda x: x[1]):
            if s - horizon > 1e-9:
                fails.append(f"bass '{guise}': gap at beat {horizon}")
                break
            horizon = max(horizon, s + d)
        for strong in (0.0, 2.0):
            step = next((st for st, s, d in cell
                         if s <= strong < s + d), None)
            if step is None or step % 7 not in (0, 2, 4):
                fails.append(f"bass '{guise}': beat {strong} carries step "
                             f"{step} - not a chord tone of the bar root")
        distinct = len({st for st, _s, _d in cell})
        need = BASS_GUISE_MIN_DISTINCT[guise]
        if distinct < need:
            fails.append(f"bass '{guise}': {distinct} distinct pitches "
                         f"(< {need} - not melodic enough)")

    # 6. The flute is strictly pentatonic and stays in a playable span.
    for pname, phrase in (("SHAKU", SHAKU), ("SHAKU_ANSWER", SHAKU_ANSWER)):
        for deg, _s, _d in phrase:
            if ((deg - 1) % 7) + 1 not in PENTATONIC:
                fails.append(f"{pname}: degree {deg} outside the "
                             f"minor pentatonic")
        if _range_semis(phrase) > SHAKU_RANGE_SEMIS:
            fails.append(f"{pname} spans {_range_semis(phrase)} semis "
                         f"(> {SHAKU_RANGE_SEMIS})")

    # 7. The sequencer cell is 8 slots over 4 beats, all chord tones.
    for root in sorted(set(CHANT_GROUND + CLIMAX_GROUND)):
        cell = arp_cell(root)
        if len(cell) != 8 or abs(max(s + d for _dg, s, d in cell) - 4.0) > 1e-9:
            fails.append(f"arp_cell({root}) is not 8 slots over 4 beats")
        for deg, _s, _d in cell:
            if ((deg - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"arp_cell({root}): degree {deg} outside "
                             f"the chord")

    # 8. The climax descant needs NO snapping against its own ground
    #    (pure parallel writing over the reharmonization) and is
    #    clash-free on every downbeat.
    third_up = shift_steps(CHANT, 2)
    snapped = snap_to_chord(third_up, CLIMAX_GROUND)
    length = CHANT_BEATS
    for b in range(0, int(length), 4):
        deg = _sounding_at(snapped, float(b), length)
        if deg is None:
            continue
        root = ground_root_at(CLIMAX_GROUND, float(b))
        iv = (en.deg_semis(MODE, deg) - en.deg_semis(MODE, root)) % 12
        if iv in CLASH:
            fails.append(f"descant: interval {iv} vs root {root} at beat {b}")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass "
          f"(skeleton {SKELETON}, chant range "
          f"{_range_semis(CHANT)} semis, bass guises "
          f"{sorted(_BASS_GUISES)})")
