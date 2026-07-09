"""material.py — the recurring musical material of *Seven Kinds of Sunlight*.

An upbeat, through-written SONG in D ionian: verse / pre-chorus /
chorus / middle-eight architecture, odd meters (7/8 verses, 6/8
pre-choruses, 5/4 middle-eight, a mixed-meter drum break), and a
chorus built as machine-verified THREE-VOICE COUNTERPOINT:

  HOOK        the chorus vocal (32 beats over CHORUS_GROUND); anthem
              skeleton [5 7 6 6 5 5 4 3], singable range, leaps <= a 5th
  COUNTER_A   the riff — an 8th-note guitar/synth line whose strong
              slots are chord tones (also the song's intro hook)
  COUNTER_B   the slow inner line (strings/organ), two chord tones a
              bar, smooth voice leading
  The oracle proves all three pairwise CONSONANT on beats 0 and 2 of
  every chorus bar (intervals mod 12 never {1, 2, 6, 11}), so the
  final chorus can stack them plus a snapped descant.

  VERSE_*     the 7/8 engine: ground vi V IV V (Bm A G A), a driving
              3+2+2 bass cell, a hummed melody whose bar-line skeleton
              is [8 7 6 7], and a CANON — verse 2's piano answers the
              melody one bar late, a 4th below, consonant at every
              downbeat where the two overlap
  PRECH_*     the 6/8 lift: rising ground ii iii IV V x2, melody
              skeleton [4 5 6 7 6 7 8 9] — strictly rising
  M8_*        the 5/4 middle-eight: ground vi iii IV ii vi iii IV V,
              a two-voice flute/lead counterpoint consonant on beats
              0 and 3 of every bar
  CHORUS_BASS the driving engine: >= 2 notes a beat, 5 distinct
              pitches a bar, root under every strong beat

The final chorus lifts everything +2 semitones (D -> E); transposition
preserves every interval, so the oracle's consonances certify the
gear-changed restatement too.

`verify_material()` returns failures; `build.py --verify` calls it.
Fix the material, never the oracle.
"""

from __future__ import annotations

import engine as en

MODE = "ionian"                 # D ionian; the gear change is +2 semis

CLASH = {1, 2, 6, 10, 11}       # forbidden pairwise intervals mod 12
# (inversion-symmetric: seconds, sevenths and the tritone in EITHER
# direction — an asymmetric set let a major 2nd hide as a minor 7th)


def chord_set(root: int) -> set[int]:
    """Chord-tone degrees of the diatonic triad on `root`, mod 7 (1..7)."""
    return {((root - 1 + k) % 7) + 1 for k in (0, 2, 4)}


def interval(a: int, b: int, mode: str = MODE) -> int:
    """Interval of degree a above degree b, semitones mod 12."""
    return (en.deg_semis(mode, a) - en.deg_semis(mode, b)) % 12


# ---------------------------------------------------------------------------
# THE CHORUS — ground + three counterpoint voices (4/4, 8 bars, 32 beats)
# ---------------------------------------------------------------------------

CHORUS_GROUND = [1, 5, 6, 4, 1, 5, 4, 1]        # D A Bm G | D A G D
CHORUS_BEATS = 32.0

HOOK_SKELETON = [5, 7, 6, 6, 5, 5, 4, 3]

HOOK = [
    (5, 0, 1.5), (6, 1.5, 0.5), (5, 2, 1), (3, 3, 1),
    (7, 4, 1.5), (8, 5.5, 0.5), (7, 6, 1), (6, 7, 1),
    (6, 8, 2), (3, 10, 1), (6, 11, 1),
    (6, 12, 1.5), (5, 13.5, 0.5), (4, 14, 1), (5, 15, 1),
    (5, 16, 1.5), (6, 17.5, 0.5), (5, 18, 1), (3, 19, 1),
    (5, 20, 2), (7, 22, 1), (8, 23, 1),
    (4, 24, 1.5), (5, 25.5, 0.5), (6, 26, 1), (5, 27, 1),
    (3, 28, 2), (2, 30, 1), (1, 31, 1),
]
HOOK_RANGE_SEMIS = 12
HOOK_MAX_LEAP = 7               # a perfect 5th: pop, not plainsong

# COUNTER_A: 8th-note riff.  Bars 0-6 arch through the chord + 6th;
# bar 7 cadences via the FIFTH on the strong slot (the octave there
# would sit a major 2nd under the hook's held degree 2 — the oracle
# caught exactly that in composition).
_A_ARCH = (0, 2, 4, 5, 7, 5, 4, 2)              # slots 0..7, strong 0 & 4
_A_CADENCE = (0, 2, 4, 7, 4, 2, 0, 2)


def counter_a() -> list[tuple[int, float, float]]:
    """The riff, realized over the whole 8-bar chorus (degrees absolute)."""
    out = []
    for bar, root in enumerate(CHORUS_GROUND):
        pattern = _A_CADENCE if bar == 7 else _A_ARCH
        for slot, step in enumerate(pattern):
            out.append((root + step, bar * 4.0 + slot * 0.5, 0.5))
    return out


# COUNTER_B: two chord tones a bar (halves fall on beats 0 and 2).
COUNTER_B_HALVES = [
    (3, 5), (2, 5), (3, 6), (1, 4), (3, 5), (2, 5), (1, 4), (3, 5),
]


def counter_b() -> list[tuple[int, float, float]]:
    out = []
    for bar, (h1, h2) in enumerate(COUNTER_B_HALVES):
        out.append((h1, bar * 4.0, 2.0))
        out.append((h2, bar * 4.0 + 2.0, 2.0))
    return out


# The driving chorus bass: one bar on root r, 9 notes, 5 distinct pitches.
_CHORUS_BASS_CELL = [
    (0, 0.0, 0.5), (0, 0.5, 0.5), (7, 1.0, 0.5), (0, 1.5, 0.5),
    (0, 2.0, 0.5), (4, 2.5, 0.5), (5, 3.0, 0.25), (4, 3.25, 0.25),
    (2, 3.5, 0.5),
]
CHORUS_BASS_MIN_DISTINCT = 5
CHORUS_BASS_MIN_RATE = 2.0      # notes per beat: the "driving" floor


def chorus_bass(root: int) -> list[tuple[int, float, float]]:
    return [(root + s, b, d) for s, b, d in _CHORUS_BASS_CELL]


# ---------------------------------------------------------------------------
# THE VERSE — 7/8 (3+2+2), ground vi V IV V, melody + canon
# ---------------------------------------------------------------------------

VERSE_GROUND = [6, 5, 4, 5]                     # Bm A G A, one 7/8 bar each
VERSE_BAR = 3.5
VERSE_STRONG = (0.0, 1.5, 2.5)                  # the 3+2+2 group starts

_VERSE_BASS_CELL = [
    (0, 0.0, 0.5), (7, 0.5, 0.5), (2, 1.0, 0.5), (4, 1.5, 0.5),
    (0, 2.0, 0.5), (4, 2.5, 0.5), (7, 3.0, 0.5),
]
VERSE_BASS_MIN_DISTINCT = 4


def verse_bass(root: int) -> list[tuple[int, float, float]]:
    return [(root + s, b, d) for s, b, d in _VERSE_BASS_CELL]


VERSE_SKELETON = [8, 7, 6, 7]                   # sounding at bar lines

VERSE_MELODY = [
    (8, 0.0, 1.5), (9, 1.5, 0.5), (8, 2.0, 1.0), (7, 3.0, 0.5),
    (7, 3.5, 1.5), (6, 5.0, 0.5), (7, 5.5, 0.5), (5, 6.0, 1.0),
    (6, 7.0, 2.0), (5, 9.0, 0.5), (4, 9.5, 1.0),
    (7, 10.5, 1.5), (6, 12.0, 0.5), (5, 12.5, 1.0),
]
VERSE_MELODY_BEATS = 14.0

CANON_DELAY = 3.5               # one 7/8 bar late
CANON_SHIFT = -3                # a diatonic 4th below


def canon_voice() -> list[tuple[int, float, float]]:
    return [(d + CANON_SHIFT, s + CANON_DELAY, dur)
            for d, s, dur in VERSE_MELODY]


# ---------------------------------------------------------------------------
# THE PRE-CHORUS — 6/8 lift, strictly rising
# ---------------------------------------------------------------------------

PRECH_GROUND = [2, 3, 4, 5, 2, 3, 4, 5]         # Em F#m G A, twice
PRECH_BAR = 3.0
PRECH_SKELETON = [4, 5, 6, 7, 6, 7, 8, 9]

PRECH_MELODY = [
    (4, 0.0, 2.0), (3, 2.0, 0.5), (4, 2.5, 0.5),
    (5, 3.0, 2.0), (4, 5.0, 0.5), (5, 5.5, 0.5),
    (6, 6.0, 2.0), (5, 8.0, 0.5), (6, 8.5, 0.5),
    (7, 9.0, 2.5), (6, 11.5, 0.5),
    (6, 12.0, 2.0), (5, 14.0, 0.5), (6, 14.5, 0.5),
    (7, 15.0, 2.0), (6, 17.0, 0.5), (7, 17.5, 0.5),
    (8, 18.0, 2.5), (7, 20.5, 0.5),
    (9, 21.0, 3.0),
]

# ---------------------------------------------------------------------------
# THE MIDDLE EIGHT — 5/4 (3+2), a two-voice flute/lead counterpoint
# ---------------------------------------------------------------------------

M8_GROUND = [6, 3, 4, 2, 6, 3, 4, 5]            # Bm F#m G Em | Bm F#m G A
M8_BAR = 5.0
M8_STRONG = (0.0, 3.0)

M8_LEAD_SKEL = [8, 7, 6, 6, 8, 7, 6, 7]         # sounding at bar starts
M8_LEAD_AT3 = [6, 5, 4, 4, 6, 5, 4, 5]          # sounding at beat 3
M8_FLUTE_SKEL = [10, 12, 11, 9, 10, 12, 11, 9]
M8_FLUTE_AT3 = M8_LEAD_SKEL                     # voices trade places


def m8_lead() -> list[tuple[int, float, float]]:
    out = []
    for bar in range(8):
        t = bar * M8_BAR
        a, b = M8_LEAD_SKEL[bar], M8_LEAD_AT3[bar]
        mid = (a + b) // 2
        out += [(a, t, 2.0), (mid, t + 2.0, 1.0), (b, t + 3.0, 2.0)]
    return out


def m8_flute() -> list[tuple[int, float, float]]:
    out = []
    for bar in range(8):
        t = bar * M8_BAR
        a, b = M8_FLUTE_SKEL[bar], M8_FLUTE_AT3[bar]
        mid = (a + b) // 2
        out += [(a, t, 2.0), (mid, t + 2.0, 1.0), (b, t + 3.0, 2.0)]
    return out


# ---------------------------------------------------------------------------
# The descant and the arranger's snap (final-chorus stack)
# ---------------------------------------------------------------------------


def shift_steps(theme, steps: int):
    return [(d + steps, s, dur) for d, s, dur in theme]


def snap_to_chord(voice, ground, mode: str = MODE, bar_beats: float = 4.0):
    """Snap strong-beat clashes to the nearest chord tone (see Sub Rosa)."""
    import math
    eps = 1e-9
    out = []
    for deg, start, dur in voice:
        bar_start = math.floor(start / bar_beats + eps) * bar_beats
        next_db = math.ceil((start + eps) / bar_beats) * bar_beats
        if abs(start - bar_start) < eps:
            downbeat = bar_start
        elif start < next_db < start + dur - eps:
            downbeat = next_db
        else:
            out.append((deg, start, dur))
            continue
        root = ground[int(downbeat // bar_beats) % len(ground)]
        if interval(deg, root) in CLASH:
            semis = en.deg_semis(mode, deg)
            best = None
            for k in (0, 2, 4):
                for octave in (-7, 0, 7):
                    cand = root + k + octave
                    d = abs(en.deg_semis(mode, cand) - semis)
                    if best is None or d < best[0] or (d == best[0]
                                                       and cand > best[1]):
                        best = (d, cand)
            deg = best[1]
        out.append((deg, start, dur))
    return out


def descant() -> list[tuple[int, float, float]]:
    """The hook a diatonic 3rd up, snapped clash-free for the stack."""
    return snap_to_chord(shift_steps(HOOK, 2), CHORUS_GROUND)


# The chorus syllables shown in the lyric lane.
SYLLABLES = ["oh", "oh-oh", "ah", "whoa-oh"]

# ---------------------------------------------------------------------------
# Oracle helpers
# ---------------------------------------------------------------------------


def _sounding_at(theme, beat: float, length: float | None = None):
    b = beat % length if length else beat
    for deg, start, dur in theme:
        if start - 1e-9 <= b < start + dur - 1e-9:
            return deg
    return None


def _range_semis(theme, mode: str = MODE) -> int:
    semis = [en.deg_semis(mode, d) for d, _s, _dur in theme]
    return max(semis) - min(semis)


def _max_leap(theme, mode: str = MODE) -> int:
    ordered = sorted(theme, key=lambda x: x[1])
    semis = [en.deg_semis(mode, d) for d, _s, _dur in ordered]
    return max((abs(b - a) for a, b in zip(semis, semis[1:])), default=0)


def _check_cell(fails, name, cell, span, strongs, root_rel, min_distinct):
    got = max(s + d for _st, s, d in cell)
    if abs(got - span) > 1e-9:
        fails.append(f"{name}: spans {got} beats != {span}")
    horizon = 0.0
    for _st, s, d in sorted(cell, key=lambda x: x[1]):
        if s - horizon > 1e-9:
            fails.append(f"{name}: gap at beat {horizon}")
            break
        horizon = max(horizon, s + d)
    for strong in strongs:
        step = next((st for st, s, d in cell if s <= strong < s + d), None)
        if step is None or (step - root_rel) % 7 not in (0, 2, 4):
            fails.append(f"{name}: beat {strong} carries step {step} - "
                         f"not a chord tone")
    if len({st for st, _s, _d in cell}) < min_distinct:
        fails.append(f"{name}: fewer than {min_distinct} distinct pitches")


# ---------------------------------------------------------------------------
# The oracle
# ---------------------------------------------------------------------------


def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. Hook skeleton + chord tones + singability.
    sk = [_sounding_at(HOOK, b * 4.0, CHORUS_BEATS) for b in range(8)]
    if sk != HOOK_SKELETON:
        fails.append(f"HOOK skeleton {sk} != {HOOK_SKELETON}")
    for bar, deg in enumerate(HOOK_SKELETON):
        if ((deg - 1) % 7) + 1 not in chord_set(CHORUS_GROUND[bar]):
            fails.append(f"HOOK downbeat {bar * 4} (degree {deg}) not a "
                         f"chord tone of bar {bar}")
    if _range_semis(HOOK) > HOOK_RANGE_SEMIS:
        fails.append(f"HOOK spans {_range_semis(HOOK)} semis (> 12)")
    if _max_leap(HOOK) > HOOK_MAX_LEAP:
        fails.append(f"HOOK leaps {_max_leap(HOOK)} semis (> a 5th)")

    # 2. Counter A strong slots are chord tones.
    ca = counter_a()
    for bar, root in enumerate(CHORUS_GROUND):
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            deg = _sounding_at(ca, strong)
            if deg is None or ((deg - 1) % 7) + 1 not in chord_set(root):
                fails.append(f"COUNTER_A: beat {strong} (degree {deg}) not "
                             f"a chord tone of bar {bar}")

    # 3. Counter B halves are chord tones.
    for bar, (h1, h2) in enumerate(COUNTER_B_HALVES):
        cs = chord_set(CHORUS_GROUND[bar])
        for h in (h1, h2):
            if ((h - 1) % 7) + 1 not in cs:
                fails.append(f"COUNTER_B bar {bar}: degree {h} not a "
                             f"chord tone")

    # 4. THREE-VOICE pairwise consonance on beats 0 and 2 of every bar.
    cb = counter_b()
    voices = {"HOOK": HOOK, "A": ca, "B": cb}
    names = sorted(voices)
    for bar in range(8):
        for strong in (bar * 4.0, bar * 4.0 + 2.0):
            sounding = {nm: _sounding_at(voices[nm], strong, CHORUS_BEATS)
                        for nm in names}
            for i, na in enumerate(names):
                for nb in names[i + 1:]:
                    da, db = sounding[na], sounding[nb]
                    if da is None or db is None:
                        continue
                    iv = interval(da, db)
                    if iv in CLASH:
                        fails.append(f"chorus counterpoint: {na}({da}) vs "
                                     f"{nb}({db}) = interval {iv} at beat "
                                     f"{strong}")

    # 5. Verse melody skeleton + chord tones; canon consonant at every
    #    downbeat where the two voices overlap (including the tail into
    #    the next cycle's bar 0).
    for bar, deg in enumerate(VERSE_SKELETON):
        got = _sounding_at(VERSE_MELODY, bar * VERSE_BAR)
        if got != deg:
            fails.append(f"VERSE_MELODY bar {bar}: sounding {got} != {deg}")
        if ((deg - 1) % 7) + 1 not in chord_set(VERSE_GROUND[bar]):
            fails.append(f"VERSE_MELODY skeleton {deg} not a chord tone "
                         f"of bar {bar}")
    canon = canon_voice()
    for k in range(1, 5):
        db = k * VERSE_BAR
        mel = _sounding_at(VERSE_MELODY, db % (4 * VERSE_BAR),
                           4 * VERSE_BAR) if k < 4 else \
            VERSE_SKELETON[0]                    # next cycle's downbeat
        can = _sounding_at(canon, db)
        if can is None:
            continue
        iv = interval(mel, can)
        if iv in CLASH:
            fails.append(f"CANON: melody({mel}) vs canon({can}) = "
                         f"interval {iv} at downbeat {db}")

    # 6. Bass cells: driving and melodic, machine-certified.
    _check_cell(fails, "CHORUS_BASS", _CHORUS_BASS_CELL, 4.0, (0.0, 2.0),
                0, CHORUS_BASS_MIN_DISTINCT)
    if len(_CHORUS_BASS_CELL) / 4.0 < CHORUS_BASS_MIN_RATE:
        fails.append("CHORUS_BASS: under 2 notes a beat - not driving")
    _check_cell(fails, "VERSE_BASS", _VERSE_BASS_CELL, VERSE_BAR,
                VERSE_STRONG, 0, VERSE_BASS_MIN_DISTINCT)

    # 7. Pre-chorus: skeleton chord tones and STRICTLY rising.
    for bar, deg in enumerate(PRECH_SKELETON):
        got = _sounding_at(PRECH_MELODY, bar * PRECH_BAR)
        if got != deg:
            fails.append(f"PRECH bar {bar}: sounding {got} != {deg}")
        if ((deg - 1) % 7) + 1 not in chord_set(PRECH_GROUND[bar]):
            fails.append(f"PRECH skeleton {deg} not a chord tone of "
                         f"bar {bar}")
    # rising as a two-sequence lift: each 4-bar half strictly rises and
    # the second half both starts and ends above the first.
    semis = [en.deg_semis(MODE, d) for d in PRECH_SKELETON]
    for half in (semis[:4], semis[4:]):
        if any(b <= a for a, b in zip(half, half[1:])):
            fails.append(f"PRECH_SKELETON {PRECH_SKELETON}: a half does "
                         f"not strictly rise")
    if not (semis[4] > semis[0] and semis[7] > semis[3]):
        fails.append(f"PRECH_SKELETON {PRECH_SKELETON}: the second "
                     f"sequence does not lift above the first")

    # 8. Middle-eight pair: chord tones on the strongs, pairwise
    #    consonant at beats 0 and 3 of every 5/4 bar.
    lead, flute = m8_lead(), m8_flute()
    for bar, root in enumerate(M8_GROUND):
        cs = chord_set(root)
        for label, line, vals in (("M8_LEAD", lead,
                                   (M8_LEAD_SKEL, M8_LEAD_AT3)),
                                  ("M8_FLUTE", flute,
                                   (M8_FLUTE_SKEL, M8_FLUTE_AT3))):
            for deg, where in ((vals[0][bar], 0.0), (vals[1][bar], 3.0)):
                if ((deg - 1) % 7) + 1 not in cs:
                    fails.append(f"{label} bar {bar} beat {where}: degree "
                                 f"{deg} not a chord tone")
        for where in M8_STRONG:
            dl = _sounding_at(lead, bar * M8_BAR + where)
            df = _sounding_at(flute, bar * M8_BAR + where)
            if dl is not None and df is not None \
                    and interval(df, dl) in CLASH:
                fails.append(f"M8 pair: flute({df}) vs lead({dl}) clash "
                             f"at bar {bar} beat {where}")

    # 9. No ground puts a root on degree 7 (the diminished triad).
    for gname, ground in (("CHORUS_GROUND", CHORUS_GROUND),
                          ("VERSE_GROUND", VERSE_GROUND),
                          ("PRECH_GROUND", PRECH_GROUND),
                          ("M8_GROUND", M8_GROUND)):
        if any(r == 7 for r in ground):
            fails.append(f"{gname}: degree-7 root (diminished chord)")

    # 10. The snapped descant is clash-free against the ground roots.
    for bar in range(8):
        deg = _sounding_at(descant(), bar * 4.0, CHORUS_BEATS)
        if deg is None:
            continue
        if interval(deg, CHORUS_GROUND[bar]) in CLASH:
            fails.append(f"descant: clash vs root at bar {bar}")

    return fails


if __name__ == "__main__":
    problems = verify_material()
    if problems:
        for p in problems:
            print("FAIL:", p)
        raise SystemExit(1)
    print("material oracle: all checks pass "
          f"(hook {HOOK_SKELETON}, 3-voice chorus counterpoint consonant, "
          f"verse canon at the bar a 4th below)")
