"""t07_german_bight — Track 7 "German Bight" of *Through Lines*.

Disc 1, 'Lines of Descent'.  HLD section 3, T7: a gale crosses a sea
area, told as lines.  Three through-lines cross the storm arc:

* the BAROMETER — a dedicated English-horn lane whose successive
  phrase-pitches fall exactly one semitone per phrase, strictly
  monotonic, for the WHOLE first half (calm glass -> freshening ->
  Gale One): 29 readings, G5 down to Eb3, a literal falling trace.
  At dawn the trace turns and climbs three readings (A3 -> Bb3 -> B3).
* the SWELL — the storm rides 9/8 grouped 3+3+3: taiko on the three
  dotted-quarter wave-points of every gale bar, wave-crash cymbals on
  the downbeats, timpani rolls the length of each wave.
* the SIGNAL — in the eye's near-silence a coastal station taps
  "GERMAN BIGHT" on a tinkle bell, rhythm computed from
  material.morse_rhythm(material.MORSE_T7) and decoded back by oracle.

The dawn heals T4: the bridge chorale that Fault Lines kept cutting off
mid-phrase returns via material.play_chorale COMPLETE — all eight
chords, note-for-note against material.chorale_pitches — and the piece
ends on open fifths (D and A only, no third: neither grief nor triumph,
just first light).

Oracle-first: every headline claim below is a falsifiable check in
oracles() (written before the music) and the headline RENDER claims are
mirrored in audio_checks() as per-section RMS dB.  All jitter comes
from the Score's own SEED-seeded rng; a rebuild is byte-identical.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 7
TITLE = 'German Bight'
FILE = '07 - German Bight.mid'
SEED = 20260907

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_HI = 0        # high strings (glass, waves, sunrise pedal)      centred
CH_HARP = 1      # harp (calm arps, crest runs, dawn)              pan 54
CH_BARO = 2      # the barometer lane, english horn                centred
CH_BRASS = 3     # brass section surges + stabs                    centred
CH_TIMP = 4      # timpani rolls                                   pan 56
CH_TAIKO = 5     # taiko drum — the wave engine                    pan 72
CH_WIND = 6      # shakuhachi wind-voice                           centred
CH_FLUTE = 7     # the eye's lone flute; dawn descant              centred
CH_BELL = 8      # tinkle bell — the coastal station               pan 76
CH_KIT = 9       # kit v2: wave-crash cymbals, ride shimmer
CH_LO = 10       # low strings bed (floored at C2)                 centred
CH_CHOIR = 11    # storm vowels; the dawn chorale                  centred
CH_RISER = 12    # reverse cymbal risers into the gales            centred

MODE = "aeolian"
TONIC_HI = 62    # D4
TONIC_MID = 50   # D3
TONIC_LO = 38    # D2

# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

CALM_T0 = 0.0        # I.   4/4 @ 56          18 bars
FRESH_T0 = 72.0      # II.  9/8 accel 60->121 20 bars
GALE1_T0 = 162.0     # III. 9/8 @ 126         26 bars
EYE_T0 = 279.0       # IV.  4/4 @ 60          11 bars
GALE2_T0 = 323.0     # V.   9/8 @ 138         36 bars (34 loud + collapse)
DAWN_T0 = 485.0      # VI.  4/4 rit 58->50    16 bars
END = 549.0

BAR9 = 4.5
GALE1_BARS = 26
GALE2_BARS = 36
GALE2_LOUD = 34      # bars 34-35 are the collapse into dawn

BARO_TOP = 79                    # G5, the first reading
BARO_FALL_PHRASES = 29           # ends on Eb3 (79 - 28 = 51)
BARO_RISE = (57, 58, 59)         # the dawn readings, one semitone apart

MORSE_T0 = 285.0
MORSE_UNIT = 0.25

CHORALE_T0 = 493.0
CHORALE_ROOT = 62                # the hymn on D, as T4 left it
CHORALE_BEATS = 3.0

DAWN_Q = 16.0                    # dawn decrescendo quarters

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Calm Glass", CALM_T0, FRESH_T0),
        ("II. Freshening", FRESH_T0, GALE1_T0),
        ("III. Gale One", GALE1_T0, EYE_T0),
        ("IV. The Eye", EYE_T0, GALE2_T0),
        ("V. Gale Two", GALE2_T0, DAWN_T0),
        ("VI. Dawn - the Chorale Unbroken", DAWN_T0, END),
    ],
    tempo_map=[
        (0.0, 56.0),
        (72.0, 60.0), (81.0, 66.0), (90.0, 72.0), (99.0, 80.0),
        (108.0, 88.0), (117.0, 96.0), (126.0, 104.0), (135.0, 110.0),
        (144.0, 116.0), (153.0, 121.0),
        (162.0, 126.0),
        (279.0, 60.0),
        (323.0, 138.0),
        (485.0, 58.0), (517.0, 54.0), (533.0, 50.0),
    ],
    time_signatures=[
        (0.0, 4, 4), (72.0, 9, 8), (279.0, 4, 4), (323.0, 9, 8),
        (485.0, 4, 4),
    ],
    keysigs=[(0.0, -1, 1), (517.0, 2, 0)],
    channels=[
        (CH_HI, "high strings", 49, 96, 64, 60),
        (CH_HARP, "harp", 46, 100, 54, 50),
        (CH_BARO, "barometer (english horn)", 69, 92, 64, 45),
        (CH_BRASS, "brass", 61, 100, 64, 42),
        (CH_TIMP, "timpani", 47, 104, 56, 50),
        (CH_TAIKO, "taiko", 116, 108, 72, 45),
        (CH_WIND, "wind (shakuhachi)", 77, 95, 64, 55),
        (CH_FLUTE, "flute", 73, 96, 64, 55),
        (CH_BELL, "signal bell", 112, 100, 76, 60),
        (CH_KIT, "kit", 0, 100, 64, 45),
        (CH_LO, "low strings", 48, 100, 64, 50),
        (CH_CHOIR, "choir", 52, 100, 64, 62),
        (CH_RISER, "riser (reverse cymbal)", 119, 95, 64, 55),
    ],
    program_changes=[(CH_KIT, 0.0, 1)],       # any non-zero = v2 kit
    extra_markers=[
        (MORSE_T0, "the signal: GERMAN BIGHT"),
        (CHORALE_T0, "the chorale, unbroken"),
        (533.0, "open fifths at sunrise"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {46, 47, 48, 49, 52, 61, 69, 73, 77,
                               112, 116, 119}
CENTERED_CHANNELS: set[int] = {CH_HI, CH_BARO, CH_BRASS, CH_WIND, CH_FLUTE,
                               CH_LO, CH_CHOIR, CH_RISER}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_HI: (55, 92),
    CH_HARP: (44, 90),
    CH_BARO: (50, 80),
    CH_BRASS: (46, 80),
    CH_TIMP: (36, 57),
    CH_TAIKO: (36, 55),
    CH_WIND: (55, 88),
    CH_FLUTE: (70, 90),
    CH_BELL: (74, 98),
    CH_LO: (36, 60),
    CH_CHOIR: (48, 84),
    CH_RISER: (48, 84),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (372.0, 392.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

COMMENT = ("Track 07 of 'Through Lines': a gale crosses the German Bight. "
           "A barometer lane falls one semitone per reading for the whole "
           "first half; the swell rides 9/8 in threes; a coastal station "
           "taps GERMAN BIGHT in Morse inside the eye; and the bridge "
           "chorale that Fault Lines kept interrupting returns unbroken "
           "at dawn, ending on open fifths.")


# ===========================================================================
# ORACLES — written before the music; the movements below are composed
# to make every one of these checks pass.
# ===========================================================================

def _spans(sc, ch):
    """[(on, off, pitch, vel)] with FIFO on/off pairing, sorted by onset."""
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


def _groups(notes, gap: float = 3.0):
    """Split onset-sorted notes into phrases at onset gaps > `gap` beats."""
    out: list[list] = []
    for nt in notes:
        if out and nt[0] - out[-1][-1][0] <= gap:
            out[-1].append(nt)
        else:
            out.append([nt])
    return out


def _ons(sc, ch, t0=-1e12, t1=1e12):
    return [nt for nt in _spans(sc, ch) if t0 <= nt[0] < t1]


def _o_barometer_falls(sc):
    """29 phrases before the eye, each exactly one semitone below the
    last (strictly monotonic), spanning all three storm-side movements;
    the lane is silent from the eye until dawn."""
    fails = []
    groups = _groups(_ons(sc, CH_BARO, t1=EYE_T0))
    anchors = [g[-1][2] for g in groups]
    want = list(range(BARO_TOP, BARO_TOP - BARO_FALL_PHRASES, -1))
    if anchors != want:
        fails.append(f"first-half anchors {anchors} != chromatic descent "
                     f"{want[0]}..{want[-1]} ({len(want)} phrases)")
    starts = [g[0][0] for g in groups]
    for name, lo, hi in (("calm", CALM_T0, FRESH_T0),
                         ("freshening", FRESH_T0, GALE1_T0),
                         ("gale one", GALE1_T0, EYE_T0)):
        if not any(lo <= s < hi for s in starts):
            fails.append(f"no barometer reading inside {name}")
    if starts and starts[-1] < EYE_T0 - 12.0:
        fails.append(f"trace stops at beat {starts[-1]:.1f}, well short "
                     f"of the eye ({EYE_T0})")
    stray = _ons(sc, CH_BARO, EYE_T0, DAWN_T0)
    if stray:
        fails.append(f"{len(stray)} barometer notes during the eye/gale "
                     f"two (the glass has bottomed out)")
    return fails


def _o_barometer_rises(sc):
    """At dawn the trace turns: three readings, one semitone up each."""
    fails = []
    groups = _groups(_ons(sc, CH_BARO, DAWN_T0, END))
    anchors = [g[-1][2] for g in groups]
    if anchors != list(BARO_RISE):
        fails.append(f"dawn anchors {anchors} != rising {list(BARO_RISE)}")
    return fails


def _o_swell(sc):
    """9/8 grouped 3+3+3: taiko marks all three dotted-quarter wave-points
    in >= 85% of gale bars; wave-crash cymbals ride the downbeats."""
    fails = []
    taiko = [nt[0] for nt in _spans(sc, CH_TAIKO)]
    crashes = [nt[0] for nt in _spans(sc, CH_KIT) if nt[2] in (49, 52, 55, 57)]
    for name, g_t0, bars, min_crash in (
            ("gale one", GALE1_T0, GALE1_BARS, 16),
            ("gale two", GALE2_T0, GALE2_BARS, 20)):
        full = 0
        crash_bars = 0
        for b in range(bars):
            t = g_t0 + BAR9 * b
            if all(any(abs(on - (t + off)) < 0.12 for on in taiko)
                   for off in (0.0, 1.5, 3.0)):
                full += 1
            if any(abs(on - t) < 0.12 for on in crashes):
                crash_bars += 1
        if full < 0.85 * bars:
            fails.append(f"{name}: only {full}/{bars} bars carry the "
                         f"3+3+3 taiko wave grouping")
        if crash_bars < min_crash:
            fails.append(f"{name}: wave-crash cymbals on only "
                         f"{crash_bars} downbeats (want >= {min_crash})")
    return fails


def _o_morse(sc):
    """The eye's bell decodes to GERMAN BIGHT (standard Morse timing)."""
    rev = {v: k for k, v in material.MORSE_TABLE.items()}
    notes = _ons(sc, CH_BELL, EYE_T0, GALE2_T0)
    if not notes:
        return ["no signal-bell notes inside the eye"]
    decoded = ""
    cur = ""
    for i, (on, off, _p, _v) in enumerate(notes):
        cur += "." if (off - on) < 2 * MORSE_UNIT else "-"
        if i + 1 < len(notes):
            gapv = notes[i + 1][0] - off
            if gapv > 5 * MORSE_UNIT:
                decoded += rev.get(cur, "?") + " "
                cur = ""
            elif gapv > 2 * MORSE_UNIT:
                decoded += rev.get(cur, "?")
                cur = ""
    decoded += rev.get(cur, "?")
    if decoded != material.MORSE_T7:
        return [f"eye bell decodes to {decoded!r}, not "
                f"{material.MORSE_T7!r}"]
    return []


def _o_chorale(sc):
    """The T4 bridge chorale returns COMPLETE: all eight chords on the
    dawn grid, note-for-note from material.chorale_pitches, untruncated,
    and nothing else on the choir channel inside the statement."""
    fails = []
    want = material.chorale_pitches(CHORALE_ROOT)
    w0 = CHORALE_T0 - 0.2
    w1 = CHORALE_T0 + len(want) * CHORALE_BEATS + 0.2
    notes = _ons(sc, CH_CHOIR, w0, w1)
    if len(notes) != 4 * len(want):
        fails.append(f"{len(notes)} choir notes in the chorale window, "
                     f"want {4 * len(want)} (8 chords x SATB, no extras)")
    for i, chord in enumerate(want):
        t = CHORALE_T0 + i * CHORALE_BEATS
        got = sorted(p for on, _off, p, _v in notes if abs(on - t) <= 0.2)
        if got != sorted(chord):
            fails.append(f"chord {i + 1} at beat {t:.0f}: {got} != "
                         f"{sorted(chord)} (material.chorale_pitches)")
    return fails


def _o_open_fifths(sc):
    """The final sonority is an open fifth: pitch classes D and A only."""
    allnotes = [nt for ch in sc.events for nt in _spans(sc, ch)]
    if not allnotes:
        return ["the piece is silent"]
    max_off = max(off for _on, off, _p, _v in allnotes)
    final = [nt for nt in allnotes if nt[1] >= max_off - 0.5]
    pcs = {p % 12 for _on, _off, p, _v in final}
    fails = []
    if pcs != {2, 9}:
        fails.append(f"final sonority pitch classes {sorted(pcs)} != "
                     f"[2, 9] (D and A, no third)")
    if len(final) < 4:
        fails.append(f"only {len(final)} voices hold to the end")
    return fails


def _energy(sc):
    notes = [nt for ch in sc.events for nt in _spans(sc, ch)]

    def per_beat(t0, t1):
        return sum(v for on, _off, _p, v in notes
                   if t0 <= on < t1) / (t1 - t0)
    return per_beat


def _o_storm_arc(sc):
    """check_arc: calm < freshening < gale1 < gale2 == max;
    eye <= 0.25 x gale1; dawn quarters non-increasing to <= half."""
    e = _energy(sc)
    calm = e(CALM_T0, FRESH_T0)
    fresh = e(FRESH_T0, GALE1_T0)
    g1 = e(GALE1_T0, EYE_T0)
    eye = e(EYE_T0, GALE2_T0)
    g2 = e(GALE2_T0, DAWN_T0)
    dawn = e(DAWN_T0, END)
    fails = []
    if not calm < fresh < g1 < g2:
        fails.append(f"no storm build: {calm:.0f} -> {fresh:.0f} -> "
                     f"{g1:.0f} -> {g2:.0f} must strictly rise")
    peak = max(calm, fresh, g1, eye, g2, dawn)
    if g2 < peak:
        fails.append(f"gale two ({g2:.0f}) is not the maximum ({peak:.0f})")
    if eye > 0.25 * g1:
        fails.append(f"the eye ({eye:.0f}) is not near-silence "
                     f"(must be <= 0.25 x gale one {g1:.0f})")
    qs = [e(DAWN_T0 + DAWN_Q * k, DAWN_T0 + DAWN_Q * (k + 1))
          for k in range(4)]
    if any(b > a + 1e-9 for a, b in zip(qs, qs[1:])):
        fails.append(f"dawn quarters {[f'{q:.0f}' for q in qs]} must be "
                     f"non-increasing (decrescendo)")
    if qs[3] > 0.5 * qs[0]:
        fails.append(f"dawn tail ({qs[3]:.0f}) must fade to <= half of "
                     f"its first quarter ({qs[0]:.0f})")
    return fails


def _o_wind_rises(sc):
    """Freshening: ten wind breaths whose held pitches strictly rise,
    spanning at least an octave."""
    fails = []
    groups = _groups(_ons(sc, CH_WIND, FRESH_T0, GALE1_T0))
    anchors = [max(g, key=lambda nt: nt[1] - nt[0])[2] for g in groups]
    if len(anchors) != 10:
        fails.append(f"{len(anchors)} wind breaths, want 10")
    if any(b <= a for a, b in zip(anchors, anchors[1:])):
        fails.append(f"wind anchors {anchors} must strictly rise")
    if anchors and anchors[-1] - anchors[0] < 12:
        fails.append(f"wind rise spans {anchors[-1] - anchors[0]} "
                     f"semitones, want >= 12")
    return fails


def _o_instrumentation(sc):
    """Calm is harp + high strings only; each gale carries timpani ROLLS
    (>= 10 consecutive strokes at <= 0.3 beats), taiko and brass; the
    eye silences every storm lane."""
    fails = []
    for ch, name in ((CH_BRASS, "brass"), (CH_TIMP, "timpani"),
                     (CH_TAIKO, "taiko"), (CH_KIT, "kit"),
                     (CH_CHOIR, "choir"), (CH_WIND, "wind"),
                     (CH_FLUTE, "flute"), (CH_BELL, "bell"),
                     (CH_RISER, "riser")):
        n = len(_ons(sc, ch, CALM_T0, FRESH_T0))
        if n:
            fails.append(f"calm glass must not contain {name} ({n} notes)")
    if len(_ons(sc, CH_HARP, CALM_T0, FRESH_T0)) < 20:
        fails.append("calm glass wants its harp (>= 20 notes)")
    if len(_ons(sc, CH_HI, CALM_T0, FRESH_T0)) < 10:
        fails.append("calm glass wants its high strings (>= 10 notes)")
    for name, t0, t1 in (("gale one", GALE1_T0, EYE_T0),
                         ("gale two", GALE2_T0, DAWN_T0)):
        ons = [nt[0] for nt in _ons(sc, CH_TIMP, t0, t1)]
        run = best = 1
        for a, b in zip(ons, ons[1:]):
            run = run + 1 if b - a <= 0.3 else 1
            best = max(best, run)
        if best < 10:
            fails.append(f"{name}: no timpani roll (longest run {best})")
        if len(_ons(sc, CH_TAIKO, t0, t1)) < 60:
            fails.append(f"{name}: taiko underpowered")
        if len(_ons(sc, CH_BRASS, t0, t1)) < 60:
            fails.append(f"{name}: brass underpowered")
    for ch, name in ((CH_BRASS, "brass"), (CH_TIMP, "timpani"),
                     (CH_TAIKO, "taiko"), (CH_KIT, "kit"),
                     (CH_CHOIR, "choir"), (CH_LO, "low strings"),
                     (CH_HARP, "harp"), (CH_WIND, "wind")):
        n = len(_ons(sc, ch, EYE_T0, 317.4))
        if n:
            fails.append(f"the eye must silence {name} ({n} notes)")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("barometer_falls", _o_barometer_falls(sc)),
        ("barometer_rises_at_dawn", _o_barometer_rises(sc)),
        ("swell_3plus3plus3", _o_swell(sc)),
        ("morse_german_bight", _o_morse(sc)),
        ("chorale_unbroken", _o_chorale(sc)),
        ("open_fifth_sunrise", _o_open_fifths(sc)),
        ("storm_arc", _o_storm_arc(sc)),
        ("wind_rises", _o_wind_rises(sc)),
        ("storm_instrumentation", _o_instrumentation(sc)),
    ]


def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """Render-side mirrors of the headline claims (per-section RMS dB)."""
    def win_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    calm = win_db(CALM_T0, FRESH_T0)
    fresh = win_db(FRESH_T0, GALE1_T0)
    g1 = win_db(GALE1_T0, EYE_T0)
    eye = win_db(283.0, 321.0)          # inset past the gale's reverb tail
    g2 = win_db(GALE2_T0, 476.0)        # the storm proper, pre-collapse
    dawn = win_db(DAWN_T0, END)
    dawn1 = win_db(DAWN_T0, DAWN_T0 + DAWN_Q)
    dawn4 = win_db(533.0, 548.0)

    arc = []
    if not calm + 1.0 <= fresh:
        arc.append(f"freshening {fresh:.1f} dB not above calm {calm:.1f}")
    if not fresh + 2.0 <= g1:
        arc.append(f"gale one {g1:.1f} dB not above freshening {fresh:.1f}")
    if not g1 + 0.5 <= g2:
        arc.append(f"gale two {g2:.1f} dB not above gale one {g1:.1f}")
    for name, v in (("calm", calm), ("freshening", fresh),
                    ("gale one", g1), ("the eye", eye), ("dawn", dawn)):
        if v >= g2:
            arc.append(f"gale two {g2:.1f} dB is not the peak "
                       f"({name} = {v:.1f} dB)")
    hush = []
    if not eye <= g1 - 12.0:
        hush.append(f"the eye ({eye:.1f} dB) is not >= 12 dB below "
                    f"gale one ({g1:.1f} dB)")
    fade = []
    if not dawn4 <= dawn1 - 6.0:
        fade.append(f"dawn does not fade: last quarter {dawn4:.1f} dB vs "
                    f"first {dawn1:.1f} dB (want >= 6 dB down)")
    return [("audio_storm_arc", arc), ("audio_eye_hush", hush),
            ("audio_dawn_fade", fade)]


# ===========================================================================
# THE MUSIC — composed to pass the oracles above.
# ===========================================================================

# Harmonic rhythm (aeolian degrees on D).
CALM_PROG = (1, 6, 3, 7, 1, 4, 6, 5, 1)                    # 9 x 8 beats
FRESH_PROG = (1, 6, 7, 1, 4, 6, 7, 5, 5, 1)                # 10 x 2 bars
GALE1_PROG = (1, 1, 7, 6, 1, 5, 6, 7, 1, 4, 4, 5, 1)       # 13 x 2 bars
GALE2_PROG = (1, 1, 7, 7, 6, 6, 1, 1, 5, 5, 6, 6, 4, 4,
              7, 7, 5, 1)                                  # 18 x 2 bars

WAVE_MID = (0, 1, 2, 3, 4, 5, 4, 3, 2)     # nine eighths, one 9/8 bar
WAVE_WIDE = (0, 2, 4, 5, 7, 8, 7, 5, 4)

WIND_LINE = (62, 64, 65, 67, 69, 70, 72, 74, 76, 77)   # D4 .. F5


def _low_root(deg: int) -> int:
    p = en.pitch(TONIC_LO, MODE, deg)
    return p + 12 if p < 36 else p


def _baro_fall_times():
    ts = ([4.0 + 12.0 * i for i in range(6)] +          # calm, every 3 bars
          [74.0 + 9.0 * i for i in range(10)] +          # freshening, 2 bars
          [164.0 + 9.0 * i for i in range(13)])          # gale one, 2 bars
    return [(t, BARO_TOP - k) for k, t in enumerate(ts)]


def _barometer(sc: en.Score, a: int, b: int) -> None:
    """Readings a..b-1 of the falling trace: the old level, then the new
    level a semitone below — the pen ticking down the drum."""
    phrases = _baro_fall_times()
    hi = len(phrases) - 1
    for k in range(a, b):
        t, anchor = phrases[k]
        vel = int(en.lerp(48, 84, k / hi))
        if k > 0:
            sc.note(CH_BARO, anchor + 1, t, 0.7, max(40, vel - 8),
                    jt=3, jv=2)
            sc.note(CH_BARO, anchor, t + 0.75, 2.2, vel, jt=3, jv=2)
        else:
            sc.note(CH_BARO, anchor, t, 2.6, vel, jt=3, jv=2)


def _timp_roll(sc: en.Score, t0: float, t1: float, pitch: int,
               v0: int, v1: int) -> None:
    steps = int(round((t1 - t0) / 0.25))
    for i in range(steps):
        sc.note(CH_TIMP, pitch, t0 + 0.25 * i, 0.22,
                int(en.lerp(v0, v1, i / max(1, steps - 1))), jt=2, jv=3)


def _timp_bar(sc: en.Score, t: float, pitch: int, base: int,
              accent: int) -> None:
    """One 9/8 bar: downbeat accent, then a rolling arch under the wave."""
    sc.note(CH_TIMP, pitch, t, 0.24, accent, jt=2, jv=3)
    for i in range(1, 18):
        b = 0.25 * i
        sc.note(CH_TIMP, pitch, t + b, 0.22,
                int(base + 16 * math.sin(math.pi * b / 4.5)), jt=2, jv=3)


def _taiko_bar(sc: en.Score, t: float, vel: int, sub: bool) -> None:
    """The 3+3+3 wave-points (D2 A2 G2), plus subdivision knocks."""
    sc.note(CH_TAIKO, 38, t, 0.45, vel, jt=2, jv=3)
    sc.note(CH_TAIKO, 45, t + 1.5, 0.45, vel - 8, jt=2, jv=3)
    sc.note(CH_TAIKO, 43, t + 3.0, 0.45, vel - 5, jt=2, jv=3)
    if sub:
        for off, dv in ((0.5, -32), (2.0, -30), (3.5, -26), (4.0, -22)):
            sc.note(CH_TAIKO, 50, t + off, 0.3, max(30, vel + dv),
                    jt=2, jv=3)


def _wave_bar(sc: en.Score, ch: int, t: float, shape, deg: int,
              vel: int) -> None:
    for i, o in enumerate(shape):
        v = vel + (7 if i in (0, 3, 6) else 0)
        sc.note(ch, en.pitch(TONIC_HI, MODE, deg + o), t + 0.5 * i, 0.48,
                v, jt=3, jv=3)


# ---------------------------------------------------------------------------
# I. Calm Glass (0-72) — harp and high strings on a windless sea; the
# barometer takes its first six readings, already falling.
# ---------------------------------------------------------------------------

def build_calm(sc: en.Score) -> None:
    for chn, v in ((CH_HI, 82), (CH_LO, 78), (CH_HARP, 104), (CH_BARO, 92)):
        sc.cc(chn, 11, v, 0.0)
    sc.cc(CH_HI, 74, 66, 0.0)                    # glassy brightness
    chords = [en.triad(TONIC_HI, MODE, d) for d in CALM_PROG]
    en.pad_block(sc, CH_HI, 0.0, chords, 8.0, size=4, lo=64, hi=84,
                 vel=42, vel_end=50)
    en.expr_curve(sc, CH_HI, [(0.0, 74), (12.0, 82), (24.0, 76),
                              (36.0, 84), (48.0, 78), (60.0, 86),
                              (71.5, 82)], step=1.0)
    for i in range(2, len(CALM_PROG)):           # low bed from bar 5
        sc.note(CH_LO, _low_root(CALM_PROG[i]), 8.0 * i, 7.9, 40 + i,
                jt=4, jv=2)
    for i, d in enumerate(CALM_PROG):
        tri = en.triad(TONIC_MID, MODE, d)
        en.arp(sc, CH_HARP, tri + [p + 12 for p in tri], 8.0 * i, 8, 1.0,
               46 + i, pattern="updown", gate=1.8)
    _barometer(sc, 0, 6)


# ---------------------------------------------------------------------------
# II. Freshening (72-162) — 9/8 arrives; the wind-voice climbs an
# octave-plus in ten breaths; distant thunder; ten more readings.
# ---------------------------------------------------------------------------

def build_fresh(sc: en.Score) -> None:
    t0 = FRESH_T0
    chords = [en.triad(TONIC_HI, MODE, d) for d in FRESH_PROG[:5]]
    en.pad_block(sc, CH_HI, t0, chords, 9.0, size=4, lo=62, hi=83,
                 vel=50, vel_end=58)
    en.expr_curve(sc, CH_HI, [(t0, 80), (t0 + 45.0, 88), (t0 + 89.5, 96)],
                  step=2.0)
    for b in range(10, 20):                      # the first true waves
        t = t0 + BAR9 * b
        _wave_bar(sc, CH_HI, t, WAVE_MID, FRESH_PROG[b // 2],
                  int(en.lerp(50, 64, (b - 10) / 9)))
    for b in range(20):
        t = t0 + BAR9 * b
        p = _low_root(FRESH_PROG[b // 2])
        vel = int(en.lerp(44, 66, b / 19))
        for off in (0.0, 1.5, 3.0):
            sc.note(CH_LO, p, t + off, 1.35, vel, jt=3, jv=3)
    for i, d in enumerate(FRESH_PROG):
        tri = en.triad(TONIC_MID, MODE, d)
        en.arp(sc, CH_HARP, tri + [p + 12 for p in tri], t0 + 9.0 * i, 18,
               0.5, 50 + i, pattern="updown", gate=1.6, accent_every=3,
               accent=8)
    for i, p in enumerate(WIND_LINE):            # the wind rises
        t = t0 + 9.0 * i
        vel = int(en.lerp(50, 72, i / 9))
        main = t
        if i >= 4:
            sc.note(CH_WIND, p - 5, t, 0.35, vel - 12, jt=3, jv=2)
            sc.note(CH_WIND, p - 2, t + 0.35, 0.35, vel - 8, jt=3, jv=2)
            main = t + 0.7
        sc.note(CH_WIND, p, main, 7.0 - (main - t), vel, jt=3, jv=2)
        en.cc_curve(sc, CH_WIND, 11, [(t, 38), (t + 3.5, 88),
                                      (t + 7.0, 44)], step=0.5)
    en.cc_curve(sc, CH_WIND, 1, [(t0, 0), (t0 + 90.0, 42)], step=4.0)
    for b in (12, 14, 16, 18):                   # distant thunder
        t = t0 + BAR9 * b
        _timp_roll(sc, t + 2.0, t + 4.4, 50, 26, 52)
    for b in range(12, 20):
        t = t0 + BAR9 * b
        for off in (0.0, 1.5, 3.0):
            sc.hit(51, t + off, int(en.lerp(30, 44, (b - 12) / 7)))
    sc.hit(49, t0 + BAR9 * 16, 38)
    sc.hit(49, t0 + BAR9 * 18, 46)
    sc.note(CH_RISER, 60, t0 + 85.5, 4.4, 72, jt=2, jv=3)   # into Gale One
    _barometer(sc, 6, 16)


# ---------------------------------------------------------------------------
# III. Gale One (162-279) — the full storm engine: timpani rolls the
# length of every wave, taiko on the 3+3+3, brass surges and stabs,
# crash downbeats.  Thirteen more readings, all the way down.
# ---------------------------------------------------------------------------

def build_gale1(sc: en.Score) -> None:
    t0 = GALE1_T0
    prev = None
    hi = len(GALE1_PROG) - 1
    for pair, d in enumerate(GALE1_PROG):
        t = t0 + 9.0 * pair
        prev = en.voice_lead(en.triad(TONIC_MID, MODE, d), prev, 3, 53, 74)
        vel = int(en.lerp(78, 92, pair / hi))
        for p in prev:
            sc.note(CH_BRASS, p, t, 4.4, vel, jt=3, jv=3)
        for off in (6.0, 7.5):
            for p in prev:
                sc.note(CH_BRASS, p, t + off, 0.45, vel + 8, jt=2, jv=3)
        en.cc_curve(sc, CH_BRASS, 11, [(t, 58), (t + 2.0, 98),
                                       (t + 4.4, 74), (t + 5.8, 92),
                                       (t + 8.5, 80)], step=0.5)
    for b in range(GALE1_BARS):
        t = t0 + BAR9 * b
        x = b / (GALE1_BARS - 1)
        d = GALE1_PROG[b // 2]
        _taiko_bar(sc, t, int(en.lerp(92, 106, x)), sub=(b % 2 == 1))
        _timp_bar(sc, t, 45 if d in (5, 7) else 50,
                  int(en.lerp(42, 58, x)), int(en.lerp(86, 100, x)))
        _wave_bar(sc, CH_HI, t, WAVE_MID, d, int(en.lerp(66, 80, x)))
        p = _low_root(d)
        for off in (0.0, 1.5, 3.0):
            sc.note(CH_LO, p, t + off, 1.35, int(en.lerp(70, 82, x)),
                    jt=3, jv=3)
        sc.hit(49 if b % 2 == 0 else 57, t, int(en.lerp(90, 102, x)))
        if b % 4 == 3:
            sc.hit(52, t + 3.0, 88)
        for off in (0.75, 2.25, 3.75):
            sc.hit(51, t + off, 46)
    for b in (2, 6, 10, 14, 18, 22):             # gusts
        t = t0 + BAR9 * b + 2.5
        for i, p in enumerate((69, 72, 74, 77)):
            sc.note(CH_WIND, p, t + 0.25 * i, 0.24, 70 + 3 * i, jt=2, jv=2)
        sc.note(CH_WIND, 81, t + 1.0, 2.4, 82, jt=2, jv=2)
    en.cc_curve(sc, CH_WIND, 11, [(t0, 72), (t0 + 116.0, 90)], step=4.0)
    en.expr_curve(sc, CH_HI, [(t0, 92), (t0 + 116.5, 100)], step=4.0)
    for b in (7, 15, 23):                        # harp spray off the crests
        t = t0 + BAR9 * b + 3.0
        for i in range(8):
            sc.note(CH_HARP, en.pitch(TONIC_HI, MODE, 1 + i), t + 0.25 * i,
                    0.35, int(en.lerp(66, 80, i / 7)), jt=2, jv=3)
    _barometer(sc, 16, BARO_FALL_PHRASES)


# ---------------------------------------------------------------------------
# IV. The Eye (279-323) — near-silence: one glassy string pedal, one
# lone flute, and the coastal station tapping GERMAN BIGHT.
# ---------------------------------------------------------------------------

def build_eye(sc: en.Score) -> None:
    t0 = EYE_T0
    sc.cc(CH_HI, 11, 46, t0)
    sc.note(CH_HI, 86, t0, 23.0, 28, jt=0, jv=2)
    sc.note(CH_HI, 81, t0 + 21.0, 23.0, 26, jt=3, jv=2)
    for on, dur in material.morse_rhythm(material.MORSE_T7, MORSE_UNIT):
        sc.note(CH_BELL, 86, MORSE_T0 + on, dur * 0.9, 54, jt=2, jv=2)
    sc.cc(CH_FLUTE, 11, 58, t0)
    for p, t, dur, vel in ((77, 282.0, 3.0, 46), (74, 286.5, 2.5, 44),
                           (81, 291.0, 3.5, 48), (79, 296.5, 3.0, 46),
                           (76, 302.0, 3.5, 44), (74, 307.5, 4.5, 42),
                           (74, 316.0, 5.0, 40)):
        sc.note(CH_FLUTE, p, t, dur, vel, jt=3, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [(282.0, 52), (291.0, 70), (302.0, 58),
                                   (316.0, 64), (321.0, 40)], step=1.0)
    sc.note(CH_RISER, 60, 317.5, 5.4, 86, jt=2, jv=3)       # the wall returns


# ---------------------------------------------------------------------------
# V. Gale Two (323-485) — bigger: four-voice brass, storm choir vowels,
# subdivision taiko every bar, splash and china, then the collapse.
# ---------------------------------------------------------------------------

def build_gale2(sc: en.Score) -> None:
    t0 = GALE2_T0
    prev_b = None
    prev_c = None
    for pair, d in enumerate(GALE2_PROG[:17]):
        t = t0 + 9.0 * pair
        x = pair / 16
        prev_b = en.voice_lead(en.triad(TONIC_MID, MODE, d), prev_b,
                               4, 51, 75)
        vel = int(en.lerp(88, 102, x))
        for p in prev_b:
            sc.note(CH_BRASS, p, t, 4.4, vel, jt=3, jv=3)
        for off in (4.5, 6.0, 7.5):
            for p in prev_b:
                sc.note(CH_BRASS, p, t + off, 0.45, min(112, vel + 10),
                        jt=2, jv=3)
        en.cc_curve(sc, CH_BRASS, 11, [(t, 66), (t + 2.0, 104),
                                       (t + 4.4, 82), (t + 5.8, 100),
                                       (t + 8.5, 86)], step=0.5)
    for k in range(7):                           # the choir joins the storm
        t = t0 + BAR9 * 6 + 18.0 * k
        d = GALE2_PROG[3 + 2 * k]
        prev_c = en.voice_lead(en.triad(TONIC_MID, MODE, d), prev_c,
                               4, 55, 79)
        vel = int(en.lerp(80, 94, k / 6))
        for p in prev_c:
            sc.note(CH_CHOIR, p, t, 17.5, vel, jt=4, jv=3)
        en.vowel_curve(sc, CH_CHOIR, [(t, 35), (t + 9.0, 96),
                                      (t + 17.5, 55)], step=1.0)
        en.cc_curve(sc, CH_CHOIR, 11, [(t, 72), (t + 9.0, 102),
                                       (t + 17.5, 76)], step=1.0)
    for b in range(GALE2_LOUD):
        t = t0 + BAR9 * b
        x = b / (GALE2_LOUD - 1)
        d = GALE2_PROG[b // 2]
        _taiko_bar(sc, t, int(en.lerp(100, 114, x)), sub=True)
        _timp_bar(sc, t, 45 if d in (5, 7) else 50,
                  int(en.lerp(52, 66, x)), int(en.lerp(96, 110, x)))
        _wave_bar(sc, CH_HI, t, WAVE_WIDE, d, int(en.lerp(76, 90, x)))
        p = _low_root(d)
        for off in (0.0, 1.5, 3.0):
            sc.note(CH_LO, p, t + off, 1.35, int(en.lerp(78, 90, x)),
                    jt=3, jv=3)
        sc.note(CH_LO, en.pitch(TONIC_LO, MODE, d + 4), t + 4.0, 0.4,
                int(en.lerp(70, 82, x)), jt=2, jv=3)
        sc.hit(49 if b % 2 == 0 else 57, t, int(en.lerp(98, 110, x)))
        if b % 2 == 1:
            sc.hit(52, t + 3.0, 94)
        if b % 4 == 2:
            sc.hit(55, t + 1.5, 80)
        for off in (0.75, 2.25, 3.75):
            sc.hit(51, t + off, 50)
    for pb in (4, 8, 12, 16):                    # wind shrieks
        t = t0 + 9.0 * pb
        sc.note(CH_WIND, 81, t, 6.0, 84, jt=3, jv=2)
        en.cc_curve(sc, CH_WIND, 11, [(t, 60), (t + 3.0, 96),
                                      (t + 6.0, 62)], step=0.5)
    for b in (5, 11, 17, 23, 29):                # spray off the big crests
        t = t0 + BAR9 * b + 3.0
        for i in range(10):
            sc.note(CH_HARP, en.pitch(TONIC_MID, MODE, 1 + 2 * i),
                    t + 0.15 * i, 0.3, int(en.lerp(70, 86, i / 9)),
                    jt=2, jv=3)
    en.expr_curve(sc, CH_HI, [(t0, 96), (t0 + 148.5, 104)], step=4.0)
    sc.note(CH_RISER, 60, t0 + 148.5, 4.4, 82, jt=2, jv=3)  # the last wave
    tc = t0 + BAR9 * GALE2_LOUD                  # 476: the wave breaks
    sc.hit(57, tc, 100)
    sc.hit(49, tc, 92)
    _timp_roll(sc, tc, tc + 8.5, 50, 80, 26)
    sc.note(CH_LO, 38, tc, 8.9, 56, jt=3, jv=2)


# ---------------------------------------------------------------------------
# VI. Dawn (485-549) — the chorale returns unbroken; the barometer
# turns; open fifths at sunrise.  A single long decrescendo.
# ---------------------------------------------------------------------------

def build_dawn(sc: en.Score) -> None:
    t0 = DAWN_T0
    # the storm-tail (dawn quarter 1)
    _timp_roll(sc, t0, t0 + 5.0, 50, 50, 22)
    sc.note(CH_LO, 38, t0, 7.9, 48, jt=3, jv=2)
    for p in (62, 65, 69, 74):
        sc.note(CH_HI, p, t0, 7.8, 44, jt=4, jv=3)
    en.expr_curve(sc, CH_HI, [(t0, 70), (t0 + 8.0, 58)], step=1.0)
    for i, p in enumerate((74, 69, 65, 62, 57, 53, 50)):
        sc.note(CH_HARP, p, t0 + 0.6 * i, 1.4, 52 - i, jt=3, jv=2)
    # the chorale, unbroken — all eight chords, note-for-note
    material.play_chorale(sc, CH_CHOIR, CHORALE_T0, CHORALE_ROOT,
                          chord_beats=CHORALE_BEATS, vel=62)
    en.vowel_curve(sc, CH_CHOIR, [(CHORALE_T0, 25), (CHORALE_T0 + 12.0, 60),
                                  (CHORALE_T0 + 24.0, 95)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(CHORALE_T0, 86), (CHORALE_T0 + 24.0, 76)],
                step=2.0)
    for t, p in ((502.0, 64), (508.0, 69), (514.0, 74)):
        sc.note(CH_HARP, p, t, 1.5, 44, jt=3, jv=2)         # bass echoes
    # sunrise (dawn quarter 3): D major light over a bare fifth
    sc.note(CH_HI, 74, 517.0, 32.0, 40, jt=0, jv=2)
    sc.note(CH_HI, 81, 519.0, 30.0, 38, jt=0, jv=2)
    for p, t, dur, vel in ((74, 517.0, 1.5, 50), (76, 519.0, 1.5, 48),
                           (78, 521.0, 2.0, 48), (81, 523.5, 2.5, 46),
                           (83, 527.0, 2.0, 44), (86, 529.5, 8.0, 42)):
        sc.note(CH_FLUTE, p, t, dur, vel, jt=3, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [(517.0, 66), (529.5, 72), (537.5, 30)],
                step=1.0)
    en.arp(sc, CH_HARP, [62, 66, 69, 74, 78], 517.0, 14, 0.5, 42,
           pattern="updown", gate=1.5)
    sc.note(CH_LO, 38, 521.0, 11.9, 42, jt=3, jv=2)
    sc.note(CH_LO, 45, 525.0, 7.9, 40, jt=3, jv=2)
    # the barometer turns: three readings, rising
    sc.note(CH_BARO, BARO_RISE[0], 518.5, 2.2, 46, jt=3, jv=2)
    for t, anchor in ((523.0, BARO_RISE[1]), (527.5, BARO_RISE[2])):
        sc.note(CH_BARO, anchor - 1, t, 0.7, 40, jt=3, jv=2)
        sc.note(CH_BARO, anchor, t + 0.75, 2.2, 44, jt=3, jv=2)
    # open fifths at sunrise (dawn quarter 4)
    sc.note(CH_CHOIR, 62, 533.0, 16.0, 44, jt=0, jv=2)
    sc.note(CH_CHOIR, 69, 533.0, 16.0, 42, jt=0, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(533.0, 82), (543.0, 45), (549.0, 15)],
                   step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(533.0, 80), (548.5, 28)], step=1.0)
    sc.note(CH_LO, 38, 533.0, 16.0, 44, jt=0, jv=2)
    sc.note(CH_LO, 45, 533.0, 16.0, 42, jt=0, jv=2)
    sc.note(CH_BELL, 86, 533.0, 0.6, 42, jt=2, jv=2)        # the lamp relit
    for i, p in enumerate((50, 57, 62, 69, 74)):
        sc.note(CH_HARP, p, 534.0 + 0.75 * i, 2.0, 44 - i, jt=3, jv=2)
    en.expr_curve(sc, CH_HI, [(517.0, 60), (533.0, 66), (548.5, 26)],
                  step=1.0)
    en.cc_curve(sc, CH_LO, 11, [(533.0, 72), (548.5, 30)], step=1.0)


BUILDERS: list = [build_calm, build_fresh, build_gale1, build_eye,
                  build_gale2, build_dawn]
