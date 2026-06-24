"""
09 - Bright Ruin   (D mixolydian, 104 bpm)  — the bittersweet, running track.

Major-leaning brightness undercut by melancholy: the mixolydian flat-7 (C natural)
keeps the sun behind a thin cloud. Piano broken chords + walking strings carry a
lyrical, wistful violin tune; one full-hearted-but-aching peak, then it eases off,
ending warm and a touch unresolved (an open D add9, never the leading-tone close).

Harmonic spine (per 4-bar cell): D - C - G/B - Am  (the flat-7 C is the wistfulness),
answered later by D - Bm - G - Asus. The album's memory motif 5-4-3 surfaces here as
A-G-F# over the home chord.

Run from anywhere: python 09_bright_ruin.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Ctx, Score, Arc, chord, theme_from_degrees, voice_chord, voiced_bars,
                    tied_line, pad, bass, arpeggiate, ostinato, melody, piano_chords,
                    expression, fade_out, write_midi, print_report)

random.seed(9)
BPB = 4
ctx = Ctx(bpm=104, root='D', mode='mixolydian', beats_per_bar=BPB)

CH_PIANO, CH_CELLO, CH_VIOLIN, CH_VIOLA, CH_BASS, CH_PAD, CH_PAD2 = range(7)
sc = Score(ctx)
for ch, (prog, nm) in {
    CH_PIANO:(0,'Piano'), CH_CELLO:(42,'Cello'), CH_VIOLIN:(40,'Violin'),
    CH_VIOLA:(41,'Viola'), CH_BASS:(43,'Contrabass'),
    CH_PAD:(48,'Strings I'), CH_PAD2:(49,'Strings II'),
}.items():
    sc.program(ch, prog, nm)

# ----------------------------------------------------------------------------
# Harmony — an 8-bar progression that turns home -> away -> home, with a lament
# descent in the bass (D - C# is avoided; the bass walks D C B A | G B C# ... no,
# stays modal: D C B A | B A G A). The flat-7 C natural is the wistful colour.
# Each entry: (chord pcs, contrabass root).
# Progression A (bars 0-7 of an 8-bar cell):
#   D  | C  | G/B | Am | Bm | G | Asus(A-D-E) | A
# Bass descends D->C->B->A then leaps up and steps B->? to lead back home.
GROUND = [
    (chord('D','F#','A'),        50),  # D     I
    (chord('C','E','G'),         48),  # C     bVII  (the flat-7 brightness/ache)
    (chord('G','B','D'),         47),  # G/B   IV    (B in the bass — descending line)
    (chord('A','C','E'),         45),  # Am    v  (minor dominant — the melancholy)
    (chord('B','D','F#'),        47),  # Bm    vi
    (chord('G','B','D'),         43),  # G     IV
    (chord('A','D','E'),         45),  # Asus4 (suspension over A)
    (chord('A','C','E'),         45),  # Am — the suspension resolves DOWN (D->C), modal close
]
# Bar 6 Asus4 (D over A) resolves its suspension downward to bar 7 Am (C over A):
# "the sigh". Fully modal — no leading tone — keeping the bittersweet, unresolved feel.

D5 = 74   # violin tonic register

# Lyrical wistful melody (one 8-bar phrase = the cell). Built from scale degrees of
# D mixolydian; the 5-4-3 memory motif (A-G-F#) is woven in over bars 0 and 4.
# (degree, start_beat, dur)
THEME = theme_from_degrees('mixolydian', [
    # bar0 D: rise to the 5th then the falling memory motif 5-4-3 (A-G-F#)
    (5, 0.0, 1.5), (6, 1.5, 0.5), (5, 2.0, 1.0), (4, 3.0, 1.0),
    # bar1 C: descend onto the flat-7 colour, sigh 3->2
    (3, 4.0, 1.5), (2, 5.5, 0.5), (1, 6.0, 1.0), (2, 7.0, 1.0),
    # bar2 G/B: lift, open it out
    (3, 8.0, 1.0), (5, 9.0, 1.0), (4, 10.0, 1.5), (3, 11.0, 1.0),
    # bar3 Am: aching turn, suspension resolving downward 4->3
    (2, 12.0, 1.0), (4, 13.0, 1.0), (3, 14.0, 2.0),
    # bar4 Bm: reach higher (the wistful peak of the phrase) — motif up an octave-ish
    (6, 16.0, 1.0), (7, 17.0, 1.0), (6, 18.0, 1.0), (5, 19.0, 1.0),
    # bar5 G: come down singing
    (5, 20.0, 1.5), (4, 21.5, 0.5), (3, 22.0, 1.0), (2, 23.0, 1.0),
    # bar6 Asus: hang on the suspended 4 (G over A), lean
    (4, 24.0, 2.0), (3, 26.0, 1.0), (2, 27.0, 1.0),
    # bar7 A: gather to lead back home (land on 1)
    (2, 28.0, 1.0), (3, 29.0, 1.0), (2, 30.0, 1.0), (1, 31.0, 1.0),
])

# ----------------------------------------------------------------------------
# Form: a single swell to one bittersweet peak, then ease off. 13 cells of 8 bars
# = 104 bars. (target ~104 bars @ 2.31s/bar = ~4:00)
SECTIONS = [
    ("intro",  8, 0.05, 0.16),   # piano alone, near-silence
    ("A",      8, 0.20, 0.30),   # + bass, pad, walking strings
    ("A'",     8, 0.30, 0.40),   # + cello countermelody
    ("B",      8, 0.40, 0.52),   # violin tune enters
    ("B'",     8, 0.52, 0.62),
    ("lift",   8, 0.62, 0.74),
    ("peak",  16, 0.80, 0.98),   # full-hearted bittersweet climax (past golden sec)
    ("ease",   8, 0.74, 0.58),
    ("recede", 8, 0.52, 0.40),
    ("settle", 8, 0.36, 0.24),
    ("coda",   8, 0.20, 0.06),
]
arc = Arc(SECTIONS, beats_per_bar=BPB, breathe=0.045)

ROLES = {  # per section texture
    "intro":  dict(piano=1,bass=0,pad=0,pad2=0,arp=0,cello=0,violin=0,viola=0,eighths=0,oct=0),
    "A":      dict(piano=1,bass=1,pad=1,pad2=0,arp=0,cello=0,violin=0,viola=1,eighths=0,oct=0),
    "A'":     dict(piano=1,bass=1,pad=1,pad2=0,arp=0,cello=1,violin=0,viola=1,eighths=0,oct=0),
    "B":      dict(piano=1,bass=1,pad=1,pad2=1,arp=0,cello=1,violin=1,viola=1,eighths=0,oct=0),
    "B'":     dict(piano=1,bass=1,pad=1,pad2=1,arp=1,cello=1,violin=1,viola=1,eighths=0,oct=0),
    "lift":   dict(piano=1,bass=1,pad=1,pad2=1,arp=1,cello=1,violin=1,viola=1,eighths=1,oct=0),
    "peak":   dict(piano=1,bass=1,pad=1,pad2=1,arp=1,cello=1,violin=1,viola=1,eighths=1,oct=1),
    "ease":   dict(piano=1,bass=1,pad=1,pad2=1,arp=1,cello=1,violin=0,viola=1,eighths=0,oct=0),
    "recede": dict(piano=1,bass=1,pad=1,pad2=0,arp=0,cello=1,violin=0,viola=1,eighths=0,oct=0),
    "settle": dict(piano=1,bass=1,pad=1,pad2=0,arp=0,cello=0,violin=0,viola=0,eighths=0,oct=0),
    "coda":   dict(piano=1,bass=0,pad=1,pad2=0,arp=0,cello=0,violin=0,viola=0,eighths=0,oct=0),
}

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

pad_on   = mask('pad')
pad2_on  = mask('pad2')
bass_on  = mask('bass')
viola_on = mask('viola')

# ----------------------------------------------------------------------------
# Sustained, voice-led pad bed (Strings I) across the whole piece. Also feeds the
# piano and arpeggios their voicings.
pad_voi, _ = voiced_bars([bar_chord[b] if pad_on[b] else None for b in range(NB)], 4, (57, 81))
for vi in range(4):
    tied_line(sc, CH_PAD, 0, [v[vi] if v else None for v in pad_voi], BPB, arc, 28, 86)
expression(sc, CH_PAD, 0, NB * BPB, arc, 36)

# All-cell voicings (regardless of pad mask) for piano/arp to use even in intro.
all_voi, _ = voiced_bars([bar_chord[b] for b in range(NB)], 4, (55, 79))

# Warm low under-pad (Strings II): the CHORD ROOT + its fifth, low and warm.
# NB: derive from the chord root (pcs[0]), never the contrabass note — on the G/B
# slash chord the bass is B, and root+5th off B would sound F#, a semitone clash
# against the held G. Snap to the nearest chord-root pitch to keep it low.
def pad2_pitches(pcs, b):
    root_pc = pcs[0] % 12
    r0 = b + 12
    up = r0
    while up % 12 != root_pc:
        up += 1
    dn = r0
    while dn % 12 != root_pc:
        dn -= 1
    root = up if (up - r0) <= (r0 - dn) else dn
    fifth_pc = (root_pc + 7) % 12
    f = root + 1
    while f % 12 != fifth_pc:
        f += 1
    return [root, f]
for vi in range(2):
    tied_line(sc, CH_PAD2, 0,
              [pad2_pitches(bar_chord[b], bar_bass[b])[vi] if pad2_on[b] else None for b in range(NB)],
              BPB, arc, 24, 72)
expression(sc, CH_PAD2, 0, NB * BPB, arc, 32)

# Viola inner voice: the 3rd of each chord, tied — the warm middle.
def viola_pitch(pcs):
    third = pcs[1] if len(pcs) > 1 else pcs[0]
    return next((q for q in range(52, 72) if q % 12 == third % 12), 60)
tied_line(sc, CH_VIOLA, 0,
          [viola_pitch(bar_chord[b]) if viola_on[b] else None for b in range(NB)],
          BPB, arc, 26, 70)
expression(sc, CH_VIOLA, 0, NB * BPB, arc, 32)

# Contrabass: the walking/descending root line (lament underneath the brightness).
bass(sc, CH_BASS, 0, [bar_bass[b] if bass_on[b] else None for b in range(NB)],
     BPB, arc, 32, 84, sustain=True, cc_floor=38)

# ----------------------------------------------------------------------------
# Per-cycle: piano broken chords (momentum), violin arpeggio sparkle, cello
# countermelody, and the lyrical violin tune.
for ci, nm in enumerate(cycles):
    t = ci * 8 * BPB
    roles = ROLES[nm]
    seg     = all_voi[ci * 8:(ci + 1) * 8]
    # Piano left-hand root an octave BELOW the voicing (distinct register, no clash).
    seg_bass = [bar_bass[ci * 8 + i] for i in range(8)]

    if roles['piano']:
        piano_chords(sc, CH_PIANO, t, seg, seg_bass, BPB, arc,
                     eighths=bool(roles['eighths']), vlo=24, vhi=64)

    if roles['arp']:
        # Glass-ish broken-chord sparkle, mid-rate, in a HIGH register clear of the
        # piano_chords voicing (top voices only, lifted an octave) so it shimmers
        # rather than re-striking the same held pitches.
        hi_voi = []
        for v in seg:
            top = sorted(set(v))[-3:]           # upper three voices
            hi_voi.append([p + 12 for p in top])
        arpeggiate(sc, CH_PIANO, t, hi_voi, BPB, arc, rate=8, pattern='broken',
                   vlo=20, vhi=54, gate=1.0, accent_every=4, accent=8)

    if roles['cello']:
        # Cello countermelody: the theme an octave+ down, gentler, slightly behind.
        melody(sc, CH_CELLO, t, THEME, D5 - 24, arc, 40, 66, gate=0.95)

    if roles['violin']:
        octv = 1 if roles['oct'] else 0
        melody(sc, CH_VIOLIN, t, THEME, D5 - 12, arc, 56, 104, octave=octv)

# ----------------------------------------------------------------------------
# Coda: a warm, slightly unresolved D add9 (D-F#-A-E) — no leading tone, the 9th
# left ringing. Fade out rather than a clean close.
t = NB * BPB
pv = voice_chord(chord('D','F#','A'), pad_voi[-1] if pad_voi[-1] else None, 4, 57, 81)
for p in pv:
    sc.note(CH_PAD, p, t, 11.0, 38, max_jit=6)
sc.note(CH_PAD2, 50, t, 11.0, 30, max_jit=6)      # low D
sc.note(CH_BASS, 38, t, 11.0, 32, max_jit=6)      # D pedal
sc.note(CH_CELLO, 57, t + 0.5, 10.5, 32, max_jit=6)   # A
sc.note(CH_VIOLIN, ctx.deg(2, D5), t + 1.0, 9.5, 30, max_jit=6)  # high E (the add9 glimmer)
# soft piano roll of the open chord
sc.cc(CH_PIANO, 64, 127, t)
for k, p in enumerate([50, 62, 66, 69, 76]):
    sc.note(CH_PIANO, p, t + k * 0.18, 10.0 - k * 0.18, 34 - k, max_jit=6)
sc.cc(CH_PIANO, 64, 0, t + 11.0)
fade_out(sc, [CH_PAD, CH_PAD2, CH_BASS, CH_CELLO, CH_VIOLIN], t, 11.0)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'midi', '09 - Bright Ruin.mid')
write_midi(sc, OUT, title='Bright Ruin', text='Vigil / 9', key='D')
print_report(OUT, allowed_pcs=['D','E','F#','G','A','B','C'])
