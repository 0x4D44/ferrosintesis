"""Six-Five-Two-One — an ecstatic build/drop manifesto in C major."""

from __future__ import annotations

import engine as en
import material
from . import common as c

ROOT = 48  # C3
MODE = "major"
PROG = material.PROG_6521

CH_ORBIT = 0
CH_PAD = 1
CH_BASS = 2
CH_PIANO = 3
CH_LEAD = 4
CH_HARP = 5
CH_BRASS_L = 6
CH_BRASS_R = 7
CH_CHOIR = 8
CH_KIT = 9
CH_TOMS = 10
CH_SYNDRUM = 11
CH_HIT = 12
CH_RISER = 13
CH_GUITAR = 14
CH_STRINGS = 15

INTRO = (0.0, 32.0)
BUILD1 = (32.0, 96.0)
DROP1 = (96.0, 208.0)
BRIDGE = (208.0, 240.0)
BUILD2 = (240.0, 336.0)
DROP2 = (336.0, 464.0)
FINALE = (464.0, 560.0)
LIFT = 512.0
OUTRO = (560.0, 584.0)


def _hit_pulses(sc: en.Score, start: float, bars: int, root: int = ROOT,
                velocity: int = 100, every: int = 2) -> None:
    for bar in range(0, bars, every):
        beat = start + 4.0 * bar
        degree = PROG[bar % len(PROG)]
        sc.note(CH_HIT, en.pitch(root, MODE, degree), beat, 0.8, velocity, jt=0, jv=3)
        sc.note(CH_SYNDRUM, 48 + (bar % 8), beat + 0.5, 0.22,
                max(56, velocity - 14), jt=0, jv=3)


def _build_layers(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  50 if not second else 56, lo=52, hi=79, lift_every=8)
    c.pulse_chords(sc, CH_PIANO, ROOT + 12, MODE, PROG, start, bars, 4.0,
                   58 if not second else 64, pulses=(0.0, 1.5, 2.75),
                   duration=0.32, lo=60, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   68 if not second else 73, syncopated=second)
    c.build_drums(sc, start, bars, 52 if not second else 57,
                  91 if not second else 99, kick_after=0.50 if not second else 0.34)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.NUMBER_HOOK,
                     start + 8.0, max(1, (bars * 4 - 8) // 16), 16.0,
                     62 if not second else 68, 89 if not second else 98,
                     transpositions=(0, 0, 1, -1), octave=0)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start + 16.0, max(1, bars - 4), 71 if not second else 78,
                  step_bars=2)
    c.riser(sc, CH_RISER, start + bars * 4.0 - 8.0, 8.0,
            86 if not second else 94)
    # Deliberately escalating melodic-tom windows: 8 < 16 < 28 notes.
    for beat, density, velocity in (
        (start + 12.0, 8, 66 if not second else 72),
        (start + bars * 2.0 - 4.0, 16, 76 if not second else 82),
        (start + bars * 4.0 - 4.0, 28, 88 if not second else 96),
    ):
        c.melodic_fill(sc, CH_TOMS, beat, density, velocity, low=45)
    if second:
        for beat in (start + 56.0, start + 72.0, start + 88.0):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, beat,
                                 (5, 7, 9, 11, 9, 7, 5, 4), 75, octave=1)
        c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG, start + 32.0,
                       max(1, bars - 8), 56, vowel0=32, vowel1=88)


def _drop(sc: en.Score, start: float, bars: int, second: bool) -> None:
    energy = 91 if not second else 99
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  66 if not second else 72, lo=50, hi=81, gate=0.98)
    c.pulse_chords(sc, CH_PIANO, ROOT + 12, MODE, PROG, start, bars, 4.0,
                   70 if not second else 77, pulses=(0.0, 0.75, 1.5, 2.5, 3.25),
                   duration=0.24, lo=60, hi=93)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   88 if not second else 94, syncopated=True)
    c.four_floor(sc, start, bars, energy, hats16=second,
                 tambourine=second, crash_every=4 if second else 8)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.NUMBER_HOOK,
                     start, bars // 2, 8.0, 94 if not second else 101,
                     101 if not second else 112,
                     transpositions=(0, 0, 2, -1), harmony=4 if second else None)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start, bars, 92 if not second else 101, step_bars=2)
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG, start + (32.0 if not second else 0.0),
                   bars - (8 if not second else 0), 61 if not second else 70,
                   vowel0=45 if not second else 72, vowel1=96)
    _hit_pulses(sc, start, bars, velocity=102 if not second else 110,
                every=2 if not second else 1)
    for bar in range(3, bars, 4):
        c.fill(sc, start + 4.0 * bar, (bar // 4) % 4, energy + 4)
        c.melodic_fill(sc, CH_TOMS, start + 4.0 * bar,
                       12 if not second else 20, energy - 8, low=43)
    if second:
        for beat in range(int(start + 8.0), int(start + bars * 4.0), 16):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, float(beat),
                                 (5, 7, 9, 11, 12, 11, 9, 7), 88, octave=1)
        c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, start, bars,
                      4.0, 0.25, 76, lo=60, hi=96)
    c.sidechain_beds(sc, (CH_PAD, CH_CHOIR), start, bars * 4.0,
                     low=61 if second else 68, high=116)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (CH_ORBIT, "orbiting steel pan", 114, 96, 64, 42, 12, 15, 1),
        (CH_PAD, "wide warm pad", 89, 92, 64, 62, 26, 4, 0),
        (CH_BASS, "synth bass", 39, 105, 64, 22, 4, 0, 0),
        (CH_PIANO, "percussive electric piano", 4, 95, 64, 35, 20, 12, 0),
        (CH_LEAD, "number hook saw", 81, 100, 64, 35, 14, 18, 0),
        (CH_HARP, "harp glitter", 46, 92, 64, 57, 14, 22, 0),
        (CH_BRASS_L, "brass call left", 61, 96, 18, 38, 8, 4, 0),
        (CH_BRASS_R, "brass answer right", 61, 96, 110, 38, 8, 4, 0),
        (CH_CHOIR, "vowel choir", 52, 86, 64, 72, 30, 9, 0),
        (CH_KIT, "arena kit", None, 110, 64, 25, 0, 0, 0),
        (CH_TOMS, "melodic tom climb", 117, 101, 64, 31, 8, 5, 1),
        (CH_SYNDRUM, "zap synth drum", 118, 92, 64, 32, 14, 11, 1),
        (CH_HIT, "orchestra hit", 55, 98, 64, 42, 7, 4, 0),
        (CH_RISER, "reverse cymbal", 119, 92, 64, 60, 8, 0, 1),
        (CH_GUITAR, "overdriven guitar", 30, 96, 64, 34, 10, 18, 0),
        (CH_STRINGS, "high string canopy", 49, 87, 64, 69, 24, 4, 0),
    ])
    sc.program(CH_KIT, 25, 0.0)  # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One

    c.section(sc, 0.0, "I. Count the Sparks", meter=(4, 4))
    c.section(sc, 32.0, "II. First Climb")
    c.section(sc, 96.0, "III. Drop One")
    c.section(sc, 208.0, "IV. Negative Space", bpm=66.0)
    c.section(sc, 240.0, "V. Second Climb", bpm=132.0)
    c.section(sc, 336.0, "VI. Drop Two")
    c.section(sc, 464.0, "VII. Every Number at Once")
    c.section(sc, 512.0, "VIII. Two Steps Brighter", bpm=136.0)
    c.section(sc, 560.0, "IX. Afterimage", bpm=112.0)

    # A persistent transient orbit gives the track physical motion while all beds stay centred.
    c.orbit_riff(sc, CH_ORBIT, ROOT + 12, MODE, 0.0, 208.0, 58,
                 octave_lift_at=96.0, period=32.0)
    c.orbit_riff(sc, CH_ORBIT, ROOT + 12, MODE, 240.0, 560.0, 70,
                 octave_lift_at=336.0, period=32.0)

    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, 0.0, 8, 4.0, 43,
                  lo=52, hi=78, gate=0.99)
    c.flowing_arp(sc, CH_PIANO, ROOT + 12, MODE, PROG, 0.0, 8, 4.0,
                  0.5, 49, lo=60, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, 16.0, 4, 4.0, 52,
                   active=False)
    for beat in (24.0, 28.0):
        c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                      beat, 1, 60, step_bars=1)

    _build_layers(sc, BUILD1[0], int((BUILD1[1] - BUILD1[0]) / 4), second=False)
    _drop(sc, DROP1[0], int((DROP1[1] - DROP1[0]) / 4), second=False)

    # The half-time aerial: no kick, no bass pulse, only a single cymbal wash.
    sc.hit(49, BRIDGE[0], 78, 1.8)
    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 45, lo=69, hi=100, gate=0.99)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 0.5, 51, lo=60, hi=96)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.NUMBER_HOOK,
                     BRIDGE[0], 4, 8.0, 43, 55,
                     transpositions=(0, -1, 1, 0), octave=0)
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, (5, 1, 0, 4),
                   BRIDGE[0], 8, 43, vowel0=24, vowel1=56)
    en.cc_curve(sc, CH_STRINGS, 11,
                [(208.0, 42), (224.0, 91), (239.5, 58)], step=0.5)
    c.riser(sc, CH_RISER, 232.0, 8.0, 82)

    _build_layers(sc, BUILD2[0], int((BUILD2[1] - BUILD2[0]) / 4), second=True)
    _drop(sc, DROP2[0], int((DROP2[1] - DROP2[0]) / 4), second=True)

    # Finale in C: all established layers play together, then the whole scene lifts to D.
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, FINALE[0], 12, 4.0, 75,
                  lo=50, hi=83, gate=0.99)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, FINALE[0], 12, 4.0, 96,
                   syncopated=True)
    c.four_floor(sc, FINALE[0], 12, 101, hats16=True, tambourine=True,
                 crash_every=4)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.NUMBER_HOOK,
                     FINALE[0], 6, 8.0, 105, 114,
                     transpositions=(0, 0, 2, -1), harmony=4)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, FINALE[0], 12, 4.0,
                  0.25, 81, lo=60, hi=98)
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG, FINALE[0], 12, 73,
                   vowel0=83, vowel1=112)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  FINALE[0], 12, 106, step_bars=1)
    _hit_pulses(sc, FINALE[0], 12, velocity=114, every=1)
    for beat in (472.0, 488.0, 504.0):
        c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, beat,
                             (5, 7, 9, 11, 12, 14, 12, 11), 92, octave=1)

    lift_root = ROOT + 2
    c.chord_cycle(sc, CH_PAD, lift_root, MODE, PROG, LIFT, 12, 4.0, 79,
                  lo=52, hi=86, gate=0.99)
    c.bass_pattern(sc, CH_BASS, lift_root, MODE, PROG, LIFT, 12, 4.0, 100,
                   syncopated=True)
    c.four_floor(sc, LIFT, 12, 105, hats16=True, tambourine=True,
                 crash_every=4)
    c.motif_sequence(sc, CH_LEAD, lift_root + 12, MODE, material.NUMBER_HOOK,
                     LIFT, 6, 8.0, 111, 120,
                     transpositions=(0, 0, 2, 0), harmony=4)
    c.flowing_arp(sc, CH_HARP, lift_root + 12, MODE, PROG, LIFT, 12, 4.0,
                  0.25, 86, lo=62, hi=100)
    c.choir_blocks(sc, CH_CHOIR, lift_root, MODE, PROG, LIFT, 12, 78,
                   vowel0=94, vowel1=120)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), lift_root, MODE, PROG,
                  LIFT, 12, 111, step_bars=1)
    _hit_pulses(sc, LIFT, 12, root=lift_root, velocity=118, every=1)
    for beat in (520.0, 536.0, 552.0):
        c.guitar_bend_phrase(sc, CH_GUITAR, lift_root, MODE, beat,
                             (5, 7, 9, 11, 12, 14, 16, 14), 97, octave=1)
    c.sidechain_beds(sc, (CH_PAD, CH_CHOIR, CH_STRINGS), FINALE[0], 96.0,
                     low=58, high=119)
    sc.note(CH_LEAD, 93, 556.0, 3.6, 124, jt=0, jv=1)

    # A deliberately small afterimage after the maximal key-lift stack.
    c.chord_cycle(sc, CH_STRINGS, lift_root + 12, MODE, (0, 3, 0),
                  OUTRO[0], 6, 4.0, 49, lo=70, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_HARP, lift_root + 12, MODE, (0, 3, 0),
                  OUTRO[0], 6, 4.0, 0.5, 53, lo=62, hi=98)
    c.motif(sc, CH_LEAD, lift_root + 12, MODE, material.NUMBER_HOOK,
            OUTRO[0], 58, octave=0, stretch=2.0)
    sc.note(CH_BASS, lift_root - 12, OUTRO[0], 15.5, 54, jt=1, jv=2)
    sc.note(CH_HIT, lift_root, 583.0, 0.8, 112, jt=0, jv=2)


def oracles(sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    results.append((
        "6521_bass_is_literal",
        c.progression_root_failures(sc, CH_BASS, ROOT, MODE, PROG,
                                    DROP1[0], 28),
    ))

    d1 = c.velocity_sum(sc, *DROP1)
    d2 = c.velocity_sum(sc, *DROP2)
    fails = []
    if d2 <= d1 * 1.10:
        fails.append(f"drop two velocity mass {d2} <= 1.10 x drop one {d1}")
    results.append(("second_drop_is_bigger", fails))

    bridge_drums = c.note_count(sc, *BRIDGE, channels={CH_KIT})
    drop_drums = c.note_count(sc, *DROP1, channels={CH_KIT})
    fails = []
    if bridge_drums > 2:
        fails.append(f"aerial bridge has {bridge_drums} drum notes, want <= 2")
    if drop_drums < 400:
        fails.append(f"drop one has only {drop_drums} drum notes")
    results.append(("negative_space_is_a_real_hush", fails))

    counts = [
        c.note_count(sc, 44.0, 48.0, {CH_TOMS}),
        c.note_count(sc, 60.0, 64.0, {CH_TOMS}),
        c.note_count(sc, 92.0, 96.0, {CH_TOMS}),
    ]
    fails = [] if counts[0] < counts[1] < counts[2] else [
        f"tom fill density is {counts}, want strictly increasing"
    ]
    results.append(("fill_density_climbs", fails))

    maxima, minima = c.full_circle_extrema(c.cc_lane(sc, CH_ORBIT, 10))
    fails = []
    if min(maxima, minima) < 10:
        fails.append(f"orbit completes only {maxima} peaks / {minima} troughs")
    results.append(("full_circle_transient_orbit", fails))

    windows = ((240.0, 272.0), (272.0, 304.0), (304.0, 336.0))
    masses = [c.velocity_sum(sc, a, b) for a, b in windows]
    fails = [] if masses[0] < masses[1] < masses[2] else [
        f"second-build velocity windows are {masses}, want strictly rising"
    ]
    results.append(("dramatic_second_build", fails))

    lifted = c.pitches_at(sc, CH_LEAD, LIFT, OUTRO[0])
    fails = []
    if not lifted or max(lifted) < 91:
        fails.append("lifted finale never reaches a high D-key summit")
    if not ({0, 2, 4, 6, 7, 9, 11} & {p % 12 for p in lifted}):
        fails.append("lifted finale has no D-major pitch material")
    results.append(("two_semitone_finale_lift", fails))

    return results
