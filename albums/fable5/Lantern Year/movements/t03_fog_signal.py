"""t03_fog_signal.py — Track 3 of *Lantern Year*: "Fog Signal" (March; ambient).

C lydian, quarter = 60, 4/4.  The lighthouse is blind: a fog bank has come in
off the water and the only clock left is the FOGHORN — a low two-note tuba
call (G2 falling to C2) that returns every 20 beats from the first bar to
the last, whatever else is happening.

Everything else is deliberately un-clocked.  The harmony plan (PLAN) moves in
segments of unequal length, never shorter than 8 beats; the droplet loops
(celesta 17 beats, crystal 23), the sweep-pad swells (13) and the sea's
breathing (11) are mutually incommensurate with the horn's 20, so nothing
lines up twice.  Nothing rises above mezzo-piano (velocity ceiling 64): the
dynamic arc is made of layers and expression curves, not attack.

Form (beats = seconds):
  I.   Fog Bank            0-60    sea, pad, the horn's first BEAM (C)
  II.  Bearings            60-132  the vibraphone tune, cello counter-line,
                                   fretless bass, choir humming; cello BEAM (G)
  III. The Keeper's Phrase 132-196 the cello borrows HYMN phrase 2 (the one
                                   that leans on the lydian F#) at stretch 2,
                                   then the one swell of the night: cello
                                   descant over the horn's BEAM (C)
  IV.  Thick Weather       196-248 the hush: pads, droplets, a beacon tapping
                                   F-O-G in Morse, the horn
  V.   The Signal Holds    248-300 the tune's opening recalled, II-V-I home in
                                   lydian, the cello's last BEAM (C), and the
                                   foghorn's low C outlasting everything
"""

from __future__ import annotations

import math
import sys

import conductor
import engine as en
import material

NUMBER = 3
TITLE = "Fog Signal"
FILE = "03 - Fog Signal.mid"
SEED = 20261203
COMMENT = ("Track 03 of 'Lantern Year' (Claude Fable 5): Fog Signal. March, "
           "ambient, C lydian at 60. A two-note foghorn returns every 20 "
           "beats, the one clock in the fog; pads, choir, vibraphone, cello "
           "and droplets drift over it in phrases of unequal length, never "
           "above mezzo-piano. The cello borrows a phrase of the keeper's "
           "hymn; a beacon taps FOG in Morse.")

MODE = "lydian"
TONIC = 48                       # C3 — degree 1 for the BEAM and the hymn
END = 300.0
CEIL = 64                        # mezzo-piano: no note-on above this

FOGHORN, HORN, CELLO, BASS, WARM, SWEEP, CHOIR, VIBES, CELESTA = range(9)
CRYSTAL, SEA, BEACON, FOGHORN2 = 10, 11, 12, 13
FOG_CHANNELS = (FOGHORN, FOGHORN2)   # tuba, and a trombone on the same call

_BOUNDS = [0.0, 60.0, 132.0, 196.0, 248.0, END]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Fog Bank", 0.0, 60.0),
               ("II. Bearings", 60.0, 132.0),
               ("III. The Keeper's Phrase", 132.0, 196.0),
               ("IV. Thick Weather", 196.0, 248.0),
               ("V. The Signal Holds", 248.0, END)],
    tempo_map=[(0.0, 60.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 0)],                     # C lydian: one sharp
    channels=[
        (FOGHORN, "foghorn (tuba)", 58, 127, 64, 80),
        (HORN, "french horn", 60, 100, 52, 78),
        (CELLO, "cello", 42, 100, 64, 62),
        (BASS, "fretless bass", 35, 92, 64, 35),
        (WARM, "warm pad", 89, 82, 46, 72),
        (SWEEP, "sweep pad", 95, 88, 84, 80),
        (CHOIR, "choir", 52, 84, 74, 78),
        (VIBES, "vibraphone", 11, 108, 42, 66),
        (CELESTA, "celesta droplets", 8, 84, 90, 76),
        (CRYSTAL, "crystal droplets", 98, 78, 36, 80),
        (SEA, "seashore", 122, 64, 64, 40),
        (BEACON, "morse beacon", 79, 62, 92, 85),
        (FOGHORN2, "foghorn (trombone)", 57, 104, 64, 80),
    ],
)

BEAM_CHANNELS = {HORN, CELLO}
PROGRAM_WHITELIST = {58, 57, 60, 42, 35, 89, 95, 52, 11, 8, 98, 122, 79}
CENTERED_CHANNELS = {FOGHORN, FOGHORN2, CELLO, BASS, SEA}
NOTE_RANGES = {
    FOGHORN: (36, 43), FOGHORN2: (36, 43), HORN: (48, 62), CELLO: (43, 69), BASS: (28, 43),
    WARM: (43, 72), SWEEP: (67, 90), CHOIR: (55, 74), VIBES: (62, 79),
    CELESTA: (79, 96), CRYSTAL: (67, 84), SEA: (60, 64), BEACON: (83, 83),
}
GAP_WHITELIST: list = []         # the sea never stops
BEND_EXEMPT: set = set()
DURATION_WINDOW = (298.0, 306.0)
BOUNDS_WHITELIST: list = []

# ---------------------------------------------------------------------------
# Harmony — the plan every harmonic lane reads.  (bass pc, chord pcs)
# ---------------------------------------------------------------------------

_C, _D, _E, _FS, _G, _A, _B = 0, 2, 4, 6, 7, 9, 11
LYDIAN_PCS = {_C, _D, _E, _FS, _G, _A, _B}

CHORDS = {
    "Cmaj9":  (_C, (_C, _E, _G, _B, _D)),
    "Clyd":   (_C, (_C, _E, _FS, _G, _B)),       # Cmaj7(#11)
    "C/E":    (_E, (_C, _E, _G, _B)),
    "D/C":    (_C, (_C, _D, _FS, _A, _E)),       # the lydian II over the tonic
    "Am9":    (_A, (_A, _C, _E, _G, _B)),
    "Em7":    (_E, (_E, _G, _B, _D, _FS)),
    "Gmaj7":  (_G, (_G, _B, _D, _FS, _A)),
    "F#m7b5": (_FS, (_FS, _A, _C, _E)),          # hymn chord 4 in lydian
    "D69":    (_D, (_D, _FS, _A, _B, _E)),       # hymn chord 2 in lydian
}

# (start beat, chord, warm-pad voicing).  Segment lengths:
# 24 20 16 | 12 16 10 14 12 8 | 8 8 8 8 12 12 8 | 20 16 16 | 12 10 14 16
PLAN = [
    (0.0, "Cmaj9", [48, 55, 62]),
    (24.0, "D/C", [48, 57, 62, 66]),
    (44.0, "Clyd", [48, 55, 59, 66]),
    (60.0, "Am9", [45, 55, 59, 60, 64]),
    (72.0, "Em7", [52, 55, 59, 62, 66]),
    (88.0, "D/C", [48, 57, 62, 66]),
    (98.0, "Cmaj9", [48, 55, 59, 62, 64]),
    (112.0, "Gmaj7", [55, 59, 62, 66]),
    (124.0, "C/E", [52, 55, 60, 64]),
    (132.0, "F#m7b5", [54, 57, 60, 64]),
    (140.0, "D69", [50, 57, 59, 64]),
    (148.0, "Clyd", [48, 55, 59, 64]),
    (156.0, "Gmaj7", [55, 59, 62, 66]),
    (164.0, "Em7", [52, 59, 62, 67]),
    (176.0, "Cmaj9", [48, 55, 62, 64, 71]),
    (188.0, "D/C", [48, 57, 62, 66]),
    (196.0, "Am9", [45, 52, 59, 60]),
    (216.0, "Clyd", [48, 55, 66]),
    (232.0, "Em7", [52, 59, 62]),
    (248.0, "D/C", [48, 57, 62, 66]),
    (260.0, "Gmaj7", [55, 59, 62, 66]),
    (270.0, "Cmaj9", [48, 55, 62, 64]),
    (284.0, "Clyd", [48, 55, 59, 64, 66]),
]
HARMONY_CHANNELS = (WARM, SWEEP, CHOIR, CELESTA, CRYSTAL)
MIN_HARMONIC_SPAN = 8.0


def _segments() -> list:
    """[(t0, t1, chord name)] from PLAN."""
    out = []
    for i, (t0, name, _v) in enumerate(PLAN):
        t1 = PLAN[i + 1][0] if i + 1 < len(PLAN) else END
        out.append((t0, t1, name))
    return out


def _chord_at(beat: float) -> str:
    name = PLAN[0][1]
    for t0, nm, _v in PLAN:
        if t0 <= beat + 1e-9:
            name = nm
    return name


def _common(t0: float, t1: float) -> list:
    """Pitch classes shared by every chord sounding during [t0, t1) — a
    held note picked from these never sours when the harmony turns."""
    pcs = set(CHORDS[_chord_at(t0)][1])
    for s0, s1, name in _segments():
        if s0 < t1 and s1 > t0:
            pcs &= set(CHORDS[name][1])
    if len(pcs) < 2:
        pcs = set(CHORDS[_chord_at(t0)][1])
    return sorted(pcs)


# ---------------------------------------------------------------------------
# The clocks.  The foghorn is the strict one; the loops are chosen so that
# no two of them (nor any of them and the horn) start together twice.
# ---------------------------------------------------------------------------

FOG_FIRST = 6.0
FOG_PERIOD = 20.0
FOG_HIGH, FOG_LOW = 43, 36       # G2 falling to C2
FOG_DROP = 3.0                   # beats from the high note to the low


def _fog_times() -> list:
    out, t = [], FOG_FIRST
    while t + FOG_DROP + 2.0 <= END - 6.0:
        out.append(t)
        t += FOG_PERIOD
    return out


# lane -> (first cycle start, period, onset offsets in the cycle, last onset)
LOOPS = {
    CELESTA: (21.0, 17.0, (0.0, 2.5, 3.5, 9.0), 290.0),
    CRYSTAL: (9.0, 23.0, (0.0, 7.0, 11.5), 290.0),
    SWEEP: (34.0, 13.0, (0.0,), 285.0),
}
SEA_BREATH = 11.0


def _loop_onsets(ch: int) -> list:
    """[(beat, cycle index, offset index)] for one loop lane."""
    start, period, offsets, limit = LOOPS[ch]
    out, k = [], 0
    while start + k * period < limit:
        for j, off in enumerate(offsets):
            b = start + k * period + off
            if b < limit:
                out.append((b, k, j))
        k += 1
    return out


MORSE_UNIT = 0.25
MORSE_TEXT = "FOG"
BEACON_PITCH = 83                # B5: far off, glassy
BEACON_TIMES = (50.5, 197.5, 233.5)


def _morse_symbols(t0: float) -> list:
    """[(onset, nominal length)] for MORSE_TEXT keyed from t0."""
    out, b = [], t0
    for letter in MORSE_TEXT:
        for sym in en._MORSE[letter]:
            ln = (3 if sym == "-" else 1) * MORSE_UNIT
            out.append((b, ln))
            b += ln + MORSE_UNIT
        b += 2 * MORSE_UNIT
    return out


# ---------------------------------------------------------------------------
# The written lines — (pitch, onset, dur, vel).
# ---------------------------------------------------------------------------

# The tune (vibraphone, movement II): "E B A, F# G" — mi-ti-la, fi-sol.
VIBES_TUNE = [
    (64, 61.0, 2.0, 50), (71, 63.0, 3.0, 54), (69, 66.0, 2.5, 52),
    (66, 68.5, 1.5, 50), (67, 70.0, 4.5, 54),
    (74, 75.5, 2.0, 54), (71, 77.5, 1.5, 50), (74, 79.0, 3.0, 54),
    (76, 82.0, 1.5, 56), (78, 83.5, 4.5, 58),
    (76, 88.5, 1.5, 54), (74, 90.0, 2.5, 54), (69, 92.5, 2.0, 50),
    (66, 94.5, 3.5, 50),
    (67, 99.0, 2.0, 50), (71, 101.0, 3.0, 54), (74, 104.0, 2.0, 56),
    (76, 106.0, 5.0, 58),
    (78, 112.5, 2.5, 58), (74, 115.0, 2.0, 54), (71, 117.0, 3.0, 52),
    (69, 120.0, 2.0, 50), (66, 122.0, 2.5, 48),
    (64, 125.0, 2.0, 48), (67, 127.0, 1.5, 48), (64, 128.5, 3.5, 44),
]
VIBES_REST = [
    # III: answers in the gaps of the cello's hymn phrase
    (76, 134.0, 3.0, 46), (72, 137.5, 2.5, 44),
    (71, 142.0, 3.0, 46), (78, 145.5, 2.5, 46),
    (67, 149.5, 2.0, 46), (71, 151.5, 3.0, 48),
    (69, 157.5, 2.5, 48), (74, 160.0, 3.5, 50),
    # the swell: a slow chain of bells falling against the rising BEAM
    (67, 165.5, 2.0, 54), (71, 167.5, 2.5, 56), (74, 170.0, 2.5, 58),
    (78, 172.5, 3.5, 60),
    (79, 177.0, 2.5, 60), (76, 179.5, 2.5, 60), (74, 182.0, 2.5, 58),
    (71, 184.5, 2.5, 58), (67, 187.0, 1.0, 54),
    (69, 188.5, 2.0, 58), (74, 190.5, 2.0, 58), (78, 192.5, 3.4, 56),
    # IV: three reminders, far apart
    (76, 209.0, 4.0, 36), (71, 221.0, 4.0, 34), (74, 239.0, 4.0, 36),
    # V: the opening motif recalled, then the way home
    (64, 249.0, 2.0, 46), (71, 251.0, 3.0, 50), (69, 254.0, 2.5, 48),
    (66, 256.5, 1.5, 46), (67, 258.0, 4.0, 50),
    (74, 263.0, 2.5, 48), (71, 265.5, 3.5, 46),
    (67, 271.0, 3.0, 44), (64, 275.0, 3.0, 42), (76, 280.0, 3.5, 44),
    (71, 285.0, 3.0, 40), (78, 288.5, 6.0, 42),
]

CELLO_II = [
    (47, 72.0, 6.0, 46), (50, 78.0, 4.0, 48), (52, 82.0, 6.0, 50),
    (57, 88.0, 5.0, 52), (54, 93.0, 5.0, 50),
    (55, 98.0, 6.0, 50), (52, 104.0, 4.0, 48), (50, 108.0, 4.2, 46),
]
CELLO_SWELL = [
    (52, 164.5, 2.0, 56), (59, 166.5, 3.0, 58), (57, 169.5, 2.0, 58),
    (54, 171.5, 1.5, 56), (55, 173.0, 3.0, 58),
    (64, 176.0, 3.0, 60), (62, 179.0, 2.5, 60), (60, 181.5, 2.0, 58),
    (59, 183.5, 2.5, 58), (64, 186.0, 2.0, 60),
    (69, 188.0, 3.0, 62), (66, 191.0, 2.0, 60), (64, 193.0, 2.6, 54),
]
CELLO_LATE = [
    (47, 236.0, 10.0, 36),
    (45, 248.5, 5.5, 46), (54, 254.0, 6.0, 50),
    (59, 260.0, 5.0, 52), (57, 265.0, 2.5, 50), (55, 267.5, 2.8, 48),
]
# BEAM statements: (channel, base pitch, onsets, durs, vel)
BEAMS = [
    (HORN, 48, (11.0, 14.0, 17.0, 19.0, 22.0), (3.0, 3.0, 2.0, 3.0, 8.0), 50),
    (CELLO, 43, (112.5, 115.0, 117.5, 119.5, 122.0),
     (2.5, 2.5, 2.0, 2.5, 8.0), 54),
    (HORN, 48, (176.5, 179.0, 181.5, 183.5, 186.0),
     (2.5, 2.5, 2.0, 2.5, 7.5), 58),
    (CELLO, 48, (270.5, 273.5, 276.5, 279.0, 282.0),
     (3.0, 3.0, 2.5, 3.0, 10.5), 54),
]
BEAM_MIN_SPAN = 8.0              # first to fifth onset: "very slow"

HYMN_AT = 132.0                  # cello: hymn phrase 2 (index 1), stretch 2
HYMN_STRETCH = 2.0
HYMN_VEL = 56

HORN_LINES = [
    (54, 36.0, 6.0, 42), (52, 48.0, 8.0, 40),
    (55, 100.0, 8.0, 44), (50, 114.0, 7.0, 42), (52, 126.0, 5.0, 42),
    (57, 140.5, 7.0, 46), (62, 157.0, 6.5, 48),
    (62, 165.0, 5.0, 52), (59, 170.0, 5.5, 52),
    (57, 250.0, 8.0, 46), (59, 261.0, 7.0, 46), (55, 271.5, 6.0, 44),
    (52, 278.5, 5.0, 42), (55, 285.0, 7.0, 40),
]

BASS_LINE = [
    (33, 60.0, 6.5, 48), (40, 66.5, 3.0, 44), (43, 69.5, 2.5, 44),
    (40, 72.0, 7.0, 50), (35, 79.0, 5.0, 46), (38, 84.0, 4.0, 46),
    (36, 88.0, 6.0, 50), (38, 94.0, 2.0, 44), (35, 96.0, 2.0, 44),
    (36, 98.0, 7.0, 50), (31, 105.0, 4.0, 46), (33, 109.0, 3.0, 46),
    (31, 112.0, 7.0, 50), (38, 119.0, 3.0, 46), (42, 122.0, 2.0, 46),
    (40, 124.0, 5.0, 50), (43, 129.0, 3.0, 46),
    (42, 132.0, 5.0, 52), (40, 137.0, 3.0, 48),
    (38, 140.0, 5.0, 52), (33, 145.0, 3.0, 48),
    (36, 148.0, 5.0, 52), (40, 153.0, 3.0, 48),
    (31, 156.0, 5.0, 54), (38, 161.0, 3.0, 50),
    (40, 164.0, 7.0, 56), (35, 171.0, 3.0, 52), (38, 174.0, 2.0, 52),
    (36, 176.0, 6.0, 58), (43, 182.0, 4.0, 54), (40, 186.0, 2.0, 52),
    (36, 188.0, 7.5, 56),
    (33, 196.0, 9.0, 42), (40, 208.0, 6.0, 38),
    (36, 216.0, 10.0, 40),
    (40, 232.0, 8.0, 40), (35, 241.0, 6.0, 38),
    (36, 248.0, 7.0, 48), (38, 255.0, 3.0, 44), (42, 258.0, 2.0, 44),
    (31, 260.0, 6.0, 50), (35, 266.0, 2.0, 46), (38, 268.0, 2.0, 46),
    (36, 270.0, 8.0, 50), (40, 278.0, 4.0, 44), (38, 282.0, 2.0, 42),
    (36, 284.0, 9.0, 46),
]

CHOIR_SEGS = [
    (74.0, 88.0, [59, 62]), (88.0, 98.0, [57, 62, 66]),
    (98.0, 112.0, [55, 59, 64]), (112.0, 124.0, [59, 62, 66]),
    (124.0, 132.0, [60, 64, 67]),
    (132.0, 140.0, [60, 64]), (140.0, 148.0, [57, 64, 66]),
    (148.0, 156.0, [55, 59, 64]), (156.0, 164.0, [59, 62, 66]),
    (164.0, 176.0, [59, 64, 67, 74]), (176.0, 188.0, [55, 64, 71, 74]),
    (188.0, 195.5, [57, 66, 69, 74]),
    (218.0, 230.0, [55, 59]),
    (249.0, 260.0, [57, 62, 66]), (260.0, 270.0, [59, 62, 67]),
    (270.0, 284.0, [55, 60, 64]), (284.0, 293.0, [55, 59, 64, 66]),
]

# dynamic-arc windows (also read by audio_checks)
PEAK_WIN = (164.0, 196.0)
HUSH_WIN = (200.0, 248.0)


# ---------------------------------------------------------------------------
# Emission.  Every lane is written for the whole track; each movement
# builder replays the lanes through a window so that note-ons land in their
# own movement (check_movement_bounds) in one deterministic order.
# ---------------------------------------------------------------------------

class _Win:
    """A Score view that keeps only events inside [lo, hi) and holds every
    velocity under the mezzo-piano ceiling."""

    def __init__(self, sc: en.Score, lo: float, hi: float) -> None:
        self.sc, self.lo, self.hi = sc, lo, hi
        self.first = lo <= 0.0
        self.last = hi >= END

    def _in(self, beat: float) -> bool:
        if self.first and beat < self.lo:
            return True
        if self.last and beat <= END:
            return beat >= self.lo
        return self.lo <= beat < self.hi

    def note(self, ch, p, beat, dur, vel, jt=0, jv=2):
        if self.lo <= beat < self.hi:
            self.sc.note(ch, p, beat, dur, min(vel, CEIL - jv), jt=jt, jv=jv)

    def cc(self, ch, num, val, beat):
        if self._in(beat):
            self.sc.cc(ch, num, val, beat)

    def bend(self, ch, beat, semis):
        if self._in(beat):
            self.sc.bend(ch, beat, semis)


def _crosses_boundary(t0: float, t1: float) -> bool:
    return any(t0 < b <= t1 for b in _BOUNDS[1:-1])


def _hairpin(w, ch, on, dur, lo, hi, at=0.45):
    en.expr_curve(w, ch, [(on, lo), (on + at * dur, hi),
                          (on + dur, lo + 8)], step=0.25)


def _bed(w, ch, segs, vel, tail=0.4, stagger=0.5):
    """Sustained chords with common tones tied across segment joins."""
    spans: dict = {}
    for t0, t1, pitches in segs:
        for i, p in enumerate(sorted(pitches)):
            runs = spans.setdefault(p, [])
            if runs and runs[-1][1] >= t0 - 1e-6:
                runs[-1][1] = t1 + tail
            else:
                runs.append([t0 + i * stagger, t1 + tail])
    notes = sorted((on, p, off) for p, runs in spans.items()
                   for on, off in runs)
    for on, p, off in notes:
        w.note(ch, p, on, off - on, vel, jt=0, jv=2)


def _sea(w):
    t, i = 0.0, 0
    while t < END - 1e-9:
        dur = min(28.0, END - t)
        ring = dur if t + dur >= END - 1e-9 else dur + 1.5
        w.note(SEA, 60 if i % 2 == 0 else 64, t, ring, 50, jt=0, jv=0)
        t += dur
        i += 1
    pts, k = [], 0
    half = SEA_BREATH / 2.0
    while k * half < END:
        b = k * half
        env = min(1.0, 0.45 + b / 14.0)
        if b > 288.0:
            env = en.lerp(1.0, 0.4, (b - 288.0) / 12.0)
        pts.append((b, int((58 if k % 2 == 0 else 104) * env)))
        k += 1
    pts.append((END, 26))
    en.cc_curve(w, SEA, 11, pts, step=0.5)


def _foghorn(w):
    times = _fog_times()
    for i, t in enumerate(times):
        low_dur = 4.5 if i == len(times) - 1 else 2.2
        # the horn itself never changes; it leans in only as much as the
        # weather around it thickens, so the clock stays readable
        top = 127 if (60.0 <= t < 196.0 or 246.0 <= t < 280.0) else 106
        for ch in FOG_CHANNELS:
            w.note(ch, FOG_HIGH, t, FOG_DROP, 64, jt=0, jv=0)
            w.note(ch, FOG_LOW, t + FOG_DROP, low_dur, 60, jt=0, jv=0)
            en.expr_curve(w, ch, [(t - 0.2, top - 40), (t + 1.2, top),
                                  (t + 2.8, top - 8), (t + FOG_DROP, top - 14),
                                  (t + FOG_DROP + low_dur, top - 50)],
                          step=0.2)


def _warm(w):
    segs = []
    for i, (t0, _name, voicing) in enumerate(PLAN):
        t1 = PLAN[i + 1][0] if i + 1 < len(PLAN) else END - 6.0
        segs.append((t0, t1, voicing))
    _bed(w, WARM, segs, 50, tail=0.5, stagger=0.6)
    en.expr_curve(w, WARM, [
        (0.0, 20), (8.0, 62), (44.0, 76), (60.0, 82), (132.0, 90),
        (164.0, 100), (188.0, 112), (196.0, 72), (216.0, 62), (248.0, 74),
        (262.0, 92), (284.0, 84), (294.5, 10)], step=1.0)


def _sweep(w):
    dur = 9.5
    for t, k, _j in _loop_onsets(SWEEP):
        pcs = _common(t, t + dur)
        pairs = [(a, b) for a in pcs for b in pcs
                 if (b - a) % 12 in (7, 5, 4, 9)]
        a, b = pairs[k % len(pairs)]
        lo = next(p for p in range(67, 80) if p % 12 == a)
        hush = HUSH_WIN[0] - 8.0 <= t < HUSH_WIN[1]
        for p in (lo, lo + (b - a) % 12):
            w.note(SWEEP, p, t, dur, 44, jt=0, jv=2)
        _hairpin(w, SWEEP, t, dur, 30, 112 if hush else 96)


def _choir(w):
    _bed(w, CHOIR, CHOIR_SEGS, 48, tail=0.4, stagger=0.5)
    en.expr_curve(w, CHOIR, [
        (74.0, 40), (90.0, 78), (132.0, 84), (164.0, 100), (188.0, 114),
        (195.5, 60), (218.0, 40), (224.0, 66), (230.0, 30), (249.0, 50),
        (262.0, 88), (284.0, 80), (293.0, 20)], step=1.0)
    # mm -> oo through II, opening to ah for the swell, closing again
    en.vowel_curve(w, CHOIR, [
        (74.0, 0), (110.0, 45), (132.0, 50), (164.0, 85), (190.0, 112),
        (196.0, 60), (218.0, 0), (249.0, 20), (270.0, 62), (284.0, 40),
        (294.0, 0)], step=0.5)


def _bass(w):
    for p, on, dur, vel in BASS_LINE:
        w.note(BASS, p, on, dur * 0.97, vel, jt=0, jv=2)


def _bow(w, notes, hi=114):
    for p, on, dur, vel in notes:
        w.note(CELLO, p, on, dur * 0.98, vel, jt=0, jv=2)
        _hairpin(w, CELLO, on, dur, hi - 40, hi)
        if dur >= 2.5 and not _crosses_boundary(on, on + dur):
            en.vibrato(w, CELLO, on, dur * 0.96, depth=0.10,
                       cycles_per_beat=5.0, delay=0.7, step=0.04)


def _beam(w, ch, base, onsets, durs, vel):
    pitches = material.beam_pitches(base, MODE)
    for p, on, dur in zip(pitches, onsets, durs):
        if ch == CELLO:
            _bow(w, [(p, on, dur, vel)], hi=108)
        else:
            w.note(ch, p, on, dur * 0.97, vel, jt=0, jv=2)
            _hairpin(w, ch, on, dur, 64, 110)


def _cello(w):
    _bow(w, CELLO_II, hi=92)          # under the vibraphone's tune
    _beam(w, *BEAMS[1])
    # the keeper's phrase: hymn phrase 2, where degree 4 is the lydian F#
    material.play_phrase(w, CELLO, HYMN_AT, TONIC, MODE, 1,
                         stretch=HYMN_STRETCH, vel=HYMN_VEL, gate=0.98,
                         jt=0, jv=2)
    for _d, on, du in material.hymn_phrase(1):
        t, dur = HYMN_AT + on * HYMN_STRETCH, du * HYMN_STRETCH
        _hairpin(w, CELLO, t, dur, 78, 116)
        en.vibrato(w, CELLO, t, dur * 0.96, depth=0.10,
                   cycles_per_beat=5.0, delay=0.7, step=0.04)
    _bow(w, CELLO_SWELL, hi=118)
    _bow(w, CELLO_LATE, hi=104)
    _beam(w, *BEAMS[3])


def _horn(w):
    _beam(w, *BEAMS[0])
    _beam(w, *BEAMS[2])
    for p, on, dur, vel in HORN_LINES:
        w.note(HORN, p, on, dur * 0.97, vel, jt=0, jv=2)
        _hairpin(w, HORN, on, dur, 60, 106, at=0.5)


def _vibes(w):
    for p, on, dur, vel in VIBES_TUNE + VIBES_REST:
        w.note(VIBES, p, on, dur * 1.3, vel, jt=3, jv=2)


def _droplets(w, ch, lo, hi, picks, vel):
    for t, k, j in _loop_onsets(ch):
        pcs = _common(t, t + 2.0)
        cand = [p for p in range(lo, hi + 1) if p % 12 in pcs]
        p = cand[(3 * k + picks[j]) % len(cand)]
        w.note(ch, p, t, 3.0, vel + (5 if j == 0 else 0), jt=0, jv=3)


def _beacon(w):
    for t0 in BEACON_TIMES:
        for on, ln in _morse_symbols(t0):
            w.note(BEACON, BEACON_PITCH, on, ln * 0.85, 40, jt=0, jv=0)


def _emit(sc: en.Score, k: int) -> None:
    lo, hi = _BOUNDS[k], _BOUNDS[k + 1]
    w = _Win(sc, lo, hi)
    _sea(w)
    _foghorn(w)
    _warm(w)
    _sweep(w)
    _choir(w)
    _bass(w)
    _cello(w)
    _horn(w)
    _vibes(w)
    _droplets(w, CELESTA, 79, 96, (0, 3, 1, 4), 42)
    _droplets(w, CRYSTAL, 67, 84, (2, 0, 4), 40)
    _beacon(w)


def _b_fog_bank(sc):
    _emit(sc, 0)


def _b_bearings(sc):
    _emit(sc, 1)


def _b_keepers_phrase(sc):
    _emit(sc, 2)


def _b_thick_weather(sc):
    _emit(sc, 3)


def _b_signal_holds(sc):
    _emit(sc, 4)


BUILDERS = [_b_fog_bank, _b_bearings, _b_keepers_phrase, _b_thick_weather,
            _b_signal_holds]


# ---------------------------------------------------------------------------
# Oracles (written before the music).
# ---------------------------------------------------------------------------

def _o_foghorn(sc) -> list:
    """The one clock: a low two-note falling call on a strict period from
    the first bars to the last, and nothing else on its channel."""
    fails = []
    ons = material.note_ons(sc, FOGHORN)
    if [(round(b * en.PPQ), p) for b, p, _v in ons] != \
            [(round(b * en.PPQ), p)
             for b, p, _v in material.note_ons(sc, FOGHORN2)]:
        fails.append("the trombone does not double the tuba tick for tick")
    pitches = sorted({p for _b, p, _v in ons})
    if len(pitches) != 2:
        return [f"foghorn uses pitches {pitches}; a two-note call needs 2"]
    low, high = pitches
    if high > 48:
        fails.append(f"foghorn high note {high} is not low (<= C3)")
    highs = [round(b * en.PPQ) for b, p, _v in ons if p == high]
    lows = [round(b * en.PPQ) for b, p, _v in ons if p == low]
    if len(highs) != len(lows):
        fails.append(f"{len(highs)} high notes vs {len(lows)} low notes")
    gaps = {b - a for a, b in zip(highs, highs[1:])}
    if gaps != {round(FOG_PERIOD * en.PPQ)}:
        fails.append(f"call-to-call gaps (ticks) {sorted(gaps)}; want only "
                     f"{round(FOG_PERIOD * en.PPQ)}")
    drops = {b - a for a, b in zip(highs, lows)}
    if len(drops) != 1 or min(drops, default=0) <= 0:
        fails.append(f"high-to-low spacing varies or rises: {sorted(drops)}")
    if highs and highs[0] > FOG_PERIOD * en.PPQ:
        fails.append("the first call comes later than one period in")
    if highs and END * en.PPQ - highs[-1] > FOG_PERIOD * en.PPQ:
        fails.append("the calls stop more than one period before the end")
    want = len(_fog_times())
    if len(highs) != want or want < 12:
        fails.append(f"{len(highs)} calls, want {want} (>= 12)")
    return fails


def _o_ceiling(sc) -> list:
    """Nothing above mezzo-piano, and no drum kit at all."""
    fails = []
    for ch in sorted(sc.events):
        loud = [(b, v) for b, _p, v in material.note_ons(sc, ch) if v > CEIL]
        if loud:
            fails.append(f"ch{ch}: {len(loud)} note(s) above velocity "
                         f"{CEIL}, first at beat {loud[0][0]:.1f} "
                         f"(vel {loud[0][1]})")
    if material.note_ons(sc, 9):
        fails.append("channel 9 plays: this track has no drum kit")
    return fails


def _o_harmonic_rhythm(sc) -> list:
    """Harmony moves no faster than once every 8 beats: the plan's segments
    are all >= 8 beats and really differ, every onset on a harmonic lane is
    a tone of the chord in force, and the bass states each new root."""
    fails = []
    segs = _segments()
    for (t0, t1, name), nxt in zip(segs, segs[1:] + [None]):
        if t1 - t0 < MIN_HARMONIC_SPAN - 1e-9:
            fails.append(f"{name} at beat {t0:.0f} lasts {t1 - t0:.1f} "
                         f"beats (< {MIN_HARMONIC_SPAN:.0f})")
        if nxt is not None and set(CHORDS[name][1]) == set(CHORDS[nxt[2]][1]):
            fails.append(f"segments at {t0:.0f} and {nxt[0]:.0f} are the "
                         f"same chord")
    for ch in HARMONY_CHANNELS:
        for beat, p, _v in material.note_ons(sc, ch):
            name = _chord_at(beat + 0.02)
            if p % 12 not in CHORDS[name][1]:
                fails.append(f"ch{ch} pitch {p} at beat {beat:.2f} is not "
                             f"a tone of {name}")
    # ... and so is every tone a bed is HOLDING once the join has settled
    # (a tie can carry a stranger across a bar line without a new onset)
    for ch in (WARM, CHOIR):
        for t0, t1, name in segs:
            for beat in (t0 + 1.5, (t0 + t1) / 2.0):
                for p in material.sounding(sc, ch, beat):
                    if p % 12 not in CHORDS[name][1]:
                        fails.append(f"ch{ch} holds pitch {p} at beat "
                                     f"{beat:.1f}, not a tone of {name}")
    bass = material.note_ons(sc, BASS)
    stated = 0
    for t0, t1, name in segs:
        first = [p for b, p, _v in bass if t0 - 0.02 <= b < t0 + 1.0]
        if not first:
            continue
        if first[0] % 12 != CHORDS[name][0]:
            fails.append(f"bass opens {name} at beat {t0:.0f} on pitch "
                         f"{first[0]}, not its root")
        else:
            stated += 1
    if stated < 16:
        fails.append(f"bass states only {stated} chord roots (need >= 16)")
    # plan-free cross-check: the warm pad never starts new notes at two
    # moments closer than 8 beats unless they belong to one staggered entry
    starts = sorted({b for b, _p, _v in material.note_ons(sc, WARM)})
    groups = [starts[0]] if starts else []
    for b in starts[1:]:
        if b - groups[-1] > 3.0:
            if b - groups[-1] < MIN_HARMONIC_SPAN - 3.0:
                fails.append(f"warm pad re-voices at {groups[-1]:.1f} and "
                             f"again at {b:.1f}")
            groups.append(b)
    return fails[:10]


def _o_lydian(sc) -> list:
    """C lydian, pure: no F natural (no pitch outside the mode) anywhere;
    F# is featured in the tune voices and present in every movement."""
    fails = []
    for ch in sorted(sc.events):
        if ch == 9:
            continue
        bad = [(b, p) for b, p, _v in material.note_ons(sc, ch)
               if p % 12 not in LYDIAN_PCS]
        if bad:
            fails.append(f"ch{ch}: {len(bad)} note(s) outside C lydian, "
                         f"first pitch {bad[0][1]} at beat {bad[0][0]:.1f}")
    total = sharp = 0.0
    for ch in (CELLO, VIBES, HORN):
        for on, off, p, _v in material.note_spans(sc, ch):
            total += off - on
            if p % 12 == _FS:
                sharp += off - on
    share = sharp / max(1e-9, total)
    if share < 0.10:
        fails.append(f"F# holds only {share:.1%} of the tune voices' "
                     f"sounding time (need >= 10%)")
    for name, t0, t1 in PART.MOVEMENTS:
        if not any(p % 12 == _FS and t0 <= b < t1
                   for ch in sc.events if ch != 9
                   for b, p, _v in material.note_ons(sc, ch)):
            fails.append(f"no F# anywhere in '{name}'")
    last = [p for ch in (WARM, CHOIR, VIBES)
            for p in material.sounding(sc, ch, END - 9.0)]
    if not any(p % 12 == _FS for p in last):
        fails.append("the final sonority has no F# (not a lydian close)")
    if [p % 12 for p in material.sounding(sc, BASS, END - 9.0)] != [_C]:
        fails.append("the bass is not on C under the final sonority")
    return fails


def _o_beam_slow(sc) -> list:
    """The BEAM, very slow, in the horn AND the cello."""
    fails = []
    for ch in sorted(BEAM_CHANNELS):
        ons = [b for b, _p, _v in material.note_ons(sc, ch)]
        starts = material.beam_statements(sc, ch)
        if not starts:
            fails.append(f"ch{ch} never states the BEAM")
        for s in starts:
            i = min(range(len(ons)), key=lambda j: abs(ons[j] - s))
            span = ons[i + 4] - ons[i]
            if span < BEAM_MIN_SPAN:
                fails.append(f"ch{ch} BEAM at beat {s:.1f} takes only "
                             f"{span:.1f} beats to reach the octave "
                             f"(need >= {BEAM_MIN_SPAN:.0f})")
    first = material.note_ons(sc, HORN)
    if not first or first[0][1] % 12 != _C \
            or material.beam_statements(sc, HORN)[:1] != [first[0][0]]:
        fails.append("the horn's first notes are not the BEAM on C")
    return fails


def _o_sea(sc) -> list:
    """Seashore under everything, breathing (a moving CC11 lane)."""
    fails = []
    spans = material.note_spans(sc, SEA)
    dry = [b + 0.5 for b in range(int(END))
           if not any(on <= b + 0.5 < off for on, off, _p, _v in spans)]
    if dry:
        fails.append(f"the sea is silent at {len(dry)} sampled beats, "
                     f"first {dry[0]:.1f}")
    lane = material.cc_lane(sc, SEA, 11)
    turns = 0
    for (_b0, a), (_b1, b), (_b2, c) in zip(lane, lane[1:], lane[2:]):
        if (b - a) * (c - b) < 0:
            turns += 1
    if turns < 40:
        fails.append(f"the sea breathes only {turns} times (need >= 40 "
                     f"turns of its expression lane)")
    return fails


def _o_unequal(sc) -> list:
    """Nothing lines up twice: each loop lane plays exactly its declared
    cycle, the periods are all different from the horn's, and no two clocks
    start a cycle together more than once in the whole track."""
    fails = []
    clocks = {"foghorn": [b for b, p, _v in material.note_ons(sc, FOGHORN)
                          if p == FOG_HIGH]}
    periods = {"foghorn": FOG_PERIOD}
    for ch in LOOPS:
        want = sorted({round(b * en.PPQ) for b, _k, _j in _loop_onsets(ch)})
        got = sorted({round(b * en.PPQ)
                      for b, _p, _v in material.note_ons(sc, ch)})
        if got != want:
            fails.append(f"ch{ch} does not play its declared loop "
                         f"({len(got)} onset ticks vs {len(want)})")
        clocks[f"ch{ch}"] = [b for b, _k, j in _loop_onsets(ch) if j == 0]
        periods[f"ch{ch}"] = LOOPS[ch][1]
        if len(clocks[f"ch{ch}"]) < 8:
            fails.append(f"ch{ch} loop runs only "
                         f"{len(clocks[f'ch{ch}'])} cycles")
    periods["sea"] = SEA_BREATH
    if len(set(periods.values())) != len(periods):
        fails.append(f"two clocks share a period: {periods}")
    names = sorted(clocks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            hits = [x for x in clocks[a]
                    if any(abs(x - y) < 0.5 for y in clocks[b])]
            if len(hits) > 1:
                fails.append(f"{a} and {b} start together {len(hits)} "
                             f"times (beats {hits[:4]})")
    return fails


def _o_arc(sc) -> list:
    """One swell and one true hush, inside the mezzo-piano ceiling."""
    fails = []
    e_open = material.energy(sc, 0.0, 60.0)
    e_two = material.energy(sc, 60.0, 132.0)
    e_peak = material.energy(sc, *PEAK_WIN)
    e_hush = material.energy(sc, *HUSH_WIN)
    e_end = material.energy(sc, 286.0, END)
    if not e_open < e_two < e_peak:
        fails.append(f"no build: opening {e_open:.1f}, bearings "
                     f"{e_two:.1f}, swell {e_peak:.1f}")
    if e_peak < 2.0 * e_hush:
        fails.append(f"swell {e_peak:.1f} is not twice the hush "
                     f"{e_hush:.1f}")
    if e_end > 0.5 * e_peak:
        fails.append(f"the ending ({e_end:.1f}) does not subside")
    tune = (CELLO, VIBES, HORN)
    if material.energy(sc, *HUSH_WIN, channels=tune) \
            > 0.2 * material.energy(sc, *PEAK_WIN, channels=tune):
        fails.append("the tune voices do not withdraw in the hush")
    return fails


def _o_hymn(sc) -> list:
    """The cello borrows hymn phrase 2 (the lydian one) at stretch 2."""
    found = material.phrase_statements(sc, CELLO, MODE, 1)
    if not any(abs(s - HYMN_AT) < 0.05 and abs(st - HYMN_STRETCH) < 0.01
               and base == TONIC for s, st, base in found):
        return [f"hymn phrase 2 not found on the cello at beat "
                f"{HYMN_AT:.0f} (found {found})"]
    return []


def _o_morse(sc) -> list:
    """The beacon lane decodes to FOG, every time it keys."""
    table = {v: k for k, v in en._MORSE.items()}
    spans = material.note_spans(sc, BEACON)
    words, word, letter = [], "", ""
    for i, (on, off, _p, _v) in enumerate(spans):
        letter += "-" if off - on > 1.5 * MORSE_UNIT else "."
        nominal = (3 if letter[-1] == "-" else 1) * MORSE_UNIT
        gap = (spans[i + 1][0] - on - nominal) if i + 1 < len(spans) else 99.0
        if gap > 2.0 * MORSE_UNIT:
            word += table.get(letter, "?")
            letter = ""
        if gap > 5.0 * MORSE_UNIT:
            words.append(word)
            word = ""
    fails = []
    if len(words) < 2 or any(wd != MORSE_TEXT for wd in words):
        fails.append(f"beacon keys {words}; want >= 2 x '{MORSE_TEXT}'")
    return fails


def _o_counterpoint(sc) -> list:
    """Cello against bass: consonant one beat into every harmony segment
    where both are sounding (the structural downbeats)."""
    fails, tested = [], 0
    for t0, _t1, name in _segments():
        c = material.sounding(sc, CELLO, t0 + 1.0)
        b = material.sounding(sc, BASS, t0 + 1.0)
        if not c or not b:
            continue
        tested += 1
        if (c[0] - b[0]) % 12 not in material.CONSONANT:
            fails.append(f"cello {c[0]} over bass {b[0]} at beat "
                         f"{t0 + 1.0:.0f} ({name}) is dissonant")
    if tested < 12:
        fails.append(f"only {tested} downbeats carry both cello and bass")
    return fails


def oracles(sc, info, spans) -> list:
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("fog_foghorn_strict_period", _o_foghorn(sc)))
    results.append(("fog_mezzo_piano_ceiling", _o_ceiling(sc)))
    results.append(("fog_harmonic_rhythm_8", _o_harmonic_rhythm(sc)))
    results.append(("fog_lydian_purity", _o_lydian(sc)))
    results.append(("fog_beam_very_slow", _o_beam_slow(sc)))
    results.append(("fog_sea_throughout", _o_sea(sc)))
    results.append(("fog_nothing_lines_up_twice", _o_unequal(sc)))
    results.append(("fog_dynamic_arc", _o_arc(sc)))
    results.append(("fog_keepers_phrase", _o_hymn(sc)))
    results.append(("fog_morse_FOG", _o_morse(sc)))
    results.append(("fog_cello_bass_downbeats", _o_counterpoint(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py).
# ---------------------------------------------------------------------------

def _tone_db(ctx, b0: float, b1: float, freq: float) -> float:
    """Goertzel level of one frequency in the mono sum over [b0, b1)."""
    i0, i1 = ctx.bar_window(b0, b1)
    i0, i1 = max(0, i0), min(len(ctx.l), i1)
    if i1 <= i0:
        return -120.0
    coeff = 2.0 * math.cos(2.0 * math.pi * freq / ctx.sample_rate)
    s1 = s2 = 0.0
    left, right = ctx.l, ctx.r
    for i in range(i0, i1):
        s0 = (left[i] + right[i]) * 0.5 + coeff * s1 - s2
        s2, s1 = s1, s0
    power = s1 * s1 + s2 * s2 - coeff * s1 * s2
    return ctx.db(2.0 * math.sqrt(max(power, 1e-12)) / (i1 - i0))


def audio_checks(ctx) -> list:
    def level(b0, b1):
        return ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(b0, b1)))

    peak = level(176.0, 192.0)
    hush = level(212.0, 225.0)          # between two foghorn calls
    opening = level(12.0, 24.0)
    tail = level(296.0, 300.0)

    arc = []
    if peak - hush < 6.0:
        arc.append(f"swell {peak:.1f} dB vs hush {hush:.1f} dB: "
                   f"{peak - hush:.1f} dB apart (need >= 6)")
    if peak - opening < 3.0:
        arc.append(f"swell {peak:.1f} dB is not 3 dB over the opening "
                   f"{opening:.1f} dB")

    horn = []
    g2 = 440.0 * 2.0 ** ((FOG_HIGH - 69) / 12.0)
    calls = _fog_times()
    for t in (calls[0], calls[11], calls[-1]):   # the three exposed calls
        on = _tone_db(ctx, t + 0.8, t + 2.8, g2)
        pre = _tone_db(ctx, t - 3.0, t - 1.0, g2)
        if on - pre < 10.0:
            horn.append(f"foghorn at beat {t:.0f}: G2 only {on - pre:.1f} "
                        f"dB above the bar before (need >= 10)")

    ending = []
    if peak - tail < 12.0:
        ending.append(f"tail {tail:.1f} dB is not 12 dB under the swell "
                      f"{peak:.1f} dB")
    if tail < -75.0:
        ending.append(f"tail {tail:.1f} dB: the sea has stopped breathing")
    return [("audio_swell_and_hush", arc),
            ("audio_foghorn_exposed", horn),
            ("audio_ending_subsides", ending)]
