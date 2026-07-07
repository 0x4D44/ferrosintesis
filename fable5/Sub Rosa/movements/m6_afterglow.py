"""m6_afterglow — Movement 6 "Afterglow" (beats 832-928, rit. from 880).

The cut.  Everything vanishes on the downbeat except the room: drone,
bell, heartbeat.  The chant finally CADENCES — the whole piece it has
hung on its unresolved ninth; here the cadence tail approaches the
tonic from above and below (the subtonic, not a leading tone) and
lands.  The bass makes one last portamento slide home, the pad's
filter closes like a door (CC74 95->28), a final whisper leaves one
word in the lyric lane, and the last bell is left ringing into the
reverb tail as the tempo lets go.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 832.0, 928.0

BASS_BASE = n("D2")
CHANT_BASE = n("D4")


def _room(sc):
    ch = cd.CH_DRONE
    sc.cc(ch, 11, 70, T0)
    for i, p in enumerate((n("D2"), n("A2"), n("D3"))):
        sc.note(ch, p, T0, 94.0, 46 - 3 * i, jt=0, jv=2)
    en.expr_curve(sc, ch, [(T0, 70), (872.0, 55), (920.0, 12)], step=2.0)

    bell = cd.CH_BELL
    sc.note(bell, n("D4"), T0, 8.0, 64, jt=0, jv=2)
    sc.note(bell, n("D3"), 912.0, 8.0, 50, jt=2, jv=2)
    sc.note(bell, n("D4"), 920.0, 6.0, 40, jt=2, jv=2)


def _drums(sc):
    beat = 836.0
    while beat < 880.0:
        sc.hit(36, beat, int(lerp(46, 34, (beat - 836.0) / 44.0)), jv=2)
        sc.hit(36, beat + 1.5, int(lerp(38, 28, (beat - 836.0) / 44.0)),
               jv=2)
        beat += 4.0


def _pad(sc):
    ch = cd.CH_PAD
    voices = [n("D3"), n("F3"), n("A3"), n("E4")]  # the Dm(add9) returns
    for t, dur in ((T0, 30.0), (864.0, 30.0), (896.0, 26.0)):
        for i, p in enumerate(voices):
            sc.note(ch, p, t, dur, 44 - i, jt=4, jv=2)
    en.cc_curve(sc, ch, 74, [(840.0, 95), (920.0, 28)], step=4.0)
    en.at_curve(sc, ch, [(T0, 0), (852.0, 55), (872.0, 0)], step=0.5)


def _choirs(sc):
    ch1, ch2 = cd.CH_CHOIR1, cd.CH_CHOIR2
    # the vowel recedes: ah -> oo -> closed
    en.vowel_curve(sc, ch1, [(834.0, 80), (860.0, 40), (884.0, 8)],
                   step=2.0)
    en.vowel(sc, ch2, 20, 834.0)
    # the cadence: the chant lands for the only time in the piece
    en.line(sc, ch1, 848.0, CHANT_BASE, AEO, m.CHANT_CADENCE, 58,
            vel_end=54, gate=0.97, jt=5, jv=3)
    en.at_curve(sc, ch1, [(848.0, 5), (854.0, 70), (859.5, 5)], step=0.5)
    # then one long tonic hum, the fifth open beneath it
    sc.note(ch1, n("D4"), 864.0, 24.0, 48, jt=4, jv=2)
    sc.note(ch2, n("D3"), 864.0, 22.0, 42, jt=4, jv=2)
    sc.note(ch2, n("A3"), 864.0, 22.0, 40, jt=4, jv=2)
    en.at_curve(sc, ch1, [(864.0, 0), (874.0, 60), (887.0, 0)], step=0.5)


def _bass(sc):
    ch = cd.CH_BASS
    en.portamento_on(sc, ch, 850.0, time_cc=64)
    sc.note(ch, en.pitch(BASS_BASE, AEO, 5), 852.0, 6.0, 48, jt=3, jv=2)
    sc.note(ch, en.pitch(BASS_BASE, AEO, 1), 860.0, 22.0, 46, jt=3, jv=2)
    en.portamento_off(sc, ch, 884.0)


def _piano(sc):
    ch = cd.CH_PIANO
    en.sustain(sc, ch, 880.0, 894.0)
    en.line(sc, ch, 880.0, CHANT_BASE, AEO, m.CHANT_FRAG, 48, vel_end=44,
            gate=0.9, jt=4, jv=3)
    en.sustain(sc, ch, 896.0, 918.0)
    sc.note(ch, n("D2"), 896.0, 20.0, 44, jt=2, jv=2)
    sc.note(ch, n("D3"), 896.0, 20.0, 40, jt=2, jv=2)
    sc.note(ch, n("A3"), 900.0, 16.0, 36, jt=2, jv=2)


def _shaku(sc):
    ch = cd.CH_SHAKU
    sc.note(ch, n("D5"), 868.0, 12.0, 50, jt=3, jv=2)
    en.cc_curve(sc, ch, 1, [(868.5, 0), (874.0, 60), (879.5, 0)],
                step=0.25)
    en.bend_ramp(sc, ch, 878.5, 879.5, 0.0, -1.8, steps=8)
    sc.bend(ch, 880.5, 0.0)
    en.echo_throw(sc, ch, 872.0, base=15, peak=80, release=3.0)


def _glass(sc):
    ch = cd.CH_CRYSTAL
    for t, deg, v in ((856.0, 8, 46), (872.0, 5, 44), (892.0, 4, 41),
                      (904.0, 1, 38)):
        sc.note(ch, en.pitch(n("D5"), AEO, deg), t, 3.0, v, jt=4, jv=2)
        en.echo_throw(sc, ch, t, base=12, peak=68, release=3.0)
    mb = cd.CH_MBOX
    for i, deg in enumerate((1, 3, 5, 8)):
        sc.note(mb, en.pitch(n("D5"), AEO, deg), 884.0 + i * 0.75, 1.5, 42,
                jt=3, jv=2)


def _whisper(sc):
    ch = cd.CH_WHISPER
    en.vowel(sc, ch, 5, 899.0)
    sc.note(ch, n("D4"), 900.0, 10.0, 38, jt=4, jv=2)
    en.expr_curve(sc, ch, [(900.0, 0), (905.0, 55), (910.0, 4)], step=0.5)
    en.lyric(sc, 900.0, "(veritas)")


def build(sc):
    _room(sc)
    _drums(sc)
    _pad(sc)
    _choirs(sc)
    _bass(sc)
    _piano(sc)
    _shaku(sc)
    _glass(sc)
    _whisper(sc)
