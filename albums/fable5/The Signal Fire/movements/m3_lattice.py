"""m3_lattice — Movement 3 "The Lattice" (beats 480-800, D dorian, 10/8, 108).

64 five-beat cycles: RIFF_10 dissolved into three interlocking guitars — the
Incantations hocket.  L1 (steel, ch7) enters alone at cycle 0, L2 (nylon,
ch8) at cycle 8, L3 (rhythm, ch10, repanned 103) at cycle 16; together they
recombine the riff verbatim, terracing 55->75 with the group-start quavers
accented (3+3+2+2 on even cycles, 2+2+3+3 cross-accents on odd), one diatonic
neighbour-turn decoration per line every 4th cycle.  Bass RIFF_10 from cycle
8 (vel 70->95, cross-accent variant every 8th cycle); the crystal's 3-beat
1-5-9 loop drifts over the 5-beat metre (realigns every 15 beats) under a
15-beat CC10 autopan; tremolo mandolin doubles the accent quavers from cycle
24; the fiddle sings THEME_B re-phrased into 4-beat calls + 1-beat breaths
across four cycles per statement (CC68 slurs on the quaver runs, delayed
vibrato on the extended finals); organ flutes lay the THEME_C chorale under
everything from cycle 32; shaker 16ths + tambourine mark the group starts;
strings pad the cycle roots (i-i-bVII-i) from cycle 40 with CC11 swells.
Cycles 56-63 build to tutti (vel +15, strings CC11 90).
Seam: last note-ons at 799.5; bass walks D-C-B-A on 796-799; strings strike
a Dm(add9) at 784 that sustains across 800 (CC11 fading 80->40); all ch14
bends recentred and CC68 released well before 800.  CC91=60 on every channel
used, set at 480.
"""

from __future__ import annotations

import engine as en
import material as m
from conductor import (CH_BASS, CH_BELLS, CH_CRYSTAL, CH_DRUMS, CH_NYLON,
                       CH_ORGAN, CH_RHYTHM, CH_STEEL, CH_STRINGS, CH_WINDS)
from engine import lerp, n

MODE = "dorian"
T0, T1 = 480.0, 800.0
CYC = m.CYCLE_10                          # 5.0 beats per 10/8 cycle
CYCLES = 64
TUTTI = 56                                # cycles 56-63: the build
D2, D3, D4, D5 = n("D2"), n("D3"), n("D4"), n("D5")

LATTICE_CH = (CH_STEEL, CH_NYLON, CH_RHYTHM)    # L1 / L2 / L3
LATTICE_ENTRY = (0, 8, 16)                      # entry cycle per line

MY_CHANNELS = (CH_CRYSTAL, CH_BASS, CH_ORGAN, CH_STRINGS, CH_STEEL,
               CH_NYLON, CH_DRUMS, CH_RHYTHM, CH_WINDS, CH_BELLS)

SHAKER, TAMBOURINE = 70, 54


def _cyc(c: int) -> float:
    return T0 + c * CYC


def _accents(c: int) -> tuple[int, ...]:
    """Even cycles keep the 3+3+2+2 grouping; odd cycles cross-accent."""
    return m.RIFF_10_ACCENTS if c % 2 == 0 else m.RIFF_10_CROSS


# ---------------------------------------------------------------------------
# Movement-start controller state (roadmap section 5: CC91 distance = 60).
# ---------------------------------------------------------------------------

def _setup(sc) -> None:
    for ch in MY_CHANNELS:
        sc.cc(ch, 91, 60, T0)
    sc.cc(CH_RHYTHM, 10, 103, T0)         # L3 repans from M2's antiphonal 30
    sc.cc(CH_CRYSTAL, 94, 35, T0)         # gentle echo bed on the loop
    for ch, v in ((CH_NYLON, 100), (CH_RHYTHM, 100),
                  (CH_BASS, 110), (CH_BELLS, 96), (CH_WINDS, 88),
                  (CH_ORGAN, 80), (CH_CRYSTAL, 92), (CH_DRUMS, 105),
                  (CH_STRINGS, 50)):
        sc.cc(ch, 11, v, T0)              # sane expression baselines
    # L1 opens the movement alone after the loud M2: full expression while
    # exposed (480-520), easing to the 100 baseline as L2 enters (the synth
    # squares CC11, so 127 -> 100 is ~-4 dB) — lifts the floor of the
    # near-inaudible opening trough without touching the terraced build.
    en.cc_curve(sc, CH_STEEL, 11, [(T0, 127), (_cyc(8), 112),
                                   (_cyc(10), 100)], step=1.0)


# ---------------------------------------------------------------------------
# The lattice — three guitars in hocket (material.lattice_line 0/1/2).
# ---------------------------------------------------------------------------

def _lattice_cycle(sc, which: int, c: int, base_vel: float) -> None:
    ch = LATTICE_CH[which]
    acc = _accents(c)
    picks = m.LATTICE_SPLIT[which]
    notes = m.lattice_line(which)
    decorate_k = None
    if c % 4 == 3 and c >= LATTICE_ENTRY[which] + 2 and c < 63:
        # one diatonic neighbour turn per line, rotating around the line
        elig = [k for k, (_d, s, d) in enumerate(notes)
                if s >= 0.5 and d >= 1.0]
        if elig:
            decorate_k = elig[(c // 4 + which) % len(elig)]
    for k, (deg, start, dur) in enumerate(notes):
        v = int(round(base_vel + (11 if picks[k] in acc else 0)))
        b = _cyc(c) + start
        p = en.pitch(D3, MODE, deg)
        if k == decorate_k:
            nb = deg + (1 if (c // 4 + which) % 2 == 0 else -1)
            sc.note(ch, p, b, 0.45, v, jt=4, jv=4)
            sc.note(ch, en.pitch(D3, MODE, nb), b + 0.5, 0.22,
                    max(1, v - 10), jt=4, jv=4)
            sc.note(ch, p, b + 0.75, max(0.35, dur - 0.8), v - 4, jt=4, jv=4)
        else:
            sc.note(ch, p, b, dur, v, jt=4, jv=4)


def _lattice(sc) -> None:
    for which in range(3):
        entry = LATTICE_ENTRY[which]
        for c in range(entry, CYCLES):
            base = lerp(55.0, 72.0, min(c, 55) / 55.0)
            if c >= TUTTI:
                base += 13.0              # the cycles 56-63 tutti build
            if c - entry == 0:            # each line fades itself in
                base -= 6.0
            elif c - entry == 1:
                base -= 3.0
            if which == 0 and c < 8:      # lift the exposed opening line
                base += 10.0              # (480-520): a near-silent trough
            _lattice_cycle(sc, which, c, base)


# ---------------------------------------------------------------------------
# Bass — RIFF_10 from cycle 8, the D-C-B-A walk into the Long Climb.
# ---------------------------------------------------------------------------

def _bass(sc) -> None:
    for c in range(8, 63):
        b = _cyc(c)
        base = lerp(70.0, 92.0, (c - 8) / 54.0) + (8.0 if c >= TUTTI else 0.0)
        cross = c >= 15 and (c - 15) % 8 == 0     # every 8th cycle
        acc = m.RIFF_10_CROSS if cross else m.RIFF_10_ACCENTS
        for qi, (deg, start, dur) in enumerate(m.RIFF_10):
            v = int(round(base + (8 if qi in acc else -4)))
            sc.note(CH_BASS, en.pitch(D2, MODE, deg), b + start, dur * 0.88,
                    v, jt=3, jv=4)
    # final cycle: downbeat D, then the quarter-note walk D-C-B-A (796-799)
    sc.note(CH_BASS, D2, 795.0, 0.95, 96, jt=2, jv=3)
    for i, (p, v) in enumerate(((D2, 94), (D2 - 2, 90),
                                (D2 - 3, 88), (D2 - 5, 92))):
        sc.note(CH_BASS, p, 796.0 + i, 0.92, v, jt=2, jv=3)


# ---------------------------------------------------------------------------
# Crystal — the 3-beat 1-5-9 loop over the 5-beat cycle (realigns each 15
# beats) with the matching 15-beat CC10 autopan.  From cycle 8.
# ---------------------------------------------------------------------------

def _crystal(sc) -> None:
    t0, t_last = _cyc(8), 799.0
    en.autopan(sc, CH_CRYSTAL, t0, t_last - t0, lo=30, hi=98,
               period_beats=15.0, step=0.5)
    degs = (1, 5, 9)
    k = 0
    b = t0
    while b <= t_last + 1e-9:
        # A 15-beat breath: the loop drops out mid-plateau and re-enters,
        # the re-entry reading as a lift into the 760 tutti.  Phase (k) keeps
        # advancing so the loop resumes exactly where it would have been.
        if not 675.0 <= b < 690.0:
            v = lerp(48.0, 56.0, (b - t0) / (t_last - t0))
            v += (5 if k % 3 == 0 else 0) + (8 if b >= _cyc(TUTTI) else 0)
            sc.note(CH_CRYSTAL, en.pitch(D5, MODE, degs[k % 3]), b, 0.9,
                    int(round(v)), jt=3, jv=3)
        b += 1.0
        k += 1
    sc.cc(CH_CRYSTAL, 10, 76, 799.7)      # hand the pan back centred-ish


# ---------------------------------------------------------------------------
# Mandolin (prog 25 tremolo) — 32nd-note repeats doubling the accent quavers
# only, from cycle 24; tacet 48-55 (shade), back for the tutti.
# ---------------------------------------------------------------------------

def _mandolin(sc) -> None:
    for c in list(range(24, 48)) + list(range(TUTTI, CYCLES)):
        base = lerp(56.0, 64.0, (c - 24) / 39.0) + (10.0 if c >= TUTTI else 0.0)
        for qi in _accents(c):
            deg = m.RIFF_10[qi][0]
            p = en.pitch(D4, MODE, deg)
            b = _cyc(c) + qi * 0.5
            for r, dv in enumerate((-4, 0, 3, -2)):    # tremolo envelope
                sc.note(CH_BELLS, p, b + r * 0.125, 0.11,
                        int(round(base + dv)), jt=2, jv=3)


# ---------------------------------------------------------------------------
# Fiddle — THEME_B re-phrased for the 10/8: each 4-beat bar becomes one
# 5-beat cycle (the final note stretched into the breath), four cycles per
# statement.  CC68 slurs the quaver runs; delayed vibrato on the finals.
# ---------------------------------------------------------------------------

def _theme_b_phrases() -> list[list[tuple[int, float, float]]]:
    phrases: list[list[tuple[int, float, float]]] = [[], [], [], []]
    for deg, start, dur in m.THEME_B:
        phrases[int(start // 4)].append((deg, start % 4.0, dur))
    for ph in phrases:
        ph.sort(key=lambda x: x[1])
        deg, start, _dur = ph[-1]
        ph[-1] = (deg, start, max(0.75, 5.0 - start - 0.6))
    return phrases


def _fiddle_statement(sc, cs: int, vel: int) -> None:
    b0 = _cyc(cs)
    en.expr_curve(sc, CH_WINDS,
                  [(b0 - 0.5, vel + 2), (b0 + 8, vel + 22),
                   (b0 + 16, vel + 18), (b0 + 19.5, vel)], step=1.0)
    for i, ph in enumerate(_theme_b_phrases()):
        b = _cyc(cs + i)
        run_end = max(s + d for _deg, s, d in ph[:-1])
        sc.cc(CH_WINDS, 68, 127, b - 0.05)          # slur the quaver run
        sc.cc(CH_WINDS, 68, 0, b + run_end)         # re-pick the long final
        en.line(sc, CH_WINDS, b, D4, MODE, ph, vel, vel_end=vel + 7,
                gate=0.97, jt=4, jv=4)
        _fdeg, fstart, fdur = ph[-1]
        if fdur >= 1.2:
            en.vibrato(sc, CH_WINDS, b + fstart, fdur, depth=0.25,
                       cycles_per_beat=1.4, delay=0.3)


def _fiddle(sc) -> None:
    for cs, vel in ((16, 62), (22, 64), (28, 66), (36, 68)):
        _fiddle_statement(sc, cs, vel)
    _fiddle_statement(sc, TUTTI, 76)                # tutti reprise
    # the last call: one long high D floating over the build, echo-thrown
    sc.note(CH_WINDS, en.pitch(D4, MODE, 8), 781.0, 7.5, 84, jt=3, jv=3)
    en.vibrato(sc, CH_WINDS, 781.0, 7.5, depth=0.3, cycles_per_beat=1.3,
               delay=0.6)
    en.expr_curve(sc, CH_WINDS, [(780.8, 88), (788.5, 50)], step=0.5)
    en.echo_throw(sc, CH_WINDS, 787.0, base=20, peak=85, release=2.5)


# ---------------------------------------------------------------------------
# Organ flutes — the THEME_C chorale under the texture from cycle 32,
# then sustained root-fifth dyads carrying the tutti into the seam.
# ---------------------------------------------------------------------------

def _organ(sc) -> None:
    for cs, third, vel in ((32, False, 48), (40, True, 50), (48, True, 52)):
        b = _cyc(cs)
        en.expr_curve(sc, CH_ORGAN, [(b - 1, 50), (b + 14, 72), (b + 31, 55)],
                      step=1.0)
        en.line(sc, CH_ORGAN, b, D3, MODE, m.THEME_C, vel, vel_end=vel + 6,
                gate=1.02, jt=3, jv=3)
        if third:                          # second voice a diatonic third down
            en.line(sc, CH_ORGAN, b, D3, MODE,
                    [(d - 2, s, dur) for d, s, dur in m.THEME_C],
                    vel - 8, vel_end=vel - 2, gate=1.02, jt=3, jv=3)
    # tutti support: root-fifth dyads, i-i-bVII-i, then the held seam dyad
    en.expr_curve(sc, CH_ORGAN, [(759, 62), (770, 74), (784, 78), (797.5, 46)],
                  step=1.0)
    for b, deg, dur, v in ((760.0, 1, 4.8, 54), (765.0, 1, 4.8, 55),
                           (770.0, 0, 4.8, 56), (775.0, 1, 4.8, 57),
                           (780.0, 1, 3.8, 58)):
        root = en.pitch(D3, MODE, deg)
        sc.note(CH_ORGAN, root, b, dur, v, jt=3, jv=3)
        sc.note(CH_ORGAN, root + 7, b, dur, v - 6, jt=3, jv=3)
    sc.note(CH_ORGAN, D3, 784.0, 13.5, 56, jt=3, jv=3)       # ends ~797.5
    sc.note(CH_ORGAN, D3 + 7, 784.0, 13.5, 50, jt=3, jv=3)


# ---------------------------------------------------------------------------
# Strings — cycle-root pads (i-i-bVII-i per 4 cycles) from cycle 40 with
# CC11 swells; the Dm(add9) seam chord at 784 sustaining across 800.
# ---------------------------------------------------------------------------

def _strings(sc) -> None:
    pts: list[tuple[float, int]] = [(676.0, 38)]
    for g in (40, 44, 48, 52):
        b = _cyc(g)
        pts += [(b, 42), (b + 10.0, 70), (b + 19.5, 48)]
    pts += [(_cyc(TUTTI), 90), (783.5, 90), (784.0, 80), (800.0, 40)]
    en.expr_curve(sc, CH_STRINGS, pts, step=1.0)
    for c in range(40, 60):
        deg = 0 if c % 4 == 2 else 1                # bVII on cycle 3 of 4
        root = en.pitch(D3, MODE, deg)
        v = int(round(lerp(44.0, 54.0, (c - 40) / 19.0)
                      + (6 if c >= TUTTI else 0)))
        dur = 5.15 if c < 59 else 4.6               # lift before the strike
        sc.note(CH_STRINGS, root, _cyc(c), dur, v, jt=4, jv=3)
        sc.note(CH_STRINGS, root + 12, _cyc(c), dur, v - 5, jt=4, jv=3)
    # the seam chord: Dm(add9), struck at ~784, ringing across 800 into M4
    for i, p in enumerate((D3, D3 + 7, D4, D4 + 2, D4 + 3)):
        sc.note(CH_STRINGS, p, 784.0 + 0.03 * i, 20.0 - 0.05 * i,
                66 - 2 * i, jt=3, jv=3)


# ---------------------------------------------------------------------------
# Percussion — shaker 16ths + tambourine on the group starts from cycle 32;
# no kit: the lattice IS the rhythm.
# ---------------------------------------------------------------------------

def _drums(sc) -> None:
    for c in range(32, CYCLES):
        b = _cyc(c)
        boost = 8 if c >= TUTTI else 0
        acc = _accents(c)
        for k in range(20):                          # 16ths (quaver = 0.5)
            t = b + k * 0.25
            if t > 799.5:
                break
            qi = k // 2
            v = 28 + (11 if k % 2 == 0 else 0) \
                + (7 if k % 2 == 0 and qi in acc else 0) + boost
            sc.hit(SHAKER, t, v, jt=2, jv=4)
        for qi in acc:                               # group starts
            sc.hit(TAMBOURINE, b + qi * 0.5, 50 + boost, jt=2, jv=4)


# ---------------------------------------------------------------------------

def build(sc) -> None:
    _setup(sc)
    _lattice(sc)
    _bass(sc)
    _crystal(sc)
    _mandolin(sc)
    _fiddle(sc)
    _organ(sc)
    _strings(sc)
    _drums(sc)
