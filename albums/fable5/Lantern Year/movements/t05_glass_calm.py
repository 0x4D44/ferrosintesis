"""t05_glass_calm.py — track 5 of *Lantern Year*: "Glass Calm".

Midsummer; mallet minimalism.  A ionian, quarter = 132, 4/4, 164 bars.

THE PROCESS.  Two marimbas play one eight-note cell built from the BEAM's
pitches (A E F# E A' F# E A' — its first five notes ARE the BEAM, so
Marimba I states the album's signature once a bar).  From bar 17 Marimba II
slips ahead by one eighth every twelve bars; after seven slips it has gone
right round the cell and at bar 101 the two are back in unison.  Every
stage is tick-verified (t05_phase_process), and a celesta picks out the
"resultant" top line that the two marimbas make between them.

Under the process the harmonic field turns once every four bars
(A -> F#m -> D -> E), darkens through B minor for the one great swell
(bars 65-88, summit at bar 85), ebbs to a hush, and comes home with the
unison.  Over it a long-breathed tune floats in notes eight to sixteen times
the length of the pulse: flute first, then strings, then both.

The whole piece is written ONCE, in absolute beats, by _compose(); each
movement builder replays it through a window that only lets its own
movement's events through (so movement bounds hold by construction).
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 5
TITLE = "Glass Calm"
FILE = "05 - Glass Calm.mid"
SEED = 20261205
COMMENT = ("Glass Calm - midsummer at the lighthouse, the sea like a mirror. "
           "Mallet minimalism in A major: two marimbas phase one BEAM-built "
           "cell through a full cycle and return to unison, while the "
           "harmony turns slowly beneath a long-breathed tune for flute and "
           "strings.  One great swell, one hush, one clear return.")

MODE = "ionian"
TONIC = 57                      # A3: degree 1 of the marimba cell
SONG = 69                       # A4: degree 1 of the tunes
BASSBASE = 33                   # A1: degree 1 of the bass arithmetic

BARS = 164
END = BARS * 4.0                # 656 beats


def B(bar: int, beat: float = 0.0) -> float:
    """Beat of 1-indexed bar (+ offset)."""
    return (bar - 1) * 4.0 + beat


def U(unit: int) -> float:
    """Beat of 1-indexed four-bar harmonic unit."""
    return (unit - 1) * 16.0


# -- channels ---------------------------------------------------------------
M1, M2, VIB, GLK, CEL, RHO, HARP, PAD, STR, SHK, FLU, BASS, LAMP = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Still Water", B(1), B(17)),
        ("II. Drift", B(17), B(49)),
        ("III. Open Water", B(49), B(81)),
        ("IV. The Swell", B(81), B(101)),
        ("V. Unison", B(101), B(133)),
        ("VI. Afterglow", B(133), END),
    ],
    tempo_map=[(0.0, 132.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 3, 0)],
    channels=[
        (M1, "Marimba I", 12, 100, 46, 30),
        (M2, "Marimba II", 12, 96, 82, 30),
        (VIB, "Vibraphone", 11, 98, 40, 55),
        (GLK, "Glockenspiel", 9, 100, 90, 60),
        (CEL, "Celesta", 8, 80, 36, 55),
        (RHO, "Rhodes", 4, 80, 58, 45),
        (HARP, "Harp", 46, 88, 88, 50),
        (PAD, "String swell", 49, 78, 54, 70),
        (STR, "String melody", 48, 118, 72, 65),
        (SHK, "Shaker", 0, 62, 64, 30),
        (FLU, "Flute", 73, 112, 64, 60),
        (BASS, "Soft bass", 35, 72, 64, 20),
        (LAMP, "Lamp bell", material.LAMP_PROGRAM, 92, 64, 75),
    ],
)

BEAM_CHANNELS = {M1, GLK}
PROGRAM_WHITELIST = {12, 11, 9, 8, 4, 46, 49, 48, 73, 35,
                     material.LAMP_PROGRAM}
CENTERED_CHANNELS = {SHK, FLU, BASS, LAMP}
NOTE_RANGES = {
    M1: (57, 69), M2: (57, 69), VIB: (52, 83), GLK: (81, 98),
    CEL: (69, 93), RHO: (52, 71), HARP: (45, 88), PAD: (57, 86),
    STR: (59, 93), FLU: (69, 93), BASS: (33, 54), LAMP: (62, 62),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (297.0, 301.5)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# The material
# ---------------------------------------------------------------------------

# The cell: eight eighths, degrees of A ionian.  Its first five are the BEAM.
CELL_DEGREES = [1, 5, 6, 5, 8, 6, 5, 8]
CELL = [en.pitch(TONIC, MODE, d) for d in CELL_DEGREES]

# The process: (first bar, how many eighths Marimba II is AHEAD).
STAGES = [(1, 0), (17, 1), (29, 2), (41, 3), (53, 4), (65, 5), (77, 6),
          (89, 7), (101, 0)]
M2_FIRST, M2_LAST = 5, 148      # Marimba II's bars
PULSE_BARS = 160                # Marimba I's unbroken eighths: bars 1..160
RESULT_BARS = (41, 88)          # the celesta "resultant" (stages 3-6)


def _stage(bar: int) -> int:
    k = 0
    for first, off in STAGES:
        if bar >= first:
            k = off
    return k


# The harmonic field: one chord per four-bar unit (41 units).
FIELD = (["A", "F#m", "D", "E"] * 4
         + ["F#m", "D", "Bm", "E", "F#m", "D", "Bm", "D", "E"]
         + ["A", "F#m", "D", "E"] * 3
         + ["A", "D", "A", "A"])
CYCLE = ["A", "F#m", "D", "E"]
ROOT_PC = {"A": 9, "F#m": 6, "D": 2, "E": 4, "Bm": 11}
CHORD = {
    #        bass degree, Rhodes voicing, string voicing, vibes dyad, triad pcs
    "A":   (8, [52, 61, 64, 71], [64, 69, 73], (64, 73), (9, 1, 4)),
    "F#m": (6, [54, 61, 64, 69], [66, 69, 73], (66, 73), (6, 9, 1)),
    "D":   (4, [54, 62, 64, 69], [66, 69, 74], (66, 74), (2, 6, 9)),
    "E":   (5, [52, 59, 64, 66], [64, 66, 71], (64, 71), (4, 8, 11)),
    "Bm":  (2, [54, 59, 62, 69], [66, 71, 74], (62, 71), (11, 2, 6)),
}

# The tune, in (degree, onset, duration) over one 16-bar field cycle.
T1 = [(5, 0, 6), (6, 6, 2), (8, 8, 6), (7, 14, 2),
      (6, 16, 8), (5, 24, 4), (3, 28, 4),
      (4, 32, 6), (5, 38, 2), (6, 40, 6), (8, 46, 2),
      (7, 48, 8), (5, 56, 4), (2, 60, 3.5)]
T2 = [(8, 0, 6), (9, 6, 2), (10, 8, 6), (9, 14, 2),
      (8, 16, 8), (6, 24, 4), (5, 28, 4),
      (6, 32, 6), (5, 38, 2), (4, 40, 4), (6, 44, 4),
      (9, 48, 6), (8, 54, 2), (7, 56, 7.5)]
# The flute's descant over the strings' first statement of T1.
D1 = [(10, 0, 6), (11, 6, 2), (12, 8, 8),
      (10, 16, 8), (8, 24, 6), (9, 30, 2),
      (8, 32, 8), (11, 40, 6), (10, 46, 2),
      (9, 48, 8), (7, 56, 7.5)]
# The swell: a rising sequence over F#m D Bm E F#m D (24 bars).
T3 = [(3, 0, 4), (6, 4, 4), (8, 8, 8),
      (6, 16, 4), (8, 20, 4), (11, 24, 8),
      (9, 32, 4), (11, 36, 4), (13, 40, 8),
      (12, 48, 8), (11, 56, 4), (9, 60, 4),
      (10, 64, 6), (12, 70, 2), (13, 72, 8),
      (15, 80, 8), (13, 88, 4), (11, 92, 4)]
EBB_STR = [(9, 0, 8), (8, 8, 4), (6, 12, 3.5)]
EBB_FLU = [(6, 0, 8), (4, 8, 8), (5, 16, 8), (2, 24, 7)]
# Vibraphone counter-melodies: they move where the tune holds.
CM1 = [(3, 0, 3), (2, 3, 1), (1, 4, 2), (2, 6, 2), (3, 8, 4), (5, 12, 2),
       (4, 14, 2),
       (1, 16, 4), (3, 20, 2), (2, 22, 2), (1, 24, 4), (-1, 28, 2),
       (1, 30, 2),
       (-1, 32, 4), (1, 36, 2), (2, 38, 2), (1, 40, 4), (4, 44, 2),
       (3, 46, 2),
       (2, 48, 4), (3, 52, 2), (4, 54, 2), (0, 56, 4), (-2, 60, 2),
       (0, 62, 2)]
CM2 = [(5, 0, 4), (3, 4, 2), (4, 6, 2), (5, 8, 4), (1, 12, 2), (2, 14, 2),
       (3, 16, 4), (1, 20, 2), (2, 22, 2), (3, 24, 4), (1, 28, 4),
       (1, 32, 4), (4, 36, 2), (3, 38, 2), (-1, 40, 4), (1, 44, 2),
       (4, 46, 2),
       (5, 48, 4), (4, 52, 2), (3, 54, 2), (2, 56, 4), (4, 60, 2),
       (5, 62, 2)]

# Where a tune meets its counter-line: (lead ch, counter ch, start beat).
COUNTERPOINT = [(STR, FLU, U(13)), (FLU, VIB, U(26)), (FLU, VIB, U(30))]

# The dynamic arc: (bar, intensity 0..1), linear between breakpoints.
DYN = [(1, .34), (5, .40), (17, .50), (41, .60), (65, .72), (77, .90),
       (81, 1.0), (89, 1.0), (90, .62), (93, .36), (97, .22), (99, .22),
       (101, .62), (117, .66), (133, .52), (149, .36), (161, .22),
       (165, .15)]
PEAK_BARS = (81, 88)
HUSH_BARS = (93, 100)
RETURN_BARS = (101, 116)


def _dyn(beat: float) -> float:
    bar = beat / 4.0 + 1.0
    for (b0, v0), (b1, v1) in zip(DYN, DYN[1:]):
        if b0 <= bar <= b1:
            return v0 + (v1 - v0) * (bar - b0) / (b1 - b0)
    return DYN[-1][1]


# ---------------------------------------------------------------------------
# The windowed emitter
# ---------------------------------------------------------------------------

class _Win:
    """Lets through only the events whose beat falls in [lo, hi)."""

    def __init__(self, sc: en.Score, lo: float, hi: float, last: bool):
        self.sc, self.lo, self.hi, self.last = sc, lo, hi, last

    def _in(self, beat: float) -> bool:
        return self.lo <= beat < self.hi or (self.last and beat == self.hi)

    def note(self, ch, p, beat, dur, vel, jt=5, jv=4):
        if self.lo <= beat < self.hi:
            self.sc.note(ch, p, beat, min(dur, END - beat), vel,
                         jt=jt, jv=jv)

    def hit(self, drum, beat, vel, jt=3, jv=5):
        self.note(SHK, drum, beat, 0.25, vel, jt=jt, jv=jv)

    def cc(self, ch, num, val, beat):
        if self._in(beat):
            self.sc.cc(ch, num, val, beat)


def _pool(pcs, lo: int, hi: int) -> list[int]:
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


# ---------------------------------------------------------------------------
# Lanes
# ---------------------------------------------------------------------------

def _marimbas(w) -> None:
    for bar in range(1, PULSE_BARS + 1):
        k = _stage(bar)
        for i in range(8):
            t = B(bar) + i * 0.5
            d = _dyn(t)
            acc = 9 if i == 0 else 4 if i == 4 else 0
            w.note(M1, CELL[i], t, 0.45, 34 + 66 * d + acc, jt=0, jv=2)
            if M2_FIRST <= bar <= M2_LAST:
                j = (i + k) % 8
                acc = 9 if j == 0 else 4 if j == 4 else 0
                w.note(M2, CELL[j], t, 0.45, 30 + 66 * d + acc, jt=0, jv=2)
    # the last stroke: both, together
    w.note(M1, CELL[0], B(161), 16, 62, jt=0, jv=0)
    w.note(M2, CELL[4], B(161), 16, 54, jt=0, jv=0)


def _top(g: int) -> int:
    """Top note of the two marimbas at global eighth index g."""
    k = _stage(g // 8 + 1)
    return max(CELL[g % 8], CELL[(g + k) % 8])


def _celesta(w) -> None:
    # the resultant: sound the composite's top voice whenever it MOVES
    for g in range((RESULT_BARS[0] - 1) * 8, RESULT_BARS[1] * 8):
        if _top(g) != _top(g - 1):
            t = g * 0.5
            w.note(CEL, _top(g) + 12, t, 0.45, 40 + 46 * _dyn(t), jt=0, jv=3)
    # after the return: a 3+3+2 glint taken from the cell itself
    for bar in range(117, 133):
        for i in (0, 3, 6):
            t = B(bar) + i * 0.5
            w.note(CEL, CELL[i] + 24, t, 0.6, 42 + 20 * _dyn(t), jt=0, jv=3)


def _rhodes(w) -> None:
    for u in range(2, 42):
        t0 = U(u)
        voicing = CHORD[FIELD[u - 1]][1]
        if u == 41:
            strikes = [(0.0, 16.0)]
        elif 17 <= u <= 22:
            strikes = [(4.0 * b, 3.7) for b in range(4)]
        else:
            strikes = [(0.0, 7.6), (8.0, 7.6)]
        for off, dur in strikes:
            v = 40 + 32 * _dyn(t0 + off)
            for i, p in enumerate(voicing):
                w.note(RHO, p, t0 + off + 0.02 * i, dur - 0.02 * i,
                       v - 2 * i, jt=0, jv=3)


def _bass_mode(u: int) -> str:
    if u <= 2:
        return "none"
    if u == 41:
        return "final"
    if u in (24, 25):
        return "held"
    if 9 <= u <= 16 or 26 <= u <= 33:
        return "flow"
    if 17 <= u <= 22:
        return "drive"
    return "calm"


def _bass(w) -> None:
    for u in range(1, 42):
        mode = _bass_mode(u)
        if mode == "none":
            continue
        t0 = U(u)
        r = CHORD[FIELD[u - 1]][0]
        nxt = CHORD[FIELD[u]][0] if u < 41 else r
        app = nxt - 1                    # the step below the next root

        def put(deg, on, dur, edge=False):
            p = en.pitch(BASSBASE, MODE, deg)
            if p > 54:
                p -= 12
            v = 58 + 40 * _dyn(t0 + on) + (6 if on == 0 else 0)
            w.note(BASS, p, t0 + on, dur, v, jt=0 if on % 4 == 0 else 3,
                   jv=3)

        if mode == "final":
            put(r, 0, 16)
            w.note(BASS, BASSBASE, t0, 16, 62, jt=0, jv=0)
        elif mode == "held":
            put(r, 0, 7.7)
            put(r, 8, 7.7)
        elif mode == "calm":
            put(r, 0, 5.8)
            put(r + 4, 6, 1.8)
            put(r, 8, 5.8)
            put(app, 14, 1.8)
        elif mode == "flow":
            for bar, cells in enumerate([
                    [(0, 0, 1.35), (0, 1.5, 1.35), (4, 3, 0.9)],
                    [(7, 0, 1.4), (4, 1.5, 1.35), (2, 3, 0.9)],
                    [(0, 0, 1.35), (0, 1.5, 1.35), (4, 3, 0.9)],
                    [(2, 0, 1.4), (1, 1.5, 1.4), (None, 3, 0.9)]]):
                for off, on, dur in cells:
                    put(app if off is None else r + off, 4 * bar + on, dur)
        else:                            # drive
            for bar in range(3):
                for off, on, dur in [(0, 0, 1.35), (0, 1.5, 0.45),
                                     (7, 2, 0.9), (4, 3, 0.45),
                                     (7, 3.5, 0.45)]:
                    put(r + off, 4 * bar + on, dur)
            for off, on, dur in [(0, 0, 0.9), (2, 1, 0.9), (4, 2, 0.9),
                                 (None, 3, 0.9)]:
                put(app if off is None else r + off, 12 + on, dur)


def _sing(w, ch, t0, notes, octave=0, double=False, vib=False,
          lift=0) -> None:
    """A long-breathed line: every note gets its own CC11 arc."""
    for deg, on, du in notes:
        t = t0 + on
        d = _dyn(t)
        p = en.pitch(SONG, MODE, deg) + 12 * octave
        vel = 66 + 34 * d + lift
        w.note(ch, p, t, du * 0.97, vel, jt=0, jv=3)
        if double:
            w.note(ch, p - 12, t, du * 0.97, vel - 8, jt=0, jv=3)
        peak = min(127, int(64 + 60 * d) + lift)
        en.cc_curve(w, ch, 11, [(t, peak - 22), (t + du * 0.55, peak),
                                (t + du * 0.97, peak - 12)], step=0.5)
        if vib and du >= 4:
            en.cc_curve(w, ch, 1, [(t, 6), (t + du * 0.6, 52),
                                   (t + du * 0.97, 28)], step=0.5)
        elif vib:
            w.cc(ch, 1, 14, t)


def _flute(w) -> None:
    _sing(w, FLU, U(5), T1, vib=True, lift=6)
    _sing(w, FLU, U(9), T2, vib=True, lift=6)
    _sing(w, FLU, U(13), D1, vib=True)
    _sing(w, FLU, U(17), [x for x in T3 if x[1] >= 32], vib=True)
    _sing(w, FLU, U(24), EBB_FLU, vib=True, lift=10)
    _sing(w, FLU, U(26), T1, vib=True, lift=6)
    _sing(w, FLU, U(30), T2, vib=True, lift=6)
    _sing(w, FLU, U(34), [(8, 0, 8), (5, 8, 7)], vib=True, lift=8)
    _sing(w, FLU, U(36), [(6, 0, 8), (8, 8, 7)], vib=True, lift=8)
    _sing(w, FLU, U(37), [(7, 0, 8), (5, 8, 7)], vib=True, lift=8)
    _sing(w, FLU, U(38), [(8, 0, 14)], vib=True, lift=8)
    _sing(w, FLU, U(40), [(5, 0, 8), (3, 8, 7)], vib=True, lift=8)
    _sing(w, FLU, U(41), [(1, 0, 16)], vib=True, lift=8)


def _strings(w) -> None:
    # the tune
    _sing(w, STR, U(13), T1, double=True)
    _sing(w, STR, U(17), T3, double=True)
    _sing(w, STR, U(23), EBB_STR)
    _sing(w, STR, U(26), T1, octave=-1)
    _sing(w, STR, U(30), T2, octave=-1)
    _sing(w, STR, U(34), [(8, 0, 8)], octave=-1)
    # the swell bed
    for u in list(range(9, 24)) + list(range(26, 42)):
        t0 = U(u)
        voicing = list(CHORD[FIELD[u - 1]][2])
        if 17 <= u <= 22:
            voicing.append(voicing[1] + 12)
        for p in voicing:
            w.note(PAD, p, t0, 15.9, 46 + 40 * _dyn(t0), jt=0, jv=3)
        a = int(30 + 80 * _dyn(t0))
        m = int(38 + 86 * _dyn(t0 + 9))
        z = int(30 + 80 * _dyn(t0 + 15.5))
        if u == 41:
            m, z = a, 12
        en.cc_curve(w, PAD, 11, [(t0, a), (t0 + 9, min(127, m)),
                                 (t0 + 15.5, z)], step=0.5)


def _vibes(w) -> None:
    def dyad(u, on, dur, extra=None):
        t = U(u) + on
        lo, hi = CHORD[FIELD[u - 1]][3]
        v = 42 + 36 * _dyn(t)
        w.note(VIB, lo, t, dur, v, jt=3, jv=3)
        w.note(VIB, hi, t + 0.03, dur, v + 4, jt=3, jv=3)
        if extra is not None:
            w.note(VIB, extra, t + 0.06, dur, v, jt=3, jv=3)

    for u in range(4, 42):
        if u in (24, 25) or 26 <= u <= 33:
            continue
        if 17 <= u <= 22:
            top = CHORD[FIELD[u - 1]][2][1] + 12
            for b in range(4):
                dyad(u, 4.0 * b, 3.6, extra=top if b % 2 == 0 else None)
        elif u >= 34:
            dyad(u, 0, 15.5 if u == 41 else 12)
        else:
            dyad(u, 0, 7)
            dyad(u, 10, 5)
    for t0, cm in ((U(26), CM1), (U(30), CM2)):
        for deg, on, du in cm:
            t = t0 + on
            w.note(VIB, en.pitch(SONG, MODE, deg), t, du * 0.95,
                   58 + 30 * _dyn(t) + (5 if on % 8 == 0 else 0),
                   jt=0, jv=3)


def _glock(w) -> None:
    # the BEAM, augmented, each time landing its top note on an arrival
    for bar, vel in ((15, 58), (47, 66), (79, 88), (99, 50), (159, 52)):
        material.play_beam(w, GLK, B(bar), SONG + 12, MODE, stretch=4.0,
                           vel=vel, vel_end=vel + 10)
    # the summit: the cell once more, in quarters, on the subdominant
    material.play_beam(w, GLK, B(85), en.pitch(SONG + 12, MODE, 4),
                       "lydian", stretch=2.0, vel=96, vel_end=104)
    # glints on the second bar of each unit while the tune is in the air
    for u in list(range(13, 21)) + list(range(26, 34)):
        pool = _pool(CHORD[FIELD[u - 1]][4], 84, 95)
        t = U(u) + 4
        w.note(GLK, pool[u % len(pool)], t, 3.0, 40 + 30 * _dyn(t),
               jt=0, jv=3)


def _harp(w) -> None:
    for u in range(3, 42):
        t0 = U(u)
        pcs = CHORD[FIELD[u - 1]][4]
        if u == 41:
            en.strum(w, HARP, [45, 52, 57, 61, 64, 69, 73], t0, 16.0, 64,
                     spread=0.06)
        elif u in (3, 4, 38, 39, 40):
            pool = _pool(pcs, 72, 88)
            root = next(p for p in pool if p % 12 == pcs[0])
            w.note(HARP, root, t0, 6.0, 46 + 20 * _dyn(t0), jt=4)
            w.note(HARP, pool[1] if pool[1] != root else pool[2], t0 + 8,
                   6.0, 42 + 20 * _dyn(t0), jt=4)
        elif u in (24, 25):
            pass
        elif 17 <= u <= 22:
            pool = _pool(pcs, 52, 88)
            for bar in range(4):
                s = (4 * u + bar) % 3
                for i, ix in enumerate([0, 1, 2, 3, 4, 3, 2, 1]):
                    t = t0 + 4 * bar + i * 0.5
                    if u == 20 and bar == 3 and i >= 4:
                        break            # the glissando takes these beats
                    w.note(HARP, pool[(ix + s) % len(pool)], t, 0.9,
                           40 + 46 * _dyn(t) + (6 if i == 0 else 0), jt=3)
        elif 13 <= u <= 16 or 26 <= u <= 33:
            pool = _pool(pcs, 52, 88)
            for bar in (0, 2):
                s = bar // 2
                for i, ix in enumerate([0, 1, 2, 3, 4, 5, 4, 3]):
                    t = t0 + 4 * bar + i * 0.5
                    w.note(HARP, pool[(ix + s) % len(pool)], t, 0.9,
                           42 + 40 * _dyn(t) + (5 if i == 0 else 0), jt=3)
        else:
            pool = _pool(pcs, 57, 84)
            for bar in (0, 2):
                s = bar // 2
                for i in range(4):
                    t = t0 + 4 * bar + i
                    w.note(HARP, pool[(i + s) % len(pool)], t, 1.8,
                           44 + 30 * _dyn(t) + 3 * i, jt=4)
    # two glissandi: into the summit, and (softly) into the return
    en.run(w, HARP, B(80, 2), TONIC, MODE, list(range(1, 17)), 0.125,
           62, 98)
    en.run(w, HARP, B(100, 2), TONIC, MODE, list(range(1, 17)), 0.125,
           38, 72)


def _shaker(w) -> None:
    shape = [46, 26, 34, 26, 42, 26, 34, 30]
    for bar in list(range(29, 89)) + list(range(101, 149)):
        soft = 0.8 if bar >= 101 else 1.0
        for i in range(8):
            t = B(bar) + i * 0.5
            w.hit(70, t, shape[i] * soft * (0.55 + 0.75 * _dyn(t)))
    for u in range(17, 23):
        w.hit(81, U(u), 52, jt=0)


def _compose(w) -> None:
    _marimbas(w)
    _celesta(w)
    _rhodes(w)
    _bass(w)
    _flute(w)
    _strings(w)
    _vibes(w)
    _glock(w)
    _harp(w)
    _shaker(w)
    # the lamp tolls once, on the subdominant, as the light goes
    w.note(LAMP, material.LAMP_PITCH, U(39), 14.0, 66, jt=0, jv=0)


def _builder(index: int):
    _name, lo, hi = PART.MOVEMENTS[index]

    def build(sc: en.Score) -> None:
        _compose(_Win(sc, lo, hi, index == len(PART.MOVEMENTS) - 1))
    return build


BUILDERS = [_builder(i) for i in range(len(PART.MOVEMENTS))]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _tick(beat: float) -> int:
    return int(round(beat * en.PPQ))


def _by_tick(sc: en.Score, ch: int) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for beat, p, _v in material.note_ons(sc, ch):
        out.setdefault(_tick(beat), []).append(p)
    return out


def _o_cell(sc) -> list[str]:
    """The cell is built from the BEAM's pitches and opens with the BEAM."""
    fails = []
    beam = material.beam_pitches(TONIC, MODE)
    if CELL[:5] != beam:
        fails.append(f"cell {CELL} does not open with the BEAM {beam}")
    stray = sorted({p % 12 for p in CELL} - {p % 12 for p in beam})
    if stray:
        fails.append(f"cell uses pitch classes {stray} outside the BEAM")
    if len({tuple(CELL[k:] + CELL[:k]) for k in range(8)}) != 8:
        fails.append("the cell's eight rotations are not all distinct")
    for ch in (M1, M2):
        odd = sorted({p for _b, p, _v in material.note_ons(sc, ch)}
                     - set(CELL))
        if odd:
            fails.append(f"ch{ch} plays {odd}, which are not cell pitches")
    n = len(material.beam_statements(sc, M1))
    if n < PULSE_BARS - 1:
        fails.append(f"Marimba I states the BEAM {n} times, want one a bar "
                     f"(>= {PULSE_BARS - 1})")
    return fails


def _o_phase(sc) -> list[str]:
    """Every stage tick-verified: II is ahead by 0,1,..,7 eighths, then 0."""
    fails = []
    m1, m2 = _by_tick(sc, M1), _by_tick(sc, M2)
    runs: list[list[int]] = []           # [offset, first bar, bars]
    for bar in range(M2_FIRST, M2_LAST + 1):
        ticks = [_tick(B(bar) + i * 0.5) for i in range(8)]
        if [m1.get(t) for t in ticks] != [[p] for p in CELL]:
            fails.append(f"bar {bar}: Marimba I is not the cell")
            continue
        got = [m2.get(t) for t in ticks]
        ks = [k for k in range(8)
              if got == [[CELL[(i + k) % 8]] for i in range(8)]]
        if len(ks) != 1:
            fails.append(f"bar {bar}: Marimba II is no rotation of the cell")
            continue
        if runs and runs[-1][0] == ks[0]:
            runs[-1][2] += 1
        else:
            runs.append([ks[0], bar, 1])
    if fails:
        return fails[:6]
    seq = [r[0] for r in runs]
    if seq != [0, 1, 2, 3, 4, 5, 6, 7, 0]:
        fails.append(f"stage offsets run {seq}; want 0..7 then 0 (unison)")
        return fails
    for off, bar, n in runs[1:-1]:
        if not 4 <= n <= 12:
            fails.append(f"stage +{off} (bar {bar}) lasts {n} bars; a slip "
                         f"is due every few bars (4..12)")
    if runs[-1][2] < 16:
        fails.append(f"the returned unison lasts only {runs[-1][2]} bars")
    want = [(max(b, M2_FIRST), k) for b, k in STAGES]
    if [(r[1], r[0]) for r in runs] != want:
        fails.append(f"stages {[(r[1], r[0]) for r in runs]} differ from "
                     f"the declared STAGES {want}")
    return fails


def _o_pulse(sc) -> list[str]:
    """An unbroken eighth-note pulse for most of the track, on the grid."""
    fails = []
    m1 = _by_tick(sc, M1)
    missing = [g for g in range(PULSE_BARS * 8)
               if m1.get(g * en.PPQ // 2) != [CELL[g % 8]]]
    if missing:
        fails.append(f"{len(missing)} eighth slot(s) lack the pulse, first "
                     f"at beat {missing[0] / 2:.1f}")
    span = PULSE_BARS * 4.0 / END
    if span < 0.9:
        fails.append(f"pulse covers only {span:.0%} of the track")
    for ch in (M1, M2, CEL):
        off = [b for b, _p, _v in material.note_ons(sc, ch)
               if _tick(b) % (en.PPQ // 2)]
        if off:
            fails.append(f"ch{ch} has {len(off)} onset(s) off the eighth "
                         f"lattice, first at beat {off[0]:.3f}")
    return fails


def _o_field(sc) -> list[str]:
    """The field turns once per four bars; the bass carries its roots."""
    fails = []
    if len(FIELD) * 16.0 != END:
        fails.append("FIELD does not cover the track")
    bass = _by_tick(sc, BASS)
    for u in range(3, len(FIELD) + 1):
        got = bass.get(_tick(U(u)))
        want = ROOT_PC[FIELD[u - 1]]
        if not got or min(got) % 12 != want:
            fails.append(f"unit {u} (bar {4 * u - 3}): bass {got} is not "
                         f"the root of {FIELD[u - 1]}")
    cycles = sum(1 for u in range(0, len(FIELD) - 3)
                 if FIELD[u:u + 4] == CYCLE)
    if cycles < 6:
        fails.append(f"only {cycles} complete A-F#m-D-E turns, want >= 6")
    if FIELD[0] != "A" or FIELD[-1] != "A" or FIELD[25] != "A":
        fails.append("the field must open, return (bar 101) and close on A")
    # slow: the Rhodes never changes chord inside a unit
    for u in range(2, len(FIELD) + 1):
        want_pcs = {p % 12 for p in CHORD[FIELD[u - 1]][1]}
        got_pcs = {p % 12 for b, p, _v in material.note_ons(sc, RHO)
                   if U(u) - 0.01 <= b < U(u + 1) - 0.01}
        if got_pcs != want_pcs:
            fails.append(f"unit {u}: Rhodes pitch classes {sorted(got_pcs)} "
                         f"are not one {FIELD[u - 1]} chord")
    return fails[:8]


def _o_breath(sc) -> list[str]:
    """The tune floats in notes far longer than the pulse; flute first."""
    fails = []
    durs = []
    for ch in (FLU, STR):
        for on, off, p, _v in material.note_spans(sc, ch):
            durs.append(off - on)
            if off - on < 1.9:
                fails.append(f"ch{ch} note at beat {on:.1f} lasts only "
                             f"{off - on:.2f} beats (< 4 pulses)")
    mean = sum(durs) / max(1, len(durs))
    if mean < 4.0:
        fails.append(f"mean melody note {mean:.2f} beats; want >= 4 "
                     f"(8 pulses)")
    flute = material.note_ons(sc, FLU)
    strings = material.note_ons(sc, STR)
    if not flute or not strings or flute[0][0] >= strings[0][0]:
        fails.append("the flute must lead the tune before the strings")
    elif flute[0][0] < B(17):
        fails.append("the tune must wait for the process to begin (bar 17)")
    return fails[:8]


def _o_arc(sc) -> list[str]:
    """One great swell, a true hush, a clear return."""
    fails = []

    def e(b0, b1):
        return material.energy(sc, B(b0), B(b1 + 1))

    windows = [(e(b, b + 7), b) for b in range(1, BARS - 6, 4)]
    best = max(windows)
    if best[1] not in (77, 81):
        fails.append(f"the loudest 8 bars start at bar {best[1]}, not at "
                     f"the swell (77..81)")
    peak, hush, ret = e(*PEAK_BARS), e(*HUSH_BARS), e(*RETURN_BARS)
    intro = e(5, 16)
    if hush > 0.45 * peak:
        fails.append(f"hush {hush:.0f} is not under 45% of the peak "
                     f"{peak:.0f}")
    if ret < 1.5 * hush:
        fails.append(f"return {ret:.0f} does not clear the hush {hush:.0f} "
                     f"by half")
    if ret > 0.9 * peak:
        fails.append(f"return {ret:.0f} rivals the peak {peak:.0f}")
    if intro > ret:
        fails.append(f"intro {intro:.0f} is louder than the return "
                     f"{ret:.0f}")
    others = [x for x, b in windows if abs(b - 81) > 8]
    if max(others) > 0.92 * peak:
        fails.append("a second swell rivals the first; there is only one")
    return fails


def _o_counterpoint(sc) -> list[str]:
    """Tune and counter-line consonant (never unison) on structural beats."""
    fails = []
    for lead, counter, t0 in COUNTERPOINT:
        for k in range(8):
            beat = t0 + 8.0 * k
            a = material.sounding(sc, lead, beat)
            b = material.sounding(sc, counter, beat)
            if not a or not b:
                fails.append(f"beat {beat:.0f}: ch{lead} or ch{counter} "
                             f"is silent")
                continue
            ic = abs(max(a) - max(b)) % 12
            if ic == 0 or ic not in material.CONSONANT:
                fails.append(f"beat {beat:.0f}: ch{lead} {max(a)} against "
                             f"ch{counter} {max(b)} (interval class {ic})")
    return fails[:8]


def _o_mode(sc) -> list[str]:
    """Bright and weightless: A ionian, with no accidentals at all."""
    scale = {(TONIC + s) % 12 for s in en.MODES[MODE]}
    fails = []
    for ch in sorted(sc.events):
        if ch == SHK:
            continue
        bad = [(b, p) for b, p, _v in material.note_ons(sc, ch)
               if p % 12 not in scale]
        if bad:
            fails.append(f"ch{ch}: {len(bad)} note(s) outside A ionian, "
                         f"first pitch {bad[0][1]} at beat {bad[0][0]:.1f}")
    return fails


def _o_resultant(sc) -> list[str]:
    """The celesta plays exactly the top line the two marimbas make."""
    fails = []
    m1, m2 = _by_tick(sc, M1), _by_tick(sc, M2)
    step = en.PPQ // 2
    lo, hi = _tick(B(RESULT_BARS[0])), _tick(B(RESULT_BARS[1] + 1))

    def top(t):
        return max(m1.get(t, [0]) + m2.get(t, [0]))

    want = {t: top(t) + 12 for t in range(lo, hi, step)
            if top(t) != top(t - step)}
    got = {t: p for t, p in ((_tick(b), p) for b, p, _v
                             in material.note_ons(sc, CEL)) if lo <= t < hi}
    if got != want:
        diff = sorted(set(want.items()) ^ set(got.items()))
        fails.append(f"celesta differs from the marimbas' top line at "
                     f"{len(diff)} point(s), first at beat "
                     f"{diff[0][0] / en.PPQ:.1f}")
    if len(want) < 100:
        fails.append("the resultant is too thin to hear")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("t05_cell_from_beam", _o_cell(sc)))
    results.append(("t05_phase_process", _o_phase(sc)))
    results.append(("t05_unbroken_pulse", _o_pulse(sc)))
    results.append(("t05_harmonic_field", _o_field(sc)))
    results.append(("t05_long_breath", _o_breath(sc)))
    results.append(("t05_swell_and_return", _o_arc(sc)))
    results.append(("t05_counterpoint", _o_counterpoint(sc)))
    results.append(("t05_mode_purity", _o_mode(sc)))
    results.append(("t05_resultant_line", _o_resultant(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    def level(b0, b1):
        i0, i1 = ctx.bar_window(B(b0), B(b1 + 1))
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    peak = level(82, 87)
    hush = level(94, 98)
    ret = level(102, 115)
    intro = level(6, 15)
    tail = level(162, 164)
    out = []

    fails = []
    if peak - hush < 6.0:
        fails.append(f"peak {peak:.1f} dB is not 6 dB over the hush "
                     f"{hush:.1f} dB")
    out.append(("t05_audio_swell_over_hush", fails))

    fails = []
    if ret - hush < 3.0:
        fails.append(f"return {ret:.1f} dB does not clear the hush "
                     f"{hush:.1f} dB by 3 dB")
    if peak - ret < 1.5:
        fails.append(f"return {ret:.1f} dB rivals the peak {peak:.1f} dB")
    out.append(("t05_audio_clear_return", fails))

    fails = []
    if peak - intro < 3.0:
        fails.append(f"peak {peak:.1f} dB is not 3 dB over the intro "
                     f"{intro:.1f} dB")
    if ret - tail < 3.0:
        fails.append(f"the last bars {tail:.1f} dB do not settle 3 dB "
                     f"under the return {ret:.1f} dB")
    out.append(("t05_audio_arc_and_close", fails))
    return out
