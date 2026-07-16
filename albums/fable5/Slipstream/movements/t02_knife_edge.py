"""t02_knife_edge — Track 2 "Knife Edge": the 90-degree pass.

The aircraft rolls to ninety degrees and holds the pass on rudder alone —
unstable, thrilling, always about to fall out of the sky.  A aeolian,
144 bpm, ~4:13.  The instability is METRIC: the verses ride a 7/8 knife
(2+2+3, pinned kit accents) and only the drops lock the floor back to 4/4.

THE DUO — formation TRADES.  In the EDGE sections the two ships alternate
strict one-bar (7/8) trades — lead ship on the even bars, wing ship on the
odd bars, an octave below — and NEVER sound together (oracle: zero
overlapping sounding spans, every bar occupied, strict alternation).  In
the DROPs they lock to rhythmic unison: both ships emitted from one riff
table, every pair a power-chord interval (7, 12 or 19 semitones), all
velocities 85+.  Both guitars stay centred (CC10 64) for the whole piece.

THE SHAPE.  Cold taxi (the lead ship states material.ASCENT_CELL as the
track's first notes, solo) -> EDGE ONE (32 bars of 7/8 trades, four
strictly-rising velocity-mass windows, fills escalating 6 < 19 < 28 < 67)
-> DROP ONE (32 bars of 4/4: four-on-floor, duo lockstep, antiphonal
posts) -> EDGE TWO (28 bars, tighter trades: sixteenth cells, ghost hats,
saw soars overhead) -> THE WOBBLE (8 bars: the lead ship holds a tone
while the bend lane rocks through pinned INTEGER plateaus +1/-1/+2/-2 —
the aircraft fighting the roll; the mix hushes under half of drop one) ->
BUILD (16 bars of 4/4, rising windows, the pad's 72-unit CC74 macro-sweep,
a CC65 portamento swoop hurling the saw up an octave, ASCENT_CELL restated
into the drop) -> DROP TWO (36 bars, > drop one by mean per-bar velocity
mass: 16 active channels, saw soars >= 6 beats with CC1 blooms, a choir
counter-line in verified two-part counterpoint against the saw, harp
sixteenths and double-time hats from the mid-drop lift) -> THE SNAP: on
the downbeat of bar 601+1 the track simply STOPS — one <= 0.5-beat unison
stab (guitars an octave apart), 3.5 beats of scored silence
(gap-whitelisted), one choked cymbal.  Ear-catching by amputation.

Every headline claim is a falsifiable oracle below (the repo method:
oracles first, music composed to pass).  No T361 quotes anywhere — an
oracle proves the orbit riff's interval signature never appears.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 2
TITLE = "Knife Edge"
FILE = "02 - Knife Edge.mid"
SEED = 20261102

COMMENT = ("Slipstream act two: the knife-edge pass.  7/8 verses (2+2+3) "
           "where the two guitars trade strict one-bar phrases and never "
           "sound together; 4/4 drops where they lock to power-chord "
           "unison.  The wobble bridge rocks the bend lane through "
           "integer plateaus; drop two stacks 16 channels and a "
           "saw-vs-choir counterpoint; the track ends on a single unison "
           "stab, silence, and one choked cymbal.")

# ---------------------------------------------------------------------------
# Grid.  144 bpm throughout; the meter does the destabilising.
# 7/8 bars are 3.5 beats long; every section boundary is a bar boundary.
# ---------------------------------------------------------------------------

BPM = 144.0
BAR78 = 3.5

TAXI = (0.0, 28.0)          # 8 bars of 7/8 — the cold taxi
EDGE1 = (28.0, 140.0)       # 32 bars of 7/8 — trades, first climb
DROP1 = (140.0, 268.0)      # 32 bars of 4/4 — the locks
EDGE2 = (268.0, 366.0)      # 28 bars of 7/8 — tighter trades
BRIDGE = (366.0, 394.0)     # 8 bars of 7/8 — the wobble (bends)
BUILD = (394.0, 458.0)      # 16 bars of 4/4 — the second climb
DROP2 = (458.0, 602.0)      # 36 bars of 4/4 — the full pass
SNAP = (602.0, 610.0)       # the stab, the silence, the choke
END = SNAP[1]

MOVS: list[tuple[str, float, float]] = [
    ("I. Taxi", *TAXI),
    ("II. Edge One (7/8 trades)", *EDGE1),
    ("III. Drop One (4/4 locks)", *DROP1),
    ("IV. Edge Two (tighter)", *EDGE2),
    ("V. The Wobble", *BRIDGE),
    ("VI. Build", *BUILD),
    ("VII. Drop Two", *DROP2),
    ("VIII. The Snap", *SNAP),
]

MODE = "aeolian"                       # A aeolian
ROOT_GTR = 57                          # A3 — lead-ship base
ROOT_WING = 45                         # A2 — wing-ship base

TIMESIGS: list[tuple[float, int, int]] = [
    (0.0, 7, 8), (DROP1[0], 4, 4), (EDGE2[0], 7, 8), (BUILD[0], 4, 4)]

# ---------------------------------------------------------------------------
# Channels.
# ---------------------------------------------------------------------------

CH_ARP, CH_PAD, CH_BASS, CH_POST_L, CH_POST_R = 0, 1, 2, 3, 4
CH_SAW, CH_HARP, CH_STR, CH_CHOIR = 5, 6, 7, 8
CH_KIT, CH_TOMS, CH_SYN, CH_HIT, CH_RISER = 9, 10, 11, 12, 13
CH_LEAD, CH_WING = 14, 15

PAN_POST_L, PAN_POST_R = 18, 110       # fixed antiphonal posts (transient)

# ---------------------------------------------------------------------------
# Harmony.  Tonic pedal in the 7/8 sections (the knife holds its line);
# chord loops only where the floor is 4/4.  8 beats per chord.
# ---------------------------------------------------------------------------

DROP1_LOOP = (1, 6, 7, 5)              # Am F G Em
DROP2_LOOP = (1, 6, 3, 7)              # Am F C G — the brighter, bigger pass
BUILD_LOOP = (1, 6, 7, 5)
DROP2_TAIL = 586.0                     # from here everything hammers the tonic

BASS_ROOT = {1: 45, 6: 41, 3: 48, 7: 43, 5: 40}     # A2 F2 C3 G2 E2
WING_ROOT = {1: 45, 6: 41, 3: 48, 7: 43, 5: 40}
POST_ROOT = {1: 69, 6: 65, 3: 72, 7: 67, 5: 64}     # A4 F4 C5 G4 E4
HIT_ROOT = {1: 57, 6: 53, 3: 48, 7: 55, 5: 52}      # A3 F3 C3 G3 E3
STR_ROOT = {1: 57, 6: 53, 3: 48, 7: 55, 5: 52}


def _chord_deg(beat: float) -> int:
    if DROP1[0] <= beat < DROP1[1]:
        return DROP1_LOOP[int((beat - DROP1[0]) // 8.0) % 4]
    if BUILD[0] <= beat < BUILD[1]:
        return BUILD_LOOP[int((beat - BUILD[0]) // 8.0) % 4]
    if DROP2[0] <= beat < DROP2_TAIL:
        return DROP2_LOOP[int((beat - DROP2[0]) // 8.0) % 4]
    return 1


# ---------------------------------------------------------------------------
# The trade cells — the duo's 7/8 vocabulary.  (offset, degree, dur) with
# degrees in A aeolian relative to each ship's base; every cell ends before
# beat 3.5 so a one-bar trade can never bleed into the other ship's bar.
# ---------------------------------------------------------------------------

CELLS: dict[str, list[tuple[float, int, float]]] = {
    "hook": [(0.0, 1, 0.45), (0.5, 1, 0.2), (0.75, 5, 0.2), (1.0, 8, 0.45),
             (1.5, 7, 0.2), (1.75, 8, 0.2), (2.0, 10, 0.7), (2.75, 8, 0.3),
             (3.125, 5, 0.25)],
    "answer": [(0.0, 8, 0.45), (0.5, 7, 0.45), (1.0, 5, 0.45),
               (1.5, 4, 0.2), (1.75, 3, 0.2), (2.0, 1, 0.7),
               (2.75, 0, 0.3), (3.125, 1, 0.25)],
    "climb": [(0.0, 1, 0.2), (0.25, 3, 0.2), (0.5, 4, 0.2), (0.75, 5, 0.2),
              (1.0, 7, 0.2), (1.25, 8, 0.2), (1.5, 10, 0.45),
              (2.0, 12, 0.85), (3.0, 10, 0.35)],
    "stab": [(0.0, 1, 0.2), (0.25, 1, 0.2), (0.5, 8, 0.4), (1.0, 1, 0.2),
             (1.25, 1, 0.2), (1.5, 8, 0.4), (2.0, 1, 0.2), (2.25, 1, 0.2),
             (2.5, 10, 0.4), (3.0, 8, 0.35)],
    "falls": [(0.0, 12, 0.2), (0.25, 10, 0.2), (0.5, 8, 0.2),
              (0.75, 7, 0.2), (1.0, 5, 0.2), (1.25, 4, 0.2), (1.5, 3, 0.4),
              (2.0, 5, 0.4), (2.5, 4, 0.2), (2.75, 3, 0.2), (3.0, 1, 0.35)],
    "coil": [(0.0, 1, 0.18), (0.25, 3, 0.18), (0.5, 4, 0.18),
             (0.75, 5, 0.18), (1.0, 4, 0.18), (1.25, 5, 0.18),
             (1.5, 7, 0.18), (1.75, 8, 0.18), (2.0, 7, 0.18),
             (2.25, 8, 0.18), (2.5, 10, 0.18), (2.75, 8, 0.18),
             (3.0, 12, 0.4)],
    "shear": [(0.0, 8, 0.18), (0.25, 7, 0.18), (0.5, 8, 0.18),
              (0.75, 10, 0.18), (1.0, 8, 0.18), (1.25, 7, 0.18),
              (1.5, 5, 0.18), (1.75, 4, 0.18), (2.0, 5, 0.4),
              (2.5, 3, 0.18), (2.75, 2, 0.18), (3.0, 1, 0.4)],
}

# Bar-by-bar trade schedules: even index = lead ship (ch14, base A3),
# odd index = wing ship (ch15, base A2).  EDGE TWO leans on the sixteenth
# cells ("coil"/"shear") — the tighter trades.
EDGE1_SCHED: list[str] = [
    "hook", "answer", "hook", "answer", "climb", "falls", "stab", "answer",
    "hook", "answer", "climb", "shear", "stab", "falls", "hook", "answer",
    "climb", "answer", "stab", "falls", "hook", "shear", "climb", "answer",
    "stab", "falls", "hook", "answer", "climb", "shear", "coil", "falls",
]
EDGE2_SCHED: list[str] = [
    "coil", "shear", "stab", "falls", "coil", "answer", "climb", "shear",
    "coil", "falls", "stab", "shear", "coil", "answer", "climb", "shear",
    "coil", "falls", "stab", "shear", "coil", "answer", "coil", "shear",
    "climb", "falls", "coil", "shear",
]
assert len(EDGE1_SCHED) == 32 and len(EDGE2_SCHED) == 28

# The taxi: the duo's pre-echo of the trades (unpinned, but never
# overlapping).  (channel, cell, base, start, vel).
TAXI_GUITAR: list[tuple[int, str, int, float, int]] = [
    (CH_LEAD, "hook", ROOT_GTR, 5.25, 84),
    (CH_WING, "answer", ROOT_WING, 10.5, 80),
    (CH_LEAD, "stab", ROOT_GTR, 17.5, 88),
    (CH_WING, "answer", ROOT_WING, 21.0, 84),
    (CH_LEAD, "climb", ROOT_GTR, 24.5, 92),
]

# The two pinned ASCENT_CELL statements (root A3): the track's very first
# notes, and the launch out of the build into drop two.
ASCENT_STARTS = (0.0, 454.0)

# ---------------------------------------------------------------------------
# The drop riffs — the duo in LOCKSTEP.  Both ships are emitted from one
# table: (offset-in-chord, dur, interval, accent).  wing = chord root
# (chug register), lead = wing + interval (7 = fifth, 12 = octave,
# 19 = octave+fifth) — power-chord pairs, never the same pitch.
# ---------------------------------------------------------------------------

RIFF_D1: list[tuple[float, float, int, int]] = [
    (0.0, 0.7, 12, 1), (0.75, 0.2, 12, 0), (1.0, 0.45, 12, 0),
    (1.5, 0.45, 7, 0), (2.0, 0.7, 12, 1), (2.75, 0.2, 12, 0),
    (3.0, 0.45, 7, 0), (3.5, 0.45, 12, 0), (4.0, 0.7, 12, 1),
    (4.75, 0.2, 12, 0), (5.0, 0.45, 12, 0), (5.5, 0.45, 7, 0),
    (6.0, 0.45, 12, 1), (6.5, 0.45, 7, 0), (7.0, 0.9, 12, 1),
]
RIFF_D2: list[tuple[float, float, int, int]] = [
    (0.0, 0.45, 12, 1), (0.5, 0.2, 12, 0), (0.75, 0.2, 12, 0),
    (1.0, 0.4, 7, 0), (1.5, 0.4, 12, 0), (2.0, 0.45, 19, 1),
    (2.5, 0.2, 12, 0), (2.75, 0.2, 12, 0), (3.0, 0.4, 7, 0),
    (3.5, 0.4, 12, 0), (4.0, 0.45, 12, 1), (4.5, 0.2, 12, 0),
    (4.75, 0.2, 12, 0), (5.0, 0.4, 7, 0), (5.5, 0.4, 12, 0),
    (6.0, 0.45, 19, 1), (6.5, 0.4, 12, 0), (7.0, 0.4, 7, 0),
    (7.5, 0.45, 12, 0),
]
LOCK_INTERVALS = {7, 12, 19}

# Build: the lead ship's rising pickups (explicit; the ascent follows).
BUILD_LEAD: list[tuple[float, int, float, int]] = [
    (410.0, 55, 0.45, 88), (418.0, 52, 0.45, 90), (426.0, 57, 0.7, 92),
    (434.0, 53, 0.7, 94), (442.0, 55, 0.7, 96), (450.0, 52, 0.45, 98),
    (452.0, 55, 0.45, 100),
]

# ---------------------------------------------------------------------------
# The wobble — the bridge's marked bend gestures on the lead ship.  One
# integer target per 7/8 bar; the lane ramps up over 0.3 beats, holds the
# plateau, ramps home, and is recentred to 0 before the movement boundary.
# The emitter and the oracle share _wobble_events(), so the written lane is
# provably exactly this table.
# ---------------------------------------------------------------------------

WOBBLE: tuple[int, ...] = (1, -1, 1, -1, 2, -2, 2, 1)


def _wobble_events() -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for k, target in enumerate(WOBBLE):
        bar = BRIDGE[0] + BAR78 * k
        for i in range(6):
            x = i / 5.0
            out.append((bar + 0.75 + 0.3 * x, target * x))
        for i in range(6):
            x = i / 5.0
            out.append((bar + 2.45 + 0.3 * x, target * (1.0 - x)))
    out.append((BRIDGE[1] - 0.6, 0.0))
    return out


# ---------------------------------------------------------------------------
# The saw — soars in EDGE TWO, the swoop out of the build, and the drop-two
# lead line (the counterpoint reference voice).  (onset, pitch, dur);
# notes >= 4 beats get a CC1 bloom; >= 6-beat notes are the pinned soars.
# ---------------------------------------------------------------------------

SAW_E2: list[tuple[float, int, float]] = [
    (272.0, 76, 6.5), (283.0, 79, 6.0), (293.5, 81, 6.5), (304.0, 83, 6.5),
    (314.5, 81, 6.0), (325.0, 84, 6.5), (335.5, 83, 6.0), (346.0, 84, 6.5),
    (356.5, 81, 6.0),
]
SAW_BUILD: list[tuple[float, int, float]] = [
    (398.0, 64, 1.5), (406.0, 67, 1.5), (414.0, 69, 1.5), (422.0, 71, 1.5),
    (430.0, 72, 2.5), (438.0, 74, 2.5), (446.0, 76, 3.0), (452.0, 79, 2.0),
    (456.0, 69, 2.05),      # the swoop launch: CC65 glides 69 -> 81
]
SWOOP_ON, SWOOP_OFF = 455.9, 460.0

SAW_D2: list[tuple[float, int, float]] = [
    (458.0, 81, 6.0),                                       # soar 1
    (464.5, 79, 0.75), (465.25, 83, 0.75),
    (466.0, 84, 3.0), (469.0, 81, 1.0), (470.0, 84, 2.0), (472.0, 83, 1.0),
    (473.0, 81, 1.0),
    (474.0, 79, 4.0), (478.0, 88, 2.0), (480.0, 86, 2.5),
    (482.5, 83, 1.0), (483.5, 81, 0.5),
    (484.0, 83, 2.5), (486.5, 81, 0.75), (487.25, 79, 0.75),
    (488.0, 81, 6.0),                                       # soar 2
    (494.0, 79, 0.75), (494.75, 77, 0.75), (495.5, 76, 0.5),
    (496.0, 77, 1.0), (497.0, 79, 1.0),
    (498.0, 81, 3.0), (501.0, 84, 1.0),
    (502.0, 81, 2.0), (504.0, 86, 2.0),
    (506.0, 79, 4.5), (510.5, 81, 1.5), (512.0, 84, 2.0),
    (514.0, 86, 4.5), (518.5, 83, 1.5), (520.0, 84, 1.0), (521.0, 83, 1.0),
    (522.0, 81, 6.0),                                       # soar 3
    (528.0, 79, 1.0), (529.0, 81, 1.0),
    (530.0, 84, 4.5), (534.5, 86, 1.5), (536.0, 84, 1.0), (537.0, 81, 1.0),
    (538.0, 84, 6.0),                                       # soar 4
    (544.0, 83, 1.0), (545.0, 84, 1.0),
    (546.0, 86, 4.5), (550.5, 88, 1.5), (552.0, 86, 1.0), (553.0, 83, 1.0),
    (554.0, 81, 4.5), (558.5, 76, 1.5), (560.0, 77, 2.0),
    (562.0, 81, 4.5), (566.5, 84, 1.5), (568.0, 81, 1.0), (569.0, 77, 1.0),
    (570.0, 79, 4.5), (574.5, 76, 1.5), (576.0, 79, 2.0),
    (578.0, 83, 4.5), (582.5, 86, 1.5), (584.0, 83, 1.0), (585.0, 81, 1.0),
    (586.0, 81, 10.0),                                      # the final soar
    (596.0, 84, 0.75), (596.75, 83, 0.75), (597.5, 79, 0.5),
    (598.0, 76, 2.0), (600.0, 81, 1.9),
]

# The choir counter-line (ch8, oo vowel): a syncopated chain that leans
# half a beat ahead of each structural downbeat — every downbeat pairwise
# consonant with the saw, onsets almost entirely off the saw's grid.
CHOIR_D2: list[tuple[float, int, float]] = [
    (459.0, 64, 3.6), (463.0, 60, 1.5), (464.5, 57, 4.0), (468.5, 62, 1.0),
    (469.5, 65, 3.5), (473.0, 64, 4.0), (477.0, 60, 4.0), (481.0, 67, 4.0),
    (485.0, 62, 3.5), (489.0, 64, 4.0), (493.0, 67, 0.9), (494.0, 72, 3.5),
    (497.5, 74, 1.0), (498.5, 72, 3.0), (501.5, 65, 4.0), (505.5, 72, 4.0),
    (509.5, 64, 4.0), (513.5, 71, 4.0), (517.5, 67, 4.0), (521.5, 72, 4.0),
    (525.5, 64, 4.0), (529.5, 65, 4.0), (533.5, 69, 4.0), (537.5, 67, 4.0),
    (541.5, 64, 4.0), (545.5, 71, 4.0), (549.5, 67, 4.0), (553.5, 72, 4.0),
    (557.5, 64, 4.0), (561.5, 72, 4.0), (565.5, 65, 4.0), (569.5, 72, 4.0),
    (573.5, 64, 4.0), (577.5, 74, 4.0), (581.5, 67, 4.0), (585.5, 64, 4.0),
    (589.5, 72, 4.0), (593.5, 64, 4.0), (597.5, 69, 4.4),
]

# ---------------------------------------------------------------------------
# Ostinato patterns (ch0 marimba — the motion engine).
# ---------------------------------------------------------------------------

ARP_78 = [(0.0, 1), (0.5, 5), (1.0, 8), (1.5, 10), (2.0, 8), (2.5, 5),
          (3.0, 4)]                          # eighths across the 7/8 bar
ARP_16 = [8, 5, 1, 5, 8, 10, 8, 5]           # sixteenth cycle in the drops

# ---------------------------------------------------------------------------
# Fills (material.FILL_LIB via material.play_fill, jt=0), risers, posts.
# ---------------------------------------------------------------------------

EDGE1_FILLS: list[tuple[float, str]] = [
    (35.0, "A"), (49.0, "A"),
    (59.5, "B"), (70.0, "A"), (80.5, "D"),
    (87.5, "C"), (94.5, "A"), (101.5, "D"), (108.5, "F"),
    (115.5, "B"), (119.0, "A"), (122.5, "G"), (126.0, "D"), (129.5, "A"),
    (132.0, "E"), (135.0, "G"), (136.5, "F"), (138.5, "H"),
]
EDGE2_FILLS: list[tuple[float, str]] = [
    (275.0, "A"), (289.0, "D"), (303.0, "A"), (317.0, "B"), (331.0, "A"),
    (345.0, "G"), (359.0, "D"),
]
BUILD_FILLS: list[tuple[float, str]] = [
    (397.0, "A"), (405.0, "B"),
    (411.5, "C"), (417.0, "D"), (423.0, "A"),
    (427.0, "B"), (431.0, "G"), (435.0, "D"), (439.0, "F"),
    (443.0, "C"), (446.0, "H"),
    (450.0, "E"), (453.0, "G"), (454.5, "F"), (456.5, "H"),
]
DROP1_FILLS: list[tuple[float, str]] = [
    (172.0, "A"), (188.0, "D"), (204.0, "B"), (220.0, "A"), (236.0, "G"),
    (252.0, "F"),
]
DROP2_FILLS: list[tuple[float, str]] = [
    (466.0, "D"), (482.0, "A"), (498.0, "B"), (514.0, "G"), (530.0, "D"),
    (538.0, "F"), (546.0, "A"), (562.0, "H"), (578.0, "G"), (588.0, "G"),
    (594.0, "E"),
]

EDGE1_WINDOWS = ((28.0, 56.0), (56.0, 84.0), (84.0, 112.0), (112.0, 140.0))
BUILD_WINDOWS = ((394.0, 410.0), (410.0, 426.0), (426.0, 442.0),
                 (442.0, 458.0))
PREDROP1 = (132.0, 140.0)
PREDROP2 = (450.0, 458.0)

RISER_PITCH = 62
RISER_NOTES = ((132.0, 8.0, 80), (390.0, 4.0, 66), (450.0, 8.0, 92),
               (522.0, 8.0, 88))
RISER_WINDOWS = ((132.0, 140.0), (390.0, 394.0), (450.0, 458.0),
                 (522.0, 530.0))

# Antiphonal posts: L calls on every drop chord, R answers 4 beats later.
POST_CALL = ((0.0, 0, 0.22), (0.25, 7, 0.22), (0.5, 12, 0.6))     # rising
POST_ANSWER = ((0.0, 12, 0.22), (0.25, 7, 0.22), (0.5, 0, 0.6))   # falling

# The snap.
STAB_BEAT = 602.0
CHOKE_BEAT = 606.0

# ---------------------------------------------------------------------------
# PART.
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVS,
    tempo_map=[(0.0, BPM)],
    time_signatures=TIMESIGS,
    keysigs=[(0.0, 0, 1)],             # A minor
    channels=[
        (CH_ARP, "engine - marimba", 12, 96, 64, 40),
        (CH_PAD, "pad - warm", 89, 92, 64, 50),
        (CH_BASS, "bass - synth", 39, 104, 64, 20),
        (CH_POST_L, "post left - brass", 61, 96, PAN_POST_L, 40),
        (CH_POST_R, "post right - brass", 61, 96, PAN_POST_R, 40),
        (CH_SAW, "saw lead", 81, 100, 64, 30),
        (CH_HARP, "harp", 46, 96, 64, 45),
        (CH_STR, "aerial strings", 49, 90, 64, 60),
        (CH_CHOIR, "choir - counter", 53, 92, 64, 55),
        (CH_KIT, "kit", 0, 100, 64, 25),
        (CH_TOMS, "melodic toms", 117, 100, 64, 30),
        (CH_SYN, "synth drum", 118, 98, 64, 30),
        (CH_HIT, "orchestra hit", 55, 100, 64, 40),
        (CH_RISER, "riser - reverse cymbal", 119, 88, 64, 55),
        (CH_LEAD, "lead ship - overdrive", 29, 118, 64, 20),
        (CH_WING, "wing ship - overdrive", 29, 114, 64, 20),
    ],
    bank_selects=[(CH_TOMS, 1), (CH_SYN, 1), (CH_RISER, 1),
                  (CH_LEAD, 1), (CH_WING, 1)],
    program_changes=[(CH_KIT, 0.0, 1)],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {12, 29, 39, 46, 49, 53, 55, 61, 81, 89,
                               117, 118, 119}
CENTERED_CHANNELS: set[int] = {CH_ARP, CH_PAD, CH_BASS, CH_SAW, CH_HARP,
                               CH_STR, CH_CHOIR, CH_KIT, CH_TOMS, CH_SYN,
                               CH_HIT, CH_RISER, CH_LEAD, CH_WING}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_ARP: (55, 86),
    CH_PAD: (50, 78),
    CH_BASS: (36, 58),
    CH_POST_L: (56, 84),
    CH_POST_R: (56, 84),
    CH_SAW: (62, 89),
    CH_HARP: (52, 86),
    CH_STR: (60, 90),
    CH_CHOIR: (50, 76),
    CH_TOMS: (44, 64),
    CH_SYN: (46, 60),
    CH_HIT: (46, 58),
    CH_RISER: (60, 64),
    CH_LEAD: (53, 78),
    CH_WING: (40, 67),
}
GAP_WHITELIST: list[tuple[float, float]] = [(602.4, 606.0)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (247.0, 260.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))
