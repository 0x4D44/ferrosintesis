"""movements — the eight movement modules of *The Ninth Bell*.

Each module exposes build(sc) and writes note-ons only inside its own
[t0, t1) span from conductor.MOVEMENTS (check_movement_bounds holds it
to that).  The HLD (wrk_docs/2026.07.07 - HLD - The Ninth Bell.md) is
the per-movement spec; the oracles in verify.py are the contract.
"""

from . import m1_veil
from . import m2_processional
from . import m3_ascent
from . import m4_hit
from . import m5_void
from . import m6_tide
from . import m7_toll
from . import m8_embers

MODULES = [m1_veil, m2_processional, m3_ascent, m4_hit,
           m5_void, m6_tide, m7_toll, m8_embers]
