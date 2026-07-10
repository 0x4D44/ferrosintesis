from __future__ import annotations

import importlib

import engine as en

t01 = importlib.import_module(".01_tidal_geometry", __name__)
t02 = importlib.import_module(".02_wire_and_wake", __name__)
t03 = importlib.import_module(".03_blue_horizon_machine", __name__)
t04 = importlib.import_module(".04_broadcasts_from_a_fractured_planet", __name__)
t05 = importlib.import_module(".05_one_cell_many_skies", __name__)
t06 = importlib.import_module(".06_late_for_the_ordinary", __name__)
t07 = importlib.import_module(".07_carry_the_lantern", __name__)
t08 = importlib.import_module(".08_parameters_in_bloom", __name__)
t09 = importlib.import_module(".09_black_glass_pursuit", __name__)
t10 = importlib.import_module(".10_the_library_at_the_end_of_weather", __name__)
t11 = importlib.import_module(".11_clockwork_orchard", __name__)
t12 = importlib.import_module(".12_letters_to_a_future_ocean", __name__)
t13 = importlib.import_module(".13_night_market_in_thirteen", __name__)
t14 = importlib.import_module(".14_every_door_opens_at_once", __name__)

SPECS = [
    en.TrackSpec(1, "Tidal Geometry", "01 - Tidal Geometry.mid", 2026071001, 108, 392,
                 t01.build, "aquatic chamber-orchestra motion in changing metre", (175, 235),
                 "Water, bodies, and light describe precise arcs before a widening horizon.",
                 650, 7, 5, 5, 3, ("fine-line",)),
    en.TrackSpec(2, "Wire and Wake", "02 - Wire and Wake.mid", 2026071002, 132, 440,
                 t02.build, "high-wire guitars, hocketing reeds, and athletic percussion", (165, 230),
                 "Tension travels along a cable, becomes propulsion, then releases into spray.",
                 900, 8, 5, 5, 4, ("fine-line",)),
    en.TrackSpec(3, "Blue Horizon Machine", "03 - Blue Horizon Machine.mid", 2026071003, 124, 416,
                 t03.build, "night-time aquatic pageant for glass, orchestra, and choir", (170, 235),
                 "A precise spectacle machine discovers breath, weightlessness, and a human horizon.",
                 850, 8, 5, 5, 3, ("fine-line",)),
    en.TrackSpec(4, "Broadcasts from a Fractured Planet", "04 - Broadcasts from a Fractured Planet.mid",
                 2026071004, 92, 400, t04.build,
                 "polymetric global collage resolving toward a fragile shared pulse", (210, 310),
                 "Alarm, argument, grief, and solidarity coexist without a false easy resolution.",
                 700, 8, 6, 5, 4, ("world",)),
    en.TrackSpec(5, "One Cell, Many Skies", "05 - One Cell, Many Skies.mid", 2026071005, 70, 456,
                 t05.build, "evolutionary variations from monody to orchestral ecology", (230, 340),
                 "One small organism mutates, specializes, cooperates, and leaves a memory.",
                 750, 8, 7, 7, 4, ("evolution",)),
    en.TrackSpec(6, "Late for the Ordinary", "06 - Late for the Ordinary.mid", 2026071006, 132, 384,
                 t06.build, "jaunty piano-and-bass morning song with crooked detours", (145, 210),
                 "Domestic routine becomes a bright, breathless change of scene.",
                 750, 7, 5, 4, 3, ("day-in-the-life-middle",)),
    en.TrackSpec(7, "Carry the Lantern", "07 - Carry the Lantern.mid", 2026071007, 104, 640,
                 t07.build, "continuous linked-song medley with callbacks and contrapuntal finale", (250, 390),
                 "Nine short rooms exchange one lantern motif and arrive together before a humane coda.",
                 1200, 9, 8, 8, 5, ("abbey-road-medley-flow",)),
    en.TrackSpec(8, "Parameters in Bloom", "08 - Parameters in Bloom.mid", 2026071008, 72, 720,
                 t08.build, "symbolic model history growing from seed token to orchestral system", (330, 500),
                 "The GPT lineage accumulates context, media, reasoning space, tools, and joined voices.",
                 1400, 10, 18, 10, 5, ("gpt-history",)),
    en.TrackSpec(9, "Black Glass Pursuit", "09 - Black Glass Pursuit.mid", 2026071009, 168, 480,
                 t09.build, "fast chromatic spy-film chase for guitar, vibraphone, brass, and orchestra", (150, 230),
                 "A reflection becomes a pursuit across trains, roofs, tunnels, and a final glass bridge.",
                 1200, 10, 6, 6, 4, ("spy-film-score",)),
    en.TrackSpec(10, "The Library at the End of Weather", "10 - The Library at the End of Weather.mid",
                 2026071010, 84, 448, t10.build,
                 "contrapuntal chamber fantasy widening into a storm orchestra", (220, 340),
                 "Inside an impossible library, pages become birds as weather enters the stacks.",
                 850, 8, 6, 6, 4, ("free-choice",)),
    en.TrackSpec(11, "Clockwork Orchard", "11 - Clockwork Orchard.mid", 2026071011, 112, 432,
                 t11.build, "baroque counterpoint infiltrated by clocks, percussion, and synths", (190, 300),
                 "Mechanical time colonizes an orchard until living rubato breaks the grid.",
                 950, 8, 6, 6, 4, ("free-choice",)),
    en.TrackSpec(12, "Letters to a Future Ocean", "12 - Letters to a Future Ocean.mid", 2026071012, 66, 384,
                 t12.build, "slow luminous epistolary music with one symphonic storm", (260, 390),
                 "Messages travel through harp, piano, winds, strings, choir, storm, and receding water.",
                 650, 8, 6, 6, 3, ("free-choice",)),
    en.TrackSpec(13, "Night Market in Thirteen", "13 - Night Market in Thirteen.mid", 2026071013, 138, 442,
                 t13.build, "joyful 13/8 world-jazz and electronic percussion hocket", (170, 250),
                 "Vendor calls, modal improvisation, and a crooked dance share one crowded street.",
                 1100, 9, 6, 6, 4, ("free-choice",)),
    en.TrackSpec(14, "Every Door Opens at Once", "14 - Every Door Opens at Once.mid", 2026071014, 108, 576,
                 t14.build, "maximalist album-finale synthesis with a quiet epilogue", (240, 370),
                 "The album's materials meet, transform one another, and leave one door open.",
                 1400, 11, 8, 8, 5, ("free-choice",)),
]
