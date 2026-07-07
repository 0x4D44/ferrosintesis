"""m6_lastlight — Part Two, Movement 6 "Last Light"
(beats 896-1024, E ionian, rit 118->60).  The guests depart, and the
Guest theme finally RESOLVES.

Roadmap section 4, M6 — the emotional payoff of the whole piece.  Layers
enter one at a time; the theme is allowed to sing; everything is warm and
conclusive.

  ch1 sweep pad (prog 95 @896): E(add9) bed, CC74 CLOSING 95->30 across
        the movement (the mirror of M1's opening sweep), CC11 fading to
        ~20 by ~1020, aftertouch blooms breathing inside the held chord.
  ch0 piano: CC67 una corda back ON; theme PHRASE 2 (bars 5-8) stated
        slow and pooled under balanced CC64 sustain pairs.
  ch8 nylon: theme BARS 7-8 farewell, fingerpicked.
  ch3 fretless (prog 35 @896): slide tones on degrees 1 and 5 (bend_ramp
        scoops, recentred after each; final recentre before 1024).
  ch6 choir I: THE FINAL HUM — theme BARS 1-3, vowel mm (CC70=0), and
        THIS TIME IT ENDS ON DEGREE 1 (the resolution Part One refused);
        aftertouch bloom then decay; lyric metas "Mm... hm... mm...
        (goodnight)".
  ch14 flute (prog 73 @896): distant echo wisps, high, with echo throws.
  ch15 ONE tubular bell (prog 14) on E @~1000 — warm, not crystalline.

Settles onto a warm E MAJOR triad (E-G#-B, the tierce de Picardie) that
rings into the fade by ~1020; silence + tail.  CC91 ~75 on all of the
movement's channels at 896 (far again, the guests receding).
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m

ION = "ionian"

T0, T1 = 896.0, 1024.0

# Degree-1 anchors per channel (E in various octaves).
PAD_BASE = en.n("E3")      # 52
PIANO_BASE = en.n("E4")    # 64 — the phrase-2 melody sings mid-high
CHOIR_BASE = en.n("E3")    # 52 — the low baritone hum (as Part One)
NYLON_BASE = en.n("E4")    # 64
BASS_BASE = en.n("E2")     # 40 — warm low pedal
FLUTE_BASE = en.n("E5")    # 76 — distant, high
BELL_PITCH = en.n("E4")    # 64 — a warm tubular strike

MY_CHANNELS = (cd.CH_PIANO, cd.CH_PAD, cd.CH_BASS, cd.CH_CHOIR1,
               cd.CH_NYLON, cd.CH_WINDS, cd.CH_BELLS)

# E(add9): E G# B (E) F#, and the E MAJOR triad it settles onto — the ninth
# falls away but the G# (the tierce de Picardie, pc8) stays: the parallel-
# major arc must ARRIVE on a major third, not evaporate to a bare fifth.
PAD_ADD9 = [en.pitch(PAD_BASE, ION, d) for d in (1, 3, 5, 8, 9)]   # 52 56 59 64 66
PAD_CLOSE = [en.pitch(PAD_BASE, ION, d) for d in (1, 3, 5)]        # 52 56 59  E G# B

# Theme slices (rebased to start at beat 0).
THEME_P2 = [(d, s - 16.0, du) for d, s, du in m.THEME[12:]]        # bars 5-8
BARS78 = [(d, s - 24.0, du) for d, s, du in m.THEME[18:]]          # bars 7-8
CHOIR_1_3 = list(m.THEME[:10])                                     # bars 1-3


# ---------------------------------------------------------------------------
# Controllers — the distance ride, the closing filter, the volume fade
# ---------------------------------------------------------------------------
def _controllers(sc):
    # CC91 ~75 on every channel of the movement at the downbeat: the guests
    # recede into the far distance again.
    for ch in MY_CHANNELS:
        sc.cc(ch, 91, 75, T0)

    # The pad's CLOSING sweep — the exact mirror of M1's opening (95 -> 30),
    # and the master expression fade to a near-silent ~18 by ~1020.
    en.cc_curve(sc, cd.CH_PAD, 74, [(T0, 95), (1020.0, 30)], step=4.0)
    en.expr_curve(sc, cd.CH_PAD, [(T0, 92), (1000.0, 68), (1020.0, 18)],
                  step=2.0)
    # Pad aftertouch: two slow blooms breathing inside the held chord, then
    # settling to nothing as the fifth fades.
    en.at_curve(sc, cd.CH_PAD,
                [(T0, 0), (914.0, 84), (940.0, 24), (962.0, 52),
                 (984.0, 80), (1006.0, 18), (1020.0, 0)], step=0.5)

    # Piano: una corda back on for the whole farewell (off just before end).
    en.soft_pedal(sc, cd.CH_PIANO, T0, 1023.5)


# ---------------------------------------------------------------------------
# ch1 — the E(add9) sweep-pad bed, closing down to a bare fifth
# ---------------------------------------------------------------------------
def _pad(sc):
    # Swell A: the full add9, entering under the departing M5 ring.
    vels_a = (51, 49, 50, 48, 46)
    for p, v in zip(PAD_ADD9, vels_a):
        sc.note(cd.CH_PAD, p, T0, 66.0, v, jt=2, jv=2)
    # Swell B: a second breath of the add9, overlapping A.
    vels_b = (49, 47, 48, 46, 44)
    for p, v in zip(PAD_ADD9, vels_b):
        sc.note(cd.CH_PAD, p, 958.0, 48.0, v, jt=2, jv=2)
    # The closing E MAJOR triad (E-G#-B): the ninth falls away but the major
    # third stays and rings on into the fade (last note-off ~1020, then
    # silence + tail) — the tierce de Picardie the whole arc resolves onto.
    for p, v in zip(PAD_CLOSE, (45, 41, 43)):
        sc.note(cd.CH_PAD, p, 1000.0, 20.0, v, jt=2, jv=2)


# ---------------------------------------------------------------------------
# ch0 — piano: theme phrase 2, slow and pooled under una corda + sustain
# ---------------------------------------------------------------------------
def _piano(sc):
    # Two balanced sustain-pedal pairs pool the two halves of the phrase.
    en.sustain(sc, cd.CH_PIANO, 901.8, 909.6)
    en.sustain(sc, cd.CH_PIANO, 909.9, 918.4)
    # Soft left-hand E3/B3 dyads ground each half; the pedal pools them.
    for b in (902.0, 910.0):
        sc.note(cd.CH_PIANO, en.n("E3"), b, 8.0, 45, jt=4, jv=3)
        sc.note(cd.CH_PIANO, en.n("B3"), b, 8.0, 43, jt=4, jv=3)
    # The phrase-2 melody, a gentle rise across the statement.
    en.line(sc, cd.CH_PIANO, 902.0, PIANO_BASE, ION, THEME_P2,
            48, vel_end=52, gate=0.9, jt=4, jv=3)


# ---------------------------------------------------------------------------
# ch8 — nylon: theme bars 7-8, the fingerpicked farewell
# ---------------------------------------------------------------------------
def _nylon(sc):
    sc.note(cd.CH_NYLON, en.n("E3"), 926.0, 8.0, 44, jt=4, jv=3)   # low root
    en.line(sc, cd.CH_NYLON, 926.0, NYLON_BASE, ION, BARS78,
            48, vel_end=52, gate=0.92, jt=4, jv=3)


# ---------------------------------------------------------------------------
# ch6 — choir I: THE FINAL HUM, resolving on degree 1
# ---------------------------------------------------------------------------
def _choir(sc):
    # Vowel mm for the whole hum (set at the downbeat and again at entry).
    en.vowel(sc, cd.CH_CHOIR1, 0, T0)
    en.vowel(sc, cd.CH_CHOIR1, 0, 944.0)

    # Bars 1-3 of the theme, low and wordless.
    en.line(sc, cd.CH_CHOIR1, 944.0, CHOIR_BASE, ION, CHOIR_1_3,
            48, vel_end=54, gate=0.96, jt=4, jv=3)
    # ... and instead of Part One's hanging leading tone, it RESOLVES: the
    # tonic held long, blooming then decaying to nothing.
    sc.note(cd.CH_CHOIR1, en.pitch(CHOIR_BASE, ION, 1), 956.0, 22.0, 54,
            jt=3, jv=2)
    en.at_curve(sc, cd.CH_CHOIR1,
                [(944.0, 8), (956.0, 58), (966.0, 90), (978.0, 8)],
                step=0.25)

    # Displayed humming — the last words of the piece.
    en.lyric(sc, 944.0, "Mm...")
    en.lyric(sc, 950.0, "hm...")
    en.lyric(sc, 956.0, "mm...")
    en.lyric(sc, 968.0, "(goodnight)")


# ---------------------------------------------------------------------------
# ch3 — fretless bass: slide tones on degrees 1 and 5, recentred after each
# ---------------------------------------------------------------------------
def _slide(sc, deg, t, dur, vel, scoop):
    """A fretless scoop: strike below pitch, glide up to it, hold centred."""
    p = en.pitch(BASS_BASE, ION, deg)
    sc.bend(cd.CH_BASS, t - 0.05, scoop)
    sc.note(cd.CH_BASS, p, t, dur, vel, jt=2, jv=3)
    en.bend_ramp(sc, cd.CH_BASS, t, t + 0.6, scoop, 0.0, steps=8)


def _bass(sc):
    _slide(sc, 1, 906.0, 14.0, 50, -1.8)     # E, scooped
    _slide(sc, 5, 924.0, 10.0, 48, -1.5)     # B, scooped
    _slide(sc, 1, 948.0, 16.0, 49, -1.8)     # E again, under the hum
    _slide(sc, 1, 992.0, 20.0, 46, -1.5)     # the final low E into the fade
    sc.bend(cd.CH_BASS, 1014.0, 0.0)         # recentre well before 1024


# ---------------------------------------------------------------------------
# ch14 — flute: distant echo wisps
# ---------------------------------------------------------------------------
def _flute(sc):
    # Echo of the piano phrase's fall, high and far.
    en.line(sc, cd.CH_WINDS, 920.5, FLUTE_BASE, ION,
            [(3, 0.0, 1.0), (1, 1.0, 2.0)], 47, gate=0.9, jt=4, jv=3)
    en.echo_throw(sc, cd.CH_WINDS, 920.5, base=20, peak=80, release=2.5)
    # A last high E answering the choir's resolution, then gone.
    sc.note(cd.CH_WINDS, en.pitch(FLUTE_BASE, ION, 1), 986.0, 4.0, 45,
            jt=4, jv=3)
    en.echo_throw(sc, cd.CH_WINDS, 986.0, base=20, peak=72, release=3.0)


# ---------------------------------------------------------------------------
# ch15 — ONE warm bell on E
# ---------------------------------------------------------------------------
def _bell(sc):
    sc.note(cd.CH_BELLS, BELL_PITCH, 1000.0, 10.0, 56, jt=2, jv=3)


def build(sc):
    _controllers(sc)
    _pad(sc)
    _piano(sc)
    _nylon(sc)
    _choir(sc)
    _bass(sc)
    _flute(sc)
    _bell(sc)
