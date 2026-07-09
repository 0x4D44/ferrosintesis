"""
RIVERWAKE — a single, unbroken ~60-minute piece in the spirit of Mike Oldfield's
"Amarok": one restless river of acoustic guitars, hand percussion, whistle, fiddle,
bells and choir, forever shifting key, tempo and mood, quoting a handful of recurring
themes but never quite repeating itself. Includes Amarok's touches: a false ending and
a hidden Morse-code message.

    python riverwake.py        ->  midi/Riverwake.mid

All structure lives here; all sound lives in folk.py / ../engine.py.
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import folk
from folk import Medley

random.seed(1990)   # the year of Amarok

# SCALE multiplies every section's bar-count to dial the total to ~60:00 without
# changing the macro shape (each section's seconds scale linearly with its bars).
SCALE = 3.24

def B(base):
    """scaled bar count, snapped to a whole 4-bar phrase, min 4."""
    return max(4, int(round(base * SCALE / 4.0)) * 4)

# ---- recurring thematic material --------------------------------------------
# THEME_A — the "main" tune (degree, dur_beats); arches up to the octave and home.
THEME_A = [(5,1.5),(6,0.5),(8,2),(7,1),(5,1),(6,2),(5,0.5),(3,0.5),
           (2,1),(1,2),(3,1),(5,1),(8,1.5),(7,0.5),(5,2)]
A_DEG = [5,8,7,5,6,5,3,1]          # degree-only, for phrase quoting
THEME_B = [1,3,5,8,5,3,2,1]        # the bell motif
THEME_C = [1,3,5,5,8,5,3,1]        # the dance motif

m = Medley(start_bpm=92)

# Common folk progressions (scale-degree per bar)
P_DOR  = [1,7,4,1]        # dorian vamp  i - bVII - IV - i
P_MIX  = [1,7,4,5]        # mixolydian
P_ION  = [1,5,6,4]        # I V vi IV
P_AEOL = [1,6,3,7]        # i VI III VII
P_FOLK = [1,4,5,4]
P_MIN  = [1,4,1,5]
# 8-bar A/B forms (the per-bar prog cycles, so an 8-degree list plays as AABB...) —
# these give long rhythmic sections a contrasting B-part instead of one static vamp.
P_DOR8  = [1,7,4,1, 6,7,4,5]
P_MIX8  = [1,7,4,5, 6,5,4,5]
P_ION8  = [1,5,6,4, 4,5,1,5]
P_FOLK8 = [1,4,5,4, 6,4,5,1]
P_MIN8  = [1,6,3,7, 4,5,1,5]
P_PHR8  = [1,2,1,7, 6,7,1,2]

# ============================================================================
# I.  AWAKENING  — D dorian dawn; the bell theme and main theme are introduced.
# ============================================================================
m.add('ambient',  bpm=68,  root='D', mode='aeolian',    bars=B(8),  prog=P_AEOL, lvl=(0.05,0.22))
m.add('pastoral', bpm=88,  root='D', mode='dorian',     bars=B(12), prog=P_DOR,  lvl=(0.22,0.4), motif=A_DEG)
m.add('bells',    bpm=92,  root='A', mode='dorian',     bars=B(10), prog=P_DOR,  lvl=(0.3,0.5),  motif=THEME_B)
m.add('pastoral', bpm=96,  root='G', mode='ionian',     bars=B(12), prog=P_ION,  lvl=(0.35,0.55), motif=A_DEG)
m.add('theme',    bpm=100, root='D', mode='dorian',     bars=B(12), prog=P_DOR,  theme=THEME_A, lead=folk.FLUTE)
m.add('transition',bpm=112,root='D', mode='mixolydian', bars=B(4),  prog=P_MIX)

# ============================================================================
# II.  FIRST DANCE  — reels and jigs, fiddle to the fore, modulating up.
# ============================================================================
m.add('folk_dance',bpm=128,root='D', mode='mixolydian', bars=B(14), prog=P_MIX8, motif=THEME_C, jiggy=False)
m.add('folk_dance',bpm=132,root='G', mode='mixolydian', bars=B(14), prog=P_MIX8, motif=THEME_C, jiggy=True)
m.add('chase',    bpm=138, root='A', mode='dorian',     bars=B(12), prog=P_DOR8, motif=A_DEG)
m.add('folk_dance',bpm=132,root='D', mode='ionian',     bars=B(12), prog=P_FOLK8, motif=THEME_C, jiggy=False)
m.add('transition',bpm=120,root='D', mode='ionian',     bars=B(4),  prog=P_FOLK)

# ============================================================================
# III.  PROCESSION  — the main theme in full, choir + bells, a wide major plateau.
# ============================================================================
m.add('theme',    bpm=104, root='D', mode='ionian',     bars=B(16), prog=P_ION, theme=THEME_A, lead=folk.FLUTE, full=True)
m.add('bells',    bpm=104, root='A', mode='ionian',     bars=B(10), prog=P_ION, lvl=(0.45,0.62), motif=THEME_B)
m.add('anthem',   bpm=108, root='D', mode='ionian',     bars=B(14), prog=P_FOLK8, motif=A_DEG)

# ============================================================================
# IV.  THE GLADE  — the river pools: ambient, a hush, then a whimsical waltz.
# ============================================================================
m.add('ambient',  bpm=72,  root='B', mode='aeolian',    bars=B(10), prog=P_AEOL, lvl=(0.12,0.3))
m.add('hush',     bpm=80,  root='E', mode='dorian',     bars=B(10), prog=P_DOR,  motif=A_DEG)
m.add('waltz',    bpm=132, root='G', mode='ionian',     bars=B(12), prog=P_ION8,  motif=A_DEG)
m.add('waltz',    bpm=150, root='C', mode='mixolydian', bars=B(12), prog=[1,4,5,1], motif=THEME_C)

# ============================================================================
# V.  DRUMS OF THE RIVER  — hand-percussion jam, marimba, polyrhythm, key shifts.
# ============================================================================
# chant interleaved between the jams + widened tempos so the block isn't a flat plateau
m.add('perc_jam', bpm=108, root='A', mode='dorian',     bars=B(12), prog=P_DOR,  motif=[1,5,8,5,3,5,8,10])
m.add('chant',    bpm=96,  root='D', mode='aeolian',    bars=B(12), prog=P_MIN8,  motif=[1,1,5,1,3,1])
m.add('perc_jam', bpm=124, root='D', mode='dorian',     bars=B(12), prog=P_DOR,  motif=[1,8,5,8,3,8,5,10])
m.add('perc_jam', bpm=134, root='E', mode='phrygian',   bars=B(12), prog=[1,2,1,7], motif=[1,2,5,8,5,2,1,7])

# ============================================================================
# VI.  THE CHASE  — restless interlocking guitars, rock-prog drive.
# ============================================================================
m.add('chase',    bpm=140, root='E', mode='dorian',     bars=B(12), prog=P_DOR8,  motif=A_DEG)
m.add('driving',  bpm=140, root='A', mode='mixolydian', bars=B(14), prog=P_MIX8,  motif=A_DEG)
m.add('chase',    bpm=146, root='D', mode='dorian',     bars=B(12), prog=P_DOR8,  motif=THEME_C)
m.add('transition',bpm=128,root='D', mode='aeolian',    bars=B(4),  prog=P_AEOL)

# ============================================================================
# VII.  CHANT & BELLS  — hypnotic, modal, building then opening out.
# ============================================================================
m.add('chant',    bpm=104, root='A', mode='aeolian',    bars=B(14), prog=P_MIN8,  motif=[1,1,3,1,5,1])
m.add('bells',    bpm=100, root='C', mode='ionian',     bars=B(10), prog=P_ION,  lvl=(0.4,0.6), motif=THEME_B)
m.add('ambient',  bpm=76,  root='F', mode='ionian',     bars=B(8),  prog=[1,5,6,4], lvl=(0.18,0.36))

# ============================================================================
# VIII.  PASTORAL REPRISE  — the opening returns, transformed, in a new light.
# ============================================================================
m.add('pastoral', bpm=96,  root='F', mode='ionian',     bars=B(12), prog=P_ION,  motif=A_DEG)
m.add('theme',    bpm=100, root='F', mode='ionian',     bars=B(14), prog=P_ION,  theme=THEME_A, lead=folk.FIDDLE)
m.add('folk_dance',bpm=128,root='Bb',mode='mixolydian', bars=B(12), prog=P_MIX8,  motif=THEME_C, jiggy=True)

# ============================================================================
# IX.  STORM  — the biggest energy: driving prog, tempo pushing, modulating hard.
# ============================================================================
m.add('driving',  bpm=144, root='D', mode='dorian',     bars=B(14), prog=P_DOR8,  motif=A_DEG)
m.add('driving',  bpm=150, root='G', mode='dorian',     bars=B(14), prog=P_DOR8,  motif=THEME_C)
m.add('chase',    bpm=156, root='A', mode='mixolydian', bars=B(12), prog=P_MIX8,  motif=A_DEG)
m.add('anthem',   bpm=140, root='D', mode='mixolydian', bars=B(10), prog=P_MIX8,  motif=A_DEG)

# ---- THE FALSE ENDING  — a grand cadence, a beat of silence... then it bursts back.
m.add('transition',bpm=120,root='D', mode='ionian',     bars=B(4),  prog=[5,5,1,1], lvl=(0.85,0.98))
m.crash_cadence(root='D', mode='ionian', bpm=120, beats=5)   # one grand chord, ringing...
m.gap(3.2)                                                   # ...then real silence
m.add('folk_dance',bpm=150,root='D', mode='mixolydian', bars=B(8),  prog=P_MIX8, motif=THEME_C, jiggy=False)

# ============================================================================
# X.  HYMN  — the main theme, full-hearted: choir, strings, bells, the summit.
# ============================================================================
m.morse("AMAROK", bpm=120, drone=('D','ionian'))            # tapped under a held D, into the Hymn
m.add('theme',    bpm=92,  root='D', mode='ionian',     bars=B(18), prog=P_FOLK, theme=THEME_A, lead=folk.FLUTE, full=True)
m.add('anthem',   bpm=96,  root='D', mode='mixolydian',  bars=B(14), prog=P_ION8,  motif=A_DEG)
m.add('bells',    bpm=92,  root='D', mode='ionian',     bars=B(10), prog=P_ION,  lvl=(0.5,0.66), motif=THEME_B)

# ============================================================================
# XI.  HOMEWARD  — the river widens to the sea: wind down to a last, luminous chord.
# ============================================================================
m.add('pastoral', bpm=84,  root='G', mode='mixolydian',  bars=B(12), prog=P_ION,  motif=A_DEG)
m.add('hush',     bpm=76,  root='B', mode='aeolian',     bars=B(10), prog=[1,4,1,5], motif=A_DEG)
m.add('ambient',  bpm=66,  root='D', mode='ionian',     bars=B(10), prog=[1,6,4,5], lvl=(0.22,0.08))
m.final_chord(root='D', mode='ionian', bpm=60, length_beats=14)

# ---------------------------------------------------------------------------
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'midi', 'Riverwake.mid')
m.write(OUT, title='Riverwake', text='a 60-minute river, after Amarok')

mm = int(m.seconds // 60)
print(f"RIVERWAKE: {mm}:{m.seconds-mm*60:05.2f}  ({m.seconds:.0f}s)   {len(m.log)} sections   SCALE={SCALE}")
r = folk.analyze(OUT)
print(f"notes={r['n_notes']}  channels={len(r['channels'])}  file={os.path.getsize(OUT)} bytes")
if __name__ == '__main__' and os.environ.get('SHOWLOG'):
    for row in m.log:
        print("  ", row)
