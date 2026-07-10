"""t08_ten_metres — Track 8 "Ten Metres of Air" of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T8 — Fine Line I: the high
dive, told as one unbroken line up the tower, off the board, through
ten metres of air, and into the water.

* THE CLIMB — four platforms, and the key centre rises a minor third
  per platform (Bb -> Db -> E -> G); the ladder figure is IDENTICAL on
  every platform, only transposed, so the mean register climbs with the
  diver (both oracle-pinned).  Under it all a heartbeat kick whose
  inter-onset interval — measured in SECONDS through every tempo
  change — strictly decreases from the first rung to the edge of the
  board (~46 bpm to ~125 bpm, oracle-pinned strict).
* THE BOARD — the minor-third ladder closes its cycle: G + m3 = Bb, the
  note you started on, ten metres higher.  Time stretches (58 bpm) and
  the texture thins to ONE high flute over the still-quickening heart
  (voice-count oracle).  A reverse-cymbal riser swells and stops
  EXACTLY at the silence.
* THE JUMP — one full bar of scored silence: zero events of any kind
  inside it (oracle scans every channel for every status byte), and the
  render's RMS inside the bar sits near the noise floor (audio oracle).
* THE PLUNGE — material.DIVE_CASCADE at four successive octaves
  (recomputed from material.py, never re-typed), harp glissandi falling
  with the diver.
* THE SPLASH — tam-tam (GM 14 + CC0 alt-bank gong ageng) + taiko + low
  toms + sub swell; the splash bar is the piece's global energy maximum
  (per-4-beat velocity-sum oracle, mirrored in RMS by audio_checks).
* UNDERWATER — dark and slow: every sustained channel authors CC74 <=
  40 (oracle), and slow pitch bends refract the light (bend-presence
  oracle; hygiene recentres them before surfacing).  audio_checks pins
  the spectral-centroid drop vs. the climb.
* SURFACING — Bb turns MAJOR: the orchestra hit of the crowd, a
  celebration groove, the cascade inverted into a climb-out theme.

Oracle-first: every claim above was a falsifiable check in oracles()
before a note was written.  All jitter comes from the Score's SEED rng
or a local random.Random derived from SEED; rebuilds are byte-identical.
"""

from __future__ import annotations

import math
import random

import conductor
import engine as en
import material

NUMBER = 8
TITLE = 'Ten Metres of Air'
FILE = '08 - Ten Metres of Air.mid'
SEED = 20260908

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_HI = 0        # high strings: ladder, dive cascade, refracted light  centred
CH_LO = 1        # low strings: pedals, sub swell, celebration bass     centred
CH_HARP = 2      # harp: poolside water, glissandi, sparkle             pan 54
CH_FLUTE = 3     # the board's lone flute; surfacing descant            centred
CH_CHOIR = 4     # awe pads, underwater hum, crowd "ah"                 centred
CH_BRASS = 5     # platform calls, surfacing fanfare                    centred
CH_TAIKO = 6     # taiko — the splash engine                            pan 72
CH_TAM = 7       # tam-tam: GM 14 + CC0 alt bank (gong ageng)           centred
CH_RISER = 8     # reverse cymbal — swells then stops                   centred
CH_KIT = 9       # kit v2: heartbeat, splash, celebration groove
CH_HIT = 10      # orchestra hit — the crowd                            pan 58
CH_VIBE = 11     # vibraphone: pool-light glints, bubbles               pan 76

MODE = "aeolian"
MAJ = "ionian"
TONIC_MID = 58                     # Bb3: platform 1's root

# ---------------------------------------------------------------------------
# The grid (all 4/4; the drama lives in the tempo map)
# ---------------------------------------------------------------------------

POOL_T0 = 0.0          # I.    poolside               @112
P1_T0 = 24.0           # II.   first platform, Bb     @112
P2_T0 = 72.0           # III.  second platform, Db    @116
P3_T0 = 120.0          # IV.   third platform, E      @120
P4_T0 = 168.0          # V.    fourth platform, G     @124
BOARD_T0 = 216.0       # VI.   the board, Bb again    @58 (time stretches)
JUMP_T0 = 248.0        # VII.  ONE BAR OF AIR         (scored silence)
PLUNGE_T0 = 252.0      # VIII. the plunge             @132
SPLASH_T0 = 260.0      # IX.   the splash             @132
UW_T0 = 268.0          # X.    underwater             @54
SURF_T0 = 332.0        # XI.   surfacing              @122, Bb MAJOR
END = 468.0

PLATFORMS = (P1_T0, P2_T0, P3_T0, P4_T0)
PLATFORM_PCS = (10, 1, 4, 7)       # Bb, Db, E, G — the minor-third ladder
PLATFORM_LEN = 48.0

RISER_T0 = 244.0                   # the riser's swell begins
HEART_T0 = 24.0                    # first heartbeat kick
HEART_T1 = 246.6                   # last kick allowed (beats)
HEART_IOI0 = 1.32                  # first inter-onset interval, SECONDS
HEART_DECAY = 0.993508             # per-kick geometric quickening

DIVE_TOP_ROOT = 82                 # Bb5: cascade octave 1 root (top = Bb6)
GROOVE_T0 = 340.0                  # the celebration groove
GROOVE_BARS = 28
CYCLE = (1, 4, 6, 5)               # Bb Eb Gm F — the celebration turnaround
UW_PROG = (1, 6, 4, 1, 3, 6, 4, 5)

TEMPO = [
    (0.0, 112.0), (72.0, 116.0), (120.0, 120.0), (168.0, 124.0),
    (216.0, 58.0), (252.0, 132.0), (268.0, 54.0), (332.0, 122.0),
]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Poolside", POOL_T0, P1_T0),
        ("II. First Platform", P1_T0, P2_T0),
        ("III. Second Platform", P2_T0, P3_T0),
        ("IV. Third Platform", P3_T0, P4_T0),
        ("V. Fourth Platform", P4_T0, BOARD_T0),
        ("VI. The Board", BOARD_T0, JUMP_T0),
        ("VII. The Jump", JUMP_T0, PLUNGE_T0),
        ("VIII. The Plunge", PLUNGE_T0, SPLASH_T0),
        ("IX. The Splash", SPLASH_T0, UW_T0),
        ("X. Underwater", UW_T0, SURF_T0),
        ("XI. Surfacing", SURF_T0, END),
    ],
    tempo_map=list(TEMPO),
    time_signatures=[(0.0, 4, 4)],
    keysigs=[
        (0.0, -5, 1),        # Bb minor
        (72.0, 4, 1),        # C# minor (Db, enharmonic)
        (120.0, 1, 1),       # E minor
        (168.0, -2, 1),      # G minor
        (216.0, -5, 1),      # Bb minor — the ladder closes its cycle
        (332.0, -2, 0),      # Bb MAJOR — surfacing
    ],
    channels=[
        (CH_HI, "high strings", 48, 96, 64, 55),
        (CH_LO, "low strings", 48, 100, 64, 50),
        (CH_HARP, "harp", 46, 100, 54, 50),
        (CH_FLUTE, "flute", 73, 98, 64, 45),
        (CH_CHOIR, "choir", 52, 98, 64, 62),
        (CH_BRASS, "brass", 61, 98, 64, 42),
        (CH_TAIKO, "taiko", 116, 106, 72, 45),
        (CH_TAM, "tam-tam (gong ageng)", 14, 104, 64, 70),
        (CH_RISER, "riser (reverse cymbal)", 119, 100, 64, 25),
        (CH_KIT, "kit", 0, 100, 64, 40),
        (CH_HIT, "orchestra hit (the crowd)", 55, 102, 58, 45),
        (CH_VIBE, "vibraphone", 11, 92, 76, 60),
    ],
    bank_selects=[(6, 1), (8, 1)],           # taiko + riser: percussion set B
    program_changes=[(CH_KIT, 0.0, 1)],      # non-zero kit program (V3 default)
    extra_markers=[
        (RISER_T0, "the last breath"),
        (460.0, "home water"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {11, 14, 46, 48, 52, 55, 61, 73, 116, 119}
CENTERED_CHANNELS: set[int] = {CH_HI, CH_LO, CH_FLUTE, CH_CHOIR, CH_BRASS,
                               CH_TAM, CH_RISER}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_HI: (45, 95),
    CH_LO: (36, 68),
    CH_HARP: (40, 95),
    CH_FLUTE: (64, 95),
    CH_CHOIR: (48, 80),
    CH_BRASS: (52, 82),
    CH_TAIKO: (36, 56),
    CH_TAM: (36, 50),
    CH_RISER: (64, 76),
    CH_HIT: (52, 66),
    CH_VIBE: (58, 96),
}
# The jump: the one whitelisted silence — a scored decision, not a bug.
GAP_WHITELIST: list[tuple[float, float]] = [(246.0, 252.5)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (289.0, 299.0)   # seconds
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

COMMENT = ("Track 08 of 'Through Lines' - Fine Line I: the high dive. "
           "Key centres climb by minor thirds per platform over a "
           "strictly quickening heartbeat; the board thins to one flute; "
           "one full bar of scored silence is the jump; the dive cascade "
           "falls four octaves into a gong-and-taiko splash (the piece's "
           "energy maximum); underwater closes every filter to CC74<=40; "
           "and Bb turns major as the crowd's orchestra hit brings the "
           "diver up.")


# ---------------------------------------------------------------------------
# Tempo-map arithmetic (static mirrors of Score.seconds_at, needed both by
# the heartbeat scheduler and by its oracle).
# ---------------------------------------------------------------------------

def _sec_at(beat: float) -> float:
    total, cursor, bpm = 0.0, 0.0, TEMPO[0][1]
    for tb, tbpm in TEMPO:
        if tb >= beat:
            break
        total += (tb - cursor) * 60.0 / bpm
        cursor, bpm = tb, tbpm
    return total + (beat - cursor) * 60.0 / bpm


def _beat_at(sec: float) -> float:
    total, cursor, bpm = 0.0, 0.0, TEMPO[0][1]
    for tb, tbpm in TEMPO:
        seg = (tb - cursor) * 60.0 / bpm
        if total + seg >= sec:
            break
        total += seg
        cursor, bpm = tb, tbpm
    return cursor + (sec - total) * bpm / 60.0


_HEART_CACHE: list[float] | None = None


def _heartbeat_beats() -> list[float]:
    """Kick onsets (tick-exact beats).  The realized inter-onset interval,
    in SECONDS, is strictly decreasing by construction: each candidate is
    tick-rounded and then pulled earlier until it beats the previous
    interval, so the oracle's strictness survives MIDI quantization."""
    global _HEART_CACHE
    if _HEART_CACHE is None:
        ticks = [int(round(HEART_T0 * en.PPQ))]
        target = HEART_IOI0
        prev = None
        while True:
            last_sec = _sec_at(ticks[-1] / en.PPQ)
            nxt = int(round(_beat_at(last_sec + target) * en.PPQ))
            nxt = max(nxt, ticks[-1] + 1)
            if prev is not None:
                while (nxt > ticks[-1] + 1
                       and _sec_at(nxt / en.PPQ) - last_sec >= prev - 1e-9):
                    nxt -= 1
            if nxt / en.PPQ > HEART_T1:
                break
            prev = _sec_at(nxt / en.PPQ) - last_sec
            ticks.append(nxt)
            target *= HEART_DECAY
        _HEART_CACHE = [t / en.PPQ for t in ticks]
    return _HEART_CACHE


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


def _ons(sc, ch, t0=-1e12, t1=1e12):
    return [nt for nt in _spans(sc, ch) if t0 <= nt[0] < t1]


def _ccs(sc, ch, num):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            out.append((tick / en.PPQ, data[2]))
    return sorted(out)


def _bends_semis(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / en.PPQ, (raw - 8192) / 8192.0 * 2.0))
    return sorted(out)


def _energy(sc, t0, t1, drums=True):
    tot = 0.0
    for ch in sc.events:
        if ch == CH_KIT and not drums:
            continue
        for on, _off, _p, v in _spans(sc, ch):
            if t0 <= on < t1:
                tot += v
    return tot / (t1 - t0)


def _pc_center(sc, t0, t1, chans=None):
    """Duration-weighted pitch-class histogram argmax over [t0, t1)."""
    w: dict[int, float] = {}
    for ch in sc.events:
        if ch == CH_KIT or (chans is not None and ch not in chans):
            continue
        for on, off, p, _v in _spans(sc, ch):
            if t0 <= on < t1:
                w[p % 12] = w.get(p % 12, 0.0) + max(0.25, off - on)
    return max(w, key=w.get) if w else None


def _o_platform_ladder(sc):
    """Key centres rise by a minor third per platform (Bb Db E G), and the
    board's flute closes the cycle back onto Bb."""
    fails = []
    got = []
    for i, t0 in enumerate(PLATFORMS):
        pc = _pc_center(sc, t0, t0 + PLATFORM_LEN)
        got.append(pc)
        if pc != PLATFORM_PCS[i]:
            fails.append(f"platform {i + 1} pitch-class centre {pc} != "
                         f"{PLATFORM_PCS[i]}")
    for a, b in zip(got, got[1:]):
        if a is None or b is None or (b - a) % 12 != 3:
            fails.append(f"ladder step {a}->{b} is not a minor third")
    board_pc = _pc_center(sc, BOARD_T0, JUMP_T0, chans={CH_FLUTE})
    if board_pc != 10:
        fails.append(f"board flute centres on pc {board_pc}, not Bb (10)")
    if got and got[-1] is not None and board_pc is not None \
            and (board_pc - got[-1]) % 12 != 3:
        fails.append("the board does not close the minor-third cycle")
    return fails


def _o_register_ascent(sc):
    """The ladder channel's mean register climbs ~3 semitones per platform
    (the identical figure, transposed with the key)."""
    fails = []
    means = []
    for i, t0 in enumerate(PLATFORMS):
        notes = _ons(sc, CH_HI, t0, t0 + PLATFORM_LEN)
        if not notes:
            fails.append(f"platform {i + 1}: no ladder notes")
            return fails
        means.append(sum(p for _on, _off, p, _v in notes) / len(notes))
    for i, (a, b) in enumerate(zip(means, means[1:])):
        if not 2.0 <= b - a <= 4.0:
            fails.append(f"platform {i + 1}->{i + 2} mean register moves "
                         f"{b - a:+.2f} semis (want +2..+4)")
    return fails


def _o_heartbeat(sc):
    """The heartbeat kick's inter-onset interval, in seconds, strictly
    decreases from the first rung to the edge of the board."""
    fails = []
    kicks = [on for on, _off, p, _v in _spans(sc, CH_KIT)
             if p == 36 and HEART_T0 - 0.01 <= on < JUMP_T0]
    if len(kicks) < 110:
        fails.append(f"{len(kicks)} heartbeat kicks, want >= 110")
        return fails
    secs = [_sec_at(b) for b in kicks]
    iois = [b - a for a, b in zip(secs, secs[1:])]
    bad = sum(1 for a, b in zip(iois, iois[1:]) if b >= a)
    if bad:
        fails.append(f"{bad} inter-onset intervals fail strict decrease")
    if iois[0] < 1.1:
        fails.append(f"first interval {iois[0]:.2f}s, want >= 1.1 (calm)")
    if iois[-1] > 0.55:
        fails.append(f"last interval {iois[-1]:.2f}s, want <= 0.55 (racing)")
    if kicks[-1] < 240.0:
        fails.append(f"heart stops at beat {kicks[-1]:.1f}, short of the "
                     f"board's edge")
    return fails


def _o_board_thins(sc):
    """The board is ONE flute over the heartbeat — no other voice sounds
    (the riser is admitted only for its final swell into the silence)."""
    fails = []
    for ch in sc.events:
        for on, _off, p, _v in _ons(sc, ch, BOARD_T0, JUMP_T0):
            if ch == CH_FLUTE:
                continue
            if ch == CH_KIT and p in (35, 36):
                continue
            if ch == CH_RISER and on >= RISER_T0 - 1e-6:
                continue
            fails.append(f"board texture broken: ch{ch} pitch {p} at "
                         f"beat {on:.2f}")
    if len(_ons(sc, CH_FLUTE, BOARD_T0, JUMP_T0)) < 8:
        fails.append("the board wants its flute (>= 8 notes)")
    return fails[:8]


def _o_riser(sc):
    """Exactly one reverse-cymbal riser on the board, ENDING exactly at
    the silence (its note-off tick == the jump's first tick)."""
    fails = []
    notes = _ons(sc, CH_RISER, BOARD_T0, PLUNGE_T0)
    if len(notes) != 1:
        return [f"{len(notes)} riser notes in [board, plunge), want exactly 1"]
    on, off, _p, vel = notes[0]
    if abs(on - RISER_T0) > 0.01:
        fails.append(f"riser starts at {on:.2f}, want {RISER_T0}")
    if abs(off - JUMP_T0) > 1e-6:
        fails.append(f"riser stops at {off:.4f}, must stop EXACTLY at the "
                     f"silence ({JUMP_T0})")
    if vel < 80:
        fails.append(f"riser velocity {vel} too shy (>= 80)")
    return fails


def _o_jump_empty(sc):
    """THE JUMP: zero channel events of ANY kind inside the silent bar."""
    t0k = int(round(JUMP_T0 * en.PPQ))
    t1k = int(round(PLUNGE_T0 * en.PPQ))
    fails = []
    for ch in sorted(sc.events):
        for tick, _prio, data in sc.events[ch]:
            if t0k < tick < t1k:
                fails.append(f"ch{ch} event 0x{data[0] & 0xF0:02X} at tick "
                             f"{tick} inside the scored silence")
    return fails[:8]


def _o_dive_cascade(sc):
    """The plunge is material.DIVE_CASCADE at four successive octaves —
    recomputed from material.py, note-for-note, onset-for-onset."""
    want = []
    for k in range(4):
        root = DIVE_TOP_ROOT - 12 * k
        for i, d in enumerate(material.DIVE_CASCADE):
            want.append((PLUNGE_T0 + (8 * k + i) * material.DIVE_STEP,
                         en.pitch(root, material.DIVE_MODE, d)))
    got = [(on, p) for on, _off, p, _v in _ons(sc, CH_HI, PLUNGE_T0,
                                               SPLASH_T0)]
    fails = []
    if len(got) != len(want):
        return [f"{len(got)} cascade notes, want {len(want)} (4 octaves x "
                f"{len(material.DIVE_CASCADE)})"]
    for i, ((won, wp), (gon, gp)) in enumerate(zip(want, got)):
        if gp != wp or abs(gon - won) > 0.02:
            fails.append(f"cascade note {i + 1}: got ({gon:.3f}, {gp}), "
                         f"want ({won:.3f}, {wp})")
    return fails[:8]


def _o_splash_anatomy(sc):
    """The splash: alt-bank tam-tam (program 14 + CC0 != 0) + taiko + low
    toms + kick + crash, all inside the splash bar."""
    fails = []
    cc0 = [v for b, v in _ccs(sc, CH_TAM, 0) if b <= SPLASH_T0]
    if not cc0 or cc0[-1] == 0:
        fails.append("tam-tam channel must author CC0 != 0 (gong alt bank)")
    progs = [data[1] for _t, _p, data in sc.events.get(CH_TAM, [])
             if (data[0] & 0xF0) == 0xC0]
    if progs != [14]:
        fails.append(f"tam-tam programs {progs} != [14]")
    tam = _ons(sc, CH_TAM, SPLASH_T0, SPLASH_T0 + 4.0)
    if len(tam) != 1:
        fails.append(f"{len(tam)} tam strikes in the splash bar, want 1")
    else:
        on, off, _p, vel = tam[0]
        if abs(on - SPLASH_T0) > 0.05:
            fails.append(f"tam strikes at {on:.2f}, want {SPLASH_T0}")
        if vel < 110:
            fails.append(f"tam velocity {vel} < 110")
        if off - on < 6.0:
            fails.append("the gong must ring (>= 6 beats)")
    if len(_ons(sc, CH_TAIKO, SPLASH_T0, SPLASH_T0 + 4.0)) < 12:
        fails.append("splash bar taiko underpowered (< 12 strokes)")
    kit = _ons(sc, CH_KIT, SPLASH_T0, SPLASH_T0 + 4.0)
    if sum(1 for _o, _f, p, _v in kit if p in (41, 43, 45)) < 3:
        fails.append("splash bar wants >= 3 low-tom strokes")
    if sum(1 for _o, _f, p, _v in kit if p in (49, 57)) < 1:
        fails.append("splash bar wants a crash")
    if sum(1 for _o, _f, p, _v in kit if p == 36) < 1:
        fails.append("splash bar wants its kick")
    return fails


def _o_splash_energy(sc):
    """The splash bar is the piece's global energy maximum (velocity sum
    over aligned 4-beat windows)."""
    windows: dict[float, float] = {}
    w = 0.0
    while w < END:
        windows[w] = 0.0
        w += 4.0
    for ch in sc.events:
        for on, _off, _p, v in _spans(sc, ch):
            key = 4.0 * math.floor(on / 4.0)
            if key in windows:
                windows[key] += v
    splash = windows[SPLASH_T0]
    fails = []
    for w, v in sorted(windows.items()):
        if w != SPLASH_T0 and v >= splash:
            fails.append(f"window [{w:.0f},{w + 4:.0f}) energy {v:.0f} >= "
                         f"the splash bar's {splash:.0f}")
    return fails[:8]


UW_DARK_CHANNELS = (CH_HI, CH_LO, CH_CHOIR)


def _o_underwater_dark(sc):
    """Underwater every sustained channel authors CC74, all values <= 40."""
    fails = []
    for ch in UW_DARK_CHANNELS:
        vals = [v for b, v in _ccs(sc, ch, 74) if UW_T0 <= b < SURF_T0]
        if not vals:
            fails.append(f"ch{ch} authors no CC74 underwater")
        elif max(vals) > 40:
            fails.append(f"ch{ch} CC74 reaches {max(vals)} underwater "
                         f"(must stay <= 40)")
    return fails


def _o_refraction(sc):
    """Slow bends like refracted light: present, gentle, and recentred."""
    fails = []
    bends = [(b, s) for b, s in _bends_semis(sc, CH_HI)
             if UW_T0 <= b < SURF_T0]
    if len(bends) < 24:
        fails.append(f"only {len(bends)} bend events underwater (>= 24)")
        return fails
    peak = max(abs(s) for _b, s in bends)
    if not 0.15 <= peak <= 0.95:
        fails.append(f"bend peak {peak:.2f} semis outside [0.15, 0.95]")
    if abs(bends[-1][1]) > 0.02:
        fails.append(f"last underwater bend {bends[-1][1]:+.2f} not "
                     f"recentred before surfacing")
    return fails


def _o_surfacing(sc):
    """Surfacing: the crowd's orchestra hit, a celebration groove, and Bb
    turned MAJOR (no Db anywhere; the major third everywhere; the final
    sonority a Bb major chord)."""
    fails = []
    hits = _ons(sc, CH_HIT, SURF_T0, END)
    if len(hits) < 6:
        fails.append(f"{len(hits)} orchestra hits, want >= 6 (the crowd)")
    kit = _spans(sc, CH_KIT)
    good_bars = 0
    n_bars = 0
    b = GROOVE_T0
    while b < GROOVE_T0 + 4.0 * GROOVE_BARS:
        n_bars += 1
        kick = any(p == 36 and abs(on - b) < 0.1 for on, _f, p, _v in kit)
        sn1 = any(p == 38 and abs(on - (b + 1.0)) < 0.1
                  for on, _f, p, _v in kit)
        sn3 = any(p == 38 and abs(on - (b + 3.0)) < 0.1
                  for on, _f, p, _v in kit)
        if kick and sn1 and sn3:
            good_bars += 1
        b += 4.0
    if good_bars < 0.9 * n_bars:
        fails.append(f"groove holds in only {good_bars}/{n_bars} bars")
    pc_counts: dict[int, int] = {}
    for ch in sc.events:
        if ch == CH_KIT:
            continue
        for on, _off, p, _v in _ons(sc, ch, SURF_T0, END):
            pc_counts[p % 12] = pc_counts.get(p % 12, 0) + 1
    if pc_counts.get(1, 0):
        fails.append(f"{pc_counts[1]} Db notes after surfacing (the minor "
                     f"third must be gone)")
    if pc_counts.get(2, 0) < 20:
        fails.append(f"only {pc_counts.get(2, 0)} D naturals after "
                     f"surfacing (want >= 20: it is MAJOR now)")
    allnotes = [nt for ch in sc.events if ch != CH_KIT
                for nt in _spans(sc, ch)]
    max_off = max(off for _on, off, _p, _v in allnotes)
    final = [nt for nt in allnotes if nt[1] >= max_off - 0.5]
    pcs = {p % 12 for _on, _off, p, _v in final}
    if not pcs <= {10, 2, 5}:
        fails.append(f"final sonority pcs {sorted(pcs)} stray outside "
                     f"Bb major (10, 2, 5)")
    if not {10, 2} <= pcs:
        fails.append(f"final sonority pcs {sorted(pcs)} must include the "
                     f"root AND the major third")
    return fails


def _o_dramatic_arc(sc):
    """check_arc: platform (melodic) energies strictly rise; the board is
    a whisper; underwater stays dark; the celebration lifts."""
    e = [_energy(sc, t0, t0 + PLATFORM_LEN, drums=False)
         for t0 in PLATFORMS]
    fails = []
    if not e[0] < e[1] < e[2] < e[3]:
        fails.append("the climb must build: platform energies "
                     + " -> ".join(f"{v:.0f}" for v in e))
    board = _energy(sc, BOARD_T0, JUMP_T0, drums=False)
    if board > 0.15 * e[3]:
        fails.append(f"the board ({board:.0f}) is not thin enough "
                     f"(<= 0.15 x platform four {e[3]:.0f})")
    uw = _energy(sc, UW_T0, SURF_T0, drums=False)
    if uw > 0.5 * e[3]:
        fails.append(f"underwater ({uw:.0f}) too loud (<= 0.5 x {e[3]:.0f})")
    surf = _energy(sc, SURF_T0, END, drums=False)
    if surf < 1.5 * uw:
        fails.append(f"surfacing ({surf:.0f}) must celebrate "
                     f"(>= 1.5 x underwater {uw:.0f})")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("platform_ladder_m3", _o_platform_ladder(sc)),
        ("register_ascent", _o_register_ascent(sc)),
        ("heartbeat_accelerando", _o_heartbeat(sc)),
        ("board_thins_to_flute", _o_board_thins(sc)),
        ("riser_into_silence", _o_riser(sc)),
        ("jump_bar_zero_events", _o_jump_empty(sc)),
        ("dive_cascade_four_octaves", _o_dive_cascade(sc)),
        ("splash_anatomy", _o_splash_anatomy(sc)),
        ("splash_energy_max", _o_splash_energy(sc)),
        ("underwater_cc74_dark", _o_underwater_dark(sc)),
        ("underwater_refraction_bends", _o_refraction(sc)),
        ("surfacing_celebration", _o_surfacing(sc)),
        ("dramatic_arc", _o_dramatic_arc(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (run by analyze.py once the WAV exists)
# ---------------------------------------------------------------------------

def _fft(re, im):
    n = len(re)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]
    length = 2
    while length <= n:
        ang = -2.0 * math.pi / length
        wr, wi = math.cos(ang), math.sin(ang)
        half = length // 2
        for i in range(0, n, length):
            cr, ci = 1.0, 0.0
            for k in range(i, i + half):
                vr = re[k + half] * cr - im[k + half] * ci
                vi = re[k + half] * ci + im[k + half] * cr
                re[k + half], im[k + half] = re[k] - vr, im[k] - vi
                re[k], im[k] = re[k] + vr, im[k] + vi
                cr, ci = cr * wr - ci * wi, cr * wi + ci * wr
        length <<= 1


def _spectral_centroid(ctx, b0, b1, nwin=5, size=8192):
    """Mean spectral centroid (Hz) over `nwin` hann-windowed FFTs."""
    i0, i1 = ctx.bar_window(b0, b1)
    i1 = min(i1, len(ctx.l))
    if i1 - i0 <= size:
        starts = [max(0, i0)]
    else:
        step = (i1 - i0 - size) // max(1, nwin - 1)
        starts = [i0 + w * step for w in range(nwin)]
    cents = []
    for s in starts:
        re = [(ctx.l[s + k] + ctx.r[s + k]) * 0.5
              * (0.5 - 0.5 * math.cos(2.0 * math.pi * k / (size - 1)))
              for k in range(size)]
        im = [0.0] * size
        _fft(re, im)
        num = den = 0.0
        for k in range(1, size // 2):
            mag = math.hypot(re[k], im[k])
            num += (k * ctx.sample_rate / size) * mag
            den += mag
        if den > 0:
            cents.append(num / den)
    return sum(cents) / len(cents) if cents else 0.0


def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """Render-side mirrors of the headline claims."""
    def wdb(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    # 1. The jump's silence sits near the noise floor.
    silence = []
    tail = wdb(249.8, 251.8)          # past the riser's stop
    late = wdb(250.9, 251.85)         # the last moment before the water
    board = wdb(220.0, 240.0)
    if tail > -48.0:
        silence.append(f"jump bar tail {tail:.1f} dB, want <= -48")
    if late > -54.0:
        silence.append(f"jump bar last beat {late:.1f} dB, want <= -54")
    if tail > board - 20.0:
        silence.append(f"jump tail {tail:.1f} dB not >= 20 dB below the "
                       f"board ({board:.1f} dB)")

    # 2. The splash is the render's peak window.
    peak = []
    splash = wdb(SPLASH_T0, SPLASH_T0 + 4.0)
    worst, worst_w = -999.0, None
    w = 0.0
    while w + 4.0 <= END:
        if abs(w - SPLASH_T0) > 1e-6:
            v = wdb(w, w + 4.0)
            if v > worst:
                worst, worst_w = v, w
        w += 4.0
    if splash + 0.75 < worst:
        peak.append(f"splash {splash:.1f} dB below window "
                    f"[{worst_w:.0f},{worst_w + 4:.0f}) at {worst:.1f} dB")
    uw = wdb(272.0, 328.0)
    if splash < uw + 10.0:
        peak.append(f"splash {splash:.1f} dB not >= 10 dB above "
                    f"underwater ({uw:.1f} dB)")

    # 3. Underwater darkens: spectral centroid drops vs. the climb.
    dark = []
    c_climb = _spectral_centroid(ctx, 172.0, 212.0)
    c_uw = _spectral_centroid(ctx, 276.0, 324.0)
    if c_uw > 0.68 * c_climb:
        dark.append(f"underwater centroid {c_uw:.0f} Hz not <= 0.68 x "
                    f"climb {c_climb:.0f} Hz")
    return [("audio_jump_silence", silence),
            ("audio_splash_peak", peak),
            ("audio_underwater_centroid", dark)]


# ===========================================================================
# THE MUSIC — composed to pass the oracles above.
# ===========================================================================

PLAT_PROG = (1, 6, 3, 4, 1, 5)          # per platform, 8 beats each
# One bar of the ladder — IDENTICAL on every platform, transposed.
LADDER_CELL = ((0, 0.0, 0.5), (2, 0.5, 0.5), (4, 1.0, 1.0),
               (2, 2.0, 0.5), (4, 2.5, 0.5), (5, 3.0, 0.95))

BOARD_SOLO = (
    (82, 216.0, 5.5, 66),
    (85, 222.5, 1.5, 60), (84, 224.0, 1.5, 58), (82, 225.5, 4.0, 62),
    (87, 231.0, 1.5, 64), (85, 232.5, 1.5, 60), (89, 234.0, 4.5, 66),
    (92, 240.0, 1.5, 68), (89, 241.5, 1.0, 64), (94, 242.5, 4.4, 70),
)

THEME = (      # the climb-out: the dive cascade inverted, Bb MAJOR
    ((1, 0.0, 0.45), (2, 0.5, 0.45), (3, 1.0, 0.45), (4, 1.5, 0.45),
     (5, 2.0, 0.45), (6, 2.5, 0.45), (7, 3.0, 0.45), (8, 3.5, 0.45)),
    ((8, 0.0, 1.4), (6, 1.5, 0.45), (7, 2.0, 0.45), (8, 2.5, 1.4)),
    ((3, 0.0, 0.45), (4, 0.5, 0.45), (5, 1.0, 0.45), (6, 1.5, 0.45),
     (7, 2.0, 0.45), (8, 2.5, 0.45), (9, 3.0, 0.45), (10, 3.5, 0.45)),
    ((10, 0.0, 0.9), (9, 1.0, 0.45), (8, 1.5, 0.45), (5, 2.0, 1.9)),
)

DESCANT = ((82, 372.0, 6.0, 62), (86, 380.0, 6.0, 64), (89, 388.0, 6.0, 66),
           (87, 396.0, 6.0, 64), (82, 404.0, 6.0, 64), (89, 412.0, 6.0, 66),
           (86, 420.0, 6.0, 68), (94, 428.0, 8.0, 70), (89, 438.0, 4.0, 66),
           (94, 444.0, 6.5, 72))


def _heart_slice(sc: en.Score, t0: float, t1: float) -> None:
    """The heartbeat kicks (and soft after-beats) inside [t0, t1)."""
    beats = _heartbeat_beats()
    n = len(beats)
    for k, b in enumerate(beats):
        if not t0 - 1e-9 <= b < t1 - 1e-9:
            continue
        vel = round(en.lerp(52, 96, k / (n - 1)))
        sc.note(CH_KIT, 36, b, 0.3, vel, jt=0, jv=0)
        delta = (beats[k + 1] - b) if k + 1 < n else (b - beats[k - 1])
        dub = b + 0.32 * delta
        if dub < min(t1 - 0.05, HEART_T1 + 0.3):
            sc.note(CH_KIT, 35, dub, 0.22, max(24, vel - 28), jt=0, jv=0)


# ---------------------------------------------------------------------------
# I. Poolside (0-24) — chlorine light: harp water, vibe glints, a low
# pedal, a closed-mouth choir, one flute wisp of the note to come.
# ---------------------------------------------------------------------------

def build_poolside(sc: en.Score) -> None:
    sc.cc(CH_TAM, 0, 1, 0.0)           # latch the gong-ageng alt bank now
    sc.cc(CH_HI, 74, 84, 0.0)          # the climb is BRIGHT (audio contrast)
    for chn, v in ((CH_HI, 80), (CH_LO, 78), (CH_CHOIR, 70),
                   (CH_FLUTE, 76), (CH_BRASS, 78), (CH_HARP, 96)):
        sc.cc(chn, 11, v, 0.0)
    sc.cc(CH_CHOIR, 70, 12, 0.0)       # mouths closed
    sc.note(CH_LO, 46, 0.0, 23.8, 44, jt=0, jv=2)
    sc.note(CH_LO, 58, 8.0, 15.8, 38, jt=4, jv=2)
    for j, d in enumerate((1, 6, 1, 4)):
        tri = en.triad(TONIC_MID, MODE, d)
        en.arp(sc, CH_HARP, tri + [p + 12 for p in tri], 6.0 * j, 6, 1.0,
               44, pattern="updown", gate=1.8)
    for p, s in ((58, 0.0), (65, 0.0)):
        sc.note(CH_CHOIR, p, s, 11.8, 40, jt=4, jv=2)
    for p in (54, 61):
        sc.note(CH_CHOIR, p, 12.0, 11.8, 42, jt=4, jv=2)
    for t, p in ((2.0, 82), (5.5, 85), (9.0, 87), (12.5, 89),
                 (16.0, 92), (19.5, 94)):
        sc.note(CH_VIBE, p, t, 2.5, 42, jt=3, jv=3)
        sc.note(CH_VIBE, p - 12, t + 1.25, 2.0, 34, jt=3, jv=3)
    sc.note(CH_FLUTE, 82, 16.0, 4.0, 50, jt=3, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [(16.0, 50), (18.0, 72), (19.9, 44)],
                step=0.5)


# ---------------------------------------------------------------------------
# II-V. The platforms (24-216) — the identical ladder, a minor third
# higher each time; the heartbeat quickens underneath.
# ---------------------------------------------------------------------------

def _platform(sc: en.Score, idx: int) -> None:
    t0 = PLATFORMS[idx]
    root = TONIC_MID + 3 * idx
    root_lo = root - 12
    # the tonic pedal — the pitch-class centre's anchor
    for j in range(6):
        t = t0 + 8.0 * j
        sc.note(CH_LO, root_lo, t, 7.9, 46 + 6 * idx + (j % 2), jt=3, jv=2)
        sc.note(CH_LO, root_lo + 12, t, 7.9, 40 + 6 * idx, jt=3, jv=2)
    # the ladder — identical figuration, transposed (register oracle)
    for b in range(12):
        d0 = 1 + b
        vel = round(en.lerp(56 + 6 * idx, 70 + 6 * idx, b / 11))
        for dd, on, du in LADDER_CELL:
            sc.note(CH_HI, en.pitch(root, MODE, d0 + dd),
                    t0 + 4.0 * b + on, du * 0.97,
                    vel + (4 if on == 0.0 else 0), jt=4, jv=3)
    # harp harmonic motion
    for j, d in enumerate(PLAT_PROG):
        tri = en.triad(root, MODE, d)
        en.arp(sc, CH_HARP, tri + [p + 12 for p in tri], t0 + 8.0 * j, 8,
               1.0, 48 + 4 * idx, pattern="updown", gate=1.8)
    # the choir joins on the upper platforms (thin air, wide eyes)
    if idx >= 2:
        chords = [en.triad(root, MODE, d) for d in PLAT_PROG]
        en.pad_block(sc, CH_CHOIR, t0, chords, 8.0, size=3, lo=55, hi=76,
                     vel=50 + 6 * (idx - 2), vel_end=56 + 6 * (idx - 2))
        en.vowel_curve(sc, CH_CHOIR, [(t0, 30), (t0 + 24.0, 55),
                                      (t0 + 47.5, 40)], step=2.0)
    # the platform call
    vel = 74 + 4 * idx
    for dd, on, du in ((1, 0.0, 0.4), (3, 0.4, 0.4), (5, 0.8, 0.4),
                       (8, 1.2, 2.6)):
        sc.note(CH_BRASS, en.pitch(root, MODE, dd), t0 + on, du * 0.95,
                vel + (6 if dd == 8 else 0), jt=3, jv=3)
    for p in en.triad(root, MODE, 1):
        sc.note(CH_BRASS, p, t0 + 24.0, 0.45, vel + 2, jt=2, jv=3)
    en.expr_curve(sc, CH_HI, [(t0, 78 + 4 * idx), (t0 + 24.0, 86 + 4 * idx),
                              (t0 + 47.5, 82 + 4 * idx)], step=2.0)
    _heart_slice(sc, t0, t0 + PLATFORM_LEN)


def build_p1(sc: en.Score) -> None:
    _platform(sc, 0)


def build_p2(sc: en.Score) -> None:
    _platform(sc, 1)


def build_p3(sc: en.Score) -> None:
    _platform(sc, 2)


def build_p4(sc: en.Score) -> None:
    _platform(sc, 3)


# ---------------------------------------------------------------------------
# VI. The Board (216-248) — time stretches to 58 bpm; one flute on Bb,
# ten metres up; the heart hammers on; the riser inhales.
# ---------------------------------------------------------------------------

def build_board(sc: en.Score) -> None:
    sc.cc(CH_FLUTE, 11, 60, BOARD_T0 - 0.1)
    for p, t, dur, vel in BOARD_SOLO:
        sc.note(CH_FLUTE, p, t, dur, vel, jt=2, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [
        (216.0, 64), (219.0, 78), (222.0, 58), (225.5, 72), (229.4, 52),
        (231.0, 66), (234.0, 80), (238.4, 56), (240.0, 70), (242.5, 84),
        (246.2, 64), (247.2, 36)], step=0.5)
    # the held top note trembles, then steadies before the edge
    en.vibrato(sc, CH_FLUTE, 243.6, 2.9, depth=0.16, cycles_per_beat=0.9,
               delay=0.5)
    _heart_slice(sc, BOARD_T0, JUMP_T0)
    # the last breath: the riser swells and stops EXACTLY at the silence
    sc.note(CH_RISER, 70, RISER_T0, JUMP_T0 - RISER_T0, 90, jt=0, jv=0)


# ---------------------------------------------------------------------------
# VII. The Jump (248-252) — one full bar of air.  NOTHING is written:
# the silence is the music.
# ---------------------------------------------------------------------------

def build_jump(sc: en.Score) -> None:
    """Four beats of scored silence — the oracle holds every channel to
    zero events here.  This builder writes nothing, deliberately."""
    del sc


# ---------------------------------------------------------------------------
# VIII. The Plunge (252-260) — the dive cascade, four octaves down, harp
# falling alongside; the water rushes up.
# ---------------------------------------------------------------------------

def build_plunge(sc: en.Score) -> None:
    sc.cc(CH_HI, 11, 92, PLUNGE_T0 - 0.0)
    m = 0
    for k in range(4):
        root = DIVE_TOP_ROOT - 12 * k
        for d in material.DIVE_CASCADE:
            t = PLUNGE_T0 + m * material.DIVE_STEP
            sc.note(CH_HI, en.pitch(root, material.DIVE_MODE, d), t, 0.24,
                    round(en.lerp(70, 104, m / 31)), jt=0, jv=3)
            m += 1
    en.run(sc, CH_HARP, 252.0, 82, MODE, list(range(8, -4, -1)), 0.125,
           72, 56, jt=1)
    en.run(sc, CH_HARP, 254.0, 70, MODE, list(range(8, -4, -1)), 0.125,
           64, 50, jt=1)
    en.run(sc, CH_HARP, 256.5, 58, MODE, list(range(8, 0, -1)), 0.125,
           62, 52, jt=1)
    # the sub swell — the water's surface rushing up
    sc.note(CH_LO, 46, 257.0, 2.9, 72, jt=0, jv=2)
    en.cc_curve(sc, CH_LO, 11, [(257.0, 55), (259.9, 116)], step=0.25)
    sc.note(CH_RISER, 70, 256.0, 4.0, 88, jt=0, jv=0)


# ---------------------------------------------------------------------------
# IX. The Splash (260-268) — gong ageng + taiko + toms + crash: the
# global energy maximum; then the white wash closes over.
# ---------------------------------------------------------------------------

def build_splash(sc: en.Score) -> None:
    # Impact micro-stagger: five sample-aligned attack transients summed in
    # ONE sample step and tripped the render click scan (23278 > 22000 under
    # the v0.12 synth). A real splash smears over milliseconds — offsets of
    # 5-10 ms decorrelate the attacks while every velocity (and so the
    # splash_energy_max oracle) is unchanged; the tam stays the on-beat
    # strike inside splash_anatomy's 0.05-beat window.
    sc.note(CH_TAM, 46, SPLASH_T0, 8.0, 122, jt=0, jv=0)
    sc.note(CH_TAIKO, 38, SPLASH_T0 + 0.010, 0.5, 122, jt=0, jv=2)
    sc.note(CH_TAIKO, 45, SPLASH_T0 + 0.020, 0.5, 116, jt=0, jv=2)
    for i in range(1, 16):
        sc.note(CH_TAIKO, 38 if i % 2 else 43, SPLASH_T0 + 0.25 * i, 0.22,
                round(en.lerp(112, 62, i / 15)), jt=1, jv=3)
    sc.note(CH_TAIKO, 38, 261.0, 0.4, 100, jt=1, jv=3)
    sc.note(CH_TAIKO, 45, 262.0, 0.4, 92, jt=1, jv=3)
    for drum, beat, vel in ((49, 260.0, 112), (57, 260.0, 108),
                            (52, 260.0, 102), (36, 260.0, 118),
                            (36, 260.5, 100), (52, 260.5, 88),
                            (41, 260.0, 112), (43, 260.125, 110),
                            (45, 260.25, 108), (41, 261.0, 96),
                            (36, 262.5, 88), (43, 262.0, 86),
                            (41, 263.0, 74)):
        sc.hit(drum, beat, vel, jt=1, jv=3)
    sc.note(CH_LO, 46, SPLASH_T0 + 0.015, 7.9, 96, jt=0, jv=2)
    sc.note(CH_LO, 41, SPLASH_T0 + 0.025, 7.9, 88, jt=0, jv=2)
    en.cc_curve(sc, CH_LO, 11, [(260.0, 118), (267.5, 60)], step=0.5)
    # bar two: the wash — bubbles roaring past, already darkening
    for p in (58, 61, 65):
        sc.note(CH_CHOIR, p, 264.0, 3.9, 46, jt=3, jv=2)
    sc.cc(CH_CHOIR, 70, 8, 263.5)
    sc.note(CH_HARP, 70, 265.0, 1.5, 38, jt=3, jv=2)
    sc.note(CH_HARP, 65, 266.2, 1.6, 34, jt=3, jv=2)
    en.cc_curve(sc, CH_HI, 74, [(264.0, 60), (267.9, 34)], step=0.5)


# ---------------------------------------------------------------------------
# X. Underwater (268-332) — 54 bpm, filters closed (CC74 <= 40), slow
# bends refracting the pool lights, the heart settling.
# ---------------------------------------------------------------------------

def build_underwater(sc: en.Score) -> None:
    t0 = UW_T0
    sc.cc(CH_HI, 74, 30, t0)
    sc.cc(CH_LO, 74, 26, t0)
    sc.cc(CH_CHOIR, 74, 22, t0)
    en.cc_curve(sc, CH_HI, 74, [(t0, 30), (300.0, 22), (331.5, 28)],
                step=4.0)
    chords_lo = [en.triad(46, MODE, d) for d in UW_PROG]
    en.pad_block(sc, CH_LO, t0, chords_lo, 8.0, size=3, lo=39, hi=58,
                 vel=40, vel_end=46)
    en.cc_curve(sc, CH_LO, 11, [(t0, 62), (300.0, 70), (331.5, 60)],
                step=2.0)
    chords_ch = [en.triad(58, MODE, d) for d in UW_PROG]
    en.pad_block(sc, CH_CHOIR, t0, chords_ch, 8.0, size=3, lo=50, hi=68,
                 vel=42, vel_end=46)
    sc.cc(CH_CHOIR, 70, 8, t0)
    en.vowel_curve(sc, CH_CHOIR, [(t0 + 0.5, 8), (300.0, 20), (331.0, 10)],
                   step=2.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(t0, 64), (300.0, 72), (331.5, 58)],
                step=2.0)
    # refracted light: one high tone per chord, bending slowly and always
    # recentring (the bend-hygiene boundary at 332 stays clean)
    sc.cc(CH_HI, 11, 60, t0)
    for j, d in enumerate(UW_PROG):
        t = t0 + 8.0 * j + 0.5
        p = en.pitch(82, MODE, d)
        sc.note(CH_HI, p, t, 6.3, 44, jt=3, jv=2)
        amp = 0.42 if j % 2 == 0 else -0.36
        en.bend_ramp(sc, CH_HI, t, t + 3.2, 0.0, amp, steps=10)
        en.bend_ramp(sc, CH_HI, t + 3.2, t + 6.3, amp, 0.0, steps=10)
    # bubbles — seeded, sparse, rising
    rng = random.Random(SEED * 7919 + 8)
    penta = (70, 73, 75, 77, 82, 85, 87, 89)
    for j in range(8):
        if j % 2 == 0 or rng.random() < 0.6:
            t = t0 + 8.0 * j + 2.0 + rng.random() * 3.0
            idx = rng.randrange(4)
            for m in range(2 + rng.randrange(2)):
                sc.note(CH_VIBE, penta[idx + m], t + 0.35 * m, 1.4,
                        30 + 3 * m, jt=2, jv=2)
    # slow harp fans, face-down drift
    for j in (0, 2, 4, 6):
        tri = en.triad(58, MODE, UW_PROG[j])
        for m, p in enumerate((tri[2], tri[1], tri[0], tri[0] - 12)):
            sc.note(CH_HARP, p, t0 + 8.0 * j + 3.5 + 0.8 * m, 2.0, 34,
                    jt=3, jv=2)
    # the heart, settling after the fall
    for j in range(8):
        t = 270.0 + 8.0 * j
        sc.note(CH_KIT, 36, t, 0.3, 36, jt=0, jv=0)
        sc.note(CH_KIT, 35, t + 0.6, 0.22, 26, jt=0, jv=0)


# ---------------------------------------------------------------------------
# XI. Surfacing (332-468) — the breach, the crowd's orchestra hit, and a
# Bb-MAJOR celebration: the dive cascade inverted into a climb-out.
# ---------------------------------------------------------------------------

def build_surfacing(sc: en.Score) -> None:
    t0 = SURF_T0
    # -- the breach ---------------------------------------------------------
    sc.cc(CH_HI, 74, 82, t0)
    sc.cc(CH_LO, 74, 70, t0)
    sc.cc(CH_CHOIR, 74, 76, t0)
    sc.cc(CH_CHOIR, 70, 92, t0)              # mouths OPEN
    sc.note(CH_HIT, 58, t0, 1.0, 112, jt=0, jv=2)
    sc.note(CH_HIT, 58, t0 + 2.0, 1.0, 104, jt=0, jv=2)
    en.run(sc, CH_HARP, t0, 58, MAJ, list(range(1, 16)), 0.125, 66, 92,
           jt=1)
    sc.hit(49, t0, 110, jt=1, jv=3)
    sc.hit(52, t0, 96, jt=1, jv=3)
    sc.hit(36, t0, 108, jt=1, jv=3)
    for p in (58, 62, 65, 70):
        sc.note(CH_BRASS, p, t0, 3.8, 96, jt=3, jv=3)
    en.cc_curve(sc, CH_BRASS, 11, [(t0, 70), (t0 + 1.5, 104),
                                   (t0 + 3.8, 80)], step=0.25)
    for p in (65, 70, 74):
        sc.note(CH_CHOIR, p, t0, 7.8, 76, jt=4, jv=2)
    en.cc_curve(sc, CH_CHOIR, 11, [(t0, 78), (t0 + 4.0, 92),
                                   (t0 + 7.8, 80)], step=1.0)
    sc.note(CH_HI, 82, t0, 7.8, 62, jt=3, jv=2)
    sc.note(CH_HI, 86, t0 + 1.0, 6.8, 58, jt=3, jv=2)
    en.cc_curve(sc, CH_HI, 11, [(t0, 78), (t0 + 7.8, 86)], step=1.0)
    for p, on in ((70, 336.0), (74, 336.5), (77, 337.0)):
        sc.note(CH_FLUTE, p, on, 0.45, 66, jt=2, jv=2)
    sc.note(CH_FLUTE, 82, 337.5, 2.4, 70, jt=2, jv=2)
    sc.note(CH_LO, 46, t0, 3.9, 84, jt=2, jv=2)
    sc.note(CH_LO, 46, t0 + 4.0, 3.9, 80, jt=2, jv=2)
    # -- the celebration groove (340-452) ------------------------------------
    pad_chords = [en.triad(70, MAJ, CYCLE[i % 4])
                  for i in range(GROOVE_BARS)]
    en.pad_block(sc, CH_CHOIR, GROOVE_T0, pad_chords, 4.0, size=3, lo=62,
                 hi=79, vel=56, vel_end=68)
    en.cc_curve(sc, CH_CHOIR, 11, [(GROOVE_T0, 70), (430.0, 84),
                                   (451.5, 78)], step=4.0)
    hat_vels = (58, 44, 52, 44, 60, 44, 52, 46)
    for b in range(GROOVE_BARS):
        t = GROOVE_T0 + 4.0 * b
        x = b / (GROOVE_BARS - 1)
        # drums
        sc.hit(36, t, round(en.lerp(92, 100, x)), jt=2, jv=3)
        sc.hit(36, t + 2.0, round(en.lerp(88, 96, x)), jt=2, jv=3)
        sc.hit(38, t + 1.0, round(en.lerp(88, 96, x)), jt=2, jv=3)
        sc.hit(38, t + 3.0, round(en.lerp(90, 98, x)), jt=2, jv=3)
        for e in range(8):
            if b % 4 == 3 and e == 7:
                sc.hit(46, t + 3.5, 60, jt=2, jv=3)
            else:
                sc.hit(42, t + 0.5 * e, hat_vels[e], jt=2, jv=3)
        if b % 8 == 0:
            sc.hit(49, t, 100, jt=2, jv=3)
        # bass riff follows the turnaround
        deg = CYCLE[b % 4]
        for on, du, dd, v in ((0.0, 0.75, 0, 82), (1.5, 0.5, 0, 76),
                              (2.5, 0.45, 4, 76), (3.0, 0.95, 2, 78)):
            sc.note(CH_LO, en.pitch(46, MAJ, deg + dd), t + on, du,
                    v + round(4 * x), jt=3, jv=3)
        # the climb-out theme
        vel = round(en.lerp(78, 92, x))
        for dd, on, du in THEME[b % 4]:
            sc.note(CH_HI, en.pitch(70, MAJ, dd), t + on, du,
                    vel + (5 if on == 0.0 else 0), jt=4, jv=3)
        # brass answers
        if b % 2 == 1:
            for p in en.triad(58, MAJ, deg):
                sc.note(CH_BRASS, p, t + 1.5, 0.3, 86, jt=2, jv=3)
            if b % 4 == 1:
                for p in en.triad(58, MAJ, deg):
                    sc.note(CH_BRASS, p, t + 3.5, 0.3, 82, jt=2, jv=3)
        # festive taiko
        if b >= 8:
            sc.note(CH_TAIKO, 38, t, 0.4, round(en.lerp(78, 86, x)),
                    jt=2, jv=3)
            sc.note(CH_TAIKO, 45, t + 2.5, 0.4, round(en.lerp(72, 80, x)),
                    jt=2, jv=3)
        # harp sparkle late in the party
        if b >= 16 and b % 2 == 0:
            tri = en.triad(58, MAJ, deg)
            en.arp(sc, CH_HARP, tri + [p + 12 for p in tri], t, 8, 0.5,
                   56, pattern="updown", gate=1.6)
    # the crowd, every four bars
    h = GROOVE_T0
    while h < 452.0:
        sc.note(CH_HIT, 58, h, 0.8, 102, jt=0, jv=2)
        h += 16.0
    for p, on, dur, vel in DESCANT:
        sc.note(CH_FLUTE, p, on, dur, vel, jt=3, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [(372.0, 66), (428.0, 84), (450.5, 72)],
                step=2.0)
    # -- home water (452-468) ------------------------------------------------
    for i in range(8):
        sc.note(CH_HI, en.pitch(70, MAJ, 1 + i), 452.0 + 0.5 * i, 0.45,
                round(en.lerp(88, 96, i / 7)), jt=2, jv=3)
    for i in range(8):
        sc.note(CH_HI, en.pitch(70, MAJ, 8 + i), 456.0 + 0.5 * i, 0.45,
                round(en.lerp(96, 104, i / 7)), jt=2, jv=3)
    for on, du, dd, v in ((0.0, 0.75, 0, 84), (1.5, 0.5, 0, 80),
                          (2.5, 0.45, 4, 82), (3.0, 0.95, 2, 84)):
        for bar in (452.0, 456.0):
            sc.note(CH_LO, en.pitch(46, MAJ, 1 + dd), bar + on, du, v,
                    jt=3, jv=3)
    sc.hit(36, 452.0, 100, jt=2, jv=3)
    sc.hit(38, 453.0, 94, jt=2, jv=3)
    sc.hit(36, 454.0, 96, jt=2, jv=3)
    sc.hit(38, 455.0, 96, jt=2, jv=3)
    sc.hit(36, 456.0, 100, jt=2, jv=3)
    for i in range(8):
        sc.hit(38, 458.0 + 0.25 * i, round(en.lerp(70, 102, i / 7)),
               jt=1, jv=3)
    en.run(sc, CH_HARP, 458.5, 58, MAJ, list(range(1, 13)), 0.125, 66, 84,
           jt=1)
    # the final chord — Bb major, rung out on the gong
    sc.hit(49, 460.0, 110, jt=1, jv=3)
    sc.hit(57, 460.0, 100, jt=1, jv=3)
    for p, v in ((82, 90), (86, 88), (89, 86)):
        sc.note(CH_HI, p, 460.0, 7.6, v, jt=2, jv=2)
    for p, v in ((46, 86), (58, 82)):
        sc.note(CH_LO, p, 460.0, 7.6, v, jt=2, jv=2)
    for p in (58, 62, 65, 70):
        sc.note(CH_BRASS, p, 460.0, 5.8, 96, jt=2, jv=2)
    for p in (70, 74, 77):
        sc.note(CH_CHOIR, p, 460.0, 7.6, 80, jt=2, jv=2)
    sc.note(CH_HIT, 58, 460.0, 1.0, 112, jt=0, jv=2)
    sc.note(CH_TAM, 41, 460.0, 8.0, 102, jt=0, jv=0)
    sc.note(CH_TAIKO, 38, 460.0, 0.5, 96, jt=1, jv=3)
    sc.note(CH_TAIKO, 45, 460.5, 0.4, 88, jt=1, jv=3)
    en.arp(sc, CH_HARP, [58, 62, 65, 70, 74, 77, 82], 460.5, 10, 0.5, 62,
           pattern="updown", gate=1.5)
    en.cc_curve(sc, CH_BRASS, 11, [(460.0, 96), (465.7, 42)], step=0.5)
    en.cc_curve(sc, CH_HI, 11, [(460.0, 88), (467.4, 40)], step=0.5)
    en.cc_curve(sc, CH_CHOIR, 11, [(460.0, 84), (467.4, 38)], step=0.5)
    en.cc_curve(sc, CH_LO, 11, [(460.0, 86), (467.4, 44)], step=0.5)
    # the heart, home safe: two slow, easy beats under the fade
    sc.note(CH_KIT, 36, 465.0, 0.3, 36, jt=0, jv=0)
    sc.note(CH_KIT, 36, 466.4, 0.3, 34, jt=0, jv=0)


BUILDERS: list = [build_poolside, build_p1, build_p2, build_p3, build_p4,
                  build_board, build_jump, build_plunge, build_splash,
                  build_underwater, build_surfacing]
