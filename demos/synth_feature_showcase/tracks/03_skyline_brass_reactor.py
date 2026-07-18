from __future__ import annotations

import engine as en
from .common import climb_line, feature, octave_riff, switch


def build(sc: en.Score) -> None:
    sc.marker(0, "Skyline Brass Reactor - low brass motor")
    sc.marker(128, "Reed ignition")
    sc.marker(256, "Bowed reactor")
    sc.channel(0, "low brass", 58, volume=104, pan=60, reverb=48, chorus=8, echo=6)
    sc.channel(1, "high brass", 56, volume=100, pan=68, reverb=46, chorus=10, echo=8)
    sc.channel(2, "reeds", 64, volume=92, pan=64, reverb=44, chorus=12, echo=18)
    sc.channel(3, "winds", 72, volume=86, pan=64, reverb=52, chorus=18, echo=24)
    sc.channel(4, "bowed strings", 40, volume=96, pan=64, reverb=50, chorus=18, echo=8)
    sc.channel(5, "fiddle reactor", 110, volume=90, pan=64, reverb=42, chorus=12, echo=20)
    sc.channel(9, "reactor kit", None, volume=82, pan=64, reverb=28, chorus=0, echo=0)

    brass_programs = list(range(56, 64))
    for i, prog in enumerate(brass_programs):
        ch = 0 if prog in (57, 58, 60, 61) else 1
        t = i * 28.0
        switch(sc, ch, prog, t)
        en.cc_curve(sc, ch, 11, [(t, 40), (t + 12, 124), (t + 27, 70)], step=0.5)
        en.at_curve(sc, ch, [(t, 0), (t + 10, 100), (t + 24, 0)], step=1.0)
        en.cc_curve(sc, ch, 1, [(t, 0), (t + 8, 92), (t + 27, 20)], step=0.5)
        sc.cc(ch, 68, 127, t + 2)
        octave_riff(sc, ch, 40 if ch == 0 else 52, "dorian", t, 26, 76 + i * 4, step=0.5)
        sc.cc(ch, 68, 0, t + 27)
    reed_programs = list(range(64, 72))
    for i, prog in enumerate(reed_programs):
        t = 112.0 + i * 22.0
        switch(sc, 2, prog, t)
        en.cc_curve(sc, 2, 1, [(t, 0), (t + 8, 108), (t + 20, 0)], step=0.5)
        sc.cc(2, 68, 127, t + 1)
        climb_line(sc, 2, 55, "dorian", t, 20, 64 + i * 3, 102, step=0.5)
        sc.cc(2, 68, 0, t + 21)
    wind_programs = list(range(72, 80))
    for i, prog in enumerate(wind_programs):
        t = 160.0 + i * 20.0
        switch(sc, 3, prog, t)
        en.echo_throw(sc, 3, t + 8, peak=86)
        en.autopan(sc, 3, t, 18, lo=46, hi=82, period=9)
        climb_line(sc, 3, 67, "minor", t, 18, 58 + i * 3, 96, step=0.25)
    bowed_programs = list(range(40, 46)) + [110]
    for i, prog in enumerate(bowed_programs):
        ch = 5 if prog == 110 else 4
        t = 232.0 + i * 20.0
        switch(sc, ch, prog, t)
        en.cc_curve(sc, ch, 1, [(t, 0), (t + 10, 118), (t + 19, 40)], step=0.5)
        sc.cc(ch, 68, 127, t + 1)
        en.bend_curve(sc, ch, [(t + 4, 0.0), (t + 7, 0.8), (t + 10, 0.0)], range_semis=2)
        climb_line(sc, ch, 52 if ch == 4 else 64, "harmonic", t, 18, 66 + i * 4, 108, step=0.5)
        sc.cc(ch, 68, 0, t + 19)
    for t in range(0, 384, 16):
        en.drum_drive(sc, t, 2, energy=68 + min(36, t // 10))

    feature(sc, "brass breath and growl", 0, 0, 224, {57, 58, 60, 61}, min_notes=120, ccs={1: (0, 92), 11: (40, 124), 68: (0, 127)}, aftertouch=(0, 100))
    feature(sc, "high brass colors", 1, 0, 224, {56, 59, 62, 63}, min_notes=90, ccs={1: (0, 92), 11: (40, 124), 68: (0, 127)}, aftertouch=(0, 100))
    feature(sc, "reed slurs", 2, 112, 288, reed_programs, min_notes=120, ccs={1: (0, 108), 68: (0, 127)}, monophonic=True)
    feature(sc, "wind descants", 3, 160, 320, wind_programs, min_notes=160, ccs={10: (46, 82), 94: (18, 86)})
    feature(sc, "bowed strings", 4, 232, 352, set(range(40, 46)), min_notes=80, ccs={1: (0, 118), 68: (0, 127)}, bend=(0.0, 0.35), monophonic=True)
    feature(sc, "fiddle feature", 5, 352, 376, {110}, min_notes=25, ccs={1: (0, 118), 68: (0, 127)}, bend=(0.0, 0.35), monophonic=True)
    sc.audio_check(en.AudioCheck("brass breath", "brightness_up", 8, 16, 0, 8, 1.10, channel=1))
