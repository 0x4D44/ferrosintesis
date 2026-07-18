"""movements/t01_neap_light.py — track 1 of *The Causeway*.

NEAP LIGHT.  The island alone; the far shore only a rumour.  An E-minor
incantation at the neap — the tide that never fully comes in — breathing
between 70 and 74 bpm, lifting to a locked ~92 for its Delerium heartbeat,
then receding.  Four movements:

  I. Grey Water   — the piano states THE ISLAND THEME twice over open-fifth
     drones; a nylon guitar answers fragments; a sealed choir ooohs under a
     capped vowel; a celesta taps NEAP in Morse; the tide breathes the tempo.
  II. The Heartbeat — a pan-flute breath herald (the hook's first three notes
     over a rising swell, two bars alone), then the groove: a low synth-bass
     HOOK1 ostinato — the heartbeat — a soft kit, FM-EP ice arpeggios, and the
     protagonist bass singing above the pulse.  Two choruses thicken with the
     doubled thumb (piano at the octave); the island theme sings once on
     strings inside the groove; the bass cadences modally, twice, the ache
     withheld.
  III. The Far Shore — the album's ONLY mainland appearance: THE MAINLAND
     THEME once, in B-flat a tritone away, on a french horn drenched in
     reverb (its send far above every other channel's — distance coded in the
     wet) while the island thins to held pads.  No island statement sounds
     against it.
  IV. Neap        — the island theme once more, slower and lower, hanging on
     F-sharp; the pad falls away; a single bell tolls the island's E, and
     nothing sounds after it.

Every device the HLD marks verified is an oracle below, and all recurring
data is single-sourced from material.py (the two themes, the hook, the
convergence pcs, the morse word, the tide-breath, the shore pans, the vowel
cap, the tolls, the cadence law).  The mainland begins a tritone from the
island (distance 6): the widest the strait ever is.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 1
TITLE = "Neap Light"
FILE = "01 - Neap Light.mid"
SEED = 202607181
COMMENT = (
    "Neap Light - the island alone, the far shore only a rumour.  An E minor "
    "incantation at the neap tide: piano states the island theme over "
    "open-fifth drones while a sealed choir hums and a celesta taps NEAP in "
    "Morse; a pan-flute breath heralds a locked Delerium heartbeat - a low "
    "synth-bass ostinato under a singing protagonist bass, doubled at the "
    "octave through two choruses; then the album's only mainland glimpse, "
    "its theme once in B-flat a tritone away on a reverb-drenched french "
    "horn, before the island theme returns slower, hangs on F-sharp, and a "
    "single bell tolls the tonic.")

# ---------------------------------------------------------------------------
# Channels (island pole left at SHORE_PANS[1][0]=40, mainland pole right at
# 88; piano / bass / celesta / drums / bells neutral at 64).  The french
# horn's reverb send is the distance code: >= 100 against <= 48 everywhere.
# ---------------------------------------------------------------------------

CH_PIANO, CH_GUITAR, CH_CHOIR, CH_CELESTA = 0, 1, 2, 3
CH_BASS, CH_HORN, CH_PANFLUTE, CH_SYNBASS = 4, 5, 6, 7
CH_EP, CH_DRUMS, CH_STRINGS, CH_BELLS, CH_PAD = 8, 9, 10, 11, 12

_MM = material.MODE_MINOR                 # aeolian - the island's mode

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]      # (40, 88)
HORN_REVERB = 112                          # the far-shore send (>= 100)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 4, 10

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 112.0
HERALD_T0, HERALD_T1 = 112.0, 120.0        # >= 2 bars, pan flute alone
II_END = 288.0
III_END = 360.0
END = 424.0

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE = en.n("E4")                   # 64 - the island tonic (deg 1)
ISLAND_BASE_HI = en.n("E5")                # 76 - statement 2, an octave up
ISLAND_STMT1_T0, ISLAND_STMT2_T0 = 8.0, 64.0
STRINGS_THEME_T0 = 200.0                   # the island sings inside the groove
NEAP_THEME_T0, NEAP_STRETCH = 364.0, 1.75  # movement IV, slower and lower
MAINLAND_BASE = en.n("Bb3")                # 58 - the far shore, a tritone away
MAINLAND_T0, MAINLAND_STRETCH = 312.0, 1.5

GROOVE_T0 = 120.0                          # the heartbeat locks in here
OSTINATO_ROOT = en.n("E2")                 # 40 - the low pulse (HOOK1 shape)
HERALD_PITCH = en.n("B4")                  # 71 - the hook head, breathed
CHORUS_SPANS = [(160.0, 192.0), (224.0, 256.0)]
CAD_WINDOWS = [(188.0, 192.0, 192.0), (252.0, 256.0, 256.0)]  # (lo, hi, down)

MORSE_T0 = 24.0
MORSE_PITCH = en.n("E5")                    # 76 - the celesta's fixed tap
TOLL_T0 = 420.0
TOLL_PITCH = en.n("E3")                     # 52 - pc 4 = the island tonic

# --- the tide-breath tempo map (the water is in the tempo) ---
# Every movement swells; none is a still point on this track.
TEMPO_MAP = (
    material.tide_breath(74.0, 0.0, I_END, period=32.0, depth=4.0)
    + material.tide_breath(92.0, I_END, II_END, period=32.0, depth=3.0)
    + material.tide_breath(72.0, II_END, III_END, period=32.0, depth=4.0)
    + material.tide_breath(68.0, III_END, END, period=32.0, depth=5.0))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Grey Water", 0.0, I_END),
               ("II. The Heartbeat", I_END, II_END),
               ("III. The Far Shore", II_END, III_END),
               ("IV. Neap", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 1)],                  # E minor: one sharp, minor
    channels=[(CH_PIANO, "piano", 0, 96, 64, 40),
              (CH_GUITAR, "nylon guitar", 24, 82, ISL_PAN, 44),
              (CH_CHOIR, "choir", 52, 78, ISL_PAN, 46),
              (CH_CELESTA, "celesta", 8, 80, 64, 38),
              (CH_BASS, "protagonist bass", 33, 100, 64, 30),
              (CH_HORN, "french horn", 60, 88, MAIN_PAN, HORN_REVERB),
              (CH_PANFLUTE, "pan flute", 75, 84, ISL_PAN, 46),
              (CH_SYNBASS, "synth bass", 38, 92, ISL_PAN, 20),
              (CH_EP, "fm ep", 5, 80, ISL_PAN, 40),
              (CH_DRUMS, "soft kit", 0, 88, 64, 28),
              (CH_STRINGS, "strings", 48, 86, ISL_PAN, 44),
              (CH_BELLS, "tubular bells", 14, 90, 64, 46),
              (CH_PAD, "warm pad", 89, 72, ISL_PAN, 44)],
    extra_markers=[(HERALD_T0, "breath herald"), (GROOVE_T0, "the heartbeat"),
                   (MAINLAND_T0, "the far shore"), (TOLL_T0, "the toll")],
)

PROGRAM_WHITELIST = {0, 24, 52, 8, 33, 60, 75, 38, 5, 48, 14, 89}
CENTERED_CHANNELS = {CH_PIANO, CH_CELESTA, CH_BASS, CH_DRUMS, CH_BELLS}
NOTE_RANGES = {
    CH_PIANO: (40, 84), CH_GUITAR: (48, 80), CH_CHOIR: (50, 79),
    CH_CELESTA: (76, 76), CH_BASS: (26, 50), CH_HORN: (55, 72),
    CH_PANFLUTE: (67, 74), CH_SYNBASS: (33, 52), CH_EP: (60, 88),
    CH_STRINGS: (60, 84), CH_BELLS: (50, 68), CH_PAD: (31, 76),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # no pitch bends: CC1/CC11 only
DURATION_WINDOW = (318.0, 345.0)            # ~5:31 incl. the 2-beat end pad
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


# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (themes, hook, morse, tolls, the herald and
# the doubled thumb) are jt=0 so every statement is findable and every shadow
# lands on its bass note's tick; texture lanes take a light jitter.
# ---------------------------------------------------------------------------

# The island's low register, E aeolian, for the walking protagonist bass.
BASS_SCALE = [en.n(x) for x in
              ("E1", "F#1", "G1", "A1", "B1", "C2", "D2", "E2", "F#2",
               "G2", "A2", "B2", "C3", "D3", "E3")]

# Open-fifth drone voicings for Grey Water: i - bVI - bIII - iv in E aeolian.
DRONE_CYCLE = [
    [en.n("E2"), en.n("B2"), en.n("E3")],     # Em  (i)
    [en.n("C2"), en.n("G2"), en.n("C3")],     # C   (bVI)
    [en.n("G1"), en.n("D2"), en.n("G2")],     # G   (bIII)
    [en.n("A1"), en.n("E2"), en.n("A2")],     # Am  (iv)
]
# The choir sings the fifth of each drone chord, sealed under the vowel cap.
CHOIR_TOPS = [en.n("B4"), en.n("G4"), en.n("D4"), en.n("E4")]


def _bar_vel(beat, base, accent=10):
    """A gentle on-beat accent for the groove lanes."""
    q = beat % 4.0
    if abs(q) < 1e-6:
        return base + accent
    if abs(q - 2.0) < 1e-6:
        return base + accent // 2
    return base


def _walk(sc, ch, t0, start_idx, deltas, dur, vel_base, jt=0):
    """Step a bass melody through BASS_SCALE by scale-step deltas (mostly
    +-1 so it stays stepwise); one note every `dur` beats.  Returns the end
    beat and the final scale index."""
    idx = start_idx
    beat = t0
    for d in deltas:
        idx = max(0, min(len(BASS_SCALE) - 1, idx + d))
        sc.note(ch, BASS_SCALE[idx], beat, dur * 0.94,
                _bar_vel(beat, vel_base), jt=jt, jv=3)
        beat += dur
    return beat, idx


# -- Grey Water -------------------------------------------------------------

def _drone(sc):
    """Open-fifth drones, 8 beats each, ending exactly at I_END so the herald
    that follows sounds alone."""
    n = int(I_END // 8)                       # 14 chords -> 0..112
    for i in range(n):
        t0 = i * 8.0
        for p in DRONE_CYCLE[i % 4]:
            sc.note(CH_PAD, p, t0, 8.0, 44, jt=0, jv=2)
    en.expr_curve(sc, CH_PAD, [(0.0, 34), (48.0, 54), (96.0, 46),
                               (I_END - 1, 40)], step=4.0)


def _choir_grey(sc):
    """The sealed choir: one held tone per drone chord, vowel <= cap, a slow
    swell, CC1 vibrato barely opening."""
    n = int(I_END // 8)
    for i in range(n):
        sc.note(CH_CHOIR, CHOIR_TOPS[i % 4], i * 8.0, 7.6, 46, jt=1, jv=3)
    en.vowel_curve(sc, CH_CHOIR, [(0.0, 10), (56.0, 30), (I_END - 1, 38)],
                   step=4.0)
    en.expr_curve(sc, CH_CHOIR, [(0.0, 40), (56.0, 62), (I_END - 1, 44)],
                  step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, [(0.0, 0), (I_END - 1, 22)], step=8.0)


def _guitar_fragments(sc):
    """Nylon answers - short island-motif gestures (never a full statement)
    between the piano's two theme readings."""
    frags = [
        (20.0, [en.n("B4"), en.n("A4"), en.n("G4")]),
        (40.0, [en.n("E4"), en.n("F#4"), en.n("G4"), en.n("E4")]),
        (88.0, [en.n("G4"), en.n("A4"), en.n("B4")]),
        (100.0, [en.n("F#4"), en.n("E4"), en.n("D4")]),
    ]
    for t0, notes in frags:
        for k, p in enumerate(notes):
            sc.note(CH_GUITAR, p, t0 + k * 0.5, 0.55, 60 - k * 2,
                    jt=3, jv=4)


# -- The Heartbeat ----------------------------------------------------------

def _herald(sc):
    """Enigma's inhale: the hook's first three notes on pan flute, alone, over
    a strictly rising CC11 swell (two bars).  Notes 1-2 share a pitch and are
    laid contiguous so no same-pitch overlap survives."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]   # [0, 0, -2]
    starts = [HERALD_T0, HERALD_T0 + 2.0, HERALD_T0 + 4.0]
    durs = [2.0, 2.0, 4.0]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, HERALD_PITCH + s, st, du, 58, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 18), (HERALD_T1, 104)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 30)],
                step=0.5)


def _ostinato(sc):
    """The heartbeat: HOOK1 on the low synth bass, every two beats, a locked
    pulse breathing only in velocity."""
    t = GROOVE_T0
    k = 0
    while t < II_END - 1e-6:
        peak = 78 + int(10 * (0.5 - 0.5 * math.cos(
            2 * math.pi * (k % 16) / 16)))
        material.play_hook(sc, CH_SYNBASS, t, OSTINATO_ROOT, NUMBER,
                           vel=peak, gate=0.9)
        t += 2.0
        k += 1


def _groove_drums(sc):
    """A soft half-time kit: kick on 1, snare on 3, quaver hats, a ride swell
    into each chorus."""
    bar = GROOVE_T0
    while bar < II_END - 1e-6:
        sc.hit(36, bar, 74, jt=0)                 # kick on the downbeat
        sc.hit(38, bar + 2.0, 62, jt=0)           # snare, half-time backbeat
        for q in range(8):
            v = 40 + (8 if q % 2 == 0 else 0)
            sc.hit(42, bar + q * 0.5, v, jt=0)    # closed hats (locked)
        bar += 4.0
    for lo, _hi in CHORUS_SPANS:                  # a ride shimmer opening each
        for q in range(8):
            sc.hit(51, lo - 4.0 + q * 0.5, 34 + q * 2, jt=0)


def _ep_arps(sc):
    """FM-EP ice: broken-chord semiquavers high over the groove, following the
    drone cycle, CC1 opening across the movement."""
    chords = {0: [en.n("E4"), en.n("G4"), en.n("B4"), en.n("E5")],
              1: [en.n("C4"), en.n("E4"), en.n("G4"), en.n("C5")],
              2: [en.n("G4"), en.n("B4"), en.n("D5"), en.n("G5")],
              3: [en.n("A4"), en.n("C5"), en.n("E5"), en.n("A5")]}
    bar = GROOVE_T0
    ci = 0
    while bar < II_END - 1e-6:
        ch_notes = chords[ci % 4]
        for q in range(8):
            idx = q if q < 4 else 7 - q         # an up-then-down ice arp
            sc.note(CH_EP, ch_notes[idx], bar + q * 0.5, 0.45,
                    52 + (idx % 4) * 3, jt=0, jv=3)
        bar += 4.0
        ci += 1
    en.cc_curve(sc, CH_EP, 1, [(GROOVE_T0, 8), (204.0, 40), (II_END - 1, 20)],
                step=8.0)
    en.expr_curve(sc, CH_EP, [(GROOVE_T0, 48), (204.0, 70), (II_END - 1, 52)],
                  step=4.0)


def _emit_bass(sc):
    """The protagonist bass: a stepwise-singing McCartney line above the pulse,
    stating HOOK1 at each chorus head and cadencing modally to E (iv-i, then
    v-i).  Returns nothing; the doubled thumb reads its onsets back."""
    v = 84
    # Verse A [120,160): a rising-then-falling walk, mostly steps.
    beat, idx = _walk(sc, CH_BASS, 120.0, 7,
                      [0, 1, 1, -1, 1, -2, 1, 1, -1, -1, 2, -1, -1, -2,
                       1, 1, 1, -1, -1, -1], 2.0, v)
    # Chorus 1 [160,192): HOOK1 head (root E2), then a walk to the cadence.
    material.play_hook(sc, CH_BASS, 160.0, en.n("E2"), NUMBER, vel=88,
                       gate=0.9)
    beat, idx = _walk(sc, CH_BASS, 162.0, 7,
                      [1, 1, -1, 1, 1, -2, -1, 1, 2, -1, -1, -1, 1, -1,
                       -1, -1, 1, 1], 1.5, v)     # -> beat 189.0
    sc.note(CH_BASS, en.n("A1"), 190.0, 1.0, 82, jt=0, jv=3)   # iv approach
    sc.note(CH_BASS, en.n("A1"), 191.0, 1.0, 80, jt=0, jv=3)
    sc.note(CH_BASS, en.n("E2"), 192.0, 2.0, 90, jt=0, jv=3)   # lands the tonic
    # Verse B [194,224): a lower, sparser answer.
    beat, idx = _walk(sc, CH_BASS, 194.0, 7,
                      [-2, 1, 1, -1, -1, 1, 2, -1, -1, -2, 1, 1, 1, -1,
                       1], 2.0, v - 4)
    # Chorus 2 [224,256): HOOK1 again, then a walk to the v-i cadence.
    material.play_hook(sc, CH_BASS, 224.0, en.n("E2"), NUMBER, vel=90,
                       gate=0.9)
    beat, idx = _walk(sc, CH_BASS, 226.0, 7,
                      [1, 2, 1, 1, -2, -1, -1, 1, -1, -2, 1, 1, -1, -1,
                       1, -1, -2, -1], 1.5, v)     # peaks C3; -> beat 253.0
    sc.note(CH_BASS, en.n("B1"), 254.0, 1.0, 84, jt=0, jv=3)   # v approach
    sc.note(CH_BASS, en.n("B1"), 255.0, 1.0, 82, jt=0, jv=3)
    sc.note(CH_BASS, en.n("E2"), 256.0, 2.0, 92, jt=0, jv=3)   # lands the tonic
    # Verse C [258,288): the groove recedes, the bass sinking home.
    _walk(sc, CH_BASS, 258.0, 7,
          [-1, -1, 1, -1, -1, -2, 1, 1, -1, -1, 1, -2, -1, 1, -1], 2.0,
          v - 8)


def _double_thumb(sc):
    """Inside the choruses only, shadow every bass note-on at the octave on
    the piano - the doubled thumb that makes a chorus feel bigger."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if any(lo <= beat < hi for lo, hi in CHORUS_SPANS):
            sc.note(CH_PIANO, pitch + 12, beat, 0.9, 70, jt=0, jv=2)
    en.sustain(sc, CH_PIANO, 160.0, 192.0)
    en.sustain(sc, CH_PIANO, 224.0, 256.0)


# -- The Far Shore & Neap ---------------------------------------------------

def _pad_hold(sc, ch, blocks, vel):
    """Sustained voicings: blocks are (t0, dur, [pitches])."""
    for t0, dur, pitches in blocks:
        for p in pitches:
            sc.note(ch, p, t0, dur, vel, jt=0, jv=2)


# ---------------------------------------------------------------------------
# I. Grey Water [0, 112) — the island theme twice over open-fifth drones
# ---------------------------------------------------------------------------

def _b_grey_water(sc):
    _drone(sc)
    _choir_grey(sc)
    _guitar_fragments(sc)
    material.play_morse(sc, CH_CELESTA, MORSE_T0, NUMBER, MORSE_PITCH)
    # The piano states THE ISLAND THEME twice; the second an octave up, both
    # implying the E-minor tonic.  jt=0 (via play_island) keeps them findable,
    # and the piano sounds nothing else here so each run stays monophonic.
    material.play_island(sc, CH_PIANO, ISLAND_STMT1_T0, ISLAND_BASE,
                         vel=74, vel_end=64)
    en.sustain(sc, CH_PIANO, ISLAND_STMT1_T0, ISLAND_STMT1_T0 + 8.0)
    material.play_island(sc, CH_PIANO, ISLAND_STMT2_T0, ISLAND_BASE_HI,
                         vel=72, vel_end=62)
    en.sustain(sc, CH_PIANO, ISLAND_STMT2_T0, ISLAND_STMT2_T0 + 8.0)


# ---------------------------------------------------------------------------
# II. The Heartbeat [112, 288) — the herald, then the locked Delerium groove
# ---------------------------------------------------------------------------

def _b_heartbeat(sc):
    _herald(sc)
    _ostinato(sc)
    _groove_drums(sc)
    _ep_arps(sc)
    _emit_bass(sc)
    _double_thumb(sc)
    # The island sings once inside the groove, on strings, clean and monophonic.
    material.play_island(sc, CH_STRINGS, STRINGS_THEME_T0, ISLAND_BASE,
                         vel=74, vel_end=64)
    en.expr_curve(sc, CH_STRINGS,
                  [(STRINGS_THEME_T0, 44), (STRINGS_THEME_T0 + 4, 86),
                   (STRINGS_THEME_T0 + 8, 40)], step=0.5)
    en.cc_curve(sc, CH_STRINGS, 1,
                [(STRINGS_THEME_T0, 6), (STRINGS_THEME_T0 + 8, 30)], step=1.0)
    en.echo_throw(sc, CH_STRINGS, STRINGS_THEME_T0 + 7.5)


# ---------------------------------------------------------------------------
# III. The Far Shore [288, 360) — the mainland's one call, a tritone away
# ---------------------------------------------------------------------------

def _b_far_shore(sc):
    _pad_hold(sc, CH_PAD,
              [(288.0, 24.0, [en.n("E2"), en.n("B2"), en.n("E3")]),
               (312.0, 24.0, [en.n("E2"), en.n("B2"), en.n("E3")]),
               (336.0, 24.0, [en.n("A1"), en.n("E2"), en.n("A2")])], 40)
    en.expr_curve(sc, CH_PAD, [(288.0, 40), (320.0, 52), (359.0, 34)],
                  step=4.0)
    for t0, dur, p in [(288.0, 24.0, en.n("B4")), (312.0, 24.0, en.n("E4")),
                       (336.0, 24.0, en.n("A4"))]:
        sc.note(CH_CHOIR, p, t0, dur * 0.98, 44, jt=1, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(288.0, 20), (336.0, 38), (359.0, 30)],
                   step=4.0)
    en.expr_curve(sc, CH_CHOIR, [(288.0, 42), (320.0, 58), (359.0, 40)],
                  step=4.0)
    en.echo_throw(sc, CH_CHOIR, 335.0)
    # THE MAINLAND THEME, once, in B-flat: the far shore, drenched in reverb.
    material.play_mainland(sc, CH_HORN, MAINLAND_T0, MAINLAND_BASE,
                           stretch=MAINLAND_STRETCH, vel=68, vel_end=58)
    en.expr_curve(sc, CH_HORN, [(MAINLAND_T0, 38), (MAINLAND_T0 + 6, 88),
                                (MAINLAND_T0 + 12, 46), (MAINLAND_T0 + 16, 18)],
                  step=0.5)
    en.cc_curve(sc, CH_HORN, 1, [(MAINLAND_T0, 0), (MAINLAND_T0 + 12, 26)],
                step=1.0)
    en.echo_throw(sc, CH_HORN, MAINLAND_T0 + 11.5)


# ---------------------------------------------------------------------------
# IV. Neap [360, 424) — the theme once more, hanging on F-sharp; one toll
# ---------------------------------------------------------------------------

def _b_neap(sc):
    _pad_hold(sc, CH_PAD,
              [(360.0, 30.0, [en.n("E2"), en.n("B2"), en.n("E3")]),
               (390.0, 30.0, [en.n("E2"), en.n("B2"), en.n("E3")])], 40)
    en.expr_curve(sc, CH_PAD, [(360.0, 40), (384.0, 46), (418.0, 26)],
                  step=4.0)
    # The last island reading: slower and lower, still hanging on degree 2.
    material.play_island(sc, CH_PIANO, NEAP_THEME_T0, ISLAND_BASE,
                         stretch=NEAP_STRETCH, vel=66, vel_end=54)
    en.sustain(sc, CH_PIANO, NEAP_THEME_T0, NEAP_THEME_T0 + 8.0 * NEAP_STRETCH)
    # The bell buoy: exactly one toll on the island's E, the final note-on.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        vel=82, dur=3.5)


BUILDERS = [_b_grey_water, _b_heartbeat, _b_far_shore, _b_neap]


# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """The island states four times (tonic E, pc 4); the mainland once
    (tonic B-flat, pc 10) — the widest strait, distance 6."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 4:
        fails.append(f"{len(isl)} island statements, want 4 (I x2, II, IV)")
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
                         f"{pc}, want {MAINLAND_TONIC_PC} (Bb)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 6:
            fails.append(f"shore distance {dist}, want 6 (a tritone)")
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
    and the fusion phrase (the album's only tonic landing) is T5's alone."""
    fails = []
    if material.theme_statements(sc, "fusion"):
        fails.append("the FUSION phrase must not sound on tracks 1-4")
    isl_end = en.deg_semis(_MM, material.ISLAND_END_DEG) - \
        en.deg_semis(_MM, material.ISLAND_FIRST_DEG)
    for ch, start, _end, first in material.theme_statements(sc, "island"):
        last_pc = (first + isl_end) % 12
        if last_pc == material.island_tonic_pc(first):
            fails.append(f"island at {start:.1f} ends on the tonic")
    return fails


def _o_hook_density(sc):
    """The heartbeat earworm: HOOK1 stated >= 6 times across the track."""
    hits = 0
    for ch in sc.events:
        hits += len(material.find_statements(material.note_ons(sc, ch),
                                             material.HOOKS[NUMBER]))
    if hits < 6:
        return [f"HOOK1 found {hits} times, want >= 6"]
    return []


def _o_protagonist_bass(sc):
    """The McCartney bass: stepwise-dominant, wide-ranging, and stating the
    hook in the bass inside each chorus."""
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
    in_chorus = [h for h in bass_hooks
                 if any(lo <= h[0] < hi for lo, hi in CHORUS_SPANS)]
    if len(in_chorus) < 2:
        fails.append(f"hook stated {len(in_chorus)} times in the bass inside "
                     f"the choruses, want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The chorus thickens: every bass note-on shadowed at the octave on the
    piano inside the choruses (coverage >= 0.80), and not outside (< 0.30)."""
    fails = []
    piano = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_PIANO)]

    def shadowed(btick, bp):
        return any(pp == bp + 12 and abs(pt - btick) <= 10 for pt, pp in piano)

    inside, outside = [], []
    for b, p, _v in _note_ons(sc, CH_BASS):
        (inside if any(lo <= b < hi for lo, hi in CHORUS_SPANS)
         else outside).append((_tick(b), p))
    cov_in = (sum(1 for bt, bp in inside if shadowed(bt, bp)) / len(inside)
              if inside else 0.0)
    cov_out = (sum(1 for bt, bp in outside if shadowed(bt, bp)) / len(outside)
               if outside else 0.0)
    if cov_in < 0.80:
        fails.append(f"doubled-thumb coverage {cov_in:.2f} inside choruses "
                     f"< 0.80")
    if cov_out >= 0.30:
        fails.append(f"bass doubled {cov_out:.2f} OUTSIDE choruses "
                     f">= 0.30 (the thickening must be a chorus event)")
    return fails


def _o_herald(sc):
    """The breath herald: >= 2 bars where only the pan flute sounds, playing
    the hook's first three notes over a strictly-rising CC11 swell."""
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
        fails.append(f"herald has {len(pf)} pan-flute notes, want 3 (the "
                     f"hook head)")
    else:
        deltas = [pf[k][1] - pf[0][1] for k in range(3)]
        if deltas != want:
            fails.append(f"herald pitch deltas {deltas}, want {want}")
    cc11 = [v for b, v in _cc_lane(sc, CH_PANFLUTE, 11)
            if HERALD_T0 - 1e-6 <= b <= HERALD_T1 + 1e-6]
    if len(cc11) < 4 or any(cc11[i] >= cc11[i + 1] for i in range(len(cc11) - 1)):
        fails.append("herald CC11 swell is not strictly rising")
    if HERALD_T1 - HERALD_T0 < 8.0:
        fails.append(f"herald window {HERALD_T1 - HERALD_T0} beats < 2 bars")
    return fails


def _o_morse(sc):
    """The tide-word NEAP, tapped on celesta (MORSE_PROGRAMS[1] = 8), in
    standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 8:
        fails.append("morse timbre for T1 must be celesta (program 8)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_CELESTA)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} "
                     f"(NEAP)")
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
                         f"{wdu * 0.9:.3f} (dit/dah)")
            break
    return fails


def _o_vowel_cap(sc):
    """The winter's mouth sealed: choir CC70 never exceeds T1's cap of 40."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_reverb_distance(sc):
    """Distance coded in the send: the far-shore horn's reverb is >= 100 while
    every other channel sits <= 48."""
    fails = []
    horn = _cc_lane(sc, CH_HORN, 91)
    if not horn or any(v < 100 for _b, v in horn):
        fails.append(f"french-horn reverb send {[v for _b, v in horn]} "
                     f"not all >= 100")
    for ch in sorted(sc.events):
        if ch == CH_HORN:
            continue
        bad = [(b, v) for b, v in _cc_lane(sc, ch, 91) if v > 48]
        if bad:
            fails.append(f"ch{ch} reverb send {bad[0][1]} > 48 (only the far "
                         f"shore is wet)")
            break
    return fails


def _o_tide_breath(sc):
    """The water is in the tempo: every movement swells (>= 2 troughs); none
    is a still point on this track."""
    fails = []
    for name, t0, t1 in [m[:3] for m in PART.MOVEMENTS]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2 "
                         f"(the map must breathe)")
    return fails


def _o_cadence(sc):
    """The withheld cadence: the bass resolves to E modally (iv-i, then v-i),
    the leading tone banned across each window on every channel."""
    fails = []
    for lo, hi, down in CAD_WINDOWS:
        for m in material.cadence_failures(sc, CH_BASS, lo, hi, down,
                                           ISLAND_TONIC_PC):
            fails.append(f"[{lo:.0f},{hi:.0f}]: {m}")
    return fails


def _o_shore_pans(sc):
    """The narrowing strait: island channels left (40), the mainland horn
    right (88) — the widest the field is on the album."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_GUITAR, CH_CHOIR, CH_PANFLUTE, CH_SYNBASS, CH_EP,
              CH_STRINGS, CH_PAD}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{ISL_PAN}} "
                         f"({ISL_PAN})")
    horn = {v for _b, v in _cc_lane(sc, CH_HORN, 10)}
    if horn != {MAIN_PAN}:
        fails.append(f"mainland horn pans {sorted(horn)}, want {MAIN_PAN}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls once (track 1); its E is the final note-on, and
    nothing sounds after it."""
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
            fails.append(f"{len(after)} note-on(s) after the toll (only the "
                         f"toll may sound last), e.g. ch{after[0][1]}")
        if all_ons and all_ons[-1][1] != CH_BELLS:
            fails.append("the final note-on is not the toll")
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
        ("morse_neap", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("reverb_distance", _o_reverb_distance(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("cadence_law", _o_cadence(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# All express the HLD sec.4 T1 note: the far-shore horn reads distant (quieter,
# wetter) against the near, full groove.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    groove = _rms_db(176.0, 208.0)      # the near, full Delerium groove
    far = _rms_db(313.0, 323.0)         # the far-shore horn + thin pads
    herald = _rms_db(113.0, 119.0)      # the pan-flute inhale, alone

    # 1. The far shore is a distant rumour: the groove sits above it.
    fails = []
    if groove - far < 0.5:
        fails.append(f"groove {groove:.1f} dB not >= 0.5 dB over the far "
                     f"shore {far:.1f} dB (the mainland should read distant)")
    checks.append(("audio_far_shore_distant", fails))

    # 2. The inhale is quieter than the groove it heralds.
    fails = []
    if groove - herald < 1.5:
        fails.append(f"groove {groove:.1f} dB not >= 1.5 dB over the herald "
                     f"{herald:.1f} dB (the breath should be the quiet part)")
    checks.append(("audio_herald_inhale", fails))

    # 3. The far shore is WET: heavy reverb makes the horn's tail ring, so the
    #    energy after the phrase stays within a band of the phrase body rather
    #    than cutting off (a dry lane would drop far further).
    body = _rms_db(313.0, 322.0)
    tail = _rms_db(325.0, 329.0)
    fails = []
    if tail - body < -12.0:
        fails.append(f"far-shore tail {tail:.1f} dB falls >12 dB below the "
                     f"body {body:.1f} dB (the horn should ring wet)")
    checks.append(("audio_far_shore_wet", fails))
    return checks


