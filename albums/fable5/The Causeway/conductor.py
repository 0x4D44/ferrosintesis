"""conductor.py — the global skeleton of *The Causeway* (five tracks).

An album by Claude Fable 5: a tidal island and a mainland village, joined by
a causeway that only shows at low water — two players, one on each shore,
sending music instead of letters across a winter.  The island writes in
late-ABBA ice (incantatory repeated notes, off-beat pushes, sequenced chill)
wrapped in Enigma/Delerium weather; the mainland writes in McCartney warmth
(melodic protagonist bass, piano pump, clavinet strut, suite-form pivots)
layered with Oldfield patience.  The design source is
"wrk_docs/2026.07.18 - HLD - The Causeway album (five crossings).md".

The album's spine is THE CONVERGENCE: the two shore themes (material.ISLAND,
material.MAINLAND) begin a tritone apart and close track by track —
6, 4, 3, 2, 0 semitones — while every cadence is modally withheld (no
leading-tone V-I in tracks 1-4) and the themes never sound simultaneously.
Track 5 crosses at dawn: both themes together in D, invertible counterpoint,
a medley of the album's four hooks, the fusion phrase's single melodic tonic
landing, and a IV-I plagal Picardy.  The stereo field is the strait: island
channels sit left, mainland channels right, the seats narrowing with the keys.

The grid is FEDERATED (the Slipstream / The Remaining shape): each track
module (movements/tNN_*.py) declares its own `Part` — movement grid, tempo
map, time signatures, key signatures, channel setups, scheduled program
changes — plus its verification config and per-track oracles.  This file
holds only what is genuinely global: the `Part` class, the album identity,
and the track registry that build.py and verify.py iterate.

Shared musical DNA (the two themes, the convergence table, the hook ledger,
the fusion phrase, the morse tide-table, the tide-breath tempo generator,
the shore pans, the tolls, the vowel clock) lives in material.py and is
oracle-pinned wherever it recurs.
"""

from __future__ import annotations

import engine as en

ALBUM = "The Causeway"
ARTIST = "Claude Fable 5"
STYLE = ("Five crossings between a tidal island and the mainland: an icy "
         "late-ABBA incantation and a warm McCartney tune begin a tritone "
         "apart and converge track by track (6-4-3-2-0 semitones), kept "
         "from ever sounding together — and from every leading-tone cadence "
         "— until the causeway dries at dawn in track 5, where both themes "
         "meet in invertible counterpoint over a piano-pump medley of the "
         "album's hooks and a fusion phrase lands the record's only melodic "
         "tonic, on a plagal Picardy.  Morse tide-words, a breath-flute "
         "herald before every groove, and a bell buoy that tolls the track "
         "number carry the letters across the water.")

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Module stems name files under movements/.  Seeds are fixed per track so a
# rebuild is byte-identical and --verify reasons about the same Scores that
# produced the committed files.
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    (1, "t01_neap_light",         "Neap Light",
        "01 - Neap Light.mid",         202607181),
    (2, "t02_the_winter_ferry",   "The Winter Ferry",
        "02 - The Winter Ferry.mid",   202607182),
    (3, "t03_spring_tide",        "Spring Tide",
        "03 - Spring Tide.mid",        202607183),
    (4, "t04_the_ebb_letter",     "The Ebb Letter",
        "04 - The Ebb Letter.mid",     202607184),
    (5, "t05_low_water_crossing", "Low Water Crossing",
        "05 - Low Water Crossing.mid", 202607185),
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
