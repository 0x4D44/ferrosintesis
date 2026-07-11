"""t09_ten_thousand_watts.py — "Ten Thousand Watts" (Big Weather, track 9).

The album's fastest, hardest track: A-minor power-chord rock at 138 BPM.
DRUM-FEATURE #2 — and deliberately the OPPOSITE of t03's long soloing
arcs over a bass pedal: here the kit converses in strict TRADING FOURS
(the middle-8 IS the trading window — three rounds of a 4-bar power-chord
band phrase answered by a 4-bar, dead-silent-band drum four), then takes
an 8-bar UNACCOMPANIED breakdown solo built from a kick-snare 16th-note
engine, cymbal chokes, and a pinned 32nd-note around-the-kit CYCLONE
figure (stated twice, oracle-recomputed).  After the breakdown the floor
falls away: a PRODUCED drop — portamento bass drone gliding A3->A2 under
a rising cymbal swell, expression ducking then blooming — and the
RE-ENTRY SLAM into the final chorus, where the timpani arrive (gated
late) and the orchestra hits (stabs only, gated to chorus 2 on) land on
every phrase corner.

Form (HLD §4, full grammar + named feature movements):
  intro | verse1 | pre1 | chorus1 | verse2 | pre2 | chorus2 |
  middle8 (trading fours) | breakdown_solo | drop | final_chorus | outro
"""

from __future__ import annotations

import conductor
import engine as en

NUMBER = 9
TITLE = "Ten Thousand Watts"
FILE = "09 - Ten Thousand Watts.mid"
SEED = 20260709

BPM = 138.0

# Channels (HLD §3; per-track deviation: no choir — like t03, the album's
# hard-rock tracks skip the choir per HLD D3; CHOIR_SPEC deliberately
# omitted.  ch12 carries the orchestra hits, ch11 the melodic timpani.)
PIANO, MUTE, DRIVE, BASS = 0, 1, 2, 3
LEAD, DRUMS, TIMP, ORCH = 6, 9, 11, 12

_SECTIONS = [
    ("intro",            0.0,  32.0),
    ("verse1",          32.0,  96.0),
    ("pre1",            96.0, 128.0),
    ("chorus1",        128.0, 192.0),
    ("verse2",         192.0, 224.0),
    ("pre2",           224.0, 256.0),
    ("chorus2",        256.0, 320.0),
    ("middle8",        320.0, 416.0),
    ("breakdown_solo", 416.0, 448.0),
    ("drop",           448.0, 464.0),
    ("final_chorus",   464.0, 544.0),
    ("outro",          544.0, 576.0),
]

PART = conductor.Part(
    number=NUMBER, title=TITLE, file=FILE,
    movements=_SECTIONS,
    tempo_map=[(0.0, BPM)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],                      # A minor
    channels=[
        (PIANO, "piano",          0,  96, 64, 45),
        (MUTE,  "mute guitar",   28,  92, 48, 30),
        (DRIVE, "drive guitar",  30,  96, 80, 28),
        (BASS,  "bass guitar",   33, 105, 64, 20),
        (LEAD,  "lead synth",    81,  92, 64, 45),
        (DRUMS, "drums",          0, 110, 64, 40),
        (TIMP,  "timpani",       47, 100, 64, 60),
        (ORCH,  "orchestra hit", 55,  96, 64, 50),
    ],
    program_changes=[
        (MUTE, 464.0, 29),      # palm-mute -> overdrive for the slam wall
        (MUTE, 544.0, 28),      # back to palm-mute for the dying outro
    ],
)

# ---------------------------------------------------------------------------
# Harmony — A aeolian.  Guitar/bass roots fold onto the low strings
# (E2..D3) so the power chords stay tight at 138 BPM.
# ---------------------------------------------------------------------------

A2, A3, A4 = en.n("A2"), en.n("A3"), en.n("A4")
_MODE = "aeolian"

VERSE_PROG = [1, 6, 3, 7]           # Am  F   C   G
PRE_PROG = [4, 5, 6, 7]             # Dm  Em  F   G  (the climb)
CHORUS_PROG = [1, 7, 6, 7]          # Am  G   F   G  (the watts pump)

# Chord degree -> bass-register degree (folds 5/6/7 below the tonic).
_BDEG = {1: 1, 3: 3, 4: 4, 5: -2, 6: -1, 7: 0}


def _pv(deg: int, octave: int = 0) -> int:
    return en.pitch(A2, _MODE, deg) + 12 * octave


def _groot(deg: int) -> int:
    """Guitar root for a chord degree, folded into E2..D3 (40..50)."""
    p = _pv(deg)
    return p - 12 if p > 50 else p


def _triad(deg: int, octave: int = 2) -> list[int]:
    return [p + 12 * octave for p in en.triad(A2, _MODE, deg)]


# The RIFF — the drive-guitar bookend (8 beats).  An A-minor stomp that
# leans on the bVII/bVI (G/F) drop and turns home through D-E.
# (beat, semitone offset from A2, dur, vel, power?)  jt=0 throughout.
_RIFF = [
    (0.00,  0, 0.70, 110, True),
    (0.75,  0, 0.45,  98, True),
    (1.50,  3, 0.45, 104, True),    # C — the minor bite
    (2.25,  0, 0.45, 100, True),
    (3.00, -2, 0.45, 102, True),    # G below
    (3.50, -4, 0.95, 106, True),    # F, held
    (4.50,  0, 0.70, 108, True),
    (5.25,  0, 0.45,  96, True),
    (6.00,  5, 0.45, 104, True),    # D
    (6.75,  7, 0.45, 106, True),    # E turns the corner
    (7.25, 12, 0.25,  94, False),   # single-note turn: A3
    (7.50, 10, 0.25,  92, False),   # G3
    (7.75,  8, 0.25,  90, False),   # F3 falls onto the next A
]

# The chorus HOOK — (degree, start, dur) over 16 beats (Am G F G), sung
# by the lead synth; bar 3 surges to the octave ("ten thousand watts"),
# bar 4 hangs on the suspended D.  Long notes get CC1 vibrato blooms.
_HOOK = [
    (5, 0.0, 0.5), (5, 0.5, 0.5), (6, 1.0, 0.75), (5, 1.75, 0.75),
    (3, 2.5, 1.4),
    (4, 4.0, 0.5), (4, 4.5, 0.5), (5, 5.0, 0.75), (4, 5.75, 0.75),
    (2, 6.5, 1.4),
    (1, 8.0, 0.5), (3, 8.5, 0.5), (5, 9.0, 0.5), (8, 9.5, 1.0),
    (7, 10.5, 1.4),
    (5, 12.0, 0.75), (7, 12.75, 0.75), (8, 13.5, 0.5), (4, 14.0, 1.9),
]

_HOOK_LYRICS = ["ten thousand watts", "every light on",
                "turn it louder", "outshine the storm"]

# The final-chorus bass hook (bars 13-16): the counterline the BASS_SPEC
# pins — 8ths singing up to the seventh, span 16 semitones.
_BASS_HOOK = [
    (0.0, 1, 0.45), (0.5, 3, 0.45), (1.0, 4, 0.45), (1.5, 5, 0.90),
    (2.5, 4, 0.45), (3.0, 3, 0.45), (3.5, 2, 0.45),
    (4.0, 0, 0.45), (4.5, 0, 0.45), (5.0, 2, 0.45), (5.5, 4, 0.90),
    (6.5, 5, 0.45), (7.0, 4, 0.45), (7.5, 3, 0.45),
    (8.0, -1, 0.45), (8.5, 1, 0.45), (9.0, 3, 0.45), (9.5, 5, 0.90),
    (10.5, 6, 0.45), (11.0, 5, 0.45), (11.5, 4, 0.45),
    (12.0, 0, 0.45), (12.5, 2, 0.45), (13.0, 4, 0.45), (13.5, 5, 0.45),
    (14.0, 7, 0.90), (15.0, 5, 0.45), (15.5, 2, 0.45),
]

# The CYCLONE — the breakdown's pinned around-the-kit 32nd-note figure
# (one bar, 32 strokes): snare -> high tom -> mid toms -> floor toms,
# closed by a china/crash/crash-2/splash volley.  jt=0/jv=0 so the
# cyclone_recurrence oracle can recompute every stroke exactly.
_CYCLONE_KEYS = ([38] * 4 + [50] * 4 + [48] * 4 + [47] * 4 + [45] * 4
                 + [43] * 4 + [41] * 4 + [52, 49, 57, 55])
_CYCLONE = [(0.125 * k, key, int(round(68 + 52 * k / 31)))
            for k, key in enumerate(_CYCLONE_KEYS)]


# ---------------------------------------------------------------------------
# Textures — the band
# ---------------------------------------------------------------------------

def _power(sc, root: int, beat: float, dur: float, vel: int,
           jt: int = 0) -> None:
    """Root + fifth + octave on the drive guitar."""
    for i, off in enumerate((0, 7, 12)):
        sc.note(DRIVE, root + off, beat, dur, vel - 4 * i, jt=jt, jv=3)


def _riff(sc, t0: float, reps: int, vel_scale: float = 1.0) -> None:
    """State the RIFF `reps` times (8 beats each) on the drive guitar."""
    for r in range(reps):
        base = t0 + 8.0 * r
        for beat, off, dur, vel, power in _RIFF:
            v = max(1, int(round(vel * vel_scale)))
            if power:
                _power(sc, A2 + off, base + beat, dur, v)
            else:
                sc.note(DRIVE, A2 + off, base + beat, dur, v, jt=0, jv=3)


def _chug(sc, t0: float, bars: int, prog: list[int], vel: int = 68) -> None:
    """Palm-mute eighths on the mute guitar: root+fifth dyads, gapped
    (true transients at pan 48 — the mono-safety lever, HLD D5)."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _groot(prog[i % len(prog)])
        for k in range(8):
            acc = 6 if k in (0, 5) else (-6 if k % 2 else 0)
            j0 = 0 if (i == 0 and k == 0) else 2
            sc.note(MUTE, r, b + 0.5 * k, 0.28, vel + acc, jt=j0, jv=3)
            sc.note(MUTE, r + 7, b + 0.5 * k, 0.26, vel + acc - 8,
                    jt=j0, jv=3)


def _power_bed(sc, t0: float, bars: int, prog: list[int],
               vel: int = 100, push: bool = True) -> None:
    """Drive guitar: held power chords with the eighth push."""
    for i in range(bars):
        b = t0 + 4.0 * i
        r = _groot(prog[i % len(prog)])
        _power(sc, r, b, 2.4, vel, jt=0 if i == 0 else 2)
        if push:
            _power(sc, r, b + 2.5, 0.45, vel - 10, jt=2)
            _power(sc, r, b + 3.5, 0.45, vel - 6, jt=2)


def _piano_anthem(sc, t0: float, bars: int, prog: list[int],
                  vel: int = 86) -> None:
    """Chorus piano: block chords with an octave crown, pedalled."""
    for i in range(bars):
        b = t0 + 4.0 * i
        deg = prog[i % len(prog)]
        tri = _triad(deg, octave=2)
        r = _groot(deg) + 12
        j0 = 0 if i == 0 else 3
        for beat, dur, dv in ((0.0, 1.4, 0), (1.5, 0.9, -6), (2.5, 1.4, -2)):
            jt = j0 if beat == 0.0 else 3
            sc.note(PIANO, r, b + beat, dur, vel + dv, jt=jt, jv=4)
            for p in tri:
                sc.note(PIANO, p, b + beat, dur, vel + dv - 5, jt=jt, jv=4)
        sc.note(PIANO, tri[0] + 12, b + 3.5, 0.45, vel + 4, jt=3, jv=4)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)


def _bass_verse(sc, t0: float, prog: list[int], reps: int = 1,
                vel: int = 96) -> None:
    """The verse bass SINGS: scale-wise eighths around each root with a
    stepwise approach into every next chord (BASS_SPEC's 40% floor)."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        d = _BDEG[deg]
        nd = _BDEG[seq[(i + 1) % len(seq)]]
        appr = nd + 1 if nd < d else nd - 1
        pat = [(0.0, d, 6), (0.5, d, -6), (1.0, d + 1, -2), (1.5, d + 2, 0),
               (2.0, d + 4, 4), (2.5, d + 3, -4), (3.0, d + 2, -2),
               (3.5, appr, 0)]
        for off, dg, dv in pat:
            j0 = 0 if (i == 0 and off == 0.0) else 2
            sc.note(BASS, en.pitch(A2, _MODE, dg), b + off, 0.45,
                    vel + dv, jt=j0, jv=3)


def _bass_drive(sc, t0: float, prog: list[int], reps: int = 1,
                vel: int = 102) -> None:
    """Chorus bass: driving eighths with the octave pop and a scale fall."""
    seq = prog * reps
    for i, deg in enumerate(seq):
        b = t0 + 4.0 * i
        d = _BDEG[deg]
        nd = _BDEG[seq[(i + 1) % len(seq)]]
        appr = nd + 1 if nd < d else nd - 1
        pat = [(0.0, d, 6), (0.5, d, -4), (1.0, d + 7, 2), (1.5, d, -4),
               (2.0, d, 2), (2.5, d + 4, 0), (3.0, d + 3, -2), (3.5, appr, 0)]
        for off, dg, dv in pat:
            j0 = 0 if (i == 0 and off == 0.0) else 2
            sc.note(BASS, en.pitch(A2, _MODE, dg), b + off, 0.42,
                    vel + dv, jt=j0, jv=3)


def _lead_hook(sc, t0: float, reps: int, vel: int, *,
               lyrics: bool = False) -> None:
    """The chorus hook; CC1 vibrato blooms on every long note."""
    for r in range(reps):
        base = t0 + 16.0 * r
        en.line(sc, LEAD, base, A4, _MODE, _HOOK, vel, jt=0, jv=0,
                gate=0.98)
        for deg, start, dur in _HOOK:
            if dur >= 1.4:
                b = base + start
                en.cc_curve(sc, LEAD, 1,
                            [(b + 0.25, 0), (b + dur * 0.6, 58),
                             (b + dur, 10)], step=0.15)
        if lyrics and r == 0:
            for k, text in enumerate(_HOOK_LYRICS):
                en.lyric(sc, base + 4.0 * k, text)


def _orch_hits(sc, t0: float, bars: int, vel: int = 102,
               dense: bool = False) -> None:
    """Orchestra hits — STABS ONLY (HLD D9): unison+octave jabs on the
    phrase corners and the and-of-4 push into each next four."""
    for g in range(bars // 4):
        b = t0 + 16.0 * g
        for p in (57, 69):
            sc.note(ORCH, p, b, 0.6, vel, jt=0, jv=0)
            sc.note(ORCH, p, b + 15.5, 0.35, vel - 8, jt=0, jv=2)
            if dense:
                sc.note(ORCH, p, b + 8.0, 0.45, vel - 6, jt=0, jv=2)


def _timp_final(sc, t0: float) -> None:
    """Timpani (gated to the final chorus): anchors on every phrase
    corner, crescendo rolls into the next, aftertouch under each roll."""
    for g in range(4):
        b = t0 + 16.0 * g
        sc.note(TIMP, 45, b, 1.2, 102, jt=0, jv=3)
        sc.note(TIMP, 52, b + 2.0, 0.9, 88, jt=2, jv=3)
        for k in range(8):
            sc.note(TIMP, 45, b + 14.0 + 0.25 * k, 0.22,
                    int(en.lerp(58, 102, k / 7)), jt=1, jv=3)
        en.at_curve(sc, TIMP, [(b + 14.0, 16), (b + 15.9, 96)], step=0.25)
    # The tag: anchor, the big roll, the last strike.
    sc.note(TIMP, 45, t0 + 64.0, 1.2, 104, jt=0, jv=3)
    for k in range(16):
        sc.note(TIMP, 45, t0 + 72.0 + 0.25 * k, 0.22,
                int(en.lerp(52, 110, k / 15)), jt=1, jv=3)
    en.at_curve(sc, TIMP, [(t0 + 72.0, 12), (t0 + 75.9, 108)], step=0.25)
    sc.note(TIMP, 45, t0 + 76.0, 2.5, 108, jt=0, jv=0)
    sc.note(TIMP, 52, t0 + 78.0, 1.5, 92, jt=2, jv=3)


def _groove(sc, t0: float, bars: int, intensity: float, *,
            ride: bool = False, crash_in: bool = False, china: bool = False,
            fills: bool = True) -> None:
    """The band kit at 138: driving kick, backbeat + ghosts, shaped hats."""
    for i in range(bars):
        b = t0 + 4.0 * i
        first, last = i == 0, i == bars - 1
        fill_bar = fills and (last or i % 8 == 7)
        v = int(round(en.lerp(70, 106, intensity)))
        if crash_in and first:
            sc.hit(49, b, min(122, v + 16), jt=0)
        if china and i % 4 == 2:
            sc.hit(52, b, v + 6, jt=2)
        sc.hit(36, b, v + 10, jt=0 if first else 2)
        sc.hit(36, b + 1.75, v - 2, jt=2)
        sc.hit(36, b + 2.5, v + 4, jt=2)
        if intensity > 0.7 and i % 2 == 1:
            sc.hit(36, b + 3.75, v - 4, jt=2)
        sc.hit(38, b + 1.0, v + 12, jt=2, jv=4)
        sc.hit(38, b + 3.0, v + 12, jt=2, jv=4)
        if intensity < 0.9:
            sc.hit(38, b + 2.25, max(16, v - 48), jt=3, jv=6)
            sc.hit(38, b + 3.75, max(16, v - 52), jt=3, jv=6)
        key = 51 if ride else 42
        for k in range(8):
            if fill_bar and k >= 5:
                continue
            sc.hit(key, b + 0.5 * k, max(20, v - (8 if k % 2 == 0 else 24)),
                   jt=2, jv=5)
        if ride and i % 2 == 0:
            sc.hit(53, b + 2.0, v - 6, jt=2)
        if not ride and not fill_bar and i % 2 == 1:
            sc.hit(46, b + 3.5, v - 16, jt=2)
        if fill_bar:
            run_keys = [38, 50, 48, 47, 45, 43, 41, 38]
            for k, key2 in enumerate(run_keys):
                sc.hit(key2, b + 2.0 + 0.25 * k,
                       int(en.lerp(v - 20, v + 14, k / 7)), jt=2)


# ---------------------------------------------------------------------------
# Textures — the trading fours and the breakdown kit writing.
# Inside DRUM_SOLO_SPEC windows every bar-start hit is jt=0 so a burst
# bar can never jitter a stroke across a counted bar line (T16 lesson).
# ---------------------------------------------------------------------------

def _interlock(sc, b: float, vel: int, kick_slots: set[int],
               acc_slots: set[int]) -> None:
    """One bar of the 16th-note kick-snare ENGINE: every slot speaks —
    kicks drive, accents crack, the rest are ghosted snare."""
    for k in range(16):
        beat = b + 0.25 * k
        if k in kick_slots:
            sc.hit(36, beat, vel + (6 if k % 4 == 0 else -2),
                   jt=0 if k == 0 else 1, jv=3)
        elif k in acc_slots:
            sc.hit(38, beat, vel + 10, jt=1, jv=3)
        else:
            sc.hit(38, beat, max(18, vel - 52), jt=2, jv=5)


_ENGINE_KICKS = {0, 2, 3, 6, 8, 10, 11, 14}
_ENGINE_ACCENTS = {4, 12}


def _four_engine(sc, t0: float) -> None:
    """Drum four A — the kick-snare engine introduces itself.
    Bars: statement (17) / answer (14) / doubled+china (22) / around the
    kit (21)."""
    # Bar 1 — the engine states itself under a crash.
    b = t0
    sc.hit(49, b, 114, jt=0)
    for beat, v in ((0.0, 110), (0.75, 96), (1.25, 98), (2.0, 106),
                    (2.75, 94), (3.25, 100)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(38, b + 1.0, 112, jt=2, jv=4)
    sc.hit(38, b + 3.0, 114, jt=2, jv=4)
    for beat, v in ((0.5, 36), (1.75, 42), (2.5, 38), (3.75, 46)):
        sc.hit(38, b + beat, v, jt=3, jv=6)
    for k in range(4):
        sc.hit(42, b + k, 66 if k % 2 == 0 else 54, jt=2, jv=5)
    # Bar 2 — the answer: barks and bell.
    b = t0 + 4.0
    for beat, v in ((0.0, 108), (0.75, 96), (1.5, 100), (2.25, 104),
                    (3.5, 96)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(38, b + 1.0, 110, jt=2, jv=4)
    sc.hit(38, b + 3.0, 112, jt=2, jv=4)
    sc.hit(38, b + 2.5, 40, jt=3, jv=6)
    sc.hit(38, b + 3.75, 44, jt=3, jv=6)
    sc.hit(46, b + 0.5, 78, jt=2)
    sc.hit(46, b + 2.5, 74, jt=2)
    sc.hit(53, b + 1.5, 82, jt=2)
    sc.hit(53, b + 3.5, 84, jt=2)
    sc.hit(41, b + 3.25, 88, jt=2)
    # Bar 3 — the engine doubles: full 16th interlock (BURST).
    b = t0 + 8.0
    sc.hit(52, b, 112, jt=0)
    _interlock(sc, b, 96, _ENGINE_KICKS, _ENGINE_ACCENTS)
    sc.hit(49, b + 2.0, 108, jt=1)
    for k in range(4):
        sc.hit(42, b + k, 60, jt=2, jv=5)
    # Bar 4 — engine, then around the kit in 16ths -> 32nds (BURST).
    b = t0 + 12.0
    for beat, v in ((0.0, 108), (0.5, 98), (0.75, 100), (1.5, 104)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 1)
    sc.hit(38, b + 1.0, 110, jt=1, jv=3)
    sc.hit(38, b + 1.25, 42, jt=2, jv=5)
    sc.hit(38, b + 1.75, 46, jt=2, jv=5)
    sc.hit(55, b + 2.0, 102, jt=1)
    for k, key in enumerate((50, 48, 47, 45)):
        sc.hit(key, b + 2.0 + 0.25 * k, int(en.lerp(84, 100, k / 3)), jt=1)
    for k, key in enumerate((43, 41, 43, 41, 43, 41, 50, 48)):
        sc.hit(key, b + 3.0 + 0.125 * k, int(en.lerp(86, 108, k / 7)), jt=1)
    sc.hit(57, b + 3.875, 108, jt=0)


def _four_chokes(sc, t0: float) -> None:
    """Drum four B — cymbal chokes: calls cut off by the snare, the choke
    volley, and a snare roll bursting into the china slam.
    Bars: 14 / 17 / 22 / 24."""
    # Bar 1 — choke calls, right <-> left across the stage.
    b = t0
    for off, cym, v in ((0.0, 52, 114), (1.5, 49, 110), (2.5, 55, 104),
                        (3.5, 57, 108)):
        sc.hit(cym, b + off, v, jt=0 if off == 0.0 else 1)
        sc.hit(38, b + off + 0.25, 88, jt=1, jv=4)
    sc.hit(42, b + 0.375, 70, jt=1)
    sc.hit(42, b + 1.875, 66, jt=1)
    for k in range(4):
        sc.hit(36, b + k, 104, jt=0 if k == 0 else 2)
    # Bar 2 — the ride keeps time, engine underneath.
    b = t0 + 4.0
    sc.hit(53, b, 92, jt=0)
    for k in range(8):
        sc.hit(51, b + 0.5 * k, 78 if k % 2 == 0 else 60, jt=2, jv=4)
    for beat, v in ((0.0, 106), (0.75, 96), (1.5, 100), (2.5, 102),
                    (3.25, 96)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(38, b + 1.0, 108, jt=2, jv=4)
    sc.hit(38, b + 3.0, 110, jt=2, jv=4)
    sc.hit(38, b + 3.75, 44, jt=3, jv=6)
    # Bar 3 — the choke volley: china/crash 16ths trade (BURST).
    b = t0 + 8.0
    for k in range(8):
        sc.hit(52 if k % 2 == 0 else 49, b + 0.25 * k,
               int(en.lerp(84, 110, k / 7)), jt=0 if k == 0 else 1)
    for k in range(4):
        sc.hit(38, b + 2.0 + 0.25 * k, int(en.lerp(60, 96, k / 3)),
               jt=1, jv=3)
    for k, key in enumerate((55, 57, 55, 57)):
        sc.hit(key, b + 3.0 + 0.25 * k, 96 + 4 * k, jt=1)
    for beat in (0.0, 1.0, 1.5, 2.0, 2.5, 3.0):
        sc.hit(36, b + beat, 102, jt=0 if beat == 0.0 else 2)
    # Bar 4 — snare roll 32nds, floor drop, china slam (BURST).
    b = t0 + 12.0
    for k in range(16):
        sc.hit(38, b + 0.125 * k, int(en.lerp(38, 104, k / 15)),
               jt=0 if k == 0 else 1, jv=3)
    sc.hit(36, b + 2.0, 106, jt=1)
    for off, key in ((2.25, 41), (2.5, 43), (2.75, 41)):
        sc.hit(key, b + off, 96, jt=1)
    sc.hit(52, b + 3.0, 112, jt=1)
    sc.hit(36, b + 3.0, 108, jt=1)
    sc.hit(49, b + 3.5, 110, jt=1)
    sc.hit(38, b + 3.75, 114, jt=1)


def _four_cyclone(sc, t0: float) -> None:
    """Drum four C — the cyclone preview: half-cyclone, choke breath, a
    full freeform shimmer-into-toms cyclone, and the rising rush that
    hands the stage to the breakdown.  Bars: 22 / 14 / 36 / 18."""
    # Bar 1 — engine, then the first half-cyclone (BURST).
    b = t0
    sc.hit(49, b, 112, jt=0)
    sc.hit(36, b, 108, jt=0)
    sc.hit(36, b + 0.75, 98, jt=1)
    sc.hit(38, b + 1.0, 108, jt=1, jv=3)
    sc.hit(42, b + 0.5, 66, jt=1)
    sc.hit(42, b + 1.5, 62, jt=1)
    for k, key in enumerate((38, 38, 50, 50, 48, 48, 47, 47,
                             45, 45, 43, 43, 41, 41, 52, 49)):
        sc.hit(key, b + 2.0 + 0.125 * k, int(en.lerp(64, 112, k / 15)),
               jt=1, jv=2)
    # Bar 2 — choke trade breath.
    b = t0 + 4.0
    sc.hit(52, b, 110, jt=0)
    sc.hit(38, b + 0.25, 86, jt=1, jv=4)
    sc.hit(49, b + 1.5, 106, jt=1)
    sc.hit(38, b + 1.75, 84, jt=1, jv=4)
    for beat, v in ((0.0, 104), (1.0, 98), (2.0, 102), (2.75, 94),
                    (3.5, 98)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(51, b + 2.0, 74, jt=2)
    sc.hit(51, b + 3.0, 78, jt=2)
    sc.hit(53, b + 3.5, 84, jt=2)
    sc.hit(38, b + 0.75, 38, jt=3, jv=6)
    sc.hit(38, b + 3.25, 40, jt=3, jv=6)
    # Bar 3 — the full freeform cyclone: shimmer into the toms (BURST).
    b = t0 + 8.0
    seq = (42, 51, 42, 51, 42, 51, 42, 51,
           50, 50, 48, 48, 47, 47, 45, 45,
           43, 43, 41, 41, 38, 38, 50, 48,
           47, 45, 43, 41, 52, 49, 57, 55)
    for k, key in enumerate(seq):
        sc.hit(key, b + 0.125 * k, int(en.lerp(58, 116, k / 31)),
               jt=0 if k == 0 else 1, jv=2)
    for k in range(4):
        sc.hit(36, b + k, 102, jt=0 if k == 0 else 1)
    # Bar 4 — the rising rush into the breakdown.
    b = t0 + 12.0
    for k in range(3):
        sc.hit(38, b + 0.125 * k, int(en.lerp(44, 72, k / 2)),
               jt=0 if k == 0 else 1)
    for k, key in enumerate((41, 43, 45, 47, 48, 50)):
        sc.hit(key, b + 0.5 + 0.25 * k, int(en.lerp(78, 104, k / 5)), jt=1)
    sc.hit(52, b + 2.0, 108, jt=1)
    sc.hit(36, b + 2.0, 104, jt=1)
    sc.hit(38, b + 2.5, 100, jt=1, jv=3)
    sc.hit(38, b + 2.75, 104, jt=1, jv=3)
    sc.hit(49, b + 3.0, 110, jt=1)
    sc.hit(36, b + 3.0, 106, jt=1)
    sc.hit(42, b + 3.25, 64, jt=1)
    sc.hit(42, b + 3.5, 68, jt=1)
    sc.hit(38, b + 3.75, 114, jt=0)


def _cyclone(sc, t0: float, vel_off: int = 0) -> None:
    """State the pinned CYCLONE figure + its quarter-note kick anchors."""
    for off, key, vel in _CYCLONE:
        sc.hit(key, t0 + off, min(127, vel + vel_off), jt=0, jv=0)
    for k in range(4):
        sc.hit(36, t0 + k, 104 + (4 if k == 0 else 0), jt=0, jv=0)


def _band_four(sc, t0: float, lift: int = 0, china: bool = False) -> None:
    """One 4-bar BAND phrase of the trading fours: power-chord stomp with
    locked bass and orchestra-hit corners; the kit's fill bar hands the
    stage to the answering drum four (band silent from 13.9 beats in)."""
    stabs = [
        (0.0,  1, 0.70, 110), (0.75, 1, 0.45, 100), (1.5, 1, 1.30, 108),
        (3.0,  7, 0.45, 102), (3.5,  6, 0.95, 104),
        (4.5,  6, 0.45, 100), (5.0,  7, 0.45, 102), (5.5, 1, 1.30, 108),
        (7.0,  3, 0.45, 104), (7.5,  4, 0.90, 106),
        (8.0,  1, 0.70, 110), (8.75, 1, 0.45, 100), (9.5, 1, 1.30, 108),
        (11.0, 4, 0.45, 104), (11.5, 5, 0.95, 106),
        (12.0, 6, 0.45, 106), (12.5, 7, 0.45, 108), (13.0, 1, 0.90, 112),
    ]
    for off, deg, dur, vel in stabs:
        _power(sc, _groot(deg), t0 + off, dur, min(127, vel + lift), jt=0)
        sc.note(BASS, en.pitch(A2, _MODE, _BDEG[deg]), t0 + off,
                min(dur, 0.6), min(127, vel - 6 + lift),
                jt=0 if off == 0.0 else 2, jv=3)
    for p in (57, 69):
        sc.note(ORCH, p, t0, 0.6, min(127, 106 + lift), jt=0, jv=0)
        sc.note(ORCH, p, t0 + 13.0, 0.5, min(127, 102 + lift), jt=0, jv=0)
    _groove(sc, t0, 4, min(1.0, 0.82 + lift / 150.0), crash_in=True,
            china=china, fills=True)


# ---------------------------------------------------------------------------
# Shared section shapes
# ---------------------------------------------------------------------------

def _pre(sc, t0: float) -> None:
    """The climb (Dm Em F G): wah opens on the chug, the piano enters,
    the drive bed joins halfway, a snare build lights the chorus fuse."""
    en.wah(sc, MUTE, t0, 32.0, lo=40, hi=104, cycles_per_beat=0.25)
    for i in range(8):
        _chug(sc, t0 + 4.0 * i, 1, [PRE_PROG[i % 4]], vel=68 + 2 * i)
    _piano_anthem(sc, t0, 8, PRE_PROG, vel=76)
    _bass_verse(sc, t0, PRE_PROG, reps=2, vel=98)
    _groove(sc, t0, 7, 0.7, crash_in=True)
    _power_bed(sc, t0 + 16.0, 4, PRE_PROG, vel=92, push=False)
    # Bar 8: the kit steps aside for the snare build.
    b = t0 + 28.0
    sc.hit(36, b, 100, jt=2)
    sc.hit(36, b + 2.0, 102, jt=2)
    for k in range(16):
        sc.hit(38, b + 0.25 * k, int(en.lerp(30, 110, k / 15)), jt=1, jv=3)
    sc.hit(49, b + 3.75, 90, jt=1)


def _chorus(sc, t0: float, bars: int, *, lift: int = 0, ride: bool = False,
            china: bool = False, lyrics: bool = False, orch: bool = False,
            dense: bool = False, bass: bool = True) -> None:
    _power_bed(sc, t0, bars, CHORUS_PROG, vel=100 + lift)
    _chug(sc, t0, bars, CHORUS_PROG, vel=70 + lift)
    _piano_anthem(sc, t0, bars, CHORUS_PROG, vel=86 + lift)
    if bass:
        _bass_drive(sc, t0, CHORUS_PROG, reps=bars // 4, vel=102 + lift)
    _groove(sc, t0, bars, min(1.0, 0.85 + lift / 150.0), ride=ride,
            china=china, crash_in=True)
    _lead_hook(sc, t0, bars // 4, 96 + lift, lyrics=lyrics)
    if orch:
        _orch_hits(sc, t0, bars, vel=102 + lift, dense=dense)


# ---------------------------------------------------------------------------
# Section builders (one per movement, in order)
# ---------------------------------------------------------------------------

def intro(sc) -> None:
    """The riff kicks the doors in: guitar + punches, then the full band."""
    _riff(sc, 0.0, 4)
    sc.hit(49, 0.0, 118, jt=0)
    sc.hit(36, 0.0, 112, jt=0)
    sc.hit(36, 4.0, 104, jt=2)
    sc.hit(36, 6.0, 100, jt=2)
    sc.hit(52, 8.0, 108, jt=0)
    for i in range(2):                      # bars 3-4: the kit warms up
        b = 8.0 + 4.0 * i
        sc.hit(36, b, 104, jt=2)
        sc.hit(36, b + 2.5, 98, jt=2)
        sc.hit(38, b + 1.0, 102, jt=2, jv=4)
        sc.hit(38, b + 3.0, 104, jt=2, jv=4)
        for k in range(8):
            sc.hit(42, b + 0.5 * k, 62 if k % 2 == 0 else 48, jt=2, jv=5)
    for k in range(8):                      # bar 4: snare pickup
        sc.hit(38, 15.0 + 0.125 * k, int(en.lerp(36, 96, k / 7)), jt=1)
    _groove(sc, 16.0, 4, 0.75, crash_in=True)
    _bass_drive(sc, 16.0, [1, 1, 6, 7], reps=1, vel=98)
    en.echo_throw(sc, DRIVE, 30.0, base=0, peak=74, release=2.0)


def verse1(sc) -> None:
    t0 = 32.0
    _chug(sc, t0, 16, VERSE_PROG, vel=66)
    _bass_verse(sc, t0, VERSE_PROG, reps=4, vel=96)
    _groove(sc, t0, 16, 0.55)
    for i in range(4):                      # drive punctuation stabs
        _power(sc, _groot(1), t0 + 16.0 * i, 0.7, 88, jt=0)


def pre1(sc) -> None:
    _pre(sc, 96.0)


def chorus1(sc) -> None:
    _chorus(sc, 128.0, 16, lyrics=True)


def verse2(sc) -> None:
    t0 = 192.0
    _chug(sc, t0, 8, VERSE_PROG, vel=68)
    _bass_verse(sc, t0, VERSE_PROG, reps=2, vel=98)
    _groove(sc, t0, 8, 0.6, crash_in=True)
    for i in range(4):                      # bars 5-8: light drive chug
        b = t0 + 16.0 + 4.0 * i
        r = _groot(VERSE_PROG[i % 4])
        for k in range(8):
            sc.note(DRIVE, r, b + 0.5 * k, 0.3,
                    66 + (6 if k in (0, 5) else 0) - (4 if k % 2 else 0),
                    jt=2, jv=3)


def pre2(sc) -> None:
    _pre(sc, 224.0)


def chorus2(sc) -> None:
    _chorus(sc, 256.0, 16, lift=2, ride=True, lyrics=True, orch=True)
    en.echo_throw(sc, LEAD, 314.0, base=0, peak=80, release=2.5)


def middle8(sc) -> None:
    """THE TRADING FOURS: three rounds — the band calls in fours, the kit
    answers in fours, band dead silent on the answers (oracle-pinned;
    the drum fours are DRUM_SOLO_SPEC windows)."""
    t0 = 320.0
    _band_four(sc, t0, lift=0)
    _four_engine(sc, t0 + 16.0)
    _band_four(sc, t0 + 32.0, lift=6)
    _four_chokes(sc, t0 + 48.0)
    _band_four(sc, t0 + 64.0, lift=12, china=True)
    _four_cyclone(sc, t0 + 80.0)


def breakdown_solo(sc) -> None:
    """The 8-bar UNACCOMPANIED breakdown: the kick-snare engine grows
    chokes, then the CYCLONE lands twice (bars 5 and 8, pinned).  Phrase
    arc: statement / answer / chokes / doubled engine // cyclone /
    choke summit / engine max / cyclone reprise.  Second half out-hits
    the first (oracle: breakdown_build)."""
    t0 = 416.0
    # Bar 1 — statement (16 hits).
    b = t0
    sc.hit(49, b, 116, jt=0)
    for beat, v in ((0.0, 112), (0.75, 98), (1.25, 100), (2.0, 108),
                    (2.75, 96)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(38, b + 1.0, 112, jt=2, jv=4)
    sc.hit(38, b + 3.0, 114, jt=2, jv=4)
    for beat, v in ((0.5, 36), (1.75, 42), (2.5, 38), (3.75, 46)):
        sc.hit(38, b + beat, v, jt=3, jv=6)
    for k in range(4):
        sc.hit(42, b + k, 64 if k % 2 == 0 else 52, jt=2, jv=5)
    # Bar 2 — answer (13 hits).
    b = t0 + 4.0
    for beat, v in ((0.0, 108), (0.75, 96), (1.5, 100), (2.25, 102),
                    (3.5, 96)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    sc.hit(38, b + 1.0, 110, jt=2, jv=4)
    sc.hit(38, b + 3.0, 112, jt=2, jv=4)
    sc.hit(38, b + 2.5, 40, jt=3, jv=6)
    sc.hit(38, b + 3.25, 42, jt=3, jv=6)
    sc.hit(46, b + 0.5, 76, jt=2)
    sc.hit(46, b + 2.5, 72, jt=2)
    sc.hit(53, b + 3.5, 82, jt=2)
    sc.hit(41, b + 3.75, 88, jt=2)
    # Bar 3 — the chokes join, left <-> right (16 hits).
    b = t0 + 8.0
    for off, cym in ((0.0, 52), (1.0, 49), (2.0, 55), (3.0, 57)):
        sc.hit(cym, b + off, 108, jt=0 if off == 0.0 else 1)
        sc.hit(38, b + off + 0.25, 86, jt=1, jv=4)
    for beat, v in ((0.0, 106), (0.5, 96), (1.5, 100), (2.5, 102),
                    (3.5, 98)):
        sc.hit(36, b + beat, v, jt=0 if beat == 0.0 else 2)
    for beat in (0.75, 1.75, 2.75):
        sc.hit(42, b + beat, 62, jt=2, jv=5)
    # Bar 4 — the engine doubles (BURST: 24 hits).
    b = t0 + 12.0
    sc.hit(52, b, 110, jt=0)
    _interlock(sc, b, 94, _ENGINE_KICKS, _ENGINE_ACCENTS)
    for beat in (0.5, 1.5, 2.5, 3.5):
        sc.hit(42, b + beat, 58, jt=2, jv=5)
    sc.hit(46, b + 3.5, 80, jt=1)
    sc.hit(38, b + 3.75, 52, jt=1)
    sc.hit(38, b + 3.875, 62, jt=1)
    # Bar 5 — CYCLONE, first statement (36 hits, pinned).
    _cyclone(sc, t0 + 16.0)
    # Bar 6 — choke summit breath (16 hits).
    b = t0 + 20.0
    for k, cym in enumerate((52, 49, 55, 57, 52, 49, 57, 55)):
        sc.hit(cym, b + 0.5 * k, int(en.lerp(94, 112, k / 7)),
               jt=0 if k == 0 else 1)
    for k in range(4):
        sc.hit(36, b + k, 104, jt=0 if k == 0 else 2)
    sc.hit(38, b + 1.0, 108, jt=2, jv=4)
    sc.hit(38, b + 3.0, 110, jt=2, jv=4)
    sc.hit(41, b + 3.25, 92, jt=1)
    sc.hit(43, b + 3.5, 96, jt=1)
    # Bar 7 — the engine at maximum (BURST: 22 hits).
    b = t0 + 24.0
    sc.hit(49, b, 114, jt=0)
    _interlock(sc, b, 100, _ENGINE_KICKS, _ENGINE_ACCENTS)
    for k in range(4):
        sc.hit(42, b + k, 62, jt=2, jv=5)
    sc.hit(52, b + 2.0, 108, jt=1)
    # Bar 8 — CYCLONE reprise, lifted (36 hits, pinned).
    _cyclone(sc, t0 + 28.0, vel_off=6)


def drop(sc) -> None:
    """THE PRODUCED DROP: the floor falls away to a portamento bass
    drone (A3 gliding down to A2) whose expression ducks then blooms,
    under a cymbal swell that rises into the re-entry slam.  Quiet, not
    silent — the drone keeps check_gaps green with no whitelist."""
    t0 = 448.0
    en.portamento_on(sc, BASS, t0 + 0.02, time_cc=68)
    sc.note(BASS, 57, t0, 2.2, 78, jt=0, jv=0)
    sc.note(BASS, 45, t0 + 2.0, 13.4, 74, jt=0, jv=0)
    en.portamento_off(sc, BASS, t0 + 15.9)
    en.expr_curve(sc, BASS, [(t0, 127), (t0 + 6.0, 64), (t0 + 12.0, 84),
                             (t0 + 15.9, 127)], step=0.5)
    # The cymbal swell: ride breaths, then the crash roll gathers.
    for k in range(16):
        sc.hit(51, t0 + 0.5 * k, int(en.lerp(16, 40, k / 15)), jt=2, jv=3)
    sc.hit(55, t0 + 10.0, 44, jt=2)
    for k in range(8):
        sc.hit(49, t0 + 12.0 + 0.5 * k, int(en.lerp(36, 78, k / 7)),
               jt=1, jv=3)
    for k in range(4):
        sc.hit(52, t0 + 15.0 + 0.25 * k, int(en.lerp(60, 92, k / 3)),
               jt=1, jv=3)
    for k in range(4):                      # snare drag into the slam
        sc.hit(38, t0 + 15.0 + 0.25 * k, int(en.lerp(36, 104, k / 3)),
               jt=0, jv=2)


def final_chorus(sc) -> None:
    """THE RE-ENTRY SLAM into the double final chorus: everything lands
    on the downbeat at once; the timpani arrive (LATE_CHANNELS) and the
    bass takes its 4-bar hook break in bars 13-16; a 4-bar half-time tag
    crowns it with the lead's kill-switch octave dive (RPN range 12)."""
    t0 = 464.0
    sc.hit(52, t0, 120, jt=0)               # china atop the slam crash
    sc.hit(57, t0, 112, jt=0)
    _chorus(sc, t0, 16, lift=8, ride=True, china=True, lyrics=True,
            orch=True, dense=True, bass=False)
    _bass_drive(sc, t0, CHORUS_PROG, reps=3, vel=110)
    for off, deg, dur in _BASS_HOOK:        # bars 13-16: the bass sings
        sc.note(BASS, en.pitch(A2, _MODE, deg), t0 + 48.0 + off, dur,
                108 + (4 if off in (0.0, 8.0) else 0),
                jt=0 if off == 0.0 else 2, jv=3)
    _timp_final(sc, t0)
    # The tag (bars 17-20): the colossus — F, G, Am, Am, every chord
    # restruck and pushed so the tag out-shouts the verses it crowns.
    tag = t0 + 64.0
    for off, deg in ((0.0, 6), (4.0, 7), (8.0, 1), (12.0, 1)):
        b = tag + off
        _power(sc, _groot(deg), b, 2.4, 110, jt=0)
        for kk in (2.5, 3.0, 3.5):
            _power(sc, _groot(deg), b + kk, 0.4, 102, jt=1)
        r = _groot(deg) + 12
        for beat, dur in ((0.0, 1.9), (2.0, 1.9)):
            sc.note(PIANO, r, b + beat, dur, 96, jt=0 if beat == 0.0 else 2,
                    jv=3)
            for p in _triad(deg, octave=2):
                sc.note(PIANO, p, b + beat, dur, 90,
                        jt=0 if beat == 0.0 else 2, jv=3)
        en.sustain(sc, PIANO, b + 0.02, b + 3.9)
        d = _BDEG[deg]
        sc.note(BASS, en.pitch(A2, _MODE, d), b, 1.4, 106, jt=0, jv=2)
        for beat, dg in ((2.0, d), (2.5, d + 1), (3.0, d + 2),
                         (3.5, d + 1)):
            sc.note(BASS, en.pitch(A2, _MODE, dg), b + beat, 0.45, 102,
                    jt=2, jv=3)
    for p in (57, 69):                      # tag orchestra stabs
        sc.note(ORCH, p, tag, 0.6, 112, jt=0, jv=0)
        sc.note(ORCH, p, tag + 4.0, 0.5, 108, jt=0, jv=0)
        sc.note(ORCH, p, tag + 8.0, 0.6, 110, jt=0, jv=0)
        sc.note(ORCH, p, tag + 12.0, 0.5, 108, jt=0, jv=0)
    for k, off in enumerate((0.0, 4.0, 8.0, 12.0)):   # tag kit
        sc.hit(49 if k % 2 == 0 else 57, tag + off, 114, jt=0)
        sc.hit(36, tag + off, 110, jt=0)
        sc.hit(38, tag + off + 2.0, 106, jt=1, jv=3)
        sc.hit(52, tag + off + 2.0, 96, jt=1)
        sc.hit(36, tag + off + 2.5, 98, jt=1)
        sc.hit(36, tag + off + 3.0, 100, jt=1)
        sc.hit(38, tag + off + 3.5, 90, jt=1, jv=3)
        for kk in range(5 if k == 3 else 8):          # ride keeps driving
            sc.hit(51, tag + off + 0.5 * kk, 80 if kk % 2 == 0 else 64,
                   jt=2, jv=4)
    for k, key in enumerate((41, 43, 45, 47, 48, 50)):   # rush to outro
        sc.hit(key, tag + 14.5 + 0.25 * k, int(en.lerp(84, 112, k / 5)),
               jt=1)
    # The lead's held A5 and the kill-switch dive (bend range 12).
    en.bend_range(sc, LEAD, 12, tag - 0.10)
    sc.note(LEAD, 81, tag, 13.0, 104, jt=0, jv=0)
    en.cc_curve(sc, LEAD, 1, [(tag + 0.5, 0), (tag + 6.0, 62),
                              (tag + 10.0, 20)], step=0.2)
    en.echo_throw(sc, LEAD, tag + 10.0, base=8, peak=86, release=3.0)
    en.bend_ramp(sc, LEAD, tag + 10.5, tag + 14.0, 0.0, -2.0, steps=24)
    sc.bend(LEAD, tag + 15.0, 0.0)
    en.bend_range(sc, LEAD, 2, tag + 15.4)


def outro(sc) -> None:
    """The riff walks the amp stack off stage, then the power-down."""
    t0 = 544.0
    _riff(sc, t0, 2, vel_scale=0.92)
    _groove(sc, t0, 4, 0.6, crash_in=True, fills=False)
    _bass_drive(sc, t0, [1, 1, 6, 7], reps=1, vel=92)
    for i in range(4):                      # dying palm-mute echoes
        b = t0 + 4.0 * i
        r = _groot([1, 1, 6, 7][i])
        for beat in (1.5, 3.5):
            sc.note(MUTE, r, b + beat, 0.24, int(en.lerp(54, 38, i / 3)),
                    jt=2, jv=3)
    # The power-down: two held blasts, ten thousand watts to zero.
    b = t0 + 16.0
    _power(sc, 45, b, 7.5, 98, jt=0)
    sc.note(BASS, 45, b, 7.5, 92, jt=0, jv=0)
    sc.hit(49, b, 114, jt=0)
    sc.hit(36, b, 108, jt=0)
    en.cc_curve(sc, DRIVE, 11, [(b, 112), (b + 7.0, 66)], step=0.5)
    for k, (off, p) in enumerate(((2.0, 81), (3.0, 76), (4.0, 72),
                                  (5.0, 69))):
        sc.note(PIANO, p, b + off, 1.4, int(en.lerp(62, 46, k / 3)),
                jt=2, jv=3)
    en.sustain(sc, PIANO, b + 2.02, b + 7.9)
    en.echo_throw(sc, DRIVE, b + 6.0, base=0, peak=78, release=4.0)
    b = t0 + 24.0
    _power(sc, 45, b, 7.5, 90, jt=0)
    sc.note(BASS, 45, b, 7.5, 86, jt=0, jv=0)
    sc.hit(49, b, 104, jt=0)
    sc.hit(36, b, 100, jt=0)
    sc.note(PIANO, 81, b, 4.0, 54, jt=0, jv=3)
    sc.note(PIANO, 88, b, 4.0, 46, jt=0, jv=3)
    en.sustain(sc, PIANO, b + 0.02, b + 6.9)
    en.cc_curve(sc, DRIVE, 11, [(b + 0.5, 100), (b + 7.5, 24)], step=0.5)
    sc.hit(52, b + 4.0, 52, jt=0)
    sc.hit(46, b + 6.0, 38, jt=0)


BUILDERS = [intro, verse1, pre1, chorus1, verse2, pre2, chorus2, middle8,
            breakdown_solo, drop, final_chorus, outro]

# ---------------------------------------------------------------------------
# Verification config (HLD §6)
# ---------------------------------------------------------------------------

PROGRAM_WHITELIST = {0, 28, 29, 30, 33, 47, 55, 81}
CENTERED_CHANNELS = {PIANO, BASS, LEAD, DRUMS, TIMP, ORCH}
NOTE_RANGES = {
    PIANO: (45, 96), MUTE: (39, 62), DRIVE: (39, 70), BASS: (36, 60),
    LEAD: (60, 84), TIMP: (40, 55), ORCH: (55, 71),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (243.0, 260.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

ENERGY_RULES = [
    ("chorus1", ">=", "verse1", 1.2),
    ("chorus2", ">=", "chorus1", 1.0),
    ("middle8", "<=", "chorus2", 0.75),
    ("drop", "<=", "chorus2", 0.30),        # the produced drop (HLD §4 t09)
    ("final_chorus", ">=", "chorus1", 1.05),
    ("final_chorus", ">=", "chorus2", 1.0),
    ("intro", "<=", "chorus1", 1.0),
    ("pre1", "<=", "chorus1", 1.0),
    ("pre2", "<=", "chorus2", 1.0),
    ("verse2", "<=", "chorus2", 1.0),
    ("outro", "<=", "final_chorus", 0.8),
]
LATE_CHANNELS = {ORCH: 256.0, TIMP: 464.0}
BASS_SPEC = {
    "channel": BASS,
    "sections": [("verse1", 9), ("chorus1", 9), ("verse2", 9),
                 ("chorus2", 9), ("final_chorus", 9)],
    "hook": "final_chorus",
}
# CHOIR_SPEC deliberately omitted — hard-rock track, no choir (HLD D3).
DRUM_SOLO_SPEC = {
    # The three trading drum fours + the unaccompanied breakdown.  No
    # accompanists anywhere: the drum bars are band-silent by design
    # (the drop is NOT a solo window — its drone is a produced texture).
    "windows": [(336.0, 352.0), (368.0, 384.0), (400.0, 416.0),
                (416.0, 448.0)],
    "accompanists": set(),
}
FEATURES_EXPECTED = {
    "bend_range", "pitch_bend", "cc1_vibrato", "cc74_wah", "cc64_sustain",
    "cc11_expression", "aftertouch", "portamento", "cc94_echo",
    "program_change",
}


# ---------------------------------------------------------------------------
# Track-specific oracles
# ---------------------------------------------------------------------------

def _spans(sc, ch):
    import verify
    return verify._note_spans(sc, ch)


def oracles(sc, info, spans):
    # 1. trading_fours — the middle-8's six 4-bar phrases STRICTLY
    # alternate band/drums: even phrases carry the drive-guitar stomp,
    # odd phrases are band-silent drum solos with real density.
    fails_tf: list[str] = []
    for k in range(6):
        w0 = 320.0 + 16.0 * k
        w1 = w0 + 16.0
        if k % 2 == 0:
            drive = [on for on, _off, _p, _v in _spans(sc, DRIVE)
                     if w0 - 1e-9 <= on < w1]
            if len(drive) < 8:
                fails_tf.append(f"band four at beat {w0:.0f}: only "
                                f"{len(drive)} drive-guitar onsets (< 8)")
        else:
            band = 0
            for ch in sc.events:
                if ch == DRUMS:
                    continue
                band += sum(1 for on, _off, _p, _v in _spans(sc, ch)
                            if w0 - 1e-9 <= on < w1 - 0.05)
            if band:
                fails_tf.append(f"drum four at beat {w0:.0f}: {band} band "
                                f"note-ons (must be silent)")
            hits = sum(1 for on, _off, _p, _v in _spans(sc, DRUMS)
                       if w0 - 1e-9 <= on < w1 - 1e-9)
            if hits < 48:
                fails_tf.append(f"drum four at beat {w0:.0f}: {hits} drum "
                                f"hits (< 48)")

    # 2. breakdown_build — the unaccompanied solo BUILDS: its second half
    # (the cyclone half) carries >= 1.15x the hits of its first half.
    fails_build: list[str] = []
    ons = [on for on, _off, _p, _v in _spans(sc, DRUMS)]
    a = sum(1 for on in ons if 416.0 - 1e-9 <= on < 432.0)
    b = sum(1 for on in ons if 432.0 <= on < 448.0 - 1e-9)
    if b < 1.15 * a:
        fails_build.append(f"breakdown second half has {b} hits, "
                           f"< 1.15 x first half ({a})")

    # 3. cyclone_recurrence — the around-the-kit 32nd CYCLONE figure is
    # stated at bar 5 and reprised at bar 8, recomputed from _CYCLONE
    # (not copied): every stroke at its exact tick, both statements.
    fails_cyc: list[str] = []
    actual = {(round(on * en.PPQ), p)
              for on, _off, p, _v in _spans(sc, DRUMS)}
    for where, anchor in (("bar 5", 432.0), ("bar 8", 444.0)):
        missing = [(off, key) for off, key, _v in _CYCLONE
                   if (round((anchor + off) * en.PPQ), key) not in actual]
        if missing:
            fails_cyc.append(f"cyclone {where} (beat {anchor:.0f}): "
                             f"missing strokes {missing[:3]}")

    return [("trading_fours", fails_tf),
            ("breakdown_build", fails_build),
            ("cyclone_recurrence", fails_cyc)]


# ---------------------------------------------------------------------------
# Audio oracles — thresholds provisional until the phase-D freeze
# (HLD §6.2: re-measured on the assembled-album render, then pinned).
# ---------------------------------------------------------------------------

# PROVISIONAL thresholds — measured 2026.07.11 on this worktree's
# per-track render (ferrosintesis 0.13.x); re-pinned at phase D on the
# assembled-album render.  Measured: lift 2.43 dB (pin - 1 dB); drop
# depth 13.11 dB (pin - 1.6); slam 13.63 dB (pin - 1.6); breakdown
# side/mid 0.118 (pin - 25%).
_LIFT_DB = 1.4        # PROVISIONAL: final chorus over verse 1
_DROP_DB = 11.5       # PROVISIONAL: drop depth below chorus 2
_SLAM_DB = 12.0       # PROVISIONAL: re-entry slam bar over the drop
_SPREAD_MIN = 0.088   # PROVISIONAL: breakdown side/mid |L-R| ratio


def audio_checks(ctx):
    def wdb(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    verse = wdb(36.0, 92.0)
    chorus2 = wdb(260.0, 316.0)
    dropv = wdb(448.0, 464.0)
    slam = wdb(464.0, 468.0)
    final = wdb(464.0, 528.0)

    fails_lift: list[str] = []
    if final < verse + _LIFT_DB:
        fails_lift.append(f"final chorus {final:.1f} dB < verse "
                          f"{verse:.1f} dB + {_LIFT_DB}")

    # The drop must LAND (HLD §6.2): deep below chorus 2, and the first
    # final-chorus bar must slam back over it.
    fails_drop: list[str] = []
    if dropv > chorus2 - _DROP_DB:
        fails_drop.append(f"drop {dropv:.1f} dB not <= chorus2 "
                          f"{chorus2:.1f} dB - {_DROP_DB}")
    fails_slam: list[str] = []
    if slam < dropv + _SLAM_DB:
        fails_slam.append(f"re-entry bar {slam:.1f} dB < drop "
                          f"{dropv:.1f} dB + {_SLAM_DB}")

    # Breakdown stereo spread: within-window side/mid ratio (HLD §6.2 —
    # no cross-section baseline; floor measured, then pinned).
    fails_spread: list[str] = []
    i0, i1 = ctx.bar_window(416.0, 448.0)
    acc_s = acc_m = 0.0
    for a, b in zip(ctx.l[i0:i1], ctx.r[i0:i1]):
        acc_s += (a - b) * (a - b)
        acc_m += (a + b) * (a + b)
    ratio = (acc_s / acc_m) ** 0.5 if acc_m > 0 else 0.0
    if ratio < _SPREAD_MIN:
        fails_spread.append(f"breakdown side/mid {ratio:.3f} "
                            f"< {_SPREAD_MIN}")

    return [("chorus_lift", fails_lift),
            ("drop_depth", fails_drop),
            ("reentry_slam", fails_slam),
            ("breakdown_spread", fails_spread)]
