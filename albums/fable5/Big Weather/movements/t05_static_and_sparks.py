"""t05_static_and_sparks.py — "Static & Sparks" (Big Weather, track 5).

The album's first minor-key rocker: F#-minor riff rock at 128 BPM.  A
distortion-guitar RIFF with a chromatic b2 "spark" (G natural against
F#) bookends the song and returns as a post-chorus every time it lands
(oracle-pinned in four windows); the verses run on a genuinely GAPPED
palm-mute chug engine (oracle-pinned duty cycle — mono safety by
construction); the rock organ is choreographed with REAL CC1 Leslie
ramps (slow chorale in the verses, spin-up into every chorus, an
exposed fast->slow coda that the audio probe measures); the middle-8
is a wah lead-guitar feature (CC74 LFO + CC71 resonance, audio-probed);
and before the final chorus the storm KNOCKS THE POWER OUT — an
8-bar whisper drop, quiet but never silent (palm-mute ticks + low organ
pad + heartbeat kick, velocity-ceiling oracle + coverage oracle), the
Leslie audibly spinning up in its last bar before the band slams back.

Form (HLD §4, full grammar + the whisper drop):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 | middle8 |
  whisper | final_chorus | outro
"""

from __future__ import annotations

import cmath
import math

import conductor
import engine as en

NUMBER = 5
TITLE = "Static & Sparks"
FILE = "05 - Static & Sparks.mid"
SEED = 20260705

BPM = 128.0

# Channels (HLD §3; lean guitar-band palette — riff rock skips the
# orchestra and the choir per HLD D3, width from the moderate 48/80
# guitar split, every sustained bed centred).
PIANO, GTR_M, GTR_D, BASS = 0, 1, 2, 3
LEAD, KEYS = 6, 7
DRUMS = 9

_SECTIONS = [
    ("intro",          0.0,  32.0),
    ("verse1",        32.0,  96.0),
    ("pre1",          96.0, 128.0),
    ("chorus1",      128.0, 176.0),
    ("verse2",       176.0, 208.0),
    ("pre2",         208.0, 240.0),
    ("chorus2",      240.0, 288.0),
    ("middle8",      288.0, 336.0),
    ("whisper",      336.0, 368.0),
    ("final_chorus", 368.0, 448.0),
    ("outro",        448.0, 488.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 3, 1)],                      # F# minor, three sharps
    channels=[
        (PIANO, "piano",          0,  96, 64, 45),
        (GTR_M, "palm-mute gtr", 28,  96, 48, 30),
        (GTR_D, "drive gtr",     30,  94, 80, 32),
        (BASS,  "bass guitar",   33, 105, 64, 22),
        (LEAD,  "lead guitar",   29,  95, 64, 50),
        (KEYS,  "rock organ",    18,  86, 64, 55),
        (DRUMS, "drums",          0, 108, 64, 42),
    ],
    program_changes=[
        (GTR_D,  32.0, 29),     # verses breathe on lighter overdrive
        (GTR_D,  96.0, 30),     # full distortion from the pre-chorus
        (GTR_D, 176.0, 29),
        (GTR_D, 208.0, 30),
    ],
)

# ---------------------------------------------------------------------------
# Harmony — F# natural minor (aeolian).  Degrees against an F#2 tonic.
# ---------------------------------------------------------------------------

FS2, FS3 = en.n("F#2"), en.n("F#3")
_MODE = "aeolian"

VERSE_PROG = [1, 1, 6, 7, 1, 1, 4, 5]     # F#m F#m D E | F#m F#m Bm C#m
PRE_PROG = [4, 6, 5, 7]                   # Bm  D   C#m E
CHORUS_PROG = [1, 6, 3, 7]                # F#m D   A   E
MID_PROG = [6, 7, 1, 1, 6, 7, 1, 1, 4, 6, 7, 7]


def _root(deg: int, octave: int = 0) -> int:
    return en.pitch(FS2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(FS2, _MODE, deg)]


# The RIFF — the drive guitar's signature (2 bars).  Power-chord punches
# on i / bIII / IV with a single-note turn whose G natural (the
# chromatic b2 "spark") bites against the F# key.  jt=0 throughout: the
# riff is oracle-pinned in four windows (riff_recur).
# (beat, semitone offset from F#2, dur, vel, power?)
_RIFF = [
    (0.00,  0, 0.70, 108, True),
    (1.00,  0, 0.40,  96, True),
    (1.50,  3, 0.40, 100, True),    # A5 — the bIII punch
    (2.00,  5, 0.45, 102, True),    # B5
    (2.50,  3, 0.40,  98, True),
    (3.00,  0, 0.90, 104, True),
    (4.00,  0, 0.70, 108, True),
    (5.00,  0, 0.40,  96, True),
    (5.50, 10, 0.28,  92, False),   # E3  — single-note turn
    (5.75, 12, 0.28,  94, False),   # F#3
    (6.00, 13, 0.28,  98, False),   # G3  — the SPARK (chromatic b2)
    (6.25, 12, 0.28,  94, False),   # F#3
    (6.50,  7, 0.45, 100, True),    # C#5
    (7.00,  5, 0.95, 104, True),    # B5 — resolves home at the loop
]

# The chorus HOOK — (degree, start, dur) over 16 beats (F#m D A E),
# sung by the lead guitar with pitch-bend vibrato blooms on the holds
# (CC1 is inert on guitars — repo honoring table — so vibrato is bends).
_HOOK = [
    (8,  0.00, 0.70), (8,  0.75, 0.45), (10, 1.50, 1.00), (8,  2.50, 1.50),
    (6,  4.00, 0.70), (8,  4.75, 0.45), (10, 5.50, 1.00), (9,  6.50, 1.50),
    (9,  8.00, 0.70), (8,  8.75, 0.45), (7,  9.50, 1.00), (5, 10.50, 1.50),
    (7, 12.00, 0.70), (8, 12.75, 0.45), (7, 13.50, 0.50), (8, 14.00, 1.90),
]

_HOOK_LYRICS = ["static and sparks", "wire in the dark",
                "count the seconds", "till the thunder"]

# The bass HOOK — chorus-2 countermelody (an answer, not a doubling;
# BASS_SPEC hook section).  (pitch, start, dur) over 16 beats.
_BASS_HOOK = [
    (42, 0.00, 1.40), (49, 1.50, 0.45), (50, 2.00, 0.90), (52, 3.00, 0.90),
    (50, 4.00, 0.70), (52, 4.75, 0.45), (54, 5.50, 0.90), (52, 6.50, 1.40),
    (45, 8.00, 0.70), (47, 8.75, 0.45), (49, 9.50, 0.90), (50, 10.50, 1.40),
    (52, 12.00, 0.70), (50, 12.75, 0.45), (49, 13.50, 0.45),
    (42, 14.00, 1.40), (44, 15.50, 0.22), (45, 15.75, 0.22),
]


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _power(sc, ch, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    """Root + fifth + octave; the per-channel Drive intermodulates them."""
    for i, off in enumerate((0, 7, 12)):
        sc.note(ch, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _riff(sc, t0: float, reps: int, vel_scale: float = 1.0) -> None:
    """State the RIFF `reps` times on the drive guitar (8 beats each)."""
    for r in range(reps):
        base = t0 + 8.0 * r
        for beat, off, dur, vel, power in _RIFF:
            v = max(1, int(round(vel * vel_scale)))
            if power:
                _power(sc, GTR_D, FS2 + off, base + beat, dur, v)
            else:
                sc.note(GTR_D, FS3 + (off - 12), base + beat, dur, v,
                        jt=0, jv=3)


def _bass_riff_lock(sc, t0: float, reps: int, vel: int = 100) -> None:
    """Bass locks the riff's power-chord roots (single notes, gapped)."""
    for r in range(reps):
        base = t0 + 8.0 * r
        for beat, off, dur, vel_r, power in _RIFF:
            if power:
                sc.note(BASS, FS2 + off, base + beat, min(dur, 0.6),
                        vel - (108 - vel_r), jt=2, jv=3)


def _chug(sc, t0: float, bars: int, prog: list[int], vel: int = 78) -> None:
    """The verse engine: GAPPED palm-mute dyads (root + fifth) — real
    rests between hits (mono safety by construction, oracle-pinned)."""
    hits = [0.0, 0.5, 0.75, 1.5, 2.0, 2.5, 3.0, 3.25]
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        for h in hits:
            accent = h in (0.0, 1.5, 3.0)
            v = vel + (8 if accent else 0) - (4 if h % 0.5 else 0)
            jt = 0 if (i == 0 and h == 0.0) else 2
            sc.note(GTR_M, r, b + h, 0.22, v, jt=jt, jv=3)
            sc.note(GTR_M, r + 7, b + h, 0.22, v - 8, jt=jt, jv=3)


def _open_eights(sc, t0: float, bars: int, prog: list[int],
                 vel: int = 84) -> None:
    """Chorus mute-guitar: open eighth dyads, still gapped (0.30 dur)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        for k in range(8):
            jt = 0 if (i == 0 and k == 0) else 2
            v = vel + (6 if k % 2 == 0 else -6)
            sc.note(GTR_M, r, b + 0.5 * k, 0.30, v, jt=jt, jv=3)
            sc.note(GTR_M, r + 7, b + 0.5 * k, 0.30, v - 8, jt=jt, jv=3)


def _power_anthem(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 98) -> None:
    """Chorus drive guitar: syncopated power-chord punches ("1, and-of-1,
    2-and... "), gapped enough to stay honest at pan 80."""
    pattern = [(0.0, 0.70), (1.0, 0.35), (1.5, 0.70), (2.5, 0.35),
               (3.0, 0.70)]
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        for k, (beat, dur) in enumerate(pattern):
            jt = 0 if (i == 0 and k == 0) else 2
            _power(sc, GTR_D, r, b + beat, dur,
                   vel - (8 if dur < 0.5 else 0), jt=jt)


def _drive_swells(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 88) -> None:
    """Pre-chorus drive guitar: one held power swell per bar, gapped."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        _power(sc, GTR_D, r, b, 1.5, vel, jt=0 if i == 0 else 2)
        _power(sc, GTR_D, r, b + 2.5, 0.45, vel - 10, jt=2)


def _spark_lick(sc, b: float, vel: int = 80) -> None:
    """The verse answer lick: the riff's chromatic turn, gapped 16ths."""
    for k, off in enumerate((10, 12, 13, 12)):
        sc.note(GTR_D, FS2 + off, b + 0.25 * k, 0.2, vel - 2 * k,
                jt=2, jv=3)


def _bass_walk(sc, t0: float, prog: list[int], vel: int = 96,
               reps: int = 1) -> None:
    """Verse bass: a stepwise minor walk — root, 2nd, 3rd, up to the
    fifth and back, stepwise approach into every next root."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        nxt = seq[(i + 1) % len(seq)]
        sc.note(BASS, _root(deg), b, 0.70, vel, jt=2, jv=3)
        sc.note(BASS, _root(deg + 1), b + 1.0, 0.40, vel - 10, jt=2, jv=3)
        sc.note(BASS, _root(deg + 2), b + 1.5, 0.40, vel - 8, jt=2, jv=3)
        sc.note(BASS, _root(deg + 4), b + 2.0, 0.65, vel - 4, jt=2, jv=3)
        sc.note(BASS, _root(deg + 2), b + 2.75, 0.20, vel - 18, jt=3, jv=4)
        sc.note(BASS, _root(deg + 1), b + 3.0, 0.45, vel - 8, jt=2, jv=3)
        approach = _root(nxt) - 1 if _root(nxt) > _root(deg) \
            else _root(nxt) + 2
        sc.note(BASS, approach, b + 3.5, 0.45, vel - 4, jt=2, jv=3)


def _bass_drive(sc, t0: float, bars: int, prog: list[int],
                vel: int = 102) -> None:
    """Chorus bass: driving eighths with an octave pop and stepwise
    turnarounds — melodic even at full tilt."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        sc.note(BASS, _root(deg), b, 0.45, vel, jt=2, jv=3)
        sc.note(BASS, _root(deg), b + 0.5, 0.40, vel - 8, jt=2, jv=3)
        sc.note(BASS, _root(deg + 7), b + 1.0, 0.45, vel - 2, jt=2, jv=3)
        sc.note(BASS, _root(deg + 4), b + 1.5, 0.40, vel - 8, jt=2, jv=3)
        sc.note(BASS, _root(deg), b + 2.0, 0.65, vel - 4, jt=2, jv=3)
        sc.note(BASS, _root(deg + 1), b + 2.75, 0.20, vel - 18, jt=3, jv=4)
        sc.note(BASS, _root(deg + 2), b + 3.0, 0.40, vel - 8, jt=2, jv=3)
        sc.note(BASS, _root(deg + 1), b + 3.5, 0.40, vel - 6, jt=2, jv=3)


def _piano_pump(sc, t0: float, bars: int, prog: list[int],
                vel: int = 74, vel_end: int = 86) -> None:
    """Pre-chorus piano: eighth-note triad pump over left-hand octaves,
    velocity rising across the section."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(vel, vel_end, i / max(1, bars - 1))))
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        jt = 0 if i == 0 else 3
        sc.note(PIANO, r, b, 1.9, v + 4, jt=jt, jv=4)
        sc.note(PIANO, r, b + 2.0, 1.9, v, jt=3, jv=4)
        for k in range(8):
            for p in tri:
                sc.note(PIANO, p, b + 0.5 * k, 0.4,
                        v - (6 if k % 2 else 0) - 8, jt=jt if k == 0 else 3,
                        jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_anthem(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 88) -> None:
    """Chorus piano: block chords with an octave crown."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        for k, (beat, dur) in enumerate(((0.0, 1.4), (1.5, 0.9),
                                         (2.5, 1.4))):
            jt = 0 if (i == 0 and k == 0) else 3
            sc.note(PIANO, r, b + beat, dur, vel, jt=jt, jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 5, jt=jt, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.0, 0.9, vel + 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _organ_pad(sc, t0: float, chords_degs: list[int], span: float = 4.0,
               vel: int = 56, lo: int = 55, hi: int = 76,
               vel_end: int | None = None) -> None:
    chords = [en.triad(FS3, _MODE, d) for d in chords_degs]
    en.pad_block(sc, KEYS, t0, chords, span, size=3, lo=lo, hi=hi,
                 vel=vel, vel_end=vel_end, legato=0.0)


def _drums(sc, t0: float, bars: int, intensity: float, *,
           ride: bool = False, crash_in: bool = False, china: bool = False,
           hats16: bool = False, fills: bool = True) -> None:
    """The kit groove: syncopated push kick, backbeat + ghosts, and a
    snare-build fill signature (16ths crescendo, closing tom pair)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        v = int(round(en.lerp(70, 106, intensity)))
        if crash_in and first:
            sc.hit(49, b, min(120, v + 14), jt=0)
        if china and i % 2 == 0 and not first:
            sc.hit(52, b, v + 4, jt=2)
        # Kick: the push pattern.
        sc.hit(36, b, v + 8, jt=0 if first else 2)
        sc.hit(36, b + 1.75, v, jt=2)
        sc.hit(36, b + 2.5, v + 2, jt=2)
        if intensity > 0.7:
            sc.hit(36, b + 3.5, v - 6, jt=2)
        # Snare 2 and 4, ghost on the a-of-4 (the fill owns beats 3-4).
        sc.hit(38, b + 1.0, v + 10, jt=2, jv=4)
        if not fill_bar:
            sc.hit(38, b + 3.0, v + 10, jt=2, jv=4)
            if intensity < 0.9:
                sc.hit(38, b + 3.75, max(16, v - 48), jt=3, jv=6)
        # Hats or ride.
        key = 51 if ride else 42
        n = 16 if hats16 else 8
        step = 4.0 / n
        for k in range(n):
            strong = k % (n // 4) == 0
            hv = v - (8 if strong else 24)
            if fill_bar and k * step >= 2.0:
                continue
            sc.hit(key, b + k * step, max(18, hv),
                   jt=0 if (first and k == 0) else 2, jv=5)
        if ride and i % 2 == 0:
            sc.hit(53, b + 2.0, v - 8, jt=2)
        if not ride and not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 16, jt=2)
        if fill_bar:
            for k in range(6):
                sc.hit(38, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 26, v + 12, k / 5)), jt=2)
            sc.hit(47, b + 3.5, v + 6, jt=2)
            sc.hit(43, b + 3.75, v + 10, jt=2)


def _halftime(sc, t0: float, bars: int, vel: int = 72) -> None:
    """Middle-8 halftime: kick, one big snare on 3, pedal-hat quarters."""
    for i in range(bars):
        b = t0 + 4.0 * i
        sc.hit(36, b, vel + 6, jt=0 if i == 0 else 2)
        sc.hit(36, b + 1.5, vel - 6, jt=2)
        sc.hit(38, b + 2.0, vel + 10, jt=2, jv=4)
        for q in (1.0, 3.0):
            sc.hit(44, b + q, vel - 34, jt=2, jv=3)


def _lead_hook(sc, t0: float, reps: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The chorus hook; pitch-bend vibrato blooms on every long note."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, FS3, _MODE, _HOOK, vel, jt=0, jv=3,
                gate=0.97)
        for deg, start, dur in _HOOK:
            if dur >= 1.4:
                en.vibrato(sc, LEAD, base + start, dur * 0.92, depth=0.22,
                           cycles_per_beat=1.4, delay=0.4)
        if lyrics:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


# The middle-8 wah feature.  Bars 1-4 are a SOLO wah CHOP riff — the
# lead repicks straight eighths (one pitch per bar, symmetric velocity
# pattern) with nothing else underneath, so every CC74 half-cycle
# contains identical fresh picks: the audio probe compares bright-half
# picks with dark-half picks of the SAME pitch and rhythm.  (GM29 is a
# decaying pluck — a "held" note is reverb tail by the dark half, so
# chops, not holds, are what a wah probe can measure — house lesson.)
_WAH_CHOP = [8, 8, 10, 12]      # F#4 F#4 A4 C#5, one chopped bar each
# Bars 5-8: the band returns halftime and the line starts to move;
# bars 9-12 fall to F#3 while the drums build — then the power cuts.
_WAH_MELODY = [
    (11, 16.0, 1.0), (10, 17.0, 0.5), (9,  17.5, 0.5), (10, 18.0, 2.0),
    (8,  20.0, 1.5), (9,  21.5, 0.5), (10, 22.0, 2.0),
    (8,  24.0, 1.0), (6,  25.0, 0.5), (8,  25.5, 0.5), (9,  26.0, 2.0),
    (12, 28.0, 3.5),
    (11, 32.0, 1.0), (10, 33.0, 1.0), (9,  34.0, 1.0), (8,  35.0, 1.0),
    (7,  36.0, 1.0), (6,  37.0, 1.0), (5,  38.0, 1.0), (4,  39.0, 1.0),
    (3,  40.0, 2.0), (2,  42.0, 2.0), (1,  44.0, 3.4),
]


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    _riff(sc, 0.0, 4)
    # Bars 3-4: hats and kick sneak in; bars 5-8 the full groove.
    for i in range(2):
        b = 8.0 + 4.0 * i
        sc.hit(36, b, 84, jt=2)
        sc.hit(36, b + 2.5, 78, jt=2)
        for k in range(8):
            sc.hit(42, b + 0.5 * k, 52 - (14 if k % 2 else 0), jt=2, jv=5)
    _drums(sc, 16.0, 4, 0.7, crash_in=True)
    _bass_riff_lock(sc, 16.0, 2)
    en.echo_throw(sc, GTR_D, 30.0, base=0, peak=72, release=1.8)


def verse1(sc) -> None:
    t0 = 32.0
    _chug(sc, t0, 16, VERSE_PROG)
    _bass_walk(sc, t0, VERSE_PROG, reps=2)
    _drums(sc, t0, 8, 0.5)
    _drums(sc, t0 + 32.0, 8, 0.6)
    for i in (3, 7, 11, 15):                     # the answer lick
        _spark_lick(sc, t0 + 4.0 * i + 3.0, vel=78 + (4 if i > 7 else 0))


def _pre(sc, t0: float, *, pickup: bool = False) -> None:
    _chug(sc, t0, 8, PRE_PROG, vel=84)
    _drive_swells(sc, t0, 8, PRE_PROG)
    _bass_walk(sc, t0, PRE_PROG, reps=2, vel=100)
    _piano_pump(sc, t0, 8, PRE_PROG)
    _organ_pad(sc, t0, [PRE_PROG[i % 4] for i in range(8)], vel=46)
    en.expr_curve(sc, KEYS, [(t0 - 0.1, 44), (t0 + 16.0, 78),
                             (t0 + 31.5, 108)], step=1.0)
    sc.cc(KEYS, 11, 127, t0 + 32.0)
    _drums(sc, t0, 4, 0.65)
    _drums(sc, t0 + 16.0, 4, 0.75, hats16=True)
    # Leslie spin-up into the chorus (headline choreography).
    en.leslie(sc, KEYS, t0 + 28.0, t0 + 32.0, 14, 96)
    if pickup:
        en.line(sc, LEAD, t0 + 30.0, FS3, _MODE,
                [(5, 0.0, 0.5), (6, 0.5, 0.5), (7, 1.0, 0.9)], 92, jt=2,
                jv=3)


def pre1(sc) -> None:
    sc.cc(KEYS, 1, 14, 95.9)                     # rotor idles slow
    _pre(sc, 96.0)


def _chorus(sc, t0: float, *, vel_lift: int = 0, lyrics: bool = False,
            bass_hook: bool = False, growl: bool = False,
            intensity: float = 0.85, china: bool = False,
            descant: int = 0) -> None:
    """8 hook bars + 4 post-chorus riff bars (the riff IS the chorus
    tail — oracle-pinned against the intro statement)."""
    _piano_anthem(sc, t0, 8, CHORUS_PROG, vel=88 + vel_lift)
    _open_eights(sc, t0, 8, CHORUS_PROG, vel=84 + vel_lift)
    _power_anthem(sc, t0, 8, CHORUS_PROG, vel=98 + vel_lift)
    _organ_pad(sc, t0, [CHORUS_PROG[i % 4] for i in range(8)],
               vel=58 + vel_lift, lo=52, hi=64)
    if descant:                                  # screaming organ top note
        for i in range(8):
            top = _root(CHORUS_PROG[i % 4], octave=2)
            sc.note(KEYS, top, t0 + 4.0 * i, 3.9, descant,
                    jt=0 if i == 0 else 3, jv=3)
    _lead_hook(sc, t0, 2, 98 + vel_lift, lyrics=lyrics)
    if bass_hook:
        for r in range(2):
            for p, start, dur in _BASS_HOOK:
                sc.note(BASS, p, t0 + 16.0 * r + start, dur,
                        104 + vel_lift, jt=2, jv=3)
    else:
        _bass_drive(sc, t0, 8, CHORUS_PROG, vel=102 + vel_lift)
    _drums(sc, t0, 8, intensity, crash_in=True, china=china)
    # Post-chorus riff (bars 9-12): guitars take the spotlight.
    _riff(sc, t0 + 32.0, 2)
    _bass_riff_lock(sc, t0 + 32.0, 2, vel=102 + vel_lift)
    _drums(sc, t0 + 32.0, 4, intensity, crash_in=True, china=china)
    _organ_pad(sc, t0 + 32.0, [1, 1, 1, 1], vel=54 + vel_lift,
               lo=52, hi=64)
    if growl:
        en.at_curve(sc, KEYS, [(t0 + 32.0, 16), (t0 + 40.0, 90),
                               (t0 + 47.0, 24)], step=0.5)


def chorus1(sc) -> None:
    t0 = 128.0
    _chorus(sc, t0, lyrics=True)
    # Leslie accelerates across the whole first chorus: 80 -> 118.
    en.leslie(sc, KEYS, t0, t0 + 32.0, 80, 118)


def verse2(sc) -> None:
    t0 = 176.0
    en.leslie(sc, KEYS, t0, t0 + 4.0, 118, 16)   # rotor brakes to chorale
    _chug(sc, t0, 8, VERSE_PROG)
    _bass_walk(sc, t0, VERSE_PROG)
    _drums(sc, t0, 8, 0.55)
    _organ_pad(sc, t0, [VERSE_PROG[i % 8] for i in range(8)], vel=40)
    for i in range(0, 8, 2):                     # dark piano root octaves
        deg = VERSE_PROG[i]
        r = _root(deg, octave=1)
        sc.note(PIANO, r, t0 + 4.0 * i, 1.8, 56, jt=3, jv=4)
        sc.note(PIANO, r + 12, t0 + 4.0 * i + 2.0, 1.8, 50, jt=3, jv=4)
    for i in (3, 7):
        _spark_lick(sc, t0 + 4.0 * i + 3.0, vel=82)


def pre2(sc) -> None:
    _pre(sc, 208.0, pickup=True)


def chorus2(sc) -> None:
    t0 = 240.0
    _chorus(sc, t0, vel_lift=4, lyrics=True, bass_hook=True, growl=True,
            intensity=0.88, descant=72)
    sc.cc(KEYS, 1, 112, t0)                      # rotor stays fast


def middle8(sc) -> None:
    t0 = 288.0
    # The wah feature (headline #2): CC74 LFO + CC71 resonance sweep.
    en.bend_range(sc, LEAD, 12, t0 - 0.10)
    sc.bend(LEAD, t0, -2.0)                      # full-deflection rise-in
    # Bars 1-4: the wah chop riff (the probe's clean windows).
    for i, deg in enumerate(_WAH_CHOP):
        b = t0 + 4.0 * i
        for k in range(8):
            vel = 100 if k % 4 == 0 else (92 if k % 2 == 0 else 88)
            sc.note(LEAD, en.pitch(FS3, _MODE, deg), b + 0.5 * k, 0.38,
                    vel, jt=0, jv=2)
    en.line(sc, LEAD, t0, FS3, _MODE, _WAH_MELODY, 96, jt=0, jv=3,
            gate=0.97)
    # A fast octave whip up — done before the probe windows open (+0.45).
    en.bend_ramp(sc, LEAD, t0 + 0.02, t0 + 0.42, -2.0, 0.0, steps=10)
    for deg, start, dur in _WAH_MELODY:
        if dur >= 2.5:
            en.vibrato(sc, LEAD, t0 + start + 0.8, dur - 1.0, depth=0.06,
                       cycles_per_beat=1.3, delay=0.0)
    en.wah(sc, LEAD, t0, 48.0, lo=30, hi=110, cycles_per_beat=0.25)
    en.cc_curve(sc, LEAD, 71, [(t0, 55), (t0 + 32.0, 82),
                               (t0 + 47.0, 50)], step=1.0)
    en.echo_throw(sc, LEAD, t0 + 45.5, base=0, peak=84, release=2.0)
    # Leslie brakes; the organ sits out the solo bars, then returns as
    # a dark low pad at bar 5 (bars 1-4 are the wah probe's windows).
    en.leslie(sc, KEYS, t0, t0 + 3.0, 112, 12)
    _organ_pad(sc, t0 + 16.0, [MID_PROG[i] for i in range(4, 12)],
               vel=40, lo=50, hi=69, vel_end=52)
    # Bars 1-4 stay lead + organ only (the probe's clean windows); the
    # halftime rhythm section returns at bar 5, bass in half notes.
    _halftime(sc, t0 + 16.0, 4)
    for i in range(4, 8):
        deg = MID_PROG[i]
        b = t0 + 4.0 * i
        sc.note(BASS, _root(deg), b, 1.8, 78, jt=2, jv=3)
        sc.note(BASS, _root(deg), b + 2.0, 0.9, 70, jt=2, jv=3)
        sc.note(BASS, _root(deg + 4), b + 3.0, 0.9, 72, jt=2, jv=3)
    # Bars 9-12: the build — chug returns, drums crescendo, then CUT.
    _chug(sc, t0 + 32.0, 4, [4, 6, 7, 7], vel=86)
    for i in range(4):
        deg = MID_PROG[8 + i]
        b = t0 + 32.0 + 4.0 * i
        for k in range(8):
            sc.note(BASS, _root(deg), b + 0.5 * k, 0.4,
                    84 + (6 if k % 4 == 0 else 0), jt=2, jv=3)
    _drums(sc, t0 + 32.0, 2, 0.75)
    for k in range(16):                          # bar 11: 16th snare ramp
        sc.hit(38, t0 + 40.0 + 0.25 * k, int(en.lerp(58, 96, k / 15)),
               jt=2, jv=4)
    for k in range(32):                          # bar 12: 32nd roll
        sc.note(DRUMS, 38, t0 + 44.0 + 0.125 * k, 0.11,
                int(en.lerp(76, 118, k / 31)), jt=1, jv=3)
    sc.hit(36, t0 + 40.0, 92, jt=2)
    sc.hit(36, t0 + 44.0, 98, jt=2)
    for i in range(2):                           # piano joins the build
        deg = MID_PROG[8 + 2 * i]
        tri = _triad(deg, octave=2)
        b = t0 + 32.0 + 8.0 * i
        for k in range(4):
            for p in tri:
                sc.note(PIANO, p, b + k * 2.0, 1.6,
                        int(en.lerp(66, 84, (2 * i + k / 2) / 3)),
                        jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 7.9)


def whisper(sc) -> None:
    """The POWER CUT: quiet but never silent.  Palm-mute ticks + a low
    organ pad + heartbeat kick carry continuous coverage; every note-on
    is velocity-capped (whisper_discipline oracle).  In the last bar the
    Leslie audibly spins up — the storm front coming back."""
    t0 = 336.0
    en.bend_range(sc, LEAD, 2, t0 + 2.0)         # restore after the wah
    sc.cc(LEAD, 74, 64, t0 + 2.0)
    sc.cc(KEYS, 11, 54, t0 - 0.02)               # organ ducks under
    sc.cc(KEYS, 1, 10, t0 - 0.01)
    # Low organ pad, hand-authored at the boundary (jt=0, T16 lesson).
    for p in (54, 57, 61):                       # F#m, low and dark
        sc.note(KEYS, p, t0, 15.9, 34, jt=0, jv=2)
    for p in (50, 54, 57):                       # D, darker still
        sc.note(KEYS, p, t0 + 16.0, 15.9, 32, jt=0, jv=2)
    # Palm-mute static ticks on the F# pedal.
    for i in range(8):
        b = t0 + 4.0 * i
        sc.note(GTR_M, 42, b, 0.18, 30, jt=0 if i == 0 else 2, jv=2)
        sc.note(GTR_M, 42, b + 0.5, 0.18, 26, jt=2, jv=2)
        if i >= 6:                               # ticks quicken slightly
            sc.note(GTR_M, 42, b + 2.0, 0.18, 30, jt=2, jv=2)
    # Bass heartbeats: i (4 bars), VI (3 bars), VII walking back up.
    for i in range(8):
        b = t0 + 4.0 * i
        p = 42 if i < 4 else (38 if i < 7 else 40)
        sc.note(BASS, p, b, 1.7, 34, jt=0 if i == 0 else 2, jv=2)
        sc.note(BASS, p, b + 2.0, 1.7, 30, jt=2, jv=2)
    # Heartbeat kit: kick, side-stick, pedal hat — all whisper-level.
    for i in range(8):
        b = t0 + 4.0 * i
        sc.hit(36, b, 34, jt=0 if i == 0 else 2, jv=2)
        sc.hit(37, b + 2.0, 30, jt=2, jv=2)
        sc.hit(44, b + 1.0, 24, jt=2, jv=2)
        sc.hit(44, b + 3.0, 22, jt=2, jv=2)
    # The rotor spins up under the whisper: the tell before the slam.
    en.leslie(sc, KEYS, t0 + 28.0, t0 + 32.0, 10, 112)


def final_chorus(sc) -> None:
    t0 = 368.0
    sc.cc(KEYS, 11, 127, t0)                     # power back ON
    # Bars 1-12: hook x2 + the post-chorus riff, everything up a notch.
    _chorus(sc, t0, vel_lift=8, lyrics=True, intensity=0.95, china=True,
            descant=76)
    # Over the riff's last bars the lead screams a legato run up...
    en.run(sc, LEAD, t0 + 46.0, FS3, _MODE, [3, 4, 5, 6, 7, 8, 9, 10],
           0.25, 84, 106, legato=True)
    # ...into bars 13-20: the DOUBLE hook (no riff tail this time).
    t1 = t0 + 48.0
    _piano_anthem(sc, t1, 8, CHORUS_PROG, vel=98)
    _open_eights(sc, t1, 8, CHORUS_PROG, vel=94)
    _power_anthem(sc, t1, 8, CHORUS_PROG, vel=108)
    _organ_pad(sc, t1, [CHORUS_PROG[i % 4] for i in range(8)], vel=68,
               lo=52, hi=64)
    for i in range(8):                           # the descant holds on
        top = _root(CHORUS_PROG[i % 4], octave=2)
        sc.note(KEYS, top, t1 + 4.0 * i, 3.9, 76, jt=0 if i == 0 else 3,
                jv=3)
    _lead_hook(sc, t1, 2, 108, lyrics=True)
    _bass_drive(sc, t1, 8, CHORUS_PROG, vel=110)
    _drums(sc, t1, 8, 0.95, crash_in=True, china=True)
    en.at_curve(sc, KEYS, [(t1 + 8.0, 20), (t1 + 16.0, 92),
                           (t1 + 24.0, 28)], step=0.5)
    en.echo_throw(sc, LEAD, t1 + 26.0, base=0, peak=78, release=3.0)


def outro(sc) -> None:
    t0 = 448.0
    _riff(sc, t0, 2, vel_scale=0.94)
    _bass_riff_lock(sc, t0, 2, vel=96)
    _drums(sc, t0, 4, 0.6, ride=True, fills=False)
    # The SLAM: one last F#5 chord, then the Leslie coda alone —
    # fast rotor, brake, slow chorale, fade (the audio probe's windows).
    _power(sc, GTR_D, 42, t0 + 16.0, 3.5, 100, jt=0)
    sc.note(BASS, 42, t0 + 16.0, 3.5, 96, jt=0, jv=0)
    sc.note(PIANO, 42, t0 + 16.0, 3.5, 74, jt=0, jv=3)
    sc.note(PIANO, 49, t0 + 16.0, 3.5, 66, jt=0, jv=3)
    sc.note(PIANO, 54, t0 + 16.0, 3.5, 70, jt=0, jv=3)
    en.sustain(sc, PIANO, t0 + 16.02, t0 + 22.0)
    sc.hit(49, t0 + 16.0, 108, jt=0)
    sc.hit(36, t0 + 16.0, 102, jt=0)
    for p in (54, 57, 61, 66):                   # the organ holds alone
        sc.note(KEYS, p, t0 + 16.0, 23.4, 52, jt=0, jv=2)
    sc.cc(KEYS, 1, 118, t0 + 16.0)               # fast rotor
    en.leslie(sc, KEYS, t0 + 28.0, t0 + 32.0, 118, 10)   # the brake
    en.expr_curve(sc, KEYS, [(t0 + 34.0, 108), (t0 + 39.4, 26)], step=0.5)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            whisper, final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 18, 28, 29, 30, 33}
CENTERED_CHANNELS = {PIANO, BASS, LEAD, KEYS, DRUMS}
NOTE_RANGES = {
    PIANO: (40, 92), GTR_M: (40, 62), GTR_D: (38, 68), BASS: (36, 64),
    LEAD: (52, 76), KEYS: (46, 79), DRUMS: (35, 82),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (220.0, 240.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.15),
    ("chorus2", ">=", "chorus1", 0.95),
    ("middle8", "<=", "chorus2", 0.8),
    ("whisper", "<=", "chorus2", 0.30),          # the drop, by the numbers
    ("final_chorus", ">=", "chorus1", 1.05),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("intro", "<=", "chorus1", 0.95),
    ("pre1", "<=", "chorus1", 1.0),
    ("outro", "<=", "final_chorus", 0.8),
]
LATE_CHANNELS = {GTR_M: 32.0, PIANO: 96.0, KEYS: 96.0, LEAD: 128.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 6), ("chorus1", 6), ("verse2", 6),
                 ("chorus2", 6), ("final_chorus", 6)],
    "hook": "chorus2",
}
# No CHOIR_SPEC: riff rock skips the choir (HLD D3 / §4 t05 brief).
FEATURES_EXPECTED = {
    "bend_range", "pitch_bend", "cc1_leslie", "cc68_legato", "cc74_wah",
    "cc64_sustain", "cc11_expression", "aftertouch", "cc94_echo",
    "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

_RIFF_WINDOWS = [(0.0, 16.0), (160.0, 176.0), (272.0, 288.0),
                 (448.0, 464.0)]
_WHISPER_WINDOW = (336.0, 368.0)
_WHISPER_CEIL = 48          # every note-on in the drop stays under this
_CHUG_WINDOWS = [("verse1", 32.0, 96.0), ("verse2", 176.0, 208.0)]


def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def _grouped_roots(sc, ch, t0, t1):
    """Chord-hit root sequence: min pitch per 0.25-beat onset group."""
    groups: dict[float, int] = {}
    for on, _off, p, _v in _spans(sc, ch):
        if t0 - 1e-9 <= on < t1:
            key = round((on - t0) * 4) / 4
            groups[key] = min(groups.get(key, 127), p)
    return [groups[k] for k in sorted(groups)]


def oracles(sc, info, spans):
    import verify

    # 1. riff_recur — the main riff recurs EXACTLY (grouped-root
    #    recompute) in both post-chorus windows and the outro.
    fails_riff: list[str] = []
    ref = _grouped_roots(sc, GTR_D, *_RIFF_WINDOWS[0])
    if len(ref) < 24:
        fails_riff.append(f"intro riff has only {len(ref)} chord-hits "
                          f"(expected 28)")
    for t0, t1 in _RIFF_WINDOWS[1:]:
        got = _grouped_roots(sc, GTR_D, t0, t1)
        if got != ref:
            fails_riff.append(f"riff at [{t0:.0f},{t1:.0f}) differs from "
                              f"the intro statement ({len(got)} vs "
                              f"{len(ref)} chord-hits)")

    # 2. whisper_discipline — the drop is quiet but NEVER silent: every
    #    note-on in the window under the ceiling, and continuous
    #    coverage (no gap > 1.5 beats), so the drop can't read as a gap.
    fails_wh: list[str] = []
    w0, w1 = _WHISPER_WINDOW
    notes = [(ch, on, off, v) for ch, on, off, _p, v
             in verify._all_notes(sc) if w0 - 0.02 <= on < w1 - 0.02]
    if len(notes) < 24:
        fails_wh.append(f"whisper too sparse ({len(notes)} note-ons)")
    loud = [(ch, on, v) for ch, on, _off, v in notes if v > _WHISPER_CEIL]
    for ch, on, v in loud[:4]:
        fails_wh.append(f"ch{ch} vel {v} at beat {on:.2f} breaks the "
                        f"whisper ceiling ({_WHISPER_CEIL})")
    horizon = w0
    for on, off in sorted((on, off) for _ch, on, off, _v in notes):
        if on - horizon > 1.5:
            fails_wh.append(f"whisper coverage gap {horizon:.2f}.."
                            f"{on:.2f}")
        horizon = max(horizon, min(off, w1))
    if w1 - horizon > 1.5:
        fails_wh.append(f"whisper coverage ends early at {horizon:.2f}")

    # 3. chug_gapped — the verse engine really rests: no palm-mute note
    #    longer than 0.5 beats, union duty <= 55%, >= 4 hit-groups/bar.
    fails_chug: list[str] = []
    for name, t0, t1 in _CHUG_WINDOWS:
        segs = [(on, off) for on, off, _p, _v in _spans(sc, GTR_M)
                if t0 - 1e-9 <= on < t1 - 1e-9]
        if not segs:
            fails_chug.append(f"'{name}': no palm-mute chug at all")
            continue
        long = [on for on, off in segs if off - on > 0.5]
        if long:
            fails_chug.append(f"'{name}': chug note at {min(long):.2f} "
                              f"longer than 0.5 beats")
        merged: list[list[float]] = []
        for on, off in sorted(segs):
            if merged and on <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], off)
            else:
                merged.append([on, off])
        duty = sum(b - a for a, b in merged) / (t1 - t0)
        if duty > 0.55:
            fails_chug.append(f"'{name}': chug duty {duty:.0%} (> 55% — "
                              f"not gapped)")
        groups = {round(on * 4) / 4 for on, _off in segs}
        bars = (t1 - t0) / 4.0
        if len(groups) / bars < 4.0:
            fails_chug.append(f"'{name}': {len(groups) / bars:.1f} "
                              f"hit-groups/bar (< 4)")

    return [("riff_recur", fails_riff),
            ("whisper_discipline", fails_wh),
            ("chug_gapped", fails_chug)]


# ---------------------------------------------------------------------------
# Audio oracles — measure-then-assert (HLD §6.2); thresholds FROZEN
# at the phase-D assembled-album freeze (2026.07.11).  Measured 2026.07.11 on
# this worktree's ferrosintesis 0.13.x per-track render:
#   chorus lift +2.96 dB, drop depth +19.58 dB, re-entry slam +20.49 dB,
#   Leslie AM-flux fast/slow 1.58, wah band-fraction bright/dark 5.85
#   (weakest single bar 3.45).  Pins sit >= 1.5 dB / >= 25% under those.
# ---------------------------------------------------------------------------

_LIFT_DB = 1.4      # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): final chorus RMS over verse-1 RMS
_DROP_DB = 14.0     # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): whisper core >= this far below chorus 2
_SLAM_DB = 14.0     # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): first final-chorus bar over the drop
_LESLIE_FLUX = 1.2  # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): fast-rotor AM flux / slow-rotor flux
_WAH_RATIO = 2.0    # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): bright-half band fraction / dark-half


def _mono(ctx, i0: int, i1: int) -> list[float]:
    return [(a + b) * 0.5 for a, b in zip(ctx.l[i0:i1], ctx.r[i0:i1])]


def _fft(x: list[complex]) -> list[complex]:
    n = len(x)
    if n == 1:
        return x
    ev, od = _fft(x[0::2]), _fft(x[1::2])
    out = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * od[k]
        out[k], out[k + n // 2] = ev[k] + t, ev[k] - t
    return out


def _band_frac(ctx, b0: float, b1: float,
               flo: float = 1500.0, fhi: float = 6000.0) -> float:
    """Fraction of spectral energy inside [flo, fhi] Hz — the band the
    wah's dark half (cutoff ~750 Hz) crushes and its bright half
    (~7 kHz) passes.  A true band fraction is note- and vibrato-proof
    where a spectral-tilt proxy is not (measured 2026.07.11)."""
    i0, i1 = ctx.bar_window(b0, b1)
    m = _mono(ctx, i0, i1)
    n = 1
    while n < len(m):
        n *= 2
    spec = _fft([complex(v, 0.0) for v in m] + [0j] * (n - len(m)))
    tot = hf = 0.0
    for k in range(1, n // 2):
        p = abs(spec[k]) ** 2
        tot += p
        f = k * ctx.sample_rate / n
        if flo <= f <= fhi:
            hf += p
    return hf / tot if tot > 0 else 0.0


def _am_flux(ctx, b0: float, b1: float) -> float:
    """Amplitude-modulation flux: mean |delta frame-RMS| / mean frame-RMS
    (40 ms frames, 20 ms hop) — the Leslie rotor speed fingerprint."""
    i0, i1 = ctx.bar_window(b0, b1)
    m = _mono(ctx, i0, i1)
    fr, hp = int(ctx.sample_rate * 0.04), int(ctx.sample_rate * 0.02)
    frames: list[float] = []
    k = 0
    while k + fr <= len(m):
        seg = m[k:k + fr]
        frames.append(math.sqrt(sum(x * x for x in seg) / fr))
        k += hp
    if len(frames) < 3:
        return 0.0
    mean = sum(frames) / len(frames)
    if mean <= 0:
        return 0.0
    return sum(abs(a - b) for a, b in zip(frames[1:], frames)) \
        / (len(frames) - 1) / mean


def audio_checks(ctx):
    # 1. Chorus lift: the final chorus over verse 1.
    fails_lift: list[str] = []
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(40.0, 88.0)))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(368.0, 440.0)))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # 2+3. The drop lands AND the re-entry slams (HLD §6.2).
    fails_drop: list[str] = []
    fails_slam: list[str] = []
    chorus2 = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(244.0, 284.0)))
    drop = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(340.0, 364.0)))
    slam = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(368.0, 372.0)))
    if drop > chorus2 - _DROP_DB:
        fails_drop.append(f"drop {drop:.1f} dB not <= chorus2 "
                          f"{chorus2:.1f} dB - {_DROP_DB}")
    if slam < drop + _SLAM_DB:
        fails_slam.append(f"re-entry {slam:.1f} dB not >= drop "
                          f"{drop:.1f} dB + {_SLAM_DB}")

    # 4. Leslie audibility (headline #1): the outro coda holds ONE organ
    #    chord through a fast-rotor window then a slow-chorale window;
    #    the fast rotor must show more amplitude-modulation flux.  The
    #    fast window opens at 470 so the beat-464 crash tail (a decaying
    #    broadband slope that fakes flux) has died first.
    fails_les: list[str] = []
    fast = _am_flux(ctx, 470.0, 476.0)
    slow = _am_flux(ctx, 480.0, 486.0)
    if slow <= 0 or fast < slow * _LESLIE_FLUX:
        fails_les.append(f"Leslie AM flux fast {fast:.4f} not >= "
                         f"{_LESLIE_FLUX} x slow {slow:.4f}")

    # 5. Wah audibility (headline #2): CC74 LFO at 0.25 cycles/beat.
    #    Middle-8 bars 1-4 chop identical eighth-note picks with nothing
    #    else underneath, so each bar compares three bright-half picks
    #    against three dark-half picks of the same pitch and rhythm.
    fails_wah: list[str] = []
    highs, lows = [], []
    for k in range(4):
        b = 288.0 + 4.0 * k
        highs.append(_band_frac(ctx, b + 0.45, b + 1.95))
        lows.append(_band_frac(ctx, b + 2.45, b + 3.95))
    hi = sum(highs) / len(highs)
    lo = sum(lows) / len(lows)
    if lo <= 0 or hi < lo * _WAH_RATIO:
        fails_wah.append(f"wah 1.5-6 kHz fraction bright {hi:.4f} not >= "
                         f"{_WAH_RATIO} x dark {lo:.4f}")

    return [("chorus_lift", fails_lift),
            ("drop_depth", fails_drop),
            ("reentry_slam", fails_slam),
            ("leslie_flux", fails_les),
            ("wah_flux", fails_wah)]
