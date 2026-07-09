"""s7_solo_break — "Guitar Solo" + "Drum Break" (beats 368-446).

The solo: sixteen bars of 7/8 under a distorted lead with its bend
range widened to 12 semitones (RPN 0) — hammered runs (CC68), unison
bends blooming into wheel vibrato (CC1), a quote of the verse melody
an octave up, a rising pre-chorus sequence, and a full-octave-minus-a-
step WHAMMY DIVE (-7) out of the last held note.  Palm-mute chug,
drive bass and organ pads carry the floor.

The break: the band punches unison stabs on the first two 7/8 bars,
then leaves the drummer alone with the fill library — kick16, cascade,
ruff — flips to 4/4 half-time power hits, and builds a snare roll and
sequencer riser into the gear-changed final chorus.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
from engine import lerp, n

MODE = m.MODE
T0 = 368.0
BREAK = 424.0
T1 = 446.0


# ---------------------------------------------------------------------------
# the floor under the solo
# ---------------------------------------------------------------------------
def _backing(sc):
    dr.groove_78(sc, T0, 16, energy=3, fill_every=8)
    sc.hit(dr.CRASH, T0, 96, jv=2)
    for bar in range(16):
        t = T0 + 3.5 * bar
        root = m.VERSE_GROUND[bar % 4]
        for deg, s, dur in m.verse_bass(root):
            sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, deg), t + s,
                    dur * 0.92, 78 + (4 if s == 0.0 else 0), jt=1, jv=2)
        p = en.pitch(n("D3"), MODE, root)                # palm-mute chug
        for s in range(7):
            v = 72 if s in (0, 3, 5) else 60
            sc.note(cd.CH_GTR, p, t + s * 0.5, 0.4, v, jt=2, jv=3)
        for i, pp in enumerate(en.triad(n("D3"), MODE, root)):
            sc.note(cd.CH_ORGAN, pp, t, 3.4, 50 - i * 2, jt=3, jv=2)


# ---------------------------------------------------------------------------
# the solo itself
# ---------------------------------------------------------------------------
SOLO_RANGE = 12.0


def _w(semis: float) -> float:
    """Semitones -> sc.bend argument under the widened RPN range.
    sc.bend maps its argument as arg/2 = fraction of the range in
    force, so arg = 2 * semis / range (the Winter Guests convention).
    Passing raw semitones here would clamp -7 into a full -12."""
    return 2.0 * semis / SOLO_RANGE


def _hold(sc, t: float, deg: int, dur: float, vel: int,
          bend_up: float = 0.0, vib: int = 70) -> None:
    """A held solo tone: optional bend up `bend_up` SEMITONES early in
    the note (while the plucked string is still loud — KS voices
    decay), wheel vibrato blooming through the tail, recentred."""
    ch = cd.CH_SOLO
    sc.note(ch, en.pitch(n("D4"), MODE, deg), t, dur, vel, jt=2, jv=2)
    if bend_up:
        en.bend_ramp(sc, ch, t + 0.15, t + dur * 0.4, 0.0, _w(bend_up),
                     steps=10)
        en.bend_ramp(sc, ch, t + dur * 0.5, t + dur * 0.75, _w(bend_up),
                     0.0, steps=8)
    en.cc_curve(sc, ch, 1, [(t + dur * 0.3, 0), (t + dur * 0.8, vib),
                            (t + dur, 0)], step=0.25)
    sc.bend(ch, t + dur + 0.05, 0.0)


def _solo(sc):
    ch = cd.CH_SOLO
    en.bend_range(sc, ch, 12, 370.0)

    # P1 (368-382): hammered scale rocket into a held, bent D5
    en.run(sc, ch, 368.5, n("D4"), MODE, [1, 2, 3, 4, 5, 6, 7, 8],
           0.25, 66, 86, legato=True)
    _hold(sc, 370.5, 8, 3.0, 88, bend_up=2.0)
    en.line(sc, ch, 375.0, n("D4"), MODE,
            [(8, 0, 0.5), (7, 0.5, 0.5), (5, 1.0, 1.0), (6, 2.0, 0.5),
             (5, 2.5, 0.5), (4, 3.0, 0.5), (5, 3.5, 2.0)],
            80, gate=0.95, jt=2, jv=2)
    en.echo_throw(sc, ch, 372.0, base=15, peak=75, release=2.0)

    # P2 (382-396): the verse melody quoted an octave up
    en.line(sc, ch, 382.0, n("D4") + 12, MODE, m.VERSE_MELODY, 82,
            vel_end=88, gate=0.94, jt=2, jv=2)

    # P3 (396-410): rising pre-chorus sequence with octave answers
    seq = [(4, 0, 1), (4 + 7, 1, 0.5), (5, 1.5, 1), (5 + 7, 2.5, 0.5),
           (6, 3.5, 1), (6 + 7, 4.5, 0.5), (7, 5.5, 1), (7 + 7, 6.5, 0.5),
           (8, 7.0, 1.5), (9, 8.5, 1), (8, 9.5, 0.5), (9, 10.5, 1.5),
           (10, 12.0, 2.0)]
    en.line(sc, ch, 396.0, n("D4"), MODE, seq, 82, vel_end=90,
            gate=0.95, jt=2, jv=2)
    _hold(sc, 410.0, 11, 3.0, 92, bend_up=2.0, vib=85)

    # P4 (413-424): peak and the whammy dive out
    en.run(sc, ch, 413.5, n("D4"), MODE, [11, 10, 9, 8, 7, 6, 5, 4],
           0.25, 88, 74, legato=True)
    _hold(sc, 415.5, 8, 2.5, 86)
    sc.note(ch, en.pitch(n("D4"), MODE, 8), 418.5, 1.8, 90, jt=2, jv=2)
    en.cc_curve(sc, ch, 1, [(419.0, 0), (420.0, 80), (420.3, 0)],
                step=0.25)
    # the DIVE: re-strike so the string is loud while it falls, then
    # -7 real semitones over ~1.7 beats and a quick rip back to pitch
    sc.note(ch, en.pitch(n("D4"), MODE, 8), 420.4, 3.0, 96, jt=1, jv=2)
    en.bend_ramp(sc, ch, 420.6, 421.7, 0.0, _w(-7.0), steps=14)
    en.bend_ramp(sc, ch, 422.2, 422.8, _w(-7.0), 0.0, steps=6)
    sc.bend(ch, 423.2, 0.0)
    en.bend_range(sc, ch, 2, 425.0)                # hygiene before the break


# ---------------------------------------------------------------------------
# the drum break
# ---------------------------------------------------------------------------
def _stab(sc, t: float, vel: int) -> None:
    """Band unison stab on the tonic (the drummer owns everything else)."""
    sc.note(cd.CH_BASS, n("D2"), t, 0.6, vel + 6, jt=1, jv=2)
    p = n("D3")
    sc.note(cd.CH_GTR, p, t, 0.5, vel, jt=1, jv=2)
    sc.note(cd.CH_GTR, p + 7, t, 0.5, vel - 6, jt=1, jv=2)
    sc.note(cd.CH_PIANO, n("D4"), t, 0.5, vel, jt=1, jv=2)
    sc.note(cd.CH_PIANO, n("D5"), t, 0.5, vel - 6, jt=1, jv=2)
    for i, pp in enumerate(en.triad(n("D3"), MODE, 1)):
        sc.note(cd.CH_ORGAN, pp, t, 0.6, vel - 4 - i * 2, jt=1, jv=2)


def _break(sc):
    # two stabbed 7/8 bars: the band answers the kit
    for t, v in ((BREAK, 92), (BREAK + 1.5, 84), (BREAK + 2.5, 86),
                 (BREAK + 3.5, 94), (BREAK + 5.0, 86), (BREAK + 6.0, 88)):
        _stab(sc, t, v)
    sc.hit(dr.CRASH, BREAK, 100, jv=2)
    sc.hit(dr.K, BREAK, 100)
    sc.hit(dr.K, BREAK + 1.5, 92)
    sc.hit(dr.SN, BREAK + 2.5, 96)
    dr.fill(sc, BREAK + 3.5, 3.5, "kick16", vel=92)
    # the drummer alone: cascade, then ruff
    dr.fill(sc, 431.0, 3.5, "cascade", vel=94)
    sc.hit(dr.CRASH2, 434.5, 98, jv=2)
    dr.fill(sc, 434.5, 3.5, "ruff", vel=92)
    # 4/4 half-time power hits, then the build
    sc.hit(dr.CRASH, 438.0, 102, jv=2)
    sc.hit(dr.K, 438.0, 102)
    _stab(sc, 438.0, 96)
    # let the power hit RING across the half-time bar (also closes the
    # only all-channel gap in the piece)
    sc.note(cd.CH_ORGAN, n("D3"), 438.0, 2.2, 74, jt=1, jv=2)
    sc.note(cd.CH_ORGAN, n("A3"), 438.0, 2.2, 68, jt=1, jv=2)
    sc.note(cd.CH_BASS, n("D2"), 438.8, 1.4, 72, jt=1, jv=2)
    sc.hit(dr.SN, 440.0, 100)
    dr.fill(sc, 440.5, 1.5, "scatter", vel=88)
    b = 442.0
    while b < 445.9:
        sc.hit(dr.K, b, 90, jt=1)
        b += 0.5
    dr.snare_build(sc, 442.0, 445.9, 60, 106, step=0.25)
    en.cc_curve(sc, cd.CH_ARP, 74, [(442.0, 25), (445.8, 105)], step=0.5)
    for i in range(8):
        sc.note(cd.CH_ARP, en.pitch(n("D4"), MODE, 1 + (i % 4) * 2),
                442.0 + i * 0.5, 0.45, int(lerp(52, 74, i / 7.0)),
                jt=1, jv=2)


def build(sc):
    _backing(sc)
    _solo(sc)
    _break(sc)
