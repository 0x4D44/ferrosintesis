"""conductor.py — the global skeleton of *The Burning Meridian*.

Three orchestral film-epic instrumentals.  The "brass" is a BUILT
section — rock organ + saw stack in octaves, fattened by a +6-cent
fine-tune spread — because hollowsynth models no brass; everything
else is the string/choir/wind/bell orchestra the synth does model.
One HORN THEME binds tracks 1 and 3 (material.py proves it fits both
grounds); track 2 quotes nothing and mourns in 3/4.

01 The Muster (D aeolian, 132):
    Embers          0 -  32   4/4   pedal D, tolling piano, choir mm
    The Ostinato   32 - 176   12/8  the engine builds, taiko layers
    The Call      176 - 356   12/8  the horn theme, thrice, + descant
    Over the Hill 356 - 428   4/4   drop; solo fiddle echo; last hit

02 Lanterns on the Water (A aeolian, 88, 3/4 throughout):
    Lanterns        0 -  36   harp arpeggios, strings gather
    Duet           36 - 132   the fiddle/flute elegy (verified pair)
    Swell         132 - 216   tutti takes the duet; bell; timpani
    Ashfall       216 - 288   rit; lanterns go out one by one

03 Meridian (D aeolian -> D MAJOR, 138):
    War Footing     0 -  60   5/4   ost_54, taiko, stab hits
    Cavalry        60 - 160   5/4   horn theme stretched to the meter
    The Break     160 - 200   4/4   half-time; the elegy remembered
    Charge        200 - 340   5/4   theme + descant stacked; barrage
    Daybreak      340 - 416   4/4   THE TURN TO MAJOR; bells; rit out
"""

from __future__ import annotations

import engine as en

CH_PIANO = 0     # tolling low octaves; track-2 pools
CH_PAD = 1       # warm pad: the hall's air
CH_HARP = 2      # harp: track 2's water; arpeggio flourishes
CH_BASSSTR = 3   # low strings: THE ostinato engine
CH_FIDDLE = 4    # solo violin: elegy voice A, echoes
CH_STRINGS = 5   # string section
CH_CHOIR1 = 6    # choir: mm in the shadows, ah at the summits
CH_CHOIR2 = 7    # choir II: descant / low hum
CH_GLOCK = 8     # glockenspiel sparkle
CH_DRUMS = 9     # taiko toms, snares, cymbals
CH_HORN1 = 10    # the built horns, organ half (18)
CH_HORN2 = 11    # the built horns, saw half (84), +6c spread
CH_TIMP = 12     # timpani (47): pitched thunder
CH_FLUTE = 13    # flute: elegy voice B, daylight
CH_CELLO = 14    # cello: counter-lines, portamento slides
CH_BELL = 15     # tubular bells: the turn to major


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
    (CH_PIANO,   "Grand Piano",     0,  92, 50, 62),
    (CH_PAD,     "Warm Pad",       89,  74, 64, 82),
    (CH_HARP,    "Harp",           46,  86, 78, 66),
    (CH_BASSSTR, "Low Strings",    48, 102, 58, 55),
    (CH_FIDDLE,  "Solo Violin",    40,  96, 56, 68),
    (CH_STRINGS, "Strings",        48,  88, 70, 72),
    (CH_CHOIR1,  "Choir I",        52,  92, 64, 82),
    (CH_CHOIR2,  "Choir II",       52,  82, 56, 82),
    (CH_GLOCK,   "Glockenspiel",    9,  76, 86, 66),
    (CH_DRUMS,   "Percussion",      0, 106, 64, 35),
    (CH_HORN1,   "Horns (organ)",  18,  88, 60, 58),
    (CH_HORN2,   "Horns (synth)",  84,  78, 68, 58),
    (CH_TIMP,    "Timpani",        47,  98, 54, 55),
    (CH_FLUTE,   "Flute",          73,  86, 68, 72),
    (CH_CELLO,   "Cello",          42,  90, 48, 62),
    (CH_BELL,    "Tubular Bells",  14,  90, 60, 82),
]

TRACK1 = Part(
    1, "The Muster", "01 - The Muster.mid",
    movements=[
        ("Embers",         0.0,  32.0),
        ("The Ostinato",  32.0, 176.0),
        ("The Call",     176.0, 356.0),
        ("Over the Hill", 356.0, 428.0),
    ],
    tempo_map=[(0.0, 132.0), (404.0, 120.0), (416.0, 100.0)],
    time_signatures=[(0.0, 4, 4), (32.0, 12, 8), (356.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=_CHANNELS,
    program_changes=[],
)

TRACK2 = Part(
    2, "Lanterns on the Water", "02 - Lanterns on the Water.mid",
    movements=[
        ("Lanterns",   0.0,  36.0),
        ("Duet",      36.0, 132.0),
        ("Swell",    132.0, 216.0),
        ("Ashfall",  216.0, 288.0),
    ],
    tempo_map=[(0.0, 88.0), (264.0, 80.0), (276.0, 68.0)],
    time_signatures=[(0.0, 3, 4)],
    keysigs=[(0.0, 0, 1)],                          # A minor
    channels=_CHANNELS,
    program_changes=[],
)

TRACK3 = Part(
    3, "Meridian", "03 - Meridian.mid",
    movements=[
        ("War Footing",   0.0,  60.0),
        ("Cavalry",      60.0, 160.0),
        ("The Break",   160.0, 200.0),
        ("Charge",      200.0, 340.0),
        ("Daybreak",    340.0, 416.0),
    ],
    tempo_map=[(0.0, 138.0), (368.0, 126.0), (392.0, 108.0),
               (404.0, 92.0)],
    time_signatures=[(0.0, 5, 4), (160.0, 4, 4), (200.0, 5, 4),
                     (340.0, 4, 4)],
    keysigs=[(0.0, -1, 1), (340.0, 2, 0)],          # d minor -> D MAJOR
    channels=_CHANNELS,
    program_changes=[],
)

PARTS = [TRACK1, TRACK2, TRACK3]
