"""m3_bamboo — Movement 3 "The Bamboo Voice" (beats 256-448, D aeolian).

The flute answers the choir.  The bass moves to its 16th-note drive
guise (the melodic engine of the movement), the guitar's wah pedal
starts breathing (CC74 LFO), and the shakuhachi speaks in strictly
pentatonic phrases — scooped into from below (pitch bends), blooming
into breath vibrato (CC1), thrown down the echo bus at every tail.

    256-272  drive groove establishes; wah begins
    272-304  CALL (SHAKU) ... glass response ... ANSWER (SHAKU_ANSWER)
    304-352  second call, ornamented; strings guide-tones from 320
    352-368  half-time: one long bent tone over a heartbeat
    368-416  rebuild; high statement an octave up; music box doubling
    416-448  high answer; legato bass run and a tom fill into the hush
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 256.0, 448.0

BASS_BASE = n("D2")
SHAKU_BASE = n("D4")
GTR_BASE = n("D3")
CRYSTAL_BASE = n("D6")
PIANO_BASE = n("D4")


def _ground_root(bar: int) -> int:
    return m.CHANT_GROUND[bar % 4]


HALF_TIME = (352.0, 368.0)


def _in_half_time(t: float) -> bool:
    return HALF_TIME[0] - 1e-9 <= t < HALF_TIME[1] - 1e-9


# ---------------------------------------------------------------------------
# drums — the M2 engine, hotter, with a half-time trapdoor
# ---------------------------------------------------------------------------
def _drums(sc):
    sc.hit(49, T0, 100, jv=2)
    nbars = int((T1 - T0) // 4)
    for bar in range(nbars):
        t = T0 + 4.0 * bar
        grow = bar / (nbars - 1)
        if _in_half_time(t):
            sc.hit(36, t, 78)
            sc.hit(38, t + 2.0, 74)
            for beat in (0.5, 1.5, 2.5, 3.5):
                sc.hit(42, t + beat, 36, jt=2, jv=3)
            continue
        fill_bar = bar % 16 == 15
        for k, beat in enumerate((0.0, 1.0, 2.0, 3.0)):
            sc.hit(36, t + beat, int(lerp(84, 92, grow)) - (0 if k == 0 else 8))
        if bar % 2 == 1:
            sc.hit(36, t + 2.75, 68)
        for beat in (1.0, 3.0):
            sc.hit(38, t + beat, int(lerp(82, 90, grow)))
            sc.hit(39, t + beat, 62)
        if not fill_bar:
            for s in range(16):
                beat = s * 0.25
                accent = 64 if s % 4 == 2 else (54 if s % 2 == 0 else 42)
                sc.hit(42, t + beat, accent + int(6 * grow), jt=2, jv=3)
            if bar % 2 == 1:
                sc.hit(46, t + 3.75, 60, jt=2)
            if t >= 384.0 and bar % 2 == 0:
                sc.hit(53, t, 58, jt=2)            # ride bell lean
                sc.hit(53, t + 2.0, 52, jt=2)
        else:
            for s, (drum, v) in enumerate(((50, 78), (48, 76), (47, 80),
                                           (45, 84), (43, 88), (41, 92),
                                           (38, 84), (38, 96))):
                sc.hit(drum, t + 2.0 + s * 0.25, v, jt=2)
    sc.hit(49, 368.0, 96, jv=2)                    # out of the trapdoor
    sc.hit(49, 384.0, 92, jv=2)


# ---------------------------------------------------------------------------
# bass — drive guise; pedal in the half-time; legato runs at the corners
# ---------------------------------------------------------------------------
def _bass(sc):
    ch = cd.CH_BASS
    nbars = int((T1 - T0) // 4)
    for bar in range(nbars):
        t = T0 + 4.0 * bar
        root = m.bass_root(_ground_root(bar))
        if _in_half_time(t):
            sc.note(ch, en.pitch(BASS_BASE, AEO, root), t, 3.8, 66, jt=2)
            continue
        # corner bars carry the legato run instead of the riff tail
        run_bar = bar % 16 == 15
        vel = int(lerp(76, 84, bar / (nbars - 1)))
        cell = m.bass_riff(root, "drive")
        if run_bar:
            cell = [e for e in cell if e[1] < 2.0]
        for deg, s, dur in cell:
            sc.note(ch, en.pitch(BASS_BASE, AEO, deg), t + s, dur * 0.95,
                    vel, jt=2, jv=3)
        if run_bar:
            en.run(sc, ch, t + 2.0, BASS_BASE, AEO,
                   [root, root + 2, root + 3, root + 4, root + 6, root + 7],
                   0.3333, vel - 6, vel + 8, legato=True)


# ---------------------------------------------------------------------------
# shakuhachi — the voice; scoops, vibrato blooms, falls, echo throws
# ---------------------------------------------------------------------------
def _shaku_phrase(sc, t0: float, phrase, vel: int, octave: int = 0,
                  scoop_at: float | None = None, fall: bool = False):
    ch = cd.CH_SHAKU
    en.line(sc, ch, t0, SHAKU_BASE + 12 * octave, AEO, phrase, vel,
            vel_end=vel + 6, gate=0.97, jt=4, jv=3)
    longest = max(phrase, key=lambda x: x[2])
    hold0 = t0 + longest[1]
    hold1 = hold0 + longest[2]
    # breath vibrato blooming through the longest tone
    en.cc_curve(sc, ch, 1, [(hold0, 0), (hold0 + 0.8, 18),
                            (hold1 - 0.3, 78), (hold1 + 0.2, 0)], step=0.25)
    if scoop_at is not None:
        # scooped entry: from 1.5 semis below, landing in a third of a beat
        b = t0 + scoop_at
        sc.bend(ch, b - 0.04, -1.5)
        en.bend_ramp(sc, ch, b, b + 0.35, -1.5, 0.0, steps=8)
    if fall:
        end = t0 + max(s + d for _dg, s, d in phrase)
        en.bend_ramp(sc, ch, end - 0.45, end - 0.05, 0.0, -1.8, steps=8)
        sc.bend(ch, end + 0.1, 0.0)
    en.echo_throw(sc, ch, hold0, base=20, peak=88, release=2.5)


def _shaku(sc):
    ch = cd.CH_SHAKU
    _shaku_phrase(sc, 272.0, m.SHAKU, 72, scoop_at=0.0)
    _shaku_phrase(sc, 304.0, m.SHAKU_ANSWER, 74, scoop_at=0.0)
    _shaku_phrase(sc, 320.0, m.SHAKU, 76, scoop_at=8.0)
    _shaku_phrase(sc, 336.0, m.SHAKU_ANSWER, 76, fall=True)
    # the half-time long tone: A4 held, bent a whole tone up and back
    sc.note(ch, en.pitch(SHAKU_BASE, AEO, 5), 352.5, 13.0, 70, jt=3)
    en.cc_curve(sc, ch, 1, [(353.0, 0), (356.0, 45), (362.0, 85),
                            (365.5, 0)], step=0.25)
    en.bend_ramp(sc, ch, 358.0, 360.0, 0.0, 2.0, steps=12)
    en.bend_ramp(sc, ch, 362.0, 364.0, 2.0, 0.0, steps=12)
    sc.bend(ch, 365.8, 0.0)
    en.echo_throw(sc, ch, 361.0, base=20, peak=90, release=3.0)
    # the high octave statements over the rebuilt groove
    _shaku_phrase(sc, 384.0, m.SHAKU, 78, octave=1, scoop_at=0.0)
    _shaku_phrase(sc, 416.0, m.SHAKU_ANSWER, 80, octave=1, scoop_at=0.0,
                  fall=True)
    # everything recentred well before the seam
    sc.bend(ch, 446.0, 0.0)


# ---------------------------------------------------------------------------
# guitar — the wah pedal breathes all movement; skanks every bar
# ---------------------------------------------------------------------------
def _guitar(sc):
    ch = cd.CH_GUITAR
    en.wah(sc, ch, T0, T1 - T0 - 2.0, lo=35, hi=100, cycles_per_beat=0.125,
           step=0.5)
    nbars = int((T1 - T0) // 4)
    for bar in range(nbars):
        t = T0 + 4.0 * bar
        if _in_half_time(t):
            continue
        root = _ground_root(bar)
        pitches = [en.pitch(GTR_BASE, AEO, root + step) for step in (0, 2, 4)]
        for beat in (0.5, 1.5, 2.5, 3.5):
            for j, p in enumerate(pitches):
                sc.note(ch, p, t + beat, 0.3, 56 - j * 2, jt=3, jv=3)
        if t >= 368.0:                             # 16th double-stop scratch
            for beat in (2.25, 2.75):
                sc.note(ch, pitches[0] + 12, t + beat, 0.2, 48, jt=3)


# ---------------------------------------------------------------------------
# the rest of the room
# ---------------------------------------------------------------------------
def _arp(sc):
    ch = cd.CH_ARP
    sc.cc(ch, 74, 88, 287.0)
    for window in ((288.0, 304.0), (368.0, 448.0)):
        lo, hi = window
        for bar in range(int((hi - lo) // 4)):
            t = lo + 4.0 * bar
            root = _ground_root(bar)
            for slot, (deg, s, dur) in enumerate(m.arp_cell(root)):
                v = 58 + (6 if slot == 0 else 0)
                sc.note(ch, en.pitch(n("D4"), AEO, deg), t + s, dur * 0.9,
                        v, jt=3, jv=3)
    en.autopan(sc, ch, 368.0, 78.0, lo=52, hi=96, period_beats=16.0,
               step=0.25)


def _strings(sc):
    ch = cd.CH_STRINGS
    chords = [en.triad(n("D3"), AEO, _ground_root(bar))
              for bar in range(int((448.0 - 320.0) // 4))]
    en.pad_block(sc, ch, 320.0, chords, span=4.0, size=2,
                 lo=n("G3"), hi=n("G4"), vel=52, vel_end=62)
    en.expr_curve(sc, ch, [(320.0, 40), (352.0, 26), (368.0, 55),
                           (446.0, 75)], step=2.0)


def _crystal(sc):
    ch = cd.CH_CRYSTAL
    # glass answers in the response window and around the high statements
    for start in (288.0, 296.0, 408.0):
        for i, deg in enumerate((8, 7, 5, 4, 3, 1)):
            sc.note(ch, en.pitch(CRYSTAL_BASE - 12, AEO, deg),
                    start + i * 0.5, 0.8, 54, jt=3, jv=3)
        en.echo_throw(sc, ch, start + 2.0, base=18, peak=80, release=2.0)


def _mbox(sc):
    ch = cd.CH_MBOX
    for bar in range(int((448.0 - 384.0) // 4)):   # doubling the ladder top
        t = 384.0 + 4.0 * bar
        root = _ground_root(bar)
        cell = m.arp_cell(root)
        for slot in (3, 7):
            deg, s, dur = cell[slot]
            sc.note(ch, en.pitch(n("D5"), AEO, deg), t + s, dur * 0.9, 50,
                    jt=3, jv=3)


def _piano(sc):
    ch = cd.CH_PIANO
    for t in (368.0, 400.0, 432.0):                # octave lean on the &4
        root = _ground_root(int((t - T0) // 4))
        p = en.pitch(PIANO_BASE, AEO, root)
        for beat in (3.5, 7.5):
            sc.note(ch, p, t + beat, 0.4, 62, jt=3)
            sc.note(ch, p + 12, t + beat, 0.4, 58, jt=3)


def _whisper(sc):
    ch = cd.CH_WHISPER
    en.vowel(sc, ch, 8, 347.0)
    sc.note(ch, n("A4"), 348.0, 6.0, 42, jt=4, jv=2)
    en.expr_curve(sc, ch, [(348.0, 0), (351.0, 60), (354.0, 5)], step=0.5)
    en.lyric(sc, 348.0, "in silentio")


def build(sc):
    _drums(sc)
    _bass(sc)
    _shaku(sc)
    _guitar(sc)
    _arp(sc)
    _strings(sc)
    _crystal(sc)
    _mbox(sc)
    _piano(sc)
    _whisper(sc)
