"""VIII. Embers (beats 356-404, bars 90-101) — the exhale and THE NINTH BELL.

HLD: section 3 (§8 spec), section 4 (toll #9), section 6 (seam states).

After the Bb fracture's scored silence, the piece exhales:

  358      the music box, wrong-footed, whispers the leap cell ONCE —
           the C stumbles in a tenth of a beat early (the void's voice
           has forgotten how to walk).  Choir "mm" (CC70 snapped to 15)
           breathes a long A-E dyad, twice, each breath softer; the
           organ lays a pp 16' A pedal while the Leslie brakes to a
           chorale stop (CC1 90->10 over 356-380).
  364-380  the intro string gesture RETURNS — one pass of Am F C G on
           the same voicing engine as beat 0 — but the CC11 swell runs
           BACKWARDS, (364,90)->(380,15): the breath that opened the
           piece, released.  Timpani heartbeat (A2, beats 1 & 3) fades
           26->14 through bars 92-98 and then simply STOPS — nothing
           after beat 392.  The stopped heart.
  380-398  strings + contrabass hold a bare open fifth A-E, voiced
           low, dying (CC11 -> 10 by 400); two bows, the second
           weaker.  Every non-bell note-on is <= beat 398 and every
           release lands by ~402.
  394-404  THE NINTH BELL (toll #9, the only resolution the piece
           grants): A4 (degree 8), E4 (degree 5), then at 399.5 the
           lone A3 — degree 1, the theme's withheld resolution — the
           very last note-on of the whole piece, thrown into the dark
           with echo_throw under a CC91 tail push.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_BELLS, CH_CBASS, CH_CHOIR, CH_MBOX, CH_ORGAN,
                       CH_STRINGS, CH_TIMPANI)

T0 = 356.0
T1 = 404.0

MODE = material.MODE
TONIC = material.TONIC


def _p(deg: int, octave: int = 0) -> int:
    """Pitch of an A-aeolian degree (base A3 = degree 1), octave-shifted."""
    return en.pitch(TONIC, MODE, deg) + 12 * octave


def build(sc: en.Score) -> None:
    # -- seam state (HLD section 6): set every CC we rely on at T0 ------
    sc.cc(CH_STRINGS, 11, 90, T0)       # entry CC11; reversed curve @364
    sc.cc(CH_STRINGS, 74, 35, T0)       # §8 closes the brightness to 35
    sc.cc(CH_ORGAN, 74, 35, T0)
    sc.cc(CH_ORGAN, 11, 55, T0)
    en.vowel(sc, CH_CHOIR, 15, T0)      # CC70 snapped back to "mm"
    sc.cc(CH_CHOIR, 11, 50, T0)
    sc.cc(CH_CHOIR, 91, 85, T0)         # wash back off the climax push
    sc.cc(CH_CBASS, 11, 40, T0)
    sc.cc(CH_TIMPANI, 11, 90, T0)
    sc.cc(CH_TIMPANI, 91, 60, T0)       # the heartbeat is close and dry
    sc.cc(CH_BELLS, 11, 95, T0)
    sc.cc(CH_BELLS, 91, 100, T0)
    sc.cc(CH_MBOX, 11, 100, T0)
    sc.cc(CH_MBOX, 91, 110, T0)

    # -- Leslie brake: the rotor spins down to a dead chorale stop ------
    en.leslie(sc, CH_ORGAN, T0, 380.0, 90, 10)

    # -- beat 358: the music box, wrong-footed — the leap cell once -----
    # The theme places the 10 a full beat after the 5; here it stumbles
    # in at +0.9, a clockwork mechanism running down.  +12 register.
    en.sustain(sc, CH_MBOX, 357.9, 362.5)
    en.line(sc, CH_MBOX, 358.0, TONIC, MODE,
            [(material.LEAP_CELL[0], 0.0, 1.0),
             (material.LEAP_CELL[1], 0.9, 2.6)],
            vel=30, octave=1)

    # -- choir "mm": long A-E dyad, two breaths, each one softer --------
    for pitch_, v in ((_p(1), 28), (_p(5), 26)):
        sc.note(CH_CHOIR, pitch_, 358.0, 17.5, v, jt=4, jv=3)
    for pitch_, v in ((_p(1), 22), (_p(5), 20)):
        sc.note(CH_CHOIR, pitch_, 376.0, 16.0, v, jt=4, jv=3)
    en.cc_curve(sc, CH_CHOIR, 11,
                [(358.0, 50), (368.0, 40), (375.5, 28),
                 (377.0, 36), (392.0, 10)], step=1.0)     # 2nd intake, fade

    # -- organ: pp 16' low A pedal under the braking rotor, gone by 394 -
    sc.note(CH_ORGAN, _p(1, -2), 358.0, 35.5, 32, jt=4, jv=3)   # A1 -> 393.5
    en.cc_curve(sc, CH_ORGAN, 11,
                [(358.0, 55), (380.0, 32), (393.5, 12)], step=1.0)

    # -- bars 92-95: the intro gesture returns, the swell reversed ------
    # ONE pass of the four home triads, the demo's exact voicing params;
    # CC11 runs (364,90)->(380,15) — the opening breath released — then
    # keeps sinking to 10 by 400 under the dying fifth (HLD §8).
    en.pad_block(sc, CH_STRINGS, 364.0, material.home_triads(), span=4.0,
                 size=4, lo=52, hi=79, vel=40)
    en.cc_curve(sc, CH_STRINGS, 11,
                [(364.0, 90), (380.0, 15), (400.0, 10)], step=0.5)

    # -- timpani heartbeat: A2 on beats 1 & 3, bars 92-98, fading -------
    # vel 26 -> 14, and it simply STOPS: last thump at 390, nothing
    # after beat 392.  jv kept tight so the fade stays legible.
    beats = [364.0 + 4 * bar + off for bar in range(7) for off in (0.0, 2.0)]
    for i, b in enumerate(beats):
        v = round(en.lerp(26.0, 14.0, i / (len(beats) - 1)))
        sc.note(CH_TIMPANI, _p(1, -1), b, 0.5, v, jt=3, jv=2)

    # -- bars 96-101: the bare open fifth, dying (two bows) -------------
    for pitch_, v0, v1 in ((_p(1, -1), 32, 23),      # A2
                           (_p(5, -1), 30, 21),      # E3
                           (_p(1), 28, 20)):         # A3
        sc.note(CH_STRINGS, pitch_, 380.0, 10.0, v0, jt=4, jv=3)
        sc.note(CH_STRINGS, pitch_, 390.0, 8.0, v1, jt=4, jv=3)   # off 398
    sc.note(CH_CBASS, _p(1, -1), 380.0, 18.0, 30, jt=4, jv=3)     # A2 -> 398
    en.cc_curve(sc, CH_CBASS, 11,
                [(380.0, 40), (392.0, 24), (400.0, 10)], step=1.0)

    # -- THE NINTH BELL (toll #9, ledger beat 394): 8, 5, the lone 1 ----
    # CC91 pushed one beat early so the tail blooms into the dark; the
    # lone A3 at 399.5 is the LAST note-on of the entire piece, thrown
    # with echo as it rings past the final barline.
    sc.cc(CH_BELLS, 91, 120, 393.0)
    sc.note(CH_BELLS, _p(8), 394.0, 4.0, 52, jt=3, jv=3)          # A4
    sc.note(CH_BELLS, _p(5), 396.0, 4.0, 48, jt=3, jv=3)          # E4
    sc.note(CH_BELLS, _p(1), 399.5, 5.0, 58, jt=2, jv=2)          # the A
    en.echo_throw(sc, CH_BELLS, 399.5, base=20, peak=85, release=4.0)
