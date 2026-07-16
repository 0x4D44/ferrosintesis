"""conductor.py — the global skeleton of *Slipstream* (ten tracks).

An album by Claude Fable 5, commissioned as the sibling of "Three-Sixty-One"
(the bonus reprise on *Through Lines*): ten aerobatic display acts, each a
richly layered, fast-paced build-drop-build spectacle.  The design source is
"wrk_docs/2026.07.16 - HLD - Slipstream album (ten displays).md".

The album's signature device is THE DUO — two overdriven guitars (ch14 the
lead ship, ch15 the wing ship) flying a different verified formation on every
track: octaves, trades, contrary motion, inversion, hocket, mirror canon,
sixths, retrograde, soar-over-pedal, lead-and-counter.

The grid is FEDERATED (the Through Lines shape): each track module
(movements/tNN_*.py) declares its own `Part` — movement grid, tempo map,
time signatures, key signatures, channel setups, scheduled program changes —
plus its verification config and per-track oracles.  This file holds only
what is genuinely global: the `Part` class, the album identity, and the
track registry (numbers, titles, files, module names, seeds) that build.py
and verify.py iterate.

Shared musical DNA (the ASCENT cell, the duo mirror arithmetic, the fill
library, the Three-Sixty-One quotes, the Morse lanes) lives in material.py
and is oracle-pinned wherever it recurs.
"""

from __future__ import annotations

import engine as en

ALBUM = "Slipstream"
ARTIST = "Claude Fable 5"
STYLE = ("Ten aerobatic display acts inspired by 'Three-Sixty-One': "
         "build-drop-build architectures, near-constant verified drum-fill "
         "escalations, soaring and sweeping synths, multiple independent "
         "counterpoints, and a two-guitar display team flying a different "
         "machine-verified formation on every track.  The finale flypast "
         "openly quotes the Three-Sixty-One orbit riff and scream.")

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Module stems name files under movements/.  Seeds are fixed per track so a
# rebuild is byte-identical and --verify reasons about the same Scores that
# produced the committed files.
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    (1,  "t01_wheels_up",    "Wheels Up",
         "01 - Wheels Up.mid",       20261101),
    (2,  "t02_knife_edge",   "Knife Edge",
         "02 - Knife Edge.mid",      20261102),
    (3,  "t03_hammerhead",   "Hammerhead",
         "03 - Hammerhead.mid",      20261103),
    (4,  "t04_cuban_eight",  "Cuban Eight",
         "04 - Cuban Eight.mid",     20261104),
    (5,  "t05_lomcevak",     "Lomcevak",
         "05 - Lomcevak.mid",        20261105),
    (6,  "t06_mirror_pass",  "Mirror Pass",
         "06 - Mirror Pass.mid",     20261106),
    (7,  "t07_vapour",       "Vapour",
         "07 - Vapour.mid",          20261107),
    (8,  "t08_split_s",      "Split-S",
         "08 - Split-S.mid",         20261108),
    (9,  "t09_night_launch", "Night Launch",
         "09 - Night Launch.mid",    20261109),
    (10, "t10_the_flypast",  "The Flypast",
         "10 - The Flypast.mid",     20261110),
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
        # channel into the alternate voicings — e.g. the sustaining
        # DRIVE_LEAD guitar, percussion set B).
        for ch, val in self.BANK_SELECTS:
            sc.cc(ch, 0, val, 0.0)
