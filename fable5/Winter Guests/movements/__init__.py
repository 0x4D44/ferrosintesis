"""movements — the six movements of *Winter Guests*, in playing order.

Part One (the cold half) is m1-m3; Part Two (the warm half) is m4-m6.
Each module exposes `build(sc)` and writes notes only inside its
movement's [t0, t1) beat span (see conductor.PART1.MOVEMENTS /
conductor.PART2.MOVEMENTS); the only exceptions are the seam carry-overs
named in the roadmap HLD (section 4).  build.py runs each part's modules
in order and records which notes each one wrote so verify.py can enforce
the bounds.
"""

from . import (m1_frost, m2_humming, m3_footsteps,
               m4_searchlight, m5_ballroom, m6_lastlight)

PART1_MODULES = [m1_frost, m2_humming, m3_footsteps]
PART2_MODULES = [m4_searchlight, m5_ballroom, m6_lastlight]
