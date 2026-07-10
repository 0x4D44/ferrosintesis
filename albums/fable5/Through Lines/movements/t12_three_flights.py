"""t12_three_flights — Track 12 "Three Flights Up" of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T12: the album's only
straight-ahead swing — night jazz in F at 92 bpm, brushes, a walk-up
tune whose "three flights of stairs" motif climbs three times in the
head, the way it climbs three flights to a small apartment above a bar.

Every headline claim below is a falsifiable oracle (oracles() was
written BEFORE the music; the track is composed to pass it):

 * A rubato SOLO-PIANO intro sculpted with the tempo map: twelve tempo
   events breathe through the intro's four phrases; the map then locks
   to 92 at the head downbeat and never moves again except the single
   shout-chorus lift to 95 (`rubato_intro`: >= 6 tempo events inside
   [0, 32), only {(32, 92), (288, 95)} at or after 32, bpm spread
   >= 12; nothing but the piano sounds before beat 32).
 * The kit is the ferrosintesis v0.11 BRUSH kit, selected the honest
   way — a channel-10 program change to 40 at beat 0 authored in
   PART.PROGRAM_CHANGES (`brush_kit`: ch9 program lane == [(0, 40)]).
 * The ride lane swings at 2:1 (`swing_ratio`: every measured
   beat/off-beat/beat inter-onset triple on ride 51 has ratio in
   [1.7, 2.4], mean in [1.85, 2.15], >= 60 triples measured).
 * The bass WALKS: in every documented walking bar (WALK_BARS — the
   per-bar root list required by the design, built from the form
   tables) it plays exactly four quarters, beat 1 is the documented
   root, and the beat-4 note approaches within +-2 semitones of the
   next bar's documented root (`walking_bass`).
 * The head is a DARKENED trumpet.  Design choice, documented: GM 59
   (muted trumpet) rather than 56+CC74, because the mute is the
   character — but CC74 is ALSO authored low (44) to close the filter
   further (`darkened_trumpet`: only program 59 on ch2; CC74 authored
   and always <= 60).
 * Trading fours, strict (`trading_fours`): six 4-bar cells marked
   "Piano fours"/"Guitar fours"/"Drum fours" (x2) alternate P G D P G D;
   piano sounds only in P cells, guitar only in G cells, the bass and
   the time drop out of D cells (drums solo alone), the trumpet is
   tacet throughout.
 * ONE shout-chorus key lift (`shout_key_lift`): key signature grid is
   exactly F major then G major at beat 288, the G-form bar roots are
   the F-form roots + 2, and the one post-intro tempo event is the
   shout lift 92 -> 95.
 * Head out == head in transposed (`head_out_fidelity`): the trumpet's
   45 head-out notes match the 45 head-in notes note-for-note, +2
   semitones, same relative onsets and durations.
 * Tag ending x3 (`tag_ending_x3`): the 7-note 2-bar cadence figure
   TAG_FIG occurs exactly three times in the whole trumpet lane, at
   beats 384/392/400, and the only trumpet event after it is the final
   held G5.
 * The FABLE cell slips into the last two bars of the piano solo in 2x
   augmentation, recomputed from material.play_cell — the album's
   signature overheard in a solo (`fable_quote`, silent L included).
 * The dramatic shape as numbers: per-beat velocity density rises
   intro < head-in < shout chorus, shout > 1.2x head
   (`dynamic_arc_midi`); audio_checks() holds the RENDER to the same
   contour in dB (`audio_night_arc`: intro <= head-in - 2 dB, shout
   >= head-in + 2 dB, shout is the loudest section window).

Deviation from a literal reading of the walking rule, documented: the
tag (384-416) is played in 2-feel (half-note roots, the classic ending
gear-change), so its bars are not in WALK_BARS and the walking oracle
does not apply there.  Everywhere the band swings in 4, the bass walks.

Movements (4/4 throughout; F major, one flat, until the lift):
    i.    Stairwell (rubato)   beats   0-32   solo piano, tempo-map rubato
    ii.   Head In              beats  32-96   muted trumpet, 16-bar form
    iii.  Piano Solo           beats  96-160  16 bars + the FABLE quote
    iv.   Guitar Solo          beats 160-192  8 bars (form bars 9-16)
    v.    Trading Fours        beats 192-288  P G D P G D
    vi.   Shout Chorus         beats 288-320  +2 to G, 95 bpm, riff x3
    vii.  Head Out             beats 320-384  the head, +2
    viii. Tag x3               beats 384-416  cadence figure x3, last chord
"""

from __future__ import annotations

import random

import conductor
import engine as en
import material

NUMBER = 12
TITLE = 'Three Flights Up'
FILE = '12 - Three Flights Up.mid'
SEED = 20260912

COMMENT = ("Track 12: night jazz in F. Rubato solo piano up the stairs, "
           "brushes at 2:1, a walking bass with documented roots, a muted "
           "trumpet head, trading fours, one key lift, tag ending x3.")

# ---------------------------------------------------------------------------
# Channels, grid constants, form tables
# ---------------------------------------------------------------------------

CH_PNO = 0        # acoustic grand (GM 0) — transient, panned left
CH_BASS = 1       # acoustic bass (GM 32) — low lane, centred
CH_TPT = 2        # muted trumpet (GM 59) — sustained lead, centred
CH_GTR = 3        # jazz guitar (GM 26) — transient, panned right
CH_DRUMS = 9      # brush kit (channel-10 program 40)

SWING = 2.0 / 3.0             # the 2:1 off-beat placement

HEADIN_T0 = 32.0              # the head downbeat: the map locks to time here
PSOLO_T0 = 96.0
GSOLO_T0 = 160.0
TRADE_T0 = 192.0
SHOUT_T0 = 288.0              # the one key lift (+2) and tempo lift
HEADOUT_T0 = 320.0
TAG_T0 = 384.0
END_T = 416.0

SWING_BPM = 92.0
SHOUT_BPM = 95.0

TRADE_PATTERN = "PGDPGD"      # six 4-bar cells
CELL_BEATS = 16.0

# The 16-bar form in F: (bass root pitch, chord quality), one chord per bar.
# This IS the documented per-bar root list the walking-bass oracle reads.
F_FORM: list[tuple[int, str]] = [
    (41, "maj6"), (38, "dom7"), (43, "min7"), (48, "dom7"),   # F  D7 Gm7 C7
    (41, "maj6"), (46, "dom7"), (45, "min7"), (38, "dom7"),   # F  Bb7 Am7 D7
    (43, "min7"), (48, "dom7"), (45, "min7"), (38, "dom7"),   # Gm7 C7 Am7 D7
    (43, "min7"), (48, "dom7"), (41, "maj6"), (48, "dom7"),   # Gm7 C7 F  C7
]
G_FORM: list[tuple[int, str]] = [(r + 2, q) for r, q in F_FORM]   # the lift

# Tag bars (G, 2-feel): |G6 E7|Am7 D7| x3 then |G6|G6|.  Timeline roots
# name each 4-beat bar's first chord (used as walk approach targets only).
TAG_TL: list[tuple[int, str]] = ([(43, "maj6"), (45, "min7")] * 3
                                 + [(43, "maj6"), (43, "maj6")])

QUAL_TONES = {"maj6": (0, 4, 7, 9), "dom7": (0, 4, 7, 10),
              "min7": (0, 3, 7, 10)}
QUAL_SCALE = {"maj6": (0, 2, 4, 5, 7, 9, 11),
              "dom7": (0, 2, 4, 5, 7, 9, 10),
              "min7": (0, 2, 3, 5, 7, 9, 10)}


def _build_timeline() -> list[tuple[float, int, str]]:
    """(bar_start_beat, root, quality) for every 4-beat bar from 32 to 416."""
    bars: list[tuple[float, int, str]] = []
    for i, (r, q) in enumerate(F_FORM):
        bars.append((HEADIN_T0 + 4.0 * i, r, q))
    for i, (r, q) in enumerate(F_FORM):
        bars.append((PSOLO_T0 + 4.0 * i, r, q))
    for i, (r, q) in enumerate(F_FORM[8:]):
        bars.append((GSOLO_T0 + 4.0 * i, r, q))
    for k in range(24):
        r, q = F_FORM[k % 16]
        bars.append((TRADE_T0 + 4.0 * k, r, q))
    for i, (r, q) in enumerate(G_FORM[:8]):
        bars.append((SHOUT_T0 + 4.0 * i, r, q))
    for i, (r, q) in enumerate(G_FORM):
        bars.append((HEADOUT_T0 + 4.0 * i, r, q))
    for i, (r, q) in enumerate(TAG_TL):
        bars.append((TAG_T0 + 4.0 * i, r, q))
    return bars


BAR_TIMELINE = _build_timeline()


def _trade_cell(beat: float) -> str | None:
    if TRADE_T0 <= beat < SHOUT_T0:
        return TRADE_PATTERN[int((beat - TRADE_T0) // CELL_BEATS)]
    return None


def _is_walked(beat: float) -> bool:
    """Bass walks everywhere in time EXCEPT drum-fours cells and the
    2-feel tag (the documented deviation)."""
    if beat < HEADIN_T0 or beat >= TAG_T0:
        return False
    return _trade_cell(beat) != "D"


# The documented walking bars: (bar_beat, root, quality, next bar's root).
WALK_BARS: list[tuple[float, int, str, int]] = [
    (t, r, q, BAR_TIMELINE[i + 1][1])
    for i, (t, r, q) in enumerate(BAR_TIMELINE) if _is_walked(t)]

# ---------------------------------------------------------------------------
# The head (45 notes, F).  (onset_in_head, dur, pitch, vel); off-beat
# eighths sit at +0.667 (= 2:1 swing).  The "three flights" motif is the
# ascending three-note figure of bars 1-3, each flight one landing higher.
# ---------------------------------------------------------------------------

HEAD: list[tuple[float, float, int, int]] = [
    # bar 1 (F6) — flight one
    (0.0, 0.6, 65, 74), (0.667, 0.3, 67, 70), (1.0, 1.9, 69, 78),
    # bar 2 (D7) — flight two
    (4.0, 0.6, 69, 74), (4.667, 0.3, 72, 72), (5.0, 1.9, 74, 80),
    # bar 3 (Gm7) — flight three, cresting
    (8.0, 0.6, 72, 76), (8.667, 0.3, 74, 74), (9.0, 1.55, 77, 84),
    (10.667, 0.3, 76, 70), (11.0, 0.95, 74, 72),
    # bar 4 (C7) — exhale on the landing
    (12.0, 1.9, 76, 74),
    # bar 5 (F6) — looking back down the well
    (16.0, 0.6, 77, 78), (16.667, 0.3, 76, 72), (17.0, 0.95, 74, 74),
    (18.0, 1.4, 72, 70),
    # bar 6 (Bb7)
    (20.0, 0.6, 70, 72), (20.667, 0.3, 72, 70), (21.0, 1.9, 74, 78),
    # bar 7 (Am7)
    (24.0, 0.6, 76, 74), (24.667, 0.3, 74, 70), (25.0, 1.9, 72, 74),
    # bar 8 (D7)
    (28.0, 1.4, 74, 76), (30.0, 0.6, 72, 70), (30.667, 0.3, 69, 66),
    # bar 9 (Gm7)
    (32.0, 1.9, 67, 72), (34.0, 0.6, 70, 70), (34.667, 0.3, 72, 68),
    # bar 10 (C7)
    (36.0, 0.6, 74, 74), (36.667, 0.3, 72, 70), (37.0, 1.9, 70, 74),
    # bar 11 (Am7) — the flight motif once more, higher
    (40.0, 0.6, 69, 72), (40.667, 0.3, 72, 72), (41.0, 1.9, 76, 80),
    # bar 12 (D7)
    (44.0, 0.6, 74, 74), (44.667, 0.3, 72, 70), (45.0, 0.95, 69, 70),
    (46.0, 1.4, 66, 68),
    # bar 13 (Gm7)
    (48.0, 1.9, 67, 72), (50.0, 0.6, 65, 66), (50.667, 0.3, 67, 66),
    # bar 14 (C7)
    (52.0, 0.6, 69, 70), (52.667, 0.3, 67, 66), (53.0, 1.9, 64, 70),
    # bar 15 (F6) — home; bar 16 (C7) is the piano's turnaround
    (56.0, 3.0, 65, 74),
]

# The 2-bar tag cadence figure (in G, over |G6 E7|Am7 D7|), 7 notes.
TAG_FIG: list[tuple[float, float, int, int]] = [
    (0.0, 1.0, 79, 84), (1.0, 0.6, 76, 74), (1.667, 0.3, 74, 70),
    (2.0, 1.5, 71, 76), (4.0, 0.6, 69, 70), (4.667, 0.3, 71, 72),
    (5.0, 1.9, 74, 80),
]
TAG_FINAL_PITCH = 79          # the held G5 over the last chord
TAG_FINAL_T0 = 408.0

# The 2-bar shout riff (in G, bluesy), stated x3 at 288/296/304.
SHOUT_RIFF: list[tuple[float, float, int, int]] = [
    (0.0, 0.6, 74, 98), (0.667, 0.3, 77, 94), (1.0, 1.5, 79, 104),
    (2.667, 0.3, 79, 92), (3.0, 0.9, 81, 102), (4.0, 0.6, 79, 98),
    (4.667, 0.3, 77, 94), (5.0, 1.4, 74, 100), (6.667, 0.3, 72, 90),
    (7.0, 0.9, 74, 98),
]
SHOUT_HITS = (0.0, 1.0, 2.667, 4.0, 5.0, 7.0)   # band stabs per 2-bar riff

# The FABLE quote: last two bars of the piano solo, 2x augmentation.
FABLE_T0 = 152.0
FABLE_ROOT = 65               # F4
FABLE_STRETCH = 2.0

TPT_CC74 = 44                 # the extra darkening on the muted trumpet

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("i. Stairwell (rubato)", 0.0, HEADIN_T0),
        ("ii. Head In", HEADIN_T0, PSOLO_T0),
        ("iii. Piano Solo", PSOLO_T0, GSOLO_T0),
        ("iv. Guitar Solo", GSOLO_T0, TRADE_T0),
        ("v. Trading Fours", TRADE_T0, SHOUT_T0),
        ("vi. Shout Chorus", SHOUT_T0, HEADOUT_T0),
        ("vii. Head Out", HEADOUT_T0, TAG_T0),
        ("viii. Tag x3", TAG_T0, END_T),
    ],
    # The rubato: twelve breathing events through the intro's four
    # phrases, the arrival at 92 ON the head downbeat (the last gesture
    # of the intro's sculpting), then one lift for the shout chorus.
    tempo_map=[
        (0.0, 58.0), (3.0, 70.0), (6.0, 56.0),
        (8.0, 62.0), (11.0, 76.0), (14.0, 58.0),
        (16.0, 68.0), (19.0, 84.0), (22.0, 62.0),
        (24.0, 60.0), (27.0, 72.0), (30.0, 80.0),
        (HEADIN_T0, SWING_BPM), (SHOUT_T0, SHOUT_BPM),
    ],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 0), (SHOUT_T0, 1, 0)],      # F major -> G major
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_PNO, "piano", 0, 100, 52, 42),
        (CH_BASS, "upright bass", 32, 105, 64, 28),
        (CH_TPT, "muted trumpet", 59, 96, 64, 52),
        (CH_GTR, "jazz guitar", 26, 88, 76, 40),
        (CH_DRUMS, "brush kit", 0, 100, 64, 44),
    ],
    program_changes=[(CH_DRUMS, 0.0, 40)],          # the BRUSH kit select
    extra_markers=[
        (TRADE_T0, "Piano fours"),
        (TRADE_T0 + 16.0, "Guitar fours"),
        (TRADE_T0 + 32.0, "Drum fours"),
        (TRADE_T0 + 48.0, "Piano fours 2"),
        (TRADE_T0 + 64.0, "Guitar fours 2"),
        (TRADE_T0 + 80.0, "Drum fours 2"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {0, 26, 32, 59}
CENTERED_CHANNELS: set[int] = {CH_BASS, CH_TPT, CH_DRUMS}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_PNO: (36, 96),
    CH_BASS: (36, 60),
    CH_TPT: (55, 84),
    CH_GTR: (43, 86),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (270.0, 284.0)   # ~4:37 written file
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

_TICK = 1.0 / en.PPQ


# ---------------------------------------------------------------------------
# Shared texture generators
# ---------------------------------------------------------------------------

def _scale_pcs(root: int, qual: str) -> set[int]:
    return {(root + o) % 12 for o in QUAL_SCALE[qual]}


def _step(p: int, pcs: set[int], dirn: int) -> int:
    q = p + dirn
    while q % 12 not in pcs:
        q += dirn
    return q


def _play_head(sc: en.Score, t0: float, shift: int, vel_add: int) -> None:
    """The head, recomputed from HEAD — head-out is exactly this, +2."""
    for on, du, p, v in HEAD:
        sc.note(CH_TPT, p + shift, t0 + on, du, min(127, v + vel_add),
                jt=2, jv=2)


def _bars_between(lo: float, hi: float) -> list[tuple[float, int, str]]:
    return [(t, r, q) for t, r, q in BAR_TIMELINE if lo - 1e-6 <= t < hi]


def _walk(sc: en.Score, rng: random.Random, lo: float, hi: float) -> None:
    """Quarter-note walking bass over WALK_BARS in [lo, hi): beat 1 the
    documented root, beats 2-3 chord tones, beat 4 a +-1/2-semitone
    approach to the next documented root."""
    for t, root, qual, nxt in WALK_BARS:
        if not lo - 1e-6 <= t < hi:
            continue
        approach = rng.choice((nxt - 1, nxt + 1, nxt - 1, nxt + 1,
                               nxt - 2, nxt + 2))
        tones = [root + o for o in QUAL_TONES[qual]] + [root + 12]
        tones = [p for p in tones if 36 <= p <= 59]
        c2 = [p for p in tones if p != root and abs(p - root) <= 7]
        b2 = rng.choice(c2) if c2 else root + 7
        c3 = [p for p in tones + [approach - 1, approach + 1,
                                  approach - 2, approach + 2]
              if 36 <= p <= 59 and p != approach and abs(p - approach) <= 5]
        b3 = rng.choice(c3) if c3 else max(36, min(59, approach + 2))
        for k, p in enumerate((root, b2, b3, approach)):
            vel = 60 + rng.randint(-3, 4) + (4 if k == 0 else 0)
            sc.note(CH_BASS, p, t + k, 0.92, vel, jt=3, jv=2)


def _swing_time(sc: en.Score, rng: random.Random, t0: float, n_bars: int,
                ride_vel: int = 52, kick_vel: int = 30, hat_vel: int = 36,
                tap_prob: float = 0.3, tap_vel: int = 40,
                swirl_prob: float = 0.0, backbeat_vel: int = 0) -> None:
    """Brush time: ride 51 in the classic swung pattern (off-beats at
    exactly +2/3 — the swing_ratio oracle measures THIS lane), pedal hat
    on 2 and 4, feathered kick, optional brush-tap comping and swirls."""
    for b in range(n_bars):
        bt = t0 + 4.0 * b
        for rel, acc in ((0.0, 0), (1.0, 5), (1.0 + SWING, -6),
                         (2.0, 0), (3.0, 5), (3.0 + SWING, -6)):
            sc.hit(51, bt + rel, max(1, ride_vel + acc + rng.randint(-2, 2)),
                   jt=2, jv=3)
        for rel in (1.0, 3.0):
            sc.hit(44, bt + rel, hat_vel + rng.randint(-2, 2), jt=3, jv=3)
            if backbeat_vel:
                sc.hit(38, bt + rel, backbeat_vel + rng.randint(-3, 3),
                       jt=3, jv=3)
        for rel in (0.0, 2.0):
            sc.hit(36, bt + rel, kick_vel + rng.randint(-3, 3), jt=3, jv=3)
        if rng.random() < tap_prob:
            rel = rng.choice((1.0 + SWING, 2.0 + SWING, 3.0 + SWING))
            sc.hit(38, bt + rel, tap_vel + rng.randint(-3, 5), jt=3, jv=3)
        if rng.random() < swirl_prob:
            sc.note(CH_DRUMS, 40, bt + rng.choice((0.0, 2.0)), 1.85,
                    38 + rng.randint(-2, 4), jt=3, jv=3)


def _drum_fill_cell(sc: en.Score, rng: random.Random, t: float) -> None:
    """One 4-bar drum-fours cell: brushes alone.  A guaranteed kick/hat
    skeleton keeps the lane gap-free; swung tap/tom figures build across
    the four bars to a crest on beat 4 of bar 4."""
    for bar in range(4):
        bt = t + 4.0 * bar
        for rel in (0.0, 2.0):
            sc.hit(36, bt + rel, 30 + 5 * bar + rng.randint(-3, 3),
                   jt=3, jv=3)
        for rel in (1.0, 3.0):
            sc.hit(44, bt + rel, 36 + 3 * bar + rng.randint(-2, 2),
                   jt=3, jv=3)
        for q in range(4):
            for off, prob in ((0.0, 0.8), (SWING, 0.6)):
                if rng.random() < prob:
                    drum = rng.choice((38, 38, 40, 41, 43, 45, 47, 48, 50))
                    vel = min(96, 46 + 5 * bar + rng.randint(-4, 10))
                    sc.hit(drum, bt + q + off, vel, jt=3, jv=4)
    sc.hit(49, t + 15.0, 58, jt=2, jv=3)


def _comp_piano(sc: en.Score, rng: random.Random,
                bars: list[tuple[float, int, str]], vel: int,
                sparse: bool = False) -> None:
    """Rootless comping: voice-led 3-note colour voicings (3rd/7th + a
    colour tone) placed on swung Charleston-family patterns."""
    patterns = ([((0.0, 1.8),), ((1.0 + SWING, 1.5),), ((2.0, 1.6),)]
                if sparse else
                [((0.0, 1.5), (1.0 + SWING, 1.0)),
                 ((1.0 + SWING, 1.2), (3.0, 0.9)),
                 ((0.0 + SWING, 1.0), (2.0 + SWING, 1.1)),
                 ((0.0, 0.9), (2.0, 1.3)),
                 ((1.0, 1.2), (3.0 + SWING, 0.5))])
    colours = {"maj6": (4, 9, 2), "dom7": (4, 10, 2), "min7": (3, 10, 5)}
    prev = None
    for t, root, qual in bars:
        pcs = [root + o for o in colours[qual]]
        prev = en.voice_lead(pcs, prev, 3, 57, 74)
        for pos, du in rng.choice(patterns):
            for p in prev:
                sc.note(CH_PNO, p, t + pos, du, vel + rng.randint(-4, 4),
                        jt=3, jv=3)


def _comp_guitar(sc: en.Score, rng: random.Random,
                 bars: list[tuple[float, int, str]], vel: int) -> None:
    """Four-to-the-bar shell voicings (root/3rd/7th), short and even."""
    prev = None
    for t, root, qual in bars:
        pcs = [root, root + QUAL_TONES[qual][1], root + QUAL_TONES[qual][3]]
        prev = en.voice_lead(pcs, prev, 3, 50, 64)
        for q in range(4):
            v = vel + (4 if q in (1, 3) else 0) + rng.randint(-2, 2)
            for p in prev:
                sc.note(CH_GTR, p, t + q, 0.55, v, jt=3, jv=2)


def _solo_line(sc: en.Score, ch: int, rng: random.Random,
               bars: list[tuple[float, int, str]], lo: int, hi: int,
               vel_lo: int, vel_hi: int) -> None:
    """A swung-eighth solo line: stepwise chord-scale motion with
    momentum, phrases of 6-12 notes separated by breathing rests."""
    slots: list[tuple[float, bool, int, str]] = []
    for t, root, qual in bars:
        for q in range(4):
            slots.append((t + q, True, root, qual))
            slots.append((t + q + SWING, False, root, qual))
    i = rng.randint(1, 3)
    cur: int | None = None
    dirn = 1
    while i < len(slots):
        length = min(rng.randint(6, 12), len(slots) - i)
        for k in range(length):
            beat, onb, root, qual = slots[i]
            if cur is None:
                centre = (lo + hi) // 2 + rng.randint(-4, 4)
                cand = [p for p in range(lo, hi + 1)
                        if (p - root) % 12 in QUAL_TONES[qual]]
                cur = min(cand, key=lambda p: abs(p - centre))
            else:
                if rng.random() < 0.3:
                    dirn = -dirn
                steps = 2 if rng.random() < 0.15 else 1
                nxt = cur
                for _ in range(steps):
                    nxt = _step(nxt, _scale_pcs(root, qual), dirn)
                if not lo <= nxt <= hi:
                    dirn = -dirn
                    nxt = _step(cur, _scale_pcs(root, qual), dirn)
                cur = nxt
            last = k == length - 1
            dur = rng.choice((1.1, 1.4, 1.8)) if last \
                else (0.55 if onb else 0.32)
            vel = (rng.randint(vel_lo, vel_hi) + (0 if onb else -4)
                   + (4 if last else 0))
            sc.note(ch, cur, beat, dur, vel, jt=3, jv=2)
            i += 1
        i += rng.randint(2, 5)


# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------

def _m1_stairwell(sc: en.Score) -> None:
    """[0, 32) Solo piano, rubato — four 8-beat phrases (F, Dm7,
    Gm7->Bb, C7) climbing the "three flights" figure while the tempo
    map breathes around them.  Nothing else sounds before beat 32."""
    sc.cc(CH_TPT, 74, TPT_CC74, 0.0)          # darken the mute before entry
    sc.cc(CH_TPT, 1, 16, 0.0)                 # a breath of vibrato, ready
    for t0, t1 in ((0.0, 7.8), (8.0, 15.8), (16.0, 23.8), (24.0, 31.6)):
        en.sustain(sc, CH_PNO, t0, t1)
    lh = [  # rolled tenths and shells under each phrase
        (41, 0.0, 3.9, 52), (48, 0.15, 3.75, 48),
        (45, 4.0, 3.9, 50), (53, 4.15, 3.75, 46),
        (38, 8.0, 3.9, 52), (48, 8.15, 3.75, 46),
        (45, 12.0, 3.9, 48), (50, 12.15, 3.75, 44),
        (43, 16.0, 3.9, 52), (53, 16.15, 3.75, 46),
        (46, 20.0, 3.9, 52), (58, 20.15, 3.75, 46),
        (36, 24.0, 3.9, 50), (48, 24.15, 3.75, 46),
        (36, 28.0, 3.85, 50), (46, 28.15, 1.8, 44), (55, 28.3, 3.6, 44),
    ]
    rh = [  # flights one, two, three — then the gather into time
        (65, 1.0, 0.7, 56), (67, 1.75, 0.7, 58), (69, 2.5, 2.4, 62),
        (72, 5.0, 0.6, 56), (69, 5.6, 0.6, 54), (67, 6.2, 1.6, 52),
        (69, 9.0, 0.7, 58), (70, 9.75, 0.7, 60), (72, 10.5, 2.4, 64),
        (74, 13.0, 0.6, 58), (72, 13.6, 0.6, 56), (70, 14.2, 1.6, 54),
        (72, 17.0, 0.7, 60), (74, 17.75, 0.7, 62), (77, 18.5, 1.9, 68),
        (77, 20.5, 0.45, 62), (76, 21.0, 0.45, 60), (74, 21.5, 0.45, 58),
        (72, 22.0, 0.45, 56), (70, 22.5, 0.65, 54), (69, 23.25, 0.7, 52),
        (67, 25.0, 0.7, 54), (65, 25.75, 0.7, 52), (64, 26.5, 1.4, 56),
        (62, 28.0, 0.45, 50), (64, 28.5, 0.45, 52), (65, 29.0, 0.7, 54),
        (67, 29.75, 0.7, 56), (69, 30.5, 1.2, 60),
    ]
    for p, on, du, v in lh + rh:
        sc.note(CH_PNO, p, on, du, v, jt=4, jv=3)


def _m2_head_in(sc: en.Score) -> None:
    """[32, 96) The head: muted trumpet over brushes, walking bass,
    rootless piano and shell guitar.  16-bar form, one chorus."""
    rng = random.Random(SEED * 1000 + 2)
    _swing_time(sc, rng, HEADIN_T0, 16, ride_vel=52, tap_prob=0.3,
                swirl_prob=0.5)
    _walk(sc, rng, HEADIN_T0, PSOLO_T0)
    _comp_piano(sc, rng, _bars_between(HEADIN_T0, PSOLO_T0), vel=50)
    _comp_guitar(sc, rng, _bars_between(HEADIN_T0, PSOLO_T0), vel=45)
    _play_head(sc, HEADIN_T0, shift=0, vel_add=0)


def _m3_piano_solo(sc: en.Score) -> None:
    """[96, 160) Piano solo, one chorus: right-hand swung lines over
    sparse left-hand shells for 14 bars; the last two bars stand aside
    for the FABLE cell in 2x augmentation (material.play_cell) — the
    album's signature overheard three flights up."""
    rng = random.Random(SEED * 1000 + 3)
    _swing_time(sc, rng, PSOLO_T0, 16, ride_vel=54, tap_prob=0.45)
    _walk(sc, rng, PSOLO_T0, GSOLO_T0)
    _comp_guitar(sc, rng, _bars_between(PSOLO_T0, GSOLO_T0), vel=44)
    _solo_line(sc, CH_PNO, rng, _bars_between(PSOLO_T0, FABLE_T0),
               lo=62, hi=86, vel_lo=60, vel_hi=76)
    prev = None
    for t, root, qual in _bars_between(PSOLO_T0, FABLE_T0):
        if rng.random() < 0.8:
            pcs = [root + QUAL_TONES[qual][1], root + QUAL_TONES[qual][3]]
            prev = en.voice_lead(pcs, prev, 2, 50, 62)
            pos = rng.choice((0.0, 1.0 + SWING, 2.0))
            for p in prev:
                sc.note(CH_PNO, p, t + pos, 1.6, 46 + rng.randint(-3, 3),
                        jt=3, jv=2)
    material.play_cell(sc, CH_PNO, FABLE_T0, FABLE_ROOT,
                       stretch=FABLE_STRETCH, vel=70, vel_end=76,
                       jt=1, jv=2)


def _m4_guitar_solo(sc: en.Score) -> None:
    """[160, 192) Guitar solo, a half chorus (form bars 9-16), piano
    comping behind."""
    rng = random.Random(SEED * 1000 + 4)
    _swing_time(sc, rng, GSOLO_T0, 8, ride_vel=54, tap_prob=0.35)
    _walk(sc, rng, GSOLO_T0, TRADE_T0)
    _comp_piano(sc, rng, _bars_between(GSOLO_T0, TRADE_T0), vel=50)
    _solo_line(sc, CH_GTR, rng, _bars_between(GSOLO_T0, TRADE_T0),
               lo=55, hi=79, vel_lo=62, vel_hi=78)


def _m5_trading(sc: en.Score) -> None:
    """[192, 288) Trading fours, strict: P G D P G D.  The band walks
    behind the piano and guitar cells; the drum cells are brushes
    alone (bass and comping tacet — the oracle holds every cell to
    exactly its own voices)."""
    rng = random.Random(SEED * 1000 + 5)
    for k, cell in enumerate(TRADE_PATTERN):
        t = TRADE_T0 + CELL_BEATS * k
        if cell == "D":
            _drum_fill_cell(sc, rng, t)
            continue
        _swing_time(sc, rng, t, 4, ride_vel=54, tap_prob=0.35)
        _walk(sc, rng, t, t + CELL_BEATS)
        if cell == "P":
            _solo_line(sc, CH_PNO, rng, _bars_between(t, t + CELL_BEATS),
                       lo=62, hi=86, vel_lo=64, vel_hi=80)
        else:
            _solo_line(sc, CH_GTR, rng, _bars_between(t, t + CELL_BEATS),
                       lo=55, hi=79, vel_lo=64, vel_hi=80)


def _m6_shout(sc: en.Score) -> None:
    """[288, 320) The shout chorus: the ONE key lift (+2, to G) and the
    one post-intro tempo event (95).  The riff x3 with full-band stabs,
    then a 2-bar drum break under a held B5 into the head out."""
    rng = random.Random(SEED * 1000 + 6)
    _swing_time(sc, rng, SHOUT_T0, 6, ride_vel=62, kick_vel=56, hat_vel=44,
                tap_prob=0.0, backbeat_vel=62)
    _walk(sc, rng, SHOUT_T0, HEADOUT_T0)
    prev_p, prev_g = None, None
    colours = {"maj6": (4, 9, 2), "dom7": (4, 10, 2), "min7": (3, 10, 5)}
    bars = _bars_between(SHOUT_T0, HEADOUT_T0)
    for rep in range(3):
        t = SHOUT_T0 + 8.0 * rep
        sc.hit(49, t, 76 + 2 * rep, jt=2, jv=3)
        for on, du, p, v in SHOUT_RIFF:
            sc.note(CH_TPT, p, t + on, du, v, jt=2, jv=3)
        for rel in SHOUT_HITS:
            _, root, qual = bars[2 * rep + (0 if rel < 4.0 else 1)]
            prev_p = en.voice_lead([root + o for o in colours[qual]] +
                                   [root + 7], prev_p, 4, 57, 76)
            prev_g = en.voice_lead([root + o for o in QUAL_TONES[qual]],
                                   prev_g, 4, 52, 68)
            for p in prev_p:
                sc.note(CH_PNO, p, t + rel, 0.9 if rel != 1.0 else 1.2,
                        92 + rng.randint(-4, 4), jt=2, jv=3)
            en.strum(sc, CH_GTR, prev_g, t + rel, 0.8, 84, spread=0.03)
    # bars 7-8: the break — held B5 over Bm7, brushes building alone
    brk = SHOUT_T0 + 24.0
    sc.hit(49, brk, 80, jt=2, jv=3)
    sc.note(CH_TPT, 83, brk, 2.4, 96, jt=2, jv=2)
    _, root, qual = bars[6]
    prev_p = en.voice_lead([root + o for o in colours[qual]] + [root + 7],
                           prev_p, 4, 57, 76)
    for p in prev_p:
        sc.note(CH_PNO, p, brk, 2.2, 90, jt=2, jv=3)
    en.strum(sc, CH_GTR, prev_g, brk, 2.0, 82, spread=0.03)
    for bar in range(2):
        bt = brk + 4.0 * bar
        for rel in (0.0, 2.0):
            sc.hit(36, bt + rel, 44 + 8 * bar + rng.randint(-3, 3),
                   jt=3, jv=3)
        for rel in (1.0, 3.0):
            sc.hit(44, bt + rel, 40 + 4 * bar, jt=3, jv=3)
        for q in range(4):
            for off, prob in ((0.0, 0.85), (SWING, 0.65)):
                if rng.random() < prob:
                    drum = rng.choice((38, 40, 41, 43, 45, 47, 48, 50))
                    sc.hit(drum, bt + q + off,
                           min(100, 54 + 10 * bar + rng.randint(-4, 10)),
                           jt=3, jv=4)


def _m7_head_out(sc: en.Score) -> None:
    """[320, 384) The head out — the head-in trumpet line note for
    note, +2 semitones into G, a shade stronger; band as head-in."""
    rng = random.Random(SEED * 1000 + 7)
    sc.hit(49, HEADOUT_T0, 66, jt=2, jv=3)
    _swing_time(sc, rng, HEADOUT_T0, 16, ride_vel=56, tap_prob=0.3,
                swirl_prob=0.4)
    _walk(sc, rng, HEADOUT_T0, TAG_T0)
    _comp_piano(sc, rng, _bars_between(HEADOUT_T0, TAG_T0), vel=54)
    _comp_guitar(sc, rng, _bars_between(HEADOUT_T0, TAG_T0), vel=47)
    _play_head(sc, HEADOUT_T0, shift=2, vel_add=6)


def _m8_tag(sc: en.Score) -> None:
    """[384, 416) Tag ending x3 over |G6 E7|Am7 D7|, the band in
    2-feel (the documented walking deviation), then the last chord:
    a rolled G6/9, a crash and swirl, the trumpet's G5 fading on a
    written CC11 decrescendo."""
    rng = random.Random(SEED * 1000 + 8)
    _swing_time(sc, rng, TAG_T0, 6, ride_vel=48, kick_vel=26, hat_vel=32,
                tap_prob=0.2)
    tag_chords = [(43, "maj6"), (40, "dom7"), (45, "min7"), (38, "dom7")]
    prev_p, prev_g = None, None
    for rep in range(3):
        t = TAG_T0 + 8.0 * rep
        for j, (root, qual) in enumerate(tag_chords):
            beat = t + 2.0 * j
            sc.note(CH_BASS, root, beat, 1.9, 58 + rng.randint(-2, 3),
                    jt=3, jv=2)
            pcs = [root + o for o in QUAL_TONES[qual]]
            prev_p = en.voice_lead(pcs, prev_p, 4, 55, 76)
            prev_g = en.voice_lead(pcs, prev_g, 3, 50, 64)
            for p in prev_p:
                sc.note(CH_PNO, p, beat, 1.85, 60 + rng.randint(-3, 3),
                        jt=3, jv=2)
            for p in prev_g:
                sc.note(CH_GTR, p, beat, 1.7, 46 + rng.randint(-2, 2),
                        jt=3, jv=2)
        for on, du, p, v in TAG_FIG:
            sc.note(CH_TPT, p, t + on, du, min(127, v + 3 * rep),
                    jt=2, jv=2)
    # the last chord: everything rings, the mute fades on CC11
    sc.hit(49, TAG_FINAL_T0, 56, jt=0, jv=2)
    sc.note(CH_DRUMS, 40, TAG_FINAL_T0, 3.5, 42, jt=0, jv=2)
    sc.note(CH_BASS, 43, TAG_FINAL_T0, 6.0, 56, jt=0, jv=2)
    en.strum(sc, CH_PNO, [43, 50, 59, 64, 69, 74], TAG_FINAL_T0, 5.5, 64,
             spread=0.06)
    en.strum(sc, CH_GTR, [50, 55, 59, 64], TAG_FINAL_T0 + 0.5, 4.5, 50,
             spread=0.05)
    sc.note(CH_TPT, TAG_FINAL_PITCH, TAG_FINAL_T0, 6.0, 74, jt=0, jv=0)
    en.cc_curve(sc, CH_TPT, 11, [(TAG_FINAL_T0, 100),
                                 (TAG_FINAL_T0 + 6.0, 30)], step=0.5)


BUILDERS: list = [_m1_stairwell, _m2_head_in, _m3_piano_solo,
                  _m4_guitar_solo, _m5_trading, _m6_shout, _m7_head_out,
                  _m8_tag]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the track is composed to pass them
# ---------------------------------------------------------------------------

_ALL_CHANNELS = (CH_PNO, CH_BASS, CH_TPT, CH_GTR, CH_DRUMS)


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


def _check_brush_kit(sc) -> list[str]:
    """The drum channel selects the brush kit — one program event, 40,
    at beat 0 — and nothing ever re-selects another kit."""
    progs = _progs(sc, CH_DRUMS)
    if progs != [(0.0, 40)]:
        return [f"ch9 program lane {progs} != [(0.0, 40)] (brush kit)"]
    return []


def _check_rubato_intro(sc) -> list[str]:
    """>= 6 tempo events sculpt [0, 32); at/after 32 the map is exactly
    the arrival at 92 and the shout lift to 95; the intro genuinely
    breathes (bpm spread >= 12); the intro is solo piano."""
    fails = []
    tempos = sorted(sc.tempos)
    intro = [e for e in tempos if e[0] < HEADIN_T0]
    later = [e for e in tempos if e[0] >= HEADIN_T0]
    if len(intro) < 6:
        fails.append(f"only {len(intro)} tempo events inside the intro "
                     f"(want >= 6)")
    if later != [(HEADIN_T0, SWING_BPM), (SHOUT_T0, SHOUT_BPM)]:
        fails.append(f"tempo events at/after beat 32 are {later}, want "
                     f"only the arrival (32, 92) and the shout lift "
                     f"(288, 95)")
    bpms = [b for _t, b in intro]
    if bpms and max(bpms) - min(bpms) < 12:
        fails.append(f"intro bpm spread {max(bpms) - min(bpms):.0f} < 12: "
                     f"not really rubato")
    for ch in _ALL_CHANNELS:
        if ch == CH_PNO:
            continue
        early = [on for on, _d, _p, _v in _notes(sc, ch)
                 if on < HEADIN_T0 - 0.06]
        if early:
            fails.append(f"ch{ch} sounds at beat {early[0]:.2f} inside the "
                         f"solo-piano intro")
    if len([1 for on, _d, _p, _v in _notes(sc, CH_PNO)
            if on < HEADIN_T0]) < 20:
        fails.append("the intro has fewer than 20 piano notes")
    return fails


def _check_swing_ratio(sc) -> list[str]:
    """Every measured beat/off-beat/beat triple on the ride lane swings
    at 2:1 within [1.7, 2.4]; the mean sits in [1.85, 2.15]."""
    fails = []
    onsets = sorted(on for on, _d, p, _v in _notes(sc, CH_DRUMS) if p == 51)
    ratios = []
    for a, b, c in zip(onsets, onsets[1:], onsets[2:]):
        if 0.9 <= c - a <= 1.1 and 0.15 <= b - a <= 0.85:
            ratios.append((b - a) / (c - b))
    if len(ratios) < 60:
        fails.append(f"only {len(ratios)} swing triples measured "
                     f"(want >= 60)")
        return fails
    bad = [r for r in ratios if not 1.7 <= r <= 2.4]
    if bad:
        fails.append(f"{len(bad)} of {len(ratios)} ride triples outside "
                     f"2:1 window [1.7, 2.4], e.g. {bad[0]:.2f}")
    mean = sum(ratios) / len(ratios)
    if not 1.85 <= mean <= 2.15:
        fails.append(f"mean swing ratio {mean:.3f} outside [1.85, 2.15]")
    return fails


def _check_walking_bass(sc) -> list[str]:
    """Every documented walking bar: exactly four quarters, beat 1 ==
    the documented root, beat 4 within +-2 semitones of the next bar's
    documented root."""
    fails = []
    bass = _notes(sc, CH_BASS)
    for t, root, _qual, nxt in WALK_BARS:
        in_bar = [x for x in bass if t - 0.03 <= x[0] < t + 4.0 - 0.03]
        if len(in_bar) != 4:
            fails.append(f"bar at beat {t:.0f}: {len(in_bar)} bass notes, "
                         f"want 4 quarters")
            continue
        for k, (on, _du, p, _v) in enumerate(in_bar):
            if abs(on - (t + k)) > 0.03:
                fails.append(f"bar at {t:.0f}: beat-{k + 1} onset "
                             f"{on:.3f} off the quarter grid")
        if in_bar[0][2] != root:
            fails.append(f"bar at {t:.0f}: beat-1 pitch {in_bar[0][2]} != "
                         f"documented root {root}")
        if abs(in_bar[3][2] - nxt) > 2:
            fails.append(f"bar at {t:.0f}: beat-4 pitch {in_bar[3][2]} not "
                         f"within +-2 of next root {nxt}")
    return fails


def _check_darkened_trumpet(sc) -> list[str]:
    """The head voice is GM 59 (muted trumpet) — the documented choice —
    and CC74 is authored low (always <= 60) to darken it further."""
    fails = []
    progs = _progs(sc, CH_TPT)
    if [p for _b, p in progs] != [59]:
        fails.append(f"trumpet program lane {progs} != a single GM 59")
    cc74 = _ccs(sc, CH_TPT, 74)
    if not cc74:
        fails.append("no CC74 authored on the trumpet (the darkening)")
    for b, v in cc74:
        if v > 60:
            fails.append(f"trumpet CC74 {v} at beat {b:.1f} > 60: not dark")
    return fails


def _check_trading_fours(sc) -> list[str]:
    """Strict 4-bar alternation P G D P G D: piano only in P cells,
    guitar only in G cells, bass and comping out of D cells (drums
    alone), trumpet tacet throughout."""
    fails = []
    counts: dict[int, list[int]] = {}
    for ch in _ALL_CHANNELS:
        ons = [on for on, _d, _p, _v in _notes(sc, ch)]
        counts[ch] = [len([1 for on in ons
                           if t - 0.03 <= on < t + CELL_BEATS - 0.03])
                      for t in (TRADE_T0 + CELL_BEATS * k
                                for k in range(len(TRADE_PATTERN)))]
    for k, cell in enumerate(TRADE_PATTERN):
        tag = f"cell {k + 1} ({cell})"
        pno, bs, tpt, gtr, drm = (counts[CH_PNO][k], counts[CH_BASS][k],
                                  counts[CH_TPT][k], counts[CH_GTR][k],
                                  counts[CH_DRUMS][k])
        if tpt:
            fails.append(f"{tag}: trumpet sounds ({tpt} notes) in the fours")
        if drm < 8:
            fails.append(f"{tag}: only {drm} drum onsets (want >= 8)")
        if cell == "P" and (pno < 6 or gtr != 0 or bs < 12):
            fails.append(f"{tag}: piano {pno} (>=6), guitar {gtr} (==0), "
                         f"bass {bs} (>=12)")
        if cell == "G" and (gtr < 6 or pno != 0 or bs < 12):
            fails.append(f"{tag}: guitar {gtr} (>=6), piano {pno} (==0), "
                         f"bass {bs} (>=12)")
        if cell == "D" and (pno or gtr or bs):
            fails.append(f"{tag}: drums must solo alone (piano {pno}, "
                         f"guitar {gtr}, bass {bs})")
    return fails


def _check_shout_key_lift(sc) -> list[str]:
    """Exactly one key lift: F major to G major at the shout chorus,
    the G-form roots == F-form roots + 2, and the lift comes with the
    one allowed tempo event (92 -> 95)."""
    fails = []
    if sorted(sc.keysigs) != [(0.0, -1, 0), (SHOUT_T0, 1, 0)]:
        fails.append(f"keysig grid {sorted(sc.keysigs)} != F major then "
                     f"G major at {SHOUT_T0:.0f}")
    if (SHOUT_T0, SHOUT_BPM) not in sc.tempos or SHOUT_BPM <= SWING_BPM:
        fails.append("no tempo lift authored at the shout chorus")
    for (fr, fq), (gr, gq) in zip(F_FORM, G_FORM):
        if gr != fr + 2 or gq != fq:
            fails.append(f"G-form bar ({gr},{gq}) is not F-form "
                         f"({fr},{fq}) lifted +2")
    return fails


def _check_head_out_fidelity(sc) -> list[str]:
    """The head out is the head in, +2 semitones: same 45 notes, same
    relative onsets and durations."""
    fails = []
    tpt = _notes(sc, CH_TPT)
    tin = [x for x in tpt if HEADIN_T0 - 0.03 <= x[0] < PSOLO_T0]
    tout = [x for x in tpt if HEADOUT_T0 - 0.03 <= x[0] < TAG_T0]
    if len(tin) != len(HEAD) or len(tout) != len(HEAD):
        fails.append(f"head-in has {len(tin)} and head-out {len(tout)} "
                     f"trumpet notes, want {len(HEAD)} each")
        return fails
    for (i_on, i_du, i_p, _iv), (o_on, o_du, o_p, _ov) in zip(tin, tout):
        rel_i, rel_o = i_on - HEADIN_T0, o_on - HEADOUT_T0
        if abs(rel_o - rel_i) > 0.03:
            fails.append(f"onset {rel_o:.3f} != head-in {rel_i:.3f}")
        if o_p != i_p + 2:
            fails.append(f"pitch {o_p} at rel beat {rel_o:.2f} != "
                         f"head-in {i_p} + 2")
        if abs(o_du - i_du) > 0.03:
            fails.append(f"duration {o_du:.3f} at rel beat {rel_o:.2f} "
                         f"!= head-in {i_du:.3f}")
    return fails


def _check_tag_x3(sc) -> list[str]:
    """The 2-bar cadence figure occurs EXACTLY three times (whole
    trumpet lane), at 384/392/400; the tag span holds nothing else but
    them and the final held G5, which ends the trumpet's night."""
    fails = []
    tpt = _notes(sc, CH_TPT)
    fig = [(on, p) for on, _du, p, _v in TAG_FIG]
    starts = []
    for i in range(len(tpt)):
        if tpt[i][2] != fig[0][1] or i + len(fig) > len(tpt):
            continue
        base = tpt[i][0]
        if all(abs((tpt[i + j][0] - base) - fig[j][0]) <= 0.03
               and tpt[i + j][2] == fig[j][1] for j in range(len(fig))):
            starts.append(base)
    if len(starts) != 3:
        fails.append(f"cadence figure occurs {len(starts)} times "
                     f"(at {[f'{s:.1f}' for s in starts]}), want exactly 3")
    for want, got in zip((TAG_T0, TAG_T0 + 8.0, TAG_T0 + 16.0), starts):
        if abs(got - want) > 0.03:
            fails.append(f"figure statement at {got:.2f}, want {want:.0f}")
    span = [x for x in tpt if TAG_T0 - 0.03 <= x[0] < TAG_T0 + 24.0 - 0.03]
    if len(span) != 3 * len(TAG_FIG):
        fails.append(f"{len(span)} trumpet notes inside the tag's three "
                     f"figures, want {3 * len(TAG_FIG)}")
    if not tpt:
        return fails or ["no trumpet notes at all"]
    on, du, p, _v = tpt[-1]
    if p != TAG_FINAL_PITCH or abs(on - TAG_FINAL_T0) > 0.03 or du < 4.0:
        fails.append(f"final trumpet event ({p} at {on:.2f}, {du:.1f} "
                     f"beats) is not the held G5 at {TAG_FINAL_T0:.0f}")
    return fails


def _check_fable_quote(sc) -> list[str]:
    """The last two piano-solo bars quote the FABLE cell in 2x
    augmentation, recomputed from material.FABLE_CELL — silent L kept."""
    fails = []
    pno = _notes(sc, CH_PNO)
    for on, _du, semi in material.FABLE_CELL:
        want_on = FABLE_T0 + on * FABLE_STRETCH
        want_p = FABLE_ROOT + semi
        if not any(abs(x[0] - want_on) <= 0.02 and x[2] == want_p
                   for x in pno):
            fails.append(f"no piano note {want_p} at beat {want_on:.2f} "
                         f"(the augmented cell)")
    l0 = FABLE_T0 + material.FABLE_SILENT_L[0] * FABLE_STRETCH
    l1 = FABLE_T0 + material.FABLE_SILENT_L[1] * FABLE_STRETCH
    inside = [x for x in pno if l0 + 0.02 <= x[0] < l1 - 0.02]
    if inside:
        fails.append(f"piano note at beat {inside[0][0]:.2f} inside the "
                     f"silent L [{l0:.0f}, {l1:.0f})")
    return fails


def _check_dynamic_arc(sc) -> list[str]:
    """The night's shape in numbers: per-beat velocity density rises
    from the solo intro through the head to the shout chorus."""
    def density(lo: float, hi: float) -> float:
        tot = 0
        for ch in _ALL_CHANNELS:
            tot += sum(v for on, _d, _p, v in _notes(sc, ch)
                       if lo - 0.03 <= on < hi - 0.03)
        return tot / (hi - lo)

    intro = density(0.0, HEADIN_T0)
    head = density(HEADIN_T0, PSOLO_T0)
    shout = density(SHOUT_T0, SHOUT_T0 + 24.0)
    fails = []
    if not intro < head:
        fails.append(f"intro density {intro:.0f} !< head {head:.0f}")
    if not head < shout:
        fails.append(f"head density {head:.0f} !< shout {shout:.0f}")
    if not shout > 1.2 * head:
        fails.append(f"shout density {shout:.0f} <= 1.2x head {head:.0f}")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("brush_kit", _check_brush_kit(sc)),
        ("rubato_intro", _check_rubato_intro(sc)),
        ("swing_ratio", _check_swing_ratio(sc)),
        ("walking_bass", _check_walking_bass(sc)),
        ("darkened_trumpet", _check_darkened_trumpet(sc)),
        ("trading_fours", _check_trading_fours(sc)),
        ("shout_key_lift", _check_shout_key_lift(sc)),
        ("head_out_fidelity", _check_head_out_fidelity(sc)),
        ("tag_ending_x3", _check_tag_x3(sc)),
        ("fable_quote", _check_fable_quote(sc)),
        ("dynamic_arc_midi", _check_dynamic_arc(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/12 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The headline dynamics on the RENDER: the solo-piano intro sits
    at least 2 dB under the head-in, the shout chorus at least 2 dB
    over it, and the shout window is the loudest section of the
    night.  Windows are inset a beat from section edges so seam
    ring-over cannot blur them."""
    sections = [
        ("intro", 2.0, 30.0),
        ("head_in", 33.0, 95.0),
        ("piano_solo", 97.0, 159.0),
        ("guitar_solo", 161.0, 191.0),
        ("trading", 193.0, 287.0),
        ("shout", 288.5, 311.5),
        ("head_out", 321.0, 383.0),
        ("tag", 385.0, 413.0),
    ]
    levels: dict[str, float] = {}
    for name, b0, b1 in sections:
        i0, i1 = ctx.bar_window(b0, b1)
        levels[name] = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
    fails = []
    if levels["intro"] > levels["head_in"] - 2.0:
        fails.append(f"intro {levels['intro']:.1f} dB is not >= 2 dB below "
                     f"head-in {levels['head_in']:.1f} dB")
    if levels["shout"] < levels["head_in"] + 2.0:
        fails.append(f"shout {levels['shout']:.1f} dB is not >= 2 dB above "
                     f"head-in {levels['head_in']:.1f} dB")
    for name, lvl in levels.items():
        if name != "shout" and lvl > levels["shout"]:
            fails.append(f"section '{name}' ({lvl:.1f} dB) is louder than "
                         f"the shout chorus ({levels['shout']:.1f} dB)")
    return [("audio_night_arc", fails)]
