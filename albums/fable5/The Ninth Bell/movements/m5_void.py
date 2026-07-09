"""V. Sotto Voce (beats 132-196) — the void after the hit.

Tempo 63 (conductor).  The E-major slam has just cut to scored silence;
what is left is a music box playing the lament's skeleton to an empty
cathedral.  A dark pad ghosts Am under it (bar 38); at bar 42 the organ's
16' pedal A creeps in ppp while frame toll #5 — a single low A, the
first secret grant of the theme's withheld 1 — answers the music box's
hanging degree 2.  Choir hums "mm" long tones; a harp drops lone notes
like water in a crypt.  Bars 46-47: the Neapolitan Bb triad (pad+choir)
— the alien light — while the cello sighs Bb3->A3 on portamento (the
only glide in the piece; CC65 off again before beat 196).  No vibrato
anywhere: stillness is the fear.

Spec: wrk_docs/2026.07.07 - HLD - The Ninth Bell.md section 3 (§5),
toll ledger section 4 (#5 @164), seam ledger section 6.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_BELLS, CH_CELLO, CH_CHOIR, CH_HARP, CH_MBOX,
                       CH_ORGAN, CH_PAD)

T0 = 132.0
T1 = 196.0

BASE = material.TONIC
MODE = material.MODE

# The lament reduced to its quarter-note skeleton (one-note-per-beat
# feel): material.THEME with the sub-beat passing tones — the flesh —
# stripped away by the void.
SKELETON: list[tuple[int, float, float]] = [
    (5, 0.0, 1.0), (10, 1.0, 2.0), (8, 3.0, 1.0),      # the leap, bare
    (8, 4.0, 2.0), (7, 6.0, 1.0), (6, 7.0, 1.0),       # the descent
    (7, 8.0, 2.0), (5, 11.0, 1.0),                     # the failed turn
    (4, 12.0, 2.0), (2, 14.0, 2.0),                    # hangs on 2
]

# Second pass (beats 148-164): only the spine remains — the theme
# dissolving, notes going missing (the pad ghost holds the air under
# the holes).  Its final degree 2 hangs at beat 162, and the ledger's
# low-A bell (toll #5, beat 164) answers it ppp.
SPINE: list[tuple[int, float, float]] = [
    (5, 0.0, 1.0), (10, 1.0, 3.0),
    (8, 4.0, 2.0), (7, 6.0, 2.0),
    (5, 10.0, 2.0),
    (4, 12.0, 2.0), (2, 14.0, 2.0),
]


def build(sc: en.Score) -> None:
    p = lambda deg: en.pitch(BASE, MODE, deg)

    # -- seam state (HLD section 6): set everything we rely on at T0 ----
    sc.cc(CH_MBOX, 91, 110, T0)          # music box deep in the room
    sc.cc(CH_MBOX, 11, 105, T0)
    sc.cc(CH_PAD, 11, 25, T0)
    sc.cc(CH_ORGAN, 11, 16, T0)          # organ silent until the creep
    sc.cc(CH_ORGAN, 74, 40, T0)          # CC74 stays 40 in sections 1-5
    sc.cc(CH_CHOIR, 11, 14, T0)
    en.vowel(sc, CH_CHOIR, 15, T0)       # CC70=15: closed "mm"
    sc.cc(CH_CELLO, 11, 24, T0)
    sc.cc(CH_CELLO, 65, 0, T0)           # portamento OFF until the sighs
    sc.cc(CH_HARP, 11, 88, T0)
    sc.cc(CH_BELLS, 11, 85, T0)
    sc.cc(CH_BELLS, 91, 118, T0)         # toll #5 rings deep in reverb
    # (organ CC1 is already authoritative at 20 — never touched here;
    #  no vibrato, no bends anywhere in this movement.)

    # -- bars 34-37: music box ALONE, the skeletal lament +12 -----------
    en.sustain(sc, CH_MBOX, T0, T0 + 15.9)                # pedal, phrase 1
    en.line(sc, CH_MBOX, T0, BASE, MODE, SKELETON, vel=32, octave=1)

    # -- bars 38-41: the spine dissolves over the pad ghost -------------
    en.sustain(sc, CH_MBOX, T0 + 16.0, T0 + 31.9)         # pedal, phrase 2
    en.line(sc, CH_MBOX, T0 + 16.0, BASE, MODE, SPINE,
            vel=28, vel_end=23, octave=1)

    # Bar 38 (beat 148): dark pad ghost Am — A2 E3 C4, barely there.
    for gp in (p(-6), p(-2), p(3)):
        sc.note(CH_PAD, gp, 148.0, 15.8, 24, jt=4, jv=2)
    en.expr_curve(sc, CH_PAD,
                  [(148.0, 25), (154.0, 40), (160.0, 33), (163.8, 26)],
                  step=1.0)

    # -- bar 42 (beat 164): the church wakes -----------------------------
    # Frame toll #5: ONE low A (degree 1 = A3), ppp, deep in the tail.
    sc.note(CH_BELLS, p(1), 164.0, 8.0, 28, jt=2, jv=2)

    # Organ 16' pedal A (A1) creeps in pp and holds to the seam.
    sc.note(CH_ORGAN, p(-13), 164.0, 32.3, 32, jt=3, jv=2)
    en.expr_curve(sc, CH_ORGAN,
                  [(164.0, 16), (170.0, 34), (176.0, 40),
                   (190.0, 40), (195.5, 33)], step=1.0)

    # Choir "mm" long tones, phrase-breathed; the Bb bar is the third
    # phrase — the alien light (bars 46-47, with the pad).
    for cp in (p(1), p(5)):                                # A3 + E4
        sc.note(CH_CHOIR, cp, 164.0, 7.8, 30, jt=4, jv=2)
    for cp in (p(1), p(3)):                                # A3 + C4
        sc.note(CH_CHOIR, cp, 172.0, 7.8, 29, jt=4, jv=2)
    for cp in (en.n("Bb3"), en.n("D4"), en.n("F4")):       # Neapolitan
        sc.note(CH_CHOIR, cp, 180.0, 7.8, 29, jt=4, jv=2)
    for cp in (p(1), p(5)):                                # home, fading
        sc.note(CH_CHOIR, cp, 188.0, 8.2, 27, jt=4, jv=2)
    en.expr_curve(sc, CH_CHOIR,
                  [(164.0, 14), (168.0, 30), (172.0, 24), (176.0, 33),
                   (180.0, 26), (184.0, 48), (188.0, 26), (192.0, 32),
                   (195.5, 18)], step=1.0)

    # Pad doubles the Bb triad pp — bars 46-47 only (en.n: chromatic).
    for bp in (en.n("Bb2"), en.n("F3"), en.n("Bb3"), en.n("D4")):
        sc.note(CH_PAD, bp, 180.0, 7.8, 26, jt=4, jv=2)
    en.expr_curve(sc, CH_PAD,
                  [(180.0, 26), (184.0, 44), (188.0, 25)], step=1.0)

    # Harp: lone single notes A/E/C, one every ~2 bars, like water.
    for beat, deg, vel in ((166.0, 15, 40), (174.0, 12, 40),
                           (182.0, 17, 40), (190.0, 8, 38)):
        sc.note(CH_HARP, p(deg), beat, 5.0, vel, jt=3, jv=3)

    # -- bars 44-49: cello phrygian sighs Bb3 -> A3 on portamento --------
    # The ONLY glide in the piece; CC65 back to 0 before beat 196.
    en.portamento_on(sc, CH_CELLO, 171.5, time_cc=70)
    bb3 = en.n("Bb3")
    for t, a_dur in ((172.0, 3.4), (180.0, 3.4), (188.0, 4.5)):
        sc.note(CH_CELLO, bb3, t, 2.1, 38, jt=4, jv=3)
        sc.note(CH_CELLO, p(1), t + 2.0, a_dur, 34, jt=4, jv=3)
    en.portamento_off(sc, CH_CELLO, 195.4)
    en.expr_curve(sc, CH_CELLO,
                  [(171.5, 24), (173.5, 46), (176.5, 22),
                   (180.0, 26), (182.0, 46), (185.5, 22),
                   (188.0, 26), (190.0, 44), (194.5, 15)], step=0.5)
