"""Bright Matter (Everything at Once) — album finale and four-hook recombination."""

from __future__ import annotations

import engine as en
import material
from . import common as c

ROOT = 52  # E3
MODE = "major"
PROG = material.PROG_6521

CH_ORBIT = 0
CH_PIANO = 1
CH_PAD = 2
CH_BASS = 3
CH_NUMBER = 4
CH_GUITAR = 5
CH_STRINGS = 6
CH_GRAVITY = 7
CH_LIGHTS = 8
CH_KIT = 9
CH_BRASS_L = 10
CH_BRASS_R = 11
CH_ORGAN = 12
CH_TOMS = 13
CH_HIT = 14
CH_RISER = 15

INTRO = (0.0, 64.0)
BUILD1 = (64.0, 160.0)
DROP1 = (160.0, 288.0)
BRIDGE = (288.0, 328.0)
BUILD2 = (328.0, 424.0)
DROP2 = (424.0, 552.0)
STACK = (552.0, 632.0)
LIFT = (632.0, 664.0)
OUTRO = (664.0, 688.0)


def _piano_pulse(sc: en.Score, start: float, bars: int, root: int,
                 velocity: int, dense: bool) -> None:
    c.pulse_chords(sc, CH_PIANO, root, MODE, PROG, start, bars, 4.0,
                   velocity,
                   pulses=(0.0, 0.75, 1.5, 2.25, 3.0, 3.5) if dense
                   else (0.0, 1.5, 2.75),
                   duration=0.25 if dense else 0.36, lo=root + 5, hi=root + 39)


def _build(sc: en.Score, start: float, bars: int, second: bool) -> None:
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  51 if not second else 59, lo=52, hi=84, gate=0.99)
    _piano_pulse(sc, start, bars, ROOT, 60 if not second else 68, dense=second)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   67 if not second else 76, syncopated=second)
    c.build_drums(sc, start, bars, 49 if not second else 58,
                  94 if not second else 103, kick_after=0.52 if not second else 0.33)
    c.motif_sequence(sc, CH_NUMBER, ROOT + 12, MODE, material.NUMBER_HOOK,
                     start + 8.0, max(1, (bars * 4 - 8) // 16), 16.0,
                     63 if not second else 72, 92 if not second else 103,
                     transpositions=(0, 0, 2, -1))
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start + 24.0, max(1, bars - 6), 73 if not second else 84,
                  step_bars=2)
    c.riser(sc, CH_RISER, start + bars * 4.0 - 8.0, 8.0,
            88 if not second else 98)
    for beat, density in ((start + 28.0, 10), (start + 60.0, 18),
                          (start + bars * 4.0 - 4.0, 30)):
        if beat < start + bars * 4.0:
            c.melodic_fill(sc, CH_TOMS, beat, density,
                           71 + density // 3 + (6 if second else 0), low=43)
    if second:
        c.chord_cycle(sc, CH_ORGAN, ROOT - 12, MODE, PROG,
                      start + 32.0, max(1, bars - 8), 4.0, 51,
                      size=4, lo=34, hi=77, gate=0.99)
        en.cc_curve(sc, CH_ORGAN, 11,
                    [(start + 32.0, 38), (start + 64.0, 70),
                     (start + bars * 4.0, 94)], step=0.5)
        for beat in (start + 48.0, start + 64.0, start + 80.0):
            c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, beat,
                                 (0, 4, 7, 9, 11, 14, 11, 9), 80, octave=1)


def _drop(sc: en.Score, start: float, bars: int, second: bool) -> None:
    energy = 93 if not second else 103
    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, start, bars, 4.0,
                  67 if not second else 75, lo=50, hi=85, gate=0.99)
    c.pulse_chords(sc, CH_STRINGS, ROOT, MODE, PROG, start, bars, 4.0,
                   65 if not second else 74, pulses=(0.0, 1.0, 2.0, 3.0),
                   duration=0.45, lo=57, hi=93)
    _piano_pulse(sc, start, bars, ROOT, 73 if not second else 82, dense=True)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, start, bars, 4.0,
                   89 if not second else 98, syncopated=True)
    c.four_floor(sc, start, bars, energy, hats16=True, tambourine=second,
                 crash_every=8 if not second else 4)
    c.motif_sequence(sc, CH_NUMBER, ROOT + 12, MODE, material.NUMBER_HOOK,
                     start, bars // 2, 8.0, 96 if not second else 106,
                     105 if not second else 117,
                     transpositions=(0, 0, 2, -1), harmony=4 if second else None)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), ROOT, MODE, PROG,
                  start, bars, 95 if not second else 108,
                  step_bars=2 if not second else 1)
    c.flowing_arp(sc, CH_LIGHTS, ROOT + 12, MODE, PROG, start, bars, 4.0,
                  0.25 if second else 0.5, 72 if not second else 84,
                  lo=64, hi=102)
    c.motif_sequence(sc, CH_GRAVITY, ROOT + 12, MODE, material.GRAVITY_HOOK,
                     start + (32.0 if not second else 0.0),
                     max(1, (bars - (8 if not second else 0)) // 2), 8.0,
                     57 if not second else 70, 72 if not second else 93,
                     transpositions=(0, -1, 0, 2), octave=-1)
    en.cc_curve(sc, CH_GRAVITY, 70,
                [(start, 35 if not second else 62),
                 (start + bars * 2.5, 96 if not second else 116),
                 (start + bars * 4.0, 76)], step=1.0)
    for beat in range(int(start + 8.0), int(start + bars * 4.0), 16):
        c.guitar_bend_phrase(sc, CH_GUITAR, ROOT, MODE, float(beat),
                             (0, 4, 7, 9, 11, 14, 11, 9),
                             86 if not second else 95, octave=1)
    for bar in range(0, bars, 2 if second else 4):
        degree = PROG[bar % 4]
        sc.note(CH_HIT, en.pitch(ROOT, MODE, degree), start + 4.0 * bar,
                0.85, 104 if not second else 116, jt=0, jv=3)
    if second:
        c.chord_cycle(sc, CH_ORGAN, ROOT - 12, MODE, PROG, start, bars, 4.0,
                      61, size=4, lo=34, hi=78, gate=0.99)
        en.cc_curve(sc, CH_ORGAN, 11,
                    [(start, 70), (start + 64.0, 104),
                     (start + bars * 4.0, 118)], step=0.5)
    c.sidechain_beds(sc, (CH_PAD, CH_STRINGS, CH_GRAVITY), start, bars * 4.0,
                     low=57 if second else 66, high=118)


def _quote_stack(sc: en.Score, start: float, root: int, entries: int,
                 lifted: bool = False) -> None:
    """State all four album hooks in every eight-beat window."""
    for i in range(entries):
        beat = start + 8.0 * i
        trans = (0, 0, 2, -1)[i % 4]
        c.motif(sc, CH_NUMBER, root + 12, MODE, material.NUMBER_HOOK,
                beat, 108 + min(10, i), transpose=trans,
                harmony=4 if lifted or i >= entries // 2 else None)
        c.motif(sc, CH_GUITAR, root, MODE, material.RUNWAY_HOOK,
                beat, 94 + min(12, i), transpose=-1 if i % 3 == 1 else 0,
                octave=1)
        c.motif(sc, CH_GRAVITY, root, MODE, material.GRAVITY_HOOK,
                beat, 76 + min(10, i), transpose=0, octave=0)
        c.motif(sc, CH_LIGHTS, root + 12, MODE, material.LIGHTS_HOOK,
                beat, 83 + min(10, i), transpose=1 if i % 4 == 2 else 0,
                octave=0)
        # One real bend per window, released before the next quotation.
        en.bend_curve(sc, CH_GUITAR,
                      [(beat, 0.0), (beat + 5.5, 0.0),
                       (beat + 6.25, 1.0), (beat + 7.5, 0.0)],
                      step=0.125)


def _maximal_stack(sc: en.Score, start: float, bars: int, root: int,
                   lifted: bool) -> None:
    c.chord_cycle(sc, CH_PAD, root, MODE, PROG, start, bars, 4.0, 78,
                  lo=root + 0, hi=root + 34, gate=0.99)
    c.chord_cycle(sc, CH_STRINGS, root + 12, MODE, PROG, start, bars, 4.0, 70,
                  lo=root + 16, hi=root + 50, gate=0.99)
    _piano_pulse(sc, start, bars, root, 85, dense=True)
    c.bass_pattern(sc, CH_BASS, root, MODE, PROG, start, bars, 4.0, 101,
                   syncopated=True)
    c.four_floor(sc, start, bars, 106 if lifted else 104,
                 hats16=True, tambourine=True, crash_every=2 if lifted else 4)
    c.brass_stabs(sc, (CH_BRASS_L, CH_BRASS_R), root, MODE, PROG,
                  start, bars, 113 if lifted else 111, step_bars=1)
    c.chord_cycle(sc, CH_ORGAN, root - 12, MODE, PROG, start, bars, 4.0,
                  70 if not lifted else 75, size=4, lo=root - 18, hi=root + 27,
                  gate=0.99)
    c.flowing_arp(sc, CH_LIGHTS, root + 12, MODE, PROG, start, bars, 4.0,
                  0.25, 87 if lifted else 84, lo=root + 12, hi=root + 50)
    for bar in range(bars):
        degree = PROG[bar % 4]
        sc.note(CH_HIT, en.pitch(root, MODE, degree), start + 4.0 * bar,
                0.9, 119 if lifted else 116, jt=0, jv=2)
        c.melodic_fill(sc, CH_TOMS, start + 4.0 * bar,
                       24 if lifted else 20, 96 if lifted else 91, low=43)
    c.sidechain_beds(sc, (CH_PAD, CH_STRINGS, CH_GRAVITY), start, bars * 4.0,
                     low=54, high=121)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (CH_ORBIT, "bright-matter steel orbit", 114, 97, 64, 43, 14, 16, 1),
        (CH_PIANO, "particle electric piano", 4, 96, 64, 38, 20, 13, 0),
        (CH_PAD, "matter field pad", 91, 92, 64, 69, 31, 8, 0),
        (CH_BASS, "bright-matter bass", 39, 106, 64, 23, 4, 0, 0),
        (CH_NUMBER, "six-five-two-one lead", 81, 101, 64, 40, 16, 19, 0),
        (CH_GUITAR, "runway guitar", 30, 99, 64, 38, 12, 20, 0),
        (CH_STRINGS, "gravity strings", 49, 90, 64, 72, 27, 5, 0),
        (CH_GRAVITY, "gravity choir", 52, 87, 64, 78, 31, 10, 0),
        (CH_LIGHTS, "late-light harp", 46, 93, 64, 67, 16, 24, 0),
        (CH_KIT, "everything kit", None, 112, 64, 25, 0, 0, 0),
        (CH_BRASS_L, "finale brass left", 61, 97, 20, 45, 9, 4, 0),
        (CH_BRASS_R, "finale brass right", 61, 97, 108, 45, 9, 4, 0),
        (CH_ORGAN, "full-mass cathedral organ", 19, 94, 64, 78, 26, 5, 0),
        (CH_TOMS, "bright-matter melodic toms", 117, 101, 64, 32, 8, 4, 1),
        (CH_HIT, "everything orchestra hit", 55, 101, 64, 44, 6, 4, 0),
        (CH_RISER, "matter reverse cymbal", 119, 92, 64, 64, 8, 0, 1),
    ])
    sc.program(CH_KIT, 1, 0.0)

    c.section(sc, 0.0, "I. Particles", meter=(4, 4))
    c.section(sc, 64.0, "II. First Ascent")
    c.section(sc, 160.0, "III. Drop One")
    c.section(sc, 288.0, "IV. Vacuum", bpm=64.0)
    c.section(sc, 328.0, "V. Second Ascent", bpm=128.0)
    c.section(sc, 424.0, "VI. Drop Two")
    c.section(sc, 552.0, "VII. Everything at Once")
    c.section(sc, 632.0, "VIII. Bright Matter", bpm=132.0)
    c.section(sc, 664.0, "IX. Afterglow", bpm=112.0)

    c.orbit_riff(sc, CH_ORBIT, ROOT + 12, MODE, 0.0, 288.0, 56,
                 octave_lift_at=160.0, period=32.0)
    c.orbit_riff(sc, CH_ORBIT, ROOT + 12, MODE, 328.0, 664.0, 72,
                 octave_lift_at=424.0, period=32.0)

    c.chord_cycle(sc, CH_PAD, ROOT, MODE, PROG, INTRO[0], 16, 4.0, 41,
                  lo=52, hi=83, gate=0.99)
    c.flowing_arp(sc, CH_PIANO, ROOT, MODE, PROG, 0.0, 16, 4.0,
                  0.5, 48, lo=57, hi=91)
    c.bass_pattern(sc, CH_BASS, ROOT, MODE, PROG, 32.0, 8, 4.0, 50,
                   active=False)
    c.motif_sequence(sc, CH_NUMBER, ROOT + 12, MODE, material.NUMBER_HOOK,
                     32.0, 4, 8.0, 45, 62,
                     transpositions=(0, -1, 0, 2))

    _build(sc, BUILD1[0], 24, second=False)
    _drop(sc, DROP1[0], 32, second=False)

    sc.hit(49, BRIDGE[0], 76, 1.8)
    c.chord_cycle(sc, CH_STRINGS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 10, 4.0, 42, lo=69, hi=101, gate=0.99)
    c.flowing_arp(sc, CH_LIGHTS, ROOT + 12, MODE, (5, 1, 0, 4),
                  BRIDGE[0], 10, 4.0, 0.5, 48, lo=64, hi=101)
    c.motif_sequence(sc, CH_NUMBER, ROOT + 12, MODE, material.NUMBER_HOOK,
                     BRIDGE[0], 5, 8.0, 41, 56,
                     transpositions=(0, -1, 1, 0))
    c.motif_sequence(sc, CH_GRAVITY, ROOT, MODE, material.GRAVITY_HOOK,
                     BRIDGE[0], 5, 8.0, 38, 52,
                     transpositions=(0, 1, -1, 0))
    en.cc_curve(sc, CH_GRAVITY, 70,
                [(288.0, 20), (308.0, 54), (328.0, 72)], step=1.0)
    c.riser(sc, CH_RISER, 320.0, 8.0, 86)

    _build(sc, BUILD2[0], 24, second=True)
    _drop(sc, DROP2[0], 32, second=True)

    _maximal_stack(sc, STACK[0], 20, ROOT, lifted=False)
    _quote_stack(sc, STACK[0], ROOT, 10, lifted=False)
    en.cc_curve(sc, CH_ORGAN, 11,
                [(552.0, 92), (584.0, 108), (616.0, 122), (632.0, 127)],
                step=0.5)
    en.cc_curve(sc, CH_ORGAN, 1,
                [(552.0, 22), (600.0, 70), (632.0, 96)], step=1.0)

    lift_root = ROOT + 2
    _maximal_stack(sc, LIFT[0], 8, lift_root, lifted=True)
    _quote_stack(sc, LIFT[0], lift_root, 4, lifted=True)
    en.cc_curve(sc, CH_ORGAN, 11,
                [(632.0, 127), (660.0, 127), (664.0, 82)], step=0.5)
    en.cc_curve(sc, CH_ORGAN, 1,
                [(632.0, 96), (656.0, 112), (664.0, 0)], step=1.0)
    sc.note(CH_NUMBER, 97, 660.0, 3.6, 124, jt=0, jv=1)

    c.chord_cycle(sc, CH_STRINGS, lift_root + 12, MODE, (0, 3, 0),
                  OUTRO[0], 6, 4.0, 48, lo=70, hi=103, gate=0.99)
    c.flowing_arp(sc, CH_LIGHTS, lift_root + 12, MODE, (0, 3, 0),
                  OUTRO[0], 6, 4.0, 0.5, 50, lo=66, hi=103)
    c.motif(sc, CH_NUMBER, lift_root + 12, MODE, material.NUMBER_HOOK,
            OUTRO[0], 57, stretch=2.0)
    sc.note(CH_ORGAN, lift_root - 24, OUTRO[0], 18.0, 45, jt=0, jv=2)
    en.cc_curve(sc, CH_ORGAN, 11, [(664.0, 82), (680.0, 28), (688.0, 0)], 0.5)
    sc.note(CH_HIT, lift_root, 687.0, 0.8, 111, jt=0, jv=2)


def oracles(sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    results.append(("6521_finale_bass",
                    c.progression_root_failures(sc, CH_BASS, ROOT, MODE, PROG,
                                                DROP1[0], 32)))

    # Every eight-beat finale window must contain all four earlier hooks.
    fails: list[str] = []
    for index in range(10):
        start = STACK[0] + 8.0 * index
        active = {ch for ch in (CH_NUMBER, CH_GUITAR, CH_GRAVITY, CH_LIGHTS)
                  if c.note_count(sc, start, start + 8.0, {ch}) > 0}
        if len(active) != 4:
            fails.append(f"stack window {index} has hook channels {sorted(active)}")
    results.append(("four_hooks_simultaneous", fails[:4]))

    # First statement of each layer must carry the expected pitch set, not generic filler.
    expected = {
        CH_NUMBER: set(c.degrees_to_pitches(ROOT + 12, MODE,
                                            tuple(d for d, _o, _dur in material.NUMBER_HOOK))),
        CH_GUITAR: set(c.degrees_to_pitches(ROOT, MODE,
                                           tuple(d for d, _o, _dur in material.RUNWAY_HOOK), 1)),
        CH_GRAVITY: set(c.degrees_to_pitches(ROOT, MODE,
                                            tuple(d for d, _o, _dur in material.GRAVITY_HOOK))),
        CH_LIGHTS: set(c.degrees_to_pitches(ROOT + 12, MODE,
                                           tuple(d for d, _o, _dur in material.LIGHTS_HOOK))),
    }
    fails = []
    for ch, wanted in expected.items():
        got = set(c.pitches_at(sc, ch, STACK[0], STACK[0] + 8.0))
        if len(got & wanted) < max(4, len(wanted) // 2):
            fails.append(f"channel {ch} does not state its recalled hook ({len(got & wanted)} matches)")
    results.append(("hook_identity_survives_recombination", fails))

    maxima, minima = c.full_circle_extrema(c.cc_lane(sc, CH_ORBIT, 10))
    results.append(("album_finale_full_circle", [] if min(maxima, minima) >= 14 else [
        f"orbit has {maxima} peaks / {minima} troughs, want >= 14"
    ]))

    organ_lane = c.cc_lane(sc, CH_ORGAN, 11)
    fails = []
    if not organ_lane or c.peak_cc(sc, CH_ORGAN, 11) < 127:
        fails.append("organ never reaches authored full swell")
    if c.note_count(sc, STACK[0], LIFT[1], {CH_ORGAN}) < 100:
        fails.append("organ is not a sustained finale layer")
    results.append(("organ_reed_drive_crowns_finale", fails))

    d1 = c.velocity_sum(sc, *DROP1)
    d2 = c.velocity_sum(sc, *DROP2)
    stack_mass = c.velocity_sum(sc, *STACK)
    fails = []
    if d2 <= d1 * 1.10:
        fails.append(f"drop two {d2} <= 1.10 x drop one {d1}")
    if stack_mass / (STACK[1] - STACK[0]) <= d2 / (DROP2[1] - DROP2[0]) * 1.10:
        fails.append("everything-at-once stack is not the densest section per beat")
    results.append(("three_stage_energy_arc", fails))

    bridge_drums = c.note_count(sc, *BRIDGE, {CH_KIT})
    results.append(("vacuum_is_silent_underneath", [] if bridge_drums <= 2 else [
        f"vacuum contains {bridge_drums} drum notes"
    ]))

    lifted = c.pitches_at(sc, CH_NUMBER, LIFT[0], LIFT[1])
    results.append(("final_key_lift", [] if lifted and max(lifted) >= 93 else [
        "lifted final hook never reaches its high summit"
    ]))

    return results
