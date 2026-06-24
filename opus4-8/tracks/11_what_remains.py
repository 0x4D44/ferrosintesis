"""
11 - What Remains   (F major, 64 bpm)  — the healing track.

After the elegy: tender, consoling, the wound beginning to close. A gentle consoling
piano under a simple warm cello melody (touched by violin at the swell) that keeps
finding CONSONANT resolutions — suspensions that resolve DOWNWARD into rest rather than
aching unresolved. Plagal (IV-I) warmth throughout. One soft hopeful mid-swell, then a
settling to a warm Fadd9 that feels like peace.

The album's falling memory motif (5-4-3) surfaces here recoloured into major and
RESOLVED — C-Bb-A over an F that finally consoles instead of grieving.

Run from anywhere: python 11_what_remains.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, nearest_above, write_midi, print_report)

random.seed(11)
BPB = 4
ctx = Ctx(bpm=64, root='F', mode='ionian', beats_per_bar=BPB)

# Palette: piano, cello (warm lead), violin (touches the swell), viola (inner warmth),
# contrabass (soft floor), strings I (warm pad). A consistent subset.
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD = range(6)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'), CH_PAD:(48,'Strings I'),
}.items():
    sc.program(ch, prog, nm)

# --------------------------------------------------------------------------------------
# Harmony: a warm consoling progression, plagal-leaning. 8-bar cycle, repeated.
#   F  -  C/E  -  Dm7  -  Bb(add9)  -  Gm7  -  C  -  F  -  Bb/F .. F   (plagal cadence)
# Bass is a gently DESCENDING line (lament bass, but now warm): F E D Bb, G C F F.
# Each chord pcs + contrabass root pitch.
CYCLE = [
    (chord('F','A','C'),        41),   # I        F2
    (chord('C','E','G'),        40),   # V6 (C/E) E2
    (chord('D','F','A','C'),    38),   # vi7 Dm7  D2
    (chord('Bb','D','F','G'),   34),   # IV add9  Bb1
    (chord('G','Bb','D','F'),   43),   # ii7 Gm7  G2
    (chord('C','E','G'),        36),   # V   C2
    (chord('F','A','C'),        41),   # I        F2
    (chord('Bb','D','F'),       41),   # IV/F (plagal) over F pedal -> resolves to I next
]
NB_PER_CYCLE = 8
N_CYCLES = 8                  # 8 * 8 = 64 bars
NB = NB_PER_CYCLE * N_CYCLES

bar_chord = [CYCLE[b % NB_PER_CYCLE][0] for b in range(NB)]
bar_bass  = [CYCLE[b % NB_PER_CYCLE][1] for b in range(NB)]

# --------------------------------------------------------------------------------------
# The tender melody. Major, singing, full of suspensions that RESOLVE downward.
# Degrees over the 8-bar cycle (a 32-beat phrase). The memory motif 5-4-3 (C-Bb-A)
# appears resolved at bars 3-4, and the phrase settles each time onto a consonance.
# (degree, start_beat, dur_beats)
THEME = theme_from_degrees('ionian', [
    # bar1: rise gently to the 3rd and rest
    (1, 0, 2), (3, 2, 2),
    # bar2: the sigh — 5 leaning to 4, resolving onto 3 (a resolved suspension)
    (5, 4, 2), (4, 6, 1), (3, 7, 1),
    # bar3-4: the memory motif, recoloured & resolved: 5-4-3 then down to 1
    (5, 8, 2), (4, 10, 2),
    (3, 12, 2), (1, 14, 2),
    # bar5-6: lift toward hope — up to 6, sigh back through 5 to the warm 3
    (5, 16, 2), (6, 18, 2),
    (5, 20, 1), (4, 21, 1), (3, 22, 2),
    # bar7-8: console home — gentle 2-1 suspension resolving, settle on the tonic
    (2, 24, 2), (1, 26, 2),
    (3, 28, 1.5), (2, 29.5, 0.5), (1, 30, 2),
])

# A small violin counter-glow at the swell: high, sparse, the same resolved sighs an
# octave up but rhythmically sparse so it consoles rather than competes.
VIOLIN_THEME = theme_from_degrees('ionian', [
    (8, 8, 4),                       # high F held
    (10, 16, 2), (9, 18, 2),         # 6 sighing to 5
    (8, 20, 4),                      # back to F, held — warmth, not climax
])

# --------------------------------------------------------------------------------------
# Form: ONE long breath. Enter near-silence, a single soft hopeful mid-swell (this track
# never roars — lower dynamic ceiling than the tragic tracks), then settle to peace.
# (name, n_bars, lvl_start, lvl_end)   levels 0..1
SECTIONS = [
    ("intro",  8, 0.05, 0.16),   # piano + pad alone, near silence
    ("A",      8, 0.18, 0.30),   # cello takes the melody, warm
    ("A'",     8, 0.30, 0.44),   # viola joins, piano broadens
    ("swell",  8, 0.50, 0.66),   # the hopeful mid-swell — violin glow enters (one climax)
    ("B",      8, 0.60, 0.50),   # recede a touch, console
    ("B'",     8, 0.44, 0.34),   # cello sings home, softer
    ("settle", 8, 0.26, 0.16),   # thinning, warm
    ("coda",   8, 0.14, 0.05),   # almost gone, leads to the Fadd9 tail
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.045)

# Per-section roles (keep it gentle and warm throughout)
ROLES = {
    "intro":  dict(pad=1, bass=1, cello=0, violin=0, viola=0, piano=1, eighths=0),
    "A":      dict(pad=1, bass=1, cello=1, violin=0, viola=0, piano=1, eighths=0),
    "A'":     dict(pad=1, bass=1, cello=1, violin=0, viola=1, piano=1, eighths=1),
    "swell":  dict(pad=1, bass=1, cello=1, violin=1, viola=1, piano=1, eighths=1),
    "B":      dict(pad=1, bass=1, cello=1, violin=1, viola=1, piano=1, eighths=1),
    "B'":     dict(pad=1, bass=1, cello=1, violin=0, viola=1, piano=1, eighths=0),
    "settle": dict(pad=1, bass=1, cello=1, violin=0, viola=0, piano=1, eighths=0),
    "coda":   dict(pad=1, bass=1, cello=0, violin=0, viola=0, piano=1, eighths=0),
}
cycles = [s[0] for s in SECTIONS]   # one section == one 8-bar cycle here

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * NB_PER_CYCLE
    return out

pad_on, bass_on, viola_on = mask('pad'), mask('bass'), mask('viola')

# --------------------------------------------------------------------------------------
# Warm string pad across the whole piece (voice-led, tied, breathing). Mid register.
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)],
                         4, (57, 80))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 26, 78)
expression(sc, CH_PAD, 0, NB * BPB, arc, 32)

# Viola inner warmth: the 3rd of each chord, tied, in viola register.
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(52, 72) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 24, 64)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 30)

# Soft contrabass floor: the gently descending warm bass, sustained.
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)],
     BPB, arc, 28, 70, cc_floor=36)

# --------------------------------------------------------------------------------------
# Per-cycle: consoling piano + cello melody + occasional violin glow.
F4 = 65   # tonic F4 = melody base for cello placement
for ci, nm in enumerate(cycles):
    t = ci * NB_PER_CYCLE * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci*NB_PER_CYCLE:(ci+1)*NB_PER_CYCLE]
    seg_bass = [bar_bass[ci*NB_PER_CYCLE+i] for i in range(NB_PER_CYCLE)]
    if roles['piano']:
        # gentle broken piano, root an octave up for warmth in the left hand
        piano_chords(sc, CH_PIANO, t, seg, [b + 12 for b in seg_bass], BPB, arc,
                     eighths=bool(roles['eighths']), vlo=24, vhi=58)
    if roles['cello']:
        # cello in its warm mid register (F3 = 53 as the tonic anchor -> sings up to ~D5)
        melody(sc, CH_CELLO, t, THEME, 53, arc, 44, 78, gate=0.98)
    if roles['violin']:
        # sparse high glow — the hopeful colour, never harsh
        melody(sc, CH_VIOLIN, t, VIOLIN_THEME, 65, arc, 40, 84, gate=0.99)

# --------------------------------------------------------------------------------------
# Coda: the warm Fadd9 that feels like peace. F-A-C plus the gentle 9th (G) above,
# resolved and at rest. A long fade to near silence.
t = NB * BPB
peace = voice_chord(chord('F','A','C'), pad_voi[-1], 4, 57, 80)
for p in peace:
    sc.note(CH_PAD, p, t + 0.25, 11.75, 38, max_jit=4)
sc.note(CH_VIOLA, 57, t, 12.0, 34, max_jit=6)            # A3 inner
sc.note(CH_BASS, 41, t, 12.0, 34, max_jit=6)             # F2 floor
sc.note(CH_CELLO, 53, t + 0.5, 11.5, 36, max_jit=6)      # F3 warm tonic
# the add9 colour: a soft G above, the 9th — consonant, hopeful, at peace
sc.note(CH_VIOLIN, 79, t + 1.5, 10.0, 30, max_jit=6)     # G5 glimmer (add9)
# piano: one last gentle Fadd9 spread
sc.cc(CH_PIANO, 64, 127, t)
for k, p in enumerate([41, 57, 60, 65, 67]):             # F2 A3 C4 F4 G4
    sc.note(CH_PIANO, p, t + 0.10 * k, 11.0, 30, max_jit=4)
sc.cc(CH_PIANO, 64, 0, t + 12.0)

fade_out(sc, [CH_PAD, CH_VIOLA, CH_BASS, CH_CELLO, CH_VIOLIN], t, 12.0, top=64)

# --------------------------------------------------------------------------------------
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '11 - What Remains.mid')
write_midi(sc, OUT, title='What Remains', text='Vigil / 11', key='F')
print_report(OUT, allowed_pcs=['F','G','A','Bb','C','D','E'])
