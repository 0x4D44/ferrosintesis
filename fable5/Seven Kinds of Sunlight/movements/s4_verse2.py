"""s4_verse2 — "Verse 2" + "Pre-Chorus 2" (beats 184-264).

The verse returns bigger: the piano CANON answers the melody one bar
late a 4th below (machine-verified in material.py), the clean guitar
plays wah-pedal 16th funk, the lead double is detuned -5 cents against
the ooh choir (RPN fine tune), vibes colour the cycle tails, ghost
snares thicken the 7/8.  Pre-chorus 2 adds choir II to the rising
line.
"""

from __future__ import annotations

import parts


def build(sc):
    parts.verse(sc, 184.0, energy=2, canon=True, wah=True,
                detune_lead=True, color=True)
    parts.prechorus(sc, 240.0, energy=2, choir=True)
