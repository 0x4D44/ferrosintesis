from __future__ import annotations

import engine as en
from .common import climb_line, feature, octave_riff, pulse_chords, switch


def build(sc: en.Score) -> None:
    sc.marker(0, "Choir of Circuitry - string engine")
    sc.marker(96, "Vowel gate")
    sc.marker(240, "Pad ignition")
    sc.channel(0, "strings", 48, volume=96, pan=64, reverb=54, chorus=34, echo=8)
    sc.channel(1, "choir", 52, volume=92, pan=64, reverb=62, chorus=38, echo=10)
    sc.channel(2, "pads", 88, volume=86, pan=64, reverb=60, chorus=42, echo=24)
    sc.channel(3, "orch hit", 55, volume=102, pan=64, reverb=46, chorus=8, echo=18)
    sc.channel(4, "fx pulses", 97, volume=80, pan=64, reverb=56, chorus=30, echo=30)
    sc.channel(9, "circuit kit", None, volume=84, pan=64, reverb=25, chorus=0, echo=0)

    string_programs = list(range(48, 52))
    for i, prog in enumerate(string_programs):
        t = i * 32.0
        switch(sc, 0, prog, t)
        en.cc_curve(sc, 0, 1, [(t, 0), (t + 16, 110), (t + 31, 25)], step=0.5)
        sc.cc(0, 68, 127, t + 4)
        octave_riff(sc, 0, 43, "minor", t, 30, 70 + i * 8, step=0.5)
        sc.cc(0, 68, 0, t + 31)
    choir_programs = [52, 53, 54]
    choir_chords = [[48, 55, 60, 64], [50, 57, 62, 65], [43, 55, 59, 67], [45, 52, 60, 69]]
    for i, prog in enumerate(choir_programs):
        t = 96.0 + i * 40.0
        switch(sc, 1, prog, t)
        en.cc_curve(sc, 1, 70, [(t, 0), (t + 12, 84), (t + 24, 127), (t + 39, 42)], step=0.5)
        en.cc_curve(sc, 1, 1, [(t, 0), (t + 20, 100), (t + 39, 30)], step=0.5)
        pulse_chords(sc, 1, choir_chords, t, 10, 62 + i * 8, span=4.0, gate=0.98)
    pad_programs = list(range(88, 96))
    for i, prog in enumerate(pad_programs):
        t = 192.0 + i * 16.0
        switch(sc, 2, prog, t)
        en.autopan(sc, 2, t, 14, lo=50, hi=78, period=10)
        en.cc_curve(sc, 2, 74, [(t, 35), (t + 8, 118), (t + 15, 80)], step=0.5)
        en.cc_curve(sc, 2, 71, [(t, 0), (t + 8, 120), (t + 15, 30)], step=0.5)
        pulse_chords(sc, 2, [[55, 60, 64], [57, 62, 67], [52, 59, 64]], t, 4, 58 + i * 5, span=4.0)
    fx_programs = [97, 99, 101, 103]
    for i, prog in enumerate(fx_programs):
        t = 288.0 + i * 20.0
        switch(sc, 4, prog, t)
        en.echo_throw(sc, 4, t + 8, peak=100)
        en.autopan(sc, 4, t, 18, lo=30, hi=98, period=6)
        climb_line(sc, 4, 60, "pent", t, 18, 60 + i * 8, 108, step=0.25)
    for t in [32, 64, 96, 160, 224, 288, 336, 368]:
        switch(sc, 3, 55, float(t))
        sc.note(3, 48, float(t), 0.8, 112, jt=0)
        en.echo_throw(sc, 3, float(t), peak=90)
    for t in range(0, 384, 16):
        en.drum_drive(sc, t, 2, energy=64 + min(42, t // 8))

    feature(sc, "string vibrato slurs", 0, 0, 128, string_programs, min_notes=160, ccs={1: (0, 110), 68: (0, 127)})
    feature(sc, "choir vowel morph", 1, 96, 216, choir_programs, min_notes=100, ccs={1: (0, 100), 70: (0, 127)})
    feature(sc, "pad filter resonance", 2, 192, 320, pad_programs, min_notes=80, ccs={10: (50, 78), 71: (0, 120), 74: (35, 118)})
    feature(sc, "orchestra hit", 3, 32, 370, {55}, min_notes=8, ccs={94: (18, 90)})
    feature(sc, "synth fx sustain", 4, 288, 368, fx_programs, min_notes=140, ccs={10: (30, 98), 94: (18, 100)})
    sc.audio_check(en.AudioCheck("vowel shifts", "hf_down", 112, 128, 96, 104, 0.97))
    sc.audio_check(en.AudioCheck("pad sweep", "hf_up", 224, 236, 192, 204, 1.03))
