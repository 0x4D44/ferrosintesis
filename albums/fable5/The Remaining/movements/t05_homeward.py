"""movements/t05_homeward.py — track 5 of *The Remaining* (STUB).

A composer replaces this file wholesale (see COMPOSER-NOTES.md and the HLD
section for "Homeward").  The grid below is the HLD starting point; the
stub's oracle fails honestly until the track is composed.
"""

from __future__ import annotations

import conductor
import engine as en          # noqa: F401  (used by the real module)
import material              # noqa: F401  (used by the real module)

NUMBER = 5
TITLE = "Homeward"
FILE = "05 - Homeward.mid"
SEED = 20261005
COMMENT = ("Track 05 of 'The Remaining' - not yet composed.")

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Procession", 0.0, 96.0),
               ("II. The Turning", 96.0, 160.0),
               ("III. All of Them, Home", 160.0, 352.0),
               ("IV. Quiet", 352.0, 472.0)],
    tempo_map=[(0.0, 63.0)],
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
DURATION_WINDOW = (360.0, 480.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def oracles(sc, info, spans):
    return [("composed", ["track 5 is a stub - not yet composed"])]
