"""t04_the_mail_boat.py — track 4 of *Lantern Year*: "The Mail Boat".

April.  The mail boat comes round the point on a bright morning and the
whole rock dances: a set of two jigs in 6/8 at dotted-quarter = 108
(tempo 162, three quarter-note beats to the bar, an eighth = 0.5 beat).

    I.   Casting Off             8 bars   guitar, woodblock "put-put", the
                                          boat's two-note whistle
    II.  The Mail Boat (G)       3 rounds fiddle / whistle / accordion+fiddle
    III. The Outbound Tide       3 rounds mandolin (the hush) / fiddle /
         (E dorian)                       accordion+whistle
    IV.  Rounding the Point      4 bars   E -> E7, the accelerando
    V.   The Mail Boat in A      2 rounds fiddle+whistle / everybody, with the
                                          keeper's HYMN (phrase 1) as an
                                          accordion descant over the A parts
    VI.  Stamped Home            6 bars   tag, two stamps and the tonic

Every round is AABB, 8 bars a part, the repeats exact.  The first jig's
opening figure IS the BEAM (G d e d g2 — degrees 1-5-6-5-8), so every A
part of every jig-1 round states it twice.  Every note-on in the track
sits on the eighth-note lattice (jt=0 throughout; the fiddle's ornaments
are pitch-bend slides, which add no onsets).
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 4
TITLE = "The Mail Boat"
FILE = "04 - The Mail Boat.mid"
SEED = 20261204
COMMENT = ("Lantern Year, track 4: The Mail Boat. April; a set of two jigs "
           "in 6/8 (dotted quarter = 108). The Mail Boat in G, whose opening "
           "figure is the album's BEAM cell, three rounds handed from fiddle "
           "to whistle to accordion; The Outbound Tide in E dorian, three "
           "rounds from a hushed mandolin up to the full band; then a short "
           "accelerando and The Mail Boat again a tone higher in A, the "
           "keeper's hymn riding over it on the accordion, and a stamped "
           "tonic. Every round is AABB with exact repeats and every onset "
           "sits on the eighth-note grid.")

PPQ = en.PPQ
E8 = 0.5                    # one eighth note, in beats
BAR = 3.0                   # a 6/8 bar
PART_LEN = 8 * BAR          # one 8-bar part
ROUND = 4 * PART_LEN        # AABB

FID, WHI, ACC, MAN, GTR, BAS, FD2, KIT = 0, 1, 2, 3, 4, 5, 6, 9

T_R = [24.0, 120.0, 216.0, 312.0, 408.0, 504.0, 612.0, 708.0]   # round starts
T_TRANS = 600.0
T_CODA = 804.0
T_STAMP = 819.0
END = 822.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. Casting Off", 0.0, 24.0),
        ("II. The Mail Boat (jig in G)", 24.0, 312.0),
        ("III. The Outbound Tide (jig in E dorian)", 312.0, 600.0),
        ("IV. Rounding the Point", 600.0, 612.0),
        ("V. The Mail Boat, a tone higher (in A)", 612.0, 804.0),
        ("VI. Stamped Home", 804.0, END),
    ],
    tempo_map=[(0.0, 162.0), (600.0, 163.5), (603.0, 165.0),
               (606.0, 166.5), (609.0, 168.0)],
    time_signatures=[(0.0, 6, 8)],
    keysigs=[(0.0, 1, 0), (312.0, 2, 0), (612.0, 3, 0)],
    channels=[
        (FID, "fiddle", 110, 124, 64, 38),
        (WHI, "tin whistle", 78, 66, 78, 44),
        (ACC, "accordion", 21, 96, 46, 36),
        (MAN, "mandolin", 25, 127, 86, 32),
        (GTR, "steel guitar", 25, 90, 40, 28),
        (BAS, "upright bass", 32, 76, 64, 20),
        (FD2, "second fiddle", 110, 90, 56, 40),
        (KIT, "tambourine, woodblock, hand drum", 0, 80, 64, 26),
    ],
    extra_markers=[
        (120.0, "Round 2: whistle"),
        (216.0, "Round 3: accordion and fiddle"),
        (408.0, "Round 5: fiddle"),
        (504.0, "Round 6: accordion and whistle"),
        (708.0, "Round 8: everybody, and the keeper's hymn"),
    ],
)

BEAM_CHANNELS = {FID, WHI, ACC, MAN}
PROGRAM_WHITELIST = {110, 78, 21, 25, 32}
CENTERED_CHANNELS = {FID, BAS, KIT}
NOTE_RANGES = {FID: (55, 88), WHI: (67, 98), ACC: (48, 88), MAN: (55, 92),
               GTR: (40, 72), BAS: (28, 60), FD2: (55, 84)}
GAP_WHITELIST: list = []
BEND_EXEMPT: set = set()
DURATION_WINDOW = (299.0, 306.0)
BOUNDS_WHITELIST: list = []


# ---------------------------------------------------------------------------
# The tunes — ABC-style bars of six eighths.  Upper case = octave 4, lower
# case = octave 5, a trailing comma drops an octave, a digit is the length in
# eighths; the key's sharps are applied by the parser.
# ---------------------------------------------------------------------------

_LET = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71}


def _abc(bars: list, sharps: str) -> list:
    """[[(pitch, start_eighth, len_eighths), ...] per bar]."""
    out = []
    for bar in bars:
        pos, row = 0, []
        for tok in bar.split():
            letter, rest = tok[0], tok[1:]
            p = _LET[letter.upper()] + (12 if letter.islower() else 0)
            if letter.upper() in sharps:
                p += 1
            while rest.startswith(","):
                p -= 12
                rest = rest[1:]
            ln = int(rest) if rest else 1
            row.append((p, pos, ln))
            pos += ln
        if pos != 6:
            raise ValueError(f"bar '{bar}' is {pos} eighths, want 6")
        out.append(row)
    return out


TUNES = {
    # The Mail Boat — G ionian.  Bars 1 and 5 open with the BEAM.
    "J1": {
        "tonic": 7, "mode": "ionian",
        "A": _abc(["G d e d g2", "f e d e d B", "c B c e d c", "A B A F2 D",
                   "G d e d g2", "b2 a g e d", "e c e d B A", "G3 B2 d"], "F"),
        "B": _abc(["e2 g b a g", "e c e g f e", "d B d g f g", "a2 f d e f",
                   "g2 b b a g", "e g e c2 e", "f a f d B A", "G3 B2 d"], "F"),
        "chA": ["G", "Bm", "C", "D", "G", "Em", ("C", "D"), "G"],
        "chB": ["Em", "C", "G", "D", "Em", "C", "D", "G"],
        # bass: the notes on eighths 0, 2, 3, 5
        "bsA": ["G2 B2 D3 B2", "B2 D3 F#3 D3", "C3 E3 G3 E3", "D3 A2 D2 F#2",
                "G2 D3 B2 F#2", "E2 B2 G2 B2", "C3 E3 D3 D2", "G2 B2 D3 D2"],
        "bsB": ["E2 G2 B2 B2", "C3 G2 E2 F#2", "G2 D3 B2 C3", "D3 A2 F#2 D2",
                "E2 B2 E3 D3", "C3 E3 G3 E3", "D3 A2 D2 F#2", "G2 B2 D3 D2"],
        # counter-melody: one note on each dotted-quarter pulse
        "ctA": [("B3", "D4"), ("D4", "B3"), ("E4", "G4"), ("F#4", "D4"),
                ("B3", "D4"), ("G4", "E4"), ("G4", "F#4"), ("B3", "G3")],
        "ctB": [("B4", "G4"), ("G4", "E4"), ("G4", "B4"), ("F#4", "A4"),
                ("B4", "G4"), ("G4", "E4"), ("A4", "F#4"), ("B3", "G3")],
    },
    # The Outbound Tide — E dorian (the C sharp is the colour).
    "J2": {
        "tonic": 4, "mode": "dorian",
        "A": _abc(["E2 B B A B", "d2 B A F D", "E2 B B A B", "c2 e c A c",
                   "e2 B e f g", "f d f a f d", "B d g f d c", "B2 G E2 B,"],
                  "FC"),
        "B": _abc(["g2 d B d g", "a2 f d f a", "b a g e2 g", "f2 d B c d",
                   "g2 d B d g", "a f d f e d", "c e a g e c", "B2 G E2 B,"],
                  "FC"),
        "chA": ["Em", "D", "Em", "A", "Em", "D", ("G", "Bm"), "Em"],
        "chB": ["G", "D", "Em", "Bm", "G", "D", "A7", "Em"],
        "bsA": ["E2 G2 B2 E3", "D3 A2 F#2 D2", "E2 G2 B2 G2", "A2 C#3 A2 D3",
                "E3 B2 G2 C#3", "D3 F#3 A2 F#2", "G2 D3 B2 D3", "E3 B2 E2 B2"],
        "bsB": ["G2 D3 B2 C#3", "D3 A2 F#2 D2", "E2 G2 B2 A2", "B2 F#3 D3 F#2",
                "G2 B2 D3 C#3", "D3 A2 D3 B2", "A2 E3 C#3 D3", "E3 B2 E2 B2"],
        "ctA": [("G3", "B3"), ("F#4", "D4"), ("G3", "B3"), ("E4", "A3"),
                ("G4", "E4"), ("A4", "F#4"), ("G4", "D4"), ("G4", "B3")],
        "ctB": [("B4", "G4"), ("F#4", "A4"), ("G4", "B4"), ("D4", "F#4"),
                ("B4", "G4"), ("F#4", "A4"), ("A3", "E4"), ("G4", "B3")],
    },
}

# Guitar voicings (open shapes; the A rounds are the same shapes "capo 2").
_GTR = {
    "G":  [43, 47, 50, 55, 59, 67],
    "C":  [48, 52, 55, 60, 64],
    "D":  [50, 57, 62, 66],
    "Em": [40, 47, 52, 55, 59, 64],
    "Bm": [47, 54, 59, 62, 66],
    "A":  [45, 52, 57, 61, 64],
    "A7": [45, 52, 55, 61, 64],
    "E5": [40, 47, 52, 59, 64],
    "E":  [40, 47, 52, 56, 59, 64],
    "E7": [40, 47, 50, 56, 59, 64],
}


class _Per(tuple):
    """A per-part value: (A1, A2, B1, B2)."""


def _pp(value, k: int):
    return value[k] if isinstance(value, _Per) else value


# The set: tune, transposition, who leads (channel, octave, velocity), and
# how thick the band is.  The oracles read "tune", "tr" and "leads" from here.
ROUNDS = [
    {"tune": "J1", "tr": 0, "leads": [(FID, 0, 88)],
     "gtr": _Per(((0, 56), (0, 58), (1, 62), (1, 64))),
     "bass": _Per((None, (0, 64), (1, 68), (1, 70))),
     "perc": _Per((0, 0, 1, 1))},
    {"tune": "J1", "tr": 0, "leads": [(WHI, 1, 92)],
     "counter": [(FID, 0, 64)],
     "gtr": (1, 66), "bass": (2, 74),
     "acc": _Per((None, None, ("pad", 58), ("pad", 62))),
     "perc": _Per((1, 1, 2, 2))},
    {"tune": "J1", "tr": 0, "leads": [(FID, 0, 94), (ACC, 0, 90)],
     "counter": [(WHI, 1, 66)],
     "man": ("arp", 70), "gtr": (2, 72), "bass": (3, 82),
     "perc": _Per((2, 2, 3, 3))},
    {"tune": "J2", "tr": 0, "leads": [(MAN, 0, 80)],
     "gtr": _Per((None, (0, 46), (0, 48), (0, 50))),
     "bass": _Per(((0, 48), (0, 50), (1, 52), (1, 54))),
     "perc": -1},
    {"tune": "J2", "tr": 0, "leads": [(FID, 0, 94)],
     "acc": ("pad", 64), "man": ("chop", 66),
     "gtr": (1, 68), "bass": (2, 76),
     "perc": _Per((1, 2, 2, 2))},
    {"tune": "J2", "tr": 0, "leads": [(ACC, 0, 96), (WHI, 1, 80)],
     "counter": [(FID, 0, 72)],
     "man": ("arp", 76), "gtr": (2, 76), "bass": (3, 86),
     "perc": 3},
    {"tune": "J1", "tr": 2, "leads": [(FID, 0, 104), (WHI, 1, 84)],
     "counter": [(FD2, 0, 80)],
     "acc": ("pulse", 70), "man": ("chop", 74),
     "gtr": (2, 80), "bass": (3, 90),
     "perc": _Per((3, 3, 4, 4))},
    {"tune": "J1", "tr": 2,
     "leads": [(FID, 0, 110), (WHI, 1, 88), (MAN, 0, 116)],
     "counter": [(FD2, 0, 88)],
     "hymn": _Per((True, True, False, False)),
     "doubles": _Per(([], [], [(ACC, 0, 98)], [(ACC, 0, 100)])),
     "gtr": (2, 88), "bass": (3, 96),
     "perc": 4},
]

# Who answers whom: round index -> (counter channel, lead channel).
COUNTER_PAIRS = {1: (FID, WHI), 2: (WHI, ACC), 5: (FID, ACC),
                 6: (FD2, FID), 7: (FD2, FID)}
HYMN_BASE = 69              # A4: the descant's degree 1 in the last round
HYMN_STRETCH = 1.5          # one hymn beat = one dotted quarter


# ---------------------------------------------------------------------------
# Players.  Everything is jt=0: the jig grid is a pinned claim.
# ---------------------------------------------------------------------------

_LILT = (8, -9, -3, 4, -9, -2)              # the jig's strong-weak-weak
_GATE = {FID: 0.96, WHI: 0.88, ACC: 0.93, MAN: 0.95, FD2: 0.96}
_BREATHING = (FID, WHI, ACC, FD2)           # voices that take CC11 shapes


def _chord_at(chords: list, bar: int, eighth: int) -> str:
    entry = chords[bar]
    if isinstance(entry, tuple):
        return entry[0] if eighth < 3 else entry[1]
    return entry


def _slide(sc: en.Score, ch: int, beat: float) -> None:
    """A fiddler's slide up into a long note (bend, so no extra onset)."""
    for i in range(5):
        sc.bend(ch, beat + i * 0.045, -0.55 * (1 - i / 4))


def _lead(sc: en.Score, ch: int, t: float, bars: list, tr: int, octv: int,
          vel: int, lift: int = 0) -> None:
    gate = _GATE.get(ch, 0.92)
    span = len(bars) * BAR
    for bi, bar in enumerate(bars):
        swell = (0, 1, 2, 3, 4, 5, 3, 1)[bi % 8]
        for p, pos, ln in bar:
            b = t + bi * BAR + pos * E8
            sc.note(ch, p + tr + 12 * octv, b, ln * E8 * gate,
                    vel + lift + _LILT[pos] + swell, jt=0, jv=3)
            if ch == FID:
                if ln == 2:
                    _slide(sc, ch, b)
                elif ln == 3:
                    en.vibrato(sc, ch, b, 1.35, depth=0.12,
                               cycles_per_beat=2.0, delay=0.3)
    if ch in _BREATHING:
        en.expr_curve(sc, ch, [(t, 104), (t + 0.6 * span, 124),
                               (t + span - 0.5, 108)], step=1.5)


def _counter(sc: en.Score, ch: int, t: float, rows: list, tr: int,
             octv: int, vel: int) -> None:
    for bi, pair in enumerate(rows):
        x = t + bi * BAR
        for half, name in enumerate(pair):
            sc.note(ch, en.n(name) + tr + 12 * octv, x + half * 1.5,
                    1.5 * 0.96, vel + (4 if half == 0 else 0), jt=0, jv=3)
        en.cc_curve(sc, ch, 11, [(x, 92), (x + 1.5, 116), (x + 2.75, 94)],
                    step=0.25)


_GPAT = {       # (eighth, full chord?, length in eighths, velocity offset)
    0: ((0, 1, 3, 0), (3, 0, 3, -14)),
    1: ((0, 1, 2, 0), (2, 0, 1, -22), (3, 1, 2, -8), (5, 0, 1, -16)),
    2: ((0, 1, 1, 0), (1, 0, 1, -30), (2, 0, 1, -16),
        (3, 1, 1, -6), (4, 0, 1, -30), (5, 0, 1, -14)),
}


def _guitar(sc: en.Score, t: float, chords: list, tr: int, level: int,
            vel: int) -> None:
    for bi in range(len(chords)):
        for e, full, ln, dv in _GPAT[level]:
            voicing = _GTR[_chord_at(chords, bi, e)]
            notes = voicing if full else voicing[-3:]
            for i, p in enumerate(notes):
                sc.note(GTR, p + tr, t + bi * BAR + e * E8, ln * E8 * 0.9,
                        vel + dv - i, jt=0, jv=4)


def _bass(sc: en.Score, t: float, rows: list, chords: list, tr: int,
          level: int, vel: int) -> None:
    for bi, row in enumerate(rows):
        n0, n2, n3, n5 = (en.n(x) + tr for x in row.split())
        lv = level
        if lv == 0 and isinstance(chords[bi], tuple):
            lv = 1                              # follow a mid-bar change
        if lv == 0:
            plan = ((0, n0, 6, 0),)
        elif lv == 1:
            plan = ((0, n0, 3, 0), (3, n3, 3, -8))
        elif lv == 2:
            plan = ((0, n0, 3, 0), (3, n3, 2, -8), (5, n5, 1, -4))
        else:
            plan = ((0, n0, 2, 0), (2, n2, 1, -12), (3, n3, 2, -6),
                    (5, n5, 1, -4))
        for e, p, ln, dv in plan:
            sc.note(BAS, p, t + bi * BAR + e * E8, ln * E8 * 0.92, vel + dv,
                    jt=0, jv=3)


def _accordion(sc: en.Score, t: float, chords: list, tr: int, mode: str,
               vel: int, state: dict) -> None:
    prev = state.get("acc")
    for bi in range(len(chords)):
        entry = chords[bi]
        segs = ([(0.0, 1.5, entry[0]), (1.5, 1.5, entry[1])]
                if isinstance(entry, tuple) else [(0.0, 3.0, entry)])
        x = t + bi * BAR
        for off, span, name in segs:
            prev = en.voice_lead([p + tr for p in _GTR[name]], prev, 3,
                                 57 + tr, 77 + tr)
            if mode == "pad":
                for p in prev:
                    sc.note(ACC, p, x + off, span * 0.95, vel, jt=0, jv=3)
            else:                               # "pulse": the bellows shake
                hits = (0.0, 1.5) if span == 3.0 else (0.0,)
                for h in hits:
                    for p in prev:
                        sc.note(ACC, p, x + off + h, 0.9,
                                vel + (6 if off + h == 0.0 else 0),
                                jt=0, jv=3)
        en.cc_curve(sc, ACC, 11, [(x, 88), (x + 1.5, 112), (x + 2.75, 92)],
                    step=0.25)
    state["acc"] = prev


def _tones(name: str, tr: int, lo: int, count: int) -> list:
    pcs = {(p + tr) % 12 for p in _GTR[name]}
    return [p for p in range(lo, lo + 30) if p % 12 in pcs][:count]


def _mandolin(sc: en.Score, t: float, chords: list, tr: int, mode: str,
              vel: int) -> None:
    for bi in range(len(chords)):
        for e in range(6):
            name = _chord_at(chords, bi, e)
            b = t + bi * BAR + e * E8
            if mode == "arp":
                tones = _tones(name, tr, 62 + tr, 4)
                idx = ((0, 1, 2, 3, 2, 1) if bi % 2 == 0
                       else (3, 2, 1, 0, 1, 2))[e]
                sc.note(MAN, tones[idx], b, E8 * 0.95,
                        vel + (8 if e in (0, 3) else 0), jt=0, jv=4)
            elif e in (2, 5):                   # "chop" on the off-beats
                for p in _tones(name, tr, 67 + tr, 3):
                    sc.note(MAN, p, b, 0.3, vel, jt=0, jv=4)


def _hit(sc: en.Score, key: int, beat: float, vel: int) -> None:
    sc.note(KIT, key, beat, 0.25, vel, jt=0, jv=5)


_BODHRAN_2 = {0: (43, 76), 2: (45, 46), 3: (43, 62), 5: (45, 50)}
_BODHRAN_3 = {0: (43, 84), 1: (45, 40), 2: (45, 52), 3: (43, 70),
              4: (45, 40), 5: (45, 56)}


def _perc(sc: en.Score, t: float, level: int, bars: int = 8,
          fill: bool = True) -> None:
    """-1 maracas (the hush) / 0 woodblock put-put / 1 + tambourine /
    2 + hand drum / 3 everything on every eighth / 4 + stamped kick."""
    for bi in range(bars):
        last = fill and bi == bars - 1 and level >= 2
        for e in range(6):
            x = t + bi * BAR + e * E8
            if level == -1:
                mv = (44, 0, 26, 36, 0, 26)[e]
                if mv:
                    _hit(sc, 70, x, mv)
                if e == 0:
                    _hit(sc, 77, x, 36)
                continue
            if level <= 2:
                if e == 0:
                    _hit(sc, 77, x, 50)
                elif e == 3:
                    _hit(sc, 76, x, 44)
            if level >= 1:
                tv = ((68, 0, 0, 58, 0, 0) if level == 1 else
                      (72, 0, 40, 60, 0, 44) if level == 2 else
                      (78, 34, 48, 66, 34, 50))[e]
                if tv:
                    _hit(sc, 54, x, tv)
            if level >= 2:
                if last and e >= 3:
                    _hit(sc, (47, 45, 43)[e - 3], x, (72, 80, 90)[e - 3])
                else:
                    hit = (_BODHRAN_2 if level == 2 else _BODHRAN_3).get(e)
                    if hit:
                        _hit(sc, hit[0], x, hit[1])
            if level >= 4:
                if e == 0:
                    _hit(sc, 36, x, 98)
                elif e == 3:
                    _hit(sc, 37, x, 72)


def _round(sc: en.Score, r: int) -> None:
    cfg, t0 = ROUNDS[r], T_R[r]
    tune, tr = TUNES[cfg["tune"]], cfg["tr"]
    state: dict = {}
    for k, sec in enumerate("AABB"):
        t = t0 + k * PART_LEN
        bars, chords = tune[sec], tune["ch" + sec]
        for ch, octv, vel in cfg["leads"]:
            _lead(sc, ch, t, bars, tr, octv, vel, lift=2 * k)
        for ch, octv, vel in _pp(cfg.get("doubles", []), k):
            _lead(sc, ch, t, bars, tr, octv, vel)
        for ch, octv, vel in cfg.get("counter", []):
            _counter(sc, ch, t, tune["ct" + sec], tr, octv, vel + k)
        if _pp(cfg.get("hymn", False), k):
            material.play_phrase(sc, ACC, t, HYMN_BASE, "ionian", 0,
                                 stretch=HYMN_STRETCH, vel=98, gate=0.96,
                                 jt=0, jv=3)
            en.expr_curve(sc, ACC, [(t, 100), (t + 13.5, 126),
                                    (t + 23.5, 108)], step=0.75)
        g = _pp(cfg.get("gtr"), k)
        if g:
            _guitar(sc, t, chords, tr, g[0], g[1])
        bs = _pp(cfg.get("bass"), k)
        if bs:
            _bass(sc, t, tune["bs" + sec], chords, tr, bs[0], bs[1])
        ac = _pp(cfg.get("acc"), k)
        if ac:
            _accordion(sc, t, chords, tr, ac[0], ac[1], state)
        mn = _pp(cfg.get("man"), k)
        if mn:
            _mandolin(sc, t, chords, tr, mn[0], mn[1])
        _perc(sc, t, _pp(cfg["perc"], k))


# ---------------------------------------------------------------------------
# Movement builders
# ---------------------------------------------------------------------------

def _b_casting_off(sc: en.Score) -> None:
    """I. Eight bars: the engine put-puts, a guitar finds the lilt, the bass
    and the accordion's bellows arrive, the boat whistles twice."""
    sc.cc(MAN, 32, 96, 0.0)                     # program 25 -> mandolin
    chords = ["G", "G", "C", "G", "Em", "C", "D", "D"]
    bass = ["G2 B2 D3 D3", "G2 B2 D3 D3", "C3 E3 G2 B2", "G2 B2 D3 D3",
            "E2 G2 B2 B2", "C3 E3 G2 B2", "D3 A2 D2 F#2", "D3 A2 D2 F#2"]
    _perc(sc, 0.0, 0, bars=6, fill=False)
    _guitar(sc, 0.0, chords[:4], 0, 0, 56)
    _guitar(sc, 12.0, chords[4:], 0, 1, 64)
    _bass(sc, 6.0, bass[2:4], chords[2:4], 0, 0, 62)
    _bass(sc, 12.0, bass[4:], chords[4:], 0, 1, 68)
    _mandolin(sc, 12.0, chords[4:], 0, "arp", 56)
    state: dict = {}
    _accordion(sc, 12.0, chords[4:], 0, "pad", 54, state)
    # the boat's whistle: toot — tooooot, on the dominant
    sc.cc(WHI, 11, 100, 0.0)
    sc.note(WHI, 86, 19.5, 0.8, 70, jt=0, jv=2)
    sc.note(WHI, 86, 21.0, 2.4, 78, jt=0, jv=2)
    en.expr_curve(sc, WHI, [(21.0, 92), (22.5, 124), (23.5, 96)], step=0.25)
    # tambourine shakes the last two bars in
    for bi in (6, 7):
        for e in range(6):
            x = bi * BAR + e * E8
            if bi == 6:
                if e == 0:
                    _hit(sc, 77, x, 50)
                elif e == 3:
                    _hit(sc, 76, x, 44)
                if e in (0, 3):
                    _hit(sc, 54, x, 56)
            else:
                _hit(sc, 54, x, 44 + 8 * e)
                if e in (0, 3):
                    _hit(sc, 43, x, 60 + 6 * e)


def _b_mail_boat(sc: en.Score) -> None:
    """II. The Mail Boat in G: fiddle; whistle; accordion and fiddle."""
    for r in (0, 1, 2):
        _round(sc, r)


def _b_outbound_tide(sc: en.Score) -> None:
    """III. The Outbound Tide in E dorian: mandolin (the hush); fiddle;
    accordion and whistle."""
    for r in (3, 4, 5):
        _round(sc, r)


def _b_rounding_the_point(sc: en.Score) -> None:
    """IV. Four bars on E: the minor third turns major, the seventh arrives,
    the tempo presses (162 -> 168) and a run falls onto the new tonic."""
    t = T_TRANS
    for bi in range(2):
        b = t + bi * BAR
        sc.note(BAS, 40, b, 1.38, 80 + 6 * bi, jt=0, jv=3)
        sc.note(BAS, 40, b + 1.5, 1.38, 74 + 6 * bi, jt=0, jv=3)
    for e, p, ln in ((0, 40, 2), (2, 47, 1), (3, 40, 2), (5, 47, 1)):
        sc.note(BAS, p, t + 6.0 + e * E8, ln * E8 * 0.92, 92, jt=0, jv=3)
    for e, p, ln in ((0, 40, 2), (2, 40, 1), (3, 42, 2), (5, 44, 1)):
        sc.note(BAS, p, t + 9.0 + e * E8, ln * E8 * 0.92, 98, jt=0, jv=3)
    _guitar(sc, t, ["E5"], 0, 1, 62)
    _guitar(sc, t + 3.0, ["E5"], 0, 1, 70)
    _guitar(sc, t + 6.0, ["E"], 0, 2, 80)
    _guitar(sc, t + 9.0, ["E7"], 0, 2, 90)
    for p in (52, 59, 64):
        sc.note(ACC, p, t, 5.8, 70, jt=0, jv=3)
    for p in (59, 64, 68):
        sc.note(ACC, p, t + 6.0, 2.85, 80, jt=0, jv=3)
    for p in (59, 62, 64, 68):
        sc.note(ACC, p, t + 9.0, 2.85, 90, jt=0, jv=3)
    en.expr_curve(sc, ACC, [(t, 72), (t + 6.0, 98), (t + 11.75, 126)],
                  step=0.5)
    # fiddle: an open-string shuffle, then the run down to the leading note
    for bi in range(3):
        dbl = (64, 71) if bi < 2 else (68, 71)
        for e in (0, 2, 3, 5):
            for p in dbl:
                sc.note(FID, p, t + bi * BAR + e * E8,
                        (1.0 if e in (0, 3) else 0.5) * 0.9,
                        66 + 9 * bi + (6 if e in (0, 3) else 0), jt=0, jv=3)
    for i, p in enumerate((76, 74, 73, 71, 69, 68)):
        sc.note(FID, p, t + 9.0 + i * E8, E8 * 0.95, 92 + 3 * i, jt=0, jv=2)
        sc.note(WHI, p + 12, t + 9.0 + i * E8, E8 * 0.88, 82 + 3 * i,
                jt=0, jv=2)
    en.expr_curve(sc, FID, [(t, 86), (t + 9.0, 118), (t + 11.75, 126)],
                  step=0.5)
    sc.cc(WHI, 11, 116, t + 8.5)
    sc.note(FD2, 71, t, 5.8, 68, jt=0, jv=3)
    sc.note(FD2, 71, t + 6.0, 2.85, 78, jt=0, jv=3)
    sc.note(FD2, 74, t + 9.0, 2.85, 88, jt=0, jv=3)
    en.expr_curve(sc, FD2, [(t, 70), (t + 6.0, 100), (t + 11.75, 126)],
                  step=0.5)
    for bi in range(4):
        for e in range(6):
            x = t + bi * BAR + e * E8
            grow = 6 * bi + e
            if bi < 3:
                key, v = _BODHRAN_3[e]
                _hit(sc, key, x, v - 20 + grow)
            else:
                _hit(sc, (47, 47, 45, 45, 43, 43)[e], x, 76 + 6 * e)
            if bi >= 2 or e in (0, 3):
                _hit(sc, 54, x, 46 + grow + (10 if e in (0, 3) else 0))
            if bi >= 2 and e in (0, 3):
                _hit(sc, 36, x, 88 + 4 * bi)


def _b_mail_boat_in_a(sc: en.Score) -> None:
    """V. The Mail Boat a tone higher: fiddle and whistle; then everybody,
    the keeper's hymn riding over the A parts on the accordion."""
    _hit(sc, 49, T_R[6], 92)
    _round(sc, 6)
    _hit(sc, 49, T_R[7], 98)
    _round(sc, 7)


def _stamp(sc: en.Score, b: float, dur: float, vel: int,
           final: bool = False) -> None:
    for p in (76, 81):
        sc.note(FID, p, b, dur, vel, jt=0, jv=2)
    sc.note(WHI, 93, b, dur, vel - 12, jt=0, jv=2)
    for p in (69, 73, 76, 81):
        sc.note(ACC, p, b, dur, vel - 8, jt=0, jv=2)
        sc.note(MAN, p, b, dur, vel - 4, jt=0, jv=2)
    for i, p in enumerate(_GTR["G"]):
        sc.note(GTR, p + 2, b, dur, vel - 6 - i, jt=0, jv=2)
    sc.note(BAS, 33 if final else 45, b, dur, vel, jt=0, jv=2)
    for p in (61, 69):
        sc.note(FD2, p, b, dur, vel - 10, jt=0, jv=2)
    _hit(sc, 36, b, 114 if final else 102)
    _hit(sc, 39, b, 100)
    _hit(sc, 54, b, 96)
    if final:
        _hit(sc, 49, b, 106)


def _b_stamped_home(sc: en.Score) -> None:
    """VI. The tag (the tune's last two bars, twice, the second time running
    up the A chord), two stamps, and the tonic stamped and held."""
    t, tr = T_CODA, 2
    tune = TUNES["J1"]
    run_up = _abc(["G2 B d2 f"], "F")[0]
    tag = [tune["B"][6], tune["B"][7], tune["B"][6], run_up]
    for ch, octv, vel in ((FID, 0, 110), (WHI, 1, 90), (MAN, 0, 116),
                          (ACC, 0, 100)):
        _lead(sc, ch, t, tag, tr, octv, vel, lift=4)
    chords = ["D", "G", "D", ("G", "D")]
    _counter(sc, FD2, t, [tune["ctB"][6], tune["ctB"][7], tune["ctB"][6],
                          ("B3", "A3")], tr, 0, 92)
    _guitar(sc, t, chords, tr, 2, 92)
    _bass(sc, t, ["D3 A2 D2 F#2", "G2 B2 D3 D2", "D3 A2 D2 F#2",
                  "G2 B2 D3 F#2"], chords, tr, 3, 100)
    _perc(sc, t, 4, bars=3, fill=False)
    for e in range(6):
        x = t + 9.0 + e * E8
        _hit(sc, (47, 47, 45, 45, 43, 43)[e], x, 80 + 6 * e)
        _hit(sc, 54, x, 70 + 5 * e)
        if e in (0, 3):
            _hit(sc, 36, x, 100)
    for ch in _BREATHING:
        sc.cc(ch, 11, 126, t + 11.75)
    _stamp(sc, t + 12.0, 0.7, 112)
    _stamp(sc, t + 13.5, 0.7, 114)
    _stamp(sc, T_STAMP, END - T_STAMP, 120, final=True)


BUILDERS = [_b_casting_off, _b_mail_boat, _b_outbound_tide,
            _b_rounding_the_point, _b_mail_boat_in_a, _b_stamped_home]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _tick(beat: float) -> int:
    return int(round(beat * PPQ))


def _in_round(ns: dict, ch: int, t0: float, t1: float) -> list:
    """[(tick relative to t0, pitch, duration ticks)] for onsets in [t0, t1)."""
    return [(_tick(on - t0), p, _tick(off - on))
            for on, off, p, _v in ns.get(ch, []) if t0 <= on < t1]


def _tune_seq(key: str) -> list:
    """The AABB round as [(tick, pitch)] at concert G / E pitch."""
    tune = TUNES[key]
    out = []
    for k, sec in enumerate("AABB"):
        for bi, bar in enumerate(tune[sec]):
            for p, pos, _ln in bar:
                out.append((_tick(k * PART_LEN + bi * BAR + pos * E8), p))
    return out


def _states_tune(notes: list, want: list, tr: int) -> bool:
    """True when the notes are the tune, rhythm exact, at any octave."""
    if len(notes) != len(want):
        return False
    shift = notes[0][1] - (want[0][1] + tr)
    if shift % 12:
        return False
    return all(tick == w_tick and p == w_p + tr + shift
               for (tick, p, _d), (w_tick, w_p) in zip(notes, want))


def _detected_leads(ns: dict, r: int) -> set:
    cfg, t0 = ROUNDS[r], T_R[r]
    want = _tune_seq(cfg["tune"])
    return {ch for ch in ns if ch != KIT and _states_tune(
        _in_round(ns, ch, t0, t0 + ROUND), want, cfg["tr"])}


def _sounding(ns: dict, ch: int, beat: float) -> list:
    return [p for on, off, p, _v in ns.get(ch, [])
            if on <= beat + 1e-9 and off >= beat + 0.05]


def _o_grid(sc) -> list:
    fails = []
    if sorted(sc.timesigs) != [(0.0, 6, 8)]:
        fails.append(f"time signatures {sorted(sc.timesigs)}, want one 6/8")
    if sorted(sc.tempos)[0] != (0.0, 162.0):
        fails.append("the set must start at tempo 162 (dotted quarter 108)")
    lattice = PPQ // 2
    for ch in sorted(sc.events):
        off = sorted(tick for tick, _p, d in sc.events[ch]
                     if (d[0] & 0xF0) == 0x90 and d[2] > 0 and tick % lattice)
        if off:
            fails.append(f"ch{ch}: {len(off)} onset(s) off the eighth-note "
                         f"lattice, first at beat {off[0] / PPQ:.3f}")
    return fails


def _o_aabb(ns) -> list:
    fails = []
    for r in range(len(ROUNDS)):
        t0 = T_R[r]
        leads = sorted(_detected_leads(ns, r))
        if not leads:
            fails.append(f"round {r + 1}: nobody states the tune")
        for ch in leads:
            parts = [_in_round(ns, ch, t0 + k * PART_LEN,
                               t0 + (k + 1) * PART_LEN) for k in range(4)]
            if min(len(p) for p in parts) < 30:
                fails.append(f"round {r + 1} ch{ch}: a part has under 30 "
                             f"notes — not a jig strain")
            if parts[0] != parts[1]:
                fails.append(f"round {r + 1} ch{ch}: A repeat is not exact")
            if parts[2] != parts[3]:
                fails.append(f"round {r + 1} ch{ch}: B repeat is not exact")
            if [p for _t, p, _d in parts[0]] == [p for _t, p, _d in parts[2]]:
                fails.append(f"round {r + 1} ch{ch}: B is only A again")
    return fails


def _o_keys(sc, ns) -> list:
    fails = []
    if sorted(sc.keysigs) != [(0.0, 1, 0), (312.0, 2, 0), (612.0, 3, 0)]:
        fails.append(f"key signatures {sorted(sc.keysigs)} are not "
                     f"G / E dorian (2 sharps) / A")
    want_plan = [("J1", 0)] * 3 + [("J2", 0)] * 3 + [("J1", 2)] * 2
    if [(c["tune"], c["tr"]) for c in ROUNDS] != want_plan:
        fails.append("the set is not G jig x3, E dorian jig x3, A jig x2")
    for r, cfg in enumerate(ROUNDS):
        t0 = T_R[r]
        tune = TUNES[cfg["tune"]]
        tonic = (tune["tonic"] + cfg["tr"]) % 12
        allowed = {(tonic + s) % 12 for s in en.MODES[tune["mode"]]}
        for ch in sorted(ns):
            if ch == KIT:
                continue
            stray = sorted({p % 12 for _t, p, _d in
                            _in_round(ns, ch, t0, t0 + ROUND)} - allowed)
            if stray:
                fails.append(f"round {r + 1} ch{ch}: pitch classes {stray} "
                             f"outside {tune['mode']} on pc {tonic}")
        down = [p for on, _off, p, _v in ns.get(BAS, []) if on == t0]
        if r != 0 and (not down or down[0] % 12 != tonic):
            fails.append(f"round {r + 1}: the bass does not open on the "
                         f"tonic (pc {tonic})")
    # the second jig is a different tune and shows its dorian sixth
    j2 = {p % 12 for _t, p in _tune_seq("J2")}
    if 1 not in j2 or 7 not in j2 or 0 in j2:
        fails.append("jig 2 must feature C sharp and G natural, no C natural")
    if ([p % 12 for _t, p in _tune_seq("J1")]
            == [(p + 3) % 12 for _t, p in _tune_seq("J2")]):
        fails.append("jig 2 is jig 1 transposed, not a second tune")
    # the last rounds are round 1 a whole tone up, note for note
    first = _in_round(ns, FID, T_R[0], T_R[0] + ROUND)
    for r in (6, 7):
        again = _in_round(ns, FID, T_R[r], T_R[r] + ROUND)
        if again != [(t, p + 2, d) for t, p, d in first]:
            fails.append(f"round {r + 1}: the fiddle is not round 1's tune "
                         f"exactly a tone higher")
    return fails


def _o_beam(sc, ns) -> list:
    fails = []
    fid = material.note_ons(sc, FID)
    if not fid or fid[0][0] != T_R[0]:
        fails.append("the fiddle's first note must open jig 1 at beat 24")
    for r, cfg in enumerate(ROUNDS):
        if cfg["tune"] != "J1":
            continue
        for ch, _octv, _vel in cfg["leads"]:
            starts = set(material.beam_statements(sc, ch))
            for k in (0, 1):
                for bar in (0, 4):
                    b = T_R[r] + k * PART_LEN + bar * BAR
                    if b not in starts:
                        fails.append(f"round {r + 1} ch{ch}: no BEAM at "
                                     f"beat {b} (A{k + 1} bar {bar + 1})")
    return fails


def _o_handoff(ns) -> list:
    fails = []
    programs = {ch: prog for ch, _n, prog, _v, _p, _r in PART.CHANNELS}
    seen: list = []
    for r, cfg in enumerate(ROUNDS):
        got = _detected_leads(ns, r)
        want = {ch for ch, _o, _v in cfg["leads"]}
        if got != want:
            fails.append(f"round {r + 1}: tune stated by {sorted(got)}, "
                         f"planned {sorted(want)}")
        if seen and got == seen[-1]:
            fails.append(f"round {r + 1}: same lead(s) as the round before")
        seen.append(got)
    everyone = set().union(*seen) if seen else set()
    if len(everyone) < 3 or len({programs[ch] for ch in everyone}) < 3:
        fails.append(f"only channels {sorted(everyone)} ever lead; need "
                     f"three different instruments")
    if seen and len(seen[-1]) != max(len(s) for s in seen):
        fails.append("the last round should have the most leads")
    return fails


def _o_thickens(sc) -> list:
    fails = []
    en_r = [material.energy(sc, t, t + ROUND) for t in T_R]
    voices = [len(material.active_channels(sc, t, t + ROUND)) for t in T_R]
    for lo, hi in ((0, 3), (3, 6), (6, 8)):
        for r in range(lo + 1, hi):
            if en_r[r] <= en_r[r - 1] * 1.05:
                fails.append(f"round {r + 1} ({en_r[r]:.0f}/beat) is not "
                             f"thicker than round {r} ({en_r[r - 1]:.0f})")
            if voices[r] < voices[r - 1]:
                fails.append(f"round {r + 1} has fewer voices "
                             f"({voices[r]}) than round {r}")
    if en_r[7] < max(en_r):
        fails.append("the last round is not the biggest")
    if en_r[3] > 0.6 * en_r[2] or en_r[3] > 0.6 * en_r[4]:
        fails.append(f"round 4 ({en_r[3]:.0f}/beat) is not a hush against "
                     f"rounds 3 ({en_r[2]:.0f}) and 5 ({en_r[4]:.0f})")
    intro = material.energy(sc, 0.0, 24.0)
    if intro >= en_r[1]:
        fails.append("the introduction is as heavy as a full round")
    return fails


def _o_counterpoint(ns) -> list:
    fails = []
    for r, (cch, lch) in sorted(COUNTER_PAIRS.items()):
        checked = 0
        for bar in range(32):
            for half in (0.0, 1.5):
                beat = T_R[r] + bar * BAR + half
                cp, lp = _sounding(ns, cch, beat), _sounding(ns, lch, beat)
                if len(cp) != 1 or len(lp) != 1:
                    fails.append(f"round {r + 1} beat {beat}: counter "
                                 f"{cp} / lead {lp} — want one note each")
                    continue
                checked += 1
                if abs(cp[0] - lp[0]) % 12 not in material.CONSONANT:
                    fails.append(f"round {r + 1} beat {beat}: counter "
                                 f"{cp[0]} against lead {lp[0]} is dissonant")
        if checked < 64:
            fails.append(f"round {r + 1}: only {checked}/64 pulses checked")
    return fails[:10]


def _o_accel_stamp(sc, ns) -> list:
    fails = []
    tempos = sorted(sc.tempos)
    bpms = [bpm for _b, bpm in tempos]
    if bpms != sorted(bpms) or len(set(bpms)) != len(bpms):
        fails.append("the tempo must only ever press forward")
    if any(not T_TRANS <= b < T_R[6] for b, _bpm in tempos[1:]):
        fails.append("the accelerando must sit inside 'Rounding the Point'")
    if not 1.02 <= bpms[-1] / bpms[0] <= 1.08:
        fails.append(f"accelerando of {bpms[-1] / bpms[0]:.3f}x is not "
                     f"'slight' (want 2-8 percent)")
    struck = {ch for ch in ns if any(on == T_STAMP for on, _o, _p, _v
                                     in ns[ch])}
    if len(struck - {KIT}) < 6 or KIT not in struck:
        fails.append(f"the last stamp is struck by {sorted(struck)}; want "
                     f"the kit and six voices")
    for ch in sorted(struck - {KIT}):
        for on, off, p, _v in ns[ch]:
            if on == T_STAMP and p % 12 not in (9, 1, 4):
                fails.append(f"ch{ch} stamps pitch {p}, not in the A chord")
            if on == T_STAMP and off != END:
                fails.append(f"ch{ch} stamp ends at {off}, not at END")
    low = [p for on, _o, p, _v in ns.get(BAS, []) if on == T_STAMP]
    if not low or low[0] % 12 != 9:
        fails.append("the bass does not stamp the tonic A")
    if not any(on == T_STAMP and p == 36 for on, _o, p, _v in ns.get(KIT, [])):
        fails.append("no kick under the last stamp")
    late = [(ch, on) for ch in ns for on, _o, _p, _v in ns[ch]
            if on > T_STAMP]
    if late:
        fails.append(f"notes after the stamp: {late[:3]}")
    return fails


def _o_hymn(sc) -> list:
    fails = []
    found = material.phrase_statements(sc, ACC, "ionian", 0)
    for b in (T_R[7], T_R[7] + PART_LEN):
        if not any(start == b and abs(stretch - HYMN_STRETCH) < 0.01
                   and base == HYMN_BASE for start, stretch, base in found):
            fails.append(f"no hymn phrase 1 on the accordion at beat {b} "
                         f"(found {found})")
    return fails


def _o_bass(ns) -> list:
    fails = []
    for r, cfg in enumerate(ROUNDS):
        tune, tr = TUNES[cfg["tune"]], cfg["tr"]
        notes = _in_round(ns, BAS, T_R[r], T_R[r] + ROUND)
        by_tick = {t: p for t, p, _d in notes}
        roots = 0
        for k, sec in enumerate("AABB"):
            for bi in range(8):
                tick = _tick(k * PART_LEN + bi * BAR)
                if tick not in by_tick:
                    continue                    # the bass may sit out a part
                root = (_GTR[_chord_at(tune["ch" + sec], bi, 0)][0] + tr) % 12
                roots += 1
                if by_tick[tick] % 12 != root:
                    fails.append(f"round {r + 1} part {k + 1} bar {bi + 1}: "
                                 f"bass {by_tick[tick]} is not the root")
        if roots < 24:
            fails.append(f"round {r + 1}: bass on only {roots} bar lines")
        if len(notes) >= 120:                   # a walking round
            if len({p % 12 for _t, p, _d in notes}) < 6:
                fails.append(f"round {r + 1}: the walking bass uses under "
                             f"six pitch classes")
            lead_ch = cfg["leads"][0][0]
            lead = {t: p % 12 for t, p, _d in
                    _in_round(ns, lead_ch, T_R[r], T_R[r] + ROUND)}
            same = sum(1 for t, p, _d in notes if lead.get(t) == p % 12)
            if same > 0.5 * len(notes):
                fails.append(f"round {r + 1}: the bass shadows the tune "
                             f"({same}/{len(notes)} onsets in unison)")
    return fails[:10]


def oracles(sc, info, spans) -> list:
    results = material.album_oracles(sys.modules[__name__], sc)
    ns = {ch: material.note_spans(sc, ch) for ch in sorted(sc.events)}
    results.append(("t04_jig_grid", _o_grid(sc)))
    results.append(("t04_aabb_repeats_exact", _o_aabb(ns)))
    results.append(("t04_two_jigs_then_a_tone_up", _o_keys(sc, ns)))
    results.append(("t04_beam_opens_the_jig", _o_beam(sc, ns)))
    results.append(("t04_tune_handed_round", _o_handoff(ns)))
    results.append(("t04_rounds_thicken", _o_thickens(sc)))
    results.append(("t04_counterpoint_on_the_pulse", _o_counterpoint(ns)))
    results.append(("t04_accelerando_and_stamp", _o_accel_stamp(sc, ns)))
    results.append(("t04_hymn_descant", _o_hymn(sc)))
    results.append(("t04_bass_roots_and_walk", _o_bass(ns)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — thresholds set from the measured render.
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list:
    def level(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    rd = [level(t + BAR, t + ROUND - BAR) for t in T_R]
    fails_hush, fails_crown, fails_stamp = [], [], []
    if rd[7] - rd[3] < 6.0:
        fails_hush.append(f"last round {rd[7]:.1f} dB vs the mandolin hush "
                          f"{rd[3]:.1f} dB: under 6 dB apart")
    if rd[7] < max(rd):
        fails_crown.append(f"the last round ({rd[7]:.1f} dB) is not the "
                           f"loudest round ({[round(x, 1) for x in rd]})")
    if rd[7] < rd[2]:
        fails_crown.append("the second peak (round 8) is below the first "
                           "(round 3)")
    stamp = level(T_STAMP, T_STAMP + 1.5)
    if stamp < rd[7] - 3.0:
        fails_stamp.append(f"the last stamp ({stamp:.1f} dB) does not land "
                           f"at the level of the last round ({rd[7]:.1f})")
    return [("t04_hush_vs_peak", fails_hush),
            ("t04_last_round_crowns", fails_crown),
            ("t04_stamp_lands", fails_stamp)]
