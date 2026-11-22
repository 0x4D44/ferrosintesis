"""t10_last_lighting.py — track 10 of *Lantern Year*: "Last Lighting".

December; the finale.  The year closes as it opened: the LAMP bell alone,
then the BEAM on an unaccompanied piano.  The keeper's HYMN is stated
complete and quietly in D dorian on the cathedral organ; a second theme
("the year remembered") sings in the cello and violins; the band gathers;
the BEAM climbs D - F - G - A as a brass call and the mode TURNS on a
dominant pedal.  The key signature becomes D major and the HYMN is crowned
complete in D ionian, tutti, under a lead-guitar descant that is consonant
on every bar line.  The second theme returns transfigured into the major,
an Amen, a last BEAM climbing four octaves from the bass to the top of the
piano, one great chord - and the LAMP bell, alone.

HLD: COMPOSER-NOTES.md section 7, T10.
"""

from __future__ import annotations

import sys

import conductor
import engine as en
import material

NUMBER = 10
TITLE = "Last Lighting"
FILE = "10 - Last Lighting.mid"
SEED = 20261210
COMMENT = ("Last Lighting: the December finale of Lantern Year.  The lamp "
           "bell alone, the BEAM on solo piano, the keeper's hymn quietly "
           "in D dorian on the cathedral organ, a second theme, a build "
           "on the BEAM that turns the mode, the hymn crowned in D major "
           "by the whole band under a guitar descant, the BEAM climbing "
           "four octaves, and the lamp bell alone again.")

DOR, ION = "dorian", "ionian"
D4 = material.LAMP_PITCH                      # 62 — the tonic all year

(PNO, ORG, ORGM, CHOIR, VLN, STR, VC, HRN, BRS, DR, TIMP, TPT, HARP, GTR,
 BASS, BELL) = range(16)

# ---------------------------------------------------------------------------
# The grid (beats are quarter notes; every bar is 4/4)
# ---------------------------------------------------------------------------

T_LAMP = 0.0        # I    the lamp bell, the BEAM, a piano prelude
T_HYMN = 40.0       # II   the hymn, D dorian, organ, quiet (16 bars)
T_YEAR = 104.0      # III  second theme: cello, then violins + horn
T_GATH = 168.0      # IV   half the hymn (horns), then the guitar's verse
T_TURN = 232.0      # V    the BEAM on D-F-G-A, then a dominant pedal
T_CROWN = 280.0     # VI   the hymn, D ionian, tutti, with the descant
T_GLOW = 344.0      # VII  second theme in the major; Amen
T_BEAM = 392.0      # VIII the last BEAM, four octaves; the final chord
T_FINAL = 408.0     #      (the final chord)
T_ALONE = 424.0     # IX   the lamp bell alone
END = 440.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("I. The Lamp", T_LAMP, T_HYMN),
        ("II. The Keeper's Hymn", T_HYMN, T_YEAR),
        ("III. The Year Remembered", T_YEAR, T_GATH),
        ("IV. Gathering", T_GATH, T_TURN),
        ("V. The Turning", T_TURN, T_CROWN),
        ("VI. The Crown", T_CROWN, T_GLOW),
        ("VII. Afterglow", T_GLOW, T_BEAM),
        ("VIII. The Last Beam", T_BEAM, T_ALONE),
        ("IX. The Lamp Alone", T_ALONE, END),
    ],
    tempo_map=[(0.0, 88), (T_YEAR, 90), (T_GATH, 92), (248.0, 93),
               (256.0, 94), (264.0, 95), (272.0, 96), (T_GLOW, 92),
               (376.0, 88), (T_FINAL, 76), (T_ALONE, 66)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 1), (T_CROWN, 2, 0)],
    channels=[
        (PNO, "piano", 0, 90, 54, 48),
        (ORG, "cathedral organ - solo", 19, 106, 64, 60),
        (ORGM, "cathedral organ - manuals and pedal", 19, 90, 64, 60),
        (CHOIR, "choir", 52, 108, 60, 70),
        (VLN, "violins", 48, 118, 48, 62),
        (STR, "low strings", 49, 104, 76, 62),
        (VC, "cello", 42, 116, 64, 55),
        (HRN, "horns", 60, 100, 64, 60),
        (BRS, "brass section", 61, 118, 78, 55),
        (DR, "kit", 0, 100, 64, 35),
        (TIMP, "timpani", 47, 100, 76, 55),
        (TPT, "trumpet", 56, 116, 64, 55),
        (HARP, "harp", 46, 124, 46, 55),
        (GTR, "lead guitar", 29, 127, 64, 50),
        (BASS, "bass", 33, 72, 64, 25),
        (BELL, "lamp bell", material.LAMP_PROGRAM, 112, 64, 70),
    ],
    bank_selects=[(PNO, 2), (ORG, 2), (ORGM, 2), (GTR, 1)],
)

BEAM_CHANNELS = {PNO, HARP, HRN, TPT, GTR, BASS, VC, ORG}
PROGRAM_WHITELIST = {0, 19, 52, 48, 49, 42, 60, 61, 47, 56, 46, 29, 33,
                     material.LAMP_PROGRAM}
CENTERED_CHANNELS = {ORG, ORGM, VC, HRN, DR, TPT, GTR, BASS, BELL}
NOTE_RANGES = {
    PNO: (26, 98), ORG: (60, 91), ORGM: (36, 79), CHOIR: (55, 81),
    VLN: (55, 93), STR: (48, 76), VC: (36, 69), HRN: (48, 79),
    BRS: (48, 72), TIMP: (40, 53), TPT: (60, 84), HARP: (38, 96),
    GTR: (62, 91), BASS: (33, 55), BELL: (62, 62),
}
GAP_WHITELIST = [(T_ALONE - 6.0, T_ALONE + 0.5)]   # the breath before the bell
BEND_EXEMPT: set = set()
DURATION_WINDOW = (294.0, 302.0)
BOUNDS_WHITELIST: list = []

# ---------------------------------------------------------------------------
# Material of this track
# ---------------------------------------------------------------------------

CHORDS = {
    "Dm": "D F A", "C": "C E G", "G": "G B D", "F": "F A C",
    "Em": "E G B", "Em7": "E G B D", "Am": "A C E", "Asus": "A D E",
    "Fmaj7": "F A C E",
    "D": "D F# A", "A": "A C# E", "A7": "A C# E G", "Bm": "B D F#",
    "Bm7": "B D F# A", "F#m": "F# A C#",
}

# The second theme, "the year remembered" (written in octave 4).
THEME_A = [
    ("A4", 0, 1.5), ("G4", 1.5, .5), ("F4", 2, 1), ("A4", 3, 1),
    ("C5", 4, 2), ("B4", 6, 1), ("G4", 7, 1),
    ("B4", 8, 1.5), ("A4", 9.5, .5), ("G4", 10, 1), ("B4", 11, 1),
    ("D5", 12, 2), ("A4", 14, 2),
    ("C5", 16, 1.5), ("A4", 17.5, .5), ("F4", 18, 1), ("A4", 19, 1),
    ("G4", 20, 2), ("E4", 22, 1), ("G4", 23, 1),
    ("B4", 24, 1.5), ("A4", 25.5, .5), ("G4", 26, 1), ("E4", 27, 1),
    ("D4", 28, 2), ("E4", 30, 2),
]
THEME_B = [x for x in THEME_A if x[1] < 16] + [
    ("A4", 16, 1.5), ("C5", 17.5, .5), ("F5", 18, 1), ("E5", 19, 1),
    ("D5", 20, 2), ("B4", 22, 1), ("G4", 23, 1),
    ("C5", 24, 1.5), ("B4", 25.5, .5), ("A4", 26, 1), ("E4", 27, 1),
    ("D4", 28, 4),
]
SEQ_A = [("Dm", 4), ("C", 4), ("G", 4), ("Dm", 4),
         ("F", 4), ("C", 4), ("Em7", 4), ("Asus", 2), ("Am", 2)]
LOW_A = ["D2", "C2", "B1", "A1", "F2", "E2", "E2", "A1", "A1"]
SEQ_B = [("Dm", 4), ("C", 4), ("G", 4), ("Dm", 4),
         ("F", 4), ("G", 4), ("Am", 4), ("Dm", 4)]
LOW_B = ["D2", "C2", "B1", "A1", "F2", "G2", "A1", "D2"]

# The horn's counter-melody to THEME_B: it moves where the theme holds.
HORN_CTR = [
    ("D4", 0, 2), ("F4", 2, 2),
    ("E4", 4, 1), ("F4", 5, 1), ("G4", 6, 2),
    ("D4", 8, 2), ("G4", 10, 2),
    ("F4", 12, 1), ("E4", 13, 1), ("F4", 14, 1), ("A4", 15, 1),
    ("F4", 16, 2), ("A4", 18, 2),
    ("G4", 20, 1), ("A4", 21, 1), ("D4", 22, 2),
    ("E4", 24, 2), ("C4", 26, 1), ("E4", 27, 1),
    ("F4", 28, 1), ("E4", 29, 1), ("F4", 30, 2),
]

# The hymn's harmony in D dorian (one chord a bar, Fmaj7 colouring bar 14).
HYMN_DOR = [("Dm", 4), ("G", 4), ("Dm", 4), ("G", 4),
            ("G", 4), ("Em", 4), ("Dm", 4), ("Am", 4),
            ("Dm", 4), ("G", 4), ("Dm", 4), ("G", 4),
            ("Dm", 4), ("Am", 2), ("Fmaj7", 2), ("Am", 4), ("Dm", 4)]
PEDAL_DOR = [
    ("D3", 0, 4), ("G2", 4, 4), ("D3", 8, 2), ("C3", 10, 2), ("B2", 12, 4),
    ("G2", 16, 4), ("E2", 20, 4), ("F2", 24, 4), ("A2", 28, 4),
    ("D3", 32, 4), ("G2", 36, 2), ("B2", 38, 2), ("D3", 40, 2),
    ("A2", 42, 2), ("G2", 44, 4),
    ("F2", 48, 4), ("A2", 52, 2), ("F2", 54, 2), ("E2", 56, 2),
    ("A2", 58, 2), ("D2", 60, 4),
]

# The crown: the hymn re-harmonised in D major, and its walking bass.
CROWN_PROG = [
    ("D", 2), ("D", 2), ("G", 2), ("A", 2),
    ("D", 2), ("Bm", 1), ("A", 1), ("G", 2), ("D", 2),
    ("G", 2), ("A", 2), ("Bm", 2), ("Em7", 2),
    ("D", 2), ("G", 2), ("Asus", 2), ("A", 2),
    ("D", 2), ("D", 2), ("G", 2), ("A", 2),
    ("D", 2), ("F#m", 1), ("A", 1), ("G", 2), ("Em7", 2),
    ("D", 2), ("G", 2), ("A", 2), ("D", 2),
    ("A7", 4), ("D", 4),
]
CROWN_BASS_BARS = [
    "D2 D3 F#2 A2", "G2 B2 A2 C#3", "D3 A2 B2 C#3", "G2 B2 F#2 D2",
    "G2 D3 A2 E3", "B2 F#2 E2 G2", "F#2 A2 G2 B2", "A2 E2 A2 C#3",
    "D2 D3 F#2 A2", "G2 B2 A2 C#3", "D3 A2 F#2 A2", "G2 B2 E2 G2",
    "F#2 D2 G2 B2", "A2 E3 A2 A2", "A2 E3 C#3 A2", "D2:2 A2 D2",
]

# The descant (lead guitar): above the tune, moving where the tune holds.
DESCANT = [
    ("A5", 0, 3), ("B5", 3, 1),
    ("D6", 4, 2), ("C#6", 6, 1), ("A5", 7, 1),
    ("A5", 8, 2), ("B5", 10, 1), ("E6", 11, 1),
    ("D6", 12, 2), ("B5", 14, .5), ("A5", 14.5, .5), ("F#5", 15, 1),
    ("B5", 16, 2), ("C#6", 18, 2),
    ("D6", 20, 2), ("E6", 22, 1), ("B5", 23, 1),
    ("A5", 24, 2), ("B5", 26, 1), ("D6", 27, 1),
    ("A5", 28, 1), ("D6", 29, 1), ("C#6", 30, 1), ("E6", 31, 1),
    ("A5", 32, 2), ("F#5", 34, 1), ("A5", 35, 1),
    ("B5", 36, 2), ("C#6", 38, 2),
    ("D6", 40, 3), ("E6", 43, 1),
    ("B5", 44, 2), ("D6", 46, 1), ("E6", 47, 1),
    ("F#6", 48, 2), ("E6", 50, 1), ("D6", 51, 1),
    ("C#6", 52, 2), ("D6", 54, 2),
    ("C#6", 56, 2), ("B5", 58, 1), ("E6", 59, 1),
    ("D6", 60, 4),
]

GLOW_PROG = [("D", 4), ("A", 4), ("G", 4), ("D", 4), ("F#m", 4), ("A7", 4),
             ("G", 2), ("Em7", 2), ("Asus", 2), ("A7", 2)]
GLOW_BASS = ["D3", "C#3", "B2", "A2", "F#2", "E2", "G2", "E2", "A2", "A2"]
AMEN_PROG = [("G", 4), ("D", 4), ("Em7", 2), ("Asus", 2), ("A7", 4)]
AMEN_BASS = ["G2", "F#2", "E2", "A2", "A2"]

BEAM_STEPS = [0, 7, 9, 7, 12]        # 1-5-6-5-8 with the major sixth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pcs(name: str) -> list:
    return [en.n(tok + "4") % 12 for tok in CHORDS[name].split()]


def _major(notes: list) -> list:
    """The dorian theme transfigured: F -> F#, C -> C#."""
    out = []
    for name, s, d in notes:
        if name[0] in "FC" and "#" not in name:
            name = name[0] + "#" + name[1:]
        out.append((name, s, d))
    return out


def _mel(sc, ch, t0, notes, vel, vel_end=None, tr=0, gate=0.97, jt=4, jv=4):
    span = max(s + d for _n, s, d in notes)
    for name, s, d in notes:
        v = vel if vel_end is None else en.lerp(vel, vel_end, s / span)
        sc.note(ch, en.n(name) + tr, t0 + s, d * gate, int(round(v)),
                jt=(0 if s == 0 else jt), jv=jv)


def _voicings(prog, size, lo, hi):
    out, prev = [], None
    for name, _d in prog:
        prev = en.voice_lead(_pcs(name), prev, size, lo, hi)
        out.append(prev)
    return out


def _starts(prog):
    out, t = [], 0.0
    for _n, d in prog:
        out.append(t)
        t += d
    return out, t


def _pad(sc, ch, t0, prog, size, lo, hi, vel, vel_end=None, tie=True,
         gate=0.98):
    """Voice-led sustained chords; with tie, common tones are held."""
    vs = _voicings(prog, size, lo, hi)
    starts, total = _starts(prog)
    for i, v in enumerate(vs):
        for p in v:
            if tie and i > 0 and p in vs[i - 1]:
                continue
            j = i
            if tie:
                while j + 1 < len(vs) and p in vs[j + 1]:
                    j += 1
            dur = starts[j] + prog[j][1] - starts[i]
            vv = vel if vel_end is None else en.lerp(vel, vel_end,
                                                     starts[i] / total)
            sc.note(ch, p, t0 + starts[i], dur * gate, int(round(vv)),
                    jt=(0 if i == 0 else 3), jv=3)
    return vs


def _flow(sc, ch, t0, prog, bass, size, lo, hi, vel, pat=(-1, 0, 1, 2, 1, 2, 1, 0),
          step=0.5, ring=1.6, pedal=False):
    """Broken-chord figuration: the bass note, then chord tones by pattern."""
    vs = _voicings(prog, size, lo, hi)
    starts, _total = _starts(prog)
    for (name, d), v, bname, a in zip(prog, vs, bass, starts):
        if pedal:
            en.sustain(sc, ch, t0 + a + 0.03, t0 + a + d - 0.1)
        for i in range(int(round(d / step))):
            idx = -1 if i == 0 else pat[i % len(pat)]
            p = en.n(bname) if idx < 0 else v[idx % len(v)]
            sc.note(ch, p, t0 + a + i * step, step * ring,
                    vel + (8 if i == 0 else 0), jt=(0 if i == 0 else 3), jv=4)


def _beam(sc, ch, t0, base, step, hold, vel, vel_end):
    """The BEAM in this track's own rhythm: four even notes and an arrival."""
    for i, semis in enumerate(BEAM_STEPS):
        sc.note(ch, base + semis, t0 + i * step,
                hold if i == 4 else step * 0.94,
                int(round(en.lerp(vel, vel_end, i / 4.0))), jt=0, jv=2)


def _gtr(sc, t0, notes, vel, tr=0):
    """Lead-guitar line: held notes get a delayed vibrato and a CC1 bloom."""
    for name, s, d in notes:
        sc.note(GTR, en.n(name) + tr, t0 + s, d * 0.97, vel, jt=0, jv=3)
        if d >= 1.5:
            _sing(sc, t0 + s, d)


def _sing(sc, b, d):
    en.vibrato(sc, GTR, b, d - 0.2, depth=0.16, cycles_per_beat=3.2,
               delay=0.45, step=0.04)
    en.cc_curve(sc, GTR, 1, [(b, 24), (b + d * 0.6, 96), (b + d - 0.1, 60)],
                step=0.25)


def _roll(sc, ch, p, t0, t1, v0, v1, step=0.25):
    n_ = int(round((t1 - t0) / step))
    for i in range(n_):
        sc.note(ch, p, t0 + i * step, step * 0.9,
                int(round(en.lerp(v0, v1, i / max(1, n_ - 1)))), jt=2, jv=3)


def _kit(sc, t, bars, kick, snare, hat_key, hat_step, kv, sv, hv,
         snare_key=38, skip=None):
    """A groove; skip = {bar: beat} leaves that bar empty from the beat on
    (room for a fill)."""
    skip = skip or {}
    per = max(1, int(round(1.0 / hat_step)))
    for b in range(bars):
        o = t + 4.0 * b
        cut = skip.get(b, 4.0)
        for k in kick:
            if k < cut:
                sc.hit(36, o + k, kv)
        for s in snare:
            if s < cut:
                sc.hit(snare_key, o + s, sv)
        for i in range(int(round(4.0 / hat_step))):
            x = i * hat_step
            if x < cut:
                sc.hit(hat_key, o + x, hv + (8 if i % per == 0 else 0))


def _fill(sc, t0, keys, v0, v1, step=0.25):
    for i, k in enumerate(keys):
        sc.hit(k, t0 + i * step,
               int(round(en.lerp(v0, v1, i / max(1, len(keys) - 1)))), jt=2)


def _pool(name, lo, hi):
    pcs = set(_pcs(name))
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


def _sweep(sc, ch, t0, name, count, step, lo, hi, v0, v1, down=False,
           ring=2.0):
    pool = _pool(name, lo, hi)
    if down:
        pool = list(reversed(pool))
    for k in range(count):
        p = pool[int(round(k * (len(pool) - 1) / max(1, count - 1)))]
        sc.note(ch, p, t0 + k * step, step * ring,
                int(round(en.lerp(v0, v1, k / max(1, count - 1)))), jt=2, jv=3)


def _crown_bass() -> list:
    """[(pitch, offset, dur)] of the crown's bass line."""
    out = []
    for bar, text in enumerate(CROWN_BASS_BARS):
        x = 4.0 * bar
        for tok in text.split():
            name, _, d = tok.partition(":")
            dur = float(d) if d else 1.0
            out.append((en.n(name), x, dur))
            x += dur
    return out


def _bass_at(line, off):
    return [p for p, x, d in line if x <= off + 1e-9 < x + d][0]


def _timp(pitch):
    """Fold a bass pitch into the drums' compass (F2..E3)."""
    return 41 + ((pitch % 12 - 5) % 12)


# ---------------------------------------------------------------------------
# I. The Lamp — the bell alone, the BEAM unaccompanied, a piano prelude
# ---------------------------------------------------------------------------

def _b_lamp(sc):
    sc.note(BELL, D4, 0.0, 7.9, 88, jt=0, jv=0)
    en.sustain(sc, PNO, 8.0, 15.9)
    material.play_beam(sc, PNO, 8.0, D4, DOR, stretch=2.0, vel=56,
                       vel_end=72, jv=2)
    sc.note(BELL, D4, 16.0, 7.5, 70, jt=0, jv=0)
    en.expr_curve(sc, STR, [(16.0, 44), (24.0, 76), (34.0, 90), (40.0, 62)])
    sc.note(STR, en.n("D3"), 16.0, 7.9, 40, jt=0)
    sc.note(STR, en.n("A3"), 16.0, 7.9, 38, jt=0)
    material.play_beam(sc, HARP, 18.0, D4 + 12, DOR, stretch=1.5, vel=52,
                       vel_end=64, gate=1.3, jv=2)

    # the prelude: the second theme in embryo, over a D-C-B-A bass
    prelude = [("A4", 0, 1.5), ("G4", 1.5, .5), ("F4", 2, 1), ("A4", 3, 1),
               ("C5", 4, 2), ("B4", 6, 1), ("G4", 7, 1),
               ("B4", 8, 1.5), ("A4", 9.5, .5), ("G4", 10, 1), ("E4", 11, 1),
               ("A4", 12, 3.6)]
    prog = [("Dm", 4), ("C", 4), ("G", 2), ("Em", 2), ("Am", 4)]
    _mel(sc, PNO, 24.0, prelude, 64, 72)
    _flow(sc, PNO, 24.0, prog, ["D2", "C2", "B1", "E2", "A1"], 3, 50, 62, 42,
          pedal=True)
    en.expr_curve(sc, VC, [(24.0, 56), (32.0, 88), (40.0, 60)])
    _mel(sc, VC, 24.0, [("D3", 0, 4), ("C3", 4, 4), ("B2", 8, 2),
                        ("E3", 10, 2), ("A2", 12, 3.9)], 52, jt=3)
    _pad(sc, STR, 24.0, prog, 3, 50, 64, 40)


# ---------------------------------------------------------------------------
# II. The Keeper's Hymn — complete, D dorian, quiet, on the organ
# ---------------------------------------------------------------------------

def _b_hymn(sc):
    t = T_HYMN
    en.expr_curve(sc, ORG, [(t, 88), (t + 32, 94), (t + 44, 106),
                            (t + 64, 86)], step=2.0)
    material.play_hymn(sc, ORG, t, D4, DOR, vel=60, vel_end=68, gate=0.98,
                       jv=2)
    sc.cc(ORGM, 11, 68, t)
    _pad(sc, ORGM, t, HYMN_DOR, 3, 53, 67, 46)
    _mel(sc, ORGM, t, PEDAL_DOR, 50, jt=3)

    # the harp marks the bar lines of phrase 2, then walks in quarters
    hv = _voicings(HYMN_DOR[4:8], 4, 52, 74)
    for i, v in enumerate(hv):
        en.strum(sc, HARP, v, t + 16 + 4 * i, 3.5, 60, spread=0.05)
    _flow(sc, HARP, t + 32, HYMN_DOR[8:],
          ["D3", "G2", "D3", "G2", "D3", "A2", "F2", "A2", "D2"],
          3, 57, 76, 62, pat=(-1, 0, 1, 2), step=1.0, ring=1.8)

    # phrase 3: the strings and a humming choir come in under the climb
    en.expr_curve(sc, STR, [(t + 32, 44), (t + 42, 94), (t + 48, 72),
                            (t + 58, 84), (t + 64, 52)])
    _pad(sc, STR, t + 32, HYMN_DOR[8:], 3, 55, 70, 42)
    en.vowel_curve(sc, CHOIR, [(t + 32, 0), (t + 44, 52), (t + 64, 16)],
                   step=1.0)
    en.expr_curve(sc, CHOIR, [(t + 32, 54), (t + 44, 96), (t + 64, 60)])
    _pad(sc, CHOIR, t + 32, HYMN_DOR[8:], 3, 57, 72, 40)

    # phrase 4: a tenor line in the cello
    en.expr_curve(sc, VC, [(t + 48, 62), (t + 56, 92), (t + 64, 60)])
    _mel(sc, VC, t + 48, [("A3", 0, 2), ("D4", 2, 2), ("C4", 4, 2),
                          ("A3", 6, 2), ("C4", 8, 1), ("B3", 9, 1),
                          ("A3", 10, 2), ("A3", 12, 3.8)], 56)


# ---------------------------------------------------------------------------
# III. The Year Remembered — the second theme
# ---------------------------------------------------------------------------

def _b_year(sc):
    t = T_YEAR
    # strain 1: the cello alone over the piano
    en.expr_curve(sc, VC, [(t, 76), (t + 6, 106), (t + 14, 88),
                           (t + 22, 114), (t + 30, 84), (t + 32, 92)])
    _mel(sc, VC, t, THEME_A, 80, 88, tr=-12)
    _flow(sc, PNO, t, SEQ_A, LOW_A, 3, 55, 69, 42, pedal=True)
    en.expr_curve(sc, STR, [(t, 52), (t + 16, 78), (t + 32, 66)], step=2.0)
    _pad(sc, STR, t, SEQ_A, 3, 53, 67, 40)

    # strain 2: violins and cello in octaves; the horn answers
    u = t + 32
    en.expr_curve(sc, VLN, [(u, 86), (u + 6, 106), (u + 16, 98),
                            (u + 18, 120), (u + 26, 102), (u + 32, 80)])
    _mel(sc, VLN, u, THEME_B, 98, 106, jt=0)
    en.expr_curve(sc, VC, [(u, 86), (u + 18, 112), (u + 32, 76)])
    _mel(sc, VC, u, THEME_B, 74, 80, tr=-12)
    en.expr_curve(sc, HRN, [(u, 74), (u + 12, 96), (u + 18, 108),
                            (u + 32, 72)])
    _mel(sc, HRN, u, HORN_CTR, 62, 68, jt=0)
    _flow(sc, PNO, u, SEQ_B, LOW_B, 3, 55, 69, 46, pedal=True)
    en.expr_curve(sc, STR, [(u, 66), (u + 18, 96), (u + 32, 64)], step=2.0)
    _pad(sc, STR, u, SEQ_B, 3, 53, 67, 48)
    en.vowel_curve(sc, CHOIR, [(u, 40), (u + 18, 72), (u + 32, 45)], step=1.0)
    en.expr_curve(sc, CHOIR, [(u, 60), (u + 18, 100), (u + 32, 62)])
    _pad(sc, CHOIR, u, SEQ_B, 3, 57, 72, 44)
    hv = _voicings(SEQ_B, 4, 57, 81)
    for i, v in enumerate(hv):
        en.strum(sc, HARP, v, u + 4 * i, 1.9, 76, spread=0.04)
        en.strum(sc, HARP, v, u + 4 * i + 2, 1.9, 66, spread=0.04,
                 down=False)
    _mel(sc, BASS, u, [
        ("D2", 0, 3), ("A2", 3, 1), ("C3", 4, 3), ("G2", 7, 1),
        ("B2", 8, 3), ("G2", 11, 1), ("A2", 12, 2), ("A2", 14, 1),
        ("G2", 15, 1), ("F2", 16, 3), ("C3", 19, 1), ("G2", 20, 3),
        ("B2", 23, 1), ("A2", 24, 2), ("E2", 26, 1), ("A2", 27, 1),
        ("D2", 28, 3.9)], 62)
    sc.hit(51, u, 40)
    sc.hit(51, u + 16, 48)


# ---------------------------------------------------------------------------
# IV. Gathering — half the hymn in the horns, then the guitar's verse
# ---------------------------------------------------------------------------

def _b_gathering(sc):
    t = T_GATH
    half = HYMN_DOR[:8]
    en.expr_curve(sc, HRN, [(t, 96), (t + 8, 114), (t + 16, 100),
                            (t + 26, 116), (t + 32, 96)])
    material.play_phrase(sc, HRN, t, D4, DOR, 0, vel=84, vel_end=90)
    material.play_phrase(sc, HRN, t + 16, D4, DOR, 1, vel=88, vel_end=84)
    en.expr_curve(sc, VC, [(t, 84), (t + 14, 104), (t + 32, 88)])
    _mel(sc, VC, t, [
        ("F3", 0, 1), ("A3", 1, 1), ("D4", 2, 1), ("C4", 3, 1),
        ("B3", 4, 2), ("D4", 6, 1), ("B3", 7, 1),
        ("A3", 8, 1), ("F3", 9, 1), ("A3", 10, 1), ("C4", 11, 1),
        ("B3", 12, 1), ("D4", 13, 1), ("G3", 14, 2),
        ("D4", 16, 2), ("B3", 18, 1), ("G3", 19, 1),
        ("E3", 20, 1), ("G3", 21, 1), ("B3", 22, 2),
        ("A3", 24, 2), ("D4", 26, 2),
        ("C4", 28, 1), ("B3", 29, 1), ("A3", 30, 1), ("E3", 31, 1)], 72)
    _flow(sc, PNO, t, half, ["D2", "G2", "D2", "B1", "G2", "E2", "F2", "A1"],
          3, 55, 69, 52, pedal=True)
    _mel(sc, BASS, t, [
        ("D2", 0, 2), ("A2", 2, 1), ("D3", 3, 1),
        ("G2", 4, 2), ("B2", 6, 1), ("D3", 7, 1),
        ("D3", 8, 2), ("C3", 10, 1), ("A2", 11, 1),
        ("G2", 12, 2), ("G2", 14, 1), ("A2", 15, 1),
        ("G2", 16, 2), ("B2", 18, 2),
        ("E2", 20, 2), ("G2", 22, 1), ("B2", 23, 1),
        ("F2", 24, 2), ("D2", 26, 2),
        ("A2", 28, 2), ("E2", 30, 1), ("A2", 31, 1)], 72)
    _kit(sc, t, 8, (0, 2.5), (1, 3), 51, 1.0, 62, 46, 40, snare_key=37)
    en.expr_curve(sc, STR, [(t, 70), (t + 32, 92)], step=2.0)
    _pad(sc, STR, t, half, 3, 53, 67, 50)
    en.vowel(sc, CHOIR, 45, t)
    en.expr_curve(sc, CHOIR, [(t, 66), (t + 32, 90)], step=2.0)
    _pad(sc, CHOIR, t, half, 3, 57, 72, 46)
    en.expr_curve(sc, VLN, [(t + 16, 60), (t + 28, 100), (t + 32, 84)])
    _mel(sc, VLN, t + 16, [("D5", 0, 4), ("E5", 4, 4), ("F5", 8, 4),
                           ("E5", 12, 3.9)], 58, jt=3)
    hv = _voicings(half, 4, 57, 79)
    for i, v in enumerate(hv):
        en.strum(sc, HARP, v, t + 4 * i, 3.0, 70, spread=0.04)

    # the guitar sings the second theme; violins take the counter-melody
    u = t + 32
    _gtr(sc, u, THEME_A, 100, tr=12)
    en.bend_ramp(sc, GTR, u + 11.95, u + 12.25, -1.0, 0.0, steps=6)
    counter = [(nm, s, d) for nm, s, d in HORN_CTR if s < 16]
    en.expr_curve(sc, VLN, [(u, 84), (u + 14, 108), (u + 22, 116),
                            (u + 32, 96)])
    _mel(sc, VLN, u, counter, 78, 84, tr=12, jt=3)
    _mel(sc, VLN, u, [("A4", 16, 2), ("C5", 18, 2), ("C5", 20, 1),
                      ("D5", 21, 1), ("E5", 22, 2), ("D5", 24, 2),
                      ("B4", 26, 2), ("A4", 28, 2), ("C5", 30, 2)], 84, jt=3)
    en.expr_curve(sc, HRN, [(u, 84), (u + 22, 108), (u + 32, 96)], step=2.0)
    _mel(sc, HRN, u, [("A3", 0, 4), ("G3", 4, 4), ("B3", 8, 4),
                      ("A3", 12, 4), ("C4", 16, 4), ("C4", 20, 2),
                      ("E4", 22, 2), ("D4", 24, 4), ("D4", 28, 2),
                      ("E4", 30, 2)], 72, jt=3)
    sc.cc(ORGM, 11, 92, u)
    _pad(sc, ORGM, u, SEQ_A, 3, 55, 69, 56)
    en.expr_curve(sc, STR, [(u, 84), (u + 22, 108), (u + 32, 100)], step=2.0)
    _pad(sc, STR, u, SEQ_A, 3, 53, 67, 58)
    en.vowel_curve(sc, CHOIR, [(u, 45), (u + 24, 84), (u + 32, 70)], step=1.0)
    en.expr_curve(sc, CHOIR, [(u, 80), (u + 24, 108), (u + 32, 96)], step=2.0)
    _pad(sc, CHOIR, u, SEQ_A, 3, 57, 72, 54)
    _flow(sc, PNO, u, SEQ_A, LOW_A, 3, 55, 69, 58)
    hv = _voicings(SEQ_A, 4, 57, 81)
    starts, _tot = _starts(SEQ_A)
    for v, a in zip(hv, starts):
        en.strum(sc, HARP, v, u + a, 1.9, 74, spread=0.04)
    _mel(sc, BASS, u, [
        (nm, float(i), 1.0) for i, nm in enumerate(
            "D2 A2 D3 A2 C3 G2 C3 G2 B2 D3 G2 B2 A2 D3 A2 G2 "
            "F2 C3 F2 A2 E2 G2 C3 G2 E2 B2 E3 D3 A2 A2 A2 E2".split())],
        82, jt=3)
    sc.hit(49, u, 84)
    _kit(sc, u, 7, (0, 1.5, 2), (1, 3), 42, 0.5, 86, 78, 52)
    o = u + 28
    sc.hit(36, o, 88)
    sc.hit(38, o + 1, 82)
    sc.hit(36, o + 2, 90)
    _fill(sc, o + 2.5, [48, 48, 45, 45, 43, 41], 72, 100)
    _roll(sc, TIMP, 45, o, o + 4, 38, 92)


# ---------------------------------------------------------------------------
# V. The Turning — the BEAM on D, F, G, A; then the dominant pedal
# ---------------------------------------------------------------------------

def _b_turning(sc):
    t = T_TURN
    units = [
        ("Dm", "D2", [(HRN, 62, 5.5)]),
        ("F", "F2", [(TPT, 65, 5.5)]),
        ("G", "G2", [(TPT, 67, 5.5), (HRN, 55, 5.5)]),
        ("A", "A2", [(TPT, 69, 5.5), (HRN, 57, 5.5), (GTR, 69, 13.6)]),
    ]
    prog = [(u[0], 8) for u in units]
    brs_v = _voicings(prog, 4, 50, 67)
    org_v = _voicings(prog, 4, 55, 74)
    str_v = _voicings(prog, 3, 53, 67)
    chr_v = _voicings(prog, 3, 60, 76)
    pno_v = _voicings(prog, 4, 57, 76)
    held = ["A4", "A5", "D6", "E6"]
    runs = ["G4 A4 B4 C5 D5 E5 F5 G5", "C5 D5 E5 F5 G5 A5 B5 C6",
            "D5 E5 F5 G5 A5 B5 C6 D6", "C#5 D5 E5 F#5 G5 A5 B5 C#6"]
    walks = [
        "D2 D2 D2 D2 D2 D2 D2 D2 D2 D2 D2 D2 C2 D2 E2 E2",
        "F2 F2 F2 F2 F2 F2 F2 F2 F2 F2 F2 F2 C3 A2 F2 F2",
        "G2 G2 G2 G2 G2 G2 G2 G2 G2 G2 G2 G2 D3 B2 G2 G2",
        "A2 A2 A2 A2 A2 A2 A2 A2 A2 A2 A2 A2 E3 C#3 A2 A2"]
    for i, (name, root, beams) in enumerate(units):
        o = t + 8.0 * i
        for ch in (BRS, STR, CHOIR, VC, HRN, TPT, VLN):
            en.expr_curve(sc, ch, [(o, 68 + 6 * i), (o + 2, 80 + 6 * i),
                                   (o + 7.5, 94 + 7 * i)], step=0.5)
        sc.cc(ORGM, 11, 78 + 10 * i, o)
        en.vowel(sc, CHOIR, [45, 70, 100, 112][i], o)
        for ch, base, hold in beams:
            _beam(sc, ch, o, base, 0.5, hold, 92 + 4 * i, 102 + 4 * i)
            if ch == GTR:
                _sing(sc, o + 2, hold)
        if i == 1:
            sc.note(HRN, 60, o, 7.5, 80, jt=0)
        if i == 2:
            sc.note(GTR, 74, o + 2, 5.5, 98, jt=0)
            _sing(sc, o + 2, 5.5)
        for p in brs_v[i]:
            sc.note(BRS, p, o + 2, 5.6, 76 + 7 * i, jt=2)
        for p in org_v[i]:
            sc.note(ORGM, p, o, 7.9, 58 + 6 * i, jt=0)
        sc.note(ORGM, en.n(root), o, 7.9, 62 + 6 * i, jt=0)
        for p in str_v[i]:
            sc.note(STR, p, o, 7.9, 54 + 6 * i, jt=0)
        for p in chr_v[i]:
            sc.note(CHOIR, p, o, 7.8, 50 + 9 * i, jt=0)
        sc.note(VC, en.n(root), o, 7.9, 78 + 4 * i, jt=0)
        for k, nm in enumerate(walks[i].split()):
            sc.note(BASS, en.n(nm), o + 0.5 * k, 0.45,
                    56 + 6 * i + (8 if k % 2 == 0 else 0), jt=2)
        tp = _timp(en.n(root))
        for x, v in ((0, 88), (1.5, 70), (2, 96), (4, 80), (6, 80),
                     (7, 76), (7.5, 86)):
            sc.note(TIMP, tp, o + x, 0.4, v - 14 + 6 * i, jt=2)
        # kit: a crash on the call, a march under the answer
        sc.hit(49, o, 78 + 6 * i)
        sc.hit(36, o, 78 + 5 * i)
        sc.hit(36, o + 2, 78 + 5 * i)
        sc.hit(45, o + 3, 66 + 6 * i)
        sc.hit(43, o + 3.5, 70 + 6 * i)
        sc.hit(36, o + 4, 74 + 5 * i)
        sc.hit(38, o + 5, 62 + 7 * i)
        sc.hit(36, o + 6, 74 + 5 * i)
        sc.hit(38, o + 7, 64 + 7 * i)
        sc.hit(38, o + 7.5, 56 + 7 * i)
        sc.hit(38, o + 7.75, 70 + 7 * i)
        for k in range(1, 16):
            sc.hit(42, o + 0.5 * k, 40 + 3 * i + (8 if k % 2 == 0 else 0))
        # piano: the bass octave, the chord on the arrival, a hammered answer
        sc.note(PNO, en.n(root), o, 1.8, 72 + 5 * i, jt=0)
        sc.note(PNO, en.n(root) + 12, o, 1.8, 70 + 5 * i, jt=0)
        for p in pno_v[i]:
            sc.note(PNO, p, o + 2, 1.8, 66 + 6 * i, jt=2)
        for k in range(8):
            for p in pno_v[i]:
                sc.note(PNO, p, o + 4 + 0.5 * k, 0.42,
                        int(en.lerp(48 + 5 * i, 70 + 5 * i, k / 7.0)), jt=2)
        _sweep(sc, HARP, o + 6, name, 8, 0.25, 57, 93, 74, 100)
        sc.note(VLN, en.n(held[i]), o, 3.5, 70 + 5 * i, jt=0)
        for k, nm in enumerate(runs[i].split()):
            sc.note(VLN, en.n(nm), o + 4 + 0.5 * k, 0.48,
                    int(en.lerp(66 + 6 * i, 84 + 6 * i, k / 7.0)), jt=2)

    # the dominant pedal: Asus4 for two bars, A7 for two — the mode has turned
    p = t + 32
    ped = [("Asus", 8), ("A7", 8)]
    for ch in (BRS, STR, CHOIR, VC, HRN, TPT, VLN):
        en.expr_curve(sc, ch, [(p, 76), (p + 8, 98), (p + 15.5, 127)],
                      step=0.5)
    en.cc_curve(sc, ORGM, 11, [(p, 90), (p + 15.5, 127)], step=1.0)
    en.vowel(sc, CHOIR, 112, p)
    _roll(sc, TIMP, 45, p, p + 16, 36, 90)
    sc.hit(49, p, 86)
    for k in range(16):
        sc.hit(36, p + k, int(en.lerp(66, 98, k / 15.0)))
    for k in range(16):
        sc.hit(43, p + 0.5 * k, int(en.lerp(42, 80, k / 15.0)))
    _fill(sc, p + 8, [38] * 28, 38, 98)
    _fill(sc, p + 15, [50, 48, 45, 43], 100, 112)
    for k in range(28):
        sc.note(BASS, 45, p + 0.5 * k, 0.45,
                int(en.lerp(60, 92, k / 27.0)) + (6 if k % 2 == 0 else 0),
                jt=2)
    for k, nm in enumerate("A2 A2 B2 C#3".split()):
        sc.note(BASS, en.n(nm), p + 14 + 0.5 * k, 0.45, 104 + k, jt=2)
    _mel(sc, VC, p, [("A2", 0, 7.9), ("A2", 8, 4), ("C#3", 12, 2),
                     ("E3", 14, 1.9)], 92, jt=0)
    _pad(sc, STR, p, ped, 4, 52, 69, 78, 92)
    _pad(sc, ORGM, p, ped, 4, 55, 74, 84, 94)
    sc.note(ORGM, 45, p, 15.9, 90, jt=0)
    _pad(sc, CHOIR, p, ped, 4, 57, 76, 86, 98)
    bv = _voicings(ped, 4, 50, 67)
    for q in bv[0]:
        sc.note(BRS, q, p, 7.8, 74, jt=0)
    fanfare = [(0, 1), (1, .5), (1.5, .5), (2, 1), (3, .5), (3.5, .5),
               (4, 1), (5, 1), (6, 1.9)]
    for k, (x, d) in enumerate(fanfare):
        for q in bv[1]:
            sc.note(BRS, q, p + 8 + x, d * 0.9,
                    int(en.lerp(94, 110, k / 8.0)), jt=2)
    sc.note(TPT, en.n("E5"), p, 7.8, 98, jt=0)
    for k, ((x, d), nm) in enumerate(zip(
            fanfare[:6] + [(4, 1), (5, .5), (5.5, .5), (6, 1.9)],
            "A4 A4 A4 C#5 C#5 C#5 E5 E5 E5 G5".split())):
        sc.note(TPT, en.n(nm), p + 8 + x, d * 0.9,
                int(en.lerp(98, 114, k / 9.0)), jt=0)
    _mel(sc, HRN, p, [("E4", 0, 4), ("D4", 4, 4), ("C#4", 8, 4),
                      ("E4", 12, 2), ("G4", 14, 1.9)], 90, jt=0)
    _mel(sc, VLN, p, [("D6", 0, 4), ("E6", 4, 3.9)], 88, jt=0)
    for k, nm in enumerate(
            "A4 B4 C#5 D5 E5 F#5 G5 A5 B5 C#6 D6 E6".split()):
        sc.note(VLN, en.n(nm), p + 8 + 0.5 * k, 0.48,
                int(en.lerp(84, 108, k / 11.0)), jt=2)
    sc.note(VLN, en.n("F#6"), p + 14, 0.95, 108, jt=0)
    sc.note(VLN, en.n("E6"), p + 15, 0.95, 110, jt=0)
    pv = _voicings(ped, 4, 57, 76)
    for k in range(8):
        for q in pv[0]:
            sc.note(PNO, q, p + k, 0.9, int(en.lerp(52, 70, k / 7.0)), jt=2)
    for k in range(16):
        for q in pv[1]:
            sc.note(PNO, q, p + 8 + 0.5 * k, 0.42,
                    int(en.lerp(54, 82, k / 15.0)), jt=2)
    for k in range(8):
        sc.note(PNO, 33, p + 2 * k, 1.8, 56 + 3 * k, jt=2)
        sc.note(PNO, 45, p + 2 * k, 1.8, 54 + 3 * k, jt=2)
    hv = _voicings(ped, 4, 57, 81)
    en.strum(sc, HARP, hv[0], p, 3.8, 80, spread=0.04)
    en.strum(sc, HARP, hv[0], p + 4, 3.8, 84, spread=0.04)
    en.strum(sc, HARP, hv[1], p + 8, 3.8, 90, spread=0.04)
    gl = [57 + s + 12 * o for o in range(3) for s in (0, 2, 4, 5, 7, 9, 10)]
    for k, q in enumerate(gl[:16]):
        sc.note(HARP, q, p + 12 + 0.25 * k, 0.6,
                int(en.lerp(74, 106, k / 15.0)), jt=2)
    _gtr(sc, p + 8, [("G5", 0, 2), ("A5", 2, 2), ("B5", 4, 2),
                     ("C#6", 6, 1), ("B5", 7, 0.9)], 104)


# ---------------------------------------------------------------------------
# VI. The Crown — the hymn complete in D major, tutti, with the descant
# ---------------------------------------------------------------------------

def _b_crown(sc):
    t = T_CROWN
    for ch in (TPT, HRN, VLN, STR, CHOIR, BRS, VC):
        pts = []
        for k in range(4):
            pts += [(t + 16 * k, 110), (t + 16 * k + 9, 127),
                    (t + 16 * k + 15, 114)]
        pts.append((t + 62, 127))
        en.expr_curve(sc, ch, pts, step=1.0)
    sc.cc(ORG, 11, 127, t)
    sc.cc(ORGM, 11, 127, t)
    en.vowel(sc, CHOIR, 118, t)

    # the tune: trumpet, horns an octave below, organ and violins above
    material.play_hymn(sc, TPT, t, D4, ION, vel=108, vel_end=114,
                       gate=0.97, jv=2)
    material.play_hymn(sc, HRN, t, D4 - 12, ION, vel=100, vel_end=106,
                       gate=0.97, jv=2)
    material.play_hymn(sc, ORG, t, D4 + 12, ION, vel=104, gate=0.99, jv=2)
    material.play_hymn(sc, VLN, t, D4 + 12, ION, vel=100, vel_end=108,
                       gate=0.97, jv=2)
    # the descant
    _gtr(sc, t, DESCANT, 120)

    # the bass line (bass guitar; cello with it), and the organ pedal
    line = _crown_bass()
    for p, x, d in line:
        sc.note(BASS, p, t + x, d * 0.92, 102, jt=0, jv=3)
        sc.note(VC, p, t + x, d * 0.95, 94, jt=0, jv=3)
    starts, _tot = _starts(CROWN_PROG)
    for (name, d), a in zip(CROWN_PROG, starts):
        sc.note(ORGM, _bass_at(line, a), t + a, d * 0.97, 94, jt=0)

    _pad(sc, ORGM, t, CROWN_PROG, 4, 57, 76, 92)
    _pad(sc, CHOIR, t, CROWN_PROG, 4, 60, 79, 96, tie=False, gate=0.95)
    _pad(sc, STR, t, CROWN_PROG, 4, 52, 72, 90)
    _pad(sc, BRS, t, CROWN_PROG, 4, 50, 69, 100, tie=False, gate=0.93)

    # piano: pulsing chords over left-hand octaves; harp: sweeping arpeggios
    pv = _voicings(CROWN_PROG, 3, 62, 79)
    for idx, ((name, d), a, v) in enumerate(zip(CROWN_PROG, starts, pv)):
        low = _bass_at(line, a)
        sc.note(PNO, low, t + a, d * 0.9, 84, jt=0)
        sc.note(PNO, low - 12, t + a, d * 0.9, 82, jt=0)
        for k in range(int(round(d * 2))):
            for q in v:
                sc.note(PNO, q, t + a + 0.5 * k, 0.42,
                        78 if k % 2 == 0 else 66, jt=2)
        _sweep(sc, HARP, t + a, name, int(round(d * 4)), 0.25, 50, 88,
               84, 100, down=(idx % 2 == 1), ring=1.5)

    # timpani: the roots, with rolls into the cadences
    for bar in range(16):
        o = t + 4.0 * bar
        if bar == 7:
            sc.note(TIMP, 45, o, 0.4, 98, jt=0)
            _roll(sc, TIMP, 45, o + 2, o + 4, 64, 104)
        elif bar == 14:
            _roll(sc, TIMP, 45, o, o + 4, 72, 108)
        elif bar == 15:
            sc.note(TIMP, 50, o, 0.4, 112, jt=0)
            _roll(sc, TIMP, 50, o + 0.25, o + 3, 98, 58)
        else:
            sc.note(TIMP, _timp(_bass_at(line, 4.0 * bar)), o, 0.4, 100, jt=0)
            q = _timp(_bass_at(line, 4.0 * bar + 2))
            sc.note(TIMP, q, o + 2, 0.4, 90, jt=2)
            if bar % 2 == 1:
                sc.note(TIMP, q, o + 3.5, 0.2, 72, jt=2)
                sc.note(TIMP, q, o + 3.75, 0.2, 84, jt=2)

    # the kit: closed hats for two phrases, the ride for the climb
    skip = {3: 3.0, 7: 2.0}
    _kit(sc, t, 8, (0, 2, 3.5), (1, 3), 42, 0.5, 104, 100, 62, skip=skip)
    _kit(sc, t + 32, 7, (0, 2, 3.5), (1, 3), 51, 0.5, 106, 102, 66,
         skip={3: 3.0})
    _fill(sc, t + 15, [38, 38, 38, 38], 84, 108)
    _fill(sc, t + 30, [50, 50, 48, 48, 47, 45, 43, 41], 88, 112)
    _fill(sc, t + 47, [38, 38, 48, 45], 88, 110)
    for bar, key, vel in ((0, 49, 110), (4, 49, 104), (8, 49, 110),
                          (10, 57, 108), (12, 49, 108)):
        sc.hit(key, t + 4.0 * bar, vel)
    o = t + 60
    sc.hit(49, o, 112)
    sc.hit(36, o, 108)
    sc.hit(38, o + 1, 98)
    sc.hit(36, o + 2, 104)
    sc.hit(57, o + 2, 96)

    # the lamp tolls on every phrase
    for k in range(4):
        sc.note(BELL, D4, t + 16.0 * k, 12.0, 102, jt=0, jv=0)


# ---------------------------------------------------------------------------
# VII. Afterglow — the second theme in the major; Amen
# ---------------------------------------------------------------------------

def _b_afterglow(sc):
    t = T_GLOW
    theme = _major(THEME_A)
    en.expr_curve(sc, VC, [(t, 84), (t + 6, 108), (t + 14, 90),
                           (t + 22, 110), (t + 32, 80)])
    _mel(sc, VC, t, [x for x in theme if x[1] < 16], 80, tr=-12)
    late = [x for x in theme if x[1] >= 16]
    _mel(sc, VC, t, late, 72, tr=-12)
    en.expr_curve(sc, VLN, [(t + 16, 80), (t + 22, 106), (t + 32, 72)])
    _mel(sc, VLN, t, late, 76)
    en.expr_curve(sc, HRN, [(t + 16, 70), (t + 24, 96), (t + 32, 66)])
    _mel(sc, HRN, t + 16, [("F#4", 0, 2), ("A4", 2, 2), ("E4", 4, 1),
                           ("C#4", 5, 1), ("E4", 6, 2), ("D4", 8, 2),
                           ("B3", 10, 2), ("A3", 12, 1), ("B3", 13, 1),
                           ("C#4", 14, 2)], 62)
    _flow(sc, HARP, t, GLOW_PROG, GLOW_BASS, 3, 57, 76, 60)
    en.expr_curve(sc, STR, [(t, 70), (t + 22, 92), (t + 32, 70)], step=2.0)
    _pad(sc, STR, t, GLOW_PROG, 3, 52, 69, 50)
    en.vowel_curve(sc, CHOIR, [(t, 70), (t + 4, 45), (t + 32, 45),
                               (t + 47, 8)], step=1.0)
    en.expr_curve(sc, CHOIR, [(t, 70), (t + 22, 94), (t + 32, 70),
                              (t + 47, 56)], step=2.0)
    _pad(sc, CHOIR, t, GLOW_PROG, 3, 57, 74, 46)
    sc.cc(ORGM, 11, 76, t)
    starts, _tot = _starts(GLOW_PROG)
    for (name, d), nm, a in zip(GLOW_PROG, GLOW_BASS, starts):
        sc.note(ORGM, en.n(nm), t + a, d * 0.97, 50, jt=0)
    pv = _voicings(GLOW_PROG, 3, 67, 84)
    for (name, d), v, a in zip(GLOW_PROG, pv, starts):
        en.sustain(sc, PNO, t + a + 0.03, t + a + d - 0.1)
        en.strum(sc, PNO, v, t + a, d * 0.9, 48, spread=0.05)

    # Amen
    a0 = t + 32
    sc.cc(GTR, 11, 82, a0)                 # the guitar, far off
    sc.cc(ORGM, 11, 72, a0)
    _pad(sc, ORGM, a0, AMEN_PROG, 3, 57, 72, 52)
    _gtr(sc, a0, [("D6", 0, 2), ("B5", 2, 2), ("A5", 4, 3), ("F#5", 7, 1),
                  ("G5", 8, 2), ("D5", 10, 2), ("C#5", 12, 3.7)], 90)
    en.expr_curve(sc, STR, [(a0, 72), (a0 + 6, 90), (a0 + 16, 66)], step=2.0)
    _pad(sc, STR, a0, AMEN_PROG, 3, 52, 69, 62)
    _pad(sc, CHOIR, a0, AMEN_PROG, 3, 57, 74, 58)
    starts, _tot = _starts(AMEN_PROG)
    hv = _voicings(AMEN_PROG, 4, 55, 79)
    for (name, d), nm, a, v in zip(AMEN_PROG, AMEN_BASS, starts, hv):
        sc.note(ORGM, en.n(nm), a0 + a, d * 0.97, 50, jt=0)
        en.strum(sc, HARP, v, a0 + a, d * 0.9, 68, spread=0.05)
    en.expr_curve(sc, VC, [(a0, 74), (a0 + 6, 92), (a0 + 16, 64)])
    _mel(sc, VC, a0, [("B3", 0, 4), ("A3", 4, 4), ("G3", 8, 2),
                      ("A3", 10, 2), ("G3", 12, 3.8)], 60)
    _roll(sc, TIMP, 45, a0 + 12, a0 + 16, 28, 70)


# ---------------------------------------------------------------------------
# VIII. The Last Beam — four octaves, bass to the top of the piano
# ---------------------------------------------------------------------------

def _b_last_beam(sc):
    t = T_BEAM
    f = T_FINAL
    sc.note(BELL, D4, t, 12.0, 84, jt=0, jv=0)
    en.sustain(sc, PNO, t + 12.0, f + 11.4)
    en.expr_curve(sc, VC, [(t, 80), (f, 94)], step=2.0)
    en.expr_curve(sc, HRN, [(t, 80), (f, 94)], step=2.0)
    climb = [(BASS, 38, 82, 94), (VC, 50, 86, 98), (HRN, 62, 90, 102),
             (PNO, 74, 94, 110)]
    for i, (ch, base, v0, v1) in enumerate(climb):
        hold = 11.0 if i == 3 else f - (t + 4 * i + 4) - 0.15
        _beam(sc, ch, t + 4.0 * i, base, 1.0, hold, v0, v1)
    _beam(sc, HARP, t + 12.0, 74, 1.0, 6.0, 80, 96)

    under = [("D", 4), ("Bm7", 4), ("D", 4), ("D", 4)]
    en.expr_curve(sc, STR, [(t, 66), (f, 92)], step=1.0)
    _pad(sc, STR, t, under, 4, 50, 69, 50, 86, tie=False)
    en.vowel_curve(sc, CHOIR, [(t, 30), (f, 118)], step=1.0)
    en.expr_curve(sc, CHOIR, [(t, 62), (f, 92)], step=1.0)
    _pad(sc, CHOIR, t, under, 4, 57, 76, 48, 88, tie=False)
    en.cc_curve(sc, ORGM, 11, [(t, 76), (f, 94)], step=1.0)
    _pad(sc, ORGM, t, under, 4, 55, 74, 52, 82, tie=False)
    _roll(sc, TIMP, 50, t + 12, f, 40, 104)
    for k in range(8):
        sc.hit(51, t + 12 + 0.5 * k, int(en.lerp(40, 82, k / 7.0)))
    _fill(sc, t + 15, [38, 38, 38, 38], 56, 104)

    # the final chord: D major, everyone, twelve beats, dying away
    ln = 11.5
    for ch in (STR, CHOIR, BRS, HRN, TPT, VLN, VC):
        en.expr_curve(sc, ch, [(f, 90), (f + 5, 90), (f + 11.4, 46)],
                      step=0.5)
    en.cc_curve(sc, ORGM, 11, [(f, 94), (f + 6, 94), (f + 11.4, 60)],
                step=0.5)
    en.cc_curve(sc, ORG, 11, [(f, 94), (f + 6, 94), (f + 11.4, 60)],
                step=0.5)
    en.vowel(sc, CHOIR, 120, f)
    for p in (38, 45, 50, 54, 57, 62, 66, 69, 74):
        sc.note(ORGM, p, f, ln, 90, jt=0)
    sc.note(ORG, 81, f, ln, 104, jt=0)
    for p in (50, 57, 62, 66):
        sc.note(BRS, p, f, ln, 98, jt=0)
        sc.note(STR, p + 0, f, ln, 96, jt=0)
    for p in (62, 66, 69, 74):
        sc.note(CHOIR, p, f, ln, 100, jt=0)
    sc.note(HRN, 66, f, ln, 100, jt=0)
    sc.note(TPT, 74, f, ln, 100, jt=0)
    sc.cc(GTR, 11, 100, f - 0.5)
    sc.note(GTR, 86, f, ln, 110, jt=0)
    _sing(sc, f, ln)
    sc.note(VLN, 81, f, ln, 104, jt=0)
    sc.note(VLN, 90, f, ln, 102, jt=0)
    sc.note(BASS, 38, f, ln, 96, jt=0)
    sc.note(VC, 38, f, ln, 98, jt=0)
    sc.note(VC, 45, f, ln, 98, jt=0)
    for k, p in enumerate((26, 38, 45, 50, 57, 62, 66, 69, 74, 78, 81)):
        sc.note(PNO, p, f + 0.04 + 0.03 * k, 11.0, 80, jt=0)
    for k, p in enumerate((50, 54, 57, 62, 66, 69, 74, 78, 81, 90, 93)):
        sc.note(HARP, p, f + 0.25 + 0.125 * k, 6.0,
                int(en.lerp(70, 98, k / 10.0)), jt=0)
    sc.note(TIMP, 50, f, 0.4, 96, jt=0)
    _roll(sc, TIMP, 50, f + 0.25, f + 6, 76, 30)
    sc.hit(49, f, 94)
    sc.hit(57, f, 86)
    sc.hit(36, f, 96)
    sc.note(BELL, D4, f, ln, 108, jt=0, jv=0)


# ---------------------------------------------------------------------------
# IX. The Lamp Alone
# ---------------------------------------------------------------------------

def _b_alone(sc):
    sc.note(BELL, D4, T_ALONE, END - T_ALONE, 92, jt=0, jv=0)


BUILDERS = [_b_lamp, _b_hymn, _b_year, _b_gathering, _b_turning, _b_crown,
            _b_afterglow, _b_last_beam, _b_alone]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

DOR_PCS = {(D4 + s) % 12 for s in en.MODES[DOR]}
ION_PCS = {(D4 + s) % 12 for s in en.MODES[ION]}
_NAMES = {m[0]: (m[1], m[2]) for m in PART.MOVEMENTS}
CROWN_NAME = "VI. The Crown"


def _all_ons(sc):
    out = []
    for ch in sorted(sc.events):
        for b, p, v in material.note_ons(sc, ch):
            out.append((b, ch, p, v))
    return sorted(out)


def _one(sc, ch, beat):
    """The single pitch sounding on ch at beat, or None."""
    got = material.sounding(sc, ch, beat)
    return got[0] if len(got) == 1 else None


def _o_opening(sc):
    """The LAMP bell alone, then the BEAM on an unaccompanied piano."""
    fails = []
    ons = _all_ons(sc)
    if ons[0][:3] != (0.0, BELL, material.LAMP_PITCH):
        fails.append(f"first sound is ch{ons[0][1]} pitch {ons[0][2]} at "
                     f"{ons[0][0]}, not the LAMP bell at beat 0")
    if ons[1][1] != PNO or ons[1][0] < 6.0:
        fails.append(f"second sound is ch{ons[1][1]} at beat {ons[1][0]}; "
                     f"the bell must stand alone for >= 6 beats, then piano")
    start = ons[1][0]
    if start not in material.beam_statements(sc, PNO):
        fails.append(f"the first melodic notes (piano, beat {start}) are "
                     f"not the BEAM")
    span = [b for b, ch, _p, _v in ons if ch == PNO][:5]
    done = span[-1] + 3.5
    others = [(b, ch) for b, ch, _p, _v in ons
              if start <= b < done and ch != PNO]
    if others:
        fails.append(f"the opening BEAM is accompanied: {others[:4]}")
    if material.sounding(sc, BELL, start):
        fails.append("the bell is still held under the opening BEAM")
    return fails


def _o_hymn_dorian(sc):
    """The HYMN complete in D dorian on the organ, quietly."""
    fails = []
    got = [(round(s, 2), round(x, 2), b)
           for s, x, b in material.hymn_statements(sc, ORG, DOR)]
    if got != [(T_HYMN, 1.0, D4)]:
        fails.append(f"organ dorian hymn statements {got}, want exactly "
                     f"one at beat {T_HYMN}, stretch 1, on D4")
    loud = [(ch, b, v) for b, ch, _p, v in _all_ons(sc)
            if T_HYMN <= b < T_YEAR and v > 76]
    if loud:
        fails.append(f"the dorian hymn is not quiet: velocities > 76 at "
                     f"{loud[:4]}")
    extra = material.active_channels(sc, T_HYMN, T_HYMN + 32.0) \
        - {ORG, ORGM, HARP}
    if extra:
        fails.append(f"phrases 1-2 belong to the organ (and harp); also "
                     f"playing: {sorted(extra)}")
    e_h = material.energy(sc, T_HYMN, T_YEAR)
    e_c = material.energy(sc, T_CROWN, T_GLOW)
    if e_h > 0.25 * e_c:
        fails.append(f"hymn energy {e_h:.0f} is not a hush beside the "
                     f"crown's {e_c:.0f}")
    return fails


def _o_turn(sc):
    """D dorian turns to D major: key signature, tempo 88 -> 96, purity."""
    fails = []
    if sorted(sc.keysigs) != [(0.0, 0, 1), (T_CROWN, 2, 0)]:
        fails.append(f"key signatures {sorted(sc.keysigs)}: want no sharps "
                     f"at 0 and two sharps (major) at the crown")
    tempos = sorted(sc.tempos)
    rise = [bpm for b, bpm in tempos if b <= T_CROWN]
    if rise[0] != 88 or rise[-1] != 96 or rise != sorted(rise):
        fails.append(f"tempo must rise 88 -> 96 into the crown, got {rise}")
    if max(bpm for _b, bpm in tempos) > 96:
        fails.append("tempo exceeds 96")
    sharps = []
    for b, ch, p, _v in _all_ons(sc):
        if ch == DR:
            continue
        pc = p % 12
        if b < T_TURN and pc not in DOR_PCS:
            fails.append(f"ch{ch} pitch {p} at beat {b:.1f} is outside "
                         f"D dorian before the turn")
        if b >= T_CROWN and pc not in ION_PCS:
            fails.append(f"ch{ch} pitch {p} at beat {b:.1f} is outside "
                         f"D major after the turn")
        if pc in (1, 6):
            sharps.append(b)
    if not sharps or not T_TURN + 16 <= min(sharps) < T_CROWN:
        fails.append("the first F#/C# must arrive inside The Turning, "
                     "after the BEAM has been called on D and F")
    f_nat = [b for b, ch, p, _v in _all_ons(sc)
             if ch != DR and p % 12 == 5]
    if not f_nat or max(f_nat) >= T_TURN + 24:
        fails.append("F natural must be gone before the dominant arrives")
    return fails[:8]


def _o_crown(sc):
    """The HYMN complete in D ionian, tutti."""
    fails = []
    carriers = []
    for ch in (TPT, HRN, ORG, VLN):
        for s, x, base in material.hymn_statements(sc, ch, ION):
            if abs(s - T_CROWN) < 0.05 and abs(x - 1.0) < 0.01 \
                    and base % 12 == D4 % 12:
                carriers.append(ch)
    if TPT not in carriers:
        fails.append("the trumpet does not carry the complete ionian hymn "
                     "at the crown")
    if len(set(carriers)) < 3:
        fails.append(f"only channels {sorted(set(carriers))} carry the "
                     f"crowned hymn; need >= 3")
    everyone = {c[0] for c in PART.CHANNELS}
    for k in range(4):
        lo = T_CROWN + 16.0 * k
        missing = everyone - material.active_channels(sc, lo, lo + 16.0)
        if missing:
            fails.append(f"crown phrase {k + 1} is not tutti: channels "
                         f"{sorted(missing)} are silent")
    for ch in sorted(everyone - {DR}):
        if any(True for _s in material.hymn_statements(sc, ch, DOR)
               if _s[0] >= T_TURN):
            fails.append(f"ch{ch} still states the dorian hymn after the "
                         f"turn")
    return fails


def _o_loudest(sc):
    """The crown is the loudest music of the track; the arc climbs to it."""
    fails = []
    e = {name: material.energy(sc, t0, t1)
         for name, t0, t1 in PART.MOVEMENTS}
    crown = e[CROWN_NAME]
    for name, val in e.items():
        if name != CROWN_NAME and val * 1.25 > crown:
            fails.append(f"'{name}' energy {val:.0f} is within 25% of the "
                         f"crown's {crown:.0f}")
    quiet = min(material.energy(sc, T_CROWN + 16.0 * k,
                                T_CROWN + 16.0 * (k + 1)) for k in range(4))
    b = 0.0
    while b + 16.0 <= END:
        if b + 16.0 <= T_CROWN or b >= T_GLOW:
            w = material.energy(sc, b, b + 16.0)
            if w >= quiet:
                fails.append(f"beats {b:.0f}-{b + 16:.0f} (energy {w:.0f}) "
                             f"outrun the crown's quietest phrase "
                             f"({quiet:.0f})")
        b += 8.0
    order = ["II. The Keeper's Hymn", "III. The Year Remembered",
             "IV. Gathering", "V. The Turning", CROWN_NAME]
    vals = [e[nm] for nm in order]
    if vals != sorted(vals):
        fails.append(f"the arc hymn < theme < gathering < turning < crown "
                     f"does not climb: {[round(v) for v in vals]}")
    if e["VII. Afterglow"] > 0.4 * crown:
        fails.append("the afterglow does not fall away from the crown")
    return fails


def _o_descant(sc):
    """The guitar descant: consonant with the tune on every bar line, above
    it, and a line of its own."""
    fails = []
    classes = set()
    for bar in range(16):
        beat = T_CROWN + 4.0 * bar
        tune = _one(sc, TPT, beat)
        desc = _one(sc, GTR, beat)
        if tune is None or desc is None:
            fails.append(f"crown bar {bar + 1}: tune {tune} / descant "
                         f"{desc} — each must sound one note on the bar line")
            continue
        ic = (desc - tune) % 12
        classes.add(ic)
        if ic not in material.CONSONANT:
            fails.append(f"crown bar {bar + 1}: descant {desc} against "
                         f"tune {tune} is a dissonance (class {ic})")
        if desc <= tune:
            fails.append(f"crown bar {bar + 1}: the descant ({desc}) is "
                         f"not above the tune ({tune})")
    if len(classes) < 4:
        fails.append(f"the descant shadows the tune (interval classes "
                     f"{sorted(classes)}); it must be a counter-melody")
    tune_on = {round(b, 2) for b, _p, _v in material.note_ons(sc, TPT)
               if T_CROWN <= b < T_GLOW}
    desc_on = [round(b, 2) for b, _p, _v in material.note_ons(sc, GTR)
               if T_CROWN <= b < T_GLOW]
    own = [b for b in desc_on if b not in tune_on]
    if len(desc_on) < 30 or len(own) < 0.3 * len(desc_on):
        fails.append(f"the descant has {len(desc_on)} notes, {len(own)} "
                     f"off the tune's rhythm; need >= 30 and >= 30%")
    return fails[:8]


def _o_bass(sc):
    """The crown's bass is an independent line under the tune."""
    fails = []
    pairs = []
    for bar in range(16):
        beat = T_CROWN + 4.0 * bar
        tune = _one(sc, TPT, beat)
        bass = _one(sc, BASS, beat)
        if tune is None or bass is None:
            fails.append(f"crown bar {bar + 1}: no single tune/bass note "
                         f"on the bar line")
            continue
        pairs.append((tune, bass))
        if (tune - bass) % 12 not in material.CONSONANT:
            fails.append(f"crown bar {bar + 1}: bass {bass} under tune "
                         f"{tune} is a dissonance")
        ons = [b for b, _p, _v in material.note_ons(sc, BASS)
               if beat <= b < beat + 4.0]
        if len(ons) < 3:
            fails.append(f"crown bar {bar + 1}: the bass only has "
                         f"{len(ons)} note(s)")
    parallel = sum(1 for (t0, b0), (t1, b1) in zip(pairs, pairs[1:])
                   if t1 - t0 == b1 - b0 and t1 != t0)
    if parallel > 3:
        fails.append(f"the bass moves in parallel with the tune across "
                     f"{parallel} bar lines")
    pcs = {p % 12 for b, p, _v in material.note_ons(sc, BASS)
           if T_CROWN <= b < T_GLOW}
    if len(pcs) < 6:
        fails.append(f"the crown bass uses only {len(pcs)} pitch classes")
    return fails[:8]


def _o_year_counter(sc):
    """III: the horn's counter-melody is consonant with the theme on every
    bar line of the second strain, and moves when the theme holds."""
    fails = []
    u = T_YEAR + 32.0
    for bar in range(8):
        beat = u + 4.0 * bar
        theme = _one(sc, VLN, beat)
        horn = _one(sc, HRN, beat)
        if theme is None or horn is None:
            fails.append(f"theme bar {bar + 9}: theme {theme} / horn {horn}")
        elif (theme - horn) % 12 not in material.CONSONANT:
            fails.append(f"theme bar {bar + 9}: horn {horn} against theme "
                         f"{theme} is a dissonance")
    theme_on = {round(b * 2) for b, _p, _v in material.note_ons(sc, VLN)
                if u <= b < u + 32.0}
    horn_on = [round(b * 2) for b, _p, _v in material.note_ons(sc, HRN)
               if u <= b < u + 32.0]
    own = [b for b in horn_on if b not in theme_on]
    if len(own) < 4:
        fails.append(f"the horn only moves with the theme ({len(own)} "
                     f"independent onsets)")
    return fails


def _o_last_beam(sc):
    """A last BEAM climbing through the octaves, each from the last arrival."""
    fails = []
    found = {}
    for ch in sorted(BEAM_CHANNELS):
        first = {round(b, 3): p for b, p, _v in material.note_ons(sc, ch)}
        for b in material.beam_statements(sc, ch):
            if T_BEAM <= b < T_FINAL:
                found.setdefault(round(b, 3), set()).add(first[round(b, 3)])
    starts = sorted(found)
    if len(starts) < 4:
        fails.append(f"only {len(starts)} BEAM statement(s) in the last "
                     f"climb (beats {starts}); need >= 4")
        return fails
    roots = []
    for b in starts:
        if len(found[b]) != 1:
            fails.append(f"BEAMs at beat {b} start on different pitches "
                         f"{sorted(found[b])}")
        roots.append(min(found[b]))
    for (b0, r0), (b1, r1) in zip(zip(starts, roots),
                                  zip(starts[1:], roots[1:])):
        if r1 - r0 != 12:
            fails.append(f"BEAM at {b1} starts on {r1}, not an octave "
                         f"above {r0}")
        if b1 - b0 < 2.0:
            fails.append(f"BEAM at {b1} begins before the one at {b0} "
                         f"has arrived")
    if any(r % 12 != D4 % 12 for r in roots):
        fails.append(f"the last BEAMs must start on D, got {roots}")
    if roots[-1] + 12 - roots[0] < 48:
        fails.append("the climb spans less than four octaves")
    return fails


def _o_closing(sc):
    """The final sound of the album is the LAMP bell alone."""
    fails = []
    ons = _all_ons(sc)
    last = ons[-1]
    if last[1] != BELL or last[2] != material.LAMP_PITCH:
        fails.append(f"last note-on is ch{last[1]} pitch {last[2]}, not "
                     f"the LAMP bell")
    if abs(last[0] - T_ALONE) > 1e-6:
        fails.append(f"the last bell stroke is at {last[0]}, not {T_ALONE}")
    for ch in sorted(sc.events):
        for on, off, p, _v in material.note_spans(sc, ch):
            if on < last[0] and off > last[0] - 2.0:
                fails.append(f"ch{ch} pitch {p} is still held at beat "
                             f"{off:.2f}: the bell is not alone")
    tail = [off for on, off, _p, _v in material.note_spans(sc, BELL)
            if on == last[0]]
    if not tail or tail[0] < END - 0.5:
        fails.append("the last bell must ring to the end of the track")
    if ons[0][1:3] != last[1:3]:
        fails.append("the track does not end with the sound it began with")
    return fails[:8]


def oracles(sc, info, spans):
    results = material.album_oracles(sys.modules[__name__], sc)
    results.append(("lamp_bell_then_beam_opening", _o_opening(sc)))
    results.append(("hymn_dorian_on_organ_quiet", _o_hymn_dorian(sc)))
    results.append(("year_theme_counter_melody", _o_year_counter(sc)))
    results.append(("key_turns_dorian_to_major", _o_turn(sc)))
    results.append(("hymn_crowned_ionian_tutti", _o_crown(sc)))
    results.append(("crown_is_the_loudest", _o_loudest(sc)))
    results.append(("descant_consonant_on_bar_lines", _o_descant(sc)))
    results.append(("crown_bass_independent", _o_bass(sc)))
    results.append(("last_beam_climbs_octaves", _o_last_beam(sc)))
    results.append(("lamp_bell_closes_alone", _o_closing(sc)))
    return results


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py)
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    def level(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    crown = level(T_CROWN + 2, T_GLOW - 2)
    hymn = level(T_HYMN + 2, T_YEAR - 2)
    turning = level(T_TURN + 2, T_CROWN - 2)
    others = {
        "I. The Lamp": level(T_LAMP, T_HYMN),
        "II. The Keeper's Hymn": hymn,
        "III. The Year Remembered": level(T_YEAR + 2, T_GATH - 2),
        "IV. Gathering": level(T_GATH + 2, T_TURN - 2),
        "V. The Turning": turning,
        "VII. Afterglow": level(T_GLOW + 4, T_BEAM - 2),
        "VIII. the final chord": level(T_FINAL, T_FINAL + 8),
    }
    arc = []
    for name, val in others.items():
        if crown - val < 2.0:
            arc.append(f"crown {crown:.1f} dB is not clearly above "
                       f"'{name}' at {val:.1f} dB")
    if crown - hymn < 6.0:
        arc.append(f"hush-to-peak is only {crown - hymn:.1f} dB "
                   f"(hymn {hymn:.1f}, crown {crown:.1f}); need >= 6")
    if turning - hymn < 3.0:
        arc.append(f"the turning ({turning:.1f} dB) does not build on the "
                   f"hymn ({hymn:.1f} dB)")

    bell = []
    first = level(0.2, 6.0)
    last = level(T_ALONE + 0.2, T_ALONE + 8.0)
    breath = level(T_ALONE - 1.5, T_ALONE - 0.1)
    if first < -50.0:
        bell.append(f"the opening bell is inaudible ({first:.1f} dB)")
    if last < -50.0:
        bell.append(f"the closing bell is inaudible ({last:.1f} dB)")
    if crown - last < 6.0:
        bell.append(f"the closing bell ({last:.1f} dB) is not a hush "
                    f"beside the crown ({crown:.1f} dB)")
    if last - breath < 3.0:
        bell.append(f"the closing bell ({last:.1f} dB) does not stand "
                    f"clear of the chord's tail ({breath:.1f} dB)")

    glow = []
    after = level(T_GLOW + 4, T_GLOW + 30)
    if crown - after < 6.0:
        glow.append(f"the afterglow ({after:.1f} dB) does not fall >= 6 dB "
                    f"from the crown ({crown:.1f} dB)")
    return [("crown_is_the_peak_audio", arc),
            ("lamp_bell_alone_audio", bell),
            ("afterglow_falls_away_audio", glow)]
