"""t03_run_the_rooftops.py — "Run the Rooftops" (Big Weather, track 3).

DRUM-FEATURE #1: rooftop-chase riff-rock in D mixolydian at 132 BPM.  A
bVII-flavoured drive-guitar RIFF bookends the song and powers every
chorus (oracle-pinned recurrence); verses run on wah rhythm guitar
(CC74+CC71 funk scratch) over a relentless eighth-note bass; brass
stabs punch the choruses.  The headline is the two DRUM SOLOS: SOLO I
(16 bars) builds from a hat/ride conversation through china<->crash-1
antiphony and high-tom<->floor-tom circuits into 32nd-note bursts and a
crash-trading summit; SOLO II (8 bars) reprises the antiphony figure
(oracle-pinned, recomputed not copied) and pushes the cymbal
conversation to 32nd-note hat<->ride shimmer before a rising tom rush.
Solo orchestration foregrounds the kit's WIDE voices (HLD §3 drum-stage
note); the pan table itself is pinned in verify.DRUM_PAN.

Form (HLD §4, bespoke):
  riff | verse1 | chorus1 | SOLO I (16 bars) | verse2 | chorus2 |
  breakdown | SOLO II (8 bars, cymbal-antiphony reprise) |
  double final chorus | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 3
TITLE = "Run the Rooftops"
FILE = "03 - Run the Rooftops.mid"
SEED = 20260703

BPM = 132.0

# Channels (HLD §3, per-track deviation: trumpet on 11, no strings/choir —
# riff-rock skips the choir per HLD D3; CHOIR_SPEC deliberately omitted).
PIANO, WAH, DRIVE, BASS = 0, 1, 2, 3
LEAD, DRUMS, BRASS, TRUMPET = 6, 9, 10, 11

_SECTIONS = [
    ("riff",          0.0,  32.0),
    ("verse1",       32.0,  96.0),
    ("chorus1",      96.0, 160.0),
    ("drum_solo_1", 160.0, 224.0),
    ("verse2",      224.0, 288.0),
    ("chorus2",     288.0, 352.0),
    ("breakdown",   352.0, 384.0),
    ("drum_solo_2", 384.0, 416.0),
    ("final_chorus", 416.0, 544.0),
    ("outro",       544.0, 592.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 0)],                  # D mixolydian: one sharp
    channels=[
        (PIANO,   "piano",        0,  96, 64, 45),
        (WAH,     "wah guitar",  26,  92, 48, 35),
        (DRIVE,   "drive guitar", 29,  94, 80, 30),
        (BASS,    "bass guitar", 33, 105, 64, 20),
        (LEAD,    "lead synth",  84,  90, 64, 45),
        (DRUMS,   "drums",        0, 110, 64, 40),
        (BRASS,   "brass",       61,  92, 64, 45),
        (TRUMPET, "trumpet",     57,  86, 64, 50),
    ],
    program_changes=[
        (DRIVE, 416.0, 30),     # overdrive -> distortion for the double chorus
        (DRIVE, 544.0, 29),     # back to overdrive for the outro riff
    ],
)

# ---------------------------------------------------------------------------
# Harmony — D mixolydian (the bVII C-natural is the chase's fuel).
# ---------------------------------------------------------------------------

D2, D3, D4 = en.n("D2"), en.n("D3"), en.n("D4")
_MODE = "mixolydian"

VERSE_PROG = [1, 7, 4, 1]           # D  C  G  D
CHORUS_PROG = [1, 1, 4, 4]          # D  D  G  G  (rides the riff transposition)
BREAK_PROG = [6, 4, 1, 7]           # Bm G  D  C


def _pv(deg: int, octave: int = 0) -> int:
    return en.pitch(D2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(D2, _MODE, deg)]


# The RIFF — drive-guitar bookend and chorus engine (jt=0 throughout: the
# recurrence is oracle-pinned).  (beat, semi offset from the root, dur,
# vel, power?).  Statements transpose wholesale (semis=+5 -> G riff).
_RIFF = [
    (0.00,  0, 0.70, 108, True),
    (0.75,  0, 0.45,  98, True),
    (1.50, 10, 0.45, 102, True),    # the bVII bite
    (2.25,  0, 0.45, 104, True),
    (3.00,  7, 0.45, 100, True),    # A
    (3.50,  5, 0.95, 104, True),    # G, held
    (4.50,  0, 0.70, 106, True),
    (5.25,  0, 0.45,  96, True),
    (6.00, 10, 0.45, 100, True),
    (6.50, 12, 0.30,  92, False),   # single-note turn, octave up
    (6.83, 14, 0.30,  90, False),
    (7.16, 17, 0.30,  94, False),
    (7.50, 16, 0.45,  96, False),   # F# pulls the corner back to D
]

# The chorus HOOK — (degree, start, dur) over 16 beats (D D G G), lead
# synth; long notes get CC1 vibrato blooms.
_HOOK = [
    (1, 0.0, 0.75), (1, 0.75, 0.25), (3, 1.0, 1.0), (5, 2.0, 1.5),
    (6, 3.5, 0.5),
    (6, 4.0, 0.75), (6, 4.75, 0.25), (8, 5.0, 1.0), (7, 6.0, 2.0),
    (8, 8.0, 0.75), (8, 8.75, 0.25), (10, 9.0, 1.0), (9, 10.0, 1.5),
    (8, 11.5, 0.5),
    (7, 12.0, 0.5), (8, 12.5, 0.5), (7, 13.0, 0.5), (5, 13.5, 0.5),
    (4, 14.0, 1.9),
]

_HOOK_LYRICS = ["run the rooftops", "wire to wire",
                "don't look down", "outrun the sky"]

# The cymbal-antiphony figure — china (R) calls, crash-1 (L) answers,
# splash and crash-2 close the sentence, kick anchors underneath.  Stated
# once in SOLO I and TWICE in SOLO II (the reprise); jt=0/jv=0 so the
# oracle can recompute every stroke exactly.  (offset, key, vel).
_ANTIPHONY = [
    (0.0, 52, 112), (0.5, 36, 96), (1.5, 49, 106), (2.0, 36, 92),
    (2.5, 52, 104), (3.5, 49, 102), (4.0, 52, 108), (4.5, 36, 96),
    (5.5, 49, 104), (6.0, 55, 98), (6.5, 57, 102), (7.0, 49, 100),
    (7.5, 52, 106),
]

_TOM_CIRCUIT = [50, 48, 47, 45, 43, 41]      # high -> floor, L -> R


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _power(sc, root: int, beat: float, dur: float, vel: int) -> None:
    """Root + fifth + octave on the drive guitar (jt=0: riff-pinned)."""
    for i, off in enumerate((0, 7, 12)):
        sc.note(DRIVE, root + off, beat, dur, vel - 4 * i, jt=0, jv=3)


def _riff_x(sc, t0: float, reps: int, vel_scale: float = 1.0,
            semis: int = 0) -> None:
    """State the RIFF `reps` times (8 beats each), transposed by `semis`."""
    for r in range(reps):
        base = t0 + 8.0 * r
        for beat, off, dur, vel, power in _RIFF:
            v = max(1, int(round(vel * vel_scale)))
            if power:
                _power(sc, D2 + semis + off, base + beat, dur, v)
            else:
                sc.note(DRIVE, D2 + semis + off, base + beat, dur, v,
                        jt=0, jv=3)


def _bass_run(sc, t0: float, prog: list[int], reps: int = 1,
              vel: int = 96, offs: tuple[int, ...] = (0, 0, 2, 3, 4, 3, 2, 1),
              ) -> None:
    """The chase bass: relentless eighths, mostly stepwise (BASS_SPEC)."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        for k, off in enumerate(offs):
            accent = k in (0, 4)
            j0 = 0 if (i == 0 and k == 0) else 2
            sc.note(BASS, _pv(deg + off), b + 0.5 * k, 0.45,
                    vel + (6 if accent else -6), jt=j0, jv=3)


_CHORUS_OFFS = (0, 0, 7, 0, 4, 3, 2, 1)      # octave pop + scale fall


def _piano_pump(sc, t0: float, bars: int, prog: list[int],
                vel: int = 66) -> None:
    """Verse piano: LH roots on 1/3, RH triad eighths driving the chase."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        j0 = 0 if i == 0 else 3
        sc.note(PIANO, _pv(deg, 1), b, 0.9, vel + 8, jt=j0, jv=4)
        sc.note(PIANO, _pv(deg, 1), b + 2.0, 0.9, vel + 4, jt=3, jv=4)
        for beat in (0.5, 1.0, 1.5, 2.5, 3.0, 3.5):
            acc = 8 if beat in (0.5, 2.5) else 0
            for p in tri:
                sc.note(PIANO, p, b + beat, 0.4, vel - 8 + acc, jt=3, jv=4)


def _piano_anthem(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 84) -> None:
    """Chorus piano: block chords, octave crown, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _pv(deg, 1)
        j0 = 0 if i == 0 else 3
        for beat, dur, dv in ((0.0, 1.4, 0), (1.5, 0.4, -8), (2.0, 1.4, 0),
                              (3.5, 0.4, -6)):
            jt = j0 if beat == 0.0 else 3
            sc.note(PIANO, r, b + beat, dur, vel + dv, jt=jt, jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel + dv - 5, jt=jt, jv=4)
        sc.note(PIANO, tri[2] + 12, b + 3.0, 0.9, vel + 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


_FUNK = [(0.0, True), (0.5, False), (0.75, True), (1.25, False),
         (1.5, True), (2.0, True), (2.5, False), (2.75, True),
         (3.25, False), (3.5, True)]


def _wah_funk(sc, t0: float, bars: int, prog: list[int],
              vel: int = 68) -> None:
    """Wah-guitar 16th scratch: fourths dyads, accents riding the LFO."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _pv(prog[i % len(prog)], 1)
        for k, (beat, accent) in enumerate(_FUNK):
            v = vel + (4 if accent else -14)
            j0 = 0 if (i == 0 and k == 0) else 3
            sc.note(WAH, r, b + beat, 0.14, v, jt=j0, jv=4)
            sc.note(WAH, r + 5, b + beat, 0.14, v - 6, jt=j0, jv=4)


def _wah_chucks(sc, t0: float, bars: int, prog: list[int],
                vel: int = 62) -> None:
    """Chorus wah guitar: off-beat up-chucks, octave above the funk."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _pv(prog[i % len(prog)], 2)
        for beat in (0.5, 1.5, 2.5, 3.5):
            sc.note(WAH, r, b + beat, 0.18, vel, jt=3, jv=4)
            sc.note(WAH, r + 5, b + beat, 0.18, vel - 6, jt=3, jv=4)


def _wah_pedal(sc, t0: float, dur: float, lo: int = 38, hi: int = 108,
               cpb: float = 0.5, res: int = 88) -> None:
    """The wah pedal itself: CC74 LFO + CC71 resonance bite."""
    sc.cc(WAH, 71, res, t0)
    en.wah(sc, WAH, t0, dur, lo=lo, hi=hi, cycles_per_beat=cpb)


def _brass_stabs(sc, t0: float, bars: int, prog: list[int],
                 vel: int = 94) -> None:
    """Section stabs on the &-of-2 and &-of-4; every 4th bar a growl."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = en.triad(D3, _MODE, prog[i % len(prog)])
        if i % 4 == 3:
            for p in tri:
                sc.note(BRASS, p, b, 3.5, vel - 8, jt=0, jv=3)
            en.at_curve(sc, BRASS, [(b, 16), (b + 2.0, 92), (b + 3.4, 28)],
                        step=0.5)
        else:
            for beat in (1.5, 3.5):
                for p in tri:
                    sc.note(BRASS, p, b + beat, 0.35, vel, jt=0, jv=3)
    en.expr_curve(sc, BRASS, [(t0, 74), (t0 + 2.0 * bars, 104),
                              (t0 + 4.0 * bars - 0.5, 84)], step=1.0)


_DESCANT = [(5, 0.0, 3.5), (6, 4.0, 3.5), (8, 8.0, 3.5), (7, 12.0, 2.0),
            (6, 14.0, 1.9)]


def _trumpet_calls(sc, t0: float, reps: int, vel: int = 88,
                   full: bool = False) -> None:
    """Trumpet: chorus-2 answering calls, or the full final descant."""
    for r in range(reps):
        base = t0 + 16.0 * r
        if full:
            en.line(sc, TRUMPET, base, D4, _MODE, _DESCANT, vel,
                    jt=0, jv=0, octave=1, gate=0.97)
            en.cc_curve(sc, TRUMPET, 2,
                        [(base, 44), (base + 8.0, 96), (base + 15.5, 52)],
                        step=1.0)
        else:
            for deg, start, dur in ((5, 2.0, 1.5), (6, 6.0, 1.5),
                                    (8, 10.0, 1.5), (7, 14.0, 1.5)):
                b = base + start
                sc.note(TRUMPET, _pv(deg, 3), b, dur, vel, jt=0, jv=3)
                en.cc_curve(sc, TRUMPET, 2, [(b, 40), (b + 0.8, 90),
                                             (b + dur, 46)], step=0.25)


def _lead_hook(sc, t0: float, reps: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The chorus hook; CC1 vibrato blooms on every long note."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, D4, _MODE, _HOOK, vel, jt=0, jv=0,
                gate=0.98)
        for deg, start, dur in _HOOK:
            if dur >= 1.5:
                b = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(b + 0.25, 0), (b + dur * 0.6, 56),
                             (b + dur, 10)], step=0.15)
        if lyrics and r == 0:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


def _groove(sc, t0: float, bars: int, intensity: float, *,
            ride: bool = False, crash_in: bool = False, china: bool = False,
            fills: bool = True) -> None:
    """The band kit: gallop kick, ghost snares, velocity-shaped hats."""
    for i in range(bars):
        b = t0 + 4.0 * i
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        v = int(round(en.lerp(70, 106, intensity)))
        if crash_in and first:
            sc.hit(49, b, min(122, v + 14), jt=0)
        if china and i % 4 == 2:
            sc.hit(52, b, v + 4, jt=2)
        sc.hit(36, b, v + 10, jt=0 if first else 2)
        sc.hit(36, b + 0.75, v - 2, jt=2)
        sc.hit(36, b + 2.5, v + 4, jt=2)
        sc.hit(38, b + 1.0, v + 12, jt=2, jv=4)
        sc.hit(38, b + 3.0, v + 12, jt=2, jv=4)
        if intensity < 0.9:
            sc.hit(38, b + 1.75, max(16, v - 48), jt=3, jv=6)
            sc.hit(38, b + 3.75, max(16, v - 52), jt=3, jv=6)
        key = 51 if ride else 42
        for k in range(8):
            if fill_bar and k >= 5:
                continue
            sc.hit(key, b + 0.5 * k, max(20, v - (8 if k % 2 == 0 else 24)),
                   jt=2, jv=5)
        if ride and i % 2 == 1:
            sc.hit(53, b + 2.0, v - 4, jt=2)
        if not ride and not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 16, jt=2)
        if fill_bar:
            run_keys = [38, 38, 50, 48, 47, 45, 43, 41]
            for k, key2 in enumerate(run_keys):
                sc.hit(key2, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 20, v + 14, k / 7)), jt=2)


def _antiphony(sc, t0: float, vel_off: int = 0) -> None:
    """The oracle-pinned cymbal antiphony (jt=0/jv=0 — exact strokes)."""
    for off, key, vel in _ANTIPHONY:
        sc.hit(key, t0 + off, max(1, min(127, vel + vel_off)), jt=0, jv=0)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def riff_intro(sc) -> None:
    _riff_x(sc, 0.0, 4)
    _groove(sc, 8.0, 6, 0.55, crash_in=True)
    _bass_run(sc, 16.0, VERSE_PROG, vel=92)
    _wah_pedal(sc, 24.0, 8.0, cpb=0.5)
    _wah_funk(sc, 24.0, 2, [1, 1], vel=62)
    en.echo_throw(sc, DRIVE, 30.0, base=0, peak=72, release=2.0)


def verse1(sc) -> None:
    t0 = 32.0
    _wah_pedal(sc, t0, 64.0, cpb=0.5, res=88)
    _wah_funk(sc, t0, 16, VERSE_PROG, vel=66)
    _piano_pump(sc, t0, 16, VERSE_PROG, vel=62)
    _bass_run(sc, t0, VERSE_PROG, reps=4, vel=92)
    _groove(sc, t0, 16, 0.5)


def _chorus(sc, t0: float, bars: int, *, vel_lift: int = 0,
            ride: bool = False, china: bool = False, lyrics: bool = False,
            bass: bool = True, drums: bool = True) -> None:
    for s in range(bars // 2):
        _riff_x(sc, t0 + 8.0 * s, 1, vel_scale=1.0 + vel_lift / 100.0,
                semis=0 if s % 2 == 0 else 5)
    _piano_anthem(sc, t0, bars, CHORUS_PROG, vel=84 + vel_lift)
    _wah_pedal(sc, t0, 4.0 * bars, cpb=0.25, res=96)
    _wah_chucks(sc, t0, bars, CHORUS_PROG, vel=62 + vel_lift)
    if bass:
        _bass_run(sc, t0, CHORUS_PROG, reps=bars // 4, vel=102 + vel_lift,
                  offs=_CHORUS_OFFS)
    if drums:
        _groove(sc, t0, bars, 0.85 + vel_lift / 200.0, ride=ride,
                china=china, crash_in=True)
    _brass_stabs(sc, t0, bars, CHORUS_PROG, vel=92 + vel_lift)
    _lead_hook(sc, t0, bars // 4, 96 + vel_lift, lyrics=lyrics)


def chorus1(sc) -> None:
    _chorus(sc, 96.0, 16, lyrics=True)


def solo1(sc) -> None:
    """SOLO I (16 bars) — call, antiphony, burst, summit.  Only the
    declared bass accompanist keeps a sparse pedal under the kit."""
    t0 = 160.0
    for off, p, dur in ((0.0, 38, 3.5), (8.0, 38, 3.0), (16.0, 38, 3.5),
                        (24.0, 45, 3.0), (32.0, 38, 3.5), (40.0, 38, 3.0),
                        (48.0, 38, 3.5), (56.0, 45, 3.0)):
        sc.note(BASS, p, t0 + off, dur, 70, jt=0 if off == 0.0 else 2, jv=3)

    # Phrase A (bars 1-4) — the call: hats state it, the ride answers.
    for bar in range(4):
        b = t0 + 4.0 * bar
        sc.hit(36, b, 112, jt=0 if bar == 0 else 2)
        sc.hit(36, b + 2.5, 100, jt=2)
        sc.hit(38, b + 1.0, 108, jt=2, jv=4)
        sc.hit(38, b + 3.0, 110, jt=2, jv=4)
        sc.hit(38, b + 1.75, 34, jt=3, jv=6)
        sc.hit(38, b + 3.25, 30, jt=3, jv=6)
        key = 42 if bar < 2 else 51
        for k in range(8):
            sc.hit(key, b + 0.5 * k, 80 if k % 2 == 0 else 58, jt=2, jv=5)
        if bar >= 2:
            sc.hit(53, b, 92, jt=2)
        if bar == 1:
            sc.hit(46, b + 3.5, 72, jt=2)
    sc.hit(55, t0 + 4.0, 96, jt=0)
    sc.hit(38, t0 + 7.75, 42, jt=0)          # drag into the ride answer
    sc.hit(38, t0 + 7.875, 52, jt=0)

    # Phrase B (bars 5-8) — across the stage: the antiphony figure (the
    # sentence SOLO II reprises), then high->floor tom circuits.
    _antiphony(sc, t0 + 16.0)
    for k in range(16):                       # quiet hat timekeeper
        sc.hit(42, t0 + 16.0 + 0.5 * k, 40 + (8 if k % 2 == 0 else 0),
               jt=2, jv=4)
    for off, v in ((1.0, 30), (3.0, 32), (5.0, 30), (7.0, 34)):
        sc.hit(38, t0 + 16.0 + off, v, jt=3, jv=5)
    for rep in range(4):                      # bars 7-8: two circuits/bar
        b = t0 + 24.0 + 2.0 * rep
        seq = _TOM_CIRCUIT if rep % 2 == 0 else list(reversed(_TOM_CIRCUIT))
        for k, key in enumerate(seq):
            sc.hit(key, b + 0.25 * k, int(en.lerp(72, 104, k / 5)), jt=2)
        sc.hit(36, b, 104, jt=2)
        sc.hit(38, b + 1.75, 98, jt=2)
    sc.hit(49, t0 + 24.0, 108, jt=0)
    sc.hit(52, t0 + 30.0, 106, jt=2)

    # Phrase C (bars 9-12) — the burst: 32nd rolls around the kit.
    b = t0 + 32.0                             # bar 9: snare -> toms, 32nds
    sc.hit(49, b, 112, jt=0)
    for k in range(8):
        sc.hit(38, b + 0.125 * k, int(en.lerp(52, 96, k / 7)), jt=1, jv=3)
    for i, key in enumerate((50, 47, 43)):
        for k in range(8):
            sc.hit(key, b + 1.0 + i + 0.125 * k,
                   int(en.lerp(66, 106, (i * 8 + k) / 23)), jt=1, jv=3)
    sc.hit(36, b, 110, jt=2)
    sc.hit(36, b + 2.0, 104, jt=2)
    b = t0 + 36.0                             # bar 10: punctuation groove
    sc.hit(52, b, 108, jt=2)
    for beat, v in ((0.0, 112), (1.5, 98), (2.5, 104)):
        sc.hit(36, b + beat, v, jt=2)
    sc.hit(38, b + 1.0, 106, jt=2)
    sc.hit(38, b + 3.0, 108, jt=2)
    for beat in (0.5, 1.5, 2.5, 3.5):
        sc.hit(51, b + beat, 68, jt=2, jv=4)
    sc.hit(41, b + 3.75, 84, jt=2)
    b = t0 + 40.0                             # bar 11: hat<->ride shimmer
    for k in range(32):
        key = 42 if k % 2 == 0 else 51
        sc.hit(key, b + 0.125 * k, 46 + int(30 * ((k % 8) / 7)), jt=1, jv=3)
    for beat in (0.0, 1.0, 2.0, 3.0):
        sc.hit(36, b + beat, 102, jt=2)
    sc.hit(38, b + 1.0, 96, jt=2)
    sc.hit(38, b + 3.0, 100, jt=2)
    b = t0 + 44.0                             # bar 12: the answer breath
    sc.hit(57, b, 110, jt=0)
    sc.hit(36, b, 108, jt=2)
    sc.hit(38, b + 0.75, 40, jt=1)
    sc.hit(38, b + 0.875, 50, jt=1)
    sc.hit(38, b + 1.0, 104, jt=2)
    sc.hit(36, b + 2.0, 100, jt=2)
    sc.hit(43, b + 2.5, 88, jt=2)
    sc.hit(43, b + 2.75, 92, jt=2)
    sc.hit(41, b + 3.0, 96, jt=2)
    sc.hit(41, b + 3.25, 100, jt=2)
    sc.hit(52, b + 3.5, 100, jt=2)

    # Phrase D (bars 13-16) — the summit: crash trades over a quarter kick.
    for bar in range(3):
        b = t0 + 48.0 + 4.0 * bar
        for k in range(4):
            sc.hit(36, b + k, 106, jt=2)
        sc.hit(38, b + 1.0, 112, jt=2)
        sc.hit(38, b + 3.0, 112, jt=2)
        sc.hit(38, b + 3.75, 60, jt=2)
        sc.hit(49 if bar % 2 == 0 else 57, b, 110, jt=0)
        sc.hit(52 if bar % 2 == 0 else 55, b + 2.0, 100, jt=2)
        for k in range(8):
            sc.hit(51 if k % 2 == 0 else 42, b + 0.5 * k,
                   74 if k % 2 == 0 else 58, jt=2, jv=4)
    b = t0 + 60.0                             # bar 16: the big fill
    fill = [50, 50, 48, 47, 45, 43, 41, 43, 45, 47, 48, 50]
    for k, key in enumerate(fill):
        sc.hit(key, b + 0.25 * k, int(en.lerp(76, 112, k / 11)), jt=1, jv=3)
    sc.hit(38, b + 2.875, 50, jt=0)
    sc.hit(38, b + 3.0, 114, jt=0)
    sc.hit(36, b + 3.5, 108, jt=0)
    sc.hit(52, b + 3.5, 112, jt=0)


def verse2(sc) -> None:
    t0 = 224.0
    _wah_pedal(sc, t0, 64.0, cpb=0.5, res=90)
    _wah_funk(sc, t0, 16, VERSE_PROG, vel=68)
    _piano_pump(sc, t0, 16, VERSE_PROG, vel=64)
    _bass_run(sc, t0, VERSE_PROG, reps=4, vel=94)
    _groove(sc, t0, 16, 0.55, crash_in=True)
    for i in range(8):                        # bars 9-16: chug build
        b = t0 + 32.0 + 4.0 * i
        r = _pv(VERSE_PROG[i % 4])
        for k in range(8):
            _power(sc, r, b + 0.5 * k, 0.32,
                   68 + (8 if k in (0, 5) else 0) - (6 if k % 2 else 0))


def chorus2(sc) -> None:
    _chorus(sc, 288.0, 16, ride=True, lyrics=True)
    _trumpet_calls(sc, 288.0, 4, vel=86)
    en.echo_throw(sc, LEAD, 348.0, base=0, peak=78, release=3.0)


def breakdown(sc) -> None:
    """The coil before SOLO II: soft piano arps, gliding bass, the lead
    climbing to a held A that dives a full octave (RPN range 12)."""
    t0 = 352.0
    en.soft_pedal(sc, PIANO, t0, t0 + 28.0)
    for i in range(8):
        b = t0 + 4.0 * i
        deg = BREAK_PROG[i % 4]
        tri = _triad(deg, octave=2)
        seq = [tri[0], tri[2], tri[1] + 12, tri[2], tri[0] + 12, tri[2],
               tri[1], tri[0]]
        for k, p in enumerate(seq):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 54, jt=0 if (i == 0 and k == 0) else 3, jv=4)
        sc.note(PIANO, _pv(deg, 1), b, 3.8, 50, jt=0 if i == 0 else 3, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    en.portamento_on(sc, BASS, t0 + 0.02, time_cc=58)
    for i in range(8):
        deg = BREAK_PROG[i % 4]
        sc.note(BASS, _pv(deg), t0 + 4.0 * i, 3.7, 64,
                jt=0 if i == 0 else 2, jv=3)
    en.portamento_off(sc, BASS, t0 + 30.5)
    _wah_pedal(sc, t0, 30.0, lo=32, hi=70, cpb=0.125, res=70)
    for i in range(7):
        b = t0 + 4.0 * i
        r = _pv(BREAK_PROG[i % 4], 1)
        for beat in (1.5, 3.5):
            sc.note(WAH, r, b + beat, 0.16, 46, jt=3, jv=4)
            sc.note(WAH, r + 5, b + beat, 0.16, 40, jt=3, jv=4)
    for i in range(7):                        # heartbeat kit
        b = t0 + 4.0 * i
        sc.hit(36, b, 76, jt=0 if i == 0 else 2)
        sc.hit(44, b + 1.0, 44, jt=2)
        sc.hit(37, b + 2.0, 52, jt=2)
        sc.hit(44, b + 3.0, 42, jt=2)
    for k in range(8):                        # bar 8: the snare announces
        sc.hit(38, t0 + 30.0 + 0.25 * k, int(en.lerp(36, 102, k / 7)),
               jt=1, jv=3)
    sc.hit(36, t0 + 30.0, 80, jt=2)
    # The lead: climb, hold, dive an octave on the widened bend range.
    en.bend_range(sc, LEAD, 12, t0 + 0.05)
    en.line(sc, LEAD, t0 + 16.0, D4, _MODE,
            [(1, 0.0, 0.5), (2, 0.5, 0.5), (3, 1.0, 0.5), (4, 1.5, 0.5),
             (5, 2.0, 1.5)], 78, jt=2, jv=2)
    sc.note(LEAD, _pv(5, 2), t0 + 20.0, 10.8, 96, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(t0 + 20.5, 0), (t0 + 24.0, 54),
                              (t0 + 26.0, 8)], step=0.2)
    en.bend_ramp(sc, LEAD, t0 + 26.0, t0 + 30.0, 0.0, -2.0, steps=24)
    sc.bend(LEAD, t0 + 31.2, 0.0)
    en.bend_range(sc, LEAD, 2, t0 + 31.6)


def solo2(sc) -> None:
    """SOLO II (8 bars) — the cymbal-antiphony reprise, foregrounded:
    the figure twice, a 32nd hat<->ride shimmer, climax trades, and the
    rising rooftop rush.  Pure drums."""
    t0 = 384.0
    _antiphony(sc, t0)                        # reprise statement 1
    _antiphony(sc, t0 + 8.0, vel_off=6)       # reprise statement 2
    for k in range(32):                       # hat timekeeper, bars 1-4
        sc.hit(42, t0 + 0.5 * k, 38 + (8 if k % 2 == 0 else 0), jt=2, jv=4)
    for off, v in ((1.0, 28), (3.0, 30), (9.0, 30), (11.0, 32)):
        sc.hit(38, t0 + off, v, jt=3, jv=5)
    for k, key in enumerate((41, 43, 41, 43)):   # floor pickup between
        sc.hit(key, t0 + 7.0 + 0.25 * k, 70 + 6 * k, jt=1)
    for k, key in enumerate((47, 48, 50, 55)):   # rising answer, bar 4
        sc.hit(key, t0 + 15.0 + 0.25 * k, 78 + 8 * k, jt=1)

    for half in range(2):                     # bars 5-6: 32nd shimmer
        b = t0 + 16.0 + 4.0 * half
        sc.hit(49 if half == 0 else 52, b, 112, jt=0)
        for k in range(32):
            key = 42 if k % 2 == 0 else 51
            sc.hit(key, b + 0.125 * k, 44 + int(32 * ((k % 8) / 7)),
                   jt=1, jv=3)
        for beat in (0.0, 1.0, 2.0, 3.0):
            sc.hit(36, b + beat, 104, jt=2)
        sc.hit(38, b + 1.0, 100, jt=2)
        sc.hit(38, b + 3.0, 102, jt=2)

    for i, key in enumerate((52, 49, 57, 55)):   # bars 7-8: climax trades
        b = t0 + 24.0 + 2.0 * i
        sc.hit(key, b, 114, jt=0)
        sc.hit(36, b, 108, jt=2)
        sc.hit(36, b + 1.0, 96, jt=2)
        sc.hit(38, b + 1.5, 104, jt=2)
    sc.hit(38, t0 + 29.75, 44, jt=0)          # ruff...
    sc.hit(38, t0 + 29.875, 54, jt=0)
    for k, key in enumerate((41, 43, 45, 47, 48, 50)):   # ...rooftop rush
        sc.hit(key, t0 + 30.0 + 0.25 * k, int(en.lerp(78, 112, k / 5)),
               jt=1)
    sc.hit(55, t0 + 31.5, 106, jt=0)
    sc.hit(38, t0 + 31.75, 116, jt=0)


def final_chorus(sc) -> None:
    t0 = 416.0
    _chorus(sc, t0, 16, vel_lift=8, ride=True, china=True, lyrics=True,
            bass=False)
    _chorus(sc, t0 + 64.0, 16, vel_lift=12, ride=True, china=True,
            bass=False)
    _trumpet_calls(sc, t0, 2, vel=86)
    _trumpet_calls(sc, t0 + 32.0, 2, vel=88)
    _trumpet_calls(sc, t0 + 64.0, 4, vel=92, full=True)
    # Bass: the runner for 12 bars, then the 4-bar countermelody break —
    # the declared BASS_SPEC hook — in each half.
    for half in (0.0, 64.0):
        _bass_run(sc, t0 + half, CHORUS_PROG, reps=3, vel=104 + int(half // 16),
                  offs=_CHORUS_OFFS)
        hb = t0 + half + 48.0
        for bar, degs in enumerate(((1, 2, 3, 4, 5, 6, 7, 8),
                                    (8, 8, 7, 6, 5, 4, 3, 2),
                                    (1, 3, 5, 8, 10, 8, 5, 3),
                                    (5, 6, 7, 8, 7, 6, 5, 2))):
            b = hb + 4.0 * bar
            for k, deg in enumerate(degs):
                sc.note(BASS, _pv(deg), b + 0.5 * k, 0.45,
                        100 + (6 if k in (0, 4) else 0), jt=2, jv=3)


def outro(sc) -> None:
    t0 = 544.0
    _riff_x(sc, t0, 4, vel_scale=0.9)
    _groove(sc, t0, 8, 0.55, fills=False)
    _bass_run(sc, t0, VERSE_PROG, reps=2, vel=88)
    _wah_pedal(sc, t0, 32.0, cpb=0.5, res=80)
    for i in range(8):
        b = t0 + 4.0 * i
        r = _pv(VERSE_PROG[i % 4], 1)
        for beat in (1.5, 3.5):
            sc.note(WAH, r, b + beat, 0.16, int(en.lerp(52, 36, i / 7)),
                    jt=3, jv=4)
    en.echo_throw(sc, WAH, t0 + 30.0, base=0, peak=76, release=3.0)
    # The chase rolls off the last roof: held D, fading echoes.
    b = t0 + 32.0
    _power(sc, D3, b, 3.8, 92)
    sc.note(BASS, D2, b, 3.8, 88, jt=0, jv=0)
    sc.hit(49, b, 108, jt=0)
    sc.hit(36, b, 104, jt=0)
    sc.note(PIANO, D4 + 12, b, 1.5, 60, jt=0, jv=3)
    sc.note(PIANO, _pv(5, 2) + 12, b + 2.0, 1.5, 54, jt=3, jv=3)
    en.sustain(sc, PIANO, b + 0.02, b + 7.9)
    _power(sc, D3, b + 4.0, 3.8, 84)
    sc.note(BASS, D2, b + 4.0, 3.8, 82, jt=2, jv=3)
    sc.hit(36, b + 4.0, 92, jt=2)
    sc.note(PIANO, D4 + 12, b + 4.0, 1.5, 50, jt=3, jv=3)
    sc.note(PIANO, _pv(3, 2) + 12, b + 6.0, 1.5, 46, jt=3, jv=3)
    _power(sc, D3, b + 8.0, 6.0, 88)
    sc.note(BASS, D2, b + 8.0, 6.0, 84, jt=0, jv=0)
    sc.hit(49, b + 8.0, 100, jt=0)
    sc.hit(36, b + 8.0, 98, jt=0)
    sc.note(PIANO, D4 + 12, b + 8.0, 4.0, 56, jt=0, jv=3)
    sc.note(PIANO, D4 + 24, b + 8.0, 4.0, 48, jt=0, jv=3)
    en.sustain(sc, PIANO, b + 8.02, b + 13.9)
    en.cc_curve(sc, DRIVE, 11, [(b + 8.0, 110), (b + 14.0, 30)], step=0.5)
    sc.hit(52, b + 12.0, 56, jt=0)
    en.echo_throw(sc, DRIVE, b + 8.5, base=0, peak=80, release=4.0)


BUILDERS = [riff_intro, verse1, chorus1, solo1, verse2, chorus2, breakdown,
            solo2, final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 26, 29, 30, 33, 57, 61, 84}
CENTERED_CHANNELS = {PIANO, BASS, LEAD, DRUMS, BRASS, TRUMPET}
NOTE_RANGES = {
    PIANO: (48, 94), WAH: (46, 76), DRIVE: (36, 74), BASS: (36, 60),
    LEAD: (58, 80), BRASS: (46, 66), TRUMPET: (78, 88),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (259.0, 280.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "verse2", 1.15),
    ("breakdown", "<=", "chorus2", 0.7),
    ("final_chorus", ">=", "chorus1", 1.0),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("riff", "<=", "chorus1", 1.0),
    ("verse1", "<=", "chorus2", 1.0),
    ("outro", "<=", "final_chorus", 0.85),
]
LATE_CHANNELS = {BRASS: 96.0, TRUMPET: 288.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 2), ("chorus1", 2), ("verse2", 2),
                 ("chorus2", 2), ("final_chorus", 2)],
    "hook": "final_chorus",
}
# CHOIR_SPEC deliberately omitted — riff-rock track, no choir (HLD D3).
DRUM_SOLO_SPEC = {
    "windows": [(160.0, 224.0), (384.0, 416.0)],
    "accompanists": {BASS},
}
FEATURES_EXPECTED = {
    "bend_range", "pitch_bend", "cc1_vibrato", "cc74_wah",
    "cc64_sustain", "cc67_soft", "cc11_expression", "cc2_breath",
    "aftertouch", "portamento", "cc94_echo", "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def _grouped_roots(sc, ch, t0, t1):
    """Chord-hit root sequence: min pitch per 0.25-beat onset group."""
    groups: dict[float, int] = {}
    for on, _off, p, _v in _spans(sc, ch):
        if t0 - 1e-9 <= on < t1:
            key = round(on * 4) / 4
            groups[key] = min(groups.get(key, 127), p)
    return [groups[k] for k in sorted(groups)]


def oracles(sc, info, spans):
    # 1. riff_recurrence — the intro riff IS the chorus engine: the same
    # chord-hit root sequence opens every chorus (both halves of the
    # double final chorus), pinned by jt=0.
    fails_riff: list[str] = []
    ref = _grouped_roots(sc, DRIVE, 0.0, 8.0)
    if not ref:
        fails_riff.append("intro riff is empty")
    for name, s0 in (("chorus1", 96.0), ("chorus2", 288.0),
                     ("final_chorus", 416.0),
                     ("final_chorus second half", 480.0)):
        got = _grouped_roots(sc, DRIVE, s0, s0 + 8.0)
        if got != ref:
            fails_riff.append(
                f"riff at {name} (beat {s0:.0f}) differs from the intro "
                f"riff ({len(got)} vs {len(ref)} chord-hits)")

    # 2. antiphony_reprise — SOLO II reprises SOLO I's cymbal-antiphony
    # figure.  Recomputed from _ANTIPHONY (not copied): every stroke of
    # the figure must land at its exact tick at the SOLO I statement and
    # at BOTH SOLO II statements.
    fails_ant: list[str] = []
    actual = {(round(on * en.PPQ), p)
              for on, _off, p, _v in _spans(sc, DRUMS)}
    for where, anchor in (("SOLO I", 176.0), ("SOLO II a", 384.0),
                          ("SOLO II b", 392.0)):
        missing = [(off, key) for off, key, _v in _ANTIPHONY
                   if (round((anchor + off) * en.PPQ), key) not in actual]
        if missing:
            fails_ant.append(f"{where} (beat {anchor:.0f}): figure "
                             f"incomplete, missing {missing[:3]}")

    # 3. solo_build — each solo builds: its second half carries >= 1.15x
    # the hits of its first half (intensity rises, not white noise).
    fails_arc: list[str] = []
    ons = [on for on, _off, _p, _v in _spans(sc, DRUMS)]
    for t0, t1 in DRUM_SOLO_SPEC["windows"]:
        mid = (t0 + t1) / 2
        a = sum(1 for on in ons if t0 - 1e-9 <= on < mid)
        b = sum(1 for on in ons if mid <= on < t1 - 1e-9)
        if b < 1.15 * a:
            fails_arc.append(f"solo [{t0:.0f},{t1:.0f}): second half has "
                             f"{b} hits, < 1.15 x first half ({a})")

    return [("riff_recurrence", fails_riff),
            ("antiphony_reprise", fails_ant),
            ("solo_build", fails_arc)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# PROVISIONAL thresholds — measured 2026.07.11 on this worktree's
# per-track render (ferrosintesis 0.13.x); re-pinned at phase D on the
# assembled-album render.  Measured: chorus lift 2.32 dB (pin - 1 dB);
# solo side/mid 0.118 / 0.174 (pin = weaker window - 25%).
_LIFT_DB = 1.3        # PROVISIONAL: final chorus over verse 1
_SPREAD_MIN = 0.088   # PROVISIONAL: solo-window side/mid |L-R| ratio


def audio_checks(ctx):
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(40.0, 88.0)
    f0, f1 = ctx.bar_window(432.0, 496.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # Drum-solo stereo spread: within-window side/mid ratio (HLD §6.2 —
    # no cross-section baseline; the mono-fed drum room dilutes side
    # energy, so the floor is measured, then pinned with margin).
    fails_spread: list[str] = []
    for b0, b1 in DRUM_SOLO_SPEC["windows"]:
        i0, i1 = ctx.bar_window(b0, b1)
        acc_s = acc_m = 0.0
        for a, b in zip(ctx.l[i0:i1], ctx.r[i0:i1]):
            acc_s += (a - b) * (a - b)
            acc_m += (a + b) * (a + b)
        ratio = (acc_s / acc_m) ** 0.5 if acc_m > 0 else 0.0
        if ratio < _SPREAD_MIN:
            fails_spread.append(f"solo [{b0:.0f},{b1:.0f}): side/mid "
                                f"{ratio:.3f} < {_SPREAD_MIN}")

    return [("chorus_lift", fails_lift),
            ("drum_solo_spread", fails_spread)]
