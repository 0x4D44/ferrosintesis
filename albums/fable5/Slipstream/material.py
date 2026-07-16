"""material.py — the shared musical DNA of *Slipstream*.

Everything that recurs across tracks lives HERE as data, and every claim the
album makes about that data is proven numerically by verify_material() —
written BEFORE the music, composed-to-pass (the repo method).  Track modules
import these objects; cross-track recurrences are recomputed from THIS file,
never re-typed.

The through-lines:

- ASCENT_CELL     the album's signature: three stacked-fifth pickups and a
                  hang — 0, +7, +12, +19 semitones, the last note held.  A
                  power-chord climb, guitar-idiomatic, mode-agnostic.  Stated
                  by the duo in T1, tumbled in T5, augmented four-fold by
                  choir and brass in T10's flypast.
- THE DUO         two overdriven guitars (ch14 lead ship, ch15 wing ship).
                  material provides the mirror arithmetic the formation
                  oracles share; each track pins its own formation.
- FILL_LIB        an eight-shape drum-fill library (melodic tom GM117 +
                  synth drum GM118).  Shapes A-F are inherited verbatim from
                  Three-Sixty-One's fill bed (the direct lineage); G and H
                  are new.  Every track schedules these shapes into verified
                  escalations.
- T361 quotes     the Three-Sixty-One references, pinned to the exact data
                  of albums/fable5/Through Lines: the ORBIT riff (quoted as
                  the searchlight in T9 and in T10's flypast stack) and the
                  SCREAM (the bent A6 peak, reprised by T10's lead guitar).
- Morse lanes     WHEELS UP (T1's radio chatter), CLEAR SKIES (T10's
                  sign-off).
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# The ASCENT cell.  Semitones above the local root; three eighth-note
# pickups climbing two stacked fifths, then the top held ("climb and hang").
# Interval walk +7, +5, +7 — a P5, its inversion, a P5 again — so the cell
# outlines root/fifth/octave/twelfth: pure power-chord geometry that reads
# identically in aeolian, dorian, phrygian and lydian contexts.
# ---------------------------------------------------------------------------

ASCENT_CELL: list[tuple[float, float, int]] = [
    # (onset_beats, dur_beats, semitones_above_root)
    (0.0, 0.5, 0),     # the root
    (0.5, 0.5, 7),     # +P5
    (1.0, 0.5, 12),    # +P4 (the octave)
    (1.5, 2.5, 19),    # +P5 (the twelfth) — the hang
]
ASCENT_LEN: float = 4.0


def ascent_pitches(root: int) -> list[int]:
    """The cell's four pitches above a MIDI root."""
    return [root + s for _, _, s in ASCENT_CELL]


def play_ascent(sc: en.Score, ch: int, t0: float, root: int,
                stretch: float = 1.0, vel: int = 90,
                vel_end: int | None = None, gate: float = 1.0,
                jt: int = 0, jv: int = 3) -> float:
    """Play the ASCENT cell; returns the end beat.

    `stretch` scales time (4.0 = the T10 flypast augmentation).  Velocity
    ramps linearly vel->vel_end across the cell when vel_end is given.
    jt defaults to 0 so oracle-pinned statements stay tick-exact.
    """
    total = ASCENT_LEN * stretch
    for on, du, semi in ASCENT_CELL:
        v = vel
        if vel_end is not None and total > 0:
            v = round(en.lerp(vel, vel_end, (on * stretch) / total))
        sc.note(ch, root + semi, t0 + on * stretch, du * stretch * gate,
                v, jt=jt, jv=jv)
    return t0 + total


# ---------------------------------------------------------------------------
# The duo arithmetic.  mirror() is the shared reflection every formation
# oracle uses (T6's inverted canon, T4's loop inversion): a pitch reflected
# about a fixed axis, in SEMITONE space (the exact mirror; the composer
# chooses an axis that keeps the image diatonically consonant on downbeats).
# ---------------------------------------------------------------------------

def mirror(p: int, axis: float) -> int:
    """Reflect MIDI pitch `p` about `axis` (may be half-integral)."""
    return int(round(2 * axis - p))


# ---------------------------------------------------------------------------
# The fill library.  Each shape is (offset, pitch, dur, vel) per lane —
# "tom" = melodic tom (GM117), "syn" = synth drum (GM118).  Tom pitches live
# in 44..64, syn in 46..60.  jt=0 when played keeps shape signatures exact
# for the per-track variety oracles.  A-F inherited note-for-note from
# Three-Sixty-One's fill bed; G "cascade" and H "stutter" are Slipstream's.
# ---------------------------------------------------------------------------

FILL_LIB: dict[str, dict[str, list[tuple[float, int, float, int]]]] = {
    "A": {  # "comma" — a 1-beat punctuation mark (3 notes)
        "tom": [(0.00, 60, 0.20, 76), (0.50, 55, 0.20, 82)],
        "syn": [(0.75, 52, 0.20, 88)]},
    "B": {  # "descend" — the house DNA (8 notes)
        "tom": [(0.00, 62, 0.20, 84), (0.50, 58, 0.20, 87),
                (0.75, 55, 0.20, 90), (1.00, 53, 0.20, 93),
                (1.50, 50, 0.20, 96), (1.75, 46, 0.20, 99)],
        "syn": [(1.25, 52, 0.20, 92), (1.75, 55, 0.20, 98)]},
    "C": {  # "lift" — an ASCENDING inversion of the DNA (9 notes)
        "tom": [(0.00, 46, 0.20, 72), (0.25, 50, 0.20, 76),
                (0.50, 53, 0.20, 80), (0.75, 55, 0.20, 84),
                (1.00, 58, 0.20, 88), (1.25, 60, 0.20, 92),
                (1.50, 62, 0.20, 96)],
        "syn": [(1.50, 50, 0.20, 90), (1.75, 57, 0.20, 98)]},
    "D": {  # "gallop" — syncopated high-low pairs (8 notes)
        "tom": [(0.00, 55, 0.18, 84), (0.25, 55, 0.18, 72),
                (0.75, 50, 0.18, 84), (1.00, 50, 0.18, 72),
                (1.50, 58, 0.18, 88), (1.75, 58, 0.18, 76)],
        "syn": [(0.50, 52, 0.18, 86), (1.25, 55, 0.18, 90)]},
    "E": {  # "roll-drop" — a one-pitch pressure roll then the floor drops (11)
        "tom": [(0.25 * i, 53, 0.18, 70 + 4 * i) for i in range(8)]
               + [(2.00, 50, 0.22, 100), (2.50, 46, 0.22, 104)],
        "syn": [(2.75, 58, 0.20, 102)]},
    "F": {  # "sputter" — double-stroke 32nd pairs (8 notes)
        "tom": [(0.000, 58, 0.12, 86), (0.125, 58, 0.12, 70),
                (0.500, 55, 0.12, 86), (0.625, 55, 0.12, 70),
                (1.000, 50, 0.12, 88), (1.125, 50, 0.12, 72)],
        "syn": [(1.50, 46, 0.20, 90), (1.75, 53, 0.20, 96)]},
    "G": {  # "cascade" — Slipstream: a strictly-falling 32nd waterfall (9),
            # tom and syn interleaved so the merged line descends unbroken
        "tom": [(0.000, 64, 0.14, 78), (0.250, 58, 0.14, 82),
                (0.500, 54, 0.14, 86), (0.750, 50, 0.14, 90),
                (1.000, 46, 0.16, 96)],
        "syn": [(0.125, 60, 0.14, 80), (0.375, 56, 0.14, 84),
                (0.625, 52, 0.14, 88), (0.875, 48, 0.14, 92)]},
    "H": {  # "stutter" — Slipstream: two triplet bursts and a floor hit (8)
        "syn": [(0 / 6, 55, 0.11, 88), (1 / 6, 55, 0.11, 72),
                (2 / 6, 55, 0.11, 80),
                (3 / 6, 50, 0.11, 92), (4 / 6, 50, 0.11, 76),
                (5 / 6, 50, 0.11, 84)],
        "tom": [(1.00, 46, 0.20, 98), (1.25, 44, 0.22, 104)]},
}


def play_fill(sc: en.Score, shape: str, t0: float, vbump: int = 0,
              ch_tom: int = 10, ch_syn: int = 11) -> None:
    """Play one library shape at beat t0 (velocity +vbump, capped 112)."""
    lib = FILL_LIB[shape]
    for off, p, dur, vel in lib.get("tom", ()):
        sc.note(ch_tom, p, t0 + off, dur, min(112, vel + vbump), jt=0, jv=4)
    for off, p, dur, vel in lib.get("syn", ()):
        sc.note(ch_syn, p, t0 + off, dur, min(112, vel + vbump), jt=0, jv=4)


def fill_note_count(shape: str) -> int:
    lib = FILL_LIB[shape]
    return len(lib.get("tom", ())) + len(lib.get("syn", ()))


# ---------------------------------------------------------------------------
# The Three-Sixty-One quotes — pinned VERBATIM to the data of
# albums/fable5/Through Lines (material.ORBIT_RIFF and the t16 finale peak).
# verify_material() asserts these literals never drift; the quoting tracks'
# oracles assert their notes match THESE constants, so the reference is
# provably the real thing, not a paraphrase.
# ---------------------------------------------------------------------------

# Through Lines material.py: ORBIT_RIFF / ORBIT_STEP / ORBIT_MODE.
ORBIT_RIFF_361: list[int] = [1, 5, 8, 10, 12, 10, 8, 5]
ORBIT_STEP_361 = 0.25
ORBIT_MODE_361 = "aeolian"

# Through Lines t16 finale: the peak A6 scream at beat 602 — approached from
# B5, landed on A6, with +2-semitone bend flicks between the downbeats.
SCREAM_APPROACH_361 = 91          # B5
SCREAM_PEAK_361 = 93              # A6
SCREAM_BEND_361 = 2.0             # the full-up flick, integer plateau


# ---------------------------------------------------------------------------
# Morse lanes.  Standard timing: dit = 1 unit on, dah = 3 on, 1 off between
# symbols, 3 off between letters, 7 off between words.
# ---------------------------------------------------------------------------

MORSE_TABLE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
}

MORSE_T1 = "WHEELS UP"       # T1's radio chatter
MORSE_T10 = "CLEAR SKIES"    # T10's sign-off


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
# verify_material — every claim above, proven numerically.
# ---------------------------------------------------------------------------

def verify_material() -> list[str]:
    fails: list[str] = []

    # --- ASCENT cell ---
    semis = [s for _, _, s in ASCENT_CELL]
    diffs = [b - a for a, b in zip(semis, semis[1:])]
    if diffs != [7, 5, 7]:
        fails.append(f"ASCENT intervals {diffs} != [7, 5, 7]")
    if any(b <= a for a, b in zip(semis, semis[1:])):
        fails.append("ASCENT must strictly rise")
    if semis[-1] - semis[0] != 19:
        fails.append(f"ASCENT span {semis[-1] - semis[0]} != 19 (a twelfth)")
    onsets = [on for on, _du, _s in ASCENT_CELL]
    if onsets != [0.0, 0.5, 1.0, 1.5]:
        fails.append(f"ASCENT pickups not contiguous eighths: {onsets}")
    durs = [du for _on, du, _s in ASCENT_CELL]
    if durs[-1] <= max(durs[:-1]):
        fails.append("ASCENT hang must be the longest note")
    if max(on + du for on, du, _s in ASCENT_CELL) != ASCENT_LEN:
        fails.append("ASCENT cell length != 4 beats")

    # --- mirror arithmetic ---
    for p in (40, 64, 76, 93):
        for axis in (63.0, 63.5, 70.0):
            if mirror(mirror(p, axis), axis) != p:
                fails.append(f"mirror not an involution at p={p} axis={axis}")
    if mirror(64, 64.0) != 64:
        fails.append("mirror must fix its own axis")
    if mirror(60, 63.5) != 67 or mirror(67, 63.5) != 60:
        fails.append("half-integral axis reflection wrong")

    # --- fill library ---
    if sorted(FILL_LIB) != list("ABCDEFGH"):
        fails.append(f"fill shapes {sorted(FILL_LIB)} != A..H")
    sigs = set()
    for shape, lanes in FILL_LIB.items():
        notes = [(off, p, dur, vel, lane)
                 for lane in ("tom", "syn")
                 for off, p, dur, vel in lanes.get(lane, ())]
        if not 3 <= len(notes) <= 11:
            fails.append(f"shape {shape}: {len(notes)} notes outside 3..11")
        for off, p, dur, vel, lane in notes:
            if dur > 0.25:
                fails.append(f"shape {shape}: dur {dur} > 0.25 (not a fill)")
            lo, hi = (44, 64) if lane == "tom" else (46, 60)
            if not lo <= p <= hi:
                fails.append(f"shape {shape}: {lane} pitch {p} outside "
                             f"[{lo},{hi}]")
        sig = tuple(sorted((off, p, lane) for off, p, _d, _v, lane in notes))
        if sig in sigs:
            fails.append(f"shape {shape} duplicates another shape")
        sigs.add(sig)
    roll = [vel for _off, _p, _d, vel in FILL_LIB["E"]["tom"][:8]]
    if any(b <= a for a, b in zip(roll, roll[1:])):
        fails.append("shape E roll velocities must strictly rise")
    g_all = sorted((off, p) for lane in ("tom", "syn")
                   for off, p, _d, _v in FILL_LIB["G"][lane])
    if any(p2 >= p1 for (_o1, p1), (_o2, p2) in zip(g_all, g_all[1:])):
        fails.append("shape G cascade must strictly descend in onset order")
    h_on = sorted(off for off, _p, _d, _v in FILL_LIB["H"]["syn"])
    gaps = [round(b - a, 6) for a, b in zip(h_on, h_on[1:])]
    if any(abs(g - 1 / 6) > 1e-6 for g in gaps):
        fails.append(f"shape H bursts not triplet-spaced: {gaps}")

    # --- the T361 quotes (verbatim pins) ---
    if ORBIT_RIFF_361 != [1, 5, 8, 10, 12, 10, 8, 5]:
        fails.append("ORBIT_RIFF_361 drifted from Through Lines")
    if ORBIT_STEP_361 != 0.25 or ORBIT_MODE_361 != "aeolian":
        fails.append("orbit quote step/mode drifted")
    triad_pcs = {en.deg_semis(ORBIT_MODE_361, d) % 12 for d in (1, 3, 5)}
    for d in ORBIT_RIFF_361:
        if en.deg_semis(ORBIT_MODE_361, d) % 12 not in triad_pcs:
            fails.append(f"orbit quote degree {d} not a tonic-triad tone")
    if (SCREAM_APPROACH_361, SCREAM_PEAK_361) != (91, 93):
        fails.append("scream quote pitches drifted (want B5 -> A6)")
    if SCREAM_PEAK_361 - SCREAM_APPROACH_361 != 2:
        fails.append("scream approach must sit a whole tone under the peak")
    if SCREAM_BEND_361 != 2.0:
        fails.append("scream bend must be the +2 integer plateau")

    # --- morse ---
    for text in (MORSE_T1, MORSE_T10):
        for chx in text:
            if chx != " " and chx not in MORSE_TABLE:
                fails.append(f"morse text {text!r}: no code for {chx!r}")
    if morse_rhythm("E", 0.25) != [(0.0, 0.25)]:
        fails.append("morse: E must be a single dit")
    if morse_rhythm("T", 0.25) != [(0.0, 0.75)]:
        fails.append("morse: T must be a single dah")
    if len(morse_rhythm(MORSE_T1)) != 23:
        fails.append(f"WHEELS UP has {len(morse_rhythm(MORSE_T1))} "
                     f"symbols, want 23")

    return fails
