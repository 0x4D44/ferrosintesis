"""
08 - The Weight of Water   (Bb aeolian, 58 bpm)  — the longest tragic build.

Glass-style ADDITIVE accumulation over an epic minor ground: Bbm - Gb - Db - Ab
(i - VI - III - VII), a 4-bar loop that repeats and accumulates. Each pass adds a
layer — under-pad, viola, violin, octave doublings, rolling piano eighths — so the
intensity climbs relentlessly, near-linearly, to the album's LOUDEST peak (~0.98)
about 72% in. Then a sudden break, and a long exhausted recession to near-silence
(~0.05): being pulled under, the weight of water closing over.

The memory motif (5-4-3 = F-Eb-Db in Bb minor), the downward "sigh" suspension, and
a stepwise descending lament bass are all present.

Run from anywhere: python 08_the_weight_of_water.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, nearest_above, write_midi, print_report)

random.seed(8)
BPB = 4
ctx = Ctx(bpm=58, root='Bb', mode='aeolian', beats_per_bar=BPB)

# Palette: piano, cello, violin, viola, contrabass, strings I + II (under-pad)
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# The epic minor ground, 4 bars: i - VI - III - VII, with a stepwise descending
# lament bass (Bb -> Gb -> F -> Eb, all falling).
GROUND = [
    (chord('Bb','Db','F'),       34),   # i    Bbm   (Bb1)
    (chord('Gb','Bb','Db'),      30),   # VI   Gb    (Gb1) -> Gb2 below floor; bass set per-bar
    (chord('Db','F','Ab'),       37),   # III  Db    (Db2)
    (chord('Ab','C','Eb'),       32),   # VII  Ab... wait C not in scale
]
# NOTE: Ab major triad spells Ab-C-Eb but C-natural is outside Bb aeolian.
# In Bb minor the VII is the Ab MAJOR triad only with a raised 3rd; to stay strictly
# diatonic we use Ab-Cb(=B? no)...  The diatonic chord on Ab is Ab-Cb-Eb? Ab's third
# diatonically is Cb (=B), not in scale either. Use the diatonic bVII = Ab major built
# from the natural-minor: the bVII triad in aeolian is Ab-C-Eb? In Bb aeolian the
# pitches are Bb C Db Eb F Gb Ab. The triad on Ab is Ab-Cb(B)-Eb -> not diatonic.
# The genuine diatonic VII chord here is Ab-C? C is degree 2 (C natural IS in Bb
# aeolian: Bb C Db Eb F Gb Ab). So Ab-C-Eb uses Ab(d7) C(d2) Eb(d4) -> all diatonic.
# Good: Ab major triad IS diatonic in Bb aeolian. Keep it.

# Bass: stepwise descending lament line across the 4-bar cell (Bb-Ab-Gb-F feel),
# kept in contrabass register.
BASS_LINE = [46, 44, 42, 41]   # Bb2, Ab2, Gb2, F2 — a falling tetrachord (lament)

# The memory motif lives in the theme: 5-4-3 = F-Eb-Db, with downward sighs.
# Theme spans the 4-bar (16-beat) cell. Degrees relative to Bb.
THEME = theme_from_degrees('aeolian', [
    (5,0,3),(4,3,1),          # F.. -> Eb  (the sigh)
    (3,4,3),(2,7,1),          # Db.. -> C
    (1,8,2),(7,10,2),         # Bb -> Ab (down a step, the ground turning)
    (5,12,2),(4,14,1),(3,15,1)  # F -> Eb -> Db : the 5-4-3 memory motif at the close
])

# A higher, more anguished counter-theme for the climax (violin soaring).
THEME_HI = theme_from_degrees('aeolian', [
    (8,0,4),(7,4,2),(6,6,2),  # Bb(oct) -> Ab -> Gb : long descent
    (5,8,4),(4,12,2),(3,14,2) # F -> Eb -> Db : the motif, sustained at the top
])

# ---------------------------------------------------------------------------
# FORM — additive accumulation. 20 cycles of the 4-bar ground = 80 bars.
# One near-linear climb to the album's loudest peak ~72% in, then collapse.
# (name, n_bars, lvl_start, lvl_end)
SECTIONS = [
    ("c01", 4, 0.05, 0.09),   # bare cell: piano + cello, near silence
    ("c02", 4, 0.10, 0.15),
    ("c03", 4, 0.16, 0.21),   # + low pad
    ("c04", 4, 0.22, 0.27),
    ("c05", 4, 0.28, 0.33),   # + under-pad, viola
    ("c06", 4, 0.34, 0.39),
    ("c07", 4, 0.40, 0.45),   # + violin
    ("c08", 4, 0.46, 0.51),
    ("c09", 4, 0.52, 0.57),   # + piano broken
    ("c10", 4, 0.58, 0.63),
    ("c11", 4, 0.64, 0.70),   # + octave doublings, rolling
    ("c12", 4, 0.71, 0.77),
    ("c13", 4, 0.78, 0.85),   # full ensemble surging
    ("c14", 4, 0.86, 0.93),
    ("c15", 4, 0.95, 0.98),   # THE PEAK — loudest on the album
    ("brk", 4, 0.30, 0.22),   # sudden break: the wave crests and drops away
    ("r01", 4, 0.20, 0.15),   # long exhausted recession
    ("r02", 4, 0.14, 0.10),
    ("r03", 4, 0.09, 0.06),
    ("r04", 4, 0.05, 0.03),   # near-silence: pulled under
]
arc = Arc(SECTIONS, beats_per_bar=BPB)

# Per-cycle layer roster — layers switch ON and never off until the break (additive).
# Each entry: which voices sound this cycle + texture flags.
ROLES = {
    "c01": dict(pad=0,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "c02": dict(pad=0,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "c03": dict(pad=1,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "c04": dict(pad=1,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "c05": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,broken=1,oct=0,eighths=0),
    "c06": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,broken=1,oct=0,eighths=0),
    "c07": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=0,eighths=0),
    "c08": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=0,eighths=0),
    "c09": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=0,eighths=1),
    "c10": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=0,eighths=1),
    "c11": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=1,eighths=1),
    "c12": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=1,eighths=1),
    "c13": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=1,eighths=1),
    "c14": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=1,eighths=1),
    "c15": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=1,piano=1,broken=1,oct=1,eighths=1),
    "brk": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "r01": dict(pad=1,pad2=1,bass=1,cello=1,viola=1,violin=0,piano=0,broken=0,oct=0,eighths=0),
    "r02": dict(pad=1,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=0,broken=0,oct=0,eighths=0),
    "r03": dict(pad=1,pad2=0,bass=1,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
    "r04": dict(pad=1,pad2=0,bass=0,cello=1,viola=0,violin=0,piano=1,broken=0,oct=0,eighths=0),
}

cycles = [s[0] for s in SECTIONS]   # one 4-bar pass each
NB = len(cycles) * 4
bar_chord = [GROUND[b % 4][0] for b in range(NB)]
bar_bass  = [BASS_LINE[b % 4]  for b in range(NB)]

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * 4
    return out

pad_on, pad2_on, bass_on, viola_on = mask('pad'), mask('pad2'), mask('bass'), mask('viola')

# ---------------------------------------------------------------------------
# Strings I — the main voice-led pad, tied across the whole piece.
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)],
                         4, (54, 79))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 26, 92)
expression(sc, CH_PAD, 0, NB * BPB, arc, 30)

# Strings II — warm under-pad: root an octave up + the chord fifth.
def pad2_pitches(pcs, broot):
    # Double the CHORD ROOT (pcs[0]) + its fifth, NOT the bass note: the lament bass
    # is an inversion line (bass != root on most bars), and doubling that non-chord
    # tone up an octave clashes a semitone with the chord 3rd in the violas.
    root_pc = pcs[0] % 12
    r0 = broot + 12
    up = r0
    while up % 12 != root_pc:
        up += 1
    dn = r0
    while dn % 12 != root_pc:
        dn -= 1
    root = up if (up - r0) <= (r0 - dn) else dn
    want = (root % 12 + 7) % 12
    fifth = min(pcs, key=lambda x: min((x - want) % 12, (want - x) % 12))
    return [root, nearest_above(fifth, root)]
for vi in range(2):
    tied_line(sc, CH_PAD2, 0,
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None
               for b in range(NB)],
              BPB, arc, 24, 76)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 28)

# Viola — inner sigh voice: the 3rd of each chord, tied.
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(50, 74) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 26, 78)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 30)

# Contrabass — the descending lament ground.
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)],
     BPB, arc, 30, 90, cc_floor=36)

# ---------------------------------------------------------------------------
# Per-cycle: piano + cello/violin melody, with the accumulating textures.
BbT_CELLO = 46    # Bb2 — cello tonic for the low theme
BbT_VIOL  = 58    # Bb3 — violin tonic for the high theme
for ci, nm in enumerate(cycles):
    t = ci * 4 * BPB
    R = ROLES[nm]
    seg = pad_voi[ci * 4:(ci + 1) * 4]

    if R['piano']:
        proots = [bar_bass[ci*4+i] + 24 for i in range(4)]   # piano LH up two octaves
        piano_chords(sc, CH_PIANO, t, seg, proots, BPB, arc,
                     eighths=bool(R['eighths']), vlo=24, vhi=70)

    if R['cello']:
        # at the peak the cello rises an octave to sing the motif with the violins,
        # adding brightness/weight without leaving its idiomatic range.
        base = BbT_CELLO + (12 if R['oct'] else 0)
        melody(sc, CH_CELLO, t, THEME, base, arc, 44, 80)

    if R['violin']:
        th = THEME_HI if (R['oct']) else THEME
        base = BbT_VIOL + (12 if R['oct'] else 0)
        melody(sc, CH_VIOLIN, t, th, base, arc, 56, 112)

# ---------------------------------------------------------------------------
# Coda — the water closes over: a hollow Bbm (root + fifth + a fading high Db,
# the b3, the unhealed wound), dissolving to silence.
t = NB * BPB
pv = voice_chord(chord('Bb','Db','F'), pad_voi[-1], 4, 54, 79)
for p in pv:
    sc.note(CH_PAD, p, t, 12.0, 30, max_jit=6)
sc.note(CH_BASS, 46, t, 12.0, 30, max_jit=6)        # Bb2
sc.note(CH_CELLO, 46, t, 12.0, 28, max_jit=6)       # Bb2
sc.note(CH_VIOLA, ctx.deg(3, 46), t + 1.5, 10.0, 26, max_jit=6)  # Db, the b3 sigh (Bb2 base)
fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO, CH_VIOLA], t, 12.0)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '08 - The Weight of Water.mid')
write_midi(sc, OUT, title='The Weight of Water', text='Vigil / 8', key='Bbm')
print_report(OUT, allowed_pcs=["Bb","C","Db","Eb","F","Gb","Ab"])
