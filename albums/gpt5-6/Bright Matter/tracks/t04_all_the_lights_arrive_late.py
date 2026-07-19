"""All the Lights Arrive Late — bright mallet-pop built around a withheld kick."""

from __future__ import annotations

import engine as en
import material
from . import common as c

ROOT = 57  # A3
MODE = "major"
PROG = material.PROG_6521

CH_BELL_L = 0
CH_BELL_R = 1
CH_PAD = 2
CH_BASS = 3
CH_PIANO = 4
CH_LEAD = 5
CH_HARP = 6
CH_STRINGS = 7
CH_BRASS_L = 8
CH_KIT = 9
CH_BRASS_R = 10
CH_CHOIR = 11
CH_TOMS = 12
CH_HIT = 13
CH_RISER = 14
CH_GUITAR = 15

INTRO = (0.0, 48.0)
BUILD1 = (48.0, 128.0)
FALSE_DROP = (128.0, 144.0)
DROP1 = (144.0, 256.0)
BRIDGE = (256.0, 288.0)
BUILD2 = (288.0, 384.0)
DROP2 = (384.0, 496.0)
OUTRO = (496.0, 544.0)


def _light_hocket(sc: en.Score, start: float, end: float, velocity: int,
                  step: float = 0.375) -> None:
    count = int((end - start) / step)
    degrees = (0, 2, 4, 7, 9, 7, 4, 2, 1, 4, 6, 9)
    for i in range(count):
        ch = CH_BELL_L if i % 2 == 0 else CH_BELL_R
        sc.note(ch, en.pitch(ROOT, MODE, degrees[i % len(degrees)], 1),
                start + i * step, step * 0.55,
                velocity + (9 if i % 8 == 0 else 0), jt=0, jv=2)


def _build(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  51 if not second else 58, lo=57, hi=86, gate=0.99)
    c.pulse_chords(sc, CH_PIANO, ROOT, MODE, PROG, start, bars, 4.0,
                   59 if not second else 67, pulses=(0.0, 0.75, 2.0, 3.25),
                   duration=0.28, lo=57, hi=89)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   67 if not second else 75, syncopated=second)
    _light_hocket(sc, start, start + bars * 4.0,
                  60 if not second else 70, step=0.375 if not second else 0.25)
    c.build_drums(sc, start, bars, 49 if not second else 57,
                  91 if not second else 101, kick_after=0.58 if not second else 0.35)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.LIGHTS_HOOK,
                     start + 8.0, max(1, (bars * 4 - 8) // 16), 16.0,
                     62 if not second else 71, 91 if not second else 102,
                     transpositions=(0, 1, 0, -1))
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start + 24.0, max(1, bars - 6), 71 if not second else 82,
                  step_bars=2)
    for beat in (start + 24.0, start + 52.0, start + bars * 4.0 - 4.0):
        if beat < start + bars * 4.0:
            c.melodic_fill(sc, CH_TOMS, beat,
                           10 if beat == start + 24.0 else (18 if beat == start + 52.0 else 28),
                           70 if not second else 79, low=45)
    c.riser(sc, CH_RISER, start + bars * 4.0 - 8.0, 8.0,
            87 if not second else 96)
    if second:
        c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG,
                       start + 32.0, max(1, bars - 8), 58,
                       vowel0=32, vowel1=91)
        for beat in (start + 48.0, start + 64.0, start + 80.0):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, beat,
                                 (0, 2, 4, 7, 9, 11, 9, 7), 76, octave=1)


def _drop(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  66 if not second else 74, lo=55, hi=88, gate=0.99)
    c.pulse_chords(sc, CH_PIANO, ROOT, MODE, PROG, start, bars, 4.0,
                   72 if not second else 81,
                   pulses=(0.0, 0.75, 1.5, 2.25, 3.0, 3.5), duration=0.24,
                   lo=57, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   89 if not second else 97, syncopated=True)
    _light_hocket(sc, start, start + bars * 4.0,
                  76 if not second else 86, step=0.25)
    c.four_floor(sc, start, bars, 92 if not second else 102,
                 hats16=True, tambourine=second,
                 crash_every=8 if not second else 4)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.LIGHTS_HOOK,
                     start, bars // 2, 8.0, 96 if not second else 106,
                     105 if not second else 117,
                     transpositions=(0, 0, 2, -1), harmony=4 if second else None)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, PROG, start, bars, 4.0,
                  0.25, 74 if not second else 84, lo=64, hi=103)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start, bars, 94 if not second else 106,
                  step_bars=2 if not second else 1)
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, PROG,
                   start + (32.0 if not second else 0.0),
                   bars - (8 if not second else 0), 62 if not second else 72,
                   vowel0=42 if not second else 68, vowel1=111)
    for bar in range(0, bars, 2 if second else 4):
        degree = PROG[bar % 4]
        sc.note(CH_HIT, en.pitch(ROOT, MODE, degree), start + 4.0 * bar,
                0.8, 103 if not second else 114, jt=0, jv=3)
    for throw in range(int(start + 12.0), int(start + bars * 4.0), 16):
        c.echo_throw(sc, CH_BELL_R if throw % 32 else CH_BELL_L,
                     float(throw), peak=116 if second else 108)
    if second:
        for beat in range(int(start + 16.0), int(start + bars * 4.0), 24):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, float(beat),
                                 (0, 4, 7, 9, 11, 14, 11, 9), 91, octave=1)
    c.sidechain_beds(sc, (CH_PAD, CH_CHOIR, CH_STRINGS), start, bars * 4.0,
                     low=58 if second else 66, high=117)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (CH_BELL_L, "late light marimba left", 12, 91, 18, 39, 10, 20, 0),
        (CH_BELL_R, "late light vibraphone right", 11, 91, 110, 48, 16, 26, 0),
        (CH_PAD, "city glow pad", 90, 91, 64, 66, 30, 8, 0),
        (CH_BASS, "night-drive bass", 38, 105, 64, 23, 4, 0, 0),
        (CH_PIANO, "glitter piano", 4, 96, 64, 38, 18, 13, 0),
        (CH_LEAD, "late-arrival lead", 81, 99, 64, 40, 16, 20, 0),
        (CH_HARP, "light-trail harp", 46, 91, 64, 66, 16, 24, 0),
        (CH_STRINGS, "window strings", 49, 89, 64, 70, 26, 5, 0),
        (CH_BRASS_L, "brass flare left", 61, 96, 22, 44, 9, 4, 0),
        (CH_KIT, "late kick kit", None, 111, 64, 25, 0, 0, 0),
        (CH_BRASS_R, "brass flare right", 61, 96, 106, 44, 9, 4, 0),
        (CH_CHOIR, "night-window choir", 52, 85, 64, 75, 30, 10, 0),
        (CH_TOMS, "city melodic toms", 117, 100, 64, 32, 8, 4, 1),
        (CH_HIT, "late orchestra hit", 55, 100, 64, 43, 6, 4, 0),
        (CH_RISER, "streetlight reverse", 119, 92, 64, 62, 8, 0, 1),
        (CH_GUITAR, "roofline guitar", 30, 96, 64, 37, 10, 19, 0),
    ])
    sc.program(CH_KIT, 25, 0.0)  # ch-10 PC 25: the ORIGINAL kit (Kit::V1) — matches Three-Sixty-One

    c.section(sc, 0.0, "I. City Blink", meter=(4, 4))
    c.section(sc, 48.0, "II. First Climb")
    c.section(sc, 128.0, "III. False Drop")
    c.section(sc, 144.0, "IV. The Kick Arrives")
    c.section(sc, 256.0, "V. Moonlit Delay", bpm=59.0)
    c.section(sc, 288.0, "VI. Second Climb", bpm=118.0)
    c.section(sc, 384.0, "VII. All the Lights", bpm=124.0)
    c.section(sc, 496.0, "VIII. Last Window", bpm=108.0)

    _light_hocket(sc, *INTRO, 48, step=0.5)
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, INTRO[0], 12, 4.0, 41,
                  lo=57, hi=86, gate=0.99)
    c.flowing_arp(sc, CH_PIANO, ROOT, MODE, PROG, 16.0, 8, 4.0,
                  0.5, 48, lo=57, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, 24.0, 6, 4.0, 50,
                   active=False)

    _build(sc, BUILD1[0], 20, second=False)

    # The melody and claps land on time; the kick is withheld for sixteen beats.
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, FALSE_DROP[0], 4, 4.0, 64,
                  lo=55, hi=88, gate=0.99)
    c.pulse_chords(sc, CH_PIANO, ROOT, MODE, PROG, FALSE_DROP[0], 4, 4.0, 72,
                   pulses=(0.0, 0.75, 1.5, 2.25, 3.0), duration=0.24,
                   lo=57, hi=91)
    _light_hocket(sc, *FALSE_DROP, 76, step=0.25)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.LIGHTS_HOOK,
                     FALSE_DROP[0], 2, 8.0, 92, 99,
                     transpositions=(0, 0))
    for bar in range(4):
        base = FALSE_DROP[0] + 4.0 * bar
        sc.hit(38, base + 1.0, 91)
        sc.hit(38, base + 3.0, 94)
        for i in range(8):
            sc.hit(42, base + 0.5 * i, 69 + (5 if i % 4 == 0 else 0), 0.07)
    c.echo_throw(sc, CH_BELL_R, 140.0, peak=118)

    _drop(sc, DROP1[0], 28, second=False)

    sc.hit(49, BRIDGE[0], 76, 1.8)
    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 42, lo=69, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_HARP, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 8, 4.0, 0.5, 47, lo=64, hi=101)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.LIGHTS_HOOK,
                     BRIDGE[0], 4, 8.0, 41, 56,
                     transpositions=(0, -1, 1, 0))
    c.choir_blocks(sc, CH_CHOIR, ROOT, MODE, (5, 1, 0, 4),
                   BRIDGE[0], 8, 41, vowel0=22, vowel1=54)
    c.echo_throw(sc, CH_BELL_L, 272.0, peak=122)
    c.riser(sc, CH_RISER, 280.0, 8.0, 84)

    _build(sc, BUILD2[0], 24, second=True)
    _drop(sc, DROP2[0], 28, second=True)

    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (0, 3, 5, 0),
                  OUTRO[0], 12, 4.0, 49, lo=69, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_BELL_R, ROOT + 24, MODE, (0, 3, 5, 0),
                  OUTRO[0], 12, 4.0, 0.5, 51, lo=76, hi=112)
    c.motif_sequence(sc, CH_LEAD, ROOT + 12, MODE, material.LIGHTS_HOOK,
                     OUTRO[0], 6, 8.0, 62, 48,
                     transpositions=(0, 0, -1, 0))
    sc.note(CH_BASS, ROOT - 12, OUTRO[0], 31.0, 51, jt=1, jv=2)
    for beat in (504.0, 520.0, 536.0):
        c.echo_throw(sc, CH_BELL_R, beat, peak=104)
    sc.note(CH_HIT, ROOT, 543.0, 0.8, 108, jt=0, jv=2)


def oracles(sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    results.append(("6521_city_bass",
                    c.progression_root_failures(sc, CH_BASS, ROOT, MODE, PROG,
                                                DROP1[0], 28)))

    fake_kicks = c.kick_count(sc, *FALSE_DROP)
    arrival_kicks = c.kick_count(sc, 144.0, 148.0)
    fails: list[str] = []
    if fake_kicks:
        fails.append(f"false drop contains {fake_kicks} kicks")
    if arrival_kicks < 4:
        fails.append(f"kick arrival bar contains only {arrival_kicks} kicks")
    results.append(("kick_arrives_late", fails))

    echo_peak = max(c.peak_cc(sc, CH_BELL_L, 94), c.peak_cc(sc, CH_BELL_R, 94))
    results.append(("mallet_echo_throws", [] if echo_peak >= 118 else [
        f"echo send peaks at {echo_peak}, want >= 118"
    ]))

    d1 = c.velocity_sum(sc, *DROP1)
    d2 = c.velocity_sum(sc, *DROP2)
    results.append(("all_lights_drop_is_bigger", [] if d2 > d1 * 1.10 else [
        f"late drop mass {d2} <= 1.10 x first drop {d1}"
    ]))

    bridge_drums = c.note_count(sc, *BRIDGE, {CH_KIT})
    results.append(("moonlit_delay_hush", [] if bridge_drums <= 2 else [
        f"moonlit delay has {bridge_drums} drum notes"
    ]))

    ons = sorted((t, ch) for t, ch, _p, _v in c.note_ons(sc)
                 if ch in (CH_BELL_L, CH_BELL_R) and t < en.tick(128.0))
    fails = [] if len(ons) >= 128 and not any(a[1] == b[1] for a, b in zip(ons, ons[1:])) else [
        "light hocket is missing or stops alternating"
    ]
    results.append(("transient_light_hocket", fails))

    return results
