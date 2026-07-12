#!/usr/bin/env python3
"""orchestral_demo.py — a short orchestral demo for ferrosintesis.

Exercises the ORCHESTRAL voice families and lots of MIDI performance effects:
  ch0  String ensemble (GM 48)   — SawStack, the sustained bed (CC11 swells)
  ch1  Solo violin    (GM 40)    — Bowed model + LA attack; CC1 vibrato bloom,
                                    pitch-bend scoops, CC68 legato slur run
  ch2  Solo cello     (GM 42)    — Bowed model; hand-drawn pitch-bend vibrato
  ch3  Choir aahs     (GM 52)    — SawStack + formant vowel morph
  ch4  Brass section  (GM 61)    — Brass model; CC11 breath opens the timbre
  ch5  Oboe           (GM 68)    — Reed model; double-reed formant bank

One program per channel with no drums, so `ferrosintesis --solo <ch>` yields a
clean single-program stem.  (Brass 56-63 and reeds 64-71 were unmodeled steel-pluck
fallbacks when this demo was written; both have been modeled families since v0.9.)

Run:  python demos/orchestral_demo.py   ->  demos/orchestral_demo.mid
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "albums" / "fable5" / "The Signal Fire"))
import engine as E  # noqa: E402
from engine import Score, triad, pitch, n, line, pad_block, run, bend_ramp, vibrato, cc_curve  # noqa: E402

MODE = "aeolian"
TONIC = n("A3")            # A natural minor
BPM = 74

sc = Score(seed=411)
sc.tempo(0.0, BPM)
sc.timesig(0.0, 4, 4)

# --- channels -------------------------------------------------------------
sc.channel(0, "strings",  program=48, volume=88,  pan=64, reverb=74)
sc.channel(1, "violin",   program=40, volume=100, pan=76, reverb=58)
sc.channel(2, "cello",    program=42, volume=96,  pan=50, reverb=62)
sc.channel(3, "choir",    program=52, volume=78,  pan=64, reverb=82, chorus=30)
sc.channel(4, "brass",    program=61, volume=100, pan=44, reverb=55)
sc.channel(5, "oboe",     program=68, volume=96,  pan=88, reverb=60)

# Harmony: i - VI - III - VII (Am - F - C - G), the album's dark idiom.
prog_degs = [1, 6, 3, 7]
chords = [triad(TONIC, MODE, d, size=3) for d in prog_degs]

# =========================================================================
# Section 1 (beats 0-16): strings swell in, choir joins.  CC11 crescendo.
# =========================================================================
sc.marker(0.0, "I. Strings + choir")
# two passes of the 4-chord loop, 4 beats each
bed = chords + chords
pad_block(sc, 0, 0.0, bed, span=4.0, size=4, lo=52, hi=79, vel=44, vel_end=70)
cc_curve(sc, 0, 11, [(0.0, 20), (8.0, 90), (16.0, 105)], step=0.5)   # swell
# choir enters at beat 8 on the second pass, higher voicing
pad_block(sc, 3, 8.0, chords, span=4.0, size=3, lo=60, hi=84, vel=40, vel_end=64)
cc_curve(sc, 3, 11, [(8.0, 0), (12.0, 70), (16.0, 84)], step=0.5)

# =========================================================================
# Section 2 (beats 16-32): solo violin theme over the strings.
#   - a pitch-bend scoop into the first note
#   - CC1 mod-wheel vibrato that blooms on the long notes (engine LFO)
#   - a CC68 legato slur run (one bow across fingered notes)
# =========================================================================
sc.marker(16.0, "II. Violin theme")
pad_block(sc, 0, 16.0, bed, span=4.0, size=4, lo=52, hi=79, vel=58)
# violin melody, degrees relative to A4
VB = n("A4")
melody = [
    (1, 0.0, 2.0), (3, 2.0, 1.0), (2, 3.0, 1.0),   # A  C  B
    (1, 4.0, 3.5),                                   # A (held, vibrato)
    (5, 8.0, 1.0), (6, 9.0, 1.0), (7, 10.0, 2.0),    # E  F  G (held)
    (8, 12.0, 3.5),                                  # A octave (held, vibrato)
]
line(sc, 1, 16.0, VB, MODE, melody, vel=92, gate=0.98, jt=3, jv=4)
# scoop up a whole step into the opening A
bend_ramp(sc, 1, 16.0, 16.35, -2.0, 0.0, steps=10)
# CC1 vibrato bloom on the two long notes (A at +4, A8 at +12)
cc_curve(sc, 1, 1, [(16.0, 0), (18.0, 0), (20.0, 95)], step=0.4)     # first held A
cc_curve(sc, 1, 1, [(27.0, 10), (28.0, 100)], step=0.4)             # held A8
# a fast legato slur run (hammer-on/pull-off, CC68) leading into bar 4
run(sc, 1, 24.0, VB, MODE, [8, 7, 6, 5, 6, 7], spacing=0.25, vel0=80, vel1=96, legato=True)

# =========================================================================
# Section 3 (beats 32-44): solo cello counter-melody, hand-drawn vibrato.
# =========================================================================
sc.marker(32.0, "III. Cello")
pad_block(sc, 0, 32.0, chords + [chords[0]], span=4.0, size=4, lo=48, hi=72, vel=52)
pad_block(sc, 3, 32.0, chords, span=4.0, size=3, lo=58, hi=81, vel=44)
CB = n("A3")
cello = [
    (5, 0.0, 3.0), (4, 3.0, 1.0),      # E  D
    (3, 4.0, 4.0),                      # C (held)
    (2, 8.0, 2.0), (1, 10.0, 2.0),      # B  A
]
line(sc, 2, 32.0, CB, MODE, cello, vel=88, gate=0.99, jt=3, jv=3)
vibrato(sc, 2, 36.0, 4.0, depth=0.28, cycles_per_beat=1.3, delay=0.6)  # on the held C

# =========================================================================
# Section 4 (beats 44-56): BRASS fanfare.  *** exposes the fallback ***
# =========================================================================
sc.marker(44.0, "IV. Brass (UNMODELED - fallback pluck)")
pad_block(sc, 0, 44.0, [chords[0], chords[3]], span=4.0, size=4, lo=48, hi=72, vel=60)
BR = n("A3")
# a rising fanfare with stabs then a sustained call
brass = [
    (1, 0.0, 0.5), (3, 0.5, 0.5), (5, 1.0, 1.0),   # A C E stab
    (5, 2.0, 0.5), (6, 2.5, 0.5), (8, 3.0, 2.0),   # E F A (held)
    (7, 6.0, 1.0), (5, 7.0, 3.0),                   # G  E (held)
]
line(sc, 4, 44.0, BR, MODE, brass, vel=104, gate=0.9, jt=2, jv=4)
# a bend + vibrato on the sustained brass notes (what a real brass model would use)
bend_ramp(sc, 4, 44.0 + 3.0, 44.0 + 3.3, -1.0, 0.0, steps=8)
vibrato(sc, 4, 44.0 + 7.0, 3.0, depth=0.2, cycles_per_beat=1.4, delay=0.7)

# =========================================================================
# Section 5 (beats 56-66): OBOE solo.  *** exposes the fallback ***
# =========================================================================
sc.marker(56.0, "V. Oboe (UNMODELED - fallback pluck)")
pad_block(sc, 0, 56.0, [chords[1], chords[2], chords[0]], span=4.0, size=4,
          lo=48, hi=72, vel=46, vel_end=40)
OB = n("A4")
oboe = [
    (5, 0.0, 1.5), (4, 1.5, 0.5), (3, 2.0, 2.0),    # E D C(held)
    (2, 4.0, 1.0), (1, 5.0, 3.0),                    # B A(held)
]
line(sc, 5, 56.0, OB, MODE, oboe, vel=90, gate=0.98, jt=3, jv=3)
bend_ramp(sc, 5, 56.0, 56.3, -2.0, 0.0, steps=10)       # reed scoop
cc_curve(sc, 5, 1, [(58.0, 0), (59.0, 90)], step=0.4)    # vibrato bloom on held C
vibrato(sc, 5, 61.0, 3.0, depth=0.3, cycles_per_beat=1.5, delay=0.5)  # on held A

# final tutti Am chord, everyone
END = 66.0
for ch, lo, hi, vel in [(0, 45, 76, 78), (3, 57, 84, 60)]:
    for p in E.voice_lead([57, 60, 64], None, 4, lo, hi):
        sc.note(ch, p, END, 4.0, vel, jt=2, jv=3)
sc.note(2, 45, END, 4.0, 84)     # cello low A
sc.note(1, 69, END, 4.0, 88)     # violin A4

out = REPO / "demos" / "orchestral_demo.mid"
sc.write(out, "hollowsynth orchestral demo",
         "strings/solo-strings/choir modeled; brass+oboe fall back to pluck")
print(f"wrote {out}  ({sc.duration_seconds():.1f}s, last beat {sc.last_beat:.1f})")
