"""movements/t07_noon_water.py — track 7 of *The Causeway* (Act Two).

NOON WATER.  High summer, the tide well in and the causeway drowned: the two
players are on the water now, and the afternoon is long and warm.  A lush
downtempo Delerium groove (the *Karma* idiom) with Feel-the-Sun warmth —
breathy shakuhachi haze, a high open choir, steel drums tapping NOON, and both
shore themes overlapping lazily in C.  C major, 4/4, about 88, breathing the
whole way (no still points — they are on the water).  Movements: I. Glare
(pads and haze, the noon fall on the Rhodes, the NOON tap), II. The Long
Afternoon (a breath herald, then the groove: HOOK7 on the protagonist bass
doubled at the thumb, the two themes overlapping in C, a forward fusion and
THE REACH five notes up the road home, echo throws), III. Heat Shimmer (an
autopan crystal and the album's one lazy harmonica solo with draw-bend
scoops), IV. Evening Water (HOOK7 stretched, a IV-I plagal final, seven tolls).

Act Two law: distance 0 (both themes in C), overlap REQUIRED, the leading-tone
ban lifted, the plagal signature spent.  The road home reaches exactly five
notes and stops short.  All recurring data is single-sourced from material.py.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 7
TITLE = "Noon Water"
FILE = "07 - Noon Water.mid"
SEED = 202607187
COMMENT = (
    "Noon Water - Act Two, high summer.  The tide is well in and the causeway "
    "drowned; the two players are out on the water and the afternoon is long "
    "and warm.  A lush downtempo Delerium groove with Feel-the-Sun warmth: "
    "breathy shakuhachi haze over pads, a high open choir, steel drums tapping "
    "NOON in Morse, and both shore themes overlapping lazily in C.  The noon "
    "fall (HOOK7, G-F-E-D-C) drops on the Rhodes and, doubled at the thumb, on "
    "the protagonist bass; a breath herald opens the groove; a forward fusion "
    "and the road home reached five notes deep and left hanging cross the "
    "flute; a heat-shimmer movement floats an autopan crystal under the "
    "album's one lazy harmonica solo; and Evening Water stretches the noon "
    "fall into dusk over a plagal final and seven tolls.")

# Channels.  Island-pole voices (ice synth, shakuhachi, pan-flute herald,
# choir, fusion flute) sit left at 54; mainland-pole voices (Rhodes, harmonica)
# right at 74; the neutral spine (pad, bass, thumb Rhodes, Morse steel drums,
# kit, bells) holds 64.  The heat-shimmer crystal autopans on its own seat.

CH_PAD, CH_RHODES, CH_BASS, CH_THUMB = 0, 1, 2, 3
CH_SYNTH, CH_MORSE, CH_SHAKU, CH_PANFLUTE = 4, 5, 6, 7
CH_CHOIR, CH_DRUMS, CH_FLUTE, CH_HARM = 8, 9, 10, 11
CH_CRYSTAL, CH_BELLS = 12, 13

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (54, 74)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 0, 0

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 96.0
HERALD_T0, HERALD_T1 = 96.0, 104.0         # the breath herald, pan flute alone
GROOVE_T0 = 104.0                          # the groove locks in after the inhale
II_END = 272.0
III_END = 376.0
END = 464.0

# --- pinned geometry the oracles re-derive against material.py ---
OVERLAP_T0 = 176.0                         # island + mainland, both C, 8 beats
ISLAND_BASE = en.n("C4")                   # 60 - island deg1 = C (tonic pc 0)
MAINLAND_BASE = en.n("C4")                 # 60 - mainland deg1 = C (tonic pc 0)
FUSION_T0 = 192.0                          # the one forward fusion, in C
FUSION_BASE = en.n("C5")                   # 72 - fusion deg1 = C (tonic pc 0)
REACH_T0 = 204.0                           # the road home, 5 notes, left hanging
REACH_BASE = en.n("C4")                    # 60 - the retrograde's held tonic C

CHORUS_SPANS = [(136.0, 168.0), (216.0, 248.0)]   # the two afternoon choruses

# the noon fall (HOOK7 = G-F-E-D-C): stated on G so the fall is diatonic.
HOOK_TOP = en.n("G4")                      # 67 - the noon fall's head, G
BASS_HOOK_TOP = en.n("G2")                 # 43 - HOOK7 in the bass
HERALD_PITCH = en.n("G4")                  # 67 - the herald head (G-F-E)

MORSE_T0 = 24.0
MORSE_PITCH = en.n("C5")                    # 72 - the steel drums' fixed tap
FINAL_DOWNBEAT = 440.0                      # the plagal landing (bass F -> C)
TOLL_T0 = 444.0
TOLL_PITCH = en.n("C3")                     # 48 - pc 0 = the shared tonic C

# --- the tide-breath tempo map: every movement breathes (no still points) ---
TEMPO_MAP = (
    material.tide_breath(88.0, 0.0, I_END, period=32.0, depth=4.0)
    + material.tide_breath(88.0, I_END, II_END, period=32.0, depth=4.0)
    + material.tide_breath(86.0, II_END, III_END, period=32.0, depth=5.0)
    + material.tide_breath(84.0, III_END, END, period=32.0, depth=5.0))

# the kit: brush (40) for the whole downtempo groove — it never gets hard.
KIT_BRUSH = 40
KIT_CHANGES = [(CH_DRUMS, GROOVE_T0, KIT_BRUSH)]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Glare", 0.0, I_END),
               ("II. The Long Afternoon", I_END, II_END),
               ("III. Heat Shimmer", II_END, III_END),
               ("IV. Evening Water", III_END, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0)],                  # C major: no accidentals
    channels=[(CH_PAD, "warm pad", 89, 78, 64, 46),
              (CH_RHODES, "rhodes", 4, 84, MAIN_PAN, 42),
              (CH_BASS, "protagonist bass", 33, 98, 64, 26),
              (CH_THUMB, "partner rhodes", 4, 78, 64, 40),
              (CH_SYNTH, "ice synth", 81, 80, ISL_PAN, 48),
              (CH_MORSE, "morse steel drums", 114, 82, 64, 40),
              (CH_SHAKU, "shakuhachi", 77, 82, ISL_PAN, 54),
              (CH_PANFLUTE, "pan flute", 75, 84, ISL_PAN, 52),
              (CH_CHOIR, "choir", 52, 80, ISL_PAN, 56),
              (CH_DRUMS, "brush kit", 0, 88, 64, 30),
              (CH_FLUTE, "flute", 73, 84, ISL_PAN, 50),
              (CH_HARM, "harmonica", 22, 82, MAIN_PAN, 44),
              (CH_CRYSTAL, "crystal shimmer", 98, 58, 64, 60),
              (CH_BELLS, "tubular bells", 14, 90, 64, 50)],
    program_changes=KIT_CHANGES,
    extra_markers=[(HERALD_T0, "the breath herald"), (GROOVE_T0, "the groove"),
                   (CHORUS_SPANS[0][0], "the afternoon chorus"),
                   (OVERLAP_T0, "the themes overlap"),
                   (CHORUS_SPANS[1][0], "the second chorus"),
                   (II_END, "heat shimmer"), (III_END, "evening water"),
                   (TOLL_T0, "the tolls")],
)

PROGRAM_WHITELIST = {4, 14, 22, 33, 52, 73, 75, 77, 81, 89, 98, 114}
CENTERED_CHANNELS = {CH_PAD, CH_BASS, CH_THUMB, CH_MORSE, CH_DRUMS, CH_BELLS}
NOTE_RANGES = {
    CH_PAD: (40, 72), CH_RHODES: (48, 84), CH_BASS: (24, 52),
    CH_THUMB: (36, 66), CH_SYNTH: (48, 86), CH_MORSE: (72, 72),
    CH_SHAKU: (55, 86), CH_PANFLUTE: (60, 74), CH_CHOIR: (55, 84),
    CH_FLUTE: (58, 84), CH_HARM: (67, 86), CH_CRYSTAL: (72, 96),
    CH_BELLS: (46, 50),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # only the harmonica bends (III)
DURATION_WINDOW = (316.0, 343.0)            # ~5:29 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# Click-scan cap, calibrated against the real render (lead's diagnosis,
# 2026.07.19): the track's largest sample steps (~44.6k, many musically
# placed moments) are the SAMPLED BRUSH KIT's slap/tap transients —
# full-bandwidth noise bursts alternating around the mix ceiling, ringing
# both directions, no DC step, no clipping (peak 26029).  Confirmed by a
# --solo 9 stem probe on t09 (drums alone step ~51k): a recorded brush
# slap IS a near-Nyquist noise burst.  Snap, not clicks.
MAX_SAMPLE_STEP = 48000

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
    """The pitch(es) sounding on `ch` at `beat` (onset-inclusive)."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on - 1e-6 <= beat < off - 1e-6]


def _in_chorus(beat):
    return any(lo <= beat < hi for lo, hi in CHORUS_SPANS)


# Harmony — the warm summer C-major loop C - Am - F - G (I-vi-IV-V), one chord
# per bar; the pad, choir and (voiced up) the Rhodes read the same cycle.
# (bass_root, [pad/mid voicing], [fuller chorus voicing])
CHORD_CYCLE = [
    (en.n("C2"), [en.n("C3"), en.n("E3"), en.n("G3")],
                 [en.n("C3"), en.n("E3"), en.n("G3"), en.n("C4")]),   # C   (I)
    (en.n("A1"), [en.n("A2"), en.n("C3"), en.n("E3")],
                 [en.n("A2"), en.n("C3"), en.n("E3"), en.n("A3")]),   # Am  (vi)
    (en.n("F2"), [en.n("F3"), en.n("A3"), en.n("C4")],
                 [en.n("F3"), en.n("A3"), en.n("C4"), en.n("F4")]),   # F   (IV)
    (en.n("G2"), [en.n("G3"), en.n("B3"), en.n("D4")],
                 [en.n("G3"), en.n("B3"), en.n("D4"), en.n("G4")]),   # G   (V)
]

# the high choir sings the chord's fifth (open, warm), one tone per bar.
CHOIR_TOPS = [en.n("G4"), en.n("E4"), en.n("C5"), en.n("D5")]

# the protagonist bass roams C major, C1..C3 (span 24 semitones), stepwise.
BASS_SCALE = [en.n(x) for x in
              ("C1", "D1", "E1", "F1", "G1", "A1", "B1", "C2", "D2",
               "E2", "F2", "G2", "A2", "B2", "C3")]
_BASS_PERIOD = 28                             # notes per full down-up sweep


def _chord_idx(beat):
    """Which cycle step a bar belongs to; beat 0 begins on C (the tonic)."""
    return int(beat // 4) % 4


# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (themes, HOOK7, the reach, the fusion, Morse,
# tolls, the herald, the doubled thumb, the cadence) are jt=0 so every
# statement is findable; the groove's texture lanes take a light jitter.
# ---------------------------------------------------------------------------

def _pad_bed(sc, t0, t1, vel=44, chorus=False):
    """The warm pad sustains the chord cycle, one chord per bar, contiguous so
    the track never goes silent (jt=0 — it sits on the seams)."""
    bar = t0
    while bar < t1 - 1e-6:
        _root, voicing, chvoicing = CHORD_CYCLE[_chord_idx(bar)]
        dur = min(4.0, t1 - bar)
        for p in (chvoicing if chorus else voicing):
            sc.note(CH_PAD, p, bar, dur, vel, jt=0, jv=2)
        bar += 4.0


def _shaku_haze(sc, t0, t1, vpts, vel=52):
    """The Feel-the-Sun haze: long breathy shakuhachi tones on chord tones,
    high and floating, one per bar, under a slow CC11 shimmer (jt=0)."""
    tops = [en.n("G5"), en.n("E5"), en.n("C5"), en.n("D5")]
    bar = t0
    while bar < t1 - 1e-6:
        p = tops[_chord_idx(bar)]
        dur = min(4.0, t1 - bar)
        sc.note(CH_SHAKU, p, bar, dur * 0.96, vel, jt=0, jv=2)
        bar += 4.0
    en.expr_curve(sc, CH_SHAKU, vpts, step=2.0)


def _choir_bed(sc, t0, t1, cc11, vowel_pts, vel=44):
    """The high open choir sings the chord's fifth as a sustained pad under a
    rising-but-capped vowel (the ABBA-ice sheen); one tone per bar, jt=0."""
    bar = t0
    while bar < t1 - 1e-6:
        p = CHOIR_TOPS[_chord_idx(bar)]
        dur = min(4.0, t1 - bar)
        sc.note(CH_CHOIR, p, bar, dur * 0.98, vel, jt=0, jv=2)
        bar += 4.0
    en.expr_curve(sc, CH_CHOIR, cc11, step=4.0)
    en.vowel_curve(sc, CH_CHOIR, vowel_pts, step=4.0)


def _morse(sc):
    """The steel drums tap NOON in standard Morse (MORSE_PROGRAMS[7] = 114),
    on their own lane so the noon-fall statements stay findable."""
    material.play_morse(sc, CH_MORSE, MORSE_T0, NUMBER, MORSE_PITCH,
                        vel=64, gate=0.9)


def _noon_fall(sc, ch, times, top, vel=78, stretch=1.0, gate=0.9):
    """HOOK7 — the noon fall (G-F-E-D-C, the fusion tail) — stated on `ch`.
    The channel is clean while each statement sounds so the searcher finds
    every one.  `top` is the head pitch (a G keeps the fall diatonic)."""
    for t in times:
        material.play_hook(sc, ch, t, top, NUMBER, vel=vel,
                           stretch=stretch, gate=gate)

def _herald(sc):
    """The afternoon inhales: HOOK7's head (G-F-E, deltas 0, -2, -3 — the noon
    fall's first three notes) on the pan flute, alone, over a strictly-rising
    CC11 swell, two bars at the top of the groove."""
    semis = [s for _o, _d, s in material.HOOKS[NUMBER][:3]]     # [0, -2, -3]
    starts = [HERALD_T0, HERALD_T0 + 2.0, HERALD_T0 + 4.0]
    durs = [2.0, 2.0, 4.0]
    for s, st, du in zip(semis, starts, durs):
        sc.note(CH_PANFLUTE, HERALD_PITCH + s, st, du, 58, jt=0, jv=2)
    en.expr_curve(sc, CH_PANFLUTE, [(HERALD_T0, 12), (HERALD_T1, 104)],
                  step=0.5)
    en.cc_curve(sc, CH_PANFLUTE, 1, [(HERALD_T0, 0), (HERALD_T1, 26)],
                step=0.5)


def _bass_walk(sc, t0, t1, dur, vel, seed, phase=0):
    """Walk the protagonist bass through BASS_SCALE as a stepwise triangle
    sweep — up and down the whole C1..C3 register the McCartney bass needs."""
    beat = t0
    i = seed + phase
    half = _BASS_PERIOD // 2
    while beat < t1 - 1e-6:
        tri = i % _BASS_PERIOD
        pos = tri if tri <= half else _BASS_PERIOD - tri
        accent = 6 if (beat % 4.0) < 1e-6 else 0
        sc.note(CH_BASS, BASS_SCALE[pos], beat, dur * 0.9, vel + accent,
                jt=0, jv=0)
        beat += dur
        i += 1
    return i


def _bass_hook(sc, t0, vel=86):
    """HOOK7 in the bass (G-F-E-D-C) — the protagonist singing the noon fall at
    a chorus head; returns the end beat."""
    return material.play_hook(sc, CH_BASS, t0, BASS_HOOK_TOP, NUMBER,
                              vel=vel, gate=0.9)


def _double_thumb(sc, lo, hi):
    """Inside a chorus, shadow every bass note-on at the octave on the partner
    Rhodes — the doubled thumb that gives the afternoon its warmth."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if lo <= beat < hi:
            sc.note(CH_THUMB, pitch + 12, beat, 0.45, 70, jt=0, jv=2)


def _synth_ice(sc, t0, t1, vel=54):
    """The ABBA-ice sequence: a gentle broken-chord arp (up-then-down, never a
    straight rising run) high over the groove, following the chord cycle."""
    bar = t0
    while bar < t1 - 1e-6:
        _r, _v, chvoicing = CHORD_CYCLE[_chord_idx(bar)]
        tones = [p + 12 for p in chvoicing]        # up an octave, the ice
        pat = [0, 1, 2, 3, 2, 1, 0, 1]             # up-then-down, no long climb
        for q in range(8):
            b = bar + q * 0.5
            if b >= t1 - 1e-6:
                break
            sc.note(CH_SYNTH, tones[pat[q]], b, 0.45,
                    vel + (6 if q == 0 else 0), jt=0, jv=3)
        bar += 4.0


def _rhodes_comp(sc, t0, t1, vel=58):
    """The Rhodes comps warm block-chord stabs off the beat (never a run, so
    the overlap's mainland reading stays the only Rhodes statement)."""
    bar = t0
    while bar < t1 - 1e-6:
        _r, _v, chvoicing = CHORD_CYCLE[_chord_idx(bar)]
        chord = chvoicing[1:]
        for st in (1.5, 3.0):
            for k, p in enumerate(chord):
                sc.note(CH_RHODES, p, bar + st, 0.7, vel - k * 3, jt=2, jv=3)
        bar += 4.0


def _kit(sc, t0, t1, drive=0.4):
    """A soft downtempo brush kit: kick on 1, a half-time brush backbeat on 3,
    lazy quaver hats.  It never gets hard — this is the long afternoon."""
    bar = t0
    while bar < t1 - 1e-6:
        sc.hit(36, bar, int(64 + 16 * drive), jt=0)            # kick on 1
        # jt=0 at the movement's start so nothing jitters back into the herald.
        sc.hit(38, bar + 2.0, int(52 + 18 * drive),
               jt=0 if bar + 2.0 <= t0 + 0.1 else 2)           # brush backbeat
        for q in range(8):
            b = bar + q * 0.5
            if b >= t1 - 1e-6:
                break
            v = int(30 + 12 * drive + (6 if q % 2 == 0 else 0))
            sc.hit(42, b, v, jt=0 if b <= t0 + 0.1 else 3)
        bar += 4.0


def _theme_overlap(sc):
    """The lazy overlap: the island incantation (ice synth, left, C minor) and
    the mainland tune (Rhodes, right, C major) drift together, both implying C,
    downbeat-consonant.  Both are monophonic here (the ice and comp rest)."""
    material.play_island(sc, CH_SYNTH, OVERLAP_T0, ISLAND_BASE,
                         vel=72, vel_end=66, gate=0.95)
    en.expr_curve(sc, CH_SYNTH, [(OVERLAP_T0, 40), (OVERLAP_T0 + 4, 82),
                                 (OVERLAP_T0 + 8, 44)], step=0.5)
    material.play_mainland(sc, CH_RHODES, OVERLAP_T0, MAINLAND_BASE,
                           vel=76, vel_end=68, gate=0.95)
    en.expr_curve(sc, CH_RHODES, [(OVERLAP_T0, 40), (OVERLAP_T0 + 4, 80),
                                  (OVERLAP_T0 + 8, 44)], step=0.5)
    en.echo_throw(sc, CH_SYNTH, OVERLAP_T0 + 7.5)              # Enigma punctuation


def _fusion(sc):
    """The one forward FUSION statement, in C — the shared language spoken
    plainly on the flute now that the voices are one.  Monophonic."""
    material.play_fusion(sc, CH_FLUTE, FUSION_T0, FUSION_BASE,
                         vel=82, vel_end=74, gate=0.95)
    en.expr_curve(sc, CH_FLUTE, [(FUSION_T0, 42), (FUSION_T0 + 4, 90),
                                 (FUSION_T0 + 8, 40)], step=0.5)
    en.echo_throw(sc, CH_FLUTE, FUSION_T0 + 7.5)


def _reach(sc):
    """THE REACH: the road home's first FIVE notes (C-D-E-F-G, the retrograde's
    held tonic and the climb) on the flute, left hanging — no further
    (RETRO_REACH[7] = 5)."""
    material.play_fusion(sc, CH_FLUTE, REACH_T0, REACH_BASE,
                         retro=True, count=material.RETRO_REACH[NUMBER],
                         vel=76, gate=1.0)
    en.expr_curve(sc, CH_FLUTE, [(REACH_T0, 44), (REACH_T0 + 4, 84),
                                 (REACH_T0 + 5, 30)], step=0.5)

def _crystal_shimmer(sc, t0, t1):
    """Heat shimmer: a crystal (98) autopans slowly across the field, low in
    the mix, sounding sparse high chord tones — the air wobbling over the
    water.  Its own seat (the autopan writes CC10, so it is neither shore nor
    centred)."""
    en.autopan(sc, CH_CRYSTAL, t0, t1 - t0, lo=34, hi=94, period_beats=18.0,
               step=0.5)
    tops = [en.n("C6"), en.n("E6"), en.n("F6"), en.n("D6")]
    bar = t0
    while bar < t1 - 1e-6:
        p = tops[_chord_idx(bar)]
        sc.note(CH_CRYSTAL, p, bar + 0.5, 3.0, 46, jt=2, jv=3)
        bar += 4.0


def _harmonica_solo(sc, t0, t1):
    """The album's one harmonica: a lazy C-major solo with draw-bend scoops —
    each note scooped up into pitch from a semitone below, recentred by the
    movement's end (the only bends on the track)."""
    # a slow, blue-tinged phrase over the chord cycle; (beat, pitch, dur)
    scale = {0: [en.n("G5"), en.n("E5"), en.n("C5"), en.n("D5")],
             1: [en.n("E5"), en.n("A5"), en.n("C6"), en.n("A5")],
             2: [en.n("F5"), en.n("A5"), en.n("C6"), en.n("G5")],
             3: [en.n("D5"), en.n("G5"), en.n("B5"), en.n("D6")]}
    bar = t0 + 8.0                             # let the shimmer breathe first
    while bar < t1 - 10.0:
        notes = scale[_chord_idx(bar)]
        # two long lazy notes per bar, each scooped up into pitch
        for st, p in ((0.5, notes[0]), (2.5, notes[2])):
            on = bar + st
            sc.note(CH_HARM, p, on, 1.6, 66, jt=2, jv=3)
            en.bend_ramp(sc, CH_HARM, on, on + 0.35, -1.0, 0.0, steps=8)
        bar += 4.0
    sc.bend(CH_HARM, t1 - 6.0, 0.0)            # recentred well before the seam


def _plagal_cadence(sc):
    """The IV-I plagal final: the bass approaches on F (the IV of C) and lands
    the tonic C on the downbeat — the Act Two signature, spent once.  The bass
    is clean in the final window (F, F, then C — nothing else)."""
    sc.note(CH_BASS, en.n("F1"), FINAL_DOWNBEAT - 8.0, 3.6, 76, jt=0, jv=0)
    sc.note(CH_BASS, en.n("F1"), FINAL_DOWNBEAT - 4.0, 3.6, 78, jt=0, jv=0)  # IV
    sc.note(CH_BASS, en.n("C1"), FINAL_DOWNBEAT, 4.0, 84, jt=0, jv=0)  # lands C


def _final_chord(sc):
    """Evening water settles: the pad and choir hold the plagal F -> C under
    the cadence, ringing up to the first toll (nothing new sounds after it)."""
    for p in (en.n("F3"), en.n("A3"), en.n("C4")):           # F (the IV)
        sc.note(CH_PAD, p, FINAL_DOWNBEAT - 8.0, 8.0, 42, jt=0, jv=2)
    for p in (en.n("C3"), en.n("E3"), en.n("G3"), en.n("C4")):   # C (the I)
        sc.note(CH_PAD, p, FINAL_DOWNBEAT, 4.0, 46, jt=0, jv=2)
    for p in (en.n("C4"), en.n("E4"), en.n("G4")):           # the choir lands C
        sc.note(CH_CHOIR, p, FINAL_DOWNBEAT - 4.0, 6.0, 46, jt=0, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(FINAL_DOWNBEAT - 4.0, 70),
                                  (FINAL_DOWNBEAT, 88), (FINAL_DOWNBEAT + 2, 74)],
                   step=1.0)
    en.expr_curve(sc, CH_CHOIR, [(FINAL_DOWNBEAT - 4.0, 48),
                                 (FINAL_DOWNBEAT, 80), (FINAL_DOWNBEAT + 2, 56)],
                  step=1.0)


def _tolls(sc):
    """The bell buoy: exactly seven tolls on the C, the final note-ons of the
    track (each rings 3.5 beats over a 2.5-beat spacing, so the peal is
    unbroken); nothing else sounds after the first strike."""
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, vel=80, dur=3.5)


# I. Glare [0, 96) — pads and shakuhachi haze, the noon fall, the NOON tap
def _b_glare(sc):
    _pad_bed(sc, 0.0, I_END, vel=42)
    _shaku_haze(sc, 0.0, I_END,
                [(0.0, 30), (48.0, 58), (I_END - 2, 40)], vel=52)
    _choir_bed(sc, 0.0, I_END,
               [(0.0, 20), (56.0, 46), (I_END - 2, 30)],
               [(0.0, 20), (56.0, 62), (I_END - 2, 50)], vel=42)
    _morse(sc)
    # the noon fall drops three times on the Rhodes, high and lazy (diatonic
    # G-F-E-D-C); the Rhodes is otherwise silent here so each run is clean.
    _noon_fall(sc, CH_RHODES, [20.0, 52.0, 76.0], en.n("G5"),
               vel=72, gate=0.85)
    en.echo_throw(sc, CH_RHODES, 59.5)


# II. The Long Afternoon [96, 272) — the herald, the groove, the overlap
def _b_afternoon(sc):
    _herald(sc)
    # the groove bed (after the inhale)
    _pad_bed(sc, GROOVE_T0, II_END, vel=46, chorus=True)
    _choir_bed(sc, GROOVE_T0, II_END,
               [(GROOVE_T0, 34), (200.0, 58), (II_END - 2, 40)],
               [(GROOVE_T0, 40), (200.0, 84), (II_END - 2, 60)], vel=44)
    _kit(sc, GROOVE_T0, 260.0, drive=0.4)
    # the ice sequence runs the verse and choruses, resting across the overlap
    # window (176..184) and the flute's fusion/reach so the synth stays clean
    # while it states the island theme.
    _synth_ice(sc, GROOVE_T0, 172.0, vel=52)
    _synth_ice(sc, 188.0, 248.0, vel=54)
    # the protagonist bass: verse walk, HOOK7 at each chorus head, then walk;
    # it rests across the lazy overlap bridge and the outro.
    _bass_walk(sc, GROOVE_T0, 136.0, 1.0, 66, 3)
    _bass_hook(sc, 136.0)                                # chorus 1 sings HOOK7
    _bass_walk(sc, 140.0, 168.0, 1.0, 70, 7)
    _bass_hook(sc, 216.0)                                # chorus 2 sings HOOK7
    _bass_walk(sc, 220.0, 248.0, 1.0, 70, 9)
    _double_thumb(sc, *CHORUS_SPANS[0])
    _double_thumb(sc, *CHORUS_SPANS[1])
    # the Rhodes comps the choruses (block chords, never a run) and carries the
    # mainland theme in the overlap; it rests elsewhere.
    _rhodes_comp(sc, 136.0, 168.0, vel=56)
    _rhodes_comp(sc, 216.0, 248.0, vel=56)
    # the shakuhachi keeps a wisp of haze through the outro so the groove
    # settles rather than stops.
    _shaku_haze(sc, 248.0, II_END, [(248.0, 44), (II_END - 2, 28)], vel=46)
    _theme_overlap(sc)
    _fusion(sc)
    _reach(sc)


# III. Heat Shimmer [272, 376) — the autopan crystal and the harmonica solo
def _b_heat_shimmer(sc):
    _pad_bed(sc, II_END, III_END, vel=40)
    _choir_bed(sc, II_END, III_END,
               [(II_END, 28), (324.0, 46), (III_END - 2, 30)],
               [(II_END, 30), (324.0, 58), (III_END - 2, 40)], vel=38)
    _shaku_haze(sc, II_END, III_END,
                [(II_END, 26), (324.0, 44), (III_END - 2, 28)], vel=44)
    _crystal_shimmer(sc, II_END, III_END)
    _harmonica_solo(sc, II_END, III_END)


# IV. Evening Water [376, 464) — the noon fall stretched, the plagal, the tolls
def _b_evening(sc):
    _pad_bed(sc, III_END, FINAL_DOWNBEAT - 8.0, vel=40)
    _choir_bed(sc, III_END, FINAL_DOWNBEAT - 8.0,
               [(III_END, 30), (410.0, 44), (FINAL_DOWNBEAT - 10, 30)],
               [(III_END, 34), (410.0, 56), (FINAL_DOWNBEAT - 10, 38)], vel=40)
    _shaku_haze(sc, III_END, FINAL_DOWNBEAT - 8.0,
                [(III_END, 26), (410.0, 42), (FINAL_DOWNBEAT - 10, 26)], vel=42)
    # the noon fall stretched into evening (augmented, stretch 2) on the flute
    # and the Rhodes — slow diatonic G-F-E-D-C falls.
    _noon_fall(sc, CH_FLUTE, [380.0], en.n("G5"), vel=70, stretch=2.0, gate=0.9)
    _noon_fall(sc, CH_RHODES, [400.0], en.n("G4"), vel=66, stretch=2.0, gate=0.9)
    en.echo_throw(sc, CH_FLUTE, 388.0)
    _plagal_cadence(sc)
    _final_chord(sc)
    _tolls(sc)


BUILDERS = [_b_glare, _b_afternoon, _b_heat_shimmer, _b_evening]

# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """Distance 0: both themes imply C (pc 0), the pair lazy together at last."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 1:
        fails.append(f"{len(isl)} island statements, want 1 (the lazy overlap)")
    if len(mnl) != 1:
        fails.append(f"{len(mnl)} mainland statements, want 1 (the lazy overlap)")
    for ch, start, _e, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {ISLAND_TONIC_PC} (C)")
    for ch, start, _e, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {MAINLAND_TONIC_PC} (C)")
    if isl and mnl:
        dist = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if dist != 0:
            fails.append(f"shore distance {dist}, want 0 (Act Two: together in C)")
    return fails


def _o_overlap(sc):
    """The simultaneity law: >= 1 island+mainland overlap, downbeat-consonant
    across it (the Act One ban is dead)."""
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
    """The shared language: >= 1 forward FUSION statement, tonic C (pc 0)."""
    fails = []
    fus = material.theme_statements(sc, "fusion")
    if len(fus) < 1:
        fails.append("no forward FUSION statement (Act Two requires >= 1)")
    for ch, start, _e, first in fus:
        if first % 12 != MAINLAND_TONIC_PC:
            fails.append(f"fusion at {start:.1f} implies pc {first % 12}, "
                         f"want {MAINLAND_TONIC_PC} (C)")
    return fails


def _o_hook_density(sc):
    """The noon-fall earworm: HOOK7 stated >= 6 times UNNESTED (the forward
    fusion auto-registers it, so that nested hit does not count)."""
    hits = material.hook_statements_unnested(sc, NUMBER)
    if len(hits) < 6:
        return [f"HOOK7 (unnested) found {len(hits)} times, want >= 6"]
    return []


def _o_protagonist_bass(sc):
    """The McCartney bass sings: stepwise-dominant, wide-ranging, stating HOOK7
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
        fails.append(f"HOOK7 in the bass inside choruses {len(in_chorus)}, "
                     f"want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The afternoon thickens: every chorus bass note-on shadowed at the octave
    on the partner Rhodes (coverage >= 0.80), and not outside (< 0.30)."""
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
    """The afternoon inhales: >= 2 bars where only the pan flute sounds, playing
    HOOK7's head over a strictly-rising CC11 swell."""
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
        fails.append(f"herald has {len(pf)} pan-flute notes, want 3 (the noon "
                     f"fall's head)")
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
    """The road home assembles exactly five notes and stops: the pinned REACH
    prefix registers, and NO longer prefix and no full retrograde exist."""
    fails = []
    target = material.RETRO_REACH[NUMBER]                # 5
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
    """The tide-word NOON, tapped on steel drums (MORSE_PROGRAMS[7] = 114), in
    standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 114:
        fails.append("morse timbre for T7 must be steel drums (program 114)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_MORSE)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} (NOON)")
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
    """Summer opens the mouth, but not all the way: choir CC70 never exceeds 95."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_echo_throws(sc):
    """The Enigma punctuation: CC94 echo throws on phrase tails, used sparingly
    (2-6 across the track)."""
    peaks = 0
    for ch in sorted(sc.events):
        peaks += sum(1 for _b, v in _cc_lane(sc, ch, 94) if v >= 88)
    if not 2 <= peaks <= 6:
        return [f"{peaks} echo throws, want 2-6 (sparing Enigma punctuation)"]
    return []


def _o_tide_breath(sc):
    """The water is in the tempo everywhere: every movement swells (>= 2
    troughs) — there are no still points on the water."""
    fails = []
    for name, t0, t1 in [m[:3] for m in PART.MOVEMENTS]:
        seq = [bpm for _b, bpm in _movement_events(t0, t1)]
        troughs = sum(1 for i in range(1, len(seq) - 1)
                      if seq[i] < seq[i - 1] and seq[i] < seq[i + 1])
        if troughs < 2:
            fails.append(f"'{name}' has {troughs} tide troughs, want >= 2")
    return fails


def _o_harmonica_scoops(sc):
    """The album's one harmonica: draw-bend scoops in movement III, recentred
    (the last bend before the seam is 0) — the generic bend-hygiene check owns
    the boundary; this proves the feature exists and is III-only."""
    fails = []
    fracs = sorted((t / _PPQ, ((d[1] | (d[2] << 7)) - 8192) / 8192.0)
                   for t, _p, d in sc.events.get(CH_HARM, [])
                   if (d[0] & 0xF0) == 0xE0)
    scoops = [f for _b, f in fracs if f < -0.02]
    if len(scoops) < 3:
        fails.append(f"harmonica has {len(scoops)} draw-bend scoops, want >= 3")
    outside = [b for b, _f in fracs if not II_END - 1e-6 <= b < III_END]
    if outside:
        fails.append(f"harmonica bends outside Heat Shimmer (e.g. beat "
                     f"{outside[0]:.1f})")
    return fails


def _o_plagal_final(sc):
    """The Act Two plagal signature: the bass approaches on F (the IV of C) and
    lands the tonic C on the final downbeat."""
    return [f"plagal final: {m}" for m in material.plagal_final_failures(
        sc, CH_BASS, FINAL_DOWNBEAT, MAINLAND_TONIC_PC, window=8.0)]


def _o_shore_pans(sc):
    """The re-opened strait: island voices left (54), mainland voices right
    (74); the autopan crystal keeps its own seat and is exempt."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_SYNTH, CH_SHAKU, CH_PANFLUTE, CH_CHOIR, CH_FLUTE}
    mainland = {CH_RHODES, CH_HARM}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{{ISL_PAN}}}")
    for ch in sorted(mainland):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {MAIN_PAN}:
            fails.append(f"mainland ch{ch} pans {sorted(pans)}, want {{{MAIN_PAN}}}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls seven times on the C, the final note-ons of the
    track; nothing else sounds after the first strike."""
    fails = []
    bells = _note_ons(sc, CH_BELLS)
    if len(bells) != material.TOLLS[NUMBER]:
        fails.append(f"{len(bells)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p, _v in bells:
        if p % 12 != ISLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want {ISLAND_TONIC_PC} (C)")
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
        ("morse_noon", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("echo_throws", _o_echo_throws(sc)),
        ("tide_breath", _o_tide_breath(sc)),
        ("harmonica_scoops", _o_harmonica_scoops(sc)),
        ("plagal_final", _o_plagal_final(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    glare = _rms_db(40.0, 88.0)         # movement I, the hazy glare
    herald = _rms_db(98.0, 104.0)       # the breath herald, alone
    chorus = _rms_db(220.0, 244.0)      # movement II, the second chorus
    shimmer = _rms_db(300.0, 360.0)     # movement III, the heat shimmer
    evening = _rms_db(392.0, 424.0)     # movement IV, before the tolls

    # 1. The afternoon is warmer than the glare: the groove chorus is not
    #    quieter than the hazy opening it grew from.
    fails = []
    if chorus - glare < -1.5:
        fails.append(f"the chorus {chorus:.1f} dB is quieter than the glare "
                     f"{glare:.1f} dB (the afternoon should build)")
    checks.append(("audio_afternoon_warmer", fails))

    # 2. The evening recedes: movement IV sits at or below the heat shimmer
    #    (the day cooling toward the tolls).
    fails = []
    if evening - shimmer > 2.0:
        fails.append(f"the evening {evening:.1f} dB is louder than the shimmer "
                     f"{shimmer:.1f} dB (dusk should recede, not swell)")
    checks.append(("audio_evening_recedes", fails))

    # 3. The breath herald is the quiet inhale: the groove chorus sits above it.
    fails = []
    if chorus - herald < 0.5:
        fails.append(f"the chorus {chorus:.1f} dB not >= 0.5 dB over the herald "
                     f"{herald:.1f} dB (the inhale should be the quiet part)")
    checks.append(("audio_herald_inhale", fails))
    return checks

