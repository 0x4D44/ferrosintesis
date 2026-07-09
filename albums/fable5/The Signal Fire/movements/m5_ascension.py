"""m5_ascension — Movement 5 "Ascension" (beats 1312-1592, A ionian, 112, ff).

The radiant arrival the whole piece climbs toward.  Downbeat 1312 lands the
full A-major tutti (crash + kick, every channel striking together); tubular
bells peal THEME_A in double augmentation twice (1312 and 1440 — the second
peal doubled 8va by the glockenspiel), strings + choir carry THEME_C in
octaves at the SAME augmentation, and the lead answers between bell phrases
with THEME_B statements and derived wails (scoop bends, blooming vibrato,
echo throws), ch13 harmonizing in real diatonic 3rds/6ths.  Underneath:
four-on-the-floor drums with open-hat offbeats and fills every 8 bars (ride
8ths join at the second peal), bass RIFF_AUG twice then the active
major-mode RIFF_FUNK, ch10+ch11 interlocking figuration (the riff composite
[1,5,8,7,5,6,4,5] split odd/even — together constant, alone sparse; doubled
to 16ths from the second peal at 1440), piano glitter arps and
full organ with the Leslie fast (CC1=127, held).  The harmonic ground is the
augmented i-bVII recoloured by the mode: A(add9) | E7 in 8-beat blocks.
1560-1584 the IV - V(sus4->3) - I cadence (D - Esus4-E - A) drives to a full
stop at 1584: only the pad's A-add9 (struck 1580, ringing to 1600) and one
final bell on A (1583, 16 beats) sound across the silence into M6, their
CC91 thrown to 90 — the ring released into the hall.  CC91 is 35 everywhere
else: the closest, driest, loudest, densest movement.
"""

from __future__ import annotations

import conductor as cd
import engine as en
import material as m
from engine import lerp, n

ION = "ionian"

T0, T1 = 1312.0, 1592.0
PEAL2 = 1440.0                  # second peal statement
CAD = 1560.0                    # IV - V(sus4->3) - I cadence
STOP = 1584.0                   # the full stop

BASS_A = n("A1")                # bass degree-1 anchor (33)
GTR_A = n("A3")                 # figuration / strings anchor (57)
CHOIR_A = n("A4")               # choir an octave above the strings (69)
LEAD_A = n("A4")                # lead + harmony anchor (69)
BELL_A = n("A4")                # bells (glockenspiel doubles +12)
PNO_A = n("A5")                 # piano glitter anchor (81)

# The riff composite condensed to 4/4 (roadmap section 4 / M5), split by
# index: even -> ch10 (on-beats), odd -> ch11 (off-beats).
COMPOSITE = (1, 5, 8, 7, 5, 6, 4, 5)

# Piano glitter arpeggio degrees per harmonic block / cadence chord.
_ARPS = {"A": (1, 3, 5, 8, 10, 12, 15), "E": (5, 7, 9, 12, 14, 16),
         "D": (4, 6, 8, 11, 13, 15), "Esus": (5, 8, 9, 12, 15, 16)}

MY_CHANNELS = (cd.CH_PIANO, cd.CH_PAD, cd.CH_CRYSTAL, cd.CH_BASS,
               cd.CH_ORGAN, cd.CH_STRINGS, cd.CH_CHOIR, cd.CH_DRUMS,
               cd.CH_RHYTHM, cd.CH_WAH, cd.CH_LEAD, cd.CH_DOUBLE,
               cd.CH_BELLS)


def _block_is_A(beat: float) -> bool:
    """Augmented ground: A(add9) / E7 alternating in 8-beat blocks."""
    return int((beat - T0) // 8) % 2 == 0


# ---------------------------------------------------------------------------
# Controllers — the movement-start mix (CC91 arc value 35, roadmap section 5)
# ---------------------------------------------------------------------------
def _controllers(sc):
    for ch in MY_CHANNELS:
        sc.cc(ch, 91, 35, T0)                 # closest, driest movement
    sc.cc(cd.CH_DOUBLE, 10, 90, T0)           # ch13 in from hard-right 108
    # ch0/ch10/ch11 (glitter + figuration) get a breath cycle instead (_breath).
    for ch, v in ((cd.CH_PAD, 80), (cd.CH_CRYSTAL, 100),
                  (cd.CH_BASS, 115), (cd.CH_ORGAN, 100), (cd.CH_DRUMS, 118),
                  (cd.CH_LEAD, 95), (cd.CH_DOUBLE, 90), (cd.CH_BELLS, 110)):
        sc.cc(ch, 11, v, T0)
    # the second peal lifts CC11 +5 everywhere it is riding
    for ch, v in ((cd.CH_ORGAN, 105),
                  (cd.CH_LEAD, 100), (cd.CH_DOUBLE, 95), (cd.CH_BELLS, 115),
                  (cd.CH_CRYSTAL, 105)):
        sc.cc(ch, 11, v, PEAL2)
    sc.cc(cd.CH_LEAD, 11, 105, CAD)
    sc.cc(cd.CH_DOUBLE, 11, 100, CAD)
    # strings + choir breathe with the peals (85 base, +5 at the second)
    for ch, off in ((cd.CH_STRINGS, 0), (cd.CH_CHOIR, -3)):
        en.expr_curve(sc, ch, [(T0, 85 + off), (1332.0, 90 + off),
                               (1352.0, 95 + off), (1374.0, 82 + off)], step=2)
        en.expr_curve(sc, ch, [(1408.0, 70 + off), (1438.0, 88 + off)], step=2)
        en.expr_curve(sc, ch, [(PEAL2, 90 + off), (1480.0, 100 + off),
                               (1502.0, 92 + off)], step=2)
        en.expr_curve(sc, ch, [(1504.0, 92 + off), (CAD, 100 + off),
                               (1580.0, 110 + off), (1583.5, 104 + off)],
                      step=2)
    sc.cc(cd.CH_ORGAN, 1, 127, T0)            # Leslie fast, held throughout
    sc.cc(cd.CH_PAD, 74, 110, T0)             # pad filter wide open
    en.cc_curve(sc, cd.CH_PAD, 11, [(1578.0, 80), (1583.0, 96)], step=0.5)
    sc.cc(cd.CH_PAD, 91, 90, 1583.0)          # throw the ring into the hall
    sc.cc(cd.CH_BELLS, 91, 90, 1583.0)


def _breath(sc):
    """A CC11 breath cycle (~95 -> 75 -> 95 per 8 bars) on the high-note-count
    glitter/figuration channels, which otherwise sit pinned wide open — so the
    climax swells and recedes.  Written only across each channel's active
    spans (the brief internal rests get no CC11)."""
    spans = {
        cd.CH_PIANO:  [(T0, 1376.0), (1408.0, CAD)],     # glitter
        cd.CH_RHYTHM: [(T0, 1376.0), (1392.0, CAD)],     # figuration (on-beat)
        cd.CH_WAH:    [(T0, 1376.0), (1392.0, CAD)],     # figuration (off-beat)
    }
    for ch, chspans in spans.items():
        for s, e in chspans:
            pts, b, peak = [], s, True
            while b < e - 1e-9:
                pts.append((b, 95 if peak else 75))
                peak = not peak
                b += 16.0
            pts.append((e, 95 if peak else 75))
            en.expr_curve(sc, ch, pts, step=2.0)


# ---------------------------------------------------------------------------
# Drums — four-on-the-floor, open-hat offbeats, crash accents, 8-bar fills
# ---------------------------------------------------------------------------
def _drums(sc):
    for bar in range(68):                     # 1312-1584
        b = T0 + bar * 4
        if bar == 67:                         # 1580-1584: drive to 1583, stop
            sc.hit(49, b, 118)
            for k in range(4):
                sc.hit(36, b + k, 114)
            sc.hit(38, b + 1.5, 102)
            sc.hit(38, b + 2.5, 106)
            sc.hit(49, b + 3, 118)            # the last strike, beat 1583
            continue
        fill_bar = (bar % 8 == 7) and b < 1576.0
        for k in range(4):
            # backbeat kicks sit under the snare: trim them (mask + declick)
            sc.hit(36, b + k, 112 if k == 0 else (104 if k % 2 else 108))
        sc.hit(38, b + 1, 102)
        sc.hit(38, b + 3, 98 if fill_bar else 102)
        for k in range(4):                    # open-hat offbeats
            if fill_bar and k >= 2:
                continue                      # clear space for the fill
            sc.hit(46, b + k + 0.5, 86 if k % 2 == 0 else 78)
        if bar % 8 == 0:
            sc.hit(49, b, 116)                # section crash
        elif b >= PEAL2 and bar % 4 == 0:
            sc.hit(57, b, 108)                # second-peal crash pushes
        if b >= PEAL2 and bar % 8 == 7:
            sc.hit(49, b + 3.5, 98)           # push into the downbeat
        if b >= PEAL2:                        # ride 8ths join the 2nd peal
            for k in range(8):
                if fill_bar and k >= 4:
                    break                     # the fill takes the kit over
                sc.hit(51, b + k * 0.5, 96 if k % 2 == 0 else 86)
        if fill_bar:
            if (bar // 8) % 2 == 0:           # snare run into tom drops
                for i, v in enumerate((88, 92, 97, 102)):
                    sc.hit(38, b + 2 + i * 0.25, v)
                for i, (d, v) in enumerate(((48, 98), (45, 100),
                                            (43, 102), (41, 104))):
                    sc.hit(d, b + 3 + i * 0.25, v)
            else:                             # tom cascade
                for i, (d, v) in enumerate(((50, 92), (48, 95), (47, 98),
                                            (45, 100), (43, 102), (41, 104))):
                    sc.hit(d, b + 2.5 + i * 0.25, v)
        if bar == 66:                         # 1576-1580 the roll into I
            for i in range(8):
                sc.hit(38, b + 2 + i * 0.25, 90 + 2 * i)
    sc.hit(49, CAD, 114)                      # cadence downbeat crashes
    sc.hit(57, 1576.0, 112)


# ---------------------------------------------------------------------------
# Bass — RIFF_AUG twice, then the active major-mode RIFF_FUNK, cadence pump
# ---------------------------------------------------------------------------
def _bass(sc):
    ch = cd.CH_BASS
    for rep in range(2):                      # 1312-1344 half-time augmented
        t = T0 + rep * 16
        for deg, s, d in m.RIFF_AUG:
            v = 106 if s in (0, 3, 8, 14) else 101
            sc.note(ch, en.pitch(BASS_A, ION, deg), t + s, d * 0.95, v,
                    jt=3, jv=3)
    for bar in range(54):                     # 1344-1560 the funk engine
        b = 1344.0 + bar * 4
        v = int(lerp(100, 105, bar / 53))
        if bar % 4 == 3:                      # every 4th bar: fill variation
            keep = [nt for nt in m.RIFF_FUNK if nt[1] < 3.0]
            en.line(sc, ch, b, BASS_A, ION, keep, v, gate=0.9, jt=3, jv=3)
            if (bar // 4) % 2 == 0:           # walk-up 5-6-7-8 (7 = G#!)
                fill = [(5, 3.0, 0.25), (6, 3.25, 0.25),
                        (7, 3.5, 0.25), (8, 3.75, 0.25)]
            else:                             # drop to 0-1
                fill = [(1, 3.0, 0.5), (0, 3.5, 0.25), (1, 3.75, 0.25)]
            en.line(sc, ch, b, BASS_A, ION, fill, v + 2, gate=0.9, jt=3, jv=3)
        else:
            en.line(sc, ch, b, BASS_A, ION, m.RIFF_FUNK, v,
                    gate=0.9, jt=3, jv=3)
            en.line(sc, ch, b, BASS_A, ION, m.RIFF_FUNK_GHOSTS, v - 30,
                    gate=0.8, jt=3, jv=3)
    # cadence: root/octave pump D -> Esus/E (walk F#-G#) -> A, stop at 1584
    for b0, root, high in ((1560.0, 4, 11), (1568.0, 5, 12)):
        for bar in range(2):
            b = b0 + bar * 4
            for k, deg in enumerate((root, root, high, root,
                                     root, high, root, root)):
                sc.note(ch, en.pitch(BASS_A, ION, deg), b + k * 0.5, 0.42,
                        105 if k == 0 else 100, jt=3, jv=3)
    for k, deg in enumerate((5, 5, 12, 5, 5, 12)):
        sc.note(ch, en.pitch(BASS_A, ION, deg), 1576.0 + k * 0.5, 0.42,
                103, jt=3, jv=3)
    sc.note(ch, en.pitch(BASS_A, ION, 6), 1579.0, 0.45, 104, jt=2, jv=3)
    sc.note(ch, en.pitch(BASS_A, ION, 7), 1579.5, 0.45, 108, jt=2, jv=3)
    for t, deg, dur in ((1580.0, 1, 0.9), (1581.0, 8, 0.45), (1581.5, 1, 0.45),
                        (1582.0, 5, 0.45), (1582.5, 1, 0.45), (1583.0, 1, 0.9)):
        sc.note(ch, en.pitch(BASS_A, ION, deg), t, dur, 108, jt=2, jv=3)


# ---------------------------------------------------------------------------
# ch10 + ch11 — the interlocking figuration (even/odd split of COMPOSITE)
# ---------------------------------------------------------------------------
def _fig_bar(sc, b, vel, sixteenth=False):
    for k, deg in enumerate(COMPOSITE):
        ch = cd.CH_RHYTHM if k % 2 == 0 else cd.CH_WAH
        v = vel + (7 if k == 0 else 0) + (3 if k == 4 else 0)
        p = en.pitch(GTR_A, ION, deg)
        if sixteenth:
            for half in range(2):
                sc.note(ch, p, b + half * 2 + k * 0.25, 0.7,
                        v - (4 if half else 0), jt=3, jv=3)
        else:
            sc.note(ch, p, b + k * 0.5, 1.4, v, jt=3, jv=3)


def _figuration(sc):
    for bar in range(16):                     # 1312-1376 with the first peal
        _fig_bar(sc, T0 + bar * 4, 94)
    for bar in range(12):                     # 1392-1440 (rests 1376-1392)
        _fig_bar(sc, 1392.0 + bar * 4, 97)
    for bar in range(30):                     # 1440-1560 doubled to 16ths
        _fig_bar(sc, PEAL2 + bar * 4, 95 + (2 if bar >= 16 else 0),
                 sixteenth=True)
    # cadence: chord-tone interlock carrying the sus4 -> 3 resolution
    plans = ((1560.0, 2, (4, 6, 8, 11), (8, 11, 6, 11)),      # D
             (1568.0, 2, (5, 8, 9, 12), (9, 12, 8, 9)),       # Esus4
             (1576.0, 1, (5, 7, 9, 12), (9, 12, 7, 9)))       # E
    for b0, bars, on_degs, off_degs in plans:
        for bar in range(bars):
            b = b0 + bar * 4
            for k in range(4):
                sc.note(cd.CH_RHYTHM, en.pitch(GTR_A, ION, on_degs[k]),
                        b + k, 0.95, 98 if k == 0 else 93, jt=3, jv=3)
                sc.note(cd.CH_WAH, en.pitch(GTR_A, ION, off_degs[k]),
                        b + k + 0.5, 0.95, 90, jt=3, jv=3)
    en.strum(sc, cd.CH_RHYTHM, [57, 61, 64, 69], 1580.0, 3.8, 100)
    en.strum(sc, cd.CH_WAH, [64, 69, 73, 76], 1580.0, 3.8, 96, down=False)


# ---------------------------------------------------------------------------
# Piano — high glitter arps (1-3-5-8 over two octaves, 16ths, RH only)
# ---------------------------------------------------------------------------
def _glitter_bar(sc, b, name=None, vel=76):
    name = name or ("A" if _block_is_A(b) else "E")
    pits = [en.pitch(PNO_A, ION, d) for d in _ARPS[name]]
    en.arp(sc, cd.CH_PIANO, pits, b, 16, 0.25, vel, "updown",
           gate=1.15, accent_every=4, accent=8)


def _glitter(sc):
    sc.note(cd.CH_PIANO, PNO_A, T0, 2.0, 100, jt=3)      # the tutti strike
    sc.note(cd.CH_PIANO, PNO_A + 12, T0, 2.0, 96, jt=3)
    for lo, hi in ((8, 16), (24, 32)):                   # 2 bars on, 2 off
        for bar in range(lo, hi):
            if bar % 4 in (0, 1):
                _glitter_bar(sc, T0 + bar * 4)
    for bar in range(32, 62):                            # 3 on, 1 off
        if bar % 4 != 3:
            _glitter_bar(sc, T0 + bar * 4)
    _glitter_bar(sc, 1564.0, "D", 74)                    # cadence sparkles
    _glitter_bar(sc, 1572.0, "Esus", 76)
    for i, d in enumerate(_ARPS["A"]):                   # final upward run
        sc.note(cd.CH_PIANO, en.pitch(PNO_A, ION, d), 1580.0 + i * 0.25,
                0.3, 88 + i, jt=2, jv=3)
    sc.note(cd.CH_PIANO, en.pitch(PNO_A, ION, 15), 1581.75, 2.1, 96, jt=2)


# ---------------------------------------------------------------------------
# Organ (full chords, Leslie fast) and pad (filter open, the final add9)
# ---------------------------------------------------------------------------
def _organ(sc):
    ch = cd.CH_ORGAN
    for blk in range(31):                     # 1312-1560, 8-beat blocks
        b = T0 + blk * 8
        pits = [57, 61, 64, 69] if blk % 2 == 0 else [56, 59, 62, 64]
        v = 92 + (3 if blk % 4 == 0 else 0)
        for i, p in enumerate(pits):
            sc.note(ch, p, b, 8.05, v - i, jt=4, jv=3)
    for b, pits, dur in ((1560.0, (50, 54, 57, 62), 8.0),     # D
                         (1568.0, (52, 57, 59, 64), 8.0),     # Esus4
                         (1576.0, (52, 56, 59, 64), 4.0),     # E
                         (1580.0, (57, 61, 64, 69), 3.85)):   # A
        for i, p in enumerate(pits):
            sc.note(ch, p, b, dur, 96 - i, jt=4, jv=3)


def _pad(sc):
    ch = cd.CH_PAD
    pcs_a, pcs_e = [57, 59, 61, 64], [56, 59, 62, 64]    # A add9 / E7
    # Split the bed at the second peal so every voice re-strikes the 1440
    # arrival — an arrival re-articulation, not one B4 tied for 248 beats.
    chords1 = [pcs_a if i % 2 == 0 else pcs_e for i in range(16)]   # 1312-1440
    en.pad_block(sc, ch, T0, chords1, 8.0, size=4, lo=55, hi=79, vel=58)
    chords2 = [pcs_a if i % 2 == 0 else pcs_e for i in range(15)]   # 1440-1560
    chords2 += [[50, 54, 57, 62], [52, 57, 59, 64]]      # D, Esus4 -> 1576
    en.pad_block(sc, ch, PEAL2, chords2, 8.0, size=4, lo=55, hi=79, vel=62)
    for p in (52, 56, 59, 64):                           # E resolution
        sc.note(ch, p, 1576.0, 3.85, 60, jt=4, jv=3)
    for i, p in enumerate((57, 64, 69, 71, 76)):         # A add9, rings to
        sc.note(ch, p, 1580.0, 20.0, 74 - i, jt=3, jv=2) # 1600 across M6


# ---------------------------------------------------------------------------
# Tubular bells — THE PEAL: THEME_A in double augmentation, twice
# ---------------------------------------------------------------------------
def _peal(sc):
    aug = [(d, s * 2.0, dur * 2.0) for d, s, dur in m.THEME_A]
    for t, v0 in ((T0, 103), (PEAL2, 106)):
        for deg, s, d in aug:
            v = v0 + (6 if deg >= 8 else 0) + (3 if s % 16.0 == 0 else 0)
            sc.note(cd.CH_BELLS, en.pitch(BELL_A, ION, deg), t + s, d * 0.9,
                    min(115, v), jt=3, jv=3)
    for deg, s, d in aug:                     # glock doubles the 2nd peal 8va
        sc.note(cd.CH_CRYSTAL, en.pitch(BELL_A, ION, deg) + 12, PEAL2 + s,
                d * 0.8, 90, jt=3, jv=3)
    for t, deg in ((1512.0, 1), (1528.0, 1), (1544.0, 5)):   # post-peal tolls
        sc.note(cd.CH_BELLS, en.pitch(BELL_A, ION, deg), t, 6.0, 102,
                jt=3, jv=3)
    # the final bell: A at 1583, ringing 16 beats across the full stop
    sc.note(cd.CH_BELLS, BELL_A, 1583.0, 16.0, 112, jt=0, jv=2)


# ---------------------------------------------------------------------------
# Strings + choir — THEME_C in octaves (same augmentation as the bells)
# ---------------------------------------------------------------------------
def _watch(sc):
    # THEME_C phrase by phrase (each 8-beat chorale phrase, augmented x2 to 16
    # beats), so each phrase can start -8 and recover across itself: the two
    # peal statements surge and recede instead of one flat crescendo.
    phrases = []
    for p in range(4):
        ph = [(d, (s - 8 * p) * 2.0, dur * 2.0)
              for d, s, dur in m.THEME_C if 8 * p <= s < 8 * (p + 1)]
        phrases.append((16.0 * p, ph))
    for t in (T0, PEAL2):
        for off, ph in phrases:
            en.line(sc, cd.CH_STRINGS, t + off, GTR_A, ION, ph, 89,
                    vel_end=97, gate=1.02, jt=4)
            en.line(sc, cd.CH_CHOIR, t + off, CHOIR_A, ION, ph, 85,
                    vel_end=93, gate=1.02, jt=4)
    rise = [(1, 0, 8), (2, 8, 8), (3, 16, 8), (5, 24, 8)]   # 1408 terrace
    en.line(sc, cd.CH_STRINGS, 1408.0, GTR_A, ION, rise, 84, vel_end=92,
            gate=1.02, jt=4)
    en.line(sc, cd.CH_CHOIR, 1408.0, CHOIR_A, ION, rise, 80, vel_end=88,
            gate=1.02, jt=4)
    holds = [(3, 0, 8), (2, 8, 8), (3, 16, 8), (2, 24, 8),  # 1504-1560
             (5, 32, 8), (5, 40, 8), (8, 48, 8)]
    en.line(sc, cd.CH_STRINGS, 1504.0, GTR_A, ION, holds, 90, vel_end=96,
            gate=1.0, jt=4)
    en.line(sc, cd.CH_CHOIR, 1504.0, CHOIR_A, ION, holds, 86, vel_end=92,
            gate=1.0, jt=4)
    # cadence: the sus4 held over E, resolving A -> G#, landing back on A
    cad = [(6, 0, 8), (8, 8, 6.5), (7, 14.5, 5.5), (8, 20, 3.8)]
    en.line(sc, cd.CH_STRINGS, CAD, GTR_A, ION, cad, 96, gate=1.0, jt=3)
    en.line(sc, cd.CH_CHOIR, CAD, CHOIR_A, ION, cad, 92, gate=1.0, jt=3)


# ---------------------------------------------------------------------------
# Lead + double — THEME_B answers and wails, real 3rds/6ths (no detune)
# ---------------------------------------------------------------------------
def _wail(sc, t, deg, dur, vel, scoop=1.2, harm=None, vib=0.3, throw=False):
    """A held answering note: scoop bend in, blooming vibrato, recentred."""
    lead = cd.CH_LEAD
    if scoop:
        sc.bend(lead, max(t - 0.02, T0 + 0.03), -scoop)
        en.bend_ramp(sc, lead, t + 0.02, t + 0.35, -scoop, 0.0, steps=8)
    sc.note(lead, en.pitch(LEAD_A, ION, deg), t, dur, vel, jt=3)
    en.vibrato(sc, lead, t, dur, depth=vib, delay=0.6)
    if harm is not None:                      # ch13: diatonic 3rd/6th below
        sc.note(cd.CH_DOUBLE, en.pitch(LEAD_A, ION, deg + harm), t, dur,
                vel - 10, jt=4)
    if throw:
        en.echo_throw(sc, lead, t + dur - 0.4, base=30, peak=92, release=2.2)


def _flare(sc, t, octave, vel, harm_shift):
    """THEME_B statement, ch13 harmonizing in diatonic 3rds/6ths."""
    en.line(sc, cd.CH_LEAD, t, LEAD_A, ION, m.THEME_B, vel, vel_end=vel + 6,
            octave=octave, gate=0.92, jt=4)
    en.line(sc, cd.CH_DOUBLE, t, LEAD_A, ION, m.THEME_B, vel - 11,
            vel_end=vel - 5, octave=octave, shift=harm_shift, gate=0.92, jt=5)
    en.echo_throw(sc, cd.CH_LEAD, t + 15.0, base=30, peak=90, release=2.5)


def _lead(sc):
    # the arrival scream on the tutti downbeat (no scoop: bend clean at 1312)
    _wail(sc, T0, 8, 2.5, 112, scoop=0, harm=-5, vib=0.35)
    # answers inside the first peal's long bell tones
    _wail(sc, 1316.5, 9, 3.0, 104, scoop=1.0, throw=True)
    _wail(sc, 1338.0, 9, 4.0, 106, scoop=1.2, harm=-2, throw=True)
    _wail(sc, 1353.0, 9, 5.0, 108, scoop=1.5, harm=-5, vib=0.35, throw=True)
    # between the peals: THEME_B front and centre
    _flare(sc, 1376.0, 0, 103, -2)            # 3rds below
    _wail(sc, 1396.0, 8, 3.0, 104, scoop=1.2, throw=True)
    _wail(sc, 1402.0, 10, 4.5, 107, scoop=1.5, harm=-2, throw=True)
    _flare(sc, 1408.0, 1, 105, -5)            # octave up, 6ths below
    # the sweep into the second peal (legato hammer-run, CC68 balanced)
    en.run(sc, cd.CH_LEAD, 1436.75, LEAD_A, ION,
           list(range(1, 14)), 0.25, 88, 112, legato=True)
    _wail(sc, PEAL2, 15, 3.5, 113, scoop=0, harm=-5, vib=0.4, throw=True)
    _wail(sc, 1466.0, 9, 4.0, 106, scoop=1.2, harm=-2, throw=True)
    _wail(sc, 1481.0, 12, 5.0, 110, scoop=1.5, harm=-2, vib=0.35, throw=True)
    # post-peal drive: the climactic statement and a falling wail sequence
    _flare(sc, 1504.0, 1, 107, -5)
    _wail(sc, 1522.0, 12, 3.0, 106, scoop=1.0, harm=-2)
    _wail(sc, 1526.0, 10, 3.0, 104, scoop=1.0, harm=-2)
    _wail(sc, 1530.0, 9, 4.0, 106, scoop=1.2, harm=-5, throw=True)
    _wail(sc, 1538.0, 8, 3.0, 104, scoop=1.0)
    _wail(sc, 1546.0, 9, 5.0, 108, scoop=1.2, harm=-2, vib=0.35, throw=True)
    # cadence: F# over D, the A suspension over E resolving to G#, then the
    # last high A (deg 15) with ch13 a diatonic 3rd below
    _wail(sc, CAD, 6, 7.0, 106, scoop=1.2, harm=-2, vib=0.35)
    _wail(sc, 1568.0, 8, 6.0, 110, scoop=1.0, vib=0.3)
    sc.note(cd.CH_DOUBLE, en.pitch(LEAD_A, ION, 5), 1568.0, 11.5, 96, jt=4)
    _wail(sc, 1574.5, 7, 5.3, 108, scoop=0, vib=0.35)
    _wail(sc, 1580.0, 15, 3.7, 115, scoop=2.0, harm=-2, vib=0.4, throw=True)


def build(sc):
    _controllers(sc)
    _breath(sc)
    _drums(sc)
    _bass(sc)
    _figuration(sc)
    _glitter(sc)
    _organ(sc)
    _pad(sc)
    _peal(sc)
    _watch(sc)
    _lead(sc)
