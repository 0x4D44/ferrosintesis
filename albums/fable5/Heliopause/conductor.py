"""conductor.py — the global skeleton of *Heliopause* (two tracks).

Synth-based instrumentals in the Jean-Michel Jarre / Oxygène idiom:
sequencer cells with filters in constant motion, slow warm harmony
under fast surfaces, portamento leads, wind transitions, sudden drops.
A aeolian throughout; one melodic idea shared between the parts (Part
Two's lead is Part One's theme inverted — see material.py).

Part One "Heliopause, Part One" (~4:55, 116 bpm):
    Solar Wind      0 -  48   4/4  drift-in: pads, wind, heartbeat
    The Sequencer  48 - 192   4/4  the cell arrives; THEME_A on glide
    Mirror Waltz  192 - 264   3/4  the waltz episode; THEME_B sung
    The Drop      264 - 344   4/4  everything cut; the theremin sings
    Two Suns      344 - 488   4/4  A + B together over GROUND_LIFT
    Dissolve      488 - 552   4/4  rit; the filter closes

Part Two "Heliopause, Part Two" (~3:50, 126 bpm):
    Ignition        0 -  36   4/4  riser; arps immediate
    Slipstream     36 - 180   6/8  shuffle cell; THEME_A_INV over a pedal
    Crosswind     180 - 228   4/4  the stomp
    Eclipse       228 - 276   6/8  drop: choir + glide lead recalls A
    Perihelion    276 - 404   4/4  TRIPLE stack: A + B + A_INV
    Afterimage    404 - 460   4/4  rit; heartbeat out
"""

from __future__ import annotations

import engine as en

CH_EP = 0        # electric piano: waltz comping, glass chords
CH_PAD = 1       # swirl pad (95): the weather
CH_SEQ = 2       # the sequencer (81): CC74/71 always moving, autopan
CH_BASS = 3      # synth bass (39): the melodic pulse
CH_LEAD = 4      # square glide lead (80): the themes, portamento
CH_STRINGS = 5   # slow strings (49): beds
CH_CHOIR = 6     # synth voice (54): airy vowels
CH_THEREMIN = 7  # voice-lead saw (85): RPN-12 bends in The Drop
CH_CRYSTAL = 8   # crystal (98): sparkles, laser accents
CH_DRUMS = 9
CH_SEQ2 = 10     # second sequencer (87): the 12-slot polymeter voice
CH_ORGAN = 11    # drawbars (16): quiet until the Leslie climax
CH_GLOCK = 12    # glockenspiel: theme doubling
CH_NYLON = 13    # nylon guitar: the waltz plucks
CH_FLUTE = 14    # pan flute (75): breathy answers
CH_BELL = 15     # tubular bell: distant tolls


class Part:
    def __init__(self, number, title, file, movements, tempo_map,
                 time_signatures, keysigs, channels, program_changes):
        self.number = number
        self.title = title
        self.file = file
        self.MOVEMENTS = movements
        self.TEMPO_MAP = tempo_map
        self.TIME_SIGNATURES = time_signatures
        self.KEYSIGS = keysigs
        self.CHANNELS = channels
        self.PROGRAM_CHANGES = program_changes
        self.END_BEAT = movements[-1][2]

    def setup(self, sc: en.Score) -> None:
        for beat, bpm in self.TEMPO_MAP:
            sc.tempo(beat, bpm)
        for beat, num, den in self.TIME_SIGNATURES:
            sc.timesig(beat, num, den)
        for beat, sharps, minor in self.KEYSIGS:
            en.keysig(sc, beat, sharps, minor)
        for name, t0, _t1 in self.MOVEMENTS:
            sc.marker(t0, name)
        for ch, name, prog, vol, pan, rev in self.CHANNELS:
            sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
        for ch, beat, prog in self.PROGRAM_CHANGES:
            sc.program(ch, prog, beat)


_CHANNELS = [
    (CH_EP,       "Electric Piano",  4,  86, 52, 62),
    (CH_PAD,      "Swirl Pad",      95,  82, 64, 82),
    (CH_SEQ,      "Sequencer",      81,  84, 74, 55),
    (CH_BASS,     "Synth Bass",     39, 108, 64, 12),
    (CH_LEAD,     "Glide Lead",     80,  98, 60, 62),
    (CH_STRINGS,  "Slow Strings",   49,  76, 70, 75),
    (CH_CHOIR,    "Synth Voice",    54,  82, 64, 85),
    (CH_THEREMIN, "Theremin",       85,  92, 56, 80),
    (CH_CRYSTAL,  "Crystal",        98,  78, 88, 78),
    (CH_DRUMS,    "Drums",           0, 104, 64, 30),
    (CH_SEQ2,     "Sequencer II",   87,  74, 46, 55),
    (CH_ORGAN,    "Drawbar Organ",  16,  70, 64, 65),
    (CH_GLOCK,    "Glockenspiel",    9,  78, 84, 68),
    (CH_NYLON,    "Nylon Guitar",   24,  84, 40, 58),
    (CH_FLUTE,    "Pan Flute",      75,  86, 68, 78),
    (CH_BELL,     "Tubular Bell",   14,  84, 58, 84),
]

PART1 = Part(
    number=1,
    title="Heliopause, Part One",
    file="01 - Heliopause, Part One.mid",
    movements=[
        ("Solar Wind",      0.0,  48.0),
        ("The Sequencer",  48.0, 192.0),
        ("Mirror Waltz",  192.0, 264.0),
        ("The Drop",      264.0, 344.0),
        ("Two Suns",      344.0, 488.0),
        ("Dissolve",      488.0, 552.0),
    ],
    tempo_map=[(0.0, 116.0), (528.0, 108.0), (540.0, 96.0),
               (546.0, 84.0)],
    time_signatures=[(0.0, 4, 4), (192.0, 3, 4), (264.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],                          # A minor
    channels=_CHANNELS,
    program_changes=[],
)

PART2 = Part(
    number=2,
    title="Heliopause, Part Two",
    file="02 - Heliopause, Part Two.mid",
    movements=[
        ("Ignition",     0.0,  36.0),
        ("Slipstream",  36.0, 180.0),
        ("Crosswind",  180.0, 228.0),
        ("Eclipse",    228.0, 276.0),
        ("Perihelion", 276.0, 404.0),
        ("Afterimage", 404.0, 460.0),
    ],
    tempo_map=[(0.0, 126.0), (404.0, 120.0), (428.0, 104.0),
               (444.0, 88.0)],
    time_signatures=[(0.0, 4, 4), (36.0, 6, 8), (180.0, 4, 4),
                     (228.0, 6, 8), (276.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],
    channels=_CHANNELS,
    program_changes=[],
)

PARTS = [PART1, PART2]
