"""t06_false_lights.py — track 6 of *Lantern Year*: "False Lights".

July, no moon.  Wreckers on the headland show a lantern to lure ships onto
the rocks.  5/4 noir (3+2) in F# phrygian at quarter = 104, 104 bars.

THE DEVICE.  The album's BEAM (1-5-6-5-8: F# C# D C# F#) is shown first
CORRUPTED — its fifth flattened to the tritone, F# C C# C F#, the true fifth
only brushed as a neighbour — by the vibraphone (the lantern), then as the
opening of the muted trumpet's tune, then hammered by the whole band until
the tritone is laid bare (a tutti F#, then a tutti C natural).  Silence.
Then an OPEN trumpet — the mute comes off, a channel that has not sounded
before — plays the true cell alone, and the same tune returns with its fifth
restored.  C natural is quarantined: it sounds only where the false light is
shown, and never while the true light holds.

The fretless bass carries a 3+2 ostinato (F# . F#' E | A G) whose last note,
the phrygian flat-2, leans on the tonic across almost every bar line — and at
the very end does not resolve: the last bass note is G.

  I    No Moon          bars 1-8     ostinato alone; the lantern (vibes) twice
  II   The Lure         bars 9-24    the tune (false form) x2, 2nd with counter
  III  Wreckers         bars 25-32   baritone bridge over a diatonic circle
  IV   The Watch        bars 33-48   muted-trumpet solo over the strict ostinato
  V    On the Rocks     bars 49-58   the tense tutti; the tritone bare; silence
  VI   The True Light   bars 59-82   the BEAM alone, the tune made true x2, codetta
  VII  Dark Water       bars 83-104  the false tune again, the beam far off, no cadence
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 6
TITLE = "False Lights"
FILE = "06 - False Lights.mid"
SEED = 20261206
COMMENT = ("False Lights - July, no moon. 5/4 noir (3+2) in F# phrygian: a "
           "fretless ostinato whose flat-2 leans on the tonic; the album's "
           "BEAM cell shown first corrupted (its fifth flattened to a "
           "tritone) by vibraphone and muted trumpet, hammered bare by the "
           "band, then answered after a silence by an open trumpet playing "
           "the true cell alone. It ends on the flat-2, unresolved.")

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

BAR = 5.0
N_BARS = 104
END = N_BARS * BAR
P = en.n


def _b(k: float) -> float:
    """Start beat of 1-based bar k."""
    return (k - 1) * BAR


M1, M2, M3, M4, M5, M6, M7 = (_b(1), _b(9), _b(25), _b(33), _b(49), _b(59),
                              _b(83))
T_TRUE = M6                      # beat 290: the true BEAM, alone
T_SLAM = _b(57)                  # the tritone laid bare: F# at +0, C at +3
PEAK = (_b(69), _b(77))          # the tune made true, second time (tutti)
TUTTI = (_b(49), _b(57))         # the tense tutti

BASS, TPT, BARI, VIB, GTR, VC, PNO, TREM, OPEN, KIT = range(10)

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. No Moon", M1, M2), ("II. The Lure", M2, M3),
               ("III. Wreckers", M3, M4), ("IV. The Watch", M4, M5),
               ("V. On the Rocks", M5, M6), ("VI. The True Light", M6, M7),
               ("VII. Dark Water", M7, END)],
    tempo_map=[(0.0, 104.0)],
    time_signatures=[(0.0, 5, 4)],
    keysigs=[(0.0, 2, 1)],              # F# phrygian wears D major's two sharps
    channels=[
        (BASS, "fretless bass", 35, 74, 64, 24),
        (TPT, "muted trumpet", 59, 118, 64, 46),
        (BARI, "baritone sax", 67, 110, 48, 40),
        (VIB, "vibraphone", 11, 106, 84, 62),
        (GTR, "jazz guitar", 26, 88, 42, 34),
        (VC, "cello", 42, 108, 76, 54),
        (PNO, "low piano", 0, 88, 56, 44),
        (TREM, "tremolo strings", 44, 88, 70, 70),
        (OPEN, "open trumpet", 56, 127, 64, 52),
        (KIT, "brush kit", 0, 96, 64, 30),
    ],
    program_changes=[(KIT, 0.0, 40)],
    extra_markers=[(_b(3), "the false light"), (T_SLAM + 3.0, "the tritone, bare"),
                   (_b(95), "the beam, far off")],
)

BEAM_CHANNELS = {OPEN, VIB, VC, BASS, TPT}
PROGRAM_WHITELIST = {35, 59, 67, 11, 26, 42, 0, 44, 56}   # ch 9 kit select is exempt
CENTERED_CHANNELS = {BASS, TPT, OPEN, KIT}
NOTE_RANGES = {BASS: (28, 60), TPT: (57, 86), BARI: (36, 69), VIB: (53, 89),
               GTR: (40, 76), VC: (36, 76), PNO: (21, 72), TREM: (48, 91),
               OPEN: (58, 82)}
GAP_WHITELIST = [(T_SLAM + 4.0, T_TRUE + 0.5)]    # the dark before the true light
BEND_EXEMPT: set = set()
DURATION_WINDOW = (298.0, 304.0)
BOUNDS_WHITELIST: list = []

# Where the false light is shown: the only places C natural may sound.
FALSE_WINDOWS = [(_b(3), _b(5)), (_b(7), _b(11)), (_b(17), _b(19)),
                 (M5, M6), (_b(83), _b(85)), (_b(93), _b(95)),
                 (_b(101), _b(103))]

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Bass cells on the 3+2 grid: onsets 0, 1.5, 2 | 3, 4.
C_OST = (42, 54, 52, 45, 43)      # F# F#' E | A G     the ostinato
C_FALSE = (42, 54, 52, 48, 43)    # F# F#' E | C G     under the false light
C_TRUE = (42, 49, 52, 45, 43)     # F# C# E | A G      the fifth restored
C_HAMMER = (42, 42, 54, 48, 43)   # F# F# F#' | C G    the tutti
C_G = (43, 55, 54, 47, 43)
C_BM = (47, 59, 57, 50, 54)
C_EM = (40, 52, 50, 43, 47)
C_A = (45, 57, 55, 49, 52)
C_D = (38, 50, 49, 42, 45)
C_CS = (37, 49, 47, 40, 43)
C_SUS = (42, 54, 52, 47, 43)
_ONS = (0.0, 1.5, 2.0, 3.0, 4.0)
_DUR = (1.38, 0.42, 0.9, 0.94, 0.9)
_ACC = (10, -8, -3, 7, -4)

GV = {"F#m": [52, 57, 61, 64], "F#o": [52, 57, 60, 64], "G": [55, 59, 62, 66],
      "Bm": [57, 59, 62, 66], "Em": [55, 59, 62, 64], "A": [55, 57, 61, 64],
      "D": [54, 57, 61, 66], "C#o": [52, 55, 59, 61], "F#sus": [52, 55, 59, 61]}
VV = {"F#m": [64, 69, 73], "F#o": [64, 69, 72], "G": [66, 71, 74],
      "Bm": [66, 69, 74], "Em": [67, 71, 74], "A": [67, 73, 76],
      "D": [66, 69, 73], "C#o": [67, 71, 76], "F#sus": [64, 67, 71]}
TV = {"F#m": [61, 64, 69], "F#o": [60, 64, 69], "G": [62, 66, 71],
      "Bm": [62, 66, 71], "Em": [59, 64, 67], "A": [61, 64, 67],
      "D": [62, 66, 69], "C#o": [61, 64, 67], "F#sus": [61, 64, 67]}
ROOT1 = {"F#m": 30, "F#o": 30, "F#sus": 30, "G": 31, "A": 33, "Bm": 35,
         "C#o": 37, "D": 38, "Em": 28}
SHELL = {"F#m": [52, 57], "F#o": [48, 52, 57], "G": [54, 59], "Bm": [50, 57],
         "Em": [50, 55], "A": [49, 55], "D": [49, 54], "C#o": [47, 52, 55],
         "F#sus": [47, 52, 55]}

_GRIDS = {
    "slow": [(0, 1.5), (1.5, 1.5), (3, 1), (4, 1), (5, 3.0)],
    "flick": [(3, .5), (3.5, .5), (4, .5), (4.5, .5), (5, 4.0)],
    "press": [(0, .75), (.75, .75), (1.5, .75), (2.25, .75), (3, 1.9)],
    "snap": [(0, .5), (.5, .5), (1, .5), (1.5, .5), (2, .9)],
    "canon": [(3, 1), (4, 1), (5, 1), (6, 1), (7, 2.8)],
}


def _light(true: bool, rhythm: str = "slow", s: int = 1, octave: int = 4):
    """The five-note light as bar lists: the BEAM (true) or the wreckers'
    lantern (its fifth flattened to a tritone)."""
    f = 7 if true else 6
    base = 66 + 12 * (octave - 4)
    pitches = [base, base + f, base + f + s, base + f, base + 12]
    bars: list = [[], []]
    for p, (on, du) in zip(pitches, _GRIDS[rhythm]):
        bars[int(on // BAR)].append((p, on % BAR, du))
    return bars


def _head(true: bool):
    """The tune, 8 bars.  Its first five notes ARE the light."""
    f, nb = ("C#5", "D5") if true else ("C5", "C#5")
    return [
        [("F#4", 0, 1.5), (f, 1.5, 1.5), (nb, 3, 1), (f, 4, 1)],
        [("F#5", 0, 2.5), ("E5", 3, 1), ("D5", 4, 1)],
        [("B4", 0, 1.5), ("D5", 1.5, 1), ("B4", 2.5, .5), ("G4", 3, 2)],
        [("A4", 0, 1.5), ("G4", 1.5, .5), ("F#4", 2, 2.5)],
        [("B4", 0, 1.5), ("D5", 1.5, 1.5), ("F#5", 3, 1), ("E5", 4, 1)],
        [("G5", 0, 2), ("F#5", 2, .5), ("E5", 2.5, .5), ("C#5", 3, 1.5),
         ("A4", 4.5, .5)],
        [("B4", 0, 1.5), ("D5", 1.5, .5), ("B4", 2, 1), ("A4", 3, 1),
         ("G4", 4, 1)],
        [("F#4", 0, 3.5)],
    ]


def _counter(true: bool):
    """Baritone counter-melody: consonant with the tune on every downbeat."""
    c = "C#4" if true else "C4"
    return [
        [("A3", 0, 3), ("E3", 3, 2)],
        [("A3", 0, 1.5), (c, 1.5, .5), ("E4", 2, 1), ("D4", 3, 1), ("B3", 4, 1)],
        [("G3", 0, 2), ("F#3", 2, 1), ("E3", 3, 1), ("D3", 4, 1)],
        [("C#3", 0, 1.5), ("E3", 1.5, .5), ("F#3", 2, 1), ("A3", 3, 1),
         ("C#4", 4, 1)],
        [("D4", 0, 3), ("C#4", 3, 1), ("B3", 4, 1)],
        [("B3", 0, 2), ("G3", 2, 1), ("A3", 3, 1.5), ("G3", 4.5, .5)],
        [("D4", 0, 1.5), ("B3", 1.5, .5), ("G3", 2, 1), ("F#3", 3, 1),
         ("E3", 4, 1)],
        [("B2", 0, 1.5), ("C#3", 1.5, .5), ("E3", 2, 1), ("G3", 3, 1.5),
         ("F#3", 4.5, .5)],
    ]


def _cello_head(true: bool):
    a = "C#4" if true else "E4"
    return [
        [(a, 0, 5)], [(a, 0, 3), ("D4", 3, 2)],
        [("D4", 0, 3), ("F#4", 3, 2)], [("E4", 0, 5)],
        [("F#4", 0, 3), ("D4", 3, 2)], [("E4", 0, 3), ("G4", 3, 2)],
        [("F#4", 0, 3), ("D4", 3, 2)], [("C#4", 0, 3), ("B3", 3, 2)],
    ]


_SCALE = [p for p in range(24, 100) if (p - 6) % 12 in en.MODES["phrygian"]]


def _sixth_below(p: int) -> int:
    """The diatonic sixth below p in F# phrygian (a third above, 8vb)."""
    return _SCALE[_SCALE.index(p) - 5]


def _head_chords(true: bool):
    a = "F#m" if true else "F#o"
    return [(a, a), (a, "G"), ("G", "G"), ("F#m", "F#m"), ("Bm", "Bm"),
            ("Em", "A"), ("G", "G"), ("F#sus", "F#sus")]


def _head_bass(true: bool):
    return [C_TRUE if true else C_FALSE,
            (42, 49 if true else 54, 52, 47, 45), C_G, (42, 54, 52, 45, 49),
            C_BM, (40, 52, 50, 45, 47), C_G, C_SUS]


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def _mel(sc, ch, t0, bars, vel, expr=100, vib=0, gate=0.94, shift=0, jt=4,
         jv=4, vel_end=None) -> None:
    """Play bar lists of (pitch-or-name, on, dur[, flags]).  Long notes get
    a CC11 swell (and CC1 vibrato when vib); flags: v = vibrato, s = scoop
    up into the note, f = fall off its end (bends, recentred)."""
    count = len(bars)
    for i, notes in enumerate(bars):
        v = vel if vel_end is None else en.lerp(vel, vel_end,
                                                i / max(1, count - 1))
        for note in notes:
            name, on, du = note[0], note[1], note[2]
            flags = note[3] if len(note) > 3 else ""
            p = (name if isinstance(name, int) else P(name)) + shift
            t = t0 + i * BAR + on
            end = t + du * gate
            sc.note(ch, p, t, du * gate, int(round(v)), jt=jt, jv=jv)
            if expr:
                if du >= 1.5:
                    en.cc_curve(sc, ch, 11, [(t, expr - 16),
                                             (t + 0.5 * du, min(127, expr + 10)),
                                             (end, expr - 10)], step=0.25)
                else:
                    sc.cc(ch, 11, expr, t)
            if vib and (du >= 2.0 or "v" in flags):
                en.cc_curve(sc, ch, 1, [(t + 0.3 * du, 0), (t + 0.7 * du, vib),
                                        (end, vib)], step=0.25)
                sc.cc(ch, 1, 0, end + 0.02)
            if "s" in flags:
                en.bend_ramp(sc, ch, t - 0.02, t + 0.16, -0.8, 0.0, steps=5)
            if "f" in flags:
                en.bend_ramp(sc, ch, end - 0.4, end, 0.0, -1.8, steps=8)
                sc.bend(ch, end + 0.04, 0.0)


def _bass_bar(sc, t, cell, vel, ghost=None, slide=False) -> None:
    for i, p in enumerate(cell):
        sc.note(BASS, p, t + _ONS[i], _DUR[i], vel + _ACC[i],
                jt=0 if i in (0, 3) else 3, jv=3)
    if ghost is not None and not slide:
        sc.note(BASS, ghost, t + 2.5, 0.4, vel - 14, jt=3, jv=3)
    if slide:                       # fretless: the flat-2 slides into the tonic
        en.bend_ramp(sc, BASS, t + 4.55, t + 4.9, 0.0, -1.0, steps=7)
        sc.bend(BASS, t + BAR, 0.0)


def _bass_run(sc, k0, cells, vel, ghosts=()) -> None:
    """One cell per bar from bar k0.  Every second bar whose G falls to an
    F# slides into it — never the last bar of a run, so the bend is always
    recentred before a movement boundary."""
    for i, cell in enumerate(cells):
        v = vel[i] if isinstance(vel, (list, tuple)) else vel
        nxt = cells[i + 1] if i + 1 < len(cells) else None
        slide = (nxt is not None and i % 2 == 1 and cell[4] == 43
                 and nxt[0] == 42)
        _bass_bar(sc, _b(k0 + i), cell, v,
                  ghost=49 if i in ghosts else None, slide=slide)


_KIT = {
    "brush": [(36, 0, 46), (44, 1, 28), (38, 1.5, 30), (44, 2, 28),
              (38, 2.5, 26), (36, 3, 40), (38, 4, 34), (44, 4, 30),
              (38, 4.5, 24)],
    "ride": [(36, 0, 54), (51, 0, 56), (51, 1, 46), (44, 1, 34),
             (51, 1.5, 34), (51, 2, 48), (38, 2, 30), (44, 2, 30),
             (36, 3, 46), (51, 3, 54), (51, 4, 44), (38, 4, 46), (44, 4, 36),
             (51, 4.5, 34)],
    "hot": [(36, 0, 60), (51, 0, 64), (38, .5, 28), (51, 1, 52), (44, 1, 38),
            (36, 1.5, 40), (51, 1.5, 40), (51, 2, 54), (38, 2, 36),
            (44, 2, 34), (38, 2.5, 30), (36, 3, 54), (51, 3, 62),
            (38, 3.5, 32), (51, 4, 50), (38, 4, 58), (44, 4, 40),
            (51, 4.5, 40)],
    "tutti": [(36, 0, 88), (51, 0, 70), (38, 1, 44), (36, 1.5, 70),
              (40, 1.5, 62), (51, 1.5, 56), (38, 2, 48), (38, 2.5, 52),
              (36, 3, 86), (40, 3, 84), (51, 3, 70), (36, 4, 72),
              (40, 4, 70), (51, 4, 60), (38, 4.5, 56)],
    "pulse": [(36, 0, 36), (44, 1, 22), (44, 2, 22), (36, 3, 30),
              (44, 4, 24)],
}


def _kit(sc, t, style, lift=0, fill=False, crash=False, bell=False) -> None:
    for key, on, v in _KIT[style]:
        if fill and on >= 3 and key != 36:
            continue                         # the fill owns the 2-group
        sc.hit(key, t + on, max(8, v + lift))
    if fill:
        for i, on in enumerate((3.0, 3.5, 4.0, 4.5)):
            sc.hit(38, t + on, max(8, 40 + 8 * i + lift))
    if crash:
        sc.hit(49, t, max(8, 76 + lift))
    if bell:
        sc.hit(53, t, max(8, 62 + lift))
        sc.hit(53, t + 3, max(8, 58 + lift))


def _comp(sc, t, c1, c2, pat, vel) -> None:
    """Jazz-guitar comping in 3+2."""
    if pat == 0:
        en.strum(sc, GTR, GV[c1], t + 1.5, 0.4, vel - 6, spread=0.018)
        en.strum(sc, GTR, GV[c2], t + 3.0, 1.5, vel, spread=0.03)
    elif pat == 1:
        en.strum(sc, GTR, GV[c1], t, 0.9, vel, spread=0.03)
        en.strum(sc, GTR, GV[c1], t + 2.5, 0.35, vel - 8, spread=0.018,
                 down=False)
        en.strum(sc, GTR, GV[c2], t + 4.0, 0.6, vel - 4, spread=0.02)
    else:                                    # the hammer: 0, 1.5 | 3, 4
        for on, c in ((0.0, c1), (1.5, c1), (3.0, c2), (4.0, c2)):
            en.strum(sc, GTR, GV[c], t + on, 0.7, vel, spread=0.015)


def _toll(sc, t, chord, vel, dur=4.6) -> None:
    r = ROOT1[chord]
    sc.note(PNO, r, t, dur, vel, jt=2, jv=3)
    sc.note(PNO, r + 12, t, dur, vel - 6, jt=2, jv=3)


def _shell(sc, t, chord, vel, dur=1.6) -> None:
    for p in SHELL[chord]:
        sc.note(PNO, p, t, dur, vel, jt=3, jv=3)


def _sus(sc, ch, t, pitches, dur, vel, e0, e1) -> None:
    """A held chord with a CC11 ramp (tremolo strings, mostly)."""
    for p in pitches:
        sc.note(ch, p, t, dur - 0.06, vel, jt=3, jv=2)
    en.expr_curve(sc, ch, [(t, e0), (t + dur - 0.1, e1)], step=0.5)


def _vchord(sc, t, pitches, vel, ring=1.8) -> None:
    for p in pitches:
        sc.note(VIB, p, t, ring, vel, jt=0, jv=2)


def _vfill(sc, t, names, on, vel, ring=1.6) -> None:
    """A vibraphone answer: ascending eighths left to ring under the pedal."""
    en.sustain(sc, VIB, t + on, t + on + 0.5 * len(names) + ring)
    for i, name in enumerate(names):
        last = i == len(names) - 1
        sc.note(VIB, P(name), t + on + 0.5 * i, ring if last else 0.48,
                vel + 2 * i, jt=3, jv=3)


# ---------------------------------------------------------------------------
# The tune as a block (used false in II and VII, true in VI)
# ---------------------------------------------------------------------------

def _head_block(sc, k0, true, lead, lead_vel, bass_vel, kit, kit_lift=0,
                comp_vel=0, counter_vel=0, cello_vel=0, cello_double=False,
                trem_vel=0, trem_up=0, piano_vel=0, hammer=False, vib_vel=0,
                vib_double=False, crash=False, lead_expr=104,
                harmony_vel=0) -> None:
    t0 = _b(k0)
    chords = _head_chords(true)
    _mel(sc, lead, t0, _head(true), lead_vel, expr=lead_expr, vib=46)
    _bass_run(sc, k0, _head_bass(true), bass_vel)
    for i, (c1, c2) in enumerate(chords):
        t = t0 + i * BAR
        _kit(sc, t, kit, lift=kit_lift, fill=(i == 7),
             crash=(crash and i in (0, 4)), bell=(hammer and i % 2 == 0))
        if comp_vel:
            _comp(sc, t, c1, c2, 1 if hammer else i % 2, comp_vel)
        if piano_vel:
            if hammer:
                _toll(sc, t, c1, piano_vel, dur=2.8)
                _shell(sc, t + 1.5, c1, piano_vel - 12, dur=0.5)
                _shell(sc, t + 3.0, c2, piano_vel - 4, dur=1.7)
            else:
                if i in (0, 4):
                    _toll(sc, t, c1, piano_vel)
                if i % 2 == 1:
                    _shell(sc, t + 3.0, c2, piano_vel - 6)
        if trem_vel:
            lo, hi = (56, 80) if i % 2 == 0 else (80, 56)
            if hammer:
                lo, hi = lo + 30, hi + 30

            def voiced(c):
                base = list(TV[c])
                return base + [p + trem_up for p in base] if trem_up else base
            if c1 == c2:
                _sus(sc, TREM, t, voiced(c1), BAR, trem_vel, lo, hi)
            else:
                _sus(sc, TREM, t, voiced(c1), 3.0, trem_vel, lo,
                     (lo + hi) // 2)
                _sus(sc, TREM, t + 3.0, voiced(c2), 2.0, trem_vel,
                     (lo + hi) // 2, hi)
    if counter_vel:
        _mel(sc, BARI, t0, _counter(true), counter_vel, expr=98, vib=30)
    if cello_vel:
        if cello_double:
            _mel(sc, VC, t0, _head(true), cello_vel, expr=104, vib=36,
                 shift=-12)
        else:
            _mel(sc, VC, t0, _cello_head(true), cello_vel, expr=92, vib=30)
    if harmony_vel:
        # the muted trumpet is drawn in: the tune a diatonic sixth below
        _mel(sc, TPT, t0, [[(_sixth_below(P(nm)), on, du)
                            for nm, on, du in notes]
                           for notes in _head(true)], harmony_vel,
             expr=108, vib=30)
    if vib_vel:
        if vib_double:
            _mel(sc, VIB, t0, _head(true), vib_vel, expr=0, gate=1.0, jt=2)
        else:
            _vfill(sc, t0 + 3 * BAR, ["A4", "C#5", "E5", "A5"], 3.0, vib_vel)
            _vfill(sc, t0 + 7 * BAR, ["B4", "E5", "G5"], 3.5, vib_vel)


# ---------------------------------------------------------------------------
# I. No Moon — the ostinato alone; the lantern is shown twice
# ---------------------------------------------------------------------------

def _b_no_moon(sc) -> None:
    _bass_run(sc, 1, [C_OST, C_OST, C_FALSE, C_FALSE, C_OST, C_OST, C_FALSE,
                      C_FALSE], [74, 76, 78, 78, 80, 80, 82, 84])
    _toll(sc, _b(1), "F#m", 50)
    for k in range(2, 9):
        _kit(sc, _b(k), "brush", lift=k - 8, fill=(k == 8))
    # the lantern, first showing: F# C C# C F#, slow, left to ring
    en.sustain(sc, VIB, _b(3), _b(5) - 0.6)
    _mel(sc, VIB, _b(3), _light(False, "slow"), 84, expr=0, gate=1.0, jt=0)
    _sus(sc, TREM, _b(3), TV["F#o"], BAR, 44, 36, 66)
    _sus(sc, TREM, _b(4), TV["F#o"], BAR, 44, 66, 44)
    _shell(sc, _b(3) + 3.0, "F#o", 44)
    # a breath: guitar, cello, the flat-2 colour
    _mel(sc, VC, _b(5), [[("B3", 0, 3), ("A3", 3, 2)],
                         [("G3", 0, 3), ("F#3", 3, 2)],
                         [("E3", 0, 5)], [("F#3", 0, 3.4)]], 62, expr=88,
         vib=28)
    for k, c in ((5, "F#sus"), (6, "F#m"), (7, "F#o"), (8, "F#o")):
        _comp(sc, _b(k), c, c, 0, 54)
        lo, hi = (44, 68) if k % 2 else (68, 44)
        _sus(sc, TREM, _b(k), TV[c], BAR, 46, lo, hi)
    _vchord(sc, _b(5) + 1.5, [71, 76], 54, ring=3.0)
    _vchord(sc, _b(6) + 1.5, [69, 76], 52, ring=3.0)
    _toll(sc, _b(7), "F#o", 48)
    # the lantern again, quicker — a flicker in the 2-group
    en.sustain(sc, VIB, _b(7) + 3.0, _b(9) - 0.6)
    _mel(sc, VIB, _b(7), _light(False, "flick"), 86, expr=0, gate=1.0, jt=0)


# ---------------------------------------------------------------------------
# II. The Lure — the tune in its false form, twice
# ---------------------------------------------------------------------------

def _b_lure(sc) -> None:
    _head_block(sc, 9, False, TPT, 86, 86, "ride", kit_lift=-4, comp_vel=60,
                piano_vel=58, vib_vel=60, lead_expr=100)
    _head_block(sc, 17, False, TPT, 92, 90, "ride", comp_vel=64,
                counter_vel=88, cello_vel=70, trem_vel=48, piano_vel=62,
                vib_vel=64, lead_expr=106)


# ---------------------------------------------------------------------------
# III. Wreckers — the baritone's bridge over a diatonic circle of fifths
# ---------------------------------------------------------------------------

_BRIDGE = ["Bm", "Em", "A", "D", "G", "C#o", "F#sus", "F#m"]


def _b_wreckers(sc) -> None:
    t0 = M3
    _mel(sc, BARI, t0, [
        [("D4", 0, 1.5), ("F#4", 1.5, 1.5), ("E4", 3, 1), ("D4", 4, 1)],
        [("B3", 0, 3), ("G3", 3, 1), ("B3", 4, 1)],
        [("C#4", 0, 1.5), ("E4", 1.5, 1.5), ("D4", 3, 1), ("C#4", 4, 1)],
        [("A3", 0, 3), ("F#3", 3, 1), ("A3", 4, 1)],
        [("B3", 0, 1.5), ("D4", 1.5, 1.5), ("C#4", 3, 1), ("B3", 4, 1)],
        [("G3", 0, 3), ("E3", 3, 1), ("G3", 4, 1)],
        [("B3", 0, 1.5), ("C#4", 1.5, 1), ("E4", 2.5, .5), ("G4", 3, 2)],
        [("F#4", 0, 3.6)],
    ], 92, vel_end=100, expr=106, vib=40)
    # cello descant: a guide-tone line, consonant on every bar line
    _mel(sc, VC, t0, [[("A4", 0, 5)], [("G4", 0, 5)], [("E4", 0, 5)],
                      [("F#4", 0, 10)], [], [("E4", 0, 10)], [],
                      [("C#4", 0, 4.6)]], 70, expr=94, vib=32)
    _bass_run(sc, 25, [C_BM, C_EM, C_A, C_D, (43, 55, 54, 47, 50), C_CS,
                       C_SUS, C_OST], 88)
    for i, c in enumerate(_BRIDGE):
        t = t0 + i * BAR
        _kit(sc, t, "ride", lift=-2, fill=(i == 7))
        _comp(sc, t, c, c, i % 2, 62)
        if i % 2 == 0:
            _toll(sc, t, c, 58)
        else:
            _shell(sc, t + 3.0, c, 52)
        lo, hi = (50, 74) if i % 2 == 0 else (74, 50)
        _sus(sc, TREM, t, TV[c], BAR, 50, lo, hi)
    _vfill(sc, t0 + 1 * BAR, ["G4", "B4", "D5", "E5"], 1.0, 62)
    _vfill(sc, t0 + 3 * BAR, ["F#4", "A4", "C#5", "D5"], 1.0, 62)
    _vfill(sc, t0 + 5 * BAR, ["E4", "G4", "B4", "C#5"], 1.0, 64)


# ---------------------------------------------------------------------------
# IV. The Watch — a muted-trumpet solo over the strict ostinato
# ---------------------------------------------------------------------------

_SOLO = [
    [("A4", 1.5, .5), ("B4", 2, 1), ("C#5", 3, 2, "v")],
    [("E5", 0, 1.5, "s"), ("D5", 1.5, .5), ("C#5", 2, .5), ("B4", 2.5, .5),
     ("G4", 3, 1.5), ("F#4", 4.5, 2.0, "v")],
    [("G4", 3, .5), ("A4", 3.5, .5), ("B4", 4, .5), ("D5", 4.5, .5)],
    [("C#5", 0, 2.5, "v"), ("E5", 3, .5), ("D5", 3.5, .5), ("B4", 4, 1, "f")],
    [("F#5", 1, .5, "s"), ("E5", 1.5, .5), ("F#5", 2, 1), ("G5", 3, 1.5, "v"),
     ("F#5", 4.5, .5)],
    [("E5", 0, 1), ("D5", 1, .5), ("B4", 1.5, .5), ("A4", 2, 1),
     ("G4", 3, .5), ("A4", 3.5, .5), ("B4", 4, 1)],
    [("D5", 0, 1.5, "s"), ("E5", 1.5, 1.5), ("F#5", 3, 1), ("G5", 4, 1)],
    [("F#5", 0, 3, "vf")],
    [("A5", 0, .5), ("G5", .5, .5), ("F#5", 1, .5), ("E5", 1.5, .5),
     ("D5", 2, .5), ("E5", 2.5, .5), ("F#5", 3, 1), ("A5", 4, 1, "s")],
    [("B5", 0, 2, "v"), ("A5", 2, .5), ("G5", 2.5, .5), ("F#5", 3, .5),
     ("E5", 3.5, .5), ("D5", 4, .5), ("C#5", 4.5, .5)],
    [("B4", 0, 1), ("D5", 1, .5), ("F#5", 1.5, .5), ("A5", 2, 1),
     ("G5", 3, 1.5, "v"), ("F#5", 4.5, .5)],
    [("E5", 0, .5), ("G5", .5, .5), ("F#5", 1, 2, "vf"), ("C#5", 4, .5),
     ("E5", 4.5, .5)],
    [("G5", 0, .5), ("B5", .5, .5), ("D6", 1, 2, "sv"), ("C#6", 3, .5),
     ("B5", 3.5, .5), ("A5", 4, .5), ("G5", 4.5, .5)],
    [("F#5", 0, 1.5), ("G5", 1.5, .5), ("F#5", 2, .5), ("E5", 2.5, .5),
     ("D5", 3, .5), ("B4", 3.5, .5), ("A4", 4, .5), ("G4", 4.5, .5)],
    [("F#4", 0, 2, "v"), ("A4", 2, .5), ("B4", 2.5, .5), ("D5", 3, 1),
     ("C#5", 4, 1)],
    [("G4", 0, 1.5, "s"), ("F#4", 1.5, 2.0, "v")],
]
_VAMP = ["F#m", "F#sus", "G", "F#m"]


def _b_watch(sc) -> None:
    t0 = M4
    _mel(sc, TPT, t0, _SOLO[:8], 88, vel_end=96, expr=102, vib=52)
    _mel(sc, TPT, t0 + 8 * BAR, _SOLO[8:], 100, vel_end=108, expr=114, vib=60)
    _bass_run(sc, 33, [C_OST] * 16, [86] * 8 + [92] * 8, ghosts=(3, 7, 11, 15))
    for i in range(16):
        t = t0 + i * BAR
        c = _VAMP[i % 4]
        late = i >= 8
        _kit(sc, t, "hot" if late else "ride", lift=(i - 8) if late else -2,
             fill=(i in (7, 15)))
        _comp(sc, t, c, c, i % 2, 68 if late else 58)
        if late:
            if i % 2 == 0:
                _toll(sc, t, "F#m", 62)
            _shell(sc, t + 3.0, c, 56)
            _vchord(sc, t + 1.5, VV[c], 58, ring=0.4)
            _vchord(sc, t + 3.0, VV[c], 64, ring=1.6)
            _sus(sc, TREM, t, TV[c], BAR, 50, 50 + 4 * (i - 8), 56 + 4 * (i - 8))
        else:
            if i % 4 == 0:
                _toll(sc, t, "F#m", 54)
            if i % 2 == 1:
                _vchord(sc, t + 3.0, VV[c], 56, ring=1.8)
    _mel(sc, VC, t0 + 8 * BAR, [
        [("C#4", 0, 5)], [("B3", 0, 5)], [("D4", 0, 5)], [("C#4", 0, 5)],
        [("E4", 0, 5)], [("D4", 0, 5)], [("G4", 0, 3), ("F#4", 3, 2)],
        [("G3", 0, 3), ("F#3", 3, 1.9)],
    ], 66, vel_end=78, expr=96, vib=32)


# ---------------------------------------------------------------------------
# V. On the Rocks — the tense tutti; the tritone laid bare; silence
# ---------------------------------------------------------------------------

def _b_rocks(sc) -> None:
    t0 = M5
    stab = [64, 69, 72, 79]               # E A C G over F#: the trap
    # the lantern hammered: trumpet, baritone an octave under, cello with it
    lines = [(0, "slow", 94), (2, "slow", 100), (4, "press", 106),
             (5, "press", 110), (6, "snap", 114)]
    for i, rhythm, v in lines:
        _mel(sc, TPT, t0 + i * BAR, _light(False, rhythm), v, expr=112, jt=2)
    _mel(sc, TPT, t0 + 6 * BAR, [[("G5", 3, 1.9)],
                                 [("G5", 0, 1.3), ("G5", 1.5, 1.3),
                                  ("G5", 3, .9), ("G5", 4, .9)]], 120,
         expr=124, jt=2)
    for i, rhythm, v in lines:
        _mel(sc, BARI, t0 + i * BAR, _light(False, rhythm, octave=3), v - 12,
             expr=118, jt=2)
    _mel(sc, BARI, t0 + 6 * BAR, [[("C4", 3, 1.9)],
                                  [("C4", 0, 1.3), ("C4", 1.5, 1.3),
                                   ("C4", 3, .9), ("C4", 4, .9)]], 110,
         expr=122, jt=2)
    _mel(sc, VC, t0, [[("F#2", 0, 5)], [("C3", 0, 4.8)]], 84, expr=104)
    for i, rhythm, v in lines[1:]:
        _mel(sc, VC, t0 + i * BAR, _light(False, rhythm, octave=3), v - 18,
             expr=112, jt=2)
    _mel(sc, VC, t0 + 6 * BAR, [[("A3", 3, 1.9)],
                                [("A3", 0, 1.3), ("A3", 1.5, 1.3),
                                 ("A3", 3, .9), ("A3", 4, .9)]], 100,
         expr=118, jt=2)
    # a second lantern answers in canon (vibes, the whole-step form)
    _vchord(sc, t0 + BAR + 3.0, VV["F#o"], 84, ring=0.8)
    _vchord(sc, t0 + BAR + 4.0, VV["F#o"], 84, ring=0.8)
    _mel(sc, VIB, t0 + 2 * BAR, _light(False, "canon", s=2), 92, expr=0,
         gate=1.0, jt=0)
    _vchord(sc, t0 + 3 * BAR + 3.0, VV["F#o"], 88, ring=0.8)
    _vchord(sc, t0 + 3 * BAR + 4.0, VV["F#o"], 88, ring=0.8)
    for i in (4, 5, 6):
        _vchord(sc, t0 + i * BAR + 3.0, stab, 86 + 2 * i, ring=1.8)
    for on in (0.0, 1.5, 3.0, 4.0):
        _vchord(sc, t0 + 7 * BAR + on, stab, 98, ring=0.9)
    _bass_run(sc, 49, [C_FALSE] * 4 + [C_HAMMER] * 4,
              [90, 92, 96, 100, 104, 108, 110, 112])
    for i in range(8):
        t = t0 + i * BAR
        v = 64 + 4 * i
        if i < 4:
            _comp(sc, t, "F#o", "F#o", 0 if i < 2 else 1, v)
            _toll(sc, t, "F#o", v, dur=2.8)
            _shell(sc, t + 3.0, "F#o", v - 4, dur=1.7)
            _sus(sc, TREM, t, TV["F#o"], BAR, 66 + 2 * i, 70 + 8 * i,
                 84 + 8 * i)
            _kit(sc, t, "tutti", lift=-20 + 3 * i, crash=(i == 0))
        else:
            _comp(sc, t, "F#o", "F#o", 2, v - 6)
            _toll(sc, t, "F#o", v - 8, dur=1.3)
            _shell(sc, t + 1.5, "F#o", v - 14, dur=0.5)
            sc.note(PNO, 36, t + 3.0, 1.8, v - 8, jt=2)   # C in the bass:
            sc.note(PNO, 48, t + 3.0, 0.9, v - 12, jt=2)  # the tritone below
            _shell(sc, t + 4.0, "F#o", v - 14, dur=0.8)
            _sus(sc, TREM, t, stab, BAR, 70 + 2 * i, 90 + 4 * (i - 4), 116)
            if i < 7:
                _kit(sc, t, "tutti", lift=2 * i - 18, crash=(i == 4))
    # bar 56: the kit breaks into the hammer rhythm, toms falling
    t = t0 + 7 * BAR
    for key, on, v in ((36, 0, 96), (40, 0, 92), (49, 0, 84), (36, 1.5, 92),
                       (40, 1.5, 90), (38, 1.0, 56), (38, 2.0, 60),
                       (38, 2.5, 66), (36, 3, 98), (50, 3, 88), (48, 3.5, 90),
                       (36, 4, 96), (47, 4, 94), (45, 4.5, 98), (41, 4.75, 100)):
        sc.hit(key, t + on, v)
    # bar 57: F# ... then everyone on C natural.  The false fifth, naked.
    t = T_SLAM
    for ch, p0, p1, v in ((BASS, 42, 48, 118), (TPT, 78, 72, 122),
                          (BARI, 54, 60, 114), (VC, 42, 48, 108)):
        sc.note(ch, p0, t, 1.3, v, jt=0, jv=0)
        sc.note(ch, p1, t + 3.0, 2.2, v, jt=0, jv=0)
    sc.cc(TPT, 11, 127, t)
    sc.cc(BARI, 11, 124, t)
    sc.cc(VC, 11, 122, t)
    for p in (30, 42, 48, 52, 57):
        sc.note(PNO, p, t, 2.9, 112, jt=0, jv=2)       # rings into the C
    for p in (24, 36, 48):
        sc.note(PNO, p, t + 3.0, 2.2, 116, jt=0, jv=2)
    en.strum(sc, GTR, GV["F#o"], t, 1.3, 104, spread=0.012)
    for p in (48, 60):
        sc.note(GTR, p, t + 3.0, 2.2, 108, jt=0, jv=2)
    _vchord(sc, t, [66, 72, 76, 79], 110, ring=2.9)
    _vchord(sc, t + 3.0, [72, 84], 112, ring=2.2)
    _sus(sc, TREM, t, stab, 1.36, 92, 127, 127)
    _sus(sc, TREM, t + 3.0, [60, 72], 2.26, 94, 127, 100)
    for on in (0.0, 3.0):
        for key, v in ((36, 104), (40, 100), (49, 96), (57, 92)):
            sc.hit(key, t + on, v, jt=0)


# ---------------------------------------------------------------------------
# VI. The True Light — the BEAM alone; the tune with its fifth restored
# ---------------------------------------------------------------------------

def _b_true_light(sc) -> None:
    t = T_TRUE
    # the mute comes off: F# C# D C# F#, alone, tick-exact
    for (p, on, du), v in zip([(66, 0, 1.5), (73, 1.5, 1.5), (74, 3, 1),
                               (73, 4, 1), (78, 5, 4.7)],
                              (104, 108, 110, 108, 116)):
        sc.note(OPEN, p, t + on, du * 0.97, v, jt=0, jv=0)
    en.expr_curve(sc, OPEN, [(t, 108), (t + 5.0, 114), (t + 7.5, 127),
                             (t + 9.6, 110)], step=0.25)
    en.cc_curve(sc, OPEN, 1, [(t + 6.0, 0), (t + 8.0, 56), (t + 9.5, 56)],
                step=0.25)
    sc.cc(OPEN, 1, 0, t + 9.6)
    # bar 60: the night comes back in tune — an open fifth, the bass's lean
    en.sustain(sc, VIB, t + 5.0, t + 9.5)
    for i, p in enumerate((54, 61, 66, 73)):
        sc.note(VIB, p, t + 5.0 + 0.25 * i, 3.6, 62 + 3 * i, jt=0, jv=2)
    _sus(sc, TREM, t + 5.0, [54, 61], BAR, 50, 30, 86)
    sc.note(BASS, 45, t + 8.0, 0.94, 86, jt=0, jv=2)
    sc.note(BASS, 43, t + 9.0, 0.9, 82, jt=3, jv=2)
    for i, on in enumerate((8.0, 8.5, 9.0, 9.5)):
        sc.hit(51, t + on, 34 + 8 * i)
    sc.hit(36, t + 8.0, 44)
    # the tune made true
    _head_block(sc, 61, True, OPEN, 106, 96, "hot", kit_lift=4, comp_vel=74,
                counter_vel=90, cello_vel=80, trem_vel=68, piano_vel=72,
                vib_vel=72, crash=True, lead_expr=110)
    _head_block(sc, 69, True, OPEN, 118, 104, "hot", kit_lift=14, comp_vel=88,
                counter_vel=102, cello_vel=98, cello_double=True, trem_vel=84,
                trem_up=12, piano_vel=90, hammer=True, vib_vel=96,
                vib_double=True, crash=True, lead_expr=120, harmony_vel=98)
    # codetta: the bridge's circle, coming down
    t0 = _b(77)
    _mel(sc, OPEN, t0, [
        [("F#5", 0, 2), ("E5", 2, 1), ("D5", 3, 2)],
        [("E5", 0, 2), ("D5", 2, 1), ("B4", 3, 2)],
        [("C#5", 0, 2), ("B4", 2, 1), ("A4", 3, 2)],
        [("D5", 0, 3), ("C#5", 3, 1), ("A4", 4, 1)],
        [("B4", 0, 3), ("A4", 3, 1), ("G4", 4, 1)],
        [("F#4", 0, 4.6)],
    ], 104, vel_end=78, expr=108, vib=46)
    _mel(sc, BARI, t0, [
        [("D4", 0, 3), ("B3", 3, 2)], [("G3", 0, 3), ("E3", 3, 2)],
        [("E3", 0, 3), ("C#3", 3, 2)], [("F#3", 0, 3), ("A3", 3, 2)],
        [("D3", 0, 3), ("E3", 3, 2)],
        [("B2", 0, 1.5), ("C#3", 1.5, .5), ("E3", 2, 1), ("G3", 3, 1.5),
         ("F#3", 4.5, .5)],
    ], 88, vel_end=68, expr=98, vib=30)
    _mel(sc, VC, t0, [[("A3", 0, 5)], [("B3", 0, 5)], [("A3", 0, 5)],
                      [("F#3", 0, 5)], [("G3", 0, 5)], [("E3", 0, 4.6)]],
         76, vel_end=60, expr=94, vib=30)
    cod = ["Bm", "Em", "A", "D", "G", "F#sus"]
    _bass_run(sc, 77, [C_BM, C_EM, C_A, C_D, C_G, C_SUS],
              [96, 92, 88, 84, 80, 76])
    for i, c in enumerate(cod):
        tb = t0 + i * BAR
        _kit(sc, tb, "hot" if i < 2 else "ride", lift=4 - 3 * i,
             crash=(i == 0))
        _comp(sc, tb, c, c, i % 2, 72 - 4 * i)
        _toll(sc, tb, c, 72 - 5 * i)
        _sus(sc, TREM, tb, TV[c], BAR, 60 - 3 * i, 84 - 7 * i, 76 - 7 * i)
    _vfill(sc, t0 + 3 * BAR, ["F#4", "A4", "C#5", "D5"], 3.0, 64)
    _vfill(sc, t0 + 5 * BAR, ["B4", "E5", "G5"], 3.5, 56)


# ---------------------------------------------------------------------------
# VII. Dark Water — the lantern is still there; no cadence
# ---------------------------------------------------------------------------

def _b_dark_water(sc) -> None:
    # the false tune again, half of it, pp; the baritone finishes it
    _mel(sc, TPT, _b(83), _head(False)[:4], 78, expr=100, vib=30)
    _mel(sc, BARI, _b(87), _head(False)[4:], 80, expr=100, vib=26, shift=-12)
    _mel(sc, VC, _b(87), [[("D4", 0, 5)], [("E4", 0, 5)], [("D4", 0, 5)],
                          [("C#4", 0, 4.6)]], 56, expr=84, vib=24)
    _bass_run(sc, 83, [C_FALSE, (42, 54, 52, 47, 45), C_G, C_OST, C_BM,
                       (40, 52, 50, 45, 47), C_G, C_SUS, C_OST, C_OST,
                       C_FALSE, C_FALSE],
              [78, 78, 76, 76, 74, 74, 72, 72, 70, 70, 68, 68])
    chords = [("F#o", "F#o"), ("F#o", "G"), ("G", "G"), ("F#m", "F#m"),
              ("Bm", "Bm"), ("Em", "A"), ("G", "G"), ("F#sus", "F#sus"),
              ("G", "G"), ("F#m", "F#m"), ("F#o", "F#o"), ("F#o", "F#o")]
    for i, (c1, c2) in enumerate(chords):
        t = _b(83 + i)
        _kit(sc, t, "brush", lift=-(i // 2) - (4 if i >= 8 else 0))
        if i < 10:
            _comp(sc, t, c1, c2, 0, 50 - i)
        lo, hi = (40, 60) if i % 2 == 0 else (60, 40)
        _sus(sc, TREM, t, TV[c1], BAR, 42, lo, hi)
    _toll(sc, _b(83), "F#o", 50)
    _toll(sc, _b(87), "Bm", 46)
    _toll(sc, _b(91), "G", 44)
    _vfill(sc, _b(90), ["B4", "E5", "G5"], 3.5, 50)
    _mel(sc, VC, _b(91), [[("G3", 0, 3), ("F#3", 3, 2)], [("E3", 0, 4.6)]],
         54, expr=82, vib=24)
    # the lantern flickers (bars 93-94)
    en.sustain(sc, VIB, _b(93) + 3.0, _b(95) - 0.6)
    _mel(sc, VIB, _b(93), _light(False, "flick"), 62, expr=0, gate=1.0, jt=0)
    # bars 95-96: the BEAM, far off, in the bass
    t = _b(95)
    for (p, on, du), v in zip([(42, 0, 1.4), (49, 1.5, 1.4), (50, 3, .95),
                               (49, 4, .95), (54, 5, 2.8)],
                              (104, 100, 102, 98, 104)):
        sc.note(BASS, p, t + on, du, v, jt=0, jv=2)
    sc.note(BASS, 45, t + 8.0, 0.94, 70, jt=0, jv=2)
    sc.note(BASS, 43, t + 9.0, 0.9, 66, jt=3, jv=2)
    _sus(sc, TREM, t, [54, 61], 2 * BAR, 40, 36, 58)
    _vchord(sc, t + 8.0, [61, 66], 48, ring=1.9)
    # bars 97-100: ostinato; the trumpet's last sigh; the BEAM in the cello
    _bass_run(sc, 97, [C_OST] * 4, [58, 57, 56, 54])
    for k in range(95, 101):
        _kit(sc, _b(k), "pulse", lift=-(k - 95))
    _mel(sc, TPT, _b(97), [[("G4", 0, 3), ("F#4", 3, 4.6)]], 58, expr=80,
         vib=34)
    _sus(sc, TREM, _b(97), TV["F#m"], 2 * BAR, 38, 54, 36)
    en.strum(sc, GTR, GV["F#sus"], _b(98) + 3.0, 1.6, 42, spread=0.03)
    for (p, on, du), v in zip([(54, 0, 1.5), (61, 1.5, 1.5), (62, 3, 1),
                               (61, 4, 1), (66, 5, 4.8)],
                              (70, 68, 70, 66, 68)):
        sc.note(VC, p, _b(99) + on, du * 0.97, v, jt=0, jv=2)
    en.expr_curve(sc, VC, [(_b(99), 108), (_b(100), 116), (_b(101) - 0.2, 50)],
                  step=0.5)
    _sus(sc, TREM, _b(99), [59, 62, 66], 2 * BAR, 36, 40, 52)
    _vchord(sc, _b(100) + 3.0, [71, 74], 46, ring=1.9)
    # bars 101-102: the false light, last showing, as it first appeared
    en.sustain(sc, VIB, _b(101), _b(103) - 0.6)
    _mel(sc, VIB, _b(101), _light(False, "slow"), 68, expr=0, gate=1.0, jt=0)
    _bass_run(sc, 101, [C_FALSE, C_OST], [56, 52])
    _sus(sc, TREM, _b(101), [54, 64], 2 * BAR, 34, 46, 40)
    # bars 103-104: the flat-2 leans ... and nothing answers
    t = _b(103)
    sc.note(BASS, 31, t, END - t, 60, jt=0, jv=0)
    sc.note(PNO, 43, t, END - t - 0.5, 40, jt=0, jv=2)
    sc.note(PNO, 50, t, END - t - 0.5, 36, jt=0, jv=2)
    for p in (59, 66, 73):
        sc.note(TREM, p, t, END - t, 38, jt=0, jv=2)
    en.expr_curve(sc, TREM, [(t, 44), (t + 4.0, 60), (END - 0.5, 14)],
                  step=0.5)
    en.sustain(sc, VIB, t + 1.0, END - 0.25)
    for i, p in enumerate((62, 66, 71, 73)):
        sc.note(VIB, p, t + 1.0 + i, 3.0, 50 - 3 * i, jt=3, jv=2)
    sc.note(VIB, 78, t + 6.5, END - (t + 6.5), 40, jt=3, jv=2)


BUILDERS = [_b_no_moon, _b_lure, _b_wreckers, _b_watch, _b_rocks,
            _b_true_light, _b_dark_water]

# ---------------------------------------------------------------------------
# Oracles (written before the music)
# ---------------------------------------------------------------------------

PITCHED = [BASS, TPT, BARI, VIB, GTR, VC, PNO, TREM, OPEN]
PHRYGIAN_PCS = {(6 + s) % 12 for s in en.MODES["phrygian"]}
MOVES = [(name, t0, t1) for name, t0, t1 in PART.MOVEMENTS]


def false_statements(sc, ch) -> list:
    """Start beats of every FALSE light on ch: the BEAM detector's shape
    with both fifth-leaps flattened (+6, +s, -s, +6; s in {1, 2})."""
    out = []
    for run in material._single_line(sc, ch):
        for i in range(len(run) - 4):
            p = [pitch for _b0, pitch in run[i:i + 5]]
            step = p[2] - p[1]
            if (p[1] - p[0] == 6 and step in (1, 2)
                    and p[3] - p[2] == -step and p[4] - p[3] == 6):
                out.append(run[i][0])
    return out


def _o_false_first(sc) -> list:
    fails = []
    falses = sorted((b, ch) for ch in PITCHED
                    for b in false_statements(sc, ch))
    trues = sorted((b, ch) for ch in PITCHED
                   for b in material.beam_statements(sc, ch))
    if not trues:
        return ["no true BEAM anywhere"]
    first_true = trues[0][0]
    before = [(b, ch) for b, ch in falses if b < first_true]
    if len(before) < 2:
        fails.append(f"only {len(before)} false light(s) before the true "
                     f"BEAM at {first_true:.1f}; need >= 2")
    if len({ch for _b0, ch in before}) < 2:
        fails.append("the false light must be shown by >= 2 voices before "
                     "the true BEAM")
    if not any(b < M2 - 1.0 for b, _ch in before):
        fails.append("no false light in movement I (it must come FIRST)")
    early = [(b, ch) for b, ch in trues if b < T_TRUE - 0.05]
    if early:
        fails.append(f"true BEAM sounds before it is due: {early[:3]}")
    if not any(b > first_true for b, _ch in falses):
        fails.append("no false light after the true one (the fade must "
                     "leave the lantern burning)")
    return fails


def _o_cuts_through(sc) -> list:
    fails = []
    trues = sorted((b, ch) for ch in PITCHED
                   for b in material.beam_statements(sc, ch))
    if not trues or trues[0][1] != OPEN or abs(trues[0][0] - T_TRUE) > 0.02:
        fails.append(f"first true BEAM must be the open trumpet at beat "
                     f"{T_TRUE}; got {trues[:1]}")
    if any(b < T_TRUE - 0.05 for b, _p, _v in material.note_ons(sc, OPEN)):
        fails.append("the open trumpet sounds before the true light")
    others = sorted(material.active_channels(sc, T_TRUE - 0.05, T_TRUE + BAR)
                    - {OPEN})
    if others:
        fails.append(f"the true BEAM is not alone: channels {others} play "
                     f"in its first bar")
    for ch in sorted(sc.events):
        for on, off, p, _v in material.note_spans(sc, ch):
            if on < T_TRUE - 0.05 and off > T_TRUE - 2.5:
                fails.append(f"ch{ch} pitch {p} still sounds at "
                             f"{off:.2f}: need 2.5 beats of dark before "
                             f"the true light")
                break
    slam = [p % 12 for ch in PITCHED
            for b, p, _v in material.note_ons(sc, ch)
            if abs(b - (T_SLAM + 3.0)) < 0.05]
    if len(slam) < 8 or set(slam) != {0}:
        fails.append(f"the last sound before the dark must be a tutti C "
                     f"natural; got pcs {sorted(set(slam))} x{len(slam)}")
    return fails


def _o_quarantine(sc) -> list:
    fails = []
    seen = [0] * len(FALSE_WINDOWS)
    for ch in PITCHED:
        for b, p, _v in material.note_ons(sc, ch):
            pc = p % 12
            if pc == 0:
                hit = [i for i, (lo, hi) in enumerate(FALSE_WINDOWS)
                       if lo - 0.05 <= b < hi]
                if not hit:
                    fails.append(f"ch{ch} C natural at beat {b:.2f} outside "
                                 f"every false-light window")
                else:
                    seen[hit[0]] += 1
            elif pc not in PHRYGIAN_PCS:
                fails.append(f"ch{ch} pitch {p} at beat {b:.2f} is outside "
                             f"F# phrygian")
    for (lo, hi), count in zip(FALSE_WINDOWS, seen):
        if count == 0:
            fails.append(f"false-light window {lo:.0f}..{hi:.0f} has no C "
                         f"natural")
    return fails[:8]


def _o_three_plus_two(sc) -> list:
    fails = []
    ons = material.note_ons(sc, BASS)
    ticks = {round(b * en.PPQ) for b, _p, _v in ons}
    good = sum(1 for k in range(1, N_BARS + 1)
               if round(_b(k) * en.PPQ) in ticks
               and round((_b(k) + 3.0) * en.PPQ) in ticks)
    if good < 98:
        fails.append(f"bass marks beats 1 and 4 (the 3+2) tick-exactly in "
                     f"only {good}/{N_BARS} bars; need >= 98")
    strong = [v for b, _p, v in ons if (b % BAR) in (0.0, 3.0)]
    weak = [v for b, _p, v in ons if (b % BAR) not in (0.0, 3.0)]
    if not strong or not weak or \
            sum(strong) / len(strong) - sum(weak) / len(weak) < 8:
        fails.append("bass accents on 1 and 4 are not >= 8 velocity above "
                     "the rest")
    two_three = sum(1 for b, _p, _v in ons if abs((b % BAR) - 2.5) < 0.05)
    if two_three > 8:
        fails.append(f"{two_three} bass onsets on beat 3.5: the bar must "
                     f"not read 2.5+2.5")
    kicks = [b % BAR for b, p, _v in material.note_ons(sc, KIT) if p == 36]
    on_grid = sum(1 for x in kicks
                  if min(abs(x - 0.0), abs(x - 3.0), abs(x - BAR)) < 0.03)
    if not kicks or on_grid / len(kicks) < 0.75:
        fails.append(f"kick on the 3+2 pillars only {on_grid}/{len(kicks)}")
    return fails


def _o_flat_two(sc) -> list:
    fails = []
    ons = material.note_ons(sc, BASS)
    leans = [b0 for (b0, p0, _v0), (b1, p1, _v1) in zip(ons, ons[1:])
             if p0 % 12 == 7 and p1 == p0 - 1
             and abs(b1 % BAR) < 0.02]
    for name, t0, t1 in MOVES:
        count = sum(1 for b in leans if t0 <= b < t1)
        if count < 3:
            fails.append(f"'{name}': the bass G leans on F# across only "
                         f"{count} bar line(s); need >= 3")
    if len(leans) < 50:
        fails.append(f"only {len(leans)} G->F# bar-line leans; need >= 50")
    sung = 0
    for ch in (TPT, OPEN):
        seq = material.note_ons(sc, ch)
        sung += sum(1 for (_a, p0, _c), (_d, p1, _e) in zip(seq, seq[1:])
                    if p0 % 12 == 7 and p1 == p0 - 1)
    if sung < 8:
        fails.append(f"the trumpets sing G->F# only {sung} times; need >= 8")
    return fails


def _o_counterpoint(sc) -> list:
    fails = []
    pairs = [(17, 8, TPT, BARI), (61, 8, OPEN, BARI), (69, 8, OPEN, BARI),
             (77, 6, OPEN, BARI), (25, 8, BARI, VC), (87, 4, BARI, VC)]
    for k0, count, lead, other in pairs:
        for k in range(k0, k0 + count):
            beat = _b(k) + 0.02
            a = material.sounding(sc, lead, beat)
            c = material.sounding(sc, other, beat)
            if not a or not c:
                fails.append(f"bar {k}: ch{lead}/ch{other} not both "
                             f"sounding on the downbeat")
            elif abs(a[0] - c[0]) % 12 not in material.CONSONANT:
                fails.append(f"bar {k}: ch{lead} {a[0]} against ch{other} "
                             f"{c[0]} is dissonant on the downbeat")
    return fails[:8]


def _o_solo(sc) -> list:
    fails = []
    ons = material.note_ons(sc, BASS)
    for k in range(33, 49):
        got = {round((b - _b(k)) * 4) / 4: p for b, p, _v in ons
               if _b(k) - 0.02 <= b < _b(k + 1) - 0.02}
        want = dict(zip(_ONS, C_OST))
        if any(got.get(on) != p for on, p in want.items()):
            fails.append(f"bar {k}: the bass leaves the ostinato "
                         f"({sorted(got.items())})")
    solo = [(b, p) for b, p, _v in material.note_ons(sc, TPT)
            if M4 <= b < M5]
    bars = {int(b // BAR) for b, _p in solo}
    if len(solo) < 60 or len(bars) < 14:
        fails.append(f"solo has {len(solo)} notes in {len(bars)} bars; "
                     f"need >= 60 in >= 14")
    if solo:
        pitches = [p for _b0, p in solo]
        if max(pitches) - min(pitches) < 17:
            fails.append("solo spans less than an octave and a fourth")
        top = max(solo, key=lambda x: x[1])[0]
        if top < M4 + 8 * BAR:
            fails.append("the solo's highest note must come in its second "
                         "half")
    for ch in (BARI, OPEN):
        if any(M4 <= b < M5 for b, _p, _v in material.note_ons(sc, ch)):
            fails.append(f"ch{ch} must be tacet under the solo")
    return fails[:8]


def _o_arc(sc) -> list:
    fails = []
    e = material.energy
    intro, head = e(sc, M1, M2), e(sc, M2, M3)
    solo = e(sc, M4, M4 + 8 * BAR)
    tutti, peak = e(sc, *TUTTI), e(sc, *PEAK)
    first_true = e(sc, _b(61), _b(69))
    lone = e(sc, T_TRUE, T_TRUE + BAR)
    fade = e(sc, _b(97), END)
    checks = [
        (intro < 0.6 * head, f"intro {intro:.0f} not < 0.6 x head {head:.0f}"),
        (tutti > 1.25 * head, f"tutti {tutti:.0f} not > 1.25 x head {head:.0f}"),
        (solo < 0.8 * tutti, f"solo opening {solo:.0f} not < 0.8 x tutti {tutti:.0f}"),
        (lone < 0.2 * tutti, f"lone BEAM {lone:.0f} not < 0.2 x tutti {tutti:.0f}"),
        (peak > first_true, f"second true statement {peak:.0f} not > first {first_true:.0f}"),
        (peak >= tutti, f"true-light peak {peak:.0f} below the tutti {tutti:.0f}"),
        (fade < 0.3 * peak, f"fade {fade:.0f} not < 0.3 x peak {peak:.0f}"),
    ]
    for ok, msg in checks:
        if not ok:
            fails.append(msg)
    loud = max((v for ch in sc.events
                for b, _p, v in material.note_ons(sc, ch) if b >= _b(97)),
               default=0)
    if loud > 72:
        fails.append(f"a velocity of {loud} in the last eight bars (cap 72)")
    return fails


def _o_unresolved(sc) -> list:
    fails = []
    ons = material.note_ons(sc, BASS)
    spans = material.note_spans(sc, BASS)
    if not ons or ons[-1][1] % 12 != 7:
        fails.append("the last bass note must be G (the flat-2), unresolved")
    elif max(off for _on, off, _p, _v in spans) < END - 0.5:
        fails.append("the last bass G must hold to the end")
    sounding = [(p, ch) for ch in PITCHED
                for p in material.sounding(sc, ch, END - 1.0)]
    if not sounding:
        fails.append("nothing sounds in the last beat")
    else:
        if min(sounding)[0] % 12 != 7:
            fails.append(f"lowest final pitch {min(sounding)[0]} is not G")
        pcs = {p % 12 for p, _ch in sounding}
        if 6 not in pcs:
            fails.append("the tonic F# must hang over the final G")
        if len(pcs) < 4:
            fails.append(f"final sonority too thin: pcs {sorted(pcs)}")
    return fails


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("false_lights_come_first", _o_false_first(sc)))
    results.append(("true_light_cuts_through", _o_cuts_through(sc)))
    results.append(("tritone_quarantine", _o_quarantine(sc)))
    results.append(("five_four_three_plus_two", _o_three_plus_two(sc)))
    results.append(("flat_two_leans_on_tonic", _o_flat_two(sc)))
    results.append(("counter_melody_consonant", _o_counterpoint(sc)))
    results.append(("solo_over_ostinato", _o_solo(sc)))
    results.append(("dynamic_arc", _o_arc(sc)))
    results.append(("unresolved_fade", _o_unresolved(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def lvl(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    peak, tutti = lvl(*PEAK), lvl(*TUTTI)
    hush = lvl(_b(97), _b(103))
    dark = lvl(T_TRUE - 2.0, T_TRUE - 0.1)
    lone = lvl(T_TRUE + 0.2, T_TRUE + BAR)
    intro = lvl(_b(1), _b(3))
    out = []
    f = []
    if peak - hush < 6.0:
        f.append(f"peak {peak:.1f} dB vs fade {hush:.1f} dB: < 6 dB apart")
    if peak - intro < 6.0:
        f.append(f"peak {peak:.1f} dB vs bare ostinato {intro:.1f} dB: "
                 f"< 6 dB apart")
    out.append(("peak_vs_hush", f))
    f = []
    if peak < tutti:
        f.append(f"true-light peak {peak:.1f} dB below the tutti "
                 f"{tutti:.1f} dB")
    out.append(("second_peak_not_smaller", f))
    f = []
    if tutti - dark < 15.0:
        f.append(f"the dark before the true light is only "
                 f"{tutti - dark:.1f} dB under the tutti")
    if lone - dark < 8.0:
        f.append(f"the lone BEAM {lone:.1f} dB is not >= 8 dB above the "
                 f"dark {dark:.1f} dB")
    if peak - lone < 3.0:
        f.append(f"the lone BEAM {lone:.1f} dB is not >= 3 dB under the "
                 f"peak {peak:.1f} dB")
    out.append(("dark_then_one_trumpet", f))
    return out
