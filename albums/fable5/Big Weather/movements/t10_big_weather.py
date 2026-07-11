"""t10_big_weather.py — "Big Weather" (Big Weather, track 10).

The title track and closer — the everything-track (HLD §4 row 10).
D major at 120 BPM.  A solo piano intro states the TITLE HOOK; the song
then rebuilds the whole album's arsenal around it, channel by channel
(LATE_CHANNELS staircases twelve entries across the song), until the
DOUBLE final chorus stands as the record's fullest tutti: all thirteen
channels — three choir layers with CC70 vowel morphs, brass growls with
CC2 breath, strings under CC11 swells, timpani rolls, drive guitar
lifted 29→30, rock organ under Leslie ramps.  The outro decays from
tutti back to the solo piano hook — the album ends where it began
(oracle: hook_bookend, recomputed not copied) — with a Morse "BW"
woodblock easter egg tapped quietly in the hush, and a REAL ritardando:
the tempo map eases 120→84 BPM over the last ten bars.

Oracle-pinned claims: the outro piano statement [528,544) equals the
intro statement [0,16) note-for-note (hook_bookend); the lead's chorus
hook is the intro piano's right hand — same melody, same octave
(title_identity); and every bar of the double final chorus has >= 11
channels sounding, with >= 8 all-thirteen bars (tutti).

Form (HLD §4, full grammar + ritardando ending):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 | middle8 |
  final_chorus (32 bars: hook x2 + tag, twice, then an 8-bar coda wall) |
  outro (tutti decay -> Morse "BW" -> solo piano hook -> last chord)
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 10
TITLE = "Big Weather"
FILE = "10 - Big Weather.mid"
SEED = 20260710

BPM = 120.0

# Channels (HLD §3).
PIANO, GTR_C, GTR_D, BASS = 0, 1, 2, 3
AAH, OOH, LEAD, KEYS = 4, 5, 6, 7
STRINGS, DRUMS, BRASS, TIMP = 8, 9, 10, 11
EH = 12

_SECTIONS = [
    ("intro",          0.0,  32.0),
    ("verse1",        32.0,  96.0),
    ("pre1",          96.0, 128.0),
    ("chorus1",      128.0, 176.0),
    ("verse2",       176.0, 240.0),
    ("pre2",         240.0, 272.0),
    ("chorus2",      272.0, 320.0),
    ("middle8",      320.0, 368.0),
    ("final_chorus", 368.0, 496.0),
    ("outro",        496.0, 560.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    # 120 straight, then the RITARDANDO ending (HLD §4): a real,
    # audible tempo-map ease-down — 120 -> 84 BPM over the last bars,
    # bottoming out under the closing chord.
    tempo_map=[(0.0, BPM), (520.0, 112.0), (528.0, 106.0),
               (536.0, 100.0), (544.0, 92.0), (552.0, 84.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 2, 0)],                      # D major, two sharps
    channels=[
        (PIANO,   "piano",        0, 100, 64, 50),
        (GTR_C,   "clean guitar", 26,  94, 48, 40),
        (GTR_D,   "drive guitar", 29,  92, 80, 32),
        (BASS,    "bass guitar",  33, 105, 64, 25),
        (AAH,     "choir aah",    52,  88, 64, 70),
        (OOH,     "choir ooh",    53,  84, 64, 70),
        (LEAD,    "lead synth",   80,  92, 64, 45),
        (KEYS,    "ep / organ",    4,  84, 64, 45),
        (STRINGS, "strings",      48,  88, 64, 65),
        (DRUMS,   "drums",         0, 108, 64, 45),
        (BRASS,   "brass",        61,  92, 64, 45),
        (TIMP,    "timpani",      47,  96, 64, 60),
        (EH,      "choir eh",     54,  82, 64, 70),
    ],
    program_changes=[
        (GTR_D, 344.0, 30),     # overdrive -> distortion (during silence,
                                # so the first tutti chord is already 30)
        (KEYS,  344.0, 18),     # EP -> rock organ (Leslie now honored)
        (GTR_D, 496.0, 29),     # relax to overdrive as the front passes
    ],
)

# ---------------------------------------------------------------------------
# Harmony — D major throughout.  The verse broods from the vi (Bm); the
# chorus is an ionian axis with the ii (Em) where t01 leaned on vi-IV-V
# and t04 on the iii.  The STORM TAG (IV V vi V) is the instrumental
# answer riff after every pair of hook statements.
# ---------------------------------------------------------------------------

D2, D3, D4 = en.n("D2"), en.n("D3"), en.n("D4")
_MODE = "ionian"

VERSE_PROG = [6, 4, 1, 5]              # Bm  G   D   A
PRE_PROG = [2, 4, 5, 5]                # Em  G   A   A (dominant pedal)
CHORUS_PROG = [1, 5, 2, 4]             # D   A   Em  G
TAG_PROG = [4, 5, 6, 5]                # G   A   Bm  A
MID_PROG = [6, 3, 4, 1, 6, 3, 2, 5]    # Bm F#m G D | Bm F#m Em A
BUILD_PROG = [4, 5, 5, 5]              # G, then the long A crescendo
CODA_PROG = [4, 5, 6, 5, 4, 5, 1, 1]   # the coda wall, landing home

CH12 = CHORUS_PROG * 2 + TAG_PROG                      # one 12-bar chorus
FINAL_SEQ = (CHORUS_PROG * 2 + TAG_PROG) * 2 + CODA_PROG   # 32-bar double


def _root(deg: int) -> int:
    return en.pitch(D2, _MODE, deg)


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(D2, _MODE, deg)]


def _lh(deg: int) -> int:
    """Piano LH root in the D2..C#3 pocket (< 50, >= 38)."""
    p = _root(deg)
    while p >= 50:
        p -= 12
    while p < 38:
        p += 12
    return p


def _bp(deg: int) -> int:
    """Bass pitch for a degree, folded into [36, 62] (no sub-C2)."""
    p = _root(deg)
    while p < 36:
        p += 12
    while p > 62:
        p -= 12
    return p


def _gr(deg: int) -> int:
    """Drive-guitar power-chord root in the [41, 55] pocket."""
    p = _root(deg)
    while p < 41:
        p += 12
    while p > 55:
        p -= 12
    return p


# ---------------------------------------------------------------------------
# The TITLE HOOK — 16 beats over D A Em G, with the dotted "Big Wea-ther"
# pickup cell recurring in bars 1, 2 and 4.  The piano states it solo in
# the intro and the outro (oracle: hook_bookend); the lead sings the
# same notes in every chorus (oracle: title_identity).
# (degree-from-D4, start, dur, vel) — jt=0 / jv=0 everywhere it appears.
# ---------------------------------------------------------------------------

_HOOK = [
    (3, 0.0, 0.75, 76), (4, 0.75, 0.25, 68), (5, 1.0, 1.5, 80),
    (8, 2.5, 1.5, 84),
    (7, 4.0, 0.75, 78), (5, 4.75, 0.25, 70), (7, 5.0, 1.0, 80),
    (9, 6.0, 2.0, 86),
    (10, 8.0, 0.75, 88), (9, 8.75, 0.25, 80), (8, 9.0, 1.0, 84),
    (7, 10.0, 0.5, 78), (5, 10.5, 0.5, 74), (6, 11.0, 1.0, 76),
    (4, 12.0, 0.75, 74), (5, 12.75, 0.25, 70), (6, 13.0, 1.0, 78),
    (3, 14.0, 2.0, 72),
]
_HOOK_LINE = [(d, s, dur) for d, s, dur, _v in _HOOK]
_HOOK_BARS = [1, 5, 2, 4]
_HOOK_LYRICS = ["big weather", "coming in", "hold together", "here it comes"]

# The final-chorus bass HOOK (16 beats, degrees from D2): the bass sings
# its own countermelody under the double chorus (BASS_SPEC hook).
_BASS_HOOK = [
    (1, 0.0, 0.7), (2, 0.75, 0.25), (3, 1.0, 0.95), (5, 2.0, 0.45),
    (4, 2.5, 0.45), (3, 3.0, 0.45), (2, 3.5, 0.45),
    (5, 4.0, 0.7), (4, 4.75, 0.25), (5, 5.0, 0.95), (7, 6.0, 0.45),
    (8, 6.5, 0.45), (7, 7.0, 0.45), (5, 7.5, 0.45),
    (2, 8.0, 0.7), (3, 8.75, 0.25), (4, 9.0, 0.95), (6, 10.0, 0.45),
    (5, 10.5, 0.45), (4, 11.0, 0.45), (3, 11.5, 0.45),
    (4, 12.0, 0.7), (5, 12.75, 0.25), (6, 13.0, 0.95), (5, 14.0, 0.45),
    (4, 14.5, 0.45), (2, 15.0, 0.45), (1, 15.5, 0.45),
]

_CODA_LEAD = [(5, 0.0, 3.5), (6, 4.0, 3.5), (8, 8.0, 3.5), (9, 12.0, 3.5),
              (10, 16.0, 7.5), (8, 24.0, 7.5)]


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _hook_piano(sc, t0: float, scale: float = 1.0) -> None:
    """One 16-beat solo-piano statement of the TITLE HOOK: RH melody
    (>= D4) over an LH root/fifth/octave pattern (< D4), pedalled.
    Fully deterministic (jt=0, jv=0) — the bookend oracle pins it."""
    for deg, start, dur, vel in _HOOK:
        sc.note(PIANO, en.pitch(D4, _MODE, deg), t0 + start, dur,
                int(round(vel * scale)), jt=0, jv=0)
    for i, deg in enumerate(_HOOK_BARS):
        b = t0 + 4.0 * i
        r = _lh(deg)
        sc.note(PIANO, r, b, 1.95, int(round(62 * scale)), jt=0, jv=0)
        sc.note(PIANO, r + 7, b + 2.0, 0.95, int(round(54 * scale)),
                jt=0, jv=0)
        sc.note(PIANO, r + 12, b + 3.0, 0.95, int(round(56 * scale)),
                jt=0, jv=0)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_verse(sc, t0: float, seq: list[int], vel: int = 54) -> None:
    """Verse piano: LH root/fifth halves, RH off-beat dyads — rain
    starting on the roof.  Pedalled."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=2)
        r = _lh(deg)
        sc.note(PIANO, r, b, 1.9, vel + 8, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, vel + 2, jt=3, jv=3)
        for beat, a, c in ((1.5, 0, 1), (2.5, 1, 2), (3.5, 0, 2)):
            sc.note(PIANO, tri[a], b + beat, 0.7, vel - 6, jt=3, jv=4)
            sc.note(PIANO, tri[c], b + beat, 0.7, vel - 10, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_pre(sc, t0: float, seq: list[int], vel0: int = 64,
               vel1: int = 84) -> None:
    """Pre-chorus piano: RH triad quarters over LH halves, one long
    section crescendo."""
    n = len(seq)
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=2)
        r = _lh(deg)
        v = int(round(en.lerp(vel0, vel1, i / max(1, n - 1))))
        sc.note(PIANO, r, b, 1.9, v + 6, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, v + 2, jt=3, jv=3)
        for k in range(4):
            for p in tri:
                sc.note(PIANO, p, b + k, 0.9, v - 8, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_anthem(sc, t0: float, seq: list[int], vel: int = 84) -> None:
    """Chorus piano: driving broken-half chords with a pushed &-of-2."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=2)
        r = _lh(deg)
        sc.note(PIANO, r, b, 1.4, vel + 6, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 12, b + 1.5, 0.9, vel, jt=3, jv=3)
        sc.note(PIANO, r, b + 2.5, 1.4, vel + 2, jt=3, jv=3)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 0.9), (3.5, 0.45)):
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 6, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_coda(sc, t0: float, seq: list[int], vel: int = 92) -> None:
    """Coda piano: broad block chords with an octave crown."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=2)
        r = _lh(deg)
        sc.note(PIANO, r, b, 1.95, vel + 6, jt=0 if i == 0 else 3, jv=3)
        sc.note(PIANO, r + 7, b + 2.0, 1.95, vel + 2, jt=3, jv=3)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 6, jt=3, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.0, 0.9, vel + 2, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _gtr_pick(sc, t0: float, seq: list[int], vel: int = 60) -> None:
    """Clean guitar: picked eighth-note broken chords (verse texture)."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=1)
        line = [tri[0], tri[2], tri[1] + 12, tri[0] + 12,
                tri[2], tri[1] + 12, tri[2] + 12, tri[1]]
        for k, p in enumerate(line):
            sc.note(GTR_C, p, b + 0.5 * k, 0.42, vel - (4 if k % 2 else 0),
                    jt=3, jv=4)


def _gtr_strum(sc, t0: float, seq: list[int], vel: int = 76) -> None:
    """Clean guitar: broad strums, down-down-up-down-up."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=1)
        chord = tri + [tri[0] + 12, tri[1] + 12]
        for beat, dur, down, dv in ((0.0, 1.4, True, 0),
                                    (1.5, 0.9, True, -8),
                                    (2.5, 0.45, False, -12),
                                    (3.0, 0.9, True, -4),
                                    (3.5, 0.45, False, -10)):
            en.strum(sc, GTR_C, chord, b + beat, dur, vel + dv,
                     spread=0.025, down=down)


def _power(sc, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    """Root + fifth + octave on the drive guitar."""
    for i, off in enumerate((0, 7, 12)):
        sc.note(GTR_D, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _power_bed(sc, t0: float, seq: list[int], vel: int = 96) -> None:
    """Drive guitar: half-bar power chords with a pushed back half."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        r = _gr(deg)
        _power(sc, r, b, 1.4, vel, jt=0 if i == 0 else 2)
        _power(sc, r, b + 1.5, 0.9, vel - 8, jt=2)
        _power(sc, r, b + 2.5, 1.9, vel - 4, jt=2)


def _chug(sc, t0: float, seq: list[int], vel: int = 78) -> None:
    """Drive guitar: gapped straight-eight chug (mono-safe transients)."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        r = _gr(deg)
        for k in range(8):
            _power(sc, r, b + 0.5 * k, 0.35,
                   vel + (6 if k in (0, 3, 6) else 0) - (4 if k % 2 else 0),
                   jt=0 if (i == 0 and k == 0) else 2)


def _bass_walk(sc, t0: float, seq: list[int], vel: int = 96) -> None:
    """The melodic verse walk: root, a stepwise rise through 2-3, the
    fifth-sixth turn, and a scale approach into every next root."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        nxt = seq[(i + 1) % len(seq)]
        sc.note(BASS, _bp(deg), b, 0.95, vel, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, _bp(deg + 1), b + 1.0, 0.45, vel - 10, jt=2, jv=3)
        sc.note(BASS, _bp(deg + 2), b + 1.5, 0.45, vel - 8, jt=2, jv=3)
        sc.note(BASS, _bp(deg + 4), b + 2.0, 0.7, vel - 4, jt=2, jv=3)
        sc.note(BASS, _bp(deg + 5), b + 2.75, 0.2, vel - 18, jt=3, jv=4)
        sc.note(BASS, _bp(deg + 4), b + 3.0, 0.45, vel - 8, jt=2, jv=3)
        sc.note(BASS, _bp(nxt - 1), b + 3.5, 0.45, vel - 6, jt=2, jv=3)


def _bass_hook(sc, t0: float, reps: int, vel: int = 102) -> None:
    """The final-chorus bass countermelody (BASS_SPEC hook), pinned."""
    for r in range(reps):
        base = t0 + 16.0 * r
        for deg, start, dur in _BASS_HOOK:
            sc.note(BASS, _bp(deg), base + start, dur, vel, jt=0, jv=0)


def _kit(sc, t0: float, bars: int, x: float, *, ride: bool = False,
         china: bool = False, crash_in: bool = False, fills: bool = True,
         ghosts: bool = True) -> None:
    """The kit groove.  x 0..1 scales velocity and busy-ness."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(70, 106, x)))
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        if crash_in and first:
            sc.hit(49, b, min(122, v + 16), jt=0)
        if china and i % 4 == 2:
            sc.hit(52, b, v + 2, jt=2)
        sc.hit(36, b, v + 8, jt=0 if first else 2)
        sc.hit(36, b + 2.5, v + 2, jt=2)
        if x > 0.65 and i % 2 == 1:
            sc.hit(36, b + 3.5, v - 2, jt=2)
        sc.hit(38, b + 1.0, v + 10, jt=2, jv=4)
        sc.hit(38, b + 3.0, v + 10, jt=2, jv=4)
        if ghosts and x < 0.9 and not fill_bar:
            # (never on fill bars: a ghost landing on a fill-run snare
            # tick would collide same-pitch at the same instant)
            sc.hit(38, b + 0.75, max(16, v - 48), jt=3, jv=6)
            sc.hit(38, b + 2.25, max(16, v - 50), jt=3, jv=6)
        key = 51 if ride else 42
        for k in range(8):
            if fill_bar and k >= 5:
                continue
            sc.hit(key, b + 0.5 * k, max(20, v - (8 if k % 2 == 0 else 24)),
                   jt=2, jv=5)
        if ride and i % 2 == 0:
            sc.hit(53, b + 2.0, v - 6, jt=2)
        if not ride and not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 18, jt=2)
        if fill_bar:
            run = (38, 38, 50, 48, 45, 43, 41, 38) if last \
                else (38, 50, 48, 47, 45, 43)
            n = len(run)
            start = 4.0 - 0.25 * n
            for k, key2 in enumerate(run):
                sc.hit(key2, b + start + 0.25 * k,
                       int(en.lerp(v - 20, v + 14, k / (n - 1))), jt=2)


def _heartbeat(sc, t0: float, bars: int, vel: int = 60) -> None:
    """Kick + side-stick heartbeat (the eye of the storm)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        sc.hit(36, b, vel + 6, jt=0 if i == 0 else 2)
        sc.hit(37, b + 2.0, vel - 8, jt=2)


def _cym_swell(sc, t0: float, bars: int, v0: int = 58,
               v1: int = 110) -> None:
    """Coda drums: continuous 16th ride crescendo under crash/china
    alternation — the wall of shimmer into the cut."""
    total = bars * 16 - 1
    for i in range(bars):
        b = t0 + 4.0 * i
        sc.hit(49 if i % 2 == 0 else 57, b, 102 + (4 if i % 2 else 0),
               jt=0 if i == 0 else 2)
        sc.hit(36, b, 106, jt=0 if i == 0 else 2)
        sc.hit(36, b + 2.0, 100, jt=2)
        sc.hit(38, b + 1.0, 104, jt=2, jv=3)
        sc.hit(38, b + 3.0, 106, jt=2, jv=3)
        for k in range(16):
            sc.hit(51, b + 0.25 * k,
                   int(en.lerp(v0, v1, (i * 16 + k) / total)), jt=2, jv=4)


def _choir_pad(sc, ch: int, t0: float, seq: list[int], vel: int,
               lo: int = 57, hi: int = 79) -> None:
    chords = [en.triad(D3, _MODE, d) for d in seq]
    en.pad_block(sc, ch, t0, chords, 4.0, size=3, lo=lo, hi=hi,
                 vel=vel, legato=0.0)


def _ooh_counter(sc, t0: float, tones: list[int], vel: int = 54) -> None:
    """Choir ooh: one held counter-tone every two bars, jt=0."""
    for i, deg in enumerate(tones):
        sc.note(OOH, en.pitch(D4, _MODE, deg), t0 + 8.0 * i, 7.5,
                vel, jt=0, jv=3)


def _strings_bed(sc, t0: float, seq: list[int], vel: int,
                 lo: int = 48, hi: int = 81,
                 swell: list[tuple[float, int]] | None = None) -> None:
    chords = [en.triad(D3, _MODE, d) for d in seq]
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=lo, hi=hi,
                 vel=vel, legato=0.0)
    if swell:
        en.expr_curve(sc, STRINGS, swell, step=1.0)


def _brass_hits(sc, t0: float, seq: list[int], vel: int = 92,
                growl_every: int = 4) -> None:
    """Section stabs on the &-of-1 and 3; a held growl (aftertouch +
    CC2 breath) every `growl_every` bars."""
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=1)
        if i % growl_every == growl_every - 1:
            for p in tri:
                sc.note(BRASS, p, b, 3.6, vel - 8, jt=0, jv=3)
            en.at_curve(sc, BRASS, [(b, 16), (b + 2.0, 96), (b + 3.5, 26)],
                        step=0.5)
            en.cc_curve(sc, BRASS, 2, [(b, 44), (b + 2.0, 110),
                                       (b + 3.5, 60)], step=0.5)
        else:
            for beat in (1.5, 3.0):
                for p in tri:
                    sc.note(BRASS, p, b + beat, 0.4, vel, jt=0, jv=3)


def _timp(sc, t0: float, bars: int, vel: int = 90) -> None:
    """Tonic/dominant strokes every downbeat; crescendo rolls on the
    dominant into every fourth downbeat."""
    tonic, dom = _bp(1), _bp(5)
    for i in range(bars):
        b = t0 + 4.0 * i
        sc.note(TIMP, tonic if i % 2 == 0 else dom, b, 1.2,
                vel + (6 if i % 2 == 0 else 0), jt=0, jv=3)
        if i % 4 == 3:
            for k in range(8):
                sc.note(TIMP, dom, b + 2.0 + 0.25 * k, 0.22,
                        int(en.lerp(vel - 32, vel + 10, k / 7)),
                        jt=0 if k == 0 else 2, jv=4)


def _lead_hook(sc, t0: float, reps: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The TITLE HOOK on the lead synth (same notes as the intro piano
    RH — oracle: title_identity); CC1 vibrato blooms on the holds."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, D4, _MODE, _HOOK_LINE, vel, jt=0, jv=0,
                gate=0.98)
        for _deg, start, dur in _HOOK_LINE:
            if dur >= 1.5:
                b = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(b + 0.25, 0), (b + dur * 0.6, 54),
                             (b + dur, 10)], step=0.15)
        if lyrics and r == 0:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


_TAG_HITS = ((0.0, 0.7), (0.75, 0.2), (1.5, 0.45), (2.0, 0.45), (3.0, 0.95))


def _storm_tag(sc, t0: float, vel: int = 100, *,
               lead_fill: bool = False) -> None:
    """The 4-bar STORM TAG: a unison rhythm riff (drive gtr + piano
    octaves + bass) over IV V vi V, with kit accents."""
    for i, deg in enumerate(TAG_PROG):
        b = t0 + 4.0 * i
        r = _gr(deg)
        pr = _lh(deg)
        tri = _triad(deg, octave=1)
        for beat, dur in _TAG_HITS:
            jt = 0 if beat == 0.0 else 2
            _power(sc, r, b + beat, dur, vel, jt=jt)
            sc.note(PIANO, pr, b + beat, dur, vel - 10, jt=jt, jv=3)
            sc.note(PIANO, pr + 12, b + beat, dur, vel - 14, jt=jt, jv=3)
            sc.note(BASS, _bp(deg), b + beat, dur, min(120, vel + 2),
                    jt=jt, jv=3)
            sc.hit(36, b + beat, vel, jt=2)
            en.strum(sc, GTR_C, tri + [tri[0] + 12], b + beat,
                     max(dur, 0.4), vel - 22, spread=0.02)
        sc.hit(49 if i % 2 == 0 else 57, b, vel + 6, jt=0 if i == 0 else 2)
        sc.hit(38, b + 1.0, vel + 4, jt=2)
        sc.hit(38, b + 3.0, vel + 6, jt=2)
        for k in range(8):
            sc.hit(42, b + 0.5 * k, vel - 26 + (6 if k % 2 == 0 else 0),
                   jt=2, jv=4)
    # The lead answers the riff with long call tones over bars 1-3.
    sc.note(LEAD, en.pitch(D4, _MODE, 9), t0, 7.5, vel - 14, jt=0, jv=2)
    sc.note(LEAD, en.pitch(D4, _MODE, 7), t0 + 8.0, 3.5, vel - 18,
            jt=0, jv=2)
    if lead_fill:
        en.line(sc, LEAD, t0 + 12.0, D4, _MODE,
                [(3, 0.0, 0.5), (4, 0.5, 0.5), (5, 1.0, 0.5), (6, 1.5, 0.5),
                 (7, 2.0, 0.5), (9, 2.5, 1.4)], 92, vel_end=106, jt=2, jv=2)


def _chorus_block(sc, t0: float, *, vel_lift: int = 0, kit_x: float = 0.8,
                  ride: bool = False, china: bool = False,
                  lyrics: bool = False, bass_hook: bool = False) -> None:
    """8 hook bars: the full-band chorus unit (TITLE HOOK x2)."""
    _piano_anthem(sc, t0, CHORUS_PROG * 2, vel=84 + vel_lift)
    _gtr_strum(sc, t0, CHORUS_PROG * 2, vel=74 + vel_lift)
    _power_bed(sc, t0, CHORUS_PROG * 2, vel=96 + vel_lift)
    if bass_hook:
        _bass_hook(sc, t0, 2, vel=100 + vel_lift)
    else:
        _bass_walk(sc, t0, CHORUS_PROG * 2, vel=100 + vel_lift)
    _kit(sc, t0, 8, kit_x, ride=ride, china=china, crash_in=True)
    _lead_hook(sc, t0, 2, 94 + vel_lift, lyrics=lyrics)


def _coda(sc, t0: float) -> None:
    """The 8-bar CODA wall: half-time chords, held lead peaks, a brass
    growl wall, the cymbal swell, and the last echo throw."""
    _piano_coda(sc, t0, CODA_PROG, vel=92)
    _gtr_strum(sc, t0, CODA_PROG, vel=80)
    for i, deg in enumerate(CODA_PROG):
        _power(sc, _gr(deg), t0 + 4.0 * i, 3.6, 104,
               jt=0 if i == 0 else 2)
    _bass_walk(sc, t0, CODA_PROG, vel=104)
    _kit(sc, t0, 4, 0.95, ride=True, china=True, fills=True)
    _cym_swell(sc, t0 + 16.0, 4)
    en.line(sc, LEAD, t0, D4, _MODE, _CODA_LEAD, 102, jt=0, jv=0, gate=0.98)
    for deg, start, dur in _CODA_LEAD:
        if dur >= 3.0:
            b = t0 + start
            en.cc_curve(sc, LEAD, 1, [(b + 0.5, 0), (b + dur * 0.6, 60),
                                      (b + dur, 12)], step=0.2)
    for i, deg in enumerate(CODA_PROG):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=1)
        for p in tri:
            sc.note(BRASS, p, b, 3.6, 86, jt=0, jv=3)
        if i % 2 == 1:
            en.at_curve(sc, BRASS, [(b, 20), (b + 2.0, 98), (b + 3.5, 36)],
                        step=0.5)
    en.echo_throw(sc, LEAD, t0 + 22.0, base=8, peak=84, release=3.0)
    en.lyric(sc, t0, "the sky wide open")


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    """Solo piano states the TITLE HOOK twice: hushed, then open."""
    en.soft_pedal(sc, PIANO, 0.0, 15.9)
    _hook_piano(sc, 0.0, scale=0.85)
    _hook_piano(sc, 16.0, scale=1.0)


def verse1(sc) -> None:
    """Bass, clean guitar and the kit arrive under the verse — kept
    genuinely quiet so the closer's chorus lift has room to be big."""
    t0 = 32.0
    _piano_verse(sc, t0, VERSE_PROG * 4, vel=50)
    _gtr_pick(sc, t0, VERSE_PROG * 4, vel=54)
    _bass_walk(sc, t0, VERSE_PROG * 4, vel=88)
    _kit(sc, t0, 16, 0.4)


def _pre(sc, t0: float, lift: int = 0) -> None:
    _piano_pre(sc, t0, PRE_PROG * 2, vel0=64 + lift, vel1=84 + lift)
    _chug(sc, t0, PRE_PROG * 2, vel=78 + lift)
    _gtr_pick(sc, t0, PRE_PROG * 2, vel=64 + lift)
    _bass_walk(sc, t0, PRE_PROG * 2, vel=98 + lift)
    _kit(sc, t0, 8, 0.62, crash_in=True)


def pre1(sc) -> None:
    """The drive guitar arrives: the gapped chug starts the climb."""
    _pre(sc, 96.0)


def chorus1(sc) -> None:
    """The lead arrives and sings the title hook; the storm tag answers."""
    _chorus_block(sc, 128.0, lyrics=True)
    _storm_tag(sc, 160.0, vel=96)


def verse2(sc) -> None:
    """EP pads join; the lead answers the ends of the piano phrases."""
    t0 = 176.0
    _piano_verse(sc, t0, VERSE_PROG * 4, vel=56)
    _gtr_pick(sc, t0, VERSE_PROG * 4, vel=62)
    _bass_walk(sc, t0, VERSE_PROG * 4, vel=98)
    _kit(sc, t0, 16, 0.55)
    chords = [en.triad(D3, _MODE, VERSE_PROG[i % 4]) for i in range(16)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=44, legato=0.0)
    for r, b0 in enumerate((t0 + 12.0, t0 + 28.0, t0 + 44.0)):
        en.line(sc, LEAD, b0, D4, _MODE,
                [(5, 0.0, 0.5), (6, 0.5, 0.5), (8, 1.0, 2.5)],
                60 + 4 * r, jt=2, jv=3)


def pre2(sc) -> None:
    _pre(sc, 240.0, lift=4)


def chorus2(sc) -> None:
    """The choir and the brass arrive: the first orchestral chorus."""
    t0 = 272.0
    _chorus_block(sc, t0, vel_lift=3, ride=True, lyrics=True)
    _storm_tag(sc, t0 + 32.0, vel=100, lead_fill=True)
    _choir_pad(sc, AAH, t0, CH12, vel=56)
    _ooh_counter(sc, t0, [5, 6, 5, 6, 5, 3], vel=52)
    en.vowel_curve(sc, AAH, [(t0, 40), (t0 + 24.0, 86), (t0 + 47.0, 64)],
                   step=2.0)
    _brass_hits(sc, t0, CH12, vel=90, growl_every=4)
    chords = [en.triad(D3, _MODE, d) for d in CH12]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=48, legato=0.0)


def middle8(sc) -> None:
    """The eye of the storm: strings slip in pp under pedalled piano
    arps, then four bars of pure build on the dominant."""
    t0 = 320.0
    en.soft_pedal(sc, PIANO, t0, t0 + 30.0)
    for i in range(8):
        b = t0 + 4.0 * i
        tri1 = _triad(MID_PROG[i], octave=1)
        tri2 = _triad(MID_PROG[i], octave=2)
        line = [tri1[0], tri1[2], tri2[0], tri2[2], tri2[1], tri2[2],
                tri2[0], tri1[2]]
        for k, p in enumerate(line):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 52,
                    jt=0 if (i == 0 and k == 0) else 3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    _strings_bed(sc, t0, MID_PROG, vel=46,
                 swell=[(t0, 36), (t0 + 8.0, 66), (t0 + 16.0, 46),
                        (t0 + 24.0, 78), (t0 + 31.0, 56)])
    for i, deg in enumerate((3, 1, 3, 2)):
        sc.note(AAH, en.pitch(D4, _MODE, deg), t0 + 8.0 * i, 7.5, 44,
                jt=0, jv=2)
    for i, deg in enumerate(MID_PROG):
        b = t0 + 4.0 * i
        nxt = MID_PROG[(i + 1) % len(MID_PROG)]
        sc.note(BASS, _bp(deg), b, 3.3, 74, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, _bp(nxt - 1), b + 3.5, 0.45, 64, jt=2, jv=3)
    _heartbeat(sc, t0, 8, vel=58)
    # THE BUILD (352-368): G, then the long dominant crescendo.
    bb = t0 + 32.0
    _piano_pre(sc, bb, BUILD_PROG[:2], vel0=58, vel1=70)
    en.line(sc, PIANO, bb + 8.0, D4, _MODE,
            [(4, 0.0, 1.0), (5, 1.0, 1.0), (6, 2.0, 1.0), (7, 3.0, 1.0),
             (8, 4.0, 1.0), (9, 5.0, 1.0), (10, 6.0, 1.0), (11, 7.0, 0.95)],
            64, vel_end=92, jt=2, jv=2)
    _strings_bed(sc, bb, BUILD_PROG, vel=54,
                 swell=[(bb, 46), (bb + 8.0, 72), (bb + 15.5, 92)])
    sc.note(BASS, _bp(4), bb, 3.5, 82, jt=0, jv=3)
    sc.note(BASS, _bp(5), bb + 4.0, 3.5, 86, jt=2, jv=3)
    for k in range(16):
        sc.note(BASS, _bp(5), bb + 8.0 + 0.5 * k, 0.4,
                int(en.lerp(66, 96, k / 15)), jt=2, jv=3)
    tri = _triad(5, octave=1)
    for p in tri:
        sc.note(BRASS, p, bb + 8.0, 7.6, 76, jt=0, jv=3)
    en.at_curve(sc, BRASS, [(bb + 8.0, 14), (bb + 14.0, 88),
                            (bb + 15.5, 98)], step=0.5)
    en.cc_curve(sc, BRASS, 2, [(bb + 8.0, 36), (bb + 15.0, 102)], step=0.5)
    for p in en.triad(D3, _MODE, 5):
        sc.note(AAH, p + 12, bb + 8.0, 7.5, 50, jt=0, jv=2)
    en.vowel_curve(sc, AAH, [(bb + 8.0, 36), (bb + 15.0, 84)], step=1.0)
    for i in range(2):
        b = bb + 4.0 * i
        sc.hit(36, b, 78, jt=0 if i == 0 else 2)
        sc.hit(37, b + 2.0, 54, jt=2)
        for k in range(4):
            sc.hit(42, b + k, 44, jt=2, jv=4)
    for k in range(16):
        sc.hit(38, bb + 8.0 + 0.5 * k, int(en.lerp(44, 100, k / 15)),
               jt=2, jv=3)
    for k in range(8):
        sc.hit(36, bb + 8.0 + k, 74 + 2 * k, jt=2)
    for k, key in enumerate((50, 48, 47, 45)):
        sc.hit(key, bb + 14.0 + 0.5 * k, 88 + 4 * k, jt=2)


def final_chorus(sc) -> None:
    """THE DOUBLE FINAL CHORUS (32 bars): all thirteen channels — the
    album's fullest tutti.  Timpani and the third choir layer arrive;
    the drive guitar is 30 and the organ rides the Leslie."""
    t0 = 368.0
    _chorus_block(sc, t0, vel_lift=6, kit_x=0.88, lyrics=True,
                  bass_hook=True)
    _storm_tag(sc, t0 + 32.0, vel=102)
    _chorus_block(sc, t0 + 48.0, vel_lift=8, kit_x=0.95, china=True,
                  bass_hook=True)
    _storm_tag(sc, t0 + 80.0, vel=104, lead_fill=True)
    _coda(sc, t0 + 96.0)
    # The orchestra, across the whole double chorus:
    _choir_pad(sc, AAH, t0, FINAL_SEQ, vel=62)
    _choir_pad(sc, EH, t0, FINAL_SEQ, vel=54, lo=62, hi=84)
    _ooh_counter(sc, t0, [5, 6, 5, 6, 5, 3, 8, 6, 5, 6, 5, 3, 5, 3, 5, 8],
                 vel=56)
    en.vowel_curve(sc, AAH, [(t0, 55), (t0 + 48.0, 96), (t0 + 96.0, 108),
                             (t0 + 126.0, 84)], step=2.0)
    en.vowel_curve(sc, EH, [(t0, 30), (t0 + 32.0, 66), (t0 + 96.0, 88)],
                   step=2.0)
    _strings_bed(sc, t0, FINAL_SEQ, vel=60,
                 swell=[(t0, 72), (t0 + 32.0, 100), (t0 + 64.0, 84),
                        (t0 + 96.0, 112), (t0 + 126.0, 90)])
    _brass_hits(sc, t0, FINAL_SEQ[:24], vel=94, growl_every=4)
    _timp(sc, t0, 32)
    chords = [en.triad(D3, _MODE, d) for d in FINAL_SEQ]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=53, hi=76,
                 vel=56, legato=0.0)
    en.leslie(sc, KEYS, t0, t0 + 10.0, 24, 106)
    en.leslie(sc, KEYS, t0 + 84.0, t0 + 96.0, 106, 36)
    en.leslie(sc, KEYS, t0 + 96.0, t0 + 112.0, 36, 118)


def outro(sc) -> None:
    """The front rolls out: tutti decay, the Morse "BW" easter egg in
    the hush, then the solo piano title hook — the album ends where it
    began — under the closing ritardando."""
    t0 = 496.0
    # 1) The last big chord, decaying (drive back on 29).
    _power(sc, _gr(1), t0, 6.0, 96, jt=0)
    en.cc_curve(sc, GTR_D, 11, [(t0, 112), (t0 + 8.0, 30)], step=0.5)
    sc.note(BASS, _bp(1), t0, 7.5, 94, jt=0, jv=0)
    sc.note(TIMP, _bp(1), t0, 1.2, 96, jt=0, jv=2)
    sc.hit(49, t0, 110, jt=0)
    sc.hit(36, t0, 104, jt=0)
    for ch, deg in ((AAH, 3), (OOH, 1), (EH, 5)):
        sc.note(ch, en.pitch(D4, _MODE, deg), t0, 7.5, 52, jt=0, jv=2)
    en.vowel_curve(sc, AAH, [(t0, 84), (t0 + 7.0, 18)], step=0.5)
    for i, (deg, beat) in enumerate(((8, 2.0), (5, 4.0), (3, 6.0))):
        sc.note(PIANO, en.pitch(D4, _MODE, deg) + 12, t0 + beat, 1.5,
                58 - 6 * i, jt=2, jv=3)
    en.sustain(sc, PIANO, t0 + 0.02, t0 + 7.9)
    for k in range(4):
        sc.hit(51, t0 + 4.0 + 2.0 * k, 46 - 8 * k, jt=2)
    # 2) The hush: a held string pedal, sparse piano fifths, and the
    #    Morse "BW" tapped on the high woodblock (centre pan, quiet).
    en.pad_block(sc, STRINGS, t0 + 8.0, [en.triad(D3, _MODE, 1)] * 2,
                 12.0, size=4, lo=50, hi=76, vel=40, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0 + 8.0, 56), (t0 + 30.0, 22)], step=1.0)
    for k in range(5):
        b = t0 + 12.0 + 4.0 * k
        r = _lh(1) + (12 if k % 2 else 0)
        sc.note(PIANO, r, b, 3.5, 50 - 3 * k, jt=2, jv=2)
        sc.note(PIANO, r + 7, b + 0.02, 3.5, 44 - 3 * k, jt=2, jv=2)
        en.sustain(sc, PIANO, b + 0.04, b + 3.9)
    en.morse(sc, "BW", t0 + 18.0, drum=76, vel=38)
    # 3) The bookend: the title hook, solo piano, slowing to rest.
    en.lyric(sc, t0 + 32.0, "big weather (the sky clears)")
    _hook_piano(sc, t0 + 32.0, scale=0.88)
    # 4) The last chord: D major spread wide, pedalled, dying away.
    for p, dv in ((38, 6), (45, 2), (50, 0), (54, -2),
                  (57, -4), (62, -6), (66, -8), (69, -10)):
        sc.note(PIANO, p, t0 + 48.0, 11.5, 52 + dv, jt=0, jv=0)
    en.sustain(sc, PIANO, t0 + 48.02, t0 + 60.0)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 4, 18, 26, 29, 30, 33, 47, 48, 52, 53, 54, 61, 80}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, LEAD, KEYS, STRINGS, DRUMS,
                     BRASS, TIMP, EH}
NOTE_RANGES = {
    PIANO: (36, 94), GTR_C: (45, 84), GTR_D: (40, 70), BASS: (36, 62),
    AAH: (52, 84), OOH: (52, 86), LEAD: (58, 86), KEYS: (48, 80),
    STRINGS: (44, 86), BRASS: (48, 82), TIMP: (36, 50), EH: (55, 88),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (276.0, 296.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "chorus1", 1.0),
    ("middle8", "<=", "chorus2", 0.8),
    ("final_chorus", ">=", "chorus2", 1.05),
    ("final_chorus", ">=", "chorus1", 1.15),
    ("pre1", "<=", "chorus1", 0.9),
    ("intro", "<=", "verse1", 0.8),
    ("outro", "<=", "final_chorus", 0.45),
]
# The staircase (HLD §4): twelve gated entries across the song.
LATE_CHANNELS = {GTR_C: 32.0, BASS: 32.0, DRUMS: 32.0, GTR_D: 96.0,
                 LEAD: 128.0, KEYS: 176.0, AAH: 272.0, OOH: 272.0,
                 BRASS: 272.0, STRINGS: 320.0, TIMP: 368.0, EH: 368.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 2), ("chorus1", 2), ("verse2", 2),
                 ("chorus2", 2), ("final_chorus", 2)],
    "hook": "final_chorus",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH, EH],
    "sections": ["chorus2", "final_chorus"],
}
FEATURES_EXPECTED = {
    "cc64_sustain", "cc67_soft", "cc11_expression", "cc70_vowel",
    "cc1_leslie", "cc1_vibrato", "aftertouch", "cc2_breath",
    "cc94_echo", "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def _cell(sc, ch, t0: float, t1: float, lo: int = 0):
    """Quarter-beat-rounded (onset-offset, pitch) list for a window."""
    return sorted((round((on - t0) * 4) / 4, p)
                  for on, _off, p, _v in _spans(sc, ch)
                  if t0 - 1e-9 <= on < t1 - 1e-9 and p >= lo)


def oracles(sc, info, spans):
    # 1. hook_bookend — the outro piano statement IS the intro statement
    # (recomputed by the same _hook_piano code, never copied).
    fails_book: list[str] = []
    intro_cell = _cell(sc, PIANO, 0.0, 16.0)
    outro_cell = _cell(sc, PIANO, 528.0, 544.0)
    if not intro_cell:
        fails_book.append("no intro piano statement in [0, 16)")
    elif intro_cell != outro_cell:
        fails_book.append(
            f"outro [528,544) is not the intro statement "
            f"({len(intro_cell)} intro vs {len(outro_cell)} outro notes)")

    # 2. title_identity — the lead's chorus hook is the intro piano's
    # right hand: same melody, same octave, note for note.
    fails_id: list[str] = []
    rh = _cell(sc, PIANO, 0.0, 16.0, lo=62)
    lead1 = _cell(sc, LEAD, 128.0, 144.0)
    if not rh:
        fails_id.append("no intro piano RH melody found in [0, 16)")
    elif rh != lead1:
        fails_id.append(
            f"chorus-1 lead hook != intro piano RH "
            f"({len(rh)} piano vs {len(lead1)} lead notes)")

    # 3. tutti — the double final chorus is the album's fullest stand:
    # every 4-beat bar of [368, 496) has >= 11 channels sounding, and at
    # least 8 bars carry all thirteen at once.
    fails_tutti: list[str] = []
    per_ch = {ch: [(on, off) for on, off, _p, _v in _spans(sc, ch)]
              for ch in sc.events}
    counts = []
    b = 368.0
    while b < 496.0 - 1e-9:
        n = sum(1 for sp in per_ch.values()
                if any(on < b + 4.0 - 1e-9 and off > b + 1e-9
                       for on, off in sp))
        counts.append(n)
        b += 4.0
    if min(counts) < 11:
        fails_tutti.append(f"a final-chorus bar has only {min(counts)} "
                           f"active channels (need >= 11 in every bar)")
    full = sum(1 for c in counts if c >= 13)
    if full < 8:
        fails_tutti.append(f"only {full} bars carry all 13 channels "
                           f"(need >= 8): {counts}")

    return [("hook_bookend", fails_book),
            ("title_identity", fails_id),
            ("tutti", fails_tutti)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds FROZEN at the phase-D album freeze (2026.07.11)
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# FROZEN at the phase-D album freeze (2026.07.11): measured on the
# 2026.07.11 per-track render, ferrosintesis 0.13.x —
# lift 4.8 dB, entry rise 3.7 dB; pinned measured - >=1.2 dB slack.
_LIFT_DB = 3.5     # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): final chorus over verse 1
_RISE_DB = 2.5     # FROZEN 2026.07.11 (phase-D album render, ferrosintesis 0.13.x): RMS rise across the beat-368 tutti entry


def audio_checks(ctx):
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(40.0, 88.0)
    f0, f1 = ctx.bar_window(416.0, 488.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    fails_rise: list[str] = []
    a0, a1 = ctx.bar_window(360.0, 368.0)
    b0, b1 = ctx.bar_window(368.0, 376.0)
    before = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    after = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    if after < before + _RISE_DB:
        fails_rise.append(f"tutti entry {after:.1f} dB not >= "
                          f"{before:.1f} + {_RISE_DB} dB")

    return [("chorus_lift", fails_lift),
            ("orch_entry_rise", fails_rise)]
