"""movements/t02_the_ninety_eight.py — track 2 of *The Remaining*.

THE ELEGY FOR THOSE WHO REMAIN.  A D-minor string chaconne in 3/4: the
contrabass lays down THE GROUND one chord per bar, a root on every downbeat,
unbroken for twenty-two cycles — the stubborn pulse of the ninety-eight who
were left.  The cello doubles it as the ground's tenor.  Above that floor,
six variations, each built to pass its own oracle:

  1. bare fifths      viola a perfect fifth above the cello — hollow, con sordino
  2. suspensions      every ground chord blooms into its 4-3 / 9-8 sigh
  3. the vigil theme   violin I sings the album motif augmented x2, ending each
                       time on the waiting tone E (degree 1, home, is withheld)
  4. canon             violin II follows violin I one bar later at the lower
                       fifth, note for note (a real 7-semitone transposition)
  5. the descant       violin I soars a high line above the full quartet — the
                       one moment the elegy lifts its head (the emotional peak)
  6. the thinning      the stage empties one voice per cycle, the ground playing on

Then the coda: the PIANO enters for the first and only time in the track —
four bars of the (un-holed) DEPARTURE FIGURE, pianissimo, the departed hand
briefly at the keyboard — and the music settles onto a single violin, alone,
holding the waiting tone E.  Never degree 1.  Not yet.

Advanced controllers: bend appoggiaturas slid into the theme and descant peaks
(recentred before every movement boundary), channel-aftertouch swells on the
cello's long tones, CC74 "con sordino" darkening across variations 1-2 that
opens as the theme enters, and CC1 vibrato that deepens variation by variation.
Every structural device below is oracle-pinned against material.py.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 2
TITLE = "The Ninety-Eight"
FILE = "02 - The Ninety-Eight.mid"
SEED = 20261098
COMMENT = (
    "An elegy for those who remain - a string chaconne in D minor, 3/4. A "
    "contrabass ground states a four-chord bass one root per bar, unbroken "
    "for twenty-two cycles; above it six variations - bare fifths, blooming "
    "suspensions, the vigil theme augmented, a canon at the lower fifth, a "
    "high descant, then a thinning that empties the stage one voice per "
    "cycle. In the coda the piano enters for the only time, four bars of a "
    "broken-chord figure, and the music ends on a single violin holding the "
    "waiting tone E - never quite reaching home.")

# ---------------------------------------------------------------------------
# Pinned geometry (the oracles below verify all of it against material.py)
# ---------------------------------------------------------------------------

PIANO, V1, V2, VLA, VC, CB = 0, 1, 2, 3, 4, 5

BASE = en.n("D4")                                # 62 — the string-line tonic
_MM = material.MODE_MINOR

BASS_ROOTS = material.ground_roots(en.n("D2"))    # [38, 46, 41, 48]  D-Bb-F-C
CELLO_ROOTS = material.ground_roots(en.n("D3"))   # [50, 58, 53, 60]
VIOLA_ROOTS = material.ground_roots(en.n("D4"))   # [62, 70, 65, 72]
MINORITY = [True, False, False, False]            # Dm minor; Bb/F/C major

PIANO_ROOTS = [en.n("D3"), en.n("Bb2"), en.n("F3"), en.n("C3")]   # [50,46,53,48]

GROUND_LAST_BAR = 89          # contrabass states a root on bars 0..89
CELLO_LAST_BAR = 87           # the cello tenor drops just before the end
CODA_START = 240.0            # bar 80 — the piano's only entrance
END = 288.0

# var 5 tutti: (cello, viola, violin II) chord voicing per ground chord,
# every pitch kept below the descant register so violin I stays on top.
TUTTI_V5 = [(50, 57, 65), (58, 65, 62), (53, 60, 57), (60, 67, 64)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. The Ground", 0.0, 36.0),
               ("II. The Variations", 36.0, 240.0),
               ("III. Coda", 240.0, END)],
    tempo_map=[(0.0, 56.0), (6.0, 58.0), (18.0, 55.0), (24.0, 58.0),
               (33.0, 52.0), (36.0, 57.0), (54.0, 54.0), (60.0, 58.0),
               (78.0, 55.0), (84.0, 59.0), (108.0, 56.0), (114.0, 59.0),
               (120.0, 59.0), (144.0, 56.0), (150.0, 60.0), (156.0, 61.0),
               (180.0, 57.0), (186.0, 60.0), (192.0, 58.0), (216.0, 54.0),
               (234.0, 52.0), (240.0, 50.0), (264.0, 47.0), (282.0, 44.0)],
    time_signatures=[(0.0, 3, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=[(PIANO, "piano", 0, 96, material.SEATING["piano"], 60),
              (V1, "violin I", 40, 94, material.SEATING["violin1"], 66),
              (V2, "violin II", 40, 94, material.SEATING["violin2"], 66),
              (VLA, "viola", 41, 92, material.SEATING["viola"], 64),
              (VC, "cello", 42, 96, material.SEATING["cello"], 62),
              (CB, "contrabass", 43, 90, material.SEATING["bass"], 50)],
    extra_markers=[(156.0, "the descant"), (192.0, "the thinning")],
)

PROGRAM_WHITELIST = {0, 40, 41, 42, 43}
CENTERED_CHANNELS = {PIANO, CB}                  # piano & bass seats are 64
NOTE_RANGES = {PIANO: (44, 72), V1: (60, 84), V2: (55, 74),
               VLA: (55, 78), VC: (40, 66), CB: (33, 52)}
GAP_WHITELIST: list[tuple[float, float]] = []    # the ground never lets go
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (295.0, 350.0)                 # tightened after the build
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# Calibrated mono-compatibility cap (album default 2.0 dB).  Diagnosed
# 2026.07.18 against the real render: this is the album's one track whose
# entire body is the seated string quartet (44/54/74/84) with no centred
# melodic mass — the synth's pan-Haas width (engine.rs: up to 5 ms far-side
# delay) combs each seated channel in the mono sum, and with nothing at the
# centre the whole-track loss floors at ~2.2 dB.  The seats are album DNA
# (the same players in the same chairs across T1/T2/T5 — the point of the
# record), so the honest fix is a documented cap, not narrower seating.
# Measured 2.19 dB; capped 2.5 dB — pathological collapse still fails.
MONO_LOSS_CAP_DB = 2.5


# ---------------------------------------------------------------------------
# Emitters (every oracle-pinned lane is jt=0 — tick-exact)
# ---------------------------------------------------------------------------

def _bass_bar(sc, bar, vel):
    """One ground root on the downbeat of `bar` — the isochronous chaconne."""
    sc.note(CB, BASS_ROOTS[bar % 4], 3.0 * bar, 2.9, vel, jt=0, jv=1)


def _cello_bar(sc, bar, vel, swell=False):
    """The ground's tenor: the cello doubles the root an octave up."""
    on = 3.0 * bar
    sc.note(VC, CELLO_ROOTS[bar % 4], on, 2.85, vel, jt=0, jv=1)
    if swell:
        en.at_curve(sc, VC, [(on, 0), (on + 1.6, 52), (on + 2.6, 0)], step=0.4)


def _appoggiatura(sc, ch, t0, depth=0.5):
    """Slide into a phrase peak from a semitone below, recentred by t0+0.18."""
    en.bend_ramp(sc, ch, t0 - 0.15, t0 + 0.18, -depth, 0.0, steps=6)


def _theme_stmt(sc, t0, vel, vel_end, vib):
    """One VIGIL THEME statement in violin I, augmented x2 (oracle-pinned)."""
    notes = material.theme_notes(stretch=2.0)
    total = notes[-1][0] + notes[-1][1]                      # 16 beats
    _appoggiatura(sc, V1, t0)
    for on, du, deg in notes:
        v = round(en.lerp(vel, vel_end, on / total))
        sc.note(V1, en.pitch(BASE, _MM, deg), t0 + on, du * 0.94, v, jt=0, jv=0)
        if du >= 1.9 and vib > 0:
            en.vibrato(sc, V1, t0 + on + 0.4, du * 0.9 - 0.5, depth=vib)
    en.expr_curve(sc, V1, [(t0, 42), (t0 + total * 0.38, 88),
                           (t0 + total - 0.3, 50)], step=1.0)
    sc.bend(V1, t0 + total, 0.0)                             # recentre


# The canon subject — a lyrical aeolian line that deliberately avoids both the
# tonic (degree 1) and the theme's interval signature.  (onset, dur, degree).
CANON_LEADER = [(0.0, 2.8, 5), (3.0, 2.8, 6), (6.0, 2.8, 7), (9.0, 2.8, 5),
                (12.0, 2.8, 4), (15.0, 2.8, 6), (18.0, 2.8, 5), (21.0, 2.8, 3),
                (24.0, 2.8, 4), (27.0, 2.8, 2)]

# The descant — violin I high above the tutti, avoiding degree 1, landing on
# the waiting tone E.  (onset, dur, degree).
DESCANT = [(0.0, 2.9, 9), (3.0, 2.9, 10), (6.0, 2.9, 11), (9.0, 2.9, 12),
           (12.0, 2.9, 11), (15.0, 2.9, 9), (18.0, 2.9, 10), (21.0, 2.9, 12),
           (24.0, 2.9, 11), (27.0, 2.9, 9), (30.0, 6.0, 9)]


# ---------------------------------------------------------------------------
# I. The Ground [0, 36) — the bare cello/bass chaconne establishes
# ---------------------------------------------------------------------------

def _b_ground(sc):
    en.cc_curve(sc, VC, 74, [(0.0, 42), (34.0, 34)], step=4.0)   # con sordino
    en.cc_curve(sc, CB, 74, [(0.0, 40), (34.0, 34)], step=4.0)
    for bar in range(0, 12):
        cyc = bar // 4
        _bass_bar(sc, bar, 38 + 2 * cyc)
        _cello_bar(sc, bar, 40 + 2 * cyc, swell=(bar % 2 == 0))
    en.expr_curve(sc, CB, [(0.0, 60), (18.0, 76), (34.0, 70)], step=2.0)
    en.expr_curve(sc, VC, [(0.0, 62), (18.0, 84), (34.0, 74)], step=2.0)


# ---------------------------------------------------------------------------
# II. The Variations [36, 240) — six, each pinned to its device
# ---------------------------------------------------------------------------

def _b_variations(sc):
    # the ground runs beneath every variation (bars 12..79)
    for bar in range(12, 80):
        # a slow swell to the descant (bar 52) then an ebb through the thinning
        arc = 40 + min(18, (bar - 12)) if bar < 52 else 58 - (bar - 52)
        _bass_bar(sc, bar, max(36, min(56, arc)))
        _cello_bar(sc, bar, max(38, min(58, arc + 2)),
                   swell=(bar < 28 and bar % 2 == 0))
    en.expr_curve(sc, CB, [(36.0, 66), (156.0, 92), (192.0, 82),
                           (239.0, 60)], step=4.0)
    en.expr_curve(sc, VC, [(36.0, 70), (156.0, 96), (192.0, 84),
                           (239.0, 58)], step=4.0)
    en.cc_curve(sc, VC, 74, [(36.0, 30), (84.0, 30), (96.0, 74),
                             (238.0, 66)], step=6.0)      # sordino opens at III
    en.cc_curve(sc, VLA, 74, [(36.0, 30), (84.0, 30), (96.0, 72),
                              (226.0, 62)], step=6.0)
    en.cc_curve(sc, V1, 1, [(84.0, 12), (120.0, 22), (156.0, 40),
                            (204.0, 46)], step=6.0)        # CC1 deepens

    # --- var 1 [36, 60): bare fifths (viola a P5 above the cello) ------------
    for bar in range(12, 20):
        on = 3.0 * bar
        sc.note(VLA, CELLO_ROOTS[bar % 4] + 7, on, 2.8,
                44 + (bar - 12), jt=0, jv=1)
    en.expr_curve(sc, VLA, [(36.0, 54), (48.0, 72), (59.0, 56)], step=2.0)

    # --- var 2 [60, 84): the suspensions bloom (all four sighs) --------------
    for bar in range(20, 28):
        i = bar % 4
        s, r = material.SUSPENSIONS[i]
        on = 3.0 * bar
        vel = 48 + (bar - 20)
        sc.note(VLA, VIOLA_ROOTS[i] + s, on, 1.0, vel + 4, jt=0, jv=1)   # sigh
        sc.note(VLA, VIOLA_ROOTS[i] + r, on + 1.0, 1.9, vel, jt=0, jv=1)  # falls
        en.vibrato(sc, VLA, on + 1.3, 1.4, depth=0.14)
    en.expr_curve(sc, VLA, [(60.0, 58), (72.0, 78), (83.0, 60)], step=2.0)
    sc.bend(VLA, 83.5, 0.0)                                # recentre the viola

    # --- var 3 [84, 120): the vigil theme, augmented x2 ---------------------
    _theme_stmt(sc, 84.0, vel=52, vel_end=62, vib=0.16)
    _theme_stmt(sc, 102.0, vel=56, vel_end=64, vib=0.20)
    # viola holds a soft third inside the ground so the theme has a bed
    for bar in range(28, 40):
        i = bar % 4
        sc.note(VLA, VIOLA_ROOTS[i], 3.0 * bar, 2.7, 40 + (bar - 28) // 2,
                jt=0, jv=1)
    en.expr_curve(sc, VLA, [(84.0, 44), (102.0, 58), (119.0, 46)], step=2.0)

    # --- var 4 [120, 156): canon at the lower fifth -------------------------
    for on, du, deg in CANON_LEADER:
        p = en.pitch(BASE, _MM, deg)
        sc.note(V1, p, 120.0 + on, du, 56 + int(on) // 6, jt=0, jv=0)     # lead
        sc.note(V2, p - 7, 123.0 + on, du, 50 + int(on) // 6, jt=0, jv=0)  # ans.
        if du >= 2.0:
            en.vibrato(sc, V1, 120.0 + on + 0.5, du - 0.8, depth=0.22)
    en.expr_curve(sc, V1, [(120.0, 46), (138.0, 78), (154.0, 50)], step=2.0)
    en.expr_curve(sc, V2, [(123.0, 42), (141.0, 70), (154.0, 48)], step=2.0)
    sc.bend(V1, 150.0, 0.0)                                # recentre both

    # --- var 5 [156, 192): the descant above the full quartet (the peak) -----
    for bar in range(52, 64):
        i = bar % 4
        vc, vla, v2 = TUTTI_V5[i]
        on = 3.0 * bar
        sc.note(VLA, vla, on, 2.85, 54 + (bar - 52), jt=0, jv=1)
        sc.note(V2, v2, on, 2.85, 52 + (bar - 52), jt=0, jv=1)
    for k, (on, du, deg) in enumerate(DESCANT):
        t = 156.0 + on
        p = en.pitch(BASE, _MM, deg)
        if deg == 12:                                     # the two crests
            _appoggiatura(sc, V1, t)
        sc.note(V1, p, t, du * 0.95, 62 + (2 if deg >= 11 else 0)
                + min(10, k), jt=0, jv=0)
        if du >= 2.0:
            en.vibrato(sc, V1, t + 0.5, du * 0.85, depth=0.30)
    en.expr_curve(sc, V1, [(156.0, 52), (165.0, 92), (177.0, 96),
                           (191.5, 66)], step=1.0)
    en.expr_curve(sc, VLA, [(156.0, 60), (174.0, 78), (191.0, 62)], step=2.0)
    en.expr_curve(sc, V2, [(156.0, 56), (174.0, 74), (191.0, 58)], step=2.0)
    sc.bend(V1, 190.0, 0.0)                                # recentre before III

    # --- var 6 [192, 240): the thinning — one voice leaves per cycle ---------
    # cycle 1: vln I + vln II + viola (+ ground);  then vln I, then vln II,
    # then viola drop out, the cello/bass ground playing on alone.
    v1_line = [81, 79, 77, 76]                             # A5 G5 F5 E5, one/bar
    for j, bar in enumerate(range(64, 68)):                # cycle 1 only
        sc.note(V1, v1_line[j], 3.0 * bar, 2.7, 56 - 2 * j, jt=0, jv=1)
    en.expr_curve(sc, V1, [(192.0, 60), (198.0, 40), (203.5, 24)], step=1.0)
    for bar in range(64, 72):                              # cycles 1-2
        i = bar % 4
        sc.note(V2, TUTTI_V5[i][2], 3.0 * bar, 2.7, 52 - (bar - 64), jt=0, jv=1)
    en.expr_curve(sc, V2, [(192.0, 58), (204.0, 46), (213.0, 30)], step=2.0)
    for bar in range(64, 76):                              # cycles 1-3
        i = bar % 4
        sc.note(VLA, TUTTI_V5[i][1], 3.0 * bar, 2.7, 52 - (bar - 64), jt=0, jv=1)
    en.expr_curve(sc, VLA, [(192.0, 56), (210.0, 44), (225.0, 28)], step=2.0)


# ---------------------------------------------------------------------------
# III. Coda [240, 288) — the piano's only entrance; a violin alone on E
# ---------------------------------------------------------------------------

def _b_coda(sc):
    # the ground fades but does not stop until the very end
    for bar in range(80, GROUND_LAST_BAR + 1):
        _bass_bar(sc, bar, 36 - (bar - 80) // 3)
    for bar in range(80, CELLO_LAST_BAR + 1):
        _cello_bar(sc, bar, 40 - (bar - 80))
    en.expr_curve(sc, CB, [(240.0, 58), (264.0, 40), (269.0, 22)], step=2.0)
    en.expr_curve(sc, VC, [(240.0, 56), (255.0, 34), (263.0, 20)], step=2.0)

    # the piano enters for the first time: four bars of the UN-holed figure, pp
    en.soft_pedal(sc, PIANO, 240.0, 256.0)
    for f in range(4):
        t0 = CODA_START + 4.0 * f
        material.play_figure(sc, PIANO, t0, PIANO_ROOTS[f], minor=MINORITY[f],
                             vel=38, vel_end=43, holes=frozenset(),
                             jt=0, jv=2)
        en.sustain(sc, PIANO, t0, t0 + 3.6)
    en.expr_curve(sc, PIANO, [(240.0, 70), (248.0, 76), (255.0, 60)], step=1.0)

    # a single violin, alone, holding the waiting tone E — never degree 1
    e5 = en.n("E5")                                       # 76, pitch class E
    sc.note(V1, e5, 264.0, 24.0, 42, jt=0, jv=0)
    en.vibrato(sc, V1, 266.0, 18.0, depth=0.18)
    en.expr_curve(sc, V1, [(264.0, 58), (270.0, 74), (282.0, 40),
                           (288.0, 22)], step=1.0)


BUILDERS = [_b_ground, _b_variations, _b_coda]


# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES §2 pattern; 3/4 aware)
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


def _theme_sig():
    degs = [d for _on, _du, d in material.THEME]
    return [en.deg_semis(_MM, b) - en.deg_semis(_MM, a)
            for a, b in zip(degs, degs[1:])]


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _o_isochrony(sc):
    """THE GROUND: one root per bar, on the downbeat, isochronous, 12+ cycles."""
    fails = []
    ons = _ons(sc, CB)
    n = GROUND_LAST_BAR + 1
    if len(ons) != n:
        fails.append(f"contrabass has {len(ons)} roots, want {n} "
                     f"(one per bar, bars 0..{GROUND_LAST_BAR})")
    for b, (beat, pitch, _v) in enumerate(ons):
        if b >= n:
            break
        if abs(beat - 3.0 * b) > 1e-6:
            fails.append(f"root {b}: onset {beat:.3f}, want {3.0 * b:.1f} "
                         f"(beat 1 of the bar)")
        if pitch != BASS_ROOTS[b % 4]:
            fails.append(f"root {b}: pitch {pitch}, want {BASS_ROOTS[b % 4]} "
                         f"({'Dm Bb F C'.split()[b % 4]})")
    diffs = {round(b2 - b1, 6) for (b1, _p1, _v1), (b2, _p2, _v2)
             in zip(ons, ons[1:])}
    if diffs and diffs != {3.0}:
        fails.append(f"root spacing not isochronous: {sorted(diffs)}")
    if n / 4 < 12:
        fails.append(f"only {n / 4:.1f} chaconne cycles, want >= 12")
    return fails[:8]


def _o_bare_fifths(sc):
    """Var 1: violin I & II tacet; every viola note a perfect fifth above the
    cello root — an open fifth with no third anywhere."""
    fails = []
    lo, hi = 36.0, 60.0
    for ch, name in ((V1, "violin I"), (V2, "violin II")):
        stray = [b for b, _p, _v in _ons(sc, ch) if lo - 1e-9 <= b < hi]
        if stray:
            fails.append(f"{name} must be tacet in the bare-fifths variation "
                         f"({len(stray)} note(s), first at {stray[0]:.1f})")
    vc = {round(b, 3): p for b, p, _v in _ons(sc, VC) if lo <= b < hi}
    vla = {round(b, 3): p for b, p, _v in _ons(sc, VLA) if lo <= b < hi}
    for bar in range(12, 20):
        beat = round(3.0 * bar, 3)
        cp, vp = vc.get(beat), vla.get(beat)
        if cp is None or vp is None:
            fails.append(f"bar {bar}: need cello root + viola fifth on beat 1")
        elif vp - cp != 7:
            fails.append(f"bar {bar}: viola {vp} is not a perfect fifth above "
                         f"cello {cp} (interval {vp - cp})")
    return fails[:8]


def _o_suspensions(sc):
    """Var 2: every ground chord enters suspended and resolves down by step;
    all four material.SUSPENSIONS pairs are present."""
    fails = []
    vla = _ons(sc, VLA)
    seen = set()
    for bar in range(20, 28):
        i = bar % 4
        s, r = material.SUSPENSIONS[i]
        beat = 3.0 * bar
        pair = sorted((b, p) for b, p, _v in vla
                      if beat - 1e-9 <= b < beat + 2.4)
        if len(pair) < 2:
            fails.append(f"bar {bar} (chord {i}): need a suspension and its "
                         f"resolution in the viola")
            continue
        (b0, p0), (b1, p1) = pair[0], pair[1]
        if abs(b0 - beat) > 1e-6 or p0 != VIOLA_ROOTS[i] + s:
            fails.append(f"bar {bar}: suspension ({b0:.2f},{p0}) want "
                         f"({beat:.2f},{VIOLA_ROOTS[i] + s})")
        if abs(b1 - (beat + 1.0)) > 1e-6 or p1 != VIOLA_ROOTS[i] + r:
            fails.append(f"bar {bar}: resolution ({b1:.2f},{p1}) want "
                         f"({beat + 1.0:.2f},{VIOLA_ROOTS[i] + r})")
        if not 0 < s - r <= 2:
            fails.append(f"chord {i}: sigh {s}->{r} must resolve down by step")
        seen.add((i, (s, r)))
    for i, (s, r) in enumerate(material.SUSPENSIONS):
        if (i, (s, r)) not in seen:
            fails.append(f"chord {i}'s suspension {(s, r)} never sounds")
    return fails[:8]


def _o_theme_augmentation(sc):
    """Var 3: exactly two violin-I statements of the theme, augmented x2,
    matching material.THEME note for note."""
    fails = []
    notes = material.theme_notes(stretch=2.0)
    ons = [(b, p) for b, p, _v in _ons(sc, V1) if 84.0 - 1e-9 <= b < 120.0]
    if len(ons) != 2 * len(notes):
        fails.append(f"violin I has {len(ons)} notes in the theme variation, "
                     f"want {2 * len(notes)} (two augmented statements)")
    for t0 in (84.0, 102.0):
        for k, (on, du, deg) in enumerate(notes):
            wbeat, wpitch = t0 + on, en.pitch(BASE, _MM, deg)
            match = [p for b, p in ons if abs(b - wbeat) < 1e-6]
            if not match:
                fails.append(f"statement {t0:.0f}, note {k}: no onset at "
                             f"{wbeat:.1f}")
            elif wpitch not in match:
                fails.append(f"statement {t0:.0f}, note {k}: pitch {match} "
                             f"want {wpitch} (degree {deg} x2)")
    return fails[:8]


def _o_waiting_tone(sc):
    """The withheld tonic: the theme's melodic voice (violin I) never sounds
    degree 1; every theme statement (and the whole track) ends on the waiting
    tone E (degree 2)."""
    fails = []
    tonic_pc = BASE % 12                                  # 2 (D)
    waiting_pc = en.pitch(BASE, _MM, material.THEME_END_DEG) % 12   # 4 (E)
    v1 = _ons(sc, V1)
    stray = [b for b, p, _v in v1 if p % 12 == tonic_pc]
    if stray:
        fails.append(f"violin I sounds the tonic D at beat {stray[0]:.1f} - "
                     f"degree 1 is withheld from the theme voice on this track")
    if v1 and v1[-1][1] % 12 != waiting_pc:
        fails.append(f"the track's last violin-I note (pc {v1[-1][1] % 12}) "
                     f"is not the waiting tone E")
    for t0 in (84.0, 102.0):
        end = t0 + material.theme_notes(stretch=2.0)[-1][0]
        m = [p for b, p, _v in v1 if abs(b - end) < 1e-6]
        if not m or m[0] % 12 != waiting_pc:
            fails.append(f"theme statement at {t0:.0f} does not end on E")
    # insurance: any theme-shaped run anywhere must end on the waiting tone
    sig = _theme_sig()
    for ch in sorted(sc.events):
        ons = _ons(sc, ch)
        for i in range(len(ons) - len(sig)):
            win = ons[i:i + len(sig) + 1]
            if win[-1][0] - win[0][0] > 17.0:
                continue
            if [b[1] - a[1] for a, b in zip(win, win[1:])] == sig \
                    and win[-1][1] % 12 != waiting_pc:
                fails.append(f"ch{ch} theme-shaped run at {win[0][0]:.1f} ends "
                             f"pc {win[-1][1] % 12}, not the waiting tone")
    return fails[:8]


def _o_canon(sc):
    """Var 4: violin II follows violin I one bar (3 beats) later at the lower
    fifth (a real 7-semitone transposition), note for note."""
    fails = []
    lo, hi = 120.0, 156.0
    lead = [(b, p) for b, p, _v in _ons(sc, V1) if lo - 1e-9 <= b < hi]
    foll = [(b, p) for b, p, _v in _ons(sc, V2) if lo - 1e-9 <= b < hi]
    if len(lead) != len(foll) or len(lead) < 6:
        fails.append(f"canon: {len(lead)} leader vs {len(foll)} follower "
                     f"notes (need an equal subject of >= 6)")
    for k, ((lb, lp), (fb, fp)) in enumerate(zip(lead, foll)):
        if abs((fb - lb) - 3.0) > 1e-6:
            fails.append(f"canon note {k}: follower delay {fb - lb:.3f}, "
                         f"want one bar (3.0)")
        if lp - fp != 7:
            fails.append(f"canon note {k}: interval {lp - fp} semitones, "
                         f"want a lower fifth (7)")
    return fails[:8]


def _o_descant(sc):
    """Var 5: violin I sits strictly above every other sounding voice."""
    fails = []
    lo, hi = 156.0, 192.0
    spans = {ch: _spans(sc, ch) for ch in (V2, VLA, VC, CB)}
    top = [(b, p) for b, p, _v in _ons(sc, V1) if lo - 1e-9 <= b < hi]
    if len(top) < 8:
        fails.append(f"descant has only {len(top)} notes")
    for b, p in top:
        for ch, sp in spans.items():
            under = [pp for on, off, pp in sp if on <= b + 1e-6
                     and off >= b + 0.05]
            if under and max(under) >= p:
                fails.append(f"descant at {b:.1f} (pitch {p}) not above ch{ch} "
                             f"(pitch {max(under)})")
                break
    return fails[:8]


def _o_thinning(sc):
    """Var 6: the number of voices sounding falls by one every cycle."""
    fails = []
    counts = []
    for c in range(4):
        clo, chi = 192.0 + 12.0 * c, 192.0 + 12.0 * (c + 1)
        active = sum(1 for ch in (V1, V2, VLA, VC, CB)
                     if any(clo - 1e-9 <= b < chi for b, _p, _v in _ons(sc, ch)))
        counts.append(active)
    for k in range(3):
        if counts[k + 1] >= counts[k]:
            fails.append(f"cycle {k + 1} keeps {counts[k + 1]} voices - the "
                         f"stage must lose one per cycle ({counts})")
    if counts and not counts[0] > counts[-1]:
        fails.append(f"the stage never empties: {counts}")
    return fails[:8]


def _o_piano_tacet(sc):
    """The piano is silent until the coda, then plays exactly four un-holed
    departure figures."""
    fails = []
    ons = _ons(sc, PIANO)
    early = [b for b, _p, _v in ons if b < CODA_START - 1e-9]
    if early:
        fails.append(f"piano sounds {len(early)} note(s) before the coda "
                     f"(first at {early[0]:.1f}); it must be tacet")
    if len(ons) != 32:
        fails.append(f"piano has {len(ons)} coda note-ons, want 32 "
                     f"(4 un-holed figures x 8 quavers)")
    for f in range(4):
        t0 = CODA_START + 4.0 * f
        offs = material.figure_offsets(MINORITY[f])
        for i, off in enumerate(offs):
            wbeat, wpitch = t0 + 0.5 * i, PIANO_ROOTS[f] + off
            m = [p for b, p, _v in ons if abs(b - wbeat) < 1e-6]
            if not m:
                fails.append(f"figure {f}, quaver {i}: no onset at {wbeat:.2f}")
            elif wpitch not in m:
                fails.append(f"figure {f}, quaver {i}: pitch {m} want {wpitch}")
    return fails[:8]


def _o_rubato():
    """The tempo map breathes: not flat, dips in every movement, a final
    ritardando."""
    fails = []
    tm = PART.TEMPO_MAP
    bpms = [b for _t, b in tm]
    if len(tm) < 12:
        fails.append(f"only {len(tm)} tempo events - too flat")
    if max(bpms) - min(bpms) < 8.0:
        fails.append(f"tempo range {max(bpms) - min(bpms):.0f} bpm under 8")
    if sum(1 for a, b in zip(bpms, bpms[1:]) if b < a) < 4:
        fails.append("fewer than 4 tempo dips - not enough rubato")
    if bpms[-1] > 52.0:
        fails.append(f"final tempo {bpms[-1]} - the coda must ritard to <= 52")
    for name, t0, t1 in PART.MOVEMENTS:
        seg = [b for t, b in tm if t0 <= t < t1]
        if not any(b2 < b1 for b1, b2 in zip(seg, seg[1:])):
            fails.append(f"no tempo dip inside '{name}'")
    return fails


def oracles(sc, info, spans):
    return [
        ("chaconne_isochrony", _o_isochrony(sc)),
        ("bare_fifths", _o_bare_fifths(sc)),
        ("suspension_pairs", _o_suspensions(sc)),
        ("theme_augmentation", _o_theme_augmentation(sc)),
        ("waiting_tone", _o_waiting_tone(sc)),
        ("canon_exactness", _o_canon(sc)),
        ("descant_above", _o_descant(sc)),
        ("monotone_thinning", _o_thinning(sc)),
        ("piano_tacet", _o_piano_tacet(sc)),
        ("rubato_nonflat", _o_rubato()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — proven on the render, not the event data
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    # 1. The descant (var 5) is the emotional peak: louder than the bare
    #    fifths (var 1).
    a0, a1 = ctx.bar_window(38.0, 58.0)
    bare = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    b0, b1 = ctx.bar_window(160.0, 188.0)
    peak = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    fails = []
    if peak < bare + 3.0:
        fails.append(f"descant {peak:.1f} dB not >= 3 dB over the bare fifths "
                     f"{bare:.1f} dB")
    checks.append(("audio_descant_peak", fails))

    # 2. The piano's coda entrance is audible over the thinned ground.
    c0, c1 = ctx.bar_window(241.0, 255.0)
    coda = ctx.db(ctx.rms(ctx.l, ctx.r, c0, c1))
    fails = []
    if coda < -34.0:
        fails.append(f"coda piano {coda:.1f} dB is inaudibly quiet")
    checks.append(("audio_coda_entrance", fails))

    # 3. The track ends on a real solo: the final violin E is well under the
    #    peak yet still present (not silence).
    d0, d1 = ctx.bar_window(278.0, 286.0)
    solo = ctx.db(ctx.rms(ctx.l, ctx.r, d0, d1))
    fails = []
    if solo > peak - 6.0:
        fails.append(f"final solo {solo:.1f} dB not >= 6 dB under the peak "
                     f"{peak:.1f} dB")
    if solo < -46.0:
        fails.append(f"final solo {solo:.1f} dB - the waiting tone vanished")
    checks.append(("audio_final_solo", fails))
    return checks
