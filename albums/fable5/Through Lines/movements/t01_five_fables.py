"""t01_five_fables — Track 1 "Five Fables": the opener of *Through Lines*.

Disc 1, 'Lines of Descent'.  HLD section 3, T1.  A self-portrait of
Claude Fable 5: five instrumental characters each state the FABLE cell
(F-A-Bb-rest-E, material.FABLE_CELL) in a different idiom, then all five
interleave into one fabric — many voices, one model — and collapse to a
single unison F, the album's first pitch.

Movements (the five idioms, then the combination):
    i.   Baroque     [0, 72)    3/4 @ 96 — two flutes, canon at the fifth
    ii.  Romantic    [72, 140)  4/4 rubato — strings, wide dynamics
    iii. Jazz        [140, 236) 4/4 @ 120 — guitar over swung brushes
    iv.  Electronic  [236, 316) 4/4 @ 126 — quantized saw, CC74 sweeps
    v.   Voice       [316, 348) 4/4 @ 58 — choir on CC70 vowel morphs
    vi.  Finale      [348, 460) 4/4 @ 112 — 5-voice counterpoint -> unison F

Every headline claim is a falsifiable oracle, written BEFORE the music
(the repo method); the track is composed to pass:

 * fable_cell_fidelity — EVERY statement of the FABLE cell (31 of them,
   declared in CELL_PLAN and played only via material.play_cell) matches
   onsets/durations/pitches recomputed from material.FABLE_CELL
   (transposition- and stretch-aware, never re-typed); the silent L is
   verified empty where the channel is otherwise free; every movement
   states the cell; in the finale all five voices state it.
 * baroque_canon — movement i is a strict canon at the fifth below:
   every dux event in [0, 48) recurs on the comes flute at +3 beats,
   -7 semitones (expected list recomputed from the shared data).
 * romantic_rubato_dynamics — movement ii has a genuinely rubato tempo
   map (>= 6 tempo events spanning >= 16 bpm) and wide dynamics on the
   strings (velocity span >= 40, peak >= 98, floor <= 34 — the pp end is
   a scored near-silence per the contract).
 * jazz_swing — movement iii sits on a 2:1 swing grid: every onset on
   guitar/bass/drums falls on {beat, +1/3, +2/3} (never on a straight
   offbeat), >= 24 swung skip-notes, and the ride's long/short pair
   ratio averages 2:1 (each pair within [1.55, 2.55], mean in
   [1.8, 2.2]).  The jazz cell statements are 2x augmentations, so the
   head lands on downbeats inside the swung texture.
 * kit_select — ch9 program 40 (brush kit) at beat 0 and program 1
   (v2 kit) at the electronic seam, exactly as PART.PROGRAM_CHANGES.
 * electronic_grid — every note-on in movement iv is EXACTLY on the
   1/16 grid (tick % 120 == 0, jt=0 everywhere); outside iv at least
   40% of onsets are off-grid (the seeded humanisation everywhere
   else); the saw authors CC74 filter sweeps (range >= 60, >= 2 rising
   sweeps of span >= 40).
 * choir_vowels — movement v authors CC70 vowel morphs on the choir:
   full mm->ah range (min <= 5, max >= 80) with >= 2 direction
   reversals.
 * finale_downbeat_consonance — on every downbeat of the finale the
   sounding pitches across the five voices are pairwise consonant
   (interval classes {0,3,4,7,8,9}; ic 5 only between upper voices),
   >= 4 voices sound on every downbeat and all 5 on >= 24 of 28.
 * unison_f_ending — the track opens on pitch-class F and its last
   sounding sonority is a single pitch class F across >= 4 channels
   (all five voices), struck together and fading under a ritardando.

audio_checks (run by analyze.py once audio/01 - Five Fables.wav
exists): the electronic movement out-powers the solo-canon and choir
movements by >= 3 dB; the unison tail fades >= 5 dB below the finale
body.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 1
TITLE = 'Five Fables'
FILE = '01 - Five Fables.mid'
SEED = 20260901

COMMENT = ("Track 1, the self-portrait: five characters - baroque canon, "
           "romantic strings, brush-kit jazz, quantized electronics, choir "
           "vowels - each state F-A-Bb-(rest)-E, then combine in 5-voice "
           "counterpoint and collapse to a unison F.")

# ---------------------------------------------------------------------------
# Channels and section grid
# ---------------------------------------------------------------------------

CH_FLUTE = 0      # flute dux (GM 73) — baroque voice, finale voice 1
CH_STR = 1        # strings (GM 48) — romantic voice, finale bass
CH_GTR = 2        # jazz guitar (GM 26) — jazz voice, transient, panned
CH_SAW = 3        # saw lead (GM 81) — electronic voice
CH_CHOIR = 4      # choir (GM 52) — vowel voice
CH_BASS = 5       # upright bass (GM 32) — jazz walking bass
CH_SYNBASS = 6    # synth bass (GM 38) — electronic four-on-floor bass
CH_FLUTE2 = 7     # flute comes (GM 73) — the canon's answer

S1, S2, S3, S4, S5, S6, END = 0.0, 72.0, 140.0, 236.0, 316.0, 348.0, 460.0
UNISON_T0 = 452.0             # all five voices strike F here
_TICK = 1.0 / en.PPQ

# ---------------------------------------------------------------------------
# The FABLE cell plan — every statement in the track, declared as data.
# Builders play these ONLY via material.play_cell; the fidelity oracle
# recomputes each statement's notes from material.FABLE_CELL.
# (channel, t0, root, stretch, vel, vel_end, jt, jv, check_silent_L)
# ---------------------------------------------------------------------------

CELL_PLAN: tuple[tuple, ...] = (
    # i. Baroque — dux, and the comes' answers a fifth below, +3 beats
    (CH_FLUTE, 0.0, 77, 1.0, 76, None, 3, 3, True),
    (CH_FLUTE, 12.0, 72, 1.0, 74, None, 3, 3, True),
    (CH_FLUTE, 24.0, 77, 1.0, 80, None, 3, 3, True),
    (CH_FLUTE, 36.0, 82, 1.0, 82, None, 3, 3, True),
    (CH_FLUTE2, 3.0, 70, 1.0, 70, None, 3, 3, True),
    (CH_FLUTE2, 15.0, 65, 1.0, 68, None, 3, 3, True),
    (CH_FLUTE2, 27.0, 70, 1.0, 74, None, 3, 3, True),
    (CH_FLUTE2, 39.0, 75, 1.0, 76, None, 3, 3, True),
    (CH_FLUTE, 60.0, 77, 1.0, 78, None, 3, 3, True),   # closing duet
    (CH_FLUTE2, 60.0, 65, 1.0, 72, None, 3, 3, True),
    # ii. Romantic — quiet first statement, fortissimo climax statement
    (CH_STR, 80.0, 65, 1.0, 62, None, 4, 3, True),
    (CH_STR, 112.0, 77, 1.0, 104, None, 4, 3, True),
    # iii. Jazz — the head: 2x augmentation, so it lands on downbeats
    (CH_GTR, 140.0, 65, 2.0, 80, None, 2, 3, True),
    (CH_GTR, 156.0, 70, 2.0, 78, None, 2, 3, True),
    (CH_GTR, 188.0, 65, 2.0, 82, None, 2, 3, True),
    (CH_GTR, 220.0, 65, 2.0, 84, None, 2, 3, True),
    # iv. Electronic — the hook, hard-quantized (jt=0)
    (CH_SAW, 244.0, 77, 1.0, 92, None, 0, 0, True),
    (CH_SAW, 252.0, 77, 1.0, 94, None, 0, 0, True),
    (CH_SAW, 268.0, 77, 1.0, 96, None, 0, 0, True),
    (CH_SAW, 284.0, 72, 1.0, 94, None, 0, 0, True),
    (CH_SAW, 300.0, 77, 1.0, 98, None, 0, 0, True),
    # v. Voice — soprano statements over the vowel pads (pads share the
    # channel, so the silent-L emptiness is not asserted here)
    (CH_CHOIR, 320.0, 65, 2.0, 60, None, 3, 2, False),
    (CH_CHOIR, 336.0, 60, 2.0, 64, None, 3, 2, False),
    # vi. Finale — all FIVE voices state the cell inside the counterpoint
    (CH_FLUTE, 380.0, 77, 1.0, 84, None, 2, 2, True),
    (CH_FLUTE, 428.0, 77, 1.0, 86, None, 2, 2, True),
    (CH_SAW, 392.0, 77, 1.0, 88, None, 2, 2, True),
    (CH_SAW, 400.0, 72, 1.0, 88, None, 2, 2, True),
    (CH_SAW, 412.0, 70, 1.0, 90, None, 2, 2, True),
    (CH_GTR, 416.0, 65, 1.0, 82, None, 2, 2, True),
    (CH_STR, 436.0, 53, 1.0, 78, None, 2, 2, True),
    (CH_CHOIR, 444.0, 65, 2.0, 62, 50, 2, 2, True),   # E resolves at 452
)


def _play_cells(sc: en.Score, lo: float, hi: float) -> None:
    """Play every planned statement whose t0 lies in [lo, hi)."""
    for ch, t0, root, stretch, vel, vel_end, jt, jv, _l in CELL_PLAN:
        if lo <= t0 < hi:
            material.play_cell(sc, ch, t0, root, stretch=stretch, vel=vel,
                               vel_end=vel_end, jt=jt, jv=jv)


# ---------------------------------------------------------------------------
# i. Baroque data — the dux line (free notes between the cells).  The
# comes plays the SAME events +3 beats, -7 semitones (canon at the fifth
# below); the canon oracle recomputes the expected answer from this data.
# (t, dur, pitch, vel), section-absolute beats.
# ---------------------------------------------------------------------------

DUX_LINE: tuple[tuple[float, float, int, int], ...] = (
    # phrase 1 continuation [4, 12)
    (4.0, 0.5, 86, 70), (4.5, 0.5, 84, 68), (5.0, 0.5, 82, 67),
    (5.5, 0.5, 81, 66), (6.0, 1.0, 79, 68), (7.0, 0.5, 77, 64),
    (7.5, 0.5, 81, 68), (8.0, 1.5, 84, 74), (9.5, 0.5, 82, 70),
    (10.0, 0.5, 81, 68), (10.5, 0.5, 79, 66), (11.0, 1.0, 77, 70),
    # phrase 2 continuation [16, 24) — the B natural echoes the answer
    (16.0, 0.5, 84, 72), (16.5, 0.5, 83, 70), (17.0, 0.5, 81, 68),
    (17.5, 0.5, 79, 66), (18.0, 1.0, 77, 68), (19.0, 0.5, 76, 64),
    (19.5, 0.5, 79, 66), (20.0, 1.5, 77, 72), (21.5, 0.5, 74, 66),
    (22.0, 0.5, 76, 68), (22.5, 0.5, 74, 66), (23.0, 1.0, 72, 70),
    # phrase 3 continuation [28, 36)
    (28.0, 0.5, 89, 76), (28.5, 0.5, 88, 74), (29.0, 0.5, 86, 72),
    (29.5, 0.5, 84, 70), (30.0, 1.0, 82, 72), (31.0, 0.5, 81, 68),
    (31.5, 0.5, 84, 72), (32.0, 1.5, 86, 78), (33.5, 0.5, 84, 74),
    (34.0, 0.5, 82, 72), (34.5, 0.5, 81, 70), (35.0, 1.0, 79, 72),
    # phrase 4 continuation [40, 48)
    (40.0, 0.5, 91, 78), (40.5, 0.5, 89, 76), (41.0, 0.5, 88, 74),
    (41.5, 0.5, 86, 72), (42.0, 1.0, 84, 74), (43.0, 0.5, 82, 70),
    (43.5, 0.5, 84, 72), (44.0, 1.5, 81, 76), (45.5, 0.5, 79, 72),
    (46.0, 0.5, 77, 70), (46.5, 0.5, 76, 68), (47.0, 1.0, 77, 72),
)

# The cells the dux states inside the strict-canon span [0, 48).
DUX_CANON_CELLS: tuple[tuple[float, int], ...] = (
    (0.0, 77), (12.0, 72), (24.0, 77), (36.0, 82))

CANON_DELAY, CANON_SHIFT = 3.0, -7

# Closing duet [48, 72) — the canon relaxes into parallel work and both
# flutes cadence on a held F octave (E->F resolutions in both voices).
DUX_CLOSE: tuple[tuple[float, float, int, int], ...] = (
    (48.0, 1.0, 81, 74), (49.0, 0.5, 82, 72), (49.5, 0.5, 84, 74),
    (50.0, 1.0, 86, 78), (51.0, 1.0, 84, 76), (52.0, 0.5, 82, 72),
    (52.5, 0.5, 81, 70), (53.0, 1.0, 79, 72), (54.0, 1.5, 82, 76),
    (55.5, 0.5, 81, 70), (56.0, 1.0, 79, 72), (57.0, 1.5, 77, 74),
    (58.5, 0.5, 79, 70), (59.0, 1.0, 81, 74),
    (64.0, 7.9, 89, 66),                       # E6 -> F6, held to the seam
)
COMES_CLOSE: tuple[tuple[float, float, int, int], ...] = (
    (52.0, 1.0, 72, 66), (53.0, 1.0, 74, 68), (54.0, 1.5, 77, 72),
    (55.5, 0.5, 76, 66), (56.0, 1.0, 74, 68), (57.0, 1.5, 72, 70),
    (58.5, 0.5, 74, 66), (59.0, 1.0, 76, 70),
    (64.0, 7.9, 77, 62),                       # E5 -> F5 under the dux
)

# ---------------------------------------------------------------------------
# ii. Romantic data — D-minor pads (two dynamic waves) and a melody with
# the widest velocity span of the piece.
# ---------------------------------------------------------------------------

_DM, _BB, _GM, _A, _F, _C = ([2, 5, 9], [10, 2, 5], [7, 10, 2],
                             [9, 1, 4], [5, 9, 0], [0, 4, 7])
PADS_II_A = [_DM, _BB, _DM, _GM, _A, _DM, _F, _BB, _GM, _C]   # [72, 112)
PADS_II_B = [_F, _BB, _DM, _GM, _A, _DM]                      # [112, 136)

MEL_II: tuple[tuple[float, float, int, int], ...] = (
    (84.0, 2.0, 77, 64), (86.0, 1.0, 76, 62), (87.0, 1.0, 74, 62),
    (88.0, 2.0, 73, 66), (90.0, 1.0, 74, 64), (91.0, 1.0, 76, 66),
    (92.0, 3.0, 77, 70), (95.0, 1.0, 74, 66),
    (96.0, 2.0, 81, 74), (98.0, 1.0, 79, 72), (99.0, 1.0, 77, 70),
    (100.0, 2.0, 82, 78), (102.0, 1.0, 81, 76), (103.0, 1.0, 79, 74),
    (104.0, 1.5, 79, 78), (105.5, 0.5, 81, 80), (106.0, 1.0, 82, 84),
    (107.0, 1.0, 84, 88),
    (108.0, 2.0, 84, 90), (110.0, 1.0, 86, 94), (111.0, 1.0, 88, 98),
    # (the ff cell statement at 112 lives in CELL_PLAN)
    (116.0, 2.0, 86, 88), (118.0, 1.0, 84, 84), (119.0, 1.0, 82, 80),
    (120.0, 2.0, 81, 76), (122.0, 1.0, 79, 72), (123.0, 1.0, 77, 68),
    (124.0, 2.0, 79, 64), (126.0, 1.0, 77, 60), (127.0, 1.0, 76, 56),
    (128.0, 2.0, 73, 52), (130.0, 1.0, 74, 48), (131.0, 1.0, 76, 44),
    (132.0, 4.0, 77, 36),
    (136.0, 3.5, 74, 28),                      # the scored pp sigh
)

# ---------------------------------------------------------------------------
# iii. Jazz data — a 12-bar form, twice.  Chorus 1: the head (augmented
# cells) with swung fills; chorus 2: statements + comping.
# ---------------------------------------------------------------------------

JAZZ_FORM = ("F", "Bb", "F", "F", "Bb", "Bb", "F", "F", "Gm", "C", "F", "C")
JAZZ_ROOT = {"F": 41, "Bb": 46, "Gm": 43, "C": 48}
JAZZ_THIRD = {"F": 4, "Bb": 4, "Gm": 3, "C": 4}
JAZZ_SHELL = {"F": [60, 65, 69], "Bb": [58, 62, 65],
              "Gm": [58, 62, 67], "C": [60, 64, 67]}
COMP_BARS = (196.0, 200.0, 204.0, 208.0, 212.0, 216.0, 228.0, 232.0)

_TH = 2.0 / 3.0   # the swung skip: 2/3 of a beat (2:1 triplet swing)

GTR_FILLS: tuple[tuple[float, float, int, int], ...] = (
    # bars 3-4 [148, 156)
    (148.0, 0.6, 69, 70), (148 + _TH, 0.3, 70, 62), (149.0, 0.6, 72, 72),
    (149 + _TH, 0.3, 74, 64), (150.0, 1.0, 77, 76), (151.0, 0.6, 76, 70),
    (151 + _TH, 0.3, 74, 62), (152.0, 1.0, 72, 72), (153.0, 0.6, 70, 68),
    (153 + _TH, 0.3, 69, 60), (154.0, 2.0, 65, 70),
    # bars 7-8 [164, 172)
    (164.0, 0.6, 77, 74), (164 + _TH, 0.3, 79, 66), (165.0, 0.6, 81, 76),
    (165 + _TH, 0.3, 82, 68), (166.0, 1.0, 84, 80), (167.0, 0.6, 82, 72),
    (167 + _TH, 0.3, 81, 64), (168.0, 0.6, 79, 72), (168 + _TH, 0.3, 77, 64),
    (169.0, 0.6, 76, 70), (169 + _TH, 0.3, 74, 62), (170.0, 2.0, 72, 72),
    # bars 9-12 [172, 188): the turnaround
    (172.0, 0.6, 70, 70), (172 + _TH, 0.3, 72, 62), (173.0, 0.6, 74, 72),
    (173 + _TH, 0.3, 72, 64), (174.0, 1.0, 70, 72), (175.0, 1.0, 67, 66),
    (176.0, 0.6, 64, 68), (176 + _TH, 0.3, 67, 62), (177.0, 0.6, 71, 70),
    (177 + _TH, 0.3, 72, 64), (178.0, 2.0, 74, 74),
    (180.0, 0.6, 77, 76), (180 + _TH, 0.3, 76, 68), (181.0, 0.6, 74, 72),
    (181 + _TH, 0.3, 72, 66), (182.0, 1.0, 69, 70), (183.0, 1.0, 70, 68),
    (184.0, 1.0, 71, 70), (185.0, 0.6, 72, 68), (185 + _TH, 0.3, 74, 66),
    (186.0, 2.0, 76, 74),
)

# ---------------------------------------------------------------------------
# v. Voice data — hand-voiced pads kept clear of the soprano cells.
# ---------------------------------------------------------------------------

PADS_V: tuple[tuple[float, tuple[int, ...], int], ...] = (
    (316.0, (53, 57, 60), 52), (320.0, (53, 57, 60), 56),
    (324.0, (50, 58, 62), 58), (328.0, (50, 58, 62), 60),
    (332.0, (50, 57, 62), 62), (336.0, (48, 52, 55), 58),
    (340.0, (53, 57, 60), 56), (344.0, (41, 53, 60), 52),
)

# ---------------------------------------------------------------------------
# vi. Finale data — 26 planned bars (then the unison holds two more).
# (chord pcs, strings root | None, guitar arp | None, saw pair | None);
# strings always take the chord ROOT, so every downbeat sonority is a
# root-position triad — consonant by construction.
# ---------------------------------------------------------------------------

_AM = [9, 0, 4]
_GF = [65, 69, 72, 77]
_GBB = [58, 62, 65, 70]
_GDM = [62, 65, 69, 74]
_GGM = [58, 62, 67, 70]
_GC = [60, 64, 67, 72]
_GAM = [57, 60, 64, 69]

FINALE_BARS: tuple[tuple, ...] = (
    (_F, 41, _GF, (72, 77)),        # 0
    (_F, 53, _GF, (77, 84)),        # 1
    (_BB, 46, _GBB, (74, 82)),      # 2
    (_F, 41, _GF, (77, 81)),        # 3
    (_DM, 50, _GDM, (74, 81)),      # 4
    (_BB, 46, _GBB, (70, 77)),      # 5
    (_GM, 43, _GGM, (74, 79)),      # 6
    (_C, 48, _GC, (76, 79)),        # 7
    (_F, 53, _GF, (77, 84)),        # 8  flute cell @380
    (_DM, 50, _GDM, (74, 86)),      # 9
    (_BB, 46, _GBB, (82, 74)),      # 10
    (_F, 41, _GF, None),            # 11 saw cell @392
    (_GM, 43, _GGM, (79, 74)),      # 12
    (_C, 48, _GC, None),            # 13 saw cell @400
    (_AM, 45, _GAM, (76, 81)),      # 14
    (_DM, 50, _GDM, (77, 74)),      # 15
    (_BB, 46, _GBB, None),          # 16 saw cell @412
    (_F, 53, None, (77, 81)),       # 17 guitar cell @416
    (_GM, 43, _GGM, (74, 70)),      # 18
    (_C, 48, _GC, (76, 84)),        # 19
    (_F, 41, _GF, (77, 72)),        # 20 flute cell @428
    (_BB, 46, _GBB, (74, 77)),      # 21
    (_F, None, _GF, (72, 77)),      # 22 strings cell @436
    (_C, 48, _GC, (79, 76)),        # 23
    (_F, 41, _GF, (77, 84)),        # 24 collapse; choir cell @444
    (_F, 41, _GF, None),            # 25 saw holds C6; choir cell's E->F
)
FLUTE_CELL_BARS = {8, 20}
FLUTE_EXPLICIT_BARS = {24, 25}
_F_SCALE = [p for p in range(72, 97) if p % 12 in (5, 7, 9, 10, 0, 2, 4)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("i. Baroque: Flute Canon at the Fifth", S1, S2),
        ("ii. Romantic: Strings Rubato", S2, S3),
        ("iii. Jazz: Brushes and Guitar", S3, S4),
        ("iv. Electronic: The Grid", S4, S5),
        ("v. Voice: Choir Vowels", S5, S6),
        ("vi. Five Together: Unison F", S6, END),
    ],
    tempo_map=[(0.0, 96.0),
               # movement ii — the rubato map (an oracle counts these)
               (72.0, 63.0), (80.0, 70.0), (88.0, 58.0), (96.0, 72.0),
               (104.0, 63.0), (112.0, 76.0), (122.0, 60.0), (130.0, 66.0),
               (136.0, 52.0),
               (140.0, 120.0), (236.0, 126.0), (316.0, 58.0),
               (348.0, 112.0), (444.0, 100.0), (452.0, 88.0)],
    time_signatures=[(0.0, 3, 4), (72.0, 4, 4)],
    keysigs=[(0.0, -1, 0), (72.0, -1, 1), (140.0, -1, 0)],
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_FLUTE, "flute (dux)", 73, 96, 64, 58),
        (CH_STR, "strings", 48, 100, 64, 60),
        (CH_GTR, "jazz guitar", 26, 98, 54, 45),
        (CH_SAW, "saw lead", 81, 92, 64, 40),
        (CH_CHOIR, "choir", 52, 96, 64, 62),
        (CH_BASS, "upright bass", 32, 100, 64, 30),
        (CH_SYNBASS, "synth bass", 38, 100, 64, 25),
        (CH_FLUTE2, "flute (comes)", 73, 90, 64, 58),
        (9, "drums", 0, 100, 64, 40),
    ],
    # ch9 kit select: 40 = brush kit from the top (movement iii), 1 = v2
    # kit at the electronic seam.  (sc.channel skips ch9 programs, so
    # these MUST be scheduled here.)
    program_changes=[(9, 0.0, 40), (9, 236.0, 1)],
    extra_markers=[
        (60.0, "canon closes on held F"),
        (112.0, "romantic climax"),
        (444.0, "the five collapse"),
        (452.0, "unison F: one voice"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {26, 32, 38, 48, 52, 73, 81}
CENTERED_CHANNELS: set[int] = {CH_FLUTE, CH_STR, CH_SAW, CH_CHOIR,
                               CH_BASS, CH_SYNBASS, CH_FLUTE2, 9}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_FLUTE: (60, 96),
    CH_STR: (36, 92),
    CH_GTR: (52, 88),
    CH_SAW: (60, 96),
    CH_CHOIR: (41, 80),
    CH_BASS: (36, 62),
    CH_SYNBASS: (36, 58),
    CH_FLUTE2: (55, 90),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (284.0, 296.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------

def _m1_baroque(sc: en.Score) -> None:
    """[0, 72) Two flutes, canon at the fifth below (comes = dux +3
    beats, -7 semitones over [0, 48)); then a free closing duet that
    cadences on a held F octave."""
    _play_cells(sc, S1, S2)
    for t, du, p, v in DUX_LINE:
        sc.note(CH_FLUTE, p, t, du, v, jt=3, jv=3)
        sc.note(CH_FLUTE2, p + CANON_SHIFT, t + CANON_DELAY, du, v - 6,
                jt=3, jv=3)
    for t, du, p, v in DUX_CLOSE:
        sc.note(CH_FLUTE, p, t, du, v, jt=3, jv=3)
    for t, du, p, v in COMES_CLOSE:
        sc.note(CH_FLUTE2, p, t, du, v, jt=3, jv=3)


def _m2_romantic(sc: en.Score) -> None:
    """[72, 140) Strings alone: two voice-led pad waves (pp -> ff -> pp)
    under a melody spanning the widest dynamics of the piece, the tempo
    map breathing rubato underneath."""
    en.cc_curve(sc, CH_STR, 11, [(72.0, 44), (96.0, 62), (111.0, 80),
                                 (116.0, 74), (126.0, 56), (136.0, 44),
                                 (139.5, 38)], step=1.0)
    en.cc_curve(sc, CH_STR, 1, [(72.0, 10), (100.0, 40), (112.0, 70),
                                (126.0, 40), (139.0, 12)], step=2.0)
    en.pad_block(sc, CH_STR, 72.0, PADS_II_A, span=4.0, size=4,
                 lo=50, hi=64, vel=34, vel_end=86, legato=0.2)
    en.pad_block(sc, CH_STR, 112.0, PADS_II_B, span=4.0, size=4,
                 lo=50, hi=64, vel=92, vel_end=38, legato=0.2)
    for p, v in ((50, 30), (57, 28), (62, 26)):        # dying Dm hold
        sc.note(CH_STR, p, 136.0, 3.9, v, jt=4, jv=2)
    _play_cells(sc, S2, S3)
    for t, du, p, v in MEL_II:
        sc.note(CH_STR, p, t, du, v, jt=4, jv=3)


def _m3_jazz(sc: en.Score) -> None:
    """[140, 236) Brush-kit swing at 2:1: ride pattern with swung skips,
    feathered kick, walking upright bass with approach notes, guitar
    head (augmented cells) + swung fills, then comping."""
    _play_cells(sc, S3, S4)
    for t, du, p, v in GTR_FILLS:
        sc.note(CH_GTR, p, t, du, v, jt=2, jv=3)
    for t in COMP_BARS:                                 # chorus-2 comping
        name = JAZZ_FORM[int((t - S3) // 4) % 12]
        for p in JAZZ_SHELL[name]:
            sc.note(CH_GTR, p, t + 1.0, 0.6, 60, jt=2, jv=3)
            sc.note(CH_GTR, p, t + 2 + _TH, 0.4, 56, jt=2, jv=3)
    bars = list(JAZZ_FORM) * 2
    for i, name in enumerate(bars):
        t = S3 + 4.0 * i
        root = JAZZ_ROOT[name]
        nxt = JAZZ_ROOT[bars[(i + 1) % len(bars)]]
        approach = nxt - 1 if i % 2 == 0 else nxt + 1
        for k, p in enumerate((root, root + JAZZ_THIRD[name],
                               root + 7, approach)):
            sc.note(CH_BASS, p, t + k, 0.92, 74, jt=2, jv=3)
        # brushes: ride with swung skips, pedal hat, feathered kick, tap
        for off, v in ((0.0, 66), (1.0, 62), (1 + _TH, 52),
                       (2.0, 66), (3.0, 62), (3 + _TH, 52)):
            sc.hit(51, t + off, v, jt=2, jv=3)
        sc.hit(44, t + 1.0, 48, jt=2, jv=3)
        sc.hit(44, t + 3.0, 48, jt=2, jv=3)
        sc.hit(36, t, 32, jt=2, jv=3)
        sc.hit(36, t + 2.0, 32, jt=2, jv=3)
        sc.hit(38, t + 2 + _TH, 36, jt=2, jv=3)


def _m4_electronic(sc: en.Score) -> None:
    """[236, 316) The grid: jt=0 everywhere, every onset a 1/16
    multiple.  Four-on-floor v2 kit, octave-pumping synth bass, the saw
    hook (quantized cells) between sixteenth arps, CC74 filter sweeps."""
    en.cc_curve(sc, CH_SAW, 74, [(236.0, 18), (244.0, 96), (252.0, 30),
                                 (268.0, 102), (284.0, 34), (300.0, 106),
                                 (312.0, 40), (315.5, 70)], step=0.5)
    sc.cc(CH_SAW, 11, 96, 236.0)
    opens = {251.5, 267.5, 283.5, 299.5}
    for b in range(236, 316):
        sc.hit(36, float(b), 104, jt=0, jv=0)
        t = b + 0.5
        if t in opens:
            sc.hit(46, t, 72, jt=0, jv=0)
        else:
            sc.hit(42, t, 64, jt=0, jv=0)
        sc.note(CH_SYNBASS, 41, float(b), 0.4, 96, jt=0, jv=0)
        sc.note(CH_SYNBASS, 53, b + 0.5, 0.4, 88, jt=0, jv=0)
        if 240 <= b < 312 and b % 2 == 1:
            sc.hit(39, float(b), 82, jt=0, jv=0)
    for b in range(284, 312):
        sc.hit(42, b + 0.25, 46, jt=0, jv=0)
        sc.hit(42, b + 0.75, 46, jt=0, jv=0)
    sc.note(CH_SAW, 77, 236.0, 7.75, 84, jt=0, jv=0)    # the riser hold
    _play_cells(sc, S4, S5)
    arps = ((248.0, 0.25, 16, (77, 81, 84, 89), 0.22, 86),
            (256.0, 0.5, 24, (77, 84, 81, 89), 0.45, 84),
            (272.0, 0.5, 24, (89, 84, 81, 77), 0.45, 86),
            (288.0, 0.25, 48, (77, 81, 84, 89), 0.22, 88),
            (304.0, 0.25, 32, (77, 84, 89, 93), 0.22, 92))
    for t0, step, count, seq, du, v in arps:
        for k in range(count):
            sc.note(CH_SAW, seq[k % 4], t0 + k * step, du, v, jt=0, jv=0)
    sc.note(CH_SAW, 77, 312.0, 3.75, 80, jt=0, jv=0)    # fade-out hold


def _m5_voice(sc: en.Score) -> None:
    """[316, 348) Choir alone: hand-voiced pads under two soprano cell
    statements, CC70 morphing mm -> oo -> ah and back — the voice that
    sings without words."""
    en.vowel_curve(sc, CH_CHOIR, [(316.0, 0), (320.0, 20), (324.0, 45),
                                  (330.0, 85), (336.0, 45), (342.0, 88),
                                  (347.5, 15)], step=0.5)
    en.cc_curve(sc, CH_CHOIR, 11, [(316.0, 46), (324.0, 58), (332.0, 66),
                                   (340.0, 60), (347.5, 48)], step=1.0)
    for t, pitches, v in PADS_V:
        for p in pitches:
            sc.note(CH_CHOIR, p, t, 3.9, v, jt=3, jv=2)
    _play_cells(sc, S5, S6)


def _m6_finale(sc: en.Score) -> None:
    """[348, 460) All five voices in counterpoint over root-position
    triads (every downbeat sonority consonant by construction), each
    voice stating the cell once; bars 25-26 collapse the texture and the
    choir's slow cell resolves E->F straight into the unison F at 452,
    held and fading under the ritardando."""
    for ch in (CH_FLUTE, CH_STR, CH_GTR, CH_SAW, CH_CHOIR):
        sc.cc(ch, 11, 86, S6)
    sc.cc(CH_SAW, 74, 84, S6)
    en.vowel_curve(sc, CH_CHOIR, [(348.0, 45), (430.0, 80), (444.0, 60),
                                  (452.0, 30), (459.0, 15)], step=2.0)
    # legato=0.0: a chord tone must END at the barline, or its tail would
    # sound into the next downbeat and muddy the consonance oracle
    en.pad_block(sc, CH_CHOIR, S6, [b[0] for b in FINALE_BARS[:24]],
                 span=4.0, size=3, lo=55, hi=72, vel=56, vel_end=68,
                 legato=0.0)
    for i, (_pcs, s_root, g_arp, saw_pair) in enumerate(FINALE_BARS):
        t = S6 + 4.0 * i
        if s_root is not None:
            v = min(74, 54 + i) if i < 24 else (62 if i == 24 else 58)
            sc.note(CH_STR, s_root, t, 3.9, v, jt=2, jv=2)
        if g_arp is not None:
            for k in range(8):
                sc.note(CH_GTR, g_arp[k % 4], t + 0.5 * k, 0.45,
                        66 if k == 0 else 64, jt=2, jv=2)
        if saw_pair is not None:
            v = min(84, 72 + i // 2)
            sc.note(CH_SAW, saw_pair[0], t, 1.9, v, jt=2, jv=2)
            sc.note(CH_SAW, saw_pair[1], t + 2.0, 1.9, v - 4, jt=2, jv=2)
    sc.note(CH_SAW, 84, 448.0, 3.9, 78, jt=2, jv=2)     # bar 25 hold
    # the flute's walking counterpoint: chord tone on every downbeat,
    # diatonic eighths toward the next bar's tone
    def flute_tone(pcs: list[int], prev: int) -> int:
        cands = [p for p in range(76, 92) if p % 12 in pcs]
        return min(cands, key=lambda p: (abs(p - prev), p))

    prev = 81
    for i in range(24):
        if i in FLUTE_CELL_BARS:
            prev = 88                                    # the cell's E6
            continue
        t = S6 + 4.0 * i
        vel = 74 + min(i, 12)
        tone = flute_tone(FINALE_BARS[i][0], prev)
        sc.note(CH_FLUTE, tone, t, 1.0, vel, jt=2, jv=2)
        target = flute_tone(FINALE_BARS[i + 1][0], tone)
        cur = _F_SCALE.index(tone)
        ti = _F_SCALE.index(target)
        for k, off in enumerate((1.5, 2.0, 2.5, 3.0, 3.5)):
            if cur < ti:
                cur += 1
            elif cur > ti:
                cur -= 1
            else:
                cur += 1 if k % 2 == 0 else -1
            sc.note(CH_FLUTE, _F_SCALE[cur], t + off, 0.45, vel - 8,
                    jt=2, jv=2)
        prev = _F_SCALE[cur]
    # bars 25-26 explicit flute: narrowing, then E6 -> F6
    for t, du, p, v in ((444.0, 1.0, 81, 78), (445.5, 0.45, 82, 70),
                        (446.0, 0.45, 81, 70), (446.5, 0.45, 79, 68),
                        (447.0, 0.45, 77, 68), (447.5, 0.45, 79, 68),
                        (448.0, 1.0, 81, 76), (449.0, 1.0, 84, 74),
                        (450.0, 1.0, 86, 72), (451.0, 1.0, 88, 70)):
        sc.note(CH_FLUTE, p, t, du, v, jt=2, jv=2)
    _play_cells(sc, S6, END)
    # the unison F: all five voices, struck together, fading
    for ch, p, v in ((CH_FLUTE, 89, 64), (CH_SAW, 77, 66),
                     (CH_CHOIR, 77, 58), (CH_GTR, 65, 62),
                     (CH_STR, 53, 60)):
        sc.note(ch, p, UNISON_T0, 7.5, v, jt=0, jv=0)
        en.cc_curve(sc, ch, 11, [(UNISON_T0, 72), (459.4, 26)], step=0.5)


BUILDERS: list = [_m1_baroque, _m2_romantic, _m3_jazz, _m4_electronic,
                  _m5_voice, _m6_finale]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the track is composed to pass them
# ---------------------------------------------------------------------------

_FIVE_VOICES = (CH_FLUTE, CH_STR, CH_GTR, CH_SAW, CH_CHOIR)
_ALL_CHANNELS = _FIVE_VOICES + (CH_BASS, CH_SYNBASS, CH_FLUTE2)


def _notes(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """[(on_beat, dur_beats, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[int, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on / en.PPQ, (tick - on) / en.PPQ,
                            data[1], vel))
    return sorted(out)


def _ccs(sc: en.Score, ch: int, num: int) -> list[tuple[float, int]]:
    return sorted((tick / en.PPQ, data[2])
                  for tick, _prio, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xB0 and data[1] == num)


def _check_fable_cell(sc) -> list[str]:
    """Every CELL_PLAN statement matches notes recomputed from
    material.FABLE_CELL; flagged statements keep the silent L empty;
    every movement states the cell; the finale's five voices all do."""
    fails = []
    by_ch = {ch: _notes(sc, ch) for ch in _ALL_CHANNELS}
    for ch, t0, root, stretch, _v, _ve, _jt, _jv, check_l in CELL_PLAN:
        notes = by_ch[ch]
        for on, du, semi in material.FABLE_CELL:
            eon, edu = t0 + on * stretch, du * stretch
            ep = root + semi
            hits = [x for x in notes
                    if x[2] == ep and abs(x[0] - eon) <= 0.035]
            if not hits:
                fails.append(f"ch{ch} cell@{t0:.0f}: no note {ep} at "
                             f"beat {eon:.2f}")
            elif not any(abs(x[1] - edu) <= 0.06 for x in hits):
                fails.append(f"ch{ch} cell@{t0:.0f}: note {ep} at "
                             f"{eon:.2f} has dur {hits[0][1]:.3f}, "
                             f"want {edu:.3f}")
        if check_l:
            l0, l1 = material.FABLE_SILENT_L
            lo, hi = t0 + l0 * stretch + 0.03, t0 + l1 * stretch - 0.03
            for x in notes:
                if lo <= x[0] < hi:
                    fails.append(f"ch{ch} cell@{t0:.0f}: note at "
                                 f"{x[0]:.2f} inside the silent L")
    spans = [(S1, S2), (S2, S3), (S3, S4), (S4, S5), (S5, S6), (S6, END)]
    for k, (lo, hi) in enumerate(spans):
        if not any(lo <= e[1] < hi for e in CELL_PLAN):
            fails.append(f"movement {k + 1} never states the cell")
    finale_chs = {e[0] for e in CELL_PLAN if e[1] >= S6}
    if finale_chs != set(_FIVE_VOICES):
        fails.append(f"finale statements cover channels {finale_chs}, "
                     f"want all five voices")
    return fails


def _check_canon(sc) -> list[str]:
    """Movement i is a strict canon: expected comes events (dux data
    +3 beats, -7 semitones, cells expanded from material.FABLE_CELL)
    all appear on ch7, and ch7 holds nothing else in the canon span."""
    fails = []
    expected: list[tuple[float, float, int]] = []
    for t0, root in DUX_CANON_CELLS:
        for on, du, semi in material.FABLE_CELL:
            expected.append((t0 + on + CANON_DELAY, du,
                             root + semi + CANON_SHIFT))
    for t, du, p, _v in DUX_LINE:
        expected.append((t + CANON_DELAY, du, p + CANON_SHIFT))
    expected.sort()
    observed = [x for x in _notes(sc, CH_FLUTE2)
                if 2.9 <= x[0] < 51.3]
    if len(observed) != len(expected):
        fails.append(f"comes has {len(observed)} notes in the canon "
                     f"span, want {len(expected)}")
        return fails
    for (on, du, p, _v), (eon, edu, ep) in zip(observed, expected):
        if p != ep or abs(on - eon) > 0.035 or abs(du - edu) > 0.06:
            fails.append(f"comes note ({on:.2f}, {du:.2f}, {p}) breaks "
                         f"the canon (want {eon:.2f}, {edu:.2f}, {ep})")
    return fails


def _check_romantic(sc) -> list[str]:
    """Movement ii: a real rubato map and wide string dynamics."""
    fails = []
    tempos = [(b, bpm) for b, bpm in sc.tempos if S2 <= b < S3]
    if len(tempos) < 6:
        fails.append(f"only {len(tempos)} tempo events in [72, 140): "
                     f"no rubato")
    bpms = [bpm for _b, bpm in tempos]
    if bpms and max(bpms) - min(bpms) < 16:
        fails.append(f"rubato span {max(bpms) - min(bpms):.0f} bpm < 16")
    vels = [v for on, _du, _p, v in _notes(sc, CH_STR) if S2 <= on < S3]
    if not vels:
        return fails + ["no string notes in movement ii"]
    if max(vels) - min(vels) < 40:
        fails.append(f"string velocity span {max(vels) - min(vels)} < 40")
    if max(vels) < 98:
        fails.append(f"string peak vel {max(vels)} < 98: no ff")
    if min(vels) > 34:
        fails.append(f"string floor vel {min(vels)} > 34: no pp")
    return fails


def _grid_dist(frac: float, targets=(0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)):
    return min(abs(frac - g) for g in targets)


def _check_swing(sc) -> list[str]:
    """Movement iii: every onset on the swing grid {0, 1/3, 2/3}, no
    straight offbeats, >= 24 swung skips, ride pairs at 2:1."""
    fails = []
    onsets: list[float] = []
    for ch in (CH_GTR, CH_BASS, 9):
        onsets.extend(on for on, _du, _p, _v in _notes(sc, ch)
                      if S3 - 0.02 <= on < S4 - 0.02)
    if len(onsets) < 200:
        fails.append(f"only {len(onsets)} onsets in the jazz section")
    skips = 0
    for on in onsets:
        frac = on % 1.0
        if _grid_dist(frac) > 0.06:
            fails.append(f"onset {on:.3f} off the swing grid")
        if 0.42 <= frac <= 0.58:
            fails.append(f"straight offbeat at {on:.3f}")
        if abs(frac - 2.0 / 3.0) <= 0.06:
            skips += 1
    if skips < 24:
        fails.append(f"only {skips} swung skip onsets (< 24)")
    rides = sorted(on for on, _du, p, _v in _notes(sc, 9)
                   if p == 51 and S3 - 0.02 <= on < S4)
    beats = {round(on): on for on in rides if _grid_dist(on % 1.0, (0.0, 1.0)) <= 0.06}
    skips_at = {round((on - 2.0 / 3.0)): on for on in rides
                if abs(on % 1.0 - 2.0 / 3.0) <= 0.08}
    ratios = []
    for b, on in beats.items():
        s, nb = skips_at.get(b), beats.get(b + 1)
        if s is not None and nb is not None:
            ratios.append((s - on) / (nb - s))
    if len(ratios) < 20:
        fails.append(f"only {len(ratios)} ride swing pairs (< 20)")
    for r in ratios:
        if not 1.55 <= r <= 2.55:
            fails.append(f"ride pair ratio {r:.2f} outside [1.55, 2.55]")
            break
    if ratios:
        mean = sum(ratios) / len(ratios)
        if not 1.8 <= mean <= 2.2:
            fails.append(f"mean swing ratio {mean:.2f} outside "
                         f"[1.8, 2.2] (want 2:1)")
    return _cap_local(fails)


def _check_kit(sc) -> list[str]:
    """Ch9 kit programs: brush kit (40) at 0, v2 kit (1) at 236."""
    progs = sorted((tick / en.PPQ, data[1]) for tick, _p, data
                   in sc.events.get(9, []) if (data[0] & 0xF0) == 0xC0)
    if progs != [(0.0, 40), (236.0, 1)]:
        return [f"ch9 programs {progs}, want [(0.0, 40), (236.0, 1)]"]
    return []


def _check_grid(sc) -> list[str]:
    """Movement iv: every note-on tick-exact on the 1/16 grid; the rest
    of the piece stays humanly loose (>= 40% off-grid); the saw authors
    real CC74 sweeps."""
    fails = []
    in_iv = out_iv = off_out = 0
    for ch in _ALL_CHANNELS + (9,):
        for tick, _prio, data in sc.events.get(ch, []):
            if (data[0] & 0xF0) != 0x90 or data[2] == 0:
                continue
            beat = tick / en.PPQ
            if S4 - 0.02 <= beat < S5 - 0.02:
                in_iv += 1
                if tick % (en.PPQ // 4):
                    fails.append(f"ch{ch} onset {beat:.4f} off the "
                                 f"1/16 grid in movement iv")
            else:
                out_iv += 1
                if tick % (en.PPQ // 4):
                    off_out += 1
    if in_iv < 300:
        fails.append(f"movement iv has only {in_iv} notes")
    if out_iv and off_out / out_iv < 0.4:
        fails.append(f"only {off_out / out_iv:.0%} of onsets outside iv "
                     f"are off-grid: humanisation missing")
    cc = [v for b, v in _ccs(sc, CH_SAW, 74) if S4 <= b < S5]
    if not cc or min(cc) > 25 or max(cc) < 95 or max(cc) - min(cc) < 60:
        fails.append("saw CC74 does not sweep (want min<=25, max>=95)")
    rises = 0
    run_lo = run_hi = cc[0] if cc else 0
    for a, b in zip(cc, cc[1:]):
        if b >= a:
            run_hi = b
        else:
            if run_hi - run_lo >= 40:
                rises += 1
            run_lo = run_hi = b
    if run_hi - run_lo >= 40:
        rises += 1
    if rises < 2:
        fails.append(f"only {rises} rising CC74 sweeps of span >= 40")
    return _cap_local(fails)


def _check_vowels(sc) -> list[str]:
    """Movement v: the choir morphs vowels across the full CC70 range
    with at least two direction reversals."""
    fails = []
    vals = [v for b, v in _ccs(sc, CH_CHOIR, 70) if S5 <= b < S6]
    if len(vals) < 10:
        return [f"only {len(vals)} CC70 events in movement v"]
    if min(vals) > 5 or max(vals) < 80:
        fails.append(f"CC70 spans [{min(vals)}, {max(vals)}], want "
                     f"[<=5, >=80] (mm -> ah)")
    reversals, direction = 0, 0
    for a, b in zip(vals, vals[1:]):
        d = (b > a) - (b < a)
        if d and direction and d != direction:
            reversals += 1
        if d:
            direction = d
    if reversals < 2:
        fails.append(f"only {reversals} vowel-morph reversals (< 2)")
    return fails


def _sounding(by_ch, t: float) -> list[tuple[int, int]]:
    out = []
    for ch, notes in by_ch.items():
        for on, du, p, _v in notes:
            if on <= t < on + du:
                out.append((ch, p))
    return out


def _check_consonance(sc) -> list[str]:
    """Every finale downbeat: >= 4 of the five voices sounding (all 5 on
    >= 24 of 28), pairwise interval classes in {0,3,4,7,8,9}; ic 5 only
    between upper voices (never against the bass note)."""
    fails = []
    by_ch = {ch: _notes(sc, ch) for ch in _FIVE_VOICES}
    full = 0
    downbeats = [S6 + 4.0 * k for k in range(28)]
    for t in downbeats:
        snd = _sounding(by_ch, t + 0.06)
        chans = {ch for ch, _p in snd}
        if len(chans) < 4:
            fails.append(f"downbeat {t:.0f}: only voices {sorted(chans)} "
                         f"sounding")
            continue
        if len(chans) == 5:
            full += 1
        pitches = sorted(p for _ch, p in snd)
        lowest = pitches[0]
        for i, a in enumerate(pitches):
            for b in pitches[i + 1:]:
                ic = (b - a) % 12
                if ic in (0, 3, 4, 7, 8, 9):
                    continue
                if ic == 5 and a > lowest:
                    continue
                fails.append(f"downbeat {t:.0f}: dissonance ic {ic} "
                             f"between {a} and {b}")
    if full < 24:
        fails.append(f"all five voices sound on only {full} of 28 "
                     f"finale downbeats (< 24)")
    return _cap_local(fails)


def _check_unison(sc) -> list[str]:
    """Bookends: the track opens on pitch-class F, and the last sounding
    sonority is a single pitch class F across >= 4 channels, struck
    together at the unison and followed by nothing."""
    fails = []
    everything = [(on, du, p, ch) for ch in _ALL_CHANNELS
                  for on, du, p, _v in _notes(sc, ch)]
    if not everything:
        return ["the piece is empty"]
    first = min(everything)
    if first[2] % 12 != 5:
        fails.append(f"first pitch {first[2]} is not pitch-class F")
    last_on = max(on for on, _du, _p, _ch in everything)
    if abs(last_on - UNISON_T0) > 0.01:
        fails.append(f"last note-on at {last_on:.2f}, want the unison "
                     f"strike at {UNISON_T0:.0f}")
    t_end = max(on + du for on, du, _p, _ch in everything)
    final = [(ch, p) for on, du, p, ch in everything
             if on <= t_end - 0.05 < on + du]
    pcs = {p % 12 for _ch, p in final}
    chans = {ch for ch, _p in final}
    if pcs != {5}:
        fails.append(f"final sonority pitch classes {sorted(pcs)}, "
                     f"want only F")
    if len(chans) < 4:
        fails.append(f"final F sounds on only {len(chans)} channels "
                     f"(< 4)")
    return fails


def _cap_local(fails: list[str], cap: int = 8) -> list[str]:
    if len(fails) > cap:
        return fails[:cap] + [f"... and {len(fails) - cap} more"]
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("fable_cell_fidelity", _check_fable_cell(sc)),
        ("baroque_canon", _check_canon(sc)),
        ("romantic_rubato_dynamics", _check_romantic(sc)),
        ("jazz_swing", _check_swing(sc)),
        ("kit_select", _check_kit(sc)),
        ("electronic_grid", _check_grid(sc)),
        ("choir_vowels", _check_vowels(sc)),
        ("finale_downbeat_consonance", _check_consonance(sc)),
        ("unison_f_ending", _check_unison(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/01 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """Headline dynamics on the RENDER: the electronic movement
    out-powers the solo flute canon and the choir movement by >= 3 dB,
    and the unison tail fades >= 5 dB below the finale body."""
    def win_db(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    fails = []
    canon = win_db(4.0, 68.0)
    grid = win_db(240.0, 312.0)
    choir = win_db(318.0, 346.0)
    if grid < canon + 3.0:
        fails.append(f"electronic {grid:.1f} dB not >= canon "
                     f"{canon:.1f} + 3")
    if grid < choir + 3.0:
        fails.append(f"electronic {grid:.1f} dB not >= choir "
                     f"{choir:.1f} + 3")
    contrast = [("audio_idiom_contrast", fails)]
    body = win_db(S6, 444.0)
    tail = win_db(456.0, 459.4)
    fade = [] if tail <= body - 5.0 else [
        f"unison tail {tail:.1f} dB not >= 5 dB below finale body "
        f"{body:.1f}"]
    return contrast + [("audio_unison_fade", fade)]
