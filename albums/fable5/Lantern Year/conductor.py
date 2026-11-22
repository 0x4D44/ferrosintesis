"""conductor.py — the global skeleton of *Lantern Year* (ten tracks).

An album by Claude Fable 5: ten nights at a lighthouse across one year,
January to December.  Each track is a different night, a different weather
and a different idiom — chamber folk, storm prog, fog ambient, a 6/8 jig,
mallet minimalism, 5/4 noir, night-sky electronica, an orchestral scherzo, a
12/8 slow blues and a cathedral finale — bound by two pieces of shared DNA
that live in material.py and are machine-verified wherever they recur:

  * THE BEAM   a five-note cell (degrees 1-5-6-5-8): the lamp swinging out
               over the water and returning.  Every track states it at least
               three times, in its own voice.
  * THE HYMN   "the keeper's hymn", a 16-bar tune whose first five notes ARE
               the beam.  Track 1 states it plainly; track 10 crowns it;
               the nights between may borrow a phrase.

The grid is FEDERATED (the Through Lines / Slipstream shape): each track
module (movements/tNN_*.py) declares its own `Part` — movement grid, tempo
map, time signatures, key signatures, channel setups, scheduled program
changes — plus its verification config and per-track oracles.  This file
holds only what is genuinely global: the `Part` class, the album identity,
and the track registry that build.py and verify.py iterate.
"""

from __future__ import annotations

import engine as en

ALBUM = "Lantern Year"
ARTIST = "Claude Fable 5"
STYLE = ("Ten nights at a lighthouse across one year, each in its own idiom "
         "(chamber folk, storm prog, fog ambient, 6/8 jig, mallet "
         "minimalism, 5/4 noir, night-sky electronica, orchestral scherzo, "
         "12/8 slow blues, cathedral finale), bound by a five-note BEAM "
         "cell stated on every track and a 16-bar keeper's hymn that opens "
         "and crowns the year — every recurrence machine-verified.")

# Every track is "around five minutes": each module's DURATION_WINDOW must
# sit inside this album-wide window (seconds of the written FILE, which
# includes write()'s 2-beat end pad).  Enforced by material.album_oracles.
ALBUM_DURATION_WINDOW: tuple[float, float] = (285.0, 315.0)

# ---------------------------------------------------------------------------
# The track registry — (number, module stem, title, midi file, seed).
# Module stems name files under movements/.  Seeds are fixed per track so a
# rebuild is byte-identical and --verify reasons about the same Scores that
# produced the committed files.
# ---------------------------------------------------------------------------

REGISTRY: list[tuple[int, str, str, str, int]] = [
    (1,  "t01_first_lighting", "First Lighting",
         "01 - First Lighting.mid",  20261201),
    (2,  "t02_northeaster",    "Northeaster",
         "02 - Northeaster.mid",     20261202),
    (3,  "t03_fog_signal",     "Fog Signal",
         "03 - Fog Signal.mid",      20261203),
    (4,  "t04_the_mail_boat",  "The Mail Boat",
         "04 - The Mail Boat.mid",   20261204),
    (5,  "t05_glass_calm",     "Glass Calm",
         "05 - Glass Calm.mid",      20261205),
    (6,  "t06_false_lights",   "False Lights",
         "06 - False Lights.mid",    20261206),
    (7,  "t07_perseids",       "Perseids",
         "07 - Perseids.mid",        20261207),
    (8,  "t08_equinox_gale",   "Equinox Gale",
         "08 - Equinox Gale.mid",    20261208),
    (9,  "t09_the_long_watch", "The Long Watch",
         "09 - The Long Watch.mid",  20261209),
    (10, "t10_last_lighting",  "Last Lighting",
         "10 - Last Lighting.mid",   20261210),
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
        # DRIVE_LEAD guitar, percussion set B, the GM19 cathedral organ at 2).
        for ch, val in self.BANK_SELECTS:
            sc.cc(ch, 0, val, 0.0)
