"""conductor.py — the global skeleton of *The Remaining* (five tracks).

An album by Claude Fable 5 in the idiom of Max Richter's score for *The
Leftovers*: grief-laden piano ostinati, string-quartet suspensions, sub-bass
drones and quiet electronics, long additive builds and sudden intimate drops.
The design source is "wrk_docs/2026.07.18 - HLD - The Remaining album (five
elegies).md".

The album's spine is THE DEPARTURE: in T1 a violin phrase (material.
DEPARTED_LINE) is interrupted mid-thought and the piano's ostinato loses two
of its eight quavers (material.HOLES); the wound stays open through three
more tracks; in T5 the departed voice returns, finishes the phrase verbatim,
the holes fill, and the album's six-note theme — which ends on the unresolved
"waiting tone" (degree 2) in every statement across tracks 1-4 — is finally
allowed its degree-1 arrival, once, recast in D major.

The grid is FEDERATED (the Slipstream / Through Lines shape): each track
module (movements/tNN_*.py) declares its own `Part` — movement grid, tempo
map, time signatures, key signatures, channel setups, scheduled program
changes — plus its verification config and per-track oracles.  This file
holds only what is genuinely global: the `Part` class, the album identity,
and the track registry (numbers, titles, files, module names, seeds) that
build.py and verify.py iterate.

Shared musical DNA (the ground and its suspensions, the theme, the departure
figure and its holes, the departed line, the morse lane, the seating plan)
lives in material.py and is oracle-pinned wherever it recurs.
"""

from __future__ import annotations

import engine as en

ALBUM = "The Remaining"
ARTIST = "Claude Fable 5"
STYLE = ("Five elegies for piano, strings, choir and quiet electronics in "
         "the idiom of Max Richter's score for The Leftovers: a four-chord "
         "ground under suspended sighs, a piano ostinato that loses two of "
         "its quavers when a violin phrase is interrupted mid-thought, a "
         "pulse track searching a dominant-minor static field, and a finale "
         "in which the departed voice returns, finishes its phrase verbatim, "
         "and the album's withheld tonic finally lands — once, in D major.")

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Module stems name files under movements/.  Seeds are fixed per track so a
# rebuild is byte-identical and --verify reasons about the same Scores that
# produced the committed files.
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    (1, "t01_october_the_fourteenth", "October the Fourteenth",
        "01 - October the Fourteenth.mid", 20261014),
    (2, "t02_the_ninety_eight",       "The Ninety-Eight",
        "02 - The Ninety-Eight.mid",       20261098),
    (3, "t03_static",                 "Static",
        "03 - Static.mid",                 20261003),
    (4, "t04_the_empty_house",        "The Empty House",
        "04 - The Empty House.mid",        20261004),
    (5, "t05_homeward",               "Homeward",
        "05 - Homeward.mid",               20261005),
]


class Part:
    """One track: grid + channel data plus setup(sc) that writes it all."""

    def __init__(self, number: int, title: str, file: str,
                 movements: list[tuple[str, float, float]],
                 tempo_map: list[tuple[float, float]],
                 time_signatures: list[tuple[float, int, int]],
                 keysigs: list[tuple[float, int, int]],
                 channels: list[tuple[int, str, int, int, int, int]],
                 program_changes: list[tuple[int, float, int]] = (),
                 extra_markers: list[tuple[float, str]] = (),
                 bank_selects: list[tuple[int, int]] = ()) -> None:
        self.number = number
        self.title = title
        self.file = file
        self.MOVEMENTS = movements
        self.TEMPO_MAP = tempo_map
        self.TIME_SIGNATURES = time_signatures
        self.KEYSIGS = keysigs
        self.CHANNELS = channels
        self.PROGRAM_CHANGES = list(program_changes)
        self.EXTRA_MARKERS = list(extra_markers)
        self.BANK_SELECTS = list(bank_selects)
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
        for beat, text in self.EXTRA_MARKERS:
            sc.marker(beat, text)
        for ch, name, prog, vol, pan, rev in self.CHANNELS:
            sc.channel(ch, name, prog, volume=vol, pan=pan, reverb=rev)
        for ch, beat, prog in self.PROGRAM_CHANGES:
            sc.program(ch, prog, beat)
        # CC0 bank select at beat 0 (ferrosintesis alt-bank: nonzero opts the
        # channel into the alternate voicings).
        for ch, val in self.BANK_SELECTS:
            sc.cc(ch, 0, val, 0.0)
