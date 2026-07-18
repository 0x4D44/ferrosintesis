"""movements/t02_the_winter_ferry.py — track 2 of *The Causeway*.

THE WINTER FERRY.  The failed crossing — a Band-on-the-Run three-act storm
built on a Mrs-Vandebilt engine.  E minor warms into an E-mixolydian false
hope, then falls back to E minor; the shores are four semitones apart now
(the strait has narrowed from track 1's tritone).  Four movements, one
suite that pivots mid-track the way McCartney's do:

  I. Harbour        — a brush kit (ch9 program 40), steel-guitar arpeggios,
     the fretless bass assembling the ferry riff (HOOK2) in fragments while a
     woodblock taps WAIT in Morse; the pan flute sings the ISLAND THEME once,
     the tide breathing the tempo around 72.
  II. The Open Water — the kit swaps to the full sampled kit (a second ch9
     program change — the mid-track swap is an oracle); a pan-flute breath
     heralds the groove (HOOK2's first three notes, two bars alone, a rising
     swell); then the strut locks: a sampled clavinet riffs HOOK2 with CC68
     hammer-on slurs, a muted guitar chops CC74 wah under the doubled thumb,
     brass stabs answer with a channel-aftertouch rasp, and the protagonist
     bass leads on fretless portamento.  E mixolydian brightens (the false
     hope) and an authored accelerando drives 112 -> 138.
  III. Turned Back  — the wave hits: one orchestra-hit + tam-tam moment
     (CC0 alt-bank 14), the tempo collapses to 66, and THE MAINLAND THEME is
     attempted once, complete but alone, on a french horn in C, distance 4;
     CC94 echo throws trail the phrases and a harmonica laments in draw-bend
     scoops over the wreckage.
  IV. Harbour Again — the brush kit returns (a third ch9 program change), the
     ferry riff at half tempo, hollow; the island theme once more; then
     exactly two bell tolls on the island's E, and nothing after them.

Every device the HLD marks verified is an oracle below, and all recurring
data is single-sourced from material.py (the two themes, HOOK2, the
convergence pcs, the morse word WAIT, the tide-breath, the shore pans, the
vowel cap, the tolls, the cadence law).  The strait is four semitones wide.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 2
TITLE = "The Winter Ferry"
FILE = "02 - The Winter Ferry.mid"
SEED = 202607182
COMMENT = (
    "The Winter Ferry - the failed crossing, a Band-on-the-Run storm on a "
    "Mrs-Vandebilt engine.  E minor warms to an E mixolydian false hope and "
    "falls back: a harbour of brush kit, steel-guitar arpeggios and a "
    "fretless assembling the ferry riff while a woodblock taps WAIT; the kit "
    "swaps to the full set for the open water, where a breath flute heralds a "
    "clavinet strut - HOOK2 with hammer-on slurs, wah-chopped muted guitar, "
    "brass stabs rasping with aftertouch, the protagonist bass leading on "
    "portamento under an accelerando 112 to 138; then the wave, an "
    "orchestra-hit and tam-tam, a collapse to 66 and the mainland theme once "
    "in C over harmonica wreckage; and the harbour again, the riff at half "
    "tempo, two bells tolling the island's E.")

# ---------------------------------------------------------------------------
# Channels.  Island pole (the ice / Enigma weather) sits left at
# SHORE_PANS[2][0]=44; the mainland pole (the McCartney band) sits right at
# 84; the neutral spine (bass, drums, doubled thumb, the wave, morse, bells,
# the harmonica lament) holds 64.  The strait is four semitones narrower than
# track 1's tritone.
# ---------------------------------------------------------------------------

CH_STEEL, CH_CLAV, CH_MUTEGTR, CH_BRASS = 0, 1, 2, 3
CH_BASS, CH_HORN, CH_PANFLUTE, CH_CHOIR = 4, 5, 6, 7
CH_PAD, CH_DRUMS, CH_HARMON, CH_WAVE = 8, 9, 10, 11
CH_WOOD, CH_BELLS = 12, 13

_MM = material.MODE_MINOR                  # aeolian - the island's mode
_MX = "mixolydian"                         # the false hope of the open water

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (44, 84)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 4, 0

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 96.0
HERALD_T0, HERALD_T1 = 96.0, 104.0         # >= 2 bars, pan flute alone
GROOVE_T0 = 104.0                          # the strut locks in
II_END = 296.0
III_END = 384.0
END = 472.0

# --- the accelerando (the authored swell of movement II) ---
ACCEL_T0, ACCEL_T1 = 96.0, 288.0
ACCEL_BPM0, ACCEL_BPM1 = 112.0, 138.0

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE = en.n("E4")                   # 64 - the island tonic (deg 1)
ISLAND_STMT1_T0 = 8.0                       # harbour: the island sings once
ISLAND_STMT2_T0, ISLAND_STMT2_STR = 400.0, 2.0   # harbour again, half tempo
MAINLAND_BASE = en.n("C4")                 # 60 - the far shore in C, distance 4
MAINLAND_T0, MAINLAND_STR = 312.0, 1.5     # the one mainland attempt

HERALD_PITCH = en.n("B4")                  # 71 - the hook head, breathed
STRUT_ROOT_LO = en.n("E3")                 # 52 - the funky low clavinet
STRUT_ROOT_HI = en.n("E4")                 # 64 - the octave-up answer
BASS_HOOK_ROOT = en.n("E2")                # 40 - HOOK2 in the bass

CHORUS_SPANS = [(104.0, 192.0), (208.0, 288.0)]      # the two strut choruses
CAD_WINDOWS = [(188.0, 192.0, 192.0),                # chorus 1 -> i
               (284.0, 288.0, 288.0),                # chorus 2 -> i
               (452.0, 456.0, 456.0)]                # the harbour resettles

MORSE_T0 = 24.0
MORSE_PITCH = en.n("E5")                    # 76 - the woodblock's fixed tap
TOLL_T0 = 466.0
TOLL_PITCH = en.n("E3")                     # 52 - pc 4 = the island tonic

# --- the tide-breath tempo map: I / III / IV breathe, II accelerates ---


def _accel(t0: float, t1: float, bpm0: float, bpm1: float,
           step: float = 8.0) -> list[tuple[float, float]]:
    """A monotonically rising tempo ramp — the authored accelerando that is
    movement II's 'swell' (the tide owns I, III and IV instead)."""
    out = []
    b = t0
    while b <= t1 + 1e-9:
        out.append((b, round(en.lerp(bpm0, bpm1, (b - t0) / (t1 - t0)), 2)))
        b += step
    return out


TEMPO_MAP = (
    material.tide_breath(72.0, 0.0, I_END, period=32.0, depth=4.0)
    + _accel(ACCEL_T0, ACCEL_T1, ACCEL_BPM0, ACCEL_BPM1)
    + material.tide_breath(66.0, II_END, III_END, period=32.0, depth=5.0)
    + material.tide_breath(60.0, III_END, END, period=32.0, depth=4.0))

# The kit swaps: brush (40) in the harbour, the full sampled kit (0) in the
# open water, brush again (40) in the harbour's return — the mid-track swap
# is an oracle.
KIT_BRUSH, KIT_FULL = 40, 0
KIT_CHANGES = [(CH_DRUMS, 0.0, KIT_BRUSH),
               (CH_DRUMS, I_END, KIT_FULL),
               (CH_DRUMS, III_END, KIT_BRUSH)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Harbour", 0.0, I_END),
               ("II. The Open Water", I_END, II_END),
               ("III. Turned Back", II_END, III_END),
               ("IV. Harbour Again", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1),                   # E minor: one sharp, minor
             (I_END, 3, 0),                 # E mixolydian (A-major parent)
             (II_END, 1, 1)],               # E minor again
    channels=[(CH_STEEL, "steel guitar", 25, 90, MAIN_PAN, 40),
              (CH_CLAV, "clavinet", 7, 96, MAIN_PAN, 30),
              (CH_MUTEGTR, "muted guitar", 28, 86, 64, 38),
              (CH_BRASS, "brass section", 61, 92, MAIN_PAN, 42),
              (CH_BASS, "fretless bass", 35, 100, 64, 25),
              (CH_HORN, "french horn", 60, 88, MAIN_PAN, 72),
              (CH_PANFLUTE, "pan flute", 75, 84, ISL_PAN, 60),
              (CH_CHOIR, "choir", 52, 76, ISL_PAN, 66),
              (CH_PAD, "warm pad", 89, 74, ISL_PAN, 70),
              (CH_DRUMS, "kit", 0, 96, 64, 28),
              (CH_HARMON, "harmonica", 22, 84, 64, 55),
              (CH_WAVE, "tam-tam", 55, 90, 64, 80),
              (CH_WOOD, "woodblock", 115, 82, 64, 30),
              (CH_BELLS, "tubular bells", 14, 90, 64, 60)],
    program_changes=KIT_CHANGES,
    extra_markers=[(HERALD_T0, "breath herald"), (GROOVE_T0, "the strut"),
                   (MAINLAND_T0, "the mainland attempt"),
                   (TOLL_T0, "the tolls")],
    bank_selects=[(CH_WAVE, 14)],           # tam-tam alt-bank (CC0=14)
)

PROGRAM_WHITELIST = {7, 14, 22, 25, 28, 35, 52, 55, 60, 61, 75, 89, 115}
CENTERED_CHANNELS = {CH_MUTEGTR, CH_BASS, CH_DRUMS, CH_HARMON, CH_WAVE,
                     CH_WOOD, CH_BELLS}
NOTE_RANGES = {
    CH_STEEL: (46, 80), CH_CLAV: (48, 74), CH_MUTEGTR: (40, 72),
    CH_BRASS: (52, 84), CH_BASS: (28, 52), CH_HORN: (52, 74),
    CH_PANFLUTE: (60, 80), CH_CHOIR: (52, 76), CH_PAD: (33, 72),
    CH_HARMON: (55, 80), CH_WAVE: (36, 60), CH_WOOD: (76, 76),
    CH_BELLS: (48, 60),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # scoops recentre at every seam
DURATION_WINDOW = (348.0, 364.0)            # ~5:55 incl. the 2-beat end pad
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


def _aftertouch_lane(sc, ch):
    return sorted((t / _PPQ, d[1]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xD0)


def _onsets_in(sc, ch, lo, hi):
    return [(b, p, v) for b, p, v in _note_ons(sc, ch) if lo - 1e-6 <= b < hi]


def _movement_events(lo, hi):
    """The tempo events whose beat falls inside [lo, hi)."""
    return [(b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6]


def _in_span(beat):
    return any(lo <= beat < hi for lo, hi in CHORUS_SPANS)


# ---------------------------------------------------------------------------
# Harmony — E aeolian (the harbours) and E mixolydian (the open water, the
# false hope).  The bass walks a low scale; pads and stabs voice triads.
# ---------------------------------------------------------------------------

# The fretless's low register: E aeolian from E1, spanning >= 19 semitones.
BASS_SCALE = [en.n(x) for x in
              ("E1", "F#1", "G1", "A1", "B1", "C2", "D2", "E2", "F#2",
               "G2", "A2", "B2", "C3", "D3")]

# The open-water bass climbs the mixolydian degrees (raised 6th C#, natural
# D) for the funk pump's brightness.
BASS_MIX = [en.n(x) for x in
            ("E1", "F#1", "G#1", "A1", "B1", "C#2", "D2", "E2", "F#2",
             "G#2", "A2", "B2", "C#3", "D3")]

# The harbour brush groove's steel-guitar arpeggio cycle (E aeolian):
# i - bVII - bVI - v, three-note broken chords rocking gently.
HARBOUR_ARPS = [
    [en.n("E3"), en.n("G3"), en.n("B3"), en.n("E4")],     # Em  (i)
    [en.n("D3"), en.n("F#3"), en.n("A3"), en.n("D4")],    # D   (bVII)
    [en.n("C3"), en.n("E3"), en.n("G3"), en.n("C4")],     # C   (bVI)
    [en.n("B2"), en.n("D3"), en.n("F#3"), en.n("B3")],    # Bm  (v)
]

# The open-water pad cycle (E mixolydian): E - D - A - B, the bright
# dominant colour under the strut.
MIX_PAD = [
    [en.n("E2"), en.n("B2"), en.n("E3"), en.n("G#3")],    # E   (I)
    [en.n("D2"), en.n("A2"), en.n("D3"), en.n("F#3")],    # D   (bVII)
    [en.n("A1"), en.n("E2"), en.n("A2"), en.n("C#3")],    # A   (IV)
    [en.n("B1"), en.n("F#2"), en.n("B2"), en.n("D3")],    # B   (v)
]

# The wreckage pad (III) — bleak of E aeolian, thinned to open fifths.
WRECK_PAD = [
    [en.n("E2"), en.n("B2"), en.n("E3")],                 # Em
    [en.n("C2"), en.n("G2"), en.n("C3")],                 # C
    [en.n("A1"), en.n("E2"), en.n("A2")],                 # Am
]

# Brass stab voicings (E mixolydian): the answering horn-section punch.
BRASS_STABS = [
    [en.n("E4"), en.n("G#4"), en.n("B4")],                # E
    [en.n("D4"), en.n("F#4"), en.n("A4")],                # D
    [en.n("A3"), en.n("C#4"), en.n("E4")],                # A
    [en.n("B3"), en.n("D4"), en.n("F#4")],                # B
]

# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (the two themes, HOOK2, morse, tolls, the
# herald, the doubled thumb) are jt=0 so every statement is findable and the
# funk pump locks hard; texture lanes take a light jitter.
# ---------------------------------------------------------------------------

def _pad_cycle(sc, ch, t0, t1, cycle, span, vel, curve, vowel=None):
    """Sustained voicings stepping through `cycle`, one chord every `span`
    beats from t0 to t1, ending exactly at t1 so no chord rings past the
    movement.  `curve` is an (beat, cc11) breakpoint list."""
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


def _brush_groove(sc, t0, t1):
    """The harbour's brush kit (ch9 program 40): a soft, swung half-time
    pattern — kick on 1, a brushed backbeat, quiet closed hats."""
    bar = t0
    while bar < t1 - 1e-6:
        sc.hit(36, bar, 60, jt=0)                     # kick on the downbeat
        sc.hit(40, bar + 2.0, 48, jt=0)               # brushed snare, half-time
        for q in range(8):
            v = 30 + (8 if q % 2 == 0 else 0)
            sc.hit(42, bar + q * 0.5, v, jt=2)        # closed hats, brushed
        if int((bar - t0) // 4) % 4 == 3:
            sc.hit(46, bar + 3.5, 34, jt=0)           # an open-hat lift per phrase
        bar += 4.0


def _steel_arps(sc, t0, t1):
    """Steel-guitar arpeggios rocking up and down the harbour chord cycle,
    eighth notes, a gentle velocity sway."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        chord = HARBOUR_ARPS[ci % len(HARBOUR_ARPS)]
        seq = chord + chord[-2:0:-1]                  # up then down (no repeat)
        for q in range(8):
            p = seq[q % len(seq)]
            v = 54 + (8 if q % 4 == 0 else 0)
            sc.note(CH_STEEL, p, bar + q * 0.5, 0.5 * 0.92, v, jt=2, jv=3)
        bar += 4.0
        ci += 1


def _bass_fragments(sc, t0, t1):
    """The fretless assembling the ferry riff (HOOK2) in growing fragments,
    then stating it whole once as the crossing is decided.  The partials are
    fewer than six notes, so they never register as full hook statements."""
    root = BASS_HOOK_ROOT                             # E2
    cell = material.HOOKS[NUMBER]
    # Growing prefixes at bars 5, 9, 13, 17 (2, 3, 4, 5 notes).
    for bar, k in [(16.0, 2), (32.0, 3), (48.0, 4), (64.0, 5)]:
        for on, du, semis in cell[:k]:
            sc.note(CH_BASS, root + semis, bar + on, du * 0.9,
                    58 + 3 * k, jt=0, jv=3)
        # a low walking pickup between fragments (keeps the fretless singing)
        for j, idx in enumerate((0, 2, 4, 2)):
            sc.note(CH_BASS, BASS_SCALE[idx], bar + 4.5 + j * 0.75, 0.7,
                    50, jt=0, jv=3)
    # bar 21: the riff comes together — one full statement (adds density).
    material.play_hook(sc, CH_BASS, 80.0, root, NUMBER, vel=74, gate=0.9)
    for j, idx in enumerate((7, 6, 5, 4, 2, 0)):      # sink home under the pad
        sc.note(CH_BASS, BASS_SCALE[idx], 84.5 + j * 1.5, 1.3, 52 - j,
                jt=0, jv=3)


def _b_harbour(sc):
    """I. Harbour [0, 96) — brush kit, steel arps, the fretless assembling
    the ferry riff, a woodblock tapping WAIT, and the island theme once."""
    _pad_cycle(sc, CH_PAD, 0.0, I_END, HARBOUR_ARPS, 8.0, 40,
               [(0.0, 34), (48.0, 52), (I_END - 1, 40)])
    _pad_cycle(sc, CH_CHOIR, 0.0, I_END, [[71], [69], [67], [66]], 8.0,
               42, [(0.0, 38), (48.0, 58), (I_END - 1, 40)],
               vowel=[(0.0, 10), (56.0, 34), (I_END - 1, 42)])
    en.cc_curve(sc, CH_CHOIR, 1, [(0.0, 0), (I_END - 1, 18)], step=8.0)
    _brush_groove(sc, 0.0, I_END)
    _steel_arps(sc, 0.0, I_END)
    _bass_fragments(sc, 0.0, I_END)
    # the woodblock taps WAIT (MORSE_PROGRAMS[2] = 115) in standard timing.
    material.play_morse(sc, CH_WOOD, MORSE_T0, NUMBER, MORSE_PITCH)
    # the island sings once, alone on its pan flute (monophonic statement).
    material.play_island(sc, CH_PANFLUTE, ISLAND_STMT1_T0, ISLAND_BASE,
                         vel=72, vel_end=62)
    en.expr_curve(sc, CH_PANFLUTE,
                  [(ISLAND_STMT1_T0, 40), (ISLAND_STMT1_T0 + 4, 84),
                   (ISLAND_STMT1_T0 + 8, 44)], step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1,
                [(ISLAND_STMT1_T0, 4), (ISLAND_STMT1_T0 + 8, 24)], step=1.0)


# -- II. The Open Water: the herald and the strut ---------------------------

def _herald(sc):
    """Enigma's inhale: HOOK2's first three notes (deltas 0, 3, 5) on the pan
    flute, alone, over a strictly rising CC11 swell — two bars.  The three
    notes are laid contiguous so nothing else sounds in the window."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]      # [0, 3, 5]
    starts = [HERALD_T0, HERALD_T0 + 3.0, HERALD_T0 + 6.0]
    durs = [2.8, 2.8, 3.6]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, HERALD_PITCH + s, st, du, 54, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 16), (HERALD_T1, 104)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 28)],
                step=0.5)


def _intensity(beat):
    """0 -> 1 across the accelerando, driving the groove's dynamic swell."""
    return max(0.0, min(1.0, (beat - GROOVE_T0) / (ACCEL_T1 - GROOVE_T0)))


def _full_kit(sc, t0, t1):
    """The full sampled kit: a driving funk backbeat that tightens with the
    accelerando (hats thicken to sixteenths, velocities climb)."""
    bar = t0
    while bar < t1 - 1e-6:
        g = _intensity(bar)
        kv = int(88 + 24 * g)
        sc.hit(36, bar, kv, jt=0)                     # kick on 1
        sc.hit(36, bar + 1.5, kv - 10, jt=0)          # the funk push (and-of-2)
        sc.hit(36, bar + 2.5, kv - 16, jt=0)          # and the and-of-3
        sc.hit(38, bar + 1.0, int(84 + 20 * g), jt=0)  # snare backbeat (2)
        sc.hit(38, bar + 3.0, int(88 + 20 * g), jt=0)  # snare backbeat (4)
        sixteenths = g > 0.45
        steps = 16 if sixteenths else 8
        for q in range(steps):
            t = bar + q * (0.25 if sixteenths else 0.5)
            drum = 46 if (q % (steps // 4) == 0) else 42
            v = int(38 + 18 * g + (10 if drum == 46 else 0))
            sc.hit(drum, t, v, jt=0)
        if int((bar - t0) // 4) % 4 == 3:
            sc.hit(38, bar + 3.5, int(60 + 20 * g), jt=0)   # a ghost-snare pickup
        bar += 4.0


def _kit_windup(sc, t0, t1):
    """The wind-up into the wave: a tom roll and a rising crash swell across
    the last two bars of the open water."""
    n = int((t1 - t0) / 0.25)
    for i in range(n):
        t = t0 + i * 0.25
        drum = (41, 43, 45, 47)[min(3, i * 4 // n)]   # toms climbing
        sc.hit(drum, t, int(50 + 60 * i / n), jt=0)
    for q in range(4):
        sc.hit(49, t1 - 2.0 + q * 0.5, 60 + q * 12, jt=0)   # crash build


def _clav_strut(sc):
    """The Vandebilt strut: the clavinet riffs HOOK2 every bar with CC68
    hammer-on slurs on the climb, alternating the low and octave-up roots,
    resting every fourth bar so the brass can answer."""
    for lo, hi in CHORUS_SPANS:
        t = lo
        i = 0
        while t < hi - 4.0 + 1e-6:
            if i % 4 != 3:                            # answer-bar rest
                root = STRUT_ROOT_LO if i % 2 == 0 else STRUT_ROOT_HI
                sc.cc(CH_CLAV, 68, 127, t + 0.7)      # hammer-on into the climb
                material.play_hook(sc, CH_CLAV, t, root, NUMBER,
                                   vel=84, vel_end=94, gate=0.9)
                sc.cc(CH_CLAV, 68, 0, t + 2.2)        # release after the +7
            t += 4.0
            i += 1


def _muted_wah(sc):
    """The muted guitar's wah: a slow CC74 sweep across each chorus, filtering
    the doubled-thumb octaves into the funk 'chk' — confined to the choruses so
    the thickening reads as a chorus event."""
    for lo, hi in CHORUS_SPANS:
        en.wah(sc, CH_MUTEGTR, lo, hi - lo, lo=34, hi=108,
               cycles_per_beat=0.25, step=0.5)


def _brass_stabs(sc):
    """Brass-section stabs answering the clav on the rest bars, vel 90+, each
    stab rasping with a channel-aftertouch swell."""
    for lo, hi in CHORUS_SPANS:
        bar = lo
        ci = 0
        while bar < hi - 1e-6:
            if int((bar - lo) // 4) % 4 == 3:         # the clav's answer bar
                chord = BRASS_STABS[ci % len(BRASS_STABS)]
                for st, du in [(0.0, 0.9), (1.5, 0.7), (2.5, 1.3)]:
                    for p in chord:
                        sc.note(CH_BRASS, p, bar + st, du * 0.9, 96, jt=0, jv=2)
                    en.at_curve(sc, CH_BRASS,
                                [(bar + st, 18), (bar + st + du * 0.5, 92),
                                 (bar + st + du, 8)], step=0.25)
            bar += 4.0
            ci += 1


# A one-bar funk cell for the fretless (BASS_MIX indices): a syncopated,
# mostly stepwise E-mixolydian pump around the root (E-F#-E-D-E-F#-G#) — the
# leaps live in the octave pops of the cadences and the harbour fragments.
BASS_CELL = [
    (0.0, 7, 0.45, 88), (0.5, 8, 0.22, 60), (1.0, 7, 0.45, 78),
    (1.75, 6, 0.28, 74), (2.5, 7, 0.45, 84), (3.0, 8, 0.45, 76),
    (3.5, 9, 0.40, 74),
]


def _bass_funk(sc, t0, t1):
    """The protagonist bass drives the funk cell, and every fourth bar climbs
    the mixolydian degrees on portamento to a high D3 with a fretless 'mwah'
    scoop — the wide range and the glide the McCartney bass is built on."""
    bar = t0
    i = 0
    while bar < t1 - 1e-6:
        if i % 4 == 3:
            en.portamento_on(sc, CH_BASS, bar, time_cc=48)
            for j, idx in enumerate((7, 8, 9, 10, 11, 12, 13)):
                du = 0.9 if idx == 13 else 0.45
                if idx == 13:
                    en.bend_ramp(sc, CH_BASS, bar + j * 0.5 - 0.18,
                                 bar + j * 0.5 + 0.12, -0.45, 0.0, steps=6)
                sc.note(CH_BASS, BASS_MIX[idx], bar + j * 0.5, du,
                        78 + j * 2, jt=0, jv=3)
            en.portamento_off(sc, CH_BASS, bar + 3.9)
        else:
            for on, idx, du, v in BASS_CELL:
                sc.note(CH_BASS, BASS_MIX[idx], bar + on, du, v, jt=0, jv=3)
        bar += 4.0
        i += 1


def _bass_cadence(sc, lo, down, approach_idx):
    """A modal approach (v or bVII) into a tonic-E landing on the downbeat —
    the withheld cadence, the leading tone nowhere near it."""
    ap = BASS_MIX[approach_idx]
    sc.note(CH_BASS, ap, down - 2.0, 1.0, 82, jt=0, jv=3)
    sc.note(CH_BASS, ap, down - 1.0, 1.0, 80, jt=0, jv=3)
    sc.note(CH_BASS, en.n("E2"), down, 2.0, 92, jt=0, jv=3)


def _bass_bridge(sc, t0, t1):
    """The breakdown between choruses: a stripped, undoubled root walk that
    stays off the tonic E (the cadence just landed it)."""
    steps = (4, 6, 3, 4, 6, 9, 6)
    for i, idx in enumerate(steps):
        sc.note(CH_BASS, BASS_MIX[idx], t0 + i * (t1 - t0) / len(steps), 1.6,
                72 - (i % 2) * 8, jt=0, jv=3)


def _bass_windup(sc, t0, t1):
    """The rising fill into the wave — the bass climbs to the break."""
    climb = (7, 8, 9, 10, 11, 12, 13, 13)
    n = len(climb)
    for i, idx in enumerate(climb):
        sc.note(CH_BASS, BASS_MIX[idx], t0 + i * (t1 - t0) / n,
                (t1 - t0) / n * 0.9, 78 + i, jt=0, jv=3)


def _bass_lead(sc):
    """The whole open-water bass: HOOK2 stated at each chorus head (>= 2 in the
    bass, inside the choruses), funk between, a modal cadence closing each
    chorus, a bridge, and the wind-up into the wave."""
    material.play_hook(sc, CH_BASS, 104.0, BASS_HOOK_ROOT, NUMBER,
                       vel=86, vel_end=94, gate=0.9)
    _bass_funk(sc, 108.0, 188.0)
    _bass_cadence(sc, 188.0, 192.0, approach_idx=6)      # D2 (bVII) -> E
    _bass_bridge(sc, 194.0, 208.0)
    material.play_hook(sc, CH_BASS, 208.0, BASS_HOOK_ROOT, NUMBER,
                       vel=88, vel_end=96, gate=0.9)
    _bass_funk(sc, 212.0, 284.0)
    _bass_cadence(sc, 284.0, 288.0, approach_idx=4)      # B1 (v) -> E
    _bass_windup(sc, 290.0, 296.0)
    sc.bend(CH_BASS, 294.0, 0.0)                         # recentre before III


def _double_thumb(sc):
    """The chorus thickens: every bass note-on inside the choruses shadowed at
    the octave on the muted guitar (the doubled thumb), and nowhere else."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if _in_span(beat):
            sc.note(CH_MUTEGTR, pitch + 12, beat, 0.4, 72, jt=0, jv=2)


def _b_open_water(sc):
    """II. The Open Water [96, 296) — the herald, then the accelerando strut:
    clavinet HOOK2, wah-chopped muted guitar under the doubled thumb, brass
    stabs, the leading fretless, an E-mixolydian pad brightening the false
    hope.  The bass is emitted before the doubled thumb reads it."""
    _herald(sc)
    _pad_cycle(sc, CH_PAD, GROOVE_T0, II_END, MIX_PAD, 8.0, 44,
               [(GROOVE_T0, 40), (200.0, 60), (II_END - 1, 52)])
    en.cc_curve(sc, CH_PAD, 1, [(GROOVE_T0, 0), (II_END - 1, 30)], step=8.0)
    _full_kit(sc, GROOVE_T0, 288.0)
    _kit_windup(sc, 288.0, II_END)
    _bass_lead(sc)
    _double_thumb(sc)
    _muted_wah(sc)
    _clav_strut(sc)
    _brass_stabs(sc)


# -- III. Turned Back: the wave, the mainland attempt, the lament -----------

# The harmonica's E-minor-blues lament (no D#, so the cadence ban is safe):
# (phrase_start, [(rel_onset, pitch, dur, vel)]).
HARMON_PHRASES = [
    (330.0, [(0.0, en.n("B4"), 1.0, 70), (1.5, en.n("A4"), 1.0, 66),
             (3.0, en.n("G4"), 2.2, 64)]),
    (338.0, [(0.0, en.n("E4"), 1.5, 66), (2.0, en.n("G4"), 1.0, 68),
             (3.0, en.n("A4"), 1.8, 64)]),
    (348.0, [(0.0, en.n("B4"), 1.0, 72), (1.5, en.n("D5"), 1.5, 70),
             (3.5, en.n("B4"), 2.2, 66)]),
    (358.0, [(0.0, en.n("A4"), 1.5, 66), (2.0, en.n("G4"), 1.0, 64),
             (3.0, en.n("E4"), 3.4, 58)]),
    (368.0, [(0.0, en.n("G4"), 1.0, 62), (1.5, en.n("A4"), 1.0, 60),
             (3.0, en.n("E4"), 4.0, 54)]),
]


def _wave(sc):
    """The wave: the orchestra-hit / tam-tam (CC0 alt-bank 14) breaks over a
    crash and a surging tom roll — the crossing lost."""
    for p in (en.n("E2"), en.n("B2")):
        sc.note(CH_WAVE, p, II_END, 6.0, 98, jt=0, jv=2)
    en.echo_throw(sc, CH_WAVE, II_END + 1.0)
    sc.hit(57, II_END, 100, jt=0)                     # crash
    for i in range(8):                                # the surge, fading
        drum = (45, 43, 41, 41)[min(3, i // 2)]
        sc.hit(drum, II_END + i * 0.25, 92 - i * 8, jt=0)


def _mainland_attempt(sc):
    """THE MAINLAND THEME, once, complete but alone: a french horn in C
    (distance 4 from the island's E), an echo throw trailing its close."""
    material.play_mainland(sc, CH_HORN, MAINLAND_T0, MAINLAND_BASE,
                           stretch=MAINLAND_STR, vel=72, vel_end=60)
    end = MAINLAND_T0 + material.MAINLAND_LEN * MAINLAND_STR
    en.expr_curve(sc, CH_HORN,
                  [(MAINLAND_T0, 36), (MAINLAND_T0 + 6, 90),
                   (MAINLAND_T0 + 11, 50), (end, 20)], step=0.5)
    en.cc_curve(sc, CH_HORN, 1, [(MAINLAND_T0, 0), (end, 24)], step=1.0)
    en.echo_throw(sc, CH_HORN, end - 1.5)


def _harmonica_lament(sc):
    """The harmonica laments over the wreckage: bluesy phrases, each scooped
    into on a draw-bend that recentres — every bend home by the movement
    boundary."""
    for start, notes in HARMON_PHRASES:
        en.bend_ramp(sc, CH_HARMON, start - 0.18, start + 0.12, -0.5, 0.0,
                     steps=6)                          # scoop into the phrase
        for on, p, du, v in notes:
            sc.note(CH_HARMON, p, start + on, du, v, jt=2, jv=3)
    en.echo_throw(sc, CH_HARMON, 342.0)
    en.echo_throw(sc, CH_HARMON, 374.5)
    sc.bend(CH_HARMON, 382.0, 0.0)                     # recentre before IV


def _b_turned_back(sc):
    """III. Turned Back [296, 384) — the wave, the collapse to 66, the one
    mainland attempt in C over a sparse wreckage of pad, sealed choir and the
    harmonica lament."""
    _wave(sc)
    _pad_cycle(sc, CH_PAD, II_END, III_END, WRECK_PAD, 8.0, 40,
               [(II_END, 46), (340.0, 40), (III_END - 1, 28)])
    _pad_cycle(sc, CH_CHOIR, II_END, III_END, [[71], [67], [64]],
               8.0, 40, [(II_END, 38), (340.0, 50), (III_END - 1, 30)],
               vowel=[(II_END, 12), (340.0, 44), (III_END - 1, 30)])
    en.cc_curve(sc, CH_CHOIR, 1, [(II_END, 0), (III_END - 1, 20)], step=8.0)
    _mainland_attempt(sc)
    _harmonica_lament(sc)


# -- IV. Harbour Again: the riff halved, the island once more, two tolls -----

def _steel_half_riff(sc, t0, root):
    """The ferry riff at half tempo on the steel guitar — hollow, the crossing
    remembered."""
    material.play_hook(sc, CH_STEEL, t0, root, NUMBER, stretch=2.0,
                       vel=58, vel_end=50, gate=0.9)


def _b_harbour_again(sc):
    """IV. Harbour Again [384, 472) — the brush kit returns, the riff at half
    tempo, the island theme once more, a modal resettle, then two bell tolls
    on the island's E and nothing after them."""
    _pad_cycle(sc, CH_PAD, III_END, 470.0, WRECK_PAD, 8.0, 38,
               [(III_END, 40), (430.0, 44), (466.0, 24)])
    _brush_groove(sc, III_END, 456.0)                 # hollow, ends at the cadence
    # the ferry riff at half tempo — fretless, then steel echoing it.
    material.play_hook(sc, CH_BASS, 392.0, BASS_HOOK_ROOT, NUMBER,
                       stretch=2.0, vel=64, vel_end=54, gate=0.9)
    _steel_half_riff(sc, 420.0, STRUT_ROOT_LO)
    # the island theme once more, slow, on its pan flute (monophonic).
    material.play_island(sc, CH_PANFLUTE, ISLAND_STMT2_T0, ISLAND_BASE,
                         stretch=ISLAND_STMT2_STR, vel=62, vel_end=52)
    en.expr_curve(sc, CH_PANFLUTE,
                  [(ISLAND_STMT2_T0, 36), (ISLAND_STMT2_T0 + 8, 70),
                   (ISLAND_STMT2_T0 + 16, 34)], step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1,
                [(ISLAND_STMT2_T0, 4), (ISLAND_STMT2_T0 + 16, 22)], step=1.0)
    # the harbour resettles: a modal cadence to E (v -> i).
    _bass_cadence(sc, 452.0, 456.0, approach_idx=4)   # B1 (v) -> E
    # the bell buoy: exactly two tolls on the island's E, the final note-ons.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, vel=80, dur=3.5)


BUILDERS = [_b_harbour, _b_open_water, _b_turned_back, _b_harbour_again]


# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """The island states twice (tonic E, pc 4); the mainland once (tonic C,
    pc 0) — distance 4, the strait a fourth narrower than track 1's tritone."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 2:
        fails.append(f"{len(isl)} island statements, want 2 (I and IV)")
    for ch, start, _end, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {ISLAND_TONIC_PC} (E)")
    if len(mnl) != 1:
        fails.append(f"{len(mnl)} mainland statements, want 1 (III only)")
    for ch, start, _end, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {MAINLAND_TONIC_PC} (C)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 4:
            fails.append(f"shore distance {dist}, want 4")
    return fails


def _o_no_overlap(sc):
    """The simultaneity ban: no island statement sounds against the mainland."""
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    pairs = material.overlapping_pairs(isl, mnl)
    return [f"island {a[1]:.1f}-{a[2]:.1f} overlaps mainland "
            f"{b[1]:.1f}-{b[2]:.1f}" for a, b in pairs]


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
    """The ferry riff earworm: HOOK2 stated >= 6 times across the track."""
    hits = 0
    for ch in sc.events:
        hits += len(material.find_statements(material.note_ons(sc, ch),
                                             material.HOOKS[NUMBER]))
    if hits < 6:
        return [f"HOOK2 found {hits} times, want >= 6"]
    return []


def _o_protagonist_bass(sc):
    """The McCartney bass leads: stepwise-dominant (floor 0.42 for the funk
    pump), wide-ranging, stating the hook in the bass inside each chorus."""
    fails = []
    ons = _note_ons(sc, CH_BASS)
    pitches = [p for _b, p, _v in ons]
    if len(pitches) < 2:
        return ["protagonist bass is silent"]
    steps = sum(1 for a, b in zip(pitches, pitches[1:]) if 1 <= abs(b - a) <= 2)
    ratio = steps / (len(pitches) - 1)
    if ratio < 0.42:
        fails.append(f"bass stepwise ratio {ratio:.2f} < 0.42")
    span = max(pitches) - min(pitches)
    if span < 19:
        fails.append(f"bass range {span} semitones < 19")
    bass_hooks = material.find_statements(material.note_ons(sc, CH_BASS),
                                          material.HOOKS[NUMBER])
    in_chorus = [h for h in bass_hooks if _in_span(h[0])]
    if len(in_chorus) < 2:
        fails.append(f"hook stated {len(in_chorus)} times in the bass inside "
                     f"the choruses, want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The chorus thickens: every bass note-on shadowed at the octave on the
    muted guitar inside the choruses (coverage >= 0.80), and not outside."""
    fails = []
    guitar = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_MUTEGTR)]

    def shadowed(btick, bp):
        return any(pp == bp + 12 and abs(pt - btick) <= 10 for pt, pp in guitar)

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
    HOOK2's first three notes over a strictly-rising CC11 swell."""
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
    """The tide-word WAIT, tapped on woodblock (MORSE_PROGRAMS[2] = 115), in
    standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 115:
        fails.append("morse timbre for T2 must be woodblock (program 115)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_WOOD)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} "
                     f"(WAIT)")
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


def _o_vowel_cap(sc):
    """The winter's mouth: choir CC70 never exceeds T2's cap of 50."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_accelerando(sc):
    """The authored swell of the open water: movement II's tempo rises
    monotonically 112 -> 138 (the accelerando owns II in place of the tide)."""
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
    if seq[-1] - seq[0] < 20.0:
        fails.append(f"accelerando span {seq[-1] - seq[0]:.1f} bpm, want >= 20")
    return fails


def _o_tide_breath(sc):
    """The water is in the tempo everywhere but the open water: movements I,
    III and IV each swell (>= 2 troughs); II accelerates instead."""
    fails = []
    for name, t0, t1 in [("I. Harbour", 0.0, I_END),
                         ("III. Turned Back", II_END, III_END),
                         ("IV. Harbour Again", III_END, END)]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2 "
                         f"(the map must breathe)")
    return fails


def _o_cadence(sc):
    """The withheld cadence: the bass resolves to E modally (bVII-i, v-i), the
    leading tone banned across each window on every channel."""
    fails = []
    for lo, hi, down in CAD_WINDOWS:
        for m in material.cadence_failures(sc, CH_BASS, lo, hi, down,
                                           ISLAND_TONIC_PC):
            fails.append(f"[{lo:.0f},{hi:.0f}]: {m}")
    return fails


def _o_kit_swap(sc):
    """The mid-track kit swap: brush (40) in the harbours, the full kit (0) in
    the open water — three ch9 program changes, pinned in time."""
    progs = sorted((t / _PPQ, d[1]) for t, _p, d in sc.events.get(CH_DRUMS, [])
                   if (d[0] & 0xF0) == 0xC0)
    want = [(0.0, KIT_BRUSH), (I_END, KIT_FULL), (III_END, KIT_BRUSH)]
    fails = []
    if len(progs) != len(want):
        fails.append(f"{len(progs)} kit program changes, want {len(want)}")
        return fails
    for (gt, gp), (wt, wp) in zip(progs, want):
        if abs(gt - wt) > 1e-6 or gp != wp:
            fails.append(f"kit change at {gt:.1f} -> prog {gp}, want "
                         f"{wt:.1f} -> {wp}")
    return fails


def _o_hammer_on(sc):
    """The clavinet's CC68 hammer-on slurs recur through the strut."""
    lane = [(b, v) for b, v in _cc_lane(sc, CH_CLAV, 68)
            if I_END <= b < II_END]
    fails = []
    if not any(v >= 64 for _b, v in lane):
        fails.append("no CC68 hammer-on engaged on the clavinet")
    if not any(v == 0 for _b, v in lane):
        fails.append("clavinet CC68 never releases")
    if len(lane) < 8:
        fails.append(f"only {len(lane)} CC68 events, want the slur to recur")
    return fails


def _o_wah(sc):
    """The muted-guitar wah: a CC74 sweep confined to the choruses."""
    lane = _cc_lane(sc, CH_MUTEGTR, 74)
    fails = []
    if len(lane) < 12:
        fails.append(f"wah CC74 lane has {len(lane)} events, want an LFO")
    vals = [v for _b, v in lane]
    if vals and max(vals) - min(vals) < 30:
        fails.append("wah CC74 barely moves (want an audible sweep)")
    stray = [b for b, _v in lane
             if not any(lo - 1e-6 <= b <= hi + 1e-6 for lo, hi in CHORUS_SPANS)]
    if stray:
        fails.append(f"wah sounds outside the choruses (e.g. beat "
                     f"{stray[0]:.1f})")
    return fails


def _o_aftertouch(sc):
    """The brass stabs rasp: channel aftertouch swells on the brass in II."""
    lane = [(b, v) for b, v in _aftertouch_lane(sc, CH_BRASS)
            if I_END <= b < II_END]
    fails = []
    if len(lane) < 8:
        fails.append(f"brass aftertouch has {len(lane)} events, want the rasp")
    if lane and max(v for _b, v in lane) < 60:
        fails.append("brass aftertouch never swells (rasp too weak)")
    return fails


def _o_portamento(sc):
    """The fretless glide: CC65/CC5 portamento engages and recentres (CC65
    back to 0) by the movement's end."""
    lane = _cc_lane(sc, CH_BASS, 65)
    fails = []
    if not any(v >= 64 for _b, v in lane):
        fails.append("fretless portamento (CC65) never engages")
    ii = [(b, v) for b, v in lane if I_END <= b < II_END]
    if ii and ii[-1][1] != 0:
        fails.append(f"portamento not recentred by movement end "
                     f"(last CC65={ii[-1][1]})")
    if not _cc_lane(sc, CH_BASS, 5):
        fails.append("no CC5 portamento-time set on the fretless")
    return fails


def _o_shore_pans(sc):
    """The narrowing strait: island channels left (44), mainland right (84) —
    a fourth narrower than track 1's tritone-wide field."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_PANFLUTE, CH_CHOIR, CH_PAD}
    mainland = {CH_STEEL, CH_CLAV, CH_BRASS, CH_HORN}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want "
                         f"{{{ISL_PAN}}}")
    for ch in sorted(mainland):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {MAIN_PAN}:
            fails.append(f"mainland ch{ch} pans {sorted(pans)}, want "
                         f"{{{MAIN_PAN}}}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls twice (track 2), on the island's E, the final
    note-ons — nothing sounds after the first toll but the second."""
    fails = []
    bells = _note_ons(sc, CH_BELLS)
    if len(bells) != material.TOLLS[NUMBER]:
        fails.append(f"{len(bells)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p, _v in bells:
        if p % 12 != ISLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want "
                         f"{ISLAND_TONIC_PC} (the island tonic E)")
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
        ("no_overlap", _o_no_overlap(sc)),
        ("end_degrees", _o_end_degrees(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("protagonist_bass", _o_protagonist_bass(sc)),
        ("doubled_thumb", _o_doubled_thumb(sc)),
        ("breath_herald", _o_herald(sc)),
        ("morse_wait", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("accelerando", _o_accelerando(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("cadence_law", _o_cadence(sc)),
        ("kit_swap", _o_kit_swap(sc)),
        ("hammer_on", _o_hammer_on(sc)),
        ("wah_lane", _o_wah(sc)),
        ("brass_aftertouch", _o_aftertouch(sc)),
        ("portamento", _o_portamento(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The accelerando/strut should read loud, the wreckage quiet, the return
# hollow.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    harbour = _rms_db(40.0, 72.0)       # movement I, the brush harbour
    peak = _rms_db(256.0, 288.0)        # movement II's climax (fast, full strut)
    wreck = _rms_db(330.0, 372.0)       # movement III, the wreckage
    return_iv = _rms_db(408.0, 448.0)   # movement IV, the hollow return

    # 1. The accelerando is audible: the strut climax is not quieter than the
    #    harbour it grew from (a generous ratio; a real strut is far louder).
    fails = []
    if peak - harbour < -2.0:
        fails.append(f"strut climax {peak:.1f} dB is quieter than the harbour "
                     f"{harbour:.1f} dB (the accelerando should build)")
    checks.append(("audio_accelerando_builds", fails))

    # 2. The wreckage is quieter than the strut's peak.
    fails = []
    if peak - wreck < 0.5:
        fails.append(f"wreckage {wreck:.1f} dB not >= 0.5 dB below the strut "
                     f"peak {peak:.1f} dB (the collapse should drop)")
    checks.append(("audio_wreckage_quieter", fails))

    # 3. The harbour's return is hollow: quieter than the strut peak.
    fails = []
    if peak - return_iv < 0.5:
        fails.append(f"the return {return_iv:.1f} dB not >= 0.5 dB below the "
                     f"strut peak {peak:.1f} dB (the reprise should be hollow)")
    checks.append(("audio_return_hollow", fails))
    return checks

