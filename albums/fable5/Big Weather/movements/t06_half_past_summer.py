"""t06_half_past_summer.py — "Half Past Summer" (Big Weather, track 6).

The bass feature: sunny G-major mid-tempo pop at 112 BPM.  Rhodes EP and
two acoustic guitars (nylon left, steel right) carry a brushy groove while
THE BASS SINGS — the verse is built around a phrase-shaped countermelody
in the bass's sweet register (oracle-pinned: it recurs verse1 -> verse2),
and the chorus rides a second melodic bass figure (pinned chorus1 ->
final_chorus).  The middle-8 is the album's bass cadenza: a scheduled
program change to FRETLESS (GM35), the tempo eases to 104, the drums thin
to a heartbeat, EP pads hold, and the fretless sings six phrases of
pitch-bend slides, portamento glides and one CC68 hammer-on run
(oracle-pinned: program 35 active exactly in the middle-8, with a bend
budget).  Warm choir pads arrive in chorus 2; no brass, no timpani —
the song stays light (HLD §3 deviation allowance).

Form (HLD §4, full grammar):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 |
  middle8 (fretless cadenza, 104 BPM) | final_chorus | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 6
TITLE = "Half Past Summer"
FILE = "06 - Half Past Summer.mid"
SEED = 20260706

BPM = 112.0
CADENZA_BPM = 104.0

# Channels (HLD §3, per-track deviation: no drive gtr / brass / timpani).
EP, GTR_N, GTR_S, BASS = 0, 1, 2, 3
AAH, OOH = 4, 5
DRUMS = 9

_SECTIONS = [
    ("intro",          0.0,  24.0),
    ("verse1",        24.0,  88.0),
    ("pre1",          88.0, 104.0),
    ("chorus1",      104.0, 136.0),
    ("verse2",       136.0, 200.0),
    ("pre2",         200.0, 216.0),
    ("chorus2",      216.0, 248.0),
    ("middle8",      248.0, 296.0),
    ("final_chorus", 296.0, 360.0),
    ("outro",        360.0, 392.0),
]

MID_T0, MID_T1 = 248.0, 296.0

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM), (MID_T0, CADENZA_BPM), (MID_T1, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 0)],                      # G major, one sharp
    channels=[
        (EP,    "rhodes ep",    4,  96, 64, 50),
        (GTR_N, "nylon guitar", 24, 92, 48, 40),
        (GTR_S, "steel guitar", 25, 88, 80, 40),
        (BASS,  "bass guitar",  33, 110, 64, 25),
        (AAH,   "choir aah",    52, 86, 64, 70),
        (OOH,   "choir ooh",    53, 82, 64, 70),
        (DRUMS, "drums",        0, 104, 64, 45),
    ],
    program_changes=[
        (BASS, MID_T0, 35),     # fretless for the cadenza
        (BASS, MID_T1, 33),     # back to fingered bass for the final lift
    ],
)

# ---------------------------------------------------------------------------
# Harmony — G major (ionian).  Degrees against a G2 tonic.
# ---------------------------------------------------------------------------

G2, G3 = en.n("G2"), en.n("G3")
_MODE = "ionian"

VERSE_PROG = [1, 2, 4, 5]           # G  Am  C   D
PRE_PROG = [6, 4, 2, 5]             # Em C   Am  D
CHORUS_PROG = [1, 3, 4, 5]          # G  Bm  C   D
MID_PROG = [6, 4, 1, 5, 6, 4, 1, 3, 2, 4, 5, 5]   # one chord per bar
OUTRO_PROG = [4, 1, 4, 1, 6, 5, 1, 1]


def _root(deg: int, octave: int = 0) -> int:
    return en.pitch(G2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(G2, _MODE, deg)]


# The verse COUNTERMELODY — the song's star line, in the bass's sweet
# register (G2-G3).  (beat, degree, dur, vel) over 16 beats of G-Am-C-D;
# jt=0 throughout: pinned by the counter_recap oracle (verse1 == verse2).
_COUNTER = [
    (0.0,  1, 0.95,  98), (1.0,  3, 0.45,  90), (1.5,  4, 0.45,  92),
    (2.0,  5, 1.40, 100), (3.5,  6, 0.45,  88),
    (4.0,  6, 0.95,  96), (5.0,  5, 0.45,  88), (5.5,  3, 0.45,  86),
    (6.0,  2, 1.40,  94), (7.5,  2, 0.45,  82),
    (8.0,  4, 0.95,  96), (9.0,  5, 0.45,  90), (9.5,  6, 0.45,  92),
    (10.0, 8, 1.40, 102), (11.5, 6, 0.45,  88),
    (12.0, 5, 0.95,  96), (13.0, 4, 0.45,  88), (13.5, 3, 0.45,  86),
    (14.0, 2, 0.95,  92), (15.0, 3, 0.45,  84), (15.5, 2, 0.45,  88),
]

# The CHORUS bass figure — octave pops and turns over G-Bm-C-D, still a
# singable line.  jt=0: pinned by chorus_recap (chorus1 == final_chorus).
_CHORUS_BASS = [
    (0.0,  1, 0.70, 104), (0.75, 1, 0.20,  88), (1.0,  5, 0.45,  96),
    (1.5,  8, 0.70, 100), (2.5,  7, 0.45,  92), (3.0,  6, 0.45,  94),
    (3.5,  5, 0.45,  96),
    (4.0,  3, 0.70, 102), (4.75, 3, 0.20,  86), (5.0,  5, 0.45,  94),
    (5.5,  7, 0.70, 100), (6.5,  5, 0.45,  92), (7.0,  4, 0.45,  90),
    (7.5,  3, 0.45,  92),
    (8.0,  4, 0.70, 104), (8.75, 4, 0.20,  88), (9.0,  6, 0.45,  96),
    (9.5,  8, 0.70, 102), (10.5, 6, 0.45,  92), (11.0, 5, 0.45,  90),
    (11.5, 4, 0.45,  92),
    (12.0, 5, 0.70, 104), (12.75, 5, 0.20,  88), (13.0, 7, 0.45,  96),
    (13.5, 9, 0.95, 102), (14.5, 7, 0.45,  94), (15.0, 3, 0.45,  90),
    (15.5, 2, 0.45,  94),
]

# The pre-chorus climb — stepwise ascent into the chorus downbeat.
_PRE_BASS = [
    (0.0,  6, 0.95,  90), (1.0,  6, 0.45,  84), (1.5,  7, 0.45,  86),
    (2.0,  8, 0.95,  92), (3.0,  7, 0.45,  86), (3.5,  8, 0.45,  88),
    (4.0,  4, 0.95,  92), (5.0,  4, 0.45,  86), (5.5,  5, 0.45,  88),
    (6.0,  6, 0.95,  94), (7.0,  5, 0.45,  88), (7.5,  4, 0.45,  90),
    (8.0,  2, 0.95,  94), (9.0,  2, 0.45,  88), (9.5,  3, 0.45,  90),
    (10.0, 4, 0.95,  96), (11.0, 3, 0.45,  92), (11.5, 2, 0.45,  94),
    (12.0, 5, 0.70,  98), (12.75, 5, 0.45,  92), (13.5, 5, 0.45,  96),
    (14.0, 6, 0.45,  98), (14.5, 7, 0.45, 100), (15.0, 8, 0.45, 102),
    (15.5, 9, 0.45, 104),
]

_CHORUS_LYRICS = ["half past summer", "gold to the rim"]


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _bass_line(sc, t0: float, table, reps: int = 1, vel_add: int = 0) -> None:
    """State a (beat, degree, dur, vel) bass table; jt=0 (oracle-pinned)."""
    for r in range(reps):
        base = t0 + 16.0 * r
        for beat, deg, dur, vel in table:
            sc.note(BASS, _root(deg), base + beat, dur,
                    min(127, vel + vel_add), jt=0, jv=2)


def _ep_fill(sc, t0: float, vel: int) -> None:
    """A five-note EP answer figure with a CC94 echo throw."""
    for beat, p, dur in ((0.0, 74, 0.4), (0.5, 71, 0.4), (0.75, 69, 0.4),
                         (1.0, 67, 0.8), (1.5, 71, 0.6)):
        sc.note(EP, p, t0 + beat, dur, vel - (6 if beat > 1.0 else 0),
                jt=2, jv=3)
    en.echo_throw(sc, EP, t0, base=0, peak=74, release=2.0)


def _ep_verse(sc, t0: float, bars: int, prog, vel: int = 66) -> None:
    """Verse EP: LH root, syncopated RH triads, pedalled every bar."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        sc.note(EP, r, b, 1.9, vel + 4, jt=3, jv=4)
        for beat, dur in ((1.5, 0.9), (2.5, 1.4)):
            for p in tri:
                sc.note(EP, p, b + beat, dur, vel - 6, jt=3, jv=4)
        en.sustain(sc, EP, b + 0.02, b + 3.9)


def _ep_anthem(sc, t0: float, bars: int, prog, vel: int = 84) -> None:
    """Chorus EP: block chords with an octave crown, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            sc.note(EP, r, b + beat, dur, vel, jt=3, jv=4)
            for p in tri:
                sc.note(EP, p, b + beat, dur, vel - 5, jt=3, jv=4)
        sc.note(EP, tri[0] + 12, b + 3.0, 0.9, vel + 2, jt=3, jv=4)
        en.sustain(sc, EP, b + 0.02, b + 3.9)


def _ep_pads(sc, t0: float, bars: int, prog, vel: int = 46) -> None:
    """Held voice-led EP bed (the cadenza's cushion)."""
    chords = [en.triad(G3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, EP, t0, chords, 4.0, size=3, lo=55, hi=74,
                 vel=vel, legato=0.0)


def _nylon_pick(sc, t0: float, bars: int, prog, vel: int = 58) -> None:
    """Nylon guitar: fingerpicked eighths, root-fifth-tenth lattice."""
    pattern = [0, 7, 12, 16, 12, 7, 12, 7]
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)], octave=1)
        for k, off in enumerate(pattern):
            sc.note(GTR_N, r + off, b + 0.5 * k, 0.42,
                    vel - (0 if k % 2 == 0 else 8), jt=3, jv=4)


def _nylon_strum(sc, t0: float, bars: int, prog, vel: int = 70) -> None:
    """Nylon guitar: open eighth strums, down-up."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        chord = tri + [tri[0] + 12]
        for k in range(8):
            en.strum(sc, GTR_N, chord, b + 0.5 * k, 0.46,
                     vel - (0 if k % 2 == 0 else 12), spread=0.02,
                     down=k % 2 == 0)


def _steel_dyads(sc, t0: float, bars: int, prog, vel: int = 52) -> None:
    """Steel guitar: off-beat double stops (the jangle answer)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=2)
        for beat in (1.5, 3.5):
            sc.note(GTR_S, tri[0], b + beat, 0.4, vel, jt=3, jv=4)
            sc.note(GTR_S, tri[1], b + beat, 0.4, vel - 6, jt=3, jv=4)


def _steel_chops(sc, t0: float, bars: int, prog, vel: int = 74,
                 turn: bool = True) -> None:
    """Steel guitar: chorus chops on the &s plus a 16th turn each 4th bar."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=2)
        for beat in (1.5, 2.5, 3.5):
            en.strum(sc, GTR_S, tri, b + beat, 0.4,
                     vel - (8 if beat == 2.5 else 0), spread=0.015)
        if turn and i % 4 == 3:
            for k, p in enumerate((tri[0], tri[1], tri[2], tri[1])):
                sc.note(GTR_S, p, b + 3.0 + 0.25 * k, 0.28, vel - 10,
                        jt=2, jv=3)


def _choir(sc, t0: float, bars: int, prog, vel: int = 54) -> None:
    """Warm layered choir: aah pad (3 voices) + a long ooh counter-line."""
    chords = [en.triad(G3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=57, hi=76,
                 vel=vel, legato=0.0)
    degs = [5, 6, 4, 5]
    for i in range(bars // 2):
        d = degs[i % len(degs)]
        sc.note(OOH, en.pitch(G3, _MODE, d) + 12, t0 + 8.0 * i, 7.5,
                vel - 4, jt=0, jv=3)


def _brush(sc, t0: float, bars: int, intensity: float, *,
           backbeat: str = "rim", tamb: bool = False, ride: bool = False,
           crash_in: bool = False, fills: bool = True,
           hat: bool = True) -> None:
    """The brushy kit: low velocities, rim clicks, ghosts, gentle fills."""
    v = int(round(en.lerp(50, 86, intensity)))
    for i in range(bars):
        b = t0 + 4.0 * i
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        if crash_in and first:
            sc.hit(49, b, min(112, v + 10), jt=0)
        sc.hit(36, b, v + 6, jt=2)
        sc.hit(36, b + 2.5, v, jt=2)
        key = 37 if backbeat == "rim" else 38
        sc.hit(key, b + 1.0, v + 6, jt=2, jv=4)
        sc.hit(key, b + 3.0, v + 6, jt=2, jv=4)
        if intensity < 0.8:
            sc.hit(key, b + 2.75, max(14, v - 38), jt=3, jv=6)   # ghost
        if hat:
            hk = 51 if ride else 42
            for k in range(8):
                hv = v - (12 if k % 2 == 0 else 26)
                if fill_bar and k >= 5:
                    continue
                sc.hit(hk, b + 0.5 * k, max(16, hv), jt=2, jv=5)
            if not ride and not fill_bar and i % 2 == 1:
                sc.hit(46, b + 3.5, v - 20, jt=2)
        if tamb:
            for k in range(8):
                tv = v - (18 if k % 2 == 0 else 30)
                sc.hit(54, b + 0.5 * k, max(16, tv), jt=2, jv=4)
        if fill_bar:
            for k, key2 in enumerate((48, 47, 45, 43)):
                sc.hit(key2, b + 3.0 + 0.25 * k,
                       int(en.lerp(v - 16, v + 8, k / 3)), jt=2)


def _slide_in(sc, t0: float, semis: float = -1.5, glide: float = 0.5) -> None:
    """Fretless slide INTO the note starting at t0 (bend from below)."""
    sc.bend(BASS, t0, semis)
    en.bend_ramp(sc, BASS, t0 + 0.02, t0 + glide, semis, 0.0, steps=8)


def _fall_off(sc, t0: float, t1: float, semis: float = -1.8) -> None:
    """Fretless fall at a note's tail; recentres just after the note-off."""
    en.bend_ramp(sc, BASS, t0, t1, 0.0, semis, steps=8)
    sc.bend(BASS, t1 + 0.1, 0.0)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    # Bars 1-2: EP alone — a Gmaj9 shimmer, then a Cmaj9 answer.
    sc.cc(EP, 11, 104, 0.0)
    for p in (55, 62, 66, 71):
        sc.note(EP, p, 0.0, 3.8, 62, jt=0, jv=3)
    for k, p in enumerate((62, 66, 71, 74)):
        sc.note(EP, p, 1.0 + 0.5 * k, 0.6, 54, jt=3, jv=3)
    en.sustain(sc, EP, 0.02, 3.9)
    for p in (60, 67, 71, 74):
        sc.note(EP, p, 4.0, 3.8, 60, jt=2, jv=3)
    en.sustain(sc, EP, 4.02, 7.9)
    _nylon_pick(sc, 4.0, 1, [4], vel=52)
    # Bars 3-4: brushes and the steel shimmer arrive.
    _ep_verse(sc, 8.0, 2, [1, 4], vel=62)
    _nylon_pick(sc, 8.0, 2, [1, 4], vel=54)
    _brush(sc, 8.0, 2, 0.35, fills=False)
    en.cc_curve(sc, GTR_S, 74, [(8.0, 36), (16.0, 78)], step=1.0)
    for k, p in enumerate((67, 71, 74, 79)):
        sc.note(GTR_S, p, 8.0 + 2.0 * k, 1.8, 48, jt=3, jv=3)
    # Bass pickup: a stepwise approach out of the haze...
    sc.note(BASS, _root(3), 14.0, 0.45, 84, jt=0, jv=2)
    sc.note(BASS, _root(2), 14.5, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, _root(2), 15.5, 0.45, 90, jt=0, jv=2)
    # ...then bars 5-6 preview the countermelody's first half (over G, Am).
    for beat, deg, dur, vel in _COUNTER[:10]:
        if beat < 8.0:
            sc.note(BASS, _root(deg), 16.0 + beat, dur, vel - 8, jt=0, jv=2)
    _ep_verse(sc, 16.0, 2, [1, 2], vel=64)
    _nylon_pick(sc, 16.0, 2, [1, 2], vel=56)
    _brush(sc, 16.0, 2, 0.45, fills=False)
    _ep_fill(sc, 22.0, 66)


def verse1(sc) -> None:
    t0 = 24.0
    sc.cc(EP, 11, 100, t0)
    sc.cc(GTR_S, 74, 56, t0)
    _ep_verse(sc, t0, 16, VERSE_PROG)
    _nylon_pick(sc, t0, 16, VERSE_PROG)
    _steel_dyads(sc, t0 + 32.0, 8, VERSE_PROG, vel=50)
    _bass_line(sc, t0, _COUNTER, reps=4)
    _brush(sc, t0, 16, 0.5)
    _ep_fill(sc, t0 + 30.0, 66)
    _ep_fill(sc, t0 + 62.0, 70)


def _pre(sc, t0: float) -> None:
    for i, deg in enumerate(PRE_PROG):
        b = t0 + 4.0 * i
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        for beat in (0.0, 2.0):
            sc.note(EP, r, b + beat, 1.9, 74 + 3 * i, jt=3, jv=4)
            for p in tri:
                sc.note(EP, p, b + beat, 1.9, 68 + 3 * i, jt=3, jv=4)
        en.sustain(sc, EP, b + 0.02, b + 3.9)
    en.expr_curve(sc, EP, [(t0, 100), (t0 + 15.5, 120)], step=1.0)
    _bass_line(sc, t0, _PRE_BASS)
    _nylon_strum(sc, t0, 4, PRE_PROG, vel=64)
    _steel_dyads(sc, t0, 4, PRE_PROG, vel=56)
    en.cc_curve(sc, GTR_S, 74, [(t0, 46), (t0 + 15.5, 112)], step=1.0)
    _brush(sc, t0, 4, 0.6, backbeat="snare", crash_in=True)


def pre1(sc) -> None:
    _pre(sc, 88.0)


def _chorus(sc, t0: float, *, vel_lift: int = 0, choir: bool = False,
            lyric: str | None = None, ride: bool = False) -> None:
    sc.cc(EP, 11, min(127, 116 + vel_lift), t0)
    sc.cc(GTR_S, 74, 108, t0)
    _ep_anthem(sc, t0, 8, CHORUS_PROG, vel=84 + vel_lift)
    _nylon_strum(sc, t0, 8, CHORUS_PROG, vel=70 + vel_lift)
    _steel_chops(sc, t0, 8, CHORUS_PROG, vel=74 + vel_lift)
    _bass_line(sc, t0, _CHORUS_BASS, reps=2, vel_add=vel_lift)
    _brush(sc, t0, 8, 0.75 + vel_lift / 60.0, backbeat="snare",
           tamb=True, ride=ride, crash_in=True)
    _ep_fill(sc, t0 + 30.0, 72 + vel_lift)
    if choir:
        _choir(sc, t0, 8, CHORUS_PROG, vel=54)
    if lyric:
        en.lyric(sc, t0, lyric)


def chorus1(sc) -> None:
    _chorus(sc, 104.0, lyric=_CHORUS_LYRICS[0])


def verse2(sc) -> None:
    t0 = 136.0
    sc.cc(EP, 11, 102, t0)
    sc.cc(GTR_S, 74, 60, t0)
    _ep_verse(sc, t0, 16, VERSE_PROG)
    _nylon_pick(sc, t0, 16, VERSE_PROG)
    _steel_dyads(sc, t0, 16, VERSE_PROG, vel=50)
    _bass_line(sc, t0, _COUNTER, reps=4)
    _brush(sc, t0, 8, 0.5)
    _brush(sc, t0 + 32.0, 8, 0.55, ride=True)
    _ep_fill(sc, t0 + 30.0, 68)
    _ep_fill(sc, t0 + 62.0, 70)


def pre2(sc) -> None:
    _pre(sc, 200.0)


def chorus2(sc) -> None:
    t0 = 216.0
    _chorus(sc, t0, lyric=_CHORUS_LYRICS[0])
    _choir(sc, t0, 8, CHORUS_PROG, vel=50)
    en.vowel_curve(sc, AAH, [(t0, 44), (t0 + 24.0, 80), (t0 + 31.0, 60)],
                   step=2.0)


def middle8(sc) -> None:
    """The bass cadenza: fretless (GM35), portamento glides, slides."""
    t0 = MID_T0
    en.portamento_on(sc, BASS, t0, time_cc=55)
    # The cushion: EP pads swelling gently, a heartbeat kit, nothing else.
    _ep_pads(sc, t0, 12, MID_PROG, vel=46)
    en.expr_curve(sc, EP, [(t0, 72), (t0 + 24.0, 92), (t0 + 47.0, 108)],
                  step=2.0)
    en.sustain(sc, EP, t0 + 0.02, t0 + 47.5)
    sc.hit(49, t0, 62, jt=0)
    for i in range(12):
        b = t0 + 4.0 * i
        sc.hit(36, b, 52 if i else 58, jt=0 if i == 0 else 2)
        sc.hit(37, b + 2.0, 42, jt=2)
        if i >= 8:
            for k in range(8):
                sc.hit(42, b + 0.5 * k, max(16, 26 - (6 if k % 2 else 0)),
                       jt=2, jv=4)
    for k, key in enumerate((48, 47, 45, 43)):
        sc.hit(key, t0 + 47.0 + 0.25 * k, int(en.lerp(48, 76, k / 3)), jt=2)

    # Phrase 1 (Em -> C): slide up into E3, sigh back down.
    _slide_in(sc, t0 + 0.5, -1.5, 0.6)
    sc.note(BASS, 52, t0 + 0.5, 2.4, 88, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 1.6, 1.2, depth=0.18, cycles_per_beat=0.9)
    sc.note(BASS, 47, t0 + 3.0, 0.45, 80, jt=0, jv=2)
    sc.note(BASS, 45, t0 + 3.5, 0.45, 78, jt=0, jv=2)
    sc.note(BASS, 43, t0 + 4.0, 1.9, 86, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 4.9, 0.9, depth=0.16, cycles_per_beat=0.9)
    sc.note(BASS, 48, t0 + 6.5, 0.7, 84, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 7.25, 0.7, 88, jt=0, jv=2)
    # Phrase 2 (G -> D): up to B3, fall away off D3.
    _slide_in(sc, t0 + 8.0, -2.0, 0.35)
    sc.note(BASS, 59, t0 + 8.0, 1.4, 94, jt=0, jv=0)
    sc.note(BASS, 57, t0 + 9.5, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, 55, t0 + 10.0, 1.4, 90, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 10.6, 0.7, depth=0.15, cycles_per_beat=0.9)
    sc.note(BASS, 54, t0 + 11.5, 0.45, 84, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 12.0, 1.9, 90, jt=0, jv=0)
    _fall_off(sc, t0 + 13.4, t0 + 13.9)
    sc.note(BASS, 45, t0 + 14.5, 0.45, 80, jt=0, jv=2)
    sc.note(BASS, 47, t0 + 15.0, 0.45, 84, jt=0, jv=2)
    sc.note(BASS, 48, t0 + 15.5, 0.45, 86, jt=0, jv=2)
    # Phrase 3 (Em -> C): the high song — up to C4.
    sc.note(BASS, 52, t0 + 16.0, 0.7, 90, jt=0, jv=2)
    sc.note(BASS, 54, t0 + 16.75, 0.45, 88, jt=0, jv=2)
    sc.note(BASS, 55, t0 + 17.5, 0.7, 92, jt=0, jv=2)
    sc.note(BASS, 59, t0 + 18.5, 1.4, 96, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 19.2, 0.6, depth=0.15, cycles_per_beat=0.9)
    _slide_in(sc, t0 + 20.0, -2.0, 0.4)
    sc.note(BASS, 60, t0 + 20.0, 1.8, 98, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 20.9, 0.8, depth=0.18, cycles_per_beat=0.9)
    sc.note(BASS, 57, t0 + 22.0, 0.45, 88, jt=0, jv=2)
    sc.note(BASS, 55, t0 + 22.5, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, 52, t0 + 23.0, 0.95, 88, jt=0, jv=2)
    # Phrase 4 (G -> Bm): the hammer-on run (CC68) up to a held G3.
    en.run(sc, BASS, t0 + 24.0, G2, _MODE, [1, 2, 3, 4, 5, 6, 7],
           0.25, 78, 100, legato=True)
    sc.note(BASS, 55, t0 + 26.0, 1.9, 100, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 26.9, 0.9, depth=0.18, cycles_per_beat=0.9)
    sc.note(BASS, 54, t0 + 28.0, 0.7, 92, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 28.75, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, 47, t0 + 29.5, 0.7, 88, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 30.0, 0.95, 90, jt=0, jv=2)
    sc.note(BASS, 47, t0 + 31.0, 0.95, 86, jt=0, jv=2)
    # Phrase 5 (Am -> C): the countermelody, quoted by the fretless.
    sc.note(BASS, 45, t0 + 32.0, 0.95, 90, jt=0, jv=2)
    sc.note(BASS, 47, t0 + 33.0, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, 48, t0 + 33.5, 0.45, 88, jt=0, jv=2)
    sc.note(BASS, 52, t0 + 34.0, 1.4, 94, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 34.7, 0.6, depth=0.15, cycles_per_beat=0.9)
    sc.note(BASS, 50, t0 + 35.5, 0.45, 86, jt=0, jv=2)
    sc.note(BASS, 48, t0 + 36.0, 0.95, 90, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 37.0, 0.45, 88, jt=0, jv=2)
    sc.note(BASS, 52, t0 + 37.5, 0.45, 90, jt=0, jv=2)
    _slide_in(sc, t0 + 38.0, -2.0, 0.4)
    sc.note(BASS, 55, t0 + 38.0, 1.4, 96, jt=0, jv=0)
    sc.note(BASS, 52, t0 + 39.5, 0.45, 88, jt=0, jv=2)
    # Phrase 6 (D pedal): the climb to D4 and the cliff-hanger fall.
    sc.note(BASS, 50, t0 + 40.0, 0.7, 92, jt=0, jv=2)
    sc.note(BASS, 52, t0 + 40.75, 0.45, 90, jt=0, jv=2)
    sc.note(BASS, 54, t0 + 41.5, 0.7, 94, jt=0, jv=2)
    sc.note(BASS, 57, t0 + 42.5, 0.7, 96, jt=0, jv=2)
    sc.note(BASS, 59, t0 + 43.25, 0.7, 98, jt=0, jv=2)
    _slide_in(sc, t0 + 44.0, -2.0, 0.4)
    sc.note(BASS, 62, t0 + 44.0, 3.0, 102, jt=0, jv=0)
    en.vibrato(sc, BASS, t0 + 45.2, 1.1, depth=0.2, cycles_per_beat=0.9)
    _fall_off(sc, t0 + 46.4, t0 + 47.0)
    sc.note(BASS, 50, t0 + 47.5, 0.45, 96, jt=0, jv=2)
    en.portamento_off(sc, BASS, t0 + 47.6)


def final_chorus(sc) -> None:
    t0 = 296.0
    sc.cc(EP, 11, 124, t0)
    sc.cc(GTR_S, 74, 112, t0)
    _ep_anthem(sc, t0, 16, CHORUS_PROG, vel=93)
    _nylon_strum(sc, t0, 16, CHORUS_PROG, vel=79)
    _steel_chops(sc, t0, 16, CHORUS_PROG, vel=83)
    # Bass: the chorus figure restated (pinned), then the countermelody
    # sung OVER the chorus changes — the song's two hooks meet.
    _bass_line(sc, t0, _CHORUS_BASS, reps=2, vel_add=6)
    _bass_line(sc, t0 + 32.0, _COUNTER, reps=2, vel_add=10)
    _brush(sc, t0, 8, 0.9, backbeat="snare", tamb=True, crash_in=True)
    _brush(sc, t0 + 32.0, 8, 0.95, backbeat="snare", tamb=True, ride=True,
           crash_in=True)
    _choir(sc, t0, 16, CHORUS_PROG, vel=62)
    en.vowel_curve(sc, AAH, [(t0, 50), (t0 + 40.0, 96), (t0 + 62.0, 80)],
                   step=2.0)
    _ep_fill(sc, t0 + 30.0, 76)
    _ep_fill(sc, t0 + 62.0, 78)
    en.lyric(sc, t0, _CHORUS_LYRICS[0])
    en.lyric(sc, t0 + 32.0, _CHORUS_LYRICS[1])


def outro(sc) -> None:
    t0 = 360.0
    en.expr_curve(sc, EP, [(t0, 100), (t0 + 28.0, 60), (t0 + 31.5, 36)],
                  step=1.0)
    sc.cc(GTR_S, 74, 64, t0)
    # Bars 1-4: the countermelody's first half says goodnight (C, G).
    for r in range(2):
        for beat, deg, dur, vel in _COUNTER[:10]:
            if beat < 8.0:
                sc.note(BASS, _root(deg), t0 + 8.0 * r + beat, dur,
                        vel - 14, jt=0, jv=2)
    _ep_verse(sc, t0, 4, OUTRO_PROG[:4], vel=58)
    _nylon_pick(sc, t0, 4, OUTRO_PROG[:4], vel=50)
    for k, p in enumerate((74, 71, 67, 71)):
        sc.note(GTR_S, p, t0 + 4.0 * k + 2.0, 1.6, 44, jt=3, jv=3)
    _brush(sc, t0, 4, 0.35, fills=False)
    # Bars 5-6: Em, D — the bass eases down; brushes to a heartbeat.
    sc.note(BASS, 52, t0 + 16.0, 1.9, 76, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 18.0, 1.9, 74, jt=0, jv=2)
    sc.note(BASS, 50, t0 + 20.0, 1.4, 72, jt=0, jv=2)
    sc.note(BASS, 45, t0 + 21.5, 0.95, 70, jt=0, jv=2)
    sc.note(BASS, 47, t0 + 22.5, 0.7, 68, jt=0, jv=2)
    sc.note(BASS, 43, t0 + 23.25, 0.7, 70, jt=0, jv=2)
    _ep_verse(sc, t0 + 16.0, 2, OUTRO_PROG[4:6], vel=54)
    _nylon_pick(sc, t0 + 16.0, 2, OUTRO_PROG[4:6], vel=46)
    for i in range(2):
        b = t0 + 16.0 + 4.0 * i
        sc.hit(36, b, 46, jt=2)
        sc.hit(37, b + 2.0, 38, jt=2)
    # Bars 7-8: one long G — EP chord, low G held, a soft crash, done.
    sc.note(BASS, 43, t0 + 24.0, 6.0, 74, jt=0, jv=0)
    for p in (55, 62, 66, 71):
        sc.note(EP, p, t0 + 24.0, 7.5, 56, jt=0, jv=3)
    en.sustain(sc, EP, t0 + 24.02, t0 + 31.8)
    for k, p in enumerate((67, 71, 74)):
        sc.note(GTR_N, p, t0 + 24.0 + 0.5 * k, 3.0, 48, jt=0, jv=3)
    sc.hit(49, t0 + 24.0, 64, jt=0)
    sc.hit(36, t0 + 24.0, 58, jt=0)
    sc.hit(46, t0 + 28.0, 32, jt=0)
    en.lyric(sc, t0 + 24.0, _CHORUS_LYRICS[0])


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {4, 24, 25, 33, 35, 52, 53}
CENTERED_CHANNELS = {EP, BASS, AAH, OOH, DRUMS}
NOTE_RANGES = {
    EP: (48, 88), GTR_N: (48, 84), GTR_S: (52, 88), BASS: (40, 64),
    AAH: (55, 79), OOH: (55, 79),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (203.0, 223.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "verse2", 1.2),
    ("middle8", "<=", "chorus2", 0.7),
    ("final_chorus", ">=", "chorus1", 1.05),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("intro", "<=", "chorus1", 0.9),
    ("pre1", "<=", "chorus1", 1.0),
    ("outro", "<=", "final_chorus", 0.7),
]
LATE_CHANNELS = {AAH: 216.0, OOH: 216.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 7), ("chorus1", 7), ("verse2", 7),
                 ("chorus2", 7), ("middle8", 4)],
    "hook": "middle8",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH],
    "sections": ["chorus2", "final_chorus"],
}
FEATURES_EXPECTED = {
    "portamento", "pitch_bend", "cc68_legato", "cc64_sustain", "cc74_wah",
    "cc11_expression", "cc70_vowel", "cc94_echo", "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _bass_onsets(sc, t0: float, t1: float):
    """Sorted (relative onset on a 16th grid, pitch) for the bass line."""
    import verify
    return sorted((round((on - t0) * 4) / 4, p)
                  for on, _off, p, _v in verify._note_spans(sc, BASS)
                  if t0 - 1e-9 <= on < t1 - 1e-9)


def oracles(sc, info, spans):
    import verify

    # 1. The verse countermelody recurs verse1 -> verse2 (recompute pin).
    fails_counter: list[str] = []
    v1 = _bass_onsets(sc, 24.0, 88.0)
    v2 = _bass_onsets(sc, 136.0, 200.0)
    if not v1 or v1 != v2:
        fails_counter.append(
            f"verse bass countermelody differs verse1 vs verse2 "
            f"({len(v1)} vs {len(v2)} notes)")

    # 2. The chorus bass figure recurs chorus1 -> final_chorus bars 1-8.
    fails_chorus: list[str] = []
    c1 = _bass_onsets(sc, 104.0, 136.0)
    fc = _bass_onsets(sc, 296.0, 328.0)
    if not c1 or c1 != fc:
        fails_chorus.append(
            f"chorus bass figure differs chorus1 vs final_chorus "
            f"({len(c1)} vs {len(fc)} notes)")

    # 3. The fretless cadenza: program 35 active EXACTLY in the middle-8,
    #    with a real bend budget and the portamento pedal down inside it.
    fails_fretless: list[str] = []
    progs = verify._programs(sc, BASS)
    fret = sorted(b for b, p in progs if p == 35)
    if fret != [MID_T0]:
        fails_fretless.append(f"program 35 events at {fret}, want exactly "
                              f"[{MID_T0}]")
    if not any(abs(b - MID_T1) < 1e-6 and p == 33 for b, p in progs):
        fails_fretless.append(f"no return to program 33 at beat {MID_T1}")
    bends = [(b, f) for b, f in verify._bend_fracs(sc, BASS)
             if MID_T0 - 1e-9 <= b < MID_T1]
    outside = [f for b, f in verify._bend_fracs(sc, BASS)
               if not MID_T0 - 1e-9 <= b < MID_T1 and abs(f) > 0.02]
    if len(bends) < 24:
        fails_fretless.append(f"{len(bends)} bend events in the cadenza "
                              f"(< 24)")
    if len({round(f, 2) for _b, f in bends}) < 5:
        fails_fretless.append("fewer than 5 distinct bend values in the "
                              "cadenza")
    if outside:
        fails_fretless.append(f"{len(outside)} non-zero bass bends outside "
                              f"the cadenza window")
    port = [(b, v) for b, v in verify._cc_events(sc, BASS, 65)]
    if not any(v >= 64 and MID_T0 - 1e-9 <= b < MID_T1 for b, v in port):
        fails_fretless.append("portamento (CC65) never engaged in the "
                              "cadenza")
    if not any(v < 64 and b <= MID_T1 for b, v in port):
        fails_fretless.append("portamento (CC65) never released")

    return [("counter_recap", fails_counter),
            ("chorus_recap", fails_chorus),
            ("fretless_cadenza", fails_fretless)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# PROVISIONAL pins (2026.07.11, per-track render, ferrosintesis v0.13.x;
# re-pinned at the phase-D assembled-album freeze).  Measured: lift
# 4.45 dB, dip 9.07 dB, re-entry 11.47 dB — pinned at measured - slack.
_LIFT_DB = 3.0          # final chorus over verse 1 (measured 4.45)
_DIP_DB = 7.0           # cadenza below chorus 2 (measured 9.07)
_REENTRY_DB = 9.0       # final-chorus slam over the cadenza (meas. 11.47)


def audio_checks(ctx):
    # 1. Chorus lift: the final chorus rises over verse 1.
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(24.0, 88.0)
    f0, f1 = ctx.bar_window(296.0, 360.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # 2. The cadenza window really is a featured step-back: the mix drops
    #    well below chorus 2 for the fretless, then the final chorus SLAMS
    #    back in over it (measured-direction contrasts, HLD §6.2 style —
    #    a low-band-fraction probe was tried and measured BACKWARDS: the
    #    fretless sings at 98-590 Hz, above a bass-band corner, so the
    #    full chorus mix is the "bassier" window; repo lesson applied).
    fails_cad: list[str] = []
    m0, m1 = ctx.bar_window(MID_T0, MID_T1)
    c0, c1 = ctx.bar_window(216.0, 248.0)
    r0, r1 = ctx.bar_window(296.0, 304.0)
    mid = ctx.db(ctx.rms(ctx.l, ctx.r, m0, m1))
    cho = ctx.db(ctx.rms(ctx.l, ctx.r, c0, c1))
    ree = ctx.db(ctx.rms(ctx.l, ctx.r, r0, r1))
    if mid > cho - _DIP_DB:
        fails_cad.append(f"cadenza {mid:.1f} dB not <= chorus2 "
                         f"{cho:.1f} dB - {_DIP_DB}")
    if ree < mid + _REENTRY_DB:
        fails_cad.append(f"re-entry {ree:.1f} dB not >= cadenza "
                         f"{mid:.1f} dB + {_REENTRY_DB}")

    return [("chorus_lift", fails_lift),
            ("fretless_cadenza_window", fails_cad)]
