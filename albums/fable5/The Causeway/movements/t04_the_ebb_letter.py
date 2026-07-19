"""movements/t04_the_ebb_letter.py — track 4 of *The Causeway*.

THE EBB LETTER.  The album's darkest hour and its emotional pivot — the
Visitors centrepiece: ice outside a winter window, one candle inside.  A
minor throughout; the shores are two semitones apart now (the strait has
narrowed to a whole tone).  Three movements, a candle framing a slab of ice:

  I. Candle       — 6/8, ~66 with a deep fermata rubato (dips to ~48): the
     piano under una corda (CC67) with a low pedal caught by the sostenuto
     (CC66), a cello sighing bend-appoggiaturas over channel-aftertouch
     swells, a sealed choir and a warm pad.  The ISLAND THEME is stated twice
     in A minor (convergence pc 9), each still hanging on degree 2 — the
     letter never signs off.
  II. The Ice     — 4/4, EXACTLY ONE tempo event (120, metronomic): the album's
     pinned still point, and the rubato either side makes the stillness audible.
     HOOK4 (the ice-arp, 16ths) on FM EP over a synth-bass pulse, with THE
     ROTATION: one pitch of the four-note cell mutates per cycle on a pinned
     schedule, a pure anchor cell stated between the mutated ones.  A sweep pad
     arcs its filter (CC74).  THE REACHING: the mainland tries to arrive on the
     french horn in G (distance 2) — three statements of 4, then 7, then 9 of
     its 10 notes, each stopping short (growth, not erosion — the album reaches,
     The Remaining lost).  A kalimba taps EBB in Morse.
  III. Wax        — 6/8 returns, slower (~56 dipping to ~46); the choir opens a
     little (still <= 55), the island theme's last pre-dawn statement, a modal
     iv-i cadence to A, and exactly four bell tolls on the island's A — nothing
     sounds after them.

EXEMPTIONS (album law — the ballad is exempt; documented, not silently
skipped): this track carries NO protagonist-bass, NO doubled-thumb and NO
breath-herald oracle.  The tide-breath governs movements I and III (deep, with
fermata dips); movement II is the metronomic still point and owns its own
tempo oracle instead.  There is no simultaneity to guard because the mainland
never completes a statement here — it only reaches — so island and mainland
can never overlap.  Every recurring datum is single-sourced from material.py
(the two themes, HOOK4, the convergence pcs, the morse word EBB, the tide
breath, the shore pans, the vowel cap, the tolls, the cadence law).
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 4
TITLE = "The Ebb Letter"
FILE = "04 - The Ebb Letter.mid"
SEED = 202607184
COMMENT = (
    "The Ebb Letter - the album's darkest hour, the Visitors centrepiece: ice "
    "outside a winter window, one candle inside.  A minor.  A 6/8 candle - "
    "piano under una corda and sostenuto, a cello sighing bend-appoggiaturas "
    "with aftertouch swells, a sealed choir - states the island theme twice, "
    "each hanging on its second degree; then the ice, a 4/4 still point locked "
    "at 120 where an FM-EP ice-arp mutates one pitch per cycle over a synth-bass "
    "pulse and a filter-swept pad, and the mainland reaches three times on a "
    "french horn in G - four notes, then seven, then nine of ten - each falling "
    "short while a kalimba taps EBB; then the wax, the 6/8 returning slower, the "
    "island theme's last pre-dawn reading, a modal cadence and four bells "
    "tolling the island's A.")

# ---------------------------------------------------------------------------
# Channels.  The island pole (the ice, the Enigma weather) sits left at
# SHORE_PANS[4][0]=54; the mainland pole (the reaching horn) sits right at 74;
# the intimate spine (piano, cello, the morse kalimba, the bells) holds 64.
# There is no drum kit - the ice is a sequencer, not a groove; channel 9 is
# left silent.
# ---------------------------------------------------------------------------

CH_PIANO, CH_CELLO, CH_CHOIR, CH_EP = 0, 1, 2, 3
CH_SYNBASS, CH_SWEEP, CH_HORN, CH_KALIMBA = 4, 5, 6, 7
CH_BELLS, CH_PAD = 8, 10

_MM = material.MODE_MINOR                   # aeolian - A natural minor
_MJ = material.MODE_MAJOR                   # ionian - the mainland's G reach

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]         # (54, 74)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 9, 7

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 108.0                               # 36 bars of 6/8 (3 beats each)
II_END = 300.0                              # 48 bars of 4/4
END = 366.0                                 # 22 bars of 6/8

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE = en.n("A3")                    # 57 - the island tonic (deg 1)
ISLAND_STMT1_T0, ISLAND_STMT2_T0 = 18.0, 78.0
ISLAND_STMT_STR = 1.25                      # the candle's spacious rubato
WAX_THEME_T0, WAX_THEME_STR = 312.0, 1.5    # movement III, the last reading

# The mainland reaches three times on the horn in G, never completing (counts
# 4, 7, 9 of 10) - growth, not erosion.  jt=0 via material.play_mainland.
MAINLAND_BASE = en.n("G3")                  # 55 - the far shore in G, distance 2
REACHING = [(140.0, 4), (184.0, 7), (232.0, 9)]
REACH_STR = 1.5

MORSE_T0 = 116.0
MORSE_PITCH = en.n("E5")                    # 76 - the kalimba's fixed tap
TOLL_T0 = 356.0
TOLL_PITCH = en.n("A4")                     # 69 - pc 9 = the island tonic A
TOLL_SPACING = 2.5

# --- the ice sequencer (movement II) ---
ICE_T0, ICE_T1 = 108.0, 300.0
ICE_ROOT = en.n("A4")                       # 69 - the glassy ice-arp root
ICE_CELL = [s for _o, _d, s in material.HOOKS[NUMBER]]   # [0, 7, 14, 15]
# THE ROTATION.  One pitch of the four-note cell mutates each cycle; the index
# rotates 3->2->1->0 and every new offset is diatonic to A minor (scale
# offsets 0,2,3,5,7,8,10,12,14,15,17,19).  A cycle is one 4/4 bar; the mutated
# cell sits on beat 1, a pure anchor cell on beat 3 (the base still registers).
ICE_SCHED_BARS = [4, 8, 12, 16, 20, 24, 28, 32]      # bars into movement II
ICE_ROTATION = [(3, 17), (2, 12), (1, 8), (0, 2),
                (3, 14), (2, 15), (1, 10), (0, 3)]

# --- the withheld cadence: the cello resolves to A modally (iv-i), G# banned ---
CAD_WINDOWS = [(102.0, 108.0, 105.0),        # I: the candle settles (iv-i)
               (350.0, 356.0, 354.0)]        # III: the wax cadence (iv-i)

# --- the tide-breath tempo map: I and III breathe with deep fermata dips,
#     II is the metronomic still point (exactly one tempo event) ---


def _fermata_map(base, t0, t1, dips, period=24.0, depth=5.0):
    """A tide-breath swell deepened by explicit fermata dips at phrase ends
    (below the tide's own +-depth, to ~48/46) - the deep candle rubato.  The
    dip beats are chosen off the tide grid (period/4 = 6) so none collide."""
    return sorted(material.tide_breath(base, t0, t1, period=period,
                                       depth=depth) + list(dips))


TEMPO_MAP = (
    _fermata_map(66.0, 0.0, I_END, [(21.0, 48.0), (45.0, 48.0),
                                    (69.0, 48.0), (93.0, 48.0)])
    + [(I_END, 120.0)]                       # the ice: the pinned still point
    + _fermata_map(56.0, II_END, END, [(321.0, 46.0), (345.0, 46.0)]))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Candle", 0.0, I_END),
               ("II. The Ice", I_END, II_END),
               ("III. Wax", II_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 6, 8), (I_END, 4, 4), (II_END, 6, 8)],
    keysigs=[(0.0, 0, 1)],                   # A minor: no accidentals, minor
    channels=[(CH_PIANO, "piano", 0, 92, 64, 42),
              (CH_CELLO, "cello", 42, 90, 64, 55),
              (CH_CHOIR, "choir", 52, 74, ISL_PAN, 70),
              (CH_EP, "fm ep", 5, 82, ISL_PAN, 40),
              (CH_SYNBASS, "synth bass", 39, 86, ISL_PAN, 20),
              (CH_SWEEP, "sweep pad", 95, 74, ISL_PAN, 75),
              (CH_HORN, "french horn", 60, 84, MAIN_PAN, 88),
              (CH_KALIMBA, "kalimba", 108, 82, 64, 40),
              (CH_BELLS, "tubular bells", 14, 90, 64, 60),
              (CH_PAD, "warm pad", 89, 72, ISL_PAN, 70)],
    extra_markers=[(ICE_T0, "the ice"),
                   (REACHING[0][0], "the reaching"),
                   (TOLL_T0, "the tolls")],
)

PROGRAM_WHITELIST = {0, 42, 52, 5, 39, 95, 60, 108, 14, 89}
CENTERED_CHANNELS = {CH_PIANO, CH_CELLO, CH_KALIMBA, CH_BELLS}
NOTE_RANGES = {
    CH_PIANO: (44, 65), CH_CELLO: (45, 65), CH_CHOIR: (55, 74),
    CH_EP: (67, 88), CH_SYNBASS: (32, 46), CH_SWEEP: (44, 65),
    CH_HORN: (53, 66), CH_KALIMBA: (76, 76), CH_BELLS: (69, 69),
    CH_PAD: (48, 69),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # cello scoops recentre at seams
DURATION_WINDOW = (272.0, 289.0)            # ~4:40 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES sec.3 pattern; beat-based, tick where noted)
# ---------------------------------------------------------------------------

_PPQ = en.PPQ


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
    return sorted((b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6)


# ---------------------------------------------------------------------------
# Harmony.  A natural minor throughout.  The candle's warm pad and choir move
# through i - iv - bVI - v (Am, Dm, F, Em) - all diatonic, so the leading tone
# G# never appears and the cadence windows are clean by construction.
# ---------------------------------------------------------------------------

CANDLE_PAD = [
    [en.n("E3"), en.n("A3"), en.n("C4")],       # Am   (i)
    [en.n("D3"), en.n("F3"), en.n("A3")],       # Dm   (iv)
    [en.n("F3"), en.n("A3"), en.n("C4")],       # F    (bVI)
    [en.n("E3"), en.n("G3"), en.n("B3")],       # Em   (v)
]
CANDLE_CHOIR_TOP = [en.n("E4"), en.n("D4"), en.n("C4"), en.n("B3")]

PAD_BLOCK = 12.0                                # a 4-bar (6/8) pad block


def _pad_bed(sc, ch, t0, t1, cycle, tops_ch, tops, vel, vowel_pts):
    """The warm pad plus a sealed choir tone per block, each held the whole
    block so nothing ever falls silent - and ending exactly at t1."""
    b = t0
    i = 0
    while b < t1 - 1e-6:
        dur = min(PAD_BLOCK, t1 - b)
        for p in cycle[i % len(cycle)]:
            sc.note(ch, p, b, dur * 0.99, vel, jt=0, jv=2)
        sc.note(tops_ch, tops[i % len(tops)], b, dur * 0.99, vel - 6, jt=0, jv=2)
        b += PAD_BLOCK
        i += 1
    en.expr_curve(sc, ch, [(t0, vel - 6), (t0 + (t1 - t0) * 0.5, vel + 8),
                           (t1 - 1, vel - 8)], step=4.0)
    en.expr_curve(sc, tops_ch, [(t0, 38), (t0 + (t1 - t0) * 0.5, 60),
                                (t1 - 1, 40)], step=4.0)
    en.vowel_curve(sc, tops_ch, vowel_pts, step=4.0)
    en.cc_curve(sc, tops_ch, 1, [(t0, 0), (t1 - 1, 18)], step=8.0)


def _low_pedal(sc, t0, dur):
    """A low piano A caught by the sostenuto (CC66) under the una corda - the
    candle's held foundation.  Emitted only BETWEEN theme statements so the
    piano stays monophonic while it states (the searcher needs a clean run)."""
    sc.note(CH_PIANO, en.n("A2"), t0, dur, 40, jt=0, jv=2)
    en.sostenuto(sc, CH_PIANO, t0 + 0.5, t0 + dur)


def _cello_sigh(sc, t0, scoop_from, land, dur1, resolve, dur2, vel):
    """A bend-appoggiatura: the cello scoops up into `land` (a bend from
    `scoop_from` semitones, recentring to 0) then falls a step to `resolve`,
    the held note swelling on channel aftertouch.  Every scoop ends at 0 so
    the bend is recentred well before the movement seam."""
    en.bend_ramp(sc, CH_CELLO, t0 - 0.2, t0 + 0.25, scoop_from, 0.0, steps=6)
    sc.note(CH_CELLO, land, t0, dur1 * 0.98, vel, jt=0, jv=2)
    en.at_curve(sc, CH_CELLO, [(t0, 16), (t0 + dur1 * 0.5, 82),
                               (t0 + dur1, 12)], step=0.25)
    sc.note(CH_CELLO, resolve, t0 + dur1, dur2 * 0.98, vel - 8, jt=0, jv=2)
    en.at_curve(sc, CH_CELLO, [(t0 + dur1, 12), (t0 + dur1 + dur2 * 0.5, 60),
                               (t0 + dur1 + dur2, 8)], step=0.25)


def _cello_cadence(sc, down, vel=70):
    """The withheld cadence in the low cello: a iv (D) approach falling to the
    tonic A on the downbeat - modal, the leading tone nowhere near it."""
    sc.note(CH_CELLO, en.n("D3"), down - 2.5, 1.1, vel, jt=0, jv=2)
    sc.note(CH_CELLO, en.n("D3"), down - 1.25, 1.1, vel - 4, jt=0, jv=2)
    sc.note(CH_CELLO, en.n("A2"), down, 3.0, vel + 4, jt=0, jv=2)
    en.at_curve(sc, CH_CELLO, [(down, 14), (down + 1.5, 54), (down + 3.0, 8)],
                step=0.25)


# ---------------------------------------------------------------------------
# I. Candle [0, 108) - 6/8, the island theme twice under una corda + sostenuto
# ---------------------------------------------------------------------------

def _b_candle(sc):
    en.soft_pedal(sc, CH_PIANO, 0.5, I_END - 1.0)         # una corda, movement I
    _pad_bed(sc, CH_PAD, 0.0, I_END, CANDLE_PAD, CH_CHOIR, CANDLE_CHOIR_TOP,
             46, [(0.0, 8), (54.0, 38), (I_END - 1, 34)])
    # low pedals caught by the sostenuto, only between the theme statements
    for t0 in (4.0, 30.0, 60.0, 90.0):
        _low_pedal(sc, t0, 12.0)
    # the cello sighs bend-appoggiaturas over aftertouch swells
    _cello_sigh(sc, 8.0, -0.5, en.n("B3"), 2.0, en.n("A3"), 2.5, 60)
    _cello_sigh(sc, 33.0, -0.6, en.n("D4"), 2.0, en.n("C4"), 2.5, 62)
    _cello_sigh(sc, 50.0, -0.5, en.n("E4"), 1.5, en.n("D4"), 2.0, 64)
    _cello_sigh(sc, 54.0, 0.0, en.n("D4"), 1.5, en.n("C4"), 2.5, 58)
    _cello_sigh(sc, 66.0, -0.6, en.n("C4"), 2.0, en.n("B3"), 2.5, 60)
    _cello_sigh(sc, 96.0, -0.5, en.n("C4"), 1.5, en.n("A3"), 2.0, 56)
    sc.bend(CH_CELLO, 100.5, 0.0)                          # recentre before the seam
    # THE ISLAND THEME, twice, in A minor, each hanging on degree 2.  The piano
    # sounds nothing else across each statement, so every run stays findable.
    material.play_island(sc, CH_PIANO, ISLAND_STMT1_T0, ISLAND_BASE,
                         stretch=ISLAND_STMT_STR, vel=62, vel_end=52)
    en.sustain(sc, CH_PIANO, ISLAND_STMT1_T0,
               ISLAND_STMT1_T0 + 8.0 * ISLAND_STMT_STR)
    material.play_island(sc, CH_PIANO, ISLAND_STMT2_T0, ISLAND_BASE,
                         stretch=ISLAND_STMT_STR, vel=60, vel_end=50)
    en.sustain(sc, CH_PIANO, ISLAND_STMT2_T0,
               ISLAND_STMT2_T0 + 8.0 * ISLAND_STMT_STR)
    # the candle settles: a modal iv-i cadence in the low cello
    _cello_cadence(sc, 105.0)


# ---------------------------------------------------------------------------
# II. The Ice [108, 300) - 4/4, the metronomic still point (120).  The FM-EP
# ice-arp mutates one pitch per cycle over a static A synth-bass pulse and a
# filter-swept pad; the mainland reaches three times on the horn in G.
# ---------------------------------------------------------------------------

ICE_SCHED = dict(zip(ICE_SCHED_BARS, ICE_ROTATION))
ICE_BARS = int((ICE_T1 - ICE_T0) / 4.0)                  # 48 bars of 4/4
# The sweep pad's static Am voicing under the ice (filter, not harmony, moves).
ICE_PAD = [en.n("A2"), en.n("E3"), en.n("A3"), en.n("C4"), en.n("E4")]


def _ice_cell(sc, t0, offsets, vel):
    """One ice-arp: four 16ths off ICE_ROOT.  A pure cell (offsets == ICE_CELL)
    is HOOK4 and is found by the searcher; a mutated cell is not."""
    for k, off in enumerate(offsets):
        sc.note(CH_EP, ICE_ROOT + off, t0 + k * 0.25, 0.22,
                vel + (6 if k == 0 else 0), jt=0, jv=0)


def _ice_sequencer(sc):
    """The additive-mutation sequencer: two cells a bar.  Beat 1 follows the
    rotation schedule (mutated on scheduled bars, pure otherwise); beat 3 is
    always the pure anchor cell - so the base keeps registering."""
    for k in range(ICE_BARS):
        beat = ICE_T0 + 4.0 * k
        if k in ICE_SCHED:
            mi, off = ICE_SCHED[k]
            offsets = list(ICE_CELL)
            offsets[mi] = off
        else:
            offsets = ICE_CELL
        _ice_cell(sc, beat, offsets, 56)
        _ice_cell(sc, beat + 2.0, ICE_CELL, 50)


def _ice_bass(sc):
    """A static A synth-bass pulse - the coldest possible drone, octave quavers
    alternating A1/A2 on every beat, so the stillness has a heartbeat."""
    for k in range(ICE_BARS):
        beat = ICE_T0 + 4.0 * k
        for j in range(4):
            p = en.n("A1") if j % 2 == 0 else en.n("A2")
            sc.note(CH_SYNBASS, p, beat + j, 0.92,
                    52 + (4 if j == 0 else 0), jt=0, jv=0)


def _ice_pad(sc):
    """The sweep pad: a held Am voicing whose FILTER arcs open then shut across
    the movement (CC74) while the harmony stays frozen."""
    b = ICE_T0
    while b < ICE_T1 - 1e-6:
        dur = min(24.0, ICE_T1 - b)
        for p in ICE_PAD:
            sc.note(CH_SWEEP, p, b, dur * 0.99, 44, jt=0, jv=0)
        b += 24.0
    en.cc_curve(sc, CH_SWEEP, 74, [(ICE_T0, 28), (204.0, 112), (ICE_T1 - 1, 36)],
                step=4.0)
    en.expr_curve(sc, CH_SWEEP, [(ICE_T0, 40), (204.0, 66), (ICE_T1 - 1, 38)],
                  step=4.0)


def _reaching(sc):
    """THE REACHING: the mainland tries to arrive on the french horn in G,
    three times - four notes, then seven, then nine of ten - each stopping
    short.  Growth, not erosion: the reach lengthens but never completes, and
    a developing vibrato deepens each time."""
    for i, (t0, count) in enumerate(REACHING):
        material.play_mainland(sc, CH_HORN, t0, MAINLAND_BASE,
                               stretch=REACH_STR, vel=60, vel_end=54,
                               count=count)
        span = max(on + du for on, du, _d in material.MAINLAND[:count]) * REACH_STR
        en.expr_curve(sc, CH_HORN,
                      [(t0, 30), (t0 + span * 0.55, 78 + i * 6),
                       (t0 + span, 22)], step=0.5)
        en.cc_curve(sc, CH_HORN, 1, [(t0, 0), (t0 + span, 12 + i * 10)],
                    step=1.0)
    last_t0, last_count = REACHING[-1]
    last_span = max(on + du for on, du, _d
                    in material.MAINLAND[:last_count]) * REACH_STR
    en.echo_throw(sc, CH_HORN, last_t0 + last_span - 1.0)


def _b_ice(sc):
    _ice_sequencer(sc)
    _ice_bass(sc)
    _ice_pad(sc)
    # the kalimba taps EBB (MORSE_PROGRAMS[4] = 108) in standard Morse timing
    material.play_morse(sc, CH_KALIMBA, MORSE_T0, NUMBER, MORSE_PITCH)
    _reaching(sc)


# ---------------------------------------------------------------------------
# III. Wax [300, 366) - 6/8 slower, the island theme's last pre-dawn reading,
# a modal cadence, and four bell tolls.
# ---------------------------------------------------------------------------

def _b_wax(sc):
    en.soft_pedal(sc, CH_PIANO, 300.5, END - 1.0)          # una corda returns
    _pad_bed(sc, CH_PAD, 300.0, 360.0, CANDLE_PAD, CH_CHOIR, CANDLE_CHOIR_TOP,
             44, [(300.0, 20), (336.0, 48), (359.0, 44)])
    _low_pedal(sc, 302.0, 9.0)                              # a low A under the intro
    # the island theme's last pre-dawn statement, slow, still hanging on deg 2
    material.play_island(sc, CH_PIANO, WAX_THEME_T0, ISLAND_BASE,
                         stretch=WAX_THEME_STR, vel=58, vel_end=48)
    en.sustain(sc, CH_PIANO, WAX_THEME_T0, WAX_THEME_T0 + 8.0 * WAX_THEME_STR)
    # the cello warms the wax, then the withheld iv-i cadence
    _cello_sigh(sc, 326.0, -0.5, en.n("C4"), 2.5, en.n("B3"), 3.0, 58)
    _cello_sigh(sc, 336.0, -0.6, en.n("D4"), 2.5, en.n("C4"), 3.5, 56)
    sc.bend(CH_CELLO, 348.0, 0.0)                           # recentre the scoop
    _cello_cadence(sc, 354.0, vel=66)
    # the bell buoy: exactly four tolls on the island's A, the final note-ons
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=TOLL_SPACING, vel=76, dur=3.5)


BUILDERS = [_b_candle, _b_ice, _b_wax]


# ---------------------------------------------------------------------------
# Oracles - every device the HLD marks verified, single-sourced from material.
# (Protagonist bass / doubled thumb / breath herald are album-exempt for the
# ballad and deliberately absent - see the module docstring.)
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """The island states three times (tonic A, pc 9); the mainland NEVER
    completes (it only reaches) - the strait is a whole tone (distance 2)."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 3:
        fails.append(f"{len(isl)} island statements, want 3 (candle x2, wax)")
    for ch, start, _end, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at beat {start:.1f} (ch{ch}) implies pc "
                         f"{pc}, want {ISLAND_TONIC_PC} (A)")
    if mnl:
        fails.append(f"{len(mnl)} complete mainland statements, want 0 (the "
                     f"mainland only reaches, never arrives here)")
    dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
    if dist != 2:
        fails.append(f"shore distance {dist}, want 2 (a whole tone)")
    return fails


def _o_no_overlap(sc):
    """The simultaneity ban holds trivially: with no complete mainland
    statement, nothing can overlap an island one."""
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    pairs = material.overlapping_pairs(isl, mnl)
    return [f"island {a[1]:.1f}-{a[2]:.1f} overlaps mainland "
            f"{b[1]:.1f}-{b[2]:.1f}" for a, b in pairs]


def _o_end_degrees(sc):
    """End-degree discipline: no island line ends on its tonic, and the fusion
    phrase (T5's alone) never sounds here."""
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
    """The ice-arp earworm: HOOK4 stated >= 6 times across the track (the pure
    anchor cells alone supply dozens)."""
    hits = 0
    for ch in sc.events:
        hits += len(material.find_statements(material.note_ons(sc, ch),
                                             material.HOOKS[NUMBER]))
    if hits < 6:
        return [f"HOOK4 found {hits} times, want >= 6"]
    return []


def _o_rotation(sc):
    """THE ROTATION: on each scheduled bar the ice-arp's beat-1 cell mutates
    exactly the pinned pitch, the beat-3 anchor cell stays pure, and the base
    cell still registers (checked by hook density too)."""
    fails = []
    ep = _note_ons(sc, CH_EP)
    by_beat: dict[float, int] = {}
    for b, p, _v in ep:
        by_beat.setdefault(round(b, 3), p)

    def cell_at(beat):
        return [by_beat.get(round(beat + k * 0.25, 3)) for k in range(4)]

    pure = [ICE_ROOT + o for o in ICE_CELL]
    for k, (mi, off) in ICE_SCHED.items():
        beat = ICE_T0 + 4.0 * k
        want = list(ICE_CELL)
        want[mi] = off
        want_p = [ICE_ROOT + o for o in want]
        if cell_at(beat) != want_p:
            fails.append(f"rotation bar {k} (beat {beat:.0f}) cell "
                         f"{cell_at(beat)} != {want_p}")
        if cell_at(beat + 2.0) != pure:
            fails.append(f"anchor cell at beat {beat + 2:.0f} is not the pure "
                         f"base ({cell_at(beat + 2.0)})")
        if off == ICE_CELL[mi]:
            fails.append(f"rotation bar {k} does not actually mutate index {mi}")
    hits = len(material.find_statements(material.note_ons(sc, CH_EP),
                                        material.HOOKS[NUMBER]))
    if hits < 6:
        fails.append(f"the base ice cell registers {hits} times, want >= 6")
    return fails


def _o_reaching(sc):
    """THE REACHING: three mainland statements on the horn in G - 4, then 7,
    then 9 of 10 notes - each stopping short (growth, not erosion), and NO
    complete 10-note statement anywhere."""
    fails = []
    horn = _note_ons(sc, CH_HORN)
    want_total = sum(c for _t, c in REACHING)
    if len(horn) != want_total:
        fails.append(f"horn has {len(horn)} note-ons, want {want_total} "
                     f"(the reaches 4 + 7 + 9)")
    degs = [d for _o, _d, d in material.MAINLAND]
    for t0, count in REACHING:
        span = max(on + du for on, du, _d
                   in material.MAINLAND[:count]) * REACH_STR
        got = _onsets_in(sc, CH_HORN, t0 - 0.05, t0 + span + 0.05)
        if len(got) != count:
            fails.append(f"reach at beat {t0:.0f} has {len(got)} notes, "
                         f"want {count}")
            continue
        want_p = [en.pitch(MAINLAND_BASE, _MJ, degs[j]) for j in range(count)]
        if [p for _b, p, _v in got] != want_p:
            fails.append(f"reach at beat {t0:.0f} pitches "
                         f"{[p for _b, p, _v in got]} != {want_p}")
    if material.theme_statements(sc, "mainland"):
        fails.append("a complete 10-note mainland statement exists (the reach "
                     "must never finish on T4)")
    counts = [c for _t, c in REACHING]
    if counts != sorted(counts) or counts != [4, 7, 9]:
        fails.append(f"reach counts {counts} must be 4, 7, 9 (growth, short of 10)")
    return fails


def _o_metronome(sc):
    """The pinned still point: movement II carries EXACTLY ONE tempo event,
    120 bpm - no tide, no mercy."""
    fails = []
    ev = _movement_events(I_END, II_END)
    if len(ev) != 1:
        fails.append(f"the ice has {len(ev)} tempo events, want exactly 1 "
                     f"(the metronomic still point)")
    if ev and abs(ev[0][1] - 120.0) > 1e-6:
        fails.append(f"the ice tempo is {ev[0][1]}, want 120")
    return fails


def _o_tide_breath(sc):
    """The water is in the tempo of the two 6/8 movements: I and III each swell
    (>= 2 troughs); the ice (II) is the still point, checked separately."""
    fails = []
    for name, t0, t1 in [("I. Candle", 0.0, I_END), ("III. Wax", II_END, END)]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2 "
                         f"(the map must breathe)")
    return fails


def _o_fermata(sc):
    """The deep candle rubato: movements I and III each dip to a fermata far
    below the tide's own swell (<= 52 bpm) - the ritard the ice will refuse."""
    fails = []
    for name, t0, t1 in [("I. Candle", 0.0, I_END), ("III. Wax", II_END, END)]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        if seq and min(seq) > 52.0:
            fails.append(f"'{name}' min tempo {min(seq):.0f} bpm, want a deep "
                         f"fermata dip <= 52")
    return fails


def _o_pedals(sc):
    """The candle's pedals: the piano's una corda (CC67) and the sostenuto
    (CC66) catching a low pedal each press down (127) and lift (0)."""
    fails = []
    una = [v for _b, v in _cc_lane(sc, CH_PIANO, 67)]
    sost = [v for _b, v in _cc_lane(sc, CH_PIANO, 66)]
    if 127 not in una or 0 not in una:
        fails.append("piano una corda (CC67) must go down (127) and up (0)")
    if 127 not in sost or 0 not in sost:
        fails.append("piano sostenuto (CC66) must catch (127) and release (0)")
    return fails


def _o_cello(sc):
    """The candle's cello: channel-aftertouch swells and bend-appoggiatura
    scoops in movement I (the scoops recentre by construction)."""
    fails = []
    at = [(b, v) for b, v in _aftertouch_lane(sc, CH_CELLO) if b < I_END]
    if len(at) < 6:
        fails.append(f"cello aftertouch has {len(at)} events in the candle, "
                     f"want the swells")
    if at and max(v for _b, v in at) < 60:
        fails.append("cello aftertouch never swells (peak too weak)")
    bends = [t for t, _p, d in sc.events.get(CH_CELLO, [])
             if (d[0] & 0xF0) == 0xE0]
    if len(bends) < 8:
        fails.append(f"cello has {len(bends)} bend events, want the "
                     f"appoggiatura scoops")
    return fails


def _o_morse(sc):
    """The tide-word EBB, tapped on kalimba (MORSE_PROGRAMS[4] = 108), in
    standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 108:
        fails.append("morse timbre for T4 must be kalimba (program 108)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_KALIMBA)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} (EBB)")
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
    """The winter's mouth: choir CC70 never exceeds T4's cap of 55."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_sweep(sc):
    """The ice's filter arc: the sweep pad's CC74 opens then shuts across the
    still point (a wide arc whose peak sits away from the edges)."""
    fails = []
    lane = _cc_lane(sc, CH_SWEEP, 74)
    if len(lane) < 12:
        fails.append(f"sweep-pad CC74 has {len(lane)} events, want a filter arc")
        return fails
    vals = [v for _b, v in lane]
    if max(vals) - min(vals) < 40:
        fails.append(f"sweep CC74 range {max(vals) - min(vals)} < 40 (the arc "
                     f"must open)")
    peak_i = vals.index(max(vals))
    if peak_i == 0 or peak_i == len(vals) - 1:
        fails.append("sweep CC74 peak sits at an edge (want an arc: open, shut)")
    return fails


def _o_cadence(sc):
    """The withheld cadence: the low cello resolves to A modally (iv-i), the
    leading tone G# banned across each window on every channel."""
    fails = []
    for lo, hi, down in CAD_WINDOWS:
        for m in material.cadence_failures(sc, CH_CELLO, lo, hi, down,
                                           ISLAND_TONIC_PC):
            fails.append(f"[{lo:.0f},{hi:.0f}]: {m}")
    return fails


def _o_shore_pans(sc):
    """The narrowing strait: island channels left (54), the mainland horn
    right (74) - a whole tone wide, the closest the field has been."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_CHOIR, CH_EP, CH_SYNBASS, CH_SWEEP, CH_PAD}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{{ISL_PAN}}}")
    horn = {v for _b, v in _cc_lane(sc, CH_HORN, 10)}
    if horn != {MAIN_PAN}:
        fails.append(f"mainland horn pans {sorted(horn)}, want {MAIN_PAN}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls four times (track 4), on the island's A, the final
    note-ons - nothing new sounds after the first toll."""
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
        ("no_overlap", _o_no_overlap(sc)),
        ("end_degrees", _o_end_degrees(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("ice_rotation", _o_rotation(sc)),
        ("reaching", _o_reaching(sc)),
        ("metronome_still_point", _o_metronome(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("fermata_rubato", _o_fermata(sc)),
        ("piano_pedals", _o_pedals(sc)),
        ("cello_appoggiatura", _o_cello(sc)),
        ("morse_ebb", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("sweep_filter_arc", _o_sweep(sc)),
        ("cadence_law", _o_cadence(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) - RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The ice reads dense and steady against the sparse candle rubato; the wax
# resolves quieter than the ice.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    candle = _rms_db(30.0, 66.0)        # movement I, the sparse rubato candle
    ice = _rms_db(180.0, 236.0)         # movement II, the dense metronomic ice
    wax = _rms_db(324.0, 348.0)         # movement III, the quiet resolution

    # 1. The ice is the fuller, denser section: its energy sits at or above the
    #    intimate candle (a generous ratio; the ice's pulse + arp read dense).
    fails = []
    if ice - candle < -2.0:
        fails.append(f"ice {ice:.1f} dB reads more than 2 dB below the candle "
                     f"{candle:.1f} dB (the still point should be the dense one)")
    checks.append(("audio_ice_dense", fails))

    # 2. The wax resolution is quieter than the ice it follows.
    fails = []
    if ice - wax < 0.5:
        fails.append(f"wax {wax:.1f} dB not >= 0.5 dB below the ice "
                     f"{ice:.1f} dB (the resolution should fall away)")
    checks.append(("audio_wax_quieter", fails))

    # 3. The candle is intimate, not silent: it holds real level against the
    #    ice (keeps the rubato from reading as a dropout).
    fails = []
    if ice - candle > 12.0:
        fails.append(f"candle {candle:.1f} dB falls >12 dB under the ice "
                     f"{ice:.1f} dB (the candle should still be present)")
    checks.append(("audio_candle_present", fails))
    return checks

