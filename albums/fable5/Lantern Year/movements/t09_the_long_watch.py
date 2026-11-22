"""t09_the_long_watch.py - track 9 of *Lantern Year*: "The Long Watch".

November, the small hours: a slow blues in B-flat, 12/8 at dotted-quarter
= 56 (tempo 84; a bar is 6 quarter-beats, an eighth is 0.5, so the triplet
lattice is the 240-tick grid).  COMPOSER-NOTES section 7, T9.

Form (bars of 12/8):
    intro   4   Rhodes alone, then bass + brushes; the BEAM on the Rhodes
    I      12   tenor sax states the head (vibes answer in the rests)
    II     12   muted trumpet solo over a walking bass (sax guide tones)
    III    12   STOP-TIME: jazz-guitar breaks over downbeat hits (bars 1-8)
    IV     12   organ solo, Leslie spinning up; horn riff behind it
    V      12   everyone: the head in the sax, trumpet counter-melody
    tag     6   V-IV-I once more, ritardando, a B-flat 6/9 and one lamp bell

Every chorus runs the same verified twelve bars (bass roots on the bar
lines: I-IV-I-I / IV-IV-I-I / V-IV-I-V) and every chorus turns round on the
BEAM - 1-5-6-5-8, the major sixth at home in a blues - in bar 11, in the
voice of that chorus's soloist.  Nothing is louder than it needs to be.
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 9
TITLE = "The Long Watch"
FILE = "09 - The Long Watch.mid"
SEED = 20261209
COMMENT = ("Track 09 of 'Lantern Year' by Claude Fable 5: The Long Watch - "
           "November, the small hours. A slow 12/8 blues in B-flat: Rhodes "
           "intro, five 12-bar choruses (tenor sax head, muted trumpet, a "
           "stop-time guitar chorus, organ with Leslie, then everyone), "
           "each turning round on the BEAM cell, and a tag that settles on "
           "a B-flat 6/9 under one stroke of the lamp bell.")

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

E = 0.5                    # one eighth of 12/8 = one triplet of the pulse
BAR = 6.0                  # twelve eighths
LATTICE_TICKS = en.PPQ // 2
INTRO = 0.0
CHORUS = [24.0 + 72.0 * k for k in range(5)]
TAG = 384.0
END = 420.0
RIT = [(402.0, 76.0), (408.0, 68.0), (414.0, 58.0)]

RH, SAX, ORG, BASS, GTR, TPT, VIB, ORGL, GTRL, DR, LAMP, RHL = range(12)

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Small Hours (intro)", INTRO, CHORUS[0]),
        ("II. The Head (tenor)", CHORUS[0], CHORUS[1]),
        ("III. Muted Trumpet", CHORUS[1], CHORUS[2]),
        ("IV. Stop-Time (guitar)", CHORUS[2], CHORUS[3]),
        ("V. Organ", CHORUS[3], CHORUS[4]),
        ("VI. Everyone", CHORUS[4], TAG),
        ("VII. Tag", TAG, END),
    ],
    tempo_map=[(0.0, 84.0)] + RIT,
    time_signatures=[(0.0, 12, 8)],
    keysigs=[(0.0, -2, 0)],
    channels=[
        (RH, "Rhodes", 4, 82, 50, 48),
        (SAX, "Tenor sax", 66, 120, 64, 52),
        (ORG, "Organ pad", 16, 84, 78, 55),
        (BASS, "Upright bass", 32, 78, 64, 24),
        (GTR, "Jazz guitar comp", 26, 100, 46, 36),
        (TPT, "Muted trumpet", 59, 112, 72, 55),
        (VIB, "Vibraphone", 11, 108, 80, 62),
        (ORGL, "Organ solo", 16, 94, 68, 50),
        (GTRL, "Jazz guitar solo", 26, 122, 54, 44),
        (DR, "Brush kit", 0, 92, 64, 36),
        (LAMP, "Lamp bell", material.LAMP_PROGRAM, 84, 64, 70),
        (RHL, "Rhodes lead", 4, 106, 46, 58),
    ],
    program_changes=[(DR, 0.0, 40)],
)

BEAM_CHANNELS = {SAX, TPT, VIB, ORGL, GTRL, RHL}
PROGRAM_WHITELIST = {4, 66, 16, 32, 26, 59, 11, material.LAMP_PROGRAM}
CENTERED_CHANNELS = {SAX, BASS, DR, LAMP}
NOTE_RANGES = {
    RH: (46, 72), SAX: (53, 77), ORG: (60, 76), BASS: (29, 55),
    GTR: (50, 68), TPT: (58, 82), VIB: (65, 82), ORGL: (60, 86),
    GTRL: (60, 82), LAMP: (62, 62), RHL: (58, 86),
}
GAP_WHITELIST: list = []
BEND_EXEMPT: set = set()
DURATION_WINDOW = (302.0, 309.0)
BOUNDS_WHITELIST: list = []

VEL_CEILING = 108

# ---------------------------------------------------------------------------
# Harmony.  One table drives the comping, the pad and the form oracle.
# ---------------------------------------------------------------------------

FORM_ROOTS = ["Bb", "Eb", "Bb", "Bb", "Eb", "Eb", "Bb", "Bb",
              "F", "Eb", "Bb", "F"]
ROOT_PC = [en.n(r + "2") % 12 for r in FORM_ROOTS]

HARM = {
    1: [(0, "Bb13")], 2: [(0, "Eb9")], 3: [(0, "Bb13")],
    4: [(0, "Bb13"), (6, "Bb7#5")],
    5: [(0, "Eb9")], 6: [(0, "Eb9"), (6, "Edim")], 7: [(0, "Bb13")],
    8: [(0, "Bb13"), (6, "Gb9")],
    9: [(0, "F9")], 10: [(0, "Eb9")], 11: [(0, "Bb13")], 12: [(0, "F7#9")],
}
HARM_INTRO = {1: [(0, "Bb13")], 2: [(0, "Eb9")], 3: [(0, "Bb13")],
              4: [(0, "F7#9"), (6, "F13")]}
HARM_TAG = {1: [(0, "F9")], 2: [(0, "Eb9")],
            3: [(0, "Bb13"), (6, "G7#9")], 4: [(0, "Cm9"), (6, "F13")],
            5: [(0, "Bb69"), (6, "Eb69")], 6: [(0, "Bb69")]}

# Rootless Rhodes voicings (the bass owns the roots).
RHV = {
    "Bb13": [56, 60, 62, 67], "Bb7#5": [56, 60, 62, 66],
    "Eb9": [55, 58, 61, 65], "Edim": [55, 58, 61, 64],
    "Gb9": [58, 61, 64, 68], "F9": [57, 60, 63, 67],
    "F7#9": [57, 60, 63, 68], "F13": [57, 62, 63, 67],
    "G7#9": [59, 62, 65, 70], "Cm9": [58, 62, 63, 67],
    "Bb69": [58, 62, 65, 67], "Eb69": [55, 58, 60, 65],
}
# Organ pad: guide tones and one colour, a register above the Rhodes.
ORGV = {
    "Bb13": [62, 68, 72], "Bb7#5": [62, 66, 68],
    "Eb9": [61, 67, 70], "Edim": [61, 64, 70],
    "Gb9": [61, 64, 68], "F9": [63, 67, 69],
    "F7#9": [63, 69, 72], "F13": [63, 69, 74],
    "G7#9": [62, 65, 71], "Cm9": [63, 67, 70, 74],
    "Bb69": [62, 65, 67, 72], "Eb69": [63, 67, 70, 72],
}


def _sym(segs, pos):
    cur = segs[0][1]
    for p, s in segs:
        if p <= pos:
            cur = s
    return cur


def _bt(t0, bar, pos):
    return t0 + (bar - 1) * BAR + pos * E


# ---------------------------------------------------------------------------
# Melodic material: (bar, eighth, length-in-eighths, note[, flag]).
# Flags: s = scooped from a semitone below (the blue third leaning up),
#        b / B = string bend up a semitone / a tone, v = finger vibrato.
# ---------------------------------------------------------------------------

BEAM_LOW = ["Bb3", "F4", "G4", "F4", "Bb4"]
BEAM_HIGH = ["Bb4", "F5", "G5", "F5", "Bb5"]


def _beam_lick(names):
    """The turnaround lick in bar 11: a triplet out, a lean on the fifth,
    and the octave arriving an eighth early."""
    return [(11, 0, 1, names[0]), (11, 1, 1, names[1]), (11, 2, 1, names[2]),
            (11, 3, 2, names[3]), (11, 5, 4, names[4])]


HEAD = [
    (1, 3, 1, "F4"), (1, 4, 1, "Ab4"), (1, 5, 1, "Bb4"),
    (1, 6, 4, "D5", "s"), (1, 10, 1, "Bb4"), (1, 11, 1, "G4"),
    (2, 0, 5, "F4"), (2, 6, 1, "G4"), (2, 7, 1, "F4"), (2, 8, 1, "Db4"),
    (2, 9, 3, "Bb3"),
    (3, 3, 1, "F4"), (3, 4, 1, "Ab4"), (3, 5, 1, "Bb4"), (3, 6, 2, "Db5"),
    (3, 8, 1, "Bb4"), (3, 9, 1, "Ab4"), (3, 10, 2, "F4"),
    (4, 0, 5, "G4"), (4, 9, 1, "Bb4"), (4, 10, 1, "Ab4"), (4, 11, 1, "Gb4"),
    (5, 0, 3, "F4"), (5, 3, 1, "G4"), (5, 4, 1, "Bb4"), (5, 5, 1, "Db5"),
    (5, 6, 4, "Eb5"), (5, 10, 1, "Db5"), (5, 11, 1, "Bb4"),
    (6, 0, 5, "G4"), (6, 6, 2, "E4"), (6, 8, 1, "G4"), (6, 9, 1, "Bb4"),
    (6, 10, 2, "Db5"),
    (7, 0, 6, "D5", "s"), (7, 6, 1, "Bb4"), (7, 7, 1, "G4"), (7, 8, 4, "F4"),
    (8, 3, 1, "D4"), (8, 4, 1, "F4"), (8, 5, 1, "G4"), (8, 6, 3, "Ab4"),
    (8, 9, 1, "Bb4"), (8, 10, 1, "Ab4"), (8, 11, 1, "Gb4"),
]
HEAD_B = [      # bars 9-10, reused by the tag ("one more time")
    (9, 0, 3, "G4"), (9, 3, 1, "A4"), (9, 4, 1, "C5"), (9, 5, 1, "Eb5"),
    (9, 6, 3, "F5"), (9, 9, 1, "Eb5"), (9, 10, 1, "C5"), (9, 11, 1, "Ab4"),
    (10, 0, 4, "Bb4"), (10, 4, 1, "G4"), (10, 5, 1, "F4"), (10, 6, 3, "G4"),
    (10, 9, 1, "F4"), (10, 10, 1, "Db4"), (10, 11, 1, "C4"),
]
HEAD_END = _beam_lick(BEAM_LOW) + [
    (11, 9, 1, "Ab4"), (11, 10, 1, "F4"), (11, 11, 1, "Eb4"),
    (12, 0, 6, "C4"),
]

VIB_FILLS = [
    (2, 10, 1, "D5"), (2, 11, 1, "F5"), (3, 0, 3, "G5"),
    (4, 5, 1, "F5"), (4, 6, 2, "D5"),
    (7, 9, 1, "D5"), (7, 10, 1, "F5"), (7, 11, 1, "G5"), (8, 0, 3, "F5"),
]
VIB_TURN = [
    (12, 2, 1, "Ab5"), (12, 3, 1, "F5"), (12, 4, 1, "Eb5"), (12, 5, 1, "C5"),
    (12, 6, 3, "Ab4"), (12, 9, 3, "A4"),
]

TPT_SOLO = [
    (1, 2, 1, "Bb4"), (1, 3, 1, "Db5"), (1, 4, 5, "D5"), (1, 9, 1, "Bb4"),
    (1, 10, 1, "G4"), (1, 11, 1, "Bb4"),
    (2, 0, 4, "Db5"), (2, 4, 1, "Bb4"), (2, 5, 1, "G4"), (2, 6, 6, "F4"),
    (3, 2, 1, "F4"), (3, 3, 1, "G4"), (3, 4, 1, "Bb4"), (3, 5, 1, "D5"),
    (3, 6, 3, "F5"), (3, 9, 1, "E5"), (3, 10, 1, "Eb5"), (3, 11, 1, "D5"),
    (4, 0, 3, "Bb4"), (4, 3, 1, "Ab4"), (4, 4, 1, "G4"), (4, 5, 1, "F4"),
    (4, 6, 4, "Gb4"), (4, 10, 1, "Ab4"), (4, 11, 1, "Bb4"),
    (5, 0, 6, "Db5"), (5, 6, 1, "Eb5"), (5, 7, 1, "Db5"), (5, 8, 1, "Bb4"),
    (5, 9, 3, "G4"),
    (6, 2, 1, "G4"), (6, 3, 1, "Bb4"), (6, 4, 1, "Db5"), (6, 5, 1, "Eb5"),
    (6, 6, 3, "E5"), (6, 9, 1, "Db5"), (6, 10, 1, "Bb4"), (6, 11, 1, "G4"),
    (7, 0, 5, "F4"), (7, 5, 1, "G4"), (7, 6, 1, "Bb4"), (7, 7, 1, "D5"),
    (7, 8, 4, "G5"),
    (8, 0, 3, "F5"), (8, 3, 1, "D5"), (8, 4, 1, "Bb4"), (8, 5, 1, "Ab4"),
    (8, 6, 2, "Bb4"), (8, 8, 1, "Db5"), (8, 9, 3, "E5"),
    (9, 0, 4, "Eb5"), (9, 4, 1, "C5"), (9, 5, 1, "A4"), (9, 6, 2, "G4"),
    (9, 8, 1, "A4"), (9, 9, 1, "C5"), (9, 10, 1, "Eb5"), (9, 11, 1, "F5"),
    (10, 0, 4, "F5"), (10, 4, 1, "Eb5"), (10, 5, 1, "Db5"),
    (10, 6, 3, "Bb4"), (10, 9, 1, "G4"), (10, 10, 1, "F4"),
    (10, 11, 1, "Db4"),
] + _beam_lick(BEAM_LOW) + [
    (11, 9, 3, "Db5"), (12, 0, 5, "C5"),
]
SAX_GUIDE = [       # the 3rd/7th line under the trumpet
    (5, 0, 10, "Db4"), (6, 0, 10, "Db4"), (7, 0, 10, "D4"),
    (8, 0, 5, "D4"), (8, 6, 5, "E4"), (9, 0, 10, "Eb4"),
    (10, 0, 10, "Db4"),
]

GTR_SOLO = [
    (1, 2, 1, "F4"), (1, 3, 1, "Ab4"), (1, 4, 1, "Bb4"), (1, 5, 1, "Db5"),
    (1, 6, 3, "D5"), (1, 9, 1, "Bb4"), (1, 10, 1, "G4"), (1, 11, 1, "F4"),
    (2, 1, 1, "G4"), (2, 2, 1, "Bb4"), (2, 3, 1, "Db5"), (2, 4, 2, "F5"),
    (2, 6, 1, "Eb5"), (2, 7, 1, "Db5"), (2, 8, 1, "Bb4"), (2, 9, 3, "G4"),
    (3, 1, 2, "Bb4"), (3, 3, 1, "Db5"), (3, 4, 1, "Eb5"), (3, 5, 1, "E5"),
    (3, 6, 2, "F5"), (3, 8, 1, "Ab5"), (3, 9, 3, "Bb5", "v"),
    (4, 1, 1, "Ab5"), (4, 2, 1, "F5"), (4, 3, 1, "E5"), (4, 4, 1, "Eb5"),
    (4, 5, 1, "Db5"), (4, 6, 2, "Bb4"), (4, 8, 1, "Ab4"), (4, 9, 1, "Gb4"),
    (4, 10, 2, "F4"),
    (5, 1, 2, "G4"), (5, 3, 1, "Bb4"), (5, 4, 1, "Db5"), (5, 5, 1, "Eb5"),
    (5, 6, 5, "Eb5", "b"), (5, 11, 1, "Db5"),
    (6, 1, 1, "Bb4"), (6, 2, 1, "G4"), (6, 3, 3, "E4"), (6, 6, 1, "G4"),
    (6, 7, 1, "Bb4"), (6, 8, 1, "Db5"), (6, 9, 3, "E5", "v"),
    (7, 1, 2, "F5"), (7, 3, 1, "D5"), (7, 4, 1, "Bb4"), (7, 5, 1, "G4"),
    (7, 6, 3, "F4"), (7, 9, 1, "G4"), (7, 10, 1, "Bb4"), (7, 11, 1, "D5"),
    (8, 1, 2, "G5"), (8, 3, 1, "F5"), (8, 4, 1, "D5"), (8, 5, 1, "Bb4"),
    (8, 6, 3, "Ab4"), (8, 9, 1, "A4"), (8, 10, 1, "C5"), (8, 11, 1, "Eb5"),
    (9, 0, 4, "F5", "B"), (9, 4, 1, "F5"), (9, 5, 1, "Eb5"), (9, 6, 2, "C5"),
    (9, 8, 1, "A4"), (9, 9, 1, "C5"), (9, 10, 1, "Eb5"), (9, 11, 1, "F5"),
    (10, 0, 3, "G5"), (10, 3, 1, "F5"), (10, 4, 1, "Db5"), (10, 5, 1, "Bb4"),
    (10, 6, 3, "Db5", "v"), (10, 9, 1, "Bb4"), (10, 10, 1, "G4"),
    (10, 11, 1, "F4"),
] + _beam_lick(BEAM_HIGH) + [
    (11, 9, 1, "Ab5"), (11, 10, 1, "F5"), (11, 11, 1, "Eb5"),
    (12, 0, 5, "C5", "v"),
]

ORG_SOLO = [
    (1, 1, 1, "D4"), (1, 2, 1, "F4"), (1, 3, 6, "Ab4"), (1, 9, 1, "G4"),
    (1, 10, 1, "F4"), (1, 11, 1, "D4"),
    (2, 0, 3, "Db4"), (2, 3, 1, "Eb4"), (2, 4, 1, "F4"), (2, 5, 1, "G4"),
    (2, 6, 6, "Bb4"),
    (3, 0, 1, "Bb4"), (3, 1, 1, "Ab4"), (3, 2, 1, "F4"), (3, 3, 1, "E4"),
    (3, 4, 1, "Eb4"), (3, 5, 1, "Db4"), (3, 6, 3, "D4"), (3, 9, 1, "F4"),
    (3, 10, 1, "G4"), (3, 11, 1, "Bb4"),
    (4, 0, 5, "D5"), (4, 5, 1, "Bb4"), (4, 6, 3, "Gb4"), (4, 9, 1, "Ab4"),
    (4, 10, 1, "Bb4"), (4, 11, 1, "C5"),
    (5, 0, 6, "Db5"), (5, 6, 1, "Eb5"), (5, 7, 1, "F5"), (5, 8, 1, "G5"),
    (5, 9, 3, "Bb5"),
    (6, 0, 3, "Bb5"), (6, 3, 1, "G5"), (6, 4, 1, "F5"), (6, 5, 1, "Eb5"),
    (6, 6, 3, "E5"), (6, 9, 1, "G5"), (6, 10, 1, "Bb5"), (6, 11, 1, "Db6"),
    (7, 0, 8, "D6"), (7, 8, 1, "Bb5"), (7, 9, 1, "G5"), (7, 10, 1, "F5"),
    (7, 11, 1, "D5"),
    (8, 0, 3, "F5"), (8, 3, 1, "Ab5"), (8, 4, 1, "G5"), (8, 5, 1, "F5"),
    (8, 6, 3, "E5"), (8, 9, 1, "Db5"), (8, 10, 1, "Bb4"), (8, 11, 1, "Ab4"),
    (9, 0, 3, "A4"), (9, 3, 1, "C5"), (9, 4, 1, "Eb5"), (9, 5, 1, "G5"),
    (9, 6, 6, "A5"),
    (10, 0, 3, "G5"), (10, 3, 1, "F5"), (10, 4, 1, "Db5"), (10, 5, 1, "Bb4"),
    (10, 6, 2, "G4"), (10, 8, 1, "Bb4"), (10, 9, 1, "Db5"),
    (10, 10, 1, "Eb5"), (10, 11, 1, "F5"),
] + _beam_lick(BEAM_HIGH) + [
    (11, 9, 1, "Ab5"), (11, 10, 1, "F5"), (11, 11, 1, "D5"),
    (12, 0, 6, "C5"),
]
# The horn riff behind the organ: (bar, sax, trumpet), "da - daaa".
HORN_RIFF = [(5, "Db4", "F4"), (6, "Db4", "E4"), (7, "D4", "G4"),
             (8, "D4", "G4"), (9, "Eb4", "G4"), (10, "Db4", "F4")]

# The trumpet's counter-melody to the head in the last chorus: it fills the
# sax's rests and sits a third or a sixth above it on the strong pulses.
TPT_COUNTER = [
    (1, 0, 2, "D5"), (1, 2, 1, "Bb4"), (1, 6, 4, "F5"), (1, 10, 1, "D5"),
    (1, 11, 1, "Bb4"),
    (2, 0, 5, "Db5"), (2, 6, 1, "Bb4"), (2, 7, 1, "Ab4"), (2, 8, 1, "F4"),
    (2, 9, 3, "Db4"),
    (3, 0, 2, "D5"), (3, 2, 1, "Bb4"), (3, 6, 2, "F5"), (3, 8, 1, "D5"),
    (3, 9, 1, "C5"), (3, 10, 2, "Ab4"),
    (4, 0, 5, "Bb4"), (4, 5, 1, "C5"), (4, 6, 3, "D5"), (4, 9, 1, "Db5"),
    (4, 10, 1, "C5"), (4, 11, 1, "Bb4"),
    (5, 0, 3, "Bb4"), (5, 6, 4, "G5"), (5, 10, 1, "F5"), (5, 11, 1, "Db5"),
    (6, 0, 5, "Bb4"), (6, 6, 2, "G4"), (6, 8, 1, "Bb4"), (6, 9, 1, "Db5"),
    (6, 10, 2, "E5"),
    (7, 0, 6, "F5"), (7, 6, 1, "D5"), (7, 7, 1, "Bb4"), (7, 8, 4, "Ab4"),
    (8, 0, 3, "G4"), (8, 3, 3, "Bb4"), (8, 6, 3, "Db5"), (8, 9, 1, "E5"),
    (8, 10, 1, "Db5"), (8, 11, 1, "Bb4"),
    (9, 0, 3, "Eb5"), (9, 3, 1, "C5"), (9, 4, 1, "Eb5"), (9, 5, 1, "G5"),
    (9, 6, 3, "A5"), (9, 9, 1, "G5"), (9, 10, 1, "Eb5"), (9, 11, 1, "C5"),
    (10, 0, 4, "Db5"), (10, 4, 1, "Bb4"), (10, 5, 1, "Ab4"),
    (10, 6, 3, "Bb4"), (10, 9, 1, "Ab4"), (10, 10, 1, "F4"),
    (10, 11, 1, "Eb4"),
] + _beam_lick(BEAM_HIGH) + [
    (11, 9, 1, "F5"), (11, 10, 1, "D5"), (11, 11, 1, "C5"),
    (12, 0, 6, "A4"),
]

RHL_INTRO = [
    (1, 3, 1, "F5"), (1, 4, 1, "Ab5"), (1, 5, 1, "Bb5"), (1, 6, 5, "D6"),
    (2, 0, 3, "Db6"), (2, 3, 1, "Bb5"), (2, 4, 1, "G5"), (2, 5, 1, "F5"),
    (2, 6, 5, "Db5"),
    (3, 0, 1, "Bb4"), (3, 1, 1, "F5"), (3, 2, 1, "G5"), (3, 3, 2, "F5"),
    (3, 5, 6, "Bb5"),
    (4, 0, 2, "Ab5"), (4, 2, 1, "F5"), (4, 3, 1, "Eb5"), (4, 4, 1, "C5"),
    (4, 5, 1, "Ab4"), (4, 6, 5, "A4"),
]

# ---------------------------------------------------------------------------
# Bass lines: bar -> [(eighth, length, pitch)].  Every bar-line note is the
# root the form names.
# ---------------------------------------------------------------------------

BASS_TWO = {        # the two-feel under the head
    1: [(0, 5, 34), (6, 4, 41), (11, 1, 38)],
    2: [(0, 5, 39), (6, 4, 46), (11, 1, 45)],
    3: [(0, 5, 46), (6, 4, 41), (11, 1, 33)],
    4: [(0, 5, 34), (6, 4, 44), (11, 1, 40)],
    5: [(0, 5, 39), (6, 4, 46), (11, 1, 41)],
    6: [(0, 5, 39), (6, 4, 40), (11, 1, 43)],
    7: [(0, 5, 46), (6, 4, 41), (11, 1, 45)],
    8: [(0, 5, 46), (6, 4, 42), (11, 1, 40)],
    9: [(0, 5, 41), (6, 4, 48), (11, 1, 52)],
    10: [(0, 5, 51), (6, 4, 46), (11, 1, 45)],
    11: [(0, 3, 46), (3, 3, 50), (6, 3, 51), (9, 3, 52)],
    12: [(0, 5, 53), (6, 4, 41), (11, 1, 45)],
}
BASS_WALK = {       # four dotted quarters to the bar
    1: [(0, 3, 46), (3, 3, 50), (6, 3, 53), (9, 3, 52)],
    2: [(0, 3, 51), (3, 3, 49), (6, 3, 46), (9, 3, 45)],
    3: [(0, 3, 46), (3, 3, 44), (6, 3, 43), (9, 3, 41)],
    4: [(0, 3, 34), (3, 3, 38), (6, 3, 44), (9, 3, 40)],
    5: [(0, 3, 39), (3, 3, 43), (6, 3, 46), (9, 3, 41)],
    6: [(0, 3, 39), (3, 3, 46), (6, 3, 40), (9, 3, 43)],
    7: [(0, 3, 46), (3, 3, 50), (6, 3, 53), (9, 3, 50)],
    8: [(0, 3, 46), (3, 3, 44), (6, 3, 42), (9, 3, 40)],
    9: [(0, 3, 41), (3, 3, 45), (6, 3, 48), (9, 3, 51)],
    10: [(0, 3, 51), (3, 3, 49), (6, 3, 46), (9, 3, 43)],
    11: [(0, 3, 34), (3, 3, 38), (6, 3, 39), (9, 3, 40)],
    12: [(0, 3, 41), (3, 3, 36), (6, 3, 41), (9, 2, 45), (11, 1, 45)],
}
STOP_ROOTS = [34, 39, 34, 34, 39, 39, 34, 34]


def _walk_skips(lines, bars):
    """The same walk with the shuffle's skip note before chosen bar lines."""
    out = dict(lines)
    for b in bars:
        *head, (pos, _dur, p) = lines[b]
        out[b] = head + [(pos, 2, p), (11, 1, p)]
    return out


# ---------------------------------------------------------------------------
# Emitters.  Everything is tick-exact (jt=0): the lattice is the style.
# ---------------------------------------------------------------------------

def _vel(base, p, center, dur):
    v = base + 0.6 * (p - center) + (3 if dur >= 3 else 0)
    return int(max(20, min(VEL_CEILING - 4, round(v))))


def _line(sc, ch, t0, notes, base, center, style, ramp=None):
    """Play a tuple line.  style: 'wind' (CC11 swell + CC1 vibrato on long
    notes), 'organ' (CC11 swell + Leslie spin-up), 'pluck' (bends, finger
    vibrato) or 'plain'."""
    for item in notes:
        bar, pos, dur, name = item[:4]
        flag = item[4] if len(item) > 4 else ""
        p = en.n(name)
        t = _bt(t0, bar, pos)
        d = dur * E
        b = base + (ramp[bar - 1] if ramp else 0)
        gate = 0.94 if dur > 1 else 0.88
        sc.note(ch, p, t, d * gate, _vel(b, p, center, dur), jt=0, jv=2)
        if style == "wind":
            if flag == "s":
                en.bend_ramp(sc, ch, t, t + 0.4, -1.0, 0.0, steps=8)
            if dur >= 3:
                en.expr_curve(sc, ch, [(t, 88), (t + 0.45 * d, 120),
                                       (t + 0.92 * d, 84)], step=0.25)
                sc.cc(ch, 11, 100, t + d)
                en.cc_curve(sc, ch, 1, [(t, 0), (t + 0.4 * d, 0),
                                        (t + 0.8 * d, 58), (t + d, 0)],
                            step=0.25)
        elif style == "organ":
            if dur >= 3:
                en.expr_curve(sc, ch, [(t, 92), (t + 0.5 * d, 122),
                                       (t + 0.94 * d, 96)], step=0.25)
                sc.cc(ch, 11, 104, t + d)
            if dur >= 5:
                en.cc_curve(sc, ch, 1, [(t, 22), (t + 0.6 * d, 114),
                                        (t + d, 34)], step=0.25)
        elif style == "pluck":
            if flag in ("b", "B"):
                up = 1.0 if flag == "b" else 2.0
                en.bend_ramp(sc, ch, t + 0.25, t + 0.9, 0.0, up, steps=8)
                en.bend_ramp(sc, ch, t + d - 0.5, t + d - 0.12, up, 0.0,
                             steps=6)
            elif flag == "v":
                en.vibrato(sc, ch, t, d * 0.9, depth=0.22,
                           cycles_per_beat=3.5, delay=0.3, step=0.07)


def _comp(sc, t0, bar, harm, pat, vel):
    """One bar of Rhodes comping."""
    segs = harm[bar]
    tb = _bt(t0, bar, 0)
    if pat == "trip":       # the slow-blues triplets, last chorus only
        sym = segs[0][1]
        for pos in range(12):
            v = RHV[_sym(segs, pos)]
            acc = vel if pos % 3 == 0 else vel - 14
            for p in v[1:]:
                sc.note(RH, p, tb + pos * E, E * 0.8, acc, jt=0, jv=3)
        for pos, s in segs:
            nxt = min([q for q, _s in segs if q > pos] + [12])
            sc.note(RH, RHV[s][0], tb + pos * E, (nxt - pos) * E - 0.2,
                    vel, jt=0, jv=2)
        return sym
    if pat == "hit":
        hits = [(0, 1.5, 1.0)]
    elif pat == "hold":
        hits = [(p, (min([q for q, _s in segs if q > p] + [12]) - p) - 1, 1.0)
                for p, _s in segs]
    elif len(segs) > 1:
        hits = [(0, 5, 1.0) if pat == "A" else (2, 3, 0.92), (6, 5, 0.9)]
    elif pat == "A":
        hits = [(0, 5, 1.0), (8, 3, 0.8)]
    else:
        hits = [(2, 3, 0.92), (8, 3, 0.8)]
    for pos, dur, scale in hits:
        v = RHV[_sym(segs, pos)]
        for i, p in enumerate(v):
            top = 4 if i == len(v) - 1 else 0
            sc.note(RH, p, tb + pos * E, dur * E * 0.96,
                    int(vel * scale) + top, jt=0, jv=3)
    return None


def _stabs(sc, t0, bar, harm, vel, positions=(3, 9)):
    """Jazz-guitar backbeat stabs: three notes, short."""
    segs = harm[bar]
    for pos in positions:
        v = RHV[_sym(segs, pos)]
        for p in (v[0], v[2], v[3]):
            sc.note(GTR, p, _bt(t0, bar, pos), E * 0.8, vel, jt=0, jv=3)


def _pad(sc, t0, bar, harm, vel, level):
    """One bar of organ pad with a CC11 swell."""
    segs = harm[bar]
    tb = _bt(t0, bar, 0)
    for i, (pos, sym) in enumerate(segs):
        nxt = segs[i + 1][0] if i + 1 < len(segs) else 12
        for p in ORGV[sym]:
            sc.note(ORG, p, tb + pos * E, (nxt - pos) * E - 0.15, vel,
                    jt=0, jv=2)
    en.expr_curve(sc, ORG, [(tb, level - 14), (tb + 3.0, level),
                            (tb + 5.75, level - 12)], step=0.5)


def _bass(sc, t0, bar, notes, vel):
    for pos, dur, p in notes:
        v = vel + (8 if pos == 0 else (-8 if dur == 1 else 0))
        sc.note(BASS, p, _bt(t0, bar, pos), dur * E * 0.92, v, jt=0, jv=3)


def _drums(sc, t0, bar, level, fill=False, crash=0):
    """One bar of brushes.  level 1..4; fill = snare triplet into the next
    bar (with toms at level 4).  Voiced for the synth's brush kit as
    measured: its ride is very soft (so it is struck hard), its snare tap
    is loud at any velocity (so it is struck lightly), and its hi-hats
    (42/44) throw full-scale noise bursts, so they are not used."""
    tb = _bt(t0, bar, 0)

    def hit(key, pos, vel):
        sc.note(DR, key, tb + pos * E, 0.25, vel, jt=0, jv=3)

    ride = {1: 70, 2: 78, 3: 88, 4: 96}[level]
    snare = {1: 30, 2: 36, 3: 44, 4: 50}[level]
    kick = {1: 44, 2: 50, 3: 56, 4: 62}[level]
    for pos in (0, 3, 6, 9):
        hit(51, pos, ride)
    for pos in ((5, 11) if level == 1 else (2, 5, 8, 11)):
        hit(51, pos, ride - 14)
    if level >= 3:
        for pos in (1, 4, 7, 10):
            hit(51, pos, ride - 26)
    for pos in (3, 9):
        if not (fill and pos == 9):
            hit(38, pos, snare)
    hit(36, 0, kick)
    if level >= 2:
        hit(36, 6, kick - 10)
        if bar % 2 == 0 and not fill:
            hit(36, 11, kick - 18)
    if fill:
        if level >= 4:
            for pos, key in ((6, 50), (7, 47), (8, 45)):
                hit(key, pos, snare - 4)
        for i, pos in enumerate((9, 10, 11)):
            hit(38, pos, snare - 4 + 5 * i)
    if crash:
        hit(49, 0, crash)


def _horn_expr_reset(sc, t):
    for ch in (SAX, TPT):
        sc.cc(ch, 11, 100, t)
        sc.cc(ch, 1, 0, t)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _b_intro(sc):
    t0 = INTRO
    for ch in (SAX, TPT):
        sc.cc(ch, 11, 100, 0.0)
    sc.cc(ORG, 11, 70, 0.0)
    sc.cc(ORG, 1, 18, 0.0)          # Leslie on the slow rotor
    sc.cc(ORGL, 11, 104, 0.0)
    sc.cc(ORGL, 1, 22, 0.0)
    _comp(sc, t0, 1, HARM_INTRO, "hold", 46)
    _comp(sc, t0, 2, HARM_INTRO, "hold", 48)
    _comp(sc, t0, 3, HARM_INTRO, "A", 48)
    _comp(sc, t0, 4, HARM_INTRO, "A", 50)
    _line(sc, RHL, t0, RHL_INTRO, 62, 76, "plain")
    _bass(sc, t0, 3, [(0, 5, 34), (6, 4, 41), (11, 1, 38)], 62)
    _bass(sc, t0, 4, [(0, 5, 41), (6, 4, 36), (11, 1, 33)], 64)
    _drums(sc, t0, 3, 1)
    _drums(sc, t0, 4, 1)


def _b_head(sc):
    t0 = CHORUS[0]
    _line(sc, SAX, t0, HEAD + HEAD_B + HEAD_END, 68, 67, "wind")
    _line(sc, VIB, t0, VIB_FILLS + VIB_TURN, 56, 74, "plain")
    for bar in range(1, 13):
        _comp(sc, t0, bar, HARM, "A", 50)
        _bass(sc, t0, bar, BASS_TWO[bar], 68)
        _drums(sc, t0, bar, 1, fill=(bar == 12))
        if bar >= 9:
            _pad(sc, t0, bar, HARM, 50, 84)


def _b_trumpet(sc):
    t0 = CHORUS[1]
    _line(sc, TPT, t0, TPT_SOLO, 76, 70, "wind")
    _line(sc, SAX, t0, SAX_GUIDE, 50, 62, "wind")
    for bar in range(1, 13):
        _comp(sc, t0, bar, HARM, "A" if bar % 2 else "B", 54)
        _stabs(sc, t0, bar, HARM, 50)
        _bass(sc, t0, bar, BASS_WALK[bar], 72)
        _drums(sc, t0, bar, 2, fill=(bar in (8, 12)))
        _pad(sc, t0, bar, HARM, 52, 92)


def _b_stop(sc):
    t0 = CHORUS[2]
    _line(sc, GTRL, t0, GTR_SOLO, 86, 72, "pluck")
    for bar in range(1, 9):         # the stops: one hit on each bar line
        tb = _bt(t0, bar, 0)
        _comp(sc, t0, bar, HARM, "hit", 72)
        sc.note(BASS, STOP_ROOTS[bar - 1], tb, 0.9, 84, jt=0, jv=3)
        sc.note(DR, 36, tb, 0.25, 64, jt=0, jv=3)
        sc.note(DR, 38, tb, 0.25, 50, jt=0, jv=3)
    for bar in range(9, 13):        # time comes back for the turnaround
        _comp(sc, t0, bar, HARM, "A", 56)
        _stabs(sc, t0, bar, HARM, 50)
        _bass(sc, t0, bar, BASS_WALK[bar], 74)
        _drums(sc, t0, bar, 2, fill=(bar == 12))
        _pad(sc, t0, bar, HARM, 52, 92)


def _b_organ(sc):
    t0 = CHORUS[3]
    ramp = [0, 0, 1, 2, 3, 4, 6, 6, 7, 7, 4, 2]
    _line(sc, ORGL, t0, ORG_SOLO, 84, 72, "organ", ramp=ramp)
    for bar, sax, tpt in HORN_RIFF:
        v = 52 + 3 * (bar - 5)
        riff = [(bar, 6, 1), (bar, 8, 3)]
        if bar == 8:                # Gb9 in the second half
            sax, tpt = "E4", "Ab4"
        _line(sc, SAX, t0, [(b, p, d, sax) for b, p, d in riff], v, 62,
              "wind")
        _line(sc, TPT, t0, [(b, p, d, tpt) for b, p, d in riff], v, 66,
              "wind")
    for bar in range(1, 13):
        _comp(sc, t0, bar, HARM, "B" if bar % 2 else "A", 60)
        _stabs(sc, t0, bar, HARM, 56)
        _bass(sc, t0, bar, BASS_WALK[bar], 78)
        _drums(sc, t0, bar, 3, fill=(bar in (4, 8, 12)),
               crash=(88 if bar == 1 else 0))
        _pad(sc, t0, bar, HARM, 50, 84)


def _b_everyone(sc):
    t0 = CHORUS[4]
    _horn_expr_reset(sc, t0)
    ramp = [0, 0, 1, 1, 2, 2, 3, 3, 5, 4, 0, -6]
    _line(sc, SAX, t0, HEAD + HEAD_B + HEAD_END, 84, 67, "wind", ramp=ramp)
    _line(sc, TPT, t0, TPT_COUNTER, 78, 70, "wind", ramp=ramp)
    _line(sc, VIB, t0, VIB_FILLS, 72, 74, "plain")
    # the organ's top line lifts the last four bars; the guitar answers
    _line(sc, ORGL, t0, [(9, 0, 11, "C6"), (10, 0, 11, "Bb5")], 82, 80,
          "organ")
    _line(sc, GTRL, t0, [(12, 6, 1, "C5"), (12, 7, 1, "Eb5"),
                         (12, 8, 1, "F5"), (12, 9, 3, "Ab5", "v")],
          78, 72, "pluck")
    walk = _walk_skips(BASS_WALK, (2, 6, 10))
    walk[12] = [(0, 3, 41), (3, 3, 45), (6, 3, 48), (9, 3, 40)]
    for bar in range(1, 13):
        loud = bar <= 10
        _comp(sc, t0, bar, HARM, "trip" if loud else "A", 58 if loud else 54)
        _stabs(sc, t0, bar, HARM, 62 if loud else 52)
        _bass(sc, t0, bar, walk[bar], 84 if loud else 74)
        _drums(sc, t0, bar, 4 if loud else 2, fill=(bar in (4, 8)),
               crash=(98 if bar in (1, 9) else 0))
        _pad(sc, t0, bar, HARM, 60, 118 if loud else 96)
    en.leslie(sc, ORG, _bt(t0, 9, 0), _bt(t0, 10, 6), 18, 110)
    en.leslie(sc, ORG, _bt(t0, 11, 0), _bt(t0, 12, 0), 110, 18)


def _b_tag(sc):
    t0 = TAG
    _horn_expr_reset(sc, t0)
    # "one more time": the head's last answer, quieter
    _line(sc, SAX, t0, [(b - 8, p, d, nm) for b, p, d, nm in HEAD_B],
          66, 67, "wind")
    _line(sc, SAX, t0, [(3, 0, 5, "D4"), (3, 6, 5, "Bb4"),
                        (4, 0, 5, "G4"), (4, 6, 3, "A4"), (4, 9, 3, "Eb5"),
                        (5, 0, 6, "D5"), (5, 6, 6, "Bb4")], 62, 67, "wind")
    _line(sc, TPT, t0, [(5, 0, 6, "F4"), (5, 6, 6, "G4")], 58, 66, "wind")
    _line(sc, VIB, t0, [(3, 2, 1, "F5"), (3, 3, 1, "G5"), (3, 4, 2, "Bb5"),
                        (4, 2, 1, "Eb5"), (4, 3, 1, "D5"), (4, 4, 2, "G5")],
          58, 76, "plain")
    walk = {1: [(0, 3, 41), (3, 3, 45), (6, 3, 48), (9, 3, 52)],
            2: [(0, 3, 51), (3, 3, 49), (6, 3, 46), (9, 3, 45)],
            3: [(0, 5, 46), (6, 4, 43), (11, 1, 37)],
            4: [(0, 5, 36), (6, 5, 41)],
            5: [(0, 5, 34), (6, 5, 34)]}
    for bar in range(1, 6):
        _comp(sc, t0, bar, HARM_TAG, "A", 52 - 2 * bar)
        _bass(sc, t0, bar, walk[bar], 70 - 2 * bar)
        _pad(sc, t0, bar, HARM_TAG, 50, 96 - 4 * bar)
        if bar <= 2:
            _stabs(sc, t0, bar, HARM_TAG, 48)
            _drums(sc, t0, bar, 2)
        elif bar <= 4:
            _drums(sc, t0, bar, 1)
        else:
            for pos in (0, 3, 6, 9):
                sc.note(DR, 51, _bt(t0, bar, pos), 0.25, 60, jt=0, jv=2)
    # the BEAM, one note to the pulse, climbing into the last chord
    t5 = _bt(t0, 5, 0)
    for i, name in enumerate(BEAM_HIGH[:4]):
        sc.note(VIB, en.n(name), t5 + 1.5 * i, 1.4, 64 + 2 * i, jt=0, jv=1)
    # the last chord: B-flat 6/9, everyone, and the lamp
    t6 = _bt(t0, 6, 0)
    ring = END - t6
    sc.note(VIB, en.n(BEAM_HIGH[4]), t6, ring, 72, jt=0, jv=1)
    sc.note(BASS, 34, t6, ring, 74, jt=0, jv=2)
    for p in (46, 53, 58, 62, 67, 72):
        sc.note(RH, p, t6, ring, 54, jt=0, jv=2)
    for p in (50, 55, 60, 65):
        sc.note(GTR, p, t6, ring, 52, jt=0, jv=2)
    for p in ORGV["Bb69"]:
        sc.note(ORG, p, t6, ring, 50, jt=0, jv=2)
    sc.note(SAX, en.n("C5"), t6, ring, 62, jt=0, jv=2)
    sc.note(TPT, en.n("G4"), t6, ring, 56, jt=0, jv=2)
    sc.note(LAMP, material.LAMP_PITCH, t6, ring, 66, jt=0, jv=0)
    for i, name in enumerate(["D5", "F5", "G5", "C6", "D6"]):
        t = t6 + (i + 1) * E
        sc.note(RHL, en.n(name), t, END - t, 50 + 2 * i, jt=0, jv=1)
    sc.note(DR, 51, t6, 0.25, 66, jt=0, jv=2)
    sc.note(DR, 36, t6, 0.25, 44, jt=0, jv=2)
    for ch, top in ((SAX, 104), (TPT, 100)):
        en.expr_curve(sc, ch, [(t6, 84), (t6 + 2.0, top), (END, 46)],
                      step=0.25)
        en.cc_curve(sc, ch, 1, [(t6, 0), (t6 + 2.0, 40), (END, 10)],
                    step=0.5)
    en.expr_curve(sc, ORG, [(t6, 70), (t6 + 2.5, 92), (END, 44)], step=0.25)


BUILDERS = [_b_intro, _b_head, _b_trumpet, _b_stop, _b_organ, _b_everyone,
            _b_tag]

# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

PITCHED = [RH, SAX, ORG, BASS, GTR, TPT, VIB, ORGL, GTRL, LAMP, RHL]
LEADS = [SAX, TPT, GTRL, ORGL]          # choruses 1-4
LEAD_LANES = [SAX, TPT, VIB, ORGL, GTRL, RHL]
RHYTHM = [RH, ORG, BASS, GTR, DR]
STOP_CHORUS = 2                          # index into CHORUS
STOP_BARS = range(0, 8)
INSTRUMENTS = [("Rhodes", (RH, RHL)), ("tenor sax", (SAX,)),
               ("organ", (ORG, ORGL)), ("bass", (BASS,)),
               ("guitar", (GTR, GTRL)), ("trumpet", (TPT,)),
               ("vibraphone", (VIB,)), ("brushes", (DR,))]
BLUE = {"b3": 1, "b5": 4, "b7": 8}       # Db, E, Ab
SIXTH_PC = 7                              # G


def _ons_in(ons, t0, t1):
    return [(b, p, v) for b, p, v in ons if t0 - 1e-6 <= b < t1 - 1e-6]


def _o_form(sc, spans, ons):
    """Twelve-bar form: on every bar line of every chorus the bass strikes
    the root the form names, and nothing sounds below it."""
    fails = []
    for k, c0 in enumerate(CHORUS):
        for b in range(12):
            t = c0 + BAR * b
            here = [p for bt, p, _v in ons[BASS] if abs(bt - t) < 1e-6]
            tag = f"chorus {k + 1} bar {b + 1}"
            if len(here) != 1:
                fails.append(f"{tag}: {len(here)} bass onsets on the bar "
                             f"line, want exactly 1")
                continue
            if here[0] % 12 != ROOT_PC[b]:
                fails.append(f"{tag}: bass pitch {here[0]} is not the "
                             f"root {FORM_ROOTS[b]}")
            below = [p for ch in PITCHED if ch != BASS
                     for on, off, p, _v in spans[ch]
                     if on <= t + 1e-9 and off >= t + 0.05 and p <= here[0]]
            if below:
                fails.append(f"{tag}: pitch {min(below)} sounds at or "
                             f"under the bass root {here[0]}")
    return fails


def _o_lattice(sc):
    """Everything sits on the triplet lattice (tick-exact), and it is a
    real 12/8: plenty of onsets on the off-pulse triplets."""
    fails = []
    total = off_pulse = 0
    for ch in sorted(sc.events):
        for tick, _prio, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0x90 and data[2] > 0:
                total += 1
                if tick % LATTICE_TICKS:
                    fails.append(f"ch{ch} onset at beat {tick / en.PPQ:.3f} "
                                 f"is off the triplet lattice")
                elif (tick // LATTICE_TICKS) % 3:
                    off_pulse += 1
    if total and off_pulse < 0.3 * total:
        fails.append(f"only {off_pulse}/{total} onsets fall on off-pulse "
                     f"triplets; a 12/8 blues needs >= 30%")
    return fails[:8]


def _mass(ons, ch, t0, t1):
    return sum(v for _b, _p, v in _ons_in(ons[ch], t0, t1))


def _o_soloists(sc, ons):
    """Each of the first four choruses is led by a different soloist; the
    last has every instrument playing."""
    fails = []
    if len(set(LEADS)) != len(LEADS):
        fails.append("the soloists are not all different")
    for k, lead in enumerate(LEADS):
        c0 = CHORUS[k]
        mine = _mass(ons, lead, c0, c0 + 72)
        count = len(_ons_in(ons[lead], c0, c0 + 72))
        if count < 40:
            fails.append(f"chorus {k + 1}: soloist ch{lead} plays only "
                         f"{count} notes")
        for ch in LEAD_LANES:
            if ch != lead and _mass(ons, ch, c0, c0 + 72) * 1.5 > mine:
                fails.append(f"chorus {k + 1}: ch{ch} rivals the soloist "
                             f"ch{lead}")
    c0 = CHORUS[4]
    for name, chans in INSTRUMENTS:
        n = sum(len(_ons_in(ons[ch], c0, c0 + 72)) for ch in chans)
        if n < 6:
            fails.append(f"last chorus: {name} plays only {n} notes")
    return fails


def _o_stop_time(sc, ons):
    """Exactly one stop-time chorus: for eight bars the rhythm section
    plays ONLY the hit on each bar line while the guitar fills the breaks;
    then time returns.  Every other chorus keeps time in every bar."""
    fails = []
    c0 = CHORUS[STOP_CHORUS]
    for b in STOP_BARS:
        t = c0 + BAR * b
        for ch in RHYTHM:
            stray = [bt for bt, _p, _v in _ons_in(ons[ch], t, t + BAR)
                     if abs(bt - t) > 1e-6]
            if stray:
                fails.append(f"stop bar {b + 1}: ch{ch} plays inside the "
                             f"break at beat {stray[0]:.2f}")
        for ch in (RH, BASS, DR):
            if not any(abs(bt - t) < 1e-6 for bt, _p, _v in ons[ch]):
                fails.append(f"stop bar {b + 1}: ch{ch} misses the hit")
        fill = [bt for bt, _p, _v in _ons_in(ons[GTRL], t, t + BAR)
                if bt > t + 1e-6]
        if len(fill) < 4:
            fails.append(f"stop bar {b + 1}: the guitar plays only "
                         f"{len(fill)} notes in the break")
    for k, k0 in enumerate(CHORUS):
        for b in range(12):
            if k == STOP_CHORUS and b in STOP_BARS:
                continue
            t = k0 + BAR * b
            if len(_ons_in(ons[BASS], t, t + BAR)) < 3:
                fails.append(f"chorus {k + 1} bar {b + 1}: the bass stops "
                             f"walking outside the stop-time bars")
            if len(_ons_in(ons[DR], t, t + BAR)) < 8:
                fails.append(f"chorus {k + 1} bar {b + 1}: the brushes "
                             f"drop the time")
    return fails[:8]


def _o_blue(sc, ons):
    """Every solo leans on the blue notes (b3, b5, b7) and on the major
    sixth the BEAM brings."""
    fails = []
    for k, lead in enumerate(LEADS):
        c0 = CHORUS[k]
        pcs = [p % 12 for _b, p, _v in _ons_in(ons[lead], c0, c0 + 72)]
        for name, pc in sorted(BLUE.items()):
            if pcs.count(pc) < 1:
                fails.append(f"chorus {k + 1}: the solo never plays the "
                             f"{name}")
        blue = sum(pcs.count(pc) for pc in BLUE.values())
        if blue < 0.15 * max(1, len(pcs)):
            fails.append(f"chorus {k + 1}: only {blue}/{len(pcs)} solo "
                         f"notes are blue notes")
        if pcs.count(SIXTH_PC) < 3:
            fails.append(f"chorus {k + 1}: the major sixth is missing "
                         f"from the solo")
    return fails


def _o_turnaround(sc, ons):
    """The BEAM is the turnaround lick: it starts on the B-flat of bar 11
    in every chorus, in that chorus's solo voice (sax AND trumpet in the
    last); the Rhodes plants it in the intro and the vibes close on it."""
    fails = []
    beams = {ch: material.beam_statements(sc, ch) for ch in BEAM_CHANNELS}
    for k, c0 in enumerate(CHORUS):
        t = c0 + BAR * 10
        for ch in ([LEADS[k]] if k < len(LEADS) else [SAX, TPT]):
            if not any(abs(b - t) < 1e-6 for b in beams[ch]):
                fails.append(f"chorus {k + 1}: no BEAM on ch{ch} at "
                             f"bar 11 (beat {t:.0f})")
                continue
            first = [p for b, p, _v in ons[ch] if abs(b - t) < 1e-6]
            if first[0] % 12 != ROOT_PC[10]:
                fails.append(f"chorus {k + 1}: the lick starts on pitch "
                             f"{first[0]}, not B-flat")
    if not any(INTRO <= b < CHORUS[0] for b in beams[RHL]):
        fails.append("no BEAM on the Rhodes in the intro")
    if not any(TAG <= b < END for b in beams[VIB]):
        fails.append("no BEAM on the vibes in the tag")
    return fails


def _o_arc(sc, ons):
    """The dynamic arc: intro < head < trumpet; the organ chorus above the
    trumpet; the last chorus the peak; the stops strip the rhythm section
    to under 60% of any other chorus; the tag sinks below the head; nothing above the
    ceiling - a quiet record."""
    fails = []
    e_intro = material.energy(sc, INTRO, CHORUS[0])
    e = [material.energy(sc, c, c + 72) for c in CHORUS]
    e_tag = material.energy(sc, TAG + 4 * BAR, END)
    if not e_intro < e[0] < e[1]:
        fails.append(f"no rise intro {e_intro:.0f} < head {e[0]:.0f} < "
                     f"trumpet {e[1]:.0f}")
    if not e[3] > 1.1 * e[1]:
        fails.append(f"organ chorus {e[3]:.0f} not above trumpet "
                     f"{e[1]:.0f} x1.1")
    if not e[4] >= 1.25 * max(e[:4]):
        fails.append(f"last chorus {e[4]:.0f} is not the peak "
                     f"(others max {max(e[:4]):.0f}, need x1.25)")
    if not e_tag < e[0]:
        fails.append(f"tag end {e_tag:.0f} does not sink below the head "
                     f"{e[0]:.0f}")
    stop = material.energy(sc, CHORUS[STOP_CHORUS],
                           CHORUS[STOP_CHORUS] + 8 * BAR, RHYTHM)
    for k, c0 in enumerate(CHORUS):
        if k == STOP_CHORUS:
            continue
        other = material.energy(sc, c0, c0 + 8 * BAR, RHYTHM)
        if not stop < 0.6 * other:
            fails.append(f"stop-time rhythm energy {stop:.0f} is not under "
                         f"60% of chorus {k + 1}'s {other:.0f}")
    loud = [(ch, b, v) for ch in sorted(ons) for b, _p, v in ons[ch]
            if v > VEL_CEILING]
    if loud:
        fails.append(f"{len(loud)} notes above velocity {VEL_CEILING}, "
                     f"first ch{loud[0][0]} at beat {loud[0][1]:.1f}")
    return fails


def _o_horns(sc, spans):
    """Counter-melody: in the last chorus the trumpet is consonant with
    the sax on every strong pulse (bar line and half bar) they share, and
    it is a real second line, not a doubling."""
    fails = []
    c0 = CHORUS[4]

    def snd(ch, t):
        return [p for on, off, p, _v in spans[ch]
                if on <= t + 1e-9 and off >= t + 0.05]

    shared = 0
    unison = 0
    for b in range(12):
        for half in (0.0, 3.0):
            t = c0 + BAR * b + half
            s, p = snd(SAX, t), snd(TPT, t)
            if not (s and p):
                continue
            shared += 1
            iv = abs(p[0] - s[0]) % 12
            if iv not in material.CONSONANT:
                fails.append(f"bar {b + 1} beat {half:.0f}: sax {s[0]} vs "
                             f"trumpet {p[0]} (interval class {iv})")
            if iv == 0:
                unison += 1
    if shared < 14:
        fails.append(f"horns share only {shared} strong pulses, want >= 14")
    if unison > 3:
        fails.append(f"{unison} unison/octave pulses: the trumpet is "
                     f"doubling, not answering")
    return fails


def _o_ending(sc, spans, ons):
    """The tag ends on a rich B-flat chord: at least five pitch classes
    including Bb D F G C, the bass B-flat underneath, every instrument in
    it, all ringing to the end - and the lamp tolls exactly once, there."""
    fails = []
    t = END - 0.25
    held = [(ch, p, off) for ch in PITCHED for on, off, p, _v in spans[ch]
            if on <= t and off >= t]
    pcs = {p % 12 for _ch, p, _off in held}
    need = {10, 2, 5, 7, 0}
    if not need <= pcs:
        fails.append(f"final chord pitch classes {sorted(pcs)} lack "
                     f"{sorted(need - pcs)}")
    if pcs - need:
        fails.append(f"final chord has stray pitch classes "
                     f"{sorted(pcs - need)}")
    if held:
        low = min(held, key=lambda h: h[1])
        if low[0] != BASS or low[1] % 12 != 10:
            fails.append(f"lowest final note is ch{low[0]} pitch {low[1]}, "
                         f"not the bass B-flat")
    for ch in (RH, SAX, ORG, BASS, GTR, TPT, VIB, LAMP, RHL):
        if not any(c == ch for c, _p, _off in held):
            fails.append(f"ch{ch} is missing from the final chord")
    early = [(ch, p) for ch, p, off in held if off < END - 0.05]
    if early:
        fails.append(f"final notes released early: {early[:4]}")
    lamp = ons[LAMP]
    if len(lamp) != 1 or lamp[0][1] != material.LAMP_PITCH \
            or lamp[0][0] < TAG:
        fails.append(f"the lamp must toll exactly once, on D4, in the "
                     f"tag: {lamp}")
    return fails


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    ons = {ch: material.note_ons(sc, ch) for ch in sorted(sc.events)}
    nspans = {ch: material.note_spans(sc, ch) for ch in sorted(sc.events)}
    results.append(("t09_twelve_bar_form", _o_form(sc, nspans, ons)))
    results.append(("t09_triplet_lattice", _o_lattice(sc)))
    results.append(("t09_soloist_per_chorus", _o_soloists(sc, ons)))
    results.append(("t09_stop_time_chorus", _o_stop_time(sc, ons)))
    results.append(("t09_blue_notes", _o_blue(sc, ons)))
    results.append(("t09_beam_turnaround", _o_turnaround(sc, ons)))
    results.append(("t09_dynamic_arc", _o_arc(sc, ons)))
    results.append(("t09_horn_counterpoint", _o_horns(sc, nspans)))
    results.append(("t09_rich_final_chord", _o_ending(sc, nspans, ons)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def _db(ctx, b0, b1):
    i0, i1 = ctx.bar_window(b0, b1)
    return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))


def audio_checks(ctx):
    intro = _db(ctx, INTRO + 1.0, INTRO + 11.0)        # Rhodes alone
    head = _db(ctx, CHORUS[0] + 6.0, CHORUS[0] + 66.0)
    trumpet = _db(ctx, CHORUS[1] + 6.0, CHORUS[1] + 66.0)
    organ = _db(ctx, CHORUS[3] + 6.0, CHORUS[3] + 66.0)
    peak = _db(ctx, CHORUS[4] + 6.0, CHORUS[4] + 60.0)
    last = _db(ctx, END - 4.0, END - 0.5)
    out = []
    fails = []
    if peak - intro < 6.0:
        fails.append(f"peak {peak:.1f} dB is not 6 dB above the intro "
                     f"hush {intro:.1f} dB")
    out.append(("t09_hush_vs_peak", fails))
    fails = []
    for name, val in (("head", head), ("trumpet", trumpet),
                      ("organ", organ)):
        if peak < val + 1.0:
            fails.append(f"last chorus {peak:.1f} dB is not above the "
                         f"{name} chorus {val:.1f} dB")
    out.append(("t09_last_chorus_is_peak", fails))
    fails = []
    if last < -60.0:
        fails.append(f"final chord has died ({last:.1f} dB) before the end")
    if last > peak - 6.0:
        fails.append(f"final chord {last:.1f} dB does not sink 6 dB under "
                     f"the peak {peak:.1f} dB")
    out.append(("t09_ending_rings_soft", fails))
    return out
