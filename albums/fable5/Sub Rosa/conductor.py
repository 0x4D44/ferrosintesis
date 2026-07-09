"""conductor.py — the global skeleton of *Sub Rosa* (one track).

An Enigma-inspired instrumental: plainsong over a fast programmed
groove, a melodic synth-bass hook, a bamboo flute that answers the
choir, and a whispered Latin text in the lyric lane.  D aeolian, 124
bpm held machine-steady until the closing ritardando — the pulse is
the incense burner; everything else swings from it.

Movement grid (beats; 124 bpm => a beat is ~0.484 s):

    Sigillum            0 - 64     the seal: drone, first hum, heartbeat
    The Chant          64 - 256    the groove ignites; the chant arrives
    The Bamboo Voice  256 - 448    shakuhachi call-and-response; bass drives
    Sub Rosa          448 - 576    breakdown: whispers, glide solo, morse
    Limina            576 - 832    the widescreen restatement (new ground)
    Afterglow         832 - 928    dissolve; the chant finally cadences

Channel map (pans follow the mono-collapse lesson: sustained beds sit
at/near centre, width comes from transient sources):
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_PIANO = 0     # sparse motif; M4 pooled arpeggios (CC64/66/67)
CH_PAD = 1       # the bed: aftertouch blooms, CC74 close in M6
CH_ARP = 2       # the sequencer: 16th ladder, CC74+CC71 sweeps, autopan
CH_BASS = 3      # THE hook: melodic synth bass, portamento slides, CC68 runs
CH_SHAKU = 4     # shakuhachi: scoops, bends, CC1 vibrato, echo throws
CH_STRINGS = 5   # guide-tone lines, M4 swell, M5 countermelody
CH_CHOIR1 = 6    # the chant: CC70 vowel morphs, aftertouch swells
CH_CHOIR2 = 7    # response / descant; RPN fine-tune beating in M4
CH_CRYSTAL = 8   # glass droplets, echo throws
CH_DRUMS = 9     # GM percussion
CH_GUITAR = 10   # wah skanks (CC74 LFO); palm-mute chug in M5
CH_LEAD = 11     # M4 glide solo: portamento + RPN bend range 12
CH_DRONE = 12    # low drawbar-organ drone; Leslie spin-up in M5 (CC1)
CH_WHISPER = 13  # breath layer (synth voice), carries the whispers
CH_BELL = 14     # tubular bell tolls at the seams
CH_MBOX = 15     # music box glitter (high, wide, transient)

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

MOVEMENTS: list[tuple[str, float, float]] = [
    ("Sigillum",           0.0,  64.0),
    ("The Chant",         64.0, 256.0),
    ("The Bamboo Voice", 256.0, 448.0),
    ("Sub Rosa",         448.0, 576.0),
    ("Limina",           576.0, 832.0),
    ("Afterglow",        832.0, 928.0),
]
END_BEAT = MOVEMENTS[-1][2]

TEMPO_MAP: list[tuple[float, float]] = [
    (0.0, 124.0),
    (880.0, 118.0), (896.0, 108.0), (908.0, 94.0), (918.0, 78.0),
]

TIME_SIGNATURES: list[tuple[float, int, int]] = [(0.0, 4, 4)]

KEYSIGS: list[tuple[float, int, int]] = [(0.0, -1, 1)]      # D minor

# (ch, name, program, volume, pan, reverb)
CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_PIANO,   "Grand Piano",     0,  95, 54, 60),
    (CH_PAD,     "Warm Pad",       89,  82, 64, 82),
    (CH_ARP,     "Sequencer",      81,  76, 76, 62),
    (CH_BASS,    "Synth Bass",     38, 110, 64, 15),
    (CH_SHAKU,   "Shakuhachi",     77, 100, 58, 78),
    (CH_STRINGS, "Strings",        48,  80, 70, 75),
    (CH_CHOIR1,  "Choir I",        52,  95, 64, 85),
    (CH_CHOIR2,  "Choir II",       52,  84, 56, 85),
    (CH_CRYSTAL, "Crystal",        98,  78, 86, 80),
    (CH_DRUMS,   "Drums",           0, 105, 64, 30),
    (CH_GUITAR,  "Wah Guitar",     27,  84, 40, 45),
    (CH_LEAD,    "Glide Lead",     81,  96, 64, 62),
    (CH_DRONE,   "Drawbar Organ",  16,  72, 64, 70),
    (CH_WHISPER, "Breath",         54,  76, 74, 88),
    (CH_BELL,    "Tubular Bell",   14,  88, 60, 82),
    (CH_MBOX,    "Music Box",      10,  80, 88, 70),
]

# (ch, beat, program)
PROGRAM_CHANGES: list[tuple[int, float, int]] = [
    (CH_GUITAR, 576.0, 28),     # clean -> palm-mute chug for the climax
    (CH_GUITAR, 832.0, 27),     # back to clean for the afterglow
]


def setup(sc: en.Score) -> None:
    """Write the conductor lane and all channel setups into `sc`."""
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
