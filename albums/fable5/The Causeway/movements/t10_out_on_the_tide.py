"""movements/t10_out_on_the_tide.py — STUB awaiting composition (Act Two).

Replace wholesale per COMPOSER-NOTES.md and the Act Two HLD addendum's
track section.
"""

from __future__ import annotations

import conductor

NUMBER = 10
TITLE = "Out on the Tide"
FILE = "10 - Out on the Tide.mid"
SEED = 202607190
COMMENT = "stub - not yet composed"

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Stub", 0.0, 8.0)],
    tempo_map=[(0.0, 96.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 0)],
    channels=[(0, "piano", 0, 100, 64, 40)],
)


def _b_stub(sc):
    sc.note(0, 62, 0.0, 4.0, 60, jt=0)


BUILDERS = [_b_stub]
PROGRAM_WHITELIST = {0}
CENTERED_CHANNELS = {0}
NOTE_RANGES = {0: (36, 96)}
GAP_WHITELIST = [(4.0, 8.0)]
BEND_EXEMPT = set()
DURATION_WINDOW = (0.0, 60.0)
BOUNDS_WHITELIST = []


def oracles(sc, info, spans):
    return [("composed", ["track not yet composed - replace this stub"])]
