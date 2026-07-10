"""t05_the_832 — Track 5 "The 8.32" of *Through Lines*.

Disc 1, 'Lines of Descent' — the McCartney-middle-section-idiom commuter
vignette (HLD section 3, T5).  ORIGINAL music in the named idiom: nothing
is quoted — no Beatles melody, chord sequence or hook appears anywhere in
this module; every cell below is composed fresh in E-flat major.

The vignette, in five movements at a brisk dry 126 bpm:

  I.   The Alarm       — an agogo alarm clock (a REAL program-113 melodic
                         voice on its own channel, deliberately NOT the
                         ch-9 key-67 tick) hammers two diatonic pitches in
                         16ths and dies away while the dry piano wakes up.
  II.  Down the Stairs — the commute engine: dry piano eighth-note chords,
                         a walking bass in quarters (every beat, always
                         approaching the next downbeat by step), tight
                         closed hats.  A breathless flute narrates in
                         phrases of EXACTLY two bars, each cut off by at
                         least one full beat of gasping rest.
  III. Platform Two    — the groove drops to bass alone; the kit flips to
                         the BRUSH kit (ch-10 program 40) and brushed-snare
                         footsteps accelerate from a walk to a sprint;
                         the classic kit slams back with a station bell.
  IV.  Doors Closing   — the harmony climbs; strings swell and gliss up a
                         full octave (RPN bend-range 12, one long ramp) —
                         the departure whistle; a reverse-cymbal riser
                         (program 119) swells into the pivot beat.
  V.   The Lift        — the dream: the tempo map HALVES (126 -> 63), the
                         meter dissolves into irregular chord lengths, and
                         a wordless choir (CC70 morphing to 'ah' >= 80)
                         climbs a whole-tone slope with harp arpeggi and
                         celesta memories of the alarm.  Everything after
                         the pivot (choir, celesta bells, harp) draws from
                         ONE whole-tone scale, and the piece hangs on an
                         augmented sonority — no E-flat-major tonic chord
                         sounds anywhere in the last four bars.  It hands
                         straight into silence.

Written oracle-first (the repo method): every headline claim above is a
falsifiable oracle below — groove_engine (piano/hat eighth coverage),
walking_bass (quarter coverage + the approach-note rule), the
lead_phrase_grammar (2-bar grid, span <= 7 beats, >= 1 beat of rest),
alarm_agogo (program 113, two alternating pitches, decaying 16ths, and NO
ch-9 agogo key anywhere), footsteps_accelerando (brush-kit program change,
non-increasing inter-onset times, rising velocities), departure_gliss
(RPN 12 + a monotone full-scale bend ramp, recentred), dream_pivot_riser
(one program-119 note ending exactly on the pivot), tempo_halves,
whole_tone_dream (post-pivot notes exist only on choir/bells/harp and sit
inside one whole-tone collection), eb_commute (everything before the pivot
is diatonic E-flat major — which is what makes the lift lift),
choir_ah (CC70 >= 80 authored after the pivot), unresolved_tail (last 16
beats: no B-flat at all, no perfect-fifth simultaneity, last event is not
the tonic), and commute_arc (rising per-window velocity means).
audio_checks() mirrors the headline render claim: narrow-band energy at
the choir's A4/B4/Db5 — pitches E-flat major never sounds — lifts by
>= 10 dB after the pivot.

Determinism: this module uses NO randomness of its own; the only jitter is
the Score's own SEED-seeded humanisation, so a rebuild is byte-identical.
"""

from __future__ import annotations

import bisect
import math

import conductor
import engine as en

NUMBER = 5
TITLE = 'The 8.32'
FILE = '05 - The 8.32.mid'
SEED = 20260905

COMMENT = ("A commuter vignette in the 'A Day in the Life' middle-section "
           "idiom - original music, nothing quoted: dry piano eighths, "
           "walking bass, tight hats, two-bar breathless flute phrases; "
           "then the dream pivot - the tempo halves and a wordless choir "
           "climbs a whole-tone slope into unresolved light.")

# ---------------------------------------------------------------------------
# The clock and the map.
# ---------------------------------------------------------------------------

BPM = 126.0                 # the commute
PIVOT = 272.0               # the dream pivot beat: tempo halves here
END = 352.0
GROOVE_T0 = 16.0            # the commute engine starts here (bar grid origin)

MOVS: list[tuple[str, float, float]] = [
    ("I. The Alarm", 0.0, 16.0),
    ("II. Down the Stairs", 16.0, 120.0),
    ("III. Platform Two", 120.0, 224.0),
    ("IV. Doors Closing", 224.0, PIVOT),
    ("V. The Lift", PIVOT, END),
]

BREAK = (176.0, 192.0)      # the footsteps break: groove out, kit -> brush
GROOVE_SPANS = [(16.0, 176.0), (192.0, 272.0)]   # full-groove beat ranges

# Channels.
CH_PIANO, CH_BASS, CH_LEAD, CH_ALARM, CH_STRINGS = 0, 1, 2, 3, 4
CH_RISER, CH_CHOIR, CH_BELLS, CH_HARP, CH_KIT = 5, 6, 7, 8, 9

# E-flat major (the commute) and the whole-tone lift (the dream).
EB_PCS = {3, 5, 7, 8, 10, 0, 2}      # Eb F G Ab Bb C D
WT1_PCS = {1, 3, 5, 7, 9, 11}        # the odd whole-tone scale (holds Eb)
KEY_BASE = 63                        # Eb4: degree-1 anchor for lead/piano
BASS_BASE = 39                       # Eb2: degree-1 anchor for the bass

# ---------------------------------------------------------------------------
# Harmony — 64 groove bars (beats 16..272), one chord per bar, all diatonic.
# An original pop progression; the loop deliberately avoids any borrowed or
# chromatic chord so the whole commute is provably inside E-flat major.
# ---------------------------------------------------------------------------

_LOOP_A = [1, 5, 6, 5, 4, 3, 2, 5]
CHORDS: list[int] = (
    _LOOP_A * 3 + [4, 5]                                   # II  (26 bars)
    + _LOOP_A + [6, 5, 4, 5, 1, 1]                         # III groove
    + [6, 4, 2, 5]                                         # III break
    + [4, 5, 6, 5, 4, 5, 1, 1]                             # III return
    + [1, 4, 1, 4, 2, 3, 4, 5, 4, 5, 4, 5]                 # IV  (12 bars)
)
assert len(CHORDS) == 64


def _bar_beat(b: int) -> float:
    return GROOVE_T0 + 4.0 * b


def _vel_scale(b: int) -> float:
    """The commute accelerates: a slow global crescendo, bar by bar."""
    return en.lerp(0.92, 1.15, b / 63.0)


def _rh_voicings() -> list[list[int]]:
    """Voice-led right-hand triads for every bar (one chain, pure data)."""
    prev = None
    out = []
    for deg in CHORDS:
        prev = en.voice_lead(en.triad(KEY_BASE, "ionian", deg), prev,
                             3, 62, 81)
        out.append(prev)
    return out


_RH = _rh_voicings()


def _lh_pitch(deg: int) -> int:
    """The left-hand root: the unique chord-root pitch inside [46, 57]."""
    pc = en.pitch(KEY_BASE, "ionian", deg) % 12
    return 46 + (pc - 46) % 12


# The walking bass: diatonic ladder Eb2..Bb3; every bar walks
# root -> third -> passing tone -> approach note (a ladder neighbour of the
# NEXT bar's root, hence always within 2 semitones of the next downbeat).
_LAD = [p for p in range(BASS_BASE, 59) if p % 12 in EB_PCS]


def _bass_walk() -> list[tuple[float, int]]:
    out: list[tuple[float, int]] = []
    for b, deg in enumerate(CHORDS):
        nxt = CHORDS[b + 1] if b + 1 < len(CHORDS) else 1
        i0 = _LAD.index(en.pitch(BASS_BASE, "ionian", deg))
        i_n = _LAD.index(en.pitch(BASS_BASE, "ionian", nxt))
        if i_n > i0:
            ia = i_n - 1
        elif i_n < i0:
            ia = i_n + 1
        else:
            ia = i_n - 1 if i_n > 0 else i_n + 1
        i1 = i0 + 2 if i0 + 2 < len(_LAD) else i0 - 2
        if ia > i1:
            i2 = ia - 1
        elif ia < i1:
            i2 = ia + 1
        else:
            i2 = ia + 1 if ia + 1 < len(_LAD) else ia - 1
        t = _bar_beat(b)
        for q, idx in enumerate((i0, i1, i2, ia)):
            out.append((t + q, _LAD[idx]))
    return out


_BASS = _bass_walk()

# ---------------------------------------------------------------------------
# The breathless flute.  Four original two-bar cells (degree, start, dur);
# every cell's last onset reaches into its second bar and its last note
# releases before beat 7 of the two-bar slot — leaving the scored gasp.
# ---------------------------------------------------------------------------

_CELLS: dict[str, list[tuple[int, float, float]]] = {
    "A": [(1, 0.0, 0.5), (2, 0.5, 0.5), (3, 1.0, 0.5), (4, 1.5, 0.5),
          (5, 2.0, 1.0), (3, 3.0, 0.5), (4, 3.5, 0.5), (6, 4.0, 2.4)],
    "B": [(8, 0.0, 0.75), (7, 0.75, 0.25), (6, 1.0, 0.5), (5, 1.5, 0.5),
          (4, 2.0, 0.75), (5, 2.75, 0.25), (3, 3.0, 1.0), (2, 4.0, 2.3)],
    "C": [(5, 0.0, 0.25), (6, 0.25, 0.25), (5, 0.5, 0.5), (3, 1.0, 0.5),
          (5, 1.5, 1.0), (6, 2.5, 0.5), (8, 3.0, 0.75), (9, 3.75, 0.25),
          (8, 4.0, 2.2)],
    "D": [(3, 0.0, 0.5), (2, 0.5, 0.5), (1, 1.0, 0.75), (2, 1.75, 0.25),
          (3, 2.0, 0.5), (4, 2.5, 0.5), (5, 3.0, 0.5), (4, 3.5, 0.5),
          (2, 4.0, 1.5), (1, 5.5, 0.9)],
}

# (slot beat, cell, degree shift, velocity) — slots sit on the two-bar grid.
_PHRASES: list[tuple[float, str, int, int]] = [
    (48.0, "A", 0, 70), (64.0, "B", 0, 72), (72.0, "C", 0, 74),
    (88.0, "D", 0, 74), (104.0, "A", 1, 76), (112.0, "B", 1, 78),
    (128.0, "C", 0, 78), (136.0, "A", 3, 80), (152.0, "B", 3, 80),
    (168.0, "D", 1, 82), (200.0, "C", 1, 82), (216.0, "A", 4, 84),
    (232.0, "B", 4, 86), (248.0, "C", 3, 88),
]

# ---------------------------------------------------------------------------
# The dream (movement V) — all data from ONE whole-tone scale (WT1_PCS).
# Chord lengths expand (7, 8, 9, 10, 12 beats): the meter dissolving.
# ---------------------------------------------------------------------------

_DREAM_CHORDS: list[tuple[float, int, float, int]] = [
    # (beat, root pitch, dur, velocity) — voices are root-12/root/+4/+8,
    # every offset even, so the whole-tone membership is closed.
    (272.0, 63, 7.2, 58),    # Eb
    (279.0, 65, 8.2, 62),    # F
    (287.0, 67, 9.2, 66),    # G
    (296.0, 69, 10.2, 70),   # A
    (306.0, 71, 12.2, 72),   # B
]
_HANG = (53, 65, 69, 73)     # F3 F4 A4 Db5 — augmented: no fifth, no tonic
_HANG_T0, _HANG_RESTRIKE, _HANG_OFF = 318.0, 333.0, 348.0

# The alarm remembered: celesta pairs, augmented 4x, whole-tone pitches.
_BELL_MEMORIES: list[tuple[float, tuple[int, ...], int]] = [
    (284.0, (85, 81, 85), 58), (300.0, (81, 85, 81), 54),
    (316.0, (85, 81, 85), 50), (332.0, (81, 77, 81), 46),
]
_LAST_BELL = (350.0, 89, 54)             # the final light: F6, then silence

# The alarm itself (movement I): two diatonic pitches, hammered.
_ALARM_HI, _ALARM_LO = 82, 79            # Bb5 / G5

# ---------------------------------------------------------------------------
# PART — grid, tempo (halving at the pivot), channels.
# ---------------------------------------------------------------------------

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=MOVS,
    tempo_map=[(0.0, BPM), (PIVOT, BPM / 2.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -3, 0), (PIVOT, 0, 0)],   # Eb major; the dream unsigned
    channels=[
        (CH_PIANO, "piano - the 8.32", 0, 105, 54, 10),      # DRY, transient
        (CH_BASS, "walking bass", 32, 110, 64, 12),
        (CH_LEAD, "flute - the commuter", 73, 96, 64, 30),
        (CH_ALARM, "agogo - the alarm", 113, 88, 84, 25),
        (CH_STRINGS, "strings - departure", 48, 92, 64, 50),
        (CH_RISER, "reverse cymbal - the pivot", 119, 105, 64, 55),
        (CH_CHOIR, "choir - the dream", 52, 108, 64, 72),
        (CH_BELLS, "celesta - dream bells", 8, 85, 74, 60),
        (CH_HARP, "harp - dream current", 46, 95, 50, 60),
        (CH_KIT, "kit", 0, 100, 64, 20),
    ],
    program_changes=[
        (CH_KIT, 176.25, 40),   # brush kit for the footsteps
        (CH_KIT, 191.75, 0),    # classic kit back for the return
    ],
    extra_markers=[
        (176.0, "footsteps - running for it"),
        (256.0, "the departure whistle"),
        (264.0, "doors closing - riser"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {0, 8, 32, 46, 48, 52, 73, 113, 119}
CENTERED_CHANNELS: set[int] = {CH_BASS, CH_LEAD, CH_STRINGS, CH_RISER,
                               CH_CHOIR}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_PIANO: (44, 86),
    CH_BASS: (36, 62),
    CH_LEAD: (58, 84),
    CH_ALARM: (70, 86),
    CH_STRINGS: (50, 80),
    CH_RISER: (65, 75),
    CH_CHOIR: (48, 84),
    CH_BELLS: (72, 92),
    CH_HARP: (48, 88),
}
GAP_WHITELIST: list[tuple[float, float]] = [
    (347.0, 350.5),   # the hang releases; one breath of air; the last bell
]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (204.0, 211.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Oracle helpers (event readers).
# ---------------------------------------------------------------------------

def _ons(sc: en.Score, ch: int) -> list[tuple[float, int, int]]:
    """(beat, pitch, vel) of every note-on, time-sorted."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick / en.PPQ, data[1], data[2]))
    return sorted(out)


def _note_spans(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """(on, off, pitch, vel) with FIFO on/off pairing, sorted by onset."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out = []
    for tick, _prio, data in sorted(sc.events.get(ch, []),
                                    key=lambda e: (e[0], e[1])):
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick / en.PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick / en.PPQ, data[1], vel))
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
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / en.PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _coverage(onsets: list[float], spans: list[tuple[float, float]],
              step: float, tol: float = 0.07) -> tuple[int, int]:
    """(covered, total) grid positions with an onset within +-tol."""
    covered = total = 0
    for lo, hi in spans:
        t = lo
        while t < hi - 1e-9:
            total += 1
            i = bisect.bisect_left(onsets, t - tol)
            if i < len(onsets) and onsets[i] <= t + tol:
                covered += 1
            t += step
    return covered, total


def _cap(fails: list[str], cap: int = 6) -> list[str]:
    if len(fails) > cap:
        return fails[:cap] + [f"... and {len(fails) - cap} more"]
    return fails


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the music; the movements below are composed to
# pass them.
# ---------------------------------------------------------------------------

def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    # --- groove_engine: dry piano eighths + tight hats cover the grid ------
    fails: list[str] = []
    piano_on = [b for b, _p, _v in _ons(sc, CH_PIANO)]
    hat_on = [b for b, p, _v in _ons(sc, CH_KIT) if p in (42, 46)]
    for name, onsets in (("piano", piano_on), ("hats", hat_on)):
        got, want = _coverage(onsets, GROOVE_SPANS, 0.5)
        if want and got / want < 0.9:
            fails.append(f"{name} eighth-grid coverage {got}/{want} < 90%")
    results.append(("groove_engine", fails))

    # --- walking_bass: quarters on every beat, approach-note discipline ----
    fails = []
    bass = _ons(sc, CH_BASS)
    bass_beats = [b for b, _p, _v in bass]
    got, want = _coverage(bass_beats, [(GROOVE_T0, PIVOT)], 1.0)
    if want and got / want < 0.95:
        fails.append(f"bass quarter coverage {got}/{want} < 95%")

    def _pitch_at(beat: float) -> int | None:
        i = bisect.bisect_left(bass_beats, beat - 0.1)
        if i < len(bass) and abs(bass[i][0] - beat) <= 0.1:
            return bass[i][1]
        return None

    for b in range(63):
        p3 = _pitch_at(_bar_beat(b) + 3.0)
        pn = _pitch_at(_bar_beat(b + 1))
        if p3 is None or pn is None:
            fails.append(f"bar {b}: missing beat-4 or downbeat bass note")
        elif abs(p3 - pn) > 2:
            fails.append(f"bar {b}: approach {p3} -> {pn} leaps "
                         f"{abs(p3 - pn)} semitones (> 2)")
    results.append(("walking_bass", _cap(fails)))

    # --- lead_phrase_grammar: EXACTLY two-bar phrases, >= 1 beat of rest ---
    fails = []
    lead = _note_spans(sc, CH_LEAD)
    phrases: list[list[tuple[float, float, int, int]]] = []
    for span in lead:
        if phrases and span[0] - max(s[1] for s in phrases[-1]) < 0.98:
            phrases[-1].append(span)
        else:
            phrases.append([span])
    if len(phrases) < 12:
        fails.append(f"only {len(phrases)} lead phrases (want >= 12)")
    for k, ph in enumerate(phrases):
        s_on = ph[0][0]
        grid = GROOVE_T0 + 8.0 * round((s_on - GROOVE_T0) / 8.0)
        if abs(s_on - grid) > 0.15:
            fails.append(f"phrase {k} starts at {s_on:.2f}, off the "
                         f"two-bar grid ({grid:.0f})")
        last_off = max(s[1] for s in ph)
        if last_off > grid + 7.05:
            fails.append(f"phrase {k} releases at {last_off:.2f} > "
                         f"{grid + 7.0:.2f}: no gasp left")
        if max(s[0] for s in ph) < grid + 3.8:
            fails.append(f"phrase {k} never reaches its second bar")
    for (a, b) in zip(phrases, phrases[1:]):
        gap = b[0][0] - max(s[1] for s in a)
        if gap < 0.98:
            fails.append(f"phrase gap {gap:.2f} beats < 1 at "
                         f"{b[0][0]:.2f}")
    if any(s[0] >= 256.0 for s in lead):
        fails.append("the flute keeps talking after the whistle (>= 256)")
    results.append(("lead_phrase_grammar", _cap(fails)))

    # --- alarm_agogo: a real program-113 voice, not the ch-9 tick ----------
    fails = []
    progs3 = _progs(sc, CH_ALARM)
    if not progs3 or any(p != 113 for _b, p in progs3):
        fails.append(f"alarm channel programs {progs3} != [113]")
    alarm = [(b, p, v) for b, p, v in _ons(sc, CH_ALARM) if b < 16.0]
    if len(alarm) < 24:
        fails.append(f"only {len(alarm)} alarm notes in movement I")
    pits = {p for _b, p, _v in alarm}
    if pits != {_ALARM_LO, _ALARM_HI}:
        fails.append(f"alarm pitches {sorted(pits)} != two-pitch bell "
                     f"{{{_ALARM_LO}, {_ALARM_HI}}}")
    burst = [(b, p, v) for b, p, v in alarm if b < 6.0]
    for (b0, p0, _v0), (b1, p1, _v1) in zip(burst, burst[1:]):
        if p0 == p1:
            fails.append(f"alarm repeats pitch {p0} at {b1:.2f} "
                         f"(must alternate)")
        if not 0.21 <= b1 - b0 <= 0.29:
            fails.append(f"alarm inter-onset {b1 - b0:.3f} at {b1:.2f} "
                         f"is not a 16th")
    if len(burst) >= 16:
        head = sum(v for _b, _p, v in burst[:8]) / 8.0
        tail = sum(v for _b, _p, v in burst[-8:]) / 8.0
        if head - tail < 6.0:
            fails.append(f"alarm does not die away ({head:.0f} -> "
                         f"{tail:.0f})")
    if any(p in (67, 68) for _b, p, _v in _ons(sc, CH_KIT)):
        fails.append("ch9 sounds the GM agogo tick (key 67/68): banned")
    results.append(("alarm_agogo", _cap(fails)))

    # --- footsteps_accelerando: brush kit, accelerating, approaching -------
    fails = []
    steps = [(b, p, v) for b, p, v in _ons(sc, CH_KIT)
             if BREAK[0] < b < BREAK[1] - 0.1]
    if len(steps) < 12:
        fails.append(f"only {len(steps)} footsteps in the break")
    if any(p not in (38, 40) for _b, p, _v in steps):
        fails.append("non-brush key inside the footsteps break")
    iois = [b1 - b0 for (b0, _p0, _v0), (b1, _p1, _v1)
            in zip(steps, steps[1:])]
    for i, (a, b) in enumerate(zip(iois, iois[1:])):
        if b > a + 0.01:
            fails.append(f"footstep interval grows at step {i + 1} "
                         f"({a:.2f} -> {b:.2f}): not accelerating")
    if iois and iois[-1] > 0.45 * iois[0]:
        fails.append(f"final stride {iois[-1]:.2f} > 45% of first "
                     f"{iois[0]:.2f}: never breaks into a run")
    vels = [v for _b, _p, v in steps]
    if any(b < a for a, b in zip(vels, vels[1:])):
        fails.append("footstep velocities not non-decreasing "
                     "(they approach)")
    kit = _progs(sc, CH_KIT)
    want_kit = [(176.25, 40), (191.75, 0)]
    if len(kit) != 2 or any(abs(gb - wb) > 0.05 or gp != wp
                            for (gb, gp), (wb, wp) in zip(kit, want_kit)):
        fails.append(f"kit program lane {kit} != {want_kit} "
                     f"(brush in, classic out)")
    results.append(("footsteps_accelerando", _cap(fails)))

    # --- departure_gliss: RPN-12 string octave gliss, recentred ------------
    fails = []
    if not any(v == 12 for _b, v in _ccs(sc, CH_STRINGS, 6)):
        fails.append("strings never author RPN data (CC6) = 12 semitones")
    if not any(v == 0 for _b, v in _ccs(sc, CH_STRINGS, 100)):
        fails.append("strings never address RPN 0 (bend range)")
    gnotes = [(b, p) for b, p, _v in _ons(sc, CH_STRINGS)
              if 255.5 <= b <= 256.5]
    if len(gnotes) != 1 or gnotes[0][1] != 70:
        fails.append(f"whistle note {gnotes} != one Bb4 at beat 256")
    if any(256.6 < b < PIVOT for b, _p, _v in _ons(sc, CH_STRINGS)):
        fails.append("stray string note during the whistle")
    ramp = [(b, f) for b, f in _bends(sc, CH_STRINGS) if 255.5 <= b <= 263.5]
    if not ramp:
        fails.append("no gliss bend ramp on the strings")
    else:
        if abs(ramp[0][1]) > 0.05:
            fails.append(f"gliss starts off-centre ({ramp[0][1]:+.2f})")
        peak = max(f for _b, f in ramp)
        if peak < 0.95:
            fails.append(f"gliss peaks at {peak:.2f} of full scale "
                         f"(< 0.95): not a full octave")
        top = max(range(len(ramp)), key=lambda i: ramp[i][1])
        for (b0, f0), (b1, f1) in zip(ramp[:top], ramp[1:top + 1]):
            if f1 < f0 - 1e-6:
                fails.append(f"gliss dips at {b1:.2f}: must rise "
                             f"monotonically")
        after = [f for b, f in _bends(sc, CH_STRINGS) if b > 263.5]
        if not after or abs(after[-1]) > 0.02:
            fails.append("gliss never recentres before the pivot")
    results.append(("departure_gliss", _cap(fails)))

    # --- dream_pivot_riser: one reverse-cymbal swell ending ON the pivot ---
    fails = []
    riser = _note_spans(sc, CH_RISER)
    if len(riser) != 1:
        fails.append(f"{len(riser)} riser notes (want exactly 1)")
    else:
        on, off, _p, vel = riser[0]
        if abs(on - 264.0) > 0.05:
            fails.append(f"riser starts at {on:.2f}, want 264")
        if abs(off - PIVOT) > 0.05:
            fails.append(f"riser stops at {off:.2f}, want the pivot "
                         f"({PIVOT})")
        if vel < 90:
            fails.append(f"riser velocity {vel} < 90")
    results.append(("dream_pivot_riser", fails))

    # --- tempo_halves -------------------------------------------------------
    fails = []
    if PART.TEMPO_MAP != [(0.0, BPM), (PIVOT, BPM / 2.0)]:
        fails.append(f"tempo map {PART.TEMPO_MAP} is not one halving "
                     f"at the pivot")
    if sorted(sc.tempos) != sorted(PART.TEMPO_MAP):
        fails.append("Score tempo lane differs from the map")
    if PIVOT != MOVS[-1][1]:
        fails.append("the pivot is not the dream movement's downbeat")
    results.append(("tempo_halves", fails))

    # --- whole_tone_dream: after the pivot, ONE whole-tone world -----------
    fails = []
    for ch in (CH_CHOIR, CH_BELLS, CH_HARP):
        for b, p, _v in _ons(sc, ch):
            if b < PIVOT - 1e-6:
                fails.append(f"dream ch{ch} plays at {b:.2f}, before "
                             f"the pivot")
            elif p % 12 not in WT1_PCS:
                fails.append(f"dream ch{ch} pitch {p} at {b:.2f} is "
                             f"outside the whole-tone scale")
    for ch in (CH_PIANO, CH_BASS, CH_LEAD, CH_ALARM, CH_STRINGS,
               CH_RISER, CH_KIT):
        for b, _p, _v in _ons(sc, ch):
            if b >= PIVOT - 1e-6:
                fails.append(f"commute ch{ch} plays at {b:.2f}, after "
                             f"the pivot")
    results.append(("whole_tone_dream", _cap(fails)))

    # --- eb_commute: everything before the pivot is E-flat major -----------
    fails = []
    for ch in (CH_PIANO, CH_BASS, CH_LEAD, CH_ALARM, CH_STRINGS, CH_RISER):
        for b, p, _v in _ons(sc, ch):
            if b < PIVOT - 1e-6 and p % 12 not in EB_PCS:
                fails.append(f"ch{ch} pitch {p} at {b:.2f} is chromatic "
                             f"(commute must stay diatonic)")
    results.append(("eb_commute", _cap(fails)))

    # --- choir_ah: the wordless choir opens to 'ah' (CC70 >= 80) -----------
    fails = []
    cc70 = _ccs(sc, CH_CHOIR, 70)
    post = [(b, v) for b, v in cc70 if b >= PIVOT - 0.05]
    if not post:
        fails.append("choir never authors CC70 after the pivot")
    else:
        if max(v for _b, v in post) < 80:
            fails.append(f"choir CC70 peaks at "
                         f"{max(v for _b, v in post)} (< 80: never 'ah')")
        if post[-1][1] < 80:
            fails.append(f"choir closes on CC70 {post[-1][1]} (< 80)")
        if not any(v >= 80 and b <= PIVOT + 10.0 for b, v in post):
            fails.append("the vowel never opens early in the dream")
    results.append(("choir_ah", fails))

    # --- unresolved_tail: no Eb-major tonic sonority in the last 4 bars ----
    fails = []
    tail: list[tuple[float, float, int]] = []
    for ch in sorted(sc.events):
        for on, off, p, _v in _note_spans(sc, ch):
            if off > END - 16.0:
                tail.append((max(on, END - 16.0), off, p))
    for _on, _off, p in tail:
        if p % 12 == 10:
            fails.append(f"Bb (pitch {p}) sounds in the last four bars: "
                         f"the dominant of Eb is banned from the tail")
    for i, (on1, off1, p1) in enumerate(tail):
        for on2, off2, p2 in tail[i + 1:]:
            if min(off1, off2) - max(on1, on2) > 0.05:
                d = (p1 - p2) % 12
                if d in (5, 7):
                    fails.append(f"perfect fifth {p1}/{p2} sounds near "
                                 f"{max(on1, on2):.1f}: too resolved")
    all_ons = [(b, p) for ch in sorted(sc.events)
               for b, p, _v in _ons(sc, ch)]
    if all_ons:
        last_b, last_p = max(all_ons)
        if last_p % 12 in (3, 10):
            fails.append(f"the last event ({last_p} at {last_b:.1f}) "
                         f"lands on the tonic/dominant: must hang")
    results.append(("unresolved_tail", _cap(fails)))

    # --- commute_arc: the commute accelerates (rising velocity means) ------
    fails = []
    windows = [(16.0, 80.0), (80.0, 144.0), (192.0, 256.0)]
    means = []
    engine_ons = (_ons(sc, CH_PIANO) + _ons(sc, CH_BASS)
                  + _ons(sc, CH_KIT))
    for lo, hi in windows:
        vels = [v for b, _p, v in engine_ons if lo <= b < hi]
        means.append(sum(vels) / len(vels) if vels else 0.0)
    for i, (a, b) in enumerate(zip(means, means[1:])):
        if b < a + 1.5:
            fails.append(f"window {i}->{i + 1} does not press on "
                         f"({a:.1f} -> {b:.1f})")
    results.append(("commute_arc", fails))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/05 - The 8.32.wav exists.
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The headline render claim: the choir band lifts after the pivot.

    The dream choir holds A4 / B4 / Db5 — pitch classes E-flat major never
    sounds, so narrow-band energy at those frequencies is near the floor
    during the commute and must LIFT once the whole-tone choir enters.
    Frame-based Goertzel (0.2 s frames, a +-25-cent comb per pitch, max
    over the comb, mean amplitude per window).
    """
    rate = ctx.sample_rate
    pitches = (69, 71, 73)                          # A4, B4, Db5
    comb = [440.0 * 2 ** ((p - 69) / 12.0 + c / 1200.0)
            for p in pitches for c in (-25.0, 0.0, 25.0)]
    frame = int(0.2 * rate)

    def band_amp(i0: int, i1: int) -> float:
        i0 = max(0, i0)
        i1 = min(len(ctx.l), i1)
        amps = []
        i = i0
        while i + frame <= i1:
            best = 0.0
            for f in comb:
                w = 2.0 * math.pi * f / rate
                coeff = 2.0 * math.cos(w)
                s1 = s2 = 0.0
                for k in range(i, i + frame):
                    s0 = (ctx.l[k] + ctx.r[k]) * 0.5 + coeff * s1 - s2
                    s2 = s1
                    s1 = s0
                power = s1 * s1 + s2 * s2 - coeff * s1 * s2
                amp = 2.0 * math.sqrt(max(power, 0.0)) / frame
                best = max(best, amp)
            amps.append(best)
            i += frame * 3                          # stride: every 3rd frame
        return sum(amps) / len(amps) if amps else 0.0

    fails: list[str] = []
    pre = band_amp(*ctx.bar_window(220.0, 252.0))     # groove, pre-whistle
    post = band_amp(*ctx.bar_window(280.0, 304.0))    # the choir climb
    pre_db, post_db = ctx.db(pre), ctx.db(post)
    lift = post_db - pre_db
    if lift < 10.0:
        fails.append(f"choir-band lift {lift:.1f} dB "
                     f"({pre_db:.1f} -> {post_db:.1f}), want >= 10")
    if post_db < -55.0:
        fails.append(f"choir band only {post_db:.1f} dB after the pivot "
                     f"(< -55: the dream is inaudible)")
    return [("audio_choir_band_lift", fails)]


# ---------------------------------------------------------------------------
# Builders — composed to pass the oracles above.
# ---------------------------------------------------------------------------

def _groove_bar(sc: en.Score, b: int, piano: bool = True,
                hats: bool = True, bass_hush: bool = False) -> None:
    """One bar of the commute engine at bar index b (beat 16 + 4b)."""
    t = _bar_beat(b)
    s = _vel_scale(b)
    if piano:
        pat = (86, 68, 76, 69, 83, 68, 77, 72)
        for e in range(8):
            for p in _RH[b]:
                sc.note(CH_PIANO, p, t + e * 0.5, 0.42, int(pat[e] * s),
                        jt=2, jv=3)
        lh = _lh_pitch(CHORDS[b])
        sc.note(CH_PIANO, lh, t, 1.6, int(80 * s), jt=2, jv=3)
        sc.note(CH_PIANO, lh, t + 2.0, 1.6, int(74 * s), jt=2, jv=3)
    hush = 0.82 if bass_hush else 1.0
    for q in range(4):
        beat, p = _BASS[b * 4 + q]
        vel = (82 if q == 0 else 76) * s * hush
        sc.note(CH_BASS, p, beat, 0.95, int(vel), jt=2, jv=3)
    if hats:
        for e in range(8):
            if b % 4 == 3 and e == 7:
                sc.note(CH_KIT, 46, t + 3.5, 0.45, int(66 * s), jt=1, jv=2)
            else:
                vel = 84 if e == 0 else (72 if e % 2 == 0 else 56)
                sc.note(CH_KIT, 42, t + e * 0.5, 0.1, int(vel * s),
                        jt=1, jv=2)
        sc.note(CH_KIT, 36, t, 0.3, int(88 * s), jt=1, jv=2)
        sc.note(CH_KIT, 36, t + 2.0, 0.3, int(80 * s), jt=1, jv=2)
        sc.note(CH_KIT, 37, t + 1.0, 0.15, int(55 * s), jt=1, jv=2)
        sc.note(CH_KIT, 37, t + 3.0, 0.15, int(55 * s), jt=1, jv=2)


def _phrases_in(sc: en.Score, t0: float, t1: float) -> None:
    """The flute's two-bar gasps whose slots fall inside [t0, t1)."""
    for slot, cell, shift, vel in _PHRASES:
        if not t0 <= slot < t1:
            continue
        en.line(sc, CH_LEAD, slot, KEY_BASE, "ionian", _CELLS[cell],
                vel=vel, shift=shift, gate=0.97, jt=2, jv=3)
        en.cc_curve(sc, CH_LEAD, 11, [
            (slot - 0.25, 60), (slot + 1.5, 86), (slot + 4.0, 96),
            (slot + 6.35, 72), (slot + 6.9, 52)], step=0.5)
        if cell in ("A", "B"):        # vibrato blooms on the held last note
            en.vibrato(sc, CH_LEAD, slot + 4.6, 1.5, depth=0.16,
                       cycles_per_beat=1.3, delay=0.3)


def build_alarm(sc: en.Score) -> None:
    """I. The Alarm (0-16): the agogo clock, then the piano wakes."""
    sc.cc(CH_LEAD, 11, 70, 0.0)
    # First ring: 24 alternating 16ths, dying away.
    for k in range(24):
        p = _ALARM_HI if k % 2 == 0 else _ALARM_LO
        vel = round(en.lerp(96, 78, k / 23.0))
        sc.note(CH_ALARM, p, k * 0.25, 0.2, vel, jt=1, jv=2)
    # Snooze ring, fainter; one last dying pair.
    for k in range(8):
        p = _ALARM_HI if k % 2 == 0 else _ALARM_LO
        sc.note(CH_ALARM, p, 8.0 + k * 0.25, 0.2,
                round(en.lerp(74, 62, k / 7.0)), jt=1, jv=2)
    sc.note(CH_ALARM, _ALARM_HI, 12.0, 0.2, 58, jt=1, jv=2)
    sc.note(CH_ALARM, _ALARM_LO, 12.25, 0.2, 54, jt=1, jv=2)
    # The piano wakes: three bars of the tonic vamp, crescendo into II.
    lh = _lh_pitch(1)
    for t in (4.0, 8.0, 12.0):
        for e in range(8):
            vel = round(en.lerp(56, 74, (t + e * 0.5 - 4.0) / 11.5))
            for p in _RH[0]:
                sc.note(CH_PIANO, p, t + e * 0.5, 0.42, vel, jt=2, jv=3)
        sc.note(CH_PIANO, lh, t, 1.6, round(en.lerp(52, 68, (t - 4) / 8)),
                jt=2, jv=3)
        sc.note(CH_PIANO, lh, t + 2.0, 1.6,
                round(en.lerp(48, 64, (t - 4) / 8)), jt=2, jv=3)
    sc.note(CH_KIT, 42, 15.0, 0.1, 58, jt=1, jv=2)
    sc.note(CH_KIT, 42, 15.5, 0.1, 62, jt=1, jv=2)


def build_stairs(sc: en.Score) -> None:
    """II. Down the Stairs (16-120): the commute engine + flute gasps."""
    sc.note(CH_KIT, 49, 16.0, 1.5, 92, jt=1, jv=2)
    for b in range(0, 26):
        _groove_bar(sc, b)
    _phrases_in(sc, 16.0, 120.0)


def build_platform(sc: en.Score) -> None:
    """III. Platform Two (120-224): groove, the footsteps break, return."""
    for b in range(26, 52):
        in_break = 40 <= b < 44
        _groove_bar(sc, b, piano=not in_break, hats=not in_break,
                    bass_hush=in_break)
    # Brushed-snare footsteps, walk -> sprint (kit swaps to brush around
    # them via PART.PROGRAM_CHANGES).  Exact (jt=0/jv=0): the accelerando
    # IS the content.
    ts: list[float] = []
    t, ioi = 177.0, 1.0
    while t < 190.4:
        ts.append(t)
        t += ioi
        ioi = max(0.30, ioi * 0.88)
    for i, beat in enumerate(ts):
        key = 38 if i % 2 == 0 else 40
        vel = round(en.lerp(58, 96, i / (len(ts) - 1)))
        sc.note(CH_KIT, key, beat, 0.28, vel, jt=0, jv=0)
    # The train arrives: crash + station bell on the agogo, groove back.
    sc.note(CH_KIT, 49, 192.0, 1.5, 96, jt=1, jv=2)
    sc.note(CH_ALARM, 79, 192.0, 0.8, 78, jt=1, jv=2)
    sc.note(CH_ALARM, 75, 193.0, 0.8, 72, jt=1, jv=2)
    sc.note(CH_ALARM, 79, 194.0, 0.8, 68, jt=1, jv=2)
    _phrases_in(sc, 120.0, 224.0)


def build_doors(sc: en.Score) -> None:
    """IV. Doors Closing (224-272): whistle gliss + riser into the pivot."""
    for b in range(52, 64):
        _groove_bar(sc, b)
    _phrases_in(sc, 224.0, PIVOT)
    # Strings: a rising pad (Fm - Gm - Ab - Bb), then the departure
    # whistle — a true octave gliss on RPN bend-range 12, recentred.
    en.bend_range(sc, CH_STRINGS, 12, 224.0)
    prev = None
    for i, deg in enumerate((2, 3, 4, 5)):
        prev = en.voice_lead(en.triad(KEY_BASE, "ionian", deg), prev,
                             3, 55, 76)
        for p in prev:
            sc.note(CH_STRINGS, p, 240.0 + 4.0 * i, 3.85, 48 + 4 * i,
                    jt=3, jv=2)
    en.cc_curve(sc, CH_STRINGS, 11, [
        (224.0, 55), (240.0, 62), (252.0, 74), (256.0, 62),
        (258.0, 86), (261.5, 102), (263.0, 40)], step=0.5)
    sc.note(CH_STRINGS, 70, 256.0, 6.0, 88, jt=0, jv=0)
    en.bend_ramp(sc, CH_STRINGS, 256.0, 261.5, 0.0, 2.0, steps=22)
    sc.bend(CH_STRINGS, 263.75, 0.0)     # recentred before the riser lands
    # The reverse-cymbal riser: swells for eight beats, stops ON the pivot.
    sc.note(CH_RISER, 70, 264.0, 8.0, 98, jt=0, jv=0)


def build_lift(sc: en.Score) -> None:
    """V. The Lift (272-352): the whole-tone dream, hanging unresolved."""
    # The wordless choir climbs the whole-tone slope; vowel opens to 'ah'.
    for t, root, dur, vel in _DREAM_CHORDS:
        jt = 0 if t == PIVOT else 3     # the pivot chord lands ON the beat
        for p in (root - 12, root, root + 4, root + 8):
            sc.note(CH_CHOIR, p, t, dur, vel, jt=jt, jv=2)
    for p in _HANG:
        sc.note(CH_CHOIR, p, _HANG_T0, _HANG_RESTRIKE - _HANG_T0 - 0.2,
                68, jt=3, jv=2)
        sc.note(CH_CHOIR, p, _HANG_RESTRIKE, _HANG_OFF - _HANG_RESTRIKE,
                56, jt=3, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [
        (PIVOT, 45), (280.0, 86), (306.0, 96), (350.0, 96)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [
        (PIVOT, 58), (288.0, 80), (316.0, 86), (326.0, 78), (350.0, 24)],
        step=1.0)
    # Harp arpeggi ride each chord (every offset even: whole-tone closed).
    for t, root, _dur, _vel in _DREAM_CHORDS:
        pitches = [root + o for o in (-12, -8, -4, 0, 4, 8, 12)]
        en.arp(sc, CH_HARP, pitches, t + 0.5, count=12, step=0.5,
               vel=58, pattern="updown", gate=1.3)
        en.arp(sc, CH_HARP, pitches[3:], t + 4.0, count=8, step=0.25,
               vel=54, pattern="up", gate=1.2)
    # The final sweep into the hang, then afterglow droplets.
    sweep = list(range(53, 86, 4))            # F3 .. Db6, whole-tone rungs
    for i, p in enumerate(sweep):
        sc.note(CH_HARP, p, _HANG_T0 + i * 0.25, 1.2,
                round(en.lerp(64, 80, i / (len(sweep) - 1))), jt=2, jv=2)
    for beat, p, vel in ((330.0, 81, 50), (336.0, 77, 46),
                         (342.0, 85, 44), (345.0, 69, 42)):
        sc.note(CH_HARP, p, beat, 1.5, vel, jt=2, jv=2)
    # Celesta: the alarm remembered in 4x augmentation, fading; then one
    # breath of scored air (GAP_WHITELIST) and the last bell.
    for t, pits, vel in _BELL_MEMORIES:
        for i, p in enumerate(pits):
            sc.note(CH_BELLS, p, t + i * 1.0, 0.9, vel - 2 * i, jt=2, jv=2)
    sc.note(CH_BELLS, _LAST_BELL[1], _LAST_BELL[0], 2.0, _LAST_BELL[2],
            jt=2, jv=2)


BUILDERS: list = [build_alarm, build_stairs, build_platform, build_doors,
                  build_lift]
