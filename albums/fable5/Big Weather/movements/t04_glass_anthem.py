"""t04_glass_anthem.py — "Glass Anthem" (Big Weather, track 4).

The album's power ballad and its biggest orchestral build.  C major at
100 BPM with a genuinely rubato solo-piano intro (the tempo map breathes
86->93->88->94->90 before locking to 100 at verse 1), then ONE long
build: a choir wisp haunts the nearly-solo-piano first verse (CC67 una
corda, CC64 pedalling throughout); bass and a drum heartbeat arrive at
the pre-chorus; clean guitar and the voice-like lead (GM85) sing the
chorus; EP pads colour verse 2; drive guitar and a second choir layer
lift chorus 2; strings slip in under the pulled-back middle 8 (92 BPM,
CC11 swells); and the final chorus KEY-LIFTS C->D (hard transpose, no
bends — keysig meta at beat 296) with brass aftertouch growls, timpani
rolls, a third choir layer and rock organ w/ Leslie all arriving at
once.  The outro restates the intro piano motif IN D — the same prayer
in a brighter room (oracle: motif_recap, recomputed not copied).

Oracle-pinned claims: the active-layer count grows monotonically along
the song's spine (layer_build); the outro piano equals the intro motif
lifted +2 (motif_recap); the final-chorus lead hook equals the chorus-1
hook lifted +2 (hook_lift).  Audio: the album's LARGEST chorus lift
(final chorus over verse 1) and the RMS rise across the beat-296
orchestra entry.

Form (HLD §4, full grammar + rubato intro):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 | middle8 |
  final_chorus (24 bars, C->D) | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 4
TITLE = "Glass Anthem"
FILE = "04 - Glass Anthem.mid"
SEED = 20260704

BPM = 100.0

# Channels (HLD §3).
PIANO, GTR_C, GTR_D, BASS = 0, 1, 2, 3
AAH, OOH, LEAD, KEYS = 4, 5, 6, 7
STRINGS, DRUMS, BRASS, TIMP = 8, 9, 10, 11
EH = 12

_SECTIONS = [
    ("intro",          0.0,  40.0),
    ("verse1",        40.0, 104.0),
    ("pre1",         104.0, 120.0),
    ("chorus1",      120.0, 152.0),
    ("verse2",       152.0, 200.0),
    ("pre2",         200.0, 216.0),
    ("chorus2",      216.0, 264.0),
    ("middle8",      264.0, 296.0),
    ("final_chorus", 296.0, 392.0),
    ("outro",        392.0, 432.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    # The rubato intro BREATHES (86->93->88->94->90), locks to 100 at
    # verse 1, pulls back to 92 for the middle 8, returns to 100 for the
    # final chorus, and eases down through the outro.  Real, audible
    # moves (5-10 BPM), not +-1 BPM theatre.
    tempo_map=[(0.0, 86.0), (8.0, 93.0), (16.0, 88.0), (24.0, 94.0),
               (32.0, 90.0), (40.0, 100.0), (264.0, 92.0),
               (296.0, 100.0), (416.0, 94.0), (424.0, 88.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0), (296.0, 2, 0)],   # C major -> D major lift
    channels=[
        (PIANO,   "piano",        0, 100, 64, 55),
        (GTR_C,   "clean guitar", 25,  92, 48, 45),
        (GTR_D,   "drive guitar", 29,  90, 80, 35),
        (BASS,    "bass guitar",  33, 105, 64, 25),
        (AAH,     "choir aah",    52,  88, 64, 70),
        (OOH,     "choir ooh",    53,  84, 64, 70),
        (LEAD,    "voice lead",   85,  94, 64, 50),
        (KEYS,    "ep / organ",    4,  82, 64, 45),
        (STRINGS, "strings",      48,  88, 64, 65),
        (DRUMS,   "drums",         0, 108, 64, 45),
        (BRASS,   "brass",        61,  92, 64, 45),
        (TIMP,    "timpani",      47,  96, 64, 60),
        (EH,      "choir eh",     54,  82, 64, 70),
    ],
    program_changes=[
        (GTR_D, 296.0, 30),     # overdrive -> full distortion at the lift
        (KEYS,  296.0, 16),     # EP -> drawbar organ (Leslie now honored)
    ],
)

# ---------------------------------------------------------------------------
# Harmony — C major, lifting to D for the final chorus + outro.
# The iii chord (Em) is the track's "glass" colour: it tints the verse
# and middle-8 where t01 leaned on vi-IV-V shapes.
# ---------------------------------------------------------------------------

C2, C4 = en.n("C2"), en.n("C4")
_MODE = "ionian"
LIFT = 2                       # semitones: the C -> D final-chorus lift

VERSE_PROG = [1, 3, 6, 4]              # C   Em  Am  F
PRE_PROG = [2, 4, 5, 5]                # Dm  F   G   G (dominant pedal)
CHORUS_PROG = [1, 4, 6, 5]             # C   F   Am  G
MID_PROG = [6, 3, 4, 1, 6, 3, 2, 5]    # Am Em F C | Am Em Dm G
CODA_PROG = [4, 5, 6, 5, 4, 5, 1, 1]   # the augmented tag


def _root(deg: int, octave: int = 0, key: int = 0) -> int:
    return en.pitch(C2 + key, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1, key: int = 0) -> list[int]:
    return [p + 12 * octave for p in en.triad(C2 + key, _MODE, deg)]


def _lh_root(deg: int, key: int = 0) -> int:
    """Left-hand piano root: keep it in the F2..E3 pocket."""
    p = _root(deg, 0, key)
    return p + 12 if p < 41 else p


def _bp(deg: int, key: int = 0) -> int:
    """Bass pitch for a scale degree, never below C2 (MIDI 36)."""
    p = _root(deg, 0, key)
    return p + 12 if p < 36 else p


# ---------------------------------------------------------------------------
# The MOTIF — the rubato intro piano statement (16 beats over C G Am F),
# restated in the outro lifted to D (oracle: motif_recap).  jt=0
# everywhere: the recurrence is pinned note-for-note.
# RH: (beat, degree-from-tonic4, dur, vel).
# ---------------------------------------------------------------------------

_MOTIF_RH = [
    (0.0, 5, 1.5, 76), (1.5, 3, 0.5, 66), (2.0, 5, 1.0, 72),
    (3.0, 8, 1.0, 78),
    (4.0, 7, 1.5, 76), (5.5, 5, 0.5, 66), (6.0, 9, 2.0, 80),
    (8.0, 8, 1.5, 76), (9.5, 7, 0.5, 68), (10.0, 6, 1.0, 72),
    (11.0, 10, 1.0, 82),
    (12.0, 6, 1.0, 74), (13.0, 5, 1.0, 70), (14.0, 3, 2.0, 68),
]
_MOTIF_BARS = [1, 5, 6, 4]             # C  G  Am  F


def _motif(sc, t0: float, key: int = 0, scale: float = 1.0) -> None:
    """One 16-beat motif statement: RH bell line + LH broken octaves,
    fully deterministic (jt=0, jv=0) so the recap oracle can pin it."""
    for beat, deg, dur, vel in _MOTIF_RH:
        sc.note(PIANO, en.pitch(C4 + key, _MODE, deg), t0 + beat, dur,
                int(round(vel * scale)), jt=0, jv=0)
    for i, deg in enumerate(_MOTIF_BARS):
        b = t0 + 4.0 * i
        r = _lh_root(deg, key)
        sc.note(PIANO, r, b, 1.95, int(round(64 * scale)), jt=0, jv=0)
        sc.note(PIANO, r + 7, b + 2.0, 0.95, int(round(56 * scale)),
                jt=0, jv=0)
        sc.note(PIANO, r + 12, b + 3.0, 0.95, int(round(58 * scale)),
                jt=0, jv=0)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


# The verse TUNE — the piano is the singer in the verses (RH top line,
# 32 beats over VERSE_PROG x2).
_VERSE_TUNE = [
    (5, 0.0, 1.5), (6, 1.5, 0.5), (5, 2.0, 1.0), (3, 3.0, 1.0),
    (7, 4.0, 1.5), (5, 5.5, 0.5), (7, 6.0, 1.0), (9, 7.0, 1.0),
    (8, 8.0, 1.5), (7, 9.5, 0.5), (6, 10.0, 2.0),
    (6, 12.0, 1.0), (5, 13.0, 1.0), (4, 14.0, 0.5), (3, 14.5, 1.5),
    (5, 16.0, 1.5), (6, 17.5, 0.5), (8, 18.0, 2.0),
    (7, 20.0, 1.0), (9, 21.0, 1.0), (10, 22.0, 2.0),
    (10, 24.0, 1.5), (9, 25.5, 0.5), (8, 26.0, 2.0),
    (6, 28.0, 1.0), (5, 29.0, 0.75), (4, 29.75, 0.25), (5, 30.0, 2.0),
]

# The chorus HOOK — 16 beats over C F Am G, sung by the voice lead
# (GM85) and lifted +2 in the final chorus (oracle: hook_lift).
_HOOK = [
    (3, 0.0, 0.75), (4, 0.75, 0.25), (5, 1.0, 2.5),
    (6, 4.0, 0.75), (5, 4.75, 0.25), (6, 5.0, 1.0), (8, 6.0, 1.75),
    (10, 8.0, 1.0), (9, 9.0, 0.5), (8, 9.5, 0.5), (9, 10.0, 1.75),
    (7, 12.0, 1.0), (6, 13.0, 0.5), (5, 13.5, 0.5), (4, 14.0, 0.75),
    (3, 14.75, 1.0),
]
_HOOK_LYRICS = ["glass anthem", "hold the light", "through the storm",
                "we shine"]

# The final-chorus bass HOOK (16 beats over D G Bm A, degrees from D2).
_BASS_HOOK = [
    (8, 0.0, 0.7), (9, 0.75, 0.25), (10, 1.0, 0.95), (8, 2.0, 0.45),
    (5, 2.5, 0.45), (6, 3.0, 0.45), (7, 3.5, 0.45),
    (4, 4.0, 0.7), (5, 4.75, 0.25), (6, 5.0, 0.95), (8, 6.0, 0.45),
    (6, 6.5, 0.45), (5, 7.0, 0.45), (4, 7.5, 0.45),
    (6, 8.0, 0.7), (7, 8.75, 0.25), (8, 9.0, 0.95), (10, 10.0, 0.7),
    (8, 10.75, 0.25), (6, 11.0, 0.45), (7, 11.5, 0.45),
    (5, 12.0, 0.7), (6, 12.75, 0.25), (7, 13.0, 0.95), (9, 14.0, 0.45),
    (7, 14.5, 0.45), (6, 15.0, 0.45), (2, 15.5, 0.45),
]


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _piano_verse(sc, t0: float, bars: int, prog: list[int], vel: int = 52,
                 tune_from: int | None = None, key: int = 0) -> None:
    """Verse piano: LH long root, RH gentle broken-triad quarters, CC64
    pedalled; from `tune_from` bars in, the RH sings the verse tune."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2, key=key)
        sc.note(PIANO, _lh_root(deg, key), b, 3.8, vel + 10,
                jt=0 if i == 0 else 3, jv=3)
        for beat, ni in ((1.0, 0), (2.0, 1), (3.0, 2), (3.5, 1)):
            sc.note(PIANO, tri[ni], b + beat, 0.9, vel - 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    if tune_from is not None:
        en.line(sc, PIANO, t0 + 4.0 * tune_from, C4 + key, _MODE,
                _VERSE_TUNE, vel + 18, octave=1, jt=2, jv=3)


def _piano_pre(sc, t0: float, bars: int, prog: list[int],
               vel0: int = 66, vel1: int = 84, key: int = 0) -> None:
    """Pre-chorus piano: RH triad quarters with a section-long
    crescendo over LH octave halves."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2, key=key)
        r = _lh_root(deg, key)
        v = int(round(en.lerp(vel0, vel1, i / max(1, bars - 1))))
        sc.note(PIANO, r, b, 1.9, v + 6, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, v + 2, jt=3, jv=3)
        for k in range(4):
            for p in tri:
                sc.note(PIANO, p, b + k, 0.9, v - 6, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_pulse(sc, t0: float, bars: int, prog: list[int], vel: int = 86,
                 key: int = 0) -> None:
    """Chorus piano: the power-ballad engine — RH triad eighths pulsing
    all bar, LH root/octave halves, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2, key=key)
        r = _lh_root(deg, key)
        sc.note(PIANO, r, b, 1.9, vel + 8, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, vel + 4, jt=3, jv=3)
        for k in range(8):
            accent = 8 if k in (0, 4) else 0
            for p in tri:
                sc.note(PIANO, p, b + 0.5 * k, 0.45, vel - 8 + accent,
                        jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_coda(sc, t0: float, bars: int, prog: list[int], vel: int = 94,
                key: int = 0) -> None:
    """Coda piano: broad block chords, half-note LH, octave crown."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2, key=key)
        r = _lh_root(deg, key)
        sc.note(PIANO, r, b, 1.95, vel + 6, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r, b + 2.0, 1.95, vel + 2, jt=3, jv=3)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 5, jt=3, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.0, 0.9, vel + 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _gtr_strum(sc, t0: float, bars: int, prog: list[int], vel: int = 76,
               key: int = 0) -> None:
    """Clean guitar: broad add9 strums (down, down, up, down)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1, key=key)
        chord = tri + [tri[0] + 14]              # add9 shimmer on top
        for beat, dur, down, dv in ((0.0, 1.4, True, 0),
                                    (1.5, 0.9, True, -8),
                                    (2.5, 0.45, False, -14),
                                    (3.0, 1.4, True, -4)):
            en.strum(sc, GTR_C, chord, b + beat, dur, vel + dv,
                     spread=0.03, down=down)


def _gtr_pick(sc, t0: float, bars: int, prog: list[int], vel: int = 58,
              key: int = 0) -> None:
    """Clean guitar: picked eighth arpeggios (verse texture)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1, key=key)
        seq = [tri[0], tri[2], tri[1] + 12, tri[2] + 12,
               tri[1] + 12, tri[2], tri[0] + 12, tri[2]]
        for k, p in enumerate(seq):
            sc.note(GTR_C, p, b + 0.5 * k, 0.42, vel, jt=3, jv=4)


def _power(sc, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    """Root + fifth + octave on the drive guitar."""
    for i, off in enumerate((0, 7, 12)):
        sc.note(GTR_D, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _gtr_root(deg: int, key: int = 0) -> int:
    p = _root(deg, 0, key)
    return p + 12 if p < 41 else p


def _power_bed(sc, t0: float, bars: int, prog: list[int], vel: int = 96,
               key: int = 0) -> None:
    """Drive guitar: long power chords, pushes on 3 and the &-of-3."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _gtr_root(prog[i % len(prog)], key)
        _power(sc, r, b, 2.4, vel, jt=0 if i == 0 else 2)
        _power(sc, r, b + 2.5, 0.45, vel - 10, jt=2)
        _power(sc, r, b + 3.5, 0.45, vel - 6, jt=2)


def _bass_walk(sc, t0: float, prog: list[int], reps: int = 1,
               vel: int = 94, key: int = 0) -> None:
    """Melodic bass: root anchor, then a diatonic walk down from the
    fifth with a stepwise approach into every next root."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        nd = seq[(i + 1) % len(seq)]
        appr = nd - 1 if _bp(nd - 1, key) >= 38 else nd + 1
        sc.note(BASS, _bp(deg, key), b, 1.45, vel,
                jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, _bp(deg + 4, key), b + 1.5, 0.45, vel - 8,
                jt=2, jv=3)
        sc.note(BASS, _bp(deg + 3, key), b + 2.0, 0.45, vel - 12,
                jt=2, jv=3)
        sc.note(BASS, _bp(deg + 2, key), b + 2.5, 0.45, vel - 10,
                jt=2, jv=3)
        sc.note(BASS, _bp(deg + 1, key), b + 3.0, 0.45, vel - 14,
                jt=2, jv=3)
        sc.note(BASS, _bp(appr, key), b + 3.5, 0.45, vel - 6,
                jt=2, jv=3)


def _bass_long(sc, t0: float, prog: list[int], vel: int = 76,
               key: int = 0) -> None:
    """Middle-8 bass: breathing long roots with a stepwise pickup."""
    for i, deg in enumerate(prog):
        b = t0 + 4.0 * i
        nd = prog[(i + 1) % len(prog)]
        appr = nd - 1 if _bp(nd - 1, key) >= 38 else nd + 1
        sc.note(BASS, _bp(deg, key), b, 3.3, vel,
                jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, _bp(appr, key), b + 3.5, 0.45, vel - 10, jt=2, jv=3)


def _kit(sc, t0: float, bars: int, x: float, *, ride: bool = False,
         china: bool = False, crash_in: bool = False, fills: bool = True,
         ghost: bool = True) -> None:
    """The ballad kit groove.  x 0..1 scales velocity and busy-ness."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(70, 106, x)))
        fill_bar = fills and (i == bars - 1 or i % 8 == 7)
        if crash_in and i == 0:
            sc.hit(49, b, min(122, v + 16), jt=0)
        if china and i % 4 == 2:
            sc.hit(52, b, v + 4, jt=2)
        sc.hit(36, b, v + 8, jt=0 if i == 0 else 2)
        sc.hit(36, b + 1.5, v - 2, jt=2)
        if x > 0.55:
            sc.hit(36, b + 2.5, v, jt=2)
        sc.hit(38, b + 1.0, v + 10, jt=2, jv=4)
        sc.hit(38, b + 3.0, v + 10, jt=2, jv=4)
        if ghost and x < 0.9:
            sc.hit(38, b + 1.75, max(16, v - 48), jt=3, jv=6)
            sc.hit(38, b + 3.75, max(16, v - 52), jt=3, jv=6)
        key = 51 if ride else 42
        for k in range(8):
            if fill_bar and k >= 5:
                continue
            hv = v - (8 if k % 2 == 0 else 24)
            sc.hit(key, b + 0.5 * k, max(20, hv), jt=2, jv=5)
        if ride and i % 2 == 1:
            sc.hit(53, b + 2.0, v - 8, jt=2)
        if not ride and not fill_bar and i % 4 == 3:
            sc.hit(46, b + 3.5, v - 16, jt=2)
        if fill_bar:
            toms = [50, 50, 48, 47, 45, 43]
            for k, key2 in enumerate(toms):
                sc.hit(key2, b + 2.5 + 0.25 * k,
                       int(en.lerp(v - 16, v + 14, k / 5)), jt=2)


def _heartbeat(sc, t0: float, bars: int, vel: int = 64,
               hats: bool = False) -> None:
    """Sparse kick + side-stick heartbeat (pre-chorus 1, middle 8)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        sc.hit(36, b, vel + 6, jt=0 if i == 0 else 2)
        sc.hit(37, b + 2.0, vel - 6, jt=2)
        if hats:
            for k in range(4):
                sc.hit(42, b + k, max(20, vel - 26), jt=2, jv=4)


def _choir_pad(sc, ch, t0: float, bars: int, prog: list[int], vel: int,
               key: int = 0, lo: int = 57, hi: int = 79,
               size: int = 3) -> None:
    chords = [en.triad(C4 - 12 + key, _MODE, prog[i % len(prog)])
              for i in range(bars)]
    en.pad_block(sc, ch, t0, chords, 4.0, size=size, lo=lo, hi=hi,
                 vel=vel, legato=0.0)


def _ooh_line(sc, t0: float, tones: list[int], vel: int,
              key: int = 0) -> None:
    """Choir ooh: one long counter-tone every two bars, jt=0."""
    for i, deg in enumerate(tones):
        sc.note(OOH, en.pitch(C4 + key, _MODE, deg), t0 + 8.0 * i, 7.5,
                vel, jt=0, jv=3)


def _strings_bed(sc, t0: float, bars: int, prog: list[int], vel: int,
                 key: int = 0, lo: int = 48, hi: int = 79,
                 swell: list[tuple[float, int]] | None = None) -> None:
    chords = [en.triad(C4 - 12 + key, _MODE, prog[i % len(prog)])
              for i in range(bars)]
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=lo, hi=hi,
                 vel=vel, legato=0.0)
    if swell:
        en.expr_curve(sc, STRINGS, swell, step=1.0)


def _brass_swells(sc, t0: float, bars: int, prog: list[int], vel: int = 90,
                  key: int = 0) -> None:
    """Held section swells (aftertouch growls) alternating with pushes."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1, key=key)
        if i % 2 == 0:
            for p in tri:
                sc.note(BRASS, p, b, 3.6, vel - 8, jt=0, jv=3)
            en.at_curve(sc, BRASS, [(b, 18), (b + 2.5, 92), (b + 3.7, 28)],
                        step=0.5)
        else:
            for beat in (1.5, 3.5):
                for p in tri:
                    sc.note(BRASS, p, b + beat, 0.4, vel, jt=0, jv=3)
            sc.note(BRASS, tri[0] + 12, b + 3.5, 0.4, vel + 4, jt=0, jv=3)


def _timp(sc, t0: float, bars: int, key: int = 0, vel: int = 88) -> None:
    """Anchor strokes on the tonic; crescendo rolls on the dominant."""
    tonic, dom = _bp(1, key), _bp(5, key)
    for i in range(bars):
        b = t0 + 4.0 * i
        if i % 4 == 0:
            sc.note(TIMP, tonic, b, 1.2, vel + 8, jt=0, jv=3)
        if i % 4 == 3:
            for k in range(8):
                sc.note(TIMP, dom, b + 2.0 + 0.25 * k, 0.22,
                        int(en.lerp(vel - 30, vel + 12, k / 7)),
                        jt=0 if k == 0 else 2, jv=4)


def _lead_hook(sc, t0: float, reps: int, vel: int, key: int = 0, *,
               lyrics: bool = False) -> None:
    """The chorus hook on the voice lead; CC1 vibrato blooms on holds."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, C4 + key, _MODE, _HOOK, vel, jt=0, jv=0,
                gate=0.98)
        for deg, start, dur in _HOOK:
            if dur >= 1.5:
                b = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(b + 0.3, 0), (b + dur * 0.6, 56),
                             (b + dur, 10)], step=0.15)
        if lyrics and r == 0:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    """Rubato solo piano: the motif twice, then a rising turn."""
    _motif(sc, 0.0, key=0, scale=0.92)
    _motif(sc, 16.0, key=0, scale=1.0)
    # The turn: two bars of F -> G, RH climbing with a crescendo.
    for j, (deg, b0) in enumerate(((4, 32.0), (5, 36.0))):
        r = _lh_root(deg, 0)
        sc.note(PIANO, r, b0, 3.8, 62 + 6 * j, jt=0, jv=0)
        sc.note(PIANO, r + 7, b0 + 2.0, 1.8, 56 + 6 * j, jt=2, jv=3)
        en.sustain(sc, PIANO, b0 + 0.02, b0 + 3.9)
    en.line(sc, PIANO, 32.0, C4, _MODE,
            [(4, 0.0, 1.0), (5, 1.0, 1.0), (6, 2.0, 1.0), (8, 3.0, 1.0),
             (5, 4.0, 1.0), (7, 5.0, 1.0), (9, 6.0, 1.0), (10, 7.0, 0.95)],
            60, vel_end=86, jt=2, jv=2)


def verse1(sc) -> None:
    """Nearly solo piano (una corda) + the choir wisp."""
    t0 = 40.0
    en.soft_pedal(sc, PIANO, t0, t0 + 62.0)
    _piano_verse(sc, t0, 16, VERSE_PROG, vel=52, tune_from=8)
    # The wisp: one soft aah tone every two bars (E4/G4 — the glass
    # colour held over C, Em, Am and Fmaj7 alike).
    for i in range(8):
        deg = 3 if i % 2 == 0 else 5
        sc.note(AAH, en.pitch(C4, _MODE, deg), t0 + 8.0 * i, 7.5,
                44, jt=0, jv=2)


def pre1(sc) -> None:
    """Bass and the drum heartbeat arrive; the piano starts to climb."""
    t0 = 104.0
    _piano_pre(sc, t0, 4, PRE_PROG, vel0=64, vel1=82)
    _bass_walk(sc, t0, PRE_PROG, vel=92)
    _heartbeat(sc, t0, 4, vel=66, hats=True)
    for i, deg in enumerate((2, 5)):
        sc.note(AAH, en.pitch(C4, _MODE, deg), t0 + 8.0 * i, 7.5, 48,
                jt=0, jv=2)


def chorus1(sc) -> None:
    """Clean guitar and the voice lead sing the first chorus."""
    t0 = 120.0
    _piano_pulse(sc, t0, 8, CHORUS_PROG, vel=84)
    _gtr_strum(sc, t0, 8, CHORUS_PROG, vel=74)
    _bass_walk(sc, t0, CHORUS_PROG, reps=2, vel=98)
    _kit(sc, t0, 8, 0.68, crash_in=True)
    _lead_hook(sc, t0, 2, 94, lyrics=True)
    _choir_pad(sc, AAH, t0, 8, CHORUS_PROG, vel=50)


def verse2(sc) -> None:
    """Everyone stays; EP pads join.  Piano keeps the tune."""
    t0 = 152.0
    en.soft_pedal(sc, PIANO, t0, t0 + 46.0)
    _piano_verse(sc, t0, 12, VERSE_PROG, vel=56, tune_from=4)
    _gtr_pick(sc, t0, 12, VERSE_PROG, vel=56)
    _bass_walk(sc, t0, VERSE_PROG, reps=3, vel=86)
    _kit(sc, t0, 12, 0.45, fills=False)
    for i in range(6):
        deg = 3 if i % 2 == 0 else 2
        sc.note(AAH, en.pitch(C4, _MODE, deg), t0 + 8.0 * i, 7.5, 42,
                jt=0, jv=2)
    chords = [en.triad(C4 - 12, _MODE, VERSE_PROG[i % 4])
              for i in range(12)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=44, legato=0.0)
    # Soft lead answers at the back of each 8-bar phrase.
    for b0 in (t0 + 12.0, t0 + 28.0, t0 + 44.0):
        en.line(sc, LEAD, b0, C4, _MODE,
                [(3, 0.0, 0.5), (4, 0.5, 0.5), (5, 1.0, 1.5)], 58,
                jt=2, jv=3)


def pre2(sc) -> None:
    """The second climb, now with the kit and EP underneath."""
    t0 = 200.0
    _piano_pre(sc, t0, 4, PRE_PROG, vel0=70, vel1=88)
    _gtr_pick(sc, t0, 4, PRE_PROG, vel=62)
    _bass_walk(sc, t0, PRE_PROG, vel=98)
    _kit(sc, t0, 4, 0.6, fills=True)
    # The lead leans in early — a rising pickup into chorus 2.
    en.line(sc, LEAD, t0 + 12.0, C4, _MODE,
            [(2, 0.0, 1.0), (3, 1.0, 1.0), (4, 2.0, 1.9)], 72, jt=2, jv=3)
    chords = [en.triad(C4 - 12, _MODE, PRE_PROG[i % 4]) for i in range(4)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=48, legato=0.0)
    for i, deg in enumerate((2, 5)):
        sc.note(AAH, en.pitch(C4, _MODE, deg), t0 + 8.0 * i, 7.5, 52,
                jt=0, jv=2)


def chorus2(sc) -> None:
    """Drive guitar and the layered choir lift the second chorus."""
    t0 = 216.0
    _piano_pulse(sc, t0, 12, CHORUS_PROG, vel=87)
    _gtr_strum(sc, t0, 12, CHORUS_PROG, vel=77)
    _power_bed(sc, t0, 12, CHORUS_PROG, vel=94)
    _bass_walk(sc, t0, CHORUS_PROG, reps=3, vel=100)
    _kit(sc, t0, 12, 0.8, ride=True, crash_in=True)
    _lead_hook(sc, t0, 3, 97, lyrics=True)
    _choir_pad(sc, AAH, t0, 12, CHORUS_PROG, vel=56)
    _ooh_line(sc, t0, [5, 4, 3, 2, 3, 4], 52)
    en.vowel_curve(sc, AAH, [(t0, 40), (t0 + 24.0, 86), (t0 + 46.0, 68)],
                   step=2.0)
    chords = [en.triad(C4 - 12, _MODE, CHORUS_PROG[i % 4])
              for i in range(12)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=50, legato=0.0)


def middle8(sc) -> None:
    """The hush at 92 BPM: pedalled piano arps, strings slip in pp with
    CC11 swells, the choir hums, and a timpani roll lifts the door."""
    t0 = 264.0
    en.soft_pedal(sc, PIANO, t0, t0 + 30.0)
    for i in range(8):
        b = t0 + 4.0 * i
        tri1 = _triad(MID_PROG[i], octave=1)
        tri2 = _triad(MID_PROG[i], octave=2)
        seq = [tri1[0], tri1[2], tri2[0], tri2[1], tri2[2], tri2[1],
               tri2[0], tri1[2]]
        for k, p in enumerate(seq):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 54,
                    jt=0 if (i == 0 and k == 0) else 3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    _strings_bed(sc, t0, 8, MID_PROG, vel=48,
                 swell=[(t0, 38), (t0 + 8.0, 72), (t0 + 16.0, 50),
                        (t0 + 24.0, 84), (t0 + 31.0, 60)])
    _choir_pad(sc, AAH, t0, 8, MID_PROG, vel=46)
    _ooh_line(sc, t0, [3, 2, 1, 2], 44)
    en.vowel_curve(sc, OOH, [(t0, 28), (t0 + 24.0, 58), (t0 + 30.0, 44)],
                   step=2.0)
    _bass_long(sc, t0, MID_PROG, vel=72)
    _heartbeat(sc, t0, 8, vel=58)
    # The dominant-of-D timpani roll opens the final door (TIMP gates
    # in at 292; jt=0 on the first stroke).
    for k in range(16):
        sc.note(TIMP, _bp(5, LIFT), 292.0 + 0.25 * k, 0.22,
                int(en.lerp(40, 96, k / 15)), jt=0 if k == 0 else 2, jv=3)


def final_chorus(sc) -> None:
    """The lift: D major, all thirteen channels, the album's biggest
    orchestral arrival — brass, timpani, third choir layer, organ."""
    t0 = 296.0
    k = LIFT
    _piano_pulse(sc, t0, 16, CHORUS_PROG, vel=92, key=k)
    _gtr_strum(sc, t0, 16, CHORUS_PROG, vel=80, key=k)
    _power_bed(sc, t0, 16, CHORUS_PROG, vel=100, key=k)
    _kit(sc, t0, 16, 0.95, ride=False, china=True, crash_in=True)
    _lead_hook(sc, t0, 4, 102, key=k, lyrics=True)
    for r in range(4):
        en.line(sc, BASS, t0 + 16.0 * r, C2 + k, _MODE, _BASS_HOOK, 104,
                jt=0, jv=0, gate=0.95)
    _choir_pad(sc, AAH, t0, 24, CHORUS_PROG, vel=62, key=k)
    _ooh_line(sc, t0, [5, 4, 3, 2, 3, 4, 5, 6, 5, 4, 3, 2], 56, key=k)
    _choir_pad(sc, EH, t0, 24, CHORUS_PROG, vel=54, key=k, lo=62, hi=84)
    en.vowel_curve(sc, AAH, [(t0, 55), (t0 + 40.0, 100), (t0 + 92.0, 82)],
                   step=2.0)
    en.vowel_curve(sc, EH, [(t0, 30), (t0 + 24.0, 72)], step=2.0)
    _strings_bed(sc, t0, 24, CHORUS_PROG, vel=62, key=k, lo=52, hi=83,
                 swell=[(t0, 60), (t0 + 24.0, 96), (t0 + 48.0, 80),
                        (t0 + 72.0, 108), (t0 + 94.0, 70)])
    _brass_swells(sc, t0, 24, CHORUS_PROG, vel=92, key=k)
    _timp(sc, t0, 24, key=k)
    chords = [en.triad(C4 - 12 + k, _MODE, CHORUS_PROG[i % 4])
              for i in range(24)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=53, hi=76,
                 vel=56, legato=0.0)
    en.leslie(sc, KEYS, t0, t0 + 8.0, 100, 30)
    en.leslie(sc, KEYS, t0 + 48.0, t0 + 70.0, 25, 112)
    # The coda tag (bars 17-24): broad chords, held lead, echo throw.
    c0 = t0 + 64.0
    _piano_coda(sc, c0, 8, CODA_PROG, vel=94, key=k)
    _gtr_strum(sc, c0, 8, CODA_PROG, vel=78, key=k)
    for i in range(8):
        _power(sc, _gtr_root(CODA_PROG[i], k), c0 + 4.0 * i, 3.6,
               98, jt=0 if i == 0 else 2)
    _kit(sc, c0, 8, 0.9, ride=True, china=True, fills=True)
    _bass_walk(sc, c0, CODA_PROG, vel=102, key=k)
    en.line(sc, LEAD, c0, C4 + k, _MODE,
            [(3, 0.0, 3.5), (4, 4.0, 3.5), (5, 8.0, 3.5),
             (8, 12.0, 11.0)], 104, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(c0 + 13.0, 0), (c0 + 18.0, 68),
                              (c0 + 23.0, 14)], step=0.2)
    en.echo_throw(sc, LEAD, c0 + 20.0, base=8, peak=82, release=3.0)
    en.lyric(sc, c0, "we shine on")


def outro(sc) -> None:
    """The motif again, in D — the same prayer in a brighter room."""
    t0 = 392.0
    _motif(sc, t0, key=LIFT, scale=0.9)
    _motif(sc, t0 + 16.0, key=LIFT, scale=0.72)
    # Strings exhale over the first statement, then hand it back.
    chords = [en.triad(C4 - 12 + LIFT, _MODE, d) for d in (1, 5)]
    en.pad_block(sc, STRINGS, t0, chords, 8.0, size=4, lo=50, hi=79,
                 vel=40, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0, 52), (t0 + 16.0, 24)], step=1.0)
    # The last chord: D major add9, pedalled, dying away.
    r = _lh_root(1, LIFT)
    for p, dv in ((r, 6), (r + 7, 2), (r + 12, 0), (r + 16, -2),
                  (r + 19, -4), (r + 26, -6)):
        sc.note(PIANO, p, t0 + 32.0, 7.0, 52 + dv, jt=0, jv=0)
    en.sustain(sc, PIANO, t0 + 32.02, t0 + 39.5)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 4, 16, 25, 29, 30, 33, 47, 48, 52, 53, 54, 61, 85}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, LEAD, KEYS, STRINGS, DRUMS,
                     BRASS, TIMP, EH}
NOTE_RANGES = {
    PIANO: (40, 92), GTR_C: (45, 86), GTR_D: (40, 76), BASS: (36, 64),
    AAH: (52, 84), OOH: (52, 86), LEAD: (55, 84), KEYS: (48, 80),
    STRINGS: (44, 86), BRASS: (48, 82), TIMP: (36, 52), EH: (55, 86),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (255.0, 276.0)   # actual 265 s (4:25) +- ~10 s
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.15),
    ("verse2", ">=", "verse1", 1.05),
    ("chorus2", ">=", "chorus1", 1.0),
    ("middle8", "<=", "chorus2", 0.8),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("final_chorus", ">=", "chorus1", 1.1),
    ("pre1", "<=", "chorus1", 0.9),
    ("pre2", "<=", "chorus2", 0.9),
    ("intro", "<=", "chorus1", 0.6),
    ("outro", "<=", "final_chorus", 0.5),
]
# The staircase: every orchestral layer is silent before its entry.
LATE_CHANNELS = {AAH: 40.0, BASS: 104.0, DRUMS: 104.0, GTR_C: 120.0,
                 LEAD: 120.0, KEYS: 152.0, GTR_D: 216.0, OOH: 216.0,
                 STRINGS: 264.0, TIMP: 292.0, BRASS: 296.0, EH: 296.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("pre1", 0), ("chorus1", 0), ("verse2", 0),
                 ("chorus2", 0), ("final_chorus", 2)],
    "hook": "final_chorus",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH, EH],
    "sections": ["chorus2", "middle8", "final_chorus"],
}
FEATURES_EXPECTED = {
    "cc64_sustain", "cc67_soft", "cc11_expression", "cc70_vowel",
    "aftertouch", "cc1_leslie", "cc1_vibrato", "cc94_echo",
    "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def _sec(name: str) -> tuple[float, float]:
    for n_, t0, t1 in _SECTIONS:
        if n_ == name:
            return t0, t1
    raise KeyError(name)


def _cell(sc, ch, t0: float, t1: float) -> list[tuple[float, int]]:
    """Quarter-beat-rounded (onset-offset, pitch) list for a window."""
    return sorted((round((on - t0) * 4) / 4, p)
                  for on, _off, p, _v in _spans(sc, ch)
                  if t0 - 1e-9 <= on < t1 - 1e-9)


def oracles(sc, info, spans):
    # 1. layer_build — the active-channel count grows monotonically
    # along the song's spine (the deliberate middle-8 pullback is not
    # on the spine), from solo piano (1) to all thirteen channels.
    spine = ["intro", "verse1", "pre1", "chorus1", "verse2", "pre2",
             "chorus2", "final_chorus"]
    counts = []
    for name in spine:
        t0, t1 = _sec(name)
        chans = {ch for ch in sc.events
                 if any(t0 - 0.05 <= on < t1 - 0.05
                        for on, _off, _p, _v in _spans(sc, ch))}
        counts.append(len(chans))
    fails_layer: list[str] = []
    pairs = list(zip(counts, counts[1:]))
    if any(b < a for a, b in pairs):
        fails_layer.append(f"layer count falls along the spine: "
                           f"{list(zip(spine, counts))}")
    rises = sum(1 for a, b in pairs if b > a)
    if rises < 6:
        fails_layer.append(f"only {rises} strict layer rises along the "
                           f"spine (need >= 6): {counts}")
    if counts and counts[0] != 1:
        fails_layer.append(f"intro uses {counts[0]} channels "
                           f"(want solo piano = 1)")
    if counts and counts[-1] != 13:
        fails_layer.append(f"final chorus uses {counts[-1]} channels "
                           f"(want all 13)")

    # 2. motif_recap — the outro piano restates the intro motif lifted
    # +2 (recomputed by the same _motif code in D, never copied).
    fails_motif: list[str] = []
    intro_cell = _cell(sc, PIANO, 0.0, 16.0)
    outro_cell = _cell(sc, PIANO, 392.0, 408.0)
    if not intro_cell:
        fails_motif.append("no intro piano motif found in [0, 16)")
    elif outro_cell != [(t, p + LIFT) for t, p in intro_cell]:
        fails_motif.append(
            f"outro [392, 408) is not the intro motif lifted +{LIFT} "
            f"({len(intro_cell)} intro vs {len(outro_cell)} outro notes)")

    # 3. hook_lift — the final-chorus lead hook is the chorus-1 hook
    # lifted +2 (the key-lift is real, not a louder restatement).
    fails_hook: list[str] = []
    c1 = _cell(sc, LEAD, 120.0, 136.0)
    fc = _cell(sc, LEAD, 296.0, 312.0)
    if not c1:
        fails_hook.append("no chorus-1 lead hook found in [120, 136)")
    elif fc != [(t, p + LIFT) for t, p in c1]:
        fails_hook.append(
            f"final-chorus hook is not the chorus-1 hook lifted "
            f"+{LIFT} ({len(c1)} vs {len(fc)} notes)")

    return [("layer_build", fails_layer),
            ("motif_recap", fails_motif),
            ("hook_lift", fails_hook)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# PROVISIONAL (re-pinned at the phase-D album freeze): measured on the
# 2026.07.11 per-track render, ferrosintesis 0.13.0 —
# lift 16.4 dB, entry rise 11.7 dB; pinned measured - >=3.5 dB slack.
_LIFT_DB = 12.0    # PROVISIONAL: final chorus over verse 1 (album max)
_RISE_DB = 8.0     # PROVISIONAL: RMS rise across the beat-296 entry


def audio_checks(ctx):
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(48.0, 96.0)
    f0, f1 = ctx.bar_window(304.0, 352.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    fails_rise: list[str] = []
    a0, a1 = ctx.bar_window(280.0, 288.0)
    b0, b1 = ctx.bar_window(296.0, 304.0)
    before = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    after = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    if after < before + _RISE_DB:
        fails_rise.append(f"orchestra entry {after:.1f} dB not >= "
                          f"{before:.1f} + {_RISE_DB} dB")

    return [("chorus_lift", fails_lift),
            ("orch_entry_rise", fails_rise)]
