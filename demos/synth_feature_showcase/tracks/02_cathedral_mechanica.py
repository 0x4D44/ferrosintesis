from __future__ import annotations

import engine as en
from .common import climb_line, feature, octave_riff, pulse_chords, switch


def build(sc: en.Score) -> None:
    sc.marker(0, "Cathedral Mechanica - prepared keys")
    sc.marker(128, "Leslie machinery")
    sc.marker(272, "Bell and kettle ascent")
    sc.channel(0, "piano and future keys", 0, volume=98, pan=64, reverb=52, chorus=0, echo=8)
    sc.channel(1, "bells and bars", 8, volume=90, pan=64, reverb=58, chorus=18, echo=16)
    sc.channel(2, "organs and free reeds", 16, volume=102, pan=64, reverb=60, chorus=28, echo=12)
    sc.channel(3, "timpani", 47, volume=104, pan=64, reverb=42, chorus=0, echo=0)
    sc.channel(4, "crystal sequencers", 96, volume=82, pan=64, reverb=54, chorus=22, echo=24)
    sc.channel(9, "cathedral kit", None, volume=86, pan=64, reverb=30, chorus=0, echo=0)

    sc.soft_pedal(0, 0, 32)
    sc.sustain(0, 8, 24)
    sc.sostenuto(0, 24, 40)
    sc.fine_tune(0, 9, 0.2)
    sc.bend_range(0, 12, 64)
    sc.portamento_on(0, 80, time_cc=92)
    en.at_curve(sc, 0, [(96, 0), (112, 112), (124, 0)], step=1.0)
    en.bend_curve(sc, 0, [(96, 0), (104, 3.0), (112, 0)], range_semis=12)

    key_programs = [0, 4, 5, 6, 7]
    for i, prog in enumerate(key_programs):
        t = i * 24.0
        switch(sc, 0, prog, t)
        octave_riff(sc, 0, 48, "harmonic", t, 24, 62 + i * 7, step=0.5)
    sc.portamento_off(0, 125)

    bell_programs = list(range(8, 15))
    for i, prog in enumerate(bell_programs):
        t = 120.0 + i * 20.0
        switch(sc, 1, prog, t)
        en.autopan(sc, 1, t, 18, lo=48, hi=80, period=8)
        en.arpeggio(sc, 1, [en.pitch(60, "minor", d) for d in [0, 2, 4, 7]], t, 18, 0.5, 76 + i * 3)

    organ_programs = list(range(16, 24))
    organ_chords = [[40, 47, 52, 55], [38, 45, 52, 57], [43, 50, 55, 59], [36, 43, 51, 55]]
    for i, prog in enumerate(organ_programs):
        t = 64.0 + i * 28.0
        switch(sc, 2, prog, t)
        en.cc_curve(sc, 2, 1, [(t, 0), (t + 8, 127), (t + 22, 30)], step=0.5)
        en.cc_curve(sc, 2, 11, [(t, 48), (t + 12, 115), (t + 27, 70)], step=1.0)
        sc.portamento_on(2, t + 2, time_cc=76)
        pulse_chords(sc, 2, organ_chords, t, 7, 64 + i * 4, span=4.0, gate=0.95)
        sc.portamento_off(2, t + 27)

    for t in range(160, 376, 8):
        sc.note(3, 43 + (t // 16) % 6, t, 1.2, 82 + min(36, (t - 160) // 8), jt=2)
    for i, prog in enumerate(range(96, 104)):
        t = 192.0 + i * 20.0
        switch(sc, 4, prog, t)
        en.autopan(sc, 4, t, 18, lo=36, hi=92, period=6)
        climb_line(sc, 4, 72, "minor", t, 18, 54 + i * 4, 94 + i * 3, step=0.25)
    for t in range(0, 384, 16):
        en.drum_drive(sc, t, 2, energy=60 + min(36, t // 8))

    feature(sc, "piano pedals and pitch", 0, 0, 126, key_programs, min_notes=130, ccs={64: (0, 127), 66: (0, 127), 67: (0, 127), 5: (92, 92), 65: (0, 127), 6: (12, 70), 100: (0, 127), 101: (0, 127)}, bend=(0.0, 0.25), aftertouch=(0, 100))
    feature(sc, "bells bars vibes", 1, 120, 260, bell_programs, min_notes=120, ccs={10: (48, 80)})
    feature(sc, "organs free reeds", 2, 64, 288, organ_programs, min_notes=160, ccs={1: (0, 127), 5: (76, 76), 11: (48, 115), 65: (0, 127)})
    feature(sc, "timpani refinement bed", 3, 160, 376, {47}, min_notes=20)
    feature(sc, "crystal programs", 4, 192, 352, set(range(96, 104)), min_notes=160, ccs={10: (36, 92)})
    sc.audio_check(en.AudioCheck("soft pedal opens", "hf_up", 36, 52, 4, 20, 1.05))
    sc.audio_check(en.AudioCheck("leslie build", "hf_up", 136, 156, 72, 92, 1.08))
