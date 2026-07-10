"""t04_fault_lines — Track 4 "Fault Lines" of *Through Lines*.

Disc 1, 'Lines of Descent'.  HLD section 3, T4: the state of the world,
2026.  Two tectonic blocks a tritone apart grind against each other —
Block A in C minor and 4/4 (orchestral: contrabass riff, strings, brass,
timpani), Block B in F sharp minor and 7/8 grouped 2+2+3 (palm-mute
guitar, synth bass, warm pad).  Between them a fragile 4-part hymn — the
album's bridge chorale — keeps trying to speak and keeps getting cut off.

THE ONE-METER LANE (binding design decision): a MIDI time-signature lane
can only carry one truth at a time, so this file's lane says 4/4 from the
first beat to the last.  Block B's 7/8 is therefore NOT in the meta lane
at all — it exists as a property of the music itself, and the
`b_block_sevens` oracle enforces it on Block B's onset grid: every guitar
onset in the B spans sits on the eighth grid of a 3.5-beat cycle, every
cycle carries its 2+2+3 group accents (positions 0, 1, 2) louder than
every off-group eighth, and every cycle is fully populated.  The key
signature lane makes the same compromise (C minor, D minor for the hymn,
F sharp minor for Block B alone, C minor for the collision and coda);
the `bitonal_blocks` oracle carries the truth the lane cannot: Block A's
channels never once leave C aeolian, Block B's never leave F sharp
aeolian, the hymn channel never leaves D aeolian, and the orchestra-hit
channel speaks only the two tonics, pitch-classes C and F sharp.

The through-lines and their oracles (all written BEFORE the music):

 * The bridge chorale (material.BRIDGE_CHORALE, on the neutral root D —
   the ground T7's dawn will pick it up from) is stated three times
   before the coda via material.play_chorale(..., n_chords=k) with
   k = 3, 5, 7 — every statement truncated (k < 8), each trying harder
   than the last (k strictly increasing), and each cut off by an
   orchestra hit within one beat of its truncation (`hymn_interruptions`;
   cut i by Block A's C hit, cut ii by Block B's F sharp hit, cut iii by
   both at once).
 * The coda plays the chorale COMPLETE — all eight chords — in BOTH keys
   simultaneously: Block A's strings carry material.chorale_pitches(60)
   (C minor) while Block B's pad carries material.chorale_pitches(66)
   (F sharp minor), note-for-note, rhythmically united (per-chord onsets
   inside one small band) — coexistence, not resolution
   (`coda_coexistence`).
 * A woodblock news-ticker (channel 9, key 76, and key 76 belongs to the
   ticker ALONE) taps HOLD THE LINE in Morse four times, timing verbatim
   from material.morse_rhythm(material.MORSE_T4); the oracle re-decodes
   the lane back to dits and dahs and the text (`morse_hold_the_line`).
 * The doomscroll: a marimba ostinato whose inter-onset intervals are an
   arithmetic sequence IN TICKS — 720 ticks down to 60 by exactly 3 —
   so the accelerando is strictly decreasing at tick resolution across
   all 221 notes, while the repeated pitch fragments downward and the
   velocity climbs (`doomscroll_accelerando`).
 * The end: after the coexistence chorale dissolves, a lone flute plays
   the piece's final two melodic events — a QUIET RISING MINOR SIXTH,
   C5 to Ab5 (+8 semitones), unresolved; Ab is G sharp, so the last
   interval belongs to both worlds at once.  The final bar's energy is
   at most 0.15x the peak bar (`ending_rising_sixth`), and the whole
   dramatic shape is pinned as per-bar velocity-sum inequalities
   (`tectonic_arc`).

Scored near-silences (contract section 6, velocity is not audibility):
the rumble pedals under the hymn statements (vel 18-30), the post-rupture
fault (beats 556-564, GAP_WHITELIST), and the final flute pair (vel
34/30) are all deliberate, and asserted — audio_checks() additionally
holds the RENDER to the collision peak, the post-hit shocks, the fault
silence and the quiet ending, in dB.

Movements (4/4 lane throughout; 112 bpm, 116 in the collision, 84 coda):
    i.    Hairline                       beats   0-56
    ii.   Block A - C minor, 4/4         beats  56-168
    iii.  The Hymn, Cut at Three         beats 168-196
    iv.   Block B - F sharp minor, 7/8   beats 196-308
    v.    The Hymn, Cut at Five          beats 308-336
    vi.   Collision                      beats 336-560
    vii.  Fault Silence                  beats 560-564
    viii. Coda - Coexistence             beats 564-640
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 4
TITLE = 'Fault Lines'
FILE = '04 - Fault Lines.mid'
SEED = 20260904

COMMENT = ("Track 4: two tectonic blocks - C minor in 4/4, F sharp minor "
           "in 7/8 - grind while a woodblock ticker taps HOLD THE LINE, a "
           "doomscroll ostinato accelerates, and a fragile hymn is cut "
           "off three times; the coda plays it whole in both keys at "
           "once and ends on a quiet rising minor sixth, unresolved.")

# ---------------------------------------------------------------------------
# Channels and fixed design data
# ---------------------------------------------------------------------------

CH_A_BASS = 0    # contrabass (GM 43) — Block A riff + pedals     centred
CH_A_STR = 1     # strings (GM 48) — A pads; C-minor coda chorale centred
CH_A_BRASS = 2   # brass section (GM 61) — Block A stabs          centred
CH_A_TIMP = 3    # timpani (GM 47) — transient                    pan 54
CH_A_FLUTE = 4   # flute (GM 73) — A lament; the final sixth      centred
CH_B_GTR = 5     # palm-mute guitar (GM 28) — Block B riff        pan 74
CH_B_BASS = 6    # synth bass (GM 38) — Block B roots             centred
CH_B_PAD = 7     # warm pad (GM 89) — B drone; F#-minor chorale   centred
CH_CHOR = 8      # choir (GM 52) — the hymn on D; coda D pedal    centred
CH_HIT = 10      # orchestra hit (GM 55) — tonics C and F# only   centred
CH_DOOM = 11     # marimba (GM 12) — the doomscroll               pan 46

_TICK = 1.0 / en.PPQ

# Pitch-class worlds (aeolian).  C: c d eb f g ab bb; F#: f# g# a b c# d e;
# D (the hymn's neutral ground, shared with T7's dawn): d e f g a bb c.
_C_AEO = {0, 2, 3, 5, 7, 8, 10}
_FS_AEO = {6, 8, 9, 11, 1, 2, 4}
_D_AEO = {2, 4, 5, 7, 9, 10, 0}

A_CHANNELS = (CH_A_BASS, CH_A_STR, CH_A_BRASS, CH_A_TIMP, CH_A_FLUTE,
              CH_DOOM)
B_CHANNELS = (CH_B_GTR, CH_B_BASS, CH_B_PAD)
_ALL_PITCHED = A_CHANNELS + B_CHANNELS + (CH_CHOR, CH_HIT)

# Core riff spans (the meter-grid oracles run inside these; pedals and
# pre-echoes outside them are not the riff).
A_SPANS = ((56.0, 168.0), (336.0, 528.0))     # 28 + 48 bars of 4/4
B_SPANS = ((196.0, 308.0), (336.0, 525.0))    # 32 + 54 cycles of 3.5

# Block A riff — one 2-bar cell (8 beats), onsets on the eighth grid,
# bar-starts 0.0 and 4.0 always struck.  All pitches in C aeolian.
A_RIFF = [(0.0, 1.0, 36), (1.0, 0.5, 36), (1.5, 0.5, 39), (2.0, 1.0, 36),
          (3.0, 1.0, 43), (4.0, 0.5, 41), (4.5, 0.5, 39), (5.0, 1.0, 36),
          (6.0, 1.0, 44), (7.0, 1.0, 43)]

# Block B riff — one 7/8 cycle (3.5 beats), 2+2+3 group starts at
# positions 0.0 / 1.0 / 2.0 accented (+14).  All pitches in F# aeolian.
B_ACCENT = 14
B_RIFF = [(0.0, 0.5, 54, B_ACCENT), (0.5, 0.5, 54, 0),
          (1.0, 0.5, 57, B_ACCENT), (1.5, 0.5, 54, 0),
          (2.0, 0.5, 52, B_ACCENT), (2.5, 0.5, 54, 0),
          (3.0, 0.5, 49, 0)]

# The hymn: three truncated statements (t0, n_chords, vel) on root D —
# k strictly increasing, always < 8 — then the coda's double statement.
HYMN_ROOT = 62
HYMN_STATEMENTS: tuple[tuple[float, int, int], ...] = (
    (172.0, 3, 58),
    (312.0, 5, 62),
    (532.0, 7, 66),
)
HYMN_CHORD_BEATS = 2.0
CODA_T0 = 568.0
CODA_CHORD_BEATS = 3.0
CODA_ROOT_A = 60                 # C minor, on Block A's strings
CODA_ROOT_B = 66                 # F# minor, on Block B's pad

# The news ticker: HOLD THE LINE, four passes, ch 9 key 76 exclusively.
TICKER_KEY = 76
TICKER_UNIT = 0.25
TICKER_PASSES: tuple[tuple[float, int], ...] = (
    (16.0, 52), (208.0, 58), (364.0, 66), (448.0, 72))

# The doomscroll: IOIs 720 ticks down to 60 by exactly 3 (221 onsets).
DOOM_T0 = 350.0
DOOM_IOI_HI, DOOM_IOI_LO, DOOM_IOI_STEP = 720, 60, 3
DOOM_COUNT = (DOOM_IOI_HI - DOOM_IOI_LO) // DOOM_IOI_STEP + 1   # 221

# The ending: a quiet rising minor sixth, unresolved.
END_P1, END_P2 = 72, 80          # C5 -> Ab5 (+8; Ab == G#: both worlds)
END_T1, END_T2 = 616.0, 621.0
FINAL_ENERGY_RATIO = 0.15

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("i. Hairline", 0.0, 56.0),
        ("ii. Block A - C minor, 4/4", 56.0, 168.0),
        ("iii. The Hymn, Cut at Three", 168.0, 196.0),
        ("iv. Block B - F sharp minor, 7/8", 196.0, 308.0),
        ("v. The Hymn, Cut at Five", 308.0, 336.0),
        ("vi. Collision", 336.0, 560.0),
        ("vii. Fault Silence", 560.0, 564.0),
        ("viii. Coda - Coexistence", 564.0, 640.0),
    ],
    tempo_map=[(0.0, 112.0), (336.0, 116.0), (560.0, 84.0)],
    # ONE meter in the lane (see module docstring): 7/8 lives in the
    # b_block_sevens oracle, not in the meta track.
    time_signatures=[(0.0, 4, 4)],
    # One key at a time in the lane, too; bitonal_blocks carries the rest.
    keysigs=[(0.0, -3, 1), (168.0, -1, 1), (196.0, 3, 1),
             (308.0, -1, 1), (336.0, -3, 1)],
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_A_BASS, "block A contrabass", 43, 105, 64, 42),
        (CH_A_STR, "block A strings", 48, 95, 64, 58),
        (CH_A_BRASS, "block A brass", 61, 96, 64, 45),
        (CH_A_TIMP, "timpani", 47, 100, 54, 50),
        (CH_A_FLUTE, "flute", 73, 95, 64, 60),
        (CH_B_GTR, "block B palm-mute", 28, 100, 74, 28),
        (CH_B_BASS, "block B synth bass", 38, 102, 64, 22),
        (CH_B_PAD, "block B pad", 89, 92, 64, 55),
        (CH_CHOR, "the hymn (choir)", 52, 95, 64, 62),
        (9, "drums", 0, 100, 64, 40),
        (CH_HIT, "orchestra hit", 55, 105, 64, 50),
        (CH_DOOM, "doomscroll marimba", 12, 95, 46, 35),
    ],
    program_changes=[(9, 0.0, 16)],          # v2 kit (sizzle, rattle)
    extra_markers=[
        (16.0, "news ticker: HOLD THE LINE (i)"),
        (172.0, "the hymn, cut at three"),
        (208.0, "news ticker (ii)"),
        (312.0, "the hymn, cut at five"),
        (350.0, "doomscroll accelerando begins"),
        (364.0, "news ticker (iii)"),
        (448.0, "news ticker (iv)"),
        (532.0, "the hymn, cut at seven"),
        (546.5, "double rupture"),
        (568.0, "the hymn, whole, in both keys at once"),
        (616.0, "a rising minor sixth, unresolved"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {43, 48, 61, 47, 73, 28, 38, 89, 52, 55, 12}
CENTERED_CHANNELS: set[int] = {CH_A_BASS, CH_A_STR, CH_A_BRASS, CH_A_FLUTE,
                               CH_B_BASS, CH_B_PAD, CH_CHOR, 9, CH_HIT}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_A_BASS: (36, 48),
    CH_A_STR: (48, 80),
    CH_A_BRASS: (52, 72),
    CH_A_TIMP: (36, 50),
    CH_A_FLUTE: (70, 85),
    CH_B_GTR: (40, 60),
    CH_B_BASS: (36, 48),
    CH_B_PAD: (50, 86),
    CH_CHOR: (50, 82),
    CH_HIT: (58, 68),
    CH_DOOM: (65, 80),
}
GAP_WHITELIST: list[tuple[float, float]] = [(555.0, 565.0)]  # the fault
BEND_EXEMPT: set[int] = set()      # the rupture dive recentres at 558.5
DURATION_WINDOW: tuple[float, float] = (342.0, 356.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Shared texture helpers
# ---------------------------------------------------------------------------

def _a_riff(sc: en.Score, s: float, vel: int) -> None:
    for on, du, p in A_RIFF:
        acc = 6 if on in (0.0, 4.0) else 0
        sc.note(CH_A_BASS, p, s + on, du * 0.96, vel + acc, jt=0, jv=3)


def _b_riff(sc: en.Score, s: float, vel: int) -> None:
    for on, du, p, acc in B_RIFF:
        sc.note(CH_B_GTR, p, s + on, du * 0.9, vel + acc, jt=0, jv=3)


def _a_drums(sc: en.Score, s: float, vel: int, crash: bool = False,
             fill: bool = False) -> None:
    """One 8-beat Block-A cell of 4/4 kit."""
    for k in (0.0, 2.5, 4.0, 6.5):
        sc.hit(36, s + k, vel)
    for k in (2.0, 6.0):
        sc.hit(38, s + k, vel + 6)
    hat_end = 7.0 if fill else 8.0
    b = 0.0
    while b < hat_end - 1e-9:
        if b not in (3.5, 7.5):
            sc.hit(42, s + b, vel - 26 + (8 if b == int(b) else 0))
        b += 0.5
    for k in (3.5, 7.5):
        if k < hat_end:
            sc.hit(46, s + k, vel - 14)
    if crash:
        sc.hit(49, s, vel + 10)
    if fill:
        for i, drum in enumerate((47, 47, 45, 45, 43, 43, 41, 41)):
            sc.hit(drum, s + 7.0 + i * 0.125, vel - 10 + i * 2)


def _b_drums(sc: en.Score, s: float, vel: int, c: int) -> None:
    """One 3.5-beat Block-B cycle of 7/8 kit (kicks on the 2+2+3 starts)."""
    sc.hit(36, s, vel)
    sc.hit(36, s + 1.0, vel - 4)
    sc.hit(40, s + 2.0, vel + 4)
    for b in (0.5, 1.5, 2.5, 3.0):
        sc.hit(42, s + b, vel - 26)
    if c % 2:
        sc.hit(53, s, vel - 10)
    if c % 16 == 0:
        sc.hit(49, s, vel + 8)


def _ticker_pass(sc: en.Score, t0: float, vel: int) -> None:
    """One verbatim HOLD THE LINE pass on ch9 key 76 (jt=0: decodable)."""
    for on, dur in material.morse_rhythm(material.MORSE_T4, TICKER_UNIT):
        sc.note(9, TICKER_KEY, t0 + on, dur, vel, jt=0, jv=2)


def _doom_events() -> list[tuple[float, float]]:
    """(onset_beats, ioi_beats) for the doomscroll — IOIs are integer
    ticks 720 down to 60 by 3, so the decrease is strict at tick
    resolution.  Deterministic; no RNG."""
    out: list[tuple[float, float]] = []
    t = int(round(DOOM_T0 * en.PPQ))
    ioi = DOOM_IOI_HI
    while ioi >= DOOM_IOI_LO:
        out.append((t / en.PPQ, ioi / en.PPQ))
        t += ioi
        ioi -= DOOM_IOI_STEP
    return out


def _doom_pitch(k: int) -> int:
    """The doomscroll pitch fragments downward as it accelerates —
    C-aeolian pitches only."""
    if k < 70:
        return 79
    if k < 120:
        return (79, 77)[k % 2]
    if k < 160:
        return (77, 75, 74)[k % 3]
    if k < 200:
        return (75, 74, 72, 70)[k % 4]
    return (72, 70, 68, 67)[k % 4]


def _hymn_statement(sc: en.Score, t0: float, k: int, vel: int) -> float:
    """One truncated chorale statement on the choir; returns truncation."""
    tc = material.play_chorale(sc, CH_CHOR, t0, HYMN_ROOT,
                               chord_beats=HYMN_CHORD_BEATS, vel=vel,
                               n_chords=k, jt=2, jv=2)
    en.vowel_curve(sc, CH_CHOR, [(t0, 15), (tc - 0.5, 50)], step=1.0)
    en.cc_curve(sc, CH_CHOR, 11, [(t0, 58), (tc - 0.5, 72)], step=1.0)
    return tc


# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------

def _m1_hairline(sc: en.Score) -> None:
    """[0, 56) Quiet C pedal, first seismic ticks, ticker pass i.  The
    pedals are scored near-silence (vel 30-42), waking slowly."""
    for k in range(7):
        sc.note(CH_A_BASS, 36, 8.0 * k, 7.9, 30 + 2 * k, jt=3, jv=2)
    en.cc_curve(sc, CH_A_STR, 11, [(0.0, 30), (24.0, 46), (55.0, 62)],
                step=1.0)
    sc.note(CH_A_STR, 48, 8.0, 15.9, 36, jt=3, jv=2)
    sc.note(CH_A_STR, 55, 12.0, 11.9, 36, jt=3, jv=2)
    sc.note(CH_A_STR, 48, 24.0, 15.9, 40, jt=3, jv=2)
    sc.note(CH_A_STR, 55, 24.0, 15.9, 38, jt=3, jv=2)
    sc.note(CH_A_STR, 60, 28.0, 11.9, 40, jt=3, jv=2)
    sc.note(CH_A_STR, 48, 40.0, 15.5, 42, jt=3, jv=2)
    sc.note(CH_A_STR, 55, 40.0, 15.5, 42, jt=3, jv=2)
    sc.note(CH_A_STR, 63, 44.0, 11.5, 44, jt=3, jv=2)
    sc.note(CH_A_TIMP, 36, 12.0, 1.0, 44, jt=2, jv=3)
    sc.note(CH_A_TIMP, 36, 28.0, 1.0, 50, jt=2, jv=3)
    sc.note(CH_A_TIMP, 43, 44.0, 1.0, 52, jt=2, jv=3)
    for i in range(16):                       # roll into Block A
        sc.note(CH_A_TIMP, 36, 52.0 + i * 0.25, 0.24,
                round(en.lerp(40, 66, i / 15)), jt=1, jv=2)
    for k in range(6):                        # heartbeat kicks
        sc.hit(36, 32.0 + 4.0 * k, 34 + 2 * k)
    _ticker_pass(sc, *TICKER_PASSES[0])


def _m2_block_a(sc: en.Score) -> None:
    """[56, 168) Block A: the C-minor 4/4 grind — 14 riff cells, kit,
    stabs, pads, a cold flute lament from beat 120, timpani roll into
    the halt at 168."""
    pcs_cm, pcs_ab = [0, 3, 7], [8, 0, 3]
    pcs_bb, pcs_eb = [10, 2, 5], [3, 7, 10]
    chords = [pcs_cm, pcs_cm, pcs_ab, pcs_bb, pcs_cm, pcs_ab, pcs_eb,
              pcs_bb, pcs_cm, pcs_cm, pcs_ab, pcs_bb, pcs_cm, pcs_bb]
    en.pad_block(sc, CH_A_STR, 56.0, chords, span=8.0, size=4,
                 lo=50, hi=74, vel=44, vel_end=56, legato=0.2)
    for c in range(14):
        s = 56.0 + 8.0 * c
        vb = round(en.lerp(64, 84, c / 13))
        _a_riff(sc, s, vb)
        _a_drums(sc, s, vb + 4, crash=(c % 4 == 0), fill=(c % 4 == 3))
        sc.note(CH_A_TIMP, 36, s, 1.0, round(en.lerp(66, 80, c / 13)),
                jt=2, jv=3)
        if c % 2 == 1:
            sc.note(CH_A_TIMP, 43, s + 4.0, 1.0, 62, jt=2, jv=3)
        if c >= 2:
            sv = round(en.lerp(72, 90, c / 13))
            for p in (60, 63, 67):
                sc.note(CH_A_BRASS, p, s + 3.5, 0.4, sv, jt=2, jv=3)
        if c >= 6:
            for p in (58, 62, 65):
                sc.note(CH_A_BRASS, p, s + 7.0, 0.4, sv - 4, jt=2, jv=3)
        if c >= 10:
            for p in (56, 60, 63):
                sc.note(CH_A_BRASS, p, s + 6.0, 0.35, sv - 6, jt=2, jv=3)
    en.cc_curve(sc, CH_A_FLUTE, 1, [(120.0, 0), (124.0, 45), (164.0, 45),
                                    (166.0, 0)], step=1.0)
    en.cc_curve(sc, CH_A_FLUTE, 11, [(120.0, 50), (140.0, 66),
                                     (165.0, 54)], step=2.0)
    for p, on, du, v in ((79, 120.0, 6.0, 52), (77, 127.0, 4.5, 54),
                         (75, 133.0, 5.0, 56), (72, 140.0, 6.0, 58),
                         (74, 147.0, 4.0, 58), (75, 152.0, 5.0, 60),
                         (79, 158.0, 7.5, 62)):
        sc.note(CH_A_FLUTE, p, on, du, v, jt=3, jv=2)
    for i in range(16):                       # roll into the halt
        sc.note(CH_A_TIMP, 36, 164.0 + i * 0.25, 0.24,
                round(en.lerp(46, 74, i / 15)), jt=1, jv=2)


def _m3_hymn_cut_i(sc: en.Score) -> None:
    """[168, 196) The grind halts; the hymn tries (3 chords, on D) and
    Block A's C hit cuts it at beat 178; palm-mute pre-echo of Block B
    crescendos into 196.  Rumble pedals are scored near-silence."""
    sc.note(CH_A_BASS, 36, 168.0, 13.9, 26, jt=0, jv=2)
    sc.note(CH_A_BASS, 36, 182.0, 12.0, 24, jt=0, jv=2)
    tc = _hymn_statement(sc, *HYMN_STATEMENTS[0])
    sc.note(CH_HIT, 60, tc + 0.5, 2.0, 98, jt=0, jv=2)
    sc.hit(36, tc + 0.5, 100)
    sc.hit(57, tc + 0.5, 96)
    for on, v in ((tc + 0.5, 92), (tc + 1.75, 78), (tc + 3.25, 64),
                  (tc + 5.0, 50)):
        sc.note(CH_A_TIMP, 36, on, 0.6, v, jt=1, jv=3)
    for i in range(16):                       # Block B pre-echo chugs
        sc.note(CH_B_GTR, 42, 188.0 + i * 0.5, 0.42,
                round(en.lerp(40, 58, i / 15)), jt=0, jv=3)


def _m4_block_b(sc: en.Score) -> None:
    """[196, 308) Block B: the F#-minor 7/8 grind — 32 cycles of 3.5
    beats grouped 2+2+3, ticker pass ii floating over it in its own
    straight time (the news does not care what meter you are in)."""
    for c in range(32):
        s = 196.0 + 3.5 * c
        vb = round(en.lerp(64, 82, c / 31))
        _b_riff(sc, s, vb)
        _b_drums(sc, s, vb + 2, c)
        sc.note(CH_B_BASS, 42, s, 0.9, vb, jt=0, jv=3)
        sc.note(CH_B_BASS, 42, s + 1.0, 0.9, vb - 4, jt=0, jv=3)
        if c % 4 == 3:
            sc.note(CH_B_BASS, 40, s + 2.0, 0.7, vb, jt=0, jv=3)
            sc.note(CH_B_BASS, 38, s + 2.75, 0.65, vb - 4, jt=0, jv=3)
        else:
            sc.note(CH_B_BASS, 37, s + 2.0, 1.4, vb, jt=0, jv=3)
    pads = [[54, 61, 66], [57, 61, 64], [59, 62, 66], [54, 61, 66],
            [50, 54, 57], [57, 61, 64], [59, 62, 66], [54, 61, 66]]
    en.cc_curve(sc, CH_B_PAD, 11, [(196.0, 46), (252.0, 60), (307.0, 66)],
                step=2.0)
    for i, chord in enumerate(pads):
        for p in chord:
            sc.note(CH_B_PAD, p, 196.0 + 14.0 * i, 13.9,
                    44 + i, jt=3, jv=2)
    _ticker_pass(sc, *TICKER_PASSES[1])


def _m5_hymn_cut_ii(sc: en.Score) -> None:
    """[308, 336) Block B halts; the hymn tries harder (5 chords) and
    Block B's F# hit cuts it at 322; both pedals then crescendo toward
    the collision, timpani roll from 332."""
    sc.note(CH_B_BASS, 42, 308.0, 13.9, 26, jt=0, jv=2)
    tc = _hymn_statement(sc, *HYMN_STATEMENTS[1])
    sc.note(CH_HIT, 66, tc + 0.5, 2.0, 102, jt=0, jv=2)
    sc.hit(36, tc + 0.5, 102)
    sc.hit(57, tc + 0.5, 98)
    sc.note(CH_B_BASS, 42, 322.0, 3.9, 24, jt=0, jv=2)
    sc.note(CH_A_BASS, 36, 326.0, 4.9, 34, jt=0, jv=2)
    sc.note(CH_A_BASS, 36, 331.0, 4.9, 44, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 326.0, 4.9, 36, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 331.0, 4.9, 46, jt=0, jv=2)
    for i in range(16):
        sc.note(CH_A_TIMP, 36, 332.0 + i * 0.25, 0.24,
                round(en.lerp(44, 78, i / 15)), jt=1, jv=2)
    for k in range(4):
        sc.hit(36, 332.0 + k, 60 + 8 * k)


def _m6_collision(sc: en.Score) -> None:
    """[336, 560) Both blocks at once: A's 4/4 riff and B's 7/8 riff
    grind over each other (the crash cymbal shadows B every 7 beats),
    the doomscroll accelerates through 221 strictly-shrinking IOIs,
    the ticker passes twice more, the flute keens; at 528 one tutti
    chord cuts to rumble, the hymn makes its longest try (7 chords),
    and the double rupture — both tonics at once — breaks it, the
    pad's ground giving way in a two-semitone dive (recentred 558.5)."""
    # the announcement: both tonics at once
    sc.note(CH_HIT, 60, 336.0, 2.0, 104, jt=0, jv=2)
    sc.note(CH_HIT, 66, 336.0, 2.0, 104, jt=0, jv=2)
    # Block A machinery — 24 cells
    pcs_cm, pcs_ab = [0, 3, 7], [8, 0, 3]
    pcs_bb, pcs_eb = [10, 2, 5], [3, 7, 10]
    chords = ([pcs_cm, pcs_ab, pcs_bb, pcs_eb,
               pcs_cm, pcs_ab, pcs_bb, pcs_cm] * 3)
    en.pad_block(sc, CH_A_STR, 336.0, chords, span=8.0, size=4,
                 lo=55, hi=79, vel=52, vel_end=62, legato=0.2)
    for c in range(24):
        s = 336.0 + 8.0 * c
        vb = round(en.lerp(76, 92, c / 23))
        _a_riff(sc, s, vb)
        _a_drums(sc, s, vb + 4, crash=(c % 4 == 0), fill=(c % 4 == 3))
        sc.note(CH_A_TIMP, 36, s, 1.0, round(en.lerp(74, 88, c / 23)),
                jt=2, jv=3)
        if c % 2 == 1:
            sc.note(CH_A_TIMP, 43, s + 4.0, 1.0, 70, jt=2, jv=3)
        if c < 20:
            sv = round(en.lerp(80, 94, c / 19))
            for p in (60, 63, 67):
                sc.note(CH_A_BRASS, p, s + 3.5, 0.4, sv, jt=2, jv=3)
            for p in (58, 62, 65):
                sc.note(CH_A_BRASS, p, s + 7.0, 0.4, sv - 4, jt=2, jv=3)
            if c >= 8:
                for p in (56, 60, 63):
                    sc.note(CH_A_BRASS, p, s + 6.0, 0.35, sv - 6,
                            jt=2, jv=3)
    # Block B machinery — 54 cycles + the 7-beat crash shadow
    for c in range(54):
        s = 336.0 + 3.5 * c
        vb = round(en.lerp(78, 90, c / 53))
        _b_riff(sc, s, vb)
        sc.note(CH_B_BASS, 42, s, 0.9, vb, jt=0, jv=3)
        sc.note(CH_B_BASS, 42, s + 1.0, 0.9, vb - 4, jt=0, jv=3)
        sc.note(CH_B_BASS, 37, s + 2.0, 1.4, vb, jt=0, jv=3)
    for k in range(27):
        sc.hit(57, 336.0 + 7.0 * k, 70)
    pads = [[54, 61, 66], [57, 61, 64], [59, 62, 66], [50, 54, 57]] * 3
    pads.append([54, 61, 66])
    en.cc_curve(sc, CH_B_PAD, 11, [(336.0, 56), (440.0, 66), (527.0, 60)],
                step=2.0)
    for i, chord in enumerate(pads[:13]):
        for p in chord:
            sc.note(CH_B_PAD, p, 336.0 + 14.0 * i, 13.9, 48 + i // 2,
                    jt=3, jv=2)
    sc.note(CH_B_PAD, 54, 518.0, 9.9, 54, jt=3, jv=2)
    sc.note(CH_B_PAD, 61, 518.0, 9.9, 52, jt=3, jv=2)
    sc.note(CH_B_PAD, 66, 518.0, 9.9, 52, jt=3, jv=2)
    # the doomscroll
    events = _doom_events()
    for k, (on, ioi) in enumerate(events):
        sc.note(CH_DOOM, _doom_pitch(k), on, ioi * 0.72,
                round(en.lerp(44, 84, k / (len(events) - 1))), jt=0, jv=2)
    # the news, twice more
    _ticker_pass(sc, *TICKER_PASSES[2])
    _ticker_pass(sc, *TICKER_PASSES[3])
    # the flute keens over the grind
    en.cc_curve(sc, CH_A_FLUTE, 1, [(400.0, 0), (404.0, 55), (468.0, 55),
                                    (469.5, 0)], step=1.0)
    en.cc_curve(sc, CH_A_FLUTE, 11, [(400.0, 56), (440.0, 72),
                                     (469.0, 58)], step=2.0)
    for p, on, du, v in ((79, 400.0, 6.0, 60), (80, 408.0, 5.0, 62),
                         (77, 414.0, 4.5, 60), (75, 420.0, 6.0, 58),
                         (79, 428.0, 6.0, 64), (84, 440.0, 8.0, 66),
                         (82, 450.0, 4.5, 62), (80, 456.0, 6.0, 60),
                         (77, 464.0, 5.0, 58)):
        sc.note(CH_A_FLUTE, p, on, du, v, jt=3, jv=2)
    # 528: one tutti chord, then the floor drops out
    sc.note(CH_HIT, 60, 528.0, 1.5, 106, jt=0, jv=2)
    sc.note(CH_HIT, 66, 528.0, 1.5, 106, jt=0, jv=2)
    for p in (60, 63, 67):
        sc.note(CH_A_BRASS, p, 528.0, 1.5, 92, jt=1, jv=2)
    sc.note(CH_A_BASS, 36, 528.0, 1.5, 90, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 528.0, 1.5, 90, jt=0, jv=2)
    sc.note(CH_A_TIMP, 36, 528.0, 1.0, 96, jt=1, jv=2)
    sc.hit(36, 528.0, 108)
    sc.hit(57, 528.0, 102)
    sc.note(CH_A_BASS, 36, 529.5, 2.4, 24, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 529.5, 2.4, 22, jt=0, jv=2)
    # the longest try: 7 chords over bare rumble
    sc.note(CH_A_BASS, 36, 532.0, 6.9, 22, jt=0, jv=1)
    sc.note(CH_A_BASS, 36, 539.0, 6.9, 20, jt=0, jv=1)
    sc.note(CH_B_BASS, 42, 532.0, 6.9, 20, jt=0, jv=1)
    sc.note(CH_B_BASS, 42, 539.0, 6.9, 18, jt=0, jv=1)
    tc = _hymn_statement(sc, *HYMN_STATEMENTS[2])
    # the double rupture: both tonics cut the hymn at once
    sc.note(CH_HIT, 60, tc + 0.5, 3.0, 108, jt=0, jv=2)
    sc.note(CH_HIT, 66, tc + 0.5, 3.0, 108, jt=0, jv=2)
    sc.hit(36, tc + 0.5, 110)
    sc.hit(57, tc + 0.5, 104)
    sc.hit(49, tc + 0.5, 100)
    sc.note(CH_A_TIMP, 36, tc + 0.5, 1.0, 100, jt=1, jv=2)
    # the ground gives way: pad dive, decelerating aftershocks
    sc.note(CH_B_PAD, 54, 546.5, 10.0, 58, jt=0, jv=2)
    sc.note(CH_B_PAD, 61, 546.5, 10.0, 56, jt=0, jv=2)
    sc.note(CH_B_PAD, 66, 546.5, 10.0, 56, jt=0, jv=2)
    en.bend_ramp(sc, CH_B_PAD, 547.0, 556.0, 0.0, -2.0, steps=16)
    sc.bend(CH_B_PAD, 558.5, 0.0)
    en.cc_curve(sc, CH_B_PAD, 11, [(546.5, 72), (556.5, 20)], step=0.5)
    sc.note(CH_A_BASS, 36, 546.5, 9.4, 40, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 546.5, 8.9, 38, jt=0, jv=2)
    en.cc_curve(sc, CH_A_BASS, 11, [(546.5, 80), (556.0, 25)], step=0.5)
    en.cc_curve(sc, CH_B_BASS, 11, [(546.5, 80), (555.5, 25)], step=0.5)
    for on, p, v in ((547.5, 36, 92), (548.75, 43, 84), (550.25, 36, 76),
                     (552.0, 43, 66), (554.0, 36, 56), (556.25, 36, 46)):
        sc.note(CH_A_TIMP, p, on, 0.5, v, jt=1, jv=2)
    for on, v in ((547.0, 88), (548.25, 78), (549.75, 68), (551.5, 58),
                  (553.5, 48), (555.75, 38)):
        sc.hit(41, on, v)


def _m7_fault_silence(sc: en.Score) -> None:
    """[560, 564) Nothing.  The fault itself — four beats of scored
    silence at the slowed coda tempo (GAP_WHITELIST covers it)."""


def _m8_coda(sc: en.Score) -> None:
    """[564, 640) Coexistence: both tonic pedals, the choir humming D
    (the one tone both keys share), and the chorale COMPLETE in both
    keys at once — C minor on Block A's strings, F sharp minor on
    Block B's pad, chord for chord.  It dissolves into open fifths,
    and the flute says the last word: C5 rising a quiet minor sixth
    to Ab5.  Unresolved."""
    sc.cc(CH_A_BASS, 11, 66, 564.0)
    sc.cc(CH_B_BASS, 11, 62, 564.0)
    sc.cc(CH_B_PAD, 11, 60, 564.0)
    sc.note(CH_A_BASS, 36, 564.0, 23.9, 30, jt=0, jv=2)
    sc.note(CH_A_BASS, 36, 588.5, 15.4, 26, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 564.5, 23.4, 28, jt=0, jv=2)
    sc.note(CH_B_BASS, 42, 588.5, 13.4, 24, jt=0, jv=2)
    sc.note(CH_CHOR, 50, 566.0, 25.9, 40, jt=2, jv=2)
    sc.note(CH_CHOR, 62, 570.0, 44.9, 38, jt=2, jv=2)
    sc.note(CH_CHOR, 50, 592.5, 22.0, 36, jt=2, jv=2)
    en.vowel_curve(sc, CH_CHOR, [(566.0, 10), (580.0, 45), (600.0, 45),
                                 (614.0, 20)], step=2.0)
    en.cc_curve(sc, CH_CHOR, 11, [(566.0, 55), (592.0, 60),
                                  (614.5, 30)], step=2.0)
    en.cc_curve(sc, CH_A_STR, 11, [(566.0, 55), (580.0, 66),
                                   (592.0, 58), (605.0, 40)], step=2.0)
    en.cc_curve(sc, CH_B_PAD, 11, [(568.0, 58), (580.0, 64),
                                   (592.0, 56), (603.0, 40)], step=2.0)
    material.play_chorale(sc, CH_A_STR, CODA_T0, CODA_ROOT_A,
                          chord_beats=CODA_CHORD_BEATS, vel=58,
                          jt=2, jv=2)
    material.play_chorale(sc, CH_B_PAD, CODA_T0, CODA_ROOT_B,
                          chord_beats=CODA_CHORD_BEATS, vel=52,
                          jt=2, jv=2)
    # the dissolve: open fifths from both worlds, fading
    sc.note(CH_A_STR, 48, 592.5, 13.0, 40, jt=2, jv=2)
    sc.note(CH_A_STR, 55, 592.5, 13.0, 38, jt=2, jv=2)
    sc.note(CH_B_PAD, 54, 592.5, 11.0, 38, jt=2, jv=2)
    sc.note(CH_B_PAD, 61, 592.5, 11.0, 36, jt=2, jv=2)
    sc.note(CH_A_TIMP, 36, 596.0, 0.5, 30, jt=1, jv=2)
    sc.note(CH_A_TIMP, 36, 604.0, 0.5, 26, jt=1, jv=2)
    # the last word: a rising minor sixth, unresolved
    en.cc_curve(sc, CH_A_FLUTE, 11, [(616.0, 55), (621.0, 50),
                                     (632.0, 8)], step=0.5)
    en.cc_curve(sc, CH_A_FLUTE, 1, [(617.0, 0), (620.0, 28),
                                    (631.5, 10)], step=0.5)
    sc.note(CH_A_FLUTE, END_P1, END_T1, 4.5, 34, jt=2, jv=2)
    sc.note(CH_A_FLUTE, END_P2, END_T2, 11.0, 30, jt=0, jv=0)


BUILDERS: list = [_m1_hairline, _m2_block_a, _m3_hymn_cut_i, _m4_block_b,
                  _m5_hymn_cut_ii, _m6_collision, _m7_fault_silence,
                  _m8_coda]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the track is composed to pass them
# ---------------------------------------------------------------------------

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


def _decode_morse(taps: list[tuple[float, float]], unit: float) -> str:
    """Decode (onset, dur) taps back to text via standard Morse timing."""
    inverse = {code: letter for letter, code in material.MORSE_TABLE.items()}
    words: list[str] = []
    letters: list[str] = []
    symbol = ""
    prev_end: float | None = None
    for on, dur in taps:
        if prev_end is not None:
            gap_units = (on - prev_end) / unit
            if gap_units > 5.0:
                letters.append(inverse.get(symbol, "?"))
                symbol = ""
                words.append("".join(letters))
                letters = []
            elif gap_units > 2.0:
                letters.append(inverse.get(symbol, "?"))
                symbol = ""
        symbol += "." if dur < 2.0 * unit else "-"
        prev_end = on + dur
    if symbol:
        letters.append(inverse.get(symbol, "?"))
    if letters:
        words.append("".join(letters))
    return " ".join(words)


def _bar_energies(sc: en.Score) -> list[float]:
    """Per-4-beat-bar sums of note-on velocities, all channels."""
    bars = [0.0] * 160                        # beats [0, 640)
    for ch in list(_ALL_PITCHED) + [9]:
        for on, _du, _p, v in _notes(sc, ch):
            b = int(on // 4.0)
            if 0 <= b < len(bars):
                bars[b] += v
    return bars


def _o_bitonal(sc) -> list[str]:
    """The tectonic plates never mix: A channels stay in C aeolian, B
    channels in F# aeolian, the hymn in D aeolian, and the orchestra-hit
    channel speaks only the two tonic pitch-classes C and F#."""
    fails = []
    worlds = ([(ch, _C_AEO, "C aeolian") for ch in A_CHANNELS]
              + [(ch, _FS_AEO, "F# aeolian") for ch in B_CHANNELS]
              + [(CH_CHOR, _D_AEO, "D aeolian"),
                 (CH_HIT, {0, 6}, "the tonics C/F#")])
    for ch, pcs, name in worlds:
        for on, _du, p, _v in _notes(sc, ch):
            if p % 12 not in pcs:
                fails.append(f"ch{ch} pitch {p} at beat {on:.2f} is "
                             f"outside {name}")
    return fails[:8]


def _grid_fails(sc, ch, spans, cycle, label) -> tuple[list[str], dict]:
    """Shared onset-grid scan: eighth-grid membership mod `cycle`.
    Returns (failures, {(span_t0, cycle_index): [(pos, vel), ...]})."""
    fails: list[str] = []
    cycles: dict[tuple[float, int], list[tuple[float, int]]] = {}
    tol = 3 * _TICK
    for t0, t1 in spans:
        for on, _du, _p, v in _notes(sc, ch):
            if not t0 - tol <= on < t1 - tol:
                continue
            rel = on - t0
            pos = rel % cycle
            grid = round(pos / 0.5) * 0.5
            diff = min(abs(pos - grid), abs(pos - (grid - cycle)))
            if diff > tol:
                fails.append(f"{label}: ch{ch} onset {on:.4f} is off the "
                             f"eighth grid (pos {pos:.4f})")
            c = int((rel + tol) // cycle)
            cycles.setdefault((t0, c), []).append((pos, v))
    return fails, cycles


def _o_b_sevens(sc) -> list[str]:
    """Block B is in 7/8 even though the lane says 4/4: every guitar
    onset in the B spans is on the eighth grid of a 3.5-beat cycle,
    every cycle is present, and the 2+2+3 group starts (positions 0,
    1, 2) are all struck and all louder than every off-group eighth."""
    fails, cycles = _grid_fails(sc, CH_B_GTR, B_SPANS, 3.5, "7/8")
    tol = 3 * _TICK
    for t0, t1 in B_SPANS:
        n_cycles = int(round((t1 - t0) / 3.5))
        for c in range(n_cycles):
            got = cycles.get((t0, c), [])
            accents = [v for pos, v in got
                       if any(abs(pos - g) <= tol for g in (0.0, 1.0, 2.0))]
            plains = [v for pos, v in got
                      if not any(abs(pos - g) <= tol
                                 for g in (0.0, 1.0, 2.0))]
            if len(accents) < 3:
                fails.append(f"7/8 cycle at beat {t0 + 3.5 * c:.1f}: only "
                             f"{len(accents)} of the 2+2+3 group starts")
            elif plains and min(accents) <= max(plains):
                fails.append(f"7/8 cycle at beat {t0 + 3.5 * c:.1f}: group "
                             f"starts not louder ({min(accents)} <= "
                             f"{max(plains)})")
    return fails[:8]


def _o_a_fours(sc) -> list[str]:
    """Block A stays in 4/4: every contrabass onset in the A spans is on
    the eighth grid of a 4-beat bar and every bar strikes its downbeat."""
    fails, cycles = _grid_fails(sc, CH_A_BASS, A_SPANS, 4.0, "4/4")
    tol = 3 * _TICK
    for t0, t1 in A_SPANS:
        for b in range(int(round((t1 - t0) / 4.0))):
            got = cycles.get((t0, b), [])
            if not any(pos <= tol or pos >= 4.0 - tol for pos, _v in got):
                fails.append(f"4/4 bar at beat {t0 + 4.0 * b:.1f} has no "
                             f"downbeat onset")
    return fails[:8]


def _o_hymn_interruptions(sc) -> list[str]:
    """Every pre-coda chorale statement is material.play_chorale
    truncated (k < 8, k strictly increasing: 3, 5, 7), note-for-note
    from material.chorale_pitches(D), and an orchestra hit lands within
    one beat AFTER each truncation — never during the statement.  The
    choir sings nothing before the coda except these statements."""
    fails = []
    want = material.chorale_pitches(HYMN_ROOT)
    chor = _notes(sc, CH_CHOR)
    hits = [on for on, _du, _p, _v in _notes(sc, CH_HIT)]
    tol = 6 * _TICK
    prev_k = 0
    windows = []
    for t0, k, _vel in HYMN_STATEMENTS:
        if not k < 8:
            fails.append(f"statement at {t0:.0f}: k={k} is not truncated")
        if not k > prev_k:
            fails.append(f"statement at {t0:.0f}: k={k} does not exceed "
                         f"the previous statement's {prev_k}")
        prev_k = k
        tc = t0 + k * HYMN_CHORD_BEATS
        windows.append((t0 - 0.2, tc + 0.2))
        got = [x for x in chor if t0 - 0.2 <= x[0] < tc + 0.2]
        if len(got) != 4 * k:
            fails.append(f"statement at {t0:.0f}: {len(got)} choir notes, "
                         f"want {4 * k}")
            continue
        for i in range(k):
            chord = [x for x in got
                     if abs(x[0] - (t0 + i * HYMN_CHORD_BEATS)) <= tol]
            if len(chord) != 4:
                fails.append(f"statement at {t0:.0f} chord {i + 1}: "
                             f"{len(chord)} notes on the grid, want 4")
            elif {p for _on, _du, p, _v in chord} != set(want[i]):
                fails.append(f"statement at {t0:.0f} chord {i + 1} != "
                             f"material.chorale_pitches")
        if not any(abs(h - tc) <= 1.0 for h in hits):
            fails.append(f"statement at {t0:.0f}: no orchestra hit within "
                         f"1 beat of the truncation at {tc:.0f}")
        if any(t0 + 0.2 <= h <= tc - 0.3 for h in hits):
            fails.append(f"statement at {t0:.0f}: an orchestra hit lands "
                         f"INSIDE the statement")
    for on, _du, _p, _v in chor:
        if on < 564.0 and not any(lo <= on < hi for lo, hi in windows):
            fails.append(f"stray pre-coda choir note at beat {on:.2f} "
                         f"(the hymn only speaks in statements)")
    return fails[:8]


def _o_coda_coexistence(sc) -> list[str]:
    """The coda states the chorale COMPLETE in both keys at once:
    all 8 chords of material.chorale_pitches(60) on Block A's strings
    and of material.chorale_pitches(66) on Block B's pad, note-for-note,
    every chord's eight onsets rhythmically aligned in one small band."""
    fails = []
    want_a = material.chorale_pitches(CODA_ROOT_A)
    want_b = material.chorale_pitches(CODA_ROOT_B)
    end = CODA_T0 + 8 * CODA_CHORD_BEATS
    str_notes = [x for x in _notes(sc, CH_A_STR)
                 if CODA_T0 - 0.2 <= x[0] < end - 0.2]
    pad_notes = [x for x in _notes(sc, CH_B_PAD)
                 if CODA_T0 - 0.2 <= x[0] < end - 0.2]
    if len(str_notes) != 32:
        fails.append(f"strings carry {len(str_notes)} coda notes, want 32 "
                     f"(8 chords x 4: COMPLETE)")
    if len(pad_notes) != 32:
        fails.append(f"pad carries {len(pad_notes)} coda notes, want 32 "
                     f"(8 chords x 4: COMPLETE)")
    if fails:
        return fails
    tol = 6 * _TICK
    for i in range(8):
        t = CODA_T0 + i * CODA_CHORD_BEATS
        ca = [x for x in str_notes if abs(x[0] - t) <= tol]
        cb = [x for x in pad_notes if abs(x[0] - t) <= tol]
        if {p for _o, _d, p, _v in ca} != set(want_a[i]):
            fails.append(f"coda chord {i + 1} (C minor) != "
                         f"material.chorale_pitches(60)")
        if {p for _o, _d, p, _v in cb} != set(want_b[i]):
            fails.append(f"coda chord {i + 1} (F# minor) != "
                         f"material.chorale_pitches(66)")
        ons = [x[0] for x in ca + cb]
        if ons and max(ons) - min(ons) > 10 * _TICK:
            fails.append(f"coda chord {i + 1}: the two keys drift "
                         f"{(max(ons) - min(ons)) / _TICK:.0f} ticks apart")
    return fails[:8]


def _o_morse(sc) -> list[str]:
    """The ch9 key-76 lane is exactly four verbatim passes of
    material.morse_rhythm(HOLD THE LINE), each decoding back to the
    text with standard dit/dah timing."""
    fails = []
    taps = [x for x in _notes(sc, 9) if x[2] == TICKER_KEY]
    want = material.morse_rhythm(material.MORSE_T4, TICKER_UNIT)
    if len(taps) != len(TICKER_PASSES) * len(want):
        return [f"ticker lane has {len(taps)} taps, want "
                f"{len(TICKER_PASSES)} x {len(want)}"]
    for pi, (t0, _vel) in enumerate(TICKER_PASSES):
        seg = taps[pi * len(want):(pi + 1) * len(want)]
        for (on, du, _p, _v), (won, wdu) in zip(seg, want):
            if abs(on - (t0 + won)) > 2 * _TICK:
                fails.append(f"pass {pi + 1}: tap at {on:.4f} != "
                             f"{t0 + won:.4f}")
            if abs(du - wdu) > 3 * _TICK:
                fails.append(f"pass {pi + 1}: dur {du:.3f} at {on:.2f} "
                             f"!= {wdu:.3f}")
        decoded = _decode_morse([(on, du) for on, du, _p, _v in seg],
                                TICKER_UNIT)
        if decoded != material.MORSE_T4:
            fails.append(f"pass {pi + 1} decodes to {decoded!r}, want "
                         f"{material.MORSE_T4!r}")
    return fails[:8]


def _o_doomscroll(sc) -> list[str]:
    """The doomscroll: exactly 221 notes whose inter-onset intervals
    strictly decrease across the whole span (1.5 beats down to ~0.13),
    while the pitch fragments downward and the velocity climbs."""
    fails = []
    notes = _notes(sc, CH_DOOM)
    if len(notes) != DOOM_COUNT:
        return [f"doomscroll has {len(notes)} notes, want {DOOM_COUNT}"]
    ons = [on for on, _du, _p, _v in notes]
    iois = [b - a for a, b in zip(ons, ons[1:])]
    for i, (a, b) in enumerate(zip(iois, iois[1:])):
        if not b < a - 1e-9:
            fails.append(f"IOI {i + 1}->{i + 2} does not strictly "
                         f"decrease ({a:.4f} -> {b:.4f})")
    if abs(iois[0] - DOOM_IOI_HI / en.PPQ) > 2 * _TICK:
        fails.append(f"first IOI {iois[0]:.4f}, want "
                     f"{DOOM_IOI_HI / en.PPQ:.4f}")
    if iois[-1] > 0.14:
        fails.append(f"last IOI {iois[-1]:.4f} never reaches the blur")
    if not DOOM_T0 - 0.05 <= ons[0] and ons[-1] < 530.0:
        fails.append(f"doomscroll span [{ons[0]:.1f}, {ons[-1]:.1f}] "
                     f"escapes [{DOOM_T0}, 530)")
    first_p = [p for _o, _d, p, _v in notes[:30]]
    last_p = [p for _o, _d, p, _v in notes[-30:]]
    if sum(last_p) / 30 >= sum(first_p) / 30 - 4:
        fails.append("the doomscroll pitch does not fragment downward")
    first_v = [v for _o, _d, _p, v in notes[:30]]
    last_v = [v for _o, _d, _p, v in notes[-30:]]
    if sum(last_v) / 30 < sum(first_v) / 30 + 20:
        fails.append("the doomscroll does not build (vel rise < 20)")
    return fails[:8]


def _o_ending(sc) -> list[str]:
    """The piece ends on a quiet rising minor sixth, unresolved: the
    final two melodic events are exactly +8 semitones apart, both at
    whisper velocity, alone at the end, and the final bar's energy is
    at most 0.15x the peak bar's."""
    fails = []
    melodic = []
    for ch in _ALL_PITCHED:
        for on, du, p, v in _notes(sc, ch):
            melodic.append((on, du, p, v, ch))
    melodic.sort()
    if len(melodic) < 3:
        return ["the piece is nearly empty"]
    (_on3, _d3, _p3, _v3, _c3) = melodic[-3]
    on1, _d1, p1, v1, _c1 = melodic[-2]
    on2, _d2, p2, v2, _c2 = melodic[-1]
    if p2 - p1 != 8:
        fails.append(f"final interval {p2 - p1:+d} semitones, want +8 "
                     f"(a rising minor sixth)")
    if v1 > 40 or v2 > 40:
        fails.append(f"final pair velocities {v1}/{v2} are no whisper "
                     f"(cap 40)")
    if on2 < 612.0:
        fails.append(f"final event at beat {on2:.1f} is not the ending")
    if _on3 > on1 - 4.0:
        fails.append(f"a note at beat {_on3:.2f} crowds the final pair "
                     f"(the sixth must stand alone)")
    bars = _bar_energies(sc)
    peak = max(bars)
    fbar = int(on2 // 4.0)
    if bars[fbar] > FINAL_ENERGY_RATIO * peak:
        fails.append(f"final bar energy {bars[fbar]:.0f} exceeds "
                     f"{FINAL_ENERGY_RATIO} x peak {peak:.0f}")
    return fails


def _o_tectonic_arc(sc) -> list[str]:
    """The dramatic shape as per-bar velocity-sum inequalities: the
    peak bar lives in the collision; the collision out-grinds both
    blocks; each hymn window is under half its neighbouring block; the
    intro is under Block A; the coda is under 0.3x the collision."""
    fails = []
    bars = _bar_energies(sc)

    def mean(b0: float, b1: float) -> float:
        seg = bars[int(b0 // 4):int(b1 // 4)]
        return sum(seg) / len(seg)

    peak_bar = max(range(len(bars)), key=lambda i: bars[i]) * 4.0
    if not 336.0 <= peak_bar < 560.0:
        fails.append(f"peak bar at beat {peak_bar:.0f} is outside the "
                     f"collision [336, 560)")
    m_a, m_b = mean(56, 168), mean(196, 308)
    m_coll = mean(336, 560)
    if not (m_coll > m_a and m_coll > m_b):
        fails.append(f"collision mean {m_coll:.0f} does not exceed both "
                     f"blocks ({m_a:.0f}, {m_b:.0f})")
    if not mean(168, 196) < 0.5 * m_a:
        fails.append(f"hymn i mean {mean(168, 196):.0f} not under half "
                     f"of Block A {m_a:.0f}")
    if not mean(308, 336) < 0.5 * m_b:
        fails.append(f"hymn ii mean {mean(308, 336):.0f} not under half "
                     f"of Block B {m_b:.0f}")
    if not mean(0, 56) < m_a:
        fails.append(f"the intro out-grinds Block A")
    if not mean(564, 640) < 0.3 * m_coll:
        fails.append(f"coda mean {mean(564, 640):.0f} not under 0.3 x "
                     f"collision {m_coll:.0f}")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("bitonal_blocks", _o_bitonal(sc)),
        ("b_block_sevens", _o_b_sevens(sc)),
        ("a_block_fours", _o_a_fours(sc)),
        ("hymn_interruptions", _o_hymn_interruptions(sc)),
        ("coda_coexistence", _o_coda_coexistence(sc)),
        ("morse_hold_the_line", _o_morse(sc)),
        ("doomscroll_accelerando", _o_doomscroll(sc)),
        ("ending_rising_sixth", _o_ending(sc)),
        ("tectonic_arc", _o_tectonic_arc(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/04 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The headline claims, held against the RENDER in dB:
    the loudest 4-beat window lives in the collision; each orchestra-hit
    shock is at least 3 dB louder than the hymn it cuts; the fault
    silence sits >= 25 dB under the peak; and the final bars sit at
    least 16.5 dB under the peak (the 0.15x amplitude claim)."""
    windows: list[tuple[float, float]] = []
    b = 0.0
    while b < 632.0:
        i0, i1 = ctx.bar_window(b, b + 4.0)
        windows.append((b, ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))))
        b += 4.0
    peak_b, peak_db = max(windows, key=lambda w: w[1])

    peak_fails = []
    if not 336.0 <= peak_b < 560.0:
        peak_fails.append(f"loudest window at beat {peak_b:.0f} "
                          f"({peak_db:.1f} dB) is outside the collision")

    shock_fails = []
    for t0, k, _vel in HYMN_STATEMENTS:
        tc = t0 + k * HYMN_CHORD_BEATS
        i0, i1 = ctx.bar_window(tc - 4.0, tc)
        pre = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
        i0, i1 = ctx.bar_window(tc + 0.5, tc + 2.5)
        post = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
        if post < pre + 3.0:
            shock_fails.append(f"hit after beat {tc:.0f}: shock "
                               f"{post:.1f} dB vs hymn {pre:.1f} dB "
                               f"(want +3)")

    i0, i1 = ctx.bar_window(560.5, 563.5)
    fault = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
    silence_fails = []
    if fault > peak_db - 25.0:
        silence_fails.append(f"fault silence {fault:.1f} dB is within "
                             f"25 dB of the peak {peak_db:.1f} dB")

    i0, i1 = ctx.bar_window(620.0, 628.0)
    final = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
    sixth_fails = []
    if final > peak_db - 16.5:
        sixth_fails.append(f"the final sixth {final:.1f} dB is louder "
                           f"than 0.15x the peak {peak_db:.1f} dB")

    return [
        ("audio_collision_peak", peak_fails),
        ("audio_hymn_shock", shock_fails),
        ("audio_fault_silence", silence_fails),
        ("audio_final_sixth_quiet", sixth_fails),
    ]
