"""T7 — Vapour.  HLD §4/T7.

Wingtip vortices flashing into cloud — the sweep-and-shimmer act.  F lydian,
138 bpm, 4/4 over a breakbeat kit (NO four-on-the-floor in the grooves —
kick displacement is the groove's signature; the drops may floor it).
Bright, airy, fast: the sweeping-synth showcase.

Architecture (154 bars, ~4:29):
  I.    Shimmer          0-64    crystal arp (the only autopanned lane) + pad
  II.   Vortex Groove   64-176   breakbeat; THE DUO glides in parallel sixths
  III.  First Sweep    176-208   CC74 macro-sweep 1 + portamento swoop, roll
  IV.   Drop One       208-288   four-floor allowed; duo hook fortissimo
  V.    Thin Air       288-320   strip: arp + pad + low choir hum
  VI.   Second Groove  320-400   breakbeat again, hook sequenced up a step
  VII.  The Big Sweep  400-440   CC74 sweep 2 (bigger) + two swoops, long roll
  VIII. Drop Two       440-552   > DROP1: double-time hats, pinned ASCENT,
                                 saw counter-line against the duo (verified
                                 counterpoint), peak phrases
  IX.   Dissolve       552-616   arp thins, sweep falls, vapour fades

Duo formation — SIXTHS: the wing ship (ch15, GM29 bank1 — it must sing) flies
parallel a diatonic sixth below the lead ship (ch14): wing = lead - (8 or 9)
semitones, diatonically correct in F lydian, for >= 80% of duo time (the
oracle samples the interval histogram on a half-beat grid).  The lydian #4
(B natural) is pinned into the hook; a purity oracle bans any non-lydian
pitch class from every melodic lane.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 7
TITLE = "Vapour"
FILE = "07 - Vapour.mid"
SEED = 20261107
COMMENT = ("Vapour - the sweep-and-shimmer act of Slipstream. Wingtip "
           "vortices flash into cloud over an F lydian breakbeat: the "
           "two-guitar display team glides in machine-verified parallel "
           "sixths, two giant CC74 filter sweeps and portamento swoops lift "
           "the piece into a pair of drops (the second provably bigger, with "
           "double-time hats and a saw counter-line in verified "
           "counterpoint), and the shimmer arp - the only moving-pan lane - "
           "dissolves the trail at the end.")

MODE = "lydian"
BASE = 65                     # F4 — degree 1 of the duo's F lydian
BASS_BASE = 41                # F2
LYD_PCS = {0, 2, 4, 5, 7, 9, 11}       # F G A B(!) C D E
_PPQ = en.PPQ

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

INTRO = (0.0, 64.0)
GROOVE1 = (64.0, 176.0)
SWEEP1 = (176.0, 208.0)
DROP1 = (208.0, 288.0)
STRIP = (288.0, 320.0)
GROOVE2 = (320.0, 400.0)
SWEEP2 = (400.0, 440.0)
DROP2 = (440.0, 552.0)
OUTRO = (552.0, 616.0)
END = OUTRO[1]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Shimmer", *INTRO),
        ("II. Vortex Groove", *GROOVE1),
        ("III. First Sweep", *SWEEP1),
        ("IV. Drop One", *DROP1),
        ("V. Thin Air", *STRIP),
        ("VI. Second Groove", *GROOVE2),
        ("VII. The Big Sweep", *SWEEP2),
        ("VIII. Drop Two", *DROP2),
        ("IX. Dissolve", *OUTRO),
    ],
    tempo_map=[(0.0, 138.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0)],                 # F lydian = no accidentals
    channels=[
        (0, "shimmer arp", 98, 96, 64, 60),      # crystal — the autopan lane
        (1, "sky pad", 89, 92, 64, 70),
        (2, "vortex bass", 39, 108, 64, 25),
        (3, "post L glk", 9, 88, 18, 55),
        (4, "post R pizz", 45, 92, 110, 45),
        (5, "soar saw", 81, 102, 64, 60),
        (6, "harp", 46, 90, 64, 65),
        (7, "aerial strings", 49, 84, 64, 75),
        (8, "vapour choir", 52, 88, 64, 80),
        (9, "kit", 0, 110, 64, 40),
        (10, "melodic toms", 117, 100, 64, 45),
        (11, "syn drum", 118, 100, 64, 45),
        (12, "orch hit", 55, 100, 64, 55),
        (13, "riser", 119, 96, 64, 70),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 108, 64, 24),
    ],
    program_changes=[(9, 0.0, 25)],   # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

# ---------------------------------------------------------------------------
# Musical DNA — explicit tables (all duo lanes emitted jt=0)
# ---------------------------------------------------------------------------

def _dp(deg: int, shift: int = 0) -> int:
    return en.pitch(BASE, MODE, deg + shift)


# The HOOK — 16 beats, two 8-beat phrases; the lydian #4 (degree 4 = B) is
# featured at rel 1.5, 5.0, 11.0 (a full-beat B on the downbeat side of bar
# 3) and 12.5.  (degree, onset, dur).
HOOK = [
    (5, 0.0, 1.0), (3, 1.0, 0.5), (4, 1.5, 0.5), (5, 2.0, 2.0),
    (6, 4.0, 1.0), (4, 5.0, 0.5), (5, 5.5, 0.5), (6, 6.0, 2.0),
    (7, 8.0, 0.75), (8, 8.75, 0.75), (7, 9.5, 0.5), (6, 10.0, 0.5),
    (5, 10.5, 0.5), (4, 11.0, 1.0),
    (3, 12.0, 0.5), (4, 12.5, 0.5), (5, 13.0, 1.0), (2, 14.0, 2.0),
]

# The PEAK phrase (DROP2's high pass), 16 beats.
PEAK = [
    (8, 0.0, 4.0), (7, 4.0, 1.0), (6, 5.0, 0.5), (7, 5.5, 0.5),
    (8, 6.0, 2.0), (9, 8.0, 3.0), (8, 11.0, 1.0), (7, 12.0, 0.5),
    (6, 12.5, 0.5), (5, 13.0, 1.0), (4, 14.0, 2.0),
]

HOLD_D1 = [(5, 0.0, 3.5), (6, 4.0, 3.5), (4, 8.0, 3.5), (2, 12.0, 3.5)]
SWELL_S1 = [(5, 0.0, 5.0), (6, 6.0, 5.0), (8, 12.0, 5.0), (9, 18.0, 6.0)]
SWELL_S2 = [(5, 0.0, 3.5), (6, 4.0, 3.5), (7, 8.0, 3.5), (8, 12.0, 3.5),
            (9, 16.0, 3.5), (10, 20.0, 3.5), (11, 24.0, 7.0)]
FINAL_HOLD = [(5, 0.0, 3.0), (4, 3.0, 3.0), (3, 6.0, 3.0), (1, 9.0, 2.5)]

# Duo statement schedule: (start_beat, table, shift, vel_lead).
DUO_PLAN = [
    (96.0, HOOK, 0, 88), (112.0, HOOK, 0, 90), (128.0, HOOK, 1, 92),
    (144.0, HOOK, 0, 94), (160.0, HOOK, 1, 96),
    (176.0, SWELL_S1, 0, 96),
    (208.0, HOOK, 0, 104), (224.0, HOOK, 0, 104), (240.0, HOOK, 1, 106),
    (256.0, HOOK, 0, 106), (272.0, HOLD_D1, 0, 100),
    (336.0, HOOK, 1, 94), (352.0, HOOK, 0, 96), (368.0, HOOK, 0, 98),
    (384.0, HOOK, 1, 100),
    (400.0, SWELL_S2, 0, 102),
    (444.0, HOOK, 0, 106), (460.0, HOOK, 0, 106), (476.0, HOOK, 0, 108),
    (492.0, PEAK, 0, 108), (508.0, PEAK, 1, 110), (524.0, HOOK, 0, 104),
    (540.0, FINAL_HOLD, 0, 100),
]

# Shift-0 hook statements where the #4 pin is enforced.
SHARP4_STATEMENTS = [96.0, 112.0, 144.0, 208.0, 224.0, 256.0, 352.0, 368.0,
                     444.0, 460.0, 476.0, 524.0]

ASCENT_BEAT = 440.0            # the pinned ASCENT statement (lead ship, F4)

# The saw counter-line (DROP2 counterpoint window 460-492): onsets chosen
# non-coincident with every hook onset; pitches contrary to the hook's local
# direction and consonant with lead+wing on every downbeat (worked out
# against the HOOK table — see oracles).
COUNTER_WINDOW = (460.0, 492.0)
COUNTER_REL = [(2.5, 81, 3.5), (6.5, 79, 4.5), (11.5, 84, 3.0),
               (15.0, 88, 1.5)]

# Fill schedule: (beat, shape).  Escalation, variety, chain-into-drop and
# drop-thinning are all oracle-verified against THIS table.
FILL_SCHEDULE = [
    (62.0, "A"),
    (92.0, "A"), (110.0, "D"), (124.0, "A"), (142.0, "B"), (156.0, "C"),
    (166.0, "G"), (174.0, "B"), (188.0, "C"), (196.0, "F"), (200.0, "H"),
    (203.95, "E"), (206.95, "G"),
    (222.0, "A"), (238.0, "H"), (254.0, "A"), (270.0, "B"),
    (334.0, "A"), (350.0, "A"), (366.0, "D"), (382.0, "C"),
    (390.0, "B"), (398.0, "G"), (414.0, "D"), (420.0, "F"), (426.0, "H"),
    (435.95, "E"), (438.95, "G"),
    (470.0, "A"), (486.0, "H"), (502.0, "A"), (518.0, "B"), (534.0, "A"),
    (560.0, "G"), (584.0, "A"),
]

BUILD1_FILL_WINDOWS = [(64.0, 96.0), (96.0, 128.0), (128.0, 160.0),
                       (160.0, 192.0), (192.0, 208.0)]
BUILD2_FILL_WINDOWS = [(320.0, 352.0), (352.0, 384.0), (384.0, 416.0),
                       (416.0, 440.0)]
DROP_FILL_WINDOWS = [(208.0, 240.0), (240.0, 272.0), (272.0, 288.0),
                     (440.0, 472.0), (472.0, 504.0), (504.0, 536.0),
                     (536.0, 552.0)]

# Contour windows (velocity-mass discipline).
BUILD1_WINDOWS = [(64.0, 96.0), (96.0, 128.0), (128.0, 160.0),
                  (160.0, 192.0), (192.0, 208.0)]
BUILD2_WINDOWS = [(320.0, 352.0), (352.0, 384.0), (384.0, 416.0),
                  (416.0, 440.0)]

# Harmony: one chord per bar, cycling I - II - vi - II (F, G, Dm, G).
CYCLE = [1, 2, 6, 2]
HIT_PITCH = {1: 65, 2: 67, 6: 62, 5: 72}

ARP_SET = [65, 71, 72, 76, 77, 83]      # F B C E F B — the lydian shimmer

# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def _bar_deg(bar: float) -> int:
    return CYCLE[int(round((bar - INTRO[0]) / 4.0)) % 4]


def _bloom(sc, ch, on, dur):
    """CC1 vibrato bloom over a held note (the digest formula)."""
    peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _duo(sc, t0, table, shift, vel_l):
    """One duo statement: lead ship + wing ship a diatonic sixth below."""
    vel_w = vel_l - 10
    for deg, on, dur in table:
        sc.note(14, _dp(deg, shift), t0 + on, dur * 0.98, vel_l, jt=0, jv=2)
        sc.note(15, _dp(deg - 5, shift), t0 + on, dur * 0.98, vel_w,
                jt=0, jv=2)
        if dur >= 2.0:
            _bloom(sc, 14, t0 + on, dur)


def _duo_in(sc, t0, t1):
    for start, table, shift, vel in DUO_PLAN:
        if t0 <= start < t1:
            _duo(sc, start, table, shift, vel)


def _fills_in(sc, t0, t1):
    for start, shape in FILL_SCHEDULE:
        if t0 <= start < t1:
            material.play_fill(sc, shape, start)


def _break_bar(sc, bar, v=0, snares=True, ghosts=True, ride=False):
    """One breakbeat bar: kick 0 / 0.75 / 2.5, snare 1.0 / 2.75 (displaced),
    ghosts, 8th hats, open hats.  jt=0 — the pattern is oracle-pinned."""
    for off in (0.0, 0.75, 2.5):
        sc.note(9, 36, bar + off, 0.3, 100 + v, jt=0, jv=3)
    if snares:
        sc.note(9, 38, bar + 1.0, 0.25, 101 + v, jt=0, jv=3)
        sc.note(9, 38, bar + 2.75, 0.25, 103 + v, jt=0, jv=3)
    if ghosts:
        sc.note(9, 38, bar + 1.75, 0.15, 44, jt=0, jv=2)
        sc.note(9, 38, bar + 3.5, 0.15, 44, jt=0, jv=2)
    for k in range(8):
        hv = (62 if k % 2 == 0 else 54) + v
        sc.note(9, 42, bar + 0.5 * k, 0.2, hv, jt=0, jv=3)
    sc.note(9, 46, bar + 1.5, 0.4, 63 + v, jt=0, jv=3)
    sc.note(9, 46, bar + 3.25, 0.4, 60 + v, jt=0, jv=3)
    if ride:
        for k in range(4):
            sc.note(9, 51, bar + k + 0.5, 0.3, 48 + v, jt=0, jv=3)


def _floor_bar(sc, bar, v=0, sixteenth=False):
    """One drop bar: four-on-the-floor (allowed only in the drops)."""
    for k in range(4):
        sc.note(9, 36, bar + float(k), 0.3, 108 + v, jt=0, jv=3)
    sc.note(9, 39, bar + 1.0, 0.3, 102 + v, jt=0, jv=3)
    sc.note(9, 39, bar + 3.0, 0.3, 104 + v, jt=0, jv=3)
    for k in range(4):
        sc.note(9, 46, bar + 0.5 + k, 0.35, 66 + v, jt=0, jv=3)
    steps = 16 if sixteenth else 8
    for k in range(steps):
        hv = (58 if k % (2 if sixteenth else 1) == 0 else 50) + v
        sc.note(9, 42, bar + 4.0 * k / steps, 0.18, hv, jt=0, jv=3)


def _roll(sc, t0, t1, v0, v1, step=0.25):
    n = int(round((t1 - t0) / step))
    for i in range(n):
        sc.note(9, 38, t0 + step * i, 0.2,
                int(round(en.lerp(v0, v1, i / max(1, n - 1)))), jt=0, jv=3)


def _crash(sc, beat, vel=96):
    sc.note(9, 49, beat, 0.8, vel, jt=0, jv=3)


def _toms8(sc, t0, t1, vel=70):
    b = t0
    while b < t1 - 1e-9:
        sc.note(9, 43, b, 0.3, vel, jt=0, jv=3)
        b += 0.5


def _bass_riff_bar(sc, bar, v=0):
    d = _bar_deg(bar)
    riff = [(0.0, d, 0.4, 96), (0.75, d, 0.3, 88), (1.5, d + 4, 0.35, 90),
            (2.25, d, 0.3, 86), (2.5, d, 0.3, 92), (3.25, d + 2, 0.35, 88)]
    for off, deg, dur, vel in riff:
        sc.note(2, en.pitch(BASS_BASE, MODE, deg), bar + off, dur, vel + v,
                jt=0, jv=3)


def _bass_eights(sc, t0, t1, vel, fifth=True):
    b = t0
    while b < t1 - 1e-9:
        bar = 4.0 * (int(b) // 4)
        d = _bar_deg(bar)
        deg = d + 4 if (fifth and abs(b - bar - 3.0) < 1e-9) else d
        sc.note(2, en.pitch(BASS_BASE, MODE, deg), b, 0.4, vel, jt=0, jv=3)
        b += 0.5


def _arp_span(sc, t0, t1, step, vel):
    count = int(round((t1 - t0) / step))
    en.arp(sc, 0, ARP_SET, t0, count, step, vel, pattern="updown",
           gate=0.9, accent_every=8, accent=8)


def _post_L(sc, beat, vel=78):
    for i, p in enumerate((77, 81, 84)):
        sc.note(3, p, beat + 0.25 * i, 0.2, vel + 2 * i, jt=0, jv=3)


def _post_R(sc, beat, vel=80):
    for i, p in enumerate((72, 69, 65)):
        sc.note(4, p, beat + 0.25 * i, 0.2, vel + 2 * i, jt=0, jv=3)


def _harp_run(sc, seam, vel0=64):
    """Eight lydian sixteenths rising into a seam (ends ON the seam)."""
    for i in range(8):
        sc.note(6, _dp(1 + i), seam - 2.0 + 0.25 * i, 0.22,
                int(round(vel0 + 2.5 * i)), jt=0, jv=2)


def _riser(sc, beat, dur, vel):
    sc.note(13, 62, beat, dur, vel, jt=0, jv=0)


def _hit(sc, beat, deg, vel):
    sc.note(12, HIT_PITCH[deg], beat, 0.9, vel, jt=0, jv=2)


# ---------------------------------------------------------------------------
# Builders (one per movement)
# ---------------------------------------------------------------------------

def _b_shimmer(sc):
    t0, t1 = INTRO
    # --- whole-timeline CC lanes (authored once, here) ---
    en.autopan(sc, 0, 0.0, END, lo=32, hi=96, period_beats=16.0, step=0.5)
    en.cc_curve(sc, 1, 74, [                        # pad brightness macro
        (0.0, 44), (64.0, 44), (120.0, 40), (176.0, 30), (202.0, 104),
        (208.0, 40), (288.0, 36), (320.0, 36), (400.0, 26), (434.0, 112),
        (440.0, 44), (504.0, 58), (552.0, 44), (616.0, 24)], step=0.5)
    en.expr_curve(sc, 1, [
        (0.0, 84), (64.0, 92), (176.0, 100), (206.0, 116), (208.0, 110),
        (288.0, 72), (320.0, 88), (400.0, 104), (438.0, 120), (440.0, 116),
        (536.0, 104), (552.0, 88), (616.0, 58)], step=1.0)
    en.vowel_curve(sc, 8, [
        (0.0, 8), (176.0, 20), (202.0, 72), (208.0, 96), (280.0, 90),
        (288.0, 18), (320.0, 24), (400.0, 55), (436.0, 96), (536.0, 80),
        (552.0, 40), (616.0, 8)], step=1.0)
    # --- the shimmer itself ---
    _arp_span(sc, 0.0, 32.0, 0.5, 48)
    _arp_span(sc, 32.0, 64.0, 0.5, 56)
    en.pad_block(sc, 1, 0.0, [en.triad(53, MODE, d)
                              for d in (1, 2, 6, 2, 1, 2, 6, 2)],
                 span=8.0, size=4, lo=52, hi=76, vel=46, vel_end=60)
    for b in (8.0, 24.0, 40.0, 56.0):               # harp arpeggi
        for i, p in enumerate((53, 60, 65, 69, 72, 77)):
            sc.note(6, p, b + 0.25 * i, 1.5 - 0.2 * i, 56 + i, jt=2, jv=3)
    for bar in (40.0, 48.0, 56.0):                  # early antiphony
        _post_L(sc, bar + 2.0, vel=66)
        _post_R(sc, bar + 3.0, vel=68)
    b = 32.0                                        # engine-idle bass pulses
    while b < 64.0 - 1e-9:
        sc.note(2, 41, b, 1.7, int(round(en.lerp(58, 72, (b - 32) / 32))),
                jt=0, jv=2)
        b += 2.0
    for bar in range(48, 56, 4):                    # hats fade in
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.2, 44 + 2 * (k % 2), jt=0, jv=3)
    for bar in (56.0, 60.0):                        # proto-groove
        _break_bar(sc, bar, v=-14)
    _riser(sc, 60.0, 3.5, 72)
    _fills_in(sc, t0, t1)


def _b_groove1(sc):
    t0, t1 = GROOVE1
    _crash(sc, 64.0, vel=82)
    bar = t0
    while bar < t1 - 1e-9:
        v = int(round((bar - t0) / (t1 - t0) * 10))
        _break_bar(sc, bar, v=v)
        _bass_riff_bar(sc, bar, v=v)
        bar += 4.0
    _arp_span(sc, 64.0, 96.0, 0.5, 60)
    _arp_span(sc, 96.0, 128.0, 0.5, 62)
    _arp_span(sc, 128.0, 160.0, 0.5, 65)
    _arp_span(sc, 160.0, 176.0, 0.5, 68)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, _bar_deg(t0 + 4.0 * i))
                             for i in range(28)],
                 span=4.0, size=4, lo=52, hi=76, vel=52, vel_end=62)
    for bar in range(128, 176, 8):                  # antiphonal posts
        _post_L(sc, bar + 2.0, vel=76)
        _post_R(sc, bar + 3.0, vel=78)
    for bar in range(132, 176, 8):
        _post_R(sc, bar + 2.0, vel=76)
        _post_L(sc, bar + 3.0, vel=78)
    _harp_run(sc, 96.0, vel0=62)
    _harp_run(sc, 160.0, vel0=66)
    _riser(sc, 92.0, 3.8, 80)                       # lift into the duo entry
    _duo_in(sc, t0, t1)
    _fills_in(sc, t0, t1)


def _b_sweep1(sc):
    t0, t1 = SWEEP1
    _crash(sc, 176.0, vel=86)
    bar = t0
    while bar < 192.0 - 1e-9:
        _break_bar(sc, bar, v=4)
        bar += 4.0
    while bar < t1 - 1e-9:                          # roll bars: no snares
        _break_bar(sc, bar, v=4, snares=False, ghosts=False)
        bar += 4.0
    _roll(sc, 192.0, 208.0, 55, 112)
    _toms8(sc, t0, t1, vel=70)
    _bass_eights(sc, t0, t1, 96)
    _arp_span(sc, t0, t1, 0.25, 70)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d) for d in (1, 2, 6, 2)],
                 span=8.0, size=4, lo=52, hi=76, vel=62, vel_end=70)
    for bar in range(176, 208, 4):                  # posts every bar
        _post_L(sc, bar + 2.0, vel=80)
        _post_R(sc, bar + 3.0, vel=82)
    # choir + strings enter
    for p, b, d in ((65, 176.0, 15.9), (72, 176.0, 15.9),
                    (69, 192.0, 15.9), (76, 192.0, 15.9)):
        sc.note(8, p, b, d, 62, jt=0, jv=2)
    for i, p in enumerate((77, 79, 81, 83)):
        sc.note(7, p, t0 + 8.0 * i, 7.9, 66 + 2 * i, jt=0, jv=2)
    # portamento swoop 1 (interval +12 under CC65)
    en.portamento_on(sc, 5, 197.5, time_cc=70)
    sc.note(5, 72, 197.6, 2.8, 92, jt=0, jv=0)
    sc.note(5, 84, 200.5, 5.5, 98, jt=0, jv=0)
    _bloom(sc, 5, 200.5, 5.5)
    en.portamento_off(sc, 5, 206.4)
    _duo_in(sc, t0, t1)
    _riser(sc, 204.0, 3.9, 92)
    _harp_run(sc, 208.0, vel0=70)
    _fills_in(sc, t0, t1)


def _b_drop1(sc):
    t0, t1 = DROP1
    bar = t0
    while bar < t1 - 1e-9:
        _floor_bar(sc, bar, v=0)
        bar += 4.0
    for b in (208.0, 240.0, 272.0):
        _crash(sc, b, vel=96)
    _bass_eights(sc, t0, t1, 98)
    _arp_span(sc, t0, t1, 0.25, 70)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d)
                             for d in (1, 2, 6, 5) * 5],
                 span=4.0, size=4, lo=52, hi=76, vel=66)
    for bar in range(208, 288, 8):
        _post_L(sc, bar + 2.0, vel=84)
    for bar in range(212, 288, 8):
        _post_R(sc, bar + 3.0, vel=84)
    for i, b in enumerate(range(208, 288, 16)):
        _hit(sc, float(b), CYCLE[i % 4], 106)
    # choir chords every 8 beats, following the cycle
    roots = [(65, 72), (67, 74), (62, 69), (67, 74)]
    for i in range(10):
        lo, hi = roots[i % 4]
        sc.note(8, lo, t0 + 8.0 * i, 7.9, 66, jt=0, jv=2)
        sc.note(8, hi, t0 + 8.0 * i, 7.9, 64, jt=0, jv=2)
    for i, p in enumerate((79, 81, 77, 79)):
        sc.note(7, p, 224.0 + 8.0 * i, 7.9, 70, jt=0, jv=2)
    sc.note(7, 81, 256.0, 15.9, 72, jt=0, jv=2)
    # saw soar (held, bloomed) over the second half
    sc.note(5, 81, 240.0, 8.0, 96, jt=0, jv=0)
    _bloom(sc, 5, 240.0, 8.0)
    sc.note(5, 79, 248.0, 4.0, 92, jt=0, jv=0)
    sc.note(5, 77, 252.0, 4.0, 90, jt=0, jv=0)
    _duo_in(sc, t0, t1)
    _fills_in(sc, t0, t1)


def _b_strip(sc):
    t0, t1 = STRIP
    _arp_span(sc, t0, t1, 0.5, 44)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d) for d in (1, 6, 1, 2)],
                 span=8.0, size=4, lo=52, hi=76, vel=50)
    for i, (deg, dur) in enumerate(((1, 7.5), (6, 7.5), (1, 7.5), (6, 7.5))):
        sc.note(2, en.pitch(BASS_BASE, MODE, deg), t0 + 8.0 * i, dur, 56,
                jt=0, jv=2)
    sc.note(8, 65, 288.0, 15.9, 54, jt=0, jv=2)     # low mm hum
    sc.note(8, 62, 304.0, 15.9, 52, jt=0, jv=2)
    for bar in range(288, 320, 8):                  # hat tick + soft kick
        sc.note(9, 36, float(bar), 0.3, 58, jt=0, jv=3)
        for k in range(4):
            sc.note(9, 42, bar + float(k), 0.2, 40, jt=0, jv=2)
    _riser(sc, 316.0, 3.8, 78)
    _harp_run(sc, 320.0, vel0=58)


def _b_groove2(sc):
    t0, t1 = GROOVE2
    _crash(sc, 320.0, vel=82)
    bar = t0
    while bar < t1 - 1e-9:
        v = int(round((bar - t0) / (t1 - t0) * 10))
        _break_bar(sc, bar, v=v, ride=(bar >= 336.0))
        _bass_riff_bar(sc, bar, v=v)
        bar += 4.0
    _arp_span(sc, 320.0, 352.0, 0.5, 62)
    _arp_span(sc, 352.0, 384.0, 0.5, 65)
    _arp_span(sc, 384.0, 400.0, 0.5, 68)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, _bar_deg(t0 + 4.0 * i))
                             for i in range(20)],
                 span=4.0, size=4, lo=52, hi=76, vel=54, vel_end=64)
    for bar in range(352, 400, 8):
        _post_L(sc, bar + 2.0, vel=78)
        _post_R(sc, bar + 3.0, vel=80)
    for bar in range(356, 400, 8):
        _post_R(sc, bar + 2.0, vel=78)
        _post_L(sc, bar + 3.0, vel=80)
    _hit(sc, 384.0, 1, 96)
    _hit(sc, 392.0, 2, 98)
    # pre-sweep saw approach
    for i, (p, b) in enumerate(((72, 376.0), (74, 378.0), (76, 380.0),
                                (77, 382.0))):
        sc.note(5, p, b, 1.9, 84 + 2 * i, jt=0, jv=0)
    _harp_run(sc, 400.0, vel0=68)
    _duo_in(sc, t0, t1)
    _fills_in(sc, t0, t1)


def _b_sweep2(sc):
    t0, t1 = SWEEP2
    _crash(sc, 400.0, vel=88)
    bar = t0
    while bar < 428.0 - 1e-9:
        _break_bar(sc, bar, v=6, ride=True)
        bar += 4.0
    while bar < t1 - 1e-9:
        _break_bar(sc, bar, v=6, snares=False, ghosts=False)
        bar += 4.0
    _roll(sc, 428.0, 434.0, 62, 84, step=0.5)      # two-stage roll
    _roll(sc, 434.0, 440.0, 88, 116)
    _toms8(sc, 416.0, t1, vel=66)
    _bass_eights(sc, t0, t1, 100)
    _arp_span(sc, t0, t1, 0.25, 72)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d) for d in (1, 2, 6, 2, 5)],
                 span=8.0, size=4, lo=52, hi=76, vel=64, vel_end=72)
    for i, bar in enumerate(range(400, 440, 4)):    # alternating posts
        if i % 2 == 0:
            _post_L(sc, bar + 2.0, vel=82)
        else:
            _post_R(sc, bar + 3.0, vel=84)
    for p, b, d in ((65, 400.0, 15.9), (72, 400.0, 15.9),
                    (67, 416.0, 15.9), (74, 416.0, 15.9),
                    (65, 432.0, 7.9), (72, 432.0, 7.9)):
        sc.note(8, p, b, d, 66, jt=0, jv=2)
    for i, p in enumerate((77, 79, 81, 83, 84)):
        sc.note(7, p, t0 + 8.0 * i, 7.9, 68 + 2 * i, jt=0, jv=2)
    # portamento swoop 2 (+12) and swoop 3 (+19, the big one)
    en.portamento_on(sc, 5, 403.5, time_cc=70)
    sc.note(5, 72, 403.6, 1.8, 92, jt=0, jv=0)
    sc.note(5, 84, 405.5, 4.5, 98, jt=0, jv=0)
    _bloom(sc, 5, 405.5, 4.5)
    en.portamento_off(sc, 5, 410.5)
    en.portamento_on(sc, 5, 427.5, time_cc=80)
    sc.note(5, 65, 427.6, 2.8, 94, jt=0, jv=0)
    sc.note(5, 84, 430.5, 8.5, 102, jt=0, jv=0)
    _bloom(sc, 5, 430.5, 8.5)
    en.portamento_off(sc, 5, 439.5)
    _duo_in(sc, t0, t1)
    _riser(sc, 436.0, 3.9, 104)
    _harp_run(sc, 440.0, vel0=72)
    _fills_in(sc, t0, t1)


def _b_drop2(sc):
    t0, t1 = DROP2
    bar = t0
    while bar < 536.0 - 1e-9:
        _floor_bar(sc, bar, v=8, sixteenth=True)
        for k in range(8):                          # tambourine shimmer
            sc.note(9, 54, bar + 0.25 + 0.5 * k, 0.15, 62, jt=0, jv=3)
        bar += 4.0
    while bar < 548.0 - 1e-9:
        _floor_bar(sc, bar, v=-6)
        bar += 4.0
    sc.note(9, 36, 548.0, 0.4, 96, jt=0, jv=0)
    for b in (440.0, 472.0, 504.0, 536.0, 548.0):
        _crash(sc, b, vel=98)
    _bass_eights(sc, t0, 548.0, 102)
    _arp_span(sc, t0, t1, 0.25, 74)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d)
                             for d in (1, 2, 6, 5) * 7],
                 span=4.0, size=4, lo=52, hi=76, vel=68)
    for bar in range(440, 552, 8):
        _post_L(sc, bar + 2.0, vel=86)
    for bar in range(444, 552, 8):
        _post_R(sc, bar + 3.0, vel=86)
    for i, b in enumerate(range(440, 536, 8)):
        _hit(sc, float(b), CYCLE[(i // 2) % 4], 110)
    roots = [(65, 72), (67, 74), (62, 69), (67, 74)]
    for i in range(12):
        lo, hi = roots[i % 4]
        sc.note(8, lo, t0 + 8.0 * i, 7.9, 70, jt=0, jv=2)
        sc.note(8, hi, t0 + 8.0 * i, 7.9, 68, jt=0, jv=2)
    sc.note(8, 65, 536.0, 13.9, 62, jt=0, jv=2)
    sc.note(8, 72, 536.0, 13.9, 60, jt=0, jv=2)
    for i, p in enumerate((81, 79, 83, 84, 81, 79, 83, 84)):
        sc.note(7, p, 460.0 + 8.0 * i, 7.9, 72, jt=0, jv=2)
    sc.note(7, 77, 524.0, 11.9, 68, jt=0, jv=2)
    # the pinned ASCENT statement — the album DNA, lead ship, F4
    material.play_ascent(sc, 14, ASCENT_BEAT, BASE, vel=106, jt=0)
    _bloom(sc, 14, ASCENT_BEAT + 1.5, 2.5)
    # saw counter-line (the verified counterpoint), then peak doubling
    for stmt in (460.0, 476.0):
        for rel, p, dur in COUNTER_REL:
            sc.note(5, p, stmt + rel, dur, 96, jt=0, jv=0)
    for p, b, d in ((89, 492.0, 3.9), (91, 500.0, 3.0), (91, 508.0, 3.9),
                    (93, 516.0, 3.0), (89, 520.0, 2.5)):
        sc.note(5, p, b, d, 98, jt=0, jv=0)
    _duo_in(sc, t0, t1)
    _riser(sc, 504.0, 3.8, 96)
    _harp_run(sc, 524.0, vel0=70)
    _harp_run(sc, 552.0, vel0=64)
    _fills_in(sc, t0, t1)


def _b_dissolve(sc):
    t0, t1 = OUTRO
    _arp_span(sc, 552.0, 584.0, 0.5, 48)
    _arp_span(sc, 584.0, 616.0, 0.5, 36)
    en.pad_block(sc, 1, t0, [en.triad(53, MODE, d)
                             for d in (1, 2, 6, 2, 1, 2, 1, 1)],
                 span=8.0, size=4, lo=52, hi=76, vel=54, vel_end=40)
    b = 552.0
    while b < 576.0 - 1e-9:
        sc.note(2, 41, b, 3.5, int(round(en.lerp(64, 46, (b - 552) / 24))),
                jt=0, jv=2)
        b += 4.0
    for bar in range(552, 576, 4):                  # kit fades
        sc.note(9, 36, float(bar), 0.3, 56, jt=0, jv=2)
        for k in range(8):
            sc.note(9, 42, bar + 0.5 * k, 0.2, 38, jt=0, jv=2)
    for p, b, d, v in ((77, 552.0, 6.0, 74), (74, 560.0, 6.0, 66),
                       (72, 568.0, 7.5, 58)):
        sc.note(5, p, b, d, v, jt=0, jv=0)
        _bloom(sc, 5, b, d)
    sc.note(8, 65, 556.0, 24.0, 52, jt=0, jv=2)     # vapour hum
    sc.note(8, 60, 584.0, 20.0, 46, jt=0, jv=2)
    for i in range(8):                              # falling harp trail
        sc.note(6, _dp(8 - i), 600.0 + 0.25 * i, 0.22, 58 - 2 * i,
                jt=0, jv=2)
    _fills_in(sc, t0, t1)


BUILDERS = [_b_shimmer, _b_groove1, _b_sweep1, _b_drop1, _b_strip,
            _b_groove2, _b_sweep2, _b_drop2, _b_dissolve]

# ---------------------------------------------------------------------------
# Verification config
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {1, 9, 29, 39, 45, 46, 49, 52, 55, 81, 89, 98,
                     117, 118, 119}
CENTERED_CHANNELS = {1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (60, 92), 1: (50, 78), 2: (33, 60), 3: (72, 96), 4: (57, 84),
    5: (55, 96), 6: (50, 90), 7: (48, 86), 8: (48, 80), 10: (44, 64),
    11: (46, 60), 12: (53, 77), 13: (60, 64), 14: (58, 88), 15: (50, 80),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (262.0, 275.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 set)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}


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


def _sounding_at(spans, tick, eps=24):
    """Pitches sounding at `tick`: on <= tick+eps, off > tick+eps."""
    return [p for on, off, p in spans if on <= tick + eps and off > tick + eps]


def _fill_lane_ons(sc):
    return sorted(_note_ons(sc, 10) + _note_ons(sc, 11))

# ---------------------------------------------------------------------------
# Track oracles — every HLD claim, falsifiable
# ---------------------------------------------------------------------------


def _o_duo_parallel_sixths(sc):
    """Formation SIXTHS: wing = lead - (8 or 9) for >= 80% of duo time,
    sampled on a half-beat grid wherever both ships sound."""
    fails = []
    lead = _note_spans(sc, 14)
    wing = _note_spans(sc, 15)
    if not lead or not wing:
        return ["a ship is silent"]
    both = ok = 0
    li = wi = 0
    lact, wact = [], []
    t = 64.25
    while t < END:
        tk = _tick(t)
        while li < len(lead) and lead[li][0] <= tk:
            lact.append(lead[li]); li += 1
        while wi < len(wing) and wing[wi][0] <= tk:
            wact.append(wing[wi]); wi += 1
        lact = [s for s in lact if s[1] > tk]
        wact = [s for s in wact if s[1] > tk]
        if lact and wact:
            both += 1
            iv = max(p for _o, _f, p in lact) - max(p for _o, _f, p in wact)
            if iv in (8, 9):
                ok += 1
        t += 0.5
    if both * 0.5 < 60.0:
        fails.append(f"duo flies together only {both * 0.5:.0f} beats "
                     f"(want >= 60)")
    frac = ok / max(1, both)
    if frac < 0.80:
        fails.append(f"parallel-sixth fraction {frac:.2f} < 0.80 "
                     f"({ok}/{both} samples)")
    return fails


def _o_cc74_macro_sweeps(sc):
    """>= 2 macro-sweeps on the pad: monotone rise >= 70 units then fall
    >= 55; the second sweep's rise strictly bigger (SWEEP2 > SWEEP1)."""
    fails = []
    rises = []
    for lo, hi in (SWEEP1, SWEEP2):
        vals = [v for t, v in _cc_lane(sc, 1, 74)
                if _tick(lo) <= t <= _tick(hi)]
        if len(vals) < 8:
            fails.append(f"sweep window {lo}-{hi}: only {len(vals)} CC74 events")
            continue
        peak = max(vals)
        m = vals.index(peak)
        if any(b < a for a, b in zip(vals[:m + 1], vals[1:m + 1])):
            fails.append(f"sweep {lo}-{hi}: rise not monotone")
        if any(b > a for a, b in zip(vals[m:], vals[m + 1:])):
            fails.append(f"sweep {lo}-{hi}: fall not monotone")
        rise, fall = peak - vals[0], peak - vals[-1]
        rises.append(rise)
        if rise < 70:
            fails.append(f"sweep {lo}-{hi}: rise {rise} < 70 units")
        if fall < 55:
            fails.append(f"sweep {lo}-{hi}: fall {fall} < 55 units")
    if len(rises) == 2 and rises[1] <= rises[0]:
        fails.append(f"SWEEP2 rise {rises[1]} must exceed SWEEP1 {rises[0]}")
    return fails


def _o_portamento_swoops(sc):
    """>= 2 swoops: CC65 on, consecutive saw notes leaping >= 12 semis;
    at least one inside SWEEP2."""
    fails = []
    lane = _cc_lane(sc, 5, 65)                     # (tick, value)
    spans, on_t = [], None
    for t, v in lane:
        if v >= 64 and on_t is None:
            on_t = t
        elif v < 64 and on_t is not None:
            spans.append((on_t, t)); on_t = None
    if on_t is not None:
        spans.append((on_t, _tick(END)))
    ons = _note_ons(sc, 5)
    swoops = []
    for lo, hi in spans:
        pitched = [(t, p) for t, p, _v in ons if lo <= t <= hi]
        for (t1, p1), (t2, p2) in zip(pitched, pitched[1:]):
            if abs(p2 - p1) >= 12:
                swoops.append((t1 / _PPQ, p1, p2))
    if len(swoops) < 2:
        fails.append(f"only {len(swoops)} portamento swoops (want >= 2)")
    if not any(SWEEP2[0] <= t <= SWEEP2[1] for t, _a, _b in swoops):
        fails.append("no swoop inside SWEEP2")
    return fails


def _o_breakbeat_not_four_floor(sc):
    """Grooves: kick displacement pinned to {0, 0.75, 2.5}; strong snares
    pinned to {1.0, 2.75}; four-on-floor therefore impossible there.
    Drops: kick floored on {0,1,2,3} every bar (the sanctioned contrast)."""
    fails = []
    kicks, snares = {}, {}
    for tick, p, v in _note_ons(sc, 9):
        if p == 36:
            kicks.setdefault(tick // (4 * _PPQ), set()).add(
                tick - (tick // (4 * _PPQ)) * 4 * _PPQ)
        elif p == 38 and v >= 80:
            snares.setdefault(tick // (4 * _PPQ), set()).add(
                tick - (tick // (4 * _PPQ)) * 4 * _PPQ)
    want_k = {0, int(0.75 * _PPQ), int(2.5 * _PPQ)}
    want_s = {_PPQ, int(2.75 * _PPQ)}
    for lo, hi in ((64.0, 176.0), (320.0, 400.0)):
        for bar in range(int(lo) // 4, int(hi) // 4):
            if kicks.get(bar, set()) != want_k:
                fails.append(f"groove bar at beat {bar * 4}: kicks "
                             f"{sorted(kicks.get(bar, set()))} != displaced "
                             f"pattern")
            if snares.get(bar, set()) != want_s:
                fails.append(f"groove bar at beat {bar * 4}: strong snares "
                             f"not the displaced {{1.0, 2.75}}")
    floor = {0, _PPQ, 2 * _PPQ, 3 * _PPQ}
    for lo, hi in ((208.0, 288.0), (440.0, 548.0)):
        for bar in range(int(lo) // 4, int(hi) // 4):
            if kicks.get(bar, set()) != floor:
                fails.append(f"drop bar at beat {bar * 4} not four-on-floor")
    return fails[:8]


def _o_double_time_hats(sc):
    """DROP2 rides double-time closed hats (>= 14/bar); DROP1 stays at
    eighths (<= 9/bar) — the 'DROP2 bigger' texture claim."""
    fails = []
    hats = {}
    for tick, p, _v in _note_ons(sc, 9):
        if p == 42:
            hats[tick // (4 * _PPQ)] = hats.get(tick // (4 * _PPQ), 0) + 1
    d1 = [hats.get(b, 0) for b in range(int(DROP1[0]) // 4, int(DROP1[1]) // 4)]
    d2 = [hats.get(b, 0) for b in range(int(DROP2[0]) // 4, 536 // 4)]
    if max(d1) > 9:
        fails.append(f"DROP1 closed hats reach {max(d1)}/bar (> 9)")
    if min(d2) < 14:
        fails.append(f"DROP2 closed hats fall to {min(d2)}/bar (< 14)")
    return fails


def _o_lydian_sharp4(sc):
    """The #4 (pc 11, B natural) is pinned into every plain hook statement
    (>= 3 onsets, one a full-beat B at rel 11.0) and used >= 40 times by the
    lead ship overall."""
    fails = []
    ons = _note_ons(sc, 14)
    spans = _note_spans(sc, 14)
    total_p11 = sum(1 for _t, p, _v in ons if p % 12 == 11)
    if total_p11 < 40:
        fails.append(f"lead ship states pc 11 only {total_p11} times (< 40)")
    for t0 in SHARP4_STATEMENTS:
        lo, hi = _tick(t0), _tick(t0 + 16.0)
        n11 = sum(1 for t, p, _v in ons if lo <= t < hi and p % 12 == 11)
        if n11 < 3:
            fails.append(f"hook at {t0}: only {n11} #4 onsets (< 3)")
        pin = _tick(t0 + 11.0)
        if not any(on == pin and p % 12 == 11 and off - on >= _tick(0.9)
                   for on, off, p in spans):
            fails.append(f"hook at {t0}: no full-beat #4 at rel 11.0")
    return fails[:8]


def _o_lydian_purity(sc):
    """No melodic lane may leave F lydian (bans Bb, Eb, ... entirely)."""
    fails = []
    for ch in (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 14, 15):
        for tick, p, _v in _note_ons(sc, ch):
            if p % 12 not in LYD_PCS:
                fails.append(f"ch{ch} pitch {p} at beat {tick / _PPQ:.2f} "
                             f"is not F lydian")
    return fails[:8]


def _o_build_drop_contour(sc):
    """Build windows strictly rising (both builds); DROP2 mean > DROP1 mean;
    the strip under 50% of DROP1."""
    fails = []
    sums = _bar_sums(sc)
    for name, windows in (("build1", BUILD1_WINDOWS),
                          ("build2", BUILD2_WINDOWS)):
        means = [_mean_barsum(sums, lo, hi) for lo, hi in windows]
        for i, (a, b) in enumerate(zip(means, means[1:])):
            if b <= a:
                fails.append(f"{name} window {i + 1}->{i + 2} not rising "
                             f"({a:.0f} -> {b:.0f})")
    d1 = _mean_barsum(sums, *DROP1)
    d2 = _mean_barsum(sums, *DROP2)
    strip = _mean_barsum(sums, *STRIP)
    if d2 <= d1:
        fails.append(f"DROP2 mean {d2:.0f} <= DROP1 mean {d1:.0f}")
    if strip >= 0.5 * d1:
        fails.append(f"strip mean {strip:.0f} >= 50% of DROP1 ({d1:.0f})")
    if _mean_barsum(sums, *BUILD2_WINDOWS[-1]) >= d2:
        fails.append("DROP2 does not top its own final build window")
    return fails


def _o_fill_escalation(sc):
    """Fill counts strictly rise through both builds, match the schedule
    exactly (lanes carry ONLY scheduled shapes), >= 5 distinct shapes per
    build, drop windows thinned to <= 12 fill notes."""
    fails = []
    ons = _fill_lane_ons(sc)

    def _count(lo, hi):
        return sum(1 for t, _p, _v in ons if _tick(lo) <= t < _tick(hi))

    def _sched(lo, hi):
        return sum(material.fill_note_count(s) for b, s in FILL_SCHEDULE
                   if lo <= b < hi)

    for name, windows in (("build1", BUILD1_FILL_WINDOWS),
                          ("build2", BUILD2_FILL_WINDOWS)):
        counts = [_count(lo, hi) for lo, hi in windows]
        for (lo, hi), got in zip(windows, counts):
            want = _sched(lo, hi)
            if got != want:
                fails.append(f"{name} {lo}-{hi}: {got} fill notes, "
                             f"schedule says {want}")
        if any(b <= a for a, b in zip(counts, counts[1:])):
            fails.append(f"{name} fill counts not strictly rising: {counts}")
    b1 = {s for b, s in FILL_SCHEDULE if 64.0 <= b < 208.0}
    b2 = {s for b, s in FILL_SCHEDULE if 320.0 <= b < 440.0}
    if len(b1) < 5 or len(b2) < 5:
        fails.append(f"build shape variety {len(b1)}/{len(b2)} (< 5)")
    for lo, hi in DROP_FILL_WINDOWS:
        c = _count(lo, hi)
        if c > 12:
            fails.append(f"drop window {lo}-{hi}: {c} fill notes (> 12, "
                         f"not thinned)")
    return fails[:8]


def _o_fill_chain_into_drops(sc):
    """A >= 20-note unbroken fill (gaps <= 0.5) lands INTO each drop."""
    fails = []
    ons = _fill_lane_ons(sc)
    for drop in (DROP1[0], DROP2[0]):
        w = sorted(t for t, _p, _v in ons
                   if _tick(drop - 4.1) <= t < _tick(drop))
        if len(w) < 20:
            fails.append(f"drop {drop}: only {len(w)} chain notes (< 20)")
            continue
        gaps = [(b - a) / _PPQ for a, b in zip(w, w[1:])]
        if max(gaps) > 0.51:
            fails.append(f"drop {drop}: chain broken (gap {max(gaps):.2f})")
        if w[-1] < _tick(drop - 0.3):
            fails.append(f"drop {drop}: chain stops {drop - w[-1] / _PPQ:.2f} "
                         f"beats early")
    return fails


def _o_autopan_transient_only(sc):
    """The moving pan rides ONLY the transient arp: ch0 sweeps wide, every
    ch0 note <= 0.62 beats; the posts hold their fixed L/R stations."""
    fails = []
    pans = [v for _b, v in _cc_lane(sc, 0, 10)]
    if len(pans) < 200 or min(pans) > 36 or max(pans) < 92:
        fails.append(f"ch0 autopan too tame ({len(pans)} events, "
                     f"{min(pans)}..{max(pans)})")
    for on, off, p in _note_spans(sc, 0):
        if off - on > _tick(0.62):
            fails.append(f"ch0 note at {on / _PPQ:.2f} lasts "
                         f"{(off - on) / _PPQ:.2f} beats — not transient")
            break
    for ch, want in ((3, 18), (4, 110)):
        vals = {v for _b, v in _cc_lane(sc, ch, 10)}
        if vals != {want}:
            fails.append(f"ch{ch} post moved off its station: {sorted(vals)}")
    return fails


def _o_counterpoint_drop2(sc):
    """DROP2's counterpoint window: saw line vs the duo — >= 50% of counter
    onsets non-coincident, >= 60% contrary+oblique, pairwise downbeat
    consonance across lead/wing/counter, pc doubling <= 25%."""
    fails = []
    lo, hi = COUNTER_WINDOW
    lead_spans = _note_spans(sc, 14)
    wing_spans = _note_spans(sc, 15)
    saw_spans = _note_spans(sc, 5)
    lead_ons = {t for t, _p, _v in _note_ons(sc, 14)}
    ctr = [(t, p) for t, p, _v in _note_ons(sc, 5)
           if _tick(lo) <= t < _tick(hi)]
    if len(ctr) < 6:
        return [f"only {len(ctr)} counter notes in {lo}-{hi}"]
    coinc = sum(1 for t, _p in ctr if t in lead_ons)
    if coinc / len(ctr) > 0.5:
        fails.append(f"{coinc}/{len(ctr)} counter onsets coincide with the "
                     f"lead (want < 50%)")

    def _ref_at(tick):
        cands = [(on, p) for on, off, p in lead_spans if on <= tick]
        return max(cands)[1] if cands else None

    good = 0
    pairs = list(zip(ctr, ctr[1:]))
    for (t1, p1), (t2, p2) in pairs:
        r1, r2 = _ref_at(t1), _ref_at(t2)
        dc, dr = p2 - p1, (r2 or 0) - (r1 or 0)
        if dc == 0 or dr == 0 or (dc > 0) != (dr > 0):
            good += 1
    if pairs and good / len(pairs) < 0.6:
        fails.append(f"contrary+oblique motion {good}/{len(pairs)} < 60%")
    for beat in range(int(lo) + 4, int(hi), 4):
        tk = _tick(float(beat))
        lines = [max(ps) for ps in
                 (_sounding_at(lead_spans, tk), _sounding_at(wing_spans, tk),
                  _sounding_at(saw_spans, tk)) if ps]
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                if abs(lines[i] - lines[j]) % 12 not in _CONSONANT:
                    fails.append(f"downbeat {beat}: {lines[i]} vs "
                                 f"{lines[j]} dissonant")
    doubled = 0
    for t, p in ctr:
        snd = _sounding_at(lead_spans, t)
        if snd and any(p % 12 == q % 12 for q in snd):
            doubled += 1
    if doubled / len(ctr) > 0.25:
        fails.append(f"pc doubling {doubled}/{len(ctr)} > 25%")
    return fails[:8]


def _o_ascent_pinned(sc):
    """The album ASCENT cell, verbatim from material.py, lead ship at 440."""
    fails = []
    spans = {(on, p): off for on, off, p in _note_spans(sc, 14)}
    for on, dur, semi in material.ASCENT_CELL:
        key = (_tick(ASCENT_BEAT + on), BASE + semi)
        if key not in spans:
            fails.append(f"ASCENT note {BASE + semi} missing at "
                         f"{ASCENT_BEAT + on}")
    hang = _tick(ASCENT_BEAT + 1.5)
    if not any(on == hang and p == BASE + 19 and off - on >= _tick(2.2)
               for on, off, p in _note_spans(sc, 14)):
        fails.append("ASCENT hang not held >= 2.2 beats")
    return fails


def _o_risers_into_drops(sc):
    fails = []
    ons = [t / _PPQ for t, _p, _v in _note_ons(sc, 13)]
    for drop in (DROP1[0], DROP2[0]):
        if not any(drop - 5.0 <= t <= drop - 1.0 for t in ons):
            fails.append(f"no riser into the drop at {drop}")
    if len(ons) < 5:
        fails.append(f"only {len(ons)} risers across the piece (< 5)")
    return fails


def _o_layers_at_climax(sc):
    lo, hi = _tick(DROP2[0]), _tick(DROP2[1])
    active = sum(1 for ch in sc.events
                 if any(lo <= t < hi for t, _p, _v in _note_ons(sc, ch)))
    if active < 15:
        return [f"only {active} channels sound inside DROP2 (want >= 15)"]
    return []


def oracles(sc, info, spans):
    return [
        ("duo_parallel_sixths", _o_duo_parallel_sixths(sc)),
        ("cc74_macro_sweeps", _o_cc74_macro_sweeps(sc)),
        ("portamento_swoops", _o_portamento_swoops(sc)),
        ("breakbeat_not_four_floor", _o_breakbeat_not_four_floor(sc)),
        ("double_time_hats_drop2", _o_double_time_hats(sc)),
        ("lydian_sharp4", _o_lydian_sharp4(sc)),
        ("lydian_purity", _o_lydian_purity(sc)),
        ("build_drop_contour", _o_build_drop_contour(sc)),
        ("fill_escalation", _o_fill_escalation(sc)),
        ("fill_chain_into_drops", _o_fill_chain_into_drops(sc)),
        ("autopan_transient_only", _o_autopan_transient_only(sc)),
        ("counterpoint_drop2", _o_counterpoint_drop2(sc)),
        ("ascent_pinned", _o_ascent_pinned(sc)),
        ("risers_into_drops", _o_risers_into_drops(sc)),
        ("layers_at_climax", _o_layers_at_climax(sc)),
    ]
