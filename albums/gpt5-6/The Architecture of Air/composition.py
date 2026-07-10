"""The score for *The Architecture of Air*.

The piece is written around ferrosintesis' default GM19 cathedral model.  Its
measurement windows are part of the form: the opening pedal, tremulant study,
wind-chest plenum, high mixtures, and final room decay are all real musical
moments rather than detached test tones.
"""

from __future__ import annotations

import engine as en


ORGAN = 0
CHOIR = 1
BELLS = 2
TIMPANI = 3

TITLE = "The Architecture of Air"
FILENAME = "01 - The Architecture of Air.mid"
SEED = 2026071019
BEATS = 512.0


SECTIONS = (
    (0.0, "I. Stone Before Breath", 58.0, (5, 4)),
    (40.0, "II. The Principal Walk", 72.0, (4, 4)),
    (104.0, "III. The Vault Answers", 88.0, (7, 8)),
    (176.0, "IV. Tremulant Light", 66.0, (3, 4)),
    (240.0, "V. Windchest", 96.0, (4, 4)),
    (336.0, "VI. Mixtures in the Lantern", 84.0, (12, 8)),
    (416.0, "VII. Full Organ", 78.0, (4, 4)),
    (456.0, "VIII. The Building Sings", 60.0, (4, 4)),
    (480.0, "IX. Air After Stone", 60.0, (4, 4)),
)


# Named, deliberately isolated windows used by analyze.py.  Values are beats;
# build.py converts them through the score's tempo map for the manifest.
AUDIO_WINDOWS = {
    "pedal": (0.5, 7.5),
    "principals": (52.0, 68.0),
    "tremulant_off": (182.0, 191.0),
    "tremulant_on": (204.0, 215.0),
    "wind_loaded": (255.0, 259.5),
    "wind_recovery": (261.0, 267.0),
    "mixtures": (337.0, 351.0),
    "climax": (458.0, 478.0),
    "tail_early": (480.2, 484.0),
    "tail_late": (486.0, 492.0),
    "tail_floor": (500.0, 508.0),
}


def _organ_chord(
    sc: en.Score,
    pitches: list[int] | tuple[int, ...],
    beat: float,
    duration: float,
    velocity: int,
    stagger: float = 0.0,
) -> None:
    """Place a centered organ chord, optionally letting pipes speak in sequence."""
    for index, pitch in enumerate(pitches):
        sc.note(ORGAN, pitch, beat + index * stagger, duration - index * stagger,
                velocity, jt=0, jv=2)


def _line(
    sc: en.Score,
    pitches: list[int] | tuple[int, ...],
    start: float,
    step: float,
    duration: float,
    velocity: int,
) -> None:
    for index, pitch in enumerate(pitches):
        sc.note(ORGAN, pitch, start + index * step, duration, velocity,
                jt=1, jv=2)


def _foundation(sc: en.Score) -> None:
    # Seven seconds of exposed C: MIDI 36 excites 32', 16' and 8' energy while
    # the dedicated room has time to establish its physical scale.
    sc.note(ORGAN, 36, 0.0, 8.0, 74, jt=0, jv=0)
    _organ_chord(sc, [36, 48, 55, 60], 12.0, 8.0, 70, stagger=0.08)
    _organ_chord(sc, [34, 46, 53, 58, 62], 22.0, 8.0, 73, stagger=0.07)
    _organ_chord(sc, [31, 43, 50, 55, 59, 62], 32.0, 7.5, 76, stagger=0.06)


def _principal_walk(sc: en.Score) -> None:
    chords = (
        ([36, 48, 55, 60, 64], [72, 74, 77, 76]),
        ([34, 46, 53, 58, 62], [70, 72, 74, 77]),
        ([31, 43, 50, 55, 59], [67, 69, 72, 74]),
        ([33, 45, 52, 57, 60], [69, 72, 76, 74]),
    )
    for cycle in range(2):
        for index, (harmony, melody) in enumerate(chords):
            beat = 40.0 + cycle * 32.0 + index * 8.0
            _organ_chord(sc, harmony, beat, 7.5, 74 + cycle * 5, stagger=0.035)
            _line(sc, melody, beat + 0.5, 1.75, 1.35, 77 + cycle * 5)


def _vault(sc: en.Score) -> None:
    upper = [60, 62, 65, 64, 67, 69, 65, 62]
    lower = [48, 50, 53, 52, 55, 57, 53, 50]
    pedals = [36, 34, 31, 33]
    for phrase in range(4):
        start = 104.0 + phrase * 18.0
        pedal = pedals[phrase]
        sc.note(ORGAN, pedal, start, 16.5, 76 + phrase * 3, jt=0, jv=1)
        _line(sc, [pitch + (12 if phrase >= 2 else 0) for pitch in upper],
              start, 2.0, 1.55, 79 + phrase * 3)
        _line(sc, lower, start + 1.0, 2.0, 1.45, 70 + phrase * 3)
        if phrase in (1, 3):
            _organ_chord(sc, [48, 55, 60, 64, 67], start + 14.0, 3.5,
                         82 + phrase * 3, stagger=0.025)

    # Human voices appear only after the organ counterpoint has established
    # itself, and remain centered so the room owns the width.
    for beat, chord in ((120.0, [48, 55, 60]), (138.0, [46, 53, 58]),
                        (156.0, [43, 50, 55])):
        for pitch in chord:
            sc.note(CHOIR, pitch + 12, beat, 12.0, 45, jt=2, jv=2)


def _tremulant(sc: en.Score) -> None:
    # One uninterrupted consonance makes CC1's fixed 5.5 Hz breathing audible:
    # off, ramp, full plateau, then release.  A high cantus floats above without
    # masking the amplitude motion.
    _organ_chord(sc, [36, 48, 55, 60, 64], 178.0, 54.0, 78, stagger=0.03)
    cantus = [72, 74, 77, 81, 79, 77, 74, 72, 76, 79, 84, 81]
    _line(sc, cantus, 180.0, 4.0, 2.7, 74)


def _windchest(sc: en.Score) -> None:
    # The first ten-note plenum is deliberately followed by one survivor.  All
    # ten notes share a channel, so the model's common chest actually loads.
    plenum = [36, 43, 48, 52, 55, 60, 64, 67, 72, 76]
    _organ_chord(sc, [36, 48, 55, 60, 64, 67], 240.0, 8.0, 86, stagger=0.02)
    _organ_chord(sc, plenum, 252.0, 8.0, 92, stagger=0.0)
    sc.note(ORGAN, 48, 260.0, 8.0, 82, jt=0, jv=0)

    progressions = (
        [34, 41, 46, 50, 53, 58, 62, 65, 70, 74],
        [31, 38, 43, 47, 50, 55, 59, 62, 67, 71],
        [33, 40, 45, 48, 52, 57, 60, 64, 69, 72],
    )
    for group in range(3):
        base = 276.0 + group * 20.0
        _organ_chord(sc, progressions[group], base, 6.0, 91 + group * 5,
                     stagger=0.018)
        _line(sc, [76, 79, 81, 84, 81, 79, 76], base + 8.0, 1.5, 1.1,
              84 + group * 4)


def _mixtures(sc: en.Score) -> None:
    # The first fourteen beats are organ alone: no bells or cymbals can take
    # credit for the brilliant mixture ceiling.
    fanfare = [84, 88, 91, 96, 93, 100, 96, 91]
    _line(sc, fanfare, 336.0, 1.75, 1.35, 92)
    for group, root in enumerate((48, 46, 43, 45)):
        beat = 352.0 + group * 14.0
        _organ_chord(sc, [root - 12, root, root + 7, root + 12, root + 16],
                     beat, 11.5, 88 + group * 3, stagger=0.025)
        _line(sc, [84 + group, 88 + group, 91 + group, 96 + group,
                   93 + group, 88 + group], beat + 1.0, 1.6, 1.1,
              91 + group * 3)

    # Four distant bells answer only after the organ's high ranks are exposed.
    for index, pitch in enumerate((72, 79, 84, 91)):
        sc.note(BELLS, pitch, 408.0 + index * 2.0, 2.5, 66 + index * 4,
                jt=1, jv=1)


def _full_organ(sc: en.Score) -> None:
    rising = (
        [36, 48, 55, 60, 64, 72],
        [34, 46, 53, 58, 62, 70, 74],
        [31, 43, 50, 55, 59, 62, 67, 76],
        [33, 45, 52, 57, 60, 64, 69, 72, 81],
        [36, 43, 48, 52, 55, 60, 64, 67, 72, 84],
    )
    for index, chord in enumerate(rising):
        beat = 416.0 + index * 8.0
        _organ_chord(sc, chord, beat, 7.7, 94 + index * 5,
                     stagger=max(0.0, 0.045 - index * 0.008))
        sc.note(TIMPANI, 43 + index % 3, beat, 1.2, 78 + index * 7,
                jt=1, jv=2)

    for pitch in (60, 64, 67):
        sc.note(CHOIR, pitch, 424.0, 24.0, 55, jt=2, jv=2)

    # Global maximum: a true twelve-note plenum with the 32-foot C beneath it.
    # Every note releases at beat 480, leaving thirty-two slow beats for the room.
    final = [36, 43, 48, 52, 55, 60, 64, 67, 72, 76, 84, 88]
    _organ_chord(sc, final, 456.0, 24.0, 118, stagger=0.0)
    for beat, pitch, velocity in ((456.0, 43, 112), (460.0, 38, 104),
                                  (464.0, 43, 116), (472.0, 36, 120)):
        sc.note(TIMPANI, pitch, beat, 1.0, velocity, jt=1, jv=1)


def build(sc: en.Score) -> None:
    # CC0 priority is lower than Program Change in this engine, so the written
    # order is also guaranteed in the serialized stream.
    sc.cc(ORGAN, 0, 0, 0.0)
    sc.channel(ORGAN, "cathedral organ - great, swell, and pedal", 19,
               volume=112, pan=64, reverb=116, chorus=0, echo=0)
    sc.channel(CHOIR, "distant human choir", 52,
               volume=62, pan=64, reverb=78, chorus=8, echo=0)
    sc.channel(BELLS, "tower bells", 14,
               volume=70, pan=64, reverb=88, chorus=0, echo=0)
    sc.channel(TIMPANI, "ceremonial timpani", 47,
               volume=84, pan=64, reverb=54, chorus=0, echo=0)

    for beat, name, bpm, meter in SECTIONS:
        sc.marker(beat, name)
        if beat > 0:
            sc.tempo(beat, bpm)
        sc.timesig(beat, meter[0], meter[1])

    # Preserve the organ's own case and dedicated room: no Haas pan, chorus,
    # delay, generic filter sweep, pitch bend, or fake velocity crescendo.
    sc.cc(ORGAN, 0, 0, 0.0)
    sc.cc(ORGAN, 10, 64, 0.0)
    sc.cc(ORGAN, 91, 116, 0.0)
    sc.cc(ORGAN, 93, 0, 0.0)
    sc.cc(ORGAN, 94, 0, 0.0)
    en.cc_curve(sc, ORGAN, 11, [
        (0.0, 46), (40.0, 66), (104.0, 82), (176.0, 58),
        (240.0, 88), (336.0, 94), (416.0, 105), (456.0, 122),
        (480.0, 116), (511.0, 116),
    ], step=1.0)
    en.cc_curve(sc, ORGAN, 1, [
        (0.0, 0), (192.0, 0), (200.0, 112), (216.0, 112),
        (224.0, 0), (512.0, 0),
    ], step=0.5)

    _foundation(sc)
    _principal_walk(sc)
    _vault(sc)
    _tremulant(sc)
    _windchest(sc)
    _mixtures(sc)
    _full_organ(sc)

    sc.feature(en.Feature("32-foot foundation", ORGAN, 0.0, 40.0, {19},
                          min_notes=12, ccs={0: (0, 0), 91: (116, 116)}))
    sc.feature(en.Feature("fixed cathedral tremulant", ORGAN, 176.0, 232.0, {19},
                          min_notes=12, ccs={1: (0, 112)}))
    sc.feature(en.Feature("shared wind-chest plenum", ORGAN, 240.0, 336.0, {19},
                          min_notes=50))
    sc.feature(en.Feature("high mixture lanterns", ORGAN, 336.0, 416.0, {19},
                          min_notes=40))
    sc.feature(en.Feature("full-organ cadence", ORGAN, 416.0, 480.0, {19},
                          min_notes=40, ccs={11: (105, 122)}))
