"""t09_night_launch.py — Slipstream T9: "Night Launch".

The night display — afterburners, searchlights, pyro.  G# aeolian, 130 bpm,
4/4, ~4:55.  The album's dynamic-range act: a near-silent night field ignites
into two dark four-on-the-floor passes, split by the SEARCHLIGHT — the pinned
Three-Sixty-One quote (ORBIT_RIFF_361 on soft vibes, ten tick-exact
statements) while a slow autopan sweeps a transient bell arp across the crowd.

HLD section 4 / T9 contracts realized here:
  * duo formation SOAR OVER PEDAL — wing ship (ch15, GM30) re-picks low
    pedal fifths on every bar line of the pinned formation spans; lead ship
    (ch14, GM29+bank1) soars above on >=6-beat held tones with CC1 blooms,
    soar pitch floor pinned at 68 (`duo_soar_over_pedal`);
  * the searchlight quote — ORBIT_RIFF_361 pinned tick-exact to
    material.py's Through Lines data, 10 statements (`searchlight_orbit_quote`);
  * pyro — orchestra hits on a pinned off-beat (x.5) schedule whose density
    strictly doubles DROP1 -> DROP2 (`pyro_schedule`);
  * the night dynamic range — quietest 32-beat window <= half the peak, and
    the peak window sits inside Full Burn (`night_dynamic_range`);
  * build/drop contour — strictly-rising 16-beat velocity-mass windows in
    both climbs, DROP2 mean per-bar mass > DROP1, searchlight hushed under
    half of DROP1 (`build_drop_contour`);
  * fills — escalating per-window counts, >=5 shapes per climb, a >=20-note
    unbroken bespoke fill into each drop, drops thinned (`fill_escalation`);
  * the panning searchlight rides ONLY the transient ch0 arp
    (`autopan_transient_only`);
  * counterpoint — lead ship vs saw in Full Burn, pinned span, downbeat
    consonance / contrary+oblique / no pc doubling (`drop2_counterpoint`);
  * album DNA — ASCENT_CELL stated tick-exact at the Full Burn downbeat
    (`ascent_statement`); CC74 macro-sweep, GM119 risers into every lift and
    the CC65 portamento swoop (`soar_sweep_risers`).
"""

from __future__ import annotations

import engine as en
import material
import conductor

NUMBER = 9
TITLE = "Night Launch"
FILE = "09 - Night Launch.mid"
SEED = 20261109
COMMENT = ("Night Launch - the night display. A sleeping airfield ignites: "
           "afterburner bass, pyro orchestra-hits on the off-beats, and the "
           "duo in SOAR-OVER-PEDAL formation - the wing ship re-picking low "
           "pedal fifths while the lead ship holds long burning tones above. "
           "Midway the searchlight pans the crowd: Three-Sixty-One's orbit "
           "riff, quoted tick-exact on soft vibes. Slipstream T9, seed "
           "20261109.")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

BPM = 130.0
MODE = "aeolian"

NF0 = 0.0      # I.    Night Field
IGN0 = 64.0    # II.   Ignition
B1S = 136.0    # III.  Burner Climb (build 1)
D1S = 208.0    # IV.   First Pass (drop 1)
SL0 = 288.0    # V.    Searchlight
B2S = 376.0    # VI.   Second Climb (build 2)
D2S = 448.0    # VII.  Full Burn (drop 2)
OUT0 = 568.0   # VIII. Afterglow
END = 636.0

MOVEMENTS = [
    ("I. Night Field", NF0, IGN0),
    ("II. Ignition", IGN0, B1S),
    ("III. Burner Climb", B1S, D1S),
    ("IV. First Pass", D1S, SL0),
    ("V. Searchlight", SL0, B2S),
    ("VI. Second Climb", B2S, D2S),
    ("VII. Full Burn", D2S, OUT0),
    ("VIII. Afterglow", OUT0, END),
]

# channels
A0, PAD, BASS, PL, PR, SAW, BEL, STR, CHO = 0, 1, 2, 3, 4, 5, 6, 7, 8
KIT, TOM, SYN, HIT, RIS, LEAD, WING = 9, 10, 11, 12, 13, 14, 15

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVEMENTS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 5, 1)],                     # G# minor: five sharps
    channels=[
        (A0, "pulse arp", 80, 96, 64, 30),     # square blips / searchlight bell
        (PAD, "night pad", 89, 100, 64, 72),
        (BASS, "burner bass", 38, 112, 64, 12),
        (PL, "post L pizz", 45, 92, 18, 40),
        (PR, "post R harp", 46, 92, 110, 48),
        (SAW, "saw soar", 81, 104, 64, 48),
        (BEL, "searchlight vibes", 11, 100, 64, 66),
        (STR, "aerial strings", 49, 96, 64, 68),
        (CHO, "night choir", 52, 102, 64, 74),
        (KIT, "kit", 0, 118, 64, 28),
        (TOM, "toms B", 117, 108, 64, 30),
        (SYN, "syndrum B", 118, 106, 64, 26),
        (HIT, "pyro hits", 55, 112, 64, 60),
        (RIS, "riser", 119, 100, 64, 70),
        (LEAD, "lead ship", 29, 118, 64, 20),
        (WING, "wing ship", 30, 110, 64, 22),
    ],
    program_changes=[(9, 0.0, 1),              # the V3 kit
                     (A0, SL0, 9),             # ch0 -> glockenspiel (searchlight)
                     (A0, 374.0, 80)],         # ch0 back to square
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1)],
)

# ---------------------------------------------------------------------------
# Harmony (G# aeolian).  Chords as pitch-class sets; per-role root anchors.
# ---------------------------------------------------------------------------

CHORD = {"Gs": (8, 11, 3), "E": (4, 8, 11), "Fs": (6, 10, 1),
         "Cs": (1, 4, 8), "B": (11, 3, 6)}
R_BASS = {"Gs": 32, "E": 28, "Fs": 30, "Cs": 37, "B": 35}
R_ARP = {"Gs": 56, "E": 52, "Fs": 54, "Cs": 49, "B": 59}
R_PED = {"Gs": 44, "E": 40, "Fs": 42, "Cs": 37, "B": 47}
R_BELL = {"Gs": 80, "E": 76, "Fs": 78, "Cs": 73, "B": 83}
ST1 = {"Gs": 75, "E": 76, "B": 78, "Fs": 73}

GRID_NF = [(0.0, "Gs"), (8.0, "Gs"), (16.0, "E"), (24.0, "E"),
           (32.0, "Cs"), (40.0, "Cs"), (48.0, "Fs"), (56.0, "Fs")]
GRID_IGN = [(64.0, "Gs"), (72.0, "E"), (80.0, "Gs"), (88.0, "Fs"),
            (96.0, "Gs"), (104.0, "E"), (112.0, "Cs"), (120.0, "Fs"),
            (128.0, "Gs")]
GRID_B1 = [(136.0, "Gs"), (144.0, "E"), (152.0, "B"), (160.0, "Fs"),
           (168.0, "Gs"), (176.0, "E"), (184.0, "B"), (192.0, "Fs"),
           (200.0, "Gs")]
GRID_D1 = [(208.0, "Gs"), (224.0, "E"), (240.0, "B"), (256.0, "Fs"),
           (272.0, "Gs")]
GRID_SL = [(288.0, "Gs"), (296.0, "E"), (304.0, "Gs"), (312.0, "Fs"),
           (320.0, "Gs"), (328.0, "E"), (336.0, "Cs"), (344.0, "Fs"),
           (352.0, "Gs"), (360.0, "E"), (368.0, "Fs")]
GRID_B2 = [(376.0, "Gs"), (384.0, "E"), (392.0, "B"), (400.0, "Fs"),
           (408.0, "Gs"), (416.0, "E"), (424.0, "B"), (432.0, "Fs"),
           (440.0, "Gs")]
GRID_D2 = [(448.0, "Gs"), (456.0, "E"), (464.0, "B"), (472.0, "Fs"),
           (480.0, "Gs"), (488.0, "E"), (496.0, "B"), (504.0, "Fs"),
           (512.0, "Gs"), (520.0, "E"), (528.0, "B"), (536.0, "Fs"),
           (544.0, "Gs"), (552.0, "Fs"), (560.0, "Gs")]
GRID_OUT = [(568.0, "Gs"), (584.0, "E"), (600.0, "Gs")]


def _slots(grid, t_end):
    """(t0, t1, name) triples for a grid closed at t_end."""
    ext = grid + [(t_end, None)]
    return [(a, b, nm) for (a, nm), (b, _n2) in zip(ext, ext[1:])]


def _bars(t0, t1):
    b = t0
    while b < t1 - 1e-9:
        yield b
        b += 4.0


# ---------------------------------------------------------------------------
# Pinned oracle data (write the oracle, compose to pass it)
# ---------------------------------------------------------------------------

FORMATION_SPANS = [(72.0, 136.0), (208.0, 288.0), (448.0, 568.0)]
LEAD_FLOOR = 66          # every lead-ship pitch in a formation span
SOAR_FLOOR = 68          # every >=6-beat soar note
SOAR_MIN = 6.0
PED_ROOT_CEIL = 47       # wing pedal root ceiling (dyad top <= 54)

QUOTE_ROOT = 68          # G#4: the searchlight states the orbit riff here
QUOTE_STARTS = [296.0 + 8.0 * k for k in range(10)]

PYRO_D1 = [D1S + 8.0 * k + 1.5 for k in range(10)]
PYRO_D2 = sorted([D2S + 4.0 * k + 1.5 for k in range(30)]
                 + [D2S + 8.0 * k + 3.5 for k in range(15)])
PYRO_FINAL = 616.5
PYRO_PITCH = 56

RISERS = [(200.0, 8.0), (440.0, 8.0), (508.0, 4.0)]   # into D1, D2, mid-burn lift

ASCENT_AT = 448.0
ASCENT_ROOT = 68

CP_SPAN = (480.0, 544.0)          # lead ship vs saw, 16 structural downbeats

B1_WINDOWS = [(144.0, 160.0), (160.0, 176.0), (176.0, 192.0), (192.0, 208.0)]
B2_WINDOWS = [(384.0, 400.0), (400.0, 416.0), (416.0, 432.0), (432.0, 448.0)]
DROP_FILL_CAP = 12

AUTOPAN_SPAN = (288.0, 374.5)
SWEEP_SPAN = (376.0, 444.2)       # CC74 macro sweep window (monotone rise)
SWOOP_PAIR = ((438.0, 68), (440.0, 80))   # CC65 portamento swoop, +12 semis

# escalating fill schedule: (beat, FILL_LIB shape, vbump)
FILL_SCHEDULE = [
    (96.0, "A", 0), (126.0, "B", 0),
    # Burner Climb: windows 3 < 9 < 16 < 44 notes
    (150.0, "A", 0), (166.0, "C", 0), (180.0, "B", 2), (188.0, "D", 2),
    (194.0, "E", 4), (199.0, "G", 4),
    # First Pass, thinned
    (238.0, "A", 2), (262.0, "H", 2), (279.5, "D", 2),
    # Searchlight, hushed
    (330.0, "A", -18), (358.0, "C", -18),
    # Second Climb: windows 9 < 11 < 17 < 45 notes
    (380.0, "A", 0), (392.0, "C", 2), (404.0, "B", 2), (412.0, "A", 2),
    (420.0, "G", 4), (426.0, "F", 4), (433.0, "E", 6), (436.5, "H", 6),
    # Full Burn, thinned
    (478.0, "A", 4), (502.0, "D", 4), (526.0, "H", 4), (549.0, "G", 4),
]
BIG_FILLS = [(202.0, 24, 70, 112), (441.5, 26, 74, 112)]   # bespoke pre-drop runs

# ---------------------------------------------------------------------------
# Module verification config
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {1, 9, 11, 29, 30, 38, 45, 46, 49, 52, 55, 80, 81, 89,
                     117, 118, 119}
CENTERED_CHANNELS = {1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    A0: (48, 88), PAD: (46, 78), BASS: (26, 50), PL: (64, 84), PR: (72, 90),
    SAW: (60, 88), BEL: (62, 90), STR: (53, 84), CHO: (49, 78), KIT: (35, 52),
    TOM: (44, 64), SYN: (46, 60), HIT: (54, 58), RIS: (60, 64),
    LEAD: (64, 90), WING: (36, 55),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (288.0, 299.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Shared emitters
# ---------------------------------------------------------------------------


def _pads(sc, ch, t0, names, span, size, lo, hi, v0, v1=None, legato=0.25):
    """Voice-led tied chord bed, jt=0 (movement-boundary safe)."""
    voicings, prev = [], None
    for nm in names:
        prev = en.voice_lead(list(CHORD[nm]), prev, size, lo, hi)
        voicings.append(prev)
    total = len(names) * span
    for vi in range(size):
        i = 0
        while i < len(voicings):
            p = voicings[i][vi]
            j = i
            while j + 1 < len(voicings) and voicings[j + 1][vi] == p:
                j += 1
            v = v0 if v1 is None else en.lerp(v0, v1, (i * span) / total)
            sc.note(ch, p, t0 + i * span, (j - i + 1) * span + legato,
                    int(round(v)), jt=0, jv=2)
            i = j + 1


def _bass_drive(sc, grid, t_end, v0, v1, push=False):
    """Afterburner ostinato: 8ths with octave pops (+ a 16th push in drops)."""
    t_start = grid[0][0]
    for a, b, nm in _slots(grid, t_end):
        r = R_BASS[nm]
        for bar in _bars(a, b):
            x = (bar - t_start) / (t_end - t_start)
            v = en.lerp(v0, v1, x)
            for k in range(8):
                p = r + (12 if k in (2, 5, 7) else 0)
                acc = 8 if k in (0, 4) else 0
                sc.note(BASS, p, bar + 0.5 * k, 0.38,
                        int(round(v)) + acc, jt=0, jv=3)
            if push:
                sc.note(BASS, r, bar + 3.75, 0.2, int(round(v)) - 6,
                        jt=0, jv=3)


def _arp8(sc, grid, t_end, v0, v1):
    """ch0 square 8ths: root / fifth blips."""
    t_start = grid[0][0]
    for a, b, nm in _slots(grid, t_end):
        base = R_ARP[nm]
        t = a
        while t < b - 1e-9:
            x = (t - t_start) / (t_end - t_start)
            p = base if (int(round(t * 2)) % 2 == 0) else base + 7
            acc = 6 if abs(t % 4.0) < 1e-9 else 0
            sc.note(A0, p, t, 0.22, int(round(en.lerp(v0, v1, x))) + acc,
                    jt=0, jv=2)
            t += 0.5


def _arp16(sc, grid, t_end, v0, v1, lift=0):
    """ch0 square 16ths [b, b+7, b+12, b+7] — the motion engine."""
    t_start = grid[0][0]
    pat = (0, 7, 12, 7)
    for a, b, nm in _slots(grid, t_end):
        base = R_ARP[nm] + lift
        t = a
        while t < b - 1e-9:
            x = (t - t_start) / (t_end - t_start)
            k = int(round((t - a) * 4)) % 4
            acc = 6 if k == 0 else 0
            sc.note(A0, base + pat[k], t, 0.2,
                    int(round(en.lerp(v0, v1, x))) + acc, jt=0, jv=2)
            t += 0.25


def _wing_pedals(sc, grid, t_end, v0, v1):
    """The wing ship's formation lane: low pedal fifths re-picked per bar."""
    t_start = grid[0][0]
    for a, b, nm in _slots(grid, t_end):
        r = R_PED[nm]
        for bar in _bars(a, b):
            v = int(round(en.lerp(v0, v1, (bar - t_start) / (t_end - t_start))))
            sc.note(WING, r, bar, 3.9, v, jt=0, jv=2)
            sc.note(WING, r + 7, bar, 3.9, max(1, v - 6), jt=0, jv=2)


def _wing_chugs(sc, grid, t_end, v0, v1, six_from=None):
    """Muted chug engine for the climbs (outside the formation spans)."""
    t_start = grid[0][0]
    for a, b, nm in _slots(grid, t_end):
        r = R_PED[nm]
        for bar in _bars(a, b):
            x = (bar - t_start) / (t_end - t_start)
            v = en.lerp(v0, v1, x)
            if six_from is not None and bar >= six_from:
                t = bar
                while t < bar + 4.0 - 1e-9:
                    sc.note(WING, r, t, 0.2, int(round(v)) + 4, jt=0, jv=3)
                    t += 0.25
            else:
                for k in range(8):
                    acc = 10 if k == 0 else 0
                    sc.note(WING, r, bar + 0.5 * k, 0.3,
                            int(round(v)) + acc, jt=0, jv=3)


def _bloom(sc, ch, on, dur):
    """The T361 CC1 bloom over a held tone (digest formula)."""
    peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _lead_table(sc, notes):
    for t, p, dur, vel in notes:
        sc.note(LEAD, p, t, dur * 0.98, vel, jt=0, jv=2)
        if dur >= 2.0:
            _bloom(sc, LEAD, t, dur)


def _slur(sc, t0, t1):
    sc.cc(LEAD, 68, 96, t0 - 0.05)
    sc.cc(LEAD, 68, 0, t1 + 0.05)


def _post_call(sc, ch, t, seq, vel):
    for i, p in enumerate(seq):
        sc.note(ch, p, t + 0.25 * i, 0.2, max(1, vel - 2 * i), jt=0, jv=3)


CALL_L = [68, 75, 80]
CALL_L4 = [68, 75, 80, 83]
CALL_DESC = [80, 75, 68]
ANS_R = [87, 80, 75]


def _slot_bells(sc, grid, t_end, vel, dur=1.5):
    for a, _b, nm in _slots(grid, t_end):
        sc.note(BEL, R_BELL[nm], a, dur, vel, jt=0, jv=3)


def _fills_in(sc, t0, t1):
    for beat, shape, vb in FILL_SCHEDULE:
        if t0 <= beat < t1:
            material.play_fill(sc, shape, beat, vbump=vb)


def _big_fill(sc, t0, n, v0, v1):
    """Bespoke pre-drop run: an unbroken 16th tom/syn cascade, jt=0."""
    toms = [64, 62, 60, 58, 55, 53, 50, 46]
    syns = [60, 57, 55, 52, 50, 48]
    ti = si = 0
    for i in range(n):
        t = t0 + 0.25 * i
        v = int(round(en.lerp(v0, v1, i / (n - 1))))
        if i % 2 == 0:
            sc.note(TOM, toms[ti % len(toms)], t, 0.18, v, jt=0, jv=2)
            ti += 1
        else:
            sc.note(SYN, syns[si % len(syns)], t, 0.18, v, jt=0, jv=2)
            si += 1


def _snare_roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(KIT, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


# ---------------------------------------------------------------------------
# Featured note tables (explicit, oracle-facing)
# ---------------------------------------------------------------------------

LEAD_IGN = [
    (72.0, 68, 8.0, 78), (84.0, 71, 8.0, 80), (96.0, 68, 6.0, 80),
    (104.0, 73, 8.0, 84), (116.0, 71, 6.0, 82), (124.0, 75, 8.0, 86),
    (132.0, 76, 4.0, 88),
]

LEAD_D1 = [
    (208.0, 75, 8.0, 98), (216.0, 71, 6.0, 94), (222.0, 73, 1.0, 90),
    (223.0, 75, 1.0, 92), (224.0, 76, 8.0, 100), (232.0, 71, 4.0, 92),
    (236.0, 73, 2.0, 92), (238.0, 75, 2.0, 94), (240.0, 78, 8.0, 102),
    (248.0, 75, 6.0, 96), (254.0, 73, 2.0, 92), (256.0, 70, 8.0, 96),
    (264.0, 73, 6.0, 96), (270.0, 75, 2.0, 94), (272.0, 80, 8.0, 104),
    (280.0, 78, 4.0, 98), (284.0, 75, 4.0, 96),
]

LEAD_D2 = [
    (452.0, 83, 2.0, 100), (454.0, 80, 2.0, 98), (456.0, 76, 6.0, 102),
    (462.0, 78, 2.0, 96), (464.0, 75, 8.0, 104), (472.0, 73, 6.0, 102),
    (478.0, 75, 1.0, 94), (479.0, 78, 1.0, 96), (480.0, 80, 8.0, 106),
    (488.0, 76, 6.0, 102), (494.0, 75, 1.0, 94), (495.0, 76, 1.0, 95),
    (496.0, 78, 6.0, 104), (502.0, 76, 1.0, 94), (503.0, 75, 1.0, 94),
    (504.0, 73, 8.0, 102), (512.0, 80, 8.0, 108), (520.0, 76, 6.0, 104),
    (526.0, 78, 1.0, 95), (527.0, 76, 1.0, 94), (528.0, 75, 8.0, 104),
    (536.0, 73, 6.0, 102), (542.0, 75, 1.0, 94), (543.0, 76, 1.0, 96),
    (544.0, 80, 8.0, 110), (552.0, 78, 6.0, 106), (558.0, 80, 1.0, 98),
    (559.0, 78, 1.0, 97), (560.0, 75, 4.0, 100), (564.0, 68, 4.0, 96),
]

SLURS = [(222.0, 224.0), (270.0, 272.0), (478.0, 480.0), (494.0, 496.0),
         (502.0, 504.0), (526.0, 528.0), (542.0, 544.0), (558.0, 560.0)]

SAW_B1 = [
    (152.0, 68, 4.0), (156.0, 71, 4.0), (160.0, 73, 4.0), (164.0, 75, 4.0),
    (168.0, 76, 4.0), (172.0, 78, 4.0), (176.0, 80, 6.0), (182.0, 78, 2.0),
    (184.0, 80, 4.0), (188.0, 82, 4.0), (192.0, 83, 8.0), (200.0, 80, 8.0),
]

SAW_B2 = [
    (384.0, 68, 4.0), (388.0, 71, 4.0), (392.0, 73, 4.0), (396.0, 75, 4.0),
    (400.0, 76, 4.0), (404.0, 78, 4.0), (408.0, 80, 4.0), (412.0, 82, 4.0),
    (416.0, 83, 4.0), (420.0, 82, 2.0), (422.0, 80, 2.0), (424.0, 83, 4.0),
    (428.0, 85, 4.0), (432.0, 87, 6.0), (438.0, 68, 2.0), (440.0, 80, 8.0),
]

# Full Burn counterpoint (saw vs lead), 16 cells of 4 beats from beat 480.
# Downbeat pitches chosen pairwise-consonant vs the lead and never doubling
# its pitch class; two approach eighths per cell steer toward the next cell.
SAW_CP_DOWN = [63, 71, 80, 73, 70, 75, 78, 82, 75, 71, 73, 68, 70, 66, 70, 78]
SAW_CP_APP = [(66, 68), (73, 76), (78, 75), (71, 68), (71, 73), (73, 76),
              (80, 83), (80, 78), (73, 70), (68, 70), (71, 70), (66, 68),
              (71, 68), (64, 68), (73, 76), (76, 78)]

SAW_CLIMAX = [
    (544.0, 80, 2.0, 92), (546.0, 82, 1.0, 90), (547.0, 83, 1.0, 92),
    (548.0, 87, 8.0, 96), (556.0, 83, 2.0, 92), (558.0, 82, 2.0, 90),
    (560.0, 80, 4.0, 92), (564.0, 75, 4.0, 88),
]

BELLS_NF = [(6.0, 80), (14.0, 75), (22.0, 71), (30.0, 80), (38.0, 73),
            (46.0, 75), (54.0, 80), (60.0, 87)]
BELLS_OUT = [(576.0, 87), (584.0, 83), (592.0, 80), (600.0, 75),
             (608.0, 71), (616.0, 68)]

# ---------------------------------------------------------------------------
# Builders — one per movement, note-ons strictly inside their windows
# ---------------------------------------------------------------------------


def _m1_night_field(sc):
    # whole-timeline CC lanes (authored once, here):
    en.cc_curve(sc, PAD, 74, [(0.0, 32), (64.0, 40), (136.0, 52), (208.0, 60),
                              (288.0, 38), (376.0, 34), (444.0, 96),
                              (448.0, 72), (568.0, 50), (628.0, 26)], step=0.5)
    en.vowel_curve(sc, CHO, [(0.0, 4), (64.0, 10), (136.0, 30), (208.0, 45),
                             (288.0, 45), (344.0, 80), (376.0, 55),
                             (448.0, 85), (568.0, 60), (604.0, 10),
                             (628.0, 4)], step=1.0)
    en.expr_curve(sc, CHO, [(0.0, 72), (136.0, 96), (208.0, 110),
                            (288.0, 100), (448.0, 124)], step=2.0)
    # the sleeping field
    _pads(sc, PAD, 0.0, [nm for _t, nm in GRID_NF], span=8.0, size=4,
          lo=48, hi=66, v0=38, v1=46)
    _pads(sc, CHO, 16.0, ["E", "Cs", "Fs"], span=16.0, size=3,
          lo=51, hi=68, v0=30, v1=36)
    for a, _b, nm in _slots(GRID_NF, IGN0):
        sc.note(BASS, R_BASS[nm], a, 2.5, 42 + int(a / 8), jt=0, jv=2)
    for t, p in BELLS_NF:
        sc.note(BEL, p, t, 0.4, 34 + int(t / 6), jt=0, jv=3)
    # runway lights blink on (transient blips only on ch0)
    t = 48.0
    while t < 64.0 - 1e-9:
        p = 56 if (int(round(t * 2)) % 2 == 0) else 68
        sc.note(A0, p, t, 0.2, int(round(en.lerp(28, 40, (t - 48) / 16))),
                jt=0, jv=2)
        t += 0.5


def _m2_ignition(sc):
    _bass_drive(sc, GRID_IGN, B1S, 62, 78)
    _wing_pedals(sc, [(72.0, "E"), (80.0, "Gs"), (88.0, "Fs"), (96.0, "Gs"),
                      (104.0, "E"), (112.0, "Cs"), (120.0, "Fs"),
                      (128.0, "Gs")], B1S, 64, 76)
    _lead_table(sc, LEAD_IGN)
    _arp8(sc, GRID_IGN, B1S, 44, 56)
    _pads(sc, PAD, IGN0, [nm for _t, nm in GRID_IGN], span=8.0, size=4,
          lo=50, hi=70, v0=48, v1=56)
    _pads(sc, CHO, IGN0, [nm for _t, nm in GRID_IGN], span=8.0, size=3,
          lo=53, hi=70, v0=38, v1=44)
    _pads(sc, STR, 96.0, ["Gs", "E", "Cs", "Fs", "Gs"], span=8.0, size=2,
          lo=55, hi=72, v0=40, v1=50)
    _slot_bells(sc, GRID_IGN, B1S, 44)
    for bar in _bars(IGN0, B1S):
        x = (bar - IGN0) / (B1S - IGN0)
        kv = int(round(en.lerp(72, 80, x)))
        sc.note(KIT, 36, bar, 0.25, kv, jt=0, jv=3)
        sc.note(KIT, 36, bar + 2.5, 0.25, kv - 8, jt=0, jv=3)
        sc.note(KIT, 37, bar + 2.0, 0.25, 52, jt=0, jv=3)
        for k in range(8):
            if k == 7 and bar >= 104.0:
                continue                      # room for the open hat
            hv = int(round(en.lerp(34, 44, x))) + (4 if k in (0, 4) else 0)
            sc.note(KIT, 42, bar + 0.5 * k, 0.15, hv, jt=0, jv=2)
        if bar >= 104.0:
            sc.note(KIT, 46, bar + 3.5, 0.4, 46, jt=0, jv=3)
    for i, bar in enumerate(b for b in _bars(IGN0, B1S)
                            if int(b - IGN0) % 16 == 0):
        _post_call(sc, PL, bar + 2.0, CALL_L, 62)
        if bar + 6.5 < B1S:
            _post_call(sc, PR, bar + 6.0, ANS_R, 58)
    _fills_in(sc, IGN0, B1S)


def _m3_burner_climb(sc):
    _bass_drive(sc, GRID_B1, D1S, 76, 94)
    _wing_chugs(sc, GRID_B1, D1S, 60, 82, six_from=204.0)
    for i, (t, p, dur) in enumerate(SAW_B1):
        sc.note(SAW, p, t, dur * 0.96,
                int(round(en.lerp(62, 86, i / (len(SAW_B1) - 1)))), jt=0, jv=2)
    _arp16(sc, GRID_B1, D1S, 52, 68)
    _pads(sc, PAD, B1S, [nm for _t, nm in GRID_B1], span=8.0, size=4,
          lo=50, hi=72, v0=56, v1=68)
    _pads(sc, CHO, B1S, [nm for _t, nm in GRID_B1], span=8.0, size=3,
          lo=53, hi=72, v0=48, v1=58)
    _pads(sc, STR, B1S, [nm for _t, nm in GRID_B1], span=8.0, size=2,
          lo=58, hi=74, v0=54, v1=66)
    _slot_bells(sc, GRID_B1, D1S, 52)
    for bar in _bars(B1S, 204.0):
        x = (bar - B1S) / (D1S - B1S)
        four = bar >= 168.0
        if four:
            for k in range(4):
                sc.note(KIT, 36, bar + k, 0.25,
                        int(round(en.lerp(88, 102, x))), jt=0, jv=2)
        else:
            sc.note(KIT, 36, bar, 0.25, 84, jt=0, jv=2)
            sc.note(KIT, 36, bar + 2.0, 0.25, 80, jt=0, jv=2)
        sv = int(round(en.lerp(70, 94, x)))
        sc.note(KIT, 38, bar + 1.0, 0.25, sv, jt=0, jv=2)
        sc.note(KIT, 38, bar + 3.0, 0.25, sv, jt=0, jv=2)
        if bar >= 184.0:
            for k in range(4):
                t = bar + k
                sc.note(KIT, 42, t, 0.15, 46, jt=0, jv=2)
                sc.note(KIT, 42, t + 0.25, 0.12,
                        int(round(en.lerp(32, 42, x))), jt=0, jv=2)
                sc.note(KIT, 42, t + 0.75, 0.12,
                        int(round(en.lerp(32, 42, x))), jt=0, jv=2)
                sc.note(KIT, 46, t + 0.5, 0.4, 52, jt=0, jv=2)
        else:
            for k in range(8):
                if k == 5:
                    continue
                sc.note(KIT, 42, bar + 0.5 * k, 0.15, 42, jt=0, jv=2)
            sc.note(KIT, 46, bar + 2.5, 0.4, 50, jt=0, jv=2)
    for k in range(4):
        sc.note(KIT, 36, 204.0 + k, 0.25, 104, jt=0, jv=2)
    _snare_roll(sc, 204.0, 208.0, 76, 112)
    bars = list(_bars(B1S, D1S))
    for i in range(0, len(bars), 2):
        side, seq, v = ((PL, CALL_L4, 66) if (i // 2) % 2 == 0
                        else (PR, ANS_R, 64))
        _post_call(sc, side, bars[i] + 2.5, seq, v)
    _fills_in(sc, B1S, D1S)
    _big_fill(sc, *BIG_FILLS[0])
    sc.note(RIS, 62, RISERS[0][0], RISERS[0][1], 92, jt=0, jv=0)


def _m4_first_pass(sc):
    sc.note(KIT, 49, D1S, 1.5, 106, jt=0, jv=0)
    for bar in _bars(D1S, SL0):
        for k in range(4):
            t = bar + k
            sc.note(KIT, 36, t, 0.25, 106, jt=0, jv=2)
            sc.note(KIT, 42, t, 0.15, 50, jt=0, jv=2)
            sc.note(KIT, 42, t + 0.25, 0.12, 40, jt=0, jv=2)
            sc.note(KIT, 46, t + 0.5, 0.4, 56, jt=0, jv=2)
            sc.note(KIT, 42, t + 0.75, 0.12, 40, jt=0, jv=2)
        for off in (1.0, 3.0):
            sc.note(KIT, 38, bar + off, 0.25, 98, jt=0, jv=2)
            sc.note(KIT, 39, bar + off, 0.25, 88, jt=0, jv=2)
        if bar in (240.0, 272.0):
            sc.note(KIT, 49, bar, 1.5, 94, jt=0, jv=0)
    for b in PYRO_D1:
        sc.note(HIT, PYRO_PITCH, b, 0.9, 100, jt=0, jv=0)
    _bass_drive(sc, GRID_D1, SL0, 94, 100, push=True)
    _wing_pedals(sc, GRID_D1, SL0, 78, 82)
    _lead_table(sc, LEAD_D1)
    for t0s, t1s, nm in _slots(GRID_D1, SL0):
        for bar in _bars(t0s, t1s):
            sc.note(SAW, ST1[nm], bar + 1.5, 0.45, 84, jt=0, jv=2)
    _arp16(sc, GRID_D1, SL0, 68, 72)
    _pads(sc, PAD, D1S, [nm for _t, nm in GRID_D1 for _ in (0, 1)],
          span=8.0, size=4, lo=52, hi=74, v0=64)
    _pads(sc, CHO, D1S, [nm for _t, nm in GRID_D1 for _ in (0, 1)],
          span=8.0, size=3, lo=56, hi=73, v0=56)
    _pads(sc, STR, D1S, [nm for _t, nm in GRID_D1 for _ in (0, 1)],
          span=8.0, size=2, lo=63, hi=79, v0=62)
    _slot_bells(sc, GRID_D1, SL0, 60)
    bars = list(_bars(D1S, SL0))
    for i in range(0, len(bars), 2):
        side, seq, v = ((PL, CALL_DESC, 72) if (i // 2) % 2 == 0
                        else (PR, ANS_R, 70))
        _post_call(sc, side, bars[i] + 2.75, seq, v)
    _fills_in(sc, D1S, SL0)


def _m5_searchlight(sc):
    # the pinned Three-Sixty-One quote, tick-exact from material's data
    for s in QUOTE_STARTS:
        for i, d in enumerate(material.ORBIT_RIFF_361):
            sc.note(BEL, en.pitch(QUOTE_ROOT, material.ORBIT_MODE_361, d),
                    s + i * material.ORBIT_STEP_361, 0.22, 58, jt=0, jv=0)
    # the searchlight itself: a transient glockenspiel arp under a slow autopan
    t = SL0
    while t < 371.5 + 1e-9:
        p = (68, 75, 80, 87)[int(round((t - SL0) * 2)) % 4]
        sc.note(A0, p, t, 0.2, 40, jt=0, jv=2)
        t += 0.5
    en.autopan(sc, A0, SL0, 84.0, lo=25, hi=103, period_beats=16.0, step=0.5)
    sc.cc(A0, 10, 64, 373.0)
    _pads(sc, PAD, SL0, [nm for _t, nm in GRID_SL], span=8.0, size=4,
          lo=50, hi=70, v0=48)
    _pads(sc, CHO, SL0, [nm for _t, nm in GRID_SL], span=8.0, size=3,
          lo=55, hi=74, v0=52)
    for a, _b, nm in _slots(GRID_SL, B2S):
        sc.note(BASS, R_BASS[nm], a, 1.8, 46, jt=0, jv=2)
        sc.note(BASS, R_BASS[nm], a + 4.0, 1.8, 42, jt=0, jv=2)
    for bar in _bars(SL0, B2S):
        sc.note(KIT, 36, bar, 0.25, 54, jt=0, jv=2)
        sc.note(KIT, 36, bar + 2.5, 0.25, 46, jt=0, jv=2)
        for k in range(8):
            sc.note(KIT, 42, bar + 0.5 * k, 0.12, 26, jt=0, jv=2)
        if int(bar - SL0) % 16 == 0:
            sc.note(KIT, 37, bar + 2.0, 0.2, 38, jt=0, jv=2)
    _fills_in(sc, SL0, B2S)


def _m6_second_climb(sc):
    _bass_drive(sc, GRID_B2, D2S, 80, 96)
    _wing_chugs(sc, GRID_B2, D2S, 64, 88, six_from=444.0)
    for i, (t, p, dur) in enumerate(SAW_B2):
        sc.note(SAW, p, t, dur * 0.96,
                int(round(en.lerp(64, 92, i / (len(SAW_B2) - 1)))), jt=0, jv=2)
    en.portamento_on(sc, SAW, 437.6, time_cc=58)
    en.portamento_off(sc, SAW, 447.8)
    _arp16(sc, GRID_B2, D2S, 58, 74)
    _pads(sc, PAD, B2S, [nm for _t, nm in GRID_B2], span=8.0, size=4,
          lo=52, hi=74, v0=60, v1=74)
    _pads(sc, CHO, B2S, [nm for _t, nm in GRID_B2], span=8.0, size=3,
          lo=55, hi=73, v0=56, v1=68)
    _pads(sc, STR, B2S, [nm for _t, nm in GRID_B2], span=8.0, size=2,
          lo=60, hi=78, v0=58, v1=72)
    _slot_bells(sc, GRID_B2, D2S, 56)
    for bar in _bars(B2S, 444.0):
        x = (bar - B2S) / (D2S - B2S)
        four = bar >= 400.0
        if four:
            for k in range(4):
                sc.note(KIT, 36, bar + k, 0.25,
                        int(round(en.lerp(92, 104, x))), jt=0, jv=2)
        else:
            sc.note(KIT, 36, bar, 0.25, 86, jt=0, jv=2)
            sc.note(KIT, 36, bar + 2.0, 0.25, 82, jt=0, jv=2)
        sv = int(round(en.lerp(72, 96, x)))
        sc.note(KIT, 38, bar + 1.0, 0.25, sv, jt=0, jv=2)
        sc.note(KIT, 38, bar + 3.0, 0.25, sv, jt=0, jv=2)
        if bar >= 416.0:
            for k in range(4):
                t = bar + k
                sc.note(KIT, 42, t, 0.15, 48, jt=0, jv=2)
                sc.note(KIT, 42, t + 0.25, 0.12,
                        int(round(en.lerp(34, 46, x))), jt=0, jv=2)
                sc.note(KIT, 42, t + 0.75, 0.12,
                        int(round(en.lerp(34, 46, x))), jt=0, jv=2)
                sc.note(KIT, 46, t + 0.5, 0.4, 54, jt=0, jv=2)
        else:
            for k in range(8):
                if k == 5:
                    continue
                sc.note(KIT, 42, bar + 0.5 * k, 0.15, 44, jt=0, jv=2)
            sc.note(KIT, 46, bar + 2.5, 0.4, 52, jt=0, jv=2)
    for k in range(4):
        sc.note(KIT, 36, 444.0 + k, 0.25, 106, jt=0, jv=2)
    _snare_roll(sc, 444.0, 448.0, 72, 112)
    bars = list(_bars(B2S, D2S))
    for i in range(0, len(bars), 2):
        side, seq, v = ((PL, CALL_L4, 68) if (i // 2) % 2 == 0
                        else (PR, ANS_R, 66))
        _post_call(sc, side, bars[i] + 2.5, seq, v)
    _fills_in(sc, B2S, D2S)
    _big_fill(sc, *BIG_FILLS[1])
    sc.note(RIS, 62, RISERS[1][0], RISERS[1][1], 104, jt=0, jv=0)


def _m7_full_burn(sc):
    for c, v in ((448.0, 108), (480.0, 96), (512.0, 96), (544.0, 96)):
        sc.note(KIT, 49, c, 1.5, v, jt=0, jv=0)
    for bar in _bars(D2S, OUT0):
        for k in range(4):
            t = bar + k
            sc.note(KIT, 36, t, 0.25, 110, jt=0, jv=2)
            sc.note(KIT, 42, t, 0.15, 50, jt=0, jv=2)
            sc.note(KIT, 42, t + 0.25, 0.12, 44, jt=0, jv=2)
            sc.note(KIT, 46, t + 0.5, 0.4, 58, jt=0, jv=2)
            sc.note(KIT, 42, t + 0.75, 0.12, 44, jt=0, jv=2)
        for off in (1.0, 3.0):
            sc.note(KIT, 38, bar + off, 0.25, 102, jt=0, jv=2)
            sc.note(KIT, 39, bar + off, 0.25, 90, jt=0, jv=2)
        if bar >= 512.0:
            for k in range(8):
                sc.note(KIT, 51, bar + 0.5 * k, 0.3, 46, jt=0, jv=2)
    sc.note(KIT, 49, 567.5, 2.0, 102, jt=0, jv=0)
    for b in PYRO_D2:
        v = 102 if abs(b % 4.0 - 1.5) < 1e-9 else 94
        sc.note(HIT, PYRO_PITCH, b, 0.9, v, jt=0, jv=0)
    _bass_drive(sc, GRID_D2, OUT0, 98, 104, push=True)
    _wing_pedals(sc, GRID_D2, OUT0, 80, 84)
    material.play_ascent(sc, LEAD, ASCENT_AT, ASCENT_ROOT,
                         vel=96, vel_end=110, jt=0, jv=0)
    _bloom(sc, LEAD, ASCENT_AT + 1.5, 2.5)
    _lead_table(sc, LEAD_D2)
    for t0, t1 in SLURS:
        _slur(sc, t0, t1)
    for t0s, t1s, nm in _slots(GRID_D2[:4], 480.0):
        for bar in _bars(t0s, t1s):
            sc.note(SAW, ST1[nm], bar + 1.5, 0.45, 86, jt=0, jv=2)
    for k in range(16):
        t = CP_SPAN[0] + 4.0 * k
        sc.note(SAW, SAW_CP_DOWN[k], t, 2.45, 88, jt=0, jv=2)
        a0p, a1p = SAW_CP_APP[k]
        sc.note(SAW, a0p, t + 2.5, 0.72, 78, jt=0, jv=2)
        sc.note(SAW, a1p, t + 3.25, 0.72, 80, jt=0, jv=2)
    for t, p, dur, v in SAW_CLIMAX:
        sc.note(SAW, p, t, dur * 0.97, v, jt=0, jv=2)
    _arp16(sc, GRID_D2[:8], 512.0, 74, 74)
    _arp16(sc, GRID_D2[8:], OUT0, 74, 76, lift=12)
    _pads(sc, PAD, D2S, [nm for _t, nm in GRID_D2], span=8.0, size=4,
          lo=52, hi=76, v0=72)
    _pads(sc, CHO, D2S, [nm for _t, nm in GRID_D2 for _ in (0, 1)],
          span=4.0, size=3, lo=56, hi=75, v0=70)
    _pads(sc, STR, D2S, [nm for _t, nm in GRID_D2 for _ in (0, 1)],
          span=4.0, size=2, lo=66, hi=82, v0=70)
    _slot_bells(sc, GRID_D2, OUT0, 66)
    for i, bar in enumerate(_bars(D2S, OUT0)):
        side, seq, v = ((PL, CALL_DESC, 76) if i % 2 == 0
                        else (PR, ANS_R, 72))
        _post_call(sc, side, bar + 2.75, seq, v)
    _fills_in(sc, D2S, OUT0)
    sc.note(RIS, 62, RISERS[2][0], RISERS[2][1], 88, jt=0, jv=0)


def _m8_afterglow(sc):
    en.expr_curve(sc, CHO, [(568.0, 124), (600.0, 92), (628.0, 44)], step=1.0)
    en.expr_curve(sc, PAD, [(568.0, 124), (632.0, 64)], step=1.0)
    _pads(sc, PAD, OUT0, ["Gs", "E"], span=16.0, size=4,
          lo=50, hi=70, v0=46, v1=42)
    _pads(sc, PAD, 600.0, ["Gs"], span=34.0, size=4, lo=48, hi=66, v0=36)
    _pads(sc, CHO, OUT0, ["Gs", "E"], span=16.0, size=3,
          lo=53, hi=70, v0=46, v1=40)
    _pads(sc, CHO, 600.0, ["Gs"], span=28.0, size=3, lo=51, hi=68, v0=34)
    _pads(sc, STR, OUT0, ["Gs", "E"], span=16.0, size=2,
          lo=55, hi=68, v0=40, v1=36)
    _pads(sc, STR, 600.0, ["Gs"], span=28.0, size=2, lo=55, hi=68, v0=30)
    t = OUT0
    while t < 616.0 - 1e-9:
        nm = "Gs" if not 584.0 <= t < 600.0 else "E"
        sc.note(BASS, R_BASS[nm], t, 2.2,
                int(round(en.lerp(42, 28, (t - OUT0) / 48.0))), jt=0, jv=2)
        t += 4.0
    for i, (t, p) in enumerate(BELLS_OUT):
        sc.note(BEL, p, t, 3.0,
                int(round(en.lerp(44, 28, i / (len(BELLS_OUT) - 1)))),
                jt=0, jv=2)
    sc.note(LEAD, 68, OUT0, 7.8, 62, jt=0, jv=2)
    _bloom(sc, LEAD, OUT0, 8.0)
    sc.note(HIT, PYRO_PITCH, PYRO_FINAL, 2.5, 60, jt=0, jv=0)


BUILDERS = [_m1_night_field, _m2_ignition, _m3_burner_climb, _m4_first_pass,
            _m5_searchlight, _m6_second_climb, _m7_full_burn, _m8_afterglow]

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 set, from the composer digest)
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


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, _p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _pitch_at(sc, ch, beat):
    """Pitch sounding at `beat` (a note starting exactly there counts)."""
    tt = _tick(beat)
    best = None
    for on, off, p in _note_spans(sc, ch):
        if on <= tt < off and (best is None or on >= best[0]):
            best = (on, p)
    return None if best is None else best[1]


# ---------------------------------------------------------------------------
# Track oracles
# ---------------------------------------------------------------------------


def _o_quote(sc):
    fails = []
    if len(QUOTE_STARTS) < 8:
        fails.append("fewer than 8 pinned searchlight statements")
    exp = set()
    for s in QUOTE_STARTS:
        for i, d in enumerate(material.ORBIT_RIFF_361):
            exp.add((_tick(s + i * material.ORBIT_STEP_361),
                     en.pitch(QUOTE_ROOT, material.ORBIT_MODE_361, d)))
    got = {(t, p) for t, p, _v in _note_ons(sc, BEL)
           if _tick(SL0) <= t < _tick(B2S)}
    missing = exp - got
    extra = got - exp
    if missing:
        fails.append(f"{len(missing)} orbit-quote notes missing or moved")
    if extra:
        fails.append(f"{len(extra)} stray ch{BEL} notes inside the "
                     f"searchlight (quote must be alone)")
    return fails


def _o_pyro(sc):
    fails = []
    sched = PYRO_D1 + PYRO_D2 + [PYRO_FINAL]
    for b in sched:
        if abs(b % 1.0 - 0.5) > 1e-9:
            fails.append(f"pyro beat {b} is not an off-beat (x.5)")
    exp = {_tick(b) for b in sched}
    got = {t for t, _p, _v in _note_ons(sc, HIT)}
    if exp - got:
        fails.append(f"{len(exp - got)} scheduled pyro hits missing")
    if got - exp:
        fails.append(f"{len(got - exp)} unscheduled orchestra hits")
    d1 = len(PYRO_D1) / (SL0 - D1S)
    d2 = len(PYRO_D2) / (OUT0 - D2S)
    if d2 < 2.0 * d1:
        fails.append(f"pyro density D2 {d2:.3f}/beat < 2x D1 {d1:.3f}/beat")
    return fails


def _o_duo(sc):
    fails = []
    wing = _note_spans(sc, WING)
    by_on = {}
    for on, off, p in wing:
        by_on.setdefault(on, []).append((off, p))
    for a, b in FORMATION_SPANS:
        bar = a
        while bar < b - 1e-9:
            grp = by_on.get(_tick(bar), [])
            if len(grp) != 2:
                fails.append(f"wing pedal at beat {bar}: "
                             f"{len(grp)} notes, want the dyad")
            else:
                ps = sorted(p for _off, p in grp)
                if ps[1] - ps[0] != 7:
                    fails.append(f"wing dyad at {bar} spans "
                                 f"{ps[1] - ps[0]} semis, want a P5")
                if ps[0] > PED_ROOT_CEIL:
                    fails.append(f"wing pedal root {ps[0]} at {bar} above "
                                 f"ceiling {PED_ROOT_CEIL}")
                for off, _p in grp:
                    if off - _tick(bar) < 3 * _PPQ - 4:
                        fails.append(f"wing pedal at {bar} rings "
                                     f"under 3 beats")
            bar += 4.0
        for on, _off, _p in wing:
            if _tick(a) <= on < _tick(b) and on % (4 * _PPQ) != 0:
                fails.append(f"wing note off the bar grid at tick {on} "
                             f"inside a formation span")
                break
    soars = 0
    for a, b in FORMATION_SPANS:
        for on, off, p in _note_spans(sc, LEAD):
            if not (_tick(a) <= on < _tick(b)):
                continue
            if p < LEAD_FLOOR:
                fails.append(f"lead pitch {p} under floor {LEAD_FLOOR} "
                             f"at tick {on}")
            if off - on >= SOAR_MIN * _PPQ - 24:
                soars += 1
                if p < SOAR_FLOOR:
                    fails.append(f"soar at tick {on} pitch {p} under "
                                 f"soar floor {SOAR_FLOOR}")
                lane = [(t, v) for t, v in _cc_lane(sc, LEAD, 1)
                        if on - 240 <= t <= off]
                if not lane or max(v for _t, v in lane) < 30:
                    fails.append(f"soar at tick {on}: no CC1 bloom peak")
                if not any(v <= 8 and t <= on + 240 for t, v in lane):
                    fails.append(f"soar at tick {on}: bloom must start low")
    if soars < 3:
        fails.append(f"only {soars} held soars >= {SOAR_MIN} beats, want 3+")
    return fails


def _o_dynrange(sc):
    fails = []
    sums = _bar_sums(sc)
    nbars = int(END // 4)
    wins = {s: sum(sums.get(bb, 0.0) for bb in range(s, s + 8))
            for s in range(0, nbars - 7)}
    smin = min(wins, key=lambda s: wins[s])
    smax = max(wins, key=lambda s: wins[s])
    if wins[smin] > 0.5 * wins[smax]:
        fails.append(f"quietest 32-beat window {wins[smin]:.0f} above half "
                     f"the peak {wins[smax]:.0f}")
    if not (D2S <= smax * 4 and (smax + 8) * 4 <= OUT0):
        fails.append(f"peak window starts at beat {smax * 4}, "
                     f"not inside Full Burn")
    d1 = _mean_barsum(sums, D1S, SL0)
    sl = _mean_barsum(sums, SL0, B2S)
    if sl >= 0.5 * d1:
        fails.append(f"searchlight mass {sl:.0f} not under half of "
                     f"First Pass {d1:.0f}")
    return fails


def _o_contour(sc):
    fails = []
    sums = _bar_sums(sc)
    for label, wins in (("Burner Climb", B1_WINDOWS),
                        ("Second Climb", B2_WINDOWS)):
        masses = [sum(sums.get(bb, 0.0)
                      for bb in range(int(a // 4), int(b // 4)))
                  for a, b in wins]
        if any(m1 <= m0 for m0, m1 in zip(masses, masses[1:])):
            fails.append(f"{label} window masses not strictly rising: "
                         f"{[int(m) for m in masses]}")
    d1 = _mean_barsum(sums, D1S, SL0)
    d2 = _mean_barsum(sums, D2S, OUT0)
    if d2 <= d1:
        fails.append(f"Full Burn per-bar mass {d2:.0f} not above "
                     f"First Pass {d1:.0f}")
    return fails


def _o_fills(sc):
    fails = []
    ons = sorted(_note_ons(sc, TOM) + _note_ons(sc, SYN))

    def count(lo, hi):
        return sum(1 for t, _p, _v in ons if _tick(lo) <= t < _tick(hi))

    for label, wins, span in (("Burner Climb", B1_WINDOWS, (B1S, D1S)),
                              ("Second Climb", B2_WINDOWS, (B2S, D2S))):
        counts = [count(a, b) for a, b in wins]
        if any(c1 <= c0 for c0, c1 in zip(counts, counts[1:])):
            fails.append(f"{label} fill counts not strictly rising: {counts}")
        shapes = {sh for b, sh, _v in FILL_SCHEDULE
                  if span[0] <= b < span[1]}
        if len(shapes) < 5:
            fails.append(f"{label} uses {len(shapes)} fill shapes, want 5+")
    for d in (D1S, D2S):
        window = [t for t, _p, _v in ons if _tick(d - 8) <= t < _tick(d)]
        best = run = 0
        last = end_tick = None
        for t in window:
            run = run + 1 if last is not None and t - last <= _PPQ // 2 else 1
            if run > best:
                best, end_tick = run, t
            last = t
        if best < 20 or end_tick is None or end_tick < _tick(d - 1.0):
            fails.append(f"no unbroken 20+-note fill landing on the drop "
                         f"at beat {d} (best run {best})")
    for d0, d1e in ((D1S, SL0), (D2S, OUT0)):
        w = d0
        while w < d1e:
            c = count(w, min(w + 16.0, d1e))
            if c > DROP_FILL_CAP:
                fails.append(f"drop window at {w} has {c} fill notes "
                             f"(cap {DROP_FILL_CAP}) — drops must thin")
            w += 16.0
    for b, sh, _v in FILL_SCHEDULE:
        first = material.FILL_LIB[sh]["tom" if "tom" in
                                      material.FILL_LIB[sh] else "syn"]
        if not any(t == _tick(b + first[0][0]) for t, _p, _vv in ons):
            fails.append(f"scheduled fill {sh} at {b} left no note")
    return fails


def _o_autopan(sc):
    fails = []
    for on, off, _p in _note_spans(sc, A0):
        if off - on > _PPQ // 2 + 8:
            fails.append(f"ch0 note at tick {on} not transient "
                         f"(the pan lane must stay transient)")
            break
    pan = _cc_lane(sc, A0, 10)
    for t, v in pan:
        if v != 64 and not (_tick(AUTOPAN_SPAN[0]) <= t
                            <= _tick(AUTOPAN_SPAN[1])):
            fails.append(f"ch0 pan {v} at tick {t} outside the "
                         f"searchlight span")
    sl_vals = [v for t, v in pan
               if _tick(AUTOPAN_SPAN[0]) <= t <= _tick(AUTOPAN_SPAN[1])]
    if not sl_vals or min(sl_vals) > 36 or max(sl_vals) < 94:
        fails.append("searchlight autopan must sweep wide (<=36 .. >=94)")
    if not pan or pan[-1][1] != 64:
        fails.append("ch0 pan must recentre to 64 after the searchlight")
    for ch, want in ((PL, 18), (PR, 110)):
        vals = [v for _t, v in _cc_lane(sc, ch, 10)]
        if vals != [want]:
            fails.append(f"post ch{ch} pan lane {vals}, want fixed [{want}]")
    return fails


def _o_counterpoint(sc):
    fails = []
    t0, t1 = CP_SPAN
    downs = [t0 + 4.0 * k for k in range(int((t1 - t0) // 4))]
    lead = [_pitch_at(sc, LEAD, d) for d in downs]
    saw = [_pitch_at(sc, SAW, d) for d in downs]
    if any(x is None for x in lead + saw):
        fails.append("a counterpoint line is silent on a structural downbeat")
        return fails
    bad = [(d, a, b) for d, a, b in zip(downs, lead, saw)
           if (a - b) % 12 not in _CONSONANT]
    if bad:
        fails.append(f"dissonant downbeats: {bad[:4]}")
    dbl = sum(1 for a, b in zip(lead, saw) if a % 12 == b % 12) / len(downs)
    if dbl > 0.25:
        fails.append(f"pitch-class doubling {dbl:.0%} above 25%")
    good = 0
    for k in range(1, len(downs)):
        dl = lead[k] - lead[k - 1]
        ds = saw[k] - saw[k - 1]
        if dl * ds < 0 or (dl == 0) != (ds == 0):
            good += 1
    if good / (len(downs) - 1) < 0.6:
        fails.append(f"contrary+oblique motion {good}/{len(downs) - 1} "
                     f"under 60%")
    lons = {t for t, _p, _v in _note_ons(sc, LEAD)
            if _tick(t0) <= t < _tick(t1)}
    sons = [t for t, _p, _v in _note_ons(sc, SAW)
            if _tick(t0) <= t < _tick(t1)]
    if not sons:
        fails.append("saw line empty in the counterpoint span")
    elif sum(1 for t in sons if t not in lons) / len(sons) < 0.5:
        fails.append("under 50% non-coincident onsets (lines not "
                     "rhythmically independent)")
    return fails


def _o_ascent(sc):
    fails = []
    spans = _note_spans(sc, LEAD)
    for on_b, du, semi in material.ASCENT_CELL:
        t = _tick(ASCENT_AT + on_b)
        p = ASCENT_ROOT + semi
        m = [s for s in spans if s[0] == t and s[2] == p]
        if not m:
            fails.append(f"ASCENT note {p} at beat {ASCENT_AT + on_b} "
                         f"missing or moved")
        elif du >= 2.0 and m[0][1] - m[0][0] < 2 * _PPQ - 24:
            fails.append("the ASCENT hang must be held")
    return fails


def _o_sweeps(sc):
    fails = []
    vals = [v for t, v in _cc_lane(sc, PAD, 74)
            if _tick(SWEEP_SPAN[0]) <= t <= _tick(SWEEP_SPAN[1])]
    if not vals or max(vals) < 90 or max(vals) - min(vals) < 60:
        fails.append("CC74 macro-sweep must cover >= 60 units to >= 90")
    if any(b < a for a, b in zip(vals, vals[1:])):
        fails.append("CC74 macro-sweep must rise monotonically")
    rs = _note_spans(sc, RIS)
    if len(rs) != len(RISERS):
        fails.append(f"{len(rs)} riser notes, want {len(RISERS)}")
    for beat, dur in RISERS:
        m = [s for s in rs if s[0] == _tick(beat)]
        if not m or m[0][1] < _tick(beat + dur) - 8:
            fails.append(f"riser at {beat} missing or cut short")
    for d in (D1S, D2S):
        if not any(_tick(d - 8) <= on < _tick(d) for on, _off, _p in rs):
            fails.append(f"no riser into the drop at {d}")
    c65 = _cc_lane(sc, SAW, 65)
    if not any(v >= 64 and _tick(436.0) <= t <= _tick(440.0) for t, v in c65):
        fails.append("portamento switch not armed before the swoop")
    if not any(v == 0 and t >= _tick(446.0) for t, v in c65):
        fails.append("portamento never released after the swoop")
    ons5 = {(t, p) for t, p, _v in _note_ons(sc, SAW)}
    (b0, p0), (b1, p1) = SWOOP_PAIR
    if (_tick(b0), p0) not in ons5 or (_tick(b1), p1) not in ons5:
        fails.append("the pinned 12-semitone swoop pair moved")
    return fails


def _o_layers(sc):
    fails = []

    def chans(lo, hi):
        return {ch for ch in sc.events
                if any(_tick(lo) <= t < _tick(hi)
                       for t, _p, _v in _note_ons(sc, ch))}

    d2 = chans(D2S, OUT0)
    nf = chans(NF0, IGN0)
    if len(d2) < 15:
        fails.append(f"Full Burn plays {len(d2)} channels, want 15+")
    if len(nf) > 6:
        fails.append(f"Night Field plays {len(nf)} channels — too busy "
                     f"for the hush")
    return fails


def oracles(sc, info, spans):
    return [
        ("searchlight_orbit_quote", _o_quote(sc)),
        ("pyro_schedule", _o_pyro(sc)),
        ("duo_soar_over_pedal", _o_duo(sc)),
        ("night_dynamic_range", _o_dynrange(sc)),
        ("build_drop_contour", _o_contour(sc)),
        ("fill_escalation", _o_fills(sc)),
        ("autopan_transient_only", _o_autopan(sc)),
        ("drop2_counterpoint", _o_counterpoint(sc)),
        ("ascent_statement", _o_ascent(sc)),
        ("soar_sweep_risers", _o_sweeps(sc)),
        ("night_layers", _o_layers(sc)),
    ]

