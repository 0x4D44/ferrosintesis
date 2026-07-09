"""
02 - First Light   (F major, 72 bpm)  — fragile hope, a gentle awakening after grief.

The brightest, lightest piece on the album: tender, not triumphant. Piano alone rocks
broken-chord 8ths (the gentle side of Glass, Richter's "Vladimir's Blues"); a cello
sings a simple rising line; violin and a light high pad join for one MODEST mid-swell
(the Arc peaks only ~0.6 — this is hope, not climax); then it gently subsides and
closes warm on a soft Fadd9/F6.

Harmony: a warm rocking loop in F major — F - Dm7 - Bb(maj7) - C  (I - vi - IV - V) —
with the album's memory motif (5-4-3 = C-Bb-A) surfacing in the cello/violin and
shading softly toward relative D minor.

Run from anywhere: python 02_first_light.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(2)
BPB = 4
ctx = Ctx(bpm=72, root='F', mode='ionian', beats_per_bar=BPB)

# Channels (GM): piano, cello, violin, viola, contrabass, high strings pad
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD = range(6)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'), CH_PAD:(48,'Strings High'),
}.items():
    sc.program(ch, prog, nm)

# ---------------------------------------------------------------------------
# The rocking loop: per-bar (chord pcs, bass root).  F - Dm7 - Bb maj7 - C
# Bass walks gently down then up so the 4-bar cell breathes (F-D-Bb-C).
# ---------------------------------------------------------------------------
LOOP = [
    (chord('F','A','C'),           41),   # F      (I)
    (chord('D','F','A','C'),       38),   # Dm7    (vi7)
    (chord('Bb','D','F','A'),      34),   # Bbmaj7 (IV)
    (chord('C','E','G'),           36),   # C      (V)
]
NB = 64                                   # 64 bars * (4 beats / 72bpm) ~= 3:33
bar_chord = [LOOP[b % 4][0] for b in range(NB)]
bar_bass  = [LOOP[b % 4][1] for b in range(NB)]

# Memory motif (5-4-3 in F = C-Bb-A), here a SIMPLE RISING cello line that lands
# on the falling sigh — a question that finds its answer. theme = (deg,start,dur).
F4 = 65  # cello/violin base = degree-1 pitch (F)
RISE = theme_from_degrees('ionian', [
    (1,0,2),(2,2,2), (3,4,3),(2,7,1),          # bar1-2: rise 1-2-3, sigh back to 2
    (5,8,2),(6,10,2), (5,12,2),(4,14,1),(3,15,1),  # bar3-4: up to 6, the 5-4-3 sigh
    (5,16,2),(4,18,2), (3,20,3),(2,23,1),      # bar5-6: 5-4-3-2 descent
    (1,24,4), (3,28,2),(2,30,2),               # bar7-8: settle, gentle lift-and-fall
])

# ---------------------------------------------------------------------------
# The Arc — ONE modest swell. Peaks only ~0.6 (hope, not climax), then recedes.
# 8-bar units. Piano-alone intro near-silence -> cello -> +violin/pad mid-swell
# -> gentle subside -> warm fade.
# (name, n_bars, lvl_start, lvl_end)
# ---------------------------------------------------------------------------
SECTIONS = [
    ("intro",  8, 0.05, 0.14),   # piano alone, rocking
    ("A",      8, 0.18, 0.30),   # cello enters, rising line
    ("A'",     8, 0.30, 0.42),   # cello continues, pad shimmers in
    ("swell",  8, 0.44, 0.60),   # violin joins — the modest peak (~0.6)
    ("hold",   8, 0.60, 0.52),   # sustain the hope, just past golden section
    ("ebb",    8, 0.46, 0.30),   # violin recedes, cello sings alone again
    ("settle", 8, 0.26, 0.14),   # piano + cello, thinning
    ("coda",   8, 0.12, 0.04),   # piano alone again -> warm close
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.045)

# Per-section roles
ROLES = {
    "intro":  dict(pad=0, cello=0, violin=0, viola=0, bass=0, piano=1),
    "A":      dict(pad=0, cello=1, violin=0, viola=0, bass=1, piano=1),
    "A'":     dict(pad=1, cello=1, violin=0, viola=1, bass=1, piano=1),
    "swell":  dict(pad=1, cello=1, violin=1, viola=1, bass=1, piano=1),
    "hold":   dict(pad=1, cello=1, violin=1, viola=1, bass=1, piano=1),
    "ebb":    dict(pad=1, cello=1, violin=0, viola=1, bass=1, piano=1),
    "settle": dict(pad=0, cello=1, violin=0, viola=0, bass=1, piano=1),
    "coda":   dict(pad=0, cello=0, violin=0, viola=0, bass=0, piano=1),
}

cycles = []  # section name per bar
for (name, nb, _a, _b) in SECTIONS:
    cycles += [name] * nb

def mask(layer):
    return [bool(ROLES[cycles[b]][layer]) for b in range(NB)]

pad_on, cello_on, violin_on = mask('pad'), mask('cello'), mask('violin')
viola_on, bass_on, piano_on = mask('viola'), mask('bass'), mask('piano')

# ---------------------------------------------------------------------------
# Piano — the rocking heart: broken 8th-note chords with sustain-pedal blur.
# Voiced gently in the middle register so it stays tender, never busy.
# ---------------------------------------------------------------------------
pno_voi, _ = voiced_bars([bar_chord[b] if piano_on[b] else None for b in range(NB)],
                         4, (53, 74))
pno_roots = [bar_bass[b] + 12 if piano_on[b] else None for b in range(NB)]
piano_chords(sc, CH_PIANO, 0, pno_voi, pno_roots, BPB, arc, eighths=True, vlo=24, vhi=58)

# ---------------------------------------------------------------------------
# Light high pad — only a 2-voice shimmer up top, voice-led & tied (breathing).
# Soft floor; never dominates the piano.
# ---------------------------------------------------------------------------
pad(sc, CH_PAD, 0, [bar_chord[b] if pad_on[b] else None for b in range(NB)],
    BPB, arc, n_voices=2, band=(74, 86), vlo=20, vhi=58, cc_floor=26)

# Viola inner warmth — the 3rd of each chord, tied, low dynamic.
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(55, 74) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 22, 56)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 28)

# Contrabass — gentle sustained root, very soft (this is the lightest track).
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)],
     BPB, arc, vlo=24, vhi=54, sustain=True, cc_floor=30)

# ---------------------------------------------------------------------------
# Melody — cello first (warm, low), then violin doubles an octave up at the swell.
# Played once per 8-bar cycle where the role is on.
# ---------------------------------------------------------------------------
for ci in range(NB // 8):
    nm = cycles[ci * 8]
    t = ci * 8 * BPB
    r = ROLES[nm]
    if r['cello']:
        melody(sc, CH_CELLO, t, RISE, F4 - 12, arc, vlo=40, vhi=74)
    if r['violin']:
        melody(sc, CH_VIOLIN, t, RISE, F4 + 12, arc, vlo=44, vhi=84)

# ---------------------------------------------------------------------------
# Coda — a warm, soft close on Fadd9/F6: F-A-C + D (6th) and G (9th), the
# brightest possible resolution. Piano arpeggio dissolving under a held string glow.
# ---------------------------------------------------------------------------
t = NB * BPB
# Soft piano roll of the Fadd9/F6 colour
add9 = [41, 45, 48, 53, 57, 60, 62, 64]  # F2 A2 C3 F3 A3 C4 D4 E4-ish spread
sc.cc(CH_PIANO, 64, 127, t)
roll = [53, 57, 60, 62, 65, 67]          # F3 A3 C4 D4 F4 G4 — F6/add9 shimmer
for k, p in enumerate(roll):
    sc.note(CH_PIANO, p, t + k * 0.5, 8.0 - k * 0.4, 30 + random.randint(-3, 3), max_jit=6)
sc.cc(CH_PIANO, 64, 0, t + 12.0)
# Held string glow: F-A-C-D (F6) high, very soft
for p in (62, 65, 69, 72):               # D4 F4 A4 C5
    sc.note(CH_PAD, p, t + 0.5, 10.5, 28, max_jit=5)
sc.note(CH_CELLO, 41, t, 11.0, 30, max_jit=6)   # low F warmth
sc.note(CH_VIOLA, 57, t + 0.5, 10.0, 26, max_jit=5)  # A
fade_out(sc, [CH_PIANO, CH_PAD, CH_CELLO, CH_VIOLA], t, 11.0, top=58)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '02 - First Light.mid')
write_midi(sc, OUT, title='First Light', text='Vigil / 2', key='F')
print_report(OUT, allowed_pcs=['F','G','A','Bb','C','D','E'])
