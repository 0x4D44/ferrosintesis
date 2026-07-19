"""movements/t05_low_water_crossing.py — track 5 of *The Causeway*.

LOW WATER CROSSING.  The crossing at dawn, and every promise the album has
withheld for twenty-one minutes, kept.  D minor turns to D major — the record's
only mode flip; the shores have converged to distance ZERO (both tonics D); and
for the first time the two themes are allowed to sound at once.  Four movements:

  I. First Light — D minor, the tide-breath still swelling around 84: a piano
     pump assembling, a warm pad and sealed choir under the last light; the two
     themes stated SEPARATELY one final time (the island in D minor, the
     mainland in a D-major inflection — same tonic at last, distance nil), never
     overlapping here.
  II. The Causeway — the key signature FLIPS to D major at the seam (the album's
     one mode flip) and the tempo FLATTENS to a dead-steady 100 (the water is
     out, the ground dry): a pan-flute breath heralds the 1985 pump, the
     protagonist bass calls HOOK5, a steel guitar jangles CC68 hammer-ons and
     the brass warms.
  III. Both Shores — the wow stack over the running pump: the island and the
     mainland themes SIMULTANEOUS in D, downbeat-consonant, and INVERTIBLE (one
     window the island rides above, a second the mainland does); the side-two
     MEDLEY (HOOKS 1-4 each restated); the choir opening toward "ah"; the
     tubular bells pealing HOME in Morse then holding the roots; an
     overdriven-lead solo on a twelve-semitone bend range; and a 32-bar
     crescendo of strictly rising bar-sums.
  IV. The Other Shore — a ritardando to 62, everything falling away: solo piano
     states THE FUSION PHRASE (the album's ONLY melodic tonic landing) into the
     IV-I plagal Picardy — the bass G falling to D with F-sharp in the chord and
     no C-natural — a long expression fade, and exactly five bells tolling D.

Every device the HLD marks verified is an oracle below, and all recurring data
is single-sourced from material.py (the two themes and the fusion phrase, HOOK5
and the medley hooks 1-4, the convergence pcs, the morse word HOME, the tide
breath, the shore pans, the vowel floor, the tolls, the plagal geometry).  The
strait has closed: island and mainland are both D, distance zero.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 5
TITLE = "Low Water Crossing"
FILE = "05 - Low Water Crossing.mid"
SEED = 202607185
COMMENT = (
    "Low Water Crossing - the crossing at dawn, every promise kept.  D minor "
    "turns to D major (the album's only mode flip) and the shores converge to "
    "distance zero.  First light: a piano pump assembling under the tide's last "
    "swell, the two themes stated apart one final time.  The causeway: the key "
    "flips to D major, the tempo flattens dead-steady to 100, a pan flute "
    "heralds the 1985 pump, the protagonist bass calls the pump-call hook, a "
    "steel guitar jangles and the brass warms.  Both shores: the island and "
    "mainland themes sounding together in D, downbeat-consonant and invertible, "
    "a medley of the album's four hooks over the pump, the choir opening to ah, "
    "the tubular bells pealing HOME then holding the roots, an overdriven lead "
    "on a twelve-semitone bend, and a 32-bar crescendo.  The other shore: a "
    "ritardando to 62, solo piano stating the fusion phrase - the record's only "
    "melodic tonic landing - into a IV-I plagal Picardy, a long fade, and five "
    "bells tolling D.")

# ---------------------------------------------------------------------------
# Channels.  The strait is at its narrowest: island pole at SHORE_PANS[5][0]=60,
# mainland pole at 68 (only eight apart).  Island weather (the island theme
# voice on strings, the choir, the pan flute, the warm pad, the vibraphone
# colour) sits left; the mainland band (the mainland theme on french horn, the
# steel guitar, the brass, the overdriven lead) sits right; the neutral spine
# (the pump piano, the protagonist bass, the kit, the bell buoy) holds 64.
# ---------------------------------------------------------------------------

CH_PIANO, CH_BASS, CH_ISLAND, CH_MAINLAND = 0, 1, 2, 3
CH_STEEL, CH_BRASS, CH_CHOIR, CH_PANFLUTE = 4, 5, 6, 7
CH_PAD, CH_DRUMS, CH_LEAD, CH_BELLS = 8, 9, 10, 11
CH_VIBES = 12

_MM = material.MODE_MINOR                   # aeolian - the island's D minor
_MJ = material.MODE_MAJOR                   # ionian - the mainland's / union D

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (60, 68)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 2, 2

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 160.0
HERALD_T0, HERALD_T1 = 160.0, 168.0         # >= 2 bars, pan flute alone
GROOVE_T0 = 168.0                           # the 1985 pump locks in
II_END = 288.0
IIIA_END = 352.0                            # the wow stack -> the crescendo
CRESC_T0, CRESC_T1 = 352.0, 480.0           # the 32-bar rising crescendo
III_END = 480.0
END = 592.0

# --- pinned geometry the oracles re-derive against material.py ---
# I: the two themes stated apart (island D minor, mainland D-major inflection).
ISLAND_I_T0 = 36.0
ISLAND_I_BASE = en.n("D4")                  # 62 - island tonic D (deg 1)
MAINLAND_I_T0 = 104.0
MAINLAND_I_BASE = en.n("D3")                # 50 - mainland tonic D (deg 1)

# III: the simultaneity - two overlapping windows, invertible.
OVERLAP1_T0 = 288.0                         # island ABOVE mainland
ISL1_BASE, MNL1_BASE = en.n("D4"), en.n("D3")     # 62 over 50
OVERLAP2_T0 = 300.0                         # mainland ABOVE island
ISL2_BASE, MNL2_BASE = en.n("D3"), en.n("D4")     # 50 under 62
OVERLAP_LEN = 8.0                           # one theme statement (8 beats)

# IV: the fusion phrase (the album's only tonic landing) and the plagal Picardy.
FUSION_T0 = 494.0
FUSION_BASE = en.n("D4")                    # 62 - the union tonic D
FUSION_STRETCH = 1.5
PLAGAL_DOWN = 512.0                         # the bass D lands here (IV-I)
PLAGAL_LO, PLAGAL_HI = 506.0, 522.0         # the final cadence window

# the pump call and the medley
BASS_HOOK_ROOT = en.n("D2")                 # 38 - HOOK5 (1-2-3-5) in the bass
CHORUS_SPANS = [(GROOVE_T0, II_END), (II_END, III_END)]   # the running pump
HOOK5_BASS_T0 = [168.0, 232.0, 296.0, 360.0]              # calls in the bass
# HOOKS 1..4 restated in the medley window (any channel/transposition).
MEDLEY = [(1, CH_VIBES, 322.0, en.n("D5")),
          (2, CH_STEEL, 326.0, en.n("D4")),
          (3, CH_VIBES, 332.0, en.n("A4")),
          (4, CH_LEAD, 336.0, en.n("D4"))]

HERALD_PITCH = en.n("A4")                   # 69 - the pump-call head, breathed
MORSE_T0 = 312.0
MORSE_PITCH = en.n("D5")                    # 74 - the bells' fixed HOME tap
BELLS_ROOT_T0 = 336.0                       # the bells hold the roots after HOME
TOLL_T0 = 566.0
TOLL_PITCH = en.n("D4")                     # 62 - pc 2 = the union tonic D
TOLL_SPACING = 3.0

# the overdriven-lead solo (RPN bend range 12, recentred by III_END)
SOLO_T0, SOLO_T1 = 356.0, 476.0
SOLO_BEND_RANGE = 12


# --- the tempo map: I breathes (the tide's last swell), II-III are the flat
#     still point (dead-steady 100, <= 1 bpm wiggle - the causeway is dry), IV
#     ritards to 62 as everything falls away. ---

def _flat(t0, t1, base, wiggle=0.4, step=8.0):
    """The flat still point: a near-metronomic map that only barely breathes
    (span <= 2*wiggle < 1 bpm) - NOT a single event (the water is out, but the
    map is still a map).  A gentle cosine so the causeway is dry, not frozen."""
    out = []
    b = t0
    i = 0
    while b < t1 - 1e-9:
        out.append((b, round(base + wiggle * math.cos(2 * math.pi * i / 8.0), 2)))
        b += step
        i += 1
    return out


def _ritard(t0, t1, bpm0, bpm1, step=8.0):
    """A monotonically falling tempo ramp - the final ritardando of movement
    IV, the tide going out under the fusion and the tolls."""
    out = []
    b = t0
    while b <= t1 + 1e-9:
        out.append((b, round(en.lerp(bpm0, bpm1, (b - t0) / (t1 - t0)), 2)))
        b += step
    return out


TEMPO_MAP = (
    material.tide_breath(84.0, 0.0, I_END, period=32.0, depth=4.0)
    + _flat(I_END, III_END, 100.0, wiggle=0.4, step=8.0)
    + _ritard(III_END, 584.0, 100.0, 62.0, step=8.0))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. First Light", 0.0, I_END),
               ("II. The Causeway", I_END, II_END),
               ("III. Both Shores", II_END, III_END),
               ("IV. The Other Shore", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1),                  # D minor: one flat, minor
             (I_END, 2, 0)],                # D major: two sharps - THE mode flip
    channels=[(CH_PIANO, "piano", 0, 100, 64, 40),
              (CH_BASS, "protagonist bass", 33, 100, 64, 28),
              (CH_ISLAND, "island strings", 48, 88, ISL_PAN, 44),
              (CH_MAINLAND, "french horn", 60, 88, MAIN_PAN, 46),
              (CH_STEEL, "steel guitar", 25, 86, MAIN_PAN, 38),
              (CH_BRASS, "brass section", 61, 90, MAIN_PAN, 40),
              (CH_CHOIR, "choir", 52, 80, ISL_PAN, 60),
              (CH_PANFLUTE, "pan flute", 75, 84, ISL_PAN, 50),
              (CH_PAD, "warm pad", 89, 74, ISL_PAN, 52),
              (CH_DRUMS, "kit", 0, 92, 64, 28),
              (CH_LEAD, "overdriven lead", 29, 84, MAIN_PAN, 42),
              (CH_BELLS, "tubular bells", 14, 90, 64, 50),
              (CH_VIBES, "vibraphone", 11, 82, ISL_PAN, 46)],
    extra_markers=[(HERALD_T0, "breath herald"), (GROOVE_T0, "the pump"),
                   (OVERLAP1_T0, "both shores"), (CRESC_T0, "the crossing"),
                   (FUSION_T0, "the fusion"), (TOLL_T0, "the tolls")],
)

PROGRAM_WHITELIST = {0, 33, 48, 60, 25, 61, 52, 75, 89, 29, 14, 11}
CENTERED_CHANNELS = {CH_PIANO, CH_BASS, CH_DRUMS, CH_BELLS}
NOTE_RANGES = {
    CH_PIANO: (31, 72), CH_BASS: (26, 52), CH_ISLAND: (48, 72),
    CH_MAINLAND: (48, 74), CH_STEEL: (48, 74), CH_BRASS: (48, 79),
    CH_CHOIR: (55, 79), CH_PANFLUTE: (60, 84), CH_PAD: (36, 74),
    CH_LEAD: (60, 84), CH_BELLS: (48, 76), CH_VIBES: (60, 84),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # only the lead bends; it recentres
DURATION_WINDOW = (379.0, 394.0)            # ~6:26 incl. the 2-beat end pad
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
    return sorted((b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6)


def _in_chorus(beat):
    return any(lo <= beat < hi for lo, hi in CHORUS_SPANS)


def _sounding(sc, ch, beat, eps=1e-6):
    """The pitch(es) whose [on, off) span covers `beat` on channel ch."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on <= beat + eps and off > beat + eps]


def _bar_sum(sc, lo, hi):
    """Sum of note-on velocities across all channels in [lo, hi) beats."""
    total = 0.0
    for ch in sc.events:
        for b, _p, v in _note_ons(sc, ch):
            if lo - 1e-6 <= b < hi:
                total += v
    return total


# ---------------------------------------------------------------------------
# Harmony.  D aeolian (the island's First Light) and D major (the causeway and
# the union).  The pump and the pad carry the harmony; the bass sings it.
# ---------------------------------------------------------------------------

# The island's low register for the warming bass (D aeolian).
BASS_MIN = [en.n(x) for x in
            ("D1", "E1", "F1", "G1", "A1", "Bb1", "C2", "D2", "E2", "F2",
             "G2", "A2", "Bb2", "C3", "D3")]
# The protagonist bass in D major (the pump), spanning >= 19 semitones.
BASS_MAJ = [en.n(x) for x in
            ("D1", "E1", "F#1", "G1", "A1", "B1", "C#2", "D2", "E2", "F#2",
             "G2", "A2", "B2", "C#3", "D3")]

# The First-Light pad cycle (D aeolian): i - bVI - bIII - iv, open voicings
# kept above D2 so the warm pad never rumbles the low end.
FIRST_PAD = [
    [en.n("D2"), en.n("A2"), en.n("D3")],       # Dm  (i)
    [en.n("Bb2"), en.n("F3"), en.n("Bb3")],     # Bb  (bVI)
    [en.n("F2"), en.n("C3"), en.n("F3")],       # F   (bIII)
    [en.n("G2"), en.n("D3"), en.n("G3")],       # Gm  (iv)
]
FIRST_CHOIR = [en.n("A4"), en.n("D4"), en.n("C4"), en.n("D4")]

# The causeway / union pad cycle (D major): I - IV - V - vi, warm triads.
CAUSE_PAD = [
    [en.n("D3"), en.n("A3"), en.n("F#4")],      # D   (I)
    [en.n("G3"), en.n("D4"), en.n("B4")],       # G   (IV)
    [en.n("A2"), en.n("E3"), en.n("C#4")],      # A   (V)
    [en.n("B2"), en.n("F#3"), en.n("D4")],      # Bm  (vi)
]
# The pump's per-bar root cycles (the octave-quaver left hand walks these).
PUMP_II = [en.n("D2"), en.n("G2"), en.n("A2"), en.n("D2")]      # I-IV-V-I
PUMP_IIIA = [en.n("D2")]                                        # tonic pedal
PUMP_CRESC = [en.n("D2"), en.n("B1"), en.n("G1"), en.n("A1")]   # I-vi-IV-V
# The pump right hand answers with the chord's upper triad (D major).
PUMP_TRIAD = {
    en.n("D2"): [en.n("D4"), en.n("F#4"), en.n("A4")],
    en.n("G2"): [en.n("D4"), en.n("G4"), en.n("B4")],
    en.n("G1"): [en.n("D4"), en.n("G4"), en.n("B4")],
    en.n("A2"): [en.n("C#4"), en.n("E4"), en.n("A4")],
    en.n("A1"): [en.n("C#4"), en.n("E4"), en.n("A4")],
    en.n("B1"): [en.n("D4"), en.n("F#4"), en.n("B4")],
}


def _bar_vel(beat, base, accent=10):
    """The pump's dynamic stress: on 1 and the and-of-2 (the 1985 accent)."""
    q = beat % 4.0
    if abs(q) < 1e-6:
        return base + accent
    if abs(q - 1.5) < 1e-6:
        return base + accent // 2
    return base


# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (the two themes, the fusion, HOOK5 and the
# medley hooks, morse, tolls, the herald and the doubled thumb) are jt=0 so
# every statement is findable and the pump locks hard; texture lanes jitter.
# ---------------------------------------------------------------------------

def _pad_cycle(sc, ch, t0, t1, cycle, span, vel, curve, vowel=None, jt=0):
    """Sustained voicings stepping through `cycle`, one chord every `span`
    beats, ending exactly at t1 so nothing rings past the movement seam."""
    b = t0
    i = 0
    while b < t1 - 1e-6:
        dur = min(span, t1 - b)
        for p in cycle[i % len(cycle)]:
            sc.note(ch, p, b, dur * 0.99, vel, jt=jt, jv=2)
        b += span
        i += 1
    en.expr_curve(sc, ch, curve, step=4.0)
    if vowel is not None:
        en.vowel_curve(sc, ch, vowel, step=4.0)


# -- I. First Light ---------------------------------------------------------

def _first_piano(sc):
    """The pump ASSEMBLING: sparse right-hand D-minor chord fragments high
    (>= D4) so it never shadows the warming bass at the octave - the pump is
    not yet the pump, only its shape gathering in the light."""
    frags = [
        (8.0, [en.n("D4"), en.n("F4"), en.n("A4")]),
        (24.0, [en.n("D4"), en.n("F4"), en.n("A4")]),
        (52.0, [en.n("C4"), en.n("F4"), en.n("A4")]),
        (68.0, [en.n("Bb3"), en.n("D4"), en.n("F4")]),
        (84.0, [en.n("D4"), en.n("G4"), en.n("Bb4")]),
        (120.0, [en.n("D4"), en.n("F4"), en.n("A4")]),
        (136.0, [en.n("A3"), en.n("D4"), en.n("F4")]),
        (150.0, [en.n("D4"), en.n("F4"), en.n("A4")]),
    ]
    for t0, chord in frags:
        for k, off in enumerate((0.0, 1.5, 2.5)):     # a preview of the pump feel
            for p in chord:
                sc.note(CH_PIANO, p, t0 + off, 1.2, 52 - k * 3, jt=2, jv=3)
        en.sustain(sc, CH_PIANO, t0, t0 + 3.8)


def _first_bass(sc):
    """The bass warming low, sparse - a slow rise through D aeolian, OUTSIDE
    the choruses so its notes are never octave-doubled (the thickening is a
    chorus event).  Stays well below the high piano fragments."""
    steps = [(2.0, 0), (10.0, 2), (18.0, 4), (26.0, 3), (40.0, 5), (56.0, 4),
             (72.0, 6), (88.0, 5), (104.0, 7), (128.0, 4), (144.0, 2)]
    for b, idx in steps:
        sc.note(CH_BASS, BASS_MIN[idx], b, 3.4, 60 - (idx % 2) * 4, jt=0, jv=3)


def _b_first_light(sc):
    """I. First Light [0, 160) - the tide's last swell over D minor: a pad and
    a sealed choir under the assembling pump, the two themes stated APART one
    final time (the island in D minor, the mainland in a D-major inflection),
    never overlapping."""
    _pad_cycle(sc, CH_PAD, 0.0, I_END, FIRST_PAD, 8.0, 44,
               [(0.0, 34), (80.0, 56), (I_END - 1, 40)])
    _pad_cycle(sc, CH_CHOIR, 0.0, I_END, [[p] for p in FIRST_CHOIR], 8.0, 42,
               [(0.0, 36), (80.0, 58), (I_END - 1, 38)],
               vowel=[(0.0, 8), (96.0, 28), (I_END - 1, 30)], jt=1)
    en.cc_curve(sc, CH_CHOIR, 1, [(0.0, 0), (I_END - 1, 18)], step=8.0)
    _first_piano(sc)
    _first_bass(sc)
    # THE ISLAND THEME, once, in D minor (base D4) - the far incantation, still
    # hanging on degree 2.  The strings sound nothing else across the statement.
    material.play_island(sc, CH_ISLAND, ISLAND_I_T0, ISLAND_I_BASE,
                         vel=74, vel_end=64)
    en.expr_curve(sc, CH_ISLAND,
                  [(ISLAND_I_T0, 42), (ISLAND_I_T0 + 4, 84),
                   (ISLAND_I_T0 + 8, 40)], step=0.5)
    en.cc_curve(sc, CH_ISLAND, 1,
                [(ISLAND_I_T0, 4), (ISLAND_I_T0 + 8, 26)], step=1.0)
    # THE MAINLAND THEME, once, in a D-major inflection (base D3) - same tonic
    # at last, distance nil - on the french horn, no island sounding against it.
    material.play_mainland(sc, CH_MAINLAND, MAINLAND_I_T0, MAINLAND_I_BASE,
                           vel=72, vel_end=62)
    en.expr_curve(sc, CH_MAINLAND,
                  [(MAINLAND_I_T0, 40), (MAINLAND_I_T0 + 5, 86),
                   (MAINLAND_I_T0 + 8, 38)], step=0.5)
    en.cc_curve(sc, CH_MAINLAND, 1,
                [(MAINLAND_I_T0, 0), (MAINLAND_I_T0 + 8, 24)], step=1.0)


# -- The pump, the kit, and the bass walk (shared by II and III) -------------

def _pump(sc, t0, t1, roots, vel_base, rh="triad", vel_top=None):
    """The 1985 engine: the piano left hand plays octave quavers on the bar
    root (accents on 1 and the and-of-2), a sustain pedal per bar, and the
    right hand answers off-beat.  `rh` is 'triad' (the full D-major answer) or
    'fifth' (an open D-A answer, pc-neutral for the theme-overlap window).  If
    `vel_top` is set the whole pump swells from vel_base to vel_top across the
    span - the dominant rising element of the crescendo."""
    bar_i = 0
    bar = t0
    while bar < t1 - 1e-6:
        vb = (vel_base if vel_top is None
              else int(en.lerp(vel_base, vel_top, (bar - t0) / (t1 - t0))))
        root = roots[bar_i % len(roots)]
        for q in range(8):
            b = bar + q * 0.5
            v = _bar_vel(b, vb)
            sc.note(CH_PIANO, root, b, 0.46, v, jt=0, jv=2)
            sc.note(CH_PIANO, root + 12, b, 0.46, v - 6, jt=0, jv=2)
        en.sustain(sc, CH_PIANO, bar, bar + 3.9)
        if rh == "triad":
            answer = PUMP_TRIAD.get(root, [root + 12, root + 16, root + 19])
        else:
            answer = [root + 19, root + 24]           # open fifth ABOVE the LH
                                                       # octave (no duplication)
        for off in (1.5, 3.5):
            for p in answer:
                sc.note(CH_PIANO, p, bar + off, 0.85, vb - 6, jt=0, jv=2)
        bar += 4.0
        bar_i += 1


def _kit(sc, t0, t1, g_fn):
    """A driving backbeat whose intensity g in [0,1] thickens the hats to
    sixteenths and lifts the velocities - the engine of the causeway and the
    crescendo.  jt=0 so the bar-sums the crescendo oracle reads are clean."""
    bar = t0
    while bar < t1 - 1e-6:
        g = max(0.0, min(1.0, g_fn(bar)))
        kv = int(84 + 30 * g)
        sc.hit(36, bar, kv, jt=0)
        sc.hit(36, bar + 1.5, kv - 12, jt=0)              # the and-of-2 push
        sc.hit(38, bar + 1.0, int(78 + 24 * g), jt=0)
        sc.hit(38, bar + 3.0, int(82 + 24 * g), jt=0)
        steps = 16 if g > 0.5 else 8
        for q in range(steps):
            b = bar + q * (0.25 if steps == 16 else 0.5)
            drum = 46 if (q % (steps // 4) == 0) else 42
            v = int(34 + 18 * g + (10 if drum == 46 else 0))
            sc.hit(drum, b, v, jt=0)
        if g > 0.7 and int((bar - t0) // 4) % 4 == 3:
            sc.hit(49, bar + 3.5, int(70 + 20 * g), jt=0)     # a crash lift
        bar += 4.0


def _walk(sc, ch, t0, start_idx, deltas, dur, vel_base, scale=BASS_MAJ):
    """Step a bass line through `scale` by mostly +-1/+-2 scale steps so it
    stays stepwise; one note every `dur` beats.  Returns the final index."""
    idx = start_idx
    beat = t0
    for d in deltas:
        idx = max(0, min(len(scale) - 1, idx + d))
        sc.note(ch, scale[idx], beat, dur * 0.9, _bar_vel(beat, vel_base),
                jt=0, jv=3)
        beat += dur
    return idx


def _herald(sc):
    """Enigma's inhale before the pump: HOOK5's first three notes (the pump
    call's head, deltas 0, 2, 4) on the pan flute, alone, over a strictly
    rising CC11 swell - two bars.  The notes are laid contiguous so the whole
    window is the flute's and no global gap opens."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]     # [0, 2, 4]
    starts = [HERALD_T0, HERALD_T0 + 2.5, HERALD_T0 + 5.0]
    durs = [2.5, 2.5, 3.0]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, HERALD_PITCH + s, st, du, 56, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 16), (HERALD_T1, 104)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 30)],
                step=0.5)


# The steel guitar's D-major jangle figure (the CC68 hammer-on strum).
STEEL_FIG = [
    [en.n("D4"), en.n("F#4"), en.n("A4")],       # D
    [en.n("G3"), en.n("B3"), en.n("D4")],        # G
    [en.n("A3"), en.n("C#4"), en.n("E4")],       # A
    [en.n("D4"), en.n("F#4"), en.n("A4")],       # D
]

# Brass warming triads (D major) and the crescendo stab voicings.
BRASS_WARM = [
    [en.n("D3"), en.n("F#3"), en.n("A3")],       # D
    [en.n("G3"), en.n("B3"), en.n("D4")],        # G
    [en.n("A3"), en.n("C#4"), en.n("E4")],       # A
    [en.n("D3"), en.n("F#3"), en.n("A3")],       # D
]
BRASS_STAB = [
    [en.n("D4"), en.n("F#4"), en.n("A4")],       # D
    [en.n("B3"), en.n("D4"), en.n("F#4")],       # Bm
    [en.n("G3"), en.n("B3"), en.n("D4")],        # G
    [en.n("A3"), en.n("C#4"), en.n("E4")],       # A
]
CAUSE_CHOIR = [en.n("A4"), en.n("B4"), en.n("C#5"), en.n("A4")]


# -- II. The Causeway -------------------------------------------------------

def _double_thumb(sc, lo, hi):
    """The chorus thickens: every bass note-on inside [lo, hi) and inside the
    running pump shadowed at the octave on the piano - the doubled thumb.  Where
    the pump's own left hand already sounds the octave (the bass sits on the bar
    root) that note IS the shadow, so no duplicate is emitted (a same-pitch
    same-tick collision).  Movement I and IV bass (outside the pump) are never
    doubled, so the thickening reads as a pump event.  Must run AFTER every
    pump so it can see the octaves already there."""
    piano = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_PIANO)]

    def covered(btick, bp):
        return any(pp == bp + 12 and abs(pt - btick) <= 10 for pt, pp in piano)

    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if lo - 1e-6 <= beat < hi and _in_chorus(beat):
            if not covered(_tick(beat), pitch):
                sc.note(CH_PIANO, pitch + 12, beat, 0.45, 70, jt=0, jv=2)


def _bass_causeway(sc):
    """The protagonist bass across the pump: the pump call HOOK5 at two chorus
    heads, stepwise-singing walks between that visit the low D1 and climb to
    D3 (the McCartney range and step), all inside the running pump."""
    material.play_hook(sc, CH_BASS, HOOK5_BASS_T0[0], BASS_HOOK_ROOT, NUMBER,
                       vel=90, vel_end=96, gate=0.9)
    _walk(sc, CH_BASS, 172.0, 11, [-1] * 11 + [1] * 13 + [-1] * 6, 2.0, 78)
    material.play_hook(sc, CH_BASS, HOOK5_BASS_T0[1], BASS_HOOK_ROOT, NUMBER,
                       vel=92, vel_end=98, gate=0.9)
    _walk(sc, CH_BASS, 236.0, 7, [1] * 7 + [-1] * 13 + [1] * 6, 2.0, 78)


def _steel_jangle(sc, t0, t1):
    """The steel guitar's causeway jangle: a rising D-major arpeggio per bar
    with a CC68 hammer-on into the climb - the McCartney chime, the advanced
    controller showcase's slur lane."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        fig = STEEL_FIG[ci % len(STEEL_FIG)]
        seq = fig + fig[-2::-1]                        # up then down (5 notes)
        sc.cc(CH_STEEL, 68, 127, bar + 0.9)            # hammer-on into the climb
        for q, p in enumerate(seq):
            sc.note(CH_STEEL, p, bar + q * 0.5, 0.46,
                    60 + (10 if q == 0 else 0), jt=0, jv=3)   # jt=0: dead-steady,
        sc.cc(CH_STEEL, 68, 0, bar + 3.0)              # never jitters the herald
        bar += 4.0
        ci += 1


def _brass_warm(sc, t0, t1):
    """The brass warming: a held D-major triad per bar swelling on CC11 - the
    band coming up to temperature under the causeway pump."""
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        for p in BRASS_WARM[ci % len(BRASS_WARM)]:
            sc.note(CH_BRASS, p, bar, 3.7, 54, jt=0, jv=2)
        bar += 4.0
        ci += 1
    en.expr_curve(sc, CH_BRASS,
                  [(t0, 28), ((t0 + t1) / 2, 62), (t1 - 1, 46)], step=4.0)
    en.cc_curve(sc, CH_BRASS, 1, [(t0, 0), (t1 - 1, 20)], step=8.0)


def _b_causeway(sc):
    """II. The Causeway [160, 288) - the key flips to D major and the tempo
    flattens dead-steady to 100: the pan-flute breath herald, then the 1985
    pump locks in with the protagonist bass calling HOOK5, the steel guitar
    jangling CC68 hammer-ons, the brass warming, and the doubled thumb."""
    _herald(sc)
    _pad_cycle(sc, CH_PAD, GROOVE_T0, II_END, CAUSE_PAD, 8.0, 44,
               [(GROOVE_T0, 38), (228.0, 60), (II_END - 1, 48)])
    _pad_cycle(sc, CH_CHOIR, GROOVE_T0, II_END, [[p] for p in CAUSE_CHOIR],
               8.0, 42, [(GROOVE_T0, 38), (228.0, 58), (II_END - 1, 44)],
               vowel=[(GROOVE_T0, 24), (II_END - 1, 34)], jt=0)
    en.cc_curve(sc, CH_CHOIR, 1, [(GROOVE_T0, 0), (II_END - 1, 22)], step=8.0)
    _pump(sc, GROOVE_T0, II_END, PUMP_II, 66, rh="triad")
    _kit(sc, GROOVE_T0, II_END,
         lambda b: 0.28 + 0.34 * (b - GROOVE_T0) / (II_END - GROOVE_T0))
    _bass_causeway(sc)
    _double_thumb(sc, I_END, II_END)
    _steel_jangle(sc, GROOVE_T0, II_END)
    _brass_warm(sc, GROOVE_T0, II_END)


# -- III. Both Shores -------------------------------------------------------

def _themes_together(sc):
    """THE SIMULTANEITY, at last: the island and the mainland themes sounding
    TOGETHER in D, downbeat-consonant, and INVERTIBLE - one window the island
    rides above (base D4 over D3), a second the mainland does (base D4 over
    D3).  Each channel is clean across its statement so both are findable."""
    material.play_island(sc, CH_ISLAND, OVERLAP1_T0, ISL1_BASE,
                         vel=82, vel_end=74)
    material.play_mainland(sc, CH_MAINLAND, OVERLAP1_T0, MNL1_BASE,
                           vel=80, vel_end=72)
    material.play_island(sc, CH_ISLAND, OVERLAP2_T0, ISL2_BASE,
                         vel=80, vel_end=72)
    material.play_mainland(sc, CH_MAINLAND, OVERLAP2_T0, MNL2_BASE,
                           vel=82, vel_end=74)
    for t0 in (OVERLAP1_T0, OVERLAP2_T0):
        en.expr_curve(sc, CH_ISLAND,
                      [(t0, 46), (t0 + 4, 88), (t0 + 8, 44)], step=0.5)
        en.expr_curve(sc, CH_MAINLAND,
                      [(t0, 44), (t0 + 4, 88), (t0 + 8, 42)], step=0.5)


def _medley(sc):
    """THE MEDLEY - the side-two payoff: HOOKS 1-4 each restated once over the
    running pump (any channel/transposition), each on a clean window so the
    searcher finds every one."""
    for n, ch, t0, fp in MEDLEY:
        material.play_hook(sc, ch, t0, fp, n, vel=84, vel_end=88, gate=0.92)
    sc.cc(CH_STEEL, 68, 127, MEDLEY[1][2] + 0.4)      # a jangle under HOOK2
    sc.cc(CH_STEEL, 68, 0, MEDLEY[1][2] + 3.0)
    en.echo_throw(sc, CH_VIBES, MEDLEY[0][2] + 1.8)   # an Enigma throw off HOOK1


def _bells_home(sc):
    """The bell buoy peals HOME in Morse (MORSE_PROGRAMS[5] = 14, tubular
    bells), then holds the roots (D) under the crescendo, swelling toward the
    climax - the letters arrived, the buoy ringing the harbour."""
    material.play_morse(sc, CH_BELLS, MORSE_T0, NUMBER, MORSE_PITCH)
    b = BELLS_ROOT_T0
    while b < III_END - 8.0 + 1e-6:
        g = (b - BELLS_ROOT_T0) / (III_END - BELLS_ROOT_T0)
        for p in (en.n("D3"), en.n("D4")):
            sc.note(CH_BELLS, p, b, 7.5, int(58 + 28 * g), jt=0, jv=2)
        b += 8.0


def _brass_cresc(sc, t0, t1):
    """The brass through the crescendo: rhythmic D-major stabs that thicken
    with the build, and the pump call HOOK5 twice on the horns (the album's
    hook lifted into the finale)."""
    hook_bars = {400.0, 448.0}
    bar = t0
    ci = 0
    while bar < t1 - 1e-6:
        if bar in hook_bars:
            material.play_hook(sc, CH_BRASS, bar, en.n("D4"), NUMBER,
                               vel=100, vel_end=108, gate=0.9)
        else:
            g = (bar - t0) / (t1 - t0)
            chord = BRASS_STAB[ci % len(BRASS_STAB)]
            offs = ([(0.0, 0.7), (2.0, 0.7)] if g < 0.5
                    else [(0.0, 0.5), (1.5, 0.4), (2.5, 0.5), (3.5, 0.4)])
            for st, du in offs:
                for p in chord:
                    sc.note(CH_BRASS, p, bar + st, du * 0.9,
                            int(84 + 24 * g), jt=0, jv=2)
        bar += 4.0
        ci += 1


def _lead_solo(sc):
    """The overdriven lead over the crescendo: a soaring D-major solo on a
    TWELVE-semitone bend range (RPN 0) with true wide bends - a fifth scoop, a
    whole-step cry, and a full octave bend up to the climactic A - every bend
    recentred before the movement seam."""
    en.bend_range(sc, CH_LEAD, SOLO_BEND_RANGE, SOLO_T0 - 1.0)
    notes = [
        (356.0, en.n("D4"), 2.0, 86), (358.5, en.n("F#4"), 1.5, 88),
        (360.5, en.n("A4"), 3.0, 92), (366.0, en.n("A4"), 1.0, 90),
        (367.5, en.n("B4"), 1.0, 92), (369.0, en.n("D5"), 3.0, 96),
        (376.0, en.n("A4"), 2.0, 90), (380.0, en.n("D5"), 3.0, 98),
        (392.0, en.n("E5"), 2.0, 100), (396.0, en.n("D5"), 2.0, 98),
        (408.0, en.n("F#5"), 3.0, 104), (416.0, en.n("A4"), 2.0, 98),
        (420.0, en.n("B4"), 2.0, 100), (424.0, en.n("D5"), 4.0, 104),
        (440.0, en.n("A5"), 3.0, 110), (448.0, en.n("F#5"), 2.0, 108),
        (456.0, en.n("D5"), 2.0, 106), (464.0, en.n("A5"), 6.0, 114),
    ]
    for on, p, du, v in notes:
        sc.note(CH_LEAD, p, on, du, v, jt=2, jv=3)
    en.expr_curve(sc, CH_LEAD,
                  [(SOLO_T0, 60), (470.0, 116), (SOLO_T1 - 1, 88)], step=1.0)
    en.bend_ramp(sc, CH_LEAD, 360.2, 361.0, -1.17, 0.0, steps=8)   # +fifth scoop
    en.bend_ramp(sc, CH_LEAD, 381.0, 383.5, 0.0, 0.33, steps=10)   # +2 cry
    en.bend_ramp(sc, CH_LEAD, 383.5, 384.0, 0.33, 0.0, steps=4)
    en.bend_ramp(sc, CH_LEAD, 464.0, 467.0, 0.0, 2.0, steps=18)    # +octave (12)
    en.bend_ramp(sc, CH_LEAD, 467.0, 470.0, 2.0, 0.0, steps=18)    # release
    sc.bend(CH_LEAD, SOLO_T1 - 0.5, 0.0)                           # recentre


def _choir_open(sc, t0, t1):
    """The winter's mouth opens toward 'ah': sustained D-major tops under a
    monotone vowel RISE (CC70) that will reach the T5 floor by the fusion -
    the choir the whole album has been sealing."""
    tops = [en.n("A4"), en.n("D5"), en.n("F#5"), en.n("A4")]
    b = t0
    i = 0
    while b < t1 - 1e-6:
        dur = min(16.0, t1 - b)
        sc.note(CH_CHOIR, tops[i % len(tops)], b, dur * 0.99, 50, jt=1, jv=2)
        b += 16.0
        i += 1
    en.vowel_curve(sc, CH_CHOIR, [(t0, 35), (t1 - 1, 75)], step=4.0)
    en.expr_curve(sc, CH_CHOIR,
                  [(t0, 44), (440.0, 74), (t1 - 1, 58)], step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, [(t0, 12), (t1 - 1, 34)], step=8.0)


def _bass_both_shores(sc):
    """The protagonist bass through Both Shores: the pump call under the wow
    stack, a stepwise walk beneath the themes, then the call again and a
    driving quarter-note walk that climbs into the crescendo's climax."""
    material.play_hook(sc, CH_BASS, HOOK5_BASS_T0[2], BASS_HOOK_ROOT, NUMBER,
                       vel=92, vel_end=98, gate=0.9)
    _walk(sc, CH_BASS, 300.0, 11, [-1] * 11 + [1] * 13 + [-1] * 2, 2.0, 76)
    material.play_hook(sc, CH_BASS, HOOK5_BASS_T0[3], BASS_HOOK_ROOT, NUMBER,
                       vel=96, vel_end=104, gate=0.9)
    # driving quarter-note walks (a pumping, stepwise finale bass) - the
    # velocity climbs 82 -> 92 -> 100 through the crescendo
    _walk(sc, CH_BASS, 364.0, 7, [1, 1, 1, 1, -1, -1, -1, -1] * 5, 1.0, 82)
    _walk(sc, CH_BASS, 404.0, 7, [1, 1, 1, -1, -1, -1] * 6, 1.0, 92)
    _walk(sc, CH_BASS, 440.0, 7, [1, 1, 1, 1, -1, -1, -1, -1] * 5, 1.0, 100)


def _b_both_shores(sc):
    """III. Both Shores [288, 480) - the wow stack over the running pump: the
    two themes simultaneous and invertible, the medley of hooks 1-4, the choir
    opening, the bells pealing HOME then holding the roots, the overdriven lead
    solo, and a 32-bar crescendo driving to the crossing's climax."""
    # both pumps first, so the doubled thumb (last) sees every octave already
    # in place and never emits a colliding duplicate.
    _pump(sc, OVERLAP1_T0, IIIA_END, PUMP_IIIA, 56, rh="fifth")     # III-a pedal
    _pump(sc, CRESC_T0, CRESC_T1, PUMP_CRESC, 48, rh="triad",       # III-b swell
          vel_top=96)
    # III-a: the delicate wow stack over the tonic-pedal pump
    _pad_cycle(sc, CH_PAD, II_END, IIIA_END,
               [[en.n("D3"), en.n("A3"), en.n("D4")]], 16.0, 40,
               [(II_END, 38), (320.0, 52), (IIIA_END - 1, 44)])
    _choir_open(sc, II_END, III_END)
    _themes_together(sc)
    _medley(sc)
    _bells_home(sc)
    # III-b: the 32-bar crescendo texture
    _pad_cycle(sc, CH_PAD, CRESC_T0, III_END, CAUSE_PAD, 8.0, 44,
               [(CRESC_T0, 44), (440.0, 66), (III_END - 1, 54)])
    _kit(sc, CRESC_T0, CRESC_T1,
         lambda b: (b - CRESC_T0) / (CRESC_T1 - CRESC_T0))
    _brass_cresc(sc, CRESC_T0, CRESC_T1)
    _lead_solo(sc)
    # the bass and its doubled thumb LAST (the thumb reads all the pump octaves)
    _bass_both_shores(sc)
    _double_thumb(sc, II_END, III_END)


# -- IV. The Other Shore ----------------------------------------------------

def _b_other_shore(sc):
    """IV. The Other Shore [480, 592) - the ritardando to 62, everything
    falling away: a D-major bed decrescendos, solo piano states THE FUSION
    PHRASE (the album's only melodic tonic landing), the IV-I plagal Picardy
    lands (bass G to D, F-sharp present, no C-natural), a long expression
    fade, and exactly five bells toll D."""
    # the falling bed: a warm pad and the choir reaching 'ah', decrescendoing
    # from the crescendo's peak; onsets all before the first toll so nothing
    # new sounds after the buoy begins.
    for t0, dur, chord in [
            (480.0, 14.0, [en.n("D3"), en.n("A3"), en.n("D4"), en.n("F#4")]),
            (494.0, 18.0, [en.n("D3"), en.n("A3"), en.n("D4")]),
            (512.0, 54.0, [en.n("D3"), en.n("F#3"), en.n("A3"), en.n("D4")])]:
        for p in chord:
            sc.note(CH_PAD, p, t0, dur * 0.99, 46, jt=0, jv=2)
    en.expr_curve(sc, CH_PAD,
                  [(480.0, 70), (500.0, 48), (540.0, 30), (564.0, 14)],
                  step=4.0)
    # the choir keeps opening to the T5 vowel floor while the volume fades
    for t0, dur, p in [(480.0, 16.0, en.n("A4")), (496.0, 20.0, en.n("D5")),
                       (516.0, 48.0, en.n("F#5"))]:
        sc.note(CH_CHOIR, p, t0, dur * 0.99, 48, jt=1, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(480.0, 75), (540.0, 90)], step=4.0)
    en.expr_curve(sc, CH_CHOIR,
                  [(480.0, 66), (508.0, 44), (564.0, 16)], step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, [(480.0, 34), (564.0, 8)], step=8.0)
    # a last low island string, falling away
    sc.note(CH_ISLAND, en.n("D4"), 480.0, 10.0, 52, jt=0, jv=2)
    en.expr_curve(sc, CH_ISLAND, [(480.0, 60), (490.0, 20)], step=1.0)
    # THE FUSION PHRASE - solo piano, the album's ONLY melodic tonic landing.
    # The piano sounds NOTHING else across the statement so the run is clean.
    material.play_fusion(sc, CH_PIANO, FUSION_T0, FUSION_BASE,
                         stretch=FUSION_STRETCH, vel=72, vel_end=64)
    en.sustain(sc, CH_PIANO, FUSION_T0, FUSION_T0 + 8.0 * FUSION_STRETCH)
    # THE IV-I PLAGAL PICARDY: the bass G falls to D, F-sharp in the chord,
    # no C-natural in the final window - the album's one authentic arrival.
    sc.note(CH_BASS, en.n("G1"), PLAGAL_DOWN - 4.0, 2.0, 70, jt=0, jv=2)  # IV
    sc.note(CH_BASS, en.n("G1"), PLAGAL_DOWN - 2.0, 2.0, 68, jt=0, jv=2)
    sc.note(CH_BASS, en.n("D1"), PLAGAL_DOWN, 6.0, 76, jt=0, jv=2)        # I
    for p in (en.n("D3"), en.n("F#3"), en.n("A3")):                       # the Picardy
        sc.note(CH_STEEL, p, PLAGAL_DOWN, 5.5, 54, jt=0, jv=2)
    en.expr_curve(sc, CH_STEEL, [(PLAGAL_DOWN, 60), (PLAGAL_DOWN + 5, 24)],
                  step=1.0)
    # the bell buoy: exactly five tolls on D (the union tonic), the final
    # note-ons - nothing sounds after the first of them but the remaining four.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=TOLL_SPACING, vel=80, dur=3.5)


BUILDERS = [_b_first_light, _b_causeway, _b_both_shores, _b_other_shore]


# ---------------------------------------------------------------------------
# Oracles - every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """The shores have closed to distance ZERO: the island states three times
    and the mainland three times, every statement implying the tonic D."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 3:
        fails.append(f"{len(isl)} island statements, want 3 (I + III x2)")
    for ch, start, _end, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {ISLAND_TONIC_PC} (D)")
    if len(mnl) != 3:
        fails.append(f"{len(mnl)} mainland statements, want 3 (I + III x2)")
    for ch, start, _end, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {MAINLAND_TONIC_PC} (D)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 0:
            fails.append(f"shore distance {dist}, want 0 (the shores have met)")
    return fails


def _o_simultaneity(sc):
    """THE LIFTING OF THE BAN: the two themes sound TOGETHER in movement III
    (>= 2 overlapping windows), each downbeat-consonant - and are stated APART
    in movement I (the last separate readings, no overlap there)."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    pairs = material.overlapping_pairs(isl, mnl)
    if len(pairs) < 2:
        fails.append(f"{len(pairs)} island/mainland overlaps, want >= 2 "
                     f"(the simultaneity, at last)")
    for a, b in pairs:
        if not (II_END <= a[1] < III_END and II_END <= b[1] < III_END):
            fails.append(f"an overlap sits outside movement III "
                         f"(island {a[1]:.1f}, mainland {b[1]:.1f})")
        for db in (a[1], a[1] + 4.0):
            for ip in _sounding(sc, CH_ISLAND, db):
                for mp in _sounding(sc, CH_MAINLAND, db):
                    if abs(ip - mp) % 12 not in _CONSONANT:
                        fails.append(f"downbeat {db:.1f}: island {ip} vs "
                                     f"mainland {mp} is dissonant")
    i_isl = [s for s in isl if s[1] < I_END]
    i_mnl = [s for s in mnl if s[1] < I_END]
    if material.overlapping_pairs(i_isl, i_mnl):
        fails.append("the movement-I statements overlap (they must be apart)")
    return fails


def _o_invertibility(sc):
    """INVERTIBLE COUNTERPOINT: in the first overlap the island rides ABOVE the
    mainland; in the second the mainland rides above the island - both windows
    verified by mean pitch."""
    fails = []

    def _mean(ch, t0):
        ps = [p for _b, p, _v in
              _onsets_in(sc, ch, t0 - 0.05, t0 + OVERLAP_LEN + 0.05)]
        return sum(ps) / len(ps) if ps else None

    im1, mm1 = _mean(CH_ISLAND, OVERLAP1_T0), _mean(CH_MAINLAND, OVERLAP1_T0)
    im2, mm2 = _mean(CH_ISLAND, OVERLAP2_T0), _mean(CH_MAINLAND, OVERLAP2_T0)
    if im1 is None or mm1 is None or not im1 > mm1:
        fails.append(f"overlap 1: island mean {im1} not above mainland {mm1}")
    if im2 is None or mm2 is None or not mm2 > im2:
        fails.append(f"overlap 2: mainland mean {mm2} not above island {im2}")
    return fails


def _o_fusion(sc):
    """THE FUSION PHRASE - the album's ONE melodic tonic landing: exactly one
    fusion statement, on the solo piano in movement IV, implying the tonic D
    (and by the theme oracles it is the only theme-family line to end there)."""
    fails = []
    fus = material.theme_statements(sc, "fusion")
    if len(fus) != 1:
        fails.append(f"{len(fus)} fusion statements, want exactly 1 (the "
                     f"album's only melodic tonic landing)")
    for ch, start, _end, first in fus:
        if ch != CH_PIANO:
            fails.append(f"fusion on ch{ch}, want the solo piano ({CH_PIANO})")
        if not III_END <= start < END:
            fails.append(f"fusion at beat {start:.1f} not in movement IV")
        if first % 12 != MAINLAND_TONIC_PC:
            fails.append(f"fusion base pc {first % 12}, want "
                         f"{MAINLAND_TONIC_PC} (D)")
    return fails


def _o_hook_density(sc):
    """The pump-call earworm: HOOK5 stated >= 6 times across the track."""
    hits = 0
    for ch in sc.events:
        hits += len(material.find_statements(material.note_ons(sc, ch),
                                             material.HOOKS[NUMBER]))
    if hits < 6:
        return [f"HOOK5 found {hits} times, want >= 6"]
    return []


def _o_medley(sc):
    """THE MEDLEY - the side-two payoff: hooks 1-4 each restated at least once
    inside movement III (any channel/transposition), over the running pump."""
    fails = []
    for n in (1, 2, 3, 4):
        hits = [s for ch in sc.events
                for s in material.find_statements(material.note_ons(sc, ch),
                                                  material.HOOKS[n])
                if II_END <= s[0] < III_END]
        if not hits:
            fails.append(f"HOOK{n} not restated in the medley (movement III)")
    return fails


def _o_protagonist_bass(sc):
    """The McCartney bass: stepwise-dominant, wide-ranging, and calling HOOK5
    in the bass inside the running pump."""
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
    in_chorus = [h for h in bass_hooks if _in_chorus(h[0])]
    if len(in_chorus) < 2:
        fails.append(f"HOOK5 stated {len(in_chorus)} times in the bass inside "
                     f"the choruses, want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The pump thickens: every bass note-on inside the running pump shadowed
    at the octave on the piano (coverage >= 0.80), and not outside (< 0.30)."""
    fails = []
    piano = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_PIANO)]

    def shadowed(btick, bp):
        return any(pp == bp + 12 and abs(pt - btick) <= 10 for pt, pp in piano)

    inside, outside = [], []
    for b, p, _v in _note_ons(sc, CH_BASS):
        (inside if _in_chorus(b) else outside).append((_tick(b), p))
    cov_in = (sum(1 for bt, bp in inside if shadowed(bt, bp)) / len(inside)
              if inside else 0.0)
    cov_out = (sum(1 for bt, bp in outside if shadowed(bt, bp)) / len(outside)
               if outside else 0.0)
    if cov_in < 0.80:
        fails.append(f"doubled-thumb coverage {cov_in:.2f} inside the pump "
                     f"< 0.80")
    if cov_out >= 0.30:
        fails.append(f"bass doubled {cov_out:.2f} OUTSIDE the pump >= 0.30")
    return fails


def _o_herald(sc):
    """The breath herald: >= 2 bars where only the pan flute sounds, playing
    the pump call's first three notes over a strictly-rising CC11 swell."""
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
    """The tide-word HOME, pealed on the tubular bells (MORSE_PROGRAMS[5] = 14)
    in standard Morse timing re-derived from material - before the bells take
    up the roots."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 14:
        fails.append("morse timbre for T5 must be tubular bells (program 14)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = [s for s in _note_spans(sc, CH_BELLS)
            if MORSE_T0 - 0.1 <= s[0] < BELLS_ROOT_T0]
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} "
                     f"(HOME)")
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
    """The winter's mouth opens: choir CC70 rises monotonically across
    movements III-IV and reaches the T5 floor (>= 80), never above the cap."""
    cap = material.VOWEL_CAPS[NUMBER]
    lane = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if b >= II_END - 1e-6]
    fails = []
    bad = [(b, v) for b, v in lane if v > cap]
    if bad:
        fails.append(f"choir vowel CC70={bad[0][1]} at beat {bad[0][0]:.1f} "
                     f"exceeds the cap {cap}")
    vals = [v for _b, v in lane]
    for i in range(len(vals) - 1):
        if vals[i + 1] < vals[i]:
            fails.append(f"vowel falls at beat {lane[i + 1][0]:.1f} "
                         f"({vals[i]} -> {vals[i + 1]}) - the morph must rise")
            break
    if not vals or max(vals) < material.VOWEL_FLOOR_T5:
        fails.append(f"choir vowel reaches {max(vals) if vals else 0}, want "
                     f">= {material.VOWEL_FLOOR_T5} (open to 'ah')")
    return fails


def _o_keysig_flip(sc):
    """The album's ONE mode flip: D minor (one flat) turning to D major (two
    sharps) at the movement-II seam."""
    want = [(0.0, -1, 1), (I_END, 2, 0)]
    got = sorted((b, int(s), 1 if m else 0) for b, s, m in sc.keysigs)
    if got != want:
        return [f"key grid {got} != {want} (D minor -> D major at {I_END:.0f})"]
    return []


def _o_flat_tempo(sc):
    """The dry causeway: movements II-III are dead-steady - the tempo wiggles
    <= 1 bpm across the whole span - yet remain a MAP (many events, not a
    single frozen tick like T4's ice)."""
    fails = []
    ev = [bpm for _b, bpm in _movement_events(I_END, III_END)]
    if len(ev) < 16:
        fails.append(f"the flat span has {len(ev)} tempo events, want a map "
                     f"(>= 16)")
    if ev and max(ev) - min(ev) > 1.0:
        fails.append(f"tempo wiggle {max(ev) - min(ev):.2f} bpm across II-III "
                     f"> 1.0 (not flat)")
    return fails


def _o_tide_breath(sc):
    """The tide's last swell governs movement I (>= 2 troughs); the flat still
    point (II-III) and the ritardando (IV) are checked separately."""
    seq = [bpm for _b, bpm in _movement_events(0.0, I_END)]
    troughs = sum(1 for i in range(1, len(seq) - 1)
                  if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
    if troughs < 2:
        return [f"movement I has {troughs} tide troughs, want >= 2 (the tide "
                f"must breathe)"]
    return []


def _o_ritardando(sc):
    """Movement IV rides the tide out: a monotonically FALLING tempo to ~62 as
    everything falls away."""
    seq = [bpm for _b, bpm in _movement_events(III_END, END)]
    fails = []
    if len(seq) < 8:
        fails.append(f"ritardando has {len(seq)} tempo events, want a ramp "
                     f"(>= 8)")
    if any(seq[i] < seq[i + 1] - 1e-9 for i in range(len(seq) - 1)):
        fails.append("the ritardando is not monotonically falling")
    if seq and abs(seq[-1] - 62.0) > 2.0:
        fails.append(f"the ritardando ends at {seq[-1]}, want ~62")
    return fails


def _o_crescendo(sc):
    """The 32-bar crescendo: the windowed bar-sums (four 8-bar windows) STRICTLY
    rise across the build - the whole band driving to the crossing's climax."""
    fails = []
    sums = [_bar_sum(sc, CRESC_T0 + 32.0 * w, CRESC_T0 + 32.0 * (w + 1))
            for w in range(4)]
    for i in range(len(sums) - 1):
        if not sums[i + 1] > sums[i]:
            fails.append(f"crescendo window {i + 1} sum {sums[i + 1]:.0f} not "
                         f"above window {i} {sums[i]:.0f}")
    return fails


def _o_decrescendo(sc):
    """Everything falls away: movement IV drops hard from the crescendo's
    climax, and the sustained bed's long expression fade falls out across it."""
    fails = []
    climax = _bar_sum(sc, CRESC_T1 - 16.0, CRESC_T1)      # last 4 bars of III
    open_iv = _bar_sum(sc, III_END, III_END + 16.0)       # first 4 bars of IV
    if not climax > open_iv:
        fails.append(f"IV opening {open_iv:.0f} not below the crescendo "
                     f"climax {climax:.0f}")
    pad11 = [v for b, v in _cc_lane(sc, CH_PAD, 11) if b >= III_END - 1e-6]
    if not pad11 or pad11[0] - min(pad11) < 20:
        fails.append("the pad's long expression fade does not fall away in IV")
    return fails


def _o_lead_solo(sc):
    """The overdriven-lead solo on a TWELVE-semitone bend range: RPN 0 set to
    12, a true wide bend reached, and (by the generic bend-hygiene check) every
    bend recentred before the movement seam."""
    fails = []
    cc6 = [v for _b, v in _cc_lane(sc, CH_LEAD, 6)]
    cc100 = [v for _b, v in _cc_lane(sc, CH_LEAD, 100)]
    if SOLO_BEND_RANGE not in cc6 or 0 not in cc100:
        fails.append(f"lead bend range not set to {SOLO_BEND_RANGE} via RPN 0 "
                     f"(CC6={cc6}, CC100={cc100})")
    fracs = []
    for tk, _p, d in sc.events.get(CH_LEAD, []):
        if (d[0] & 0xF0) == 0xE0:
            fracs.append(((d[1] | (d[2] << 7)) - 8192) / 8192.0)
    if not fracs or max(abs(f) for f in fracs) < 0.5:
        fails.append("the lead never plays a wide bend (>= half the "
                     "twelve-semitone range)")
    return fails


def _o_cc68_jangle(sc):
    """The steel guitar's CC68 hammer-on jangle recurs across the causeway."""
    lane = _cc_lane(sc, CH_STEEL, 68)
    fails = []
    if not any(v >= 64 for _b, v in lane):
        fails.append("no CC68 hammer-on engaged on the steel guitar")
    if not any(v == 0 for _b, v in lane):
        fails.append("steel CC68 never releases")
    if len(lane) < 8:
        fails.append(f"only {len(lane)} CC68 events, want the jangle to recur")
    return fails


def _o_plagal(sc):
    """THE IV-I PLAGAL PICARDY - the album's one authentic arrival: the bass G
    falls to D at the final cadence, F-sharp sounds in the chord (the Picardy
    third), and no C-natural is anywhere in the final window."""
    fails = []
    bass = _note_ons(sc, CH_BASS)
    landing = [p for b, p, _v in bass if abs(b - PLAGAL_DOWN) <= 0.1]
    if not landing or all(p % 12 != MAINLAND_TONIC_PC for p in landing):
        fails.append(f"the bass does not land on D (pc {MAINLAND_TONIC_PC}) at "
                     f"the plagal downbeat {PLAGAL_DOWN:.0f}")
    prior = [p for b, p, _v in bass
             if PLAGAL_LO - 1e-6 <= b < PLAGAL_DOWN - 0.1]
    if not prior or prior[-1] % 12 != 7:            # G = pc 7, the IV
        fails.append(f"the bass approach into the plagal cadence is not G "
                     f"(IV); got {[p % 12 for p in prior]}")
    fsharp = False
    cnat = None
    for ch in sorted(sc.events):
        if ch == 9:
            continue
        for b, p, _v in _note_ons(sc, ch):
            if PLAGAL_LO - 1e-6 <= b <= PLAGAL_HI + 1e-6:
                if p % 12 == 6:
                    fsharp = True
                if p % 12 == 0:
                    cnat = (ch, b, p)
    if not fsharp:
        fails.append("no F-sharp in the plagal chord (the Picardy third is "
                     "missing)")
    if cnat is not None:
        fails.append(f"a C-natural sounds in the final window (ch{cnat[0]} "
                     f"beat {cnat[1]:.1f}) - it must be absent (plagal purity)")
    return fails


def _o_shore_pans(sc):
    """The strait at its narrowest: island channels left (60), mainland right
    (68) - only eight apart, the closest the field ever is."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_ISLAND, CH_CHOIR, CH_PANFLUTE, CH_PAD, CH_VIBES}
    mainland = {CH_MAINLAND, CH_STEEL, CH_BRASS, CH_LEAD}
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
    """The bell buoy tolls FIVE times (track 5) on D (the union tonic), the
    final note-ons - after the first toll nothing new sounds but the four
    remaining tolls."""
    fails = []
    tolls = [(b, p) for b, p, _v in _note_ons(sc, CH_BELLS)
             if b >= TOLL_T0 - 1e-6]
    if len(tolls) != material.TOLLS[NUMBER]:
        fails.append(f"{len(tolls)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p in tolls:
        if p % 12 != MAINLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want "
                         f"{MAINLAND_TONIC_PC} (D)")
            break
    all_ons = sorted((b, ch) for ch in sc.events
                     for b, _p, _v in _note_ons(sc, ch))
    if tolls:
        toll_on = tolls[0][0]
        after = [(b, ch) for b, ch in all_ons
                 if b > toll_on + 1e-6 and ch != CH_BELLS]
        if after:
            fails.append(f"{len(after)} note-on(s) after the first toll (e.g. "
                         f"ch{after[0][1]} at {after[0][0]:.1f})")
        if all_ons and all_ons[-1][1] != CH_BELLS:
            fails.append("the final note-on is not a toll")
    return fails


def oracles(sc, info, spans):
    return [
        ("convergence", _o_convergence(sc)),
        ("simultaneity", _o_simultaneity(sc)),
        ("invertibility", _o_invertibility(sc)),
        ("fusion_landing", _o_fusion(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("medley", _o_medley(sc)),
        ("protagonist_bass", _o_protagonist_bass(sc)),
        ("doubled_thumb", _o_doubled_thumb(sc)),
        ("breath_herald", _o_herald(sc)),
        ("morse_home", _o_morse(sc)),
        ("vowel_rise", _o_vowel_rise(sc)),
        ("keysig_flip", _o_keysig_flip(sc)),
        ("flat_tempo", _o_flat_tempo(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("ritardando", _o_ritardando(sc)),
        ("crescendo", _o_crescendo(sc)),
        ("decrescendo", _o_decrescendo(sc)),
        ("lead_bend_solo", _o_lead_solo(sc)),
        ("cc68_jangle", _o_cc68_jangle(sc)),
        ("plagal_picardy", _o_plagal(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) - RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The crossing blooms from First Light, the crescendo builds, and the tolls
# ring into a quiet tail.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    first = _rms_db(40.0, 72.0)          # First Light, sparse D minor
    early = _rms_db(356.0, 384.0)        # the crescendo's start
    climax = _rms_db(456.0, 478.0)       # the crescendo's climax
    tail = _rms_db(569.0, 582.0)         # the tolls ringing into the tail

    # 1. The crescendo builds: the climax sits above its own start.
    fails = []
    if climax - early < 1.0:
        fails.append(f"crescendo climax {climax:.1f} dB not >= 1 dB over its "
                     f"start {early:.1f} dB (the build should be audible)")
    checks.append(("audio_crescendo_builds", fails))

    # 2. The tolls ring into a quiet tail, well below the climax.
    fails = []
    if climax - tail < 1.0:
        fails.append(f"the toll tail {tail:.1f} dB not >= 1 dB below the "
                     f"climax {climax:.1f} dB (the finale should fall away)")
    checks.append(("audio_tolls_quiet_tail", fails))

    # 3. The union crossing blooms far above the estranged First Light.
    fails = []
    if climax - first < 1.0:
        fails.append(f"the crossing climax {climax:.1f} dB not >= 1 dB over "
                     f"First Light {first:.1f} dB (the union should bloom)")
    checks.append(("audio_union_blooms", fails))
    return checks

