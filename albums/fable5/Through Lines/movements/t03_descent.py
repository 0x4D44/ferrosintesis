"""t03_descent — Track 3 "Descent with Modification" of *Through Lines*.

Disc 1, 'Lines of Descent' — the evolution track (HLD section 3, T3): the
engine LITERALLY runs a seeded genetic algorithm over 4-bar motifs and
the piece is that run's transcript.  compute_evolution() breeds 18
generations of an 8-member population from a primordial motif (eight
half-notes on A — one repeating note) under fitness(motif) =
ground-consonance against the tonic drone + contour smoothness +
rhythmic viability, with (mu+lambda) selection, single-cut bar-line
crossover, and four mutation operators (interval tweak / rhythm split /
rhythm merge / transposition).  Every random draw comes from
random.Random(SEED) constructed INSIDE the function (memoized, so the
builders and the oracles reason about the identical run), and every
offspring's construction is recorded in a replayable mutation ledger.
Because survivors always compete with their own offspring for the mu
slots ((mu+lambda) selection), the k-th best of each new generation is
>= the k-th best of the previous one, so mean population fitness is
non-decreasing by construction — and the oracle recomputes it from
scratch to prove the run really happened that way.

Sections are generations (the movement grid):
  I.   Primordial Waters  (0-64)    drone + the one repeating note (gen 0)
  II.  First Replicators  (64-176)  gens 1-4: copies with mutation
                                    errors, 1 -> 4 voices, A minor
                                    pentatonic palette
  III. Cambrian Explosion (176-272) gens 5-9: 8-voice polyphony of
                                    variants, diatonic palette
  IV.  Selection          (272-352) gens 10-14: low-fitness lineages
                                    starve and fall silent (8 -> 3
                                    voices); the palette opens to the
                                    full chromatic
  V.   Extinction         (352-384) the crash (riser -> orchestra hit +
                                    timpani + kit, the piece's loudest
                                    bar); texture cut to a tenth; two
                                    survivors whisper (the near-silence
                                    velocities there are SCORED)
  VI.  Re-radiation       (384-496) gens 15-18: the survivors diversify
                                    into instrument niches (flute /
                                    oboe / fiddle / bass), 2 -> 6 voices
  VII. Emergence          (496-576) the fittest lineage, harmonized as a
                                    four-part chorale; ends on a HALF
                                    CADENCE (E major — the story isn't
                                    over)

Written oracle-first (the repo method): mean-fitness monotonicity, the
ledger replay (the chorale soprano is a documented descendant of the
primordial motif — its whole ancestry replays note-for-note), the
per-bar speciation contour (rise to 8, crash to <= 2, re-rise to 6), the
extinction energy cut (every post-crash bar's velocity sum <= 0.10x the
crash bar's), the pentatonic -> diatonic -> chromatic palette arc, the
chorale emergence and the half cadence are all falsifiable oracles
below; audio_checks() re-asserts the extinction drop, the speciation
swell and the cadence ring on the rendered WAV.  This track quotes no
material.py through-line: the HLD assigns it none — its DNA is grown
in-module by the algorithm itself.
"""

from __future__ import annotations

import random
from collections import namedtuple

import conductor
import engine as en

NUMBER = 3
TITLE = 'Descent with Modification'
FILE = '03 - Descent with Modification.mid'
SEED = 20260903

COMMENT = ("A seeded genetic algorithm run as music: 18 generations of "
           "4-bar motifs bred from one repeating note, with a replayable "
           "mutation ledger.  Mean population fitness is non-decreasing "
           "(mu+lambda selection); sections are generations; the closing "
           "chorale's soprano is the run's fittest descendant.  Ends on "
           "a half cadence.")

# ---------------------------------------------------------------------------
# The genome.  A motif is a tuple of (dur_beats, midi_pitch) pairs whose
# durations tile exactly MOTIF_BEATS (4 bars of 4/4) — notes are
# contiguous, so a motif is a complete 4-bar melody with no rests.
# ---------------------------------------------------------------------------

MOTIF_BEATS = 16.0
PITCH_LO, PITCH_HI = 55, 81            # the band all genomes live in
TONIC_PC = 9                           # A: the drone the fitness hears

# One repeating note over the drone: eight half-notes on A4.
PRIMORDIAL: tuple = tuple((2.0, 69) for _ in range(8))

MU, LAMBDA, GENERATIONS = 8, 16, 18

PENTA_PCS = {9, 0, 2, 4, 7}            # A C D E G
DIATONIC_PCS = {9, 11, 0, 2, 4, 5, 7}  # A natural minor
CHROMATIC_PCS = set(range(12))

# Interval classes (vs the tonic pc) the drone hears as consonant.
_CONS_ICS = {0, 3, 4, 7, 8, 9}


def fitness(motif) -> float:
    """The selection pressure — a PURE function of one motif in [0, 1].

    ground-consonance (0.45): duration-weighted fraction of the motif
    consonant against the tonic drone A; contour smoothness (0.30):
    repeated notes and leaps beyond a major third are penalized;
    rhythmic viability (0.25): note-count near 10 and duration variety.
    The oracles call this exact function to re-prove the run.
    """
    if not motif:
        return 0.0
    total = sum(d for d, _p in motif)
    if abs(total - MOTIF_BEATS) > 1e-6:
        return 0.0
    cons = sum(d for d, p in motif if (p - TONIC_PC) % 12 in _CONS_ICS)
    cons /= total
    steps = [b[1] - a[1] for a, b in zip(motif, motif[1:])]
    pen = 0.0
    for s in steps:
        if s == 0:
            pen += 0.5
        pen += 0.5 * max(0, abs(s) - 4)
    smooth = max(0.0, 1.0 - pen / max(1, len(steps)))
    nn = len(motif)
    r1 = max(0.0, 1.0 - abs(nn - 10) / 8.0)
    r2 = min(1.0, (len({d for d, _p in motif}) - 1) / 3.0)
    rhythm = 0.6 * r1 + 0.4 * r2
    return 0.45 * cons + 0.30 * smooth + 0.25 * rhythm


# ---------------------------------------------------------------------------
# Genetic operators.  All are PURE: the evolution loop draws random
# parameters, resolves them, and records the resolved operation in the
# ledger; replaying a ledger entry applies these functions with no RNG.
# ---------------------------------------------------------------------------

def _palette_pcs(gen: int) -> set:
    """Pentatonic waters -> diatonic shallows -> the chromatic open sea."""
    if gen <= 4:
        return PENTA_PCS
    if gen <= 9:
        return DIATONIC_PCS
    return CHROMATIC_PCS


def _palette(gen: int) -> list:
    pcs = _palette_pcs(gen)
    return [p for p in range(PITCH_LO, PITCH_HI + 1) if p % 12 in pcs]


def _snap(p: int, pal: list) -> int:
    return min(pal, key=lambda q: (abs(q - p), q))


def _normalize(motif, gen: int):
    """Clamp into the band and snap to the generation's pitch palette."""
    pal = _palette(gen)
    return tuple((d, _snap(min(PITCH_HI, max(PITCH_LO, p)), pal))
                 for d, p in motif)


def _crossover(ma, mb, cut: float):
    """Head of `ma` up to the bar-line `cut`, tail of `mb` after it."""
    head = []
    t = 0.0
    for d, p in ma:
        if t >= cut - 1e-9:
            break
        head.append((min(d, cut - t), p))
        t += d
    tail = []
    t = 0.0
    for d, p in mb:
        end = t + d
        if end > cut + 1e-9:
            start = max(t, cut)
            tail.append((end - start, p))
        t = end
    return tuple(head + tail)


def _apply_op(motif, op):
    """Apply one recorded mutation.  Pure; used by evolution AND replay."""
    m = list(motif)
    kind = op[0]
    if kind == "pitch":                      # interval tweak
        i, new_p = op[1], op[2]
        m[i] = (m[i][0], new_p)
    elif kind == "split":                    # rhythm split
        i, p2 = op[1], op[2]
        d, p = m[i]
        m[i:i + 1] = [(d / 2.0, p), (d / 2.0, p2)]
    elif kind == "merge":                    # rhythm merge
        i = op[1]
        (d1, p1), (d2, p2) = m[i], m[i + 1]
        m[i:i + 2] = [(d1 + d2, p1 if d1 >= d2 else p2)]
    elif kind == "transpose":
        m = [(d, p + op[1]) for d, p in m]
        if min(p for _d, p in m) < PITCH_LO:
            m = [(d, p + 12) for d, p in m]
        elif max(p for _d, p in m) > PITCH_HI:
            m = [(d, p - 12) for d, p in m]
    return tuple(m)


def _draw_ops(rng: random.Random, motif, gen: int):
    """Draw 1-3 mutations, applying each; returns (motif, resolved ops)."""
    pal = _palette(gen)
    m = motif
    ops = []
    for _ in range(rng.randint(1, 3)):
        roll = rng.random()
        op = None
        if roll < 0.40:
            i = rng.randrange(len(m))
            old = m[i][1]
            cands = [p for p in pal if p != old and abs(p - old) <= 4]
            if cands:
                op = ("pitch", i, rng.choice(cands))
        elif roll < 0.65:
            cands = [i for i, (d, _p) in enumerate(m)
                     if d in (1.0, 2.0, 3.0, 4.0)]
            if cands and len(m) < 16:
                i = rng.choice(cands)
                near = [p for p in pal if abs(p - m[i][1]) <= 5]
                op = ("split", i, rng.choice(near))
        elif roll < 0.80:
            if len(m) > 5:
                op = ("merge", rng.randrange(len(m) - 1))
        else:
            op = ("transpose", rng.choice((-7, -5, -4, -3, 3, 4, 5, 7)))
        if op is None:                       # infeasible draw: retry as tweak
            i = rng.randrange(len(m))
            old = m[i][1]
            cands = [p for p in pal if p != old and abs(p - old) <= 4]
            if not cands:
                continue
            op = ("pitch", i, rng.choice(cands))
        m = _apply_op(m, op)
        ops.append(op)
    return m, ops


_EVO_CACHE: dict | None = None


def compute_evolution() -> dict:
    """Run (once) and memoize the whole seeded genetic algorithm.

    The ONLY source of randomness is random.Random(SEED) constructed
    here, so a rebuild is byte-identical and the oracles reason about
    the identical run.  Returns:
      motifs       id -> motif tuple
      fits         id -> stored fitness (oracle recomputes)
      ledger       id -> ("seed",) | ("offspring", pa, pb, cut, ops, gen)
      generations  list of MU-long id lists, gen 0 .. GENERATIONS,
                   each sorted best-first ((-fitness, id))
      champion     the fittest id of the final generation
    """
    global _EVO_CACHE
    if _EVO_CACHE is not None:
        return _EVO_CACHE
    rng = random.Random(SEED)
    motifs: dict[int, tuple] = {}
    fits: dict[int, float] = {}
    ledger: dict[int, tuple] = {}
    next_id = 0
    pop: list[int] = []
    for _ in range(MU):                      # gen 0: the primordial copies
        i = next_id
        next_id += 1
        motifs[i] = PRIMORDIAL
        fits[i] = fitness(PRIMORDIAL)
        ledger[i] = ("seed",)
        pop.append(i)
    generations = [list(pop)]

    def tourney() -> int:
        idxs = rng.sample(range(len(pop)), 3)
        return min((pop[i] for i in idxs), key=lambda j: (-fits[j], j))

    for gen in range(1, GENERATIONS + 1):
        cand = list(pop)
        for _ in range(LAMBDA):
            pa, pb = tourney(), tourney()
            cut = rng.choice((4.0, 8.0, 12.0))
            child = _crossover(motifs[pa], motifs[pb], cut)
            child, ops = _draw_ops(rng, child, gen)
            child = _normalize(child, gen)
            i = next_id
            next_id += 1
            motifs[i] = child
            fits[i] = fitness(child)
            ledger[i] = ("offspring", pa, pb, cut, tuple(ops), gen)
            cand.append(i)
        cand.sort(key=lambda j: (-fits[j], j))
        pop = cand[:MU]                      # (mu+lambda): elites persist
        generations.append(list(pop))

    _EVO_CACHE = {
        "motifs": motifs, "fits": fits, "ledger": ledger,
        "generations": generations, "champion": generations[-1][0],
    }
    return _EVO_CACHE


def replay(evo: dict, ind: int, memo: dict | None = None) -> tuple:
    """Rebuild an individual's motif purely from its ledger ancestry."""
    if memo is None:
        memo = {}
    if ind in memo:
        return memo[ind]
    rec = evo["ledger"][ind]
    if rec[0] == "seed":
        m = PRIMORDIAL
    else:
        _kind, pa, pb, cut, ops, gen = rec
        m = _crossover(replay(evo, pa, memo), replay(evo, pb, memo), cut)
        for op in ops:
            m = _apply_op(m, op)
        m = _normalize(m, gen)
    memo[ind] = m
    return m


def _lineage_depth(evo: dict, ind: int, memo: dict | None = None) -> int:
    if memo is None:
        memo = {}
    if ind in memo:
        return memo[ind]
    rec = evo["ledger"][ind]
    d = 0 if rec[0] == "seed" else 1 + max(
        _lineage_depth(evo, rec[1], memo), _lineage_depth(evo, rec[2], memo))
    memo[ind] = d
    return d


# ---------------------------------------------------------------------------
# The stage.  Sections, channels, cycles: which generation sounds where.
# ---------------------------------------------------------------------------

SEC = [
    ("I. Primordial Waters", 0.0, 64.0),
    ("II. First Replicators", 64.0, 176.0),
    ("III. Cambrian Explosion", 176.0, 272.0),
    ("IV. Selection", 272.0, 352.0),
    ("V. Extinction", 352.0, 384.0),
    ("VI. Re-radiation", 384.0, 496.0),
    ("VII. Emergence", 496.0, 576.0),
]
END = 576.0
TOTAL_BARS = 144
CRASH = 352.0
CRASH_BAR = 88

CH_DRONE = 0
CH_S, CH_A, CH_T, CH_B = 10, 11, 12, 13     # the chorale
CH_HIT, CH_TIMP, DRUMS = 14, 15, 9
LINEAGE = frozenset(range(1, 9)) | {CH_S, CH_A, CH_T, CH_B}

# Rank r of a generation's population plays on channel 1 + r.
# Octave shifts are per-channel presentation registers, not genome edits.
SHIFT_OLD = {1: 0, 2: 12, 3: 0, 4: 12, 5: 0, 6: -12, 7: -12, 8: 12}
SHIFT_NEW = {1: 0, 2: 12, 3: 12, 4: 0, 5: 0, 6: -12}

# Presentation cycles: (start_beat, generation, ranks sounding, vel base).
CYCLES_II = [
    (64.0, 1, (0,), 54), (80.0, 1, (0, 1), 56),
    (96.0, 2, (0, 1), 57), (112.0, 2, (0, 1, 2), 58),
    (128.0, 3, (0, 1, 2), 60), (144.0, 3, (0, 1, 2, 3), 61),
    (160.0, 4, (0, 1, 2, 3), 62),
]
_ALL8 = tuple(range(8))
CYCLES_III = [
    (176.0, 5, _ALL8, 62), (192.0, 6, _ALL8, 65), (208.0, 7, _ALL8, 68),
    (224.0, 8, _ALL8, 71), (240.0, 9, _ALL8, 74), (256.0, 9, _ALL8, 76),
]
CYCLES_IV = [
    (272.0, 10, tuple(range(8)), 72), (288.0, 11, tuple(range(7)), 71),
    (304.0, 12, tuple(range(5)), 70), (320.0, 13, tuple(range(4)), 69),
    (336.0, 14, (0, 1, 2), 68),
]
CYCLES_VI = [
    (384.0, 15, (0, 1), 48), (400.0, 15, (0, 1, 2), 52),
    (416.0, 16, (0, 1, 2, 3), 56), (432.0, 16, (0, 1, 2, 3, 4), 58),
    (448.0, 17, (0, 1, 2, 3, 4), 62), (464.0, 17, (0, 1, 2, 3, 4, 5), 64),
    (480.0, 18, (0, 1, 2, 3, 4, 5), 66),
]

# V: the two survivors (gen 14's ranks 0 and 1) whisper 3-note fragments.
WHISPERS = [(358.0, 0), (362.0, 1), (366.0, 0), (370.0, 1),
            (373.0, 0), (374.5, 1), (378.0, 1), (381.5, 0)]
WHISPER_DURS = (0.5, 0.5, 1.0)

# VII: the chorale statements and the appended half cadence (S, A, T, B).
ST1, ST2, CADENCE = 496.0, 528.0, 560.0
CAD_CHORDS = [
    (560.0, 7.8, (69, 65, 62, 50), 56),      # iv (D minor) — the question
    (568.0, 7.5, (68, 64, 59, 40), 52),      # V (E MAJOR) — unresolved
]

# First presentation beat of each generation (drives the marker lane).
_GEN_MARKS: dict[int, float] = {}
for _cycles in (CYCLES_II, CYCLES_III, CYCLES_IV, CYCLES_VI):
    for _t0, _g, _ranks, _v in _cycles:
        _GEN_MARKS.setdefault(_g, _t0)

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=SEC,
    tempo_map=[(0.0, 60.0), (64.0, 72.0), (176.0, 84.0), (272.0, 82.0),
               (352.0, 66.0), (384.0, 88.0), (496.0, 63.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],                   # A minor
    channels=[
        (CH_DRONE, "primordial drone - warm pad", 89, 96, 64, 60),
        (1, "lineage 1 - marimba", 12, 100, 40, 35),
        (2, "lineage 2 - kalimba", 108, 96, 88, 35),
        (3, "lineage 3 - vibraphone > flute", 11, 96, 24, 40),
        (4, "lineage 4 - celesta > oboe", 8, 92, 100, 40),
        (5, "lineage 5 - harp > fiddle", 46, 98, 52, 40),
        (6, "lineage 6 - nylon guitar > bass", 24, 98, 64, 35),
        (7, "lineage 7 - pizzicato", 45, 96, 76, 35),
        (8, "lineage 8 - xylophone", 13, 90, 112, 35),
        (DRUMS, "percussion", 0, 100, 64, 30),
        (CH_S, "chorale S - choir", 52, 100, 64, 55),
        (CH_A, "chorale A - choir", 52, 98, 64, 55),
        (CH_T, "chorale T - choir", 52, 98, 64, 55),
        (CH_B, "chorale B - choir", 52, 100, 64, 55),
        (CH_HIT, "cataclysm - riser > orchestra hit", 119, 110, 64, 45),
        (CH_TIMP, "timpani", 47, 105, 64, 45),
    ],
    program_changes=[
        (CH_HIT, 351.75, 55),                # reverse cymbal -> orch hit
        (3, 386.0, 73),                      # niches for the re-radiation:
        (4, 386.0, 68),                      # flute, oboe,
        (5, 386.0, 110),                     # fiddle,
        (6, 386.0, 32),                      # acoustic bass
    ],
    extra_markers=sorted(
        [(beat, f"generation {g}") for g, beat in _GEN_MARKS.items()]
        + [(358.0, "two survivors"), (560.0, "half cadence")]),
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {8, 11, 12, 13, 24, 32, 45, 46, 47, 52,
                               55, 68, 73, 89, 108, 110, 119}
CENTERED_CHANNELS: set[int] = {CH_DRONE, 6, DRUMS, CH_S, CH_A, CH_T, CH_B,
                               CH_HIT, CH_TIMP}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_DRONE: (40, 52),
    1: (55, 81), 2: (67, 93), 3: (55, 93), 4: (55, 93),
    5: (55, 81), 6: (43, 69), 7: (43, 69), 8: (67, 93),
    CH_S: (55, 81), CH_A: (45, 80), CH_T: (41, 76), CH_B: (36, 59),
    CH_HIT: (45, 72), CH_TIMP: (36, 57),
}
GAP_WHITELIST: list[tuple[float, float]] = [(354.0, 358.6)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (462.0, 474.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# The chorale harmonizer — PURE function of the champion motif.
# ---------------------------------------------------------------------------

_CHORDS = (("Am", (9, 0, 4)), ("F", (5, 9, 0)), ("C", (0, 4, 7)),
           ("Dm", (2, 5, 9)), ("Em", (4, 7, 11)), ("G", (7, 11, 2)))


def harmonize(motif) -> list:
    """SATB rows [(dur, s, a, t, b)]: soprano IS the motif; A/T/B are
    chord tones of the first palette chord containing the soprano's
    pitch class (a chromatic soprano keeps the previous chord — a
    passing note over held harmony).  Deterministic."""
    rows = []
    pcs = _CHORDS[0][1]
    bass_prev = 45
    for dur, sp in motif:
        for _name, cand in _CHORDS:
            if sp % 12 in cand:
                pcs = cand
                break
        alto = max(p for p in range(45, sp) if p % 12 in pcs)
        tenor = max(p for p in range(41, alto) if p % 12 in pcs)
        root = pcs[0]
        cands = [p for p in range(36, 60) if p % 12 == root and p < tenor]
        bass = min(cands, key=lambda p: (abs(p - bass_prev), p))
        bass_prev = bass
        rows.append((dur, sp, alto, tenor, bass))
    return rows


# ---------------------------------------------------------------------------
# The presentation plan.  Every lineage/chorale note in the piece comes
# from exactly one Stmt; builders realize them and oracles hold the
# Score to them, so the plan is the single source of truth.
# ---------------------------------------------------------------------------

Stmt = namedtuple("Stmt", "sec ch t0 seq scale vel0 vel1 gate")

_PLAN_CACHE: dict | None = None


def _shifted(seq, shift: int):
    return tuple((d, p + shift) for d, p in seq)


def _plan() -> dict:
    global _PLAN_CACHE
    if _PLAN_CACHE is not None:
        return _PLAN_CACHE
    evo = compute_evolution()
    gens, motifs = evo["generations"], evo["motifs"]

    def motif_of(gen: int, rank: int):
        return motifs[gens[gen][rank]]

    stmts: list[Stmt] = []
    # I. gen 0: the repeating note, three statements, slowly waking.
    for t0, v in ((16.0, 46), (32.0, 52), (48.0, 58)):
        stmts.append(Stmt(0, 1, t0, PRIMORDIAL, 1.0, v, v + 4, 0.96))
    # II / III / IV / VI: the generation cycles.
    tables = ((1, CYCLES_II, SHIFT_OLD, 2), (2, CYCLES_III, SHIFT_OLD, 1),
              (3, CYCLES_IV, SHIFT_OLD, 1), (5, CYCLES_VI, SHIFT_NEW, 2))
    for sec_i, cycles, shifts, per_rank in tables:
        for ci, (t0, gen, ranks, base) in enumerate(cycles):
            for r in ranks:
                ch = 1 + r
                dying = (sec_i == 3 and ci + 1 < len(cycles)
                         and r not in cycles[ci + 1][2])
                v0 = base - per_rank * r
                v1 = 42 if dying else v0 + 4
                stmts.append(Stmt(sec_i, ch, t0,
                                  _shifted(motif_of(gen, r), shifts[ch]),
                                  1.0, v0, v1, 0.96))
    # V. the survivors' whispered fragments (scored near-silence).
    for t0, rank in WHISPERS:
        ch = 1 + rank
        frag = tuple(zip(WHISPER_DURS,
                         [p for _d, p in motif_of(14, rank)[:3]]))
        stmts.append(Stmt(4, ch, t0, _shifted(frag, SHIFT_OLD[ch]),
                          1.0, 32, 30, 0.97))
    # VII. the chorale: champion soprano + harmonized A/T/B, twice.
    champ = motifs[evo["champion"]]
    rows = harmonize(champ)
    for t0, (vs0, vs1), vatb in ((ST1, (55, 59), 50), (ST2, (66, 70), 61)):
        stmts.append(Stmt(6, CH_S, t0, champ, 2.0, vs0, vs1, 0.975))
        for ch, vi in ((CH_A, 2), (CH_T, 3), (CH_B, 4)):
            seq = tuple((d, row[vi]) for d, row in zip(
                (r[0] for r in rows), rows))
            stmts.append(Stmt(6, ch, t0, seq, 2.0, vatb, vatb + 3, 0.975))
    # statement 2 doublers: the niches sing the winning theme too.
    stmts.append(Stmt(6, 3, ST2, _shifted(champ, 12), 2.0, 50, 54, 0.975))
    stmts.append(Stmt(6, 5, ST2, champ, 2.0, 56, 60, 0.975))
    # the half cadence, appended after the second statement.
    for t0, dur, satb, v in CAD_CHORDS:
        for ch, p in zip((CH_S, CH_A, CH_T, CH_B), satb):
            stmts.append(Stmt(6, ch, t0, ((dur, p),), 1.0, v, v, 1.0))

    # Expected per-bar lineage-voice counts, derived from the statements
    # with the same geometry the counting oracle measures.
    per_bar = [set() for _ in range(TOTAL_BARS)]
    for st in stmts:
        if st.ch not in LINEAGE:
            continue
        for b in _bars_of(st):
            per_bar[b].add(st.ch)
    expected = [len(s) for s in per_bar]

    _PLAN_CACHE = {"stmts": stmts, "expected": expected,
                   "champion": champ, "rows": rows}
    return _PLAN_CACHE


def _bars_of(st: Stmt) -> list:
    """Bars whose interior window [bar+0.15, bar+3.85] the statement's
    sounding span [t0, gated end] intersects."""
    total = sum(d for d, _p in st.seq) * st.scale
    last = st.seq[-1][0] * st.scale
    end = st.t0 + total - last * (1.0 - st.gate)
    out = []
    for b in range(int(st.t0 // 4.0), min(TOTAL_BARS, int(end // 4.0) + 1)):
        if st.t0 < b * 4.0 + 3.85 and end > b * 4.0 + 0.15:
            out.append(b)
    return out


def _stmts_for(sec_i: int) -> list:
    return [st for st in _plan()["stmts"] if st.sec == sec_i]


def _realize(sc: en.Score, st: Stmt) -> None:
    total = sum(d for d, _p in st.seq) * st.scale
    t = st.t0
    for d, p in st.seq:
        v = en.lerp(st.vel0, st.vel1, (t - st.t0) / total)
        sc.note(st.ch, p, t, d * st.scale * st.gate, int(round(v)),
                jt=3, jv=2)
        t += d * st.scale


# ---------------------------------------------------------------------------
# Oracle helpers (event extraction mirrors verify.py's conventions).
# ---------------------------------------------------------------------------

def _note_ons(sc: en.Score, ch: int) -> list:
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick / en.PPQ, data[1], data[2]))
    return sorted(out)


def _note_spans(sc: en.Score, ch: int) -> list:
    pending: dict[int, list] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append(tick / en.PPQ)
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                out.append((queue.pop(0), tick / en.PPQ, data[1]))
    return sorted(out)


def _bar_sums(sc: en.Score) -> list:
    sums = [0.0] * TOTAL_BARS
    for ch in sc.events:
        for beat, _p, vel in _note_ons(sc, ch):
            b = int(beat // 4.0)
            if 0 <= b < TOTAL_BARS:
                sums[b] += vel
    return sums


def _lineage_counts(sc: en.Score) -> list:
    counts = [0] * TOTAL_BARS
    for ch in sorted(LINEAGE):
        spans = _note_spans(sc, ch)
        for b in range(TOTAL_BARS):
            lo, hi = b * 4.0 + 0.15, b * 4.0 + 3.85
            if any(on < hi and off > lo for on, off, _p in spans):
                counts[b] += 1
    return counts


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the builders; the music is composed to pass.
# ---------------------------------------------------------------------------

def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    evo = compute_evolution()
    plan = _plan()
    results: list[tuple[str, list[str]]] = []

    # --- ga_fitness_recompute: stored fitnesses are the pure function's ---
    fails: list[str] = []
    for i, m in evo["motifs"].items():
        f = fitness(m)
        if abs(f - evo["fits"][i]) > 1e-12:
            fails.append(f"individual {i}: stored fitness {evo['fits'][i]} "
                         f"!= recomputed {f}")
    champ = evo["champion"]
    final = evo["generations"][-1]
    best = min(final, key=lambda j: (-fitness(evo["motifs"][j]), j))
    if champ != best:
        fails.append(f"champion {champ} is not the final generation's "
                     f"fittest ({best})")
    for i in evo["motifs"]:
        f = fitness(evo["motifs"][i])
        if not 0.0 <= f <= 1.0:
            fails.append(f"individual {i}: fitness {f} outside [0, 1]")
    results.append(("ga_fitness_recompute", fails[:8]))

    # --- ga_fitness_nondecreasing: evolution demonstrably ran ------------
    fails = []
    means = []
    for g, gen_pop in enumerate(evo["generations"]):
        if len(gen_pop) != MU:
            fails.append(f"generation {g} has {len(gen_pop)} members")
        means.append(sum(fitness(evo["motifs"][i]) for i in gen_pop) / MU)
    for g in range(1, len(means)):
        if means[g] < means[g - 1] - 1e-12:
            fails.append(f"mean fitness fell {means[g - 1]:.4f} -> "
                         f"{means[g]:.4f} at generation {g}")
    if means and means[-1] <= means[0] + 0.05:
        fails.append(f"evolution barely improved: mean {means[0]:.4f} -> "
                     f"{means[-1]:.4f} (want > +0.05)")
    results.append(("ga_fitness_nondecreasing", fails[:8]))

    # --- ga_ledger_replays: every genome is reachable from the seed ------
    fails = []
    memo: dict = {}
    for i, m in evo["motifs"].items():
        if replay(evo, i, memo) != m:
            fails.append(f"individual {i}: ledger replay diverges from "
                         f"the stored motif")
    if evo["ledger"][champ][0] == "seed":
        fails.append("champion is the unevolved seed itself")
    depth = _lineage_depth(evo, champ)
    if depth < 4:
        fails.append(f"champion lineage depth {depth} < 4: barely evolved")
    results.append(("ga_ledger_replays", fails[:8]))

    # --- ga_palette_arc: pentatonic -> diatonic -> chromatic -------------
    fails = []
    for g in range(1, GENERATIONS + 1):
        want = _palette_pcs(g)
        for i in evo["generations"][g]:
            bad = {p % 12 for _d, p in evo["motifs"][i]} - want
            if bad:
                fails.append(f"gen {g} individual {i} uses pitch classes "
                             f"{sorted(bad)} outside its era's palette")
    chrom = set()
    for g in range(10, GENERATIONS + 1):
        for i in evo["generations"][g]:
            chrom |= {p % 12 for _d, p in evo["motifs"][i]}
    if not chrom - DIATONIC_PCS:
        fails.append("no chromatic pitch class ever enters the gene pool "
                     "after generation 10")
    vii_pcs = {p % 12 for ch in (CH_S, CH_A, CH_T, CH_B)
               for on, p, _v in _note_ons(sc, ch) if on >= 560.0}
    if 8 not in vii_pcs:
        fails.append("the half cadence never sounds G# (pc 8): the music "
                     "never arrives at the chromatic")
    results.append(("ga_palette_arc", fails[:8]))

    # --- primordial_seed: one repeating note, restated three times -------
    fails = []
    if len({p for _d, p in PRIMORDIAL}) != 1:
        fails.append("the primordial motif is not one repeating note")
    if PRIMORDIAL[0][1] % 12 != TONIC_PC:
        fails.append("the primordial note is not the tonic A")
    # (jitter-tolerant boundary, the statements_fidelity convention:
    # section II's first note at 64.0 may jitter up to 3 ticks early)
    ons1 = [o for o in _note_ons(sc, 1) if o[0] < 64.0 - 0.03]
    if len(ons1) != 3 * len(PRIMORDIAL):
        fails.append(f"section I has {len(ons1)} ch1 notes, want "
                     f"{3 * len(PRIMORDIAL)}")
    if any(p != PRIMORDIAL[0][1] for _b, p, _v in ons1):
        fails.append("section I sounds a pitch other than the primordial A")
    results.append(("primordial_seed", fails[:8]))

    # --- speciation_contour: the per-bar voice-count curve ---------------
    fails = []
    expected = plan["expected"]
    actual = _lineage_counts(sc)
    for b in range(TOTAL_BARS):
        if actual[b] != expected[b]:
            fails.append(f"bar {b}: {actual[b]} lineage voices sound, "
                         f"plan says {expected[b]}")
    if max(expected[44:68]) < 8:
        fails.append("the Cambrian never reaches 8 simultaneous voices")
    if any(c > 2 for c in expected[89:96]):
        fails.append("more than 2 voices survive the extinction")
    if max(expected[96:124]) < 5:
        fails.append("the re-radiation never re-rises to 5 voices")
    if expected[CRASH_BAR] != 0:
        fails.append("lineage voices play through the crash bar")
    results.append(("speciation_contour", fails[:8]))

    # --- statements_fidelity: the Score realizes the plan exactly --------
    fails = []
    ons_by_ch = {ch: _note_ons(sc, ch) for ch in sorted(LINEAGE | {3, 5})}
    for st in plan["stmts"]:
        total = sum(d for d, _p in st.seq) * st.scale
        w0, w1 = st.t0 - 0.03, st.t0 + total - 0.03
        got = [(b, p) for b, p, _v in ons_by_ch[st.ch] if w0 <= b < w1]
        want = []
        t = st.t0
        for d, p in st.seq:
            want.append((t, p))
            t += d * st.scale
        if [p for _b, p in got] != [p for _b, p in want]:
            fails.append(f"ch{st.ch} @ {st.t0}: pitch sequence differs "
                         f"from the plan ({len(got)} vs {len(want)} notes)")
        elif any(abs(gb - wb) > 0.05 for (gb, _), (wb, _) in
                 zip(got, want)):
            fails.append(f"ch{st.ch} @ {st.t0}: onsets drift > 0.05 beats "
                         f"from the plan")
    results.append(("statements_fidelity", fails[:8]))

    # --- extinction_energy: texture cut to a tenth -----------------------
    fails = []
    sums = _bar_sums(sc)
    peak = max(sums)
    if sums.index(peak) != CRASH_BAR:
        fails.append(f"loudest bar is {sums.index(peak)}, want the crash "
                     f"bar {CRASH_BAR}")
    for b in range(89, 96):
        if sums[b] > 0.10 * sums[CRASH_BAR]:
            fails.append(f"post-extinction bar {b} velocity sum "
                         f"{sums[b]:.0f} > 0.10x the crash bar "
                         f"({0.10 * sums[CRASH_BAR]:.0f})")
    results.append(("extinction_energy", fails[:8]))

    # --- arc_dynamics: the long dramatic shape ---------------------------
    fails = []

    def mean(lo, hi):
        return sum(sums[lo:hi]) / (hi - lo)

    m1, m2, m3 = mean(0, 16), mean(16, 44), mean(44, 68)
    if not m1 < m2 < m3:
        fails.append(f"section means do not rise I<II<III "
                     f"({m1:.0f}, {m2:.0f}, {m3:.0f})")
    after, rerad = mean(89, 96), mean(96, 124)
    if rerad <= 2.0 * after:
        fails.append(f"re-radiation mean {rerad:.0f} not > 2x the "
                     f"aftermath mean {after:.0f}")
    results.append(("arc_dynamics", fails[:8]))

    # --- cambrian_diversity: the explosion is of DIFFERENT variants ------
    fails = []
    for g in range(5, 10):
        distinct = len({evo["motifs"][i] for i in evo["generations"][g]})
        if distinct < 5:
            fails.append(f"generation {g} has only {distinct} distinct "
                         f"motifs among {MU}")
    results.append(("cambrian_diversity", fails[:8]))

    # --- chorale_emergence: the soprano IS the champion ------------------
    fails = []
    champ_m = plan["champion"]
    for t0 in (ST1, ST2):
        got = [(b, p) for b, p, _v in _note_ons(sc, CH_S)
               if t0 - 0.03 <= b < t0 + 32.0 - 0.03]
        if [p for _b, p in got] != [p for _d, p in champ_m]:
            fails.append(f"statement @ {t0}: soprano pitches != champion")
            continue
        t = t0
        for (gb, _p), (d, _p2) in zip(got, champ_m):
            if abs(gb - t) > 0.05:
                fails.append(f"statement @ {t0}: soprano rhythm is not "
                             f"the champion's durations x2")
                break
            t += d * 2.0
    for dur, s, a, t, b in plan["rows"]:
        if not (s > a > t > b):
            fails.append(f"chorale voices cross: {(s, a, t, b)}")
        if b < 36:
            fails.append(f"chorale bass {b} below the C2 floor")
    results.append(("chorale_emergence", fails[:8]))

    # --- half_cadence: ends on V, held, nothing after ---------------------
    fails = []
    tail = []
    for ch in sc.events:
        for on, off, p in _note_spans(sc, ch):
            if on >= 567.95:
                tail.append((on, off, p))
    pcs = {p % 12 for _on, _off, p in tail}
    if not pcs <= {4, 8, 11}:
        fails.append(f"final harmony pitch classes {sorted(pcs)} stray "
                     f"outside E major {{4, 8, 11}}")
    if not {4, 8, 11} <= pcs:
        fails.append(f"final harmony {sorted(pcs)} is not the full "
                     f"E-major triad (the half cadence)")
    if tail:
        last_on = max(on for on, _off, _p in tail)
        if last_on > 575.0:
            fails.append(f"a note starts at {last_on:.2f}, after the "
                         f"cadence has settled")
        if max(off for _on, off, _p in tail) < 574.5:
            fails.append("the final chord is not held to the end")
    else:
        fails.append("nothing sounds in the final cadence")
    if TONIC_PC in pcs:
        fails.append("the tonic sounds in the final chord: that is a "
                     "resolution, not a half cadence")
    results.append(("half_cadence", fails[:8]))

    # --- generation_ladder: sections really are successive generations ---
    fails = []
    seq = [g for cycles in (CYCLES_II, CYCLES_III, CYCLES_IV, CYCLES_VI)
           for _t0, g, _r, _v in cycles]
    if seq != sorted(seq):
        fails.append("presented generations are not non-decreasing in time")
    if set(seq) != set(range(1, GENERATIONS + 1)):
        fails.append("the cycles do not present every generation 1..18")
    marks = {(b, t) for b, t in sc.markers}
    for g, beat in sorted(_GEN_MARKS.items()):
        if (beat, f"generation {g}") not in marks:
            fails.append(f"missing 'generation {g}' marker at beat {beat}")
    results.append(("generation_ladder", fails[:8]))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/03 - ....wav exists.
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    def wrms(b0: float, b1: float, stride: int = 4) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        i1 = min(i1, len(ctx.l))
        acc, n = 0.0, 0
        for i in range(max(0, i0), i1, stride):
            acc += ctx.l[i] * ctx.l[i] + ctx.r[i] * ctx.r[i]
            n += 2
        return (acc / n) ** 0.5 if n else 0.0

    # 1. Extinction: post-crash bar ENERGY <= 0.10x the pre-crash peak
    #    bar (RMS -10 dB), measured from bar 91 (two decay bars granted
    #    for the crash's reverb tail).
    fails: list[str] = []
    peak = max(wrms(b * 4.0, b * 4.0 + 4.0) for b in range(0, 89))
    cap = peak * (0.10 ** 0.5)
    for b in range(91, 96):
        r = wrms(b * 4.0, b * 4.0 + 4.0)
        if r > cap:
            fails.append(f"bar {b} RMS {ctx.db(r):.1f} dB > extinction cap "
                         f"{ctx.db(cap):.1f} dB (peak {ctx.db(peak):.1f})")
    checks.append(("audio_extinction_drop", fails))

    # 2. Speciation is audible: the Cambrian is >= 6 dB over the
    #    primordial waters; the re-radiation >= 6 dB over the aftermath.
    fails = []
    prim = wrms(16.0, 64.0)
    camb = wrms(176.0, 272.0)
    if ctx.db(camb) < ctx.db(prim) + 6.0:
        fails.append(f"Cambrian {ctx.db(camb):.1f} dB not >= primordial "
                     f"{ctx.db(prim):.1f} dB + 6")
    after = wrms(356.0, 384.0)
    rerad = wrms(448.0, 496.0)
    if ctx.db(rerad) < ctx.db(after) + 6.0:
        fails.append(f"re-radiation {ctx.db(rerad):.1f} dB not >= "
                     f"aftermath {ctx.db(after):.1f} dB + 6")
    checks.append(("audio_speciation_swell", fails))

    # 3. The half cadence rings and decays: the last two seconds sit
    #    below the chord's strike window.
    fails = []
    strike = wrms(568.0, 572.0)
    n2 = 2 * ctx.sample_rate
    acc, n = 0.0, 0
    for i in range(max(0, len(ctx.l) - n2), len(ctx.l), 4):
        acc += ctx.l[i] * ctx.l[i] + ctx.r[i] * ctx.r[i]
        n += 2
    tail = (acc / n) ** 0.5 if n else 0.0
    if tail >= strike:
        fails.append(f"tail RMS {ctx.db(tail):.1f} dB does not decay "
                     f"below the cadence strike {ctx.db(strike):.1f} dB")
    checks.append(("audio_cadence_ring", fails))

    return checks


# ---------------------------------------------------------------------------
# Builders — one per movement.
# ---------------------------------------------------------------------------

def _drone(sc: en.Score, t0: float, t1: float, vel: int,
           pitches=(45, 52)) -> None:
    """The environment: 8-beat re-struck pad fifths (A2+E3), centred."""
    t = t0
    while t < t1 - 1e-6:
        dur = min(8.0, t1 - t)
        for p in pitches:
            sc.note(CH_DRONE, p, t, dur, vel, jt=2, jv=2)
        t += 8.0


def _build_primordial(sc: en.Score) -> None:
    _drone(sc, 0.0, 64.0, 34)
    en.cc_curve(sc, CH_DRONE, 11, [(0.0, 18), (16.0, 46), (40.0, 56),
                                   (63.5, 58)], step=1.0)
    for st in _stmts_for(0):
        _realize(sc, st)


def _build_replicators(sc: en.Score) -> None:
    _drone(sc, 64.0, 176.0, 36)
    en.cc_curve(sc, CH_DRONE, 11, [(64.0, 58), (120.0, 62), (175.5, 64)],
                step=2.0)
    for st in _stmts_for(1):
        _realize(sc, st)


def _build_cambrian(sc: en.Score) -> None:
    _drone(sc, 176.0, 272.0, 38)
    en.cc_curve(sc, CH_DRONE, 11, [(176.0, 64), (240.0, 70), (271.5, 72)],
                step=2.0)
    for st in _stmts_for(2):
        _realize(sc, st)
    # The explosion's climax cycle gets a pulse under it.
    sc.hit(49, 256.0, 68)
    for k in range(4):
        bar = 256.0 + 4.0 * k
        sc.hit(36, bar, 58 + 4 * k)
        sc.hit(36, bar + 2.0, 52 + 4 * k)
        sc.hit(41, bar + 3.0, 54 + 4 * k)


def _build_selection(sc: en.Score) -> None:
    _drone(sc, 272.0, 352.0, 38)
    en.cc_curve(sc, CH_DRONE, 11, [(272.0, 70), (344.0, 66), (351.5, 74)],
                step=2.0)
    for st in _stmts_for(3):
        _realize(sc, st)
    # The reverse-cymbal riser into the cataclysm (swells, then stops).
    sc.note(CH_HIT, 60, 348.5, 3.1, 92, jt=0, jv=0)


def _build_extinction(sc: en.Score) -> None:
    # The crash — the loudest bar of the piece, deterministic (jt=jv=0).
    for p, v in ((45, 124), (57, 122)):
        sc.note(CH_HIT, p, 352.0, 3.0, v, jt=0, jv=0)
    for p, v in ((45, 118), (57, 116)):
        sc.note(CH_HIT, p, 352.5, 2.5, v, jt=0, jv=0)
    for i in range(16):
        sc.note(CH_TIMP, 45, 352.0 + 0.25 * i, 0.3,
                int(round(en.lerp(124, 96, i / 15.0))), jt=0, jv=0)
    for drum, beat, v in ((36, 352.0, 124), (49, 352.0, 124),
                          (57, 352.0, 114), (41, 352.25, 118),
                          (43, 352.5, 112)):
        sc.note(DRUMS, drum, beat, 0.25, v, jt=0, jv=0)
    # The scored void (GAP_WHITELIST), then two survivors whisper.
    for st in _stmts_for(4):
        _realize(sc, st)
    _drone(sc, 360.0, 383.5, 22)
    en.cc_curve(sc, CH_DRONE, 11, [(358.0, 24), (383.0, 30)], step=2.0)


def _build_reradiation(sc: en.Score) -> None:
    _drone(sc, 384.0, 496.0, 30)
    en.cc_curve(sc, CH_DRONE, 11, [(384.0, 34), (440.0, 48), (495.5, 54)],
                step=2.0)
    for st in _stmts_for(5):
        _realize(sc, st)
    # Life's small engine restarts: maracas eighths, then a rim pulse.
    t = 432.0
    k = 0
    while t < 495.5:
        sc.hit(70, t, 26 if k % 2 else 34)
        t += 0.5
        k += 1
    for bar in range(448, 496, 4):
        sc.hit(37, bar + 2.0, 38)


def _build_emergence(sc: en.Score) -> None:
    _drone(sc, 496.0, 560.0, 30, pitches=(45,))
    # The ground itself finally moves: A -> D under iv, E+B under V.
    sc.note(CH_DRONE, 45, 560.0, 7.8, 30, jt=2, jv=2)
    for p in (40, 47):
        sc.note(CH_DRONE, p, 568.0, 7.5, 30, jt=2, jv=2)
    en.cc_curve(sc, CH_DRONE, 11, [(496.0, 54), (544.0, 60), (568.0, 62),
                                   (575.0, 40)], step=2.0)
    for st in _stmts_for(6):
        _realize(sc, st)
    # Vowels: mm/oo for the first statement, opening to ah; expression
    # swells with the second statement and dies with the cadence.
    for ch in (CH_S, CH_A, CH_T, CH_B):
        en.vowel_curve(sc, ch, [(496.0, 38), (526.0, 44), (528.0, 50),
                                (544.0, 80), (560.0, 85), (568.0, 88)],
                       step=2.0)
        en.cc_curve(sc, ch, 11, [(496.0, 66), (526.0, 72), (528.0, 80),
                                 (552.0, 88), (560.0, 84), (568.0, 80),
                                 (575.5, 46)], step=1.0)
    # The niche doublers breathe a little vibrato on the second statement.
    for ch in (3, 5):
        sc.cc(ch, 1, 30, 527.8)
        sc.cc(ch, 1, 0, 560.2)
    # A pp timpani roll on E under the held half cadence.
    t = 570.0
    while t <= 574.5 + 1e-9:
        sc.note(CH_TIMP, 40, t, 0.35, 26, jt=2, jv=2)
        t += 0.3


BUILDERS: list = [_build_primordial, _build_replicators, _build_cambrian,
                  _build_selection, _build_extinction, _build_reradiation,
                  _build_emergence]
