"""t08_neon_cathedral.py — "Neon Cathedral" (Big Weather, track 8).

The album's breather: introspective E-minor pop at 96 BPM.  A cathedral
organ (GM19, INTRO ONLY per HLD D9/R5 — the channel is re-programmed to
the GM16 drawbar at the prelude's end, oracle-enforced) states the THEME
alone; then the band enters quietly — echo guitar (CC94 ping-pong throws,
the headline feature, proven by a matched dry/wet audio probe in the
reprise), soft una-corda piano, melodic bass and the GM2 brush kit.  The
chorus HOOK is sung by the echo guitar; a G-major bridge brings in a warm
portamento square lead; the SWELL is the track's dynamic peak — strings
gate in, sticks replace brushes, the drive guitar lights up, and channel
aftertouch swells the organ and strings under the hook's return — before
a quiet reprise recalls the prelude THEME on the band's own instruments
(recompute-pinned oracle).

Form (HLD §4, bespoke):
  prelude | verse1 | chorus1 | verse2 | chorus2 | bridge |
  swell_rise | swell_peak | reprise
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 8
TITLE = "Neon Cathedral"
FILE = "08 - Neon Cathedral.mid"
SEED = 20260708

BPM = 96.0

# Channels (HLD §3, reduced stage: no brass/timpani — this is the breather).
PIANO, GTR_E, GTR_W, BASS = 0, 1, 2, 3
AAH, OOH, LEAD, KEYS = 4, 5, 6, 7
STRINGS, DRUMS = 8, 9

PRELUDE_END = 48.0

_SECTIONS = [
    ("prelude",      0.0,  48.0),
    ("verse1",      48.0, 112.0),
    ("chorus1",    112.0, 160.0),
    ("verse2",     160.0, 208.0),
    ("chorus2",    208.0, 256.0),
    ("bridge",     256.0, 296.0),
    ("swell_rise", 296.0, 328.0),
    ("swell_peak", 328.0, 376.0),
    ("reprise",    376.0, 432.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1),        # E minor (one sharp)
             (256.0, 1, 0),      # bridge: G major (relative — grid stays clean)
             (296.0, 1, 1)],     # back to E minor for the swell
    channels=[
        (PIANO,   "piano",           0, 100, 64, 50),
        (GTR_E,   "echo guitar",    26,  96, 48, 40),
        (GTR_W,   "warm guitar",    25,  90, 80, 40),
        (BASS,    "bass guitar",    33, 105, 64, 25),
        (AAH,     "choir aah",      52,  84, 64, 70),
        (OOH,     "choir ooh",      53,  82, 64, 70),
        (LEAD,    "lead synth",     80,  88, 64, 45),
        (KEYS,    "cathedral organ", 19,  96, 64, 62),
        (STRINGS, "strings",        48,  86, 64, 65),
        (DRUMS,   "drums",           0, 104, 64, 45),
    ],
    program_changes=[
        (KEYS,  PRELUDE_END, 16),  # cathedral confined to the prelude (D9/R5)
        (GTR_W, 328.0, 29),        # acoustic -> overdrive for the swell peak
        (DRUMS,   0.0, 40),        # GM2 brush kit for the song's quiet body
        (DRUMS, 296.0,  0),        # sticks (V3 kit) for the swell
        (DRUMS, 376.0, 40),        # brushes return for the reprise
    ],
)

# ---------------------------------------------------------------------------
# Harmony — E aeolian; the bridge borrows the relative major (G ionian).
# ---------------------------------------------------------------------------

E2, E3, E4 = en.n("E2"), en.n("E3"), en.n("E4")
G2 = en.n("G2")
_MODE = "aeolian"

VERSE_PROG = [1, 4, 6, 5]           # Em  Am  C   Bm
CHORUS_PROG = [6, 3, 7, 1]          # C   G   D   Em
RISE_PROG = [1, 6, 3, 7]            # Em  C   G   D
BRIDGE_PROG = [1, 4, 5, 4, 1, 6, 4, 5, 2, 5]   # G ionian, one chord per bar


def _root(deg: int, octave: int = 0) -> int:
    return en.pitch(E2, _MODE, deg) + 12 * octave


def _triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(E2, _MODE, deg)]


def _g_triad(deg: int, octave: int = 1) -> list[int]:
    return [p + 12 * octave for p in en.triad(G2, "ionian", deg)]


# The THEME — the cathedral prelude's melody, recalled note-for-note by the
# echo guitar in the reprise (oracle: prelude_recall, recomputed from the
# Score on both sides, never copied).  16 beats, E aeolian over E4; jt=0.
_THEME = [
    (1, 0.0, 1.5), (2, 1.5, 0.5), (3, 2.0, 1.0), (5, 3.0, 1.0),
    (6, 4.0, 2.5), (5, 6.5, 0.5), (4, 7.0, 1.0),
    (5, 8.0, 1.5), (3, 9.5, 0.5), (4, 10.0, 1.0), (2, 11.0, 1.0),
    (1, 12.0, 4.0),
]

# The chorus HOOK — 16 beats over C G D Em, sung by the echo guitar in the
# choruses and returned fortissimo by the lead in the swell (oracle:
# hook_return).  jt=0 wherever it is oracle-pinned.
_HOOK = [
    (6, 0.0, 1.5), (5, 1.5, 0.5), (6, 2.0, 1.0), (7, 3.0, 1.0),
    (5, 4.0, 2.0), (3, 6.0, 0.75), (4, 6.75, 0.25), (5, 7.0, 1.0),
    (9, 8.0, 1.5), (8, 9.5, 0.5), (7, 10.0, 1.0), (8, 11.0, 1.0),
    (5, 12.0, 2.5), (4, 14.5, 0.5), (3, 15.0, 1.0),
]

_HOOK_LYRICS = ["neon cathedral", "every window burning",
                "cold light", "warm heart"]

# The reprise "neon tag" — the staccato figure of the echo-throw audio
# probe (semitone offset from E4, start, dur, vel); jt=0, jv=0 so the dry
# and wet statements are bit-identical apart from the CC94 throw.
_TAG = [(12, 1.0, 0.22, 78), (7, 1.25, 0.22, 74), (3, 1.5, 0.22, 72)]

# Hand-written bass lines (semitone offset from E2, beat, dur, vel) — the
# brief demands a bass that SINGS: stepwise, wide, with real countermelody.
_VERSE_BASS = [
    (0, 0.0, 1.9, 92), (3, 2.0, 0.9, 78), (5, 3.0, 0.9, 82),
    (5, 4.0, 1.4, 90), (7, 5.5, 0.45, 76), (8, 6.0, 0.9, 84),
    (7, 7.0, 0.9, 80),
    (8, 8.0, 1.9, 90), (12, 10.0, 0.9, 82), (10, 11.0, 0.9, 80),
    (7, 12.0, 1.4, 90), (5, 13.5, 0.45, 76), (3, 14.0, 0.95, 80),
    (2, 15.0, 0.95, 78),
]
_CHORUS_BASS = [
    (8, 0.0, 1.4, 96), (7, 1.5, 0.45, 82), (8, 2.0, 0.9, 88),
    (10, 3.0, 0.45, 84), (5, 3.5, 0.45, 80),
    (3, 4.0, 1.4, 96), (5, 5.5, 0.45, 80), (7, 6.0, 0.9, 86),
    (12, 7.0, 0.9, 88),
    (10, 8.0, 1.4, 96), (14, 9.5, 0.45, 84), (15, 10.0, 0.9, 90),
    (14, 11.0, 0.9, 86),
    (12, 12.0, 1.9, 96), (7, 14.0, 0.9, 84), (3, 15.0, 0.95, 82),
]
_SWELL_BASS = [                       # the descending lament countermelody
    (12, 0.0, 1.9, 100), (10, 2.0, 0.9, 90), (8, 3.0, 0.9, 92),
    (7, 4.0, 1.9, 98), (5, 6.0, 0.9, 88), (3, 7.0, 0.9, 90),
    (5, 8.0, 1.4, 96), (7, 9.5, 0.45, 84), (8, 10.0, 0.9, 92),
    (10, 11.0, 0.9, 90),
    (12, 12.0, 1.4, 100), (10, 13.5, 0.45, 86), (7, 14.0, 0.95, 92),
    (2, 15.0, 0.95, 88),
]


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _bass_line(sc, t0: float, pattern, reps: int = 1, vel_lift: int = 0,
               jt: int = 2) -> None:
    for r in range(reps):
        base = t0 + 16.0 * r
        for off, beat, dur, vel in pattern:
            sc.note(BASS, E2 + off, base + beat, dur, vel + vel_lift,
                    jt=(0 if beat == 0.0 and r == 0 else jt), jv=3)


def _piano_verse(sc, t0: float, bars: int, prog, vel: int = 58) -> None:
    """Gentle broken chords: LH root, RH rising fragments, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        sc.note(PIANO, tri[0], b, 1.9, vel + 4, jt=(0 if i == 0 else 3),
                jv=4)
        sc.note(PIANO, tri[1], b + 1.0, 0.9, vel - 6, jt=3, jv=4)
        sc.note(PIANO, tri[2], b + 2.0, 1.4, vel - 4, jt=3, jv=4)
        sc.note(PIANO, tri[1] + 12, b + 3.0, 0.9, vel - 8, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_anthem(sc, t0: float, bars: int, prog, vel: int = 84) -> None:
    """Chorus piano: dotted block chords with an octave crown."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=2)
        root = _root(prog[i % len(prog)], octave=1)
        for beat, dur in ((0.0, 1.4), (1.5, 0.9), (2.5, 1.4)):
            sc.note(PIANO, root, b + beat, dur, vel,
                    jt=(0 if i == 0 and beat == 0.0 else 3), jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel - 5,
                        jt=(0 if i == 0 and beat == 0.0 else 3), jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.5, 0.45, vel + 2, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _gtr_arp(sc, t0: float, bars: int, prog, vel: int = 52,
             vel_end: int | None = None) -> None:
    """Echo guitar: chiming picked eighths, high and glassy."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        v = vel if vel_end is None else int(en.lerp(vel, vel_end,
                                                    i / max(1, bars - 1)))
        seq = [tri[0], tri[2], tri[1] + 12, tri[2] + 12,
               tri[1] + 12, tri[0] + 12, tri[2], tri[1]]
        for k, p in enumerate(seq):
            sc.note(GTR_E, p, b + 0.5 * k, 0.42, v - (6 if k % 2 else 0),
                    jt=(0 if i == 0 and k == 0 else 3), jv=4)


def _gtr_call(sc, t0: float, vel: int = 74) -> None:
    """The 'neon call': a staccato answer figure with a CC94 throw."""
    for k, (off, beat, dur) in enumerate([(15, 0.0, 0.3), (14, 0.5, 0.3),
                                          (12, 1.0, 0.3), (7, 1.5, 0.7)]):
        sc.note(GTR_E, E3 + off, t0 + beat, dur, vel - 3 * k, jt=2, jv=3)
    en.echo_throw(sc, GTR_E, t0 + 1.5, base=0, peak=92, release=2.5)


def _strum_bed(sc, t0: float, bars: int, prog, vel: int = 68,
               eighths: bool = True) -> None:
    """Warm guitar: open strums, down-up."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = _triad(prog[i % len(prog)], octave=1)
        chord = tri + [tri[0] + 12]
        beats = [0.5 * k for k in range(8)] if eighths else [0.0, 1.5, 2.5]
        for k, beat in enumerate(beats):
            en.strum(sc, GTR_W, chord, b + beat, 0.46,
                     vel - (0 if k % 2 == 0 else 12), spread=0.02,
                     down=k % 2 == 0)


def _power(sc, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    for i, off in enumerate((0, 7, 12)):
        sc.note(GTR_W, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _organ_pad(sc, t0: float, bars: int, prog, vel: int = 46,
               lo: int = 52, hi: int = 74) -> None:
    chords = [en.triad(E3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=lo, hi=hi,
                 vel=vel, legato=0.0)


def _brush(sc, t0: float, bars: int, intensity: float, *,
           kick: bool = True, tap: bool = True, hats: bool = True,
           crash_in: bool = False, fills: bool = True) -> None:
    """The GM2 brush-kit groove (program 40 on ch 10)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(50, 92, intensity)))
        fill_bar = fills and i % 8 == 7
        if crash_in and i == 0:
            sc.hit(49, b, min(112, v + 12), jt=0)
        sc.hit(40, b, v - 18, jt=(0 if i == 0 else 3), jv=4)       # stir
        sc.hit(40, b + 2.0, v - 24, jt=3, jv=4)
        if kick:
            sc.hit(36, b, v, jt=2)
            sc.hit(36, b + 2.5, v - 8, jt=2)
        if tap and not fill_bar:
            sc.hit(38, b + 1.0, v + 6, jt=2, jv=4)                 # tap
            sc.hit(38, b + 3.0, v + 6, jt=2, jv=4)
            if intensity > 0.55:
                sc.hit(38, b + 2.75, max(16, v - 40), jt=3, jv=6)  # ghost
        elif not tap:
            sc.hit(37, b + 1.0, v - 8, jt=2, jv=4)                 # rim
            sc.hit(37, b + 3.0, v - 10, jt=2, jv=4)
        if hats:
            for k in range(8):
                if fill_bar and k >= 5:
                    continue
                hv = v - (16 if k % 2 == 0 else 30)
                sc.hit(42, b + 0.5 * k, max(16, hv), jt=2, jv=5)
            if i % 2 == 1 and not fill_bar:
                sc.hit(46, b + 3.5, v - 24, jt=2)
        if intensity > 0.6 and i % 4 == 2:
            sc.hit(39, b + 3.75, v - 12, jt=2)                     # slap
        if fill_bar:
            sc.hit(38, b + 1.0, v + 6, jt=2, jv=4)   # backbeat, then fill
            for k in range(6):
                sc.hit(38 if k % 2 == 0 else 39, b + 2.5 + 0.25 * k,
                       int(en.lerp(v - 26, v + 8, k / 5)), jt=2)


def _kit_build(sc, t0: float, bars: int) -> None:
    """Swell-rise sticks: heartbeat toms growing into a snare roll."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(58, 96, i / max(1, bars - 1))))
        sc.hit(36, b, v, jt=(0 if i == 0 else 2))
        sc.hit(36, b + 2.5, v - 10, jt=2)
        sc.hit(41, b + 1.0, v - 12, jt=2, jv=4)                    # floor tom
        sc.hit(41, b + 3.0, v - 14, jt=2, jv=4)
        if i >= 2:
            sc.hit(37, b + 2.0, v - 16, jt=2)                      # cross-stick
        for k in range(8):
            sc.hit(42, b + 0.5 * k, max(16, v - 34 + (6 if k % 2 == 0
                                                      else 0)), jt=2, jv=5)
        if i == bars - 2:
            for k in range(8):
                sc.hit(38, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 30, v - 6, k / 7)), jt=2)
        if i == bars - 1:
            for k in range(16):
                sc.hit(38, b + 0.25 * k,
                       int(en.lerp(v - 24, v + 14, k / 15)), jt=2)
            sc.hit(45, b + 3.0, v, jt=2)
            sc.hit(43, b + 3.5, v + 4, jt=2)
            sc.hit(41, b + 3.75, v + 8, jt=2)


def _kit_full(sc, t0: float, bars: int, vel: int = 100) -> None:
    """Swell-peak sticks: wide crash conversation over a solid backbeat."""
    for i in range(bars):
        b = t0 + 4.0 * i
        fill_bar = i % 4 == 3
        if i % 4 == 0:
            sc.hit(49, b, vel + 6, jt=0 if i == 0 else 2)
        elif i % 4 == 2:
            sc.hit(57, b, vel, jt=2)                               # crash 2
        sc.hit(36, b, vel + 4, jt=2)
        sc.hit(36, b + 2.5, vel - 4, jt=2)
        if i % 2 == 1:
            sc.hit(36, b + 3.75, vel - 8, jt=2)
        sc.hit(38, b + 1.0, vel + 6, jt=2, jv=4)
        sc.hit(38, b + 3.0, vel + 6, jt=2, jv=4)
        sc.hit(38, b + 2.75, max(18, vel - 44), jt=3, jv=6)
        for k in range(8):
            if fill_bar and k >= 4:
                continue
            sc.hit(51, b + 0.5 * k, vel - (14 if k % 2 == 0 else 26),
                   jt=2, jv=5)
        if i % 2 == 0:
            sc.hit(53, b, vel - 10, jt=2)                          # ride bell
        if not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, vel - 18, jt=2)
        if fill_bar:
            toms = [50, 48, 47, 45, 43, 41, 38, 41]
            for k, key in enumerate(toms):
                sc.hit(key, b + 2.0 + 0.25 * k,
                       int(en.lerp(vel - 20, vel + 12, k / 7)), jt=2)


def _choir(sc, t0: float, bars: int, prog, vel: int = 54,
           counter_degs=None) -> None:
    chords = [en.triad(E3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=57, hi=79,
                 vel=vel, legato=0.0)
    if counter_degs:
        for i, d in enumerate(counter_degs):
            sc.note(OOH, en.pitch(E4, _MODE, d), t0 + 8.0 * i, 7.5,
                    vel - 4, jt=0, jv=3)


def _strings_bed(sc, t0: float, bars: int, prog, vel: int, lo: int,
                 hi: int, swell) -> None:
    chords = [en.triad(E3, _MODE, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=lo, hi=hi,
                 vel=vel, legato=0.0)
    en.expr_curve(sc, STRINGS, swell, step=1.0)


def _hook(sc, ch: int, t0: float, reps: int, vel: int, *, jt: int = 0,
          jv: int = 0, lyrics: bool = False, throws: bool = False) -> None:
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, ch, base, E4, _MODE, _HOOK, vel, jt=jt, jv=jv,
                gate=0.97)
        if throws:
            en.echo_throw(sc, GTR_E, base + 14.5, base=0, peak=88,
                          release=2.5)
        if lyrics:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def prelude(sc) -> None:
    """The cathedral alone: pedal fifth, then the THEME twice, and a
    VI-iv-i cadence.  GM19 lives ONLY here (D9/R5)."""
    sc.cc(GTR_E, 94, 0, 0.0)          # author the echo send dry: throws only
    en.expr_curve(sc, KEYS, [(0.0, 34), (8.0, 66), (24.0, 80),
                             (40.0, 88), (47.0, 58)], step=1.0)
    # Pedal fifth, breathing in.
    for p, v in ((E2, 64), (E2 + 7, 56), (E3, 52)):
        sc.note(KEYS, p, 0.0, 7.9, v, jt=0, jv=0)
    # Two theme statements over slow low-mid chords (chords stay <= B3 so
    # the melody extraction in prelude_recall is unambiguous).
    chords_1 = [[40, 47, 52, 55], [48, 52, 55, 59],
                [43, 50, 55, 59], [40, 47, 52, 55]]     # Em C G Em
    chords_2 = [[40, 47, 52, 55], [48, 52, 55, 59],
                [45, 48, 52, 57], [48, 52, 55, 59]]     # Em C Am C
    for k, chord in enumerate(chords_1):
        for p in chord:
            sc.note(KEYS, p, 8.0 + 4.0 * k, 3.95, 66, jt=0, jv=2)
    en.line(sc, KEYS, 8.0, E4, _MODE, _THEME, 74, jt=0, jv=0, gate=0.99)
    for k, chord in enumerate(chords_2):
        for p in chord:
            sc.note(KEYS, p, 24.0 + 4.0 * k, 3.95, 72, jt=0, jv=2)
    en.line(sc, KEYS, 24.0, E4, _MODE, _THEME, 82, jt=0, jv=0, gate=0.99)
    # Tremulant blooms through the second statement (GM19: CC1 = depth).
    en.cc_curve(sc, KEYS, 1, [(24.0, 0), (32.0, 44), (44.0, 16),
                              (47.0, 0)], step=0.5)
    # Cadence: Am -> Em under a held E4 suspension.
    for p in (45, 48, 52, 57):
        sc.note(KEYS, p, 40.0, 3.95, 70, jt=0, jv=2)
    for p in (40, 47, 52, 55):
        sc.note(KEYS, p, 44.0, 3.9, 64, jt=0, jv=2)
    sc.note(KEYS, E4, 40.0, 7.9, 74, jt=0, jv=0)


def verse1(sc) -> None:
    t0 = 48.0
    sc.cc(KEYS, 91, 45, t0)           # drawbar era: back to the hall send
    en.soft_pedal(sc, PIANO, t0, t0 + 32.0)   # una corda, first half only
    _piano_verse(sc, t0, 16, VERSE_PROG, vel=56)
    _bass_line(sc, t0, _VERSE_BASS, reps=4)
    # Guitar entries stay aligned to the 4-bar harmonic cycle.
    _gtr_arp(sc, t0 + 16.0, 3, VERSE_PROG, vel=48)
    _gtr_call(sc, t0 + 28.0, vel=70)
    _gtr_arp(sc, t0 + 32.0, 7, VERSE_PROG, vel=52, vel_end=60)
    _gtr_call(sc, t0 + 60.0, vel=76)
    _brush(sc, t0, 8, 0.32, kick=False, tap=False, fills=False)
    _brush(sc, t0 + 32.0, 8, 0.45)


def chorus1(sc) -> None:
    t0 = 112.0
    _hook(sc, GTR_E, t0, 3, 84, lyrics=True, throws=True)
    _piano_anthem(sc, t0, 12, CHORUS_PROG, vel=80)
    _strum_bed(sc, t0, 12, CHORUS_PROG, vel=62)
    _bass_line(sc, t0, _CHORUS_BASS, reps=3)
    _organ_pad(sc, t0, 12, CHORUS_PROG, vel=44)
    en.leslie(sc, KEYS, t0 + 32.0, t0 + 46.0, 20, 72)
    _brush(sc, t0, 12, 0.72, crash_in=True)


def verse2(sc) -> None:
    t0 = 160.0
    _piano_verse(sc, t0, 12, VERSE_PROG, vel=60)
    _bass_line(sc, t0, _VERSE_BASS, reps=3)
    _gtr_arp(sc, t0, 6, VERSE_PROG, vel=54)
    _gtr_call(sc, t0 + 28.0, vel=74)
    _gtr_arp(sc, t0 + 32.0, 4, VERSE_PROG, vel=56, vel_end=62)
    _organ_pad(sc, t0, 12, VERSE_PROG, vel=40)
    _brush(sc, t0, 12, 0.5)


def chorus2(sc) -> None:
    t0 = 208.0
    _hook(sc, GTR_E, t0, 3, 87, lyrics=True, throws=True)
    _piano_anthem(sc, t0, 12, CHORUS_PROG, vel=82)
    _strum_bed(sc, t0, 12, CHORUS_PROG, vel=60)
    _bass_line(sc, t0, _CHORUS_BASS, reps=3, vel_lift=3)
    _organ_pad(sc, t0, 12, CHORUS_PROG, vel=48)
    en.leslie(sc, KEYS, t0 + 36.0, t0 + 47.0, 24, 96)
    _brush(sc, t0, 12, 0.8, crash_in=True)
    # The choir arrives (LATE_CHANNELS): aah pad + ooh counter, oo -> ah.
    _choir(sc, t0, 12, CHORUS_PROG, vel=56, counter_degs=[5, 4, 5, 6, 7, 8])
    en.vowel_curve(sc, AAH, [(t0, 40), (t0 + 24.0, 80), (t0 + 44.0, 96),
                             (t0 + 47.0, 70)], step=2.0)
    en.vowel(sc, OOH, 45, t0)


def bridge(sc) -> None:
    """The relative major: the lead's warm square voice, glides and all."""
    t0 = 256.0
    G4 = G2 + 24
    # Piano: brighter G-major arpeggios.
    for i, deg in enumerate(BRIDGE_PROG):
        b = t0 + 4.0 * i
        tri = _g_triad(deg, octave=1)
        seq = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2], tri[1],
               tri[0] + 12, tri[2]]
        for k, p in enumerate(seq):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 60,
                    jt=(0 if i == 0 and k == 0 else 3), jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    # Warm guitar: halftime open strums, voiced in G ionian by hand
    # (_strum_bed voices via the E-aeolian _triad, wrong mode here).
    for i, deg in enumerate(BRIDGE_PROG):
        b = t0 + 4.0 * i
        tri = _g_triad(deg, octave=1)
        chord = tri + [tri[0] + 12]
        for k, beat in enumerate((0.0, 1.5, 2.5)):
            en.strum(sc, GTR_W, chord, b + beat, 0.9,
                     56 - (10 if k else 0), spread=0.025, down=k == 0)
    # Bass: rooted walking line under the G-major turn.
    roots = [3, 8, 10, 8, 3, 0, 8, 10, 5, 10]        # G C D C G E C D A D
    for i, off in enumerate(roots):
        b = t0 + 4.0 * i
        r = E2 + off
        nxt = E2 + roots[(i + 1) % len(roots)]
        sc.note(BASS, r, b, 1.4, 88, jt=(0 if i == 0 else 2), jv=3)
        fifth = r + 7 if r + 7 <= 55 else r - 5
        sc.note(BASS, fifth, b + 1.5, 0.45, 76, jt=2, jv=3)
        sc.note(BASS, r, b + 2.0, 0.9, 82, jt=2, jv=3)
        approach = nxt - 1 if nxt > r else nxt + 2
        sc.note(BASS, approach, b + 3.0, 0.95, 80, jt=2, jv=3)
    # The lead: portamento glides, a legato run, vibrato blooms.
    en.portamento_on(sc, LEAD, t0, time_cc=45)
    mel = [(3, 0.0, 1.5), (2, 1.5, 0.5), (3, 2.0, 1.0), (5, 3.0, 1.0),
           (4, 4.0, 2.5), (3, 6.5, 0.5), (2, 7.0, 1.0),
           (1, 8.0, 1.5), (2, 9.5, 0.5), (3, 10.0, 1.0), (4, 11.0, 1.0),
           (5, 12.0, 3.5),
           (6, 16.0, 1.5), (5, 17.5, 0.5), (4, 18.0, 1.0), (3, 19.0, 1.0),
           (4, 20.0, 2.5), (2, 22.5, 0.5), (3, 23.0, 1.0),
           (2, 24.0, 1.5), (3, 25.5, 0.5), (4, 26.0, 1.0), (5, 27.0, 1.0),
           (3, 28.0, 3.0)]
    en.line(sc, LEAD, t0, G4, "ionian", mel, 76, jt=2, jv=3, gate=0.99)
    en.vibrato(sc, LEAD, t0 + 12.0, 3.4, depth=0.22, delay=0.6)
    en.vibrato(sc, LEAD, t0 + 28.0, 2.8, depth=0.2, delay=0.5)
    # The turn: a hammered run up to a held sixth, gliding down to the V.
    en.run(sc, LEAD, t0 + 32.0, G4, "ionian", [1, 2, 3, 4, 5], 0.25,
           56, 80, legato=True)
    sc.note(LEAD, en.pitch(G4, "ionian", 6), t0 + 33.25, 2.5, 84,
            jt=0, jv=0)
    en.vibrato(sc, LEAD, t0 + 33.25, 2.5, depth=0.24, delay=0.7)
    sc.note(LEAD, en.pitch(G4, "ionian", 5), t0 + 36.0, 3.0, 78,
            jt=0, jv=0)
    en.vibrato(sc, LEAD, t0 + 36.0, 2.9, depth=0.2, delay=0.8)
    en.portamento_off(sc, LEAD, t0 + 39.5)
    # Ooh bed and brushes at half intensity.
    ooh_degs = [3, 4, 5, 4, 3]
    for i, d in enumerate(ooh_degs):
        sc.note(OOH, en.pitch(G4, "ionian", d), t0 + 8.0 * i, 7.5, 44,
                jt=0, jv=3)
    _brush(sc, t0, 10, 0.4, tap=False, fills=False)
    _gtr_call(sc, t0 + 30.0, vel=68)


def swell_rise(sc) -> None:
    """Back in E minor: the front rolls in.  Strings gate in pp; sticks
    replace brushes; everything leans forward for eight bars."""
    t0 = 296.0
    _strings_bed(sc, t0, 8, RISE_PROG, vel=44, lo=48, hi=76,
                 swell=[(t0, 20), (t0 + 28.0, 84)])
    en.at_curve(sc, STRINGS, [(t0 + 4.0, 8), (t0 + 30.0, 66)], step=0.5)
    _organ_pad(sc, t0, 8, RISE_PROG, vel=40, lo=50, hi=72)
    en.leslie(sc, KEYS, t0, t0 + 30.0, 12, 44)
    en.at_curve(sc, KEYS, [(t0, 4), (t0 + 30.0, 72)], step=0.5)
    # Piano: pulsing octaves, rising register, from almost nothing.
    for i in range(8):
        b = t0 + 4.0 * i
        r = _root(RISE_PROG[i % 4], octave=1) + (12 if i >= 4 else 0)
        v = int(en.lerp(44, 78, i / 7))
        for k in range(8):
            sc.note(PIANO, r + (12 if k % 4 == 3 else 0), b + 0.5 * k,
                    0.45, v - (8 if k % 2 else 0),
                    jt=(0 if i == 0 and k == 0 else 3), jv=4)
    # Bass: eighth-note pedal walking the rise progression.
    for i in range(8):
        b = t0 + 4.0 * i
        r = _root(RISE_PROG[i % 4])
        v = int(en.lerp(70, 100, i / 7))
        for k in range(8):
            p = r + (7 if k in (3, 7) else (12 if k == 5 else 0))
            sc.note(BASS, p, b + 0.5 * k, 0.45, v - (6 if k % 2 else 0),
                    jt=(0 if i == 0 and k == 0 else 2), jv=3)
    # The band stacks in: arps from bar 1, strums bar 5, sticks bar 3.
    _gtr_arp(sc, t0, 8, RISE_PROG, vel=44, vel_end=74)
    _strum_bed(sc, t0 + 16.0, 4, RISE_PROG, vel=62)
    _kit_build(sc, t0 + 8.0, 6)


def swell_peak(sc) -> None:
    """The peak: the HOOK returns on the lead over the full band, then a
    four-bar climax cadence dissolves toward the reprise."""
    t0 = 328.0
    en.lyric(sc, t0, "hold up the sky")
    # The hook, twice, lead + echo-guitar unison (lead pinned jt=0).
    _hook(sc, LEAD, t0, 2, 104)
    _hook(sc, GTR_E, t0, 2, 92, jt=2, jv=3, throws=True)
    # Drive-guitar power chords (program 29 from this beat).
    peak_prog = RISE_PROG + RISE_PROG
    for i, deg in enumerate(peak_prog):
        b = t0 + 4.0 * i
        r = _root(deg)
        _power(sc, r, b, 2.4, 108, jt=0 if i == 0 else 2)
        _power(sc, r, b + 2.5, 0.45, 98, jt=2)
        _power(sc, r, b + 3.5, 0.45, 102, jt=2)
    _piano_anthem(sc, t0, 8, RISE_PROG, vel=98)
    _bass_line(sc, t0, _SWELL_BASS, reps=2, vel_lift=4)
    chords = [en.triad(E3, _MODE, d) for d in peak_prog] + \
             [en.triad(E3, _MODE, 6), en.triad(E3, _MODE, 7),
              en.triad(E3, _MODE, 1), en.triad(E3, _MODE, 1)]
    # Choir rides the whole peak, climax cadence included.
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=57, hi=79,
                 vel=70, legato=0.0)
    for i, d in enumerate([8, 7, 6, 8]):
        sc.note(OOH, en.pitch(E4, _MODE, d), t0 + 8.0 * i, 7.5, 62,
                jt=0, jv=3)
    sc.note(OOH, en.pitch(E4, _MODE, 8), t0 + 32.0, 11.0, 64, jt=0, jv=0)
    en.vowel_curve(sc, AAH, [(t0, 60), (t0 + 24.0, 100), (t0 + 40.0, 84)],
                   step=2.0)
    en.pad_block(sc, STRINGS, t0, chords, 4.0, size=4, lo=55, hi=79,
                 vel=72, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0, 70), (t0 + 28.0, 104),
                                (t0 + 44.0, 112), (t0 + 47.0, 44)], step=1.0)
    en.at_curve(sc, STRINGS, [(t0 + 4.0, 20), (t0 + 28.0, 88),
                              (t0 + 42.0, 100), (t0 + 46.0, 24)], step=0.5)
    en.pad_block(sc, KEYS, t0, chords, 4.0, size=3, lo=52, hi=74,
                 vel=66, legato=0.0)
    en.leslie(sc, KEYS, t0, t0 + 40.0, 44, 112)
    en.at_curve(sc, KEYS, [(t0, 24), (t0 + 24.0, 90), (t0 + 44.0, 96),
                           (t0 + 47.0, 18)], step=0.5)
    _kit_full(sc, t0, 8, vel=104)
    # Climax cadence (VI - VII - i): the lead holds a high tonic with a
    # blooming vibrato and one last echo throw; the band lands with it.
    for k, (deg, beat) in enumerate([(6, 32.0), (7, 36.0), (1, 40.0)]):
        r = _root(deg)
        _power(sc, r, t0 + beat, 3.4 if k < 2 else 7.4, 102 - 2 * k, jt=0)
        root = _root(deg, octave=1)
        for hit in (0.0, 2.0):
            sc.note(PIANO, root, t0 + beat + hit, 1.9, 94, jt=0, jv=3)
            for p in _triad(deg, octave=2):
                sc.note(PIANO, p, t0 + beat + hit, 1.9, 90, jt=0, jv=3)
        en.sustain(sc, PIANO, t0 + beat + 0.02, t0 + beat + 3.9)
        sc.note(BASS, r, t0 + beat, 3.7 if k < 2 else 7.0, 100, jt=0, jv=0)
        sc.hit(49 if k % 2 == 0 else 57, t0 + beat, 106, jt=0)
        sc.hit(36, t0 + beat, 102, jt=0)
    sc.note(BASS, _root(1), t0 + 44.0, 3.4, 88, jt=0, jv=0)
    for b in (33.0, 34.0, 35.0, 37.0, 38.0, 39.0):
        sc.hit(51, t0 + b, 78, jt=2, jv=4)
        sc.hit(36, t0 + b, 80, jt=2)
    for k in range(8):
        sc.hit(41 if k % 2 == 0 else 43, t0 + 40.0 + 0.5 * k, 88 - 3 * k,
               jt=2, jv=4)
    sc.hit(49, t0 + 44.0, 84, jt=0)
    sc.note(LEAD, en.pitch(E4, _MODE, 8), t0 + 32.0, 11.4, 102, jt=0, jv=0)
    en.vibrato(sc, LEAD, t0 + 32.0, 11.2, depth=0.28, delay=1.2)
    en.echo_throw(sc, GTR_E, t0 + 40.0, base=0, peak=96, release=3.0)
    sc.note(GTR_E, E4 + 12, t0 + 40.0, 3.4, 82, jt=0, jv=0)


def reprise(sc) -> None:
    """The quiet answer: the THEME comes home on the echo guitar, and the
    neon tag is stated dry then thrown — the CC94 audio probe."""
    t0 = 376.0
    en.soft_pedal(sc, PIANO, t0, t0 + 52.0)
    en.leslie(sc, KEYS, t0, t0 + 10.0, 60, 8)     # rotor brakes to a halt
    # Two settling bars: Em broken piano over a low pedal.
    for i in range(2):
        b = t0 + 4.0 * i
        for k, p in enumerate([52, 55, 59, 64, 59, 55, 52, 47]):
            sc.note(PIANO, p, b + 0.5 * k, 0.6, 44 - 2 * i,
                    jt=(0 if i == 0 and k == 0 else 3), jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
        sc.note(BASS, E2, b, 3.9, 66, jt=0, jv=0)
        sc.hit(40, b, 34, jt=0, jv=0)
        sc.hit(37, b + 2.0, 30, jt=0, jv=0)
    for p, v in ((40, 38), (47, 34), (52, 32)):
        sc.note(KEYS, p, t0, 7.9, v, jt=0, jv=2)
    en.pad_block(sc, STRINGS, t0, [en.triad(E3, _MODE, 1)], 8.0, size=3,
                 lo=52, hi=72, vel=34, legato=0.0)
    en.expr_curve(sc, STRINGS, [(t0, 52), (t0 + 7.5, 16)], step=1.0)
    # The THEME on the band's own instruments (oracle: prelude_recall).
    en.line(sc, GTR_E, t0 + 8.0, E4, _MODE, _THEME, 66, jt=0, jv=0,
            gate=0.99)
    rep_chords = [[1, 384.0], [6, 388.0], [4, 392.0], [6, 396.0]]
    for deg, b in rep_chords:
        tri = _triad(deg, octave=1)
        sc.note(PIANO, tri[0] - 12, b, 3.9, 48, jt=0, jv=3)
        for p in tri:
            sc.note(PIANO, p, b + 0.5, 3.4, 42, jt=3, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
        sc.note(BASS, _root(deg), b, 3.9, 62, jt=0, jv=0)
        sc.hit(40, b, 30, jt=0, jv=0)
        sc.hit(37, b + 2.0, 26, jt=0, jv=0)
    en.pad_block(sc, AAH, 384.0, [en.triad(E3, _MODE, 1)], 14.0, size=3,
                 lo=55, hi=76, vel=34, legato=0.0)
    sc.note(OOH, en.pitch(E4, _MODE, 5), 384.0, 13.5, 30, jt=0, jv=0)
    en.vowel(sc, AAH, 14, 384.0)
    # The A/B echo probe: identical bed + tag, dry at 400, thrown at 408.
    for b in (400.0, 404.0, 408.0, 412.0):
        for p, v in ((52, 50), (55, 46), (59, 44), (64, 40)):
            sc.note(PIANO, p, b, 3.9, v, jt=0, jv=0)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
        sc.note(BASS, E2, b, 3.9, 64, jt=0, jv=0)
        sc.hit(40, b, 28, jt=0, jv=0)
        sc.hit(37, b + 2.0, 24, jt=0, jv=0)
    for base in (400.0, 408.0):
        for off, beat, dur, vel in _TAG:
            sc.note(GTR_E, E4 + off, base + beat, dur, vel, jt=0, jv=0)
    en.echo_throw(sc, GTR_E, 408.9, base=0, peak=105, release=2.2)
    # Final cadence: iv -> i, the last high E rolled out on the echo bus.
    for chord, b in (((45, 52, 57, 60), 416.0), ((40, 52, 55, 59), 420.0)):
        for k, p in enumerate(chord):
            sc.note(PIANO, p, b, 3.9, 46 - 2 * k, jt=0, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    sc.note(BASS, E2 + 5, 416.0, 3.9, 62, jt=0, jv=0)
    sc.note(BASS, E2, 420.0, 3.9, 60, jt=0, jv=0)
    sc.hit(40, 416.0, 26, jt=0, jv=0)
    sc.hit(40, 420.0, 22, jt=0, jv=0)
    # Em(add9) hush: piano + a last organ breath + the thrown high E.
    for p, v in ((40, 34), (47, 30), (52, 28), (55, 26), (66, 26)):
        sc.note(KEYS, p, 424.0, 6.9, v, jt=0, jv=2)
    for k, p in enumerate((52, 59, 64, 66)):
        sc.note(PIANO, p, 424.0, 5.9, 44 - 2 * k, jt=0, jv=3)
    en.sustain(sc, PIANO, 424.02, 430.5)
    sc.note(BASS, E2, 424.0, 5.9, 58, jt=0, jv=0)
    sc.note(GTR_E, E4 + 12, 424.0, 3.0, 58, jt=0, jv=0)
    en.echo_throw(sc, GTR_E, 424.2, base=0, peak=88, release=3.5)
    sc.hit(40, 424.0, 20, jt=0, jv=0)
    sc.hit(46, 428.0, 18, jt=0, jv=0)
    en.expr_curve(sc, KEYS, [(424.0, 70), (430.5, 24)], step=0.5)
    en.expr_curve(sc, AAH, [(384.0, 60), (397.0, 20)], step=1.0)


BUILDERS = [prelude, verse1, chorus1, verse2, chorus2, bridge,
            swell_rise, swell_peak, reprise]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 16, 19, 25, 26, 29, 33, 48, 52, 53, 80}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, LEAD, KEYS, STRINGS, DRUMS}
NOTE_RANGES = {
    PIANO: (40, 92), GTR_E: (48, 84), GTR_W: (38, 78), BASS: (36, 64),
    AAH: (52, 84), OOH: (52, 88), LEAD: (55, 91), KEYS: (40, 76),
    STRINGS: (46, 82),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (261.0, 281.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.15),
    ("chorus2", ">=", "chorus1", 1.0),
    ("verse2", "<=", "chorus2", 0.9),
    ("bridge", "<=", "chorus2", 0.9),
    ("swell_peak", ">=", "chorus2", 1.1),
    ("swell_peak", ">=", "chorus1", 1.1),
    ("swell_rise", "<=", "swell_peak", 0.8),
    ("prelude", "<=", "chorus1", 0.9),
    ("reprise", "<=", "swell_peak", 0.45),
]
LATE_CHANNELS = {AAH: 208.0, OOH: 208.0, LEAD: 256.0, STRINGS: 296.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 4), ("chorus1", 4), ("verse2", 4),
                 ("chorus2", 4), ("swell_peak", 4)],
    "hook": "swell_peak",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH],
    "sections": ["chorus2", "swell_peak"],
}
FEATURES_EXPECTED = {
    "pitch_bend", "cc1_leslie", "cc68_legato", "cc64_sustain", "cc67_soft",
    "cc11_expression", "aftertouch", "portamento", "cc70_vowel",
    "cc94_echo", "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _melody(sc, ch: int, t0: float, t1: float):
    """(relative onset rounded to 1/4 beat, top pitch) per onset group —
    recomputed from the Score, never copied (recall-oracle discipline)."""
    import verify
    groups: dict[float, int] = {}
    for on, _off, p, _v in verify._note_spans(sc, ch):
        if t0 - 1e-9 <= on < t1:
            key = round((on - t0) * 4) / 4
            groups[key] = max(groups.get(key, 0), p)
    return [(k, groups[k]) for k in sorted(groups)]


def oracles(sc, info, spans):
    import verify

    # 1. The cathedral colour is confined to the prelude (HLD D9/R5):
    # every GM19 program event sits at the top of the file on the organ
    # channel; the organ demonstrably plays under GM19 inside the prelude;
    # and every organ note after the prelude sounds under a re-programmed
    # (non-19) voice.
    fails_cath: list[str] = []
    for ch in sorted(sc.events):
        if ch == 9:
            continue
        for beat, prog in verify._programs(sc, ch):
            if prog == 19 and not (ch == KEYS and beat <= 0.05):
                fails_cath.append(f"GM19 authored on ch{ch} at beat "
                                  f"{beat:.2f} (allowed only on the organ "
                                  f"at beat 0)")
    timeline = sorted(verify._programs(sc, KEYS))
    organ = verify._note_spans(sc, KEYS)
    prelude_notes = [on for on, _off, _p, _v in organ if on < PRELUDE_END]
    if not prelude_notes:
        fails_cath.append("the prelude has no cathedral-organ notes")
    elif verify._program_at(timeline, min(prelude_notes)) != 19:
        fails_cath.append("prelude organ notes do not sound under GM19")
    for on, _off, _p, _v in organ:
        if on >= PRELUDE_END - 1e-9 and \
                verify._program_at(timeline, on) == 19:
            fails_cath.append(f"organ note at beat {on:.2f} still sounds "
                              f"under GM19 after the prelude")
            break

    # 2. The reprise recalls the prelude THEME on the band's instruments:
    # the organ's prelude melody (top line, first statement) must equal the
    # echo guitar's reprise statement in rhythm and pitch class, both
    # recomputed from the Score.
    fails_recall: list[str] = []
    a = _melody(sc, KEYS, 8.0, 24.0)
    b = _melody(sc, GTR_E, 384.0, 400.0)
    if len(a) != len(b):
        fails_recall.append(f"prelude theme has {len(a)} onset groups, "
                            f"reprise recall has {len(b)}")
    else:
        for (ka, pa), (kb, pb) in zip(a, b):
            if abs(ka - kb) > 1e-6 or (pa - pb) % 12 != 0:
                fails_recall.append(
                    f"recall diverges at +{kb:.2f} beats "
                    f"(prelude pitch {pa} vs reprise {pb})")
                break

    # 3. The swell returns the chorus HOOK: the lead's first swell
    # statement equals the echo guitar's first chorus statement (rhythm +
    # pitch class), recomputed from the Score.
    fails_hook: list[str] = []
    ha = _melody(sc, GTR_E, 112.0, 128.0)
    hb = _melody(sc, LEAD, 328.0, 344.0)
    if len(ha) != len(hb):
        fails_hook.append(f"chorus hook has {len(ha)} onset groups, swell "
                          f"return has {len(hb)}")
    else:
        for (ka, pa), (kb, pb) in zip(ha, hb):
            if abs(ka - kb) > 1e-6 or (pa - pb) % 12 != 0:
                fails_hook.append(
                    f"hook return diverges at +{kb:.2f} beats "
                    f"(chorus pitch {pa} vs swell {pb})")
                break

    return [("cathedral_confined", verify._cap(fails_cath)),
            ("prelude_recall", fails_recall),
            ("hook_return", fails_hook)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds FROZEN at the phase-D album freeze (2026.07.11)
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# FROZEN at the phase-D assembled-album freeze (2026.07.11); pinned at
# measured - slack on the 2026-07-11 per-track render (ferrosintesis 0.13.x).
_LIFT_DB = 5.0        # measured +7.25 dB (peak -19.5 vs verse -26.8)
_ECHO_DB = 2.4        # measured +3.91 dB (wet -42.7 vs dry -46.6)
_RISE_DB = 2.5        # measured +4.09 dB (end -21.7 vs start -25.8)


def audio_checks(ctx):
    # 1. The swell is the track's dynamic peak: hook-return bars vs verse.
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(56.0, 104.0)
    p0, p1 = ctx.bar_window(328.0, 360.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    peak = ctx.db(ctx.rms(ctx.l, ctx.r, p0, p1))
    if peak < verse + _LIFT_DB:
        fails_lift.append(f"swell peak {peak:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # 2. The CC94 throw is audible: the reprise states the same staccato
    # tag twice over an identical bed — dry at 400, thrown at 408.  The
    # 0.75-beat ping-pong echoes land in the post-phrase window, so the
    # wet window must carry real extra energy.
    fails_echo: list[str] = []
    d0, d1 = ctx.bar_window(402.0, 403.6)
    w0, w1 = ctx.bar_window(410.0, 411.6)
    dry = ctx.db(ctx.rms(ctx.l, ctx.r, d0, d1))
    wet = ctx.db(ctx.rms(ctx.l, ctx.r, w0, w1))
    if wet < dry + _ECHO_DB:
        fails_echo.append(f"echo window {wet:.1f} dB < dry window "
                          f"{dry:.1f} dB + {_ECHO_DB}")

    # 3. The aftertouch/expression swell rises: the end of swell_rise
    # sits well above its start.
    fails_rise: list[str] = []
    a0, a1 = ctx.bar_window(296.0, 304.0)
    b0, b1 = ctx.bar_window(320.0, 328.0)
    lo = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    hi = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    if hi < lo + _RISE_DB:
        fails_rise.append(f"swell rise end {hi:.1f} dB < start "
                          f"{lo:.1f} dB + {_RISE_DB}")

    return [("swell_lift", fails_lift),
            ("echo_throw_audible", fails_echo),
            ("swell_build_rise", fails_rise)]
