"""T5 - the drum roll-call: every implemented channel-10 voice, the Brush kit, the
hi-hat choke group and a tom velocity sweep. Isolation here is structural (the
intended key set), not acoustic - unmapped keys deliberately emit a generic tick
(drums.rs:2023), so 'every key sounded' would be vacuous.
"""
from __future__ import annotations

import engine as en

# Every key with a distinct voice in drums.rs (keys 35-82, contiguous - survey D).
DRUM_KEYS = list(range(35, 83))

DRUM_NAMES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick", 38: "Acoustic Snare",
    39: "Hand Clap", 40: "Electric Snare", 41: "Low Floor Tom", 42: "Closed Hi-Hat",
    43: "High Floor Tom", 44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1", 50: "High Tom",
    51: "Ride Cymbal 1", 52: "Chinese Cymbal", 53: "Ride Bell", 54: "Tambourine",
    55: "Splash Cymbal", 56: "Cowbell", 57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo", 61: "Low Bongo", 62: "Mute Hi Conga",
    63: "Open Hi Conga", 64: "Low Conga", 65: "High Timbale", 66: "Low Timbale",
    67: "High Agogo", 68: "Low Agogo", 69: "Cabasa", 70: "Maracas",
    71: "Short Whistle", 72: "Long Whistle", 73: "Short Guiro", 74: "Long Guiro",
    75: "Claves", 76: "Hi Wood Block", 77: "Low Wood Block", 78: "Mute Cuica",
    79: "Open Cuica", 80: "Mute Triangle", 81: "Open Triangle", 82: "Shaker",
}

CH = 9
GRID = 4.0             # 2.0 s at 120 BPM: one drum per grid cell, marker+hit on the line
_CHOKE_AFTER = 1.3     # beats after the hit to choke the ring before the next cell
BRUSH_KEYS = [35, 36, 37, 38, 39, 40, 42, 44, 46]   # the keys the Brush kit remaps (drums.rs:1435)
TAIL_BEATS = 2.0


def _hit(sc: en.Score, key: int, beat: float, vel: int = 108) -> None:
    sc.note(CH, key, beat, 0.2, vel, jt=0, jv=0)


def total_beats() -> float:
    # roll-call + brush: one grid cell each; hi-hat choke + tom sweep: two cells each.
    n_roll = len(DRUM_KEYS)
    n_brush = len(BRUSH_KEYS)
    return (n_roll + n_brush) * GRID + 2 * GRID + 2 * GRID + TAIL_BEATS


def build(sc: en.Score) -> None:
    sc.channel(CH, "kit", program=None, volume=110, pan=64, reverb=0, chorus=0, echo=0)
    t = 0.0

    # V3 kit roll-call: one isolated hit per 2 s cell, ON the grid line, choked
    # before the next cell so scrubbing to a label lands exactly on that drum.
    for key in DRUM_KEYS:
        sc.marker(t, f"KEY {key:03d} {DRUM_NAMES.get(key, '?')}")
        _hit(sc, key, t)
        sc.cc(CH, 120, 0, t + _CHOKE_AFTER)
        t += GRID

    # Brush kit: program 40 selects it (drums.rs:1342); author the PC in the previous
    # cell's tail so the first brush hit still lands on its grid line.
    sc.program(CH, 40, t - 0.5)
    for key in BRUSH_KEYS:
        sc.marker(t, f"BRUSH {key:03d} {DRUM_NAMES.get(key, '?')}")
        _hit(sc, key, t)
        sc.cc(CH, 120, 0, t + _CHOKE_AFTER)
        t += GRID
    sc.program(CH, 0, t - 0.5)   # back to V3, in the tail before the next cell

    # Hi-hat choke group: 42/44/46 choke each other (engine.rs:1078). Open then
    # closed, x3 - a two-cell (4 s) window.
    sc.marker(t, "HI-HAT CHOKE 46->42")
    for i in range(3):
        _hit(sc, 46, t + i * 2.0, 110)          # open hat rings...
        _hit(sc, 42, t + i * 2.0 + 0.5, 100)     # ...closed hat chokes it
    t += 2 * GRID

    # Tom velocity sweep on one key, to hear the pitch-glide / velocity response -
    # a two-cell (4 s) window.
    sc.marker(t, "TOM VELOCITY SWEEP (key 045)")
    for i, vel in enumerate((40, 70, 100, 127)):
        _hit(sc, 45, t + i * 1.5, vel)
    t += 2 * GRID
