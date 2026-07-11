"""Gravity Has a Chorus — asymmetric launch vectors resolving into a massed vocal drop."""

from __future__ import annotations

import engine as en
import material
from . import common as c

ROOT = 50  # D3
MODE = "major"
PROG = material.PROG_6521

CH_GLASS = 0
CH_ARP = 1
CH_PAD = 2
CH_BASS = 3
CH_LEAD = 4
CH_STRINGS = 5
CH_CHOIR_A = 6
CH_CHOIR_B = 7
CH_BRASS_L = 8
CH_KIT = 9
CH_BRASS_R = 10
CH_HARP = 11
CH_ORGAN = 12
CH_TOMS = 13
CH_HIT = 14
CH_RISER = 15

INTRO = (0.0, 56.0)
BUILD1 = (56.0, 112.0)
DROP1 = (112.0, 240.0)
BRIDGE = (240.0, 280.0)
BUILD2 = (280.0, 364.0)
DROP2 = (364.0, 492.0)
FINALE = (492.0, 564.0)
OUTRO = (564.0, 588.0)


def _seven_engine(sc: en.Score, start: float, bars: int, velocity: int,
                  dense: bool = False) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 3.5, velocity - 13,
                  lo=51, hi=82, gate=0.97)
    c.flowing_arp(sc, CH_ARP, ROOT + 12, MODE, PROG, start, bars, 3.5,
                  0.25 if dense else 0.5, velocity, lo=61, hi=98,
                  order=(0, 1, 2, 3, 2, 1, 2, 0))
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 3.5,
                   velocity + 9, syncopated=dense)
    for bar in range(bars):
        base = start + bar * 3.5
        subdivisions = 14 if dense or bar >= bars // 2 else 7
        step = 3.5 / subdivisions
        for i in range(subdivisions):
            sc.hit(42, base + i * step, velocity - 22 + (6 if i % 7 == 0 else 0), 0.06)
        sc.hit(38, base + 1.75, velocity - 5)
        if bar >= bars // 2:
            sc.hit(36, base, velocity + 8)
            sc.hit(36, base + 2.0, velocity + 2)
        if bar % 4 == 3:
            c.melodic_fill(sc, CH_TOMS, base - 0.5, 12 if not dense else 20,
                           velocity + 1, low=43)


def _gravity_drop(sc: en.Score, start: float, bars: int, second: bool) -> None:
    energy = 91 if not second else 101
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  66 if not second else 74, lo=50, hi=83, gate=0.99)
    c.pulse_chords(sc, CH_STRINGS, ROOT, MODE, PROG, start, bars, 4.0,
                   64 if not second else 73, pulses=(0.0, 1.0, 2.0, 3.0),
                   duration=0.43, lo=57, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   88 if not second else 97, syncopated=True)
    c.four_floor(sc, start, bars, energy, hats16=second, tambourine=second,
                 crash_every=8 if not second else 4)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     start, bars // 2, 8.0, 92 if not second else 103,
                     102 if not second else 116,
                     transpositions=(0, 0, 2, -1), harmony=4 if second else None)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start, bars, 93 if not second else 105,
                  step_bars=2 if not second else 1)
    c.choir_blocks(sc, CH_CHOIR_A, ROOT, MODE, PROG, start, bars,
                   63 if not second else 73,
                   vowel0=38 if not second else 66, vowel1=106)
    c.choir_blocks(sc, CH_CHOIR_B, ROOT + 12, MODE, PROG,
                   start + (32.0 if not second else 0.0),
                   max(1, bars - (8 if not second else 0)),
                   52 if not second else 65, vowel0=25, vowel1=91)
    for bar in range(0, bars, 2 if second else 4):
        degree = PROG[bar % len(PROG)]
        sc.note(CH_HIT, en.pitch(ROOT, MODE, degree), start + 4.0 * bar,
                0.9, 103 if not second else 114, jt=0, jv=3)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, start, bars, 4.0,
                  0.5 if not second else 0.25, 67 if not second else 80,
                  lo=62, hi=99)
    c.sidechain_beds(sc, (CH_PAD, CH_CHOIR_A, CH_CHOIR_B), start, bars * 4.0,
                     low=60 if second else 68, high=116)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (CH_GLASS, "gravity glass", 8, 88, 64, 52, 16, 20, 0),
        (CH_ARP, "vector arpeggiator", 5, 95, 64, 39, 22, 16, 0),
        (CH_PAD, "mass field pad", 91, 91, 64, 68, 30, 7, 0),
        (CH_BASS, "gravity bass", 39, 105, 64, 23, 4, 0, 0),
        (CH_LEAD, "gravity call lead", 82, 99, 64, 42, 15, 17, 0),
        (CH_STRINGS, "orbital strings", 49, 91, 64, 70, 26, 5, 0),
        (CH_CHOIR_A, "chorus ah", 52, 88, 64, 77, 32, 8, 0),
        (CH_CHOIR_B, "chorus oo counterline", 53, 83, 64, 78, 28, 10, 0),
        (CH_BRASS_L, "mass brass left", 61, 96, 20, 45, 9, 4, 0),
        (CH_KIT, "gravity kit", None, 111, 64, 25, 0, 0, 0),
        (CH_BRASS_R, "mass brass right", 61, 96, 108, 45, 9, 4, 0),
        (CH_HARP, "zero-g harp", 46, 91, 64, 68, 16, 22, 0),
        (CH_ORGAN, "cathedral mass organ", 19, 91, 64, 75, 26, 5, 0),
        (CH_TOMS, "vector toms", 117, 101, 64, 32, 7, 4, 1),
        (CH_HIT, "gravity orchestra hit", 55, 100, 64, 43, 6, 4, 0),
        (CH_RISER, "mass reverse cymbal", 119, 91, 64, 63, 8, 0, 1),
    ])
    sc.program(CH_KIT, 1, 0.0)

    c.section(sc, 0.0, "I. Weightless Count", meter=(7, 8))
    c.section(sc, 56.0, "II. First Vector")
    c.section(sc, 112.0, "III. Gravity Drop", bpm=140.0, meter=(4, 4))
    c.section(sc, 240.0, "IV. Zero-G Choir", bpm=70.0, meter=(5, 4))
    c.section(sc, 280.0, "V. Massing", bpm=140.0, meter=(7, 8))
    c.section(sc, 364.0, "VI. Gravity Returns", meter=(4, 4))
    c.section(sc, 492.0, "VII. Chorus of Mass")
    c.section(sc, 564.0, "VIII. Quiet Field", bpm=112.0)

    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, INTRO[0], 16, 3.5, 40,
                  lo=51, hi=81, gate=0.99)
    c.flowing_arp(sc, CH_GLASS, ROOT + 24, MODE, PROG, INTRO[0], 16, 3.5,
                  0.5, 48, lo=72, hi=108)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     7.0, 6, 8.0, 45, 63,
                     transpositions=(0, -1, 0, 2))
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, 28.0, 8, 3.5, 48,
                   active=False)

    _seven_engine(sc, BUILD1[0], 16, 61, dense=False)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     60.0, 6, 8.0, 62, 91,
                     transpositions=(0, 0, 2, -1))
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  80.0, 8, 74, step_bars=2)
    c.riser(sc, CH_RISER, 104.0, 8.0, 88)

    _gravity_drop(sc, DROP1[0], 32, second=False)

    # At zero gravity the pulse vanishes and the choir's vowel slowly opens.
    sc.hit(49, BRIDGE[0], 77, 1.8)
    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 5.0, 42, lo=68, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 5.0, 0.5, 48, lo=62, hi=99)
    c.choir_blocks(sc, CH_CHOIR_A, ROOT, MODE, (5, 1, 0, 4),
                   BRIDGE[0], 10, 43, vowel0=18, vowel1=67)
    c.choir_blocks(sc, CH_CHOIR_B, ROOT + 12, MODE, (0, 4, 1, 5),
                   BRIDGE[0], 10, 38, vowel0=24, vowel1=53)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     BRIDGE[0], 5, 8.0, 42, 56,
                     transpositions=(0, -1, 1, 0))
    c.riser(sc, CH_RISER, 272.0, 8.0, 84)

    _seven_engine(sc, BUILD2[0], 24, 67, dense=True)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     284.0, 10, 8.0, 70, 101,
                     transpositions=(0, 2, 0, -1), harmony=4)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  312.0, 13, 83, step_bars=2)
    c.choir_blocks(sc, CH_CHOIR_A, ROOT, MODE, PROG, 312.0, 13, 57,
                   vowel0=35, vowel1=91)
    c.riser(sc, CH_RISER, 356.0, 8.0, 96)

    _gravity_drop(sc, DROP2[0], 32, second=True)

    # The organ arrives last and turns authored CC11 into both volume and reed drive.
    c.chord_cycle(sc, CH_ORGAN, ROOT - 12, MODE, PROG, FINALE[0], 18, 4.0,
                  70, size=4, lo=34, hi=77, gate=0.99)
    en.cc_curve(sc, CH_ORGAN, 11,
                [(492.0, 48), (516.0, 78), (540.0, 108), (560.0, 127),
                 (564.0, 82)], step=0.5)
    en.cc_curve(sc, CH_ORGAN, 1,
                [(492.0, 8), (532.0, 54), (560.0, 92), (564.0, 0)], step=1.0)
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, FINALE[0], 18, 4.0, 76,
                  lo=50, hi=84, gate=0.99)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, FINALE[0], 18, 4.0, 99,
                   syncopated=True)
    c.four_floor(sc, FINALE[0], 18, 104, hats16=True, tambourine=True,
                 crash_every=3)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     FINALE[0], 9, 8.0, 108, 119,
                     transpositions=(0, 0, 2, -1), harmony=4)
    c.choir_blocks(sc, CH_CHOIR_A, ROOT, MODE, PROG, FINALE[0], 18, 78,
                   vowel0=84, vowel1=122)
    c.choir_blocks(sc, CH_CHOIR_B, ROOT + 12, MODE, (0, 5, 3, 1),
                   FINALE[0], 18, 67, vowel0=45, vowel1=96)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  FINALE[0], 18, 111, step_bars=1)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, FINALE[0], 18, 4.0,
                  0.25, 83, lo=62, hi=101)
    for bar in range(18):
        degree = PROG[bar % 4]
        sc.note(CH_HIT, en.pitch(ROOT, MODE, degree), FINALE[0] + 4.0 * bar,
                0.9, 116, jt=0, jv=3)
    c.sidechain_beds(sc, (CH_PAD, CH_CHOIR_A, CH_CHOIR_B),
                     FINALE[0], 72.0, low=56, high=120)

    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (0, 3, 0),
                  OUTRO[0], 6, 4.0, 47, lo=69, hi=101, gate=0.99)
    c.choir_blocks(sc, CH_CHOIR_A, ROOT, MODE, (0, 3, 0),
                   OUTRO[0], 6, 42, vowel0=68, vowel1=32)
    sc.note(CH_ORGAN, ROOT - 24, OUTRO[0], 18.0, 45, jt=0, jv=2)
    en.cc_curve(sc, CH_ORGAN, 11, [(564.0, 82), (580.0, 32), (588.0, 0)], 0.5)
    sc.note(CH_HIT, ROOT, 587.0, 0.8, 108, jt=0, jv=2)


def oracles(sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    results.append(("6521_gravity_bass",
                    c.progression_root_failures(sc, CH_BASS, ROOT, MODE, PROG,
                                                DROP1[0], 32)))

    meters = {(num, den) for _beat, num, den in sc.timesigs}
    wanted = {(7, 8), (4, 4), (5, 4)}
    results.append(("meters_change_with_gravity", [] if wanted <= meters else [
        f"meters {sorted(meters)} do not include {sorted(wanted)}"
    ]))

    organ_notes = c.note_count(sc, FINALE[0], FINALE[1], {CH_ORGAN})
    organ_lane = c.cc_lane(sc, CH_ORGAN, 11)
    fails: list[str] = []
    if organ_notes < 60:
        fails.append(f"organ finale has only {organ_notes} notes")
    if c.floor_cc(sc, CH_ORGAN, 11) > 50 or c.peak_cc(sc, CH_ORGAN, 11) < 127:
        fails.append("organ swell does not span quiet to full reed drive")
    if not organ_lane:
        fails.append("organ authors no CC11 swell")
    results.append(("organ_swell_to_full_mass", fails))

    vowels = c.cc_lane(sc, CH_CHOIR_A, 70) + c.cc_lane(sc, CH_CHOIR_B, 70)
    vals = [value for _tick, value in vowels]
    fails = []
    if not vals or min(vals) > 25 or max(vals) < 115:
        fails.append(f"choir vowel range is {min(vals) if vals else 'none'}..{max(vals) if vals else 'none'}")
    results.append(("choir_opens_from_oo_to_ah", fails))

    d1 = c.velocity_sum(sc, *DROP1)
    d2 = c.velocity_sum(sc, *DROP2)
    results.append(("gravity_returns_bigger", [] if d2 > d1 * 1.10 else [
        f"drop two mass {d2} <= 1.10 x drop one {d1}"
    ]))

    bridge_drums = c.note_count(sc, *BRIDGE, {CH_KIT})
    results.append(("zero_g_is_weightless", [] if bridge_drums <= 2 else [
        f"zero-g bridge has {bridge_drums} drum notes"
    ]))

    return results
