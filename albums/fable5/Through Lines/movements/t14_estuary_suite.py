"""t14_estuary_suite — Track 14 "The Estuary Suite" of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T14: the centerpiece — eight
original songs plus a hidden epilogue, seamlessly segued in the Abbey Road
side-2 medley dramaturgy (the FLOW is the homage; zero Beatles material):
ballad -> dream -> two grotesques -> soul -> lullaby-anthem -> finale with
trading solos -> scored silence -> a tiny acoustic afterthought, cut off.

Every headline claim is a falsifiable oracle (oracles() was written BEFORE
the music; the suite is composed to pass it):

 * (a) The Ledger states material.LEDGER_THEME — recomputed from
   material.py, never re-typed — five times (`ledger_theme`: piano
   note-fidelity at the five documented statements, incl. the octave-up
   fourth pass), then collapses via honky-tonk double-time
   (`honky_tonk_collapse`: ch0 program lane exactly 0 -> 3 at 120 -> 0 at
   176; tempo 132 >= 1.7x the ballad's 72; piano onset density in the
   honky span >= 1.5x the ballad verses).
 * (b) Sun on the Estuary breathes ONE chord (`sun_one_chord`: every
   sustained-channel pitch in [176, 264) is an F-triad pitch class; the
   transient sparkles and the flute stay inside F major pentatonic; choir
   CC70 morphs mm->ah, span 20..80+; organ CC1 Leslie spread >= 60), with
   birdsong flute (`sun_birdsong`: >= 12 short high calls in >= 4
   separated clusters).
 * (c) Mr. Mudlark is a fuzz grotesque (`mudlark_fuzz`: lead GM 30 and
   rhythm GM 29 drive guitars; the 2-bar RIFF_MUD stated 12 times
   note-for-note; backbeat snare coverage >= 90% of stomp bars).
 * (d) Polly on the Towpath slides (`polly_slides`: >= 12 pitch-bend
   slide gestures on the lead inside [396, 580), each excursion >= 0.5
   semitone and recentred within 2 beats).
 * (e) Out of My Window hangs on a syncopated hook (`window_hook`: the
   HOOK_WIN figure stated >= 6 times by brass AND electric piano in
   octaves at the documented beats; >= 50% of its onsets off the beat).
 * (f) Slumber Line swells into (g) (`slumber_swell`: 3/4 authored at
   748; mean velocity of the lullaby's second half > first half; the
   anthem's opening beats denser than the lullaby's close).
 * (g) Carry the Current's ground bass IS the FABLE cell (`fable_ground`:
   42 consecutive 4-beat loops recomputed from material.FABLE_CELL at F2,
   onsets AND pitches, with NO bass onset inside the silent L of any
   loop).
 * (h) The End of the Line opens the album's only drum break
   (`drum_break_alone`: one melodically-silent span with drums active in
   the whole track, exactly the 3 bars [998, 1010), >= 16 hits), then
   guitar/organ/fiddle trade strict 2-bar solos x3 rounds
   (`trading_solos`: nine 8-beat cells, owner plays >= 5 notes, the other
   two soloists exactly 0), and the final chorale resolves the FABLE cell
   against its own inversion to the major tonic (`final_chorale`: strings
   state the cell 2x-augmented at 1082 and 1090, cello mirrors it exactly
   inverted, E resolves up to F, inverted-E down to F, and the resolution
   chord is F MAJOR — pitch class A present, Ab absent).
 * The medley is seamless (`segue_continuity`: between songs (a)-(h) no
   all-channel silence > 0.5 s, measured in seconds via the tempo map),
   then holds 18-22 s of scored silence (`hidden_silence`: the gap from
   the last (h) note-off to the first (i) note-on, via sc.seconds_at,
   in [18, 22]; GAP_WHITELIST covers it) before (i) the hidden epilogue
   quotes The Ledger and is cut off mid-phrase (`epilogue_quote`: exactly
   material.LEDGER_EPILOGUE_NOTES dulcimer notes, note-fidelity against
   material.LEDGER_THEME transposed up an octave, nothing else sounding,
   and they are the last notes of the file).
 * The dramatic shape as numbers (`suite_dynamic_arc`: sun < mudlark,
   anthem crest the densest late window, epilogue quiet but >= vel 40);
   audio_checks() holds the RENDER to the same contour in dB.

Movements (the songs):
    (a) The Ledger              0-176    A minor -> C, 72 then 132 bpm
    (b) Sun on the Estuary    176-264    F, 62 bpm, one chord breathing
    (c) Mr. Mudlark           264-396    E minor, 112 bpm fuzz stomp
    (d) Polly on the Towpath  396-580    A, 138 bpm slide rocker
    (e) Out of My Window      580-748    C minor, 98 bpm soul
    (f) Slumber Line          748-814    F, 69 bpm, 3/4 lullaby
    (g) Carry the Current     814-990    F, 88 bpm, FABLE ground anthem
    (h) The End of the Line   990-1130   D minor -> F major, 116 bpm
    (i) The Ledger, Again    1130-1166   hidden: silence then solo pluck
"""

from __future__ import annotations

import random

import conductor
import engine as en
import material

NUMBER = 14
TITLE = 'The Estuary Suite'
FILE = '14 - The Estuary Suite.mid'
SEED = 20260914

COMMENT = ("Track 14: the centerpiece. Eight songs and a hidden epilogue "
           "in the side-2 medley manner: a ledger ballad gone honky-tonk, "
           "one chord in the sun, two canal grotesques, a soul window, a "
           "lullaby that becomes an anthem on the FABLE ground, the only "
           "drum break, trading twos, a chorale against its own mirror, "
           "twenty seconds of nothing, and a dulcimer that stops mid-line.")

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_PNO = 0        # piano (GM 0; GM 3 honky-tonk inside the collapse)
CH_BASS = 1       # bass (GM 32 acoustic; GM 33 fingered from (c) on)
CH_LEAD = 2       # lead guitar (GM 30 fuzz; GM 29 slide-overdrive in (d))
CH_ORG = 3        # drawbar organ (GM 16, CC1 Leslie)
CH_CHOIR = 4      # choir (GM 52, CC70 vowels)
CH_STR = 5        # strings (GM 48)
CH_FLUTE = 6      # flute (GM 73) — the birdsong
CH_FID = 7        # fiddle (GM 110)
CH_CELLO = 8      # cello (GM 42)
CH_DRUMS = 9      # kit (v2 via ch-10 program 1)
CH_RTM = 10       # rhythm guitar (GM 29 drive; GM 28 palm-mute from (d))
CH_EP = 11        # electric piano (GM 4)
CH_BRASS = 12     # brass section (GM 61)
CH_HARP = 13      # harp (GM 46)
CH_DULC = 14      # dulcimer (GM 15) — the hidden epilogue's pluck
CH_PAD = 15       # warm pad (GM 89)

# ---------------------------------------------------------------------------
# The suite grid
# ---------------------------------------------------------------------------

A_T0 = 0.0
HONKY_T0 = 120.0
SUN_T0 = 176.0
MUD_T0 = 264.0
POL_T0 = 396.0
WIN_T0 = 580.0
SLU_T0 = 748.0
CUR_T0 = 814.0
ENDL_T0 = 990.0
SIL_T0 = 1130.0          # movement (i) opens with the scored silence
EPI_NOTE_T0 = 1150.0     # ... and the dulcimer enters here
EPI_END = 1166.0

BALLAD_BPM = 72.0
HONKY_BPM = 132.0
SUN_BPM = 62.0
MUD_BPM = 112.0
POL_BPM = 138.0
WIN_BPM = 98.0
SLU_BPM = 69.0
CUR_BPM = 88.0
ENDL_BPM = 116.0
TAIL_BPM = 60.0

# (a) The Ledger: the five documented theme statements (t0, base pitch).
LEDGER_STATEMENTS: tuple[tuple[float, int], ...] = (
    (8.0, 69), (24.0, 69), (48.0, 69), (64.0, 81), (88.0, 69))

# (e) the hook's documented full (brass + EP) statements.
HOOK_TIMES: tuple[float, ...] = (588.0, 596.0, 636.0, 644.0, 700.0, 708.0)

# (g) the ground: 42 consecutive FABLE loops from CUR_T0, then the cadence.
GROUND_ROOT = 41          # F2 (>= the C2 floor)
GROUND_LOOPS = 42
CADENCE_T0 = CUR_T0 + 4.0 * GROUND_LOOPS          # 982.0

# (h) internals.
BREAK_T0 = 998.0
BREAK_T1 = 1010.0
TRADE_T0 = 1010.0
TRADE_CELL = 8.0
SOLO_ORDER = (CH_LEAD, CH_ORG, CH_FID)            # guitar / organ / fiddle
TRADE_ROUNDS = 3
CHORALE_T0 = 1082.0
CHORALE_ROOT = 65         # F4: the cell sung where it can mirror
CHORALE_STRETCH = 2.0
RESOLVE_T0 = 1098.0
LAST_H_OFF = 1126.8       # the final chord's release (gap = ~21.7 s)

# (i) the epilogue quote: The Ledger, up an octave, in A minor.
EPI_BASE = 81

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("(a) The Ledger", A_T0, SUN_T0),
        ("(b) Sun on the Estuary", SUN_T0, MUD_T0),
        ("(c) Mr. Mudlark", MUD_T0, POL_T0),
        ("(d) Polly on the Towpath", POL_T0, WIN_T0),
        ("(e) Out of My Window", WIN_T0, SLU_T0),
        ("(f) Slumber Line", SLU_T0, CUR_T0),
        ("(g) Carry the Current", CUR_T0, ENDL_T0),
        ("(h) The End of the Line", ENDL_T0, SIL_T0),
        ("(i) The Ledger, Again (hidden)", SIL_T0, EPI_END),
    ],
    tempo_map=[
        (A_T0, BALLAD_BPM), (HONKY_T0, HONKY_BPM), (SUN_T0, SUN_BPM),
        (MUD_T0, MUD_BPM), (POL_T0, POL_BPM), (WIN_T0, WIN_BPM),
        (SLU_T0, SLU_BPM), (CUR_T0, CUR_BPM), (ENDL_T0, ENDL_BPM),
        (SIL_T0, TAIL_BPM),
    ],
    time_signatures=[(0.0, 4, 4), (SLU_T0, 3, 4), (CUR_T0, 4, 4)],
    keysigs=[
        (A_T0, 0, 1),        # A minor — the ledger
        (HONKY_T0, 0, 0),    # C major — the honky-tonk collapse
        (SUN_T0, -1, 0),     # F major — the sun
        (MUD_T0, 1, 1),      # E minor — the mudlark
        (POL_T0, 3, 0),      # A major — Polly
        (WIN_T0, -3, 1),     # C minor — the window
        (SLU_T0, -1, 0),     # F major — lullaby and anthem
        (ENDL_T0, -1, 1),    # D minor — the end of the line
        (CHORALE_T0, -1, 0),  # F major — the resolution
        (SIL_T0, 0, 1),      # A minor — the hidden ledger
    ],
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_PNO, "piano", 0, 100, 52, 42),
        (CH_BASS, "bass", 32, 105, 64, 26),
        (CH_LEAD, "lead guitar", 30, 92, 72, 40),
        (CH_ORG, "organ", 16, 90, 64, 45),
        (CH_CHOIR, "choir", 52, 92, 64, 62),
        (CH_STR, "strings", 48, 92, 64, 58),
        (CH_FLUTE, "flute", 73, 88, 64, 55),
        (CH_FID, "fiddle", 110, 92, 64, 48),
        (CH_CELLO, "cello", 42, 94, 64, 50),
        (CH_DRUMS, "drums", 0, 100, 64, 42),
        (CH_RTM, "rhythm guitar", 29, 84, 56, 35),
        (CH_EP, "electric piano", 4, 94, 74, 45),
        (CH_BRASS, "brass", 61, 92, 64, 48),
        (CH_HARP, "harp", 46, 90, 46, 58),
        (CH_DULC, "dulcimer", 15, 127, 64, 100),
        (CH_PAD, "pad", 89, 78, 64, 60),
    ],
    program_changes=[
        (CH_PNO, HONKY_T0, 3), (CH_PNO, SUN_T0, 0),
        (CH_BASS, MUD_T0, 33),
        (CH_LEAD, POL_T0, 29), (CH_LEAD, ENDL_T0, 30),
        (CH_RTM, POL_T0, 28),
        (CH_DRUMS, 0.0, 1),                      # the v2 kit
    ],
    extra_markers=[
        (HONKY_T0, "the Ledger goes honky-tonk"),
        (BREAK_T0, "the drum break"),
        (TRADE_T0, "trading twos: guitar / organ / fiddle"),
        (CHORALE_T0, "final chorale: FABLE vs its inversion"),
        (EPI_NOTE_T0, "hidden epilogue: the Ledger, cut off"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {0, 3, 4, 15, 16, 28, 29, 30, 32, 33, 42,
                               46, 48, 52, 61, 73, 89, 110}
CENTERED_CHANNELS: set[int] = {CH_BASS, CH_ORG, CH_CHOIR, CH_STR, CH_FLUTE,
                               CH_FID, CH_CELLO, CH_DRUMS, CH_BRASS,
                               CH_DULC, CH_PAD}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_PNO: (36, 96), CH_BASS: (36, 67), CH_LEAD: (40, 92),
    CH_ORG: (36, 86), CH_CHOIR: (48, 86), CH_STR: (41, 91),
    CH_FLUTE: (60, 100), CH_FID: (55, 93), CH_CELLO: (36, 79),
    CH_RTM: (40, 80), CH_EP: (36, 96), CH_BRASS: (46, 84),
    CH_HARP: (38, 95), CH_DULC: (57, 93), CH_PAD: (41, 84),
}
GAP_WHITELIST: list[tuple[float, float]] = [(1126.0, 1151.0)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (736.0, 758.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


def _rng(k: int) -> random.Random:
    """Deterministic per-song RNG (rebuilds must be byte-identical)."""
    return random.Random(SEED * 100 + k)


# ---------------------------------------------------------------------------
# Shared gesture helpers
# ---------------------------------------------------------------------------

def _scoop(sc: en.Score, ch: int, t: float, dur: float, p: int, vel: int,
           depth: float = 1.5, rise: float = 0.28) -> None:
    """A slide INTO a note: the bend starts `depth` semitones flat and
    glides up to centre across `rise` beats.  Ends recentred at 0."""
    sc.bend(ch, t - 0.02, -depth)
    en.bend_ramp(sc, ch, t, t + rise, -depth, 0.0, steps=5)
    sc.note(ch, p, t, dur, vel, jt=0, jv=2)


def _fall(sc: en.Score, ch: int, t_off: float, depth: float = 1.2) -> None:
    """A fall-off at a note's release; snaps back to centre just after."""
    en.bend_ramp(sc, ch, t_off - 0.18, t_off, 0.0, -depth, steps=4)
    sc.bend(ch, t_off + 0.06, 0.0)


def _ledger_theme(sc: en.Score, ch: int, t0: float, base: int, vel: int,
                  vel_end: int | None = None, gate: float = 0.97,
                  jt: int = 3, jv: int = 3) -> None:
    """One statement of material.LEDGER_THEME (recomputed, never typed)."""
    t = 0.0
    count = len(material.LEDGER_THEME)
    for i, (deg, dur) in enumerate(material.LEDGER_THEME):
        v = vel if vel_end is None else en.lerp(vel, vel_end,
                                                i / (count - 1))
        sc.note(ch, en.pitch(base, material.LEDGER_MODE, deg),
                t0 + t, dur * gate, int(v), jt=jt, jv=jv)
        t += dur


def _rock_bar(sc: en.Score, rng: random.Random, bt: float, crash: bool,
              kick_vel: int, snare_vel: int, hat_vel: int,
              open_hat: bool = True) -> None:
    """One 4-beat rock bar: kick 1/3, backbeat 2/4, eighth hats."""
    if crash:
        sc.hit(49, bt, snare_vel + 8, jt=2, jv=3)
    for rel in (0.0, 2.0):
        sc.hit(36, bt + rel, kick_vel + rng.randint(-3, 3), jt=2, jv=3)
    for rel in (1.0, 3.0):
        sc.hit(38, bt + rel, snare_vel + rng.randint(-3, 3), jt=2, jv=3)
    for e in range(8):
        drum = 46 if (open_hat and e == 7 and rng.random() < 0.35) else 42
        sc.hit(drum, bt + 0.5 * e,
               hat_vel + (5 if e % 2 == 0 else -4) + rng.randint(-2, 2),
               jt=2, jv=3)


def _drum_fill(sc: en.Score, rng: random.Random, t: float,
               beats: float = 2.0, vel: int = 72) -> None:
    """A tom fill across the last `beats` of a phrase."""
    toms = (50, 48, 47, 45, 43, 41)
    steps = int(beats * 2)
    for k in range(steps):
        drum = toms[min(len(toms) - 1, k * len(toms) // steps)]
        sc.hit(drum, t + 0.5 * k, vel + rng.randint(-4, 8), jt=2, jv=4)
        if rng.random() < 0.4:
            sc.hit(38, t + 0.5 * k + 0.25, vel - 14 + rng.randint(-4, 4),
                   jt=2, jv=4)


# ---------------------------------------------------------------------------
# (a) The Ledger — the wistful ballad and its honky-tonk collapse
# ---------------------------------------------------------------------------

# A-aeolian verse harmony under the theme: Am / G / F / Em, one bar each.
_BAR_CHORDS = ((45, 15), (43, 16), (41, 16), (40, 15))   # (root, third off)
_HONKY_BARS = [  # (stride bass low/alt, chord voicing) per honky bar
    (36, 43, (60, 64, 67)), (36, 43, (60, 64, 67)),
    (36, 43, (60, 64, 67)), (36, 43, (58, 60, 64)),      # C7
    (41, 48, (57, 60, 65)), (41, 48, (57, 60, 65)),
    (36, 43, (60, 64, 67)), (36, 43, (60, 64, 67)),
    (43, 50, (59, 62, 65)), (41, 48, (57, 60, 65)),      # G7 F
    (36, 43, (60, 64, 67)), (43, 50, (59, 62, 65)),      # C G7
]


def _ballad_lh(sc: en.Score, t0: float, n_cycles: int, vel: int,
               vel_end: int | None = None) -> None:
    """Broken-chord left hand, one bar per verse chord, with pedal."""
    total = n_cycles * 16.0
    for c in range(n_cycles):
        for i, (r, third) in enumerate(_BAR_CHORDS):
            bar = t0 + 16.0 * c + 4.0 * i
            v = vel if vel_end is None else int(
                en.lerp(vel, vel_end, (bar - t0) / total))
            en.sustain(sc, CH_PNO, bar, bar + 3.9)
            for rel, p, dv in ((0.0, r, 2), (1.0, r + 7, -4),
                               (2.0, r + 12, -2), (3.0, r + third, -5)):
                sc.note(CH_PNO, p, bar + rel, 1.9 if rel == 0.0 else 0.95,
                        v + dv, jt=3, jv=3)


def _ledger_frag(sc: en.Score, ch: int, t0: float, base: int,
                 vel: int) -> None:
    """Bar 1 of the theme only — the collapse-build fragment."""
    t = 0.0
    for deg, dur in material.LEDGER_THEME[:4]:
        sc.note(ch, en.pitch(base, material.LEDGER_MODE, deg),
                t0 + t, dur * 0.95, vel, jt=3, jv=3)
        t += dur


def _a_ledger(sc: en.Score) -> None:
    rng = _rng(1)
    # -- intro [0, 8): piano alone, then the cello breathes in ------------
    en.sustain(sc, CH_PNO, 0.0, 7.8)
    for rel, p, v in ((0.0, 45, 54), (1.0, 52, 48), (2.0, 57, 50),
                      (3.0, 60, 46), (4.0, 45, 52), (5.0, 52, 48),
                      (6.0, 57, 50), (7.0, 64, 48)):
        sc.note(CH_PNO, p, rel, 1.9, v, jt=3, jv=3)
    sc.note(CH_PNO, 69, 2.0, 2.0, 52, jt=3, jv=2)
    sc.note(CH_PNO, 71, 6.0, 2.0, 50, jt=3, jv=2)
    sc.note(CH_CELLO, 45, 4.0, 3.9, 44, jt=4, jv=2)
    en.expr_curve(sc, CH_CELLO, [(4.0, 60), (8.0, 76)], step=1.0)

    # -- V1 [8, 24) / V2 [24, 40): the theme, then the cello counter ------
    _ballad_lh(sc, 8.0, 2, 50, 56)
    _ledger_theme(sc, CH_PNO, 8.0, 69, 62)
    _ledger_theme(sc, CH_PNO, 24.0, 69, 66)
    counter = [(1, 0, 2), (3, 2, 2), (0, 4, 2), (2, 6, 2),
               (-1, 8, 2), (1, 10, 2), (0, 12, 2), (2, 14, 2)]
    en.line(sc, CH_CELLO, 24.0, 57, "aeolian", counter, vel=54, gate=0.97)
    en.cc_curve(sc, CH_CELLO, 11, [(24.0, 72), (32.0, 84), (39.5, 70)],
                step=1.0)

    # -- interlude [40, 48) ------------------------------------------------
    for i, (r, third) in enumerate(((45, 15), (40, 15))):
        bar = 40.0 + 4.0 * i
        en.sustain(sc, CH_PNO, bar, bar + 3.9)
        for rel, p in ((0.0, r), (1.0, r + 7), (2.0, r + 12),
                       (3.0, r + third)):
            sc.note(CH_PNO, p, bar + rel, 0.95, 50, jt=3, jv=3)
    en.line(sc, CH_PNO, 40.0, 69, "aeolian",
            [(8, 0, .5), (7, .5, .5), (6, 1, .5), (5, 1.5, .5),
             (4, 2, .5), (5, 2.5, .5), (3, 3, 1), (4, 4, .5),
             (3, 4.5, .5), (2, 5, .5), (3, 5.5, .5), (1, 6, 1.5)],
            vel=58, gate=0.95)

    # -- V3 [48, 64): strings under; V4 [64, 80): the octave-up pass ------
    _ballad_lh(sc, 48.0, 2, 54, 60)
    _ledger_theme(sc, CH_PNO, 48.0, 69, 68)
    en.pad_block(sc, CH_STR, 48.0,
                 [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 55, 59]],
                 span=4.0, size=4, lo=55, hi=79, vel=44, vel_end=50)
    _ledger_theme(sc, CH_PNO, 64.0, 81, 72)
    en.line(sc, CH_CELLO, 64.0, 57, "aeolian", counter, vel=58, gate=0.97)
    en.pad_block(sc, CH_STR, 64.0,
                 [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 55, 59]],
                 span=4.0, size=4, lo=55, hi=79, vel=50, vel_end=56)
    for i, r in enumerate((45, 43, 41, 40)):
        sc.note(CH_BASS, r, 64.0 + 4.0 * i, 3.9, 52, jt=4, jv=2)

    # -- turn [80, 88): the first daylight of C major ----------------------
    en.arp(sc, CH_PNO, [60, 64, 67, 72], 80.0, 8, 0.5, 58, gate=1.1)
    en.arp(sc, CH_PNO, [55, 59, 62, 67], 84.0, 8, 0.5, 60, gate=1.1)
    sc.note(CH_BASS, 48, 80.0, 3.9, 54, jt=4, jv=2)
    sc.note(CH_BASS, 43, 84.0, 3.9, 54, jt=4, jv=2)
    sc.note(CH_CELLO, 48, 80.0, 3.9, 56, jt=4, jv=2)
    sc.note(CH_CELLO, 43, 84.0, 3.9, 56, jt=4, jv=2)
    en.pad_block(sc, CH_STR, 80.0, [[60, 64, 67], [55, 59, 62]],
                 span=4.0, size=4, lo=55, hi=79, vel=52)

    # -- the build [88, 120): statement five, fragments, the pivot --------
    _ledger_theme(sc, CH_PNO, 88.0, 69, 74)
    for c in range(4):                       # pulsing eighth left hand
        r, third = _BAR_CHORDS[c]
        bar = 88.0 + 4.0 * c
        for e in range(8):
            p = r if e % 2 == 0 else r + 7
            sc.note(CH_PNO, p, bar + 0.5 * e, 0.45,
                    int(en.lerp(56, 66, c / 3)), jt=3, jv=3)
    en.pad_block(sc, CH_STR, 88.0,
                 [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 55, 59]],
                 span=4.0, size=4, lo=55, hi=79, vel=54, vel_end=62)
    for i, r in enumerate((45, 43, 41, 40)):
        sc.note(CH_BASS, r, 88.0 + 4.0 * i, 3.9, 56, jt=4, jv=2)
    _ledger_frag(sc, CH_PNO, 104.0, 69, 78)
    _ledger_frag(sc, CH_PNO, 108.0, 69, 82)
    for c in range(2):
        r, third = _BAR_CHORDS[c]
        bar = 104.0 + 4.0 * c
        for e in range(8):
            sc.note(CH_PNO, r if e % 2 == 0 else r + 7, bar + 0.5 * e,
                    0.45, 66 + 4 * c, jt=3, jv=3)
    for i, (b, p) in enumerate(((104.0, 45), (106.0, 47), (108.0, 48),
                                (110.0, 50), (112.0, 52), (114.0, 53),
                                (116.0, 55), (118.0, 55))):
        sc.note(CH_BASS, p, b, 1.9, int(en.lerp(58, 72, i / 7)), jt=3, jv=2)
        sc.note(CH_CELLO, p + 12, b, 1.9, int(en.lerp(60, 72, i / 7)),
                jt=3, jv=2)
    en.run(sc, CH_PNO, 112.0, 48, "ionian", list(range(1, 17)), 0.25,
           62, 86)
    for e in range(8):                       # G7 hammering into the honk
        for p in (55, 59, 62, 65):
            sc.note(CH_PNO, p, 116.0 + 0.5 * e, 0.45,
                    int(en.lerp(70, 84, e / 7)), jt=3, jv=3)
    en.pad_block(sc, CH_STR, 112.0, [[60, 64, 67], [55, 59, 62, 65]],
                 span=4.0, size=4, lo=55, hi=79, vel=60, vel_end=68)
    for k in range(8):                       # snare pickup into the honk
        sc.hit(38, 118.0 + 0.25 * k, int(en.lerp(40, 72, k / 7)),
               jt=2, jv=3)

    # -- the honky-tonk collapse [120, 176) --------------------------------
    sc.hit(49, HONKY_T0, 84, jt=0, jv=3)
    tones = {(60, 64, 67): (60, 64, 67, 72), (58, 60, 64): (58, 60, 64, 67),
             (57, 60, 65): (57, 60, 65, 69), (59, 62, 65): (59, 62, 65, 67)}
    for b, (lo, alt, chord) in enumerate(_HONKY_BARS):
        bar = HONKY_T0 + 4.0 * b
        vel = int(en.lerp(74, 86, b / 11))
        for rel, p in ((0.0, lo), (2.0, alt)):
            sc.note(CH_PNO, p, bar + rel, 0.9, vel + 4, jt=3, jv=3)
        for rel in (1.0, 3.0):
            for p in chord:
                sc.note(CH_PNO, p, bar + rel, 0.55, vel - 8, jt=3, jv=3)
        pool = tones[chord]
        cur = rng.choice((76, 79, 84))
        for e in range(8):                   # the honky right hand
            if rng.random() < 0.82:
                step = rng.choice((-5, -3, -2, 2, 3, 4))
                cand = [p for p in range(72, 89)
                        if p % 12 in {q % 12 for q in pool}
                        and abs(p - (cur + step)) <= 2]
                cur = cand[0] if cand else rng.choice(pool) + 12
                if rng.random() < 0.25:      # the honky crush
                    sc.note(CH_PNO, cur - 1, bar + 0.5 * e - 0.12, 0.11,
                            vel - 16, jt=1, jv=2)
                sc.note(CH_PNO, cur, bar + 0.5 * e, 0.4, vel - 2, jt=3, jv=4)
                if rng.random() < 0.4:
                    third = [p for p in range(cur - 5, cur - 2)
                             if p % 12 in {q % 12 for q in pool}]
                    if third:
                        sc.note(CH_PNO, third[0], bar + 0.5 * e, 0.4,
                                vel - 10, jt=3, jv=4)
        sc.note(CH_BASS, lo + 12, bar, 1.9, vel - 12, jt=3, jv=2)
        sc.note(CH_BASS, alt, bar + 2.0, 1.9, vel - 14, jt=3, jv=2)
        _rock_bar(sc, rng, bar, crash=False, kick_vel=52,
                  snare_vel=int(en.lerp(56, 72, b / 11)), hat_vel=42,
                  open_hat=False)
    _drum_fill(sc, rng, HONKY_T0 + 46.0, beats=2.0, vel=66)
    # bars 13-14: the collapse — a chromatic tumble onto a held G
    for k in range(24):
        sc.note(CH_PNO, 88 - k, 168.0 + 0.25 * k, 0.22,
                int(en.lerp(84, 58, k / 23)), jt=2, jv=3)
    for e in range(12):
        for p in (55, 59, 62):
            sc.note(CH_PNO, p, 168.0 + 0.5 * e, 0.45, 62, jt=3, jv=3)
    sc.note(CH_BASS, 43, 174.0, 2.0, 70, jt=0, jv=2)
    sc.note(CH_PNO, 43, 174.2, 1.7, 64, jt=0, jv=2)
    for k in range(12):
        sc.hit(38, 173.0 + 0.25 * k, int(en.lerp(46, 80, k / 11)),
               jt=2, jv=3)
    sc.hit(49, 174.0, 78, jt=0, jv=3)


# ---------------------------------------------------------------------------
# (b) Sun on the Estuary — one chord, breathing
# ---------------------------------------------------------------------------

# The birdsong: five separated flute call-clusters (abs beat, calls).
BIRD_CALLS: list[tuple[float, list[tuple[float, float, int]]]] = [
    (186.0, [(0.0, 0.15, 84), (0.2, 0.15, 86), (0.45, 0.3, 89)]),
    (202.0, [(0.0, 0.12, 86), (0.18, 0.12, 84), (0.4, 0.4, 81),
             (1.0, 0.15, 84), (1.25, 0.15, 86)]),
    (218.0, [(0.0, 0.2, 89), (0.3, 0.15, 86), (0.55, 0.15, 84),
             (0.85, 0.5, 86)]),
    (234.0, [(0.0, 0.12, 91), (0.18, 0.12, 89), (0.36, 0.12, 86),
             (0.6, 0.35, 89)]),
    (249.0, [(0.0, 0.15, 84), (0.28, 0.15, 81), (0.55, 0.6, 84),
             (1.4, 0.15, 86), (1.65, 0.3, 89)]),
]


def _b_sun(sc: en.Score) -> None:
    sc.hit(49, SUN_T0, 46, jt=0, jv=2)               # the sun blooms
    for k in range(11):                              # the held bass F
        sc.note(CH_BASS, 41, SUN_T0 + 8.0 * k, 7.9, 46, jt=2, jv=2)
    for t0, dur, chord in ((176.0, 21.9, (48, 53, 57, 60)),
                           (198.0, 21.9, (53, 57, 60, 65)),
                           (220.0, 21.9, (48, 57, 60, 65)),
                           (242.0, 21.5, (53, 60, 65, 69))):
        for p in chord:
            sc.note(CH_ORG, p, t0, dur, 46, jt=3, jv=2)
    en.cc_curve(sc, CH_ORG, 1, [(176.0, 8), (200.0, 92), (224.0, 18),
                                (248.0, 102), (262.0, 26)], step=1.0)
    en.expr_curve(sc, CH_ORG, [(176.0, 52), (194.0, 84), (210.0, 58),
                               (228.0, 88), (244.0, 62), (262.0, 52)],
                  step=1.0)
    # choir: low voices hold, the soprano arcs over the one chord
    for p, t0, dur in ((53, 176.0, 43.9), (53, 220.0, 43.5),
                       (60, 178.0, 41.9), (60, 220.5, 42.9),
                       (57, 180.0, 39.9), (57, 221.0, 41.9)):
        sc.note(CH_CHOIR, p, t0, dur, 50, jt=3, jv=2)
    for p, t0, dur in ((65, 180.0, 19.9), (69, 200.0, 23.9),
                       (72, 224.0, 15.9), (69, 240.0, 15.9),
                       (65, 256.0, 7.4)):
        sc.note(CH_CHOIR, p, t0, dur, 54, jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(176.0, 10), (192.0, 45), (208.0, 96),
                                  (224.0, 40), (240.0, 100), (262.0, 18)],
                   step=1.0)
    en.expr_curve(sc, CH_CHOIR, [(176.0, 58), (190.0, 86), (204.0, 62),
                                 (218.0, 90), (232.0, 64), (246.0, 92),
                                 (262.0, 58)], step=1.0)
    for p, t0, dur in ((41, 176.0, 43.9), (41, 220.0, 43.5),
                       (48, 177.0, 42.9), (48, 220.5, 42.9)):
        sc.note(CH_PAD, p, t0, dur, 42, jt=3, jv=2)
    en.expr_curve(sc, CH_PAD, [(176.0, 40), (220.0, 70), (262.0, 42)],
                  step=2.0)
    # transient light on the water: piano and harp, F pentatonic only
    for t0, ps in ((182.0, (65, 69, 72, 77, 81, 84)),
                   (206.0, (65, 69, 72, 77, 81, 84)),
                   (230.0, (69, 72, 77, 81, 84, 89)),
                   (250.0, (65, 72, 77, 84))):
        en.arp(sc, CH_PNO, list(ps), t0, len(ps), 0.5, 50, gate=1.6)
    for t0 in (190.0, 214.0, 238.0, 256.0):
        en.arp(sc, CH_HARP, [86, 84, 81, 79, 77, 74, 72, 69], t0, 8,
               0.5, 48, pattern="up", gate=1.5)
    # the birdsong
    for t0, calls in BIRD_CALLS:
        for rel, dur, p in calls:
            sc.note(CH_FLUTE, p, t0 + rel, dur, 62, jt=2, jv=3)
        en.expr_curve(sc, CH_FLUTE, [(t0 - 0.4, 52), (t0 + 0.6, 96),
                                     (t0 + 2.4, 56)], step=0.2)


# ---------------------------------------------------------------------------
# (c) Mr. Mudlark — the fuzz grotesque
# ---------------------------------------------------------------------------

MUD_BASE = 52                     # E3: the riff's floor on the lead
RIFF_MUD: list[tuple[float, float, int]] = [
    # (onset, dur, semitones above E3) — the b5 gives it the leer
    (0.0, 0.7, 0), (1.0, 0.7, 3), (2.0, 0.45, 5), (2.5, 0.45, 6),
    (3.0, 0.9, 5), (4.0, 0.45, 3), (4.5, 0.45, 5), (5.0, 0.9, 0),
    (6.5, 0.7, -2), (7.25, 0.6, 0),
]
MUD_STATEMENTS: tuple[float, ...] = (264.0, 272.0, 280.0, 288.0, 296.0,
                                     304.0, 344.0, 352.0, 360.0, 368.0,
                                     376.0, 384.0)
_MUD_STOMP_SPANS = ((264.0, 312.0), (344.0, 392.0))


def _mud_riff(sc: en.Score, t: float, vel: int, octave_up: bool) -> None:
    for on, dur, semi in RIFF_MUD:
        sc.note(CH_LEAD, MUD_BASE + semi, t + on, dur, vel, jt=2, jv=3)
        if octave_up:
            sc.note(CH_LEAD, MUD_BASE + semi + 12, t + on, dur, vel - 8,
                    jt=2, jv=3)


def _mud_stomp(sc: en.Score, rng: random.Random, bt: float, vel: int,
               tamb: bool) -> None:
    """One grotesque stomp bar: leaden kick, doubled backbeat."""
    for rel in (0.0, 2.5):
        sc.hit(36, bt + rel, vel + rng.randint(-3, 3), jt=2, jv=3)
        sc.hit(41, bt + rel, vel - 16 + rng.randint(-3, 3), jt=2, jv=3)
    for rel in (1.0, 3.0):
        sc.hit(38, bt + rel, vel + 6 + rng.randint(-3, 3), jt=2, jv=3)
        sc.hit(40, bt + rel, vel - 10 + rng.randint(-3, 3), jt=2, jv=3)
    for q in range(4):
        sc.hit(46, bt + q, vel - 34 + rng.randint(-3, 3), jt=2, jv=3)
    if tamb:
        for e in range(8):
            sc.hit(54, bt + 0.5 * e, 48 + (6 if e % 2 == 0 else 0),
                   jt=2, jv=4)


def _c_mudlark(sc: en.Score) -> None:
    rng = _rng(3)
    sc.hit(49, MUD_T0, 96, jt=0, jv=3)
    riff_roots = {0.0: 0, 1.0: 3, 2.0: 5, 2.5: 6, 3.0: 5, 4.0: 3,
                  4.5: 5, 5.0: 0, 6.5: -2, 7.25: 0}
    for t in MUD_STATEMENTS:
        big = t >= 344.0
        _mud_riff(sc, t, 96 if big else 90, octave_up=big or t >= 280.0)
        if t not in (264.0, 272.0):          # the band piles on
            for e in range(16):              # bass hammers the riff roots
                rel = 0.5 * e
                last = 0
                for k in sorted(riff_roots):
                    if k <= rel:
                        last = riff_roots[k]
                sc.note(CH_BASS, 40 + last, t + rel, 0.42,
                        84 + rng.randint(-4, 4), jt=2, jv=3)
            for e in range(16):              # rhythm chugs the low fifth
                sc.note(CH_RTM, 40, t + 0.5 * e, 0.4,
                        (86 if e % 2 == 0 else 76) + rng.randint(-3, 3),
                        jt=2, jv=3)
                sc.note(CH_RTM, 47, t + 0.5 * e, 0.4,
                        (80 if e % 2 == 0 else 70) + rng.randint(-3, 3),
                        jt=2, jv=3)
    for span_lo, span_hi in _MUD_STOMP_SPANS:
        b = span_lo
        while b < span_hi - 1e-6:
            _mud_stomp(sc, rng, b, 100, tamb=b >= 344.0)
            b += 4.0
    sc.hit(49, 280.0, 100, jt=0, jv=3)
    sc.hit(49, 344.0, 104, jt=0, jv=3)
    # -- the mud bridge [312, 344): half-time, wah, scooped moans ---------
    for bar in range(8):
        bt = 312.0 + 4.0 * bar
        sc.hit(36, bt, 88 + rng.randint(-3, 3), jt=2, jv=3)
        sc.hit(38, bt + 2.0, 92 + rng.randint(-3, 3), jt=2, jv=3)
        for q in range(4):
            sc.hit(46, bt + q, 52 + rng.randint(-3, 3), jt=2, jv=3)
        sc.note(CH_BASS, 40 if bar % 4 < 2 else 43, bt, 3.8, 78, jt=3, jv=2)
        for e in range(8):
            sc.note(CH_RTM, 40, bt + 0.5 * e, 0.35, 56 + rng.randint(-3, 3),
                    jt=2, jv=3)
    en.wah(sc, CH_LEAD, 312.0, 32.0, lo=32, hi=98, cycles_per_beat=0.25)
    for t, dur, p in ((312.0, 3.4, 64), (316.0, 3.4, 62), (320.0, 3.4, 60),
                      (324.0, 3.0, 58), (328.0, 3.4, 64), (332.0, 3.4, 67),
                      (336.0, 3.0, 64), (340.0, 3.2, 62)):
        _scoop(sc, CH_LEAD, t, dur, p, 88, depth=1.6, rise=0.4)
    sc.cc(CH_LEAD, 74, 78, 344.0)            # wah pedal parked open
    # -- outro [376, 396): two last leers, the unison cut, the count-in ---
    for p in (52, 64):                       # the cut rings as feedback
        sc.note(CH_LEAD, p, 392.0, 3.8, 110, jt=0, jv=2)
    for p in (40, 47):
        sc.note(CH_RTM, p, 392.0, 1.4, 104, jt=0, jv=2)
    sc.note(CH_BASS, 40, 392.0, 1.4, 106, jt=0, jv=2)
    sc.hit(49, 392.0, 108, jt=0, jv=2)
    sc.hit(36, 392.0, 104, jt=0, jv=2)
    for k in range(8):
        sc.hit(38, 394.0 + 0.25 * k, int(en.lerp(58, 92, k / 7)),
               jt=2, jv=3)


# ---------------------------------------------------------------------------
# (d) Polly on the Towpath — the slide-guitar rocker
# ---------------------------------------------------------------------------

_POL_VERSE = (45, 45, 50, 45, 52, 50, 45, 52)      # A A D A E D A E
_POL_CHORUS = (50, 50, 45, 45, 52, 50, 45, 52)     # D D A A E D A E
_POL_TRIADS = {45: (61, 64, 69), 50: (62, 66, 69), 52: (64, 68, 71)}

# The slide riff (16 beats): 1 in the last slot marks a scooped entry.
RIFF_POL: list[tuple[float, float, int, int]] = [
    (0.0, 1.2, 64, 1), (1.5, 0.4, 62, 0), (2.0, 0.4, 61, 0),
    (2.5, 1.2, 57, 1), (4.0, 1.2, 64, 1), (5.5, 0.4, 66, 0),
    (6.0, 0.4, 67, 0), (6.5, 1.4, 69, 1), (8.0, 1.2, 64, 1),
    (9.5, 0.4, 62, 0), (10.0, 0.4, 61, 0), (10.5, 1.2, 57, 1),
    (12.0, 0.8, 60, 1), (13.0, 0.8, 61, 0), (14.0, 1.6, 57, 1),
]


def _pol_riff(sc: en.Score, t: float, vel: int) -> None:
    for on, dur, p, sl in RIFF_POL:
        if sl:
            _scoop(sc, CH_LEAD, t + on, dur, p, vel, depth=1.4, rise=0.3)
        else:
            sc.note(CH_LEAD, p, t + on, dur, vel - 6, jt=2, jv=3)
    _fall(sc, CH_LEAD, t + 15.6, depth=1.2)


def _pol_backing(sc: en.Score, rng: random.Random, t0: float,
                 roots, vel: int, fill_end: bool) -> None:
    """One 8-bar block: boogie bass, palm chugs, offbeat piano, drums."""
    for i, r in enumerate(roots):
        bar = t0 + 4.0 * i
        for e, off in enumerate((0, 0, 4, 4, 7, 7, 9, 7)):
            sc.note(CH_BASS, r + off, bar + 0.5 * e, 0.44,
                    vel + (4 if e % 2 == 0 else -4) + rng.randint(-3, 3),
                    jt=2, jv=3)
        for e in range(8):
            for p in (r + 12, r + 19):
                sc.note(CH_RTM, p, bar + 0.5 * e, 0.32,
                        vel - 22 + (6 if e % 2 == 0 else 0)
                        + rng.randint(-3, 3), jt=2, jv=3)
        for rel in (1.5, 3.5):
            for p in _POL_TRIADS[r]:
                sc.note(CH_PNO, p, bar + rel, 0.4, vel - 18
                        + rng.randint(-3, 3), jt=3, jv=3)
        _rock_bar(sc, rng, bar, crash=(i == 0), kick_vel=vel - 4,
                  snare_vel=vel + 2, hat_vel=vel - 34)
    if fill_end:
        _drum_fill(sc, rng, t0 + 4.0 * len(roots) - 2.0, beats=2.0,
                   vel=vel + 2)


def _d_polly(sc: en.Score) -> None:
    rng = _rng(4)
    # intro [396, 412): the riff over the boogie
    _pol_backing(sc, rng, POL_T0, _POL_VERSE[:4], 88, fill_end=False)
    _pol_riff(sc, POL_T0, 92)
    # verse 1 [412, 444)
    _pol_backing(sc, rng, 412.0, _POL_VERSE, 86, fill_end=True)
    lick_pool = (57, 60, 61, 62, 64, 66, 67, 69, 72)
    for phrase_t in (424.0, 440.0, 488.0, 504.0):
        cur = rng.choice((64, 66, 67))
        for k in range(5):
            step = rng.choice((-2, -1, 1, 2))
            idx = max(0, min(len(lick_pool) - 1,
                             lick_pool.index(cur) + step))
            cur = lick_pool[idx]
            sc.note(CH_LEAD, cur, phrase_t + 0.5 * k, 0.42,
                    84 + rng.randint(-4, 4), jt=2, jv=3)
        _scoop(sc, CH_LEAD, phrase_t + 2.5, 1.2, cur, 88, depth=1.2)
    # chorus 1 [444, 476): the riff again, fiddle harmony above
    _pol_backing(sc, rng, 444.0, _POL_CHORUS, 90, fill_end=True)
    _pol_riff(sc, 444.0, 96)
    _pol_riff(sc, 460.0, 98)
    for t, p in ((444.0, 69), (452.0, 74), (460.0, 69), (468.0, 76)):
        sc.note(CH_FID, p, t, 6.4, 62, jt=3, jv=2)
        en.vibrato(sc, CH_FID, t + 0.8, 5.0, depth=0.18,
                   cycles_per_beat=1.1, delay=0.3)
    # verse 2 [476, 508)
    _pol_backing(sc, rng, 476.0, _POL_VERSE, 87, fill_end=True)
    # the slide solo [508, 540)
    _pol_backing(sc, rng, 508.0, _POL_CHORUS, 90, fill_end=True)
    for ph in range(4):
        t = 508.0 + 8.0 * ph
        top = rng.choice((69, 72, 76))
        _scoop(sc, CH_LEAD, t, 2.4, top, 96, depth=1.8, rise=0.45)
        run_len = 6
        cur = top
        for k in range(run_len):
            idx = max(0, lick_pool.index(min(lick_pool,
                                             key=lambda q: abs(q - cur)))
                      - rng.choice((1, 1, 2)))
            cur = lick_pool[idx]
            sc.note(CH_LEAD, cur, t + 3.0 + 0.5 * k, 0.42,
                    88 + rng.randint(-4, 4), jt=2, jv=3)
        _scoop(sc, CH_LEAD, t + 6.0, 1.6, cur + 12 if cur + 12 <= 84
               else cur, 94, depth=1.4)
        _fall(sc, CH_LEAD, t + 7.6, depth=1.3)
    # chorus 2 [540, 572)
    _pol_backing(sc, rng, 540.0, _POL_CHORUS, 92, fill_end=False)
    _pol_riff(sc, 540.0, 100)
    _pol_riff(sc, 556.0, 102)
    for t, p in ((540.0, 76), (548.0, 74), (556.0, 76), (564.0, 81)):
        sc.note(CH_FID, p, t, 6.4, 66, jt=3, jv=2)
        en.vibrato(sc, CH_FID, t + 0.8, 5.0, depth=0.2,
                   cycles_per_beat=1.15, delay=0.3)
    # turnaround [572, 580): stop-time hits, then the tumble into soul
    for hit_t in (572.0, 573.5, 575.0):
        for p in (45, 57):
            sc.note(CH_BASS if p == 45 else CH_LEAD, p, hit_t, 0.7, 104,
                    jt=0, jv=2)
        for p in (57, 64):
            sc.note(CH_RTM, p, hit_t, 0.7, 96, jt=0, jv=2)
        for p in _POL_TRIADS[45]:
            sc.note(CH_PNO, p, hit_t, 0.7, 92, jt=0, jv=2)
        sc.hit(49, hit_t, 96, jt=0, jv=2)
        sc.hit(36, hit_t, 98, jt=0, jv=2)
    for i, p in enumerate((45, 47, 49, 52)):
        sc.note(CH_BASS, p, 576.0 + i, 0.95, 96, jt=2, jv=2)
    _drum_fill(sc, rng, 576.0, beats=4.0, vel=84)


# ---------------------------------------------------------------------------
# (e) Out of My Window — the syncopated soul hook
# ---------------------------------------------------------------------------

# The hook (2 bars).  7 of its 9 onsets are off the beat — that lean IS
# the song, and the syncopation oracle measures this table.
HOOK_WIN: list[tuple[float, float, int]] = [
    (0.0, 0.5, 60), (0.75, 0.5, 63), (1.75, 0.6, 65), (2.5, 0.5, 63),
    (3.25, 1.0, 67), (4.75, 0.5, 70), (5.5, 0.5, 67), (6.25, 0.6, 65),
    (7.0, 0.9, 63),
]
_WIN_CYCLE = (36, 36, 44, 46)               # Cm Cm Ab Bb bar roots
_WIN_EP_CHORDS = {36: (58, 63, 67), 44: (56, 60, 63), 46: (58, 62, 65)}
_WIN_BASS_CELL = ((0.0, 0.7, 0), (0.75, 0.25, 0), (1.0, 0.5, 7),
                  (1.75, 0.4, 10), (2.5, 0.5, 12), (3.25, 0.35, 10),
                  (3.75, 0.22, 7))


def _hook(sc: en.Score, t: float, vel: int, ep_only: bool = False) -> None:
    for on, dur, p in HOOK_WIN:
        if not ep_only:
            sc.note(CH_BRASS, p, t + on, dur, vel, jt=2, jv=3)
        sc.note(CH_EP, p + 12, t + on, dur, vel - 6, jt=2, jv=3)


def _soul_bar(sc: en.Score, rng: random.Random, bt: float, vel: int,
              claps: bool = False, open_end: bool = False) -> None:
    for rel in (0.0, 1.75, 2.5):
        if rel == 2.5 and rng.random() < 0.35:
            continue
        sc.hit(36, bt + rel, vel + rng.randint(-3, 3), jt=2, jv=3)
    for rel in (1.0, 3.0):
        sc.hit(38, bt + rel, vel + 6 + rng.randint(-3, 3), jt=2, jv=3)
        if claps:
            sc.hit(39, bt + rel, vel + rng.randint(-3, 5), jt=3, jv=4)
    for s in range(16):
        if s == 15 and open_end:
            sc.hit(46, bt + 0.25 * s, vel - 18, jt=2, jv=3)
        else:
            sc.hit(42, bt + 0.25 * s,
                   vel - 32 + (8 if s % 4 == 0 else 0) + rng.randint(-2, 2),
                   jt=2, jv=3)
    if rng.random() < 0.4:
        sc.hit(40, bt + rng.choice((2.25, 3.75)), vel - 24, jt=2, jv=3)


def _win_groove(sc: en.Score, rng: random.Random, t0: float, bars: int,
                vel: int, ep: bool = True, chucks: bool = False,
                claps: bool = False) -> None:
    for b in range(bars):
        bar = t0 + 4.0 * b
        root = _WIN_CYCLE[b % 4]
        _soul_bar(sc, rng, bar, vel, claps=claps,
                  open_end=(b % 4 == 3))
        for on, dur, off in _WIN_BASS_CELL:
            sc.note(CH_BASS, root + off, bar + on, dur,
                    vel - 6 + rng.randint(-3, 3), jt=2, jv=3)
        if ep:
            chord = _WIN_EP_CHORDS[root]
            for on, dur in ((0.0, 1.4), (1.75, 0.8), (2.5, 1.1)):
                if rng.random() < 0.85:
                    for p in chord:
                        sc.note(CH_EP, p, bar + on, dur,
                                vel - 22 + rng.randint(-3, 3), jt=3, jv=3)
        if chucks:
            for rel in (0.5, 1.5, 2.5, 3.5):
                for p in (67, 72):
                    sc.note(CH_RTM, p, bar + rel, 0.14,
                            vel - 26 + rng.randint(-3, 3), jt=2, jv=3)


def _e_window(sc: en.Score) -> None:
    rng = _rng(5)
    sc.hit(49, WIN_T0, 92, jt=0, jv=3)
    # intro [580, 588)
    _win_groove(sc, rng, WIN_T0, 2, 88, ep=True)
    # hooks and verses (HOOK_TIMES pins the six full statements)
    _hook(sc, 588.0, 92)
    _hook(sc, 596.0, 94)
    _win_groove(sc, rng, 588.0, 4, 88, ep=False, chucks=True)
    _win_groove(sc, rng, 604.0, 8, 86, ep=True)             # verse 1
    ep_pool = (72, 75, 77, 79, 82, 84, 87)
    for ph in range(4):
        t = 606.0 + 8.0 * ph
        cur = rng.choice((79, 82))
        for k in range(rng.randint(3, 5)):
            idx = max(0, min(len(ep_pool) - 1,
                             ep_pool.index(cur) + rng.choice((-2, -1, 1))))
            cur = ep_pool[idx]
            sc.note(CH_EP, cur, t + 0.75 * k + 0.25, 0.5,
                    72 + rng.randint(-4, 4), jt=3, jv=3)
    _hook(sc, 636.0, 96)
    _hook(sc, 644.0, 96)
    _win_groove(sc, rng, 636.0, 4, 90, ep=False, chucks=True)
    _win_groove(sc, rng, 652.0, 8, 88, ep=True, chucks=True)  # verse 2
    for t0, dur, chord in ((652.0, 15.9, (55, 60, 63)),
                           (668.0, 15.9, (55, 58, 63))):
        for p in chord:
            sc.note(CH_ORG, p, t0, dur, 44, jt=3, jv=2)
    en.expr_curve(sc, CH_ORG, [(652.0, 40), (668.0, 66), (683.5, 44)],
                  step=1.0)
    # breakdown [684, 700): drums, bass, claps, ghost EP
    _win_groove(sc, rng, 684.0, 4, 84, ep=False, claps=True)
    for k in range(6):
        t = 684.5 + 2.5 * k
        sc.note(CH_EP, rng.choice((70, 72, 75)), t, 0.5, 58, jt=3, jv=3)
    _hook(sc, 700.0, 100)
    _hook(sc, 708.0, 102)
    _win_groove(sc, rng, 700.0, 4, 92, ep=False, chucks=True)
    # climax verse [716, 732)
    _win_groove(sc, rng, 716.0, 4, 94, ep=True, chucks=True, claps=True)
    for t0, p in ((716.0, 68), (720.0, 68), (724.0, 67), (728.0, 65)):
        sc.note(CH_BRASS, p, t0, 3.4, 84, jt=3, jv=3)
        sc.note(CH_BRASS, p - 8 if p - 8 >= 56 else p - 5, t0, 3.4, 76,
                jt=3, jv=3)
    # winddown [732, 748): the hook once, alone at the window
    _hook(sc, 732.0, 60, ep_only=True)
    _win_groove(sc, rng, 732.0, 2, 62, ep=False)
    for p in (58, 63, 67, 74):
        sc.note(CH_EP, p, 740.0, 7.4, 46, jt=3, jv=2)
    sc.note(CH_BASS, 36, 740.0, 7.6, 48, jt=2, jv=2)
    for q in range(10):
        sc.hit(42, 738.0 + q, 34 + rng.randint(-2, 2), jt=2, jv=3)


# ---------------------------------------------------------------------------
# (f) Slumber Line — the lullaby that starts to lean forward
# ---------------------------------------------------------------------------

# 3/4 harmony, one chord per bar: two 8-bar cycles, then the six-bar swell.
_SLU_CYCLE = ("F", "Dm", "Bb", "C", "F", "Dm", "Gm", "C")
_SLU_CODA = ("F", "Bb", "Gm", "C", "C7", "C7")
_SLU_CHORDS = {
    "F": (53, 60, 65, 69), "Dm": (50, 57, 62, 65), "Bb": (46, 58, 62, 65),
    "C": (48, 55, 64, 67), "Gm": (43, 55, 58, 62), "C7": (48, 58, 64, 67),
}
_SLU_ROOTS = {"F": 41, "Dm": 38, "Bb": 46, "C": 48, "Gm": 43, "C7": 48}

# The lullaby tune: one 8-bar (24-beat) phrase, F ionian degrees.
LULL: list[tuple[int, float, float]] = [
    (3, 0, 2), (2, 2, 1), (4, 3, 2), (3, 5, 1), (4, 6, 2), (5, 8, 1),
    (2, 9, 3), (5, 12, 2), (6, 14, 1), (6, 15, 2), (5, 17, 1),
    (4, 18, 1.5), (3, 19.5, 1.5), (2, 21, 3),
]
# The swell line over the coda (18 beats), reaching for the anthem.
CODA_FL: list[tuple[int, float, float]] = [
    (5, 0, 2), (6, 2, 1), (8, 3, 2), (7, 5, 1), (6, 6, 1.5),
    (5, 7.5, 1.5), (4, 9, 2), (5, 11, 1), (6, 12, 2), (7, 14, 1),
    (8, 15, 3),
]


def _slu_harp_bar(sc: en.Score, bt: float, chord, vel: int) -> None:
    for e, idx in enumerate((0, 1, 2, 3, 2, 1)):
        sc.note(CH_HARP, chord[idx], bt + 0.5 * e, 0.8,
                vel + (4 if e == 0 else 0), jt=3, jv=3)


def _f_slumber(sc: en.Score) -> None:
    rng = _rng(6)
    names = list(_SLU_CYCLE) * 2 + list(_SLU_CODA)
    for b, name in enumerate(names):
        bt = SLU_T0 + 3.0 * b
        vel = int(en.lerp(48, 54, b / 15)) if b < 16 else \
            int(en.lerp(56, 74, (b - 16) / 5))
        _slu_harp_bar(sc, bt, _SLU_CHORDS[name], vel)
        sc.note(CH_CELLO, _SLU_ROOTS[name], bt, 2.9,
                max(40, vel - 8), jt=3, jv=2)
    en.line(sc, CH_FLUTE, SLU_T0, 65, "ionian", LULL, vel=52, gate=0.96)
    en.line(sc, CH_FLUTE, SLU_T0 + 24.0, 65, "ionian", LULL, vel=58,
            gate=0.96)
    en.line(sc, CH_FLUTE, 796.0, 65, "ionian", CODA_FL, vel=64,
            vel_end=78, gate=0.97)
    # the hum: choir on a low F-C dyad, mm, opening to ah in the swell
    for t0, dur, vel in ((748.0, 11.9, 40), (760.0, 11.9, 41),
                         (772.0, 11.9, 42), (784.0, 11.9, 44)):
        for p in (53, 60):
            sc.note(CH_CHOIR, p, t0, dur, vel, jt=3, jv=2)
    for p, vel in ((53, 56), (57, 54), (60, 58), (65, 60)):
        sc.note(CH_CHOIR, p, 796.0, 8.9, vel, jt=3, jv=2)
    for p, vel in ((55, 62), (58, 60), (60, 64), (65, 66)):
        sc.note(CH_CHOIR, p, 805.0, 8.8, vel, jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(748.0, 8), (790.0, 12), (802.0, 55),
                                  (813.0, 92)], step=1.0)
    en.expr_curve(sc, CH_CHOIR, [(748.0, 60), (790.0, 66), (813.5, 96)],
                  step=1.5)
    # strings shade in for the second cycle, then carry the swell
    chords2 = [list(_SLU_CHORDS[n][1:]) for n in list(_SLU_CYCLE)]
    en.pad_block(sc, CH_STR, 772.0, chords2, span=3.0, size=3, lo=55,
                 hi=79, vel=40, vel_end=48)
    chords3 = [list(_SLU_CHORDS[n][1:]) for n in list(_SLU_CODA)]
    en.pad_block(sc, CH_STR, 796.0, chords3, span=3.0, size=3, lo=55,
                 hi=79, vel=52, vel_end=70)
    en.expr_curve(sc, CH_STR, [(772.0, 58), (796.0, 70), (813.5, 98)],
                  step=1.5)
    for k in range(16):                       # the roll that wakes the tide
        sc.hit(38, 810.0 + 0.25 * k, int(en.lerp(30, 72, k / 15)),
               jt=2, jv=3)
    del rng


# ---------------------------------------------------------------------------
# (g) Carry the Current — the anthem on the FABLE ground
# ---------------------------------------------------------------------------

# The anthem tune (16 beats = 4 ground loops), F ionian degrees.
ANTH: list[tuple[int, float, float]] = [
    (3, 0, 3), (4, 3, 1), (5, 4, 3), (6, 7, 1), (8, 8, 2), (7, 10, 1),
    (6, 11, 1), (5, 12, 2), (4, 14, 1), (5, 15, 1),
]
STATE_TIMES: tuple[float, ...] = tuple(846.0 + 16.0 * k for k in range(8))

_F_PCS = [53, 57, 60]             # F major
_C_PCS = [48, 52, 55]             # C major (C/E over the cell's E)


def _g_current(sc: en.Score) -> None:
    rng = _rng(7)
    sc.hit(49, CUR_T0, 72, jt=0, jv=3)
    # THE ground: the FABLE cell, 42 unbroken loops, F2, rising all the way
    for k in range(GROUND_LOOPS):
        material.play_cell(sc, CH_BASS, CUR_T0 + 4.0 * k, GROUND_ROOT,
                           vel=int(en.lerp(54, 96, k / 41)), gate=0.96,
                           jt=3, jv=3)
    en.pad_block(sc, CH_ORG, CUR_T0, [_F_PCS, _C_PCS] * 42, span=2.0,
                 size=3, lo=48, hi=72, vel=44, vel_end=62)
    en.pad_block(sc, CH_CHOIR, 830.0, [_F_PCS, _C_PCS] * 38, span=2.0,
                 size=3, lo=55, hi=76, vel=42, vel_end=68)
    en.vowel_curve(sc, CH_CHOIR, [(830.0, 38), (910.0, 50), (942.0, 96),
                                  (981.0, 90)], step=2.0)
    en.expr_curve(sc, CH_CHOIR, [(830.0, 62), (910.0, 74), (958.0, 92),
                                 (988.0, 98)], step=2.0)
    en.expr_curve(sc, CH_STR, [(846.0, 60), (910.0, 76), (958.0, 94),
                               (988.0, 100)], step=2.0)
    en.cc_curve(sc, CH_ORG, 1, [(942.0, 20), (950.0, 95), (970.0, 95),
                                (980.0, 30)], step=1.0)
    # the anthem, orchestrated wider with every statement
    for i, t in enumerate(STATE_TIMES):
        vel = int(en.lerp(58, 88, i / 7))
        en.line(sc, CH_STR, t, 65, "ionian", ANTH, vel=vel, gate=0.97)
        if i >= 1:
            en.line(sc, CH_FLUTE, t, 65, "ionian", ANTH, vel=vel - 8,
                    octave=1, gate=0.96)
        if i >= 2:
            en.line(sc, CH_BRASS, t, 65, "ionian", ANTH, vel=vel - 6,
                    gate=0.96)
        if i >= 4:
            en.line(sc, CH_FID, t, 65, "ionian", ANTH, vel=vel - 10,
                    gate=0.96)
    sc.note(CH_STR, 77, 974.0, 7.8, 84, jt=2, jv=2)      # the crest held
    sc.note(CH_STR, 72, 974.0, 7.8, 78, jt=2, jv=2)
    # sparkle and chug
    for k in range(12, GROUND_LOOPS):
        t = CUR_T0 + 4.0 * k
        vel = int(en.lerp(50, 68, (k - 12) / 29))
        en.arp(sc, CH_PNO, [53, 57, 60, 65], t, 8, 0.25, vel, gate=1.3)
        en.arp(sc, CH_PNO, [52, 55, 60, 64], t + 2.0, 8, 0.25, vel,
               gate=1.3)
    for k in range(16, GROUND_LOOPS):
        t = CUR_T0 + 4.0 * k
        vel = int(en.lerp(58, 76, (k - 16) / 25))
        for e in range(8):
            dyad = (53, 60) if e < 4 else (52, 59)
            for p in dyad:
                sc.note(CH_RTM, p, t + 0.5 * e, 0.4,
                        vel + (4 if e % 2 == 0 else -4)
                        + rng.randint(-3, 3), jt=2, jv=3)
    # drums: half-time tide from loop 16, full stride from loop 24
    for bar in range(8):
        bt = 878.0 + 4.0 * bar
        sc.hit(36, bt, 78 + rng.randint(-3, 3), jt=2, jv=3)
        sc.hit(38, bt + 2.0, 84 + rng.randint(-3, 3), jt=2, jv=3)
        for q in range(4):
            sc.hit(42, bt + q, 46 + rng.randint(-2, 2), jt=2, jv=3)
    for bar in range(18):
        bt = 910.0 + 4.0 * bar
        _rock_bar(sc, rng, bt, crash=False,
                  kick_vel=int(en.lerp(84, 96, bar / 17)),
                  snare_vel=int(en.lerp(88, 100, bar / 17)), hat_vel=54)
    for t in (878.0, 910.0, 926.0, 942.0, 958.0, 974.0):
        sc.hit(49, t, 88, jt=0, jv=3)
    for t in (908.0, 924.0, 940.0, 956.0, 972.0):
        _drum_fill(sc, rng, t, beats=2.0, vel=82)
    # the cadence [982, 990): the ground finally walks away — Bb, C, launch
    sc.hit(49, 982.0, 96, jt=0, jv=3)
    sc.note(CH_BASS, 46, 982.0, 1.9, 92, jt=2, jv=2)
    sc.note(CH_BASS, 48, 984.0, 1.9, 94, jt=2, jv=2)
    sc.note(CH_BASS, 48, 986.0, 0.95, 96, jt=2, jv=2)
    sc.note(CH_BASS, 45, 987.0, 0.95, 96, jt=2, jv=2)
    for e in range(4):
        sc.note(CH_BASS, 48, 988.0 + 0.5 * e, 0.45, 98, jt=2, jv=2)
    for ch, chords in ((CH_STR, ((58, 62, 65), (55, 60, 64))),
                       (CH_CHOIR, ((58, 62, 65), (55, 60, 64))),
                       (CH_ORG, ((46, 58, 62), (48, 55, 64))),
                       (CH_BRASS, ((58, 62, 65), (55, 60, 64)))):
        for p in chords[0]:
            sc.note(ch, p, 982.0, 1.9, 84, jt=2, jv=2)
        for p in chords[1]:
            sc.note(ch, p, 984.0, 5.7, 88, jt=2, jv=2)
    for bar in range(2):
        _rock_bar(sc, rng, 982.0 + 4.0 * bar, crash=False, kick_vel=96,
                  snare_vel=100, hat_vel=58)
    _drum_fill(sc, rng, 986.0, beats=4.0, vel=92)


# ---------------------------------------------------------------------------
# (h) The End of the Line — break, trading twos, the mirror chorale
# ---------------------------------------------------------------------------

_TRADE_CHORDS = ((38, (62, 65, 69)), (46, (62, 65, 70)),
                 (41, (60, 65, 69)), (48, (60, 64, 67)))
_TRADE_DYADS = ((50, 57), (46, 53), (41, 48), (48, 55))


def _trade_backing(sc: en.Score, rng: random.Random, t: float,
                   vel: int) -> None:
    """Two bars of engine room under a trading cell: Dm Bb F C."""
    sc.hit(49, t, vel + 6, jt=0, jv=3)
    for half in range(2):
        _rock_bar(sc, rng, t + 4.0 * half, crash=False, kick_vel=vel - 2,
                  snare_vel=vel + 4, hat_vel=vel - 34)
    for j, (root, chord) in enumerate(_TRADE_CHORDS):
        seg = t + 2.0 * j
        for e in range(4):
            sc.note(CH_BASS, root, seg + 0.5 * e, 0.44,
                    vel - 4 + (4 if e % 2 == 0 else 0) + rng.randint(-3, 3),
                    jt=2, jv=3)
        for e in range(4):
            for p in _TRADE_DYADS[j]:
                sc.note(CH_RTM, p, seg + 0.5 * e, 0.36,
                        vel - 26 + rng.randint(-3, 3), jt=2, jv=3)
        for p in chord:
            sc.note(CH_PNO, p, seg + 0.5, 0.7, vel - 18 + rng.randint(-3, 3),
                    jt=3, jv=3)
        if rng.random() < 0.7:
            for p in chord:
                sc.note(CH_PNO, p, seg + 1.5, 0.4,
                        vel - 24 + rng.randint(-3, 3), jt=3, jv=3)


_GTR_POOL = (62, 65, 67, 69, 70, 72, 74, 77, 79, 81)


def _solo_guitar(sc: en.Score, rng: random.Random, t: float,
                 heat: int) -> None:
    cur = rng.choice((74, 77))
    _scoop(sc, CH_LEAD, t, 1.2, cur, 96 + 2 * heat, depth=1.6, rise=0.35)
    beat = t + 1.5
    while beat < t + 6.3:
        idx = _GTR_POOL.index(cur) + rng.choice((-2, -1, -1, 1, 1, 2))
        idx = max(0, min(len(_GTR_POOL) - 1, idx))
        cur = _GTR_POOL[idx]
        dur = rng.choice((0.25, 0.5, 0.5))
        sc.note(CH_LEAD, cur, beat, dur * 0.9,
                90 + 2 * heat + rng.randint(-5, 5), jt=2, jv=3)
        beat += dur
    sc.note(CH_LEAD, cur, t + 6.5, 1.2, 98 + 2 * heat, jt=0, jv=2)
    en.bend_ramp(sc, CH_LEAD, t + 6.5, t + 7.0, 0.0, 1.0, steps=5)
    en.bend_ramp(sc, CH_LEAD, t + 7.2, t + 7.6, 1.0, 0.0, steps=5)


def _solo_organ(sc: en.Score, rng: random.Random, t: float,
                heat: int) -> None:
    sc.cc(CH_ORG, 1, 96, t - 0.1)                    # rotor to fast
    en.run(sc, CH_ORG, t, 62, "dorian", list(range(1, 9)), 0.25,
           74 + 3 * heat, 88 + 3 * heat)
    en.run(sc, CH_ORG, t + 2.0, 62, "dorian", [8, 7, 8, 9, 8, 7, 6, 5],
           0.25, 84 + 3 * heat, 78 + 3 * heat)
    en.run(sc, CH_ORG, t + 4.0, 62, "dorian",
           [4, 5, 6, 7, 8, 9, 10, 11], 0.25, 80 + 3 * heat, 92 + 3 * heat)
    for p in (62, 65, 69, 74):
        sc.note(CH_ORG, p, t + 6.0, 1.7, 88 + 3 * heat, jt=2, jv=3)
    sc.cc(CH_ORG, 1, 30, t + 7.9)
    del rng


_FID_TUNE = [(74, 0.0, 0.5), (77, 0.5, 0.5), (79, 1.0, 1.0),
             (77, 2.0, 0.5), (74, 2.5, 0.5), (72, 3.0, 1.0),
             (74, 4.0, 0.5), (77, 4.5, 0.5), (79, 5.0, 0.5),
             (81, 5.5, 0.5)]


def _solo_fiddle(sc: en.Score, rng: random.Random, t: float,
                 heat: int) -> None:
    lift = 12 if heat >= 2 else 0
    for p, on, dur in _FID_TUNE:
        sc.note(CH_FID, p + (lift if p + lift <= 93 else 0), t + on,
                dur * 0.94, 78 + 4 * heat + rng.randint(-4, 4), jt=2, jv=3)
        if on in (0.0, 4.0):                          # the open-string drone
            sc.note(CH_FID, 69, t + on, 0.9, 64 + 4 * heat, jt=2, jv=3)
    close = rng.choice((74, 77))
    sc.note(CH_FID, close, t + 6.0, 1.6, 84 + 4 * heat, jt=0, jv=2)
    en.vibrato(sc, CH_FID, t + 6.3, 1.2, depth=0.22, cycles_per_beat=1.3,
               delay=0.2)


def _h_endline(sc: en.Score) -> None:
    rng = _rng(8)
    # -- the arrival [990, 998): three stabs and the tumble ---------------
    for t, dur, bass_p, gtr, pno in (
            (990.0, 1.1, 38, (50, 62), (62, 65, 69, 74)),
            (991.5, 1.1, 46, (46, 58), (62, 65, 70, 74)),
            (993.0, 0.9, 48, (48, 60), (60, 64, 67, 72))):
        sc.note(CH_BASS, bass_p, t, dur, 100, jt=0, jv=2)
        for p in gtr:
            sc.note(CH_LEAD, p, t, dur, 102, jt=0, jv=2)
        for p in pno:
            sc.note(CH_PNO, p, t, dur, 96, jt=0, jv=2)
        sc.hit(49, t, 98, jt=0, jv=3)
        sc.hit(36, t, 100, jt=0, jv=3)
    fall = (74, 72, 70, 69, 67, 65, 62, 60, 58, 57, 55, 53, 50, 50)
    for i, p in enumerate(fall):
        beat = 994.0 + 0.25 * i
        v = int(en.lerp(88, 106, i / 13))
        sc.note(CH_LEAD, p, beat, 0.2, v, jt=1, jv=2)
        sc.note(CH_PNO, p + 12, beat, 0.2, v - 8, jt=1, jv=2)
        if i % 2 == 0:
            sc.note(CH_BASS, 38 if i % 4 == 0 else 50, beat, 0.42, v - 4,
                    jt=1, jv=2)
        sc.hit(38, beat, 60 + 3 * i, jt=1, jv=3)
        if i % 4 == 0:
            sc.hit(36, beat, 96, jt=1, jv=3)
    # -- the album's only drum break [998, 1010): three bars, kit alone ---
    sc.hit(49, BREAK_T0, 108, jt=0, jv=2)
    for rel, drum, v in ((0.0, 36, 106), (0.75, 38, 68), (1.0, 38, 98),
                         (2.0, 36, 102), (2.5, 38, 72), (3.0, 38, 100),
                         (3.75, 40, 64)):
        sc.hit(drum, 998.0 + rel, v, jt=1, jv=3)
    toms = (50, 50, 48, 48, 47, 45, 45, 43)
    for e, drum in enumerate(toms):
        sc.hit(drum, 1002.0 + 0.5 * e, 84 + 2 * e, jt=1, jv=3)
        if e % 2 == 1:
            sc.hit(36, 1002.0 + 0.5 * e, 92, jt=1, jv=3)
    for s in range(16):
        drum = (38, 45, 43, 41)[s % 4] if s < 12 else 38
        sc.hit(drum, 1006.0 + 0.25 * s, int(en.lerp(78, 112, s / 15)),
               jt=1, jv=3)
        if s % 4 == 0:
            sc.hit(36, 1006.0 + 0.25 * s, 100, jt=1, jv=3)
    # -- trading twos [1010, 1082): guitar / organ / fiddle, three rounds -
    for k in range(TRADE_ROUNDS * len(SOLO_ORDER)):
        t = TRADE_T0 + TRADE_CELL * k
        heat = k // 3
        _trade_backing(sc, rng, t, 88 + 3 * heat)
        owner = SOLO_ORDER[k % 3]
        if owner == CH_LEAD:
            _solo_guitar(sc, rng, t, heat)
        elif owner == CH_ORG:
            _solo_organ(sc, rng, t, heat)
        else:
            _solo_fiddle(sc, rng, t, heat)
    # -- the chorale [1082, 1098): the cell against its own mirror --------
    for st, vel in ((CHORALE_T0, 68), (CHORALE_T0 + 8.0, 84)):
        material.play_cell(sc, CH_STR, st, CHORALE_ROOT,
                           stretch=CHORALE_STRETCH, vel=vel, gate=0.98,
                           jt=2, jv=2)
        for on, dur, semi in material.FABLE_CELL:
            sc.note(CH_CELLO, CHORALE_ROOT - semi,
                    st + on * CHORALE_STRETCH,
                    dur * CHORALE_STRETCH * 0.98, vel - 4, jt=2, jv=2)
    for on, dur, semi in material.FABLE_CELL:       # brass joins the mirror
        sc.note(CH_BRASS, CHORALE_ROOT + semi,
                CHORALE_T0 + 8.0 + on * CHORALE_STRETCH,
                dur * CHORALE_STRETCH * 0.96, 74, jt=2, jv=2)
    sc.note(CH_ORG, 53, CHORALE_T0, 12.8, 46, jt=2, jv=2)   # F under the L
    for i, bt in enumerate((1082.0, 1086.0, 1090.0)):
        sc.note(CH_BASS, 41, bt, 3.9, 60 + 8 * i, jt=2, jv=2)
    # -- the resolution [1098, ~1127): E up to F, Gb down to F — F MAJOR --
    hold = LAST_H_OFF - RESOLVE_T0
    sc.hit(49, RESOLVE_T0, 92, jt=0, jv=2)
    sc.note(CH_BASS, 41, RESOLVE_T0, hold, 82, jt=0, jv=2)
    sc.note(CH_CELLO, 53, RESOLVE_T0, hold, 78, jt=0, jv=2)
    for p in (48, 53, 60):
        sc.note(CH_ORG, p, RESOLVE_T0, hold, 66, jt=0, jv=2)
    for p in (60, 65, 69, 72):
        sc.note(CH_CHOIR, p, RESOLVE_T0, hold, 74, jt=0, jv=2)
    for p in (65, 69, 72, 77):
        sc.note(CH_STR, p, RESOLVE_T0, hold, 80, jt=0, jv=2)
    for p in (65, 69):
        sc.note(CH_BRASS, p, RESOLVE_T0, 14.0, 76, jt=0, jv=2)
    for p in (41, 48, 53):
        sc.note(CH_LEAD, p, RESOLVE_T0, 8.0, 86, jt=0, jv=2)
    en.strum(sc, CH_PNO, [41, 48, 53, 60, 65, 72, 77], RESOLVE_T0, 6.0,
             84, spread=0.05)
    en.arp(sc, CH_PNO, [65, 69, 72, 77, 81, 84], 1110.0, 6, 0.5, 46,
           gate=1.5)
    en.vowel(sc, CH_CHOIR, 98, RESOLVE_T0 - 0.1)
    for q in range(24):
        sc.hit(51, 1100.0 + q, int(en.lerp(40, 24, q / 23)), jt=2, jv=2)
    for ch in (CH_CHOIR, CH_STR, CH_ORG):
        en.expr_curve(sc, ch, [(RESOLVE_T0, 92), (1112.0, 66),
                               (1126.0, 30)], step=1.0)


# ---------------------------------------------------------------------------
# (i) The Ledger, Again — hidden, and cut off mid-phrase
# ---------------------------------------------------------------------------

def _i_epilogue(sc: en.Score) -> None:
    """The dulcimer whisper.  A hammered dulcimer has no dampers, so every
    struck course RINGS until the tape-cut — each note is held to the cut
    instant rather than choked at its notated length (the synth's release
    would otherwise silence the ring and the render-side
    audio_hidden_silence oracle would hear -50s dB: scored, not audible).
    Velocity alone cannot carry the audibility claim: the suite_dynamic_arc
    band (min >= 40, mean <= 70) pins the strikes to a whisper, and the
    synth's vel curve is (v/127)^1.6 — the whole legal velocity range is
    worth ~1 dB of render level.  So the room does the lifting instead:
    hall send wide open (CC91 127), the album's ping-pong tape echo
    (CC94 100) patting each strike into the gaps between plucks, and a
    breath of chorus shimmer (CC93 96) on the double courses.  The strikes
    themselves open the band fully — a real first-hammer accent dying
    linearly to pp (90 -> 44, mean ~67) — which centres the render level
    between audio_hidden_silence's two bounds (audible >= -50 dB, yet a
    whisper <= resolve - 6 dB).  The accent and the echo send are capped
    where they are because of the click-scan oracle: the dulcimer strike
    is a zero-attack transient erupting from digital silence, and at
    vel 94 / send 127 its echo replay measured a 22194 sample step
    (cap 22000)."""
    sc.cc(CH_DULC, 91, 127, SIL_T0)      # hall wide open for the ghost
    sc.cc(CH_DULC, 93, 96, SIL_T0)       # course shimmer
    sc.cc(CH_DULC, 94, 100, SIL_T0)      # the tape echo carries the ring
    quote = material.LEDGER_THEME[:material.LEDGER_EPILOGUE_NOTES]
    cut = sum(dur for _deg, dur in quote[:-1]) + 0.28   # the cut instant
    t = 0.0
    for i, (deg, dur) in enumerate(quote):
        last = i == len(quote) - 1
        vel = int(en.lerp(90, 44, i / (len(quote) - 1)))
        sc.note(CH_DULC, en.pitch(EPI_BASE, material.LEDGER_MODE, deg),
                EPI_NOTE_T0 + t, 0.28 if last else cut - t, vel,
                jt=2, jv=2)
        t += dur


BUILDERS: list = [_a_ledger, _b_sun, _c_mudlark, _d_polly, _e_window,
                  _f_slumber, _g_current, _h_endline, _i_epilogue]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the suite is composed to pass them
# ---------------------------------------------------------------------------

_TOL = 0.06


def _notes(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """[(on_beat, dur_beats, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[int, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on / en.PPQ, (tick - on) / en.PPQ,
                            data[1], vel))
    return sorted(out)


def _ccs(sc: en.Score, ch: int, num: int) -> list[tuple[float, int]]:
    return sorted((tick / en.PPQ, data[2])
                  for tick, _prio, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xB0 and data[1] == num)


def _progs(sc: en.Score, ch: int) -> list[tuple[float, int]]:
    return sorted((tick / en.PPQ, data[1])
                  for tick, _prio, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xC0)


def _bends(sc: en.Score, ch: int) -> list[tuple[float, float]]:
    return sorted((tick / en.PPQ, ((data[1] | (data[2] << 7)) - 8192)
                   / 8192.0)
                  for tick, _prio, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xE0)


def _has_note(notes, t: float, p: int, tol: float = _TOL) -> bool:
    return any(abs(on - t) <= tol and pitch == p
               for on, _d, pitch, _v in notes)


_MELODIC = (CH_PNO, CH_BASS, CH_LEAD, CH_ORG, CH_CHOIR, CH_STR, CH_FLUTE,
            CH_FID, CH_CELLO, CH_RTM, CH_EP, CH_BRASS, CH_HARP, CH_DULC,
            CH_PAD)


def _density(sc, lo: float, hi: float) -> float:
    """Velocity mass per beat across every channel in [lo, hi)."""
    tot = 0
    for ch in list(_MELODIC) + [CH_DRUMS]:
        tot += sum(v for on, _d, _p, v in _notes(sc, ch)
                   if lo - 0.03 <= on < hi - 0.03)
    return tot / (hi - lo)


def _check_ledger_theme(sc) -> list[str]:
    """(a) states material.LEDGER_THEME at all five documented spots."""
    fails = []
    pno = _notes(sc, CH_PNO)
    for t0, base in LEDGER_STATEMENTS:
        t = 0.0
        for deg, dur in material.LEDGER_THEME:
            want = en.pitch(base, material.LEDGER_MODE, deg)
            if not _has_note(pno, t0 + t, want):
                fails.append(f"statement at {t0:.0f}: no piano {want} at "
                             f"beat {t0 + t:.2f}")
            t += dur
    return fails


def _check_honky_tonk(sc) -> list[str]:
    """The collapse: honky-tonk program, double-time tempo, doubled
    keyboard traffic."""
    fails = []
    lane = _progs(sc, CH_PNO)
    if lane != [(0.0, 0), (HONKY_T0, 3), (SUN_T0, 0)]:
        fails.append(f"ch0 program lane {lane} != piano/honky-tonk/piano")
    tempos = dict(sc.tempos)
    if tempos.get(HONKY_T0) != HONKY_BPM or HONKY_BPM < 1.7 * BALLAD_BPM:
        fails.append(f"no double-time jump at {HONKY_T0:.0f} "
                     f"({tempos.get(HONKY_T0)} vs {BALLAD_BPM} x1.7)")
    ons = [on for on, _d, _p, _v in _notes(sc, CH_PNO)]
    ballad = len([1 for on in ons if 8.0 <= on < 88.0]) / 80.0
    honky = len([1 for on in ons if 120.0 <= on < 168.0]) / 48.0
    if honky < 1.5 * ballad:
        fails.append(f"honky keyboard density {honky:.2f}/beat < 1.5x "
                     f"ballad {ballad:.2f}/beat")
    return fails


_SUN_TRIAD = {5, 9, 0}
_SUN_PENT = {5, 7, 9, 0, 2}


def _check_sun_one_chord(sc) -> list[str]:
    """(b) is ONE F chord breathing: sustained lanes strictly triadic,
    sparkles pentatonic; the choir morphs vowels; the organ's Leslie
    genuinely spins up and down."""
    fails = []
    for ch in (CH_BASS, CH_ORG, CH_CHOIR, CH_PAD):
        for on, _d, p, _v in _notes(sc, ch):
            if SUN_T0 - 0.03 <= on < MUD_T0 - 0.03 \
                    and p % 12 not in _SUN_TRIAD:
                fails.append(f"ch{ch} pitch {p} at {on:.1f} is outside "
                             f"the F triad")
    for ch in (CH_PNO, CH_HARP, CH_FLUTE):
        for on, _d, p, _v in _notes(sc, ch):
            if SUN_T0 - 0.03 <= on < MUD_T0 - 0.03 \
                    and p % 12 not in _SUN_PENT:
                fails.append(f"ch{ch} pitch {p} at {on:.1f} is outside "
                             f"F pentatonic")
    cc70 = [v for b, v in _ccs(sc, CH_CHOIR, 70)
            if SUN_T0 <= b < MUD_T0]
    if len(cc70) < 8 or min(cc70) > 20 or max(cc70) < 80:
        fails.append(f"choir CC70 in the sun: {len(cc70)} events, "
                     f"span {min(cc70, default=0)}..{max(cc70, default=0)} "
                     f"(want >= 8 events, mm <= 20 to ah >= 80)")
    cc1 = [v for b, v in _ccs(sc, CH_ORG, 1) if SUN_T0 <= b < MUD_T0]
    if len(cc1) < 10 or (max(cc1, default=0) - min(cc1, default=0)) < 60:
        fails.append("the organ Leslie does not genuinely spin "
                     f"({len(cc1)} CC1 events, spread "
                     f"{max(cc1, default=0) - min(cc1, default=0)})")
    return fails


def _check_sun_birdsong(sc) -> list[str]:
    """>= 12 short high flute calls in >= 4 separated clusters."""
    fails = []
    calls = sorted(on for on, d, p, _v in _notes(sc, CH_FLUTE)
                   if SUN_T0 <= on < MUD_T0 and d <= 0.45 and p >= 77)
    if len(calls) < 12:
        fails.append(f"only {len(calls)} short high flute calls "
                     f"(want >= 12)")
    clusters = 1 if calls else 0
    for a, b in zip(calls, calls[1:]):
        if b - a > 2.0:
            clusters += 1
    if clusters < 4:
        fails.append(f"birdsong falls in {clusters} clusters (want >= 4)")
    return fails


def _check_mudlark_fuzz(sc) -> list[str]:
    """Fuzz programs, twelve riff statements, relentless backbeat."""
    fails = []
    if _progs(sc, CH_LEAD) != [(0.0, 30), (POL_T0, 29), (ENDL_T0, 30)]:
        fails.append(f"lead program lane {_progs(sc, CH_LEAD)} unexpected")
    if _progs(sc, CH_RTM) != [(0.0, 29), (POL_T0, 28)]:
        fails.append(f"rhythm program lane {_progs(sc, CH_RTM)} unexpected")
    lead = _notes(sc, CH_LEAD)
    for t in MUD_STATEMENTS:
        for on, _dur, semi in RIFF_MUD:
            if not _has_note(lead, t + on, MUD_BASE + semi):
                fails.append(f"riff at {t:.0f}: no lead {MUD_BASE + semi} "
                             f"at beat {t + on:.2f}")
    snare = [on for on, _d, p, _v in _notes(sc, CH_DRUMS) if p == 38]
    want = hits = 0
    for lo, hi in _MUD_STOMP_SPANS:
        b = lo
        while b < hi - 1e-6:
            for rel in (1.0, 3.0):
                want += 1
                if any(abs(s - (b + rel)) <= 0.1 for s in snare):
                    hits += 1
            b += 4.0
    if hits < 0.9 * want:
        fails.append(f"stomp backbeat coverage {hits}/{want} < 90%")
    return fails


def _check_polly_slides(sc) -> list[str]:
    """>= 12 slide gestures on the lead inside (d), each recentred."""
    fails = []
    fracs = [(b, f) for b, f in _bends(sc, CH_LEAD)
             if POL_T0 - 0.1 <= b < WIN_T0]
    gestures = 0
    start = None
    for b, f in fracs:
        if start is None and abs(f) >= 0.25:
            start = b
        elif start is not None and abs(f) <= 0.02:
            if b - start <= 2.0:
                gestures += 1
            start = None
    if gestures < 12:
        fails.append(f"only {gestures} recentred slide gestures in (d) "
                     f"(want >= 12)")
    return fails


def _check_window_hook(sc) -> list[str]:
    """The hook: leaning off the beat, stated six times in octaves."""
    fails = []
    off = sum(1 for on, _d, _p in HOOK_WIN if abs(on - round(on)) > 1e-6)
    if off / len(HOOK_WIN) < 0.5:
        fails.append(f"HOOK_WIN is only {off}/{len(HOOK_WIN)} off-beat")
    brass = _notes(sc, CH_BRASS)
    ep = _notes(sc, CH_EP)
    for t in HOOK_TIMES:
        for on, _dur, p in HOOK_WIN:
            if not _has_note(brass, t + on, p):
                fails.append(f"hook at {t:.0f}: no brass {p} at "
                             f"{t + on:.2f}")
            if not _has_note(ep, t + on, p + 12):
                fails.append(f"hook at {t:.0f}: no EP {p + 12} at "
                             f"{t + on:.2f}")
    return fails


def _check_slumber_swell(sc) -> list[str]:
    """The lullaby genuinely swells, and the tide keeps rising."""
    fails = []
    if (SLU_T0, 3, 4) not in sc.timesigs:
        fails.append("no 3/4 time signature at the lullaby")
    def mean_vel(lo, hi):
        vels = [v for ch in _MELODIC for on, _d, _p, v in _notes(sc, ch)
                if lo - 0.03 <= on < hi - 0.03]
        return sum(vels) / max(1, len(vels))
    first, second = mean_vel(SLU_T0, 781.0), mean_vel(781.0, CUR_T0)
    if not first < second:
        fails.append(f"lullaby velocities do not swell "
                     f"({first:.1f} !< {second:.1f})")
    crest = _density(sc, 942.0, 982.0)
    close = _density(sc, 781.0, CUR_T0)
    if not crest > close:
        fails.append(f"anthem crest density {crest:.0f} !> lullaby close "
                     f"{close:.0f}")
    return fails


def _check_fable_ground(sc) -> list[str]:
    """(g)'s ground bass IS material.FABLE_CELL — 42 loops, L silent."""
    fails = []
    bass = _notes(sc, CH_BASS)
    l0, l1 = material.FABLE_SILENT_L
    for k in range(GROUND_LOOPS):
        t = CUR_T0 + 4.0 * k
        for on, _dur, semi in material.FABLE_CELL:
            if not _has_note(bass, t + on, GROUND_ROOT + semi):
                fails.append(f"loop {k + 1}: no bass "
                             f"{GROUND_ROOT + semi} at {t + on:.2f}")
        if any(t + l0 + 0.03 <= on < t + l1 - 0.03
               for on, _d, _p, _v in bass):
            fails.append(f"loop {k + 1}: a bass note sings the silent L")
    return fails


def _check_drum_break(sc) -> list[str]:
    """The track's ONE melodically-silent-with-drums span is the break:
    2-4 bars, kit alone, >= 16 hits."""
    fails = []
    spans = sorted((on, on + d) for ch in _MELODIC
                   for on, d, _p, _v in _notes(sc, ch)
                   if on < LAST_H_OFF)
    drum_ons = [on for on, _d, _p, _v in _notes(sc, CH_DRUMS)]
    gaps = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > 1.0:
            gaps.append((horizon, on))
        horizon = max(horizon, off)
    breaks = [(lo, hi) for lo, hi in gaps
              if sum(1 for d in drum_ons if lo <= d < hi) >= 8]
    if len(breaks) != 1:
        fails.append(f"{len(breaks)} drums-alone spans {breaks} "
                     f"(want exactly the one break)")
        return fails
    lo, hi = breaks[0]
    if not (997.0 <= lo <= 999.0 and 1009.0 <= hi <= 1011.0):
        fails.append(f"the break sits at [{lo:.2f}, {hi:.2f}), want "
                     f"~[998, 1010)")
    if not 8.0 <= hi - lo <= 16.0:
        fails.append(f"break length {hi - lo:.1f} beats outside 2-4 bars")
    n_hits = sum(1 for d in drum_ons if BREAK_T0 - 0.1 <= d < BREAK_T1)
    if n_hits < 16:
        fails.append(f"only {n_hits} kit hits inside the break")
    return fails


def _check_trading_solos(sc) -> list[str]:
    """Nine 8-beat cells, strict guitar/organ/fiddle alternation x3."""
    fails = []
    counts = {ch: [on for on, _d, _p, _v in _notes(sc, ch)]
              for ch in SOLO_ORDER}
    for k in range(TRADE_ROUNDS * len(SOLO_ORDER)):
        t = TRADE_T0 + TRADE_CELL * k
        owner = SOLO_ORDER[k % 3]
        tag = (f"cell {k + 1} (round {k // 3 + 1}, "
               f"ch{owner})")
        for ch in SOLO_ORDER:
            n = len([1 for on in counts[ch]
                     if t - 0.03 <= on < t + TRADE_CELL - 0.03])
            if ch == owner and n < 5:
                fails.append(f"{tag}: owner plays only {n} notes")
            if ch != owner and n != 0:
                fails.append(f"{tag}: ch{ch} intrudes with {n} notes")
    return fails


def _check_final_chorale(sc) -> list[str]:
    """The cell against its exact inversion, resolving to F MAJOR."""
    fails = []
    strs = _notes(sc, CH_STR)
    cel = _notes(sc, CH_CELLO)
    for st in (CHORALE_T0, CHORALE_T0 + 8.0):
        for on, _dur, semi in material.FABLE_CELL:
            b = st + on * CHORALE_STRETCH
            if not _has_note(strs, b, CHORALE_ROOT + semi):
                fails.append(f"no cell note {CHORALE_ROOT + semi} "
                             f"at {b:.1f} (strings)")
            if not _has_note(cel, b, CHORALE_ROOT - semi):
                fails.append(f"no mirrored note {CHORALE_ROOT - semi} "
                             f"at {b:.1f} (cello)")
    if not _has_note(strs, RESOLVE_T0, CHORALE_ROOT + 12):
        fails.append("the E does not resolve up to F at the resolution")
    if not _has_note(cel, RESOLVE_T0, CHORALE_ROOT - 12):
        fails.append("the Gb does not resolve down to F")
    pcs = {p % 12 for ch in _MELODIC
           for on, _d, p, _v in _notes(sc, ch)
           if RESOLVE_T0 - 0.06 <= on <= RESOLVE_T0 + 0.6}
    if not pcs <= {5, 9, 0}:
        fails.append(f"resolution chord pcs {sorted(pcs)} stray from "
                     f"F major")
    if 9 not in pcs:
        fails.append("no A in the resolution — the tonic is not MAJOR")
    return fails


def _check_segue_continuity(sc) -> list[str]:
    """Songs (a)-(h): no all-channel silence longer than 0.5 seconds."""
    fails = []
    spans = sorted((on, on + d) for ch in list(_MELODIC) + [CH_DRUMS]
                   for on, d, _p, _v in _notes(sc, ch)
                   if on < LAST_H_OFF - 1.0)
    horizon = spans[0][1] if spans else 0.0
    for on, off in spans:
        if on > horizon:
            gap_s = sc.seconds_at(on) - sc.seconds_at(horizon)
            if gap_s > 0.5:
                fails.append(f"silence of {gap_s:.2f}s at beats "
                             f"[{horizon:.2f}, {on:.2f})")
        horizon = max(horizon, off)
    return fails


def _check_hidden_silence(sc) -> list[str]:
    """18-22 seconds of scored nothing before the epilogue."""
    fails = []
    last_off = max((on + d for ch in list(_MELODIC) + [CH_DRUMS]
                    for on, d, _p, _v in _notes(sc, ch)
                    if ch != CH_DULC and on < SIL_T0), default=0.0)
    dul = _notes(sc, CH_DULC)
    if not dul:
        return ["the epilogue never sounds"]
    gap_s = sc.seconds_at(dul[0][0]) - sc.seconds_at(last_off)
    if not 18.0 <= gap_s <= 22.0:
        fails.append(f"the pre-epilogue silence is {gap_s:.1f}s "
                     f"(want 18-22)")
    return fails


def _check_epilogue_quote(sc) -> list[str]:
    """The hidden track: the Ledger's opening, alone, cut mid-phrase."""
    fails = []
    dul = _notes(sc, CH_DULC)
    n_quote = material.LEDGER_EPILOGUE_NOTES
    if len(dul) != n_quote:
        fails.append(f"{len(dul)} dulcimer notes, want exactly {n_quote}")
        return fails
    t = 0.0
    for i, (deg, dur) in enumerate(material.LEDGER_THEME[:n_quote]):
        want = en.pitch(EPI_BASE, material.LEDGER_MODE, deg)
        if not _has_note(dul, EPI_NOTE_T0 + t, want):
            fails.append(f"epilogue note {i + 1}: no {want} at "
                         f"{EPI_NOTE_T0 + t:.2f}")
        t += dur
    if dul[-1][1] > 0.35:
        fails.append(f"the last note rings {dul[-1][1]:.2f} beats — "
                     f"not cut off")
    for ch in _MELODIC:
        if ch == CH_DULC:
            continue
        intruders = [on for on, _d, _p, _v in _notes(sc, ch)
                     if on >= SIL_T0 - 0.03]
        if intruders:
            fails.append(f"ch{ch} sounds at {intruders[0]:.1f} inside "
                         f"the hidden epilogue")
    drum_late = [on for on, _d, _p, _v in _notes(sc, CH_DRUMS)
                 if on >= SIL_T0 - 0.03]
    if drum_late:
        fails.append(f"the kit sounds at {drum_late[0]:.1f} after the end "
                     f"of the line")
    all_ons = [(on, ch) for ch in list(_MELODIC) + [CH_DRUMS]
               for on, _d, _p, _v in _notes(sc, ch)]
    last_on, last_ch = max(all_ons)
    if last_ch != CH_DULC:
        fails.append(f"the file's last note is on ch{last_ch}, not the "
                     f"dulcimer")
    return fails


def _check_dynamic_arc(sc) -> list[str]:
    """The suite's shape in numbers."""
    fails = []
    d_sun = _density(sc, SUN_T0, MUD_T0)
    d_mud = _density(sc, MUD_T0, POL_T0)
    d_crest = _density(sc, 942.0, 982.0)
    if not d_mud > 1.4 * d_sun:
        fails.append(f"mudlark {d_mud:.0f} !> 1.4x sun {d_sun:.0f}")
    if not d_crest > 1.5 * d_sun:
        fails.append(f"anthem crest {d_crest:.0f} !> 1.5x sun {d_sun:.0f}")
    epi = [v for _on, _d, _p, v in _notes(sc, CH_DULC)]
    if epi and (min(epi) < 40 or sum(epi) / len(epi) > 70):
        fails.append(f"epilogue velocities {min(epi)}..{max(epi)} outside "
                     f"the quiet-but-audible band")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("ledger_theme", _check_ledger_theme(sc)),
        ("honky_tonk_collapse", _check_honky_tonk(sc)),
        ("sun_one_chord", _check_sun_one_chord(sc)),
        ("sun_birdsong", _check_sun_birdsong(sc)),
        ("mudlark_fuzz", _check_mudlark_fuzz(sc)),
        ("polly_slides", _check_polly_slides(sc)),
        ("window_hook", _check_window_hook(sc)),
        ("slumber_swell", _check_slumber_swell(sc)),
        ("fable_ground", _check_fable_ground(sc)),
        ("drum_break_alone", _check_drum_break(sc)),
        ("trading_solos", _check_trading_solos(sc)),
        ("final_chorale", _check_final_chorale(sc)),
        ("segue_continuity", _check_segue_continuity(sc)),
        ("hidden_silence", _check_hidden_silence(sc)),
        ("epilogue_quote", _check_epilogue_quote(sc)),
        ("suite_dynamic_arc", _check_dynamic_arc(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/14 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The suite's contour on the RENDER, plus the hidden-track physics:
    the scored silence must be silent AIR, and the epilogue must be
    audible despite its low velocities (velocity is not audibility)."""
    def level(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    sun = level(178.0, 262.0)
    mud = level(266.0, 394.0)
    crest = level(942.0, 982.0)
    brk = level(998.5, 1009.5)
    resolve = level(1098.5, 1120.0)
    arc_fails = []
    if mud < sun + 3.0:
        arc_fails.append(f"mudlark {mud:.1f} dB is not >= 3 dB over the "
                         f"sun {sun:.1f} dB")
    if crest < sun + 4.0:
        arc_fails.append(f"anthem crest {crest:.1f} dB is not >= 4 dB "
                         f"over the sun {sun:.1f} dB")
    if brk < -45.0:
        arc_fails.append(f"the drum break ({brk:.1f} dB) is inaudible")

    silence = level(1132.0, 1148.0)
    epilogue = level(1150.5, 1159.5)
    hid_fails = []
    if silence > -55.0:
        hid_fails.append(f"the scored silence measures {silence:.1f} dB "
                         f"(want <= -55)")
    if epilogue < -50.0:
        hid_fails.append(f"the epilogue measures {epilogue:.1f} dB — "
                         f"scored but not audible")
    if epilogue > resolve - 6.0:
        hid_fails.append(f"the epilogue ({epilogue:.1f} dB) is not a "
                         f"whisper next to the resolution "
                         f"({resolve:.1f} dB)")
    return [("audio_suite_arc", arc_fails),
            ("audio_hidden_silence", hid_fails)]
