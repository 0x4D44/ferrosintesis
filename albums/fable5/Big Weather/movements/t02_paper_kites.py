"""t02_paper_kites.py — "Paper Kites" (Big Weather, track 2).

Jangle-pop in A major at 118 BPM.  A picked add9 eighth-note arpeggio
(the "jangle engine", GM26) and piano carry the verses over a singing
diatonic bass walk; the layered choir arrives at the pre-chorus and
swells through a CC70 oo->ah vowel morph (the track's signature move,
oracle-pinned and audio-probed); the chorus HOOK is sung by a
portamento synth lead (GM80, CC5/65 glide + CC68 slurs, oracle-pinned
to recur identically in all three choruses) over a melodic bass
countermelody; strings gate in at the middle-8 (LATE_CHANNELS); the
chime guitar lifts to overdrive (GM29) for the final chorus only, then
the jangle returns to close the frame.

Form (HLD 4, full grammar):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 | middle8 |
  final_chorus (+tag) | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 2
TITLE = "Paper Kites"
FILE = "02 - Paper Kites.mid"
SEED = 20260702

BPM = 118.0

# Channels (HLD 3; no brass/timpani on this track — kept jangle-light).
PIANO, GTR_L, GTR_R, BASS = 0, 1, 2, 3
AAH, OOH, LEAD, KEYS = 4, 5, 6, 7
STRINGS, DRUMS = 8, 9

_SECTIONS = [
    ("intro",          0.0,  32.0),
    ("verse1",        32.0,  96.0),
    ("pre1",          96.0, 128.0),
    ("chorus1",      128.0, 176.0),
    ("verse2",       176.0, 208.0),
    ("pre2",         208.0, 240.0),
    ("chorus2",      240.0, 288.0),
    ("middle8",      288.0, 320.0),
    ("final_chorus", 320.0, 400.0),
    ("outro",        400.0, 432.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 3, 0)],                       # A major, three sharps
    channels=[
        (PIANO,   "piano",         0, 100, 64, 50),
        (GTR_L,   "jangle guitar", 26,  96, 48, 42),
        (GTR_R,   "chime guitar",  25,  92, 80, 42),
        (BASS,    "bass guitar",   33, 105, 64, 25),
        (AAH,     "choir aah",     52,  88, 64, 70),
        (OOH,     "choir ooh",     53,  84, 64, 70),
        (LEAD,    "glide lead",    80,  90, 64, 48),
        (KEYS,    "ep pad",         4,  82, 64, 45),
        (STRINGS, "strings",       48,  86, 64, 65),
        (DRUMS,   "drums",          0, 108, 64, 45),
    ],
    program_changes=[
        (GTR_R, 320.0, 29),      # chime -> overdrive: the final-chorus lift
        (GTR_R, 400.0, 25),      # and back to chimes for the outro frame
    ],
)

# ---------------------------------------------------------------------------
# Harmony — A major.  Degrees against an A tonic (ionian).
# ---------------------------------------------------------------------------

A2, A3, A4 = en.n("A2"), en.n("A3"), en.n("A4")
_MODE = "ionian"

INTRO_PROG = [1, 4, 1, 5]            # A   D    A    E
VERSE_PROG = [1, 4, 6, 5]            # A   D    F#m  E
PRE_PROG = [6, 4, 2, 5]              # F#m D    Bm   E
CHORUS_PROG = [4, 1, 5, 6]           # D   A    E    F#m
MID_PROG = [6, 5, 4, 1, 6, 5, 2, 5]  # F#m E D A | F#m E Bm E
TAG_PROG = [4, 5, 1, 1]              # D   E    A    A
OUTRO_PROG = [1, 4, 6, 5, 1, 4]


def _root(deg: int, octave: int = 0) -> int:
    return en.pitch(A2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(A2, _MODE, deg)]


# The chorus HOOK — (degree rel A4, start, dur) over 16 beats
# (D A E F#m), sung by the glide lead with portamento swoops; jt=0
# throughout so the recurrence oracle (kite_hook) can pin it exactly.
_HOOK = [
    (4, 0.0, 0.5), (5, 0.5, 0.5), (6, 1.0, 1.5), (8, 2.5, 1.5),
    (7, 4.0, 0.5), (8, 4.5, 0.5), (9, 5.0, 1.5), (8, 6.5, 0.5),
    (7, 7.0, 1.0),
    (7, 8.0, 0.75), (5, 8.75, 0.75), (4, 9.5, 0.5), (5, 10.0, 2.0),
    (6, 12.0, 1.0), (5, 13.0, 0.5), (4, 13.5, 0.5), (3, 14.0, 1.75),
]

_HOOK_LYRICS = ["paper kites", "catch the wind", "over rooftops",
                "let them go"]

# The chorus bass countermelody — (beat, pitch, dur, vel delta) over 16
# beats: a singing, mostly stepwise line that mirrors the hook's arc
# (BASS_SPEC hook; >= 6 distinct pitches spanning >= 7 semitones).
_CHORUS_BASS = [
    (0.0, 50, 0.70, 0), (0.75, 50, 0.20, -22), (1.0, 52, 0.45, -8),
    (1.5, 54, 0.45, -8), (2.0, 57, 0.95, -2), (3.0, 54, 0.45, -8),
    (3.5, 52, 0.45, -6),
    (4.0, 45, 0.70, 0), (4.75, 45, 0.20, -22), (5.0, 49, 0.45, -8),
    (5.5, 50, 0.45, -8), (6.0, 52, 0.95, -2), (7.0, 50, 0.45, -8),
    (7.5, 49, 0.45, -6),
    (8.0, 52, 0.70, 0), (8.75, 52, 0.20, -22), (9.0, 54, 0.45, -8),
    (9.5, 56, 0.45, -8), (10.0, 59, 0.95, -2), (11.0, 56, 0.45, -8),
    (11.5, 54, 0.45, -6),
    (12.0, 54, 0.70, 0), (12.75, 54, 0.20, -22), (13.0, 52, 0.45, -8),
    (13.5, 50, 0.45, -8), (14.0, 49, 0.70, -2), (14.75, 47, 0.45, -8),
    (15.5, 49, 0.45, -6),
]

# Choir counter-lines — (degree rel A3, start, dur); all jt=0 holds.
_PRE_OOH = [(3, 0.0, 3.9), (4, 4.0, 3.9), (6, 8.0, 3.9), (8, 12.0, 3.9),
            (5, 16.0, 3.9), (6, 20.0, 3.9), (8, 24.0, 3.9), (9, 28.0, 3.5)]
_CHORUS_OOH = [(6, 0.0, 3.9), (5, 4.0, 3.9), (7, 8.0, 3.9), (6, 12.0, 3.9)]
_MID_OOH = [(3, 0.0, 7.5), (1, 8.0, 7.5), (2, 16.0, 7.5), (2, 24.0, 7.0)]

_JANGLE_PATTERN = [0, 4, 7, 8, 9, 8, 7, 4]        # add9 up-down (degrees)
_SHIMMER_PATTERN = [7, 9, 8, 9, 11, 9, 8, 9]      # octave-region sparkle


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _jangle(sc, ch, t0: float, bars: int, prog: list[int], vel: int) -> None:
    """The jangle engine: picked add9 eighth-note arpeggios, 8 notes/bar
    (oracle: jangle_engine)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        for k, off in enumerate(_JANGLE_PATTERN):
            jt = 0 if (i == 0 and k == 0) else 3
            sc.note(ch, en.pitch(A3, _MODE, d + off), b + 0.5 * k, 0.42,
                    vel + (4 if k == 0 else 0), jt=jt, jv=4)


def _chimes(sc, t0: float, bars: int, prog: list[int], vel: int, *,
            boundary: bool = False) -> None:
    """High ringing root+fifth dyads on the chime guitar."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = en.pitch(A4, _MODE, prog[i % len(prog)])
        if boundary and i == 0:
            sc.note(GTR_R, r, b, 3.7, vel, jt=0, jv=3)
            sc.note(GTR_R, r + 7, b + 0.04, 3.66, vel - 2, jt=0, jv=3)
        else:
            en.strum(sc, GTR_R, [r, r + 7], b, 3.7, vel, spread=0.04)


def _shimmer(sc, t0: float, bars: int, prog: list[int], vel: int) -> None:
    """Chime guitar: octave-region add9 eighths — 12-string sparkle."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        for k, off in enumerate(_SHIMMER_PATTERN):
            jt = 0 if (i == 0 and k == 0) else 3
            sc.note(GTR_R, en.pitch(A3, _MODE, d + off), b + 0.5 * k, 0.40,
                    vel - (0 if k % 2 == 0 else 8), jt=jt, jv=4)


def _strums(sc, t0: float, bars: int, prog: list[int], vel: int) -> None:
    """Jangle guitar: open eighth strums, down-up."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        chord = tri + [tri[0] + 12]
        for k in range(8):
            down = k % 2 == 0
            v = vel - (0 if down else 12)
            if i == 0 and k == 0:
                for j, p in enumerate(chord):
                    sc.note(GTR_L, p, b, 0.46, v - j, jt=0, jv=3)
            else:
                en.strum(sc, GTR_L, chord, b + 0.5 * k, 0.46, v,
                         spread=0.02, down=down)


def _power(sc, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    for i, off in enumerate((0, 7, 12)):
        sc.note(GTR_R, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _power_bed(sc, t0: float, bars: int, prog: list[int], vel: int,
               push: bool = True) -> None:
    """Overdrive guitar: sustained power chords with an eighth push."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        _power(sc, r, b, 2.4, vel, jt=0 if i == 0 else 2)
        if push:
            _power(sc, r, b + 2.5, 0.45, vel - 10, jt=2)
            _power(sc, r, b + 3.5, 0.45, vel - 6, jt=2)


def _comp(sc, t0: float, bars: int, prog: list[int], vel: int) -> None:
    """Verse piano: LH root-fifth halves, RH off-beat add9 colours."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        r = _root(d, octave=1)
        tri = _triad(d, octave=2)
        nine = en.pitch(A2, _MODE, d + 8) + 12
        sc.note(PIANO, r, b, 1.9, vel + 6, jt=0 if i == 0 else 3, jv=4)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, vel + 2, jt=3, jv=4)
        sc.note(PIANO, tri[0], b + 1.5, 0.9, vel - 6, jt=3, jv=4)
        sc.note(PIANO, tri[1], b + 1.5, 0.9, vel - 8, jt=3, jv=4)
        sc.note(PIANO, tri[1], b + 3.0, 0.9, vel - 6, jt=3, jv=4)
        sc.note(PIANO, tri[2], b + 3.0, 0.9, vel - 8, jt=3, jv=4)
        sc.note(PIANO, nine, b + 3.5, 0.45, vel - 10, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _anthem(sc, t0: float, bars: int, prog: list[int], vel: int) -> None:
    """Chorus piano: driving block chords with an octave crown."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        r = _root(d, octave=1)
        tri = _triad(d, octave=2)
        for beat, dur in ((0.0, 1.9), (2.0, 0.9), (3.0, 0.9)):
            jt = 0 if (i == 0 and beat == 0.0) else 3
            sc.note(PIANO, r, b + beat, dur, vel, jt=jt, jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 5, jt=jt, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.5, 0.45, vel + 2, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _bass_walk(sc, t0: float, prog: list[int], reps: int = 1,
               vel: int = 94) -> None:
    """Verse bass: a diatonic singing walk — root, 2nd, 3rd, 5th, 4th,
    3rd, then a stepwise approach into the next root."""
    seq = prog * reps
    for i, d in enumerate(seq):
        b = t0 + 4.0 * i
        r = _root(d)
        nxt = _root(seq[(i + 1) % len(seq)])
        appr = nxt - 1 if nxt > r else nxt + 2
        sc.note(BASS, r, b, 0.95, vel, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 1), b + 1.0, 0.45, vel - 8,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 2), b + 1.5, 0.45, vel - 10,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 4), b + 2.0, 0.70, vel - 4,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 3), b + 2.75, 0.20, vel - 20,
                jt=3, jv=4)
        sc.note(BASS, en.pitch(A2, _MODE, d + 2), b + 3.0, 0.45, vel - 8,
                jt=2, jv=3)
        sc.note(BASS, appr, b + 3.5, 0.45, vel - 6, jt=2, jv=3)


def _bass_chorus(sc, t0: float, statements: int, vel: int) -> None:
    for s in range(statements):
        base = t0 + 16.0 * s
        for k, (beat, p, dur, dv) in enumerate(_CHORUS_BASS):
            jt = 0 if (s == 0 and k == 0) else 2
            sc.note(BASS, p, base + beat, dur, vel + dv, jt=jt, jv=3)


def _bass_pre(sc, t0: float, vel: int) -> None:
    """Pre-chorus build: half one walks quarters, half two drives
    eighths into a scalar launch run under the choir swell."""
    for i, d in enumerate(PRE_PROG):                     # bars 1-4
        b = t0 + 4.0 * i
        sc.note(BASS, _root(d), b, 0.95, vel, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 4), b + 1.0, 0.95, vel - 8,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 2), b + 2.0, 0.95, vel - 6,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 1), b + 3.0, 0.95, vel - 4,
                jt=2, jv=3)
    for i, d in enumerate(PRE_PROG[:3]):                 # bars 5-7
        b = t0 + 16.0 + 4.0 * i
        r = _root(d)
        for k in range(8):
            v = int(en.lerp(vel - 6, vel + 6, (i * 8 + k) / 23))
            p = r if k % 4 != 3 else en.pitch(A2, _MODE, d + 1)
            sc.note(BASS, p, b + 0.5 * k, 0.42, v, jt=2, jv=3)
    b = t0 + 28.0                                        # bar 8: the launch
    for k in range(8):
        sc.note(BASS, en.pitch(A2, _MODE, 1 + k), b + 0.5 * k, 0.44,
                int(en.lerp(vel - 2, vel + 10, k / 7)), jt=2, jv=3)


def _bass_mid(sc, t0: float) -> None:
    """Middle-8 bass: long low roots (floor C2) with stepwise approaches."""
    def low(deg: int) -> int:
        r = _root(deg) - 12
        return r if r >= 36 else r + 12
    for i, d in enumerate(MID_PROG):
        b = t0 + 4.0 * i
        r = low(d)
        nxt = low(MID_PROG[(i + 1) % len(MID_PROG)])
        appr = nxt - 1 if nxt > r else nxt + 2
        sc.note(BASS, r, b, 3.4, 76, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, appr, b + 3.5, 0.45, 62, jt=2, jv=3)


def _bass_outro(sc, t0: float) -> None:
    for i, d in enumerate(OUTRO_PROG):
        b = t0 + 4.0 * i
        v = int(en.lerp(84, 68, i / 5))
        sc.note(BASS, _root(d), b, 1.9, v, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 4), b + 2.0, 0.95, v - 8,
                jt=2, jv=3)
        sc.note(BASS, en.pitch(A2, _MODE, d + 2), b + 3.0, 0.95, v - 10,
                jt=2, jv=3)


def _choir_pads(sc, t0: float, prog: list[int], bars: int, vel: int,
                vel_end: int | None = None) -> None:
    chords = [en.triad(A3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=55, hi=77,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _ooh_line(sc, t0: float, notes, vel: int) -> None:
    """Held counter-line on the ooh choir; jt=0 (boundary-safe holds)."""
    for deg, start, dur in notes:
        sc.note(OOH, en.pitch(A3, _MODE, deg), t0 + start, dur, vel,
                jt=0, jv=3)


def _ep_pads(sc, t0: float, prog: list[int], bars: int, vel: int) -> None:
    chords = [en.triad(A3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=vel, legato=0.0)


def _strings_pad(sc, t0: float, prog: list[int], bars: int, vel: int,
                 swell: list[tuple[float, int]]) -> None:
    chords = [en.triad(A3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=50, hi=79,
                 vel=vel, legato=0.0)
    en.expr_curve(sc, STRINGS, swell, step=1.0)


def _drums(sc, t0: float, bars: int, intensity: float, *,
           sidestick: bool = False, crash_in: bool = False,
           tamb: bool = False, fills: bool = True,
           fourfloor: bool = False) -> None:
    """The kit groove.  intensity 0..1 scales velocity and busy-ness."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(68, 104, intensity)))
        fill_bar = fills and (i == bars - 1 or i % 8 == 7)
        if crash_in and i == 0:
            sc.hit(49, b, min(120, v + 14), jt=0)
        sc.hit(36, b, v + 8, jt=0 if i == 0 else 2)
        if fourfloor:
            for q in (1.0, 2.0, 3.0):
                sc.hit(36, b + q, v + 4, jt=2)
        else:
            sc.hit(36, b + 2.5, v + 2, jt=2)
            if intensity > 0.75 and i % 2 == 1:
                sc.hit(36, b + 3.75, v - 6, jt=2)
        key = 37 if sidestick else 38
        sc.hit(key, b + 1.0, v + (4 if sidestick else 10), jt=2, jv=4)
        sc.hit(key, b + 3.0, v + (4 if sidestick else 10), jt=2, jv=4)
        if not sidestick and intensity < 0.8:
            sc.hit(38, b + 1.75, max(18, v - 48), jt=3, jv=6)   # ghost
        for k in range(8):
            if fill_bar and k >= 5:
                continue
            sc.hit(42, b + 0.5 * k, max(20, v - (12 if k % 2 == 0 else 26)),
                   jt=2, jv=5)
        if not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 20, jt=2)                   # open lift
        if tamb:
            for k in range(8):
                sc.hit(54, b + 0.5 * k,
                       max(18, v - 34 + (8 if k % 2 == 0 else 0)),
                       jt=3, jv=5)
        if fill_bar:
            for k, key2 in enumerate((41, 43, 45, 47, 48, 50)):
                sc.hit(key2, b + 2.5 + 0.25 * k,
                       int(en.lerp(v - 20, v + 12, k / 5)), jt=2)


def _snare_build(sc, b: float) -> None:
    """The pre-chorus launch bar: 16th snare crescendo over quarter kicks."""
    for q in range(4):
        sc.hit(36, b + q, 96, jt=2)
    for k in range(16):
        sc.hit(38, b + 0.25 * k, int(en.lerp(46, 114, k / 15)), jt=2, jv=4)
    sc.hit(46, b + 3.5, 78, jt=2)


def _lead_hook(sc, t0: float, statements: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The chorus hook on the glide lead: CC68 slurs, CC1 blooms on the
    long notes; jt=0/jv=0 so every statement is oracle-identical."""
    sc.cc(LEAD, 68, 127, t0 - 0.05)
    for s in range(statements):
        base = t0 + 16.0 * s
        v = vel + (3 if s == statements - 1 else 0)
        en.line(sc, LEAD, base, A4, _MODE, _HOOK, v, jt=0, jv=0, gate=1.03)
        for deg, start, dur in _HOOK:
            if dur >= 1.5:
                bb = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(bb + 0.25, 0), (bb + dur * 0.7, 55),
                             (bb + dur, 10)], step=0.15)
    sc.cc(LEAD, 68, 0, t0 + 16.0 * statements - 0.25)
    if lyrics:
        for k, text in enumerate(_HOOK_LYRICS):
            en.lyric(sc, t0 + 4.0 * k, text)


def _chorus(sc, t0: float, statements: int, *, vel_lift: int = 0,
            ep: bool = False, power: bool = False, lyrics: bool = False,
            intensity: float = 0.8, porta_off: bool = True) -> None:
    bars = statements * 4
    _anthem(sc, t0, bars, CHORUS_PROG, vel=84 + vel_lift)
    _strums(sc, t0, bars, CHORUS_PROG, vel=74 + vel_lift)
    if power:
        _power_bed(sc, t0, bars, CHORUS_PROG, vel=98 + vel_lift)
    else:
        _shimmer(sc, t0, bars, CHORUS_PROG, vel=56 + vel_lift)
    _bass_chorus(sc, t0, statements, vel=100 + vel_lift)
    _drums(sc, t0, bars, intensity, crash_in=True, tamb=True)
    _choir_pads(sc, t0, CHORUS_PROG, bars, vel=54 + vel_lift)
    for s in range(statements):
        _ooh_line(sc, t0 + 16.0 * s, _CHORUS_OOH, vel=50 + vel_lift)
    if ep:
        _ep_pads(sc, t0, CHORUS_PROG, bars, vel=46 + vel_lift)
    en.portamento_on(sc, LEAD, t0 - 0.1, time_cc=52)
    _lead_hook(sc, t0, statements, vel=94 + vel_lift, lyrics=lyrics)
    if porta_off:
        en.portamento_off(sc, LEAD, t0 + 16.0 * statements - 0.25)


def _pre(sc, t0: float, hot: int, ep: bool = False) -> None:
    """The pre-chorus: choir arrives and SWELLS (CC70 oo->ah morph, the
    signature move) while the band builds under it."""
    _anthem(sc, t0, 4, PRE_PROG, vel=74 + hot)
    _anthem(sc, t0 + 16.0, 4, PRE_PROG, vel=80 + hot)
    _strums(sc, t0, 4, PRE_PROG, vel=62 + hot)
    _strums(sc, t0 + 16.0, 4, PRE_PROG, vel=72 + hot)
    _shimmer(sc, t0 + 16.0, 4, PRE_PROG, vel=52 + hot)
    _bass_pre(sc, t0, vel=98 + hot)
    _drums(sc, t0, 4, 0.55, fills=False)
    _drums(sc, t0 + 16.0, 3, 0.72, fourfloor=True, fills=False)
    _snare_build(sc, t0 + 28.0)
    _choir_pads(sc, t0, PRE_PROG, 8, vel=44 + hot, vel_end=74 + hot)
    _ooh_line(sc, t0, _PRE_OOH, vel=46 + hot)
    en.vowel_curve(sc, AAH, [(t0, 32), (t0 + 16.0, 58), (t0 + 28.0, 88),
                             (t0 + 31.5, 103)], step=1.0)
    en.vowel_curve(sc, OOH, [(t0, 36), (t0 + 31.5, 98)], step=2.0)
    if ep:
        _ep_pads(sc, t0 + 16.0, PRE_PROG, 4, vel=44)


def _mid_lead(sc, t0: float) -> None:
    """Middle-8 drift phrases: long portamento glides — kites on the wind."""
    en.portamento_on(sc, LEAD, t0 + 15.8, time_cc=70)
    en.line(sc, LEAD, t0, A4, _MODE,
            [(3, 16.0, 3.5), (2, 20.0, 3.5), (4, 24.0, 1.5),
             (2, 25.5, 5.8)], 66, jt=0, jv=0, gate=1.0)
    en.vibrato(sc, LEAD, t0 + 27.0, 4.0, depth=0.22, cycles_per_beat=1.0)
    en.portamento_off(sc, LEAD, t0 + 31.6)


def _tag_lead(sc, t0: float) -> None:
    """The tag: an F#5-G#5 rise onto a held A5 with vibrato and an echo."""
    en.line(sc, LEAD, t0, A4, _MODE,
            [(6, 0.0, 1.9), (7, 2.0, 1.9), (8, 4.0, 9.5)], 100, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(t0 + 4.5, 0), (t0 + 9.0, 62),
                              (t0 + 13.0, 18)], step=0.2)
    en.vibrato(sc, LEAD, t0 + 6.0, 7.0, depth=0.24, cycles_per_beat=1.1)
    en.echo_throw(sc, LEAD, t0 + 11.0, base=0, peak=84, release=3.0)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    _jangle(sc, GTR_L, 0.0, 8, INTRO_PROG, vel=58)
    en.soft_pedal(sc, PIANO, 0.0, 30.0)              # una corda wash
    for i, d in enumerate(INTRO_PROG):
        b = 8.0 * i
        chord = [_root(d, octave=1)] + _triad(d, octave=2)
        for j, p in enumerate(chord):
            off = 0.0 if i == 0 else 0.05 * j
            sc.note(PIANO, p, b + off, 7.5 - off, 52 - 2 * j,
                    jt=0 if i == 0 else 3, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 7.9)
    _chimes(sc, 16.0, 4, INTRO_PROG, vel=44)
    _bass_walk(sc, 16.0, INTRO_PROG, vel=86)
    _drums(sc, 16.0, 4, 0.35, sidestick=True, fills=False)
    en.echo_throw(sc, GTR_L, 28.0, base=0, peak=72, release=2.5)
    for k, key in enumerate((41, 43, 45, 47)):       # pickup into verse 1
        sc.hit(key, 30.0 + 0.5 * k, int(en.lerp(60, 88, k / 3)), jt=2)


def verse1(sc) -> None:
    t0 = 32.0
    _comp(sc, t0, 16, VERSE_PROG, vel=66)
    _jangle(sc, GTR_L, t0, 16, VERSE_PROG, vel=62)
    _chimes(sc, t0 + 32.0, 8, VERSE_PROG, vel=50)
    _bass_walk(sc, t0, VERSE_PROG, reps=4, vel=94)
    _drums(sc, t0, 8, 0.42, sidestick=True, fills=False)
    _drums(sc, t0 + 32.0, 8, 0.52)


def pre1(sc) -> None:
    _pre(sc, 96.0, hot=0)


def chorus1(sc) -> None:
    _chorus(sc, 128.0, 3, lyrics=True, intensity=0.78)
    en.vowel_curve(sc, AAH, [(128.0, 96), (174.0, 84)], step=4.0)
    en.vowel(sc, OOH, 92, 128.0)


def verse2(sc) -> None:
    t0 = 176.0
    _comp(sc, t0, 8, VERSE_PROG, vel=68)
    _jangle(sc, GTR_L, t0, 8, VERSE_PROG, vel=64)
    _chimes(sc, t0, 8, VERSE_PROG, vel=50, boundary=True)
    _bass_walk(sc, t0, VERSE_PROG, reps=2, vel=96)
    _drums(sc, t0, 8, 0.55)


def pre2(sc) -> None:
    _pre(sc, 208.0, hot=4, ep=True)


def chorus2(sc) -> None:
    _chorus(sc, 240.0, 3, vel_lift=5, ep=True, lyrics=True, intensity=0.86)
    en.vowel_curve(sc, AAH, [(240.0, 100), (286.0, 88)], step=4.0)
    en.vowel(sc, OOH, 96, 240.0)
    en.echo_throw(sc, LEAD, 284.0, base=0, peak=80, release=3.0)


def middle8(sc) -> None:
    t0 = 288.0
    en.soft_pedal(sc, PIANO, t0, t0 + 30.0)
    for i, d in enumerate(MID_PROG):
        b = t0 + 4.0 * i
        tri = _triad(d, octave=1)
        seq = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2] + 12,
               tri[1] + 12, tri[2], tri[1]]
        for k, p in enumerate(seq):
            jt = 0 if (i == 0 and k == 0) else 3
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 54, jt=jt, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    _strings_pad(sc, t0, MID_PROG, 8, vel=54,
                 swell=[(t0, 46), (t0 + 24.0, 84), (t0 + 31.0, 72)])
    _ooh_line(sc, t0, _MID_OOH, vel=44)
    en.vowel(sc, OOH, 40, t0)
    _bass_mid(sc, t0)
    for i in range(8):
        b = t0 + 4.0 * i
        sc.hit(36, b, 60, jt=0 if i == 0 else 2)
        sc.hit(37, b + 2.0, 44, jt=2)               # side-stick heartbeat
    _mid_lead(sc, t0)


def final_chorus(sc) -> None:
    t0 = 320.0
    _chorus(sc, t0, 4, vel_lift=6, ep=True, power=True, lyrics=True,
            intensity=0.92, porta_off=False)
    _strings_pad(sc, t0, CHORUS_PROG, 16, vel=56,
                 swell=[(t0, 70), (t0 + 32.0, 90), (t0 + 64.0, 104),
                        (t0 + 78.0, 78)])
    en.vowel_curve(sc, AAH, [(t0, 102), (t0 + 68.0, 112), (t0 + 79.0, 92)],
                   step=4.0)
    en.vowel(sc, OOH, 100, t0)
    # THE TAG (384-400): the last lift, then release into the outro.
    tag = t0 + 64.0
    _anthem(sc, tag, 4, TAG_PROG, vel=92)
    _power_bed(sc, tag, 4, TAG_PROG, vel=102, push=False)
    chords = [en.triad(A3, _MODE, d) for d in TAG_PROG]
    en.pad_block(sc, STRINGS, tag, chords, 4.0, size=4, lo=50, hi=79,
                 vel=60, legato=0.0)
    _choir_pads(sc, tag, TAG_PROG, 4, vel=62)
    _ooh_line(sc, tag, [(6, 0.0, 3.9), (7, 4.0, 3.9), (8, 8.0, 7.4)],
              vel=56)
    _tag_lead(sc, tag)
    en.lyric(sc, tag, "fly on")
    _drums(sc, tag, 4, 0.85, crash_in=True, tamb=True)
    sc.note(BASS, 50, tag, 3.8, 102, jt=2, jv=3)
    sc.note(BASS, 52, tag + 4.0, 3.8, 100, jt=2, jv=3)
    sc.note(BASS, 45, tag + 8.0, 3.8, 100, jt=2, jv=3)
    for k in range(8):          # descending release run into the outro
        sc.note(BASS, en.pitch(A2, _MODE, 8 - k), tag + 12.0 + 0.5 * k,
                0.44, int(en.lerp(96, 78, k / 7)), jt=2, jv=3)
    en.portamento_off(sc, LEAD, t0 + 79.5)


def outro(sc) -> None:
    t0 = 400.0
    _jangle(sc, GTR_L, t0, 4, OUTRO_PROG[:4], vel=54)
    _jangle(sc, GTR_L, t0 + 16.0, 2, [1, 4], vel=48)
    _chimes(sc, t0, 6, OUTRO_PROG, vel=44, boundary=True)
    _bass_outro(sc, t0)
    en.soft_pedal(sc, PIANO, t0, t0 + 30.0)
    for i in range(3):                               # falling piano bells
        b = t0 + 8.0 * i
        v = int(en.lerp(54, 40, i / 2))
        sc.note(PIANO, 81, b, 1.5, v, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, 76, b + 1.5, 1.5, v - 4, jt=3, jv=3)
        sc.note(PIANO, 73, b + 3.0, 1.0, v - 8, jt=3, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 7.9)
    _drums(sc, t0, 4, 0.32, sidestick=True, fills=False)
    for k in range(16):                              # hats thin out
        sc.hit(42, t0 + 16.0 + 0.5 * k, int(en.lerp(40, 26, k / 15)),
               jt=2, jv=4)
    _ooh_line(sc, t0, [(5, 0.0, 7.5), (6, 8.0, 7.5)], vel=42)
    en.vowel(sc, OOH, 30, t0)                        # back to a closed mm
    chords = [en.triad(A3, _MODE, d) for d in (1, 4)]
    en.pad_block(sc, STRINGS, t0, chords, 8.0, size=3, lo=52, hi=76,
                 vel=44, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0, 62), (t0 + 15.5, 28)], step=1.0)
    en.echo_throw(sc, GTR_L, t0 + 22.0, base=0, peak=76, release=4.0)
    # The kite lets go: one ringing A-add9, dying away.
    ring = t0 + 24.0
    en.strum(sc, GTR_L, [57, 61, 64, 69, 71], ring, 7.4, 58, spread=0.06)
    sc.note(GTR_R, 81, ring, 7.4, 46, jt=0, jv=0)
    sc.note(GTR_R, 76, ring + 0.06, 7.3, 42, jt=0, jv=0)
    for j, p in enumerate((57, 64, 69, 73)):
        sc.note(PIANO, p, ring, 7.4, 54 - 2 * j, jt=0, jv=0)
    en.sustain(sc, PIANO, ring + 0.02, ring + 7.5)
    sc.note(BASS, 45, ring, 7.4, 76, jt=0, jv=0)
    sc.hit(49, ring, 84, jt=0)
    sc.hit(36, ring, 82, jt=0)
    en.cc_curve(sc, GTR_L, 11, [(ring, 100), (ring + 7.0, 40)], step=0.5)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD 6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 4, 25, 26, 29, 33, 48, 52, 53, 80}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, LEAD, KEYS, STRINGS, DRUMS}
NOTE_RANGES = {
    PIANO: (52, 94), GTR_L: (55, 83), GTR_R: (44, 86), BASS: (37, 63),
    AAH: (53, 79), OOH: (55, 73), LEAD: (68, 84), KEYS: (50, 76),
    STRINGS: (48, 81),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (210.0, 230.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "chorus1", 1.0),
    ("final_chorus", ">=", "chorus1", 1.05),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("pre1", "<=", "chorus1", 1.0),
    ("verse2", "<=", "chorus2", 0.9),
    ("middle8", "<=", "chorus2", 0.8),
    ("intro", "<=", "chorus1", 0.8),
    ("outro", "<=", "final_chorus", 0.6),
]
LATE_CHANNELS = {AAH: 96.0, OOH: 96.0, LEAD: 128.0, KEYS: 224.0,
                 STRINGS: 288.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 9), ("chorus1", 9), ("verse2", 9),
                 ("chorus2", 9), ("final_chorus", 9)],
    "hook": "final_chorus",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH],
    "sections": ["pre1", "chorus1", "pre2", "chorus2", "final_chorus"],
}
FEATURES_EXPECTED = {
    "portamento", "cc70_vowel", "cc64_sustain", "cc67_soft",
    "cc11_expression", "cc68_legato", "cc94_echo", "pitch_bend",
    "cc1_vibrato", "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles (written before the music, composed to pass)
# ---------------------------------------------------------------------------

_CHORUS_ONSETS = (128.0, 240.0, 320.0)


def oracles(sc, info, spans):
    import verify

    # 1. kite_hook — the hook recurs note-for-note at every chorus onset.
    fails_hook: list[str] = []
    onsets = {(round(on * 4) / 4, p)
              for on, _off, p, _v in verify._note_spans(sc, LEAD)}
    for c in _CHORUS_ONSETS:
        for deg, start, _dur in _HOOK:
            want = (round((c + start) * 4) / 4, en.pitch(A4, _MODE, deg))
            if want not in onsets:
                fails_hook.append(f"hook note (deg {deg}) missing at beat "
                                  f"{c + start:.2f}")

    # 2. glide_signature — portamento is ON at every chorus onset and
    # OFF again by the second verse (the glide is a chorus signature).
    fails_glide: list[str] = []
    cc65 = verify._cc_events(sc, LEAD, 65)

    def _last(beat):
        state = None
        for b, v in cc65:
            if b <= beat:
                state = v
            else:
                break
        return state

    for c in _CHORUS_ONSETS:
        v = _last(c + 0.5)
        if v is None or v < 64:
            fails_glide.append(f"portamento not engaged at chorus onset {c}")
    if (_last(200.0) or 0) >= 64:
        fails_glide.append("portamento still on in verse 2 (beat 200)")

    # 3. choir_morph — CC70 opens from oo (<= 50) to ah (>= 85) inside
    # each pre-chorus window: the signature swell.
    fails_morph: list[str] = []
    cc70 = verify._cc_events(sc, AAH, 70)
    for t0, t1 in ((96.0, 128.0), (208.0, 240.0)):
        win = [(b, v) for b, v in cc70 if t0 - 1e-9 <= b < t1]
        if not win:
            fails_morph.append(f"no CC70 on the aah choir in [{t0}, {t1})")
            continue
        first = win[0][1]
        last_q = [v for b, v in win if b >= t1 - 8.0]
        if first > 50:
            fails_morph.append(f"pre at {t0}: starts at CC70={first} "
                               f"(not an oo, need <= 50)")
        if not last_q or max(last_q) < 85:
            fails_morph.append(f"pre at {t0}: never opens to ah "
                               f"(max {max(last_q) if last_q else 'none'} "
                               f"in the last 8 beats, need >= 85)")

    # 4. jangle_engine — the verses really are wall-to-wall picked
    # eighths on the jangle guitar (>= 8 notes per bar).
    fails_jangle: list[str] = []
    gtr = verify._note_spans(sc, GTR_L)
    for name, t0, t1 in (("verse1", 32.0, 96.0), ("verse2", 176.0, 208.0)):
        bars = (t1 - t0) / 4.0
        count = sum(1 for on, _off, _p, _v in gtr if t0 - 0.05 <= on < t1)
        if count < 8 * bars:
            fails_jangle.append(f"{name}: {count} jangle notes "
                                f"(< {int(8 * bars)})")

    return [("kite_hook", fails_hook),
            ("glide_signature", fails_glide),
            ("choir_morph", fails_morph),
            ("jangle_engine", fails_jangle)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD 6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# PROVISIONAL: measured 3.80 dB (2026.07.11, ferrosintesis 0.13.1
# per-track render); pinned with 1.8 dB slack, re-pinned at phase D.
_LIFT_DB = 2.0    # final chorus over verse 1
# PROVISIONAL: measured 2.66 dB (2026.07.11, ferrosintesis 0.13.1
# per-track render); pinned with 1.16 dB slack, re-pinned at phase D.
_SWELL_DB = 1.5   # pre-chorus-2 second half over first half


def audio_checks(ctx):
    # 1. Chorus lift: the final chorus lands well above the verse bed.
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(40.0, 88.0)
    f0, f1 = ctx.bar_window(320.0, 384.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # 2. The pre-chorus choir swell: pre 2 audibly rises into chorus 2.
    fails_swell: list[str] = []
    a0, a1 = ctx.bar_window(208.0, 224.0)
    b0, b1 = ctx.bar_window(224.0, 240.0)
    first = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    second = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    if second < first + _SWELL_DB:
        fails_swell.append(f"pre-chorus swell: 2nd half {second:.1f} dB "
                           f"not >= 1st half {first:.1f} dB + {_SWELL_DB}")

    return [("chorus_lift", fails_lift),
            ("prechorus_swell", fails_swell)]
