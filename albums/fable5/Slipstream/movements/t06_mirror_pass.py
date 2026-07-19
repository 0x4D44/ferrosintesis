"""T6 — Mirror Pass (HLD section 4, T6).

Two aircraft fly toward each other, one inverted — the mirror pass.  The
album's contrapuntal centrepiece, C aeolian, 120 bpm, ~4:49.

The duo formation is the MIRROR CANON: for every note in a canon span the
wing ship (ch15) plays `mirror(lead(t - lag), AXIS)` — the lead ship's line
reflected about the pinned axis F4 = 65 (the reflection that maps C aeolian
onto itself), delayed by the lag, tick-exact and velocity-shaped
(wing = lead - 6).  PASS ONE and DROP ONE fly the canon at a 2-beat lag;
DROP TWO tightens it to 1 beat and adds the choir as a third, free line.
The interlude hands the canon pair to choir + saw while the guitars rest,
and the resolution lands both ships on the axis pitch itself, in unison.

Architecture (movement grid, 4/4 at 120):
  I    0-40    Approach — pads, the axis tone alone (saw holds F4)
  II   40-136  Pass One — the canon, lag 2 (lead 44-131.5, wing 46-133.5)
  III  136-184 Build One — four-on-floor, fill escalation, soar, ASCENT
  IV   184-280 Drop One — canon (lag 2, +12) OVER the floor
  V    280-360 Interlude — guitars silent; saw quotes the cantus, choir
               counters in verified free counterpoint
  VI   360-408 Build Two — bigger: rising windows verified over Build One's
  VII  408-520 Drop Two — verified > Drop One; canon lag 1 + choir line
  VIII 520-576 Resolution — both ships land on F4=65 in unison, then sink
               to a unison C

Downbeat consonance of the canon is arithmetic, designed in: with axis 65,
interval(lead_t, wing_t) = (lead_t + lead_{t-lag} + 2) mod 12, so the cantus
tables were generated so every bar-line pair sum falls in the consonant set.
"""

from __future__ import annotations

import engine as en
import material
import conductor

NUMBER = 6
TITLE = "Mirror Pass"
FILE = "06 - Mirror Pass.mid"
SEED = 20261106

COMMENT = (
    "Mirror Pass - the mirror canon. Two guitars fly at each other, one "
    "inverted: the wing ship plays the lead ship's line reflected about F4 "
    "and delayed two beats, tick-exact for whole sections; the second drop "
    "tightens the canon to a single beat and adds a free choir line. The "
    "interlude hands the pair to choir and saw while the guitars rest, and "
    "both ships land on the axis pitch in unison to close.")

MODE = "aeolian"
BASE2 = 36                     # C2 — bass root octave
AXIS = 65                      # F4 — the mirror axis (fixes C aeolian)
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ

END = 576.0

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Approach - the axis tone", 0.0, 40.0),
        ("II. Pass One - canon at two beats", 40.0, 136.0),
        ("III. Build One", 136.0, 184.0),
        ("IV. Drop One - canon over the floor", 184.0, 280.0),
        ("V. Interlude - the handoff", 280.0, 360.0),
        ("VI. Build Two", 360.0, 408.0),
        ("VII. Drop Two - canon at one beat", 408.0, 520.0),
        ("VIII. Resolution - unison on the axis", 520.0, 576.0),
    ],
    tempo_map=[(0.0, 120.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -3, 1)],                     # C minor
    channels=[
        (0, "crystal arp", 98, 96, 54, 40),
        (1, "mirror pad", 89, 100, 64, 60),
        (2, "synth bass", 39, 112, 64, 24),
        (3, "post L pizz", 45, 100, 18, 45),
        (4, "post R glock", 9, 92, 110, 45),
        (5, "saw soar", 81, 104, 64, 55),
        (6, "harp", 46, 98, 74, 55),
        (7, "aerial strings", 49, 92, 64, 66),
        (8, "choir", 52, 100, 64, 62),
        (9, "kit", 0, 110, 64, 30),
        (10, "melodic toms", 117, 102, 48, 35),
        (11, "syn drum", 118, 102, 80, 35),
        (12, "orchestra hit", 55, 104, 64, 45),
        (13, "riser", 119, 96, 64, 70),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 112, 64, 26),
    ],
    program_changes=[(9, 0.0, 25)],   # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One
    extra_markers=[
        (44.0, "lead ship in"),
        (46.0, "wing ship - inverted, two beats behind"),
        (180.0, "ascent"),
        (412.0, "canon tightens to one beat"),
        (520.0, "unison landing on the axis"),
    ],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

PROGRAM_WHITELIST = {98, 89, 39, 45, 9, 81, 46, 49, 52, 117, 118, 55, 119, 29}
CENTERED_CHANNELS = {1, 2, 5, 7, 8, 9, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (58, 96), 1: (48, 80), 2: (30, 53), 3: (55, 86), 4: (67, 96),
    5: (55, 92), 6: (48, 92), 7: (46, 84), 8: (48, 79), 10: (44, 64),
    11: (46, 60), 12: (36, 74), 13: (60, 64), 14: (55, 92), 15: (38, 86),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (285.0, 293.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Harmony grid — one scale degree per 4-beat bar, 144 bars
# ---------------------------------------------------------------------------

DEGS = (
    [1, 1, 6, 6, 3, 3, 7, 7, 1, 1]                                    # I
    + [1, 1, 6, 6, 3, 3, 7, 7, 1, 1, 6, 6,
       3, 3, 7, 7, 1, 1, 6, 6, 7, 7, 1, 1]                            # II
    + [4, 4, 6, 6, 7, 7, 1, 1, 6, 7, 7, 7]                            # III
    + [1, 6, 3, 7] * 6                                                # IV
    + [6, 3, 4, 1] * 5                                                # V
    + [4, 4, 6, 6, 7, 7, 1, 6, 7, 7, 7, 7]                            # VI
    + [1, 6, 3, 7] * 6 + [6, 7, 1, 1]                                 # VII
    + [4, 4, 1, 5] + [1] * 10                                         # VIII
)
assert len(DEGS) == 144


def _deg_at(t: float) -> int:
    return DEGS[max(0, min(143, int(t // 4)))]


def _root2(t: float) -> int:
    return en.pitch(BASE2, MODE, _deg_at(t))


def _root3(t: float) -> int:
    return en.pitch(BASE2 + 12, MODE, _deg_at(t))


# ---------------------------------------------------------------------------
# The cantus tables (generated offline against the mirror arithmetic:
# every bar-line pair (lead_t, lead_{t-lag}) has (a+b) mod 12 in the set
# {10,1,2,3,5,6,7} == {(c-2) mod 12 : c consonant}, so lead-vs-wing is
# consonant on every structural downbeat by construction — then PROVEN
# from the Score by mirror_canon_exact / three_lines_drop2 below.)
# ---------------------------------------------------------------------------

C1 = [  # (onset, pitch, dur, vel) — 22 bars, the lag-2 cantus
    (0, 67, 1.95, 86), (2, 65, 1.95, 83), (4, 62, 0.95, 84), (5, 60, 0.95, 78),
    (6, 58, 1.95, 83), (8, 60, 1.95, 87), (10, 62, 0.95, 82), (11, 63, 0.95, 79),
    (12, 65, 0.95, 85), (14, 67, 1.95, 84), (16, 68, 0.95, 85), (17, 70, 0.95, 79),
    (18, 72, 1.95, 84), (20, 74, 1.45, 85), (21.5, 75, 0.45, 79), (22, 77, 0.95, 82),
    (23, 75, 0.95, 79), (24, 74, 0.95, 86), (25, 75, 0.45, 80), (25.5, 77, 0.45, 80),
    (26, 75, 0.95, 83), (27, 74, 0.45, 80), (27.5, 75, 0.45, 80), (28, 74, 1.95, 88),
    (30, 72, 1.95, 85), (32, 74, 0.95, 86), (33, 75, 0.95, 80), (34, 74, 1.95, 85),
    (36, 72, 0.45, 87), (36.5, 74, 0.45, 81), (37, 75, 0.95, 81), (38, 77, 1.45, 84),
    (39.5, 75, 0.45, 81), (40, 74, 1.45, 87), (41.5, 72, 0.45, 81), (42, 70, 0.95, 84),
    (43, 68, 0.95, 81), (44, 67, 1.95, 89), (46, 65, 0.95, 84), (47, 67, 0.95, 81),
    (48, 68, 0.95, 87), (49, 70, 0.45, 81), (49.5, 68, 0.45, 81), (50, 67, 0.95, 84),
    (51, 68, 0.45, 81), (51.5, 70, 0.45, 81), (52, 68, 1.45, 88), (53.5, 67, 0.45, 82),
    (54, 65, 0.95, 85), (55, 63, 0.95, 82), (56, 62, 1.95, 90), (58, 63, 1.95, 87),
    (60, 62, 0.45, 88), (60.5, 63, 0.45, 82), (61, 65, 0.95, 82), (62, 63, 1.45, 85),
    (63.5, 62, 0.45, 82), (64, 60, 0.95, 89), (65, 58, 0.95, 83), (66, 60, 1.95, 88),
    (68, 62, 0.95, 89), (69, 63, 0.45, 83), (69.5, 65, 0.45, 83), (70, 67, 0.95, 86),
    (71, 65, 0.45, 83), (71.5, 63, 0.45, 83), (72, 60, 1.45, 89), (73.5, 58, 0.45, 83),
    (74, 60, 0.95, 86), (75, 62, 0.95, 83), (76, 63, 1.95, 91), (78, 65, 0.95, 86),
    (79, 67, 0.95, 83), (80, 68, 0.95, 90), (81, 70, 0.95, 84), (82, 72, 1.95, 89),
    (84, 70, 3.45, 92),
]

C2 = [  # (onset, pitch, dur, vel) — 24 bars, the lag-1 cantus (Drop Two)
    (0, 72, 0.95, 92), (1, 70, 0.45, 86), (1.5, 68, 0.45, 86), (2, 67, 0.95, 86),
    (3, 68, 0.95, 88), (4, 70, 0.45, 92), (4.5, 72, 0.45, 86), (5, 74, 0.45, 86),
    (5.5, 75, 0.45, 86), (6, 77, 0.95, 86), (7, 79, 0.95, 88), (8, 75, 0.45, 93),
    (8.5, 74, 0.45, 87), (9, 72, 0.45, 87), (9.5, 70, 0.45, 87), (10, 68, 0.45, 87),
    (10.5, 70, 0.45, 87), (11, 72, 0.95, 89), (12, 74, 1.45, 93), (13.5, 75, 0.45, 87),
    (14, 77, 0.95, 87), (15, 79, 0.45, 89), (15.5, 77, 0.45, 87), (16, 75, 0.45, 93),
    (16.5, 77, 0.45, 87), (17, 79, 0.45, 87), (17.5, 77, 0.45, 87), (18, 75, 0.95, 87),
    (19, 74, 0.95, 89), (20, 72, 0.95, 93), (21, 74, 0.45, 87), (21.5, 72, 0.45, 87),
    (22, 74, 0.95, 87), (23, 72, 0.95, 89), (24, 70, 0.45, 94), (24.5, 72, 0.45, 88),
    (25, 74, 0.95, 88), (26, 75, 0.45, 88), (26.5, 77, 0.45, 88), (27, 75, 0.45, 90),
    (27.5, 74, 0.45, 88), (28, 75, 1.45, 94), (29.5, 74, 0.45, 88), (30, 72, 0.95, 88),
    (31, 70, 0.45, 90), (31.5, 68, 0.45, 88), (32, 67, 0.45, 94), (32.5, 65, 0.45, 88),
    (33, 63, 0.45, 88), (33.5, 62, 0.45, 88), (34, 60, 0.95, 88), (35, 62, 0.95, 90),
    (36, 63, 0.45, 94), (36.5, 62, 0.45, 88), (37, 60, 0.45, 88), (37.5, 62, 0.45, 88),
    (38, 63, 0.45, 88), (38.5, 65, 0.45, 88), (39, 67, 0.95, 90), (40, 68, 0.95, 95),
    (41, 70, 0.45, 89), (41.5, 68, 0.45, 89), (42, 67, 0.95, 89), (43, 65, 0.95, 91),
    (44, 68, 1.45, 95), (45.5, 67, 0.45, 89), (46, 65, 0.95, 89), (47, 63, 0.45, 91),
    (47.5, 62, 0.45, 89), (48, 63, 0.45, 95), (48.5, 62, 0.45, 89), (49, 60, 0.45, 89),
    (49.5, 62, 0.45, 89), (50, 60, 0.95, 89), (51, 62, 0.95, 91), (52, 60, 0.45, 95),
    (52.5, 62, 0.45, 89), (53, 63, 0.95, 89), (54, 65, 0.45, 89), (54.5, 67, 0.45, 89),
    (55, 68, 0.45, 91), (55.5, 67, 0.45, 89), (56, 65, 0.95, 96), (57, 63, 0.45, 90),
    (57.5, 62, 0.45, 90), (58, 63, 0.95, 90), (59, 65, 0.95, 92), (60, 68, 0.45, 96),
    (60.5, 70, 0.45, 90), (61, 72, 0.45, 90), (61.5, 74, 0.45, 90), (62, 72, 0.95, 90),
    (63, 70, 0.95, 92), (64, 68, 0.45, 96), (64.5, 70, 0.45, 90), (65, 72, 0.45, 90),
    (65.5, 70, 0.45, 90), (66, 68, 0.45, 90), (66.5, 67, 0.45, 90), (67, 65, 0.95, 92),
    (68, 68, 1.45, 96), (69.5, 67, 0.45, 90), (70, 65, 0.95, 90), (71, 63, 0.45, 92),
    (71.5, 62, 0.45, 90), (72, 63, 0.95, 97), (73, 65, 0.45, 91), (73.5, 63, 0.45, 91),
    (74, 62, 0.95, 91), (75, 60, 0.95, 93), (76, 62, 0.45, 97), (76.5, 63, 0.45, 91),
    (77, 65, 0.45, 91), (77.5, 67, 0.45, 91), (78, 68, 0.95, 91), (79, 70, 0.95, 93),
    (80, 72, 0.45, 97), (80.5, 74, 0.45, 91), (81, 75, 0.95, 91), (82, 77, 0.45, 91),
    (82.5, 79, 0.45, 91), (83, 77, 0.45, 93), (83.5, 75, 0.45, 91), (84, 74, 1.45, 97),
    (85.5, 72, 0.45, 91), (86, 70, 0.95, 91), (87, 68, 0.45, 93), (87.5, 67, 0.45, 91),
    (88, 65, 0.45, 98), (88.5, 67, 0.45, 92), (89, 68, 0.45, 92), (89.5, 67, 0.45, 92),
    (90, 65, 0.95, 92), (91, 63, 0.95, 94), (92, 62, 3.45, 98),
]

# Drop One flies the first 21 bars of the cantus an octave up (pcs — and
# therefore all mirror consonances — are unchanged).
C1_D1 = [nt for nt in C1 if nt[0] < 84.0]
# The interlude saw quote: the cantus' first 15 bars, untransposed.
QUOTE = [nt for nt in C1 if nt[0] < 60.0]

ICHOIR = [  # interlude counterline (onset rel to 284, pitch, dur)
    (2.75, 58, 3.85), (6.75, 63, 3.85), (10.75, 62, 3.85), (14.75, 60, 3.85),
    (18.75, 58, 3.85), (22.75, 58, 3.85), (26.75, 58, 3.85), (30.75, 58, 3.85),
    (34.75, 56, 3.85), (38.75, 55, 3.85), (42.75, 58, 3.85), (46.75, 60, 3.85),
    (50.75, 60, 3.85), (54.75, 65, 3.85),
]

D2CHOIR = [  # Drop Two third line (onset rel to 412, pitch, dur)
    (2.5, 67, 3.9), (6.5, 67, 3.9), (10.5, 67, 3.9), (14.5, 67, 3.9),
    (18.5, 68, 3.9), (22.5, 74, 3.9), (26.5, 72, 3.9), (30.5, 72, 3.9),
    (34.5, 72, 3.9), (38.5, 72, 3.9), (42.5, 72, 3.9), (46.5, 72, 3.9),
    (50.5, 72, 3.9), (54.5, 70, 3.9), (58.5, 72, 3.9), (62.5, 72, 3.9),
    (66.5, 72, 3.9), (70.5, 72, 3.9), (74.5, 74, 3.9), (78.5, 68, 3.9),
    (82.5, 65, 3.9), (86.5, 70, 3.9), (90.5, 70, 3.9),
]

# Canon spans: (lead_t0, lead_t1, lag, octave shift, vel shift, table).
CANON_SPANS = [
    (44.0, 132.0, 2.0, 0, -2, C1),          # Pass One
    (188.0, 272.0, 2.0, 12, 12, C1_D1),     # Drop One
    (412.0, 508.0, 1.0, 0, 6, C2),          # Drop Two
]

# Resolution: both ships land on the axis in unison, then sink to C.
RES_DUO = [
    (520.0, 65, 7.9, 96), (528.0, 63, 3.9, 90),
    (532.0, 62, 3.9, 88), (536.0, 60, 15.9, 92),
]

# ---------------------------------------------------------------------------
# Fill and riser schedules (all jt=0 — signatures stay exact)
# ---------------------------------------------------------------------------

FILL_SCHEDULE = [
    # Pass One — sparse punctuation
    (67.0, "A", -6), (99.0, "D", -4), (131.0, "A", -4),
    # Build One — three 16-beat windows, strictly rising counts (11/17/39)
    (139.0, "A", 0), (147.0, "D", 0),
    (155.0, "B", 4), (163.0, "C", 4),
    (171.0, "H", 8), (175.0, "G", 8),
    (179.0, "A", 10), (180.0, "F", 10), (181.0, "E", 10),  # 22-note chain
    # Drop One — thinned
    (199.0, "A", 6), (215.0, "H", 6), (231.0, "A", 6), (247.0, "G", 6),
    (263.0, "D", 6),
    # Interlude — whispers
    (311.0, "A", -16), (339.0, "D", -14),
    # Build Two — windows 14/20/39
    (363.0, "D", 2), (367.0, "A", 2), (371.0, "A", 2),
    (379.0, "B", 6), (383.0, "C", 6), (387.0, "A", 6),
    (393.0, "G", 10),
    (402.0, "H", 10), (403.5, "A", 10), (404.5, "F", 12), (405.0, "E", 12),
    # Drop Two — thinned
    (423.0, "A", 8), (439.0, "H", 8), (455.0, "G", 8), (471.0, "D", 8),
    (487.0, "B", 8), (503.0, "A", 8),
]

BUILD_WINDOWS = {
    "build one": [(136.0, 152.0), (152.0, 168.0), (168.0, 184.0)],
    "build two": [(360.0, 376.0), (376.0, 392.0), (392.0, 408.0)],
}
DROP_STARTS = [184.0, 408.0]

RISERS = [  # (beat, dur, vel) — ch13 GM119 reverse cymbal, pitch 62
    (176.0, 7.9, 88), (244.0, 4.0, 66), (400.0, 7.9, 96),
    (452.0, 4.0, 70), (484.0, 4.0, 74), (512.0, 7.5, 78),
]

HITS = [  # (beat, vel) — ch12 GM55, pitch = chord root (computed)
    (184.0, 100), (200.0, 98), (214.5, 92), (216.0, 100), (232.0, 98),
    (246.5, 92), (248.0, 100), (264.0, 98),
    (408.0, 106), (416.0, 100), (424.0, 102), (432.0, 100), (440.0, 104),
    (448.0, 100), (456.0, 102), (464.0, 100), (472.0, 104), (480.0, 100),
    (488.0, 102), (496.0, 100), (504.0, 104), (508.0, 106), (512.0, 108),
    (516.0, 104),
    (520.0, 86),
]

POSTS = [  # (call beat, vel): ch3 pizz call, ch4 glock mirrored answer at +2
    (64.0, 70), (96.0, 72), (128.0, 74),
    (206.5, 88), (238.5, 88), (270.5, 88),
    (430.5, 92), (462.5, 92), (494.5, 92),
]
POST_CALL = [(0.0, 72), (0.5, 67), (1.0, 63)]
POST_ANS = [(0.0, 82), (0.5, 87), (1.0, 91)]   # the call mirrored about 77

# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


def _bloom(sc, ch, on, dur):
    peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _emit_canon(sc, t0, table, lag, oct_shift, vel_shift):
    for on, p, dur, vel in table:
        lp = p + oct_shift
        lv = min(112, vel + vel_shift)
        sc.note(14, lp, t0 + on, dur, lv, jt=0, jv=0)
        sc.note(15, material.mirror(lp, float(AXIS)), t0 + on + lag, dur,
                max(1, lv - 6), jt=0, jv=0)
        if dur >= 1.9:
            _bloom(sc, 14, t0 + on, dur)
            _bloom(sc, 15, t0 + on + lag, dur)


def _pad(sc, t0, t1, vel, vel_end=None):
    chords = [en.triad(48, MODE, DEGS[i]) for i in
              range(int(t0 // 4), int(t1 // 4))]
    en.pad_block(sc, 1, t0, chords, span=4.0, size=4, lo=52, hi=76,
                 vel=vel, vel_end=vel_end)


def _strings(sc, t0, t1, vel, vel_end=None, size=3):
    chords = [en.triad(48, MODE, DEGS[i]) for i in
              range(int(t0 // 4), int(t1 // 4))]
    en.pad_block(sc, 7, t0, chords, span=4.0, size=size, lo=55, hi=76,
                 vel=vel, vel_end=vel_end)


def _four_floor(sc, t0, t1, kick, clap, hat, ohat, hat16=0, ride=0, snare=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(9, 46, t + 0.5, 0.4, ohat, jt=0, jv=4)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
            if ride:
                sc.note(9, 51, t, 0.3, ride, jt=0, jv=4)
        sc.note(9, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(9, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)
        if snare:
            sc.note(9, 38, bar + 1.0, 0.25, snare, jt=0, jv=4)
            sc.note(9, 38, bar + 3.0, 0.25, snare, jt=0, jv=4)


def _roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _kick4(sc, t0, t1, vel):
    t = t0
    while t < t1 - 1e-9:
        sc.note(9, 36, t, 0.25, vel, jt=0, jv=4)
        t += 1.0


def _bass_8ths(sc, t0, t1, vel0, vel1, pop=False):
    n = int(round((t1 - t0) / 0.5))
    for i in range(n):
        t = t0 + 0.5 * i
        root = _root2(t)
        p = root
        if pop and abs((t % 4.0) - 3.5) < 1e-9 and root + 12 <= 52:
            p = root + 12
        v = round(en.lerp(vel0, vel1, i / max(1, n - 1)))
        if t % 4.0 < 1e-9:
            v = min(112, v + 4)
        sc.note(2, p, t, 0.4, v, jt=0, jv=3)


def _bass_holds(sc, t0, t1, span, vel):
    t = t0
    while t < t1 - 1e-9:
        sc.note(2, _root2(t), t, span - 0.2, vel, jt=0, jv=3)
        t += span


def _arp_pool(base, deg, cap=96):
    chord = en.triad(base, MODE, deg)
    return [p for p in chord + [q + 12 for q in chord] if p <= cap]


def _arp(sc, t0, t1, base, vel0, vel1, step):
    n = int(round((t1 - t0) / step))
    k = 0
    for i in range(n):
        t = t0 + step * i
        pool = _arp_pool(base, _deg_at(t))
        v = round(en.lerp(vel0, vel1, i / max(1, n - 1)))
        if t % 1.0 < 1e-9:
            v = min(112, v + 6)
        sc.note(0, pool[k % len(pool)], t, step * 0.9, v, jt=0, jv=2)
        k += 1


def _sweep(sc, t0, vel0, vel1, n=8):
    chord = en.triad(55, MODE, _deg_at(t0))
    pool = chord + [p + 12 for p in chord] + [chord[0] + 24]
    for i in range(n):
        sc.note(6, pool[i % len(pool)], t0 + 0.125 * i, 0.3,
                round(en.lerp(vel0, vel1, i / max(1, n - 1))), jt=0, jv=3)


def _harp_quarters(sc, t0, t1, vel):
    k = 0
    t = t0
    while t < t1 - 1e-9:
        pool = _arp_pool(55, _deg_at(t), cap=89)
        sc.note(6, pool[k % len(pool)], t, 0.7, vel, jt=0, jv=3)
        k += 1
        t += 1.0


def _posts(sc, t0, t1):
    for t, vel in POSTS:
        if t0 <= t < t1:
            for off, p in POST_CALL:
                sc.note(3, p, t + off, 0.4, vel, jt=0, jv=3)
            for off, p in POST_ANS:
                sc.note(4, p, t + 2.0 + off, 0.4, vel - 6, jt=0, jv=3)


def _hits(sc, t0, t1):
    for t, vel in HITS:
        if t0 <= t < t1:
            sc.note(12, _root3(t), t, 0.9, vel, jt=0, jv=3)


def _fills(sc, t0, t1):
    for beat, shape, vb in FILL_SCHEDULE:
        if t0 <= beat < t1:
            material.play_fill(sc, shape, beat, vbump=vb)


def _risers(sc, t0, t1):
    for t, dur, vel in RISERS:
        if t0 <= t < t1:
            sc.note(13, 62, t, dur, vel, jt=0, jv=0)


# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------


def _b_approach(sc):
    # Whole-timeline CC choreography (authored once, here).
    en.cc_curve(sc, 1, 74, [(0, 30), (136, 36), (176, 58), (184, 72),
                            (272, 52), (280, 38), (360, 42), (400, 72),
                            (408, 102), (520, 48), (END, 30)], step=0.5)
    en.expr_curve(sc, 1, [(0, 64), (40, 76), (136, 86), (184, 102),
                          (272, 84), (280, 60), (344, 66), (360, 84),
                          (408, 112), (520, 92), (560, 60), (END, 42)],
                  step=1.0)
    en.vowel_curve(sc, 8, [(0, 5), (40, 28), (136, 40), (184, 88),
                           (272, 60), (280, 45), (356, 50), (408, 96),
                           (520, 50), (556, 12), (END, 2)], step=0.5)
    _pad(sc, 0.0, 40.0, 44)
    # The axis tone, alone: the saw holds F4 = 65 and slowly swells.
    for k, t in enumerate((0.0, 8.0, 16.0, 24.0, 32.0)):
        sc.note(5, AXIS, t, 7.9, 44 + 3 * k, jt=0, jv=0)
    for t in (0.0, 8.0, 16.0, 24.0, 32.0):
        sc.note(8, 60, t, 7.9, 40, jt=3, jv=2)
        sc.note(8, 55, t, 7.9, 36, jt=3, jv=2)
    _bass_holds(sc, 16.0, 40.0, 2.0, 50)
    _harp_quarters(sc, 16.0, 38.0, 38)
    _sweep(sc, 38.0, 44, 60)


def _b_pass_one(sc):
    _pad(sc, 40.0, 136.0, 50)
    _strings(sc, 40.0, 136.0, 42, size=2)
    _emit_canon(sc, 44.0, C1, 2.0, 0, -2)
    _arp(sc, 40.0, 136.0, 60, 44, 52, 0.5)
    _bass_holds(sc, 40.0, 72.0, 2.0, 56)
    _bass_8ths(sc, 72.0, 136.0, 62, 70)
    for b in range(16):                       # light kit from bar 72
        bar = 72.0 + 4.0 * b
        for k in (0.0, 2.0):
            sc.note(9, 36, bar + k, 0.25, 82, jt=0, jv=4)
        for k in (1.0, 3.0):
            sc.note(9, 37, bar + k, 0.2, 62, jt=0, jv=4)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.2, 52, jt=0, jv=4)
        sc.note(9, 46, bar + 3.5, 0.4, 44, jt=0, jv=4)
    _posts(sc, 40.0, 136.0)
    _sweep(sc, 70.0, 46, 64)
    _sweep(sc, 102.0, 48, 66)
    _sweep(sc, 134.0, 52, 70)
    _fills(sc, 40.0, 136.0)


def _b_build_one(sc):
    _pad(sc, 136.0, 184.0, 56, vel_end=72)
    _strings(sc, 136.0, 184.0, 52, vel_end=68)
    sc.note(9, 49, 136.0, 0.5, 100, jt=0, jv=3)
    _four_floor(sc, 136.0, 152.0, 102, 92, 68, 60)
    _four_floor(sc, 152.0, 176.0, 102, 92, 68, 60, hat16=44)
    _roll(sc, 176.0, 184.0, 60, 112)
    _kick4(sc, 176.0, 184.0, 100)
    _bass_8ths(sc, 136.0, 184.0, 78, 96)
    _arp(sc, 136.0, 184.0, 72, 60, 78, 0.25)
    for i in range(48):                       # wing ship chugs in
        t = 152.0 + 0.5 * i
        sc.note(15, 48, t, 0.4, round(en.lerp(70, 88, i / 47)), jt=0, jv=3)
    sc.note(5, 79, 168.0, 7.9, 78, jt=0, jv=0)   # the soar
    _bloom(sc, 5, 168.0, 7.9)
    material.play_ascent(sc, 14, 180.0, 60, vel=100, vel_end=112,
                         gate=0.9, jt=0, jv=0)
    _risers(sc, 136.0, 184.0)
    _fills(sc, 136.0, 184.0)


def _b_drop_one(sc):
    _pad(sc, 184.0, 280.0, 68)
    _strings(sc, 184.0, 280.0, 66)
    for t, v in ((184.0, 112), (216.0, 96), (248.0, 96), (272.0, 84)):
        sc.note(9, 49, t, 0.5, v, jt=0, jv=3)
    _four_floor(sc, 184.0, 216.0, 106, 96, 70, 62)
    _four_floor(sc, 216.0, 272.0, 106, 96, 70, 62, hat16=48)
    _four_floor(sc, 272.0, 280.0, 88, 80, 58, 50)
    _bass_8ths(sc, 184.0, 272.0, 96, 100, pop=True)
    _bass_8ths(sc, 272.0, 280.0, 84, 80)
    _arp(sc, 184.0, 272.0, 72, 70, 74, 0.25)
    _arp(sc, 272.0, 280.0, 72, 60, 56, 0.25)
    _emit_canon(sc, 188.0, C1_D1, 2.0, 12, 12)
    for k in range(12):                       # saw high pedal (oblique)
        sc.note(5, 79, 184.0 + 8.0 * k, 7.9, 54, jt=0, jv=2)
    for k in range(22):                       # choir bar roots, ah
        t = 184.0 + 4.0 * k
        sc.note(8, en.pitch(60, MODE, _deg_at(t)), t, 3.9, 62, jt=0, jv=2)
    _hits(sc, 184.0, 280.0)
    _posts(sc, 184.0, 280.0)
    _sweep(sc, 214.0, 55, 75)
    _sweep(sc, 246.0, 55, 75)
    _sweep(sc, 278.0, 50, 68)
    _risers(sc, 184.0, 280.0)
    _fills(sc, 184.0, 280.0)


def _b_interlude(sc):
    _pad(sc, 280.0, 360.0, 46)
    _strings(sc, 280.0, 360.0, 54)
    for on, p, dur, vel in QUOTE:             # saw takes the cantus
        sc.note(5, p, 284.0 + on, dur, max(1, vel - 14), jt=0, jv=0)
    sc.note(5, 65, 344.0, 5.9, 58, jt=0, jv=0)
    sc.note(5, 63, 350.0, 5.9, 54, jt=0, jv=0)
    for on, p, dur in ICHOIR:                 # choir counters, free
        sc.note(8, p, 284.0 + on, dur, 58, jt=0, jv=0)
    sc.note(8, 56, 344.0, 5.9, 54, jt=0, jv=0)
    sc.note(8, 55, 350.0, 5.9, 50, jt=0, jv=0)
    _bass_holds(sc, 280.0, 360.0, 4.0, 52)
    _harp_quarters(sc, 280.0, 344.0, 45)
    for b in range(20):                       # hush kit
        bar = 280.0 + 4.0 * b
        sc.note(9, 36, bar, 0.25, 56, jt=0, jv=3)
        sc.note(9, 37, bar + 2.0, 0.2, 40, jt=0, jv=3)
        if bar >= 312.0:
            for k in range(8):
                sc.note(9, 42, bar + 0.5 * k, 0.2, 38, jt=0, jv=3)
    _fills(sc, 280.0, 360.0)


def _b_build_two(sc):
    _pad(sc, 360.0, 408.0, 60, vel_end=76)
    _strings(sc, 360.0, 408.0, 58, vel_end=76)
    sc.note(9, 49, 360.0, 0.5, 104, jt=0, jv=3)
    _four_floor(sc, 360.0, 400.0, 106, 96, 72, 64, hat16=46)
    _roll(sc, 400.0, 408.0, 64, 118)
    _kick4(sc, 400.0, 408.0, 104)
    _bass_8ths(sc, 360.0, 408.0, 86, 102)
    _arp(sc, 360.0, 408.0, 72, 68, 82, 0.25)
    for i in range(64):                       # wing chugs, hungrier
        t = 368.0 + 0.5 * i
        sc.note(15, 48, t, 0.4, round(en.lerp(76, 96, i / 63)), jt=0, jv=3)
    for k, t in enumerate((384.0, 388.0, 392.0, 396.0)):   # lead stabs
        sc.note(14, 72, t, 0.4, 90 + 2 * k, jt=0, jv=0)
    sc.note(5, 84, 392.0, 7.9, 84, jt=0, jv=0)   # the second soar
    _bloom(sc, 5, 392.0, 7.9)
    _risers(sc, 360.0, 408.0)
    _fills(sc, 360.0, 408.0)


def _b_drop_two(sc):
    _pad(sc, 408.0, 520.0, 74)
    _strings(sc, 408.0, 520.0, 76)
    for t, v in ((408.0, 116), (440.0, 100), (472.0, 100), (504.0, 108)):
        sc.note(9, 49, t, 0.5, v, jt=0, jv=3)
    _four_floor(sc, 408.0, 520.0, 112, 102, 76, 68, hat16=60, ride=70,
                snare=92)
    _bass_8ths(sc, 408.0, 520.0, 104, 106, pop=True)
    _arp(sc, 408.0, 520.0, 72, 80, 84, 0.25)
    _emit_canon(sc, 412.0, C2, 1.0, 0, 6)
    for on, p, dur in D2CHOIR:                # the third line
        sc.note(8, p, 412.0 + on, dur, 78, jt=0, jv=0)
    for k in range(14):                       # saw pedal octaves
        sc.note(5, 79 if k % 2 == 0 else 84, 408.0 + 8.0 * k, 7.9, 58,
                jt=0, jv=2)
    _hits(sc, 408.0, 520.0)
    _posts(sc, 408.0, 520.0)
    _sweep(sc, 438.0, 60, 80)
    _sweep(sc, 470.0, 60, 80)
    _sweep(sc, 502.0, 60, 80)
    _risers(sc, 408.0, 520.0)
    _fills(sc, 408.0, 520.0)


def _b_resolution(sc):
    _pad(sc, 520.0, END, 62, vel_end=40)
    _strings(sc, 520.0, 568.0, 60, vel_end=42)
    for on, p, dur, vel in RES_DUO:           # unison landing on the axis
        sc.note(14, p, on, dur, vel, jt=0, jv=0)
        sc.note(15, p, on, dur, max(1, vel - 6), jt=0, jv=0)
        _bloom(sc, 14, on, dur)
        _bloom(sc, 15, on, dur)
    _hits(sc, 520.0, END)
    sc.note(9, 49, 520.0, 0.5, 96, jt=0, jv=3)
    sc.note(9, 49, 536.0, 0.5, 72, jt=0, jv=3)
    for k, t in enumerate((520.0, 524.0, 528.0, 532.0, 536.0)):
        sc.note(9, 36, t, 0.25, 74 - 6 * k, jt=0, jv=3)
    t = 520.0
    while t < 550.0 + 1e-9:
        sc.note(9, 51, t, 0.3, 40, jt=0, jv=3)
        t += 2.0
    sc.note(8, 60, 536.0, 15.9, 46, jt=0, jv=0)
    sc.note(8, 55, 536.0, 15.9, 42, jt=0, jv=0)
    sc.note(8, 60, 552.0, 19.9, 36, jt=0, jv=0)
    sc.note(8, 55, 552.0, 19.9, 32, jt=0, jv=0)
    sc.note(2, 41, 520.0, 7.8, 72, jt=0, jv=2)
    sc.note(2, 39, 528.0, 3.8, 66, jt=0, jv=2)
    sc.note(2, 43, 532.0, 3.8, 62, jt=0, jv=2)
    sc.note(2, 36, 536.0, 15.8, 58, jt=0, jv=2)
    _sweep(sc, 552.0, 44, 58)
    _harp_quarters(sc, 556.0, 568.0, 38)
    sc.note(5, 72, 552.0, 15.9, 36, jt=0, jv=0)


BUILDERS = [_b_approach, _b_pass_one, _b_build_one, _b_drop_one,
            _b_interlude, _b_build_two, _b_drop_two, _b_resolution]

# ---------------------------------------------------------------------------
# Oracle helpers
# ---------------------------------------------------------------------------


def _tick(beat):
    return max(0, int(round(beat * _PPQ)))


def _full_notes(sc, ch):
    """[(on_tick, off_tick, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[int, int]]] = {}
    out = []
    for tick, _prio, data in sorted(sc.events.get(ch, []),
                                    key=lambda e: (e[0], e[1])):
        s = data[0] & 0xF0
        if s == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick, data[2]))
        elif s == 0x80 or (s == 0x90 and data[2] == 0):
            q = pending.get(data[1])
            if q:
                on, vel = q.pop(0)
                out.append((on, tick, data[1], vel))
    return sorted(out)


def _in_win(notes, lo, hi):
    lot, hit = _tick(lo), _tick(hi)
    return [nt for nt in notes if lot <= nt[0] < hit]


def _cc_lane(sc, ch, num):
    return sorted((t, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _pitch_at(notes, beat):
    """Pitch sounding at `beat` (attack-inclusive), latest onset wins."""
    t = _tick(beat)
    best = None
    for on, off, p, _v in notes:
        if on <= t and off > t and (best is None or on > best[0]):
            best = (on, p)
    return None if best is None else best[1]


def _bar_sums(sc):
    out: dict[int, float] = {}
    for ch in sc.events:
        for on, _off, _p, v in _full_notes(sc, ch):
            out[on // (4 * _PPQ)] = out.get(on // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _dir(a, b):
    return 0 if a == b else (1 if b > a else -1)


def _counterpoint_metrics(cn, ln, downbeats):
    """(noncoincident_frac, contrary_oblique_frac, bad_consonance,
    doubling_frac) for counter-notes `cn` against lead notes `ln`."""
    l_ons = {on for on, _off, _p, _v in ln}
    c_ons = sorted((on, p) for on, _off, p, _v in cn)
    nonco = sum(1 for on, _p in c_ons if on not in l_ons) / max(1, len(c_ons))
    good = total = 0
    for i in range(1, len(c_ons)):
        t_now, t_prev = c_ons[i][0] / _PPQ, c_ons[i - 1][0] / _PPQ
        a_now, a_prev = _pitch_at(ln, t_now), _pitch_at(ln, t_prev)
        if a_now is None or a_prev is None:
            continue
        total += 1
        cd = _dir(c_ons[i - 1][1], c_ons[i][1])
        ld = _dir(a_prev, a_now)
        if cd * ld < 0 or cd == 0 or ld == 0:
            good += 1
    motion = good / max(1, total)
    bad = []
    doubled = checked = 0
    for t in downbeats:
        a, c = _pitch_at(ln, t), _pitch_at(cn, t)
        if a is None or c is None:
            bad.append(f"missing voice at downbeat {t:g}")
            continue
        checked += 1
        if (a - c) % 12 not in _CONSONANT:
            bad.append(f"dissonant pair at {t:g}: {a} vs {c}")
        if a % 12 == c % 12:
            doubled += 1
    return nonco, motion, bad, doubled / max(1, checked)


# ---------------------------------------------------------------------------
# Track oracles
# ---------------------------------------------------------------------------


def _o_mirror_canon(sc):
    """wing(t) = mirror(lead(t - lag), AXIS) — tick-exact, velocity-shaped
    (wing = lead - 6), for every note of every canon span, both lags."""
    fails = []
    lead, wing = _full_notes(sc, 14), _full_notes(sc, 15)
    for t0, t1, lag, oct_shift, vel_shift, table in CANON_SPANS:
        ln = _in_win(lead, t0, t1)
        wn = _in_win(wing, t0 + lag, t1 + lag)
        if len(ln) != len(table):
            fails.append(f"span {t0:g}: lead has {len(ln)} notes, "
                         f"table {len(table)}")
        lagt = _tick(lag)
        expect = sorted((on + lagt, off + lagt,
                         material.mirror(p, float(AXIS)), max(1, v - 6))
                        for on, off, p, v in ln)
        if expect != wn:
            n_bad = sum(1 for a, b in zip(expect, wn) if a != b)
            fails.append(f"span {t0:g} lag {lag:g}: wing lane is not the "
                         f"mirrored lead ({n_bad} mismatches of "
                         f"{len(expect)}/{len(wn)})")
        for t in range(int(t0 - t0 % 4 + 4), int(t1), 4):
            a, w = _pitch_at(ln, float(t)), _pitch_at(wn, float(t))
            if a is None or w is None:
                fails.append(f"no duo pair sounding at downbeat {t}")
            elif (a - w) % 12 not in _CONSONANT:
                fails.append(f"duo dissonant at downbeat {t}: {a} vs {w}")
    return fails[:8]


def _o_axis_resolution(sc):
    """Both ships land ON the axis pitch, in unison, at 520; every
    resolution duo note is unison; the last is a held tonic C."""
    fails = []
    if material.mirror(AXIS, float(AXIS)) != AXIS:
        fails.append("AXIS is not the mirror fixpoint")
    lead = _in_win(_full_notes(sc, 14), 520.0, END)
    wing = _in_win(_full_notes(sc, 15), 520.0, END)
    want = [(_tick(on), p) for on, p, _d, _v in RES_DUO]
    if [(on, p) for on, _off, p, _v in lead] != want:
        fails.append("lead resolution lane differs from RES_DUO")
    if [(on, p) for on, _off, p, _v in wing] != want:
        fails.append("wing resolution lane differs from RES_DUO")
    if [(on, off, p) for on, off, p, _v in lead] != \
            [(on, off, p) for on, off, p, _v in wing]:
        fails.append("resolution duo is not tick-exact unison")
    if not lead or lead[0][2] != AXIS or lead[0][0] != _tick(520.0):
        fails.append("first resolution note is not the axis pitch at 520")
    if not lead or lead[-1][2] != 60 or \
            (lead[-1][1] - lead[-1][0]) < _tick(12.0):
        fails.append("final note is not a >=12-beat unison C")
    return fails[:8]


def _o_interlude_handoff(sc):
    """Guitars rest for the whole interlude; the saw takes the cantus
    (first 15 bars, pinned note-for-note); the choir sings against it."""
    fails = []
    for ch, name in ((14, "lead"), (15, "wing")):
        n = len(_in_win(_full_notes(sc, ch), 280.0, 360.0))
        if n:
            fails.append(f"{name} ship plays {n} notes in the interlude")
    saw = _in_win(_full_notes(sc, 5), 284.0, 344.0)
    expect = []
    for on, p, dur, _v in QUOTE:
        on_t = _tick(284.0 + on)
        off_t = max(on_t + _PPQ // 16, _tick(284.0 + on + max(0.05, dur)))
        expect.append((on_t, off_t, p))
    if [(on, off, p) for on, off, p, _v in saw] != sorted(expect):
        fails.append(f"saw lane {len(saw)} notes does not equal the "
                     f"{len(expect)}-note cantus quote")
    n_choir = len(_in_win(_full_notes(sc, 8), 284.0, 352.0))
    if n_choir < 14:
        fails.append(f"choir sings only {n_choir} interlude notes (<14)")
    return fails[:8]


def _o_interlude_counterpoint(sc):
    """The choir/saw pair meets the full counterpoint discipline."""
    fails = []
    saw = _in_win(_full_notes(sc, 5), 284.0, 344.0)
    choir = _in_win(_full_notes(sc, 8), 284.0, 344.0)
    downbeats = [float(t) for t in range(288, 344, 4)]
    nonco, motion, bad, doubling = _counterpoint_metrics(
        choir, saw, downbeats)
    if nonco < 0.5:
        fails.append(f"non-coincident onsets {nonco:.2f} < 0.5")
    if motion < 0.6:
        fails.append(f"contrary+oblique motion {motion:.2f} < 0.6")
    fails.extend(bad)
    if doubling > 0.25:
        fails.append(f"pitch-class doubling {doubling:.2f} > 0.25")
    return fails[:8]


def _o_three_lines_drop2(sc):
    """Drop Two runs three simultaneous lines: lead, mirrored wing (lag 1)
    and a free choir line — all pairwise consonant on bar downbeats."""
    fails = []
    lead = _in_win(_full_notes(sc, 14), 412.0, 508.0)
    wing = _in_win(_full_notes(sc, 15), 413.0, 509.0)
    choir = _in_win(_full_notes(sc, 8), 412.0, 508.0)
    for name, notes, need in (("lead", lead, 80), ("wing", wing, 80),
                              ("choir", choir, 20)):
        if len(notes) < need:
            fails.append(f"{name}: {len(notes)} notes < {need}")
        span = _tick(504.0) - _tick(416.0)
        cover = sum(min(off, _tick(504.0)) - max(on, _tick(416.0))
                    for on, off, _p, _v in notes
                    if off > _tick(416.0) and on < _tick(504.0)) / span
        if cover < 0.7:
            fails.append(f"{name}: sounding coverage {cover:.2f} < 0.7")
    downbeats = [float(t) for t in range(416, 508, 4)]
    for t in downbeats:
        trio = {"lead": _pitch_at(lead, t), "wing": _pitch_at(wing, t),
                "choir": _pitch_at(choir, t)}
        if None in trio.values():
            fails.append(f"a line is silent at downbeat {t:g}")
            continue
        for x, y in (("lead", "wing"), ("choir", "lead"), ("choir", "wing")):
            if (trio[x] - trio[y]) % 12 not in _CONSONANT:
                fails.append(f"{x}/{y} dissonant at {t:g}: "
                             f"{trio[x]} vs {trio[y]}")
    nonco, motion, _bad, doubling = _counterpoint_metrics(
        choir, lead, downbeats)
    if nonco < 0.5:
        fails.append(f"choir onsets coincide with lead: {nonco:.2f} < 0.5")
    if motion < 0.6:
        fails.append(f"choir contrary+oblique {motion:.2f} < 0.6")
    if doubling > 0.25:
        fails.append(f"choir/lead pc doubling {doubling:.2f} > 0.25")
    return fails[:8]


def _o_build_drop_contour(sc):
    """Builds strictly rise window over window; Drop Two carries strictly
    more per-bar velocity mass than Drop One; the interlude is a genuine
    hush; the approach sits below the first pass."""
    fails = []
    sums = _bar_sums(sc)
    for name, wins in BUILD_WINDOWS.items():
        means = [_mean_barsum(sums, lo, hi) for lo, hi in wins]
        for a, b in zip(means, means[1:]):
            if b <= a:
                fails.append(f"{name} windows not strictly rising: "
                             f"{[round(m) for m in means]}")
                break
    d1 = _mean_barsum(sums, 184.0, 272.0)
    d2 = _mean_barsum(sums, 408.0, 504.0)
    if d2 < 1.05 * d1:
        fails.append(f"drop two ({d2:.0f}/bar) not > 1.05x drop one "
                     f"({d1:.0f}/bar)")
    hush = _mean_barsum(sums, 288.0, 344.0)
    if hush > 0.5 * d1:
        fails.append(f"interlude {hush:.0f}/bar > 50% of drop one {d1:.0f}")
    appr = _mean_barsum(sums, 0.0, 40.0)
    pass1 = _mean_barsum(sums, 48.0, 132.0)
    if appr > 0.6 * pass1:
        fails.append(f"approach {appr:.0f}/bar > 60% of pass one {pass1:.0f}")
    return fails[:8]


def _o_fill_escalation(sc):
    """The fill lanes carry exactly the schedule; per-window counts rise
    strictly through each build; >=5 distinct shapes per build; a >=20-note
    unbroken chain lands each drop; drop windows stay thinned (<=20)."""
    fails = []
    expect: list[tuple[int, int, int]] = []
    beats: list[float] = []
    shapes_at: list[tuple[float, str]] = []
    for beat, shape, _vb in FILL_SCHEDULE:
        shapes_at.append((beat, shape))
        for lane, ch in (("tom", 10), ("syn", 11)):
            for off, p, _dur, _vel in material.FILL_LIB[shape].get(lane, ()):
                expect.append((ch, _tick(beat + off), p))
                beats.append(beat + off)
    actual = [(ch, on, p) for ch in (10, 11)
              for on, _off, p, _v in _full_notes(sc, ch)]
    if sorted(expect) != sorted(actual):
        fails.append(f"fill lanes ({len(actual)} notes) differ from the "
                     f"schedule ({len(expect)})")
    beats.sort()
    for name, wins in BUILD_WINDOWS.items():
        counts = [sum(1 for b in beats if lo <= b < hi) for lo, hi in wins]
        for a, b in zip(counts, counts[1:]):
            if b <= a:
                fails.append(f"{name} fill counts not rising: {counts}")
                break
        shapes = {s for t, s in shapes_at
                  if wins[0][0] <= t < wins[-1][1]}
        if len(shapes) < 5:
            fails.append(f"{name} uses only {len(shapes)} shapes (<5)")
    for drop in DROP_STARTS:
        run = [b for b in beats if drop - 6.5 <= b < drop]
        chain = 1
        for i in range(len(run) - 1, 0, -1):
            if run[i] - run[i - 1] <= 0.5:
                chain += 1
            else:
                break
        if not run or run[-1] < drop - 1.0 or chain < 20:
            fails.append(f"no >=20-note unbroken fill into drop {drop:g} "
                         f"(chain {chain})")
        for w0 in (drop, drop + 32.0, drop + 64.0):
            n = sum(1 for b in beats if w0 <= b < w0 + 32.0)
            if n > 20:
                fails.append(f"drop window {w0:g} has {n} fill notes (>20)")
    return fails[:8]


def _o_soar_sweep_risers(sc):
    """CC74 macro-sweep >= 60 units on the pad; pinned reverse-cymbal
    risers land both drops (and the resolution); two >=6-beat saw soars
    at/above G5 each carry a CC1 bloom."""
    fails = []
    cc74 = [v for _t, v in _cc_lane(sc, 1, 74)]
    if not cc74 or max(cc74) - min(cc74) < 60:
        fails.append(f"pad CC74 sweep span "
                     f"{(max(cc74) - min(cc74)) if cc74 else 0} < 60")
    risers = _full_notes(sc, 13)
    want = [(_tick(t), 62) for t, _d, _v in RISERS]
    if [(on, p) for on, _off, p, _v in risers] != want:
        fails.append("riser lane differs from the pinned schedule")
    for drop in DROP_STARTS + [520.0]:
        if not any(on < _tick(drop) <= off + _tick(0.5)
                   for on, off, _p, _v in risers):
            fails.append(f"no riser lands the drop at {drop:g}")
    cc1 = _cc_lane(sc, 5, 1)
    soars = 0
    for on, off, p, _v in _full_notes(sc, 5):
        if p >= 79 and off - on >= _tick(6.0):
            vals = [v for t, v in cc1 if on <= t <= off]
            if vals and max(vals) - min(vals) >= 30:
                soars += 1
    if soars < 2:
        fails.append(f"only {soars} bloomed >=6-beat soars (<2)")
    return fails[:8]


def _o_ascent_statement(sc):
    """The lead ship states material.ASCENT_CELL on C4 at beat 180,
    hanging on the twelfth straight into Drop One."""
    fails = []
    lead = _in_win(_full_notes(sc, 14), 179.9, 184.0)
    want = [(_tick(180.0 + on), 60 + s) for on, _d, s in material.ASCENT_CELL]
    got = [(on, p) for on, _off, p, _v in lead]
    if got != want:
        fails.append(f"ascent notes {got} != pinned {want}")
    elif lead[-1][1] - lead[-1][0] < _tick(2.0):
        fails.append("ascent hang shorter than 2 beats")
    elif [v for _on, _off, _p, v in lead] != \
            sorted(v for _on, _off, _p, v in lead):
        fails.append("ascent velocities must not decrease")
    return fails[:8]


def _o_layer_count(sc):
    """14-16 channels genuinely active inside each drop's core."""
    fails = []
    for lo, hi in ((216.0, 272.0), (440.0, 504.0)):
        active = sum(1 for ch in range(16)
                     if _in_win(_full_notes(sc, ch), lo, hi))
        if active < 14:
            fails.append(f"only {active} active channels in [{lo:g},{hi:g})")
    return fails[:8]


def oracles(sc, info, spans):
    return [
        ("mirror_canon_exact", _o_mirror_canon(sc)),
        ("axis_resolution", _o_axis_resolution(sc)),
        ("interlude_handoff", _o_interlude_handoff(sc)),
        ("interlude_counterpoint", _o_interlude_counterpoint(sc)),
        ("three_lines_drop2", _o_three_lines_drop2(sc)),
        ("build_drop_contour", _o_build_drop_contour(sc)),
        ("fill_escalation", _o_fill_escalation(sc)),
        ("soar_sweep_risers", _o_soar_sweep_risers(sc)),
        ("ascent_statement", _o_ascent_statement(sc)),
        ("layer_count", _o_layer_count(sc)),
    ]
