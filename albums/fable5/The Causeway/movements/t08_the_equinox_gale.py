"""movements/t08_the_equinox_gale.py — track 8 of *The Causeway* (Act Two).

THE EQUINOX GALE.  The album's heaviest track — the storm that cannot part
them.  The causeway has been drowned for weeks; the strait is at its widest of
the whole record (42/86).  This is a Stranglehold vamp with Rough Ride weight:
a rock organ on a fast Leslie, two driven guitars, a horn section rasping with
channel aftertouch, and a protagonist bass that churns D aeolian while the gale
riff (HOOK8 — three hammered notes slamming down a major sixth, the pitch-
retrograde of the fusion head) drives the octaves.  D minor, 4/4, and — unlike
every other track — NO tide-breath anywhere: the storm owns the whole tempo map
with an authored, lurching shape (surge 116->134, collapse to 68 at the end),
pinned by its own oracle.

Four movements:
  I.  Glass Falling  — the pressure drop: low drones, a sealed choir (vowel
      <= 45), the timpani tapping GALE in Morse on its own lane (program 47,
      the gale's thunder), and HOOK8 assembling in fragments that never quite
      complete.
  II. The Gale       — the riff track: HOOK8 on the driven guitar and bass in
      octaves (the doubled thumb IS the riff), horn stabs answering with an
      aftertouch rasp (the Stranglehold engine), the rock organ on a fast
      Leslie.  THE THESIS OF THE ACT: both shore themes are stated INTO the
      storm and overlap twice (island left, mainland right, both in D, downbeat
      consonant) — the storm cannot part them.
  III. Eye           — sudden near-silence (the drop is whitelisted): one
      forward FUSION alone on the piano (the language holds in the eye), then
      THE REACH (the road home, six notes now) — snatched away as the back wall
      hits on a crash re-entry.
  IV. Blown Out      — collapse: the riff halved and hollow (no octave double),
      and NO BENEDICTION.  The final cadence lands on the iv (the bass's last
      note is G) and REFUSES the tonic — no melodic channel lands D in the
      pinned final window.  Then the lone bell buoy tolls the D the music would
      not: exactly eight strikes, and nothing after them.

NO HERALD (documented exemption, HLD addendum s1.10 / s2 T8): the storm arrives
unannounced — there is no breath-flute inhale before the gale, by design.  The
final cadence is UNRESOLVED (HLD s1.9): T8 is NOT in ACT2_PLAGAL_TRACKS, so
this module writes its own unresolved-final oracle instead of
plagal_final_failures.  All recurring data is single-sourced from material.py.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 8
TITLE = "The Equinox Gale"
FILE = "08 - The Equinox Gale.mid"
SEED = 202607188
COMMENT = (
    "The Equinox Gale - the album's heaviest track, the storm that cannot "
    "part them.  The causeway drowned for weeks; the strait at its widest.  A "
    "Stranglehold vamp with Rough Ride weight: rock organ on a fast Leslie, "
    "driven guitars, a horn section rasping with aftertouch, a protagonist "
    "bass churning D aeolian while the gale riff (three hammered notes slamming "
    "down a major sixth) drives the octaves.  D minor, 4/4, an authored "
    "lurching storm tempo with no tide-breath - surge to 134 and collapse to "
    "68.  Glass Falling drops the pressure over low drones, a sealed choir and "
    "the timpani tapping GALE in Morse; The Gale states both shore themes INTO "
    "the storm and overlaps them twice, the storm unable to part them; the Eye "
    "falls to near-silence for one fusion and the road home, six notes reached "
    "and snatched away by a crash; and Blown Out collapses on the halved riff "
    "to an unresolved iv - the tonic refused - before the buoy tolls the D the "
    "music would not, eight times.")

# ---------------------------------------------------------------------------
# Channels.  The re-opened strait at its widest (42/86): island-pole voices
# (the two rock organs and the sealed choir) sit hard left at 42; mainland-pole
# voices (the mainland-theme guitar and the horn section) sit hard right at 86;
# the neutral spine (bass, the octave-doubling guitar, timpani Morse, kit, the
# eye's piano, the bell buoy, the low drone) holds 64.
# ---------------------------------------------------------------------------

CH_BASS, CH_GTR, CH_MAIN, CH_BRASS = 0, 1, 2, 3
CH_ORGAN, CH_ISLE, CH_CHOIR, CH_DRONE = 4, 5, 6, 7
CH_TIMP, CH_DRUMS, CH_PIANO, CH_BELLS = 8, 9, 10, 11

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (42, 86)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 2, 2

_MM = material.MODE_MINOR                               # D aeolian - the storm

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 128.0
II_T0 = 128.0
II_END = 400.0
III_T0 = 400.0
III_END = 448.0
IV_T0 = 448.0
END = 584.0

# the two choruses of the gale (HOOK8 in the bass, the octave double engaged)
CHORUS_SPANS = [(160.0, 256.0), (288.0, 384.0)]

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE = en.n("D4")               # 62 - island deg1 = D (tonic pc 2)
MAINLAND_BASE = en.n("D4")             # 62 - mainland deg1 = D (tonic pc 2)
OVERLAP_T0 = [176.0, 304.0]            # the two island+mainland overlaps in II
FUSION_T0 = 406.0                      # the eye: one forward fusion, alone
FUSION_BASE = en.n("D4")               # 62 - fusion deg1 = D (tonic pc 2)
REACH_T0 = 440.0                       # the road home, six notes, then snatched
REACH_BASE = en.n("D4")               # 62 - the retrograde's held tonic D
CRASH_T0 = 448.0                       # the back wall hits (IV's crash re-entry)

BASS_HOOK_ROOT = en.n("A2")            # 45 - HOOK8 in the bass: A-A-A slam to C
MORSE_T0 = 16.0
MORSE_PITCH = en.n("D2")               # 38 - the timpani's fixed low thunder

# the unresolved final: the bass lands the iv (G, pc 7) and no melodic channel
# lands the tonic D (pc 2) anywhere in this window; the bell buoy is exempt.
FINAL_WINDOW = (544.0, 561.0)
FINAL_G = en.n("G2")                   # 43 - the iv the bass refuses to leave
TOLL_T0 = 562.0
TOLL_PITCH = en.n("D3")                # 50 - pc 2 = the D the music would not land

# ---------------------------------------------------------------------------
# THE AUTHORED STORM TEMPO MAP.  No tide-breath anywhere on this track (HLD
# addendum s1.10): the storm owns the whole map with a lurching shape, pinned
# here and checked by _o_storm_tempo.  I. drops the glass (a wobbling descent);
# II. surges and lurches 116<->134 (the gale); III. falls near-still for the
# eye; IV. collapses monotonically to 68 (blown out).
# ---------------------------------------------------------------------------

STORM_TEMPO: list[tuple[float, float]] = [
    # I. Glass Falling - the barometer wobbling down
    (0.0, 100.0), (16.0, 96.0), (32.0, 100.0), (48.0, 92.0),
    (64.0, 96.0), (80.0, 90.0), (96.0, 94.0), (112.0, 88.0),
    # II. The Gale - surge and lurch
    (128.0, 116.0), (144.0, 126.0), (160.0, 112.0), (176.0, 132.0),
    (192.0, 118.0), (208.0, 130.0), (224.0, 114.0), (240.0, 128.0),
    (256.0, 120.0), (272.0, 134.0), (288.0, 116.0), (304.0, 130.0),
    (320.0, 122.0), (336.0, 132.0), (352.0, 118.0), (368.0, 128.0),
    (384.0, 124.0),
    # III. Eye - near-still
    (400.0, 80.0), (416.0, 76.0), (432.0, 78.0),
    # IV. Blown Out - the collapse (strictly descending to the end)
    (448.0, 118.0), (464.0, 110.0), (480.0, 102.0), (496.0, 94.0),
    (512.0, 86.0), (528.0, 80.0), (544.0, 74.0), (560.0, 68.0),
]

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Glass Falling", 0.0, I_END),
               ("II. The Gale", II_T0, II_END),
               ("III. Eye", III_T0, III_END),
               ("IV. Blown Out", IV_T0, END)],
    tempo_map=STORM_TEMPO,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 1)],                 # D minor: one flat (signed), minor
    channels=[(CH_BASS, "protagonist bass", 34, 104, 64, 22),
              (CH_GTR, "driven guitar (octaves)", 30, 96, 64, 24),
              (CH_MAIN, "mainland guitar", 29, 92, MAIN_PAN, 30),
              (CH_BRASS, "horn section", 61, 96, MAIN_PAN, 34),
              (CH_ORGAN, "rock organ", 18, 92, ISL_PAN, 40),
              (CH_ISLE, "island organ", 18, 88, ISL_PAN, 40),
              (CH_CHOIR, "sealed choir", 52, 78, ISL_PAN, 46),
              (CH_DRONE, "storm drone", 89, 80, 64, 50),
              (CH_TIMP, "timpani morse", 47, 90, 64, 36),
              (CH_DRUMS, "kit", 0, 100, 64, 26),
              (CH_PIANO, "eye piano", 0, 88, 64, 44),
              (CH_BELLS, "bell buoy", 14, 90, 64, 54)],
    extra_markers=[(MORSE_T0, "GALE (morse)"),
                   (OVERLAP_T0[0], "the storm cannot part them"),
                   (CHORUS_SPANS[1][0], "the gale, harder"),
                   (III_T0, "the eye"), (REACH_T0, "the road home"),
                   (CRASH_T0, "the back wall"), (TOLL_T0, "the buoy")],
)

PROGRAM_WHITELIST = {0, 14, 18, 29, 30, 34, 47, 52, 61, 89}
CENTERED_CHANNELS = {CH_BASS, CH_GTR, CH_DRONE, CH_TIMP, CH_DRUMS,
                     CH_PIANO, CH_BELLS}
NOTE_RANGES = {
    CH_BASS: (26, 50), CH_GTR: (46, 60), CH_MAIN: (60, 74),
    CH_BRASS: (44, 74), CH_ORGAN: (33, 74), CH_ISLE: (60, 72),
    CH_CHOIR: (48, 72), CH_DRONE: (24, 55), CH_TIMP: (38, 38),
    CH_PIANO: (60, 74), CH_BELLS: (50, 50),
}
# The eye's near-silence is intended (HLD s2 T8): the drop after the storm, the
# held breath between the fusion and the road home, and the hang before the
# back wall hits are all whitelisted, plus the pre-toll settle in the collapse.
GAP_WHITELIST: list[tuple[float, float]] = [
    (398.0, 408.0),      # the drop into the eye
    (412.0, 441.0),      # the held breath between the fusion and the reach
    (445.0, 449.0),      # the reach snatched away, before the back wall
    (555.0, 563.0),      # the collapse settling before the buoy
]
BEND_EXEMPT: set[int] = set()               # the rasp is aftertouch, not bend
DURATION_WINDOW = (336.0, 356.0)            # ~5:45 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# Click-scan cap: the provisional 28000 was CALIBRATED against the real
# render (lead's pass, 2026.07.19) and removed — the gale's measured max
# step is 19412, comfortably inside the album default (22000).  The V3
# kit's dense cymbals step far less than the sampled brush kit does
# (see t07/t09), so the loudest track needs no override at all.

# ---------------------------------------------------------------------------
# Oracle helpers (COMPOSER-NOTES sec.3 pattern; beat-based, tick where noted)
# ---------------------------------------------------------------------------

_PPQ = en.PPQ
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}


def _tick(beat: float) -> int:
    return max(0, int(round(beat * _PPQ)))


def _note_ons(sc, ch):
    out = []
    for tick, _p, d in sc.events.get(ch, []):
        if (d[0] & 0xF0) == 0x90 and d[2] > 0:
            out.append((tick / _PPQ, d[1], d[2]))
    return sorted(out)


def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _p, d in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = d[0] & 0xF0
        if s == 0x90 and d[2] > 0:
            pending.setdefault(d[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and d[2] == 0):
            q = pending.get(d[1])
            if q:
                out.append((q.pop(0) / _PPQ, tick / _PPQ, d[1]))
    return sorted(out)


def _cc_lane(sc, ch, num):
    return sorted((t / _PPQ, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)


def _aftertouch_lane(sc, ch):
    return sorted((t / _PPQ, d[1]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xD0)


def _onsets_in(sc, ch, lo, hi):
    return [(b, p, v) for b, p, v in _note_ons(sc, ch) if lo - 1e-6 <= b < hi]


def _pitch_at(sc, ch, beat):
    return [p for on, off, p in _note_spans(sc, ch)
            if on - 1e-6 <= beat < off - 1e-6]


def _in_chorus(beat):
    return any(lo <= beat < hi for lo, hi in CHORUS_SPANS)


# ---------------------------------------------------------------------------
# Harmony.  D aeolian, a heavy Stranglehold vamp: i - bVII - bVI - bVII (Dm - C
# - Bb - C), voiced as root-fifth power chords so the gale has no third to
# clash with the mainland theme's raised leading tone when the shores overlap.
# ---------------------------------------------------------------------------

# The four-bar storm cycle: (bass root pitch, power-chord voicing on the organ).
STORM_CYCLE = [
    (en.n("D2"), [en.n("D2"), en.n("A2"), en.n("D3"), en.n("A3")]),   # i
    (en.n("C2"), [en.n("C2"), en.n("G2"), en.n("C3"), en.n("G3")]),   # bVII
    (en.n("Bb1"), [en.n("Bb1"), en.n("F2"), en.n("Bb2"), en.n("F3")]),  # bVI
    (en.n("C2"), [en.n("C2"), en.n("G2"), en.n("C3"), en.n("G3")]),   # bVII
]

# The bass churn: a relentless stepwise eighth-note ostinato through D aeolian
# (index into BASS_SCALE), the Rough Ride engine that keeps the protagonist
# line stepwise-dominant under the leaping riff.
BASS_SCALE = [en.n(x) for x in
              ("D1", "E1", "F1", "G1", "A1", "Bb1", "C2", "D2", "E2", "F2",
               "G2", "A2", "Bb2", "C3", "D3")]
#              0     1     2     3     4     5      6     7     8     9
#              10    11    12     13    14
CHURN_CELL = [7, 8, 9, 8, 7, 6, 5, 6]        # D2-E2-F2-E2-D2-C2-Bb1-C2 (stepwise)

# The horn-section stabs (D aeolian triads, mid register): the Stranglehold
# answer, each stab rasping with a channel-aftertouch swell.
BRASS_STABS = [
    [en.n("D3"), en.n("F3"), en.n("A3")],    # Dm  (i)
    [en.n("C3"), en.n("E3"), en.n("G3")],    # C   (bVII)   - E natural passing
    [en.n("Bb2"), en.n("D3"), en.n("F3")],   # Bb  (bVI)
    [en.n("C3"), en.n("E3"), en.n("G3")],    # C   (bVII)
]

# ---------------------------------------------------------------------------
# Emitters.  Oracle-pinned lanes (the two themes, HOOK8, the fusion, the reach,
# the Morse, the tolls, the doubled thumb, the final cadence) are jt=0 so every
# statement is findable and the gale locks hard; the drums take a light jitter.
# ---------------------------------------------------------------------------

def _chord_idx(beat):
    """Which storm-cycle step a bar belongs to (choruses start on i)."""
    return int(beat // 4) % 4


def _drone(sc, t0, t1, vel):
    """The low storm drone: a D power-fifth pedal (D1-A1-D2) held in eight-beat
    swells, contiguous so the gale never lifts off the floor.  jt=0 - it sits
    on the seams."""
    pitches = [en.n("D1"), en.n("A1"), en.n("D2")]
    b = t0
    while b < t1 - 1e-6:
        dur = min(8.0, t1 - b) * 0.98
        for p in pitches:
            sc.note(CH_DRONE, p, b, dur, vel, jt=0, jv=2)
        b += 8.0


def _choir_bed(sc, t0, t1, vpts, vowel_pts, cc1):
    """The sealed choir: a low D-aeolian open voicing held under the storm, its
    mouth kept shut (CC70 <= 45 always).  `vpts`/`vowel_pts` are (beat, value)
    breakpoints for CC11 and CC70; `cc1` for a slow modulation."""
    voicing = [en.n("D3"), en.n("A3"), en.n("F3")]
    b = t0
    while b < t1 - 1e-6:
        dur = min(8.0, t1 - b) * 0.99
        for p in voicing:
            sc.note(CH_CHOIR, p, b, dur, 44, jt=0, jv=2)
        b += 8.0
    en.expr_curve(sc, CH_CHOIR, vpts, step=4.0)
    en.vowel_curve(sc, CH_CHOIR, vowel_pts, step=4.0)
    en.cc_curve(sc, CH_CHOIR, 1, cc1, step=8.0)


def _organ_bed(sc, t0, t1, vel, leslie_pts, gate=0.98):
    """The rock organ's power-chord vamp, one voicing per bar through the storm
    cycle, plus the Leslie choreography (CC1): slow in the pressure drop,
    ramped FAST in the gale.  A chord channel, never a statement channel."""
    bar = t0
    while bar < t1 - 1e-6:
        _root, voicing = STORM_CYCLE[_chord_idx(bar)]
        dur = min(4.0, t1 - bar) * gate
        for p in voicing:
            sc.note(CH_ORGAN, p, bar, dur, vel, jt=0, jv=2)
        bar += 4.0
    en.cc_curve(sc, CH_ORGAN, 1, leslie_pts, step=1.0)


def _morse(sc):
    """The timpani taps GALE in standard Morse (MORSE_PROGRAMS[8] = 47 - the
    gale's thunder), on its own clean lane so nothing else muddies the count."""
    material.play_morse(sc, CH_TIMP, MORSE_T0, NUMBER, MORSE_PITCH)


def _hook_fragment(sc, t0, root, k, vel):
    """HOOK8 assembling: the first `k` notes of the gale riff (k < 4, so the
    searcher never registers a full statement) - the riff trying to form in the
    pressure drop."""
    for on, du, semis in material.HOOKS[NUMBER][:k]:
        sc.note(CH_BASS, root + semis, t0 + on, du * 0.9, vel, jt=0, jv=2)


def _bass_churn(sc, t0, t1, vel):
    """The Rough Ride engine: a relentless stepwise eighth-note ostinato through
    D aeolian - the protagonist bass churning, so the leaping riff never
    starves the stepwise ratio."""
    b = t0
    i = 0
    while b < t1 - 1e-6:
        idx = CHURN_CELL[i % len(CHURN_CELL)]
        accent = 6 if (b % 4.0) < 1e-6 else 0
        sc.note(CH_BASS, BASS_SCALE[idx], b, 0.46, vel + accent, jt=0, jv=2)
        b += 0.5
        i += 1


def _bass_chorus(sc, cs, ce, vel):
    """The gale riff track: every eight-beat cell opens with HOOK8 (A-A-A slam
    down the sixth to C) then a stepwise pickup and a churn bar - the riff and
    its Rough Ride tail, monophonic so the searcher finds every statement."""
    cell = cs
    while cell < ce - 1e-6:
        material.play_hook(sc, CH_BASS, cell, BASS_HOOK_ROOT, NUMBER,
                           vel=vel, vel_end=vel + 6, gate=0.9)
        sc.note(CH_BASS, BASS_SCALE[7], cell + 3.5, 0.45, vel - 8, jt=0, jv=2)
        _bass_churn(sc, cell + 4.0, cell + 8.0, vel - 4)
        cell += 8.0


def _double_thumb(sc, lo, hi):
    """The doubled thumb IS the riff octaves: shadow every chorus bass note-on
    at +12 on the driven guitar (coverage >= 0.80 inside, < 0.30 out) - bass and
    guitar slamming the gale in octaves."""
    for beat, pitch, _v in _note_ons(sc, CH_BASS):
        if lo <= beat < hi:
            sc.note(CH_GTR, pitch + 12, beat, 0.4, 88, jt=0, jv=2)


def _brass_stabs(sc, cs, ce):
    """The Stranglehold horns: section stabs answering the riff on the second
    half of each cell, vel 90+, each stab rasping with a channel-aftertouch
    swell (the rasp is pressure, not pitch bend)."""
    cell = cs
    while cell < ce - 1e-6:
        for st, du in [(4.0, 0.8), (5.5, 0.7), (6.5, 1.2)]:
            chord = BRASS_STABS[_chord_idx(cell + st)]
            for p in chord:
                sc.note(CH_BRASS, p, cell + st, du * 0.9, 96, jt=0, jv=2)
            en.at_curve(sc, CH_BRASS,
                        [(cell + st, 20), (cell + st + du * 0.5, 94),
                         (cell + st + du, 10)], step=0.25)
        cell += 8.0


def _overlaps(sc):
    """THE THESIS: both shores stated INTO the storm and overlapping twice, both
    in D (island left on the organ lead, mainland right on the guitar), downbeat
    consonant across each overlap - the storm cannot part them.  Each statement
    is monophonic on its own lead lane."""
    for ov in OVERLAP_T0:
        material.play_island(sc, CH_ISLE, ov, ISLAND_BASE, vel=86, vel_end=80)
        en.expr_curve(sc, CH_ISLE, [(ov, 60), (ov + 4, 100), (ov + 8, 62)],
                      step=0.5)
        material.play_mainland(sc, CH_MAIN, ov, MAINLAND_BASE, vel=88,
                               vel_end=82)
        en.expr_curve(sc, CH_MAIN, [(ov, 60), (ov + 4, 100), (ov + 8, 62)],
                      step=0.5)


def _kit(sc, t0, t1, drive):
    """The storm kit: a heavy backbeat that firms with `drive` (0..1) - kick on
    1 with funk pushes, snare on 2 and 4, driving hats, a crash at phrase
    heads."""
    bar = t0
    while bar < t1 - 1e-6:
        kv = int(84 + 30 * drive)
        sc.hit(36, bar, kv, jt=0)
        if drive > 0.4:
            sc.hit(36, bar + 1.5, kv - 12, jt=0)
            sc.hit(36, bar + 2.5, kv - 18, jt=0)
        sc.hit(38, bar + 1.0, int(78 + 26 * drive), jt=0)
        sc.hit(38, bar + 3.0, int(82 + 26 * drive), jt=0)
        for q in range(8):
            b = bar + q * 0.5
            if b >= t1 - 1e-6:
                break
            drum = 46 if q == 0 else 42
            sc.hit(drum, b, int(38 + 18 * drive), jt=2)
        if int((bar - t0) // 4) % 4 == 0:
            sc.hit(49, bar, int(68 + 22 * drive), jt=0)
        bar += 4.0


def _storm_pulse(sc, t0, t1):
    """The pressure drop's percussion: a slow ominous low-tom pulse under the
    drones, far too sparse to be a groove - the gale not yet arrived."""
    bar = t0
    while bar < t1 - 1e-6:
        sc.hit(41, bar, 52, jt=0)
        if int((bar - t0) // 4) % 2 == 1:
            sc.hit(45, bar + 2.0, 44, jt=0)
        bar += 4.0

def _collapse_descent(sc, t0, t1):
    """Blown out: a long stepwise descent from C3 to the depths of D1 - the
    protagonist bass sinking as the storm gives out (touching D2 and D1 here,
    all before the final window, so the tonic-refusal still holds)."""
    idxs = list(range(13, -1, -1))              # C3 down to D1 (14 notes)
    n = len(idxs)
    for i, idx in enumerate(idxs):
        b = t0 + i * (t1 - t0) / n
        sc.note(CH_BASS, BASS_SCALE[idx], b, (t1 - t0) / n * 0.9,
                max(48, 70 - i), jt=0, jv=2)


def _final_cadence(sc):
    """NO BENEDICTION: the last fall is D-free (C3 - Bb2 - A2) and the bass
    lands G2 - the iv - as its LAST note, refusing the tonic.  A hollow iv
    voicing (G-Bb, no D) rings on the organ beneath it."""
    for b, p in [(544.0, en.n("C3")), (548.0, en.n("Bb2")), (552.0, en.n("A2"))]:
        sc.note(CH_BASS, p, b, 3.5, 82, jt=0, jv=2)
    sc.note(CH_BASS, FINAL_G, 556.0, 6.0, 90, jt=0, jv=2)   # the iv, held, last
    for p in (en.n("G2"), en.n("Bb2"), en.n("G3")):
        sc.note(CH_ORGAN, p, 544.0, 16.0, 58, jt=0, jv=2)


# I. Glass Falling [0, 128) — the pressure drop: drones, sealed choir, GALE in
# Morse, HOOK8 assembling in fragments.
def _b_glass_falling(sc):
    _drone(sc, 0.0, I_END, 76)
    _choir_bed(sc, 0.0, I_END,
               [(0.0, 30), (64.0, 50), (124.0, 40)],
               [(0.0, 8), (64.0, 30), (124.0, 42)],
               [(0.0, 0), (124.0, 20)])
    _organ_bed(sc, 0.0, I_END, 70, [(0.0, 10), (64.0, 30), (124.0, 58)])
    _morse(sc)
    _storm_pulse(sc, 0.0, I_END)
    _hook_fragment(sc, 40.0, BASS_HOOK_ROOT, 2, 70)
    _hook_fragment(sc, 72.0, BASS_HOOK_ROOT, 3, 76)
    _hook_fragment(sc, 104.0, BASS_HOOK_ROOT, 3, 82)


# II. The Gale [128, 400) — the riff track, the horns, the fast Leslie, and the
# thesis: both shores stated into the storm and overlapping twice.
def _b_the_gale(sc):
    _drone(sc, II_T0, II_END, 84)
    _organ_bed(sc, II_T0, II_END, 90,
               [(II_T0, 70), (140.0, 122), (II_END - 2, 122)])
    _choir_bed(sc, II_T0, II_END,
               [(II_T0, 40), (280.0, 64), (II_END - 4, 44)],
               [(II_T0, 22), (280.0, 44), (II_END - 4, 40)],
               [(II_T0, 16), (II_END - 4, 34)])
    # intro build
    _bass_churn(sc, 128.0, 160.0, 88)
    _kit(sc, 128.0, 160.0, 0.5)
    # chorus 1
    _bass_chorus(sc, 160.0, 256.0, 100)
    _kit(sc, 160.0, 256.0, 0.9)
    _brass_stabs(sc, 160.0, 256.0)
    # breakdown between choruses
    _bass_churn(sc, 256.0, 288.0, 84)
    _kit(sc, 256.0, 288.0, 0.5)
    # chorus 2, harder
    _bass_chorus(sc, 288.0, 384.0, 104)
    _kit(sc, 288.0, 384.0, 1.0)
    _brass_stabs(sc, 288.0, 384.0)
    # the wind-up into the eye
    _bass_churn(sc, 384.0, 400.0, 96)
    _kit(sc, 384.0, 400.0, 0.8)
    # the thesis: the two shores stated INTO the storm, overlapping twice
    _overlaps(sc)
    # the doubled thumb IS the riff octaves - only inside the choruses
    for lo, hi in CHORUS_SPANS:
        _double_thumb(sc, lo, hi)


# III. Eye [400, 448) — near-silence: one forward fusion, then the road home,
# snatched away.  (The whitelisted drop, held breath, and hang are intended.)
def _b_eye(sc):
    material.play_fusion(sc, CH_PIANO, FUSION_T0, FUSION_BASE,
                         vel=82, vel_end=74, gate=0.95)
    en.expr_curve(sc, CH_PIANO,
                  [(FUSION_T0, 40), (FUSION_T0 + 4, 90), (FUSION_T0 + 8, 34)],
                  step=0.5)
    material.play_fusion(sc, CH_PIANO, REACH_T0, REACH_BASE, retro=True,
                         count=material.RETRO_REACH[NUMBER],
                         vel=80, vel_end=64, gate=1.0)
    en.expr_curve(sc, CH_PIANO,
                  [(REACH_T0, 44), (REACH_T0 + 3, 82), (REACH_T0 + 6, 28)],
                  step=0.5)


# IV. Blown Out [448, 584) — the crash re-entry, the halved hollow riff, the
# collapse, the unresolved iv, and eight tolls of the refused D.
def _b_blown_out(sc):
    sc.hit(57, CRASH_T0, 108, jt=0)                 # the back wall (crash + splash)
    sc.hit(55, CRASH_T0, 100, jt=0)
    _organ_bed(sc, IV_T0, 544.0, 74, [(IV_T0, 100), (540.0, 28)], gate=0.99)
    for t in (448.0, 464.0, 480.0):                 # the riff halved, hollow
        material.play_hook(sc, CH_BASS, t, BASS_HOOK_ROOT, NUMBER,
                           stretch=2.0, vel=84, vel_end=72, gate=0.9)
    _collapse_descent(sc, 490.0, 540.0)
    _kit(sc, IV_T0, 512.0, 0.5)                      # a kit that gives out
    _final_cadence(sc)
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=2.5, vel=82, dur=3.5)


BUILDERS = [_b_glass_falling, _b_the_gale, _b_eye, _b_blown_out]

# ---------------------------------------------------------------------------
# Oracles — every device the HLD marks verified, single-sourced from material.
# ---------------------------------------------------------------------------

def _o_convergence(sc):
    """Distance 0: both shores imply D (pc 2), the pair never apart again."""
    fails = []
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")
    if len(isl) != 2:
        fails.append(f"{len(isl)} island statements, want 2 (the two overlaps)")
    if len(mnl) != 2:
        fails.append(f"{len(mnl)} mainland statements, want 2 (the two overlaps)")
    for ch, start, _e, first in isl:
        pc = material.island_tonic_pc(first)
        if pc != ISLAND_TONIC_PC:
            fails.append(f"island at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {ISLAND_TONIC_PC} (D)")
    for ch, start, _e, first in mnl:
        pc = material.mainland_tonic_pc(first)
        if pc != MAINLAND_TONIC_PC:
            fails.append(f"mainland at {start:.1f} (ch{ch}) implies pc {pc}, "
                         f"want {MAINLAND_TONIC_PC} (D)")
    if isl and mnl:
        d = material.pc_distance(ISLAND_TONIC_PC, MAINLAND_TONIC_PC)
        if d != 0:
            fails.append(f"shore distance {d}, want 0 (Act Two: together in D)")
    return fails


def _o_storm_overlap(sc):
    """THE THESIS: >= 2 island+mainland overlaps INSIDE the storm movement, each
    downbeat-consonant - the storm cannot part them."""
    isl = [s for s in material.theme_statements(sc, "island")
           if II_T0 <= s[1] < II_END]
    mnl = [s for s in material.theme_statements(sc, "mainland")
           if II_T0 <= s[1] < II_END]
    pairs = material.overlapping_pairs(isl, mnl)
    fails = []
    if len(pairs) < 2:
        return [f"the storm has {len(pairs)} island+mainland overlap(s) in II, "
                f"want >= 2 (the storm cannot part them)"]
    for a, b in pairs:
        ach, a0, a1, _ap = a
        bch, b0, b1, _bp = b
        lo, hi = max(a0, b0), min(a1, b1)
        db = math.ceil(lo / 4.0 - 1e-9) * 4.0
        checked = 0
        while db < hi - 1e-9:
            ip = _pitch_at(sc, ach, db)
            mp = _pitch_at(sc, bch, db)
            if ip and mp:
                checked += 1
                if all((p - q) % 12 not in _CONSONANT
                       for p in ip for q in mp):
                    fails.append(f"overlap downbeat {db:.1f}: island {ip} vs "
                                 f"mainland {mp} is dissonant")
            db += 4.0
        if checked == 0:
            fails.append(f"overlap [{lo:.1f},{hi:.1f}] shares no downbeat to test")
    return fails


def _o_fusion(sc):
    """The shared language holds in the eye: >= 1 forward FUSION, tonic D."""
    fails = []
    fus = material.theme_statements(sc, "fusion")
    if len(fus) < 1:
        fails.append("no forward FUSION statement (Act Two requires >= 1)")
    for ch, start, _e, first in fus:
        if first % 12 != MAINLAND_TONIC_PC:
            fails.append(f"fusion at {start:.1f} implies pc {first % 12}, "
                         f"want {MAINLAND_TONIC_PC} (D)")
    return fails


def _o_hook_density(sc):
    """The gale-riff earworm: HOOK8 stated >= 6 times UNNESTED."""
    hits = material.hook_statements_unnested(sc, NUMBER)
    if len(hits) < 6:
        return [f"HOOK8 (unnested) found {len(hits)} times, want >= 6"]
    return []


def _o_protagonist_bass(sc):
    """The McCartney bass churns: stepwise-dominant (floor 0.42, the Rough Ride
    pump), wide-ranging, slamming HOOK8 in the bass inside the choruses."""
    fails = []
    ons = _note_ons(sc, CH_BASS)
    pitches = [p for _b, p, _v in ons]
    if len(pitches) < 2:
        return ["protagonist bass is silent"]
    steps = sum(1 for a, b in zip(pitches, pitches[1:]) if 1 <= abs(b - a) <= 2)
    ratio = steps / (len(pitches) - 1)
    if ratio < 0.42:
        fails.append(f"bass stepwise ratio {ratio:.2f} < 0.42")
    span = max(pitches) - min(pitches)
    if span < 19:
        fails.append(f"bass range {span} semitones < 19")
    bass_hooks = material.find_statements(material.note_ons(sc, CH_BASS),
                                          material.HOOKS[NUMBER])
    in_chorus = [h for h in bass_hooks if _in_chorus(h[0])]
    if len(in_chorus) < 2:
        fails.append(f"HOOK8 in the bass inside choruses {len(in_chorus)}, "
                     f"want >= 2")
    return fails


def _o_doubled_thumb(sc):
    """The riff octaves: every chorus bass note-on shadowed at +12 on the driven
    guitar (coverage >= 0.80 inside, < 0.30 out) - and hollow (undoubled)
    everywhere else, so the collapse rings bare."""
    fails = []
    thumb = [(_tick(b), p) for b, p, _v in _note_ons(sc, CH_GTR)]

    def shadowed(bt, bp):
        return any(pp == bp + 12 and abs(pt - bt) <= 10 for pt, pp in thumb)

    inside, outside = [], []
    for b, p, _v in _note_ons(sc, CH_BASS):
        (inside if _in_chorus(b) else outside).append((_tick(b), p))
    cov_in = (sum(1 for bt, bp in inside if shadowed(bt, bp)) / len(inside)
              if inside else 0.0)
    cov_out = (sum(1 for bt, bp in outside if shadowed(bt, bp)) / len(outside)
               if outside else 0.0)
    if cov_in < 0.80:
        fails.append(f"doubled-thumb coverage {cov_in:.2f} inside choruses < 0.80")
    if cov_out >= 0.30:
        fails.append(f"bass doubled {cov_out:.2f} OUTSIDE choruses >= 0.30")
    return fails


def _o_reach(sc):
    """The road home reaches exactly six notes and stops: the pinned prefix
    registers, and NO longer prefix and no full retrograde exist."""
    fails = []
    target = material.RETRO_REACH[NUMBER]                # 6
    cell = material.retro_prefix_cell(target)
    hits = sum(len(material.find_statements(material.note_ons(sc, ch), cell))
               for ch in sc.events)
    if hits < 1:
        fails.append(f"the {target}-note road home (REACH) is not stated")
    for c in range(target + 1, len(material.FUSION_RETRO) + 1):
        longer = material.retro_prefix_cell(c)
        n = sum(len(material.find_statements(material.note_ons(sc, ch), longer))
                for ch in sc.events)
        if n:
            fails.append(f"a length-{c} retro prefix registered {n}x - the "
                         f"road home must stop at {target}")
    if material.theme_statements(sc, "fusion_retro"):
        fails.append("the full retrograde must not sound before T10")
    return fails


def _o_withheld(sc):
    """The withheld payoffs: island_major and fusion_retro are banned on 6-9."""
    fails = []
    if material.theme_statements(sc, "island_major"):
        fails.append("island_major is banned before T10")
    if material.theme_statements(sc, "fusion_retro"):
        fails.append("fusion_retro (the full road home) is banned before T10")
    return fails


def _o_morse(sc):
    """The tide-word GALE, tapped on timpani (MORSE_PROGRAMS[8] = 47 - the
    gale's thunder), in standard Morse timing re-derived from material."""
    fails = []
    if material.MORSE_PROGRAMS[NUMBER] != 47:
        fails.append("morse timbre for T8 must be timpani (program 47)")
    pairs = material.morse_rhythm(material.MORSE_WORDS[NUMBER])
    taps = _note_spans(sc, CH_TIMP)
    if len(taps) != len(pairs):
        fails.append(f"morse lane has {len(taps)} taps, want {len(pairs)} (GALE)")
        return fails
    for k, ((on, off, p), (won, wdu)) in enumerate(zip(taps, pairs)):
        if p != MORSE_PITCH:
            fails.append(f"morse tap {k} pitch {p}, want {MORSE_PITCH}")
            break
        if abs(on - (MORSE_T0 + won)) > 1e-6:
            fails.append(f"morse tap {k} onset {on:.3f}, want {MORSE_T0 + won:.3f}")
            break
        if abs((off - on) - wdu * 0.9) > 0.02:
            fails.append(f"morse tap {k} dur {off - on:.3f}, want {wdu * 0.9:.3f}")
            break
    return fails


def _o_vowel_cap(sc):
    """The gale seals the mouths again: choir CC70 never exceeds 45."""
    cap = material.VOWEL_CAPS[NUMBER]
    bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
    return [f"choir vowel CC70={v} at beat {b:.1f} exceeds the cap {cap}"
            for b, v in bad[:4]]


def _o_storm_tempo(sc):
    """The authored storm map: NO tide-breath anywhere - the whole tempo is the
    pinned lurching shape, surging and collapsing, with many reversals (a
    tide-breath swell would have few) and a strictly-descending final collapse."""
    fails = []
    if list(sc.tempos) != STORM_TEMPO:
        fails.append("tempo map is not the authored STORM_TEMPO")
    bpms = [b for _t, b in STORM_TEMPO]
    dirs = [1 if bpms[i + 1] > bpms[i] else (-1 if bpms[i + 1] < bpms[i] else 0)
            for i in range(len(bpms) - 1)]
    nz = [d for d in dirs if d != 0]
    reversals = sum(1 for i in range(1, len(nz)) if nz[i] != nz[i - 1])
    if reversals < 6:
        fails.append(f"storm tempo has {reversals} reversals, want >= 6 "
                     f"(lurching, not a tide-breath swell)")
    if all(d >= 0 for d in dirs) or all(d <= 0 for d in dirs):
        fails.append("storm tempo is monotone (it must surge AND collapse)")
    tail = bpms[-6:]
    if any(tail[i] <= tail[i + 1] for i in range(len(tail) - 1)):
        fails.append("storm tempo does not collapse (final run not strictly "
                     "descending)")
    if max(bpms) - bpms[-1] < 25:
        fails.append(f"storm collapse only {max(bpms) - bpms[-1]} bpm, want >= 25")
    return fails


def _o_aftertouch(sc):
    """The Stranglehold rasp: channel-aftertouch swells on the horn stabs in
    the gale."""
    lane = [(b, v) for b, v in _aftertouch_lane(sc, CH_BRASS)
            if II_T0 <= b < II_END]
    fails = []
    if len(lane) < 8:
        fails.append(f"brass aftertouch has {len(lane)} events, want the rasp")
    if lane and max(v for _b, v in lane) < 60:
        fails.append("brass aftertouch never swells (the rasp is too weak)")
    return fails


def _o_leslie(sc):
    """The rock organ on a FAST Leslie: CC1 high through the gale."""
    lane = [(b, v) for b, v in _cc_lane(sc, CH_ORGAN, 1)
            if II_T0 <= b < II_END]
    if not lane:
        return ["no Leslie CC1 on the rock organ in the gale"]
    top = max(v for _b, v in lane)
    if top < 100:
        return [f"organ Leslie tops out at CC1={top}, want fast (>= 100)"]
    return []


def _o_unresolved_final(sc):
    """NO BENEDICTION: in the pinned final window the bass's LAST note is the iv
    (pc 7, G) and NO melodic channel lands the tonic D (pc 2) - the bell buoy is
    exempt (it tolls the D the music refused)."""
    fails = []
    fw0, fw1 = FINAL_WINDOW
    bass = [(b, p) for b, p, _v in _note_ons(sc, CH_BASS) if fw0 <= b <= fw1]
    if not bass:
        fails.append("no bass note in the final window")
    elif bass[-1][1] % 12 != 7:
        fails.append(f"final bass pc {bass[-1][1] % 12}, want 7 (the iv, G) - "
                     f"the tonic must be refused")
    for ch in sorted(sc.events):
        if ch in (CH_BELLS, CH_DRUMS):
            continue
        for b, p, _v in _note_ons(sc, ch):
            if fw0 <= b <= fw1 and p % 12 == ISLAND_TONIC_PC:
                fails.append(f"ch{ch} lands pc {ISLAND_TONIC_PC} (D) at {b:.1f} "
                             f"in the final window - the tonic must be refused")
                break
    return fails


def _o_shore_pans(sc):
    """The widest strait of the act: island voices hard left (42), mainland
    voices hard right (86)."""
    fails = []
    if (ISL_PAN, MAIN_PAN) != material.SHORE_PANS[NUMBER]:
        fails.append(f"shore seats {(ISL_PAN, MAIN_PAN)} != "
                     f"{material.SHORE_PANS[NUMBER]}")
    island = {CH_ORGAN, CH_ISLE, CH_CHOIR}
    mainland = {CH_MAIN, CH_BRASS}
    for ch in sorted(island):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {ISL_PAN}:
            fails.append(f"island ch{ch} pans {sorted(pans)}, want {{{ISL_PAN}}}")
    for ch in sorted(mainland):
        pans = {v for _b, v in _cc_lane(sc, ch, 10)}
        if pans != {MAIN_PAN}:
            fails.append(f"mainland ch{ch} pans {sorted(pans)}, want {{{MAIN_PAN}}}")
    return fails


def _o_tolls(sc):
    """The bell buoy tolls the refused D eight times, the final note-ons of the
    track; nothing else sounds after the first strike."""
    fails = []
    bells = _note_ons(sc, CH_BELLS)
    if len(bells) != material.TOLLS[NUMBER]:
        fails.append(f"{len(bells)} tolls, want {material.TOLLS[NUMBER]}")
    for b, p, _v in bells:
        if p % 12 != ISLAND_TONIC_PC:
            fails.append(f"toll at {b:.1f} pc {p % 12}, want {ISLAND_TONIC_PC} (D)")
            break
    all_ons = sorted((b, ch) for ch in sc.events
                     for b, _p, _v in _note_ons(sc, ch))
    if bells:
        toll_on = bells[0][0]
        after = [(b, ch) for b, ch in all_ons
                 if b > toll_on + 1e-6 and ch != CH_BELLS]
        if after:
            fails.append(f"{len(after)} note-on(s) after toll 1 (e.g. ch"
                         f"{after[0][1]} at {after[0][0]:.1f})")
        if all_ons and all_ons[-1][1] != CH_BELLS:
            fails.append("the final note-on is not a toll")
    return fails


def _o_unheralded(sc):
    """The storm arrives unannounced (HLD addendum s1.10 / s2 T8): the exemption
    made machine-checkable - no breath-flute herald voice on the track."""
    if PROGRAM_WHITELIST & {75, 77}:
        return ["T8 must be unheralded - no pan flute / shakuhachi herald voice"]
    return []


def oracles(sc, info, spans):
    return [
        ("convergence", _o_convergence(sc)),
        ("storm_overlap", _o_storm_overlap(sc)),
        ("fusion", _o_fusion(sc)),
        ("hook_density", _o_hook_density(sc)),
        ("protagonist_bass", _o_protagonist_bass(sc)),
        ("doubled_thumb", _o_doubled_thumb(sc)),
        ("the_reach", _o_reach(sc)),
        ("withheld_payoffs", _o_withheld(sc)),
        ("morse_gale", _o_morse(sc)),
        ("vowel_cap", _o_vowel_cap(sc)),
        ("storm_tempo", _o_storm_tempo(sc)),
        ("brass_aftertouch", _o_aftertouch(sc)),
        ("organ_leslie", _o_leslie(sc)),
        ("unresolved_final", _o_unresolved_final(sc)),
        ("shore_pans", _o_shore_pans(sc)),
        ("tolls", _o_tolls(sc)),
        ("unheralded", _o_unheralded(sc)),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (analyze.py) — RATIO-based per the repo lesson; thresholds are
# generous and PROVISIONAL, to be calibrated against the real render later.
# The gale is the track's loudest water; the eye falls far below it; the
# collapse is hollow (below the gale).
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    checks = []

    def _rms_db(b0, b1):
        i0, i1 = ctx.bar_window(b0, b1)
        return ctx.db(ctx.rms(ctx.l, ctx.r, i0, i1))

    glass = _rms_db(48.0, 96.0)         # I, the pressure drop
    gale = _rms_db(300.0, 360.0)        # II, chorus 2 - the hardest
    eye = _rms_db(406.0, 446.0)         # III, the near-silent eye
    collapse = _rms_db(456.0, 500.0)    # IV, the halved hollow riff

    # 1. The gale is the loudest water on the track (not below the pressure drop).
    fails = []
    if gale - glass < -1.0:
        fails.append(f"the gale {gale:.1f} dB is quieter than the pressure drop "
                     f"{glass:.1f} dB (the gale should be the loudest)")
    checks.append(("audio_gale_loudest", fails))

    # 2. The eye drops far below the gale (devastating by contrast).
    fails = []
    if gale - eye < 3.0:
        fails.append(f"the eye {eye:.1f} dB is not far enough below the gale "
                     f"{gale:.1f} dB (want >= 3 dB drop)")
    checks.append(("audio_eye_drops", fails))

    # 3. The collapse is hollow: below the gale it fell from.
    fails = []
    if gale - collapse < 0.5:
        fails.append(f"the collapse {collapse:.1f} dB is not below the gale "
                     f"{gale:.1f} dB (the riff halved should be hollow)")
    checks.append(("audio_collapse_hollow", fails))
    return checks
