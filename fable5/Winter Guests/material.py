"""material.py — the recurring musical material of *Winter Guests*.

Everything is scale DEGREES (see engine.pitch).  The piece's DNA is one
theme with three machine-verified lives:

  THEME          "the Guest theme" — 32 beats, strong-beat skeleton
                 [1 5 2 1 3 7 4 1], range <= 16 semitones (hummable)
  CHORUS_GUISE   the same skeleton re-rhythmed ABBA-style (every phrase
                 anticipated on the &-of-4 into the next bar)
  GUITAR_GUISE   the same skeleton ornamented with connecting runs

Grounds:

  HUM_GROUND     i  III VII iv           (CTD verse, aeolian)
  CHORUS_GROUND  I V ii vi | I V IV I    (the ABBA chorus, ionian)
  COLD_CELL      i | VI arpeggio cell    (The Visitors sequencer)
  FOOTSTEPS      7/8 bass cell, 3+2+2    (the dark third movement)

Stacks: `stack_thirds` builds parallel 3rd-above / 6th-below voices;
`snap_to_chord` corrects any strong-beat clash to the nearest chord tone
(what a real vocal arranger does).  The oracle proves: skeleton identity
across all three guises, hummable range, theme downbeats are chord tones
of BOTH grounds, the chorus stack is clash-free against the ground roots
(in ionian, and trivially at the +2 gear change — transposition preserves
intervals), and the snapped aeolian verse-2 pairing is clash-free.

`verify_material()` returns failures; `build.py --verify` calls it.
Fix the material, never the oracle.
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# The Guest theme.  Strong-beat skeleton [1 5 2 1 3 7 4 1] at beats 0,4,..28.
# ---------------------------------------------------------------------------

SKELETON = [1, 5, 2, 1, 3, 7, 4, 1]

THEME = [
    (1, 0, 2), (2, 2, 1), (3, 3, 1),
    (5, 4, 2), (4, 6, 1), (3, 7, 1),
    (2, 8, 1.5), (3, 9.5, 0.5), (4, 10, 1), (2, 11, 1),
    (1, 12, 3), (0, 15, 1),
    (3, 16, 2), (4, 18, 1), (5, 19, 1),
    (7, 20, 2), (8, 22, 1), (6, 23, 1),
    (4, 24, 1.5), (3, 25.5, 0.5), (2, 26, 1), (3, 27, 1),
    (1, 28, 4),
]
THEME_FRAG = THEME[:6]          # bars 1-2: the "knock at the door" fragment

# ABBA guise: same skeleton, pop rhythm, every phrase anticipated on the
# &-of-4 so the new chord's note arrives half a beat early and HOLDS the
# downbeat (the anticipation is the style; the oracle checks the downbeat).
CHORUS_GUISE = [
    (1, 0, 1), (1, 1, 0.5), (2, 1.5, 0.5), (3, 2, 1), (3, 3, 0.5),
    (5, 3.5, 2.5),
    (4, 6, 0.5), (3, 6.5, 0.5), (2, 7, 0.5), (2, 7.5, 1.5),
    (2, 9, 0.5), (3, 9.5, 0.5), (4, 10, 1), (2, 11, 0.5),
    (1, 11.5, 2.5),
    (0, 14, 0.5), (1, 14.5, 0.5), (2, 15, 0.5),
    (3, 15.5, 2.5),
    (4, 18, 0.5), (5, 18.5, 0.5), (6, 19, 0.5),
    (7, 19.5, 2.5),
    (8, 22, 1), (6, 23, 0.5),
    (4, 23.5, 2),
    (3, 25.5, 0.5), (2, 26, 0.5), (3, 26.5, 1),
    (1, 27.5, 4.5),
]

# Oldfield guise: the skeleton ornamented with connecting 8th/16th runs.
GUITAR_GUISE = [
    (1, 0, 1.5), (2, 1.5, 0.5), (3, 2, 0.5), (4, 2.5, 0.5), (3, 3, 0.5),
    (4, 3.5, 0.5),
    (5, 4, 1.5), (6, 5.5, 0.25), (5, 5.75, 0.25), (4, 6, 0.5), (3, 6.5, 0.5),
    (2, 7, 0.5), (1, 7.5, 0.5),
    (2, 8, 1), (3, 9, 0.5), (4, 9.5, 0.5), (3, 10, 0.5), (2, 10.5, 0.5),
    (1, 11, 0.5), (2, 11.5, 0.5),
    (1, 12, 2), (2, 14, 0.5), (1, 14.5, 0.5), (0, 15, 0.5), (1, 15.5, 0.5),
    (3, 16, 1.5), (4, 17.5, 0.5), (5, 18, 0.5), (6, 18.5, 0.5), (5, 19, 0.5),
    (6, 19.5, 0.5),
    (7, 20, 1.5), (8, 21.5, 0.5), (8, 22, 0.5), (7, 22.5, 0.5), (6, 23, 0.5),
    (5, 23.5, 0.5),
    (4, 24, 1), (5, 25, 0.5), (4, 25.5, 0.5), (3, 26, 0.5), (2, 26.5, 0.5),
    (3, 27, 0.5), (2, 27.5, 0.5),
    (1, 28, 4),
]

GUISES = {"THEME": THEME, "CHORUS_GUISE": CHORUS_GUISE,
          "GUITAR_GUISE": GUITAR_GUISE}
THEME_BEATS = 32.0
HUMMABLE_SEMIS = 16             # a minor 10th: a baritone can hum it

# ---------------------------------------------------------------------------
# Grounds.  Chords are diatonic triads on the listed root degrees; the
# chord-degree set of root r is {r, r+2, r+4} compared mod 7.
# ---------------------------------------------------------------------------

HUM_GROUND = [1, 3, 7, 4]                 # i III VII iv  (Em G D Am), 1 bar each
CHORUS_GROUND = [1, 5, 2, 6, 1, 5, 4, 1]  # I V ii vi | I V IV I (D A Em Bm ...)


def chord_set(root: int) -> set[int]:
    """Chord-tone degrees of the diatonic triad on `root`, mod 7 (1..7)."""
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def ground_root_at(ground: list[int], beat: float, bar_beats: float = 4.0) -> int:
    return ground[int(beat // bar_beats) % len(ground)]


# ---------------------------------------------------------------------------
# The Visitors: cold arpeggio cell (i | VI), realized by cold_arp().
# ---------------------------------------------------------------------------

COLD_CHORDS = [1, 6]                       # Em | C in E aeolian
COLD_PATTERN = (0, 2, 3, 4, 3, 2, 3, 4)    # ladder indices per 8 slots/bar
COLD_LADDER = (0, 2, 4, 7, 9)              # root, 3rd, 5th, 8ve, 10th (degree steps)


def cold_arp(bar: int) -> list[tuple[int, float, float]]:
    """One bar (8 quaver slots, 4 beats) of the cold cell; `bar` alternates
    the i and VI harmonies.  Returns (degree, start_in_bar, dur)."""
    root = COLD_CHORDS[bar % 2]
    out = []
    for slot, ladder_ix in enumerate(COLD_PATTERN):
        deg = root + COLD_LADDER[ladder_ix]
        out.append((deg, slot * 0.5, 0.5))
    return out


# The dark movement's 7/8 cell (quaver = 0.5 beat; 3+2+2).
FOOTSTEPS = [
    (1, 0.0, 0.5), (1, 0.5, 0.5), (5, 1.0, 0.5),   # 3
    (4, 1.5, 0.5), (5, 2.0, 0.5),                  # 2
    (0, 2.5, 0.5), (1, 3.0, 0.5),                  # 2
]
FOOTSTEPS_ACCENTS = (0, 3, 5)
FOOTSTEPS_BEATS = 3.5

# ---------------------------------------------------------------------------
# Stacks (ABBA) and the arranger's snap.
# ---------------------------------------------------------------------------

CLASH = {1, 6, 11}              # forbidden intervals vs the ground root, mod 12


def shift_steps(theme: list[tuple[int, float, float]], steps: int):
    return [(d + steps, s, dur) for d, s, dur in theme]


def stack_thirds(theme: list[tuple[int, float, float]]):
    """(top, mid, low): parallel diatonic 3rd above, the theme, 3rd below
    (which the arrangement usually drops an octave => a 6th below)."""
    return shift_steps(theme, 2), list(theme), shift_steps(theme, -2)


def snap_to_chord(voice: list[tuple[int, float, float]], ground: list[int],
                  mode: str, bar_beats: float = 4.0):
    """Correct strong-beat clashes: any note SOUNDING on a bar-start whose
    interval vs the ground root is in CLASH is snapped to the nearest
    chord tone (in semitones; ties resolve upward).  Other notes pass
    through — passing dissonance off the strong beats is music."""
    out = []
    for deg, start, dur in voice:
        new_deg = deg
        bar_start = float(int(start // bar_beats)) * bar_beats
        sounding_downbeat = start <= bar_start < start + dur or start == bar_start
        if sounding_downbeat:
            root = ground_root_at(ground, bar_start, bar_beats)
            iv = (en.deg_semis(mode, deg) - en.deg_semis(mode, root)) % 12
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


# ---------------------------------------------------------------------------
# Oracle helpers
# ---------------------------------------------------------------------------

def _sounding_at(theme, beat: float, length: float):
    b = beat % length
    for deg, start, dur in theme:
        if start <= b < start + dur:
            return deg
    return None


def _skeleton_of(theme) -> list[int | None]:
    return [_sounding_at(theme, float(b), THEME_BEATS) for b in range(0, 32, 4)]


def _range_semis(theme, mode: str) -> int:
    semis = [en.deg_semis(mode, d) for d, _s, _dur in theme]
    return max(semis) - min(semis)


def _strong_beat_clashes(voice, ground, mode, label: str,
                         bar_beats: float = 4.0) -> list[str]:
    fails = []
    length = max(s + d for _dg, s, d in voice)
    for b in range(0, int(length), int(bar_beats)):
        deg = _sounding_at(voice, float(b), length)
        if deg is None:
            continue
        root = ground_root_at(ground, float(b), bar_beats)
        iv = (en.deg_semis(mode, deg) - en.deg_semis(mode, root)) % 12
        if iv in CLASH:
            fails.append(f"{label}: interval {iv} vs root degree {root} "
                         f"at beat {b}")
    return fails


# ---------------------------------------------------------------------------
# The oracle
# ---------------------------------------------------------------------------

def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. Tri-guise skeleton identity.
    for name, guise in GUISES.items():
        sk = _skeleton_of(guise)
        if sk != SKELETON:
            fails.append(f"{name}: strong-beat skeleton {sk} != {SKELETON}")

    # 2. Hummable range (both modes it is sung in).
    for mode in ("aeolian", "ionian"):
        r = _range_semis(THEME, mode)
        if r > HUMMABLE_SEMIS:
            fails.append(f"THEME spans {r} semis in {mode} "
                         f"(> {HUMMABLE_SEMIS} - not hummable)")

    # 3. Theme downbeats are chord tones of BOTH grounds.
    for gname, ground, mode in (("HUM_GROUND", HUM_GROUND, "aeolian"),
                                ("CHORUS_GROUND", CHORUS_GROUND, "ionian")):
        for i, deg in enumerate(SKELETON):
            root = ground[i % len(ground)]
            if ((deg - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"THEME downbeat {i * 4} (degree {deg}) is not "
                             f"a chord tone of {gname} bar {i} "
                             f"(root {root})")

    # 4. The chorus stack is clash-free vs the ground roots in ionian
    #    (the +2 gear change preserves every interval, so this also
    #    certifies the E-major restatement).
    top, mid, low = stack_thirds(CHORUS_GUISE)
    for label, voice in (("stack top", top), ("stack mid", mid),
                         ("stack low", low)):
        fails += _strong_beat_clashes(snap_to_chord(voice, CHORUS_GROUND,
                                                    "ionian"),
                                      CHORUS_GROUND, "ionian",
                                      f"CHORUS {label}")
    # The chorus stack should need NO snapping (pure parallel writing):
    for label, voice in (("top", top), ("low", low)):
        if snap_to_chord(voice, CHORUS_GROUND, "ionian") != voice:
            fails.append(f"CHORUS stack {label} required snapping - "
                         f"reharmonize the ground or the guise")

    # 5. The verse-2 hum harmony (3rd above, aeolian) is clash-free AFTER
    #    the arranger's snap (the snap is allowed here; M2 uses it).
    verse_harmony = snap_to_chord(shift_steps(THEME, 2), HUM_GROUND, "aeolian")
    fails += _strong_beat_clashes(verse_harmony, HUM_GROUND, "aeolian",
                                  "VERSE-2 harmony (snapped)")

    # 6. Cold cell and footsteps well-formed.
    for bar in (0, 1):
        cell = cold_arp(bar)
        if len(cell) != 8 or abs(max(s + d for _dg, s, d in cell) - 4.0) > 1e-9:
            fails.append(f"cold_arp({bar}) is not 8 slots over 4 beats")
        root = COLD_CHORDS[bar % 2]
        for deg, _s, _d in cell:
            if ((deg - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"cold_arp({bar}): degree {deg} outside the "
                             f"chord on {root}")
    span = max(s + d for _dg, s, d in FOOTSTEPS)
    if abs(span - FOOTSTEPS_BEATS) > 1e-9:
        fails.append(f"FOOTSTEPS spans {span} beats != {FOOTSTEPS_BEATS}")

    # 7. Gear-change range sanity: the chorus stack's top voice at +2
    #    semis stays under MIDI 96 when sung from A4 (the tessitura the
    #    roadmap gives choir I in the E-major chorus).
    top_max = max(en.deg_semis("ionian", d) for d, _s, _dur in top)
    if 69 + top_max + 2 > 96:
        fails.append("gear-changed stack top exceeds the choir ceiling")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass "
          f"(skeleton {SKELETON}, theme range "
          f"{_range_semis(THEME, 'aeolian')} semis)")
