"""movements — the twelve movement builders of *Heliopause*."""

from . import p1
from . import p2


class _M:
    def __init__(self, fn):
        self.build = fn


PART1_MODULES = [_M(p1.solar_wind), _M(p1.the_sequencer),
                 _M(p1.mirror_waltz), _M(p1.the_drop), _M(p1.two_suns),
                 _M(p1.dissolve)]
PART2_MODULES = [_M(p2.ignition), _M(p2.slipstream), _M(p2.crosswind),
                 _M(p2.eclipse), _M(p2.perihelion), _M(p2.afterimage)]
