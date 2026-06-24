"""
07 - Snow   (A aeolian, 60 bpm)  — the interlude; the quiet eye between two storms.

The smallest track on *Vigil*: solo piano almost throughout, intimate and fragile.
Slow broken chords with lots of space and pedal; a bare falling right-hand melody
(the memory motif, 5-4-3 = E-D-C in A minor); and only at the very end a whisper of
high string pad. Very low dynamics throughout — the Arc peaks near 0.4 and the piece
ends suspended, barely there (an unresolved Am add9, the high B left hanging).

Harmony: gentle A aeolian, one chord per bar, a lament-leaning descent that keeps
returning home — Am - F - C - G threaded with Em and Dm, the bass stepping downward.

Run from the tracks/ dir (or anywhere): python 07_snow.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord,
                    voiced_bars, tied_line, pad, piano_chords, melody,
                    expression, fade_out, write_midi, print_report)

random.seed(7)
BPB = 4
ctx = Ctx(bpm=60, root='A', mode='aeolian', beats_per_bar=BPB)

CH_PIANO, CH_PAD = 0, 1
sc = Score(ctx)
sc.program(CH_PIANO, 0, 'Piano')
sc.program(CH_PAD, 49, 'Strings')

# ---------------------------------------------------------------------------
# Harmony — one chord per bar. A 8-bar progression that descends in the bass
# (A-G-F-E-D-... lament feel) and keeps coming home to Am. 32 bars = 4 passes,
# the last pass thinned to a suspended close. Plus a 1-bar pickup of pure space.
# ---------------------------------------------------------------------------
PROG = [
    (chord('A','C','E'), 45),   # Am   — home
    (chord('F','A','C'), 41),   # F    \
    (chord('C','E','G'), 48),   # C     descent / lift
    (chord('G','B','D'), 43),   # G
    (chord('A','C','E'), 45),   # Am
    (chord('E','G','B'), 40),   # Em   — the sigh, bass low E
    (chord('D','F','A'), 38),   # Dm
    (chord('G','B','D'), 43),   # G    — half-cadence, leaning back home
]
NPASS = 4
NB = len(PROG) * NPASS                      # 32 bars
bar_chord = [PROG[b % 8][0] for b in range(NB)]
bar_bass  = [PROG[b % 8][1] for b in range(NB)]

# Right-hand voicings (close, mid-register piano) — voice-led for soft suspensions.
rh_voi, _ = voiced_bars(bar_chord, 3, (55, 72))

# ---------------------------------------------------------------------------
# The Arc — one slow breath, peaking ~0.4 (this is the most fragile track).
# Enter from near-silence; a single gentle swell mid-piece; recede to nothing.
# ---------------------------------------------------------------------------
arc = Arc([
    ("hush",    8, 0.05, 0.14),
    ("opening", 8, 0.16, 0.30),
    ("bloom",   8, 0.34, 0.40),   # the one (very modest) high point
    ("settle",  6, 0.30, 0.10),
    ("vanish",  2, 0.08, 0.03),
], beats_per_bar=BPB, breathe=0.035)

# ---------------------------------------------------------------------------
# Solo piano: slow broken chords with pedal. Low velocities; the bass note of
# each bar is the chord root an octave down, the rest a gentle upward roll.
# ---------------------------------------------------------------------------
piano_chords(sc, CH_PIANO, 0, rh_voi, [b - 0 for b in bar_bass], BPB, arc,
             eighths=False, vlo=22, vhi=52, pedal=True)

# ---------------------------------------------------------------------------
# The bare memory motif (5-4-3 = E-D-C), surfacing in the right hand high above
# the chords. A4 = 69 is degree 1; motif sits up at E5/D5/C5. It appears a few
# times, each entrance starting on a downbeat of a bar, sparse and unhurried.
# Built as (semitone-from-A4, start-beat, dur) so it reads as the falling sigh.
# ---------------------------------------------------------------------------
A4 = 69
# 5-4-3 then a downward continuation 3-2-1 (E-D-C ... C-B-A) — the lament, bare.
MOTIF = theme_from_degrees('aeolian', [
    (5, 0.0, 3.0), (4, 3.0, 1.0),        # E - D
    (3, 4.0, 3.5),                        # C  (held, the sigh resolving down)
])
MOTIF2 = theme_from_degrees('aeolian', [
    (5, 0.0, 2.0), (4, 2.0, 2.0),        # E - D
    (3, 4.0, 2.0), (2, 6.0, 1.0), (1, 7.0, 1.0),   # C - B - A : full fall home
])
# Place motif entrances on chosen bar-starts (beats). Sparse, with silence between.
for bar in (2, 10, 18):
    melody(sc, CH_PIANO, bar * BPB, MOTIF, A4, arc, vlo=30, vhi=54, gate=0.98, max_jit=8)
melody(sc, CH_PIANO, 26 * BPB, MOTIF2, A4, arc, vlo=28, vhi=50, gate=0.98, max_jit=8)

# ---------------------------------------------------------------------------
# A whisper of high string pad — only in the last few bars (from bar 28),
# barely audible, two thin voices high above the piano. Enters under the final
# fall and is left hanging on an Am add9 (the high B), fading to nothing.
# ---------------------------------------------------------------------------
PAD_START = 28
pad_chords = [None] * PAD_START + [bar_chord[b] for b in range(PAD_START, NB)]
pad(sc, CH_PAD, 0, pad_chords, BPB, arc, n_voices=2, band=(76, 88),
    vlo=14, vhi=30, cc_floor=18)

# ---------------------------------------------------------------------------
# Suspended coda: a bare Am held in the piano, with a high unresolved B (the 9th)
# left ringing in the strings. Everything fades to barely-there.
# ---------------------------------------------------------------------------
t = NB * BPB
# piano: low A + C + E, soft, with pedal held then released into the fade
sc.cc(CH_PIANO, 64, 127, t)
for p in (45, 52, 57, 64):              # A2, E3, A3, E4 — open, hollow
    sc.note(CH_PIANO, p, t, 9.0, 26, max_jit=6)
sc.note(CH_PIANO, 72, t + 1.0, 8.0, 24, max_jit=6)     # high C5 (the b3), bare
sc.cc(CH_PIANO, 64, 0, t + 9.0)
# strings: the hanging B (the add9), barely sounding
sc.note(CH_PAD, 83, t + 0.5, 8.5, 20, max_jit=6)        # B5 — unresolved 9th
sc.note(CH_PAD, 76, t + 0.5, 8.5, 18, max_jit=6)        # E5
fade_out(sc, [CH_PIANO, CH_PAD], t, 9.0, beats=12, top=42)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '07 - Snow.mid')
write_midi(sc, OUT, title='Snow', text='Vigil / 7', key='Am')
print_report(OUT, allowed_pcs=["A", "B", "C", "D", "E", "F", "G"])
