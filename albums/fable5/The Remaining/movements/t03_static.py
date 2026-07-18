"""movements/t03_static.py — track 3 of *The Remaining* (STUB).

A composer replaces this file wholesale (see COMPOSER-NOTES.md and the HLD
section for "Static").  The grid below is the HLD starting point; the
stub's oracle fails honestly until the track is composed.
"""

from __future__ import annotations

import conductor
import engine as en          # noqa: F401  (used by the real module)
import material              # noqa: F401  (used by the real module)

NUMBER = 3
TITLE = "Static"
FILE = "03 - Static.mid"
SEED = 20261003
COMMENT = ("Track 03 of 'The Remaining' - not yet composed.")

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Pulse", 0.0, 160.0),
               ("II. Search", 160.0, 352.0),
               ("III. Cutoff", 352.0, 504.0)],
    tempo_map=[(0.0, 112.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],
    channels=[(0, "piano", 0, 100, 64, 60)],
)

BUILDERS = [lambda sc: None, lambda sc: None, lambda sc: None]

PROGRAM_WHITELIST = {0}
CENTERED_CHANNELS = {0}
NOTE_RANGES = {0: (21, 108)}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (240.0, 330.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def oracles(sc, info, spans):
    return [("composed", ["track 3 is a stub - not yet composed"])]
