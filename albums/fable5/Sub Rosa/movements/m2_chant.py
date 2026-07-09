"""m2_chant — Movement 2 "The Chant" (beats 64-256, D aeolian, 124).

The groove ignites on a crash and the letter is read aloud.  Twelve
cycles of the verse ground (Dm C Bb C) under: the bass hook in its
spacious verse guise; the chant sung closed-mouthed (CC70 = 0) at 96,
answered by a choir-II organum drone from the second statement; the
sequencer entering at 128 with its filter opening across the whole
movement (CC74 30->95, CC71 riding); glass echoes of the chant's tail;
a piano figure at the cycle corners under pedal pools; wah-less guitar
skanks arriving at 208 to foreshadow the third movement; and a first
whispered "sub rosa" at 240 as the choir falls silent.

    64-96    groove + hook establish
    96-128   chant, first statement (mm)
    128-160  chant again; organum drone; the sequencer wakes
    160-192  instrumental: glass runs, piano corners
    192-224  chant, third statement (morphing toward oo); open-fifth drone
    224-256  voices out; skanks + drive-guise bass build the seam
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"
T0, T1 = 64.0, 256.0

BASS_BASE = n("D2")
CHANT_BASE = n("D4")
DRONE_LOW = n("D3")
FIFTH = n("A3")
CRYSTAL_BASE = n("D6")
PIANO_BASE = n("D3")
GTR_BASE = n("D3")
PAD_LO, PAD_HI = n("G2"), n("G4")


def _ground_root(bar: int) -> int:
    return m.CHANT_GROUND[bar % 4]


# ---------------------------------------------------------------------------
# drums — the engine of the piece
# ---------------------------------------------------------------------------
def _drums(sc):
    sc.hit(49, T0, 96, jv=2)                       # the igniting crash
    nbars = int((T1 - T0) // 4)
    for bar in range(nbars):
        t = T0 + 4.0 * bar
        grow = bar / (nbars - 1)
        fill_bar = bar % 16 == 15
        # kick: four on the floor, first beat leaning hardest
        for k, beat in enumerate((0.0, 1.0, 2.0, 3.0)):
            sc.hit(36, t + beat, int(lerp(78, 86, grow)) - (0 if k == 0 else 8))
        # the pushed kick on the 2& every other bar — the Enigma lean
        if bar % 2 == 1:
            sc.hit(36, t + 2.75, 62)
        # snare + clap together on 2 and 4
        for beat in (1.0, 3.0):
            sc.hit(38, t + beat, int(lerp(76, 84, grow)))
            sc.hit(39, t + beat, 58)
        # 16th hats, accents on the off-8ths; open hat closing each 2 bars
        if not fill_bar:
            for s in range(16):
                beat = s * 0.25
                accent = 58 if s % 4 == 2 else (48 if s % 2 == 0 else 38)
                sc.hit(42, t + beat, accent + int(6 * grow), jt=2, jv=3)
            if bar % 2 == 1:
                sc.hit(46, t + 3.75, 56, jt=2)
        else:
            # tom run into the next cycle
            for s, (drum, v) in enumerate(((48, 74), (48, 70), (47, 76),
                                           (47, 72), (45, 80), (45, 76),
                                           (41, 84), (41, 88))):
                sc.hit(drum, t + 2.0 + s * 0.25, v, jt=2)
            sc.hit(42, t + 0.25, 46, jt=2)
            sc.hit(42, t + 0.75, 44, jt=2)
            sc.hit(38, t + 1.0, 80)
    for beat in (128.0, 192.0):
        sc.hit(49, beat, 88, jv=2)                 # cycle crashes


# ---------------------------------------------------------------------------
# bass — the hook, verse guise; drive guise through the seam build
# ---------------------------------------------------------------------------
def _bass(sc):
    ch = cd.CH_BASS
    nbars = int((T1 - T0) // 4)
    for bar in range(nbars):
        t = T0 + 4.0 * bar
        guise = "drive" if t >= 224.0 else "verse"
        root = m.bass_root(_ground_root(bar))
        vel = int(lerp(68, 78, bar / (nbars - 1)))
        for deg, s, dur in m.bass_riff(root, guise):
            sc.note(ch, en.pitch(BASS_BASE, AEO, deg), t + s, dur * 0.95,
                    vel, jt=2, jv=3)


# ---------------------------------------------------------------------------
# pad — voice-led ground bed
# ---------------------------------------------------------------------------
def _pad(sc):
    ch = cd.CH_PAD
    chords = [en.triad(n("D3"), AEO, _ground_root(bar)) for bar in range(48)]
    en.pad_block(sc, ch, T0, chords, span=4.0, size=4,
                 lo=PAD_LO, hi=PAD_HI, vel=46, vel_end=54)
    for phrase in range(6):                        # breathing blooms
        t = T0 + phrase * 32.0
        en.at_curve(sc, ch, [(t, 0), (t + 16.0, 70), (t + 31.0, 0)],
                    step=0.5)


# ---------------------------------------------------------------------------
# choir — three chant statements over an organum drone
# ---------------------------------------------------------------------------
def _choir(sc):
    ch = cd.CH_CHOIR1
    en.vowel(sc, ch, 0, 95.5)                      # closed mouth
    en.vowel_curve(sc, ch, [(96.0, 0), (128.0, 12), (160.0, 12),
                            (192.0, 40), (222.0, 58)], step=4.0)
    for start, vel in ((96.0, 58), (128.0, 62), (192.0, 66)):
        en.line(sc, ch, start, CHANT_BASE, AEO, m.CHANT, vel,
                vel_end=vel + 5, gate=0.97, jt=5, jv=3)
        for k in range(4):                         # a swell per phrase pair
            p0 = start + 8.0 * k
            en.at_curve(sc, ch, [(p0, 5), (p0 + 4.0, 75), (p0 + 7.5, 10)],
                        step=0.5)

    ch2 = cd.CH_CHOIR2
    en.vowel(sc, ch2, 0, 127.0)
    # Organum: a D drone under statement 2, the open fifth added for 3.
    for t in range(128, 160, 8):
        sc.note(ch2, DRONE_LOW, float(t), 7.8, 48, jt=4, jv=2)
    for t in range(192, 224, 8):
        sc.note(ch2, DRONE_LOW, float(t), 7.8, 50, jt=4, jv=2)
        sc.note(ch2, FIFTH, float(t), 7.8, 46, jt=4, jv=2)


# ---------------------------------------------------------------------------
# sequencer — enters at 128, filter opening across the movement
# ---------------------------------------------------------------------------
def _arp(sc):
    ch = cd.CH_ARP
    sc.cc(ch, 74, 30, 127.0)
    en.cc_curve(sc, ch, 74, [(128.0, 30), (254.0, 95)], step=4.0)
    en.cc_curve(sc, ch, 71, [(128.0, 45), (200.0, 80), (254.0, 55)],
                step=4.0)
    en.autopan(sc, ch, 128.0, 126.0, lo=52, hi=96, period_beats=24.0,
               step=0.25)
    for bar in range(32):                          # 128..256
        t = 128.0 + 4.0 * bar
        root = _ground_root(bar)                   # same phase as the ground
        vel = int(lerp(54, 62, bar / 31.0))
        for slot, (deg, s, dur) in enumerate(m.arp_cell(root)):
            v = vel + (6 if slot == 0 else 0)
            sc.note(ch, en.pitch(n("D4"), AEO, deg), t + s, dur * 0.9, v,
                    jt=3, jv=3)


# ---------------------------------------------------------------------------
# crystal — echoes of the chant tail; glass runs in the feature window
# ---------------------------------------------------------------------------
def _crystal(sc):
    ch = cd.CH_CRYSTAL
    # After each chant statement, its last two tones fall as glass.
    for start in (96.0, 128.0, 192.0):
        t = start + 30.0
        sc.note(ch, en.pitch(CRYSTAL_BASE, AEO, 3) - 12, t, 1.5, 52, jt=4)
        sc.note(ch, en.pitch(CRYSTAL_BASE, AEO, 2) - 12, t + 1.0, 2.5, 50,
                jt=4)
        en.echo_throw(sc, ch, t, base=18, peak=82, release=2.5)
    # The feature window: pentatonic glass runs, one per cycle.
    for k, start in enumerate((160.0, 168.0, 176.0, 184.0)):
        degs = [1, 3, 4, 5, 7, 8, 10, 12] if k % 2 == 0 \
            else [12, 10, 8, 7, 5, 4, 3, 1]
        for i, deg in enumerate(degs):
            sc.note(ch, en.pitch(CRYSTAL_BASE - 12, AEO, deg), start + i * 0.5,
                    0.8, 50 + (4 if i == 0 else 0), jt=3, jv=3)
        en.echo_throw(sc, ch, start + 3.0, base=18, peak=78, release=2.0)


# ---------------------------------------------------------------------------
# piano — corner figure under pedal pools
# ---------------------------------------------------------------------------
def _piano(sc):
    ch = cd.CH_PIANO
    for start in (112.0, 176.0, 240.0):
        en.sustain(sc, ch, start - 0.1, start + 7.8)
        for i, deg in enumerate((1, 3, 5, 8, 9, 8, 5, 3)):
            sc.note(ch, en.pitch(PIANO_BASE, AEO, deg), start + i * 0.5,
                    0.7, 56 - (2 if i % 2 else 0), jt=3, jv=3)
        sc.note(ch, en.pitch(PIANO_BASE, AEO, 1) + 12, start + 4.0, 3.5,
                58, jt=3)


# ---------------------------------------------------------------------------
# guitar — dry off-beat skanks from 208 (the wah arrives with M3)
# ---------------------------------------------------------------------------
def _guitar(sc):
    ch = cd.CH_GUITAR
    for bar in range(12):                          # 208..256
        t = 208.0 + 4.0 * bar
        root = _ground_root(bar)                   # ground phase persists
        pitches = [en.pitch(GTR_BASE, AEO, root + step) for step in (0, 2, 4)]
        for beat in (0.5, 1.5, 2.5, 3.5):
            for j, p in enumerate(pitches):
                sc.note(ch, p, t + beat, 0.3, 50 - j * 2, jt=3, jv=3)


# ---------------------------------------------------------------------------
# whisper, strings, bell — the seam furniture
# ---------------------------------------------------------------------------
def _whisper(sc):
    ch = cd.CH_WHISPER
    en.vowel(sc, ch, 8, 239.0)
    sc.note(ch, n("D4"), 240.0, 8.0, 44, jt=4, jv=2)
    en.expr_curve(sc, ch, [(240.0, 0), (244.0, 66), (248.0, 6)], step=0.5)
    en.lyric(sc, 240.0, "sub rosa")


def _strings(sc):
    ch = cd.CH_STRINGS
    sc.cc(ch, 11, 0, 239.0)
    sc.note(ch, n("D3"), 240.0, 16.0, 52, jt=4, jv=2)
    sc.note(ch, n("A3"), 240.0, 16.0, 48, jt=4, jv=2)
    en.expr_curve(sc, ch, [(240.0, 0), (252.0, 70), (255.5, 78)], step=1.0)


def _bell(sc):
    sc.note(cd.CH_BELL, n("D4"), 64.0, 6.0, 62, jt=0, jv=2)
    sc.note(cd.CH_BELL, n("D4"), 192.0, 6.0, 58, jt=3, jv=2)


def build(sc):
    _drums(sc)
    _bass(sc)
    _pad(sc)
    _choir(sc)
    _arp(sc)
    _crystal(sc)
    _piano(sc)
    _guitar(sc)
    _whisper(sc)
    _strings(sc)
    _bell(sc)
