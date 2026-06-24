"""
05 - Letters Unsent   (G minor, harmonic-minor F# for the V, 66 bpm)  — the tragic core.

A lament for words never said. The emotional centre of *Vigil*: openly romantic and
aching, in the manner of Howard Shore's tragic theme for "The Departed" and Richter's
"On the Nature of Daylight". A long swelling arc with a genuinely devastating climax —
full strings, violin high — just past the golden section, then a slow broken
falling-away to a quiet, grief-stricken close.

The tragic device is the HARMONIC-MINOR leading tone F#: the V (D major, often D/F#)
pulling down into i. Many suspensions resolving downward — "the sigh".

Lament ground (per 8-bar pass, descending bass D-C-Bb-A-G... voice-led):
   Gm  -  D/F#  -  Eb(maj7)  -  Bb  -  Cm  -  Gm/Bb  -  D(sus->)/A  -  Gm

Run from anywhere: python 05_letters_unsent.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(5)
BPB = 4
ctx = Ctx(bpm=66, root='G', mode='harmonic_minor', beats_per_bar=BPB)

# Channels (GM): piano, cello, violin, viola, contrabass, strings I + II under-pad
CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# ---------------------------------------------------------------------------
# The lament ground — per-bar (chord pcs, contrabass pitch).
# Bass falls stepwise: D - F#(low) - Eb - Bb -> Cm rises then settles, V/i cadence.
# Built so the descending lament line and the F#->G leading-tone pull both speak.
#   Gm    D/F#       Ebmaj7        Bb        Cm        Gm/Bb     D7sus/A->D  Gm
GROUND = [
    (chord('G','Bb','D'),         43),  # i        (G2)
    (chord('D','F#','A'),         42),  # V/F#     (F#2)  leading tone in the bass
    (chord('Eb','G','Bb','D'),    39),  # bVI maj7 (Eb2)
    (chord('Bb','D','F'),         46),  # III      (Bb2)
    (chord('C','Eb','G'),         48),  # iv       (C3)
    (chord('G','Bb','D'),         46),  # i/Bb     (Bb2)
    (chord('D','G','A'),          45),  # V sus4   (A2)  -> resolves to F#
    (chord('G','Bb','D'),         43),  # i        (G2)
]

# Memory motif coloured for grief: 5-4-3 in G minor = D-C-Bb, with the sigh leaning.
# Cello low statement / violin octave-up climax use the same theme.
G4 = 67  # G4 as the melody's degree-1 anchor
THEME = theme_from_degrees('harmonic_minor', [
    # phrase 1 — the falling memory figure, suspensions resolving down
    (5,0,3),(4,3,1),  (3,4,2),(2,6,2),
    (3,8,2),(4,10,2),  (5,12,2),(4,14,2),
    # phrase 2 — reaches up, then the long sigh down to the tonic
    (3,16,2),(5,18,2),  (6,20,2),(5,22,1),(4,23,1),
    (5,24,3),(4,27,1),  (3,28,2),(1,30,2),
])

# A higher counter-phrase for the climax (violin soaring, the heartbreak)
THEME_HI = theme_from_degrees('harmonic_minor', [
    (8,0,4),  (7,4,2),(6,6,2),  (5,8,3),(4,11,1),  (3,12,2),(2,14,2),
    (5,16,4), (6,20,2),(7,22,2),(8,24,4), (7,28,2),(5,30,2),
]) if False else None  # (kept simple: reuse THEME up an octave at the climax)

# ---------------------------------------------------------------------------
# Form: one long swell to a DEVASTATING climax just past the golden section
# (golden of ~80 bars ~= bar 49), then a slow broken falling-away. 80 bars = 10 passes.
# (name, n_bars, lvl_start, lvl_end)  levels 0..1
SECTIONS = [
    ("intro",   8, 0.04, 0.16),   # near-silence: pad + bass alone
    ("A",       8, 0.18, 0.30),   # cello takes the low statement
    ("A'",      8, 0.30, 0.44),   # piano + inner strings join
    ("B",       8, 0.46, 0.60),   # violin enters, warms
    ("B'",      8, 0.60, 0.74),   # building, fuller
    ("climax", 16, 0.80, 1.00),   # FULL strings, violin high — the devastation
    ("descent",16, 0.66, 0.34),   # broken falling-away begins, long and grieving
    ("coda",    8, 0.28, 0.04),   # grief-stricken quiet close
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.06)

# Roles per section (which instruments + texture)
ROLES = {
    "intro":   dict(pad=1,pad2=0,bass=1,cello=0,violin=0,viola=0,piano=0,eighths=0,climax=0),
    "A":       dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,climax=0),
    "A'":      dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,climax=0),
    "B":       dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=0,climax=0),
    "B'":      dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,climax=0),
    "climax":  dict(pad=1,pad2=1,bass=1,cello=1,violin=1,viola=1,piano=1,eighths=1,climax=1),
    "descent": dict(pad=1,pad2=1,bass=1,cello=1,violin=0,viola=1,piano=1,eighths=0,climax=0),
    "coda":    dict(pad=1,pad2=0,bass=1,cello=1,violin=0,viola=0,piano=0,eighths=0,climax=0),
}

# Expand the form into 8-bar cycles
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

# ---------------------------------------------------------------------------
# Strings I — the main voice-led pad bed across the whole piece (rich, breathing).
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)], 4, (55, 79))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 28, 96)
expression(sc, CH_PAD, 0, NB * BPB, arc, 30)

# Strings II — warm lower under-pad: a voice-led 2-voice bed in a low band so it
# adds weight without colliding on a single pitch (engine voice-leading avoids that).
pad2_voi, _ = voiced_bars([bar_chord[b] if pad2_on[b] else None for b in range(NB)], 2, (50, 67))
for vi in range(2):
    tied_line(sc, CH_PAD2, 0, [v[vi] if v else None for v in pad2_voi], BPB, arc, 24, 80)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 28)

# Viola inner voice — the chord 3rd, tied, for the warm middle.
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(52, 74) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 26, 74)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 30)

# Contrabass — the descending lament ground.
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)], BPB, arc, 32, 90, cc_floor=38)

# ---------------------------------------------------------------------------
# Melody (cello low / violin high) + piano support, per cycle.
for ci, nm in enumerate(cycles):
    t = ci * 8 * BPB
    roles = ROLES[nm]
    seg = pad_voi[ci * 8:(ci + 1) * 8]
    if roles['piano']:
        piano_chords(sc, CH_PIANO, t, seg,
                     [bar_bass[ci*8+i] + 12 for i in range(8)], BPB, arc,
                     eighths=bool(roles['eighths']))
    if roles['cello']:
        # cello carries the low statement except at the climax where the violin soars
        # (cello then doubles an octave below for weight).
        melody(sc, CH_CELLO, t, THEME, G4 - 12, arc, 46, 70)
    if roles['violin']:
        oct_up = 1 if roles['climax'] else 0
        melody(sc, CH_VIOLIN, t, THEME, G4 + (12 if roles['climax'] else 0),
               arc, 58, 112, octave=oct_up if False else 0)

# ---------------------------------------------------------------------------
# Coda tail — a dissolving Gm with a high unresolved A (the suspended 9th / the
# unanswered letter), strings fading to near-silence. Ends musically, never abruptly.
t = NB * BPB
pv = voice_chord(chord('G','Bb','D'), pad_voi[-1], 4, 55, 79)
for p in pv:
    sc.note(CH_PAD, p, t, 11.0, 38, max_jit=6)
sc.note(CH_PAD2, 43, t, 11.0, 34, max_jit=6)   # low G under-pad
sc.note(CH_BASS, 43, t, 11.0, 34, max_jit=6)   # G2 root
sc.note(CH_CELLO, 55, t, 11.0, 32, max_jit=6)  # G3
sc.note(CH_VIOLIN, ctx.deg(2, G4), t + 1.5, 9.5, 28, max_jit=6)  # high A — the unsent word
fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO, CH_VIOLIN], t, 11.0)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '05 - Letters Unsent.mid')
write_midi(sc, OUT, title='Letters Unsent', text='Vigil / 5', key='Gm')
print_report(OUT, allowed_pcs=["G","A","Bb","C","D","Eb","F","F#"])
