"""t10_the_flypast.py — Slipstream T10: "The Flypast" (finale).

HLD section 4/T10.  E aeolian, 128 bpm (Three-Sixty-One's key AND tempo,
deliberate), 4/4, ~5:42.  Every aircraft of the day airborne at once: a
muster roll-call quotes this album's own formations (T1 octaves, T6 mirror,
T7 sixths), then three build/drop cycles — each verified bigger — end in the
flypast STACK: the ORBIT_RIFF_361 steel ostinato (tick-exact), ASCENT_CELL
in 4x augmentation (choir + brass, pinned), the lead ship's T361 SCREAM
reprise (91 -> held 93 with +2 bend flicks), and the wing ship's counter-line
under the full counterpoint discipline — all over a tonic pedal, every
structural downbeat of the core pairwise-consonant across the four lanes.
Sign-off: Morse CLEAR SKIES on the woodblock, then one final unison E.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 10
TITLE = "The Flypast"
FILE = "10 - The Flypast.mid"
SEED = 20261110

COMMENT = ("The Flypast - Slipstream's finale in Three-Sixty-One's own key and "
           "tempo. A muster roll-call of the album's duo formations, three "
           "climbing cycles each bigger than the last, and the final stack: "
           "the 361 orbit riff on steel, the ascent cell augmented four-fold "
           "in choir and brass, the lead guitar's screamed A6 reprise and the "
           "wing guitar's counter-line over a tonic pedal. Morse CLEAR SKIES "
           "signs the show off; one unison E ends it.")

# ---------------------------------------------------------------------------
# Grid (beats).  Six movements, contiguous; END = 728 (~5:42 at 128 bpm).
# ---------------------------------------------------------------------------

BPM = 128.0
MODE = "aeolian"
BASE = 64                      # E4 — degree-1 anchor for lines
END = 728.0

M1 = (0.0, 72.0)               # I.   Muster (roll call)
M2 = (72.0, 224.0)             # II.  First Pass  (BUILD1 72-152, DROP1 152-216)
M3 = (224.0, 392.0)            # III. Second Pass (BUILD2 224-304, DROP2 304-384)
M4 = (392.0, 504.0)            # IV.  The Long Climb (BUILD3)
M5 = (504.0, 648.0)            # V.   The Flypast (DROP3 / the stack)
M6 = (648.0, 728.0)            # VI.  Clear Skies (sign-off)

B1 = (72.0, 152.0)
D1 = (152.0, 216.0)
B2 = (224.0, 304.0)
D2 = (304.0, 384.0)
B3 = (392.0, 504.0)
D3 = (504.0, 632.0)

ORBIT_SPAN = (512.0, 624.0)    # the steel ostinato, 2-beat cells
CORE = (568.0, 584.0)          # scream hold == the 4-lane simultaneity core
CP_WINDOW = (552.0, 600.0)     # wing-vs-lead counterpoint window
MORSE_T0 = 672.0
UNISON_T0 = 712.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Muster", *M1),
        ("II. First Pass", *M2),
        ("III. Second Pass", *M3),
        ("IV. The Long Climb", *M4),
        ("V. The Flypast", *M5),
        ("VI. Clear Skies", *M6),
    ],
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1)],                       # E minor
    channels=[
        (0, "steel ostinato", 114, 94, 64, 45),
        (1, "warm pad", 89, 96, 64, 70),
        (2, "synth bass", 39, 108, 64, 20),
        (3, "post L", 80, 88, 18, 45),
        (4, "post R", 80, 88, 110, 45),
        (5, "saw soar", 81, 104, 64, 50),
        (6, "harp", 46, 92, 64, 55),
        (7, "aerial strings", 49, 88, 64, 70),
        (8, "choir", 52, 96, 64, 70),
        (9, "kit", 0, 112, 64, 35),
        (10, "melodic toms", 117, 100, 64, 40),
        (11, "synth drum", 118, 100, 64, 40),
        (12, "brass", 61, 100, 64, 45),
        (13, "riser", 119, 100, 64, 60),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 106, 64, 24),
    ],
    program_changes=[(9, 0.0, 1)],               # the V3 kit
    extra_markers=[
        (152.0, "Drop 1"),
        (304.0, "Drop 2"),
        (504.0, "The Flypast"),
        (568.0, "Scream"),
        (672.0, "Morse: CLEAR SKIES"),
    ],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

# ---------------------------------------------------------------------------
# Harmony.  Build/drop loop | Em | C | G | D | (degree, bar each); muster and
# sign-off breathe on Em / C / Am.
# ---------------------------------------------------------------------------

LOOP_DEGS = [1, 6, 3, 7]                     # Em C G D in E aeolian
LOOP_ROOTS2 = [40, 36, 43, 38]               # bass roots, octave 2
LOOP_ROOTS3 = [52, 48, 55, 50]               # chug roots, octave 3


def _triads(degs):
    return [en.triad(52, MODE, d) for d in degs]


# ---------------------------------------------------------------------------
# The muster cameos (all jt=0; oracle-pinned).
# ---------------------------------------------------------------------------

CAMEO_OCT_T0 = 16.0            # T1 formation: wing == lead - 12, tick-for-tick
CAMEO_MIR_T0 = 32.0            # T6 formation: wing == mirror(lead, 63)
CAMEO_MIR_AXIS = 63.0
CAMEO_SIX_T0 = 48.0            # T7 formation: parallel diatonic sixths

CAMEO_MIR_LEAD = [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 71, 0.5),
                  (1.5, 69, 0.5), (2.0, 71, 2.0)]
CAMEO_SIX_LEAD = [(0.0, 71, 0.5), (0.5, 69, 0.5), (1.0, 67, 0.5),
                  (1.5, 69, 0.5), (2.0, 71, 1.5), (4.0, 74, 0.5),
                  (4.5, 71, 0.5), (5.0, 69, 0.5), (5.5, 67, 1.5)]
CAMEO_SIX_MAP = {71: 62, 69: 60, 67: 59, 74: 66}   # diatonic sixth below

# ---------------------------------------------------------------------------
# The hook (DROP1, restated +12 in the flypast).  Offsets in beats over a
# 32-beat (8-bar) frame; E4 register.
# ---------------------------------------------------------------------------

HOOK = [
    (0.0, 64, 1.0), (1.0, 67, 0.5), (1.5, 71, 1.5), (3.0, 69, 1.0),
    (4.0, 67, 1.0), (5.0, 69, 0.5), (5.5, 71, 1.5), (7.0, 74, 1.0),
    (8.0, 76, 1.5), (9.5, 74, 0.5), (10.0, 71, 1.0), (11.0, 69, 1.0),
    (12.0, 67, 1.0), (13.0, 69, 1.0), (14.0, 71, 2.0),
    (16.0, 64, 1.0), (17.0, 67, 0.5), (17.5, 71, 1.5), (19.0, 69, 1.0),
    (20.0, 67, 1.0), (21.0, 69, 0.5), (21.5, 74, 1.5), (23.0, 76, 1.0),
    (24.0, 79, 1.5), (25.5, 76, 0.5), (26.0, 74, 1.0), (27.0, 71, 1.0),
    (28.0, 69, 1.0), (29.0, 71, 1.0), (30.0, 76, 2.0),
]

# ---------------------------------------------------------------------------
# Flypast lead + wing tables (M5).  The counterpoint window downbeat pitches
# are load-bearing: they were composed against the consonance/motion oracles.
# ---------------------------------------------------------------------------

LEAD_M5 = [
    # soar into the scream
    (536.0, 76, 4.0, 96), (540.0, 79, 4.0, 98), (544.0, 81, 8.0, 100),
    (552.0, 76, 4.0, 98), (556.0, 79, 4.0, 100), (560.0, 81, 4.0, 102),
    (564.0, 83, 2.0, 104),
    (566.0, material.SCREAM_APPROACH_361, 2.0, 106),   # the approach (91)
    (568.0, material.SCREAM_PEAK_361, 16.0, 110),      # the held peak (93)
    # victory descent
    (584.0, 81, 2.0, 104), (586.0, 79, 4.0, 102), (590.0, 78, 2.0, 100),
    (592.0, 76, 4.0, 102), (596.0, 74, 2.0, 100), (598.0, 71, 2.0, 98),
    (600.0, 76, 6.0, 100), (606.0, 79, 2.0, 96), (608.0, 83, 4.0, 98),
    (612.0, 79, 4.0, 96), (616.0, 76, 8.0, 94), (624.0, 71, 4.0, 88),
    (628.0, 76, 12.0, 90),
]

WING_M5_FREE = [                       # 536-552: approach lines (pre-window)
    (536.0, 64, 2.0), (538.0, 67, 1.0), (539.0, 69, 1.0), (540.0, 72, 2.0),
    (542.0, 71, 1.0), (543.0, 69, 1.0), (544.0, 67, 2.0), (546.0, 64, 1.0),
    (547.0, 62, 1.0), (548.0, 64, 2.0), (550.0, 67, 1.0), (551.0, 71, 1.0),
]

WING_M5_CP = [                         # 552-600: the counter-line
    (552.0, 72, 2.0), (554.0, 74, 1.0), (555.0, 72, 1.0),
    (556.0, 71, 2.0), (558.0, 69, 1.0), (559.0, 66, 1.0),
    (560.0, 64, 2.0), (562.0, 67, 0.5), (562.5, 66, 0.5), (563.0, 64, 1.0),
    (564.0, 62, 2.0), (566.0, 60, 1.0), (567.0, 59, 1.0),
    (568.0, 60, 2.0), (570.0, 64, 1.0), (571.0, 62, 1.0),
    (572.0, 64, 2.0), (574.0, 67, 1.0), (575.0, 64, 1.0),
    (576.0, 60, 2.0), (578.0, 62, 1.0), (579.0, 64, 1.0),
    (580.0, 64, 2.0), (582.0, 67, 1.0), (583.0, 66, 1.0),
    (584.0, 66, 2.0), (586.0, 72, 1.0), (587.0, 69, 1.0),
    (588.0, 71, 2.0), (590.0, 74, 1.0), (591.0, 71, 1.0),
    (592.0, 72, 2.0), (594.0, 72, 1.0), (595.0, 74, 1.0),
    (596.0, 78, 2.0), (598.0, 76, 1.0), (599.0, 74, 1.0),
]

WING_M5_OUT = [                        # 600-648: trades and wind-down
    (600.0, 72, 2.0), (602.0, 71, 1.0), (603.0, 69, 1.0), (604.0, 67, 2.0),
    (606.0, 64, 1.0), (607.0, 62, 1.0), (608.0, 64, 4.0), (612.0, 67, 2.0),
    (614.0, 71, 2.0), (616.0, 64, 8.0), (624.0, 64, 1.0), (625.0, 62, 1.0),
    (626.0, 60, 1.0), (627.0, 59, 1.0), (628.0, 57, 4.0), (632.0, 55, 4.0),
    (636.0, 52, 12.0),
]

# The 4x-augmented ASCENT statements (choir ch8 root / brass ch12 root).
# The 568 statement co-spans the scream hold: its A/E geometry keeps every
# core downbeat pairwise-consonant against the held A6 and the orbit's E.
AUG_STATEMENTS = [(520.0, 64, 52), (568.0, 69, 57), (592.0, 64, 52)]

# ---------------------------------------------------------------------------
# Fill schedule (shape library material.FILL_LIB; jt=0 inside play_fill).
# Counts per quarter-window were composed against fill_escalation_x3:
#   B1 3/11/17/29   B2 8/12/17/37   B3 11/20/36/62   (peaks strictly rising)
# and each drop is entered through a >=20-note unbroken run.
# ---------------------------------------------------------------------------

FILL_SCHEDULE = [
    (68.0, "A", 0),
    # BUILD1
    (88.0, "A", 0), (96.0, "D", 0), (108.0, "A", 0),
    (118.0, "C", 2), (126.0, "B", 2), (134.0, "G", 4),
    (148.25, "A", 6), (149.0, "F", 6), (151.0, "G", 6),
    # DROP1 (thinned)
    (168.0, "D", 4), (184.0, "A", 4), (200.0, "D", 4),
    # BUILD2
    (236.0, "H", 2), (252.0, "C", 2), (260.0, "A", 2),
    (268.0, "G", 4), (276.0, "D", 4), (288.0, "F", 6), (292.0, "C", 6),
    (300.25, "A", 8), (301.0, "F", 8), (303.0, "G", 8),
    # DROP2 (thinned)
    (320.0, "A", 6), (336.0, "D", 6), (352.0, "A", 6), (368.0, "H", 6),
    # BUILD3
    (412.0, "A", 4), (416.0, "H", 4), (424.0, "C", 6), (432.0, "D", 6),
    (444.0, "A", 6), (452.0, "G", 8), (460.0, "B", 8), (468.0, "F", 8),
    (472.0, "E", 8), (478.0, "C", 10), (482.0, "H", 10), (486.0, "G", 10),
    (490.0, "B", 10), (497.25, "E", 10), (500.25, "F", 10), (502.25, "G", 10),
    # DROP3 (thinned)
    (520.0, "D", 8), (536.0, "A", 8), (584.5, "A", 8),
    (600.0, "D", 8), (616.0, "G", 8),
]

RISERS = [                     # (beat, dur, vel) — ch13 GM119 reverse cymbal
    (148.0, 4.0, 88), (300.0, 4.0, 96),
    (456.0, 6.0, 84), (472.0, 6.0, 90), (488.0, 10.0, 98), (500.0, 4.0, 110),
    (564.0, 4.0, 104),
]

# ---------------------------------------------------------------------------
# Emitter helpers
# ---------------------------------------------------------------------------


def _build_fills(sc, t0, t1):
    for start, shape, vbump in FILL_SCHEDULE:
        if t0 <= start < t1:
            material.play_fill(sc, shape, start, vbump=vbump)


def _risers(sc, t0, t1):
    for beat, dur, vel in RISERS:
        if t0 <= beat < t1:
            sc.note(13, 62, beat, dur, vel, jt=0, jv=0)


def _bloom(sc, ch, on, dur, peak=None):
    """CC1 bloom over a held note (the T361 lead-voice gesture)."""
    if peak is None:
        peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _table(sc, ch, notes, vel=None, jt=0, jv=3, gate=0.98, bloom=False):
    for row in notes:
        if len(row) == 4:
            t, p, d, v = row
        else:
            t, p, d = row
            v = vel
        sc.note(ch, p, t, d * gate, v, jt=jt, jv=jv)
        if bloom and d >= 2.0:
            _bloom(sc, ch, t, d)


def _post_call(sc, ch, t, pitches, vel, dur=0.22):
    for i, p in enumerate(pitches):
        sc.note(ch, p, t + 0.25 * i, dur, vel, jt=2, jv=3)


def _bass_eighths(sc, t0, t1, roots, v0, v1, pop=False, jt=2):
    """Roots cycle bar-by-bar; pop=True lifts 8th #4/#8 an octave."""
    nbars = int(round((t1 - t0) / 4.0))
    for b in range(nbars):
        root = roots[b % len(roots)]
        for k in range(8):
            t = t0 + 4.0 * b + 0.5 * k
            p = root + (12 if pop and k in (3, 7) else 0)
            v = en.lerp(v0, v1, (t - t0) / max(1e-9, t1 - t0))
            sc.note(2, p, t, 0.42, int(v) + (4 if k == 0 else 0), jt=jt, jv=3)


def _chug(sc, t0, t1, roots, v0, v1, fifth=False):
    """Wing-ship 8th chugs; fifth=True accents beats 1.5/3.0 a fifth up."""
    nbars = int(round((t1 - t0) / 4.0))
    for b in range(nbars):
        root = roots[b % len(roots)]
        for k in range(8):
            t = t0 + 4.0 * b + 0.5 * k
            p = root + (7 if fifth and k in (3, 6) else 0)
            v = en.lerp(v0, v1, (t - t0) / max(1e-9, t1 - t0))
            sc.note(15, p, t, 0.36, int(v), jt=2, jv=3)


def _gallop(sc, t0, t1, roots, v0, v1):
    """Wing-ship gallop chug (the BUILD2 texture)."""
    offs = [0.0, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5]
    nbars = int(round((t1 - t0) / 4.0))
    for b in range(nbars):
        root = roots[b % len(roots)]
        for off in offs:
            t = t0 + 4.0 * b + off
            v = en.lerp(v0, v1, (t - t0) / max(1e-9, t1 - t0))
            sc.note(15, root, t, 0.3, int(v), jt=2, jv=3)


def _ost_cell(sc, t0, t1, pitches, step, v0, v1, jv=2):
    """Steel ostinato: cycle `pitches` at `step` with a velocity ramp."""
    n = int(round((t1 - t0) / step))
    for i in range(n):
        t = t0 + step * i
        v = en.lerp(v0, v1, i / max(1, n - 1))
        sc.note(0, pitches[i % len(pitches)], t, step * 0.9, int(v),
                jt=0, jv=jv)


def _groove_half(sc, t0, t1, kick, snare, hat):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        sc.note(9, 36, bar, 0.25, kick, jt=0, jv=4)
        sc.note(9, 38, bar + 2.0, 0.3, snare, jt=0, jv=4)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.2, hat, jt=0, jv=4)


def _groove_full(sc, t0, t1, kick, snare, hat, oh=0, hat16=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for beat in (0.0, 2.0):
            sc.note(9, 36, bar + beat, 0.25, kick, jt=0, jv=4)
        for beat in (1.0, 3.0):
            sc.note(9, 38, bar + beat, 0.3, snare, jt=0, jv=4)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.2, hat, jt=0, jv=4)
        if oh:
            for beat in (0.5, 2.5):
                sc.note(9, 46, bar + beat, 0.4, oh, jt=0, jv=4)
        if hat16:
            for k in range(8):
                sc.note(9, 42, bar + 0.5 * k + 0.25, 0.14, hat16, jt=0, jv=4)


def _four_floor(sc, t0, t1, kick, clap, hat, open_hat, hat16=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(9, 46, t + 0.5, 0.4, open_hat, jt=0, jv=4)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
        sc.note(9, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(9, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)


def _snare_roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _crash(sc, beat, vel):
    sc.note(9, 49, beat, 1.0, vel, jt=0, jv=3)


def _play_hook(sc, ch, t0, vel, transpose=0, bloom=False):
    for off, p, d in HOOK:
        sc.note(ch, p + transpose, t0 + off, d * 0.98, vel, jt=0, jv=3)
        if bloom and d >= 2.0:
            _bloom(sc, ch, t0 + off, d)


# ---------------------------------------------------------------------------
# Builders (one per movement; note-ons stay inside the movement's window)
# ---------------------------------------------------------------------------


def _m1_muster(sc):
    # Whole-timeline CC lanes, authored once here (CC is bounds-exempt).
    en.cc_curve(sc, 1, 74, [
        (0.0, 32), (64.0, 44), (72.0, 50), (150.0, 86), (152.0, 70),
        (216.0, 58), (224.0, 54), (302.0, 92), (304.0, 74), (384.0, 60),
        (392.0, 50), (500.0, 100), (504.0, 96), (568.0, 110), (648.0, 60),
        (700.0, 42), (728.0, 38)], step=1.0)
    en.cc_curve(sc, 1, 11, [
        (0.0, 70), (72.0, 84), (152.0, 100), (216.0, 80), (224.0, 84),
        (304.0, 104), (384.0, 84), (392.0, 78), (504.0, 110), (648.0, 84),
        (712.0, 60), (728.0, 50)], step=2.0)
    en.vowel_curve(sc, 8, [
        (0.0, 45), (300.0, 45), (304.0, 85), (384.0, 60), (392.0, 20),
        (456.0, 45), (504.0, 90), (648.0, 45), (672.0, 20), (700.0, 0)],
        step=1.0)

    # Pad bed: Em breathing on C, one Am colour, D turn into BUILD1.
    en.pad_block(sc, 1, 0.0, _triads([1, 1, 6, 1, 1, 6, 1, 7, 1]),
                 span=8.0, size=4, lo=52, hi=76, vel=40, vel_end=56)
    # Bass swells.
    for k in range(9):
        sc.note(2, 40, 8.0 * k, 7.5, 44 + 2 * k, jt=2, jv=2)
    # Harp arpeggios between the cameos.
    for i, t in enumerate((8.0, 24.0, 40.0, 56.0)):
        en.arp(sc, 6, [52, 59, 64, 67, 71, 76], t, 12, 0.25, 46 + 3 * i)
    # Radio posts: L call, R answer.
    for i, t in enumerate((10.0, 26.0, 42.0, 58.0)):
        _post_call(sc, 3, t, [76, 76, 79], 44 + 3 * i)
        _post_call(sc, 4, t + 2.0, [71, 71, 74], 42 + 3 * i)
    # Strings shading.
    _table(sc, 7, [(32.0, 64, 16.0, 40), (32.0, 59, 16.0, 38),
                   (48.0, 67, 16.0, 44), (48.0, 60, 16.0, 40)], jt=3)

    # CAMEO 1 — T1 octaves: the duo states ASCENT, wing tick-for-tick -12.
    material.play_ascent(sc, 14, CAMEO_OCT_T0, 64, vel=66, vel_end=76, jt=0)
    material.play_ascent(sc, 15, CAMEO_OCT_T0, 52, vel=62, vel_end=72, jt=0)
    # CAMEO 2 — T6 mirror about D#4 (axis 63): images stay diatonic.
    for off, p, d in CAMEO_MIR_LEAD:
        sc.note(14, p, CAMEO_MIR_T0 + off, d * 0.98, 70, jt=0, jv=3)
        sc.note(15, material.mirror(p, CAMEO_MIR_AXIS), CAMEO_MIR_T0 + off,
                d * 0.98, 64, jt=0, jv=3)
    # CAMEO 3 — T7 sixths: parallel diatonic sixths.
    for off, p, d in CAMEO_SIX_LEAD:
        sc.note(14, p, CAMEO_SIX_T0 + off, d * 0.98, 74, jt=0, jv=3)
        sc.note(15, CAMEO_SIX_MAP[p], CAMEO_SIX_T0 + off, d * 0.98, 68,
                jt=0, jv=3)

    # Taxi out: ostinato and soft kit wake up under a first fill.
    _ost_cell(sc, 64.0, 72.0, [64, 71, 76, 71], 0.5, 56, 70)
    for k in range(16):
        sc.note(9, 42, 60.0 + 0.5 * k, 0.2, 32 + k, jt=0, jv=3)
    sc.note(9, 36, 64.0, 0.25, 54, jt=0, jv=3)
    sc.note(9, 36, 68.0, 0.25, 60, jt=0, jv=3)
    sc.note(9, 38, 70.0, 0.3, 52, jt=0, jv=3)
    _build_fills(sc, *M1)


def _m2_first_pass(sc):
    # --- BUILD1 (72-152): strict quarter-window escalation ---
    en.pad_block(sc, 1, 72.0, _triads(LOOP_DEGS * 5),
                 span=4.0, size=4, lo=52, hi=76, vel=52, vel_end=72)
    _bass_eighths(sc, 72.0, 152.0, LOOP_ROOTS2, 60, 84)
    _chug(sc, 72.0, 152.0, LOOP_ROOTS3, 60, 82)
    _ost_cell(sc, 72.0, 152.0, [64, 71, 76, 71], 0.5, 56, 84)
    _groove_half(sc, 72.0, 104.0, 70, 66, 40)
    _groove_full(sc, 104.0, 136.0, 78, 74, 44, oh=50)
    _groove_full(sc, 136.0, 152.0, 84, 80, 48, oh=56, hat16=40)
    # Lead fragments preview the hook.
    _table(sc, 14, [(104.0, 64, 1.0, 66), (105.0, 67, 0.5, 68),
                    (105.5, 71, 1.5, 70),
                    (112.0, 64, 1.0, 68), (113.0, 67, 0.5, 70),
                    (113.5, 71, 1.5, 72),
                    (120.0, 67, 1.0, 72), (121.0, 69, 0.5, 74),
                    (121.5, 74, 1.5, 76),
                    (128.0, 71, 1.0, 76), (129.0, 74, 0.5, 78),
                    (129.5, 76, 2.0, 80)], bloom=True)
    # Strings climb in octaves of the loop.
    _table(sc, 7, [(104.0, 64, 8.0, 48), (112.0, 67, 8.0, 52),
                   (120.0, 71, 8.0, 56), (128.0, 74, 8.0, 60),
                   (136.0, 76, 8.0, 64), (144.0, 79, 8.0, 68)], jt=3)
    # Saw wakes late in the build.
    _table(sc, 5, [(136.0, 64, 8.0, 60), (144.0, 67, 8.0, 64)], jt=2)
    _bloom(sc, 5, 136.0, 8.0)
    _bloom(sc, 5, 144.0, 8.0)
    # Posts trade over the build.
    for i, t in enumerate((86.0, 102.0, 118.0, 134.0)):
        _post_call(sc, 3, t, [76, 79, 76], 56 + 2 * i)
        _post_call(sc, 4, t + 2.0, [71, 74, 71], 54 + 2 * i)

    # --- DROP1 (152-216): the hook lands ---
    _crash(sc, 152.0, 100)
    _crash(sc, 184.0, 92)
    _four_floor(sc, 152.0, 216.0, 96, 90, 52, 58)
    en.pad_block(sc, 1, 152.0, _triads(LOOP_DEGS * 4),
                 span=4.0, size=4, lo=52, hi=76, vel=74)
    _bass_eighths(sc, 152.0, 216.0, LOOP_ROOTS2, 88, 96, pop=True)
    _ost_cell(sc, 152.0, 216.0, [64, 71, 76, 79], 0.25, 72, 88)
    _play_hook(sc, 14, 152.0, 92, bloom=True)
    _play_hook(sc, 14, 184.0, 98, bloom=True)
    _chug(sc, 152.0, 216.0, LOOP_ROOTS3, 86, 92, fifth=True)
    _table(sc, 5, [(152.0, 83, 16.0, 74), (168.0, 79, 16.0, 74),
                   (184.0, 83, 16.0, 76), (200.0, 88, 16.0, 78)], jt=2)
    _table(sc, 7, [(152.0, 76, 32.0, 66), (184.0, 79, 32.0, 68)], jt=3)
    for t in (166.0, 182.0, 198.0):
        en.arp(sc, 6, [64, 67, 71, 76, 79, 83, 88], t, 8, 0.25, 66)
    for i, t in enumerate((168.5, 184.5, 200.5)):
        sc.note(3, 79, t, 0.4, 66, jt=2, jv=3)
        sc.note(4, 79, t + 2.0, 0.4, 66, jt=2, jv=3)

    # --- turn (216-224): strip to bass + pad ---
    en.pad_block(sc, 1, 216.0, _triads([1, 1]),
                 span=4.0, size=4, lo=52, hi=76, vel=60)
    _table(sc, 2, [(216.0, 40, 2.0, 70), (218.0, 40, 2.0, 66),
                   (220.0, 40, 2.0, 62), (222.0, 40, 2.0, 58)], jt=2)
    sc.note(9, 36, 216.0, 0.25, 78, jt=0, jv=3)
    for k in range(8):
        sc.note(9, 42, 216.0 + k, 0.2, 36, jt=0, jv=3)
    _build_fills(sc, *M2)
    _risers(sc, *M2)


def _m3_second_pass(sc):
    # --- BUILD2 (224-304) ---
    _crash(sc, 224.0, 80)
    en.pad_block(sc, 1, 224.0, _triads(LOOP_DEGS * 5),
                 span=4.0, size=4, lo=52, hi=76, vel=56, vel_end=76)
    _bass_eighths(sc, 224.0, 304.0, LOOP_ROOTS2, 64, 88)
    _gallop(sc, 224.0, 304.0, LOOP_ROOTS3, 64, 86)
    _ost_cell(sc, 224.0, 304.0, [64, 71, 76, 71], 0.5, 60, 86)
    _groove_half(sc, 224.0, 256.0, 72, 68, 40)
    _groove_full(sc, 256.0, 288.0, 80, 76, 46, oh=52)
    _groove_full(sc, 288.0, 304.0, 86, 82, 50, oh=58, hat16=42)
    # Lead machine-gun runs, each capped with a held tone.
    en.run(sc, 14, 248.0, BASE, MODE, [1, 2, 3, 4, 5, 6, 7, 8],
           0.25, 68, 80, legato=True)
    _table(sc, 14, [(250.0, 76, 2.0, 80)], bloom=True)
    en.run(sc, 14, 264.0, BASE, MODE, [3, 4, 5, 6, 7, 8, 9, 10],
           0.25, 74, 84, legato=True)
    _table(sc, 14, [(266.0, 79, 2.0, 84)], bloom=True)
    en.run(sc, 14, 272.0, BASE, MODE, [5, 6, 7, 8, 9, 10, 11, 12],
           0.25, 78, 88, legato=True)
    _table(sc, 14, [(274.0, 83, 2.0, 88)], bloom=True)
    en.run(sc, 14, 288.0, BASE, MODE, [8, 9, 10, 11, 12, 13, 14, 15],
           0.25, 84, 94, legato=True)
    _table(sc, 14, [(290.0, 88, 4.0, 94)], bloom=True)
    # Strings and brass swell under the runs.
    _table(sc, 7, [(224.0, 67, 16.0, 52), (240.0, 71, 16.0, 56),
                   (256.0, 74, 16.0, 60), (272.0, 76, 16.0, 64),
                   (288.0, 79, 16.0, 68)], jt=3)
    _table(sc, 12, [(272.0, 52, 8.0, 54), (280.0, 55, 8.0, 58),
                    (288.0, 59, 8.0, 64), (296.0, 62, 8.0, 70)], jt=2)
    for t in (232.0, 248.0, 264.0, 280.0):
        en.arp(sc, 6, [52, 59, 64, 67, 71, 76], t, 8, 0.25, 54)
    for i, t in enumerate((232.0, 248.0, 264.0, 280.0, 296.0)):
        _post_call(sc, 3, t, [76, 79, 76], 60 + 2 * i)
        _post_call(sc, 4, t + 2.0, [71, 74, 71], 58 + 2 * i)
    # Saw swoop into DROP2: portamento glide E4 -> G5 (15 semitones).
    en.portamento_on(sc, 5, 303.4, time_cc=58)
    sc.note(5, 64, 303.5, 0.45, 86, jt=0, jv=2)

    # --- DROP2 (304-384): bigger than DROP1 ---
    sc.note(5, 79, 304.0, 4.0, 94, jt=0, jv=2)
    en.portamento_off(sc, 5, 308.5)
    _crash(sc, 304.0, 104)
    _crash(sc, 336.0, 96)
    _crash(sc, 368.0, 98)
    _four_floor(sc, 304.0, 384.0, 100, 94, 56, 62, hat16=44)
    en.pad_block(sc, 1, 304.0, _triads(LOOP_DEGS * 5),
                 span=4.0, size=4, lo=52, hi=76, vel=78)
    _bass_eighths(sc, 304.0, 384.0, LOOP_ROOTS2, 92, 100, pop=True)
    _ost_cell(sc, 304.0, 384.0, [64, 71, 76, 79], 0.25, 72, 88)
    _play_hook(sc, 14, 304.0, 102, bloom=True)
    _play_hook(sc, 14, 336.0, 106, bloom=True)
    _play_hook(sc, 15, 304.0, 96, transpose=-12)     # octaves formation, full
    _play_hook(sc, 15, 336.0, 100, transpose=-12)
    _table(sc, 14, [(368.0, 76, 2.0, 104), (370.0, 79, 2.0, 104),
                    (372.0, 81, 2.0, 106), (374.0, 83, 2.0, 106),
                    (376.0, 88, 6.0, 108), (382.0, 83, 2.0, 100)],
           bloom=True)
    _table(sc, 15, [(368.0, 52, 0.4, 94), (368.5, 52, 0.4, 94),
                    (369.0, 52, 0.4, 94), (369.5, 52, 0.4, 94),
                    (370.0, 52, 0.4, 94), (370.5, 52, 0.4, 94),
                    (371.0, 52, 0.4, 94), (371.5, 52, 0.4, 94),
                    (372.0, 52, 0.4, 96), (372.5, 52, 0.4, 96),
                    (373.0, 52, 0.4, 96), (373.5, 52, 0.4, 96),
                    (374.0, 52, 0.4, 96), (374.5, 52, 0.4, 96),
                    (375.0, 52, 0.4, 96), (375.5, 52, 0.4, 96),
                    (376.0, 55, 1.0, 98), (377.0, 57, 1.0, 98),
                    (378.0, 59, 1.0, 100), (379.0, 62, 1.0, 100),
                    (380.0, 64, 4.0, 102)])
    _table(sc, 5, [(308.0, 83, 8.0, 92), (316.0, 79, 8.0, 90),
                   (324.0, 76, 8.0, 90), (332.0, 79, 4.0, 92),
                   (336.0, 83, 8.0, 94), (344.0, 79, 8.0, 92),
                   (352.0, 76, 8.0, 92), (360.0, 83, 8.0, 94),
                   (368.0, 88, 12.0, 96), (380.0, 83, 4.0, 90)], jt=2)
    _bloom(sc, 5, 368.0, 12.0)
    _table(sc, 7, [(304.0, 83, 16.0, 72), (320.0, 79, 16.0, 72),
                   (336.0, 83, 16.0, 74), (352.0, 79, 16.0, 72),
                   (368.0, 83, 16.0, 76)], jt=3)
    _table(sc, 8, [(304.0, 71, 16.0, 60), (320.0, 72, 16.0, 60),
                   (336.0, 71, 16.0, 62), (352.0, 74, 16.0, 62),
                   (368.0, 76, 16.0, 66)], jt=3)
    for k in range(8):
        base_t = 304.0 + 8.0 * k
        for p in en.triad(52, MODE, [1, 3][k % 2]):
            sc.note(12, p, base_t, 1.4, 90 + (2 if k % 2 else 0), jt=1, jv=3)
    _table(sc, 12, [(368.0, 52, 8.0, 88), (368.0, 59, 8.0, 86)], jt=1)
    for t in (320.0, 336.0, 352.0, 368.0):
        en.arp(sc, 6, [52, 59, 64, 67, 71, 76, 79, 83, 88], t, 16, 0.25, 62)
    for t in (312.5, 328.5, 344.5, 360.5, 376.5):
        sc.note(3, 79, t, 0.4, 70, jt=2, jv=3)
        sc.note(4, 79, t + 2.0, 0.4, 70, jt=2, jv=3)

    # --- turn (384-392) ---
    en.pad_block(sc, 1, 384.0, _triads([4, 7]),
                 span=4.0, size=4, lo=52, hi=76, vel=64)
    _table(sc, 2, [(384.0, 45, 2.0, 72), (386.0, 45, 2.0, 68),
                   (388.0, 38, 2.0, 66), (390.0, 38, 2.0, 62)], jt=2)
    sc.note(9, 36, 384.0, 0.25, 80, jt=0, jv=3)
    for k in range(8):
        sc.note(9, 42, 384.0 + k, 0.2, 34, jt=0, jv=3)
    _build_fills(sc, *M3)
    _risers(sc, *M3)


def _m4_long_climb(sc):
    # --- BUILD3 (392-504): the longest riser chain of the album ---
    en.pad_block(sc, 1, 392.0, _triads([1, 4]),
                 span=16.0, size=4, lo=52, hi=76, vel=46, vel_end=54)
    en.pad_block(sc, 1, 424.0, _triads(LOOP_DEGS * 2 + [4, 7]),
                 span=8.0, size=4, lo=52, hi=76, vel=50, vel_end=80)
    # Heartbeat, then the groove reassembles.
    for k in range(32):
        sc.note(9, 36, 392.0 + k, 0.25, 60 + k // 3, jt=0, jv=3)
    _groove_half(sc, 424.0, 456.0, 74, 70, 42)
    _groove_full(sc, 456.0, 488.0, 82, 78, 48, oh=54)
    _groove_full(sc, 488.0, 496.0, 88, 84, 52, oh=60, hat16=44)
    for k in range(8):
        sc.note(9, 36, 496.0 + k, 0.25, 92, jt=0, jv=3)
        sc.note(9, 42, 496.0 + k + 0.5, 0.2, 54, jt=0, jv=3)
    _snare_roll(sc, 496.0, 504.0, 64, 112)
    # Bass: halves -> loop 8ths -> tonic-pedal 8ths.
    for k in range(16):
        sc.note(2, 40, 392.0 + 2.0 * k, 1.8, 56 + (12 * k) // 16, jt=2, jv=2)
    _bass_eighths(sc, 424.0, 472.0, LOOP_ROOTS2, 68, 84)
    _bass_eighths(sc, 472.0, 504.0, [40], 84, 96)
    # The duo climbs in echoed ASCENT statements.
    for t, root in ((424.0, 64), (440.0, 67), (456.0, 69), (472.0, 71)):
        material.play_ascent(sc, 14, t, root, vel=78 + (root - 64),
                             vel_end=88 + (root - 64), jt=0)
    for t, root in ((432.0, 52), (448.0, 55), (464.0, 57), (480.0, 59)):
        material.play_ascent(sc, 15, t, root, vel=72 + (root - 52),
                             vel_end=82 + (root - 52), jt=0)
    _chug(sc, 488.0, 504.0, [40], 74, 94)
    # Lead climb-out into the flypast.
    _table(sc, 14, [(488.0, 76, 1.0, 96), (489.0, 79, 1.0, 97),
                    (490.0, 81, 1.0, 98), (491.0, 83, 1.0, 99),
                    (492.0, 84, 1.0, 100), (493.0, 86, 1.0, 101),
                    (494.0, 88, 1.0, 102), (495.0, 86, 1.0, 103),
                    (496.0, 88, 8.0, 104)], bloom=True)
    # Ostinato rejoins, then doubles to sixteenths.
    _ost_cell(sc, 440.0, 472.0, [64, 71, 76, 71], 0.5, 62, 78)
    _ost_cell(sc, 472.0, 504.0, [64, 71, 76, 79], 0.25, 78, 92)
    # Choir and brass swells (mm -> ah rides the vowel lane).
    _table(sc, 8, [(424.0, 64, 16.0, 46), (440.0, 67, 16.0, 52),
                   (456.0, 69, 16.0, 58), (472.0, 71, 16.0, 64),
                   (488.0, 76, 16.0, 70)], jt=3)
    _table(sc, 12, [(440.0, 52, 12.0, 50), (456.0, 55, 12.0, 58),
                    (472.0, 59, 12.0, 66), (488.0, 64, 12.0, 74)], jt=2)
    _table(sc, 7, [(392.0, 64, 8.0, 40), (408.0, 67, 8.0, 46),
                   (424.0, 71, 16.0, 52), (440.0, 74, 16.0, 58),
                   (456.0, 76, 16.0, 64), (472.0, 79, 16.0, 70),
                   (488.0, 83, 16.0, 76)], jt=3)
    _table(sc, 5, [(456.0, 76, 8.0, 72), (464.0, 79, 8.0, 76),
                   (472.0, 81, 8.0, 80), (480.0, 83, 8.0, 84),
                   (488.0, 86, 8.0, 88), (496.0, 88, 8.0, 92)], jt=2)
    for t in (468.0, 484.0):
        en.arp(sc, 6, [52, 59, 64, 67, 71, 76, 79, 83], t, 12, 0.25, 58)
    for i, t in enumerate((416.0, 444.0, 468.0, 492.0)):
        _post_call(sc, 3, t, [76, 79, 76], 56 + 4 * i)
        _post_call(sc, 4, t + 2.0, [71, 74, 71], 54 + 4 * i)
    _build_fills(sc, *M4)
    _risers(sc, *M4)


def _m5_flypast(sc):
    # --- DROP3 / THE STACK (504-648) ---
    _crash(sc, 504.0, 108)
    for t, v in ((520.0, 96), (536.0, 100), (568.0, 110), (584.0, 100),
                 (600.0, 96), (616.0, 94)):
        _crash(sc, t, v)
    _four_floor(sc, 504.0, 632.0, 104, 100, 66, 70, hat16=56)
    for k in range(16):
        sc.note(9, 36, 632.0 + k, 0.25, int(en.lerp(84, 68, k / 15)),
                jt=0, jv=3)
        sc.note(9, 42, 632.0 + k + 0.5, 0.2, 36, jt=0, jv=3)
    # Pad: one Em bed under the whole stack.
    en.pad_block(sc, 1, 504.0, _triads([1] * 18),
                 span=8.0, size=4, lo=52, hi=76, vel=80, vel_end=68)
    # Tonic pedal (pure pitch-class E through the stack).
    _bass_eighths(sc, 504.0, 632.0, [40], 94, 98, pop=True, jt=0)
    for k in range(16):
        sc.note(2, 40, 632.0 + k, 0.9, int(en.lerp(82, 64, k / 15)),
                jt=0, jv=2)
    # THE ORBIT (T361 quote): tick-exact sixteenth cells, 512-624.
    orbit_pitches = [en.pitch(64, material.ORBIT_MODE_361, d)
                     for d in material.ORBIT_RIFF_361]
    cell = ORBIT_SPAN[0]
    while cell < ORBIT_SPAN[1] - 1e-9:
        hot = CORE[0] <= cell < CORE[1]
        for k, p in enumerate(orbit_pitches):
            v = 88 + (8 if k == 0 else 0) + (4 if hot else 0)
            sc.note(0, p, cell + material.ORBIT_STEP_361 * k, 0.22, v,
                    jt=0, jv=0)
        cell += 2.0
    _ost_cell(sc, 624.0, 632.0, [64, 71, 76, 71], 0.5, 74, 60)
    en.autopan(sc, 0, 512.0, 120.0, lo=44, hi=84, period_beats=16.0)
    sc.cc(0, 10, 64, 633.0)
    # Hook restated +12 — the last full pass before the scream.
    _play_hook(sc, 14, 504.0, 106, transpose=12, bloom=True)
    # Wing octave bed under the hook pass (pitch-class E).
    for k in range(32):
        sc.note(15, 40 if k % 2 == 0 else 52, 504.0 + 0.5 * k, 0.36,
                92, jt=2, jv=3)
        sc.note(15, 40 if k % 2 == 0 else 52, 520.0 + 0.5 * k, 0.36,
                94, jt=2, jv=3)
    # Lead soar, approach and SCREAM REPRISE (bends only here).
    _table(sc, 14, LEAD_M5)
    _bloom(sc, 14, 544.0, 8.0)
    _bloom(sc, 14, 568.0, 16.0, peak=90)
    _bloom(sc, 14, 600.0, 6.0)
    _bloom(sc, 14, 616.0, 8.0)
    _bloom(sc, 14, 628.0, 12.0)
    sc.cc(14, 68, 90, 565.9)             # slur the approach into the peak
    sc.cc(14, 68, 0, 585.0)
    for f0 in (570.5, 574.5, 578.5):     # +2 integer-plateau bend flicks
        en.bend_ramp(sc, 14, f0, f0 + 0.5, 0.0, material.SCREAM_BEND_361,
                     steps=4)
        sc.bend(14, f0 + 1.0, material.SCREAM_BEND_361)
        en.bend_ramp(sc, 14, f0 + 1.0, f0 + 1.5, material.SCREAM_BEND_361,
                     0.0, steps=4)
    sc.bend(14, 582.0, 0.0)
    # Wing ship: chug bed then THE COUNTER-LINE (CP window 552-600) over
    # a driving low-E chug floor (pitch-class E keeps the stack consonant).
    _chug(sc, 536.0, 632.0, [40], 90, 96)
    _table(sc, 15, WING_M5_FREE, vel=88)
    _table(sc, 15, WING_M5_CP, vel=92)
    _table(sc, 15, WING_M5_OUT, vel=86)
    _bloom(sc, 15, 616.0, 8.0)
    _bloom(sc, 15, 636.0, 12.0)
    # ASCENT in 4x augmentation — choir + brass, pinned statements.
    for t, root8, root12 in AUG_STATEMENTS:
        material.play_ascent(sc, 8, t, root8, stretch=4.0, vel=82,
                             vel_end=96, jt=0, jv=0)
        material.play_ascent(sc, 12, t, root12, stretch=4.0, vel=84,
                             vel_end=98, jt=0, jv=0)
    _table(sc, 8, [(536.0, 76, 12.0, 70), (608.0, 76, 16.0, 68),
                   (624.0, 71, 16.0, 62)], jt=3)
    _table(sc, 12, [(536.0, 52, 8.0, 78), (544.0, 59, 8.0, 80)], jt=2)
    # Strings shimmer above; saw counter-soars; harp sweeps.
    _table(sc, 7, [(504.0, 88, 32.0, 72), (536.0, 83, 32.0, 72),
                   (568.0, 88, 16.0, 74), (584.0, 83, 16.0, 72),
                   (600.0, 88, 24.0, 72), (624.0, 76, 24.0, 66)], jt=3)
    _table(sc, 5, [(504.0, 88, 8.0, 96), (516.0, 83, 4.0, 90),
                   (520.0, 88, 16.0, 94), (536.0, 83, 8.0, 92),
                   (544.0, 86, 8.0, 94), (552.0, 83, 4.0, 90),
                   (556.0, 88, 4.0, 92), (560.0, 88, 6.0, 94),
                   (568.0, 88, 8.0, 90), (576.0, 88, 8.0, 90),
                   (584.0, 86, 4.0, 88), (588.0, 83, 4.0, 86),
                   (592.0, 79, 8.0, 86), (600.0, 76, 8.0, 84),
                   (608.0, 79, 8.0, 86), (616.0, 76, 8.0, 80)], jt=2)
    _bloom(sc, 5, 520.0, 16.0)
    _bloom(sc, 5, 560.0, 6.0)
    for t in (512.0, 528.0, 544.0, 592.0, 608.0):
        en.arp(sc, 6, [52, 59, 64, 71, 76, 79, 83, 88], t, 16, 0.25, 70)
    for t in (524.0, 540.0):
        sc.note(3, 79, t, 0.4, 72, jt=2, jv=3)
        sc.note(4, 79, t + 2.0, 0.4, 72, jt=2, jv=3)
    for t in (596.0, 604.0, 612.0):
        _post_call(sc, 3, t, [76, 79, 83], 72, dur=0.2)
        _post_call(sc, 4, t + 2.0, [76, 79, 83], 72, dur=0.2)
    _build_fills(sc, *M5)
    _risers(sc, *M5)


def _m6_clear_skies(sc):
    # --- Sign-off (648-728): the stage empties ---
    en.pad_block(sc, 1, 648.0, _triads([1, 6, 4, 1]),
                 span=16.0, size=4, lo=52, hi=76, vel=58, vel_end=42)
    roots = {648.0: 40, 664.0: 36, 680.0: 33, 696.0: 40}
    for seg, root in roots.items():
        for k in range(8):
            sc.note(2, root, seg + 2.0 * k, 1.9,
                    int(en.lerp(54, 44, (seg - 648.0) / 64.0)), jt=2, jv=2)
    _table(sc, 7, [(648.0, 76, 16.0, 56), (664.0, 72, 16.0, 50),
                   (680.0, 69, 16.0, 46), (696.0, 71, 16.0, 44)], jt=3)
    _table(sc, 8, [(648.0, 64, 16.0, 52), (664.0, 60, 16.0, 48),
                   (680.0, 57, 16.0, 44), (696.0, 59, 16.0, 42)], jt=3)
    _table(sc, 6, [(652.0, 76, 1.0, 46), (656.0, 71, 1.0, 44),
                   (660.0, 67, 1.0, 42), (664.0, 72, 1.0, 44),
                   (668.0, 67, 1.0, 42)], jt=2)
    for i, t in enumerate((648.0, 652.0, 656.0, 660.0)):
        sc.note(9, 36, t, 0.25, 58 - 4 * i, jt=0, jv=2)
        sc.note(9, 42, t + 2.0, 0.2, 30, jt=0, jv=2)
    sc.note(9, 36, 664.0, 0.25, 42, jt=0, jv=2)
    sc.note(9, 36, 668.0, 0.25, 40, jt=0, jv=2)
    # Morse CLEAR SKIES on the hi woodblock — pinned to material timing.
    for on, dur in material.morse_rhythm(material.MORSE_T10, 0.25):
        sc.note(9, 76, MORSE_T0 + on, dur, 52, jt=0, jv=0)
    # Tower lights: last two antiphonal pings.
    sc.note(3, 76, 700.0, 0.5, 54, jt=0, jv=2)
    sc.note(4, 76, 704.0, 0.5, 52, jt=0, jv=2)
    # Final unison E.
    en.arp(sc, 6, [52, 64, 76], 710.5, 3, 0.25, 58, gate=1.5)
    _crash(sc, UNISON_T0, 96)
    sc.note(9, 36, UNISON_T0, 0.25, 90, jt=0, jv=2)
    sc.note(2, 40, UNISON_T0, 16.0, 72, jt=0, jv=0)
    sc.note(14, 76, UNISON_T0, 14.0, 72, jt=0, jv=0)
    sc.note(15, 64, UNISON_T0, 14.0, 70, jt=0, jv=0)
    sc.note(7, 76, UNISON_T0, 14.0, 44, jt=0, jv=0)
    sc.note(7, 88, UNISON_T0, 14.0, 40, jt=0, jv=0)
    sc.note(8, 64, UNISON_T0, 14.0, 46, jt=0, jv=0)
    sc.note(8, 52, UNISON_T0, 14.0, 44, jt=0, jv=0)
    sc.note(12, 52, UNISON_T0, 14.0, 50, jt=0, jv=0)
    _bloom(sc, 14, UNISON_T0, 14.0)


BUILDERS = [_m1_muster, _m2_first_pass, _m3_second_pass,
            _m4_long_climb, _m5_flypast, _m6_clear_skies]

# ---------------------------------------------------------------------------
# Verification config (consumed by verify.py's generic checks)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {29, 39, 46, 49, 52, 61, 80, 81, 89, 114, 117, 118, 119}
CENTERED_CHANNELS = {1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (60, 84), 1: (50, 78), 2: (33, 55), 3: (59, 88), 4: (59, 88),
    5: (62, 91), 6: (48, 88), 7: (55, 88), 8: (52, 88), 10: (44, 64),
    11: (46, 60), 12: (50, 88), 13: (62, 62), 14: (64, 93), 15: (40, 80),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (338.0, 346.0)     # 730 beats at 128 bpm = 342.2 s
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 set)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ


def _tick(beat):
    return max(0, int(round(beat * _PPQ)))


def _note_ons(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _prio, data in sorted(sc.events.get(ch, []),
                                    key=lambda e: (e[0], e[1])):
        s = data[0] & 0xF0
        if s == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and data[2] == 0):
            q = pending.get(data[1])
            if q:
                out.append((q.pop(0), tick, data[1]))
    return sorted(out)


def _cc_lane(sc, ch, num):
    return sorted((t, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _bend_lane(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick, (raw - 8192) / 8192.0 * 2.0))   # semitones
    return sorted(out)


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, _p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _sounding(sc, ch, tick):
    """Pitches active at `tick` (a note starting exactly there counts)."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on <= tick < off]


def _pairwise_consonant(pitches):
    ps = sorted(set(pitches))
    for i, a in enumerate(ps):
        for b in ps[i + 1:]:
            if (b - a) % 12 not in _CONSONANT:
                return (a, b)
    return None


def _quarters(lo, hi):
    w = (hi - lo) / 4.0
    return [(lo + w * i, lo + w * (i + 1)) for i in range(4)]


def _fill_ons(sc):
    return sorted(_note_ons(sc, 10) + _note_ons(sc, 11))


def _count_in(ons, lo, hi):
    lo_t, hi_t = _tick(lo), _tick(hi)
    return sum(1 for t, _p, _v in ons if lo_t <= t < hi_t)


# ---------------------------------------------------------------------------
# Track oracles — every contractual claim of HLD section 4/T10.
# ---------------------------------------------------------------------------


def _o_muster_cameos(sc):
    fails = []
    lead, wing = _note_ons(sc, 14), _note_ons(sc, 15)

    def win(ons, lo, hi):
        return [(t, p) for t, p, _v in ons if _tick(lo) <= t < _tick(hi)]

    # T1 octaves: ASCENT on the lead, wing tick-for-tick an octave down.
    length = win(lead, 16.0, 24.0)
    wght = win(wing, 16.0, 24.0)
    if len(length) != 4 or len(wght) != 4:
        fails.append(f"octave cameo: {len(length)} lead / {len(wght)} wing "
                     f"notes, want 4/4")
    else:
        if [t for t, _ in length] != [t for t, _ in wght]:
            fails.append("octave cameo: wing onsets differ from lead")
        if any(wp != lp - 12 for (_t, lp), (_t2, wp) in zip(length, wght)):
            fails.append("octave cameo: wing is not lead - 12 everywhere")
        if [p for _, p in length] != material.ascent_pitches(64):
            fails.append("octave cameo: lead pitches are not ASCENT on E4")
    # T6 mirror about axis 63.
    lm, wm = win(lead, 32.0, 40.0), win(wing, 32.0, 40.0)
    if len(lm) < 4 or len(lm) != len(wm):
        fails.append(f"mirror cameo: {len(lm)} lead / {len(wm)} wing notes")
    else:
        if [t for t, _ in lm] != [t for t, _ in wm]:
            fails.append("mirror cameo: onsets differ")
        bad = [(lp, wp) for (_t, lp), (_t2, wp) in zip(lm, wm)
               if wp != material.mirror(lp, CAMEO_MIR_AXIS)]
        if bad:
            fails.append(f"mirror cameo: not a mirror about 63: {bad[:3]}")
    # T7 sixths.
    ls, ws = win(lead, 48.0, 56.0), win(wing, 48.0, 56.0)
    if len(ls) < 6 or len(ls) != len(ws):
        fails.append(f"sixths cameo: {len(ls)} lead / {len(ws)} wing notes")
    else:
        if [t for t, _ in ls] != [t for t, _ in ws]:
            fails.append("sixths cameo: onsets differ")
        bad = [(lp, wp) for (_t, lp), (_t2, wp) in zip(ls, ws)
               if lp - wp not in (8, 9)]
        if bad:
            fails.append(f"sixths cameo: interval not a sixth: {bad[:3]}")
    return fails


def _o_flypast_stack(sc):
    fails = []
    # (a) ORBIT_RIFF_361 ostinato, tick-exact against the material constants.
    want = [en.pitch(64, material.ORBIT_MODE_361, d)
            for d in material.ORBIT_RIFF_361]
    ons0 = {t: p for t, p, _v in _note_ons(sc, 0)}
    cell = ORBIT_SPAN[0]
    missing = 0
    while cell < ORBIT_SPAN[1] - 1e-9:
        for k, p in enumerate(want):
            t = _tick(cell + material.ORBIT_STEP_361 * k)
            if ons0.get(t) != p:
                missing += 1
        cell += 2.0
    if missing:
        fails.append(f"orbit ostinato: {missing} cell notes missing or "
                     f"wrong-pitched in {ORBIT_SPAN}")
    # (b) tonic pedal: every bass note in the stack is pitch-class E.
    bad = [t / _PPQ for t, p, _v in _note_ons(sc, 2)
           if _tick(ORBIT_SPAN[0]) <= t < _tick(ORBIT_SPAN[1])
           and p % 12 != 4]
    if bad:
        fails.append(f"tonic pedal broken at beats {bad[:4]}")
    # (c) the core: all four lanes sounding + pairwise-consonant downbeats.
    t = CORE[0]
    while t < CORE[1] - 1e-9:
        tk = _tick(t)
        orbit = _sounding(sc, 0, tk)
        asc = _sounding(sc, 8, tk) + _sounding(sc, 12, tk)
        lead = _sounding(sc, 14, tk)
        wing = _sounding(sc, 15, tk)
        for name, lane in (("orbit", orbit), ("ascent", asc),
                           ("lead", lead), ("wing", wing)):
            if not lane:
                fails.append(f"core downbeat {t:.0f}: {name} lane silent")
        clash = _pairwise_consonant(orbit + asc + lead + wing)
        if clash:
            fails.append(f"core downbeat {t:.0f}: pitches {clash} clash")
        t += 4.0
    return fails


def _o_scream_reprise(sc):
    fails = []
    spans = _note_spans(sc, 14)
    approach = [s for s in spans
                if s[2] == material.SCREAM_APPROACH_361
                and _tick(560.0) <= s[0] < _tick(568.0)]
    if not approach:
        fails.append("no approach note (91) in (560, 568)")
    peak = [s for s in spans
            if s[2] == material.SCREAM_PEAK_361
            and abs(s[0] - _tick(568.0)) <= 2
            and s[1] - s[0] >= 12 * _PPQ]
    if not peak:
        fails.append("no held peak (93) of >= 12 beats at 568")
    # Bend flicks: episodes reaching the +2 plateau inside the hold.
    bends = [(t, v) for t, v in _bend_lane(sc, 14)
             if _tick(CORE[0]) <= t <= _tick(CORE[1])]
    episodes, hot = 0, False
    for _t, v in bends:
        if not hot and abs(v - material.SCREAM_BEND_361) <= 0.02:
            episodes += 1
            hot = True
        elif hot and v < 0.5:
            hot = False
    if episodes < 2:
        fails.append(f"only {episodes} +2 bend flicks in the hold, want >= 2")
    over = [v for _t, v in _bend_lane(sc, 14)
            if v > material.SCREAM_BEND_361 + 0.02]
    if over:
        fails.append(f"bend exceeds the +2 integer plateau: {over[:3]}")
    tail = [v for t, v in _bend_lane(sc, 14) if t > _tick(586.0)]
    if any(abs(v) > 0.02 for v in tail):
        fails.append("bend not recentred after the scream")
    cc1 = [v for t, v in _cc_lane(sc, 14, 1)
           if _tick(CORE[0]) <= t <= _tick(CORE[1])]
    if not cc1 or max(cc1) < 60:
        fails.append("no CC1 bloom >= 60 over the held peak")
    return fails


def _o_ascent_augmentation(sc):
    fails = []
    for ch, root_idx in ((8, 1), (12, 2)):
        spans = {(on, p): off for on, off, p in _note_spans(sc, ch)}
        for stmt in AUG_STATEMENTS:
            t0, root = stmt[0], stmt[root_idx]
            for (on, du, semi) in material.ASCENT_CELL:
                key = (_tick(t0 + on * 4.0), root + semi)
                off = spans.get(key)
                if off is None:
                    fails.append(f"ch{ch} aug statement at {t0:.0f}: missing "
                                 f"note +{semi} at {t0 + on * 4.0:.0f}")
                elif abs((off - key[0]) - du * 4.0 * _PPQ) > 2:
                    fails.append(f"ch{ch} aug at {t0:.0f}: note +{semi} not "
                                 f"4x-stretched ({(off - key[0]) / _PPQ:.2f} "
                                 f"beats)")
    # One statement must co-span the scream hold (the simultaneity claim).
    if not any(t0 == CORE[0] for t0, _r8, _r12 in AUG_STATEMENTS):
        fails.append("no augmentation statement co-spans the scream hold")
    return fails


def _o_three_cycle_chain(sc):
    fails = []
    sums = _bar_sums(sc)
    d1 = _mean_barsum(sums, *D1)
    d2 = _mean_barsum(sums, *D2)
    d3 = _mean_barsum(sums, *D3)
    if not d1 < d2 < d3:
        fails.append(f"drop chain not rising: D1 {d1:.0f} / D2 {d2:.0f} / "
                     f"D3 {d3:.0f}")
    for tag, (lo, hi) in (("B1", B1), ("B2", B2), ("B3", B3)):
        means = [_mean_barsum(sums, qlo, qhi) for qlo, qhi in _quarters(lo, hi)]
        if any(b <= a for a, b in zip(means, means[1:])):
            fails.append(f"{tag} quarter-windows not strictly rising: "
                         f"{[round(m) for m in means]}")
    return fails


def _o_fill_escalation_x3(sc):
    fails = []
    ons = _fill_ons(sc)
    peaks = []
    for tag, (lo, hi) in (("B1", B1), ("B2", B2), ("B3", B3)):
        counts = [_count_in(ons, qlo, qhi) for qlo, qhi in _quarters(lo, hi)]
        if any(b <= a for a, b in zip(counts, counts[1:])):
            fails.append(f"{tag} fill counts not strictly rising: {counts}")
        peaks.append(max(counts))
        shapes = {sh for b, sh, _v in FILL_SCHEDULE if lo <= b < hi}
        if len(shapes) < 5:
            fails.append(f"{tag} uses only {len(shapes)} fill shapes, want 5+")
    if not peaks[0] < peaks[1] < peaks[2]:
        fails.append(f"fill peaks not rising build-over-build: {peaks}")
    # Every scheduled fill must actually land on its lane.
    lane_ons = {10: {t for t, _p, _v in _note_ons(sc, 10)},
                11: {t for t, _p, _v in _note_ons(sc, 11)}}
    for b, sh, _v in FILL_SCHEDULE:
        lib = material.FILL_LIB[sh]
        for lane, ch in (("tom", 10), ("syn", 11)):
            for off, _p, _d, _vv in lib.get(lane, ()):
                if _tick(b + off) not in lane_ons[ch]:
                    fails.append(f"scheduled fill {sh}@{b} missing its "
                                 f"{lane} note at +{off}")
                break
    # A >= 20-note unbroken run must land into every drop.
    for drop in (D1[0], D2[0], D3[0]):
        window = [t for t, _p, _v in ons
                  if _tick(drop - 8.0) <= t <= _tick(drop + 0.5)]
        best, chain, last = 0, 0, None
        chain_end = None
        for t in window:
            chain = chain + 1 if last is not None and t - last <= _PPQ // 2 \
                else 1
            if chain > best or (chain == best and True):
                best, chain_end = max(best, chain), t
            last = t
        if best < 20 or chain_end is None or chain_end < _tick(drop - 1.5):
            fails.append(f"no >=20-note unbroken fill run into drop {drop:.0f}"
                         f" (best {best})")
    # Drops are thinned: capped fill counts per full 8-bar drop window.
    for lo, hi in ((152.0, 184.0), (184.0, 216.0), (304.0, 336.0),
                   (336.0, 368.0), (504.0, 536.0), (536.0, 568.0),
                   (568.0, 600.0), (600.0, 632.0)):
        c = _count_in(ons, lo, hi)
        if c > 24:
            fails.append(f"drop window ({lo:.0f},{hi:.0f}) has {c} fill "
                         f"notes (cap 24)")
    return fails


def _o_wing_counterpoint(sc):
    fails = []
    lo, hi = _tick(CP_WINDOW[0]), _tick(CP_WINDOW[1])
    lead = [(t, p) for t, p, _v in _note_ons(sc, 14) if lo <= t < hi]
    wing = [(t, p) for t, p, _v in _note_ons(sc, 15) if lo <= t < hi]
    if len(wing) < 20:
        fails.append(f"wing counter-line too thin: {len(wing)} onsets")
        return fails
    lead_ticks = {t for t, _p in lead}
    coincident = sum(1 for t, _p in wing if t in lead_ticks)
    if coincident / len(wing) > 0.5:
        fails.append(f"{coincident}/{len(wing)} wing onsets coincide with "
                     f"the lead (want < 50%)")
    # Downbeat top-voice motion + consonance.
    downbeats = [CP_WINDOW[0] + 4.0 * i for i in range(12)]
    ltop, wtop = [], []
    for t in downbeats:
        ls = _sounding(sc, 14, _tick(t))
        ws = _sounding(sc, 15, _tick(t))
        if not ls or not ws:
            fails.append(f"downbeat {t:.0f}: a duo voice is silent")
            return fails
        ltop.append(max(ls))
        wtop.append(max(ws))
        if (ltop[-1] - wtop[-1]) % 12 not in _CONSONANT:
            fails.append(f"downbeat {t:.0f}: {ltop[-1]}/{wtop[-1]} dissonant")
    good = 0
    total = len(downbeats) - 1
    for i in range(total):
        dl = ltop[i + 1] - ltop[i]
        dw = wtop[i + 1] - wtop[i]
        if dl * dw < 0 or (dl == 0) != (dw == 0):
            good += 1
    if good / total < 0.6:
        fails.append(f"only {good}/{total} contrary/oblique motions "
                     f"(want >= 60%)")
    # Pitch-class doubling <= 25% of wing onsets.
    doubled = 0
    for t, p in wing:
        ls = _sounding(sc, 14, t)
        if ls and max(ls) % 12 == p % 12:
            doubled += 1
    if doubled / len(wing) > 0.25:
        fails.append(f"{doubled}/{len(wing)} wing onsets double the lead's "
                     f"pitch class")
    return fails


def _o_soar_sweep_risers(sc):
    fails = []
    cc74 = [v for _t, v in _cc_lane(sc, 1, 74)]
    if not cc74 or max(cc74) - min(cc74) < 60:
        fails.append("pad CC74 macro-sweep spans < 60 units")
    risers = _note_spans(sc, 13)
    for drop in (D1[0], D2[0], D3[0]):
        if not any(on < _tick(drop) and abs(off - _tick(drop)) <= _PPQ // 2
                   for on, off, _p in risers):
            fails.append(f"no riser resolving into drop {drop:.0f}")
    counts = [sum(1 for on, _off, _p in risers
                  if _tick(lo) <= on < _tick(hi))
              for lo, hi in (B1, B2, B3)]
    if not (counts[2] >= 3 and counts[2] > counts[0]
            and counts[2] > counts[1]):
        fails.append(f"BUILD3 riser chain not the longest: {counts}")
    # Portamento swoop: CC65 on, then an adjacent >= 12-semitone leap.
    cc65 = [(t, v) for t, v in _cc_lane(sc, 5, 65) if v >= 64]
    swoop = False
    saw = _note_ons(sc, 5)
    for t, _v in cc65:
        for (t1, p1, _v1), (t2, p2, _v2) in zip(saw, saw[1:]):
            if t <= t2 <= t + 2 * _PPQ and abs(p2 - p1) >= 12:
                swoop = True
    if not swoop:
        fails.append("no portamento swoop (CC65 + >=12-semitone leap) on saw")
    # A >= 6-beat held lead soar under a CC1 bloom (beyond the scream).
    holds = [(on, off) for on, off, _p in _note_spans(sc, 14)
             if off - on >= 6 * _PPQ]
    cc1 = _cc_lane(sc, 14, 1)
    if not any(any(on <= t <= off and v >= 60 for t, v in cc1)
               for on, off in holds):
        fails.append("no >= 6-beat lead soar with a CC1 bloom >= 60")
    return fails


def _o_clear_skies_morse(sc):
    fails = []
    expected = [( _tick(MORSE_T0 + on), _tick(MORSE_T0 + on + dur))
                for on, dur in material.morse_rhythm(material.MORSE_T10, 0.25)]
    actual = [(on, off) for on, off, p in _note_spans(sc, 9)
              if p == 76 and _tick(MORSE_T0) <= on < _tick(700.0)]
    if len(actual) != len(expected):
        fails.append(f"{len(actual)} woodblock symbols, want {len(expected)}")
        return fails
    for (won, woff), (aon, aoff) in zip(expected, actual):
        if aon != won or abs(aoff - woff) > 2:
            fails.append(f"morse symbol at tick {aon} drifts from the "
                         f"material timing ({won})")
            break
    others = [t for t, p, _v in _note_ons(sc, 9)
              if p != 76 and _tick(MORSE_T0) <= t < _tick(700.0)]
    if others:
        fails.append(f"{len(others)} non-woodblock kit notes under the "
                     f"morse sign-off")
    return fails


def _o_final_unison(sc):
    fails = []
    lo, hi = _tick(UNISON_T0 + 0.5), _tick(UNISON_T0 + 14.0)
    sounding_chs = 0
    for ch in (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 14, 15):
        pitches = [p for on, off, p in _note_spans(sc, ch)
                   if on < hi and off > lo]
        if pitches:
            sounding_chs += 1
            bad = [p for p in pitches if p % 12 != 4]
            if bad:
                fails.append(f"ch{ch} sounds non-E pitches {bad[:4]} in the "
                             f"final unison")
    if sounding_chs < 4:
        fails.append(f"only {sounding_chs} channels join the final unison")
    if not any(t == _tick(UNISON_T0) and p == 49
               for t, p, _v in _note_ons(sc, 9)):
        fails.append("no crash on the final unison downbeat")
    return fails


def oracles(sc, info, spans):
    return [
        ("muster_cameos", _o_muster_cameos(sc)),
        ("flypast_stack", _o_flypast_stack(sc)),
        ("scream_reprise", _o_scream_reprise(sc)),
        ("ascent_augmentation", _o_ascent_augmentation(sc)),
        ("three_cycle_chain", _o_three_cycle_chain(sc)),
        ("fill_escalation_x3", _o_fill_escalation_x3(sc)),
        ("wing_counterpoint", _o_wing_counterpoint(sc)),
        ("soar_sweep_risers", _o_soar_sweep_risers(sc)),
        ("clear_skies_morse", _o_clear_skies_morse(sc)),
        ("final_unison_e", _o_final_unison(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — trimmed inner windows, conservative margins.
# ---------------------------------------------------------------------------


def audio_checks(ctx):
    def db_of(beat0, beat1):
        i0, i1 = ctx.bar_window(beat0, beat1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    fails_stack = []
    core, muster = db_of(560.0, 592.0), db_of(8.0, 24.0)
    if core - muster < 6.0:
        fails_stack.append(f"stack core only {core - muster:.1f} dB above "
                           f"the muster (want >= 6)")
    fails_chain = []
    d1, d3 = db_of(156.0, 180.0), db_of(508.0, 532.0)
    if d3 - d1 < 0.5:
        fails_chain.append(f"DROP3 not louder than DROP1 in audio "
                           f"({d3 - d1:+.1f} dB)")
    fails_lift = []
    b2, dd2 = db_of(226.0, 242.0), db_of(308.0, 332.0)
    if dd2 - b2 < 3.0:
        fails_lift.append(f"DROP2 only {dd2 - b2:.1f} dB above BUILD2's "
                          f"strip (want >= 3)")
    fails_hush = []
    tail, peak = db_of(700.0, 710.0), db_of(560.0, 592.0)
    if peak - tail < 8.0:
        fails_hush.append(f"sign-off only {peak - tail:.1f} dB under the "
                          f"peak (want >= 8)")
    return [
        ("audio_stack_lift", fails_stack),
        ("audio_drop_chain", fails_chain),
        ("audio_drop2_lift", fails_lift),
        ("audio_signoff_hush", fails_hush),
    ]
