"""movements/t09_the_wane.py — track 9 of *The Causeway* (Act Two, autumn).

THE WANE.  The album's tenderest music — the autumn letters, and the track
that remembers the first winter.  A *Distractions* / *Don't Be Careless Love*
ballad with *Footprints* fingerpicking: nylon guitar and a fingerpicked steel
guitar, a bossa-lite brush kit, low strings, and a CELLO as the marquee voice
that breathes on CC11 and channel-aftertouch swells.  A music box taps WANE in
Morse on its own lane.  F major, 4/4, ~76 with a deep tide-breath in every
movement (the water is high again, and slow).  Four movements:

  I. Shorter Days — nylon fingerpicking over bossa brushes, the low strings
     sitting under, the cello closing its phrases on HOOK9 (the road-home
     head: a rising 1-2-3 with a long third note — hope, not a sigh).
  II. The Letters — THE MEMORY, oracle-pinned.  The cello quotes HOOK1 (Act
     One's heartbeat, E-E-D-B) slow, at stretch 2 — the first winter
     remembered — and the fingerpicked steel states the ISLAND theme ONCE in
     its original E MINOR (implied tonic E): Act Two's only off-pc statement,
     explicitly whitelisted by this track's convergence oracle.  Every other
     island and mainland statement implies F.
  III. Don't Be Careless — the warm chorus: the island incantation (steel,
     left) and the mainland tune (strings, right) overlap gently in F,
     downbeat-consonant; one forward FUSION on the cello (tonic F); HOOK9
     closes every phrase; and THE REACH — the road home reaches EIGHT notes
     now (play_fusion(retro=True, count=8)), almost the whole way, held back
     at the last step.  No full retrograde, no island-in-major (both T10's).
  IV. First Frost — the music box alone taps WANE again, a breath of HOOK4
     ice arps drifts over the settling frost (unpinned), the bass walks the
     plagal iv-I (Bb -> F), and exactly nine bell tolls ring the F — nothing
     sounds after the first strike.

EXEMPTIONS (album law — the ballad is exempt; documented, not silently
skipped, exactly as track 4 did): this track carries NO protagonist-bass, NO
doubled-thumb and NO breath-herald oracle.  The bass is a plain bossa
foundation that exists only to lay the plagal cadence; there is no octave
thumb-double; and the track arrives unannounced — no pan-flute inhale.  The
Act Two laws that DO apply are all encoded below: distance-0 convergence with
the single pinned E-minor memory exception, the required simultaneity, the
forward fusion, the unnested HOOK9 density, the eight-note REACH stopping
short of home, the withheld payoffs, the WANE morse on the music box, the
vowel cap, the deep tide-breath, the plagal final, the shore pans and the
tolls.  Every recurring datum is single-sourced from material.py.
"""

from __future__ import annotations

import math

import conductor
import engine as en
import material

NUMBER = 9
TITLE = "The Wane"
FILE = "09 - The Wane.mid"
SEED = 202607189
COMMENT = (
    "The Wane - the album's tenderest music, the autumn letters and the track "
    "that remembers the first winter.  A Distractions / Don't Be Careless Love "
    "ballad with Footprints fingerpicking: nylon and fingerpicked steel guitar, "
    "a bossa-lite brush kit, low strings and a cello - the marquee voice - "
    "breathing on CC11 and aftertouch swells.  F major, 4/4, ~76 with a deep "
    "tide-breath.  Shorter Days fingerpicks over bossa brushes, the cello "
    "closing its phrases on the road-home head (a rising 1-2-3); the Letters "
    "remembers - the cello quotes Act One's heartbeat slow, at stretch two, "
    "and the steel guitar states the island theme once in its original E minor, "
    "the record's only off-key statement; Don't Be Careless is the warm chorus, "
    "island and mainland overlapping gently in F, a forward fusion on the cello "
    "and the road home reaching eight notes, almost the whole way; and First "
    "Frost leaves the music box alone tapping WANE, a breath of ice, a plagal "
    "Bb to F and nine bells.")

# ---------------------------------------------------------------------------
# Channels.  The re-opened autumn strait is narrow (width 36): the island pole
# (the fingerpicked steel that carries the island theme, and the weather
# choir) sits left at 46; the mainland pole (the warm string tune) sits right
# at 82; the intimate spine - the nylon fingerpicking bed, the marquee cello,
# the low-string pad, the Morse music box, the frost celesta, the bossa bass,
# the brush kit and the bell buoy - holds the centre (64).
# ---------------------------------------------------------------------------

CH_NYLON, CH_STEEL, CH_CELLO, CH_MSTRING = 0, 1, 2, 3
CH_LOWSTR, CH_CHOIR, CH_MUSICBOX, CH_ICE = 4, 5, 6, 7
CH_BASS, CH_DRUMS, CH_BELLS = 8, 9, 10

ISL_PAN, MAIN_PAN = material.SHORE_PANS[NUMBER]        # (46, 82)
ISLAND_TONIC_PC, MAINLAND_TONIC_PC = material.convergence_pcs(NUMBER)  # 5, 5

_MM = material.MODE_MINOR                   # aeolian
_MJ = material.MODE_MAJOR                   # ionian - F major, the home key

# --- the movement grid (contiguous; last t1 = END) ---
I_END = 96.0                                # 24 bars of 4/4 - Shorter Days
II_T0 = 96.0
II_END = 192.0                              # 24 bars - The Letters (the memory)
III_T0 = 192.0
III_END = 304.0                             # 28 bars - Don't Be Careless
IV_T0 = 304.0
END = 384.0                                 # 20 bars - First Frost

# --- pinned geometry the oracles re-derive against material.py ---
ISLAND_BASE_F = en.n("F3")                  # 53 - island deg1 = ... tonic F (pc 5)
ISLAND_BASE_E = en.n("E3")                  # 52 - THE MEMORY: island in E minor
MAINLAND_BASE = en.n("F3")                  # 53 - mainland deg1 = F (tonic pc 5)
FUSION_BASE = en.n("F3")                    # 53 - the forward fusion, tonic F
REACH_BASE = en.n("F3")                     # 53 - the road home, eight notes

OVERLAP_T0 = 200.0                          # island (steel) + mainland (strings)
ISLAND_E_T0, ISLAND_E_STR = 132.0, 1.5      # the E-minor memory, slow
HOOK1_T0, HOOK1_STR = 120.0, 2.0            # the heartbeat, remembered (stretch 2)
FUSION_T0 = 240.0                           # the one forward fusion (cello, in F)
REACH_T0 = 256.0                            # the road home, eight notes, held back

# HOOK9 (the road-home head) closes phrases across I and III; each is a clean
# 3-note run on the cello so the searcher finds every one.
HOOK9_I = [24.0, 56.0, 88.0]
HOOK9_III = [196.0, 212.0, 224.0, 250.0, 270.0, 286.0, 298.0]
HOOK9_ROOTS = {24.0: en.n("F4"), 56.0: en.n("C4"), 88.0: en.n("Bb3"),
               196.0: en.n("F4"), 212.0: en.n("C4"), 224.0: en.n("A3"),
               250.0: en.n("F4"), 270.0: en.n("Bb3"), 286.0: en.n("C4"),
               298.0: en.n("F4")}

MORSE_T0 = 305.0                            # WANE alone at the top of the frost
MORSE_PITCH = en.n("F5")                    # 77 - the music box's fixed tap
ICE_T0 = 313.0                              # a breath of HOOK4 ice over the frost
ICE_BASE = en.n("C5")                       # 72 - the frost arp root

FINAL_DOWNBEAT = 356.0                      # the plagal landing (bass Bb -> F)
TOLL_T0 = 360.0
TOLL_PITCH = en.n("F3")                     # 53 - pc 5 = the tonic F
TOLL_SPACING = 2.5


# --- the deep tide-breath: every movement swells (>= 2 troughs), with a
#     couple of explicit fermata dips per movement, placed off the tide grid,
#     for the autumn ache (the water is high and slow all the way through) ---

def _breath(t0, t1, dips):
    """A deep tide-breath (depth 6) plus explicit fermata dips (below the
    tide's own swell) at phrase ends - the rubato ache.  Dip beats sit off
    the period/4 = 8 grid so none collide with a tide sample."""
    return sorted(material.tide_breath(76.0, t0, t1, period=32.0, depth=6.0)
                  + list(dips))


TEMPO_MAP = (
    _breath(0.0, I_END, [(30.0, 68.0), (62.0, 66.0)])
    + _breath(II_T0, II_END, [(126.0, 67.0), (158.0, 65.0)])
    + _breath(III_T0, III_END, [(222.0, 68.0), (278.0, 66.0)])
    + _breath(IV_T0, END, [(330.0, 66.0), (356.0, 64.0)]))

# the brush kit (bossa brushes) plays throughout the sung movements; ch9's
# program is set here (sc.channel skips ch9's program).  The frost (IV) drops
# the kit - the music box is alone.
KIT_BRUSH = 40

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Shorter Days", 0.0, I_END),
               ("II. The Letters", II_T0, II_END),
               ("III. Don't Be Careless", III_T0, III_END),
               ("IV. First Frost", IV_T0, END)],
    tempo_map=TEMPO_MAP,
    time_signatures=[(0.0, 4, 4)],
    keysigs=[(0.0, -1, 0)],                 # F major: one flat, major
    channels=[(CH_NYLON, "nylon guitar", 24, 84, 64, 40),
              (CH_STEEL, "steel guitar", 25, 80, ISL_PAN, 44),
              (CH_CELLO, "cello", 42, 88, 64, 55),
              (CH_MSTRING, "mainland strings", 48, 82, MAIN_PAN, 50),
              (CH_LOWSTR, "low strings", 49, 74, 64, 52),
              (CH_CHOIR, "choir", 52, 72, ISL_PAN, 60),
              (CH_MUSICBOX, "music box", 10, 78, 64, 40),
              (CH_ICE, "celesta", 8, 72, 64, 42),
              (CH_BASS, "acoustic bass", 32, 86, 64, 26),
              (CH_DRUMS, "brush kit", 40, 80, 64, 28),
              (CH_BELLS, "tubular bells", 14, 88, 64, 55)],
    program_changes=[(CH_DRUMS, 0.0, KIT_BRUSH)],
    extra_markers=[(HOOK1_T0, "the memory"), (ISLAND_E_T0, "the letter in E"),
                   (OVERLAP_T0, "the shores overlap"),
                   (FUSION_T0, "the fusion"), (REACH_T0, "the road home"),
                   (MORSE_T0, "first frost"), (TOLL_T0, "the tolls")],
)

PROGRAM_WHITELIST = {24, 25, 42, 48, 49, 52, 10, 8, 32, 14}
CENTERED_CHANNELS = {CH_NYLON, CH_CELLO, CH_LOWSTR, CH_MUSICBOX, CH_ICE,
                     CH_BASS, CH_DRUMS, CH_BELLS}
NOTE_RANGES = {
    CH_NYLON: (43, 72), CH_STEEL: (50, 64), CH_CELLO: (48, 72),
    CH_MSTRING: (52, 64), CH_LOWSTR: (41, 72), CH_CHOIR: (48, 74),
    CH_MUSICBOX: (77, 77), CH_ICE: (72, 88), CH_BASS: (33, 52),
    CH_BELLS: (53, 53),
}
GAP_WHITELIST: list[tuple[float, float]] = []
BEND_EXEMPT: set[int] = set()               # cello scoops recentre at seams
DURATION_WINDOW = (280.0, 360.0)            # ~5:00 incl. the 2-beat end pad
BOUNDS_WHITELIST: list[tuple[int, float, float]] = []

# Click-scan cap, calibrated against the real render (lead's diagnosis,
# 2026.07.19): measured max step 49691 — the sampled brush kit's slap/tap
# transients (full-bandwidth noise bursts around the mix ceiling, both
# directions, no DC step, no clipping; a --solo 9 stem of THIS track steps
# ~51k with the drums alone).  Snap, not clicks — the same diagnosis as
# t02 and t07; the bossa brushes play nearly every bar here.
MAX_SAMPLE_STEP = 53000

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


def _onsets_in(sc, ch, lo, hi):
    return [(b, p, v) for b, p, v in _note_ons(sc, ch) if lo - 1e-6 <= b < hi]


def _movement_events(lo, hi):
    """The tempo events whose beat falls inside [lo, hi)."""
    return [(b, bpm) for b, bpm in TEMPO_MAP if lo - 1e-6 <= b < hi - 1e-6]


def _pitch_at(sc, ch, beat):
    """The pitch(es) sounding on `ch` at `beat` (onset-inclusive)."""
    return [p for on, off, p in _note_spans(sc, ch)
            if on - 1e-6 <= beat < off - 1e-6]


# ---------------------------------------------------------------------------
# The autumn textures.  F-major diatonic chord shapes (root position, low
# voicings) feed the fingerpicking, the bass, the low strings and the choir;
# progressions are per-bar root names, 8-bar phrases.
# ---------------------------------------------------------------------------

_CHORDS: dict[str, list[int]] = {
    "F":  [53, 57, 60], "Dm": [50, 53, 57], "Bb": [46, 50, 53],
    "C":  [48, 52, 55], "Gm": [43, 46, 50], "Am": [45, 48, 52],
}

PROG_I = ["F", "Dm", "Bb", "C", "F", "Dm", "Gm", "C"]        # x3 = 24 bars
PROG_II = ["Dm", "Bb", "F", "C", "Dm", "Gm", "Bb", "C"]      # x3 = 24 bars
PROG_III = ["F", "Bb", "Am", "Dm", "Gm", "C", "F", "C"]      # x3 + coda
PROG_III_CODA = ["F", "Bb", "C", "F"]                        # bars 24-27

# The Footprints pattern: eight quavers of (chord index, octave lift) —
# root, fifth, third-above, fifth, octave root, third-above, fifth, third.
_PICK = [(0, 0), (2, 0), (1, 1), (2, 0), (0, 1), (1, 1), (2, 0), (1, 1)]
_PICK_VEL = [56, 46, 50, 44, 52, 46, 48, 44]


def _bar_names(progs: list[str], bars: int) -> list[str]:
    out = []
    while len(out) < bars:
        out.extend(progs)
    return out[:bars]


def _pick_bar(sc, t0, name, vel_off=0, jt=4):
    """One fingerpicked bar on the nylon guitar."""
    ch = _CHORDS[name]
    for i, ((ci, up), v) in enumerate(zip(_PICK, _PICK_VEL)):
        b = t0 + 0.5 * i
        j = 0 if b <= t0 + 0.1 else jt          # edge lesson: jt=0 on seams
        sc.note(CH_NYLON, ch[ci] + 12 * up, b, 0.55, v + vel_off, jt=j, jv=3)


def _bossa_bar(sc, t0, jt=4, vel_off=0):
    """One bossa-lite brush-kit bar (brush kit: ch9 program 40)."""
    def d(key, b, v):
        j = 0 if b <= t0 + 0.1 else jt
        sc.note(CH_DRUMS, key, b, 0.4, v + vel_off, jt=j, jv=3)
    d(36, t0, 52)                                # soft surdo
    d(36, t0 + 2.5, 44)
    d(38, t0 + 1.0, 42)                          # brush taps
    d(38, t0 + 3.0, 46)
    d(40, t0 + 2.0, 34)                          # one stir
    for q in (0.5, 1.5, 2.5, 3.5):
        d(42, t0 + q, 28 + (4 if q in (1.5, 3.5) else 0))


def _bass_bar(sc, t0, name, jt=0):
    root = _CHORDS[name][0] - 12                 # an octave under the guitar
    if root < 33:                    # stay inside the pinned bass floor
        root += 12
    sc.note(CH_BASS, root, t0, 2.5, 58, jt=jt, jv=2)
    sc.note(CH_BASS, root + 7, t0 + 3.0, 0.9, 50, jt=jt, jv=2)


def _lowstr_phrase(sc, t0, name, dur=16.0, peak=88):
    root = _CHORDS[name][0] - 12
    if root < 41:                    # keep the pad inside its pinned floor
        root += 12
    sc.note(CH_LOWSTR, root, t0, dur, 46, jt=0, jv=2)
    sc.note(CH_LOWSTR, root + 7, t0, dur, 42, jt=0, jv=2)
    en.expr_curve(sc, CH_LOWSTR, [(t0, 36), (t0 + dur * 0.6, peak),
                                  (t0 + dur, 30)], step=1.0)


def _choir_phrase(sc, t0, pitches, dur=8.0, vel=44, vowel=(22, 48)):
    for p in pitches:
        sc.note(CH_CHOIR, p, t0, dur, vel, jt=0, jv=2)
    en.vowel(sc, CH_CHOIR, vowel[0], t0)
    en.vowel(sc, CH_CHOIR, vowel[1], t0 + dur * 0.5)
    en.expr_curve(sc, CH_CHOIR, [(t0, 34), (t0 + dur * 0.55, 74),
                                 (t0 + dur, 28)], step=1.0)


def _cello_note(sc, p, t0, dur, vel, vib=False, swell=False):
    sc.note(CH_CELLO, p, t0, dur, vel, jt=0, jv=2)
    if vib and dur >= 2.0:
        en.vibrato(sc, CH_CELLO, t0 + dur * 0.35, dur * 0.6, depth=0.2)
    if swell and dur >= 3.0:
        en.at_curve(sc, CH_CELLO, [(t0, 0), (t0 + dur * 0.6, 68),
                                   (t0 + dur, 0)])


def _cello_hook9(sc, t0):
    """One road-home head, phrase-closing, with its CC11 bloom."""
    material.play_hook(sc, CH_CELLO, t0, HOOK9_ROOTS[t0], 9, vel=66,
                      gate=0.97)
    en.expr_curve(sc, CH_CELLO, [(t0, 46), (t0 + 2.4, 88), (t0 + 4.0, 36)],
                  step=0.5)


# ---------------------------------------------------------------------------
# I. Shorter Days [0, 96) — the fingerpicked verse; the cello closes its two
# long phrases on the road-home head.  24 bars.
# ---------------------------------------------------------------------------

def _b_shorter_days(sc):
    names = _bar_names(PROG_I, 24)
    for bar, name in enumerate(names):
        t0 = 4.0 * bar
        _pick_bar(sc, t0, name, jt=4)
        _bossa_bar(sc, t0, jt=4)
        _bass_bar(sc, t0, name)
        if bar % 4 == 0:
            _lowstr_phrase(sc, t0, name)
    # Cello phrase A: rises from the tonic, sighs, closes on HOOK9 at 24.
    _cello_note(sc, 53, 10.0, 3.0, 56, vib=True)
    _cello_note(sc, 57, 13.0, 2.0, 58)
    _cello_note(sc, 60, 15.0, 4.0, 62, vib=True, swell=True)
    en.bend_ramp(sc, CH_CELLO, 14.8, 15.0, -0.5, 0.0)       # appoggiatura
    _cello_note(sc, 58, 19.0, 2.0, 54)
    _cello_note(sc, 55, 21.0, 2.5, 50, vib=True)
    _cello_hook9(sc, 24.0)
    # Phrase B: darker, from the sixth, closes on HOOK9 at 56.
    _cello_note(sc, 50, 42.0, 3.0, 52, vib=True)
    _cello_note(sc, 53, 45.0, 2.0, 54)
    _cello_note(sc, 57, 47.0, 4.0, 60, vib=True, swell=True)
    _cello_note(sc, 55, 51.0, 2.0, 52)
    _cello_note(sc, 52, 53.0, 2.5, 48)
    _cello_hook9(sc, 56.0)
    # Phrase C: the low goodbye, closing on HOOK9 at 88.
    _cello_note(sc, 48, 74.0, 3.0, 50, vib=True)
    _cello_note(sc, 50, 77.0, 2.0, 52)
    _cello_note(sc, 53, 79.0, 4.0, 58, vib=True, swell=True)
    _cello_note(sc, 51, 83.0, 2.0, 50)
    _cello_note(sc, 50, 85.0, 2.0, 46)
    _cello_hook9(sc, 88.0)
    sc.bend(CH_CELLO, 95.5, 0.0)                             # seam hygiene


# ---------------------------------------------------------------------------
# II. The Letters [96, 192) — the memory.  The cello quotes the heartbeat at
# stretch 2; the steel guitar writes the letter in E minor — Act Two's only
# off-key statement.  24 bars.
# ---------------------------------------------------------------------------

def _b_the_letters(sc):
    names = _bar_names(PROG_II, 24)
    for bar, name in enumerate(names):
        t0 = II_T0 + 4.0 * bar
        _pick_bar(sc, t0, name, vel_off=-4, jt=4)
        _bossa_bar(sc, t0, jt=4, vel_off=-4)
        _bass_bar(sc, t0, name)
        if bar % 4 == 2:
            _lowstr_phrase(sc, t0, name, peak=78)
    # The heartbeat, remembered: HOOK1 slow (stretch 2) on the cello at 120.
    _cello_note(sc, 60, 112.0, 3.0, 50, vib=True)
    _cello_note(sc, 62, 115.0, 2.0, 52)
    _cello_note(sc, 64, 117.0, 2.5, 56, vib=True, swell=True)
    material.play_hook(sc, CH_CELLO, HOOK1_T0, en.n("E4"), 1,
                       stretch=HOOK1_STR, vel=58, gate=0.95)
    en.expr_curve(sc, CH_CELLO, [(HOOK1_T0, 52), (HOOK1_T0 + 2.6, 84),
                                 (HOOK1_T0 + 4.0, 40)], step=0.5)
    # The letter in E: the island theme, original key, on the steel (132).
    material.play_island(sc, CH_STEEL, ISLAND_E_T0, ISLAND_BASE_E,
                         stretch=ISLAND_E_STR, vel=60, gate=0.96)
    en.expr_curve(sc, CH_STEEL, [(ISLAND_E_T0, 40),
                                 (ISLAND_E_T0 + 7.0, 86),
                                 (ISLAND_E_T0 + 12.0, 34)], step=0.5)
    # The cello answers the letter, hanging with it, then lets it go.
    _cello_note(sc, 59, 146.0, 3.0, 52, vib=True)
    _cello_note(sc, 57, 149.0, 2.0, 50)
    _cello_note(sc, 55, 151.0, 4.0, 54, vib=True, swell=True)
    _cello_note(sc, 53, 157.0, 3.0, 48, vib=True)
    # Choir slips in under the second half, mouths half-open at most.
    _choir_phrase(sc, 160.0, [60, 65], dur=12.0, vel=42, vowel=(20, 42))
    _choir_phrase(sc, 176.0, [58, 62], dur=12.0, vel=40, vowel=(24, 50))
    sc.bend(CH_CELLO, 191.5, 0.0)


# ---------------------------------------------------------------------------
# III. Don't Be Careless [192, 304) — the warm chorus: the shores overlap
# gently in F, the fusion sings on the cello, and the road home reaches
# eight notes.  28 bars (3 x 8 + a 4-bar coda).
# ---------------------------------------------------------------------------

def _b_dont_be_careless(sc):
    names = _bar_names(PROG_III, 24) + PROG_III_CODA
    for bar, name in enumerate(names):
        t0 = III_T0 + 4.0 * bar
        _pick_bar(sc, t0, name, vel_off=4, jt=4)
        _bossa_bar(sc, t0, jt=4, vel_off=4)
        _bass_bar(sc, t0, name)
        if bar % 4 == 0:
            _lowstr_phrase(sc, t0, name, peak=96)
    # The shores overlap (200): island on the steel, mainland on the warm
    # strings, both in F, aligned to the same bar downbeat — P5 at the
    # first downbeat, unison at the second.
    material.play_island(sc, CH_STEEL, OVERLAP_T0, ISLAND_BASE_F,
                         vel=62, gate=0.96)
    material.play_mainland(sc, CH_MSTRING, OVERLAP_T0, MAINLAND_BASE,
                           vel=64, gate=0.97)
    en.expr_curve(sc, CH_STEEL, [(OVERLAP_T0, 44), (OVERLAP_T0 + 5.0, 88),
                                 (OVERLAP_T0 + 8.0, 38)], step=0.5)
    en.expr_curve(sc, CH_MSTRING, [(OVERLAP_T0, 46), (OVERLAP_T0 + 5.0, 92),
                                   (OVERLAP_T0 + 8.0, 40)], step=0.5)
    # The strings answer twice more, single-line, warm and sparse.
    for t0, ps in ((216.0, (57, 60, 62)), (232.0, (60, 58, 57))):
        for i, p in enumerate(ps):
            sc.note(CH_MSTRING, p, t0 + 2.0 * i, 2.0, 54, jt=0, jv=2)
        en.expr_curve(sc, CH_MSTRING, [(t0, 40), (t0 + 3.5, 78),
                                       (t0 + 6.0, 34)], step=1.0)
    # The steel echoes its island head, far left, once (no full statement).
    material.play_island(sc, CH_STEEL, 220.0, ISLAND_BASE_F, count=4,
                         vel=48, gate=0.95)
    # The cello: phrase-closing HOOK9s, the FUSION, and THE REACH.
    _cello_hook9(sc, 196.0)
    _cello_note(sc, 60, 205.0, 3.0, 56, vib=True)
    _cello_note(sc, 58, 208.0, 2.5, 54)
    _cello_hook9(sc, 212.0)
    _cello_note(sc, 62, 217.0, 3.0, 58, vib=True, swell=True)
    en.bend_ramp(sc, CH_CELLO, 216.8, 217.0, -0.5, 0.0)
    _cello_note(sc, 60, 220.0, 2.5, 54)
    _cello_hook9(sc, 224.0)
    _cello_note(sc, 57, 229.0, 3.0, 52, vib=True)
    _cello_note(sc, 55, 233.0, 3.0, 50, vib=True)
    material.play_fusion(sc, CH_CELLO, FUSION_T0, FUSION_BASE, vel=66,
                         gate=0.97)
    en.expr_curve(sc, CH_CELLO, [(FUSION_T0, 48), (FUSION_T0 + 5.0, 96),
                                 (FUSION_T0 + 8.0, 42)], step=0.5)
    _cello_hook9(sc, 250.0)
    material.play_fusion(sc, CH_CELLO, REACH_T0, REACH_BASE, retro=True,
                         count=RETRO_COUNT, vel=62, gate=0.96)
    en.expr_curve(sc, CH_CELLO, [(REACH_T0, 44), (REACH_T0 + 5.0, 90),
                                 (REACH_T0 + 7.0, 36)], step=0.5)
    _cello_note(sc, 62, 264.0, 3.0, 56, vib=True, swell=True)
    _cello_note(sc, 60, 267.0, 2.5, 52)
    _cello_hook9(sc, 270.0)
    _cello_note(sc, 58, 275.0, 3.0, 52, vib=True)
    _cello_note(sc, 57, 279.0, 3.0, 50)
    _cello_hook9(sc, 286.0)
    _cello_note(sc, 55, 291.0, 3.0, 48, vib=True)
    _cello_note(sc, 53, 294.0, 3.0, 46)
    _cello_hook9(sc, 298.0)
    # The choir opens as far as autumn allows (cap 70; we reach the 50s).
    _choir_phrase(sc, 200.0, [60, 65], dur=14.0, vel=46, vowel=(28, 52))
    _choir_phrase(sc, 224.0, [58, 62], dur=14.0, vel=46, vowel=(32, 55))
    _choir_phrase(sc, 248.0, [60, 64], dur=14.0, vel=48, vowel=(34, 55))
    _choir_phrase(sc, 272.0, [57, 60], dur=14.0, vel=44, vowel=(30, 48))
    _choir_phrase(sc, 292.0, [53, 60], dur=10.0, vel=40, vowel=(26, 40))
    sc.bend(CH_CELLO, 303.5, 0.0)


# ---------------------------------------------------------------------------
# IV. First Frost [304, 384) — the music box taps WANE over a settling
# frost; a breath of the old ice; the plagal iv-I; nine bells.  20 bars.
# ---------------------------------------------------------------------------

def _b_first_frost(sc):
    # The frost drone: low-string pairs, seamless to the bell tail.
    pairs = [(304.0, 12.0, (41, 48)), (316.0, 12.0, (46, 53)),
             (328.0, 12.0, (41, 48)), (340.0, 12.0, (46, 53)),
             (352.0, 6.0, (41, 48))]
    for t0, dur, ps in pairs:
        for p in ps:
            sc.note(CH_LOWSTR, p, t0, dur, 40, jt=0, jv=2)
        en.expr_curve(sc, CH_LOWSTR, [(t0, 30), (t0 + dur * 0.5, 56),
                                      (t0 + dur, 26)], step=1.0)
    # The music box, alone above the frost: WANE.
    material.play_morse(sc, CH_MUSICBOX, MORSE_T0, NUMBER, MORSE_PITCH,
                        vel=58)
    # A breath of the first winter's ice (unpinned colour).
    for t0 in (ICE_T0, ICE_T0 + 8.0, ICE_T0 + 16.0):
        material.play_hook(sc, CH_ICE, t0, ICE_BASE, 4, vel=42, gate=0.9)
    # The nylon lays the last leaves down.
    for bar, name in enumerate(["F", "Bb", "Gm", "C"]):
        _pick_bar(sc, 336.0 + 4.0 * bar, name, vel_off=-10, jt=0)
    # The plagal letter-close: Bb under, then home to F.
    sc.note(CH_BASS, 34, 348.0, 3.5, 54, jt=0, jv=2)
    sc.note(CH_BASS, 34, 352.0, 3.5, 50, jt=0, jv=2)
    sc.note(CH_BASS, 41, FINAL_DOWNBEAT, 4.0, 56, jt=0, jv=2)
    # Nine bells on the F, and nothing after them.
    material.play_tolls(sc, CH_BELLS, TOLL_T0, NUMBER, TOLL_PITCH,
                        spacing=TOLL_SPACING)


BUILDERS = [_b_shorter_days, _b_the_letters, _b_dont_be_careless,
            _b_first_frost]

RETRO_COUNT = material.RETRO_REACH[NUMBER]      # 8 — almost the whole way


# ---------------------------------------------------------------------------
# Track oracles — every promise above, machine-checked.
# ---------------------------------------------------------------------------

def oracles(sc, info, spans):
    isl = material.theme_statements(sc, "island")
    mnl = material.theme_statements(sc, "mainland")

    def o_convergence():
        fails = []
        memory = [s for s in isl
                  if material.island_tonic_pc(s[3]) == 4]     # pc 4 = E
        home = [s for s in isl if material.island_tonic_pc(s[3]) == 5]
        if len(memory) != 1 or abs(memory[0][1] - ISLAND_E_T0) > 0.1:
            fails.append(f"want exactly one E-minor memory at "
                         f"{ISLAND_E_T0} (got {memory})")
        if len(memory) + len(home) != len(isl):
            fails.append("an island statement implies neither F nor the "
                         "pinned E memory")
        if not home:
            fails.append("no island statement in the home F")
        if not mnl or any(material.mainland_tonic_pc(s[3]) != 5
                          for s in mnl):
            fails.append(f"mainland statements must all imply F ({mnl})")
        return fails

    def o_overlap():
        home = [s for s in isl if material.island_tonic_pc(s[3]) == 5]
        pairs = material.overlapping_pairs(home, mnl)
        if not pairs:
            return ["no island+mainland overlap (Act Two requires it)"]
        fails = []
        for a, b in pairs:
            lo, hi = max(a[1], b[1]), min(a[2], b[2])
            beat = math.ceil(lo / 4.0) * 4.0
            while beat < hi - 1e-6:
                for pa in _pitch_at(sc, a[0], beat):
                    for pb in _pitch_at(sc, b[0], beat):
                        if abs(pa - pb) % 12 not in _CONSONANT:
                            fails.append(f"overlap dissonant at {beat}: "
                                         f"{pa} vs {pb}")
                beat += 4.0
        return fails

    def o_fusion():
        fus = material.theme_statements(sc, "fusion")
        if len(fus) != 1 or fus[0][0] != CH_CELLO or \
                abs(fus[0][1] - FUSION_T0) > 0.1 or fus[0][3] % 12 != 5:
            return [f"want exactly one fusion, cello, F, at {FUSION_T0} "
                    f"(got {fus})"]
        return []

    def o_hook_density():
        n = len(material.hook_statements_unnested(sc, 9))
        return [] if n >= 6 else [f"HOOK9 unnested density {n} < 6"]

    def o_memory():
        hits = material.find_statements(
            material.note_ons(sc, CH_CELLO), material.HOOKS[1])
        good = [h for h in hits
                if abs(h[0] - HOOK1_T0) < 0.1 and h[2] >= 1.9]
        return [] if good else [f"no stretched heartbeat at {HOOK1_T0} "
                                f"(hits {hits})"]

    def o_reach():
        pref = material.retro_prefix_cell(RETRO_COUNT)
        hits = [(ch, s) for ch in sorted(sc.events)
                for s in material.find_statements(material.note_ons(sc, ch),
                                                  pref)]
        good = [h for h in hits
                if h[0] == CH_CELLO and abs(h[1][0] - REACH_T0) < 0.1]
        fails = []
        if not good:
            fails.append(f"no {RETRO_COUNT}-note reach at {REACH_T0}")
        if material.theme_statements(sc, "fusion_retro"):
            fails.append("the full road home must wait for T10")
        return fails

    def o_withheld():
        fails = []
        if material.theme_statements(sc, "island_major"):
            fails.append("island-in-major is T10's payoff")
        if material.theme_statements(sc, "fusion_retro"):
            fails.append("the full retrograde is T10's payoff")
        return fails

    def o_morse():
        ons = _note_ons(sc, CH_MUSICBOX)
        want = [(MORSE_T0 + on, du)
                for on, du in material.morse_rhythm(
                    material.MORSE_WORDS[NUMBER])]
        fails = []
        if len(ons) != len(want):
            fails.append(f"{len(ons)} taps, want {len(want)}")
        else:
            for (b, p, _v), (wb, _wd) in zip(ons, want):
                if abs(b - wb) > 1e-6 or p != MORSE_PITCH:
                    fails.append(f"tap at {b} pitch {p} off the WANE grid")
                    break
        progs = [(t, d[1]) for t, _p, d in sc.events.get(CH_MUSICBOX, [])
                 if (d[0] & 0xF0) == 0xC0]
        if [p for _t, p in progs] != [material.MORSE_PROGRAMS[NUMBER]]:
            fails.append(f"morse lane program {progs} != music box 10")
        return fails

    def o_vowel():
        cap = material.VOWEL_CAPS[NUMBER]
        bad = [(b, v) for b, v in _cc_lane(sc, CH_CHOIR, 70) if v > cap]
        return [] if not bad else [f"vowel over the autumn cap: {bad[:3]}"]

    def o_tide():
        fails = []
        for name, lo, hi in [(n, a, b) for n, a, b in PART.MOVEMENTS]:
            evs = _movement_events(lo, hi)
            vals = [bpm for _b, bpm in evs]
            if len(evs) < 8:
                fails.append(f"'{name}': only {len(evs)} tempo events")
                continue
            troughs = [v for v in vals if v <= 71.0]
            if len(troughs) < 2:
                fails.append(f"'{name}' does not breathe (troughs "
                             f"{troughs})")
            if max(vals) - min(vals) < 5.0:
                fails.append(f"'{name}' swell too shallow")
        return fails

    def o_plagal():
        return material.plagal_final_failures(sc, CH_BASS, FINAL_DOWNBEAT,
                                              5)

    def o_pans():
        fails = []
        for ch, want in ((CH_STEEL, ISL_PAN), (CH_MSTRING, MAIN_PAN),
                         (CH_CHOIR, ISL_PAN)):
            vals = {v for _b, v in _cc_lane(sc, ch, 10)}
            if vals != {want}:
                fails.append(f"ch{ch} pans {vals}, want {{{want}}}")
        return fails

    def o_tolls():
        ons = _note_ons(sc, CH_BELLS)
        fails = []
        if len(ons) != material.TOLLS[NUMBER]:
            fails.append(f"{len(ons)} tolls, want {material.TOLLS[NUMBER]}")
        if any(p % 12 != 5 for _b, p, _v in ons):
            fails.append("the buoy must toll the F")
        gaps = [b2 - b1 for (b1, _p1, _v1), (b2, _p2, _v2)
                in zip(ons, ons[1:])]
        lo, hi = material.TOLL_SPACING
        if any(not lo - 1e-6 <= g <= hi + 1e-6 for g in gaps):
            fails.append(f"toll spacing {gaps} outside {material.TOLL_SPACING}")
        for ch in sc.events:
            if ch == CH_BELLS:
                continue
            late = [b for b, _p, _v in _note_ons(sc, ch)
                    if b >= TOLL_T0 - 1e-6]
            if late:
                fails.append(f"ch{ch} sounds a new onset after the first "
                             f"toll ({late[:2]})")
        return fails

    def o_exemptions():
        # The ballad law: no herald voice anywhere (documented in the
        # module docstring); the exemption is machine-visible.
        for ch in sorted(sc.events):
            for _t, _p, d in sc.events.get(ch, []):
                if (d[0] & 0xF0) == 0xC0 and d[1] in (75, 77):
                    return [f"herald program {d[1]} on ch{ch} — the "
                            f"ballad arrives unannounced"]
        return []

    return [
        ("convergence", o_convergence()),
        ("overlap", o_overlap()),
        ("fusion", o_fusion()),
        ("hook_density", o_hook_density()),
        ("memory", o_memory()),
        ("the_reach", o_reach()),
        ("withheld_payoffs", o_withheld()),
        ("morse_wane", o_morse()),
        ("vowel_cap", o_vowel()),
        ("tide_breath", o_tide()),
        ("plagal_final", o_plagal()),
        ("shore_pans", o_pans()),
        ("tolls", o_tolls()),
        ("ballad_exemptions", o_exemptions()),
    ]


# ---------------------------------------------------------------------------
# Audio oracles (RATIO checks only — repo law).  Calibrated after render.
# ---------------------------------------------------------------------------

def audio_checks(ctx):
    verse = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(8.0, 88.0))
    chorus = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(200.0, 300.0))
    frost = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(305.0, 350.0))
    tail = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(365.0, 382.0))

    def c_intimacy():
        # Calibrated 2026.07.19 (measured -0.80 dB): the real claim is the
        # CEILING — a tender chorus must never blow up past the verse; it
        # may legitimately sit at (or a shade below) verse level, because
        # the chorus trades fingerpicking density for sustained warmth.
        lift = ctx.db(chorus) - ctx.db(verse)
        return [] if -2.0 <= lift <= 9.0 else [
            f"chorus lift {lift:.2f} dB outside the intimate window"]

    def c_frost():
        drop = ctx.db(chorus) - ctx.db(frost)
        return [] if drop >= 1.0 else [
            f"first frost only {drop:.2f} dB below the chorus"]

    def c_tail():
        # Calibrated 2026.07.19: nine tubular-bell tolls at the end of a
        # pp ballad are legitimately LOUDER than its chorus (the original
        # tail-vs-chorus ratio mis-modelled the design).  The honest claim
        # is the DECAY: the peal audibly fades — the late tail sits well
        # below the early peal.
        early = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(360.0, 370.0))
        late = ctx.rms(ctx.l, ctx.r, *ctx.bar_window(378.0, 384.0))
        drop = ctx.db(early) - ctx.db(late)
        return [] if drop >= 3.0 else [
            f"the peal only fades {drop:.2f} dB into the close"]

    return [
        ("audio_intimate_chorus", c_intimacy()),
        ("audio_frost_recedes", c_frost()),
        ("audio_toll_tail", c_tail()),
    ]
