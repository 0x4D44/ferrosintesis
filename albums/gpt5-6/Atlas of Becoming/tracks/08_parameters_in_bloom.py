"""Parameters in Bloom — an original symbolic history of language models."""

from __future__ import annotations

import engine as en
from . import common as c

ROOT = 43  # G2: a low seed grows upward across the piece
SEED = [0, 2, 1, 4, 3]

MILESTONES = [
    (0, "GPT-1: Seed Token", 72, (4, 4), "minor"),
    (36, "GPT-2: Wider Window", 76, (5, 4), "minor"),
    (72, "GPT-3: Few-Shot Constellation", 80, (4, 4), "dorian"),
    (108, "InstructGPT: Human Arrow", 84, (3, 4), "dorian"),
    (144, "GPT-3.5: Conversation Loop", 88, (6, 8), "mixolydian"),
    (180, "GPT-4: Deep Polyphony", 82, (7, 8), "minor"),
    (220, "GPT-4 Turbo: Compressed Distance", 96, (4, 4), "dorian"),
    (260, "GPT-4o: Sight Sound Text", 100, (12, 8), "lydian"),
    (300, "o1 reasoning counterline", 68, (5, 4), "harmonic"),
    (340, "GPT-4.5: Warm Bridge", 88, (4, 4), "major"),
    (380, "GPT-4.1: Precise Return", 94, (7, 8), "mixolydian"),
    (420, "o3/o4-mini tool-use branch", 102, (11, 8), "dorian"),
    (460, "GPT-5: Joined Streams", 98, (4, 4), "dorian"),
    (500, "GPT-5.1: Stable Weave", 104, (6, 8), "major"),
    (540, "GPT-5.2: Longer Horizon", 108, (4, 4), "lydian"),
    (576, "GPT-5.3: Quickened Spark", 112, (5, 4), "mixolydian"),
    (612, "GPT-5.4: Architectural Chorus", 116, (7, 8), "lydian"),
    (652, "GPT-5.5 Current Chorus", 120, (4, 4), "major"),
]


def _seed_phrase(sc: en.Score, ch: int, mode: str, start: float, vel: int, octave: int, expand: int) -> None:
    offsets = [0.0, 0.75, 1.5, 2.0, 3.0]
    durations = [0.55, 0.55, 0.35, 0.7, 0.9]
    for i, degree in enumerate(SEED):
        # Each generation gets a slightly wider interval vocabulary while retaining identity.
        grown = degree + (expand // 4 if i == 3 else 0) + (expand // 7 if i == 4 else 0)
        sc.note(ch, en.pitch(ROOT, mode, grown, octave), start + offsets[i], durations[i], vel + i * 2, jt=1, jv=2)


def build(sc: en.Score) -> None:
    c.setup_band(sc, [
        (0, "seed voice", 80, 93, 64, 48, 13, 12),
        (1, "context piano", 0, 98, 64, 39, 8, 5),
        (2, "parameter strings", 48, 86, 64, 72, 23, 7),
        (3, "token bass", 33, 104, 64, 24, 0, 0),
        (4, "instruction clarinet", 71, 88, 44, 54, 8, 15),
        (5, "vision flute", 73, 88, 82, 63, 14, 18),
        (6, "audio choir", 52, 78, 64, 78, 24, 12),
        (7, "spatial marimba", 12, 88, 25, 44, 10, 20),
        (8, "reasoning cello", 42, 94, 64, 58, 12, 8),
        (10, "tool call guitar", 27, 92, 35, 35, 8, 18),
        (11, "tool response brass", 61, 94, 93, 49, 7, 8),
        (9, "training clock", None, 104, 64, 32, 0, 0),
    ])

    for i, (start, name, bpm, meter, mode) in enumerate(MILESTONES):
        c.section(sc, start, name, bpm, meter)
        end = MILESTONES[i + 1][0] if i + 1 < len(MILESTONES) else 720
        span = end - start

        # The original five-token seed stays audible while harmony and context accumulate.
        phrase_step = 8.0 if i < 3 else (6.0 if i < 9 else 4.0)
        phrase = start + (8.0 if i == 0 else 0.0)
        entry = 0
        while phrase + 3.9 < end:
            _seed_phrase(sc, 0, mode, phrase, 49 + min(44, i * 3), 1 + (i >= 12), i)
            if i >= 2 and entry % 2 == 1:
                _seed_phrase(sc, 4, mode, phrase + 1.5, 42 + min(36, i * 2), 2, i // 2)
            phrase += phrase_step
            entry += 1

        # Context begins as a single held answer and grows to four-note memory blocks.
        bars = max(1, int(span / 4.0))
        degrees = [0, 3, 5, 1, 4, 2, 6, 3]
        for bar in range(bars):
            b = start + bar * 4.0
            size = 1 if i == 0 else min(4, 2 + i // 3)
            notes = en.chord(ROOT, mode, degrees[(bar + i) % len(degrees)], size=size, octave=0)
            en.pad(sc, 2, notes, b, min(4.05, end - b), 28 + min(34, i * 2))
            if i >= 1:
                tone = notes[(bar + i) % len(notes)] + 12
                sc.note(1, tone, b + 0.5, min(2.8, end - b - 0.5), 47 + min(37, i * 2), jt=2, jv=3)

        c.bass_pattern(sc, 3, ROOT - 12, mode, degrees, start, bars, 4.0,
                       45 + min(43, i * 3), anticipation=i >= 4)

        # Successive capabilities arrive as independent musical dimensions.
        if i >= 2:
            step = 1.0 if i < 6 else (0.5 if i < 12 else 0.25)
            context_degrees = [0, 2, 1, 4, 3, 6, 5, 8, 7, 4, 2, 5]
            count = int(span / step)
            for k in range(count):
                ch = 1 if i < 7 else (1, 4, 7)[k % 3]
                octave = 1 + (k // 16) % 2
                sc.note(ch, en.pitch(ROOT, mode, context_degrees[(k + i) % len(context_degrees)], octave),
                        start + k * step, step * 0.72, 49 + min(43, i * 2) + (k % 8 == 0) * 8,
                        jt=1, jv=2)

        if i >= 7:  # GPT-4o: three media share one time-line without becoming unison.
            for k in range(int(span / 1.0)):
                beat = start + k
                deg = (SEED[k % len(SEED)] + k // 8) % 11
                sc.note(5, en.pitch(ROOT + 12, mode, deg, 1), beat, 0.72, 62 + min(28, i), jt=1, jv=2)
                if k % 2 == 0:
                    sc.note(6, en.pitch(ROOT, mode, deg + 2, 0), beat + 0.24, 1.3, 43 + i, jt=1, jv=2)
                if k % 3 == 0:
                    sc.note(7, en.pitch(ROOT + 12, mode, deg + 4, 1), beat + 0.48, 0.38, 59 + i, jt=1, jv=2)

        if i >= 8:  # Deliberate silence inside each reasoning unit is part of the counterline.
            for k in range(int(span / 0.5)):
                if k % 12 in (4, 5, 10):
                    continue
                degree = [0, 3, 2, 6, 5, 1, 4, 7, 3][(k + i) % 9]
                sc.note(8, en.pitch(ROOT - 12, mode, degree, 0), start + k * 0.5,
                        0.42 if k % 4 else 0.8, 58 + min(36, i * 2), jt=1, jv=2)

        if i >= 11:  # Tool calls on the left receive transformed brass answers on the right.
            for call in range(int(span / 4.0)):
                b = start + call * 4.0
                degree = [0, 4, 1, 5, 2, 6][(call + i) % 6]
                for n in range(4):
                    sc.note(10, en.pitch(ROOT + 12, mode, degree + n, 1), b + n * 0.5,
                            0.32, 69 + min(29, i), jt=1, jv=2)
                answer = en.chord(ROOT, mode, degree + 2, size=3, octave=1)
                for p in answer:
                    sc.note(11, p, b + 2.5, 0.72, 73 + min(25, i), jt=1, jv=2)

        # The training clock changes from sparse supervision to a quick collaborative pulse.
        if i == 0:
            for b in range(int(start + 16), int(end), 8):
                sc.hit(37, b, 40)
        else:
            subdivision = 1.0 if i < 4 else (0.5 if i < 11 else 0.25)
            c.drum_groove(sc, start, bars, 4.0, 52 + min(47, i * 3), subdivision=subdivision,
                          toms=i in (5, 8, 11, 17))

    # The o-series counterline is not a side ending: it rises into and supports GPT-5's chorus.
    en.cc_curve(sc, 8, 11, [(300, 42), (420, 78), (460, 92), (612, 106), (719, 84)], 1.0)
    for ch in (0, 1, 2, 5, 6, 8, 10, 11):
        c.expression_arc(sc, ch, 612, 720, 58, 119, 82)
    sc.sustain(1, 652, 719.5)

    c.feature(sc, "seed grows into current chorus", 0, 8, 716, {80}, min_notes=120, monophonic=True)
    c.feature(sc, "reasoning counterline feeds GPT-5", 8, 300, 720, {42}, min_notes=120, monophonic=True)
    c.feature(sc, "tool call and response branch", 10, 420, 720, {27}, min_notes=80, monophonic=True)
