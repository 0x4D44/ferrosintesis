"""m2_humming — Part One, Movement 2 "The Humming" (beats 256-544,
E aeolian -> dorian from 400, 84).  Crash Test Dummies.

Roadmap section 4, M2:

  Ground: HUM_GROUND loops (i III VII iv = Em G D Am, 16-beat cycles);
  ch7 steel fingerpicks it (4-voice broken pattern), ch4 harmonium holds
  chords with CC66 sostenuto pedal-points — the cycle root (E) is caught
  at each cycle start and released at cycle end (downs == ups); ch0 piano
  una corda (CC67) for the whole movement (off at 544), sparse pools.
  272-304  Verse 1: ch6 sings THEME complete, CC70=mm, low, vel 55-65;
           lyric metas "Mm"/"hm" on its notes (>= 6 in the movement).
  304-336  Answer: ch14 flute theme bars 5-6; nylon counter-arps.
  336-400  Verse 2: hum + ch11 a diatonic 3rd above at CC70~45 ("oo"),
           vel -8; RPN fine-tune -6 cents on ch11 at 256.
  400-464  Bridge: dorian F# admitted; strings enter; harmonium walks
           III-IV(dorian)-VII; hum fragments trade; aftertouch crescendo.
  464-528  Verse 3: fullest — both choirs, strings, flute descant.
  528-544  thins to harmonium + one choir "mm" on degree 2 (half cadence).

Implementation notes
--------------------
* No pitch bends anywhere in M2 (the choirs express through channel
  aftertouch + CC70 vowel morphs), so every channel is trivially recentred
  at the 256/544 boundaries the bend-hygiene oracle checks.
* The E pedal-point is a real 16-beat drone AND a CC66 sostenuto gesture,
  so the sound survives on any synth while the controller shows the pedal.
* ch11 ensemble width is RPN 1 fine-tune (-6 cents), NOT the bend lane.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m

AEO = "aeolian"
DOR = "dorian"

T0, T1 = 256.0, 544.0
CYCLE = 16.0

# A mono-safe stereo image for the intimate hum (fix: the -5.6 dB mono
# collapse).  The synth localises CC10 pan with a Haas micro-delay
# (engine.rs ~L682); on SUSTAINED tonal voices that micro-delay combs when
# the mix folds to mono, and The Humming is sparse+wet enough that the comb
# dominated the whole mix (measured full-mix corr -0.45).  Fix: keep the
# sustained beds dead centre (no Haas), take the width from the choir spread
# plus the transient fingerpicked guitars (bright plucked content does NOT
# comb at the Haas lag), and leave those guitars at their wide conductor
# pans.  Measured M2 mono loss drops to ~0.6 dB.  (CC93 chorus is nearly
# mono-neutral on this synth — the finding's "chorus bus" diagnosis was
# wrong — but we still trim it a shade per the brief; it barely matters.)
CHOIR_CHORUS = 30        # a shade under the ~38 (0.30) choir program default
CHOIR1_PAN = 56          # choir I a little left of centre
CHOIR2_PAN = 72          # choir II a little right of centre
BED_PAN = 64             # sustained beds dead centre (mono-safe: no Haas)
# Conductor pans, restored at the M2->M3 seam so M3 keeps its own image.
_CONDUCTOR_PANS = {cd.CH_PIANO: 50, cd.CH_ORGAN: 58, cd.CH_STRINGS: 70,
                   cd.CH_WINDS: 70, cd.CH_CHOIR1: 54, cd.CH_CHOIR2: 74}

# Section boundaries (all land on 16-beat cycle starts).
V1, ANS, V2A, V2L = 272.0, 304.0, 336.0, 368.0
BR, V3A, V3B, END = 400.0, 464.0, 496.0, 528.0

# Modal anchors: degree 1 = E in each register (P1 is E aeolian).
ORG_ROOT = en.n("E2")    # 40 — harmonium pedal-point drone
ORG_BASE = en.n("E3")    # 52 — harmonium reed chords (mid)
CH1_BASE = en.n("E3")    # 52 — choir I hum, low (degrees 0..8 -> 50..64)
CH2_BASE = en.n("E3")    # 52 — choir II (the +2 shift lifts it a 3rd)
STEEL_BASE = en.n("E3")  # 52 — fingerpicked ground
NYL_BASE = en.n("E3")    # 52 — counter-arpeggios
PIANO_BASE = en.n("E4")  # 64 — pooled una-corda arps, high
FLUTE_BASE = en.n("E4")  # 64 — verse answers / descant, high
STR_BASE = en.n("E3")    # 52 — bridge + verse-3 pad

# The channels M2 actually plays (for the CC91 distance set at 256).
MY_CHANNELS = (cd.CH_PIANO, cd.CH_ORGAN, cd.CH_STRINGS, cd.CH_CHOIR1,
               cd.CH_STEEL, cd.CH_NYLON, cd.CH_CHOIR2, cd.CH_WINDS)

# ch11's verse-2 harmony, once: the theme a diatonic 3rd above, snapped to
# HUM_GROUND chord tones on the strong beats (material's verified pairing).
HARM2 = m.snap_to_chord(m.shift_steps(m.THEME, 2), m.HUM_GROUND, AEO)

# The flute's answer: theme bars 5-6 (beats 16-24), rebased to start at 0.
ANSWER = [(d, s - 16.0, du) for d, s, du in m.THEME if 16.0 <= s < 24.0]

# Steel fingerpick patterns: (offset_in_bar, voice_index) over voices
# [low(root-8ve), triad[0], triad[1], triad[2]].
PICK4 = [(0.0, 0), (1.0, 1), (2.0, 2), (3.0, 3)]
PICK6 = [(0.0, 0), (1.0, 3), (1.5, 2), (2.0, 1), (3.0, 3), (3.5, 2)]


# ---------------------------------------------------------------------------
# Section / harmony lookup
# ---------------------------------------------------------------------------
def _section(b: float) -> str:
    if b < V1:
        return "intro"
    if b < ANS:
        return "v1"
    if b < V2A:
        return "answer"
    if b < V2L:
        return "v2a"
    if b < BR:
        return "v2link"
    if b < V3A:
        return "bridge"
    if b < END:
        return "v3"
    return "end"


def _bar_chord(b: float) -> tuple[int, str]:
    """(root degree, mode) of the ground chord sounding in the bar at `b`."""
    cyc = 256 + 16 * ((int(b) - 256) // 16)
    if BR <= cyc < V3A:                       # bridge cycles: dorian walk
        return [3, 4, 7, 1][((int(b) - 256) // 4) % 4], DOR
    return [1, 3, 7, 4][((int(b) - 256) // 4) % 4], AEO   # i III VII iv


# ---------------------------------------------------------------------------
# Distance arc + the mono-safe stereo image (see the pan notes at the top)
# ---------------------------------------------------------------------------
def _distance(sc) -> None:
    for ch in MY_CHANNELS:
        sc.cc(ch, 91, 70, T0)                     # CC91 ~70 distance
    # Centre the sustained beds (piano pools, harmonium drone, string pads,
    # flute) so their Haas micro-delay cannot comb in mono; the width comes
    # from the choir spread (in _choir) and the transient fingerpicked
    # guitars, which stay at their wide conductor pans.
    for ch in (cd.CH_PIANO, cd.CH_ORGAN, cd.CH_STRINGS, cd.CH_WINDS):
        sc.cc(ch, 10, BED_PAN, T0)
    # Restore every re-panned channel to its conductor pan at the seam so
    # Footsteps (M3) inherits its own stereo image, not M2's.
    for ch, pan in _CONDUCTOR_PANS.items():
        sc.cc(ch, 10, pan, T1 - 0.2)


# ---------------------------------------------------------------------------
# Harmonium (ch4): held reed chords + E pedal-point held by CC66 sostenuto
# ---------------------------------------------------------------------------
_HARM_VEL = {"intro": 50, "v1": 54, "answer": 53, "v2a": 56, "v2link": 56,
             "bridge": 55, "v3": 60, "end": 52}


def _harmonium(sc) -> None:
    for c in range(256, 528, 16):             # 17 cycles; the 18th is the end
        sec = _section(c)
        mode = DOR if BR <= c < V3A else AEO
        roots = [3, 4, 7, 1] if mode == DOR else [1, 3, 7, 4]
        vel = _HARM_VEL[sec]
        # E pedal-point: a real drone AND the sostenuto pedal that catches it.
        sc.note(cd.CH_ORGAN, ORG_ROOT, c, 15.85, vel - 4, jt=3, jv=3)
        en.sostenuto(sc, cd.CH_ORGAN, c + 0.03, c + 15.8)
        # Voice-led reed chords, one per bar, common tones tied.
        chords = [en.triad(ORG_BASE, mode, r) for r in roots]
        en.pad_block(sc, cd.CH_ORGAN, c, chords, span=4.0, size=3,
                     lo=50, hi=74, vel=vel, legato=0.35)

    # 528-544: the half cadence.  A hanging Bm (v) over the E pedal — an
    # unresolved E/F#/B/D sonority — Part One must not resolve.
    sc.note(cd.CH_ORGAN, ORG_ROOT, END, 16.5, 48, jt=3, jv=3)   # E rings on
    en.sostenuto(sc, cd.CH_ORGAN, END + 0.03, 543.8)
    for p, dv in ((en.n("B3"), 0), (en.n("D4"), -3), (en.n("F#4"), -2)):
        sc.note(cd.CH_ORGAN, p, END, 15.5, 50 + dv, jt=3, jv=3)


# ---------------------------------------------------------------------------
# Steel guitar (ch7): fingerpicked ground, 4-voice broken pattern
# ---------------------------------------------------------------------------
def _steel(sc) -> None:
    for b in range(260, 528, 4):              # enters one bar in; out at 528
        sec = _section(b)
        rd, mode = _bar_chord(b)
        low = en.pitch(STEEL_BASE, mode, rd) - 12
        tri = en.triad(STEEL_BASE, mode, rd)
        voices = [low, tri[0], tri[1], tri[2]]
        if sec == "v1":
            # The FIRST hum is the most intimate moment: leave it bare.  Two
            # soft sustained half-note chords per bar under the voice — no
            # busy fingerpicking (that returns in verse 2 at 336).
            for hb in (0.0, 2.0):
                en.strum(sc, cd.CH_STEEL, [low, tri[0], tri[1], tri[2]],
                         b + hb, 1.9, 50, spread=0.05, down=True)
            continue
        if sec == "v3":                       # fullest: busier pick
            pattern, vel = PICK6, 59
        elif sec in ("v2a", "bridge"):
            pattern, vel = PICK6, 57
        else:
            pattern, vel = PICK4, 55
        for off, vi in pattern:
            on_beat = abs(off - round(off)) < 1e-9
            acc = 3 if off == 0.0 else (-4 if not on_beat else 0)
            dur = 0.95 if on_beat else 0.55
            sc.note(cd.CH_STEEL, voices[vi], b + off, dur, vel + acc,
                    jt=4, jv=4)


# ---------------------------------------------------------------------------
# Piano (ch0): una corda whole movement; sparse high pooled arpeggios
# ---------------------------------------------------------------------------
def _piano(sc) -> None:
    en.soft_pedal(sc, cd.CH_PIANO, T0, T1)    # CC67 on at 256, off at 544
    pools = [264.0] + [272.0, 288.0, 336.0, 352.0,
                       464.0, 480.0, 496.0, 512.0]
    for c in pools:
        rd, mode = _bar_chord(c)
        vel = 48 if c < BR else 54            # a shade fuller in verse 3
        for k, dg in enumerate((rd, rd + 2, rd + 4, rd + 7)):
            p = en.pitch(PIANO_BASE, mode, dg)
            sc.note(cd.CH_PIANO, p, c + k * 0.75, 6.5, vel, jt=6, jv=4)


# ---------------------------------------------------------------------------
# Choir singing helper (theme / harmony / fragment) with a gentle arch
# ---------------------------------------------------------------------------
def _sing(sc, ch, t0, base, mode, phrase, vel, shift=0, octave=0,
          gate=0.95, jt=5, jv=4, lyr=None) -> None:
    for deg, s, d in phrase:
        arch = 4 if 18.0 <= s <= 24.0 else (2 if 8.0 <= s <= 12.0 else 0)
        p = en.pitch(base, mode, deg + shift) + 12 * octave
        sc.note(ch, p, t0 + s, d * gate, vel + arch, jt=jt, jv=jv)
    for b, txt in (lyr or ()):
        en.lyric(sc, t0 + b, txt)


def _swell(sc, ch, t0, t1, lo, peak, end) -> None:
    """A breathing aftertouch crescendo/decrescendo inside a held phrase."""
    en.at_curve(sc, ch, [(t0, lo), ((t0 + t1) / 2.0, peak), (t1, end)],
                step=0.5)


LYR_V1 = [(0.0, "Mm"), (4.0, "mm"), (8.0, "hm"), (12.0, "mm"),
          (16.0, "Mm"), (20.0, "mm"), (24.0, "hm"), (28.0, "mm")]


# ---------------------------------------------------------------------------
# Choir I (ch6) + Choir II (ch11): the humming
# ---------------------------------------------------------------------------
def _choir(sc) -> None:
    # The choirs carry the hum's width: spread a little left/right (mono-safe
    # at this modest offset — the sustained beds are centred so the Haas comb
    # stays small).  CC93 trimmed a shade under the choir program default.
    sc.cc(cd.CH_CHOIR1, 93, CHOIR_CHORUS, T0)
    sc.cc(cd.CH_CHOIR2, 93, CHOIR_CHORUS, T0)
    sc.cc(cd.CH_CHOIR1, 10, CHOIR1_PAN, T0)    # a little left of centre
    sc.cc(cd.CH_CHOIR2, 10, CHOIR2_PAN, T0)    # a little right of centre

    en.vowel(sc, cd.CH_CHOIR1, 0, T0)          # mm for the whole movement
    en.vowel(sc, cd.CH_CHOIR2, 45, V2A)        # oo when choir II enters
    en.fine_tune(sc, cd.CH_CHOIR2, -6, T0)     # ensemble width (RPN, not bend)

    # Verse 1: choir I sings the theme, low, wordless.
    _sing(sc, cd.CH_CHOIR1, V1, CH1_BASE, AEO, m.THEME, 58, lyr=LYR_V1)
    _swell(sc, cd.CH_CHOIR1, V1, ANS - 0.5, 22, 80, 34)

    # Verse 2a: choir I theme + choir II a diatonic 3rd above (oo).
    _sing(sc, cd.CH_CHOIR1, V2A, CH1_BASE, AEO, m.THEME, 59,
          lyr=[(0.0, "Mm"), (12.0, "mm"), (28.0, "hm")])
    _sing(sc, cd.CH_CHOIR2, V2A, CH2_BASE, AEO, HARM2, 51)
    _swell(sc, cd.CH_CHOIR1, V2A, V2L - 0.5, 26, 82, 40)
    _swell(sc, cd.CH_CHOIR2, V2A, V2L - 0.5, 18, 62, 30)

    # Verse-2 link: both choirs sustain a held 3rd, breathing up the bridge.
    sc.note(cd.CH_CHOIR1, en.pitch(CH1_BASE, AEO, 1), V2L, 14.0, 55, jt=4)
    sc.note(cd.CH_CHOIR2, en.pitch(CH2_BASE, AEO, 3), V2L, 14.0, 49, jt=4)
    en.lyric(sc, V2L, "mm")
    _swell(sc, cd.CH_CHOIR1, V2L, V2L + 14.0, 30, 72, 52)
    _swell(sc, cd.CH_CHOIR2, V2L, V2L + 14.0, 24, 62, 46)

    # Bridge: 8-beat hum fragments trade choir I <-> choir II, growing.
    starts = list(range(int(BR), int(V3A), 8))
    for i, t in enumerate(starts):
        grow = i / (len(starts) - 1)
        ch = cd.CH_CHOIR1 if i % 2 == 0 else cd.CH_CHOIR2
        base = CH1_BASE if i % 2 == 0 else CH2_BASE
        _sing(sc, ch, float(t), base, DOR, m.THEME_FRAG,
              int(en.lerp(50, 63, grow)))
    en.at_curve(sc, cd.CH_CHOIR1, [(BR, 25), (V3A - 2, 112)], step=0.5)
    en.at_curve(sc, cd.CH_CHOIR2, [(BR, 22), (V3A - 2, 104)], step=0.5)
    en.lyric(sc, BR, "mm")
    en.lyric(sc, 432.0, "hm")

    # Verse 3 (aeolian again): both choirs, two statements — the fullest.
    for t0, v1, v2 in ((V3A, 61, 55), (V3B, 62, 56)):
        _sing(sc, cd.CH_CHOIR1, t0, CH1_BASE, AEO, m.THEME, v1,
              lyr=[(0.0, "Mm"), (16.0, "mm")])
        _sing(sc, cd.CH_CHOIR2, t0, CH2_BASE, AEO, HARM2, v2)
        _swell(sc, cd.CH_CHOIR1, t0, t0 + 31.5, 34, 88, 44)
        _swell(sc, cd.CH_CHOIR2, t0, t0 + 31.5, 28, 70, 38)

    # 528-544: one choir holds degree 2 (F#) on "mm" — the half cadence.
    sc.note(cd.CH_CHOIR1, en.pitch(CH1_BASE, AEO, 2), END, 16.0, 53, jt=4)
    en.lyric(sc, END, "Mm...")
    en.lyric(sc, 536.0, "(hm)")
    en.at_curve(sc, cd.CH_CHOIR1, [(END, 42), (534.0, 66), (543.5, 16)],
                step=0.5)


# ---------------------------------------------------------------------------
# Flute (ch14): verse answers + verse-3 descant
# ---------------------------------------------------------------------------
def _flute(sc) -> None:
    _sing(sc, cd.CH_WINDS, ANS, FLUTE_BASE, AEO, ANSWER, 62)          # answer
    _sing(sc, cd.CH_WINDS, ANS + 16.0, FLUTE_BASE, AEO, ANSWER, 60)   # echo
    _sing(sc, cd.CH_WINDS, 384.0, FLUTE_BASE, AEO, ANSWER, 58)        # link
    # Verse-3 descant: the +2-step harmony an octave up, high and floating.
    _sing(sc, cd.CH_WINDS, V3A, FLUTE_BASE, AEO, HARM2, 60, octave=1)
    _sing(sc, cd.CH_WINDS, V3B, FLUTE_BASE, AEO, HARM2, 61, octave=1)


# ---------------------------------------------------------------------------
# Nylon (ch8): counter-arpeggios under the answer
# ---------------------------------------------------------------------------
def _nylon(sc) -> None:
    for b in range(int(ANS), int(V2A), 4):
        rd, mode = _bar_chord(b)
        pcs = en.triad(NYL_BASE, mode, rd)
        en.arp(sc, cd.CH_NYLON, pcs, float(b), 8, 0.5, 54,
               pattern="updown", gate=0.9, accent_every=4, accent=6)


# ---------------------------------------------------------------------------
# Strings (ch5): terrace in for the bridge, pad through verse 3
# ---------------------------------------------------------------------------
def _strings(sc) -> None:
    for b in range(int(BR), int(END), 4):
        rd, mode = _bar_chord(b)
        root = en.pitch(STR_BASE, mode, rd)
        fifth = en.pitch(STR_BASE, mode, rd + 4)
        vel = 53 if b < V3A else 57
        sc.note(cd.CH_STRINGS, root, float(b), 4.1, vel, jt=3, jv=3)
        sc.note(cd.CH_STRINGS, fifth, float(b), 4.1, vel - 4, jt=3, jv=3)
    en.expr_curve(sc, cd.CH_STRINGS, [(BR, 30), (V3A - 2, 74)], step=2.0)
    en.expr_curve(sc, cd.CH_STRINGS, [(V3A, 72), (END - 2, 82)], step=2.0)


# ---------------------------------------------------------------------------
def build(sc) -> None:
    _distance(sc)
    _harmonium(sc)
    _steel(sc)
    _piano(sc)
    _nylon(sc)
    _strings(sc)
    _flute(sc)
    _choir(sc)
