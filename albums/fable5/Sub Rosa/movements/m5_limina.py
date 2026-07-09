"""m5_limina — Movement 5 "Limina" (beats 576-832, the widescreen).

Thresholds.  The same chant, but the ground under it is reharmonized
(Bb C Dm Am F Gm Bb C — CLIMAX_GROUND) and the choir finally opens its
mouth: CC70 to full "ah".  Eight 8-bar cycles:

    c0 576  the floor arrives: climax-guise bass, organ Leslie spinning
            up, palm-mute chug, 16th sequencer, piano octave stabs
    c1 608  chant, first full-voice statement; bell tolls the cycle
    c2 640  shakuhachi call and answer, an octave up
    c3 672  chant + choir-II descant (the machine-verified 3rd)
    c4 704  shakuhachi again; ride bell; music-box glitter
    c5 736  chant + descant + strings doubling the chant an octave down
    c6 768  the peak statement; shakuhachi holds bent peak tones
    c7 800  the engine alone: octave-pumping bass, the densest fill,
            a long snare roll — cut dead into the afterglow

The bass's climax guise (octave pops, seven distinct pitches a bar) is
the "melodic bass" brief made law; the movement must carry the piece's
highest mean velocity and its densest notes-per-beat.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 576.0, 832.0
NBARS = int((T1 - T0) // 4)                        # 64
CYCLES = [T0 + 32.0 * k for k in range(8)]

BASS_BASE = n("D2")
CHANT_BASE = n("D4")
SHAKU_BASE = n("D4")
GTR_BASE = n("D3")


def _root(bar: int) -> int:
    return m.CLIMAX_GROUND[bar % 8]


# ---------------------------------------------------------------------------
# drums — the widescreen floor
# ---------------------------------------------------------------------------
def _drums(sc):
    for k, t in enumerate(CYCLES):
        sc.hit(49, t, 100 if k == 0 else 92, jv=2)
    for bar in range(NBARS):
        t = T0 + 4.0 * bar
        grow = bar / (NBARS - 1)
        last_cycle = bar >= 56
        fill_bar = bar % 8 == 7
        for k, beat in enumerate((0.0, 1.0, 2.0, 3.0)):
            sc.hit(36, t + beat, int(lerp(88, 96, grow)) - (0 if k == 0 else 6))
        sc.hit(36, t + 2.75, 74)                   # the lean, every bar now
        if bar % 2 == 1:
            sc.hit(36, t + 1.75, 66)
        for beat in (1.0, 3.0):
            sc.hit(38, t + beat, int(lerp(88, 96, grow)))
            sc.hit(39, t + beat, 68)
        if not fill_bar or last_cycle:
            for s in range(16):
                beat = s * 0.25
                accent = 74 if s % 4 == 2 else (60 if s % 2 == 0 else 48)
                sc.hit(42, t + beat, accent, jt=2, jv=3)
            sc.hit(46, t + 3.75, 66, jt=2)
            if t >= 704.0:
                for beat in (0.0, 2.0):
                    sc.hit(53, t + beat, 62, jt=2)
        if fill_bar and not last_cycle:
            for s, (drum, v) in enumerate(((50, 84), (48, 82), (47, 86),
                                           (45, 88), (43, 92), (41, 96),
                                           (38, 92), (38, 100))):
                sc.hit(drum, t + 2.0 + s * 0.25, v, jt=2)
    # the terminal roll: two bars of gathering snare under the pump
    b = 824.0
    while b < 831.5:
        x = (b - 824.0) / 7.5
        sc.hit(38, b, int(lerp(60, 104, x)), jt=2, jv=3)
        b += 0.25
    sc.hit(49, 831.5, 106, jt=0, jv=2)


# ---------------------------------------------------------------------------
# bass — the climax guise; the final cycle pumps octaves
# ---------------------------------------------------------------------------
def _bass(sc):
    ch = cd.CH_BASS
    for bar in range(NBARS):
        t = T0 + 4.0 * bar
        root = m.bass_root(_root(bar))
        vel = int(lerp(82, 90, bar / (NBARS - 1)))
        last_cycle = bar >= 56
        run_bar = bar % 8 == 7 and not last_cycle
        if last_cycle:
            # octave pump: root/root+7 16ths, accents on the beat
            for s in range(16):
                deg = root + (7 if s % 2 else 0)
                v = vel + (6 if s % 4 == 0 else -4)
                sc.note(ch, en.pitch(BASS_BASE, AEO, deg), t + s * 0.25,
                        0.22, v, jt=1, jv=2)
            continue
        cell = m.bass_riff(root, "climax")
        if run_bar:
            cell = [e for e in cell if e[1] < 2.0]
        for deg, s, dur in cell:
            sc.note(ch, en.pitch(BASS_BASE, AEO, deg), t + s, dur * 0.95,
                    vel, jt=2, jv=3)
        if run_bar:
            en.run(sc, ch, t + 2.0, BASS_BASE, AEO,
                   [root, root + 2, root + 3, root + 4, root + 6, root + 7,
                    root + 9, root + 11],
                   0.25, vel - 6, vel + 10, legato=True)


# ---------------------------------------------------------------------------
# choirs — the chant at full voice; the descant certified in material.py
# ---------------------------------------------------------------------------
def _choirs(sc):
    ch1, ch2 = cd.CH_CHOIR1, cd.CH_CHOIR2
    en.vowel(sc, ch1, 110, 606.0)                  # mouth OPEN
    en.vowel(sc, ch2, 100, 606.0)
    en.vowel(sc, ch2, 100, 671.0)
    statements = [(608.0, 76), (672.0, 80), (736.0, 82), (768.0, 84)]
    for start, vel in statements:
        en.line(sc, ch1, start, CHANT_BASE, AEO, m.CHANT, vel,
                vel_end=vel + 4, gate=0.97, jt=5, jv=3)
        for k in range(4):
            p0 = start + 8.0 * k
            en.at_curve(sc, ch1, [(p0, 10), (p0 + 4.0, 90), (p0 + 7.5, 20)],
                        step=0.5)
    desc = m.descant(m.CLIMAX_GROUND)
    for start in (672.0, 736.0, 768.0):
        en.line(sc, ch2, start, CHANT_BASE, AEO, desc, 70, vel_end=76,
                gate=0.97, jt=5, jv=3)
    # the outro cycle: one long open vowel riding the pump down to earth
    sc.note(ch1, en.pitch(CHANT_BASE, AEO, 8), 800.0, 16.0, 80, jt=4, jv=2)
    sc.note(ch1, en.pitch(CHANT_BASE, AEO, 5), 816.0, 12.0, 74, jt=4, jv=2)
    sc.note(ch2, en.pitch(CHANT_BASE, AEO, 3), 800.0, 16.0, 68, jt=4, jv=2)
    en.at_curve(sc, ch1, [(800.0, 20), (808.0, 95), (824.0, 30)], step=0.5)


# ---------------------------------------------------------------------------
# shakuhachi — high phrases between the chant, bent peak tones at c6
# ---------------------------------------------------------------------------
def _shaku(sc):
    ch = cd.CH_SHAKU
    for t0, phrase in ((640.0, m.SHAKU), (656.0, m.SHAKU_ANSWER),
                       (704.0, m.SHAKU), (720.0, m.SHAKU_ANSWER)):
        en.line(sc, ch, t0, SHAKU_BASE + 12, AEO, phrase, 78, vel_end=84,
                gate=0.97, jt=4, jv=3)
        longest = max(phrase, key=lambda x: x[2])
        h0 = t0 + longest[1]
        en.cc_curve(sc, ch, 1, [(h0, 0), (h0 + longest[2] * 0.7, 75),
                                (h0 + longest[2], 0)], step=0.25)
        en.echo_throw(sc, ch, h0, base=20, peak=85, release=2.0)
        sc.bend(ch, t0 - 0.06, -1.2)               # scooped entries
        en.bend_ramp(sc, ch, t0, t0 + 0.3, -1.2, 0.0, steps=6)
    # c6: two held peak tones, bent up a whole step and released
    for t0, deg in ((776.0, 12), (788.0, 11)):
        sc.note(ch, en.pitch(SHAKU_BASE, AEO, deg), t0, 9.0, 82, jt=3)
        en.cc_curve(sc, ch, 1, [(t0, 0), (t0 + 4.0, 85), (t0 + 9.0, 0)],
                    step=0.25)
        en.bend_ramp(sc, ch, t0 + 2.0, t0 + 4.0, 0.0, 2.0, steps=12)
        en.bend_ramp(sc, ch, t0 + 6.0, t0 + 8.0, 2.0, 0.0, steps=12)
        en.echo_throw(sc, ch, t0 + 3.0, base=20, peak=88, release=2.5)
    sc.bend(ch, 798.5, 0.0)                        # recentred before the pump


# ---------------------------------------------------------------------------
# the harmonic floor — organ (Leslie), pad, strings, chug, piano
# ---------------------------------------------------------------------------
def _organ(sc):
    ch = cd.CH_DRONE
    chords = [en.triad(n("D3"), AEO, _root(bar)) for bar in range(NBARS)]
    en.pad_block(sc, ch, T0, chords, span=4.0, size=3,
                 lo=n("C3"), hi=n("C5"), vel=58, vel_end=66)
    en.leslie(sc, ch, 578.0, 640.0, 8, 127)        # the rotor wakes
    en.cc_curve(sc, ch, 1, [(796.0, 127), (824.0, 36)], step=2.0)


def _pad(sc):
    ch = cd.CH_PAD
    chords = [en.triad(n("D3"), AEO, _root(bar)) for bar in range(NBARS)]
    en.pad_block(sc, ch, T0, chords, span=4.0, size=4,
                 lo=n("G2"), hi=n("G4"), vel=54, vel_end=60)
    for t in CYCLES:
        en.at_curve(sc, ch, [(t, 0), (t + 16.0, 75), (t + 31.0, 0)],
                    step=0.5)


def _strings(sc):
    ch = cd.CH_STRINGS
    chords = [en.triad(n("D4"), AEO, _root(bar)) for bar in range(NBARS)]
    en.pad_block(sc, ch, T0, chords, span=4.0, size=3,
                 lo=n("A3"), hi=n("A5"), vel=62, vel_end=70)
    # c5: the chant doubled an octave below the choir — same skeleton,
    # same chord tones, certified by the material oracle.
    en.line(sc, ch, 736.0, CHANT_BASE - 12, AEO, m.CHANT, 66, vel_end=72,
            gate=0.97, jt=5, jv=3)


def _guitar(sc):
    ch = cd.CH_GUITAR                              # program 28: palm mute
    sc.cc(ch, 74, 108, T0 - 0.2)
    for bar in range(NBARS):
        t = T0 + 4.0 * bar
        root = _root(bar)
        p = en.pitch(GTR_BASE, AEO, root)
        gallop = bar >= 56
        if gallop:
            for s in range(16):
                v = 78 if s % 4 == 0 else 62
                sc.note(ch, p if s % 8 < 6 else p + 7, t + s * 0.25, 0.2,
                        v, jt=2, jv=3)
        else:
            for s in range(8):
                v = 74 if s % 4 == 0 else 62
                sc.note(ch, p, t + s * 0.5, 0.4, v, jt=2, jv=3)


def _piano(sc):
    ch = cd.CH_PIANO
    for bar in range(NBARS):
        t = T0 + 4.0 * bar
        p = en.pitch(n("D4"), AEO, _root(bar))
        for beat in (1.5, 3.5):
            sc.note(ch, p, t + beat, 0.4, 72, jt=3, jv=3)
            sc.note(ch, p + 12, t + beat, 0.4, 66, jt=3, jv=3)


# ---------------------------------------------------------------------------
# glitter — sequencer 16ths, crystal cascades, music box, bells
# ---------------------------------------------------------------------------
def _arp(sc):
    ch = cd.CH_ARP
    sc.cc(ch, 74, 100, T0 - 0.1)
    en.cc_curve(sc, ch, 71, [(576.0, 60), (704.0, 95), (830.0, 70)],
                step=4.0)
    en.autopan(sc, ch, T0, T1 - T0 - 2.0, lo=50, hi=98, period_beats=12.0,
               step=0.25)
    for bar in range(NBARS):
        t = T0 + 4.0 * bar
        root = _root(bar)
        vel = int(lerp(60, 68, bar / (NBARS - 1)))
        for s in range(16):                        # 16th ladder
            ix = m.ARP_PATTERN[s % 8]
            deg = root + m.ARP_LADDER[ix]
            v = vel + (8 if s % 4 == 0 else 0)
            sc.note(ch, en.pitch(n("D4"), AEO, deg), t + s * 0.25, 0.22, v,
                    jt=2, jv=3)


def _glitter(sc):
    cr, mb, bell = cd.CH_CRYSTAL, cd.CH_MBOX, cd.CH_BELL
    for k, t in enumerate(CYCLES):
        root = _root(k * 8)
        if k >= 1:
            for i, step in enumerate((0, 2, 4, 7, 9, 11)):
                sc.note(cr, en.pitch(n("D5"), AEO, root + step), t + i * 0.25,
                        1.2, 62, jt=3, jv=3)
            en.echo_throw(sc, cr, t + 1.0, base=18, peak=82, release=2.0)
        if k >= 4:
            for i, step in enumerate((7, 4, 2, 0)):
                sc.note(mb, en.pitch(n("D5"), AEO, root + step) + 12,
                        t + 2.0 + i * 0.5, 0.8, 54, jt=3, jv=3)
    for t in (608.0, 672.0, 736.0, 768.0, 800.0):
        bar = int((t - T0) // 4)
        sc.note(bell, en.pitch(n("D4"), AEO, _root(bar)), t, 6.0, 78,
                jt=2, jv=2)


def build(sc):
    _drums(sc)
    _bass(sc)
    _choirs(sc)
    _shaku(sc)
    _organ(sc)
    _pad(sc)
    _strings(sc)
    _guitar(sc)
    _piano(sc)
    _arp(sc)
    _glitter(sc)
