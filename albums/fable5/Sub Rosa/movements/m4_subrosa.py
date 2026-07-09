"""m4_subrosa — Movement 4 "Sub Rosa" (beats 448-576, the breakdown).

The title movement: the groove withdraws to a heartbeat and the piece
speaks under the rose.  The bass walks down a four-stage pedal
(D - C - Bb - A) on long portamento slides; the piano pools arpeggios
under all three pedals at once (sostenuto holding a low D, sustain
pooling each phrase, una corda the whole way); choir II detunes six
cents against choir I so the two voices beat like a cold room; the
whispered text arrives line by line in the lyric lane; a woodblock
taps SUB ROSA in Morse; and the glide lead — bend range widened to 12
semitones — sighs across intervals no default channel could reach.
The final A in the bass leans a half-step up into Limina's opening Bb.

Everything here must be tidied by the seam: portamento off, bend range
back to 2, bends recentred, pedals up.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 448.0, 576.0

BASS_BASE = n("D2")
PHASES = [(448.0, 1), (480.0, 0), (512.0, -1), (544.0, -2)]  # D C Bb A


def _drums(sc):
    # the heartbeat
    beat = T0
    while beat < 568.0:
        sc.hit(36, beat, 58, jv=3)
        sc.hit(36, beat + 1.5, 46, jv=3)
        if int(beat) % 8 == 0:
            sc.hit(37, beat + 3.0, 34, jt=2)       # side-stick tick
        beat += 4.0
    # the Morse woodblock: SUB ROSA (the only woodblock in the window)
    en.morse(sc, "SUB ROSA", 500.0, unit=0.25, drum=76, vel=38)
    # the snare crescendo into Limina
    b = 568.0
    while b < T1 - 1e-9:
        x = (b - 568.0) / 8.0
        sc.hit(38, b, int(lerp(36, 84, x)), jt=2, jv=3)
        b += 0.25


def _bass(sc):
    ch = cd.CH_BASS
    en.portamento_on(sc, ch, 450.0, time_cc=70)
    plan = [(450.0, 1, 7.0), (458.0, 5, 5.0), (464.0, 1, 14.0),
            (482.0, 0, 7.0), (490.0, 4, 5.0), (496.0, 0, 14.0),
            (514.0, -1, 7.0), (522.0, 3, 5.0), (528.0, -1, 14.0),
            (546.0, -2, 7.0), (554.0, 2, 5.0), (560.0, -2, 13.0)]
    for beat, deg, dur in plan:
        sc.note(ch, en.pitch(BASS_BASE, AEO, deg), beat, dur, 56, jt=3, jv=2)
    en.portamento_off(sc, ch, 574.5)


def _piano(sc):
    ch = cd.CH_PIANO
    en.soft_pedal(sc, ch, 449.0, 574.0)            # una corda throughout
    # sostenuto pedal points: a low D caught and held under each half
    for strike, lift in ((452.0, 506.0), (508.0, 570.0)):
        sc.note(ch, n("D2"), strike, 1.5, 52, jt=2)
        en.sostenuto(sc, ch, strike + 0.6, lift)
    # pooled arpeggios, one pool per pedal phase
    for t, root in PHASES:
        en.sustain(sc, ch, t + 8.0, t + 23.5)
        degs = (root + 7, root + 9, root + 11, root + 14, root + 15,
                root + 14, root + 11, root + 9)
        for i, deg in enumerate(degs):
            sc.note(ch, en.pitch(n("D2"), AEO, deg), t + 8.0 + i * 1.5,
                    2.2, 46 - (2 if i % 2 else 0), jt=4, jv=3)


def _choirs(sc):
    ch1, ch2 = cd.CH_CHOIR1, cd.CH_CHOIR2
    en.vowel(sc, ch1, 5, 449.0)
    en.vowel(sc, ch2, 0, 449.0)
    en.fine_tune(sc, ch2, -6.0, 450.0)             # the six-cent beat
    for t, dur in ((452.0, 16.0), (470.0, 14.0), (500.0, 16.0),
                   (530.0, 14.0)):
        sc.note(ch1, n("D4"), t, dur, 48, jt=4, jv=2)
        sc.note(ch2, n("D4"), t + 0.1, dur - 0.2, 46, jt=4, jv=2)
        en.at_curve(sc, ch1, [(t, 0), (t + dur * 0.5, 60), (t + dur, 5)],
                    step=0.5)
    en.fine_tune(sc, ch2, 0.0, 575.0)              # restored at the seam


def _lead(sc):
    ch = cd.CH_LEAD
    en.bend_range(sc, ch, 12, 482.0)
    en.portamento_on(sc, ch, 484.0, time_cc=78)
    sc.cc(ch, 11, 30, 486.0)
    notes = [(488.0, 69, 7.5), (498.0, 67, 8.0), (508.0, 70, 10.0),
             (520.0, 65, 8.0), (530.0, 69, 12.0), (544.0, 72, 10.0),
             (556.0, 67, 8.0)]
    for beat, p, dur in notes:
        sc.note(ch, p, beat, dur, 58, jt=3, jv=2)
        en.expr_curve(sc, ch, [(beat, 30), (beat + dur * 0.6, 72),
                               (beat + dur, 34)], step=0.5)
    # the sighs — intervals only a widened bend range can walk
    en.bend_ramp(sc, ch, 490.0, 494.0, 0.0, 5.0, steps=16)
    en.bend_ramp(sc, ch, 494.6, 495.4, 5.0, 0.0, steps=8)
    sc.bend(ch, 495.7, 0.0)
    en.bend_ramp(sc, ch, 510.0, 516.0, 0.0, 7.0, steps=20)
    en.bend_ramp(sc, ch, 516.2, 517.5, 7.0, 0.0, steps=8)
    sc.bend(ch, 517.8, 0.0)
    en.bend_ramp(sc, ch, 532.0, 536.0, 0.0, -5.0, steps=16)
    en.bend_ramp(sc, ch, 538.0, 540.0, -5.0, 0.0, steps=10)
    sc.bend(ch, 540.4, 0.0)
    en.bend_ramp(sc, ch, 558.0, 561.0, 0.0, 3.0, steps=12)
    en.bend_ramp(sc, ch, 562.0, 563.5, 3.0, -2.0, steps=10)
    en.bend_ramp(sc, ch, 563.7, 564.5, -2.0, 0.0, steps=6)
    sc.bend(ch, 565.0, 0.0)
    en.portamento_off(sc, ch, 570.0)
    en.bend_range(sc, ch, 2, 574.0)                # hygiene at the seam


def _strings(sc):
    ch = cd.CH_STRINGS
    for t, root in PHASES:
        pitches = en.triad(n("D3"), AEO, root)
        for i, p in enumerate(pitches):
            sc.note(ch, p, t + 2.0, 28.0, 46 - i * 2, jt=4, jv=2)
        en.expr_curve(sc, ch, [(t + 2.0, 12), (t + 16.0, 62),
                               (t + 30.0, 16)], step=1.0)


def _whisper(sc):
    ch = cd.CH_WHISPER
    en.vowel(sc, ch, 0, 448.5)                     # closed mouth: the hush
    texts = [(456.0, "sub rosa", 62), (488.0, "in silentio", 62),
             (520.0, "veritas dormit", 69), (552.0, "sub rosa loquimur", 62)]
    for t, text, p in texts:
        sc.note(ch, p, t, 8.0, 42, jt=4, jv=2)
        en.expr_curve(sc, ch, [(t, 0), (t + 4.0, 62), (t + 8.0, 6)],
                      step=0.5)
        en.lyric(sc, t, text)


def _pad(sc):
    ch = cd.CH_PAD
    for t, root in PHASES:
        p0 = en.pitch(n("D3"), AEO, root)
        sc.note(ch, p0, t, 31.5, 42, jt=4, jv=2)
        sc.note(ch, p0 + 7, t, 31.5, 39, jt=4, jv=2)   # open fifth
        en.at_curve(sc, ch, [(t, 0), (t + 16.0, 55), (t + 31.0, 0)],
                    step=0.5)


def _furniture(sc):
    sc.note(cd.CH_BELL, n("D4"), 448.0, 6.0, 56, jt=0, jv=2)
    sc.note(cd.CH_BELL, n("A3"), 544.0, 6.0, 50, jt=3, jv=2)
    ch = cd.CH_CRYSTAL
    for t, deg in ((478.0, 5), (510.0, 4), (542.0, 3)):
        sc.note(ch, en.pitch(n("D5"), AEO, deg), t, 2.5, 44, jt=4, jv=3)
        en.echo_throw(sc, ch, t, base=15, peak=70, release=2.5)
    # the riser: the sequencer sweeps back in under the snare crescendo
    arp = cd.CH_ARP
    en.cc_curve(sc, arp, 74, [(568.0, 20), (575.5, 100)], step=0.5)
    for i in range(12):
        b = 570.0 + i * 0.5
        sc.note(arp, en.pitch(n("D4"), AEO, 1 + (i % 3) * 2), b, 0.45,
                int(lerp(48, 68, i / 11.0)), jt=2, jv=3)


def build(sc):
    _drums(sc)
    _bass(sc)
    _piano(sc)
    _choirs(sc)
    _lead(sc)
    _strings(sc)
    _whisper(sc)
    _pad(sc)
    _furniture(sc)
