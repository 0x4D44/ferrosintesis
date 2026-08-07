#!/usr/bin/env python3
"""The five deterministic compositions in *Every Voice Forward*.

The first four pieces each take responsibility for one contiguous quarter of the
General MIDI program map.  Every program is given a real musical role for at least
one section; the fifth piece then recombines the four hooks using a hand-picked
Ferrosintesis ensemble and its non-basic performance controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Sequence

import engine as en
import material as mat


# ---------------------------------------------------------------------------
# Shared arrangement machinery


def _opening_state(sc: en.Score, sharps: int, tempo: float, title: str) -> None:
    sc.gm_reset(0.0)
    sc.gs_reset(0.02)
    sc.xg_reset(0.04)
    sc.xg_hall1(0.06)
    sc.xg_chorus1(0.08)
    sc.timesig(0.0, 4, 4)
    sc.keysig(0.0, sharps, False)
    if abs(sc.initial_tempo - tempo) > 1e-9:
        sc.tempo(0.0, tempo)
    sc.marker(0.0, "00 · Wake")
    sc.lyric(0.0, f"Instrumental listening guide — {title}")
    sc.channel(9, "Ferrosintesis drums", program=None, volume=108, pan=64, expression=127,
               reverb=38, chorus=0, echo=0, beat=0.125)


def _finish(sc: en.Score, beat: float, channels: Sequence[int]) -> None:
    for ch in channels:
        sc.reset_controls(ch, beat)
        sc.all_notes_off(ch, beat + 0.03)
        sc.reset_all_controllers(ch, beat + 0.06)
        sc.all_sound_off(ch, beat + 1.5)
    sc.all_notes_off(9, beat + 0.03)
    sc.reset_all_controllers(9, beat + 0.06)
    sc.last_beat = max(sc.last_beat, beat + 2.0)


def _showcase_channels(sc: en.Score, programs: Sequence[int], beat: float, prefix: str,
                       volumes: Sequence[int] | None = None) -> list[int]:
    if len(programs) != 8:
        raise ValueError("family showcase expects exactly eight programs")
    channels = list(range(8))
    pans = (26, 102, 42, 86, 18, 110, 54, 74)
    vols = volumes or (98, 91, 88, 88, 86, 94, 85, 87)
    for ch, program, pan, volume in zip(channels, programs, pans, vols):
        if ch not in sc.events:
            sc.channel(ch, f"{prefix} {ch + 1}", program=program, volume=volume, pan=pan,
                       expression=120, reverb=44, chorus=12, echo=0, beat=beat)
        else:
            sc.set_patch(ch, program, beat)
            sc.cc(ch, 7, volume, beat + 0.02)
            sc.cc(ch, 10, pan, beat + 0.025)
            sc.cc(ch, 11, 120, beat + 0.03)
            sc.cc(ch, 91, 44, beat + 0.035)
            sc.cc(ch, 93, 12, beat + 0.04)
            sc.cc(ch, 94, 0, beat + 0.045)
        sc.annotate("family_patch", beat, (prefix, ch, program, en.GM_PROGRAMS[program]))
    return channels


def _chord(root: int, semitone: int, quality: str, low: int, high: int,
           inversion: int = 0, size: int = 4, spread: bool = False) -> list[int]:
    return mat.voiced(mat.chord_for_semitone(root, semitone, quality, size), low, high,
                      inversion=inversion, spread=spread)


def _qualities_for(progression: Sequence[int]) -> tuple[str, ...]:
    # Works for the suite's diatonic progressions: 0,5,7 are major; 2/4/9 minor.
    return tuple("minor" if degree in (2, 4, 9, 11) else "major" for degree in progression)


def _theme_every_four_bars(sc: en.Score, ch: int, theme: mat.Theme, root: int, start: float,
                           bars: int, low: int, high: int, velocity: int, progression: Sequence[int],
                           mode: str = "major", tag: str | None = None) -> None:
    for bar in range(0, bars, 4):
        trans = progression[(bar // 4) % len(progression)]
        mat.emit_theme(sc, ch, theme, root + trans, mode, start + bar * 4, velocity,
                       low, high, repeats=2, tag=tag or theme.name)


def _chord_pulses(sc: en.Score, ch: int, root: int, start: float, bars: int,
                  progression: Sequence[int], velocity: int, low: int, high: int,
                  gate: float = 0.72, offbeat: bool = False, spread: bool = False) -> None:
    qualities = _qualities_for(progression)
    for bar in range(bars):
        p = progression[bar % len(progression)]
        quality = qualities[bar % len(qualities)]
        notes = _chord(root, p, quality, low, high, inversion=bar % 3, spread=spread)
        positions = (0.5, 1.5, 2.5, 3.5) if offbeat else (0.0, 1.0, 2.0, 3.0)
        for index, pos in enumerate(positions):
            en.strum(sc, ch, notes, start + bar * 4 + pos, gate,
                     velocity + (7 if index == 0 else 0), direction=1 if index % 2 == 0 else -1,
                     spread=0.012)


def _long_pads(sc: en.Score, ch: int, root: int, start: float, bars: int,
               progression: Sequence[int], velocity: int, low: int, high: int,
               bars_per_chord: int = 1, spread: bool = True) -> None:
    qualities = _qualities_for(progression)
    for bar in range(0, bars, bars_per_chord):
        index = (bar // bars_per_chord) % len(progression)
        notes = _chord(root, progression[index], qualities[index], low, high,
                       inversion=index % 3, size=5, spread=spread)
        en.pad(sc, ch, notes, start + bar * 4, bars_per_chord * 4 - 0.12, velocity)


def _sparkle(sc: en.Score, ch: int, root: int, start: float, bars: int,
             progression: Sequence[int], velocity: int, low: int, high: int,
             step: float = 0.5) -> None:
    qualities = _qualities_for(progression)
    for bar in range(bars):
        index = bar % len(progression)
        notes = _chord(root, progression[index], qualities[index], low, high,
                       inversion=bar % 2, size=4)
        en.arpeggio(sc, ch, notes, start + bar * 4, 4.0, step, velocity,
                    order=(0, 2, 1, 3, 2, 1, 3, 2), octave_cycle=(0, 0, 1, 0))


def _root_ostinato(sc: en.Score, ch: int, root: int, start: float, bars: int,
                   progression: Sequence[int], velocity: int, register: int = 0,
                   syncopated: bool = True) -> None:
    qualities = _qualities_for(progression)
    for bar in range(bars):
        p = progression[bar % len(progression)]
        base = root + p + register * 12
        pattern = ((0.0, 0, 0.72), (1.5, 7, 0.38), (2.0, 12, 0.72), (3.25, 7, 0.44)) \
            if syncopated else ((0.0, 0, 0.8), (1.0, 7, 0.8), (2.0, 12, 0.8), (3.0, 7, 0.8))
        if qualities[bar % len(qualities)] == "minor":
            pattern = tuple((off, interval if interval != 12 else 12, dur) for off, interval, dur in pattern)
        for off, interval, duration in pattern:
            sc.note(ch, en.fit_range(base + interval, 28, 62), start + bar * 4 + off,
                    duration, velocity, jt=1, jv=3)


def _riser(sc: en.Score, ch: int, start: float, duration: float, low_note: int,
           high_note: int, velocity: int = 78) -> None:
    steps = int(duration / 0.5)
    for index in range(steps):
        t = index / max(1, steps - 1)
        note = round(en.lerp(low_note, high_note, t))
        sc.note(ch, note, start + index * 0.5, 0.42, velocity + int(t * 24), jt=1, jv=2)


def _section_drums(sc: en.Score, start: float, bars: int, kind: str, energy: float) -> None:
    if kind == "four":
        en.four_on_floor(sc, start, bars, energy=energy, hats=True, claps=True, ride=energy > 0.9)
    elif kind == "break":
        en.breakbeat(sc, start, bars, energy=energy)
    elif kind == "half":
        for bar in range(bars):
            b = start + bar * 4
            sc.hit(36, b, int(94 + 20 * energy))
            sc.hit(38, b + 2, int(96 + 20 * energy))
            for i in range(8):
                sc.hit(42 if i != 7 else 46, b + i * 0.5, int(54 + (i % 2) * 14 + energy * 8))
            if bar % 4 == 3:
                sc.hit(49, b + 3.75, int(102 + energy * 12))
    else:
        raise ValueError(kind)


# ---------------------------------------------------------------------------
# Track 1 — programs 0..31


def build_daybreak_relay(sc: en.Score) -> None:
    _opening_state(sc, 0, 132.0, sc.title)
    root = 48  # C3
    progression = mat.UPWARD
    channels = _showcase_channels(sc, tuple(range(0, 8)), 0.125, "Piano relay")

    sc.marker(4, "I · Eight Keys, One Sunrise")
    sc.cc(0, 64, 112, 3.9)       # sustain
    sc.cc(1, 66, 127, 3.9)       # sostenuto
    sc.cc(3, 67, 127, 3.9)       # una corda / soft pedal
    sc.cc(4, 93, 42, 3.9)
    _section_drums(sc, 4, 32, "break", 0.65)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 12, 4, 32, 60, 88, 91, progression, tag="A-piano")
    _chord_pulses(sc, 1, root + 12, 4, 32, progression, 62, 52, 80, gate=0.78)
    _root_ostinato(sc, 2, root, 4, 32, progression, 73, register=0, syncopated=False)
    _chord_pulses(sc, 3, root + 12, 4, 32, progression, 57, 54, 84, gate=0.35, offbeat=True)
    _sparkle(sc, 4, root + 12, 4, 32, progression, 66, 60, 96, step=0.5)
    _root_ostinato(sc, 5, root - 12, 4, 32, progression, 68, register=0)
    _sparkle(sc, 6, root + 24, 4, 32, progression, 54, 65, 102, step=0.25)
    _chord_pulses(sc, 7, root + 12, 4, 32, progression, 59, 55, 88, gate=0.28, offbeat=True)
    en.cc_curve(sc, 0, 64, [(4, 112), (68, 96), (124, 0)], step=4)
    en.cc_curve(sc, 3, 67, [(4, 127), (52, 90), (100, 0), (124, 0)], step=4)
    sc.cc(1, 66, 0, 124)

    # Chromatic percussion — the hook becomes light itself.
    phase = 132
    _showcase_channels(sc, tuple(range(8, 16)), phase, "Mallet relay",
                       volumes=(86, 82, 78, 86, 94, 82, 81, 88))
    sc.marker(phase, "II · Light Learns to Bounce")
    _section_drums(sc, phase, 32, "four", 0.78)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 24, phase, 32, 72, 102, 83, progression, tag="A-celesta")
    _sparkle(sc, 1, root + 24, phase, 32, progression, 66, 76, 108, step=1.0)
    _theme_every_four_bars(sc, 2, mat.DAYBREAK, root + 24, phase + 8, 30, 72, 100, 66,
                           mat.SECOND_WIND, tag="A-music-box")
    _long_pads(sc, 3, root + 12, phase, 32, progression, 62, 60, 90, bars_per_chord=2)
    _root_ostinato(sc, 4, root - 12, phase, 32, progression, 84, register=0)
    _chord_pulses(sc, 5, root + 12, phase, 32, progression, 65, 58, 92, gate=0.18, offbeat=True)
    for bar in range(32):
        if bar % 4 in (0, 3):
            notes = _chord(root + 24, progression[bar % 4], _qualities_for(progression)[bar % 4], 72, 108,
                           inversion=bar % 2, size=3)
            en.strum(sc, 6, notes, phase + bar * 4, 2.4, 78, spread=0.08)
    _sparkle(sc, 7, root + 12, phase, 32, progression, 68, 60, 96, step=0.25)
    en.autopan(sc, 1, phase, 128, lo=22, hi=106, period=16)
    en.autopan(sc, 6, phase, 128, lo=100, hi=28, period=24, phase_offset=0.25)
    sc.cc(3, 1, 96, phase)

    # Organs and free reeds — a genuine swell, not just a patch list.
    phase = 260
    _showcase_channels(sc, tuple(range(16, 24)), phase, "Air relay",
                       volumes=(90, 86, 92, 88, 78, 84, 78, 84))
    sc.marker(phase, "III · The Air Starts Singing")
    _section_drums(sc, phase, 32, "half", 0.82)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 12, phase, 32, 60, 91, 88, progression, tag="A-drawbar")
    _chord_pulses(sc, 1, root + 12, phase, 32, progression, 58, 53, 84, gate=0.55)
    _chord_pulses(sc, 2, root + 12, phase, 32, progression, 69, 50, 82, gate=0.32, offbeat=True)
    _long_pads(sc, 3, root, phase, 32, progression, 69, 36, 79, bars_per_chord=2, spread=True)
    _root_ostinato(sc, 4, root - 12, phase, 32, progression, 65, register=0, syncopated=False)
    _chord_pulses(sc, 5, root + 12, phase, 32, progression, 64, 52, 86, gate=0.72, offbeat=True)
    _theme_every_four_bars(sc, 6, mat.DAYBREAK, root + 12, phase + 8, 30, 60, 88, 75,
                           mat.SECOND_WIND, tag="A-harmonica")
    _chord_pulses(sc, 7, root + 12, phase, 32, progression, 62, 52, 87, gate=0.48, offbeat=True)
    en.cc_curve(sc, 0, 1, [(phase, 8), (phase + 48, 48), (phase + 96, 110), (phase + 127, 18)], step=1)
    en.cc_curve(sc, 2, 1, [(phase, 0), (phase + 64, 127), (phase + 127, 32)], step=1)
    en.cc_curve(sc, 3, 11, [(phase, 44), (phase + 96, 119), (phase + 127, 62)], step=1)
    en.cc_curve(sc, 6, 2, [(phase, 70), (phase + 64, 118), (phase + 127, 86)], step=2)
    en.aftertouch_curve(sc, 6, [(phase, 0), (phase + 80, 58), (phase + 127, 0)], step=1)

    # Guitars — the final relay becomes a bright rock launch.
    phase = 388
    _showcase_channels(sc, tuple(range(24, 32)), phase, "Guitar relay",
                       volumes=(88, 90, 82, 86, 84, 88, 82, 78))
    sc.marker(phase, "IV · Strings Catch Fire")
    sc.tempo(phase, 136)
    _section_drums(sc, phase, 32, "four", 1.0)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 12, phase, 32, 58, 88, 88, progression, tag="A-nylon")
    _sparkle(sc, 1, root + 12, phase, 32, progression, 67, 55, 91, step=0.5)
    _chord_pulses(sc, 2, root + 12, phase, 32, progression, 62, 52, 84, gate=0.62, offbeat=True)
    _chord_pulses(sc, 3, root + 12, phase, 32, progression, 66, 52, 86, gate=0.46, offbeat=True)
    _root_ostinato(sc, 4, root - 12, phase, 32, progression, 77, register=0)
    for bar in range(32):
        p = progression[bar % 4]
        power = _chord(root, p, "power", 40, 76, inversion=0, size=4)
        en.strum(sc, 5, power, phase + bar * 4, 1.75, 75 + (10 if bar >= 16 else 0), spread=0.018)
        en.strum(sc, 5, power, phase + bar * 4 + 2, 1.55, 70 + (10 if bar >= 16 else 0), direction=-1, spread=0.018)
    _theme_every_four_bars(sc, 6, mat.DAYBREAK, root + 24, phase + 16, 28, 67, 100, 87,
                           mat.SECOND_WIND, tag="A-distortion")
    _sparkle(sc, 7, root + 24, phase, 32, progression, 58, 72, 108, step=1.0)
    sc.bend_range(6, 12, phase)
    sc.cc(6, 68, 127, phase)
    sc.cc(6, 5, 74, phase)
    sc.cc(6, 65, 127, phase)
    sc.xg_amp_sim(6, drive=74, dry_wet=94, beat=phase + 0.1)
    for bar in range(16, 32, 4):
        b = phase + bar * 4 + 12
        note = en.fit_range(root + 36 + progression[(bar // 4) % 4], 67, 103)
        sc.note(6, note, b, 3.6, 104, jt=0, jv=1)
        en.bend_curve(sc, 6, [(b, -2), (b + 0.5, 0), (b + 2.5, 2.5), (b + 3.4, 0)],
                      step=0.125, range_semitones=12)
    en.cc_curve(sc, 4, 74, [(phase, 118), (phase + 48, 58), (phase + 96, 122), (phase + 127, 84)], step=0.5)
    en.cc_curve(sc, 4, 71, [(phase, 36), (phase + 64, 96), (phase + 127, 44)], step=1)
    sc.cc(4, 68, 127, phase)
    sc.marker(452, "V · Relay Acceleration")
    sc.marker(484, "VI · Every String Upward")
    sc.tempo(508, 128)
    sc.marker(512, "VII · Sun on the Last Chord")
    final_notes = _chord(root + 12, 0, "major", 55, 100, inversion=1, size=5, spread=True)
    for ch in channels:
        en.pad(sc, ch, [en.fit_range(n + (ch % 3) * 12, 48, 108) for n in final_notes], 512, 4.0,
               68 + ch * 3)
    sc.hit(49, 512, 124, 0.7)
    _finish(sc, 516, channels)


# ---------------------------------------------------------------------------
# Track 2 — programs 32..63


def build_brighter_engines(sc: en.Score) -> None:
    _opening_state(sc, 2, 126.0, sc.title)  # D major
    root = 38  # D2
    progression = mat.WIDE_HORIZON
    channels = _showcase_channels(sc, tuple(range(32, 40)), 0.125, "Bass engines",
                                  volumes=(87, 91, 88, 91, 82, 82, 84, 84))
    sc.marker(4, "I · Eight Engines Under One Road")
    _section_drums(sc, 4, 32, "break", 0.78)
    # A bass orchestra: pairwise hockets keep the low end readable.
    pairs = ((0, 1), (2, 3), (4, 5), (6, 7))
    for block, (left, right) in enumerate(pairs):
        block_start = 4 + block * 32
        for bar in range(8):
            p = progression[(bar + block) % 4]
            base = root + p
            for step, interval in enumerate((0, 7, 12, 7, 3, 7, 12, 14)):
                ch = left if step % 2 == 0 else right
                sc.note(ch, en.fit_range(base + interval, 28, 62), block_start + bar * 4 + step * 0.5,
                        0.38 if step % 2 else 0.44, 76 + (step % 4) * 5 + block * 3, jt=1, jv=3,
                        tag=f"bass pair {block + 1}")
        if block == 1:
            # Fretless slur and portamento.
            sc.bend_range(3, 12, block_start)
            sc.cc(3, 5, 64, block_start)
            sc.cc(3, 65, 127, block_start)
            sc.cc(3, 68, 127, block_start)
            for phrase in range(0, 32, 8):
                b = block_start + phrase + 6
                note = en.fit_range(root + 12 + progression[(phrase // 8) % 4], 40, 68)
                sc.note(3, note, b, 1.8, 93, jt=0, jv=2)
                en.bend_curve(sc, 3, [(b, -1.5), (b + 0.45, 0), (b + 1.3, 1), (b + 1.75, 0)],
                              step=0.125, range_semitones=12)
    en.autopan(sc, 6, 68, 64, lo=34, hi=94, period=8)
    en.autopan(sc, 7, 68, 64, lo=94, hi=34, period=8, phase_offset=0.5)

    # Orchestral solo strings / harp / timpani.
    phase = 132
    _showcase_channels(sc, tuple(range(40, 48)), phase, "Orchestral lift",
                       volumes=(88, 84, 88, 82, 76, 83, 86, 92))
    sc.marker(phase, "II · The Road Becomes a Bow")
    _section_drums(sc, phase, 32, "half", 0.68)
    _theme_every_four_bars(sc, 0, mat.ENGINES, root + 24, phase, 32, 60, 94, 86, progression, tag="B-violin")
    _theme_every_four_bars(sc, 1, mat.ENGINES, root + 12, phase + 8, 30, 54, 86, 72,
                           mat.SECOND_WIND, tag="B-viola")
    _long_pads(sc, 2, root + 12, phase, 32, progression, 67, 45, 78, bars_per_chord=1)
    _root_ostinato(sc, 3, root - 12, phase, 32, progression, 70, register=0, syncopated=False)
    _chord_pulses(sc, 4, root + 12, phase, 32, progression, 59, 52, 86, gate=0.26, offbeat=True)
    _chord_pulses(sc, 5, root + 12, phase, 32, progression, 65, 52, 86, gate=0.25, offbeat=True)
    _sparkle(sc, 6, root + 24, phase, 32, progression, 66, 62, 101, step=0.5)
    for bar in range(32):
        p = progression[bar % 4]
        sc.note(7, en.fit_range(root - 12 + p, 33, 58), phase + bar * 4, 1.4, 88 + (bar % 4) * 4,
                jt=1, jv=3)
        if bar % 4 == 3:
            sc.note(7, en.fit_range(root - 5 + p, 38, 62), phase + bar * 4 + 2.5, 1.2, 98,
                    jt=1, jv=2)
    # A few cents of opposing RPN-1 tuning turns the solo strings into a
    # breathing section without relying solely on chorus.
    for ch, cents in ((0, -7.0), (1, 5.0), (2, -3.0), (4, 8.0)):
        sc.fine_tune(ch, cents, phase + 0.05)
    for ch in (0, 1, 2, 4):
        en.cc_curve(sc, ch, 1, [(phase, 12), (phase + 48, 72), (phase + 96, 116), (phase + 127, 30)], step=1)
        en.cc_curve(sc, ch, 11, [(phase, 68), (phase + 64, 112), (phase + 96, 76), (phase + 127, 108)], step=1)
    # Poly pressure on exposed violin notes.
    for bar in range(4, 32, 4):
        note = mat.theme_notes(mat.ENGINES, root + 24 + progression[(bar // 4) % 4], "major", 60, 94)[4]
        sc.poly_aftertouch(0, note, 48 + bar, phase + bar * 4 + 2.0)
        sc.poly_aftertouch(0, note, 0, phase + bar * 4 + 3.5)

    # Ensembles and voices.
    phase = 260
    _showcase_channels(sc, tuple(range(48, 56)), phase, "Ensemble lift",
                       volumes=(88, 84, 78, 78, 84, 80, 82, 96))
    sc.marker(phase, "III · A Choir Finds the Motor")
    _section_drums(sc, phase, 32, "four", 0.86)
    _long_pads(sc, 0, root + 12, phase, 32, progression, 72, 46, 86, bars_per_chord=1)
    _chord_pulses(sc, 1, root + 12, phase, 32, progression, 60, 50, 86, gate=0.62, offbeat=True)
    _sparkle(sc, 2, root + 24, phase, 32, progression, 60, 65, 103, step=0.5)
    _sparkle(sc, 3, root + 12, phase, 32, progression, 56, 55, 93, step=0.25)
    _theme_every_four_bars(sc, 4, mat.ENGINES, root + 12, phase, 32, 55, 88, 84, progression, tag="B-aah")
    _theme_every_four_bars(sc, 5, mat.ENGINES, root + 12, phase + 4, 31, 55, 88, 75,
                           mat.SECOND_WIND, tag="B-ooh")
    _theme_every_four_bars(sc, 6, mat.ENGINES, root + 24, phase + 8, 30, 67, 101, 72,
                           mat.OPEN_DOOR, tag="B-synth-voice")
    for bar in range(32):
        if bar % 2 == 0:
            chord_notes = _chord(root + 12, progression[bar % 4], _qualities_for(progression)[bar % 4],
                                 52, 88, inversion=bar % 3, size=5)
            en.strum(sc, 7, chord_notes, phase + bar * 4, 0.8, 82 + (10 if bar >= 24 else 0), spread=0.018)
    # Ferrosintesis vowel morph across mm→oo→ah→eh.
    for ch, offset in ((4, 0), (5, 18), (6, 36)):
        en.cc_curve(sc, ch, 70,
                    [(phase, 0 + offset), (phase + 32, 42 + offset // 3),
                     (phase + 72, 84), (phase + 112, 127), (phase + 127, 64)], step=0.5)
        en.aftertouch_curve(sc, ch, [(phase, 0), (phase + 80, 55 + ch * 4), (phase + 127, 0)], step=1)
        sc.cc(ch, 93, 74, phase)
    en.expression_pump(sc, 2, phase + 64, 64, low=62, high=116, beat_step=1)

    # Brass — breath, lip, growl and a full-width final fanfare.
    phase = 388
    _showcase_channels(sc, tuple(range(56, 64)), phase, "Brass lift",
                       volumes=(86, 87, 84, 78, 88, 90, 80, 80))
    sc.marker(phase, "IV · Brass Against the Blue")
    sc.tempo(phase, 130)
    _section_drums(sc, phase, 32, "four", 1.0)
    _theme_every_four_bars(sc, 0, mat.ENGINES, root + 24, phase, 32, 63, 99, 92, progression, tag="B-trumpet")
    _theme_every_four_bars(sc, 1, mat.ENGINES, root + 12, phase + 4, 31, 52, 88, 84,
                           mat.SECOND_WIND, tag="B-trombone")
    _root_ostinato(sc, 2, root - 12, phase, 32, progression, 76, register=0, syncopated=False)
    _chord_pulses(sc, 3, root + 12, phase, 32, progression, 61, 58, 90, gate=0.42, offbeat=True)
    _long_pads(sc, 4, root + 12, phase, 32, progression, 72, 49, 87, bars_per_chord=2)
    _chord_pulses(sc, 5, root + 12, phase, 32, progression, 74, 52, 92, gate=0.72)
    _sparkle(sc, 6, root + 12, phase, 32, progression, 62, 57, 94, step=0.5)
    _sparkle(sc, 7, root + 12, phase, 32, progression, 60, 57, 94, step=0.5)
    for ch in channels:
        en.cc_curve(sc, ch, 2, [(phase, 54), (phase + 64, 112), (phase + 112, 127), (phase + 127, 76)], step=1)
        en.cc_curve(sc, ch, 11, [(phase, 66), (phase + 48, 104), (phase + 96, 119), (phase + 127, 82)], step=1)
        en.aftertouch_curve(sc, ch, [(phase, 0), (phase + 80, 48 + ch * 4), (phase + 120, 88),
                                      (phase + 127, 0)], step=1)
    sc.bend_range(0, 4, phase)
    for bar in range(8, 32, 8):
        b = phase + bar * 4 + 14
        note = en.fit_range(root + 36 + progression[(bar // 8) % 4], 66, 101)
        sc.note(0, note, b, 1.8, 112, jt=0, jv=1)
        en.bend_curve(sc, 0, [(b, -0.8), (b + 0.3, 0), (b + 1.2, 0.5), (b + 1.7, 0)],
                      step=0.1, range_semitones=4)

    # Eight-bar coda picks one voice from each earlier family.
    coda = 516
    coda_programs = (35, 40, 42, 46, 48, 52, 60, 61)
    _showcase_channels(sc, coda_programs, coda, "Engine coda",
                       volumes=(90, 82, 80, 78, 84, 80, 86, 88))
    sc.marker(coda, "V · Every Engine Becomes a Wing")
    _section_drums(sc, coda, 8, "half", 1.0)
    _root_ostinato(sc, 0, root - 12, coda, 8, mat.UPWARD, 82)
    _theme_every_four_bars(sc, 1, mat.ENGINES, root + 24, coda, 8, 62, 97, 90, mat.UPWARD, tag="B-coda")
    _theme_every_four_bars(sc, 2, mat.DAYBREAK, root + 12, coda + 4, 7, 53, 86, 76, mat.UPWARD, tag="A-coda")
    _sparkle(sc, 3, root + 24, coda, 8, mat.UPWARD, 64, 64, 102, step=0.5)
    _long_pads(sc, 4, root + 12, coda, 8, mat.UPWARD, 70, 48, 88, bars_per_chord=1)
    _theme_every_four_bars(sc, 5, mat.ENGINES, root + 12, coda, 8, 56, 88, 78, mat.UPWARD, tag="B-choir-coda")
    _long_pads(sc, 6, root + 12, coda, 8, mat.UPWARD, 72, 50, 90, bars_per_chord=1)
    _chord_pulses(sc, 7, root + 12, coda, 8, mat.UPWARD, 76, 53, 93, gate=0.8)
    sc.marker(544, "VI · Horizon Release")
    sc.tempo(544, 118)
    _finish(sc, 548, channels)


# ---------------------------------------------------------------------------
# Track 3 — programs 64..95


def build_open_sky_signal(sc: en.Score) -> None:
    _opening_state(sc, 4, 136.0, sc.title)  # E major
    root = 40  # E2
    progression = mat.UPWARD
    channels = _showcase_channels(sc, tuple(range(64, 72)), 0.125, "Reed signal",
                                  volumes=(80, 82, 85, 82, 78, 78, 76, 82))
    sc.marker(4, "I · The Reeds Draw a Skyline")
    _section_drums(sc, 4, 32, "break", 0.8)
    # Sax quartet on 0..3; woodwind quartet on 4..7.
    for bar in range(32):
        p = progression[bar % 4]
        quality = _qualities_for(progression)[bar % 4]
        sax = _chord(root + 24, p, quality, 49, 91, inversion=bar % 4, size=4, spread=True)
        wood = _chord(root + 36, p, quality, 60, 103, inversion=(bar + 1) % 3, size=4)
        for ch, note in enumerate(sax):
            rhythm = ((0.0, 1.4), (2.0, 0.7), (3.0, 0.7)) if bar % 2 == 0 else ((0.5, 0.7), (1.5, 0.7), (2.5, 1.2))
            for off, duration in rhythm:
                sc.note(ch, note + (12 if ch == 0 and off == 3.0 else 0), 4 + bar * 4 + off,
                        duration, 70 + ch * 3 + (8 if bar >= 16 else 0), jt=1, jv=2)
        for index, note in enumerate(wood):
            ch = index + 4
            if index == 3:
                # Clarinet carries the hook.
                continue
            sc.note(ch, note, 4 + bar * 4, 3.6, 58 + index * 4, jt=1, jv=2)
    _theme_every_four_bars(sc, 7, mat.OPEN_SKY, root + 24, 4, 32, 58, 94, 82, progression, tag="C-clarinet")
    for ch in channels:
        sc.cc(ch, 2, 72, 4)
        sc.cc(ch, 1, 20, 4)
        sc.cc(ch, 68, 127, 4)
        en.cc_curve(sc, ch, 2, [(4, 62), (52, 92), (100, 120), (131, 74)], step=1)
        en.cc_curve(sc, ch, 1, [(4, 8), (68, 52), (116, 94), (131, 18)], step=2)
    en.aftertouch_curve(sc, 2, [(4, 0), (76, 42), (116, 70), (131, 0)], step=1)
    en.aftertouch_curve(sc, 7, [(4, 0), (92, 58), (131, 0)], step=1)

    # Pipes and blown voices.
    phase = 132
    _showcase_channels(sc, tuple(range(72, 80)), phase, "Pipe signal",
                       volumes=(78, 86, 79, 80, 70, 79, 76, 82))
    sc.marker(phase, "II · Air Above the Buildings")
    _section_drums(sc, phase, 32, "four", 0.84)
    _theme_every_four_bars(sc, 1, mat.OPEN_SKY, root + 36, phase, 32, 68, 105, 88, progression, tag="C-flute")
    _theme_every_four_bars(sc, 0, mat.OPEN_SKY, root + 48, phase + 8, 30, 78, 112, 73,
                           mat.SECOND_WIND, tag="C-piccolo")
    _chord_pulses(sc, 2, root + 24, phase, 32, progression, 54, 62, 94, gate=0.45, offbeat=True)
    _sparkle(sc, 3, root + 24, phase, 32, progression, 57, 63, 99, step=0.5)
    _root_ostinato(sc, 4, root - 12, phase, 32, progression, 58, register=1, syncopated=False)
    _theme_every_four_bars(sc, 5, mat.OPEN_SKY, root + 24, phase + 4, 31, 58, 94, 77,
                           mat.OPEN_DOOR, tag="C-shakuhachi")
    _chord_pulses(sc, 6, root + 24, phase, 32, progression, 62, 66, 100, gate=0.22, offbeat=True)
    _theme_every_four_bars(sc, 7, mat.OPEN_SKY, root + 24, phase + 12, 29, 60, 96, 74,
                           mat.LYDIAN_LIFT, tag="C-ocarina")
    for ch in channels:
        sc.cc(ch, 68, 127, phase)
        en.cc_curve(sc, ch, 2, [(phase, 50), (phase + 40, 92), (phase + 88, 122), (phase + 127, 68)], step=1)
        en.cc_curve(sc, ch, 1, [(phase, 5), (phase + 64, 46), (phase + 112, 86), (phase + 127, 12)], step=2)
    # Breath-note scoops.
    sc.bend_range(5, 4, phase)
    for bar in range(4, 32, 8):
        b = phase + bar * 4
        note = en.fit_range(root + 36 + progression[(bar // 4) % 4], 66, 101)
        sc.note(5, note, b, 3.2, 96, jt=0, jv=2)
        en.bend_curve(sc, 5, [(b, -1.0), (b + 0.55, 0), (b + 2.6, 0.4), (b + 3.1, 0)],
                      step=0.1, range_semitones=4)

    # Synth leads: sixteen bars of 7/8 launch, then a square 4/4 release.
    phase = 260
    _showcase_channels(sc, tuple(range(80, 88)), phase, "Lead signal",
                       volumes=(78, 83, 75, 77, 79, 74, 76, 84))
    sc.marker(phase, "III · Seven Steps Through the Cloud")
    sc.timesig(phase, 7, 8)
    for ch in channels:
        sc.bend_range(ch, 12, phase)
        sc.cc(ch, 5, 54 + ch * 5, phase)
        sc.cc(ch, 65, 127, phase)
        sc.cc(ch, 68, 127, phase)
        sc.cc(ch, 84, 60 + ch, phase)
        sc.cc(ch, 74, 62, phase)
        sc.cc(ch, 71, 58, phase)
        sc.cc(ch, 94, 28 + ch * 4, phase)
    # 16 measures of 7/8 = 56 quarter-note beats.
    for measure in range(16):
        base = phase + measure * 3.5
        p = progression[measure % 4]
        scale = mat.theme_notes(mat.OPEN_SKY, root + 24 + p, "major", 55, 102)
        for step in range(7):
            ch = (step + measure) % 8
            note = scale[(step * 3 + measure) % len(scale)] + (12 if ch in (0, 2, 4) else 0)
            sc.note(ch, en.fit_range(note, 55, 108), base + step * 0.5, 0.42,
                    72 + (step == 0) * 12 + measure // 4 * 3, jt=1, jv=2, tag="C-seven")
        sc.hit(36, base, 104)
        sc.hit(38, base + 1.5, 96)
        sc.hit(38, base + 3.0, 102)
        for e in range(7):
            sc.hit(42 if e < 6 else 46, base + e * 0.5, 55 + (e % 2) * 15)
    return_four = phase + 56
    sc.timesig(return_four, 4, 4)
    sc.marker(return_four, "IV · The Sky Answers in Four")
    _section_drums(sc, return_four, 18, "four", 1.0)
    _theme_every_four_bars(sc, 1, mat.OPEN_SKY, root + 36, return_four, 18, 68, 108, 91, progression, tag="C-saw")
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 24, return_four + 4, 17, 58, 96, 72,
                           mat.SECOND_WIND, tag="A-square-answer")
    _sparkle(sc, 2, root + 24, return_four, 18, progression, 66, 60, 101, step=0.5)
    _chord_pulses(sc, 3, root + 24, return_four, 18, progression, 62, 55, 94, gate=0.28, offbeat=True)
    _chord_pulses(sc, 4, root + 12, return_four, 18, progression, 64, 50, 88, gate=0.42, offbeat=True)
    _theme_every_four_bars(sc, 5, mat.OPEN_SKY, root + 24, return_four + 8, 16, 60, 96, 77,
                           mat.OPEN_DOOR, tag="C-voice-lead")
    _long_pads(sc, 6, root + 24, return_four, 18, progression, 56, 58, 99, bars_per_chord=1)
    _root_ostinato(sc, 7, root - 12, return_four, 18, progression, 73, register=1)
    for ch in channels:
        en.cc_curve(sc, ch, 74, [(return_four, 48), (return_four + 24, 108),
                                  (return_four + 56, 68), (phase + 127, 126)], step=0.5)
        en.cc_curve(sc, ch, 71, [(return_four, 42), (return_four + 48, 96),
                                  (phase + 127, 54)], step=1)
    for phrase in range(0, 72, 16):
        b = return_four + phrase + 12
        ch = (phrase // 16) % 8
        note = en.fit_range(root + 48 + progression[(phrase // 16) % 4], 72, 112)
        sc.note(ch, note, b, 3.5, 108, jt=0, jv=1)
        en.bend_curve(sc, ch, [(b, -3), (b + 0.6, 0), (b + 2.4, 4), (b + 3.3, 0)],
                      step=0.1, range_semitones=12)

    # Pads: a filter-controlled horizon that opens into the final chord.
    phase = 388
    _showcase_channels(sc, tuple(range(88, 96)), phase, "Pad signal",
                       volumes=(77, 82, 76, 80, 76, 72, 78, 82))
    sc.marker(phase, "V · Eight Colours of Horizon")
    _section_drums(sc, phase, 32, "half", 0.88)
    for ch in channels:
        _long_pads(sc, ch, root + 12 + (12 if ch >= 4 else 0), phase, 32, progression,
                   54 + ch * 2, 45 + ch * 2, 96 + min(ch, 4), bars_per_chord=2, spread=True)
        sc.cc(ch, 93, 48 + ch * 7, phase)
        sc.cc(ch, 94, 20 + ch * 8, phase)
        en.cc_curve(sc, ch, 74,
                    [(phase, 24 + ch * 3), (phase + 48, 78 + ch * 3),
                     (phase + 80, 42 + ch * 2), (phase + 116, 127), (phase + 127, 96)], step=0.5)
        en.cc_curve(sc, ch, 71,
                    [(phase, 24), (phase + 64, 84 + ch * 3), (phase + 127, 38)], step=1)
        en.expression_pump(sc, ch, phase + 64, 48, low=62 + ch, high=112, beat_step=1)
        en.autopan(sc, ch, phase, 128, lo=18 + ch * 2, hi=110 - ch * 2,
                   period=16 + ch * 2, phase_offset=ch / 8)
    _theme_every_four_bars(sc, 7, mat.OPEN_SKY, root + 24, phase + 64, 16, 62, 102, 70,
                           progression, tag="C-sweep-pad")
    sc.marker(452, "VI · Filters to Daylight")
    sc.marker(500, "VII · Open-Sky Signal")
    sc.tempo(508, 124)
    final = _chord(root + 24, 0, "major", 55, 110, inversion=2, size=5, spread=True)
    for ch in channels:
        en.pad(sc, ch, [en.fit_range(n + (ch % 2) * 12, 50, 112) for n in final], 512, 4, 64 + ch * 3)
    sc.hit(49, 512, 124, 0.7)
    _finish(sc, 516, channels)


# ---------------------------------------------------------------------------
# Track 4 — programs 96..127 and every GM drum key


def build_world_in_the_chorus(sc: en.Score) -> None:
    _opening_state(sc, 1, 124.0, sc.title)  # G major
    root = 43  # G2
    progression = mat.OPEN_DOOR
    channels = _showcase_channels(sc, tuple(range(96, 104)), 0.125, "Weather voices",
                                  volumes=(72, 76, 70, 77, 73, 69, 72, 75))

    # Six persistent musical anchors keep the effects and SFX chapters musical.
    anchors = {
        8: (25, 86, 38, 48, 0, 96),   # XG mandolin variation
        10: (35, 91, 64, 34, 0, 0),   # fretless bass
        11: (48, 78, 52, 76, 0, 0),   # strings
        12: (80, 76, 78, 55, 0, 0),   # square lead
        13: (89, 77, 50, 68, 0, 0),   # warm pad
        14: (114, 82, 88, 42, 0, 0),  # steel drums
        15: (104, 80, 100, 48, 0, 0), # sitar
    }
    for ch, (program, volume, pan, reverb, bank_msb, bank_lsb) in anchors.items():
        sc.channel(ch, f"World anchor {ch + 1}", program=program, volume=volume, pan=pan,
                   expression=118, reverb=reverb, chorus=30 if ch in (11, 13) else 8,
                   echo=22 if ch in (12, 15) else 0, bank_msb=bank_msb, bank_lsb=bank_lsb,
                   beat=0.125)
    sc.marker(4, "I · Weather with a Pulse")
    _section_drums(sc, 4, 32, "half", 0.62)
    _long_pads(sc, 13, root + 12, 4, 32, progression, 58, 48, 92, bars_per_chord=2)
    _root_ostinato(sc, 10, root - 12, 4, 32, progression, 71)
    # The owner-recorded mandolin variation (GM25 + LSB96) is an actual musical
    # anchor before this channel is repurposed as the second GS rhythm part.
    _chord_pulses(sc, 8, root + 12, 4, 16, progression, 58, 55, 90,
                  gate=0.18, offbeat=True)
    sc.cc(8, 93, 24, 4)
    sc.cc(8, 94, 14, 4)
    _sparkle(sc, 14, root + 12, 4, 32, progression, 62, 58, 94, step=0.5)
    _theme_every_four_bars(sc, 12, mat.WORLD, root + 24, 4, 32, 61, 100, 67, progression, tag="D-square-anchor")
    # Each FX voice gets a foreground gesture and a sustained bed.
    for ch in channels:
        program = 96 + ch
        for block in range(4):
            b = 4 + block * 32 + ch * 0.5
            note = 48 + (program * 5 + block * 7) % 24
            sc.note(ch, note, b, 10.0 if program not in (100, 103) else 4.0,
                    54 + ch * 4 + block * 3, jt=1, jv=2, tag=f"FX {program}")
        sc.cc(ch, 91, 72 + ch * 5, 4)
        sc.cc(ch, 93, 18 + ch * 8, 4)
        sc.cc(ch, 94, 20 + ch * 9, 4)
        en.cc_curve(sc, ch, 74, [(4, 30 + ch * 4), (52, 108), (96, 45 + ch * 4), (131, 124)], step=0.5)
        en.cc_curve(sc, ch, 71, [(4, 28), (76, 92 + ch * 3), (131, 42)], step=1)
        en.autopan(sc, ch, 4, 128, lo=16 + ch * 3, hi=112 - ch * 3, period=18 + ch,
                   phase_offset=ch / 8)

    # Ethnic instruments: eight lines from different traditions share one hook.
    phase = 132
    _showcase_channels(sc, tuple(range(104, 112)), phase, "World voices",
                       volumes=(82, 84, 78, 79, 82, 78, 84, 80))
    sc.marker(phase, "II · The World Joins In")
    _section_drums(sc, phase, 32, "four", 0.88)
    _theme_every_four_bars(sc, 0, mat.WORLD, root + 24, phase, 32, 60, 98, 84, progression, tag="D-sitar")
    _chord_pulses(sc, 1, root + 12, phase, 32, progression, 65, 54, 89, gate=0.25, offbeat=True)
    _theme_every_four_bars(sc, 2, mat.WORLD, root + 24, phase + 4, 31, 62, 99, 73,
                           mat.SECOND_WIND, tag="D-shamisen")
    _sparkle(sc, 3, root + 24, phase, 32, progression, 65, 66, 103, step=0.5)
    _sparkle(sc, 4, root + 12, phase, 32, progression, 68, 57, 95, step=0.5)
    _long_pads(sc, 5, root, phase, 32, progression, 57, 40, 76, bars_per_chord=2)
    _theme_every_four_bars(sc, 6, mat.WORLD, root + 24, phase + 8, 30, 62, 101, 79,
                           mat.LYDIAN_LIFT, tag="D-fiddle")
    _theme_every_four_bars(sc, 7, mat.WORLD, root + 24, phase + 12, 29, 62, 101, 77,
                           mat.OPEN_DOOR, tag="D-shanai")
    for ch in channels:
        sc.cc(ch, 68, 127, phase)
        sc.cc(ch, 1, 24 + ch * 8, phase)
        sc.cc(ch, 2, 76 + ch * 5, phase)
        sc.cc(ch, 93, 18 + ch * 7, phase)
    sc.bend_range(0, 7, phase)
    sc.bend_range(6, 7, phase)
    sc.bend_range(7, 7, phase)
    for bar in range(4, 32, 8):
        for ch, sign in ((0, 1), (6, -1), (7, 1)):
            b = phase + bar * 4 + ch * 0.15
            note = en.fit_range(root + 36 + progression[(bar // 4) % 4] + ch, 62, 104)
            sc.note(ch, note, b, 3.3, 100 - ch * 2, jt=0, jv=1)
            en.bend_curve(sc, ch, [(b, -1.2 * sign), (b + 0.45, 0), (b + 2.5, 1.5 * sign), (b + 3.2, 0)],
                          step=0.1, range_semitones=7)
    # Program 109 default sampled bagpipe, then its CC0=1 modeled alternate as a call-back.
    sc.set_patch(5, 109, phase + 96, bank_msb=1, bank_lsb=0)
    _theme_every_four_bars(sc, 5, mat.WORLD, root + 12, phase + 96, 8, 50, 86, 72,
                           progression, tag="D-bagpipe-alt")

    # Melodic percussion.
    phase = 260
    _showcase_channels(sc, tuple(range(112, 120)), phase, "Percussion voices",
                       volumes=(77, 82, 86, 78, 88, 82, 79, 74))
    sc.marker(phase, "III · Everything That Can Ring")
    _section_drums(sc, phase, 32, "break", 0.94)
    _theme_every_four_bars(sc, 2, mat.WORLD, root + 24, phase, 32, 60, 98, 88, progression, tag="D-steel")
    _sparkle(sc, 0, root + 24, phase, 32, progression, 62, 72, 106, step=1.0)
    _chord_pulses(sc, 1, root + 12, phase, 32, progression, 62, 60, 92, gate=0.24, offbeat=True)
    _chord_pulses(sc, 3, root + 12, phase, 32, progression, 66, 58, 93, gate=0.14, offbeat=True)
    _root_ostinato(sc, 4, root - 12, phase, 32, progression, 81, register=0, syncopated=False)
    _root_ostinato(sc, 5, root - 12, phase, 32, progression, 76, register=1)
    _sparkle(sc, 6, root + 12, phase, 32, progression, 64, 55, 96, step=0.25)
    for bar in range(32):
        if bar % 2 == 1:
            sc.note(7, 60 + (bar % 8), phase + bar * 4 + 3.5, 0.5, 80 + (bar % 4) * 6,
                    jt=1, jv=2)
    for ch in channels:
        en.autopan(sc, ch, phase, 128, lo=18 + ch * 3, hi=110 - ch * 2, period=8 + ch * 1.5,
                   phase_offset=ch / 8)
        sc.cc(ch, 91, 36 + ch * 7, phase)
        sc.cc(ch, 94, 10 + ch * 8, phase)

    # GM sound effects, arranged as scene changes over the persistent anchors.
    phase = 388
    _showcase_channels(sc, tuple(range(120, 128)), phase, "Scene voices",
                       volumes=(64, 58, 65, 60, 66, 68, 72, 58))
    sc.marker(phase, "IV · The World Becomes the Chorus")
    _section_drums(sc, phase, 32, "half", 0.9)
    _root_ostinato(sc, 10, root - 12, phase, 32, progression, 76)
    _long_pads(sc, 11, root + 12, phase, 32, progression, 62, 48, 91, bars_per_chord=2)
    _long_pads(sc, 13, root + 12, phase, 32, progression, 54, 49, 96, bars_per_chord=2)
    _sparkle(sc, 14, root + 12, phase, 32, progression, 62, 58, 95, step=0.5)
    _theme_every_four_bars(sc, 15, mat.WORLD, root + 24, phase, 32, 59, 98, 75, progression, tag="D-sitar-anchor")
    _theme_every_four_bars(sc, 12, mat.DAYBREAK, root + 24, phase + 8, 30, 60, 100, 68,
                           mat.SECOND_WIND, tag="A-world-answer")
    # Four musical gestures per SFX program, with long gaps so each reads as colour.
    sfx_durations = (0.35, 1.0, 5.0, 0.7, 1.2, 4.0, 2.2, 0.5)
    for ch in channels:
        for occurrence in range(4):
            b = phase + occurrence * 28 + ch * 1.5
            note = 48 + (ch * 5 + occurrence * 7) % 28
            sc.note(ch, note, b, sfx_durations[ch], 72 + ch * 4 + occurrence * 3,
                    jt=0, jv=2, tag=f"SFX {120 + ch}")
        sc.cc(ch, 91, 68 + ch * 5, phase)
        sc.cc(ch, 94, 18 + ch * 8, phase)
        en.autopan(sc, ch, phase, 128, lo=20, hi=108, period=12 + ch * 2, phase_offset=ch / 8)

    # Additional GS rhythm part and an every-key percussion parade.
    parade = 516
    sc.marker(parade, "V · Forty-Seven Drums, One Celebration")
    sc.gs_drum_mode(8, True, parade - 0.1, map_number=1)
    sc.cc(8, 7, 92, parade)
    sc.cc(8, 10, 86, parade)
    sc.cc(8, 91, 62, parade)
    en.percussion_parade(sc, parade, ch=9, second_ch=8)
    # Anchors state the hook over the parade.
    _root_ostinato(sc, 10, root - 12, parade, 8, mat.UPWARD, 82)
    _theme_every_four_bars(sc, 12, mat.WORLD, root + 24, parade, 8, 61, 101, 82, mat.UPWARD, tag="D-parade")
    _long_pads(sc, 11, root + 12, parade, 8, mat.UPWARD, 68, 47, 92, bars_per_chord=1)
    _sparkle(sc, 14, root + 12, parade, 8, mat.UPWARD, 70, 60, 96, step=0.5)
    sc.gs_drum_mode(8, False, parade + 32.1)
    sc.marker(548, "VI · One World, Open Hands")
    sc.tempo(548, 112)
    final = _chord(root + 12, 0, "major", 50, 105, inversion=1, size=5, spread=True)
    for ch in (10, 11, 12, 13, 14, 15):
        en.pad(sc, ch, [en.fit_range(n + (ch % 2) * 12, 48, 108) for n in final], 548, 4, 70)
    sc.hit(49, 548, 124, 0.8)
    _finish(sc, 552, tuple(list(channels) + list(anchors)))


# ---------------------------------------------------------------------------
# Track 5 — finale, selected voices and four-theme counterpoint


def build_every_voice_forward(sc: en.Score) -> None:
    _opening_state(sc, 3, 140.0, sc.title)  # A major
    root = 45  # A2
    progression = mat.UPWARD
    # One deliberately chosen voice per melodic channel.  Three patches use
    # Ferrosintesis-specific bank variations.
    patches = {
        0: (0, 0, 0, "Grand piano", 94, 50, 52),
        1: (11, 0, 0, "Vibraphone", 78, 86, 58),
        2: (19, 2, 0, "Cathedral organ", 84, 64, 92),
        3: (25, 0, 96, "Mandolin variation", 87, 36, 42),
        4: (35, 0, 0, "Fretless bass", 92, 64, 34),
        5: (46, 0, 0, "Concert harp", 82, 28, 58),
        6: (48, 0, 0, "String ensemble", 82, 46, 72),
        7: (52, 0, 0, "Choir", 80, 74, 78),
        8: (60, 0, 0, "French horn", 86, 88, 68),
        10: (66, 0, 0, "Tenor sax", 84, 96, 52),
        11: (73, 0, 0, "Flute", 82, 104, 62),
        12: (81, 0, 0, "Saw lead", 78, 82, 44),
        13: (89, 0, 0, "Warm pad", 78, 56, 76),
        14: (104, 0, 0, "Sitar", 78, 106, 48),
        15: (114, 0, 0, "Steel drums", 82, 22, 48),
    }
    melodic = sorted(patches)
    for ch, (program, bank_msb, bank_lsb, name, volume, pan, reverb) in patches.items():
        sc.channel(ch, name, program=program, volume=volume, pan=pan, expression=118,
                   reverb=reverb, chorus=42 if ch in (6, 7, 13) else 12,
                   echo=32 if ch in (1, 12, 14, 15) else 0,
                   bank_msb=bank_msb, bank_lsb=bank_lsb, beat=0.125)
    # Hollow-release XG pad variant cameo is bank LSB 19 on program 99 later.
    sc.annotate("finale_patches", 0.125, patches)

    # Initial controller personality.
    sc.cc(0, 64, 108, 0.2)
    sc.cc(5, 64, 96, 0.2)
    sc.cc(2, 1, 18, 0.2)
    sc.cc(2, 11, 38, 0.2)
    sc.cc(4, 5, 62, 0.2)
    sc.cc(4, 65, 127, 0.2)
    sc.cc(4, 68, 127, 0.2)
    sc.cc(6, 1, 22, 0.2)
    sc.cc(7, 70, 0, 0.2)
    sc.cc(8, 2, 72, 0.2)
    sc.cc(10, 2, 78, 0.2)
    sc.cc(10, 68, 127, 0.2)
    sc.cc(11, 2, 78, 0.2)
    sc.cc(11, 68, 127, 0.2)
    sc.bend_range(12, 12, 0.2)
    sc.cc(12, 5, 68, 0.2)
    sc.cc(12, 65, 127, 0.2)
    sc.cc(12, 68, 127, 0.2)
    sc.cc(12, 84, 72, 0.2)
    sc.cc(13, 74, 36, 0.2)
    sc.cc(13, 71, 52, 0.2)
    sc.cc(14, 68, 127, 0.2)
    sc.xg_amp_sim(12, drive=58, dry_wet=74, beat=0.3)

    # I. Small spark — Daybreak hook.
    sc.marker(4, "I · A Small Spark Chooses Forward")
    _section_drums(sc, 4, 16, "half", 0.48)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 12, 4, 16, 58, 92, 82, progression, tag="A-finale")
    _sparkle(sc, 3, root + 12, 4, 16, progression, 66, 55, 92, step=0.25)
    _root_ostinato(sc, 4, root - 12, 4, 16, progression, 68)
    _long_pads(sc, 13, root + 12, 4, 16, progression, 50, 48, 92, bars_per_chord=2)
    en.autopan(sc, 1, 4, 64, lo=30, hi=98, period=16)

    # II. Engine hook joins.
    phase = 68
    sc.marker(phase, "II · The Road Learns to Lift")
    _section_drums(sc, phase, 16, "break", 0.78)
    _root_ostinato(sc, 4, root - 12, phase, 16, mat.WIDE_HORIZON, 82)
    _theme_every_four_bars(sc, 8, mat.ENGINES, root + 24, phase, 16, 58, 96, 88,
                           mat.WIDE_HORIZON, tag="B-finale")
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 12, phase + 4, 15, 57, 91, 72,
                           mat.SECOND_WIND, tag="A-under-B")
    _long_pads(sc, 6, root + 12, phase, 16, mat.WIDE_HORIZON, 65, 48, 91, bars_per_chord=1)
    _sparkle(sc, 5, root + 24, phase, 16, mat.WIDE_HORIZON, 64, 63, 104, step=0.5)
    en.cc_curve(sc, 8, 2, [(phase, 58), (phase + 40, 112), (phase + 63, 74)], step=1)
    en.aftertouch_curve(sc, 8, [(phase, 0), (phase + 48, 62), (phase + 63, 0)], step=1)

    # III. Open-sky hook.
    phase = 132
    sc.marker(phase, "III · The Air Opens Above Us")
    _section_drums(sc, phase, 16, "four", 0.86)
    _theme_every_four_bars(sc, 11, mat.OPEN_SKY, root + 36, phase, 16, 70, 108, 88,
                           progression, tag="C-finale-flute")
    _theme_every_four_bars(sc, 10, mat.OPEN_SKY, root + 24, phase + 4, 15, 58, 97, 80,
                           mat.OPEN_DOOR, tag="C-finale-sax")
    _root_ostinato(sc, 4, root - 12, phase, 16, progression, 82)
    _chord_pulses(sc, 3, root + 12, phase, 16, progression, 68, 54, 92, gate=0.28, offbeat=True)
    _long_pads(sc, 13, root + 12, phase, 16, progression, 60, 48, 95, bars_per_chord=1)
    for ch in (10, 11):
        en.cc_curve(sc, ch, 2, [(phase, 60), (phase + 40, 118), (phase + 63, 72)], step=1)
        en.cc_curve(sc, ch, 1, [(phase, 8), (phase + 48, 82), (phase + 63, 18)], step=1)
        en.aftertouch_curve(sc, ch, [(phase, 0), (phase + 44, 52), (phase + 63, 0)], step=1)

    # IV. World hook and a real mandolin tremolo.
    phase = 196
    sc.marker(phase, "IV · The World Steps Into the Chorus")
    _section_drums(sc, phase, 16, "four", 0.94)
    _theme_every_four_bars(sc, 14, mat.WORLD, root + 24, phase, 16, 60, 99, 84,
                           progression, tag="D-finale-sitar")
    _theme_every_four_bars(sc, 15, mat.WORLD, root + 24, phase + 4, 15, 62, 100, 78,
                           mat.SECOND_WIND, tag="D-finale-steel")
    _sparkle(sc, 3, root + 12, phase, 16, progression, 70, 55, 94, step=0.25)
    _root_ostinato(sc, 4, root - 12, phase, 16, progression, 84)
    _long_pads(sc, 6, root + 12, phase, 16, progression, 67, 48, 92, bars_per_chord=1)
    en.autopan(sc, 15, phase, 64, lo=20, hi=108, period=8)
    en.autopan(sc, 14, phase, 64, lo=104, hi=24, period=12, phase_offset=0.5)

    # V. Seven-beat construction site — all hooks fragmented.
    phase = 260
    sc.marker(phase, "V · Seven Steps, No Ceiling")
    sc.timesig(phase, 7, 8)
    for measure in range(24):  # 84 quarter-note beats
        base = phase + measure * 3.5
        p = progression[measure % 4]
        fragments = (
            (0, mat.DAYBREAK, root + 12, 58, 92),
            (8, mat.ENGINES, root + 24, 52, 92),
            (11, mat.OPEN_SKY, root + 36, 68, 108),
            (14, mat.WORLD, root + 24, 60, 101),
        )
        for index, (ch, theme, troot, low, high) in enumerate(fragments):
            degree = theme.degrees[(measure + index * 2) % len(theme.degrees)]
            note = en.fit_range(en.pitch(troot + p, "major", degree), low, high)
            sc.note(ch, note, base + index * 0.5, 1.15, 72 + index * 6 + measure // 6 * 3,
                    jt=1, jv=2, tag=f"fragment-{theme.name}")
        for step in range(7):
            sc.note(12, en.fit_range(root + 24 + p + (0, 7, 12, 14, 16, 19, 21)[step], 60, 106),
                    base + step * 0.5, 0.4, 66 + step * 4, jt=1, jv=2, tag="seven-lead")
        sc.hit(36, base, 108)
        sc.hit(38, base + 1.5, 100)
        sc.hit(38, base + 3.0, 106)
        for step in range(7):
            sc.hit(42 if step < 6 else 46, base + step * 0.5, 58 + (step % 2) * 15)
    phase2 = phase + 84
    sc.timesig(phase2, 4, 4)
    sc.marker(phase2, "VI · First Full-Voice Drop")
    _section_drums(sc, phase2, 24, "four", 1.0)
    _root_ostinato(sc, 4, root - 12, phase2, 24, progression, 88)
    _chord_pulses(sc, 3, root + 12, phase2, 24, progression, 72, 53, 94, gate=0.28, offbeat=True)
    _long_pads(sc, 6, root + 12, phase2, 24, progression, 72, 48, 94, bars_per_chord=1)
    _long_pads(sc, 13, root + 12, phase2, 24, progression, 58, 48, 98, bars_per_chord=2)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 24, phase2, 24, 61, 99, 87, progression, tag="A-drop")
    _theme_every_four_bars(sc, 8, mat.ENGINES, root + 24, phase2 + 4, 23, 58, 96, 84,
                           mat.SECOND_WIND, tag="B-drop")
    _theme_every_four_bars(sc, 11, mat.OPEN_SKY, root + 36, phase2 + 8, 22, 70, 108, 82,
                           mat.OPEN_DOOR, tag="C-drop")
    _theme_every_four_bars(sc, 14, mat.WORLD, root + 24, phase2 + 12, 21, 60, 101, 80,
                           mat.LYDIAN_LIFT, tag="D-drop")
    _sparkle(sc, 1, root + 24, phase2, 24, progression, 66, 67, 103, step=0.5)
    _sparkle(sc, 5, root + 24, phase2, 24, progression, 62, 64, 104, step=0.5)
    _theme_every_four_bars(sc, 10, mat.OPEN_SKY, root + 24, phase2 + 16, 20, 58, 97, 76,
                           mat.SECOND_WIND, tag="C-sax-answer")
    _theme_every_four_bars(sc, 15, mat.WORLD, root + 24, phase2 + 20, 19, 62, 100, 74,
                           mat.OPEN_DOOR, tag="D-steel-answer")
    # Controller apex.
    en.cc_curve(sc, 2, 11, [(phase2, 42), (phase2 + 48, 86), (phase2 + 80, 118), (phase2 + 95, 70)], step=0.5)
    en.cc_curve(sc, 2, 1, [(phase2, 12), (phase2 + 72, 104), (phase2 + 95, 28)], step=0.5)
    en.cc_curve(sc, 7, 70, [(phase2, 0), (phase2 + 32, 42), (phase2 + 64, 84),
                             (phase2 + 88, 127), (phase2 + 95, 64)], step=0.5)
    en.aftertouch_curve(sc, 7, [(phase2, 0), (phase2 + 72, 74), (phase2 + 95, 0)], step=1)
    en.cc_curve(sc, 13, 74, [(phase2, 28), (phase2 + 64, 112), (phase2 + 95, 58)], step=0.5)
    en.cc_curve(sc, 13, 71, [(phase2, 36), (phase2 + 72, 98), (phase2 + 95, 44)], step=1)
    en.expression_pump(sc, 13, phase2, 96, low=58, high=116, beat_step=1)
    for ch in melodic:
        sc.cc(ch, 91, min(112, 36 + (ch * 7) % 70), phase2)
        sc.cc(ch, 93, min(110, 8 + (ch * 9) % 90), phase2)
        sc.cc(ch, 94, min(104, (ch * 11) % 88), phase2)

    # VII. Negative-space bridge: organ/harp/choir, sostenuto and fine tuning.
    bridge = phase2 + 96
    sc.marker(bridge, "VII · Room Enough for Hope")
    for ch in melodic:
        sc.all_notes_off(ch, bridge - 0.05)
    sc.cc(0, 66, 127, bridge)
    sc.cc(0, 67, 127, bridge)
    sc.fine_tune(6, -7.0, bridge)
    sc.fine_tune(7, 5.0, bridge)
    _long_pads(sc, 2, root, bridge, 16, mat.SECOND_WIND, 60, 31, 84, bars_per_chord=4, spread=True)
    _sparkle(sc, 5, root + 24, bridge, 16, mat.SECOND_WIND, 58, 64, 105, step=0.5)
    _theme_every_four_bars(sc, 7, mat.DAYBREAK, root + 12, bridge, 16, 55, 90, 66,
                           mat.SECOND_WIND, tag="A-choir-bridge")
    _theme_every_four_bars(sc, 0, mat.ENGINES, root + 12, bridge + 8, 14, 54, 90, 64,
                           mat.OPEN_DOOR, tag="B-piano-bridge")
    en.cc_curve(sc, 2, 11, [(bridge, 28), (bridge + 48, 94), (bridge + 63, 42)], step=0.5)
    en.cc_curve(sc, 7, 70, [(bridge, 0), (bridge + 24, 42), (bridge + 48, 84), (bridge + 63, 127)], step=0.5)
    sc.cc(0, 66, 0, bridge + 60)
    sc.cc(0, 67, 0, bridge + 60)

    # VIII. Second ascent. Temporary Hollow Release pad (program 99 + LSB 19).
    ascent = bridge + 64
    sc.marker(ascent, "VIII · The Second Ascent")
    sc.set_patch(13, 99, ascent, bank_msb=0, bank_lsb=19)
    _section_drums(sc, ascent, 16, "break", 1.0)
    _root_ostinato(sc, 4, root - 12, ascent, 16, progression, 90)
    _sparkle(sc, 3, root + 12, ascent, 16, progression, 74, 54, 96, step=0.25)
    _long_pads(sc, 13, root + 12, ascent, 16, progression, 62, 48, 100, bars_per_chord=2)
    _theme_every_four_bars(sc, 12, mat.OPEN_SKY, root + 24, ascent, 16, 62, 104, 88,
                           progression, tag="C-lead-ascent")
    _theme_every_four_bars(sc, 8, mat.ENGINES, root + 24, ascent + 4, 15, 58, 96, 86,
                           mat.SECOND_WIND, tag="B-horn-ascent")
    _theme_every_four_bars(sc, 14, mat.WORLD, root + 24, ascent + 8, 14, 60, 101, 82,
                           mat.OPEN_DOOR, tag="D-sitar-ascent")
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, root + 24, ascent + 12, 13, 61, 99, 80,
                           mat.LYDIAN_LIFT, tag="A-piano-ascent")
    en.cc_curve(sc, 13, 74, [(ascent, 22), (ascent + 32, 78), (ascent + 56, 126), (ascent + 63, 82)], step=0.5)
    for ch in (8, 10, 11):
        en.cc_curve(sc, ch, 2, [(ascent, 54), (ascent + 48, 124), (ascent + 63, 78)], step=1)
        en.aftertouch_curve(sc, ch, [(ascent, 0), (ascent + 48, 68), (ascent + 63, 0)], step=1)

    # IX. Key lift and four simultaneous themes.
    finale = ascent + 64
    sc.marker(finale, "IX · Every Voice Forward")
    sc.keysig(finale, 5, False)  # B major
    sc.tempo(finale, 144)
    lifted_root = root + 2
    sc.set_patch(13, 89, finale, bank_msb=0, bank_lsb=0)
    _section_drums(sc, finale, 24, "four", 1.08)
    _root_ostinato(sc, 4, lifted_root - 12, finale, 24, progression, 94)
    _chord_pulses(sc, 3, lifted_root + 12, finale, 24, progression, 78, 55, 98, gate=0.26, offbeat=True)
    _long_pads(sc, 6, lifted_root + 12, finale, 24, progression, 76, 50, 96, bars_per_chord=1)
    _long_pads(sc, 13, lifted_root + 12, finale, 24, progression, 62, 50, 100, bars_per_chord=2)
    _sparkle(sc, 1, lifted_root + 24, finale, 24, progression, 70, 68, 105, step=0.5)
    _sparkle(sc, 5, lifted_root + 24, finale, 24, progression, 66, 66, 106, step=0.5)
    _theme_every_four_bars(sc, 0, mat.DAYBREAK, lifted_root + 24, finale, 24, 62, 101, 92,
                           progression, tag="A-counterpoint")
    _theme_every_four_bars(sc, 8, mat.ENGINES, lifted_root + 24, finale, 24, 58, 98, 90,
                           progression, tag="B-counterpoint")
    _theme_every_four_bars(sc, 11, mat.OPEN_SKY, lifted_root + 36, finale, 24, 70, 110, 88,
                           progression, tag="C-counterpoint")
    _theme_every_four_bars(sc, 14, mat.WORLD, lifted_root + 24, finale, 24, 60, 103, 86,
                           progression, tag="D-counterpoint")
    _theme_every_four_bars(sc, 10, mat.OPEN_SKY, lifted_root + 24, finale + 4, 23, 58, 99, 78,
                           mat.SECOND_WIND, tag="C-answer")
    _theme_every_four_bars(sc, 15, mat.WORLD, lifted_root + 24, finale + 8, 22, 62, 102, 78,
                           mat.OPEN_DOOR, tag="D-answer")
    _theme_every_four_bars(sc, 7, mat.DAYBREAK, lifted_root + 12, finale + 12, 21, 55, 92, 75,
                           mat.LYDIAN_LIFT, tag="A-choir")
    _theme_every_four_bars(sc, 12, mat.ENGINES, lifted_root + 36, finale + 16, 20, 70, 110, 84,
                           mat.SECOND_WIND, tag="B-saw")
    # Lead bends and final controller crescendi.
    for bar in range(4, 24, 4):
        b = finale + bar * 4 + 12
        note = en.fit_range(lifted_root + 48 + progression[(bar // 4) % 4], 72, 112)
        sc.note(12, note, b, 3.4, 112, jt=0, jv=1)
        en.bend_curve(sc, 12, [(b, -2.5), (b + 0.45, 0), (b + 2.4, 4.0), (b + 3.25, 0)],
                      step=0.1, range_semitones=12)
    for ch in melodic:
        en.cc_curve(sc, ch, 11, [(finale, 72), (finale + 48, 104), (finale + 80, 124),
                                  (finale + 95, 88)], step=1)
    en.cc_curve(sc, 2, 1, [(finale, 24), (finale + 72, 112), (finale + 95, 36)], step=0.5)
    en.cc_curve(sc, 7, 70, [(finale, 42), (finale + 32, 84), (finale + 64, 127),
                             (finale + 95, 84)], step=0.5)
    en.cc_curve(sc, 13, 74, [(finale, 48), (finale + 72, 127), (finale + 95, 92)], step=0.5)
    en.cc_curve(sc, 13, 71, [(finale, 46), (finale + 64, 104), (finale + 95, 52)], step=1)

    coda = finale + 96
    sc.marker(coda, "X · Open Hands, Open Sky")
    sc.tempo(coda, 118)
    final_chord = _chord(lifted_root + 12, 0, "major", 45, 112, inversion=2, size=5, spread=True)
    for ch in melodic:
        notes = [en.fit_range(n + (ch % 3) * 12, 43, 114) for n in final_chord]
        en.pad(sc, ch, notes, coda, 6.0, 62 + (ch * 3) % 32)
    sc.hit(49, coda, 124, 1.0)
    sc.hit(81, coda + 0.5, 96, 1.2)
    sc.hit(39, coda + 2, 88, 0.2)
    _finish(sc, coda + 6.0, melodic)


SPECS: tuple[en.TrackSpec, ...] = (
    en.TrackSpec(
        1, "Daybreak Relay", "01 - Daybreak Relay.mid", 0xE7F001, 132.0, 518.0,
        build_daybreak_relay,
        "upbeat progressive pop-rock relay for pianos, mallets, organs and guitars",
        "The same ascending hook is physically passed through GM programs 0-31, ending as a guitar launch.",
        program_range=(0, 31), duration_window=(220.0, 270.0), min_notes=2100, min_channels=9,
        min_markers=7, tags=("programs-0-31", "relay", "controllers", "guitar-finale"),
    ),
    en.TrackSpec(
        2, "Brighter Engines", "02 - Brighter Engines.mid", 0xE7F002, 126.0, 550.0,
        build_brighter_engines,
        "cinematic funk-rock ascent for bass orchestra, bowed strings, choir and brass",
        "Programs 32-63 become engines, wings and finally a breath-driven brass horizon.",
        program_range=(32, 63), duration_window=(245.0, 300.0), min_notes=1900, min_channels=9,
        min_markers=6, tags=("programs-32-63", "bass-orchestra", "choir-vowels", "brass"),
    ),
    en.TrackSpec(
        3, "Open-Sky Signal", "03 - Open-Sky Signal.mid", 0xE7F003, 136.0, 518.0,
        build_open_sky_signal,
        "soaring reed-to-synth anthem with a 7/8 launch and filter-controlled horizon",
        "Programs 64-95 move from a sax/woodwind skyline through pipes and portamento leads into eight opening pads.",
        program_range=(64, 95), duration_window=(215.0, 270.0), min_notes=1900, min_channels=9,
        min_markers=7, tags=("programs-64-95", "7-8", "portamento", "filter-sweeps"),
    ),
    en.TrackSpec(
        4, "The World in the Chorus", "04 - The World in the Chorus.mid", 0xE7F004, 124.0, 554.0,
        build_world_in_the_chorus,
        "uplifting world-electronic celebration with weather, folk strings, tuned percussion and scene effects",
        "Programs 96-127 become a journey from rain to applause, capped by every GM percussion key and a second GS rhythm part.",
        program_range=(96, 127), duration_window=(255.0, 320.0), min_notes=2200, min_channels=16,
        min_markers=6, tags=("programs-96-127", "all-drums", "GS-rhythm", "world-electronic"),
    ),
    en.TrackSpec(
        5, "Every Voice Forward", "05 - Every Voice Forward.mid", 0xE7F005, 140.0, 672.0,
        build_every_voice_forward,
        "maximalist uplifting finale for fifteen hand-picked Ferrosintesis voices",
        "Four earlier hooks assemble through 7/8, a negative-space bridge and a B-major key lift into simultaneous counterpoint.",
        program_range=None, duration_window=(285.0, 360.0), min_notes=2600, min_channels=16,
        min_markers=10, tags=("finale", "four-theme-counterpoint", "alt-banks", "key-lift"),
    ),
)
