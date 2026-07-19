"""t04_cuban_eight.py — Slipstream T4: "Cuban Eight".

HLD section 4/T4.  The figure-eight: two loops joined by half-rolls — loop
two is loop one UPSIDE DOWN.  G dorian, 128 bpm, 4/4, ~4:35.

Architecture: entry -> LOOP1 build -> over-the-top suspension -> DROP1 (the
32-beat HOOK on lead ship + saw double) -> HALF-ROLL (4-bar turnaround, the
harmony pivots Bb-C-Dm-Dm and lands back on G) -> LOOP2 build (hotter) ->
DROP2 where the hook returns EXACTLY INVERTED (material.mirror about G4=67,
tick-exact, on the wing ship while the lead harmonizes) -> EXIT PASS: hook
and mirror-hook sound SIMULTANEOUSLY in two-part counterpoint, pairwise
consonant on every downbeat, with a third free saw counter-line above ->
out.  G dorian is reflection-symmetric about its own tonic, so the mirror
image of the hook is again G dorian; hook downbeats are restricted to
odd-valued pitches (pcs F/G/A) so hook-vs-mirror downbeat intervals are
always in the consonant set.

Duo formation — INVERSION (the loop flown upside down).
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 4
TITLE = "Cuban Eight"
FILE = "04 - Cuban Eight.mid"
SEED = 20261104

COMMENT = (
    "Track 04 of 'Slipstream' (Claude Fable 5): the Cuban Eight - two "
    "loops joined by half-rolls, so the second loop is the first flown "
    "upside down.  A 32-beat guitar hook crests loop one; after the "
    "half-roll pivot the wing ship flies the hook exactly inverted "
    "(mirrored about G4); the exit pass states hook and mirror at once "
    "in two-part counterpoint, consonant on every downbeat.")

BPM = 128.0
END = 584.0

# --- movement grid ----------------------------------------------------------
T_ENTRY, T_LOOP1, T_OTT = 0.0, 64.0, 192.0
T_DROP1, T_ROLL, T_LOOP2 = 200.0, 264.0, 280.0
T_DROP2, T_EXIT, T_OUT = 408.0, 472.0, 536.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Entry", T_ENTRY, T_LOOP1),
        ("II. Loop One", T_LOOP1, T_OTT),
        ("III. Over the Top", T_OTT, T_DROP1),
        ("IV. Drop One", T_DROP1, T_ROLL),
        ("V. Half-Roll", T_ROLL, T_LOOP2),
        ("VI. Loop Two", T_LOOP2, T_DROP2),
        ("VII. Drop Two", T_DROP2, T_EXIT),
        ("VIII. Exit Pass", T_EXIT, T_OUT),
        ("IX. Out", T_OUT, END),
    ],
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],            # G dorian carries one flat
    channels=[
        (0, "crystal arp", 98, 96, 64, 45),
        (1, "warm pad", 89, 92, 64, 60),
        (2, "synth bass", 39, 108, 64, 25),
        (3, "post L", 80, 90, 18, 40),
        (4, "post R", 56, 90, 110, 40),
        (5, "saw soar", 81, 104, 64, 50),
        (6, "harp", 46, 96, 64, 55),
        (7, "strings", 49, 88, 64, 62),
        (8, "choir", 52, 90, 64, 66),
        (9, "kit", 0, 110, 64, 35),
        (10, "melodic toms", 117, 100, 64, 40),
        (11, "syn drum", 118, 100, 64, 40),
        (12, "orchestra hit", 55, 100, 64, 50),
        (13, "riser", 119, 95, 64, 60),
        (14, "lead ship", 29, 118, 64, 20),
        (15, "wing ship", 29, 112, 64, 22),
    ],
    program_changes=[(9, 0.0, 25)],   # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One
    extra_markers=[(200.0, "the hook"), (408.0, "inverted"),
                   (472.0, "double hook")],
    bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1), (15, 1)],
)

# --- harmony ----------------------------------------------------------------
GM_ = [55, 58, 62]          # Gm
BB_ = [58, 62, 65]          # Bb
C__ = [60, 64, 67]          # C
F__ = [53, 57, 60]          # F
DM_ = [50, 53, 57]          # Dm

BUILD_ROOTS = [43, 46, 41, 48]                   # G Bb F C per bar
BUILD_CHORDS = [GM_, BB_, F__, C__]
DROP_ROOTS = [43, 46, 48, 41, 43, 48, 50, 41]    # aligned to hook downbeats
DROP_CHORDS = [GM_, BB_, C__, F__, GM_, C__, DM_, F__]
ROLL_ROOTS = [46, 48, 50, 50]                    # the half-roll pivot Bb C D D
ROLL_CHORDS = [BB_, C__, DM_, DM_]

# --- THE HOOK (32 beats).  Downbeats sit only on odd MIDI pitches
# (pcs F/G/A), which makes hook-vs-mirror downbeat intervals consonant;
# every pitch and every mirror image is G dorian (the mode reflects onto
# itself about its tonic).  AXIS is G4. -----------------------------------
AXIS = 67

HOOK = [
    (0.0, 67, 0.75, 102), (0.75, 69, 0.25, 88), (1.0, 70, 0.5, 92),
    (1.5, 74, 0.5, 94), (2.0, 72, 0.75, 96), (2.75, 70, 0.25, 88),
    (3.0, 69, 1.0, 94),
    (4.0, 67, 0.5, 102), (4.5, 70, 0.5, 90), (5.0, 72, 0.5, 92),
    (5.5, 74, 1.5, 98), (7.0, 76, 0.5, 92), (7.5, 77, 0.5, 94),
    (8.0, 79, 1.0, 104), (9.0, 77, 0.5, 92), (9.5, 74, 0.5, 90),
    (10.0, 76, 0.75, 94), (10.75, 74, 0.25, 88), (11.0, 72, 0.5, 90),
    (11.5, 70, 0.5, 92),
    (12.0, 69, 1.5, 100), (13.5, 72, 0.5, 90), (14.0, 74, 0.5, 92),
    (14.5, 72, 0.5, 90), (15.0, 70, 0.5, 92), (15.5, 69, 0.5, 90),
    (16.0, 67, 0.5, 96), (16.5, 69, 0.5, 92), (17.0, 70, 0.5, 94),
    (17.5, 72, 0.5, 96), (18.0, 74, 0.5, 98), (18.5, 76, 0.5, 100),
    (19.0, 77, 1.0, 102),
    (20.0, 79, 2.0, 106), (22.0, 77, 0.5, 94), (22.5, 76, 0.5, 92),
    (23.0, 74, 0.5, 94), (23.5, 72, 0.5, 92),
    (24.0, 69, 0.75, 100), (24.75, 70, 0.25, 88), (25.0, 72, 0.5, 92),
    (25.5, 74, 0.5, 94), (26.0, 70, 0.75, 94), (26.75, 69, 0.25, 88),
    (27.0, 67, 1.0, 96),
    (28.0, 65, 0.5, 98), (28.5, 67, 0.5, 92), (29.0, 69, 0.5, 94),
    (29.5, 70, 0.5, 96), (30.0, 72, 0.5, 98), (30.5, 74, 0.5, 100),
    (31.0, 69, 1.0, 96),
]
HOOK_LEN = 32.0
HOOK_DOWNBEATS = [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0]

# The free saw counter-line of the exit pass: sustained, mostly
# off-the-onset, contrary to the wing lane, consonant with BOTH hook lanes
# on every downbeat.
SAW_EXIT = [
    (0.0, 74, 3.5, 86), (3.5, 82, 3.75, 88), (7.25, 86, 4.25, 90),
    (11.25, 84, 4.0, 88), (15.25, 82, 4.25, 88), (19.5, 84, 4.0, 90),
    (23.25, 81, 4.25, 88), (27.5, 77, 4.0, 88), (31.5, 79, 0.5, 86),
]

# --- fill schedule (shapes from material.FILL_LIB, jt=0 signatures) ---------
FILLS_LOOP1 = [
    (78.0, "A"), (92.0, "B"),
    (102.0, "A"), (110.0, "C"), (124.0, "D"),
    (134.0, "B"), (142.0, "H"), (150.0, "F"), (158.0, "A"),
    (166.0, "C"), (172.0, "G"), (178.0, "H"), (182.0, "D"),
    (186.0, "F"), (189.0, "B"),
]
FILLS_OTT = [(195.75, "E"), (198.75, "G")]
FILLS_DROP1 = [(214.0, "A"), (226.0, "A"), (246.0, "B"), (258.0, "A")]
FILLS_LOOP2 = [
    (286.0, "A"), (294.0, "B"),
    (318.0, "C"), (326.0, "D"), (334.0, "A"),
    (348.0, "H"), (356.0, "F"), (364.0, "G"), (372.0, "A"),
    (378.0, "C"), (384.0, "H"), (388.0, "G"), (392.0, "D"),
    (396.0, "B"), (400.0, "F"), (403.75, "E"), (406.75, "G"),
]
FILLS_DROP2 = [(422.0, "A"), (434.0, "A"), (452.0, "B"), (464.0, "A"),
               (467.75, "E"), (470.75, "G")]
FILLS_EXIT = [(486.0, "A"), (518.0, "A")]
ALL_FILLS = (FILLS_LOOP1 + FILLS_OTT + FILLS_DROP1 + FILLS_LOOP2
             + FILLS_DROP2 + FILLS_EXIT)

# The loop-build lead fragments: hook bar 1's rhythm, climbing diatonically
# each cycle (LOOP1), and its contour inversion climbing likewise (LOOP2).
FRAG = [(1, 0.0, 0.75), (2, 0.75, 0.25), (3, 1.0, 0.5), (5, 1.5, 0.5),
        (4, 2.0, 0.75), (3, 2.75, 0.25), (2, 3.0, 1.0)]
FRAG_INV = [(8, 0.0, 0.75), (7, 0.75, 0.25), (6, 1.0, 0.5), (4, 1.5, 0.5),
            (5, 2.0, 0.75), (6, 2.75, 0.25), (7, 3.0, 1.0)]


# ---------------------------------------------------------------------------
# Emitter helpers (jt=0 on every oracle-pinned lane)
# ---------------------------------------------------------------------------

def _bloom(sc, ch, on, dur, peak=None):
    """CC1 bloom over a held note (the T361 soar gesture)."""
    if peak is None:
        peak = min(90, 34 + int(round(dur * 9)))
    en.cc_curve(sc, ch, 1, [(on, 0), (on + 0.35 * dur, peak),
                            (on + dur - 0.1, 0)], step=0.25)


def _play_hook(sc, ch, t0, vbump=0, mirrored=False):
    for off, p, dur, vel in HOOK:
        pp = material.mirror(p, AXIS) if mirrored else p
        sc.note(ch, pp, t0 + off, dur * 0.98, vel + vbump, jt=0, jv=2)
    for off, p, dur, _vel in HOOK:
        if dur >= 1.5:
            _bloom(sc, ch, t0 + off, dur)
    # legato bracket over the bar-5 stepwise run (hammer-on feel)
    sc.cc(ch, 68, 90, t0 + 15.95)
    sc.cc(ch, 68, 0, t0 + 19.15)


def _play_table(sc, ch, t0, table, vbump=0):
    for off, p, dur, vel in table:
        sc.note(ch, p, t0 + off, dur, vel + vbump, jt=0, jv=2)


def _build_groove(sc, t0, t1, lvl, vb=0):
    """Loop-build kit: kick 1/3, snare 2/4, 8th hats; lvl 1..4 layers up."""
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            if k in (0, 2):
                sc.note(9, 36, t, 0.25, 78 + vb + 2 * lvl, jt=0, jv=3)
            else:
                sc.note(9, 38, t, 0.25, 74 + vb + 3 * lvl, jt=0, jv=3)
            sc.note(9, 42, t, 0.2, 46 + vb + 3 * lvl, jt=0, jv=3)
            sc.note(9, 42, t + 0.5, 0.2, 42 + vb + 3 * lvl, jt=0, jv=3)
            if lvl >= 3:
                sc.note(9, 42, t + 0.25, 0.15, 34 + vb + 2 * lvl, jt=0, jv=3)
                sc.note(9, 42, t + 0.75, 0.15, 34 + vb + 2 * lvl, jt=0, jv=3)
        if lvl >= 2:
            sc.note(9, 36, bar + 2.5, 0.25, 68 + vb + 2 * lvl, jt=0, jv=3)
        if lvl >= 4:
            sc.note(9, 46, bar + 3.5, 0.4, 58 + vb, jt=0, jv=3)


def _four_floor(sc, t0, t1, kick, clap, hat, open_hat, hat16=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(9, 46, t + 0.5, 0.4, open_hat, jt=0, jv=4)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
        sc.note(9, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(9, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)


def _snare_roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)


def _riser(sc, beat, vel):
    sc.note(13, 62, beat, 4.0, vel, jt=0, jv=0)


def _bass_8ths(sc, t0, nbars, roots, vel, pop=True):
    for b in range(nbars):
        r = roots[b % len(roots)]
        bar = t0 + 4.0 * b
        for i in range(8):
            p = r + 12 if (pop and i == 7) else r
            sc.note(2, p, bar + 0.5 * i, 0.4,
                    vel + (4 if i in (0, 4) else 0), jt=0, jv=3)


def _chugs(sc, t0, nbars, roots, vel):
    """Wing-ship palm-muted chugs: root+12, strictly short, strictly low."""
    for b in range(nbars):
        r = roots[b % len(roots)] + 12
        bar = t0 + 4.0 * b
        for i in range(8):
            sc.note(15, r, bar + 0.5 * i, 0.28,
                    vel + (6 if i == 0 else 0), jt=0, jv=3)
        sc.note(15, r, bar + 3.75, 0.2, vel - 6, jt=0, jv=3)


def _arp_bars(sc, t0, nbars, chords, vel0, vel1, octv=12):
    for b in range(nbars):
        cp = [p + octv for p in chords[b % len(chords)]]
        seq = cp + [cp[0] + 12]
        v = int(round(en.lerp(vel0, vel1, b / max(1, nbars - 1))))
        en.arp(sc, 0, seq, t0 + 4.0 * b, 16, 0.25, v,
               pattern="updown", gate=1.1, accent_every=4)


def _hits_bars(sc, t0, nbars, roots, vel, step=4.0):
    for b in range(nbars):
        bar = t0 + 4.0 * b
        t = bar
        while t < bar + 4.0 - 1e-9:
            sc.note(12, roots[b % len(roots)] + 12, t, 0.9, vel, jt=0, jv=3)
            t += step


def _post_pair(sc, t, vel):
    """Antiphonal exchange: L calls, R answers two beats later."""
    for i, p in enumerate((79, 77, 74)):
        sc.note(3, p, t + 0.25 * i, 0.22, vel, jt=0, jv=3)
    for i, p in enumerate((67, 70, 72)):
        sc.note(4, p, t + 2.0 + 0.25 * i, 0.22 if i < 2 else 0.6,
                vel + 4, jt=0, jv=3)


def _post_stabs(sc, t0, nbars, vel):
    """Drop-time stabs: R answers odd bars, L answers even bars."""
    for b in range(nbars):
        bar = t0 + 4.0 * b
        if b % 2 == 0:
            for i, p in enumerate((72, 74, 77)):
                sc.note(4, p, bar + 3.0 + 0.25 * i, 0.2, vel, jt=0, jv=3)
        else:
            for i, p in enumerate((82, 81, 79)):
                sc.note(3, p, bar + 3.25 + 0.25 * i, 0.18, vel - 4,
                        jt=0, jv=3)


def _fills(sc, schedule, vbump_at=None):
    for start, shape in schedule:
        vb = vbump_at(start) if vbump_at else 0
        material.play_fill(sc, shape, start, vbump=vb)

# ---------------------------------------------------------------------------
# Builders (one per movement; note-ons stay inside each builder's window)
# ---------------------------------------------------------------------------

def _b_entry(sc):
    # Whole-timeline CC choreography, authored once (CC is bounds-exempt):
    # the pad macro-sweep (>= 60 CC74 units per loop), expression arcs and
    # the choir vowel journey mm -> oo -> ah -> mm.
    en.cc_curve(sc, 1, 74, [
        (0.0, 28), (64.0, 44), (192.0, 96), (200.0, 88), (264.0, 40),
        (280.0, 40), (408.0, 104), (472.0, 110), (536.0, 64), (584.0, 30),
    ], step=1.0)
    en.cc_curve(sc, 1, 11, [
        (0.0, 72), (192.0, 96), (200.0, 104), (264.0, 80), (280.0, 84),
        (408.0, 110), (472.0, 116), (536.0, 90), (584.0, 60),
    ], step=2.0)
    en.vowel_curve(sc, 8, [
        (0.0, 0), (150.0, 20), (176.0, 45), (200.0, 45), (280.0, 30),
        (344.0, 60), (408.0, 95), (472.0, 105), (536.0, 45), (584.0, 10),
    ], step=2.0)
    # the orbit-style moving pan rides ONLY the transient crystal arp
    en.autopan(sc, 0, 48.0, 488.0, lo=34, hi=94, period_beats=16.0)

    # pad bed from the first beat
    en.pad_block(sc, 1, 0.0, [GM_, GM_, BB_, F__, C__, C__, GM_, GM_],
                 span=8.0, size=4, lo=52, hi=76, vel=44, vel_end=56)
    # harp figuration
    for b in range(16):
        chord = [GM_, GM_, BB_, F__, C__, C__, GM_, GM_][b // 2]
        v = int(round(en.lerp(54, 70, b / 15)))
        en.arp(sc, 6, [chord[0], chord[1], chord[2], chord[0] + 12,
                       chord[1] + 12], 4.0 * b, 8, 0.5, v,
               pattern="up", gate=1.6)
    # bass wakes at bar 5
    for b in range(4, 16):
        r = {4: 46, 5: 46, 6: 41, 7: 41, 8: 48, 9: 48, 10: 48, 11: 48,
             12: 43, 13: 43, 14: 43, 15: 43}[b]
        sc.note(2, r, 4.0 * b, 3.6, int(en.lerp(66, 80, (b - 4) / 11)),
                jt=0, jv=3)
    # kit taxis in
    for b in range(4, 16):
        bar = 4.0 * b
        sc.note(9, 37, bar + 1.0, 0.2, 46, jt=0, jv=3)
        sc.note(9, 37, bar + 3.0, 0.2, 48, jt=0, jv=3)
        if b >= 8:
            for i in range(8):
                sc.note(9, 42, bar + 0.5 * i, 0.2,
                        int(en.lerp(38, 52, (b - 8) / 7)), jt=0, jv=3)
        if b >= 12:
            sc.note(9, 36, bar, 0.25, 62, jt=0, jv=3)
            sc.note(9, 36, bar + 2.0, 0.25, 58, jt=0, jv=3)
    # THE DUO wakes: lead states the ASCENT cell (pinned), wing echoes an
    # octave down two bars later.
    material.play_ascent(sc, 14, 32.0, 67, vel=88, jt=0)
    _bloom(sc, 14, 33.5, 2.5, peak=70)
    material.play_ascent(sc, 15, 40.0, 55, vel=80, jt=0)
    # first antiphonal exchange
    _post_pair(sc, 24.0, 70)
    # crystal arp enters for the last four bars
    _arp_bars(sc, 48.0, 4, [GM_, GM_, GM_, BB_], 58, 66)
    # lead pickup phrase into the loop
    _play_table(sc, 14, 0.0, [
        (56.0, 62, 0.5, 80), (56.5, 65, 0.5, 82), (57.0, 67, 1.5, 86),
        (58.5, 70, 0.5, 84), (59.0, 69, 1.0, 86), (60.0, 65, 0.5, 82),
        (60.5, 67, 0.5, 84), (61.0, 70, 0.75, 86), (61.75, 72, 0.25, 84),
        (62.0, 74, 2.0, 90)])
    _bloom(sc, 14, 62.0, 2.0, peak=64)
    _riser(sc, 60.0, 60)


def _b_loop_one(sc):
    # four 8-bar windows, each strictly more massive than the last
    for w in range(4):
        t0 = T_LOOP1 + 32.0 * w
        _build_groove(sc, t0, t0 + 32.0, w + 1)
        _bass_8ths(sc, t0, 8, BUILD_ROOTS, 74 + 4 * w)
        _chugs(sc, t0, 8, BUILD_ROOTS, 68 + 5 * w)
        _arp_bars(sc, t0, 8, BUILD_CHORDS, 60 + 6 * w, 66 + 6 * w)
        en.pad_block(sc, 1, t0, [BUILD_CHORDS[b % 4] for b in range(8)],
                     span=4.0, size=4, lo=52, hi=76,
                     vel=50 + 4 * w, vel_end=54 + 4 * w)
        sc.note(9, 49, t0, 1.2, 76 + 6 * w, jt=0, jv=3)
    # the loop climb: hook-teaser fragments, one per 4 bars, each a step
    # higher (lead ship pulling g)
    for c in range(8):
        en.line(sc, 14, T_LOOP1 + 16.0 * c, 67, "dorian", FRAG,
                78 + 2 * c, shift=c, jt=0, jv=3)
    # posts trade every 8 bars
    for i, t in enumerate((84.0, 116.0, 148.0, 180.0)):
        _post_pair(sc, t, 72 + 5 * i)
    # strings shade in from bar 17, choir from bar 25
    en.pad_block(sc, 7, 128.0, [BUILD_CHORDS[b % 4] for b in range(16)],
                 span=4.0, size=3, lo=56, hi=76, vel=54, vel_end=66)
    en.pad_block(sc, 8, 160.0, [BUILD_CHORDS[b % 4] for b in range(8)],
                 span=4.0, size=3, lo=55, hi=74, vel=60, vel_end=72)
    # saw begins its climb-out toward the top of the loop
    for i, (p, t) in enumerate(((67, 176.0), (70, 180.0), (74, 184.0),
                                (77, 188.0))):
        sc.note(5, p, t, 3.9, 76 + 3 * i, jt=0, jv=2)
        _bloom(sc, 5, t, 3.9, peak=50 + 8 * i)
    _fills(sc, FILLS_LOOP1, vbump_at=lambda s: max(0, int((s - 96) // 32)) * 2)


def _b_over_the_top(sc):
    # the suspension bar: everything hangs on Csus4 while the world turns
    for p in (60, 65, 67, 72):
        sc.note(1, p, T_OTT, 8.0, 64, jt=0, jv=2)
    for p in (65, 67, 72):
        sc.note(8, p, T_OTT, 8.0, 70, jt=0, jv=2)
    # the >= 6-beat held saw soar with its CC1 bloom (the sweep carrier)
    sc.note(5, 79, T_OTT, 7.9, 84, jt=0, jv=0)
    _bloom(sc, 5, T_OTT, 7.9, peak=90)
    sc.note(9, 49, T_OTT, 1.5, 88, jt=0, jv=3)
    sc.note(9, 36, T_OTT, 0.25, 84, jt=0, jv=3)
    # bar two: the 20-note unbroken fill (E then G) + snare roll + riser
    _fills(sc, FILLS_OTT)
    _snare_roll(sc, 196.0, 200.0, 60, 104)
    _riser(sc, 196.0, 78)


def _b_drop_one(sc):
    # THE HOOK, twice, lead ship + saw double an octave up
    _play_hook(sc, 14, 200.0)
    _play_hook(sc, 14, 232.0, vbump=4)
    for off, p, dur, vel in HOOK:
        sc.note(5, p + 12, 200.0 + off, dur * 0.98, vel - 12, jt=0, jv=2)
        sc.note(5, p + 12, 232.0 + off, dur * 0.98, vel - 8, jt=0, jv=2)
    # wing ship holds formation below: strictly short, strictly low chugs
    _chugs(sc, 200.0, 16, DROP_ROOTS, 82)
    _bass_8ths(sc, 200.0, 16, DROP_ROOTS, 88)
    _four_floor(sc, 200.0, 264.0, 100, 92, 58, 64)
    sc.note(9, 49, 200.0, 1.5, 100, jt=0, jv=3)
    sc.note(9, 57, 232.0, 1.5, 96, jt=0, jv=3)
    _hits_bars(sc, 200.0, 16, DROP_ROOTS, 94, step=4.0)
    _arp_bars(sc, 200.0, 16, DROP_CHORDS, 72, 76)
    en.pad_block(sc, 1, 200.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=4, lo=52, hi=76, vel=64, vel_end=68)
    _post_stabs(sc, 200.0, 16, 80)
    _fills(sc, FILLS_DROP1)


def _b_half_roll(sc):
    # the turnaround: harmony pivots Bb -> C -> Dm -> Dm (pinned via the
    # bass chord-root lane), texture drops to a breather
    sc.note(9, 49, T_ROLL, 1.5, 84, jt=0, jv=3)
    for b in range(4):
        bar = T_ROLL + 4.0 * b
        r = ROLL_ROOTS[b]
        sc.note(2, r, bar, 1.9, 78, jt=0, jv=0)
        for i in range(4, 8):
            sc.note(2, r, bar + 0.5 * i, 0.4, 70, jt=0, jv=3)
        sc.note(9, 51, bar, 0.3, 54, jt=0, jv=3)
        sc.note(9, 51, bar + 1.0, 0.3, 50, jt=0, jv=3)
        sc.note(9, 51, bar + 2.0, 0.3, 54, jt=0, jv=3)
        sc.note(9, 51, bar + 3.0, 0.3, 50, jt=0, jv=3)
        sc.note(9, 36, bar, 0.25, 64, jt=0, jv=3)
        sc.note(9, 36, bar + 2.0, 0.25, 60, jt=0, jv=3)
        sc.note(9, 37, bar + 1.0, 0.2, 48, jt=0, jv=3)
        sc.note(9, 37, bar + 3.0, 0.2, 48, jt=0, jv=3)
        en.arp(sc, 6, list(ROLL_CHORDS[b]) + [ROLL_CHORDS[b][0] + 12],
               bar, 8, 0.5, 62, pattern="up", gate=1.5)
        en.arp(sc, 0, [p + 12 for p in ROLL_CHORDS[b]], bar, 8, 0.5, 58,
               pattern="updown", gate=1.1)
    en.pad_block(sc, 1, T_ROLL, ROLL_CHORDS, span=4.0, size=4,
                 lo=52, hi=76, vel=58, vel_end=64)
    en.pad_block(sc, 7, 272.0, [DM_, DM_], span=4.0, size=3,
                 lo=56, hi=76, vel=54, vel_end=60)
    # lead ship rolls over the top of the eight (a breather melody)
    _play_table(sc, 14, 0.0, [
        (266.0, 70, 1.0, 82), (267.0, 69, 0.5, 78), (267.5, 67, 1.5, 80),
        (270.0, 65, 0.75, 78), (270.75, 67, 0.25, 76), (271.0, 69, 2.0, 84),
        (274.0, 74, 1.5, 86), (275.5, 72, 0.5, 82), (276.0, 70, 1.0, 82),
        (277.0, 69, 0.5, 80), (277.5, 70, 0.5, 82), (278.0, 72, 2.0, 86)])
    _bloom(sc, 14, 271.0, 2.0, peak=56)
    _bloom(sc, 14, 278.0, 2.0, peak=60)


def _b_loop_two(sc):
    # loop two: the same climb flown hotter (velocities up, layers earlier)
    for w in range(4):
        t0 = T_LOOP2 + 32.0 * w
        # the last groove bar yields to the snare roll into the drop
        _build_groove(sc, t0, t0 + 32.0 if w < 3 else 404.0, w + 1, vb=6)
        _bass_8ths(sc, t0, 8, BUILD_ROOTS, 80 + 4 * w)
        _chugs(sc, t0, 8, BUILD_ROOTS, 74 + 5 * w)
        _arp_bars(sc, t0, 8, BUILD_CHORDS, 66 + 6 * w, 72 + 6 * w)
        en.pad_block(sc, 1, t0, [BUILD_CHORDS[b % 4] for b in range(8)],
                     span=4.0, size=4, lo=52, hi=76,
                     vel=56 + 4 * w, vel_end=60 + 4 * w)
        sc.note(9, 49, t0, 1.2, 82 + 6 * w, jt=0, jv=3)
    # the inverted fragments: same rhythm, contour flipped (the wing's
    # inversion foreshadowed), climbing a step per cycle
    for c in range(8):
        en.line(sc, 14, T_LOOP2 + 16.0 * c, 67, "dorian", FRAG_INV,
                80 + 2 * c, shift=c, jt=0, jv=3)
    for i, t in enumerate((300.0, 332.0, 364.0, 396.0)):
        _post_pair(sc, t, 76 + 5 * i)
    # strings from the first bar, choir from bar 9 - earlier than loop one
    en.pad_block(sc, 7, T_LOOP2, [BUILD_CHORDS[b % 4] for b in range(32)],
                 span=4.0, size=3, lo=56, hi=76, vel=56, vel_end=70)
    en.pad_block(sc, 8, 312.0, [BUILD_CHORDS[b % 4] for b in range(24)],
                 span=4.0, size=3, lo=55, hi=74, vel=60, vel_end=74)
    # orchestra hits mark the cycle heads, tightening across the build
    _hits_bars(sc, 280.0, 8, [43, 46, 41, 48], 82, step=8.0)
    _hits_bars(sc, 344.0, 16, [43, 46, 41, 48], 90, step=4.0)
    # saw climb-out, then the portamento swoop into the inverted drop
    for i, (p, t) in enumerate(((67, 392.0), (74, 396.0), (77, 400.0))):
        sc.note(5, p, t, 3.9, 80 + 3 * i, jt=0, jv=2)
        _bloom(sc, 5, t, 3.9, peak=56 + 8 * i)
    en.portamento_on(sc, 5, 403.9, time_cc=58)
    sc.note(5, 62, 404.0, 2.0, 82, jt=0, jv=0)
    sc.note(5, 79, 406.0, 2.0, 90, jt=0, jv=0)
    en.portamento_off(sc, 5, 408.05)
    _snare_roll(sc, 404.0, 408.0, 60, 108)
    _riser(sc, 404.0, 84)
    _fills(sc, FILLS_LOOP2,
           vbump_at=lambda s: max(0, int((s - 312) // 32)) * 2)


def _b_drop_two(sc):
    # THE HOOK INVERTED: the wing ship flies loop one upside down
    # (tick-exact mirror about G4), twice, while the lead harmonizes in
    # power-chord dyads and the saw doubles the mirror an octave up.
    _play_hook(sc, 15, 408.0, vbump=-4, mirrored=True)
    _play_hook(sc, 15, 440.0, mirrored=True)
    for off, p, dur, vel in HOOK:
        m = material.mirror(p, AXIS)
        sc.note(5, m + 12, 408.0 + off, dur * 0.98, vel - 12, jt=0, jv=2)
        sc.note(5, m + 12, 440.0 + off, dur * 0.98, vel - 8, jt=0, jv=2)
    for b in range(16):
        bar = 408.0 + 4.0 * b
        r = DROP_ROOTS[b % 8]
        for on, du in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            sc.note(14, r + 12, bar + on, du, 92, jt=0, jv=3)
            sc.note(14, r + 19, bar + on, du, 88, jt=0, jv=3)
    _bass_8ths(sc, 408.0, 16, DROP_ROOTS, 92)
    _four_floor(sc, 408.0, 472.0, 104, 96, 60, 66, hat16=50)
    sc.note(9, 49, 408.0, 1.5, 104, jt=0, jv=3)
    sc.note(9, 57, 440.0, 1.5, 100, jt=0, jv=3)
    _hits_bars(sc, 408.0, 16, DROP_ROOTS, 100, step=2.0)
    _arp_bars(sc, 408.0, 16, DROP_CHORDS, 78, 82)
    en.pad_block(sc, 1, 408.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=4, lo=52, hi=76, vel=70, vel_end=74)
    en.pad_block(sc, 7, 408.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=3, lo=62, hi=81, vel=70, vel_end=74)
    en.pad_block(sc, 8, 408.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=3, lo=55, hi=74, vel=74, vel_end=78)
    _post_stabs(sc, 408.0, 16, 86)
    _fills(sc, FILLS_DROP2)
    _snare_roll(sc, 468.0, 472.0, 70, 112)
    _riser(sc, 468.0, 88)


def _b_exit(sc):
    # the album's "aha": hook and mirror-hook AT ONCE, twice, with a free
    # saw counter-line soaring above all three
    _play_hook(sc, 14, 472.0)
    _play_hook(sc, 15, 472.0, vbump=-4, mirrored=True)
    _play_hook(sc, 14, 504.0, vbump=4)
    _play_hook(sc, 15, 504.0, mirrored=True)
    _play_table(sc, 5, 472.0, SAW_EXIT)
    _play_table(sc, 5, 504.0, SAW_EXIT, vbump=2)
    _bass_8ths(sc, 472.0, 16, DROP_ROOTS, 94)
    _four_floor(sc, 472.0, 536.0, 106, 98, 62, 68, hat16=54)
    sc.note(9, 49, 472.0, 1.5, 106, jt=0, jv=3)
    sc.note(9, 57, 504.0, 1.5, 102, jt=0, jv=3)
    _hits_bars(sc, 472.0, 12, DROP_ROOTS, 102, step=2.0)
    _hits_bars(sc, 520.0, 4, [43, 48, 50, 41], 104, step=1.0)
    _arp_bars(sc, 472.0, 16, DROP_CHORDS, 80, 84)
    en.pad_block(sc, 1, 472.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=4, lo=52, hi=76, vel=72, vel_end=76)
    en.pad_block(sc, 7, 472.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=3, lo=62, hi=81, vel=72, vel_end=76)
    en.pad_block(sc, 8, 472.0, [DROP_CHORDS[b % 8] for b in range(16)],
                 span=4.0, size=3, lo=55, hi=74, vel=76, vel_end=80)
    _post_stabs(sc, 472.0, 16, 88)
    # harp glissandi crown the pass
    for t in (488.0, 520.0):
        for i, p in enumerate((55, 58, 62, 67, 70, 74, 79)):
            sc.note(6, p, t + 0.125 * i, 0.2, 68 + i, jt=0, jv=3)
    _fills(sc, FILLS_EXIT)
    _riser(sc, 532.0, 70)


def _b_out(sc):
    # throttle back: the field again, one last ASCENT and its mirrored
    # landing, everything gliding home to Gm
    sc.note(9, 49, T_OUT, 1.5, 92, jt=0, jv=3)
    en.pad_block(sc, 1, T_OUT, [GM_, F__, BB_, GM_, GM_, GM_],
                 span=8.0, size=4, lo=52, hi=76, vel=60, vel_end=40)
    en.pad_block(sc, 7, T_OUT, [GM_, F__, BB_, GM_], span=12.0, size=3,
                 lo=56, hi=76, vel=50, vel_end=36)
    en.pad_block(sc, 8, T_OUT, [GM_, GM_, GM_], span=16.0, size=3,
                 lo=55, hi=72, vel=56, vel_end=40)
    for b in range(4, 10):
        r = [43, 43, 41, 46, 43, 43][b - 4]
        sc.note(2, r, T_OUT + 4.0 * b, 3.6,
                int(en.lerp(58, 44, (b - 4) / 5)), jt=0, jv=3)
    for b in range(4):
        bar = T_OUT + 4.0 * b
        sc.note(9, 36, bar, 0.25, int(en.lerp(60, 46, b / 3)), jt=0, jv=3)
        sc.note(9, 36, bar + 2.0, 0.25, int(en.lerp(56, 44, b / 3)),
                jt=0, jv=3)
        for i in range(8):
            sc.note(9, 42, bar + 0.5 * i, 0.2,
                    int(en.lerp(46, 36, b / 3)), jt=0, jv=3)
    for b in range(4, 8):
        bar = T_OUT + 4.0 * b
        for k in range(4):
            sc.note(9, 51, bar + k, 0.3, int(en.lerp(46, 38, (b - 4) / 3)),
                    jt=0, jv=3)
    # gentle arp fade
    _arp_bars(sc, T_OUT, 6, [GM_, GM_, F__, F__, BB_, BB_], 56, 44)
    # harp winds down
    for b in range(6):
        chord = [GM_, F__, BB_, GM_, GM_, GM_][b]
        en.arp(sc, 6, [chord[2] + 12, chord[1] + 12, chord[0] + 12, chord[2],
                       chord[1]], T_OUT + 8.0 * b, 8, 0.5,
               int(en.lerp(58, 42, b / 5)), pattern="up", gate=1.5)
    # the final pinned ASCENT - the lead ship pulls up and away
    material.play_ascent(sc, 14, 552.0, 67, vel=84, jt=0)
    _bloom(sc, 14, 553.5, 2.5, peak=72)
    _play_table(sc, 14, 0.0, [
        (558.0, 74, 1.0, 78), (559.0, 72, 0.5, 74), (559.5, 70, 1.5, 76),
        (562.0, 69, 1.0, 72), (563.0, 67, 5.0, 74)])
    _bloom(sc, 14, 563.0, 5.0, peak=60)
    # the wing ship lands: the ASCENT mirrored about the tonic, descending
    _play_table(sc, 15, 0.0, [
        (560.0, 67, 0.5, 72), (560.5, 60, 0.5, 70), (561.0, 55, 0.5, 68),
        (561.5, 48, 2.5, 70)])
    # final harp roll over the closing Gm
    en.strum(sc, 6, [55, 58, 62, 67, 70, 74, 79], 576.0, 7.5, 60,
             spread=0.06)


BUILDERS = [_b_entry, _b_loop_one, _b_over_the_top, _b_drop_one,
            _b_half_roll, _b_loop_two, _b_drop_two, _b_exit, _b_out]


# ---------------------------------------------------------------------------
# Verification config
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {1, 29, 39, 46, 49, 52, 55, 56, 80, 81, 89, 98,
                     117, 118, 119}
CENTERED_CHANNELS = {1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
NOTE_RANGES = {
    0: (55, 95), 1: (50, 80), 2: (36, 63), 3: (67, 91), 4: (55, 84),
    5: (55, 96), 6: (48, 84), 7: (50, 84), 8: (52, 79), 9: (35, 57),
    10: (44, 64), 11: (46, 60), 12: (50, 70), 13: (62, 62),
    14: (50, 92), 15: (46, 80),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (266.0, 283.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (the proven t16 shapes)
# ---------------------------------------------------------------------------

_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ
_GDOR = {7, 9, 10, 0, 2, 4, 5}


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


def _onset_map(ons, lo_t, hi_t):
    """tick -> pitch for onsets inside [lo_t, hi_t) (last write wins)."""
    return {t: p for t, p, _v in ons if lo_t <= t < hi_t}


# ---------------------------------------------------------------------------
# The track oracles
# ---------------------------------------------------------------------------

def oracles(sc, info, spans):
    checks = []

    # --- hook_wellformed: the data invariants the whole design rests on ---
    f = []
    if len(HOOK) != 52:
        f.append(f"hook has {len(HOOK)} notes, want 52")
    if abs(max(o + d for o, _p, d, _v in HOOK) - HOOK_LEN) > 1e-9:
        f.append("hook does not span exactly 32 beats")
    onsets = [o for o, _p, _d, _v in HOOK]
    if onsets != sorted(onsets) or len(set(onsets)) != len(onsets):
        f.append("hook onsets must strictly increase")
    hp = {o: p for o, p, _d, _v in HOOK}
    for db in HOOK_DOWNBEATS:
        p = hp.get(db)
        if p is None:
            f.append(f"no hook onset on downbeat {db}")
        elif p % 12 not in {5, 7, 9}:
            f.append(f"hook downbeat {db} pitch {p} not pc F/G/A "
                     f"(mirror consonance breaks)")
    for o, p, _d, _v in HOOK:
        if p % 12 not in _GDOR:
            f.append(f"hook pitch {p} at {o} not G dorian")
        if material.mirror(p, AXIS) % 12 not in _GDOR:
            f.append(f"mirror of {p} leaves G dorian")
    for (o1, p1, _d1, _v1), (o2, p2, _d2, _v2) in zip(HOOK, HOOK[1:]):
        if p1 == p2:
            f.append(f"hook repeats pitch {p1} at {o2} (kills the mirror "
                     f"motion count)")
    if material.mirror(material.mirror(74, AXIS), AXIS) != 74:
        f.append("material.mirror is not an involution at the track axis")
    checks.append(("hook_wellformed", f))

    # --- hook_inversion_exact: DROP1 hook on lead; DROP2 mirrored on wing,
    # tick-exact over all 32 beats, both statements, nothing else in the
    # featured lane ---
    f = []
    ons14 = _note_ons(sc, 14)
    ons15 = _note_ons(sc, 15)
    set14 = {(t, p) for t, p, _v in ons14}
    set15 = {(t, p) for t, p, _v in ons15}
    for stmt in (200.0, 232.0):
        for o, p, _d, _v in HOOK:
            if (_tick(stmt + o), p) not in set14:
                f.append(f"lead hook note missing at {stmt + o} pitch {p}")
    for stmt in (408.0, 440.0):
        for o, p, _d, _v in HOOK:
            m = material.mirror(p, AXIS)
            if (_tick(stmt + o), m) not in set15:
                f.append(f"wing mirror note missing at {stmt + o} "
                         f"pitch {m}")
    n14 = sum(1 for t, _p, _v in ons14
              if _tick(200.0) <= t < _tick(264.0))
    if n14 != 104:
        f.append(f"drop-one lead lane has {n14} onsets, want exactly "
                 f"2 x 52 (the hook and nothing else)")
    n15 = sum(1 for t, _p, _v in ons15
              if _tick(408.0) <= t < _tick(472.0))
    if n15 != 104:
        f.append(f"drop-two wing lane has {n15} onsets, want exactly "
                 f"2 x 52 (the mirror and nothing else)")
    checks.append(("hook_inversion_exact", f[:8]))

    # --- exit_double_hook: both lanes complete AND simultaneous, pairwise
    # consonant on every downbeat ---
    f = []
    for stmt in (472.0, 504.0):
        for o, p, _d, _v in HOOK:
            if (_tick(stmt + o), p) not in set14:
                f.append(f"exit lead hook missing at {stmt + o}")
            m = material.mirror(p, AXIS)
            if (_tick(stmt + o), m) not in set15:
                f.append(f"exit wing mirror missing at {stmt + o}")
        for db in HOOK_DOWNBEATS:
            lead = hp[db]
            wing = material.mirror(lead, AXIS)
            if (lead - wing) % 12 not in _CONSONANT:
                f.append(f"exit downbeat {stmt + db}: lead {lead} vs "
                         f"wing {wing} dissonant")
    for lane, ch in (("lead", 14), ("wing", 15)):
        n = sum(1 for t, _p, _v in _note_ons(sc, ch)
                if _tick(472.0) <= t < _tick(536.0))
        if n != 104:
            f.append(f"exit {lane} lane has {n} onsets, want 104")
    checks.append(("exit_double_hook", f[:8]))

    # --- exit_counterpoint: the free saw line vs the wing lane ---
    f = []
    saw = [(t, p) for t, p, _v in _note_ons(sc, 5)
           if _tick(472.0) <= t < _tick(536.0)]
    wing_exit = [(t, p) for t, p, _v in ons15
                 if _tick(472.0) <= t < _tick(536.0)]
    wing_ticks = {t for t, _p in wing_exit}
    if len(saw) < 16:
        f.append(f"saw counter-line has only {len(saw)} onsets")
    coincident = sum(1 for t, _p in saw if t in wing_ticks)
    if saw and coincident / len(saw) > 0.5:
        f.append(f"{coincident}/{len(saw)} saw onsets coincide with the "
                 f"wing (need >= 50% independent)")

    def _pitch_at(lane, t):
        best = None
        for tt, pp in lane:
            if tt <= t:
                best = pp
            else:
                break
        return best

    good = total = 0
    for (t1, p1), (t2, p2) in zip(saw, saw[1:]):
        w1, w2 = _pitch_at(wing_exit, t1), _pitch_at(wing_exit, t2)
        if w1 is None or w2 is None:
            continue
        ds, dw = p2 - p1, w2 - w1
        total += 1
        if (ds > 0 > dw) or (ds < 0 < dw) or \
                (ds == 0) != (dw == 0) and (ds == 0 or dw == 0):
            good += 1
    if total and good / total < 0.6:
        f.append(f"saw-vs-wing contrary+oblique {good}/{total} < 60%")
    doubled = 0
    dbs = [472.0 + 4.0 * i for i in range(16)]
    for db in dbs:
        t = _tick(db)
        sp = _pitch_at(saw, t)
        lp = _pitch_at([(tt, pp) for tt, pp, _v in ons14
                        if _tick(472.0) <= tt < _tick(536.0)], t)
        wp = _pitch_at(wing_exit, t)
        if sp is None or lp is None or wp is None:
            f.append(f"downbeat {db}: a lane is silent")
            continue
        for a, b, na, nb in ((sp, lp, "saw", "lead"),
                             (sp, wp, "saw", "wing"),
                             (lp, wp, "lead", "wing")):
            if (a - b) % 12 not in _CONSONANT:
                f.append(f"downbeat {db}: {na} {a} vs {nb} {b} dissonant")
        if sp % 12 == wp % 12:
            doubled += 1
    if doubled > 0.25 * len(dbs):
        f.append(f"saw doubles the wing pc on {doubled}/{len(dbs)} "
                 f"downbeats (> 25%)")
    checks.append(("exit_counterpoint", f[:8]))

    # --- duo_roles: who flies which position, per drop ---
    f = []
    for on, off, p in _note_spans(sc, 15):
        if _tick(200.0) <= on < _tick(264.0):
            if (off - on) / _PPQ > 0.6:
                f.append(f"drop-one wing note at {on / _PPQ:.2f} too long "
                         f"for a chug")
            if p > 62:
                f.append(f"drop-one wing pitch {p} above the chug register")
    d2_14 = [(on, off) for on, off, _p in _note_spans(sc, 14)
             if _tick(408.0) <= on < _tick(472.0)]
    if len(d2_14) < 24:
        f.append(f"drop-two lead harmony too thin ({len(d2_14)} notes)")
    if any(abs(on - _tick(408.75)) < 2 for on, _off in d2_14):
        f.append("drop-two lead states the hook pickup (should harmonize, "
                 "not double the wing)")
    if any((off - on) / _PPQ > 1.6 for on, off in d2_14):
        f.append("drop-two lead notes must stay stabs (<= 1.6 beats)")
    checks.append(("duo_roles", f[:8]))

    # --- halfroll_pivot: the key-area shift, pinned via the bass roots ---
    f = []
    ons2 = _note_ons(sc, 2)
    want = [(264.0, 10), (268.0, 0), (272.0, 2), (276.0, 2)]
    pmap = {t: p for t, p, _v in ons2}
    for beat, pc in want:
        p = pmap.get(_tick(beat))
        if p is None:
            f.append(f"no bass root on half-roll downbeat {beat}")
        elif p % 12 != pc:
            f.append(f"half-roll downbeat {beat}: bass pc {p % 12}, "
                     f"want {pc}")
    for t, p, _v in ons2:
        if _tick(264.0) <= t < _tick(280.0) and p % 12 == 7:
            f.append(f"bass touches G during the pivot at "
                     f"{t / _PPQ:.2f} (the pivot must leave home)")
            break
    p280 = pmap.get(_tick(280.0))
    if p280 is None or p280 % 12 != 7:
        f.append("loop two must land back on a G root at beat 280")
    checks.append(("halfroll_pivot", f))

    # --- build_drop_contour: rising builds, later drops bigger, hushes ---
    f = []
    sums = _bar_sums(sc)
    for name, t0 in (("loop one", 64.0), ("loop two", 280.0)):
        wins = [_mean_barsum(sums, t0 + 32.0 * w, t0 + 32.0 * (w + 1))
                for w in range(4)]
        for a, b in zip(wins, wins[1:]):
            if b <= a:
                f.append(f"{name} windows not strictly rising: "
                         f"{[round(w) for w in wins]}")
                break
    d1 = _mean_barsum(sums, 200.0, 264.0)
    d2 = _mean_barsum(sums, 408.0, 472.0)
    ex = _mean_barsum(sums, 472.0, 536.0)
    if d2 <= d1:
        f.append(f"drop two ({d2:.0f}) not bigger than drop one ({d1:.0f})")
    if ex <= d1:
        f.append(f"exit pass ({ex:.0f}) not bigger than drop one "
                 f"({d1:.0f})")
    roll = _mean_barsum(sums, 264.0, 280.0)
    if roll >= 0.5 * d1:
        f.append(f"half-roll ({roll:.0f}) not under 50% of drop one "
                 f"({d1:.0f})")
    tail = _mean_barsum(sums, 568.0, 584.0)
    if tail >= 0.5 * ex:
        f.append(f"out tail ({tail:.0f}) not under 50% of the exit "
                 f"({ex:.0f})")
    checks.append(("build_drop_contour", f))

    # --- fill_escalation: every scheduled shape realized tick-exact;
    # per-window counts strictly rise through each build; >= 5 shapes per
    # build; drops thinned ---
    f = []
    fill_ons = sorted(_note_ons(sc, 10) + _note_ons(sc, 11))
    fill_set = {(t, p) for t, p, _v in fill_ons}
    for start, shape in ALL_FILLS:
        lib = material.FILL_LIB[shape]
        for lane in ("tom", "syn"):
            for off, p, _d, _v in lib.get(lane, ()):
                if (_tick(start + off), p) not in fill_set:
                    f.append(f"fill {shape}@{start}: {lane} note {p} "
                             f"missing at +{off}")
    for name, t0 in (("loop one", 64.0), ("loop two", 280.0)):
        counts = [sum(1 for t, _p, _v in fill_ons
                      if _tick(t0 + 32.0 * w) <= t < _tick(t0 + 32.0 * (w + 1)))
                  for w in range(4)]
        for a, b in zip(counts, counts[1:]):
            if b <= a:
                f.append(f"{name} fill counts not strictly rising: {counts}")
                break
    if len({s for _t, s in FILLS_LOOP1}) < 5:
        f.append("loop one uses fewer than 5 fill shapes")
    if len({s for _t, s in FILLS_LOOP2}) < 5:
        f.append("loop two uses fewer than 5 fill shapes")
    for name, lo in (("drop one", 200.0), ("drop two", 408.0)):
        n = sum(1 for t, _p, _v in fill_ons
                if _tick(lo) <= t < _tick(lo + 32.0))
        if n > 12:
            f.append(f"{name} first half not thinned: {n} fill notes > 12")
    checks.append(("fill_escalation", f[:8]))

    # --- big_fill_into_drops: >= 20-note unbroken fill into every drop ---
    f = []
    for drop in (200.0, 408.0, 472.0):
        window = [t for t, _p, _v in fill_ons
                  if _tick(drop - 4.5) <= t < _tick(drop)]
        if len(window) < 20:
            f.append(f"only {len(window)} fill notes in the 4.5 beats "
                     f"into {drop}")
            continue
        gaps = [(b - a) / _PPQ for a, b in zip(window, window[1:])]
        if max(gaps) > 0.75:
            f.append(f"fill into {drop} breaks (gap {max(gaps):.2f} beats)")
        if window[-1] < _tick(drop - 0.5):
            f.append(f"fill into {drop} stops early")
    checks.append(("big_fill_into_drops", f))

    # --- ascent_pinned: the album cell, stated by the lead ship ---
    f = []
    for t0 in (32.0, 552.0):
        for on, _du, s in material.ASCENT_CELL:
            if (_tick(t0 + on), 67 + s) not in set14:
                f.append(f"ASCENT note {67 + s} missing at {t0 + on}")
    checks.append(("ascent_pinned", f))

    # --- soar_and_sweep: the synth discipline, all four devices ---
    f = []
    cc74 = _cc_lane(sc, 1, 74)
    if cc74:
        vals = [v for _t, v in cc74]
        if max(vals) - min(vals) < 60:
            f.append(f"CC74 macro-sweep span {max(vals) - min(vals)} < 60")
        loop2 = [v for t, v in cc74
                 if _tick(280.0) <= t <= _tick(408.0)]
        if not loop2 or loop2[0] > 48 or max(loop2) < 100:
            f.append("loop-two CC74 sweep must climb from <= 48 to >= 100")
    else:
        f.append("no CC74 lane on the pad")
    riser_spans = _note_spans(sc, 13)
    for t in (196.0, 404.0, 468.0, 532.0):
        hit = [s for s in riser_spans if abs(s[0] - _tick(t)) <= 2]
        if not hit:
            f.append(f"no riser at beat {t}")
        elif (hit[0][1] - hit[0][0]) / _PPQ < 3.4:
            f.append(f"riser at {t} too short")
    soar = [s for s in _note_spans(sc, 5)
            if s[0] <= _tick(192.1) and s[1] >= _tick(199.5)]
    if not soar:
        f.append("no >= 6-beat held saw soar over the top")
    else:
        cc1 = [v for t, v in _cc_lane(sc, 5, 1)
               if _tick(192.0) <= t <= _tick(200.0)]
        if not cc1 or max(cc1) < 50:
            f.append("the over-the-top soar lacks its CC1 bloom")
    cc65 = _cc_lane(sc, 5, 65)
    on_ev = [t for t, v in cc65 if v >= 64 and t <= _tick(404.05)]
    off_ev = [t for t, v in cc65
              if v < 64 and _tick(407.5) <= t <= _tick(409.0)]
    p404 = {p for t, p, _v in _note_ons(sc, 5)
            if abs(t - _tick(404.0)) <= 2}
    p406 = {p for t, p, _v in _note_ons(sc, 5)
            if abs(t - _tick(406.0)) <= 2}
    if not (on_ev and off_ev and p404 and p406
            and max(p406) - min(p404) >= 12):
        f.append("no >= 12-semitone portamento swoop into drop two")
    checks.append(("soar_and_sweep", f))

    # --- layer_density: the highly-layered promise, counted ---
    f = []
    def _active(lo, hi):
        return sum(1 for ch in sc.events
                   if any(_tick(lo) <= t < _tick(hi)
                          for t, _p, _v in _note_ons(sc, ch)))
    n_exit = _active(472.0, 536.0)
    n_d2 = _active(408.0, 472.0)
    if n_exit < 15:
        f.append(f"exit pass runs only {n_exit} channels (want >= 15)")
    if n_d2 < 14:
        f.append(f"drop two runs only {n_d2} channels (want >= 14)")
    checks.append(("layer_density", f))

    return checks


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — trimmed inner windows, margins >= 3 dB where
# a difference is claimed
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def win_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    d1 = win_db(202.0, 262.0)
    d2 = win_db(410.0, 470.0)
    ex = win_db(474.0, 534.0)
    checks = []
    f = []
    if d2 < d1 - 1.0:
        f.append(f"inverted drop ({d2:.1f} dB) quieter than drop one "
                 f"({d1:.1f} dB)")
    checks.append(("audio_drop2_holds", f))
    f = []
    if ex < d1 - 1.0:
        f.append(f"exit pass ({ex:.1f} dB) below drop one ({d1:.1f} dB)")
    checks.append(("audio_exit_holds", f))
    f = []
    roll = win_db(265.0, 279.0)
    if roll > d1 - 3.0:
        f.append(f"half-roll ({roll:.1f} dB) not a breather vs drop one "
                 f"({d1:.1f} dB)")
    checks.append(("audio_halfroll_breather", f))
    f = []
    tail = win_db(566.0, 582.0)
    if tail > ex - 6.0:
        f.append(f"out tail ({tail:.1f} dB) does not fade vs the exit "
                 f"({ex:.1f} dB)")
    checks.append(("audio_out_fades", f))
    return checks
