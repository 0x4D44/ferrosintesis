"""conductor.py — the global skeleton of *Seven Kinds of Sunlight*.

An upbeat, through-written SONG (one track, ~3:55): D ionian at 138
bpm, verse / pre-chorus / chorus / middle-eight architecture, odd
meters, and a +2 gear change (D -> E) for the final chorus.  The title
is a nod to the 7/8 verses.

Section grid (beats are quarter notes; a 7/8 bar is 3.5 beats):

    Intro          0 -  32   4/4   the riff, filter opening, band falls in
    Verse 1       32 -  88   7/8   hummed melody over the 3+2+2 engine
    Pre-Chorus 1  88 - 112   6/8   the rising lift, toms climbing
    Chorus 1     112 - 176   4/4   HOOK + counter A + counter B
    Turnaround   176 - 184   4/4   the riff, two bars
    Verse 2      184 - 264   7/8   + piano CANON, wah guitar, then PC2
    Pre-Chorus 2 240 - 264   6/8   (inside the verse-2 module)
    Chorus 2     264 - 328   4/4   + choir-II descant
    Middle Eight 328 - 368   5/4   flute/lead counterpoint, portamento
    Guitar Solo  368 - 424   7/8   RPN bend range 12, hammer-ons, dive
    Drum Break   424 - 446   7/8 then 4/4 at 438: stabs + fill showcase
    Final Chorus 446 - 510   4/4   E MAJOR: everything stacked
    Outro        510 - 542   4/4   riff out, stop-time, one long ring

Channel map (sustained beds centred; width from transient sources):
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_PIANO = 0     # comping; the verse-2 CANON; M8 pools; final stabs
CH_PAD = 1       # beds; outro filter close
CH_ARP = 2       # pulse synth: intro riff, COUNTER_A, risers (CC74/71)
CH_BASS = 3      # picked bass: THE driving engine (oracle-certified)
CH_LEAD = 4      # bright lead: verse melody double (fine-tuned), M8 glide
CH_STRINGS = 5   # COUNTER_B, swells
CH_CHOIR1 = 6    # the chorus HOOK (CC70 ah), lyric syllables
CH_CHOIR2 = 7    # the snapped descant
CH_GLOCK = 8     # glockenspiel: riff accents, sparkle
CH_DRUMS = 9     # see drums.py
CH_GTR = 10      # rhythm guitar: clean skank / wah funk / overdrive
CH_SOLO = 11     # distortion lead: the 7/8 solo (RPN 12, CC68, dive)
CH_ORGAN = 12    # pads, COUNTER_B double; Leslie in the final chorus
CH_OOHS = 13     # voice oohs: verse melody (closed), final-chorus vocalise
CH_FLUTE = 14    # M8 counterpoint voice; final-chorus descant echo
CH_VIBES = 15    # vibraphone shimmer -> tubular bells for the finale

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

SECTIONS: list[tuple[str, float, float]] = [
    ("Intro",          0.0,  32.0),
    ("Verse 1",       32.0,  88.0),
    ("Pre-Chorus 1",  88.0, 112.0),
    ("Chorus 1",     112.0, 176.0),
    ("Turnaround",   176.0, 184.0),
    ("Verse 2",      184.0, 240.0),
    ("Pre-Chorus 2", 240.0, 264.0),
    ("Chorus 2",     264.0, 328.0),
    ("Middle Eight", 328.0, 368.0),
    ("Guitar Solo",  368.0, 424.0),
    ("Drum Break",   424.0, 446.0),
    ("Final Chorus", 446.0, 510.0),
    ("Outro",        510.0, 542.0),
]
END_BEAT = SECTIONS[-1][2]

# Module spans (movement-bounds oracle): modules may cover 2 sections.
MODULE_SPANS: list[tuple[str, float, float]] = [
    ("s1_intro",       0.0,  32.0),
    ("s2_verse1",     32.0, 112.0),
    ("s3_chorus1",   112.0, 184.0),
    ("s4_verse2",    184.0, 264.0),
    ("s5_chorus2",   264.0, 328.0),
    ("s6_middle8",   328.0, 368.0),
    ("s7_solo_break", 368.0, 446.0),
    ("s8_final",     446.0, 542.0),
]

TEMPO_MAP: list[tuple[float, float]] = [
    (0.0, 138.0), (368.0, 139.0), (446.0, 140.0),
]

TIME_SIGNATURES: list[tuple[float, int, int]] = [
    (0.0, 4, 4), (32.0, 7, 8), (88.0, 6, 8), (112.0, 4, 4),
    (184.0, 7, 8), (240.0, 6, 8), (264.0, 4, 4), (328.0, 5, 4),
    (368.0, 7, 8), (438.0, 4, 4),
]

KEYSIGS: list[tuple[float, int, int]] = [(0.0, 2, 0), (446.0, 4, 0)]

# (ch, name, program, volume, pan, reverb)
CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_PIANO,   "Grand Piano",     0,  95, 52, 55),
    (CH_PAD,     "Warm Pad",       89,  78, 64, 78),
    (CH_ARP,     "Pulse Synth",    81,  76, 78, 55),
    (CH_BASS,    "Picked Bass",    34, 110, 64, 12),
    (CH_LEAD,    "Bright Lead",    81,  92, 60, 55),
    (CH_STRINGS, "Strings",        48,  78, 70, 70),
    (CH_CHOIR1,  "Choir I",        52,  96, 64, 72),
    (CH_CHOIR2,  "Choir II",       52,  86, 56, 72),
    (CH_GLOCK,   "Glockenspiel",    9,  80, 86, 65),
    (CH_DRUMS,   "Drums",           0, 108, 64, 28),
    (CH_GTR,     "Rhythm Guitar",  27,  88, 42, 40),
    (CH_SOLO,    "Solo Guitar",    30,  96, 64, 55),
    (CH_ORGAN,   "Drawbar Organ",  16,  76, 64, 60),
    (CH_OOHS,    "Voice Oohs",     53,  84, 72, 75),
    (CH_FLUTE,   "Flute",          73,  86, 66, 70),
    (CH_VIBES,   "Vibraphone",     11,  82, 84, 65),
]

# (ch, beat, program)
PROGRAM_CHANGES: list[tuple[int, float, int]] = [
    (CH_GTR,   112.0, 29),      # overdrive for the choruses
    (CH_GTR,   184.0, 27),      # clean wah funk for verse 2
    (CH_GTR,   264.0, 29),
    (CH_GTR,   328.0, 27),      # clean colour in the middle eight
    (CH_GTR,   368.0, 28),      # palm-mute chug under the solo
    (CH_GTR,   446.0, 29),      # overdrive to the end
    (CH_ORGAN, 446.0, 18),      # rock organ + Leslie for the finale
    (CH_VIBES, 446.0, 14),      # vibes -> tubular bells
]


def setup(sc: en.Score) -> None:
    """Write the conductor lane and all channel setups into `sc`."""
    for beat, bpm in TEMPO_MAP:
        sc.tempo(beat, bpm)
    for beat, num, den in TIME_SIGNATURES:
        sc.timesig(beat, num, den)
    for beat, sharps, minor in KEYSIGS:
        en.keysig(sc, beat, sharps, minor)
    for name, t0, _t1 in SECTIONS:
        sc.marker(t0, name)
    for ch, name, prog, vol, pan, rev in CHANNELS:
        sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
    for ch, beat, prog in PROGRAM_CHANGES:
        sc.program(ch, prog, beat)
