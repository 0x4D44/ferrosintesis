"""movements/t01_october_the_fourteenth.py — track 1 of *The Remaining*.

THE DEPARTURE ITSELF.  Solo piano states the departure figure over the
ground under soft pedal; a sub drone joins; then a Richter build adds one
voice per 8-bar cycle (cello lament, viola sighs, violin II beginning the
DEPARTED LINE at sixfold augmentation — so slow it reads as weather, not
melody — violin I the VIGIL THEME).  At beat 193.5 — a mid-bar quaver,
1.5 beats into note seven of the departed line — violin II and viola stop
mid-note, everything else happens to end, and there are 2.5 beats of total
silence.  The piano resumes alone with the HOLED figure (quavers {3,6}
gone — the peak of the phrase simply isn't there); drone, cello and
violin I re-enter one by one around the holes; the Vigil states the theme
twice more, the second statement's waiting tone E hanging over a bare
open fifth D–A while the piano erodes to a lone repeated quaver D.
Every structural device is oracle-pinned below.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 1
TITLE = "October the Fourteenth"
FILE = "01 - October the Fourteenth.mid"
SEED = 20261014
COMMENT = (
    "The departure itself. A piano ostinato over a four-chord ground, a "
    "string build one voice per cycle, and a violin phrase interrupted on "
    "its seventh note at beat 193.5 - mid-bar, mid-thought. 2.5 beats of "
    "total silence; then the same music returns missing two of its eight "
    "quavers, and the remaining voices keep playing around the holes.")

# ---------------------------------------------------------------------------
# Pinned geometry (the oracles below verify all of it against material.py)
# ---------------------------------------------------------------------------

BASE = en.n("D4")                                # 62 — string-line tonic
PIANO_ROOTS = [en.n("D3"), en.n("Bb2"), en.n("F3"), en.n("C3")]
MINORITY = [True, False, False, False]           # chord thirds on the walk
VIOLA_ROOTS = [r + 12 for r in PIANO_ROOTS]
DRONE_D = en.n("D1")                             # 26

LINE_START = 144.0                               # departed line enters (II c3)
LINE_STRETCH = 6.0                               # sixfold augmentation
DEPARTURE_BEAT = 193.5                           # mid-bar quaver, NOT a downbeat
SILENCE_END = 196.0                              # 2.5 beats of nothing
FREEZE_BEAT = 292.0                              # harmony stops; lone D from here
LAST_NOTE = 336.0                                # the final quaver D
END = 340.0

_MM = material.MODE_MINOR
HOLED_SET = tuple(sorted(set(range(8)) - set(material.HOLES)))   # (0,1,2,4,5,7)

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Morning", 0.0, 64.0),
               ("II. The Vanishing", 64.0, 192.0),
               ("III. The Fourteenth", 192.0, 260.0),
               ("IV. Vigil", 260.0, END)],
    tempo_map=[(0.0, 63.0), (4.0, 66.0), (28.0, 62.0), (32.0, 66.0),
               (56.0, 61.0), (64.0, 66.0), (92.0, 63.0), (96.0, 67.0),
               (124.0, 63.0), (128.0, 67.0), (156.0, 64.0), (160.0, 68.0),
               (186.0, 64.0), (190.0, 60.0), (192.0, 58.0), (196.0, 60.0),
               (212.0, 62.0), (228.0, 63.0), (236.0, 64.0), (252.0, 60.0),
               (260.0, 59.0), (284.0, 58.0), (300.0, 57.0), (316.0, 55.0),
               (328.0, 54.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=[(0, "piano", 0, 100, material.SEATING["piano"], 58),
              (1, "violin I", 40, 96, material.SEATING["violin1"], 66),
              (2, "violin II", 40, 96, material.SEATING["violin2"], 66),
              (3, "viola", 41, 92, material.SEATING["viola"], 64),
              (4, "cello", 42, 98, material.SEATING["cello"], 62),
              (5, "sub drone", 38, 88, material.SEATING["bass"], 45)],
    extra_markers=[(DEPARTURE_BEAT, "the departure")],
)

PROGRAM_WHITELIST = {0, 38, 40, 41, 42}
CENTERED_CHANNELS = {0, 5}
NOTE_RANGES = {0: (32, 72), 1: (59, 84), 2: (60, 80),
               3: (52, 76), 4: (36, 60), 5: (24, 30)}
GAP_WHITELIST: list[tuple[float, float]] = [(DEPARTURE_BEAT, SILENCE_END)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (312.0, 348.0)
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# the cello's four-bar mourning line under the build (II)
_CELLO_LINE = [(0.0, "D3"), (2.0, "C3"), (4.0, "Bb2"), (6.0, "D3"),
               (8.0, "A2"), (10.0, "F3"), (12.0, "E3"), (14.0, "G3")]
# post-departure cello re-entry: one long tone per bar, around the holes
_CELLO_REENTRY = {0: "A2", 1: "Bb2", 2: "A2", 3: "G2"}


# ---------------------------------------------------------------------------
# Emitters (all oracle-adjacent lanes jt=0)
# ---------------------------------------------------------------------------

def _piano_bar(sc, bar, walk_i, vel, holes=frozenset(), lh=False):
    root = PIANO_ROOTS[walk_i]
    material.play_figure(sc, 0, bar, root, minor=MINORITY[walk_i],
                         vel=vel, vel_end=vel + 6, holes=holes, jt=0, jv=2)
    if lh:
        sc.note(0, root - 12, bar, 3.9, max(1, vel - 12), jt=0, jv=2)
    en.sustain(sc, 0, bar, bar + 3.9)


def _viola_sigh(sc, bar, walk_i, vel):
    root = VIOLA_ROOTS[walk_i]
    s, r = material.SUSPENSIONS[walk_i]
    sc.note(3, root + s, bar, 1.0, vel + 6, jt=0, jv=2)          # the sigh
    sc.note(3, root + r, bar + 1.0, 3.0, vel, jt=0, jv=2)        # resolves


def _emit_theme(sc, ch, t0, base, vel, vel_end=None, last_dur=None,
                vib=0.0, vib_last=True):
    """One oracle-pinned VIGIL THEME statement, augmented x2, jt=0."""
    notes = material.theme_notes(stretch=2.0)
    total = notes[-1][0] + notes[-1][1]
    for i, (on, du, deg) in enumerate(notes):
        d = du
        last = (i == len(notes) - 1)
        if last and last_dur is not None:
            d = last_dur
        v = vel if vel_end is None else round(en.lerp(vel, vel_end, on / total))
        sc.note(ch, en.pitch(base, _MM, deg), t0 + on, d, v, jt=0, jv=0)
        if vib > 0 and d >= 1.9 and (vib_last or not last):
            en.vibrato(sc, ch, t0 + on + 0.35, d - 0.85, depth=vib)


# ---------------------------------------------------------------------------
# I. Morning [0, 64) — solo piano, soft pedal; the drone joins at 32
# ---------------------------------------------------------------------------

def _b_morning(sc):
    en.soft_pedal(sc, 0, 0.0, 64.0)
    swell = [0, 1, 2, 3, 3, 2, 1, 0]
    for bar_i in range(16):
        vel = (46 if bar_i < 8 else 51) + swell[bar_i % 8]
        _piano_bar(sc, bar_i * 4.0, bar_i % 4, vel)
    en.expr_curve(sc, 0, [(0.0, 88), (24.0, 96), (31.0, 86), (32.0, 90),
                          (52.0, 98), (63.0, 84)], step=1.0)
    for k, t in enumerate((32.0, 48.0)):
        sc.note(5, DRONE_D, t, 16.0, 38 + 2 * k, jt=0, jv=0)
    en.expr_curve(sc, 5, [(32.0, 30), (40.0, 52), (47.5, 34), (48.0, 36),
                          (56.0, 58), (63.5, 36)], step=1.0)


# ---------------------------------------------------------------------------
# II. The Vanishing [64, 192) — one voice per 8-bar cycle
# ---------------------------------------------------------------------------

def _b_vanishing(sc):
    swell = [0, 1, 2, 2, 3, 2, 1, 0]
    for bar_i in range(16, 48):
        cyc = (bar_i - 16) // 8
        vel = 54 + 4 * cyc + swell[bar_i % 8]
        _piano_bar(sc, bar_i * 4.0, bar_i % 4, vel, lh=(cyc >= 2))
    en.expr_curve(sc, 0, [(64.0, 92), (96.0, 96), (128.0, 100),
                          (160.0, 104), (190.0, 110)], step=2.0)

    # sub drone breathes in 8-beat waves; the last wave rings to the cut
    for k in range(15):
        sc.note(5, DRONE_D, 64.0 + 8.0 * k, 8.0, 40 + k // 4, jt=0, jv=0)
    sc.note(5, DRONE_D, 184.0, DEPARTURE_BEAT - 184.0, 44, jt=0, jv=0)
    en.expr_curve(sc, 5, [(64.0, 40), (128.0, 52), (190.0, 62)], step=2.0)

    # cycle 1: cello mourning line (eight 4-bar passes)
    for p in range(8):
        t0, vel = 64.0 + 16.0 * p, 48 + 2 * p
        for on, name in _CELLO_LINE:
            b = t0 + on
            sc.note(4, en.n(name), b, 1.96, vel, jt=0, jv=2)
            en.vibrato(sc, 4, b + 0.3, 1.2, depth=0.12 + 0.02 * p)
        en.expr_curve(sc, 4, [(t0, 44), (t0 + 9, 80 + 2 * p),
                              (t0 + 15.5, 48)], step=1.0)
    en.cc_curve(sc, 4, 1, [(64.0, 12), (192.0, 55)], step=4.0)

    # cycle 2: viola suspensions inside the ground
    for bar_i in range(24, 48):
        _viola_sigh(sc, bar_i * 4.0, bar_i % 4, 46 + (bar_i - 24) // 4)
    en.expr_curve(sc, 3, [(96.0, 52), (128.0, 60), (160.0, 68),
                          (190.0, 74)], step=2.0)
    en.cc_curve(sc, 3, 1, [(96.0, 10), (192.0, 48)], step=4.0)

    # cycle 3: violin II begins the DEPARTED LINE, x6 augmentation
    for k, (on, du, deg) in enumerate(material.departed_notes(6)):
        b = LINE_START + LINE_STRETCH * on
        d = LINE_STRETCH * du
        sc.note(2, en.pitch(BASE, _MM, deg), b, d,
                (58, 61, 64, 67, 70, 74)[k], jt=0, jv=0)
        en.vibrato(sc, 2, b + 0.5, d - 1.0, depth=0.16 + 0.03 * k)
        en.expr_curve(sc, 2, [(b, 48), (b + d * 0.6, 78 + 3 * k),
                              (b + d - 0.1, 60)], step=0.5)
    en.cc_curve(sc, 2, 1, [(144.0, 20), (192.0, 58)], step=4.0)

    # cycle 4: violin I states the VIGIL THEME twice; the second E hangs
    _emit_theme(sc, 1, 160.0, BASE, vel=56, vel_end=62, vib=0.20)
    _emit_theme(sc, 1, 176.0, BASE, vel=62, vel_end=68,
                last_dur=DEPARTURE_BEAT - 188.0, vib=0.24, vib_last=False)
    en.vibrato(sc, 1, 188.4, 3.0, depth=0.28)     # recentres before beat 192
    en.expr_curve(sc, 1, [(160.0, 50), (168.0, 84), (176.0, 60),
                          (186.0, 92), (191.5, 96)], step=1.0)
    en.cc_curve(sc, 1, 1, [(160.0, 25), (192.0, 55)], step=4.0)


# ---------------------------------------------------------------------------
# III. The Fourteenth [192, 260) — the cut, the silence, the holed return
# ---------------------------------------------------------------------------

def _b_fourteenth(sc):
    # the cut bar: figure interrupted after quaver 2, everyone rings to 193.5
    material.play_figure(sc, 0, 192.0, PIANO_ROOTS[0], minor=True, vel=70,
                         holes=frozenset({3, 4, 5, 6, 7}), jt=0, jv=2)
    en.sustain(sc, 0, 192.0, DEPARTURE_BEAT)
    sc.note(3, VIOLA_ROOTS[0] + material.SUSPENSIONS[0][0], 192.0,
            DEPARTURE_BEAT - 192.0, 62, jt=0, jv=0)   # a sigh never resolved
    sc.note(4, en.n("D2"), 192.0, DEPARTURE_BEAT - 192.0, 58, jt=0, jv=0)
    on7, _du7, deg7 = material.DEPARTED_LINE[material.INTERRUPT_AFTER - 1]
    b7 = LINE_START + LINE_STRETCH * on7              # 192.0
    sc.note(2, en.pitch(BASE, _MM, deg7), b7, DEPARTURE_BEAT - b7,
            72, jt=0, jv=0)                           # note 7, cut mid-note

    # [193.5, 196.0): TOTAL silence — whitelisted, the album's only one

    # the piano resumes alone: the holed figure, una corda
    en.soft_pedal(sc, 0, SILENCE_END, 339.5)
    for bar_i in range(49, 65):
        _piano_bar(sc, bar_i * 4.0, (bar_i - 49) % 4,
                   44 + (bar_i - 49) // 2, holes=material.HOLES)
    en.expr_curve(sc, 0, [(196.0, 80), (212.0, 86), (236.0, 92),
                          (259.0, 88)], step=2.0)

    # re-entries, one by one: drone 212, cello 220, violin I 236
    for k in range(6):
        sc.note(5, DRONE_D, 212.0 + 8.0 * k, 8.0,
                34 + (1 if k >= 3 else 0), jt=0, jv=0)
    en.expr_curve(sc, 5, [(212.0, 28), (232.0, 44), (259.5, 38)], step=2.0)

    for bar_i in range(55, 65):
        bar = bar_i * 4.0
        p = en.n(_CELLO_REENTRY[(bar_i - 49) % 4])
        sc.note(4, p, bar + 1.0, 3.0, 46 + (bar_i - 55), jt=0, jv=2)
        en.vibrato(sc, 4, bar + 1.3, 2.2, depth=0.24)
    en.expr_curve(sc, 4, [(221.0, 40), (240.0, 66), (259.5, 52)], step=2.0)

    for t0, v in ((236.0, 50), (248.0, 55)):          # half-phrases only:
        for on, du, deg in material.THEME[:3]:        # the vigil lacks the
            sc.note(1, en.pitch(BASE, _MM, deg),      # strength to finish
                    t0 + 2.0 * on, 2.0 * du, v, jt=0, jv=0)
        en.vibrato(sc, 1, t0 + 4.4, 3.0, depth=0.30)
        en.expr_curve(sc, 1, [(t0, 42), (t0 + 5, 72), (t0 + 7.9, 36)],
                      step=0.5)
    en.cc_curve(sc, 1, 1, [(236.0, 40), (260.0, 60)], step=4.0)


# ---------------------------------------------------------------------------
# IV. Vigil [260, 340) — two theme statements; the fifth; the lone D
# ---------------------------------------------------------------------------

def _b_vigil(sc):
    for bar_i in range(65, 73):                       # holed walk continues
        _piano_bar(sc, bar_i * 4.0, (bar_i - 49) % 4,
                   46 - (bar_i - 65) // 2, holes=material.HOLES)
    for bar_i in range(73, 84):                       # the root alone
        bar = bar_i * 4.0
        vel = 42 - (bar_i - 73) // 2
        for q in HOLED_SET:
            sc.note(0, PIANO_ROOTS[0], bar + 0.5 * q, 0.45, vel, jt=0, jv=1)
        en.sustain(sc, 0, bar, bar + 3.9)
    sc.note(0, PIANO_ROOTS[0], LAST_NOTE, 3.5, 36, jt=0, jv=0)
    en.sustain(sc, 0, LAST_NOTE, LAST_NOTE + 3.5)
    en.expr_curve(sc, 0, [(260.0, 86), (292.0, 78), (320.0, 66),
                          (339.0, 52)], step=2.0)

    # the vigil: the theme twice; the second, an octave up, ends on the
    # waiting tone E held twenty beats over the bare fifth
    _emit_theme(sc, 1, 264.0, BASE, vel=54, vel_end=60, vib=0.30)
    _emit_theme(sc, 1, 288.0, BASE + 12, vel=60, vel_end=64,
                last_dur=20.0, vib=0.35)
    en.expr_curve(sc, 1, [(264.0, 46), (272.0, 78), (280.0, 40),
                          (288.0, 55), (300.0, 74), (319.5, 16)], step=1.0)
    en.cc_curve(sc, 1, 1, [(260.0, 45), (300.0, 70), (330.0, 70)], step=4.0)

    # cello: the walk to the freeze, then the bare open fifth D–A
    for bar_i in range(65, 73):
        bar = bar_i * 4.0
        p = en.n(_CELLO_REENTRY[(bar_i - 49) % 4])
        sc.note(4, p, bar + 1.0, 3.0, 44 + (72 - bar_i), jt=0, jv=2)
        en.vibrato(sc, 4, bar + 1.3, 2.2, depth=0.26)
    for t0, d in ((FREEZE_BEAT, 12.0), (304.0, 12.0), (316.0, 8.0)):
        sc.note(4, en.n("D2"), t0, d, 44, jt=0, jv=0)
        sc.note(4, en.n("A2"), t0, d, 40, jt=0, jv=0)
        en.at_curve(sc, 4, [(t0, 0), (t0 + d * 0.6, 58), (t0 + d - 0.2, 0)],
                    step=0.5)
    en.expr_curve(sc, 4, [(261.0, 52), (292.0, 58), (316.0, 48),
                          (323.5, 30)], step=2.0)

    for k in range(9):                                # the floor, fading
        sc.note(5, DRONE_D, 260.0 + 8.0 * k, 8.0, 34, jt=0, jv=0)
    sc.note(5, DRONE_D, 332.0, 4.0, 32, jt=0, jv=0)
    en.expr_curve(sc, 5, [(260.0, 38), (300.0, 34), (336.0, 20)], step=2.0)


BUILDERS = [_b_morning, _b_vanishing, _b_fourteenth, _b_vigil]


# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES §2 pattern)
# ---------------------------------------------------------------------------

def _ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / en.PPQ, d[1], d[2]))
    return sorted(out)


def _spans(sc, ch):
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


def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for b, _p, v in _ons(sc, ch):
            out[int(b // 4)] = out.get(int(b // 4), 0.0) + v
    return out


def _theme_sig():
    degs = [d for _on, _du, d in material.THEME]
    return [en.deg_semis(_MM, b) - en.deg_semis(_MM, a)
            for a, b in zip(degs, degs[1:])]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _o_departure(sc):
    fails = []
    want = [(LINE_START + LINE_STRETCH * on, en.pitch(BASE, _MM, deg))
            for on, _du, deg in
            material.DEPARTED_LINE[:material.INTERRUPT_AFTER]]
    got = [(b, p) for b, p, _v in _ons(sc, 2)]
    if len(got) != material.INTERRUPT_AFTER:
        fails.append(f"violin II has {len(got)} note-ons, want exactly "
                     f"{material.INTERRUPT_AFTER}")
    for i, ((wb, wp), (gb, gp)) in enumerate(zip(want, got)):
        if abs(wb - gb) > 1e-6 or wp != gp:
            fails.append(f"departed-line note {i}: got ({gb:.3f},{gp}) "
                         f"want ({wb:.3f},{wp})")
    sp2 = _spans(sc, 2)
    if sp2:
        last_on, last_off, _p = sp2[-1]
        nat_end = LINE_START + LINE_STRETCH * (
            material.DEPARTED_LINE[material.INTERRUPT_AFTER - 1][0]
            + material.DEPARTED_LINE[material.INTERRUPT_AFTER - 1][1])
        if abs(last_off - DEPARTURE_BEAT) > 1e-6:
            fails.append(f"note 7 off at {last_off:.3f}, want the "
                         f"departure beat {DEPARTURE_BEAT}")
        if not last_on < DEPARTURE_BEAT < nat_end:
            fails.append("the cut must land MID-note-7 "
                         f"({last_on} .. {nat_end})")
    ons3 = [b for b, _p, _v in _ons(sc, 3)]
    if not ons3 or max(ons3) > 192.0 + 1e-6:
        fails.append("viola note-ons must cease at beat 192.0")
    late3 = [off for on, off, _p in _spans(sc, 3) if on >= 191.9]
    if not late3 or abs(max(late3) - DEPARTURE_BEAT) > 1e-6:
        fails.append("viola's last note must be cut exactly at the "
                     "departure beat")
    return fails


def _o_holes(sc):
    fails = []
    if HOLED_SET != (0, 1, 2, 4, 5, 7):
        fails.append(f"holed quaver set {HOLED_SET} does not match "
                     f"material.HOLES")
    bars = {}
    for b, p, _v in _ons(sc, 0):
        q = (b % 4.0) / 0.5
        if abs(q - round(q)) > 1e-6:
            fails.append(f"piano onset off the quaver grid at beat {b:.3f}")
            continue
        bars.setdefault(int(b // 4) * 4, set()).add(int(round(q)))
    for bar, quavers in sorted(bars.items()):
        if bar < 192.0:
            want = set(range(8))
            tag = "pre-departure"
        elif bar == 192.0:
            want = {0, 1, 2}
            tag = "the cut bar"
        elif bar < LAST_NOTE:
            want = set(HOLED_SET)
            tag = "post-departure"
        else:
            want = {0}
            tag = "the last bar"
        if quavers != want:
            fails.append(f"{tag} bar {bar:.0f}: quavers "
                         f"{sorted(quavers)} want {sorted(want)}")
    for b, p, _v in _ons(sc, 0):
        if b >= FREEZE_BEAT and p != PIANO_ROOTS[0]:
            fails.append(f"after the freeze the piano may only sound its "
                         f"root D ({PIANO_ROOTS[0]}), got {p} at {b:.1f}")
    return fails[:8]


def _o_additive(sc):
    fails = []
    sums = _bar_sums(sc)

    def mean(lo, hi):
        bars = range(int(lo // 4), int(hi // 4))
        return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))

    wins = [(0.0, 32.0), (32.0, 64.0), (64.0, 96.0), (96.0, 128.0),
            (128.0, 160.0), (160.0, 192.0)]
    means = [mean(lo, hi) for lo, hi in wins]
    for i in range(len(means) - 1):
        if means[i + 1] <= means[i]:
            fails.append(f"bar-sum energy not rising into cycle {i + 1}: "
                         f"{means[i]:.0f} -> {means[i + 1]:.0f}")
    entries = {5: (32.0, 64.0), 4: (64.0, 96.0), 3: (96.0, 128.0),
               2: (128.0, 160.0), 1: (160.0, 192.0)}
    for ch, (lo, hi) in sorted(entries.items()):
        ons = [b for b, _p, _v in _ons(sc, ch)]
        if not ons:
            fails.append(f"ch{ch} never plays")
        elif not lo <= ons[0] < hi:
            fails.append(f"ch{ch} first note at {ons[0]:.1f}, want its "
                         f"cycle [{lo:.0f},{hi:.0f})")
    return fails


def _o_theme(sc):
    fails = []
    sig = _theme_sig()
    waiting_pc = en.pitch(BASE, _MM, material.THEME_END_DEG) % 12
    tonic_pc = en.pitch(BASE, _MM, 1) % 12
    rel = [on for on, _du, _deg in material.theme_notes(stretch=2.0)]
    pinned = {160.0: BASE, 176.0: BASE, 264.0: BASE, 288.0: BASE + 12}
    hits = {}
    for ch in sorted(sc.events):
        ons = _ons(sc, ch)
        for i in range(len(ons) - 5):
            win = ons[i:i + 6]
            if [w2[1] - w1[1] for w1, w2 in zip(win, win[1:])] != sig:
                continue
            hits.setdefault(ch, []).append(win)
            if win[-1][1] % 12 != waiting_pc:
                fails.append(f"ch{ch} theme statement at {win[0][0]:.1f} "
                             f"ends pc {win[-1][1] % 12}, not the waiting "
                             f"tone")
            if i + 6 < len(ons) and ons[i + 6][1] % 12 == tonic_pc:
                fails.append(f"ch{ch} statement at {win[0][0]:.1f} is "
                             f"followed by the tonic - the arrival is "
                             f"T5's alone")
    others = {ch: h for ch, h in hits.items() if ch != 1}
    if others:
        fails.append(f"complete theme statements outside violin I: "
                     f"{sorted(others)}")
    got = hits.get(1, [])
    if len(got) != len(pinned):
        fails.append(f"violin I has {len(got)} complete statements, "
                     f"want {len(pinned)} at {sorted(pinned)}")
    for win in got:
        t0 = win[0][0]
        if t0 not in pinned:
            fails.append(f"unpinned theme statement at {t0:.2f}")
            continue
        base = pinned[t0]
        for k, (b, p, _v) in enumerate(win):
            won = rel[k]
            wp = en.pitch(base, _MM,
                          material.theme_notes(stretch=2.0)[k][2])
            if abs((b - t0) - won) > 1e-6 or p != wp:
                fails.append(f"statement at {t0:.0f}, note {k}: "
                             f"({b - t0:.2f},{p}) want ({won:.2f},{wp})")
    return fails[:8]


def _o_silence(sc):
    fails = []
    if (DEPARTURE_BEAT * 2.0) % 1.0 != 0.0:
        fails.append("departure beat is not on the quaver grid")
    if DEPARTURE_BEAT % 4.0 == 0.0:
        fails.append("departure beat must NOT be a downbeat")
    if GAP_WHITELIST != [(DEPARTURE_BEAT, SILENCE_END)] or \
            abs(SILENCE_END - DEPARTURE_BEAT - 2.5) > 1e-9:
        fails.append("GAP_WHITELIST must be exactly the one 2.5-beat "
                     "departure silence")
    on7 = LINE_START + LINE_STRETCH * material.DEPARTED_LINE[
        material.INTERRUPT_AFTER - 1][0]
    if not on7 < DEPARTURE_BEAT < on7 + 4.0:
        fails.append("departure beat is not inside note 7 of the line")
    allspans = [s for ch in sc.events for s in _spans(sc, ch)]
    ring = [(on, off) for on, off, _p in allspans
            if on < DEPARTURE_BEAT - 1e-9 and off > DEPARTURE_BEAT + 1e-6]
    if ring:
        fails.append(f"{len(ring)} note(s) ring through the departure, "
                     f"e.g. {ring[0]}")
    pre_offs = [off for on, off, _p in allspans if on < DEPARTURE_BEAT]
    if abs(max(pre_offs) - DEPARTURE_BEAT) > 1e-6:
        fails.append(f"last pre-departure note-off {max(pre_offs):.3f}, "
                     f"want {DEPARTURE_BEAT}")
    post = sorted(on for on, _off, _p in allspans
                  if on > DEPARTURE_BEAT - 1e-9)
    if not post or abs(post[0] - SILENCE_END) > 1e-6:
        fails.append(f"first post-silence note at "
                     f"{post[0] if post else None}, want {SILENCE_END}")
    return fails


def _o_rubato():
    fails = []
    tm = PART.TEMPO_MAP
    bpms = [b for _t, b in tm]
    if len(tm) < 12:
        fails.append(f"only {len(tm)} tempo events - the map may not be flat")
    if max(bpms) - min(bpms) < 8.0:
        fails.append("tempo range under 8 bpm - not enough rubato")
    dips = sum(1 for a, b in zip(bpms, bpms[1:]) if b < a)
    if dips < 4:
        fails.append(f"only {dips} tempo dips, want phrase-end breathing")
    if bpms[-1] > 56.0:
        fails.append(f"final tempo {bpms[-1]} - the vigil must ritard "
                     f"to <= 56")
    for name, t0, t1 in PART.MOVEMENTS:
        seg = [(t, b) for t, b in tm if t0 <= t < t1]
        if not any(b2 < b1 for (_t1, b1), (_t2, b2) in zip(seg, seg[1:])):
            fails.append(f"no tempo dip inside '{name}'")
    return fails


def oracles(sc, info, spans):
    return [
        ("departure_discipline", _o_departure(sc)),
        ("holes_pattern", _o_holes(sc)),
        ("additive_build", _o_additive(sc)),
        ("theme_waiting_tone", _o_theme(sc)),
        ("silence_gap", _o_silence(sc)),
        ("rubato_nonflat", _o_rubato()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py): the silence is silent; the drop is a drop
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    i0, i1 = ctx.bar_window(194.75, 195.85)
    silence = ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))
    j0, j1 = ctx.bar_window(188.0, 193.0)
    tutti = ctx.db(ctx.rms(ctx.l, ctx.r, j0, j1))
    fails = []
    if silence > tutti - 20.0:
        fails.append(f"departure silence {silence:.1f} dB is not >= 20 dB "
                     f"under the tutti {tutti:.1f} dB")
    if silence > -36.0:
        fails.append(f"departure silence {silence:.1f} dB above -36 dBFS")
    checks.append(("audio_departure_silence", fails))

    a0, a1 = ctx.bar_window(197.0, 211.0)
    alone = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    fails = []
    if alone > tutti - 3.0:
        fails.append(f"piano-alone {alone:.1f} dB not >= 3 dB under the "
                     f"pre-departure tutti {tutti:.1f} dB")
    checks.append(("audio_intimate_drop", fails))

    c0, c1 = ctx.bar_window(66.0, 94.0)
    early = ctx.db(ctx.rms(ctx.l, ctx.r, c0, c1))
    d0, d1 = ctx.bar_window(162.0, 190.0)
    late = ctx.db(ctx.rms(ctx.l, ctx.r, d0, d1))
    fails = []
    if late < early + 3.0:
        fails.append(f"build cycle 4 {late:.1f} dB not >= 3 dB over "
                     f"cycle 1 {early:.1f} dB")
    checks.append(("audio_additive_build", fails))
    return checks
