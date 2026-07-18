"""movements/t03_static.py — track 3 of *The Remaining*.

THE SEARCHING.  The album's one pulse track, and the opposite of every
other: dry, close, metronomic — a machine sweeping a dead field for a
signal.  A synth-bass quaver pulse holds an unbroken 112-bpm grid over the
GROUND transposed to the dominant minor (Am - F - C - G, the same aeolian
walk [1,6,3,7]).  Above it a dry solo violin (reverb send 0 - the point)
spins a moto perpetuo built from the DEPARTURE FIGURE at double speed, its
phrases lengthening 4 -> 8 -> 16 notes as the search grows insistent; in a
middle B section the arpeggio's tenth-leaps swoop under portamento.  A
warm pad breathes on a slow filter arc; a single crystal shimmer autopans
(the only voice off-centre, kept low).  Buried under the pulse a woodblock
taps "REMEMBER US" in Morse, twice.  Then the interruption: on quaver 6 of
the last bar everything stops at once - pulse, pad, and the violin caught
mid-phrase on the VIGIL THEME's first three notes, A-G-F (its only theme
material, quoted at concert pitch, never completed).  One beat of nothing.
A single dry woodblock tap.  A flat tempo map is mandatory here - the anti-
rubato, the machine's indifference.  Every device is oracle-pinned below.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 3
TITLE = "Static"
FILE = "03 - Static.mid"
SEED = 20261003
COMMENT = (
    "The searching - the album's one pulse track, dry and metronomic at a "
    "flat 112 bpm. An unbroken synth-bass quaver pulse holds the ground "
    "transposed to A minor (Am-F-C-G); over it a dry solo violin spins a "
    "moto perpetuo from the departure figure at double speed, its phrases "
    "lengthening and sliding under portamento. A pad breathes, a crystal "
    "shimmer drifts, and a woodblock taps REMEMBER US in Morse twice. Then "
    "on quaver six of the last bar everything stops at once - the violin "
    "caught mid-phrase on the theme's first three notes A-G-F, never "
    "finished - one beat of nothing, and a single dry woodblock tap.")

# ---------------------------------------------------------------------------
# Pinned geometry (the oracles below verify all of it against material.py)
# ---------------------------------------------------------------------------

CH_PULSE, CH_VIOLIN, CH_PAD, CH_SHIMMER, CH_WOOD = 0, 1, 2, 3, 4

_MM = material.MODE_MINOR                       # aeolian

GROUND_BASE = en.n("A1")                        # 33 - the dominant-minor tonic
PULSE_ROOTS = material.ground_roots(GROUND_BASE)  # [33,41,36,43] = A1,F2,C2,G2
MOTO_ROOTS = [en.n("A4"), en.n("F4"), en.n("C5"), en.n("G4")]  # [69,65,72,67]
THEME_BASE = en.n("D5")                         # 74 - theme head at concert pitch
FIG = material.figure_offsets(True)             # [0,7,12,15,12,7,12,7]
SEMI = 0.25                                     # moto spacing = half a quaver

PAD_CHORD = [en.n("A3"), en.n("E4"), en.n("A4")]              # 57,64,69 drone
SHIMMER_PITCHES = [en.n("A5"), en.n("C6"), en.n("E6"), en.n("C6")]  # 81,84,88,84
MORSE_PITCH = en.n("C5")                        # 72 - the woodblock's fixed tap
MORSE_GATE = 0.9

MOTO_START_BAR = 8
N_FULL_BARS = 124                               # bars 0..123 pulse in full
CUT_QUAVERS = 6                                 # the last bar stops on quaver 6
CUT_T0 = N_FULL_BARS * 4.0                       # 496.0 - the last sounding bar
CUT_INSTANT = CUT_T0 + 3.0                       # 499.0 - quaver 6, everything stops
TAP_BEAT = CUT_T0 + 4.0                          # 500.0 - the lone final tap
END = 504.0

MORSE1_START = 64.0                             # statement 1 (movement I)
MORSE2_START = 256.0                            # statement 2 (movement II)
B_START = 224.0                                 # portamento in
B_END = 288.0                                   # portamento out
PAD_START = 16.0                                # the pad breathes in at bar 4

THEME_VEL = 70
TAP_VEL = 50
PAD_VEL = 42

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Pulse", 0.0, 160.0),
               ("II. Search", 160.0, 352.0),
               ("III. Cutoff", 352.0, END)],
    tempo_map=[(0.0, 112.0)],                   # exactly one event - metronomic
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1)],                      # A minor: no accidentals, minor
    channels=[(CH_PULSE, "synth bass", 38, 90, 64, 8),
              (CH_VIOLIN, "violin", 40, 100, 64, 0),   # reverb 0 - dry, close
              (CH_PAD, "warm pad", 89, 66, 64, 30),
              (CH_SHIMMER, "crystal", 98, 48, 64, 40),  # autopans; kept low
              (CH_WOOD, "woodblock", 115, 78, 64, 6)],
    extra_markers=[(B_START, "the b section"), (CUT_INSTANT, "the cutoff")],
)

PROGRAM_WHITELIST = {38, 40, 89, 98, 115}
CENTERED_CHANNELS = {CH_PULSE, CH_VIOLIN, CH_PAD, CH_WOOD}  # only shimmer drifts
NOTE_RANGES = {CH_PULSE: (31, 45), CH_VIOLIN: (64, 88), CH_PAD: (55, 71),
               CH_SHIMMER: (72, 90), CH_WOOD: (72, 72)}
GAP_WHITELIST: list[tuple[float, float]] = []   # the pulse never lets a gap open
BEND_EXEMPT: set[int] = set()                   # no pitch bends at all on this track
DURATION_WINDOW = (258.0, 282.0)                # ~4:29 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Phrase geometry — the moto perpetuo lengthens across the track
# ---------------------------------------------------------------------------

def _phrase_len(bar: int) -> int:
    """Notes in the violin's moto phrase for `bar` (0 = the violin rests)."""
    if MOTO_START_BAR <= bar <= 39:
        return 4
    if 40 <= bar <= 71:
        return 8
    if 72 <= bar <= 121:
        return 16
    return 0


def _pulse_vel(bar: int, q: int) -> int:
    """The quiet machine: a slow swell with a light on-beat accent."""
    base = 44 + min(10, bar // 12)
    return base + (5 if q % 2 == 0 else 0)


def _moto_vel(bar: int, i: int) -> int:
    """The search brightens over the track and peaks at the figure's crest."""
    glob = 56 + min(18, bar // 6)
    contour = FIG[i % 8] * 6 // 15
    return min(90, glob + contour)


# ---------------------------------------------------------------------------
# Emitters (every oracle-pinned lane is jt=0, jv=0 — the grid is mechanical)
# ---------------------------------------------------------------------------

def _pulse_bar(sc, bar: int, quavers: int = 8) -> None:
    root = PULSE_ROOTS[bar % 4]
    t0 = bar * 4.0
    for q in range(quavers):
        sc.note(CH_PULSE, root, t0 + 0.5 * q, 0.45, _pulse_vel(bar, q),
                jt=0, jv=0)


def _moto_bar(sc, bar: int) -> None:
    length = _phrase_len(bar)
    if not length:
        return
    root = MOTO_ROOTS[bar % 4]
    t0 = bar * 4.0
    for i in range(length):
        sc.note(CH_VIOLIN, root + FIG[i % 8], t0 + SEMI * i, 0.24,
                _moto_vel(bar, i), jt=0, jv=0)


def _pad_wave(sc, t0: float, dur: float, vel: int = PAD_VEL) -> None:
    for p in PAD_CHORD:
        sc.note(CH_PAD, p, t0, dur, vel, jt=0, jv=0)


def _morse_statement(sc, start: float, vel: int = 40) -> None:
    """Tap REMEMBER US on the pitched woodblock (NOT a drum kit), buried."""
    for on, du in material.morse_rhythm(material.MORSE_TEXT):
        sc.note(CH_WOOD, MORSE_PITCH, start + on, du * MORSE_GATE, vel,
                jt=0, jv=0)


# ---------------------------------------------------------------------------
# I. Pulse [0, 160) — the machine boots: pulse, then pad, then the search
# ---------------------------------------------------------------------------

def _b_pulse(sc):
    en.bend_range(sc, CH_VIOLIN, 2, 0.0)        # RPN bend range = 2 at setup

    for bar in range(0, 40):                    # the unbroken quaver pulse
        _pulse_bar(sc, bar)

    for t in range(int(PAD_START), 160, 8):     # the pad breathes in 8-beat waves
        _pad_wave(sc, float(t), 8.0)
    en.cc_curve(sc, CH_PAD, 74, [(16.0, 40), (80.0, 66), (144.0, 40),
                                 (159.0, 52)], step=4.0)
    en.expr_curve(sc, CH_PAD, [(16.0, 44), (80.0, 60), (159.0, 52)], step=4.0)

    for bar in range(MOTO_START_BAR, 40):       # the violin's first short gestures
        _moto_bar(sc, bar)
    en.expr_curve(sc, CH_VIOLIN, [(32.0, 40), (96.0, 70), (159.0, 58)],
                  step=4.0)
    en.cc_curve(sc, CH_VIOLIN, 1, [(32.0, 0), (159.0, 18)], step=8.0)

    _morse_statement(sc, MORSE1_START)          # REMEMBER US, first time


# ---------------------------------------------------------------------------
# II. Search [160, 352) — phrases lengthen; the B section slides; shimmer
# ---------------------------------------------------------------------------

def _b_search(sc):
    for bar in range(40, 88):
        _pulse_bar(sc, bar)

    for t in range(160, 352, 8):
        _pad_wave(sc, float(t), 8.0)
    en.cc_curve(sc, CH_PAD, 74, [(160.0, 52), (224.0, 70), (300.0, 44),
                                 (351.0, 58)], step=4.0)
    en.expr_curve(sc, CH_PAD, [(160.0, 54), (256.0, 64), (351.0, 56)],
                  step=4.0)

    for bar in range(40, 88):                   # L=8 then L=16 - the search fills in
        _moto_bar(sc, bar)
    en.expr_curve(sc, CH_VIOLIN, [(160.0, 60), (256.0, 84), (351.0, 72)],
                  step=4.0)
    en.cc_curve(sc, CH_VIOLIN, 1, [(160.0, 18), (288.0, 40), (351.0, 46)],
                step=8.0)

    # the B section: portamento makes the arpeggio's tenth-leaps swoop
    en.portamento_on(sc, CH_VIOLIN, B_START, time_cc=30)
    en.portamento_off(sc, CH_VIOLIN, B_END)

    # one crystal shimmer, slowly autopanning - the only off-centre voice
    for k, t in enumerate(range(176, 340, 32)):
        sc.note(CH_SHIMMER, SHIMMER_PITCHES[k % len(SHIMMER_PITCHES)],
                float(t), 6.0, 30, jt=0, jv=0)
    en.autopan(sc, CH_SHIMMER, 160.0, 188.0, lo=48, hi=80,
               period_beats=48.0, step=2.0)
    en.expr_curve(sc, CH_SHIMMER, [(176.0, 30), (256.0, 46), (340.0, 26)],
                  step=4.0)

    _morse_statement(sc, MORSE2_START)          # REMEMBER US, second time


# ---------------------------------------------------------------------------
# III. Cutoff [352, 504) — the search runs on, then is cut mid-phrase
# ---------------------------------------------------------------------------

def _b_cutoff(sc):
    for bar in range(88, N_FULL_BARS):          # the pulse, still unbroken
        _pulse_bar(sc, bar)
    _pulse_bar(sc, N_FULL_BARS, quavers=CUT_QUAVERS)  # the last bar: only 6 quavers

    for t in range(352, 496, 8):                # the pad, breathing to the edge
        _pad_wave(sc, float(t), 8.0)
    _pad_wave(sc, CUT_T0, CUT_INSTANT - CUT_T0)  # the last chord, cut at quaver 6
    en.cc_curve(sc, CH_PAD, 74, [(352.0, 58), (420.0, 72), (488.0, 46),
                                 (496.0, 40)], step=4.0)
    en.expr_curve(sc, CH_PAD, [(352.0, 56), (440.0, 64), (496.0, 40)],
                  step=4.0)

    for bar in range(88, 122):                  # the moto at full stretch (L=16)
        _moto_bar(sc, bar)                       # bars 122-123: the violin holds off
    en.expr_curve(sc, CH_VIOLIN, [(352.0, 72), (440.0, 92), (487.0, 78),
                                  (496.0, 88), (498.5, 70)], step=2.0)
    en.cc_curve(sc, CH_VIOLIN, 1, [(352.0, 46), (480.0, 60), (496.0, 40)],
                step=8.0)

    # the theme, reached for and never finished: A-G-F, the third cut short
    for on, _du, deg in material.THEME[:3]:
        t = CUT_T0 + on
        end = min(t + _du, CUT_INSTANT)
        sc.note(CH_VIOLIN, en.pitch(THEME_BASE, _MM, deg), t, end - t,
                THEME_VEL, jt=0, jv=0)

    # one beat of nothing, then the single dry woodblock tap
    sc.note(CH_WOOD, MORSE_PITCH, TAP_BEAT, 0.45, TAP_VEL, jt=0, jv=0)


BUILDERS = [_b_pulse, _b_search, _b_cutoff]


# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES §2 pattern, beat-based)
# ---------------------------------------------------------------------------

def _ons_b(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / en.PPQ, d[1], d[2]))
    return sorted(out)


def _spans_b(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = d[0] & 0xF0
        if s == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                out.append((q.pop(0) / en.PPQ, tick / en.PPQ, d[1]))
    return sorted(out)


def _cc_b(sc, ch, num):
    return sorted((t / en.PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _o_pulse(sc):
    """The synth-bass pulse: an isochronous 0.5-beat quaver grid, unbroken
    for the whole track bar the last, cut on quaver 6."""
    fails = []
    ons = _ons_b(sc, CH_PULSE)
    want = N_FULL_BARS * 8 + CUT_QUAVERS
    if len(ons) != want:
        fails.append(f"pulse has {len(ons)} quavers, want {want} "
                     f"(unbroken to the cut)")
    for i, (b, p, _v) in enumerate(ons):
        exp = 0.5 * i
        if abs(b - exp) > 1e-6:
            fails.append(f"quaver {i} at {b:.3f}, want {exp:.3f} "
                         f"(the pulse must be isochronous, jt=0)")
            break
        bar = int(b // 4)
        if p != PULSE_ROOTS[bar % 4]:
            fails.append(f"quaver {i} (bar {bar}) pitch {p}, want "
                         f"{PULSE_ROOTS[bar % 4]} (the Am-F-C-G walk)")
            break
    if ons:
        last = ons[-1][0]
        if abs(last - (CUT_T0 + 2.5)) > 1e-6:
            fails.append(f"last pulse quaver at {last:.3f}, want "
                         f"{CUT_T0 + 2.5:.3f} (quaver 5 of the cut bar)")
        if any(b >= CUT_INSTANT - 1e-9 for b, _p, _v in ons):
            fails.append("the pulse sounds at/after the cutoff (quaver 6)")
    return fails[:8]


def _o_ground(sc):
    """The harmonic floor is THE GROUND transposed to the dominant minor:
    Am - F - C - G, the same aeolian degree walk [1,6,3,7]."""
    fails = []
    expect = material.ground_roots(GROUND_BASE)
    if PULSE_ROOTS != expect:
        fails.append(f"PULSE_ROOTS {PULSE_ROOTS} != ground_roots {expect}")
    if material.GROUND_DEGREES != [1, 6, 3, 7]:
        fails.append(f"ground degrees {material.GROUND_DEGREES} != [1,6,3,7]")
    pcs = [r % 12 for r in PULSE_ROOTS]
    if pcs != [9, 5, 0, 7]:
        fails.append(f"root walk pitch-classes {pcs} != A,F,C,G [9,5,0,7]")
    if [r % 12 for r in MOTO_ROOTS] != pcs:
        fails.append(f"the moto roots {[r % 12 for r in MOTO_ROOTS]} do not "
                     f"follow the ground walk {pcs}")
    if GROUND_BASE % 12 != 9:
        fails.append("the ground is not transposed to A (the dominant minor)")
    return fails


def _o_moto(sc):
    """The violin moto perpetuo is the DEPARTURE FIGURE at double speed: the
    same 8-offset walk, spaced a semiquaver apart, phrases 4 -> 8 -> 16."""
    fails = []
    if abs(SEMI * 2 - 0.5) > 1e-9:
        fails.append("moto spacing is not double the figure's quaver (0.5)")
    if FIG != material.figure_offsets(True):
        fails.append("the moto offsets are not the minor departure figure")
    expected = []
    for bar in range(MOTO_START_BAR, 122):
        length = _phrase_len(bar)
        root = MOTO_ROOTS[bar % 4]
        t0 = bar * 4.0
        for i in range(length):
            expected.append((t0 + SEMI * i, root + FIG[i % 8]))
    moto = [(b, p) for b, p, _v in _ons_b(sc, CH_VIOLIN) if b < CUT_T0 - 1e-9]
    if len(moto) != len(expected):
        fails.append(f"violin moto has {len(moto)} notes, want "
                     f"{len(expected)} (double-speed figure walk)")
    lengths = {_phrase_len(b) for b in range(MOTO_START_BAR, 122)}
    if lengths != {4, 8, 16}:
        fails.append(f"phrase lengths {sorted(lengths)} are not 4,8,16")
    for k, ((gb, gp), (eb, ep)) in enumerate(zip(moto, expected)):
        if abs(gb - eb) > 1e-6 or gp != ep:
            fails.append(f"moto note {k}: got ({gb:.3f},{gp}) want "
                         f"({eb:.3f},{ep})")
            break
    return fails[:8]


def _o_morse(sc):
    """The static lane: REMEMBER US tapped twice, in standard Morse timing
    (verified against material.morse_rhythm), buried under the pulse."""
    fails = []
    pairs = material.morse_rhythm(material.MORSE_TEXT)
    wood = _spans_b(sc, CH_WOOD)
    morse = sorted((on, off) for on, off, _p in wood if on < TAP_BEAT - 1e-9)
    if len(morse) != 2 * len(pairs):
        fails.append(f"morse lane has {len(morse)} taps, want "
                     f"{2 * len(pairs)} (REMEMBER US x2)")
    for s, start in enumerate((MORSE1_START, MORSE2_START)):
        seg = morse[s * len(pairs):(s + 1) * len(pairs)]
        if len(seg) != len(pairs):
            fails.append(f"statement {s + 1} has {len(seg)} taps, "
                         f"want {len(pairs)}")
            continue
        for k, ((on, off), (won, wdu)) in enumerate(zip(seg, pairs)):
            if abs(on - (start + won)) > 1e-6:
                fails.append(f"statement {s + 1} symbol {k}: onset {on:.3f}, "
                             f"want {start + won:.3f}")
                break
            if abs((off - on) - wdu * MORSE_GATE) > 0.02:
                fails.append(f"statement {s + 1} symbol {k}: dur "
                             f"{off - on:.3f}, want {wdu * MORSE_GATE:.3f} "
                             f"(dit/dah timing)")
                break
    return fails[:8]


def _o_dry_violin(sc):
    """The solo violin is DRY (reverb send 0) — the close, static idiom."""
    fails = []
    rev = PART.CHANNELS[CH_VIOLIN][5]
    if rev != 0:
        fails.append(f"violin channel reverb {rev} != 0 (must be dry, close)")
    bad = [(b, v) for b, v in _cc_b(sc, CH_VIOLIN, 91) if v != 0]
    if bad:
        fails.append(f"violin CC91 (reverb send) is non-zero: {bad[:3]}")
    return fails


def _o_cutoff(sc):
    """The interruption: everything stops together on quaver 6 of the last
    bar; >= 1 beat of silence; then exactly one final woodblock tap."""
    fails = []
    allspans = [(on, off, ch) for ch in sc.events
                for (on, off, _p) in _spans_b(sc, ch)]
    tap = [(on, off) for on, off, _p in _spans_b(sc, CH_WOOD)
           if on >= TAP_BEAT - 1e-9]
    if len(tap) != 1:
        fails.append(f"want exactly one final woodblock tap, got {len(tap)}")
    elif abs(tap[0][0] - TAP_BEAT) > 1e-6:
        fails.append(f"final tap at {tap[0][0]:.3f}, want {TAP_BEAT}")
    late = [(on, ch) for on, _off, ch in allspans if on >= CUT_INSTANT - 1e-9]
    if len(late) != 1 or late[0][1] != CH_WOOD:
        fails.append(f"only the woodblock tap may sound after the cutoff; "
                     f"got channels {sorted({ch for _o, ch in late})}")
    through = [(on, off, ch) for on, off, ch in allspans
               if on < CUT_INSTANT - 1e-9 and off > CUT_INSTANT + 1e-6]
    if through:
        fails.append(f"{len(through)} note(s) ring through the cutoff, "
                     f"e.g. ch{through[0][2]}")
    pre = [off for on, off, _ch in allspans if on < CUT_INSTANT - 1e-9]
    if pre and abs(max(pre) - CUT_INSTANT) > 1e-6:
        fails.append(f"last pre-cut note-off {max(pre):.3f}, want the "
                     f"cutoff {CUT_INSTANT} (everything stops together)")
    if TAP_BEAT - CUT_INSTANT < 1.0 - 1e-9:
        fails.append(f"only {TAP_BEAT - CUT_INSTANT:.2f} beats of silence "
                     f"before the tap, want >= 1.0")
    if abs((CUT_INSTANT - CUT_T0) - 3.0) > 1e-9:
        fails.append("the cutoff is not on quaver 6 of the last bar")
    return fails[:8]


def _o_theme_fragment(sc):
    """Exactly the theme's first three notes (A-G-F) appear, at the cutoff;
    no complete 6-note statement occurs anywhere (T5's privilege)."""
    fails = []
    frag = [(b, p) for b, p, _v in _ons_b(sc, CH_VIOLIN) if b >= CUT_T0 - 1e-9]
    want = [(CUT_T0 + on, en.pitch(THEME_BASE, _MM, deg))
            for on, _du, deg in material.THEME[:3]]
    if len(frag) != 3:
        fails.append(f"the cutoff has {len(frag)} violin notes, want the "
                     f"3-note theme head A-G-F")
    for (gb, gp), (wb, wp) in zip(frag, want):
        if abs(gb - wb) > 1e-6 or gp != wp:
            fails.append(f"theme-head note: got ({gb:.3f},{gp}) want "
                         f"({wb:.3f},{wp})")
            break
    degs = [d for _on, _du, d in material.THEME]
    sig = [en.deg_semis(_MM, b) - en.deg_semis(_MM, a)
           for a, b in zip(degs, degs[1:])]
    for ch in sorted(sc.events):
        ons = _ons_b(sc, ch)
        for i in range(len(ons) - 5):
            win = ons[i:i + 6]
            if [b[1] - a[1] for a, b in zip(win, win[1:])] == sig:
                fails.append(f"a complete 6-note theme statement sounds on "
                             f"ch{ch} at beat {win[0][0]:.2f} (only the "
                             f"3-note head is allowed on this track)")
                break
    return fails[:8]


def _o_metronomic(sc, info):
    """The anti-rubato oracle: exactly one tempo event (the point of T3)."""
    fails = []
    if len(PART.TEMPO_MAP) != 1:
        fails.append(f"{len(PART.TEMPO_MAP)} tempo events, want exactly 1 "
                     f"(T3 is metronomic - a flat map is mandatory here)")
    elif PART.TEMPO_MAP[0] != (0.0, 112.0):
        fails.append(f"tempo {PART.TEMPO_MAP[0]}, want (0.0, 112.0)")
    if len(sc.tempos) != 1:
        fails.append(f"Score has {len(sc.tempos)} tempo events, want 1")
    if info is not None and info.get("tempo_events") != 1:
        fails.append(f"file has {info['tempo_events']} tempo events, want 1")
    return fails


def _o_static_devices(sc):
    """The static lane's controllers: portamento across the B section, the
    RPN bend range at setup, and the one autopanning shimmer."""
    fails = []
    cc65 = _cc_b(sc, CH_VIOLIN, 65)
    if not any(abs(b - B_START) < 0.1 and v == 127 for b, v in cc65):
        fails.append(f"portamento not switched on at the B section ({B_START})")
    if not any(abs(b - B_END) < 0.1 and v == 0 for b, v in cc65):
        fails.append(f"portamento not released at {B_END}")
    if not _cc_b(sc, CH_VIOLIN, 5):
        fails.append("no CC5 portamento-time set on the violin")
    if not any(abs(b) < 0.05 and v == 2 for b, v in _cc_b(sc, CH_VIOLIN, 6)):
        fails.append("RPN bend-range (=2) not set at setup on the violin")
    pans = {v for _b, v in _cc_b(sc, CH_SHIMMER, 10)}
    if len(pans) < 3:
        fails.append(f"the crystal shimmer does not autopan (CC10 {pans})")
    return fails


def oracles(sc, info, spans):
    return [
        ("pulse_isochrony", _o_pulse(sc)),
        ("transposed_ground", _o_ground(sc)),
        ("moto_derivation", _o_moto(sc)),
        ("morse_lane", _o_morse(sc)),
        ("dry_violin", _o_dry_violin(sc)),
        ("cutoff_shape", _o_cutoff(sc)),
        ("theme_fragment", _o_theme_fragment(sc)),
        ("metronomic_map", _o_metronomic(sc, info)),
        ("static_devices", _o_static_devices(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — the render, not just the event data
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    # 1. The machine is steady: body windows stay within a tight band (unlike
    #    the rubato elegies, whose energy swings widely).
    levels = []
    for b0, b1 in ((48.0, 80.0), (176.0, 208.0), (360.0, 424.0)):
        i0, i1 = ctx.bar_window(b0, b1)
        levels.append(ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1)))
    fails = []
    if max(levels) - min(levels) > 9.0:
        fails.append(f"pulse energy swings {max(levels) - min(levels):.1f} dB "
                     f"across the body (the machine should stay steady)")
    checks.append(("audio_pulse_steady", fails))

    # 2. The interruption: near-silence between the cutoff and the tap.
    g0, g1 = ctx.bar_window(CUT_INSTANT + 0.05, TAP_BEAT - 0.05)
    gap = ctx.db(ctx.rms(ctx.l, ctx.r, g0, g1))
    p0, p1 = ctx.bar_window(CUT_T0, CUT_INSTANT)
    pre = ctx.db(ctx.rms(ctx.l, ctx.r, p0, p1))
    fails = []
    if gap > pre - 15.0:
        fails.append(f"interruption {gap:.1f} dB not >= 15 dB under the final "
                     f"bar {pre:.1f} dB")
    checks.append(("audio_interruption", fails))

    # 3. The final tap actually sounds after the silence.
    t0, t1 = ctx.bar_window(TAP_BEAT, TAP_BEAT + 1.0)
    tap = ctx.db(ctx.rms(ctx.l, ctx.r, t0, t1))
    fails = []
    if tap < gap + 4.0:
        fails.append(f"final tap {tap:.1f} dB not clearly above the silence "
                     f"{gap:.1f} dB")
    checks.append(("audio_final_tap", fails))
    return checks
