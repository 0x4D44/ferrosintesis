"""
12 - The Light We Keep   (D minor -> D MAJOR, Picardy, 60 bpm)  — the finale.

The cycle-closing summation. We begin hushed in D minor, recapitulating track 1's
memory motif (5-4-3) over the same descending lament ground. The ensemble gathers;
we pass through a darker swell that remembers the tragedy; then the long-withheld grief
finally turns into LIGHT — a radiant cathartic climax that resolves to D MAJOR via the
Picardy third (F#, C#), the ONLY true major resolution on the album. A long luminous,
peaceful close: a warm Dadd9, fading like dawn, with a gentle ritardando.

Run from anywhere: python tracks/12_the_light_we_keep.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, nearest_above, write_midi, print_report)

random.seed(12)
BPB = 4
ctx = Ctx(bpm=60, root='D', mode='aeolian', beats_per_bar=BPB)

# One palette: piano, cello, violin, viola, contrabass, strings I + II
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# ---------------------------------------------------------------------------
# Two grounds over the same descending lament bass.
#   MINOR ground  (track 1's passacaglia) — for the opening and the dark swell.
#   MAJOR ground  (the Picardy turn) — D major / mixture, for the radiant close.
# Each is 8 bars; bass descends a full octave (50 -> 38), the lament line.
# ---------------------------------------------------------------------------
GROUND_MIN = [
    (chord('D','F','A'),       50), (chord('C','E','G'),       48),
    (chord('Bb','D','F'),      46), (chord('A','C','E','G'),   45),
    (chord('G','Bb','D','F'),  43), (chord('F','A','C'),       41),
    (chord('E','G','Bb','D'),  40), (chord('A','C#','E'),      38),  # V7-ish dominant turn
]
# Major / mixture ground: D major home, borrowed colours, ending on a glowing Dadd9.
GROUND_MAJ = [
    (chord('D','F#','A'),      50), (chord('A','C#','E'),      45),  # I  - V
    (chord('Bb','D','F'),      46), (chord('F','A','C'),       41),  # bVI - bIII (mixture glow)
    (chord('G','B','D'),       43), (chord('D','F#','A'),      38),  # IV - I
    (chord('A','C#','E','G'),  40), (chord('D','F#','A','E'),  38),  # V7 - Dadd9 resolution
]

D4 = 62
# Track 1's memory theme (5-4-3 falling figure recapitulated), aeolian.
THEME = theme_from_degrees('aeolian', [
    (5,0,3),(6,3,1), (5,4,2),(4,6,2), (3,8,2),(4,10,1),(3,11,1), (2,12,2),(1,14,2),
    (6,16,2),(8,18,2), (10,20,2),(9,22,1),(8,23,1), (8,24,2),(6,26,2), (3,28,3),(1,31,1),
])
# Major-coloured theme for the radiant reprise (raised 3rd -> Picardy brightness).
THEME_MAJ = theme_from_degrees('ionian', [
    (5,0,3),(6,3,1), (5,4,2),(4,6,2), (3,8,2),(4,10,1),(3,11,1), (2,12,2),(1,14,2),
    (6,16,2),(8,18,2), (10,20,2),(9,22,1),(8,23,1), (8,24,2),(6,26,2), (3,28,3),(1,31,1),
])

# ---------------------------------------------------------------------------
# Form — one long breath, the longest on the album (~6:00 = 90 bars).
# 11 eight-bar cycles + a long coda. Minor -> dark swell -> Picardy -> dawn.
# (name, n_bars, lvl_start, lvl_end), key, theme-flag
# ---------------------------------------------------------------------------
# (section name, key 'min'/'maj')
PLAN = [
    ("intro",  'min'),   # 1  hush: pad + bass only, the ground alone
    ("recall", 'min'),   # 2  cello sings the memory motif (track-1 recap)
    ("gather", 'min'),   # 3  viola + piano join
    ("full",   'min'),   # 4  violin doubles, strings II under-pad
    ("dark",   'min'),   # 5  the darker swell — remembers the tragedy
    ("turn",   'maj'),   # 6  the Picardy turn begins (light breaks)
    ("rise",   'maj'),   # 7  building radiance, violin reprise in major
    ("climax", 'maj'),   # 8  radiant cathartic climax, full ensemble, D major
    ("glow",   'maj'),   # 9  the light held
    ("settle", 'maj'),   # 10 receding into warmth
    ("rest",   'maj'),   # 11 last quiet pass of the major ground
]
SECTIONS = [
    ("intro",  8, 0.05, 0.12),
    ("recall", 8, 0.14, 0.24),
    ("gather", 8, 0.26, 0.36),
    ("full",   8, 0.38, 0.50),
    ("dark",   8, 0.54, 0.66),   # the tragedy swell
    ("turn",   8, 0.52, 0.64),   # light breaks (relax then build)
    ("rise",   8, 0.66, 0.82),
    ("climax", 8, 0.88, 1.00),   # the one true climax
    ("glow",   8, 0.84, 0.66),
    ("settle", 8, 0.58, 0.38),
    ("rest",   8, 0.30, 0.12),
]
arc = Arc(SECTIONS, beats_per_bar=BPB)

ROLES = {
    "intro":  dict(pad=1,pad2=0,bass=1,cello=0,violin=0,viola=0,piano=0,eighths=0,arp=0,climax=0),
    "recall": dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,arp=0,climax=0),
    "gather": dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,arp=0,climax=0),
    "full":   dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=0,arp=0,climax=0),
    "dark":   dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,arp=0,climax=0),
    "turn":   dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,arp=1,climax=0),
    "rise":   dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,arp=1,climax=0),
    "climax": dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,arp=1,climax=1),
    "glow":   dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=0,arp=1,climax=0),
    "settle": dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,arp=0,climax=0),
    "rest":   dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,arp=0,climax=0),
}

cycles = [p[0] for p in PLAN]
keymap = {p[0]: p[1] for p in PLAN}
NB = len(cycles) * 8

def ground_for(cycle_name):
    return GROUND_MAJ if keymap[cycle_name] == 'maj' else GROUND_MIN

bar_chord, bar_bass = [], []
for nm in cycles:
    g = ground_for(nm)
    for i in range(8):
        bar_chord.append(g[i][0])
        bar_bass.append(g[i][1])

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * 8
    return out

pad_on, pad2_on, bass_on, viola_on = mask('pad'), mask('pad2'), mask('bass'), mask('viola')

# ---------------------------------------------------------------------------
# Sustained, voice-led pad bed across the whole piece (also feeds the piano).
# ---------------------------------------------------------------------------
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)], 4, (57, 81))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 28, 96)
expression(sc, CH_PAD, 0, NB * BPB, arc, 34)

# Warm under-pad (strings II): root an octave above bass + the chord's fifth.
def pad2_pitches(pcs, b):
    root = b + 12
    want = (root % 12 + 7) % 12
    fifth = min(pcs, key=lambda x: min((x - want) % 12, (want - x) % 12))
    return [root, nearest_above(fifth, root)]
for vi in range(2):
    tied_line(sc, CH_PAD2, 0,
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None for b in range(NB)],
              BPB, arc, 26, 80)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 30)

# Viola inner voice: the 3rd of each chord, tied (carries the minor->major turn).
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(55, 75) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0, [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 28, 78)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 32)

# Contrabass: the descending lament ground.
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)], BPB, arc, 34, 90, cc_floor=40)

# ---------------------------------------------------------------------------
# Per-cycle: piano, melody (cello/violin), arpeggio shimmer at the height of light.
# ---------------------------------------------------------------------------
for ci, nm in enumerate(cycles):
    t = ci * 8 * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci * 8:(ci + 1) * 8]
    is_maj = keymap[nm] == 'maj'

    if roles['piano']:
        piano_chords(sc, CH_PIANO, t, seg, [bar_bass[ci*8+i] + 12 for i in range(8)], BPB, arc,
                     eighths=bool(roles['eighths']))

    # Glass-style shimmer in the upper strings II register at the radiant peak.
    if roles['arp']:
        arp_voi = [[p + 12 for p in v] if v else None for v in seg]
        arpeggiate(sc, CH_PAD2, t, arp_voi, BPB, arc, rate=8, pattern='broken',
                   vlo=20, vhi=58, gate=0.9)

    if roles['cello']:
        th = THEME_MAJ if is_maj else THEME
        melody(sc, CH_CELLO, t, th, D4 - 12, arc, 46, 66)
    if roles['violin']:
        th = THEME_MAJ if is_maj else THEME
        oct_up = 12 if roles['climax'] else 0
        melody(sc, CH_VIOLIN, t, th, D4 + oct_up, arc, 58, 112)

# ---------------------------------------------------------------------------
# Coda — a long luminous D major (glowing Dadd9), fading like dawn, with a
# gentle ritardando. The ONLY true major resolution on the album.
# ---------------------------------------------------------------------------
t = NB * BPB
CODA_LEN = 16.0
# Ritardando over the close: ease the pulse down as the light settles.
sc.tempo(t, 60)
sc.tempo(t + 6, 52)
sc.tempo(t + 11, 44)

# Glowing Dadd9 (D F# A E) across the strings, warm and full.
final_pcs = chord('D', 'F#', 'A', 'E')
pv = voice_chord(final_pcs, pad_voi[-1], 4, 57, 83)
for p in pv:
    sc.note(CH_PAD, p, t, CODA_LEN, 52, max_jit=6)
# Under-pad: low D + A open fifth, the bedrock of home.
sc.note(CH_PAD2, 50, t, CODA_LEN, 44, max_jit=6)
sc.note(CH_PAD2, 57, t, CODA_LEN, 40, max_jit=6)
# Deep bass D — the journey home.
sc.note(CH_BASS, 38, t, CODA_LEN, 40, max_jit=6)
# Cello on the major 3rd (F#) — the Picardy colour sung low and warm.
sc.note(CH_CELLO, 54, t + 0.5, CODA_LEN - 1.0, 38, max_jit=6)
# Viola fills the fifth (A).
sc.note(CH_VIOLA, 57, t + 0.5, CODA_LEN - 1.0, 34, max_jit=6)
# Violin: a high luminous E (the add9 glimmer) then a settling F# — dawn light.
sc.note(CH_VIOLIN, 81, t + 1.0, 7.0, 36, max_jit=6)   # high E
sc.note(CH_VIOLIN, 78, t + 8.0, CODA_LEN - 8.0, 30, max_jit=6)  # settles to F#
# Piano: a final spread Dadd9 arpeggio, pedal blurred.
sc.cc(CH_PIANO, 64, 0, t - 0.02)
sc.cc(CH_PIANO, 64, 127, t)
for k, p in enumerate([38, 50, 54, 57, 62, 66]):  # D D F# A D F#
    sc.note(CH_PIANO, p, t + k * 0.5, CODA_LEN - k * 0.5, 40 + k, max_jit=8)
sc.cc(CH_PIANO, 64, 0, t + CODA_LEN - 0.2)

fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO, CH_VIOLA, CH_VIOLIN, CH_PIANO],
         t, CODA_LEN, beats=14, top=70)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '12 - The Light We Keep.mid')
write_midi(sc, OUT, title='The Light We Keep', text='Vigil / 12', key='Dm')
print_report(OUT, allowed_pcs=["D","E","F","F#","G","A","Bb","B","C","C#"])
