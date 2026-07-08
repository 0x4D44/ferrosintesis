"""movements — the seven section builders of *Tuxedo Noir*."""

from . import s


class _M:
    def __init__(self, fn):
        self.build = fn


MODULES = [_M(s.cold_open), _M(s.the_vamp), _M(s.stabs), _M(s.velvet),
           _M(s.the_chase), _M(s.showdown), _M(s.last_cigarette)]
