"""material.py — the shared musical DNA of *Through Lines*.

Everything that recurs across tracks lives HERE as data, and every claim the
album makes about that data is proven numerically by verify_material() —
written BEFORE the music, composed-to-pass (the repo method). Track modules
import these objects; the cross-track "through-line" oracles in each track's
module compare the track's notes against THIS file, never against another
track's rendered output.

The through-lines:
- FABLE_CELL      F-A-Bb-(rest)-E: the album's signature. The L is silent —
                  scored as a half-beat rest where the fourth letter would
                  sing. Stated in T1, ground bass of T14(g), augmented 4x as
                  the music-box melody of T15.
- BRIDGE_CHORALE  a fragile 8-chord aeolian hymn. Interrupted mid-phrase
                  throughout T4 (Fault Lines); returns UNBROKEN at the dawn
                  of T7 (German Bight).
- WALKER_THEME    the slackline melody of T9, confined to a perfect fifth;
                  recalled in T10's finale stack.
- DIVE_CASCADE    T8's plunge figure; recalled in T10's finale stack.
- ORBIT_RIFF      T10's rotating arp cell.
- LEDGER_THEME    T14(a)'s ballad melody; quoted, truncated mid-phrase, by
                  the hidden epilogue T14(i).
- Morse lanes     CLAUDE (T2's theme rhythm), HOLD THE LINE (T4),
                  GERMAN BIGHT (T7), GOODNIGHT (T15).
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# The FABLE cell.  Semitones above the local root; the rest at [2.0, 2.5)
# is the silent L.  F->A +4 (major third), A->Bb +1 (semitone), Bb->E +6
# (the tritone that gives the cell its bite; its E->F resolution gives the
# closer its tenderness).
# ---------------------------------------------------------------------------

FABLE_CELL: list[tuple[float, float, int]] = [
    # (onset_beats, dur_beats, semitones_above_root)
    (0.0, 1.0, 0),    # F
    (1.0, 0.5, 4),    # A
    (1.5, 0.5, 5),    # Bb
    (2.5, 1.5, 11),   # E   (the L before it is silent: rest [2.0, 2.5))
]
FABLE_SILENT_L: tuple[float, float] = (2.0, 2.5)
FABLE_LEN: float = 4.0


def fable_pitches(root: int) -> list[int]:
    """The cell's four pitches above a MIDI root (F recommended)."""
    return [root + s for _, _, s in FABLE_CELL]


def play_cell(sc: en.Score, ch: int, t0: float, root: int,
              cell: list[tuple[float, float, int]] = None,
              stretch: float = 1.0, vel: int = 90, vel_end: int = None,
              gate: float = 1.0, jt: int = 5, jv: int = 4) -> float:
    """Play a (onset, dur, semis) cell; returns the end beat.

    `stretch` scales time (4.0 = the T15 augmentation). Velocity ramps
    linearly vel->vel_end across the cell when vel_end is given.
    """
    if cell is None:
        cell = FABLE_CELL
    total = max(on + du for on, du, _ in cell) * stretch
    for on, du, semi in cell:
        v = vel
        if vel_end is not None and total > 0:
            v = round(en.lerp(vel, vel_end, (on * stretch) / total))
        sc.note(ch, root + semi, t0 + on * stretch, du * stretch * gate,
                v, jt=jt, jv=jv)
    return t0 + total


# ---------------------------------------------------------------------------
# The bridge chorale.  Eight chords, two phrases, aeolian, SATB as scale
# degrees (engine degree arithmetic: deg 8 = tonic+octave, deg 0 = seventh
# below, any int valid).  Each chord holds 2 beats; the whole hymn is 16.
# Composed to pass verify_material's consonance/voice-leading oracle.
# ---------------------------------------------------------------------------

CHORALE_MODE = "aeolian"
CHORALE_CHORD_BEATS = 2.0
# ((S, A, T, B) degrees, chord-tone degree set (1-7))
BRIDGE_CHORALE: list[tuple[tuple[int, int, int, int], tuple[int, ...]]] = [
    ((10, 8, 5, 1),   (1, 3, 5)),   # i
    ((10, 8, 6, -1),  (6, 1, 3)),   # VI
    ((12, 10, 7, -4), (3, 5, 7)),   # III
    ((11, 9, 7, -5),  (7, 2, 4)),   # VII
    ((11, 8, 6, -3),  (4, 6, 1)),   # iv
    ((9, 7, 5, -2),   (5, 7, 2)),   # v
    ((8, 6, 3, -1),   (6, 1, 3)),   # VI
    ((8, 5, 3, 1),    (1, 3, 5)),   # i
]


def chorale_pitches(root: int) -> list[tuple[int, int, int, int]]:
    """The chorale as MIDI pitches (S, A, T, B) above a tonic MIDI root."""
    return [tuple(en.pitch(root, CHORALE_MODE, d) for d in satb)
            for satb, _tones in BRIDGE_CHORALE]


def play_chorale(sc: en.Score, channels, t0: float, root: int,
                 chord_beats: float = CHORALE_CHORD_BEATS, vel: int = 64,
                 n_chords: int = None, gate: float = 0.98,
                 jt: int = 4, jv: int = 3) -> float:
    """Play the chorale (optionally truncated to n_chords — T4's cut-offs).

    `channels` is one int (all four voices on one channel) or a (S, A, T, B)
    tuple of channels.  Returns the end beat.
    """
    chords = chorale_pitches(root)
    if n_chords is not None:
        chords = chords[:n_chords]
    if isinstance(channels, int):
        channels = (channels,) * 4
    t = t0
    for satb in chords:
        for voice, p in enumerate(satb):
            sc.note(channels[voice], p, t, chord_beats * gate, vel,
                    jt=jt, jv=jv)
        t += chord_beats
    return t


# ---------------------------------------------------------------------------
# Fine Line trilogy motifs.
# ---------------------------------------------------------------------------

# T9: the walker — one 5/8+6/8 cycle (eleven eighths), confined to a perfect
# fifth (degrees 1..5 aeolian = 0..7 semitones: the wire).
WALKER_THEME: list[int] = [1, 2, 3, 2, 1,   3, 4, 5, 4, 3, 2]
WALKER_STEP = 0.5              # each entry an eighth
WALKER_MODE = "aeolian"
WALKER_CYCLE_BEATS = 5.5       # 5/8 bar + 6/8 bar

# T8: the plunge — one strictly-descending octave of sixteenths; the
# composer repeats it at successively lower octaves for the four-octave fall.
DIVE_CASCADE: list[int] = [8, 7, 6, 5, 4, 3, 2, 1]
DIVE_STEP = 0.25
DIVE_MODE = "aeolian"

# T10: the orbit — an eight-sixteenth tonic-triad arp cell that rises and
# falls while its pan sweeps the theatre.
ORBIT_RIFF: list[int] = [1, 5, 8, 10, 12, 10, 8, 5]
ORBIT_STEP = 0.25
ORBIT_MODE = "aeolian"


# ---------------------------------------------------------------------------
# T14(a) "The Ledger" — the suite's opening ballad melody (aeolian).  Four
# 4/4 bars; ends on degree 2, unresolved (wistful).  The hidden epilogue
# T14(i) quotes bars 1-2 and is cut off inside bar 3.
# ---------------------------------------------------------------------------

LEDGER_THEME: list[tuple[int, float]] = [
    # (degree, dur_beats) — bar 1
    (5, 1.5), (4, 0.5), (3, 1.0), (2, 1.0),
    # bar 2
    (4, 1.5), (3, 0.5), (2, 1.0), (1, 1.0),
    # bar 3
    (3, 1.5), (2, 0.5), (1, 1.0), (0, 1.0),
    # bar 4
    (2, 4.0),
]
LEDGER_MODE = "aeolian"
LEDGER_BEATS = 16.0
# The epilogue plays entries [0:10] — it dies away inside bar 3.
LEDGER_EPILOGUE_NOTES = 10


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

MORSE_T2 = "CLAUDE"          # the theme rhythm of Scaling Laws
MORSE_T4 = "HOLD THE LINE"   # Fault Lines' news ticker
MORSE_T7 = "GERMAN BIGHT"    # the coastal station in the eye of the storm
MORSE_T15 = "GOODNIGHT"      # Landing Lights' last whisper


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

# Interval classes (mod 12) consonant against ANY voice; 5 (perfect fourth)
# is consonant only between upper voices (bass not in the pair).
_CONSONANT = {0, 3, 4, 7, 8, 9}


def verify_material() -> list[str]:
    fails: list[str] = []

    # --- FABLE cell ---
    semis = [s for _, _, s in FABLE_CELL]
    diffs = [b - a for a, b in zip(semis, semis[1:])]
    if diffs != [4, 1, 6]:
        fails.append(f"FABLE intervals {diffs} != [4, 1, 6]")
    if FABLE_CELL[2][0] + FABLE_CELL[2][1] != FABLE_SILENT_L[0]:
        fails.append("FABLE: Bb must end exactly where the silent L begins")
    if FABLE_CELL[3][0] != FABLE_SILENT_L[1]:
        fails.append("FABLE: E must start exactly where the silent L ends")
    if FABLE_SILENT_L[1] - FABLE_SILENT_L[0] != 0.5:
        fails.append("FABLE: the silent L must last half a beat")
    if max(on + du for on, du, _ in FABLE_CELL) != FABLE_LEN:
        fails.append("FABLE: cell length != 4 beats")

    # --- bridge chorale ---
    if len(BRIDGE_CHORALE) != 8:
        fails.append(f"chorale has {len(BRIDGE_CHORALE)} chords, want 8")
    prev_s = None
    for idx, (satb, tones) in enumerate(BRIDGE_CHORALE):
        p = [en.deg_semis(CHORALE_MODE, d) for d in satb]
        if not (p[0] > p[1] > p[2] > p[3]):
            fails.append(f"chorale chord {idx + 1}: voices not S>A>T>B: {p}")
        tone_pcs = {en.deg_semis(CHORALE_MODE, d) % 12 for d in tones}
        for vi, sp in enumerate(p):
            if sp % 12 not in tone_pcs:
                fails.append(f"chorale chord {idx + 1} voice {'SATB'[vi]} "
                             f"is not a chord tone")
        for a in range(4):
            for b in range(a + 1, 4):
                ic = (p[a] - p[b]) % 12
                ok = _CONSONANT | ({5} if b != 3 else set())
                if ic not in ok:
                    fails.append(f"chorale chord {idx + 1}: dissonance "
                                 f"{ic} between {'SATB'[a]}/{'SATB'[b]}")
        if prev_s is not None and abs(p[0] - prev_s) > 4:
            fails.append(f"chorale chord {idx + 1}: soprano leap "
                         f"{abs(p[0] - prev_s)} > 4 semitones")
        prev_s = p[0]
    first, last = BRIDGE_CHORALE[0], BRIDGE_CHORALE[-1]
    for which, (satb, _t) in (("first", first), ("last", last)):
        if en.deg_semis(CHORALE_MODE, satb[3]) % 12 != 0:
            fails.append(f"chorale {which} bass is not the tonic")
    if en.deg_semis(CHORALE_MODE, last[0][0]) % 12 != 0:
        fails.append("chorale must end with the soprano on the tonic")

    # --- walker ---
    wsem = [en.deg_semis(WALKER_MODE, d) for d in WALKER_THEME]
    if max(wsem) - min(wsem) > 7:
        fails.append(f"walker ambitus {max(wsem) - min(wsem)} exceeds a P5")
    if len(WALKER_THEME) != 11:
        fails.append("walker cycle must be eleven eighths (5/8 + 6/8)")
    if len(WALKER_THEME) * WALKER_STEP != WALKER_CYCLE_BEATS:
        fails.append("walker cycle beats inconsistent")
    for a, b in zip(wsem, wsem[1:]):
        if abs(b - a) > 3:
            fails.append(f"walker leap {abs(b - a)} > 3 semitones "
                         f"(the wire walk is stepwise)")

    # --- dive cascade ---
    dsem = [en.deg_semis(DIVE_MODE, d) for d in DIVE_CASCADE]
    if any(b >= a for a, b in zip(dsem, dsem[1:])):
        fails.append("dive cascade must strictly descend")
    if dsem[0] - dsem[-1] != 12:
        fails.append("dive cascade must span exactly one octave")

    # --- orbit riff ---
    triad_pcs = {en.deg_semis(ORBIT_MODE, d) % 12 for d in (1, 3, 5)}
    osem = [en.deg_semis(ORBIT_MODE, d) for d in ORBIT_RIFF]
    for d, s in zip(ORBIT_RIFF, osem):
        if s % 12 not in triad_pcs:
            fails.append(f"orbit riff degree {d} is not a tonic-triad tone")
    if len(ORBIT_RIFF) != 8:
        fails.append("orbit riff must be eight sixteenths")

    # --- ledger theme ---
    total = sum(du for _, du in LEDGER_THEME)
    if total != LEDGER_BEATS:
        fails.append(f"ledger theme is {total} beats, want {LEDGER_BEATS}")
    t = 0.0
    for deg, du in LEDGER_THEME:
        bar_pos = t % 4.0
        t += du
        if t > LEDGER_BEATS:
            fails.append("ledger theme overruns its four bars")
        del bar_pos, deg
    lsem = [en.deg_semis(LEDGER_MODE, d) for d, _ in LEDGER_THEME]
    if max(lsem) - min(lsem) > 12:
        fails.append("ledger theme exceeds an octave")
    if LEDGER_THEME[-1][0] != 2:
        fails.append("ledger theme must end on degree 2 (unresolved)")
    if not 8 <= LEDGER_EPILOGUE_NOTES < len(LEDGER_THEME):
        fails.append("epilogue quote must be a strict mid-phrase truncation")

    # --- morse ---
    events = morse_rhythm(MORSE_T2)
    if len(events) != 17:
        fails.append(f"CLAUDE has {len(events)} Morse symbols, want 17")
    for text in (MORSE_T2, MORSE_T4, MORSE_T7, MORSE_T15):
        for chx in text:
            if chx != " " and chx not in MORSE_TABLE:
                fails.append(f"morse text {text!r}: no code for {chx!r}")
    # dit:dah must be 1:3 and letters separated by 3 units
    if morse_rhythm("E", 0.25) != [(0.0, 0.25)]:
        fails.append("morse: E must be a single dit")
    tt = morse_rhythm("T", 0.25)
    if tt != [(0.0, 0.75)]:
        fails.append("morse: T must be a single dah")

    return fails
