"""T6 - controllers and effects, each on a program that demonstrably responds. A
named list of AUDIBLE features, not 'every CC'. Family gates are narrow: a demo
aimed at the wrong program shows nothing (CC70 on a piano is silent), so each
section names its program from the HLD table.

This track authors controllers on purpose, so it is NOT dry and is exempt from the
audio-isolation oracles. check_coverage(d) asserts each named feature CC is present.
"""
from __future__ import annotations

import engine as en

from .audition import dry_sends

CH = 0
# CCs this track must exercise (check_coverage(d) mirrors this).
REQUIRED = {91, 93, 94, 1, 74, 71, 64, 70, 2, 5}

GRID = 3.0  # 2.0 s at 90 BPM: snap every section marker onto a :x0/:x2/:x4... line


def _grid(t: float) -> float:
    """Round t UP to the next 2 s (3-beat) grid line so the floored lyric time is
    exact. Sections keep their natural, content-driven length; the snap adds at most
    ~1 s of lead-in gap. The +6.0-beat A/B sub-markers are already 2 grid cells, so
    they stay aligned when the section start does."""
    r = t % GRID
    return t if r < 1e-6 or GRID - r < 1e-6 else t - r + GRID


def _chord(sc, ch, root, beat, dur, vel=100):
    for off in (0, 4, 7):
        sc.note(ch, root + off, beat, dur, vel, jt=0, jv=0)


def _section(sc, t, label):
    # Snap the section onto the 2 s grid, then CC121 (reset all controllers) between
    # demos - unlike the melodic slot_reset it DESTROYS the wah filter (engine.rs:1458),
    # so the CC71/CC74 resonance section does not colour every section after it. The
    # following program change + dry CCs re-establish a clean channel. Returns the
    # snapped t so the section's content lays out from the grid line.
    t = _grid(t)
    sc.marker(t, label)
    sc.cc(CH, 121, 0, t + 0.05)
    return t


def build(sc: en.Score) -> None:
    sc.channel(CH, "effects", program=None, volume=104, pan=64, reverb=0, chorus=0, echo=0)
    t = 0.0

    # CC91 hall reverb A/B - strings 48.
    t = _section(sc, t, "CC91 hall reverb: dry")
    sc.program(CH, 48, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    _chord(sc, CH, 60, t + 1.0, 3.0)
    sc.cc(CH, 120, 0, t + 5.0)
    sc.marker(t + 6.0, "CC91 hall reverb: wet")
    sc.cc(CH, 91, 110, t + 6.1)
    _chord(sc, CH, 60, t + 7.0, 3.0)
    sc.cc(CH, 120, 0, t + 11.5)
    t += 13.0

    # CC93 chorus A/B - pad 88.
    t = _section(sc, t, "CC93 chorus: dry")
    sc.program(CH, 88, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    _chord(sc, CH, 55, t + 1.0, 3.0)
    sc.cc(CH, 120, 0, t + 5.0)
    sc.marker(t + 6.0, "CC93 chorus: on")
    sc.cc(CH, 93, 127, t + 6.1)
    _chord(sc, CH, 55, t + 7.0, 3.0)
    sc.cc(CH, 120, 0, t + 11.5)
    t += 13.0

    # CC94 echo A/B - electric guitar 30 (staccato so the repeats are exposed).
    t = _section(sc, t, "CC94 echo: dry")
    sc.program(CH, 30, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    for i in range(3):
        sc.note(CH, 52, t + 1.0 + i * 1.0, 0.2, 104, jt=0, jv=0)
    sc.cc(CH, 120, 0, t + 5.0)
    sc.marker(t + 6.0, "CC94 echo: on")
    sc.cc(CH, 94, 127, t + 6.1)
    for i in range(3):
        sc.note(CH, 52, t + 7.0 + i * 1.0, 0.2, 104, jt=0, jv=0)
    sc.cc(CH, 120, 0, t + 12.5)
    t += 14.0

    # CC1 vibrato - violin 40, held note, mod wheel rises.
    t = _section(sc, t, "CC1 vibrato (violin)")
    sc.program(CH, 40, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.note(CH, 67, t + 1.0, 6.0, 100, jt=0, jv=0)
    en.cc_curve(sc, CH, 1, [(t + 1.5, 0), (t + 6.0, 110)], step=0.25)
    sc.cc(CH, 120, 0, t + 7.5)
    t += 9.0

    # CC1 Leslie - percussive organ 17; hold each end >= 3s for the rotor inertia.
    t = _section(sc, t, "CC1 Leslie ramp (organ)")
    sc.program(CH, 17, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    _chord(sc, CH, 55, t + 1.0, 11.0, vel=96)
    en.cc_curve(sc, CH, 1, [(t + 1.5, 0), (t + 5.5, 0), (t + 6.0, 127), (t + 11.0, 127)], step=0.5)
    sc.cc(CH, 120, 0, t + 12.5)
    t += 14.0

    # CC74 filter sweep - saw lead 81; sweep 126 -> 20, NEVER park on 127 (127 = bypass).
    t = _section(sc, t, "CC74 filter sweep (lead)")
    sc.program(CH, 81, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.note(CH, 64, t + 1.0, 6.0, 104, jt=0, jv=0)
    en.cc_curve(sc, CH, 74, [(t + 1.2, 126), (t + 6.5, 20)], step=0.25)
    sc.cc(CH, 120, 0, t + 7.5)
    t += 9.0

    # CC71 resonance - steel guitar 25, with CC74 parked in band first (else it parks at 12kHz).
    t = _section(sc, t, "CC71 resonance (guitar, CC74 in band)")
    sc.program(CH, 25, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.cc(CH, 74, 45, t + 0.6)
    sc.note(CH, 55, t + 1.0, 6.0, 104, jt=0, jv=0)
    en.cc_curve(sc, CH, 71, [(t + 1.5, 0), (t + 6.0, 127)], step=0.25)
    sc.cc(CH, 120, 0, t + 7.5)
    t += 9.0

    # CC64 sustain - piano 0, staccato notes held by the pedal across their offs.
    t = _section(sc, t, "CC64 sustain pedal (piano)")
    sc.program(CH, 0, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.sustain(CH, t + 0.9, t + 5.0)
    for i, p in enumerate((48, 52, 55, 60, 64)):
        sc.note(CH, p, t + 1.0 + i * 0.6, 0.2, 100, jt=0, jv=0)
    sc.cc(CH, 120, 0, t + 6.5)
    t += 8.0

    # CC70 vowel morph - choir 52; sweep the four anchors mm/oo/ah/eh.
    t = _section(sc, t, "CC70 vowel morph (choir)")
    sc.program(CH, 52, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    _chord(sc, CH, 55, t + 1.0, 6.0, vel=96)
    en.cc_curve(sc, CH, 70, [(t + 1.2, 0), (t + 6.5, 127)], step=0.25)
    sc.cc(CH, 120, 0, t + 7.5)
    t += 9.0

    # CC2 breath - flute 73; cut-only (127 is neutral), so ramp DOWN.
    t = _section(sc, t, "CC2 breath cut (flute)")
    sc.program(CH, 73, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.note(CH, 74, t + 1.0, 5.0, 100, jt=0, jv=0)
    en.cc_curve(sc, CH, 2, [(t + 1.2, 127), (t + 5.5, 45)], step=0.25)
    sc.cc(CH, 120, 0, t + 6.5)
    t += 8.0

    # Pitch bend - violin 40.
    t = _section(sc, t, "Pitch bend (violin)")
    sc.program(CH, 40, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.note(CH, 67, t + 1.0, 4.0, 100, jt=0, jv=0)
    en.bend_curve(sc, CH, [(t + 1.5, 0.0), (t + 2.5, 2.0), (t + 3.5, -2.0), (t + 4.5, 0.0)], step=0.125)
    sc.cc(CH, 120, 0, t + 5.5)
    t += 7.0

    # Channel aftertouch - brass section 61.
    t = _section(sc, t, "Channel aftertouch (brass)")
    sc.program(CH, 61, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.note(CH, 55, t + 1.0, 5.0, 100, jt=0, jv=0)
    en.at_curve(sc, CH, [(t + 1.5, 0), (t + 5.0, 127)], step=0.25)
    sc.cc(CH, 120, 0, t + 6.5)
    t += 8.0

    # Portamento - saw lead 81; CC5 time + CC65 on, a leap glides.
    t = _section(sc, t, "Portamento (lead)")
    sc.program(CH, 81, t + 0.3)
    dry_sends(sc, CH, t + 0.4)
    sc.portamento_on(CH, t + 0.6, time_cc=100)
    sc.note(CH, 52, t + 1.0, 1.5, 104, jt=0, jv=0)
    sc.note(CH, 64, t + 2.5, 2.5, 104, jt=0, jv=0)
    sc.portamento_off(CH, t + 5.2)
    sc.cc(CH, 120, 0, t + 5.5)
    t += 7.0

    # No-CC A/Bs - features with no MIDI off switch; demo by swapping the PROGRAM.
    for label, a, b, root, gesture in (
        ("A/B piano sympathetic: GM000 vs GM004", 0, 4, 48, "chord"),
        ("A/B guitar sympathetic: GM024 vs GM026", 24, 26, 45, "strum"),
        ("A/B overdrive insert: GM027 vs GM030", 27, 30, 40, "power"),
    ):
        for prog in (a, b):
            t = _section(sc, t, f"{label} [{prog:03d}]")
            sc.program(CH, prog, t + 0.3)
            dry_sends(sc, CH, t + 0.4)
            if gesture == "power":
                sc.note(CH, root, t + 1.0, 3.0, 110, jt=0, jv=0)
                sc.note(CH, root + 7, t + 1.0, 3.0, 110, jt=0, jv=0)
            else:
                _chord(sc, CH, root, t + 1.0, 3.0, vel=104)
            sc.cc(CH, 120, 0, t + 5.0)
            t += 6.0

    sc.marker(_grid(t), "end")
