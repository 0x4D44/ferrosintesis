"""movements — the eight section modules of *Seven Kinds of Sunlight*.

Each module exposes build(sc) and writes note-ons only inside its own
span from conductor.MODULE_SPANS (a module may cover two adjacent
sections, e.g. verse + its pre-chorus).
"""

from . import s1_intro
from . import s2_verse1
from . import s3_chorus1
from . import s4_verse2
from . import s5_chorus2
from . import s6_middle8
from . import s7_solo_break
from . import s8_final

MODULES = [s1_intro, s2_verse1, s3_chorus1, s4_verse2, s5_chorus2,
           s6_middle8, s7_solo_break, s8_final]
