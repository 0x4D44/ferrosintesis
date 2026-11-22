"""t02_northeaster.py - track 2 of *Lantern Year*: "Northeaster".

February.  A gale comes down on the light out of the north-east: prog rock in
E aeolian at quarter = 150, the verses lurching in 7/8 (2+2+3) and the
choruses squaring up to it in 4/4.

The headline claims (each pinned by an oracle below):

  * the BEAM *is* the 7/8 riff - bass and distortion guitar in octaves, the
    five beam notes on the first five eighths of every "A" riff bar, the
    riff transposed diatonically with the harmony;
  * 7/8 verses (kick-kick-snare on eighths 0/2/4, no backbeat) against 4/4
    choruses (snare on 2 and 4);
  * two storm peaks, the second verifiably bigger (score energy, voices);
  * between them the eye of the storm - twelve bars of surf, one toll of the
    LAMP and a phrase of the keeper's HYMN on a far-off organ;
  * an organ solo and a guitar solo with real (ramped) string bends;
  * a second line in counterpoint to the chorus tune, consonant with it and
    with the bass on every bar line;
  * E aeolian throughout; a slammed unison E to finish.
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 2
TITLE = "Northeaster"
FILE = "02 - Northeaster.mid"
SEED = 20261202
COMMENT = ("Lantern Year, track 2: Northeaster. A February gale at the "
           "light - prog rock in E aeolian, 7/8 verses (2+2+3) against 4/4 "
           "choruses. The album's BEAM cell is the 7/8 riff; two storm "
           "peaks frame the eye of the storm, where the lamp tolls once and "
           "a far organ remembers the keeper's hymn. Organ solo, guitar "
           "solo, slammed unison.")

MODE = "aeolian"
E8 = 0.5                     # an eighth note, in beats
BAR7 = 3.5                   # a 7/8 bar
BAR4 = 4.0                   # a 4/4 bar
ACCENTS7 = (0, 2, 4)         # the 2+2+3 grouping, in eighths
SCALE_PCS = {(4 + s) % 12 for s in en.MODES[MODE]}

LEAD, RHY, BASS, ORG, SOLO, BRASS, TIMP, SEA, REV, DR, LAMP, RHY2 = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
E1, E2, E3, E4 = 28, 40, 52, 64

K, SN, STICK, HH, OH, CR, RD, T1, T2, FT = 36, 38, 37, 42, 46, 49, 51, 50, 47, 41

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

_GRID = [                                   # (name, bars, meter)
    ("I. Landfall", 16, 7),
    ("II. Verse - The Glass Falls", 16, 7),
    ("III. Chorus - Hold the Light", 16, 4),
    ("IV. Verse - Green Water", 16, 7),
    ("V. Chorus - The First Peak", 16, 4),
    ("VI. Organ Solo - Spindrift", 24, 7),
    ("VII. The Eye of the Storm", 16, 4),
    ("VIII. Guitar Solo - The Back Wall", 24, 7),
    ("IX. Verse - All Hands", 16, 7),
    ("X. Chorus - The Second Peak", 24, 4),
    ("XI. Coda - Slammed Unison", 20, 7),
]
MOVES: list[tuple[str, float, float, int, int]] = []
_t = 0.0
for _name, _bars, _meter in _GRID:
    _len = _bars * (BAR7 if _meter == 7 else BAR4)
    MOVES.append((_name, _t, _t + _len, _meter, _bars))
    _t += _len
END = _t                                     # 750 beats = 300 s
(T_INTRO, T_V1, T_C1, T_V2, T_C2, T_OSOLO, T_EYE, T_GSOLO, T_V3, T_C3,
 T_CODA) = [m[1] for m in MOVES]
(I_INTRO, I_V1, I_C1, I_V2, I_C2, I_OSOLO, I_EYE, I_GSOLO, I_V3, I_C3,
 I_CODA) = range(11)
VERSE_IDX = (I_V1, I_V2, I_V3)
CHORUS_IDX = (I_C1, I_C2, I_C3)
EYE_CORE = (T_EYE, T_EYE + 12 * BAR4)        # twelve bars of almost nothing

_SIGS: list[tuple[float, int, int]] = []
for _name, _a, _b, _meter, _bars in MOVES:
    _sig = (7, 8) if _meter == 7 else (4, 4)
    if not _SIGS or _SIGS[-1][1:] != _sig:
        _SIGS.append((_a, _sig[0], _sig[1]))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[(m[0], m[1], m[2]) for m in MOVES],
    tempo_map=[(0.0, 150.0)],
    time_signatures=_SIGS,
    keysigs=[(0.0, 1, 1)],
    channels=[
        (LEAD, "Lead guitar (overdrive)", 29, 124, 64, 42),
        (RHY, "Rhythm guitar (distortion)", 30, 86, 42, 28),
        (BASS, "Picked bass", 34, 106, 64, 18),
        (ORG, "Rock organ", 18, 74, 86, 40),
        (SOLO, "Solo organ", 16, 114, 76, 46),
        (BRASS, "Brass section", 61, 90, 48, 44),
        (TIMP, "Timpani", 47, 92, 56, 50),
        (SEA, "Seashore", 122, 58, 64, 60),
        (REV, "Reverse cymbal", 119, 84, 72, 50),
        (DR, "Drum kit", 0, 108, 64, 26),
        (LAMP, "The lamp (tubular bell)", material.LAMP_PROGRAM, 92, 64, 70),
        (RHY2, "Rhythm guitar II", 30, 80, 90, 30),
    ],
    bank_selects=[(LEAD, 1)],
)

# ---------------------------------------------------------------------------
# The material (module-level data, so every oracle reads what the music read)
# ---------------------------------------------------------------------------

# The riff, as diatonic offsets from the chord root, seven eighths (2+2+3).
# RIFF_A opens with the BEAM (1-5-6-5-8); RIFF_B walks back down to answer it.
RIFF_A = [0, 4, 5, 4, 7, 6, 4]
RIFF_B = [7, 6, 4, 3, 2, 3, 4]
RIFF = {"A": RIFF_A, "B": RIFF_B}

VERSE_CH = [1, 1, 6, 7, 1, 1, 3, 7, 4, 4, 6, 6, 7, 7, 5, 5]
VERSE_KIND = "ABAAABAAABABABAB"

# The verse tune: per 7/8 bar, (degree, start, dur) in EIGHTHS, base E4.
VERSE_TUNE = [
    [(5, 0, 2), (8, 2, 2), (7, 4, 3)],
    [(5, 0, 2), (3, 2, 2), (4, 4, 1), (5, 5, 2)],
    [(6, 0, 2), (8, 2, 2), (10, 4, 3)],
    [(9, 0, 2), (7, 2, 2), (4, 4, 3)],
    [(5, 0, 2), (8, 2, 2), (7, 4, 3)],
    [(8, 0, 2), (10, 2, 2), (9, 4, 1), (8, 5, 2)],
    [(7, 0, 2), (5, 2, 2), (3, 4, 3)],
    [(4, 0, 4), (7, 4, 3)],
    [(4, 0, 2), (6, 2, 2), (8, 4, 3)],
    [(8, 0, 1), (7, 1, 1), (6, 2, 2), (4, 4, 3)],
    [(3, 0, 2), (6, 2, 2), (8, 4, 3)],
    [(10, 0, 2), (8, 2, 2), (6, 4, 3)],
    [(7, 0, 2), (9, 2, 2), (11, 4, 3)],
    [(11, 0, 2), (10, 2, 2), (9, 4, 3)],
    [(9, 0, 2), (7, 2, 2), (5, 4, 3)],
    [(5, 0, 1), (7, 1, 1), (8, 2, 1), (10, 3, 1), (9, 4, 1), (8, 5, 1),
     (7, 6, 1)],
]

# The chorus: chord per 4/4 bar (a tuple splits the bar), and the tune as
# (degree, start, dur) in BEATS, base E4.
CHORUS_CH = [6, 7, 1, 1, 6, 7, 3, 5, 6, 7, 1, 3, 4, 5, (6, 7), 1]
CHORUS_TUNE = [
    [(8, 0, 3), (10, 3, 1)],
    [(9, 0, 2), (7, 2, 1), (9, 3, 1)],
    [(10, 0, 3), (9, 3, 0.5), (10, 3.5, 0.5)],
    [(8, 0, 2), (5, 2, 1), (8, 3, 1)],
    [(8, 0, 3), (10, 3, 1)],
    [(11, 0, 2), (9, 2, 1), (7, 3, 1)],
    [(12, 0, 3), (11, 3, 1)],
    [(9, 0, 4)],
    [(6, 0, 1), (8, 1, 1), (10, 2, 2)],
    [(7, 0, 1), (9, 1, 1), (11, 2, 2)],
    [(12, 0, 3), (11, 3, 1)],
    [(10, 0, 2), (7, 2, 2)],
    [(8, 0, 1.5), (6, 1.5, 0.5), (4, 2, 1), (6, 3, 1)],
    [(5, 0, 1), (7, 1, 1), (9, 2, 2)],
    [(10, 0, 2), (11, 2, 2)],
    [(12, 0, 4)],
]
# The counter-melody (solo organ) - it moves where the tune holds, and falls
# where the tune climbs.
COUNTER = [
    [(6, 0, 1), (5, 1, 1), (3, 2, 2)],
    [(4, 0, 2), (7, 2, 2)],
    [(5, 0, 1), (7, 1, 1), (8, 2, 2)],
    [(3, 0, 2), (5, 2, 2)],
    [(6, 0, 1), (5, 1, 1), (3, 2, 2)],
    [(7, 0, 2), (4, 2, 2)],
    [(7, 0, 1), (8, 1, 1), (10, 2, 2)],
    [(7, 0, 1), (5, 1, 1), (7, 2, 1), (9, 3, 1)],
    [(8, 0, 2), (6, 2, 2)],
    [(9, 0, 2), (7, 2, 2)],
    [(8, 0, 1), (7, 1, 1), (5, 2, 2)],
    [(5, 0, 2), (7, 2, 2)],
    [(6, 0, 2), (8, 2, 2)],
    [(7, 0, 2), (5, 2, 2)],
    [(8, 0, 2), (9, 2, 2)],
    [(10, 0, 4)],
]
# The second peak adds eight bars: the tune goes over the top to E6.
EXT_CH = [6, 7, 1, 3, 4, 5, 6, 7]
EXT_TUNE = [
    [(8, 0, 1), (10, 1, 1), (13, 2, 2)],
    [(9, 0, 1), (11, 1, 1), (14, 2, 2)],
    [(15, 0, 3), (14, 3, 1)],
    [(12, 0, 2), (10, 2, 2)],
    [(11, 0, 1.5), (10, 1.5, 0.5), (8, 2, 1), (10, 3, 1)],
    [(9, 0, 1), (11, 1, 1), (12, 2, 2)],
    [(13, 0, 4)],
    [(14, 0, 4)],
]
EXT_COUNTER = [
    [(6, 0, 2), (8, 2, 2)],
    [(7, 0, 2), (9, 2, 2)],
    [(10, 0, 1), (9, 1, 1), (7, 2, 2)],
    [(7, 0, 2), (10, 2, 2)],
    [(6, 0, 2), (8, 2, 2)],
    [(7, 0, 2), (5, 2, 2)],
    [(8, 0, 2), (10, 2, 2)],
    [(9, 0, 2), (11, 2, 2)],
]
FINAL_CH = CHORUS_CH + EXT_CH
FINAL_TUNE = CHORUS_TUNE + EXT_TUNE
FINAL_COUNTER = COUNTER + EXT_COUNTER

# Velocity planes of the two storm peaks (the second also adds voices).
PEAK1_VEL = 98
PEAK2_VEL = 106

# The solos ride an eight-bar loop over a galloping bass ostinato.
SOLO_CH = [1, 1, 6, 6, 4, 4, 7, 7] * 2 + [1, 1, 6, 6, 4, 4, 5, 5]
OST = [0, 7, 0, 7, 0, 4, 6]


def _r(degs, s=0.0, u=0.5):
    """A run: evenly spaced degrees from eighth s, each u eighths long."""
    return [(d, s + i * u, u) for i, d in enumerate(degs)]


# Organ solo: (degree, start, dur) in eighths, base E4.
OSOLO = [
    [(8, 0, 3), (7, 3, 1), (5, 4, 3)],
    [(3, 0, 1), (5, 1, 1), (8, 2, 2), (7, 4, 1), (5, 5, 1), (7, 6, 1)],
    [(8, 0, 3), (6, 3, 1), (10, 4, 3)],
    [(10, 0, 1), (8, 1, 1), (6, 2, 2), (8, 4, 3)],
    [(11, 0, 3), (10, 3, 1), (8, 4, 3)],
    [(6, 0, 1), (8, 1, 1), (11, 2, 2), (10, 4, 1), (8, 5, 1), (6, 6, 1)],
    [(7, 0, 2), (9, 2, 2), (11, 4, 3)],
    [(11, 0, 1), (9, 1, 1), (7, 2, 1), (9, 3, 1), (11, 4, 1), (14, 5, 2)],
    _r([8, 9, 10, 8, 9, 10, 11, 9, 10, 11, 12, 10, 11, 12]),
    _r([15, 14, 12, 10, 12, 10, 8, 7, 8, 7, 5, 3]) + [(5, 6, 1)],
    _r([6, 8, 10, 13, 10, 8, 6, 8, 10, 13, 15, 13, 10, 8]),
    [(13, 0, 3), (12, 3, 1), (10, 4, 1), (8, 5, 1), (10, 6, 1)],
    _r([11, 13, 15, 13, 11, 13, 15, 13, 11, 8, 11, 13, 15, 13]),
    [(15, 0, 2), (14, 2, 1), (13, 3, 1), (11, 4, 3)],
    _r([14, 13, 12, 11, 13, 12, 11, 10, 12, 11, 10, 9, 11, 9]),
    [(7, 0, 1), (9, 1, 1), (11, 2, 1), (14, 3, 1), (16, 4, 3)],
    [(15, 0, 4), (14, 4, 1), (12, 5, 1), (10, 6, 1)],
    _r([12, 10, 8, 10, 12, 10, 8, 10, 12, 15, 12, 10, 8, 7]),
    [(13, 0, 2), (15, 2, 2), (17, 4, 3)],
    [(17, 0, 1), (15, 1, 1), (13, 2, 1), (12, 3, 1), (10, 4, 3)],
    [(11, 0, 3), (8, 3, 1), (6, 4, 3)],
    [(4, 0, 2), (6, 2, 2), (8, 4, 3)],
    [(9, 0, 3), (7, 3, 1), (5, 4, 3)],
    [(5, 0, 7)],
]

# Guitar solo: as above plus an articulation flag - "b" bend up into the
# degree from the scale step below, "r" pre-bend and release, "v" vibrato.
GSOLO = [
    [(5, 0, 3, "b"), (7, 3, 1), (8, 4, 3, "v")],
    [(10, 0, 2, "b"), (8, 2, 1), (7, 3, 1), (5, 4, 3, "v")],
    [(8, 0, 1), (10, 1, 1), (13, 2, 2, "b"), (12, 4, 1), (10, 5, 2)],
    [(10, 0, 4, "r"), (8, 4, 3, "v")],
    [(11, 0, 3, "b"), (10, 3, 1), (8, 4, 3)],
    [(6, 0, 1), (8, 1, 1), (11, 2, 1), (13, 3, 1), (15, 4, 3, "b")],
    [(14, 0, 2, "v"), (11, 2, 2), (9, 4, 3, "b")],
    [(7, 0, 1), (9, 1, 1), (11, 2, 1), (9, 3, 1), (11, 4, 1),
     (14, 5, 2, "b")],
    _r([8, 10, 12, 10, 8, 10, 12, 10, 8, 10, 12, 15, 12, 10]),
    [(15, 0, 3, "b")] + _r([14, 12, 10, 8], 3.0) + [(7, 5, 2, "v")],
    _r([6, 8, 10, 8, 6, 8, 10, 13, 10, 8, 10, 13, 15, 13]),
    [(17, 0, 3, "b"), (15, 3, 1), (13, 4, 3, "v")],
    _r([11, 13, 15, 13, 11, 8, 11, 13, 15, 13, 11, 13, 15, 17]),
    [(15, 0, 4, "r"), (13, 4, 1), (11, 5, 2)],
    _r([14, 12, 11, 9, 12, 11, 9, 7, 11, 9, 7, 5, 7, 9]),
    [(11, 0, 2, "b"), (14, 2, 2, "b"), (16, 4, 3, "b")],
    [(15, 0, 5, "b"), (14, 5, 1), (12, 6, 1)],
    _r([15, 12, 10, 12, 15, 12, 10, 12, 15, 12, 10, 8, 10, 12]),
    [(13, 0, 2, "b"), (15, 2, 2), (17, 4, 3, "b")],
    _r([17, 15, 13, 12, 15, 13, 12, 10, 13, 12, 10, 8, 10, 8]),
    [(11, 0, 3, "b"), (13, 3, 1), (15, 4, 3, "b")],
    _r([15, 13, 11, 13, 15, 13, 11, 8, 11, 8, 6, 8, 11, 13]),
    [(12, 0, 2, "b"), (14, 2, 2, "b"), (16, 4, 3, "b")],
    [(16, 0, 3, "v")] + _r([14, 12, 11, 9], 3.0) + [(8, 5, 1), (7, 6, 1)],
]

INTRO_CH = [1] * 12 + [6, 6, 7, 7]
INTRO_KIND = "AB" * 6 + "ABAA"
INTRO_LEAD = [
    [(8, 0, 7)], [(7, 0, 4), (5, 4, 3)], [(10, 0, 7)],
    [(8, 0, 4), (6, 4, 3)], [(9, 0, 7)], [(11, 0, 4), (9, 4, 3)],
]

EYE_PHRASE = 0               # the hymn phrase the far organ remembers
EYE_STRETCH = 2.0
T_HYMN = T_EYE + 8.0
EYE_BASS = [8, 4, 8, 4, 8]   # E / A / E / A / E, eight beats each

CODA_CH = [1, 1, 1, 1, 6, 7, 1, 1, 4, 5, 6, 7, 1, 1, 1, 1]
CODA_KIND = "ABABAAAB" + "AAAA" + "ABAB"
CODA_LEAD = [[(11, 0, 7)], [(12, 0, 7)], [(13, 0, 7)], [(14, 0, 7)]]
T_STOP = T_CODA + 16 * BAR7  # two stop-time bars: the beam, bare
T_RUN = T_CODA + 18 * BAR7   # one bar of unison scale
T_SLAM = T_CODA + 19 * BAR7  # the slammed unison
SLAM = [(LEAD, 76), (RHY, 40), (RHY2, 52), (BASS, 28), (ORG, 52), (ORG, 64),
        (SOLO, 76), (BRASS, 52), (BRASS, 64), (TIMP, 40)]
PITCHED = (LEAD, RHY, BASS, ORG, SOLO, BRASS, TIMP, LAMP, RHY2)

BASS_CH_ROOT = {1: 8, 3: 10, 4: 4, 5: 5, 6: 6, 7: 7}
TIMP_P = {1: 40, 3: 43, 4: 45, 5: 47, 6: 48, 7: 50}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def P(base: int, degree: int) -> int:
    return en.pitch(base, MODE, degree)


def _halves(c):
    return c if isinstance(c, tuple) else (c, c)


def _line(sc, ch, t0, base, notes, unit, vel, gate=0.94, jt=3, jv=4,
          bloom=False, shift=0):
    """Play (degree, start, dur) triples; bloom opens CC1 on held notes."""
    for item in notes:
        d, s, du = item[0], item[1], item[2]
        b, ln = t0 + s * unit, du * unit
        sc.note(ch, P(base, d + shift), b, ln * gate, vel, jt=jt, jv=jv)
        if bloom and ln >= 1.5:
            en.cc_curve(sc, ch, 1, [(b, 0), (b + ln * 0.4, 15),
                                    (b + ln * 0.8, 85), (b + ln * 0.95, 0)],
                        step=0.25)


def _riff_bar(sc, t, root, kind, vel, voices, count=7):
    """One 7/8 riff bar in octaves across voices [(ch, base, jt)]."""
    for i, off in enumerate(RIFF[kind][:count]):
        v = vel + (9 if i in ACCENTS7 else -3)
        for ch, base, jt in voices:
            sc.note(ch, P(base, root + off), t + i * E8, E8 * 0.9, v,
                    jt=jt, jv=3)


def _d7(sc, t, v, crash=False, kick6=False, hat=HH, fill=False, snare=SN):
    """A 7/8 bar of kit: kick-kick-snare on eighths 0/2/4 (the 2+2+3)."""
    sc.hit(K, t, v + 4)
    sc.hit(K, t + 1.0, v - 6)
    if fill:
        for i, key in enumerate([SN, SN, T1, T1, T2, FT]):
            sc.note(DR, key, t + 2.0 + i * 0.25, 0.2, v - 12 + i * 5,
                    jt=2, jv=3)
    else:
        sc.hit(snare, t + 2.0, v + 8)
        if kick6:
            sc.hit(K, t + 3.0, v - 10)
    for i in range(7):
        if fill and i >= 4:
            break
        if crash and i == 0:
            sc.note(DR, CR, t, 1.5, v + 2, jt=2, jv=3)
            continue
        sc.note(DR, hat, t + i * E8, 0.4,
                v - 36 + (10 if i in ACCENTS7 else 0), jt=2, jv=4)


def _d4(sc, t, v, crash=False, hats16=False, kicks=(0.0, 1.5, 2.0),
        fill=False):
    """A 4/4 bar of kit: the backbeat (snare on 2 and 4)."""
    for k in kicks:
        sc.hit(K, t + k, v + 4 if k == 0.0 else v - 6)
    sc.hit(SN, t + 1.0, v + 8)
    if fill:
        for i, key in enumerate([SN, SN, T1, T1, SN, T2, T2, FT]):
            sc.note(DR, key, t + 2.0 + i * 0.25, 0.2, v - 14 + i * 4,
                    jt=2, jv=3)
    else:
        sc.hit(SN, t + 3.0, v + 8)
    n = 16 if hats16 else 8
    step = BAR4 / n
    for i in range(n):
        b = i * step
        if fill and b >= 2.0:
            break
        if crash and i == 0:
            sc.note(DR, CR, t, 1.5, v + 2, jt=2, jv=3)
            continue
        on_beat = abs(b - round(b)) < 1e-9
        key = OH if (not hats16 and i == 7) else HH
        vel = v - 34 + (10 if on_beat else 0) - (8 if (hats16 and i % 2) else 0)
        sc.note(DR, key, t + b, step * 0.8, vel, jt=2, jv=4)


def _pad(sc, t0, roots, span, vel, lo=52, hi=72, vel_end=None):
    en.pad_block(sc, ORG, t0, [en.triad(E3, MODE, r) for r in roots], span,
                 size=3, lo=lo, hi=hi, vel=vel, vel_end=vel_end,
                 legato=-0.08)


def _brass_voicing(root):
    return en.voice_lead(en.triad(E3, MODE, root), None, 3, 57, 76)


def _stab(sc, t, root, vel, dur=0.42):
    for p in _brass_voicing(root):
        sc.note(BRASS, p, t, dur, vel, jt=2, jv=3)


def _timp_roll(sc, t0, t1, pitch, v0, v1, step=0.25):
    n = int(round((t1 - t0) / step))
    for i in range(n):
        sc.note(TIMP, pitch, t0 + i * step, step * 0.9,
                round(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _rev(sc, target, lead=4.0, vel=96):
    """Reverse-cymbal swell arriving at target."""
    sc.note(REV, 60, target - lead, lead - 0.05, vel, jt=0, jv=0)
    en.cc_curve(sc, REV, 11, [(target - lead, 30), (target - 0.1, 127)],
                step=0.25)


def _sea(sc, t0, t1, pts):
    """The surf: one held key per movement, CC11 breathing."""
    sc.note(SEA, 60, t0, (t1 - t0) - 0.06, 64, jt=0, jv=0)
    en.cc_curve(sc, SEA, 11, pts, step=1.0)


# ---------------------------------------------------------------------------
# Section engines
# ---------------------------------------------------------------------------


def _verse(sc, t0, vel, harmony=(), brass=(), timp=(), org_vel=60):
    _pad(sc, t0, VERSE_CH, BAR7, org_vel)
    for i, r in enumerate(VERSE_CH):
        t = t0 + i * BAR7
        _riff_bar(sc, t, r, VERSE_KIND[i], vel, [(BASS, E1, 0), (RHY, E2, 2)])
        _d7(sc, t, vel, crash=(i % 8 == 0), kick6=(i % 2 == 1),
            fill=(i % 8 == 7))
        _line(sc, LEAD, t, E4, VERSE_TUNE[i], E8, vel + 8, bloom=True)
        if i in harmony:
            _line(sc, SOLO, t, E4, VERSE_TUNE[i], E8, vel - 8, shift=-2)
        if i in brass:
            _stab(sc, t, r, vel)
            _stab(sc, t + 2.0, r, vel - 6)
        if i in timp:
            sc.note(TIMP, TIMP_P[r], t, 0.9, vel, jt=0, jv=3)


def _chorus(sc, t0, chords, tune, vel, next_root, counter=None, brass=0,
            timp=0, rhy2=False, hats16=False, dbl_from=None, crash_every=4,
            org_vel=74):
    nb = len(chords)
    halves = [h for c in chords for h in _halves(c)]
    _pad(sc, t0, halves, 2.0, org_vel)
    for i, c in enumerate(chords):
        t = t0 + i * BAR4
        a, b = _halves(c)
        nxt = _halves(chords[i + 1])[0] if i + 1 < nb else next_root
        last = i == nb - 1
        kicks = (0.0, 1.5, 2.0)
        if dbl_from is not None and i >= dbl_from:
            kicks = tuple(k * 0.5 for k in range(8))
        _d4(sc, t, vel, crash=(i % crash_every == 0), hats16=hats16,
            kicks=kicks, fill=(i % 8 == 7))
        # bass: driving eighths, root / octave / fifth, then a step into the
        # next root
        ca, cb, nr = BASS_CH_ROOT[a], BASS_CH_ROOT[b], BASS_CH_ROOT[nxt]
        if nr == cb + 1:
            appr = nr + 1
        elif nr > cb:
            appr = nr - 1
        elif nr < cb:
            appr = nr + 1
        else:
            appr = cb + 4
        if a == b:
            degs = [ca, ca, ca + 7, ca, ca + 4, ca + 4, ca + 7, appr]
        else:
            degs = [ca, ca, ca + 7, ca + 4, cb, cb, cb + 7, appr]
        for k, d in enumerate(degs):
            sc.note(BASS, P(E1, d), t + k * E8, E8 * 0.9,
                    vel + (8 if k % 2 == 0 else -2),
                    jt=0 if k == 0 else 3, jv=3)
        # rhythm guitar: power chords on the 3+3+2, palm chugs between
        for k in range(8):
            root = P(E2, a if k < 4 else b)
            if k in (0, 3, 6):
                for j, p in enumerate((root, root + 7, root + 12)):
                    sc.note(RHY, p, t + k * E8, 0.46, vel + 6 - j, jt=2, jv=3)
            else:
                sc.note(RHY, root, t + k * E8, 0.38, vel - 20, jt=2, jv=3)
        if rhy2:
            for r, off in ((a, 0.0), (b, 2.0)):
                root = P(E3, r)
                for p in (root, root + 7):
                    sc.note(RHY2, p, t + off, 1.9, vel, jt=2, jv=3)
        _line(sc, LEAD, t, E4, tune[i], 1.0, vel + 8, bloom=True)
        if counter is not None:
            _line(sc, SOLO, t, E4, counter[i], 1.0, vel - 2)
        if brass:
            _stab(sc, t, a, vel + 2)
            _stab(sc, t + 1.5, a, vel - 4)
            if brass == 2:
                _stab(sc, t + 3.0, b, vel + 2)
        if timp and last:
            sc.note(TIMP, TIMP_P[a], t, 0.9, vel + 4, jt=0, jv=3)
            _timp_roll(sc, t + 2.0, t + 4.0, TIMP_P[b], vel - 34, vel + 10)
        elif timp == 2:
            sc.note(TIMP, TIMP_P[a], t, 0.9, vel + 4, jt=0, jv=3)
            sc.note(TIMP, TIMP_P[b], t + 2.0, 0.9, vel - 8, jt=0, jv=3)
        elif timp and i % 4 == 0:
            sc.note(TIMP, TIMP_P[a], t, 0.9, vel + 4, jt=0, jv=3)


def _backing(sc, t0, vels, rhy_bars, hats, crash_bars, fill_bars, org_vel,
             timp_bars=(0, 8, 16)):
    """The solo bed: galloping bass ostinato, 7/8 kit, organ pad."""
    _pad(sc, t0, SOLO_CH, BAR7, org_vel, lo=48, hi=67)
    for i, r in enumerate(SOLO_CH):
        t, v = t0 + i * BAR7, vels[i]
        for k, off in enumerate(OST):
            sc.note(BASS, P(E1, r + off), t + k * E8, E8 * 0.88,
                    v + (8 if k in ACCENTS7 else -4),
                    jt=0 if k == 0 else 3, jv=3)
        _d7(sc, t, v, crash=i in crash_bars, kick6=(i % 2 == 1),
            hat=hats[i], fill=i in fill_bars)
        if i in rhy_bars:
            root = P(E2, r)
            for k in ACCENTS7:
                for p in (root, root + 7):
                    sc.note(RHY, p, t + k * E8, 0.42, v - 4, jt=2, jv=3)
        if i in timp_bars:
            sc.note(TIMP, TIMP_P[r], t, 0.9, v, jt=0, jv=3)


def _lead_solo(sc, t, notes, vel):
    """Guitar-solo bar: plain notes, bends ("b"), releases ("r"), vibrato."""
    for item in notes:
        d, s, du = item[0], item[1], item[2]
        flag = item[3] if len(item) > 3 else ""
        b, ln = t + s * E8, du * E8
        if flag == "b":
            lo = P(E4, d - 1)
            step = float(P(E4, d) - lo)
            sc.note(LEAD, lo, b, ln * 0.93, vel, jt=0, jv=3)
            en.bend_ramp(sc, LEAD, b + 0.05, b + min(0.45, ln * 0.45),
                         0.0, step, steps=8)
            if ln >= 1.5:
                en.vibrato(sc, LEAD, b + 0.6, ln * 0.93 - 0.7, depth=0.2,
                           cycles_per_beat=1.5, delay=0.0, center=step)
            sc.bend(LEAD, b + ln - 0.06, 0.0)
        elif flag == "r":
            step = float(P(E4, d + 1) - P(E4, d))
            sc.bend(LEAD, b, step)
            sc.note(LEAD, P(E4, d), b, ln * 0.93, vel, jt=0, jv=3)
            en.bend_ramp(sc, LEAD, b + ln * 0.35, b + ln * 0.7, step, 0.0,
                         steps=8)
        elif flag == "v":
            sc.note(LEAD, P(E4, d), b, ln * 0.93, vel, jt=0, jv=3)
            en.vibrato(sc, LEAD, b, ln * 0.9, depth=0.25,
                       cycles_per_beat=1.5, delay=0.3)
        else:
            sc.note(LEAD, P(E4, d), b, ln * 0.93, vel, jt=0, jv=3)


# ---------------------------------------------------------------------------
# The movements
# ---------------------------------------------------------------------------


def _b_intro(sc):
    """I. Landfall - surf, a drone, and the riff alone: the beam in 7/8."""
    t0 = T_INTRO
    for ch in (RHY, ORG, BRASS):
        sc.cc(ch, 11, 104, 0.0)
    sc.cc(SOLO, 11, 112, 0.0)
    _sea(sc, t0, T_V1, [(0.0, 70), (5.0, 124), (21.0, 96), (35.0, 60),
                        (56.0, 46)])
    # organ drone under the first ten bars, fading up
    sc.note(ORG, 40, 0.0, 34.8, 58, jt=0, jv=0)
    sc.note(ORG, 47, 0.0, 34.8, 54, jt=0, jv=0)
    en.expr_curve(sc, ORG, [(0.0, 24), (7.0, 70), (21.0, 92), (35.0, 104)])
    en.leslie(sc, ORG, 0.0, 35.0, 8, 44)
    sc.note(TIMP, 40, 0.0, 2.0, 58, jt=0, jv=0)
    _rev(sc, 2 * BAR7, lead=5.0, vel=80)
    for i in range(2, 16):
        t = t0 + i * BAR7
        vel = round(en.lerp(74, 98, (i - 2) / 13))
        voices = [(RHY, E2, 2)]
        if i >= 6:
            voices.insert(0, (BASS, E1, 0))
        _riff_bar(sc, t, INTRO_CH[i], INTRO_KIND[i], vel, voices)
        if i in (4, 5):                         # the hat finds the 2+2+3
            for k in range(7):
                sc.note(DR, HH, t + k * E8, 0.4,
                        50 + (14 if k in ACCENTS7 else 0), jt=2, jv=4)
        elif 6 <= i < 10:
            _d7(sc, t, vel - 12, snare=STICK)
        elif i >= 10:
            _d7(sc, t, vel, crash=(i == 10), kick6=(i % 2 == 1),
                fill=(i == 15))
    _pad(sc, t0 + 10 * BAR7, INTRO_CH[10:], BAR7, 66)
    for j, bar in enumerate(INTRO_LEAD):        # the lead's first call
        _line(sc, LEAD, t0 + (10 + j) * BAR7, E4, bar, E8, 100, bloom=True)
    for p in _brass_voicing(7):                 # a swell on the dominant side
        sc.note(BRASS, p, t0 + 14 * BAR7, 2 * BAR7 - 0.15, 84, jt=2, jv=3)
    en.expr_curve(sc, BRASS, [(49.0, 36), (55.5, 116), (56.0, 104)],
                  step=0.5)
    _timp_roll(sc, t0 + 15 * BAR7, T_V1, 50, 40, 104)
    _rev(sc, T_V1, lead=4.0)


def _b_verse1(sc):
    """II. Verse - the tune over the riff."""
    _sea(sc, T_V1, T_C1, [(T_V1, 46)])
    sc.cc(ORG, 1, 30, T_V1)
    _verse(sc, T_V1, 92)
    _rev(sc, T_C1, lead=4.0)


def _b_chorus1(sc):
    """III. Chorus - 4/4, the tune squares up to the wind."""
    _sea(sc, T_C1, T_V2, [(T_C1, 44)])
    en.leslie(sc, ORG, T_C1, T_C1 + 4.0, 30, 112)
    _chorus(sc, T_C1, CHORUS_CH, CHORUS_TUNE, 94, next_root=1)
    en.leslie(sc, ORG, T_V2 - 4.0, T_V2, 112, 30)


def _b_verse2(sc):
    """IV. Verse - the organ shadows the tune in thirds; brass, timpani."""
    _sea(sc, T_V2, T_C2, [(T_V2, 46)])
    _verse(sc, T_V2, 95, harmony=range(8, 16), brass=(8, 10, 12, 14),
           timp=(0, 4, 8, 12), org_vel=64)
    _timp_roll(sc, T_C2 - 1.5, T_C2, 47, 60, 106)
    _rev(sc, T_C2, lead=4.0)


def _b_chorus2(sc):
    """V. Chorus - the first peak: counter-melody, brass stabs, timpani."""
    _sea(sc, T_C2, T_OSOLO, [(T_C2, 44)])
    en.leslie(sc, ORG, T_C2, T_C2 + 4.0, 30, 118)
    _chorus(sc, T_C2, CHORUS_CH, CHORUS_TUNE, PEAK1_VEL, next_root=1,
            counter=COUNTER, brass=1, timp=1, org_vel=78)


def _b_organ_solo(sc):
    """VI. Organ solo - eight bars singing, eight running, eight blown out."""
    t0 = T_OSOLO
    _sea(sc, t0, T_EYE, [(t0, 46), (t0 + 70.0, 46), (T_EYE, 70)])
    vels = [90] * 8 + [96] * 12 + [88, 80, 70, 58]
    hats = [RD] * 8 + [HH] * 12 + [RD] * 4
    _backing(sc, t0, vels, rhy_bars=range(8, 20), hats=hats,
             crash_bars=(0, 8, 16), fill_bars=(7, 15), org_vel=58)
    en.leslie(sc, ORG, t0, t0 + 4.0, 118, 36)
    for i, bar in enumerate(OSOLO):
        v = 102 if i < 20 else (96, 88, 78, 66)[i - 20]
        _line(sc, SOLO, t0 + i * BAR7, E4, bar, E8, v, gate=0.92, jt=2)
    # the Leslie: slow chorale, spun up for the high held notes, then down
    en.cc_curve(sc, SOLO, 1, [(t0, 24), (t0 + 28.0, 50), (t0 + 38.5, 118),
                              (t0 + 42.0, 60), (t0 + 56.0, 124),
                              (t0 + 70.0, 96), (T_EYE, 12)], step=0.5)
    en.expr_curve(sc, SOLO, [(t0, 112), (t0 + 70.0, 112), (T_EYE, 70)])
    # the band falls away under the last four bars
    en.expr_curve(sc, ORG, [(t0 + 70.0, 104), (T_EYE - 0.5, 60)])
    en.expr_curve(sc, BASS, [(t0 + 70.0, 127), (T_EYE - 0.5, 70)])
    sc.cc(BASS, 11, 127, T_EYE)
    sc.cc(ORG, 11, 104, T_EYE)


def _b_eye(sc):
    """VII. The eye of the storm - surf, the lamp, the keeper's hymn."""
    t0 = T_EYE
    _sea(sc, t0, T_GSOLO, [(t0, 70), (t0 + 6.0, 127), (t0 + 44.0, 120),
                           (t0 + 56.0, 90), (T_GSOLO, 46)])
    sc.note(TIMP, 40, t0, 3.0, 40, jt=0, jv=0)        # the last gust
    sc.note(LAMP, material.LAMP_PITCH, t0 + 4.0, 12.0, 70, jt=0, jv=0)
    # the far organ: hymn phrase 1 (which is the beam, augmented), half speed
    sc.cc(SOLO, 1, 8, t0)
    en.expr_curve(sc, SOLO, [(t0, 70), (T_HYMN + 16.0, 100),
                             (T_HYMN + 40.0, 62), (T_GSOLO - 1.0, 112)])
    material.play_phrase(sc, SOLO, T_HYMN, E4, MODE, EYE_PHRASE,
                         stretch=EYE_STRETCH, vel=50, gate=0.98, jt=0, jv=2)
    sc.note(SOLO, P(E4, 1), T_HYMN + 32.0, 7.6, 44, jt=0, jv=0)
    for j, d in enumerate(EYE_BASS):
        sc.note(BASS, P(E1, d), T_HYMN + j * 8.0, 7.8, 48, jt=0, jv=2)
    # the back wall of the storm arrives: four bars of gathering
    tb = EYE_CORE[1]
    for k in range(32):
        sc.note(BASS, E2, tb + k * E8, E8 * 0.9,
                round(en.lerp(46, 100, k / 31)), jt=0, jv=2)
    for k in range(16):
        sc.note(RHY, E2, tb + 8.0 + k * E8, 0.36,
                round(en.lerp(48, 98, k / 15)), jt=0, jv=2)
        if k % 2 == 0:
            sc.note(DR, K, tb + 8.0 + k * E8, 0.25,
                    round(en.lerp(60, 104, k / 15)), jt=0, jv=2)
    sc.note(ORG, 40, tb, 15.8, 60, jt=0, jv=0)
    sc.note(ORG, 47, tb, 15.8, 60, jt=0, jv=0)
    sc.note(ORG, 52, tb + 8.0, 7.8, 64, jt=0, jv=0)
    en.expr_curve(sc, ORG, [(tb, 30), (T_GSOLO - 0.5, 112),
                            (T_GSOLO, 104)])
    en.leslie(sc, ORG, tb, T_GSOLO, 10, 110)
    _timp_roll(sc, tb + 8.0, T_GSOLO, 40, 30, 110)
    for k in range(16):                                # snare roll
        sc.note(DR, SN, tb + 12.0 + k * 0.25, 0.2,
                round(en.lerp(34, 112, k / 15)), jt=0, jv=2)
    _rev(sc, T_GSOLO, lead=6.0, vel=100)


def _b_guitar_solo(sc):
    """VIII. Guitar solo - the back wall: bends, runs, a high F sharp."""
    t0 = T_GSOLO
    _sea(sc, t0, T_V3, [(t0, 46)])
    vels = [94] * 8 + [98] * 8 + [102] * 8
    _backing(sc, t0, vels, rhy_bars=range(24), hats=[HH] * 16 + [OH] * 8,
             crash_bars=(0, 8, 16, 20), fill_bars=(7, 15, 23), org_vel=70)
    sc.cc(ORG, 1, 110, t0)
    for i, bar in enumerate(GSOLO):
        _lead_solo(sc, t0 + i * BAR7, bar, 104 + (i // 8) * 4)
    for p in _brass_voicing(5):
        sc.note(BRASS, p, t0 + 22 * BAR7, 2 * BAR7 - 0.15, 86, jt=2, jv=3)
    en.expr_curve(sc, BRASS, [(t0 + 22 * BAR7, 40), (T_V3 - 0.5, 118),
                              (T_V3, 104)], step=0.5)
    _timp_roll(sc, T_V3 - 2.0, T_V3, 47, 56, 108)
    _rev(sc, T_V3, lead=4.0)


def _b_verse3(sc):
    """IX. Verse - all hands: tune in thirds, brass on every beam bar."""
    _sea(sc, T_V3, T_C3, [(T_V3, 46)])
    _verse(sc, T_V3, 100, harmony=range(16),
           brass=[i for i, k in enumerate(VERSE_KIND) if k == "A"],
           timp=(0, 4, 8, 12), org_vel=70)
    _timp_roll(sc, T_C3 - 1.5, T_C3, 47, 60, 112)
    _rev(sc, T_C3, lead=5.0, vel=110)


def _b_chorus3(sc):
    """X. Chorus - the second peak: everything, and eight bars more."""
    _sea(sc, T_C3, T_CODA, [(T_C3, 44)])
    for ch in (RHY, ORG, BRASS):
        sc.cc(ch, 11, 127, T_C3)
    sc.cc(SOLO, 11, 124, T_C3)
    sc.cc(SOLO, 1, 100, T_C3)
    sc.cc(ORG, 1, 124, T_C3)
    _chorus(sc, T_C3, FINAL_CH, FINAL_TUNE, PEAK2_VEL, next_root=1,
            counter=FINAL_COUNTER, brass=2, timp=2, rhy2=True, hats16=True,
            dbl_from=16, crash_every=2, org_vel=86)
    # the last held D is bent up a whole tone into the coda's E
    tl = T_CODA - BAR4
    en.bend_ramp(sc, LEAD, tl + 2.5, tl + 3.4, 0.0, 2.0, steps=10)
    sc.bend(LEAD, tl + 3.92, 0.0)


def _b_coda(sc):
    """XI. Coda - the riff tutti, the beam bare, a slammed unison."""
    t0 = T_CODA
    sc.note(SEA, 60, t0, (T_SLAM - t0) - 0.06, 64, jt=0, jv=0)
    sc.cc(SEA, 11, 60, t0)
    _pad(sc, t0, CODA_CH, BAR7, 86)
    for i, r in enumerate(CODA_CH):
        t = t0 + i * BAR7
        kind = CODA_KIND[i]
        voices = [(BASS, E1, 0), (RHY, E2, 2), (RHY2, E3, 2), (SOLO, E3, 2)]
        if i < 8:
            voices.append((LEAD, E4, 1))
        elif i >= 12:
            voices.append((LEAD, E4 + 12, 1))
        _riff_bar(sc, t, r, kind, 104, voices)
        if 8 <= i < 12:                          # the lead climbs over it
            _line(sc, LEAD, t, E4, CODA_LEAD[i - 8], E8, 112, bloom=True)
            _stab(sc, t, r, 106)
        else:
            for k in ACCENTS7:
                sc.note(BRASS, P(E3, r + RIFF[kind][k]) + 12, t + k * E8,
                        0.4, 104, jt=2, jv=3)
        sc.note(TIMP, TIMP_P[r], t, 0.9, 104, jt=0, jv=3)
        if i >= 12:
            sc.note(TIMP, TIMP_P[r], t + 2.0, 0.9, 98, jt=0, jv=3)
        _d7(sc, t, 106, crash=(i % 4 == 0 or i >= 12), kick6=True,
            hat=OH if i >= 12 else HH)
    unison = [(BASS, E1), (RHY, E2), (RHY2, E3), (SOLO, E3), (LEAD, E4),
              (BRASS, E3)]
    for t in (T_STOP, T_STOP + BAR7):            # stop-time: the beam, bare
        for k, off in enumerate(RIFF_A[:5]):
            for ch, base in unison:
                sc.note(ch, P(base, 1 + off), t + k * E8, 0.3, 112,
                        jt=0, jv=2)
            sc.note(DR, K, t + k * E8, 0.25, 112, jt=0, jv=2)
            sc.note(DR, CR if k == 0 else SN, t + k * E8, 0.4, 110,
                    jt=0, jv=2)
        sc.note(TIMP, 40, t, 0.9, 108, jt=0, jv=2)
        sc.note(TIMP, 40, t + 2.0, 0.9, 110, jt=0, jv=2)
    for k in range(7):                           # the run up
        v = round(en.lerp(96, 120, k / 6))
        for ch, base in unison:
            sc.note(ch, P(base, 1 + k), T_RUN + k * E8, E8 * 0.9, v,
                    jt=0, jv=2)
        sc.note(DR, SN, T_RUN + k * E8, 0.25, v, jt=0, jv=2)
        if k in ACCENTS7:
            sc.note(DR, K, T_RUN + k * E8, 0.25, v, jt=0, jv=2)
    _timp_roll(sc, T_RUN, T_SLAM, 47, 64, 116)
    for ch, p in SLAM:                           # the slam
        sc.note(ch, p, T_SLAM, END - T_SLAM, 124, jt=0, jv=0)
    sc.note(DR, K, T_SLAM, 0.5, 127, jt=0, jv=0)
    sc.note(DR, SN, T_SLAM, 0.5, 124, jt=0, jv=0)
    sc.note(DR, CR, T_SLAM, END - T_SLAM, 124, jt=0, jv=0)


BUILDERS = [_b_intro, _b_verse1, _b_chorus1, _b_verse2, _b_chorus2,
            _b_organ_solo, _b_eye, _b_guitar_solo, _b_verse3, _b_chorus3,
            _b_coda]

# ---------------------------------------------------------------------------
# Verification config
# ---------------------------------------------------------------------------

BEAM_CHANNELS: set[int] = {BASS, RHY}
PROGRAM_WHITELIST: set[int] = {29, 30, 34, 18, 16, 61, 47, 122, 119,
                               material.LAMP_PROGRAM}
CENTERED_CHANNELS: set[int] = {LEAD, BASS, DR, SEA, LAMP}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    LEAD: (57, 93), RHY: (40, 67), BASS: (28, 55), ORG: (40, 79),
    SOLO: (52, 93), BRASS: (48, 88), TIMP: (38, 53), SEA: (60, 60),
    REV: (60, 60), LAMP: (62, 62), RHY2: (52, 76),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (298.0, 304.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------


def _near(beats, b, tol=0.03):
    return any(abs(x - b) <= tol for x in beats)


def _bends(sc, ch):
    """[(beat, semitones)] of every pitch-bend event on ch, in order."""
    out = []
    for tick, _prio, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0xE0:
            out.append((tick, (((d[1] | (d[2] << 7)) - 8192) / 8192.0) * 2.0))
    out.sort(key=lambda e: e[0])
    return [(t / en.PPQ, s) for t, s in out]


def _o_meter(sc):
    """7/8 verses grouped 2+2+3 against 4/4 backbeat choruses."""
    fails = []
    if sorted(sc.timesigs) != sorted(PART.TIME_SIGNATURES):
        fails.append("time-signature lane differs from PART.TIME_SIGNATURES")
    for name, t0, _t1, meter, _bars in MOVES:
        sig = [s for s in sorted(sc.timesigs) if s[0] <= t0 + 1e-9][-1]
        want = (7, 8) if meter == 7 else (4, 4)
        if (sig[1], sig[2]) != want:
            fails.append(f"'{name}' sounds under {sig[1]}/{sig[2]}, "
                         f"want {want[0]}/{want[1]}")
    drums = material.note_ons(sc, DR)
    kicks = [b for b, p, _v in drums if p == K]
    snares = [b for b, p, _v in drums if p == SN]
    bass = [b for b, _p, _v in material.note_ons(sc, BASS)]
    for idx in VERSE_IDX:
        name, t0, _t1, meter, bars = MOVES[idx]
        if meter != 7:
            fails.append(f"'{name}' is a verse but not in 7/8")
        for k in range(bars):
            b0 = t0 + k * BAR7
            if not (_near(kicks, b0) and _near(kicks, b0 + 1.0)
                    and _near(snares, b0 + 2.0)):
                fails.append(f"'{name}' bar {k + 1}: kit does not mark "
                             f"2+2+3 (kick, kick, snare on eighths 0/2/4)")
            if _near(snares, b0 + 1.0) or _near(snares, b0 + 3.0):
                fails.append(f"'{name}' bar {k + 1}: a 4/4 backbeat snare "
                             f"inside a 7/8 bar")
            got = [b for b in bass if b0 - 1e-6 <= b < b0 + BAR7 - 1e-6]
            want_b = [b0 + i * E8 for i in range(7)]
            if len(got) != 7 or any(abs(g - w) > 1e-6
                                    for g, w in zip(got, want_b)):
                fails.append(f"'{name}' bar {k + 1}: bass is not seven "
                             f"eighths on the 7/8 lattice")
    for idx in CHORUS_IDX:
        name, t0, _t1, meter, bars = MOVES[idx]
        if meter != 4:
            fails.append(f"'{name}' is a chorus but not in 4/4")
        for k in range(bars):
            b0 = t0 + k * BAR4
            if not (_near(kicks, b0) and _near(snares, b0 + 1.0)
                    and _near(snares, b0 + 3.0)):
                fails.append(f"'{name}' bar {k + 1}: no 4/4 backbeat "
                             f"(kick on 1, snare on 2 and 4)")
    return fails[:10]


def _o_beam_riff(sc):
    """The BEAM is the 7/8 riff: on every 'A' bar of every verse the bass
    states the cell on the first five eighths from the chord root, and the
    rhythm guitar doubles it an octave up."""
    fails = []
    bass = material.note_ons(sc, BASS)
    rhy = material.note_ons(sc, RHY)
    starts = {BASS: material.beam_statements(sc, BASS),
              RHY: material.beam_statements(sc, RHY)}
    count = 0
    for idx in VERSE_IDX:
        name, t0, _t1, _meter, _bars = MOVES[idx]
        for k, kind in enumerate(VERSE_KIND):
            if kind != "A":
                continue
            b0 = t0 + k * BAR7
            for ch in (BASS, RHY):
                if not _near(starts[ch], b0, 0.02):
                    fails.append(f"'{name}' bar {k + 1}: no BEAM on ch{ch} "
                                 f"at the bar line")
            five = [(b, p) for b, p, _v in bass
                    if b0 - 0.02 <= b < b0 + 2.5 - 0.02]
            dbl = [(b, p) for b, p, _v in rhy
                   if b0 - 0.02 <= b < b0 + 2.5 - 0.02]
            if len(five) != 5 or any(abs(b - (b0 + i * E8)) > 1e-6
                                     for i, (b, _p) in enumerate(five)):
                fails.append(f"'{name}' bar {k + 1}: the bass beam is not "
                             f"five straight eighths from the bar line")
                continue
            if five[0][1] % 12 != P(E1, VERSE_CH[k]) % 12:
                fails.append(f"'{name}' bar {k + 1}: beam root is not the "
                             f"chord root")
            if [p for _b, p in dbl] != [p + 12 for _b, p in five]:
                fails.append(f"'{name}' bar {k + 1}: guitar does not double "
                             f"the bass riff at the octave")
            count += 1
    if count < 24:
        fails.append(f"only {count} riff-beam bars verified, want >= 24")
    return fails[:10]


def _o_storm(sc):
    """Two storm peaks, the second verifiably bigger - and the biggest
    thing in the track."""
    fails = []
    e = [material.energy(sc, m[1], m[2]) for m in MOVES]
    p1, p2 = e[I_C2], e[I_C3]
    if p2 < 1.15 * p1:
        fails.append(f"second peak energy {p2:.0f} is not >= 1.15 x first "
                     f"peak {p1:.0f}")
    if max(e) != p2:
        fails.append(f"'{MOVES[e.index(max(e))][0]}' ({max(e):.0f}) "
                     f"out-masses the second peak ({p2:.0f})")
    for i in range(I_C2):
        if e[i] >= p1:
            fails.append(f"'{MOVES[i][0]}' ({e[i]:.0f}) is not below the "
                         f"first peak ({p1:.0f})")
    a1 = material.active_channels(sc, MOVES[I_C2][1], MOVES[I_C2][2])
    a2 = material.active_channels(sc, MOVES[I_C3][1], MOVES[I_C3][2])
    if len(a2) <= len(a1):
        fails.append(f"second peak plays {len(a2)} voices, first "
                     f"{len(a1)}: it must add voices")
    return fails


def _o_eye(sc):
    """The eye of the storm: >= 8 bars (here 12) stripped to almost nothing."""
    fails = []
    c0, c1 = EYE_CORE
    if (c1 - c0) / BAR4 < 8:
        fails.append("the eye is shorter than eight bars")
    p1 = material.energy(sc, MOVES[I_C2][1], MOVES[I_C2][2])
    e = material.energy(sc, c0, c1)
    if e > 0.05 * p1:
        fails.append(f"eye energy {e:.1f} exceeds 5% of the first peak "
                     f"({p1:.0f})")
    act = material.active_channels(sc, c0, c1)
    if len(act) > 5:
        fails.append(f"{len(act)} voices play in the eye; at most 5")
    loud = act & {LEAD, RHY, RHY2, BRASS, DR}
    if loud:
        fails.append(f"storm voices {sorted(loud)} play inside the eye")
    for ch in sorted(act):
        top = max(v for b, _p, v in material.note_ons(sc, ch) if c0 <= b < c1)
        if top > 76:
            fails.append(f"ch{ch} strikes velocity {top} in the eye (cap 76)")
    es = [material.energy(sc, m[1], m[2]) for m in MOVES]
    if min(es) != es[I_EYE]:
        fails.append("the eye is not the quietest movement")
    return fails


def _o_solos(sc):
    """An organ solo (guitar tacet) and a guitar solo (organ tacet) with
    real bends: ramped, a semitone or more, at least five of a whole tone."""
    fails = []
    o0, o1 = MOVES[I_OSOLO][1], MOVES[I_OSOLO][2]
    g0, g1 = MOVES[I_GSOLO][1], MOVES[I_GSOLO][2]
    organ = [x for x in material.note_ons(sc, SOLO) if o0 <= x[0] < o1]
    if len(organ) < 100:
        fails.append(f"organ solo has only {len(organ)} notes")
    if len({p for _b, p, _v in organ}) < 12:
        fails.append("organ solo uses fewer than 12 distinct pitches")
    if any(o0 <= b < o1 for b, _p, _v in material.note_ons(sc, LEAD)):
        fails.append("lead guitar plays during the organ solo")
    if any(g0 <= b < g1 for b, _p, _v in material.note_ons(sc, SOLO)):
        fails.append("solo organ plays during the guitar solo")
    spans = [s for s in material.note_spans(sc, LEAD) if g0 <= s[0] < g1]
    if len(spans) < 120:
        fails.append(f"guitar solo has only {len(spans)} notes")
    bends = _bends(sc, LEAD)
    real = whole = 0
    for on, off, _p, _v in spans:
        before = [s for b, s in bends if b <= on + 1e-6]
        start = before[-1] if before else 0.0
        vals = [s for b, s in bends if on + 1e-6 < b <= off + 1e-6]
        if len(set(vals)) < 5:
            continue                              # a jump is not a bend
        rise = abs(start) <= 0.1 and max(vals) >= 0.9
        fall = start >= 0.9 and min(vals) <= 0.1
        if rise or fall:
            real += 1
            if max([start] + vals) >= 1.9:
                whole += 1
    if real < 12:
        fails.append(f"only {real} real bends in the guitar solo, want >= 12")
    if whole < 5:
        fails.append(f"only {whole} whole-tone bends, want >= 5")
    return fails


def _o_purity(sc):
    """E aeolian throughout: no pitched voice leaves the mode."""
    fails = []
    for ch in PITCHED:
        bad = [(round(b, 2), p) for b, p, _v in material.note_ons(sc, ch)
               if p % 12 not in SCALE_PCS]
        if bad:
            fails.append(f"ch{ch} leaves E aeolian: {bad[:4]}")
    first = material.note_ons(sc, BASS)[0]
    if first[1] % 12 != 4:
        fails.append("the bass does not enter on E")
    return fails


def _o_counterpoint(sc):
    """Chorus counter-melody: consonant with the tune and the bass on every
    bar line of both peaks, and a line of its own (not a doubling)."""
    fails = []
    for idx in (I_C2, I_C3):
        name, t0, _t1, _meter, bars = MOVES[idx]
        same = 0
        for k in range(bars):
            b = t0 + k * BAR4 + 0.06
            lead = material.sounding(sc, LEAD, b)
            ctr = material.sounding(sc, SOLO, b)
            bass = material.sounding(sc, BASS, b)
            if len(lead) != 1 or len(ctr) != 1 or len(bass) != 1:
                fails.append(f"'{name}' bar {k + 1}: need one tune, one "
                             f"counter and one bass note on the bar line "
                             f"(got {lead}, {ctr}, {bass})")
                continue
            for a, c, what in ((lead[0], ctr[0], "tune/counter"),
                               (lead[0], bass[0], "tune/bass"),
                               (ctr[0], bass[0], "counter/bass")):
                if abs(a - c) % 12 not in material.CONSONANT:
                    fails.append(f"'{name}' bar {k + 1}: {what} interval "
                                 f"class {abs(a - c) % 12} is dissonant")
            if lead[0] % 12 == ctr[0] % 12:
                same += 1
        if same > bars // 5:
            fails.append(f"'{name}': counter doubles the tune on {same} of "
                         f"{bars} bar lines")
        # independence of rhythm: the counter moves where the tune holds
        lead_on = [b for b, _p, _v in material.note_ons(sc, LEAD)
                   if t0 <= b < t0 + bars * BAR4]
        ctr_on = [b for b, _p, _v in material.note_ons(sc, SOLO)
                  if t0 <= b < t0 + bars * BAR4]
        own = sum(1 for b in ctr_on if not _near(lead_on, b, 0.05))
        if own < bars // 2:
            fails.append(f"'{name}': only {own} counter onsets fall between "
                         f"the tune's notes")
    return fails[:10]


def _o_hymn_in_the_eye(sc):
    """In the eye the solo organ borrows one phrase of the keeper's hymn
    (half speed, E aeolian) and the LAMP tolls exactly once."""
    fails = []
    c0, c1 = EYE_CORE
    got = [s for s in material.phrase_statements(sc, SOLO, MODE, 0)
           if c0 <= s[0] < c1]
    if len(got) != 1:
        fails.append(f"{len(got)} hymn-phrase statements in the eye, want 1")
    else:
        _start, stretch, base = got[0]
        if abs(stretch - 2.0) > 0.01 or base % 12 != 4:
            fails.append(f"hymn phrase at stretch {stretch:.2f} on pitch "
                         f"{base}; want stretch 2 on E")
    lamp = material.note_ons(sc, LAMP)
    if len(lamp) != 1 or lamp[0][1] != material.LAMP_PITCH \
            or not c0 <= lamp[0][0] < c1:
        fails.append(f"the LAMP must toll once, on D4, in the eye: {lamp}")
    return fails


def _o_slam(sc):
    """Ends on a slammed unison: every pitched voice strikes E together,
    fortissimo, nothing follows, and it rings to the double bar."""
    fails = []
    for ch in (LEAD, RHY, RHY2, BASS, ORG, SOLO, BRASS, TIMP):
        spans = material.note_spans(sc, ch)
        last_on = max(s[0] for s in spans)
        final = [s for s in spans if abs(s[0] - last_on) < 1e-6]
        if abs(last_on - T_SLAM) > 1e-6:
            fails.append(f"ch{ch} last strikes at {last_on:.2f}, not with "
                         f"the slam at {T_SLAM:.2f}")
            continue
        for _on, off, p, v in final:
            if p % 12 != 4:
                fails.append(f"ch{ch} slams pitch {p}, not an E")
            if v < 115:
                fails.append(f"ch{ch} slam velocity {v} < 115")
            if off < END - 0.05:
                fails.append(f"ch{ch} slam stops at {off:.2f}, before END")
    for ch in sc.events:
        late = [b for b, _p, _v in material.note_ons(sc, ch)
                if b > T_SLAM + 1e-6]
        if late:
            fails.append(f"ch{ch} sounds a note after the slam")
    return fails[:10]


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("meter_7_8_against_4_4", _o_meter(sc)))
    results.append(("beam_is_the_riff", _o_beam_riff(sc)))
    results.append(("two_storm_peaks", _o_storm(sc)))
    results.append(("eye_of_the_storm", _o_eye(sc)))
    results.append(("solos_and_bends", _o_solos(sc)))
    results.append(("aeolian_purity", _o_purity(sc)))
    results.append(("chorus_counterpoint", _o_counterpoint(sc)))
    results.append(("hymn_and_lamp_in_the_eye", _o_hymn_in_the_eye(sc)))
    results.append(("slammed_unison", _o_slam(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------


def _db(ctx, b0, b1):
    i0, i1 = ctx.bar_window(b0, b1)
    return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))


def audio_checks(ctx):
    p1 = _db(ctx, T_C2 + 4.0, T_OSOLO - 4.0)
    p2 = _db(ctx, T_C3 + 4.0, T_CODA - 4.0)
    eye = _db(ctx, EYE_CORE[0] + 6.0, EYE_CORE[1] - 4.0)
    v1 = _db(ctx, T_V1 + 3.5, T_C1 - 3.5)
    slam = _db(ctx, T_SLAM, T_SLAM + 2.0)
    out = []
    fails = []
    if p2 < p1 + 0.5:
        fails.append(f"second peak {p2:.1f} dB is not >= 0.5 dB over the "
                     f"first {p1:.1f} dB")
    if p1 < v1:
        fails.append(f"first peak {p1:.1f} dB is below verse 1 {v1:.1f} dB")
    out.append(("storm_peaks_audio", fails))
    fails = []
    if eye > p1 - 10.0:
        fails.append(f"eye {eye:.1f} dB is not >= 10 dB under the first "
                     f"peak {p1:.1f} dB")
    if eye < -70.0:
        fails.append(f"eye {eye:.1f} dB: the surf and the hymn are inaudible")
    out.append(("eye_hush_audio", fails))
    fails = []
    if slam < p2 - 6.0:
        fails.append(f"slam {slam:.1f} dB is more than 6 dB under the "
                     f"second peak {p2:.1f} dB")
    out.append(("slam_audio", fails))
    return out
