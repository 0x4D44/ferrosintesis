"""movements — the six movement modules of *Sub Rosa*, in album order.

Each module exposes build(sc) and writes note-ons only inside its own
[t0, t1) span from conductor.MOVEMENTS (check_movement_bounds holds it
to that).
"""

from . import m1_sigillum
from . import m2_chant
from . import m3_bamboo
from . import m4_subrosa
from . import m5_limina
from . import m6_afterglow

MODULES = [m1_sigillum, m2_chant, m3_bamboo, m4_subrosa, m5_limina,
           m6_afterglow]
