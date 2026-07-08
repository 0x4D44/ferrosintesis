"""IV. The Hit & the Hollow (beats 128-132).  HLD section 3/4.

The ear was promised Am; beat 128 slams a fortissimo E MAJOR chord
instead — one beat, every channel, then nothing.  The chromatic G# is
built from note names (the one licensed departure from the degree
lattice).  Frame toll #4 is the single E bell INSIDE the chord.  Only
the solo cello survives: it strikes E3 and holds ~3.5 beats while a
bend sags 0 -> -0.5 semitones (the life leaving), then the bend is
recentred silently for the hygiene oracle.  No other note-on in beats
129-132: the silence is scored, and the CC91 push from bar 32 lets the
tail bloom into it.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_STRINGS, CH_CELLO, CH_CHOIR, CH_ORGAN, CH_BELLS,
                       CH_TIMPANI, CH_VIOLIN, CH_CBASS, CH_PIANO)

T0, T1 = 128.0, 132.0
# Nominal onset a hair AFTER the downbeat: with jitter, notes at exactly
# 128.0 can land at 127.99 and bleed the hit's energy into bar 32 (both
# the arc oracle and the movement bound want them in bar 33).
HIT = 128.02
D = 1.1                      # every hit note <= 1.2 beats except the cello


def build(sc: en.Score) -> None:
    # ---- seam state (HLD section 6) -----------------------------------
    for ch, v in ((CH_STRINGS, 115), (CH_CHOIR, 115), (CH_ORGAN, 115),
                  (CH_VIOLIN, 115), (CH_CBASS, 112), (CH_PIANO, 115)):
        sc.cc(ch, 11, v, T0 - 0.1)
    sc.cc(CH_STRINGS, 74, 40, T0 - 0.1)
    sc.cc(CH_ORGAN, 74, 40, T0 - 0.1)
    for ch in (CH_BELLS, CH_CHOIR, CH_TIMPANI):
        sc.cc(ch, 91, 127, T0 - 0.1)          # tail stays wide for the bloom

    # Choir mouth snaps open for the stab only, then closes again.
    en.vowel(sc, CH_CHOIR, 105, 127.9)
    en.vowel(sc, CH_CHOIR, 15, 131.0)

    # ---- THE HIT: E major, chromatic G# via note names ------------------
    for p in ("E3", "G#3", "B3", "E4", "G#4", "B4", "E5"):    # full 52-79
        sc.note(CH_STRINGS, en.n(p), HIT, D, 120, jt=2, jv=3)
    for p in ("E5", "G#5", "E6"):
        sc.note(CH_VIOLIN, en.n(p), HIT, D, 118, jt=2, jv=3)
    for p in ("E2", "B2", "E3"):
        sc.note(CH_ORGAN, en.n(p), HIT, D, 118, jt=2, jv=3)
    for p in ("E4", "G#4", "B4", "E5", "G#5"):                # "ah" stab
        sc.note(CH_CHOIR, en.n(p), HIT, D, 117, jt=2, jv=3)
    for p in ("E1", "E2"):
        sc.note(CH_CBASS, en.n(p), HIT, D, 116, jt=2, jv=3)
    for p in ("E1", "E2"):                                    # piano octave
        sc.note(CH_PIANO, en.n(p), HIT, D, 120, jt=2, jv=3)

    # Frame toll #4 (ledger): the single degree-5 bell inside the chord.
    sc.note(CH_BELLS, en.pitch(material.TONIC, material.MODE, 5), HIT,
            1.2, 122, jt=2, jv=2)

    # Timpani E2 roll-flam, choked before the scored silence.
    e2 = en.n("E2")
    for dt, vel, dur in ((0.0, 92, 0.09), (0.08, 120, 0.09),
                         (0.18, 106, 0.09), (0.28, 98, 0.09),
                         (0.38, 94, 0.09), (0.5, 116, 0.3)):
        sc.note(CH_TIMPANI, e2, HIT + dt, dur, vel, jt=1, jv=3)

    # Bass drum + both crashes.
    sc.hit(36, HIT, 122)
    sc.hit(49, HIT, 118)
    sc.hit(57, HIT + 0.02, 114)

    # ---- the hollow: only the cello is left alive -----------------------
    # E3 held ~3.5 beats; the bend sags half a semitone over 129.5-131.5
    # (the life leaving), CC11 dying under it; recentred silently at 131.9
    # (no note sounding) so check_bend_hygiene is clean at beat 132.
    sc.note(CH_CELLO, en.n("E3"), HIT, 3.45, 112, jt=2, jv=2)
    sc.bend(CH_CELLO, HIT, 0.0)
    en.expr_curve(sc, CH_CELLO,
                  [(128.0, 105), (129.5, 88), (131.5, 40)], step=0.25)
    en.bend_ramp(sc, CH_CELLO, 129.5, 131.5, 0.0, -0.5, steps=16)
    sc.bend(CH_CELLO, 131.9, 0.0)
