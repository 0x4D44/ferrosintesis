"""conductor.py — the global skeleton of *Winter Guests*, in TWO parts.

Implements roadmap sections 1 (global grids) and 2 (channel map) of
"2026.07.06 - HLD - Winter Guests composition roadmap" EXACTLY, as data.
Each part is a `Part` carrying its movement grid, tempo map, time
signatures, key-signature metas, channel setups (the two parts open with
DIFFERENT programs on several channels) and scheduled program changes,
plus `setup(sc)` that writes it all into a Score.

Movement writers import the shared channel constants (CH_CHOIR1 etc.) and
their part's MOVEMENTS from here; each must write notes only inside its
own [t0, t1) span.
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# Section 2 — the channel roles are shared across both parts.
# ---------------------------------------------------------------------------

CH_PIANO = 0     # M2/M6 una-corda verses, M4 off-beat octave comp, M5 glitter
CH_PAD = 1       # M1 bed (CC74 + aftertouch blooms), M4 breakdown, M6 close
CH_ARP = 2       # THE Visitors sequencer: 16th cells, CC74+CC71 sweeps
CH_BASS = 3      # M1 pedal slides, M3 7/8 cell, M4/M5 pop riffing, M6 slides
CH_ORGAN = 4     # M2 harmonium ground (CC66), M5 full organ (CC1 Leslie)
CH_STRINGS = 5   # M2 bridge, M3 tension pads, M4/M5 lines
CH_CHOIR1 = 6    # THE VOICE: hum guise (CC70=mm), chorus stack top+mid (ah)
CH_STEEL = 7     # M2 fingerpicked ground, M4 backbeat strums, M5 figuration
CH_NYLON = 8     # M2 counter-arpeggios, M6 theme farewell
CH_DRUMS = 9     # GM percussion channel
CH_RHYTHM = 10   # M3 palm-mute 7/8 chug, M4 off-beat skanks, M5 figuration
CH_CHOIR2 = 11   # M2 harmonized hum ("oo"), M5 low hum counterline (mm)
CH_LEAD = 12     # M3 portamento synth solo (bend range 12); P2 Oldfield lead
CH_DOUBLE = 13   # P2 ABBA double: RPN fine-tune +8c, hard-panned, 3rds M4
CH_WINDS = 14    # M2 flute answers, M5 fiddle countermelody, M6 last echo
CH_BELLS = 15    # M1 music box, M5 bell peal / glock, M6 final bell


class Part:
    """One track: grid + channel data plus setup(sc) that writes it all."""

    def __init__(self, number: int, title: str, file: str,
                 movements: list[tuple[str, float, float]],
                 tempo_map: list[tuple[float, float]],
                 time_signatures: list[tuple[float, int, int]],
                 keysigs: list[tuple[float, int, int]],
                 channels: list[tuple[int, str, int, int, int, int]],
                 program_changes: list[tuple[int, float, int]]) -> None:
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
        """Write the conductor lane and all channel setups into `sc`."""
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


# ---------------------------------------------------------------------------
# Part One — "The Cold Half" (E minor; the guests arrive)
# ---------------------------------------------------------------------------

# Tempo grid: 92 @0, 84 @256, 92 @544 then +2 per 48 beats reaching 104 @832
# (the 4/4 coda holds 104).
PART1_TEMPO: list[tuple[float, float]] = (
    [(0.0, 92.0), (256.0, 84.0), (544.0, 92.0)]
    + [(544.0 + 48.0 * i, 92.0 + 2.0 * i) for i in range(1, 7)]   # ... 104 @832
)

# (ch, name, initial program, volume, pan, reverb).  Pans per the roadmap:
# choir I 54 / choir II 74, harmonium 58, fingerpick 36 / nylon 92; the arp
# autopans and the ABBA double is repanned by CC10 in its movements.
PART1_CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_PIANO,   "Grand Piano",      0, 100,  50, 55),
    (CH_PAD,     "Sweep Pad",       95,  80,  64, 85),
    (CH_ARP,     "Ice Arp",         81,  78,  76, 70),
    (CH_BASS,    "Fretless Bass",   35, 105,  64, 25),
    (CH_ORGAN,   "Harmonium",       20,  82,  58, 50),
    (CH_STRINGS, "Strings",         48,  80,  70, 75),
    (CH_CHOIR1,  "Choir I",         52,  88,  54, 80),
    (CH_STEEL,   "Steel Guitar",    25,  88,  36, 55),
    (CH_NYLON,   "Nylon Guitar",    24,  88,  92, 55),
    (CH_DRUMS,   "Drums",            0, 100,  64, 35),
    (CH_RHYTHM,  "Rhythm Guitar",   27,  85,  40, 45),
    (CH_CHOIR2,  "Choir II",        52,  82,  74, 80),
    (CH_LEAD,    "Saw Lead",        81, 100,  64, 60),
    (CH_DOUBLE,  "Lead Double",     30,  92,  84, 60),
    (CH_WINDS,   "Flute",           73,  85,  70, 80),
    (CH_BELLS,   "Music Box",       10,  90,  80, 75),
]

PART1 = Part(
    number=1,
    title="Winter Guests, Part One",
    file="01 - Winter Guests, Part One.mid",
    movements=[
        ("Frost",                   0.0, 256.0),   # E aeolian, 92
        ("The Humming",           256.0, 544.0),   # E aeolian->dorian, 84
        ("Footsteps in the Hall", 544.0, 864.0),   # 7/8, 92->104; 4/4 coda
    ],
    tempo_map=PART1_TEMPO,
    time_signatures=[(0.0, 4, 4), (544.0, 7, 8), (832.0, 4, 4)],
    keysigs=[(0.0, 1, 1)],                          # E minor
    channels=PART1_CHANNELS,
    program_changes=[
        (CH_BASS,   544.0, 33),    # fretless -> fingered for the 7/8 cell
        (CH_RHYTHM, 544.0, 28),    # clean -> palm-mute chug
    ],
)

# ---------------------------------------------------------------------------
# Part Two — "The Warm Half" (D major lifting to E major; the house warms up)
# ---------------------------------------------------------------------------

PART2_TEMPO: list[tuple[float, float]] = [
    (0.0, 118.0),
    (928.0, 104.0), (960.0, 88.0), (992.0, 72.0), (1008.0, 60.0),   # M6 rit
]

PART2_CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_PIANO,   "Grand Piano",      0, 100,  50, 55),
    (CH_PAD,     "Warm Pad",        89,  80,  64, 85),
    (CH_ARP,     "Ice Arp",         81,  78,  76, 70),
    (CH_BASS,    "Fingered Bass",   33, 105,  64, 25),
    (CH_ORGAN,   "Drawbar Organ",   16,  82,  58, 50),
    (CH_STRINGS, "Strings",         48,  80,  70, 75),
    (CH_CHOIR1,  "Choir I",         52,  88,  54, 80),
    (CH_STEEL,   "Steel Guitar",    25,  88,  36, 55),
    (CH_NYLON,   "Nylon Guitar",    24,  88,  92, 55),
    (CH_DRUMS,   "Drums",            0, 100,  64, 35),
    (CH_RHYTHM,  "Rhythm Guitar",   27,  85,  40, 45),
    (CH_CHOIR2,  "Choir II",        52,  82,  74, 80),
    (CH_LEAD,    "Overdrive Lead",  30, 100,  64, 60),
    (CH_DOUBLE,  "Lead Double",     30,  92,  84, 60),
    (CH_WINDS,   "Fiddle",          40,  85,  70, 80),
    (CH_BELLS,   "Glockenspiel",     9,  90,  80, 75),
]

PART2 = Part(
    number=2,
    title="Winter Guests, Part Two",
    file="02 - Winter Guests, Part Two.mid",
    movements=[
        ("Searchlight",          0.0,  448.0),   # D ionian -> E @320, 118
        ("The Glass Ballroom", 448.0,  896.0),   # E ionian, 118
        ("Last Light",         896.0, 1024.0),   # E ionian, rit 118->60
    ],
    tempo_map=PART2_TEMPO,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 2, 0), (320.0, 4, 0)],          # D major, E major @320
    channels=PART2_CHANNELS,
    program_changes=[
        (CH_ORGAN,  448.0, 18),    # drawbar -> rock organ for the ballroom
        (CH_BELLS,  448.0, 14),    # glock -> tubular bells for the peal
        (CH_PAD,    896.0, 95),    # warm -> sweep pad for the close
        (CH_BASS,   896.0, 35),    # fingered -> fretless slides
        (CH_WINDS,  896.0, 73),    # fiddle -> flute for the last echo
    ],
)

PARTS: list[Part] = [PART1, PART2]
