"""t16_three_sixty_one — Track 16 "Three-Sixty-One", the bonus variant of T10.

A remix of "Three-Sixty" (t10_three_sixty.py) that keeps the whole 360-degree
AquaTheater architecture note-for-note and ADDS three layers: an overdriven
distorted-guitar SOLO (ch14) that builds in through the second climb and soars
on top of the finale stack; an independent choir COUNTERPOINT (ch15) weaving
under it late; and an escalating-density bed of varied melodic-tom / synth-drum
DRUM FILLS across both builds.  Everything the original oracles pinned is
preserved; the three additions carry their own falsifiable oracles below.

Disc 2, 'Lines of Flight' — the Fine Line trilogy finale (HLD section 3,
T10): the 360-degree AquaTheater panorama.  E minor, 128 bpm, ~5:25.

THE ORBIT.  A transient steel-drum arp (ch0) plays material.ORBIT_RIFF as
an unbroken sixteenth ostinato, phase-locked to the global grid, while its
CC10 pan lane sweeps FULL CIRCLES around the theatre: 64 -> 127 -> 0 -> 64
per eight bars (32 beats), piecewise-linear at a half-beat grid.  The lane
completes 19 whole rotations (9 before the bridge, 10 after), and the
oracle walks the lane's extrema: strictly alternating 127-peaks and
0-troughs, monotonic sweeps between them, start and end at centre.  Only
TRANSIENT sources leave the centre (orbit notes are <= 0.5 beats; the
antiphonal brass calls are <= 0.75 beats): every sustained bed holds CC10
64 for the whole piece — the mono-collapse discipline, mirrored in
audio_checks as a <= 2 dB mono-sum loss over the widest span.

THE SHAPE.  Two build-drop cycles with the second strictly bigger:
intro [0,64) -> build one [64,160) with strictly-rising 8-bar velocity
windows -> DROP ONE [160,288) (four-on-floor kick on every beat, orchestra
hits every 8 beats, saw-lead hook, brass antiphony) -> the AERIAL bridge
[288,320): the tempo map literally halves (128 -> 64 bpm), drums fall
silent, suspended high strings + harp arpeggi + the choir's first entry ->
build two [320,416) -> DROP TWO [416,544) with the full company (choir on
an oo->ah CC70 morph, sixteenth hats, doubled orchestra hits, orbit lifted
an octave): its mean per-bar velocity sum exceeds drop one's by > 10%,
mirrored in render RMS.  Reverse-cymbal risers (GM 119) and melodic-tom
(117) + synth-drum (118) fills articulate every lift.

THE FINALE [544,640) stacks the trilogy: material.DIVE_CASCADE (T8, harp,
twelve four-octave falls), material.WALKER_THEME (T9, saw lead, twelve
statements) and material.ORBIT_RIFF (the orbit, still circling) sound
SIMULTANEOUSLY over a tonic pedal.  Both recalled lanes are held
note-for-note tick-exact to material.py by oracle, and every finale
downbeat's sounding trio is pairwise consonant across the three lanes.

Written oracle-first (the repo method): every headline claim above is a
falsifiable oracle below, and the audio headline claims are mirrored in
audio_checks() for analyze.py once the WAV exists.  No randomness beyond
the Score's own SEED-derived jitter is used; a rebuild is byte-identical.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 16
TITLE = 'Three-Sixty-One'
FILE = '16 - Three-Sixty-One.mid'
SEED = 20260916

COMMENT = ("Fine Line III: the 360-degree finale.  A transient arp orbits "
           "the theatre (CC10 full circles, 19 rotations); two build-drop "
           "cycles, the second bigger; a half-time aerial bridge; the "
           "finale stacks the dive cascade, the walker theme and the "
           "orbit riff in counterpoint.  Beds stay centred.")

# ---------------------------------------------------------------------------
# Grid.
# ---------------------------------------------------------------------------

BPM_MAIN = 128.0
BPM_BRIDGE = 64.0            # the aerial: exactly half time

INTRO = (0.0, 64.0)
BUILD1 = (64.0, 160.0)
DROP1 = (160.0, 288.0)
BRIDGE = (288.0, 320.0)
BUILD2 = (320.0, 416.0)
DROP2 = (416.0, 544.0)
FINALE = (544.0, 640.0)
OUTRO = (640.0, 660.0)
END = OUTRO[1]

MOVS: list[tuple[str, float, float]] = [
    ("I. House Lights", *INTRO),
    ("II. First Climb", *BUILD1),
    ("III. Drop One", *DROP1),
    ("IV. Aerial (half time)", *BRIDGE),
    ("V. Second Climb", *BUILD2),
    ("VI. Drop Two - Full Company", *DROP2),
    ("VII. Three-Sixty (the stack)", *FINALE),
    ("VIII. Splashdown", *OUTRO),
]

MODE = material.ORBIT_MODE            # aeolian — E minor on root E

# ---------------------------------------------------------------------------
# Channels.
# ---------------------------------------------------------------------------

CH_ORBIT, CH_PAD, CH_BASS, CH_BRASS_L, CH_BRASS_R = 0, 1, 2, 3, 4
CH_LEAD, CH_HARP, CH_AERIAL, CH_CHOIR = 5, 6, 7, 8
CH_KIT, CH_TOMS, CH_SYNDRUM, CH_HIT, CH_RISER = 9, 10, 11, 12, 13
CH_GUITAR, CH_CHOIR2 = 14, 15        # -One: distorted solo, choir counterpoint

PAN_BRASS_L, PAN_BRASS_R = 18, 110    # the antiphonal calls (transient)

# ---------------------------------------------------------------------------
# The orbit.
# ---------------------------------------------------------------------------

ORBIT_PERIOD = 32.0                   # one full rotation per eight bars
ORBIT_SPANS = ((0.0, 288.0), (320.0, 640.0))   # paused for the aerial
ORBIT_STEP = material.ORBIT_STEP      # sixteenths
ORBIT_ROOT_LO = 52                    # E3 until the lift
ORBIT_ROOT_HI = 64                    # E4 from drop two on
ORBIT_LIFT = DROP2[0]
ORBIT_DUR = 0.22                      # transient: << the 0.5-beat cap
PAN_GRID = 0.5


def _orbit_pan_value(beat: float) -> int:
    """The circle: 64 -> 127 (8 beats) -> 0 (16 beats) -> 64 (8 beats)."""
    ph = beat % ORBIT_PERIOD
    if ph < 8.0:
        return int(round(64 + 63 * ph / 8.0))
    if ph < 24.0:
        return int(round(127 - 127 * (ph - 8.0) / 16.0))
    return int(round(64 * (ph - 24.0) / 8.0))


def _orbit_vel(beat: float, slot: int) -> int:
    """Section-shaped velocity with a beat-head accent (+8 on the beat)."""
    if beat < 16.0:
        base = en.lerp(52, 68, beat / 16.0)
    elif beat < BUILD1[0]:
        base = 68
    elif beat < DROP1[0]:
        base = en.lerp(72, 80, (beat - BUILD1[0]) / 96.0)
    elif beat < BRIDGE[0]:
        base = 86
    elif beat < DROP2[0]:
        base = en.lerp(76, 84, (beat - BUILD2[0]) / 96.0)
    elif beat < FINALE[0]:
        base = 92
    else:
        base = 96
    return int(round(base)) + (8 if slot % 4 == 0 else 0)


# ---------------------------------------------------------------------------
# Harmony — i / VI / III / VII in E aeolian, two bars per chord, looping
# through both builds and both drops; tonic pedal everywhere else.
# ---------------------------------------------------------------------------

CHORD_DEGS = (1, 6, 3, 7)             # Em, C, G, D
HARMONY_SECTIONS = (BUILD1, DROP1, BUILD2, DROP2)

BASS_ROOT = {1: 40, 6: 36, 3: 43, 7: 38}     # E2 C2 G2 D2 (floored at C2)
BRASS_ROOT = {1: 64, 6: 60, 3: 67, 7: 62}    # E4 C4 G4 D4
HIT_ROOT = {1: 52, 6: 48, 3: 55, 7: 50}      # E3 C3 G3 D3


def _chord_deg(beat: float) -> int:
    for a, b in HARMONY_SECTIONS:
        if a <= beat < b:
            return CHORD_DEGS[int((beat - a) // 8.0) % 4]
    return 1


# ---------------------------------------------------------------------------
# Fixed material of this track.
# ---------------------------------------------------------------------------

# The drop hook: one 8-bar phrase over the full chord loop (saw lead).
LEAD_ROOT = 64
HOOK: list[tuple[int, float, float]] = [
    (8, 0.0, 1.5), (10, 1.5, 0.5), (8, 2.0, 1.0), (7, 3.0, 1.0),
    (5, 4.0, 1.5), (7, 5.5, 0.5), (8, 6.0, 2.0),
    (6, 8.0, 1.5), (8, 9.5, 0.5), (10, 10.0, 2.0), (8, 12.0, 1.0),
    (6, 13.0, 1.0), (5, 14.0, 2.0),
    (5, 16.0, 1.5), (7, 17.5, 0.5), (8, 18.0, 1.0), (9, 19.0, 1.0),
    (10, 20.0, 2.0), (9, 22.0, 1.0), (8, 23.0, 1.0),
    (9, 24.0, 1.5), (8, 25.5, 0.5), (7, 26.0, 1.0), (5, 27.0, 1.0),
    (4, 28.0, 1.0), (2, 29.0, 1.0), (1, 30.0, 2.0),
]

# Finale stack geometry: statements every 8 beats keep every downbeat on
# walker degree 1 or 4 (E / A) and dive degree 8 (E) — consonant with the
# orbit's downbeat E by construction.
WALKER_ROOT = 76                      # E5: the wire strung above the orbit
WALKER_STARTS = tuple(FINALE[0] + 8.0 * k for k in range(12))
DIVE_ROOTS = (76, 64, 52, 40)         # the four-octave fall, E6 -> E2
DIVE_STARTS = tuple(FINALE[0] + 8.0 * k for k in range(12))

# Brass call-pair start beats (L at t, R answers at t+2), per section.
BRASS_PAIRS: dict[str, tuple[tuple[float, ...], int, int]] = {
    # name: (starts, vel_first, vel_last)
    "intro": ((48.0, 56.0), 60, 66),
    "build1": (tuple(68.0 + 8.0 * k for k in range(11)), 72, 88),
    "drop1": (tuple(164.0 + 8.0 * k for k in range(15)), 94, 94),
    "build2": (tuple(324.0 + 8.0 * k for k in range(11)), 76, 92),
    "drop2": (tuple(420.0 + 8.0 * k for k in range(15)), 98, 98),
}

# Reverse-cymbal risers (beat, dur, vel) and the windows the oracle pins.
RISER_PITCH = 62
RISER_NOTES = ((152.0, 8.0, 84), (316.0, 4.0, 72),
               (408.0, 8.0, 92), (536.0, 8.0, 96))
RISER_WINDOWS = ((150.0, 160.0), (314.0, 320.0),
                 (406.0, 416.0), (534.0, 544.0))

# Tom/synth-drum fill anchors: big 4-beat lifts into each drop + finale,
# small 2-beat turns inside the drops and the finale.
FILLS_BIG = (156.0, 412.0, 540.0)
FILLS_SMALL = (190.0, 222.0, 254.0, 446.0, 478.0, 510.0, 574.0, 606.0)
TOM_SEQ = (62, 60, 58, 55, 53, 50, 48, 46)

# Choir tables (root/fifth in the climbs, full triads in drop two).
CHOIR_RF = {1: (52, 59), 6: (48, 55), 3: (55, 62), 7: (50, 57)}
CHOIR_TRIAD = {1: (52, 55, 59), 6: (48, 52, 55), 3: (55, 59, 62),
               7: (50, 53, 57)}

# Aerial bridge voicings (suspended high strings) and harp arps.
AERIAL_CHORDS = (((76, 79, 83, 86), 288.0, 54), ((72, 76, 79, 83), 304.0, 57))
HARP_EM9 = (52, 59, 64, 67, 71, 74, 79, 83)
HARP_CM9 = (48, 55, 60, 64, 67, 71, 76, 79)

# ---------------------------------------------------------------------------
# -One additions — designed by Fable 5 (the original composer) as a consult;
# see wrk_docs/2026.07.11 - HLD - Three-Sixty-One additions.md.  Every note
# below is composed to the oracles at the bottom of this file: the guitar and
# choir land only pitch-classes consonant with the tonic pedal (and, on the
# finale's A-beats, only {E,A,C}); the fills escalate strictly per window.
# ---------------------------------------------------------------------------

# (A) The distorted-guitar solo (ch14, GM30).  (onset, MIDI pitch, dur, vel).
# jt=0 so onsets stay tick-exact for the downbeat-consonance oracle; the life
# is in the CC1 vibrato swells and the marked bends, not timing smear.

GUITAR_B2: list[tuple[float, int, float, int]] = [
    # Second climb: three fragments, strictly escalating (4 / 10 / 13 notes).
    (346.0, 71, 0.5, 66), (346.5, 74, 0.5, 68), (347.0, 76, 1.0, 70),
    (348.0, 69, 2.0, 72),
    (356.0, 76, 1.0, 74), (357.0, 74, 0.5, 72), (357.5, 71, 0.5, 70),
    (358.0, 67, 1.0, 72), (359.0, 69, 0.5, 74), (360.0, 69, 2.0, 76),
    (372.0, 71, 0.75, 76), (373.0, 74, 0.75, 78), (374.0, 76, 0.5, 78),
    (374.5, 79, 1.5, 80),
    (388.0, 76, 0.5, 80), (388.5, 79, 0.5, 82), (389.0, 81, 0.5, 82),
    (389.5, 83, 1.5, 84),
    (396.0, 79, 1.0, 82), (397.0, 76, 0.5, 82), (397.5, 74, 0.5, 80),
    (398.0, 76, 1.5, 84),
    (404.0, 74, 0.5, 86), (404.5, 76, 0.5, 86), (405.0, 79, 0.5, 88),
    (405.5, 81, 0.45, 88), (406.0, 81, 2.75, 90),   # bend to B5 over the 408 D-beat
]

GUITAR_D2: list[tuple[float, int, float, int]] = [
    # Drop two: four hook rotations, register rising 83 -> 91.
    (420.0, 83, 2.0, 96), (422.0, 81, 0.5, 92), (422.5, 79, 0.5, 90),
    (423.0, 76, 1.0, 90), (425.5, 79, 0.5, 92), (426.0, 81, 0.5, 92),
    (426.5, 79, 0.5, 90), (427.0, 81, 0.9, 94), (428.0, 76, 2.0, 96),
    (432.0, 86, 1.75, 98), (434.0, 83, 0.5, 94), (434.5, 81, 0.5, 92),
    (435.0, 79, 0.5, 92), (435.5, 81, 0.5, 92), (436.0, 83, 1.5, 96),
    (438.5, 81, 0.5, 92), (439.0, 78, 0.5, 92), (439.5, 81, 0.45, 94),
    (440.0, 78, 1.0, 96), (441.0, 81, 3.0, 98),
    (448.0, 88, 2.0, 100), (450.0, 86, 0.5, 96), (450.5, 83, 0.5, 96),
    (451.0, 86, 0.5, 98), (451.5, 88, 0.5, 98), (452.0, 91, 2.0, 102),
    (455.0, 88, 0.5, 98), (455.5, 86, 0.5, 96), (456.0, 88, 2.5, 100),
    (462.0, 84, 0.5, 96), (462.5, 86, 0.5, 98), (463.0, 88, 0.5, 98),
    (463.5, 86, 0.5, 96), (464.5, 81, 3.5, 102),   # THE SCREAM: bend to B5
    (468.5, 83, 0.5, 98), (469.0, 86, 0.5, 98), (469.5, 83, 0.5, 96),
    (470.0, 79, 1.5, 96), (473.0, 81, 0.5, 96), (473.5, 83, 0.5, 98),
    (474.0, 86, 0.5, 98), (474.5, 90, 1.5, 100),
    (480.0, 83, 4.5, 100), (485.0, 79, 0.5, 98), (485.5, 81, 0.5, 98),
    (486.0, 83, 0.5, 100), (486.5, 86, 0.5, 100), (487.0, 88, 3.0, 102),
    (492.0, 91, 3.0, 104),                         # "sob": dip to -1 between beats
    (496.0, 86, 1.0, 100), (497.0, 83, 0.5, 98), (497.5, 86, 0.5, 100),
    (498.0, 88, 1.5, 100), (500.0, 83, 3.5, 102), (505.0, 81, 0.5, 98),
    (505.5, 83, 0.5, 98), (506.0, 81, 0.5, 96), (506.5, 79, 0.5, 96),
    (507.0, 81, 1.0, 98), (508.0, 78, 2.0, 96),
    (512.0, 88, 2.0, 100), (514.0, 86, 0.5, 98), (514.5, 83, 0.5, 96),
    (515.0, 79, 1.0, 96), (517.0, 81, 0.5, 94), (517.5, 79, 0.5, 94),
    (518.0, 76, 1.5, 96), (521.0, 79, 0.5, 94), (521.5, 81, 0.5, 94),
    (522.0, 79, 0.5, 92), (522.5, 76, 1.5, 94), (526.0, 76, 0.5, 94),
    (526.5, 79, 0.5, 94), (527.0, 81, 0.5, 96), (527.5, 83, 0.5, 96),
    (528.0, 86, 2.0, 98), (532.0, 83, 2.0, 96), (536.0, 81, 2.0, 94),
    (538.0, 78, 1.5, 90), (540.0, 81, 1.5, 92),
]

GUITAR_FIN: list[tuple[float, int, float, int]] = [
    # The soar: everything >= 83 (B5), sparse-but-high, peak A6 (93).
    (552.0, 83, 4.0, 104), (556.0, 88, 4.0, 106), (560.0, 91, 3.0, 106),
    (564.0, 88, 2.0, 104), (566.0, 86, 1.0, 102), (567.0, 83, 1.0, 102),
    (576.0, 88, 6.0, 106),
    (584.0, 83, 1.0, 106), (585.0, 86, 1.0, 106), (586.0, 88, 2.0, 107),
    (588.0, 93, 2.0, 108), (590.0, 91, 1.0, 106), (591.0, 88, 1.0, 106),
    (592.0, 88, 4.0, 108),
    (600.0, 91, 2.0, 108), (602.0, 93, 6.0, 110),   # THE PEAK: scream-flick bends
    (612.0, 88, 3.0, 106), (615.0, 86, 1.0, 104), (616.0, 83, 3.5, 104),
    (624.0, 88, 8.0, 104),                          # the farewell tone; exits at 632
]

GUITAR_SOLO = GUITAR_B2 + GUITAR_D2 + GUITAR_FIN

# ch14 pitch-bend gestures, as linear ramp segments (t0, t1, semis0, semis1);
# each gesture ends at 0 well before its section boundary (416/544/640) so the
# generic check_bend_hygiene stays green.  CC1 vibrato rides on top separately.
GUITAR_BENDS: list[tuple[float, float, float, float]] = [
    (406.25, 406.75, 0.0, 2.0), (408.25, 408.75, 2.0, 0.0),   # B5 over the D-beat
    (432.5, 433.0, 0.0, 2.0), (433.25, 433.6, 2.0, 0.0),      # E6 flick
    (465.0, 465.75, 0.0, 2.0), (467.5, 467.9, 2.0, 0.0),      # the scream to B5
    (493.0, 493.5, 0.0, -1.0), (493.5, 494.0, -1.0, 0.0),     # the sob
    (602.5, 603.25, 0.0, 2.0), (603.25, 603.9, 2.0, 0.0),     # peak flick 1 -> B6
    (606.0, 606.5, 0.0, 2.0), (606.5, 607.0, 2.0, 0.0),       # peak flick 2
]

# (B) The choir counterpoint (ch15, GM53 Voice Oohs).  (onset, pitch, dur, vel).
# Enters at 512 rising while the guitar descends (contrary motion), then a true
# countermelody through the finale; range E4-D5, a full octave under the solo.
CHOIR2_D2: list[tuple[float, int, float, int]] = [
    (512.0, 64, 4.0, 58), (516.0, 67, 3.9, 60), (520.0, 67, 4.0, 62),
    (524.0, 69, 2.0, 62), (526.0, 71, 2.0, 64), (528.0, 71, 4.0, 66),
    (532.0, 74, 4.0, 68), (536.0, 69, 8.0, 66),   # tail crosses into the finale
]

CHOIR2_FIN: list[tuple[float, int, float, int]] = [
    (548.0, 69, 4.0, 64), (554.0, 71, 2.0, 64), (556.0, 69, 3.0, 66),
    (559.0, 67, 1.0, 64), (560.0, 64, 4.0, 66), (564.0, 72, 2.0, 68),
    (566.0, 71, 1.0, 66), (567.0, 69, 1.0, 66), (568.0, 67, 3.0, 68),
    (571.0, 71, 1.0, 66), (572.0, 69, 4.0, 68), (576.0, 72, 4.0, 70),
    (580.0, 69, 4.0, 70), (584.0, 67, 2.0, 70), (586.0, 66, 1.0, 68),
    (587.0, 64, 1.0, 68), (588.0, 64, 4.0, 70), (596.0, 69, 4.0, 70),
    (600.0, 71, 3.0, 72), (603.0, 72, 5.0, 74), (608.0, 71, 2.0, 72),
    (610.0, 69, 2.0, 70), (612.0, 64, 4.0, 70), (616.0, 67, 3.0, 70),
    (619.0, 69, 1.0, 68), (620.0, 72, 4.0, 72), (624.0, 71, 2.0, 70),
    (626.0, 69, 2.0, 68), (628.0, 64, 10.0, 66),   # lands the tonic, holds to 638
]

CHOIR2_SOLO = CHOIR2_D2 + CHOIR2_FIN

# (C) Escalating drum fills.  A six-shape library; each shape is (offset,
# pitch, dur, vel) for tom (ch10, GM117) and syn (ch11, GM118).  toms 44-64,
# syn 46-60.  jt=0 keeps the shape signatures exact for the variety oracle.
FILL_LIB: dict[str, dict[str, list[tuple[float, int, float, int]]]] = {
    "A": {  # "comma" — a 1-beat punctuation mark (3 notes)
        "tom": [(0.00, 60, 0.20, 76), (0.50, 55, 0.20, 82)],
        "syn": [(0.75, 52, 0.20, 88)]},
    "B": {  # "descend" — the house DNA (the former _fill_small, 8 notes)
        "tom": [(0.00, 62, 0.20, 84), (0.50, 58, 0.20, 87),
                (0.75, 55, 0.20, 90), (1.00, 53, 0.20, 93),
                (1.50, 50, 0.20, 96), (1.75, 46, 0.20, 99)],
        "syn": [(1.25, 52, 0.20, 92), (1.75, 55, 0.20, 98)]},
    "C": {  # "lift" — an ASCENDING inversion of the DNA (9 notes)
        "tom": [(0.00, 46, 0.20, 72), (0.25, 50, 0.20, 76),
                (0.50, 53, 0.20, 80), (0.75, 55, 0.20, 84),
                (1.00, 58, 0.20, 88), (1.25, 60, 0.20, 92),
                (1.50, 62, 0.20, 96)],
        "syn": [(1.50, 50, 0.20, 90), (1.75, 57, 0.20, 98)]},
    "D": {  # "gallop" — syncopated high-low pairs (8 notes)
        "tom": [(0.00, 55, 0.18, 84), (0.25, 55, 0.18, 72),
                (0.75, 50, 0.18, 84), (1.00, 50, 0.18, 72),
                (1.50, 58, 0.18, 88), (1.75, 58, 0.18, 76)],
        "syn": [(0.50, 52, 0.18, 86), (1.25, 55, 0.18, 90)]},
    "E": {  # "roll-drop" — a one-pitch pressure roll then the floor drops (11)
        "tom": [(0.25 * i, 53, 0.18, 70 + 4 * i) for i in range(8)]
               + [(2.00, 50, 0.22, 100), (2.50, 46, 0.22, 104)],
        "syn": [(2.75, 58, 0.20, 102)]},
    "F": {  # "sputter" — double-stroke 32nd pairs (8 notes)
        "tom": [(0.000, 58, 0.12, 86), (0.125, 58, 0.12, 70),
                (0.500, 55, 0.12, 86), (0.625, 55, 0.12, 70),
                (1.000, 50, 0.12, 88), (1.125, 50, 0.12, 72)],
        "syn": [(1.50, 46, 0.20, 90), (1.75, 53, 0.20, 96)]},
}

# Fill start beats per build, escalating (counts 22<39<66, 28<47<71).  The big
# fills at 156/412/540 and the drop/finale smalls stay in FILLS_BIG/FILLS_SMALL.
FILL_SCHEDULE: list[tuple[float, str]] = [
    # BUILD1 — W0 [64,96): 22 notes; W1 [96,128): 39; W2 [128,160): 66 (+BIG@156)
    (71.0, "A"), (78.0, "B"), (87.0, "A"), (94.0, "D"),
    (99.0, "A"), (102.0, "B"), (110.0, "D"), (115.0, "A"), (118.0, "C"),
    (126.0, "F"),
    (131.0, "A"), (134.0, "D"), (139.0, "A"), (142.0, "C"), (146.0, "F"),
    (150.0, "B"), (153.0, "E"),
    # BUILD2 — W0 [320,352): 28; W1 [352,384): 47; W2 [384,416): 71 (+BIG@412)
    (326.0, "B"), (335.0, "A"), (342.0, "D"), (350.0, "C"),
    (355.0, "A"), (358.0, "D"), (366.0, "B"), (371.0, "A"), (374.0, "C"),
    (378.0, "F"), (382.0, "D"),
    (387.0, "A"), (390.0, "F"), (394.0, "D"), (398.0, "C"), (402.0, "B"),
    (405.0, "E"), (410.0, "F"),
]

# ---------------------------------------------------------------------------
# PART.
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVS,
    tempo_map=[(0.0, BPM_MAIN), (BRIDGE[0], BPM_BRIDGE),
               (BUILD2[0], BPM_MAIN)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1)],            # E minor
    channels=[
        (CH_ORBIT, "orbit - steel drums", 114, 96, 64, 45),
        (CH_PAD, "bed - warm pad", 89, 92, 64, 50),
        (CH_BASS, "bass - synth", 39, 104, 64, 20),
        (CH_BRASS_L, "brass left", 61, 98, PAN_BRASS_L, 40),
        (CH_BRASS_R, "brass right", 61, 98, PAN_BRASS_R, 40),
        (CH_LEAD, "lead - saw", 81, 100, 64, 30),
        (CH_HARP, "harp / cascade", 46, 98, 64, 45),
        (CH_AERIAL, "aerial strings", 49, 90, 64, 60),
        (CH_CHOIR, "choir", 52, 92, 64, 55),
        (CH_KIT, "kit v2", 0, 100, 64, 25),
        (CH_TOMS, "melodic toms", 117, 100, 64, 30),
        (CH_SYNDRUM, "synth drum", 118, 98, 64, 30),
        (CH_HIT, "orchestra hit", 55, 100, 64, 40),
        (CH_RISER, "riser - reverse cymbal", 119, 88, 64, 55),
        (CH_GUITAR, "solo - distortion guitar", 30, 104, 64, 26),
        (CH_CHOIR2, "choir - counterpoint", 53, 90, 64, 52),
    ],
    bank_selects=[(0, 1), (10, 1), (11, 1), (13, 1)],   # steel/toms/synth-drum/riser: set B
    program_changes=[(CH_KIT, 0.0, 1)],     # non-zero kit program (V3 default)
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {30, 39, 46, 49, 52, 53, 55, 61, 81, 89,
                               114, 117, 118, 119}
CENTERED_CHANNELS: set[int] = {CH_PAD, CH_BASS, CH_LEAD, CH_HARP,
                               CH_AERIAL, CH_CHOIR, CH_TOMS, CH_SYNDRUM,
                               CH_HIT, CH_RISER, CH_GUITAR, CH_CHOIR2}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_ORBIT: (52, 83),
    CH_PAD: (52, 77),
    CH_BASS: (36, 55),        # floored at C2
    CH_BRASS_L: (56, 84),
    CH_BRASS_R: (56, 84),
    CH_LEAD: (62, 86),
    CH_HARP: (40, 92),
    CH_AERIAL: (72, 88),
    CH_CHOIR: (46, 66),
    CH_TOMS: (44, 64),
    CH_SYNDRUM: (46, 60),
    CH_HIT: (46, 58),
    CH_RISER: (60, 64),
    CH_GUITAR: (64, 94),      # distorted lead: written G4..A6 (bends ride on top)
    CH_CHOIR2: (62, 76),      # counterpoint: E4..D5, an octave under the solo
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (318.0, 331.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}    # ic-symmetric: P4/P5 allowed
_PPQ = en.PPQ


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))


# ---------------------------------------------------------------------------
# Oracle helpers.
# ---------------------------------------------------------------------------

def _note_ons(sc: en.Score, ch: int) -> list[tuple[int, int, int]]:
    """(tick, pitch, vel) of every note-on, sorted."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _note_spans(sc: en.Score, ch: int) -> list[tuple[int, int, int]]:
    """(on_tick, off_tick, pitch) with FIFO pairing."""
    pending: dict[int, list[int]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append(tick)
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                out.append((queue.pop(0), tick, data[1]))
    return sorted(out)


def _cc_lane(sc: en.Score, ch: int, num: int) -> list[tuple[int, int]]:
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            out.append((tick, data[2]))
    return sorted(out)


def _phrases(ons: list[tuple[int, int, int]],
             gap_ticks: int = _PPQ) -> list[int]:
    """Start ticks of note groups separated by more than `gap_ticks`."""
    starts: list[int] = []
    last = None
    for tick, _p, _v in ons:
        if last is None or tick - last > gap_ticks:
            starts.append(tick)
        last = tick
    return starts


def _bar_sums(sc: en.Score) -> dict[int, float]:
    """Sum of note-on velocities per 4-beat bar, all channels."""
    bar_ticks = 4 * _PPQ
    out: dict[int, float] = {}
    for ch in sc.events:
        for tick, p, v in _note_ons(sc, ch):
            out[tick // bar_ticks] = out.get(tick // bar_ticks, 0.0) + v
    return out


def _mean_barsum(sums: dict[int, float], lo: float, hi: float) -> float:
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


# -- helpers for the -One consonance oracles --------------------------------

def _bend_events(sc: en.Score, ch: int) -> list[tuple[int, float]]:
    """(tick, frac in [-1,1]) pitch-bend events on a channel, sorted."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick, (raw - 8192) / 8192.0))
    return sorted(out)


def _frac_at(bends: list[tuple[int, float]], tick: int) -> float:
    frac = 0.0
    for t, f in bends:
        if t > tick:
            break
        frac = f
    return frac


def _eff(p: int, frac: float) -> int:
    """Effective pitch: written pitch plus the +/-2 semitone bend state."""
    return p + int(round(2.0 * frac))


def _sounding(sc: en.Score, ch: int, tick: int, eps: int = 24) -> list[int]:
    """Pitches on `ch` that strictly SPAN `tick` (a note ending exactly on a
    downbeat does not 'sound' there)."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on <= tick - eps and off >= tick + eps]


def _last_pitch_at(onsets: list[tuple[int, int]], tick: int) -> int | None:
    pitch = None
    for t, p in onsets:
        if t > tick:
            break
        pitch = p
    return pitch


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the builders; the music is composed to pass.
# ---------------------------------------------------------------------------

def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    # --- orbit_pan_cycles: the CC10 lane sweeps whole circles ---------------
    # Walk the lane: dedupe, then require strictly alternating extrema —
    # every peak exactly 127, every trough exactly 0, >= 6 full rotations,
    # start and end at centre 64, and no step larger than 8 (smooth sweep).
    fails: list[str] = []
    lane = _cc_lane(sc, CH_ORBIT, 10)
    vals: list[int] = []
    for _t, v in lane:
        if not vals or vals[-1] != v:
            vals.append(v)
    if len(vals) < 8:
        fails.append("orbit pan lane is missing")
    else:
        if vals[0] != 64:
            fails.append(f"lane starts at {vals[0]}, want centre 64")
        if vals[-1] != 64:
            fails.append(f"lane ends at {vals[-1]}, want centre 64")
        big = [(a, b) for a, b in zip(vals, vals[1:]) if abs(b - a) > 8]
        if big:
            fails.append(f"pan jumps {big[:3]} exceed 8 per step "
                         f"(not a smooth sweep)")
        ext: list[tuple[str, int]] = []
        for i in range(1, len(vals) - 1):
            if vals[i - 1] < vals[i] > vals[i + 1]:
                ext.append(("max", vals[i]))
            elif vals[i - 1] > vals[i] < vals[i + 1]:
                ext.append(("min", vals[i]))
        for (a, _va), (b, _vb) in zip(ext, ext[1:]):
            if a == b:
                fails.append("consecutive same-kind extrema: a sweep "
                             "reverses mid-flight (not monotonic)")
                break
        maxima = [v for k, v in ext if k == "max"]
        minima = [v for k, v in ext if k == "min"]
        if not ext or ext[0][0] != "max":
            fails.append("lane must first sweep UP to a 127 peak")
        if any(v != 127 for v in maxima):
            fails.append(f"peaks {sorted(set(maxima))} must all be 127")
        if any(v != 0 for v in minima):
            fails.append(f"troughs {sorted(set(minima))} must all be 0")
        if len(maxima) != len(minima):
            fails.append(f"{len(maxima)} peaks vs {len(minima)} troughs: "
                         f"an incomplete rotation")
        if min(len(maxima), len(minima)) < 6:
            fails.append(f"only {min(len(maxima), len(minima))} full "
                         f"rotations, want >= 6")
    results.append(("orbit_pan_cycles", fails))

    # --- orbit_transient_riff: the orbit is material.ORBIT_RIFF, phase-
    #     locked sixteenths, transient (<= 0.5 beats), exactly covering the
    #     active spans; root lifts an octave at drop two -------------------
    fails = []
    expected: list[tuple[int, int]] = []
    for a, b in ORBIT_SPANS:
        for k in range(int(round(a / 0.25)), int(round(b / 0.25))):
            t = k * 0.25
            root = ORBIT_ROOT_HI if t >= ORBIT_LIFT else ORBIT_ROOT_LO
            deg = material.ORBIT_RIFF[k % len(material.ORBIT_RIFF)]
            expected.append((k * (_PPQ // 4),
                             en.pitch(root, material.ORBIT_MODE, deg)))
    got = [(t, p) for t, p, _v in _note_ons(sc, CH_ORBIT)]
    if got != sorted(expected):
        bad = next((i for i, (g, w) in enumerate(zip(got, sorted(expected)))
                    if g != w), min(len(got), len(expected)))
        fails.append(f"orbit notes differ from the phase-locked riff "
                     f"(first at index {bad}; {len(got)} vs "
                     f"{len(expected)} notes)")
    long = [(on, off - on) for on, off, _p in _note_spans(sc, CH_ORBIT)
            if off - on > _PPQ // 2]
    if long:
        fails.append(f"{len(long)} orbit notes exceed 0.5 beats — the "
                     f"orbiting source must stay transient")
    results.append(("orbit_transient_riff", fails))

    # --- width_only_transients: nothing but the orbit and the brass calls
    #     ever leaves pan 64; the brass sits at fixed L/R posts ------------
    fails = []
    for ch in sorted(sc.events):
        lane = _cc_lane(sc, ch, 10)
        off = sorted({v for _t, v in lane if v != 64})
        if ch == CH_ORBIT:
            continue                       # the orbit is oracle #1's job
        elif ch == CH_BRASS_L:
            if off != [PAN_BRASS_L]:
                fails.append(f"brass L pans {off} != [{PAN_BRASS_L}]")
        elif ch == CH_BRASS_R:
            if off != [PAN_BRASS_R]:
                fails.append(f"brass R pans {off} != [{PAN_BRASS_R}]")
        elif off:
            fails.append(f"ch{ch} leaves the centre (pans {off[:4]}) — "
                         f"beds must hold 64")
    want_centred = {CH_PAD, CH_BASS, CH_LEAD, CH_HARP, CH_AERIAL, CH_CHOIR,
                    CH_TOMS, CH_SYNDRUM, CH_HIT, CH_RISER,
                    CH_GUITAR, CH_CHOIR2}
    if CENTERED_CHANNELS != want_centred:
        fails.append("CENTERED_CHANNELS no longer covers every bed")
    results.append(("width_only_transients", fails))

    # --- antiphonal_brass: short calls, strict L/R alternation ------------
    fails = []
    ons_l, ons_r = _note_ons(sc, CH_BRASS_L), _note_ons(sc, CH_BRASS_R)
    for name, ch, ons in (("L", CH_BRASS_L, ons_l), ("R", CH_BRASS_R, ons_r)):
        long = [on for on, off, _p in _note_spans(sc, ch)
                if off - on > int(1.5 * _PPQ)]
        if long:
            fails.append(f"brass {name}: {len(long)} notes exceed 1.5 "
                         f"beats — calls must stay short")
    ph_l, ph_r = _phrases(ons_l), _phrases(ons_r)
    if len(ph_l) < 8 or len(ph_r) < 8:
        fails.append(f"{len(ph_l)} L / {len(ph_r)} R phrases, want >= 8 "
                     f"per side")
    merged = sorted([(t, "L") for t in ph_l] + [(t, "R") for t in ph_r])
    for (t0, s0), (t1, s1) in zip(merged, merged[1:]):
        if s0 == s1:
            fails.append(f"two consecutive {s0} calls at ticks {t0}/{t1}: "
                         f"antiphony broken")
            break
    if merged and merged[0][1] != "L":
        fails.append("the first call must come from the left")
    results.append(("antiphonal_brass", fails))

    # --- build_drop_contour: rising windows x2; drop2 > drop1; hush -------
    fails = []
    sums = _bar_sums(sc)
    b1 = [_mean_barsum(sums, 64, 96), _mean_barsum(sums, 96, 128),
          _mean_barsum(sums, 128, 160)]
    b2 = [_mean_barsum(sums, 320, 352), _mean_barsum(sums, 352, 384),
          _mean_barsum(sums, 384, 416)]
    for name, wins in (("build one", b1), ("build two", b2)):
        for i, (x, y) in enumerate(zip(wins, wins[1:])):
            if y <= x:
                fails.append(f"{name} window {i}->{i + 1} does not rise "
                             f"({x:.0f} -> {y:.0f})")
    d1 = _mean_barsum(sums, *DROP1)
    d2 = _mean_barsum(sums, *DROP2)
    br = _mean_barsum(sums, *BRIDGE)
    fin = _mean_barsum(sums, *FINALE)
    if d1 <= 1.15 * (sum(b1) / 3):
        fails.append(f"drop one {d1:.0f} <= 1.15x build one mean "
                     f"{sum(b1) / 3:.0f}")
    if d2 <= 1.10 * d1:
        fails.append(f"drop two {d2:.0f} <= 1.10x drop one {d1:.0f} — "
                     f"the second drop must be bigger")
    if br >= 0.5 * d1:
        fails.append(f"bridge {br:.0f} >= half of drop one {d1:.0f}: "
                     f"the aerial must hush")
    if fin < d1:
        fails.append(f"finale {fin:.0f} < drop one {d1:.0f}: the sprint "
                     f"must not sag")
    results.append(("build_drop_contour", fails))

    # --- halftime_bridge: the tempo map literally halves ------------------
    fails = []
    tm = sorted(PART.TEMPO_MAP)
    if len(tm) != 3:
        fails.append(f"tempo map has {len(tm)} entries, want 3")
    else:
        if tm[0] != (0.0, BPM_MAIN) or tm[2] != (BUILD2[0], BPM_MAIN):
            fails.append("main tempo grid mangled")
        if tm[1][0] != BRIDGE[0] or tm[1][1] * 2 != tm[0][1]:
            fails.append(f"bridge tempo {tm[1]} is not half of "
                         f"{tm[0][1]} bpm at beat {BRIDGE[0]}")
    kicks = [t for t, p, _v in _note_ons(sc, CH_KIT)
             if p == 36 and _tick(BRIDGE[0]) <= t < _tick(BRIDGE[1])]
    if kicks:
        fails.append(f"{len(kicks)} kicks inside the aerial — the floor "
                     f"must fall away")
    results.append(("halftime_bridge", fails))

    # --- tom_syndrum_fills: 117 + 118 articulate every lift ---------------
    fails = []
    toms, syn = _note_ons(sc, CH_TOMS), _note_ons(sc, CH_SYNDRUM)
    for t0 in FILLS_BIG:
        lo, hi = _tick(t0), _tick(t0 + 4.0)
        n_t = sum(1 for t, _p, _v in toms if lo <= t < hi)
        n_s = sum(1 for t, _p, _v in syn if lo <= t < hi)
        if n_t < 6:
            fails.append(f"big fill at {t0:.0f}: only {n_t} tom notes "
                         f"(want >= 6)")
        if n_s < 3:
            fails.append(f"big fill at {t0:.0f}: only {n_s} synth-drum "
                         f"notes (want >= 3)")
    if len(toms) < 40:
        fails.append(f"only {len(toms)} melodic-tom notes, want >= 40")
    if len(syn) < 20:
        fails.append(f"only {len(syn)} synth-drum notes, want >= 20")
    results.append(("tom_syndrum_fills", fails))

    # --- four_floor_and_hits: kick every beat in the drops + finale;
    #     orchestra hits exactly on their grids, denser in drop two --------
    fails = []
    kick_ticks = {t for t, p, _v in _note_ons(sc, CH_KIT) if p == 36}
    missing = []
    for lo, hi in (DROP1, DROP2, FINALE):
        for beat in range(int(lo), int(hi)):
            if beat * _PPQ not in kick_ticks:
                missing.append(beat)
    if missing:
        fails.append(f"four-on-floor broken: no kick at beats "
                     f"{missing[:6]}{'...' if len(missing) > 6 else ''}")
    want_hits: list[tuple[int, int]] = []
    for lo, hi, step in ((DROP1[0], DROP1[1], 8.0),
                         (DROP2[0], DROP2[1], 4.0),
                         (FINALE[0], FINALE[1], 4.0)):
        t = lo
        while t < hi - 1e-9:
            want_hits.append((_tick(t), HIT_ROOT[_chord_deg(t)]))
            t += step
    want_hits.append((_tick(OUTRO[0]), HIT_ROOT[1]))
    got_hits = [(t, p) for t, p, _v in _note_ons(sc, CH_HIT)]
    if got_hits != sorted(want_hits):
        fails.append(f"orchestra hits differ from the grid "
                     f"({len(got_hits)} vs {len(want_hits)})")
    results.append(("four_floor_and_hits", fails))

    # --- finale_stack_fidelity: DIVE_CASCADE + WALKER_THEME + ORBIT_RIFF
    #     simultaneously, note-for-note from material.py -------------------
    fails = []
    lo, hi = _tick(FINALE[0]), _tick(FINALE[1])
    want_walker = sorted(
        (_tick(s + i * material.WALKER_STEP),
         en.pitch(WALKER_ROOT, material.WALKER_MODE, deg))
        for s in WALKER_STARTS
        for i, deg in enumerate(material.WALKER_THEME))
    got_walker = [(t, p) for t, p, _v in _note_ons(sc, CH_LEAD)
                  if lo <= t < hi]
    if got_walker != want_walker:
        fails.append(f"walker lane differs from material.WALKER_THEME "
                     f"({len(got_walker)} vs {len(want_walker)} notes)")
    want_dive = sorted(
        (_tick(s + oi * 2.0 + i * material.DIVE_STEP),
         en.pitch(root, material.DIVE_MODE, deg))
        for s in DIVE_STARTS
        for oi, root in enumerate(DIVE_ROOTS)
        for i, deg in enumerate(material.DIVE_CASCADE))
    got_dive = [(t, p) for t, p, _v in _note_ons(sc, CH_HARP)
                if lo <= t < hi]
    if got_dive != want_dive:
        fails.append(f"dive lane differs from material.DIVE_CASCADE "
                     f"({len(got_dive)} vs {len(want_dive)} notes)")
    n_orbit = sum(1 for t, _p, _v in _note_ons(sc, CH_ORBIT)
                  if lo <= t < hi)
    want_orbit = int(round((FINALE[1] - FINALE[0]) / 0.25))
    if n_orbit != want_orbit:
        fails.append(f"orbit plays {n_orbit} of {want_orbit} finale "
                     f"sixteenths — the riff must run the whole stack")
    if len(WALKER_STARTS) < 10 or len(DIVE_STARTS) < 10:
        fails.append("fewer than 10 statements per recalled lane")
    span = ((max(p for _t, p in want_dive) - min(p for _t, p in want_dive))
            if want_dive else 0)
    if span != 48:
        fails.append(f"dive span {span} semitones != 48 (four octaves)")
    results.append(("finale_stack_fidelity", fails))

    # --- finale_downbeat_consonance: the three lanes agree ----------------
    fails = []
    by_lane = {ch: {} for ch in (CH_ORBIT, CH_LEAD, CH_HARP)}
    for ch in by_lane:
        for t, p, _v in _note_ons(sc, ch):
            by_lane[ch].setdefault(t, []).append(p)
    beat = FINALE[0]
    while beat < FINALE[1] - 1e-9:
        tick = _tick(beat)
        lanes = [by_lane[ch].get(tick, []) for ch in
                 (CH_ORBIT, CH_LEAD, CH_HARP)]
        if any(not la for la in lanes):
            fails.append(f"downbeat {beat:.0f}: a stack lane is silent")
        for i in range(3):
            for j in range(i + 1, 3):
                for a in lanes[i]:
                    for b in lanes[j]:
                        if (a - b) % 12 not in _CONSONANT:
                            fails.append(
                                f"downbeat {beat:.0f}: dissonance "
                                f"{(a - b) % 12} between lanes "
                                f"{i}/{j} ({a} vs {b})")
        beat += 4.0
    results.append(("finale_downbeat_consonance", fails[:8]))

    # --- choir_second_cycle: the full company arrives after the aerial ----
    fails = []
    choir = _note_ons(sc, CH_CHOIR)
    early = [t for t, _p, _v in choir if t < _tick(BRIDGE[0])]
    if early:
        fails.append(f"{len(early)} choir notes before the aerial — the "
                     f"company enters with cycle two")
    n_cycle2 = sum(1 for t, _p, _v in choir
                   if _tick(BUILD2[0]) <= t < _tick(DROP2[1]))
    if n_cycle2 < 20:
        fails.append(f"only {n_cycle2} choir notes in cycle two, want "
                     f">= 20")
    if not any(_tick(DROP2[0]) <= t < _tick(DROP2[1])
               for t, _p, _v in choir):
        fails.append("no choir in drop two — 'full company' unmet")
    vowels = _cc_lane(sc, CH_CHOIR, 70)
    if not vowels:
        fails.append("choir authors no CC70 vowel lane")
    else:
        if vowels[0][1] > 45:
            fails.append(f"vowel lane opens at {vowels[0][1]} (> oo 45)")
        peak = max((v for t, v in vowels if t < _tick(441.0)), default=0)
        if peak < 80:
            fails.append(f"vowel morph never reaches ah (>= 80) by drop "
                         f"two (peak {peak})")
    results.append(("choir_second_cycle", fails))

    # --- risers: every lift is announced by the reverse cymbal ------------
    fails = []
    riser_spans = _note_spans(sc, CH_RISER)
    for lo_b, hi_b in RISER_WINDOWS:
        if not any(_tick(lo_b) <= on < _tick(hi_b)
                   for on, _off, _p in riser_spans):
            fails.append(f"no riser inside [{lo_b:.0f}, {hi_b:.0f})")
    for on, off, _p in riser_spans:
        if not any(_tick(lo_b) <= on < _tick(hi_b)
                   for lo_b, hi_b in RISER_WINDOWS):
            fails.append(f"stray riser at tick {on}")
        if off - on < 2 * _PPQ:
            fails.append(f"riser at tick {on} shorter than 2 beats — "
                         f"it must swell")
    results.append(("risers", fails))

    # -- the -One additions --------------------------------------------------
    g_ons = _note_ons(sc, CH_GUITAR)
    gbends = _bend_events(sc, CH_GUITAR)
    stack: dict[int, list[int]] = {}
    for ch in (CH_ORBIT, CH_LEAD, CH_HARP):
        for t, p, _v in _note_ons(sc, ch):
            stack.setdefault(t, []).append(p)

    # --- guitar_solo_arc: silent-then-rising, soaring, breathing, consonant -
    fails = []
    if any(t < _tick(BUILD2[0]) for t, _p, _v in g_ons):
        fails.append("guitar sounds before the second climb (beat 320)")

    def _gwin(lo: float, hi: float) -> int:
        return sum(1 for t, _p, _v in g_ons if _tick(lo) <= t < _tick(hi))

    w = [_gwin(320, 352), _gwin(352, 384), _gwin(384, 416)]
    if w[0] < 3 or not (w[0] < w[1] < w[2]):
        fails.append(f"build-two guitar windows not rising: {w}")

    def _gmean(lo: float, hi: float, idx: int) -> float:
        xs = [e[idx] for e in g_ons if _tick(lo) <= e[0] < _tick(hi)]
        return sum(xs) / len(xs) if xs else 0.0

    mb, md, mf = _gmean(320, 416, 1), _gmean(416, 544, 1), _gmean(544, 640, 1)
    if not (mb < md < mf):
        fails.append(f"guitar register not rising: {mb:.0f}/{md:.0f}/{mf:.0f}")
    if _gwin(320, 416) / 96.0 >= _gwin(416, 544) / 128.0:
        fails.append("guitar density not rising into drop two")
    if _gmean(544, 640, 2) <= _gmean(416, 544, 2):
        fails.append("finale guitar not louder than drop two")
    fin_p = [p for t, p, _v in g_ons if _tick(544) <= t < _tick(640)]
    if fin_p and min(fin_p) < 83:
        fails.append(f"guitar dips to {min(fin_p)} in the finale (must soar >= 83)")
    for lo, hi in ((416, 544), (544, 640)):
        seg = [e for e in g_ons if _tick(lo) <= e[0] < _tick(hi)]
        if len(_phrases(seg, gap_ticks=2 * _PPQ)) < 5:
            fails.append(f"guitar has < 5 phrases in [{lo},{hi})")
        secspans = sorted((on, off) for on, off, _p in _note_spans(sc, CH_GUITAR)
                          if _tick(lo) <= on < _tick(hi))
        sounding = sum(off - on for on, off in secspans) / _PPQ
        if sounding > 0.75 * (hi - lo):
            fails.append(f"guitar over-plays [{lo},{hi}) (duty "
                         f"{sounding / (hi - lo):.2f} > 0.75)")
        horizon, max_gap = _tick(lo), 0
        for on, off in secspans:
            max_gap = max(max_gap, on - horizon)
            horizon = max(horizon, off)
        if max_gap < 4 * _PPQ:
            fails.append(f"guitar never rests >= 4 beats in [{lo},{hi})")
    cf = 0
    beat = BUILD2[0]
    while beat < FINALE[1] - 1e-9 and cf <= 6:
        tick = _tick(beat)
        root = HIT_ROOT[_chord_deg(beat)]
        frac = _frac_at(gbends, tick)
        effs = [_eff(p, frac) for p in _sounding(sc, CH_GUITAR, tick)]
        for e in effs:
            if (e - root) % 12 not in _CONSONANT:
                fails.append(f"guitar {e} vs root {root} dissonant at beat "
                             f"{beat:.0f}")
                cf += 1
        if beat >= FINALE[0]:
            others = stack.get(tick, []) + _sounding(sc, CH_CHOIR2, tick)
            for e in effs:
                for o in others:
                    if (e - o) % 12 not in _CONSONANT:
                        fails.append(f"guitar {e} clashes with stack {o} at "
                                     f"beat {beat:.0f}")
                        cf += 1
        beat += 4.0
    results.append(("guitar_solo_arc", fails[:8]))

    # --- choir_counterpoint: late, under the solo, independent, consonant ---
    fails = []
    c_ons = _note_ons(sc, CH_CHOIR2)
    if any(t < _tick(512) for t, _p, _v in c_ons):
        fails.append("counterpoint sounds before beat 512")
    n_d2 = sum(1 for t, _p, _v in c_ons if _tick(512) <= t < _tick(544))
    n_fin = sum(1 for t, _p, _v in c_ons if _tick(544) <= t < _tick(640))
    if n_d2 < 6:
        fails.append(f"only {n_d2} counterpoint notes in drop two (want >= 6)")
    if n_fin < 20:
        fails.append(f"only {n_fin} counterpoint notes in the finale (>= 20)")
    if any(t >= _tick(640) for t, _p, _v in c_ons):
        fails.append("counterpoint bleeds into the outro")
    c_fin = sorted((t, p) for t, p, _v in c_ons
                   if _tick(544) <= t < _tick(640))
    if c_fin and fin_p and max(p for _t, p in c_fin) >= min(fin_p):
        fails.append(f"counterpoint {max(p for _t, p in c_fin)} not under the "
                     f"solo floor {min(fin_p)}")
    cf = 0
    beat = 512.0
    while beat < FINALE[1] - 1e-9 and cf <= 6:
        tick = _tick(beat)
        root = HIT_ROOT[_chord_deg(beat)]
        for p in _sounding(sc, CH_CHOIR2, tick):
            if (p - root) % 12 not in _CONSONANT:
                fails.append(f"counterpoint {p} vs root {root} at beat "
                             f"{beat:.0f}")
                cf += 1
            if beat >= FINALE[0]:
                gfrac = _frac_at(gbends, tick)
                others = stack.get(tick, []) + [
                    _eff(gp, gfrac) for gp in _sounding(sc, CH_GUITAR, tick)]
                for o in others:
                    if (p - o) % 12 not in _CONSONANT:
                        fails.append(f"counterpoint {p} clashes with {o} at "
                                     f"beat {beat:.0f}")
                        cf += 1
        beat += 4.0
    g_on_ticks = [t for t, _p, _v in g_ons]
    indep = sum(1 for t, _p in c_fin
                if all(abs(t - gt) > 60 for gt in g_on_ticks))
    if indep < 12:
        fails.append(f"only {indep} independent counterpoint onsets (>= 12)")
    g_sorted = sorted((t, p) for t, p, _v in g_ons)
    contrary = classified = obl_con = 0
    prev = None
    for t, p in c_fin:
        if prev is not None:
            dc = p - prev[1]
            gn, gp = _last_pitch_at(g_sorted, t), _last_pitch_at(g_sorted, prev[0])
            dg = (gn - gp) if (gn is not None and gp is not None) else 0
            classified += 1
            if dc * dg < 0:
                contrary += 1
                obl_con += 1
            elif dc == 0 or dg == 0:
                obl_con += 1
        prev = (t, p)
    if contrary < 6:
        fails.append(f"only {contrary} contrary motions vs the solo (>= 6)")
    if classified and obl_con / classified < 0.6:
        fails.append(f"counterpoint too parallel ({obl_con}/{classified})")
    shared = sum(1 for t, p in c_fin
                 if any((p - gp) % 12 == 0
                        for gp in _sounding(sc, CH_GUITAR, t)))
    if c_fin and shared / len(c_fin) > 0.20:
        fails.append(f"counterpoint doubles the solo pc too often "
                     f"({shared}/{len(c_fin)})")
    vk = _cc_lane(sc, CH_CHOIR2, 70)
    if not vk:
        fails.append("counterpoint authors no CC70 vowel lane")
    elif any(v > 45 for _t, v in vk):
        fails.append(f"counterpoint vowel not held 'oo' (max "
                     f"{max(v for _t, v in vk)})")
    results.append(("choir_counterpoint", fails[:8]))

    # --- drum_fill_escalation: strict rise per window, varied, drops thin ---
    fails = []
    fill_ons = sorted((t, p) for ch in (CH_TOMS, CH_SYNDRUM)
                      for t, p, _v in _note_ons(sc, ch))

    def _fc(lo: float, hi: float) -> int:
        return sum(1 for t, _p in fill_ons if _tick(lo) <= t < _tick(hi))

    b1 = [_fc(64, 96), _fc(96, 128), _fc(128, 160)]
    b2 = [_fc(320, 352), _fc(352, 384), _fc(384, 416)]
    for name, ws in (("build one", b1), ("build two", b2)):
        if not (ws[0] < ws[1] < ws[2]):
            fails.append(f"{name} fills not strictly rising: {ws}")
    for i in range(3):
        if b2[i] < b1[i]:
            fails.append(f"build-two window {i} ({b2[i]}) below build one "
                         f"({b1[i]})")
    if _fc(152, 160) < 20:
        fails.append(f"fill into drop one only {_fc(152, 160)} notes (>= 20)")
    if _fc(408, 416) < 20:
        fails.append(f"fill into drop two only {_fc(408, 416)} notes (>= 20)")

    def _sigs(lo: float, hi: float) -> set:
        pts = [(t, p) for t, p in fill_ons if _tick(lo) <= t < _tick(hi)]
        out, cluster, start, last = set(), [], None, None
        for t, p in pts:
            if last is not None and t - last > _PPQ:
                out.add(tuple(sorted((tt - start, pp) for tt, pp in cluster)))
                cluster, start = [], None
            start = t if start is None else start
            cluster.append((t, p))
            last = t
        if cluster:
            out.add(tuple(sorted((tt - start, pp) for tt, pp in cluster)))
        return out

    for name, (lo, hi) in (("build one", (64, 160)), ("build two", (320, 416))):
        n = len(_sigs(lo, hi))
        if n < 5:
            fails.append(f"{name} uses only {n} distinct fill shapes (>= 5)")
    peak1, peak2 = max(b1), max(b2)
    for lo, hi, peak, name in ((160, 288, peak1, "drop one"),
                               (416, 544, peak2, "drop two")):
        for w0 in range(lo, hi, 32):
            c = _fc(w0, w0 + 32)
            if c > 24 or c >= 0.5 * peak:
                fails.append(f"{name} window @{w0} has {c} fills (cap 24, "
                             f"< half of {peak})")
    results.append(("drum_fill_escalation", fails[:8]))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/10 - Three-Sixty.wav exists.
# Trimmed inner windows keep reverb tails honest.
# ---------------------------------------------------------------------------

AUDIO_BUILD1 = (66.0, 94.0)
AUDIO_DROP1 = (168.0, 280.0)
AUDIO_BRIDGE = (292.0, 318.0)
AUDIO_DROP2 = (424.0, 536.0)
AUDIO_FINALE = (552.0, 632.0)


def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    def span_db(a: float, b: float) -> float:
        i0, i1 = ctx.bar_window(a, b)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    b1 = span_db(*AUDIO_BUILD1)
    d1 = span_db(*AUDIO_DROP1)
    d2 = span_db(*AUDIO_DROP2)
    br = span_db(*AUDIO_BRIDGE)
    fin = span_db(*AUDIO_FINALE)

    # 1. Two build-drop cycles, the second bigger — on the RENDER.
    fails: list[str] = []
    if d1 < b1 + 3.0:
        fails.append(f"drop one {d1:.1f} dB < build one {b1:.1f} + 3")
    if d2 < d1 + 0.2:
        fails.append(f"drop two {d2:.1f} dB not above drop one "
                     f"{d1:.1f} + 0.2 — the second drop must be bigger")
    if fin < d1 - 1.0:
        fails.append(f"finale {fin:.1f} dB sags below drop one "
                     f"{d1:.1f} - 1.0")
    checks.append(("audio_build_drop_x2", fails))

    # 2. The aerial hush.
    fails = []
    if br > d1 - 6.0:
        fails.append(f"bridge {br:.1f} dB is not >= 6 dB below drop one "
                     f"{d1:.1f}")
    checks.append(("audio_bridge_hush", fails))

    # 3. The orbit must be audibly wide across drop one...
    fails = []
    i0, i1 = ctx.bar_window(*AUDIO_DROP1)
    i1 = min(i1, len(ctx.l))
    mid_acc = side_acc = 0.0
    n = 0
    for i in range(i0, i1, 4):
        m = (ctx.l[i] + ctx.r[i]) / 2.0
        s = (ctx.l[i] - ctx.r[i]) / 2.0
        mid_acc += m * m
        side_acc += s * s
        n += 1
    if n == 0:
        fails.append("no samples in drop one")
    else:
        width_db = (ctx.db((side_acc / n) ** 0.5)
                    - ctx.db((mid_acc / n) ** 0.5))
        if width_db < -16.0:
            fails.append(f"side energy {width_db:.1f} dB below mid "
                         f"(want >= -16): the orbit is not circling")
    checks.append(("audio_orbit_width", fails))

    # 4. ...yet mono-safe even there (transient sources only).
    fails = []
    if n:
        mono_acc = 0.0
        m2 = 0
        for i in range(i0, i1, 2):
            mono_acc += ((ctx.l[i] + ctx.r[i]) / 2.0) ** 2
            m2 += 1
        stereo = ctx.rms(ctx.l, ctx.r, i0, i1)
        loss = ctx.db(stereo) - ctx.db((mono_acc / m2) ** 0.5)
        if loss > 2.0:
            fails.append(f"mono sum loses {loss:.2f} dB over drop one "
                         f"(cap 2.0)")
    checks.append(("audio_drop_mono_safe", fails))

    return checks


# ---------------------------------------------------------------------------
# Texture helpers — deterministic emitters the builders share.
# ---------------------------------------------------------------------------

def _orbit_notes(sc: en.Score, t0: float, t1: float) -> None:
    """The riff, phase-locked to the global sixteenth grid, clipped to
    the orbit's active spans and to this movement's beat range."""
    for a, b in ORBIT_SPANS:
        lo, hi = max(t0, a), min(t1, b)
        if lo >= hi:
            continue
        for k in range(int(round(lo / 0.25)), int(round(hi / 0.25))):
            t = k * 0.25
            root = ORBIT_ROOT_HI if t >= ORBIT_LIFT else ORBIT_ROOT_LO
            deg = material.ORBIT_RIFF[k % len(material.ORBIT_RIFF)]
            sc.note(CH_ORBIT, en.pitch(root, material.ORBIT_MODE, deg),
                    t, ORBIT_DUR, _orbit_vel(t, k), jt=0, jv=3)


def _orbit_pan_lane(sc: en.Score) -> None:
    """The full-piece CC10 orbit (CC events are not bounds-checked)."""
    for a, b in ORBIT_SPANS:
        n = int(round((b - a) / PAN_GRID))
        for i in range(n):
            t = a + i * PAN_GRID
            sc.cc(CH_ORBIT, 10, _orbit_pan_value(t), t)
        sc.cc(CH_ORBIT, 10, 64, b)     # each span lands back at centre


def _pad_chords(sc: en.Score, t0: float, degs: list[int], span: float,
                vel: int, vel_end: int | None = None) -> None:
    en.pad_block(sc, CH_PAD, t0, [en.triad(52, MODE, d) for d in degs],
                 span=span, size=4, lo=52, hi=76, vel=vel, vel_end=vel_end)


def _bass_half_notes(sc: en.Score, t0: float, t1: float, v0: int,
                     v1: int) -> None:
    n = int(round((t1 - t0) / 2.0))
    for i in range(n):
        t = t0 + 2.0 * i
        sc.note(CH_BASS, BASS_ROOT[_chord_deg(t)], t, 1.8,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=3, jv=2)


def _bass_8ths(sc: en.Score, t0: float, t1: float, v0: int, v1: int,
               pops: bool) -> None:
    n = int(round((t1 - t0) / 0.5))
    for i in range(n):
        t = t0 + 0.5 * i
        root = BASS_ROOT[_chord_deg(t)]
        p = root + (12 if pops and i % 8 in (3, 6) else 0)
        sc.note(CH_BASS, p, t, 0.4,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _brass_pairs(sc: en.Score, starts: tuple[float, ...], v0: int,
                 v1: int) -> None:
    """Call from the left post, answer from the right, chord-rooted."""
    n = len(starts)
    for i, t in enumerate(starts):
        vel = int(en.lerp(v0, v1, i / max(1, n - 1)))
        r = BRASS_ROOT[_chord_deg(t)]
        for p, off, dur in ((r, 0.0, 0.4), (r + 7, 0.5, 0.4),
                            (r + 12, 1.0, 0.75)):
            sc.note(CH_BRASS_L, p, t + off, dur,
                    vel + (4 if off == 1.0 else 0), jt=2, jv=4)
        for p, off, dur in ((r + 12, 2.0, 0.4), (r + 7, 2.5, 0.4),
                            (r, 3.0, 0.75)):
            sc.note(CH_BRASS_R, p, t + off, dur,
                    vel + (4 if off == 3.0 else 0), jt=2, jv=4)


def _four_floor(sc: en.Score, t0: float, t1: float, kick: int, clap: int,
                hat: int, open_hat: int, hat16: int = 0,
                tamb: int = 0) -> None:
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(CH_KIT, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(CH_KIT, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(CH_KIT, 46, t + 0.5, 0.4, open_hat, jt=0, jv=4)
            if hat16:
                sc.note(CH_KIT, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(CH_KIT, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
            if tamb:
                sc.note(CH_KIT, 54, t + 0.5, 0.3, tamb, jt=0, jv=4)
        sc.note(CH_KIT, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(CH_KIT, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)


def _build_drums(sc: en.Score, t0: float, hats: tuple[int, int, int],
                 claps: tuple[int, int, int],
                 kicks: tuple[int, int, int]) -> None:
    """24 bars of climbing groove in three 8-bar windows."""
    for b in range(24):
        bar = t0 + 4.0 * b
        w = b // 8
        for k in range(8):
            sc.note(CH_KIT, 42, bar + 0.5 * k, 0.2, hats[w], jt=0, jv=3)
        sc.note(CH_KIT, 39, bar + 1.0, 0.3, claps[w], jt=0, jv=4)
        sc.note(CH_KIT, 39, bar + 3.0, 0.3, claps[w], jt=0, jv=4)
        if kicks[w]:
            for k in range(4):
                sc.note(CH_KIT, 36, bar + k, 0.25, kicks[w], jt=0, jv=4)


def _snare_roll(sc: en.Score, t0: float, t1: float, v0: int,
                v1: int) -> None:
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(CH_KIT, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _fill_big(sc: en.Score, t0: float) -> None:
    for i in range(12):
        sc.note(CH_TOMS, TOM_SEQ[i % 8], t0 + 0.25 * i, 0.22,
                int(en.lerp(74, 112, i / 11)), jt=0, jv=4)
    for i, p in enumerate((50, 52, 55, 57)):
        sc.note(CH_SYNDRUM, p, t0 + 3.0 + 0.25 * i, 0.22, 96 + 4 * i,
                jt=0, jv=4)


def _fill_small(sc: en.Score, t0: float) -> None:
    for i, (off, p) in enumerate(((0.0, 62), (0.5, 58), (0.75, 55),
                                  (1.0, 53), (1.5, 50), (1.75, 46))):
        sc.note(CH_TOMS, p, t0 + off, 0.2, 84 + 3 * i, jt=0, jv=4)
    sc.note(CH_SYNDRUM, 52, t0 + 1.25, 0.2, 92, jt=0, jv=4)
    sc.note(CH_SYNDRUM, 55, t0 + 1.75, 0.2, 98, jt=0, jv=4)


def _fills_in(sc: en.Score, t0: float, t1: float) -> None:
    for t in FILLS_BIG:
        if t0 <= t < t1:
            _fill_big(sc, t)
    for t in FILLS_SMALL:
        if t0 <= t < t1:
            _fill_small(sc, t)


def _risers_in(sc: en.Score, t0: float, t1: float) -> None:
    for t, dur, vel in RISER_NOTES:
        if t0 <= t < t1:
            sc.note(CH_RISER, RISER_PITCH, t, dur, vel, jt=0, jv=0)


def _hits(sc: en.Score, t0: float, t1: float, step: float,
          vel: int) -> None:
    n = int(round((t1 - t0) / step))
    for i in range(n):
        t = t0 + step * i
        sc.note(CH_HIT, HIT_ROOT[_chord_deg(t)], t, 0.9, vel, jt=0, jv=3)


def _crashes(sc: en.Score, t0: float, t1: float, vel: int) -> None:
    t = t0
    while t < t1 - 1e-9:
        sc.note(CH_KIT, 49, t, 1.5, vel, jt=0, jv=4)
        vel = max(88, vel - 12)
        t += 32.0


# ---------------------------------------------------------------------------
# -One emitters — the distorted guitar, the choir counterpoint, the fills.
# ---------------------------------------------------------------------------

def _guitar_solo(sc: en.Score, t0: float, t1: float) -> None:
    """Emit distorted-lead notes with onset in [t0, t1).  jt=0: tick-exact."""
    for onset, p, dur, vel in GUITAR_SOLO:
        if t0 <= onset < t1:
            sc.note(CH_GUITAR, p, onset, dur, vel, jt=0, jv=2)


def _guitar_bends(sc: en.Score, t0: float, t1: float) -> None:
    """Emit the marked pitch-bend gestures starting in [t0, t1) as linear
    ramps; each ends at 0 before its section boundary (bend hygiene)."""
    for a, b, s0, s1 in GUITAR_BENDS:
        if not (t0 <= a < t1):
            continue
        n = max(1, int(round((b - a) / 0.0625)))
        for i in range(n + 1):
            sc.bend(CH_GUITAR, a + (b - a) * i / n, en.lerp(s0, s1, i / n))


def _guitar_cc1(sc: en.Score, t0: float, t1: float) -> None:
    """Mod-wheel wail: a CC1 swell (0 -> peak -> 0) over every sustained
    (>= 2 beat) guitar note in [t0, t1).  Keeps the bend lane clean."""
    for onset, p, dur, vel in GUITAR_SOLO:
        if not (t0 <= onset < t1) or dur < 2.0:
            continue
        peak = min(90, 34 + int(round(dur * 9)))
        en.cc_curve(sc, CH_GUITAR, 1,
                    [(onset, 0), (onset + 0.35 * dur, peak),
                     (onset + dur - 0.1, 0)], step=0.25)


def _choir2(sc: en.Score, t0: float, t1: float) -> None:
    """Emit counterpoint notes with onset in [t0, t1) (no bends — CC1 only)."""
    for onset, p, dur, vel in CHOIR2_SOLO:
        if t0 <= onset < t1:
            sc.note(CH_CHOIR2, p, onset, dur, vel, jt=0, jv=2)


def _choir2_controllers(sc: en.Score) -> None:
    """The counterpoint's expression lanes (CC is not bounds-checked, so the
    whole span is authored once here): an 'oo' vowel held low for contrast
    with the ch8 'ah' bed, an entry swell, and light vibrato on long tones."""
    en.vowel_curve(sc, CH_CHOIR2, [(510.0, 30), (560.0, 36), (638.0, 40)],
                   step=4.0)
    en.cc_curve(sc, CH_CHOIR2, 11,
                [(510.0, 60), (514.0, 100), (636.0, 100), (639.0, 66)],
                step=1.0)
    for onset, p, dur, vel in CHOIR2_SOLO:
        if dur >= 4.0:
            en.cc_curve(sc, CH_CHOIR2, 1,
                        [(onset, 0), (onset + 0.4 * dur, 28),
                         (onset + dur - 0.2, 0)], step=0.5)


def _play_fill(sc: en.Score, shape: str, t0: float, vbump: int = 0) -> None:
    """Play one library fill shape at beat t0 (velocity +vbump for build two)."""
    lib = FILL_LIB[shape]
    for off, p, dur, vel in lib["tom"]:
        sc.note(CH_TOMS, p, t0 + off, dur, min(112, vel + vbump), jt=0, jv=4)
    for off, p, dur, vel in lib["syn"]:
        sc.note(CH_SYNDRUM, p, t0 + off, dur, min(112, vel + vbump), jt=0, jv=4)


def _build_fills(sc: en.Score, t0: float, t1: float) -> None:
    """Play the escalating fill schedule for starts in [t0, t1)."""
    for start, shape in FILL_SCHEDULE:
        if t0 <= start < t1:
            _play_fill(sc, shape, start, vbump=4 if start >= BUILD2[0] else 0)


# ---------------------------------------------------------------------------
# Builders — one per movement.
# ---------------------------------------------------------------------------

def _b_intro(sc: en.Score) -> None:
    """[0,64): the orbit alone, then the stage assembles around it."""
    _orbit_pan_lane(sc)                       # the whole piece's circles
    _orbit_notes(sc, *INTRO)
    # Pad breathing + brightness choreography for the full timeline.
    en.cc_curve(sc, CH_PAD, 74, [
        (0.0, 46), (64.0, 46), (159.5, 100), (160.0, 104), (287.5, 104),
        (288.0, 60), (320.0, 48), (415.5, 104), (416.0, 110),
        (640.0, 84), (657.0, 44)], step=2.0)
    en.cc_curve(sc, CH_PAD, 11, [(0.0, 100), (288.0, 88), (320.0, 104),
                                 (640.0, 102), (657.0, 30)], step=4.0)
    _pad_chords(sc, 16.0, [1, 1, 1], span=16.0, vel=48, vel_end=54)
    for k in range(8):
        sc.note(CH_BASS, BASS_ROOT[1], 32.0 + 4.0 * k, 3.8, 46 + k,
                jt=3, jv=2)
    for i in range(64):                       # hats tick in from bar 9
        sc.note(CH_KIT, 42, 32.0 + 0.5 * i, 0.2,
                int(en.lerp(34, 50, i / 63)), jt=0, jv=3)
    _brass_pairs(sc, *BRASS_PAIRS["intro"])


def _b_build1(sc: en.Score) -> None:
    """[64,160): climb one — three strictly-rising 8-bar windows."""
    _orbit_notes(sc, *BUILD1)
    _pad_chords(sc, BUILD1[0], list(CHORD_DEGS) * 3, span=8.0,
                vel=54, vel_end=66)
    _bass_half_notes(sc, 64.0, 96.0, 58, 62)
    _bass_8ths(sc, 96.0, 160.0, 68, 78, pops=False)
    _build_drums(sc, BUILD1[0], hats=(54, 60, 66), claps=(56, 64, 70),
                 kicks=(0, 92, 100))
    _brass_pairs(sc, *BRASS_PAIRS["build1"])
    _snare_roll(sc, 152.0, 160.0, 46, 90)
    _fills_in(sc, *BUILD1)
    _build_fills(sc, *BUILD1)          # -One: the escalating fill bed
    _risers_in(sc, *BUILD1)


def _b_drop1(sc: en.Score) -> None:
    """[160,288): drop one — the theatre in full circle."""
    _orbit_notes(sc, *DROP1)
    _pad_chords(sc, DROP1[0], list(CHORD_DEGS) * 4, span=8.0, vel=70)
    _bass_8ths(sc, *DROP1, 86, 90, pops=True)
    _four_floor(sc, *DROP1, kick=112, clap=106, hat=72, open_hat=80)
    _crashes(sc, *DROP1, vel=112)
    for r in range(4):
        en.line(sc, CH_LEAD, DROP1[0] + 32.0 * r, LEAD_ROOT, MODE, HOOK,
                vel=95, gate=0.96, jt=2, jv=4)
    _hits(sc, *DROP1, step=8.0, vel=104)
    _brass_pairs(sc, *BRASS_PAIRS["drop1"])
    _fills_in(sc, *DROP1)


def _b_bridge(sc: en.Score) -> None:
    """[288,320): the aerial — half time, drums silent, the sky."""
    sc.note(CH_KIT, 49, BRIDGE[0], 2.0, 80, jt=0, jv=3)   # wash into it
    for pitches, t, vel in AERIAL_CHORDS:
        for p in pitches:
            sc.note(CH_AERIAL, p, t, 15.7, vel, jt=3, jv=2)
    en.cc_curve(sc, CH_AERIAL, 11, [
        (288.0, 70), (296.0, 96), (304.0, 82), (312.0, 100),
        (318.0, 90)], step=1.0)
    for b in range(8):
        pitches = HARP_EM9 if b % 2 == 0 else HARP_CM9
        en.arp(sc, CH_HARP, list(pitches), 288.0 + 4.0 * b, count=8,
               step=0.25, vel=58 + b, pattern="up")
    sc.cc(CH_CHOIR, 11, 108, 302.0)
    en.vowel_curve(sc, CH_CHOIR, [(288.0, 25), (304.0, 32), (320.0, 45)],
                   step=2.0)
    for p in CHOIR_RF[1]:
        sc.note(CH_CHOIR, p, 304.0, 15.5, 46, jt=3, jv=2)
    _risers_in(sc, *BRIDGE)


def _b_build2(sc: en.Score) -> None:
    """[320,416): climb two — the company gathers."""
    _orbit_notes(sc, *BUILD2)
    _pad_chords(sc, BUILD2[0], list(CHORD_DEGS) * 3, span=8.0,
                vel=58, vel_end=70)
    _bass_half_notes(sc, 320.0, 352.0, 62, 66)
    _bass_8ths(sc, 352.0, 416.0, 72, 82, pops=False)
    _build_drums(sc, BUILD2[0], hats=(58, 64, 70), claps=(60, 68, 74),
                 kicks=(0, 96, 104))
    _brass_pairs(sc, *BRASS_PAIRS["build2"])
    for c in range(12):
        t = BUILD2[0] + 8.0 * c
        for p in CHOIR_RF[_chord_deg(t)]:
            sc.note(CH_CHOIR, p, t, 7.8, int(en.lerp(52, 68, c / 11)),
                    jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(320.0, 45), (352.0, 62), (384.0, 74),
                                  (416.0, 88)], step=2.0)
    _snare_roll(sc, 408.0, 416.0, 50, 96)
    _fills_in(sc, *BUILD2)
    _build_fills(sc, *BUILD2)          # -One: denser fills on the second climb
    _guitar_solo(sc, *BUILD2)          # -One: the solo materializes, teasing
    _guitar_bends(sc, *BUILD2)
    _guitar_cc1(sc, *BUILD2)
    _risers_in(sc, *BUILD2)


def _b_drop2(sc: en.Score) -> None:
    """[416,544): drop two — full company, orbit lifted an octave."""
    _orbit_notes(sc, *DROP2)
    _pad_chords(sc, DROP2[0], list(CHORD_DEGS) * 4, span=8.0, vel=74)
    _bass_8ths(sc, *DROP2, 90, 94, pops=True)
    _four_floor(sc, *DROP2, kick=116, clap=108, hat=74, open_hat=82,
                hat16=58, tamb=54)
    _crashes(sc, *DROP2, vel=116)
    for r in range(4):
        en.line(sc, CH_LEAD, DROP2[0] + 32.0 * r, LEAD_ROOT, MODE, HOOK,
                vel=100, gate=0.96, jt=2, jv=4)
    _hits(sc, *DROP2, step=4.0, vel=106)
    _brass_pairs(sc, *BRASS_PAIRS["drop2"])
    for c in range(16):
        t = DROP2[0] + 8.0 * c
        for p in CHOIR_TRIAD[_chord_deg(t)]:
            sc.note(CH_CHOIR, p, t, 7.8, 76, jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(416.0, 88), (540.0, 95)], step=4.0)
    _guitar_solo(sc, *DROP2)           # -One: the full wail over drop two
    _guitar_bends(sc, *DROP2)
    _guitar_cc1(sc, *DROP2)
    _choir2(sc, *DROP2)                # -One: counterpoint enters, rising
    _choir2_controllers(sc)            # authors the whole ch15 CC span once
    _fills_in(sc, *DROP2)
    _risers_in(sc, *DROP2)


def _b_finale(sc: en.Score) -> None:
    """[544,640): the stack — dive + walker + orbit in counterpoint."""
    _orbit_notes(sc, *FINALE)
    for s in WALKER_STARTS:
        for i, deg in enumerate(material.WALKER_THEME):
            sc.note(CH_LEAD,
                    en.pitch(WALKER_ROOT, material.WALKER_MODE, deg),
                    s + i * material.WALKER_STEP, 0.45, 102, jt=0, jv=3)
    for s in DIVE_STARTS:
        for oi, root in enumerate(DIVE_ROOTS):
            for i, deg in enumerate(material.DIVE_CASCADE):
                sc.note(CH_HARP, en.pitch(root, material.DIVE_MODE, deg),
                        s + oi * 2.0 + i * material.DIVE_STEP, ORBIT_DUR,
                        int(en.lerp(98, 78, (oi * 8 + i) / 31)),
                        jt=0, jv=3)
    _pad_chords(sc, FINALE[0], [1] * 12, span=8.0, vel=74)
    _bass_8ths(sc, *FINALE, 92, 92, pops=True)
    _four_floor(sc, *FINALE, kick=112, clap=106, hat=72, open_hat=80,
                hat16=56)
    _crashes(sc, *FINALE, vel=118)
    _hits(sc, *FINALE, step=4.0, vel=108)
    for k in range(6):
        for p in (52, 64):
            sc.note(CH_CHOIR, p, FINALE[0] + 16.0 * k, 15.7, 74,
                    jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(544.0, 96), (640.0, 80)], step=4.0)
    for k in range(3):
        for p in (76, 83):
            sc.note(CH_AERIAL, p, FINALE[0] + 32.0 * k, 31.5, 56,
                    jt=3, jv=2)
    _guitar_solo(sc, *FINALE)          # -One: the soaring solo on top
    _guitar_bends(sc, *FINALE)
    _guitar_cc1(sc, *FINALE)
    _choir2(sc, *FINALE)               # -One: the finale counterpoint
    _fills_in(sc, *FINALE)


def _b_outro(sc: en.Score) -> None:
    """[640,660): splashdown — one hit, the pads settle, lights out."""
    sc.note(CH_KIT, 49, OUTRO[0], 2.0, 108, jt=0, jv=3)
    sc.note(CH_HIT, HIT_ROOT[1], OUTRO[0], 2.0, 118, jt=0, jv=3)
    en.pad_block(sc, CH_PAD, OUTRO[0], [en.triad(52, MODE, 1)],
                 span=17.5, size=4, lo=52, hi=76, vel=58)
    for i, p in enumerate((52, 59, 64)):
        sc.note(CH_CHOIR, p, OUTRO[0], 17.5, 60 - i, jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(640.0, 80), (656.0, 28)], step=2.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(640.0, 104), (657.0, 26)], step=1.0)
    # Deterministic (jt=0) so the first note cannot jitter back across the
    # 640 boundary into the finale window: the -One additions shift the shared
    # RNG stream, and en.arp's jt=4 would otherwise let it bleed into the dive
    # lane's [544,640) count (finale_stack_fidelity).
    for i, p in enumerate((52, 59, 64, 71, 76, 79, 83, 88)):
        sc.note(CH_HARP, p, OUTRO[0] + 0.5 * i, 0.625, 62, jt=0, jv=4)
    sc.note(CH_BASS, BASS_ROOT[1], 640.0, 7.8, 56, jt=3, jv=2)
    sc.note(CH_BASS, BASS_ROOT[1], 648.0, 7.8, 46, jt=3, jv=2)


BUILDERS: list = [_b_intro, _b_build1, _b_drop1, _b_bridge,
                  _b_build2, _b_drop2, _b_finale, _b_outro]
