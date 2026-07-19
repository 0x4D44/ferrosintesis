"""movements/t10_out_on_the_tide.py — track 10 of *The Causeway* (the finale).

OUT ON THE TIDE.  The second crossing: both voices leave together at low
water, and the album ends on open sea.  Band-on-the-Run gallop and
Pipes-of-Peace pomp — piano pump, protagonist bass, steel-guitar jangle,
brass, tubular bells, timpani, the choir at its fullest — in D major at a
tide-breathing ~96 that NEVER goes flat: the tempo law is inverted from T5,
because this time they are ON the water, and the deepest swell is the last.
Not a remake of T5: the payoffs get their own movements, and the ending is a
fade at full sail, not a fall-away.  Four movements:

  Herald + I. Eight Bells — the last inhale: the pan flute alone states THE
     SAIL (HOOK10 — the fusion frame: first note, crest, last note lifted an
     octave) twice over a rising swell, before anything else sounds.  Then
     the dawn assembly, additive: piano pump, bass, strings, kit, brass;
     the glockenspiel taps SAIL in Morse; one unpinned echo of Act One's
     pump call (HOOK5) drifts through on the piano.
  II. The Boarding — the gallop, and THE ACT-TWO MEDLEY: hooks 6, 7, 8 and
     9 each return over the running pump (counted UNNESTED — and this
     movement is fusion-free by law, so every hit is genuine).  The
     protagonist bass sings HOOK10 through two octave-doubled choruses
     (the pump switches from root-fifth to full octaves exactly there);
     steel-guitar CC68 hammer-on jangle; brass warming with aftertouch;
     island and mainland overlap in D, downbeat-consonant, one last time
     before the slack.
  III. The Slack — becalmed, the gallop stops: THE ISLAND IN MAJOR — the
     payoff the act has withheld — twice, on the island's own violin, with
     the stage cleared to pads and the choir beginning its final monotone
     rise.  Even melted, the island still hangs on degree 2.
  IV. Hull Down — the wind returns and crests (a verified crescendo), and
     then THE PALINDROME: one forward FUSION on the piano and, immediately
     after it, the full FUSION RETROGRADE — the road out and the road back
     as one audible mirror, the retrograde's only statement on the album.
     The plagal IV-I lands (bass G to D), the full ensemble holds its
     D-major chord, a seashore swells beneath (one held key, started before
     the bells so it legally rings through), and TEN TOLLS widen into the
     wash while CC11 carries everything below the horizon.  The sea sounds
     last.

The one-boat law: the two THEME-CARRYING channels (island violin, mainland
strings) both sit at centre (64) — one point on a wide sea — while the
accompaniment holds a pinned symmetric seating plan around them (steel 54 /
brass 74, pan flute 48 / flute 80, glockenspiel 58 / bells 70) so the
album's fullest track is anything but mono.  Every recurring datum is
single-sourced from material.py.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 10
TITLE = "Out on the Tide"
FILE = "10 - Out on the Tide.mid"
SEED = 202607190
COMMENT = (
    "Out on the Tide - the second crossing: both voices leave together at "
    "low water and the album ends on open sea.  A pan flute alone breathes "
    "the sail figure, then the dawn assembly: piano pump, singing bass, "
    "steel jangle, brass, bells, timpani, the glockenspiel tapping SAIL in "
    "Morse.  The Boarding gallops through the act-two medley - the flood "
    "bell, the noon fall, the gale riff and the road-home head all return "
    "over the pump - and the shores overlap one last time.  The Slack "
    "clears the stage and the island theme finally turns MAJOR, still "
    "hanging on its second degree.  Hull Down crests, then the palindrome: "
    "the fusion phrase forward and immediately backward - the road out and "
    "the road back as one mirror - into a plagal IV-I, a held D-major "
    "chord, a seashore swelling beneath, and ten bell tolls widening into "
    "the wash as everything sails below the horizon.  The sea sounds last.")

# ---------------------------------------------------------------------------
# Channels and the one-boat seating.
# ---------------------------------------------------------------------------

CH_PIANO, CH_BASS, CH_STEEL, CH_BRASS = 0, 1, 2, 3
CH_MSTRING, CH_IVIOLIN, CH_CHOIR, CH_PANFL = 4, 5, 6, 7
CH_FLUTE, CH_DRUMS, CH_BELLS, CH_GLOCK = 8, 9, 10, 11
CH_TIMP, CH_SEA = 12, 13

BOAT_PAN = material.SHORE_PANS[NUMBER]                  # (64, 64) — one boat
SYM_SEATS = {CH_STEEL: 54, CH_BRASS: 74, CH_PANFL: 48, CH_FLUTE: 80,
             CH_GLOCK: 58, CH_BELLS: 70}
TONIC_PC = material.convergence_pcs(NUMBER)[0]          # 2 — D, home

_MJ = material.MODE_MAJOR
_MM = material.MODE_MINOR

# --- the movement grid ---
HERALD_T1 = 8.0                     # the inhale: pan flute ALONE in [0, 8)
I_END = 112.0                       # Eight Bells (assembly)
II_T0, II_END = 112.0, 320.0        # The Boarding (gallop + medley)
III_T0, III_END = 320.0, 416.0      # The Slack (becalmed; the melting)
IV_T0, END = 416.0, 596.0           # Hull Down (palindrome, tolls, the sea)

# --- pinned geometry ---
HOOK_BASE_HERALD = en.n("D5")       # 74 — the sail, breathed
HOOK5_ECHO_T0 = 48.0                # Act One's pump call, unpinned colour
MORSE_T0 = 24.0                     # SAIL on the glockenspiel
MORSE_PITCH = en.n("D6")            # 86

CHORUS_SPANS = [(144.0, 176.0), (272.0, 304.0)]
BASS_HOOK_T0S = [148.0, 164.0, 276.0, 292.0]            # HOOK10 in the bass
MEDLEY = [(6, CH_BELLS, 192.0, en.n("D4")),      # the flood bell, ON bells
          (7, CH_FLUTE, 208.0, en.n("A5")),
          (8, CH_STEEL, 224.0, en.n("B3")),
          (9, CH_FLUTE, 240.0, en.n("D5"))]
OVERLAP_T0 = 256.0                  # island + mainland, one last time, in D

MAJOR_T0S = [336.0, 368.0]          # THE MELTING: island in major (violin)
WIND_T0 = 404.0                     # hook10 on the flute — the wind returns

CRESC_LO, CRESC_HI = 416.0, 500.0   # the verified crescendo window
FUSION_T0 = 520.0                   # the palindrome: forward...
RETRO_T0 = 528.0                    # ...and straight back (adjacent)
FINAL_DOWNBEAT = 544.0              # the plagal landing (bass G -> D)
SEA_T0, SEA_DUR = 544.0, 48.0       # the seashore: rings through the bells
TOLL_T0 = 548.0                     # ten tolls, widening into the wash
TOLL_PITCH = en.n("D4")             # 62 — pc 2
FADE_LO, FADE_HI = 544.0, 592.0     # CC11 carries the band below the horizon

THEME_BASE = en.n("D4")             # 62 — island, mainland, fusion, retro
BASS_HOOK_PITCH = en.n("D2")        # 38 (+9 -> 47, +12 -> 50)

# --- the tide, breathing everywhere; the deepest swell is the last ---

TEMPO_MAP = (
    material.tide_breath(96.0, 0.0, I_END, period=32.0, depth=4.0)
    + material.tide_breath(100.0, II_T0, II_END, period=32.0, depth=4.0)
    + material.tide_breath(92.0, III_T0, III_END, period=32.0, depth=5.0)
    + material.tide_breath(98.0, IV_T0, END, period=32.0, depth=6.0))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Eight Bells", 0.0, I_END),
               ("II. The Boarding", II_T0, II_END),
               ("III. The Slack", III_T0, III_END),
               ("IV. Hull Down", IV_T0, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 2, 0)],                       # D major
    channels=[(CH_PIANO, "piano", 0, 92, 64, 40),
              (CH_BASS, "bass", 33, 90, 64, 26),
              (CH_STEEL, "steel guitar", 25, 82, SYM_SEATS[CH_STEEL], 40),
              (CH_BRASS, "brass", 61, 84, SYM_SEATS[CH_BRASS], 46),
              (CH_MSTRING, "mainland strings", 48, 84, BOAT_PAN[1], 52),
              (CH_IVIOLIN, "island violin", 40, 86, BOAT_PAN[0], 52),
              (CH_CHOIR, "choir", 52, 82, 64, 58),
              (CH_PANFL, "pan flute", 75, 80, SYM_SEATS[CH_PANFL], 48),
              (CH_FLUTE, "flute", 73, 80, SYM_SEATS[CH_FLUTE], 44),
              (CH_DRUMS, "kit", 0, 86, 64, 30),
              (CH_BELLS, "tubular bells", 14, 88, SYM_SEATS[CH_BELLS], 56),
              (CH_GLOCK, "glockenspiel", 9, 78, SYM_SEATS[CH_GLOCK], 42),
              (CH_TIMP, "timpani", 47, 84, 64, 48),
              (CH_SEA, "the sea", 122, 74, 64, 30)],
    extra_markers=[(MORSE_T0, "eight bells"), (192.0, "the medley"),
                   (OVERLAP_T0, "both shores"), (MAJOR_T0S[0], "the melting"),
                   (FUSION_T0, "the road out"), (RETRO_T0, "the road back"),
                   (TOLL_T0, "ten bells"), (FADE_LO, "hull down")],
)

PROGRAM_WHITELIST = {0, 33, 25, 61, 48, 40, 52, 75, 73, 14, 9, 47, 122}
CENTERED_CHANNELS = {CH_PIANO, CH_BASS, CH_MSTRING, CH_IVIOLIN, CH_CHOIR,
                     CH_DRUMS, CH_TIMP, CH_SEA}
NOTE_RANGES = {
    CH_PIANO: (38, 86), CH_BASS: (33, 52), CH_STEEL: (50, 76),
    CH_BRASS: (48, 72), CH_MSTRING: (50, 76), CH_IVIOLIN: (55, 79),
    CH_CHOIR: (57, 76), CH_PANFL: (69, 91), CH_FLUTE: (67, 91),
    CH_BELLS: (57, 76), CH_GLOCK: (79, 96), CH_TIMP: (36, 50),
    CH_SEA: (60, 60),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (330.0, 430.0)                 # ~6:20 incl. the end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES sec.3 pattern).
# ---------------------------------------------------------------------------

_PPQ = en.PPQ
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}


def _note_ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []),
                              key=lambda e: (e[0], e[1])):
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


def _pitch_at(sc, ch, beat):
    return [p for on, off, p in _note_spans(sc, ch)
            if on - 1e-6 <= beat < off - 1e-6]


def _bar_sums(sc, lo, hi):
    out = {}
    for ch in sc.events:
        if ch == CH_DRUMS:
            continue
        for b, _p, v in _note_ons(sc, ch):
            if lo - 1e-6 <= b < hi:
                out[int(b // 4)] = out.get(int(b // 4), 0.0) + v
    return out


def _movement_events(lo, hi):
    return [(b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6]


# ---------------------------------------------------------------------------
# The gallop textures.  D-major bar chords cycle D-G-Bm-A; the pump plays
# root + fifth in the verses and root + OCTAVE exactly in the chorus spans
# (the octave-thickening IS the chorus event, and keeps the doubled-thumb
# out-of-span coverage honest).
# ---------------------------------------------------------------------------

_ROOTS = {"D": 38, "G": 43, "Bm": 47, "A": 45}
_TRIADS = {"D": [62, 66, 69], "G": [62, 67, 71], "Bm": [62, 66, 71],
           "A": [61, 64, 69]}
_CYCLE = ["D", "G", "Bm", "A"]


def _bar_name(bar: int) -> str:
    return _CYCLE[bar % 4]


def _in_chorus(t0: float) -> bool:
    return any(lo - 1e-6 <= t0 < hi for lo, hi in CHORUS_SPANS)


def _pump_bar(sc, t0, vel=72, jt=3):
    """Eight pump quavers: roots on the beats, fifth (verse) or octave
    (chorus) on the off-beats; the RH answers on the and-of-1 and and-of-3."""
    name = _bar_name(int(t0 // 4))
    root = _ROOTS[name]
    upper = root + (12 if _in_chorus(t0) else 7)
    for i in range(8):
        b = t0 + 0.5 * i
        j = 0 if b <= t0 + 0.1 else jt
        p = root if i % 2 == 0 else upper
        v = vel + (6 if i in (0, 5) else 0) - (4 if i % 2 else 0)
        sc.note(CH_PIANO, p, b, 0.5, v, jt=j, jv=3)
    for b, v in ((t0 + 1.5, vel - 8), (t0 + 3.5, vel - 12)):
        for p in _TRIADS[name]:
            sc.note(CH_PIANO, p, b, 0.45, v, jt=3, jv=3)
    en.sustain(sc, CH_PIANO, t0, t0 + 3.9)


def _kit_bar(sc, t0, vel=0, crash=False, jt=4):
    def d(key, b, v, dur=0.4):
        j = 0 if b <= t0 + 0.1 else jt
        sc.note(CH_DRUMS, key, b, dur, v + vel, jt=j, jv=3)
    d(36, t0, 84)
    d(36, t0 + 2.5, 74)
    d(38, t0 + 1.0, 80)
    d(38, t0 + 3.0, 84)
    for q in range(8):
        d(42, t0 + 0.5 * q, 34 + (6 if q % 2 == 0 else 0))
    if crash:
        d(49, t0, 88, dur=2.0)


def _fill_bar(sc, t0, jt=6):
    for i, key in enumerate((48, 47, 45, 41)):
        sc.note(CH_DRUMS, key, t0 + 2.0 + 0.5 * i, 0.4, 72 + 4 * i,
                jt=jt, jv=4)


_DSCALE = [33, 35, 36, 38, 40, 42, 43, 45, 47, 48, 50, 52]   # A1..E3, diatonic


def _bass_walk(sc, t0, t1, skip=()):
    """The protagonist stride: a stepwise triangle sweep of the D-major
    scale, one note per beat, pausing for the pinned hook statements."""
    idx, direction = 3, 1                        # start on D2, rising
    b = t0
    while b < t1 - 1e-6:
        if any(lo - 1e-6 <= b < hi for lo, hi in skip):
            b += 1.0
            continue
        sc.note(CH_BASS, _DSCALE[idx], b, 0.9, 66, jt=0, jv=2)
        if idx >= len(_DSCALE) - 1:
            direction = -1
        elif idx <= 0:
            direction = 1
        idx += direction
        b += 1.0


def _steel_bar(sc, t0, vel=54, jt=3):
    name = _bar_name(int(t0 // 4))
    ps = [p - 12 for p in _TRIADS[name]] + [_TRIADS[name][0]]
    for i, p in enumerate(ps + ps[1:3]):
        b = t0 + 0.5 * i
        j = 0 if b <= t0 + 0.1 else jt
        sc.note(CH_STEEL, p + 12, b, 0.5, vel + (4 if i == 0 else 0),
                jt=j, jv=3)


def _jangle_pair(sc, t0):
    """A CC68 hammer-on pair on the steel: pick one, slur the next."""
    sc.note(CH_STEEL, 66, t0, 0.5, 62, jt=0, jv=2)
    sc.cc(CH_STEEL, 68, 127, t0 + 0.45)
    sc.note(CH_STEEL, 69, t0 + 0.5, 0.6, 58, jt=0, jv=2)
    sc.cc(CH_STEEL, 68, 0, t0 + 1.2)


def _brass_stab(sc, t0, dur=1.2, vel=78):
    for p in (62, 66, 69):
        sc.note(CH_BRASS, p, t0, dur, vel, jt=0, jv=3)
    en.at_curve(sc, CH_BRASS, [(t0, 0), (t0 + dur * 0.5, 72),
                               (t0 + dur, 0)])


def _pad(sc, ch, t0, dur, pitches, vel=52, peak=84):
    for p in pitches:
        sc.note(ch, p, t0, dur, vel, jt=0, jv=2)
    en.expr_curve(sc, ch, [(t0, 40), (t0 + dur * 0.55, peak),
                           (t0 + dur, 34)], step=1.0)


# ---------------------------------------------------------------------------
# Herald + I. Eight Bells [0, 112) — the inhale, then the dawn assembly.
# ---------------------------------------------------------------------------

def _b_eight_bells(sc):
    # The herald: the pan flute ALONE breathes the sail, twice, rising.
    material.play_hook(sc, CH_PANFL, 0.5, HOOK_BASE_HERALD, 10, vel=52,
                       gate=0.98)
    material.play_hook(sc, CH_PANFL, 4.5, HOOK_BASE_HERALD, 10, vel=60,
                       gate=0.98)
    en.expr_curve(sc, CH_PANFL, [(0.0, 24), (4.0, 62), (7.9, 96)],
                  step=0.5)
    # Eight ship's-bells strikes: four ding-ding pairs across the assembly.
    for i in range(4):
        t0 = 10.5 + 4.0 * i
        sc.note(CH_BELLS, 62, t0, 0.45, 74, jt=0, jv=2)
        sc.note(CH_BELLS, 62, t0 + 0.5, 3.0, 70, jt=0, jv=2)
    # The assembly, additive: pump 8, bass 16, strings 24, brass 64, kit 80.
    for bar in range(2, 28):
        t0 = 4.0 * bar
        _pump_bar(sc, t0, vel=62 + min(8, bar // 4), jt=3)
    _bass_walk(sc, 16.0, 112.0)
    for t0 in (24.0, 40.0, 56.0, 72.0, 88.0):
        name = _bar_name(int(t0 // 4))
        _pad(sc, CH_MSTRING, t0, 16.0, [p - 0 for p in _TRIADS[name][:2]],
             vel=48, peak=76)
    # SAIL on the glockenspiel (pitch 86 is reserved for the Morse lane).
    material.play_morse(sc, CH_GLOCK, MORSE_T0, NUMBER, MORSE_PITCH, vel=62)
    # Act One's pump call drifts through, unpinned (the piano remembers).
    material.play_hook(sc, CH_PIANO, HOOK5_ECHO_T0, en.n("D5"), 5, vel=58,
                       gate=0.95)
    for t0 in (64.0, 80.0, 96.0):
        _brass_stab(sc, t0 + 2.5, dur=1.0, vel=66)
    for bar in range(20, 28):
        _kit_bar(sc, 4.0 * bar, vel=-14, crash=(bar == 20), jt=4)
    # The dawn roll: timpani under the last bars of the assembly.
    for i in range(16):
        sc.note(CH_TIMP, 38, 104.0 + 0.5 * i, 0.45, 36 + i, jt=0, jv=3)


# ---------------------------------------------------------------------------
# II. The Boarding [112, 320) — the gallop, the medley, the last overlap.
# ---------------------------------------------------------------------------

def _b_the_boarding(sc):
    hook_spans = [(t, t + 4.0) for t in BASS_HOOK_T0S]
    for bar in range(28, 80):
        t0 = 4.0 * bar
        boost = 8 if _in_chorus(t0) else 0
        _pump_bar(sc, t0, vel=70 + boost, jt=3)
        _kit_bar(sc, t0, vel=boost - 4, crash=(bar in (28, 36, 48, 68)),
                 jt=4)
        if bar % 8 == 7:
            _fill_bar(sc, t0)
        if not any(lo - 4.0 < t0 < hi for lo, hi in
                   [(222.0, 228.0)]):          # clear the gale-riff moment
            _steel_bar(sc, t0, vel=50 + boost // 2, jt=3)
    _bass_walk(sc, 112.0, 320.0, skip=hook_spans)
    # The protagonist sings the sail through both choruses.
    for t in BASS_HOOK_T0S:
        material.play_hook(sc, CH_BASS, t, BASS_HOOK_PITCH, 10, vel=76,
                           gate=0.95)
    # The doubled thumb: every chorus bass note shadowed at +12, tick-exact.
    # When the pump's own root already sounds that pitch on that beat, the
    # pump note IS the shadow — emitting a duplicate would knife-edge
    # check_overlaps, so we skip it and let the pump carry the double.
    for b, p, _v in list(_note_ons(sc, CH_BASS)):
        if _in_chorus(b):
            root = _ROOTS[_bar_name(int(b // 4))]
            if p + 12 == root and abs(b - round(b)) < 1e-6:
                continue
            sc.note(CH_PIANO, p + 12, b, 0.5, 62, jt=0, jv=2)
    # THE ACT-TWO MEDLEY: hooks 6, 7, 8, 9 over the running pump.
    for n, ch, t0, base in MEDLEY:
        material.play_hook(sc, ch, t0, base, n, vel=74, gate=0.96)
    # The jangle: CC68 hammer-on pairs on the arpeggio's rest beat.
    for t0 in (147.0, 155.0, 163.0, 171.0, 275.0, 283.0, 291.0, 299.0):
        _jangle_pair(sc, t0)
    # Brass warms through the gallop.
    for t0 in (128.0, 160.0, 186.0, 248.0, 268.0, 308.0):
        _brass_stab(sc, t0 + 2.5, dur=1.4, vel=74)
    # The shores overlap one last time before the slack — in D, together.
    material.play_island(sc, CH_IVIOLIN, OVERLAP_T0, THEME_BASE, vel=72,
                         gate=0.96)
    material.play_mainland(sc, CH_MSTRING, OVERLAP_T0, THEME_BASE, vel=72,
                           gate=0.97)
    en.expr_curve(sc, CH_IVIOLIN, [(OVERLAP_T0, 50), (OVERLAP_T0 + 5.0, 92),
                                   (OVERLAP_T0 + 8.0, 44)], step=0.5)
    en.expr_curve(sc, CH_MSTRING, [(OVERLAP_T0, 52), (OVERLAP_T0 + 5.0, 94),
                                   (OVERLAP_T0 + 8.0, 46)], step=0.5)
    # Strings pads elsewhere in the movement (clear of the statement).
    for t0 in (128.0, 176.0, 224.0, 288.0):
        name = _bar_name(int(t0 // 4))
        _pad(sc, CH_MSTRING, t0, 14.0, _TRIADS[name][:2], vel=46, peak=72)


# ---------------------------------------------------------------------------
# III. The Slack [320, 416) — becalmed: the gallop stops and the island
# theme finally turns MAJOR on its own violin, the stage cleared.
# ---------------------------------------------------------------------------

def _b_the_slack(sc):
    # The becalmed bed: chained string pads, no two same pitches adjacent.
    pads = [(320.0, 17.0, (62, 69)), (336.0, 17.0, (66, 71)),
            (352.0, 17.0, (62, 69)), (368.0, 17.0, (67, 71)),
            (384.0, 17.0, (62, 69)), (400.0, 16.0, (66, 74))]
    for t0, dur, ps in pads:
        _pad(sc, CH_MSTRING, t0, dur, ps, vel=44, peak=68)
    # THE MELTING: the island in major, twice, on the island's own violin.
    for t0 in MAJOR_T0S:
        material.play_island(sc, CH_IVIOLIN, t0, THEME_BASE, major=True,
                             vel=66, gate=0.97)
        en.expr_curve(sc, CH_IVIOLIN, [(t0, 44), (t0 + 5.5, 90),
                                       (t0 + 8.0, 40)], step=0.5)
        en.vibrato(sc, CH_IVIOLIN, t0 + 6.7, 1.2, depth=0.25)
    # Connective sighs between the two statements.
    sc.note(CH_IVIOLIN, 69, 348.0, 3.0, 52, jt=0, jv=2)
    sc.note(CH_IVIOLIN, 67, 352.0, 3.0, 50, jt=0, jv=2)
    sc.note(CH_IVIOLIN, 66, 356.0, 4.0, 48, jt=0, jv=2)
    # The choir begins its final monotone rise (58 -> 82 across the slack).
    for t0, val, ps in ((320.0, 58, (62, 66)), (344.0, 66, (64, 69)),
                        (368.0, 74, (62, 67)), (392.0, 82, (66, 69))):
        en.vowel(sc, CH_CHOIR, val, t0)
        _pad(sc, CH_CHOIR, t0, 20.0, ps, vel=46, peak=72)
    # The pan flute drifts two-note fragments of the sail (never a match).
    for t0 in (332.0, 364.0, 396.0):
        sc.note(CH_PANFL, 74, t0, 1.5, 44, jt=0, jv=2)
        sc.note(CH_PANFL, 83, t0 + 1.5, 2.5, 40, jt=0, jv=2)
    # The wind returns: the sail on the flute, and the slack is over.
    material.play_hook(sc, CH_FLUTE, WIND_T0, en.n("A4"), 10, vel=64,
                       gate=0.97)
    en.expr_curve(sc, CH_FLUTE, [(WIND_T0, 40), (WIND_T0 + 3.0, 86),
                                 (WIND_T0 + 4.0, 60)], step=0.5)


# ---------------------------------------------------------------------------
# IV. Hull Down [416, 596) — the crest, the palindrome, the plagal landing,
# ten widening tolls, and the sea.
# ---------------------------------------------------------------------------

def _b_hull_down(sc):
    # The wind fills the sails: pump and kit resume and CREST.
    for bar in range(104, 129):                  # 416 .. 512
        t0 = 4.0 * bar
        vel = 66 + min(18, (bar - 104))
        _pump_bar(sc, t0, vel=vel, jt=3)
        _kit_bar(sc, t0, vel=min(10, (bar - 104) // 2) - 4,
                 crash=(bar in (104, 112, 120, 128)), jt=4)
        if bar % 8 == 7:
            _fill_bar(sc, t0)
        if bar < 125:
            _steel_bar(sc, t0, vel=50 + min(12, bar - 104), jt=3)
    _kit_bar(sc, 516.0, vel=4, crash=False, jt=4)
    for bar in (130, 131, 132, 133):             # 520-536: heartbeat kit only
        sc.note(CH_DRUMS, 36, 4.0 * bar, 0.4, 58, jt=0, jv=2)
        sc.note(CH_DRUMS, 36, 4.0 * bar + 2.5, 0.4, 50, jt=0, jv=2)
    sc.note(CH_DRUMS, 36, 536.0, 0.4, 54, jt=0, jv=2)
    sc.note(CH_DRUMS, 36, 540.0, 0.4, 56, jt=0, jv=2)
    sc.note(CH_DRUMS, 49, FINAL_DOWNBEAT, 4.0, 92, jt=0, jv=2)
    _bass_walk(sc, 416.0, 536.0)
    # Brass, strings, bells, glock, timpani, flutes layer INTO the crest.
    for t0 in (432.0, 464.0):
        _brass_stab(sc, t0 + 2.5, dur=1.6, vel=78)
    for p in (62, 66, 69):
        sc.note(CH_BRASS, p, 496.0, 16.0, 74, jt=0, jv=2)
    en.at_curve(sc, CH_BRASS, [(496.0, 0), (504.0, 84), (512.0, 20)])
    for t0, dur, ps in ((416.0, 16.0, (62, 69)), (448.0, 16.0, (66, 71)),
                        (480.0, 16.0, (62, 69, 74))):
        _pad(sc, CH_MSTRING, t0, dur, ps, vel=50 + (8 if t0 >= 480 else 0),
             peak=90)
    _pad(sc, CH_MSTRING, 512.0, 31.5, (62, 66), vel=44, peak=64)
    for t0, p in ((480.0, 62), (488.0, 69), (496.0, 74), (504.0, 62),
                  (512.0, 69)):
        sc.note(CH_BELLS, p, t0, 6.0, 76, jt=0, jv=2)
    for i, p in enumerate((81, 84, 88, 91, 88, 84)):
        sc.note(CH_GLOCK, p, 482.0 + 4.0 * i, 1.5, 58, jt=0, jv=3)
    for i in range(16):
        sc.note(CH_TIMP, 38, 492.0 + 0.5 * i, 0.45, 44 + 2 * i, jt=0, jv=3)
    # The violin and flutes fly the crest line.
    for t0, p in ((480.0, 69), (484.0, 74), (488.0, 78), (492.0, 74),
                  (496.0, 76), (500.0, 74), (504.0, 71), (508.0, 69)):
        sc.note(CH_IVIOLIN, p, t0, 3.8, 66, jt=0, jv=2)
    en.expr_curve(sc, CH_IVIOLIN, [(480.0, 56), (500.0, 96), (514.0, 50)],
                  step=1.0)
    for t0, p in ((484.0, 81), (492.0, 86), (500.0, 83), (508.0, 79)):
        sc.note(CH_PANFL, p, t0, 3.5, 56, jt=0, jv=2)
    # The choir's rise continues through the crest (86 -> 104 by the chord).
    for t0, val, ps, dur in ((416.0, 86, (62, 66), 16.0),
                             (448.0, 90, (64, 69), 16.0),
                             (480.0, 94, (66, 71), 16.0),
                             (512.0, 98, (62, 67), 30.0)):
        en.vowel(sc, CH_CHOIR, val, t0)
        _pad(sc, CH_CHOIR, t0, dur, ps, vel=50, peak=88)
    # THE PALINDROME: the road out, then the road back — piano alone above
    # the held bed.  The retrograde's only statement on the album.
    en.sustain(sc, CH_PIANO, 520.0, 535.5)
    material.play_fusion(sc, CH_PIANO, FUSION_T0, THEME_BASE, vel=82,
                         gate=0.97)
    material.play_fusion(sc, CH_PIANO, RETRO_T0, THEME_BASE, retro=True,
                         vel=78, gate=0.97)
    # The plagal letter-close, and THE CHORD at the landing.
    sc.note(CH_BASS, 43, 538.0, 1.8, 62, jt=0, jv=2)
    sc.note(CH_BASS, 43, 540.0, 3.5, 64, jt=0, jv=2)
    sc.note(CH_BASS, 38, FINAL_DOWNBEAT, 4.0, 70, jt=0, jv=2)
    for p in (50, 62, 66, 69, 74):
        sc.note(CH_PIANO, p, FINAL_DOWNBEAT, 44.0, 72, jt=0, jv=2)
    en.sustain(sc, CH_PIANO, FINAL_DOWNBEAT, FINAL_DOWNBEAT + 44.0)
    for ch, ps in ((CH_MSTRING, (62, 66, 69, 74)), (CH_BRASS, (62, 66, 69)),
                   (CH_CHOIR, (62, 66, 69, 74)), (CH_STEEL, (66, 71)),
                   (CH_IVIOLIN, (74,))):
        for p in ps:
            sc.note(ch, p, FINAL_DOWNBEAT, 46.0, 64, jt=0, jv=2)
    en.vowel(sc, CH_CHOIR, 104, FINAL_DOWNBEAT)
    sc.note(CH_BELLS, 62, FINAL_DOWNBEAT, 3.9, 78, jt=0, jv=2)
    sc.note(CH_TIMP, 38, FINAL_DOWNBEAT, 4.0, 72, jt=0, jv=2)
    # The sea, started before the bells so it legally rings through.
    sc.note(CH_SEA, 60, SEA_T0, SEA_DUR, 66, jt=0, jv=0)
    en.expr_curve(sc, CH_SEA, [(SEA_T0, 60), (SEA_T0 + 12.0, 96),
                               (FADE_HI, 70)], step=1.0)
    # TEN TOLLS, widening into the wash.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, widen=0.15)
    # Hull down: CC11 carries the band below the horizon.  The fades are
    # the ending — the music never stops playing, it just gets farther away.
    for ch in (CH_MSTRING, CH_CHOIR, CH_BRASS, CH_STEEL, CH_IVIOLIN,
               CH_PIANO):
        en.expr_curve(sc, ch, [(FADE_LO + 0.5, 100), (568.0, 46),
                               (FADE_HI, 8)], step=1.0)


BUILDERS = [_b_eight_bells, _b_the_boarding, _b_the_slack, _b_hull_down]

_TIDE_TABLE = [("I. Eight Bells", 0.0, I_END, 96.0, 4.0),
               ("II. The Boarding", II_T0, II_END, 100.0, 4.0),
               ("III. The Slack", III_T0, III_END, 92.0, 5.0),
               ("IV. Hull Down", IV_T0, END, 98.0, 6.0)]


# ---------------------------------------------------------------------------
# Track oracles — every promise above, machine-checked.
# ---------------------------------------------------------------------------

def oracles(sc, info, spans):
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    maj = material.theme_statements(sc, "island_major")
    fus = material.theme_statements(sc, "fusion")
    ret = material.theme_statements(sc, "fusion_retro")

    def o_convergence():
        fails = []
        if not isl or any(material.island_tonic_pc(s[3]) != TONIC_PC
                          for s in isl):
            fails.append(f"island statements must all imply D ({isl})")
        if not mnl or any(material.mainland_tonic_pc(s[3]) != TONIC_PC
                          for s in mnl):
            fails.append(f"mainland statements must all imply D ({mnl})")
        if any(material.island_tonic_pc(s[3]) != TONIC_PC for s in maj):
            fails.append("the melted island must stay in D")
        return fails

    def o_overlap():
        pairs = material.overlapping_pairs(isl, mnl)
        if not pairs:
            return ["no island+mainland overlap (Act Two requires it)"]
        fails = []
        for a, b in pairs:
            lo, hi = max(a[1], b[1]), min(a[2], b[2])
            beat = math.ceil(lo / 4.0) * 4.0
            while beat < hi - 1e-6:
                for pa in _pitch_at(sc, a[0], beat):
                    for pb in _pitch_at(sc, b[0], beat):
                        if abs(pa - pb) % 12 not in _CONSONANT:
                            fails.append(f"overlap dissonant at {beat}: "
                                         f"{pa} vs {pb}")
                beat += 4.0
        return fails

    def o_medley():
        fails = []
        for n, _ch, _t0, _base in MEDLEY:
            hits = [h for h in material.hook_statements_unnested(sc, n)
                    if II_T0 - 1e-6 <= h[1] < II_END]
            if not hits:
                fails.append(f"hook {n} missing from the medley movement")
        if any(s[1] < IV_T0 for s in fus + ret):
            fails.append("the medley movement must stay fusion-free "
                         "(fusion lives in IV only)")
        return fails

    def o_palindrome():
        fails = []
        if not fus or any(s[0] != CH_PIANO or s[1] < IV_T0 for s in fus):
            fails.append(f"forward fusion must live on the piano in IV "
                         f"({fus})")
        if len(ret) != 1 or ret[0][0] != CH_PIANO or \
                abs(ret[0][1] - RETRO_T0) > 0.1:
            fails.append(f"the road back must be walked exactly once, "
                         f"piano, at {RETRO_T0} ({ret})")
        if fus and ret and not any(abs(ret[0][1] - f[2]) <= 1.0
                                   for f in fus):
            fails.append("the retrograde must follow a forward fusion "
                         "immediately (the palindrome)")
        return fails

    def o_melting():
        if not maj:
            return ["the island never turns major (T10's payoff)"]
        bad = [s for s in maj
               if s[0] != CH_IVIOLIN or not
               III_T0 - 1e-6 <= s[1] < III_END]
        return [] if not bad else [f"the melting belongs to the violin in "
                                   f"the slack ({bad})"]

    def o_hook_density():
        n = len(material.hook_statements_unnested(sc, 10))
        return [] if n >= 6 else [f"HOOK10 unnested density {n} < 6"]

    def o_bass():
        ons = _note_ons(sc, CH_BASS)
        if len(ons) < 40:
            return [f"only {len(ons)} bass notes"]
        deltas = [abs(b[1] - a[1]) for a, b in zip(ons, ons[1:])]
        ratio = sum(1 for d in deltas if 1 <= d <= 2) / len(deltas)
        fails = []
        if ratio < 0.50:
            fails.append(f"bass stepwise ratio {ratio:.2f} < 0.50")
        span = max(p for _b, p, _v in ons) - min(p for _b, p, _v in ons)
        if span < 19:
            fails.append(f"bass range {span} < 19")
        hooks = [h for h in material.find_statements(
                     material.note_ons(sc, CH_BASS), material.HOOKS[10])
                 if _in_chorus(h[0])]
        if len(hooks) < 2:
            fails.append(f"bass sings the sail {len(hooks)}x in the "
                         f"choruses, want >= 2")
        return fails

    def o_thumb():
        piano = {round(b * _PPQ): set() for b, _p, _v in
                 _note_ons(sc, CH_PIANO)}
        for b, p, _v in _note_ons(sc, CH_PIANO):
            piano.setdefault(round(b * _PPQ), set()).add(p)
        bass = _note_ons(sc, CH_BASS)

        def covered(b, p):
            t = round(b * _PPQ)
            return any(p + 12 in piano.get(t + dt, ())
                       for dt in range(-10, 11))
        inside = [(b, p) for b, p, _v in bass if _in_chorus(b)]
        outside = [(b, p) for b, p, _v in bass if not _in_chorus(b)]
        cov_in = sum(1 for b, p in inside if covered(b, p)) / \
            max(1, len(inside))
        cov_out = sum(1 for b, p in outside if covered(b, p)) / \
            max(1, len(outside))
        fails = []
        if cov_in < 0.80:
            fails.append(f"thumb coverage {cov_in:.2f} in the choruses")
        if cov_out >= 0.30:
            fails.append(f"thumb leaks outside the choruses "
                         f"({cov_out:.2f})")
        return fails

    def o_herald():
        fails = []
        for ch in sc.events:
            if ch == CH_PANFL:
                continue
            early = [b for b, _p, _v in _note_ons(sc, ch)
                     if b < HERALD_T1 - 1e-6]
            if early:
                fails.append(f"ch{ch} sounds inside the herald window "
                             f"({early[:2]})")
        hits = [h for h in material.find_statements(
                    material.note_ons(sc, CH_PANFL), material.HOOKS[10])
                if h[0] < HERALD_T1]
        if not hits:
            fails.append("the herald never breathes the sail")
        lane = [v for b, v in _cc_lane(sc, CH_PANFL, 11)
                if b < HERALD_T1 - 1e-6]
        if lane != sorted(lane) or len(set(lane)) < 4:
            fails.append("the herald swell must rise")
        return fails

    def o_morse():
        taps = [(b, v) for b, p, v in _note_ons(sc, CH_GLOCK)
                if p == MORSE_PITCH]
        want = [MORSE_T0 + on for on, _du in material.morse_rhythm(
            material.MORSE_WORDS[NUMBER])]
        if len(taps) != len(want) or \
                any(abs(b - w) > 1e-6 for (b, _v), w in zip(taps, want)):
            return [f"SAIL grid mismatch on the glockenspiel "
                    f"({len(taps)} taps, want {len(want)})"]
        return []

    def o_vowel():
        lane = _cc_lane(sc, CH_CHOIR, 70)
        rise = [(b, v) for b, v in lane if b >= III_T0 - 1e-6]
        fails = []
        if not rise or [v for _b, v in rise] != \
                sorted(v for _b, v in rise):
            fails.append("the final rise must be monotone")
        if not rise or max(v for _b, v in rise) < material.VOWEL_FLOOR_T10:
            fails.append(f"the choir never reaches "
                         f"{material.VOWEL_FLOOR_T10}")
        if any(v > material.VOWEL_CAPS[NUMBER] for _b, v in lane):
            fails.append("vowel over the cap")
        return fails

    def o_tide():
        fails = []
        spreads = {}
        for name, lo, hi, base, depth in _TIDE_TABLE:
            evs = _movement_events(lo, hi)
            vals = [bpm for _b, bpm in evs]
            if len(evs) < 8:
                fails.append(f"'{name}': only {len(evs)} tempo events")
                continue
            troughs = [v for v in vals if v <= base - depth + 0.5]
            if len(troughs) < 2:
                fails.append(f"'{name}' does not breathe")
            spreads[name] = max(vals) - min(vals)
        if spreads and spreads.get("IV. Hull Down", 0) != max(
                spreads.values()):
            fails.append("the deepest swell must be the last")
        return fails

    def o_crescendo():
        sums = _bar_sums(sc, CRESC_LO, CRESC_HI)

        def mean(lo, hi):
            bars = range(int(lo // 4), int(hi // 4))
            return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))
        a, b, c = (mean(416.0, 444.0), mean(444.0, 472.0),
                   mean(472.0, 500.0))
        return [] if a < b < c else [
            f"the crest must build: {a:.0f}, {b:.0f}, {c:.0f}"]

    def o_fade():
        fails = []
        for ch in (CH_MSTRING, CH_CHOIR, CH_BRASS):
            lane = [v for b, v in _cc_lane(sc, ch, 11)
                    if FADE_LO + 0.25 <= b <= FADE_HI + 1e-6]
            if len(lane) < 4 or lane != sorted(lane, reverse=True):
                fails.append(f"ch{ch} does not sail below the horizon")
            elif lane[0] - lane[-1] < 40:
                fails.append(f"ch{ch} fade too shallow")
        return fails

    def o_jangle():
        lane = _cc_lane(sc, CH_STEEL, 68)
        ons = sum(1 for _b, v in lane if v >= 64)
        offs = sum(1 for _b, v in lane if v < 64)
        return [] if ons >= 4 and offs >= 4 else [
            f"jangle pairs {ons} on / {offs} off, want >= 4 each"]

    def o_brass_at():
        n = sum(1 for _t, _p, d in sc.events.get(CH_BRASS, [])
                if (d[0] & 0xF0) == 0xD0)
        return [] if n >= 12 else [f"only {n} brass aftertouch events"]

    def o_plagal():
        return material.plagal_final_failures(sc, CH_BASS, FINAL_DOWNBEAT,
                                              TONIC_PC)

    def o_one_boat():
        fails = []
        for ch in (CH_MSTRING, CH_IVIOLIN):
            vals = {v for _b, v in _cc_lane(sc, ch, 10)}
            if vals != {64}:
                fails.append(f"theme ch{ch} must hold the boat's centre "
                             f"({vals})")
        for a, b in ((CH_STEEL, CH_BRASS), (CH_PANFL, CH_FLUTE),
                     (CH_GLOCK, CH_BELLS)):
            va = {v for _b, v in _cc_lane(sc, a, 10)}
            vb = {v for _b, v in _cc_lane(sc, b, 10)}
            if len(va) != 1 or len(vb) != 1 or \
                    next(iter(va)) + next(iter(vb)) != 128:
                fails.append(f"ch{a}/ch{b} seats not symmetric "
                             f"({va}, {vb})")
        return fails

    def o_tolls_and_sea():
        fails = []
        tolls = [(b, p) for b, p, _v in _note_ons(sc, CH_BELLS)
                 if b >= TOLL_T0 - 1e-6]
        if len(tolls) != material.TOLLS[NUMBER]:
            fails.append(f"{len(tolls)} tolls, want "
                         f"{material.TOLLS[NUMBER]}")
        if any(p % 12 != TONIC_PC for _b, p in tolls):
            fails.append("the buoy must toll the D")
        gaps = [b2 - b1 for (b1, _), (b2, _) in zip(tolls, tolls[1:])]
        lo, hi = material.TOLL_SPACING
        if any(not lo - 1e-6 <= g <= hi + 1e-6 for g in gaps):
            fails.append(f"toll gaps outside {material.TOLL_SPACING}")
        if gaps != sorted(gaps):
            fails.append("the tolls must WIDEN into the wash")
        for ch in sc.events:
            if ch == CH_BELLS:
                continue
            late = [b for b, _p, _v in _note_ons(sc, ch)
                    if b >= TOLL_T0 - 1e-6]
            if late:
                fails.append(f"ch{ch} sounds a new onset after the first "
                             f"toll ({late[:2]})")
        sea = _note_spans(sc, CH_SEA)
        if len(sea) != 1 or sea[0][0] >= TOLL_T0 or \
                (tolls and sea[0][1] < tolls[-1][0]):
            fails.append(f"the sea must hold one key from before the "
                         f"bells to beyond the last toll ({sea})")
        return fails

    return [
        ("convergence", o_convergence()),
        ("overlap", o_overlap()),
        ("medley", o_medley()),
        ("palindrome", o_palindrome()),
        ("the_melting", o_melting()),
        ("hook_density", o_hook_density()),
        ("protagonist_bass", o_bass()),
        ("doubled_thumb", o_thumb()),
        ("breath_herald", o_herald()),
        ("morse_sail", o_morse()),
        ("vowel_floor", o_vowel()),
        ("tide_breath", o_tide()),
        ("crescendo", o_crescendo()),
        ("distance_fade", o_fade()),
        ("cc68_jangle", o_jangle()),
        ("brass_aftertouch", o_brass_at()),
        ("plagal_final", o_plagal()),
        ("one_boat", o_one_boat()),
        ("tolls_and_sea", o_tolls_and_sea()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (RATIO checks only — repo law).  Calibrated after render.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    early = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(416.0, 444.0))
    crest = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(472.0, 500.0))
    slack = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(330.0, 400.0))
    boarding = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(144.0, 304.0))
    tail = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(576.0, 592.0))

    def c_crest():
        gain = ctx.db(crest) - ctx.db(early)
        return [] if gain >= 2.0 else [
            f"the crest only gains {gain:.2f} dB"]

    def c_becalmed():
        drop = ctx.db(boarding) - ctx.db(slack)
        return [] if drop >= 2.0 else [
            f"the slack only {drop:.2f} dB below the boarding"]

    def c_sea():
        drop = ctx.db(crest) - ctx.db(tail)
        return [] if drop >= 6.0 else [
            f"the wash only {drop:.2f} dB below the crest"]

    return [
        ("audio_crest_builds", c_crest()),
        ("audio_slack_becalmed", c_becalmed()),
        ("audio_sea_takes_it", c_sea()),
    ]
