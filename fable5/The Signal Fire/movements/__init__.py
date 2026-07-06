"""movements — the six movements of *The Signal Fire*, in playing order.

Each module exposes `build(sc)` and writes notes only inside its movement's
[t0, t1) beat span (see conductor.MOVEMENTS); the only exceptions are the
seam carry-overs named in the roadmap HLD (section 4).  build.py runs the
MODULES in order and records which notes each one wrote so verify.py can
enforce the bounds.
"""

from . import (m1_signal, m2_ignition, m3_lattice, m4_climb,
               m5_ascension, m6_afterglow)

MODULES = [m1_signal, m2_ignition, m3_lattice, m4_climb,
           m5_ascension, m6_afterglow]
