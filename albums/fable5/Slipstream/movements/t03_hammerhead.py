"""t03_hammerhead.py — Slipstream T3, "Hammerhead".

HLD section 4/T3: the vertical climb until airspeed dies, the yaw pivot at
the top, the vertical dive, the pull-out — twice, the second higher.
D aeolian, 126 bpm with the dives accelerating to 138, 4/4, ~4:45.

Architecture (movement grid below): run-in -> CLIMB1 (20-bar single
crescendo, register and velocity strictly rising) -> STALL1 (2 bars of
near-silence: ONE high pedal tone) -> PIVOT1 (drum-fill cadenza, ch10/11
only) -> DIVE1 (descending cascades, tempo 126->138) -> PULL-OUT/DROP1
(tempo back, four-on-floor) -> CLIMB2 (higher) -> STALL2 -> PIVOT2 (bigger)
-> DIVE2 -> DROP2 (> DROP1) -> victory-pass outro.

Duo formation — CONTRARY: in each climb the lead ship (ch14) rises one
scale degree per bar while the wing ship (ch15) descends one degree per
bar; the symmetric walk keeps every downbeat interval inside
{0,2,3,4,5,7,8,9,10} (no m2/tritone/M7 clashes — the whole-tone bars are
the airframe shudder), and the ships MEET IN UNISON at bar 8 of each climb
(the pinned crossing: beat 60 and beat 320) before swapping registers.

Oracles (all HLD-contractual): climb_monotone, duo_contrary_cross,
stall_hush, pivot_fills_only, dive_descent_and_accel, build_drop_contour,
fill_escalation, plus ascent_statements, soar_and_sweep,
drop2_counterpoint and layered_climax for the album-wide disciplines.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 3
TITLE = "Hammerhead"
FILE = "03 - Hammerhead.mid"
SEED = 20261103

COMMENT = (
    "The hammerhead turn, flown twice. A twenty-bar vertical climb - the two "
    "guitars in strict contrary motion, meeting in unison mid-climb and "
    "swapping registers - until the airspeed dies to a single hanging pedal "
    "tone; a one-bar drum cadenza pivots the nose, the dive accelerates from "
    "126 to 138 bpm under waterfalls of harp, and the pull-out lands on a "
    "four-on-the-floor drop. The second climb tops the first, the second "
    "pivot is longer, and the second drop is bigger, with a soaring saw "
    "counter-line in verified counterpoint against the guitar hook.")

MODE = "aeolian"
BASE = 50                     # D3 — degree 1

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

RUN_T0, RUN_T1 = 0.0, 32.0
C1_T0, C1_T1 = 32.0, 112.0
S1_T0, S1_T1 = 112.0, 120.0
P1_T0, P1_T1 = 120.0, 124.0
D1_T0, D1_T1 = 124.0, 164.0
DR1_T0, DR1_T1 = 164.0, 292.0
C2_T0, C2_T1 = 292.0, 372.0
S2_T0, S2_T1 = 372.0, 380.0
P2_T0, P2_T1 = 380.0, 388.0
D2_T0, D2_T1 = 388.0, 428.0
DR2_T0, DR2_T1 = 428.0, 556.0
OUT_T0, OUT_T1 = 556.0, 600.0

CROSS_BAR = 7                 # 0-based climb bar where the ships meet
CROSS1_BEAT = C1_T0 + 4.0 * CROSS_BAR      # 60.0
CROSS2_BEAT = C2_T0 + 4.0 * CROSS_BAR      # 320.0

TEMPO_MAP = [
    (0.0, 126.0),
    (124.0, 129.0), (132.0, 132.0), (140.0, 135.0), (148.0, 138.0),
    (164.0, 126.0),
    (388.0, 129.0), (396.0, 132.0), (404.0, 135.0), (412.0, 138.0),
    (428.0, 126.0),
]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Run-In", RUN_T0, RUN_T1),
        ("II. Climb One", C1_T0, C1_T1),
        ("III. Stall One", S1_T0, S1_T1),
        ("IV. Pivot One", P1_T0, P1_T1),
        ("V. Dive One", D1_T0, D1_T1),
        ("VI. Pull-Out One", DR1_T0, DR1_T1),
        ("VII. Climb Two", C2_T0, C2_T1),
        ("VIII. Stall Two", S2_T0, S2_T1),
        ("IX. Pivot Two", P2_T0, P2_T1),
        ("X. Dive Two", D2_T0, D2_T1),
        ("XI. Pull-Out Two", DR2_T0, DR2_T1),
        ("XII. Victory Pass", OUT_T0, OUT_T1),
    ],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],                     # D minor
    channels=[
        (0, "pulse arp", 80, 88, 64, 30),
        (1, "pad", 89, 86, 64, 60),
        (2, "bass", 39, 104, 64, 15),
        (3, "post L", 45, 92, 18, 35),
        (4, "post R", 45, 92, 110, 35),
        (5, "saw soar", 81, 100, 64, 45),
        (6, "harp cascade", 46, 96, 64, 50),
        (7, "strings", 49, 88, 64, 60),
        (8, "choir", 52, 90, 64, 65),
        (9, "kit", 0, 110, 64, 25),
        (10, "melodic toms", 117, 102, 64, 30),
        (11, "syn drum", 118, 102, 64, 30),
        (12, "orch hit", 55, 102, 64, 45),
        (13, "riser", 119, 96, 64, 55),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 106, 64, 22),
    ],
    program_changes=[(9, 0.0, 25)],   # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One
    extra_markers=[(CROSS1_BEAT, "the ships cross"),
                   (CROSS2_BEAT, "the ships cross again")],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

# ---------------------------------------------------------------------------
# Note tables (the pinned lanes)
# ---------------------------------------------------------------------------

# Contrary climbs: symmetric one-degree walks (verified: every downbeat
# interval mod 12 lies in _MILD; the ships meet in unison at CROSS_BAR).
LEAD1_DEGS = list(range(1, 21))            # D3 50 .. Bb5 82
WING1_DEGS = list(range(15, -5, -1))       # D5 74 .. F2 41
LEAD2_DEGS = list(range(3, 23))            # F3 53 .. D6 86
WING2_DEGS = list(range(17, -3, -1))       # F5 77 .. A2 45

STALL1_PITCH = 81                          # A5 — the hanging airspeed
STALL2_PITCH = 86                          # D6 — higher the second time

# The pull-out hook (lead ship), one 8-bar phrase; degrees rel BASE.
# Downbeat degrees [8,10,8,12,7,10,11,8]; onsets avoid 2.75/3.25 (the
# counter's private 16th slots).
HOOK_BARS: list[list[tuple[float, int, float]]] = [
    [(0.0, 8, 1.0), (1.5, 10, 0.5), (2.0, 12, 1.5), (3.5, 10, 0.45)],
    [(0.0, 10, 1.0), (1.5, 8, 0.5), (2.0, 12, 0.5), (2.5, 13, 1.0),
     (3.5, 12, 0.45)],
    [(0.0, 8, 1.0), (1.5, 7, 0.5), (2.0, 8, 1.0), (3.0, 10, 0.95)],
    [(0.0, 12, 1.5), (1.5, 13, 0.5), (2.0, 15, 1.5), (3.5, 14, 0.45)],
    [(0.0, 7, 1.0), (1.5, 8, 0.5), (2.0, 7, 0.5), (2.5, 5, 1.4)],
    [(0.0, 10, 1.0), (1.5, 12, 0.5), (2.0, 10, 1.0), (3.0, 8, 0.95)],
    [(0.0, 11, 1.0), (1.5, 12, 0.5), (2.0, 13, 1.0), (3.0, 12, 0.5),
     (3.5, 10, 0.45)],
    [(0.0, 8, 2.0), (2.5, 7, 0.5), (3.0, 8, 0.95)],
]
HOOK_DOWN_DEGS = [bars[0][1] for bars in HOOK_BARS]     # [8,10,8,12,7,10,11,8]

# The DROP2 saw counter-line (searched: consonant on every downbeat vs the
# hook, one octave-doubling of eight bars, 7/7 contrary-or-oblique motion).
CTR_DEGS = [25, 22, 24, 21, 23, 20, 18, 19]             # 91 86 89 84 88 82 79 81
CTR_PASS = [23, 23, 22, 22, 21, 19, 18, 20]             # 16th passing tones @2.75
CTR_APPROACH_BARS = (3, 7)                              # extra 16th @3.25, deg 24

WING_CHUG = [50, 50, 58, 58, 60, 60, 55, 57]            # per drop bar
BASS_CYCLE = [38, 38, 46, 46, 48, 48, 43, 45]
SAW_D1 = [81, 77, 79, 76]                               # DROP1 phr 3-4 sustains
STR_ROOTS = [74, 70, 72, 69]

ARP_C1 = [[62, 65, 69, 74], [65, 69, 74, 77], [69, 74, 77, 81],
          [74, 77, 81, 86], [77, 81, 86, 89]]
ARP_C2 = [[65, 69, 74, 77], [69, 74, 77, 81], [74, 77, 81, 84],
          [77, 81, 84, 89], [81, 84, 89, 93]]

# Fill programme.  Climb windows escalate strictly (3/8/12/17/22 and
# 8/12/17/22/36 library notes per 16 beats); >=20-note unbroken chains run
# into both drops; drop windows stay thinned (<=12).
FILL_SCHEDULE: list[tuple[float, str]] = [
    (28.0, "A"),
    # CLIMB1
    (46.0, "A"), (60.0, "D"), (72.0, "A"), (76.0, "C"),
    (88.0, "D"), (92.0, "G"), (100.0, "A"), (104.0, "B"), (108.0, "E"),
    # DIVE1 (chain into DROP1 at the tail)
    (140.0, "H"), (152.0, "D"), (160.0, "E"), (162.75, "G"),
    # DROP1 (thinned)
    (179.0, "A"), (194.5, "H"), (226.0, "D"), (243.0, "A"),
    (258.5, "G"), (274.0, "B"),
    # CLIMB2
    (304.0, "D"), (312.0, "A"), (316.0, "C"), (328.0, "D"), (332.0, "G"),
    (340.0, "E"), (342.0, "A"), (344.0, "B"),
    (357.0, "F"), (360.0, "E"), (364.0, "B"), (367.0, "C"),
    # DIVE2 (chain into DROP2 at the tail)
    (396.0, "H"), (408.0, "D"), (424.0, "E"), (426.75, "G"),
    # DROP2 (thinned)
    (443.0, "A"), (458.5, "H"), (474.0, "D"), (490.5, "G"),
    (507.0, "A"), (522.0, "B"), (538.0, "F"), (552.0, "E"),
    # OUTRO
    (572.0, "A"),
]

PIVOT1_FILLS = [(120.0, "G"), (121.0, "E")]                       # 20 notes
PIVOT2_FILLS = [(380.0, "E"), (382.75, "G"), (384.0, "H"),
                (385.5, "B"), (387.0, "A")]                       # 39 notes

RISER_BEATS = [28.0, 160.0, 288.0, 424.0, 552.0]        # 4 beats before lifts

CC74_POINTS = [(0.0, 28), (32.0, 34), (108.0, 104), (120.0, 40),
               (164.0, 96), (288.0, 44), (368.0, 110), (388.0, 60),
               (424.0, 100), (428.0, 88), (552.0, 118), (578.0, 36),
               (600.0, 30)]
VOWEL_POINTS = [(0.0, 20), (96.0, 55), (112.0, 80), (164.0, 30),
                (340.0, 60), (372.0, 85), (428.0, 95), (556.0, 70),
                (598.0, 45)]

# ---------------------------------------------------------------------------
# Verification config (module contract)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {29, 39, 45, 46, 49, 52, 55, 80, 81, 89, 117, 118, 119}
CENTERED_CHANNELS = {0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (60, 94), 1: (46, 80), 2: (33, 61), 3: (62, 80), 4: (62, 80),
    5: (56, 96), 6: (48, 92), 7: (64, 88), 8: (56, 80),
    10: (44, 64), 11: (46, 60), 12: (48, 64), 13: (60, 64),
    14: (48, 90), 15: (39, 79),
}
GAP_WHITELIST = [(112.0, 124.0), (372.0, 388.0)]        # stall + pivot zones
BEND_EXEMPT: set[int] = set()                           # no bends anywhere
DURATION_WINDOW = (277.0, 291.0)                        # ~4:44 file seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


def _play_scheduled(sc: en.Score, lo: float, hi: float) -> None:
    for b, shape in FILL_SCHEDULE:
        if lo <= b < hi:
            material.play_fill(sc, shape, b, vbump=_vbump(b))


def _vbump(b: float) -> int:
    if 148 <= b < 164 or 412 <= b < 428:
        return 8                                        # pre-drop chains
    if C1_T0 <= b < C1_T1:
        return int(en.lerp(0, 8, (b - C1_T0) / 80.0))
    if C2_T0 <= b < C2_T1:
        return int(en.lerp(0, 8, (b - C2_T0) / 80.0))
    if DR1_T0 <= b < DR1_T1 or DR2_T0 <= b < DR2_T1:
        return 4
    return 0


def _riser(sc: en.Score, beat: float, vel: int) -> None:
    sc.note(13, 62, beat, 4.0, vel, jt=0, jv=0)


def _post_call(sc: en.Score, ch: int, t: float, pitches: list[int],
               vel: int) -> None:
    for i, p in enumerate(pitches):
        sc.note(ch, p, t + 0.25 * i, 0.2, vel - 2 * i, jt=0, jv=3)


def _climb_kit(sc: en.Score, t0: float, second: bool) -> None:
    four_from = 5 if second else 10
    for bar in range(20):
        b = t0 + 4.0 * bar
        x = bar / 19.0
        hv = round(en.lerp(56 if second else 50, 82 if second else 76, x))
        kv = round(en.lerp(80 if second else 74, 106 if second else 100, x))
        sv = round(en.lerp(72 if second else 66, 98 if second else 92, x))
        for k in range(4):
            t = b + k
            if bar >= four_from or k in (0, 2):
                sc.note(9, 36, t, 0.25, kv, jt=0, jv=3)
            sc.note(9, 42, t, 0.2, hv, jt=0, jv=3)
            sc.note(9, 42, t + 0.5, 0.15, hv - 8, jt=0, jv=3)
        if bar >= four_from:
            sc.note(9, 38, b + 1.0, 0.25, sv, jt=0, jv=3)
            sc.note(9, 38, b + 3.0, 0.25, sv, jt=0, jv=3)
        if bar >= 16:
            for k in range(8):
                sc.note(9, 42, b + 0.25 + 0.5 * k, 0.12, hv - 16, jt=0, jv=3)
            sc.note(9, 46, b + 3.5, 0.3, hv - 4, jt=0, jv=3)
    sc.note(9, 49, t0, 0.5, 100, jt=0, jv=0)
    sc.note(9, 49, t0 + (20.0 if second else 40.0), 0.5, 94, jt=0, jv=0)


def _climb(sc: en.Score, t0: float, leads: list[int], wings: list[int],
           second: bool) -> None:
    """The 20-bar single crescendo: contrary duo + rising engine."""
    v0, v1 = (72, 108) if second else (66, 104)
    for i in range(20):
        b = t0 + 4.0 * i
        x = i / 19.0
        lv = round(en.lerp(v0, v1, x))
        lp = en.pitch(BASE, MODE, leads[i])
        wp = en.pitch(BASE, MODE, wings[i])
        # lead ship: pinned downbeat + escape-figure pickups
        sc.note(14, lp, b, 2.0, lv, jt=0, jv=2)
        nxt = leads[i + 1] if i < 19 else leads[i] + 2
        sc.note(14, lp, b + 2.5, 0.45, lv - 8, jt=0, jv=2)
        sc.note(14, en.pitch(BASE, MODE, leads[i] + 2), b + 3.0, 0.45,
                lv - 4, jt=0, jv=2)
        sc.note(14, en.pitch(BASE, MODE, nxt), b + 3.5, 0.45, lv, jt=0, jv=2)
        # wing ship: pinned downbeat + descending chug tail
        sc.note(15, wp, b, 2.0, lv - 6, jt=0, jv=2)
        for k, off in enumerate((2.0, 2.5, 3.0, 3.5)):
            sc.note(15, wp, b + off, 0.4, lv - 16 + 2 * k, jt=0, jv=2)
    # bass: driving eighths, root with octave pops
    bv0, bv1 = (64, 102) if second else (58, 96)
    for i in range(160):
        b = t0 + 0.5 * i
        p = 38 if (i % 4) < 3 else 50
        v = round(en.lerp(bv0, bv1, i / 159.0)) + (6 if i % 8 == 0 else 0)
        sc.note(2, p, b, 0.4, v, jt=2, jv=3)
    # arp: sixteenths, register rising per 4 bars
    sets = ARP_C2 if second else ARP_C1
    for i in range(320):
        b = t0 + 0.25 * i
        w = min(4, i // 64)
        v = round(en.lerp(56 if second else 52, 82 if second else 78,
                          i / 319.0)) + (4 if i % 16 == 0 else 0)
        sc.note(0, sets[w][i % 4], b, 0.22, v, jt=2, jv=3)
    # pad: rising voice-led chords
    en.pad_block(sc, 1, t0,
                 [en.triad(BASE, MODE, d) for d in (1, 6, 3, 7, 1)],
                 span=16.0, size=4, lo=52, hi=76,
                 vel=50 if second else 44, vel_end=68 if second else 62)
    # strings
    if second:
        tones = [69, 72, 74, 76, 77, 79, 81, 82, 84, 86]
        for j, p in enumerate(tones):
            sc.note(7, p, t0 + 8.0 * j, 8.2,
                    round(en.lerp(52, 72, j / 9.0)), jt=3, jv=3)
    else:
        for j, p in enumerate([74, 76, 77, 79, 81]):
            sc.note(7, p, t0 + 40.0 + 8.0 * j, 8.2,
                    round(en.lerp(50, 68, j / 4.0)), jt=3, jv=3)
    # choir joins for the top of the climb
    if second:
        en.pad_block(sc, 8, t0 + 48.0,
                     [en.triad(BASE, MODE, d) for d in (1, 6, 4, 1)],
                     span=8.0, size=3, lo=58, hi=79, vel=56, vel_end=70)
    else:
        en.pad_block(sc, 8, t0 + 64.0,
                     [en.triad(BASE, MODE, 1)] * 2,
                     span=8.0, size=3, lo=58, hi=76, vel=48, vel_end=62)
    # the saw pre-soar into the stall pitch
    sc.note(5, STALL2_PITCH if second else STALL1_PITCH, t0 + 64.0, 16.0,
            56 if second else 54, jt=0, jv=0)
    _climb_kit(sc, t0, second)
    _play_scheduled(sc, t0, t0 + 80.0)


def _stall(sc: en.Score, t0: float, pitch: int) -> None:
    """Near-silence: ONE hanging pedal tone with a CC1 bloom (the soar)."""
    sc.note(14, pitch, t0, 7.9, 50, jt=0, jv=0)
    en.cc_curve(sc, 14, 1, [(t0, 0), (t0 + 3.0, 72), (t0 + 7.5, 8)],
                step=0.25)


def _pivot(sc: en.Score, fills: list[tuple[float, str]], vbump: int) -> None:
    for b, shape in fills:
        material.play_fill(sc, shape, b, vbump=vbump)


def _dive(sc: en.Score, t0: float, second: bool) -> None:
    """Descending cascades under the accelerating tempo map."""
    # the saw swoop: portamento drop of 19 semitones
    en.portamento_on(sc, 5, t0 - 0.25, time_cc=72)
    sc.note(5, 93, t0, 2.0, 90, jt=0, jv=0)
    sc.note(5, 74, t0 + 2.0, 2.0, 86, jt=0, jv=0)
    en.portamento_off(sc, 5, t0 + 4.5)
    # saw descent line
    for j, d in enumerate(range(22, 5, -1)):
        sc.note(5, en.pitch(BASE, MODE, d), t0 + 6.0 + 2.0 * j, 1.8,
                round(en.lerp(82, 70, j / 16.0)), jt=2, jv=2)
    # harp cascades: five 8-beat waterfalls, each window's mean pitch lower
    for w in range(5):
        top = 24 - 2 * w
        for j in range(32):
            sc.note(6, en.pitch(BASE, MODE, top - (j % 16)),
                    t0 + 8.0 * w + 0.25 * j, 0.23,
                    round(en.lerp(80, 68, j / 31.0)), jt=0, jv=3)
    # bass walks the floor down
    roots = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1]
    for bar in range(10):
        rp = en.pitch(38, MODE, roots[bar])
        for k in range(8):
            v = round(en.lerp(74, 96, bar / 9.0)) + (4 if k == 0 else 0)
            sc.note(2, rp, t0 + 4.0 * bar + 0.5 * k, 0.4, v, jt=0, jv=3)
    # lead ship: two hammered descending runs (CC68-slurred)
    en.run(sc, 14, t0 + 8.0, BASE, MODE, list(range(15, 0, -1)), 0.25,
           84, 96, jt=1, legato=True)
    en.run(sc, 14, t0 + 24.0, BASE, MODE, list(range(13, 0, -1)), 0.25,
           88, 100, jt=1, legato=True)
    # wing ship: pedal chugs
    for bar in range(10):
        wp = 50 if bar % 2 == 0 else 45
        for k in range(8):
            v = 84 + (4 if k in (0, 4) else 0)
            sc.note(15, wp, t0 + 4.0 * bar + 0.5 * k, 0.4, v, jt=0, jv=3)
    # kit: driving syncopation + the roll into the pull-out
    sc.note(9, 49, t0, 0.5, 102, jt=0, jv=0)
    for bar in range(10):
        b = t0 + 4.0 * bar
        for off in (0.0, 1.5, 2.5):
            sc.note(9, 36, b + off, 0.25, 96, jt=0, jv=3)
        if bar < 9:                     # bar 9 belongs to the snare roll
            sc.note(9, 38, b + 1.0, 0.25, 88, jt=0, jv=3)
            sc.note(9, 38, b + 3.0, 0.25, 88, jt=0, jv=3)
        for k in range(16):
            sc.note(9, 42, b + 0.25 * k, 0.12, 62 + (6 if k % 4 == 0 else 0),
                    jt=0, jv=3)
    for i in range(16):
        sc.note(9, 38, t0 + 36.0 + 0.25 * i, 0.2,
                round(en.lerp(70, 110, i / 15.0)), jt=0, jv=3)
    # pad drone holds the belly of the dive
    for p, v in ((50, 50), (57, 48), (62, 46)):
        sc.note(1, p, t0, 40.0, v + (6 if second else 0), jt=0, jv=0)
    _riser(sc, t0 + 36.0, 104 if second else 96)
    _play_scheduled(sc, t0, t0 + 40.0)


def _four_floor(sc: en.Score, p: float, bars: int, second: bool) -> None:
    for bar in range(bars):
        b = p + 4.0 * bar
        for k in range(4):
            t = b + k
            sc.note(9, 36, t, 0.25, 108 if second else 104, jt=0, jv=3)
            sc.note(9, 42, t, 0.2, 66 if second else 62, jt=0, jv=3)
            sc.note(9, 46, t + 0.5, 0.4, 56 if second else 52, jt=0, jv=3)
            if second:
                sc.note(9, 42, t + 0.25, 0.12, 44, jt=0, jv=3)
                sc.note(9, 42, t + 0.75, 0.12, 44, jt=0, jv=3)
        for off in (1.0, 3.0):
            sc.note(9, 39, b + off, 0.3, 100 if second else 96, jt=0, jv=3)
            sc.note(9, 38, b + off, 0.25, 100 if second else 94, jt=0, jv=3)


def _counter_phrase(sc: en.Score, p: float) -> None:
    """One 8-bar statement of the DROP2 saw counter-line."""
    for bar in range(8):
        b = p + 4.0 * bar
        sc.note(5, en.pitch(BASE, MODE, CTR_DEGS[bar]), b, 2.0, 88,
                jt=0, jv=2)
        sc.note(5, en.pitch(BASE, MODE, CTR_PASS[bar]), b + 2.75, 0.6, 76,
                jt=0, jv=2)
        if bar in CTR_APPROACH_BARS:
            sc.note(5, en.pitch(BASE, MODE, 24), b + 3.25, 0.5, 72,
                    jt=0, jv=2)


def _drop(sc: en.Score, t0: float, second: bool) -> None:
    """The pull-out: four-on-floor, the hook, four 8-bar phrases."""
    for ph in range(4):
        p = t0 + 32.0 * ph
        # lead ship hook
        for bar in range(8):
            for off, d, du in HOOK_BARS[bar]:
                v = (102 if second else 96) + (6 if off == 0.0 else 0)
                sc.note(14, en.pitch(BASE, MODE, d), p + 4.0 * bar + off,
                        du, v, jt=0, jv=2)
        # wing ship chugs
        for bar in range(8):
            for k in range(8):
                v = (92 if second else 86) + (6 if k == 0 else 0)
                sc.note(15, WING_CHUG[bar], p + 4.0 * bar + 0.5 * k, 0.4,
                        v, jt=0, jv=2)
        # bass cycle
        for bar in range(8):
            for k in range(8):
                bp = BASS_CYCLE[bar] + (12 if k == 5 else 0)
                v = (92 if second else 86) + (8 if k == 0 else 0)
                sc.note(2, bp, p + 4.0 * bar + 0.5 * k, 0.4, v, jt=2, jv=3)
        _four_floor(sc, p, 8, second)
        sc.note(9, 49, p, 0.5, 104, jt=0, jv=0)
        # arp
        cyc = [69, 74, 77, 81] if second else [62, 65, 69, 74]
        for i in range(128):
            v = (64 if second else 58) + (6 if i % 8 == 0 else 0)
            sc.note(0, cyc[i % 4], p + 0.25 * i, 0.22, v, jt=2, jv=3)
        # pad
        en.pad_block(sc, 1, p,
                     [en.triad(BASE, MODE, d)
                      for d in (1, 1, 6, 6, 7, 7, 4, 5)],
                     span=4.0, size=4, lo=52, hi=76,
                     vel=64 if second else 56)
        # strings
        for j in range(4):
            sc.note(7, STR_ROOTS[j], p + 8.0 * j, 8.1,
                    62 if second else 56, jt=3, jv=3)
            if second:
                sc.note(7, STR_ROOTS[j] + 7, p + 8.0 * j, 8.1, 58,
                        jt=3, jv=3)
        # antiphonal posts
        _post_call(sc, 3, p + 4.0, [74, 69, 77], 82)
        _post_call(sc, 4, p + 6.0, [69, 64, 72], 82)
        if second:
            _post_call(sc, 3, p + 20.0, [74, 69, 77], 84)
            _post_call(sc, 4, p + 22.0, [69, 64, 72], 84)
        # orchestra hits (pyro doubles in DROP2)
        if second:
            for off, hp, v in ((0.0, 62, 106), (3.5, 50, 96),
                               (8.0, 62, 100), (11.5, 50, 96)):
                sc.note(12, hp, p + off, 0.9, v, jt=0, jv=2)
        else:
            sc.note(12, 50, p, 0.9, 100, jt=0, jv=2)
            sc.note(12, 50, p + 8.0, 0.9, 92, jt=0, jv=2)
        # saw: sustains in DROP1's back half; the counter-line in DROP2
        if not second and ph >= 2:
            for j in range(4):
                sc.note(5, SAW_D1[j], p + 8.0 * j, 7.5, 54, jt=2, jv=2)
        if second:
            if ph == 0:
                for j, sp in enumerate((86, 82, 84, 81)):
                    sc.note(5, sp, p + 8.0 * j, 7.5, 70, jt=2, jv=2)
            else:
                _counter_phrase(sc, p)
        # choir + harp lift (DROP2 only)
        if second:
            en.pad_block(sc, 8, p,
                         [en.triad(BASE, MODE, d) for d in (1, 6, 7, 1)],
                         span=8.0, size=3, lo=58, hi=79, vel=66)
            for j in range(8):
                sc.note(6, en.pitch(BASE, MODE, 8 + j), p + 0.25 * j, 0.23,
                        72, jt=2, jv=3)
    _riser(sc, t0 + 124.0, 88)
    _play_scheduled(sc, t0, t0 + 128.0)


# ---------------------------------------------------------------------------
# Builders (one per movement)
# ---------------------------------------------------------------------------


def _b_run_in(sc: en.Score) -> None:
    # whole-timeline CC choreography, authored once
    en.cc_curve(sc, 1, 74, CC74_POINTS, step=1.0)
    en.vowel_curve(sc, 8, VOWEL_POINTS, step=1.0)
    # pad drone under the field
    for p, v in ((50, 44), (57, 42), (62, 40)):
        sc.note(1, p, 0.0, 32.0, v, jt=0, jv=0)
    # THE DUO states the ASCENT cell (pinned): lead at 0, wing answer at 8
    material.play_ascent(sc, 14, 0.0, 62, vel=94, jv=0)
    material.play_ascent(sc, 15, 8.0, 50, vel=88, jv=0)
    # taxi riff: duo octaves (unpinned)
    motif = [(8, 0.0, 0.75), (10, 1.0, 0.5), (12, 1.5, 1.0),
             (10, 3.0, 0.5), (8, 3.5, 0.45)]
    for r, t in enumerate((16.0, 20.0, 24.0, 28.0)):
        en.line(sc, 14, t, BASE + 12, MODE, motif, 78 + 4 * r, jt=0, jv=3)
        en.line(sc, 15, t, BASE, MODE, motif, 72 + 4 * r, jt=0, jv=3)
    # engine idle -> spool-up
    for i in range(12):
        sc.note(2, 38, 2.0 * i, 1.7, 46 + 2 * i, jt=3, jv=3)
    for i in range(16):
        sc.note(2, 38 if i % 2 == 0 else 50, 24.0 + 0.5 * i, 0.4, 62 + i,
                jt=2, jv=3)
    # arp wakes
    for i in range(16):
        sc.note(0, [62, 65, 69, 74][i % 4], 16.0 + 0.5 * i, 0.4, 50 + i // 4,
                jt=2, jv=3)
    for i in range(32):
        sc.note(0, [62, 65, 69, 74][i % 4], 24.0 + 0.25 * i, 0.22,
                58 + i // 8, jt=2, jv=3)
    # kit taxis in
    for bar in range(4):
        b = 16.0 + 4.0 * bar
        for k in range(4):
            sc.note(9, 42, b + k, 0.2, 42 + 4 * bar, jt=0, jv=3)
            sc.note(9, 42, b + k + 0.5, 0.15, 36 + 4 * bar, jt=0, jv=3)
        sc.note(9, 36, b, 0.25, 70 + 4 * bar, jt=0, jv=3)
        sc.note(9, 36, b + 2.0, 0.25, 70 + 4 * bar, jt=0, jv=3)
        if bar >= 2:
            sc.note(9, 38, b + 1.0, 0.25, 60 + 4 * bar, jt=0, jv=3)
            sc.note(9, 38, b + 3.0, 0.25, 60 + 4 * bar, jt=0, jv=3)
    sc.note(9, 49, 24.0, 0.5, 72, jt=0, jv=0)
    # radio posts
    _post_call(sc, 3, 20.0, [74, 69, 77], 78)
    _post_call(sc, 4, 22.0, [69, 64, 72], 78)
    _riser(sc, 28.0, 76)
    _play_scheduled(sc, RUN_T0, RUN_T1)


def _b_climb1(sc: en.Score) -> None:
    _climb(sc, C1_T0, LEAD1_DEGS, WING1_DEGS, second=False)


def _b_stall1(sc: en.Score) -> None:
    _stall(sc, S1_T0, STALL1_PITCH)


def _b_pivot1(sc: en.Score) -> None:
    _pivot(sc, PIVOT1_FILLS, vbump=6)


def _b_dive1(sc: en.Score) -> None:
    _dive(sc, D1_T0, second=False)


def _b_drop1(sc: en.Score) -> None:
    _drop(sc, DR1_T0, second=False)


def _b_climb2(sc: en.Score) -> None:
    _climb(sc, C2_T0, LEAD2_DEGS, WING2_DEGS, second=True)


def _b_stall2(sc: en.Score) -> None:
    _stall(sc, S2_T0, STALL2_PITCH)


def _b_pivot2(sc: en.Score) -> None:
    _pivot(sc, PIVOT2_FILLS, vbump=10)


def _b_dive2(sc: en.Score) -> None:
    _dive(sc, D2_T0, second=True)


def _b_drop2(sc: en.Score) -> None:
    _drop(sc, DR2_T0, second=True)


def _b_outro(sc: en.Score) -> None:
    t0 = OUT_T0
    # the flypast lands
    sc.note(9, 49, t0, 0.5, 102, jt=0, jv=0)
    sc.note(12, 62, t0, 0.9, 104, jt=0, jv=0)
    sc.note(14, 74, t0, 3.5, 106, jt=0, jv=0)
    sc.note(15, 50, t0, 3.5, 100, jt=0, jv=0)
    for j in range(15):
        sc.note(6, en.pitch(BASE, MODE, 1 + j), t0 + 0.125 * j, 0.2, 74,
                jt=0, jv=3)
    # the final ASCENT statements (pinned)
    material.play_ascent(sc, 14, 560.0, 62, vel=98, jv=0)
    material.play_ascent(sc, 15, 564.0, 50, vel=92, jv=0)
    # victory lap in octaves
    for j, d in enumerate([15, 12, 13, 15, 14, 12, 10, 8]):
        b = 568.0 + 2.0 * j
        sc.note(14, en.pitch(BASE, MODE, d) + 12, b, 1.9, 94 - j, jt=0, jv=2)
        sc.note(15, en.pitch(BASE, MODE, d), b, 1.9, 88 - j, jt=0, jv=2)
    # final holds (re-picked so they never blip out)
    sc.note(14, 74, 584.0, 8.0, 84, jt=0, jv=0)
    sc.note(14, 74, 592.0, 6.0, 72, jt=0, jv=0)
    sc.note(15, 62, 584.0, 8.0, 80, jt=0, jv=0)
    sc.note(15, 62, 592.0, 6.0, 68, jt=0, jv=0)
    en.cc_curve(sc, 14, 1, [(584.0, 0), (590.0, 60), (597.0, 5)], step=0.5)
    # beds
    for p, v in ((50, 54), (57, 52), (62, 50), (65, 48)):
        sc.note(1, p, t0, 44.0, v, jt=0, jv=0)
    for p, v in ((62, 60), (65, 58), (69, 56)):
        sc.note(8, p, t0, 28.0, v, jt=0, jv=0)
    for p, v in ((62, 46), (65, 44), (69, 42)):
        sc.note(8, p, 584.0, 14.0, v, jt=0, jv=0)
    sc.note(7, 74, 560.0, 20.0, 56, jt=3, jv=3)
    sc.note(7, 69, 580.0, 18.0, 50, jt=3, jv=3)
    for j in range(9):
        sc.note(2, 38, t0 + 4.0 * j, 3.5, 76 - 3 * j, jt=2, jv=3)
    sc.note(2, 38, 592.0, 6.0, 56, jt=0, jv=0)
    for i in range(64):
        sc.note(0, [62, 65, 69, 74][i % 4], t0 + 0.5 * i, 0.4,
                round(en.lerp(56, 42, i / 63.0)), jt=2, jv=3)
    # kit throttles back
    for bar in range(4):
        b = t0 + 4.0 * bar
        for k in range(4):
            sc.note(9, 36, b + k, 0.25, 92 - 4 * bar, jt=0, jv=3)
            sc.note(9, 42, b + k, 0.2, 54 - 3 * bar, jt=0, jv=3)
        for off in (1.0, 3.0):
            sc.note(9, 39, b + off, 0.3, 84 - 4 * bar, jt=0, jv=3)
    for bar in range(4):
        b = t0 + 16.0 + 4.0 * bar
        sc.note(9, 36, b, 0.25, 72 - 3 * bar, jt=0, jv=3)
        sc.note(9, 36, b + 2.0, 0.25, 66 - 3 * bar, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, b + 0.5 * k, 0.15, 44 - 3 * bar, jt=0, jv=3)
    sc.note(9, 49, 584.0, 0.5, 88, jt=0, jv=0)
    sc.note(12, 62, 584.0, 0.9, 96, jt=0, jv=0)
    sc.note(9, 36, 596.0, 0.25, 88, jt=0, jv=0)
    sc.note(9, 49, 596.0, 0.5, 92, jt=0, jv=0)
    sc.note(12, 50, 596.0, 0.9, 92, jt=0, jv=0)
    # posts wave goodbye
    _post_call(sc, 3, 566.0, [74, 69, 77], 76)
    _post_call(sc, 4, 568.0, [69, 64, 72], 76)
    _play_scheduled(sc, OUT_T0, OUT_T1)


BUILDERS = [_b_run_in, _b_climb1, _b_stall1, _b_pivot1, _b_dive1, _b_drop1,
            _b_climb2, _b_stall2, _b_pivot2, _b_dive2, _b_drop2, _b_outro]

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 set)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_MILD = _CONSONANT | {2, 10}          # climbs may pass whole-tone shudders
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


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, _p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _ons_between(sc, ch, lo, hi):
    t0, t1 = _tick(lo), _tick(hi)
    return [(t, p, v) for t, p, v in _note_ons(sc, ch) if t0 <= t < t1]


def _all_ons_between(sc, lo, hi):
    out = []
    for ch in sc.events:
        for t, p, v in _ons_between(sc, ch, lo, hi):
            out.append((ch, t, p, v))
    return sorted(out, key=lambda e: e[1])


def _downbeat_pitches(sc, ch, t0, count):
    """The single pinned onset at each bar line, or None."""
    ons = _note_ons(sc, ch)
    by_tick = {}
    for t, p, _v in ons:
        by_tick.setdefault(t, []).append(p)
    out = []
    for i in range(count):
        cand = by_tick.get(_tick(t0 + 4.0 * i), [])
        out.append(cand[0] if len(cand) == 1 else None)
    return out


# ---------------------------------------------------------------------------
# Track oracles
# ---------------------------------------------------------------------------


def _o_climb_monotone(sc):
    fails = []
    sums = _bar_sums(sc)
    peaks = []
    for tag, t0 in (("C1", C1_T0), ("C2", C2_T0)):
        downs = _downbeat_pitches(sc, 14, t0, 20)
        if None in downs:
            fails.append(f"{tag}: lead downbeat missing/ambiguous at bar "
                         f"{downs.index(None)}")
            continue
        if any(b <= a for a, b in zip(downs, downs[1:])):
            fails.append(f"{tag}: lead downbeats not strictly rising: {downs}")
        peaks.append(max(downs))
        masses = [_mean_barsum(sums, t0 + 16.0 * w, t0 + 16.0 * (w + 1))
                  for w in range(5)]
        if any(b <= a for a, b in zip(masses, masses[1:])):
            fails.append(f"{tag}: 4-bar velocity masses not strictly rising: "
                         f"{[round(m) for m in masses]}")
    if len(peaks) == 2 and peaks[1] <= peaks[0]:
        fails.append(f"CLIMB2 peak {peaks[1]} must top CLIMB1 peak {peaks[0]}")
    return fails


def _o_duo_contrary_cross(sc):
    fails = []
    for tag, t0, cross_beat in (("C1", C1_T0, CROSS1_BEAT),
                                ("C2", C2_T0, CROSS2_BEAT)):
        lead = _downbeat_pitches(sc, 14, t0, 20)
        wing = _downbeat_pitches(sc, 15, t0, 20)
        if None in lead or None in wing:
            fails.append(f"{tag}: a duo downbeat is missing")
            continue
        if any(b >= a for a, b in zip(wing, wing[1:])):
            fails.append(f"{tag}: wing downbeats not strictly falling")
        bad = [i for i, (l, w) in enumerate(zip(lead, wing))
               if (w - l) % 12 not in _MILD]
        if bad:
            fails.append(f"{tag}: harsh duo interval at bars {bad}")
        if wing[0] - lead[0] < 12:
            fails.append(f"{tag}: opening spread {wing[0] - lead[0]} < 12")
        if lead[-1] - wing[-1] < 12:
            fails.append(f"{tag}: closing swap {lead[-1] - wing[-1]} < 12")
        cross = next((i for i in range(20) if lead[i] >= wing[i]), None)
        if cross != CROSS_BAR:
            fails.append(f"{tag}: crossing at bar {cross}, pinned "
                         f"{CROSS_BAR} (beat {cross_beat})")
        elif lead[CROSS_BAR] != wing[CROSS_BAR]:
            fails.append(f"{tag}: ships must MEET in unison at the cross")
        if any(lead[i] >= wing[i] for i in range(CROSS_BAR)) or \
                any(lead[i] <= wing[i] for i in range(CROSS_BAR + 1, 20)):
            fails.append(f"{tag}: register swap not clean around the cross")
    return fails


def _o_stall_hush(sc):
    fails = []
    for tag, s0, s1, pin, c0 in (("S1", S1_T0, S1_T1, STALL1_PITCH, C1_T0),
                                 ("S2", S2_T0, S2_T1, STALL2_PITCH, C2_T0)):
        ons = _all_ons_between(sc, s0, s1)
        if len(ons) != 1:
            fails.append(f"{tag}: {len(ons)} note-ons in the stall, want "
                         f"exactly 1 (the pedal)")
            continue
        ch, t, p, v = ons[0]
        if ch != 14 or p != pin or t != _tick(s0):
            fails.append(f"{tag}: pedal is ch{ch} pitch {p}, want ch14 "
                         f"pitch {pin} at beat {s0}")
        if v > 60:
            fails.append(f"{tag}: pedal velocity {v} > 60 (not a hush)")
        span = [s for s in _note_spans(sc, 14) if s[0] == _tick(s0)]
        if not span or span[0][1] - span[0][0] < 7.5 * _PPQ:
            fails.append(f"{tag}: pedal shorter than 7.5 beats")
        cc1 = [val for b, val in _cc_lane(sc, 14, 1)
               if _tick(s0) <= b <= _tick(s1)]
        if not cc1 or max(cc1) < 40:
            fails.append(f"{tag}: no CC1 bloom on the stall soar")
        # velocity mass < 10% of the climb's own 8-beat peak
        climb = _all_ons_between(sc, c0, c0 + 80.0)
        peak = 0.0
        for w0 in range(int(c0), int(c0 + 80.0) - 7, 4):
            peak = max(peak, sum(v for _c, t2, _p, v in climb
                                 if _tick(w0) <= t2 < _tick(w0 + 8.0)))
        if v >= 0.10 * peak:
            fails.append(f"{tag}: stall mass {v} >= 10% of climb peak "
                         f"window {peak:.0f}")
    return fails


def _o_pivot_fills_only(sc):
    fails = []
    counts = []
    for tag, p0, p1, fills in (("P1", P1_T0, P1_T1, PIVOT1_FILLS),
                               ("P2", P2_T0, P2_T1, PIVOT2_FILLS)):
        ons = _all_ons_between(sc, p0, p1)
        alien = [ch for ch, _t, _p, _v in ons if ch not in (10, 11)]
        if alien:
            fails.append(f"{tag}: non-fill channels sound in the cadenza: "
                         f"{sorted(set(alien))}")
        want = sum(material.fill_note_count(s) for _b, s in fills)
        if len(ons) != want:
            fails.append(f"{tag}: {len(ons)} cadenza notes, schedule says "
                         f"{want}")
        counts.append(len(ons))
    if counts[0] < 18:
        fails.append(f"P1 cadenza too small: {counts[0]} < 18")
    if counts[1] <= counts[0]:
        fails.append(f"P2 ({counts[1]}) must out-fill P1 ({counts[0]})")
    return fails


def _o_dive_descent_and_accel(sc):
    fails = []
    if sorted(sc.tempos) != sorted(TEMPO_MAP):
        fails.append("tempo map drifted from the pinned dive accelerations")
    for (d0, ret) in ((D1_T0, DR1_T0), (D2_T0, DR2_T0)):
        ramp = [bpm for b, bpm in sorted(TEMPO_MAP) if d0 <= b < ret]
        if ramp != [129.0, 132.0, 135.0, 138.0]:
            fails.append(f"dive at {d0}: ramp {ramp} != 129..138")
        back = [bpm for b, bpm in TEMPO_MAP if b == ret]
        if back != [126.0]:
            fails.append(f"pull-out at {ret} must return to 126")
        # harp cascade centroid strictly falls, window over window
        means = []
        for w in range(5):
            notes = _ons_between(sc, 6, d0 + 8.0 * w, d0 + 8.0 * (w + 1))
            if not notes:
                fails.append(f"dive at {d0}: harp silent in window {w}")
                break
            means.append(sum(p for _t, p, _v in notes) / len(notes))
        if len(means) == 5 and any(b >= a for a, b in zip(means, means[1:])):
            fails.append(f"dive at {d0}: cascade centroid not strictly "
                         f"falling: {[round(m, 1) for m in means]}")
        # the swoop: >=12-semitone portamento drop at the dive lip
        saws = _ons_between(sc, 5, d0, d0 + 4.0)
        if len(saws) < 2 or saws[0][1] < 90 or \
                saws[0][1] - saws[1][1] < 12:
            fails.append(f"dive at {d0}: no >=12-semitone swoop from >=90")
        cc65 = [(b, val) for b, val in _cc_lane(sc, 5, 65)
                if _tick(d0 - 1.0) <= b <= _tick(d0 + 2.0)]
        if not any(val == 127 for _b, val in cc65):
            fails.append(f"dive at {d0}: portamento switch (CC65) not on")
    return fails


def _o_build_drop_contour(sc):
    fails = []
    sums = _bar_sums(sc)
    m_run = _mean_barsum(sums, RUN_T0, RUN_T1)
    m_d1 = _mean_barsum(sums, DR1_T0, DR1_T1)
    m_d2 = _mean_barsum(sums, DR2_T0, DR2_T1)
    if m_d2 <= m_d1:
        fails.append(f"DROP2 mean bar mass {m_d2:.0f} must exceed DROP1 "
                     f"{m_d1:.0f}")
    if m_d1 <= 2.0 * m_run:
        fails.append(f"DROP1 {m_d1:.0f} must dwarf the run-in {m_run:.0f}")
    return fails


def _o_fill_escalation(sc):
    fails = []
    fons = sorted((t, p) for ch in (10, 11) for t, p, _v in _note_ons(sc, ch))

    def count(lo, hi):
        return sum(1 for t, _p in fons if _tick(lo) <= t < _tick(hi))

    for tag, b0 in (("C1", C1_T0), ("C2", C2_T0)):
        counts, expect = [], []
        for w in range(5):
            lo, hi = b0 + 16.0 * w, b0 + 16.0 * (w + 1)
            counts.append(count(lo, hi))
            expect.append(sum(material.fill_note_count(s)
                              for b, s in FILL_SCHEDULE if lo <= b < hi))
        if counts != expect:
            fails.append(f"{tag}: fill windows {counts} drifted from the "
                         f"schedule {expect}")
        if any(b <= a for a, b in zip(counts, counts[1:])):
            fails.append(f"{tag}: fill escalation not strict: {counts}")
        shapes = {s for b, s in FILL_SCHEDULE if b0 <= b < b0 + 80.0}
        if len(shapes) < 5:
            fails.append(f"{tag}: only {len(shapes)} fill shapes, want >=5")
    for drop in (DR1_T0, DR2_T0):
        chain = [t for t, _p in fons
                 if _tick(drop - 4.25) <= t < _tick(drop)]
        if len(chain) < 20:
            fails.append(f"drop at {drop}: chain has {len(chain)} notes, "
                         f"want >=20 unbroken")
            continue
        gaps = [(b - a) / _PPQ for a, b in zip(chain, chain[1:])]
        if max(gaps) > 0.5:
            fails.append(f"drop at {drop}: chain broken (gap "
                         f"{max(gaps):.2f} beats)")
        if chain[-1] < _tick(drop - 0.5):
            fails.append(f"drop at {drop}: chain stops early")
    for d0, d1 in ((DR1_T0, DR1_T1), (DR2_T0, DR2_T1)):
        for w in range(8):
            c = count(d0 + 16.0 * w, d0 + 16.0 * (w + 1))
            if c > 12:
                fails.append(f"drop window at {d0 + 16.0 * w}: {c} fill "
                             f"notes > the thinning cap 12")
    return fails


def _o_ascent_statements(sc):
    fails = []
    pins = [(0.0, 14, 62), (8.0, 15, 50), (560.0, 14, 62), (564.0, 15, 50)]
    for t0, ch, root in pins:
        ons = {(t, p) for t, p, _v in _note_ons(sc, ch)}
        for on, du, semi in material.ASCENT_CELL:
            if (_tick(t0 + on), root + semi) not in ons:
                fails.append(f"ASCENT at {t0} ch{ch}: missing note "
                             f"{root + semi} at +{on}")
        hang = [s for s in _note_spans(sc, ch)
                if s[0] == _tick(t0 + 1.5) and s[2] == root + 19]
        if not hang or hang[0][1] - hang[0][0] < 2.0 * _PPQ:
            fails.append(f"ASCENT at {t0} ch{ch}: hang not held >=2 beats")
    return fails


def _o_soar_and_sweep(sc):
    fails = []
    lane = _cc_lane(sc, 1, 74)
    if len(lane) < 100:
        fails.append(f"pad CC74 lane too sparse ({len(lane)} events)")
    vals = [v for _t, v in lane]
    if not vals or max(vals) - min(vals) < 60:
        fails.append("CC74 macro-sweep spans < 60 units")

    def at(beat):
        prior = [v for t, v in lane if t <= _tick(beat)]
        return prior[-1] if prior else None

    v_lo, v_hi, v_dump = at(33.0), at(108.0), at(120.0)
    if v_lo is None or v_hi is None or v_hi - v_lo < 60:
        fails.append(f"CC74 climb sweep {v_lo}->{v_hi} rises < 60")
    if v_dump is None or v_dump > 50:
        fails.append(f"CC74 must dump for the stall (got {v_dump})")
    spans13 = _note_spans(sc, 13)
    for lift in (C1_T0, DR1_T0, C2_T0, DR2_T0, OUT_T0):
        hit = [s for s in spans13
               if _tick(lift - 4.5) <= s[0] <= _tick(lift - 3.4)
               and s[1] - s[0] >= 3.5 * _PPQ]
        if not hit:
            fails.append(f"no riser into the lift at beat {lift}")
    return fails


def _o_drop2_counterpoint(sc):
    fails = []
    hook = [en.pitch(BASE, MODE, d) for d in HOOK_DOWN_DEGS]
    ctr = [en.pitch(BASE, MODE, d) for d in CTR_DEGS]
    lead_ticks = {t for t, _p, _v in _note_ons(sc, 14)}
    for p0 in (460.0, 492.0, 524.0):
        lp = _downbeat_pitches(sc, 14, p0, 8)
        for bar in range(8):
            if lp[bar] != hook[bar]:
                fails.append(f"phrase {p0} bar {bar}: hook downbeat "
                             f"{lp[bar]} != pinned {hook[bar]}")
        c_by_tick = {}
        for t, p, _v in _ons_between(sc, 5, p0, p0 + 32.0):
            c_by_tick.setdefault(t, []).append(p)
        cp = [c_by_tick.get(_tick(p0 + 4.0 * bar), [None])[0]
              for bar in range(8)]
        if None in cp:
            fails.append(f"phrase {p0}: counter missing a downbeat")
            continue
        for bar in range(8):
            if cp[bar] != ctr[bar]:
                fails.append(f"phrase {p0} bar {bar}: counter {cp[bar]} != "
                             f"pinned {ctr[bar]}")
        bad = [b for b in range(8) if (cp[b] - hook[b]) % 12 not in _CONSONANT]
        if bad:
            fails.append(f"phrase {p0}: dissonant downbeats at bars {bad}")
        doub = sum(1 for b in range(8) if (cp[b] - hook[b]) % 12 == 0)
        if doub > 2:
            fails.append(f"phrase {p0}: {doub}/8 pitch-class doublings > 25%")
        good = 0
        for b in range(1, 8):
            dl, dc = hook[b] - hook[b - 1], cp[b] - cp[b - 1]
            if dc == 0 or dl == 0 or (dc > 0) != (dl > 0):
                good += 1
        if good / 7.0 < 0.6:
            fails.append(f"phrase {p0}: contrary+oblique {good}/7 < 60%")
        c_ticks = sorted(c_by_tick)
        off_grid = sum(1 for t in c_ticks if t not in lead_ticks)
        if off_grid / max(1, len(c_ticks)) < 0.5:
            fails.append(f"phrase {p0}: only {off_grid}/{len(c_ticks)} "
                         f"counter onsets independent of the hook")
    return fails


def _o_layered_climax(sc):
    fails = []
    for tag, lo, hi, want in (("DROP1", DR1_T0, DR1_T1, 13),
                              ("DROP2", DR2_T0, DR2_T1, 15)):
        active = {ch for ch in sc.events if _ons_between(sc, ch, lo, hi)}
        if len(active) < want:
            fails.append(f"{tag}: {len(active)} active channels < {want}")
    return fails


def oracles(sc, info, spans):
    return [
        ("climb_monotone", _o_climb_monotone(sc)),
        ("duo_contrary_cross", _o_duo_contrary_cross(sc)),
        ("stall_hush", _o_stall_hush(sc)),
        ("pivot_fills_only", _o_pivot_fills_only(sc)),
        ("dive_descent_and_accel", _o_dive_descent_and_accel(sc)),
        ("build_drop_contour", _o_build_drop_contour(sc)),
        ("fill_escalation", _o_fill_escalation(sc)),
        ("ascent_statements", _o_ascent_statements(sc)),
        ("soar_and_sweep", _o_soar_and_sweep(sc)),
        ("drop2_counterpoint", _o_drop2_counterpoint(sc)),
        ("layered_climax", _o_layered_climax(sc)),
    ]
