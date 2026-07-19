"""Runway Aurora — neon synth-rock accelerating from runway lamps into sky."""

from __future__ import annotations

import engine as en
import material
from . import common as c

ROOT = 52  # E3
MODE = "major"
PROG = material.PROG_6521

CH_LIGHT_L = 0
CH_LIGHT_R = 1
CH_PAD = 2
CH_BASS = 3
CH_MUTED = 4
CH_GUITAR = 5
CH_LEAD = 6
CH_STRINGS = 7
CH_BRASS_L = 8
CH_KIT = 9
CH_BRASS_R = 10
CH_CHOIR = 11
CH_TOMS = 12
CH_HIT = 13
CH_RISER = 14
CH_HARP = 15

INTRO = (0.0, 32.0)
BUILD1 = (32.0, 160.0)
DROP1 = (160.0, 272.0)
BRIDGE = (272.0, 304.0)
BUILD2 = (304.0, 400.0)
DROP2 = (400.0, 520.0)
OUTRO = (520.0, 548.0)


def _runway_hocket(sc: en.Score, start: float, end: float, velocity: int,
                   step: float = 0.25, lift: bool = False) -> None:
    degrees = material.ASCENT_CELL + tuple(reversed(material.ASCENT_CELL))
    count = int(round((end - start) / step))
    for i in range(count):
        ch = CH_LIGHT_L if i % 2 == 0 else CH_LIGHT_R
        octave = 1 + (1 if lift and i % 16 >= 12 else 0)
        note = en.pitch(ROOT, MODE, degrees[i % len(degrees)], octave)
        sc.note(ch, note, start + i * step, step * 0.58,
                velocity + (8 if i % 8 == 0 else 0), jt=0, jv=2)


def _muted_engine(sc: en.Score, start: float, bars: int, velocity: int) -> None:
    roots = c.voice_led_progression(ROOT, MODE, PROG, size=3, lo=52, hi=76)
    for bar in range(bars):
        base = start + 4.0 * bar
        chord = roots[bar % len(roots)]
        for pulse in range(8):
            note = chord[(pulse + bar) % len(chord)]
            sc.note(CH_MUTED, note, base + 0.5 * pulse, 0.22,
                    velocity + (8 if pulse in (0, 6) else 0), jt=1, jv=3)


def _build(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  51 if not second else 58, lo=52, hi=82, gate=0.99)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   66 if not second else 74, syncopated=second)
    _muted_engine(sc, start, bars, 59 if not second else 68)
    _runway_hocket(sc, start, start + bars * 4.0,
                   58 if not second else 67, lift=second)
    c.build_drums(sc, start, bars, 48 if not second else 56,
                  93 if not second else 102, kick_after=0.57 if not second else 0.36)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.RUNWAY_HOOK,
                     start + 16.0, max(1, (bars * 4 - 16) // 16), 16.0,
                     63 if not second else 72, 91 if not second else 101,
                     transpositions=(0, 2, 0, -1))
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start + 32.0, max(1, bars - 8), 72 if not second else 82,
                  step_bars=2)
    for index, beat in enumerate((start + 44.0, start + 76.0, start + bars * 4.0 - 4.0)):
        if beat >= start + bars * 4.0:
            continue
        c.melodic_fill(sc, CH_TOMS, beat, 10 + index * 8,
                       70 + index * 8 + (6 if second else 0), low=43)
    c.riser(sc, CH_RISER, start + bars * 4.0 - 8.0, 8.0,
            86 if not second else 96)
    if second:
        c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG,
                       start + 32.0, max(1, bars - 8), 58,
                       vowel0=30, vowel1=92)
        for beat in (start + 48.0, start + 64.0, start + 80.0):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, beat,
                                 (0, 4, 7, 9, 11, 9, 7, 4), 79, octave=1)


def _drop(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  67 if not second else 74, lo=50, hi=84, gate=0.99)
    c.pulse_chords(sc, CH_STRINGS, ROOT, MODE, PROG, start, bars, 4.0,
                   65 if not second else 72, pulses=(0.0, 1.0, 2.5),
                   duration=0.58, lo=57, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   88 if not second else 96, syncopated=True)
    _muted_engine(sc, start, bars, 76 if not second else 84)
    _runway_hocket(sc, start, start + bars * 4.0,
                   75 if not second else 85, lift=True)
    c.four_floor(sc, start, bars, 92 if not second else 102,
                 hats16=True, tambourine=second,
                 crash_every=8 if not second else 4)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.RUNWAY_HOOK,
                     start, bars // 2, 8.0, 96 if not second else 105,
                     104 if not second else 116,
                     transpositions=(0, 0, 2, -1), harmony=4 if second else None)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start, bars, 94 if not second else 106,
                  step_bars=2 if not second else 1)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, start, bars, 4.0,
                  0.25 if second else 0.5, 68 if not second else 82,
                  lo=64, hi=100)
    for beat in range(int(start + 8.0), int(start + bars * 4.0), 16):
        c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, float(beat),
                             (0, 4, 7, 9, 11, 14, 11, 9),
                             85 if not second else 94, octave=1)
    for bar in range(0, bars, 2 if second else 4):
        degree = PROG[bar % len(PROG)]
        sc.note(CH_HIT, en.pitch(ROOT, MODE, degree), start + 4.0 * bar,
                0.75, 103 if not second else 113, jt=0, jv=3)
    if second:
        c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG, start, bars, 70,
                       vowel0=65, vowel1=112)
    c.sidechain_beds(sc, (CH_PAD, CH_STRINGS, CH_CHOIR), start, bars * 4.0,
                     low=59 if second else 66, high=117)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (CH_LIGHT_L, "runway marimba left", 12, 92, 18, 36, 8, 18, 0),
        (CH_LIGHT_R, "runway celesta right", 8, 90, 110, 44, 13, 24, 0),
        (CH_PAD, "aurora sweep pad", 95, 91, 64, 65, 30, 8, 0),
        (CH_BASS, "launch bass", 38, 105, 64, 22, 4, 0, 0),
        (CH_MUTED, "muted rhythm guitar", 28, 95, 64, 28, 9, 7, 0),
        (CH_GUITAR, "distorted sky guitar", 30, 99, 64, 38, 12, 19, 0),
        (CH_LEAD, "runway pulse lead", 81, 100, 64, 39, 15, 18, 0),
        (CH_STRINGS, "high cloud strings", 49, 88, 64, 70, 24, 6, 0),
        (CH_BRASS_L, "horn flare left", 60, 96, 24, 44, 10, 4, 0),
        (CH_KIT, "launch kit", None, 111, 64, 24, 0, 0, 0),
        (CH_BRASS_R, "horn flare right", 60, 96, 104, 44, 10, 4, 0),
        (CH_CHOIR, "aurora choir", 53, 85, 64, 74, 30, 10, 0),
        (CH_TOMS, "ascending melodic toms", 117, 100, 64, 31, 8, 4, 1),
        (CH_HIT, "launch orchestra hits", 55, 100, 64, 42, 5, 4, 0),
        (CH_RISER, "jet wash reverse", 119, 91, 64, 62, 8, 0, 1),
        (CH_HARP, "high-altitude harp", 46, 91, 64, 64, 14, 22, 0),
    ])
    sc.program(CH_KIT, 25, 0.0)  # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One

    c.section(sc, 0.0, "I. Cold Lamps", meter=(4, 4))
    c.section(sc, 32.0, "II. Edge Lights")
    c.section(sc, 96.0, "III. Ignition")
    c.section(sc, 160.0, "IV. First Launch")
    c.section(sc, 272.0, "V. Cloud Deck", bpm=64.0, meter=(6, 8))
    c.section(sc, 304.0, "VI. Re-entry Build", bpm=126.0, meter=(4, 4))
    c.section(sc, 400.0, "VII. Aurora Drop", bpm=138.0)
    c.section(sc, 520.0, "VIII. Wheels Down", bpm=112.0)

    _runway_hocket(sc, *INTRO, 48, step=0.5)
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, INTRO[0], 8, 4.0, 42,
                  lo=52, hi=82, gate=0.99)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, 16.0, 4, 4.0, 50,
                   active=False)
    _muted_engine(sc, 24.0, 2, 48)

    _build(sc, BUILD1[0], int((BUILD1[1] - BUILD1[0]) / 4), second=False)
    _drop(sc, DROP1[0], int((DROP1[1] - DROP1[0]) / 4), second=False)

    # High-altitude pause: the kit and bass disappear, guitar turns to a distant signal.
    sc.hit(49, BRIDGE[0], 77, 1.5)
    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 43, lo=68, hi=100, gate=0.99)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 0.5, 49, lo=64, hi=100)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.RUNWAY_HOOK,
                     BRIDGE[0], 4, 8.0, 42, 55,
                     transpositions=(0, -1, 0, 2))
    c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, 288.0,
                         (0, 2, 4, 7, 9, 7, 4, 2), 60, octave=1)
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, (5, 1, 0, 4),
                   BRIDGE[0], 8, 42, vowel0=22, vowel1=54)
    c.riser(sc, CH_RISER, 296.0, 8.0, 84)

    _build(sc, BUILD2[0], int((BUILD2[1] - BUILD2[0]) / 4), second=True)
    _drop(sc, DROP2[0], int((DROP2[1] - DROP2[0]) / 4), second=True)

    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (0, 3, 0, 0),
                  OUTRO[0], 7, 4.0, 48, lo=69, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_LIGHT_R, ROOT + 24, MODE, (0, 3, 0, 0),
                  OUTRO[0], 7, 4.0, 0.5, 50, lo=72, hi=108)
    c.motif(sc, CH_GUITAR, ROOT, MODE, material.RUNWAY_HOOK,
            OUTRO[0], 61, octave=1, stretch=2.0)
    sc.note(CH_BASS, ROOT - 12, OUTRO[0], 18.0, 52, jt=1, jv=2)
    sc.note(CH_HIT, ROOT, 547.0, 0.8, 110, jt=0, jv=2)


def oracles(sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    results.append(("6521_launch_bass",
                    c.progression_root_failures(sc, CH_BASS, ROOT, MODE, PROG,
                                                DROP1[0], 28)))

    # The runway lamps must alternate left/right, never becoming a sustained stereo bed.
    ons = sorted((t, ch) for t, ch, _p, _v in c.note_ons(sc)
                 if ch in (CH_LIGHT_L, CH_LIGHT_R) and en.tick(0) <= t < en.tick(96))
    fails: list[str] = []
    if len(ons) < 128:
        fails.append(f"only {len(ons)} runway-light notes")
    elif any(a[1] == b[1] for a, b in zip(ons, ons[1:])):
        fails.append("runway light hocket stops alternating L/R")
    if {v for _t, v in c.cc_lane(sc, CH_LIGHT_L, 10)} != {18}:
        fails.append("left runway lamp leaves pan 18")
    if {v for _t, v in c.cc_lane(sc, CH_LIGHT_R, 10)} != {110}:
        fails.append("right runway lamp leaves pan 110")
    results.append(("runway_lights_hocket", fails))

    bends = c.bend_lane(sc, CH_GUITAR)
    fails = []
    if len(bends) < 80:
        fails.append(f"only {len(bends)} guitar bend events")
    if not any(value > 11000 for _tick, value in bends):
        fails.append("guitar never bends above centre")
    for boundary in (160.0, 272.0, 304.0, 400.0, 520.0):
        prior = [value for tick, value in bends if tick <= en.tick(boundary)]
        if prior and prior[-1] != 8192:
            fails.append(f"bend not centred at section boundary {boundary:g}")
    results.append(("guitar_bend_arc_and_hygiene", fails))

    d1 = c.velocity_sum(sc, *DROP1)
    d2 = c.velocity_sum(sc, DROP2[0], DROP2[0] + (DROP1[1] - DROP1[0]))
    fails = [] if d2 > d1 * 1.12 else [
        f"aurora drop mass {d2} <= 1.12 x first launch {d1}"
    ]
    results.append(("aurora_drop_is_bigger", fails))

    bridge_drums = c.note_count(sc, *BRIDGE, channels={CH_KIT})
    results.append(("cloud_deck_hush", [] if bridge_drums <= 2 else [
        f"cloud deck contains {bridge_drums} drum notes"
    ]))

    peak_tempo = max(bpm for _beat, bpm in sc.tempos)
    results.append(("final_tempo_acceleration", [] if peak_tempo >= 138.0 else [
        f"peak tempo is {peak_tempo:g}, want >= 138"
    ]))

    return results
