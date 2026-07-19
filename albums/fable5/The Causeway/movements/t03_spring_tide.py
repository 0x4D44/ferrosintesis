"""movements/t03_spring_tide.py — track 3 of *The Causeway*.

SPRING TIDE.  The turn of the year — the shores close enough to CALL AND
ANSWER.  A minor warms toward C major (the same white-note collection: the
brightness is emphasis, never an accidental — so the leading tone G# never
sounds); the strait narrows to three semitones, and for the first time the
two themes come within touching distance, adjacent but still never
overlapping.  Four movements over a 3-against-4 quaver lattice:

  I. The Lattice   — a marimba cycles HOOK3 (the 3-quaver cell) against a
     kalimba on the 4-quaver grid; the two realign every twelve quavers — the
     reward beat.  A choir begins a verified vowel RISE (mm toward ah, sealed
     under 75); a steelpan colours the off-beats from a CC0 second-percussion
     bank; a muted guitar taps TURN in Morse; the tide breathes ~96.
  II. Answer       — a pan-flute breath heralds the spring groove: a Rhodes
     and brass punch THE MAINLAND THEME in C, and the ISLAND answers in A
     minor within two beats — call and answer, adjacent, never overlapping.
     A drawbar organ spins its Leslie up (slow to fast), the protagonist bass
     sings and states HOOK3, the Rhodes doubles its thumb through two
     choruses, and an authored accelerando quickens 96 -> 106.
  III. High Water  — the lattice returns under BOTH themes, alternating
     faster (the gaps tighten, the tension of near-touch), tempo locked toward
     108; a crystal shimmer autopans low across the field; the water collapses
     to a suspended iv-i.
  IV. Slack        — the kalimba alone over a held pad, a last modal cadence
     to A, and exactly three bell tolls on the island's A, nothing after them.

Every device the HLD marks verified is an oracle below, and all recurring
data is single-sourced from material.py (the two themes, HOOK3, the
convergence pcs, the morse word TURN, the tide-breath, the shore pans, the
rising vowel cap, the tolls, the cadence law).  The strait is three semitones.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 3
TITLE = "Spring Tide"
FILE = "03 - Spring Tide.mid"
SEED = 202607183
COMMENT = (
    "Spring Tide - the turn of the year, the shores close enough to call and "
    "answer.  A minor warms toward C major over a 3-against-4 quaver lattice: "
    "a marimba cycles the 3-quaver hook against a kalimba on the 4-grid, "
    "realigning every twelve quavers while a choir's vowels rise and a muted "
    "guitar taps TURN.  A breath flute heralds the spring groove, where a "
    "Rhodes and brass punch the mainland theme in C and the island answers in "
    "A minor within two beats - adjacent, never overlapping - over a "
    "Leslie-spinning organ, a singing protagonist bass and a doubled thumb, "
    "an accelerando quickening 96 to 106; then high water, the lattice back "
    "under both themes alternating faster beneath a crystal shimmer; and "
    "slack water, a kalimba alone over a held pad, three bells tolling the "
    "island's A.")

# ---------------------------------------------------------------------------
# Channels.  Island pole (the ice / Enigma weather - marimba, kalimba, choir,
# steelpan, vibes, pan flute, pad) sits left at SHORE_PANS[3][0]=50; the
# mainland pole (the McCartney band - Rhodes, organ, brass) sits right at 78;
# the neutral spine (bass, drums, the morse guitar, bells) holds 64.  The
# crystal shimmer is the album's one autopan channel - neither centered nor a
# fixed shore seat.  The strait is a whole tone narrower than track 2's.
# ---------------------------------------------------------------------------

CH_MARIMBA, CH_KALIMBA, CH_CHOIR, CH_STEELPAN = 0, 1, 2, 3
CH_BASS, CH_RHODES, CH_ORGAN, CH_BRASS = 4, 5, 6, 7
CH_VIBES, CH_DRUMS, CH_PANFLUTE, CH_MUTEGTR = 8, 9, 10, 11
CH_PAD, CH_CRYSTAL, CH_BELLS = 12, 13, 14

_MM = material.MODE_MINOR                  # aeolian - the island's mode
_MJ = material.MODE_MAJOR                   # ionian - the mainland's spring

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]       # (50, 78)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 9, 0

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 120.0
HERALD_T0, HERALD_T1 = 120.0, 128.0        # >= 2 bars, pan flute alone
GROOVE_T0 = 128.0                          # the spring groove locks in
II_END = 288.0
III_END = 400.0
END = 496.0

# --- the accelerando (the spring quickening of movement II) ---
ACCEL_T0, ACCEL_T1 = 120.0, 280.0
ACCEL_BPM0, ACCEL_BPM1 = 96.0, 106.0

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE = en.n("A4")                   # 69 - the island tonic A (deg 1)
MAINLAND_BASE = en.n("C4")                 # 60 - the mainland tonic C (deg 1)
BASS_HOOK_ROOT = en.n("A1")                # 33 - HOOK3 in the protagonist bass

# call-and-answer statement schedule (mainland calls in C, island answers in
# A minor within <= 2 beats; III alternates faster - the gaps tighten).
MAINLAND_CALLS = [184.0, 300.0, 340.0]     # brass, base C
ISLAND_ANSWERS = [193.0, 309.0, 348.5]     # vibes, base A - answers within 2

# the 3-against-4 lattice grids (in beats): the marimba cell every 3 quavers
# (1.5 beats), the kalimba every 4 quavers (2.0 beats); they realign every 12
# quavers (6.0 beats) - the reward beat.
MARIMBA_GRID = 1.5
KALIMBA_GRID = 2.0
REWARD_GRID = 6.0
LATTICE_SPANS = [(0.0, I_END), (III_END - 112.0, 396.0)]   # I and III lattice

CHORUS_SPANS = [(136.0, 180.0), (204.0, 256.0)]   # the two spring choruses
CAD_WINDOWS = [(176.0, 180.0, 180.0),      # chorus 1 -> i  (v-i, E->A)
               (252.0, 256.0, 256.0),      # chorus 2 -> i  (iv-i, D->A)
               (392.0, 396.0, 396.0),      # III collapse (suspended iv-i)
               (436.0, 440.0, 440.0)]      # IV slack resettle (v-i)

MORSE_T0 = 32.0
MORSE_PITCH = en.n("A4")                    # 69 - the muted guitar's fixed tap
TOLL_T0 = 480.0
TOLL_PITCH = en.n("A3")                     # 57 - pc 9 = the island tonic A

# --- the tide-breath tempo map: I / III / IV breathe, II accelerates ---


def _accel(t0: float, t1: float, bpm0: float, bpm1: float,
           step: float = 8.0) -> list[tuple[float, float]]:
    """A monotonically rising tempo ramp - the authored spring accelerando
    that is movement II's swell (the tide owns I, III and IV instead)."""
    out = []
    b = t0
    while b <= t1 + 1e-9:
        out.append((b, round(en.lerp(bpm0, bpm1, (b - t0) / (t1 - t0)), 2)))
        b += step
    return out


TEMPO_MAP = (
    material.tide_breath(96.0, 0.0, I_END, period=32.0, depth=4.0)
    + _accel(ACCEL_T0, ACCEL_T1, ACCEL_BPM0, ACCEL_BPM1)
    + material.tide_breath(108.0, II_END, III_END, period=32.0, depth=3.0)
    + material.tide_breath(92.0, III_END, END, period=32.0, depth=5.0))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. The Lattice", 0.0, I_END),
               ("II. Answer", I_END, II_END),
               ("III. High Water", II_END, III_END),
               ("IV. Slack", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1),                   # A minor: no sharps, minor
             (GROOVE_T0, 0, 0),             # C major: the spring turn
             (III_END, 0, 1)],              # A minor again for the slack
    channels=[(CH_MARIMBA, "marimba", 12, 88, ISL_PAN, 42),
              (CH_KALIMBA, "kalimba", 108, 84, ISL_PAN, 46),
              (CH_CHOIR, "choir", 52, 70, ISL_PAN, 60),
              (CH_STEELPAN, "steelpan", 114, 80, ISL_PAN, 40),
              (CH_BASS, "protagonist bass", 33, 100, 64, 22),
              (CH_RHODES, "rhodes", 4, 86, MAIN_PAN, 34),
              (CH_ORGAN, "drawbar organ", 16, 84, MAIN_PAN, 36),
              (CH_BRASS, "brass section", 61, 90, MAIN_PAN, 40),
              (CH_VIBES, "vibraphone", 11, 82, ISL_PAN, 48),
              (CH_DRUMS, "kit", 0, 92, 64, 26),
              (CH_PANFLUTE, "pan flute", 75, 84, ISL_PAN, 52),
              (CH_MUTEGTR, "muted guitar", 28, 80, 64, 30),
              (CH_PAD, "warm pad", 89, 68, ISL_PAN, 58),
              (CH_CRYSTAL, "crystal", 98, 48, 64, 60),
              (CH_BELLS, "tubular bells", 14, 90, 64, 50)],
    extra_markers=[(HERALD_T0, "breath herald"),
                   (GROOVE_T0, "the spring groove"),
                   (MAINLAND_CALLS[0], "call and answer"),
                   (II_END, "high water"),
                   (TOLL_T0, "the tolls")],
    bank_selects=[(CH_STEELPAN, 112)],      # steelpan CC0 second-perc bank
)

PROGRAM_WHITELIST = {4, 11, 12, 14, 16, 28, 33, 52, 61, 75, 89, 98, 108, 114}
CENTERED_CHANNELS = {CH_BASS, CH_DRUMS, CH_MUTEGTR, CH_BELLS}
NOTE_RANGES = {
    CH_MARIMBA: (67, 79), CH_KALIMBA: (57, 86), CH_CHOIR: (55, 84),
    CH_STEELPAN: (55, 84), CH_BASS: (28, 53), CH_RHODES: (40, 84),
    CH_ORGAN: (43, 84), CH_BRASS: (48, 84), CH_VIBES: (60, 84),
    CH_PANFLUTE: (67, 79), CH_MUTEGTR: (69, 69), CH_PAD: (33, 76),
    CH_CRYSTAL: (72, 96), CH_BELLS: (52, 64),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # no pitch bends: CC only
DURATION_WINDOW = (292.0, 309.0)            # ~5:00 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES sec.3 pattern; beat-based, tick where noted)
# ---------------------------------------------------------------------------

_PPQ = en.PPQ
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))


def _note_ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = d[0] & 0xF0
        if s == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                out.append((q.pop(0) / _PPQ, tick / _PPQ, d[1]))
    return sorted(out)


def _cc_lane(sc, ch, num):
    return sorted((t / _PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _onsets_in(sc, ch, lo, hi):
    return [(b, p, v) for b, p, v in _note_ons(sc, ch) if lo - 1e-6 <= b < hi]


def _movement_events(lo, hi):
    """The tempo events whose beat falls inside [lo, hi)."""
    return [(b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6]


def _in_span(beat, spans=CHORUS_SPANS):
    return any(lo <= beat < hi for lo, hi in spans)


def _on_grid(beat, grid):
    return abs((beat / grid) - round(beat / grid)) < 0.02


# ---------------------------------------------------------------------------
# Harmony — A aeolian (the island) and C ionian (the mainland spring) share
# one white-note collection, so no line ever needs the leading tone G#: the
# brightness is emphasis (major triads on C/F/G), never an accidental.
# ---------------------------------------------------------------------------

# The lattice pad cycle (A aeolian): i - bIII - bVII - iv, open voicings.
LATTICE_PAD = [
    [en.n("A2"), en.n("E3"), en.n("A3")],     # Am  (i)
    [en.n("C3"), en.n("G3"), en.n("C4")],     # C   (bIII)
    [en.n("G2"), en.n("D3"), en.n("G3")],     # G   (bVII)
    [en.n("F2"), en.n("C3"), en.n("F3")],     # F   (bVI)
]
# The choir tops for the lattice (the fifth of each chord), rising with vowel.
LATTICE_CHOIR = [en.n("E4"), en.n("G4"), en.n("D4"), en.n("C4")]

# The spring groove pad cycle (C ionian): I - IV - V - vi, bright triads.
SPRING_PAD = [
    [en.n("C3"), en.n("G3"), en.n("E4")],     # C   (I)
    [en.n("F3"), en.n("C4"), en.n("A4")],     # F   (IV)
    [en.n("G3"), en.n("D4"), en.n("B4")],     # G   (V)
    [en.n("A2"), en.n("E3"), en.n("A3")],     # Am  (vi)
]
SPRING_CHOIR = [en.n("G4"), en.n("A4"), en.n("B4"), en.n("A4")]

# The high-water pad (A aeolian again, thinned to fifths under the lattice).
HIGH_PAD = [
    [en.n("A2"), en.n("E3"), en.n("A3")],     # Am
    [en.n("F2"), en.n("C3"), en.n("F3")],     # F
    [en.n("G2"), en.n("D3"), en.n("G3")],     # G
    [en.n("E3"), en.n("A3"), en.n("C4")],     # Am/E -> the suspension
]
HIGH_CHOIR = [en.n("E4"), en.n("C4"), en.n("D4"), en.n("E4")]

# The slack pad (a held A-minor bed for the kalimba to fall over).
SLACK_PAD = [
    [en.n("A2"), en.n("E3"), en.n("A3"), en.n("C4")],   # Am
    [en.n("F2"), en.n("C3"), en.n("A3"), en.n("C4")],   # F
]

# The kalimba's 4-grid answer (descending A-minor pentatonic colour).
KALIMBA_CYCLE = [en.n("A5"), en.n("E5"), en.n("C5"), en.n("G4"),
                 en.n("A5"), en.n("D5"), en.n("C5"), en.n("E5")]
# The kalimba's slack solo (a slow descending fall over the held pad).
KALIMBA_SLACK = [en.n("A5"), en.n("G5"), en.n("E5"), en.n("D5"),
                 en.n("C5"), en.n("A4"), en.n("E4"), en.n("A4")]

# The protagonist bass's low register: A aeolian, spanning >= 19 semitones.
BASS_SCALE = [en.n(x) for x in
              ("E1", "G1", "A1", "B1", "C2", "D2", "E2", "F2", "G2",
               "A2", "B2", "C3", "D3", "E3")]

# Brass stab voicings (C ionian): the answering horn-section punch.
BRASS_STABS = [
    [en.n("C4"), en.n("E4"), en.n("G4")],                # C
    [en.n("F4"), en.n("A4"), en.n("C5")],                # F
    [en.n("G3"), en.n("B3"), en.n("D4")],                # G
    [en.n("A3"), en.n("C4"), en.n("E4")],                # Am
]

# Steelpan colour cells (A minor, the off-beat sparkle of the lattice).
STEELPAN_CELL = [en.n("A4"), en.n("C5"), en.n("E5"), en.n("D5")]


# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (the lattice hook, the two themes, morse,
# tolls, the herald and the doubled thumb) are jt=0 so every statement is
# findable and every grid onset lands true; texture lanes take a light jitter.
# ---------------------------------------------------------------------------

def _pad_cycle(sc, ch, t0, t1, cycle, span, vel, curve, vowel=None):
    """Sustained voicings stepping through `cycle`, one chord every `span`
    beats from t0 to t1, ending exactly at t1 so no chord rings past the
    movement.  `curve` is a (beat, cc11) breakpoint list."""
    b = t0
    i = 0
    while b < t1 - 1e-6:
        dur = min(span, t1 - b)
        for p in cycle[i % len(cycle)]:
            sc.note(ch, p, b, dur, vel, jt=0, jv=2)
        b += span
        i += 1
    en.expr_curve(sc, ch, curve, step=4.0)
    if vowel is not None:
        en.vowel_curve(sc, ch, vowel, step=4.0)


# -- I. The Lattice ---------------------------------------------------------

def _lattice_marimba(sc, t0, t1):
    """The 3-quaver cell: HOOK3 cycled every 1.5 beats (three quavers), the
    reward beats (every 12 quavers) accented - the marimba on the 3-grid."""
    t = t0
    while t < t1 - 1e-6:
        reward = _on_grid(t, REWARD_GRID)
        material.play_hook(sc, CH_MARIMBA, t, ISLAND_BASE, NUMBER,
                           vel=86 if reward else 72, gate=0.9)
        t += MARIMBA_GRID


def _lattice_kalimba(sc, t0, t1):
    """The 4-grid answer: one kalimba pluck every 2.0 beats (four quavers),
    accented on the reward beats where it meets the marimba's cell head."""
    i = 0
    t = t0
    while t < t1 - 1e-6:
        reward = _on_grid(t, REWARD_GRID)
        p = KALIMBA_CYCLE[i % len(KALIMBA_CYCLE)]
        sc.note(CH_KALIMBA, p, t, 1.5, 68 + (12 if reward else 0),
                jt=0, jv=3)
        t += KALIMBA_GRID
        i += 1


def _choir_weather(sc, t0, t1, tops, span, v0, v1, vowel0, vowel1):
    """A sealed choir bed: one held top per chord under a rising vowel morph
    and a slow swell.  Ends exactly at t1 so it clears the herald window."""
    b = t0
    i = 0
    while b < t1 - 1e-6:
        dur = min(span, t1 - b)
        sc.note(CH_CHOIR, tops[i % len(tops)], b, dur * 0.98, 46, jt=1, jv=2)
        b += span
        i += 1
    en.expr_curve(sc, CH_CHOIR, [(t0, v0), ((t0 + t1) / 2, v1), (t1 - 1, v0)],
                  step=4.0)
    en.vowel_curve(sc, CH_CHOIR, [(t0, vowel0), (t1 - 1, vowel1)], step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, [(t0, 4), (t1 - 1, 24)], step=8.0)


def _steelpan_colour(sc, t0, t1):
    """Steelpan sparkle from the CC0 second-percussion bank: an off-beat
    figure every bar, colouring the lattice (island, never a statement)."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        for k, off in enumerate((0.5, 1.5, 2.5, 3.5)):
            p = STEELPAN_CELL[(ci + k) % len(STEELPAN_CELL)]
            sc.note(CH_STEELPAN, p, bar + off, 0.45, 54 + (k % 2) * 6,
                    jt=2, jv=4)
        bar += 4.0
        ci += 1


def _b_lattice(sc):
    """I. The Lattice [0, 120) - the marimba's 3-quaver cell against the
    kalimba's 4-grid, a rising sealed choir, steelpan colour, and the muted
    guitar tapping TURN in Morse.  Everything ends by 120 so the pan-flute
    herald that opens II sounds alone."""
    _lattice_marimba(sc, 0.0, I_END)
    _lattice_kalimba(sc, 0.0, I_END)
    _pad_cycle(sc, CH_PAD, 0.0, I_END, LATTICE_PAD, 8.0, 40,
               [(0.0, 32), (60.0, 52), (I_END - 1, 40)])
    _choir_weather(sc, 0.0, I_END, LATTICE_CHOIR, 8.0, 40, 60, 8, 30)
    _steelpan_colour(sc, 0.0, I_END)
    # the muted guitar taps TURN (MORSE_PROGRAMS[3] = 28) in standard timing.
    material.play_morse(sc, CH_MUTEGTR, MORSE_T0, NUMBER, MORSE_PITCH)


# -- II. Answer: the herald, then the spring groove ------------------------

def _herald(sc):
    """Enigma's inhale: HOOK3's three notes (deltas 0, 3, 7) on the pan flute,
    alone, over a strictly rising CC11 swell - two bars.  The notes are laid
    contiguous so the whole window is the flute's."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]      # [0, 3, 7]
    starts = [HERALD_T0, HERALD_T0 + 2.0, HERALD_T0 + 4.0]
    durs = [2.0, 2.0, 4.0]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, ISLAND_BASE + s, st, du, 56, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 16), (HERALD_T1, 104)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 28)],
                step=0.5)


def _bar_vel(beat, base, accent=10):
    q = beat % 4.0
    if abs(q) < 1e-6:
        return base + accent
    if abs(q - 2.0) < 1e-6:
        return base + accent // 2
    return base


def _walk(sc, ch, t0, start_idx, deltas, dur, vel_base):
    """Step a bass melody through BASS_SCALE by mostly +-1 scale steps so it
    stays stepwise; returns the end beat and final scale index."""
    idx = start_idx
    beat = t0
    for d in deltas:
        idx = max(0, min(len(BASS_SCALE) - 1, idx + d))
        sc.note(ch, BASS_SCALE[idx], beat, dur * 0.9,
                _bar_vel(beat, vel_base), jt=0, jv=3)
        beat += dur
    return beat, idx


def _bass_cadence(sc, down, approach_pitch):
    """A modal approach into a tonic-A landing on the downbeat - the withheld
    cadence, the leading tone G# nowhere near it (all white notes)."""
    sc.note(CH_BASS, approach_pitch, down - 2.0, 1.0, 82, jt=0, jv=3)
    sc.note(CH_BASS, approach_pitch, down - 1.0, 1.0, 80, jt=0, jv=3)
    sc.note(CH_BASS, en.n("A2"), down, 2.0, 90, jt=0, jv=3)


# stepwise chorus walks (all +-1 scale steps -> 100% stepwise; visiting both
# extremes of BASS_SCALE so the protagonist range clears 19 semitones).
_WALK1 = [1] * 11 + [-1] * 13 + [1] * 13 + [-1]           # 138 -> ~176
_WALK2 = [1] * 11 + [-1] * 13 + [1] * 13 + [-1] * 9       # 206 -> ~252


def _emit_bass_II(sc):
    """The protagonist bass: a HOOK3 head then a stepwise-singing McCartney
    walk through each chorus, a modal cadence closing each, sparse roots in
    the interlude and outro.  Emitted before the doubled thumb reads it."""
    # intro vamp [128, 136) - not a chorus
    for b in (128.0, 130.0, 132.0, 134.0):
        sc.note(CH_BASS, BASS_SCALE[2], b, 1.8, 74, jt=0, jv=3)     # A1
    # chorus 1 [136, 180): HOOK3 head then the walk, cadence v-i (E->A)
    material.play_hook(sc, CH_BASS, 136.0, BASS_HOOK_ROOT, NUMBER,
                       vel=88, gate=0.9)
    _walk(sc, CH_BASS, 138.0, 2, _WALK1, 1.0, 82)
    _bass_cadence(sc, 180.0, en.n("E2"))                            # v -> A
    # interlude [180, 204): sparse roots under the call and answer
    for b, idx in ((184.0, 2), (188.0, 4), (192.0, 6), (196.0, 4),
                   (200.0, 2)):
        sc.note(CH_BASS, BASS_SCALE[idx], b, 1.6, 66, jt=0, jv=3)
    # chorus 2 [204, 256): HOOK3 head then the walk, cadence iv-i (D->A)
    material.play_hook(sc, CH_BASS, 204.0, BASS_HOOK_ROOT, NUMBER,
                       vel=90, gate=0.9)
    _walk(sc, CH_BASS, 206.0, 2, _WALK2, 1.0, 82)
    _bass_cadence(sc, 256.0, en.n("D2"))                            # iv -> A
    # outro [256, 288): the groove recedes, the bass sinking home
    for k, idx in enumerate((6, 5, 4, 3, 2, 4, 2, 0)):
        sc.note(CH_BASS, BASS_SCALE[idx], 258.0 + k * 3.5, 3.0,
                62 - (k % 2) * 6, jt=0, jv=3)


def _double_thumb(sc):
    """The chorus thickens: every bass note-on inside the choruses shadowed at
    the octave on the Rhodes (the doubled thumb), and nowhere else."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if _in_span(beat):
            sc.note(CH_RHODES, pitch + 12, beat, 0.9, 70, jt=0, jv=2)


def _rhodes_comp(sc, t0, t1):
    """Sparse high Rhodes comping outside the choruses - a disjoint register
    (>= G4) from the doubled thumb's octaves, so the thickening reads as a
    chorus event and never leaks outside."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        top = [p + 12 for p in SPRING_PAD[ci % len(SPRING_PAD)] if p + 12 >= 67]
        for off in (0.0, 2.0):
            for p in top:
                sc.note(CH_RHODES, p, bar + off, 1.6, 56, jt=0, jv=3)
        bar += 4.0
        ci += 1


def _organ_bed(sc, t0, t1):
    """The drawbar organ's spring chord bed (C ionian) with its Leslie
    choreography - the rotor spinning up into each chorus (slow -> fast)."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        for p in SPRING_PAD[ci % len(SPRING_PAD)]:
            sc.note(CH_ORGAN, p, bar, 3.8, 56, jt=0, jv=2)
        bar += 4.0
        ci += 1
    en.expr_curve(sc, CH_ORGAN,
                  [(t0, 44), ((t0 + t1) / 2, 66), (t1 - 1, 48)], step=4.0)


def _leslie_spinups(sc):
    """Two Leslie spin-ups on the organ: a slow chorale ramping to a fast
    tremolo into each chorus, then easing back (CC1, an oracle)."""
    en.leslie(sc, CH_ORGAN, 130.0, 138.0, 8, 104)     # spin-up into chorus 1
    en.leslie(sc, CH_ORGAN, 176.0, 184.0, 104, 16)    # ease back
    en.leslie(sc, CH_ORGAN, 200.0, 208.0, 10, 110)    # spin-up into chorus 2
    en.leslie(sc, CH_ORGAN, 252.0, 260.0, 110, 20)    # ease back


def _spring_drums(sc, t0, t1):
    """The full kit: a bright, driving spring backbeat - kick on 1 and the
    and-of-3, snares on 2 and 4, an open hat opening each beat's quavers."""
    bar = t0
    while bar < t1 - 1e-6:
        sc.hit(36, bar, 92, jt=0)                      # kick on 1
        sc.hit(36, bar + 2.5, 78, jt=0)                # the push
        sc.hit(38, bar + 1.0, 84, jt=0)                # snare on 2
        sc.hit(38, bar + 3.0, 88, jt=0)                # snare on 4
        for q in range(8):
            drum = 46 if q % 4 == 0 else 42
            sc.hit(drum, bar + q * 0.5, 42 + (10 if drum == 46 else 0), jt=0)
        bar += 4.0


def _mainland_call(sc, t0, vel=82):
    """THE MAINLAND THEME in C on the brass, clean and monophonic - a spring
    call across the strait, distance three."""
    material.play_mainland(sc, CH_BRASS, t0, MAINLAND_BASE, vel=vel,
                           vel_end=vel - 8)
    end = t0 + material.MAINLAND_LEN
    en.expr_curve(sc, CH_BRASS,
                  [(t0, 40), (t0 + 4, 92), (t0 + 6, 60), (end, 42)], step=0.5)


def _island_answer(sc, t0, vel=76):
    """THE ISLAND THEME in A minor on the vibraphone - the near shore
    answering within two beats, still hanging on degree 2."""
    material.play_island(sc, CH_VIBES, t0, ISLAND_BASE, vel=vel,
                         vel_end=vel - 8)
    end = t0 + material.ISLAND_LEN
    en.expr_curve(sc, CH_VIBES,
                  [(t0, 38), (t0 + 4, 84), (end, 36)], step=0.5)
    en.echo_throw(sc, CH_VIBES, end - 0.5)


def _b_answer(sc):
    """II. Answer [120, 288) - the pan-flute herald, then the spring groove:
    the mainland calls in C and the island answers in A minor within two
    beats, over a Leslie-spinning organ, the driving kit, the singing bass
    doubled through two choruses, and a bright Rhodes comp between them."""
    _herald(sc)
    _pad_cycle(sc, CH_PAD, GROOVE_T0, II_END, SPRING_PAD, 8.0, 42,
               [(GROOVE_T0, 40), (208.0, 60), (II_END - 1, 46)])
    en.cc_curve(sc, CH_PAD, 1, [(GROOVE_T0, 0), (II_END - 1, 26)], step=8.0)
    _choir_weather(sc, GROOVE_T0, II_END, SPRING_CHOIR, 8.0, 42, 62, 30, 55)
    _organ_bed(sc, GROOVE_T0, II_END)
    _leslie_spinups(sc)
    _spring_drums(sc, GROOVE_T0, II_END)
    _emit_bass_II(sc)
    _double_thumb(sc)
    _rhodes_comp(sc, GROOVE_T0, 136.0)
    _rhodes_comp(sc, 180.0, 204.0)
    _rhodes_comp(sc, 256.0, II_END)
    # the one call-and-answer of the movement: mainland calls, island answers.
    _mainland_call(sc, MAINLAND_CALLS[0])
    _island_answer(sc, ISLAND_ANSWERS[0])


# -- III. High Water: the lattice back under both themes --------------------

def _crystal_shimmer(sc, t0, t1):
    """The album's one autopan channel: a crystal shimmer sweeping the field,
    kept LOW (velocity + channel volume) so the mono-collapse never bites."""
    en.autopan(sc, CH_CRYSTAL, t0, t1 - t0, lo=34, hi=94,
               period_beats=12.0, step=0.5)
    seq = [en.n("E5"), en.n("A5"), en.n("C6"), en.n("B5"), en.n("E6")]
    b = t0
    i = 0
    while b < t1 - 1e-6:
        sc.note(CH_CRYSTAL, seq[i % len(seq)], b, 1.8, 40, jt=3, jv=4)
        b += 3.0
        i += 1


def _emit_bass_III(sc):
    """A slow stepwise bass under the high-water lattice, then the collapse:
    a suspended iv-i, the bass D falling to A."""
    _walk(sc, CH_BASS, 292.0, 7,
          [-1, 1, -1, -1, 1, 1, -1, -1, -1, 1, 1, -1, 1, -1, -1, 1, -1, -1,
           1, 1, -1, -1, -1, 1], 4.0, 66)
    _bass_cadence(sc, 396.0, en.n("D2"))                            # iv -> A


def _b_high_water(sc):
    """III. High Water [288, 400) - the marimba/kalimba lattice returns under
    BOTH themes alternating faster (the gaps tighten, still never overlapping)
    beneath a low crystal shimmer, and the water collapses to a suspended
    iv-i."""
    _lattice_marimba(sc, II_END, 392.0)
    _lattice_kalimba(sc, II_END, 392.0)
    _pad_cycle(sc, CH_PAD, II_END, III_END, HIGH_PAD, 8.0, 40,
               [(II_END, 44), (340.0, 58), (III_END - 1, 34)])
    _choir_weather(sc, II_END, 396.0, HIGH_CHOIR, 8.0, 40, 58, 55, 72)
    _crystal_shimmer(sc, II_END, 392.0)
    _emit_bass_III(sc)
    _mainland_call(sc, MAINLAND_CALLS[1], vel=84)
    _island_answer(sc, ISLAND_ANSWERS[1], vel=78)
    _mainland_call(sc, MAINLAND_CALLS[2], vel=86)
    _island_answer(sc, ISLAND_ANSWERS[2], vel=80)


# -- IV. Slack: the kalimba alone, a modal cadence, three tolls -------------

def _kalimba_slack(sc, t0, t1):
    """The kalimba alone over the held pad - a slow descending fall, free of
    the lattice grid (the water has gone slack)."""
    seq = KALIMBA_SLACK
    b = t0
    i = 0
    while b < t1 - 1e-6:
        sc.note(CH_KALIMBA, seq[i % len(seq)], b, 1.8,
                58 - (i % 3) * 4, jt=2, jv=3)
        b += 2.0
        i += 1


def _b_slack(sc):
    """IV. Slack [400, 496) - the kalimba alone over a held A-minor pad, a
    last modal cadence to A, then exactly three bells tolling the island's A,
    and nothing after the first of them."""
    _pad_cycle(sc, CH_PAD, III_END, TOLL_T0, SLACK_PAD, 16.0, 38,
               [(III_END, 42), (440.0, 48), (TOLL_T0 - 1, 26)])
    _kalimba_slack(sc, 402.0, 476.0)
    _bass_cadence(sc, 440.0, en.n("E2"))                            # v -> A
    # the bell buoy: exactly three tolls on the island's A, the final note-ons.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, vel=82, dur=3.5)


BUILDERS = [_b_lattice, _b_answer, _b_high_water, _b_slack]


# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """The island states three times (tonic A, pc 9); the mainland three times
    (tonic C, pc 0) — distance 3, the strait a whole tone narrower than T2."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 3:
        fails.append(f"{len(isl)} island statements, want 3 (II + III x2)")
    for ch, start, _end, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {ISLAND_TONIC_PC} (A)")
    if len(mnl) != 3:
        fails.append(f"{len(mnl)} mainland statements, want 3 (II + III x2)")
    for ch, start, _end, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {MAINLAND_TONIC_PC} (C)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 3:
            fails.append(f"shore distance {dist}, want 3")
    return fails


def _o_call_answer(sc):
    """The escalation: the two themes never overlap, and every mainland call
    is answered by an island statement within two beats (adjacent, disjoint)."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    for a, b in material.overlapping_pairs(isl, mnl):
        fails.append(f"island {a[1]:.1f}-{a[2]:.1f} overlaps mainland "
                     f"{b[1]:.1f}-{b[2]:.1f} (T3 forbids simultaneity)")
    for m in mnl:
        gaps = []
        for i in isl:
            if i[1] >= m[2] - 1e-6:            # island answers after the call
                gaps.append(i[1] - m[2])
            elif m[1] >= i[2] - 1e-6:          # island called before
                gaps.append(m[1] - i[2])
        if not gaps or min(gaps) > 2.0 + 1e-6:
            near = f"{min(gaps):.2f}" if gaps else "none"
            fails.append(f"mainland at {m[1]:.1f} has no island answer within "
                         f"2 beats (nearest gap {near})")
    return fails


def _o_end_degrees(sc):
    """End-degree discipline: no theme-family line ends on its local tonic,
    and the fusion phrase (T5's alone) never sounds here."""
    fails = []
    if material.theme_statements(sc, "fusion"):
        fails.append("the FUSION phrase must not sound on tracks 1-4")
    isl_end = en.deg_semis(_MM, material.ISLAND_END_DEG) - \
        en.deg_semis(_MM, material.ISLAND_FIRST_DEG)
    for ch, start, _end, first in material.theme_statements(sc, "island"):
        if (first + isl_end) % 12 == material.island_tonic_pc(first):
            fails.append(f"island at {start:.1f} ends on the tonic")
    return fails


def _o_hook_density(sc):
    """The lattice earworm: HOOK3 stated >= 6 times across the track."""
    hits = 0
    for ch in sc.events:
        hits += len(material.find_statements(material.note_ons(sc, ch),
                                             material.HOOKS[NUMBER]))
    if hits < 6:
        return [f"HOOK3 found {hits} times, want >= 6"]
    return []


def _o_lattice(sc):
    """The 3-against-4 lattice: the marimba cycles HOOK3 on the 3-quaver grid,
    the kalimba answers on the 4-quaver grid, and the two coincide on every
    reward beat (twelve quavers)."""
    fails = []
    mar = material.find_statements(material.note_ons(sc, CH_MARIMBA),
                                   material.HOOKS[NUMBER])
    if len(mar) < 20:
        fails.append(f"marimba states HOOK3 {len(mar)} times, want the "
                     f"cycling lattice (>= 20)")
    off = [s for s, _p, _st in mar if not _on_grid(s, MARIMBA_GRID)]
    if off:
        fails.append(f"marimba cell at {off[0]:.2f} off the 3-quaver grid")
    kal = [(b, p, v) for b, p, v in _note_ons(sc, CH_KALIMBA)
           if _in_span(b, LATTICE_SPANS)]
    if len(kal) < 20:
        fails.append(f"kalimba plays {len(kal)} lattice onsets, want the "
                     f"4-grid answer")
    stray = [b for b, _p, _v in kal if not _on_grid(b, KALIMBA_GRID)]
    if stray:
        fails.append(f"kalimba onset at {stray[0]:.2f} off the 4-quaver grid")
    mar_ons = {round(b, 3) for b, _p, _v in _note_ons(sc, CH_MARIMBA)}
    kal_ons = {round(b, 3) for b, _p, _v in _note_ons(sc, CH_KALIMBA)}
    rewards = [i * REWARD_GRID for i in range(1, int(END // REWARD_GRID))
               if _in_span(i * REWARD_GRID, LATTICE_SPANS)]
    missed = [r for r in rewards
              if not (any(abs(m - r) < 0.05 for m in mar_ons)
                      and any(abs(k - r) < 0.05 for k in kal_ons))]
    if missed:
        fails.append(f"reward beat {missed[0]:.1f} lacks a marimba+kalimba "
                     f"coincidence")
    return fails


def _o_protagonist_bass(sc):
    """The McCartney bass sings: stepwise-dominant, wide-ranging, and stating
    HOOK3 in the bass inside each spring chorus."""
    fails = []
    ons = _note_ons(sc, CH_BASS)
    pitches = [p for _b, p, _v in ons]
    if len(pitches) < 2:
        return ["protagonist bass is silent"]
    steps = sum(1 for a, b in zip(pitches, pitches[1:]) if 1 <= abs(b - a) <= 2)
    ratio = steps / (len(pitches) - 1)
    if ratio < 0.50:
        fails.append(f"bass stepwise ratio {ratio:.2f} < 0.50")
    span = max(pitches) - min(pitches)
    if span < 19:
        fails.append(f"bass range {span} semitones < 19")
    bass_hooks = material.find_statements(material.note_ons(sc, CH_BASS),
                                          material.HOOKS[NUMBER])
    in_chorus = [h for h in bass_hooks if _in_span(h[0])]
    if len(in_chorus) < 2:
        fails.append(f"HOOK3 stated {len(in_chorus)} times in the bass inside "
                     f"the choruses, want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The chorus thickens: every bass note-on shadowed at the octave on the
    Rhodes inside the choruses (coverage >= 0.80), and not outside (< 0.30)."""
    fails = []
    rhodes = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_RHODES)]

    def shadowed(btick, bp):
        return any(pp == bp + 12 and abs(pt - btick) <= 10 for pt, pp in rhodes)

    inside, outside = [], []
    for b, p, _v in _note_ons(sc, CH_BASS):
        (inside if _in_span(b) else outside).append((_tick(b), p))
    cov_in = (sum(1 for bt, bp in inside if shadowed(bt, bp)) / len(inside)
              if inside else 0.0)
    cov_out = (sum(1 for bt, bp in outside if shadowed(bt, bp)) / len(outside)
               if outside else 0.0)
    if cov_in < 0.80:
        fails.append(f"doubled-thumb coverage {cov_in:.2f} inside choruses "
                     f"< 0.80")
    if cov_out >= 0.30:
        fails.append(f"bass doubled {cov_out:.2f} OUTSIDE choruses >= 0.30")
    return fails


def _o_herald(sc):
    """The breath herald: >= 2 bars where only the pan flute sounds, playing
    HOOK3's three notes over a strictly-rising CC11 swell."""
    fails = []
    for ch in sorted(sc.events):
        if ch == CH_PANFLUTE:
            continue
        if _onsets_in(sc, ch, HERALD_T0, HERALD_T1):
            fails.append(f"ch{ch} sounds inside the herald window "
                         f"[{HERALD_T0:.0f},{HERALD_T1:.0f}) - only the pan "
                         f"flute may")
            break
    pf = _onsets_in(sc, CH_PANFLUTE, HERALD_T0, HERALD_T1)
    want = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]
    if len(pf) != 3:
        fails.append(f"herald has {len(pf)} pan-flute notes, want 3")
    else:
        deltas = [pf[k][1] - pf[0][1] for k in range(3)]
        if deltas != want:
            fails.append(f"herald pitch deltas {deltas}, want {want}")
    cc11 = [v for b, v in _cc_lane(sc, CH_PANFLUTE, 11)
            if HERALD_T0 - 1e-6 <= b <= HERALD_T1 + 1e-6]
    if len(cc11) < 4 or any(cc11[i] >= cc11[i + 1]
                            for i in range(len(cc11) - 1)):
        fails.append("herald CC11 swell is not strictly rising")
    if HERALD_T1 - HERALD_T0 < 8.0:
        fails.append(f"herald window {HERALD_T1 - HERALD_T0} beats < 2 bars")
    return fails


def _o_morse(sc):
    """The tide-word TURN, tapped on the muted guitar (MORSE_PROGRAMS[3] = 28),
    in standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 28:
        fails.append("morse timbre for T3 must be muted guitar (program 28)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_MUTEGTR)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} "
                     f"(TURN)")
        return fails
    for k, ((on, off, p), (won, wdu)) in enumerate(zip(taps, pairs)):
        if p != MORSE_PITCH:
            fails.append(f"morse tap {k} pitch {p}, want {MORSE_PITCH}")
            break
        if abs(on - (MORSE_T0 + won)) > 1e-6:
            fails.append(f"morse tap {k} onset {on:.3f}, want "
                         f"{MORSE_T0 + won:.3f}")
            break
        if abs((off - on) - wdu * 0.9) > 0.02:
            fails.append(f"morse tap {k} dur {off - on:.3f}, want "
                         f"{wdu * 0.9:.3f}")
            break
    return fails


def _o_vowel_rise(sc):
    """The winter's mouth opening into spring: choir CC70 never exceeds T3's
    cap of 75, and RISES — its per-8-bar-window maximum is non-decreasing."""
    cap = material.VOWEL_CAPS[NUMBER]
    lane = _cc_lane(sc, CH_CHOIR, 70)
    fails = []
    bad = [(b, v) for b, v in lane if v > cap]
    if bad:
        fails.append(f"choir vowel CC70={bad[0][1]} at beat {bad[0][0]:.1f} "
                     f"exceeds the cap {cap}")
    windows: dict[int, int] = {}
    for b, v in lane:
        w = int(b // 32.0)
        windows[w] = max(windows.get(w, 0), v)
    seq = [windows[w] for w in sorted(windows)]
    for i in range(len(seq) - 1):
        if seq[i + 1] < seq[i]:
            fails.append(f"vowel window {i + 1} max {seq[i + 1]} < window {i} "
                         f"max {seq[i]} (the morph must not fall)")
            break
    return fails


def _o_leslie(sc):
    """The drawbar organ's Leslie: at least two spin-ups (slow chorale ramping
    to fast tremolo) on the CC1 rotor lane."""
    lane = _cc_lane(sc, CH_ORGAN, 1)
    fails = []
    if len(lane) < 16:
        fails.append(f"organ Leslie CC1 lane has {len(lane)} events, want the "
                     f"spin-ups")
    vals = [v for _b, v in lane]
    spinups = 0
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] >= vals[j]:
            j += 1
        if j > i and vals[j] - vals[i] >= 50 and vals[j] >= 90:
            spinups += 1
        i = j + 1 if j > i else i + 1
    if spinups < 2:
        fails.append(f"only {spinups} Leslie spin-ups (slow->fast), want >= 2")
    return fails


def _o_steelpan_bank(sc):
    """The steelpan's CC0 second-percussion bank is selected (an alt-bank
    opt-in, verified present)."""
    banks = {v for _b, v in _cc_lane(sc, CH_STEELPAN, 0)}
    if 112 not in banks:
        return [f"steelpan CC0 second-percussion bank (112) not selected "
                f"(got {sorted(banks)})"]
    return []


def _o_accelerando(sc):
    """The spring quickening: movement II's tempo rises monotonically
    96 -> 106 (the accelerando owns II in place of the tide)."""
    seq = [bpm for _b, bpm in _movement_events(I_END, II_END)]
    fails = []
    if len(seq) < 8:
        fails.append(f"accelerando has {len(seq)} tempo events, want >= 8")
        return fails
    if any(seq[i] > seq[i + 1] + 1e-9 for i in range(len(seq) - 1)):
        fails.append("accelerando is not monotonically rising")
    if abs(seq[0] - ACCEL_BPM0) > 1.0:
        fails.append(f"accelerando starts at {seq[0]}, want ~{ACCEL_BPM0:.0f}")
    if abs(seq[-1] - ACCEL_BPM1) > 1.0:
        fails.append(f"accelerando ends at {seq[-1]}, want ~{ACCEL_BPM1:.0f}")
    if seq[-1] - seq[0] < 8.0:
        fails.append(f"accelerando span {seq[-1] - seq[0]:.1f} bpm, want >= 8")
    return fails


def _o_tide_breath(sc):
    """The water is in the tempo everywhere but the spring groove: movements
    I, III and IV each swell (>= 2 troughs); II accelerates instead."""
    fails = []
    for name, t0, t1 in [("I. The Lattice", 0.0, I_END),
                         ("III. High Water", II_END, III_END),
                         ("IV. Slack", III_END, END)]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2 "
                         f"(the map must breathe)")
    return fails


def _o_cadence(sc):
    """The withheld cadence: the bass resolves to A modally (v-i, iv-i), the
    leading tone G# banned across each window on every channel."""
    fails = []
    for lo, hi, down in CAD_WINDOWS:
        for m in material.cadence_failures(sc, CH_BASS, lo, hi, down,
                                           ISLAND_TONIC_PC):
            fails.append(f"[{lo:.0f},{hi:.0f}]: {m}")
    return fails


def _o_shore_pans(sc):
    """The narrowing strait: island channels left (50), mainland right (78) —
    a whole tone narrower than track 2.  The crystal shimmer is exempt (it is
    the album's one autopan channel)."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_MARIMBA, CH_KALIMBA, CH_CHOIR, CH_STEELPAN, CH_VIBES,
              CH_PANFLUTE, CH_PAD}
    mainland = {CH_RHODES, CH_ORGAN, CH_BRASS}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{{ISL_PAN}}}")
    for ch in sorted(mainland):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {MAIN_PAN}:
            fails.append(f"mainland ch{ch} pans {sorted(pans)}, want "
                         f"{{{MAIN_PAN}}}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls three times (track 3), on the island's A, the final
    note-ons — nothing sounds after the first toll but the remaining tolls."""
    fails = []
    bells = _note_ons(sc, CH_BELLS)
    if len(bells) != material.TOLLS[NUMBER]:
        fails.append(f"{len(bells)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p, _v in bells:
        if p % 12 != ISLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want "
                         f"{ISLAND_TONIC_PC} (the island tonic A)")
            break
    all_ons = sorted((b, ch) for ch in sc.events
                     for b, _p, _v in _note_ons(sc, ch))
    if bells:
        toll_on = bells[0][0]
        after = [(b, ch) for b, ch in all_ons
                 if b > toll_on + 1e-6 and ch != CH_BELLS]
        if after:
            fails.append(f"{len(after)} note-on(s) after toll 1 (e.g. ch"
                         f"{after[0][1]} at {after[0][0]:.1f})")
        if all_ons and all_ons[-1][1] != CH_BELLS:
            fails.append("the final note-on is not a toll")
    return fails


def oracles(sc, info, spans):
    return [
        ("convergence", _o_convergence(sc)),
        ("call_and_answer", _o_call_answer(sc)),
        ("end_degrees", _o_end_degrees(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("lattice_3v4", _o_lattice(sc)),
        ("protagonist_bass", _o_protagonist_bass(sc)),
        ("doubled_thumb", _o_doubled_thumb(sc)),
        ("breath_herald", _o_herald(sc)),
        ("morse_turn", _o_morse(sc)),
        ("vowel_rise", _o_vowel_rise(sc)),
        ("leslie_spinups", _o_leslie(sc)),
        ("steelpan_bank", _o_steelpan_bank(sc)),
        ("accelerando", _o_accelerando(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("cadence_law", _o_cadence(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The spring groove reads brighter than the lattice, the herald is the quiet
# inhale, and the slack falls away below high water.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    lattice = _rms_db(40.0, 72.0)       # movement I, the bare 3v4 lattice
    herald = _rms_db(121.0, 127.0)      # the pan-flute inhale, alone
    groove = _rms_db(212.0, 244.0)      # movement II, the full spring chorus
    high = _rms_db(300.0, 344.0)        # movement III, both themes + lattice
    slack = _rms_db(448.0, 472.0)       # movement IV, the kalimba over the pad

    # 1. The spring groove is brighter/denser than the lattice it grew from.
    fails = []
    if groove - lattice < -1.0:
        fails.append(f"spring groove {groove:.1f} dB is quieter than the "
                     f"lattice {lattice:.1f} dB (the answer should bloom)")
    checks.append(("audio_groove_blooms", fails))

    # 2. The herald is the quiet inhale before the groove.
    fails = []
    if groove - herald < 1.0:
        fails.append(f"groove {groove:.1f} dB not >= 1.0 dB over the herald "
                     f"{herald:.1f} dB (the breath should be the quiet part)")
    checks.append(("audio_herald_inhale", fails))

    # 3. Slack water falls away below high water.
    fails = []
    if high - slack < 0.5:
        fails.append(f"slack {slack:.1f} dB not >= 0.5 dB below high water "
                     f"{high:.1f} dB (the tide should recede)")
    checks.append(("audio_slack_recedes", fails))
    return checks





