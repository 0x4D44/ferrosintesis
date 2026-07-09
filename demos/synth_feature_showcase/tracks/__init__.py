from __future__ import annotations

import importlib

import engine as en

t01 = importlib.import_module(".01_ignition_court", __name__)
t02 = importlib.import_module(".02_cathedral_mechanica", __name__)
t03 = importlib.import_module(".03_skyline_brass_reactor", __name__)
t04 = importlib.import_module(".04_choir_of_circuitry", __name__)
t05 = importlib.import_module(".05_atlas_of_unbuilt_machines", __name__)

SPECS = [
    en.TrackSpec(1, "Ignition Court", "01 - Ignition Court.mid", 202607091, 156, 384, t01.build, "guitar/bass/drum/synth-lead chase", (135, 170)),
    en.TrackSpec(2, "Cathedral Mechanica", "02 - Cathedral Mechanica.mid", 202607092, 150, 384, t02.build, "modal keys, organs, bells, timpani", (140, 175)),
    en.TrackSpec(3, "Skyline Brass Reactor", "03 - Skyline Brass Reactor.mid", 202607093, 168, 384, t03.build, "brass, reeds, winds, bowed strings", (125, 160)),
    en.TrackSpec(4, "Choir of Circuitry", "04 - Choir of Circuitry.mid", 202607094, 160, 384, t04.build, "strings, choir, pads, synth FX", (132, 166)),
    en.TrackSpec(5, "Atlas of Unbuilt Machines", "05 - Atlas of Unbuilt Machines.mid", 202607095, 154, 384, t05.build, "future seams, world plucks, SFX", (136, 170)),
]
