"""m4_searchlight — Part Two, Movement 4 "Searchlight"
(beats 0-448, D ionian -> E ionian at the beat-320 gear change, 118).

Super Trouper — THE ABBA gear change.  Roadmap section 4, M4:

  0-64     Intro: ch0 OFF-BEAT OCTAVE COMP (the ABBA engine — octaves on
           the &s, roots on 1/3 in LH), four-on-floor kit assembling,
           ch7 steel backbeat strums, ch3 bass pop octave-8ths on the
           CHORUS_GROUND roots (I V ii vi | I V IV I = D A Em Bm | D A G D).
  64-128   Chorus 1: ch6 sings the CHORUS_GUISE, vowel ah (CC70=100), with
           stack_thirds top+mid on ch6 and the low voice on ch11 (all snapped
           to CHORUS_GROUND for safety); ch15 glock doubles the hook.
  128-224  Verse interlude: ch12 takes GUITAR_GUISE fragments (clean,
           delayed echo throws), ch13 harmonizes a 3rd below, piano comp
           continues, steel keeps the backbeat.
  224-288  Chorus 2: bigger — ch14 fiddle descant, ch5 strings pads, bass
           walks.
  288-320  Breakdown: drums to kick, ch1 pad + both choirs hold "oo"
           (CC70~45) under a LONG aftertouch crescendo, snare-roll build.
  320      GEAR CHANGE: keysig E major (conductor); chorus restated at +2
           semitones, full band, vowel ah, tambourine, glock 8va.
           Chorus 3 (320-384), then tail (384-448) rides the E ground vamp
           I-IV-I-V as the disco pulse hands over to M5.

Everything at/after 320 is in E ionian: degrees are shifted +2 semitones
via the base pitch (D->E), staying inside verify.NOTE_RANGES.  CC91 sits
near 50 across the movement; bends are clean (recentred) at 448.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp

ION = "ionian"

T0, T1 = 0.0, 448.0
GEAR = 320.0
INTRO, CH1, VERSE, CH2, BRK, CH3, TAIL = 0.0, 64.0, 128.0, 224.0, 288.0, 320.0, 384.0

# Degree-1 anchors in D ionian; +2 semitones after the gear change gives E.
BASS_D = en.n("D2")        # 38
PIANO_LO_D = en.n("D2")    # 38  left-hand roots on 1 & 3
PIANO_HI_D = en.n("D4")    # 62  right-hand offbeat octaves (the ABBA engine)
STEEL_D = en.n("D3")       # 50  backbeat strums
RHYTHM_D = en.n("D3")      # 50  offbeat skank chops
CHOIR_D = en.n("D4")       # 62  choir I: chorus stack top + mid
CHOIR_LOW_D = en.n("D3")   # 50  choir II: the low stack voice
GLOCK_D = en.n("D4")       # 62  hook double (unison ch1/2, 8va in ch3)
GTR_D = en.n("D4")         # 62  guitar-guise fragments
STR_D = en.n("D3")         # 50  strings pads
WIND_D = en.n("D5")        # 74  fiddle descant (sustained fifths)
PAD_D = en.n("D3")         # 50  breakdown pad

# The E-major tail vamp: I - IV - I - V (one chord per bar).
VAMP = [1, 4, 1, 5]

# The ABBA chorus voices, built once and snapped to the ground for safety
# (the material oracle certifies top/low need no snap; mid may touch it).
_TOP, _MID, _LOW = m.stack_thirds(m.CHORUS_GUISE)
TOP = m.snap_to_chord(_TOP, m.CHORUS_GROUND, ION)
MID = m.snap_to_chord(_MID, m.CHORUS_GROUND, ION)
LOW = m.snap_to_chord(_LOW, m.CHORUS_GROUND, ION)

# Guitar-guise fragments for the verse (bars 1-2 and bars 5-6, rebased to 0).
GG = m.GUITAR_GUISE
FRAG_A = [(d, s, du) for d, s, du in GG if s < 8.0]
FRAG_B = [(d, s - 16.0, du) for d, s, du in GG if 16.0 <= s < 24.0]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _base(base_d: float, beat: float) -> int:
    """Degree-1 anchor for `beat`: +2 semitones once the gear change hits."""
    return int(base_d) + (2 if beat >= GEAR else 0)


def _root_at(beat: float) -> int:
    """The chord root degree in force at `beat` (CHORUS_GROUND up to the
    tail, then the E vamp I-IV-I-V)."""
    if beat < TAIL:
        return m.ground_root_at(m.CHORUS_GROUND, beat)
    return VAMP[int((beat - TAIL) // 4) % 4]


def _triad(base_d: float, beat: float, extra_octave: bool = False) -> list[int]:
    root = _root_at(beat)
    b = _base(base_d, beat)
    tri = en.triad(b, ION, root)
    if extra_octave:
        tri = tri + [en.pitch(b, ION, root + 7)]     # add the octave on top
    return tri


# ---------------------------------------------------------------------------
# Controllers — CC91 distance ~50, choir vowels, breakdown aftertouch
# ---------------------------------------------------------------------------
def _controllers(sc):
    for ch in (cd.CH_PIANO, cd.CH_PAD, cd.CH_BASS, cd.CH_STRINGS,
               cd.CH_CHOIR1, cd.CH_STEEL, cd.CH_DRUMS, cd.CH_RHYTHM,
               cd.CH_CHOIR2, cd.CH_LEAD, cd.CH_DOUBLE, cd.CH_WINDS,
               cd.CH_BELLS):
        sc.cc(ch, 91, 50, T0)
    # A touch more room around the voices and the breakdown pad.
    sc.cc(cd.CH_CHOIR1, 91, 58, T0)
    sc.cc(cd.CH_CHOIR2, 91, 58, T0)
    sc.cc(cd.CH_PAD, 91, 62, T0)

    # Choir vowel timeline (CC70): ah in the choruses, oo in the breakdown.
    for ch in (cd.CH_CHOIR1, cd.CH_CHOIR2):
        en.vowel(sc, ch, 100, CH1 - 1.0)     # chorus 1: ah
        en.vowel(sc, ch, 100, CH2 - 1.0)     # chorus 2: ah
        en.vowel(sc, ch, 45, BRK)            # breakdown: oo
        en.vowel(sc, ch, 100, CH3)           # gear change: ah again


# ---------------------------------------------------------------------------
# ch0 piano — the ABBA off-beat octave comp (roots on 1/3, octaves on the &s)
# ---------------------------------------------------------------------------
def _piano(sc):
    for bar in range(112):
        b = bar * 4.0
        if BRK <= b < CH3:
            continue                          # tacet through the breakdown
        root = _root_at(b)
        lo = _base(PIANO_LO_D, b)
        hi = _base(PIANO_HI_D, b)
        grow = 1.0 if b >= CH1 else lerp(0.55, 1.0, b / CH1)
        # Left hand: the root on beats 1 and 3.
        for beat in (0.0, 2.0):
            sc.note(cd.CH_PIANO, en.pitch(lo, ION, root), b + beat, 1.7,
                    int(78 * grow), jt=4, jv=4)
        # Right hand: octave dyads on the &s (0.5, 1.5, 2.5, 3.5).
        light = VERSE <= b < CH2               # verse: thin to two octaves/bar
        offs = (1.5, 3.5) if light else (0.5, 1.5, 2.5, 3.5)
        p = en.pitch(hi, ION, root)
        for off in offs:
            v = int(lerp(72, 80, off / 4.0) * grow)
            sc.note(cd.CH_PIANO, p, b + off, 0.45, v, jt=3, jv=4)
            sc.note(cd.CH_PIANO, p + 12, b + off, 0.45, v - 4, jt=3, jv=4)


# ---------------------------------------------------------------------------
# ch3 bass — pop octave-8ths on the ground roots; walks in chorus 2
# ---------------------------------------------------------------------------
def _bass(sc):
    for bar in range(112):
        b = bar * 4.0
        if b < 8.0:
            continue                          # enters after the piano
        if BRK <= b < CH3:
            continue                          # out for the breakdown
        root = _root_at(b)
        base = _base(BASS_D, b)
        vel = int(lerp(74, 82, min(1.0, b / CH1)))
        walk = CH2 <= b < BRK                  # chorus 2: the bass walks
        for k in range(8):
            t = b + 0.5 * k
            acc = 6 if k == 0 else (2 if k == 4 else -3)
            if k == 7:                         # pickup: the fifth into the bar
                deg = root + 4
            elif walk and k in (5, 6):         # a little stepwise walk-up
                deg = root + (2 if k == 5 else 3)
            else:
                deg = root if k % 2 == 0 else root + 7   # octave pop
            sc.note(cd.CH_BASS, en.pitch(base, ION, deg), t, 0.42,
                    vel + acc, jt=3, jv=4)


# ---------------------------------------------------------------------------
# ch7 steel — strummed backbeat (beats 2 and 4); ch10 rhythm — offbeat skanks
# ---------------------------------------------------------------------------
def _guitars_rhythm(sc):
    for bar in range(112):
        b = bar * 4.0
        sec_full = b >= CH1 or b >= 40.0       # steel enters late in the intro
        if BRK <= b < CH3:
            continue
        tri = _triad(STEEL_D, b, extra_octave=True)
        if b >= 40.0:                          # backbeat strums on 2 and 4
            v = int(lerp(62, 72, min(1.0, (b - 40.0) / 64.0)))
            en.strum(sc, cd.CH_STEEL, tri, b + 1.0, 0.9, v, down=True)
            en.strum(sc, cd.CH_STEEL, tri, b + 3.0, 0.9, v + 2, down=False)
        # Offbeat skank chops (the disco "chk") once the choruses arrive.
        if (CH1 <= b < VERSE) or (CH2 <= b < BRK) or (b >= CH3):
            chop = _triad(RHYTHM_D, b)
            for off in (1.5, 3.5):
                en.strum(sc, cd.CH_RHYTHM, chop, b + off, 0.22, 63,
                         spread=0.02, down=True)


# ---------------------------------------------------------------------------
# ch9 drums — four-on-floor, assembling in the intro, kick-only in the break
# ---------------------------------------------------------------------------
def _drums(sc):
    crashes = {CH1, VERSE, CH2, CH3, TAIL}
    for bar in range(112):
        b = bar * 4.0
        if b in crashes:
            sc.hit(49, b, 108)
        # ---- breakdown: drums reduce to a rising kick + a build ----
        if BRK <= b < CH3:
            g = (b - BRK) / (CH3 - BRK)
            kv = int(lerp(78, 104, g))
            sc.hit(36, b, kv)
            sc.hit(36, b + 2.0, kv - 4)
            if b >= CH3 - 8.0:                  # last two bars: snare roll
                n = 8 if b >= CH3 - 4.0 else 4
                for k in range(n):
                    sc.hit(38, b + 4.0 * k / n,
                           int(lerp(60, 116, (b - (CH3 - 8.0) + 4.0 * k / n)
                                    / 8.0)), jt=2, jv=3)
            continue
        # ---- intro assembling ----
        if b < 16.0:
            continue
        assemble = b < CH1
        kv = int(lerp(90, 102, min(1.0, b / CH1)))
        sv = int(lerp(96, 106, min(1.0, b / CH1)))
        # four-on-floor kick
        for beat in (0.0, 1.0, 2.0, 3.0):
            sc.hit(36, b + beat, kv + (4 if beat == 0 else 0))
        if b >= 32.0:                           # snare backbeat from bar 8
            sc.hit(38, b + 1.0, sv)
            sc.hit(38, b + 3.0, sv)
        verse = VERSE <= b < CH2
        if verse:                               # verse: tighter, closed hats
            for k in range(4):
                sc.hit(42, b + k, 46)
        elif b >= 32.0 or not assemble:         # open-hat offbeats (disco)
            for off in (0.5, 1.5, 2.5, 3.5):
                sc.hit(46, b + off, 52)
        # tambourine rides from the gear change
        if b >= CH3:
            for off in (0.5, 1.5, 2.5, 3.5):
                sc.hit(54, b + off, 50)
        # a modest snare fill at the end of each 32-beat block
        if bar % 8 == 7 and b + 4 <= T1 and not verse:
            for j, drum in enumerate((38, 38, 40, 38)):
                sc.hit(drum, b + 3.0 + 0.25 * j, int(lerp(80, 104, j / 3.0)))


# ---------------------------------------------------------------------------
# ch6/ch11 choir — the ABBA stacked chorus (top+mid on ch6, low on ch11)
# ---------------------------------------------------------------------------
def _sing(sc, ch, base_d, voice, t_start, vel, vel_end):
    en.line(sc, ch, t_start, _base(base_d, t_start), ION, voice,
            vel, vel_end=vel_end, gate=0.95, jt=5, jv=4)


def _chorus_voices(sc, t0, vel, glock_extra=0):
    """Sing one 32-beat chorus statement starting at t0."""
    self_top = vel + 2
    self_mid = vel
    self_low = vel - 4
    self_glk = vel - 8
    _sing(sc, cd.CH_CHOIR1, CHOIR_D, TOP, t0, self_top, self_top + 4)
    _sing(sc, cd.CH_CHOIR1, CHOIR_D, MID, t0, self_mid, self_mid + 4)
    _sing(sc, cd.CH_CHOIR2, CHOIR_LOW_D, LOW, t0, self_low, self_low + 3)
    # ch15 glock doubles the hook (the mid melody's first phrase); 8va after
    # the gear change.
    gbase = _base(GLOCK_D, t0) + glock_extra
    hook = [(d, s, du) for d, s, du in MID if s < 16.0]
    en.line(sc, cd.CH_BELLS, t0, gbase, ION, hook, self_glk, gate=0.6,
            jt=3, jv=4)


def _choruses(sc):
    # Chorus 1 (64-128) and Chorus 2 (224-288): two 32-beat statements each.
    for t0 in (CH1, CH1 + 32.0):
        _chorus_voices(sc, t0, 78)
    for t0 in (CH2, CH2 + 32.0):
        _chorus_voices(sc, t0, 80)
    # Chorus 3 (320-384): the restatement at +2, fuller, glock 8va.
    for t0 in (CH3, CH3 + 32.0):
        _chorus_voices(sc, t0, 82, glock_extra=12)


# ---------------------------------------------------------------------------
# ch5 strings — pads through chorus 2, the gear change and the tail
# ---------------------------------------------------------------------------
def _strings(sc):
    def pad(t0, t1, vel):
        bars = int((t1 - t0) // 4)
        chords = [_triad(STR_D, t0 + 4.0 * i) for i in range(bars)]
        lo = _base(STR_D, t0)
        en.pad_block(sc, cd.CH_STRINGS, t0, chords, 4.0, size=3,
                     lo=lo, hi=lo + 24, vel=vel, vel_end=vel + 4)
    pad(CH2, BRK, 58)          # chorus 2 pads
    pad(CH3, TAIL, 64)         # gear-change chorus, fuller
    pad(TAIL, T1 - 0.5, 60)    # the E vamp tail


# ---------------------------------------------------------------------------
# ch14 fiddle — a soaring descant (sustained chord-fifths) over chorus 2 & 3
# ---------------------------------------------------------------------------
def _descant(sc):
    for t0, t1, vel in ((CH2, BRK, 70), (CH3, TAIL, 74)):
        bars = int((t1 - t0) // 4)
        for i in range(bars):
            b = t0 + 4.0 * i
            root = _root_at(b)
            p = en.pitch(_base(WIND_D, b), ION, root + 4)    # the fifth, high
            sc.note(cd.CH_WINDS, p, b + 0.5, 3.2, vel, jt=4, jv=4)
            en.vibrato(sc, cd.CH_WINDS, b + 0.5, 3.2, depth=0.25, delay=0.8)


# ---------------------------------------------------------------------------
# ch12/ch13 guitars — GUITAR_GUISE fragments in the verse (ch13 a 3rd below)
# ---------------------------------------------------------------------------
def _verse_guitars(sc):
    frags = [FRAG_A, FRAG_B]
    for i, t in enumerate(range(int(VERSE), int(CH2), 16)):
        frag = frags[i % 2]
        base = _base(GTR_D, t)
        vel = int(lerp(70, 76, i / 5.0))
        en.line(sc, cd.CH_LEAD, float(t), base, ION, frag, vel,
                gate=0.9, jt=5, jv=4)
        en.line(sc, cd.CH_DOUBLE, float(t), base, ION,
                m.shift_steps(frag, -2), vel - 8, gate=0.9, jt=5, jv=4)
        # a little delayed sparkle at the phrase end (echo throw)
        end = t + max(s + d for _dg, s, d in frag)
        en.echo_throw(sc, cd.CH_LEAD, end, base=25, peak=80, release=2.0)
        # vibrato on the fragment's held tail note
        dg, s, d = max(frag, key=lambda nt: nt[2])
        if d >= 1.0:
            en.vibrato(sc, cd.CH_LEAD, t + s, d, depth=0.28, delay=0.3)
    # Recentre both channels well before the 448 boundary (bend hygiene).
    for ch in (cd.CH_LEAD, cd.CH_DOUBLE):
        sc.bend(ch, CH2 - 0.5, 0.0)


# ---------------------------------------------------------------------------
# ch1 pad + choirs — the breakdown hold with the LONG aftertouch crescendo
# ---------------------------------------------------------------------------
def _breakdown(sc):
    # A held D-major triad on the pad, plus both choirs on a long "oo" vowel.
    tri = _triad(PAD_D, BRK)                    # D major, in D ionian
    for p in tri:
        sc.note(cd.CH_PAD, p, BRK, CH3 - BRK - 0.2, 46, jt=2, jv=3)
    # Choir I holds the 3rd + 5th, choir II the low root — a wide "oo" chord.
    cb = _base(CHOIR_D, BRK)
    for deg in (3, 5):
        sc.note(cd.CH_CHOIR1, en.pitch(cb, ION, deg), BRK, CH3 - BRK - 0.2,
                52, jt=2, jv=3)
    sc.note(cd.CH_CHOIR2, en.pitch(_base(CHOIR_LOW_D, BRK), ION, 1),
            BRK, CH3 - BRK - 0.2, 50, jt=2, jv=3)
    # The LONG aftertouch crescendo swelling into the gear change.
    for ch in (cd.CH_PAD, cd.CH_CHOIR1, cd.CH_CHOIR2):
        en.at_curve(sc, ch, [(BRK, 0), (CH3 - 1.0, 100), (CH3 - 0.1, 118)],
                    step=0.5)
        en.at_curve(sc, ch, [(CH3 - 0.1, 0)], step=0.5)   # release at the top


# ---------------------------------------------------------------------------
# The tail (384-448): choirs sustain the E vamp; band keeps the disco pulse
# ---------------------------------------------------------------------------
def _tail(sc):
    # Choir I sings the vamp roots as long "ah" chords handing over to M5.
    for i in range(int((T1 - TAIL) // 4)):
        b = TAIL + 4.0 * i
        root = _root_at(b)
        cb = _base(CHOIR_D, b)
        for deg in (root, root + 2, root + 4):
            sc.note(cd.CH_CHOIR1, en.pitch(cb, ION, deg), b + 0.05, 3.7,
                    76, jt=3, jv=4)
        # glock pings the chord top on each downbeat (8va)
        sc.note(cd.CH_BELLS, en.pitch(cb + 12, ION, root + 4), b, 1.0, 68,
                jt=3, jv=4)


# ---------------------------------------------------------------------------
def build(sc) -> None:
    _controllers(sc)
    _piano(sc)
    _bass(sc)
    _guitars_rhythm(sc)
    _drums(sc)
    _choruses(sc)
    _strings(sc)
    _descant(sc)
    _verse_guitars(sc)
    _breakdown(sc)
    _tail(sc)
