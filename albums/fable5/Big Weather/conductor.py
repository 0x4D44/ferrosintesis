"""conductor.py — the global skeleton of *Big Weather* (10 tracks).

A rock/pop album by Claude Fable 5: builds and drops as weather fronts —
every song a forecast.  Design source:
"wrk_docs/2026.07.11 - HLD - Big Weather rockpop album.md".

The grid is FEDERATED (the Through Lines shape): each track module
(movements/tNN_*.py) declares its own `Part` — its movement grid (verse /
pre-chorus / chorus / middle-8 sections as named movements), tempo map,
time signatures, key signatures, channel setups and scheduled program
changes — plus its verification config and per-track oracles.  This file
holds only what is genuinely global: the `Part` class, the album identity,
and the track registry that build.py and verify.py iterate.
"""

from __future__ import annotations

import engine as en

ALBUM = "Big Weather"
ARTIST = "Claude Fable 5"
STYLE = ("A ten-track instrumental rock/pop album: upbeat, catchy songs "
         "with melodic bass guitar, stereo-spread drum features, layered "
         "wordless choir, overdriven guitars and piano, orchestral "
         "elements (strings, brass, timpani) arriving as each song "
         "builds. Builds and drops as weather fronts - every song a "
         "forecast.")

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Seeds are fixed per track so a rebuild is byte-identical and --verify
# reasons about the same Scores that produced the committed files.  Each
# track is its own Score(seed): tracks are mutually isolated, so editing
# one can never re-roll another (the single-RNG-stream lesson applies
# WITHIN a track only — re-verify the whole track after any movement edit).
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    (1,  "t01_first_light_freeway", "First Light Freeway",
         "01 - First Light Freeway.mid",   20260701),
    (2,  "t02_paper_kites",         "Paper Kites",
         "02 - Paper Kites.mid",           20260702),
    (3,  "t03_run_the_rooftops",    "Run the Rooftops",
         "03 - Run the Rooftops.mid",      20260703),
    (4,  "t04_glass_anthem",        "Glass Anthem",
         "04 - Glass Anthem.mid",          20260704),
    (5,  "t05_static_and_sparks",   "Static & Sparks",
         "05 - Static & Sparks.mid",       20260705),
    (6,  "t06_half_past_summer",    "Half Past Summer",
         "06 - Half Past Summer.mid",      20260706),
    (7,  "t07_the_getaway_choir",   "The Getaway Choir",
         "07 - The Getaway Choir.mid",     20260707),
    (8,  "t08_neon_cathedral",      "Neon Cathedral",
         "08 - Neon Cathedral.mid",        20260708),
    (9,  "t09_ten_thousand_watts",  "Ten Thousand Watts",
         "09 - Ten Thousand Watts.mid",    20260709),
    (10, "t10_big_weather",         "Big Weather",
         "10 - Big Weather.mid",           20260710),
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
        for ch, val in self.BANK_SELECTS:
            sc.cc(ch, 0, val, 0.0)
