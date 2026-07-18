"""movements/t05_homeward.py — track 5 of *The Remaining*.

THE RETURN.  The album's full ensemble finally gathers.  A PROCESSION
assembles out of a low-D organ pedal, one voice per cycle (timpani, sub
drone, ensemble strings on the minor GROUND, harp, then the cello singing
the VIGIL THEME) — grief, but no longer alone.  THE TURNING pivots on a
single bare bar of open D (root and fifth, no third — neither major nor
minor) and then THE MAJOR GROUND enters, D-A-Bm-G, whose suspensions now
resolve UPWARD (the Richter sigh inverts into a lift); the tempo eases up
to 72.  ALL OF THEM, HOME stacks a machine-verified QUADRUPLE counterpoint
over the major ground — the piano's DEPARTURE FIGURE with its holes filled
at last, violin I's THEME in D major, the cello's THEME augmented x2, the
celesta's THEME diminished — all four sounding together, every downbeat a
consonance; and violin II returns to state the whole twelve-note DEPARTED
LINE verbatim, finishing the phrase interrupted in T1.  The choir opens to
"ah", the tubular bells peal the ground roots, and a long crescendo lifts
the tutti.  Then QUIET: everything falls away over eight bars, and the solo
piano states the THEME with its ARRIVAL — the album's one and only degree-1
ending, A-G-F#-G-F#-E-D in the major — settling onto a D-major-add9 chord in
which the waiting tone E is at last absorbed as a consonance.  Home.
Every structural device is oracle-pinned below against material.py.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 5
TITLE = "Homeward"
FILE = "05 - Homeward.mid"
SEED = 20261005
COMMENT = (
    "The return. The album's full ensemble assembles from a low organ pedal "
    "- timpani, drone, the minor ground, harp, the cello's theme - then turns "
    "on one bare bar of open D into the major ground, D-A-Bm-G, its sighs now "
    "rising. A quadruple counterpoint locks together over the major ground: "
    "the piano figure with its holes filled, the theme in D major, the theme "
    "augmented on cello and diminished on celesta, all four at once. Violin "
    "II returns and finishes the twelve-note phrase interrupted in track one. "
    "Then everything falls away, and the solo piano reaches the tonic the "
    "album withheld for twenty-five minutes - once - into a D-major-add9 in "
    "which the waiting tone finally comes home.")

# ---------------------------------------------------------------------------
# Channels.  Channel 9 is skipped (GM drum channel); no drums on this album.
# ---------------------------------------------------------------------------

PIANO, V1, V2, VLA, VC = 0, 1, 2, 3, 4
ENS, CHOIR, HARP, CEL = 5, 6, 7, 8
BELLS, TIMP, ORGAN, DRONE = 10, 11, 12, 13

BASE = en.n("D4")                       # 62 — the string-line / theme tonic
_MM = material.MODE_MINOR
_MJ = material.MODE_MAJOR

# ground roots (minor, procession) and (major, the turning + home)
ENS_MIN = material.ground_roots(en.n("D3"))                 # [50,46,53,48]
ENS_MAJ = material.ground_roots(en.n("D3"), major=True)     # [50,57,59,55]
MIN_MINORITY = [True, False, False, False]      # Dm minor; Bb/F/C major thirds
MAJ_MINORITY = [False, False, True, False]      # D/A/G major; Bm minor third

# the piano figure roots over the MAJOR ground (D-A-Bm-G)
PIANO_MAJ = [en.n("D3"), en.n("A2"), en.n("B2"), en.n("G2")]   # [50,45,47,43]

# theme bases per counterpoint voice (all in D, the recognizable motif)
VC_THEME_BASE = en.n("D3")              # 50 — cello, augmented x2
V1_THEME_BASE = en.n("D5")             # 74 — violin I, in tempo
CEL_THEME_BASE = en.n("D6")            # 86 — celesta music box, diminished
BELL_BASE = en.n("D5")                 # 74 — the peal register

# --- the pinned geometry of movement III -----------------------------------
# The major ground began at bar 25, so its D-bars fall where (bar-25)%4==0:
# bars 41, 45, ... The quadruple counterpoint runs one 4-bar unit [D,A,Bm,G]
# per D-bar, bars 41..84 (beats 164..340) — 11 units, 44 bars.
CP_D_BARS = list(range(41, 82, 4))      # [41,45,...,81] — the unit downbeats
CP_T0 = 164.0                           # counterpoint block start (bar 41)
CP_T1 = 340.0                           # ... ends (bar 84); then the peak
DEPARTED_T0 = 228.0                     # violin II returns (bar 57, a D-bar)

# --- the turning ----------------------------------------------------------
BARE_T0 = 96.0                          # one bar of bare open D (no third)
TURN_T0 = 100.0                         # the major ground enters here (keysig)

# --- movement IV (the arrival) --------------------------------------------
FALL_T0 = 352.0                         # the decrescendo begins
FALL_T1 = 384.0                         # ... over eight bars
IV_THEME_T0 = 392.0                     # the solo piano's theme
ARRIVAL_BEAT = IV_THEME_T0 + 8.0        # 400.0 — the degree-1 tonic lands
FINAL_CHORD_T0 = 408.0                  # the D-major-add9
END = 472.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Procession", 0.0, 96.0),
               ("II. The Turning", 96.0, 160.0),
               ("III. All of Them, Home", 160.0, 352.0),
               ("IV. Quiet", 352.0, END)],
    tempo_map=[(0.0, 63.0), (8.0, 65.0), (24.0, 62.0), (32.0, 66.0),
               (56.0, 63.0), (64.0, 66.0), (88.0, 63.0),
               (96.0, 66.0), (100.0, 68.0), (120.0, 65.0), (128.0, 70.0),
               (152.0, 68.0), (160.0, 72.0),
               (168.0, 70.0), (176.0, 73.0), (208.0, 71.0), (240.0, 74.0),
               (272.0, 72.0), (288.0, 74.0), (320.0, 72.0), (344.0, 73.0),
               (352.0, 66.0), (360.0, 62.0), (384.0, 56.0), (400.0, 52.0),
               (424.0, 49.0), (448.0, 47.0), (464.0, 46.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1), (TURN_T0, 2, 0)],       # D minor -> D major
    channels=[(PIANO, "piano", 0, 100, material.SEATING["piano"], 60),
              (V1, "violin I", 40, 94, material.SEATING["violin1"], 66),
              (V2, "violin II", 40, 94, material.SEATING["violin2"], 66),
              (VLA, "viola", 41, 92, material.SEATING["viola"], 64),
              (VC, "cello", 42, 96, material.SEATING["cello"], 64),
              (ENS, "ensemble", 48, 88, 64, 68),
              (CHOIR, "choir", 52, 84, material.SEATING["choir"], 70),
              (HARP, "harp", 46, 86, material.SEATING["harp"], 55),
              (CEL, "celesta", 8, 84, material.SEATING["celesta"], 55),
              (BELLS, "tubular bells", 14, 82, material.SEATING["bells"], 70),
              (TIMP, "timpani", 47, 88, material.SEATING["timpani"], 55),
              (ORGAN, "organ", 19, 86, material.SEATING["organ"], 70),
              (DRONE, "sub drone", 38, 84, material.SEATING["bass"], 45)],
    extra_markers=[(BARE_T0, "the bare fifth"), (TURN_T0, "the turning"),
                   (DEPARTED_T0, "the departed line returns"),
                   (ARRIVAL_BEAT, "the arrival")],
)

PROGRAM_WHITELIST = {0, 8, 14, 19, 38, 40, 41, 42, 46, 47, 48, 52}
CENTERED_CHANNELS = {PIANO, ENS, CHOIR, TIMP, ORGAN, DRONE}
NOTE_RANGES = {PIANO: (40, 84), V1: (60, 90), V2: (55, 84), VLA: (48, 78),
               VC: (36, 66), ENS: (45, 84), CHOIR: (48, 84), HARP: (38, 92),
               CEL: (72, 100), BELLS: (55, 90), TIMP: (36, 55),
               ORGAN: (26, 55), DRONE: (24, 40)}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (395.0, 470.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ
_TONIC_PC = BASE % 12                                # D = 2
_WAITING_PC = en.pitch(BASE, _MJ, material.THEME_END_DEG) % 12   # E = 4


# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES §2 pattern)
# ---------------------------------------------------------------------------

def _ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = d[0] & 0xF0
        if s == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                out.append((q.pop(0) / _PPQ, tick / _PPQ, d[1]))
    return sorted(out)


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for b, _p, v in _ons(sc, ch):
            out[int(b // 4)] = out.get(int(b // 4), 0.0) + v
    return out


def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))


def _sounding_pcs(sc, ch, beat, probe=0.125):
    """Pitch-classes the channel sounds just after `beat` (catches a note
    onsetting on the downbeat and any note sustained across it)."""
    t = beat + probe
    return {p % 12 for on, off, p in _spans(sc, ch) if on <= t < off}


def _theme_sig(mode):
    degs = [d for _on, _du, d in material.THEME]
    return tuple(en.deg_semis(mode, b) - en.deg_semis(mode, a)
                 for a, b in zip(degs, degs[1:]))


# ---------------------------------------------------------------------------
# Emitters — every oracle-pinned lane is jt=0 (tick-exact)
# ---------------------------------------------------------------------------

def _ground_bar(sc, ch, bar_t0, i, vel, major, body_gate=4.0):
    """One ensemble ground chord: the suspension on the barline resolving by
    step (down in minor, UP in major) on beat 2, over the held triad body."""
    roots = ENS_MAJ if major else ENS_MIN
    sus = material.MAJOR_SUSPENSIONS if major else material.SUSPENSIONS
    triad = material.ground_triad(en.n("D3"), i, major)
    root = roots[i]
    s, r = sus[i]
    sc.note(ch, root + s, bar_t0, 1.0, vel + 4, jt=0, jv=2)          # the sigh
    sc.note(ch, root + r, bar_t0 + 1.0, 3.0, vel, jt=0, jv=2)        # resolves
    for p in triad:
        if p % 12 not in ((root + s) % 12, (root + r) % 12):
            sc.note(ch, p, bar_t0, body_gate, max(1, vel - 8), jt=0, jv=2)


def _v1_home(sc, t0, vel):
    """Violin I over one 4-bar major-ground unit [D,A,Bm,G] starting on the
    D-bar `t0`: a held major third, the THEME across the A+B bars (ending on
    the waiting tone E), then the E sustained over the G-bar — every downbeat
    a consonance, the line sounding continuously."""
    base = V1_THEME_BASE
    sc.note(V1, base + 4, t0, 3.9, vel, jt=0, jv=0)                 # F# over D
    material.play_theme(sc, V1, t0 + 4.0, base, mode=_MJ,
                        vel=vel + 4, vel_end=vel + 8, jt=0, jv=0)   # A,B bars
    sc.note(V1, base + 2, t0 + 12.0, 3.9, vel, jt=0, jv=0)         # E over G


def _cel_home(sc, t0, vel):
    """Celesta music box over one 4-bar unit: the THEME diminished on the D
    and A bars, ringing on the waiting tone E over the B and G bars."""
    material.play_theme(sc, CEL, t0, CEL_THEME_BASE, mode=_MJ,
                        stretch=0.5, vel=vel, jt=0, jv=0)
    material.play_theme(sc, CEL, t0 + 4.0, CEL_THEME_BASE, mode=_MJ,
                        stretch=0.5, vel=vel, jt=0, jv=0)
    sc.note(CEL, CEL_THEME_BASE + 2, t0 + 8.0, 3.9, vel - 2, jt=0, jv=0)
    sc.note(CEL, CEL_THEME_BASE + 2, t0 + 12.0, 3.9, vel - 2, jt=0, jv=0)


def _timp_roll(sc, t0, n, dur, v0, v1, pitch=en.n("D2")):
    """A soft timpani roll — the procession's tread, never a march."""
    step = dur / n
    for k in range(n):
        v = round(en.lerp(v0, v1, k / max(1, n - 1)))
        sc.note(TIMP, pitch, t0 + k * step, step * 0.9, v, jt=1, jv=2)


def _organ_pedal(sc, t0, t1, v0, v1, pitch=en.n("D2")):
    """The low-D church-organ pedal, re-struck every 8 beats so it breathes
    without ever letting go of the floor."""
    b = t0
    while b < t1 - 1e-9:
        d = min(8.0, t1 - b)
        sc.note(ORGAN, pitch, b, d, round(en.lerp(v0, v1, (b - t0) /
                max(1.0, t1 - t0))), jt=0, jv=0)
        b += 8.0


# ---------------------------------------------------------------------------
# I. Procession [0, 96) — the minor ground assembles, one voice per cycle
# ---------------------------------------------------------------------------

def _b_procession(sc):
    # cycle 0 [0,16): the organ pedal alone — the floor
    _organ_pedal(sc, 0.0, 96.0, 32, 46)
    en.expr_curve(sc, ORGAN, [(0.0, 60), (48.0, 82), (95.0, 92)], step=4.0)

    # cycle 1 [16,32): soft timpani rolls enter (tonic, then dominant)
    for bar in range(4, 24):
        t0 = 4.0 * bar
        pitch = en.n("D2") if bar % 4 != 1 else en.n("A2")
        _timp_roll(sc, t0, 6, 1.5, 24 + (bar - 4) // 2, 34 + (bar - 4) // 2,
                   pitch)
    en.expr_curve(sc, TIMP, [(16.0, 54), (56.0, 74), (95.0, 84)], step=4.0)

    # cycle 2 [32,48): the sub drone joins, D1
    b = 32.0
    while b < 96.0 - 1e-9:
        sc.note(DRONE, en.n("D1"), b, 8.0, 30 + int((b - 32.0) // 16),
                jt=0, jv=0)
        b += 8.0
    en.expr_curve(sc, DRONE, [(32.0, 44), (64.0, 60), (95.0, 68)], step=4.0)

    # cycle 3 [48,64): the ensemble states the MINOR ground with its sighs
    for bar in range(12, 24):
        _ground_bar(sc, ENS, 4.0 * bar, bar % 4, 40 + (bar - 12), major=False)
    en.expr_curve(sc, ENS, [(48.0, 60), (72.0, 78), (95.0, 86)], step=4.0)

    # cycle 4 [64,80): the harp arpeggiates the ground (rising energy)
    for bar in range(16, 24):
        i = bar % 4
        triad = material.ground_triad(en.n("D4"), i, major=False)
        notes = triad + [triad[0] + 12, triad[1] + 12]
        for k in range(8):
            sc.note(HARP, notes[k % len(notes)], 4.0 * bar + 0.5 * k, 0.45,
                    40 + k + 2 * (bar - 16), jt=0, jv=2)
    en.expr_curve(sc, HARP, [(64.0, 62), (80.0, 82), (95.0, 88)], step=2.0)

    # cycle 5 [80,96): the cello sings the VIGIL THEME (augmented x2, minor),
    # ending on the waiting tone E — home is still one movement away
    material.play_theme(sc, VC, 80.0, VC_THEME_BASE, mode=_MM, stretch=2.0,
                        vel=52, vel_end=60, jt=0, jv=0)
    for on, du, deg in material.theme_notes(stretch=2.0):
        if du >= 3.5:
            en.vibrato(sc, VC, 80.0 + on + 0.6, du - 1.2, depth=0.18)
    en.expr_curve(sc, VC, [(80.0, 56), (88.0, 84), (95.0, 66)], step=1.0)
    sc.bend(VC, 95.6, 0.0)                          # recentre before II


TURN_BAR0 = 25                                       # bar of the first D major


# ---------------------------------------------------------------------------
# II. The Turning [96, 160) — one bare bar of open D, then the MAJOR ground
# ---------------------------------------------------------------------------

def _b_turning(sc):
    # the pedal and drone hold the tonic through the pivot
    _organ_pedal(sc, 96.0, 160.0, 46, 54)
    en.expr_curve(sc, ORGAN, [(96.0, 84), (128.0, 88), (159.0, 92)], step=4.0)
    b = 96.0
    while b < 160.0 - 1e-9:
        sc.note(DRONE, en.n("D1"), b, 8.0, 34 + int((b - 96.0) // 24),
                jt=0, jv=0)
        b += 8.0
    en.expr_curve(sc, DRONE, [(96.0, 66), (128.0, 72), (159.0, 76)], step=4.0)

    # --- the bare fifth [96,100): open D, NOT a single third anywhere -------
    sc.note(ENS, en.n("D3"), 96.0, 4.0, 46, jt=0, jv=1)
    sc.note(ENS, en.n("A3"), 96.0, 4.0, 44, jt=0, jv=1)
    sc.note(VC, en.n("D2"), 96.0, 4.0, 44, jt=0, jv=0)
    sc.note(VLA, en.n("A4"), 96.0, 4.0, 40, jt=0, jv=0)
    _timp_roll(sc, 96.0, 6, 2.0, 30, 40)
    en.expr_curve(sc, ENS, [(96.0, 62), (98.0, 78), (99.5, 60)], step=0.5)

    # --- the MAJOR ground [100,160): sighs now resolve UPWARD ---------------
    for bar in range(TURN_BAR0, 40):
        i = (bar - TURN_BAR0) % 4
        t0 = 4.0 * bar
        vel = 44 + (bar - TURN_BAR0)
        _ground_bar(sc, ENS, t0, i, min(66, vel), major=True)
        sc.note(VC, ENS_MAJ[i] - 12, t0, 3.9, min(60, 42 + (bar - TURN_BAR0)),
                jt=0, jv=1)                                     # the bass root
        _timp_roll(sc, t0, 4, 1.0, 26, 34)
    en.expr_curve(sc, ENS, [(100.0, 66), (128.0, 82), (159.0, 90)], step=4.0)
    en.expr_curve(sc, VC, [(100.0, 60), (130.0, 76), (159.0, 70)], step=4.0)
    en.expr_curve(sc, TIMP, [(100.0, 56), (140.0, 72), (159.0, 78)], step=4.0)

    # viola inner third + harp arpeggios lift the major ground
    for bar in range(TURN_BAR0, 40):
        i = (bar - TURN_BAR0) % 4
        triad = material.ground_triad(en.n("D4"), i, major=True)
        sc.note(VLA, triad[1], 4.0 * bar + 1.0, 2.9,
                40 + (bar - TURN_BAR0) // 2, jt=0, jv=1)        # the third
        for k in range(8):
            sc.note(HARP, (triad + [triad[0] + 12, triad[2] + 12])[k % 5],
                    4.0 * bar + 0.5 * k, 0.9,
                    38 + k + (bar - TURN_BAR0) // 2, jt=2, jv=2)
    en.expr_curve(sc, HARP, [(100.0, 66), (140.0, 84), (159.0, 90)], step=4.0)
    en.expr_curve(sc, VLA, [(100.0, 52), (140.0, 66), (159.0, 70)], step=4.0)

    # the choir gathers on a closed vowel (never "ah" yet — that waits for III)
    for cyc in range(4):
        t0 = 100.0 + 16.0 * cyc
        sc.note(CHOIR, en.n("D4"), t0, 15.5, 34 + 3 * cyc, jt=0, jv=1)
        sc.note(CHOIR, en.n("A4"), t0, 15.5, 30 + 3 * cyc, jt=0, jv=1)
    en.vowel_curve(sc, CHOIR, [(100.0, 12), (140.0, 34), (159.0, 46)], step=4.0)
    en.expr_curve(sc, CHOIR, [(100.0, 48), (140.0, 66), (159.0, 72)], step=4.0)
    sc.bend(VLA, 159.5, 0.0)
    sc.bend(VC, 159.5, 0.0)


def _gi(bar):
    """The major-ground chord index for a bar (D,A,Bm,G walk from bar 25)."""
    return (bar - TURN_BAR0) % 4


# ---------------------------------------------------------------------------
# III. All of Them, Home [160, 352) — the harmonic bed under the counterpoint
# ---------------------------------------------------------------------------

def _b_home_bed(sc):
    # organ pedal + sub drone hold the home tonic under everything
    _organ_pedal(sc, 160.0, 352.0, 54, 70)
    en.expr_curve(sc, ORGAN, [(160.0, 92), (300.0, 104), (351.0, 110)],
                  step=8.0)
    b = 160.0
    while b < 352.0 - 1e-9:
        sc.note(DRONE, en.n("D1"), b, 8.0, 36 + int((b - 160.0) // 40),
                jt=0, jv=0)
        b += 8.0
    en.expr_curve(sc, DRONE, [(160.0, 76), (300.0, 88), (351.0, 92)], step=8.0)

    # the ensemble major ground, sighs rising, through the whole movement
    for bar in range(40, 88):
        vel = min(74, 46 + (bar - 40) * 3 // 5)
        _ground_bar(sc, ENS, 4.0 * bar, _gi(bar), vel, major=True)
    en.expr_curve(sc, ENS, [(160.0, 74), (280.0, 92), (340.0, 104),
                            (351.0, 100)], step=8.0)

    # the tubular bells peal the ground roots (bars 40..84)
    for bar in range(40, 85):
        i = _gi(bar)
        bell = en.pitch(BELL_BASE, _MJ, material.MAJOR_GROUND_DEGREES[i])
        sc.note(BELLS, bell, 4.0 * bar, 3.8, min(74, 40 + (bar - 40) * 4 // 5),
                jt=0, jv=1)
    en.expr_curve(sc, BELLS, [(160.0, 70), (300.0, 92), (339.0, 100)],
                  step=8.0)

    # the choir opens — the album's first "ah" — on a luminous tonic pedal
    b = 160.0
    while b < 352.0 - 1e-9:
        v = min(78, 40 + int((b - 160.0) // 12))
        sc.note(CHOIR, en.n("D4"), b, 8.0, v, jt=0, jv=1)
        sc.note(CHOIR, en.n("D5"), b, 8.0, v - 4, jt=0, jv=1)
        b += 8.0
    en.vowel_curve(sc, CHOIR, [(160.0, 48), (208.0, 72), (260.0, 92),
                               (351.0, 104)], step=8.0)     # >= 80 = "ah"
    en.expr_curve(sc, CHOIR, [(160.0, 72), (300.0, 92), (351.0, 98)], step=8.0)

    # viola inner third + harp arpeggios thicken the bed (not the counterpoint)
    for bar in range(40, 88):
        i = _gi(bar)
        triad = material.ground_triad(en.n("D4"), i, major=True)
        sc.note(VLA, triad[1], 4.0 * bar, 3.9, min(66, 44 + (bar - 40) // 2),
                jt=0, jv=1)
        for k in range(8):
            p = (triad + [triad[0] + 12, triad[2] + 12])[k % 5]
            sc.note(HARP, p, 4.0 * bar + 0.5 * k, 0.9,
                    min(76, 44 + k + (bar - 40) // 2), jt=2, jv=2)
    en.expr_curve(sc, VLA, [(160.0, 60), (300.0, 76), (351.0, 78)], step=8.0)
    en.expr_curve(sc, HARP, [(160.0, 72), (300.0, 90), (351.0, 94)], step=8.0)
    sc.bend(VLA, 351.5, 0.0)


def _b_home_cp(sc):
    """The QUADRUPLE counterpoint (bars 41..84) + violin II's returning line
    + the tutti peak."""
    for u, bar in enumerate(CP_D_BARS):
        t0 = 4.0 * bar
        pv = min(82, 55 + u * 3)
        # (a) the piano DEPARTURE FIGURE, its holes FILLED, one bar each
        for db in range(4):
            b2 = bar + db
            i = _gi(b2)
            material.play_figure(sc, PIANO, 4.0 * b2, PIANO_MAJ[i],
                                 minor=MAJ_MINORITY[i], vel=pv, vel_end=pv + 4,
                                 holes=frozenset(), jt=0, jv=2)
            en.sustain(sc, PIANO, 4.0 * b2, 4.0 * b2 + 3.9)
        # (b) violin I — the THEME in D major
        _v1_home(sc, t0, min(72, 52 + u * 2))
        # (c) cello — the THEME augmented x2
        material.play_theme(sc, VC, t0, VC_THEME_BASE, mode=_MJ, stretch=2.0,
                            vel=min(72, 50 + u * 2),
                            vel_end=min(76, 54 + u * 2), jt=0, jv=0)
        # (d) celesta — the THEME diminished
        _cel_home(sc, t0, min(70, 48 + u * 2))
    en.expr_curve(sc, PIANO, [(164.0, 80), (300.0, 98), (339.0, 106)], step=8.0)
    en.expr_curve(sc, V1, [(164.0, 72), (300.0, 92), (339.0, 98)], step=8.0)
    en.expr_curve(sc, VC, [(164.0, 70), (300.0, 90), (339.0, 94)], step=8.0)
    en.expr_curve(sc, CEL, [(164.0, 66), (300.0, 84), (339.0, 88)], step=8.0)
    sc.bend(V1, 351.5, 0.0)
    sc.bend(VC, 351.5, 0.0)

    # --- violin II RETURNS: the whole 12-note DEPARTED LINE, verbatim -------
    material.play_departed(sc, V2, DEPARTED_T0, BASE, mode=_MM, count=None,
                          vel=70, jt=0, jv=0)
    for on, du, _deg in material.DEPARTED_LINE:
        if du >= 2.0:
            en.vibrato(sc, V2, DEPARTED_T0 + on + 0.5, du - 1.0, depth=0.24)
    en.expr_curve(sc, V2, [(DEPARTED_T0, 58), (DEPARTED_T0 + 7.0, 94),
                           (DEPARTED_T0 + 15.5, 64)], step=1.0)
    sc.bend(V2, 351.5, 0.0)

    # --- the peak [340,352): the full ensemble lands home in D major --------
    for k, p in enumerate((50, 54, 57, 62, 66, 69)):        # rolled D major
        sc.note(PIANO, p, 340.0 + 0.04 * k, 11.0, 72, jt=0, jv=1)
    en.sustain(sc, PIANO, 340.0, 351.5)
    sc.note(V1, en.n("A5"), 340.0, 11.0, 68, jt=0, jv=0)
    en.vibrato(sc, V1, 341.0, 9.0, depth=0.3)
    sc.note(VC, en.n("D3"), 340.0, 11.0, 66, jt=0, jv=0)
    for k, deg in enumerate((1, 3, 5, 8)):                  # celesta flourish
        sc.note(CEL, en.pitch(CEL_THEME_BASE, _MJ, deg), 340.0 + 0.5 * k,
                8.0 - 0.5 * k, 62, jt=0, jv=1)
    sc.note(BELLS, en.n("D5"), 340.0, 10.0, 76, jt=0, jv=1)
    _timp_roll(sc, 340.0, 10, 3.5, 30, 52)
    sc.note(TIMP, en.n("D2"), 343.5, 4.0, 54, jt=0, jv=1)
    en.expr_curve(sc, TIMP, [(340.0, 70), (348.0, 84), (351.0, 78)], step=1.0)
    sc.bend(V1, 351.6, 0.0)


def _b_home(sc):
    _b_home_bed(sc)
    _b_home_cp(sc)


IV_THEME_BASE = en.n("D4")              # 62 — the solo piano's arrival register


# ---------------------------------------------------------------------------
# IV. Quiet [352, 472) — everything falls away; the solo piano reaches home
# ---------------------------------------------------------------------------

def _b_quiet(sc):
    # the soft floor holds under the whole movement (no global silence)
    _organ_pedal(sc, 352.0, 418.0, 58, 28)
    en.expr_curve(sc, ORGAN, [(352.0, 96), (384.0, 60), (417.0, 30)], step=4.0)
    b = 352.0
    while b < 418.0 - 1e-9:
        sc.note(DRONE, en.n("D1"), b, 8.0, 34 - int((b - 352.0) // 24),
                jt=0, jv=0)
        b += 8.0
    en.expr_curve(sc, DRONE, [(352.0, 80), (384.0, 50), (417.0, 26)], step=4.0)

    # --- the decrescendo [352,384): the ensemble falls away, staggered ------
    for bar in range(88, 92):                              # ensemble -> 368
        _ground_bar(sc, ENS, 4.0 * bar, _gi(bar), 58 - 6 * (bar - 88),
                    major=True, body_gate=3.9)
    en.expr_curve(sc, ENS, [(352.0, 92), (360.0, 66), (367.5, 40)], step=2.0)
    for bar in range(88, 91):                              # viola -> 364
        sc.note(VLA, material.ground_triad(en.n("D4"), _gi(bar), True)[1],
                4.0 * bar, 3.8, 52 - 6 * (bar - 88), jt=0, jv=1)
    en.expr_curve(sc, VLA, [(352.0, 84), (360.0, 56), (363.5, 34)], step=2.0)
    for bar in range(88, 90):                              # bells -> 360
        i = _gi(bar)
        sc.note(BELLS, en.pitch(BELL_BASE, _MJ, material.MAJOR_GROUND_DEGREES[i]),
                4.0 * bar, 3.6, 48 - 8 * (bar - 88), jt=0, jv=1)
    for bar in range(88, 91):                              # harp -> 364
        triad = material.ground_triad(en.n("D4"), _gi(bar), True)
        for k in range(6):
            sc.note(HARP, (triad + [triad[0] + 12])[k % 4], 4.0 * bar + 0.5 * k,
                    0.9, 50 - 6 * (bar - 88) - k, jt=2, jv=2)
    for cyc in range(3):                                   # choir -> 376
        t0 = 352.0 + 8.0 * cyc
        v = 60 - 12 * cyc
        sc.note(CHOIR, en.n("D4"), t0, 7.8, v, jt=0, jv=1)
        sc.note(CHOIR, en.n("D5"), t0, 7.8, v - 4, jt=0, jv=1)
    en.vowel_curve(sc, CHOIR, [(352.0, 100), (376.0, 70)], step=4.0)
    en.expr_curve(sc, CHOIR, [(352.0, 90), (368.0, 54), (375.5, 30)], step=2.0)
    _timp_roll(sc, 352.0, 8, 3.0, 34, 20)                  # a last soft tread
    sc.bend(VLA, 383.5, 0.0)

    # --- the solo piano: the THEME with its ARRIVAL (the album's one home) ---
    en.soft_pedal(sc, PIANO, 388.0, 471.0)                 # una corda
    material.play_theme(sc, PIANO, IV_THEME_T0, IV_THEME_BASE, mode=_MJ,
                        vel=46, vel_end=44, arrival=True, jt=0, jv=0)
    for on, du, _deg in material.theme_notes(arrival=True):
        en.sustain(sc, PIANO, IV_THEME_T0 + on, IV_THEME_T0 + on + du * 0.95)
    en.expr_curve(sc, PIANO, [(IV_THEME_T0, 70), (ARRIVAL_BEAT, 82),
                              (ARRIVAL_BEAT + 4.0, 66)], step=1.0)

    # --- the final D-major-add9: the waiting tone E absorbed as a consonance -
    chord = [en.n("D3"), en.n("A3"), en.n("D4"), en.n("F#4"), en.n("A4"),
             en.n("E5")]                                   # D-F#-A + the add9 E
    for k, p in enumerate(chord):
        sc.note(PIANO, p, FINAL_CHORD_T0 + 0.05 * k, 62.0, 44, jt=0, jv=1)
    en.sustain(sc, PIANO, FINAL_CHORD_T0, 470.0)
    # a soft string + choir glow gives the chord its long decay
    for p, v in ((en.n("D3"), 34), (en.n("A3"), 30), (en.n("F#4"), 30),
                 (en.n("E5"), 26)):
        sc.note(ENS, p, FINAL_CHORD_T0, 62.0, v, jt=0, jv=0)
    sc.note(CHOIR, en.n("D4"), FINAL_CHORD_T0, 62.0, 30, jt=0, jv=0)
    sc.note(CHOIR, en.n("F#4"), FINAL_CHORD_T0, 62.0, 26, jt=0, jv=0)
    en.vowel(sc, CHOIR, 100, FINAL_CHORD_T0)               # "ah", at home
    en.expr_curve(sc, ENS, [(FINAL_CHORD_T0, 60), (430.0, 44), (470.0, 12)],
                  step=4.0)
    en.expr_curve(sc, CHOIR, [(FINAL_CHORD_T0, 58), (430.0, 42), (470.0, 10)],
                  step=4.0)
    en.expr_curve(sc, PIANO, [(FINAL_CHORD_T0, 84), (440.0, 60), (470.0, 18)],
                  step=4.0)


BUILDERS = [_b_procession, _b_turning, _b_home, _b_quiet]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _o_turning(sc):
    """The pivot: one bare bar of open D (no third anywhere), then the MAJOR
    ground D-A-Bm-G whose sighs resolve UPWARD onto the third."""
    fails = []
    # --- the bare fifth [96,100): only D and A sound, never a third --------
    for ch in sorted(sc.events):
        for on, off, p in _spans(sc, ch):
            if on < BARE_T0 + 4.0 - 1e-9 and off > BARE_T0 + 1e-9:
                if p % 12 not in (2, 9):                # D, A
                    fails.append(f"bare bar: ch{ch} sounds pc {p % 12} "
                                 f"(must be only D or A — no third)")
    # --- the major root walk [1,5,6,4] -------------------------------------
    want_roots = [en.pitch(en.n("D3"), _MJ, d)
                  for d in material.MAJOR_GROUND_DEGREES]
    if material.MAJOR_GROUND_DEGREES != [1, 5, 6, 4]:
        fails.append("the major ground walk is not [1,5,6,4]")
    if ENS_MAJ != want_roots:
        fails.append(f"ensemble major roots {ENS_MAJ} != {want_roots}")
    ens_ons = _ons(sc, ENS)
    for bar in range(TURN_BAR0, 88):
        i = (bar - TURN_BAR0) % 4
        t0 = 4.0 * bar
        here = [p for b, p, _v in ens_ons if abs(b - t0) < 1e-6]
        if want_roots[i] not in here:
            fails.append(f"bar {bar}: ground root {want_roots[i]} absent "
                         f"(walk index {i})")
    # --- the sighs now RISE by step onto the third -------------------------
    seen = set()
    for bar in range(TURN_BAR0, 88):
        i = (bar - TURN_BAR0) % 4
        s, r = material.MAJOR_SUSPENSIONS[i]
        root = ENS_MAJ[i]
        t0 = 4.0 * bar
        sus = [p for b, p, _v in ens_ons if abs(b - t0) < 1e-6 and p == root + s]
        res = [p for b, p, _v in ens_ons
               if abs(b - (t0 + 1.0)) < 1e-6 and p == root + r]
        if not sus or not res:
            fails.append(f"bar {bar}: the suspension {(s, r)} is not stated")
            continue
        if not 1 <= r - s <= 2:
            fails.append(f"chord {i}: sigh {s}->{r} must RISE by step")
        third = material.ground_triad(en.n("D3"), i, major=True)[1] % 12
        if (root + r) % 12 != third:
            fails.append(f"chord {i}: rising sigh must land on the third")
        seen.add(i)
    for i in range(4):
        if i not in seen:
            fails.append(f"major suspension {i} never sounds")
    return fails[:8]


def _theme_at(sc, ch, t0, base, mode, stretch, tag):
    """Assert `ch` states the theme (optionally stretched) at t0 — pitches
    and onsets exact against material.  Returns a list of failures."""
    fails = []
    ons = _ons(sc, ch)
    for on, _du, deg in material.theme_notes(stretch=stretch):
        wb, wp = t0 + on, en.pitch(base, mode, deg)
        m = [p for b, p, _v in ons if abs(b - wb) < 1e-6]
        if wp not in m:
            fails.append(f"{tag} @ {t0:.0f}: note at {wb:.1f} is {m}, "
                         f"want {wp} (deg {deg})")
    return fails


def _o_quadruple(sc):
    """Four independent lines over the major ground — piano figure, violin I
    theme, cello theme augmented, celesta theme diminished — sounding together
    for >= 8 bars, every downbeat a consonance against the ground root."""
    fails = []
    simultaneous = 0
    for bar in range(41, 85):
        root_pc = ENS_MAJ[_gi(bar)] % 12
        t0 = 4.0 * bar
        alive = True
        for ch in (PIANO, V1, VC, CEL):
            pcs = _sounding_pcs(sc, ch, t0)
            if not pcs:
                alive = False
                continue
            for pc in pcs:
                if (pc - root_pc) % 12 not in _CONSONANT:
                    fails.append(f"bar {bar}: ch{ch} pc {pc} dissonant over "
                                 f"root pc {root_pc}")
        if alive:
            simultaneous += 1
    if simultaneous < 8:
        fails.append(f"only {simultaneous} bars with all four lines sounding "
                     f"(want >= 8)")
    # the counterpoint CONTENT: each unit states its transform of the theme
    for bar in CP_D_BARS:
        t0 = 4.0 * bar
        fails += _theme_at(sc, V1, t0 + 4.0, V1_THEME_BASE, _MJ, 1.0, "vln I")
        fails += _theme_at(sc, VC, t0, VC_THEME_BASE, _MJ, 2.0, "cello aug")
        fails += _theme_at(sc, CEL, t0, CEL_THEME_BASE, _MJ, 0.5, "celesta")
    return fails[:8]


def _o_departed(sc):
    """Violin II returns and states the whole 12-note DEPARTED LINE verbatim
    — the same material T1 pinned its interrupted first seven to."""
    fails = []
    want = [(DEPARTED_T0 + on, en.pitch(BASE, _MM, deg))
            for on, _du, deg in material.DEPARTED_LINE]
    got = [(b, p) for b, p, _v in _ons(sc, V2)]
    if len(got) != len(material.DEPARTED_LINE):
        fails.append(f"violin II has {len(got)} note-ons, want exactly 12 "
                     f"(the whole departed line)")
    for i, ((wb, wp), (gb, gp)) in enumerate(zip(want, got)):
        if abs(wb - gb) > 1e-6 or wp != gp:
            fails.append(f"departed note {i}: got ({gb:.3f},{gp}) want "
                         f"({wb:.3f},{wp})")
    # the first seven are exactly what T1 interrupted on
    if got[:material.INTERRUPT_AFTER] != want[:material.INTERRUPT_AFTER]:
        fails.append("the first seven notes do not match T1's interruption")
    return fails[:8]


def _o_holes_filled(sc):
    """Every piano figure in III is WHOLE again — all eight quavers, the holes
    {3,6} filled for the first time since T1's departure."""
    fails = []
    for bar in range(41, 85):
        i = _gi(bar)
        root, offs = PIANO_MAJ[i], material.figure_offsets(MAJ_MINORITY[i])
        t0 = 4.0 * bar
        ons = [(round((b - t0) / 0.5), p) for b, p, _v in _ons(sc, PIANO)
               if t0 - 1e-9 <= b < t0 + 4.0 - 1e-9]
        quavers = {q for q, _p in ons}
        if quavers != set(range(8)):
            fails.append(f"bar {bar}: quavers {sorted(quavers)} — the figure "
                         f"is not whole (holes must be filled)")
        for qi, off in enumerate(offs):
            if (qi, root + off) not in ons:
                fails.append(f"bar {bar} quaver {qi}: want pitch {root + off}")
    return fails[:8]


def _bar_sums_ex(sc, skip):
    out = {}
    for ch in sc.events:
        if ch in skip:
            continue
        for b, _p, v in _ons(sc, ch):
            out[int(b // 4)] = out.get(int(b // 4), 0.0) + v
    return out


def _o_crescendo(sc):
    """A long crescendo across the counterpoint (bars 41..84): the windowed
    bar-sum energy (the tutti, less violin II's melodic return) strictly
    rises."""
    fails = []
    sums = _bar_sums_ex(sc, {V2})
    edges = [164.0, 208.0, 252.0, 296.0, 340.0]        # 4 windows of 11 bars
    means = [_mean_barsum(sums, edges[i], edges[i + 1])
             for i in range(len(edges) - 1)]
    for i in range(len(means) - 1):
        if means[i + 1] <= means[i]:
            fails.append(f"crescendo window {i + 1} not louder: "
                         f"{means[i]:.0f} -> {means[i + 1]:.0f}")
    return fails


def _o_decrescendo(sc):
    """The Quiet: everything falls away over eight bars — the bar-sum energy
    strictly decays across [352,384)."""
    fails = []
    sums = _bar_sums(sc)
    edges = [352.0, 360.0, 368.0, 376.0, 384.0]
    means = [_mean_barsum(sums, edges[i], edges[i + 1]) for i in range(4)]
    for i in range(len(means) - 1):
        if means[i + 1] >= means[i]:
            fails.append(f"decrescendo window {i + 1} not quieter: "
                         f"{means[i]:.0f} -> {means[i + 1]:.0f}")
    return fails


def _o_arrival(sc):
    """The album's withheld tonic: a THEME statement ending on degree 1 occurs
    EXACTLY ONCE across the whole track, and only in the finale."""
    fails = []
    sigs = (_theme_sig(_MM), _theme_sig(_MJ))
    arrivals = []
    for ch in sorted(sc.events):
        ons = _ons(sc, ch)
        durs = {(round(o, 4), p): off - o for o, off, p in _spans(sc, ch)}
        for i in range(len(ons) - 6):
            win = ons[i:i + 7]
            span = win[6][0] - win[0][0]
            gaps = [win[k + 1][0] - win[k][0] for k in range(6)]
            if max(gaps) > 5.0 or not 6.0 < span < 10.0:
                continue
            ivs = tuple(win[k + 1][1] - win[k][1] for k in range(6))
            if ivs[:5] in sigs and ivs[5] == -2:
                lb, lp, _lv = win[6]
                if lp % 12 == _TONIC_PC and durs.get((round(lb, 4), lp), 0) >= 2.0:
                    arrivals.append((ch, win[0][0]))
    if len(arrivals) != 1:
        fails.append(f"{len(arrivals)} theme statements reach the tonic; the "
                     f"album allows exactly one (got {arrivals[:4]})")
    elif not FALL_T0 <= arrivals[0][1] < END:
        fails.append(f"the arrival is at beat {arrivals[0][1]:.1f}, not in "
                     f"the finale")
    return fails


def _o_final(sc):
    """The last sonority is a D-major-add9 — the waiting tone E at last a
    consonance beside D, F# and A, with no foreign tone."""
    fails = []
    t = END - 6.0
    pcs = set()
    for ch in sc.events:
        for on, off, p in _spans(sc, ch):
            if on <= t < off:
                pcs.add(p % 12)
    named = ((_TONIC_PC, "D"), ((BASE + 4) % 12, "F#"),
             ((BASE + 7) % 12, "A"), (_WAITING_PC, "E"))
    required = {pc for pc, _n in named}
    for pc, name in named:
        if pc not in pcs:
            fails.append(f"the final chord is missing {name}")
    foreign = pcs - required
    if foreign:
        fails.append(f"the final chord has foreign tones {sorted(foreign)} "
                     f"(not a clean D-major-add9)")
    return fails


def _o_additive(sc):
    """The procession assembles: each cycle introduces one channel that has
    not sounded before, and the per-cycle energy strictly rises."""
    fails = []
    entries = {ORGAN: (0.0, 16.0), TIMP: (16.0, 32.0), DRONE: (32.0, 48.0),
               ENS: (48.0, 64.0), HARP: (64.0, 80.0), VC: (80.0, 96.0)}
    for ch, (lo, hi) in sorted(entries.items()):
        ons = [b for b, _p, _v in _ons(sc, ch) if b < 96.0]
        if not ons:
            fails.append(f"ch{ch} never enters the procession")
            continue
        if not lo <= ons[0] < hi:
            fails.append(f"ch{ch} enters at {ons[0]:.1f}, want its cycle "
                         f"[{lo:.0f},{hi:.0f})")
        if any(b < lo - 1e-9 for b in ons):
            fails.append(f"ch{ch} sounds before its entry cycle")
    sums = _bar_sums(sc)
    means = [_mean_barsum(sums, 16.0 * c, 16.0 * (c + 1)) for c in range(6)]
    for i in range(5):
        if means[i + 1] <= means[i]:
            fails.append(f"procession energy not rising into cycle {i + 1}: "
                         f"{means[i]:.0f} -> {means[i + 1]:.0f}")
    return fails[:8]


def _o_rubato():
    """Rubato is mandatory: the tempo breathes, dips in every movement, and
    the finale slows to a fermata."""
    fails = []
    tm = PART.TEMPO_MAP
    bpms = [b for _t, b in tm]
    if len(tm) < 12:
        fails.append(f"only {len(tm)} tempo events — the map may be too flat")
    if max(bpms) - min(bpms) < 8.0:
        fails.append(f"tempo range {max(bpms) - min(bpms):.0f} bpm under 8")
    if sum(1 for a, b in zip(bpms, bpms[1:]) if b < a) < 4:
        fails.append("fewer than 4 tempo dips — not enough rubato")
    if bpms[-1] > 50.0:
        fails.append(f"final tempo {bpms[-1]} — the finale must slow to <= 50")
    for name, t0, t1 in PART.MOVEMENTS:
        seg = [b for t, b in tm if t0 <= t < t1]
        if not any(b2 < b1 for b1, b2 in zip(seg, seg[1:])):
            fails.append(f"no tempo dip inside '{name}'")
    return fails


def oracles(sc, info, spans):
    return [
        ("additive_build", _o_additive(sc)),
        ("turning_geometry", _o_turning(sc)),
        ("quadruple_counterpoint", _o_quadruple(sc)),
        ("departed_line_completion", _o_departed(sc)),
        ("holes_filled", _o_holes_filled(sc)),
        ("crescendo_arc", _o_crescendo(sc)),
        ("decrescendo_arc", _o_decrescendo(sc)),
        ("arrival_uniqueness", _o_arrival(sc)),
        ("final_add9", _o_final(sc)),
        ("rubato_nonflat", _o_rubato()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py): the crescendo rises, the finale is intimate,
# the last chord truly rings.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    # 1. the long III crescendo actually rises in the render
    a0, a1 = ctx.bar_window(172.0, 200.0)
    early = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    b0, b1 = ctx.bar_window(308.0, 336.0)
    late = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    fails = []
    if late < early + 3.0:
        fails.append(f"III crescendo: late {late:.1f} dB not >= 3 dB over "
                     f"early {early:.1f} dB")
    checks.append(("audio_crescendo", fails))

    # 2. the finale is an intimate drop — the solo arrival well under the peak
    p0, p1 = ctx.bar_window(320.0, 338.0)
    peak = ctx.db(ctx.rms(ctx.l, ctx.r, p0, p1))
    s0, s1 = ctx.bar_window(392.0, 404.0)
    solo = ctx.db(ctx.rms(ctx.l, ctx.r, s0, s1))
    fails = []
    if solo > peak - 6.0:
        fails.append(f"solo arrival {solo:.1f} dB not >= 6 dB under the peak "
                     f"{peak:.1f} dB")
    if solo < -46.0:
        fails.append(f"solo arrival {solo:.1f} dB — the theme vanished")
    checks.append(("audio_intimate_arrival", fails))

    # 3. the final D-major-add9 still rings eight seconds after its onset
    onset_i, _ = ctx.bar_window(FINAL_CHORD_T0, FINAL_CHORD_T0)
    r8 = onset_i + 8 * ctx.sample_rate
    r9 = onset_i + 9 * ctx.sample_rate
    fails = []
    if r9 <= len(ctx.l):
        ring = ctx.db(ctx.rms(ctx.l, ctx.r, r8, r9))
        if ring < -46.0:
            fails.append(f"final chord {ring:.1f} dB eight seconds in — it "
                         f"decayed too soon")
    else:
        fails.append("render ends before the final chord can ring 8 s")
    checks.append(("audio_final_chord_decay", fails))
    return checks
