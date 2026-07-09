"""m3_footsteps — Part One, Movement 3 "Footsteps in the Hall"
(beats 544-864, E aeolian, 7/8 (3+2+2) at 544, 4/4 coda at 832, 92->104).

The Visitors, inside.  Roadmap section 4, M3:

  ch3 bass (prog 33): FOOTSTEPS cell, relentless, vel 70->90.
  ch10 palm-mute (28): chug on the 3+2+2 accents.
  ch2 ice arp: COLD_CELL compressed to 7/8, CC71 high (80-100),
        CC74 sweeps per 8 bars.
  ch9: 7/8 kit — kick on group starts, hats quavers, snare on group 2.
  576   ch12 portamento synth lead: bend_range(12) + CC65 on / CC5 ~70;
        gliding phrases every 16 bars; ~768 whammy dive -12 over 2 beats;
        ~800 THE scream: dive -12, rip back to 0; bend_range reset to 2
        and bend recentred by 832.
  ch5 strings: tension pads, aeolian b6-5 neighbor oscillations.
  704   ch6 choir: fragmented "mm" stabs on group starts, aftertouch spikes.
  832   4/4 coda: only ch4 organ swell + ch6 choir I hum (theme bars 1-2)
        ending ON DEGREE 2, dying to nothing by 860.  Unresolved.

This is the driving, anxious PEAK of Part One (mean velocity band 68-78,
the densest movement).  Everything layers in one at a time over the
relentless footsteps; the coda pulls the floor out from under it.

Pitch discipline for the bend controller: ferrosintesis's sc.bend maps its
`semis` argument assuming the default +/-2 range (raw = 8192 + semis/2 *
8192).  Once ch12's RPN range is widened to 12, a bend to a fraction f of
that range is written as sc.bend(..., 2 * f): f = -1 (arg -2) reads back as
a full -12-semitone dive.  So the whammy ramps run 0 -> -2 in the argument,
which the RPN-aware oracle sees as 0 -> -12 real semitones.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n, pitch

AEO = "aeolian"

T0, T1 = 544.0, 864.0
CODA = 832.0                       # 4/4 coda begins
BAR = m.FOOTSTEPS_BEATS            # 3.5 beats per 7/8 bar (3+2+2)
N_BARS = int((CODA - T0) / BAR)    # 82 full 7/8 bars in [544, 832)

# Layered entries — the anxiety assembles voice by voice.
E_DRUMS = T0 + 1 * BAR             # 547.5  drums join
E_CHUG = T0 + 2 * BAR              # 551.0  palm-mute chug
E_ARP = 576.0                      # ice sequencer + the solo + strings
E_LEAD = 576.0
E_STR = 576.0
E_CHOIR = 704.0                    # the hum made anxious

# The breakdown: for ~32 beats the low-end drive (bass) and the cold arp fall
# away and the kit thins to a heartbeat, leaving the string tension-pad and
# the portamento lead exposed — then the full texture (and the choir at 704)
# SLAMS back in.  Turns the flat 2.5-min crescendo into a terraced build.
BREAK_LO, BREAK_HI = 672.0, 704.0

# Solo geography (ch12).
DIVE = 768.0                       # whammy dive -12 over 2 beats
SCREAM = 800.0                     # dive -12, rip back to 0
RANGE_RESET = 828.0               # RPN bend range back to 2
PORTA_OFF = 830.0
RECENTER = 831.0

# Degree-1 anchors per channel.
BASS_E = n("E2")                   # 40
RHY_E = n("E2")                    # 40
ARP_E = n("E4")                    # 64
STR_E = n("E3")                    # 52
LEAD_E = n("E4")                   # 64
CHOIR_E = n("E3")                  # 52 (low "mm" stabs)
CODA_CHOIR_E = n("E4")             # 64 (the coda hum, sings clearly)
CODA_ORGAN_E = n("E3")             # 52

# The ice arp: COLD_CELL squeezed from a 2-bar / 16-quaver figure to two
# 7-quaver 7/8 bars (drop two quavers).  Ladder indices per 7/8 bar; the
# harmony alternates i (Em) and VI (C) exactly as material.COLD_CHORDS.
ARP_PATTERN = (0, 2, 3, 4, 3, 2, 3)     # 7 quaver slots, grouped 3+2+2
ARP_ACCENT_SLOTS = {0, 3, 5}            # the 3+2+2 group starts


def _bars():
    """Yield (i, bar_start_beat) for every 7/8 bar in [544, 832)."""
    for i in range(N_BARS):
        yield i, T0 + BAR * i


# ---------------------------------------------------------------------------
# Controllers — the distance arc lands the whole movement one step closer.
# ---------------------------------------------------------------------------
def _controllers(sc):
    for ch in (cd.CH_BASS, cd.CH_RHYTHM, cd.CH_ARP, cd.CH_DRUMS,
               cd.CH_STRINGS, cd.CH_LEAD, cd.CH_CHOIR1, cd.CH_ORGAN):
        sc.cc(ch, 91, 55, T0)


# ---------------------------------------------------------------------------
# ch3 bass — the FOOTSTEPS cell, relentless, vel 70 -> 90
# ---------------------------------------------------------------------------
def _bass(sc):
    for i, b in _bars():
        if BREAK_LO <= b < BREAK_HI:          # breakdown: the bass drops out
            continue
        grow = i / (N_BARS - 1)
        vbase = int(lerp(70, 90, grow))
        for idx, (deg, s, dur) in enumerate(m.FOOTSTEPS):
            accent = 7 if idx in m.FOOTSTEPS_ACCENTS else -2
            sc.note(cd.CH_BASS, pitch(BASS_E, AEO, deg), b + s, dur * 0.9,
                    vbase + accent, jt=3, jv=3)
        # every other bar, thud the low octave on the very first step
        if i % 2 == 0:
            sc.note(cd.CH_BASS, pitch(BASS_E, AEO, 1) - 12, b, 0.45,
                    vbase + 4, jt=3, jv=3)
    # the final footstep across the seam so the floor does not drop out
    # before the coda organ enters at 832.
    sc.note(cd.CH_BASS, pitch(BASS_E, AEO, 1), 831.0, 1.6, 90, jt=2, jv=2)


# ---------------------------------------------------------------------------
# ch10 palm-mute chug — power-fifth stabs on the 3+2+2 group starts
# ---------------------------------------------------------------------------
def _rhythm(sc):
    starts = (0.0, 1.5, 2.5)                 # the group downbeats
    for i, b in _bars():
        if b < E_CHUG or BREAK_LO <= b < BREAK_HI:  # chug drops in the breakdown
            continue
        grow = (i - 2) / (N_BARS - 3)
        vbase = int(lerp(72, 90, grow))
        for j, s in enumerate(starts):
            acc = 6 if j == 0 else (2 if j == 2 else -3)
            for p, dv in ((pitch(RHY_E, AEO, 1), 0), (pitch(RHY_E, AEO, 5), -4)):
                sc.note(cd.CH_RHYTHM, p, b + s, 0.32, vbase + acc + dv,
                        jt=2, jv=3)


# ---------------------------------------------------------------------------
# ch9 kit — kick on group starts, snare on group 2, hats on every quaver
# ---------------------------------------------------------------------------
def _drums(sc):
    for i, b in _bars():
        if b < E_DRUMS:
            continue
        if BREAK_LO <= b < BREAK_HI:          # breakdown: a soft heartbeat only
            sc.hit(36, b + 0.0, 54, jt=2)
            continue
        grow = (i - 1) / (N_BARS - 2)
        kv = int(lerp(84, 102, grow))
        sv = int(lerp(82, 100, grow))
        # kick on the outer group starts (3+..+2), a soft kick under the snare
        sc.hit(36, b + 0.0, kv)
        sc.hit(36, b + 2.5, kv - 6)
        sc.hit(36, b + 1.5, kv - 20)         # group-2 start: body under snare
        sc.hit(38, b + 1.5, sv)              # the backbeat snare (group 2)
        # hats on all seven quavers, the offbeats a touch brighter
        for q in range(7):
            t = b + 0.5 * q
            drum = 46 if q in (1, 4, 6) else 42     # open on some offbeats
            hv = int(lerp(44, 54, grow)) + (4 if drum == 46 else 0)
            sc.hit(drum, t, hv, jt=2, jv=3)
        if i % 8 == 7:                       # a snare flam fill into the phrase
            sc.hit(38, b + 3.0, sv - 6)
            sc.hit(40, b + 3.25, sv - 2)
    # crashes mark the layer entries and the 16-bar solo phrase starts;
    # pushed a hair BEFORE the downbeat so their broadband transient does
    # not sum onto the max-polyphony instant (keeps the peak off the ceiling
    # and the click scan clean).
    for cb in (E_ARP, 640.0, 704.0, 768.0, 800.0):
        sc.hit(49, cb - 0.05, 90, jt=1, jv=3)


# ---------------------------------------------------------------------------
# ch2 ice arp — the Visitors sequencer, compressed and COLDER (CC71 high)
# ---------------------------------------------------------------------------
def _arp(sc):
    arp_bar = 0
    for i, b in _bars():
        if b < E_ARP or BREAK_LO <= b < BREAK_HI:   # arp drops in the breakdown
            continue
        grow = (b - E_ARP) / (CODA - E_ARP)
        vbase = int(lerp(56, 70, grow))
        root = m.COLD_CHORDS[arp_bar % 2]    # i (Em) / VI (C)
        for slot, ix in enumerate(ARP_PATTERN):
            deg = root + m.COLD_LADDER[ix]
            acc = 6 if slot in ARP_ACCENT_SLOTS else -2
            sc.note(cd.CH_ARP, pitch(ARP_E, AEO, deg), b + slot * 0.5, 0.46,
                    vbase + acc, jt=2, jv=3)
        arp_bar += 1
    # CC71 resonance HIGH (80-100) — narrow, glassy, cold.
    en.cc_curve(sc, cd.CH_ARP, 71,
                [(E_ARP, 82), (660.0, 99), (740.0, 86), (RANGE_RESET, 94)],
                step=8.0)
    # CC74 cutoff sweeps: a triangle per 8 bars (28 beats).
    s = E_ARP
    while s < CODA - 1e-9:
        hi = min(CODA, s + 14.0)
        en.cc_curve(sc, cd.CH_ARP, 74,
                    [(s, 48), (hi, 96), (min(CODA, s + 28.0), 48)], step=2.0)
        s += 28.0


# ---------------------------------------------------------------------------
# ch5 strings — tension pad, the aeolian b6 <-> 5 neighbour oscillation
# ---------------------------------------------------------------------------
def _strings(sc):
    """Two-bar cycles: a held Em open fifth with an upper voice that leans
    from the flat sixth (deg 6 = C) onto the fifth (deg 5 = B) and back —
    the paranoid semitone rock of aeolian b6-5."""
    cycle = 0
    i = int(round((E_STR - T0) / BAR))            # first bar at/after 576
    while T0 + BAR * i < CODA:
        b = T0 + BAR * i
        span = min(2 * BAR, CODA - b)             # 7-beat two-bar pad
        grow = (b - E_STR) / (CODA - E_STR)
        v = int(lerp(52, 68, grow))
        # sustained open fifth (root + 5th), the bed
        sc.note(cd.CH_STRINGS, pitch(STR_E, AEO, 1), b, span, v, jt=3, jv=3)
        sc.note(cd.CH_STRINGS, pitch(STR_E, AEO, 5), b, span, v - 4, jt=3, jv=3)
        # upper neighbour: b6 on bar 1, resolve to 5 on bar 2 (the oscillation)
        top6 = pitch(STR_E, AEO, 6) + 12          # C5, the flat sixth
        top5 = pitch(STR_E, AEO, 5) + 12          # B4, the fifth
        d1 = min(BAR, CODA - b)
        sc.note(cd.CH_STRINGS, top6, b, d1, v - 2, jt=3, jv=3)
        if b + BAR < CODA:
            sc.note(cd.CH_STRINGS, top5, b + BAR, min(BAR, CODA - b - BAR),
                    v - 2, jt=3, jv=3)
        cycle += 1
        i += 2
    # a slow swell that tightens toward the scream, then eases off
    en.expr_curve(sc, cd.CH_STRINGS,
                  [(E_STR, 60), (SCREAM, 92), (RANGE_RESET, 74)], step=4.0)


# ---------------------------------------------------------------------------
# ch12 — THE portamento synth solo (bend range 12, glide, dives, the scream)
# ---------------------------------------------------------------------------
# Phrases as (degree, start_in_phrase, dur).  The portamento pedal does the
# gliding between notes; the writing states the theme skeleton, building.
LEAD_PH1 = [               # 576-632: long, floating theme tones
    (1, 0, 3), (2, 3, 1.5), (3, 4.5, 1.5), (5, 6, 4),
    (4, 10, 2), (3, 12, 2), (2, 14, 3.5), (1, 17.5, 4.5),
    (3, 22, 3), (5, 25, 3), (7, 28, 5), (6, 33, 2),
    (5, 35, 3), (4, 38, 2), (2, 40, 4), (1, 44, 6),
    (5, 50, 3), (4, 53, 3),
]
LEAD_PH2 = [               # 640-698: the theme in motion, gliding
    (1, 0, 2), (2, 2, 1), (3, 3, 1), (5, 4, 2), (4, 6, 1), (3, 7, 1),
    (2, 8, 2), (3, 10, 1), (4, 11, 1), (5, 12, 2), (7, 14, 2), (8, 16, 2),
    (7, 18, 1), (6, 19, 1), (5, 20, 2), (4, 22, 1), (3, 23, 1), (2, 24, 3),
    (1, 27, 3), (5, 30, 2), (6, 32, 1), (7, 33, 1), (8, 34, 4),
    (5, 38, 2), (4, 40, 2), (3, 42, 2), (2, 44, 2), (1, 46, 4),
    (3, 50, 2), (5, 52, 2), (4, 54, 2), (3, 56, 2),
]
LEAD_PH3 = [               # 704-736: shorter, higher, tightening
    (1, 0, 1), (3, 1, 1), (5, 2, 1), (7, 3, 1), (8, 4, 2), (7, 6, 1), (5, 7, 1),
    (4, 8, 1), (5, 9, 1), (7, 10, 1), (8, 11, 1), (9, 12, 2), (8, 14, 1),
    (7, 15, 1), (5, 16, 2), (7, 18, 2), (8, 20, 2), (10, 22, 2), (8, 24, 2),
    (7, 26, 1), (5, 27, 1), (4, 28, 2), (3, 30, 1), (2, 31, 1),
]


def _lead(sc):
    ch = cd.CH_LEAD
    # Open the glide and widen the bend range for the whammy work.
    en.bend_range(sc, ch, 12, E_LEAD)
    en.portamento_on(sc, ch, E_LEAD, time_cc=70)
    sc.cc(ch, 11, 88, E_LEAD)               # violining body
    # Phrase 1 — floating.
    en.line(sc, ch, E_LEAD, LEAD_E, AEO, LEAD_PH1, 78, vel_end=86,
            gate=1.0, jt=3)
    # Phrase 2 — the theme starts to walk.
    en.line(sc, ch, 640.0, LEAD_E, AEO, LEAD_PH2, 84, vel_end=90,
            gate=0.98, jt=3)
    # Phrase 3 — tightening, then a machine-gun burst into the dive.
    en.line(sc, ch, 704.0, LEAD_E, AEO, LEAD_PH3, 88, vel_end=94,
            gate=0.96, jt=3)
    en.run(sc, ch, 742.0, LEAD_E, AEO,
           [1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 6, 7, 8, 9, 10], 0.25, 88, 96,
           legato=True)
    en.line(sc, ch, 748.0, LEAD_E, AEO,
            [(8, 0, 2), (7, 2, 1), (5, 3, 1), (7, 4, 2), (8, 6, 2),
             (10, 8, 4), (9, 12, 2), (8, 14, 4)], 92, vel_end=96, gate=0.98)

    # --- the whammy dive: hold E5, dive a full octave down and recover ----
    p_dive = pitch(LEAD_E, AEO, 8)          # E5
    sc.note(ch, p_dive, DIVE, 4.0, 96, jt=0)
    en.bend_ramp(sc, ch, DIVE, DIVE + 2.0, 0.0, -2.0, steps=16)   # -> -12
    en.bend_ramp(sc, ch, DIVE + 2.0, DIVE + 3.6, -2.0, 0.0, steps=14)  # back
    sc.bend(ch, DIVE + 3.7, 0.0)

    # climb back up, wilder, toward the scream
    en.line(sc, ch, 772.0, LEAD_E, AEO,
            [(5, 0, 1), (7, 1, 1), (8, 2, 2), (10, 4, 2), (8, 6, 2),
             (7, 8, 1), (8, 9, 1), (10, 10, 2)], 92, vel_end=98, gate=0.97)
    en.run(sc, ch, 784.0, LEAD_E, AEO,
           [3, 4, 5, 6, 7, 8, 9, 10, 9, 8, 10, 11, 12, 11, 10, 12], 0.25,
           92, 100, legato=True)
    en.line(sc, ch, 790.0, LEAD_E, AEO,
            [(8, 0, 2), (10, 2, 2), (12, 4, 3), (10, 7, 1), (8, 8, 4)],
            96, vel_end=100, gate=0.98)

    # --- THE scream: hold G5, dive -12 and rip straight back to 0 ---------
    p_scream = pitch(LEAD_E, AEO, 10)       # G5
    sc.note(ch, p_scream, SCREAM, 5.0, 102, jt=0)
    en.bend_ramp(sc, ch, SCREAM, SCREAM + 0.7, 0.0, -2.0, steps=8)     # dive
    en.bend_ramp(sc, ch, SCREAM + 0.8, SCREAM + 1.5, -2.0, 0.0, steps=8)  # rip
    sc.bend(ch, SCREAM + 1.6, 0.0)

    # wind down: descend and resolve, dying into the footsteps
    en.line(sc, ch, 806.0, LEAD_E, AEO,
            [(8, 0, 2), (7, 2, 2), (5, 4, 3), (4, 7, 1), (3, 8, 3),
             (2, 11, 2), (1, 13, 5)], 92, vel_end=80, gate=0.98)
    en.line(sc, ch, 826.0, LEAD_E, AEO, [(1, 0, 4)], 74, gate=1.0, jt=1)

    # close the solo controllers cleanly before the coda seam.
    en.bend_range(sc, ch, 2, RANGE_RESET)   # RPN range back to +/-2
    en.portamento_off(sc, ch, PORTA_OFF)    # CC65 off by 832
    sc.bend(ch, RECENTER, 0.0)              # recentred by 832 (oracle)


# ---------------------------------------------------------------------------
# ch6 choir — fragmented "mm" stabs on the group starts, aftertouch spikes
# ---------------------------------------------------------------------------
def _choir(sc):
    en.vowel(sc, cd.CH_CHOIR1, 0, E_CHOIR)      # mm — the anxious hum
    starts = (0.0, 1.5, 2.5)
    for i, b in _bars():
        if b < E_CHOIR:
            continue
        grow = (b - E_CHOIR) / (CODA - E_CHOIR)
        v = int(lerp(62, 78, grow))
        # a low Em triad stab, voiced root/5th/3rd across the three groups
        for j, (s, deg) in enumerate(zip(starts, (1, 5, 3))):
            acc = 4 if j == 0 else -2
            sc.note(cd.CH_CHOIR1, pitch(CHOIR_E, AEO, deg), b + s, 0.4,
                    v + acc, jt=2, jv=3)
            # a short pressure spike inside each stab (the anxiety)
            en.at_curve(sc, cd.CH_CHOIR1,
                        [(b + s, 8), (b + s + 0.18, v + 12), (b + s + 0.4, 0)],
                        step=0.12)


# ---------------------------------------------------------------------------
# 832 coda (4/4) — organ swell + choir hum, ending ON DEGREE 2, unresolved
# ---------------------------------------------------------------------------
def _coda(sc):
    # ch4 organ: a low Em open-fifth swell, rising then dying to nothing.
    for p, dv in ((pitch(CODA_ORGAN_E, AEO, 1), 0),
                  (pitch(CODA_ORGAN_E, AEO, 5), -3),
                  (pitch(CODA_ORGAN_E, AEO, 1) + 12, -6)):
        sc.note(cd.CH_ORGAN, p, CODA, 25.0, 64 + dv, jt=3, jv=2)
    en.expr_curve(sc, cd.CH_ORGAN,
                  [(CODA, 8), (844.0, 88), (852.0, 66), (859.0, 0)], step=2.0)

    # ch6 choir I: hum the theme's first phrase and land on degree 2.
    en.vowel(sc, cd.CH_CHOIR1, 0, CODA)         # mm
    phrase = m.THEME[:7]                        # bars 1-2, arriving on deg 2
    en.line(sc, cd.CH_CHOIR1, CODA, CODA_CHOIR_E, AEO, phrase, 60,
            vel_end=54, gate=1.0, jt=2)
    # hold the degree-2 (F#4) — the half cadence — and let it die away.
    hold_start = CODA + 8.0
    sc.note(cd.CH_CHOIR1, pitch(CODA_CHOIR_E, AEO, 2), hold_start, 15.0, 56,
            jt=2, jv=2)
    en.at_curve(sc, cd.CH_CHOIR1,
                [(hold_start, 6), (hold_start + 6, 66),
                 (hold_start + 12, 30), (hold_start + 16, 0)], step=0.5)


def build(sc) -> None:
    _controllers(sc)
    _bass(sc)
    _rhythm(sc)
    _drums(sc)
    _arp(sc)
    _strings(sc)
    _lead(sc)
    _choir(sc)
    _coda(sc)
