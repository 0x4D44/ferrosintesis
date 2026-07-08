"""II. Processional (beats 32-96, bars 9-24) — the lament enters.

HLD section 3, movement II.  Over the intro's ground — continued on ch0
as voice-led pad chords whose voicing picks up EXACTLY where the
verbatim veil's last chord left off — the solo cello sings the 13-note
lament twice (bars 9-16, base A3, DEAD-straight: no vibrato, no bends,
gate 0.99, flat velocity; a lament sung by someone who has stopped
hoping — only CC11 still breathes).  At bar 17 the violin restates the
theme an octave up, still restrained: vibrato is permitted to bloom on
only its two longest notes (the held A5 and the final hanging B4 of the
second statement); the cello walks the collapsing-staircase
countersubject beneath it.  A timpani heartbeat (A2, beats 1 and 3) and
a contrabass pedal A (whole notes) enter with the violin.  Frame tolls
#1 (beat 32) and #2 (beat 64), pp, per the ledger (falling 10->5, base
A3: C5 then E4).

Seam discipline (HLD section 6): ch0 CC11 starts at exactly 90 on beat
32 and nothing earlier (the intro's curve is sacrosanct); ch0 CC74 set
to its section-1-5 value 40; every sustained channel used here gets its
CC11 state at beat 32.  The violin's last vibrato recentres its bend at
beat 95.85, safely before the movement boundary.  Dyn 4-5 of 10: above
the veil, clearly below the First Ascent.
"""

from __future__ import annotations

import engine as en
import material
from conductor import (CH_BELLS, CH_CBASS, CH_CELLO, CH_STRINGS,
                       CH_TIMPANI, CH_VIOLIN)

T0 = 32.0            # bar 9
HALF = 64.0          # bar 17: violin pass; heartbeat and pedal enter
T1 = 96.0

_A2 = en.pitch(material.TONIC, material.MODE, 1) - 12    # timpani A
_A1 = en.pitch(material.TONIC, material.MODE, 1) - 24    # contrabass A


def _intro_final_voicing() -> list[int]:
    """Recompute the verbatim veil's LAST pad voicing (from the engine,
    never hardcoded) so bar 9's chord voice-leads straight out of it."""
    prev = None
    for pcs in material.home_triads() * 2:
        prev = en.voice_lead(pcs, prev, 4, 52, 79)
    return prev


def _ground_pads(sc: en.Score) -> None:
    """pad_block's exact algorithm (span 4, size 4, lo 52, hi 79, tied
    common tones, legato 0.25) with the voice-leading SEEDED from the
    intro's final chord — pad_block cannot take a prev voicing, and a
    fresh call would re-spread bar 9 and dent the seam.  Vel 52->58
    across the movement (dyn 4 rising toward 5)."""
    span, size = 4.0, 4
    prev = _intro_final_voicing()
    voicings: list[list[int]] = []
    for pcs in material.home_triads() * 4:          # bars 9-24
        prev = en.voice_lead(pcs, prev, size, 52, 79)
        voicings.append(prev)
    total = len(voicings) * span
    for vi in range(size):
        i = 0
        while i < len(voicings):
            p = voicings[i][vi]
            j = i
            while j + 1 < len(voicings) and voicings[j + 1][vi] == p:
                j += 1
            vel = int(en.lerp(52, 58, (i * span) / total))
            sc.note(CH_STRINGS, p, T0 + i * span,
                    (j - i + 1) * span + 0.25, vel, jt=4, jv=3)
            i = j + 1


def _toll(sc: en.Score, beat: float, vel_strike: int, vel_answer: int) -> None:
    """One pp ledger toll: the falling 10->5 figure (C5 then E4)."""
    for deg, start, dur in material.TOLL_FALL:
        vel = vel_strike if start == 0.0 else vel_answer
        sc.note(CH_BELLS, en.pitch(material.TONIC, material.MODE, deg),
                beat + start, dur, vel, jt=3, jv=2)


def _lament_arc(t0: float, base: int) -> list[tuple[float, int]]:
    """CC11 breathing for one 16-beat theme statement: a swell into the
    anguish leap, a sag through the descent, dying on the hanging 2."""
    shape = [(0.0, 4), (1.0, 12), (2.5, 16), (4.0, 8), (6.0, 12),
             (8.0, 6), (9.5, 10), (11.0, 8), (12.0, 4), (14.0, 0),
             (15.8, -6)]
    return [(t0 + b, base + d) for b, d in shape]


def build(sc: en.Score) -> None:
    # -- seam state at beat 32 (HLD section 6) ----------------------------
    sc.cc(CH_STRINGS, 74, 40, T0)                 # brightness: veiled
    en.cc_curve(sc, CH_STRINGS, 11, [            # bed breathes around 90
        (32.0, 90), (40.0, 93), (48.0, 88), (56.0, 92), (63.5, 87),
        (64.0, 91), (72.0, 95), (80.0, 90), (88.0, 96), (95.5, 92)],
        step=1.0)
    sc.cc(CH_VIOLIN, 11, 72, T0)                  # idle until bar 17
    sc.cc(CH_CBASS, 11, 78, T0)

    # -- the ground, continued (ch0 pads, bars 9-24) ----------------------
    _ground_pads(sc)

    # -- frame tolls #1 (beat 32) and #2 (beat 64), pp --------------------
    _toll(sc, T0, 44, 36)
    _toll(sc, HALF, 46, 38)

    # -- bars 9-16: the lament, solo cello, dead-straight -----------------
    en.line(sc, CH_CELLO, T0, material.TONIC, material.MODE,
            material.THEME, vel=62, gate=0.99)
    en.line(sc, CH_CELLO, T0 + 16.0, material.TONIC, material.MODE,
            material.THEME, vel=64, gate=0.99)
    cello_cc = (_lament_arc(T0, 72) + _lament_arc(T0 + 16.0, 75)
                # staircase tread under the violin, slowly subsiding
                + [(64.0, 76), (68.0, 80), (72.0, 74), (76.0, 78),
                   (80.0, 72), (84.0, 76), (88.0, 70), (92.0, 74),
                   (95.5, 68)])
    en.cc_curve(sc, CH_CELLO, 11, cello_cc, step=0.5)

    # -- bars 17-24: violin 8va; cello takes the staircase ----------------
    en.line(sc, CH_VIOLIN, HALF, material.TONIC, material.MODE,
            material.THEME, vel=66, octave=1, gate=0.985)
    en.line(sc, CH_VIOLIN, HALF + 16.0, material.TONIC, material.MODE,
            material.THEME, vel=68, octave=1, gate=0.985)
    en.cc_curve(sc, CH_VIOLIN, 11, [
        (63.0, 72),
        (64.0, 76), (65.0, 84), (66.5, 88), (68.0, 90), (70.0, 84),
        (72.0, 86), (73.5, 90), (75.0, 84), (76.0, 88), (78.0, 92),
        (79.7, 80),
        (80.0, 82), (81.0, 90), (82.5, 94), (84.0, 97), (86.0, 90),
        (88.0, 92), (89.5, 96), (91.0, 90), (92.0, 94), (94.0, 99),
        (95.7, 88)], step=0.5)
    # Vibrato blooms ONLY on the restatement's two longest notes: the
    # held A5 (bar 22) and the final hanging B4.  The last one is
    # trimmed to recentre the bend at 95.85 (bend hygiene at beat 96).
    en.vibrato(sc, CH_VIOLIN, 84.0, 1.9, depth=0.20, cycles_per_beat=1.4,
               delay=0.45)
    en.vibrato(sc, CH_VIOLIN, 94.0, 1.85, depth=0.22, cycles_per_beat=1.2,
               delay=0.4)

    en.line(sc, CH_CELLO, HALF, material.TONIC, material.MODE,
            material.COUNTER, vel=56, gate=0.97)
    en.line(sc, CH_CELLO, HALF + 16.0, material.TONIC, material.MODE,
            material.COUNTER, vel=58, gate=0.97)

    # -- heartbeat and pedal from bar 17 -----------------------------------
    for k in range(8):                            # bars 17-24
        bar = HALF + 4.0 * k
        lub = 34 + k // 4                         # grows a hair, late half
        sc.note(CH_TIMPANI, _A2, bar, 0.6, lub, jt=3, jv=2)
        sc.note(CH_TIMPANI, _A2, bar + 2.0, 0.6, lub - 3, jt=3, jv=2)
        sc.note(CH_CBASS, _A1, bar, 3.9, int(en.lerp(39, 42, k / 7)),
                jt=4, jv=2)
