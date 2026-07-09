"""
06 - Pulse   (E phrygian, 144 bpm, 4/4)  — the motoric chase.

The most rhythmic, anxious track of *Vigil*. A relentless low ostinato hammers a
pedal-point E (low piano + contrabass, repeated 16ths/8ths) from near the start.
Phrygian flat-2 (F natural) gives the menace. Over the drone, upper triads arrive as
EVENTS, not a flowing line — Em / F / Em / Dm, then darker Em / C / Am / F — stabbed
out staccato by the strings with velocity accents and short rising figures. Dread
ratchets via accumulating voices and rising harmony to a brief terrifying peak — then
it CUTS OUT, dropping to a single throbbing low E that gutters and dies.

No lyrical melody. The memory motif (5-4-3 = B-A-G in E minor) surfaces only as a
clipped, anxious stab-figure near the peak. Run: python tracks/06_pulse.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(6)
BPB = 4
ctx = Ctx(bpm=144, root='E', mode='phrygian', beats_per_bar=BPB)

# Palette subset: piano (low hammer), contrabass (the pedal), cello (low ostinato
# reinforcement + stabs), viola + violin (staccato upper-triad stabs / rising figures),
# strings I as a thin reinforcing pad for the peak.
CH_PIANO, CH_BASS, CH_CELLO, CH_VIOLA, CH_VIOLIN, CH_PAD = range(6)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_BASS:(43,'Contrabass'), CH_CELLO:(42,'Cello'),
    CH_VIOLA:(41,'Viola'), CH_VIOLIN:(40,'Violin'), CH_PAD:(48,'Strings I'),
}.items():
    sc.program(ch, prog, nm)

# ---------------------------------------------------------------------------
# Harmony as EVENTS over a pedal E. Two 4-bar event-cells; the second is darker.
# Upper triads (pcs) per bar; the bass/ostinato stays nailed to E throughout.
EM = chord('E','G','B'); F = chord('F','A','C'); DM = chord('D','F','A')
C  = chord('C','E','G'); AM = chord('A','C','E')
CELL_A = [EM, F,  EM, DM]            # Em - F(menace) - Em - Dm
CELL_B = [EM, C,  AM, F]             # Em - C  - Am - F  (darker, rising tension)
E_PED  = 40                          # E2 contrabass pedal (low, throbbing, idiomatic)
E_PED2 = 40                          # E2 piano-hand hammer (locks with the bass)

# ---------------------------------------------------------------------------
# Form: 128 bars at bar=1.667s -> ~213s ~ 3:33. One long ratcheting swell to a brief
# peak near the golden section, then an abrupt cut to a guttering low pedal.
SECTIONS = [
    ("creep",   16, 0.08, 0.20),   # bare pedal pulse emerges from near-silence
    ("stir",    16, 0.22, 0.34),   # cello doubles the ostinato; first faint stabs
    ("press",   16, 0.36, 0.50),   # viola stabs land on the event-triads
    ("drive",   16, 0.52, 0.66),   # violin rising figures; cell B (darker) enters
    ("clench",  16, 0.68, 0.84),   # full stabs, accents tighten
    ("peak",    16, 0.90, 1.00),   # terrifying peak — everything hammering
    ("cut",      8, 0.30, 0.16),   # abrupt collapse to a single throbbing pedal
    ("gutter",  24, 0.14, 0.02),   # the pedal flickers and dies
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.03)

cycles = []
for (name, nb, _a, _b) in SECTIONS:
    cycles += [name] * nb
NB = len(cycles)

# Per-bar upper-triad event harmony. Cells alternate; CELL_B from "drive" onward.
def bar_triad(b):
    nm = cycles[b]
    cell = CELL_B if nm in ("drive", "clench", "peak") else CELL_A
    return cell[b % 4]

# Roles per section (which layers sound). The accumulation is the dread engine.
ROLES = {
    "creep":  dict(pedal16=0, bass=1, cello=0, viola=0, violin=0, pad=0, stab=0, rise=0, peak=0),
    "stir":   dict(pedal16=1, bass=1, cello=1, viola=0, violin=0, pad=0, stab=0, rise=0, peak=0),
    "press":  dict(pedal16=1, bass=1, cello=1, viola=1, violin=0, pad=0, stab=1, rise=0, peak=0),
    "drive":  dict(pedal16=1, bass=1, cello=1, viola=1, violin=1, pad=0, stab=1, rise=1, peak=0),
    "clench": dict(pedal16=1, bass=1, cello=1, viola=1, violin=1, pad=1, stab=1, rise=1, peak=0),
    "peak":   dict(pedal16=1, bass=1, cello=1, viola=1, violin=1, pad=1, stab=1, rise=1, peak=1),
    "cut":    dict(pedal16=0, bass=1, cello=0, viola=0, violin=0, pad=0, stab=0, rise=0, peak=0),
    "gutter": dict(pedal16=0, bass=1, cello=0, viola=0, violin=0, pad=0, stab=0, rise=0, peak=0),
}
def on(layer, b):
    return bool(ROLES[cycles[b]][layer])

# ---------------------------------------------------------------------------
# 1) THE PEDAL — contrabass throbbing E on every beat (and 8ths once driving).
#    Detached, accented downbeat. This is the heartbeat of dread.
for b in range(NB):
    bb = b * BPB
    eighth = on('pedal16', b)
    # quarter pulse always; subdivide to 8ths when the engine is running
    n_hits = 8 if eighth else 4
    step = BPB / n_hits
    for k in range(n_hits):
        t = bb + k * step
        acc = (k == 0)
        vel = arc.vel(t, 30, 104) + (12 if acc else 0) + random.randint(-3, 3)
        # gutter: let the pulse thin to a heavy quarter-note throb
        if cycles[b] == 'gutter' and (k % 2 == 1):
            continue
        sc.note(CH_BASS, E_PED, t, step * (0.55 if eighth else 0.8), vel, max_jit=3)
expression(sc, CH_BASS, 0, NB * BPB, arc, 40)

# ---------------------------------------------------------------------------
# 2) THE OSTINATO ENGINE — low piano driving 16ths on the pedal E, the motoric core.
#    A repeated-note cell; callable pitch lets it dip to phrygian-2 (F) as a grind.
def osti_pitch(bar):
    # mostly the pedal E2; on bar's beat-4 region nudge to F (flat-2 menace) when driving
    return E_PED2
# build the cell: four 16ths per beat -> sixteen per bar, accent the beat
def piano_ostinato(t0, n_bars, start_bar):
    for bar in range(n_bars):
        gb = start_bar + bar
        bb = t0 + bar * BPB
        if not on('pedal16', gb):
            # creep/cut/gutter: sparse — a single low piano thud on the downbeat
            if on('bass', gb) and cycles[gb] in ('creep',):
                vel = arc.vel(bb, 26, 70) + random.randint(-3, 3)
                sc.note(CH_PIANO, E_PED2, bb, BPB * 0.5, vel, max_jit=4)
            continue
        # pedal blur off — we want crisp motoric attacks, so no sustain pedal here
        for k in range(16):
            t = bb + k * (BPB / 16)
            acc = (k % 4 == 0)
            # phrygian-2 grind: the last 16th of beats 2 & 4 leans to F
            p = E_PED2
            if k in (7, 15):
                p = E_PED2 + 1   # F2
            vel = arc.vel(t, 30, 100) + (14 if acc else 0) + random.randint(-4, 4)
            sc.note(CH_PIANO, p, t, (BPB / 16) * 0.85, vel, max_jit=2)
piano_ostinato(0, NB, 0)
expression(sc, CH_PIANO, 0, NB * BPB, arc, 36)

# ---------------------------------------------------------------------------
# 3) CELLO — reinforces the ostinato an octave up (driving 8ths) once it stirs;
#    a low E3 grind that locks with the piano. Detached, accented.
for b in range(NB):
    if not on('cello', b):
        continue
    bb = b * BPB
    for k in range(8):
        t = bb + k * (BPB / 8)
        acc = (k % 2 == 0)
        p = 52  # E3
        if k in (3, 7):
            p = 53  # F3 — the menace leans up
        vel = arc.vel(t, 28, 92) + (8 if acc else 0) + random.randint(-3, 3)
        sc.note(CH_CELLO, p, t, (BPB / 8) * 0.6, vel, max_jit=3)
# expression spans the whole cello channel (silent bars simply carry no notes)
expression(sc, CH_CELLO, 0, NB * BPB, arc, 36)

# ---------------------------------------------------------------------------
# 4) STACCATO UPPER-TRIAD STABS — viola voices the event-triad, short & hard,
#    landing on beats 1 and 3 (off-pulse jabs). Voice-led for natural sighs.
viola_band = (55, 74)
prev_v = None
for b in range(NB):
    if not on('stab', b):
        continue
    bb = b * BPB
    pcs = bar_triad(b)
    prev_v = voice_chord(pcs, prev_v, 3, *viola_band)
    # two clipped stabs per bar (beats 1 and 3); accent the first
    for (beat, acc) in ((0.0, True), (2.0, False)):
        for p in prev_v:
            vel = arc.vel(bb + beat, 36, 100) + (10 if acc else 0) + random.randint(-4, 4)
            sc.note(CH_VIOLA, p, bb + beat, 0.45, vel, max_jit=4)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 34)

# ---------------------------------------------------------------------------
# 5) VIOLIN — short RISING figures (anxious, scrabbling up the phrygian scale) plus,
#    near the peak, a clipped statement of the memory motif (5-4-3 = B-A-G), stabbed.
E5 = 76  # violin register
RISE = theme_from_degrees('phrygian', [
    (1, 0.0, 0.5), (2, 0.5, 0.5), (3, 1.0, 0.5), (5, 1.5, 0.5),   # E F G B clipped run up
])
MOTIF = theme_from_degrees('phrygian', [
    (5, 0.0, 0.5), (4, 0.75, 0.5), (3, 1.5, 0.75),                # B - A - G  (memory, anxious)
])
for b in range(NB):
    if not on('rise', b):
        continue
    bb = b * BPB
    nm = cycles[b]
    if on('peak', b) and (b % 2 == 0):
        # peak: clipped memory motif, high and hard
        melody(sc, CH_VIOLIN, bb, MOTIF, E5, arc, 64, 112, gate=0.7, max_jit=4)
        melody(sc, CH_VIOLIN, bb + 2.0, RISE, E5, arc, 60, 110, gate=0.7, max_jit=4)
    else:
        # rising scrabble on beats 1 and 3
        melody(sc, CH_VIOLIN, bb, RISE, E5, arc, 54, 100, gate=0.7, max_jit=4)
        melody(sc, CH_VIOLIN, bb + 2.0, RISE, E5 - 0, arc, 54, 100, gate=0.7, max_jit=4)
expression(sc, CH_VIOLIN, 0, NB * BPB, arc, 34)

# ---------------------------------------------------------------------------
# 6) PAD — a thin, sustained reinforcing string bed only at clench/peak: the
#    event-triad held under the stabs to thicken the terror. Tied (no re-bowing).
pad_chords = [bar_triad(b) if on('pad', b) else None for b in range(NB)]
pad(sc, CH_PAD, 0, pad_chords, BPB, arc, n_voices=3, band=(60, 81),
    vlo=24, vhi=82, cc_floor=30)

# ---------------------------------------------------------------------------
# 7) THE CUT + GUTTER coda. "cut" already drops to bare bass pulse above; here we
#    let the final pedal flicker and die with a fade. The contrabass keeps a heavy,
#    slowing throb through 'gutter'; we add a low piano after-resonance and fade out.
t_end = NB * BPB
# a final low E thud that rings and decays under the fade
sc.note(CH_BASS, E_PED, t_end, 8.0, 30, max_jit=4)
sc.note(CH_PIANO, E_PED2, t_end, 8.0, 24, max_jit=4)
fade_out(sc, [CH_BASS, CH_PIANO, CH_PAD, CH_CELLO, CH_VIOLA, CH_VIOLIN], t_end, 8.0, beats=12, top=40)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '06 - Pulse.mid')
write_midi(sc, OUT, title='Pulse', text='Vigil / 6', key='Em')
print_report(OUT, allowed_pcs=["E","F","G","A","B","C","D"])
