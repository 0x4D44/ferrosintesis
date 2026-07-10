"""t15_landing_lights — Track 15 "Landing Lights": the closer of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T15.  After the epic of the
Estuary Suite, a small and direct goodnight in F major: a music box says
the album's name very slowly, a bell whispers GOODNIGHT, and the lamp
goes out on a single high F.

Every headline claim below is a falsifiable oracle (oracles() was written
BEFORE the music; the track is composed to pass it):

 * The music box (GM 10) states the FABLE cell in exact 4x augmentation,
   six times, via material.play_cell(..., stretch=4.0) — the cell's silent
   L becomes a scored 2-beat rest inside every statement
   (`cell_augmentation`: onsets, pitches, durations and the empty L-span
   are all recomputed from material.FABLE_CELL, never re-typed).
 * The music box, strings, LOW choir bed and harp all sit at pan 64
   (the mono-collapse rule: ferrosintesis gives any off-centre channel
   a Haas micro-delay, and these narrowband ringing/sustained sources
   comb-filter the mono sum — measured -6.8 dB on a pan-56 box stem).
   Stereo width comes only from the tinkle bell, a sparse transient
   whisper, and the hall (generic check_pan + CENTERED_CHANNELS).
 * A tinkle bell (GM 112, new in ferrosintesis v0.11) whispers GOODNIGHT
   in Morse, timing taken verbatim from
   material.morse_rhythm(material.MORSE_T15) — `morse_goodnight` decodes
   the bell lane back to the text and caps its velocity at a whisper.
 * The final event of the whole piece is a single high F (F6, MIDI 89)
   fading for 16 beats under a written-out ritardando (`final_high_f`:
   pitch class F, octave >= 5, strictly nothing after it).  The album's
   last pitch is therefore its FIRST — T1 "Five Fables" opens on F — the
   double album closes on the first letter of its own name.
 * The whole last minute is one long decrescendo: after beat 144 every
   channel's note velocities and CC11 values only fall
   (`closing_decrescendo_midi`), and audio_checks() holds the RENDER to
   strictly falling RMS per 10-second window over the last 60 s plus a
   >= 10 dB total fade (`audio_final_decrescendo`).
 * The music box's statement velocities form the track's dramatic arc —
   four rising statements into the "flare", two falling ones into the
   fade (`statement_arc`); everything stays diatonic to F major
   (`f_major_diatonic`).

Deliberate near-silences (contract section 6, "velocity is not
audibility"): the Morse bell (vel ~36) is scored as a whisper, and the
final section deliberately decays below vel 40 — both are the design,
asserted by the oracles above.

Movements (4/4 throughout, 60 bpm easing to 51 in the final bars):
    i.   Glide Path         beats   0-16   strings bloom out of silence
    ii.  Approach Lights    beats  16-88   music-box statements 1-3
    iii. Goodnight          beats  88-112  the Morse whisper
    iv.  Flare              beats 112-140  statement 4, the gentle peak
    v.   Touchdown and Fade beats 140-204  statements 5-6, the last F
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 15
TITLE = 'Landing Lights'
FILE = '15 - Landing Lights.mid'
SEED = 20260915

COMMENT = ("Track 15, the closer: a music box says F-A-Bb-(rest)-E four "
           "times too slowly; a tinkle bell whispers GOODNIGHT in Morse; "
           "the last light is a single high F - the album's first pitch - "
           "fading.")

# ---------------------------------------------------------------------------
# Channels and fixed design data
# ---------------------------------------------------------------------------

CH_BOX = 0        # music box (GM 10) — the FABLE cell at 4x, pan 64
CH_STR = 1        # strings (GM 48) — sustained bed, pan 64
CH_CHOIR = 2      # choir (GM 52) — LOW bed (F2/C3), pan 64, CC70 vowels
CH_BELL = 3       # tinkle bell (GM 112) — the Morse whisper, the one
                  # off-centre voice (transient, so no mono comb)
CH_HARP = 4       # harp (GM 46) — answers and 1x cell echoes, pan 64

ROOT_BOX = 77             # F5: the cell root; pitches 77/81/82/88 (F A Bb E)
FINAL_F = 89              # F6: the album's last (and first) pitch
FINAL_T0 = 188.0          # the E of statement 6 ends here; F6 resolves it
FINAL_DUR = 16.0
FINAL_VEL = 26            # scored near-silence: the lamp going out
STRETCH = 4.0             # the T15 augmentation factor (HLD through-line)

# Music-box statement grid: (start_beat, vel, vel_end-or-None).  Four
# rising statements toward the flare, two falling into the fade.
# Statement 5 sits at 146 so its long E (156-162) still rings inside
# the 10-s analysis window before statement 6 — the rendered last
# minute must fall window over window, with no silent hole for
# statement 6 to swell out of (audio_final_decrescendo).
STATEMENTS: tuple[tuple[float, int, int | None], ...] = (
    (16.0, 58, None),
    (40.0, 62, None),
    (64.0, 66, None),
    (112.0, 72, None),          # the peak ("Flare")
    (146.0, 56, 50),
    (172.0, 36, 30),            # ...its E resolves to FINAL_F at 188
)

MORSE_T0 = 89.0           # the bell starts one beat into "Goodnight"
MORSE_UNIT = 0.25         # dit = a sixteenth at 60 bpm
BELL_PITCH = 84           # C6 — diatonic, clear of the box's F/A/Bb/E
MORSE_VEL = 36            # a whisper, scored (oracle caps it at 40)

DECRESC_T0 = 144.0        # from here on, velocities and CC11 only fall

_TICK = 1.0 / en.PPQ

# F major pitch classes (F G A Bb C D E)
_F_MAJOR_PCS = {5, 7, 9, 10, 0, 2, 4}

# M2/M4 harmony as pitch-class sets, all diatonic to F major.
_F, _Gm, _Am, _Bb, _C, _Dm = ([5, 9, 0], [7, 10, 2], [9, 0, 4],
                              [10, 2, 5], [0, 4, 7], [2, 5, 9])
_M2_CHORDS = [_F, _Dm, _Bb, _C, _F, _Am, _Bb, _Gm,
              _F, _Dm, _Bb, _C, _F, _Gm, _Am, _Bb, _C, _C]   # 18 x 4 beats
_M4_CHORDS = [_F, _Bb, _F, _Dm, _Gm, _C, _F]                 # 7 x 4 beats

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("i. Glide Path", 0.0, 16.0),
        ("ii. Approach Lights", 16.0, 88.0),
        ("iii. Goodnight", 88.0, 112.0),
        ("iv. Flare", 112.0, 140.0),
        ("v. Touchdown and Fade", 140.0, 204.0),
    ],
    # A written-out ritardando: the music box winds down with the piece.
    tempo_map=[(0.0, 60.0), (168.0, 57.0), (176.0, 55.0),
               (184.0, 53.0), (192.0, 51.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 0)],                  # F major (one flat)
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_BOX, "music box", 10, 100, 64, 62),
        (CH_STR, "strings bed", 48, 90, 64, 58),
        (CH_CHOIR, "low choir", 52, 86, 64, 60),
        (CH_BELL, "tinkle bell", 112, 92, 74, 66),
        (CH_HARP, "harp", 46, 96, 64, 55),
    ],
    bank_selects=[(3, 1)],   # tinkle bell: percussion set B
    extra_markers=[
        (MORSE_T0, "tinkle bell taps GOODNIGHT"),
        (FINAL_T0, "last light: high F - the album's first pitch"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {10, 46, 48, 52, 112}
# Every ringing/sustained voice is centred (mono-collapse rule); only
# the transient tinkle bell carries pan width.
CENTERED_CHANNELS: set[int] = {CH_BOX, CH_STR, CH_CHOIR, CH_HARP}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_BOX: (72, 91),
    CH_STR: (48, 84),
    CH_CHOIR: (36, 60),      # the LOW bed: F2/C3 only, floored above C2
    CH_BELL: (80, 88),
    CH_HARP: (41, 86),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (205.0, 216.0)   # ~3:31 written file
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------

def _m1_glide_path(sc: en.Score) -> None:
    """[0, 16) Strings bloom out of silence on an F chord; the low choir
    hum enters at bar 3; the harp climbs the tonic triad — landing lights
    appearing one by one."""
    en.cc_curve(sc, CH_STR, 11, [(0.0, 26), (8.0, 50), (15.5, 58)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(7.5, 26), (15.5, 44)], step=1.0)
    en.vowel(sc, CH_CHOIR, 0, 7.5)                        # closed "mm"
    sc.note(CH_STR, 53, 0.0, 16.0, 40, jt=0, jv=2)        # F3
    sc.note(CH_STR, 60, 4.0, 12.0, 40, jt=3, jv=2)        # C4
    sc.note(CH_STR, 57, 8.0, 8.0, 42, jt=3, jv=2)         # A3
    sc.note(CH_STR, 65, 12.0, 4.0, 42, jt=3, jv=2)        # F4
    sc.note(CH_CHOIR, 41, 8.0, 7.9, 40, jt=3, jv=2)       # F2
    for beat, p, v in ((4.0, 53, 40), (6.0, 60, 42), (8.0, 69, 44),
                       (10.0, 72, 44), (12.0, 77, 46)):
        sc.note(CH_HARP, p, beat, 3.5 if p == 77 else 2.5, v, jt=3, jv=2)


def _m2_approach_lights(sc: en.Score) -> None:
    """[16, 88) The music box states the cell three times (rising 58, 62,
    66); voice-led string pads and the F2/C3 choir pedal underneath; the
    harp answers each statement with a rising tonic arpeggio."""
    en.cc_curve(sc, CH_STR, 11, [(16.0, 58), (28.0, 64), (40.0, 60),
                                 (52.0, 68), (64.0, 63), (76.0, 70),
                                 (87.5, 60)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(16.0, 44), (36.0, 52), (56.0, 56),
                                   (76.0, 54), (87.5, 50)], step=1.0)
    en.vowel_curve(sc, CH_CHOIR, [(16.0, 0), (48.0, 18), (87.5, 30)],
                   step=2.0)
    en.pad_block(sc, CH_STR, 16.0, _M2_CHORDS, span=4.0, size=4,
                 lo=53, hi=79, vel=42, vel_end=48, legato=0.2)
    for k, v in enumerate((42, 43, 44, 45, 46, 46, 45, 44, 44)):
        sc.note(CH_CHOIR, 41, 16.0 + 8.0 * k, 7.9, v, jt=3, jv=2)
    for k in range(5):
        sc.note(CH_CHOIR, 48, 48.0 + 8.0 * k, 7.9, 42 + (k % 2), jt=3, jv=2)
    for t0, vel, vel_end in STATEMENTS[:3]:
        material.play_cell(sc, CH_BOX, t0, ROOT_BOX, stretch=STRETCH,
                           vel=vel, vel_end=vel_end, jt=0, jv=1)
    for t, v in ((32.5, 44), (56.5, 46), (80.5, 46)):
        en.arp(sc, CH_HARP, [53, 60, 65, 69, 72, 77], t, count=6,
               step=0.5, vel=v, gate=1.2)


def _m3_goodnight(sc: en.Score) -> None:
    """[88, 112) The beds thin to a held F triad and the choir opens to
    "oo"; over them the tinkle bell whispers GOODNIGHT in Morse, timing
    verbatim from material.morse_rhythm.  The music box listens."""
    en.cc_curve(sc, CH_STR, 11, [(88.0, 52), (100.0, 48), (111.5, 46)],
                step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(88.0, 52), (96.0, 58), (111.5, 50)],
                step=1.0)
    en.vowel_curve(sc, CH_CHOIR, [(88.0, 32), (92.0, 45), (106.0, 45),
                                  (111.5, 25)], step=1.0)
    for p in (53, 57, 60):
        sc.note(CH_STR, p, 88.0, 12.1, 40, jt=3, jv=2)
    for p in (53, 60, 65):
        sc.note(CH_STR, p, 100.0, 12.0, 38, jt=3, jv=2)
    for k, v in enumerate((46, 46, 44)):
        sc.note(CH_CHOIR, 41, 88.0 + 8.0 * k, 7.9, v, jt=3, jv=2)
        sc.note(CH_CHOIR, 48, 88.0 + 8.0 * k, 7.9, v - 2, jt=3, jv=2)
    for on, dur in material.morse_rhythm(material.MORSE_T15, MORSE_UNIT):
        sc.note(CH_BELL, BELL_PITCH, MORSE_T0 + on, dur, MORSE_VEL,
                jt=0, jv=2)


def _m4_flare(sc: en.Score) -> None:
    """[112, 140) The gentle peak: statement 4 at vel 72 over the fullest
    pads of the piece; the harp answers up, then down — the nose lifts
    once before touchdown."""
    en.cc_curve(sc, CH_STR, 11, [(112.0, 60), (120.0, 70), (128.0, 74),
                                 (134.0, 68), (139.5, 64)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(112.0, 56), (122.0, 62), (132.0, 58),
                                   (139.5, 56)], step=1.0)
    en.vowel_curve(sc, CH_CHOIR, [(112.0, 22), (126.0, 12), (139.5, 8)],
                   step=2.0)
    en.pad_block(sc, CH_STR, 112.0, _M4_CHORDS, span=4.0, size=4,
                 lo=53, hi=81, vel=48, vel_end=52, legato=0.2)
    for k, v in enumerate((48, 48, 46, 44)):
        du = 7.9 if k < 3 else 3.9
        sc.note(CH_CHOIR, 41, 112.0 + 8.0 * k, du, v, jt=3, jv=2)
        sc.note(CH_CHOIR, 48, 112.0 + 8.0 * k, du, v - 2, jt=3, jv=2)
    t0, vel, vel_end = STATEMENTS[3]
    material.play_cell(sc, CH_BOX, t0, ROOT_BOX, stretch=STRETCH,
                       vel=vel, vel_end=vel_end, jt=0, jv=1)
    en.arp(sc, CH_HARP, [53, 60, 65, 69, 72, 77], 128.5, count=6,
           step=0.5, vel=48, gate=1.2)
    en.arp(sc, CH_HARP, [77, 72, 69, 65, 60, 53], 133.0, count=6,
           step=0.5, vel=46, gate=1.2)
    en.arp(sc, CH_HARP, [53, 60, 65], 136.5, count=3, step=0.5, vel=44,
           gate=1.2)


def _m5_touchdown(sc: en.Score) -> None:
    """[140, 204) The long fade.  Statements 5 and 6 wind down in velocity
    while the written ritardando slows the spring; the harp remembers the
    cell at its ORIGINAL 1x speed (the same DNA at two time scales); the
    beds thin voice by voice and are gone by 188, where statement 6's E
    resolves up to the piece's final event: one high F, alone, fading.
    From beat 144 every velocity and CC11 in the track only falls, and
    the box gets its own falling CC11 lane from 164 so the RENDER of
    statement 6 and the last F sits below the statement-5 window
    (audio_final_decrescendo: presence is not audibility)."""
    en.cc_curve(sc, CH_BOX, 11, [(164.0, 124), (172.0, 88), (188.0, 72),
                                 (203.0, 60)], step=1.0)
    en.cc_curve(sc, CH_STR, 11, [(140.0, 62), (152.0, 54), (164.0, 44),
                                 (176.0, 28), (187.5, 16)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(140.0, 56), (152.0, 48), (164.0, 38),
                                   (176.0, 24), (183.5, 14)], step=1.0)
    en.vowel_curve(sc, CH_CHOIR, [(140.0, 8), (160.0, 4), (180.0, 0)],
                   step=2.0)
    for t, ps, v in ((140.0, (53, 57, 60, 65), 44),
                     (148.0, (53, 57, 60), 42),
                     (156.0, (53, 60, 65), 40),
                     (164.0, (53, 60), 38),
                     (172.0, (53, 60), 36),
                     (180.0, (53, 60), 34)):
        for p in ps:
            sc.note(CH_STR, p, t, 8.0 if t == 180.0 else 8.1, v, jt=3, jv=1)
    for k, v in enumerate((44, 42, 40, 38, 36, 34)):
        sc.note(CH_CHOIR, 41, 140.0 + 8.0 * k, 7.9, v, jt=3, jv=1)
        sc.note(CH_CHOIR, 48, 140.0 + 8.0 * k, 7.9, v, jt=3, jv=1)
    t0, vel, vel_end = STATEMENTS[4]
    material.play_cell(sc, CH_BOX, t0, ROOT_BOX, stretch=STRETCH,
                       vel=vel, vel_end=vel_end, jt=0, jv=1)
    material.play_cell(sc, CH_HARP, 154.0, ROOT_BOX - 12, stretch=1.0,
                       vel=46, vel_end=42, jt=2, jv=1)
    material.play_cell(sc, CH_HARP, 162.0, ROOT_BOX - 12, stretch=1.0,
                       vel=40, vel_end=36, jt=2, jv=1)
    t0, vel, vel_end = STATEMENTS[5]
    material.play_cell(sc, CH_BOX, t0, ROOT_BOX, stretch=STRETCH,
                       vel=vel, vel_end=vel_end, jt=0, jv=1)
    sc.note(CH_BOX, FINAL_F, FINAL_T0, FINAL_DUR, FINAL_VEL, jt=0, jv=0)


BUILDERS: list = [_m1_glide_path, _m2_approach_lights, _m3_goodnight,
                  _m4_flare, _m5_touchdown]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the track is composed to pass them
# ---------------------------------------------------------------------------

_ALL_CHANNELS = (CH_BOX, CH_STR, CH_CHOIR, CH_BELL, CH_HARP)


def _notes(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """[(on_beat, dur_beats, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[int, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on / en.PPQ, (tick - on) / en.PPQ,
                            data[1], vel))
    return sorted(out)


def _ccs(sc: en.Score, ch: int, num: int) -> list[tuple[float, int]]:
    return sorted((tick / en.PPQ, data[2])
                  for tick, _prio, data in sc.events.get(ch, [])
                  if (data[0] & 0xF0) == 0xB0 and data[1] == num)


def _decode_morse(taps: list[tuple[float, float]], unit: float) -> str:
    """Decode (onset, dur) taps back to text using standard Morse timing."""
    inverse = {code: letter for letter, code in material.MORSE_TABLE.items()}
    words: list[str] = []
    letters: list[str] = []
    symbol = ""
    prev_end: float | None = None
    for on, dur in taps:
        if prev_end is not None:
            gap_units = (on - prev_end) / unit
            if gap_units > 5.0:                    # word gap (7 units)
                letters.append(inverse.get(symbol, "?"))
                symbol = ""
                words.append("".join(letters))
                letters = []
            elif gap_units > 2.0:                  # letter gap (3 units)
                letters.append(inverse.get(symbol, "?"))
                symbol = ""
        symbol += "." if dur < 2.0 * unit else "-"
        prev_end = on + dur
    if symbol:
        letters.append(inverse.get(symbol, "?"))
    if letters:
        words.append("".join(letters))
    return " ".join(words)


def _check_cell_augmentation(sc) -> list[str]:
    """The music-box lane is EXACTLY six 4x-augmented FABLE cells plus the
    final F — onsets, pitches, durations and the 2-beat silent L are all
    recomputed from material.py."""
    fails = []
    box = _notes(sc, CH_BOX)
    expected: list[tuple[float, float, int]] = []
    for t0, _v, _ve in STATEMENTS:
        for on, du, semi in material.FABLE_CELL:
            expected.append((t0 + on * STRETCH, du * STRETCH,
                             ROOT_BOX + semi))
    expected.append((FINAL_T0, FINAL_DUR, FINAL_F))
    expected.sort()
    if len(box) != len(expected):
        fails.append(f"music box has {len(box)} notes, want "
                     f"{len(expected)} (6 cells + the final F)")
        return fails
    for (on, du, p, _v), (eon, edu, ep) in zip(box, expected):
        if abs(on - eon) > 1.5 * _TICK:
            fails.append(f"box onset {on:.4f} != augmented cell {eon:.4f}")
        if p != ep:
            fails.append(f"box pitch {p} at beat {on:.2f} != cell {ep}")
        if abs(du - edu) > 3.0 * _TICK:
            fails.append(f"box duration {du:.3f} at beat {on:.2f} != "
                         f"augmented {edu:.3f}")
    l0, l1 = material.FABLE_SILENT_L
    if (l1 - l0) * STRETCH != 2.0:
        fails.append("the augmented silent L is not 2 beats")
    for t0, _v, _ve in STATEMENTS:
        lo, hi = t0 + l0 * STRETCH, t0 + l1 * STRETCH
        for on, _du, _p, _vv in box:
            if lo - 1e-6 <= on < hi - 1e-6:
                fails.append(f"box note at {on:.2f} inside the silent L "
                             f"[{lo:.1f}, {hi:.1f}) of the cell at {t0:.0f}")
    return fails


def _check_morse_goodnight(sc) -> list[str]:
    """The bell lane matches material.morse_rhythm(MORSE_T15) verbatim,
    decodes back to GOODNIGHT, and stays a whisper (vel <= 40)."""
    fails = []
    bell = _notes(sc, CH_BELL)
    want = material.morse_rhythm(material.MORSE_T15, MORSE_UNIT)
    if len(bell) != len(want):
        fails.append(f"bell taps {len(bell)} symbols, want {len(want)}")
        return fails
    for (on, du, _p, _v), (won, wdu) in zip(bell, want):
        if abs(on - (MORSE_T0 + won)) > 1.5 * _TICK:
            fails.append(f"bell onset {on:.4f} != morse {MORSE_T0 + won:.4f}")
        if abs(du - wdu) > 3.0 * _TICK:
            fails.append(f"bell dur {du:.3f} at beat {on:.2f} != {wdu:.3f}")
    decoded = _decode_morse([(on, du) for on, du, _p, _v in bell],
                            MORSE_UNIT)
    if decoded != material.MORSE_T15:
        fails.append(f"bell decodes to {decoded!r}, want "
                     f"{material.MORSE_T15!r}")
    for on, _du, _p, v in bell:
        if v > 40:
            fails.append(f"bell vel {v} at beat {on:.2f} is no whisper "
                         f"(cap 40)")
    return fails


def _check_final_high_f(sc) -> list[str]:
    """The piece's last event is ONE high F (pc 5, octave >= 5) on the
    music box, long and quiet, at least a beat clear of everything else."""
    fails = []
    everything = [(on, du, p, v, ch) for ch in _ALL_CHANNELS
                  for on, du, p, v in _notes(sc, ch)]
    if not everything:
        return ["the piece is empty"]
    last_on = max(on for on, _du, _p, _v, _ch in everything)
    finals = [x for x in everything if x[0] > last_on - 1e-6]
    if len(finals) != 1:
        fails.append(f"{len(finals)} simultaneous final events, want 1")
        return fails
    on, du, p, v, ch = finals[0]
    if p % 12 != 5:
        fails.append(f"final pitch {p} is not pitch-class F")
    if p // 12 - 1 < 5:
        fails.append(f"final pitch {p} is below octave 5")
    if ch != CH_BOX:
        fails.append(f"final note is on ch{ch}, not the music box")
    if du < 8.0:
        fails.append(f"final F holds only {du:.1f} beats (< 8): no fade")
    if v > 45:
        fails.append(f"final F vel {v} is not quiet (cap 45)")
    runner_up = max(o for o, _d, _p2, _v2, _c in everything
                    if o < on - 1e-6)
    if runner_up > on - 1.0:
        fails.append(f"a note at beat {runner_up:.2f} crowds the final F "
                     f"at {on:.2f} (< 1 beat clear)")
    return fails


def _check_closing_decrescendo(sc) -> list[str]:
    """From beat 144 to the end, per channel: note velocities never rise
    (tolerance +2 for the seeded +-1/2 jitter) and CC11 never rises."""
    fails = []
    for ch in _ALL_CHANNELS:
        tail = [x for x in _notes(sc, ch) if x[0] >= DECRESC_T0 - 1e-9]
        for (on1, _d1, _p1, v1), (on2, _d2, _p2, v2) in zip(tail, tail[1:]):
            if v2 > v1 + 2:
                fails.append(f"ch{ch} vel rises {v1}->{v2} at beat "
                             f"{on2:.2f} inside the closing decrescendo")
        ccs = [x for x in _ccs(sc, ch, 11) if x[0] >= DECRESC_T0 - 1e-9]
        for (b1, v1), (b2, v2) in zip(ccs, ccs[1:]):
            if v2 > v1:
                fails.append(f"ch{ch} CC11 rises {v1}->{v2} at beat "
                             f"{b2:.2f} inside the closing decrescendo")
    return fails


def _check_statement_arc(sc) -> list[str]:
    """Statement first-note velocities rise strictly to the flare
    (s1<s2<s3<s4), then fall strictly (s4>s5>s6>final F)."""
    fails = []
    box = _notes(sc, CH_BOX)
    firsts: list[int] = []
    for t0, _v, _ve in STATEMENTS:
        hits = [v for on, _du, _p, v in box if abs(on - t0) <= 2 * _TICK]
        if len(hits) != 1:
            fails.append(f"statement at beat {t0:.0f}: {len(hits)} "
                         f"first-note candidates")
            return fails
        firsts.append(hits[0])
    for a, b in zip(firsts[:3], firsts[1:4]):
        if not a < b:
            fails.append(f"rising arc broken: statement vels {firsts[:4]}")
            break
    for a, b in zip(firsts[3:], firsts[4:]):
        if not a > b:
            fails.append(f"falling arc broken: statement vels {firsts[3:]}")
            break
    final_vel = [v for on, _du, p, v in box
                 if p == FINAL_F and abs(on - FINAL_T0) <= 2 * _TICK]
    if not final_vel or final_vel[0] >= firsts[-1]:
        fails.append(f"final F vel {final_vel} not below statement 6's "
                     f"{firsts[-1]}")
    return fails


def _check_f_major_diatonic(sc) -> list[str]:
    """Small and direct: every pitched note is diatonic to F major."""
    fails = []
    for ch in _ALL_CHANNELS:
        for on, _du, p, _v in _notes(sc, ch):
            if p % 12 not in _F_MAJOR_PCS:
                fails.append(f"ch{ch} pitch {p} at beat {on:.2f} is not "
                             f"in F major")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("cell_augmentation", _check_cell_augmentation(sc)),
        ("morse_goodnight", _check_morse_goodnight(sc)),
        ("final_high_f", _check_final_high_f(sc)),
        ("closing_decrescendo_midi", _check_closing_decrescendo(sc)),
        ("statement_arc", _check_statement_arc(sc)),
        ("f_major_diatonic", _check_f_major_diatonic(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/15 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The headline dynamics claim, held against the RENDER: over the last
    60 s of the piece the stereo RMS falls STRICTLY from each 10-s window
    to the next, and the minute as a whole fades by >= 10 dB.  Windows are
    anchored at the score's musical end (ctx.sc.duration_seconds()), so a
    renderer tail of silence cannot shift them."""
    end_s = ctx.sc.duration_seconds()
    rate = ctx.sample_rate
    n = len(ctx.l)
    vals: list[float] = []
    for k in range(6):
        t0 = end_s - 60.0 + 10.0 * k
        i0 = max(0, min(n, int(t0 * rate)))
        i1 = max(0, min(n, int((t0 + 10.0) * rate)))
        vals.append(ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1)))
    fails = []
    for k, (a, b) in enumerate(zip(vals, vals[1:])):
        if b >= a:
            fails.append(f"10s window {k + 1}->{k + 2}: RMS {a:.1f} -> "
                         f"{b:.1f} dB (each window must be quieter)")
    if vals and vals[-1] > vals[0] - 10.0:
        fails.append(f"the last minute fades only "
                     f"{vals[0] - vals[-1]:.1f} dB (want >= 10)")
    return [("audio_final_decrescendo", fails)]
