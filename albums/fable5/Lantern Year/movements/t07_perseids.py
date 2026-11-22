"""t07_perseids.py — track 7 of *Lantern Year*: "Perseids".

August, the meteor shower; night-sky electronica.  B aeolian at 126, 4/4,
lifting to D major (the relative major, tonic moved from B to D) for the
second drop.

The BEAM (1-5-6-5-8) is the SEED of the crystal arpeggio: the track opens
with the cell alone, in eighths, and it germinates into the sixteenth-note
arpeggio whose every bar re-plants the cell on that bar's chord root.  The
saw lead's hook is a two-bar motif that follows the harmony (fifth, third,
fourth, fifth, then the leap home to the root — the BEAM's last step), the
square lead answers it in contrary motion, borrows the first phrase of the
keeper's HYMN (portamento, in the breakdown) and the synth bass keeps its
own off-beat line.  METEORS — fast falling pentatonic runs on glockenspiel
and crystal — arrive at irregular moments and thicken, movement by
movement, to a verified peak in the second drop.

Form (bars of 4/4):
    I.   First Dark      0- 24   seed -> arpeggio, broken beat, rising bass
    II.  First Drop     24- 48   four-on-the-floor; tune A, A + counter, B
    III. Breakdown      48- 72   the hush: hymn phrase, dialogue, arp returns
    IV.  Bigger Build   72- 88   hand-offs, snare roll, A7 climb, the break
    V.   Second Drop    88-128   D major: A, A + counter, B, A tutti, tag
    VI.  Afterglow     128-156   memories, the seed again, the lamp bell
"""

from __future__ import annotations

import random
import sys

import conductor
import engine as en
import material

NUMBER = 7
TITLE = "Perseids"
FILE = "07 - Perseids.mid"
SEED = 20261207
COMMENT = ("Perseids - track 7 of Lantern Year. August at the lighthouse: "
           "night-sky electronica in B aeolian lifting to D major. The BEAM "
           "cell seeds a crystal arpeggio, a saw lead carries the tune over "
           "a synth kit, and meteors (falling glockenspiel and crystal "
           "runs) grow in density to a peak in the second, bigger drop.")

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

BPM = 126.0
BAR = 4.0
MODE = "aeolian"                 # B aeolian == D ionian pitch set
SCALE_PCS = {11, 1, 2, 4, 6, 7, 9}
PENTA_PCS = {11, 2, 4, 6, 9}     # B minor / D major pentatonic (meteors)

B_I, B_II, B_III, B_IV, B_V, B_VI, B_END = 0, 24, 48, 72, 88, 128, 156


def bar(b: float) -> float:
    return BAR * b


LEAD, SQR, BASS, PAD, ARP, SWEEP, GLOCK, LASER, CRYS = 0, 1, 2, 3, 4, 5, 6, 7, 8
DR, CHOIR, STAB, REV, BELL, OCT = 9, 10, 11, 12, 13, 14

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. First Dark", bar(B_I), bar(B_II)),
        ("II. First Drop", bar(B_II), bar(B_III)),
        ("III. Breakdown", bar(B_III), bar(B_IV)),
        ("IV. Bigger Build", bar(B_IV), bar(B_V)),
        ("V. Second Drop", bar(B_V), bar(B_VI)),
        ("VI. Afterglow", bar(B_VI), bar(B_END)),
    ],
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 2, 1), (bar(B_V), 2, 0), (bar(B_VI + 8), 2, 1)],
    channels=[
        (LEAD, "saw lead", 81, 122, 64, 48),
        (SQR, "square lead", 80, 104, 78, 55),
        (BASS, "synth bass", 38, 106, 64, 16),
        (PAD, "warm pad", 89, 96, 52, 70),
        (ARP, "crystal arp", 98, 84, 44, 50),
        (SWEEP, "sweep pad", 95, 100, 82, 72),
        (GLOCK, "glock meteors", 9, 118, 90, 68),
        (LASER, "laser", 103, 58, 42, 60),
        (CRYS, "crystal meteors", 98, 90, 38, 68),
        (DR, "synth kit", 0, 72, 64, 22),
        (CHOIR, "choir pad", 91, 90, 70, 75),
        (STAB, "fm stabs", 5, 84, 58, 40),
        (REV, "reverse cymbal", 119, 80, 64, 50),
        (BELL, "lamp bell", 14, 100, 64, 72),
        (OCT, "saw octave", 81, 112, 64, 45),
    ],
    program_changes=[(DR, 0.0, 24)],            # the synth kit
)

BEAM_CHANNELS = {ARP, SQR}
PROGRAM_WHITELIST = {81, 80, 38, 89, 98, 95, 9, 103, 91, 5, 119, 14, 24}
CENTERED_CHANNELS = {LEAD, BASS, DR, REV, BELL, OCT}
NOTE_RANGES = {
    LEAD: (57, 91), SQR: (55, 88), BASS: (33, 59), PAD: (47, 76),
    ARP: (62, 98), SWEEP: (72, 90), GLOCK: (60, 108), CRYS: (60, 108),
    LASER: (80, 90), CHOIR: (57, 81), STAB: (55, 76), REV: (62, 62),
    BELL: (62, 62), OCT: (57, 80),
}
GAP_WHITELIST: list = []
BEND_EXEMPT: set = set()
DURATION_WINDOW = (296.0, 301.0)
BOUNDS_WHITELIST: list = []

# ---------------------------------------------------------------------------
# Harmony: one chord root (a B-aeolian degree) per bar.
# 1 Bm  3 D  4 Em  5 F#m  6 G  7 A   (ii-dim is never used)
# ---------------------------------------------------------------------------

CHORDS: list = (
    [1, 1, 6, 6, 3, 3, 7, 7] + [1, 1, 6, 6, 3, 3, 7, 7]
    + [4, 4, 5, 5, 6, 6, 7, 7]                                   # I
    + [1, 1, 6, 6, 3, 3, 7, 7] * 2 + [4, 5, 6, 7, 4, 5, 7, 1]    # II
    + [1, 3, 6, 3, 6, 7, 4, 5] + [6, 7, 1, 1, 6, 7, 3, 3]
    + [6, 6, 4, 4, 1, 1, 5, 5]                                   # III
    + [6, 6, 7, 7, 1, 1, 7, 7] + [4, 4, 6, 6, 7, 7, 7, 7]        # IV
    + [3, 3, 1, 1, 6, 6, 7, 7] * 2 + [4, 7, 3, 1, 4, 7, 3, 7]
    + [3, 3, 1, 1, 6, 6, 7, 7] + [6, 7, 1, 6, 6, 7, 3, 3]        # V
    + [3, 3, 1, 1, 6, 6, 7, 7] + [1, 1, 6, 6, 3, 3, 7, 7]
    + [6, 6, 4, 4, 5, 5, 1, 1] + [1, 1, 1, 1]                    # VI
)
assert len(CHORDS) == B_END

CHORD_BASE = 59                  # B3: chord pitch-class source
BASS_BASE = 35                   # B1
LEAD_BASE = 71                   # B4
ARP_BASE = 71                    # B4
ARP_ROOT = {1: 1, 3: 3, 4: -3, 5: -2, 6: -1, 7: 0}   # chord -> arp degree


def _pcs(b: int, size: int = 3) -> list:
    return en.triad(CHORD_BASE, MODE, CHORDS[b], size)


def _root_pc(b: int) -> int:
    return en.pitch(CHORD_BASE, MODE, CHORDS[b]) % 12


# ---------------------------------------------------------------------------
# The arpeggio — every pattern BEGINS with the BEAM cell (offsets 0 4 5 4 7
# from the chord root = degrees 1 5 6 5 8 on that root).
# ---------------------------------------------------------------------------

ARP_8 = [0, 4, 5, 4, 7, 4, 5, 4]
ARP_A = [0, 4, 5, 4, 7, 4, 5, 4, 7, 9, 8, 7, 5, 4, 5, 7]
ARP_A2 = [0, 4, 5, 4, 7, 9, 7, 4, 5, 4, 7, 9, 8, 7, 5, 4]
ARP_B = [0, 4, 5, 4, 7, 9, 11, 9, 7, 4, 5, 4, 7, 11, 9, 7]
ARP_B2 = [0, 4, 5, 4, 7, 11, 12, 11, 9, 7, 9, 11, 12, 11, 9, 7]
ARP_CLIMB = [0, 4, 5, 4, 7, 11, 12, 11, 14]
ARP_ACC = [12, 0, 0, 7, 0, 0, 9, 0, 3, 0, 8, 0, 9, 0, 0, 4]

# 16th-arp bars (the oracle checks the seed at the head of each one).
ARP16_BARS: list = (list(range(8, 48)) + list(range(68, 144)))


def _arp_bar(sc, b: int, pattern: list, vel: int, step: float = 0.25,
             count: int = 0, ring: float = 1.5) -> None:
    r = ARP_ROOT[CHORDS[b]]
    t = bar(b)
    n = count or len(pattern)
    for i in range(n):
        v = vel + (ARP_ACC[i % 16] if step == 0.25 else (8 if i % 4 == 0 else 0))
        sc.note(ARP, en.pitch(ARP_BASE, MODE, r + pattern[i]), t + i * step,
                step * ring, v, jt=0, jv=3)


# ---------------------------------------------------------------------------
# The tune.  MOTIF is chord-relative (offsets from the chord root degree):
# fifth, third, fourth, fifth, leap to the root, then the fall.
# ---------------------------------------------------------------------------

MOTIF = [(4, 0.0, 1.5), (2, 1.5, 0.5), (3, 2.0, 0.5), (4, 2.5, 1.0),
         (7, 3.5, 2.0), (6, 5.5, 0.5), (4, 6.0, 1.0), (2, 7.0, 1.0)]
MOTIF_HEAD = [(4, 0.0, 1.5), (2, 1.5, 0.5), (3, 2.0, 0.5), (4, 2.5, 1.0),
              (7, 3.5, 3.0)]
# The answer: contrary motion, an octave down, moving while the tune holds.
COUNTER = [(-5, 0.0, 2.0), (-6, 2.0, 1.0), (-5, 3.0, 1.0),
           (-3, 4.0, 1.5), (-5, 5.5, 0.5), (-3, 6.0, 0.5), (0, 6.5, 1.5)]

CAD_B = [(9, 0.0, 1.0), (8, 1.0, 0.5), (7, 1.5, 1.0), (5, 2.5, 0.5),
         (4, 3.0, 1.0), (2, 4.0, 2.5)]
CAD_B_CTR = [(0, 0.0, 2.0), (2, 2.0, 1.0), (0, 3.0, 1.0), (0, 4.0, 1.0),
             (-1, 5.0, 0.5), (-2, 5.5, 0.5), (-3, 6.0, 1.0)]
CAD_D = [(11, 0.0, 1.0), (9, 1.0, 0.5), (10, 1.5, 1.0), (9, 2.5, 0.5),
         (7, 3.0, 1.0), (9, 4.0, 2.5)]
CAD_D_CTR = [(0, 0.0, 2.0), (2, 2.0, 1.0), (4, 3.0, 1.0), (4, 4.0, 1.0),
             (3, 5.0, 0.5), (2, 5.5, 0.5), (0, 6.0, 1.0)]


def _tune_a(roots: list, cad: list, picks: tuple) -> list:
    out = []
    for i, r in enumerate(roots):
        out += [(r + o, 8.0 * i + on, du) for o, on, du in MOTIF]
    out += [(d, 24.0 + on, du) for d, on, du in cad]
    out += [(picks[0], 31.0, 0.5), (picks[1], 31.5, 0.5)]
    return out


def _counter_a(roots: list, cad: list, picks: tuple) -> list:
    out = []
    for i, r in enumerate(roots):
        out += [(r + o, 8.0 * i + on, du) for o, on, du in COUNTER]
    out += [(d, 24.0 + on, du) for d, on, du in cad]
    out += [(picks[0] - 2, 31.0, 0.5), (picks[1] - 2, 31.5, 0.5)]
    return out


ROOTS_B = [1, -1, 3]             # Bm, G, D     (then the cadence on A)
ROOTS_D = [3, 1, 6]              # D, Bm, G     (then the cadence on A)

TUNE_B1 = [   # Em F#m G A | Em F#m A Bm
    (8, 0.0, 2.0), (6, 2.0, 1.0), (4, 3.0, 1.0),
    (5, 4.0, 1.5), (7, 5.5, 1.5), (9, 7.0, 1.0),
    (10, 8.0, 2.5), (9, 10.5, 0.5), (8, 11.0, 1.0),
    (9, 12.0, 1.0), (7, 13.0, 1.0), (4, 14.0, 1.5), (7, 15.5, 0.5),
    (8, 16.0, 2.0), (6, 18.0, 0.5), (8, 18.5, 0.5), (11, 19.0, 1.0),
    (12, 20.0, 1.5), (9, 21.5, 1.5), (7, 23.0, 1.0),
    (11, 24.0, 1.0), (9, 25.0, 1.0), (7, 26.0, 1.0), (9, 27.0, 1.0),
    (8, 28.0, 3.5),
]
HARM_B1 = [6, 7, 8, 7, 6, 7, 9, 5]
TUNE_B2 = [   # Em A D Bm | Em A D A   (ii-V-I-vi, ii-V-I-V in D)
    (8, 0.0, 2.0), (6, 2.0, 1.0), (4, 3.0, 1.0),
    (7, 4.0, 1.5), (9, 5.5, 1.5), (11, 7.0, 1.0),
    (12, 8.0, 2.5), (11, 10.5, 0.5), (10, 11.0, 1.0),
    (8, 12.0, 1.0), (10, 13.0, 1.0), (12, 14.0, 1.5), (10, 15.5, 0.5),
    (11, 16.0, 2.0), (13, 18.0, 0.5), (11, 18.5, 0.5), (8, 19.0, 1.0),
    (9, 20.0, 1.5), (11, 21.5, 1.5), (7, 23.0, 1.0),
    (10, 24.0, 1.5), (9, 25.5, 0.5), (10, 26.0, 0.5), (12, 26.5, 1.5),
    (11, 28.0, 2.5), (9, 31.0, 0.5), (8, 31.5, 0.5),
]
HARM_B2 = [6, 4, 7, 5, 6, 4, 5, 9]
TUNE_TAG = [  # G A Bm G | G A D D
    (10, 0.0, 3.0), (8, 3.0, 1.0),
    (9, 4.0, 3.0), (11, 7.0, 1.0),
    (12, 8.0, 2.0), (10, 10.0, 1.0), (8, 11.0, 1.0),
    (10, 12.0, 3.5), (8, 15.5, 0.5),
    (13, 16.0, 2.0), (12, 18.0, 1.0), (10, 19.0, 1.0),
    (11, 20.0, 2.0), (9, 22.0, 1.0), (11, 23.0, 1.0),
    (10, 24.0, 7.5),
]
HARM_TAG = [8, 7, 10, 8, 8, 9, 5, 5]

# Spans where the square lead is a verified counter-voice to the saw.
COUNTER_SPANS = [(32, 48), (60, 64), (80, 88), (96, 128)]

# ---------------------------------------------------------------------------
# Meteors — a deterministic plan (own RNG; never touches the Score's stream).
# (start_beat, channel, pool_index_of_top_note, notes, step_beats, velocity)
# ---------------------------------------------------------------------------

METEOR_CHANNELS = [GLOCK, CRYS]
METEOR_MIN = 5
METEOR_POOL = sorted((p for p in range(60, 108) if p % 12 in PENTA_PCS),
                     reverse=True)


def _meteor_plan() -> list:
    rng = random.Random(SEED * 31 + 7)
    zones = [   # (bar0, bar1, count, vel_lo, vel_hi)
        (6, B_II, 3, 64, 76),
        (B_II, B_III, 6, 72, 86),
        (B_III, B_IV, 7, 62, 78),
        (B_IV, B_V, 6, 74, 90),
        (B_V, B_V + 16, 10, 82, 96),
        (B_V + 16, B_VI, 22, 86, 102),
        (B_VI, B_END - 8, 4, 56, 70),
    ]
    plan = []
    for b0, b1, count, v_lo, v_hi in zones:
        t0 = bar(b0)
        slot = bar(b1 - b0) / count
        for i in range(count):
            n = rng.randint(6, 11)
            step = rng.choice((0.125, 0.125, 1.0 / 6.0))
            room = max(0.0, slot - n * step - 0.75)
            off = round(rng.uniform(0.0, room) * 4) / 4.0
            start = round((t0 + i * slot) * 4) / 4.0 + off
            ch = GLOCK if rng.random() < 0.55 else CRYS
            top_hi = min(5 if ch == GLOCK else 7, len(METEOR_POOL) - n)
            top = rng.randint(0 if ch == GLOCK else 2, top_hi)
            plan.append((start, ch, top, n, step, rng.randint(v_lo, v_hi)))
    return plan


METEOR_PLAN = _meteor_plan()


def _meteors(sc, b0: int, b1: int) -> None:
    k = 0
    for start, ch, top, n, step, vel in METEOR_PLAN:
        if not bar(b0) <= start < bar(b1):
            continue
        if ch == GLOCK:
            vel = min(124, vel + 22)
        for i in range(n):
            v = round(en.lerp(vel, vel * 0.5, i / (n - 1)))
            sc.note(ch, METEOR_POOL[top + i], start + i * step, 0.4, v,
                    jt=0, jv=2)
        if b0 == B_V and k % 4 == 0:        # a laser streak with the big ones
            sc.note(LASER, 86, start, 1.5, 66, jt=0, jv=2)
        k += 1


# ---------------------------------------------------------------------------
# Small emitters
# ---------------------------------------------------------------------------

def _bloom(sc, ch: int, t: float, dur: float, peak: int) -> None:
    """CC1 vibrato bloom inside one held note: straight, then opening."""
    sc.cc(ch, 1, 0, t)
    en.cc_curve(sc, ch, 1, [(t + 0.3 * dur, 0), (t + 0.8 * dur, peak)],
                step=0.25)
    sc.cc(ch, 1, 0, t + dur)


def _mel(sc, ch: int, t0: float, notes: list, vel: int, octave: int = 0,
         gate: float = 0.94, bloom: int = 64) -> None:
    for deg, on, du in notes:
        t = t0 + on
        d = du * gate
        v = vel + (5 if on % 4.0 == 0.0 else 0)
        sc.note(ch, en.pitch(LEAD_BASE, MODE, deg) + 12 * octave, t, d, v,
                jt=0, jv=3)
        if bloom and du >= 1.5:
            _bloom(sc, ch, t, d, bloom)


def _motif(sc, ch: int, b: int, r: int, vel: int, head: bool = False,
           octave: int = 0) -> None:
    src = MOTIF_HEAD if head else MOTIF
    _mel(sc, ch, bar(b), [(r + o, on, du) for o, on, du in src], vel,
         octave=octave)


def _harm(sc, ch: int, b: int, degs: list, vel: int) -> None:
    """Square harmony voice: one pushed pair per bar under the tune."""
    for i, d in enumerate(degs):
        t = bar(b + i)
        _mel(sc, ch, t, [(d, 0.0, 2.5), (d, 2.5, 1.5)], vel, bloom=48)


def _pad(sc, ch: int, b0: int, b1: int, size: int, lo: int, hi: int,
         vel: int, sevenths: bool = False, legato: float = 0.1,
         vel_end=None) -> None:
    chords = [_pcs(b, 4 if sevenths else 3) for b in range(b0, b1)]
    en.pad_block(sc, ch, bar(b0), chords, BAR, size=size, lo=lo, hi=hi,
                 vel=vel, vel_end=vel_end, legato=legato)


def _pump(sc, ch: int, b0: int, b1: int, lo: int, hi: int) -> None:
    """Side-chain breathing: CC11 ducks on every kick and re-opens."""
    for q in range(int(bar(b0)), int(bar(b1))):
        sc.cc(ch, 11, lo, q)
        sc.cc(ch, 11, (lo + hi) // 2, q + 0.25)
        sc.cc(ch, 11, hi, q + 0.5)


def _bass(sc, deg: int, t: float, dur: float, vel: int) -> None:
    sc.note(BASS, en.pitch(BASS_BASE, MODE, deg), t, dur, vel, jt=0, jv=3)


def _approach(b: int) -> int:
    """A step into the next bar's root (the fifth when the chord holds)."""
    r = CHORDS[b]
    nxt = CHORDS[b + 1] if b + 1 < B_END else r
    if nxt == r:
        return r + 4
    return nxt - 1 if nxt > r else nxt + 1


# (16th step, offset from root or "ap", length in 16ths, velocity)
BASS_D1 = [
    [(0, 0, 1.6, 106), (3, 7, 0.9, 82), (6, 0, 1.4, 96), (7, 0, 0.8, 78),
     (10, 7, 1.0, 92), (11, 4, 0.9, 80), (14, 0, 1.0, 94), (15, "ap", 0.9, 86)],
    [(0, 0, 1.6, 106), (3, 7, 0.9, 82), (6, 4, 1.4, 94), (7, 4, 0.8, 76),
     (10, 7, 1.0, 92), (11, 6, 0.9, 80), (13, 4, 0.9, 78), (14, 2, 1.0, 90),
     (15, "ap", 0.9, 86)],
]
BASS_D2 = [
    [(0, 0, 1.0, 112), (2, 0, 0.9, 94), (3, 7, 0.9, 88), (4, 0, 0.9, 98),
     (6, 0, 0.9, 94), (7, 7, 0.9, 88), (8, 0, 0.9, 100), (10, 4, 0.9, 94),
     (11, 7, 0.9, 90), (12, 0, 0.9, 98), (14, 2, 0.9, 92), (15, "ap", 0.9, 90)],
    [(0, 0, 1.0, 112), (2, 0, 0.9, 94), (3, 7, 0.9, 88), (4, 4, 0.9, 96),
     (6, 4, 0.9, 92), (7, 7, 0.9, 88), (8, 0, 0.9, 100), (10, 7, 0.9, 94),
     (11, 6, 0.9, 90), (12, 4, 0.9, 96), (13, 2, 0.9, 86), (14, 0, 0.9, 92),
     (15, "ap", 0.9, 90)],
]


def _bass_bar(sc, b: int, patterns: list, lift: int = 0) -> None:
    r = CHORDS[b]
    t = bar(b)
    for step, off, ln, vel in patterns[b % 2]:
        deg = _approach(b) if off == "ap" else r + off
        _bass(sc, deg, t + step * 0.25, ln * 0.25, vel + lift)


def _bass_long(sc, b: int, vel: int, hold: float = 3.0) -> None:
    _bass(sc, CHORDS[b], bar(b), hold * 0.97, vel)
    if hold < 4.0:
        _bass(sc, _approach(b), bar(b) + hold, (4.0 - hold) * 0.95, vel - 8)


def _bass_pulse(sc, b: int, vel0: int, vel1: int, step: float = 0.5,
                beats: float = 4.0) -> None:
    n = int(round(beats / step))
    for i in range(n):
        last = (i == n - 1 and beats == 4.0)
        deg = _approach(b) if last else CHORDS[b]
        _bass(sc, deg, bar(b) + i * step, step * 0.8,
              round(en.lerp(vel0, vel1, i / max(1, n - 1)))
              + (8 if i % int(1 / step) == 0 else 0))


# ---------------------------------------------------------------------------
# Drums — the synth kit.  Kicks are tick-exact (jt=0): the floor is pinned.
# ---------------------------------------------------------------------------

def _hit(sc, key: int, t: float, vel: int, jt: int = 0, dur: float = 0.2) -> None:
    sc.note(DR, key, t, dur, vel, jt=jt, jv=3)


def _floor_bar(sc, b: int, lvl: int, crash: bool = False,
               fill: bool = False, busy: bool = True) -> None:
    """Four-on-the-floor.  lvl 1 = first drop, lvl 2 = second drop."""
    t = bar(b)
    for q in range(4):
        _hit(sc, 36, t + q, 106 if lvl == 2 else 100)
    for q in (1, 3):
        _hit(sc, 39, t + q, 120 if lvl == 2 else 112)
        if lvl == 2:
            _hit(sc, 38, t + q, 104)
    for s in range(16):
        pos = s % 4
        if fill and s >= 12:
            continue
        if pos == 2:
            _hit(sc, 46, t + s * 0.25, 60 if lvl == 2 else 54)
        elif lvl == 2 or (busy and pos != 1) or pos == 0:
            v = (50, 36, 0, 42)[pos] + (4 if lvl == 2 else 0)
            _hit(sc, 42, t + s * 0.25, v, dur=0.15)
    if lvl == 2:
        for e in range(8):
            _hit(sc, 54, t + e * 0.5 + 0.25, 50, dur=0.15)
    if crash:
        _hit(sc, 49, t, 102 if lvl == 2 else 96, dur=1.0)
    if fill:
        keys = (38, 38, 38, 38) if lvl == 1 else (50, 47, 45, 38)
        for i, key in enumerate(keys):
            _hit(sc, key, t + 3.0 + i * 0.25, 84 + 9 * i, dur=0.15)


BROKEN = [
    {"k": [0.0, 2.5], "s": [1.0, 3.0], "rim": [1.75], "oh": []},
    {"k": [0.0, 0.75, 2.5], "s": [1.0, 3.0], "rim": [3.75], "oh": [3.5]},
    {"k": [0.0, 1.5, 2.75], "s": [1.0, 3.5], "rim": [2.25], "oh": [1.5]},
]


def _broken_bar(sc, b: int, variant: int, level: float = 1.0,
                snare: bool = True, hats: bool = True) -> None:
    """A two-step / broken beat: the kick skips, never four to the bar."""
    t = bar(b)
    pat = BROKEN[variant]
    for k in pat["k"]:
        _hit(sc, 36, t + k, round(100 * level))
    if snare:
        for s in pat["s"]:
            _hit(sc, 39, t + s, round(112 * level))
        for s in pat["rim"]:
            _hit(sc, 37, t + s, round(76 * level), jt=2)
    if hats:
        for e in range(8):
            pos = e * 0.5
            if pos in pat["oh"]:
                _hit(sc, 46, t + pos, round(56 * level), jt=2)
            else:
                _hit(sc, 42, t + pos, round((52 if e % 2 else 38) * level),
                     jt=2, dur=0.15)


def _roll(sc, t0: float, t1: float, step: float, v0: int, v1: int,
          key: int = 38) -> None:
    n = int(round((t1 - t0) / step))
    for i in range(n):
        _hit(sc, key, t0 + i * step, round(en.lerp(v0, v1, i / max(1, n - 1))),
             dur=min(0.15, step * 0.7))


def _stabs(sc, b0: int, b1: int, vel: int) -> None:
    prev = None
    for b in range(b0, b1):
        prev = en.voice_lead(_pcs(b), prev, 3, 57, 74)
        for pos in (0.75, 1.5, 2.75, 3.5):
            for p in prev:
                sc.note(STAB, p, bar(b) + pos, 0.22, vel, jt=0, jv=4)


# ---------------------------------------------------------------------------
# I. First Dark (bars 0-24): the seed, alone; it germinates.
# ---------------------------------------------------------------------------

def _b_first_dark(sc) -> None:
    # Standing sends: meteor trails, a little echo on arp and leads.
    for ch in METEOR_CHANNELS:
        sc.cc(ch, 94, 52, 0.0)
    sc.cc(ARP, 94, 30, 0.0)
    sc.cc(LEAD, 94, 16, 0.0)
    sc.cc(SQR, 94, 22, 0.0)
    sc.cc(LEAD, 11, 118, 0.0)

    # The seed: the BEAM, unaccompanied, and its echo.
    material.play_beam(sc, ARP, bar(0), ARP_BASE, MODE, vel=86, gate=0.97,
                       jt=0, jv=0)
    material.play_beam(sc, ARP, bar(1), ARP_BASE, MODE, vel=58, gate=0.97,
                       jt=0, jv=0)
    en.cc_curve(sc, ARP, 74, [(0.0, 96), (bar(8), 70), (bar(23), 127)],
                step=1.0)
    for b in range(2, 8):
        _arp_bar(sc, b, ARP_8, 62 + 3 * (b - 2), step=0.5, ring=1.3)
    for b in range(8, 24):
        _arp_bar(sc, b, ARP_A if b % 2 == 0 else ARP_A2,
                 round(en.lerp(60, 78, (b - 8) / 15)))

    # Pads swell in from bar 2.
    _pad(sc, PAD, 2, 24, 4, 50, 72, 58, sevenths=True)
    en.expr_curve(sc, PAD, [(bar(2), 20), (bar(8), 92), (bar(16), 100),
                            (bar(24), 116)])
    _pad(sc, SWEEP, 8, 24, 2, 74, 88, 52)
    en.cc_curve(sc, SWEEP, 74, [(bar(8), 28), (bar(23.5), 118)], step=0.5)
    en.expr_curve(sc, SWEEP, [(bar(8), 40), (bar(24), 112)])

    # Bass: long roots, then pulsing eighths under the rising chords.
    for b in range(8, 16):
        _bass_long(sc, b, 84, hold=3.5)
    for b in range(16, 24):
        _bass_pulse(sc, b, 78 + 2 * (b - 16), 84 + 2 * (b - 16))

    # Broken beat arrives in stages.
    for b in range(8, 12):
        _broken_bar(sc, b, 0, level=0.8, snare=False)
    for b in range(12, 22):
        _broken_bar(sc, b, (0, 1, 0, 2)[b % 4], level=0.92)
    _broken_bar(sc, 22, 1, hats=False, snare=False)
    _roll(sc, bar(22), bar(23), 0.5, 68, 92)
    _hit(sc, 36, bar(23), 100)
    _hit(sc, 36, bar(23) + 2.5, 100)
    _roll(sc, bar(23), bar(24), 0.25, 80, 114)
    sc.note(REV, 62, bar(23), 4.0, 92, jt=0, jv=0)

    # The square lead tries out the tune's head, rising with the bass.
    _motif(sc, SQR, 16, -3, 88, head=True)
    _motif(sc, SQR, 18, -2, 92, head=True)
    _motif(sc, SQR, 20, -1, 96)
    _mel(sc, SQR, bar(22), [(0, 0.0, 1.0), (2, 1.0, 1.0), (4, 2.0, 1.0),
                            (7, 3.0, 1.0), (9, 4.0, 3.5)], 100)
    en.echo_throw(sc, SQR, bar(23), base=22, peak=96, release=3.5)

    _meteors(sc, B_I, B_II)


# ---------------------------------------------------------------------------
# II. First Drop (bars 24-48): tune A, A with its counter-melody, tune B.
# ---------------------------------------------------------------------------

def _b_first_drop(sc) -> None:
    t = bar(B_II)
    sc.note(LASER, 86, t, 1.5, 62, jt=0, jv=0)
    sc.cc(ARP, 74, 127, t)

    _mel(sc, LEAD, t, _tune_a(ROOTS_B, CAD_B, (3, 4)), 100)
    _mel(sc, LEAD, bar(32), _tune_a(ROOTS_B, CAD_B, (5, 7)), 103)
    _mel(sc, SQR, bar(32), _counter_a(ROOTS_B, CAD_B_CTR, (5, 7)), 74,
         bloom=40)
    _mel(sc, LEAD, bar(40), TUNE_B1, 106)
    _harm(sc, SQR, 40, HARM_B1, 78)
    for b in (30, 38):
        en.echo_throw(sc, LEAD, bar(b) + 4.0, base=16, peak=94, release=2.5)
    en.echo_throw(sc, LEAD, bar(47), base=16, peak=100, release=3.5)

    for b in range(24, 48):
        _arp_bar(sc, b, ARP_A if b % 2 == 0 else ARP_A2, 56 if b < 40 else 62)
        _bass_bar(sc, b, BASS_D1, lift=-6)
        _floor_bar(sc, b, 1, crash=(b % 8 == 0), fill=(b % 8 == 7),
                   busy=(b >= 32))
    _stabs(sc, 32, 48, 60)

    _pad(sc, PAD, 24, 48, 4, 50, 72, 62)
    _pump(sc, PAD, 24, 48, 48, 100)
    _pad(sc, SWEEP, 40, 48, 2, 74, 88, 56)
    sc.cc(SWEEP, 74, 112, bar(40))
    sc.cc(SWEEP, 11, 96, bar(40))

    _meteors(sc, B_II, B_III)


# ---------------------------------------------------------------------------
# III. Breakdown (bars 48-72): the hush.  The square lead borrows the first
# phrase of the keeper's hymn (which IS the beam, augmented); the saw
# answers; the arpeggio creeps back.
# ---------------------------------------------------------------------------

def _b_breakdown(sc) -> None:
    t = bar(B_III)
    sc.cc(PAD, 11, 84, t)
    _pad(sc, PAD, 48, 72, 4, 50, 72, 54, sevenths=True)
    en.expr_curve(sc, PAD, [(t, 84), (bar(52), 96), (bar(56), 80),
                            (bar(64), 92), (bar(72), 106)])

    # The hymn phrase: portamento square, one note a bar.
    en.portamento_on(sc, SQR, t - 0.5, time_cc=52)
    sc.cc(SQR, 68, 127, t - 0.5)
    material.play_phrase(sc, SQR, t, LEAD_BASE, MODE, 0, stretch=2.0,
                         vel=86, gate=1.0, jt=0, jv=2)
    for _d, on, du in material.hymn_phrase(0):
        _bloom(sc, SQR, t + 2.0 * on, 2.0 * du, 60)
    en.expr_curve(sc, SQR, [(t, 96), (bar(52), 118), (bar(56), 92)])
    en.echo_throw(sc, SQR, bar(55), base=22, peak=98, release=3.5)
    en.portamento_off(sc, SQR, bar(56))
    sc.cc(SQR, 68, 0, bar(56))
    sc.cc(SQR, 11, 110, bar(60))

    # Bass sings under it: a root and a passing step each bar.
    for b in range(48, 64):
        _bass_long(sc, b, 58, hold=3.0)

    # The saw answers quietly (56-64); the square shadows it from bar 60.
    _mel(sc, LEAD, bar(56), [
        (3, 0.0, 3.0), (4, 3.0, 1.0),
        (4, 4.0, 2.0), (2, 6.0, 1.0), (4, 7.0, 1.0),
        (5, 8.0, 3.5), (3, 11.5, 0.5),
        (3, 12.0, 1.0), (1, 13.0, 2.5),
        (6, 16.0, 3.0), (8, 19.0, 1.0),
        (7, 20.0, 2.0), (9, 22.0, 1.0), (7, 23.0, 1.0),
        (10, 24.0, 2.0), (7, 26.0, 1.0), (5, 27.0, 1.0),
        (3, 28.0, 3.5)], 76, bloom=56)
    _mel(sc, SQR, bar(60), [
        (1, 0.0, 2.0), (3, 2.0, 2.0),
        (2, 4.0, 2.0), (4, 6.0, 2.0),
        (5, 8.0, 3.0), (3, 11.0, 1.0),
        (-2, 12.0, 3.5)], 68, bloom=44)
    _pad(sc, CHOIR, 56, 72, 3, 60, 79, 50)
    en.expr_curve(sc, CHOIR, [(bar(56), 30), (bar(63), 96), (bar(66), 70),
                              (bar(72), 110)])
    for b in range(56, 64):
        _hit(sc, 37, bar(b) + 1.0, 66, jt=2)
        _hit(sc, 37, bar(b) + 2.75, 56, jt=2)
        for e in (0.5, 1.5, 2.5, 3.5):
            _hit(sc, 42, bar(b) + e, 38, jt=2, dur=0.15)

    # The arpeggio returns, filtered; the pulse wakes.
    en.cc_curve(sc, ARP, 74, [(bar(64), 34), (bar(71), 62)], step=1.0)
    for b in range(64, 68):
        _arp_bar(sc, b, ARP_8, 56, step=0.5, ring=1.3)
    for b in range(68, 72):
        _arp_bar(sc, b, ARP_A, 58 + 2 * (b - 68))
    for b in range(64, 72):
        r = CHORDS[b]
        _bass(sc, r, bar(b), 1.4, 68)
        _bass(sc, r + 7, bar(b) + 1.5, 0.45, 58)
        _bass(sc, r, bar(b) + 2.0, 1.4, 66)
        _bass(sc, _approach(b), bar(b) + 3.5, 0.45, 62)
        _broken_bar(sc, b, (0, 2)[b % 2], level=0.72, snare=(b >= 68))
    _mel(sc, LEAD, bar(68), [
        (5, 0.0, 4.0), (3, 4.0, 3.0), (4, 7.0, 1.0),
        (5, 8.0, 2.0), (7, 10.0, 2.0), (9, 12.0, 3.8)], 80, bloom=60)

    _meteors(sc, B_III, B_IV)


# ---------------------------------------------------------------------------
# IV. Bigger Build (bars 72-88): the tune handed saw -> square -> saw, the
# snare roll, the filter opening, an A7 climb (the dominant of D) and a
# half-bar of held breath.
# ---------------------------------------------------------------------------

def _b_build(sc) -> None:
    t = bar(B_IV)
    en.cc_curve(sc, ARP, 74, [(t, 40), (bar(87), 127)], step=1.0)
    for b in range(72, 87):
        _arp_bar(sc, b, ARP_A if b % 2 == 0 else ARP_A2,
                 round(en.lerp(50, 86, (b - 72) / 14)))
    _arp_bar(sc, 87, ARP_A, 88, count=8)

    _pad(sc, PAD, 72, 87, 4, 50, 72, 60, sevenths=True)
    en.expr_curve(sc, PAD, [(t, 72), (bar(80), 96), (bar(87), 124)])
    _pad(sc, SWEEP, 72, 87, 2, 74, 88, 56)
    en.cc_curve(sc, SWEEP, 74, [(t, 24), (bar(87), 124)], step=0.5)
    en.expr_curve(sc, SWEEP, [(t, 36), (bar(80), 70), (bar(87), 122)])
    _pad(sc, CHOIR, 80, 87, 3, 60, 79, 54)
    en.expr_curve(sc, CHOIR, [(bar(80), 56), (bar(87), 120)])
    # the last chord of the build stops dead at the break
    for ch, size, lo, hi in ((PAD, 4, 50, 72), (SWEEP, 2, 74, 88),
                             (CHOIR, 3, 60, 79)):
        for p in en.voice_lead(_pcs(87, 4), None, size, lo, hi):
            sc.note(ch, p, bar(87), 1.9, 70, jt=0, jv=2)

    # Hand-offs.
    _motif(sc, LEAD, 72, -1, 100)
    _motif(sc, SQR, 74, 0, 100)
    _motif(sc, LEAD, 76, 1, 104)
    _motif(sc, SQR, 78, 0, 104)
    # The climb: E G A C# E over Em G A A — an A7 spelled upward.
    en.portamento_on(sc, LEAD, bar(80) - 0.25, time_cc=44)
    sc.cc(LEAD, 68, 127, bar(80) - 0.25)
    _mel(sc, LEAD, bar(80), [(4, 0.0, 8.0), (6, 8.0, 8.0), (7, 16.0, 8.0),
                             (9, 24.0, 4.0), (11, 28.0, 2.0)], 106,
         gate=1.0, bloom=84)
    _mel(sc, SQR, bar(80), [(-1, 0.0, 8.0), (1, 8.0, 8.0), (2, 16.0, 8.0),
                            (4, 24.0, 4.0), (6, 28.0, 2.0)], 92,
         gate=1.0, bloom=70)
    en.portamento_off(sc, LEAD, bar(87) + 2.0)
    sc.cc(LEAD, 68, 0, bar(87) + 2.0)

    # Bass: eighths, then sixteenths hammering the roots.
    for b in range(72, 80):
        _bass_pulse(sc, b, 68 + 2 * (b - 72), 76 + 2 * (b - 72))
    for b in range(80, 87):
        _bass_pulse(sc, b, 86 + 2 * (b - 80), 92 + 2 * (b - 80), step=0.25)
    _bass_pulse(sc, 87, 102, 112, step=0.25, beats=2.0)

    # Drums: the broken beat tightens into a roll.
    for b in range(72, 80):
        _broken_bar(sc, b, (1, 2, 1, 0)[b % 4],
                    level=0.76 if b < 76 else 0.9)
    for b in range(80, 84):
        _broken_bar(sc, b, (1, 2)[b % 2], snare=False)
        _roll(sc, bar(b), bar(b + 1), 0.5, 72 + 5 * (b - 80), 80 + 5 * (b - 80))
    for b in range(84, 87):
        _hit(sc, 36, bar(b), 100)
        _hit(sc, 36, bar(b) + 2.5, 100)
        _roll(sc, bar(b), bar(b + 1), 0.25, 86 + 6 * (b - 84), 96 + 6 * (b - 84))
    _hit(sc, 36, bar(87), 100)
    _hit(sc, 36, bar(87) + 1.5, 100)
    _roll(sc, bar(87), bar(87) + 2.0, 0.125, 100, 124)
    sc.note(REV, 62, bar(86) + 2.0, 6.0, 100, jt=0, jv=0)

    _meteors(sc, B_IV, B_V)


# ---------------------------------------------------------------------------
# V. Second Drop (bars 88-128): D major.  The tune starts where it used to
# climax; everything is here; the sky is full.
# ---------------------------------------------------------------------------

def _b_second_drop(sc) -> None:
    t = bar(B_V)
    sc.note(LASER, 86, t, 1.5, 70, jt=0, jv=0)
    sc.cc(ARP, 74, 127, t)
    sc.cc(LEAD, 11, 124, t)
    sc.cc(SQR, 11, 116, t)

    _mel(sc, LEAD, t, _tune_a(ROOTS_D, CAD_D, (5, 6)), 106, bloom=72)
    _mel(sc, LEAD, bar(96), _tune_a(ROOTS_D, CAD_D, (6, 7)), 108, bloom=72)
    _mel(sc, SQR, bar(96), _counter_a(ROOTS_D, CAD_D_CTR, (6, 7)), 86,
         bloom=44)
    _mel(sc, LEAD, bar(104), TUNE_B2, 110, bloom=76)
    _harm(sc, SQR, 104, HARM_B2, 84)
    last_a = _tune_a(ROOTS_D, CAD_D, (7, 9))
    _mel(sc, LEAD, bar(112), last_a, 112, bloom=78)
    _mel(sc, OCT, bar(112), last_a, 96, octave=-1, bloom=50)
    _mel(sc, SQR, bar(112), _counter_a(ROOTS_D, CAD_D_CTR, (7, 9)), 90,
         bloom=44)
    _mel(sc, LEAD, bar(120), TUNE_TAG, 114, bloom=86)
    _mel(sc, OCT, bar(120), TUNE_TAG, 98, octave=-1, bloom=56)
    _harm(sc, SQR, 120, HARM_TAG, 88)
    for b in (94, 102, 110, 118):
        en.echo_throw(sc, LEAD, bar(b) + 4.0, base=16, peak=96, release=2.5)
    en.echo_throw(sc, LEAD, bar(126), base=16, peak=104, release=6.0)

    for b in range(88, 127):
        _arp_bar(sc, b, ARP_B if b % 2 == 0 else ARP_B2, 70 if b < 112 else 76)
    _arp_bar(sc, 127, ARP_CLIMB, 90)
    r_top = en.pitch(ARP_BASE, MODE, ARP_ROOT[CHORDS[127]] + 14)
    sc.note(ARP, r_top, bar(127) + 2.25, 1.6, 96, jt=0, jv=0)
    en.echo_throw(sc, ARP, bar(127) + 2.0, base=30, peak=104, release=6.0)

    for b in range(88, 128):
        _bass_bar(sc, b, BASS_D2)
        _floor_bar(sc, b, 2, crash=(b % 8 == 0), fill=(b % 8 == 7))
    for b in range(104, 128):
        for q in range(4):
            _hit(sc, 51, bar(b) + q, 60, jt=1, dur=0.2)
    _stabs(sc, 88, 128, 76)

    _pad(sc, PAD, 88, 128, 4, 50, 74, 70)
    _pump(sc, PAD, 88, 128, 58, 122)
    _pad(sc, CHOIR, 88, 128, 3, 62, 81, 66)
    _pump(sc, CHOIR, 88, 128, 64, 122)
    _pad(sc, SWEEP, 88, 128, 2, 76, 90, 62)
    en.wah(sc, SWEEP, t, bar(40), lo=78, hi=124, cycles_per_beat=1.0 / 16.0,
           step=0.5)
    sc.cc(SWEEP, 11, 112, t)
    sc.note(REV, 62, bar(119), 4.0, 96, jt=0, jv=0)

    _meteors(sc, B_V, B_VI)


# ---------------------------------------------------------------------------
# VI. Afterglow (bars 128-156): the floor falls away; memories of the tune;
# the arpeggio slows back into the seed; the lamp tolls once.
# ---------------------------------------------------------------------------

def _b_afterglow(sc) -> None:
    t = bar(B_VI)
    _hit(sc, 49, t, 86, dur=1.0)
    sc.cc(LEAD, 11, 112, t)
    sc.cc(SQR, 11, 108, t)

    _pad(sc, PAD, 128, 152, 4, 50, 72, 58, sevenths=True)
    en.expr_curve(sc, PAD, [(t, 112), (bar(144), 92), (bar(152), 78),
                            (bar(156), 60)])
    _pad(sc, CHOIR, 128, 144, 3, 60, 79, 52, vel_end=40)
    en.expr_curve(sc, CHOIR, [(t, 104), (bar(144), 40)])
    _pad(sc, SWEEP, 128, 144, 2, 74, 88, 50)
    en.cc_curve(sc, SWEEP, 74, [(t, 112), (bar(144), 26)], step=0.5)
    en.expr_curve(sc, SWEEP, [(t, 100), (bar(144), 36)])

    # The arpeggio thins: sixteenths, then eighths, then the seed.
    en.cc_curve(sc, ARP, 74, [(t, 120), (bar(152), 60)], step=1.0)
    for b in range(128, 144):
        _arp_bar(sc, b, ARP_A if b % 2 == 0 else ARP_A2,
                 round(en.lerp(62, 46, (b - 128) / 15)))
    for b in range(144, 152):
        _arp_bar(sc, b, ARP_8, 58 - (b - 144), step=0.5, ring=1.3)
    sc.cc(ARP, 74, 96, bar(152))
    material.play_beam(sc, ARP, bar(152), ARP_BASE, MODE, vel=72, gate=0.97,
                       jt=0, jv=0)
    material.play_beam(sc, ARP, bar(153), ARP_BASE, MODE, vel=50, gate=0.97,
                       jt=0, jv=0)
    material.play_beam(sc, ARP, bar(154), ARP_BASE, MODE, stretch=2.0,
                       vel=70, vel_end=84, gate=1.0, jt=0, jv=0)

    # Bass: roots that walk, then whole notes, then the last B.
    for b in range(128, 144):
        r = CHORDS[b]
        _bass(sc, r, bar(b), 2.4, 68)
        _bass(sc, r + 4, bar(b) + 2.5, 0.9, 58)
        _bass(sc, _approach(b), bar(b) + 3.5, 0.45, 58)
    for b in range(144, 152):
        _bass_long(sc, b, 58, hold=4.0)
    _bass(sc, 1, bar(154), 8.0, 66)

    # Drums recede: a soft broken beat, then hats and rim, then nothing.
    for b in range(128, 136):
        _broken_bar(sc, b, (0, 1, 0, 2)[b % 4], level=0.74)
    for b in range(136, 144):
        _hit(sc, 37, bar(b) + 1.0, 62, jt=2)
        for e in (0.5, 1.5, 2.5, 3.5):
            _hit(sc, 42, bar(b) + e, 36, jt=2, dur=0.15)

    # Memories: the hook an octave down; the beam on the square; a last
    # phrase that ends on the beam's own rise, fifth to octave.
    _motif(sc, LEAD, 128, 3, 88, octave=-1)
    _motif(sc, LEAD, 130, 1, 84, octave=-1)
    _mel(sc, LEAD, bar(132), [(3, 0.0, 3.0), (1, 3.0, 1.0), (-1, 4.0, 3.8),
                              (0, 8.0, 3.0), (2, 11.0, 1.0), (4, 12.0, 3.8)],
         82, bloom=50)
    material.play_beam(sc, SQR, bar(136), LEAD_BASE - 12, MODE, stretch=2.0,
                       vel=90, gate=0.96, jt=0, jv=2)
    _bloom(sc, SQR, bar(137), 3.8, 50)
    _mel(sc, SQR, bar(138), [(-1, 0.0, 3.0), (1, 3.0, 1.0), (3, 4.0, 3.8)],
         84, bloom=44)
    _mel(sc, LEAD, bar(140), [(7, 0.0, 2.0), (5, 2.0, 2.0), (3, 4.0, 3.8),
                              (2, 8.0, 3.0), (4, 11.0, 1.0), (2, 12.0, 3.8)],
         80, bloom=50)
    _mel(sc, LEAD, bar(144), [(3, 0.0, 6.0), (1, 6.0, 2.0),
                              (-1, 8.0, 4.0), (1, 12.0, 2.0), (4, 14.0, 2.0),
                              (2, 16.0, 4.0), (5, 20.0, 4.0),
                              (8, 24.0, 8.0)], 80, bloom=58)
    en.expr_curve(sc, LEAD, [(bar(144), 112), (bar(150), 104),
                             (bar(152), 56)])
    en.echo_throw(sc, LEAD, bar(150), base=16, peak=100, release=7.0)

    # The last chord: Bm, with the lamp's D as its third.
    for p in en.voice_lead(_pcs(155), None, 4, 50, 72):
        sc.note(PAD, p, bar(152), 16.0, 52, jt=0, jv=2)
    sc.note(BELL, material.LAMP_PITCH, bar(155), 4.0, 92, jt=0, jv=0)

    _meteors(sc, B_VI, B_END)


BUILDERS = [_b_first_dark, _b_first_drop, _b_breakdown, _b_build,
            _b_second_drop, _b_afterglow]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _meteor_runs(sc):
    """Falling runs on the meteor channels: ([(start, ch, n)], strays)."""
    runs, strays = [], []
    for ch in METEOR_CHANNELS:
        ons = material.note_ons(sc, ch)
        i = 0
        while i < len(ons):
            j = i
            while (j + 1 < len(ons) and ons[j + 1][0] - ons[j][0] <= 0.26
                   and ons[j + 1][1] < ons[j][1]):
                j += 1
            if j - i + 1 >= METEOR_MIN:
                runs.append((ons[i][0], ch, j - i + 1))
            else:
                strays.append(f"ch{ch} beat {ons[i][0]:.2f}: {j - i + 1} "
                              f"note(s) that are not a falling run")
            i = j + 1
    return sorted(runs), strays


def _kicks(sc) -> set:
    return {round(b * en.PPQ) for b, p, _v in material.note_ons(sc, DR)
            if p == 36}


def _movement_bars() -> list:
    return [(B_I, B_II), (B_II, B_III), (B_III, B_IV), (B_IV, B_V),
            (B_V, B_VI), (B_VI, B_END)]


def _o_beam_seed(sc) -> list:
    fails = []
    beams = material.beam_statements(sc, ARP)
    first = min((b, ch) for ch in sc.events
                for b, _p, _v in material.note_ons(sc, ch))
    if first != (0.0, ARP) or 0.0 not in beams:
        fails.append(f"the track must open with the BEAM on the arp at beat "
                     f"0 (first note-on is ch{first[1]} at {first[0]:.2f})")
    early = sorted(ch for ch in material.active_channels(sc, 0.0,
                                                         bar(2) - 0.05)
                   if ch != ARP)
    if early:
        fails.append(f"the seed must be unaccompanied for two bars; "
                     f"channels {early} also play")
    arp = material.note_ons(sc, ARP)
    bass_on = {round(b * en.PPQ): p for b, p, _v in material.note_ons(sc, BASS)}
    for b in ARP16_BARS:
        head = [(x, p) for x, p, _v in arp if bar(b) - 1e-6 <= x < bar(b) + 1.2]
        want = [bar(b) + 0.25 * i for i in range(5)]
        if len(head) != 5 or any(abs(x - w) > 1e-6
                                 for (x, _p), w in zip(head, want)):
            fails.append(f"bar {b}: the arp does not start with five "
                         f"sixteenths")
            continue
        p = [q for _x, q in head]
        iv = [p[1] - p[0], p[2] - p[1], p[3] - p[2], p[4] - p[3]]
        if not (iv[0] == 7 and iv[1] in (1, 2) and iv[2] == -iv[1]
                and iv[3] == 5):
            fails.append(f"bar {b}: arp head intervals {iv} are not the BEAM")
        if p[0] % 12 != _root_pc(b):
            fails.append(f"bar {b}: the seed is not planted on the chord root")
        bp = bass_on.get(round(bar(b) * en.PPQ))
        if bp is not None and bp % 12 != p[0] % 12:
            fails.append(f"bar {b}: arp seed pc {p[0] % 12} disagrees with "
                         f"the bass downbeat pc {bp % 12}")
    if len(beams) < len(ARP16_BARS):
        fails.append(f"only {len(beams)} BEAM statements on the arp; want "
                     f">= {len(ARP16_BARS)}")
    for (name, t0, t1) in PART.MOVEMENTS:
        if not any(t0 <= x < t1 for x in beams):
            fails.append(f"no arp BEAM inside '{name}'")
    if not beams or beams[-1] < bar(B_END - 2) or arp[-1][0] < bar(B_END - 1):
        fails.append("the last arp notes must be the BEAM (the seed returns)")
    return fails[:10]


def _o_meteor_peak(sc) -> list:
    fails = []
    runs, strays = _meteor_runs(sc)
    fails += strays[:4]
    if len(runs) != len(METEOR_PLAN):
        fails.append(f"{len(runs)} falling runs detected, the plan has "
                     f"{len(METEOR_PLAN)}")
    dens = []
    for b0, b1 in _movement_bars():
        k = sum(1 for s, _c, _n in runs if bar(b0) <= s < bar(b1))
        dens.append(k / (b1 - b0))
    for i in range(4):
        if not dens[i] < dens[i + 1]:
            fails.append(f"meteor density must grow through movement "
                         f"{i + 2}: {dens[i]:.3f} !< {dens[i + 1]:.3f} "
                         f"per bar")
    if dens[4] < 2.0 * max(dens[:4] + dens[5:]):
        fails.append(f"second-drop density {dens[4]:.3f}/bar is not twice "
                     f"every other movement ({[round(d, 3) for d in dens]})")
    if dens[5] > dens[4] / 3.0:
        fails.append("the afterglow must thin to under a third of the peak")
    counts = {b: sum(1 for s, _c, _n in runs if bar(b) <= s < bar(b + 16))
              for b in range(0, B_END - 15)}
    best = max(counts.values())
    peaks = [b for b, c in counts.items() if c == best]
    if any(not (B_V <= b and b + 16 <= B_VI) for b in peaks) or best < 12:
        fails.append(f"the busiest 16 bars ({best} meteors, starting at "
                     f"bar(s) {peaks}) must lie inside the second drop")
    half = bar((B_V + B_VI) / 2)
    first = sum(1 for s, _c, _n in runs if bar(B_V) <= s < half)
    second = sum(1 for s, _c, _n in runs if half <= s < bar(B_VI))
    if second <= first:
        fails.append(f"the shower must still be growing inside the drop "
                     f"({first} then {second})")
    return fails


def _o_meteor_irregular(sc) -> list:
    fails = []
    runs, _strays = _meteor_runs(sc)
    starts = [s for s, _c, _n in runs]
    phases = {round((s % BAR) * 4) for s in starts}
    if len(phases) < 9:
        fails.append(f"meteors start on only {len(phases)} of 16 bar "
                     f"positions; want >= 9 (irregular moments)")
    gaps = [round((b - a) * 4) for a, b in zip(starts, starts[1:])]
    if gaps:
        common = max(gaps.count(g) for g in set(gaps))
        if common > 0.2 * len(gaps):
            fails.append(f"one gap recurs {common}/{len(gaps)} times: the "
                         f"shower is periodic")
        if len(set(gaps)) < 14:
            fails.append(f"only {len(set(gaps))} distinct gaps")
    for ch in METEOR_CHANNELS:
        for b, p, _v in material.note_ons(sc, ch):
            if p % 12 not in PENTA_PCS:
                fails.append(f"ch{ch} beat {b:.2f}: pitch {p} is outside "
                             f"the pentatonic")
    if {c for _s, c, _n in runs} != set(METEOR_CHANNELS):
        fails.append("meteors must fall on both glockenspiel and crystal")
    if any(n < 6 for _s, _c, n in runs):
        fails.append("a meteor shorter than six notes")
    return fails[:8]


def _o_floor_and_broken(sc) -> list:
    fails = []
    kicks = _kicks(sc)
    progs = [(t, d[1]) for t, _p, d in sc.events.get(DR, [])
             if (d[0] & 0xF0) == 0xC0]
    if progs != [(0, 24)]:
        fails.append(f"ch9 must select the synth kit (24) at beat 0: {progs}")
    for b in range(B_END):
        on_beat = [round((bar(b) + q) * en.PPQ) in kicks for q in range(4)]
        in_bar = [k for k in kicks
                  if bar(b) * en.PPQ <= k < bar(b + 1) * en.PPQ]
        if B_II <= b < B_III or B_V <= b < B_VI:
            if not all(on_beat):
                fails.append(f"bar {b} (drop): the kick misses a beat "
                             f"{on_beat}")
            if any(k % en.PPQ for k in in_bar):
                fails.append(f"bar {b} (drop): a kick off the floor")
        else:
            if all(on_beat):
                fails.append(f"bar {b}: four-on-the-floor outside a drop")
            if len(in_bar) >= 2 and not any(k % en.PPQ for k in in_bar):
                fails.append(f"bar {b}: an unbroken beat (every kick on a "
                             f"quarter) outside a drop")
    if any(bar(B_III) * en.PPQ <= k < bar(B_III + 16) * en.PPQ for k in kicks):
        fails.append("the breakdown's first 16 bars must have no kick")
    return fails[:8]


def _o_bigger_drop(sc) -> list:
    fails = []
    e1 = material.energy(sc, bar(B_II), bar(B_III))
    e2 = material.energy(sc, bar(B_V), bar(B_VI))
    if e2 < 1.25 * e1:
        fails.append(f"second drop energy {e2:.0f} < 1.25 x first {e1:.0f}")
    a1 = material.active_channels(sc, bar(B_II), bar(B_III))
    a2 = material.active_channels(sc, bar(B_V), bar(B_VI))
    if not (a1 <= a2 and len(a2) >= len(a1) + 2):
        fails.append(f"second drop voices {sorted(a2)} must extend the "
                     f"first drop's {sorted(a1)} by two or more")
    top1 = max(p for b, p, _v in material.note_ons(sc, LEAD)
               if bar(B_II) <= b < bar(B_III))
    top2 = max(p for b, p, _v in material.note_ons(sc, LEAD)
               if bar(B_V) <= b < bar(B_VI))
    if top2 <= top1:
        fails.append(f"the lead must reach higher in the second drop "
                     f"({top2} vs {top1})")
    hush = material.energy(sc, bar(B_III), bar(B_III + 8))
    if hush > 0.2 * e1:
        fails.append(f"breakdown hush energy {hush:.0f} > 20% of the first "
                     f"drop ({e1:.0f})")
    for name, (b0, b1) in zip("I II III IV V VI".split(), _movement_bars()):
        e = material.energy(sc, bar(b0), bar(b1))
        if name not in ("V",) and e >= e2:
            fails.append(f"movement {name} energy {e:.0f} >= the second "
                         f"drop's {e2:.0f}")
    lo = material.energy(sc, bar(B_IV), bar(B_IV + 4))
    hi = material.energy(sc, bar(B_V - 4), bar(B_V) - 2.0)
    if hi < 1.3 * lo:
        fails.append(f"the build does not build ({lo:.0f} -> {hi:.0f})")
    if material.energy(sc, bar(B_IV + 8), bar(B_V)) <= \
            material.energy(sc, bar(B_II - 8), bar(B_II)):
        fails.append("the second build must be bigger than the first")
    brk = [ch for ch in sc.events if ch != REV
           and (material.sounding(sc, ch, bar(B_V) - 1.0)
                or any(bar(B_V) - 1.99 <= b < bar(B_V) - 0.05
                       for b, _p, _v in material.note_ons(sc, ch)))]
    if brk:
        fails.append(f"the half-bar break before the drop is not empty: "
                     f"channels {sorted(brk)}")
    return fails


def _o_mode_and_lift(sc) -> list:
    fails = []
    for ch in sorted(sc.events):
        if ch == DR:
            continue
        for b, p, _v in material.note_ons(sc, ch):
            if p % 12 not in SCALE_PCS:
                fails.append(f"ch{ch} beat {b:.2f}: pitch {p} is outside "
                             f"B aeolian / D major")
    bass = {round(b * en.PPQ): p for b, p, _v in material.note_ons(sc, BASS)}

    def root(b: int):
        p = bass.get(round(bar(b) * en.PPQ))
        return None if p is None else p % 12

    if root(B_II) != 11:
        fails.append(f"the first drop must land on B in the bass, got "
                     f"{root(B_II)}")
    if root(B_V - 1) != 9 or root(B_V) != 2:
        fails.append(f"the lift must be A -> D in the bass (V-I of D); got "
                     f"{root(B_V - 1)} -> {root(B_V)}")
    if [root(b) for b in (104, 105, 106)] != [4, 9, 2]:
        fails.append("bars 104-106 must walk ii-V-I in D (E, A, D)")
    for b in range(B_V, B_VI):
        if root(b) != _root_pc(b):
            fails.append(f"bar {b}: bass downbeat pc {root(b)} is not the "
                         f"chord root {_root_pc(b)}")
    d_count = sum(1 for b in range(B_V, B_VI) if root(b) == 2)
    b_count = sum(1 for b in range(B_V, B_VI) if root(b) == 11)
    if d_count < 10 or d_count <= b_count:
        fails.append(f"the second drop must centre on D ({d_count} D "
                     f"downbeats vs {b_count} B)")
    if sum(1 for b in range(B_II, B_III) if root(b) == 11) < 5:
        fails.append("the first drop must centre on B")
    spans = material.note_spans(sc, BASS)
    if not spans or spans[-1][2] % 12 != 11 \
            or spans[-1][1] < bar(B_END) - 0.01:
        fails.append("the bass must end on B, held to the last beat")
    if sorted(sc.keysigs) != [(0.0, 2, 1), (bar(B_V), 2, 0),
                              (bar(B_VI + 8), 2, 1)]:
        fails.append("key signatures must read b minor / D major / b minor")
    return fails[:8]


def _o_counterpoint(sc) -> list:
    fails = []
    lead = material.note_spans(sc, LEAD)
    sqr = material.note_spans(sc, SQR)
    bass = {round(b * en.PPQ): p for b, p, _v in material.note_ons(sc, BASS)}

    def at(spans, beat):
        return [p for on, off, p, _v in spans
                if on <= beat + 1e-9 and off >= beat + 0.05]

    checked = 0
    for b0, b1 in COUNTER_SPANS:
        for b in range(b0, b1):
            lp, sp = at(lead, bar(b)), at(sqr, bar(b))
            if len(lp) != 1 or len(sp) != 1:
                fails.append(f"bar {b}: need one saw and one square note on "
                             f"the bar line (saw {lp}, square {sp})")
                continue
            checked += 1
            if (lp[0] - sp[0]) % 12 not in material.CONSONANT - {0}:
                fails.append(f"bar {b}: saw {lp[0]} against square {sp[0]} "
                             f"is not an imperfect/perfect consonance")
    if checked < 50:
        fails.append(f"only {checked} bar lines carry both voices")
    # The two voices are independent: they move in contrary or oblique
    # motion more often than in parallel across the checked bar lines.
    moves = {"contrary": 0, "similar": 0}
    for b0, b1 in COUNTER_SPANS:
        for b in range(b0, b1 - 1):
            l0, l1 = at(lead, bar(b)), at(lead, bar(b + 1))
            s0, s1 = at(sqr, bar(b)), at(sqr, bar(b + 1))
            if l0 and l1 and s0 and s1:
                dl, ds = l1[0] - l0[0], s1[0] - s0[0]
                moves["similar" if dl * ds > 0 and dl == ds else "contrary"] += 1
    if moves["similar"] > moves["contrary"] / 3:
        fails.append(f"the counter-voice shadows the tune in strict "
                     f"parallel too often ({moves})")
    # The tune's bar-line notes agree with the bass (drops only).
    for b in list(range(B_II, B_III)) + list(range(B_V, B_VI)):
        lp = at(lead, bar(b))
        bp = bass.get(round(bar(b) * en.PPQ))
        if lp and bp is not None and (lp[0] - bp) % 12 not in material.CONSONANT:
            fails.append(f"bar {b}: lead {lp[0]} dissonant with the bass {bp}")
    return fails[:8]


def _o_expression(sc) -> list:
    fails = []
    for ch in (LEAD, SQR, OCT):
        cc1 = material.cc_lane(sc, ch, 1)
        for on, off, p, _v in material.note_spans(sc, ch):
            if off - on < 1.8:
                continue
            inside = [v for b, v in cc1 if on < b < off]
            if not inside or max(inside) < 30:
                fails.append(f"ch{ch} held note at {on:.1f} ({off - on:.1f} "
                             f"beats) has no CC1 bloom")
            elif inside[0] != 0:
                fails.append(f"ch{ch} note at {on:.1f}: the bloom must start "
                             f"from a straight tone")
    port = material.cc_lane(sc, SQR, 65)
    if not any(v == 127 and b <= bar(B_III) for b, v in port) or \
            not any(v == 0 and bar(B_III) < b <= bar(B_III + 8) for b, v in port):
        fails.append("the square lead must glide (CC65) through the hymn "
                     "phrase and release after it")
    if not any(v == 127 for _b, v in material.cc_lane(sc, LEAD, 65)):
        fails.append("the saw lead never uses portamento")
    for ch in (SWEEP, ARP):
        lane = [(b, v) for b, v in material.cc_lane(sc, ch, 74)
                if bar(B_IV) <= b < bar(B_V) - 4.0]
        vals = [v for _b, v in lane]
        if len(vals) < 12 or vals != sorted(vals) or vals[0] > 45 \
                or vals[-1] < 115:
            fails.append(f"ch{ch}: the build's CC74 sweep must rise "
                         f"monotonically from <= 45 to >= 115")
    throws = sum(1 for ch in (LEAD, SQR, ARP)
                 for _b, v in material.cc_lane(sc, ch, 94) if v >= 90)
    if throws < 8:
        fails.append(f"only {throws} echo throws (CC94 >= 90); want >= 8")
    for ch in (PAD, CHOIR):
        lane = [v for b, v in material.cc_lane(sc, ch, 11)
                if bar(B_V) <= b < bar(B_VI)]
        if len(lane) < 300 or max(lane) - min(lane) < 40:
            fails.append(f"ch{ch}: no side-chain pump in the second drop")
    return fails[:8]


def _o_hymn_borrowed(sc) -> list:
    fails = []
    found = material.phrase_statements(sc, SQR, MODE, 0)
    ok = [f for f in found if abs(f[0] - bar(B_III)) < 0.05
          and abs(f[1] - 2.0) < 0.01 and f[2] % 12 == 11]
    if len(ok) != 1:
        fails.append(f"the square lead must state hymn phrase 1 once, at "
                     f"the breakdown, stretch 2, on B (found {found})")
    if any(bar(B_III) <= b < bar(B_III + 8)
           for b, _p, _v in material.note_ons(sc, LEAD)):
        fails.append("the saw lead must be silent under the hymn phrase")
    busy = material.active_channels(sc, bar(B_III), bar(B_III + 8)) \
        - {SQR, PAD, BASS, GLOCK, CRYS}
    if busy:
        fails.append(f"the hush is crowded: channels {sorted(busy)}")
    bells = material.note_ons(sc, BELL)
    if len(bells) != 1 or bells[0][1] != material.LAMP_PITCH \
            or bells[0][0] < bar(B_END - 2):
        fails.append("the lamp bell must toll exactly once, on D, in the "
                     "last two bars")
    return fails


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("perseids_beam_seeds_arpeggio", _o_beam_seed(sc)))
    results.append(("perseids_meteors_peak_in_drop_2", _o_meteor_peak(sc)))
    results.append(("perseids_meteors_irregular", _o_meteor_irregular(sc)))
    results.append(("perseids_floor_vs_broken_beat", _o_floor_and_broken(sc)))
    results.append(("perseids_bigger_second_drop", _o_bigger_drop(sc)))
    results.append(("perseids_mode_and_lift_to_d", _o_mode_and_lift(sc)))
    results.append(("perseids_counterpoint", _o_counterpoint(sc)))
    results.append(("perseids_expression", _o_expression(sc)))
    results.append(("perseids_hymn_phrase_in_hush", _o_hymn_borrowed(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def level(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(bar(b0), bar(b1))
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    drop1 = level(B_II + 1, B_III - 1)
    drop2 = level(B_V + 1, B_VI - 1)
    hush = level(B_III + 1, B_III + 7)
    build_lo = level(B_IV, B_IV + 4)
    build_hi = level(B_V - 5, B_V - 1)
    glow = level(B_END - 12, B_END - 4)

    out = []
    f = []
    if drop2 < drop1 + 0.5:
        f.append(f"second drop {drop2:.1f} dB is not above the first "
                 f"{drop1:.1f} dB (+0.5)")
    out.append(("second_drop_louder", f))
    f = []
    if hush > drop2 - 6.0:
        f.append(f"breakdown hush {hush:.1f} dB is within 6 dB of the peak "
                 f"{drop2:.1f} dB")
    if hush > drop1 - 5.0:
        f.append(f"breakdown hush {hush:.1f} dB is within 5 dB of the first "
                 f"drop {drop1:.1f} dB")
    out.append(("breakdown_is_a_hush", f))
    f = []
    if build_hi < build_lo + 3.0:
        f.append(f"the build rises only {build_hi - build_lo:.1f} dB "
                 f"({build_lo:.1f} -> {build_hi:.1f})")
    out.append(("build_rises", f))
    f = []
    if glow > drop2 - 6.0:
        f.append(f"afterglow {glow:.1f} dB is within 6 dB of the peak "
                 f"{drop2:.1f} dB")
    out.append(("afterglow_settles", f))
    return out
