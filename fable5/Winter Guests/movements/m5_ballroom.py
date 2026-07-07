"""m5_ballroom — Part Two, Movement 5 "The Glass Ballroom"
(beats 448-896, E ionian, 118).  The apotheosis: THE densest, loudest
movement, where all three guises of the Guest theme sound AT ONCE.

Roadmap section 4, M5:

  ch12 (30) violining entries in the build, then the GUITAR GUISE
        ornamented with machine-gun run() bursts figurating between the
        voices; ch13 = the ABBA DOUBLE — fine_tune(+8c) at 448, hard-split
        pans (ch12->20 L, ch13->108 R), mirrors ch12 at vel-8 (honest
        double-tracking; the +8c beat is the width, bends stay free).
  ch15 tubular bells: THEME AUGMENTED x2 pealing from 512 (base E), octave
        doubles in the second peal.
  ch11 choir II sings the HUM GUISE low (vowel mm, CC70=0) as a counterline
        while ch6 choir I answers with CHORUS_GUISE stacks at vowel ah — so
        all three guises sound together: bells=theme augmented, ch6=chorus
        stack, ch11=low hum, guitars figurate between.
  ch4 full organ (18 @448), CC1 Leslie ramps into each 32-beat peak;
        ch14 fiddle reel-flavoured 8th-note countermelody (the Oldfield
        wink).

Structure:
  448-512  build   — the disco vamp continues, guitars assemble (violining)
  512-640  peal 1  — bells peal, choir stacks + low hum, full band
  640-704  break   — choirs + bells only, pad + aftertouch swells breathing
  704-832  peal 2  — full: piano glitter, bell octave doubles, drum fills
  832-880  cadence — the big IV-V-I(sus) over the four-on-floor
  880-896  full stop at 884 EXCEPT the ch1 pad chord + ch15 final bell
           ringing on (CC91 -> 90 on both — the ballroom recedes)

CC91 ~35 on every channel at 448 (closest/driest of the whole piece).
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

ION = "ionian"

T0, T1 = 448.0, 896.0
PEAL1, BREAK, PEAL2, CADENCE, STOP = 512.0, 640.0, 704.0, 832.0, 880.0

# ---------------------------------------------------------------------------
# Degree-1 anchors (E ionian throughout — no gear change in this movement).
# ---------------------------------------------------------------------------
BASS_E = n("E2")       # 40  disco octave-8ths
PIANO_LO = n("E2")     # 40  left-hand roots on 1 & 3
PIANO_HI = n("E4")     # 64  right-hand offbeat octaves (the ABBA engine)
STEEL_E = n("E3")      # 52  off-beat chic strums
RHYTHM_E = n("E3")     # 52  power-chord quarter drive
ORGAN_E = n("E3")      # 52  full-organ triads
STR_E = n("E3")        # 52  string shimmer pads
PAD_E = n("E3")        # 52  low warm bed
CHOIR_E = n("E4")      # 64  choir I: chorus stack top + mid ("ah")
HUM_E = n("E3")        # 52  choir II: the low hum counterline ("mm")
BELL_E = n("E4")       # 64  the final bell (warm, into Last Light)
BELL_PEAL_E = n("E5")  # 76  the PEAL an octave up so the bells ring CLEARLY
#                            above the midrange guitars/choir/organ (register
#                            separation at the peaks — see _bells).
LEAD_E = n("E4")       # 64  overdriven lead + its double
FIDDLE_E = n("E4")     # 64  reel countermelody

# The band grooves through the build + both peals, tacet in the breakdown.
GROOVE = ([T0 + 4.0 * i for i in range(int((BREAK - T0) // 4))]        # 448-636
          + [PEAL2 + 4.0 * i for i in range(int((CADENCE - PEAL2) // 4))])  # 704-828

# 32-beat peaks the Leslie and crashes drive into.
PEAKS = [512.0, 544.0, 576.0, 608.0, 704.0, 736.0, 768.0, 800.0]
BIG_PEAKS = {512.0, 576.0, 704.0, 768.0}          # heavy crash (49)

# The ABBA chorus stack, snapped to the ground for safety (as M4 does).
_TOP, _MID, _LOW = m.stack_thirds(m.CHORUS_GUISE)
TOP = m.snap_to_chord(_TOP, m.CHORUS_GROUND, ION)
MID = m.snap_to_chord(_MID, m.CHORUS_GROUND, ION)

# The Guest theme AUGMENTED x2 (durations and offsets doubled -> 64 beats).
THEME_AUG = [(deg, s * 2.0, dur * 2.0) for deg, s, dur in m.THEME]

# GUITAR_GUISE fragments (first and second half, each rebased to 0).
GG = m.GUITAR_GUISE
GG_A = [(d, s, du) for d, s, du in GG if s < 16.0]
GG_B = [(d, s - 16.0, du) for d, s, du in GG if s >= 16.0]

# A lively E-major reel figure (droning on the tonic — reels do that).
REEL_A = [(1, 0.0, 0.5), (3, 0.5, 0.5), (5, 1.0, 0.5), (3, 1.5, 0.5),
          (6, 2.0, 0.5), (5, 2.5, 0.5), (3, 3.0, 0.5), (2, 3.5, 0.5)]
REEL_B = [(5, 0.0, 0.5), (4, 0.5, 0.5), (3, 1.0, 0.5), (2, 1.5, 0.5),
          (1, 2.0, 0.5), (3, 2.5, 0.5), (5, 3.0, 0.5), (8, 3.5, 0.5)]

# Machine-gun run shapes (degrees, capped so ch12/13 stay <= MIDI 96).
RUN_UP = list(range(1, 15))                        # E scale run to deg 14
RUN_ZIG = [1, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9]
RUN_DBL = list(range(1, 13))                        # octave-doubled (top 95)

# ---------------------------------------------------------------------------
# Velocity plan (mean must land in [84, 94]; this is the loudest movement).
# ---------------------------------------------------------------------------
V_KICK, V_SNARE, V_HAT, V_OHAT = 102, 100, 78, 88
V_BASS, V_BASS_OFF = 92, 84
V_PIANO_L, V_PIANO_R = 86, 80
V_STEEL, V_RHY = 82, 88
V_ORGAN, V_STR, V_PAD = 88, 82, 66
V_CHOIR, V_HUM = 92, 82
V_BELL, V_LEAD, V_FID = 96, 98, 86


def _rootdeg(b: float) -> int:
    return m.CHORUS_GROUND[int((b - T0) // 4.0) % 8]


def _in_groove(b: float) -> bool:
    return (T0 <= b < BREAK) or (PEAL2 <= b < CADENCE)


# ---------------------------------------------------------------------------
# Controllers — distance, the ABBA double split + fine-tune, Leslie, vowels,
# aftertouch blooms, the final CC91 recede, and the bend recentres.
# ---------------------------------------------------------------------------
def _controllers(sc):
    channels = (cd.CH_PIANO, cd.CH_PAD, cd.CH_BASS, cd.CH_ORGAN,
                cd.CH_STRINGS, cd.CH_CHOIR1, cd.CH_STEEL, cd.CH_DRUMS,
                cd.CH_RHYTHM, cd.CH_CHOIR2, cd.CH_LEAD, cd.CH_DOUBLE,
                cd.CH_WINDS, cd.CH_BELLS)
    for ch in channels:
        sc.cc(ch, 91, 35, T0)                       # closest / driest

    # The ABBA double: hard L/R split, +8-cent fine tune (RPN 1, not bend).
    sc.cc(cd.CH_LEAD, 10, 20, T0)                   # ch12 hard left
    sc.cc(cd.CH_DOUBLE, 10, 108, T0)                # ch13 hard right
    en.fine_tune(sc, cd.CH_DOUBLE, 8.0, T0)
    # Both lead channels recentred at the movement boundary (bend hygiene).
    sc.bend(cd.CH_LEAD, T0, 0.0)
    sc.bend(cd.CH_DOUBLE, T0, 0.0)
    # Lead expression bed (violining swells draw it down and back per entry).
    sc.cc(cd.CH_LEAD, 11, 96, T0)
    sc.cc(cd.CH_DOUBLE, 11, 96, T0)

    # Choir vowels: choir I "ah" (chorus), choir II "mm" (the low hum).
    en.vowel(sc, cd.CH_CHOIR1, 112, T0)
    en.vowel(sc, cd.CH_CHOIR2, 0, T0)

    # ch4 full organ — Leslie CC1 rotor ramps into each 32-beat peak.
    for pk in PEAKS:
        en.leslie(sc, cd.CH_ORGAN, pk - 6.0, pk, 24, 118)
        en.leslie(sc, cd.CH_ORGAN, pk + 0.5, pk + 6.0, 118, 44)

    # ch1 pad — aftertouch blooms inside the held chords, and the big
    # breakdown breath (0 -> 112 -> 0 across 640-704).
    for pk in (512.0, 576.0, 704.0, 768.0):
        en.at_curve(sc, cd.CH_PAD, [(pk, 0), (pk + 10.0, 96), (pk + 16.0, 20)],
                    step=0.5)
    en.at_curve(sc, cd.CH_PAD,
                [(BREAK, 0), (BREAK + 40.0, 112), (PEAL2 - 1.0, 30)], step=0.5)

    # ch6 choir — aftertouch swells per chorus phrase + the breakdown breath.
    for t in (512.0, 576.0, 704.0, 768.0):
        en.at_curve(sc, cd.CH_CHOIR1,
                    [(t, 30), (t + 12.0, 104), (t + 30.0, 50)], step=0.5)
    en.at_curve(sc, cd.CH_CHOIR1,
                [(BREAK, 20), (BREAK + 40.0, 110), (PEAL2 - 1.0, 40)], step=0.5)

    # The full stop at 884: the pad and the final bell recede (CC91 -> 90).
    sc.cc(cd.CH_PAD, 91, 90, 884.0)
    sc.cc(cd.CH_BELLS, 91, 90, 884.0)

    # Final bend recentres before the 896 boundary (both lead channels).
    sc.bend(cd.CH_LEAD, T1 - 0.5, 0.0)
    sc.bend(cd.CH_DOUBLE, T1 - 0.5, 0.0)


# ---------------------------------------------------------------------------
# ch9 drums — four-on-floor through the groove; fills every 8 beats in peal 2
# ---------------------------------------------------------------------------
def _drums(sc):
    for pk in PEAKS:
        sc.hit(49 if pk in BIG_PEAKS else 57, pk, 110 if pk in BIG_PEAKS else 96)
    for b in GROOVE:
        peal2 = b >= PEAL2
        grow = 0.6 + 0.4 * ((b - T0) / (BREAK - T0)) if b < BREAK else 1.0
        kv = int(V_KICK * (0.9 + 0.1 * grow))
        for beat in (0.0, 1.0, 2.0, 3.0):        # four-on-floor
            sc.hit(36, b + beat, kv + (4 if beat == 0.0 else 0))
        sc.hit(38, b + 1.0, V_SNARE)             # backbeat 2 & 4
        sc.hit(38, b + 3.0, V_SNARE + 2)
        for off in (0.5, 1.5, 2.5):              # closed-hat off-beats
            sc.hit(42, b + off, V_HAT)
        sc.hit(46, b + 3.5, V_OHAT)              # open hat on the & of 4
        if peal2:
            for off in (0.5, 1.5, 2.5, 3.5):     # tambourine shimmer
                sc.hit(54, b + off, 60)
            if int((b - PEAL2) // 4.0) % 2 == 1:  # a fill every 8 beats
                for j, drum in enumerate((38, 40, 45, 43)):
                    sc.hit(drum, b + 3.0 + 0.25 * j,
                           int(lerp(84, 108, j / 3.0)))
    # Cadence 832-880: the dance drives to the end, huge fill into the stop.
    for i in range(int((STOP - CADENCE) // 4)):
        b = CADENCE + 4.0 * i
        for beat in (0.0, 1.0, 2.0, 3.0):
            sc.hit(36, b + beat, V_KICK + (5 if beat == 0.0 else 0))
        sc.hit(38, b + 1.0, V_SNARE + 2)
        sc.hit(38, b + 3.0, V_SNARE + 3)
        for off in (0.5, 1.5, 2.5, 3.5):
            sc.hit(42, b + off, V_HAT + 2)
            sc.hit(54, b + off, 62)
    for j in range(8):                            # the roll into 880
        sc.hit(38, 878.0 + 0.25 * j, int(lerp(80, 118, j / 7.0)), jt=2, jv=3)
    sc.hit(49, STOP, 116)                          # the final crash
    sc.hit(36, STOP, 118)


# ---------------------------------------------------------------------------
# ch3 bass — driving disco octave-8ths on the CHORUS_GROUND roots
# ---------------------------------------------------------------------------
def _bass(sc):
    for b in GROOVE:
        root = _rootdeg(b)
        for k in range(8):
            deg = root if k % 2 == 0 else root + 7      # octave pop on the &s
            if k == 7:
                deg = root + 4                          # a fifth pickup
            v = V_BASS if k % 2 == 0 else V_BASS_OFF
            if k == 0:
                v += 4
            sc.note(cd.CH_BASS, en.pitch(BASS_E, ION, deg), b + 0.5 * k, 0.42,
                    v, jt=3, jv=4)
    _cadence_bass(sc)


# ---------------------------------------------------------------------------
# ch0 piano — the ABBA off-beat octave comp; high glitter in peal 2
# ---------------------------------------------------------------------------
def _piano(sc):
    for b in GROOVE:
        root = _rootdeg(b)
        for beat in (0.0, 2.0):                    # LH roots on 1 & 3
            sc.note(cd.CH_PIANO, en.pitch(PIANO_LO, ION, root), b + beat, 1.7,
                    V_PIANO_L, jt=4, jv=4)
        p = en.pitch(PIANO_HI, ION, root)          # RH octaves on the &s
        for off in (0.5, 1.5, 2.5, 3.5):
            sc.note(cd.CH_PIANO, p, b + off, 0.45, V_PIANO_R, jt=3, jv=4)
            sc.note(cd.CH_PIANO, p + 12, b + off, 0.45, V_PIANO_R - 4,
                    jt=3, jv=4)
    # Glitter: sparkling high arpeggios sprinkled through the second peal.
    for b in GROOVE:
        if b < PEAL2 or int((b - PEAL2) // 4.0) % 2 != 0:
            continue
        root = _rootdeg(b)
        tri = en.triad(PIANO_HI + 12, ION, root)   # up around E5
        seq = tri + [en.pitch(PIANO_HI + 12, ION, root + 7)]
        en.arp(sc, cd.CH_PIANO, seq, b + 2.0, 6, 0.25, 78, gate=0.7,
               accent_every=4, accent=6)


# ---------------------------------------------------------------------------
# ch7 steel — off-beat chic strums; ch10 rhythm — power-chord quarter drive
# ---------------------------------------------------------------------------
def _rhythm_guitars(sc):
    for b in GROOVE:
        root = _rootdeg(b)
        chic = en.triad(STEEL_E, ION, root)        # bright up-strum chops
        for off in (0.5, 1.5, 2.5, 3.5):
            en.strum(sc, cd.CH_STEEL, chic, b + off, 0.22, V_STEEL,
                     spread=0.02, down=False)
        power = [en.pitch(RHYTHM_E, ION, root),    # root + fifth + octave
                 en.pitch(RHYTHM_E, ION, root) + 7,
                 en.pitch(RHYTHM_E, ION, root) + 12]
        for beat in (0.0, 1.0, 2.0, 3.0):
            en.strum(sc, cd.CH_RHYTHM, power, b + beat, 0.85,
                     V_RHY + (4 if beat in (0.0, 2.0) else 0),
                     spread=0.015, down=True)


# ---------------------------------------------------------------------------
# ch4 organ + ch5 strings + ch1 pad — the voice-led chord beds
# ---------------------------------------------------------------------------
def _cycle_chords():
    return [en.triad(52, ION, m.CHORUS_GROUND[i], 3) for i in range(8)]


def _beds(sc):
    cycles = [c for c in (448.0, 480.0, 512.0, 544.0, 576.0, 608.0,
                          704.0, 736.0, 768.0, 800.0)]
    chords = _cycle_chords()
    for t in cycles:
        en.pad_block(sc, cd.CH_ORGAN, t, chords, 4.0, size=3,
                     lo=48, hi=79, vel=V_ORGAN, vel_end=V_ORGAN + 2)
        en.pad_block(sc, cd.CH_STRINGS, t, chords, 4.0, size=3,
                     lo=59, hi=83, vel=V_STR, vel_end=V_STR + 4)
        en.pad_block(sc, cd.CH_PAD, t, chords, 4.0, size=3,
                     lo=45, hi=69, vel=V_PAD, vel_end=V_PAD + 4)
    # Breakdown 640-704: only the soft pad breathes under the choirs + bells.
    brk_chords = [en.triad(52, ION, m.CHORUS_GROUND[i % 8], 3)
                  for i in range(int((PEAL2 - BREAK) // 4))]
    en.pad_block(sc, cd.CH_PAD, BREAK, brk_chords, 4.0, size=3,
                 lo=45, hi=69, vel=54, vel_end=60)


# ---------------------------------------------------------------------------
# ch14 fiddle — the reel-flavoured countermelody (the Oldfield wink)
# ---------------------------------------------------------------------------
def _fiddle(sc):
    for b in GROOVE:
        cell = REEL_A if int((b - T0) // 4.0) % 2 == 0 else REEL_B
        en.line(sc, cd.CH_WINDS, b, FIDDLE_E, ION, cell, V_FID - 4,
                vel_end=V_FID, gate=0.9, jt=3, jv=4)
    # Cadence flourish: a soaring reel run up to the final E.
    en.run(sc, cd.CH_WINDS, 872.0, FIDDLE_E, ION, list(range(1, 13)), 0.25,
           84, 100, gate=0.9, jt=2)
    sc.note(cd.CH_WINDS, en.pitch(FIDDLE_E, ION, 8), STOP, 3.5, 104, jt=2)


# ---------------------------------------------------------------------------
# ch15 tubular bells — THEME AUGMENTED x2 pealing; the final bell rings on
# ---------------------------------------------------------------------------
def _bells(sc):
    for si, t in enumerate((512.0, 576.0, 640.0, 704.0, 768.0)):
        octave_double = si >= 3                    # richer in the second peal
        for deg, s, dur in THEME_AUG:
            b = t + s
            v = V_BELL + (6 if deg >= 7 else 0)
            # The peal sits an octave up (BELL_PEAL_E) so it rings clearly
            # ABOVE the midrange band; the second peal doubles DOWN an octave
            # (into the old bell register) for body without extra shrillness.
            sc.note(cd.CH_BELLS, en.pitch(BELL_PEAL_E, ION, deg), b, dur * 0.9,
                    v, jt=3, jv=4)
            if octave_double and deg in (1, 5, 7, 8):
                sc.note(cd.CH_BELLS, en.pitch(BELL_PEAL_E, ION, deg) - 12,
                        b + 0.02, dur * 0.6, v - 16, jt=3, jv=4)
    # The final bell — struck at 880, rings on into Last Light.
    sc.note(cd.CH_BELLS, en.pitch(BELL_E, ION, 1), STOP, 18.0, 100, jt=2)
    sc.note(cd.CH_BELLS, en.pitch(BELL_E, ION, 1) + 12, STOP + 0.1, 16.0,
            82, jt=2)


# ---------------------------------------------------------------------------
# ch6 choir I (chorus stack, "ah") + ch11 choir II (low hum guise, "mm")
# ---------------------------------------------------------------------------
def _choir(sc):
    # Choir I — the ABBA chorus stack (top + mid) on the peal cycles.
    for t in (512.0, 544.0, 576.0, 608.0, 704.0, 736.0, 768.0, 800.0):
        vel = V_CHOIR if t < BREAK else V_CHOIR + 2
        en.line(sc, cd.CH_CHOIR1, t, CHOIR_E, ION, MID, vel,
                vel_end=vel + 4, gate=0.96, jt=5, jv=4)
        en.line(sc, cd.CH_CHOIR1, t, CHOIR_E, ION, TOP, vel - 2,
                vel_end=vel + 2, gate=0.96, jt=5, jv=4)
    # Breakdown 640-704: choir I holds a wide, breathing "ah" chord.
    for i in range(int((PEAL2 - BREAK) // 4)):
        b = BREAK + 4.0 * i
        if i % 2 != 0:
            continue
        root = _rootdeg(b)
        for deg in (root, root + 2, root + 4):
            sc.note(cd.CH_CHOIR1, en.pitch(CHOIR_E, ION, deg), b + 0.05, 7.8,
                    72, jt=3, jv=3)
    # Choir II — the LOW HUM guise (plain theme), a wordless counterline that
    # runs from the first peal straight through the breakdown to the second.
    for t in (512.0, 544.0, 576.0, 608.0, 640.0, 672.0,
              704.0, 736.0, 768.0, 800.0):
        vel = V_HUM if (t < BREAK or t >= PEAL2) else V_HUM - 6
        en.line(sc, cd.CH_CHOIR2, t, HUM_E, ION, m.THEME, vel,
                vel_end=vel + 4, gate=0.98, jt=5, jv=3)


# ---------------------------------------------------------------------------
# ch12/ch13 lead — violining entries, then GUITAR GUISE + machine-gun runs
# ---------------------------------------------------------------------------
def _duo_line(sc, t0, notes, vel, gate=0.94, jt=3):
    en.line(sc, cd.CH_LEAD, t0, LEAD_E, ION, notes, vel, gate=gate, jt=jt)
    en.line(sc, cd.CH_DOUBLE, t0, LEAD_E, ION, notes, vel - 8, gate=gate, jt=jt)


def _duo_run(sc, t0, degs, spacing, v0, v1, octave_double=None):
    en.run(sc, cd.CH_LEAD, t0, LEAD_E, ION, degs, spacing, v0, v1,
           legato=False, octave_double=octave_double)
    en.run(sc, cd.CH_DOUBLE, t0, LEAD_E, ION, degs, spacing, v0 - 8, v1 - 8,
           legato=False, octave_double=octave_double)
    return t0 + len(degs) * spacing


def _violin_entry(sc, t, deg, dur, vel):
    """A bowed-in guitar note: expression swells up from nothing, blooming
    vibrato, recentred at the end."""
    p = en.pitch(LEAD_E, ION, deg)
    sc.note(cd.CH_LEAD, p, t, dur, vel, jt=2)
    sc.note(cd.CH_DOUBLE, p, t, dur, vel - 8, jt=2)
    en.expr_curve(sc, cd.CH_LEAD, [(t, 6), (t + dur * 0.7, 100)], step=0.25)
    en.expr_curve(sc, cd.CH_DOUBLE, [(t, 6), (t + dur * 0.7, 96)], step=0.25)
    en.vibrato(sc, cd.CH_LEAD, t, dur, depth=0.25, delay=dur * 0.4)
    # restore full expression for the following material
    sc.cc(cd.CH_LEAD, 11, 100, t + dur - 0.05)
    sc.cc(cd.CH_DOUBLE, 11, 100, t + dur - 0.05)


def _lead(sc):
    # Build 448-512: the guitar assembles with three violining entries.
    _violin_entry(sc, 456.0, 5, 6.0, 84)          # B4
    _violin_entry(sc, 472.0, 8, 7.0, 88)          # E5
    _violin_entry(sc, 492.0, 10, 8.0, 92)         # G#5, reaching up to the peal

    # Peal 1 512-640: guise statements alternating with machine-gun bursts.
    _duo_line(sc, 512.0, GG_A, 92, gate=0.9)      # guise bars 1-2
    _duo_run(sc, 528.0, RUN_UP, 0.25, 92, 104)    # burst into 544
    _duo_line(sc, 544.0, GG_B, 92, gate=0.9)      # guise bars 5-6 idea
    _duo_run(sc, 560.0, RUN_ZIG, 0.25, 92, 104)
    _duo_line(sc, 576.0, GG_A, 94, gate=0.9)
    _duo_run(sc, 592.0, RUN_UP, 0.25, 94, 106)
    _duo_line(sc, 608.0, GG_B, 94, gate=0.9)
    _duo_run(sc, 624.0, RUN_ZIG, 0.25, 94, 106)

    # Breakdown 640-704: the guitars rest (choirs + bells only).

    # Peal 2 704-832: fuller, octave-doubled machine-gun runs.
    _duo_line(sc, 704.0, GG_A, 96, gate=0.9)
    _duo_run(sc, 720.0, RUN_DBL, 0.25, 96, 108, octave_double=12)
    _duo_line(sc, 736.0, GG_B, 96, gate=0.9)
    _duo_run(sc, 752.0, RUN_DBL, 0.25, 96, 108, octave_double=12)
    _duo_line(sc, 768.0, GG_A, 98, gate=0.9)
    _duo_run(sc, 784.0, RUN_DBL, 0.25, 98, 110, octave_double=12)
    _duo_line(sc, 800.0, GG_B, 98, gate=0.9)
    _duo_run(sc, 816.0, RUN_UP, 0.25, 98, 110)

    # Cadence 832-880: a climbing run, then the lead lands on the final E.
    _duo_run(sc, 872.0, list(range(1, 15)), 0.25, 96, 112)
    p = en.pitch(LEAD_E, ION, 8)
    sc.note(cd.CH_LEAD, p, STOP, 4.0, 110, jt=2)
    sc.note(cd.CH_DOUBLE, p, STOP, 4.0, 102, jt=2)
    en.vibrato(sc, cd.CH_LEAD, STOP, 4.0, depth=0.3, delay=0.6)


# ---------------------------------------------------------------------------
# The big IV-V-I(sus) cadence (832-880) and the full stop (880-896)
# ---------------------------------------------------------------------------
def _cadence_bass(sc):
    # Bass roots for the cadence: A (IV) | B (V) | E (I / sus) driving 8ths.
    plan = [(832.0, 4), (848.0, 5), (864.0, 1), (872.0, 1)]
    for t, root in plan:
        for i in range(int(((t + (16.0 if t < 864.0 else 8.0)) - t) // 0.5)):
            b = t + 0.5 * i
            deg = root if i % 2 == 0 else root + 7
            sc.note(cd.CH_BASS, en.pitch(BASS_E, ION, deg), b, 0.42,
                    V_BASS + (4 if i % 8 == 0 else 0), jt=3, jv=4)
    # The final low E, struck on the downbeat and held to the stop.
    sc.note(cd.CH_BASS, en.pitch(BASS_E, ION, 1), STOP, 4.0, V_BASS + 6, jt=2)


def _cadence(sc):
    # IV (A) 832-848, V (B) 848-864, I(sus->E) 864-880, on organ+strings+pad
    # +choir, sustained and swelling, then the tutti E chord at the stop.
    def chord(base, deg, extra=()):
        return [en.pitch(base, ION, deg), en.pitch(base, ION, deg + 2),
                en.pitch(base, ION, deg + 4)] + [en.pitch(base, ION, e)
                                                 for e in extra]

    plan = [(832.0, 16.0, 4, ()),                  # IV = A
            (848.0, 16.0, 5, ()),                  # V  = B
            (864.0, 8.0, 1, (3,)),                 # I  = E (with sus colour)
            (872.0, 8.0, 1, ())]                   # I  resolved, building
    for t, dur, deg, extra in plan:
        vel = int(lerp(84, 96, (t - CADENCE) / (STOP - CADENCE)))
        for ch, base, gv in ((cd.CH_ORGAN, ORGAN_E, vel),
                             (cd.CH_STRINGS, STR_E + 12, vel - 4),
                             (cd.CH_PAD, PAD_E, vel - 14)):
            for p in chord(base, deg, extra):
                sc.note(ch, p, t + 0.02, dur - 0.1, gv, jt=2, jv=3)
        # Choir I belts the cadence "ah" (Esus4 -> E is the ABBA lift).
        cdeg = (4, 6, 8) if deg == 4 else (5, 7, 9) if deg == 5 else \
               ((1, 4, 6) if extra else (1, 3, 5))
        for d in cdeg:
            sc.note(cd.CH_CHOIR1, en.pitch(CHOIR_E, ION, d), t + 0.03,
                    dur - 0.1, vel, jt=2, jv=3)

    # The full stop at 884: the tutti E major chord struck at 880, ringing to
    # 884; the pad chord and the final bell (see _bells) ring on beyond it.
    tutti = [(cd.CH_ORGAN, ORGAN_E), (cd.CH_STRINGS, STR_E + 12),
             (cd.CH_CHOIR1, CHOIR_E)]
    for ch, base in tutti:
        for deg in (1, 3, 5, 8):
            sc.note(ch, en.pitch(base, ION, deg), STOP, 3.6, 104, jt=2, jv=3)
    # ch1 pad — the chord that survives the stop, ringing far (CC91->90).
    for deg in (1, 3, 5, 8):
        sc.note(cd.CH_PAD, en.pitch(PAD_E, ION, deg), STOP, 15.0, 74,
                jt=2, jv=3)


# ---------------------------------------------------------------------------
def build(sc) -> None:
    _controllers(sc)
    _drums(sc)
    _bass(sc)
    _piano(sc)
    _rhythm_guitars(sc)
    _beds(sc)
    _fiddle(sc)
    _bells(sc)
    _choir(sc)
    _lead(sc)
    _cadence(sc)
