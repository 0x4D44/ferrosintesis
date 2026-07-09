from __future__ import annotations

import engine as en
from .common import climb_line, feature, octave_riff, switch


def build(sc: en.Score) -> None:
    sc.marker(0, "Ignition Court - palm mute engine")
    sc.marker(128, "Lead reactor")
    sc.marker(288, "Final ignition")
    sc.channel(0, "guitar left", 24, volume=100, pan=26, reverb=28, chorus=10, echo=14)
    sc.channel(1, "guitar right", 25, volume=96, pan=102, reverb=28, chorus=10, echo=14)
    sc.channel(2, "bass engines", 32, volume=108, pan=64, reverb=12, chorus=0, echo=0)
    sc.channel(3, "synth lead", 80, volume=100, pan=64, reverb=45, chorus=35, echo=28)
    sc.channel(4, "wah answer", 29, volume=88, pan=58, reverb=22, chorus=12, echo=20)
    sc.channel(9, "default kit", None, volume=110, pan=64, reverb=34, chorus=0, echo=0)

    for t in range(0, 384, 32):
        en.drum_drive(sc, t, 8, energy=90 + min(28, t // 16))
    for t in range(0, 384, 24):
        sc.cc(9, 10, 64 + ((t // 24) % 3 - 1) * 10, t)

    guitar_programs = list(range(24, 32))
    bass_programs = list(range(32, 40))
    lead_programs = list(range(80, 88))
    for i, prog in enumerate(guitar_programs):
        t = i * 24.0
        switch(sc, 0, prog, t)
        switch(sc, 1, guitar_programs[-1 - i], t)
        octave_riff(sc, 0, 40, "phrygian", t, 24, 74 + i * 4, step=0.5)
        octave_riff(sc, 1, 40, "phrygian", t + 0.25, 23.5, 70 + i * 4, step=0.5, octave=1)
    for i, prog in enumerate(bass_programs):
        t = i * 32.0
        switch(sc, 2, prog, t)
        octave_riff(sc, 2, 28, "phrygian", t, 32, 78 + i * 4, step=0.5)
        if prog == 35:
            en.bend_curve(sc, 2, [(t + 4, 0.0), (t + 5.5, 0.8), (t + 7, 0.0)], range_semis=2)
    for i, prog in enumerate(lead_programs):
        t = 112.0 + i * 28.0
        switch(sc, 3, prog, t)
        sc.bend_range(3, 12, t + 0.05)
        sc.cc(3, 93, 25 + i * 8, t + 0.1)
        en.cc_curve(sc, 3, 1, [(t, 0), (t + 6, 127), (t + 16, 60), (t + 27, 0)], step=0.5)
        en.echo_throw(sc, 3, t + 12, peak=98)
        sc.portamento_on(3, t + 1.0, time_cc=88)
        climb_line(sc, 3, 52, "minor", t, 26, 76, 118, step=0.5)
        sc.portamento_off(3, t + 26.5)
        en.bend_curve(sc, 3, [(t + 18, 0.0), (t + 20, 5.0), (t + 22, 0.0)], range_semis=12)

    en.wah(sc, 4, 64, 96, lo=24, hi=120)
    en.cc_curve(sc, 4, 71, [(64, 0), (96, 127), (144, 35)], step=1.0)
    en.autopan(sc, 4, 64, 120, lo=42, hi=86, period=12)
    for t in range(64, 184, 16):
        switch(sc, 4, 29 if (t // 16) % 2 == 0 else 30, float(t))
        octave_riff(sc, 4, 52, "phrygian", float(t), 16, 86, step=0.25)

    sc.cc(0, 68, 127, 300)
    sc.cc(1, 68, 127, 300)
    en.bend_curve(sc, 0, [(300, 0.0), (302, 1.0), (304, -0.5), (306, 0.0)], step=0.25)
    octave_riff(sc, 0, 52, "phrygian", 300, 32, 112, step=0.25)
    octave_riff(sc, 1, 52, "phrygian", 300.125, 32, 108, step=0.25)
    climb_line(sc, 3, 64, "phrygian", 288, 72, 104, 124, step=0.25)
    octave_riff(sc, 4, 52, "phrygian", 320, 48, 116, step=0.25)
    octave_riff(sc, 0, 40, "phrygian", 336, 40, 122, step=0.25)
    octave_riff(sc, 1, 52, "phrygian", 336.125, 39.5, 118, step=0.25)
    sc.cc(0, 68, 0, 333)
    sc.cc(1, 68, 0, 333)

    feature(sc, "all guitars", 0, 0, 192, guitar_programs, min_notes=180, ccs={10: (26, 26)})
    feature(sc, "all basses", 2, 0, 256, bass_programs, min_notes=160, bend=(0.0, 0.35))
    feature(sc, "all synth leads", 3, 112, 340, lead_programs, min_notes=160, ccs={1: (0, 127), 93: (25, 80), 94: (18, 98), 5: (88, 88), 65: (0, 127)}, bend=(0.0, 0.35))
    feature(sc, "wah resonance drive", 4, 64, 184, {29, 30}, min_notes=180, ccs={71: (0, 127), 74: (24, 120), 10: (42, 86)})
    feature(sc, "default drum kit", 9, 0, 384, set(), min_notes=200, drum_kit=True)
    sc.audio_check(en.AudioCheck("wah resonance bite", "hf_up", 80, 88, 72, 80, 1.08))
    sc.audio_check(en.AudioCheck("lead bloom", "hf_up", 128, 148, 112, 124, 1.08))
