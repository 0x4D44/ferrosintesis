"""movements/t02_the_ninety_eight.py — track 2 of *The Remaining* (STUB).

A composer replaces this file wholesale (see COMPOSER-NOTES.md and the HLD
section for "The Ninety-Eight").  The grid below is the HLD starting point; the
stub's oracle fails honestly until the track is composed.
"""

from __future__ import annotations

import conductor
import engine as en          # noqa: F401  (used by the real module)
import material              # noqa: F401  (used by the real module)

NUMBER = 2
TITLE = "The Ninety-Eight"
FILE = "02 - The Ninety-Eight.mid"
SEED = 20261098
COMMENT = ("Track 02 of 'The Remaining' - not yet composed.")

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Ground", 0.0, 36.0),
               ("II. Variations", 36.0, 252.0),
               ("III. Coda", 252.0, 330.0)],
    tempo_map=[(0.0, 60.0)],
    time_signatures=[(0.0, 3, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=[(0, "piano", 0, 100, 64, 60)],
)

BUILDERS = [lambda sc: None, lambda sc: None, lambda sc: None]

PROGRAM_WHITELIST = {0}
CENTERED_CHANNELS = {0}
NOTE_RANGES = {0: (21, 108)}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (280.0, 390.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def oracles(sc, info, spans):
    return [("composed", ["track 2 is a stub - not yet composed"])]
