"""
04 - Undertow   (C aeolian, 56 bpm)  — grief's gravity, a slow downward pull.

The DARKEST, lowest track of *Vigil*. A heavy 4-bar ground descends C - Bb - Ab - G
(i - bVII - bVI - v) under a low, brooding cello theme built on the memory motif
(G - F - Eb in Cm). Everything sits low: contrabass + cello prominent, a dark/low
string pad, low broken piano. The swell strains upward — one strained high violin
note at the climax — but the undertow pulls it back down to a low, unresolved Cm.

Run from anywhere: python tracks/04_undertow.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(4)
BPB = 4
ctx = Ctx(bpm=56, root='C', mode='aeolian', beats_per_bar=BPB)

# Channels (GM): piano, cello, violin, viola, contrabass, strings I + II
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# The 4-bar ground: descending bass C - Bb - Ab - G, chords i - bVII - bVI - v(Gsus->Gm).
# Gm is the minor v (D-F natural? no: Gm = G-Bb-D) — all diatonic to C aeolian.
GROUND = [
    (chord('C','Eb','G'),  36),   # Cm   over C2
    (chord('Bb','D','F'),  34),   # Bb   over Bb1
    (chord('Ab','C','Eb'), 32),   # Ab   over Ab1
    (chord('G','Bb','D'),  31),   # Gm   over G1
]
GROUND_LEN = len(GROUND)

# Cello theme — low and heavy, built on the memory motif G-F-Eb (5-4-3 in Cm).
# base = C3 (48); offsets are semitone-from-base from theme_from_degrees.
# Degrees: 5=G,4=F,3=Eb,2=D,1=C,7=Bb(below),6=Ab.
C3 = 48
THEME = theme_from_degrees('aeolian', [
    (5,0,3),(4,3,1),                 # G ... F  (the sigh begins)
    (3,4,3),(2,7,1),                 # Eb ... D
    (1,8,4),                         # C  (settle, bar 3)
    (-1,12,2),(-2,14,2),             # Bb below ... Ab below — the pull downward
])

# Form: dark low intro, theme enters, a slow swell that strains up then is pulled back,
# sink to a low unresolved close. 14 cycles x 4 bars = 56 bars ~= 4:00 at bar=4.286s.
# (name, n_bars, lvl_start, lvl_end)  — levels kept LOW; this track broods.
# Totals to 56 bars (14 four-bar cycles) -> ~4:00 at bar=4.286s.
SECTIONS = [
    ("intro",   8, 0.04, 0.14),
    ("A",       8, 0.16, 0.26),     # cello theme enters, low
    ("A'",      8, 0.26, 0.40),     # piano + viola thicken
    ("rise",    8, 0.42, 0.62),     # the strain upward begins
    ("climax",  8, 0.66, 0.84),     # one strained high violin note
    ("pull",    8, 0.60, 0.34),     # the undertow drags it back down
    ("coda",    8, 0.20, 0.03),     # descent + sink to a low, unresolved Cm
]
arc = Arc(SECTIONS, beats_per_bar=BPB)

ROLES = {
    "intro":  dict(pad=1,pad2=1,bass=1,cello=0,viola=0,violin=0,piano=0,eighths=0,climax=0),
    "A":      dict(pad=1,pad2=1,bass=1,cello=1,viola=0,violin=0,piano=0,eighths=0,climax=0),
    "A'":     dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,eighths=0,climax=0),
    "rise":   dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,eighths=0,climax=0),
    "climax": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,eighths=0,climax=1),
    "pull":   dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,eighths=0,climax=0),
    "descent":dict(pad=1,pad2=1,bass=1,cello=1,viola=0,violin=0,piano=0,eighths=0,climax=0),
    "coda":   dict(pad=1,pad2=0,bass=1,cello=0,viola=0,violin=0,piano=0,eighths=0,climax=0),
}

# Expand into 4-bar cycles
cycles = []
for (name, nb, _a, _b) in SECTIONS:
    for _ in range(nb // GROUND_LEN):
        cycles.append(name)
NB = len(cycles) * GROUND_LEN
bar_chord = [GROUND[b % GROUND_LEN][0] for b in range(NB)]
bar_bass  = [GROUND[b % GROUND_LEN][1] for b in range(NB)]

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * GROUND_LEN
    return out

pad_on, pad2_on, bass_on, viola_on = mask('pad'), mask('pad2'), mask('bass'), mask('viola')

# --- Dark, LOW string pad (band lower than track 01: 48-72) --------------------
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)],
                         4, (48, 72))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 26, 80)
expression(sc, CH_PAD, 0, NB * BPB, arc, 30)

# --- Warm low under-pad (Strings II): root + chord fifth, in the cello/viola register
def pad2_pitches(pcs, root_bass):
    root = root_bass + 12          # an octave above the contrabass
    want = (root % 12 + 7) % 12    # the fifth above the root
    fifth = min(pcs, key=lambda x: min((x - want) % 12, (want - x) % 12))
    f = root
    while f % 12 != fifth % 12:
        f += 1
    return [root, f]
for vi in range(2):
    tied_line(sc, CH_PAD2, 0,
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None
               for b in range(NB)],
              BPB, arc, 24, 70)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 28)

# --- Viola inner voice: the 3rd of each chord, tied, dark mid-low register ------
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(50, 67) if q % 12 == third % 12), 55)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 26, 66)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 30)

# --- Contrabass: the descending lament ground, sustained & heavy ----------------
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)],
     BPB, arc, 30, 80, cc_floor=36)

# --- Cello theme + low piano, per cycle -----------------------------------------
for ci, nm in enumerate(cycles):
    t = ci * GROUND_LEN * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci*GROUND_LEN:(ci+1)*GROUND_LEN]
    if roles['piano']:
        # LOW broken piano: roots an octave above contrabass (still low: ~C3 area)
        piano_chords(sc, CH_PIANO, t, seg,
                     [bar_bass[ci*GROUND_LEN+i] + 12 for i in range(GROUND_LEN)],
                     BPB, arc, eighths=bool(roles['eighths']), vlo=22, vhi=58)
    if roles['cello']:
        # Cello carries the memory motif, low and heavy (base C3)
        melody(sc, CH_CELLO, t, THEME, C3, arc, 40, 70)

# --- The one strained high violin note at the climax ----------------------------
# A single high G5 (the 5th, top of the G-F-Eb motif) that strains upward then
# is pulled back: it sighs G5 -> F5 -> Eb5 over the climax cycle, never resolving up.
climax_ci = next(i for i, nm in enumerate(cycles) if nm == 'climax')
ct = climax_ci * GROUND_LEN * BPB
G5 = ctx.deg(5, 72)            # degree 5 (G) with tonic at C5(72) => MIDI 79 = true G5
sc.note(CH_VIOLIN, G5, ct + 1.0, 5.0, 78, max_jit=8)      # G5 strains up
sc.note(CH_VIOLIN, G5 - 2, ct + 7.0, 4.0, 70, max_jit=8)  # F5  (the sigh down)
sc.note(CH_VIOLIN, G5 - 4, ct + 12.0, 3.0, 60, max_jit=8) # Eb5 — pulled back down
expression(sc, CH_VIOLIN, ct, ct + GROUND_LEN * BPB, arc, 30)

# --- Coda: sink to a low, UNRESOLVED Cm (an added 9th D lingering, no third on top)
t = NB * BPB
# A low, hollow Cm voicing in the pad's dark band
pv = voice_chord(chord('C','Eb','G'), pad_voi[-1], 4, 48, 72)
for p in pv:
    sc.note(CH_PAD, p, t, 12.0, 34, max_jit=6)
sc.note(CH_BASS, 36, t, 12.0, 32, max_jit=6)         # low C2 anchor
sc.note(CH_CELLO, 48, t, 12.0, 30, max_jit=6)        # C3
sc.note(CH_PAD2, 50, t + 1.5, 10.0, 26, max_jit=6)   # D — the unresolved 9th, low
fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO], t, 12.0)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '04 - Undertow.mid')
write_midi(sc, OUT, title='Undertow', text='Vigil / 4', key='Cm')
print_report(OUT, allowed_pcs=['C','D','Eb','F','G','Ab','Bb'])
