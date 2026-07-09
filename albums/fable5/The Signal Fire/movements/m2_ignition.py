"""m2_ignition — Movement 2 "Ignition" (beats 176-480, A dorian, 100 bpm).

The Mastermind funk engine, assembled by terraces:

  176  kick pattern alone (a crash marks the ignition)
  208  16th hats with accents; fingered bass loops RIFF_FUNK (ghosts at
       vel-30; every 4th bar a fill: walk-up 5-6-7-8 / drop to 0-1 /
       octave kick, rotating)
  240  snare backbeat + ghosts; palm-mute chug (ch10, 16ths on 1 and 5);
       wah guitar scratches (ch11, CC74 sine LFO 40-100 at 0.5 cycles/beat,
       parked at 127 whenever it rests); Hammond states THEME_B, Leslie slow
  256  Hammond stabs on the &-of-2 (i triad) and 4 (bVII triad); wah riff
       top voice joins
  272  wah guitar answers THEME_B an octave up; Leslie ramps 0->127 into 304
  288  nylon offbeat upstrokes (vel ~45, reggae-light)
  304  first peak: antiphonal 2-bar call (ch10, pan 30) / answer (ch11,
       pan 98) cells built from THEME_B halves; whistle floats THEME_A_FRAG
  336  piano offbeat comping (Am7 on the &-of-2, G6 pushed to the "and-a"
       of 4); second Leslie ramp into the 368 peak
  400  THE BREAK: drums drop to kick+hats, bass feature with slide bends
       0->1 (pre-bend -2 ramps to centre), organ swell (CC11 + Leslie ramp)
       rebuilding into...
  432  full tutti; ch12 lead's first violining wails (CC11 0->90 swells,
       -2 pre-bend sliding up into pitch, delayed vibrato, recentred);
       the last four bars displace the beat-3& kick to the "e" — a push
       that also keeps the stacked attacks click-clean in the render
  464  dissolve: drums thin to hats, bass pivots to RIFF_10 rooted on D
       (cycles at 464/469/474, last pickup note-on at 479.5), warm pad
       swells into the Lattice seam

CC91 sits at 55 on every channel used (the distance arc).  End state:
ch11 CC74 parked at 127, ch4 CC1 back at 0 by 480, all bends recentred.
"""

from __future__ import annotations

import engine as en
import material as m
from conductor import (CH_BASS, CH_DRUMS, CH_LEAD, CH_NYLON, CH_ORGAN,
                       CH_PAD, CH_PIANO, CH_RHYTHM, CH_WAH, CH_WINDS)
from engine import lerp, n

T0, T1 = 176.0, 480.0
MODE = "dorian"
A1, A2, A3, A4 = n("A1"), n("A2"), n("A3"), n("A4")
D2 = n("D2")

MY_CHANNELS = (CH_PIANO, CH_PAD, CH_BASS, CH_ORGAN, CH_NYLON, CH_DRUMS,
               CH_RHYTHM, CH_WAH, CH_LEAD, CH_WINDS)

# Antiphonal cells from 304: (start beat, degree shift, THEME_B half offset).
CELLS = ((304.0, 0, 0.0), (320.0, 0, 8.0), (336.0, 2, 0.0), (352.0, 0, 8.0))


def bar(i: int) -> float:
    return T0 + 4.0 * i


def _theme_half(offset: float) -> list[tuple[int, float, float]]:
    """One 8-beat half of THEME_B, rebased to start at 0."""
    return [(d, s - offset, dur) for (d, s, dur) in m.THEME_B
            if offset <= s < offset + 8.0]


# ---------------------------------------------------------------------------
# Drums — one element per 8 bars: kick 176, hats 208, snare 240.
# ---------------------------------------------------------------------------

_KICK = ((0.0, 1.0), (0.75, 0.78), (1.75, 0.84), (2.5, 0.94), (3.5, 0.8))
_HAT_16 = [k * 0.25 for k in range(16)]
_HAT_FUNK = [0.0, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 2.75, 3.0, 3.5]
_HAT_8 = [k * 0.5 for k in range(8)]
_FILL_BARS = {15, 31, 47, 55, 63, 71}
_BIG_FILLS = {55, 63}


def _drums(sc: en.Score) -> None:
    for i in range(76):
        b = bar(i)
        fill = i in _FILL_BARS
        big = i in _BIG_FILLS
        # kick — the first element; a heartbeat in the break; out at 464
        if i < 72:
            if 56 <= i < 64:
                sc.hit(36, b, 80)
                sc.hit(36, b + 2.5, 70)
            else:
                base = (lerp(78, 92, i / 8) if i < 8 else
                        94 if i < 16 else 96 if i < 64 else 93)
                for s, w in _KICK:
                    if fill and big and s >= 2.5:
                        continue
                    if i >= 68 and s == 2.5:   # late-tutti displaced kick
                        s = 2.75
                    sc.hit(36, b + s, int(base * w))
        # hats — 16ths w/ accents from 208; funk pattern mid-movement
        if i >= 8:
            if 56 <= i < 64:
                grid, hv = _HAT_8, 50
            elif i >= 72:
                grid, hv = _HAT_8, int(lerp(52, 38, (i - 72) / 4))
            elif 16 <= i < 48:
                grid, hv = _HAT_FUNK, 58
            else:
                grid, hv = _HAT_16, (54 if i < 16 else 62 if i < 56 else 64)
            open_hat = (i % 4 == 1 and 16 <= i < 72 and not fill)
            for s in grid:
                if fill and s >= 2.5:
                    continue
                if open_hat and s == 3.75:
                    continue
                acc = 12 if s % 1.0 == 0 else (4 if s % 0.5 == 0 else -4)
                sc.hit(42, b + s, hv + acc)
            if open_hat:
                sc.hit(46, b + 3.75, hv + 8)
        # snare — backbeat + ghosts from 240; silent in break and dissolve
        if (16 <= i < 56 or 64 <= i < 72):
            sv = 100 if i < 64 else 104
            sc.hit(38, b + 1, sv)
            if not fill:
                sc.hit(38, b + 3, sv)
                if i % 2 == 1:
                    sc.hit(38, b + 1.75, 42)
                if i % 4 == 2:
                    sc.hit(38, b + 3.25, 40)
        # fills each 16 bars
        if fill:
            if big:
                seq = ((2.5, 38, 80), (2.75, 38, 88), (3.0, 48, 92),
                       (3.25, 47, 96), (3.5, 45, 100), (3.75, 43, 104))
            else:
                seq = ((3.0, 38, 72), (3.25, 38, 82),
                       (3.5, 38, 90), (3.75, 38, 97))
            for s, d, v in seq:
                sc.hit(d, b + s, v)
    for beat, vel in ((176.0, 85), (240.0, 92), (304.0, 96),
                      (368.0, 96), (432.0, 102)):
        sc.hit(49, beat, vel)
    sc.hit(57, 400.0, 68)          # softer crash colours the break
    sc.hit(46, 464.0, 60)          # open hat marks the dissolve


# ---------------------------------------------------------------------------
# Bass — RIFF_FUNK engine from 208, feature in the break, RIFF_10-in-D out.
# ---------------------------------------------------------------------------

_FILL_WALK = ((5, 3.0, 0.25), (6, 3.25, 0.25), (7, 3.5, 0.25), (8, 3.75, 0.25))
_FILL_DROP = ((0, 3.0, 0.5), (1, 3.5, 0.45))
_FILL_OCT = ((1, 3.0, 0.25), (8, 3.25, 0.25), (1, 3.5, 0.25), (8, 3.75, 0.25))
_FILLS = (_FILL_WALK, _FILL_DROP, _FILL_OCT)
_ACCENTS = {0.0: 6, 1.5: 2, 2.0: 3}


def _bass_bar(sc: en.Score, b: float, vel: int, fill=None,
              slide: bool = False) -> None:
    for deg, s, d in m.RIFF_FUNK:
        if fill is not None and s >= 3.0:
            continue
        v = vel + _ACCENTS.get(s, 0) - (4 if s in (0.5, 2.75) else 0)
        sc.note(CH_BASS, en.pitch(A1, MODE, deg), b + s, d * 0.95, v, jt=4)
    for deg, s, d in m.RIFF_FUNK_GHOSTS:
        if fill is None or s < 3.0:
            sc.note(CH_BASS, en.pitch(A1, MODE, deg), b + s, d * 0.8,
                    vel - 30, jt=4)
    if fill is not None:
        for k, (deg, s, d) in enumerate(fill):
            sc.note(CH_BASS, en.pitch(A1, MODE, deg), b + s, d * 0.9,
                    vel + 2 + 2 * k, jt=4)
    if slide:  # slide 0->1: pre-bent -2 semis, gliding up into the tonic
        en.bend_ramp(sc, CH_BASS, b, b + 0.35, -2.0, 0.0, steps=8)


def _bass(sc: en.Score) -> None:
    fills = 0
    for r in range(48):                            # 208-400: the engine
        b = 208.0 + 4.0 * r
        if b < 240:
            vel = int(lerp(85, 90, r / 8))
        elif b < 304:
            vel = int(lerp(88, 94, (b - 240) / 64))
        elif b < 368:
            vel = int(lerp(92, 97, (b - 304) / 64))
        else:
            vel = int(lerp(96, 100, (b - 368) / 32))
        fill = None
        if r % 4 == 3:
            fill = _FILLS[fills % 3]
            fills += 1
        _bass_bar(sc, b, vel, fill)
    for r in range(8):                             # 400-432: the feature
        b = 400.0 + 4.0 * r
        vel = 98 + r // 2
        if r == 5:                                 # high answering lick
            lick = ((8, 0.0, 0.5), (10, 0.5, 0.5), (8, 1.0, 0.5),
                    (7, 1.5, 0.5), (5, 2.0, 1.0), (4, 3.0, 0.5),
                    (3, 3.5, 0.5))
            for deg, s, d in lick:
                sc.note(CH_BASS, en.pitch(A1, MODE, deg), b + s, d * 0.9,
                        vel, jt=4)
        else:
            fill = (_FILL_WALK if r == 7 else
                    _FILL_DROP if r == 3 else None)
            _bass_bar(sc, b, vel, fill, slide=(r % 2 == 0))
    for r in range(8):                             # 432-464: tutti
        b = 432.0 + 4.0 * r
        fill = None
        if r % 4 == 3:
            fill = _FILLS[fills % 3]
            fills += 1
        _bass_bar(sc, b, 96, fill)
    # 464-480 dissolve: RIFF_10 rooted on D, cycling down in velocity
    for c, vel in ((464.0, 88), (469.0, 80), (474.0, 72)):
        for q, (deg, s, d) in enumerate(m.RIFF_10):
            v = vel + (6 if q in m.RIFF_10_ACCENTS else 0) - (4 if q == 1 else 0)
            sc.note(CH_BASS, en.pitch(D2, MODE, deg), c + s, d * 0.92, v, jt=4)
    sc.note(CH_BASS, en.pitch(D2, MODE, 0), 479.0, 0.45, 66, jt=3)
    sc.note(CH_BASS, en.pitch(D2, MODE, 1), 479.5, 0.45, 70, jt=3)


# ---------------------------------------------------------------------------
# Rhythm guitar (ch10, pan 30) — palm-mute chug from 240; antiphonal calls.
# ---------------------------------------------------------------------------

_CHUG_PAT = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
             2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5)
_CHUG_FIFTH = {0.75, 1.5, 2.75, 3.5}


def _chug_bar(sc: en.Score, b: float, vel: int, start: float = 0.0) -> None:
    for s in _CHUG_PAT:
        if s < start:
            continue
        deg = 5 if s in _CHUG_FIFTH else 1
        acc = 7 if s % 1.0 == 0 else (0 if s % 0.5 == 0 else -5)
        sc.note(CH_RHYTHM, en.pitch(A2, MODE, deg), b + s, 0.16,
                vel + acc, jt=3, jv=3)


def _rhythm(sc: en.Score) -> None:
    for i in range(16, 32):                        # 240-304
        _chug_bar(sc, bar(i), 64)
    for cs, sh, off in CELLS:                      # 304-368: call, then chug
        en.line(sc, CH_RHYTHM, cs, A3, MODE, _theme_half(off), 78,
                vel_end=84, shift=sh, gate=0.9, jt=5)
        _chug_bar(sc, cs + 8.0, 66)
        _chug_bar(sc, cs + 12.0, 66)
    for i in range(48, 56):                        # 368-400: peak groove
        _chug_bar(sc, bar(i), 70, start=(2.0 if i == 48 else 0.0))
    for i in range(64, 72):                        # 432-464: tutti
        _chug_bar(sc, bar(i), 74, start=(2.0 if i in (64, 68) else 0.0))
    # power-5th strums open the section peaks
    for t, v in ((368.0, 80), (432.0, 84), (448.0, 82)):
        en.strum(sc, CH_RHYTHM, [A2, A2 + 7, A3], t, 1.8, v, spread=0.03)


# ---------------------------------------------------------------------------
# Wah guitar (ch11, pan 98) — the Mastermind sound.  CC74 LFO runs whenever
# it plays; parked at 127 in every rest.
# ---------------------------------------------------------------------------

_SCR_DENSE = (0.0, 0.25, 0.5, 1.0, 1.25, 1.75, 2.0, 2.25, 2.75, 3.0, 3.5, 3.75)
_SCR_SPARSE = (0.5, 1.0, 1.5, 2.5, 3.0, 3.5)


def _scratch_bar(sc: en.Score, b: float, vel: int, dense: bool = True) -> None:
    for s in (_SCR_DENSE if dense else _SCR_SPARSE):
        v = min(70, max(55, vel + (8 if s % 1.0 == 0 else 0)
                        - (4 if s % 0.5 == 0.25 else 0)))
        sc.note(CH_WAH, en.pitch(A3, MODE, 1), b + s, 0.2, v, jt=3, jv=3)


def _wah_riff_bar(sc: en.Score, b: float, vel: int) -> None:
    for deg, s, d in m.RIFF_FUNK:                  # riff top voice
        acc = 6 if s in (0.0, 2.0) else 0
        sc.note(CH_WAH, en.pitch(A3, MODE, deg), b + s, d * 0.85,
                vel + acc, jt=3)
    for s in (1.25, 3.75):                         # scratches in the gaps
        sc.note(CH_WAH, en.pitch(A3, MODE, 1), b + s, 0.2, 58, jt=3, jv=3)


def _wah_guitar(sc: en.Score) -> None:
    sc.cc(CH_WAH, 74, 127, T0)                     # parked until it plays
    for k in range(4):                             # 240-256: scratches
        _scratch_bar(sc, 240.0 + 4.0 * k, 56 + k)
    for k in range(2):                             # 256-264: riff top voice
        _wah_riff_bar(sc, 256.0 + 4.0 * k, 76)
    en.wah(sc, CH_WAH, 240.0, 23.75)
    sc.cc(CH_WAH, 74, 127, 264.0)                  # two-bar breath
    en.line(sc, CH_WAH, 272.0, A3, MODE, m.THEME_B, 78, vel_end=86,
            octave=1, gate=0.92)                   # the clean-guitar answer
    for k in range(3):                             # 288-300
        _wah_riff_bar(sc, 288.0 + 4.0 * k, 78)
    en.wah(sc, CH_WAH, 272.0, 27.75)
    sc.cc(CH_WAH, 74, 127, 300.0)                  # breath into the peak
    for cs, sh, off in CELLS:                      # 304-368: answers (R)
        _scratch_bar(sc, cs, 55, dense=False)
        _scratch_bar(sc, cs + 4.0, 55, dense=False)
        en.line(sc, CH_WAH, cs + 8.0, A3, MODE, _theme_half(off), 82,
                vel_end=88, shift=sh, octave=1, gate=0.9, jt=5)
    for k in range(7):                             # 368-396: peak riffing
        _wah_riff_bar(sc, 368.0 + 4.0 * k, 78 + k // 2)
    en.wah(sc, CH_WAH, 304.0, 91.75)
    sc.cc(CH_WAH, 74, 127, 396.0)                  # rests through the break
    for k in range(8):                             # 432-464: tutti
        _wah_riff_bar(sc, 432.0 + 4.0 * k, 75 + k // 2)
    en.wah(sc, CH_WAH, 432.0, 31.75)
    sc.cc(CH_WAH, 74, 127, 464.0)                  # end state: parked at 127


# ---------------------------------------------------------------------------
# Hammond (ch4) — THEME_B call, stabs on the &-of-2 and 4, Leslie ramps.
# ---------------------------------------------------------------------------

def _organ(sc: en.Score) -> None:
    sc.cc(CH_ORGAN, 1, 0, T0)                      # Leslie slow at entry
    sc.cc(CH_ORGAN, 11, 105, T0)
    en.line(sc, CH_ORGAN, 240.0, A3, MODE, m.THEME_B, 74, vel_end=84,
            gate=0.95, jt=5)                       # the call
    for i in range(20, 72):                        # stabs, breathing 1-in-4
        b = bar(i)
        if 400.0 <= b < 432.0 or i % 4 == 3:
            continue
        vel = (72 if b < 304 else 76 if b < 368 else
               80 if b < 400 else 82)
        for p in en.triad(A3, MODE, 1):            # i triad on the &-of-2
            sc.note(CH_ORGAN, p, b + 1.5, 0.35, vel, jt=3, jv=3)
        for p in en.triad(A2, MODE, 7):            # bVII triad on 4
            sc.note(CH_ORGAN, p, b + 3.0, 0.4, vel - 4, jt=3, jv=3)
    # break: the swell that rebuilds (CC11 + Leslie ramp into the tutti)
    for p in (A3, A3 + 3, A3 + 7, A3 + 14):        # Am add9
        sc.note(CH_ORGAN, p, 408.0, 24.0, 60, jt=4, jv=2)
    en.expr_curve(sc, CH_ORGAN, [(408.0, 35), (432.0, 115)], step=0.5)
    sc.cc(CH_ORGAN, 11, 105, 436.0)
    # Leslie choreography: 8-bar spin-ups into each peak, back to 20 after
    en.leslie(sc, CH_ORGAN, 272.0, 304.0, 0, 127)
    sc.cc(CH_ORGAN, 1, 20, 305.0)
    en.leslie(sc, CH_ORGAN, 336.0, 368.0, 20, 127)
    sc.cc(CH_ORGAN, 1, 20, 369.0)
    en.leslie(sc, CH_ORGAN, 400.0, 432.0, 20, 127)
    sc.cc(CH_ORGAN, 1, 20, 436.0)
    en.leslie(sc, CH_ORGAN, 464.0, 474.0, 20, 0)   # back to 0 by 480


# ---------------------------------------------------------------------------
# Colour layers — nylon skank, piano comps, whistle floats, lead wails, pad.
# ---------------------------------------------------------------------------

def _nylon(sc: en.Score) -> None:
    am = [A3 + 7, A4, A4 + 3]                      # E4 A4 C5 upstroke
    g7 = [A3 + 5, A3 + 10, A4 + 2]                 # D4 G4 B4
    for i in range(28, 72):                        # 288-464 minus the break
        b = bar(i)
        if 400.0 <= b < 432.0:
            continue
        en.strum(sc, CH_NYLON, am, b + 1.5, 0.35, 45, spread=0.02, down=False)
        en.strum(sc, CH_NYLON, g7, b + 3.5, 0.35, 42, spread=0.02, down=False)


def _piano(sc: en.Score) -> None:
    am7 = (60, 64, 67)                             # C4 E4 G4
    g6 = (59, 62, 67)                              # B3 D4 G4
    for i in list(range(40, 56)) + list(range(64, 72)):
        if i % 2:
            continue
        b = bar(i)
        for p in am7:
            sc.note(CH_PIANO, p, b + 1.75, 0.5, 58, jt=4, jv=3)
        for p in g6:                # the "and-a" push, off the beat-4 wall
            sc.note(CH_PIANO, p, b + 3.75, 0.6, 55, jt=4, jv=3)


def _whistle_frag(sc: en.Score, t: float, vel: int) -> None:
    en.line(sc, CH_WINDS, t, A4, MODE, m.THEME_A_FRAG, vel, gate=0.95, jt=4)
    en.vibrato(sc, CH_WINDS, t + 0.6, 2.4, depth=0.22,
               cycles_per_beat=1.2, delay=0.5)     # blooms on the long 5
    en.expr_curve(sc, CH_WINDS, [(t, 45), (t + 3.5, 75), (t + 8.0, 52)],
                  step=0.5)
    en.echo_throw(sc, CH_WINDS, t + 6.0, base=20, peak=85)


def _whistle(sc: en.Score) -> None:
    for t, vel in ((304.0, 66), (312.0, 55), (368.0, 70), (376.0, 59)):
        _whistle_frag(sc, t, vel)


def _lead(sc: en.Score) -> None:
    wails = ((434.0, n("E5"), 6.0, 92), (442.0, n("G5"), 5.0, 95),
             (450.0, n("A5"), 6.0, 98), (458.0, n("C6"), 5.0, 95))
    for t, p, dur, vel in wails:
        sc.bend(CH_LEAD, t - 0.15, -2.0)           # pre-bend a tone below
        sc.note(CH_LEAD, p, t, dur, vel, jt=3, jv=2)
        en.bend_ramp(sc, CH_LEAD, t, t + 0.6, -2.0, 0.0, steps=10)
        en.expr_curve(sc, CH_LEAD, [(t - 0.15, 0), (t + 1.5, 90)], step=0.1)
        en.vibrato(sc, CH_LEAD, t + 1.0, dur - 1.0, depth=0.3,
                   cycles_per_beat=1.3, delay=0.8)  # ends recentred


def _pad(sc: en.Score) -> None:
    for p, v in ((50, 52), (53, 50), (57, 54), (64, 56)):   # D minor add9
        sc.note(CH_PAD, p, 464.0, 17.0, v, jt=3, jv=2)
    en.expr_curve(sc, CH_PAD, [(464.0, 30), (479.5, 85)], step=0.5)


def build(sc: en.Score) -> None:
    for ch in MY_CHANNELS:                         # the distance arc
        sc.cc(ch, 91, 55, T0)
    _drums(sc)
    _bass(sc)
    _rhythm(sc)
    _wah_guitar(sc)
    _organ(sc)
    _nylon(sc)
    _piano(sc)
    _whistle(sc)
    _lead(sc)
    _pad(sc)
