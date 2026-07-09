"""m1_sigillum — Movement 1 "Sigillum" (beats 0-64, D aeolian, 124).

The seal on the letter.  A low organ drone lights first; the pad breathes
over it in aftertouch blooms; a tubular bell tolls three times; glass
droplets fall in the dark.  At 32 the heartbeat starts and the choir hums
the chant's opening fragment with its mouth closed (CC70 = 0).  The bass
slides awake on portamento at 48, and a snare crescendo over the last
four beats throws the doors open into The Chant.

Quietest movement by construction: everything sits in the 35-55 band.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 0.0, 64.0

DRONE_VOICES = [n("D2"), n("A2"), n("D3")]
PAD_VOICES = [n("D3"), n("F3"), n("A3"), n("E4")]   # Dm(add9)
CHOIR_BASE = n("D3")            # 50 — the hum sits low
BASS_BASE = n("D2")             # 38
CRYSTAL_BASE = n("D6")          # 86
BELL_D = n("D4")                # 62


def _drone(sc):
    ch = cd.CH_DRONE
    sc.cc(ch, 11, 0, 0.0)
    for i, p in enumerate(DRONE_VOICES):
        sc.note(ch, p, 0.0, 63.5, 42 - 3 * i, jt=0, jv=2)
    en.expr_curve(sc, ch, [(0.0, 0), (12.0, 46), (56.0, 52), (63.5, 56)],
                  step=1.0)


def _pad(sc):
    ch = cd.CH_PAD
    for phrase in range(4):                       # four 16-beat breaths
        t = phrase * 16.0
        base_v = int(lerp(36, 44, phrase / 3.0))
        for i, p in enumerate(PAD_VOICES):
            sc.note(ch, p, t, 15.7, base_v - i, jt=4, jv=3)
        top = min(T1 - 0.5, t + 15.5)
        en.at_curve(sc, ch, [(t, 0), (t + 8.0, 85), (top, 0)], step=0.5)


def _bell(sc):
    ch = cd.CH_BELL
    for t, v in ((8.0, 48), (24.0, 52), (40.0, 56)):
        sc.note(ch, BELL_D, t, 6.0, v, jt=3, jv=3)
        en.echo_throw(sc, ch, t, base=15, peak=80, release=3.0)


def _crystal(sc):
    ch = cd.CH_CRYSTAL
    # Glass droplets on the pentatonic — sparse, falling, echoing.
    drops = [(12.0, 5), (20.0, 3), (28.0, 4), (36.0, 1), (44.0, 5),
             (52.0, 7), (58.0, 8)]
    for t, deg in drops:
        sc.note(ch, en.pitch(CRYSTAL_BASE, AEO, deg) - 12, t, 2.5,
                int(lerp(40, 50, t / 60.0)), jt=4, jv=3)
        en.echo_throw(sc, ch, t, base=18, peak=75, release=2.0)


def _choir(sc):
    ch = cd.CH_CHOIR1
    en.vowel(sc, ch, 0, 30.0)                    # mouth closed: mm
    en.line(sc, ch, 32.0, CHOIR_BASE, AEO, m.CHANT_FRAG, 46, vel_end=52,
            gate=0.97, jt=5, jv=3)
    en.at_curve(sc, ch, [(33.0, 0), (38.0, 78), (43.5, 12)], step=0.25)
    # A second, longer-held breath of the same fragment an octave up.
    en.line(sc, ch, 48.0, CHOIR_BASE + 12, AEO, m.CHANT_FRAG, 50,
            vel_end=55, gate=0.97, jt=5, jv=3)
    en.at_curve(sc, ch, [(49.0, 0), (54.0, 85), (59.5, 15)], step=0.25)


def _whisper(sc):
    ch = cd.CH_WHISPER
    en.vowel(sc, ch, 8, 14.0)
    sc.cc(ch, 11, 0, 14.0)
    sc.note(ch, n("D4"), 16.0, 13.0, 42, jt=4, jv=2)
    en.expr_curve(sc, ch, [(16.0, 0), (22.0, 68), (29.0, 8)], step=0.5)


def _bass(sc):
    ch = cd.CH_BASS
    en.portamento_on(sc, ch, 46.0, time_cc=62)
    plan = [(48.0, 1, 4.0), (54.0, 5, 2.0), (58.0, 1, 5.0)]
    for beat, deg, dur in plan:
        sc.note(ch, en.pitch(BASS_BASE, AEO, deg), beat, dur,
                int(lerp(44, 50, (beat - 48.0) / 10.0)), jt=3, jv=2)
    en.portamento_off(sc, ch, 63.5)


def _drums(sc):
    # The heartbeat: a soft two-stroke kick figure every two bars.
    beat = 32.0
    while beat < 56.0:
        sc.hit(36, beat, int(lerp(48, 56, (beat - 32.0) / 24.0)), jv=3)
        sc.hit(36, beat + 1.5, 42, jv=3)
        beat += 4.0
    # Doubling pulse under the second choir breath.
    beat = 56.0
    while beat < 60.0:
        sc.hit(36, beat, 56, jv=3)
        beat += 2.0
    # The snare crescendo that opens the doors.
    step = 0.25
    b = 60.0
    while b < T1 - 1e-9:
        x = (b - 60.0) / 4.0
        sc.hit(38, b, int(lerp(30, 68, x)), jt=2, jv=3)
        b += step


def build(sc):
    _drone(sc)
    _pad(sc)
    _bell(sc)
    _crystal(sc)
    _choir(sc)
    _whisper(sc)
    _bass(sc)
    _drums(sc)
