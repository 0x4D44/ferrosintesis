"""s8_final — "Final Chorus" + "Outro" (beats 446-542, 4/4, E MAJOR).

The gear change: everything the song owns, up a whole step.  The hook,
the descant, counter A (pulse synth + glock), counter B sung as a
vocalise by the ooh choir AND doubled by strings and rock organ under
a Leslie spin-up, tubular bells instead of vibes, ride from the second
statement, the flute doubling the hook an octave up on the repeat —
the full machine-verified stack.

The outro rides the riff out, punches three stop-time hits, gives the
drummer one last ruff, and lands on a long E-major ring with the bass
sliding home an octave on portamento while the pad's filter closes.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
import parts
from engine import n

MODE = m.MODE
GEAR = 2                        # D -> E
T0, OUT, T1 = 446.0, 510.0, 542.0


def _final_chorus(sc):
    parts.chorus(sc, T0, semis=GEAR, energy=3, statements=2,
                 descant=True, vocalise=True, organ=True, vibes=True,
                 leslie=True, autopan=True, ride_from=478.0,
                 syllable_offset=2)
    # the flute doubles the hook an octave up on the repeat
    en.line(sc, cd.CH_FLUTE, 478.0, n("D5") + GEAR, MODE, m.HOOK, 62,
            vel_end=68, gate=0.95, jt=3, jv=2)


def _outro(sc):
    base4, base5 = n("D4") + GEAR, n("D5") + GEAR
    # three riff bars over the groove
    dr.groove_44(sc, OUT, 3, energy=2, fill_every=0)
    sc.hit(dr.CRASH, OUT, 96, jv=2)
    ca = [e for e in m.counter_a() if e[1] < 12.0]
    for deg, s, dur in ca:
        sc.note(cd.CH_ARP, en.pitch(base4, MODE, deg), OUT + s, dur * 0.9,
                64 + (6 if s % 2.0 == 0.0 else 0), jt=2, jv=3)
        if s % 2.0 == 0.0:
            sc.note(cd.CH_GLOCK, en.pitch(base5, MODE, deg), OUT + s, dur,
                    56, jt=2, jv=3)
    for bar in range(3):
        t = OUT + 4.0 * bar
        root = m.CHORUS_GROUND[bar]
        for deg, s, dur in m.chorus_bass(root):
            sc.note(cd.CH_BASS, en.pitch(n("D2") + GEAR, MODE, deg), t + s,
                    dur * 0.92, 78, jt=1, jv=2)
        p = en.pitch(n("D3") + GEAR, MODE, root)
        for s in range(8):
            sc.note(cd.CH_GTR, p, t + s * 0.5, 0.45, 66 - 6 * (s % 2),
                    jt=2, jv=3)
            sc.note(cd.CH_GTR, p + 7, t + s * 0.5, 0.45, 58 - 6 * (s % 2),
                    jt=2, jv=3)

    # stop-time: three unison punches, ringing across the silence
    for k, (t, dur) in enumerate(((522.0, 1.4), (523.5, 1.4), (525.0, 3.0))):
        v = 88 + 4 * k
        sc.note(cd.CH_BASS, n("E2"), t, dur, v, jt=1, jv=2)
        sc.note(cd.CH_GTR, n("E3"), t, dur, v - 4, jt=1, jv=2)
        sc.note(cd.CH_GTR, n("B3"), t, dur, v - 10, jt=1, jv=2)
        sc.note(cd.CH_PIANO, n("E4"), t, dur, v - 4, jt=1, jv=2)
        sc.note(cd.CH_PIANO, n("E5"), t, dur, v - 10, jt=1, jv=2)
        sc.hit(dr.K, t, v + 8)
        sc.hit(dr.CRASH if k == 2 else dr.CRASH2, t, v + 6, jv=2)
    dr.fill(sc, 528.0, 2.0, "ruff", vel=84)        # the drummer's last word

    # the long ring: E major, everything sustaining, the door closing
    T = 530.0
    sc.hit(dr.CRASH, T, 104, jv=2)
    sc.hit(dr.SPLASH, T + 2.0, 66, jv=2)
    en.vowel(sc, cd.CH_CHOIR1, 105, T - 0.3)
    sc.note(cd.CH_CHOIR1, n("E4"), T, 8.0, 74, jt=2, jv=2)
    sc.note(cd.CH_CHOIR1, n("B4"), T, 8.0, 68, jt=2, jv=2)
    sc.note(cd.CH_CHOIR2, n("G#4"), T, 8.0, 62, jt=2, jv=2)
    en.at_curve(sc, cd.CH_CHOIR1, [(T, 20), (T + 3.0, 85), (T + 8.0, 0)],
                step=0.5)
    for i, p in enumerate((n("E3"), n("B3"), n("E4"), n("G#4"))):
        sc.note(cd.CH_STRINGS, p, T, 9.0, 62 - i * 3, jt=2, jv=2)
        sc.note(cd.CH_ORGAN, p, T, 8.5, 56 - i * 3, jt=2, jv=2)
    for i, p in enumerate((n("E2"), n("E3"), n("B3"), n("E4"))):
        sc.note(cd.CH_PAD, p, T, 10.0, 52 - i * 2, jt=2, jv=2)
    sc.note(cd.CH_GTR, n("E3"), T, 6.0, 78, jt=1, jv=2)
    sc.note(cd.CH_GTR, n("B3"), T, 6.0, 70, jt=1, jv=2)
    en.sustain(sc, cd.CH_PIANO, T - 0.1, T + 10.0)
    sc.note(cd.CH_PIANO, n("E2"), T, 9.0, 66, jt=1, jv=2)
    sc.note(cd.CH_PIANO, n("E4"), T, 9.0, 60, jt=1, jv=2)
    sc.note(cd.CH_VIBES, n("E4"), T, 8.0, 70, jt=1, jv=2)   # tubular bell
    sc.note(cd.CH_VIBES, n("E3"), T + 4.0, 6.0, 56, jt=2, jv=2)
    for i, deg in enumerate((1, 3, 5, 8)):
        sc.note(cd.CH_GLOCK, en.pitch(base5, MODE, deg), T + 0.5 + i * 0.4,
                2.0, 58 - i * 3, jt=2, jv=2)
    en.lyric(sc, T, "(oh)")

    # the bass slides home an octave; the pad's filter closes the door
    sc.note(cd.CH_BASS, n("E2"), T, 3.5, 70, jt=1, jv=2)
    en.portamento_on(sc, cd.CH_BASS, T + 3.0, time_cc=70)
    sc.note(cd.CH_BASS, n("E1"), T + 4.0, 6.0, 58, jt=1, jv=2)
    en.portamento_off(sc, cd.CH_BASS, T + 11.0)
    en.cc_curve(sc, cd.CH_PAD, 74, [(512.0, 95), (528.0, 72),
                                    (T + 10.0, 28)], step=2.0)
    en.expr_curve(sc, cd.CH_PAD, [(T, 90), (T + 10.0, 30)], step=1.0)


def build(sc):
    _final_chorus(sc)
    _outro(sc)
