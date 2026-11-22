"""T1 — First Lighting.  COMPOSER-NOTES §7/T1.

January dusk; chamber folk.  D dorian, quarter = 92, 4/4.  The keeper
strikes the lamp for the first time this year: one tubular-bell stroke alone,
then the BEAM unaccompanied on the piano, then the keeper's HYMN stated
plainly so the listener can learn it.

Architecture (114 bars, ~5:00):
  I.   Lamp and Beam        0-40    the LAMP bell alone; the BEAM on solo
                                    piano; the cello answers; a guitar vamp
                                    built from the BEAM figure
  II.  The Keeper's Hymn   40-112   the complete HYMN, plain, piano melody
                                    over fingerstyle guitar (+ a 2-bar link)
  III. Second Verse       112-184   the HYMN on violin with the clarinet's
                                    verified counter-melody; walking upright
                                    bass, flowing piano (+ a ii-V link to C)
  IV.  Thaw Light         184-312   the brighter middle in C: a new lilting
                                    tune (clarinet, then violin in sixths),
                                    a call-and-response bridge, the tune
                                    tutti, and a dominant retransition with
                                    the BEAM in the cello
  V.   The Hymn, Full     312-376   the HYMN tutti: violin + piano + clarinet
                                    on the tune, the counter-melody now in
                                    the cello, strings, strummed guitar,
                                    harp sweeps, brushes
  VI.  The Year Begins    376-456   the cadence phrase echoed; the BEAM in
                                    guitar, cello and piano; the lamp bell
                                    tolling every four bars to the end
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 1
TITLE = "First Lighting"
FILE = "01 - First Lighting.mid"
SEED = 20261201
COMMENT = ("Track 01 of 'Lantern Year' by Claude Fable 5: First Lighting - "
           "January dusk, chamber folk in D dorian.  The lamp bell alone, "
           "the BEAM on solo piano, the keeper's hymn stated plainly, a "
           "second verse with a clarinet counter-melody, a brighter middle "
           "in C, and the hymn again in full before the bell tolls the "
           "year in.")

MODE = "dorian"
TONIC = 62                       # D4
WHITE = {0, 2, 4, 5, 7, 9, 11}   # D dorian's pitch classes

PNO, VC, VN, CL, HP, GT, STR, BS, BELL, DR, PNL = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

T_LAMP, T_HYMN, T_LINK1, T_VAR, T_LINK2 = 0.0, 40.0, 104.0, 112.0, 176.0
T_MID, T_FULL, T_CODA, END = 184.0, 312.0, 376.0, 456.0
T_A2, T_B, T_A3, T_RETRANS = 216.0, 248.0, 280.0, 296.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Lamp and Beam", T_LAMP, T_HYMN),
        ("II. The Keeper's Hymn", T_HYMN, T_VAR),
        ("III. Second Verse", T_VAR, T_MID),
        ("IV. Thaw Light", T_MID, T_FULL),
        ("V. The Hymn, Full", T_FULL, T_CODA),
        ("VI. The Year Begins", T_CODA, END),
    ],
    tempo_map=[(0.0, 92.0), (424.0, 86.0), (440.0, 78.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],
    channels=[
        (PNO, "Piano (melody)", 0, 102, 64, 48),
        (VC, "Cello", 42, 104, 52, 55),
        (VN, "Violin", 40, 106, 78, 58),
        (CL, "Clarinet", 71, 112, 48, 55),
        (HP, "Harp", 46, 86, 88, 62),
        (GT, "Steel guitar (fingerstyle)", 25, 118, 40, 42),
        (STR, "Soft strings", 49, 78, 70, 70),
        (BS, "Upright bass", 32, 102, 64, 30),
        (BELL, "Lamp bell", material.LAMP_PROGRAM, 122, 64, 72),
        (DR, "Brushes", 0, 82, 64, 40),
        (PNL, "Piano (accompaniment)", 0, 90, 64, 48),
    ],
    program_changes=[(DR, 0.0, 40)],
    extra_markers=[(T_LINK2, "to C"), (T_A2, "tune, violin"),
                   (T_B, "bridge"), (T_A3, "tune, tutti"),
                   (T_RETRANS, "retransition")],
    bank_selects=[(GT, 1)],
)

BEAM_CHANNELS = {PNO, VC, GT}
PROGRAM_WHITELIST = {0, 42, 40, 71, 46, 25, 49, 32, material.LAMP_PROGRAM}
CENTERED_CHANNELS = {PNO, BS, BELL, DR, PNL}
NOTE_RANGES = {
    PNO: (48, 96), VC: (36, 67), VN: (55, 93), CL: (50, 84), HP: (36, 96),
    GT: (40, 76), STR: (43, 84), BS: (28, 55),
    BELL: (material.LAMP_PITCH, material.LAMP_PITCH), PNL: (33, 76),
}
GAP_WHITELIST: list = []
BEND_EXEMPT: set = set()
DURATION_WINDOW = (297.5, 305.5)
BOUNDS_WHITELIST: list = []

# ---------------------------------------------------------------------------
# Harmony.  A progression is [(onset, dur, chord, bass_pc_name)].
# ---------------------------------------------------------------------------

PCS = {
    "Dm": [2, 5, 9], "Dm7": [2, 5, 9, 0], "G": [7, 11, 2],
    "G7": [7, 11, 2, 5], "Em": [4, 7, 11], "Am": [9, 0, 4],
    "Am7": [9, 0, 4, 7], "C": [0, 4, 7], "Cmaj7": [0, 4, 7, 11],
    "F": [5, 9, 0], "Fmaj7": [5, 9, 0, 4], "D7": [2, 6, 9, 0],
    "Gsus": [7, 0, 2], "Asus": [9, 2, 4], "A": [9, 1, 4],
}


def _h(spec):
    out, t = [], 0.0
    for dur, name, bass in spec:
        out.append((t, float(dur), name, bass))
        t += dur
    return out


def _sub(prog, a, b):
    return [(on - a, dur, name, bass) for on, dur, name, bass in prog
            if a <= on < b]


# The hymn as material.py harmonises it: one chord per bar (bar 14 lets the
# melody's F take its own chord over the held A).
HYMN_PLAIN = _h([
    (4, "Dm", "D"), (4, "G", "G"), (4, "Dm", "D"), (4, "G", "G"),
    (4, "G", "G"), (4, "Em", "E"), (4, "Dm", "D"), (4, "Am", "A"),
    (4, "Dm", "D"), (4, "G", "G"), (4, "Dm", "D"), (4, "G", "G"),
    (4, "Dm", "D"), (2, "Am", "A"), (2, "F", "A"), (4, "Am", "A"),
    (4, "Dm", "D")])

# The same tune with the harmony moving twice a bar under a walking bass.
HYMN_RICH = _h([
    (2, "Dm", "D"), (2, "Dm", "F"), (2, "G", "G"), (2, "G", "B"),
    (2, "Dm", "D"), (2, "Dm7", "C"), (2, "G", "G"), (2, "Am7", "A"),
    (2, "Cmaj7", "C"), (2, "F", "F"), (2, "Em", "E"), (2, "Em", "G"),
    (2, "Dm", "D"), (2, "G", "B"), (2, "Am", "A"), (2, "Am", "E"),
    (2, "Dm", "D"), (2, "F", "F"), (2, "G", "G"), (2, "C", "C"),
    (2, "Dm", "F"), (2, "Dm", "D"), (2, "G", "G"), (2, "G", "B"),
    (4, "Dm", "D"), (2, "Am", "A"), (2, "F", "A"),
    (2, "C", "C"), (2, "Am", "A"), (4, "Dm", "D")])

MID_A = _h([(4, "C", "C"), (4, "G", "B"), (4, "Am", "A"), (4, "F", "F"),
            (4, "C", "E"), (4, "Dm7", "D"), (2, "C", "G"), (2, "Gsus", "G"),
            (4, "G", "G")])
MID_A2 = _h([(4, "C", "C"), (4, "G", "B"), (4, "Am", "A"), (4, "F", "F"),
             (4, "C", "E"), (4, "Dm7", "D"), (2, "C", "G"), (2, "G7", "G"),
             (4, "C", "C")])
MID_B = _h([(4, "F", "F"), (4, "G", "G"), (4, "Em", "E"), (4, "Am", "A"),
            (4, "F", "F"), (4, "D7", "F#"), (4, "Gsus", "G"),
            (4, "G7", "G")])
MID_A3 = _h([(4, "C", "C"), (4, "G", "B"), (4, "Am", "A"), (4, "F", "F")])
RETRANS = _h([(4, "Fmaj7", "F"), (4, "G", "G"), (4, "Asus", "A"),
              (2, "Asus", "A"), (2, "A", "A")])

# ---------------------------------------------------------------------------
# Lines (name, onset, dur) — or (degree, onset, dur) for the counter-melody.
# ---------------------------------------------------------------------------

# The counter-melody: consonant with the hymn on every half-bar, moving when
# the tune holds, mostly in contrary or oblique motion.  Degrees of D dorian.
COUNTER = [
    (3, 0, 1.5), (4, 1.5, .5), (3, 2, 1), (2, 3, 1),
    (1, 4, 2), (2, 6, 1), (1, 7, 1),
    (3, 8, 1), (5, 9, 1), (4, 10, .5), (3, 10.5, .5), (2, 11, 1),
    (1, 12, 1), (-1, 13, 1), (0, 14, 1), (1, 15, 1),
    (2, 16, 1.5), (1, 17.5, .5), (0, 18, 1), (2, 19, 1),
    (4, 20, 1.5), (3, 21.5, .5), (2, 22, 1), (0, 23, 1),
    (1, 24, 1.5), (0, 25.5, .5), (-1, 26, 1), (1, 27, 1),
    (0, 28, 1), (2, 29, 1), (5, 30, 1.5), (4, 31.5, .5),
    (5, 32, 2), (3, 34, 1), (2, 35, 1),
    (4, 36, 1), (5, 37, 1), (4, 38, 1), (2, 39, 1),
    (1, 40, 1), (3, 41, 1), (5, 42, 1), (4, 43, 1),
    (6, 44, 1.5), (5, 45.5, .5), (4, 46, 1), (2, 47, 1),
    (3, 48, 1), (2, 49, 1), (1, 50, 1.5), (0, 51.5, .5),
    (2, 52, 1), (1, 53, .5), (0, 53.5, .5), (-2, 54, 1), (-1, 55, 1),
    (0, 56, 1), (-1, 57, 1), (-2, 58, 1), (-1, 59, 1),
    (-2, 60, 1), (1, 61, 1), (3, 62, 2),
]

# Upright bass under the second verse: in two, with walk-ups.
BASS2 = [
    ("D2", 0, 2), ("F2", 2, 2), ("G2", 4, 2), ("B2", 6, 1), ("C3", 7, 1),
    ("D3", 8, 2), ("C3", 10, 2), ("G2", 12, 2), ("A2", 14, 2),
    ("C3", 16, 2), ("F2", 18, 2), ("E2", 20, 2), ("G2", 22, 1),
    ("E2", 23, 1), ("D2", 24, 2), ("B1", 26, 2), ("A1", 28, 2),
    ("E2", 30, 1), ("C2", 31, 1),
    ("D2", 32, 2), ("F2", 34, 2), ("G2", 36, 2), ("C3", 38, 2),
    ("F2", 40, 2), ("D2", 42, 1), ("F2", 43, 1), ("G2", 44, 2),
    ("B2", 46, 2), ("D3", 48, 3), ("B2", 51, 1), ("A2", 52, 3),
    ("B2", 55, 1), ("C3", 56, 2), ("A2", 58, 2), ("D2", 60, 2),
    ("A2", 62, 1), ("D3", 63, 1),
]

# ... and under the full hymn: walking in four, same harmonic skeleton.
_WALK = ("D2 E2 F2 A2  G2 A2 B2 C3  D3 A2 C3 A2  G2 B2 A2 B2 "
         "C3 G2 F2 A2  E2 B2 G2 E2  D2 F2 B1 D2  A1 C2 E2 C2 "
         "D2 A2 F2 A2  G2 B2 C3 E2  F2 A2 D2 F2  G2 D3 B2 C3 "
         "D3 A2 D3 B2  A2 E2 A2 B2  C3 G2 A2 E2  D2 A2").split()
BASS3 = [(nm, float(i), 1.0) for i, nm in enumerate(_WALK)] + [("D3", 62, 2)]

CELLO_II = [("G2", 16, 4), ("E2", 20, 4), ("D2", 24, 4), ("A2", 28, 4),
            ("D3", 32, 4), ("B2", 36, 4), ("D3", 40, 4), ("G2", 44, 4),
            ("D3", 48, 4), ("A2", 52, 4), ("A2", 56, 4), ("D2", 60, 4)]
CLAR_II = [("F4", 48, 2), ("G4", 50, 2), ("E4", 52, 2), ("C4", 54, 6),
           ("A3", 60, 4)]

# The middle's own tune (C major): a lilting dotted figure that never quotes
# the hymn.
TUNE_A = [
    ("E5", 0, 1.5), ("G5", 1.5, .5), ("E5", 2, 1), ("C5", 3, 1),
    ("D5", 4, 1.5), ("E5", 5.5, .5), ("D5", 6, 1), ("B4", 7, 1),
    ("C5", 8, 1.5), ("D5", 9.5, .5), ("E5", 10, 1), ("C5", 11, 1),
    ("A4", 12, 2), ("G4", 14, 1), ("A4", 15, 1),
    ("G4", 16, 1), ("C5", 17, 1), ("E5", 18, 1), ("G5", 19, 1),
    ("F5", 20, 1.5), ("E5", 21.5, .5), ("D5", 22, 1), ("C5", 23, 1),
    ("E5", 24, 1), ("D5", 25, 1), ("C5", 26, 2),
    ("B4", 28, 1.5), ("A4", 29.5, .5), ("G4", 30, 2),
]
TUNE_A2 = TUNE_A[:23] + [("E5", 24, 1.5), ("D5", 25.5, .5), ("B4", 26, 1),
                         ("D5", 27, 1), ("C5", 28, 3.5)]
HARM_A2 = [
    ("G4", 0, 1.5), ("B4", 1.5, .5), ("G4", 2, 1), ("E4", 3, 1),
    ("B4", 4, 1.5), ("C5", 5.5, .5), ("B4", 6, 1), ("G4", 7, 1),
    ("A4", 8, 1.5), ("B4", 9.5, .5), ("C5", 10, 1), ("A4", 11, 1),
    ("F4", 12, 2), ("E4", 14, 1), ("F4", 15, 1),
    ("E4", 16, 2), ("G4", 18, 2),
    ("A4", 20, 1.5), ("G4", 21.5, .5), ("F4", 22, 1), ("A4", 23, 1),
    ("G4", 24, 2), ("G4", 26, 1), ("F4", 27, 1), ("E4", 28, 3.5),
]
TUNE_A3 = TUNE_A[:12] + [("A4", 12, 2), ("C5", 14, 1), ("D5", 15, 1)]
HARM_A3 = HARM_A2[:12] + [("F4", 12, 2), ("A4", 14, 1), ("B4", 15, 1)]

BASS_A = [
    ("C2", 0, 1.5), ("G2", 1.5, .5), ("E2", 2, 1), ("C3", 3, 1),
    ("B2", 4, 1.5), ("D3", 5.5, .5), ("G2", 6, 1), ("B2", 7, 1),
    ("A2", 8, 1.5), ("E2", 9.5, .5), ("A2", 10, 1), ("G2", 11, 1),
    ("F2", 12, 1.5), ("C3", 13.5, .5), ("A2", 14, 1), ("F2", 15, 1),
    ("E2", 16, 1.5), ("G2", 17.5, .5), ("C3", 18, 1), ("E3", 19, 1),
    ("D3", 20, 1.5), ("A2", 21.5, .5), ("F2", 22, 1), ("D2", 23, 1),
    ("G2", 24, 1.5), ("D3", 25.5, .5), ("G2", 26, 2),
]
BASS_A_END = [("G2", 28, 1.5), ("D2", 29.5, .5), ("G2", 30, 1),
              ("B2", 31, 1)]
BASS_A2_END = [("C3", 28, 1.5), ("G2", 29.5, .5), ("C2", 30, 1),
               ("E2", 31, 1)]
BASS_B = [
    ("F2", 0, 1.5), ("C3", 1.5, .5), ("A2", 2, 1), ("F2", 3, 1),
    ("G2", 4, 1.5), ("D3", 5.5, .5), ("B2", 6, 1), ("G2", 7, 1),
    ("E2", 8, 1.5), ("B2", 9.5, .5), ("G2", 10, 1), ("E2", 11, 1),
    ("A2", 12, 1.5), ("E2", 13.5, .5), ("A2", 14, 1), ("G2", 15, 1),
    ("F2", 16, 1.5), ("C3", 17.5, .5), ("A2", 18, 1), ("F2", 19, 1),
    ("F#2", 20, 1.5), ("D3", 21.5, .5), ("A2", 22, 1), ("F#2", 23, 1),
    ("G2", 24, 2), ("D3", 26, 1), ("G2", 27, 1),
    ("G2", 28, 2), ("G2", 30, 1), ("B2", 31, 1),
]
BASS_RT = [
    ("F2", 0, 2), ("C3", 2, 1), ("F2", 3, 1), ("G2", 4, 2), ("D3", 6, 1),
    ("G2", 7, 1), ("A2", 8, 1.5), ("A2", 9.5, .5), ("A2", 10, 1),
    ("E2", 11, 1), ("A2", 12, 1), ("A2", 13, 1), ("A2", 14, 1),
    ("A1", 15, 1),
]

# ---------------------------------------------------------------------------
# Texture helpers
# ---------------------------------------------------------------------------


def _pc(name: str) -> int:
    return en.n(name + "4") % 12


def _fit(name: str, lo: int, hi: int) -> int:
    """The lowest pitch >= lo with this pitch class (must be <= hi)."""
    pc = _pc(name)
    p = lo + (pc - lo) % 12
    assert p <= hi, (name, lo, hi)
    return p


def _v(vel, vel_end, on, total) -> int:
    if vel_end is None:
        return int(vel)
    return int(round(en.lerp(vel, vel_end, on / max(1e-9, total))))


def _span(prog) -> float:
    return prog[-1][0] + prog[-1][1]


def seq(sc, ch, t0, notes, vel, vel_end=None, gate=0.96, jt=4, jv=4,
        transpose=0):
    total = max(on + du for _n, on, du in notes)
    for nm, on, du in notes:
        sc.note(ch, en.n(nm) + transpose, t0 + on, du * gate,
                _v(vel, vel_end, on, total), jt=jt, jv=jv)


def vib(sc, ch, t, dur, depth=0.1):
    """A bowed vibrato on notes long enough to want one (~5.4 Hz)."""
    if dur >= 2.0:
        en.vibrato(sc, ch, t, dur * 0.96, depth=depth, cycles_per_beat=3.5,
                   delay=0.45, step=0.04)


def sing(sc, ch, t0, notes, vel, vel_end=None, depth=0.1, gate=0.98):
    seq(sc, ch, t0, notes, vel, vel_end, gate=gate, jt=3, jv=3)
    for _nm, on, du in notes:
        vib(sc, ch, t0 + on, du, depth)


_FINGER = ["B", 1, 2, 1, "A", 0, 2, 1]


def guitar_finger(sc, t0, prog, vel, vel_end=None, lo=55, hi=69):
    """Fingerstyle: thumb on the bass and its alternate, fingers rolling
    the top three strings in eighths."""
    prev, total = None, _span(prog)
    for on, dur, name, bass in prog:
        pcs = PCS[name]
        up = en.voice_lead(pcs, prev, 3, lo, hi)
        prev = up
        b = _fit(bass, 40, 51)
        alt = min([p for p in range(b + 3, b + 13) if p % 12 in pcs],
                  key=lambda p: abs(p - (b + 7)))
        v = _v(vel, vel_end, on, total)
        for i in range(int(round(dur * 2))):
            what = _FINGER[i % 8]
            t = t0 + on + i * 0.5
            if what == "B":
                sc.note(GT, b, t, 1.9, v + 6)
            elif what == "A":
                sc.note(GT, alt, t, 1.9, v + 2)
            else:
                sc.note(GT, up[what], t, 0.95, v - (0 if i % 2 == 0 else 3))


def guitar_boomchick(sc, t0, prog, vel, vel_end=None):
    """Bass note on 1 and 3, a light brushed chord on 2 and 4."""
    prev, total = None, _span(prog)
    for on, dur, name, bass in prog:
        pcs = PCS[name]
        up = en.voice_lead(pcs, prev, 4, 52, 71)
        prev = up
        b = _fit(bass, 40, 51)
        alt = min([p for p in range(b + 3, b + 13) if p % 12 in pcs],
                  key=lambda p: abs(p - (b + 7)))
        v = _v(vel, vel_end, on, total)
        for k in range(int(round(dur))):
            t = t0 + on + k
            if k % 2 == 0:
                sc.note(GT, b if k % 4 == 0 else alt, t, 0.95, v + 5)
            else:
                en.strum(sc, GT, up, t, 0.9, v - 3, spread=0.022)


def guitar_strum(sc, t0, prog, vel, vel_end=None):
    """Full folk strumming: down on the beats, a light up-stroke on the
    'and' of 2 and 4."""
    prev, total = None, _span(prog)
    for on, dur, name, bass in prog:
        pcs = PCS[name]
        up = en.voice_lead(pcs, prev, 4, 52, 72)
        prev = up
        b = _fit(bass, 40, 51)
        chord = [b] + [p for p in up if p > b]
        v = _v(vel, vel_end, on, total)
        for k in range(int(round(dur))):
            t = t0 + on + k
            if k % 2 == 0:
                en.strum(sc, GT, chord, t, 0.95, v, spread=0.025)
            else:
                en.strum(sc, GT, up, t, 0.5, v - 9, spread=0.02)
                en.strum(sc, GT, up[1:], t + 0.5, 0.45, v - 17,
                         spread=0.015, down=False)


def piano_shell(sc, t0, prog, vel, vel_end=None):
    """Left hand for the plain hymn: a bass note, then a quiet held chord."""
    prev, total = None, _span(prog)
    for on, dur, name, bass in prog:
        up = en.voice_lead(PCS[name][:3], prev, 3, 55, 67)
        prev = up
        b = _fit(bass, 43, 54)
        v = _v(vel, vel_end, on, total)
        t = t0 + on
        en.sustain(sc, PNL, t + 0.03, t + dur - 0.08)
        sc.note(PNL, b, t, dur * 0.95, v + 3, jt=3)
        off = 2.0 if dur >= 4 else 1.0
        for p in up:
            sc.note(PNL, p, t + off, (dur - off) * 0.95, v - 7, jt=3)


_FLOW4 = ["B", 0, 2, 1]
_FLOW8 = ["B", 0, 2, 1, "A", 0, 2, 1]


def piano_flow(sc, t0, prog, vel, vel_end=None, lo=55, hi=69,
               octave=False):
    """Flowing broken chords in eighths under a per-chord pedal."""
    prev, total = None, _span(prog)
    for on, dur, name, bass in prog:
        pcs = PCS[name]
        up = en.voice_lead(pcs, prev, 3, lo, hi)
        prev = up
        b = _fit(bass, 41, 52)
        alt = min([p for p in range(b + 3, b + 13) if p % 12 in pcs],
                  key=lambda p: abs(p - (b + 7)))
        v = _v(vel, vel_end, on, total)
        t = t0 + on
        en.sustain(sc, PNL, t + 0.03, t + dur - 0.07)
        n8 = int(round(dur * 2))
        pat = _FLOW8 if n8 >= 8 else _FLOW4
        for i in range(n8):
            what = pat[i % len(pat)]
            tt = t + i * 0.5
            if what == "B":
                sc.note(PNL, b, tt, 1.8, v + 5)
                if octave and b - 12 >= 33:
                    sc.note(PNL, b - 12, tt, 1.8, v + 2)
            elif what == "A":
                sc.note(PNL, alt, tt, 0.9, v)
            else:
                sc.note(PNL, up[what], tt, 0.48,
                        v - (1 if i % 2 == 0 else 4))


def pad(sc, t0, prog, size, lo, hi, vel, vel_end=None):
    chords = []
    for _on, dur, name, _bass in prog:
        chords += [PCS[name]] * int(round(dur / 2))
    en.pad_block(sc, STR, t0, chords, 2.0, size=size, lo=lo, hi=hi,
                 vel=vel, vel_end=vel_end, legato=0.12)


def tenor_line(sc, ch, t0, prog, vel, vel_end=None, lo=50, hi=60,
               start=57):
    """A sustained inner voice: the nearest non-bass chord tone, tied
    through common tones."""
    picks: list = []
    prev = start
    for on, dur, name, bass in prog:
        bpc = _pc(bass)
        cands = [p for p in range(lo, hi + 1)
                 if p % 12 in PCS[name][:3] and p % 12 != bpc]
        if not cands:
            cands = [p for p in range(lo, hi + 1) if p % 12 in PCS[name]]
        p = min(cands, key=lambda q: (abs(q - prev), q))
        prev = p
        if picks and picks[-1][2] == p and picks[-1][1] < 8.0:
            picks[-1] = (picks[-1][0], picks[-1][1] + dur, p)
        else:
            picks.append((on, dur, p))
    total = _span(prog)
    for on, dur, p in picks:
        sc.note(ch, p, t0 + on, dur * 0.99, _v(vel, vel_end, on, total),
                jt=3, jv=3)


def chord_tones(name, lo, count):
    return [p for p in range(lo, lo + 48) if p % 12 in PCS[name][:3]][:count]


def harp_roll(sc, t, pitches, vel, spread=0.07, dur=3.0):
    for i, p in enumerate(pitches):
        sc.note(HP, p, t + i * spread, dur, vel + 2 * i, jt=2, jv=3)


def harp_run(sc, t, pitches, step, vel, vel_end):
    last = max(1, len(pitches) - 1)
    for i, p in enumerate(pitches):
        sc.note(HP, p, t + i * step, 1.5,
                int(round(en.lerp(vel, vel_end, i / last))), jt=2, jv=3)


def beam_vamp(sc, t0, roots, vel, vel_end=None):
    """The BEAM as a fingerstyle figure: 1-5-6-5-8 then 5-x-5, one bar per
    root (D dorian and G mixolydian share the white keys)."""
    total = 4.0 * len(roots)
    for i, root in enumerate(roots):
        mode = MODE if root % 12 == 2 else "mixolydian"
        cell = material.beam_pitches(root, mode)
        tail = [cell[1], cell[2] if root % 12 == 2 else root + 16, cell[1]]
        for k, p in enumerate(cell + tail):
            on = 4.0 * i + 0.5 * k
            sc.note(GT, p, t0 + on, 1.0 if k else 1.9,
                    _v(vel, vel_end, on, total) + (6 if k in (0, 4) else 0),
                    jt=3, jv=3)


def brushes(sc, t0, bars, vel, vel_end=None):
    for b in range(bars):
        t = t0 + 4.0 * b
        v = _v(vel, vel_end, 4.0 * b, 4.0 * bars)
        sc.hit(36, t, v - 6)
        sc.hit(36, t + 2.5, v - 16)
        sc.hit(38, t + 1.0, v - 4)
        sc.hit(38, t + 3.0, v - 2)
        for k in range(8):
            sc.hit(42, t + 0.5 * k, v - (20 if k % 2 == 0 else 28))
        if b % 4 == 3:
            sc.hit(38, t + 3.5, v - 16)
            sc.hit(38, t + 3.75, v - 10)


def expr(sc, ch, points):
    en.expr_curve(sc, ch, points, step=0.5)


def bell(sc, t, vel, dur=7.8):
    sc.note(BELL, material.LAMP_PITCH, t, dur, vel, jt=0, jv=0)


def counter(sc, ch, t0, base, vel, vel_end=None, lo=0.0, hi=64.0):
    """The counter-melody (or the slice of it inside [lo, hi))."""
    for d, on, du in COUNTER:
        if lo <= on < hi:
            sc.note(ch, en.pitch(base, MODE, d), t0 + on - lo, du * 1.02,
                    _v(vel, vel_end, on - lo, hi - lo), jt=0, jv=3)


DM9 = [50, 57, 62, 65, 69, 76]          # the lamp-room chord: D A D F A E


# ---------------------------------------------------------------------------
# Movement builders
# ---------------------------------------------------------------------------

def _b_lamp(sc: en.Score) -> None:
    """I — the lamp, alone; then the BEAM, alone; then the first answers."""
    bell(sc, 0.0, 98)
    en.sustain(sc, PNO, 8.0, 15.7)
    material.play_beam(sc, PNO, 8.0, 50, MODE, stretch=2.0, vel=46,
                       vel_end=60, gate=1.0, jt=0, jv=0)

    bell(sc, 16.0, 80)
    for ch in (VC, VN, CL):
        sc.cc(ch, 68, 127, 15.5)
    expr(sc, VC, [(15.5, 72), (20.0, 108), (24.0, 84), (30.0, 100),
                  (32.0, 82), (38.0, 104), (40.0, 88)])
    material.play_beam(sc, VC, 16.0, 38, MODE, stretch=2.0, vel=72,
                       vel_end=84, gate=1.0, jt=0, jv=2)
    harp_roll(sc, 20.0, DM9, 48)

    beam_vamp(sc, 24.0, [50, 43, 50, 43], 58, 66)
    sc.note(VC, 38, 24.0, 7.9, 60, jt=0)
    sc.note(VC, 43, 32.0, 7.9, 62, jt=0)
    expr(sc, STR, [(23.5, 40), (32.0, 74), (40.0, 60)])
    for p in (62, 69):
        sc.note(STR, p, 24.0, 8.0, 40, jt=0)
    for p in (62, 71):
        sc.note(STR, p, 32.0, 7.9, 42, jt=0)
    for t, nm in ((26.0, "A4"), (30.0, "D5"), (34.0, "B4"), (38.0, "D5")):
        sc.note(HP, en.n(nm), t, 2.0, 46)
    en.sustain(sc, PNL, 24.0, 39.8)
    for t, lo in ((24.0, 38), (32.0, 43)):
        sc.note(PNL, lo, t, 7.5, 40, jt=0)
        sc.note(PNL, lo + 7, t, 7.5, 38, jt=0)


def _b_hymn(sc: en.Score) -> None:
    """II — the keeper's hymn, plainly: piano tune, fingerstyle guitar."""
    t0 = T_HYMN
    for k, (a, b) in enumerate([(66, 70), (70, 70), (74, 82), (78, 68)]):
        material.play_phrase(sc, PNO, t0 + 16.0 * k, TONIC, MODE, k,
                             vel=a, vel_end=b, gate=0.98, jt=0, jv=2)
    piano_shell(sc, t0, HYMN_PLAIN, 44, 52)
    guitar_finger(sc, t0, HYMN_PLAIN, 56, 66)

    expr(sc, VC, [(t0 + 15.5, 70), (t0 + 24, 100), (t0 + 32, 84),
                  (t0 + 42, 112), (t0 + 48, 96), (t0 + 56, 104),
                  (t0 + 64, 84), (T_VAR, 90)])
    seq(sc, VC, t0, CELLO_II, 58, 66, gate=0.99, jt=0)

    for bar in range(8, 16):
        name = HYMN_PLAIN[bar if bar < 14 else bar + 1][2]
        harp_roll(sc, t0 + 4.0 * bar, chord_tones(name, 57, 4),
                  48 + (6 if bar in (10, 11) else 0))
    expr(sc, STR, [(t0 + 31.5, 48), (t0 + 42, 88), (t0 + 48, 76),
                   (t0 + 56, 84), (t0 + 64, 62), (T_VAR, 70)])
    pad(sc, t0 + 32, _sub(HYMN_PLAIN, 32, 64), 3, 57, 72, 40, 44)

    expr(sc, CL, [(t0 + 47.5, 62), (t0 + 52, 92), (t0 + 58, 80),
                  (t0 + 64, 56)])
    seq(sc, CL, t0, CLAR_II, 54, 48, gate=1.0, jt=0)

    # Two bars of the BEAM vamp: the guitar turns the page.
    link = _h([(4, "Dm", "D"), (4, "G", "G")])
    beam_vamp(sc, T_LINK1, [50, 43], 56, 62)
    piano_shell(sc, T_LINK1, link, 46)
    seq(sc, VC, T_LINK1, [("D2", 0, 4), ("G2", 4, 4)], 60, gate=0.99, jt=0)
    pad(sc, T_LINK1, link, 3, 57, 72, 40, 46)
    seq(sc, BS, T_LINK1, [("G2", 4, 2), ("E2", 6, 1), ("C2", 7, 1)], 70, 78,
        gate=0.92)
    harp_run(sc, T_LINK1 + 6.0,
             [en.n(x) for x in "A4 B4 C5 D5 E5 F5 G5 A5".split()],
             0.25, 42, 60)


def _b_variation(sc: en.Score) -> None:
    """III — second verse: violin tune, clarinet counter-melody."""
    t0 = T_VAR
    expr(sc, VN, [(t0 - 0.5, 86), (t0 + 8, 106), (t0 + 16, 92),
                  (t0 + 24, 104), (t0 + 32, 94), (t0 + 42, 122),
                  (t0 + 48, 104), (t0 + 56, 108), (t0 + 64, 88),
                  (t0 + 68, 100), (T_MID - 0.5, 74)])
    material.play_hymn(sc, VN, t0, TONIC + 12, MODE, vel=80, vel_end=90,
                       gate=1.02, jt=0, jv=2)
    for _d, on, du in material.HYMN:
        vib(sc, VN, t0 + on, du, 0.09)

    expr(sc, CL, [(t0 - 0.5, 80), (t0 + 10, 104), (t0 + 16, 88),
                  (t0 + 30, 110), (t0 + 32, 92), (t0 + 42, 118),
                  (t0 + 48, 100), (t0 + 62, 108), (t0 + 64, 90),
                  (T_MID - 2.0, 96), (T_MID, 112)])
    counter(sc, CL, t0, TONIC, 80, 88)

    piano_flow(sc, t0, HYMN_RICH, 48, 58)
    # The piano's right hand only answers when the tune holds.
    seq(sc, PNO, t0, [("A4", 29, .5), ("C5", 29.5, .5), ("E5", 30, .5),
                      ("A5", 30.5, 1.4)], 48, 54, jt=2)
    seq(sc, PNO, t0, [("D4", 60.5, .5), ("A4", 61, .5), ("B4", 61.5, .5),
                      ("A4", 62, .5), ("D5", 62.5, 1.4)], 48, 56, jt=0)

    guitar_boomchick(sc, t0, HYMN_RICH, 48, 56)
    seq(sc, BS, t0, BASS2, 76, 84, gate=0.92, jt=5)
    expr(sc, VC, [(t0, 84), (t0 + 12, 104), (t0 + 16, 88), (t0 + 42, 114),
                  (t0 + 64, 86), (T_MID, 92)])
    tenor_line(sc, VC, t0, HYMN_RICH, 58, 64)
    expr(sc, STR, [(t0, 66), (t0 + 14, 84), (t0 + 32, 76), (t0 + 42, 104),
                   (t0 + 64, 72), (T_MID - 1.0, 92), (T_MID, 60)])
    pad(sc, t0, HYMN_RICH, 3, 60, 76, 44, 52)
    for bar in range(8, 16):
        seg = [s for s in HYMN_RICH if s[0] <= 4.0 * bar < s[0] + s[1]][0]
        harp_roll(sc, t0 + 4.0 * bar, chord_tones(seg[2], 62, 4), 50)
    harp_run(sc, t0 + 30.0, [en.n(x) for x in "A3 E4 A4 C5".split()],
             0.5, 46, 54)

    # ii-V into C: the dusk brightens.
    link = _h([(4, "Dm7", "D"), (4, "G7", "G")])
    piano_flow(sc, T_LINK2, link, 54, 60)
    guitar_boomchick(sc, T_LINK2, link, 52, 58)
    seq(sc, BS, T_LINK2, [("D2", 0, 2), ("F2", 2, 2), ("G2", 4, 1.5),
                          ("G2", 5.5, .5), ("A2", 6, 1), ("B2", 7, 1)],
        78, 86, gate=0.92)
    sing(sc, VN, T_LINK2, [("A5", 0, 2), ("G5", 2, 2), ("F5", 4, 3.6)],
         78, 68, depth=0.09, gate=1.0)
    seq(sc, CL, T_LINK2, [("G4", 6.5, .5), ("C5", 7, .5), ("D5", 7.5, .5)],
        72, 80, gate=1.0, jt=2)
    tenor_line(sc, VC, T_LINK2, link, 60)
    pad(sc, T_LINK2, link, 3, 60, 76, 46, 54)
    harp_run(sc, T_LINK2 + 6.0,
             [en.n(x) for x in "G4 B4 D5 F5 G5 B5 D6 F6".split()],
             0.25, 40, 58)


def _b_middle(sc: en.Score) -> None:
    """IV — Thaw Light: C major, a tune of its own."""
    t0 = T_MID
    sc.cc(CL, 68, 0, t0 - 0.05)          # tongued, folk-style
    # A — clarinet tune over fingerstyle guitar and a bass in two.
    expr(sc, CL, [(t0, 104), (t0 + 6, 116), (t0 + 15, 100), (t0 + 20, 120),
                  (t0 + 31, 96), (T_A2, 92)])
    seq(sc, CL, t0, TUNE_A, 84, 88, gate=0.95, jt=3)
    guitar_finger(sc, t0, MID_A, 56, 60, lo=57, hi=72)
    seq(sc, BS, t0, BASS_A + BASS_A_END, 80, 84, gate=0.9)
    expr(sc, VC, [(t0, 88), (t0 + 16, 104), (t0 + 32, 90)])
    tenor_line(sc, VC, t0, MID_A, 56)
    seq(sc, PNO, t0, [("F5", 13, .5), ("A5", 13.5, .5), ("C6", 14, 1.5)],
        56, 62, jt=2)
    seq(sc, PNO, t0, [("D5", 29, .5), ("G5", 29.5, .5), ("B5", 30, 1.5)],
        56, 62, jt=2)
    for bar in (1, 3, 5, 7):
        seg = [s for s in MID_A if s[0] <= 4.0 * bar < s[0] + s[1]][0]
        harp_run(sc, t0 + 4.0 * bar + 2.0, chord_tones(seg[2], 64, 4),
                 0.5, 46, 54)

    # A2 — the violin takes it; the clarinet shadows in thirds and sixths.
    t = T_A2
    expr(sc, VN, [(t - 0.5, 96), (t + 6, 112), (t + 15, 98), (t + 20, 120),
                  (t + 32, 100)])
    sing(sc, VN, t, TUNE_A2, 86, 92, depth=0.09, gate=0.97)
    expr(sc, CL, [(t, 88), (t + 20, 104), (t + 32, 84)])
    seq(sc, CL, t, HARM_A2, 66, 70, gate=0.95, jt=3)
    piano_flow(sc, t, MID_A2, 52, 58, lo=57, hi=72)
    guitar_boomchick(sc, t, MID_A2, 54, 58)
    seq(sc, BS, t, BASS_A + BASS_A2_END, 82, 86, gate=0.9)
    expr(sc, VC, [(t, 90), (t + 20, 108), (t + 32, 92)])
    tenor_line(sc, VC, t, MID_A2, 58)
    for bar in (1, 3, 5, 7):
        seg = [s for s in MID_A2 if s[0] <= 4.0 * bar < s[0] + s[1]][0]
        harp_run(sc, t + 4.0 * bar + 2.0, chord_tones(seg[2], 64, 4),
                 0.5, 48, 56)

    # B — the bridge: violin calls, clarinet answers, strings arrive.
    t = T_B
    expr(sc, VN, [(t, 104), (t + 6, 116), (t + 8, 72), (t + 16, 106),
                  (t + 22, 124), (t + 28, 104), (t + 32, 112)])
    sing(sc, VN, t, [("A5", 0, 1.5), ("G5", 1.5, .5), ("F5", 2, 1),
                     ("C5", 3, 1), ("D5", 4, 1.5), ("E5", 5.5, .5),
                     ("D5", 6, 2)], 86, 88, depth=0.09, gate=0.97)
    seq(sc, VN, t, [("G5", 8, 4), ("E5", 12, 3.8)], 58, 60, gate=1.0, jt=3)
    sing(sc, VN, t, [("A5", 16, 1.5), ("G5", 17.5, .5), ("F5", 18, 1),
                     ("A5", 19, 1), ("D6", 20, 1.5), ("C6", 21.5, .5),
                     ("A5", 22, 1), ("F#5", 23, 1), ("G5", 24, 4),
                     ("G5", 28, 2), ("A5", 30, .5), ("G5", 30.5, .5),
                     ("F5", 31, .5), ("D5", 31.5, .5)], 88, 94, depth=0.1,
         gate=0.97)
    expr(sc, CL, [(t, 70), (t + 8, 104), (t + 12, 116), (t + 16, 72),
                  (t + 24, 100), (t + 32, 108)])
    seq(sc, CL, t, [("A4", 0, 4), ("B4", 4, 3.8)], 56, 58, gate=1.0, jt=3)
    seq(sc, CL, t, [("G4", 8, .5), ("B4", 8.5, .5), ("E5", 9, 1),
                    ("D5", 10, 1), ("B4", 11, 1), ("C5", 12, 1.5),
                    ("B4", 13.5, .5), ("A4", 14, 2)], 84, 86, gate=0.96,
        jt=3)
    seq(sc, CL, t, [("C5", 16, 4), ("A4", 20, 3.8)], 56, 60, gate=1.0, jt=3)
    seq(sc, CL, t, [("C5", 24, 2), ("D5", 26, 2), ("B4", 28, 3.5)], 72, 78,
        gate=0.98, jt=3)
    piano_flow(sc, t, MID_B, 54, 64, lo=57, hi=72)
    guitar_finger(sc, t, MID_B, 56, 64, lo=57, hi=72)
    seq(sc, BS, t, BASS_B, 82, 88, gate=0.9)
    expr(sc, VC, [(t, 92), (t + 22, 116), (t + 32, 100)])
    tenor_line(sc, VC, t, MID_B, 60, 66)
    expr(sc, STR, [(t - 0.5, 58), (t + 8, 80), (t + 22, 108), (t + 32, 92)])
    pad(sc, t, MID_B, 3, 60, 77, 46, 58)
    for bar in range(8):
        harp_roll(sc, t + 4.0 * bar, chord_tones(MID_B[bar][2], 60, 4),
                  50 + bar)

    # A3 — the tune, everybody.
    t = T_A3
    expr(sc, VN, [(t, 108), (t + 6, 122), (t + 16, 110)])
    sing(sc, VN, t, TUNE_A3, 92, 96, depth=0.1, gate=0.97)
    expr(sc, CL, [(t, 100), (t + 6, 114), (t + 16, 104)])
    seq(sc, CL, t, HARM_A3, 76, 80, gate=0.95, jt=3)
    seq(sc, PNO, t, TUNE_A3, 66, 72, gate=0.9, jt=3, transpose=12)
    piano_flow(sc, t, MID_A3, 60, 66, lo=57, hi=72)
    guitar_strum(sc, t, MID_A3, 60, 66)
    seq(sc, BS, t, BASS_A[:16], 86, 90, gate=0.9)
    expr(sc, VC, [(t, 100), (t + 16, 110)])
    tenor_line(sc, VC, t, MID_A3, 64)
    expr(sc, STR, [(t, 92), (t + 8, 108), (t + 16, 100)])
    pad(sc, t, MID_A3, 3, 60, 77, 54, 58)
    for bar in range(4):
        harp_run(sc, t + 4.0 * bar + 2.0, chord_tones(MID_A3[bar][2], 64, 4),
                 0.5, 54, 62)

    # Retransition — F, G, then the dominant; the BEAM climbs in the cello.
    t = T_RETRANS
    expr(sc, VN, [(t, 104), (t + 8, 116), (t + 14, 127), (t + 16, 120)])
    sing(sc, VN, t, [("C5", 0, 1), ("F5", 1, 1), ("A5", 2, 2),
                     ("D5", 4, 1), ("G5", 5, 1), ("B5", 6, 2),
                     ("D6", 8, 6), ("C#6", 14, 1.6)], 88, 102, depth=0.11,
         gate=0.98)
    expr(sc, CL, [(t, 96), (t + 8, 110), (t + 15, 127)])
    seq(sc, CL, t, [("A4", 0, 2), ("C5", 2, 2), ("B4", 4, 2), ("D5", 6, 2),
                    ("E5", 8, 4), ("E5", 12, 3.6)], 74, 88, gate=0.98, jt=3)
    piano_flow(sc, t, RETRANS, 60, 76, lo=57, hi=72)
    guitar_strum(sc, t, RETRANS, 62, 78)
    seq(sc, BS, t, BASS_RT, 84, 96, gate=0.92)
    expr(sc, VC, [(t, 100), (t + 8, 104), (t + 12, 122), (t + 16, 127)])
    sc.cc(VC, 68, 0, t + 7.5)
    tenor_line(sc, VC, t, RETRANS[:2], 66)
    material.play_beam(sc, VC, t + 8.0, 45, "aeolian", stretch=2.0, vel=84,
                       vel_end=100, gate=0.97, jt=0, jv=2)
    expr(sc, STR, [(t, 96), (t + 8, 108), (t + 15, 127), (t + 16, 118)])
    pad(sc, t, RETRANS, 4, 57, 79, 56, 74)
    harp_run(sc, t + 14.0, [57, 61, 64, 67, 69, 73, 76, 79], 0.25, 56, 82)
    for bar in range(4):
        tb = t + 4.0 * bar
        v = 40 + 7 * bar
        sc.hit(38, tb + 1.0, v)
        sc.hit(38, tb + 3.0, v + 3)
        if bar >= 2:
            sc.hit(36, tb, v + 6)
            for k in range(8):
                sc.hit(42, tb + 0.5 * k, v - 12 + (5 if k % 2 == 0 else 0))
    for i, v in enumerate((50, 57, 64, 72)):
        sc.hit(38, t + 15.0 + 0.25 * i, v, jt=1)


def _b_full(sc: en.Score) -> None:
    """V — the hymn again, everybody in the lamp room."""
    t0 = T_FULL
    bell(sc, t0, 86, dur=6.0)
    bell(sc, t0 + 32.0, 80, dur=6.0)
    sc.cc(VC, 68, 127, t0 - 0.02)

    expr(sc, VN, [(t0 - 0.2, 112), (t0 + 10, 122), (t0 + 16, 110),
                  (t0 + 32, 116), (t0 + 42, 127), (t0 + 48, 118),
                  (t0 + 60, 122), (t0 + 64, 104)])
    material.play_hymn(sc, VN, t0, TONIC + 12, MODE, vel=98, vel_end=106,
                       gate=1.02, jt=0, jv=2)
    for _d, on, du in material.HYMN:
        vib(sc, VN, t0 + on, du, 0.12)
    for k, (a, b) in enumerate([(92, 96), (92, 94), (98, 106), (100, 94)]):
        material.play_phrase(sc, PNO, t0 + 16.0 * k, TONIC, MODE, k,
                             vel=a, vel_end=b, gate=0.98, jt=0, jv=2)
        material.play_phrase(sc, CL, t0 + 16.0 * k, TONIC, MODE, k,
                             vel=a - 8, vel_end=b - 8, gate=0.97, jt=0,
                             jv=2)
    expr(sc, CL, [(t0, 108), (t0 + 32, 112), (t0 + 42, 127),
                  (t0 + 64, 100)])

    expr(sc, VC, [(t0 - 0.02, 112), (t0 + 10, 124), (t0 + 16, 110),
                  (t0 + 30, 124), (t0 + 42, 127), (t0 + 48, 114),
                  (t0 + 62, 122), (t0 + 64, 100)])
    counter(sc, VC, t0, TONIC - 12, 88, 94)

    expr(sc, STR, [(t0 - 0.02, 100), (t0 + 16, 108), (t0 + 32, 112),
                   (t0 + 42, 127), (t0 + 56, 114), (t0 + 64, 96)])
    pad(sc, t0, HYMN_RICH, 4, 60, 81, 62, 72)
    piano_flow(sc, t0, HYMN_RICH, 70, 78, octave=True)
    guitar_strum(sc, t0, HYMN_RICH, 66, 74)
    seq(sc, BS, t0, BASS3, 92, 98, gate=0.9, jt=4)
    for bar in range(16):
        seg = [s for s in HYMN_RICH if s[0] <= 4.0 * bar < s[0] + s[1]][0]
        v = 60 + (10 if 8 <= bar < 12 else 0)
        harp_run(sc, t0 + 4.0 * bar, chord_tones(seg[2], 50, 6), 0.25, v,
                 v + 14)
    brushes(sc, t0, 8, 62, 66)
    brushes(sc, t0 + 32.0, 4, 72, 74)
    brushes(sc, t0 + 48.0, 4, 68, 60)
    sc.hit(49, t0, 56)
    sc.hit(49, t0 + 32.0, 62)


def _b_coda(sc: en.Score) -> None:
    """VI — the cadence echoed, the BEAM handed round, the bell tolling."""
    t0 = T_CODA
    for t, v, d in ((t0, 74, 7.8), (t0 + 16, 70, 7.8), (t0 + 32, 66, 7.8),
                    (t0 + 48, 62, 7.8), (t0 + 64, 58, 7.8)):
        bell(sc, t, v, d)

    # 376-392: the last phrase once more, as the room empties.
    material.play_phrase(sc, PNO, t0, TONIC, MODE, 3, vel=64, vel_end=54,
                         gate=0.98, jt=0, jv=2)
    expr(sc, VC, [(t0, 96), (t0 + 8, 104), (t0 + 16, 80), (t0 + 24, 96),
                  (t0 + 32, 84), (t0 + 36, 100), (t0 + 48, 84),
                  (t0 + 72, 60)])
    counter(sc, VC, t0, TONIC - 12, 62, 54, lo=48.0, hi=64.0)
    tail = _sub(HYMN_RICH, 48, 64)
    guitar_finger(sc, t0, tail, 48, 42)
    seq(sc, BS, t0, [("D2", 0, 3), ("B1", 3, 1), ("A1", 4, 4), ("C2", 8, 2),
                     ("A1", 10, 2), ("D2", 12, 4)], 64, 56, gate=0.95)
    expr(sc, STR, [(t0, 84), (t0 + 16, 66), (t0 + 32, 70), (t0 + 48, 64),
                   (t0 + 64, 52), (END, 24)])
    pad(sc, t0, tail, 3, 57, 72, 42, 38)

    # 392-408: the BEAM as the guitar's vamp; a high violin traces 5-6-5-8.
    t = t0 + 16.0
    beam_vamp(sc, t, [50, 43, 50, 43], 52, 44)
    sc.note(VC, 38, t, 15.8, 52, jt=0)
    expr(sc, VN, [(t - 0.5, 60), (t + 6, 84), (t + 12, 76), (t + 16, 50)])
    seq(sc, VN, t, [("A5", 0, 4), ("B5", 4, 4), ("A5", 8, 4), ("D6", 12, 4)],
        48, 44, gate=1.01, jt=0)
    for tt, nm in ((t + 2, "D5"), (t + 6, "B4"), (t + 10, "D5"),
                   (t + 14, "G5")):
        sc.note(HP, en.n(nm), tt, 2.0, 42)
    pad(sc, t, _h([(4, "Dm", "D"), (4, "G", "G"), (4, "Dm", "D"),
                   (4, "G", "G")]), 3, 57, 72, 36)

    # 408-424: the cello swings the BEAM out once more.
    t = t0 + 32.0
    en.strum(sc, GT, [50, 57, 62, 65], t, 6.0, 46, spread=0.05)
    material.play_beam(sc, VC, t, 38, MODE, stretch=2.0, vel=60, vel_end=54,
                       gate=1.0, jt=0, jv=2)
    sc.note(VC, 38, t + 8.0, 7.9, 48, jt=0)
    sc.note(BS, 38, t, 3.0, 56)
    sc.note(BS, 38, t + 8.0, 3.0, 50)
    for p in (57, 62, 65):
        sc.note(STR, p, t, 15.9, 34, jt=0)
    harp_roll(sc, t + 8.0, DM9, 42)
    sc.cc(CL, 68, 127, t)
    expr(sc, CL, [(t + 7.5, 60), (t + 10, 84), (t + 16, 44)])
    seq(sc, CL, t, [("E4", 8, 2), ("F4", 10, 2), ("D4", 12, 3.8)], 48, 42,
        gate=1.0, jt=0)

    # 424-440: the piano's BEAM as at the start, then once more an octave up.
    t = t0 + 48.0
    en.sustain(sc, PNO, t, t + 15.6)
    material.play_beam(sc, PNO, t, 50, MODE, stretch=2.0, vel=58,
                       vel_end=64, gate=1.0, jt=0, jv=0)
    cell = material.beam_pitches(TONIC, MODE)
    for k, p in enumerate(cell):
        sc.note(PNO, p, t + 8.0 + 0.5 * k, 0.5 if k < 4 else 5.5, 52 + 2 * k,
                jt=0, jv=0)
    for p in (50, 57, 62):
        sc.note(STR, p, t, 31.9, 32, jt=0)
    sc.note(VC, 38, t, 23.5, 46, jt=0)

    # 440-456: the lamp-room chord, and the bell.
    t = t0 + 64.0
    harp_roll(sc, t, DM9, 40, spread=0.09, dur=12.0)
    en.sustain(sc, PNL, t, END - 0.3)
    sc.note(PNL, 38, t, 15.5, 38, jt=0)
    sc.note(PNL, 45, t, 15.5, 36, jt=0)
    bell(sc, t + 8.0, 50, dur=8.0)


BUILDERS = [_b_lamp, _b_hymn, _b_variation, _b_middle, _b_full, _b_coda]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _voice_at(spans, beat):
    """The most recently started pitch sounding at the beat, or None."""
    best = None
    for on, off, p, _v in spans:
        if on <= beat + 1e-9 and off >= beat + 0.05:
            if best is None or on > best[0]:
                best = (on, p)
    return None if best is None else best[1]


def _pitched(sc):
    return [ch for ch in sorted(sc.events) if ch != DR]


def _has_hymn(sc, ch, t0, base):
    return any(abs(s - t0) < 0.01 and abs(st - 1.0) < 0.01 and b == base
               for s, st, b in material.hymn_statements(sc, ch, MODE))


def _o_lamp_then_beam(sc):
    fails = []
    ons = sorted((b, ch, p) for ch in _pitched(sc) + [DR]
                 for b, p, _v in material.note_ons(sc, ch))
    first = ons[0]
    if first[1] != BELL or first[2] != material.LAMP_PITCH or first[0] != 0.0:
        fails.append(f"first sound is ch{first[1]} pitch {first[2]} at beat "
                     f"{first[0]:.2f}, want the LAMP bell at 0")
    progs = [d[1] for _t, _p, d in sc.events[BELL] if (d[0] & 0xF0) == 0xC0]
    if progs != [material.LAMP_PROGRAM]:
        fails.append(f"lamp channel programs {progs}")
    rest = [o for o in ons if o[1] != BELL]
    if rest[0][0] < 6.0:
        fails.append(f"the bell is alone for only {rest[0][0]:.1f} beats "
                     f"(need >= 6)")
    five = rest[:5]
    if len({ch for _b, ch, _p in five}) != 1:
        fails.append("the first five melodic notes are not on one channel")
    ch = five[0][1]
    want = material.beam_pitches(five[0][2], MODE)
    if [p for _b, _c, p in five] != want:
        fails.append(f"the first melodic notes {[p for _b, _c, p in five]} "
                     f"are not the BEAM {want}")
    beams = material.beam_statements(sc, ch)
    if not beams or abs(beams[0] - five[0][0]) > 1e-6:
        fails.append("beam_statements does not open on the first note")
    # Unaccompanied: until the cell's arrival note has rung two beats,
    # nothing but the cell sounds (the bell's own tail aside).
    until = five[-1][0] + 2.0
    others = [o for o in ons if o[0] < until and o not in five
              and not (o[1] == BELL and o[0] == 0.0)]
    if others:
        fails.append(f"the BEAM is accompanied: {others[:3]}")
    return fails


def _o_hymn_plain(sc):
    fails = []
    if not _has_hymn(sc, PNO, T_HYMN, TONIC):
        fails.append("no complete HYMN on the piano at beat 40, stretch 1, "
                     "base D4")
    got = [(b, p) for b, p, _v in material.note_ons(sc, PNO)
           if T_HYMN <= b < T_HYMN + material.HYMN_LEN]
    want = [(T_HYMN + on, en.pitch(TONIC, MODE, d))
            for d, on, _du in material.HYMN]
    if got != want:
        fails.append(f"the piano tune is not the bare hymn: {len(got)} "
                     f"note-ons, want exactly {len(want)} on the grid")
    # Plain also means lightly dressed and purely dorian.
    for ch in _pitched(sc):
        bad = [(b, p) for b, p, _v in material.note_ons(sc, ch)
               if T_HYMN <= b < T_MID and p % 12 not in WHITE]
        if bad:
            fails.append(f"ch{ch} leaves D dorian in the hymn verses: "
                         f"{bad[:3]}")
    if any(b < T_MID for b, _p, _v in material.note_ons(sc, DR)):
        fails.append("percussion under the plain hymn")
    return fails


def _counter_fails(sc, t0, mel_ch, mel_base, ctr_ch, tag):
    fails = []
    if not _has_hymn(sc, mel_ch, t0, mel_base):
        fails.append(f"{tag}: no complete HYMN on ch{mel_ch} at {t0}")
        return fails
    mel = material.note_spans(sc, mel_ch)
    ctr = material.note_spans(sc, ctr_ch)
    pairs = []
    for i in range(32):
        beat = t0 + 2.0 * i
        m, c = _voice_at(mel, beat), _voice_at(ctr, beat)
        if m is None or c is None:
            fails.append(f"{tag}: a voice is silent at beat {beat}")
            continue
        pairs.append((m, c))
        if (m - c) % 12 not in material.CONSONANT:
            fails.append(f"{tag}: dissonance at beat {beat} "
                         f"(tune {m}, counter {c})")
        if c >= m:
            fails.append(f"{tag}: counter crosses the tune at beat {beat}")
    mel_on = [b for b, _p, _v in material.note_ons(sc, mel_ch)
              if t0 <= b < t0 + 64]
    own = [b for b, _p, _v in material.note_ons(sc, ctr_ch)
           if t0 <= b < t0 + 64
           and all(abs(b - m) > 0.1 for m in mel_on)]
    if len(own) < 24:
        fails.append(f"{tag}: only {len(own)} counter onsets of its own "
                     f"(need >= 24)")
    similar = contrary = 0
    for (m0, c0), (m1, c1) in zip(pairs, pairs[1:]):
        dm, dc = m1 - m0, c1 - c0
        if dm and dc:
            if (dm > 0) == (dc > 0):
                similar += 1
            else:
                contrary += 1
    if contrary < 10 or similar > contrary:
        fails.append(f"{tag}: motion is {similar} similar / {contrary} "
                     f"contrary (need >= 10 contrary, and contrary >= "
                     f"similar)")
    if len({(m - c) % 12 for m, c in pairs}) < 4:
        fails.append(f"{tag}: the counter shadows the tune (fewer than 4 "
                     f"interval classes)")
    return fails


def _o_counter(sc):
    return (_counter_fails(sc, T_VAR, VN, TONIC + 12, CL, "verse 2")
            + _counter_fails(sc, T_FULL, VN, TONIC + 12, VC, "full hymn"))


def _o_bass(sc):
    """The upright bass has a line of its own under verses 2 and 3."""
    fails = []
    bass = material.note_spans(sc, BS)
    mel = material.note_spans(sc, VN)
    for t0, tag, need in ((T_VAR, "verse 2", 30), (T_FULL, "full hymn", 56)):
        ons = [(b, p) for b, p, _v in material.note_ons(sc, BS)
               if t0 - 0.05 <= b < t0 + 64 - 0.05]
        if len(ons) < need:
            fails.append(f"{tag}: bass has {len(ons)} notes (need {need})")
            continue
        if len({p % 12 for _b, p in ons}) < 6:
            fails.append(f"{tag}: bass uses fewer than 6 pitch classes")
        if max(p for _b, p in ons) - min(p for _b, p in ons) < 12:
            fails.append(f"{tag}: bass range under an octave")
        doubled = 0
        for bar in range(16):
            beat = t0 + 4.0 * bar
            b, m = _voice_at(bass, beat + 0.06), _voice_at(mel, beat)
            if b is None or m is None:
                fails.append(f"{tag}: no bass on bar line {beat}")
                continue
            if (m - b) % 12 not in material.CONSONANT:
                fails.append(f"{tag}: bass {b} against tune {m} at {beat}")
            doubled += (m - b) % 12 == 0
        if doubled > 8:
            fails.append(f"{tag}: bass doubles the tune on {doubled} of 16 "
                         f"bar lines")
        steps = sum(1 for (_a, p), (_b2, q) in zip(ons, ons[1:])
                    if 0 < abs(q - p) <= 2)
        if steps < 6:
            fails.append(f"{tag}: bass has only {steps} stepwise moves")
    return fails


def _o_middle(sc):
    """The middle leaves the tune, leaves D, and sits higher and brighter."""
    fails = []
    for ch in _pitched(sc):
        for mode in ("dorian", "ionian"):
            for k in range(4):
                hits = [s for s, _st, _b in
                        material.phrase_statements(sc, ch, mode, k)
                        if T_MID - 16 < s < T_FULL]
                if hits:
                    fails.append(f"ch{ch} quotes hymn phrase {k + 1} "
                                 f"({mode}) at {hits[0]:.1f}")
    bass = material.note_spans(sc, BS)
    roots = [_voice_at(bass, T_MID + 4.0 * bar + 0.06) for bar in range(32)]
    if None in roots:
        fails.append("the bass misses a bar line in the middle")
        return fails
    if roots[0] % 12 != 0:
        fails.append(f"the middle opens on bass pc {roots[0] % 12}, want C")
    on_d = sum(1 for r in roots if r % 12 == 2)
    on_cg = sum(1 for r in roots if r % 12 in (0, 7))
    if on_d > 4:
        fails.append(f"bass sits on D for {on_d} of 32 bar lines (max 4)")
    if on_cg < 10:
        fails.append(f"bass finds C or G on only {on_cg} of 32 bar lines")
    lead = [p for ch in (CL, VN) for b, p, v in material.note_ons(sc, ch)
            if T_MID <= b < T_RETRANS and v >= 80]
    hymn = [p for b, p, _v in material.note_ons(sc, PNO)
            if T_HYMN <= b < T_LINK1]
    if not lead or sum(lead) / len(lead) < sum(hymn) / len(hymn) + 3.0:
        fails.append("the middle's lead line is not >= 3 semitones above "
                     "the hymn's tessitura")
    e3 = sum(1 for ch in _pitched(sc) for b, p, _v in material.note_ons(
        sc, ch) if T_MID <= b < T_MID + 4 and p % 12 == 4)
    eb = sum(1 for ch in _pitched(sc) for b, p, _v in material.note_ons(
        sc, ch) if T_MID <= b < T_MID + 4 and p % 12 == 3)
    if e3 < 3 or eb:
        fails.append("the middle's first bar is not a C major chord")
    return fails


def _o_hymn_fuller(sc):
    fails = []
    for ch, base in ((VN, TONIC + 12), (PNO, TONIC)):
        if not _has_hymn(sc, ch, T_FULL, base):
            fails.append(f"no complete HYMN on ch{ch} at beat {T_FULL}")
    e1 = material.energy(sc, T_HYMN, T_HYMN + 64)
    e2 = material.energy(sc, T_VAR, T_VAR + 64)
    e3 = material.energy(sc, T_FULL, T_FULL + 64)
    if e3 < 1.8 * e1:
        fails.append(f"full hymn energy {e3:.0f} is not >= 1.8x the plain "
                     f"hymn's {e1:.0f}")
    if not e1 < e2 < e3:
        fails.append(f"the three verses do not grow: {e1:.0f}, {e2:.0f}, "
                     f"{e3:.0f}")
    n1 = len(material.active_channels(sc, T_HYMN, T_HYMN + 64))
    n3 = len(material.active_channels(sc, T_FULL, T_FULL + 64))
    if n3 < n1 + 3:
        fails.append(f"full hymn uses {n3} voices against {n1} (need +3)")

    def tune_vel(t0):
        v = [vel for b, _p, vel in material.note_ons(sc, PNO)
             if t0 <= b < t0 + 64]
        return sum(v) / max(1, len(v))
    if tune_vel(T_FULL) < tune_vel(T_HYMN) + 15:
        fails.append("the tune itself is not played >= 15 velocity louder")
    for name, t0, t1 in PART.MOVEMENTS:
        if t0 != T_FULL and material.energy(sc, t0, t1) >= e3:
            fails.append(f"'{name}' out-weighs the full hymn")
    return fails


def _o_quiet_close(sc):
    fails = []
    ons = sorted((b, ch, p, v) for ch in sorted(sc.events)
                 for b, p, v in material.note_ons(sc, ch))
    last = ons[-1]
    if last[1] != BELL or last[2] != material.LAMP_PITCH:
        fails.append(f"the last note-on is ch{last[1]} at {last[0]:.1f}, "
                     f"not the LAMP bell")
    tolls = [b for b, _p, _v in material.note_ons(sc, BELL) if b >= T_CODA]
    if len(tolls) < 4:
        fails.append(f"the bell tolls {len(tolls)} time(s) in the coda "
                     f"(need >= 4)")
    gaps = {round(b - a, 3) for a, b in zip(tolls, tolls[1:-1])}
    if len(gaps) > 1:
        fails.append(f"the tolling is not regular: gaps {sorted(gaps)}")
    loud = [(b, ch, v) for b, ch, _p, v in ons if b >= END - 32 and v > 70]
    if loud:
        fails.append(f"loud notes in the last eight bars: {loud[:3]}")
    full = material.energy(sc, T_FULL, T_FULL + 64)
    tail = material.energy(sc, END - 32, END)
    plain = material.energy(sc, T_HYMN, T_HYMN + 64)
    if tail > 0.2 * full or tail > 0.6 * plain:
        fails.append(f"the close is not a hush: tail {tail:.0f} against "
                     f"full hymn {full:.0f}, plain hymn {plain:.0f}")
    drums = [b for b, _p, _v in material.note_ons(sc, DR)]
    if drums and (min(drums) < T_A3 or max(drums) >= T_CODA):
        fails.append(f"brushes outside the late pages "
                     f"({min(drums):.0f}..{max(drums):.0f})")
    if sc.seconds_at(END) - sc.seconds_at(END - 16) <= 16 * 60.0 / 92.0:
        fails.append("no ritardando into the last bell")
    return fails


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("t01_lamp_then_beam_alone", _o_lamp_then_beam(sc)))
    results.append(("t01_hymn_plain_dorian", _o_hymn_plain(sc)))
    results.append(("t01_counter_melody", _o_counter(sc)))
    results.append(("t01_bass_line", _o_bass(sc)))
    results.append(("t01_middle_leaves_tune", _o_middle(sc)))
    results.append(("t01_hymn_returns_fuller", _o_hymn_fuller(sc)))
    results.append(("t01_quiet_close_bell", _o_quiet_close(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def level(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    lamp = level(0.2, 7.0)
    beam = level(8.5, 15.5)
    plain = level(T_HYMN + 4, T_HYMN + 60)
    verse2 = level(T_VAR + 4, T_VAR + 60)
    full = level(T_FULL + 4, T_FULL + 60)
    hush = level(END - 28, END - 4)
    out = []

    fails = []
    if lamp < -60.0:
        fails.append(f"the opening bell is inaudible ({lamp:.1f} dB)")
    if beam < -55.0:
        fails.append(f"the solo BEAM is inaudible ({beam:.1f} dB)")
    if beam > plain + 1.0:
        fails.append(f"the solo BEAM ({beam:.1f} dB) outweighs the hymn "
                     f"({plain:.1f} dB)")
    out.append(("audio_lamp_and_beam", fails))

    fails = []
    if full < plain + 3.0:
        fails.append(f"full hymn {full:.1f} dB is not >= 3 dB over the "
                     f"plain hymn {plain:.1f} dB")
    if full < verse2:
        fails.append(f"full hymn {full:.1f} dB is below verse 2 "
                     f"{verse2:.1f} dB")
    out.append(("audio_hymn_returns_louder", fails))

    fails = []
    if full - hush < 6.0:
        fails.append(f"the close {hush:.1f} dB is not >= 6 dB under the "
                     f"peak {full:.1f} dB")
    if hush < -70.0:
        fails.append(f"the close is silent ({hush:.1f} dB)")
    out.append(("audio_peak_and_hush", fails))
    return out
