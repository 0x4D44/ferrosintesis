"""movements/t04_the_empty_house.py — track 4 of *The Remaining*.

MEMORY, INTERIOR — the piano at the centre throughout, walking the rooms of
a house someone has left.  Four movements, one continuous interior:

  I.  Rooms      — solo piano.  THE VIGIL THEME *inverted* about degree 3
                   (axis F: material.invert_theme) in the right hand, sung
                   over widely-spaced left-hand tenths.  A sostenuto pedal
                   (CC66) catches a low D at each section start and holds it
                   while the hands change harmony above; the una corda (CC67)
                   is down the whole movement.
  II. The Music Box — a celesta plays THE THEME in diminution / 4 at the top
                   of the keyboard (the child's music box) over the piano's
                   HOLED departure figure — the SAME {3,6} holes as T1, the
                   house still missing exactly those two notes.  A harp lays
                   one arpeggio per ground cycle.  The box repeats once per
                   cycle and each time forgets its ending sooner: 6 notes,
                   then 5, then 4, then 3 — memory fading.  (It loses the
                   waiting tone E first, then the rest.)
  III. Hum      — a choir enters on closed vowels (mm -> oo, never "ah"),
                   pianissimo, under the piano's UN-HOLED figure — the first
                   whole statement of the ostinato since the departure (hope,
                   briefly).  Violin I sings one octave-high thread of the
                   theme and lets it hang on the waiting tone E (degree 2;
                   home is still withheld).
  IV. Clock     — everything gone but the celesta, reduced to a single stuck
                   E (the waiting tone as a stopped clock), decelerating and
                   spacing out irregularly as it winds down.  Then silence,
                   and one lone bass D, four beats, pianissimo.

Every structural device is oracle-pinned below against material.py: the
inversion is exact, the erosion sequence is [6,5,4,3], the holes are T1's,
the choir never opens past "oo", the piano dominates the note count, the
Clock strictly decelerates, and the sung thread ends on the waiting tone.
"""

from __future__ import annotations

import conductor
import engine as en
import material

NUMBER = 4
TITLE = "The Empty House"
FILE = "04 - The Empty House.mid"
SEED = 20261004
COMMENT = (
    "Memory, interior - the piano at the centre throughout. The vigil theme "
    "inverted about its third sings over widely-spaced tenths; a celesta "
    "music box plays the theme in diminution over the piano's holed figure - "
    "the house still missing the same two notes as the departure - and each "
    "repeat forgets its ending sooner, 6 notes to 3. A choir hums on closed "
    "vowels under the first un-holed figure since the departure, and a violin "
    "lets one octave-high thread hang on the waiting tone E. Then everything "
    "is gone but a celesta ticking a single stuck E, a clock winding down, "
    "and one lone bass D, pianissimo.")

# ---------------------------------------------------------------------------
# Pinned geometry (the oracles below verify all of it against material.py)
# ---------------------------------------------------------------------------

PIANO, CELESTA, HARP, CHOIR, VLN1, BASS = 0, 1, 2, 3, 4, 5

_MM = material.MODE_MINOR
_PPQ = en.PPQ

BASE_RH = en.n("D5")                     # 74 — the inverted-theme register (RH)
BASE_BOX = en.n("D6")                    # 86 — the music box, top of the keyboard
BASE_VLN = en.n("D5")                    # 74 — vln I's octave-high theme thread
CLOCK_E = en.pitch(BASE_BOX, _MM, 2)     # 88 — E6, the box's own waiting tone
HARP_BASE = en.n("D3")                   # 50 — the harp arpeggio's low root

# the piano ground (Dm - Bb - F - C), one chord per bar; the departure figure
# and the left-hand tenths both walk these roots
PIANO_ROOTS = [en.n("D3"), en.n("Bb2"), en.n("F3"), en.n("C3")]   # [50,46,53,48]
MINORITY = [True, False, False, False]                            # chord thirds
TENTHS = [15 if m else 16 for m in MINORITY]                      # LH tenth span

PEDAL_D = en.n("D2")                     # 38 — the sostenuto-caught low D (I)
BASS_D = en.n("D2")                      # 38 — the lone final bass D (IV)

HOLED_SET = tuple(sorted(set(range(8)) - set(material.HOLES)))    # (0,1,2,4,5,7)
BOX_EROSION = [6, 5, 4, 3]               # notes per music-box repeat (II)

# the choir hum: ground root + fifth per bar, in the low-mid register (III)
CHOIR_ROOTS = [en.n("D3"), en.n("Bb2"), en.n("F3"), en.n("C3")]   # [50,46,53,48]

# the harp arpeggio: a Dm spread over two octaves, one per ground cycle (II)
HARP_DEGREES = [1, 3, 5, 8, 10, 12]

VLN_T0 = 148.0                           # vln I's theme thread enters (III)

# IV — the clock: irregular, decelerating celesta taps, then a lone bass D
CLOCK_TAPS = [192.0, 193.5, 195.25, 197.25, 199.5, 202.0,
              205.0, 208.5, 213.0, 216.5, 222.0, 224.5]
BASS_D_T0 = 231.0
END = 238.0

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Rooms", 0.0, 64.0),
               ("II. The Music Box", 64.0, 128.0),
               ("III. Hum", 128.0, 192.0),
               ("IV. Clock", 192.0, END)],
    tempo_map=[
        # I. Rooms — heavy rubato around 54, deep phrase-end dips
        (0.0, 54.0), (6.0, 50.0), (8.0, 54.0), (14.0, 49.0), (16.0, 53.0),
        (24.0, 50.0), (30.0, 47.0), (32.0, 53.0), (40.0, 50.0), (48.0, 54.0),
        (54.0, 49.0), (56.0, 53.0), (62.0, 48.0),
        # II. The Music Box
        (64.0, 53.0), (72.0, 49.0), (80.0, 54.0), (88.0, 50.0), (96.0, 52.0),
        (104.0, 48.0), (112.0, 53.0), (120.0, 49.0), (126.0, 47.0),
        # III. Hum — warms to 54 at its close (the brief hope), then holds
        (128.0, 52.0), (134.0, 54.0), (140.0, 50.0), (148.0, 54.0),
        (156.0, 50.0), (164.0, 53.0), (172.0, 50.0), (180.0, 53.0),
        (188.0, 54.0),
        # IV. Clock — strictly decelerating, 54 -> 40
        (192.0, 54.0), (200.0, 50.0), (208.0, 46.0), (216.0, 43.0),
        (222.0, 41.0), (228.0, 40.0)],
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],
    channels=[(PIANO, "piano", 0, 100, material.SEATING["piano"], 58),
              (CELESTA, "celesta", 8, 88, material.SEATING["celesta"], 66),
              (HARP, "harp", 46, 80, material.SEATING["harp"], 60),
              (CHOIR, "choir", 52, 78, material.SEATING["choir"], 72),
              (VLN1, "violin I", 40, 90, material.SEATING["violin1"], 66),
              (BASS, "sub bass", 38, 84, material.SEATING["bass"], 40)],
    extra_markers=[(BASS_D_T0, "the last chime")],
)

PROGRAM_WHITELIST = {0, 8, 46, 52, 40, 38}
CENTERED_CHANNELS = {PIANO, CHOIR, BASS}          # seats 64; celesta/harp/vln offset
NOTE_RANGES = {PIANO: (36, 81), CELESTA: (84, 96), HARP: (48, 72),
               CHOIR: (44, 62), VLN1: (72, 84), BASS: (33, 45)}
# the Clock winds down to nothing but the celesta: the widening taps and the
# stopped-clock pause before the final bass D are scored silence
GAP_WHITELIST: list[tuple[float, float]] = [(200.0, END)]
BEND_EXEMPT: set[int] = set()
DURATION_WINDOW = (276.0, 291.0)                  # ~283s, tightened after the build
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []


# ---------------------------------------------------------------------------
# Emitters (every oracle-pinned lane is jt=0 — tick-exact)
# ---------------------------------------------------------------------------

def _inv_theme(sc, t0, vel, vel_end):
    """One statement of THE VIGIL THEME diatonically inverted about degree 3
    (material.invert_theme) in the right hand.  Ends on degree 4, not home."""
    notes = material.theme_notes(invert_axis=material.INVERT_AXIS)
    total = notes[-1][0] + notes[-1][1]
    for on, du, deg in notes:
        v = round(en.lerp(vel, vel_end, on / total))
        sc.note(PIANO, en.pitch(BASE_RH, _MM, deg), t0 + on, du * 0.95, v,
                jt=0, jv=0)


def _box(sc, t0, count, vel):
    """The music box: THE THEME in diminution / 4, its first `count` notes,
    at the top of the keyboard (oracle-pinned, jt=0)."""
    for on, du, deg in material.theme_notes(stretch=0.25)[:count]:
        sc.note(CELESTA, en.pitch(BASE_BOX, _MM, deg), t0 + on, du * 0.9, vel,
                jt=0, jv=0)


def _harp_arp(sc, t0, vel):
    """One rising harp arpeggio (a Dm spread over two octaves) per cycle."""
    for i, deg in enumerate(HARP_DEGREES):
        sc.note(HARP, en.pitch(HARP_BASE, _MM, deg), t0 + 0.3 * i, 1.6,
                vel - i, jt=1, jv=2)


def _vln_theme(sc, t0):
    """Violin I sings the theme an octave high, augmented x2, and lets the
    waiting tone E hang (degree 2 — home is withheld; jt=0, oracle-pinned)."""
    notes = material.theme_notes(stretch=2.0)
    total = notes[-1][0] + notes[-1][1]                     # 16 beats
    for i, (on, du, deg) in enumerate(notes):
        last = (i == len(notes) - 1)
        d = 8.0 if last else du * 0.95                      # the hang
        v = round(en.lerp(46, 58, on / total))
        sc.note(VLN1, en.pitch(BASE_VLN, _MM, deg), t0 + on, d, v, jt=0, jv=0)
        if du >= 1.9:
            en.vibrato(sc, VLN1, t0 + on + 0.5,
                       (d if last else du * 0.9) - 0.8, depth=0.16 + 0.02 * i)
    en.expr_curve(sc, VLN1, [(t0, 42), (t0 + 6.0, 82), (t0 + 12.0, 70),
                             (t0 + total + 4.0, 40)], step=1.0)
    en.cc_curve(sc, VLN1, 1, [(t0, 18), (t0 + total, 46)], step=2.0)
    sc.bend(VLN1, t0 + total + 4.5, 0.0)                    # recentre before III end


# ---------------------------------------------------------------------------
# I. Rooms [0, 64) — solo piano: inverted theme over tenths, sostenuto low D
# ---------------------------------------------------------------------------

def _b_rooms(sc):
    en.soft_pedal(sc, PIANO, 0.0, 63.9)                     # una corda throughout
    swell = [0, 1, 2, 3, 2, 1, 0, -1]
    # two 8-bar sections; each catches a low D under sostenuto while the hands
    # change harmony above it
    for sec in range(2):
        t0 = sec * 32.0
        sc.note(PIANO, PEDAL_D, t0, 31.4, 34 + 2 * sec, jt=0, jv=0)
        en.sostenuto(sc, PIANO, t0 + 0.02, t0 + 31.6)
    # left-hand tenths, one per bar
    for b in range(16):
        root = PIANO_ROOTS[b % 4]
        bar_t = 4.0 * b
        vel = 40 + swell[b % 8]
        sc.note(PIANO, root, bar_t, 3.8, vel - 4, jt=0, jv=1)
        sc.note(PIANO, root + TENTHS[b % 4], bar_t, 3.8, vel, jt=0, jv=1)
        en.sustain(sc, PIANO, bar_t, bar_t + 3.8)
    # the inverted theme, once per ground cycle (breathing dynamics)
    for c, (v0, v1) in enumerate([(46, 50), (48, 52), (47, 51), (43, 47)]):
        _inv_theme(sc, 16.0 * c, v0, v1)
    en.expr_curve(sc, PIANO, [(0.0, 80), (24.0, 92), (40.0, 86), (56.0, 78),
                              (63.0, 70)], step=2.0)


# ---------------------------------------------------------------------------
# II. The Music Box [64, 128) — celesta box over the HOLED piano figure
# ---------------------------------------------------------------------------

def _b_musicbox(sc):
    en.soft_pedal(sc, PIANO, 64.0, 127.9)
    swell = [0, 1, 2, 2, 1, 0, -1, -1]
    for b in range(16, 32):
        bar_t = 4.0 * b
        vel = 42 + swell[b % 8]
        material.play_figure(sc, PIANO, bar_t, PIANO_ROOTS[b % 4],
                             minor=MINORITY[b % 4], vel=vel, vel_end=vel + 5,
                             holes=material.HOLES, jt=0, jv=1)
        en.sustain(sc, PIANO, bar_t, bar_t + 3.9)
    en.expr_curve(sc, PIANO, [(64.0, 82), (96.0, 88), (127.0, 76)], step=2.0)

    # the celesta music box: once per ground cycle, forgetting its end sooner
    for k, count in enumerate(BOX_EROSION):
        _box(sc, 64.0 + 16.0 * k, count, vel=48 - 2 * k)
    en.expr_curve(sc, CELESTA, [(64.0, 74), (96.0, 60), (120.0, 46)], step=4.0)

    # the harp: a single arpeggio per ground cycle
    for k in range(4):
        _harp_arp(sc, 64.0 + 16.0 * k, vel=40 - k)
    en.expr_curve(sc, HARP, [(64.0, 66), (96.0, 58), (120.0, 46)], step=4.0)


# ---------------------------------------------------------------------------
# III. Hum [128, 192) — choir on closed vowels under the UN-HOLED figure
# ---------------------------------------------------------------------------

def _b_hum(sc):
    en.soft_pedal(sc, PIANO, 128.0, 191.9)
    swell = [0, 1, 2, 2, 1, 0, -1, 0]
    for b in range(32, 48):
        bar_t = 4.0 * b
        vel = 40 + swell[b % 8]
        material.play_figure(sc, PIANO, bar_t, PIANO_ROOTS[b % 4],
                             minor=MINORITY[b % 4], vel=vel, vel_end=vel + 4,
                             holes=frozenset(), jt=0, jv=1)          # UN-holed
        en.sustain(sc, PIANO, bar_t, bar_t + 3.9)
    en.expr_curve(sc, PIANO, [(128.0, 78), (160.0, 88), (191.0, 80)], step=2.0)

    # the choir hum: closed vowels only (mm -> oo, never "ah"), pp
    en.vowel_curve(sc, CHOIR, [(128.0, 0), (160.0, 30), (191.0, 45)], step=1.0)
    for b in range(32, 48):
        bar_t = 4.0 * b
        root = CHOIR_ROOTS[b % 4]
        vel = 34 + (swell[b % 8] if swell[b % 8] > 0 else 0)
        sc.note(CHOIR, root, bar_t, 3.8, vel, jt=0, jv=1)
        sc.note(CHOIR, root + 7, bar_t, 3.8, vel - 2, jt=0, jv=1)
    en.expr_curve(sc, CHOIR, [(128.0, 28), (160.0, 44), (191.0, 32)], step=2.0)

    # violin I: one octave-high thread of the theme, hanging on the waiting tone
    _vln_theme(sc, VLN_T0)


# ---------------------------------------------------------------------------
# IV. Clock [192, 238) — a single stuck E winding down, then a lone bass D
# ---------------------------------------------------------------------------

def _b_clock(sc):
    for i, t in enumerate(CLOCK_TAPS):
        nxt = CLOCK_TAPS[i + 1] if i + 1 < len(CLOCK_TAPS) else t + 2.0
        dur = min(1.1, (nxt - t) * 0.85)
        vel = max(32, 40 - i)
        sc.note(CELESTA, CLOCK_E, t, dur, vel, jt=0, jv=0)
    en.expr_curve(sc, CELESTA, [(192.0, 40), (210.0, 32), (225.0, 24)], step=2.0)

    # the lone bass D — four beats, pianissimo
    sc.note(BASS, BASS_D, BASS_D_T0, 4.0, 34, jt=0, jv=0)
    en.expr_curve(sc, BASS, [(BASS_D_T0, 30), (BASS_D_T0 + 4.0, 18)], step=1.0)


BUILDERS = [_b_rooms, _b_musicbox, _b_hum, _b_clock]


# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES §2 pattern)
# ---------------------------------------------------------------------------

def _tick(beat):
    return max(0, int(round(beat * _PPQ)))


def _ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _onset_ticks(sc, ch):
    out = set()
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.add((tick, d[1]))
    return out


def _cc_lane(sc, ch, num):
    return sorted((t / _PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


# ---------------------------------------------------------------------------
# Oracles
# ---------------------------------------------------------------------------

def _o_inversion(sc):
    """I: the right hand states THE VIGIL THEME diatonically inverted about
    degree 3, exactly (recomputed from material), at each cycle start."""
    fails = []
    if material.INVERT_AXIS != 3:
        fails.append(f"inversion axis is {material.INVERT_AXIS}, want 3")
    inv = material.theme_notes(invert_axis=material.INVERT_AXIS)
    # the inversion must map the theme's contour 5-4-3-4-3-2 -> 1-2-3-2-3-4
    if [d for _on, _du, d in inv] != [1, 2, 3, 2, 3, 4]:
        fails.append(f"inverted degrees {[d for _o, _u, d in inv]} "
                     f"!= [1,2,3,2,3,4]")
    if inv[-1][2] == 1:
        fails.append("the inverted theme must not END on degree 1 (home)")
    piano = _onset_ticks(sc, PIANO)
    for c in range(4):
        t0 = 16.0 * c
        for k, (on, _du, deg) in enumerate(inv):
            want = (_tick(t0 + on), en.pitch(BASE_RH, _MM, deg))
            if want not in piano:
                fails.append(f"cycle {c}, note {k}: no RH onset at beat "
                             f"{t0 + on:.2f} pitch {want[1]} (degree {deg})")
    return fails[:8]


def _o_erosion(sc):
    """II: the music box repeats once per cycle, each repeat one note shorter
    (6 -> 5 -> 4 -> 3), matching the diminished theme prefix note for note."""
    fails = []
    if BOX_EROSION != [6, 5, 4, 3]:
        fails.append(f"erosion sequence {BOX_EROSION} != [6,5,4,3]")
    for a, b in zip(BOX_EROSION, BOX_EROSION[1:]):
        if b != a - 1:
            fails.append(f"erosion must fall by one note per repeat: {BOX_EROSION}")
            break
    if BOX_EROSION and BOX_EROSION[-1] != 3:
        fails.append(f"the box must erode down to 3 notes, got {BOX_EROSION[-1]}")
    dim = material.theme_notes(stretch=0.25)
    cel = {(t, p) for t, p in [(round(b, 6), p) for b, p, _v in _ons(sc, CELESTA)]
           if b < 128.0}
    for k, count in enumerate(BOX_EROSION):
        t0 = 64.0 + 16.0 * k
        window = [(b, p) for b, p, _v in _ons(sc, CELESTA)
                  if t0 - 1e-9 <= b < t0 + 3.9]
        if len(window) != count:
            fails.append(f"repeat {k}: {len(window)} box notes in its cycle, "
                         f"want {count}")
        for j in range(count):
            on, _du, deg = dim[j]
            want = (round(t0 + on, 6), en.pitch(BASE_BOX, _MM, deg))
            if want not in cel:
                fails.append(f"repeat {k}, note {j}: no box onset at beat "
                             f"{t0 + on:.3f} pitch {want[1]}")
    return fails[:8]


def _o_holes(sc):
    """II: the piano's figure carries exactly T1's holes — quavers {3,6} gone,
    {0,1,2,4,5,7} present — recomputed from material.HOLES, and III is un-holed."""
    fails = []
    if set(material.HOLES) != {3, 6} or HOLED_SET != (0, 1, 2, 4, 5, 7):
        fails.append(f"holes {sorted(material.HOLES)} / played {HOLED_SET} "
                     f"do not match T1's {{3,6}}")
    bars = {}
    for b, _p, _v in _ons(sc, PIANO):
        if b < 64.0 or b >= 192.0:                     # figures live in II & III
            continue
        q = (b % 4.0) / 0.5
        if abs(q - round(q)) > 1e-6:
            fails.append(f"piano figure off the quaver grid at beat {b:.3f}")
            continue
        bars.setdefault(int(b // 4) * 4, set()).add(int(round(q)))
    for bar, quavers in sorted(bars.items()):
        want = set(HOLED_SET) if bar < 128.0 else set(range(8))   # II holed, III full
        tag = "holed (II)" if bar < 128.0 else "un-holed (III)"
        if quavers != want:
            fails.append(f"{tag} bar {bar:.0f}: quavers {sorted(quavers)} "
                         f"want {sorted(want)}")
    return fails[:8]


def _o_vowels(sc):
    """III: the choir never opens past 'oo' — every vowel CC70 value < 60
    everywhere on the track."""
    fails = []
    seen = False
    for ch in sorted(sc.events):
        for beat, val in _cc_lane(sc, ch, 70):
            seen = True
            if val >= 60:
                fails.append(f"ch{ch} vowel {val} at beat {beat:.1f} reaches "
                             f"open (>= 60); the choir stays closed on T4")
    if not seen:
        fails.append("no vowel automation found — the choir must hum")
    return fails[:8]


def _o_centrality(sc):
    """The piano is the centre: it has at least as many note-ons as any other
    channel on the track."""
    fails = []
    counts = {ch: len(_ons(sc, ch)) for ch in sc.events}
    piano = counts.get(PIANO, 0)
    for ch, n in sorted(counts.items()):
        if ch != PIANO and n > piano:
            fails.append(f"ch{ch} has {n} note-ons > piano's {piano} — the "
                         f"piano must stay central")
    if piano <= 0:
        fails.append("the piano is silent")
    return fails[:8]


def _o_clock(sc):
    """IV: everything gone but the celesta, ticking a single stuck E; the
    tempo strictly decelerates; the last event is the lone bass D."""
    fails = []
    tm = [(t, b) for t, b in PART.TEMPO_MAP if 192.0 <= t < END]
    bpms = [b for _t, b in tm]
    if len(bpms) < 4:
        fails.append(f"only {len(bpms)} tempo events in the Clock — too few")
    for a, b in zip(bpms, bpms[1:]):
        if b >= a:
            fails.append(f"Clock tempo not strictly falling: {bpms}")
            break
    if bpms and (bpms[0] < 48 or bpms[-1] > 42):
        fails.append(f"Clock must wind down from ~54 to ~40, got "
                     f"{bpms[0]}..{bpms[-1]}")
    # only the celesta (and the final bass D) may sound in IV
    for ch in sorted(sc.events):
        if ch in (CELESTA, BASS):
            continue
        late = [b for b, _p, _v in _ons(sc, ch) if b >= 192.0]
        if late:
            fails.append(f"ch{ch} still sounds in the Clock (first at "
                         f"{late[0]:.1f}); only the celesta remains")
    cel = _ons(sc, CELESTA)
    ticks = [(b, p) for b, p, _v in cel if b >= 192.0]
    if len(ticks) != len(CLOCK_TAPS):
        fails.append(f"{len(ticks)} clock taps, want {len(CLOCK_TAPS)}")
    for j, (b, p) in enumerate(ticks):
        if p != CLOCK_E:
            fails.append(f"clock tap {j} pitch {p} != the stuck E {CLOCK_E}")
        if j < len(CLOCK_TAPS) and abs(b - CLOCK_TAPS[j]) > 1e-6:
            fails.append(f"clock tap {j} at {b:.2f}, want {CLOCK_TAPS[j]:.2f}")
    # the taps must space out (a decelerating clock), ending irregularly wide
    gaps = [round(CLOCK_TAPS[i + 1] - CLOCK_TAPS[i], 3)
            for i in range(len(CLOCK_TAPS) - 1)]
    if max(gaps) < 3.0 or gaps[0] > gaps[-1]:
        fails.append(f"clock taps do not wind down (gaps {gaps})")
    # the lone bass D is the final note-on, pp, four beats
    allons = sorted((b, ch, p) for ch in sc.events
                    for b, p, _v in _ons(sc, ch))
    if not allons or allons[-1][1] != BASS or allons[-1][2] != BASS_D:
        fails.append("the last note must be the lone bass D")
    bass = _ons(sc, BASS)
    if len(bass) != 1 or abs(bass[0][0] - BASS_D_T0) > 1e-6:
        fails.append(f"the bass must play exactly one D at {BASS_D_T0}, got "
                     f"{[(round(b, 2), p) for b, p, _v in bass]}")
    return fails[:8]


def _o_theme_end(sc):
    """III: violin I's sung thread is the theme (augmented x2), ends on the
    waiting tone E (degree 2), and never sounds home (degree 1)."""
    fails = []
    notes = material.theme_notes(stretch=2.0)
    v1 = _ons(sc, VLN1)
    tonic_pc = en.pitch(BASE_VLN, _MM, 1) % 12
    waiting_pc = en.pitch(BASE_VLN, _MM, material.THEME_END_DEG) % 12
    stray = [b for b, p, _v in v1 if p % 12 == tonic_pc]
    if stray:
        fails.append(f"violin I sounds home (degree 1) at beat {stray[0]:.1f} "
                     f"— withheld from the theme voice on tracks 1-4")
    ticks = _onset_ticks(sc, VLN1)
    for k, (on, _du, deg) in enumerate(notes):
        want = (_tick(VLN_T0 + on), en.pitch(BASE_VLN, _MM, deg))
        if want not in ticks:
            fails.append(f"vln thread note {k}: no onset at beat "
                         f"{VLN_T0 + on:.2f} pitch {want[1]} (degree {deg})")
    if v1:
        last_deg_pitch = en.pitch(BASE_VLN, _MM, material.THEME_END_DEG)
        if v1[-1][1] != last_deg_pitch:
            fails.append(f"vln I ends on pitch {v1[-1][1]} (pc {v1[-1][1] % 12}), "
                         f"not the waiting tone E ({last_deg_pitch})")
        if v1[-1][1] % 12 != waiting_pc:
            fails.append("the sung thread must hang on the waiting tone")
    return fails[:8]


def _o_rubato():
    """The album's most rubato track: a non-flat map, dips in every movement,
    a final ritardando to 40."""
    fails = []
    tm = PART.TEMPO_MAP
    bpms = [b for _t, b in tm]
    if len(tm) < 14:
        fails.append(f"only {len(tm)} tempo events — too flat for heavy rubato")
    if max(bpms) - min(bpms) < 8.0:
        fails.append(f"tempo range {max(bpms) - min(bpms):.0f} bpm under 8")
    dips = sum(1 for a, b in zip(bpms, bpms[1:]) if b < a)
    if dips < 6:
        fails.append(f"only {dips} tempo dips — not enough breathing")
    if bpms[-1] > 42.0:
        fails.append(f"final tempo {bpms[-1]} — the clock must wind to ~40")
    for name, t0, t1 in PART.MOVEMENTS:
        seg = [b for t, b in tm if t0 <= t < t1]
        if not any(b2 < b1 for b1, b2 in zip(seg, seg[1:])):
            fails.append(f"no tempo dip inside '{name}'")
    return fails


def oracles(sc, info, spans):
    return [
        ("inversion_exactness", _o_inversion(sc)),
        ("music_box_erosion", _o_erosion(sc)),
        ("holes_identity", _o_holes(sc)),
        ("vowel_ceiling", _o_vowels(sc)),
        ("piano_centrality", _o_centrality(sc)),
        ("clock_deceleration", _o_clock(sc)),
        ("theme_end_degree2", _o_theme_end(sc)),
        ("rubato_nonflat", _o_rubato()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — proven on the render, not the event data
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    # 1. Movement I is real, present piano (the room is not empty of sound).
    a0, a1 = ctx.bar_window(8.0, 56.0)
    rooms = ctx.db(ctx.rms(ctx.l, ctx.r, a0, a1))
    fails = []
    if rooms < -46.0:
        fails.append(f"Rooms {rooms:.1f} dB — the piano is inaudibly quiet")
    checks.append(("audio_rooms_present", fails))

    # 2. The ending is spare: the lone bass D window sits well under the body
    #    of the piece, yet is not dead silence.
    b0, b1 = ctx.bar_window(150.0, 188.0)
    body = ctx.db(ctx.rms(ctx.l, ctx.r, b0, b1))
    c0, c1 = ctx.bar_window(BASS_D_T0, BASS_D_T0 + 4.0)
    coda = ctx.db(ctx.rms(ctx.l, ctx.r, c0, c1))
    fails = []
    if coda > body - 6.0:
        fails.append(f"final bass D {coda:.1f} dB not >= 6 dB under the body "
                     f"{body:.1f} dB")
    if coda < -60.0:
        fails.append(f"final bass D {coda:.1f} dB — the last chime vanished")
    checks.append(("audio_spare_ending", fails))
    return checks
