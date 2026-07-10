"""conductor.py — the global skeleton of *Through Lines* (15 tracks).

A double album by Claude Fable 5: every piece is a line — a lineage, a high
wire, a fault line, a bass line, a timeline. Design source:
"wrk_docs/2026.07.09 - HLD - Through Lines double album.md".

Unlike the single-track albums, the grid here is FEDERATED: each track module
(movements/tNN_*.py) declares its own `Part` — its movement grid, tempo map,
time signatures, key signatures, channel setups and scheduled program
changes — plus its verification config and per-track oracles. This file holds
only what is genuinely global: the `Part` class, the album identity, and the
track registry (numbers, titles, files, module names, seeds) that build.py
and verify.py iterate.

Shared musical DNA (the FABLE cell, the bridge chorale, the trilogy motifs,
the Morse lanes) lives in material.py and is oracle-pinned wherever it recurs.
"""

from __future__ import annotations

import engine as en

ALBUM = "Through Lines"
ARTIST = "Claude Fable 5"
STYLE = ("A fifteen-track double album (with a bonus finale reprise, "
         "'Three-Sixty-One'): Disc 1 'Lines of Descent' (ideas — "
         "self-portrait, model lineage, evolution, the world, memory, "
         "process, weather), Disc 2 'Lines of Flight' (spectacles — the "
         "AquaTheater trilogy, an action cue, night jazz, bronze, a "
         "medley suite, a lullaby). Leitmotifs are machine-verified "
         "wherever they recur.")

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Module stems name files under movements/.  Seeds are fixed per track so a
# rebuild is byte-identical and --verify reasons about the same Scores that
# produced the committed files.
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    # ---- Disc 1 — Lines of Descent ----
    (1,  "t01_five_fables",     "Five Fables",
         "01 - Five Fables.mid",              20260901),
    (2,  "t02_scaling_laws",    "Scaling Laws",
         "02 - Scaling Laws.mid",             20260902),
    (3,  "t03_descent",         "Descent with Modification",
         "03 - Descent with Modification.mid", 20260903),
    (4,  "t04_fault_lines",     "Fault Lines",
         "04 - Fault Lines.mid",              20260904),
    (5,  "t05_the_832",         "The 8.32",
         "05 - The 8.32.mid",                 20260905),
    (6,  "t06_two_rooms",       "Two Rooms, One Clock",
         "06 - Two Rooms, One Clock.mid",     20260906),
    (7,  "t07_german_bight",    "German Bight",
         "07 - German Bight.mid",             20260907),
    # ---- Disc 2 — Lines of Flight ----
    (8,  "t08_ten_metres",      "Ten Metres of Air",
         "08 - Ten Metres of Air.mid",        20260908),
    (9,  "t09_wirewalker",      "Wirewalker",
         "09 - Wirewalker.mid",               20260909),
    (10, "t10_three_sixty",     "Three-Sixty",
         "10 - Three-Sixty.mid",              20260910),
    (11, "t11_night_train",     "Night Train to Tirana",
         "11 - Night Train to Tirana.mid",    20260911),
    (12, "t12_three_flights",   "Three Flights Up",
         "12 - Three Flights Up.mid",         20260912),
    (13, "t13_bronze_water",    "Bronze Water",
         "13 - Bronze Water.mid",             20260913),
    (14, "t14_estuary_suite",   "The Estuary Suite",
         "14 - The Estuary Suite.mid",        20260914),
    (15, "t15_landing_lights",  "Landing Lights",
         "15 - Landing Lights.mid",           20260915),
    # ---- Bonus track — a variant of T10 "Three-Sixty" ----
    (16, "t16_three_sixty_one",  "Three-Sixty-One",
         "16 - Three-Sixty-One.mid",          20260916),
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
        # channel into the alternate voicings — percussion set B / gong).
        for ch, val in self.BANK_SELECTS:
            sc.cc(ch, 0, val, 0.0)
