from __future__ import annotations

import engine as en
from .common import climb_line, feature, octave_riff, switch


def build(sc: en.Score) -> None:
    sc.marker(0, "Atlas of Unbuilt Machines - future seams")
    sc.marker(128, "World pluck atlas")
    sc.marker(256, "Noise gates")
    sc.channel(0, "future keys", 4, volume=90, pan=64, reverb=46, chorus=12, echo=12)
    sc.channel(1, "free reeds", 20, volume=92, pan=64, reverb=50, chorus=20, echo=12)
    sc.channel(2, "world plucks", 104, volume=96, pan=64, reverb=42, chorus=12, echo=18)
    sc.channel(3, "harp timpani vibes", 46, volume=98, pan=64, reverb=50, chorus=12, echo=12)
    sc.channel(4, "sfx fallback", 120, volume=72, pan=64, reverb=40, chorus=0, echo=28)
    sc.channel(5, "bagpipe shanai placeholders", 109, volume=84, pan=64, reverb=48, chorus=12, echo=18)
    sc.channel(9, "atlas kit", None, volume=78, pan=64, reverb=22, chorus=0, echo=0)

    future_keys = [4, 5, 6, 7]
    for i, prog in enumerate(future_keys):
        t = i * 28.0
        switch(sc, 0, prog, t)
        sc.sustain(0, t + 4, t + 14)
        en.at_curve(sc, 0, [(t, 0), (t + 12, 90), (t + 26, 0)], step=1.0)
        octave_riff(sc, 0, 48, "mixolydian", t, 26, 62 + i * 8, step=0.5)
    free_reeds = [20, 21, 22, 23]
    for i, prog in enumerate(free_reeds):
        t = 96.0 + i * 28.0
        switch(sc, 1, prog, t)
        en.cc_curve(sc, 1, 11, [(t, 35), (t + 12, 116), (t + 27, 55)], step=0.5)
        if prog == 22:
            en.cc_curve(sc, 1, 1, [(t, 0), (t + 10, 120), (t + 27, 20)], step=0.5)
        octave_riff(sc, 1, 52, "minor", t, 26, 66 + i * 8, step=0.5)
    world = [104, 105, 106, 107, 108]
    for i, prog in enumerate(world):
        t = 168.0 + i * 22.0
        switch(sc, 2, prog, t)
        en.echo_throw(sc, 2, t + 8, peak=92)
        en.autopan(sc, 2, t, 20, lo=38, hi=90, period=7)
        climb_line(sc, 2, 55, "pent", t, 20, 64 + i * 8, 108, step=0.25)
    refinement = [(46, 0.0), (11, 48.0), (47, 272.0)]
    for prog, t in refinement:
        switch(sc, 3, prog, t)
        if prog == 46:
            for off in range(0, 44, 4):
                en.arpeggio(sc, 3, [36, 43, 48, 55, 60, 67], t + off, 3.5, 0.25, 72 + off // 2)
        elif prog == 11:
            for off in range(0, 44, 4):
                sc.note(3, 72 + (off // 4) % 5, t + off, 3.6, 62 + off)
        else:
            for off in range(0, 96, 4):
                sc.note(3, 40 + (off // 8) % 7, t + off, 1.1, 76 + min(40, off // 2))
    for i, prog in enumerate(range(120, 128)):
        t = 256.0 + i * 8.0
        switch(sc, 4, prog, t)
        sc.cc(4, 10, 24 + (i % 4) * 26, t)
        sc.note(4, 60 + i, t, 0.7, 92 + i * 3, jt=0)
        en.echo_throw(sc, 4, t, peak=84)
    for t in [240.0 + i * 2.0 for i in range(32)]:
        sc.note(2, 72 + int(t) % 12, t, 0.45, 112, jt=1)
        sc.note(3, 48 + int(t) % 7, t + 0.25, 0.9, 108, jt=1)
    for t in [264.0 + i * 1.0 for i in range(24)]:
        sc.note(2, 84 + int(t) % 7, t, 0.35, 118, jt=1)
    for i, prog in enumerate([109, 111]):
        t = 328.0 + i * 24.0
        switch(sc, 5, prog, t)
        en.cc_curve(sc, 5, 11, [(t, 40), (t + 8, 118), (t + 23, 62)], step=0.5)
        en.cc_curve(sc, 5, 1, [(t, 0), (t + 10, 116), (t + 23, 20)], step=0.5)
        en.at_curve(sc, 5, [(t, 0), (t + 12, 100), (t + 23, 0)], step=1.0)
        sc.cc(5, 68, 127, t + 2)
        if prog == 109:
            for off in range(0, 24, 4):
                sc.note(5, 43, t + off, 3.8, 58)
            climb_line(sc, 5, 67, "mixolydian", t, 22, 68, 104, step=0.5)
        else:
            climb_line(sc, 5, 64, "harmonic", t, 22, 72, 112, step=0.5)
        sc.cc(5, 68, 0, t + 23)
    for t in range(0, 384, 16):
        en.drum_drive(sc, t, 2, energy=58 + min(44, t // 7))

    feature(sc, "future keys", 0, 0, 112, future_keys, min_notes=110, ccs={64: (0, 127)}, aftertouch=(0, 90))
    feature(sc, "free reeds", 1, 96, 208, free_reeds, min_notes=100, ccs={1: (0, 120), 11: (35, 116)})
    feature(sc, "world plucks", 2, 168, 278, world, min_notes=180, ccs={10: (39, 89), 94: (18, 92)})
    feature(sc, "harp refinement", 3, 0, 44, {46}, min_notes=60)
    feature(sc, "vibes refinement", 3, 48, 92, {11}, min_notes=11)
    feature(sc, "timpani refinement", 3, 272, 368, {47}, min_notes=20)
    feature(sc, "sfx fallback", 4, 256, 320, set(range(120, 128)), min_notes=8, ccs={10: (24, 102), 94: (18, 84)})
    feature(sc, "bagpipe shanai placeholders", 5, 328, 376, {109, 111}, min_notes=60, ccs={1: (0, 116), 11: (40, 118), 68: (0, 127)}, aftertouch=(0, 100))
    sc.audio_check(en.AudioCheck("noise impact", "hf_up", 256, 264, 240, 248, 1.05))
    sc.audio_check(en.AudioCheck("shanai pressure", "rms_up", 356, 372, 328, 340, 1.05))
