"""t01_first_light_freeway.py — "First Light Freeway" (Big Weather, track 1).

The opener: E-major driving pop-rock at 126 BPM.  A mixolydian-edged
drive-guitar RIFF bookends the song (intro/outro, oracle-pinned); verses
walk a melodic bass under clean-guitar eighths and off-beat piano; the
chorus HOOK is sung by the lead synth and — in the final chorus — doubled
note-for-note by the bass an octave down (oracle-pinned).  Brass and the
layered choir arrive in chorus 2, strings in the middle-8, timpani in the
final chorus (LATE_CHANNELS gates all four).  The lead break sets a
12-semitone bend range and dives a full octave+ into the last choruses.

Form (HLD §4, full grammar):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 | middle8 |
  lead_break | final_chorus | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 1
TITLE = "First Light Freeway"
FILE = "01 - First Light Freeway.mid"
SEED = 20260701

BPM = 126.0

# Channels (HLD §3).
PIANO, GTR_L, GTR_R, BASS = 0, 1, 2, 3
AAH, OOH, LEAD, KEYS = 4, 5, 6, 7
STRINGS, DRUMS, BRASS, TIMP = 8, 9, 10, 11

_SECTIONS = [
    ("intro",        0.0,  32.0),
    ("verse1",      32.0,  96.0),
    ("pre1",        96.0, 128.0),
    ("chorus1",    128.0, 192.0),
    ("verse2",     192.0, 224.0),
    ("pre2",       224.0, 256.0),
    ("chorus2",    256.0, 320.0),
    ("middle8",    320.0, 352.0),
    ("lead_break", 352.0, 384.0),
    ("final_chorus", 384.0, 464.0),
    ("outro",      464.0, 504.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 4, 0)],                      # E major, four sharps
    channels=[
        (PIANO,   "piano",        0, 100, 64, 50),
        (GTR_L,   "clean guitar", 26,  96, 48, 40),
        (GTR_R,   "drive guitar", 29,  92, 80, 35),
        (BASS,    "bass guitar",  33, 105, 64, 25),
        (AAH,     "choir aah",    52,  88, 64, 70),
        (OOH,     "choir ooh",    53,  84, 64, 70),
        (LEAD,    "lead synth",   81,  92, 64, 45),
        (KEYS,    "ep / organ",    4,  84, 64, 45),
        (STRINGS, "strings",      48,  86, 64, 65),
        (DRUMS,   "drums",         0, 108, 64, 45),
        (BRASS,   "brass",        61,  92, 64, 45),
        (TIMP,    "timpani",      47,  96, 64, 60),
    ],
    program_changes=[
        (KEYS,  256.0, 18),     # EP -> driven rock organ for chorus 2 on
        (GTR_R, 384.0, 30),     # overdrive -> full distortion, final lift
        (GTR_R, 464.0, 29),     # back to overdrive for the outro riff
    ],
)

# ---------------------------------------------------------------------------
# Harmony — E major.  Degrees against an E tonic (ionian).
# ---------------------------------------------------------------------------

E2, E3, E4 = en.n("E2"), en.n("E3"), en.n("E4")
_MODE = "ionian"

VERSE_PROG = [1, 6, 4, 5]           # E   C#m  A    B
PRE_PROG = [4, 5, 6, 5]             # A   B    C#m  B
CHORUS_PROG = [1, 5, 6, 4]          # E   B    C#m  A
MID_PROG = [6, 4, 1, 5, 6, 4, 2, 5]  # C#m A E B | C#m A F#m B


def _root(deg: int, octave: int = 0) -> int:
    return en.pitch(E2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(E2, _MODE, deg)]


# The RIFF — the drive guitar's bookend hook (E mixolydian bite: G and D
# naturals against the E-major key).  (beat, semitone offset from E, dur,
# vel, power?) — jt=0 throughout: the riff is oracle-pinned (riff_recap).
_RIFF = [
    (0.00,  0, 0.70, 106, True),
    (0.75,  0, 0.45,  96, True),
    (1.50,  3, 0.45, 100, True),    # G5 — the borrowed bIII
    (2.00,  5, 0.95, 104, True),    # A5
    (3.00, 12, 0.30,  92, False),   # single-note turn: E3
    (3.33, 10, 0.30,  88, False),   # D3
    (3.66,  7, 0.30,  90, False),   # B2
    (4.00,  0, 0.70, 106, True),
    (4.75,  0, 0.45,  96, True),
    (5.50, -2, 0.45, 100, True),    # D5 — the mixolydian bVII
    (6.50,  5, 0.45, 102, True),
    (7.00,  7, 0.95, 104, True),    # B5 turns the corner home
]

# The chorus HOOK — (degree, start, dur) over 16 beats (E B C#m A), sung
# by the lead and, in the final chorus, doubled by the bass an octave
# down (oracle: hook_doubling).  Long notes get a CC1 vibrato bloom.
_HOOK = [
    (5, 0.0, 0.75), (5, 0.75, 0.25), (6, 1.0, 1.0), (5, 2.0, 1.5),
    (3, 3.5, 0.5),
    (2, 4.0, 0.75), (2, 4.75, 0.25), (5, 5.0, 1.0), (4, 6.0, 2.0),
    (3, 8.0, 0.75), (3, 8.75, 0.25), (4, 9.0, 1.0), (5, 10.0, 2.0),
    (6, 12.0, 1.0), (5, 13.0, 0.5), (4, 13.5, 0.5), (3, 14.0, 1.9),
]

_HOOK_LYRICS = ["first light", "freeway", "hold the lane", "till morning"]


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
                _power(sc, GTR_R, E2 + off, base + beat, dur, v)
            else:
                sc.note(GTR_R, E3 + off, base + beat, dur, v, jt=0, jv=3)


def _drums(sc, t0: float, bars: int, intensity: float, *,
           ride: bool = False, crash_in: bool = False,
           china: bool = False, fills: bool = True) -> None:
    """The kit groove.  intensity 0..1 scales velocity and busy-ness."""
    for i in range(bars):
        b = t0 + 4.0 * i
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        v = int(round(en.lerp(72, 104, intensity)))
        if crash_in and first:
            sc.hit(49, b, min(120, v + 14), jt=0)
        if china and i % 4 == 0 and not first:
            sc.hit(52, b, v + 6, jt=2)
        # Kick.
        sc.hit(36, b, v + 8, jt=2)
        sc.hit(36, b + 2.5, v + 2, jt=2)
        if intensity > 0.6 and i % 2 == 1:
            sc.hit(36, b + 3.75, v - 4, jt=2)
        # Snare 2 and 4, ghosts between.
        sc.hit(38, b + 1.0, v + 10, jt=2, jv=4)
        sc.hit(38, b + 3.0, v + 10, jt=2, jv=4)
        if intensity < 0.85:
            sc.hit(38, b + 2.75, max(18, v - 46), jt=3, jv=6)
        # Hats or ride.
        key = 51 if ride else 42
        for k in range(8):
            strong = k % 2 == 0
            hv = v - (10 if strong else 26)
            if fill_bar and k >= 4:
                continue
            sc.hit(key, b + 0.5 * k, max(20, hv), jt=2, jv=5)
        if ride and i % 2 == 0:
            sc.hit(53, b, v - 6, jt=2)              # ride bell accent
        if not ride and not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 18, jt=2)        # open-hat lift
        if fill_bar:
            # Tom run down the kit, 16ths, crescendo into the next bar.
            toms = [50, 48, 47, 45, 43, 41, 38, 41]
            for k, key2 in enumerate(toms):
                sc.hit(key2, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 18, v + 16, k / 7)), jt=2)


def _bass_walk(sc, t0: float, prog: list[int], bars_per_chord: int = 1,
               vel: int = 96, reps: int = 1) -> None:
    """Melodic bass: root anchors with fifth/sixth motion, an octave
    apex, and a stepwise approach into every next root."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * bars_per_chord * i
        r = _root(deg)
        nxt = _root(seq[(i + 1) % len(seq)])
        approach = nxt - 1 if nxt > r else nxt + 2
        sc.note(BASS, r, b, 0.95, vel, jt=2, jv=3)
        sc.note(BASS, r + 7, b + 1.0, 0.45, vel - 8, jt=2, jv=3)
        sc.note(BASS, r + 9, b + 1.5, 0.45, vel - 12, jt=2, jv=3)
        sc.note(BASS, r + 12, b + 2.0, 0.70, vel - 4, jt=2, jv=3)
        sc.note(BASS, r + 9, b + 2.75, 0.20, vel - 22, jt=3, jv=4)
        sc.note(BASS, r + 7, b + 3.0, 0.45, vel - 10, jt=2, jv=3)
        sc.note(BASS, approach, b + 3.5, 0.45, vel - 6, jt=2, jv=3)


def _piano_comp(sc, t0: float, bars: int, prog: list[int],
                vel: int = 72) -> None:
    """Verse piano: LH octave pulse, RH off-beat triads, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        sc.note(PIANO, r, b, 1.9, vel + 6, jt=3, jv=4)
        sc.note(PIANO, r + 12, b + 2.0, 1.9, vel + 2, jt=3, jv=4)
        for beat, dur in ((1.5, 0.9), (2.5, 0.9), (3.5, 0.45)):
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 6, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_anthem(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 86) -> None:
    """Chorus piano: block chords with an octave crown."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _root(deg, octave=1)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            sc.note(PIANO, r, b + beat, dur, vel, jt=3, jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 5, jt=3, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.0, 0.9, vel + 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _gtr_verse(sc, t0: float, bars: int, prog: list[int],
               vel: int = 62) -> None:
    """Clean guitar: picked eighth-note arpeggio, tight gate."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)], octave=1)
        pattern = [0, 7, 12, 7, 16, 12, 7, 12]
        for k, off in enumerate(pattern):
            sc.note(GTR_L, r + off, b + 0.5 * k, 0.42, vel, jt=3, jv=4)


def _gtr_chorus(sc, t0: float, bars: int, prog: list[int],
                vel: int = 78) -> None:
    """Clean guitar: open eighth strums, down-up."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        chord = tri + [tri[0] + 12]
        for k in range(8):
            en.strum(sc, GTR_L, chord, b + 0.5 * k, 0.46,
                     vel - (0 if k % 2 == 0 else 12), spread=0.02,
                     down=k % 2 == 0)


def _power_bed(sc, t0: float, bars: int, prog: list[int],
               vel: int = 98, push: bool = True) -> None:
    """Drive guitar: sustained power chords with an eighth push."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        _power(sc, GTR_R, r, b, 2.4, vel, jt=2)
        if push:
            _power(sc, GTR_R, r, b + 2.5, 0.45, vel - 10, jt=2)
            _power(sc, GTR_R, r, b + 3.5, 0.45, vel - 6, jt=2)


def _chug(sc, t0: float, bars: int, prog: list[int], vel: int = 84) -> None:
    """Drive guitar: straight-eight chug, accents on 1 and the &-of-2."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _root(prog[i % len(prog)])
        for k in range(8):
            accent = k in (0, 5)
            _power(sc, GTR_R, r, b + 0.5 * k, 0.40,
                   vel + (8 if accent else 0) - (6 if k % 2 else 0), jt=2)


def _choir(sc, t0: float, bars: int, prog: list[int], vel: int = 62,
           counter: bool = True) -> None:
    """Layered wordless choir: aah pad (3 voices) + ooh counter-line."""
    chords = [en.triad(E3, _MODE, prog[i % len(prog)])
              for i in range(bars)]
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=57, hi=79,
                 vel=vel, legato=0.0)
    if counter:
        degs = [5, 4, 3, 2]
        for i in range(bars // 2):
            d = degs[i % len(degs)]
            sc.note(OOH, en.pitch(E4, _MODE, d), t0 + 8.0 * i, 7.5,
                    vel - 4, jt=0, jv=3)


def _strings_bed(sc, t0: float, bars: int, prog: list[int],
                 vel: int = 58, swell: tuple[int, int] = (46, 88)) -> None:
    chords = [en.triad(E3, _MODE, prog[i % len(prog)])
              for i in range(bars)]
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=48, hi=79,
                 vel=vel, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0, swell[0]), (t0 + 2.0 * bars, swell[1]),
                                (t0 + 4.0 * bars - 0.5, swell[0] + 16)],
                  step=1.0)


def _brass_stabs(sc, t0: float, bars: int, prog: list[int],
                 vel: int = 92) -> None:
    """Section stabs on the &-of-2 / 4, a held growl every fourth bar."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        if i % 4 == 3:
            for p in tri:
                sc.note(BRASS, p, b, 3.6, vel - 6, jt=0, jv=3)
            en.at_curve(sc, BRASS, [(b, 20), (b + 2.0, 96), (b + 3.5, 30)],
                        step=0.5)
        else:
            for beat in (1.5, 3.5):
                for p in tri:
                    sc.note(BRASS, p, b + beat, 0.4, vel, jt=0, jv=3)


def _timp_rolls(sc, t0: float, bars: int, vel: int = 88) -> None:
    """A crescendo roll into every fourth downbeat, plus anchor strokes."""
    for i in range(bars):
        b = t0 + 4.0 * i
        if i % 4 == 0:
            sc.note(TIMP, E2, b, 1.2, vel + 8, jt=0, jv=3)
        if i % 4 == 3:
            for k in range(8):
                sc.note(TIMP, en.n("B2"), b + 2.0 + 0.25 * k, 0.22,
                        int(en.lerp(vel - 30, vel + 12, k / 7)), jt=2, jv=4)


def _lead_hook(sc, t0: float, reps: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The chorus hook on the lead synth; CC1 vibrato blooms on holds."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, E4, _MODE, _HOOK, vel, jt=0, jv=0,
                gate=0.98)
        for deg, start, dur in _HOOK:
            if dur >= 1.5:
                b = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(b + 0.3, 0), (b + dur * 0.6, 58),
                             (b + dur, 12)], step=0.15)
        if lyrics:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    _riff(sc, 0.0, 4)
    _drums(sc, 0.0, 4, 0.45, fills=False)
    _drums(sc, 16.0, 4, 0.6, crash_in=True)
    _bass_walk(sc, 16.0, [1, 1, 6, 5], vel=92)
    en.echo_throw(sc, GTR_R, 14.0, base=0, peak=70, release=2.0)


def verse1(sc) -> None:
    _piano_comp(sc, 32.0, 16, VERSE_PROG)
    _gtr_verse(sc, 32.0, 16, VERSE_PROG)
    _bass_walk(sc, 32.0, VERSE_PROG, reps=4)
    _drums(sc, 32.0, 16, 0.5)


def _pre(sc, t0: float) -> None:
    _piano_anthem(sc, t0, 8, PRE_PROG, vel=78)
    _chug(sc, t0, 8, PRE_PROG, vel=80)
    _bass_walk(sc, t0, PRE_PROG, reps=2, vel=100)
    _drums(sc, t0, 8, 0.7, crash_in=True)
    en.wah(sc, GTR_L, t0, 16.0, lo=44, hi=104, cycles_per_beat=0.25)
    _gtr_verse(sc, t0, 8, PRE_PROG, vel=70)
    en.cc_curve(sc, GTR_L, 74, [(t0 + 16.0, 100), (t0 + 17.0, 127)],
                step=0.5)


def pre1(sc) -> None:
    _pre(sc, 96.0)


def _chorus(sc, t0: float, bars: int, *, lyrics: bool = False,
            vel_lift: int = 0, bass: bool = True) -> None:
    _piano_anthem(sc, t0, bars, CHORUS_PROG, vel=88 + vel_lift)
    _gtr_chorus(sc, t0, bars, CHORUS_PROG, vel=78 + vel_lift)
    _power_bed(sc, t0, bars, CHORUS_PROG, vel=100 + vel_lift)
    if bass:
        _bass_walk(sc, t0, CHORUS_PROG, reps=bars // 4, vel=102 + vel_lift)
    _drums(sc, t0, bars, 0.85, crash_in=True)
    _lead_hook(sc, t0, bars // 4, 96 + vel_lift, lyrics=lyrics)


def chorus1(sc) -> None:
    _chorus(sc, 128.0, 16, lyrics=True)


def verse2(sc) -> None:
    _piano_comp(sc, 192.0, 8, VERSE_PROG)
    _gtr_verse(sc, 192.0, 8, VERSE_PROG)
    _bass_walk(sc, 192.0, VERSE_PROG, reps=2)
    _drums(sc, 192.0, 8, 0.55)
    # EP colour pads (CC1 stays untouched while the EP program is active).
    chords = [en.triad(E3, _MODE, VERSE_PROG[i % 4]) for i in range(8)]
    en.pad_block(sc, KEYS, 192.0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=48, legato=0.0)


def pre2(sc) -> None:
    _pre(sc, 224.0)


def chorus2(sc) -> None:
    _chorus(sc, 256.0, 16, lyrics=True)
    _choir(sc, 256.0, 16, CHORUS_PROG, vel=60)
    en.vowel_curve(sc, AAH, [(256.0, 42), (280.0, 84), (312.0, 96),
                             (318.0, 60)], step=2.0)
    _brass_stabs(sc, 256.0, 16, CHORUS_PROG)
    # Rock organ (program 18 from beat 256): held chords + Leslie ramp.
    chords = [en.triad(E3, _MODE, CHORUS_PROG[i % 4]) for i in range(16)]
    en.pad_block(sc, KEYS, 256.0, chords, 4.0, size=3, lo=55, hi=76,
                 vel=58, legato=0.0)
    en.leslie(sc, KEYS, 304.0, 318.0, 20, 112)


def middle8(sc) -> None:
    t0 = 320.0
    # Introspective: pedalled piano arpeggios, choir oo, strings enter pp.
    for i in range(8):
        b = t0 + 4.0 * i
        tri = _triad(MID_PROG[i], octave=1)
        seq = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2], tri[1],
               tri[0] + 12, tri[1]]
        for k, p in enumerate(seq):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 56, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    en.soft_pedal(sc, PIANO, t0, t0 + 16.0)
    _choir(sc, t0, 8, [6, 4, 1, 5], vel=54, counter=True)
    en.vowel_curve(sc, OOH, [(t0, 30), (t0 + 16.0, 58), (t0 + 31.5, 88)],
                   step=2.0)
    _strings_bed(sc, t0, 8, [6, 4, 1, 5], vel=52, swell=(40, 84))
    for i, deg in enumerate(MID_PROG):
        sc.note(BASS, _root(deg), t0 + 4.0 * i, 3.6, 78, jt=0, jv=3)
    for i in range(8):
        b = t0 + 4.0 * i
        sc.hit(36, b, 62, jt=2)
        sc.hit(37, b + 2.0, 44, jt=2)               # side-stick heartbeat


def lead_break(sc) -> None:
    t0 = 352.0
    en.bend_range(sc, LEAD, 12, t0 - 0.02)
    _chug(sc, t0, 8, [1, 6, 4, 5], vel=86)
    _bass_walk(sc, t0, [1, 6, 4, 5], reps=2, vel=100)
    _drums(sc, t0, 8, 0.8, ride=True, crash_in=True)
    # Climb: legato hammer-on run up two octaves...
    en.run(sc, LEAD, t0, E4, _MODE, [1, 2, 3, 5, 6, 8, 9, 10, 12, 13, 15],
           0.25, 84, 108, legato=True)
    # ...to a held peak with vibrato, echo throws...
    peak = en.pitch(E4, _MODE, 15)
    sc.note(LEAD, peak, t0 + 3.0, 8.5, 106, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(t0 + 3.5, 0), (t0 + 7.0, 70),
                              (t0 + 11.0, 20)], step=0.2)
    en.echo_throw(sc, LEAD, t0 + 10.0, base=10, peak=88, release=3.0)
    # ...answered low, then THE DIVE: a full octave on the 12-semi range.
    en.line(sc, LEAD, t0 + 12.0, E4, _MODE,
            [(8, 0.0, 0.5), (7, 0.5, 0.5), (6, 1.0, 0.5), (5, 1.5, 0.5),
             (6, 2.0, 1.0), (3, 3.0, 1.0)], 92, jt=2)
    dive = en.pitch(E4, _MODE, 8)
    sc.note(LEAD, dive, t0 + 17.0, 12.5, 104, jt=0, jv=0)
    en.bend_ramp(sc, LEAD, t0 + 24.0, t0 + 28.0, 0.0, -2.0, steps=24)
    sc.bend(LEAD, t0 + 29.5, 0.0)
    en.bend_range(sc, LEAD, 2, t0 + 31.5)


def final_chorus(sc) -> None:
    t0 = 384.0
    # bass=False: here the bass sings the hook itself (doubling below),
    # not the walk — one bass line at a time.
    _chorus(sc, t0, 16, lyrics=True, vel_lift=6, bass=False)
    # Double-length last time: bars 17-20 augment the tag.
    _piano_anthem(sc, t0 + 64.0, 4, [4, 5, 6, 1], vel=94)
    _power_bed(sc, t0 + 64.0, 4, [4, 5, 6, 1], vel=106, push=False)
    _drums(sc, t0 + 64.0, 4, 0.95, china=True, crash_in=True)
    en.line(sc, LEAD, t0 + 64.0, E4, _MODE,
            [(5, 0.0, 2.0), (6, 2.0, 2.0), (8, 4.0, 7.5)], 104, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(t0 + 68.5, 0), (t0 + 72.0, 64),
                              (t0 + 75.0, 16)], step=0.2)
    # The bass doubles the hook an octave down (oracle: hook_doubling),
    # with a two-note tonic pickup walking into each restatement.
    for r in range(4):
        base = t0 + 16.0 * r
        en.line(sc, BASS, base, E3, _MODE, _HOOK, 104, jt=0, jv=0,
                gate=0.95)
        sc.note(BASS, E3, base + 15.0, 0.45, 96, jt=0, jv=0)
        sc.note(BASS, en.pitch(E3, _MODE, 2), base + 15.5, 0.45, 98,
                jt=0, jv=0)
    # Full orchestra.
    _choir(sc, t0, 20, CHORUS_PROG, vel=64)
    en.vowel_curve(sc, AAH, [(t0, 60), (t0 + 40.0, 96), (t0 + 79.0, 84)],
                   step=2.0)
    _brass_stabs(sc, t0, 20, CHORUS_PROG, vel=96)
    _strings_bed(sc, t0, 20, CHORUS_PROG, vel=60, swell=(60, 100))
    _timp_rolls(sc, t0, 20)
    chords = [en.triad(E3, _MODE, CHORUS_PROG[i % 4]) for i in range(20)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=55, hi=76,
                 vel=60, legato=0.0)
    en.leslie(sc, KEYS, t0, t0 + 8.0, 112, 30)
    en.leslie(sc, KEYS, t0 + 56.0, t0 + 76.0, 30, 118)


def outro(sc) -> None:
    t0 = 464.0
    _riff(sc, t0, 4, vel_scale=0.92)
    _drums(sc, t0, 8, 0.55, fills=False)
    _bass_walk(sc, t0, [1, 1, 6, 5], reps=2, vel=88)
    for i in range(4):
        b = t0 + 8.0 * i
        sc.note(PIANO, E4 + 12, b, 1.5, int(en.lerp(60, 40, i / 3)),
                jt=3, jv=4)
        sc.note(PIANO, en.pitch(E4, _MODE, 5) + 12, b + 1.5, 1.5,
                int(en.lerp(56, 36, i / 3)), jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 7.9)
    en.echo_throw(sc, GTR_R, t0 + 30.0, base=0, peak=76, release=4.0)
    # The last front rolls out: one held E5 with a crash, dying away.
    _power(sc, GTR_R, E2, t0 + 32.0, 7.5, 96, jt=0)
    sc.note(BASS, E2 + 12, t0 + 32.0, 7.5, 92, jt=0, jv=0)
    sc.hit(49, t0 + 32.0, 106, jt=0)
    sc.hit(36, t0 + 32.0, 100, jt=0)
    en.cc_curve(sc, GTR_R, 11, [(t0 + 32.0, 110), (t0 + 39.5, 30)],
                step=0.5)
    sc.hit(46, t0 + 36.0, 40, jt=0)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            lead_break, final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 4, 18, 26, 29, 30, 33, 47, 48, 52, 53, 61, 81}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, LEAD, KEYS, STRINGS, DRUMS,
                     BRASS, TIMP}
NOTE_RANGES = {
    PIANO: (40, 100), GTR_L: (40, 92), GTR_R: (33, 76), BASS: (36, 64),
    AAH: (52, 84), OOH: (52, 88), LEAD: (52, 100), KEYS: (48, 80),
    STRINGS: (44, 84), BRASS: (52, 88), TIMP: (36, 60),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (228.0, 252.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.15),
    ("chorus2", ">=", "chorus1", 1.0),
    ("middle8", "<=", "chorus2", 0.8),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("final_chorus", ">=", "chorus1", 1.05),
    ("outro", "<=", "final_chorus", 0.7),
    ("intro", "<=", "chorus1", 1.0),
    ("pre1", "<=", "chorus1", 1.0),
]
LATE_CHANNELS = {AAH: 256.0, OOH: 256.0, BRASS: 256.0, STRINGS: 320.0,
                 TIMP: 384.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 4), ("chorus1", 4), ("verse2", 4),
                 ("chorus2", 4), ("final_chorus", 4)],
    "hook": "final_chorus",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH],
    "sections": ["chorus2", "middle8", "final_chorus"],
}
FEATURES_EXPECTED = {
    "bend_range", "pitch_bend", "cc1_vibrato", "cc1_leslie", "cc68_legato",
    "cc74_wah", "cc64_sustain", "cc67_soft", "cc11_expression",
    "aftertouch", "cc94_echo", "program_change",
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
    import verify

    fails_recap: list[str] = []
    intro_roots = _grouped_roots(sc, GTR_R, 0.0, 16.0)
    outro_roots = _grouped_roots(sc, GTR_R, 464.0, 480.0)
    if intro_roots != outro_roots:
        fails_recap.append(
            f"outro riff differs from intro riff "
            f"({len(intro_roots)} vs {len(outro_roots)} chord-hits)")

    fails_hook: list[str] = []
    lead = {(round(on * 4) / 4, p) for on, _off, p, _v in _spans(sc, LEAD)
            if 384.0 <= on < 448.0}
    bass = {(round(on * 4) / 4, p) for on, _off, p, _v in _spans(sc, BASS)
            if 384.0 <= on < 448.0}
    matched = sum(1 for on, p in lead if (on, p - 12) in bass)
    if not lead or matched / len(lead) < 0.7:
        pct = 0.0 if not lead else matched / len(lead)
        fails_hook.append(f"bass doubles only {pct:.0%} of the final-chorus "
                          f"hook (need >= 70%)")

    fails_dive: list[str] = []
    bends = [f for b, f in verify._bend_fracs(sc, LEAD)
             if 352.0 <= b < 384.0]
    if not bends or min(bends) > -0.95:
        fails_dive.append("no full-deflection dive bend in the lead break")

    return [("riff_recap", fails_recap),
            ("hook_doubling", fails_hook),
            ("lead_dive", fails_dive)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

_LIFT_DB = 2.0          # PROVISIONAL: final chorus over verse 1
_BRASS_RISE_DB = 0.4    # PROVISIONAL: RMS rise across the chorus-2 entry


def audio_checks(ctx):
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(40.0, 88.0)
    f0, f1 = ctx.bar_window(384.0, 448.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    fails_brass: list[str] = []
    a0, a1 = ctx.bar_window(248.0, 256.0)
    b0, b1 = ctx.bar_window(256.0, 264.0)
    before = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    after = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    if after < before + _BRASS_RISE_DB:
        fails_brass.append(f"chorus-2 entry {after:.1f} dB not "
                           f">= {before:.1f} + {_BRASS_RISE_DB} dB")

    return [("chorus_lift", fails_lift),
            ("orch_entry_rise", fails_brass)]
