"""movements/t06_the_flood.py — track 6 of *The Causeway* (Act Two opens).

THE FLOOD.  The morning after the dawn crossing: they walk back as the tide
chases them across the sand — jaunty McCartney domestic pop (the *Another Day*
gait: bouncing piano, acoustic guitar, light kit) breaking into a stacked
*Super Trouper* chorus of layered synth hooks.  G major with an E-minor lean,
4/4, about 112.  The act inhales at the top (a pan flute alone), and from here
the two shore voices — apart for four winters — sound TOGETHER for the first
easy time, both in G.  Movements: I. Dry Shod (the gait; the flood bell HOOK6
on vibraphone, which also taps FLOOD; the first easy overlap; THE REACH left
hanging), II. Water at the Heels (an authored accelerando 112->132 and a
rising CC74 brightness as the chorus stacks — protagonist bass, doubled thumb,
Super Trouper hooks), III. The Last Stones (the sprint, a pan-flute echo of
HOOK6's head over the run), IV. Landed (the half-tempo reprise, one forward
FUSION in G, a IV-I plagal final, six tolls).

Act Two law is inverted from Act One: distance 0 (both themes in G), overlap
REQUIRED, the leading-tone ban lifted, the plagal signature spent.  The road
home (the fusion retrograde) reaches exactly three notes here and stops short.
All recurring data is single-sourced from material.py.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 6
TITLE = "The Flood"
FILE = "06 - The Flood.mid"
SEED = 202607186
COMMENT = (
    "The Flood - Act Two opens.  The morning after the dawn crossing: they "
    "walk back as the tide chases them, jaunty McCartney domestic pop (the "
    "Another Day gait) breaking into a stacked Super Trouper chorus.  The act "
    "inhales at the top - a pan flute alone taps the flood bell's head - then "
    "the two shore themes, apart for four winters, overlap for the first easy "
    "time, both in G.  The flood bell (HOOK6, D-B-B-B) tolls on vibraphone, "
    "which also taps FLOOD in Morse; the road home is reached three notes deep "
    "and left hanging.  Water at the Heels drives an accelerando 112 to 132 "
    "under a rising filter brightness as the chorus stacks; the Last Stones "
    "sprint under a pan-flute echo; and Landed brings the half-tempo reprise, "
    "a forward fusion in G, a plagal final and six tolls.")

# ---------------------------------------------------------------------------
# Channels.  The re-opened strait: island-pole voices (pan flute, choir, the
# Super Trouper synth, the flood-bell vibraphone) sit left at 56; mainland-pole
# voices (acoustic guitar, Rhodes) sit right at 72; the neutral spine (gait
# piano, bass, the doubled-thumb piano, Morse, kit, bells, pad) holds 64.
# ---------------------------------------------------------------------------

CH_PIANO, CH_GUITAR, CH_BASS, CH_THUMB = 0, 1, 2, 3
CH_VIBES, CH_MORSE, CH_PANFLUTE, CH_CHOIR = 4, 5, 6, 7
CH_SYNTH, CH_DRUMS, CH_EP, CH_BELLS, CH_PAD = 8, 9, 10, 11, 12

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (56, 72)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 7, 7

# --- the movement grid (contiguous; last t1 = END) ---
HERALD_T0, HERALD_T1 = 0.0, 8.0            # the pan flute alone, at the top
I_END = 168.0
II_T0 = 168.0
II_END = 336.0
III_END = 448.0
END = 584.0

# --- the authored accelerando (movement II's swell; the tide owns it) ---
ACCEL_T0, ACCEL_T1 = 168.0, 328.0          # end inside II so its last event pins
ACCEL_BPM0, ACCEL_BPM1 = 112.0, 132.0

# --- the rising filter arc (the water as brightness) across movement II ---
CC74_T0, CC74_T1 = 168.0, 332.0
CC74_LO, CC74_HI = 28, 116

# --- pinned geometry the oracles re-derive against material.py ---
GAIT_T0 = 8.0                              # the gait begins after the inhale
OVERLAP_T0 = 88.0                          # island + mainland, both G, 8 beats
ISLAND_BASE = en.n("G3")                   # 55 - island deg1 = G (tonic pc 7)
MAINLAND_BASE = en.n("G3")                 # 55 - mainland deg1 = G (tonic pc 7)
REACH_T0 = 120.0                           # the road home, 3 notes, left hanging
REACH_BASE = en.n("G4")                    # 67 - the retrograde's held tonic G
FUSION_T0 = 516.0                          # the one forward fusion (in IV)
FUSION_BASE = en.n("G4")                   # 67 - fusion deg1 = G (tonic pc 7)

CHORUS_SPANS = [(216.0, 312.0), (472.0, 544.0)]   # the stack, then the reprise

# the flood bell / herald / echo pitches (the D-B-B-B shape)
HERALD_PITCH = en.n("D4")                  # 62 - the inhale, low and warm
BELL_PITCH = en.n("D5")                    # 74 - the flood bell, bright
ECHO_PITCH = en.n("D5")                    # 74 - the pan-flute echo over the run
SYNTH_HOOK_PITCH = en.n("D5")              # 74 - the Super Trouper top hook

MORSE_T0 = 24.0
MORSE_PITCH = en.n("D5")                    # 74 - the vibraphone's fixed tap
FINAL_DOWNBEAT = 556.0                      # the plagal landing (bass C -> G)
TOLL_T0 = 560.0
TOLL_PITCH = en.n("G3")                     # 55 - pc 7 = the shared tonic G


def _accel(t0: float, t1: float, bpm0: float, bpm1: float,
           step: float = 8.0) -> list[tuple[float, float]]:
    """A monotonically rising tempo ramp - the authored accelerando that is
    movement II's swell (the tide-breath owns I, III and IV instead)."""
    out = []
    b = t0
    while b <= t1 + 1e-9:
        out.append((b, round(en.lerp(bpm0, bpm1, (b - t0) / (t1 - t0)), 2)))
        b += step
    return out


# --- the tide-breath tempo map: I, III, IV breathe; II accelerates ---
TEMPO_MAP = (
    material.tide_breath(112.0, 0.0, I_END, period=32.0, depth=4.0)
    + _accel(ACCEL_T0, ACCEL_T1, ACCEL_BPM0, ACCEL_BPM1)
    + material.tide_breath(132.0, II_END, III_END, period=32.0, depth=4.0)
    + material.tide_breath(92.0, III_END, END, period=32.0, depth=5.0))

# the kit: brush (40) for the domestic gait and the landed reprise, the full
# sampled kit (0) for the stacked chorus and the sprint.
KIT_BRUSH, KIT_FULL = 40, 0
KIT_CHANGES = [(CH_DRUMS, 0.0, KIT_BRUSH),
               (CH_DRUMS, II_T0, KIT_FULL),
               (CH_DRUMS, III_END, KIT_BRUSH)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Dry Shod", 0.0, I_END),
               ("II. Water at the Heels", I_END, II_END),
               ("III. The Last Stones", II_END, III_END),
               ("IV. Landed", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 1, 0)],                  # G major: one sharp, major
    channels=[(CH_PIANO, "gait piano", 0, 94, 64, 34),
              (CH_GUITAR, "acoustic guitar", 25, 88, MAIN_PAN, 40),
              (CH_BASS, "protagonist bass", 33, 100, 64, 26),
              (CH_THUMB, "partner piano", 0, 84, 64, 34),
              (CH_VIBES, "vibraphone", 11, 88, ISL_PAN, 52),
              (CH_MORSE, "morse vibraphone", 11, 78, 64, 40),
              (CH_PANFLUTE, "pan flute", 75, 86, ISL_PAN, 54),
              (CH_CHOIR, "choir", 52, 82, ISL_PAN, 58),
              (CH_SYNTH, "super trouper synth", 81, 84, ISL_PAN, 44),
              (CH_DRUMS, "kit", 0, 94, 64, 28),
              (CH_EP, "rhodes", 4, 84, MAIN_PAN, 42),
              (CH_BELLS, "tubular bells", 14, 90, 64, 50),
              (CH_PAD, "warm pad", 89, 74, 64, 46)],
    program_changes=KIT_CHANGES,
    extra_markers=[(HERALD_T0, "the act inhales"), (GAIT_T0, "the gait"),
                   (OVERLAP_T0, "the first easy overlap"),
                   (CHORUS_SPANS[0][0], "the stacked chorus"),
                   (II_END, "the sprint"), (III_END, "landed"),
                   (TOLL_T0, "the tolls")],
)

PROGRAM_WHITELIST = {0, 4, 11, 14, 25, 33, 52, 75, 81, 89}
CENTERED_CHANNELS = {CH_PIANO, CH_BASS, CH_THUMB, CH_MORSE, CH_DRUMS,
                     CH_BELLS, CH_PAD}
NOTE_RANGES = {
    CH_PIANO: (36, 84), CH_GUITAR: (48, 84), CH_BASS: (28, 55),
    CH_THUMB: (38, 66), CH_VIBES: (72, 84), CH_MORSE: (74, 74),
    CH_PANFLUTE: (60, 84), CH_CHOIR: (48, 81), CH_SYNTH: (48, 86),
    CH_EP: (48, 76), CH_BELLS: (53, 57), CH_PAD: (36, 72),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # no pitch bends on this track
DURATION_WINDOW = (300.0, 326.0)            # ~5:13 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES sec.3 pattern; beat-based, tick where noted)
# ---------------------------------------------------------------------------

_PPQ = en.PPQ
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))


def _note_ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = d[0] & 0xF0
        if s == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                out.append((q.pop(0) / _PPQ, tick / _PPQ, d[1]))
    return sorted(out)


def _cc_lane(sc, ch, num):
    return sorted((t / _PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _onsets_in(sc, ch, lo, hi):
    return [(b, p, v) for b, p, v in _note_ons(sc, ch) if lo - 1e-6 <= b < hi]


def _movement_events(lo, hi):
    """The tempo events whose beat falls inside [lo, hi)."""
    return [(b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6]


def _pitch_at(sc, ch, beat):
    """The pitch(es) of the note(s) sounding on `ch` at `beat` (onset-inclusive)."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on - 1e-6 <= beat < off - 1e-6]


def _in_chorus(beat):
    return any(lo <= beat < hi for lo, hi in CHORUS_SPANS)


# Harmony - the addictive G major I-V-vi-IV loop (G - D - Em - C), one chord
# per bar; the pump, guitar, pad, choir and bass all read the same cycle.
# (bass_root, [pad voicing, mid register], [chorus choir/EP voicing])
CHORD_CYCLE = [
    (en.n("G2"), [en.n("G3"), en.n("B3"), en.n("D4")],
                 [en.n("G3"), en.n("B3"), en.n("D4"), en.n("G4")]),   # G   (I)
    (en.n("D2"), [en.n("F#3"), en.n("A3"), en.n("D4")],
                 [en.n("F#3"), en.n("A3"), en.n("D4"), en.n("F#4")]),  # D   (V)
    (en.n("E2"), [en.n("G3"), en.n("B3"), en.n("E4")],
                 [en.n("E3"), en.n("G3"), en.n("B3"), en.n("E4")]),   # Em  (vi)
    (en.n("C2"), [en.n("G3"), en.n("C4"), en.n("E4")],
                 [en.n("C3"), en.n("E3"), en.n("G3"), en.n("C4")]),   # C   (IV)
]

# the gait's right-hand chord (bright close voicing) per cycle step
RH_CHORD = [
    [en.n("B3"), en.n("D4"), en.n("G4")],    # G
    [en.n("A3"), en.n("D4"), en.n("F#4")],   # D
    [en.n("B3"), en.n("E4"), en.n("G4")],    # Em
    [en.n("C4"), en.n("E4"), en.n("G4")],    # C
]

# the protagonist bass roams G major / E aeolian, E1..E3 (span 24 semitones).
BASS_SCALE = [en.n(x) for x in
              ("E1", "F#1", "G1", "A1", "B1", "C2", "D2", "E2", "F#2",
               "G2", "A2", "B2", "C3", "D3", "E3")]

BASS_HOOK_ROOT = en.n("G2")                  # 43 - HOOK6 in the bass: G-E-E-E


def _chord_idx(beat):
    """Which cycle step a bar belongs to; aligned so beat 8 (the gait's
    downbeat) begins on G."""
    return (int(beat // 4) + 2) % 4


# Emitters.  Oracle-pinned lanes (themes, HOOK6, the reach, the fusion, Morse,
# tolls, the herald, the doubled thumb, the cadence) are jt=0 so every
# statement is findable; the gait's texture lanes take a light jitter.

def _pad_bed(sc, t0, t1):
    """The warm pad sustains the chord cycle, one chord per bar, contiguous so
    the track never goes silent under the gait (jt=0 - it sits on the seams)."""
    bar = t0
    while bar < t1 - 1e-6:
        _root, voicing, _chorus = CHORD_CYCLE[_chord_idx(bar)]
        dur = min(4.0, t1 - bar)
        for p in voicing:
            sc.note(CH_PAD, p, bar, dur, 42, jt=0, jv=2)
        bar += 4.0


def _pump(sc, t0, t1, vel_lo, vel_hi):
    """The Another Day gait: the piano's left hand pumps octave roots in
    quavers (accents on 1 and the and-of-2), its right hand answers with
    bright off-beat chord stabs.  A sustain pedal per bar blurs it warm."""
    bar = t0
    while bar < t1 - 1e-6:
        idx = _chord_idx(bar)
        root, _voicing, _chorus = CHORD_CYCLE[idx]
        for q in range(8):
            b = bar + q * 0.5
            if b >= t1 - 1e-6:
                break
            accent = 12 if q == 0 else (8 if q == 3 else 0)   # 1 and and-of-2
            v = vel_lo + accent
            sc.note(CH_PIANO, root, b, 0.46, v, jt=0, jv=3)
            sc.note(CH_PIANO, root + 12, b, 0.46, v - 6, jt=0, jv=3)
        for st in (1.5, 2.5, 3.5):                            # off-beat stabs
            for p in RH_CHORD[idx]:
                sc.note(CH_PIANO, p, bar + st, 0.4, vel_hi - 8, jt=2, jv=4)
        en.sustain(sc, CH_PIANO, bar, bar + 3.92)
        bar += 4.0


def _guitar_gait(sc, t0, t1, vel):
    """The acoustic guitar: a boom-chick strum - a bass note on 1 and 3, a
    bright chord chop on the off-beats (the domestic-pop shuffle)."""
    bar = t0
    while bar < t1 - 1e-6:
        idx = _chord_idx(bar)
        root, _voicing, chorus = CHORD_CYCLE[idx]
        chord = [p for p in chorus if p >= en.n("D3")]
        for beat in (0.0, 2.0):
            jt = 0 if bar + beat <= t0 + 0.1 else 3     # keep the herald alone
            sc.note(CH_GUITAR, root + 12, bar + beat, 0.45, vel, jt=jt, jv=4)
        for beat in (1.0, 1.5, 3.0, 3.5):
            for k, p in enumerate(chord):
                sc.note(CH_GUITAR, p, bar + beat + k * 0.02, 0.3,
                        vel - 10 - k * 2, jt=3, jv=4)
        bar += 4.0


def _kit(sc, t0, t1, drive):
    """A light kit that firms up with `drive` (0..1): kick on 1 (and a funk
    push when driven), a backbeat on 2 and 4, quaver hats thickening to
    sixteenths in the sprint."""
    bar = t0
    while bar < t1 - 1e-6:
        kv = int(70 + 34 * drive)
        sc.hit(36, bar, kv, jt=0)
        if drive > 0.4:
            sc.hit(36, bar + 1.5, kv - 14, jt=0)              # the funk push
        sc.hit(38, bar + 1.0, int(64 + 26 * drive), jt=0)     # backbeat 2
        sc.hit(38, bar + 3.0, int(68 + 26 * drive), jt=0)     # backbeat 4
        sixteenths = drive > 0.6
        steps = 16 if sixteenths else 8
        for q in range(steps):
            b = bar + q * (0.25 if sixteenths else 0.5)
            if b >= t1 - 1e-6:
                break
            drum = 46 if (q % (steps // 4) == 0 and q) else 42
            v = int(34 + 16 * drive + (8 if drum == 46 else 0))
            sc.hit(drum, b, v, jt=0 if b <= t0 + 0.1 else 3)  # herald stays alone
        bar += 4.0


def _choir_bed(sc, t0, t1, vpts, vowel_pts, cc11):
    """The choir sings the chord cycle as sustained pads under a rising vowel
    (kept under the cap) - the ABBA-ice half of the stack.  `vpts`/`vowel_pts`
    are (beat, value) breakpoints for CC11 and CC70."""
    bar = t0
    while bar < t1 - 1e-6:
        _root, _voicing, chorus = CHORD_CYCLE[_chord_idx(bar)]
        dur = min(4.0, t1 - bar)
        for p in chorus[:3]:
            sc.note(CH_CHOIR, p, bar, dur * 0.99, 46, jt=0, jv=2)
        bar += 4.0
    en.expr_curve(sc, CH_CHOIR, vpts, step=4.0)
    en.vowel_curve(sc, CH_CHOIR, vowel_pts, step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, cc11, step=8.0)


def _herald(sc):
    """The act inhales: HOOK6's head (semitone deltas 0, +9, +9 - the flood
    bell) on the pan flute, alone, over a strictly-rising CC11 swell, two bars
    at the very top of the track.  Notes 2 and 3 share a pitch, laid contiguous
    so no same-pitch overlap survives."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]     # [0, 9, 9]
    starts = [HERALD_T0, HERALD_T0 + 2.0, HERALD_T0 + 4.0]
    durs = [2.0, 2.0, 4.0]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, HERALD_PITCH + s, st, du, 60, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 14), (HERALD_T1, 108)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 30)],
                step=0.5)


def _morse(sc):
    """The vibraphone taps FLOOD in standard Morse (MORSE_PROGRAMS[6] = 11),
    on its own lane so the flood-bell statements stay findable."""
    material.play_morse(sc, CH_MORSE, MORSE_T0, NUMBER, MORSE_PITCH)


def _bell(sc, times, vel=84):
    """The flood bell: HOOK6 (D-B-B-B, fusion[0:4]) on the vibraphone.  The
    channel is clean while each 3-beat statement sounds so the searcher finds
    every one."""
    for t in times:
        material.play_hook(sc, CH_VIBES, t, BELL_PITCH, NUMBER,
                           vel=vel, gate=0.9)


def _reach(sc):
    """THE REACH: the road home's first three notes (the fusion retrograde's
    held tonic G, then the climb to degree 3) on the synth, left hanging - and
    NO further (RETRO_REACH[6] = 3)."""
    material.play_fusion(sc, CH_SYNTH, REACH_T0, REACH_BASE,
                         retro=True, count=material.RETRO_REACH[NUMBER],
                         vel=78, gate=1.0)


def _theme_overlap(sc):
    """The first easy overlap: the island incantation (synth, left) and the
    mainland tune (Rhodes, right) sound together, both implying G, downbeat-
    consonant across the eight bars.  Both are monophonic while they state."""
    material.play_island(sc, CH_SYNTH, OVERLAP_T0, ISLAND_BASE,
                         vel=76, vel_end=70)
    en.expr_curve(sc, CH_SYNTH, [(OVERLAP_T0, 40), (OVERLAP_T0 + 4, 84),
                                 (OVERLAP_T0 + 8, 44)], step=0.5)
    material.play_mainland(sc, CH_EP, OVERLAP_T0, MAINLAND_BASE,
                           vel=78, vel_end=70)
    en.expr_curve(sc, CH_EP, [(OVERLAP_T0, 40), (OVERLAP_T0 + 4, 82),
                              (OVERLAP_T0 + 8, 44)], step=0.5)


def _sprint_echo(sc, times):
    """A pan-flute ECHO of HOOK6's head rides OVER the sprint (its own head-cell
    rhythm - onsets 0, 1, 1.5 - so the searcher finds it as the head, NOT as
    the herald whose spacing differs).  It is an echo, not a herald: the run
    roars underneath it."""
    head = material.HOOKS[NUMBER][:3]
    for t in times:
        for on, du, s in head:
            sc.note(CH_PANFLUTE, ECHO_PITCH + s, t + on, du * 0.9, 70,
                    jt=0, jv=2)


def _synth_hooks(sc, times):
    """The Super Trouper top: HOOK6 layered high on the synth through the
    chorus - monophonic while stating."""
    for t in times:
        material.play_hook(sc, CH_SYNTH, t, SYNTH_HOOK_PITCH, NUMBER,
                           vel=82, gate=0.9)


def _ep_comp(sc, t0, t1, vel):
    """The Rhodes comps the chord cycle through the chorus - warm off-beat
    stabs (never a theme statement, so the overlap's mainland reading stays the
    only one)."""
    bar = t0
    while bar < t1 - 1e-6:
        _root, _voicing, chorus = CHORD_CYCLE[_chord_idx(bar)]
        chord = chorus[1:]
        for st in (0.5, 2.0, 3.0):
            for k, p in enumerate(chord):
                sc.note(CH_EP, p, bar + st + k * 0.01, 0.7, vel - k * 3,
                        jt=2, jv=3)
        bar += 4.0


_BASS_PERIOD = 28                              # notes per full down-up sweep


def _bass_walk(sc, t0, t1, dur, vel, seed, phase=0):
    """Walk the protagonist bass through BASS_SCALE as a stepwise triangle
    sweep - up and down the whole low register - so the line is entirely
    stepwise yet spans the full E1..E3 range the McCartney bass needs.  `seed`
    offsets the sweep so successive segments start in different places."""
    beat = t0
    i = seed + phase
    half = _BASS_PERIOD // 2                    # 14 -> indices 0..14 (E1..E3)
    while beat < t1 - 1e-6:
        tri = i % _BASS_PERIOD
        pos = tri if tri <= half else _BASS_PERIOD - tri
        accent = 6 if (beat % 4.0) < 1e-6 else 0
        sc.note(CH_BASS, BASS_SCALE[pos], beat, dur * 0.9, vel + accent,
                jt=0, jv=0)
        beat += dur
        i += 1
    return i


def _bass_hook(sc, t0, vel=88):
    """HOOK6 in the bass (G-E-E-E) - the protagonist singing the flood bell at
    a chorus head; returns the end beat."""
    return material.play_hook(sc, CH_BASS, t0, BASS_HOOK_ROOT, NUMBER,
                              vel=vel, gate=0.9)


def _double_thumb(sc, lo, hi):
    """Inside a chorus, shadow every bass note-on at the octave on the partner
    piano - the doubled thumb that makes the stack feel huge."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if lo <= beat < hi:
            sc.note(CH_THUMB, pitch + 12, beat, 0.4, 72, jt=0, jv=2)


def _fusion(sc):
    """The one forward FUSION statement, in G - the shared language spoken
    plainly now that the voices are one.  Monophonic on the synth."""
    material.play_fusion(sc, CH_SYNTH, FUSION_T0, FUSION_BASE,
                         vel=84, vel_end=76, gate=0.95)
    en.expr_curve(sc, CH_SYNTH, [(FUSION_T0, 44), (FUSION_T0 + 4, 92),
                                 (FUSION_T0 + 8, 40)], step=0.5)


def _plagal_cadence(sc):
    """The IV-I plagal final: the bass approaches on C (the IV of G) and lands
    the tonic G on the downbeat - the Act Two signature, spent once."""
    sc.note(CH_BASS, en.n("C2"), 548.0, 3.4, 78, jt=0, jv=0)
    sc.note(CH_BASS, en.n("C2"), 552.0, 3.4, 80, jt=0, jv=0)   # the IV, last prior
    sc.note(CH_BASS, en.n("G2"), FINAL_DOWNBEAT, 4.0, 90, jt=0, jv=0)  # lands G


def _final_chord(sc):
    """Landed and laughing: the pad and choir hold the plagal C -> G under the
    cadence, ringing up to the first toll (nothing new sounds after it)."""
    for p in (en.n("G3"), en.n("C4"), en.n("E4")):            # C (the IV)
        sc.note(CH_PAD, p, 544.0, 12.0, 44, jt=0, jv=2)
    for p in (en.n("G3"), en.n("B3"), en.n("D4")):            # G (the I)
        sc.note(CH_PAD, p, FINAL_DOWNBEAT, 4.0, 46, jt=0, jv=2)
    for p in (en.n("G3"), en.n("B3"), en.n("D4")):            # the choir lands G
        sc.note(CH_CHOIR, p, 552.0, 8.0, 48, jt=0, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(544.0, 60), (552.0, 82), (559.0, 74)],
                   step=1.0)
    en.expr_curve(sc, CH_CHOIR, [(544.0, 50), (552.0, 78), (559.0, 60)],
                  step=1.0)


def _tolls(sc):
    """The bell buoy: exactly six tolls on the G, the final note-ons of the
    track (each rings 3.5 beats over a 2.5-beat spacing, so the peal is
    unbroken); nothing else sounds after the first strike."""
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, vel=82, dur=3.5)


# I. Dry Shod [0, 168) — the inhale, the gait, the first easy overlap, the reach
def _b_dry_shod(sc):
    _herald(sc)
    _pad_bed(sc, GAIT_T0, I_END)
    _pump(sc, GAIT_T0, I_END, 58, 76)
    _guitar_gait(sc, GAIT_T0, I_END, 62)
    _kit(sc, GAIT_T0, I_END, 0.2)
    _choir_bed(sc, GAIT_T0, I_END,
               [(GAIT_T0, 38), (80.0, 54), (I_END - 4, 40)],
               [(GAIT_T0, 8), (80.0, 32), (I_END - 4, 38)],
               [(GAIT_T0, 0), (I_END - 4, 20)])
    _morse(sc)
    _bell(sc, [40.0, 72.0, 136.0])
    _bass_walk(sc, GAIT_T0, I_END, 1.0, 62, 7)
    _theme_overlap(sc)
    _reach(sc)


# II. Water at the Heels [168, 336) — the accelerando, the brightness, the stack
def _b_water_at_heels(sc):
    _pad_bed(sc, II_T0, II_END)
    en.cc_curve(sc, CH_PAD, 74, [(CC74_T0, CC74_LO), (CC74_T1, CC74_HI)],
                step=4.0)                              # the water as brightness
    _pump(sc, II_T0, II_END, 64, 84)
    _guitar_gait(sc, II_T0, II_END, 68)
    _kit(sc, II_T0, II_END, 0.6)
    _choir_bed(sc, II_T0, II_END,
               [(II_T0, 44), (260.0, 74), (II_END - 4, 54)],
               [(II_T0, 40), (264.0, 85), (II_END - 4, 70)],
               [(II_T0, 10), (II_END - 4, 34)])
    _bass_walk(sc, II_T0, 216.0, 1.0, 68, 7)
    _bass_hook(sc, 216.0)                              # the protagonist sings HOOK6
    _bass_walk(sc, 219.0, 280.0, 1.0, 72, 9)
    _bass_hook(sc, 280.0)
    _bass_walk(sc, 283.0, II_END, 1.0, 70, 9)
    _double_thumb(sc, *CHORUS_SPANS[0])
    _synth_hooks(sc, [216.0, 248.0, 280.0])
    _ep_comp(sc, 216.0, 312.0, 66)
    _bell(sc, [232.0, 296.0])


# III. The Last Stones [336, 448) — the sprint; the echo rides over the run
def _b_last_stones(sc):
    _pad_bed(sc, II_END, III_END)
    _pump(sc, II_END, III_END, 66, 88)
    _guitar_gait(sc, II_END, III_END, 72)
    _kit(sc, II_END, III_END, 0.85)
    _choir_bed(sc, II_END, III_END,
               [(II_END, 50), (400.0, 74), (III_END - 4, 50)],
               [(II_END, 50), (400.0, 78), (III_END - 4, 60)],
               [(II_END, 10), (III_END - 4, 30)])
    _bass_walk(sc, II_END, III_END, 0.5, 74, 7)
    _bell(sc, [368.0, 408.0])
    _sprint_echo(sc, [356.0, 396.0])


# IV. Landed [448, 584) — the half-tempo reprise, the fusion, the plagal, tolls
def _b_landed(sc):
    _pad_bed(sc, III_END, 544.0)
    _pump(sc, III_END, 544.0, 54, 72)
    _guitar_gait(sc, III_END, 544.0, 58)
    _kit(sc, III_END, 544.0, 0.3)
    _choir_bed(sc, III_END, 544.0,
               [(III_END, 44), (500.0, 70), (540.0, 46)],
               [(III_END, 40), (500.0, 80), (540.0, 64)],
               [(III_END, 6), (540.0, 24)])
    _bass_walk(sc, III_END, 472.0, 1.0, 60, 7)
    _bass_hook(sc, 472.0)                              # the reprise sings HOOK6
    _bass_walk(sc, 475.0, 504.0, 1.0, 64, 9)
    _bass_hook(sc, 504.0)
    _bass_walk(sc, 507.0, 540.0, 1.0, 64, 9)
    _double_thumb(sc, *CHORUS_SPANS[1])
    _synth_hooks(sc, [472.0, 504.0])
    _ep_comp(sc, 472.0, 540.0, 62)
    _bell(sc, [488.0])
    _fusion(sc)
    _plagal_cadence(sc)
    _final_chord(sc)
    _tolls(sc)


BUILDERS = [_b_dry_shod, _b_water_at_heels, _b_last_stones, _b_landed]


# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """Distance 0: both themes imply G (pc 7), the pair together at last."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 1:
        fails.append(f"{len(isl)} island statements, want 1 (the easy overlap)")
    if len(mnl) != 1:
        fails.append(f"{len(mnl)} mainland statements, want 1 (the easy overlap)")
    for ch, start, _e, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {ISLAND_TONIC_PC} (G)")
    for ch, start, _e, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {MAINLAND_TONIC_PC} (G)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 0:
            fails.append(f"shore distance {dist}, want 0 (Act Two: together in G)")
    return fails


def _o_overlap(sc):
    """The simultaneity law, inverted: >= 1 island+mainland overlap,
    downbeat-consonant across it (the ban of tracks 1-4 is dead)."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    pairs = material.overlapping_pairs(isl, mnl)
    if not pairs:
        return ["Act Two requires >= 1 island+mainland overlap; none found"]
    for a, b in pairs:
        ach, a0, a1, _ap = a
        bch, b0, b1, _bp = b
        lo, hi = max(a0, b0), min(a1, b1)
        db = math.ceil(lo / 4.0 - 1e-9) * 4.0
        checked = 0
        while db < hi - 1e-9:
            ip = _pitch_at(sc, ach, db)
            mp = _pitch_at(sc, bch, db)
            if ip and mp:
                checked += 1
                if all((p - q) % 12 not in _CONSONANT
                       for p in ip for q in mp):
                    fails.append(f"overlap downbeat {db:.1f}: island {ip} vs "
                                 f"mainland {mp} is dissonant")
            db += 4.0
        if checked == 0:
            fails.append(f"overlap [{lo:.1f},{hi:.1f}] shares no downbeat to test")
    return fails


def _o_fusion(sc):
    """The shared language: >= 1 forward FUSION statement, tonic G (pc 7)."""
    fails = []
    fus = material.theme_statements(sc, "fusion")
    if len(fus) < 1:
        fails.append("no forward FUSION statement (Act Two requires >= 1)")
    for ch, start, _e, first in fus:
        if first % 12 != MAINLAND_TONIC_PC:
            fails.append(f"fusion at {start:.1f} implies pc {first % 12}, "
                         f"want {MAINLAND_TONIC_PC} (G)")
    return fails


def _o_hook_density(sc):
    """The flood-bell earworm: HOOK6 stated >= 6 times UNNESTED (fusion
    statements auto-register it, so those nested hits do not count)."""
    hits = material.hook_statements_unnested(sc, NUMBER)
    if len(hits) < 6:
        return [f"HOOK6 (unnested) found {len(hits)} times, want >= 6"]
    return []


def _o_protagonist_bass(sc):
    """The McCartney bass sings: stepwise-dominant, wide-ranging, stating HOOK6
    in the bass inside the choruses."""
    fails = []
    ons = _note_ons(sc, CH_BASS)
    pitches = [p for _b, p, _v in ons]
    if len(pitches) < 2:
        return ["protagonist bass is silent"]
    steps = sum(1 for a, b in zip(pitches, pitches[1:]) if 1 <= abs(b - a) <= 2)
    ratio = steps / (len(pitches) - 1)
    if ratio < 0.50:
        fails.append(f"bass stepwise ratio {ratio:.2f} < 0.50")
    span = max(pitches) - min(pitches)
    if span < 19:
        fails.append(f"bass range {span} semitones < 19")
    bass_hooks = material.find_statements(material.note_ons(sc, CH_BASS),
                                          material.HOOKS[NUMBER])
    in_chorus = [h for h in bass_hooks if _in_chorus(h[0])]
    if len(in_chorus) < 2:
        fails.append(f"HOOK6 in the bass inside choruses {len(in_chorus)}, "
                     f"want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The stack thickens: every chorus bass note-on shadowed at the octave on
    the partner piano (coverage >= 0.80), and not outside (< 0.30)."""
    fails = []
    thumb = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_THUMB)]

    def shadowed(bt, bp):
        return any(pp == bp + 12 and abs(pt - bt) <= 10 for pt, pp in thumb)

    inside, outside = [], []
    for b, p, _v in _note_ons(sc, CH_BASS):
        (inside if _in_chorus(b) else outside).append((_tick(b), p))
    cov_in = (sum(1 for bt, bp in inside if shadowed(bt, bp)) / len(inside)
              if inside else 0.0)
    cov_out = (sum(1 for bt, bp in outside if shadowed(bt, bp)) / len(outside)
               if outside else 0.0)
    if cov_in < 0.80:
        fails.append(f"doubled-thumb coverage {cov_in:.2f} inside choruses < 0.80")
    if cov_out >= 0.30:
        fails.append(f"bass doubled {cov_out:.2f} OUTSIDE choruses >= 0.30")
    return fails


def _o_herald(sc):
    """The act inhales: >= 2 bars at the top where only the pan flute sounds,
    playing HOOK6's head over a strictly-rising CC11 swell."""
    fails = []
    for ch in sorted(sc.events):
        if ch == CH_PANFLUTE:
            continue
        if _onsets_in(sc, ch, HERALD_T0, HERALD_T1):
            fails.append(f"ch{ch} sounds inside the herald window "
                         f"[{HERALD_T0:.0f},{HERALD_T1:.0f}) - only the pan flute may")
            break
    pf = _onsets_in(sc, CH_PANFLUTE, HERALD_T0, HERALD_T1)
    want = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]
    if len(pf) != 3:
        fails.append(f"herald has {len(pf)} pan-flute notes, want 3 (the flood "
                     f"bell's head)")
    else:
        deltas = [pf[k][1] - pf[0][1] for k in range(3)]
        if deltas != want:
            fails.append(f"herald pitch deltas {deltas}, want {want}")
    cc11 = [v for b, v in _cc_lane(sc, CH_PANFLUTE, 11)
            if HERALD_T0 - 1e-6 <= b <= HERALD_T1 + 1e-6]
    if len(cc11) < 4 or any(cc11[i] >= cc11[i + 1]
                            for i in range(len(cc11) - 1)):
        fails.append("herald CC11 swell is not strictly rising")
    if HERALD_T1 - HERALD_T0 < 8.0:
        fails.append(f"herald window {HERALD_T1 - HERALD_T0} beats < 2 bars")
    return fails


def _o_reach(sc):
    """The road home assembles exactly three notes and stops: the pinned REACH
    prefix registers, and NO longer prefix and no full retrograde exist."""
    fails = []
    target = material.RETRO_REACH[NUMBER]                # 3
    cell = material.retro_prefix_cell(target)
    hits = sum(len(material.find_statements(material.note_ons(sc, ch), cell))
               for ch in sc.events)
    if hits < 1:
        fails.append(f"the {target}-note road home (REACH) is not stated")
    for c in range(target + 1, len(material.FUSION_RETRO) + 1):
        longer = material.retro_prefix_cell(c)
        n = sum(len(material.find_statements(material.note_ons(sc, ch), longer))
                for ch in sc.events)
        if n:
            fails.append(f"a length-{c} retro prefix registered {n}x - the "
                         f"road home must stop at {target}")
    if material.theme_statements(sc, "fusion_retro"):
        fails.append("the full retrograde must not sound before T10")
    return fails


def _o_withheld(sc):
    """The withheld payoffs: island_major and fusion_retro are banned on 6-9."""
    fails = []
    if material.theme_statements(sc, "island_major"):
        fails.append("island_major is banned before T10")
    if material.theme_statements(sc, "fusion_retro"):
        fails.append("fusion_retro (the full road home) is banned before T10")
    return fails


def _o_morse(sc):
    """The tide-word FLOOD, tapped on vibraphone (MORSE_PROGRAMS[6] = 11), in
    standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 11:
        fails.append("morse timbre for T6 must be vibraphone (program 11)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_MORSE)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} (FLOOD)")
        return fails
    for k, ((on, off, p), (won, wdu)) in enumerate(zip(taps, pairs)):
        if p != MORSE_PITCH:
            fails.append(f"morse tap {k} pitch {p}, want {MORSE_PITCH}")
            break
        if abs(on - (MORSE_T0 + won)) > 1e-6:
            fails.append(f"morse tap {k} onset {on:.3f}, want {MORSE_T0 + won:.3f}")
            break
        if abs((off - on) - wdu * 0.9) > 0.02:
            fails.append(f"morse tap {k} dur {off - on:.3f}, want {wdu * 0.9:.3f}")
            break
    return fails


def _o_vowel_cap(sc):
    """Summer opens the mouth, but not all the way: choir CC70 never exceeds 90."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_accelerando(sc):
    """The tide catches up: movement II's tempo rises monotonically 112 -> 132
    (the authored accelerando owns II in place of the tide-breath)."""
    seq = [bpm for _b, bpm in _movement_events(II_T0, II_END)]
    fails = []
    if len(seq) < 8:
        fails.append(f"accelerando has {len(seq)} tempo events, want >= 8")
        return fails
    if any(seq[i] > seq[i + 1] + 1e-9 for i in range(len(seq) - 1)):
        fails.append("accelerando is not monotonically rising")
    if abs(seq[0] - ACCEL_BPM0) > 1.0:
        fails.append(f"accelerando starts at {seq[0]}, want ~{ACCEL_BPM0:.0f}")
    if abs(seq[-1] - ACCEL_BPM1) > 1.0:
        fails.append(f"accelerando ends at {seq[-1]}, want ~{ACCEL_BPM1:.0f}")
    if seq[-1] - seq[0] < 15.0:
        fails.append(f"accelerando span {seq[-1] - seq[0]:.1f} bpm, want >= 15")
    return fails


def _o_cc74_arc(sc):
    """The water as brightness: a rising CC74 filter arc across movement II,
    from dark to bright, non-decreasing (oracle-pinned endpoints)."""
    lane = [(b, v) for b, v in _cc_lane(sc, CH_PAD, 74)
            if II_T0 - 1e-6 <= b <= II_END + 1e-6]
    fails = []
    if len(lane) < 8:
        fails.append(f"CC74 brightness arc has {len(lane)} events, want a sweep")
        return fails
    vals = [v for _b, v in lane]
    if vals[0] > CC74_LO + 8:
        fails.append(f"CC74 arc starts at {vals[0]}, want <= {CC74_LO + 8} (dark first)")
    if vals[-1] < CC74_HI - 8:
        fails.append(f"CC74 arc ends at {vals[-1]}, want >= {CC74_HI - 8} (brightness rises)")
    if any(vals[i] > vals[i + 1] + 1 for i in range(len(vals) - 1)):
        fails.append("CC74 brightness arc is not non-decreasing")
    return fails


def _o_tide_breath(sc):
    """The water is in the tempo everywhere but the accelerando: movements I,
    III and IV each swell (>= 2 troughs); II accelerates instead."""
    fails = []
    for name, t0, t1 in [("I. Dry Shod", 0.0, I_END),
                         ("III. The Last Stones", II_END, III_END),
                         ("IV. Landed", III_END, END)]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2")
    return fails


def _o_plagal_final(sc):
    """The Act Two plagal signature: the bass approaches on C (the IV of G) and
    lands the tonic G on the final downbeat."""
    return [f"plagal final: {m}" for m in material.plagal_final_failures(
        sc, CH_BASS, FINAL_DOWNBEAT, MAINLAND_TONIC_PC, window=8.0)]


def _o_shore_pans(sc):
    """The re-opened strait: island voices left (56), mainland voices right (72)."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_VIBES, CH_PANFLUTE, CH_CHOIR, CH_SYNTH}
    mainland = {CH_GUITAR, CH_EP}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{{ISL_PAN}}}")
    for ch in sorted(mainland):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {MAIN_PAN}:
            fails.append(f"mainland ch{ch} pans {sorted(pans)}, want {{{MAIN_PAN}}}")
    return fails


def _o_sprint_echo(sc):
    """A pan-flute echo of HOOK6's head rides OVER the sprint - it is an echo,
    not a herald: it does not sound alone."""
    fails = []
    head = material.HOOKS[NUMBER][:3]
    hits = [h for h in material.find_statements(
        material.note_ons(sc, CH_PANFLUTE), head)
        if II_END <= h[0] < III_END]
    if len(hits) < 1:
        return ["no pan-flute echo of HOOK6's head over the sprint"]
    t = hits[0][0]
    others = [ch for ch in sc.events
              if ch != CH_PANFLUTE and _onsets_in(sc, ch, t, t + 3.0)]
    if not others:
        fails.append(f"the sprint echo at {t:.1f} sounds alone - it must ride "
                     f"over the run")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls six times on the G, the final note-ons of the track;
    nothing else sounds after the first strike."""
    fails = []
    bells = _note_ons(sc, CH_BELLS)
    if len(bells) != material.TOLLS[NUMBER]:
        fails.append(f"{len(bells)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p, _v in bells:
        if p % 12 != MAINLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want {MAINLAND_TONIC_PC} (G)")
            break
    all_ons = sorted((b, ch) for ch in sc.events
                     for b, _p, _v in _note_ons(sc, ch))
    if bells:
        toll_on = bells[0][0]
        after = [(b, ch) for b, ch in all_ons
                 if b > toll_on + 1e-6 and ch != CH_BELLS]
        if after:
            fails.append(f"{len(after)} note-on(s) after toll 1 (e.g. ch"
                         f"{after[0][1]} at {after[0][0]:.1f})")
        if all_ons and all_ons[-1][1] != CH_BELLS:
            fails.append("the final note-on is not a toll")
    return fails


def oracles(sc, info, spans):
    return [
        ("convergence", _o_convergence(sc)),
        ("overlap", _o_overlap(sc)),
        ("fusion", _o_fusion(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("protagonist_bass", _o_protagonist_bass(sc)),
        ("doubled_thumb", _o_doubled_thumb(sc)),
        ("breath_herald", _o_herald(sc)),
        ("the_reach", _o_reach(sc)),
        ("withheld_payoffs", _o_withheld(sc)),
        ("morse_flood", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("accelerando", _o_accelerando(sc)),
        ("cc74_brightness", _o_cc74_arc(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("plagal_final", _o_plagal_final(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("sprint_echo", _o_sprint_echo(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The tide catches up (II brighter/louder than I), the sprint peaks (III), and
# the landing settles a touch below the sprint.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    dry = _rms_db(40.0, 80.0)           # movement I, the dry-shod gait
    heels = _rms_db(240.0, 300.0)       # movement II, the stacked chorus
    sprint = _rms_db(360.0, 440.0)      # movement III, the sprint
    landed = _rms_db(480.0, 536.0)      # movement IV, the reprise

    # 1. The tide catches up: the stacked chorus is not quieter than the dry
    #    gait it grew from (the accelerando + brightness should build).
    fails = []
    if heels - dry < -1.5:
        fails.append(f"the chorus {heels:.1f} dB is quieter than the gait "
                     f"{dry:.1f} dB (the flood should build)")
    checks.append(("audio_flood_builds", fails))

    # 2. The sprint is the track's peak: not below the chorus.
    fails = []
    if sprint - heels < -1.0:
        fails.append(f"the sprint {sprint:.1f} dB sits below the chorus "
                     f"{heels:.1f} dB (the last stones should be the peak)")
    checks.append(("audio_sprint_peaks", fails))

    # 3. Landed settles a touch below the sprint peak (soaked and laughing, not
    #    louder than the run).
    fails = []
    if sprint - landed < -1.5:
        fails.append(f"the landing {landed:.1f} dB is louder than the sprint "
                     f"{sprint:.1f} dB (the reprise should ease off)")
    checks.append(("audio_landed_eases", fails))
    return checks




