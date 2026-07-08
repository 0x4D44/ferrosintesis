"""movements — the movement builders of *The Burning Meridian*."""

from . import t1
from . import t2
from . import t3


class _M:
    def __init__(self, fn):
        self.build = fn


TRACK1_MODULES = [_M(t1.embers), _M(t1.the_ostinato), _M(t1.the_call),
                  _M(t1.over_the_hill)]
TRACK2_MODULES = [_M(t2.lanterns), _M(t2.duet), _M(t2.swell),
                  _M(t2.ashfall)]
TRACK3_MODULES = [_M(t3.war_footing), _M(t3.cavalry), _M(t3.the_break),
                  _M(t3.charge), _M(t3.daybreak)]

PART_MODULES = {1: TRACK1_MODULES, 2: TRACK2_MODULES, 3: TRACK3_MODULES}
