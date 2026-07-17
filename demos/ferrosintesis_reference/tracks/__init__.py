"""Track specs. T1-T4 are the same melodic emitter over a program range; T5 is the
drum roll-call; T6 is the controllers/effects list."""
from __future__ import annotations

import engine as en

import programs as pr
from . import audition, effects, kit

# Melodic tracks: number -> (program lo, hi). analyze.py reads this to recompute the
# slot grid rather than bloat the manifest with an AudioCheck per slot.
MELODIC = {1: (0, 31), 2: (32, 63), 3: (64, 95), 4: (96, 127)}
# 96 BPM makes SLOT_BEATS (8) land on exactly 5.0 s, so every instrument slot
# starts on a :x0/:x5 clock boundary. At 100 BPM a slot was 4.8 s and the roll
# drifted off the 5-second grid (…0:15, 0:19, 0:24… instead of …0:15, 0:20…).
BPM_MELODIC = 96.0

_TITLES = {
    1: "Keys, Chromatic, Organ, Guitar",
    2: "Bass, Solo Strings, Ensemble, Brass",
    3: "Reed, Pipe, Lead, Pad",
    4: "FX, World, Percussive, Noise",
}


def _melodic_builder(lo: int, hi: int):
    slots = pr.melodic_slots(lo, hi)

    def build(sc: en.Score) -> None:
        audition.build_melodic(sc, slots)

    return build, len(slots)


def _measure(builder) -> float:
    probe = en.Score(0, "probe", 120.0, 0.0)
    builder(probe)
    return probe.last_beat


def _window(secs: float) -> tuple[float, float]:
    return (secs * 0.85, secs * 1.15)


SPECS: list[en.TrackSpec] = []

for num, (lo, hi) in MELODIC.items():
    build, n = _melodic_builder(lo, hi)
    beats = audition.track_beats(n)
    secs = beats * 60.0 / BPM_MELODIC
    SPECS.append(en.TrackSpec(
        num, _TITLES[num], f"{num:02d} - {_TITLES[num]}.mid",
        202607120 + num, BPM_MELODIC, beats, build, "instrument audition", _window(secs),
    ))

_KIT_BPM = 120.0
_kit_beats = kit.total_beats()
SPECS.append(en.TrackSpec(
    5, "Kit Roll-Call", "05 - Kit Roll-Call.mid", 202607125, _KIT_BPM, _kit_beats,
    kit.build, "every drum voice + brush kit", _window(_kit_beats * 60.0 / _KIT_BPM),
))

_FX_BPM = 90.0
_fx_beats = _measure(effects.build) + 2.0
SPECS.append(en.TrackSpec(
    6, "Controllers and Effects", "06 - Controllers and Effects.mid", 202607126, _FX_BPM, _fx_beats,
    effects.build, "audible controllers + effects", _window(_fx_beats * 60.0 / _FX_BPM),
))
