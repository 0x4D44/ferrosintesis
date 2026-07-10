"""t11_night_train — Track 11 "Night Train to Tirana" of *Through Lines*.

Disc 2, 'Lines of Flight'.  HLD section 3, T11: the Bond-IDIOM action cue —
original spy material, zero quotes, and the deliberate opposite of Tuxedo
Noir: no swing in the action, no lounge, and the ending is a brutal unison
sting, not a chord.  C minor, 168 bpm, 12/8 -> 7/8 (the roof fight) -> 12/8.

Every headline claim is a falsifiable oracle (oracles() was written BEFORE
the music; the track is composed to pass it):

 * `meter_map` — the time-signature grid is exactly 12/8 (0) -> 7/8 (the
   roof fight, beat 360) -> 12/8 (beat 549), and the fight movement spans
   the 7/8 region precisely (the metric modulation IS the form).
 * `ostinato_relentless` — the bass ostinato covers >= 90% of all
   eighth-note slots (the 0.5-beat grid) across every action section
   (Full Steam, Roof Fight, Terminus).  Relentlessness, measured.
 * `brass_stabs` — every documented stab (STAB_TIMES) lands >= 3 notes,
   close-voiced within 12 semitones, all shorter than half a beat; and
   every short brass note in the piece sits ON a documented hit.
 * `whammy_dive` — the guitar authors RPN 0 = 12 semitones, then exactly
   ONE full-depth dive (bend to <= -0.98 of range, monotonic on the way
   down) at beat 744, recentred straight after.  Fall-off bends elsewhere
   never exceed -0.9: the dive is unique.
 * `falloff_bends` — the twang lead's documented fall-offs (FALLOFF_TIMES,
   38 of them) each dip below -0.12 of bend range at the note's tail and
   recentre within two-thirds of a beat.
 * `swing_confined` — the suave reed theme in the Bar Car swings at 2:1
   (onsets only on the beat or at beat+2/3, >= 12 off-lobe onsets, >= 8
   strict long-short pairs); OUTSIDE the Bar Car no melodic channel ever
   places an onset in the swing lobe.  Brief swing THERE only.
 * `chromatic_creep` — the dedicated inner line (ch5) moves ONLY by
   semitone within every movement, and its last step resolves +1 onto the
   unison C of the sting.
 * `whistle_gliss` — the train whistle is a brass CLUSTER (>= 3 notes,
   adjacent gaps <= 2 semitones) with a >= half-range pitch-bend gliss,
   recentred, at all four documented blasts.
 * `brakes_gesture` — the brakes are a strictly chromatic string descent
   spanning >= 12 semitones plus a choked (<= 0.5 beat) crash cymbal.
 * `taiko_fight` — the taiko (GM 116, new in ferrosintesis v0.11) plays in
   every one of the 54 roof-fight bars and nowhere else.
 * `unison_sting` — the final sonority is ONE pitch class (C) across >= 4
   melodic channels, every note <= 1 beat, fortissimo (vel >= 100), out of
   a scored 1.5-beat silence, with nothing after it.
 * `dramatic_arc` — per-beat velocity-sum densities: intro < 0.60x Full
   Steam, Bar Car < 0.55x, Roof Fight > 1.15x, Terminus > 1.00x.

audio_checks() mirrors the headline claims on the RENDER: the dynamic arc
in dB (`audio_dynamic_arc`), the sting's C-ness by Goertzel probes
(`audio_sting_unison`), and the post-sting cutoff (`audio_sting_cutoff`).

Movements (quarter-note beats; a 12/8 bar = 6 beats, a 7/8 bar = 3.5):
    i.   Platform Zero      0-72     night station; ostinato fades in
    ii.  Full Steam        72-264    main action; twang theme; stabs
    iii. The Bar Car      264-360    suave reed, swung, 126 bpm
    iv.  Roof Fight       360-549    7/8; taiko, hits, double-time stabs
    v.   Emergency Brakes 549-561    string gliss down + cymbal choke
    vi.  Terminus         561-777    sprint; whistle II; whammy dive; sting
"""

from __future__ import annotations

import bisect
import math

import conductor
import engine as en

NUMBER = 11
TITLE = 'Night Train to Tirana'
FILE = '11 - Night Train to Tirana.mid'
SEED = 20260911

COMMENT = ("Track 11: a Bond-idiom symphonic sprint - relentless bass "
           "ostinato, close brass stabs, twang guitar with one whammy "
           "dive, a 7/8 roof fight, and a brutal unison sting on C.")

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

CH_BASS = 0       # picked bass (GM 34) — THE ostinato, centred
CH_GTR = 1        # clean electric (GM 27) — the twang lead, transient
CH_BRASS = 2      # brass section (GM 61) — stabs, whistle, line; centred
CH_HORN = 3       # french horn (GM 60) — menace counterlines; centred
CH_STR = 4        # strings (GM 48) — beds, the brakes gliss; centred
CH_CREEP = 5      # strings (GM 48) — the chromatic inner line; centred
CH_SAX = 6        # alto sax (GM 65) — the Bar Car's suave theme; centred
CH_TAIKO = 7      # taiko (GM 116) — the roof fight only; transient
CH_TIMP = 8       # timpani (GM 47) — transient, panned slightly left
DRUMS = 9         # kit v2 (program 1); brush kit (40) in the Bar Car
CH_HIT = 10       # orchestra hit (GM 55); riser (GM 119) into the fight

# ---------------------------------------------------------------------------
# The grid (quarter-note beats; 12/8 bar = 6.0, 7/8 bar = 3.5)
# ---------------------------------------------------------------------------

M1, M2, M3, M4, M5, M6, END = 0.0, 72.0, 264.0, 360.0, 549.0, 561.0, 777.0
FIGHT_BARS = 54                    # 54 x 3.5 = 189 beats of 7/8
STING_T = 775.0                    # the kill

# ---------------------------------------------------------------------------
# Musical data — everything the oracles pin lives HERE as constants
# ---------------------------------------------------------------------------

# The relentless ostinato (C minor; eighth = 0.5 beat).  Chromatic tails
# (G-F#-F / C-B-Bb) give it the creep without quoting anything.
OST_A = (36, 36, 43, 36, 36, 46, 36, 36, 44, 43, 42, 41)
OST_B = (36, 36, 43, 36, 36, 46, 48, 47, 46, 44, 43, 39)
OST_7 = (36, 36, 43, 36, 46, 44, 43)          # the 7/8 compression

ACTION_SPANS = ((M2, M3), (M4, M5), (M6, 771.0))   # ostinato coverage spans

# The twang theme (pitch, rel_beat, dur) — 4 bars; onsets on the 0.5 grid
# (NO swing in the action).  Fall-offs at the marked note tails.
THEME_A = (
    (67, 0.0, 2.0), (70, 2.5, 0.5), (72, 3.0, 2.5),
    (67, 6.0, 1.5), (63, 8.0, 0.5), (62, 8.5, 0.5), (63, 9.0, 2.5),
    (67, 12.0, 1.0), (70, 13.0, 0.5), (72, 13.5, 0.5), (75, 14.0, 2.0),
    (74, 16.5, 0.5), (75, 17.0, 1.0), (74, 18.0, 1.0), (72, 19.0, 1.5),
    (68, 21.0, 2.5),
)
THEME_FALL_REL = (2.0, 5.5, 11.5, 23.5)
# (start_beat, octave_shift): four statements in Full Steam, three in
# Terminus (the last doubled by the horn an octave down).
THEME_STARTS = ((84.0, 0), (120.0, 12), (192.0, 0), (228.0, 12),
                (573.0, 0), (597.0, 12), (669.0, 0))

B_PHRASE = (
    (55, 0.0, 2.5), (51, 3.0, 0.5), (53, 3.5, 0.5), (55, 4.0, 1.5),
    (58, 6.0, 2.0), (55, 8.5, 0.5), (56, 9.0, 3.0),
    (55, 12.0, 1.5), (53, 14.0, 0.5), (51, 14.5, 0.5), (48, 15.0, 2.0),
    (55, 18.0, 1.0), (56, 19.0, 1.0), (58, 20.0, 1.0), (60, 21.0, 2.5),
)
B_FALL_REL = (2.5, 23.5)
B_STARTS = (156.0, 621.0)

INTRO_FRAGS = ((67, 24.0, 2.0), (63, 36.0, 2.0), (60, 48.0, 2.5))

FIGHT_RIFF = ((60, 0.0, 0.5), (63, 0.5, 0.5), (60, 1.0, 0.5),
              (65, 1.5, 1.0), (63, 2.5, 0.75))
FIGHT_RIFF_BARS = (5, 7, 9, 11, 21, 23, 25, 27, 37, 39, 41, 43)
FIGHT_FALL_CELL = ((67, 0.0, 1.0), (65, 1.0, 1.0), (63, 2.0, 1.25))
FIGHT_FALL_BARS = (13, 29, 45)

# Every fall-off in the piece, as absolute beats (the oracle iterates this).
FALLOFF_TIMES: tuple[float, ...] = tuple(
    [24.0 + 2.0, 36.0 + 2.0, 48.0 + 2.5]
    + [s + r for s, _o in THEME_STARTS for r in THEME_FALL_REL]
    + [s + r for s in B_STARTS for r in B_FALL_REL]
    + [M4 + 3.5 * b + 3.25 for b in FIGHT_FALL_BARS])

DIVE_T = 744.0                     # the ONE whammy dive (RPN range 12)

# Close-voiced stab voicings (all span <= 12): Cm(add9), its chromatic
# upward creep, and a rootless G7.
STAB_V = ((60, 62, 63, 67), (60, 62, 63, 67),
          (61, 63, 64, 68), (59, 62, 65, 67))


def _stab_times() -> tuple[float, ...]:
    out: list[float] = []
    # Full Steam double-hits (no stab in bars 22-25: the brass section
    # carries the sustained line there instead)
    for b in (3, 7, 11, 15, 19, 27, 31):
        out += [M2 + 6 * b + 4.5, M2 + 6 * b + 5.0]
    for b in (2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46):   # the fight
        out += [M4 + 3.5 * b, M4 + 3.5 * b + 2.0]
    for b in (48, 49, 50, 51, 52, 53):              # double-time climax
        out += [M4 + 3.5 * b, M4 + 3.5 * b + 1.5, M4 + 3.5 * b + 2.5]
    for b in (3, 7, 11, 15, 19, 23):                # Terminus
        out += [M6 + 6 * b + 4.5, M6 + 6 * b + 5.0]
    out += [771.0, 772.0, 773.0]                    # the pre-sting trio
    return tuple(out)


STAB_TIMES = _stab_times()

# The train whistle: (blast_beat, dur) — a cluster gliss, twice per call.
WHISTLE_BLASTS = ((60.0, 2.5), (63.0, 2.0), (717.0, 2.5), (720.0, 2.0))
WHISTLE_CLUSTER = (74, 76, 77)

# The chromatic inner line — one note per bar, semitone steps ONLY.
CREEP_FS = (55, 56, 57, 58, 57, 56, 55, 54,
            55, 56, 57, 58, 59, 58, 57, 56,
            55, 56, 57, 58, 57, 56, 55, 54,
            53, 54, 55, 56, 57, 58, 59, 60)
CREEP_FIGHT = tuple((62, 63, 64, 65, 64, 63)[i % 6] for i in range(54))
CREEP_TERM = tuple((56, 57, 58, 59, 58, 57)[i % 6] for i in range(34))
# CREEP_TERM ends on 59 (B3); the sting's C4 on ch5 is its +1 resolution.

# The Bar Car (264-360, 126 bpm): Eb-major suavity, swung 2:1.
_Eb, _Cm, _Ab, _Fm, _Bb, _G7 = ((3, 7, 10), (0, 3, 7), (8, 0, 3),
                                (5, 8, 0), (10, 2, 5), (7, 11, 2))
BC_CHORDS = (_Eb, _Eb, _Cm, _Ab, _Eb, _Fm, _Bb, _Eb,
             _Ab, _Ab, _Cm, _Cm, _Fm, _Bb, _Eb, _G7)
BC_ROOTS = {_Eb: 39, _Cm: 36, _Ab: 44, _Fm: 41, _Bb: 46, _G7: 43}

SAX_A = (
    (67, 0.0, 0.667), (68, 0.667, 0.333), (70, 1.0, 1.667),
    (72, 2.667, 0.333), (70, 3.0, 0.667), (67, 3.667, 0.333), (65, 4.0, 2.0),
    (63, 6.0, 0.667), (65, 6.667, 0.333), (67, 7.0, 1.5),
    (65, 8.667, 0.333), (63, 9.0, 0.667), (62, 9.667, 0.333),
    (63, 10.0, 1.667), (58, 11.667, 0.333), (60, 12.0, 3.5),
)
SAX_B = (
    (70, 0.0, 0.667), (72, 0.667, 0.333), (75, 1.0, 1.667),
    (74, 2.667, 0.333), (72, 3.0, 0.667), (70, 3.667, 0.333),
    (72, 4.0, 0.667), (68, 4.667, 0.333), (67, 5.0, 2.5),
    (65, 8.0, 0.667), (67, 8.667, 0.333), (68, 9.0, 1.667),
    (67, 10.667, 0.333), (65, 11.0, 0.667), (63, 11.667, 0.333),
    (65, 12.0, 1.0), (63, 13.0, 2.5),
)
SAX_TAIL = ((72, 0.0, 0.667), (70, 0.667, 0.333), (67, 1.0, 3.0),
            (63, 5.0, 0.667), (65, 5.667, 0.333), (63, 6.0, 4.0))
SAX_STARTS = ((276.0, SAX_A), (312.0, SAX_B), (336.0, SAX_TAIL))

# Full-Steam brass line (bars 22-25) — every note >= 1 beat (no stab
# ambiguity), the section's only sustained brass melody.
BRASS_LINE = ((72, 0.0, 2.5), (75, 3.0, 1.0), (74, 4.0, 1.0), (72, 5.0, 1.0),
              (70, 6.0, 2.5), (67, 9.0, 1.0), (68, 10.0, 1.0),
              (70, 11.0, 1.0), (72, 12.0, 2.5), (75, 15.0, 1.0),
              (77, 16.0, 2.0), (75, 18.0, 1.5), (74, 19.5, 1.5),
              (72, 21.0, 1.5), (67, 22.5, 1.5))

HORN_ANSWER_1 = ((60, 0.0, 3.0), (58, 3.0, 3.0), (56, 6.0, 3.0),
                 (55, 9.0, 2.5))
HORN_ANSWER_2 = ((63, 0.0, 3.0), (62, 3.0, 3.0), (60, 6.0, 3.0),
                 (55, 9.0, 2.5))
HORN_COUNTER = ((60, 0.0, 3.0), (58, 3.0, 3.0), (56, 6.0, 3.0),
                (55, 9.0, 3.0), (56, 12.0, 3.0), (58, 15.0, 3.0),
                (60, 18.0, 3.0), (62, 21.0, 2.5))

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[
        ("i. Platform Zero", M1, M2),
        ("ii. Full Steam", M2, M3),
        ("iii. The Bar Car", M3, M4),
        ("iv. Roof Fight", M4, M5),
        ("v. Emergency Brakes", M5, M6),
        ("vi. Terminus", M6, END),
    ],
    tempo_map=[(M1, 168.0), (M3, 126.0), (M4, 168.0),
               (M5, 132.0), (555.0, 100.0), (M6, 168.0)],
    time_signatures=[(M1, 12, 8), (M4, 7, 8), (M5, 12, 8)],
    keysigs=[(M1, -3, 1)],                        # C minor
    channels=[
        # (ch, name, program, volume, pan, reverb)
        (CH_BASS, "picked bass", 34, 105, 64, 40),
        (CH_GTR, "twang guitar", 27, 100, 54, 48),
        (CH_BRASS, "brass section", 61, 100, 64, 52),
        (CH_HORN, "french horn", 60, 96, 64, 56),
        (CH_STR, "strings", 48, 92, 64, 58),
        (CH_CREEP, "inner line", 48, 88, 64, 52),
        (CH_SAX, "alto sax", 65, 98, 64, 55),
        (CH_TAIKO, "taiko", 116, 102, 74, 50),
        (CH_TIMP, "timpani", 47, 100, 48, 52),
        (DRUMS, "kit", 0, 100, 64, 42),
        (CH_HIT, "orchestra hit", 55, 100, 64, 50),
    ],
    bank_selects=[(7, 1), (10, 1)],   # taiko + the 119 window: set B (prog 55 passes through the alt bank untouched)
    program_changes=[
        (DRUMS, 0.0, 1),          # kit v2 (sizzle hats, snare rattle)
        (DRUMS, M3, 40),          # brush kit for the Bar Car
        (DRUMS, M4, 1),           # v2 back for the fight
        (CH_HIT, 352.0, 119),     # reverse-cymbal riser...
        (CH_HIT, M4, 55),         # ...then orchestra hit again
    ],
    extra_markers=[
        (60.0, "train whistle"),
        (352.0, "riser onto the roof"),
        (717.0, "whistle II"),
        (DIVE_T, "the whammy dive"),
        (STING_T, "unison sting"),
    ],
)

# -- verification config (consumed by verify.run_track) ---------------------
PROGRAM_WHITELIST: set[int] = {34, 27, 61, 60, 48, 65, 116, 47, 55, 119}
CENTERED_CHANNELS: set[int] = {CH_BASS, CH_BRASS, CH_HORN, CH_STR,
                               CH_CREEP, CH_SAX}
NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH_BASS: (36, 55),        # floored at C2 (the low-bed rule)
    CH_GTR: (40, 88),
    CH_BRASS: (58, 84),
    CH_HORN: (43, 79),
    CH_STR: (43, 96),
    CH_CREEP: (48, 72),
    CH_SAX: (53, 84),
    CH_TAIKO: (36, 60),
    CH_TIMP: (36, 57),
    CH_HIT: (48, 72),
}
GAP_WHITELIST: list[tuple[float, float]] = [(773.0, 775.2)]   # the held
# breath between the pre-sting trio and the kill — a scored silence.
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW: tuple[float, float] = (286.0, 297.0)   # ~4:51 written file
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

def _ost_bar(sc: en.Score, t: float, pat, vel: int) -> None:
    """One ostinato bar: eighths on the 0.5 grid, pulse accents."""
    for i, p in enumerate(pat):
        v = vel + (12 if i == 0 else 6 if i % 3 == 0 else 0)
        sc.note(CH_BASS, p, t + 0.5 * i, 0.42, v, jt=3, jv=3)


def _stab(sc: en.Score, t: float, idx: int, vel: int) -> None:
    """One documented close-voiced brass stab (< half a beat)."""
    for p in STAB_V[idx % 4]:
        sc.note(CH_BRASS, p, t, 0.38, vel, jt=1, jv=3)


def _falloff(sc: en.Score, t: float) -> None:
    """Twang fall-off at a note tail: dip ~-3.3 semitones (range 12),
    recentred well inside two-thirds of a beat."""
    sc.bend(CH_GTR, t - 0.3, 0.0)
    en.bend_ramp(sc, CH_GTR, t - 0.25, t + 0.1, 0.0, -0.55, steps=5)
    sc.bend(CH_GTR, t + 0.42, 0.0)


def _whistle(sc: en.Score, w: float, dur: float) -> None:
    """One whistle blast: minor-second brass cluster, gliss up a
    semitone and a half, sag back to centre before release."""
    for p in WHISTLE_CLUSTER:
        sc.note(CH_BRASS, p, w, dur, 90, jt=1, jv=2)
    sc.bend(CH_BRASS, w - 0.02, 0.0)
    en.bend_ramp(sc, CH_BRASS, w, w + 0.5, 0.0, 1.5, steps=6)
    en.bend_ramp(sc, CH_BRASS, w + dur - 0.7, w + dur - 0.1, 1.5, 0.0,
                 steps=6)


def _theme(sc: en.Score, t0: float, oct_shift: int, vel: int) -> None:
    for p, rel, dur in THEME_A:
        sc.note(CH_GTR, p + oct_shift, t0 + rel, dur * 0.96, vel, jt=3, jv=4)
    for r in THEME_FALL_REL:
        _falloff(sc, t0 + r)


def _line(sc: en.Score, ch: int, t0: float, data, vel: int,
          shift: int = 0) -> None:
    for p, rel, dur in data:
        sc.note(ch, p + shift, t0 + rel, dur * 0.97, vel, jt=3, jv=3)


def _dr12(sc: en.Score, t: float, k: int, heat: int = 0) -> None:
    """One 12/8 action bar of kit: driving eighth hats, kick on the
    outer pulses, backbeat snares, open-hat lift, 8-bar fills."""
    if k % 8 == 0:
        sc.hit(49, t, 106 + heat)
    for i in range(12):
        v = 40 + heat + (10 if i % 3 == 0 else 0)
        sc.hit(42, t + 0.5 * i, v, jt=2, jv=3)
    sc.hit(36, t, 102 + heat)
    sc.hit(36, t + 3.0, 100 + heat)
    sc.hit(38, t + 1.5, 102 + heat)
    sc.hit(38, t + 4.5, 104 + heat)
    if k % 2 == 1:
        sc.hit(46, t + 5.5, 76 + heat)
    if k % 8 == 7:
        for j, d in enumerate((47, 45, 41, 38)):
            sc.hit(d, t + 5.0 + 0.25 * j, 84 + heat + 4 * j)


def _dr7(sc: en.Score, t: float, k: int) -> None:
    """One 7/8 roof-fight bar of kit."""
    if k % 8 == 0:
        sc.hit(49, t, 112)
    for i in range(7):
        sc.hit(42, t + 0.5 * i, 46 + (10 if i in (0, 3, 5) else 0),
               jt=2, jv=3)
    sc.hit(36, t, 106)
    sc.hit(36, t + 1.5, 102)
    sc.hit(38, t + 2.5, 108)
    if k % 4 == 3:
        sc.hit(38, t + 3.0, 96)
    if k % 8 == 7:
        sc.hit(47, t + 3.0, 92)
        sc.hit(45, t + 3.25, 96)


def _timp_roll(sc: en.Score, t0: float, v0: int, v1: int) -> None:
    """Two beats of sixteenth roll on C2, crescendo into a downbeat."""
    for j in range(8):
        v = round(en.lerp(v0, v1, j / 7))
        sc.note(CH_TIMP, 36, t0 + 0.25 * j, 0.22, v, jt=2, jv=2)


# ---------------------------------------------------------------------------
# Builders — one per movement
# ---------------------------------------------------------------------------

def _m1_platform_zero(sc: en.Score) -> None:
    """[0, 72) Night station.  Hats tick, a C drone gathers, the ostinato
    fades in from bar 3, twang fragments fall away, the whistle blows."""
    en.bend_range(sc, CH_GTR, 12, 0.0)      # the dive's RPN, authored early
    sc.cc(CH_GTR, 74, 96, 0.0)              # bright twang
    # ticking hats, growing
    for k in range(12):
        t = 6.0 * k
        for i in range(12):
            sc.hit(42, t + 0.5 * i, 28 + 2 * k + (8 if i % 3 == 0 else 0),
                   jt=2, jv=3)
        if k >= 8:
            sc.hit(36, t, 64 + 2 * k)
            sc.hit(36, t + 3.0, 60 + 2 * k)
    # tom fill into Full Steam
    for j, d in enumerate((47, 47, 45, 45, 41, 41, 38, 38)):
        sc.hit(d, 70.0 + 0.25 * j, round(en.lerp(70, 102, j / 7)))
    # the C drone: strings low, then the fifth
    for k in range(6):
        sc.note(CH_STR, 48, 12.0 * k, 11.95, 36 + 3 * k, jt=3, jv=2)
    for k in range(3):
        sc.note(CH_STR, 55, 36.0 + 12.0 * k, 11.95, 40 + 2 * k, jt=3, jv=2)
    en.expr_curve(sc, CH_STR, [(0.0, 40), (36.0, 58), (71.5, 74)], step=2.0)
    # horn swells
    for t, v in ((24.0, 44), (36.0, 48), (54.0, 52)):
        sc.note(CH_HORN, 48, t, 5.8, v, jt=3, jv=2)
    # the ostinato fades in (bars 3-12)
    for k in range(10):
        _ost_bar(sc, 12.0 + 6.0 * k, OST_A, 56 + round(2.4 * k))
    # twang fragments, each falling off the note tail
    for p, t, dur in INTRO_FRAGS:
        sc.note(CH_GTR, p, t, dur * 0.96, 78, jt=3, jv=3)
        _falloff(sc, t + dur)
    # the whistle: two blasts
    _whistle(sc, 60.0, 2.5)
    _whistle(sc, 63.0, 2.0)


def _m2_full_steam(sc: en.Score) -> None:
    """[72, 264) The main action: ostinato A/B, the twang theme (x2 then
    x2 an octave up), horn answers, the brass line, documented stabs."""
    for k in range(32):
        t = M2 + 6.0 * k
        _ost_bar(sc, t, OST_A if k % 2 == 0 else OST_B, 82)
        _dr12(sc, t, k, heat=2)
    # the chromatic inner line — its own channel, semitones only
    for k, p in enumerate(CREEP_FS):
        sc.note(CH_CREEP, p, M2 + 6.0 * k, 5.7, 60, jt=3, jv=2)
    # string fifths, two-bar breaths, lifting for the last statements
    for k in range(16):
        lo, hi, v = (60, 67, 52) if k < 12 else (63, 70, 58)
        sc.note(CH_STR, lo, M2 + 12.0 * k, 11.9, v, jt=3, jv=2)
        sc.note(CH_STR, hi, M2 + 12.0 * k, 11.9, v - 2, jt=3, jv=2)
    # theme statements (Full Steam's four)
    for t0, oct_shift in THEME_STARTS[:4]:
        _theme(sc, t0, oct_shift, 96 + (6 if oct_shift else 0))
        sc.note(CH_HIT, 60, t0, 0.5, 106, jt=1, jv=3)
    # the low B phrase
    _line(sc, CH_GTR, B_STARTS[0], B_PHRASE, 88)
    for r in B_FALL_REL:
        _falloff(sc, B_STARTS[0] + r)
    # horn answers
    _line(sc, CH_HORN, 108.0, HORN_ANSWER_1, 76)
    _line(sc, CH_HORN, 180.0, HORN_ANSWER_2, 80)
    # the brass line takes the tune (bars 22-25)
    _line(sc, CH_BRASS, 204.0, BRASS_LINE, 92)
    # timpani features (bars 12-13, 24-25)
    for base, va in ((144.0, 84), (216.0, 88)):
        sc.note(CH_TIMP, 36, base, 0.8, va, jt=2, jv=2)
        sc.note(CH_TIMP, 43, base + 3.0, 0.6, va - 4, jt=2, jv=2)
        sc.note(CH_TIMP, 36, base + 6.0, 0.8, va + 2, jt=2, jv=2)
        _timp_roll(sc, base + 10.0, 58, 92)
    # documented stabs
    for i, t in enumerate(STAB_TIMES):
        if M2 <= t < M3:
            _stab(sc, t, i, 106)


def _m3_bar_car(sc: en.Score) -> None:
    """[264, 360) The suave interlude: 126 bpm, brush kit, Eb major, the
    sax swinging 2:1 — the ONLY swing in the piece.  A riser at the end
    throws the band onto the roof."""
    for k, pcs in enumerate(BC_CHORDS):
        t = M3 + 6.0 * k
        root = BC_ROOTS[pcs]
        nxt = BC_ROOTS[BC_CHORDS[k + 1]] if k + 1 < 16 else 36
        app = nxt - 1 if nxt - 1 >= 37 else nxt + 1
        sc.note(CH_BASS, root, t, 2.8, 58, jt=3, jv=2)
        sc.note(CH_BASS, root + 7, t + 3.0, 1.8, 54, jt=3, jv=2)
        sc.note(CH_BASS, app, t + 5.0, 0.9, 52, jt=3, jv=2)
        # brushes: ride on the beat, skip-lobe on 1 and 4, soft taps
        for b in range(6):
            sc.hit(51, t + b, 42, jt=2, jv=3)
        for b in (1.667, 4.667):
            sc.hit(51, t + b, 33, jt=2, jv=2)
        sc.hit(38, t + 2.0, 30, jt=2, jv=2)
        sc.hit(38, t + 5.0, 30, jt=2, jv=2)
        sc.hit(36, t, 48, jt=2, jv=2)
        sc.hit(36, t + 3.0, 44, jt=2, jv=2)
        # guitar comps, dry and low, odd bars
        if k % 2 == 1:
            chord = sorted(p for p in range(58, 73)
                           if p % 12 in set(pcs))[:3]
            for p in chord:
                sc.note(CH_GTR, p, t + 1.5, 1.0, 44, jt=3, jv=3)
                sc.note(CH_GTR, p, t + 4.0, 0.8, 40, jt=3, jv=3)
    en.pad_block(sc, CH_STR, M3, list(list(c) for c in BC_CHORDS),
                 span=6.0, size=4, lo=55, hi=79, vel=44, vel_end=48,
                 legato=0.2)
    # the suave reed — swung 2:1, and only here
    sc.cc(CH_SAX, 1, 28, M3)
    en.expr_curve(sc, CH_SAX, [(M3, 66), (300.0, 78), (330.0, 72),
                               (352.0, 60)], step=2.0)
    for t0, phrase in SAX_STARTS:
        for p, rel, dur in phrase:
            sc.note(CH_SAX, p, t0 + rel, dur * 0.94, 74, jt=2, jv=3)
    # the riser onto the roof (GM 119 via the scheduled program change)
    sc.note(CH_HIT, 60, 356.0, 3.9, 82, jt=0, jv=2)


def _m4_roof_fight(sc: en.Score) -> None:
    """[360, 549) Metric modulation to 7/8: the ostinato compresses to
    seven eighths, taiko in every bar, double-time stabs at the climax."""
    for k in range(FIGHT_BARS):
        t = M4 + 3.5 * k
        _ost_bar(sc, t, OST_7, 86)
        _dr7(sc, t, k)
        # taiko — every bar of the fight, nowhere else in the piece
        sc.note(CH_TAIKO, 43, t, 0.5, 112, jt=2, jv=3)
        sc.note(CH_TAIKO, 43, t + 1.0, 0.35, 82, jt=2, jv=3)
        sc.note(CH_TAIKO, 48, t + 1.5, 0.5, 102, jt=2, jv=3)
        sc.note(CH_TAIKO, 36, t + 2.5, 0.6, 118, jt=2, jv=3)
        if k % 4 == 2:
            sc.note(CH_TAIKO, 48, t + 3.0, 0.4, 94, jt=2, jv=3)
        # horn pulses on even bars
        if k % 2 == 0:
            sc.note(CH_HORN, 48, t, 1.3, 72, jt=3, jv=3)
            sc.note(CH_HORN, 55, t + 2.0, 1.3, 70, jt=3, jv=3)
        # timpani on odd bars; rolls into the 8-bar marks
        if k % 2 == 1:
            sc.note(CH_TIMP, 36 if (k // 2) % 2 == 0 else 43, t, 0.6, 88,
                    jt=2, jv=3)
        if k % 8 == 6:
            _timp_roll(sc, t + 1.5, 58, 96)
    # the inner line keeps creeping, a fourth higher
    for k, p in enumerate(CREEP_FIGHT):
        sc.note(CH_CREEP, p, M4 + 3.5 * k, 3.3, 76, jt=3, jv=2)
    # string octaves rising a semitone every nine bars
    for s in range(6):
        for j in range(3):
            t = M4 + 31.5 * s + 10.5 * j
            sc.note(CH_STR, 67 + s, t, 10.4, 62, jt=3, jv=2)
            sc.note(CH_STR, 79 + s, t, 10.4, 58, jt=3, jv=2)
    # guitar riff cells and the falling cells
    for b in FIGHT_RIFF_BARS:
        _line(sc, CH_GTR, M4 + 3.5 * b, FIGHT_RIFF, 90)
    for b in FIGHT_FALL_BARS:
        _line(sc, CH_GTR, M4 + 3.5 * b, FIGHT_FALL_CELL, 94)
        _falloff(sc, M4 + 3.5 * b + 3.25)
    # orchestra hits on the structural downbeats
    for b in (0, 8, 16, 24, 32, 40, 44, 48, 52):
        sc.note(CH_HIT, 60, M4 + 3.5 * b, 0.5, 112, jt=1, jv=3)
    # documented stabs (including the double-time climax)
    for i, t in enumerate(STAB_TIMES):
        if M4 <= t < M5:
            _stab(sc, t, i, 108)
    # snare run off the roof edge, into the brakes
    for j in range(6):
        sc.hit(38, 547.5 + 0.25 * j, round(en.lerp(70, 104, j / 5)))


def _m5_brakes(sc: en.Score) -> None:
    """[549, 561) Emergency brakes: a strictly chromatic string screech
    down 17 semitones, a choked crash, the ride ticking as the wheels
    grind to walking pace (the tempo map does the deceleration)."""
    sc.hit(49, M5, 114)                              # the choked crash
    # Drum NoteOff is deliberately inert because every ordinary hit authors
    # one. CC120 is the standard, explicit all-sound-off signal: choke this
    # crash at its notated quarter-beat without changing any other MIDI.
    sc.cc(DRUMS, 120, 0, M5 + 0.25)
    for j in range(18):
        sc.note(CH_STR, 84 - j, M5 + 0.5 * j, 0.45,
                round(en.lerp(102, 58, j / 17)), jt=2, jv=2)
    sc.note(CH_STR, 55, 558.0, 2.8, 46, jt=3, jv=2)  # the hanging dominant
    for j in range(11):
        sc.hit(51, M5 + float(j), round(en.lerp(52, 34, j / 10)),
               jt=2, jv=2)


def _m6_terminus(sc: en.Score) -> None:
    """[561, 777) The sprint: ostinato back at full heat, theme x3 (the
    last doubled by horn), whistle II, the ONE whammy dive, the pre-sting
    trio of hits, the scored silence, the unison C sting."""
    for k in range(35):
        t = M6 + 6.0 * k
        _ost_bar(sc, t, OST_A if k % 2 == 0 else OST_B, 86)
        _dr12(sc, t, k, heat=6)
    # inner line, resolving onto the sting's C
    for k, p in enumerate(CREEP_TERM):
        sc.note(CH_CREEP, p, M6 + 6.0 * k, 5.7, 70, jt=3, jv=2)
    # string beds
    for k in range(11):
        sc.note(CH_STR, 60, M6 + 12.0 * k, 11.9, 54, jt=3, jv=2)
        sc.note(CH_STR, 67, M6 + 12.0 * k, 11.9, 52, jt=3, jv=2)
    for t, lo, hi in ((693.0, 67, 79), (705.0, 70, 82)):
        sc.note(CH_STR, lo, t, 11.9, 62, jt=3, jv=2)
        sc.note(CH_STR, hi, t, 11.9, 58, jt=3, jv=2)
    for t in (729.0, 741.0, 753.0):
        sc.note(CH_STR, 72, t, 11.9, 66, jt=3, jv=2)
        sc.note(CH_STR, 84, t, 11.9, 62, jt=3, jv=2)
    # themes (the third doubled by the horn an octave down)
    for t0, oct_shift in THEME_STARTS[4:]:
        _theme(sc, t0, oct_shift, 100 + (6 if oct_shift else 0))
        sc.note(CH_HIT, 60, t0, 0.5, 108, jt=1, jv=3)
    for p, rel, dur in THEME_A:
        sc.note(CH_HORN, p - 12, 669.0 + rel, dur * 0.97, 84, jt=3, jv=3)
    _line(sc, CH_HORN, 597.0, HORN_COUNTER, 78)
    # the low B phrase again
    _line(sc, CH_GTR, B_STARTS[1], B_PHRASE, 92)
    for r in B_FALL_REL:
        _falloff(sc, B_STARTS[1] + r)
    # orchestra hits on the statements and the dive bar
    for t in (621.0, 645.0, 693.0, 741.0):
        sc.note(CH_HIT, 60, t, 0.5, 108, jt=1, jv=3)
    # timpani four-bar downbeats, then the roll into the trio
    for k in range(0, 33, 4):
        sc.note(CH_TIMP, 36, M6 + 6.0 * k, 0.8, 92, jt=2, jv=3)
    _timp_roll(sc, 769.0, 62, 104)
    # whistle II
    _whistle(sc, 717.0, 2.5)
    _whistle(sc, 720.0, 2.0)
    # the chug: palm-of-the-hand eighths under the dive
    for j in range(30):                              # 729 .. 744
        sc.note(CH_GTR, 48, 729.0 + 0.5 * j, 0.4, 84, jt=2, jv=3)
    for j in range(35):                              # 747.5 .. 765
        sc.note(CH_GTR, 48, 747.5 + 0.5 * j, 0.4, 86, jt=2, jv=3)
    # THE whammy dive: RPN-12 channel, full-depth, monotonic, recentred
    sc.note(CH_GTR, 72, DIVE_T, 3.0, 112, jt=1, jv=2)
    sc.bend(CH_GTR, DIVE_T + 0.3, 0.0)
    en.bend_ramp(sc, CH_GTR, DIVE_T + 0.5, DIVE_T + 2.2, 0.0, -2.0,
                 steps=17)
    sc.bend(CH_GTR, DIVE_T + 2.9, -2.0)
    sc.bend(CH_GTR, DIVE_T + 3.3, 0.0)
    # documented stabs (terminus punctuation + the pre-sting trio)
    for i, t in enumerate(STAB_TIMES):
        if M6 <= t:
            _stab(sc, t, i, 114 if t >= 771.0 else 108)
    for t in (771.0, 772.0, 773.0):
        sc.note(CH_TIMP, 36, t, 0.4, 112, jt=1, jv=2)
        sc.note(CH_HIT, 60, t, 0.4, 114, jt=1, jv=2)
        sc.note(CH_BASS, 36, t, 0.4, 112, jt=1, jv=2)
        sc.hit(36, t, 116, jt=1)
    sc.hit(49, 771.0, 112, jt=1)
    # ...one and a half beats of held breath (GAP_WHITELIST)...
    # the sting: ONE pitch class, eight melodic channels, fortissimo
    for ch, p, v in ((CH_BASS, 36, 118), (CH_GTR, 60, 114),
                     (CH_BRASS, 72, 116), (CH_HORN, 60, 114),
                     (CH_STR, 72, 112), (CH_CREEP, 60, 110),
                     (CH_SAX, 72, 110), (CH_TIMP, 36, 116)):
        sc.note(ch, p, STING_T, 0.7, v, jt=0, jv=2)
    sc.note(DRUMS, 36, STING_T, 0.25, 120, jt=0, jv=2)


BUILDERS: list = [_m1_platform_zero, _m2_full_steam, _m3_bar_car,
                  _m4_roof_fight, _m5_brakes, _m6_terminus]


# ---------------------------------------------------------------------------
# Oracle helpers — score readers (ticks, not beats, for exactness)
# ---------------------------------------------------------------------------

_PPQ = en.PPQ
MELODIC_CHANNELS = (CH_BASS, CH_GTR, CH_BRASS, CH_HORN, CH_STR,
                    CH_CREEP, CH_SAX, CH_TAIKO, CH_TIMP, CH_HIT)


def _tk(beat: float) -> int:
    return int(round(beat * _PPQ))


def _note_ons(sc: en.Score, ch: int) -> list[tuple[int, int, int]]:
    """[(tick, pitch, vel)] for every note-on of the channel."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)


def _spans(sc: en.Score, ch: int) -> list[tuple[int, int, int, int]]:
    """[(on, off, pitch, vel)] with FIFO on/off pairing (verify's rule)."""
    pending: dict[int, list[tuple[int, int]]] = {}
    out = []
    for tick, _prio, data in sorted(sc.events.get(ch, []),
                                    key=lambda e: (e[0], e[1])):
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick, data[1], vel))
    return sorted(out)


def _bend_lane(sc: en.Score, ch: int) -> list[tuple[int, float]]:
    """[(tick, frac)]: raw bend as a fraction (-1..+1) of the channel's
    full bend range (whatever RPN 0 declares that range to be)."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick, (raw - 8192) / 8192.0))
    return sorted(out)


# ---------------------------------------------------------------------------
# Oracles — written BEFORE the music; the track is composed to pass them.
# ---------------------------------------------------------------------------

def oracles(sc: en.Score, info, spans) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []

    # --- meter_map: 12/8 -> 7/8 (the fight, exactly) -> 12/8 --------------
    fails: list[str] = []
    want_ts = [(M1, 12, 8), (M4, 7, 8), (M5, 12, 8)]
    if sorted(sc.timesigs) != want_ts:
        fails.append(f"time signatures {sorted(sc.timesigs)} != {want_ts}")
    name, t0, t1 = PART.MOVEMENTS[3]
    if (t0, t1) != (M4, M5):
        fails.append(f"'{name}' spans [{t0}, {t1}), want the 7/8 region "
                     f"[{M4}, {M5})")
    if abs((M5 - M4) - FIGHT_BARS * 3.5) > 1e-9:
        fails.append(f"7/8 region is {(M5 - M4) / 3.5:.2f} bars, want "
                     f"{FIGHT_BARS} whole bars")
    if abs((M3 - M2) % 6.0) > 1e-9 or abs((END - M6) % 3.0) > 1e-9:
        fails.append("12/8 sections are not whole numbers of bars")
    results.append(("meter_map", fails))

    # --- ostinato_relentless: >= 90% of eighth slots in every action span -
    fails = []
    bass_ticks = [t for t, _p, _v in _note_ons(sc, CH_BASS)]
    tol = int(round(0.1 * _PPQ))
    for a, b in ACTION_SPANS:
        n_slots = int(round((b - a) / 0.5))
        covered = 0
        for k in range(n_slots):
            slot = _tk(a + 0.5 * k)
            i = bisect.bisect_left(bass_ticks, slot - tol)
            if i < len(bass_ticks) and bass_ticks[i] <= slot + tol:
                covered += 1
        cov = covered / max(1, n_slots)
        if cov < 0.90:
            fails.append(f"span [{a:.0f}, {b:.0f}): bass covers only "
                         f"{cov:.1%} of the eighth grid (want >= 90%)")
    results.append(("ostinato_relentless", fails))

    # --- brass_stabs: every documented hit lands >= 3 close short notes;
    #     every short brass note sits ON a documented hit ------------------
    fails = []
    brass = _spans(sc, CH_BRASS)
    tol = int(round(0.08 * _PPQ))
    stab_ticks = [_tk(t) for t in STAB_TIMES]
    for t_beat, st in zip(STAB_TIMES, stab_ticks):
        grp = [(on, off, p) for on, off, p, _v in brass
               if abs(on - st) <= tol]
        if len(grp) < 3:
            fails.append(f"stab at {t_beat:.1f}: only {len(grp)} notes "
                         f"(want >= 3)")
            continue
        ps = sorted(p for _on, _off, p in grp)
        if ps[-1] - ps[0] > 12:
            fails.append(f"stab at {t_beat:.1f}: span {ps[-1] - ps[0]} "
                         f"> 12 semitones")
        for on, off, p in grp:
            if off - on > int(0.5 * _PPQ) + 2:
                fails.append(f"stab at {t_beat:.1f}: pitch {p} lasts "
                             f"{(off - on) / _PPQ:.2f} beats (> 0.5)")
    for on, off, p, _v in brass:
        if off - on <= int(0.55 * _PPQ):
            i = bisect.bisect_left(stab_ticks, on - tol)
            if not (i < len(stab_ticks) and stab_ticks[i] <= on + tol):
                fails.append(f"stray short brass note (pitch {p}) at beat "
                             f"{on / _PPQ:.2f} is on no documented hit")
    results.append(("brass_stabs", fails[:8]))

    # --- whammy_dive: RPN 0 = 12, ONE full-depth monotonic dive, recentred
    fails = []
    r101 = r100 = None
    authored = []                       # (tick, semis) bend-range writes
    for tick, _prio, data in sorted(sc.events.get(CH_GTR, []),
                                    key=lambda e: (e[0], e[1])):
        if (data[0] & 0xF0) != 0xB0:
            continue
        num, val = data[1], data[2]
        if num == 101:
            r101 = val
        elif num == 100:
            r100 = val
        elif num == 6 and r101 == 0 and r100 == 0:
            authored.append((tick, val))
    if [semis for _t, semis in authored] != [12]:
        fails.append(f"guitar RPN-0 writes {authored}: want exactly one, "
                     f"= 12 semitones")
    elif authored[0][0] > _tk(DIVE_T):
        fails.append("bend range 12 authored after the dive")
    lane = _bend_lane(sc, CH_GTR)
    dive_lo, dive_hi = _tk(DIVE_T), _tk(DIVE_T + 3.5)
    deep = [(t, f) for t, f in lane if f <= -0.9]
    if not deep:
        fails.append("no full-depth dive anywhere")
    else:
        if min(f for _t, f in deep) > -0.98:
            fails.append(f"dive bottoms out at {min(f for _t, f in deep):+.2f}"
                         f" of range (want <= -0.98)")
        strays = [t for t, _f in deep if not dive_lo <= t <= dive_hi]
        if strays:
            fails.append(f"deep bend outside the dive bar at beats "
                         f"{[round(t / _PPQ, 1) for t in strays[:3]]}")
    seg = [f for t, f in lane
           if _tk(DIVE_T + 0.4) <= t <= _tk(DIVE_T + 2.3)]
    if any(f1 > f0 + 1e-9 for f0, f1 in zip(seg, seg[1:])):
        fails.append("the dive wobbles on the way down (not monotonic)")
    rec = [t for t, f in lane
           if _tk(DIVE_T + 2.3) <= t <= _tk(DIVE_T + 3.5) and abs(f) <= 0.02]
    if not rec:
        fails.append("dive not recentred straight after the bottom")
    results.append(("whammy_dive", fails))

    # --- falloff_bends: 38 documented fall-offs, dip and recentre ----------
    fails = []
    if len(FALLOFF_TIMES) != 38:
        fails.append(f"{len(FALLOFF_TIMES)} documented fall-offs, want 38")
    for t in FALLOFF_TIMES:
        win = [f for tk, f in lane if _tk(t - 0.4) <= tk <= _tk(t + 0.2)]
        if not win or min(win) > -0.12:
            fails.append(f"fall-off at {t:.2f}: no dip below -0.12 "
                         f"of range")
        rec = [tk for tk, f in lane
               if _tk(t) <= tk <= _tk(t + 0.667) and abs(f) <= 0.02]
        if not rec:
            fails.append(f"fall-off at {t:.2f} not recentred within "
                         f"two-thirds of a beat")
    results.append(("falloff_bends", fails[:8]))

    # --- swing_confined: 2:1 swing in the Bar Car, and ONLY there ----------
    fails = []
    bc0, bc1 = _tk(M3), _tk(M4)
    sax_in = [(t, p, v) for t, p, v in _note_ons(sc, CH_SAX)
              if bc0 <= t < bc1]
    if not sax_in:
        fails.append("the suave reed never plays in the Bar Car")
    lobe = 0
    for t, _p, _v in sax_in:
        pos = (t % _PPQ) / _PPQ
        on_beat = pos <= 0.04 or pos >= 0.96
        on_lobe = abs(pos - 2.0 / 3.0) <= 0.04
        if not (on_beat or on_lobe):
            fails.append(f"sax onset at beat {t / _PPQ:.2f} is neither on "
                         f"the beat nor at beat+2/3 (pos {pos:.3f})")
        if on_lobe:
            lobe += 1
    if lobe < 12:
        fails.append(f"only {lobe} swing-lobe onsets (want >= 12)")
    ons = sorted(t for t, _p, _v in sax_in)
    pair_tol = int(round(0.05 * _PPQ))
    pairs = sum(1 for a, b, c in zip(ons, ons[1:], ons[2:])
                if abs((b - a) - 2 * _PPQ // 3) <= pair_tol
                and abs((c - b) - _PPQ // 3) <= pair_tol)
    if pairs < 8:
        fails.append(f"only {pairs} strict 2:1 long-short pairs "
                     f"(want >= 8)")
    for ch in MELODIC_CHANNELS:
        for t, p, _v in _note_ons(sc, ch):
            if bc0 <= t < bc1:
                continue
            pos = (t % _PPQ) / _PPQ
            if 0.60 <= pos <= 0.73:
                fails.append(f"ch{ch} onset in the swing lobe at beat "
                             f"{t / _PPQ:.2f} — swing must stay in the "
                             f"Bar Car")
    results.append(("swing_confined", fails[:8]))

    # --- chromatic_creep: the inner line moves by semitone only ------------
    fails = []
    creep = _note_ons(sc, CH_CREEP)
    for name, t0, t1 in PART.MOVEMENTS:
        seq = [p for t, p, _v in creep
               if _tk(t0) - 24 <= t < _tk(t1) - 24]
        for a, b in zip(seq, seq[1:]):
            if abs(b - a) != 1:
                fails.append(f"'{name}': creep steps {a} -> {b} "
                             f"(|{b - a}| != 1 semitone)")
    if len(creep) < 100:
        fails.append(f"only {len(creep)} creep notes — the inner line "
                     f"must run the action")
    if creep:
        last_t, last_p, _v = creep[-1]
        prev_p = creep[-2][1] if len(creep) > 1 else None
        if last_t != _tk(STING_T) or last_p % 12 != 0:
            fails.append("the creep's last note is not the sting's C")
        elif prev_p is not None and last_p - prev_p != 1:
            fails.append(f"the creep resolves {prev_p} -> {last_p}, "
                         f"want a +1 semitone resolution onto C")
    results.append(("chromatic_creep", fails[:8]))

    # --- whistle_gliss: brass cluster + >= half-range gliss, recentred ----
    fails = []
    brass_lane = _bend_lane(sc, CH_BRASS)
    for w, dur in WHISTLE_BLASTS:
        grp = [(on, off, p) for on, off, p, _v in brass
               if abs(on - _tk(w)) <= int(0.08 * _PPQ)
               and off - on > _PPQ]
        if len(grp) < 3:
            fails.append(f"whistle at {w:.0f}: only {len(grp)} sustained "
                         f"cluster notes (want >= 3)")
            continue
        ps = sorted(p for _on, _off, p in grp)
        if any(b - a > 2 for a, b in zip(ps, ps[1:])):
            fails.append(f"whistle at {w:.0f}: pitches {ps} are not a "
                         f"cluster (adjacent gaps must be <= 2)")
        win = [f for t, f in brass_lane
               if _tk(w) <= t <= _tk(w + dur)]
        if not win or max(win) < 0.5:
            fails.append(f"whistle at {w:.0f}: bend gliss peaks at "
                         f"{max(win) if win else 0:+.2f} (want >= +0.50 "
                         f"of range)")
        tail = [f for t, f in brass_lane
                if _tk(w + dur - 0.3) <= t <= _tk(w + dur + 0.3)]
        if not tail or abs(tail[-1]) > 0.02:
            fails.append(f"whistle at {w:.0f}: gliss not recentred by "
                         f"the end of the blast")
    results.append(("whistle_gliss", fails))

    # --- brakes_gesture: chromatic string screech + choked crash ----------
    fails = []
    run_notes = [(t, p) for t, p, _v in _note_ons(sc, CH_STR)
                 if _tk(M5) - 24 <= t < _tk(558.0) - 24]
    run_notes.sort()
    if len(run_notes) < 13:
        fails.append(f"brake gliss has {len(run_notes)} notes — cannot "
                     f"span 12 chromatic semitones")
    else:
        for (t0, p0), (_t1, p1) in zip(run_notes, run_notes[1:]):
            if p1 - p0 != -1:
                fails.append(f"brake gliss step {p0} -> {p1} at beat "
                             f"{t0 / _PPQ:.1f} is not a falling semitone")
        span = run_notes[0][1] - run_notes[-1][1]
        if span < 12:
            fails.append(f"brake gliss spans {span} semitones (want >= 12)")
    chokes = [(on, off) for on, off, p, _v in _spans(sc, DRUMS)
              if p == 49 and abs(on - _tk(M5)) <= int(0.08 * _PPQ)]
    if not chokes:
        fails.append("no crash cymbal on the brake downbeat")
    elif any(off - on > int(0.5 * _PPQ) for on, off in chokes):
        fails.append("the brake crash rings — it must be choked "
                     "(<= 0.5 beat)")
    all_sound_off = [tick for tick, _prio, data in sc.events.get(DRUMS, [])
                     if (data[0] & 0xF0) == 0xB0 and data[1] == 120]
    if _tk(M5 + 0.25) not in all_sound_off:
        fails.append("the brake crash has no explicit CC120 choke at its "
                     "notated note-off")
    results.append(("brakes_gesture", fails[:8]))

    # --- taiko_fight: GM 116 in all 54 fight bars and nowhere else --------
    fails = []
    taiko = [t for t, _p, _v in _note_ons(sc, CH_TAIKO)]
    for k in range(FIGHT_BARS):
        lo, hi = _tk(M4 + 3.5 * k) - 24, _tk(M4 + 3.5 * (k + 1)) - 24
        i = bisect.bisect_left(taiko, lo)
        if not (i < len(taiko) and taiko[i] < hi):
            fails.append(f"fight bar {k + 1} has no taiko")
    strays = [t for t in taiko
              if not _tk(M4) - 24 <= t < _tk(M5) - 24]
    if strays:
        fails.append(f"taiko outside the fight at beats "
                     f"{[round(t / _PPQ, 1) for t in strays[:4]]}")
    results.append(("taiko_fight", fails[:8]))

    # --- unison_sting: one pitch class C, >= 4 channels, <= 1 beat, ff,
    #     out of a scored silence, and nothing after ------------------------
    fails = []
    sting_tick = _tk(STING_T)
    sting_chs = set()
    for ch in sorted(sc.events):
        for on, off, p, v in _spans(sc, ch):
            if on > sting_tick + 24:
                fails.append(f"ch{ch} note at beat {on / _PPQ:.2f} AFTER "
                             f"the sting — the sting must kill the piece")
            if abs(on - sting_tick) > 24:
                continue
            if ch == DRUMS:
                continue                    # the kick is punctuation
            sting_chs.add(ch)
            if p % 12 != 0:
                fails.append(f"sting note on ch{ch} is pitch {p} — not C")
            if off - on > _PPQ + 4:
                fails.append(f"sting note on ch{ch} lasts "
                             f"{(off - on) / _PPQ:.2f} beats (> 1)")
            if v < 100:
                fails.append(f"sting note on ch{ch} at velocity {v} — "
                             f"want fortissimo (>= 100)")
    if len(sting_chs) < 4:
        fails.append(f"sting spans only {len(sting_chs)} melodic channels "
                     f"(want >= 4)")
    held = [(ch, t) for ch in sorted(sc.events)
            for t, _p, _v in _note_ons(sc, ch)
            if _tk(773.5) <= t < _tk(774.95)]
    if held:
        fails.append(f"notes inside the held breath [773.5, 775): {held[:3]}")
    results.append(("unison_sting", fails[:8]))

    # --- dramatic_arc: per-beat velocity-sum densities ---------------------
    fails = []
    all_ons: list[tuple[int, int]] = []
    for ch in sc.events:
        all_ons.extend((t, v) for t, _p, v in _note_ons(sc, ch))
    all_ons.sort()
    ticks = [t for t, _v in all_ons]

    def density(a: float, b: float) -> float:
        i0 = bisect.bisect_left(ticks, _tk(a))
        i1 = bisect.bisect_left(ticks, _tk(b))
        return sum(v for _t, v in all_ons[i0:i1]) / max(1e-9, b - a)

    d_intro = density(M1, M2)
    d_fs = density(M2, M3)
    d_bc = density(M3, M4)
    d_rf = density(M4, M5)
    d_term = density(M6, 771.0)
    for name, got, op, ratio in (
            ("intro", d_intro, "<", 0.60), ("Bar Car", d_bc, "<", 0.55),
            ("Roof Fight", d_rf, ">", 1.15), ("Terminus", d_term, ">", 1.00)):
        want = ratio * d_fs
        ok = got < want if op == "<" else got > want
        if not ok:
            fails.append(f"{name} density {got:.0f} is not {op} "
                         f"{ratio:.2f}x Full Steam ({d_fs:.0f}/beat)")
    results.append(("dramatic_arc", fails))

    return results


# ---------------------------------------------------------------------------
# Audio oracles — run by analyze.py once audio/11 - Night Train to
# Tirana.wav exists.  Trimmed inner windows keep seams and reverb honest.
# ---------------------------------------------------------------------------

AUDIO_INTRO = (12.0, 66.0)
AUDIO_FULL_STEAM = (84.0, 252.0)
AUDIO_BAR_CAR = (276.0, 348.0)
AUDIO_FIGHT = (367.0, 542.0)
AUDIO_TERMINUS = (567.0, 756.0)
AUDIO_HUSH = (773.9, 774.85)
AUDIO_STING = (775.0, 775.7)


def _goertzel_power(x: list[float], rate: int, freq: float) -> float:
    """Normalized Goertzel power of `x` at `freq` Hz."""
    w = 2.0 * math.pi * freq / rate
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for v in x:
        s0 = v + coeff * s1 - s2
        s2, s1 = s1, s0
    return max(0.0, s1 * s1 + s2 * s2 - coeff * s1 * s2) / max(1, len(x)) ** 2


def audio_checks(ctx) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []

    def span_db(a: float, b: float) -> float:
        i0, i1 = ctx.bar_window(a, b)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    # 1. The dramatic arc, in dB on the render.
    fails: list[str] = []
    intro = span_db(*AUDIO_INTRO)
    fs = span_db(*AUDIO_FULL_STEAM)
    bc = span_db(*AUDIO_BAR_CAR)
    rf = span_db(*AUDIO_FIGHT)
    term = span_db(*AUDIO_TERMINUS)
    if intro > fs - 2.0:
        fails.append(f"intro {intro:.1f} dB not >= 2 dB under Full Steam "
                     f"{fs:.1f}")
    if bc > fs - 3.0:
        fails.append(f"Bar Car {bc:.1f} dB not >= 3 dB under Full Steam "
                     f"{fs:.1f}")
    if rf < fs + 0.3:
        fails.append(f"Roof Fight {rf:.1f} dB not above Full Steam "
                     f"{fs:.1f} + 0.3")
    if term < fs - 0.5:
        fails.append(f"Terminus {term:.1f} dB sags below Full Steam "
                     f"{fs:.1f} - 0.5")
    checks.append(("audio_dynamic_arc", fails))

    # 2. The sting is C — Goertzel energy at C1..C5 vs foreign pitch
    #    classes (D, Eb, F#, A; G is skipped: it is C's 3rd harmonic).
    fails = []
    i0, i1 = ctx.bar_window(*AUDIO_STING)
    i1 = min(i1, len(ctx.l))
    mono = [(ctx.l[i] + ctx.r[i]) / 2.0 for i in range(i0, i1)]
    if len(mono) < 256:
        fails.append("sting window missing from the render")
    else:
        c_e = sum(_goertzel_power(mono, ctx.sample_rate, f)
                  for f in (65.41, 130.81, 261.63, 523.25))
        o_e = sum(_goertzel_power(mono, ctx.sample_rate, f)
                  for f in (293.66, 311.13, 369.99, 440.0))
        if c_e < 5.0 * o_e:
            fails.append(f"sting C-energy only {c_e / max(o_e, 1e-12):.1f}x "
                         f"the foreign-pitch energy (want >= 5x)")
    checks.append(("audio_sting_unison", fails))

    # 3. The cutoff: silence before, a leap, then a die-away to nothing.
    fails = []
    hush = span_db(*AUDIO_HUSH)
    sting = span_db(*AUDIO_STING)
    if sting < hush + 8.0:
        fails.append(f"sting {sting:.1f} dB does not leap >= 8 dB out of "
                     f"the held breath ({hush:.1f} dB)")
    on_s = ctx.sc.seconds_at(AUDIO_STING[0])

    def sec_db(a: float, b: float) -> float:
        i0 = int(a * ctx.sample_rate)
        i1 = min(int(b * ctx.sample_rate), len(ctx.l))
        if i1 - i0 < 256:
            return -120.0
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    d1 = sec_db(on_s + 1.0, on_s + 1.6)
    d2 = sec_db(on_s + 2.2, on_s + 3.2)
    if d1 > sting - 6.0:
        fails.append(f"1s after the sting still {d1:.1f} dB "
                     f"(want <= sting - 6)")
    if d2 > -120.0 and d2 > sting - 15.0:
        fails.append(f"2.2s after the sting still {d2:.1f} dB "
                     f"(want <= sting - 15)")
    checks.append(("audio_sting_cutoff", fails))

    return checks
