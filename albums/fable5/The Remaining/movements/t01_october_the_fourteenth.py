"""movements/t01_october_the_fourteenth.py — track 1 of *The Remaining* (STUB).

A composer replaces this file wholesale (see COMPOSER-NOTES.md and the HLD
section for "October the Fourteenth").  The grid below is the HLD starting point; the
stub's oracle fails honestly until the track is composed.
"""

from __future__ import annotations

import conductor
import engine as en          # noqa: F401  (used by the real module)
import material              # noqa: F401  (used by the real module)

NUMBER = 1
TITLE = "October the Fourteenth"
FILE = "01 - October the Fourteenth.mid"
SEED = 20261014
COMMENT = ("Track 01 of 'The Remaining' - not yet composed.")

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Morning", 0.0, 64.0),
               ("II. The Vanishing", 64.0, 160.0),
               ("III. The Fourteenth", 160.0, 256.0),
               ("IV. Vigil", 256.0, 384.0)],
    tempo_map=[(0.0, 66.0)],
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
DURATION_WINDOW = (300.0, 420.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def oracles(sc, info, spans):
    return [("composed", ["track 1 is a stub - not yet composed"])]
