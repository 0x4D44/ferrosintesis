"""t02_scaling_laws — Track 2 "Scaling Laws" of *Through Lines*.

Disc 1, 'Lines of Descent'.  HLD section 3, T2.  One theme — its rhythm
is the word CLAUDE in Morse code, taken verbatim from
material.morse_rhythm(material.MORSE_T2) — played through the model
generations, D dorian resolving at last into D major.  Seven eras, seven
movements, each marker naming a real release; the arrangement's
CAPABILITY SET grows monotonically era by era, and the growth itself is
the headline oracle.

Every headline claim below is a falsifiable oracle (oracles() was
written BEFORE the music; the track is composed to pass it):

 * `monotonic_capability` — for each era the tuple (channel count, set
   of authored CC numbers, velocity stddev, pitch range, tempo-event
   count in span) is <= / subset-of the next era's.  The beat-0 channel
   setup burst (CC7/10/91, program) is excluded; everything else counts.
 * `era1_morse_theme` — Claude 1's flute lane is exactly three theme
   statements whose onset/duration pattern EQUALS the CLAUDE Morse
   rhythm (17 symbols, dit=0.25 beat), pitches from THEME_DEGREES.
 * `era1_rigidity` — era 1 is ONE channel, every velocity exactly 80
   (jv=0), onsets hard-quantized to the sixteenth grid (jt=0), range
   within one octave, zero expressive CCs, zero bends/aftertouch, and a
   single tempo event (flat 100 bpm).
 * `era2_hallucination` — Claude 2 contains EXACTLY ONE non-diatonic
   note (C#5 at the theme's peak, beat 71 — the model overreaches), and
   the next phrase corrects it by step (C natural at beat 87).  The C#
   is also a prophecy: it is the very pitch class D major will make
   diatonic in the Fable 5 era.
 * `era6_first_bends` — no pitch bend exists anywhere before Claude 4.5
   (beat 448); bends appear there and remain in Fable 5.
 * `fable5_freedom` — the last era authors CC70 vowels, CC1 Leslie,
   channel aftertouch, bends, and an elastic tempo lane (>= 10 events,
   >= 15 bpm spread, closing ritardando), and the piece's final
   sounding chord is D MAJOR: pitch classes {D, F#, A} present, the
   major third F# explicitly, no F or C natural.
 * `modal_integrity` — before the pivot (beat 584) every note is
   diatonic to D dorian except the one documented hallucination; from
   the pivot on, every note is diatonic to D major.
 * `era_markers` — the seven movement markers name the releases.

Eras (4/4 throughout; D dorian, then D major at beat 584):
    i.   Claude 1 (2023)                    0-48    one flute, vel 80
    ii.  Claude 2                          48-112   parallel organum
    iii. Claude 3: Haiku, Sonnet, Opus    112-224   celesta/piano/strings
    iv.  Claude 3.5 / 3.7                 224-352   fugato, CC11, rubato
    v.   Claude 4                         352-448   full orchestra
    vi.  Claude 4.5                       448-528   space, first bends
    vii. Fable 5                          528-640   free; dorian -> major

Scored silences: the early models fall silent between phrases (the
2.25-beat rest after each 13.75-beat Morse statement in eras 1-2) —
GAP_WHITELIST names each one.  From era 3 on, sustained texture covers
the seams.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 2
TITLE = 'Scaling Laws'
FILE = '02 - Scaling Laws.mid'
SEED = 20260902

COMMENT = ("Track 02: one theme - the word CLAUDE in Morse - played "
           "through the model generations. Each era's capability set "
           "(channels, CCs, dynamics, range, tempo freedom) grows "
           "monotonically; D dorian resolves into D major at Fable 5.")

# ---------------------------------------------------------------------------
# Channels and fixed design data
# ---------------------------------------------------------------------------

CH_FLUTE = 0      # flute (GM 73) — the model's voice, present from era 1
CH_REC = 1        # recorder (GM 74) — the organum second voice
CH_CEL = 2        # celesta (GM 8) — Haiku
CH_PNO = 3        # piano (GM 0) — Sonnet
CH_STR = 4        # strings (GM 48) — Opus, sustained bed, pan 64
CH_OBOE = 5       # oboe (GM 68) — the fugato voice
CH_HORN = 6       # horns (GM 60) — era 4/Claude 4 brass
CH_TIMP = 7       # timpani (GM 47) — transient, slightly right
CH_CHOIR = 8      # choir (GM 52) — Fable 5 vowels (CC70)
CH_ORG = 10       # drawbar organ (GM 16) — Fable 5 Leslie (CC1)

MODE = "dorian"
MAJ = "ionian"
D2, D3, D4, D5, D6, D7 = 38, 50, 62, 74, 86, 98

THEME_UNIT = 0.25          # dit = one sixteenth
# One melodic degree per Morse symbol of CLAUDE (17 symbols):
#   C: dah dit dah dit | L: dit dah dit dit | A: dit dah
#   U: dit dit dah     | D: dah dit dit     | E: dit
THEME_DEGREES = (1, 3, 2, 1,   3, 4, 3, 2,   5, 7,
                 6, 5, 4,   3, 2, 1,   1)
# Symbol-index slices, one per letter of the word.
LETTERS = {"C": (0, 4), "L": (4, 8), "A": (8, 10),
           "U": (10, 13), "D": (13, 16), "E": (16, 17)}

_MORSE = material.morse_rhythm(material.MORSE_T2, THEME_UNIT)
THEME_SPAN = max(on + du for on, du in _MORSE)          # 13.75 beats

# Era grid: (marker name, start_beat, end_beat).
ERAS = [
    ("Claude 1 (2023)", 0.0, 48.0),
    ("Claude 2", 48.0, 112.0),
    ("Claude 3: Haiku, Sonnet, Opus", 112.0, 224.0),
    ("Claude 3.5 / 3.7 - extended thinking", 224.0, 352.0),
    ("Claude 4", 352.0, 448.0),
    ("Claude 4.5", 448.0, 528.0),
    ("Fable 5", 528.0, 640.0),
]
PIVOT = 584.0              # D dorian -> D major, inside the Fable 5 era

# The hallucination: at the theme's peak (Morse symbol 9, the dah of A)
# Claude 2's second statement overreaches C5 by a semitone.
HALL_SLOT = 9
HALL_T0 = 64.0                                   # phrase 2 of era 2
CORR_T0 = 80.0                                   # phrase 3 corrects it
HALL_BEAT = HALL_T0 + _MORSE[HALL_SLOT][0]       # 71.0
CORR_BEAT = CORR_T0 + _MORSE[HALL_SLOT][0]       # 87.0
HALL_PITCH = 73                                  # C#5 (non-diatonic)

_TICK = 1.0 / en.PPQ
_DORIAN_PCS = {0, 2, 4, 5, 7, 9, 11}             # D dorian = white keys
_DMAJOR_PCS = {1, 2, 4, 6, 7, 9, 11}             # D major (F#, C#)

# Tempo lane: era-by-era tempo-event counts 1,1,2,8,8,8,12 — themselves
# part of the monotonic-capability claim.
TEMPO_MAP = [
    (0.0, 100.0),                                # Claude 1: metronomic
    (48.0, 100.0),                               # Claude 2: still rigid
    (112.0, 101.0), (176.0, 102.0),              # Claude 3: first motion
    (224.0, 96.0), (240.0, 92.0), (256.0, 98.0), (272.0, 94.0),
    (288.0, 99.0), (304.0, 95.0), (320.0, 100.0), (336.0, 97.0),
    (352.0, 104.0), (364.0, 105.0), (376.0, 106.0), (388.0, 104.0),
    (400.0, 107.0), (412.0, 105.0), (424.0, 108.0), (436.0, 106.0),
    (448.0, 78.0), (458.0, 76.0), (468.0, 79.0), (478.0, 77.0),
    (488.0, 80.0), (498.0, 76.0), (508.0, 78.0), (518.0, 75.0),
    (528.0, 90.0), (540.0, 94.0), (552.0, 88.0), (564.0, 96.0),
    (576.0, 92.0), (584.0, 98.0), (592.0, 95.0), (600.0, 97.0),
    (608.0, 93.0), (616.0, 88.0), (624.0, 80.0), (632.0, 72.0),
]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=ERAS,
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, 0, 0), (PIVOT, 2, 0)],        # dorian ink, then D major
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_FLUTE, "flute - the voice", 73, 100, 64, 55),
        (CH_REC, "recorder - organum", 74, 92, 64, 52),
        (CH_CEL, "celesta - Haiku", 8, 96, 78, 60),
        (CH_PNO, "piano - Sonnet", 0, 100, 50, 45),
        (CH_STR, "strings - Opus", 48, 95, 64, 60),
        (CH_OBOE, "oboe", 68, 94, 64, 52),
        (CH_HORN, "horns", 60, 95, 64, 58),
        (CH_TIMP, "timpani", 47, 100, 57, 60),
        (CH_CHOIR, "choir", 52, 92, 64, 62),
        (CH_ORG, "organ - Leslie", 16, 90, 64, 50),
    ],
    extra_markers=[
        (HALL_BEAT, "the hallucination: C sharp over D dorian"),
        (CORR_BEAT, "corrected by a step"),
        (PIVOT, "the resolution: D dorian becomes D major"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {0, 8, 16, 47, 48, 52, 60, 68, 73, 74}
CENTERED_CHANNELS: set[int] = {CH_FLUTE, CH_REC, CH_STR, CH_OBOE,
                               CH_HORN, CH_CHOIR, CH_ORG}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_FLUTE: (60, 94),
    CH_REC: (50, 78),
    CH_CEL: (72, 105),
    CH_PNO: (36, 84),
    CH_STR: (36, 78),
    CH_OBOE: (60, 88),
    CH_HORN: (45, 76),
    CH_TIMP: (36, 50),
    CH_CHOIR: (55, 74),
    CH_ORG: (36, 72),
}
# The early models fall silent between Morse statements (13.75-beat
# phrase in a 16-beat frame): every era-1/2 phrase seam is scored.
GAP_WHITELIST: list[tuple[float, float]] = [
    (16.0 * k - 2.5, 16.0 * k + 0.5) for k in range(1, 8)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (398.0, 412.0)   # ~6:44 written file
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# The theme
# ---------------------------------------------------------------------------

def _theme(sc: en.Score, ch: int, t0: float, base: int, mode: str = MODE,
           unit: float = THEME_UNIT, vel: int = 80,
           vel_end: int | None = None, shift: int = 0, jt: int = 0,
           jv: int = 0, gate: float = 1.0, invert: bool = False,
           override: dict[int, int] | None = None,
           slots: tuple[int, int] | None = None) -> float:
    """Play the CLAUDE Morse theme (or one letter of it, via `slots`).

    Rhythm comes verbatim from material.morse_rhythm; pitch is
    THEME_DEGREES on a D-rooted `base` (any integer `shift` keeps the
    line inside the mode's collection).  Returns the end beat.
    """
    pairs = list(zip(material.morse_rhythm(material.MORSE_T2, unit),
                     THEME_DEGREES))
    lo, hi = (0, len(pairs)) if slots is None else slots
    pairs = pairs[lo:hi]
    t_off = pairs[0][0][0]
    span = max(on + du for (on, du), _d in pairs) - t_off
    for k, ((on, du), deg) in enumerate(pairs):
        d = (2 - deg) if invert else deg
        p = en.pitch(base, mode, d + shift)
        if override and (lo + k) in override:
            p = override[lo + k]
        v = vel
        if vel_end is not None and span > 0:
            v = round(en.lerp(vel, vel_end, (on - t_off) / span))
        sc.note(ch, p, t0 + (on - t_off), du * gate, v, jt=jt, jv=jv)
    return t0 + span


# ---------------------------------------------------------------------------
# Builders — one per era
# ---------------------------------------------------------------------------

def _e1_claude_1(sc: en.Score) -> None:
    """[0, 48) One flute.  Three identical Morse statements, velocity
    exactly 80, hard-quantized, one octave, no CCs, flat 100 bpm.  The
    model says its one word, then waits."""
    for s in (0.0, 16.0, 32.0):
        _theme(sc, CH_FLUTE, s, D4, vel=80, jt=0, jv=0, gate=1.0)


def _e2_claude_2(sc: en.Score) -> None:
    """[48, 112) A second voice appears: the recorder shadows the flute
    in parallel diatonic sixths (organum).  Phrase 2 hallucinates C#5 at
    the theme's peak; phrase 3 corrects it by step.  Everything still
    velocity-80 rigid."""
    for t0 in (48.0, 64.0, 80.0, 96.0):
        override = {HALL_SLOT: HALL_PITCH} if t0 == HALL_T0 else None
        _theme(sc, CH_FLUTE, t0, D4, vel=80, jt=0, jv=0, gate=1.0,
               override=override)
        _theme(sc, CH_REC, t0, D4, shift=-5, vel=80, jt=0, jv=0,
               gate=1.0)


def _e3_claude_3(sc: en.Score) -> None:
    """[112, 224) The trio: Haiku (quick celesta), Sonnet (piano,
    balanced), Opus (deep strings, the theme at half speed) converse.
    The first dynamics — velocities finally move."""
    # Opus's bed carries the whole era (jt=0 splices, no seams).
    for t0, ps, du, v in ((112.0, (D3, 57), 16.0, 44),
                          (128.0, (D3, 53, 57), 16.0, 46),
                          (144.0, (45,), 28.0, 42),
                          (172.0, (D3, 57), 20.0, 46),
                          (192.0, (D3, 57, 62), 16.0, 48),
                          (208.0, (D3, 57), 15.5, 50)):
        for p in ps:
            sc.note(CH_STR, p, t0, du, v, jt=0, jv=2)
    # Haiku: the theme at double speed, then answering sparkles.
    _theme(sc, CH_CEL, 112.0, D5, unit=0.125, vel=58, vel_end=72,
           jt=1, jv=3, gate=0.95)
    en.arp(sc, CH_CEL, [74, 77, 81, 86], 120.0, count=8, step=0.5,
           vel=58, pattern="updown", gate=1.1)
    # Sonnet: the theme, balanced, with left-hand fifths on the letters.
    _theme(sc, CH_PNO, 128.0, D4, vel=60, vel_end=76, jt=2, jv=3,
           gate=0.95)
    for lb in (0.0, 3.5, 6.5, 8.5, 11.0, 13.5):
        sc.note(CH_PNO, D3, 128.0 + lb, 2.0, 54, jt=2, jv=3)
        sc.note(CH_PNO, 57, 128.0 + lb, 2.0, 52, jt=2, jv=3)
    # Opus: the theme itself, deep and slow (half speed), rising.
    _theme(sc, CH_STR, 144.0, D3, unit=0.5, vel=50, vel_end=70,
           jt=2, jv=3, gate=0.95)
    # Haiku answers over the Opus statement.
    _theme(sc, CH_CEL, 160.0, D5, unit=0.125, vel=62, vel_end=74,
           jt=1, jv=3, gate=0.95)
    en.arp(sc, CH_CEL, [74, 77, 81, 86], 168.0, count=6, step=0.5,
           vel=60, pattern="up", gate=1.1)
    # Sonnet again; Haiku echoes it in canon two beats behind.
    _theme(sc, CH_PNO, 176.0, D4, vel=64, vel_end=80, jt=2, jv=3,
           gate=0.95)
    for lb in (0.0, 3.5, 6.5, 8.5, 11.0, 13.5):
        sc.note(CH_PNO, D3, 176.0 + lb, 2.0, 56, jt=2, jv=3)
        sc.note(CH_PNO, 57, 176.0 + lb, 2.0, 54, jt=2, jv=3)
    _theme(sc, CH_CEL, 178.0, D5, vel=58, vel_end=68, jt=2, jv=3,
           gate=0.95)
    # Conversation: piano broken chords, celesta glitter.
    en.arp(sc, CH_PNO, [D3, 57, 62, 65], 192.0, count=16, step=0.5,
           vel=58, pattern="updown", gate=1.0)
    en.arp(sc, CH_PNO, [48, 55, 60, 64], 200.0, count=12, step=0.5,
           vel=56, pattern="updown", gate=1.0)
    en.arp(sc, CH_CEL, [74, 77, 81, 86], 196.0, count=8, step=0.25,
           vel=66, pattern="up", gate=1.1)
    # Cadence: G - Am - Dm (the dorian IV-v-i), celesta star on top.
    for t0, ps, du, v in ((208.0, (55, 59, 62), 3.5, 66),
                          (212.0, (57, 60, 64), 3.5, 62),
                          (216.0, (D3, 57, 62, 65), 7.0, 70)):
        for p in ps:
            sc.note(CH_PNO, p, t0, du, v, jt=2, jv=3)
    sc.note(CH_CEL, 81, 212.0, 2.0, 58, jt=2, jv=2)
    sc.note(CH_CEL, 86, 216.0, 6.0, 64, jt=2, jv=2)


def _e4_extended_thinking(sc: en.Score) -> None:
    """[224, 352) Extended thinking: a long fugato on the theme.  Four
    entries (flute, oboe at the fifth, recorder, piano with bass), then
    a development that turns the word's letters over one by one.  The
    first expression CCs (CC11 arcs) and the first rubato."""
    # A thought-stream pedal keeps the floor unbroken.
    sc.note(CH_STR, D3, 224.0, 48.0, 40, jt=0, jv=1)
    en.cc_curve(sc, CH_STR, 11, [(224.0, 52), (256.0, 66), (287.0, 58)],
                step=2.0)
    # Entry 1: flute, tonic.
    en.cc_curve(sc, CH_FLUTE, 11, [(224.0, 74), (232.0, 104),
                                   (238.0, 88)], step=1.0)
    _theme(sc, CH_FLUTE, 224.0, D5, vel=64, vel_end=84, jt=3, jv=4,
           gate=0.95)
    # Entry 2: oboe answers at the fifth (diatonic: shift +4).
    en.cc_curve(sc, CH_OBOE, 11, [(240.0, 72), (248.0, 102),
                                  (254.0, 86)], step=1.0)
    _theme(sc, CH_OBOE, 240.0, D4, shift=4, vel=66, vel_end=84,
           jt=3, jv=4, gate=0.95)
    en.line(sc, CH_FLUTE, 240.0, D5, MODE,
            [(8, 0.0, 3.0), (7, 3.5, 2.5), (6, 6.5, 1.5), (5, 8.5, 2.0),
             (4, 11.0, 2.0), (5, 13.5, 2.0)], vel=62, jt=3, jv=4)
    # Entry 3: recorder, tonic an octave down.
    en.cc_curve(sc, CH_REC, 11, [(256.0, 70), (264.0, 96), (270.0, 82)],
                step=1.0)
    _theme(sc, CH_REC, 256.0, D4, vel=58, vel_end=74, jt=3, jv=4,
           gate=0.95)
    en.line(sc, CH_OBOE, 256.0, D4, MODE,
            [(8, 0.0, 3.0), (7, 3.5, 2.5), (6, 6.5, 1.5), (5, 8.5, 2.0),
             (6, 11.0, 2.0), (5, 13.5, 2.0)], vel=60, jt=3, jv=4)
    # Entry 4: piano at the fifth below, with its own bass.
    _theme(sc, CH_PNO, 272.0, D3, shift=4, vel=68, vel_end=82,
           jt=3, jv=4, gate=0.95)
    for lb, dv in ((0.0, 0), (3.5, -2), (6.5, -2), (8.5, -4),
                   (11.0, -4), (13.5, -6)):
        sc.note(CH_PNO, 45, 272.0 + lb, 2.0, 60 + dv, jt=2, jv=3)
    sc.note(CH_STR, D3, 272.0, 16.0, 46, jt=0, jv=2)
    sc.note(CH_STR, 57, 272.0, 16.0, 44, jt=0, jv=2)
    # Development [288, 336): the letters of the word, tossed around.
    en.cc_curve(sc, CH_STR, 11, [(288.0, 60), (312.0, 92), (335.0, 76)],
                step=2.0)
    en.pad_block(sc, CH_STR, 288.0,
                 [en.triad(D3, MODE, d) for d in (1, 2, 3, 4, 5, 4, 3, 2)],
                 span=6.0, size=3, lo=50, hi=74, vel=50, vel_end=62,
                 legato=0.2)
    en.cc_curve(sc, CH_FLUTE, 11, [(288.0, 80), (316.0, 106),
                                   (334.0, 92)], step=2.0)
    en.cc_curve(sc, CH_OBOE, 11, [(288.0, 78), (320.0, 104),
                                  (334.0, 90)], step=2.0)
    for ch, t0, base, shift, letter, v in (
            (CH_FLUTE, 288.0, D5, 0, "C", 70),
            (CH_OBOE, 291.0, D4, 4, "C", 72),
            (CH_REC, 294.0, D4, 1, "C", 66),
            (CH_PNO, 297.0, D4, 2, "C", 74),
            (CH_FLUTE, 300.0, D5, 1, "L", 74),
            (CH_OBOE, 303.0, D4, 5, "L", 76),
            (CH_PNO, 306.0, D3, 4, "L", 72),
            (CH_REC, 309.0, D4, 2, "L", 68),
            (CH_FLUTE, 312.0, D5, 2, "A", 78),
            (CH_OBOE, 315.0, D4, 6, "A", 80),
            (CH_PNO, 318.0, D3, 3, "U", 74),
            (CH_FLUTE, 321.0, D5, 3, "U", 82),
            (CH_OBOE, 324.0, D4, 7, "D", 78),
            (CH_PNO, 327.0, D3, 2, "D", 76),
            (CH_FLUTE, 330.0, D5, 4, "A", 84),
            (CH_OBOE, 332.5, D4, 8, "A", 82)):
        _theme(sc, ch, t0, base, shift=shift, vel=v, vel_end=v + 6,
               jt=3, jv=4, gate=0.95, slots=LETTERS[letter])
    for t0, v in ((296.0, 76), (308.0, 72), (320.0, 80), (332.0, 78)):
        sc.note(CH_CEL, 93, t0, 1.0, v, jt=2, jv=3)
    # Convergence [336, 352): the thought resolves onto the dominant.
    sc.note(CH_STR, 45, 336.0, 16.0, 56, jt=0, jv=2)
    sc.note(CH_STR, 57, 336.0, 16.0, 52, jt=0, jv=2)
    en.cc_curve(sc, CH_STR, 11, [(336.0, 76), (351.5, 108)], step=1.0)
    en.line(sc, CH_FLUTE, 336.0, D5, MODE,
            [(7, 0.0, 2.0), (6, 2.0, 2.0), (5, 4.0, 4.0), (4, 8.0, 2.0),
             (3, 10.0, 2.0), (2, 12.0, 2.0), (1, 14.0, 2.0)],
            vel=76, vel_end=90, jt=3, jv=4)
    en.line(sc, CH_OBOE, 337.0, D4, MODE,
            [(9, 0.0, 2.0), (8, 2.0, 2.0), (7, 4.0, 4.0), (6, 8.0, 2.0),
             (5, 10.0, 2.0), (4, 12.0, 2.0), (3, 14.0, 1.0)],
            vel=72, vel_end=86, jt=3, jv=4)
    sc.note(CH_REC, 57, 340.0, 11.5, 56, jt=3, jv=3)
    for k in range(16):
        sc.note(CH_PNO, 45 if k % 2 else 57, 344.0 + 0.5 * k, 0.4,
                62 + 2 * k, jt=1, jv=3)
    en.run(sc, CH_CEL, 348.0, D5, MODE, [1, 2, 3, 4, 5, 6, 7, 8],
           0.375, 70, 88, jt=1)


def _e5_claude_4(sc: en.Score) -> None:
    """[352, 448) Claude 4: the full orchestra, dense counterpoint —
    theme, answer, inversion and countersubjects all at once; the piano
    gains its sustain pedal (CC64)."""
    en.cc_curve(sc, CH_STR, 11, [(352.0, 84), (384.0, 100), (416.0, 92),
                                 (447.5, 106)], step=2.0)
    en.pad_block(sc, CH_STR, 352.0,
                 [en.triad(D3, MODE, d) for d in
                  (1, 4, 1, 5, 3, 4, 5, 1, 7, 4, 5, 1)],
                 span=8.0, size=4, lo=50, hi=76, vel=62, vel_end=74,
                 legato=0.2)
    # Horns: the theme in canon (tonic, then the fifth, then tonic).
    _theme(sc, CH_HORN, 352.0, D4, vel=82, vel_end=90, jt=3, jv=4,
           gate=0.95)
    _theme(sc, CH_HORN, 368.0, D3, shift=4, vel=78, vel_end=86,
           jt=3, jv=4, gate=0.95)
    _theme(sc, CH_HORN, 400.0, D4, vel=86, vel_end=94, jt=3, jv=4,
           gate=0.95)
    sc.note(CH_HORN, 57, 384.0, 14.0, 68, jt=3, jv=3)
    sc.note(CH_HORN, 62, 416.0, 14.0, 70, jt=3, jv=3)
    sc.note(CH_HORN, 57, 432.0, 15.0, 74, jt=3, jv=3)
    # Flute: theme high, then its INVERSION — the model argues both ways.
    en.cc_curve(sc, CH_FLUTE, 11, [(352.0, 88), (368.0, 104),
                                   (400.0, 96), (440.0, 110)], step=2.0)
    _theme(sc, CH_FLUTE, 360.0, D5, vel=78, vel_end=90, jt=3, jv=4,
           gate=0.95)
    _theme(sc, CH_FLUTE, 384.0, D5, vel=80, vel_end=92, jt=3, jv=4,
           gate=0.95, invert=True)
    _theme(sc, CH_FLUTE, 408.0, D5, vel=84, vel_end=96, jt=3, jv=4,
           gate=0.95)
    _theme(sc, CH_FLUTE, 432.0, D5, shift=1, vel=86, vel_end=96,
           jt=3, jv=4, gate=0.95)
    # Oboe: answers at the fifth, plus a free countersubject.
    en.cc_curve(sc, CH_OBOE, 11, [(352.0, 86), (392.0, 102),
                                  (447.5, 104)], step=2.0)
    _theme(sc, CH_OBOE, 368.0, D4, shift=4, vel=74, vel_end=86,
           jt=3, jv=4, gate=0.95)
    _theme(sc, CH_OBOE, 416.0, D4, shift=4, vel=80, vel_end=92,
           jt=3, jv=4, gate=0.95)
    en.line(sc, CH_OBOE, 392.0, D4, MODE,
            [(5, 0.0, 3.0), (6, 3.0, 1.0), (7, 4.0, 3.0), (8, 7.0, 1.0),
             (9, 8.0, 4.0), (8, 12.0, 2.0)], vel=76, jt=3, jv=4)
    # Recorder: inner countersubject in long tones.
    for t0, deg, du, v in ((352.0, 5, 7.5, 60), (360.0, 4, 7.5, 58),
                           (368.0, 3, 7.5, 60), (376.0, 5, 7.5, 62),
                           (384.0, 6, 7.5, 62), (392.0, 5, 7.5, 60),
                           (400.0, 8, 7.5, 64), (408.0, 7, 7.5, 62),
                           (416.0, 6, 7.5, 64), (424.0, 5, 7.5, 62),
                           (432.0, 8, 7.5, 66), (440.0, 8, 7.0, 68)):
        sc.note(CH_REC, en.pitch(D4, MODE, deg), t0, du, v, jt=3, jv=3)
    # Piano: driving eighths under the counterpoint, pedalled per bar.
    for k, d in enumerate((1, 4, 1, 5, 3, 4, 5, 1, 7, 4, 5, 1)):
        t0 = 352.0 + 8.0 * k
        pcs = en.triad(D3, MODE, d)
        en.sustain(sc, CH_PNO, t0 + 0.05, t0 + 7.6)
        en.arp(sc, CH_PNO, pcs + [pcs[0] + 12], t0, count=16, step=0.5,
               vel=64, pattern="updown", gate=1.0, accent_every=4,
               accent=8)
    # Celesta: doubling sparkles, then the climb to C7.
    for k in range(6):
        sc.note(CH_CEL, 86, 352.0 + 16.0 * k, 0.75, 80, jt=2, jv=3)
        if k < 5:
            sc.note(CH_CEL, 93, 360.0 + 16.0 * k, 0.75, 76, jt=2, jv=3)
    en.arp(sc, CH_CEL, [74, 77, 81, 84, 86, 89, 93, 96], 436.0,
           count=16, step=0.25, vel=82, pattern="up", gate=1.1)
    sc.note(CH_CEL, 96, 444.0, 2.0, 88, jt=1, jv=2)
    # Timpani: the word's first letter as a drum figure, and the roll.
    for k in range(6):
        t0 = 352.0 + 16.0 * k
        for on, du in _MORSE[:4]:
            sc.note(CH_TIMP, D2, t0 + on, min(du, 0.4), 88 + 2 * k,
                    jt=2, jv=3)
        sc.note(CH_TIMP, 45, t0 + 8.0, 0.4, 80, jt=2, jv=3)
    for k in range(8):
        sc.note(CH_TIMP, D2, 444.0 + 0.5 * k, 0.3, 74 + 4 * k,
                jt=1, jv=2)


def _e6_claude_4_5(sc: en.Score) -> None:
    """[448, 528) Claude 4.5: subtlety.  Fewer notes, more space — the
    word taken apart, one letter per gesture, over an unbroken pp
    string floor.  The album's FIRST pitch bends (flute scoops), and
    the first timbre CCs (CC74)."""
    for t0, ps, du, v in ((448.0, (D3, 57), 20.0, 32),
                          (468.0, (D3, 53), 20.0, 30),
                          (488.0, (48, 55), 20.0, 31),
                          (508.0, (D3, 57), 19.5, 30)):
        for p in ps:
            sc.note(CH_STR, p, t0, du, v, jt=0, jv=1)
    en.cc_curve(sc, CH_STR, 11, [(448.0, 54), (480.0, 44), (527.0, 40)],
                step=2.0)
    en.cc_curve(sc, CH_FLUTE, 74, [(448.0, 84), (460.0, 46),
                                   (500.0, 60)], step=1.0)
    en.cc_curve(sc, CH_OBOE, 74, [(476.0, 78), (486.0, 44)], step=1.0)
    # C — piano, pedalled.
    _theme(sc, CH_PNO, 452.0, D4, slots=LETTERS["C"], vel=56, jt=2,
           jv=3, gate=0.9)
    en.sustain(sc, CH_PNO, 451.9, 456.5)
    # L — flute, with the album's first bend: a scoop from below.
    en.bend_ramp(sc, CH_FLUTE, 461.6, 462.0, -0.6, 0.0, steps=6)
    _theme(sc, CH_FLUTE, 462.0, D5, slots=LETTERS["L"], vel=52, jt=2,
           jv=3, gate=0.9)
    # A — celesta, and a single very high star.
    _theme(sc, CH_CEL, 472.0, D5, slots=LETTERS["A"], vel=60, jt=2,
           jv=3, gate=0.9)
    sc.note(CH_CEL, D7, 484.0, 2.5, 72, jt=1, jv=2)
    # U — oboe, darkened.
    _theme(sc, CH_OBOE, 490.0, D4, shift=4, slots=LETTERS["U"], vel=52,
           jt=2, jv=3, gate=0.9)
    sc.note(CH_HORN, D3, 494.0, 12.0, 33, jt=2, jv=1)
    # D — piano again.
    _theme(sc, CH_PNO, 502.0, D4, slots=LETTERS["D"], vel=58, jt=2,
           jv=3, gate=0.9)
    en.sustain(sc, CH_PNO, 501.9, 506.0)
    sc.note(CH_REC, D5, 510.0, 3.0, 44, jt=2, jv=2)
    # E — the closing dit, bent up to and held.
    en.bend_ramp(sc, CH_FLUTE, 515.6, 516.0, -0.4, 0.0, steps=6)
    sc.note(CH_FLUTE, D5, 516.0, 4.0, 60, jt=2, jv=2)
    sc.note(CH_CEL, D7, 520.0, 3.0, 66, jt=1, jv=2)
    sc.note(CH_TIMP, D2, 449.0, 1.0, 30, jt=2, jv=2)
    sc.note(CH_TIMP, D2, 524.0, 1.5, 28, jt=2, jv=2)


def _e7_fable_5(sc: en.Score) -> None:
    """[528, 640) Fable 5: the theme free at last — organ Leslie (CC1),
    choir vowels (CC70), aftertouch blooms, expressive bends, an elastic
    tempo lane — and at beat 584 the mode itself resolves: D dorian
    becomes D major.  The final chord holds the major third."""
    # -- dorian half [528, 584) ---------------------------------------
    en.leslie(sc, CH_ORG, 528.0, 536.0, 12, 60)
    en.leslie(sc, CH_ORG, 560.0, 576.0, 60, 96)
    for t0, ps, du, v in ((528.0, (D3, 57, 62), 16.0, 46),
                          (544.0, (48, 55, 64), 16.0, 48),
                          (560.0, (D3, 55, 62), 12.0, 52),
                          (572.0, (D3, 57, 64), 11.8, 56)):
        for p in ps:
            sc.note(CH_ORG, p, t0, du, v, jt=0, jv=2)
    en.vowel_curve(sc, CH_CHOIR, [(536.0, 0), (556.0, 25), (576.0, 45),
                                  (584.0, 60), (600.0, 88), (614.0, 85),
                                  (626.0, 50), (638.0, 20)], step=1.0)
    en.cc_curve(sc, CH_CHOIR, 11, [(536.0, 40), (560.0, 62),
                                   (584.0, 84), (612.0, 88),
                                   (639.0, 30)], step=1.0)
    for t0, ps, du, v in ((536.0, (62,), 8.0, 46),
                          (544.0, (62, 69), 16.0, 50),
                          (560.0, (62, 67), 12.0, 54),
                          (572.0, (62, 69), 11.8, 58)):
        for p in ps:
            sc.note(CH_CHOIR, p, t0, du, v, jt=0, jv=2)
    en.cc_curve(sc, CH_FLUTE, 11, [(536.0, 82), (550.0, 104),
                                   (562.0, 90), (582.0, 106)], step=1.0)
    _theme(sc, CH_FLUTE, 536.0, D5, vel=72, vel_end=86, jt=5, jv=5,
           gate=0.92)
    sc.note(CH_FLUTE, D6, 552.0, 6.0, 80, jt=3, jv=3)
    en.vibrato(sc, CH_FLUTE, 552.0, 6.0, depth=0.35, delay=1.0)
    en.at_curve(sc, CH_FLUTE, [(552.0, 0), (555.0, 68), (558.0, 0)],
                step=0.25)
    _theme(sc, CH_OBOE, 560.0, D4, shift=4, vel=66, vel_end=80, jt=4,
           jv=4, gate=0.92)
    for k, d in enumerate((1, 7, 4, 1, 5, 4, 1)):
        t0 = 528.0 + 8.0 * k
        pcs = en.triad(D3, MODE, d)
        en.sustain(sc, CH_PNO, t0 + 0.05, t0 + 7.6)
        en.arp(sc, CH_PNO, pcs + [pcs[0] + 12], t0, count=8, step=1.0,
               vel=48, pattern="up", gate=1.1)
    sc.note(CH_STR, D3, 536.0, 24.0, 40, jt=0, jv=2)
    sc.note(CH_STR, 57, 536.0, 24.0, 38, jt=0, jv=2)
    sc.note(CH_STR, D3, 560.0, 23.8, 46, jt=0, jv=2)
    sc.note(CH_STR, 62, 560.0, 23.8, 44, jt=0, jv=2)
    en.cc_curve(sc, CH_STR, 11, [(536.0, 46), (566.0, 66), (583.0, 84)],
                step=2.0)
    # The ascent into the pivot.
    en.line(sc, CH_HORN, 576.0, D3, MODE,
            [(1, 0.0, 2.0), (2, 2.0, 2.0), (4, 4.0, 2.0),
             (5, 6.0, 1.8)], vel=68, vel_end=88, jt=3, jv=3)
    sc.note(CH_REC, 62, 576.0, 7.8, 56, jt=3, jv=3)
    for k in range(4):
        sc.note(CH_TIMP, D2, 576.0 + 2.0 * k, 0.4, 60 + 8 * k,
                jt=2, jv=3)
    # -- the resolution [584, 640): D MAJOR ----------------------------
    en.cc_curve(sc, CH_FLUTE, 11, [(584.0, 108), (600.0, 100),
                                   (616.0, 92), (636.0, 60)], step=1.0)
    _theme(sc, CH_FLUTE, 584.0, D5, mode=MAJ, vel=92, vel_end=102,
           jt=4, jv=4, gate=0.95)
    _theme(sc, CH_OBOE, 584.0, D4, mode=MAJ, vel=86, vel_end=96,
           jt=4, jv=4, gate=0.95)
    for p, v in ((62, 100), (66, 96), (69, 98)):
        sc.note(CH_HORN, p, 584.0, 6.0, v, jt=2, jv=3)
    _theme(sc, CH_HORN, 600.0, D4, mode=MAJ, vel=88, vel_end=98,
           jt=3, jv=4, gate=0.95)
    en.pad_block(sc, CH_STR, 584.0,
                 [en.triad(D3, MAJ, d) for d in (1, 4, 5, 1)],
                 span=8.0, size=4, lo=50, hi=76, vel=64, vel_end=72,
                 legato=0.2)
    en.leslie(sc, CH_ORG, 584.0, 592.0, 96, 110)
    en.cc_curve(sc, CH_ORG, 74, [(584.0, 96), (616.0, 70),
                                 (636.0, 40)], step=2.0)
    for t0, ps, du, v in ((584.0, (D3, 54, 57, 62), 16.0, 58),
                          (600.0, (D3, 54, 62, 66), 16.0, 56)):
        for p in ps:
            sc.note(CH_ORG, p, t0, du, v, jt=0, jv=2)
    for t0, ps, du, v in ((584.0, (62, 66, 69), 16.0, 62),
                          (600.0, (62, 66), 16.0, 58)):
        for p in ps:
            sc.note(CH_CHOIR, p, t0, du, v, jt=0, jv=2)
    for k, d in enumerate((1, 4, 1, 5)):
        t0 = 584.0 + 8.0 * k
        pcs = en.triad(D3, MAJ, d)
        en.sustain(sc, CH_PNO, t0 + 0.05, t0 + 7.6)
        en.arp(sc, CH_PNO, pcs + [pcs[0] + 12], t0, count=16, step=0.5,
               vel=68, pattern="updown", gate=1.0, accent_every=4,
               accent=8)
    sc.note(CH_CEL, D7, 592.0, 1.5, 84, jt=1, jv=2)
    en.run(sc, CH_CEL, 602.0, D6, MAJ, [1, 3, 5, 8, 10, 12], 0.5,
           74, 92, jt=1)
    sc.note(CH_REC, 69, 584.0, 15.5, 54, jt=3, jv=3)
    sc.note(CH_REC, 66, 600.0, 14.0, 52, jt=3, jv=3)
    for t0, p, v in ((584.0, D2, 102), (588.0, 45, 88), (592.0, D2, 94),
                     (600.0, D2, 98), (608.0, 45, 86)):
        sc.note(CH_TIMP, p, t0, 0.5, v, jt=2, jv=3)
    # -- coda [616, 640): the lamp stays lit, and dims -----------------
    for k in range(10):
        sc.note(CH_TIMP, D2, 616.0 + 0.5 * k, 0.3, 44 - 2 * k,
                jt=1, jv=2)
    en.leslie(sc, CH_ORG, 616.0, 634.0, 90, 6)
    sc.note(CH_ORG, D2, 616.0, 22.0, 44, jt=0, jv=1)
    for p in (D3, 54, 57):
        sc.note(CH_ORG, p, 616.0, 22.0, 42, jt=0, jv=1)
    for p in (D3, 54, 57, 62):
        sc.note(CH_STR, p, 616.0, 22.0, 44, jt=0, jv=1)
    for p in (62, 66, 69):
        sc.note(CH_CHOIR, p, 616.0, 22.0, 46, jt=0, jv=1)
    sc.note(CH_PNO, D2, 616.0, 6.0, 46, jt=1, jv=2)
    en.sustain(sc, CH_PNO, 616.05, 630.0)
    sc.note(CH_FLUTE, 78, 618.0, 20.0, 56, jt=2, jv=2)      # F#5
    en.vibrato(sc, CH_FLUTE, 620.0, 16.0, depth=0.3,
               cycles_per_beat=0.9, delay=2.0)
    sc.bend(CH_FLUTE, 639.0, 0.0)
    en.at_curve(sc, CH_FLUTE, [(620.0, 0), (630.0, 72), (638.5, 0)],
                step=0.5)
    en.at_curve(sc, CH_CHOIR, [(618.0, 0), (628.0, 55), (637.0, 0)],
                step=0.5)
    sc.note(CH_OBOE, 66, 617.0, 18.0, 44, jt=2, jv=2)       # F#4
    sc.note(CH_REC, 74, 618.0, 18.0, 40, jt=2, jv=2)        # D5
    for t0, p, v in ((620.0, 86, 26), (624.0, 93, 24), (628.0, 98, 22)):
        sc.note(CH_CEL, p, t0, 2.5, v, jt=1, jv=1)


BUILDERS: list = [_e1_claude_1, _e2_claude_2, _e3_claude_3,
                  _e4_extended_thinking, _e5_claude_4, _e6_claude_4_5,
                  _e7_fable_5]


# ---------------------------------------------------------------------------
# Oracles — written before the music; the track is composed to pass them
# ---------------------------------------------------------------------------

_ALL_CHANNELS = (CH_FLUTE, CH_REC, CH_CEL, CH_PNO, CH_STR, CH_OBOE,
                 CH_HORN, CH_TIMP, CH_CHOIR, CH_ORG)


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


def _all_notes(sc) -> list[tuple[int, float, float, int, int]]:
    return [(ch, on, du, p, v) for ch in _ALL_CHANNELS
            for on, du, p, v in _notes(sc, ch)]


def _span_notes(sc, t0: float, t1: float):
    return [x for x in _all_notes(sc) if t0 - 0.05 <= x[1] < t1 - 0.05]


def _ccs_in(sc, t0: float, t1: float) -> set[int]:
    """CC numbers authored in [t0, t1), excluding the beat-0 setup."""
    out: set[int] = set()
    for ch in sc.events:
        for tick, _prio, data in sc.events[ch]:
            beat = tick / en.PPQ
            if (data[0] & 0xF0) == 0xB0 and beat > 0.05 \
                    and t0 - 0.05 <= beat < t1 - 0.05:
                out.add(data[1])
    return out


def _bends_in(sc, t0: float, t1: float) -> list[float]:
    out = []
    for ch in sc.events:
        for tick, _prio, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0xE0:
                beat = tick / en.PPQ
                if t0 - 0.05 <= beat < t1 - 0.05:
                    out.append(beat)
    return sorted(out)


def _ats_in(sc, t0: float, t1: float) -> list[float]:
    out = []
    for ch in sc.events:
        for tick, _prio, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0xD0:
                beat = tick / en.PPQ
                if t0 - 0.05 <= beat < t1 - 0.05:
                    out.append(beat)
    return sorted(out)


def _std(vals: list[int]) -> float:
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    return (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5


def _era_metrics(sc, t0: float, t1: float) -> tuple:
    notes = _span_notes(sc, t0, t1)
    chans = {ch for ch, *_rest in notes}
    vels = [v for *_x, v in notes]
    pitches = [p for _ch, _on, _du, p, _v in notes]
    prange = (max(pitches) - min(pitches)) if pitches else 0
    tempo_n = sum(1 for b, _bpm in TEMPO_MAP if t0 <= b < t1)
    return (len(chans), _ccs_in(sc, t0, t1), round(_std(vels), 3),
            prange, tempo_n)


def _check_monotonic_capability(sc) -> list[str]:
    """THE HEADLINE: each era's (channel count, CC set, velocity
    stddev, pitch range, tempo events) is <= / subset-of the next's."""
    fails = []
    rows = [(name, _era_metrics(sc, t0, t1)) for name, t0, t1 in ERAS]
    for (na, a), (nb, b) in zip(rows, rows[1:]):
        if a[0] > b[0]:
            fails.append(f"channels shrink {na}({a[0]}) -> {nb}({b[0]})")
        if not a[1] <= b[1]:
            fails.append(f"CC set not nested {na}{sorted(a[1])} -> "
                         f"{nb}{sorted(b[1])}")
        if a[2] > b[2] + 1e-9:
            fails.append(f"velocity stddev falls {na}({a[2]}) -> "
                         f"{nb}({b[2]})")
        if a[3] > b[3]:
            fails.append(f"pitch range shrinks {na}({a[3]}) -> "
                         f"{nb}({b[3]})")
        if a[4] > b[4]:
            fails.append(f"tempo events fall {na}({a[4]}) -> "
                         f"{nb}({b[4]})")
    if fails:
        for name, m in rows:
            fails.append(f"  [{name}] ch={m[0]} cc={sorted(m[1])} "
                         f"vstd={m[2]} range={m[3]} tempo={m[4]}")
    return fails


def _check_era_markers(sc) -> list[str]:
    """The seven era markers name the releases, at the era starts."""
    fails = []
    marks = {(b, t) for b, t in sc.markers}
    for name, t0, _t1 in ERAS:
        if (t0, name) not in marks:
            fails.append(f"missing era marker {name!r} at beat {t0}")
    return fails


def _check_era1_morse(sc) -> list[str]:
    """Era 1 = exactly three theme statements whose onset/duration
    pattern equals morse_rhythm('CLAUDE') scaled by the sixteenth."""
    fails = []
    if len(_MORSE) != len(THEME_DEGREES):
        fails.append(f"{len(THEME_DEGREES)} theme degrees for "
                     f"{len(_MORSE)} Morse symbols")
        return fails
    got = [x for x in _notes(sc, CH_FLUTE) if x[0] < 48.0]
    want = [(s + on, du, en.pitch(D4, MODE, deg))
            for s in (0.0, 16.0, 32.0)
            for (on, du), deg in zip(_MORSE, THEME_DEGREES)]
    if len(got) != len(want):
        fails.append(f"era 1 has {len(got)} notes, want {len(want)} "
                     f"(3 x 17 Morse symbols)")
        return fails
    for (on, du, p, _v), (won, wdu, wp) in zip(got, want):
        if abs(on - won) > 2 * _TICK:
            fails.append(f"onset {on:.4f} != Morse {won:.4f}")
        if abs(du - wdu) > 2 * _TICK:
            fails.append(f"duration {du:.4f} at {on:.2f} != {wdu:.4f}")
        if p != wp:
            fails.append(f"pitch {p} at beat {on:.2f} != theme {wp}")
    return fails


def _check_era1_rigidity(sc) -> list[str]:
    """One channel, velocity exactly 80, sixteenth grid, one octave,
    zero expressive CCs, zero bends/aftertouch, one flat tempo event."""
    fails = []
    notes = _span_notes(sc, 0.0, 48.0)
    chans = {ch for ch, *_r in notes}
    if chans != {CH_FLUTE}:
        fails.append(f"era 1 channels {sorted(chans)} != flute only")
    grid = en.PPQ // 4
    for ch, on, _du, p, v in notes:
        if v != 80:
            fails.append(f"velocity {v} at beat {on:.2f} != 80")
        if round(on * en.PPQ) % grid:
            fails.append(f"onset {on:.4f} off the sixteenth grid")
    pitches = [p for _c, _o, _d, p, _v in notes]
    if pitches and max(pitches) - min(pitches) > 12:
        fails.append(f"era 1 range {max(pitches) - min(pitches)} "
                     f"exceeds one octave")
    if _ccs_in(sc, 0.0, 48.0):
        fails.append(f"era 1 authors CCs {sorted(_ccs_in(sc, 0, 48))}")
    if _bends_in(sc, 0.0, 48.0) or _ats_in(sc, 0.0, 48.0):
        fails.append("era 1 authors bends or aftertouch")
    t_events = [(b, bpm) for b, bpm in TEMPO_MAP if b < 48.0]
    if t_events != [(0.0, 100.0)]:
        fails.append(f"era 1 tempo lane {t_events} is not one flat "
                     f"100-bpm event")
    return fails


def _check_era2_hallucination(sc) -> list[str]:
    """Exactly one non-diatonic note in era 2 — C#5 at the peak of
    phrase 2 — and phrase 3 corrects it by step at the same slot."""
    fails = []
    notes = _span_notes(sc, 48.0, 112.0)
    bad = [x for x in notes if x[3] % 12 not in _DORIAN_PCS]
    if len(bad) != 1:
        fails.append(f"{len(bad)} non-diatonic era-2 notes, want "
                     f"exactly 1 (the hallucination)")
        return fails
    ch, on, _du, p, _v = bad[0]
    if ch != CH_FLUTE or abs(on - HALL_BEAT) > 2 * _TICK:
        fails.append(f"hallucination at ch{ch} beat {on:.2f}, want "
                     f"flute at {HALL_BEAT}")
    if p != HALL_PITCH:
        fails.append(f"hallucinated pitch {p} != {HALL_PITCH} (C#5)")
    corr = [x for x in _notes(sc, CH_FLUTE)
            if abs(x[0] - CORR_BEAT) <= 2 * _TICK]
    if len(corr) != 1:
        fails.append(f"{len(corr)} correction candidates at beat "
                     f"{CORR_BEAT}")
        return fails
    cp = corr[0][2]
    if cp % 12 not in _DORIAN_PCS:
        fails.append(f"correction pitch {cp} is itself non-diatonic")
    if not 1 <= abs(HALL_PITCH - cp) <= 2:
        fails.append(f"correction {cp} is not by step from "
                     f"{HALL_PITCH} (|d|={abs(HALL_PITCH - cp)})")
    return fails


def _check_first_bends(sc) -> list[str]:
    """No pitch bend before Claude 4.5; bends live in eras 6 and 7."""
    fails = []
    early = _bends_in(sc, 0.0, 448.0)
    if early:
        fails.append(f"{len(early)} bend events before beat 448 "
                     f"(first at {early[0]:.2f})")
    if not _bends_in(sc, 448.0, 528.0):
        fails.append("Claude 4.5 authors no bends")
    if not _bends_in(sc, 528.0, 640.0):
        fails.append("Fable 5 authors no bends")
    return fails


def _check_fable5_freedom(sc) -> list[str]:
    """Fable 5 authors vowels + Leslie + aftertouch + elastic tempo,
    and the piece ends on a sounding D-MAJOR chord (F# present)."""
    fails = []
    ccs = _ccs_in(sc, 528.0, 640.0)
    for num, what in ((70, "CC70 vowels"), (1, "CC1 Leslie"),
                      (11, "CC11 expression"), (64, "CC64 pedal"),
                      (74, "CC74 brightness")):
        if num not in ccs:
            fails.append(f"Fable 5 era does not author {what}")
    if _ats_in(sc, 0.0, 528.0):
        fails.append("aftertouch appears before the Fable 5 era")
    if not _ats_in(sc, 528.0, 640.0):
        fails.append("Fable 5 era authors no aftertouch")
    tempi = [bpm for b, bpm in TEMPO_MAP if 528.0 <= b < 640.0]
    if len(tempi) < 10:
        fails.append(f"only {len(tempi)} era-7 tempo events (< 10)")
    if tempi and max(tempi) - min(tempi) < 15:
        fails.append(f"tempo spread {max(tempi) - min(tempi):.0f} bpm "
                     f"< 15 (no elasticity)")
    if tempi and tempi[-1] > 76:
        fails.append(f"final tempo {tempi[-1]:.0f} bpm: no closing "
                     f"ritardando")
    # The final sounding chord.
    all_n = _all_notes(sc)
    end = max(on + du for _c, on, du, _p, _v in all_n)
    chord = {p % 12 for _c, on, du, p, _v in all_n
             if on <= end - 2.0 and on + du >= end - 0.1}
    for pc, name in ((2, "D"), (6, "F# (the major third)"), (9, "A")):
        if pc not in chord:
            fails.append(f"final chord lacks {name} (pcs {sorted(chord)})")
    if chord & {0, 3, 5, 8, 10}:
        fails.append(f"final chord holds non-D-major pcs "
                     f"{sorted(chord & {0, 3, 5, 8, 10})}")
    return fails


def _check_modal_integrity(sc) -> list[str]:
    """Before the pivot everything is D dorian (one documented
    hallucination excepted); from the pivot on, D major."""
    fails = []
    for ch, on, _du, p, _v in _all_notes(sc):
        if on < PIVOT - 0.05:
            if p % 12 not in _DORIAN_PCS and \
                    not (abs(on - HALL_BEAT) <= 2 * _TICK
                         and p == HALL_PITCH):
                fails.append(f"ch{ch} pitch {p} at beat {on:.2f} not "
                             f"in D dorian")
        elif p % 12 not in _DMAJOR_PCS:
            fails.append(f"ch{ch} pitch {p} at beat {on:.2f} not in "
                         f"D major (after the pivot)")
    return fails


def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    del info, spans
    return [
        ("era_markers", _check_era_markers(sc)),
        ("era1_morse_theme", _check_era1_morse(sc)),
        ("era1_rigidity", _check_era1_rigidity(sc)),
        ("era2_hallucination", _check_era2_hallucination(sc)),
        ("monotonic_capability", _check_monotonic_capability(sc)),
        ("era6_first_bends", _check_first_bends(sc)),
        ("fable5_freedom", _check_fable5_freedom(sc)),
        ("modal_integrity", _check_modal_integrity(sc)),
    ]


# ---------------------------------------------------------------------------
# Render-side oracles (run by analyze.py once audio/02 - *.wav exists)
# ---------------------------------------------------------------------------

def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    """The capability arc, held against the RENDER."""
    def era_db(b0: float, b1: float) -> float:
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    # 1. Growth: the Claude 4 tutti and the Fable 5 climax both sit at
    #    least 6 dB over the one-flute era 1.
    e1, e5, e6 = era_db(0.0, 48.0), era_db(352.0, 448.0), \
        era_db(448.0, 528.0)
    clx = era_db(584.0, 616.0)
    growth = []
    if e5 < e1 + 6.0:
        growth.append(f"Claude 4 ({e5:.1f} dB) is not 6 dB over "
                      f"Claude 1 ({e1:.1f} dB)")
    if clx < e1 + 6.0:
        growth.append(f"the Fable 5 climax ({clx:.1f} dB) is not 6 dB "
                      f"over Claude 1 ({e1:.1f} dB)")
    # 2. Restraint: Claude 4.5 audibly steps back from Claude 4.
    restraint = []
    if e6 > e5 - 3.0:
        restraint.append(f"Claude 4.5 ({e6:.1f} dB) is not 3 dB below "
                         f"Claude 4 ({e5:.1f} dB)")
    # 3. Rigidity: era 1's three identical statements render at the
    #    same level (within 3 dB of each other).
    flat = []
    vals = [era_db(s, s + THEME_SPAN) for s in (0.0, 16.0, 32.0)]
    if max(vals) - min(vals) > 3.0:
        flat.append(f"era-1 statement RMS spread "
                    f"{max(vals) - min(vals):.1f} dB > 3 (not rigid)")
    # 4. The lamp dims: the coda's three 8-beat windows each get
    #    quieter, at least 4 dB in total.
    fade = []
    w = [era_db(616.0, 624.0), era_db(624.0, 632.0),
         era_db(632.0, 640.0)]
    for k, (a, b) in enumerate(zip(w, w[1:])):
        if b >= a:
            fade.append(f"coda window {k + 1}->{k + 2}: {a:.1f} -> "
                        f"{b:.1f} dB (must fall)")
    if w[0] - w[-1] < 4.0:
        fade.append(f"coda fades only {w[0] - w[-1]:.1f} dB (< 4)")
    return [
        ("audio_capability_growth", growth),
        ("audio_restraint_4_5", restraint),
        ("audio_era1_rigidity", flat),
        ("audio_final_fade", fade),
    ]
