"""III. First Ascent (beats 96-128) — the build.  HLD section 3.

Frame toll #3 (mf) opens it.  The organ's 16' pedal (A1+E2, rotor
authoritatively SLOW: first CC1 event on ch3 = 20) and the choir's
closed-mouth hum (CC70=15) slide in under the ground; the ch0 strings
abandon the pads for pulsing quavers on the same voice-led chords
(vel 60->92); the violin sequences the anguish leap upward one step
per two bars (5-10, 6-11, 7-12) while the cello keeps collapsing down
the staircase and the contrabass walks the lament tetrachord onto the
dominant.  Bars 31-32: timpani roll crescendo, CC91 bloom on
bells/choir/timpani 110->127 — every arrow points at a triumphant Am
downbeat at bar 33 that never comes.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_STRINGS, CH_CELLO, CH_CHOIR, CH_ORGAN, CH_BELLS,
                       CH_TIMPANI, CH_VIOLIN, CH_CBASS)

T0, T1 = 96.0, 128.0
BASE = material.TONIC
MODE = material.MODE


def build(sc: en.Score) -> None:
    # ---- seam state (HLD section 6) -----------------------------------
    # Organ: the FIRST CC1 event anywhere on ch3 must be 20 (slow rotor)
    # and must precede its first note; choir mouth closed before the hum.
    sc.cc(CH_ORGAN, 1, 20, T0 - 0.1)
    sc.cc(CH_ORGAN, 74, 40, T0 - 0.1)
    sc.cc(CH_STRINGS, 74, 40, T0)
    en.vowel(sc, CH_CHOIR, 15, T0 - 0.1)

    # CC11 beds 70 -> 115 across the ascent (HLD section 3); the cello's
    # lane rises less — it is the voice collapsing, not the tide.
    for ch in (CH_STRINGS, CH_CHOIR, CH_ORGAN, CH_CBASS):
        en.expr_curve(sc, ch, [(T0, 70), (T1, 115)], step=1.0)
    en.expr_curve(sc, CH_CELLO, [(T0, 70), (112.0, 85), (T1, 100)], step=1.0)

    # ---- frame toll #3 (ledger): the falling 10->5, mf ------------------
    en.line(sc, CH_BELLS, T0, BASE, MODE, material.TOLL_FALL, vel=78,
            jt=3, jv=3)

    # ---- ch0 strings: the ground becomes pulsing quavers ---------------
    # Same voice-led voicings as the intro pads (voice_lead from None is
    # deterministic), now struck as urgent eighths, vel ramp 60 -> 92.
    voicings, prev = [], None
    for pcs in material.home_triads() + material.home_triads():
        prev = en.voice_lead(pcs, prev, 4, 52, 79)
        voicings.append(prev)
    for bar, voicing in enumerate(voicings):
        for q in range(8):
            t = T0 + bar * 4.0 + q * 0.5
            vel = int(en.lerp(60, 92, (t - T0) / (T1 - T0)))
            if q % 2 == 0:
                vel += 4                      # on-beat accents drive the pulse
            for p in voicing:
                sc.note(CH_STRINGS, p, t, 0.34, vel, jt=4, jv=3)

    # ---- cello: the collapsing staircase, twice, rising in weight ------
    en.line(sc, CH_CELLO, T0, BASE, MODE, material.COUNTER,
            vel=62, vel_end=72)
    en.line(sc, CH_CELLO, T0 + 16.0, BASE, MODE, material.COUNTER,
            vel=70, vel_end=80)

    # ---- violin: the anguish leap sequenced upward ----------------------
    # bar 27: 5-10, bar 29: 6-11, bar 31: 7-12; the last held note is the
    # E that the hit chord will keep — the betrayal sounds UNDER the theme.
    for t, d1, d2, hold, vel, depth in (
            (104.0, 5, 10, 2.45, 90, 0.20),
            (112.0, 6, 11, 2.45, 98, 0.24),
            (120.0, 7, 12, 6.85, 104, 0.30)):
        sc.note(CH_VIOLIN, en.pitch(BASE, MODE, d1) + 12, t, 0.95, vel, jt=4)
        sc.note(CH_VIOLIN, en.pitch(BASE, MODE, d2) + 12, t + 1.0, hold,
                vel + 6, jt=4)
        en.vibrato(sc, CH_VIOLIN, t + 1.0, hold - 0.05, depth=depth,
                   delay=0.6)
    en.expr_curve(sc, CH_VIOLIN, [
        (96.0, 80), (104.0, 84), (106.0, 98), (107.5, 100), (109.0, 80),
        (112.0, 88), (114.0, 104), (115.5, 106), (117.0, 84),
        (120.0, 96), (124.0, 110), (127.7, 120)], step=0.5)

    # ---- organ: 16' pedal A1 + E2, re-bowed every two bars --------------
    pedal = (en.pitch(BASE, MODE, 1) - 24, en.pitch(BASE, MODE, 5) - 24)
    for i in range(4):
        for p in pedal:
            sc.note(CH_ORGAN, p, T0 + i * 8.0, 7.9, 56 + i * 5, jt=3, jv=2)

    # ---- choir: closed-mouth hum on the ground, entering a bar late ----
    tri = material.home_triads()
    hum_prev = None
    for bar in range(8):
        hum_prev = en.voice_lead(tri[bar % 4], hum_prev, 3, 57, 76)
        if bar == 0:
            continue                          # the hum steals in at bar 26
        vel = int(en.lerp(56, 78, bar / 7.0))
        for p in hum_prev:
            sc.note(CH_CHOIR, p, T0 + bar * 4.0, 4.1, vel, jt=6, jv=3)

    # ---- contrabass: the lament tetrachord, one note per two bars ------
    # A2 G2 F2 E2 — landing on the dominant that bar 33 will weaponise.
    for i, deg in enumerate(material.TETRACHORD_DEGS):
        sc.note(CH_CBASS, en.pitch(BASE, MODE, deg) - 12, T0 + i * 8.0,
                7.9, 52 + i * 3, jv=3)

    # ---- bars 31-32: timpani roll crescendo + the pre-hit CC91 bloom ---
    a2 = en.pitch(BASE, MODE, 1) - 12
    for k in range(32):
        sc.note(CH_TIMPANI, a2, 120.0 + k * 0.25, 0.22,
                int(en.lerp(50, 110, k / 31.0)), jt=2, jv=3)
    for ch in (CH_BELLS, CH_CHOIR, CH_TIMPANI):
        en.cc_curve(sc, ch, 91, [(124.0, 110), (128.0, 127)], step=0.5)
