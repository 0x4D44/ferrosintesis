"""I. The Veil (beats 0-32) — the demo string-chord gesture, VERBATIM.

This is the seed Arthur loves (`demos/orchestral_demo.py` ch0): two
passes of the Am F C G loop, voice-led four-note string chords swelling
out of near-silence on CC11.  The second pass's common-tone voicings
drift into the ambiguous A-C dyad texture — that suspension IS the
sound.  Nothing else may sound here; the intro stays pure (the first
omen, toll #1, falls exactly on this movement's final barline, which
belongs to II).

check_intro_fidelity recomputes this gesture from the engine and holds
this module to it note-for-note.  DO NOT EDIT the parameters.
"""

from __future__ import annotations

import engine as en
import material
from conductor import CH_STRINGS

T0 = 0.0


def build(sc: en.Score) -> None:
    chords = material.home_triads()
    bed = chords + chords                      # two 4-chord passes
    en.pad_block(sc, CH_STRINGS, T0, bed, span=4.0, size=4,
                 lo=52, hi=79, vel=44, vel_end=70)
    en.cc_curve(sc, CH_STRINGS, 11,
                [(0.0, 20), (8.0, 90), (16.0, 105)], step=0.5)
