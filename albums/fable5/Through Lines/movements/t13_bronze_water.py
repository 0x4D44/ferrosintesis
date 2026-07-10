"""t13_bronze_water — Track 13 "Bronze Water" of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T13: a gamelan-inspired
colotomy — nested bronze layers around a 16-beat gong cycle, a
slendro-approximating tuning authored as static per-channel pitch-bend
offsets, an irama gear-change at the exact time-midpoint, a rebab
floating free of the density chain, and a closing Western string
chorale coexisting with (never replacing) the bronze.

TUNING — the 5-tone slendro-approximating table
-----------------------------------------------
Ideal slendro divides the octave into five near-equal steps of ~240
cents: 0, 240, 480, 720, 960 c above the tonic.  The nearest 12-TET
pentatonic (C D F G A = 0, 200, 500, 700, 900 c) misses those targets
by +0, +40, -20, +20, +60 cents respectively.  Those five deviations
ARE the tuning table, authored one per bronze channel as a STATIC
pitch bend at t=0 (after an explicit RPN-0 bend range of 2 semitones),
so the ensemble as a whole samples every slendro inflection and
adjacent layers beat gently against each other — the ombak shimmer of
paired bronze.  Exact authored offsets (14-bit quantized):

    ch0  gong ageng (GM 14 + CC0 alt bank)   +0.00 c  (raw 8192)
    ch1  kemanak    (GM 113 agogo)          +39.99 c  (raw 9830)
    ch2  bronze pots (GM 112 tinkle bell)   -19.99 c  (raw 7373)
    ch3  saron      (GM 8 celesta)          +19.99 c  (raw 9011)
    ch4  peking     (GM 9 glockenspiel)     +60.01 c  (raw 10650)

All five channels are BEND_EXEMPT: the shared bend-hygiene check then
asserts the offset never MOVES inside any movement.  The rebab (ch5)
and chorale strings (ch6) stay 12-TET and author no bends at all —
the closing coexistence is bronze water against Western glass.

COLOTOMY AND DENSITY HIERARCHY
------------------------------
The gong cycle is 16 beats; the gong ageng strikes EXACTLY on every
16-beat boundary (beats 0, 16, ..., 384) and nowhere else, jitter-free
(jt=0 across the bronze: gamelan tightness is the aesthetic; the life
lives in the detune shimmer, velocity contour and the rebab's rubato).
Above the gong, each moving layer plays exactly 2x the notes per cycle
of the layer below it — the chain is strict in BOTH halves:

    layer            irama I (cycles 1-16)   irama II (cycles 17-24)
    kemanak                  2                        4
    bronze pots              4                        8
    saron                    8                       16
    peking                  16                       32
    (gong, the fixed anchor: 1 per cycle in both halves)

At the seam (beat 256) the tempo map halves (96 -> 48 bpm) while the
whole moving hierarchy doubles its per-beat density — the fastest
layer (peking) goes from 1 to 2 notes per beat — so notes-per-second
hold roughly steady while the gong cycle stretches from 10 s to 20 s:
the classic irama transition.  The seam is the exact time-midpoint of
the cycled music (160 s of irama I, 160 s of irama II).  Design note:
the HLD's "2x chain" and "only the fastest doubles" cannot BOTH be
strict (a strict chain over a 1-per-cycle gong forces the gong to 2);
this module keeps the chain strict across the four moving layers and
lets the gong anchor the chain at ratio 2 (irama I) / 4 (irama II).

MATERIAL
--------
Balungan rows (pentatonic tone indices 0-4 over C D F G A), both
arriving on the gong tone C at every cycle head:
    ROW_A: C D F D F A G D        ROW_B: C G F G A F D D
Saron carries the row (doubled note-for-note in irama II); peking
alternates each row tone with the NEXT row tone (nacah); the pots ring
every other row tone an octave above; the kemanak clang a fixed
A5/D6 pair.  The rebab (GM 110, portamento + CC1 vibrato + CC11
breath) floats free across movements II-V — seeded random-walk
phrases, exempt from the density chain by design and by oracle.
Chorale: material.play_chorale (recomputed, never re-typed), root A3,
stated twice — Chorale I at beat 336, Chorale II at beat 368 — both
UNTRUNCATED (8 chords x 4 voices), the second landing so its final
chord resolves as the last gong falls.

ORACLES (written before the music; the music is composed to pass)
-----------------------------------------------------------------
colotomy_gong       gong onsets == every 16-beat boundary, nothing else
tuning_table        RPN-2 + exactly one static bend per bronze channel,
                    cent-exact; rebab/strings bend-free
density_hierarchy   exact per-cycle counts and the strict 2x chain
irama_shift         tempo halves at beat 256 == the time midpoint;
                    peking 16 -> 32 notes/cycle across the seam
pentatonic_bronze   all bronze + rebab pitch classes in {C D F G A}
rebab_free          fiddle only, enters mvt II, per-cycle counts VARY
chorale_coexist     both statements complete; bronze sounds beneath
dynamic_arc         build to a crest at cycle 16, irama drop, flat
                    chorale plateau, final gong the loudest stroke
"""

from __future__ import annotations

import random

import conductor
import engine as en
import material

NUMBER = 13
TITLE = 'Bronze Water'
FILE = '13 - Bronze Water.mid'
SEED = 20260913

COMMENT = ("Gamelan-inspired colotomy: slendro-approximating static "
           "per-channel detunes (+0/+40/-20/+20/+60 cents), 16-beat gong "
           "cycles, a strict 2x density hierarchy, an irama shift at the "
           "time midpoint, a free-floating rebab, and a closing Western "
           "string chorale coexisting with the bronze.")

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_GONG = 0       # GM 14 tubular bells + CC0 alt bank -> tam-tam / gong ageng
CH_KEMANAK = 1    # GM 113 agogo
CH_POTS = 2       # GM 112 tinkle bell
CH_SARON = 3      # GM 8 celesta
CH_PEKING = 4     # GM 9 glockenspiel
CH_REBAB = 5      # GM 110 fiddle
CH_STRINGS = 6    # GM 48 string ensemble

BRONZE = (CH_GONG, CH_KEMANAK, CH_POTS, CH_SARON, CH_PEKING)

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

BPM_1, BPM_2 = 96.0, 48.0
CYCLE = 16.0
N_CYC_H1, N_CYC_H2 = 16, 8
N_CYC = N_CYC_H1 + N_CYC_H2
SEAM = CYCLE * N_CYC_H1            # 256.0 — the irama gear-change
END_CYCLES = CYCLE * N_CYC         # 384.0 — the final gong boundary
END = 396.0                        # the final gong rings 12 beats

# ---------------------------------------------------------------------------
# Tuning (see module docstring) and pitch material
# ---------------------------------------------------------------------------

TUNING_CENTS: list[tuple[int, float]] = [
    (CH_GONG, 0.0), (CH_KEMANAK, 40.0), (CH_POTS, -20.0),
    (CH_SARON, 20.0), (CH_PEKING, 60.0),
]
CENT_TOL = 0.05                    # 14-bit quantization is ~0.0244 c

_SCALE = [0, 2, 5, 7, 9]           # C D F G A above the tonic
_PENTA_PCS = {0, 2, 5, 7, 9}
GONG_PITCH = 36                    # C2 — the C2 floor, honoured exactly
KEMANAK_PAIR = (81, 86)            # A5 / D6, both pentatonic tones

ROW_A = [0, 1, 2, 1, 2, 4, 3, 1]   # C D F D F A G D
ROW_B = [0, 3, 2, 3, 4, 2, 1, 1]   # C G F G A F D D
_ROWS = (ROW_A, ROW_B)

CHORALE_ROOT = 57                  # A3 — A aeolian contains all five bronze pcs
CHORALE_T1, CHORALE_T2 = 336.0, 368.0

# Per-cycle base velocity: build across irama I to a crest at cycle 16,
# drop into irama II, swell, then a FLAT plateau under the chorale so the
# audio chorale-lift is attributable to the strings alone.
_CYCLE_BASE = [52, 55, 58, 61,                 # I.  surface
               62, 64, 65, 67, 68, 70,         # II. rebab floats
               70, 72, 75, 78, 81, 85,         # III. crest
               66, 68, 70, 72,                 # IV. irama II
               74, 74, 74, 74]                 # V.  chorale plateau
FINAL_GONG_VEL = 106

# ---------------------------------------------------------------------------
# PART
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Surface - bronze alone", 0.0, 64.0),
        ("II. The rebab floats", 64.0, 160.0),
        ("III. Bronze crest", 160.0, 256.0),
        ("IV. Irama II - deep water", 256.0, 320.0),
        ("V. Chorale on bronze water", 320.0, 384.0),
        ("VI. Gong ageng", 384.0, END),
    ],
    tempo_map=[(0.0, BPM_1), (SEAM, BPM_2)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],                     # A minor (the chorale's key)
    channels=[
        (CH_GONG,    "gong ageng",       14, 100, 64, 75),
        (CH_KEMANAK, "kemanak",         113,  84, 78, 55),
        (CH_POTS,    "bronze pots",     112,  82, 50, 60),
        (CH_SARON,   "saron",             8,  96, 56, 50),
        (CH_PEKING,  "peking",            9,  78, 72, 50),
        (CH_REBAB,   "rebab",           110,  92, 64, 65),
        (CH_STRINGS, "chorale strings",  48, 100, 64, 60),
    ],
    bank_selects=[(1, 1), (2, 1)],   # kemanak + bronze pots: percussion set B
    extra_markers=[(CHORALE_T1, "Chorale I"), (CHORALE_T2, "Chorale II")],
)

# ---------------------------------------------------------------------------
# Verification config (consumed by verify.run_track)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST: set[int] = {8, 9, 14, 48, 110, 112, 113}
CENTERED_CHANNELS: set[int] = {CH_GONG, CH_REBAB, CH_STRINGS}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_GONG: (36, 36),
    CH_KEMANAK: (81, 86),
    CH_POTS: (84, 93),
    CH_SARON: (60, 69),
    CH_PEKING: (72, 81),
    CH_REBAB: (60, 84),
    CH_STRINGS: (47, 76),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set(BRONZE)            # static slendro detunes
DURATION_WINDOW: tuple[float, float] = (330.0, 345.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# The bronze machine
# ---------------------------------------------------------------------------

def _next_tone(row: list[int], nxt: list[int], step: int) -> int:
    """The balungan tone AFTER `step` (wrapping into the next cycle's row) —
    the peking always leans toward where the melody is going."""
    return row[step + 1] if step + 1 < len(row) else nxt[0]


def _bronze_cycles(sc: en.Score, c0: int, c1: int) -> None:
    """Write gong cycles c0..c1-1 (0-based).  Irama by cycle index.

    Every bronze note is authored jt=0 so the per-cycle density counts,
    and the gong's boundary onsets, are tick-exact for the oracles."""
    for c in range(c0, c1):
        t = CYCLE * c
        base = _CYCLE_BASE[c]
        row = _ROWS[c % 2]
        nxt = _ROWS[(c + 1) % 2]
        irama2 = c >= N_CYC_H1

        # Gong ageng: one stroke, exactly on the boundary, jitter-free.
        sc.note(CH_GONG, GONG_PITCH, t, 12.0, min(110, base + 16),
                jt=0, jv=0)

        # Kemanak: the fixed A5/D6 pair, low-high alternation.
        k_n = 4 if irama2 else 2
        k_sp = CYCLE / k_n
        for i in range(k_n):
            sc.note(CH_KEMANAK, KEMANAK_PAIR[i % 2], t + k_sp * i, 0.3,
                    base + 2, jt=0, jv=3)

        # Bronze pots: every other row tone (irama I) / the full row
        # (irama II), an octave above the saron.
        p_n = 8 if irama2 else 4
        p_sp = CYCLE / p_n
        for i in range(p_n):
            tone = row[i] if irama2 else row[2 * i]
            v = base - 4 + (5 if i % 2 == 0 else 0)
            sc.note(CH_POTS, 84 + _SCALE[tone], t + p_sp * i, 1.2, v,
                    jt=0, jv=3)

        # Saron: the balungan row; note-for-note doubled in irama II.
        s_n = 16 if irama2 else 8
        s_sp = CYCLE / s_n
        for i in range(s_n):
            tone = row[i // 2] if irama2 else row[i]
            v = base + (5 if i % (s_n // 2) == 0 else 0)
            sc.note(CH_SARON, 60 + _SCALE[tone], t + s_sp * i,
                    s_sp * 0.9, v, jt=0, jv=3)

        # Peking: alternates each row tone with the NEXT tone (nacah);
        # in irama II the alternation itself doubles (nacah rangkep).
        pk_n = 32 if irama2 else 16
        pk_sp = CYCLE / pk_n
        per_step = pk_n // len(row)
        for i in range(pk_n):
            step = i // per_step
            tone = row[step] if i % 2 == 0 else _next_tone(row, nxt, step)
            v = base - 6 + (3 if i % (per_step * 2) == 0
                            else (-2 if i % 2 else 0))
            sc.note(CH_PEKING, 72 + _SCALE[tone], t + pk_sp * i,
                    pk_sp * 0.85, v, jt=0, jv=3)


# ---------------------------------------------------------------------------
# The rebab — floats free of the density chain
# ---------------------------------------------------------------------------

def _rebab(sc: en.Score, mi: int, t0: float, t1: float) -> None:
    """One movement's share of the rebab line: seeded random-walk phrases
    over the pentatonic, portamento slides, CC11 breath, CC1 vibrato
    blooming on each phrase-final long tone.  Deterministic: the RNG is
    derived from SEED and the movement index, constructed here."""
    rng = random.Random(SEED * 100003 + mi * 977 + 5)
    tone = rng.randint(3, 7)                   # absolute index 0..10
    t = t0 + rng.choice([1.0, 1.5, 2.0])
    while t < t1 - 7.0:
        n_notes = rng.randint(3, 6)
        phrase: list[tuple[float, float, int, int]] = []
        pt = t
        for k in range(n_notes):
            if pt >= t1 - 1.6:
                break
            last = k == n_notes - 1
            dur = rng.choice([2.0, 3.0, 4.0] if last
                             else [1.0, 1.0, 1.5, 2.0])
            dur = max(0.5, min(dur, (t1 - 0.4) - pt))
            tone = max(0, min(10, tone + rng.choice([-2, -1, -1, 1, 1, 2])))
            p = 60 + 12 * (tone // 5) + _SCALE[tone % 5]
            base = _CYCLE_BASE[min(N_CYC - 1, int(pt // CYCLE))]
            vel = max(48, min(88, base - 2 + rng.randint(-3, 3)))
            phrase.append((pt, dur, p, vel))
            pt += dur
        for b, d, p, v in phrase:
            sc.note(CH_REBAB, p, b, d * 0.97, v, jt=4, jv=3)
        end = phrase[-1][0] + phrase[-1][1]
        en.expr_curve(sc, CH_REBAB, [(t - 0.3, 52), (t + 0.5, 78),
                                     (end - 1.0, 88), (end, 58)], step=0.5)
        fb, fd, _p, _v = phrase[-1]
        en.cc_curve(sc, CH_REBAB, 1, [(fb, 8), (fb + 0.6, 14),
                                      (fb + fd * 0.7, 66), (end, 22)],
                    step=0.25)
        t = end + rng.choice([1.0, 1.25, 1.5])


# ---------------------------------------------------------------------------
# Movement builders
# ---------------------------------------------------------------------------

def _m1(sc: en.Score) -> None:
    """I. Surface — the tuning table, the alt-bank gong, cycles 1-4."""
    for ch, cents in TUNING_CENTS:
        en.bend_range(sc, ch, 2, 0.0)          # RPN 0 = 2 semitones
        sc.bend(ch, 0.0, cents / 100.0)        # the static slendro offset
    sc.cc(CH_GONG, 0, 1, 0.0)                  # CC0 nonzero: gong ageng bank
    _bronze_cycles(sc, 0, 4)


def _m2(sc: en.Score) -> None:
    """II. The rebab floats — cycles 5-10; the fiddle enters, gliding."""
    en.portamento_on(sc, CH_REBAB, 64.0, time_cc=52)
    _bronze_cycles(sc, 4, 10)
    _rebab(sc, 2, 64.0, 160.0)


def _m3(sc: en.Score) -> None:
    """III. Bronze crest — cycles 11-16 build to the irama-I peak."""
    _bronze_cycles(sc, 10, 16)
    _rebab(sc, 3, 160.0, 256.0)


def _m4(sc: en.Score) -> None:
    """IV. Irama II — tempo halves, the hierarchy doubles, water deepens."""
    _bronze_cycles(sc, 16, 20)
    _rebab(sc, 4, 256.0, 320.0)


def _m5(sc: en.Score) -> None:
    """V. Chorale on bronze water — two untruncated statements coexist
    with the unbroken bronze cycle; the rebab yields after Chorale I."""
    _bronze_cycles(sc, 20, 24)
    _rebab(sc, 5, 320.0, 352.0)
    en.portamento_off(sc, CH_REBAB, 352.0)
    en.expr_curve(sc, CH_STRINGS, [(334.0, 66), (336.0, 74), (344.0, 88),
                                   (351.0, 74), (352.0, 60)], step=0.5)
    material.play_chorale(sc, CH_STRINGS, CHORALE_T1, CHORALE_ROOT, vel=62)
    # Chorale II is the climactic statement, authored a full forte
    # (vel 88, expression peaking at 127 — the synth maps CC7 and CC11
    # to amplitude on squared curves, so expression headroom is the
    # strongest per-point lever).  The GM 48 ensemble sits ~13 dB under
    # the bronze bed at mezzo levels (measured from a --solo 6 stem
    # against the full-mix pre-normalization peaks), so a mezzo second
    # statement reads in the event data but not the RENDER; this forte
    # lands the strings ~5 dB under the bronze — an audible lift
    # (analyze.py: audio_chorale_lift >= +0.5 dB, measured ~+1.2 dB,
    # so the claim holds with margin) that still coexists with, never
    # replaces, the bronze.
    en.expr_curve(sc, CH_STRINGS, [(366.0, 92), (368.0, 112), (376.0, 127),
                                   (383.0, 118)], step=0.5)
    material.play_chorale(sc, CH_STRINGS, CHORALE_T2, CHORALE_ROOT, vel=88)


def _m6(sc: en.Score) -> None:
    """VI. Gong ageng — the final stroke, the loudest, ringing out."""
    sc.note(CH_GONG, GONG_PITCH, END_CYCLES, 12.0, FINAL_GONG_VEL,
            jt=0, jv=0)


BUILDERS: list = [_m1, _m2, _m3, _m4, _m5, _m6]


# ---------------------------------------------------------------------------
# Oracle helpers (event extraction mirrors verify.py's conventions)
# ---------------------------------------------------------------------------

def _ons(sc: en.Score, ch: int) -> list[tuple[float, int, int]]:
    """Sorted (beat, pitch, velocity) note-ons for a channel."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick / en.PPQ, data[1], data[2]))
    return sorted(out)


def _ccs(sc: en.Score, ch: int, num: int) -> list[tuple[float, int]]:
    return sorted((tick / en.PPQ, data[2])
                  for tick, _p, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xB0 and data[1] == num)


def _bend_events(sc: en.Score, ch: int) -> list[tuple[float, float]]:
    out = []
    for tick, _p, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / en.PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _cycle_count(ons: list[tuple[float, int, int]], c: int) -> int:
    lo, hi = CYCLE * c, CYCLE * (c + 1)
    return sum(1 for b, _p, _v in ons if lo <= b < hi)


def _density_table(c: int) -> dict[int, int]:
    if c < N_CYC_H1:
        return {CH_KEMANAK: 2, CH_POTS: 4, CH_SARON: 8, CH_PEKING: 16}
    return {CH_KEMANAK: 4, CH_POTS: 8, CH_SARON: 16, CH_PEKING: 32}


# ---------------------------------------------------------------------------
# Track-specific oracles (written before the music)
# ---------------------------------------------------------------------------

def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    res: list[tuple[str, list[str]]] = []

    # -- colotomy: gong strokes EXACTLY on every 16-beat cycle boundary
    #    (0, 16, ..., 384) and nowhere else; alt bank selected at t=0. ------
    fails: list[str] = []
    gongs = _ons(sc, CH_GONG)
    want = [CYCLE * k for k in range(N_CYC + 1)]
    got = [b for b, _p, _v in gongs]
    if len(got) != len(want):
        fails.append(f"{len(got)} gong strokes, want {len(want)}")
    else:
        for g, w in zip(got, want):
            if abs(g - w) > 1e-6:
                fails.append(f"gong stroke at beat {g} != boundary {w}")
    for b, p, _v in gongs:
        if p != GONG_PITCH:
            fails.append(f"gong pitch {p} at beat {b:.1f} != {GONG_PITCH}")
    cc0 = [v for b, v in _ccs(sc, CH_GONG, 0) if b <= 1e-6]
    if not cc0 or cc0[-1] == 0:
        fails.append("gong channel must select CC0 != 0 (alt bank) at t=0")
    res.append(("colotomy_gong", fails[:8]))

    # -- tuning table: RPN bend-range 2 plus exactly ONE static bend per
    #    bronze channel, cent-exact; the 12-TET voices author no bends. ----
    fails = []
    for ch, cents in TUNING_CENTS:
        c6 = [v for b, v in _ccs(sc, ch, 6) if b <= 0.02]
        c101 = [v for b, v in _ccs(sc, ch, 101) if b <= 0.02]
        if 2 not in c6 or 0 not in c101:
            fails.append(f"ch{ch}: RPN bend-range-2 not authored at t=0")
        bends = _bend_events(sc, ch)
        if len(bends) != 1 or bends[0][0] > 1e-9:
            fails.append(f"ch{ch}: want exactly one bend at t=0, got "
                         f"{[(b, round(f, 4)) for b, f in bends[:3]]}")
        else:
            got_c = bends[0][1] * 200.0
            if abs(got_c - cents) > CENT_TOL:
                fails.append(f"ch{ch}: offset {got_c:+.2f} c != "
                             f"{cents:+.2f} c")
    for ch in (CH_REBAB, CH_STRINGS):
        if _bend_events(sc, ch):
            fails.append(f"ch{ch} must stay 12-TET (no bends)")
    res.append(("tuning_table", fails[:8]))

    # -- density hierarchy: exact per-cycle counts, strict 2x chain. -------
    fails = []
    ons_by = {ch: _ons(sc, ch) for ch in BRONZE}
    for c in range(N_CYC):
        cnt = {ch: _cycle_count(ons_by[ch], c) for ch in BRONZE}
        if cnt[CH_GONG] != 1:
            fails.append(f"cycle {c + 1}: {cnt[CH_GONG]} gongs, want 1")
        for ch, wanted in _density_table(c).items():
            if cnt[ch] != wanted:
                fails.append(f"cycle {c + 1}: ch{ch} has {cnt[ch]} notes, "
                             f"want {wanted}")
        chain = (cnt[CH_KEMANAK], cnt[CH_POTS], cnt[CH_SARON],
                 cnt[CH_PEKING])
        if any(2 * a != b for a, b in zip(chain, chain[1:])):
            fails.append(f"cycle {c + 1}: chain {chain} is not strict 2x")
    res.append(("density_hierarchy", fails[:8]))

    # -- irama shift: tempo halves at the seam == the time midpoint of the
    #    cycled music; the fastest layer's per-beat density doubles. -------
    fails = []
    if PART.TEMPO_MAP != [(0.0, BPM_1), (SEAM, BPM_2)] or BPM_2 * 2 != BPM_1:
        fails.append(f"tempo map {PART.TEMPO_MAP} must halve {BPM_1} -> "
                     f"{BPM_1 / 2} at beat {SEAM}")
    mid, full = sc.seconds_at(SEAM), sc.seconds_at(END_CYCLES)
    if abs(mid - (full - mid)) > 1e-6:
        fails.append(f"seam at {mid:.2f} s is not the time midpoint of "
                     f"{full:.2f} s of cycles")
    pre = _cycle_count(_ons(sc, CH_PEKING), N_CYC_H1 - 1)
    post = _cycle_count(_ons(sc, CH_PEKING), N_CYC_H1)
    if (pre, post) != (16, 32):
        fails.append(f"peking across the seam: {pre} -> {post} per cycle, "
                     f"want 16 -> 32 (per-beat density 1 -> 2)")
    res.append(("irama_shift", fails[:8]))

    # -- pentatonic bronze: every bronze + rebab pitch class in C D F G A. -
    fails = []
    for ch in list(BRONZE) + [CH_REBAB]:
        for b, p, _v in _ons(sc, ch):
            if p % 12 not in _PENTA_PCS:
                fails.append(f"ch{ch} pitch {p} at beat {b:.1f} is outside "
                             f"the 5-tone scale")
    res.append(("pentatonic_bronze", fails[:8]))

    # -- rebab floats free: fiddle only, enters mvt II, leaves before
    #    Chorale II, per-cycle counts VARY (exempt from the chain). --------
    fails = []
    progs = [(tick / en.PPQ, data[1]) for tick, _p, data
             in sc.events.get(CH_REBAB, [])
             if (data[0] & 0xF0) == 0xC0]
    if progs != [(0.0, 110)]:
        fails.append(f"rebab programs {progs} != [(0.0, 110)]")
    r_ons = _ons(sc, CH_REBAB)
    if len(r_ons) < 40:
        fails.append(f"only {len(r_ons)} rebab notes, want >= 40")
    if r_ons and (r_ons[0][0] < 64.0 - 0.05 or r_ons[-1][0] >= 352.0):
        fails.append(f"rebab must sing inside [64, 352), got "
                     f"[{r_ons[0][0]:.2f}, {r_ons[-1][0]:.2f}]")
    counts = [_cycle_count(r_ons, c) for c in range(4, 22)]
    if len(set(counts)) < 2:
        fails.append(f"rebab per-cycle counts {counts} are uniform - it "
                     f"must float free of the density chain")
    if not any(v == 127 for _b, v in _ccs(sc, CH_REBAB, 65)):
        fails.append("rebab portamento (CC65 on) not authored")
    if not any(v == 0 for _b, v in _ccs(sc, CH_REBAB, 65)):
        fails.append("rebab portamento never released (CC65 off missing)")
    if not any(v > 0 for _b, v in _ccs(sc, CH_REBAB, 1)):
        fails.append("rebab CC1 vibrato not authored")
    res.append(("rebab_free", fails[:8]))

    # -- chorale coexistence: two complete (untruncated) statements of the
    #    material.py chorale, recomputed here, with bronze beneath both. ---
    fails = []
    want_chords = material.chorale_pitches(CHORALE_ROOT)
    s_ons = _ons(sc, CH_STRINGS)
    if len(s_ons) != 2 * 4 * len(want_chords):
        fails.append(f"{len(s_ons)} string notes != two untruncated "
                     f"statements ({2 * 4 * len(want_chords)})")
    for t_stmt in (CHORALE_T1, CHORALE_T2):
        for i, satb in enumerate(want_chords):
            t_chord = t_stmt + material.CHORALE_CHORD_BEATS * i
            got_p = sorted(p for b, p, _v in s_ons
                           if abs(b - t_chord) <= 0.05)
            if got_p != sorted(satb):
                fails.append(f"statement at {t_stmt:.0f}, chord {i + 1}: "
                             f"pitches {got_p} != {sorted(satb)}")
    bronze_under = sum(1 for ch in BRONZE for b, _p, _v in _ons(sc, ch)
                       if CHORALE_T2 <= b < END_CYCLES)
    if bronze_under < 32:
        fails.append(f"only {bronze_under} bronze notes under Chorale II - "
                     f"the cycle must coexist, not yield")
    res.append(("chorale_coexist", fails[:8]))

    # -- dynamic arc: build to the crest, irama drop, flat chorale plateau,
    #    final gong the loudest stroke of the piece. -----------------------
    fails = []

    def cyc_mean(c: int) -> float:
        vels = [v for ch in BRONZE for b, _p, v in ons_by[ch]
                if CYCLE * c <= b < CYCLE * (c + 1)]
        return sum(vels) / len(vels) if vels else 0.0

    means = [cyc_mean(c) for c in range(N_CYC)]
    if means[15] - means[0] < 20.0:
        fails.append(f"crest {means[15]:.1f} < opening {means[0]:.1f} + 20")
    for c in range(15):
        if means[c] >= means[15]:
            fails.append(f"cycle {c + 1} mean {means[c]:.1f} >= crest "
                         f"cycle 16 ({means[15]:.1f})")
    if means[16] > means[15] - 12.0:
        fails.append(f"irama drop: cycle 17 mean {means[16]:.1f} not "
                     f">= 12 below the crest {means[15]:.1f}")
    if abs(means[21] - means[22]) > 2.0:
        fails.append(f"chorale plateau not flat: cycles 22/23 means "
                     f"{means[21]:.1f} vs {means[22]:.1f}")
    g_vels = [v for _b, _p, v in gongs]
    if g_vels and (g_vels[-1] < 96 or g_vels[-1] <= max(g_vels[:-1])):
        fails.append(f"final gong vel {g_vels[-1]} must be >= 96 and the "
                     f"loudest stroke (max earlier: {max(g_vels[:-1])})")
    res.append(("dynamic_arc", fails[:8]))

    return res


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/13 - Bronze Water.wav
# exists; mirrors the headline claims in rendered dB, not velocities)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    def win_db(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    res: list[tuple[str, list[str]]] = []

    # The irama-I build is audible: crest cycle >= opening cycle + 3 dB.
    quiet, crest = win_db(0.0, 16.0), win_db(240.0, 256.0)
    fails = [] if crest >= quiet + 3.0 else [
        f"crest {crest:.1f} dB < opening {quiet:.1f} dB + 3"]
    res.append(("audio_crest", fails))

    # The gear-change does not collapse: the first irama-II cycles hold
    # within 6 dB of the crest (density doubles as the tempo halves).
    post = win_db(SEAM, SEAM + 32.0)
    fails = [] if post >= crest - 6.0 else [
        f"irama II opens {post:.1f} dB, more than 6 dB under the "
        f"crest {crest:.1f} dB"]
    res.append(("audio_irama_alive", fails))

    # Chorale II adds audible energy over the identical bronze-only cycle
    # before it (bronze velocities are flat across cycles 21-24 and the
    # rebab is silent in both windows, so the lift is the strings).
    bronze_only, with_chorale = win_db(352.0, 368.0), win_db(368.0, 384.0)
    fails = [] if with_chorale >= bronze_only + 0.5 else [
        f"Chorale II cycle {with_chorale:.1f} dB not >= bronze-only cycle "
        f"{bronze_only:.1f} dB + 0.5"]
    res.append(("audio_chorale_lift", fails))

    # The final gong is present and decays: bloom window audible, late
    # tail at least 1 dB below it.
    bloom, tail = win_db(END_CYCLES, END_CYCLES + 4.0), win_db(392.0, END)
    fails = []
    if bloom < -45.0:
        fails.append(f"final gong bloom {bloom:.1f} dB below -45 dB")
    if tail > bloom - 1.0:
        fails.append(f"gong tail {tail:.1f} dB does not decay from bloom "
                     f"{bloom:.1f} dB")
    res.append(("audio_gong_tail", fails))
    return res
