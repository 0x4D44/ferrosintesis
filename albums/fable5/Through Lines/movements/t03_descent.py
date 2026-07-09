"""t03_descent — Track 3 "Descent with Modification" of *Through Lines* (STUB).

Disc 1, 'Lines of Descent'.  NOT YET COMPOSED: this placeholder obeys the track-module
contract (see movements/__init__.py, build.py, verify.py) — registry
identity, a one-movement Part, one quiet middle-C builder, and the
verification config — so the album machinery runs end to end.  Its
oracles() returns one deliberate failure, keeping `build.py --verify`
honestly red until a composer replaces this file wholesale with the
real track.
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 3
TITLE = 'Descent with Modification'
FILE = '03 - Descent with Modification.mid'
SEED = 20260903

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("(stub)", 0.0, 8.0)],
    tempo_map=[(0.0, 100.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0)],
    channels=[(0, "piano", 0, 100, 64, 40)],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {0}
CENTERED_CHANNELS: set[int] = {0}
NOTE_RANGES: dict[int, tuple[int, int]] = {0: (36, 96)}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (1.0, 60.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def _stub(sc: en.Score) -> None:
    """One quiet middle-C whole note — enough for the generic oracles."""
    sc.note(0, 60, 0.0, 4.0, 40)


BUILDERS: list = [_stub]


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    """Track-specific oracles — deliberately red while this is a stub."""
    return [("composed", ["STUB - track not composed yet"])]
