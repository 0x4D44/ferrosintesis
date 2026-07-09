"""conductor.py — the global skeleton of *The Ninth Bell* (one track).

A Gabriel-Knight-idiom gothic orchestral piece: the string-chord gesture
of `demos/orchestral_demo.py` ch0 opens it verbatim, then one dramatic
spring is compressed twice — build, HIT on the wrong chord, void, rebuild
(with a feint), full toll, Neapolitan fracture, embers.  Nine tubular-bell
tolls frame the piece; the ninth — a lone A, the theme's withheld
resolution — is its last note.  A aeolian, 4/4, 101 bars.

Design: `wrk_docs/2026.07.07 - HLD - The Ninth Bell.md` (the HLD is the
spec; every movement module cites the section it implements).

Movement grid (beats; bar N starts at beat 4*(N-1)):

    I.    The Veil          0 -  32   the demo gesture, verbatim, alone
    II.   Processional     32 -  96   theme (cello), countersubject (violin 8va pass)
    III.  First Ascent     96 - 128   the build; the ear is set up
    IV.   The Hit          128 - 132  E-major slam; scored silence
    V.    Sotto Voce      132 - 196   music box in the void; Bb surfaces
    VI.   Rising Tide     196 - 292   the long rebuild; feint drop at 244
    VII.  Full Toll       292 - 356   climax on Am|Dm|Em|E7; Bb fracture
    VIII. Embers          356 - 404   the exhale; the ninth bell (lone A)
"""

from __future__ import annotations

import engine as en

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_STRINGS = 0    # THE intro gesture verbatim; beds, pulses, tutti chords
CH_CELLO = 1      # theme voice 1, countersubject, sighs, the dying sag
CH_CHOIR = 2      # dread bed; CC70 mm->ah arc; "ah" stab on the hits
CH_ORGAN = 3      # 16' pedals, rebuild chords, climax power; CC1 Leslie arc
CH_BELLS = 4      # tubular bells: the nine-toll ledger + climax peal ONLY
CH_HARP = 5       # void harmonics, rebuild arps, post-hit falling gesture
CH_TIMPANI = 6    # heartbeats, rolls, ostinato, both hits
CH_MBOX = 7       # music box: the void's voice and the coda mirror
CH_VIOLIN = 8     # theme 8va, leap-cell sequences, the b6 scream
CH_DRUMS = 9      # GM percussion: BD 36, crashes 49/57, toms 41/43
CH_PIANO = 10     # low tolling octaves (rebuild), hammered octaves (climax)
CH_PAD = 11       # void ghost + the Neapolitan Bb colour only
CH_CBASS = 12     # bowed low reinforcement, lament-tetrachord bass

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

MOVEMENTS: list[tuple[str, float, float]] = [
    ("I. The Veil",       0.0,  32.0),
    ("II. Processional", 32.0,  96.0),
    ("III. First Ascent", 96.0, 128.0),
    ("IV. The Hit",     128.0, 132.0),
    ("V. Sotto Voce",   132.0, 196.0),
    ("VI. Rising Tide", 196.0, 292.0),
    ("VII. Full Toll",  292.0, 356.0),
    ("VIII. Embers",    356.0, 404.0),
]
END_BEAT = MOVEMENTS[-1][2]

# Tempo is itself a dramatic controller (HLD section 3): shock slows time
# at the void, the rebuild is a staircase, the coda is an exhale.
TEMPO_MAP: list[tuple[float, float]] = [
    (0.0, 74.0),
    (132.0, 63.0),                              # the void: time slows
    (196.0, 66.0), (212.0, 70.0), (228.0, 74.0), (260.0, 80.0),  # rebuild
    (356.0, 60.0),                              # embers
    (388.0, 56.0), (396.0, 52.0),               # final ritardando
]

TIME_SIGNATURES: list[tuple[float, int, int]] = [(0.0, 4, 4)]

KEYSIGS: list[tuple[float, int, int]] = [(0.0, 0, 1)]       # A minor

# Extra dramatic markers beyond the movement names (HLD graft #8).
EXTRA_MARKERS: list[tuple[float, str]] = [
    (128.0, "THE HIT (E major)"),
    (352.0, "THE FRACTURE (Bb)"),
]

# (ch, name, program, volume, pan, reverb)
# Sustained beds sit at pan 64 (mono-collapse lesson); stereo width comes
# from the transient sources only (bells/harp/music box/piano/timpani).
# CH_STRINGS setup values are the demo's EXACT parameters — do not touch.
CHANNELS: list[tuple[int, str, int, int, int, int]] = [
    (CH_STRINGS, "strings",      48,  88, 64, 74),
    (CH_CELLO,   "cello",        42,  96, 64, 70),
    (CH_CHOIR,   "choir",        52,  84, 64, 80),
    (CH_ORGAN,   "church organ", 19,  78, 64, 60),
    (CH_BELLS,   "tubular bells", 14, 92, 48, 90),
    (CH_HARP,    "harp",         46,  80, 80, 70),
    (CH_TIMPANI, "timpani",      47, 100, 56, 55),
    (CH_MBOX,    "music box",    10,  72, 72, 110),
    (CH_VIOLIN,  "violin",       40,  90, 64, 72),
    (CH_DRUMS,   "percussion",    0,  90, 64, 70),
    (CH_PIANO,   "piano",         0,  85, 44, 50),
    (CH_PAD,     "dark pad",     89,  60, 64, 95),
    (CH_CBASS,   "contrabass",   43,  86, 64, 60),
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
    for beat, text in EXTRA_MARKERS:
        sc.marker(beat, text)
    for ch, name, prog, vol, pan, rev in CHANNELS:
        sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
