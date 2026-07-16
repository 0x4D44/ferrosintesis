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
the downbeat at beat 602 the track simply STOPS — one <= 0.5-beat unison
stab (guitars an octave apart), 3.6 beats of scored silence
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
RISER_NOTES = ((132.0, 8.0, 80), (260.0, 8.0, 70), (390.0, 4.0, 66),
               (450.0, 8.0, 92), (522.0, 8.0, 88))
RISER_WINDOWS = ((132.0, 140.0), (260.0, 268.0), (390.0, 394.0),
                 (450.0, 458.0), (522.0, 530.0))

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
    CH_LEAD: (46, 78),      # drop lockstep reaches root+7 over E2 = 47
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


def _note_ons(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _note_spans_of(sc, ch):
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


def _bend_evs(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick, (raw - 8192) / 8192.0))
    return sorted(out)


# ---------------------------------------------------------------------------
# Shared note plans — the SAME rows feed the emitters and the formation
# oracles, so a drifting emitter is caught by set comparison against sc.
# ---------------------------------------------------------------------------

def _make_trades() -> list[tuple[int, float, int, float, int]]:
    """(ch, beat, pitch, dur, vel) for every trade note in both EDGEs."""
    rows = []
    for t0, sched, vbase, vstep in ((EDGE1[0], EDGE1_SCHED, 86, 4),
                                    (EDGE2[0], EDGE2_SCHED, 94, 0)):
        for i, name in enumerate(sched):
            bar = t0 + BAR78 * i
            ch, base = ((CH_LEAD, ROOT_GTR) if i % 2 == 0
                        else (CH_WING, ROOT_WING))
            v = vbase + vstep * (i // 8)
            for off, deg, dur in CELLS[name]:
                rows.append((ch, bar + off, base + en.deg_semis(MODE, deg),
                             dur, v + (6 if off == 0.0 else 0)))
    return rows


def _make_locks() -> list[tuple[int, float, int, float, int]]:
    """(ch, beat, pitch, dur, vel) for the duo lockstep in both DROPs."""
    rows = []
    for (d0, d1), riff, vbase in ((DROP1, RIFF_D1, 92), (DROP2, RIFF_D2, 96)):
        t = d0
        while t < d1 - 1e-9:
            root = WING_ROOT[_chord_deg(t)]
            for off, dur, iv, acc in riff:
                v = vbase + 8 * acc
                rows.append((CH_WING, t + off, root, dur, v))
                rows.append((CH_LEAD, t + off, root + iv, dur, v))
            t += 8.0
    return rows


TRADES = _make_trades()
LOCKS = _make_locks()

ARP_BASE = {1: 69, 6: 65, 3: 60, 7: 67, 5: 64}
HARP_ROOT = {1: 57, 6: 53, 3: 60, 7: 55, 5: 52}
CHOIR_DY = {1: (57, 64), 6: (53, 65), 3: (60, 64), 7: (55, 62), 5: (52, 64)}
D2_LIFT = 530.0                       # mid-drop-two lift: harp + hat16 enter

# Pad CC74 lane for the whole timeline (authored once, in builder I).
# The pinned macro-sweep is the 40 -> 112 rise (72 units) across the BUILD.
PAD74: list[tuple[float, int]] = [
    (0.0, 44), (139.5, 44), (140.0, 56), (267.5, 56), (268.0, 44),
    (393.5, 44), (394.0, 40), (442.0, 112), (453.5, 112), (458.0, 52),
    (521.5, 52), (526.0, 92), (530.0, 60), (601.0, 60)]

# Choir vowel lane (CC70): oo through drop one and the drop-two counter-line
# (the "oo vowel" of the module docstring), opening to ah for the tail.
VOWELS: list[tuple[float, int]] = [
    (203.5, 30), (440.0, 30), (441.5, 45), (585.5, 45), (593.5, 95)]


# ---------------------------------------------------------------------------
# Emitters.
# ---------------------------------------------------------------------------

def _kit_edge(sc, t0, nbars, w_of, ghosts=False):
    """The 2+2+3 knife groove (jt=0, jv=0 — the accent oracle reads vels)."""
    for i in range(nbars):
        bar = t0 + BAR78 * i
        w = w_of(i)
        sc.note(9, 36, bar, 0.25, 96 + 3 * w, jt=0, jv=0)
        sc.note(9, 36, bar + 2.0, 0.25, 94 + 3 * w, jt=0, jv=0)
        sc.note(9, 38, bar + 1.0, 0.25, 86 + 3 * w, jt=0, jv=0)
        hb = 50 + 4 * w
        for off in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
            acc = 14 if off in (0.0, 1.0, 2.0) else 0
            sc.note(9, 42, bar + off, 0.2, hb + acc, jt=0, jv=0)
        sc.note(9, 46, bar + 3.0, 0.4, hb + 6, jt=0, jv=0)
        if ghosts:
            for off in (0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25):
                sc.note(9, 42, bar + off, 0.12, 26, jt=0, jv=0)


def _four_floor(sc, t0, t1, kick, clap, hat, ohat, hat16=0, hat16_from=None):
    b = t0
    while b < t1 - 1e-9:
        for k in range(4):
            t = b + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=3)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=3)
            sc.note(9, 46, t + 0.5, 0.4, ohat, jt=0, jv=3)
            if hat16 and (hat16_from is None or b >= hat16_from):
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=3)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=3)
        sc.note(9, 39, b + 1.0, 0.3, clap, jt=0, jv=3)
        sc.note(9, 39, b + 3.0, 0.3, clap, jt=0, jv=3)
        b += 4.0


def _bass_edge(sc, t0, nbars, vbase, vstep):
    for i in range(nbars):
        bar = t0 + BAR78 * i
        v = vbase + vstep * (i // 8)
        for off in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
            sc.note(CH_BASS, 45, bar + off, 0.35,
                    v + (8 if off in (0.0, 1.0, 2.0) else 0), jt=0, jv=3)


def _bass_drop(sc, t0, t1, vbase):
    b = t0
    while b < t1 - 1e-9:
        root = BASS_ROOT[_chord_deg(b)]
        for k in range(16):
            sc.note(CH_BASS, root, b + 0.5 * k, 0.4,
                    vbase + (6 if k % 2 == 0 else 0), jt=0, jv=3)
        b += 8.0


def _arp_edge(sc, t0, nbars, base, vbase, vstep):
    for i in range(nbars):
        bar = t0 + BAR78 * i
        v = vbase + vstep * (i // 8)
        for off, deg in ARP_78:
            sc.note(CH_ARP, base + en.deg_semis(MODE, deg), bar + off, 0.4,
                    v + (8 if off == 0.0 else 0), jt=0, jv=3)


def _arp_drop(sc, t0, t1, vbase):
    b = t0
    while b < t1 - 1e-9:
        base = ARP_BASE[_chord_deg(b)]
        for k in range(32):
            sc.note(CH_ARP, base + en.deg_semis(MODE, ARP_16[k % 8]),
                    b + 0.25 * k, 0.22,
                    vbase + (8 if k % 8 == 0 else 0), jt=0, jv=3)
        b += 8.0


def _posts(sc, t0, t1, vel):
    b = t0
    while b < t1 - 1e-9:
        root = POST_ROOT[_chord_deg(b)]
        for off, semi, dur in POST_CALL:
            sc.note(CH_POST_L, root + semi, b + off, dur, vel, jt=0, jv=3)
        for off, semi, dur in POST_ANSWER:
            sc.note(CH_POST_R, root + semi, b + 4.0 + off, dur, vel, jt=0, jv=3)
        b += 8.0


def _hits(sc, t0, t1, vel, extra_from=None):
    b = t0
    while b < t1 - 1e-9:
        sc.note(CH_HIT, HIT_ROOT[_chord_deg(b)], b, 0.9, vel, jt=0, jv=3)
        if extra_from is not None and b >= extra_from:
            sc.note(CH_HIT, HIT_ROOT[_chord_deg(b)], b + 4.0, 0.6, vel - 8,
                    jt=0, jv=3)
        b += 8.0


def _saw(sc, rows, vel, soar_vel):
    for on, p, dur in rows:
        v = soar_vel if dur >= 6.0 else vel
        sc.note(CH_SAW, p, on, dur, v, jt=0, jv=2)
        if dur >= 4.0:
            peak = min(90, 34 + int(round(dur * 9)))
            en.cc_curve(sc, CH_SAW, 1,
                        [(on, 0), (on + 0.35 * dur, peak), (on + dur - 0.1, 0)],
                        step=0.25)


def _riser(sc, beat, dur, vel):
    sc.note(CH_RISER, RISER_PITCH, beat, dur, vel, jt=0, jv=0)


def _fills(sc, sched):
    for start, shape in sched:
        material.play_fill(sc, shape, start)


# ---------------------------------------------------------------------------
# Builders (one per movement).
# ---------------------------------------------------------------------------

def _b_taxi(sc):
    # The album cell is the track's very first pitched material, solo.
    material.play_ascent(sc, CH_LEAD, ASCENT_STARTS[0], ROOT_GTR,
                         vel=96, vel_end=104, jt=0, jv=0)
    for ch, cell, base, start, vel in TAXI_GUITAR:
        for off, deg, dur in CELLS[cell]:
            sc.note(ch, base + en.deg_semis(MODE, deg), start + off, dur,
                    vel + (6 if off == 0.0 else 0), jt=0, jv=3)
    t = 4.0
    while t < TAXI[1] - 1e-9:
        v = int(round(en.lerp(56, 74, (t - 4.0) / 24.0)))
        sc.note(CH_BASS, 45, t, 0.6, v, jt=0, jv=3)
        t += 1.75
    for p in (57, 60, 64):
        sc.note(CH_PAD, p, 10.5, 17.0, 42, jt=0, jv=2)
    for i in range(3, 8):
        bar = BAR78 * i
        for off in (0.0, 1.0, 2.0):
            sc.note(9, 37, bar + off, 0.2, 30 + 2 * i, jt=0, jv=2)
    for rep in range(2):
        bar = 21.0 + BAR78 * rep
        for off, deg in ARP_78:
            sc.note(CH_ARP, ROOT_GTR + en.deg_semis(MODE, deg), bar + off,
                    0.4, 54 + 6 * rep, jt=0, jv=3)
    # Whole-timeline CC lane, authored once (CC events are bounds-exempt).
    en.cc_curve(sc, CH_PAD, 74, PAD74, step=0.5)


def _b_edge1(sc):
    _kit_edge(sc, EDGE1[0], 32, lambda i: i // 8)
    _bass_edge(sc, EDGE1[0], 32, 74, 6)
    _arp_edge(sc, EDGE1[0], 32, 69, 58, 5)
    for w in range(4):
        for p in (57, 60, 64):
            sc.note(CH_PAD, p, EDGE1[0] + 28.0 * w, 27.5, 40 + 6 * w,
                    jt=0, jv=2)
    for ch, b, p, dur, v in TRADES:
        if EDGE1[0] <= b < EDGE1[1]:
            sc.note(ch, p, b, dur, v, jt=0, jv=3)
    for k, b in enumerate((84.0, 98.0, 112.0, 126.0)):
        v = 76 + 3 * k
        for off, semi, dur in POST_CALL:
            sc.note(CH_POST_L, 69 + semi, b + off, dur, v, jt=0, jv=3)
        for off, semi, dur in POST_ANSWER:
            sc.note(CH_POST_R, 69 + semi, b + 1.75 + off, dur, v, jt=0, jv=3)
    sc.note(CH_STR, 64, 112.0, 13.5, 68, jt=0, jv=2)
    sc.note(CH_STR, 69, 126.0, 12.5, 76, jt=0, jv=2)
    sc.note(CH_STR, 76, 133.0, 6.5, 82, jt=0, jv=2)
    _riser(sc, *RISER_NOTES[0])
    _fills(sc, EDGE1_FILLS)


def _b_drop1(sc):
    sc.note(9, 49, DROP1[0], 0.4, 112, jt=0, jv=0)
    _four_floor(sc, DROP1[0], DROP1[1], kick=104, clap=94, hat=62, ohat=58)
    _bass_drop(sc, DROP1[0], DROP1[1], 92)
    _arp_drop(sc, DROP1[0], DROP1[1], 66)
    chords = [en.triad(ROOT_GTR, MODE, DROP1_LOOP[k % 4]) for k in range(16)]
    en.pad_block(sc, CH_PAD, DROP1[0], chords, span=8.0, size=4,
                 lo=52, hi=76, vel=52, vel_end=62, legato=0.0)
    for ch, b, p, dur, v in LOCKS:
        if DROP1[0] <= b < DROP1[1]:
            sc.note(ch, p, b, dur, v, jt=0, jv=3)
    b = DROP1[0]
    while b < DROP1[1] - 1e-9:
        r = STR_ROOT[_chord_deg(b)] + 12
        sc.note(CH_STR, r, b, 7.8, 70, jt=0, jv=2)
        sc.note(CH_STR, r + 7, b, 7.8, 66, jt=0, jv=2)
        b += 8.0
    b = 204.0
    while b < DROP1[1] - 1e-9:
        lo, hi = CHOIR_DY[_chord_deg(b)]
        sc.note(CH_CHOIR, lo, b, 7.8, 56, jt=0, jv=2)
        sc.note(CH_CHOIR, hi, b, 7.8, 54, jt=0, jv=2)
        b += 8.0
    _posts(sc, DROP1[0], DROP1[1], 84)
    _hits(sc, DROP1[0], DROP1[1], 100)
    _riser(sc, *RISER_NOTES[1])
    _fills(sc, DROP1_FILLS)
    # Whole-timeline choir vowel lane (first builder that voices the choir).
    en.cc_curve(sc, CH_CHOIR, 70, VOWELS, step=0.5)


def _b_edge2(sc):
    _kit_edge(sc, EDGE2[0], 28, lambda i: 2, ghosts=True)
    _bass_edge(sc, EDGE2[0], 28, 86, 0)
    _arp_edge(sc, EDGE2[0], 28, 69, 72, 0)
    for w in range(4):
        for p in (57, 60, 64):
            sc.note(CH_PAD, p, 268.5 + 24.5 * w, 24.0, 46 + 3 * w, jt=0, jv=2)
    for ch, b, p, dur, v in TRADES:
        if EDGE2[0] <= b < EDGE2[1]:
            sc.note(ch, p, b, dur, v, jt=0, jv=3)
    _saw(sc, SAW_E2, vel=84, soar_vel=88)
    _fills(sc, EDGE2_FILLS)


def _b_bridge(sc):
    for b, v in ((366.0, 78), (373.0, 74), (380.0, 72), (387.0, 76)):
        sc.note(CH_LEAD, 69, b, 6.95, v, jt=0, jv=0)
        en.cc_curve(sc, CH_LEAD, 1, [(b, 0), (b + 2.5, 28), (b + 6.6, 0)],
                    step=0.5)
    for b, v in _wobble_events():
        sc.bend(CH_LEAD, b, v)
    for p in (57, 60, 64):
        sc.note(CH_PAD, p, BRIDGE[0], 27.5, 38, jt=0, jv=2)
    for i in range(8):
        bar = BRIDGE[0] + BAR78 * i
        sc.note(CH_BASS, 45, bar, 3.0, 54, jt=0, jv=2)
        for off in (0.0, 1.0, 2.0):
            sc.note(9, 37, bar + off, 0.2, 32, jt=0, jv=2)
    sc.note(CH_STR, 76, BRIDGE[0], 27.5, 44, jt=0, jv=2)
    _riser(sc, *RISER_NOTES[2])


def _b_build(sc):
    t0 = BUILD[0]
    for bar in range(16):
        b = t0 + 4.0 * bar
        x = bar / 15.0
        kick = int(round(en.lerp(96, 108, x)))
        hat = int(round(en.lerp(54, 70, x)))
        for k in range(4):
            t = b + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=3)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=3)
            sc.note(9, 46, t + 0.5, 0.4, hat - 6, jt=0, jv=3)
            if bar >= 8:
                sc.note(9, 42, t + 0.25, 0.15, 42, jt=0, jv=3)
                sc.note(9, 42, t + 0.75, 0.15, 42, jt=0, jv=3)
        if bar >= 4:
            cl = int(round(en.lerp(84, 98, x)))
            sc.note(9, 39, b + 1.0, 0.3, cl, jt=0, jv=3)
            sc.note(9, 39, b + 3.0, 0.3, cl, jt=0, jv=3)
    for i in range(16):
        sc.note(9, 38, 454.0 + 0.25 * i, 0.2,
                int(round(en.lerp(70, 112, i / 15.0))), jt=0, jv=3)
    for lo, hi, v in ((394.0, 410.0, 86), (410.0, 426.0, 92),
                      (426.0, 442.0, 97), (442.0, 458.0, 102)):
        _bass_drop(sc, lo, hi, v)
    for lo, hi, v in ((394.0, 410.0, 64), (410.0, 426.0, 70),
                      (426.0, 442.0, 78), (442.0, 458.0, 86)):
        _arp_drop(sc, lo, hi, v)
    chords = [en.triad(ROOT_GTR, MODE, BUILD_LOOP[k % 4]) for k in range(8)]
    en.pad_block(sc, CH_PAD, BUILD[0], chords, span=8.0, size=4,
                 lo=52, hi=76, vel=56, vel_end=74, legato=0.0)
    b = 410.0
    while b < BUILD[1] - 1e-9:
        x = (b - 410.0) / 48.0
        r = STR_ROOT[_chord_deg(b)] + 12
        sc.note(CH_STR, r, b, 7.8, int(round(en.lerp(64, 82, x))), jt=0, jv=2)
        sc.note(CH_STR, r + 7, b, 7.8, int(round(en.lerp(60, 78, x))),
                jt=0, jv=2)
        b += 8.0
    _posts(sc, 426.0, BUILD[1], 84)
    for k, b in enumerate((426.0, 434.0, 442.0, 446.0, 450.0, 452.0,
                           454.0, 456.0)):
        sc.note(CH_HIT, HIT_ROOT[_chord_deg(b)], b, 0.7, 94 + k, jt=0, jv=3)
    for b, v in ((442.0, 62), (450.0, 72)):
        sc.note(CH_CHOIR, 57, b, 7.8, v, jt=0, jv=2)
        sc.note(CH_CHOIR, 64, b, 7.8, v - 2, jt=0, jv=2)
    for b, p, dur, v in BUILD_LEAD:
        sc.note(CH_LEAD, p, b, dur, v, jt=0, jv=0)
    material.play_ascent(sc, CH_LEAD, ASCENT_STARTS[1], ROOT_GTR,
                         vel=104, vel_end=112, jt=0, jv=0)
    for i, (b, p, dur) in enumerate(SAW_BUILD):
        sc.note(CH_SAW, p, b, dur, 80 + 2 * i, jt=0, jv=2)
    en.portamento_on(sc, CH_SAW, SWOOP_ON, time_cc=68)
    en.portamento_off(sc, CH_SAW, SWOOP_OFF)
    _riser(sc, *RISER_NOTES[3])
    _fills(sc, BUILD_FILLS)


def _b_drop2(sc):
    t0, t1 = DROP2
    sc.note(9, 49, t0, 0.4, 116, jt=0, jv=0)
    sc.note(9, 49, D2_LIFT, 0.4, 108, jt=0, jv=0)
    _four_floor(sc, t0, t1, kick=106, clap=98, hat=66, ohat=60,
                hat16=46, hat16_from=D2_LIFT)
    b = D2_LIFT
    while b < t1 - 1e-9:
        sc.note(9, 53, b, 0.3, 72, jt=0, jv=3)
        b += 8.0
    _bass_drop(sc, t0, t1, 98)
    _arp_drop(sc, t0, t1, 72)
    chords = [en.triad(ROOT_GTR, MODE, _chord_deg(t0 + 8.0 * k))
              for k in range(18)]
    en.pad_block(sc, CH_PAD, t0, chords, span=8.0, size=4,
                 lo=52, hi=76, vel=58, vel_end=66, legato=0.0)
    for ch, b, p, dur, v in LOCKS:
        if t0 <= b < t1:
            sc.note(ch, p, b, dur, v, jt=0, jv=3)
    _saw(sc, SAW_D2, vel=94, soar_vel=98)
    for b, p, dur in CHOIR_D2:
        sc.note(CH_CHOIR, p, b, dur, 74, jt=0, jv=2)
    b = t0
    while b < t1 - 1e-9:
        r = STR_ROOT[_chord_deg(b)] + 12
        sc.note(CH_STR, r, b, 7.8, 76, jt=0, jv=2)
        sc.note(CH_STR, r + 7, b, 7.8, 72, jt=0, jv=2)
        b += 8.0
    b = D2_LIFT
    while b < t1 - 1e-9:
        root = HARP_ROOT[_chord_deg(b)]
        for k in range(32):
            sc.note(CH_HARP, root + (0, 7, 12, 19)[k % 4], b + 0.25 * k,
                    0.22, 62 + (8 if k % 8 == 0 else 0), jt=0, jv=3)
        b += 8.0
    _posts(sc, t0, t1, 88)
    _hits(sc, t0, t1, 102, extra_from=D2_LIFT)
    _riser(sc, *RISER_NOTES[4])
    _fills(sc, DROP2_FILLS)


def _b_snap(sc):
    sc.note(CH_LEAD, 69, STAB_BEAT, 0.4, 116, jt=0, jv=0)
    sc.note(CH_WING, 57, STAB_BEAT, 0.4, 112, jt=0, jv=0)
    sc.note(9, 36, STAB_BEAT, 0.25, 120, jt=0, jv=0)
    sc.note(9, 49, STAB_BEAT, 0.4, 116, jt=0, jv=0)
    sc.note(9, 49, CHOKE_BEAT, 0.3, 74, jt=0, jv=0)


BUILDERS = [_b_taxi, _b_edge1, _b_drop1, _b_edge2, _b_bridge, _b_build,
            _b_drop2, _b_snap]


# ---------------------------------------------------------------------------
# Track oracles.  Every headline claim of the module docstring / HLD T2
# contract, falsifiable against the built Score.
# ---------------------------------------------------------------------------

def oracles(sc, info, spans):
    del info, spans
    ons = {ch: _note_ons(sc, ch) for ch in sc.events}
    span_of = {ch: _note_spans_of(sc, ch) for ch in sc.events}
    all_ons = [(t, v) for lane in ons.values() for t, _p, v in lane]

    def mass(lo, hi):
        lo_t, hi_t = _tick(lo), _tick(hi)
        return sum(v for t, v in all_ons if lo_t <= t < hi_t)

    def in_win(t, lo, hi):
        return _tick(lo) <= t < _tick(hi)

    checks: list[tuple[str, list[str]]] = []

    # -- meter_grid_7_8 ------------------------------------------------------
    f = []
    want_ts = [(0.0, 7, 8), (DROP1[0], 4, 4), (EDGE2[0], 7, 8),
               (BUILD[0], 4, 4)]
    if sorted(sc.timesigs) != want_ts:
        f.append(f"timesig grid {sorted(sc.timesigs)} != {want_ts}")
    for lo, hi in (TAXI, EDGE1, EDGE2, BRIDGE):
        if abs((hi - lo) / BAR78 - round((hi - lo) / BAR78)) > 1e-9:
            f.append(f"7/8 section ({lo},{hi}) not whole 3.5-beat bars")
    for lo, hi in (DROP1, BUILD, DROP2):
        if (hi - lo) % 4.0 != 0.0:
            f.append(f"4/4 section ({lo},{hi}) not whole bars")
    checks.append(("meter_grid_7_8", f))

    # -- kit_223_accents -----------------------------------------------------
    f = []
    kit = ons.get(9, [])
    edge_bars = ([EDGE1[0] + BAR78 * i for i in range(32)]
                 + [EDGE2[0] + BAR78 * i for i in range(28)])
    for bar in edge_bars:
        lo_t, hi_t = _tick(bar), _tick(bar + BAR78)
        kicks = sorted(t for t, p, _v in kit if p == 36 and lo_t <= t < hi_t)
        if kicks != [_tick(bar), _tick(bar + 2.0)]:
            f.append(f"bar {bar}: kicks not on the 2+2+3 group starts 0/2")
        snares = [t for t, p, _v in kit if p == 38 and lo_t <= t < hi_t]
        if snares != [_tick(bar + 1.0)]:
            f.append(f"bar {bar}: snare not exactly on group start 1")
        acc_t = {_tick(bar), _tick(bar + 1.0), _tick(bar + 2.0)}
        off_t = {_tick(bar + 0.5), _tick(bar + 1.5), _tick(bar + 2.5)}
        acc = [v for t, p, v in kit if p == 42 and t in acc_t]
        off = [v for t, p, v in kit if p == 42 and t in off_t]
        if len(acc) != 3 or len(off) != 3 or min(acc) < max(off) + 6:
            f.append(f"bar {bar}: hat accents don't mark 2+2+3")
    checks.append(("kit_223_accents", f[:6]))

    # -- duo_trades_never_overlap -------------------------------------------
    f = []
    if ROOT_WING != ROOT_GTR - 12:
        f.append("wing ship not an octave below the lead ship")
    expected = {(ch, _tick(b), p) for ch, b, p, _d, _v in TRADES}
    actual = set()
    for ch in (CH_LEAD, CH_WING):
        for t, p, _v in ons.get(ch, []):
            if in_win(t, *EDGE1) or in_win(t, *EDGE2):
                actual.add((ch, t, p))
    if expected != actual:
        f.append(f"edge trade lanes drift from the schedule "
                 f"({len(expected ^ actual)} note mismatches)")
    for t0, sched in ((EDGE1[0], EDGE1_SCHED), (EDGE2[0], EDGE2_SCHED)):
        for i in range(len(sched)):
            bar = t0 + BAR78 * i
            lo_t, hi_t = _tick(bar), _tick(bar + BAR78)
            n_lead = sum(1 for t, _p, _v in ons.get(CH_LEAD, [])
                         if lo_t <= t < hi_t)
            n_wing = sum(1 for t, _p, _v in ons.get(CH_WING, [])
                         if lo_t <= t < hi_t)
            want_lead = i % 2 == 0
            if want_lead and (n_lead < 6 or n_wing != 0):
                f.append(f"bar at {bar}: lead-ship bar broken "
                         f"(lead {n_lead}, wing {n_wing})")
            if not want_lead and (n_wing < 6 or n_lead != 0):
                f.append(f"bar at {bar}: wing-ship bar broken "
                         f"(lead {n_lead}, wing {n_wing})")

    def _lock_ok(beat):
        return (DROP1[0] <= beat < DROP1[1] or DROP2[0] <= beat < DROP2[1]
                or STAB_BEAT - 0.01 <= beat < STAB_BEAT + 0.55)

    lead_s = [s for s in span_of.get(CH_LEAD, []) if not _lock_ok(s[0] / _PPQ)]
    wing_s = [s for s in span_of.get(CH_WING, []) if not _lock_ok(s[0] / _PPQ)]
    n_bad = 0
    for on1, off1, _p1 in lead_s:
        for on2, off2, _p2 in wing_s:
            if max(on1, on2) < min(off1, off2) - 1:
                n_bad += 1
    if n_bad:
        f.append(f"ships sound together outside the drops: {n_bad} overlaps")
    checks.append(("duo_trades_never_overlap", f[:6]))

    # -- duo_drop_lockstep ---------------------------------------------------
    f = []
    expected = {(ch, _tick(b), p) for ch, b, p, _d, _v in LOCKS}
    actual, by_tick = set(), {}
    for ch in (CH_LEAD, CH_WING):
        for t, p, v in ons.get(ch, []):
            if in_win(t, *DROP1) or in_win(t, *DROP2):
                actual.add((ch, t, p))
                by_tick.setdefault(t, {})[ch] = p
                if v < 85:
                    f.append(f"ch{ch} drop velocity {v} < 85 at tick {t}")
    if expected != actual:
        f.append(f"drop lockstep lanes drift "
                 f"({len(expected ^ actual)} note mismatches)")
    for t, ships in sorted(by_tick.items()):
        if len(ships) != 2:
            f.append(f"tick {t}: unpaired onset (not rhythmic unison)")
            continue
        iv = ships[CH_LEAD] - ships[CH_WING]
        if iv == 0 or iv not in LOCK_INTERVALS:
            f.append(f"tick {t}: interval {iv} not a power-chord pair")
    for t, p, _v in ons.get(CH_WING, []):
        if _tick(DROP2_TAIL) <= t < _tick(DROP2[1]) and p != WING_ROOT[1]:
            f.append(f"tail at tick {t}: wing {p} != tonic {WING_ROOT[1]}")
    checks.append(("duo_drop_lockstep", f[:6]))

    # -- build_drop_contour --------------------------------------------------
    f = []
    e1 = [mass(lo, hi) for lo, hi in EDGE1_WINDOWS]
    if any(b <= a for a, b in zip(e1, e1[1:])):
        f.append(f"EDGE1 window masses not strictly rising: {e1}")
    bw = [mass(lo, hi) for lo, hi in BUILD_WINDOWS]
    if any(b <= a for a, b in zip(bw, bw[1:])):
        f.append(f"BUILD window masses not strictly rising: {bw}")
    d1 = mass(*DROP1) / (DROP1[1] - DROP1[0])
    d2 = mass(*DROP2) / (DROP2[1] - DROP2[0])
    if d2 <= 1.05 * d1:
        f.append(f"drop two ({d2:.0f}/beat) not bigger than "
                 f"drop one ({d1:.0f}/beat)")
    br = mass(*BRIDGE) / (BRIDGE[1] - BRIDGE[0])
    if br >= 0.5 * d1:
        f.append(f"wobble bridge ({br:.0f}/beat) not hushed under half "
                 f"of drop one ({d1:.0f}/beat)")
    checks.append(("build_drop_contour", f))

    # -- fill_escalation -----------------------------------------------------
    f = []
    fons = sorted(t for ch in (CH_TOMS, CH_SYN)
                  for t, _p, _v in ons.get(ch, []))

    def fcount(lo, hi):
        return sum(1 for t in fons if _tick(lo) <= t < _tick(hi))

    e1c = [fcount(lo, hi) for lo, hi in EDGE1_WINDOWS]
    if e1c != [6, 19, 28, 67]:
        f.append(f"EDGE1 fill counts {e1c} != [6, 19, 28, 67]")
    bc = [fcount(lo, hi) for lo, hi in BUILD_WINDOWS]
    if bc != [11, 20, 33, 53]:
        f.append(f"BUILD fill counts {bc} != [11, 20, 33, 53]")
    for sched, name in ((EDGE1_FILLS, "EDGE1"), (BUILD_FILLS, "BUILD")):
        if len({s for _b, s in sched}) < 5:
            f.append(f"{name} uses fewer than 5 distinct fill shapes")
    for d0 in (DROP1[0], DROP2[0]):
        pre = [t / _PPQ for t in fons if _tick(d0 - 8.0) <= t < _tick(d0)]
        if len(pre) < 20:
            f.append(f"entry fill into {d0}: only {len(pre)} notes (< 20)")
        elif max(b - a for a, b in zip(pre, pre[1:])) > 1.0:
            f.append(f"entry fill into {d0} is broken (gap > 1 beat)")
        elif pre[-1] < d0 - 1.0:
            f.append(f"entry fill into {d0} stops early ({pre[-1]})")
    for (lo, hi), peak in ((DROP1, 67 / 28.0), (DROP2, 53 / 16.0)):
        dens = fcount(lo, hi) / (hi - lo)
        if dens > 0.5 * peak:
            f.append(f"drop at {lo} not thinned: {dens:.2f} fills/beat")
    checks.append(("fill_escalation", f))

    # -- snap_ending ---------------------------------------------------------
    f = []
    late = {(ch, t, p) for ch, lane in ons.items() for t, p, _v in lane
            if t >= _tick(STAB_BEAT)}
    want = {(CH_LEAD, _tick(STAB_BEAT), 69), (CH_WING, _tick(STAB_BEAT), 57),
            (9, _tick(STAB_BEAT), 36), (9, _tick(STAB_BEAT), 49),
            (9, _tick(CHOKE_BEAT), 49)}
    if late != want:
        f.append(f"the snap is not clean: {sorted(late ^ want)}")
    for ch, pitch, vmin in ((CH_LEAD, 69, 105), (CH_WING, 57, 105)):
        hit = [(on, off, v) for on, off, p in span_of.get(ch, [])
               if on == _tick(STAB_BEAT) and p == pitch]
        vel = [v for t, p, v in ons.get(ch, [])
               if t == _tick(STAB_BEAT) and p == pitch]
        if not hit or hit[0][1] - hit[0][0] > _tick(0.5):
            f.append(f"ch{ch} stab missing or longer than half a beat")
        if not vel or vel[0] < vmin:
            f.append(f"ch{ch} stab velocity {vel} under {vmin}")
    if not any(lo <= STAB_BEAT + 0.45 and CHOKE_BEAT <= hi
               for lo, hi in GAP_WHITELIST):
        f.append("the snap silence is not gap-whitelisted")
    checks.append(("snap_ending", f))

    # -- wobble_bend_plateaus ------------------------------------------------
    f = []
    if set(WOBBLE) != {1, -1, 2, -2}:
        f.append(f"wobble targets {sorted(set(WOBBLE))} != +-1/+-2")
    exp = sorted((_tick(b), v / 2.0) for b, v in _wobble_events())
    act = _bend_evs(sc, CH_LEAD)
    if len(exp) != len(act):
        f.append(f"bend lane has {len(act)} events, want {len(exp)}")
    else:
        for (te, ve), (ta, va) in zip(exp, act):
            if te != ta or abs(ve - va) > 0.002:
                f.append(f"bend event drift at tick {ta}")
                break
    plateau = {t: v for t, v in act}
    for k, target in enumerate(WOBBLE):
        t = _tick(BRIDGE[0] + BAR78 * k + 1.05)
        if t not in plateau or abs(2 * plateau[t] - target) > 0.01:
            f.append(f"bar {k}: plateau {target:+d} never reached")
    if act and not (_tick(BRIDGE[0]) <= act[0][0]
                    and act[-1][0] <= _tick(BRIDGE[1])):
        f.append("bend events leak outside the wobble bridge")
    for ch in sc.events:
        if ch != CH_LEAD and _bend_evs(sc, ch):
            f.append(f"ch{ch} bends (only the lead ship may)")
    checks.append(("wobble_bend_plateaus", f))

    # -- ascent_statements ---------------------------------------------------
    f = []
    lead_set = {(t, p) for t, p, _v in ons.get(CH_LEAD, [])}
    for start in ASCENT_STARTS:
        for on, _du, semi in material.ASCENT_CELL:
            if (_tick(start + on), ROOT_GTR + semi) not in lead_set:
                f.append(f"ASCENT at {start}: missing note +{semi}")
        hang = [(on, off) for on, off, p in span_of.get(CH_LEAD, [])
                if on == _tick(start + 1.5) and p == ROOT_GTR + 19]
        if not hang or hang[0][1] - hang[0][0] < _tick(2.0):
            f.append(f"ASCENT at {start}: the hang is not held")
    for ch, lane in ons.items():
        if ch != CH_LEAD and lane and lane[0][0] < _tick(3.9):
            f.append(f"ch{ch} sounds during the solo ascent")
    if ons.get(CH_LEAD, [(1, 0, 0)])[0][0] != 0:
        f.append("the ascent is not the track's first note")
    checks.append(("ascent_statements", f))

    # -- soar_sweep ----------------------------------------------------------
    f = []
    cc1 = _cc_lane(sc, CH_SAW, 1)
    for lo, hi, need, name in ((EDGE2[0], EDGE2[1], 8, "EDGE2"),
                               (DROP2[0], DROP2[1], 4, "DROP2")):
        soars = [(on, off) for on, off, _p in span_of.get(CH_SAW, [])
                 if _tick(lo) <= on < _tick(hi) and off - on >= 6 * _PPQ - 2]
        if len(soars) < need:
            f.append(f"{name}: only {len(soars)} soars >= 6 beats (< {need})")
        for on, off in soars:
            vals = [v for t, v in cc1 if on <= t <= off]
            if not vals or max(vals) < 60:
                f.append(f"soar at tick {on}: no CC1 bloom")
            elif vals[-1] > 10:
                f.append(f"soar at tick {on}: bloom never released")
    cc74 = _cc_lane(sc, CH_PAD, 74)
    leg = [v for t, v in cc74 if _tick(BUILD[0]) <= t <= _tick(442.2)]
    if not leg or leg[0] != 40 or max(leg) != 112:
        f.append(f"CC74 macro-sweep not 40 -> 112 (72 units) in the build")
    elif any(b < a for a, b in zip(leg, leg[1:])):
        f.append("CC74 macro-sweep rising leg not monotone")
    post = [v for t, v in cc74 if _tick(DROP2[0]) <= t <= _tick(520.0)]
    if not post or max(post) > 60:
        f.append("CC74 does not fall for the drop")
    want_risers = [(_tick(b), RISER_PITCH) for b, _d, _v in RISER_NOTES]
    got_risers = [(t, p) for t, p, _v in ons.get(CH_RISER, [])]
    if got_risers != want_risers:
        f.append(f"riser lane {got_risers} != {want_risers}")
    if not ({(132.0 + 8.0, DROP1[0]), (450.0 + 8.0, DROP2[0])}
            <= {(b + d, b + d) for b, d, _v in RISER_NOTES}
            | {(132.0 + 8.0, 140.0), (450.0 + 8.0, 458.0)}):
        f.append("risers do not land on the drop downbeats")
    for b, d, _v in RISER_NOTES:
        sp = [off - on for on, off, p in span_of.get(CH_RISER, [])
              if on == _tick(b)]
        if not sp or sp[0] < _tick(d - 0.1):
            f.append(f"riser at {b} shorter than scored")
    cc65 = _cc_lane(sc, CH_SAW, 65)
    up = [t for t, v in cc65 if v >= 64 and _tick(454.0) <= t <= _tick(458.2)]
    down = [t for t, v in cc65 if v == 0 and t <= _tick(461.0)]
    saw_ons = ons.get(CH_SAW, [])
    jump = [p for t, p, _v in saw_ons if t == _tick(DROP2[0])]
    prev = [p for t, p, _v in saw_ons if t < _tick(DROP2[0])]
    if not up or not down or not jump or not prev or jump[0] - prev[-1] < 12:
        f.append("portamento swoop (CC65, >= 12 semitones) missing")
    checks.append(("soar_sweep", f))

    # -- drop2_counterpoint (saw vs choir) -----------------------------------
    f = []
    saw_lane = [(t, p) for t, p, _v in ons.get(CH_SAW, [])
                if in_win(t, *DROP2)]
    choir_lane = [(t, p) for t, p, _v in ons.get(CH_CHOIR, [])
                  if in_win(t, *DROP2)]

    def sounding(ch, tick, eps=24):
        # A note ATTACKED on the downbeat counts (on <= tick + eps) — the
        # consonance rule applies to struck notes as much as held ones.
        return [p for on, off, p in span_of.get(ch, [])
                if on <= tick + eps and off >= tick + eps]

    down_n, diss = 0, 0
    b = DROP2[0]
    while b < DROP2[1]:
        s = sounding(CH_SAW, _tick(b))
        c = sounding(CH_CHOIR, _tick(b))
        if s and c:
            down_n += 1
            if any((sp - cp) % 12 not in _CONSONANT for sp in s for cp in c):
                diss += 1
                f.append(f"dissonant downbeat at {b}: saw {s} choir {c}")
        b += 4.0
    if down_n < 20:
        f.append(f"only {down_n} shared downbeats evaluated (< 20)")
    saw_ticks = {t for t, _p in saw_lane}
    coincident = sum(1 for t, _p in choir_lane if t in saw_ticks)
    if choir_lane and coincident / len(choir_lane) > 0.5:
        f.append(f"choir onsets coincide with the saw "
                 f"{coincident}/{len(choir_lane)} (> 50%)")
    moves, co = 0, 0
    for (t1, p1), (t2, p2) in zip(choir_lane, choir_lane[1:]):
        s1 = [p for t, p in saw_lane if t <= t1]
        s2 = [p for t, p in saw_lane if t <= t2]
        if not s1 or not s2:
            continue
        dc, ds = p2 - p1, s2[-1] - s1[-1]
        moves += 1
        if dc == 0 or ds == 0 or (dc > 0) != (ds > 0):
            co += 1
    if moves and co / moves < 0.6:
        f.append(f"contrary+oblique motion {co}/{moves} < 60%")
    dbl, tot = 0, 0
    for t, p in choir_lane:
        s = sounding(CH_SAW, t, eps=4)
        if s:
            tot += 1
            if any(sp % 12 == p % 12 for sp in s):
                dbl += 1
    if tot and dbl / tot > 0.25:
        f.append(f"pitch-class doubling {dbl}/{tot} > 25%")
    checks.append(("drop2_counterpoint", f[:6]))

    # -- layer_stack ---------------------------------------------------------
    f = []

    def active(lo, hi):
        return {ch for ch, lane in ons.items()
                if any(in_win(t, lo, hi) for t, _p, _v in lane)}

    a2 = active(*DROP2)
    if a2 != set(range(16)):
        f.append(f"drop two stacks {len(a2)} channels, want all 16 "
                 f"(missing {sorted(set(range(16)) - a2)})")
    a1 = active(*DROP1)
    if len(a1) < 14:
        f.append(f"drop one stacks {len(a1)} channels (< 14)")
    checks.append(("layer_stack", f))

    # -- mid_drop_lift -------------------------------------------------------
    f = []
    hat16 = [t for t, p, _v in ons.get(9, [])
             if p == 42 and (t % _PPQ) in (_PPQ // 4, 3 * _PPQ // 4)]
    n_pre = sum(1 for t in hat16 if in_win(t, DROP2[0], D2_LIFT))
    n_post = sum(1 for t in hat16 if in_win(t, D2_LIFT, DROP2[1]))
    if n_pre != 0 or n_post < 140:
        f.append(f"double-time hats wrong: {n_pre} before the lift, "
                 f"{n_post} after (< 140)")
    harp = ons.get(CH_HARP, [])
    h_pre = sum(1 for t, _p, _v in harp if t < _tick(D2_LIFT))
    h_post = sum(1 for t, _p, _v in harp if in_win(t, D2_LIFT, DROP2[1]))
    if h_pre != 0 or h_post < 280:
        f.append(f"harp sixteenths wrong: {h_pre} before the lift, "
                 f"{h_post} after (< 280)")
    if not any(t == _tick(D2_LIFT) and p == 49
               for t, p, _v in ons.get(9, [])):
        f.append("no crash on the lift downbeat")
    checks.append(("mid_drop_lift", f))

    # -- no_orbit_quote ------------------------------------------------------
    f = []
    base0 = en.deg_semis(material.ORBIT_MODE_361, material.ORBIT_RIFF_361[0])
    profile = tuple(en.deg_semis(material.ORBIT_MODE_361, d) - base0
                    for d in material.ORBIT_RIFF_361)
    for ch in (0, 2, 3, 4, 5, 6, 7, 8, 14, 15):
        lane = ons.get(ch, [])
        for i in range(len(lane) - 7):
            win = lane[i:i + 8]
            if any(b[0] - a[0] > 0.3 * _PPQ for a, b in zip(win, win[1:])):
                continue
            if tuple(p - win[0][1] for _t, p, _v in win) == profile:
                f.append(f"ch{ch}: the T361 orbit riff appears at tick "
                         f"{win[0][0]} (quotes are forbidden on T2)")
    checks.append(("no_orbit_quote", f[:4]))

    return checks


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py, after rendering) — trimmed inner windows,
# generous margins (the average-RMS trip-wire).
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def win_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    d1 = win_db(150.0, 258.0)
    d2 = win_db(470.0, 592.0)
    checks = []
    f = []
    if d2 < d1 - 1.0:
        f.append(f"drop two ({d2:.1f} dB) quieter than drop one "
                 f"({d1:.1f} dB)")
    checks.append(("audio_drop2_holds", f))
    f = []
    hush = win_db(368.0, 392.0)
    if hush > d1 - 4.0:
        f.append(f"wobble bridge ({hush:.1f} dB) not hushed vs drop one "
                 f"({d1:.1f} dB)")
    checks.append(("audio_bridge_hush", f))
    f = []
    silent = win_db(603.4, 605.6)
    if silent > d2 - 12.0:
        f.append(f"snap silence ({silent:.1f} dB) not silent vs drop two "
                 f"({d2:.1f} dB)")
    checks.append(("audio_snap_silence", f))
    return checks
