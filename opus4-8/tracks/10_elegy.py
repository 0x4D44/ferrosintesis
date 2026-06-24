"""
10 - Elegy   (D minor, 52 bpm — the slowest, heaviest track) — the album's tragic nadir.

The MEMORY MOTIF of track 1 (falling 5-4-3, A-G-F in Dm) returns in full grief: stated
by the cello low and dark, answered an octave up by the violin, developed and darkened
over the lament bass D-C-Bb-A-G-F-E-D (slower and heavier than track 1). Full sustained
strings dominate; piano is sparse, low and tolling. One immense slow climax of overwhelming
sorrow — approached through an A MAJOR chord (a SINGLE C#, the only chromatic note in the
album's diatonic Dm, one stab of pain) resolving to Dm — then a long hollow decay.

Reference: Barber "Adagio for Strings"; Richter at his most desolate.

Run from anywhere: python tracks/10_elegy.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(10)
BPB = 4
ctx = Ctx(bpm=52, root='D', mode='aeolian', beats_per_bar=BPB)

# Channels (GM): piano, cello, violin, viola, contrabass, strings I + II under-pad
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# The lament ground (8 bars): per-bar (chord pcs, contrabass pitch).
# Bass descends D-C-Bb-A-G-F-E-D over an octave; harmony
# Dm - Bb - F - C - Gm - Dm/F - Em7b5 - A(sus)/Dm.
GROUND = [
    (chord('D','F','A'),        50),  # Dm        D
    (chord('Bb','D','F'),       48),  # Bb        C (bass under Bb -> Bb/C, lament step)
    (chord('F','A','C'),        46),  # F         Bb
    (chord('C','E','G'),        45),  # C         A
    (chord('G','Bb','D'),       43),  # Gm        G
    (chord('D','F','A'),        41),  # Dm/F      F
    (chord('E','G','Bb','D'),   40),  # Em7b5     E
    (chord('A','C','E','G'),    38),  # Asus/Am7  D (low) — resolves to Dm at top of next cycle
]
# The memory motif: falling 5-4-3 in D aeolian (A-G-F), grief-laden, slow.
# A two-bar phrase per 8-beat span; developed/extended in later forms.
D4 = 62
# Core motif (degrees 5-4-3 then sinking to the tonic), spread across the slow bars.
MOTIF = theme_from_degrees('aeolian', [
    (5, 0, 3), (4, 4, 2), (3, 6, 2),          # A . . | G . F .  (the falling sigh)
    (5, 8, 2), (4, 10, 2), (3, 12, 2), (2, 14, 2),  # A G F E (darkened extension)
])
# A longer grief statement for the climax cycles: the motif reaching higher then collapsing.
MOTIF_HI = theme_from_degrees('aeolian', [
    (5, 0, 4), (4, 4, 2), (3, 6, 2),
    (8, 8, 4), (7, 12, 2), (5, 14, 2),        # leap to high D, sink back: the overwhelming swell
])

# Form: one long, weighty swell to a single immense climax past the golden section,
# then a long hollow decay. (name, n_bars, lvl_start, lvl_end), levels 0..1.
SECTIONS = [
    ("intro",   8, 0.04, 0.14),
    ("A",       8, 0.16, 0.28),
    ("A'",      8, 0.28, 0.42),
    ("B",       8, 0.44, 0.58),
    ("climax",  8, 0.66, 0.97),   # the immense sorrow, with the C# stab into it
    ("descent", 8, 0.66, 0.40),
    ("hollow",  8, 0.34, 0.16),
    ("coda",    8, 0.14, 0.03),
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.045)

# Per-section instrumentation (texture grows then thins).
ROLES = {
    "intro":   dict(pad=1,pad2=0,bass=1,cello=0,violin=0,viola=0,piano=0,motif='lo',hi=0,cs=0),
    "A":       dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=1,piano=0,motif='lo',hi=0,cs=0),
    "A'":      dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,motif='lo',hi=0,cs=0),
    "B":       dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,motif='lo',hi=0,cs=0),
    "climax":  dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,motif='hi',hi=1,cs=1),
    "descent": dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,motif='lo',hi=0,cs=0),
    "hollow":  dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,motif='lo',hi=0,cs=0),
    "coda":    dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,motif='lo',hi=0,cs=0),
}

# Expand into cycles (one cycle = one 8-bar pass of the ground).
cycles = []
for (name, nb, _a, _b) in SECTIONS:
    for _ in range(nb // 8):
        cycles.append(name)
NB = len(cycles) * 8
bar_chord = [GROUND[b % 8][0] for b in range(NB)]
bar_bass  = [GROUND[b % 8][1] for b in range(NB)]

# Locate the climax cycle so we can inject the single C# (A major) at its final approach.
climax_ci = cycles.index("climax")

# In the climax cycle, darken the penultimate chord to A MAJOR (C#) — the one chromatic
# stab of pain — resolving to Dm at the top of the descent cycle. Bar index 7 of the
# climax cycle (the Em7b5 slot becomes the dominant approach: A major).
CS_BAR = climax_ci * 8 + 7
bar_chord[CS_BAR] = chord('A', 'C#', 'E')   # A major — the declared single C#
bar_bass[CS_BAR]  = 45                        # A in the bass under the dominant

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * 8
    return out

pad_on, pad2_on, bass_on, viola_on = mask('pad'), mask('pad2'), mask('bass'), mask('viola')

# --- Sustained, voice-led pad across the whole piece (the thick string bed) ---
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)], 4, (55, 84))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 26, 86, legato=0.4)
expression(sc, CH_PAD, 0, NB * BPB, arc, 30)

# --- Warm lower under-pad (Strings II): root an octave above the bass + the fifth ---
from engine import nearest_above
def pad2_pitches(pcs, b):
    # Double the CHORD ROOT (pcs[0]) + its fifth, NOT the inversion bass note —
    # else the non-chord-tone bass, doubled an octave up, clashes a semitone with
    # the viola's chord 3rd (e.g. F-chord over a Bb bass -> Bb vs the viola's A).
    root_pc = pcs[0] % 12
    r0 = b + 12
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
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None for b in range(NB)],
              BPB, arc, 22, 70, legato=0.4)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 28)

# --- Viola inner voice: the chord 3rd, tied (warm middle) ---
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(52, 74) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0, [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 24, 68, legato=0.4)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 30)

# --- Contrabass: the slow, heavy descending lament ground ---
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)], BPB, arc, 30, 84,
     legato=0.4, cc_floor=38)

# --- Memory motif (cello low / violin high) + sparse tolling piano, per cycle ---
for ci, nm in enumerate(cycles):
    t = ci * 8 * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci * 8:(ci + 1) * 8]
    theme = MOTIF_HI if roles['motif'] == 'hi' else MOTIF
    if roles['piano']:
        # Sparse, low, TOLLING: a bare bass note + its fifth on the downbeat of each
        # half-cycle, under sustain pedal (a slow funeral bell).
        for half in (0, 4):
            bb = t + half * BPB
            root = bar_bass[ci*8 + half] + 12
            sc.cc(CH_PIANO, 64, 0, bb - 0.02); sc.cc(CH_PIANO, 64, 127, bb)
            v = arc.vel(bb, 20, 50)
            sc.note(CH_PIANO, root, bb, BPB * 3.5, v, max_jit=8)
            sc.note(CH_PIANO, root + 7, bb + 0.5, BPB * 3.0, v - 4, max_jit=8)
            sc.cc(CH_PIANO, 64, 0, bb + BPB * 3.9)
    if roles['cello']:
        melody(sc, CH_CELLO, t, theme, D4 - 12, arc, 40, 78, gate=1.0, max_jit=10)
    if roles['violin']:
        melody(sc, CH_VIOLIN, t, theme, D4 + (12 if roles['hi'] else 0), arc, 52, 100, gate=1.0, max_jit=10)

# --- Coda tail: a long hollow decay on a bare Dm (open fifth + the falling 5-4-3 dying) ---
t = NB * BPB
pv = voice_chord(chord('D', 'F', 'A'), pad_voi[-1], 4, 55, 79)
for p in pv:
    sc.note(CH_PAD, p, t, 14.0, 32, max_jit=6)
sc.note(CH_PAD2, 50, t, 14.0, 28, max_jit=6)       # D
sc.note(CH_BASS, 38, t, 14.0, 30, max_jit=6)       # low D — hollow bottom
# The motif sounds one last time, dying: A -> G -> F (5-4-3) in the cello, very soft.
sc.note(CH_CELLO, ctx.deg(5, D4 - 12), t + 1.0, 4.0, 30, max_jit=6)
sc.note(CH_CELLO, ctx.deg(4, D4 - 12), t + 5.0, 4.0, 26, max_jit=6)
sc.note(CH_CELLO, ctx.deg(3, D4 - 12), t + 9.0, 5.0, 22, max_jit=6)
fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO], t, 14.0, beats=14)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '10 - Elegy.mid')
write_midi(sc, OUT, title='Elegy', text='Vigil / 10', key='Dm')
print_report(OUT, allowed_pcs=['D', 'E', 'F', 'G', 'A', 'Bb', 'C', 'C#'])
