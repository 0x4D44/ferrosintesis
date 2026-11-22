"""material.py — the shared musical DNA of *Lantern Year*.

Everything that recurs across the ten nights lives HERE as data, and every
claim the album makes about that data is proven numerically by
verify_material() — written BEFORE the music, composed-to-pass (the repo
method).  Track modules import these objects; a recurrence is always
recomputed from THIS file, never re-typed.

The through-lines:

- BEAM_CELL   the album's signature: degrees 1-5-6-5-8.  The lamp swings out
              (a fifth), brushes the horizon (the sixth, a neighbour note),
              and comes home an octave higher.  Written in DEGREES, so it
              takes the colour of each night's mode; the detector is
              rhythm-free and transposition-free, so a track may state it
              as a jig figure, a bass ostinato or a brass fanfare.
- HYMN        "the keeper's hymn": 16 bars, four 4-bar phrases, with one
              chord per bar.  Phrase 1 opens with the BEAM in augmentation.
              Track 1 states it plainly; track 10 crowns it.
- oracle kit  the event readers and the two album-wide oracles every track
              runs (album_oracles): the BEAM census and the five-minute
              window.
"""

from __future__ import annotations

import conductor
import engine as en

PPQ = en.PPQ

# ---------------------------------------------------------------------------
# The BEAM cell — (onset_beats, dur_beats, degree).  Four even pickups and a
# held arrival; `stretch` rescales it to any meter.
# ---------------------------------------------------------------------------

BEAM_CELL: list[tuple[float, float, int]] = [
    (0.0, 0.5, 1),
    (0.5, 0.5, 5),
    (1.0, 0.5, 6),
    (1.5, 0.5, 5),
    (2.0, 2.0, 8),
]
BEAM_LEN: float = 4.0
BEAM_DEGREES: list[int] = [d for _on, _du, d in BEAM_CELL]


def beam_pitches(base: int, mode: str) -> list[int]:
    """The cell's five pitches where `base` is degree 1 of `mode`."""
    return [en.pitch(base, mode, d) for d in BEAM_DEGREES]


def play_beam(sc: en.Score, ch: int, t0: float, base: int, mode: str,
              stretch: float = 1.0, vel: int = 90,
              vel_end: int | None = None, gate: float = 0.95,
              jt: int = 0, jv: int = 3) -> float:
    """Play the BEAM cell; returns the end beat.

    jt defaults to 0 so pinned statements stay tick-exact.  The channel must
    be otherwise silent across the cell for beam_statements() to count it
    (the detector reads consecutive single note-ons).
    """
    total = BEAM_LEN * stretch
    for on, du, deg in BEAM_CELL:
        v = vel
        if vel_end is not None:
            v = round(en.lerp(vel, vel_end, on / BEAM_CELL[-1][0]))
        sc.note(ch, en.pitch(base, mode, deg), t0 + on * stretch,
                du * stretch * gate, v, jt=jt, jv=jv)
    return t0 + total


# ---------------------------------------------------------------------------
# The LAMP — one tubular-bell stroke on D.  It is the first sound of track 1
# and the last sound of track 10 (each pinned by that track's oracle), and
# any night may let it toll.
# ---------------------------------------------------------------------------

LAMP_PROGRAM: int = 14          # GM tubular bells
LAMP_PITCH: int = 62            # D4


# ---------------------------------------------------------------------------
# The keeper's HYMN — (degree, onset_beats, dur_beats), 64 beats of 4/4.
# One chord per bar (HYMN_CHORDS, diatonic triad roots as degrees).  Every
# bar's downbeat melody note is a chord tone (proven in verify_material), so
# the tune harmonises itself in ANY of the engine's modes: dorian gives the
# January hymn its major IV and minor v; ionian gives December its V-I.
# ---------------------------------------------------------------------------

HYMN: list[tuple[int, float, float]] = [
    # phrase 1 — the beam, augmented, and its echo
    (1, 0.0, 2.0), (5, 2.0, 2.0), (6, 4.0, 2.0), (5, 6.0, 2.0),
    (8, 8.0, 3.0), (7, 11.0, 1.0), (6, 12.0, 2.0), (5, 14.0, 2.0),
    # phrase 2 — the answer, settling on the supertonic
    (4, 16.0, 2.0), (5, 18.0, 2.0), (6, 20.0, 3.0), (5, 23.0, 1.0),
    (3, 24.0, 2.0), (4, 26.0, 2.0), (2, 28.0, 4.0),
    # phrase 3 — the climb to the tenth
    (3, 32.0, 2.0), (5, 34.0, 2.0), (8, 36.0, 2.0), (9, 38.0, 2.0),
    (10, 40.0, 3.0), (9, 43.0, 1.0), (8, 44.0, 2.0), (6, 46.0, 2.0),
    # phrase 4 — the cadence home
    (5, 48.0, 2.0), (6, 50.0, 2.0), (5, 52.0, 2.0), (3, 54.0, 2.0),
    (2, 56.0, 3.0), (1, 59.0, 1.0), (1, 60.0, 4.0),
]
HYMN_LEN: float = 64.0
PHRASE_LEN: float = 16.0
HYMN_CHORDS: list[int] = [1, 4, 1, 4,
                          4, 2, 1, 5,
                          1, 4, 1, 4,
                          1, 5, 5, 1]


def hymn_phrase(k: int) -> list[tuple[int, float, float]]:
    """Phrase k (0..3) with onsets rebased to the phrase start."""
    lo = k * PHRASE_LEN
    return [(d, on - lo, du) for d, on, du in HYMN
            if lo <= on < lo + PHRASE_LEN]


def hymn_chord(base: int, mode: str, bar: int, size: int = 3) -> list[int]:
    """The diatonic chord under hymn bar `bar` (0..15), root position."""
    return en.triad(base, mode, HYMN_CHORDS[bar], size)


def play_phrase(sc: en.Score, ch: int, t0: float, base: int, mode: str,
                k: int, stretch: float = 1.0, vel: int = 88,
                vel_end: int | None = None, gate: float = 0.96,
                jt: int = 0, jv: int = 3) -> float:
    """Play hymn phrase k starting at t0; returns the end beat."""
    for d, on, du in hymn_phrase(k):
        v = vel if vel_end is None else round(
            en.lerp(vel, vel_end, on / PHRASE_LEN))
        sc.note(ch, en.pitch(base, mode, d), t0 + on * stretch,
                du * stretch * gate, v, jt=jt, jv=jv)
    return t0 + PHRASE_LEN * stretch


def play_hymn(sc: en.Score, ch: int, t0: float, base: int, mode: str,
              stretch: float = 1.0, vel: int = 88,
              vel_end: int | None = None, gate: float = 0.96,
              jt: int = 0, jv: int = 3) -> float:
    """Play the whole hymn (four phrases); returns the end beat."""
    for k in range(4):
        a, b = vel, vel
        if vel_end is not None:
            a = round(en.lerp(vel, vel_end, k / 4))
            b = round(en.lerp(vel, vel_end, (k + 1) / 4))
        play_phrase(sc, ch, t0 + k * PHRASE_LEN * stretch, base, mode, k,
                    stretch=stretch, vel=a, vel_end=b, gate=gate,
                    jt=jt, jv=jv)
    return t0 + HYMN_LEN * stretch


# ---------------------------------------------------------------------------
# The oracle kit — event readers shared by every track's oracles().  All
# times are in BEATS (floats); nothing here assumes a meter.
# ---------------------------------------------------------------------------

CONSONANT = {0, 3, 4, 5, 7, 8, 9}        # interval classes (4th included)


def note_ons(sc: en.Score, ch: int) -> list[tuple[float, int, int]]:
    """[(beat, pitch, vel)] sorted by onset."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick / PPQ, data[1], data[2]))
    return sorted(out)


def note_spans(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """[(on_beat, off_beat, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick / PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick / PPQ, data[1], vel))
    return sorted(out)


def cc_lane(sc: en.Score, ch: int, num: int) -> list[tuple[float, int]]:
    """[(beat, value)] for one controller, sorted."""
    return sorted((t / PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def sounding(sc: en.Score, ch: int, beat: float,
             eps: float = 0.05) -> list[int]:
    """Pitches sounding on `ch` at `beat` (held across it by >= eps)."""
    return [p for on, off, p, _v in note_spans(sc, ch)
            if on <= beat + 1e-9 and off >= beat + eps]


def energy(sc: en.Score, t0: float, t1: float,
           channels=None) -> float:
    """Mean note-on velocity mass per beat over [t0, t1) — the score-side
    loudness proxy the dynamic-arc oracles compare."""
    total = 0.0
    for ch in (sc.events if channels is None else channels):
        for beat, _p, vel in note_ons(sc, ch):
            if t0 <= beat < t1:
                total += vel
    return total / max(1e-9, t1 - t0)


def active_channels(sc: en.Score, t0: float, t1: float) -> set[int]:
    """Channels with at least one note-on inside [t0, t1)."""
    return {ch for ch in sc.events
            if any(t0 <= b < t1 for b, _p, _v in note_ons(sc, ch))}


def _single_line(sc: en.Score, ch: int) -> list[list[tuple[float, int]]]:
    """The channel's note-ons split into runs of SINGLE onsets: a tick that
    carries two or more note-ons (a chord) breaks the run."""
    by_tick: dict[int, list[int]] = {}
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            by_tick.setdefault(tick, []).append(data[1])
    runs: list[list[tuple[float, int]]] = [[]]
    for tick in sorted(by_tick):
        if len(by_tick[tick]) == 1:
            runs[-1].append((tick / PPQ, by_tick[tick][0]))
        else:
            runs.append([])
    return [r for r in runs if r]


def beam_statements(sc: en.Score, ch: int) -> list[float]:
    """Start beats of every BEAM statement on `ch`.

    A statement is five consecutive single note-ons whose intervals are
    +7, +s, -s, +5 semitones with s in {1, 2} — root, fifth, sixth, fifth,
    octave in any mode whose fifth is perfect — in ANY rhythm, at ANY
    transposition.
    """
    out = []
    for run in _single_line(sc, ch):
        for i in range(len(run) - 4):
            p = [pitch for _b, pitch in run[i:i + 5]]
            step = p[2] - p[1]
            if (p[1] - p[0] == 7 and step in (1, 2)
                    and p[3] - p[2] == -step and p[4] - p[3] == 5):
                out.append(run[i][0])
    return out


def phrase_statements(sc: en.Score, ch: int, mode: str, k: int,
                      tol: float = 0.08) -> list[tuple[float, float, int]]:
    """Every statement of hymn phrase k on `ch`: [(start_beat, stretch,
    base_pitch)].  Pitches must match the phrase's degrees in `mode` at any
    transposition; onsets must be the phrase's rhythm under one uniform
    stretch (within `tol` beats)."""
    phrase = hymn_phrase(k)
    want = [en.deg_semis(mode, d) - en.deg_semis(mode, phrase[0][0])
            for d, _on, _du in phrase]
    span = phrase[-1][1] - phrase[0][1]
    out = []
    for run in _single_line(sc, ch):
        for i in range(len(run) - len(phrase) + 1):
            win = run[i:i + len(phrase)]
            if [p - win[0][1] for _b, p in win] != want:
                continue
            stretch = (win[-1][0] - win[0][0]) / span
            if stretch <= 0:
                continue
            if all(abs((b - win[0][0]) - stretch * (on - phrase[0][1]))
                   <= tol for (b, _p), (_d, on, _du) in zip(win, phrase)):
                base = win[0][1] - en.deg_semis(mode, phrase[0][0])
                out.append((win[0][0], stretch, base))
    return out


def hymn_statements(sc: en.Score, ch: int, mode: str,
                    tol: float = 0.08) -> list[tuple[float, float, int]]:
    """Every COMPLETE hymn on `ch` (phrases 0-3 back to back at one
    stretch and one transposition): [(start_beat, stretch, base_pitch)]."""
    later = [phrase_statements(sc, ch, mode, k, tol) for k in (1, 2, 3)]
    out = []
    for start, stretch, base in phrase_statements(sc, ch, mode, 0, tol):
        if all(any(abs(s - (start + (k + 1) * PHRASE_LEN * stretch)) <= tol
                   and abs(st - stretch) <= 0.01 and b == base
                   for s, st, b in later[k]) for k in range(3)):
            out.append((start, stretch, base))
    return out


# ---------------------------------------------------------------------------
# The album-wide oracles.  Every track's oracles() must begin with
#     results = material.album_oracles(sys.modules[__name__], sc)
# ---------------------------------------------------------------------------

BEAM_MIN_STATEMENTS = 3
MIN_VOICES = 6


def album_oracles(module, sc: en.Score) -> list[tuple[str, list[str]]]:
    """The disciplines every night shares: the BEAM census (>= 3 statements,
    across module.BEAM_CHANNELS, the first and last at least a third of the
    track apart — the cell must bind the track, not decorate one corner),
    the five-minute window, and a real ensemble (>= 6 sounding voices)."""
    end = module.PART.END_BEAT
    fails_beam: list[str] = []
    channels = getattr(module, "BEAM_CHANNELS", None)
    if not channels:
        fails_beam.append("module declares no BEAM_CHANNELS")
        starts: list[float] = []
    else:
        starts = sorted(b for ch in channels
                        for b in beam_statements(sc, ch))
        if len(starts) < BEAM_MIN_STATEMENTS:
            fails_beam.append(
                f"{len(starts)} BEAM statement(s) on channels "
                f"{sorted(channels)}, need >= {BEAM_MIN_STATEMENTS}")
        elif starts[-1] - starts[0] < end / 3.0:
            fails_beam.append(
                f"BEAM statements span only beats {starts[0]:.1f}.."
                f"{starts[-1]:.1f}; need >= a third of the track "
                f"({end / 3.0:.1f} beats)")

    fails_win: list[str] = []
    lo, hi = module.DURATION_WINDOW
    a_lo, a_hi = conductor.ALBUM_DURATION_WINDOW
    if lo < a_lo or hi > a_hi or lo >= hi:
        fails_win.append(f"DURATION_WINDOW ({lo}, {hi}) must sit inside the "
                         f"album window ({a_lo}, {a_hi})")
    secs = sc.seconds_at(end)
    if not a_lo <= secs <= a_hi:
        fails_win.append(f"score runs {secs:.1f}s, outside "
                         f"({a_lo}, {a_hi})")

    fails_ens: list[str] = []
    voices = active_channels(sc, 0.0, end + 1.0)
    if len(voices) < MIN_VOICES:
        fails_ens.append(f"only {len(voices)} channel(s) play; need >= "
                         f"{MIN_VOICES}")
    return [("album_beam_census", fails_beam),
            ("album_five_minutes", fails_win),
            ("album_ensemble", fails_ens)]


# ---------------------------------------------------------------------------
# Self-proof — run once by build.py --verify / --check.
# ---------------------------------------------------------------------------

def verify_material() -> list[str]:
    fails: list[str] = []

    # 1. The hymn is contiguous, 64 beats, four 16-beat phrases.
    cursor = 0.0
    for d, on, du in HYMN:
        if abs(on - cursor) > 1e-9:
            fails.append(f"hymn: note at {on} does not abut {cursor}")
        cursor = on + du
    if abs(cursor - HYMN_LEN) > 1e-9:
        fails.append(f"hymn ends at {cursor}, want {HYMN_LEN}")
    if sum(len(hymn_phrase(k)) for k in range(4)) != len(HYMN):
        fails.append("hymn phrases do not partition the tune")
    if len(HYMN_CHORDS) != 16:
        fails.append("hymn needs one chord per bar (16)")

    # 2. Phrase 1 opens with the BEAM, augmented x4.
    if [d for d, _on, _du in HYMN[:5]] != BEAM_DEGREES:
        fails.append("hymn does not open with the BEAM degrees")
    for (d, on, _du), (b_on, _b_du, _b_d) in zip(HYMN[:5], BEAM_CELL):
        if abs(on - 4.0 * b_on) > 1e-9:
            fails.append(f"hymn note {d} at {on} is not the BEAM x4")

    # 3. Every bar's downbeat melody note is a chord tone (so the tune
    #    harmonises itself in every mode), and the tune stays inside a
    #    tenth (singable by any voice the album gives it).
    for bar, root in enumerate(HYMN_CHORDS):
        beat = 4.0 * bar
        deg = next(d for d, on, du in HYMN if on <= beat < on + du)
        if (deg - root) % 7 not in (0, 2, 4):
            fails.append(f"hymn bar {bar + 1}: degree {deg} is not a tone "
                         f"of chord {root}")
    degs = [d for d, _on, _du in HYMN]
    if min(degs) != 1 or max(degs) != 10:
        fails.append("hymn range must be degrees 1..10")
    if HYMN[-1][0] != 1 or HYMN_CHORDS[-1] != 1 or HYMN_CHORDS[0] != 1:
        fails.append("hymn must begin and end on the tonic")

    # 4. The detectors find what the emitters play — in every mode, at a
    #    stretch, with a chord beside the line — and nothing else.
    for mode in en.MODES:
        sc = en.Score(1)
        play_beam(sc, 0, 4.0, 62, mode, stretch=1.5)
        if beam_statements(sc, 0) != [4.0]:
            fails.append(f"beam detector misses the cell in {mode}")
        sc = en.Score(1)
        play_hymn(sc, 0, 8.0, 60, mode, stretch=0.75, jt=3)
        found = hymn_statements(sc, 0, mode)
        if len(found) != 1 or found[0][2] != 60 \
                or abs(found[0][1] - 0.75) > 0.01:
            fails.append(f"hymn detector misses the tune in {mode}")
        if len(beam_statements(sc, 0)) != 1:
            fails.append(f"hymn in {mode} should carry exactly one BEAM")
    sc = en.Score(1)
    for i, p in enumerate([60, 67, 69, 65, 72, 60, 67, 68, 67, 71]):
        sc.note(0, p, float(i), 0.9, 80, jt=0, jv=0)
    if beam_statements(sc, 0):
        fails.append("beam detector accepts a near-miss")
    sc = en.Score(1)
    play_beam(sc, 0, 0.0, 60, "ionian")
    sc.note(0, 48, 1.0, 0.5, 80, jt=0, jv=0)      # a chord on the 3rd note
    if beam_statements(sc, 0):
        fails.append("beam detector must not read through a chord")
    return fails
