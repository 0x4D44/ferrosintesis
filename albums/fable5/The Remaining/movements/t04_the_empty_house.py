"""movements/t04_the_empty_house.py — track 4 of *The Remaining* (STUB).

A composer replaces this file wholesale (see COMPOSER-NOTES.md and the HLD
section for "The Empty House").  The grid below is the HLD starting point; the
stub's oracle fails honestly until the track is composed.
"""

from __future__ import annotations

import conductor
import engine as en          # noqa: F401  (used by the real module)
import material              # noqa: F401  (used by the real module)

NUMBER = 4
TITLE = "The Empty House"
FILE = "04 - The Empty House.mid"
SEED = 20261004
COMMENT = ("Track 04 of 'The Remaining' - not yet composed.")

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Rooms", 0.0, 64.0),
               ("II. The Music Box", 64.0, 144.0),
               ("III. Hum", 144.0, 216.0),
               ("IV. Clock", 216.0, 272.0)],
    tempo_map=[(0.0, 54.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=[(0, "piano", 0, 100, 64, 60)],
)

BUILDERS = [lambda sc: None, lambda sc: None, lambda sc: None, lambda sc: None]

PROGRAM_WHITELIST = {0}
CENTERED_CHANNELS = {0}
NOTE_RANGES = {0: (21, 108)}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (260.0, 360.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def oracles(sc, info, spans):
    return [("composed", ["track 4 is a stub - not yet composed"])]
