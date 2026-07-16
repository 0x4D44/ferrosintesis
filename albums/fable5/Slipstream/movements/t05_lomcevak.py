"""T5 — Lomcevak (the tumble).  HLD §4/T5.

The gyroscopic tumble: the aircraft departs controlled flight end-over-end.
Controlled chaos — the album's rhythm laboratory, its fastest tempo and its
densest fills.  B phrygian, 152 bpm, 4/4 with inserted 2/4 hiccup bars.

Architecture (646 beats):
  I.    Launch       0-48    bass+kit spool up; duo states ASCENT; hook preview
  II.   Tumble One  48-168   the polyrhythm engine: kit accents every 4 beats,
                             tom cycle every 3, syndrum cycle every 5 — all
                             three coincide every 60 beats (48/108/168, the
                             realignment crashes pinned); duo HOCKET flies
  III.  Gather     168-232   BUILD1: strictly-rising windows, fills escalate,
                             saw climbs in, 24-note unbroken run into the drop
  IV.   Drop One   232-296   full power: duo riff, 8-beat saw soar + CC1 bloom
  V.    Tumble Two 296-394   hiccup bars: seven 2/4 bars inserted (pinned in
                             the timesig grid), H-stutter fills announce them;
                             hocket resumes across the hiccups
  VI.   Build Two  394-458   BUILD2 (denser than BUILD1), portamento swoop
  VII.  Drop Two   458-554   > DROP1: the 3:4:5 engine rides ON TOP of a
                             four-on-floor; hocket fortissimo; the guitar/saw
                             counterpoint climax; realignment crash at 518
  VIII. Recovery   554-646   hush; final ASCENT; the three cycles tick from
                             582 and land together on the final downbeat 642

Duo formation — HOCKET: one continuous sixteenth line split between the two
ships: the chug anchor holds the even sixteenths while the melody answers on
the odd sixteenths, and the roles trade every two bars (the ships cross).
In every hocket span the merged onset grid is unbroken and the intersection
is empty (oracle-pinned).  The melody leans on C — the phrygian flat-2.
"""

from __future__ import annotations

import bisect

import conductor
import engine as en
import material

NUMBER = 5
TITLE = "Lomcevak"
FILE = "05 - Lomcevak.mid"
SEED = 20261105
COMMENT = ("Lomcevak - the gyroscopic tumble and the album's rhythm "
           "laboratory. A 3:4:5 polyrhythm engine (kit accents every 4 "
           "beats, tom cycle every 3, syndrum cycle every 5) realigns in "
           "pinned crashes; seven 2/4 hiccup bars trip the meter; the two "
           "guitars hocket one unbroken sixteenth line between them, trading "
           "roles every two bars. B phrygian, 152 bpm, the densest fills of "
           "Slipstream, and a second drop verified bigger than the first, "
           "with the three cycles landing together on the final downbeat.")

MODE = "phrygian"

# -- the grid (beats) --------------------------------------------------------
L0, T1A, G0, D1A = 0.0, 48.0, 168.0, 232.0
T2A, B2A, D2A, O0, END = 296.0, 394.0, 458.0, 554.0, 646.0
FINAL_DB = 642.0            # the recovery-lock downbeat
CYC0_OUT = 582.0            # outro cycle start: 642 - 60
HICCUPS = [308.0, 322.0, 336.0, 350.0, 364.0, 378.0, 392.0]   # 2/4 bars

_TSIGS = [(0.0, 4, 4)]
for _h in HICCUPS:
    _TSIGS += [(_h, 2, 4), (_h + 2.0, 4, 4)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Launch", L0, T1A),
        ("II. Tumble One", T1A, G0),
        ("III. Gather", G0, D1A),
        ("IV. Drop One", D1A, T2A),
        ("V. Tumble Two", T2A, B2A),
        ("VI. Build Two", B2A, D2A),
        ("VII. Drop Two", D2A, O0),
        ("VIII. Recovery", O0, END),
    ],
    tempo_map=[(0.0, 152.0)],
    time_signatures=_TSIGS,
    keysigs=[(0.0, 1, 1)],                      # B phrygian (1 sharp)
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (0, "crystal ostinato", 98, 90, 64, 50),
        (1, "warm pad", 89, 94, 64, 70),
        (2, "synth bass", 39, 110, 64, 26),
        (3, "post L", 80, 86, 18, 45),
        (4, "post R", 80, 86, 110, 45),
        (5, "saw soar", 81, 100, 64, 55),
        (6, "glock spark", 9, 82, 64, 60),
        (7, "aerial strings", 49, 86, 64, 68),
        (8, "choir", 52, 90, 64, 74),
        (9, "kit", 0, 110, 64, 36),
        (10, "melodic toms", 117, 104, 64, 45),
        (11, "synth drum", 118, 100, 64, 45),
        (12, "orchestra hit", 55, 98, 64, 55),
        (13, "riser", 119, 98, 64, 70),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 30, 108, 64, 24),
    ],
    program_changes=[(9, 0.0, 1)],              # the V3 kit
    extra_markers=[(108.0, "realign"), (518.0, "realign over the floor"),
                   (642.0, "recovery lock")],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1)],
)

# -- verification config -----------------------------------------------------
PROGRAM_WHITELIST = {9, 29, 30, 39, 49, 52, 55, 80, 81, 89, 98, 117, 118, 119}
CENTERED_CHANNELS = {0, 1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (55, 94), 1: (43, 80), 2: (35, 60), 3: (66, 96), 4: (66, 96),
    5: (59, 96), 6: (71, 103), 7: (50, 88), 8: (47, 79), 9: (35, 59),
    10: (44, 64), 11: (46, 60), 12: (47, 71), 13: (60, 64),
    14: (46, 92), 15: (46, 92),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (250.5, 261.0)               # 648 beats at 152 bpm = 255.8 s
BOUNDS_WHITELIST: list[tuple[int, float, float]] = [
    (5, 454.5, 462.0),      # the portamento swoop note sails across the seam
]

# -- polyrhythm engine constants (all lanes jt=0) -----------------------------
TOM_CYCLE_P = 45            # tom-cycle pitch (no FILL_LIB shape uses 45)
SYN_CYCLE_P = 47            # syn-cycle pitch (no FILL_LIB shape uses 47)
REALIGNS_T1 = [48.0, 108.0, 168.0]     # coincidences of the tumble-one engine
REALIGN_D2 = 518.0                     # 458 + 60, over the four-on-floor

# -- harmonic grid: (start_beat, phrygian degree) 1=Bm 2=C 3=D 4=Em 6=G 7=Am --
_GRID: list[tuple[float, int]] = (
    [(0.0, 1), (24.0, 2), (32.0, 1), (44.0, 2)]
    + [(48.0, 1), (64.0, 2), (80.0, 1), (96.0, 7), (112.0, 1), (128.0, 2),
       (144.0, 7), (160.0, 2)]
    + [(168.0, 1), (176.0, 2), (184.0, 4), (192.0, 2), (200.0, 1),
       (208.0, 2), (216.0, 7), (224.0, 2)]
    + [(b + o, d) for b in (232.0, 248.0, 264.0, 280.0)
       for o, d in ((0.0, 1), (4.0, 2), (8.0, 7), (12.0, 1))]
    + [(296.0, 1), (310.0, 2), (324.0, 1), (338.0, 7), (352.0, 2),
       (366.0, 1), (380.0, 2)]
    + [(394.0, 1), (402.0, 2), (410.0, 4), (418.0, 2), (426.0, 1),
       (434.0, 2), (442.0, 7), (450.0, 2)]
    + [(b + o, d) for b in (458.0, 474.0)
       for o, d in ((0.0, 1), (4.0, 2), (8.0, 6), (12.0, 7))]
    + [(490.0, 6), (494.0, 1), (498.0, 3), (502.0, 1), (506.0, 6),
       (510.0, 1), (514.0, 3), (518.0, 1), (522.0, 6)]
    + [(526.0, 2), (530.0, 1), (534.0, 2), (538.0, 1), (542.0, 2), (546.0, 1)]
    + [(554.0, 1), (562.0, 4), (570.0, 1), (578.0, 2), (586.0, 1),
       (602.0, 4), (618.0, 1), (634.0, 2), (642.0, 1)]
)
_GRID_BEATS = [b for b, _d in _GRID]
_DEG_ROOT_SEMIS = {1: 0, 2: 1, 3: 3, 4: 5, 6: 8, 7: 10}


def _deg_at(beat: float) -> int:
    i = bisect.bisect_right(_GRID_BEATS, beat + 1e-9) - 1
    return _GRID[max(0, i)][1]


def _root(deg: int, lo: int) -> int:
    """Chord root at or just above MIDI pitch `lo` (B=11 pitch class base)."""
    semis = _DEG_ROOT_SEMIS[deg]
    p = lo + ((47 + semis - lo) % 12)
    return p


def _chord(deg: int) -> list[int]:
    return en.triad(59, MODE, deg)


def _bloom(sc, ch, on, dur, peak=None):
    """CC1 bloom over a held note (the digest formula)."""
    if peak is None:
        peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


# ---------------------------------------------------------------------------
# THE DUO — hocket machinery.  One continuous sixteenth line: even sixteenths
# are the chug anchor (low B), odd sixteenths the melody; roles swap between
# the ships every two bars.  All notes jt=0 (the formation is oracle-pinned).
# ---------------------------------------------------------------------------

CHUG_P = 47                                     # B2, the anchor
_HOCKET_MELODY = {                               # 8 degrees per 4-beat cell
    0: [1, 2, 1, 0, 1, 2, 3, 2],                # the flat-2 bite
    1: [3, 2, 1, 2, 5, 4, 3, 2],
    2: [5, 4, 3, 2, 1, 0, 1, 2],
    3: [1, 2, 3, 4, 5, 6, 5, 4],
}
HOCKET_SPANS = [(64.0, 112.0), (120.0, 160.0),          # Tumble One
                (300.0, 336.0), (344.0, 380.0),          # Tumble Two
                (462.0, 494.0)]                          # Drop Two, ff
_HOCKET_CFG = {64.0: (71, [0, 1, 0, 2], 84, 78),
               120.0: (71, [2, 3, 0, 1], 86, 80),
               300.0: (71, [0, 2, 1, 3], 88, 80),
               344.0: (71, [3, 1, 2, 0], 90, 82),
               462.0: (83, [0, 1, 2, 3], 102, 96)}


def _hocket(sc, t0, t1):
    base, variants, vm, vc = _HOCKET_CFG[t0]
    ncells = int(round((t1 - t0) / 4.0))
    for c in range(ncells):
        cell = t0 + 4.0 * c
        degs = _HOCKET_MELODY[variants[c % len(variants)]]
        swap = (c // 2) % 2 == 1                # the ships cross every 2 bars
        mel_ch, chug_ch = (15, 14) if swap else (14, 15)
        for k in range(16):
            t = cell + 0.25 * k
            if k % 2 == 0:
                v = vc + (6 if k % 4 == 0 else 0)
                sc.note(chug_ch, CHUG_P, t, 0.22, v, jt=0, jv=2)
            else:
                p = en.pitch(base, MODE, degs[k // 2])
                v = vm + (8 if k % 8 == 1 else 0)
                sc.note(mel_ch, p, t, 0.22, v, jt=0, jv=2)


# ---------------------------------------------------------------------------
# Fills.  The album's densest schedule: all eight FILL_LIB shapes, strictly
# escalating window counts through both builds, thinned in both drops, an
# H-stutter announcing the hiccup bars, and a bespoke 24-note unbroken
# sixteenth run into each drop.
# ---------------------------------------------------------------------------

FILL_SCHEDULE: list[tuple[float, str]] = [
    # Launch
    (28.0, "A"), (44.0, "B"),
    # Tumble One
    (56.0, "A"), (70.0, "D"), (78.0, "B"), (86.0, "C"), (94.0, "F"),
    (102.0, "G"), (110.0, "E"), (118.0, "A"), (126.0, "H"), (134.0, "B"),
    (142.0, "G"), (150.0, "D"), (158.0, "C"), (166.0, "B"),
    # Gather (BUILD1): 16-beat windows count 2, 3, 4, 5
    (174.0, "A"), (182.0, "D"),
    (186.0, "C"), (192.0, "F"), (198.0, "B"),
    (202.0, "G"), (206.0, "A"), (210.0, "H"), (214.0, "E"),
    (216.0, "F"), (218.0, "C"), (221.0, "G"), (223.0, "A"), (224.5, "H"),
    # Drop One: thinned (cap 2 per window)
    (246.0, "A"), (258.0, "G"), (272.0, "A"), (288.0, "D"),
    # Tumble Two (H-stutters land 1.5 beats before a hiccup bar)
    (302.0, "D"), (306.5, "H"), (312.0, "C"), (316.0, "G"), (320.5, "H"),
    (326.0, "F"), (330.0, "B"), (340.0, "E"), (346.0, "A"), (348.5, "H"),
    (356.0, "G"), (360.0, "D"), (368.0, "C"), (372.0, "B"), (376.5, "H"),
    (384.0, "F"), (388.0, "G"), (391.0, "A"),
    # Build Two (BUILD2): 16-beat windows count 3, 4, 5, 6
    (398.0, "A"), (402.0, "D"), (408.0, "C"),
    (412.0, "B"), (416.0, "G"), (420.0, "F"), (424.0, "H"),
    (428.0, "A"), (431.0, "C"), (434.0, "E"), (438.0, "G"), (440.0, "D"),
    (442.0, "G"), (443.5, "A"), (444.0, "B"), (446.0, "C"), (448.0, "H"),
    (449.0, "E"),
    # Drop Two: thinned (cap 2 per window)
    (470.0, "A"), (486.0, "G"), (506.0, "D"), (522.0, "A"), (538.0, "G"),
    (550.0, "B"),
    # Recovery
    (566.0, "A"),
]
_BUILD_FILL_WINDOWS = {                         # build -> 16-beat windows
    "gather": [(168.0, 184.0), (184.0, 200.0), (200.0, 216.0), (216.0, 232.0)],
    "build2": [(394.0, 410.0), (410.0, 426.0), (426.0, 442.0), (442.0, 458.0)],
}
_DROP_WINDOWS = [(232.0 + 16.0 * k, 248.0 + 16.0 * k) for k in range(4)] + \
                [(458.0 + 16.0 * k, 474.0 + 16.0 * k) for k in range(6)]
PRE_DROP_RUNS = [(226.0, 232.0), (452.0, 458.0)]    # 24 unbroken sixteenths


def _fills(sc, t0, t1, vbump=0):
    for start, shape in FILL_SCHEDULE:
        if t0 <= start < t1:
            material.play_fill(sc, shape, start, vbump=vbump)


def _big_run(sc, t0):
    """24 unbroken sixteenths into a drop, toms and syn interleaved."""
    for i in range(24):
        t = t0 + 0.25 * i
        vel = int(round(en.lerp(76, 112, i / 23.0)))
        if i % 2 == 0:
            sc.note(10, 44 + i // 2, t, 0.2, vel, jt=0, jv=0)
        else:
            sc.note(11, 46 + i // 2, t, 0.2, vel, jt=0, jv=0)


# ---------------------------------------------------------------------------
# Featured note tables
# ---------------------------------------------------------------------------

# Drop One duo riff, one 8-beat phrase (offset, pitch, dur, vel); lead ship.
_D1_RIFF = [
    (0.0, 71, 1.5, 104), (1.5, 72, 0.5, 98), (2.0, 74, 1.0, 102),
    (3.0, 72, 0.5, 96), (3.5, 71, 0.5, 98), (4.0, 66, 2.0, 102),
    (6.0, 67, 0.5, 96), (6.5, 69, 0.5, 98),
]
_D1_TAIL_EVEN = (7.0, 71, 1.0, 104)
_D1_TAIL_ODD = (7.0, 72, 1.0, 102)              # the flat-2 kiss

# The counterpoint climax (494-526): guitar lead = reference line,
# saw = counter line.  Designed against the oracle: >=50% non-coincident
# onsets, >=60% contrary+oblique motion, consonant structural downbeats,
# no pitch-class doubling.
CP_T0, CP_T1 = 494.0, 526.0
_CP_GTR_PHRASE_A = [
    (0.0, 71, 1.0, 102), (1.0, 72, 0.5, 98), (1.5, 74, 1.0, 100),
    (3.0, 76, 1.0, 102), (4.0, 78, 2.0, 106), (6.0, 76, 0.75, 100),
    (7.0, 74, 0.5, 98), (7.5, 72, 0.5, 96),
]
_CP_GTR_PHRASE_B = [
    (0.0, 74, 1.0, 102), (1.0, 72, 0.5, 98), (1.5, 71, 1.5, 100),
    (3.0, 69, 1.0, 98), (4.0, 67, 2.0, 102), (6.0, 69, 0.75, 98),
    (7.0, 71, 1.0, 102),
]
_CP_GTR_PHRASE_B2 = [
    (0.0, 74, 1.0, 106), (1.0, 72, 0.5, 102), (1.5, 71, 1.5, 104),
    (3.0, 69, 1.0, 102), (4.0, 67, 2.0, 106), (6.0, 78, 2.0, 110),
]
_CP_SAW_PHRASE_A = [
    (0.0, 86, 2.0, 88), (2.0, 84, 2.0, 86), (4.0, 81, 2.0, 88),
    (6.0, 83, 2.0, 90),
]
_CP_SAW_PHRASE_B = [
    (0.0, 78, 2.0, 88), (2.0, 79, 2.0, 86), (4.0, 83, 2.0, 90),
    (6.0, 79, 2.0, 88),
]
_CP_SAW_PHRASE_B2 = [
    (0.0, 78, 2.0, 92), (2.0, 79, 2.0, 90), (4.0, 83, 4.0, 94),
]
CP_TABLE = (
    [(CP_T0 + o, p, d, v) for o, p, d, v in _CP_GTR_PHRASE_A]
    + [(CP_T0 + 8 + o, p, d, v) for o, p, d, v in _CP_GTR_PHRASE_B]
    + [(CP_T0 + 16 + o, p, d, v + 6) for o, p, d, v in _CP_GTR_PHRASE_A]
    + [(CP_T0 + 24 + o, p, d, v) for o, p, d, v in _CP_GTR_PHRASE_B2],
    [(CP_T0 + o, p, d, v) for o, p, d, v in _CP_SAW_PHRASE_A]
    + [(CP_T0 + 8 + o, p, d, v) for o, p, d, v in _CP_SAW_PHRASE_B]
    + [(CP_T0 + 16 + o, p, d, v + 4) for o, p, d, v in _CP_SAW_PHRASE_A]
    + [(CP_T0 + 24 + o, p, d, v) for o, p, d, v in _CP_SAW_PHRASE_B2],
)

# Pinned ASCENT statements: (channel, beat, root)
ASCENTS = [(14, 8.0, 59), (15, 16.0, 47), (14, 560.0, 59)]

# ---------------------------------------------------------------------------
# Texture emitters
# ---------------------------------------------------------------------------

def _pads(sc, t0, t1, span, vel, vel_end=None, size=4, lo=52, hi=76):
    n = int(round((t1 - t0) / span))
    chords = [_chord(_deg_at(t0 + i * span)) for i in range(n)]
    en.pad_block(sc, 1, t0, chords, span=span, size=size, lo=lo, hi=hi,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _choir(sc, t0, t1, span, vel, vel_end=None):
    n = int(round((t1 - t0) / span))
    chords = [_chord(_deg_at(t0 + i * span)) for i in range(n)]
    en.pad_block(sc, 8, t0, chords, span=span, size=3, lo=52, hi=74,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _ost(sc, t0, t1, step, v0, v1, octu=12):
    """Crystal ostinato: updown broken chord, harmony from the grid."""
    total = t1 - t0
    k = 0
    t = t0
    while t < t1 - 1e-9:
        pts = _chord(_deg_at(t))
        seq = [pts[0], pts[1], pts[2], pts[0] + 12, pts[2], pts[1]]
        p = seq[k % 6] + octu
        v = en.lerp(v0, v1, (t - t0) / total) + (8 if (t - t0) % 4.0 < step else 0)
        sc.note(0, p, t, step * 1.1, int(v), jt=3, jv=3)
        k += 1
        t = t0 + (k * step)


def _bass_8ths(sc, t0, t1, v0, v1=None, bite=True, pop=False):
    v1 = v0 if v1 is None else v1
    n = int(round((t1 - t0) / 0.5))
    for i in range(n):
        t = t0 + 0.5 * i
        off = (t - t0) % 4.0
        deg = _deg_at(t)
        p = _root(deg, 40)
        if bite and deg == 1 and abs(off - 3.5) < 1e-9:
            p += 1                              # the flat-2 neighbour
        v = int(en.lerp(v0, v1, i / max(1, n - 1))) + (6 if off < 0.25 else 0)
        sc.note(2, p, t, 0.4, v, jt=2, jv=3)
        if pop and abs(off - 3.75) < 1e-9:
            sc.note(2, p + 12, t + 0.25, 0.2, v - 4, jt=2, jv=3)


def _bass_16ths(sc, t0, t1, v0, v1=None):
    v1 = v0 if v1 is None else v1
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        t = t0 + 0.25 * i
        p = _root(_deg_at(t), 40)
        if (t - t0) % 1.0 >= 0.75:
            p += 12 if p < 50 else 0
        v = int(en.lerp(v0, v1, i / max(1, n - 1))) + (6 if (t - t0) % 4.0 < 0.2 else 0)
        sc.note(2, p, t, 0.2, v, jt=1, jv=3)


def _bass_holds(sc, table):
    for t, p, d, v in table:
        sc.note(2, p, t, d, v, jt=1, jv=2)


def _post_call(sc, t, vel=88):
    for i, p in enumerate((83, 84, 83)):
        sc.note(3, p, t + 0.25 * i, 0.22, vel, jt=0, jv=3)
    for i, p in enumerate((78, 79, 78)):
        sc.note(4, p, t + 2.0 + 0.25 * i, 0.22, vel - 4, jt=0, jv=3)


def _hit(sc, t, vel):
    sc.note(12, _root(_deg_at(t), 55), t, 0.9, vel, jt=0, jv=3)


def _riser(sc, t, vel):
    sc.note(13, 62, t, 4.0, vel, jt=0, jv=0)


def _crash(sc, t, vel):
    sc.note(9, 49, t, 0.4, vel, jt=0, jv=0)


def _spark(sc, t0, t1, step, vel, alt=True):
    k = 0
    t = t0
    while t < t1 - 1e-9:
        p = _root(_deg_at(t), 79) + (12 if alt and k % 2 else 0)
        sc.note(6, p, t, 1.2, vel, jt=0, jv=4)
        k += 1
        t = t0 + k * step
    return


def _snare_roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _cycles(sc, t0, t1, vt, vs, inclusive=False, ramp_from=None):
    """The 3- and 5-beat lanes of the polyrhythm engine (jt=0, jv=0)."""
    lim = t1 + 1e-9 if inclusive else t1 - 1e-9
    t = t0
    while t <= lim:
        v = vt if ramp_from is None or t < ramp_from else vt + int((t - ramp_from) // 3) * 4
        sc.note(10, TOM_CYCLE_P, t, 0.3, min(112, v), jt=0, jv=0)
        t += 3.0
    t = t0
    while t <= lim:
        v = vs if ramp_from is None or t < ramp_from else vs + int((t - ramp_from) // 5) * 6
        sc.note(11, SYN_CYCLE_P, t, 0.3, min(112, v), jt=0, jv=0)
        t += 5.0


def _lead_table(sc, table, bloom_min=2.0):
    for t, p, d, v in table:
        sc.note(14, p, t, d * 0.98, v, jt=0, jv=2)
        if d >= bloom_min:
            _bloom(sc, 14, t, d)


def _saw_table(sc, table, bloom_min=4.0):
    for t, p, d, v in table:
        sc.note(5, p, t, d * 0.99, v, jt=0, jv=2)
        if d >= bloom_min:
            _bloom(sc, 5, t, d, peak=min(90, 40 + int(round(d * 6))))


def _wing_chugs(sc, t0, t1, step, v0, v1=None, pickup=False):
    v1 = v0 if v1 is None else v1
    n = int(round((t1 - t0) / step))
    for i in range(n):
        t = t0 + step * i
        v = int(en.lerp(v0, v1, i / max(1, n - 1))) + (5 if (t - t0) % 4.0 < step else 0)
        sc.note(15, CHUG_P, t, step * 0.8, v, jt=0, jv=3)
        if pickup and abs((t - t0) % 4.0 - 3.5) < 1e-9:
            sc.note(15, CHUG_P, t + 0.25, 0.2, v - 6, jt=0, jv=3)


def _hook_solo(sc, t0, variants, base=71, vm=90, vc=82):
    """The whole hocket line on the lead ship alone (the hook preview)."""
    for c, var in enumerate(variants):
        cell = t0 + 4.0 * c
        degs = _HOCKET_MELODY[var]
        for k in range(16):
            t = cell + 0.25 * k
            if k % 2 == 0:
                sc.note(14, CHUG_P, t, 0.22, vc + (6 if k % 4 == 0 else 0),
                        jt=0, jv=2)
            else:
                sc.note(14, en.pitch(base, MODE, degs[k // 2]), t, 0.22,
                        vm + (8 if k % 8 == 1 else 0), jt=0, jv=2)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _b_launch(sc):
    # whole-timeline CC lanes, authored once
    en.cc_curve(sc, 1, 74, [(0.0, 40), (48.0, 46), (168.0, 30), (232.0, 95),
                            (296.0, 70), (394.0, 35), (458.0, 100),
                            (526.0, 100), (554.0, 80), (646.0, 28)], step=1.0)
    # kit spool-up
    for b in range(12):
        bar = 4.0 * b
        sc.note(9, 36, bar, 0.25, 70 + 2 * b, jt=0, jv=3)
        if b >= 2:
            for k in range(4):
                sc.note(9, 42, bar + k + 0.5, 0.15, 46 + 2 * b, jt=2, jv=3)
        if b >= 4:
            sc.note(9, 36, bar + 2.0, 0.25, 66 + 2 * b, jt=0, jv=3)
            for k in range(4):
                sc.note(9, 42, bar + k, 0.15, 44 + 2 * b, jt=2, jv=3)
        if b >= 6:
            sc.note(9, 38, bar + 1.0, 0.25, 60 + 3 * b, jt=0, jv=3)
            sc.note(9, 38, bar + 3.0, 0.25, 62 + 3 * b, jt=0, jv=3)
        if b >= 8:
            sc.note(9, 36, bar + 1.5, 0.2, 70 + b, jt=0, jv=3)
    _crash(sc, 32.0, 100)
    # bass: halves then eighths
    _bass_holds(sc, [(0.0, 47, 4.0, 76), (4.0, 47, 4.0, 78),
                     (8.0, 47, 4.0, 80), (12.0, 47, 4.0, 82)])
    _bass_8ths(sc, 16.0, 48.0, 84, 96)
    # pad + arp + spark
    _pads(sc, 0.0, 48.0, 8.0, 46, 58)
    _ost(sc, 16.0, 48.0, 0.5, 60, 72, octu=0)
    _spark(sc, 24.0, 48.0, 8.0, 74)
    # THE DUO: pinned ASCENT statements, then the hook preview
    material.play_ascent(sc, 14, 8.0, 59, vel=96)
    material.play_ascent(sc, 15, 16.0, 47, vel=92)
    _hook_solo(sc, 32.0, [0, 1, 0, 2])
    for k in range(8):                          # wing settles under the hook
        sc.note(15, CHUG_P, 40.0 + k, 0.45, 88, jt=1, jv=3)
    _fills(sc, L0, T1A)
    _riser(sc, 44.0, 84)


def _b_tumble1(sc):
    for t in (48.0, 108.0):                     # pinned realignment crashes
        _crash(sc, t, 122)
        _hit(sc, t, 106)
    # kit: the 4-beat accent lane under the spinning 3s and 5s
    for b in range(30):
        bar = 48.0 + 4.0 * b
        sc.note(9, 36, bar, 0.25, 118, jt=0, jv=0)      # pinned accent
        sc.note(9, 36, bar + (1.75 if b % 2 == 0 else 2.5), 0.2, 96, jt=0, jv=3)
        sc.note(9, 38, bar + 1.0, 0.25, 84, jt=0, jv=3)
        sc.note(9, 38, bar + 3.0, 0.25, 86, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.12, 52, jt=2, jv=3)
        if b % 2 == 1:
            sc.note(9, 46, bar + 3.5, 0.35, 64, jt=0, jv=3)
    _cycles(sc, 48.0, 168.0, 90, 96)
    # THE DUO hockets (formation-pinned)
    _hocket(sc, 64.0, 112.0)
    _hocket(sc, 120.0, 160.0)
    # wing holds the floor while the hocket rests
    _wing_chugs(sc, 112.0, 120.0, 0.5, 88)
    _wing_chugs(sc, 160.0, 168.0, 0.5, 90, pickup=True)
    _bass_8ths(sc, 48.0, 168.0, 86, 92)
    _pads(sc, 48.0, 168.0, 8.0, 50)
    _ost(sc, 48.0, 168.0, 0.5, 62, 66)
    _spark(sc, 56.0, 168.0, 16.0, 72)
    for t in (56.0, 72.0, 88.0, 104.0, 136.0, 152.0):
        _post_call(sc, t)
    _fills(sc, T1A, G0)


def _b_gather(sc):
    _crash(sc, 168.0, 122)                      # pinned realignment crash
    _hit(sc, 168.0, 106)
    # kit: two rising stages, snare roll into the drop
    for b in range(14):
        bar = 168.0 + 4.0 * b
        sc.note(9, 36, bar, 0.25, 96 + b, jt=0, jv=3)
        sc.note(9, 36, bar + 2.0, 0.25, 92 + b, jt=0, jv=3)
        if b >= 8:
            sc.note(9, 36, bar + 2.5, 0.2, 88 + b, jt=0, jv=3)
        sc.note(9, 38, bar + 1.0, 0.25, 82 + b, jt=0, jv=3)
        sc.note(9, 38, bar + 3.0, 0.25, 84 + b, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.12, 50 + b, jt=2, jv=3)
        if b >= 8:
            sc.note(9, 42, bar + 0.25, 0.1, 48 + b, jt=1, jv=3)
            sc.note(9, 42, bar + 2.25, 0.1, 48 + b, jt=1, jv=3)
    sc.note(9, 36, 224.0, 0.25, 108, jt=0, jv=3)
    sc.note(9, 36, 226.0, 0.25, 110, jt=0, jv=3)
    _snare_roll(sc, 228.0, 232.0, 72, 112)
    _bass_8ths(sc, 168.0, 200.0, 86, 92)
    _bass_8ths(sc, 200.0, 216.0, 92, 98, pop=True)
    _bass_16ths(sc, 216.0, 232.0, 98, 108)
    _pads(sc, 168.0, 232.0, 8.0, 50, 64)
    _ost(sc, 168.0, 200.0, 0.5, 64, 70)
    _ost(sc, 200.0, 232.0, 0.25, 70, 84)
    # strings ladder
    for i, (p, v) in enumerate(((66, 62), (67, 65), (71, 68), (72, 71),
                                (74, 74), (76, 78), (78, 81), (79, 84))):
        sc.note(7, p, 168.0 + 8.0 * i, 8.0, v, jt=2, jv=2)
    _choir(sc, 200.0, 232.0, 8.0, 54, 66)
    en.vowel_curve(sc, 8, [(200.0, 20), (232.0, 80)])
    # saw climbs in
    _saw_table(sc, [(184.0, 74, 4.0, 84), (188.0, 76, 4.0, 86),
                    (192.0, 78, 4.0, 88), (196.0, 79, 4.0, 90),
                    (200.0, 81, 6.0, 92), (206.0, 83, 10.0, 94),
                    (216.0, 84, 4.0, 96), (220.0, 83, 12.0, 98)])
    # duo: lead rising calls over wing chugs
    _lead_table(sc, [(172.0, 59, 2.0, 88), (180.0, 62, 2.0, 90),
                     (188.0, 66, 2.0, 92), (196.0, 71, 2.0, 95),
                     (204.0, 74, 2.0, 98), (212.0, 78, 2.0, 100),
                     (220.0, 79, 4.0, 102), (226.0, 83, 6.0, 104)])
    _wing_chugs(sc, 168.0, 216.0, 0.5, 84, 94)
    _wing_chugs(sc, 216.0, 232.0, 0.25, 96, 102)
    _spark(sc, 168.0, 232.0, 8.0, 74)
    _post_call(sc, 176.0)
    _post_call(sc, 208.0, vel=92)
    _hit(sc, 216.0, 96)
    _hit(sc, 224.0, 100)
    _fills(sc, G0, D1A, vbump=4)
    _big_run(sc, 226.0)
    _riser(sc, 228.0, 96)


def _b_drop1(sc):
    _crash(sc, 232.0, 124)
    _crash(sc, 264.0, 110)
    for k in range(8):
        _hit(sc, 232.0 + 8.0 * k, 104)
    # kit: full-power groove (restrained next to Drop Two's floor)
    for b in range(16):
        bar = 232.0 + 4.0 * b
        for off, v in ((0.0, 112), (1.5, 100), (2.0, 108)):
            sc.note(9, 36, bar + off, 0.22, v, jt=0, jv=3)
        sc.note(9, 38, bar + 1.0, 0.25, 102, jt=0, jv=3)
        sc.note(9, 38, bar + 3.0, 0.25, 104, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.12, 62, jt=2, jv=3)
        sc.note(9, 46, bar + 2.5, 0.35, 72, jt=0, jv=3)
    # THE DUO: the drop riff
    for k in range(8):
        t0 = 232.0 + 8.0 * k
        _lead_table(sc, [(t0 + o, p, d, v) for o, p, d, v in _D1_RIFF])
        o, p, d, v = _D1_TAIL_EVEN if k % 2 == 0 else _D1_TAIL_ODD
        _lead_table(sc, [(t0 + o, p, d, v)])
    _wing_chugs(sc, 232.0, 296.0, 0.5, 96, 100, pickup=True)
    # saw: the eight-beat soar (CC1 bloom) then answers
    _saw_table(sc, [(232.0, 83, 8.0, 96), (244.0, 84, 2.0, 92),
                    (246.0, 83, 2.0, 92), (248.0, 81, 4.0, 92),
                    (256.0, 79, 4.0, 90), (260.0, 81, 4.0, 92),
                    (264.0, 83, 8.0, 96), (276.0, 79, 4.0, 90),
                    (280.0, 81, 4.0, 92), (284.0, 83, 4.0, 94),
                    (288.0, 84, 4.0, 96), (292.0, 83, 4.0, 94)])
    _bass_8ths(sc, 232.0, 296.0, 100, 104, pop=True)
    _pads(sc, 232.0, 296.0, 8.0, 60)
    _ost(sc, 232.0, 296.0, 0.5, 72, 76)
    for i, (p, v) in enumerate(((78, 72), (79, 74), (78, 74), (79, 76))):
        sc.note(7, p, 232.0 + 16.0 * i, 16.0, v, jt=2, jv=2)
    _choir(sc, 232.0, 296.0, 8.0, 60)
    en.vowel_curve(sc, 8, [(232.0, 85), (294.0, 85)])
    _spark(sc, 232.0, 296.0, 4.0, 82)
    for t in (240.0, 256.0, 288.0):
        _post_call(sc, t, vel=90)
    _fills(sc, D1A, T2A)
    _riser(sc, 292.0, 88)

def _b_tumble2(sc):
    _crash(sc, 296.0, 112)
    bars = [(296.0 + 14.0 * g + o, ln) for g in range(7)
            for o, ln in ((0.0, 4), (4.0, 4), (8.0, 4), (12.0, 2))]
    for bar, ln in bars:
        if ln == 4:
            sc.note(9, 36, bar, 0.25, 104, jt=0, jv=3)
            sc.note(9, 36, bar + 2.5, 0.2, 96, jt=0, jv=3)
            sc.note(9, 38, bar + 1.0, 0.25, 92, jt=0, jv=3)
            sc.note(9, 38, bar + 3.0, 0.25, 94, jt=0, jv=3)
            for k in range(2 * ln):
                sc.note(9, 42, bar + 0.5 * k, 0.12, 54, jt=2, jv=3)
        else:                                   # the 2/4 hiccup bar (pinned)
            sc.note(9, 36, bar, 0.25, 112, jt=0, jv=0)
            sc.note(9, 38, bar + 1.0, 0.25, 100, jt=0, jv=0)
            for k in range(2 * ln):
                sc.note(9, 42, bar + 0.5 * k, 0.12, 58, jt=2, jv=3)
    for h in HICCUPS:                           # pinned recovery crashes
        if h + 2.0 < B2A:
            _crash(sc, h + 2.0, 116)
            sc.note(6, _root(_deg_at(h + 2.0), 79), h + 2.0, 1.2, 84,
                    jt=0, jv=3)
    # THE DUO hockets across the hiccups
    _hocket(sc, 300.0, 336.0)
    _hocket(sc, 344.0, 380.0)
    _wing_chugs(sc, 296.0, 300.0, 0.5, 90)
    _wing_chugs(sc, 336.0, 344.0, 0.5, 92, pickup=True)
    _wing_chugs(sc, 380.0, 394.0, 0.5, 92, pickup=True)
    en.run(sc, 14, 340.0, 59, MODE, list(range(1, 17)), 0.25, 84, 104,
           legato=True)
    _lead_table(sc, [(380.0, 71, 1.5, 96), (381.5, 72, 0.5, 92),
                     (382.0, 74, 2.0, 96), (384.0, 76, 1.5, 98),
                     (385.5, 74, 0.5, 94), (386.0, 72, 1.0, 94),
                     (387.0, 71, 1.0, 96), (388.0, 69, 2.0, 94),
                     (390.0, 71, 3.5, 100)])
    _bass_8ths(sc, 296.0, 394.0, 92, 96)
    _pads(sc, 296.0, 394.0, 7.0, 52)
    _ost(sc, 296.0, 394.0, 0.5, 66, 70)
    for g in range(7):
        t = 296.0 + 14.0 * g
        sc.note(7, 74 if g % 2 == 0 else 76, t, 1.5, 70, jt=0, jv=3)
        _hit(sc, t, 92)
    _choir(sc, 300.0, 380.0, 8.0, 46)
    en.vowel_curve(sc, 8, [(300.0, 15), (340.0, 45), (380.0, 25)])
    _post_call(sc, 316.0)
    _post_call(sc, 358.0, vel=90)
    _fills(sc, T2A, B2A, vbump=4)


def _b_build2(sc):
    _crash(sc, 394.0, 112)                      # resolves the last hiccup
    for b in range(16):
        bar = 394.0 + 4.0 * b
        sc.note(9, 36, bar, 0.25, 100 + b, jt=0, jv=3)
        sc.note(9, 36, bar + 2.0, 0.25, 96 + b, jt=0, jv=3)
        if b >= 8:
            sc.note(9, 36, bar + 2.5, 0.2, 92 + b, jt=0, jv=3)
        for off in (1.0, 3.0):
            if bar + off < 454.0:               # the roll owns the last bar
                sc.note(9, 38, bar + off, 0.25, 88 + b, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.12, 52 + b, jt=2, jv=3)
        if b >= 8:
            sc.note(9, 42, bar + 0.25, 0.1, 50 + b, jt=1, jv=3)
            sc.note(9, 42, bar + 2.25, 0.1, 50 + b, jt=1, jv=3)
    _snare_roll(sc, 454.0, 458.0, 78, 118)
    _bass_8ths(sc, 394.0, 426.0, 92, 100)
    _bass_16ths(sc, 426.0, 458.0, 100, 112)
    _pads(sc, 394.0, 458.0, 8.0, 56, 70)
    _ost(sc, 394.0, 458.0, 0.25, 72, 88)
    for i, (p, v) in enumerate(((67, 66), (69, 69), (71, 72), (72, 75),
                                (74, 78), (76, 81), (78, 84), (79, 88))):
        sc.note(7, p, 394.0 + 8.0 * i, 8.0, v, jt=2, jv=2)
    _choir(sc, 410.0, 458.0, 8.0, 56, 70)
    en.vowel_curve(sc, 8, [(410.0, 30), (458.0, 85)])
    _saw_table(sc, [(402.0, 76, 4.0, 86), (406.0, 78, 4.0, 88),
                    (410.0, 79, 6.0, 90), (418.0, 81, 6.0, 92),
                    (426.0, 83, 8.0, 94), (436.0, 84, 4.0, 96),
                    (440.0, 86, 6.0, 98), (446.0, 88, 4.0, 100),
                    (450.0, 86, 3.5, 100)])
    # the portamento swoop: B4 -> B5 (a full octave) sailing into Drop Two
    en.portamento_on(sc, 5, 453.9, time_cc=58)
    sc.note(5, 71, 454.0, 0.5, 102, jt=0, jv=0)
    sc.note(5, 83, 454.5, 7.5, 106, jt=0, jv=0)
    _bloom(sc, 5, 454.5, 7.5, peak=80)
    en.portamento_off(sc, 5, 462.2)
    _lead_table(sc, [(398.0, 66, 2.0, 90), (406.0, 67, 2.0, 92),
                     (414.0, 69, 2.0, 94), (422.0, 71, 2.0, 96)])
    for k in range(4):
        t0 = 426.0 + 8.0 * k
        _lead_table(sc, [(t0 + o, p, d, min(112, v + 4))
                         for o, p, d, v in _D1_RIFF])
        o, p, d, v = _D1_TAIL_EVEN if k % 2 == 0 else _D1_TAIL_ODD
        _lead_table(sc, [(t0 + o, p, d, min(112, v + 4))])
    _wing_chugs(sc, 394.0, 442.0, 0.5, 92, 100)
    _wing_chugs(sc, 442.0, 458.0, 0.25, 102, 108, pickup=False)
    _spark(sc, 394.0, 458.0, 8.0, 78)
    _post_call(sc, 402.0)
    _post_call(sc, 434.0, vel=92)
    _post_call(sc, 450.0, vel=96)
    _hit(sc, 442.0, 100)
    _hit(sc, 450.0, 102)
    _fills(sc, B2A, D2A, vbump=8)
    _big_run(sc, 452.0)
    _riser(sc, 454.0, 100)


def _b_drop2(sc):
    _crash(sc, 458.0, 126)
    _crash(sc, REALIGN_D2, 124)                 # pinned: realign on the floor
    _hit(sc, REALIGN_D2, 112)
    _crash(sc, 526.0, 116)
    for k in range(12):
        _hit(sc, 458.0 + 8.0 * k, 108)
    # four-on-floor with the 4-beat accent lane on top
    for b in range(96):
        t = 458.0 + b
        if b % 4 == 0:
            sc.note(9, 36, t, 0.25, 119, jt=0, jv=0)
        else:
            sc.note(9, 36, t, 0.25, 104, jt=0, jv=2)
        if b % 4 in (1, 3):
            sc.note(9, 39, t, 0.3, 100, jt=0, jv=3)
        sc.note(9, 46, t + 0.5, 0.35, 66, jt=0, jv=3)
        sc.note(9, 42, t + 0.25, 0.1, 56, jt=1, jv=3)
        sc.note(9, 42, t + 0.75, 0.1, 56, jt=1, jv=3)
    _cycles(sc, 458.0, 554.0, 94, 98)           # the 3s and 5s ride the floor
    # THE DUO: hocket fortissimo, then the counterpoint climax
    _hocket(sc, 462.0, 494.0)
    _lead_table(sc, CP_TABLE[0])
    _saw_table(sc, CP_TABLE[1], bloom_min=3.0)
    _wing_chugs(sc, 494.0, 546.0, 0.5, 98, 102, pickup=True)
    # the finish: lead climbs, machine-gun run, held peak with a marked bend
    _lead_table(sc, [(526.0, 83, 1.0, 106), (527.0, 84, 0.5, 102),
                     (527.5, 86, 1.5, 106), (529.0, 84, 0.5, 102),
                     (529.5, 83, 1.5, 106), (531.0, 81, 1.0, 104),
                     (532.0, 79, 0.5, 102), (532.5, 81, 1.5, 106),
                     (534.0, 83, 1.0, 108), (535.0, 84, 0.5, 104),
                     (535.5, 86, 2.5, 110)])
    en.run(sc, 14, 538.0, 59, MODE, list(range(1, 17)), 0.25, 88, 112,
           legato=True)
    sc.note(14, 83, 542.0, 12.0, 112, jt=0, jv=0)
    _bloom(sc, 14, 542.0, 12.0, peak=90)
    en.bend_ramp(sc, 14, 546.0, 547.0, 0.0, 2.0, steps=8)
    en.bend_ramp(sc, 14, 549.0, 550.0, 2.0, 0.0, steps=8)
    sc.note(15, 47, 546.0, 8.0, 100, jt=0, jv=0)
    sc.note(15, 54, 546.0, 8.0, 94, jt=0, jv=0)
    # saw finish over the top
    _saw_table(sc, [(526.0, 88, 4.0, 94), (530.0, 86, 4.0, 92),
                    (534.0, 88, 4.0, 96), (538.0, 91, 4.0, 98),
                    (542.0, 95, 10.0, 96)])
    _bass_8ths(sc, 458.0, 542.0, 106, 108, pop=True)
    _bass_16ths(sc, 542.0, 554.0, 108, 114)
    _pads(sc, 458.0, 554.0, 4.0, 64)
    _choir(sc, 458.0, 554.0, 8.0, 64)
    en.vowel_curve(sc, 8, [(458.0, 85), (552.0, 85)])
    for t, p, d, v in ((458.0, 78, 16.0, 72), (474.0, 79, 16.0, 74),
                       (490.0, 71, 8.0, 76), (498.0, 74, 8.0, 78),
                       (506.0, 71, 8.0, 78), (514.0, 74, 8.0, 80),
                       (522.0, 71, 4.0, 80), (526.0, 78, 12.0, 84),
                       (538.0, 79, 16.0, 86)):
        sc.note(7, p, t, d, v, jt=2, jv=2)
    _ost(sc, 458.0, 526.0, 0.25, 80, 84)
    _ost(sc, 526.0, 554.0, 0.5, 84, 84)
    _spark(sc, 458.0, 554.0, 4.0, 84)
    for t in (478.0, 498.0, 510.0, 530.0):
        _post_call(sc, t, vel=92)
    _fills(sc, D2A, O0, vbump=6)
    _riser(sc, 514.0, 92)


def _b_outro(sc):
    _crash(sc, 554.0, 110)
    _pads(sc, 554.0, 642.0, 8.0, 52, 42)
    for p in _chord(1):
        sc.note(1, p, 642.0, 4.0, 56, jt=0, jv=2)
    _choir(sc, 556.0, 636.0, 8.0, 46, 40)
    en.vowel_curve(sc, 8, [(554.0, 80), (566.0, 25), (630.0, 25),
                           (638.0, 88)])
    for p in (59, 62, 66):
        sc.note(8, p, 638.0, 8.0, 58, jt=0, jv=2)
    material.play_ascent(sc, 14, 560.0, 59, vel=66)     # pinned final ASCENT
    _lead_table(sc, [(596.0, 71, 2.0, 58), (604.0, 72, 2.0, 56),
                     (612.0, 71, 2.0, 54)])
    _bass_holds(sc, [(554.0, 47, 8.0, 72), (562.0, 40, 8.0, 68),
                     (570.0, 47, 8.0, 66), (578.0, 48, 8.0, 64),
                     (586.0, 47, 16.0, 60), (602.0, 40, 16.0, 58),
                     (618.0, 47, 16.0, 56), (634.0, 48, 8.0, 58)])
    _ost(sc, 556.0, 582.0, 0.5, 56, 44, octu=0)
    _ost(sc, 582.0, 614.0, 1.0, 44, 36, octu=0)
    for t, p, d, v in ((600.0, 66, 16.0, 52), (616.0, 67, 16.0, 50),
                       (632.0, 66, 10.0, 48)):
        sc.note(7, p, t, d, v, jt=2, jv=2)
    # the recovery lock: all three cycles tick from 582 and land on 642
    _cycles(sc, CYC0_OUT, FINAL_DB, 52, 50, inclusive=True, ramp_from=618.0)
    k = 0
    while CYC0_OUT + 4.0 * k <= FINAL_DB + 1e-9:
        t = CYC0_OUT + 4.0 * k
        v = 46 if t < 618.0 else 46 + int((t - 618.0) // 4) * 6
        sc.note(9, 37, t, 0.2, min(112, v), jt=0, jv=0)
        k += 1
    _riser(sc, 638.0, 72)
    _crash(sc, FINAL_DB, 122)
    _hit(sc, FINAL_DB, 102)
    sc.note(6, 95, FINAL_DB, 4.0, 88, jt=0, jv=0)
    sc.note(14, 71, FINAL_DB, 4.0, 98, jt=0, jv=0)
    _bloom(sc, 14, FINAL_DB, 4.0)
    sc.note(15, 47, FINAL_DB, 4.0, 96, jt=0, jv=0)
    sc.note(15, 54, FINAL_DB, 4.0, 90, jt=0, jv=0)
    _bass_holds(sc, [(642.0, 35, 4.0, 92)])
    _fills(sc, O0, END, vbump=-18)


BUILDERS = [_b_launch, _b_tumble1, _b_gather, _b_drop1,
            _b_tumble2, _b_build2, _b_drop2, _b_outro]

# ---------------------------------------------------------------------------
# Oracles (helpers are the proven t16 set, via the composer digest)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ
_PHRYG_PCS = {11, 0, 2, 4, 6, 7, 9}             # B phrygian pitch classes


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


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, _p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _has_on(ons_set, beat, pitch):
    return (_tick(beat), pitch) in ons_set


def _ons_set(sc, ch):
    return {(t, p) for t, p, _v in _note_ons(sc, ch)}


def _cc_at(lane, beat):
    val = None
    tk = _tick(beat)
    for t, v in lane:
        if t <= tk:
            val = v
        else:
            break
    return val


def _o_ascent(sc):
    fails = []
    for ch, t0, root in ASCENTS:
        ons = _ons_set(sc, ch)
        for on, _du, semi in material.ASCENT_CELL:
            if not _has_on(ons, t0 + on, root + semi):
                fails.append(f"ascent ch{ch}@{t0}: missing {root + semi} "
                             f"at {t0 + on}")
    return fails


def _cycle_fails(sc, name, t0, t1, inclusive=False):
    """Tom lane every 3, syn lane every 5 from t0; returns failures."""
    fails = []
    toms = _ons_set(sc, 10)
    syns = _ons_set(sc, 11)
    lim = t1 + 1e-9 if inclusive else t1 - 1e-9
    t = t0
    while t <= lim:
        if not _has_on(toms, t, TOM_CYCLE_P):
            fails.append(f"{name}: tom cycle missing at {t}")
        t += 3.0
    t = t0
    while t <= lim:
        if not _has_on(syns, t, SYN_CYCLE_P):
            fails.append(f"{name}: syn cycle missing at {t}")
        t += 5.0
    return fails


def _accent_beats(sc, pitch, lo, hi, vmin):
    return {t for t, p, v in _note_ons(sc, 9)
            if p == pitch and v >= vmin and _tick(lo) <= t <= _tick(hi)}


def _o_poly(sc):
    fails = _cycle_fails(sc, "tumble1", 48.0, 168.0)
    fails += _cycle_fails(sc, "drop2", 458.0, 554.0)
    fails += _cycle_fails(sc, "outro", CYC0_OUT, FINAL_DB, inclusive=True)
    kicks = _accent_beats(sc, 36, 0.0, END, 112)
    for k in range(30):                          # tumble1 4-beat accent lane
        if _tick(48.0 + 4.0 * k) not in kicks:
            fails.append(f"tumble1: accent kick missing at {48 + 4 * k}")
    for k in range(24):                          # drop2 accent lane
        if _tick(458.0 + 4.0 * k) not in kicks:
            fails.append(f"drop2: accent kick missing at {458 + 4 * k}")
    floor = {t for t, p, _v in _note_ons(sc, 9) if p == 36}
    for b in range(96):                          # drop2 four-on-floor
        if _tick(458.0 + b) not in floor:
            fails.append(f"drop2: floor kick missing at {458 + b}")
            break
    crashes = _accent_beats(sc, 49, 0.0, END, 118)
    for t in REALIGNS_T1 + [458.0, REALIGN_D2]:  # pinned realignment crashes
        if _tick(t) not in crashes:
            fails.append(f"realignment crash missing at {t}")
    # triple coincidences are exactly the realignments
    def triple(t0, t1, accents, inclusive=False):
        toms = {t for t, p in _ons_set(sc, 10) if p == TOM_CYCLE_P}
        syns = {t for t, p in _ons_set(sc, 11) if p == SYN_CYCLE_P}
        lo, hi = _tick(t0), _tick(t1)
        out = set()
        for tk in toms & syns & accents:
            if lo <= tk <= (hi if inclusive else hi - 1):
                out.add(tk)
        return out
    got = triple(48.0, 168.0, kicks)
    want = {_tick(48.0), _tick(108.0)}
    if got != want:
        fails.append(f"tumble1 coincidences {sorted(got)} != {sorted(want)}")
    got = triple(458.0, 554.0, kicks)
    want = {_tick(458.0), _tick(REALIGN_D2)}
    if got != want:
        fails.append(f"drop2 coincidences {sorted(got)} != {sorted(want)}")
    rims = {t for t, p, _v in _note_ons(sc, 9) if p == 37}
    got = triple(CYC0_OUT, FINAL_DB, rims, inclusive=True)
    want = {_tick(CYC0_OUT), _tick(FINAL_DB)}
    if got != want:
        fails.append(f"outro coincidences {sorted(got)} != {sorted(want)}")
    if _tick(FINAL_DB) not in crashes:
        fails.append("recovery-lock crash missing at the final downbeat")
    return fails


def _o_hocket(sc):
    fails = []
    ons14 = {t for t, _p in _ons_set(sc, 14)}
    ons15 = {t for t, _p in _ons_set(sc, 15)}
    for t0, t1 in HOCKET_SPANS:
        lo, hi = _tick(t0), _tick(t1)
        a = {t for t in ons14 if lo <= t < hi}
        b = {t for t in ons15 if lo <= t < hi}
        both = a & b
        if both:
            fails.append(f"hocket {t0}-{t1}: {len(both)} simultaneous onsets")
        grid = {_tick(t0 + 0.25 * i) for i in range(int(round((t1 - t0) * 4)))}
        union = a | b
        if union != grid:
            miss = len(grid - union)
            extra = len(union - grid)
            fails.append(f"hocket {t0}-{t1}: grid holes={miss} extras={extra}")
        share = len(a) / max(1, len(union))
        if not 0.3 <= share <= 0.7:
            fails.append(f"hocket {t0}-{t1}: lead share {share:.2f}")
    return fails


def _o_hiccup(sc):
    fails = []
    two_four = sorted(b for b, n, d in sc.timesigs if (n, d) == (2, 4))
    if two_four != HICCUPS:
        fails.append(f"2/4 grid {two_four} != {HICCUPS}")
    for h in HICCUPS:
        if (h + 2.0, 4, 4) not in [(b, n, d) for b, n, d in sc.timesigs]:
            fails.append(f"no 4/4 restore at {h + 2}")
    kit = {(t, p): v for t, p, v in _note_ons(sc, 9)}
    for h in HICCUPS:
        if kit.get((_tick(h), 36), 0) < 108:
            fails.append(f"hiccup kick missing at {h}")
        if kit.get((_tick(h + 1.0), 38), 0) < 96:
            fails.append(f"hiccup snare missing at {h + 1}")
        if kit.get((_tick(h + 2.0), 49), 0) < 108:
            fails.append(f"hiccup resolution crash missing at {h + 2}")
    stutters = [s for s, shape in FILL_SCHEDULE
                if shape == "H" and s + 1.5 in HICCUPS]
    if len(stutters) < 3:
        fails.append(f"only {len(stutters)} H-stutters announce hiccups")
    return fails


def _o_fills(sc):
    fails = []
    toms = _ons_set(sc, 10)
    syns = _ons_set(sc, 11)
    for start, shape in FILL_SCHEDULE:
        lib = material.FILL_LIB[shape]
        for off, p, _d, _v in lib.get("tom", ()):
            if not _has_on(toms, start + off, p):
                fails.append(f"fill {shape}@{start}: tom {p} missing")
                break
        for off, p, _d, _v in lib.get("syn", ()):
            if not _has_on(syns, start + off, p):
                fails.append(f"fill {shape}@{start}: syn {p} missing")
                break
    if {s for _b, s in FILL_SCHEDULE} != set("ABCDEFGH"):
        fails.append("not every FILL_LIB shape is used")
    for build, wins in _BUILD_FILL_WINDOWS.items():
        counts = [sum(1 for s, _sh in FILL_SCHEDULE if w0 <= s < w1)
                  for w0, w1 in wins]
        if any(b <= a for a, b in zip(counts, counts[1:])):
            fails.append(f"{build} fill counts not strictly rising: {counts}")
        shapes = {sh for s, sh in FILL_SCHEDULE
                  if wins[0][0] <= s < wins[-1][1]}
        if len(shapes) < 5:
            fails.append(f"{build}: only {len(shapes)} distinct shapes")
    for w0, w1 in _DROP_WINDOWS:
        c = sum(1 for s, _sh in FILL_SCHEDULE if w0 <= s < w1)
        if c > 2:
            fails.append(f"drop window {w0}: {c} fills (not thinned)")
    for t0, t1 in PRE_DROP_RUNS:
        merged = {t for t, _p in toms | syns if _tick(t0) <= t < _tick(t1)}
        grid = [_tick(t0 + 0.25 * i) for i in range(int(round((t1 - t0) * 4)))]
        covered = [t for t in grid if t in merged]
        if len(covered) < 20 or covered != grid:
            fails.append(f"pre-drop run at {t0}: {len(covered)}/24 slots")
    return fails


def _o_contour(sc):
    fails = []
    sums = _bar_sums(sc)
    for name, (w0, w1, w2) in (("gather", (168.0, 200.0, 232.0)),
                               ("build2", (394.0, 426.0, 458.0))):
        a = _mean_barsum(sums, w0, w1)
        b = _mean_barsum(sums, w1, w2)
        if b <= a * 1.02:
            fails.append(f"{name}: window mass not rising ({a:.0f} -> {b:.0f})")
    d1 = _mean_barsum(sums, D1A, T2A)
    d2 = _mean_barsum(sums, D2A, O0)
    if d2 <= d1 * 1.05:
        fails.append(f"drop2 mass {d2:.0f} not > drop1 {d1:.0f} (+5%)")
    hush = _mean_barsum(sums, 558.0, 586.0)
    if hush >= 0.5 * d2:
        fails.append(f"recovery hush {hush:.0f} >= 50% of drop2 {d2:.0f}")
    return fails


def _o_phrygian(sc):
    fails = []
    for ch in (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 14, 15):
        bad = [(t, p) for t, p, _v in _note_ons(sc, ch)
               if p % 12 not in _PHRYG_PCS]
        if bad:
            fails.append(f"ch{ch}: {len(bad)} non-phrygian notes, "
                         f"first {bad[0]}")
    flat2 = sum(1 for ch in (0, 2, 5, 14, 15)
                for _t, p, _v in _note_ons(sc, ch) if p % 12 == 0)
    if flat2 < 80:
        fails.append(f"flat-2 count {flat2} < 80")
    for t0, t1 in HOCKET_SPANS:
        c = sum(1 for ch in (14, 15) for t, p, _v in _note_ons(sc, ch)
                if p % 12 == 0 and _tick(t0) <= t < _tick(t1))
        if c < 8:
            fails.append(f"hocket {t0}: only {c} flat-2 bites")
    return fails


def _o_soar(sc):
    fails = []
    lane74 = _cc_lane(sc, 1, 74)
    vals = [v for _t, v in lane74]
    if not vals or max(vals) - min(vals) < 60:
        fails.append("pad CC74 macro-sweep spans < 60")
    for b0, b1 in ((G0, D1A), (B2A, D2A)):
        v0, v1 = _cc_at(lane74, b0), _cc_at(lane74, b1)
        if v0 is None or v1 is None or v1 - v0 < 40:
            fails.append(f"CC74 not sweeping up across build {b0}-{b1}")
    risers = _ons_set(sc, 13)
    for w0 in (228.0, 454.0, 638.0):
        if not any(_tick(w0) <= t < _tick(w0 + 4.0) for t, _p in risers):
            fails.append(f"no riser into the drop at {w0}")
    # the >=6-beat drop-one soar under a CC1 bloom
    lane1 = _cc_lane(sc, 5, 1)
    soars = [(on, off) for on, off, _p in _note_spans(sc, 5)
             if _tick(D1A) <= on < _tick(T2A) and off - on >= 6 * _PPQ]
    if not soars:
        fails.append("no >=6-beat saw soar in drop one")
    elif not any(on <= t <= off and v >= 60 for on, off in soars
                 for t, v in lane1):
        fails.append("drop-one soar has no CC1 bloom >= 60")
    # the portamento swoop: CC65 on, then a >=12-semitone note pair
    lane65 = _cc_lane(sc, 5, 65)
    if _cc_at(lane65, 454.4) != 127:
        fails.append("portamento switch not on for the swoop")
    ons5 = _ons_set(sc, 5)
    if not (_has_on(ons5, 454.0, 71) and _has_on(ons5, 454.5, 83)):
        fails.append("swoop notes 71 -> 83 missing")
    return fails


def _pitch_at(spans, beat):
    tk = _tick(beat)
    for on, off, p in spans:
        if on <= tk + 1 < off:
            return p
    return None


def _o_counter(sc):
    fails = []
    lo, hi = _tick(CP_T0), _tick(CP_T1)
    a_ons = {t for t, _p in _ons_set(sc, 14) if lo <= t < hi}
    b_ons = {t for t, _p in _ons_set(sc, 5) if lo <= t < hi}
    union = a_ons | b_ons
    if not union:
        return ["counterpoint window is empty"]
    shared = len(a_ons & b_ons) / len(union)
    if shared > 0.5:
        fails.append(f"coincident onsets {shared:.2f} > 0.5")
    sp14 = [s for s in _note_spans(sc, 14) if lo <= s[0] < hi]
    sp5 = [s for s in _note_spans(sc, 5) if lo <= s[0] < hi]
    good = total = 0
    doubled = defined = 0
    prev = None
    b = CP_T0 + 1.0
    while b < CP_T1 - 1e-9:
        pa, pb = _pitch_at(sp14, b), _pitch_at(sp5, b)
        if pa is not None and pb is not None:
            defined += 1
            if pa % 12 == pb % 12:
                doubled += 1
            if prev is not None:
                da, db = pa - prev[0], pb - prev[1]
                total += 1
                if da * db < 0 or da == 0 or db == 0:
                    good += 1
            prev = (pa, pb)
        else:
            prev = None
        b += 1.0
    if total == 0 or good / total < 0.6:
        fails.append(f"contrary+oblique {good}/{total} < 60%")
    if defined and doubled / defined > 0.25:
        fails.append(f"pitch-class doubling {doubled}/{defined} > 25%")
    db = CP_T0
    while db <= 522.0 + 1e-9:
        pa, pb = _pitch_at(sp14, db), _pitch_at(sp5, db)
        if pa is not None and pb is not None \
                and (pa - pb) % 12 not in _CONSONANT:
            fails.append(f"downbeat {db}: interval {(pa - pb) % 12} dissonant")
        db += 4.0
    return fails


def _o_layers(sc):
    lo, hi = _tick(CP_T0), _tick(CP_T1)
    live = {ch for ch in sc.events
            if any(on < hi and off > lo for on, off, _p in _note_spans(sc, ch))}
    if len(live) < 15:
        return [f"only {len(live)} channels sounding at the climax: "
                f"{sorted(live)}"]
    return []


def oracles(sc, info, spans):
    return [
        ("ascent_statements", _o_ascent(sc)),
        ("polyrhythm_3_4_5", _o_poly(sc)),
        ("duo_hocket", _o_hocket(sc)),
        ("hiccup_bars", _o_hiccup(sc)),
        ("fills_all_shapes", _o_fills(sc)),
        ("build_drop_contour", _o_contour(sc)),
        ("phrygian_flavor", _o_phrygian(sc)),
        ("soar_sweep", _o_soar(sc)),
        ("counterpoint_climax", _o_counter(sc)),
        ("climax_layers", _o_layers(sc)),
    ]
