"""
03 - The Crowded Hour   (A dorian, 132 bpm)  — the morning rush, life crowding in.

The fastest, most motoric track of *Vigil*. A relentless Glass-style perpetual-motion
piano ostinato (16ths, pendulum) churns almost throughout, never stopping until the
last bar. Sustained strings enter with long lines above the churn; a violin rides
held notes over the top; the contrabass pulses the roots. We build by adding voices +
rising register to an energetic peak ~2/3 in, keep the momentum, then a SUDDEN HUSH at
the very end: the motion stops dead on one held A-dorian chord that fades to silence.

The dorian F# is the glassy brightness; the memory motif (5-4-3 = E-D-C) surfaces in
the violin's long lines, recoloured into the bright dorian.

Run from anywhere: python tracks/03_the_crowded_hour.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord,
                    voiced_bars, tied_line, pad, bass, arpeggiate, melody,
                    expression, fade_out, write_midi, print_report)

random.seed(3)
BPB = 4
ctx = Ctx(bpm=132, root='A', mode='dorian', beats_per_bar=BPB)

# Palette: piano (the engine), contrabass (pulsing roots), cello (inner long line),
# violin (soaring held melody), two string pads (the sustained bed above the churn).
CH_PIANO, CH_BASS, CH_CELLO, CH_VIOLIN, CH_PAD, CH_PAD2 = range(6)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_BASS:(43,'Contrabass'), CH_CELLO:(42,'Cello'),
    CH_VIOLIN:(40,'Violin'), CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# --- The churning loop: 4 bars, changing every 1-2 bars, all in A dorian. ---
# Am - C - G - D  (the dorian D major IV chord = the F#-bright lift each cycle).
LOOP = [
    (chord('A','C','E'),  45),   # Am   (contrabass A2)
    (chord('C','E','G'),  48),   # C
    (chord('G','B','D'),  43),   # G    (contrabass G2 — a step down)
    (chord('D','F#','A'), 50),   # D    (the glassy dorian F#)
]
LOOP_CH = [c for c, _ in LOOP]
LOOP_BS = [b for _, b in LOOP]

# --- Form: enter from near-silence, swell to one energetic peak ~2/3 in, recede. ---
# 33 cycles of 4 bars = 132 bars. At 1.818s/bar -> ~4:00.
SECTIONS = [
    ("intro",   12, 0.05, 0.16),   # piano alone emerging
    ("A",       16, 0.20, 0.34),   # pad + bass join
    ("A'",      16, 0.36, 0.50),   # cello inner line
    ("B",       16, 0.52, 0.66),   # violin enters above
    ("rise",    16, 0.68, 0.84),   # building to the peak
    ("peak",    20, 0.92, 1.00),   # the crowded hour — full, high, relentless
    ("ebb",     20, 0.82, 0.50),   # momentum keeps but recedes
    ("recede",  12, 0.42, 0.20),   # thinning out
    ("hush",     8, 0.16, 0.05),   # almost gone — still churning
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.04)

# Per-section roles (which layers sound, and the piano/violin register octave).
ROLES = {
    "intro":  dict(pad=0,bass=0,cello=0,violin=0,p_oct=0,v_oct=0),
    "A":      dict(pad=1,bass=1,cello=0,violin=0,p_oct=0,v_oct=0),
    "A'":     dict(pad=1,bass=1,cello=1,violin=0,p_oct=0,v_oct=0),
    "B":      dict(pad=1,bass=1,cello=1,violin=1,p_oct=0,v_oct=0),
    "rise":   dict(pad=1,bass=1,cello=1,violin=1,p_oct=1,v_oct=0),
    "peak":   dict(pad=1,bass=1,cello=1,violin=1,p_oct=1,v_oct=1),
    "ebb":    dict(pad=1,bass=1,cello=1,violin=1,p_oct=0,v_oct=0),
    "recede": dict(pad=1,bass=1,cello=0,violin=1,p_oct=0,v_oct=0),
    "hush":   dict(pad=1,bass=0,cello=0,violin=0,p_oct=0,v_oct=0),
}

# Expand sections -> per-cycle names (each cycle = one 4-bar pass of the loop).
cycles = []
for (name, nb, _a, _b) in SECTIONS:
    for _ in range(nb // 4):
        cycles.append(name)
NB = len(cycles) * 4
bar_chord = [LOOP_CH[b % 4] for b in range(NB)]
bar_bass  = [LOOP_BS[b % 4] for b in range(NB)]

def mask(layer):
    out = []
    for nm in cycles:
        out += [bool(ROLES[nm][layer])] * 4
    return out

pad_on, bass_on, cello_on, violin_on = mask('pad'), mask('bass'), mask('cello'), mask('violin')

# --- THE ENGINE: perpetual-motion piano, 16ths, pendulum, never stops till the hush. ---
# Voice the loop into compact 4-note piano chords; the register lifts an octave for
# the rise/peak. Runs every bar except the final held-chord bar.
LAST = NB - 1   # the very last bar is the SUDDEN HUSH (no churn)
piano_band_lo = (52, 76)
piano_voi_lo, _ = voiced_bars(bar_chord[:LAST], 4, piano_band_lo)
# Per-bar octave shift for the piano (driven by p_oct of that bar's section).
p_oct_bar = []
for nm in cycles:
    p_oct_bar += [ROLES[nm]['p_oct']] * 4
piano_voi = []
for i in range(LAST):
    v = piano_voi_lo[i]
    if v and p_oct_bar[i]:
        v = [p + 12 for p in v]
    piano_voi.append(v)
arpeggiate(sc, CH_PIANO, 0, piano_voi, BPB, arc, rate=16, pattern='pendulum',
           vlo=30, vhi=82, gate=1.15, vel_jit=4, accent_every=4, accent=9)

# --- Contrabass: pulsing roots (detached, sustain=False) — the heartbeat of the rush. ---
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB - 1)],
     BPB, arc, vlo=36, vhi=86, sustain=False, gate=0.55, cc_floor=40)

# --- String pad: the sustained bed above the churn (two tied voices in separate
# registers, on two channels, so no same-pitch crossing on one channel). Each voice
# is the highest / a middle chord-tone, voice-led across the loop. ---
def pad_voice(b, target):
    pcs = {p % 12 for p in bar_chord[b]}
    return min((q for q in range(60, 86) if q % 12 in pcs), key=lambda q: abs(q - target))
pad_hi  = [pad_voice(b, 78) if pad_on[b] else None for b in range(NB - 1)]   # ~F#5/E5 top
pad_mid = [pad_voice(b, 69) if pad_on[b] else None for b in range(NB - 1)]   # ~A4 inner
tied_line(sc, CH_PAD,  0, pad_hi,  BPB, arc, vlo=26, vhi=80)
tied_line(sc, CH_PAD2, 0, pad_mid, BPB, arc, vlo=24, vhi=74)
expression(sc, CH_PAD,  0, (NB - 1) * BPB, arc, 32)
expression(sc, CH_PAD2, 0, (NB - 1) * BPB, arc, 30)

# --- Cello: a slow inner long line (the lament-coloured tenor under the brightness). ---
# Moves once per 2 bars between chord tones, mostly stepwise/descending.
def cello_pitch(b):
    pcs = {p % 12 for p in bar_chord[b]}
    # the inner line rises with the swell and sinks when quiet — a real contour,
    # not a fixed cell; always snapped to a chord tone in the tenor band.
    drift = int(round(6 * arc.level(b * BPB)))
    target = [55, 53, 50, 50][b % 4] + drift
    return min((q for q in range(45, 66) if q % 12 in pcs), key=lambda q: abs(q - target))
cello_line = [cello_pitch(b) if cello_on[b] else None for b in range(NB - 1)]
tied_line(sc, CH_CELLO, 0, cello_line, BPB, arc, vlo=30, vhi=78)
expression(sc, CH_CELLO, 0, (NB - 1) * BPB, arc, 34)

# --- Violin: LONG held notes riding over the top. The memory motif 5-4-3 (E-D-C),
# recoloured bright, surfaces and is answered, then climbs at the peak. ---
A4 = 69  # the pitch of degree 1 (A4) for the violin's high lines
# Each entry sounds for 2 bars (8 beats); shaped as gentle downward sighs.
VIOLIN = theme_from_degrees('dorian', [
    (5, 0, 7.5),            # E  (the 5)
    (4, 8, 7.5),            # D  (the 4)  — sigh down
    (3, 16, 7.5),           # C  (the 3)  — the memory motif lands
    (5, 24, 7.5),           # E
    (8, 32, 7.5),           # A (octave) — lift
    (7, 40, 7.5),           # G
    (5, 48, 7.5),           # E
    (4, 56, 7.5),           # D
    (3, 64, 7.5),           # C  — motif again, lower swell
    (2, 72, 7.5),           # B
    (8, 80, 7.5),           # A — the climb begins
    (9, 88, 7.5),           # B (9th)
    (10, 96, 7.5),          # C (10th, high) — peak apex
    (8, 104, 7.5),          # A
    (7, 112, 7.5),          # G
    (5, 120, 7.5),          # E — last of the rise

    # --- PEAK (bars 76-95): the soaring climax of the line, lifted an octave by
    # v_oct=1; the memory motif up high, reaffirmed and answered. ---
    (8, 128, 7.5),          # A  (lifted -> A6) — apex
    (7, 136, 7.5),          # G
    (8, 144, 7.5),          # A
    (6, 152, 7.5),          # F# (the dorian brightness, high)
    (5, 160, 7.5),          # E
    (8, 168, 7.5),          # A  — reaffirm the height
    (7, 176, 7.5),          # G
    (5, 184, 7.5),          # E
    (4, 192, 7.5),          # D
    (3, 200, 7.5),          # C  — the motif at the very top of the peak

    # --- EBB (bars 96-115): the line falls back to earth (oct 0), descending,
    # the memory motif 5-4-3 sighing lower each pass. ---
    (5, 208, 7.5),          # E  (un-lifted, mid register again)
    (4, 216, 7.5),          # D
    (3, 224, 7.5),          # C  (motif)
    (2, 232, 7.5),          # B
    (3, 240, 7.5),          # C
    (1, 248, 7.5),          # A
    (2, 256, 7.5),          # B
    (1, 264, 7.5),          # A
    (5, 272, 7.5),          # E  — one last gentle sigh
    (3, 280, 11.5),         # C  — long, dissolving into the recede
]
)
# The violin enters where its mask first turns on (the B section) and rides one long
# continuous line of held notes through the rise, the peak (an octave up), and the ebb.
VIOLIN_ENTRY = next(b for b in range(NB) if violin_on[b])   # first violin-on bar
V_T0 = VIOLIN_ENTRY * BPB                                    # entry beat
def violin_octave_at(start_beat):
    bar = int(start_beat // BPB)
    bar = min(max(bar, 0), NB - 1)
    nm = cycles[bar // 4]
    return ROLES[nm]['v_oct']

for (off, start, dur) in VIOLIN:
    abs_start = V_T0 + start
    bar = int(abs_start // BPB)
    if bar < NB - 1 and violin_on[bar]:
        oc = violin_octave_at(abs_start)
        sc.note(CH_VIOLIN, A4 + off + 12 * oc, abs_start, dur * 0.97,
                arc.vel(abs_start, 58, 108) + random.randint(-5, 5), max_jit=10)
expression(sc, CH_VIOLIN, V_T0, (NB - 1) * BPB, arc, 36)

# --- THE SUDDEN HUSH: motion stops on one held A-dorian chord (Am add9 glow), fading. ---
t = LAST * BPB
HUSH = voice_chord(chord('A','C','E'), piano_voi[-1] if piano_voi else None, 4, 55, 79)
hush_len = 9.0
for p in HUSH:
    sc.note(CH_PAD, p, t, hush_len, 44, max_jit=6)
    sc.note(CH_PIANO, p, t, hush_len, 40, max_jit=6)   # piano lets the last chord ring
sc.note(CH_PAD2, 45, t, hush_len, 40, max_jit=6)        # low A in the under-pad
sc.note(CH_CELLO, 57, t, hush_len, 38, max_jit=6)       # A3 in the cello
sc.note(CH_VIOLIN, A4 + 7, t + 0.5, hush_len - 0.5, 34, max_jit=6)  # high E (the 5) glimmer
sc.cc(CH_PIANO, 64, 127, t)   # pedal down — let it bloom
fade_out(sc, [CH_PAD, CH_PAD2, CH_PIANO, CH_CELLO, CH_VIOLIN], t, hush_len, beats=10, top=64)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '03 - The Crowded Hour.mid')
write_midi(sc, OUT, title='The Crowded Hour', text='Vigil / 3', key='Am')
print_report(OUT, allowed_pcs=["A","B","C","D","E","F#","G"])
