"""parts.py — the reusable section writers of *Seven Kinds of Sunlight*.

The song states its chorus three times and its verse/pre-chorus twice;
these writers realize them with per-statement options (descant on/off,
vocalise, Leslie, gear-change transposition) so the section modules
stay thin and the arrangement grows the way a record does — each
return adds a layer.

All pitch math goes through `base + semis` so the +2 gear change is a
single argument.
"""

from __future__ import annotations

import conductor as cd
import drums as dr
import engine as en
import material as m
from engine import lerp, n

MODE = m.MODE


def _tri(base: int, root: int) -> list[int]:
    return en.triad(base, MODE, root)


# ---------------------------------------------------------------------------
# THE CHORUS — hook + counter A + counter B (+ descant, vocalise, ...)
# ---------------------------------------------------------------------------

def chorus(sc: en.Score, t0: float, semis: int = 0, energy: int = 2,
           statements: int = 2, descant: bool = False,
           vocalise: bool = False, organ: bool = False,
           vibes: bool = False, leslie: bool = False,
           autopan: bool = False, ride_from: float | None = None,
           syllable_offset: int = 0) -> None:
    hook_base = n("D4") + semis
    bass_base = n("D2") + semis
    b_base = n("D3") + semis
    bars = 8 * statements
    end = t0 + 4.0 * bars

    dr.groove_44(sc, t0, bars, energy=energy, fill_every=4,
                 ride_from=ride_from)
    sc.hit(dr.CRASH, t0, 78 + 8 * energy, jv=2)

    # bass — the driving engine (oracle: root pc on every bar line)
    vel_b = 74 + 4 * energy
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.CHORUS_GROUND[bar % 8]
        for deg, s, dur in m.chorus_bass(root):
            sc.note(cd.CH_BASS, en.pitch(bass_base, MODE, deg), t + s,
                    dur * 0.92, vel_b + (4 if s == 0.0 else 0), jt=1, jv=2)

    # rhythm guitar — power 5ths in 8ths, pushed into each new bar
    vel_g = 68 + 4 * energy
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.CHORUS_GROUND[bar % 8]
        p = en.pitch(n("D3") + semis, MODE, root)
        for s in range(8):
            v = vel_g + (6 if s == 0 else -6 if s % 2 else 0)
            sc.note(cd.CH_GTR, p, t + s * 0.5, 0.45, v, jt=2, jv=3)
            sc.note(cd.CH_GTR, p + 7, t + s * 0.5, 0.45, v - 8, jt=2, jv=3)

    # choir I — the HOOK, full voice, swelling, echoing
    en.vowel(sc, cd.CH_CHOIR1, 115, t0 - 0.5)
    vel_h = 76 + 3 * energy
    for k in range(statements):
        st = t0 + 32.0 * k
        en.line(sc, cd.CH_CHOIR1, st, hook_base, MODE, m.HOOK, vel_h,
                vel_end=vel_h + 5, gate=0.97, jt=4, jv=3)
        for ph in range(4):
            p0 = st + 8.0 * ph
            en.at_curve(sc, cd.CH_CHOIR1,
                        [(p0, 10), (p0 + 4.0, 85), (p0 + 7.5, 15)],
                        step=0.5)
        en.echo_throw(sc, cd.CH_CHOIR1, st + 28.0, base=15, peak=80,
                      release=2.5)
        for i, beat in enumerate((0.0, 8.0, 16.0, 24.0)):
            en.lyric(sc, st + beat,
                     m.SYLLABLES[(i + syllable_offset) % len(m.SYLLABLES)])

    # choir II — the snapped descant
    if descant:
        en.vowel(sc, cd.CH_CHOIR2, 108, t0 - 0.4)
        desc = m.descant()
        for k in range(statements):
            st = t0 + 32.0 * k
            en.line(sc, cd.CH_CHOIR2, st, hook_base, MODE, desc,
                    vel_h - 8, vel_end=vel_h - 3, gate=0.97, jt=4, jv=3)

    # counter A — pulse synth, glock doubling the strong slots
    ca = m.counter_a()
    vel_a = 58 + 3 * energy
    for k in range(statements):
        st = t0 + 32.0 * k
        for deg, s, dur in ca:
            sc.note(cd.CH_ARP, en.pitch(hook_base, MODE, deg), st + s,
                    dur * 0.9, vel_a + (6 if s % 2.0 == 0.0 else 0),
                    jt=2, jv=3)
        for deg, s, dur in ca:
            if s % 2.0 == 0.0:
                sc.note(cd.CH_GLOCK, en.pitch(n("D5") + semis, MODE, deg),
                        st + s, dur, vel_a - 4, jt=2, jv=3)
    if autopan:
        en.autopan(sc, cd.CH_ARP, t0, 4.0 * bars - 2.0, lo=54, hi=98,
                   period_beats=16.0, step=0.25)

    # counter B — strings (and organ double, and the final vocalise)
    cb = m.counter_b()
    for k in range(statements):
        st = t0 + 32.0 * k
        for deg, s, dur in cb:
            p = en.pitch(b_base, MODE, deg)
            sc.note(cd.CH_STRINGS, p, st + s, dur * 1.02, 52 + 3 * energy,
                    jt=3, jv=2)
            if organ:
                sc.note(cd.CH_ORGAN, p, st + s, dur, 48 + 3 * energy,
                        jt=3, jv=2)
            if vocalise:
                sc.note(cd.CH_OOHS, p + 12, st + s, dur, 56 + 2 * energy,
                        jt=3, jv=2)
    if vocalise:
        en.vowel(sc, cd.CH_OOHS, 45, t0 - 0.3)
    if leslie:
        en.leslie(sc, cd.CH_ORGAN, t0 + 2.0, t0 + 30.0, 10, 127)
        en.cc_curve(sc, cd.CH_ORGAN, 1, [(end - 10.0, 127), (end - 1.0, 45)],
                    step=1.0)

    # pad bed + piano off-beat octaves + vibes peal on the repeat
    chords = [_tri(n("D3") + semis, m.CHORUS_GROUND[bar % 8])
              for bar in range(bars)]
    en.pad_block(sc, cd.CH_PAD, t0, chords, span=4.0, size=4,
                 lo=n("G2") + semis, hi=n("G4") + semis,
                 vel=44 + 3 * energy)
    en.at_curve(sc, cd.CH_PAD, [(t0, 0), (t0 + 16.0, 70), (t0 + 31.0, 0)],
                step=0.5)
    for bar in range(bars):
        t = t0 + 4.0 * bar
        root = m.CHORUS_GROUND[bar % 8]
        p = en.pitch(n("D4") + semis, MODE, root)
        for beat in (1.5, 3.5):
            sc.note(cd.CH_PIANO, p, t + beat, 0.4, 58 + 3 * energy, jt=3)
            sc.note(cd.CH_PIANO, p + 12, t + beat, 0.4, 52 + 3 * energy,
                    jt=3)
    if vibes:
        for k in range(statements):
            st = t0 + 32.0 * k + 16.0
            for i, step in enumerate((0, 2, 4, 7, 9, 11)):
                sc.note(cd.CH_VIBES,
                        en.pitch(n("D5") + semis, MODE, 1 + step),
                        st + i * 0.25, 1.5, 56 + 2 * energy, jt=2, jv=3)


# ---------------------------------------------------------------------------
# THE VERSE — 7/8 engine, hummed melody, optional canon / wah / detune
# ---------------------------------------------------------------------------

def verse(sc: en.Score, t0: float, energy: int = 1, canon: bool = False,
          wah: bool = False, detune_lead: bool = False,
          color: bool = False) -> None:
    bars = 16
    end = t0 + 3.5 * bars

    dr.groove_78(sc, t0, bars, energy=energy, fill_every=8)
    sc.hit(dr.CRASH, t0, 74 + 6 * energy, jv=2)

    vel_b = 64 + 4 * energy
    for bar in range(bars):
        t = t0 + 3.5 * bar
        root = m.VERSE_GROUND[bar % 4]
        for deg, s, dur in m.verse_bass(root):
            sc.note(cd.CH_BASS, en.pitch(n("D2"), MODE, deg), t + s,
                    dur * 0.92, vel_b + (4 if s == 0.0 else 0), jt=1, jv=2)

    # the hummed melody: voice oohs closed-mouth, bright lead beneath
    en.vowel(sc, cd.CH_OOHS, 8, t0 - 0.5)
    if detune_lead:
        en.fine_tune(sc, cd.CH_LEAD, -5.0, t0 + 1.5)
    for cyc in range(4):
        st = t0 + 14.0 * cyc
        vel = 52 + 3 * energy + cyc
        en.line(sc, cd.CH_OOHS, st, n("D4"), MODE, m.VERSE_MELODY, vel,
                vel_end=vel + 4, gate=0.96, jt=4, jv=3)
        en.line(sc, cd.CH_LEAD, st, n("D4"), MODE, m.VERSE_MELODY,
                vel - 8, vel_end=vel - 4, gate=0.9, jt=4, jv=3)
        en.at_curve(sc, cd.CH_OOHS, [(st, 0), (st + 7.0, 60),
                                     (st + 13.5, 5)], step=0.5)
    if detune_lead:
        en.fine_tune(sc, cd.CH_LEAD, 0.0, end - 1.5)

    # piano: the CANON in verse 2, plain bar-line chords in verse 1
    if canon:
        cv = m.canon_voice()
        for cyc in range(4):
            st = t0 + 14.0 * cyc
            last = max(s + d for _dg, s, d in cv)
            if st + last > end - 0.5:              # keep the tail inside
                cv_use = [e for e in cv if st + e[1] + e[2] <= end - 0.2]
            else:
                cv_use = cv
            en.line(sc, cd.CH_PIANO, st, n("D4"), MODE, cv_use,
                    50 + 3 * energy, gate=0.94, jt=4, jv=3)
    else:
        for bar in range(0, bars, 2):
            t = t0 + 3.5 * bar
            for i, p in enumerate(_tri(n("D3"), m.VERSE_GROUND[bar % 4])):
                sc.note(cd.CH_PIANO, p, t, 3.2, 46 + 3 * energy - i * 2,
                        jt=3, jv=2)

    # wah funk guitar (verse 2): 16th scratches under the melody
    if wah:
        en.wah(sc, cd.CH_GTR, t0, 3.5 * bars - 2.0, lo=30, hi=105,
               cycles_per_beat=0.25, step=0.5)
        for bar in range(bars):
            t = t0 + 3.5 * bar
            root = m.VERSE_GROUND[bar % 4]
            p = en.pitch(n("D4"), MODE, root)
            for beat in (0.75, 1.25, 2.25, 2.75, 3.25):
                sc.note(cd.CH_GTR, p, t + beat, 0.2,
                        44 + 4 * energy, jt=2, jv=4)

    # pad fifths; vibes colour on the second half of each cycle
    for bar in range(0, bars, 4):
        t = t0 + 3.5 * bar
        p0 = en.pitch(n("D3"), MODE, m.VERSE_GROUND[0])
        sc.note(cd.CH_PAD, p0, t, 13.8, 40 + 2 * energy, jt=3, jv=2)
        sc.note(cd.CH_PAD, p0 + 7, t, 13.8, 37 + 2 * energy, jt=3, jv=2)
    if color:
        for cyc in range(4):
            st = t0 + 14.0 * cyc + 7.0
            root = m.VERSE_GROUND[2]
            for i, step in enumerate((4, 2, 0)):
                sc.note(cd.CH_VIBES, en.pitch(n("D5"), MODE, root + step),
                        st + i * 0.5, 1.2, 48 + 2 * energy, jt=3, jv=3)


# ---------------------------------------------------------------------------
# THE PRE-CHORUS — 6/8 lift: rising melody, climbing toms, riser
# ---------------------------------------------------------------------------

def prechorus(sc: en.Score, t0: float, energy: int = 2,
              choir: bool = False) -> None:
    bars = 8
    end = t0 + 3.0 * bars

    dr.groove_68(sc, t0, bars, energy=energy)
    sc.hit(dr.CRASH2, t0, 70 + 6 * energy, jv=2)

    # bass: dotted-quarter pulses, then an 8th run with hammer-ons
    vel_b = 66 + 4 * energy
    for bar in range(bars - 2):
        t = t0 + 3.0 * bar
        root = m.PRECH_GROUND[bar % 8]
        p = en.pitch(n("D2"), MODE, root)
        sc.note(cd.CH_BASS, p, t, 1.4, vel_b + 4, jt=1, jv=2)
        sc.note(cd.CH_BASS, p, t + 1.5, 1.3, vel_b - 2, jt=1, jv=2)
    run_t = t0 + 3.0 * (bars - 2)
    root = m.PRECH_GROUND[6]
    en.run(sc, cd.CH_BASS, run_t, n("D2"), MODE,
           [root, root + 1, root + 2, root + 3, root + 4, root + 5,
            root + 6, root + 7, root + 8, root + 9, root + 10, root + 11],
           0.5, vel_b - 4, vel_b + 12, legato=True)

    # the rising melody: lead + oohs in octaves (choir joins on PC2)
    vel = 56 + 4 * energy
    en.line(sc, cd.CH_LEAD, t0, n("D4"), MODE, m.PRECH_MELODY, vel,
            vel_end=vel + 10, gate=0.97, jt=3, jv=3)
    en.line(sc, cd.CH_OOHS, t0, n("D4"), MODE, m.PRECH_MELODY, vel - 6,
            vel_end=vel + 2, gate=0.97, jt=4, jv=3)
    if choir:
        en.vowel(sc, cd.CH_CHOIR2, 45, t0 - 0.3)
        en.line(sc, cd.CH_CHOIR2, t0, n("D4"), MODE, m.PRECH_MELODY,
                vel - 10, vel_end=vel - 2, gate=0.97, jt=4, jv=3)

    # strings swell; piano climbing chords; the sequencer riser
    for bar in range(bars):
        t = t0 + 3.0 * bar
        for i, p in enumerate(_tri(n("D3"), m.PRECH_GROUND[bar % 8])):
            sc.note(cd.CH_STRINGS, p, t, 2.9, 46 + 4 * energy - i * 2,
                    jt=3, jv=2)
        for i, p in enumerate(_tri(n("D4"), m.PRECH_GROUND[bar % 8])):
            sc.note(cd.CH_PIANO, p, t + 1.5, 1.3, 50 + 3 * energy + bar,
                    jt=3, jv=3)
    en.expr_curve(sc, cd.CH_STRINGS, [(t0, 40), (end - 1.0, 90)], step=1.0)
    en.cc_curve(sc, cd.CH_ARP, 74, [(t0, 30), (end - 1.0, 100)], step=2.0)
    en.cc_curve(sc, cd.CH_ARP, 71, [(t0, 45), (t0 + 16.0, 85),
                                    (end - 1.0, 60)], step=2.0)
    for s in range(int((3.0 * bars) / 0.5)):
        b = t0 + s * 0.5
        root = m.PRECH_GROUND[int(s // 6) % 8]
        deg = root + (0, 2, 4)[s % 3] + 7
        sc.note(cd.CH_ARP, en.pitch(n("D4"), MODE, deg), b, 0.45,
                int(lerp(46, 66, s / (6.0 * bars))), jt=2, jv=3)
