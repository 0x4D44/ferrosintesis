#!/usr/bin/env python3
"""guitar_bass_demo.py — a short guitar+bass demo for hollowsynth.

Shows off the most-developed families (Pluck / KS guitar+bass, distortion
cabinet) and hammers every MIDI performance effect the engine honours:
  ch0  Steel guitar   (GM 25)  — clean arpeggio intro + clean fills
  ch1  Distortion gtr (GM 30)  — power-chord riff + lead: bends, slides,
                                  hammer-ons/pull-offs (CC68), vibrato wails,
                                  bend-and-hold into CC1 vibrato, CC74 wah
  ch2  Palm mute       (GM 28) — the chugging 8th-note bed
  ch3  Bass fingered  (GM 33)  — groove; program-switches to slap (36) and
                                  fretless (35) for the fill (slide = pitch bend)
  ch9  Drums                   — a simple rock beat for context

Run:  python demos/guitar_bass_demo.py   ->  demos/guitar_bass_demo.mid
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "fable5" / "The Signal Fire"))
import engine as E  # noqa: E402
from engine import Score, arp, bend_ramp, vibrato, wah, cc_curve  # noqa: E402

BPM = 100
sc = Score(seed=530)
sc.tempo(0.0, BPM)
sc.timesig(0.0, 4, 4)

sc.channel(0, "steel",   program=25, volume=90,  pan=58, reverb=40, chorus=14)
sc.channel(1, "lead",    program=30, volume=104, pan=68, reverb=34)
sc.channel(2, "palmmute",program=28, volume=92,  pan=48, reverb=22)
sc.channel(3, "bass",    program=33, volume=100, pan=64, reverb=16)
sc.channel(9, "drums")

# Power chord = root, fifth, octave.
def power(root):     return [root, root + 7, root + 12]
EM, C, G, D, AM = power(40), power(48), power(43), power(50), power(45)


def chug(ch, root, t0, count, step=0.5, vel=96):
    """Palm-muted eighth-note chugs on a root + fifth."""
    for k in range(count):
        v = vel + (8 if k % 2 == 0 else 0)
        sc.note(ch, root, t0 + k * step, step * 0.55, v, jt=2, jv=4)
        sc.note(ch, root + 7, t0 + k * step, step * 0.55, v - 6, jt=2, jv=4)


def beat(t0, bars, fill_last=False):
    for b in range(bars):
        base = t0 + b * 4
        sc.hit(36, base + 0.0, 108); sc.hit(36, base + 1.5, 96)
        sc.hit(36, base + 2.0, 104); sc.hit(36, base + 3.5, 92)
        sc.hit(38, base + 1.0, 104); sc.hit(38, base + 3.0, 108)
        for k in range(8):
            sc.hit(42, base + k * 0.5, 70 + (14 if k % 2 == 0 else 0))
        if fill_last and b == bars - 1:
            for k, t in enumerate([2.0, 2.5, 3.0, 3.5]):
                sc.hit(38 + (0 if k < 2 else 3), base + t, 96 + k * 4)
            sc.hit(49, t0 + bars * 4, 112)


# =========================================================================
# A. Clean intro (beats 0-16): steel arpeggio + bass roots.  Em - C - G - D.
# =========================================================================
sc.marker(0.0, "A. Clean intro")
# bass roots are a real 4-string LOW octave: E1=28, C2=36, G1=31, D2=38
prog = [(EM, 28), (C, 36), (G, 31), (D, 38)]
for i, (ch_notes, bassroot) in enumerate(prog):
    t0 = i * 4
    arp(sc, 0, [ch_notes[0], ch_notes[0] + 12, ch_notes[1] + 5, ch_notes[0] + 12],
        t0, count=8, step=0.5, vel=72, pattern="up", gate=1.2)
    sc.note(3, bassroot, t0, 3.6, 88)
    sc.note(3, bassroot + 12, t0 + 3.0, 1.0, 72)

# =========================================================================
# B. Distorted riff (beats 16-40): power chords + palm-mute chugs + drums.
# =========================================================================
sc.marker(16.0, "B. Distorted riff")
beat(16.0, 6, fill_last=True)
# bass roots one octave BELOW the guitar power chords (E1=28 ... G1=31)
riff = [(EM, 28), (EM, 28), (C, 36), (G, 31), (D, 38), (EM, 28)]
for i, (ch_notes, bassroot) in enumerate(riff):
    t0 = 16.0 + i * 4
    # accented power chord on the downbeat
    for p in ch_notes:
        sc.note(1, p, t0, 1.4, 104, jt=3, jv=4)
    for p in ch_notes:
        sc.note(1, p, t0 + 2.0, 0.9, 96, jt=3, jv=4)
    # palm-mute chug fills the bar
    chug(2, ch_notes[0], t0 + 1.0, 2)
    chug(2, ch_notes[0], t0 + 3.0, 2)
    # bass eighth-note groove: stays deep (root + low fifth, octave-up as accent)
    groove = [bassroot, bassroot, bassroot + 7, bassroot, bassroot + 12, bassroot, bassroot + 7, bassroot]
    for k, bp in enumerate(groove):
        sc.note(3, bp, t0 + k * 0.5, 0.45, 96 + (8 if k % 2 == 0 else 0), jt=2, jv=4)

# =========================================================================
# C. Lead (beats 40-72): every effect on the distortion channel.
#   pentatonic E G A B D  ->  E4=64 G4=67 A4=69 B4=71 D5=74 E5=76 G5=79
# =========================================================================
sc.marker(40.0, "C. Lead - bends, slides, hammer-ons, wah")
beat(40.0, 8, fill_last=True)
# keep the rhythm section under the lead
for i in range(8):
    t0 = 40.0 + i * 4
    root = [40, 40, 45, 45, 43, 43, 50, 40][i]
    chug(2, root, t0, 8, step=0.5, vel=84)
    broot = root - 12          # bass an octave below the palm-mute guitar
    for k in range(8):
        bp = broot + (0 if k % 4 < 2 else 7) + (12 if k == 7 else 0)
        sc.note(3, bp, t0 + k * 0.5, 0.45, 92, jt=2, jv=4)

L = 1  # lead channel
# phrase 1 (40-48): a sung line with a whole-step bend up and a vibrato wail
sc.note(L, 71, 40.0, 1.0, 100)                    # B
sc.note(L, 74, 41.0, 1.0, 100)                    # D
sc.note(L, 76, 42.0, 2.0, 104)                    # E, bend up then wail
bend_ramp(sc, L, 42.0, 42.5, 0.0, 2.0, steps=12)  # bend up a whole step
cc_curve(sc, L, 1, [(43.0, 0), (44.0, 110)], step=0.3)  # CC1 vibrato bloom on the held, bent note
sc.bend(L, 44.05, 0.0)                             # release the bend before next note
sc.note(L, 74, 44.0, 0.5, 96); sc.note(L, 71, 44.5, 0.5, 96)
sc.note(L, 69, 45.0, 3.0, 100)                     # A, held
vibrato(sc, L, 46.0, 2.0, depth=0.5, cycles_per_beat=1.6, delay=0.3)  # hand-drawn vibrato

# phrase 2 (48-56): a fast hammer-on / pull-off run (CC68 legato)
sc.cc(L, 68, 127, 47.9)
hammer = [64, 67, 69, 67, 69, 71, 74, 71, 74, 76]
for k, p in enumerate(hammer):
    sc.note(L, p, 48.0 + k * 0.25, 0.3, 92 + k, jt=1, jv=2)   # overlap -> hammer, not re-pick
sc.cc(L, 68, 0, 48.0 + len(hammer) * 0.25 + 0.2)
sc.note(L, 76, 51.0, 3.0, 104)                     # land on high E, wah it
wah(sc, L, 51.0, 3.0, lo=30, hi=110, cycles_per_beat=0.75)  # CC74 wah sweep
vibrato(sc, L, 52.5, 1.5, depth=0.35, cycles_per_beat=1.5, delay=0.2)

# phrase 3 (56-64): a long slide up (bend_ramp) and a pre-bend release
sc.note(L, 69, 56.0, 1.0, 96)
sc.note(L, 71, 57.0, 3.0, 104)                     # slide up into it, then down-bend
bend_ramp(sc, L, 56.5, 57.0, -2.0, 0.0, steps=12)  # slide up a whole step into B
bend_ramp(sc, L, 59.0, 59.8, 0.0, -2.0, steps=12)  # sink a whole step (release)
sc.bend(L, 60.0, 0.0)
sc.note(L, 76, 60.0, 4.0, 106)                     # big high E, bend+hold+wah+vibrato
bend_ramp(sc, L, 60.0, 60.4, -1.5, 0.0, steps=10)  # scoop into it
wah(sc, L, 60.0, 2.0, lo=45, hi=105, cycles_per_beat=1.0)
cc_curve(sc, L, 1, [(62.0, 20), (63.5, 120)], step=0.3)  # vibrato blooms wide
# phrase 4 (64-72): descending pentatonic answer, clean steel doubling an octave up
answer = [(76, 0.0), (74, 0.75), (71, 1.5), (69, 2.25), (67, 3.0), (64, 4.5)]
for p, off in answer:
    sc.note(L, p, 64.0 + off, 0.7, 98, jt=2, jv=3)
    sc.note(0, p + 12, 64.0 + off, 0.6, 60, jt=2, jv=3)   # clean steel harmony
sc.note(L, 64, 68.5, 3.0, 100)
vibrato(sc, L, 69.5, 2.0, depth=0.4, cycles_per_beat=1.4, delay=0.3)

# =========================================================================
# D. Bass spotlight + close (beats 72-84): slap then fretless slide.
# =========================================================================
sc.marker(72.0, "D. Bass spotlight (slap -> fretless) + close")
beat(72.0, 3)
sc.program(3, 36, 72.0)    # -> slap bass: low thumb (E1/A1/G1) + popped octaves
slap = [28, 28, 40, 35, 28, 31, 40, 28, 33, 33, 45, 40]
for k, bp in enumerate(slap):
    sc.note(3, bp, 72.0 + k * 0.5, 0.4, 96 + (12 if bp >= 40 else 0), jt=2, jv=5)
sc.program(3, 35, 78.0)    # -> fretless, deep
sc.note(3, 28, 78.0, 1.5, 92)
sc.note(3, 33, 79.5, 2.5, 96)
bend_ramp(sc, 3, 78.5, 79.5, -2.0, 0.0, steps=12)   # fretless slide up into A1
vibrato(sc, 3, 80.5, 1.5, depth=0.3, cycles_per_beat=1.2, delay=0.2)  # fretless mwah
sc.bend(3, 82.0, 0.0)

# final Em chord: full band
END = 82.0
for p in EM + [64, 67]:
    sc.note(1, p, END, 4.0, 104)
sc.note(0, 76, END, 4.0, 66); sc.note(0, 79, END, 4.0, 62)
sc.program(3, 33, END - 0.01)
sc.note(3, 28, END, 4.0, 100)          # low E bass
sc.hit(49, END, 118); sc.hit(36, END, 112)

out = REPO / "demos" / "guitar_bass_demo.mid"
sc.write(out, "hollowsynth guitar+bass demo",
         "steel/distortion/palm-mute guitar + fingered/slap/fretless bass, all effects")
print(f"wrote {out}  ({sc.duration_seconds():.1f}s, last beat {sc.last_beat:.1f})")
