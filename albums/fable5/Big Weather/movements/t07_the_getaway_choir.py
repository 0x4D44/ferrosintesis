"""t07_the_getaway_choir.py — "The Getaway Choir" (Big Weather, track 7).

THE CHOIR FEATURE: gospel-tinged rock in B minor rising to D major at
124 BPM.  Three choir channels sing true SATB-style layers — the eh
sopranos (GM54) carry the whistleable descant HOOK (oracle-pinned to
recur identically in both B-minor choruses and, diatonically re-rooted,
in the D-major lift), the aahs (GM52) are the voice-led body, and the
oohs (GM53) walk a bass-ish counter-line (satb_choir oracle: registral
order, rhythmic independence, moving counter).  CC70 vowel morphs are
the featured device: every chorus MOVES through vowels, the vamp trades
oo/AH per answer, and the a-cappella tag morphs oo -> eh across its
midpoint (headline audio probe: HF-tilt rise between the tag halves).
The vamp is strict piano/choir antiphony — twelve 8-beat cells, piano
calls in the first half, choir answers landing on beat 5 (antiphony
oracle; bass + drums are the declared rhythm section underneath).  The
tag is choir + claps/tambourine ONLY (tag_purity oracle).  The key-lift
chorus re-roots the same degree material from B aeolian to its relative
D ionian (same two-sharp collection, keysig grid flips minor -> major),
with a light drive guitar gated to enter there (LATE_CHANNELS).

Form (HLD 4, bespoke):
  intro (piano+choir) | verse1 | chorus1 | verse2 | chorus2 |
  vamp (call-and-response) | lift_chorus (D major) | tag (a cappella) |
  outro
"""

from __future__ import annotations

import math

import conductor
import engine as en

NUMBER = 7
TITLE = "The Getaway Choir"
FILE = "07 - The Getaway Choir.mid"
SEED = 20260707

BPM = 124.0

# Channels (HLD 3; organ/strings/brass/timpani deliberately absent —
# the choir IS the orchestra on this track).
PIANO, GTR_C, GTR_D, BASS = 0, 1, 2, 3
AAH, OOH, DRUMS, EH = 4, 5, 9, 12

_SECTIONS = [
    ("intro",         0.0,  32.0),
    ("verse1",       32.0,  96.0),
    ("chorus1",      96.0, 160.0),
    ("verse2",      160.0, 224.0),
    ("chorus2",     224.0, 288.0),
    ("vamp",        288.0, 384.0),
    ("lift_chorus", 384.0, 464.0),
    ("tag",         464.0, 496.0),
    ("outro",       496.0, 528.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 2, 1), (384.0, 2, 0)],   # B minor -> D major (the lift)
    channels=[
        (PIANO, "piano",         0, 100, 64, 50),
        (GTR_C, "clean guitar", 26,  90, 48, 40),
        (GTR_D, "drive guitar", 29,  86, 80, 35),
        (BASS,  "bass guitar",  33, 105, 64, 25),
        (AAH,   "choir aah",    52,  96, 64, 70),
        (OOH,   "choir ooh",    53,  92, 64, 70),
        (DRUMS, "drums",         0, 104, 64, 45),
        (EH,    "choir eh",     54,  95, 64, 72),
    ],
    extra_markers=[(384.0, "key lift: D major")],
)

# ---------------------------------------------------------------------------
# Harmony.  B aeolian for the body of the song; the lift chorus re-roots
# the SAME degree material to D ionian — the relative major shares the
# two-sharp collection, so the hook rises a diatonic third and the world
# turns from dusk to daylight without a single accidental.
# ---------------------------------------------------------------------------

B2, B3 = en.n("B2"), en.n("B3")
D2, D3, D4 = en.n("D2"), en.n("D3"), en.n("D4")
_MIN, _MAJ = "aeolian", "ionian"

VERSE_PROG = [1, 3, 7, 6]        # Bm  D   A   G
CHORUS_PROG = [1, 6, 4, 5]       # Bm  G   Em  F#m  |  lift: D  Bm  G  A
INTRO_PROG = [1, 6, 4, 5]        # two bars each
TAG_PROG = [1, 6, 4, 5, 1, 4, 5, 1]          # D ionian, one chord per bar
_TAG_EH = [8, 6, 5, 7, 8, 5, 7, 8]           # tag soprano top line

# The chorus HOOK — (degree, start, dur) over 16 beats, sung by the eh
# sopranos above the pad (oracle: satb_choir pins its exact recurrence
# in chorus1/chorus2 and its D-ionian re-rooting in the lift).  Offbeat
# entries keep it rhythmically independent of the aah pad (onsets never
# within 0.3 beats of the pad's 4-beat grid).
_HOOK = [
    (5, 0.5, 1.0), (8, 1.5, 1.5), (7, 3.0, 0.9),
    (6, 4.5, 1.0), (5, 5.5, 1.5), (3, 7.0, 0.9),
    (4, 8.5, 1.0), (6, 9.5, 1.5), (8, 11.0, 0.9),
    (7, 12.5, 1.0), (9, 13.5, 2.4),
]

# The ooh counter-line — (degree, start, dur) over 16 beats, a bass-ish
# inner voice under the pad (relative to B2 / D3), jt=0 throughout.
_COUNTER = [
    (8, 0.0, 2.0), (7, 2.0, 2.0), (6, 4.0, 2.0), (8, 6.0, 2.0),
    (4, 8.0, 2.0), (6, 10.0, 2.0), (5, 12.0, 3.5),
]

# The vamp bass HOOK — pinned riff (semitone offsets from the cell root,
# jt=0): a pentatonic climb-and-fall that walks the whole cell.
_VAMP_RIFF = [
    (0.0, 0, 0.70, 0), (0.75, 0, 0.20, -26), (1.0, 3, 0.45, -6),
    (1.5, 5, 0.45, -8), (2.0, 7, 0.90, 0), (3.0, 10, 0.45, -6),
    (3.5, 12, 0.45, -4), (4.0, 10, 0.90, -2), (5.0, 7, 0.45, -8),
    (5.5, 5, 0.45, -10), (6.0, 3, 0.90, -4), (7.0, -2, 0.45, -8),
    (7.5, 0, 0.45, -6),
]

_LYRICS = [(96.0, "get away"), (224.0, "get away, get away"),
           (384.0, "carry us home"), (464.0, "oo... eh!")]


def _fold(p: int, hi: int = 62) -> int:
    """Fold a bass pitch down an octave when it climbs out of the pocket."""
    return p - 12 if p > hi else p


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------

def _piano_verse(sc, t0: float, bars: int, prog, base_lo: int, base_mid: int,
                 mode: str, vel: int = 66) -> None:
    """Verse comp: LH root+fifth pulse, RH off-beat gospel dyads."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        r = en.pitch(base_lo, mode, d)
        tri = en.triad(base_mid, mode, d)
        jt0 = 0 if i == 0 else 3
        sc.note(PIANO, r, b, 1.9, vel + 6, jt=jt0, jv=4)
        sc.note(PIANO, r + 7, b + 2.0, 1.4, vel, jt=3, jv=4)
        for beat, dur in ((1.5, 0.8), (3.0, 0.8)):
            sc.note(PIANO, tri[1], b + beat, dur, vel - 6, jt=3, jv=4)
            sc.note(PIANO, tri[2], b + beat, dur, vel - 8, jt=3, jv=4)
        if i % 4 == 3:                          # turn into the next phrase
            sc.note(PIANO, tri[0] + 12, b + 3.5, 0.45, vel - 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_gospel(sc, t0: float, bars: int, prog, base_lo: int,
                  base_mid: int, mode: str, vel: int = 86) -> None:
    """Chorus comp: driving chords with an add9 shimmer and a push."""
    for i in range(bars):
        b = t0 + 4.0 * i
        d = prog[i % len(prog)]
        r = en.pitch(base_lo, mode, d)
        chord = en.triad(base_mid, mode, d)
        if i % 2 == 1:
            chord = chord + [en.pitch(base_mid, mode, d + 8)]   # add9
        jt0 = 0 if i == 0 else 3
        sc.note(PIANO, r, b, 1.9, vel + 5, jt=jt0, jv=4)
        sc.note(PIANO, r + 7, b + 2.0, 1.9, vel - 2, jt=3, jv=4)
        for beat, dur, dv in ((0.0, 0.9, 0), (1.5, 0.4, -8),
                              (2.0, 0.9, -3), (3.5, 0.4, -6)):
            for p in chord:
                sc.note(PIANO, p, b + beat, dur, vel + dv, jt=jt0 if
                        beat == 0.0 else 3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _piano_call(sc, c0: float, d: int, vel: int) -> None:
    """One vamp CALL: a chord stab and an ascending, question-shaped
    lick, all onsets inside [c0, c0+3.9) (the antiphony oracle's half)."""
    r = en.pitch(B3, _MIN, d)
    tri = en.triad(B3, _MIN, d)
    sc.note(PIANO, r - 12, c0, 0.55, vel + 6, jt=2, jv=3)
    for p in tri:
        sc.note(PIANO, p, c0, 0.55, vel, jt=2, jv=3)
    for k, off in enumerate((4, 5, 6, 7)):      # 16th climb
        sc.note(PIANO, en.pitch(B3, _MIN, d + off), c0 + 1.0 + 0.25 * k,
                0.22, vel - 10 + 3 * k, jt=2, jv=3)
    sc.note(PIANO, en.pitch(B3, _MIN, d + 8), c0 + 2.0, 0.5, vel + 4,
            jt=2, jv=3)
    sc.note(PIANO, en.pitch(B3, _MIN, d + 7), c0 + 3.0, 0.85, vel - 2,
            jt=2, jv=3)
    en.sustain(sc, PIANO, c0 + 0.02, c0 + 3.85)


def _bass_verse(sc, t0: float, prog, base: int, mode: str, reps: int = 1,
                vel: int = 96) -> None:
    """Verse bass: a singing walk — root, descent from the octave,
    stepwise approach into every next root."""
    seq = list(prog) * reps
    for i, d in enumerate(seq):
        b = t0 + 4.0 * i
        r = _fold(en.pitch(base, mode, d))
        nr = _fold(en.pitch(base, mode, seq[(i + 1) % len(seq)]))
        app = nr - 1 if nr > r else nr + 2
        sc.note(BASS, r, b, 0.95, vel, jt=0 if i == 0 else 2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 7)), b + 1.0, 0.45,
                vel - 8, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 5)), b + 1.5, 0.45,
                vel - 10, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 4)), b + 2.0, 0.70,
                vel - 4, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 4)), b + 2.75, 0.20,
                max(20, vel - 30), jt=3, jv=5)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 2)), b + 3.0, 0.45,
                vel - 8, jt=2, jv=3)
        sc.note(BASS, app, b + 3.5, 0.45, vel - 6, jt=2, jv=3)


def _bass_chorus(sc, t0: float, prog, base: int, mode: str, reps: int = 1,
                 vel: int = 102) -> None:
    """Chorus bass: octave pop then a stepwise strut down the scale."""
    seq = list(prog) * reps
    for i, d in enumerate(seq):
        b = t0 + 4.0 * i
        r = _fold(en.pitch(base, mode, d))
        nr = _fold(en.pitch(base, mode, seq[(i + 1) % len(seq)]))
        app = nr - 1 if nr > r else nr + 2
        sc.note(BASS, r, b, 0.70, vel, jt=0 if i == 0 else 2, jv=3)
        pop = r + 12 if r + 12 <= 62 else r + 7     # octave (or fifth) pop
        sc.note(BASS, pop, b + 0.75, 0.30, vel - 10, jt=2, jv=3)
        sc.note(BASS, r, b + 1.0, 0.45, vel - 6, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 4)), b + 1.5, 0.45,
                vel - 8, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 5)), b + 2.0, 0.70,
                vel - 4, jt=2, jv=3)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 4)), b + 2.75, 0.20,
                max(20, vel - 28), jt=3, jv=5)
        sc.note(BASS, _fold(en.pitch(base, mode, d + 2)), b + 3.0, 0.45,
                vel - 8, jt=2, jv=3)
        sc.note(BASS, app, b + 3.5, 0.45, vel - 6, jt=2, jv=3)


def _gtr_chorus(sc, t0: float, bars: int, prog, base: int, mode: str,
                vel: int = 72) -> None:
    """Clean guitar: gospel push strums (down down down-up ... up)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        tri = en.triad(base, mode, prog[i % len(prog)])
        chord = tri + [tri[0] + 12]
        for beat, dur, down, dv in ((0.0, 0.7, True, 0), (1.0, 0.45, True, -8),
                                    (2.0, 0.7, True, -2), (2.75, 0.4, False, -12),
                                    (3.5, 0.45, False, -8)):
            en.strum(sc, GTR_C, chord, b + beat, dur, vel + dv,
                     spread=0.02, down=down)


def _drive_bed(sc, t0: float, bars: int, prog, base: int, mode: str,
               vel: int = 92) -> None:
    """Drive guitar: light power-chord bed with a gospel push."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = en.pitch(base, mode, prog[i % len(prog)])
        if r > 57:
            r -= 12
        jt0 = 0 if i == 0 else 2
        for beat, dur, dv in ((0.0, 1.9, 0), (2.0, 0.4, -8), (2.5, 1.4, -4)):
            for k, off in enumerate((0, 7, 12)):
                sc.note(GTR_D, r + off, b + beat, dur, vel + dv - 4 * k,
                        jt=jt0 if beat == 0.0 else 2, jv=3)


def _choir_pad(sc, t0: float, bars: int, prog, base: int, mode: str,
               vel: int = 66) -> None:
    """The aah body: voice-led three-part pad, one chord per bar."""
    chords = [en.triad(base, mode, prog[i % len(prog)]) for i in range(bars)]
    en.pad_block(sc, AAH, t0, chords, 4.0, size=3, lo=57, hi=76,
                 vel=vel, legato=0.0)


def _choir_counter(sc, t0: float, reps: int, base: int, mode: str,
                   vel: int = 62) -> None:
    """The ooh counter-line (16 beats per statement, jt=0 pinned)."""
    for rep in range(reps):
        for deg, start, dur in _COUNTER:
            sc.note(OOH, en.pitch(base, mode, deg), t0 + 16.0 * rep + start,
                    dur, vel, jt=0, jv=3)


def _choir_hook(sc, t0: float, reps: int, base: int, mode: str,
                vel: int = 84) -> None:
    """The eh descant hook (jt=0 — oracle-pinned) + CC1 blooms on holds."""
    for rep in range(reps):
        b0 = t0 + 16.0 * rep
        en.line(sc, EH, b0, base, mode, _HOOK, vel, jt=0, jv=0, gate=0.96)
        for _deg, start, dur in _HOOK:
            if dur >= 1.5:
                b = b0 + start
                en.cc_curve(sc, EH, 1, [(b + 0.25, 0), (b + dur * 0.6, 52),
                                        (b + dur, 10)], step=0.15)


def _kit(sc, t0: float, bars: int, x: float, *, claps: bool = False,
         tamb: bool = False, sticks: bool = False, four: bool = False,
         crash_in: bool = False, fills: bool = True,
         china: bool = False) -> None:
    """The kit: gospel-rock pocket.  x = intensity 0..1."""
    for i in range(bars):
        b = t0 + 4.0 * i
        v = int(round(en.lerp(66, 102, x)))
        fill = fills and (i % 8 == 7 or i == bars - 1)
        if crash_in and i == 0:
            sc.hit(49, b, min(120, v + 16), jt=0)
        if china and i % 4 == 2:
            sc.hit(52, b, v + 4, jt=2)
        if four:
            for q in range(4):
                sc.hit(36, b + q, v + (6 if q == 0 else -2), jt=2)
        else:
            sc.hit(36, b, v + 6, jt=2)
            sc.hit(36, b + 2.5, v, jt=2)
            if x > 0.55 and i % 2 == 1:
                sc.hit(36, b + 3.5, v - 6, jt=2)
        key = 37 if sticks else 38
        for q in (1.0, 3.0):
            sc.hit(key, b + q, v + 9, jt=2, jv=4)
            if claps:
                sc.hit(39, b + q, v + 3, jt=3, jv=5)
        if not sticks and x < 0.9:
            sc.hit(38, b + 1.75, max(16, v - 48), jt=3, jv=6)
        for k in range(8):
            if fill and k >= 5:
                continue
            sc.hit(42, b + 0.5 * k, max(18, v - (12 if k % 2 == 0 else 26)),
                   jt=2, jv=5)
        if i % 2 == 1 and not fill:
            sc.hit(46, b + 3.5, v - 16, jt=2)
        if tamb:
            for k in range(8):
                if k == 5 and not four:
                    continue        # lift off the kick's &-of-2 push
                sc.hit(54, b + 0.5 * k, max(16, v - (22 if k % 2 == 0
                                                     else 34)), jt=3, jv=5)
        if fill:
            for k, key2 in enumerate((48, 47, 45, 43, 41, 38, 43, 41)):
                sc.hit(key2, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 16, v + 14, k / 7)), jt=2)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    """Piano + choir only: arpeggi under an mm -> oo choir bloom, the
    piano foreshadowing the chorus hook in its last four bars."""
    for i in range(4):                          # 2 bars per chord
        b = 8.0 * i
        d = INTRO_PROG[i]
        r = en.pitch(B2, _MIN, d)
        tri = en.triad(B3, _MIN, d)
        jt0 = 0 if i == 0 else 3
        sc.note(PIANO, r, b, 3.8, 60, jt=jt0, jv=3)
        seq = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2], tri[1]]
        for k, p in enumerate(seq):
            sc.note(PIANO, p, b + 0.5 + 0.5 * k, 0.7, 52 + 2 * (k % 3),
                    jt=jt0 if k == 0 else 3, jv=4)
        sc.note(PIANO, tri[2], b + 4.0, 1.4, 54, jt=3, jv=4)
        sc.note(PIANO, tri[1], b + 5.5, 1.4, 50, jt=3, jv=4)
        sc.note(PIANO, tri[0], b + 7.0, 0.9, 48, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 7.9)
    en.soft_pedal(sc, PIANO, 0.0, 30.0)
    en.line(sc, PIANO, 16.0, B3 + 12, _MIN, _HOOK, 58, jt=3, jv=4)
    chords = [en.triad(B3, _MIN, d) for d in INTRO_PROG]
    en.pad_block(sc, AAH, 0.0, chords, 8.0, size=3, lo=57, hi=74,
                 vel=54, legato=0.0)
    for i, d in enumerate(INTRO_PROG):
        sc.note(OOH, _fold(en.pitch(B2, _MIN, d), 55), 8.0 * i, 7.5, 50,
                jt=0, jv=3)
    en.vowel_curve(sc, AAH, [(0.0, 8), (16.0, 42), (30.0, 58)], step=2.0)
    en.vowel_curve(sc, OOH, [(0.0, 8), (16.0, 40), (30.0, 50)], step=2.0)
    en.expr_curve(sc, AAH, [(0.0, 58), (24.0, 88), (31.0, 80)], step=1.0)
    en.expr_curve(sc, OOH, [(0.0, 58), (24.0, 84), (31.0, 78)], step=1.0)


def verse1(sc) -> None:
    _piano_verse(sc, 32.0, 16, VERSE_PROG, B2, B3, _MIN)
    _bass_verse(sc, 32.0, VERSE_PROG, B2, _MIN, reps=4)
    _kit(sc, 32.0, 16, 0.45, sticks=True, crash_in=True)


def _chorus(sc, t0: float, *, vel_lift: int = 0, vowels, tamb: bool = True,
            intensity: float = 0.8) -> None:
    """One 16-bar B-minor chorus: full band + three-layer SATB choir."""
    _piano_gospel(sc, t0, 16, CHORUS_PROG, B2, B3, _MIN, vel=84 + vel_lift)
    _gtr_chorus(sc, t0, 16, CHORUS_PROG, B3, _MIN, vel=72 + vel_lift)
    _bass_chorus(sc, t0, CHORUS_PROG, B2, _MIN, reps=4, vel=100 + vel_lift)
    _kit(sc, t0, 16, intensity, claps=True, tamb=tamb, crash_in=True)
    _choir_pad(sc, t0, 16, CHORUS_PROG, B3, _MIN, vel=64 + vel_lift)
    _choir_counter(sc, t0, 4, B2, _MIN, vel=60 + vel_lift)
    _choir_hook(sc, t0, 4, B3, _MIN, vel=82 + vel_lift)
    en.vowel_curve(sc, AAH, vowels, step=2.0)
    en.vowel_curve(sc, OOH, [(t0, 30), (t0 + 32.0, 46), (t0 + 63.0, 56)],
                   step=2.0)
    en.vowel_curve(sc, EH, [(t0, 68), (t0 + 24.0, 100), (t0 + 48.0, 112),
                            (t0 + 63.0, 90)], step=2.0)
    en.expr_curve(sc, AAH, [(t0, 78), (t0 + 32.0, 96), (t0 + 63.0, 88)],
                  step=1.0)
    en.expr_curve(sc, EH, [(t0, 82), (t0 + 48.0, 100), (t0 + 63.0, 92)],
                  step=1.0)


def chorus1(sc) -> None:
    _chorus(sc, 96.0, vowels=[(96.0, 44), (120.0, 84), (152.0, 96),
                              (158.0, 68)])


def verse2(sc) -> None:
    t0 = 160.0
    _piano_verse(sc, t0, 16, VERSE_PROG, B2, B3, _MIN, vel=70)
    _bass_verse(sc, t0, VERSE_PROG, B2, _MIN, reps=4, vel=98)
    _kit(sc, t0, 16, 0.55, crash_in=True)
    # The choir hums low under the second verse — the front is closer.
    chords = [en.triad(B3, _MIN, VERSE_PROG[i % 4]) for i in range(8)]
    en.pad_block(sc, AAH, t0, chords, 8.0, size=3, lo=57, hi=72,
                 vel=44, legato=0.0)
    for i in range(4):
        d = VERSE_PROG[(2 * i) % 4]
        sc.note(OOH, _fold(en.pitch(B2, _MIN, d), 55), t0 + 16.0 * i, 7.5,
                42, jt=0, jv=3)
    en.vowel_curve(sc, AAH, [(t0, 20), (t0 + 32.0, 40), (t0 + 63.0, 48)],
                   step=2.0)


def chorus2(sc) -> None:
    _chorus(sc, 224.0, vel_lift=3, intensity=0.85,
            vowels=[(224.0, 40), (248.0, 88), (272.0, 108), (286.0, 72)])


def vamp(sc) -> None:
    """Call-and-response: twelve 8-beat cells — the piano asks in the
    first half of each cell, the choir answers G -> A (oo -> AH!) in the
    second, over the pinned bass riff and a four-on-the-floor pocket.
    The constant VI->VII answer is a long dominant preparation: the last
    A chord resolves straight onto the D-major lift."""
    t0 = 288.0
    for k in range(12):
        c0 = t0 + 8.0 * k
        d = 1 if k % 2 == 0 else 4              # Bm / Em call harmony
        _piano_call(sc, c0, d, vel=82 + k)
        if k % 4 == 3:
            en.echo_throw(sc, PIANO, c0 + 3.5, base=0, peak=76, release=2.0)
        # The bass riff (the track's bass HOOK, jt=0, root-adapted).
        root = B2 if k % 2 == 0 else B2 + 5
        for beat, off, dur, dv in _VAMP_RIFF:
            sc.note(BASS, root + off, c0 + beat, dur,
                    max(20, 96 + k // 2 + dv), jt=0, jv=3)
        # The choir answer: two chords, oo then AH (vowel trading).
        av = 72 + k
        for ch, pitches in ((AAH, (59, 62)), (OOH, (55,)), (EH, (67,))):
            if ch == EH and k < 4:
                continue                        # sopranos join from cell 5
            for p in pitches:
                sc.note(ch, p, c0 + 4.0, 1.4, av - 4, jt=0, jv=3)
            for p in pitches:
                sc.note(ch, p + 2, c0 + 5.5, 2.4, av, jt=0, jv=3)
            en.vowel(sc, ch, 46, c0 + 4.0)
            en.vowel(sc, ch, 92, c0 + 5.5)
    _kit(sc, t0, 24, 0.62, claps=True, tamb=True, four=True, fills=False)


def lift_chorus(sc) -> None:
    """The key lift: the same degree material re-rooted to D ionian —
    four hook statements plus a 16-beat climax (drive guitar enters,
    aftertouch swell, CC68 soprano melisma into the held apex)."""
    t0 = 384.0
    _piano_gospel(sc, t0, 16, CHORUS_PROG, D3, D4, _MAJ, vel=90)
    _gtr_chorus(sc, t0, 16, CHORUS_PROG, D4, _MAJ, vel=76)
    _drive_bed(sc, t0, 20, CHORUS_PROG, D3, _MAJ, vel=90)
    _bass_chorus(sc, t0, CHORUS_PROG, D2, _MAJ, reps=4, vel=104)
    _kit(sc, t0, 16, 0.92, claps=True, tamb=True, crash_in=True, china=True)
    _choir_pad(sc, t0, 16, CHORUS_PROG, D4, _MAJ, vel=70)
    _choir_counter(sc, t0, 4, D3, _MAJ, vel=64)
    _choir_hook(sc, t0, 4, D4, _MAJ, vel=86)
    en.vowel_curve(sc, AAH, [(t0, 50), (t0 + 24.0, 96), (t0 + 56.0, 118),
                             (t0 + 78.0, 104)], step=2.0)
    en.vowel_curve(sc, OOH, [(t0, 36), (t0 + 40.0, 60), (t0 + 78.0, 70)],
                   step=2.0)
    en.vowel_curve(sc, EH, [(t0, 80), (t0 + 32.0, 112), (t0 + 78.0, 120)],
                   step=2.0)
    # Climax bars 17-20: held SATB + piano + drive, soprano melisma apex.
    c0 = t0 + 64.0
    for i, d in enumerate((6, 4, 5, 1)):
        b = c0 + 4.0 * i
        r = en.pitch(D3, _MAJ, d)
        chord = en.triad(D4, _MAJ, d)
        sc.note(PIANO, r - 12 if r - 12 >= 43 else r, b, 3.8, 96, jt=0, jv=3)
        for p in chord:
            sc.note(PIANO, p, b, 3.8, 92, jt=0, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
    chords = [en.triad(D4, _MAJ, d) for d in (6, 4, 5, 1)]
    en.pad_block(sc, AAH, c0, chords, 4.0, size=3, lo=57, hi=76,
                 vel=74, legato=0.0)
    for i, d in enumerate((6, 4, 5, 1)):
        sc.note(OOH, _fold(en.pitch(D3, _MAJ, d), 55), c0 + 4.0 * i, 3.8,
                66, jt=0, jv=3)
    en.run(sc, EH, c0, D4, _MAJ, [3, 4, 5, 6, 8, 9, 10], 0.25, 76, 94,
           legato=True)
    apex = en.pitch(D4, _MAJ, 10)
    sc.note(EH, apex, c0 + 2.0, 12.5, 94, jt=0, jv=0)
    en.cc_curve(sc, EH, 1, [(c0 + 2.5, 0), (c0 + 8.0, 58), (c0 + 14.0, 12)],
                step=0.2)
    en.at_curve(sc, AAH, [(c0, 18), (c0 + 8.0, 88), (c0 + 14.0, 26)],
                step=0.5)
    _kit(sc, c0, 4, 0.95, claps=True, tamb=True, crash_in=True,
         fills=True)
    # Park the choir lanes for the tag: expression steady, mouths ready.
    for ch in (AAH, OOH, EH):
        en.expr_curve(sc, ch, [(c0 + 8.0, 100), (c0 + 15.0, 100)], step=2.0)


_TAG_T0 = 464.0


def tag(sc) -> None:
    """A-cappella-style: SATB choir + claps/tambourine ONLY.  Both
    halves share the same rhythm; only the vowel moves (oo -> eh across
    the midpoint) — the headline audio probe measures the HF-tilt rise
    between the halves, so the percussion pattern is kept identical."""
    t0 = _TAG_T0
    prev = None
    for i, d in enumerate(TAG_PROG):
        b = t0 + 4.0 * i
        up = 8 if i >= 4 else 0                 # the eh half leans in
        pcs = en.triad(D3, _MAJ, d)
        prev = en.voice_lead(pcs, prev, 3, 60, 72)
        for p in prev:                          # the aah body, three voices
            sc.note(AAH, p, b, 3.9, 76 + up, jt=0, jv=2)
        r = en.pitch(D3, _MAJ, d)               # the ooh bass root
        sc.note(OOH, r - 12 if r > 52 else r, b, 3.9, 74 + up, jt=0, jv=2)
        main = en.pitch(D4, _MAJ, _TAG_EH[i])   # the eh top line
        if i == len(TAG_PROG) - 1:
            sc.note(EH, main, b, 3.9, 82 + up, jt=0, jv=0)
        else:
            sc.note(EH, main, b, 2.4, 80 + up, jt=0, jv=0)
            sc.note(EH, en.pitch(D4, _MAJ, _TAG_EH[i] - 1), b + 2.5, 1.4,
                    76 + up, jt=0, jv=0)
        for q in (1.0, 3.0):                    # claps on 2 and 4
            sc.hit(39, b + q, 78, jt=2, jv=3)
        for k in range(8):                      # tambourine eighths
            sc.hit(54, b + 0.5 * k, 44 if k % 2 == 0 else 34, jt=2, jv=3)
    for ch in (AAH, OOH, EH):                   # the featured morph
        en.vowel(sc, ch, 38, t0)
        en.vowel_curve(sc, ch, [(t0 + 16.0, 38), (t0 + 20.0, 118)],
                       step=0.5)


def outro(sc) -> None:
    """Plagal amens: piano G -> D over a closing-mouth choir hum."""
    t0 = 496.0
    for i in range(8):
        b = t0 + 4.0 * i
        d = 4 if i % 2 == 0 else 1              # G . D . amens
        r = en.pitch(D3, _MAJ, d)
        r = r - 12 if r > 52 else r
        chord = en.triad(D4, _MAJ, d)
        vel = int(en.lerp(72, 46, i / 7))
        if i < 7:
            sc.note(PIANO, r, b, 3.8, vel + 4, jt=0 if i == 0 else 3, jv=3)
            for p in chord:
                sc.note(PIANO, p, b, 3.8, vel, jt=0 if i == 0 else 3, jv=3)
            en.sustain(sc, PIANO, b + 0.02, b + 3.9)
        if i < 4:
            sc.note(BASS, r - 12 if r - 12 >= 38 else r, b, 3.6, vel + 10,
                    jt=0 if i == 0 else 2, jv=3)
            sc.hit(36, b, 52, jt=2)
            sc.hit(42, b + 2.0, 34, jt=2)
    # Final Dadd9, held to the last bar with the choir breathing out.
    final = t0 + 28.0
    for p in (50, 62, 66, 69, 76):
        sc.note(PIANO, p, final, 3.6, 56, jt=0, jv=2)
    en.sustain(sc, PIANO, final + 0.02, final + 3.8)
    chords = [en.triad(D4, _MAJ, 1)] * 2
    en.pad_block(sc, AAH, t0 + 16.0, chords, 8.0, size=3, lo=57, hi=74,
                 vel=52, vel_end=40, legato=0.0)
    sc.note(OOH, 50, t0 + 16.0, 15.5, 46, jt=0, jv=2)
    sc.note(EH, 74, t0 + 24.0, 7.5, 48, jt=0, jv=2)
    for ch in (AAH, OOH, EH):
        en.vowel_curve(sc, ch, [(t0, 96), (t0 + 12.0, 40), (t0 + 28.0, 10)],
                       step=1.0)
        en.expr_curve(sc, ch, [(t0 + 16.0, 92), (t0 + 31.0, 58)], step=1.0)
    for beat, text in _LYRICS:
        en.lyric(sc, beat, text)


BUILDERS = [intro, verse1, chorus1, verse2, chorus2, vamp, lift_chorus,
            tag, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD 6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 26, 29, 33, 52, 53, 54}
CENTERED_CHANNELS = {PIANO, BASS, AAH, OOH, DRUMS, EH}
NOTE_RANGES = {
    PIANO: (40, 92), GTR_C: (50, 86), GTR_D: (43, 74), BASS: (36, 64),
    AAH: (54, 78), OOH: (43, 62), EH: (60, 80),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (246.0, 266.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# Factors carry >= 10% headroom against measured energies (2026.07.11:
# intro 521, verse1 994, chorus1 3275, verse2 1162, chorus2 3372,
# vamp 1473, lift 4025, tag 980, outro 649).
ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "chorus1", 0.9),
    ("chorus2", ">=", "verse2", 1.2),
    ("vamp", "<=", "chorus2", 0.9),
    ("lift_chorus", ">=", "chorus1", 1.05),
    ("lift_chorus", ">=", "chorus2", 1.0),
    ("tag", "<=", "lift_chorus", 0.5),
    ("intro", "<=", "chorus1", 0.6),
    ("outro", "<=", "lift_chorus", 0.6),
]
LATE_CHANNELS = {BASS: 32.0, DRUMS: 32.0, GTR_C: 96.0, EH: 96.0,
                 GTR_D: 384.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 11), ("chorus1", 11), ("verse2", 11),
                 ("chorus2", 11), ("lift_chorus", 2)],
    "hook": "vamp",
}
CHOIR_SPEC = {
    "channels": [AAH, OOH, EH],
    "sections": ["chorus1", "chorus2", "vamp", "lift_chorus", "tag"],
}
FEATURES_EXPECTED = {
    "cc70_vowel", "cc64_sustain", "cc67_soft", "cc11_expression",
    "cc68_legato", "cc94_echo", "aftertouch", "cc1_vibrato",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def _rel_set(sc, ch, t0, t1):
    """{(rel onset rounded to 16th, pitch)} for a pinned (jt=0) line."""
    return {(round((on - t0) * 4) / 4, p) for on, _off, p, _v
            in _spans(sc, ch) if t0 - 1e-9 <= on < t1 - 1e-9}


def oracles(sc, info, spans):
    # 1. antiphony — the vamp really is call-and-response: in each of
    #    the twelve 8-beat cells the piano speaks only in [c0, c0+3.9)
    #    and the choir answers within half a beat of beat 5, never
    #    earlier (bass + drums are the declared rhythm section and are
    #    exempt by design).
    fails_ant: list[str] = []
    for k in range(12):
        c0 = 288.0 + 8.0 * k
        cell = f"cell {k + 1} [{c0:.0f},{c0 + 8:.0f})"
        piano = [on for on, _o, _p, _v in _spans(sc, PIANO)
                 if c0 - 0.1 <= on < c0 + 8.0 - 0.1]
        if len(piano) < 3:
            fails_ant.append(f"{cell}: only {len(piano)} piano call notes")
        late = [on for on in piano if on >= c0 + 3.9]
        if late:
            fails_ant.append(f"{cell}: piano plays at {min(late):.2f}, "
                             f"inside the answer half")
        choir = sorted(on for ch in (AAH, OOH, EH)
                       for on, _o, _p, _v in _spans(sc, ch)
                       if c0 - 0.1 <= on < c0 + 8.0 - 0.1)
        early = [on for on in choir if on < c0 + 3.9]
        if early:
            fails_ant.append(f"{cell}: choir answers at {min(early):.2f}, "
                             f"before the call has finished")
        if not choir or choir[0] > c0 + 4.5:
            fails_ant.append(f"{cell}: no choir answer within 0.5 beats "
                             f"of beat 5")
        if len(choir) < 3:
            fails_ant.append(f"{cell}: only {len(choir)} choir answer "
                             f"notes (< 3)")

    # 2. tag_purity — the a-cappella tag is choir + claps/tambourine
    #    ONLY: every non-choir melodic channel is silent, the kit plays
    #    nothing but 39/54, and the choir actually sings.
    fails_tag: list[str] = []
    t0, t1 = _TAG_T0, _TAG_T0 + 32.0
    for ch in sorted(sc.events):
        if ch in (AAH, OOH, EH, DRUMS):
            continue
        bad = [on for on, _o, _p, _v in _spans(sc, ch)
               if t0 - 0.02 <= on < t1 - 0.02]
        if bad:
            fails_tag.append(f"ch{ch} plays at beat {min(bad):.2f} inside "
                             f"the a-cappella tag")
    bad_keys = {p for on, _o, p, _v in _spans(sc, DRUMS)
                if t0 - 0.02 <= on < t1 - 0.02} - {39, 54}
    if bad_keys:
        fails_tag.append(f"kit keys {sorted(bad_keys)} in the tag "
                         f"(claps 39 / tambourine 54 only)")
    sung = sum(1 for ch in (AAH, OOH, EH)
               for on, _o, _p, _v in _spans(sc, ch)
               if t0 - 0.02 <= on < t1)
    if sung < 24:
        fails_tag.append(f"only {sung} choir notes in the tag (< 24)")

    # 3. satb_choir — the three choir channels are true SATB layers:
    #    (a) the eh descant recurs EXACTLY in chorus1 and chorus2 and,
    #    re-rooted to D ionian, in the lift's four statements; (b) the
    #    registers stay ordered eh > aah > ooh in every chorus + tag;
    #    (c) the descant is rhythmically independent of the pad; (d) the
    #    ooh counter-line MOVES (>= 4 distinct pitches per chorus).
    fails_satb: list[str] = []
    c1 = _rel_set(sc, EH, 96.0, 160.0)
    c2 = _rel_set(sc, EH, 224.0, 288.0)
    if not c1 or c1 != c2:
        fails_satb.append(f"eh descant differs between chorus1 ({len(c1)} "
                          f"notes) and chorus2 ({len(c2)})")
    want_lift = {(round((16.0 * rep + start) * 4) / 4,
                  en.pitch(D4, _MAJ, deg))
                 for rep in range(4) for deg, start, _d in _HOOK}
    lift = _rel_set(sc, EH, 384.0, 448.0)
    if lift != want_lift:
        fails_satb.append("lift descant is not the hook re-rooted to "
                          "D ionian")
    for name, s0, s1 in (("chorus1", 96.0, 160.0), ("chorus2", 224.0, 288.0),
                         ("lift_chorus", 384.0, 464.0),
                         ("tag", 464.0, 496.0)):
        means = []
        for ch in (EH, AAH, OOH):
            ps = [p for on, _o, p, _v in _spans(sc, ch)
                  if s0 - 0.1 <= on < s1]
            means.append(sum(ps) / len(ps) if ps else 0.0)
        if not means[0] > means[1] > means[2]:
            fails_satb.append(f"'{name}': registers not ordered "
                              f"eh {means[0]:.1f} > aah {means[1]:.1f} "
                              f"> ooh {means[2]:.1f}")
    for name, s0, s1 in (("chorus1", 96.0, 160.0),
                         ("chorus2", 224.0, 288.0)):
        pad = [on for on, _o, _p, _v in _spans(sc, AAH)
               if s0 - 0.1 <= on < s1]
        free = [on for on, _o, _p, _v in _spans(sc, EH)
                if s0 - 0.1 <= on < s1
                and all(abs(on - q) > 0.3 for q in pad)]
        if len(free) < 24:
            fails_satb.append(f"'{name}': only {len(free)} eh onsets clear "
                              f"of the pad grid (< 24)")
        ooh_ps = {p for on, _o, p, _v in _spans(sc, OOH)
                  if s0 - 0.1 <= on < s1}
        if len(ooh_ps) < 4:
            fails_satb.append(f"'{name}': ooh counter has only "
                              f"{len(ooh_ps)} distinct pitches (< 4)")

    return [("antiphony", fails_ant),
            ("tag_purity", fails_tag),
            ("satb_choir", fails_satb)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds FROZEN at the phase-D album freeze (2026.07.11)
# (HLD 6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# FROZEN 2026.07.11 (phase-D album render): measured 4.13 dB (ferrosintesis
# 0.13.x per-track render); pinned with 2.1 dB slack, re-pinned at phase D.
_LIFT_DB = 2.0        # lift chorus over verse 1
# FROZEN 2026.07.11 (phase-D album render): measured 3.07x (band ratio
# 0.0563 -> 0.1729, per-track render); pinned 41% below the measurement,
# re-pinned at phase D.  The oo -> eh morph retunes the choir's F2 600 -> 1900 Hz and
# lifts the band-2/3 gains 0.35/0.10 -> 0.85/0.50 (engine.rs
# VOWEL_ANCHORS), so the 1.9 kHz / 450 Hz energy ratio must jump.
_VOWEL_RATIO = 1.8    # tag formant-band ratio, eh half over oo half
# FROZEN 2026.07.11 (phase-D album render): measured 2.13 dB; pinned with 1.1 dB slack.
_VOWEL_RMS_DB = 1.0   # the opening mouth also leans in


def _band_energy(l, r, i0: int, i1: int, f0: float, fs: float,
                 q: float = 1.0) -> float:
    """Mean-square energy of the mono sum through an RBJ bandpass
    biquad centred at f0 (constant-skirt, Q=1 — about 1.4 octaves)."""
    w0 = 2 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2 * q)
    a0 = 1 + alpha
    b0, b2 = alpha / a0, -alpha / a0
    a1, a2 = -2 * math.cos(w0) / a0, (1 - alpha) / a0
    x1 = x2 = y1 = y2 = 0.0
    acc = 0.0
    for j in range(i0, i1):
        x = (l[j] + r[j]) * 0.5
        y = b0 * x + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x
        y2, y1 = y1, y
        acc += y * y
    return acc / max(1, i1 - i0)


def audio_checks(ctx):
    # 1. Chorus lift: the D-major lift lands well above the first verse.
    fails_lift: list[str] = []
    v0, v1 = ctx.bar_window(40.0, 88.0)
    f0, f1 = ctx.bar_window(384.0, 448.0)
    verse = ctx.db(ctx.rms(ctx.l, ctx.r, v0, v1))
    final = ctx.db(ctx.rms(ctx.l, ctx.r, f0, f1))
    if final < verse + _LIFT_DB:
        fails_lift.append(f"lift chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # 2. The headline vowel morph: across the tag's midpoint the choir's
    #    formant balance must shift from oo to eh — the 1.9 kHz (eh F2)
    #    over 450 Hz (oo energy centre) band-energy ratio jumps, and the
    #    opening mouth gets louder.  Both halves share the same rhythm
    #    and percussion pattern; only CC70 moves.
    fails_vowel: list[str] = []
    a0, a1 = ctx.bar_window(465.0, 479.0)      # oo plateau
    b0, b1 = ctx.bar_window(485.0, 495.5)      # eh plateau
    rate = ctx.sample_rate
    oo = (_band_energy(ctx.l, ctx.r, a0, a1, 1900.0, rate)
          / max(1e-9, _band_energy(ctx.l, ctx.r, a0, a1, 450.0, rate)))
    eh = (_band_energy(ctx.l, ctx.r, b0, b1, 1900.0, rate)
          / max(1e-9, _band_energy(ctx.l, ctx.r, b0, b1, 450.0, rate)))
    if eh < oo * _VOWEL_RATIO:
        fails_vowel.append(f"tag vowel morph: eh-half band ratio {eh:.4f} "
                           f"not >= oo-half {oo:.4f} x {_VOWEL_RATIO}")
    h0 = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(464.0, 480.0)))
    h1 = ctx.db(ctx.rms(ctx.l, ctx.r, *ctx.bar_window(480.0, 496.0)))
    if h1 < h0 + _VOWEL_RMS_DB:
        fails_vowel.append(f"tag vowel morph: eh half {h1:.1f} dB not "
                           f">= oo half {h0:.1f} dB + {_VOWEL_RMS_DB}")

    return [("chorus_lift", fails_lift),
            ("tag_vowel_morph", fails_vowel)]
