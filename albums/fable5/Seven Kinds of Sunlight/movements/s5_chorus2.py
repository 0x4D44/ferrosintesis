"""s5_chorus2 — "Chorus 2" (beats 264-328, 4/4, D).

The chorus returns with the choir-II descant over the hook, the organ
doubling counter B, the sequencer autopanning, and vibraphone peals on
the statement repeats.
"""

from __future__ import annotations

import parts


def build(sc):
    parts.chorus(sc, 264.0, semis=0, energy=2, statements=2,
                 descant=True, vocalise=False, organ=True, vibes=True,
                 leslie=False, autopan=True, syllable_offset=1)
