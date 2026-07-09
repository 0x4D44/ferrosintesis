"""
01 - Of the Light That Stays   (D aeolian, 60 bpm)  — the opening elegy.

WORKED EXAMPLE for the album engine. A slow, introspective passacaglia: a descending
diatonic lament bass (Dm-C-Bb-Am7-Gm7-F-Em7b5-Dm) under a singing theme of downward
suspensions. One long swell from near-silence to a single climax (violin soaring to
F6) and back to a dissolving, unresolved Dm.

Run from the tracks/ dir (or anywhere): python 01_of_the_light_that_stays.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord,
                    nearest_above, pad, bass, melody, piano_chords, expression,
                    fade_out, voiced_bars, write_midi, print_report)

random.seed(48)
BPB = 4
ctx = Ctx(bpm=60, root='D', mode='aeolian', beats_per_bar=BPB)

# Channels (GM): piano, cello, violin, viola, contrabass, strings I + II under-pad
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# The passacaglia: per-bar (chord pcs, contrabass pitch) — bass descends a full octave
GROUND = [
    (chord('D','F','A'),      50), (chord('C','E','G'),      48),
    (chord('Bb','D','F'),     46), (chord('A','C','E','G'),  45),
    (chord('G','Bb','D','F'), 43), (chord('F','A','C'),      41),
    (chord('E','G','Bb','D'), 40), (chord('D','F','A'),      38),
]
D4 = 62
THEME = theme_from_degrees('aeolian', [
    (5,0,3),(6,3,1), (5,4,2),(4,6,2), (3,8,2),(4,10,1),(3,11,1), (2,12,2),(1,14,2),
    (6,16,2),(8,18,2), (10,20,2),(9,22,1),(8,23,1), (8,24,2),(6,26,2), (3,28,3),(1,31,1),
])

# Form: one long swell to a climax just past the golden section, then dissolution.
# (name, n_bars, lvl_start, lvl_end)
SECTIONS = [
    ("intro",   8, 0.06, 0.18), ("A",     8, 0.20, 0.30), ("A'",   8, 0.30, 0.42),
    ("B",       8, 0.44, 0.58), ("B'",    8, 0.58, 0.70), ("climax",16, 0.74, 0.96),
    ("descent", 8, 0.62, 0.34), ("coda",  8, 0.26, 0.05),
]
arc = Arc(SECTIONS, beats_per_bar=BPB)
ROLES = {  # per section: which instruments + texture
    "intro":  dict(pad=1,pad2=0,bass=1,cello=0,violin=0,viola=0,piano=0,eighths=0,climax=0),
    "A":      dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,climax=0),
    "A'":     dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=1,eighths=0,climax=0),
    "B":      dict(pad=1,pad2=1,bass=1,cello=0,violin=1,viola=1,piano=1,eighths=0,climax=0),
    "B'":     dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,climax=0),
    "climax": dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,climax=1),
    "descent":dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,climax=0),
    "coda":   dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,climax=0),
}

# Expand the form into cycles (each = one 8-bar pass of the ground)
cycles = []
for (name, nb, _a, _b) in SECTIONS:
    for _ in range(nb // 8):
        cycles.append(name)
NB = len(cycles) * 8
bar_chord = [GROUND[b % 8][0] for b in range(NB)]
bar_bass  = [GROUND[b % 8][1] for b in range(NB)]

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * 8
    return out

pad_on, pad2_on, bass_on, viola_on = mask('pad'), mask('pad2'), mask('bass'), mask('viola')

# Sustained, voice-led pad across the whole piece (also feeds the piano)
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)], 4, (57, 81))
for vi in range(4):
    from engine import tied_line
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 30, 92)
expression(sc, CH_PAD, 0, NB * BPB, arc, 34)

# Warm under-pad: root (octave above bass) + the chord's actual fifth
def pad2_pitches(pcs, b):
    root = b + 12
    want = (root % 12 + 7) % 12
    fifth = min(pcs, key=lambda x: min((x - want) % 12, (want - x) % 12))
    return [root, nearest_above(fifth, root)]
for vi in range(2):
    from engine import tied_line
    tied_line(sc, CH_PAD2, 0,
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None for b in range(NB)],
              BPB, arc, 26, 74)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 30)

# Viola inner voice: the 3rd of each chord, tied
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(55, 75) if q % 12 == third % 12), 60)
from engine import tied_line
tied_line(sc, CH_VIOLA, 0, [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 28, 70)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 32)

# Contrabass: the descending lament ground
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)], BPB, arc, 34, 88, cc_floor=40)

# Melody (cello / violin) + piano, per cycle
for ci, nm in enumerate(cycles):
    t = ci * 8 * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci * 8:(ci + 1) * 8]
    if roles['piano']:
        piano_chords(sc, CH_PIANO, t, seg, [bar_bass[ci*8+i] + 12 for i in range(8)], BPB, arc,
                     eighths=bool(roles['eighths']))
    if roles['cello']:
        melody(sc, CH_CELLO, t, THEME, D4 - 12, arc, 48, 65)
    if roles['violin']:
        melody(sc, CH_VIOLIN, t, THEME, D4 + (12 if roles['climax'] else 0), arc, 60, 110)

# Coda tail: a dissolving Dm with a high unresolved E (the 9th), fading out
t = NB * BPB
pv = voice_chord(chord('D','F','A'), pad_voi[-1], 4, 57, 81)
for p in pv:
    sc.note(CH_PAD, p, t, 10.0, 40, max_jit=6)
sc.note(CH_BASS, 38, t, 10.0, 36, max_jit=6)
sc.note(CH_CELLO, 50, t, 10.0, 34, max_jit=6)
sc.note(CH_VIOLIN, ctx.deg(2, D4), t + 1.0, 9.0, 30, max_jit=6)   # high E glimmer
fade_out(sc, [CH_PAD, CH_BASS, CH_CELLO, CH_VIOLIN], t, 10.0)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '01 - Of the Light That Stays.mid')
write_midi(sc, OUT, title='Of the Light That Stays',
           text='Vigil / I — in the manner of Max Richter', key='Dm')
print_report(OUT, allowed_pcs=['D','E','F','G','A','Bb','C'])
