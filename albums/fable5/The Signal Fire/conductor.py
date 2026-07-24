"""conductor.py — the global skeleton of *The Signal Fire*.

Implements roadmap sections 1 (global grid) and 2 (channel map) of
"2026.07.06 - HLD - The Signal Fire composition roadmap" EXACTLY, as data,
plus one function `setup(sc)` that writes it all into a Score:

  * the full tempo map — the M1 ignition spin-up (drift 74/76 at 152/160,
    spin-up 80/88 at 168/172), the M4 accelerando (+2 bpm every 32 beats
    from 800, holding 112 from 1120) and the M6 ritardando steps;
  * the time-signature events (4/4 at 0, 10/8 at 480, 4/4 at 800);
  * the six movement markers (exact roadmap titles);
  * all 16 channel setups (names / programs / volumes / pans / reverb);
  * every scheduled mid-piece program change.

Movement writers import the channel constants (CH_LEAD etc.) and MOVEMENTS
from here; they must write notes only inside their [t0, t1) span.
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# Section 1 — the global grid.  Beats are quarter notes, cumulative from 0.
# ---------------------------------------------------------------------------

MOVEMENTS: list[tuple[str, float, float]] = [
    ("Signal",         0.0,  176.0),   # A aeolian -> dorian, 72 drifting
    ("Ignition",     176.0,  480.0),   # A dorian, 100, the funk engine
    ("The Lattice",  480.0,  800.0),   # D dorian, 10/8, 108
    ("The Long Climb", 800.0, 1312.0),  # A dorian, 92 -> 112, THE solo
    ("Ascension",   1312.0, 1592.0),   # A ionian, 112, ff
    ("Afterglow",   1592.0, 1678.0),   # A ionian, rit. 112 -> 66
]
END_BEAT = MOVEMENTS[-1][2]

# Tempo map.  M1 spin-up reconciles the grid table ("drifting 72-76,
# spin-up 80/88 at 168/172") with the movement brief ("72->76->80->88 at
# 152/160/168/172"): the drift supplies 74/76 at 152/160, the spin-up
# 80/88 at 168/172, and M2 lands 100 at 176.
TEMPO_MAP: list[tuple[float, float]] = (
    [
        (0.0, 72.0),
        (152.0, 74.0), (160.0, 76.0),        # M1 drift
        (168.0, 80.0), (172.0, 88.0),        # M1 ignition spin-up
        (176.0, 100.0),                      # M2 Ignition
        (480.0, 108.0),                      # M3 The Lattice
        (800.0, 92.0),                       # M4 The Long Climb
    ]
    # M4 accelerando: +2 bpm every 32 beats, reaching 112 at 1120.
    + [(800.0 + 32.0 * i, 92.0 + 2.0 * i) for i in range(1, 11)]
    + [
        (1312.0, 112.0),                     # M5 Ascension (hold)
        (1592.0, 112.0),                     # M6 ritardando steps
        (1608.0, 96.0), (1628.0, 80.0), (1648.0, 66.0),
    ]
)

TIME_SIGNATURES: list[tuple[float, int, int]] = [
    (0.0, 4, 4), (480.0, 10, 8), (800.0, 4, 4),
]

# ---------------------------------------------------------------------------
# Section 2 — the channel map.  16 channels, rotating roles.
# ---------------------------------------------------------------------------

CH_PIANO = 0     # M1/M6 pedalled pools, M2 comping, M5 glitter
CH_PAD = 1       # M1 filter-opening bed, M4 terraces, M6 bookend
CH_CRYSTAL = 2   # M1 echo sparks, M3 polymeter loop, glock sparkle, M6
CH_BASS = 3      # slides / funk riff / 10/8 riff / ground / augmented
CH_ORGAN = 4     # Hammond stabs (Leslie), flute chorale, sustained power
CH_STRINGS = 5   # M3 pads, M4 terrace, M5 Theme C
CH_CHOIR = 6     # M4 terrace, M5 Theme C octave
CH_STEEL = 7     # M3 lattice L1, M4 ground strums, M6 backing
CH_NYLON = 8     # M2 offbeat comps, M3 lattice L2, M6 Theme A reprise
CH_DRUMS = 9     # GM percussion channel
CH_RHYTHM = 10   # M2 palm-mute chug, M3 lattice L3, M4 chug, M5 figuration
CH_WAH = 11      # M2 wah riffing (CC74 LFO), M4 arps, M5 funk return
CH_LEAD = 12     # THE solo (M4), M5 wails; violining entries
CH_DOUBLE = 13   # M4 unison-bend partner / +6c detune double, M5 harmony
CH_WINDS = 14    # whistle Theme A (M1) / fiddle (M3) / flute (M4) / whistle
CH_BELLS = 15    # M3 tremolo mandolin -> M4/M5 tubular bells

# (ch, name, initial program, volume, pan, reverb).  Pans per the roadmap:
# drums/bass/lead centred; the M3 lattice sits 25/64/103 (ch7/8/10 — ch10 is
# repanned by CC10 per movement: 30 for the M2 antiphonal pair, 103 in M3);
# M2 antiphonal pair ch10=30 / ch11=98; ch13 hard-splits 20/108 from M4-W3
# via CC10; crystal autopans.  Reverb here is the M1 starting point of the
# global CC91 distance arc; movements ride CC91 from there.
CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_PIANO,   "Grand Piano",     0, 100,  54, 60),
    (CH_PAD,     "Sweep Pad",      95,  80,  64, 85),
    (CH_CRYSTAL, "Crystal",        98,  70,  76, 90),
    (CH_BASS,    "Fretless Bass",  35, 105,  64, 25),
    (CH_ORGAN,   "Hammond Organ",  18,  78,  58, 45),
    (CH_STRINGS, "Strings",        48,  80,  60, 75),
    (CH_CHOIR,   "Choir",          52,  80,  68, 80),
    (CH_STEEL,   "Steel Guitar",   25,  90,  25, 55),
    (CH_NYLON,   "Nylon Guitar",   24,  90,  64, 55),
    (CH_DRUMS,   "Drums",           0, 100,  64, 35),
    (CH_RHYTHM,  "Rhythm Guitar",  27,  88,  30, 45),
    (CH_WAH,     "Wah Guitar",     27,  90,  98, 45),
    (CH_LEAD,    "Lead Guitar",    30, 100,  64, 60),
    (CH_DOUBLE,  "Lead Double",    30,  92,  64, 60),
    (CH_WINDS,   "Winds",          78,  85,  70, 80),
    (CH_BELLS,   "Mandolin & Bells", 25, 95, 76, 70),
]

# Every scheduled mid-piece program change: (ch, beat, program).
# Initial programs (beat 0) live in CHANNELS above; roles whose roadmap
# "@beat" program equals the one already sounding need no change event
# (e.g. ch4's "18 rock @176" is the initial program).
PROGRAM_CHANGES: list[tuple[int, float, int]] = [
    (CH_PAD,     176.0, 89),    # sweep -> warm pad for M2-M5
    (CH_PAD,    1592.0, 95),    # back to sweep for the M6 bookend
    (CH_CRYSTAL, 1230.0, 9),    # crystal -> glockenspiel (M4-W5 sparkle)
    (CH_CRYSTAL, 1592.0, 98),   # back to crystal for M6
    (CH_BASS,    176.0, 33),    # fretless -> fingered for the funk engine
    (CH_BASS,   1592.0, 35),    # back to fretless slides in M6
    (CH_ORGAN,   480.0, 16),    # rock organ -> drawbar flutes (M3 chorale)
    (CH_ORGAN,   800.0, 18),    # back to rock organ for M4/M5 power
    (CH_RHYTHM,  240.0, 28),    # clean -> palm-mute chug in M2
    (CH_RHYTHM,  480.0, 27),    # clean lattice line L3 in M3
    (CH_RHYTHM,  800.0, 28),    # palm-mute chug ground in M4
    (CH_RHYTHM, 1312.0, 27),    # open figuration in M5
    (CH_WINDS,   480.0, 40),    # whistle -> fiddle (M3 Theme B)
    (CH_WINDS,   800.0, 73),    # fiddle -> flute (M4 terrace octaves)
    (CH_WINDS,  1592.0, 78),    # back to whistle for the M6 echo
    (CH_BELLS,  1290.0, 14),    # mandolin -> tubular bells for the peal
]

# Bank-select LSB changes: (ch, beat, LSB). ferrosintesis has a real mandolin at
# the XG cell "Steel Guitar (25) + bank LSB 96" — General MIDI has no mandolin
# program at all, which is why this channel used to be a bare steel guitar played
# with 32nd-note repeats to imply the tremolo. Selecting the cell gets the actual
# recorded instrument, and its tremolo strokes are real recorded picks.
#
# The LSB must be back to 0 before the channel becomes tubular bells, or a player
# would look up the undefined cell (14, 96) there.
BANK_CHANGES: list[tuple[int, float, int]] = [
    (CH_BELLS,     0.0, 96),    # XG Mandolin for M3's tremolo
    (CH_BELLS,  1289.0, 0),     # base bank back for the M4/M5 bell peal
]


def setup(sc: en.Score) -> None:
    """Write the conductor lane and all channel setups into `sc`."""
    for beat, bpm in TEMPO_MAP:
        sc.tempo(beat, bpm)
    for beat, num, den in TIME_SIGNATURES:
        sc.timesig(beat, num, den)
    for name, t0, _t1 in MOVEMENTS:
        sc.marker(t0, name)
    for ch, name, prog, vol, pan, rev in CHANNELS:
        sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
    for ch, beat, prog in PROGRAM_CHANGES:
        sc.program(ch, prog, beat)
    for ch, beat, lsb in BANK_CHANGES:
        sc.cc(ch, 32, lsb, beat)
    # `Score.channel` writes each initial Program Change at beat 0, and events at
    # one tick sort program-before-CC, so the beat-0 bank select above lands just
    # AFTER it. ferrosintesis reads the bank at note-on and is correct either way,
    # but a hardware XG player latches the bank at the Program Change — so re-issue
    # the mandolin program once the bank is set, and the file is right on both.
    sc.program(CH_BELLS, 25, 1.0)
