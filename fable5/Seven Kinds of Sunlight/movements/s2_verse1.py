"""s2_verse1 — "Verse 1" + "Pre-Chorus 1" (beats 32-112).

The 7/8 engine arrives (3+2+2), the melody hummed closed-mouth by the
voice-ooh choir with the bright lead underneath, plain piano chords on
the bar lines.  At 88 the 6/8 pre-chorus lifts: rising melody, toms
climbing the kit, string swell, the sequencer riser, and a legato bass
run into the first chorus.
"""

from __future__ import annotations

import parts


def build(sc):
    parts.verse(sc, 32.0, energy=1, canon=False, wah=False,
                detune_lead=False, color=False)
    parts.prechorus(sc, 88.0, energy=2, choir=False)
