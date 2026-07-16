"""T1 — Wheels Up (the opener).  HLD §4/T1.

The field wakes: radio chatter taps WHEELS UP in Morse on a woodblock, the
engines turn over in low bass swells, THE DUO states the ASCENT cell as the
very first pitched notes of the album (before any drum), taxis in on muted
octave chugs, and flies the first full pass of the day.  E aeolian, 132 bpm.

Architecture (144 bars):
  I.    Contact        0-48    radio Morse + engine start + pinned duo ASCENT
  II.   Taxi          48-112   ostinato in, duo octave chugs
  III.  Throttle Up  112-176   BUILD1: four-floor, fills escalate, saw sweeps in
  IV.   First Pass   176-256   DROP1: the hook in duo octaves
  V.    Coast        256-288   STRIP: texture down to bass + duo (+ hat tick)
  VI.   Climb Out    288-368   BUILD2: denser fills, the two-bar ORBIT wink
  VII.  Full Power   368-496   DROP2 (> DROP1): hook + wing counterpoint +
                               saw counter + choir; lead soars
  VIII. Throttle Back 496-576  wind-down; final ASCENT, solo lead ship

Duo formation — OCTAVES: through beat 368 the wing ship (ch15, GM30) doubles
the lead ship (ch14, GM29 bank1) exactly one octave down, tick-for-tick
(oracle-pinned).  In DROP2 the wing breaks formation into free counterpoint
(counterpoint oracle applies against the lead hook).
"""

from __future__ import annotations

import bisect

import conductor
import engine as en
import material

NUMBER = 1
TITLE = "Wheels Up"
FILE = "01 - Wheels Up.mid"
SEED = 20261101
COMMENT = ("Wheels Up - the Slipstream opener. Radio chatter taps WHEELS UP "
           "in Morse, engines turn over, and the two-guitar display team "
           "states the album's ASCENT cell before a single drum sounds, then "
           "flies the whole first pass in strict octaves before the wing "
           "ship breaks into free counterpoint at full power. E aeolian, "
           "132 bpm, build-drop-build with the second drop verified bigger.")

MODE = "aeolian"

# -- the grid (beats) --------------------------------------------------------
INTRO0, TAXI0, B10, D10 = 0.0, 48.0, 112.0, 176.0
STRIP0, B20, D20, OUT0, END = 256.0, 288.0, 368.0, 496.0, 576.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Contact", INTRO0, TAXI0),
        ("II. Taxi", TAXI0, B10),
        ("III. Throttle Up", B10, D10),
        ("IV. First Pass", D10, STRIP0),
        ("V. Coast", STRIP0, B20),
        ("VI. Climb Out", B20, D20),
        ("VII. Full Power", D20, OUT0),
        ("VIII. Throttle Back", OUT0, END),
    ],
    tempo_map=[(0.0, 132.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1)],                      # E minor
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (0, "crystal ostinato", 98, 92, 64, 50),
        (1, "warm pad", 89, 96, 64, 70),
        (2, "synth bass", 38, 112, 64, 30),
        (3, "post L", 80, 88, 18, 45),
        (4, "post R", 80, 88, 110, 45),
        (5, "saw soar", 81, 100, 64, 60),
        (6, "steel color", 114, 90, 64, 50),
        (7, "aerial strings", 49, 84, 64, 70),
        (8, "choir", 52, 92, 64, 74),
        (9, "kit", 0, 110, 64, 40),
        (10, "melodic toms", 117, 104, 64, 45),
        (11, "synth drum", 118, 100, 64, 45),
        (12, "orchestra hit", 55, 100, 64, 55),
        (13, "riser", 119, 100, 64, 70),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 30, 108, 64, 24),
    ],
    program_changes=[(9, 0.0, 1)],              # the V3 kit
    extra_markers=[(6.0, "radio check: WHEELS UP"),
                   (320.0, "orbit wink"),
                   (552.0, "final ascent - solo lead")],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1)],
)

# -- verification config -----------------------------------------------------
PROGRAM_WHITELIST = {29, 30, 38, 49, 52, 55, 80, 81, 89, 98, 114, 117, 118, 119}
CENTERED_CHANNELS = {0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (58, 84), 1: (50, 78), 2: (36, 64), 3: (70, 92), 4: (70, 92),
    5: (60, 92), 6: (60, 88), 7: (52, 84), 8: (52, 80), 9: (35, 81),
    10: (44, 64), 11: (46, 60), 12: (60, 78), 13: (60, 68),
    14: (46, 90), 15: (34, 74),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (257.0, 268.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# -- harmonic grid: (start_beat, aeolian degree); 1=Em 6=C 3=G 7=D ----------
_GRID: list[tuple[float, int]] = (
    [(0.0, 1), (48.0, 1), (80.0, 6), (96.0, 7),
     (112.0, 1), (128.0, 6), (144.0, 3), (160.0, 7)]
    + [(b + o, d) for b in (176.0, 192.0, 208.0, 224.0, 240.0)
       for o, d in ((0.0, 1), (4.0, 6), (8.0, 3), (12.0, 7))]
    + [(256.0, 1), (272.0, 6), (280.0, 7),
       (288.0, 1), (304.0, 6), (320.0, 3), (336.0, 7), (352.0, 1)]
    + [(b + o, d) for b in [368.0 + 16.0 * k for k in range(8)]
       for o, d in ((0.0, 1), (4.0, 6), (8.0, 3), (12.0, 7))]
    + [(496.0, 1), (504.0, 7), (512.0, 6), (520.0, 1),
       (528.0, 6), (536.0, 7), (544.0, 1)]
)
_GRID_BEATS = [b for b, _d in _GRID]

_DEG_ROOT_SEMIS = {1: 0, 3: 3, 6: 8, 7: 10}


def _deg_at(beat: float) -> int:
    i = bisect.bisect_right(_GRID_BEATS, beat + 1e-9) - 1
    return _GRID[max(0, i)][1]


def _root(deg: int, lo: int) -> int:
    """Lowest chord-root pitch >= lo (roots from E1=28 upward)."""
    p = 28 + _DEG_ROOT_SEMIS[deg]
    while p < lo:
        p += 12
    return p


def _third(deg: int) -> int:
    tri = en.triad(52, MODE, deg)
    return tri[1] - tri[0]


# -- THE HOOK (lead ship, one 16-beat statement over Em C G D) ---------------
HOOK: list[tuple[float, int, float, int]] = [
    (0.0, 76, 0.75, 104), (0.75, 74, 0.25, 92), (1.0, 76, 0.5, 98),
    (1.5, 79, 1.0, 106), (2.5, 76, 0.5, 96), (3.0, 74, 0.5, 96),
    (3.5, 71, 0.5, 94),
    (4.0, 72, 0.75, 102), (4.75, 71, 0.25, 90), (5.0, 72, 0.5, 96),
    (5.5, 76, 1.0, 104), (6.5, 79, 0.75, 100), (7.25, 76, 0.75, 96),
    (8.0, 74, 0.75, 104), (8.75, 71, 0.25, 92), (9.0, 74, 0.5, 96),
    (9.5, 79, 1.5, 106), (11.0, 83, 1.0, 108),
    (12.0, 81, 0.75, 104), (12.75, 79, 0.25, 92), (13.0, 78, 0.5, 98),
    (13.5, 76, 1.0, 100), (14.5, 74, 0.5, 94), (15.0, 71, 1.0, 96),
]
HOOK_STARTS = (176.0, 192.0, 208.0, 224.0, 368.0, 384.0, 400.0, 416.0,
               464.0, 480.0)

# DROP1 tag (beats 240-256): three blooming holds then the run-down.
TAG: list[tuple[float, int, float, int]] = [
    (0.0, 76, 3.5, 104), (4.0, 79, 3.5, 106), (8.0, 83, 3.5, 108),
    (12.0, 83, 0.5, 102), (12.5, 81, 0.5, 100), (13.0, 79, 0.5, 98),
    (13.5, 76, 0.5, 96), (14.0, 74, 0.5, 94), (14.5, 71, 0.5, 92),
    (15.0, 67, 0.5, 90), (15.5, 64, 0.5, 88),
]

# DROP2 wing counterpoint (one 16-beat statement; designed contrary/oblique
# against HOOK, chord tones on every bar downbeat, low pc-doubling).
WING_CTR: list[tuple[float, int, float, int]] = [
    (0.0, 52, 1.75, 84), (2.25, 57, 1.25, 80), (3.75, 60, 2.25, 84),
    (6.0, 59, 1.75, 80), (8.0, 59, 2.0, 84), (10.5, 57, 1.25, 80),
    (12.0, 54, 1.5, 84), (13.75, 57, 1.0, 80), (14.75, 59, 1.2, 82),
]

# DROP2 saw counter-line (never sounding on a bar downbeat by design).
SAW_CTR: list[tuple[float, int, float, int]] = [
    (1.0, 83, 2.75, 92), (4.5, 79, 3.25, 90), (9.5, 83, 2.25, 92),
    (12.5, 81, 3.25, 94),
]

# DROP2 soar section (lead ship, absolute beats 432-464).
SOAR: list[tuple[float, int, float, int]] = [
    (432.0, 88, 8.0, 106), (440.5, 86, 1.5, 100), (442.0, 83, 1.5, 98),
    (443.5, 81, 0.5, 96), (444.0, 79, 4.0, 102),
    (448.0, 83, 6.0, 106), (454.0, 81, 1.0, 96), (455.0, 79, 0.5, 94),
    (455.5, 78, 0.5, 94),
    (456.0, 76, 0.75, 100), (456.75, 79, 0.25, 96), (457.0, 81, 1.0, 102),
    (458.0, 83, 1.5, 104), (459.5, 86, 0.5, 100), (460.0, 88, 4.0, 108),
]

# OUTRO lead echoes (before the pinned solo ascent at 552).
LEAD_OUT: list[tuple[float, int, float, int]] = [
    (500.0, 76, 2.0, 80), (508.0, 74, 2.0, 74), (516.0, 71, 2.0, 70),
    (524.0, 67, 2.5, 64), (532.0, 64, 3.0, 60), (540.0, 59, 3.5, 56),
]

# Pinned ASCENT statements: (t0, lead_root, stretch, duo?).  The 0.0 one is
# the album's very first pitched sound; 552.0 is the solo lead sign-off.
ASCENT_PINS: list[tuple[float, int, float, bool]] = [
    (0.0, 52, 1.0, True), (24.0, 52, 1.0, True), (40.0, 64, 1.0, True),
    (356.0, 52, 1.0, True), (360.0, 64, 1.0, True),
    (552.0, 52, 2.0, False),
]

# Radio Morse lane: two pinned WHEELS UP statements (woodblock 76, unit 1/4).
MORSE_T0S = (6.0, 556.0)

# The T361 wink: exactly two bars (4 riff statements) on the steel channel.
ORBIT_T0, ORBIT_STATEMENTS, ORBIT_BASE = 320.0, 4, 64

# Fill schedule: (beat, shape, velocity bump).  Window counts verified.
FILL_SCHEDULE: list[tuple[float, str, int]] = [
    # taxi
    (79.0, "A", 0), (95.0, "D", 0), (110.0, "B", 0),
    # BUILD1 window 1 (112-144) = 28 notes
    (119.0, "A", 0), (127.0, "C", 0), (135.0, "D", 4), (141.0, "B", 4),
    # BUILD1 window 2 (144-176) = 45 notes, ending in the 20-note chain
    (151.0, "F", 4), (159.0, "G", 6), (167.0, "H", 6),
    (171.5, "E", 8), (174.75, "G", 10),
    # DROP1 punctuation (thinned)
    (199.0, "A", 0), (223.0, "D", 0), (239.0, "A", 0),
    # BUILD2 window 1 (288-308) = 20
    (295.0, "A", 0), (303.0, "D", 2), (305.0, "C", 2),
    # BUILD2 window 2 (308-328) = 25
    (311.0, "B", 2), (315.0, "F", 4), (317.5, "C", 4),
    # BUILD2 window 3 (328-348) = 36
    (331.0, "G", 4), (335.0, "H", 4), (339.0, "B", 6), (343.0, "E", 6),
    # BUILD2 window 4 (348-368) = 53, ending in the 28-note chain
    (351.0, "F", 6), (355.0, "D", 6), (359.0, "C", 8),
    (362.0, "E", 10), (365.0, "H", 10), (366.5, "G", 12),
    # DROP2 punctuation (thinned)
    (375.0, "A", 0), (383.0, "D", 0), (399.0, "A", 0), (415.0, "D", 0),
    (430.5, "G", 0), (447.0, "A", 0), (462.5, "G", 0), (479.0, "D", 0),
    (492.5, "E", 6),
    # outro echoes
    (503.0, "A", -10), (519.0, "G", -10), (535.0, "A", -12),
]

RISERS: list[tuple[float, float, int, int]] = [
    # (beat, dur, vel, pitch)
    (40.0, 8.0, 70, 62), (104.0, 8.0, 84, 62), (168.0, 8.0, 92, 62),
    (280.0, 8.0, 80, 62), (360.0, 8.0, 102, 62), (364.0, 4.0, 96, 66),
    (380.0, 4.0, 72, 66), (492.0, 4.0, 88, 62),
]


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def _bloom(sc, ch, on, dur, peak=None):
    """CC1 bloom over a held note (the T361 lead-voice gesture)."""
    if peak is None:
        peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _duo_note(sc, p, t, dur, vel, wv=None):
    """Lead ship + wing ship one octave down, tick-for-tick (the formation)."""
    sc.note(14, p, t, dur, vel, jt=0, jv=0)
    sc.note(15, p - 12, t, dur, wv if wv is not None else max(1, vel - 8),
            jt=0, jv=0)


def _duo_chugs(sc, t0, t1, offs, vel, acc=(0.0, 2.25), lo=48):
    b = t0
    while b < t1 - 1e-9:
        r = _root(_deg_at(b), lo)
        for o in offs:
            _duo_note(sc, r, b + o, 0.22, vel + (8 if o in acc else 0))
        b += 4.0


def _duo_riff(sc, t0, t1, vel, lo=48, push=False):
    b = t0
    while b < t1 - 1e-9:
        deg = _deg_at(b)
        r, t3 = _root(deg, lo), _third(deg)
        pat = [(0.0, 0), (0.5, 0), (0.75, 7), (1.5, 0), (2.0, t3),
               (2.5, 7), (3.0, 0), (3.5, 7)]
        for o, s in pat:
            _duo_note(sc, r + s, b + o, 0.22,
                      vel + (6 if o in (0.0, 2.0) else 0))
        if push:
            _duo_note(sc, r + 12, b + 3.75, 0.2, vel)
        b += 4.0


def _hook(sc, st, vbump=0, wing=True):
    for o, p, d, v in HOOK:
        vv = min(120, v + vbump)
        if wing:
            _duo_note(sc, p, st + o, d, vv)
        else:
            sc.note(14, p, st + o, d, vv, jt=0, jv=0)
    for a in (0.7, 4.7, 8.7):                   # hammer-on brackets
        sc.cc(14, 68, 90, st + a)
        sc.cc(14, 68, 0, st + a + 0.7)
    en.cc_curve(sc, 14, 1, [(st + 9.5, 0), (st + 10.3, 46), (st + 10.9, 0)],
                step=0.25)


def _kit_four(sc, t0, t1, kick=98, hat=56, oh=46, back=("clap", 92),
              hat16=0, crash_every=0, crash_vel=102, ride=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        if crash_every and b % crash_every == 0:
            sc.note(9, 49, bar, 0.4, crash_vel, jt=0, jv=3)
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.22, kick, jt=0, jv=3)
            sc.note(9, 42, t, 0.16, hat, jt=0, jv=3)
            sc.note(9, 46, t + 0.5, 0.3, max(1, hat - 10), jt=0, jv=3)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.12, hat16, jt=0, jv=3)
                sc.note(9, 42, t + 0.75, 0.12, hat16, jt=0, jv=3)
            if ride:
                sc.note(9, 51, t, 0.2, ride, jt=0, jv=3)
                sc.note(9, 51, t + 0.5, 0.2, max(1, ride - 6), jt=0, jv=3)
        for bt in (1.0, 3.0):
            sc.note(9, 39, bar + bt, 0.25, back[1], jt=0, jv=3)
            if back[0] == "both":
                sc.note(9, 38, bar + bt, 0.25, max(1, back[1] - 6),
                        jt=0, jv=3)


def _kit_taxi(sc, t0, t1, kick=86, stick=68, hat=50):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        sc.note(9, 36, bar, 0.22, kick, jt=0, jv=3)
        sc.note(9, 36, bar + 2.5, 0.22, kick - 6, jt=0, jv=3)
        for bt in (1.0, 3.0):
            sc.note(9, 37, bar + bt, 0.2, stick, jt=0, jv=3)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.14,
                    hat + (6 if k % 2 == 0 else 0), jt=0, jv=3)
        if b % 4 == 3:
            sc.note(9, 46, bar + 3.5, 0.3, 48, jt=0, jv=3)


def _bass_eighths(sc, t0, t1, vel, vel_end=None, pop=False, push16=False):
    b = t0
    while b < t1 - 1e-9:
        r = _root(_deg_at(b), 38)
        v = vel if vel_end is None else en.lerp(vel, vel_end,
                                                (b - t0) / (t1 - t0))
        for i in range(8):
            p = r + (12 if pop and i % 4 == 2 else 0)
            sc.note(2, p, b + 0.5 * i, 0.4, int(v) + (4 if i == 0 else 0),
                    jt=0, jv=3)
        if push16:
            sc.note(2, r, b + 3.75, 0.2, int(v), jt=0, jv=3)
        b += 4.0


def _bass_halves(sc, t0, t1, vel, vel_end=None):
    b = t0
    while b < t1 - 1e-9:
        r = _root(_deg_at(b), 38)
        v = vel if vel_end is None else en.lerp(vel, vel_end,
                                                (b - t0) / (t1 - t0))
        sc.note(2, r, b, 1.9, int(v), jt=0, jv=3)
        sc.note(2, r, b + 2.0, 1.9, max(1, int(v) - 6), jt=0, jv=3)
        b += 4.0


def _ost16(sc, t0, t1, v0, v1, accent=8):
    b = t0
    while b < t1 - 1e-9:
        deg = _deg_at(b)
        r, t3 = _root(deg, 60), _third(deg)
        v = en.lerp(v0, v1, (b - t0) / max(1e-9, t1 - t0))
        for i, s in enumerate((0, 7, 12, t3 + 12)):
            sc.note(0, r + s, b + 0.25 * i, 0.22,
                    int(v) + (accent if i == 0 else 0), jt=0, jv=2)
        b += 1.0


def _ost8(sc, t0, t1, v0, v1):
    b = t0
    while b < t1 - 1e-9:
        r = _root(_deg_at(b), 60)
        v = en.lerp(v0, v1, (b - t0) / max(1e-9, t1 - t0))
        sc.note(0, r + 12, b, 0.45, int(v), jt=0, jv=2)
        sc.note(0, r + 7, b + 0.5, 0.45, max(1, int(v) - 6), jt=0, jv=2)
        b += 1.0


def _steel_off(sc, t0, t1, vel, skip=()):
    b = t0
    k = 0
    while b < t1 - 1e-9:
        tt = b + 0.5
        if not any(lo <= tt < hi for lo, hi in skip):
            r = _root(_deg_at(b), 72)
            sc.note(6, r if k % 2 == 0 else r + 7, tt, 0.2, vel, jt=0, jv=3)
        k += 1
        b += 1.0


def _orbit_riff(sc):
    """The T361 wink: 4 pinned statements of ORBIT_RIFF_361 (2 bars)."""
    pitches = [en.pitch(ORBIT_BASE, material.ORBIT_MODE_361, d)
               for d in material.ORBIT_RIFF_361]
    for s in range(ORBIT_STATEMENTS):
        st = ORBIT_T0 + 2.0 * s
        for i, p in enumerate(pitches):
            sc.note(6, p, st + i * material.ORBIT_STEP_361, 0.22,
                    84 + (6 if i == 0 else 0), jt=0, jv=0)


def _post(sc, ch, t, up=True, vel=88):
    r = _root(_deg_at(t), 72)
    ps = (r, r + 7, r + 12) if up else (r + 12, r + 7, r)
    for i, p in enumerate(ps):
        sc.note(ch, p, t + 0.25 * i, 0.2, max(1, vel - 4 * i), jt=0, jv=2)


def _hit(sc, t, vel):
    sc.note(12, _root(_deg_at(t), 64), t, 0.9, vel, jt=0, jv=2)


def _riser_window(sc, t0, t1):
    for t, dur, vel, p in RISERS:
        if t0 <= t < t1:
            sc.note(13, p, t, dur, vel, jt=0, jv=0)


def _fills(sc, t0, t1):
    for t, shape, vb in FILL_SCHEDULE:
        if t0 <= t < t1:
            material.play_fill(sc, shape, t, vbump=vb)


def _morse(sc, t0):
    for on, dur in material.morse_rhythm(material.MORSE_T1, 0.25):
        sc.note(9, 76, t0 + on, dur * 0.8, 62 if dur > 0.3 else 54,
                jt=0, jv=0)


def _pads(sc, t0, t1, span, vel, vel_end=None, lo=52, hi=76, size=4):
    n = int(round((t1 - t0) / span))
    chords = [en.triad(52, MODE, _deg_at(t0 + span * i)) for i in range(n)]
    en.pad_block(sc, 1, t0, chords, span=span, size=size, lo=lo, hi=hi,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _choir_block(sc, t0, t1, span, vel, vel_end=None):
    n = int(round((t1 - t0) / span))
    chords = [en.triad(52, MODE, _deg_at(t0 + span * i)) for i in range(n)]
    en.pad_block(sc, 8, t0, chords, span=span, size=3, lo=55, hi=79,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _ascent_duo(sc, t0, root, stretch=1.0, vel=96):
    material.play_ascent(sc, 14, t0, root, stretch=stretch, vel=vel,
                         vel_end=vel + 12, jt=0, jv=0)
    material.play_ascent(sc, 15, t0, root - 12, stretch=stretch, vel=vel - 8,
                         vel_end=vel + 4, jt=0, jv=0)
    _bloom(sc, 14, t0 + 1.5 * stretch, 2.5 * stretch, peak=52)


def _wing_pump(sc, t0, t1, vel):
    b = t0
    while b < t1 - 1e-9:
        r = _root(_deg_at(b), 48) - 12
        for i in range(8):
            sc.note(15, r, b + 0.5 * i, 0.4, vel + (6 if i in (0, 4) else 0),
                    jt=0, jv=2)
        b += 4.0


# ---------------------------------------------------------------------------
# Builders (one per movement; note-ons stay inside each window)
# ---------------------------------------------------------------------------

def _b_contact(sc):
    # whole-timeline pad CC choreography (authored once, here)
    en.cc_curve(sc, 1, 74, [(0.0, 30), (48.0, 42), (112.0, 50), (176.0, 72),
                            (252.0, 72), (256.0, 38), (288.0, 40),
                            (368.0, 104), (432.0, 92), (496.0, 64),
                            (574.0, 30)], step=1.0)
    en.expr_curve(sc, 1, [(0.0, 80), (48.0, 88), (112.0, 96), (176.0, 110),
                          (256.0, 70), (288.0, 92), (368.0, 118),
                          (496.0, 96), (560.0, 72), (575.0, 52)], step=2.0)
    # the pinned duo ASCENT statements - the album's first pitched notes
    for t0, root, st, duo in ASCENT_PINS:
        if INTRO0 <= t0 < TAXI0:
            _ascent_duo(sc, t0, root, st, vel=96)
    # engine start: low bass swells with CC11 breathing
    for t, dur in ((2.0, 6.5), (10.0, 6.5), (18.0, 6.5), (26.0, 5.5)):
        sc.note(2, 40, t, dur, 62, jt=0, jv=2)
    en.expr_curve(sc, 2, [(0.0, 55), (2.0, 50), (5.0, 90), (8.5, 55),
                          (10.0, 50), (13.0, 92), (16.5, 56), (18.0, 52),
                          (21.0, 94), (24.5, 58), (26.0, 54), (29.0, 96),
                          (32.0, 84), (40.0, 96), (48.0, 108)], step=1.0)
    for i in range(16):                          # idle rumble quarters
        sc.note(2, 40, 32.0 + i, 0.85, int(en.lerp(60, 74, i / 15)),
                jt=0, jv=2)
    # radio chatter: pinned Morse statement
    _morse(sc, MORSE_T0S[0])
    # warm pad stack building under the radio
    for t, p, v in ((4.0, 52, 40), (8.0, 59, 44), (12.0, 64, 48),
                    (16.0, 67, 50)):
        sc.note(1, p, t, 47.75 - t, v, jt=0, jv=2)
    # faint choir hum
    for t, p, v in ((32.0, 64, 40), (36.0, 71, 42), (40.0, 67, 44)):
        sc.note(8, p, t, 47.75 - t, v, jt=0, jv=2)
    en.vowel_curve(sc, 8, [(32.0, 0), (46.0, 25)])
    # radio blips answering the Morse (antiphonal posts)
    for t, ch, up, v in ((12.0, 3, True, 58), (14.0, 4, False, 56),
                         (20.0, 3, True, 62), (22.0, 4, False, 60),
                         (28.0, 3, True, 66), (30.0, 4, False, 64),
                         (36.0, 3, True, 70), (38.0, 4, False, 68)):
        _post(sc, ch, t, up=up, vel=v)
    # heartbeat kick as the engines catch
    for i in range(16):
        sc.note(9, 36, 32.0 + i, 0.22, int(en.lerp(46, 62, i / 15)),
                jt=0, jv=2)
    for k in range(16):
        sc.note(9, 42, 40.0 + 0.5 * k, 0.14, 36, jt=0, jv=2)
    _riser_window(sc, INTRO0, TAXI0)


def _b_taxi(sc):
    _duo_chugs(sc, TAXI0, B10, (0.0, 0.5, 1.0, 1.75, 2.25, 3.0, 3.5),
               vel=70, lo=48)
    _kit_taxi(sc, TAXI0, B10)
    _bass_eighths(sc, TAXI0, B10, 74, vel_end=82)
    _ost16(sc, TAXI0, B10, 56, 66)
    _steel_off(sc, 80.0, B10, 52)
    for t, p, d, v in ((96.0, 69, 8.0, 54), (104.0, 71, 8.0, 58)):
        sc.note(7, p, t, d, v, jt=0, jv=2)
    for t, ch, up, v in ((56.0, 3, True, 70), (58.0, 4, False, 68),
                         (72.0, 3, True, 74), (74.0, 4, False, 72),
                         (88.0, 3, True, 78), (90.0, 4, False, 76),
                         (104.0, 3, True, 82), (106.0, 4, False, 80)):
        _post(sc, ch, t, up=up, vel=v)
    _pads(sc, TAXI0, B10, 8.0, 52)
    _fills(sc, TAXI0, B10)
    _riser_window(sc, TAXI0, B10)


def _b_build1(sc):
    _duo_riff(sc, B10, 144.0, 76, lo=48)
    _duo_riff(sc, 144.0, D10, 84, lo=48)
    _kit_four(sc, B10, 144.0, kick=94, hat=54, oh=44, back=("clap", 88),
              crash_every=8)
    _kit_four(sc, 144.0, D10, kick=100, hat=58, oh=46, back=("clap", 92),
              hat16=40, crash_every=8)
    _bass_eighths(sc, B10, D10, 86, vel_end=96, pop=True)
    _ost16(sc, B10, D10, 62, 78)
    # saw sweeps in with blooms, then the portamento swoop (G4 -> G5)
    for t, p, d, v in ((128.0, 71, 8.0, 84), (136.0, 74, 8.0, 86),
                       (144.0, 79, 6.0, 88), (150.0, 76, 2.0, 84),
                       (152.0, 67, 8.0, 86)):
        sc.note(5, p, t, d, v, jt=0, jv=2)
        if d >= 2.0:
            _bloom(sc, 5, t, d, peak=min(76, 30 + int(round(d * 6))))
    en.portamento_on(sc, 5, 159.8, time_cc=58)
    sc.note(5, 79, 160.0, 14.0, 90, jt=0, jv=0)
    _bloom(sc, 5, 160.0, 14.0, peak=84)
    en.portamento_off(sc, 5, 175.5)
    for t, p, d, v in ((144.0, 71, 16.0, 60), (160.0, 74, 16.0, 66),
                       (160.0, 66, 16.0, 62)):
        sc.note(7, p, t, d, v, jt=0, jv=2)
    for i in range(8):
        _post(sc, 3, 116.0 + 8.0 * i, up=True, vel=78 + i * 2)
        _post(sc, 4, 118.0 + 8.0 * i, up=False, vel=76 + i * 2)
    _steel_off(sc, B10, D10, 55)
    for t in (128.0, 144.0, 160.0):
        _hit(sc, t, 92)
    for t, p, v in ((168.0, 64, 52), (168.0, 67, 48)):
        sc.note(8, p, t, 7.75, v, jt=0, jv=2)
    en.vowel_curve(sc, 8, [(168.0, 20), (176.0, 60)])
    _pads(sc, B10, D10, 8.0, 56, vel_end=70)
    _fills(sc, B10, D10)
    _riser_window(sc, B10, D10)


def _b_drop1(sc):
    for st in (176.0, 192.0, 208.0, 224.0):
        _hook(sc, st, vbump=0, wing=True)
    for o, p, d, v in TAG:
        _duo_note(sc, p, 240.0 + o, d, v)
    for o, d in ((0.0, 3.5), (4.0, 3.5), (8.0, 3.5)):
        _bloom(sc, 14, 240.0 + o, d)
    _kit_four(sc, D10, 208.0, kick=102, hat=58, oh=46, back=("both", 96),
              crash_every=4)
    _kit_four(sc, 208.0, 240.0, kick=104, hat=60, oh=47, back=("both", 98),
              hat16=42, crash_every=4)
    _kit_four(sc, 240.0, STRIP0, kick=104, hat=60, oh=47, back=("both", 98),
              hat16=44, crash_every=2)
    _bass_eighths(sc, D10, STRIP0, 100, pop=True)
    _ost16(sc, D10, STRIP0, 80, 84)
    _steel_off(sc, D10, STRIP0, 58)
    for st in (176.0, 192.0, 208.0, 224.0):
        _post(sc, 3, st + 12.5, up=True, vel=90)
        _post(sc, 4, st + 14.5, up=False, vel=88)
    for t in range(0, 32, 4):
        _hit(sc, 176.0 + t, 98)
    for t in range(32, 80, 8):
        _hit(sc, 176.0 + t, 96)
    for t, p in ((176.0, 76), (192.0, 76), (208.0, 79), (224.0, 76),
                 (240.0, 76)):
        sc.note(7, p, t, 16.0, 62, jt=0, jv=0)
        sc.note(7, p - 12, t, 16.0, 56, jt=0, jv=0)
    _pads(sc, D10, STRIP0, 4.0, 72)
    _fills(sc, D10, STRIP0)


def _b_strip(sc):
    _duo_chugs(sc, STRIP0, B20, (0.0, 1.5, 2.0, 3.0), vel=52,
               acc=(0.0,), lo=48)
    _bass_eighths(sc, STRIP0, B20, 56)
    for b in range(8):
        bar = STRIP0 + 4.0 * b
        sc.note(9, 36, bar, 0.22, 34, jt=0, jv=2)
        sc.note(9, 36, bar + 2.0, 0.22, 32, jt=0, jv=2)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.14, 28, jt=0, jv=2)
    _ost16(sc, 280.0, B20, 46, 58)
    _riser_window(sc, STRIP0, B20)


def _b_build2(sc):
    _duo_riff(sc, B20, 320.0, 78, lo=60)
    _duo_riff(sc, 320.0, 356.0, 86, lo=60, push=True)
    for t0, root, st, duo in ASCENT_PINS:
        if B20 <= t0 < D20:
            _ascent_duo(sc, t0, root, st, vel=102)
    _kit_four(sc, B20, 328.0, kick=98, hat=56, oh=45, back=("clap", 90),
              crash_every=8)
    _kit_four(sc, 328.0, D20, kick=104, hat=60, oh=47, back=("clap", 96),
              hat16=44, crash_every=8)
    _bass_eighths(sc, B20, D20, 90, vel_end=102, pop=True)
    _ost16(sc, B20, D20, 68, 86)
    for t, p, d, v in ((304.0, 72, 8.0, 84), (312.0, 76, 8.0, 86),
                       (320.0, 79, 8.0, 88), (328.0, 74, 8.0, 86),
                       (336.0, 78, 8.0, 88), (344.0, 81, 8.0, 90),
                       (352.0, 83, 10.0, 92), (362.5, 88, 3.5, 94)):
        sc.note(5, p, t, d, v, jt=0, jv=2)
        _bloom(sc, 5, t, d, peak=min(80, 30 + int(round(d * 6))))
    _steel_off(sc, B20, D20, 60, skip=((319.0, 328.0),))
    _orbit_riff(sc)
    for t, p, d, v in ((288.0, 71, 16.0, 58), (304.0, 72, 16.0, 60),
                       (320.0, 74, 16.0, 64), (336.0, 74, 16.0, 66),
                       (352.0, 76, 16.0, 70)):
        sc.note(7, p, t, d, v, jt=0, jv=0)
    for t, p, v in ((352.0, 64, 54), (356.0, 67, 50), (360.0, 71, 52)):
        sc.note(8, p, t, 367.75 - t, v, jt=0, jv=2)
    en.vowel_curve(sc, 8, [(352.0, 20), (368.0, 70)])
    for i in range(9):
        _post(sc, 3, 292.0 + 8.0 * i, up=True, vel=80 + i)
        _post(sc, 4, 294.0 + 8.0 * i, up=False, vel=78 + i)
    for i, t in enumerate((304.0, 320.0, 336.0, 352.0, 356.0, 360.0, 364.0)):
        _hit(sc, t, 94 + 2 * i)
    _pads(sc, B20, D20, 8.0, 56, vel_end=74)
    _fills(sc, B20, D20)
    _riser_window(sc, B20, D20)


def _b_drop2(sc):
    # hook statements: lead free of the wing (formation broken)
    for st in (368.0, 384.0, 400.0, 416.0):
        _hook(sc, st, vbump=4, wing=False)
        for o, p, d, v in WING_CTR:
            sc.note(15, p, st + o, d, v, jt=0, jv=0)
        for o, p, d, v in SAW_CTR:
            sc.note(5, p, st + o, d, v, jt=0, jv=2)
            _bloom(sc, 5, st + o, d, peak=min(72, 28 + int(round(d * 8))))
    # the soar section
    for t, p, d, v in SOAR:
        sc.note(14, p, t, d, v, jt=0, jv=0)
        if d >= 4.0:
            _bloom(sc, 14, t, d)
    en.vibrato(sc, 14, 432.0, 8.0, depth=0.22, delay=1.5)
    en.vibrato(sc, 14, 448.0, 6.0, depth=0.2, delay=1.2)
    en.vibrato(sc, 14, 460.0, 4.0, depth=0.2, delay=1.0)
    # wing pump under the soars
    _wing_pump(sc, 432.0, 464.0, 80)
    # final wall: duo back in octaves
    for st in (464.0, 480.0):
        _hook(sc, st, vbump=8, wing=True)
    # kit
    _kit_four(sc, D20, 432.0, kick=108, hat=62, oh=48, back=("both", 100),
              hat16=46, crash_every=2)
    _kit_four(sc, 432.0, 464.0, kick=104, hat=58, oh=46, back=("both", 96),
              hat16=44, crash_every=2, ride=40)
    _kit_four(sc, 464.0, OUT0, kick=110, hat=63, oh=48, back=("both", 102),
              hat16=48, crash_every=2)
    _bass_eighths(sc, D20, 432.0, 104, pop=True)
    _bass_eighths(sc, 432.0, 464.0, 98)
    _bass_eighths(sc, 464.0, OUT0, 106, pop=True, push16=True)
    _ost16(sc, D20, 432.0, 86, 90)
    _ost16(sc, 432.0, 464.0, 78, 84)
    _ost16(sc, 464.0, OUT0, 90, 94)
    _steel_off(sc, D20, OUT0, 66)
    # saw under the soars and over the final wall
    for t, p, d, v in ((436.0, 83, 4.0, 92), (440.0, 79, 8.0, 92),
                       (448.0, 79, 6.0, 90), (456.0, 86, 8.0, 94),
                       (464.0, 88, 4.0, 94), (468.0, 84, 4.0, 92),
                       (472.0, 86, 4.0, 94), (476.0, 90, 4.0, 96),
                       (480.0, 88, 4.0, 96), (484.0, 84, 4.0, 94),
                       (488.0, 86, 4.0, 94), (492.0, 81, 4.0, 92)):
        sc.note(5, p, t, d, v, jt=0, jv=2)
    _choir_block(sc, D20, 432.0, 4.0, 66)
    _choir_block(sc, 432.0, OUT0, 4.0, 62)
    en.vowel_curve(sc, 8, [(368.0, 0), (376.0, 88), (430.0, 88),
                           (434.0, 55), (462.0, 70), (464.0, 85),
                           (494.0, 80), (496.0, 30)])
    for t, p, d, v in ((368.0, 76, 16.0, 64), (384.0, 76, 16.0, 64),
                       (400.0, 79, 16.0, 66), (416.0, 76, 16.0, 64),
                       (432.0, 79, 8.0, 60), (440.0, 76, 8.0, 58),
                       (448.0, 79, 8.0, 60), (456.0, 83, 8.0, 64),
                       (464.0, 83, 16.0, 66), (480.0, 83, 16.0, 66),
                       (464.0, 76, 16.0, 60), (480.0, 76, 16.0, 60)):
        sc.note(7, p, t, d, v, jt=0, jv=0)
    for st in (368.0, 384.0, 400.0, 416.0, 464.0, 480.0):
        _post(sc, 3, st + 12.5, up=True, vel=90)
        _post(sc, 4, st + 14.5, up=False, vel=88)
    for t, ch, up in ((436.0, 3, True), (438.0, 4, False), (444.0, 3, True),
                      (446.0, 4, False), (452.0, 3, True), (454.0, 4, False)):
        _post(sc, ch, t, up=up, vel=84)
    for t in range(0, 32, 4):
        _hit(sc, 368.0 + t, 104)
    for t in (432.0, 440.0, 448.0, 456.0):
        _hit(sc, t, 100)
    for t in range(96, 128, 4):
        _hit(sc, 368.0 + t, 106)
    _pads(sc, 368.25, 496.25, 4.0, 76)
    _fills(sc, D20, OUT0)
    _riser_window(sc, D20, OUT0)


def _b_outro(sc):
    for t, p, d, v in LEAD_OUT:
        sc.note(14, p, t, d, v, jt=0, jv=0)
        _bloom(sc, 14, t, d, peak=min(60, 24 + int(round(d * 8))))
    # the pinned solo final ASCENT (lead ship alone; wing silent all movement)
    material.play_ascent(sc, 14, 552.0, 52, stretch=2.0, vel=92, vel_end=78,
                         jt=0, jv=0)
    _bloom(sc, 14, 555.0, 5.0, peak=70)
    en.vibrato(sc, 14, 556.0, 4.0, depth=0.2, delay=0.8)
    _morse(sc, MORSE_T0S[1])
    _bass_halves(sc, OUT0, 544.0, 66, vel_end=46)
    sc.note(2, 40, 544.0, 3.5, 44, jt=0, jv=2)
    _ost8(sc, OUT0, 528.0, 58, 42)
    for b in range(4):
        sc.note(0, 76, 528.0 + 4.0 * b, 0.9, 38 - 2 * b, jt=0, jv=2)
    for b in range(8):                          # fading half kit
        bar = OUT0 + 4.0 * b
        sc.note(9, 36, bar, 0.22, int(en.lerp(74, 52, b / 7)), jt=0, jv=2)
        sc.note(9, 36, bar + 2.0, 0.22, int(en.lerp(68, 46, b / 7)),
                jt=0, jv=2)
        sc.note(9, 37, bar + 3.0, 0.2, 40, jt=0, jv=2)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.14, int(en.lerp(42, 28, b / 7)),
                    jt=0, jv=2)
    for b in range(5):
        bar = 528.0 + 4.0 * b
        sc.note(9, 36, bar, 0.22, 40 - b, jt=0, jv=2)
        for k in range(4):
            sc.note(9, 42, bar + k, 0.14, 26, jt=0, jv=2)
    _pads(sc, 496.5, 576.5, 8.0, 58, vel_end=36)
    _choir_block(sc, 496.5, 528.5, 8.0, 54, vel_end=40)
    en.vowel_curve(sc, 8, [(496.5, 30), (526.0, 10)])
    for t, p, d, v in ((496.0, 76, 24.0, 56), (520.0, 74, 16.0, 50),
                       (536.0, 71, 20.0, 46), (556.0, 71, 16.0, 40),
                       (496.0, 71, 24.0, 52), (520.0, 67, 16.0, 46),
                       (536.0, 64, 20.0, 42), (556.0, 64, 16.0, 38)):
        sc.note(7, p, t, d, v, jt=0, jv=0)
    for t, ch, up, v in ((504.0, 3, True, 70), (506.0, 4, False, 62),
                         (520.0, 3, True, 58), (522.0, 4, False, 50)):
        _post(sc, ch, t, up=up, vel=v)
    for t, v in ((496.0, 92), (512.0, 78), (528.0, 64)):
        _hit(sc, t, v)
    _fills(sc, OUT0, END)


BUILDERS = [_b_contact, _b_taxi, _b_build1, _b_drop1, _b_strip,
            _b_build2, _b_drop2, _b_outro]


# ---------------------------------------------------------------------------
# Oracles (written first; the music above is composed to pass them)
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


_CELL = [(0.0, 0), (0.5, 7), (1.0, 12), (1.5, 19)]


def _o_formation(sc):
    """OCTAVES: wing = lead - 12, tick-for-tick, through beat 368."""
    fails = []
    hi = _tick(368.0)
    lead = sorted((t, p) for t, p, _v in _note_ons(sc, 14) if t < hi)
    wing = sorted((t, p) for t, p, _v in _note_ons(sc, 15) if t < hi)
    if len(lead) < 150:
        fails.append(f"only {len(lead)} lead notes in the formation span")
    if len(lead) != len(wing):
        fails.append(f"formation span: {len(lead)} lead vs {len(wing)} "
                     f"wing notes")
        return fails
    for (lt, lp), (wt, wp) in zip(lead, wing):
        if lt != wt or wp != lp - 12:
            fails.append(f"formation broken at tick {lt}: lead {lp}@{lt} "
                         f"vs wing {wp}@{wt}")
            if len(fails) > 4:
                break
    return fails


def _o_ascent(sc):
    """Pinned ASCENT statements; the 0.0 one is the album's first pitched
    sound (before any drum); the 552.0 one is solo lead ship."""
    fails = []
    lead = {(t, p) for t, p, _v in _note_ons(sc, 14)}
    wing = {(t, p) for t, p, _v in _note_ons(sc, 15)}
    for t0, root, st, duo in ASCENT_PINS:
        for on, semi in _CELL:
            tk = _tick(t0 + on * st)
            if (tk, root + semi) not in lead:
                fails.append(f"ascent@{t0}: lead {root + semi} missing "
                             f"at tick {tk}")
            if duo and (tk, root + semi - 12) not in wing:
                fails.append(f"ascent@{t0}: wing {root + semi - 12} missing "
                             f"at tick {tk}")
    # solo: the wing ship is silent for the whole outro
    wing_out = [t for t, _p, _v in _note_ons(sc, 15) if t >= _tick(OUT0)]
    if wing_out:
        fails.append(f"{len(wing_out)} wing notes in the outro "
                     f"(final ascent must be solo lead)")
    # first pitched notes of the album are the duo cell, before any drum
    for ch in range(16):
        if ch in (9, 14, 15) or ch not in sc.events:
            continue
        ons = _note_ons(sc, ch)
        if ons and ons[0][0] < _tick(2.0):
            fails.append(f"ch{ch} sounds at tick {ons[0][0]}, before the "
                         f"duo ascent finishes its pickups")
    drum = _note_ons(sc, 9)
    if drum and drum[0][0] < _tick(4.0):
        fails.append(f"first drum at tick {drum[0][0]} < beat 4 "
                     f"(ascent must precede any drum)")
    lead_first = sorted(lead)[:4]
    want = [(_tick(on), 52 + s) for on, s in _CELL]
    if lead_first != want:
        fails.append(f"album's first lead notes {lead_first} != cell {want}")
    return fails


def _o_morse(sc):
    """The WHEELS UP radio lane, pinned to material.morse_rhythm."""
    fails = []
    rhythm = material.morse_rhythm(material.MORSE_T1, 0.25)
    if len(rhythm) != 23:
        fails.append(f"morse rhythm has {len(rhythm)} symbols, want 23")
    expected = sorted(_tick(t0 + on) for t0 in MORSE_T0S
                      for on, _du in rhythm)
    actual = sorted(t for t, p, _v in _note_ons(sc, 9) if p == 76)
    if actual != expected:
        fails.append(f"woodblock lane: {len(actual)} onsets vs "
                     f"{len(expected)} expected (or ticks drifted)")
    durs = {on: (off - on) / _PPQ for on, off, p in _note_spans(sc, 9)
            if p == 76}
    for t0 in MORSE_T0S:
        for on, du in rhythm:
            got = durs.get(_tick(t0 + on))
            if got is None:
                continue
            if du > 0.5 and got < 0.45:
                fails.append(f"dah at {t0 + on:.2f} too short ({got:.2f}b)")
            if du < 0.5 and got > 0.35:
                fails.append(f"dit at {t0 + on:.2f} too long ({got:.2f}b)")
    return fails


def _o_hook(sc):
    """Every hook statement is the pinned table, and nothing else."""
    fails = []
    ons = _note_ons(sc, 14)
    for st in HOOK_STARTS:
        lo, hi = _tick(st), _tick(st + 16.0)
        actual = sorted((t, p) for t, p, _v in ons if lo <= t < hi)
        want = sorted((_tick(st + o), p) for o, p, _d, _v in HOOK)
        if actual != want:
            fails.append(f"hook@{st}: {len(actual)} lead notes != pinned "
                         f"{len(want)} (or ticks/pitches drifted)")
    return fails


def _o_contour(sc):
    """Builds strictly rise per window; DROP2 > DROP1; STRIP is a hush."""
    fails = []
    sums = _bar_sums(sc)
    taxi = _mean_barsum(sums, TAXI0, B10)
    b1a, b1b = _mean_barsum(sums, 112, 144), _mean_barsum(sums, 144, 176)
    d1 = _mean_barsum(sums, D10, STRIP0)
    strip = _mean_barsum(sums, STRIP0, B20)
    b2a, b2b = _mean_barsum(sums, 288, 328), _mean_barsum(sums, 328, 368)
    d2 = _mean_barsum(sums, D20, OUT0)
    if not taxi < b1a < b1b:
        fails.append(f"BUILD1 not strictly rising: taxi {taxi:.0f}, "
                     f"w1 {b1a:.0f}, w2 {b1b:.0f}")
    if not b2a < b2b:
        fails.append(f"BUILD2 not rising: w1 {b2a:.0f}, w2 {b2b:.0f}")
    if not d2 > 1.05 * d1:
        fails.append(f"DROP2 mean {d2:.0f} not > 1.05 x DROP1 {d1:.0f}")
    if not strip < 0.5 * d1:
        fails.append(f"STRIP {strip:.0f} not under 50% of DROP1 {d1:.0f}")
    return fails


def _o_fills(sc):
    """Escalation, variety, the unbroken pre-drop runs, thinned drops,
    and every scheduled fill pinned tick-exact."""
    fails = []
    ons10 = {(t, p) for t, p, _v in _note_ons(sc, 10)}
    ons11 = {(t, p) for t, p, _v in _note_ons(sc, 11)}
    for t, shape, _vb in FILL_SCHEDULE:
        lib = material.FILL_LIB[shape]
        for lane, ons in (("tom", ons10), ("syn", ons11)):
            for off, p, _d, _v in lib.get(lane, ()):
                if (_tick(t + off), p) not in ons:
                    fails.append(f"fill {shape}@{t}: {lane} note {p} at "
                                 f"+{off} missing")
    merged = sorted(t for t, _p in (ons10 | ons11))

    def cnt(lo, hi):
        a, b = _tick(lo), _tick(hi)
        return sum(1 for t in merged if a <= t < b)

    b1 = [cnt(112, 144), cnt(144, 176)]
    if not b1[0] < b1[1]:
        fails.append(f"BUILD1 fill windows not rising: {b1}")
    b2 = [cnt(288, 308), cnt(308, 328), cnt(328, 348), cnt(348, 368)]
    if any(x >= y for x, y in zip(b2, b2[1:])):
        fails.append(f"BUILD2 fill windows not strictly rising: {b2}")
    for lo, hi, name in ((112.0, 176.0, "BUILD1"), (288.0, 368.0, "BUILD2")):
        shapes = {s for t, s, _v in FILL_SCHEDULE if lo <= t < hi}
        if len(shapes) < 5:
            fails.append(f"{name} uses only {len(shapes)} fill shapes")
    beats = [t / _PPQ for t in merged]
    for drop in (D10, D20):
        run, last = 0, None
        for b in reversed([x for x in beats if x < drop]):
            if last is None:
                if b < drop - 1.2:
                    break
                run, last = 1, b
            elif last - b <= 0.55:
                run, last = run + 1, b
            else:
                break
        if run < 20:
            fails.append(f"pre-drop run into {drop}: only {run} unbroken "
                         f"fill notes (want >= 20)")
    for lo, hi in ((D10, STRIP0), (D20, OUT0)):
        w = lo
        while w < hi:
            c = cnt(w, min(w + 32.0, hi))
            if c > 24:
                fails.append(f"drop window {w}-{w + 32}: {c} fill notes "
                             f"(cap 24; drops must thin)")
            w += 32.0
    return fails


def _o_orbit(sc):
    """Exactly two bars of ORBIT_RIFF_361 on the steel channel, pinned."""
    fails = []
    riffp = [en.pitch(ORBIT_BASE, material.ORBIT_MODE_361, d)
             for d in material.ORBIT_RIFF_361]
    step_t = _tick(material.ORBIT_STEP_361)
    expected = sorted((_tick(ORBIT_T0 + 2.0 * s + i * material.ORBIT_STEP_361),
                       riffp[i])
                      for s in range(ORBIT_STATEMENTS) for i in range(8))
    lo, hi = _tick(ORBIT_T0), _tick(ORBIT_T0 + 2.0 * ORBIT_STATEMENTS)
    actual = sorted((t, p) for t, p, _v in _note_ons(sc, 6) if lo <= t < hi)
    if actual != expected:
        fails.append(f"orbit wink: window has {len(actual)} steel notes, "
                     f"want the {len(expected)} pinned riff notes")
    ons = _note_ons(sc, 6)
    matches = []
    for i in range(len(ons) - 7):
        seg = ons[i:i + 8]
        if ([p for _t, p, _v in seg] == riffp
                and all(seg[k + 1][0] - seg[k][0] == step_t
                        for k in range(7))):
            matches.append(seg[0][0])
    if len(matches) != ORBIT_STATEMENTS:
        fails.append(f"{len(matches)} orbit statements found, want exactly "
                     f"{ORBIT_STATEMENTS} (<= 8 per the HLD)")
    if any(not lo <= m < hi for m in matches):
        fails.append("an orbit statement escaped the pinned two bars")
    return fails


def _o_counter(sc):
    """DROP2 counterpoint: wing (and saw) against the lead hook."""
    fails = []
    lo, hi = _tick(368.0), _tick(432.0)
    lead = [(t, p) for t, p, _v in _note_ons(sc, 14) if lo <= t < hi]
    wing = [(t, p) for t, p, _v in _note_ons(sc, 15) if lo <= t < hi]
    saw = [(t, p) for t, p, _v in _note_ons(sc, 5) if lo <= t < hi]
    if len(wing) < 30:
        fails.append(f"only {len(wing)} wing notes in the window")
    if len(saw) < 12:
        fails.append(f"only {len(saw)} saw notes in the window")
    lead_ticks = [t for t, _p in lead]
    lead_set = set(lead_ticks)

    def lead_pitch_at(t):
        i = bisect.bisect_right(lead_ticks, t) - 1
        return lead[i][1] if i >= 0 else None

    non_coinc = sum(1 for t, _p in wing if t not in lead_set)
    if non_coinc / max(1, len(wing)) < 0.5:
        fails.append(f"wing onsets only {non_coinc}/{len(wing)} "
                     f"non-coincident (< 50%)")
    good = total = 0
    for (t1, p1), (t2, p2) in zip(wing, wing[1:]):
        l1, l2 = lead_pitch_at(t1), lead_pitch_at(t2)
        if l1 is None or l2 is None:
            continue
        dw, dl = p2 - p1, l2 - l1
        total += 1
        if dw == 0 or dl == 0 or (dw > 0) != (dl > 0):
            good += 1
    if total and good / total < 0.6:
        fails.append(f"contrary+oblique motion only {good}/{total} (< 60%)")
    doubled = sum(1 for t, p in wing
                  if lead_pitch_at(t) is not None
                  and p % 12 == lead_pitch_at(t) % 12)
    if doubled / max(1, len(wing)) > 0.25:
        fails.append(f"pitch-class doubling {doubled}/{len(wing)} (> 25%)")
    spans = {ch: _note_spans(sc, ch) for ch in (14, 15, 5)}
    sounding_bars = 0
    for db in range(368, 432, 4):
        tk = _tick(float(db))
        at = {}
        for ch, sp in spans.items():
            ps = [p for on, off, p in sp if on <= tk < off]
            if ps:
                at[ch] = ps
        if 15 in at:
            sounding_bars += 1
        chans = sorted(at)
        for i, a in enumerate(chans):
            for b in chans[i + 1:]:
                for pa in at[a]:
                    for pb in at[b]:
                        if (pa - pb) % 12 not in _CONSONANT:
                            fails.append(f"downbeat {db}: ch{a} {pa} vs "
                                         f"ch{b} {pb} dissonant")
    if sounding_bars < 13:
        fails.append(f"wing sounding on only {sounding_bars}/16 downbeats")
    return fails


def _o_soar(sc):
    """CC74 macro-sweep >= 60 units; risers into both drops; a >= 6-beat
    held lead soar with a CC1 bloom; the saw portamento swoop."""
    fails = []
    cc74 = _cc_lane(sc, 1, 74)
    lo_win = [v for t, v in cc74 if _tick(252.0) <= t <= _tick(300.0)]
    hi_win = [v for t, v in cc74 if _tick(352.0) <= t <= _tick(372.0)]
    if not lo_win or not hi_win or max(hi_win) - min(lo_win) < 60:
        span = (max(hi_win) - min(lo_win)) if (lo_win and hi_win) else 0
        fails.append(f"pad CC74 macro-sweep only {span} units (< 60)")
    riser_ons = [t for t, _p, _v in _note_ons(sc, 13)]
    for d in (D10, D20):
        if not any(_tick(d - 8.0) <= t < _tick(d) for t in riser_ons):
            fails.append(f"no riser into the drop at {d}")
    soars = [(on, off) for on, off, _p in _note_spans(sc, 14)
             if off - on >= 6 * _PPQ and on >= _tick(432.0)]
    cc1 = _cc_lane(sc, 14, 1)
    ok = False
    for on, off in soars:
        peak = max([v for t, v in cc1 if on < t < off], default=0)
        tail = [v for t, v in cc1 if off - _PPQ // 2 <= t <= off + _PPQ]
        if peak >= 78 and (not tail or min(tail) <= 8):
            ok = True
            break
    if not ok:
        fails.append("no >= 6-beat lead soar with a full CC1 bloom")
    cc65 = [v for _t, v in _cc_lane(sc, 5, 65)]
    if 127 not in cc65 or 0 not in cc65:
        fails.append("saw portamento swoop missing (CC65 on+off)")
    return fails


def _o_layers(sc):
    """All 16 channels are used, and all 16 sound in DROP2's first 4 bars."""
    fails = []
    used = [ch for ch in range(16) if _note_ons(sc, ch)]
    if len(used) != 16:
        fails.append(f"only {len(used)} channels used: {used}")
    lo, hi = _tick(D20), _tick(D20 + 16.0)
    missing = [ch for ch in range(16)
               if not any(lo <= t < hi for t, _p, _v in _note_ons(sc, ch))]
    if missing:
        fails.append(f"channels missing from the DROP2 climax window: "
                     f"{missing}")
    return fails


def oracles(sc, info, spans):
    return [
        ("duo_octave_formation", _o_formation(sc)),
        ("ascent_first_pitches", _o_ascent(sc)),
        ("radio_morse_lane", _o_morse(sc)),
        ("hook_statements", _o_hook(sc)),
        ("build_drop_contour", _o_contour(sc)),
        ("fill_escalation", _o_fills(sc)),
        ("orbit_wink", _o_orbit(sc)),
        ("drop2_counterpoint", _o_counter(sc)),
        ("soar_sweep", _o_soar(sc)),
        ("climax_layers", _o_layers(sc)),
    ]
