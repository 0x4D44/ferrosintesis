"""t09_ten_thousand_watts.py — STUB: 'Ten Thousand Watts' awaits composition.

See the track brief in "wrk_docs/2026.07.11 - HLD - Big Weather rockpop
album.md" §4.  A composer replaces this file wholesale; the honest stub
oracle below fails until then.
"""

from __future__ import annotations

import conductor

NUMBER = 9
TITLE = "Ten Thousand Watts"
FILE = "09 - Ten Thousand Watts.mid"
SEED = 20260709

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=[("stub", 0.0, 16.0)],
    tempo_map=[(0.0, 120.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0)],
    channels=[(0, "piano", 0, 100, 64, 55)],
)


def _stub(sc):
    pass


BUILDERS = [_stub]

PROGRAM_WHITELIST = {0}
CENTERED_CHANNELS = {0}
NOTE_RANGES = {0: (21, 108)}
GAP_WHITELIST = [(0.0, 16.0)]
BEND_EXEMPT = set()
DURATION_WINDOW = (0.0, 60.0)
BOUNDS_WHITELIST = []


def oracles(sc, info, spans):
    return [("stub", ["track 09 not yet composed"])]
