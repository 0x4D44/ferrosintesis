"""m1_frost — Part One, Movement 1 "Frost" (beats 0-256, E aeolian, 92).

The Visitors, arriving.  The coldest, sparsest movement: one register at a
time, everything distant (high CC91) drawing slowly nearer, mean velocity
kept low (the whole movement sits in the 40-48 band, below M2).  Roadmap
section 4, M1:

  beat 0    ch1 pad: Em(add9) bed, aftertouch blooms 0->90->0 per 16-beat
            phrase (crescendo inside the held chords).
  beat 16   ch2 ice arp: COLD_CELL cells (cold_arp), CC74 45->95 across the
            movement, CC71 resonance rides 50->85->60 (the analog sweep),
            slow autopan; every 32 beats a variation (octave lift / passing
            9th) so it is not wallpaper.  Thins to single notes 248-256.
  beat 30   ch3 fretless: pedal E's with portamento (CC5~60, CC65 on),
            sliding between degrees 1 and 5; sparse; glide off by 250.
  beat 64   ch15 music box: THEME bars 1-2 fragments, high and icy, with
            echo throws.
  beat 128  ch4 low reed-organ (harmonium) cluster swells (CC11); ch9
            electro pulse (kick on 1&3, rim ticks; sparse).
  beat 176  ch6 choir I: the FIRST HUM — theme phrase 1 (16 beats),
            CC70=0 (mm), low octave (~E3), vel ~50, aftertouch swell
            mid-phrase.  The guests knock.
  Seam OUT: arp thins to single notes 248-256; the last ch1 pad chord is
            struck at 240 and sustains across into M2 (rings to ~258).
            No pitch bends anywhere; portamento off by 250 — nothing to
            recentre at 256.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

AEO = "aeolian"

T0, T1 = 0.0, 256.0
ARP_START = 16.0
ARP_END = 248.0                 # arp thins to single notes over 248-256

ARP_BASE = n("E4")              # 64 — the ice sequencer's degree-1 anchor
PAD_VOICES = [n("E3"), n("G3"), n("B3"), n("F#4")]     # Em(add9): E G B F#
ORGAN_VOICES = [n("E2"), n("G2"), n("B2"), n("F#3")]   # low reed cluster
BASS_BASE = n("E2")             # 40 — fretless pedal
MBOX_BASE = n("E5")             # 76 — high, icy music box
CHOIR_BASE = n("E3")            # 52 — the hum sits low in the choir range


# ---------------------------------------------------------------------------
# Controllers — the distance arc and the ice arp's analog sweep
# ---------------------------------------------------------------------------
def _controllers(sc):
    # CC91 distance arc: the guests approach from the cold night — every
    # voice starts far (wet) and draws a little nearer across the movement.
    for ch in (cd.CH_PAD, cd.CH_ARP, cd.CH_BELLS, cd.CH_CHOIR1,
               cd.CH_ORGAN, cd.CH_BASS):
        en.cc_curve(sc, ch, 91, [(0.0, 88), (ARP_END, 72)], step=16.0)

    # The ice arp's analog sweep: filter cutoff opens 45->95 while the
    # resonance rides up then eases back (50->85->60).
    en.cc_curve(sc, cd.CH_ARP, 74, [(ARP_START, 45), (ARP_END, 95)], step=4.0)
    en.cc_curve(sc, cd.CH_ARP, 71,
                [(ARP_START, 50), (140.0, 85), (ARP_END, 60)], step=4.0)

    # Slow autopan — the sequencer drifts across the stereo field.  A fine
    # step keeps the pan motion smooth (coarse steps zipper a sustained,
    # resonant voice).
    en.autopan(sc, cd.CH_ARP, ARP_START, ARP_END - ARP_START,
               lo=48, hi=88, period_beats=32.0, step=0.25)


# ---------------------------------------------------------------------------
# ch1 pad — Em(add9) bed with aftertouch blooms inside every 16-beat phrase
# ---------------------------------------------------------------------------
def _pad(sc):
    ch = cd.CH_PAD
    for p in range(16):                         # sixteen 16-beat phrases
        t = p * 16.0
        seam = (p == 15)                        # the last chord carries over
        dur = 18.0 if seam else 15.6
        base_v = int(lerp(38, 44, p / 15.0))
        for i, pp in enumerate(PAD_VOICES):
            sc.note(ch, pp, t, dur, base_v - i, jt=4, jv=3)
        # aftertouch bloom 0 -> 90 -> 0, kept strictly inside the movement.
        top = min(255.0, t + 16.0 - 0.5)
        en.at_curve(sc, ch, [(t, 0), (t + 8.0, 90), (top, 0)], step=0.5)


# ---------------------------------------------------------------------------
# ch2 ice arp — cold_arp cells from 16, a variation every 32 beats, thinning
# ---------------------------------------------------------------------------
def _arp(sc):
    ch = cd.CH_ARP
    nbars = int((ARP_END - ARP_START) // 4)     # 58 two-beat... four-beat bars
    var_i = 0
    for idx in range(nbars):
        beat = ARP_START + 4.0 * idx
        grow = idx / (nbars - 1)
        vbar = int(lerp(40, 47, grow))
        cell = m.cold_arp(idx)
        variation = (beat - ARP_START) % 32.0 == 0.0    # every 32 beats
        lift = variation and var_i % 2 == 0             # octave lift
        ninth = variation and var_i % 2 == 1            # passing 9th (add9)
        if variation:
            var_i += 1
        for slot, (deg, s, dur) in enumerate(cell):
            d = 9 if (ninth and slot == 5) else deg
            oct_shift = 12 if lift else 0
            p = en.pitch(ARP_BASE, AEO, d) + oct_shift
            v = vbar + (4 if slot == 0 else 0)
            sc.note(ch, p, beat + s, dur * 0.9, v, jt=3, jv=3)

    # Seam: thin to single sustained notes over 248-256 (pulse i - v - i - v).
    for k, beat in enumerate((248.0, 250.0, 252.0, 254.0)):
        deg = 1 if k % 2 == 0 else 5
        sc.note(ch, en.pitch(ARP_BASE, AEO, deg), beat, 1.6,
                int(lerp(44, 40, k / 3.0)), jt=3, jv=2)


# ---------------------------------------------------------------------------
# ch3 fretless bass — sparse pedal E's, portamento slides between 1 and 5
# ---------------------------------------------------------------------------
def _bass(sc):
    ch = cd.CH_BASS
    en.portamento_on(sc, ch, 30.0, time_cc=60)          # CC5=60, CC65 on
    # (beat, degree, dur): consecutive notes glide (the fretless slide);
    # the 5th (degree 5) is reached by portamento and released back to 1.
    plan = [(32.0, 1, 4.0), (48.0, 1, 3.0), (56.0, 5, 2.0),
            (72.0, 1, 6.0), (96.0, 1, 4.0), (112.0, 5, 2.0),
            (128.0, 1, 6.0), (160.0, 1, 4.0), (176.0, 1, 6.0),
            (200.0, 5, 3.0), (216.0, 1, 4.0), (232.0, 1, 4.0),
            (244.0, 5, 2.0)]
    for beat, deg, dur in plan:
        v = int(lerp(40, 45, (beat - 32.0) / 212.0))
        sc.note(ch, en.pitch(BASS_BASE, AEO, deg), beat, dur, v, jt=4, jv=3)
    en.portamento_off(sc, ch, 250.0)                    # glide off before 256


# ---------------------------------------------------------------------------
# ch4 harmonium — low reed-organ cluster swells from 128 (CC11)
# ---------------------------------------------------------------------------
def _organ(sc):
    ch = cd.CH_ORGAN
    sc.cc(ch, 11, 0, 128.0)
    for t, dur in ((128.0, 32.0), (160.0, 32.0), (192.0, 32.0), (224.0, 30.0)):
        for i, pp in enumerate(ORGAN_VOICES):
            sc.note(ch, pp, t, dur + 1.0, 40 - i, jt=4, jv=3)
        en.expr_curve(sc, ch,
                      [(t, 10), (t + dur * 0.5, 58), (t + dur - 1.0, 16)],
                      step=1.0)


# ---------------------------------------------------------------------------
# ch15 music box — THEME bars 1-2 fragments from 64, high/icy, echo throws
# ---------------------------------------------------------------------------
def _music_box(sc):
    ch = cd.CH_BELLS
    frag = m.THEME_FRAG                          # THEME[:6], beats 0-8
    for st in (64.0, 96.0, 128.0, 168.0, 208.0, 232.0):
        en.line(sc, ch, st, MBOX_BASE, AEO, frag, 46, vel_end=52,
                gate=0.6, jt=5, jv=3)
        en.echo_throw(sc, ch, st + 4.0, base=20, peak=85, release=2.5)


# ---------------------------------------------------------------------------
# ch6 choir I — the FIRST HUM at 176 (theme phrase 1, mm, low, swelling)
# ---------------------------------------------------------------------------
def _choir_hum(sc):
    ch = cd.CH_CHOIR1
    en.vowel(sc, ch, 0, 176.0)                   # CC70 = 0: "mm"
    en.line(sc, ch, 176.0, CHOIR_BASE, AEO, m.THEME[:12], 48, vel_end=52,
            gate=0.95, jt=5, jv=3)               # phrase 1 = beats 0-16
    # Aftertouch swell mid-phrase: the hum blooms and settles.
    en.at_curve(sc, ch, [(180.0, 0), (186.0, 82), (190.0, 20)], step=0.25)


# ---------------------------------------------------------------------------
# ch9 drums — sparse electro pulse from 128 (kick on 1 & 3, rim ticks)
# ---------------------------------------------------------------------------
def _drums(sc):
    beat = 128.0
    while beat < 256.0:                          # kick on 1 & 3 of each bar
        # A defined electro thud: punchy enough to read as an attack over
        # the sustained bed (a quiet kick buried in the bed renders as a
        # click, not a hit), but still restrained for the cold texture.
        sc.hit(36, beat, int(lerp(58, 66, (beat - 128.0) / 128.0)))
        beat += 2.0
    bar = 128.0
    while bar < 256.0:                           # side-stick rim ticks
        sc.hit(37, bar + 1.5, 34)
        if int(bar // 4) % 2 == 0:
            sc.hit(37, bar + 3.5, 32)
        bar += 4.0


def build(sc):
    _controllers(sc)
    _pad(sc)
    _arp(sc)
    _bass(sc)
    _organ(sc)
    _music_box(sc)
    _choir_hum(sc)
    _drums(sc)
