"""t08_equinox_gale.py — Lantern Year, track 8: "Equinox Gale".

September, the equinox gale: an orchestral scherzo in C aeolian, 3/4 felt
one-in-a-bar at quarter = 174, with the raised leading tone (B natural) only
where the harmony really cadences.

Form (bars of 3/4):

  I.   Scherzo         88 bars   intro (the BEAM in the basses, answered as a
                                 trumpet call and a horn call) - theme (x2) -
                                 woodwind episode in E flat - storm build over
                                 the BEAM in the basses - theme tutti - codetta
  II.  Trio            64 bars   C major, quarter = 144: a pastoral oboe tune
                                 over harp and pizzicato, then the HORNS quote
                                 the keeper's HYMN (phrases 1-2, later phrase 4)
                                 one note to the bar, with verified
                                 counter-melodies
  III. Scherzo da capo 72 bars   the scherzo again, bigger in every statement
  IV.  Coda            48 bars   180 -> 186 -> 192 -> 200: the theme's head in
                                 stretto between strings and brass, BEAM calls
                                 over a tonic pedal, a chain of hemiolas, home

The scherzo theme's first five notes ARE the BEAM (C G Ab G C'), so the cell
binds the tune itself; every phrase closes on a hemiola (three half-note
strokes across two bars) that lands on a V-i cadence.
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 8
TITLE = "Equinox Gale"
FILE = "08 - Equinox Gale.mid"
SEED = 20261208
COMMENT = ("Equinox Gale: the September night of Lantern Year. An orchestral "
           "scherzo in C minor, one-in-a-bar, whose theme opens with the "
           "album's BEAM cell; a calmer C major trio in which the horns quote "
           "the keeper's hymn; the scherzo again, bigger; and a coda that "
           "presses the tempo up through a chain of hemiolas.")

BAR = 3.0
(VN, SOLO, VA, VC, CB, TREM, TPT, HN, TBN, DR, TUBA, PICC, OB, CL, BSN,
 TIMP) = range(16)

# ---------------------------------------------------------------------------
# Layout (beats; every section starts on a bar line)
# ---------------------------------------------------------------------------
S1 = 0.0
S1_A1, S1_A2, S1_B, S1_A3, S1_CDT = (S1 + BAR * k for k in (8, 24, 40, 64, 80))
TRIO = S1 + BAR * 88                      # 264
T_A, T_H1, T_A2, T_H2 = (TRIO + BAR * k for k in (4, 20, 36, 52))
S2 = TRIO + BAR * 64                      # 456
S2_A1, S2_B, S2_A2, S2_CDT = (S2 + BAR * k for k in (8, 24, 48, 64))
CODA = S2 + BAR * 72                      # 672
C2, C3, C4 = (CODA + BAR * k for k in (16, 32, 40))
END = CODA + BAR * 48                     # 816

SCHERZO_TEMPO = 174.0
TRIO_TEMPO = 144.0

VOL = {VN: 118, SOLO: 100, VA: 90, VC: 98, CB: 106, TREM: 82, TPT: 104,
       HN: 102, TBN: 98, DR: 100, TUBA: 98, PICC: 92, OB: 100, CL: 94,
       BSN: 94, TIMP: 102}

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Scherzo", S1, TRIO),
               ("II. Trio", TRIO, S2),
               ("III. Scherzo da capo", S2, CODA),
               ("IV. Coda", CODA, END)],
    tempo_map=[(0.0, SCHERZO_TEMPO), (TRIO, TRIO_TEMPO), (S2, SCHERZO_TEMPO),
               (CODA, 180.0), (C2, 186.0), (C3, 192.0), (C4, 200.0)],
    time_signatures=[(0.0, 3, 4)],
    keysigs=[(0.0, -3, 1), (TRIO, 0, 0), (S2, -3, 1)],
    channels=[
        (VN, "Violins", 48, VOL[VN], 64, 50),
        (SOLO, "Solo violin", 40, VOL[SOLO], 64, 48),
        (VA, "Violas and seconds", 49, VOL[VA], 74, 52),
        (VC, "Cellos", 42, VOL[VC], 78, 48),
        (CB, "Contrabasses", 43, VOL[CB], 64, 42),
        (TREM, "Tremolo / pizzicato strings", 44, VOL[TREM], 48, 55),
        (TPT, "Trumpets", 56, VOL[TPT], 64, 52),
        (HN, "Horns", 60, VOL[HN], 42, 60),
        (TBN, "Trombones / harp", 57, VOL[TBN], 82, 52),
        (DR, "Orchestral percussion", 0, VOL[DR], 64, 45),
        (TUBA, "Tuba", 58, VOL[TUBA], 64, 46),
        (PICC, "Piccolo / flute", 72, VOL[PICC], 64, 50),
        (OB, "Oboes", 68, VOL[OB], 48, 48),
        (CL, "Clarinets", 71, VOL[CL], 72, 48),
        (BSN, "Bassoons", 70, VOL[BSN], 64, 46),
        (TIMP, "Timpani", 47, VOL[TIMP], 64, 50),
    ],
    program_changes=[
        (TREM, S1_B - 0.5, 45), (TREM, S1_B + 48 - 0.5, 44),
        (TREM, TRIO - 0.5, 45), (PICC, TRIO - 0.5, 73), (TBN, TRIO - 0.5, 46),
        (TREM, S2 - 0.5, 44), (PICC, S2 - 0.5, 72), (TBN, S2 - 0.5, 57),
        (TREM, S2_B - 0.5, 45), (TREM, S2_B + 48 - 0.5, 44),
    ],
    extra_markers=[
        (S1_A1, "Scherzo theme"), (S1_B, "Episode in E flat"),
        (S1_A3, "Theme, tutti"), (T_H1, "The horns quote the keeper's hymn"),
        (T_H2, "Hymn, cadence home"), (S2_A2, "Theme, full orchestra"),
        (C3, "Hemiola chain"),
    ],
)

BEAM_CHANNELS = {VN, TPT, HN, CB}
PROGRAM_WHITELIST = {48, 40, 49, 42, 43, 44, 45, 56, 60, 57, 46, 58, 72, 73,
                     68, 71, 70, 47}
# The synth's pan stage costs a panned voice 1.5-5 dB in a mono fold-down
# (measured per stem), so everything that carries the tune, the calls or
# the pulse sits in the centre; only the harmony voices are spread.
CENTERED_CHANNELS = {VN, SOLO, CB, TPT, DR, TUBA, PICC, BSN, TIMP}
NOTE_RANGES = {
    VN: (55, 91), SOLO: (55, 91), VA: (48, 79), VC: (36, 77), CB: (28, 60),
    TREM: (36, 84), TPT: (55, 84), HN: (41, 77), TBN: (34, 96),
    TUBA: (31, 58), PICC: (60, 101), OB: (58, 89), CL: (50, 89),
    BSN: (34, 72), TIMP: (40, 53),
}
GAP_WHITELIST: list = []
BEND_EXEMPT: set = set()
DURATION_WINDOW = (289.0, 296.0)
BOUNDS_WHITELIST: list = []

# ---------------------------------------------------------------------------
# Notation helpers
# ---------------------------------------------------------------------------

PCS = {
    "Cm": (0, 3, 7), "Fm": (5, 8, 0), "Fm7": (5, 8, 0, 3), "Eb": (3, 7, 10),
    "Ab": (8, 0, 3), "Bb": (10, 2, 5), "Bb7": (10, 2, 5, 8),
    "G": (7, 11, 2), "G7": (7, 11, 2, 5), "Do": (2, 5, 8, 0),
    "C": (0, 4, 7), "F": (5, 9, 0), "Am": (9, 0, 4), "Dm": (2, 5, 9),
    "Dm7": (2, 5, 9, 0),
}


def N(text):
    """'C5 1 G5 1 Ab5 .5' -> [(name, beats)]; 'r' is a rest."""
    tok = text.split()
    return [(tok[i], float(tok[i + 1])) for i in range(0, len(tok), 2)]


def H(text):
    """A hemiola pair: six beats written as three half-note strokes."""
    return ("H", N(text))


def E(*bars):
    """Bars -> [(offset, notes, is_hemiola)] laid end to end."""
    out, off = [], 0.0
    for bar in bars:
        hem = isinstance(bar, tuple)
        notes = bar[1] if hem else bar
        out.append((off, notes, hem))
        off += sum(d for _n, d in notes)
    return out


def S(*bars):
    """Harmony -> [(offset, dur, chord, bass, is_hemiola)]."""
    out, off = [], 0.0
    for bar in bars:
        if bar[0] == "H":
            for chord, bass in bar[1]:
                out.append((off, 2.0, chord, bass, True))
                off += 2.0
        else:
            out.append((off, BAR, bar[0], bar[1], False))
            off += BAR
    return out


def low_pitch(name, lo):
    """The lowest pitch >= lo carrying the pitch class of the note name."""
    pc = en.n(name + "4") % 12
    return lo + (pc - lo) % 12


def timp_pitch(chord):
    """Three drums: F2, G2, C3 — the root if tuned, else a chord tone."""
    table = {0: 48, 7: 43, 5: 41}
    pcs = PCS[chord]
    if pcs[0] in table:
        return table[pcs[0]]
    for pc in (0, 7, 5):
        if pc in pcs:
            return table[pc]
    return 48


def _on_bar(t):
    return abs(t / BAR - round(t / BAR)) < 1e-6


def seq(sc, ch, t0, notes, vel, tr=0, gate=0.86, jt=2, jv=3, acc=7):
    """Play a sequential (name, beats) list; downbeats are accented."""
    t = t0
    for name, dur in notes:
        if name != "r":
            v = vel
            if _on_bar(t):
                v += acc
            elif dur <= 0.5:
                v -= 5
            g = gate if dur < 1.5 else max(gate, 0.94)
            sc.note(ch, en.n(name) + tr, t, dur * g, v, jt=jt, jv=jv)
        t += dur
    return t


def part(sc, ch, t0, entries, vel, tr=0, lo=0.0, hi=1e9, gate=0.86,
         acc=7):
    """Play E() entries whose offset is in [lo, hi); hemiolas are tick-exact
    and every stroke of one is accented."""
    for off, notes, hem in entries:
        if lo - 1e-9 <= off < hi:
            if hem:
                seq(sc, ch, t0 + off, notes, vel + acc, tr=tr, gate=gate,
                    jt=0, acc=0)
            else:
                seq(sc, ch, t0 + off, notes, vel, tr=tr, gate=gate, acc=acc)


# ---------------------------------------------------------------------------
# The scherzo material
# ---------------------------------------------------------------------------

HEM_CAD = ("H", [("Ab", "Ab"), ("Do", "F"), ("G", "G")])

# The theme: its head (bar 1 into bar 2) is the BEAM, C G Ab G C'; bars 5-6
# answer with the BEAM on E flat.  Bars 9-11 are the gale itself; bar 12 a
# dominant that the hemiola (13-14) deceives and then closes.
MEL_A = E(
    N("C5 1 G5 1 Ab5 .5 G5 .5"), N("C6 2 G5 1"),
    N("Ab5 1 F5 1 G5 .5 F5 .5"), N("Eb5 2 C5 1"),
    N("Eb5 1 Bb5 1 C6 .5 Bb5 .5"), N("Eb6 2 Bb5 1"),
    N("C6 1 Ab5 1 Bb5 .5 Ab5 .5"), N("G5 1 B5 1 D6 1"),
    N("Eb6 .5 D6 .5 C6 .5 Bb5 .5 Ab5 .5 G5 .5"),
    N("F5 .5 Eb5 .5 D5 .5 C5 .5 Bb4 .5 G4 .5"),
    N("Ab4 .5 C5 .5 Eb5 .5 F5 .5 Ab5 .5 C6 .5"), N("D6 1 B5 1 G5 1"),
    H("C6 2 D6 2 B5 2"), N("C6 1 G5 1 Eb5 1"), N("C5 2 r 1"))

A_SEGS = S(("Cm", "C"), ("Cm", "C"), ("Fm", "F"), ("Cm", "Eb"),
           ("Eb", "Eb"), ("Eb", "Eb"), ("Ab", "Ab"), ("G", "G"),
           ("Cm", "C"), ("Fm", "Ab"), ("Fm7", "F"), ("G", "G"),
           HEM_CAD, ("Cm", "C"), ("Cm", "C"))

A_BASS = E(
    N("C3 1 r 1 G2 1"), N("C3 1 r 1 Eb3 1"), N("F3 1 r 1 C3 1"),
    N("Eb3 1 r 1 D3 1"), N("Eb3 1 r 1 Bb2 1"), N("Eb3 1 r 1 G3 1"),
    N("Ab3 1 r 1 Ab2 1"), N("G2 1 B2 1 D3 1"), N("C3 1 r 1 Bb2 1"),
    N("Ab2 1 r 1 G2 1"), N("F2 1 Ab2 1 F2 1"), N("G2 1 D3 1 G2 1"),
    H("Ab2 2 F2 2 G2 2"), N("C3 1 r 1 G2 1"), N("C2 1 r 1 G2 1"))

# The horns' broad counter-line: one note to the bar against the busy tune.
HORN_A = E(
    N("C4 3"), N("Eb4 3"), N("F4 3"), N("G4 3"), N("G4 3"), N("Bb4 3"),
    N("C5 3"), N("B4 3"), N("C5 3"), N("C5 3"), N("Ab4 3"), N("G4 3"),
    H("Ab4 2 Ab4 2 G4 2"), N("G4 3"), N("C4 2 r 1"))

TPT_A = [
    (3.0, N("G4 1 G4 .5 G4 .5 C5 1"), False),
    (9.0, N("G4 1 G4 .5 G4 .5 G4 1"), False),
    (15.0, N("Bb4 1 Bb4 .5 Bb4 .5 Eb5 1"), False),
    (21.0, N("D5 1 D5 .5 D5 .5 D5 1"), False),
    (33.0, N("D5 1 D5 .5 D5 .5 D5 1"), False),
    (36.0, N("Eb5 2 F5 2 D5 2"), True),
    (42.0, N("G5 1 Eb5 1 C5 1"), False),
    (45.0, N("G4 2"), False),
]
# At full stretch the trumpets carry the theme's head (the BEAM) themselves.
TPT_A5 = [
    (0.0, N("C4 1 G4 1 Ab4 .5 G4 .5 C5 2"), False),
    (9.0, N("G4 1 G4 .5 G4 .5 G4 1"), False),
    (12.0, N("Eb4 1 Bb4 1 C5 .5 Bb4 .5 Eb5 2"), False),
] + TPT_A[3:]

# The episode: a lilting woodwind tune in the relative major.
MEL_B = E(
    N("G5 1 Bb5 .5 Ab5 .5 G5 1"), N("Eb5 2 G5 1"),
    N("Ab5 1 C6 .5 Bb5 .5 Ab5 1"), N("F5 2 Bb5 1"),
    N("Bb5 1 Eb6 .5 D6 .5 C6 1"), N("C6 2 Ab5 1"),
    N("Ab5 1 G5 .5 F5 .5 D5 1"), N("Eb5 3"))
MEL_B2 = MEL_B[:6] + [(18.0, N("Ab5 1 G5 .5 F5 .5 Eb5 1"), False),
                      (21.0, N("D5 3"), False)]
CL_B = E(
    N("Eb5 1 G5 .5 F5 .5 Eb5 1"), N("C5 2 Eb5 1"),
    N("C5 1 Eb5 .5 D5 .5 C5 1"), N("D5 2 F5 1"),
    N("G5 1 C6 .5 Bb5 .5 Ab5 1"), N("Ab5 2 Eb5 1"),
    N("F5 1 Eb5 .5 D5 .5 Bb4 1"), N("G4 3"))
CL_B2 = CL_B[:6] + [(18.0, N("F5 1 Eb5 .5 D5 .5 C5 1"), False),
                    (21.0, N("B4 3"), False)]
B1_CH = [("Eb", "Eb"), ("Cm", "C"), ("Ab", "Ab"), ("Bb", "Bb"),
         ("Eb", "G"), ("Ab", "Ab"), ("Bb7", "Bb"), ("Eb", "Eb")]
B1B_CH = B1_CH[:6] + [("Fm", "F"), ("G", "G")]
VN_B2 = E(N("Bb4 3"), N("C5 3"), N("Eb5 3"), N("D5 3"), N("Eb5 3"),
          N("Eb5 3"), N("F5 3"), N("D5 3"))

# The storm build: the BEAM in the basses, one note to the bar.
B2_SEGS = S(("Cm", "C"), ("Cm", "G"), ("Ab", "Ab"), ("G", "G"),
            ("Cm", "C"), ("Ab", "Ab"),
            ("H", [("Fm", "F"), ("Do", "D"), ("G", "G")]))
B2_BASS = E(N("C2 3"), N("G2 3"), N("Ab2 3"), N("G2 3"), N("C3 3"),
            N("Ab2 3"), H("F2 2 D2 2 G2 2"))
B2_MEL = E(
    N("C5 .5 D5 .5 Eb5 .5 F5 .5 G5 .5 Ab5 .5"),
    N("G5 .5 Ab5 .5 Bb5 .5 C6 .5 D6 .5 Eb6 .5"),
    N("Eb6 .5 C6 .5 Ab5 .5 Eb6 .5 C6 .5 Ab5 .5"),
    N("D6 .5 B5 .5 G5 .5 D6 .5 B5 .5 G5 .5"),
    N("Eb6 1 C6 1 G5 1"), N("Ab5 1 C6 1 Eb6 1"), H("F6 2 D6 2 B5 2"))
B2_TPT = [
    (6.0, N("C5 1 C5 .5 C5 .5 C5 1"), False),
    (9.0, N("D5 1 D5 .5 D5 .5 D5 1"), False),
    (12.0, N("Eb5 3"), False), (15.0, N("Eb5 3"), False),
    (18.0, N("C5 2 D5 2 D5 2"), True),
]


def accomp(sc, t0, segs, lv, lo=0.0, va=True, trem=True, horn=False,
           low_brass=True, lb_skip=(), timp=True, drums=True,
           last_trim=True):
    """The orchestral engine room under a harmony: staccato inner strings,
    tremolo, low-brass stabs, timpani and percussion.  In a hemiola
    segment every part strikes the segment start and nothing else."""
    base = min(100, 62 + 5 * lv)
    pv = pt = ph = pb = None
    segs = [s for s in segs if s[0] >= lo - 1e-9]
    for i, (rt, dur, chord, bass, hem) in enumerate(segs):
        t = t0 + rt
        pcs = list(PCS[chord])
        bar_i = int(round(rt / BAR))
        jt = 0 if hem else 2
        if va:
            pv = en.voice_lead(pcs, pv, 3, 55, 72)
            if hem:
                for p in pv:
                    sc.note(VA, p, t, 1.6, base + 10, jt=0, jv=3)
            elif lv >= 3:
                for k in range(6):
                    for p in pv:
                        sc.note(VA, p, t + 0.5 * k, 0.3,
                                base + (8 if k == 0 else -6), jt=2, jv=3)
            else:
                for k in range(3):
                    for p in pv:
                        sc.note(VA, p, t + k, 0.5,
                                base + (8 if k == 0 else -6), jt=2, jv=3)
        if trem:
            pt = en.voice_lead(pcs, pt, 3, 60, 79)
            d = dur - (1.0 if last_trim and i == len(segs) - 1 else 0.06)
            for p in pt:
                sc.note(TREM, p, t, d, base - 6, jt=jt, jv=3)
        if horn and lv >= 2:
            ph = en.voice_lead(pcs, ph, 2, 53, 67)
            for p in ph:
                sc.note(HN, p, t, dur * 0.93, base, jt=jt, jv=3)
        if low_brass and lv >= 3 and rt not in lb_skip:
            pb = en.voice_lead(pcs, pb, 2, 46, 60)
            d = dur * 0.9 if (hem or lv >= 5) else 0.8
            for p in pb:
                sc.note(TBN, p, t, d, base + 4, jt=jt, jv=3)
            sc.note(TUBA, low_pitch(bass, 33), t, d, base + 6, jt=jt, jv=3)
        if timp:
            tp = timp_pitch(chord)
            if hem or lv >= 2 or bar_i % 4 == 0:
                sc.note(TIMP, tp, t, 0.6, base + 12, jt=jt, jv=3)
            if lv >= 3 and not hem:
                sc.note(TIMP, tp, t + 2.0, 0.3, base - 8, jt=2, jv=3)
                sc.note(TIMP, tp, t + 2.5, 0.3, base - 2, jt=2, jv=3)
        if drums and lv >= 3:
            if hem:
                sc.hit(36, t, base + 8, jt=0)
                sc.hit(38, t, base, jt=0)
            else:
                if bar_i % 2 == 0:
                    sc.hit(36, t, base + 4)
                if lv >= 4 and bar_i % 2 == 1:
                    sc.hit(38, t + 2.0, base - 22)
                    sc.hit(38, t + 2.5, base - 14)


def bassline(sc, t0, entries, lv, lo=0.0):
    """Contrabasses, with cellos and bassoons an octave above."""
    v = min(112, 80 + 5 * lv)
    part(sc, CB, t0, entries, v, lo=lo, gate=0.8)
    part(sc, VC, t0, entries, v - 6, tr=12, lo=lo, gate=0.8)
    part(sc, BSN, t0, entries, v - 10, tr=12, lo=lo, gate=0.62)


def tutti(sc, t, chord, bass, top, vel, dur=0.8, crash=True, tops=True):
    """One stroke of the whole orchestra."""
    pcs = list(PCS[chord])
    if tops:
        sc.note(VN, top, t, dur, vel, jt=0, jv=2)
        sc.note(SOLO, top, t, dur, vel - 8, jt=0, jv=2)
        sc.note(PICC, top + 12 if top + 12 <= 101 else top, t, dur,
                vel - 10, jt=0, jv=2)
        sc.note(OB, top if top <= 89 else top - 12, t, dur, vel - 6,
                jt=0, jv=2)
        sc.note(CL, en.voice_lead(pcs, None, 1, 64, 72)[0], t, dur,
                vel - 10, jt=0, jv=2)
    for p in en.voice_lead(pcs, None, 3, 55, 72):
        sc.note(VA, p, t, dur, vel - 6, jt=0, jv=2)
    for p in en.voice_lead(pcs, None, 3, 60, 79):
        sc.note(TREM, p, t, dur, vel - 10, jt=0, jv=2)
    for p in en.voice_lead(pcs, None, 2, 53, 67):
        sc.note(HN, p, t, dur, vel - 4, jt=0, jv=2)
    for p in en.voice_lead(pcs, None, 2, 67, 79):
        sc.note(TPT, p, t, dur, vel - 2, jt=0, jv=2)
    for p in en.voice_lead(pcs, None, 2, 46, 60):
        sc.note(TBN, p, t, dur, vel - 4, jt=0, jv=2)
    sc.note(TUBA, low_pitch(bass, 33), t, dur, vel - 2, jt=0, jv=2)
    sc.note(CB, low_pitch(bass, 36), t, dur, vel, jt=0, jv=2)
    sc.note(VC, low_pitch(bass, 48), t, dur, vel - 6, jt=0, jv=2)
    sc.note(BSN, low_pitch(bass, 48), t, dur, vel - 10, jt=0, jv=2)
    sc.note(TIMP, timp_pitch(chord), t, min(dur, 0.6), vel, jt=0, jv=2)
    sc.hit(36, t, vel, jt=0)
    if crash:
        sc.hit(49, t, vel - 12, jt=0)


def roll(sc, ch_or_key, t0, count, v0, v1, pitch=None, skip=()):
    """An eighth-note roll: timpani (pitch given) or a drum key."""
    for k in range(count):
        if k in skip:
            continue
        v = round(en.lerp(v0, v1, k / max(1, count - 1)))
        if pitch is None:
            sc.hit(ch_or_key, t0 + 0.5 * k, v, jt=2, jv=3)
        else:
            sc.note(ch_or_key, pitch, t0 + 0.5 * k, 0.3, v, jt=2, jv=3)


def intro(sc, t0, lv):
    """Eight bars: the BEAM in the basses under a timpani roll (i - i6/4 -
    VI - V - i, so its last step is a real cadence), then the BEAM as a
    trumpet call (on C) answered by the horns (on G)."""
    v = 80 + 8 * lv
    beam = E(N("C2 3"), N("G2 3"), N("Ab2 3"), N("G2 3"), N("C3 3"),
             N("C3 1 r 1 G2 1"), N("G2 3"), N("G2 3"))
    part(sc, CB, t0, beam, v + 6, gate=0.9)
    part(sc, VC, t0, beam, v, tr=12, gate=0.9)
    part(sc, BSN, t0, beam, v - 4, tr=12, gate=0.9)
    if lv >= 2:
        part(sc, TUBA, t0, beam, v, gate=0.9)
        part(sc, TBN, t0, beam, v - 2, tr=12, gate=0.9)
    for ch in (CB, VC, BSN, TUBA, TBN):
        en.expr_curve(sc, ch, [(t0, 84), (t0 + 12.0, 127)])
    # tremolo strings: C + E flat, swelling
    for p in (72, 75):
        sc.note(TREM, p, t0, 8.9, 64, jt=0)
    for p in (71, 74):                      # bar 4: a true dominant
        sc.note(TREM, p, t0 + 9.0, 2.9, 70, jt=0)
    en.expr_curve(sc, TREM, [(t0, 48), (t0 + 11.0, 127)])
    for p in (72, 75, 79):
        sc.note(TREM, p, t0 + 12.0, 5.9, 90, jt=0)
    for p in (71, 74, 79):
        sc.note(TREM, p, t0 + 18.0, 5.0, 92, jt=0)
    roll(sc, TIMP, t0, 24, 30 + 6 * lv, 86 + 8 * lv, pitch=48)
    sc.note(TIMP, 48, t0 + 12.0, 0.6, 112, jt=0)
    sc.note(TIMP, 48, t0 + 15.0, 0.6, 96, jt=0)
    roll(sc, TIMP, t0 + 18.0, 12, 58, 108, pitch=43)
    # the tutti stroke at bar 5 and the inner strings' drive
    for p in (75, 79, 84):
        sc.note(VN, p, t0 + 12.0, 0.8, v + 16, jt=0)
    sc.note(SOLO, 84, t0 + 12.0, 0.8, v + 6, jt=0)
    sc.note(PICC, 96, t0 + 12.0, 0.8, v, jt=0)
    sc.note(OB, 79, t0 + 12.0, 0.8, v + 4, jt=0)
    sc.note(CL, 75, t0 + 12.0, 0.8, v, jt=0)
    for k in range(12):
        for p in (60, 63, 67):
            sc.note(VA, p, t0 + 12.0 + 0.5 * k, 0.3,
                    v + (0 if k % 6 == 0 else -14), jt=2)
    for k in range(12):
        for p in (59, 62, 67):
            sc.note(VA, p, t0 + 18.0 + 0.5 * k, 0.3,
                    round(en.lerp(v - 10, v + 10, k / 11)), jt=2)
    gust = N("G4 .5 B4 .5 D5 .5 G5 .5 B5 .5 D6 .5")
    seq(sc, VN, t0 + 21.0, gust, v + 8)
    seq(sc, SOLO, t0 + 21.0, gust, v)
    # the calls
    seq(sc, TPT, t0 + 12.0, N("C4 1 G4 1 Ab4 .5 G4 .5 C5 2.8"),
        108 + 4 * lv, jt=0, gate=0.9)
    seq(sc, HN, t0 + 18.0, N("G3 1 D4 1 Eb4 .5 D4 .5 G4 2.8"),
        94 + 5 * lv, jt=0, gate=0.9)
    # woodwinds hold the dominant
    for ch, p in ((OB, 74), (CL, 71), (PICC, 91)):
        sc.note(ch, p, t0 + 18.0, 5.4, v - 2, jt=0)
        en.expr_curve(sc, ch, [(t0 + 18.0, 90), (t0 + 23.0, 127)])
    sc.hit(36, t0 + 12.0, 112, jt=0)
    sc.hit(49, t0 + 12.0, 84 + 8 * lv, jt=0)
    if lv >= 2:
        roll(sc, 38, t0 + 18.0, 12, 44, 98)
        sc.hit(36, t0 + 18.0, 100, jt=0)


def theme_A(sc, t0, lv, lo=0.0):
    """The sixteen-bar theme at orchestration level 1..5."""
    mv = 88 + 4 * lv
    part(sc, VN, t0, MEL_A, mv + 4, lo=lo)
    part(sc, SOLO, t0, MEL_A, mv - 6, lo=lo)
    part(sc, OB, t0, MEL_A, mv - 4, lo=lo)
    part(sc, CL, t0, MEL_A, mv - 8, tr=-12, lo=lo)
    if lv >= 2:
        part(sc, PICC, t0, MEL_A, mv - 8, tr=12, lo=lo)
    bassline(sc, t0, A_BASS, lv, lo=lo)
    accomp(sc, t0, A_SEGS, lv, lo=lo)
    if lv >= 2:
        hv = 72 + 5 * lv
        part(sc, HN, t0, HORN_A, hv, lo=lo, gate=0.94)
        if lv >= 4:
            part(sc, HN, t0, HORN_A, hv - 6, tr=-12, lo=lo, gate=0.94)
        pts = [(t0, 104), (t0 + 21.0, 127), (t0 + 24.0, 106),
               (t0 + 40.0, 127), (t0 + 47.0, 116)]
        pts = [(b, v) for b, v in pts if b >= t0 + lo - 1e-9]
        en.expr_curve(sc, HN, pts)
        en.expr_curve(sc, TREM, pts)
    if lv >= 3:
        part(sc, TPT, t0, TPT_A5 if lv >= 5 else TPT_A, 84 + 5 * lv, lo=lo)
        sc.hit(49, t0 + lo, 78 + 6 * lv, jt=0)
        sc.hit(49, t0 + 42.0, 80 + 6 * lv, jt=0)
    elif lv == 2:
        sc.hit(36, t0, 92, jt=0)
        sc.hit(36, t0 + 42.0, 96, jt=0)


def _light(sc, t0, chords, lv, second):
    """Pizzicato um-pah-pah, a soft arco bass and a held viola chord."""
    pv = pp = None
    for i, (chord, bass) in enumerate(chords):
        t = t0 + BAR * i
        pcs = list(PCS[chord])
        last = second and i == len(chords) - 1
        sc.note(TREM, low_pitch(bass, 41), t, 0.6, 92, jt=3)
        if not last:
            pp = en.voice_lead(pcs, pp, 2, 58, 70)
            for k in (1, 2):
                for p in pp:
                    sc.note(TREM, p, t + k, 0.4, 72, jt=3)
        sc.note(CB, low_pitch(bass, 36), t, 2.4, 62 + 4 * lv, jt=2)
        pv = en.voice_lead(pcs, pv, 3, 55, 70)
        for p in pv:
            sc.note(VA, p, t, 2.85, 54 + 4 * lv, jt=3)
        if second or lv >= 3:
            sc.note(VC, low_pitch(bass, 48), t, 2.6, 58 + 4 * lv, jt=2)


def section_B(sc, t0, lv):
    """24 bars: the woodwind episode (twice, the second time turning back
    to C minor), then the storm build over the BEAM in the basses."""
    # --- B1: oboe and clarinet in thirds over pizzicato --------------------
    part(sc, OB, t0, MEL_B, 92 + 2 * lv, gate=0.9, acc=4)
    part(sc, CL, t0, CL_B, 82 + 2 * lv, gate=0.9, acc=4)
    if lv >= 3:
        part(sc, SOLO, t0, MEL_B, 76, gate=0.9, acc=4)
    for ch in (OB, CL, SOLO):
        en.expr_curve(sc, ch, [(t0, 100), (t0 + 13.0, 124), (t0 + 23.0, 98),
                               (t0 + 24.0, 104), (t0 + 38.0, 127),
                               (t0 + 47.0, 110)])
    _light(sc, t0, B1_CH, lv, False)
    for i, name in enumerate(("G3", "G3", "Ab3", "Bb3", "Bb3", "Ab3", "Ab3",
                              "G3")):
        sc.note(HN, en.n(name), t0 + BAR * i, 2.9, 56 + 2 * lv, jt=3)
    en.expr_curve(sc, HN, [(t0, 96), (t0 + 24.0, 110), (t0 + 47.0, 120)])
    en.expr_curve(sc, VA, [(t0, 92), (t0 + 12.0, 116), (t0 + 24.0, 96),
                           (t0 + 40.0, 124), (t0 + 47.0, 127)])
    # --- B1': the tune again, fuller, bending back toward the dominant ------
    u = t0 + 24.0
    part(sc, OB, u, MEL_B2, 86 + 2 * lv, gate=0.9, acc=4)
    part(sc, SOLO, u, MEL_B2, 82 + 2 * lv, gate=0.9, acc=4)
    part(sc, PICC, u, MEL_B2, 72 + 2 * lv, tr=12, gate=0.9, acc=4)
    part(sc, CL, u, CL_B2, 76 + 2 * lv, gate=0.9, acc=4)
    part(sc, VN, u, VN_B2, 68 + 3 * lv, gate=0.96, acc=2)
    en.expr_curve(sc, VN, [(u, 96), (u + 12.0, 120), (u + 23.5, 127)])
    _light(sc, u, B1B_CH, lv, True)
    for i, name in enumerate(("G3", "G3", "Ab3", "Bb3", "Bb3", "Ab3", "Ab3",
                              "G3")):
        sc.note(HN, en.n(name), u + BAR * i, 2.9, 60 + 2 * lv, jt=3)
    for i, (chord, bass) in enumerate(B1B_CH):          # bassoon chatter
        p0 = low_pitch(bass, 43)
        tones = [p for p in range(p0, p0 + 30) if p % 12 in PCS[chord]][:4]
        for k, idx in enumerate((0, 1, 2, 3, 2, 1)):
            sc.note(BSN, tones[idx], u + BAR * i + 0.5 * k, 0.28,
                    64 + 2 * lv + (6 if k == 0 else 0), jt=2)
    roll(sc, TIMP, u + 21.0, 6, 46, 88, pitch=43)
    # --- B2: the storm build -----------------------------------------------
    w = t0 + 48.0
    lv2 = lv + 1
    for ch in (VN, VA, HN, OB, CL, SOLO, TREM):
        sc.cc(ch, 11, 127, w)
    accomp(sc, w, B2_SEGS, lv2, horn=True, low_brass=False, timp=False,
           last_trim=True)
    bv = 84 + 5 * lv2
    part(sc, CB, w, B2_BASS, bv + 4, gate=0.92)
    part(sc, VC, w, B2_BASS, bv - 2, tr=12, gate=0.92)
    part(sc, BSN, w, B2_BASS, bv - 6, tr=12, gate=0.92)
    part(sc, TUBA, w, B2_BASS, bv, gate=0.92)
    part(sc, TBN, w, B2_BASS, bv - 2, tr=12, gate=0.92)
    mv = 82 + 5 * lv2
    part(sc, VN, w, B2_MEL, mv + 4)
    part(sc, SOLO, w, B2_MEL, mv - 6)
    part(sc, OB, w, B2_MEL, mv - 4)
    part(sc, CL, w, B2_MEL, mv - 8, tr=-12)
    part(sc, PICC, w, B2_MEL, mv - 8, tr=12)
    part(sc, TPT, w, B2_TPT, 78 + 5 * lv2)
    en.expr_curve(sc, TPT, [(w + 6.0, 100), (w + 23.0, 127)])
    for k, tp in enumerate((48, 43, 48, 43)):
        roll(sc, TIMP, w + BAR * k, 6, 48 + 12 * k, 62 + 12 * k, pitch=tp)
    sc.note(TIMP, 48, w + 12.0, 0.6, 112, jt=0)
    sc.note(TIMP, 48, w + 15.0, 0.6, 104, jt=2)
    for k, tp in enumerate((41, 41, 43)):
        sc.note(TIMP, tp, w + 18.0 + 2.0 * k, 0.6, 110, jt=0)
    roll(sc, 38, w + 6.0, 12, 40, 96)
    sc.hit(49, w + 12.0, 84 + 6 * lv2, jt=0)


def codetta(sc, t0, lv, link):
    """Eight bars: two hemiola cadences, then either the hand-over to the
    trio (two strokes and a lone horn G) or the run into the coda."""
    segs = S(HEM_CAD, ("Cm", "C"), ("Cm", "C"), HEM_CAD)
    accomp(sc, t0, segs, lv, horn=True, last_trim=True)
    bassline(sc, t0, E(H("Ab2 2 F2 2 G2 2"), N("C3 1 r 1 G2 1"),
                       N("C3 1 r 1 C3 1"), H("Ab2 2 F2 2 G2 2")), lv)
    mel = E(H("Eb6 2 F6 2 D6 2"), N("C6 1 G5 1 Eb5 1"),
            N("C5 1 Eb5 1 G5 1"), H("C6 2 D6 2 B5 2"))
    mv = 86 + 5 * lv
    part(sc, VN, t0, mel, mv + 4)
    part(sc, SOLO, t0, mel, mv - 6)
    part(sc, PICC, t0, mel, mv - 8, tr=12)
    part(sc, OB, t0, mel, mv - 4)
    part(sc, CL, t0, mel, mv - 8, tr=-12)
    part(sc, TPT, t0, E(H("C5 2 D5 2 B4 2"), N("Eb5 1 C5 1 G4 1"),
                        N("G4 1 G4 .5 G4 .5 G4 1"), H("Eb5 2 F5 2 D5 2")),
         80 + 5 * lv)
    sc.hit(49, t0 + 6.0, 80 + 6 * lv, jt=0)
    u = t0 + 18.0
    if link:
        tutti(sc, u, "Cm", "C", en.n("C6"), 98 + 4 * lv)
        sc.note(TIMP, 43, u + 2.0, 0.4, 72, jt=0)
        tutti(sc, u + 3.0, "Cm", "C", en.n("C5"), 86 + 4 * lv, crash=False)
        sc.note(HN, en.n("G3"), u + 4.0, 7.0, 66, jt=0)   # the bridge note
        en.expr_curve(sc, HN, [(u + 4.0, 112), (u + 10.5, 64)])
    else:
        tutti(sc, u, "Cm", "C", en.n("C6"), 100 + 4 * lv, tops=False)
        tutti(sc, u + 3.0, "Cm", "C", en.n("C6"), 96 + 4 * lv, tops=False,
              crash=False)
        sc.note(CB, en.n("G2"), u + 5.0, 0.8, 104, jt=2)
        run = N("C5 .5 D5 .5 Eb5 .5 F5 .5 G5 .5 Ab5 .5 "
                "Bb5 .5 Ab5 .5 G5 .5 F5 .5 Eb5 .5 D5 .5")
        seq(sc, VN, u, run, mv + 4)
        seq(sc, SOLO, u, run, mv - 6)
        seq(sc, OB, u, run, mv - 4)
        seq(sc, CL, u, run, mv - 8, tr=-12)
        seq(sc, PICC, u, run, mv - 8, tr=12)
        roll(sc, TIMP, u, 12, 70, 112, pitch=48, skip=(0, 6))


# ---------------------------------------------------------------------------
# The trio material (C major)
# ---------------------------------------------------------------------------

TRIO_TUNE = E(
    N("G5 2 E5 1"), N("C5 2 D5 1"), N("E5 1.5 F5 .5 G5 1"), N("A5 3"),
    N("G5 2 C6 1"), N("B5 2 A5 1"), N("G5 1.5 F5 .5 E5 1"), N("D5 3"),
    N("G5 2 E5 1"), N("C5 2 D5 1"), N("E5 1.5 F5 .5 G5 1"), N("A5 2 B5 1"),
    N("C6 2 A5 1"), N("G5 2 E5 1"), N("F5 1 D5 1 B4 1"), N("C5 3"))
TRIO_CTR = E(
    N("E4 2 G4 1"), N("A4 2 G4 1"), N("G4 3"), N("F4 2 E4 1"),
    N("E4 2 G4 1"), N("G4 2 F4 1"), N("E4 3"), N("G4 3"),
    N("E4 2 G4 1"), N("A4 2 G4 1"), N("G4 3"), N("F4 2 G4 1"),
    N("A4 2 F4 1"), N("E4 2 C4 1"), N("D4 3"), N("E4 3"))
TRIO_THIRDS = E(
    N("E5 2 C5 1"), N("A4 2 B4 1"), N("C5 1.5 D5 .5 E5 1"), N("F5 2 G5 1"),
    N("A5 2 F5 1"), N("E5 2 C5 1"), N("D5 1 B4 1 G4 1"), N("E4 3"))
TRIO_CH = [("C", "C"), ("Am", "A"), ("C", "E"), ("F", "F"),
           ("C", "E"), ("G", "G"), ("C", "G"), ("G", "G"),
           ("C", "C"), ("Am", "A"), ("C", "E"), ("F", "F"),
           ("Dm7", "F"), ("C", "G"), ("G7", "G"), ("C", "C")]
H1_CH = [("C", "C"), ("C", "E"), ("F", "F"), ("C", "E"),
         ("C", "C"), ("C", "C"), ("F", "F"), ("G", "G"),
         ("Dm", "D"), ("G", "B"), ("Am", "A"), ("F", "F"),
         ("Am", "A"), ("Dm", "F"), ("G", "G"), ("G7", "G")]
H1_DESC = E(
    N("E5 2 G5 1"), N("C6 2 B5 1"), N("C6 1 A5 1 F5 1"), N("E5 2 G5 1"),
    N("E6 2 D6 1"), N("G5 3"), N("F5 1 A5 1 C6 1"), N("D6 3"),
    N("D6 1 C6 1 A5 1"), N("B5 2 D6 1"), N("C6 2 E6 1"), N("F6 2 E6 1"),
    N("C6 2 A5 1"), N("A5 2 F5 1"), N("G5 1 A5 1 B5 1"), N("D6 2 r 1"))
H2_CH = [("C", "E"), ("F", "F"), ("C", "G"), ("Am", "A"),
         ("G7", "G"), ("G7", "G"), ("C", "C"), ("C", "C"),
         ("C", "C"), ("C", "C"), ("C", "C"), ("C", "C")]
H2_CTR = E(
    N("E4 2 D4 1"), N("C4 2 D4 1"), N("E4 3"), N("C4 2 B3 1"),
    N("B3 2 A3 1"), N("G3 2 F3 1"), N("E3 3"), N("G3 3"))
H2_SOLO = E(N("E5 3"), N("F5 3"), N("E5 3"), N("C5 3"), N("B4 3"),
            N("B4 2 D5 1"), N("E5 6"))
HYMN_BASE = 60                 # C4: the horns sing the hymn in C major
HYMN_STRETCH = 1.5             # one hymn half-note = one bar of 3/4


def _harp_bar(sc, t, chord, bass, vel):
    p0 = low_pitch(bass, 43)
    tones = [p for p in range(p0, p0 + 30) if p % 12 in PCS[chord]][:4]
    for k, idx in enumerate((0, 1, 2, 3, 2, 1)):
        sc.note(TBN, tones[idx], t + 0.5 * k, 0.45 if k == 5 else 0.9,
                vel + (6 if k == 0 else 0), jt=3, jv=4)


def _trio_bed(sc, t0, chords, vel, vn=False, harp=True, pizz=True,
              arco=False, dyads=False):
    """Held strings, harp arpeggios and a pizzicato bass under the trio."""
    pcs = [list(PCS[c]) for c, _b in chords]
    en.pad_block(sc, VA, t0, pcs, BAR, size=3, lo=52, hi=67, vel=vel,
                 legato=0.0)
    if vn:
        en.pad_block(sc, VN, t0, pcs, BAR, size=2, lo=67, hi=79,
                     vel=vel - 2, legato=0.0)
    pp = None
    for i, (chord, bass) in enumerate(chords):
        t = t0 + BAR * i
        if harp:
            _harp_bar(sc, t, chord, bass, vel + 4)
        if pizz:
            sc.note(TREM, low_pitch(bass, 36), t, 0.7, vel + 16, jt=3)
            if dyads:
                pp = en.voice_lead(PCS[chord], pp, 2, 57, 69)
                for k in (1, 2):
                    for p in pp:
                        sc.note(TREM, p, t + k, 0.4, vel, jt=3)
        if arco:
            sc.note(CB, low_pitch(bass, 36), t, 2.9, vel, jt=3)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _b_scherzo(sc):
    intro(sc, S1, 1)
    theme_A(sc, S1_A1, 1)
    theme_A(sc, S1_A2, 2)
    section_B(sc, S1_B, 2)
    theme_A(sc, S1_A3, 3)
    codetta(sc, S1_CDT, 3, link=True)


def _b_trio(sc):
    t0 = TRIO
    sc.cc(TBN, 7, 100, t0 - 0.4)                  # the harp's level
    for ch in (VN, VA, VC, CB, OB, CL, BSN, SOLO, PICC, TREM):
        sc.cc(ch, 11, 110, t0)
    for ch, depth in ((OB, 28), (SOLO, 36), (VC, 30), (PICC, 30)):
        sc.cc(ch, 1, depth, t0)
    # --- four bars of weather clearing --------------------------------------
    opening = [("C", "C"), ("C", "E"), ("F", "F"), ("G", "G")]
    _trio_bed(sc, t0, opening, 52, vn=True)
    for ch in (VA, VN):
        en.expr_curve(sc, ch, [(t0, 84), (t0 + 11.0, 110)])
    # --- the pastoral tune: oboe, the cellos singing against it -------------
    part(sc, OB, T_A, TRIO_TUNE, 80, gate=0.95, acc=3)
    part(sc, VC, T_A, TRIO_CTR, 70, gate=0.95, acc=2)
    part(sc, CL, T_A + 24.0, TRIO_THIRDS, 64, gate=0.95, acc=2)
    _trio_bed(sc, T_A, TRIO_CH, 46)
    for ch in (OB, VC, CL):
        en.expr_curve(sc, ch, [(T_A, 98), (T_A + 10.0, 122),
                               (T_A + 22.0, 100), (T_A + 24.0, 102),
                               (T_A + 37.0, 127), (T_A + 47.0, 98)])
    # --- the horns quote the keeper's hymn: phrases 1 and 2 -----------------
    t = T_H1
    material.play_phrase(sc, HN, t, HYMN_BASE, "ionian", 0,
                         stretch=HYMN_STRETCH, vel=68, gate=0.97)
    material.play_phrase(sc, HN, t + 24.0, HYMN_BASE, "ionian", 1,
                         stretch=HYMN_STRETCH, vel=68, gate=0.97)
    en.expr_curve(sc, HN, [(t - 1.0, 92), (t + 13.0, 116), (t + 23.0, 96),
                           (t + 36.0, 118), (t + 47.0, 92)])
    part(sc, SOLO, t, H1_DESC, 68, gate=0.95, acc=2)
    en.expr_curve(sc, SOLO, [(t, 96), (t + 13.0, 120), (t + 23.0, 100),
                             (t + 34.0, 124), (t + 47.0, 96)])
    _trio_bed(sc, t, H1_CH, 46, vn=True, arco=True)
    h1 = [list(PCS[c]) for c, _b in H1_CH]
    en.pad_block(sc, CL, t, h1, BAR, size=1, lo=60, hi=67, vel=52,
                 legato=0.0)
    en.pad_block(sc, BSN, t, h1, BAR, size=1, lo=48, hi=57, vel=52,
                 legato=0.0)
    for i, (_c, bass) in enumerate(H1_CH):
        sc.note(VC, low_pitch(bass, 48), t + BAR * i, 2.9, 56, jt=3)
    for ch in (VA, VN, CL, BSN, VC):
        en.expr_curve(sc, ch, [(t, 96), (t + 14.0, 118), (t + 24.0, 100),
                               (t + 38.0, 122), (t + 47.0, 100)])
    sc.hit(81, t, 44, jt=0)
    # --- the tune again: flute, the solo violin taking the counter-melody ---
    t = T_A2
    part(sc, PICC, t, TRIO_TUNE, 82, gate=0.95, acc=3)
    part(sc, SOLO, t, TRIO_CTR, 66, tr=12, gate=0.95, acc=2)
    part(sc, OB, t + 24.0, TRIO_THIRDS, 62, gate=0.95, acc=2)
    for i, (chord, bass) in enumerate(TRIO_CH):          # cellos walk
        p0 = low_pitch(bass, 48)
        tones = [p for p in range(p0, p0 + 20) if p % 12 in PCS[chord]][:3]
        for k in range(3):
            sc.note(VC, tones[k], t + BAR * i + k, 0.85, 60 - 3 * k, jt=3)
    for i in range(8):
        sc.note(HN, en.n("G3"), t + 6.0 * i, 5.8, 52, jt=3)
    _trio_bed(sc, t, TRIO_CH, 50, dyads=True)
    for ch in (PICC, SOLO, OB, VC, HN, VA):
        en.expr_curve(sc, ch, [(t, 100), (t + 10.0, 122), (t + 22.0, 102),
                               (t + 37.0, 127), (t + 47.0, 104)])
    sc.hit(81, t, 44, jt=0)
    sc.hit(81, t + 24.0, 46, jt=0)
    # --- the hymn's last phrase: the cadence home, then the air goes still --
    t = T_H2
    material.play_phrase(sc, HN, t, HYMN_BASE, "ionian", 3,
                         stretch=HYMN_STRETCH, vel=72, gate=0.97)
    for d, on, du in material.hymn_phrase(3):            # flute, two octaves up
        sc.note(PICC, en.pitch(HYMN_BASE + 24, "ionian", d),
                t + on * HYMN_STRETCH, du * HYMN_STRETCH * 0.95, 62, jt=3)
    part(sc, VC, t, H2_CTR, 74, gate=0.95, acc=2)
    part(sc, SOLO, t, H2_SOLO, 66, gate=0.96, acc=2)
    _trio_bed(sc, t, H2_CH, 48, vn=True, harp=False, pizz=False, arco=False)
    for i, (chord, bass) in enumerate(H2_CH[:8]):
        _harp_bar(sc, t + BAR * i, chord, bass, 58)
    for i, (chord, bass) in enumerate(H2_CH[:10]):
        sc.note(TREM, low_pitch(bass, 36), t + BAR * i, 0.7, 68, jt=3)
        sc.note(CB, low_pitch(bass, 36), t + BAR * i, 2.9, 54, jt=3)
    h2 = [list(PCS[c]) for c, _b in H2_CH[:8]]
    en.pad_block(sc, CL, t, h2, BAR, size=1, lo=60, hi=67, vel=54,
                 legato=0.0)
    en.pad_block(sc, BSN, t, h2, BAR, size=1, lo=48, hi=57, vel=54,
                 legato=0.0)
    en.expr_curve(sc, HN, [(t - 0.5, 96), (t + 12.0, 120), (t + 24.0, 88)])
    for ch in (VA, VN, VC, SOLO, PICC, CL, BSN):
        en.expr_curve(sc, ch, [(t, 104), (t + 12.0, 127), (t + 24.0, 100),
                               (t + 35.5, 40)])
    for k, name in enumerate(("C3", "G3", "C4", "E4", "G4", "C5")):
        sc.note(TBN, en.n(name), t + 24.0 + 0.5 * k, 1.6, 54, jt=3)
    for k, name in enumerate(("E5", "G5", "C6")):
        sc.note(TBN, en.n(name), t + 27.0 + k, 1.8, 50 - 2 * k, jt=3)
    sc.hit(81, t, 46, jt=0)
    roll(sc, TIMP, t + 30.0, 12, 26, 50, pitch=43)    # a far-off dominant


def _b_scherzo2(sc):
    sc.cc(TBN, 7, VOL[TBN], S2 - 0.4)
    for ch in range(16):
        if ch != DR:
            sc.cc(ch, 11, 127, S2)
            sc.cc(ch, 1, 0, S2)
    intro(sc, S2, 2)
    theme_A(sc, S2_A1, 4)
    section_B(sc, S2_B, 3)
    theme_A(sc, S2_A2, 5)
    codetta(sc, S2_CDT, 5, link=False)


def _swirl(table, hem):
    return E(*([N(" ".join(x + " .5" for x in table[c].split()))
                for c in ("Cm", "Cm", "Ab", "Ab", "Fm", "Fm")] + [H(hem)]))


def _b_coda(sc):
    t = CODA
    for ch in range(16):
        if ch != DR:
            sc.cc(ch, 11, 127, t)
    # --- C1: the theme's head in stretto, strings against brass -------------
    accomp(sc, t, S(("Cm", "C"), ("Cm", "C"), ("Ab", "Ab"), ("Ab", "Ab"),
                    ("Fm", "F"), ("Fm", "F"), ("G", "G"), ("G", "G")), 5,
           last_trim=False)
    bassline(sc, t, E(N("C3 1 r 1 G2 1"), N("C3 1 r 1 Bb2 1"),
                      N("Ab2 1 r 1 Eb3 1"), N("Ab2 1 r 1 G2 1"),
                      N("F2 1 r 1 C3 1"), N("F2 1 Ab2 1 F2 1"),
                      N("G2 1 r 1 D3 1"), N("G2 1 r 1 G2 1")), 5)
    for off, head in ((0.0, N("C5 1 G5 1 Ab5 .5 G5 .5 C6 2")),
                      (12.0, N("F5 1 C6 1 D6 .5 C6 .5 F6 2"))):
        seq(sc, VN, t + off, head, 114)
        seq(sc, SOLO, t + off, head, 102)
        seq(sc, OB, t + off, head, 104)
        seq(sc, CL, t + off, head, 100, tr=-12)
        seq(sc, PICC, t + off, head, 100, tr=12)
    for off, name in ((6.0, "C6"), (9.0, "Ab5"), (18.0, "D6"), (21.0, "B5")):
        for ch, v in ((VN, 108), (SOLO, 98), (OB, 100)):
            sc.note(ch, en.n(name), t + off, 0.8, v, jt=2)
    for off, head, v in ((6.0, N("Ab4 1 Eb5 1 F5 .5 Eb5 .5 Ab5 2"), 110),
                         (18.0, N("G4 1 D5 1 Eb5 .5 D5 .5 G5 2"), 112)):
        seq(sc, TPT, t + off, head, v, jt=0, gate=0.9)
        seq(sc, HN, t + off, head, v - 8, tr=-12, jt=0, gate=0.9)
    for off, names in ((0.0, ("C4", "Eb4")), (12.0, ("C4", "F4"))):
        for name in names:
            sc.note(HN, en.n(name), t + off, 5.6, 94, jt=2)
    sc.hit(49, t, 108, jt=0)
    theme_A(sc, t, 5, lo=24.0)
    # --- C2: BEAM calls over a tonic pedal, the strings swirling ------------
    t = C2
    u = t + 24.0
    accomp(sc, t, S(("Cm", "C"), ("Cm", "C"), ("Ab", "C"), ("Ab", "C"),
                    ("Fm", "C"), ("Fm", "C"), HEM_CAD), 5, last_trim=False)
    accomp(sc, u, S(("Cm", "C"), ("Cm", "C"), ("Ab", "Ab"), ("Ab", "Ab"),
                    ("Fm", "F"), ("Fm", "F"), HEM_CAD), 6, lb_skip=(0.0, 3.0),
           last_trim=False)
    bassline(sc, t, E(N("C3 1 r 1 G2 1"), N("C3 1 r 1 C2 1"),
                      N("C3 1 r 1 G2 1"), N("C3 1 r 1 C2 1"),
                      N("C3 1 r 1 G2 1"), N("C3 1 r 1 C2 1"),
                      H("Ab2 2 F2 2 G2 2")), 5)
    bassline(sc, u, E(N("C2 1 G2 1 Ab2 .5 G2 .5"), N("C3 2 r 1"),
                      N("Ab2 1 r 1 Eb3 1"), N("Ab2 1 r 1 G2 1"),
                      N("F2 1 r 1 C3 1"), N("F2 1 Ab2 1 F2 1"),
                      H("Ab2 2 F2 2 G2 2")), 6)
    low_beam = N("C2 1 G2 1 Ab2 .5 G2 .5 C3 2")
    seq(sc, TUBA, u, low_beam, 110, gate=0.9)
    seq(sc, TBN, u, low_beam, 108, tr=12, gate=0.9)
    sw1 = _swirl({"Cm": "G5 Ab5 G5 Eb5 C5 Eb5", "Ab": "Ab5 Bb5 Ab5 Eb5 C5 Eb5",
                  "Fm": "Ab5 Bb5 Ab5 F5 C5 F5"}, "C6 2 D6 2 B5 2")
    sw2 = _swirl({"Cm": "Eb6 F6 Eb6 C6 G5 C6", "Ab": "Eb6 F6 Eb6 C6 Ab5 C6",
                  "Fm": "F6 G6 F6 C6 Ab5 C6"}, "Eb6 2 F6 2 D6 2")
    part(sc, VN, t, sw1, 108)
    part(sc, SOLO, t, sw1, 98)
    part(sc, OB, t, sw1, 100)
    part(sc, CL, t, sw1, 96, tr=-12)
    part(sc, PICC, t, sw1, 96, tr=12)
    part(sc, VN, u, sw2, 112)
    part(sc, SOLO, u, sw2, 102)
    part(sc, OB, u, sw2, 102, tr=-12)
    part(sc, CL, u, sw2, 98, tr=-12)
    part(sc, PICC, u, sw2, 100)
    seq(sc, TPT, t, N("C5 1 G5 1 Ab5 .5 G5 .5 C6 2"), 112, jt=0, gate=0.9)
    sc.note(TPT, en.n("Eb5"), t + 6.0, 5.6, 98, jt=2)
    seq(sc, TPT, t + 12.0, N("F4 1 C5 1 D5 .5 C5 .5 F5 2"), 110, jt=0,
        gate=0.9)
    seq(sc, TPT, t + 18.0, N("Eb5 2 F5 2 D5 2"), 114, jt=0, acc=0)
    for name in ("C4", "G4"):
        sc.note(HN, en.n(name), t, 5.6, 96, jt=2)
    seq(sc, HN, t + 6.0, N("Ab3 1 Eb4 1 F4 .5 Eb4 .5 Ab4 2"), 108, jt=0,
        gate=0.9)
    for name in ("C4", "F4"):
        sc.note(HN, en.n(name), t + 12.0, 5.6, 98, jt=2)
    hem_horns = ((("C4", "Eb4"), 0.0), (("Ab3", "D4"), 2.0),
                 (("G3", "B3"), 4.0))
    for base in (t + 18.0, u + 18.0):
        for names, off in hem_horns:
            for name in names:
                sc.note(HN, en.n(name), base + off, 1.8, 106, jt=0)
    sc.note(TPT, en.n("G5"), u, 5.6, 102, jt=2)
    for name in ("C4", "Eb4"):
        sc.note(HN, en.n(name), u, 5.6, 100, jt=2)
    seq(sc, TPT, u + 6.0, N("Ab4 1 Eb5 1 F5 .5 Eb5 .5 Ab5 2"), 114, jt=0,
        gate=0.9)
    for name in ("Ab3", "C4"):
        sc.note(HN, en.n(name), u + 6.0, 5.6, 100, jt=2)
    beam_f = N("F4 1 C5 1 D5 .5 C5 .5 F5 2")
    seq(sc, TPT, u + 12.0, beam_f, 116, jt=0, gate=0.9)
    seq(sc, HN, u + 12.0, beam_f, 110, tr=-12, jt=0, gate=0.9)
    seq(sc, TPT, u + 18.0, N("Ab5 2 F5 2 D5 2"), 118, jt=0, acc=0)
    sc.hit(49, t, 106, jt=0)
    sc.hit(49, u, 110, jt=0)
    # --- C3: the hemiola chain ----------------------------------------------
    t = C3
    accomp(sc, t, S(("Cm", "C"), ("Cm", "Eb"), HEM_CAD,
                    ("Cm", "C"), ("Cm", "Eb"),
                    ("H", [("Fm", "Ab"), ("Do", "F"), ("G", "G")])), 6,
           horn=True, last_trim=True)
    bassline(sc, t, E(N("C3 1 r 1 G2 1"), N("Eb3 1 r 1 G2 1"),
                      H("Ab2 2 F2 2 G2 2"), N("C3 1 r 1 G2 1"),
                      N("Eb3 1 r 1 G2 1"), H("Ab2 2 F2 2 G2 2")), 6)
    mel = E(N("Eb6 1 C6 1 G5 1"), N("Eb5 1 G5 1 C6 1"), H("Eb6 2 F6 2 D6 2"),
            N("Eb6 1 C6 1 G5 1"), N("Eb5 1 G5 1 C6 1"), H("F6 2 F6 2 G6 2"))
    part(sc, VN, t, mel, 114)
    part(sc, SOLO, t, mel, 104)
    part(sc, OB, t, mel, 104, tr=-12)
    part(sc, CL, t, mel, 100, tr=-12)
    part(sc, PICC, t, mel, 102)
    part(sc, TPT, t, E(N("G5 1 Eb5 1 C5 1"), N("C5 1 C5 .5 C5 .5 Eb5 1"),
                       H("C5 2 D5 2 B4 2"), N("G5 1 Eb5 1 C5 1"),
                       N("C5 1 C5 .5 C5 .5 Eb5 1"), H("Ab5 2 Ab5 2 G5 2")),
         110)
    sc.hit(49, t, 110, jt=0)
    sc.hit(49, t + 12.0, 112, jt=0)
    # --- C4: the last gust and the hammer strokes ---------------------------
    t = C4
    rush = N("G4 .5 Ab4 .5 Bb4 .5 C5 .5 D5 .5 Eb5 .5 "
             "F5 .5 G5 .5 Ab5 .5 Bb5 .5 C6 .5 D6 .5")
    for ch, tr, v in ((VN, 0, 110), (SOLO, 0, 100), (OB, 0, 102),
                      (CL, -12, 98), (PICC, 12, 98), (VC, -12, 100),
                      (BSN, -24, 96)):
        seq(sc, ch, t, rush, v, tr=tr)
    held = ((CB, (36,)), (TUBA, (36,)), (TBN, (48, 55)), (HN, (60, 63)),
            (TPT, (67, 72)), (TREM, (72, 75, 79)))
    for ch, pitches in held:
        for p in pitches:
            sc.note(ch, p, t, 5.8, 100, jt=0)
        en.expr_curve(sc, ch, [(t, 88), (t + 5.5, 127)], step=0.5)
    for k in range(12):
        for p in (60, 63, 67):
            sc.note(VA, p, t + 0.5 * k, 0.3,
                    round(en.lerp(84, 108, k / 11)), jt=2)
    roll(sc, TIMP, t, 12, 64, 112, pitch=48)
    roll(sc, 38, t, 12, 50, 104)
    strokes = (("Cm", "C", "Eb6"), ("G", "G", "D6"), ("Cm", "C", "Eb6"),
               ("G", "G", "D6"), ("Cm", "C", "C6"))
    for k, (chord, bass, top) in enumerate(strokes):
        b = t + 6.0 + BAR * k
        tutti(sc, b, chord, bass, en.n(top), 116 + k)
        if k < 4:
            sc.note(TIMP, 43, b + 2.0, 0.3, 96, jt=2)
            sc.note(TIMP, 43, b + 2.5, 0.3, 104, jt=2)
        else:
            roll(sc, TIMP, b, 6, 84, 116, pitch=48, skip=(0,))
            roll(sc, 38, b, 6, 70, 108, skip=(0,))
    b = END - BAR
    tutti(sc, b, "Cm", "C", en.n("C6"), 124, dur=3.0)
    roll(sc, TIMP, b, 6, 112, 84, pitch=48, skip=(0,))


BUILDERS = [_b_scherzo, _b_trio, _b_scherzo2, _b_coda]

# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

MINOR_SPANS = [(S1, TRIO), (S2, CODA), (CODA, END)]
AEOLIAN = {0, 2, 3, 5, 7, 8, 10}
IONIAN = {0, 2, 4, 5, 7, 9, 11}
DOMINANT = {7, 11, 2}
TONAL = [ch for ch in range(16) if ch != DR]


def _minor_bars():
    for lo, hi in MINOR_SPANS:
        bar0 = lo
        while bar0 < hi - 1e-6:
            yield bar0
            bar0 += BAR


def find_hemiolas(sc):
    """Bar pairs (in the minor sections) where at least five voices strike
    h, h+2 and h+4 and NOTHING strikes the second bar line h+3: three
    half-note strokes across two bars of three."""
    ons = {ch: [b for b, _p, _v in material.note_ons(sc, ch)]
           for ch in sorted(sc.events)}

    def hit(ch, beat, tol=0.03):
        return any(abs(b - beat) <= tol for b in ons[ch])

    out = []
    for h in _minor_bars():
        voices = [ch for ch in ons
                  if hit(ch, h) and hit(ch, h + 2.0) and hit(ch, h + 4.0)]
        barline = [ch for ch in ons if hit(ch, h + 3.0, 0.2)]
        if len(voices) >= 5 and not barline:
            out.append(h)
    return out


def _o_form(sc):
    fails = []
    names = [m[0] for m in PART.MOVEMENTS]
    for want, got in zip(("Scherzo", "Trio", "Scherzo", "Coda"), names):
        if want not in got:
            fails.append(f"movement '{got}' should be the {want}")
    if len(names) != 4:
        fails.append(f"{len(names)} movements, want 4")
    if sorted(sc.keysigs) != [(0.0, -3, 1), (TRIO, 0, 0), (S2, -3, 1)]:
        fails.append("key signatures must read c minor / C major / c minor")
    stray_trio, stray_minor, thirds = [], [], {3: 0, 4: 0}
    for ch in TONAL:
        for beat, p, _v in material.note_ons(sc, ch):
            pc = p % 12
            if TRIO <= beat < S2:
                if pc not in IONIAN:
                    stray_trio.append((ch, round(beat, 2), p))
                if pc in thirds:
                    thirds[pc] += 1
            elif pc not in AEOLIAN and pc != 11:
                stray_minor.append((ch, round(beat, 2), p))
    if stray_trio:
        fails.append(f"trio leaves C major: {stray_trio[:4]}")
    if thirds[4] < 40 or thirds[3]:
        fails.append(f"trio must sound the major third: E natural x"
                     f"{thirds[4]}, E flat x{thirds[3]}")
    if stray_minor:
        fails.append(f"scherzo/coda leave C minor: {stray_minor[:4]}")
    return fails


def _o_trio_quieter(sc):
    fails = []
    e_s1 = material.energy(sc, S1, TRIO)
    e_trio = material.energy(sc, TRIO, S2)
    if e_trio > 0.45 * e_s1:
        fails.append(f"trio energy {e_trio:.0f} is not under 45% of the "
                     f"scherzo's {e_s1:.0f}")
    loud = max(v for ch in sorted(sc.events)
               for b, _p, v in material.note_ons(sc, ch)
               if TRIO <= b < S2 - 0.05)
    if loud > 96:
        fails.append(f"trio reaches velocity {loud} (ceiling 96)")
    trio_bpm = [bpm for b, bpm in sorted(sc.tempos) if b <= TRIO][-1]
    if trio_bpm >= SCHERZO_TEMPO:
        fails.append(f"trio tempo {trio_bpm} is not calmer than the "
                     f"scherzo's {SCHERZO_TEMPO}")
    kit = [b for b, p, _v in material.note_ons(sc, DR)
           if TRIO <= b < S2 and p != 81]
    if kit:
        fails.append(f"only the triangle may sound in the trio: {kit[:4]}")
    return fails


def _o_return_bigger(sc):
    fails = []
    e_s1 = material.energy(sc, S1, TRIO)
    e_s2 = material.energy(sc, S2, CODA)
    if e_s2 < 1.15 * e_s1:
        fails.append(f"scherzo return energy {e_s2:.0f} < 1.15 x first "
                     f"scherzo {e_s1:.0f}")
    first = material.energy(sc, S1_A1, S1_A1 + 48.0)
    back = material.energy(sc, S2_A1, S2_A1 + 48.0)
    last = material.energy(sc, S2_A2, S2_A2 + 48.0)
    if back < 1.3 * first:
        fails.append(f"returning theme {back:.0f} < 1.3 x its first "
                     f"statement {first:.0f}")
    if last < back:
        fails.append(f"final theme {last:.0f} < the returning theme "
                     f"{back:.0f}")
    v1 = material.active_channels(sc, S1_A1 + 0.1, S1_A1 + 47.9)
    v2 = material.active_channels(sc, S2_A1 + 0.1, S2_A1 + 47.9)
    if len(v2) < len(v1) + 4:
        fails.append(f"returning theme uses {len(v2)} voices vs "
                     f"{len(v1)}; want at least 4 more")
    return fails


def _o_hymn_in_horns(sc):
    fails = []
    for k, t in ((0, T_H1), (1, T_H1 + 24.0), (3, T_H2)):
        found = material.phrase_statements(sc, HN, "ionian", k)
        if not any(abs(s - t) <= 0.05 and abs(st - HYMN_STRETCH) <= 0.01
                   and base == HYMN_BASE for s, st, base in found):
            fails.append(f"horns do not state hymn phrase {k + 1} at beat "
                         f"{t:.0f} (found {found})")
        outside = [s for s, _st, _b in found if not TRIO <= s < S2]
        if outside:
            fails.append(f"hymn phrase {k + 1} leaks outside the trio: "
                         f"{outside}")
    return fails


def _o_hemiolas(sc):
    fails = []
    hems = find_hemiolas(sc)
    cb = material.note_ons(sc, CB)

    def cb_pc(beat):
        hit = [p % 12 for b, p, _v in cb if abs(b - beat) <= 0.03]
        return hit[0] if hit else None

    for h in hems:
        if cb_pc(h + 4.0) != 7 or cb_pc(h + 6.0) != 0:
            fails.append(f"hemiola at beat {h:.0f} is not a cadence: basses "
                         f"play pc {cb_pc(h + 4.0)} then {cb_pc(h + 6.0)} "
                         f"(want G then C)")
    for name, lo, hi, need in (("scherzo", S1, TRIO, 6),
                               ("scherzo return", S2, CODA, 5),
                               ("coda", CODA, END, 5)):
        got = sum(1 for h in hems if lo <= h < hi)
        if got < need:
            fails.append(f"{name}: {got} hemiola cadence(s), need {need}")
    # every statement of the theme closes on one (bars 13-14)
    for t in (S1_A1, S1_A2, S1_A3, S2_A1, S2_A2, CODA):
        if not any(abs(h - (t + 36.0)) < 1e-6 for h in hems):
            fails.append(f"theme at beat {t:.0f} has no hemiola in its "
                         f"bars 13-14")
    return fails


def _o_leading_tone(sc):
    """B natural only over a dominant bass; every V-i cadence has it; B flat
    and B natural never share a bar."""
    fails = []
    cb_bar: dict = {}
    for b, p, _v in material.note_ons(sc, CB):
        cb_bar.setdefault(int((b + 0.03) // BAR), []).append((b, p % 12))
    nat: dict = {}
    flat: dict = {}
    held: dict = {}
    for ch in TONAL:
        for on, off, p, _v in material.note_spans(sc, ch):
            pc = p % 12
            k = int((on + 0.03) // BAR)
            if pc == 11:
                nat.setdefault(k, []).append((ch, on))
                while k * BAR < off - 0.25:
                    held[k] = True
                    k += 1
            elif pc == 10:
                flat.setdefault(k, []).append((ch, on))
    cadences = 0
    for bar0 in _minor_bars():
        k = int(round(bar0 / BAR))
        pcs = {pc for _b, pc in cb_bar.get(k, [])}
        dominant = bool(pcs) and pcs <= DOMINANT and 7 in pcs
        if k in nat and not dominant:
            fails.append(f"B natural at beat {nat[k][0][1]:.1f} (ch"
                         f"{nat[k][0][0]}) is not over a dominant bass")
        if k in nat and k in flat:
            fails.append(f"bar at beat {bar0:.0f} mixes B flat and B natural")
        nxt = cb_bar.get(k + 1, [])
        if dominant and nxt and abs(nxt[0][0] - (bar0 + BAR)) <= 0.03 \
                and nxt[0][1] == 0 and bar0 + BAR < END:
            cadences += 1
            if k not in held:
                fails.append(f"V-i cadence at beat {bar0:.0f} lacks the "
                             f"raised leading tone")
            if k in flat:
                fails.append(f"V-i cadence at beat {bar0:.0f} sounds B flat")
    if cadences < 20:
        fails.append(f"only {cadences} V-i cadences with a leading tone, "
                     f"need >= 20")
    return fails[:8]


def _o_one_in_a_bar(sc):
    fails = []
    skip = {h + BAR for h in find_hemiolas(sc)}
    low = sorted(b for ch in (CB, VC, BSN, TUBA, TIMP)
                 for b, _p, _v in material.note_ons(sc, ch))
    missing = []
    for bar0 in _minor_bars():
        if bar0 in skip:
            continue
        if not any(abs(b - bar0) <= 0.04 for b in low):
            missing.append(bar0)
    if missing:
        fails.append(f"{len(missing)} bar(s) without a bass downbeat: "
                     f"{missing[:6]}")
    mass = [0.0, 0.0, 0.0]
    off_grid = []
    for ch in sorted(sc.events):
        for b, _p, v in material.note_ons(sc, ch):
            if abs(b * 2.0 - round(b * 2.0)) > 0.06:
                off_grid.append((ch, round(b, 3)))
            if not any(lo <= b + 0.04 and b < hi for lo, hi in MINOR_SPANS):
                continue
            pos = (b + 0.04) % BAR
            if pos < 0.08:
                mass[0] += v
            elif abs(pos - 1.04) < 0.04:
                mass[1] += v
            elif abs(pos - 2.04) < 0.04:
                mass[2] += v
    if off_grid:
        fails.append(f"{len(off_grid)} onset(s) off the eighth-note "
                     f"lattice: {off_grid[:4]}")
    if mass[0] < 1.25 * max(mass[1], mass[2]):
        fails.append(f"the bar is not felt in one: velocity mass on beats "
                     f"1/2/3 = {mass[0]:.0f}/{mass[1]:.0f}/{mass[2]:.0f}")
    return fails


def _o_beam_voices(sc):
    fails = []
    for name, ch, need in (("trumpet", TPT, 3), ("horn", HN, 3),
                           ("contrabass", CB, 4), ("violin theme", VN, 5)):
        got = material.beam_statements(sc, ch)
        if len(got) < need:
            fails.append(f"{name}: {len(got)} BEAM statement(s), need "
                         f"{need} ({[round(b) for b in got]})")
    cb = material.beam_statements(sc, CB)
    if not cb or abs(cb[0] - 0.0) > 0.05:
        fails.append("the track must open with the BEAM in the basses")
    tp = material.beam_statements(sc, TPT)
    if not any(abs(b - (S1 + 12.0)) <= 0.05 for b in tp):
        fails.append("no trumpet BEAM call at bar 5")
    return fails


def _o_counterpoint(sc):
    fails = []
    for name, lead, ctr, t0, nbars in (
            ("oboe tune / cellos", OB, VC, T_A, 16),
            ("hymn / solo violin", HN, SOLO, T_H1, 16),
            ("flute tune / solo violin", PICC, SOLO, T_A2, 16),
            ("hymn / cellos", HN, VC, T_H2, 8)):
        for k in range(nbars):
            beat = t0 + BAR * k + 0.25
            a = material.sounding(sc, lead, beat)
            c = material.sounding(sc, ctr, beat)
            if len(a) != 1 or len(c) != 1:
                fails.append(f"{name} bar {k + 1}: need one note each, got "
                             f"{a} / {c}")
            elif (a[0] - c[0]) % 12 not in material.CONSONANT:
                fails.append(f"{name} bar {k + 1}: {a[0]} against {c[0]} "
                             f"is dissonant")
    return fails[:8]


def _o_coda_presses(sc):
    fails = []
    tempos = [bpm for b, bpm in sorted(sc.tempos) if b >= CODA]
    if len(tempos) < 3 or tempos != sorted(set(tempos)) \
            or tempos[0] <= SCHERZO_TEMPO or tempos[-1] < 196.0:
        fails.append(f"coda tempos {tempos} must climb strictly from above "
                     f"{SCHERZO_TEMPO:.0f} to at least 196")
    e_coda = material.energy(sc, CODA, C4)
    e_s2 = material.energy(sc, S2, CODA)
    if e_coda < e_s2:
        fails.append(f"coda energy {e_coda:.0f} falls below the scherzo "
                     f"return's {e_s2:.0f}")
    last = [(ch, p) for ch in TONAL
            for on, off, p, _v in material.note_spans(sc, ch)
            if abs(off - END) <= 0.01 and on <= END - BAR + 0.01]
    if len({ch for ch, _p in last}) < 12:
        fails.append(f"only {len({ch for ch, _p in last})} voices hold the "
                     f"final chord to the end")
    if any(p % 12 not in (0, 3, 7) for _ch, p in last):
        fails.append("the final chord is not C minor")
    if not any(p % 12 == 0 and ch == CB for ch, p in last):
        fails.append("the basses do not end on C")
    return fails


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("form_scherzo_trio_scherzo_coda", _o_form(sc)))
    results.append(("trio_quieter_and_major", _o_trio_quieter(sc)))
    results.append(("scherzo_return_bigger", _o_return_bigger(sc)))
    results.append(("hymn_quoted_by_horns", _o_hymn_in_horns(sc)))
    results.append(("hemiolas_at_cadences", _o_hemiolas(sc)))
    results.append(("leading_tone_at_cadences", _o_leading_tone(sc)))
    results.append(("one_in_a_bar_grid", _o_one_in_a_bar(sc)))
    results.append(("beam_brass_and_basses", _o_beam_voices(sc)))
    results.append(("trio_counterpoint", _o_counterpoint(sc)))
    results.append(("coda_presses_home", _o_coda_presses(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def level(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    first = level(S1_A1 + 3.0, S1_A1 + 45.0)
    back = level(S2_A1 + 3.0, S2_A1 + 45.0)
    last = level(S2_A2 + 3.0, S2_A2 + 45.0)
    trio = level(T_A + 6.0, T_H2 + 18.0)
    coda = level(C2 + 3.0, C4 - 3.0)

    hush = []
    if trio > back - 6.0 or trio > first - 3.0:
        hush.append(f"trio {trio:.1f} dB must sit 6 dB under the scherzo's "
                    f"return ({back:.1f}) and 3 dB under its first "
                    f"statement ({first:.1f})")
    if trio < -60.0:
        hush.append(f"trio is inaudible ({trio:.1f} dB)")
    bigger = []
    if back < first + 0.5:
        bigger.append(f"returning theme {back:.1f} dB is not above its "
                      f"first statement {first:.1f} dB")
    if last < first + 0.5:
        bigger.append(f"final theme {last:.1f} dB is not above the first "
                      f"statement {first:.1f} dB")
    peak = []
    if coda < first + 0.5:
        peak.append(f"coda {coda:.1f} dB is not above the first theme "
                    f"{first:.1f} dB")
    if coda < trio + 9.0:
        peak.append(f"coda {coda:.1f} dB is not 9 dB over the trio "
                    f"{trio:.1f} dB")
    return [("audio_trio_is_the_hush", hush),
            ("audio_return_is_bigger", bigger),
            ("audio_coda_is_the_peak", peak)]
