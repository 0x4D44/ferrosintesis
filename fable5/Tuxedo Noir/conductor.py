"""conductor.py — the global skeleton of *Tuxedo Noir* (one track).

A spy-idiom single: swung walking vamp, twang-guitar theme against a
built horn-section stab line (machine-verified counterpoint), a 12/8
velvet middle, a 7/8 chase, and the genre's minor-major-9 chord saved
for the final ring.  E aeolian, swung at 128.

    Cold Open        0 -  16   4/4   vibes shimmer, low piano, rim
    The Vamp        16 -  96   4/4   the walking bass; the theme at 48
    Stabs           96 - 144   4/4   the horn section answers
    Velvet         144 - 204   12/8  flute and sliding fiddle, bongos
    The Chase      204 - 274   7/8   pursuit; palm-mute; solo riffs
    Showdown       274 - 354   4/4   theme + stabs stacked; the dive
    Last Cigarette 354 - 392   4/4   reprise; the min-maj9 ring
"""

from __future__ import annotations

import engine as en

CH_PIANO = 0     # noir comping, low tolls, the final chord
CH_PAD = 1       # tension air
CH_VIBES = 2     # the shimmer
CH_BASS = 3      # flatwound fingered bass: THE vamp
CH_TWANG = 4     # clean electric + echo bus: the theme voice
CH_STRINGS = 5   # slow strings: suspense beds
CH_CHOIR = 6     # sparse "ah" at the summit
CH_ORG = 7       # horn stabs, organ half (18)
CH_SAW = 8       # horn stabs, saw half (84), +5c spread
CH_DRUMS = 9     # swing ride, brushes, bongos, 7/8 drive
CH_COMP = 10     # comping guitar; palm-mute in the chase
CH_SOLO = 11     # overdrive: chase riffs, the showdown dive (RPN 12)
CH_FLUTE = 12    # velvet lead
CH_FIDDLE = 13   # velvet slides (portamento)
CH_CELESTA = 14  # the drips
CH_BELL = 15     # danger tolls

MOVEMENTS = [
    ("Cold Open",        0.0,  16.0),
    ("The Vamp",        16.0,  96.0),
    ("Stabs",           96.0, 144.0),
    ("Velvet",         144.0, 204.0),
    ("The Chase",      204.0, 274.0),
    ("Showdown",       274.0, 354.0),
    ("Last Cigarette", 354.0, 392.0),
]
END_BEAT = MOVEMENTS[-1][2]

TEMPO_MAP = [(0.0, 128.0), (204.0, 132.0), (274.0, 128.0),
             (372.0, 112.0), (382.0, 92.0)]
TIME_SIGNATURES = [(0.0, 4, 4), (144.0, 12, 8), (204.0, 7, 8),
                   (274.0, 4, 4)]
KEYSIGS = [(0.0, 1, 1)]                             # E minor

CHANNELS = [
    (CH_PIANO,   "Grand Piano",    0,  92, 50, 58),
    (CH_PAD,     "Warm Pad",      89,  72, 64, 80),
    (CH_VIBES,   "Vibraphone",    11,  88, 72, 66),
    (CH_BASS,    "Fingered Bass", 33, 110, 64, 15),
    (CH_TWANG,   "Twang Guitar",  27,  98, 56, 58),
    (CH_STRINGS, "Slow Strings",  49,  78, 70, 74),
    (CH_CHOIR,   "Choir",         52,  84, 64, 80),
    (CH_ORG,     "Stabs (organ)", 18,  90, 58, 52),
    (CH_SAW,     "Stabs (saw)",   84,  76, 70, 52),
    (CH_DRUMS,   "Drums",          0, 104, 64, 32),
    (CH_COMP,    "Comp Guitar",   27,  82, 40, 45),
    (CH_SOLO,    "Solo Guitar",   29,  92, 62, 55),
    (CH_FLUTE,   "Flute",         73,  88, 66, 72),
    (CH_FIDDLE,  "Fiddle",        40,  88, 48, 68),
    (CH_CELESTA, "Celesta",        8,  80, 84, 68),
    (CH_BELL,    "Tubular Bell",  14,  86, 60, 80),
]

PROGRAM_CHANGES = [
    (CH_COMP, 204.0, 28),       # palm-mute for the chase
    (CH_COMP, 274.0, 27),
]


def setup(sc: en.Score) -> None:
    for beat, bpm in TEMPO_MAP:
        sc.tempo(beat, bpm)
    for beat, num, den in TIME_SIGNATURES:
        sc.timesig(beat, num, den)
    for beat, sharps, minor in KEYSIGS:
        en.keysig(sc, beat, sharps, minor)
    for name, t0, _t1 in MOVEMENTS:
        sc.marker(t0, name)
    for ch, name, prog, vol, pan, rev in CHANNELS:
        sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
    for ch, beat, prog in PROGRAM_CHANGES:
        sc.program(ch, prog, beat)
