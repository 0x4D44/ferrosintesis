"""
folk.py — a folk/prog medley engine for the long-form piece *RIVERWAKE*
(in the spirit of Mike Oldfield's "Amarok": one unbroken, restless 60-minute river
of acoustic guitars, hand percussion, whistle, fiddle, bells and choir, forever
shifting key, tempo and mood and never quite repeating itself).

Built on ../engine.py (Score, voice-leading, scales, MIDI writer w/ tempo map,
analyzer). Adds:
  * a FIXED 16-channel acoustic orchestra (so timbres stay consistent across the hour)
  * percussion grooves on the GM drum channel (bodhran / congas / kit / shakers / fills)
  * idiomatic primitives: strum, interlocking picked guitars, riffs, runs, folk melody
  * ~13 SECTION generators (pastoral, folk-dance/jig, driving-prog, bells, ambient,
    percussion-jam, anthem, waltz, chase, chant, hush, transition, morse easter-egg)
  * a Medley assembler that chains sections with per-section tempo & key onto ONE
    continuous timeline and totals the running time in seconds.
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import (Score, Ctx, MODES, scale_pcs, deg_off, voice_chord,
                    pcs_in_band, write_midi, analyze, NAMES)

# ----------------------------------------------------------------------------
# The fixed orchestra (channel -> GM program, name). Channel 9 is GM percussion.
# ----------------------------------------------------------------------------
NYLON, STEEL, BANJO, BASS, GLOCK, BELLS, FLUTE, FIDDLE, ACCORD, DRUMS, \
    CHOIR, STRINGS, ORGAN, EGTR, PAN, MARIMBA = range(16)

ORCHESTRA = {
    NYLON:  (24, 'Nylon Guitar'),   STEEL:  (25, 'Steel Guitar'),
    BANJO:  (105, 'Banjo'),         BASS:   (32, 'Acoustic Bass'),
    GLOCK:  (9, 'Glockenspiel'),    BELLS:  (14, 'Tubular Bells'),
    FLUTE:  (73, 'Flute'),          FIDDLE: (110, 'Fiddle'),
    ACCORD: (21, 'Accordion'),      DRUMS:  (0, 'Drums'),
    CHOIR:  (52, 'Choir Aahs'),     STRINGS:(48, 'Strings'),
    ORGAN:  (19, 'Church Organ'),   EGTR:   (27, 'Clean Guitar'),
    PAN:    (75, 'Pan Flute'),      MARIMBA:(12, 'Marimba'),
}
# comfortable MIDI ranges per channel (lo, hi) to keep parts idiomatic
RANGE = {
    NYLON:(40,76), STEEL:(43,79), BANJO:(50,81), BASS:(28,52), GLOCK:(84,103),
    BELLS:(60,84), FLUTE:(62,93), FIDDLE:(55,89), ACCORD:(46,82), CHOIR:(48,77),
    STRINGS:(48,84), ORGAN:(36,84), EGTR:(40,84), PAN:(62,89), MARIMBA:(48,84),
}

# GM percussion note numbers
KICK, RIM, SNARE, CLAP, TOM_L, HHC, TOM_M, HHP, TOM_H, HHO = 36, 37, 38, 39, 45, 42, 47, 44, 50, 46
CRASH, RIDE, TAMB, COWBELL = 49, 51, 54, 56
BONGO_H, BONGO_L, CONGA_MH, CONGA_H, CONGA_L = 60, 61, 62, 63, 64
CLAVES, WOOD_H, WOOD_L, CABASA, MARACA, SHAKER, TRIANGLE = 75, 76, 77, 69, 70, 82, 81

BPB = 4   # working beats-per-bar (meter feels are made by rhythm, not the time-sig)


def program_all(sc):
    for ch, (prog, nm) in ORCHESTRA.items():
        sc.program(ch, prog, nm)


# ----------------------------------------------------------------------------
# Pitch / chord helpers (modal, folk)
# ----------------------------------------------------------------------------
def pcof(root, mode, degree):
    return (root + deg_off(mode, degree)) % 12

def triad(root, mode, degree):
    return [pcof(root, mode, degree), pcof(root, mode, degree + 2), pcof(root, mode, degree + 4)]

def seventh(root, mode, degree):
    return triad(root, mode, degree) + [pcof(root, mode, degree + 6)]

def degree_pitch(root, mode, degree, base):
    """MIDI pitch of a scale degree, with `base` = pitch of degree 1 (tonic)."""
    return base + deg_off(mode, degree)

def chord_in_band(pcs, lo, hi, n=4, prev=None):
    return voice_chord(pcs, prev, n, lo, hi)

def bass_pitch(root, mode, degree, lo=28, hi=52):
    pcs = [pcof(root, mode, degree)]
    cand = pcs_in_band(pcs, lo, hi)
    return cand[len(cand) // 2] if cand else 40


def env(local_beat, total_beats, a, b, breathe=0.0):
    """linear level a->b across a section + optional per-bar breathing hump."""
    t = 0.0 if total_beats <= 0 else local_beat / total_beats
    lvl = a + (b - a) * t
    if breathe:
        ph = (local_beat % BPB) / BPB
        lvl += breathe * math.sin(math.pi * ph)
    return max(0.0, min(1.0, lvl))

def vel(level, lo, hi, jit=5):
    return int(max(1, min(127, lo + (hi - lo) * level + random.randint(-jit, jit))))

def fold(p, lo, hi):
    """Octave-fold a pitch into [lo, hi] so parts stay in their instrument's range."""
    while p > hi:
        p -= 12
    while p < lo:
        p += 12
    return p


# ----------------------------------------------------------------------------
# Percussion grooves
# ----------------------------------------------------------------------------
# 1-bar patterns as {drum: [16th-slot indices]}  (sub=16 straight, sub=12 compound)
GROOVES = {
    'kit':    (16, {KICK:[0,6,8,14], SNARE:[4,12], HHC:[2,6,10,14], RIDE:[0,4,8,12]}),
    'rock':   (16, {KICK:[0,3,8,10], SNARE:[4,12], HHC:[2,6,10,14], RIDE:[0,4,8,12], HHO:[7,15]}),
    'folk':   (16, {KICK:[0,8], SNARE:[4,12], TAMB:[2,6,10,14], HHC:[0,4,8,12]}),
    'bodhran':(16, {TOM_L:[0,8], TOM_M:[4,12], WOOD_H:[2,6,10,14], KICK:[0,8], TRIANGLE:[0]}),
    'conga':  (16, {CONGA_L:[0,8], CONGA_H:[3,7,11,14], CONGA_MH:[5,13], CABASA:[2,6,10,14], CLAVES:[0,8]}),
    'jig':    (12, {KICK:[0,6], SNARE:[3,9], TAMB:[0,2,4,6,8,10], WOOD_H:[5,11], TRIANGLE:[0]}),  # 6/8 feel
    'reel':   (16, {KICK:[0,4,8,12], SNARE:[4,12], HHC:[2,6,10,14], TAMB:[0,8], HHO:[14]}),
    'shaker': (16, {SHAKER:[0,2,4,6,8,10,12,14], TAMB:[4,12], TRIANGLE:[0]}),
    'march':  (16, {KICK:[0,8], SNARE:[4,8,12], HHC:[2,6,10,14], RIDE:[0,4,8,12], CRASH:[0]}),
    'half':   (16, {KICK:[0], SNARE:[8], TAMB:[4,12], RIDE:[0,8]}),
    'tribal': (12, {TOM_L:[0,6], TOM_H:[3,9], CONGA_H:[1,4,7,10], CONGA_L:[0,6], COWBELL:[2,8]}),
}

def groove(sc, t0, bars, name, level=0.7, bpb=BPB, fill_last=False,
           crash_first=False, hum=8):
    sub, pat = GROOVES[name]
    step = bpb / sub
    for bar in range(bars):
        if fill_last and bar == bars - 1:
            _drum_fill(sc, t0 + bar * bpb, bpb, level)
            continue
        for drum, slots in pat.items():
            for s in slots:
                b = t0 + bar * bpb + s * step
                acc = 1.12 if (s == 0) else (1.0 if s % (sub // 2) == 0 else 0.82)
                v = vel(level * acc, 30, 118, jit=6)
                sc.note(DRUMS, drum, b, step * 0.9, v, max_jit=hum, dur_jit=2)
        if crash_first and bar == 0:
            sc.note(DRUMS, CRASH, t0, bpb * 0.5, vel(level, 60, 110), max_jit=4)

def _drum_fill(sc, t0, bpb, level):
    toms = [TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_L, SNARE, SNARE]
    step = bpb / len(toms)
    for i, d in enumerate(toms):
        sc.note(DRUMS, d, t0 + i * step, step * 0.95, vel(level + i * 0.02, 60, 118), max_jit=4)
    sc.note(DRUMS, CRASH, t0 + bpb, bpb * 0.5, vel(level, 70, 116), max_jit=3)


# ----------------------------------------------------------------------------
# Pitched primitives
# ----------------------------------------------------------------------------
def strum(sc, ch, beat, pitches, dur, v, down=True, roll=0.035, hum=4):
    seq = sorted(pitches) if down else sorted(pitches, reverse=True)
    for i, p in enumerate(seq):
        sc.note(ch, p, beat + i * roll, dur, max(1, v - i * 2), max_jit=hum)

def strum_pattern(sc, ch, t0, voicings, bars, level, bpb=BPB, pattern=None, lo=42, hi=92):
    """Rhythmic strumming over per-bar chord voicings. pattern = list of
    (beat_in_bar, down?, accent) — defaults to a folk down/up strum."""
    if pattern is None:
        pattern = [(0,True,1.1),(1,False,.8),(1.5,True,.9),(2,True,1.0),(3,False,.8),(3.5,True,.9)]
    for bar, v in enumerate(voicings):
        if not v:
            continue
        for (bt, down, acc) in pattern:
            b = t0 + bar * bpb + bt
            strum(sc, ch, b, v, (bpb - bt) * 0.5 if bt < 1 else 0.7,
                  vel(level * acc, lo, hi), down=down)

def picked(sc, ch, t0, voicings, bars, level, bpb=BPB, rate=8, pattern='updown',
           lo=34, hi=86, gate=1.1, jit=4):
    """A single picked-arpeggio guitar voice over per-bar voicings."""
    for bar, v in enumerate(voicings):
        if not v:
            continue
        seq = _arp_seq(v, pattern, rate)
        step = bpb / rate
        for k, p in enumerate(seq):
            b = t0 + bar * bpb + k * step
            sc.note(ch, p, b, step * gate, vel(level, lo, hi, jit), max_jit=3)

def interlock(sc, t0, root, mode, degrees, bars, level, bpb=BPB, rate=16,
              ch_a=NYLON, ch_b=STEEL, lo=46, hi=82):
    """Two guitars genuinely HOCKET — the Oldfield signature. Each plays a MOVING
    modal line (not one static chord echoed): A weaves up/down the scale from the
    bar's chord-root degree; B starts a third above with a rotating phase
    (3-against-4), so the lines truly interlock and change every bar."""
    step = bpb / rate
    base = root + 48
    SHAPE = [0, 1, 2, 3, 4, 3, 2, 1, 2, 4, 3, 1, 0, 2, 1, 3]   # a weaving contour
    for bar in range(bars):
        d0 = degrees[bar % len(degrees)]
        rot = (bar * 3) % len(SHAPE)         # 3-against-4 rotation per bar
        for k in range(rate):
            sa = SHAPE[k % len(SHAPE)]
            sb = SHAPE[(k + rot + 2) % len(SHAPE)] + 2     # B a third above, phase-shifted
            pa = fold(base + deg_off(mode, d0 + sa), lo, hi)
            pb = fold(base + deg_off(mode, d0 + sb), lo + 4, hi + 4)
            b = t0 + bar * bpb + k * step
            sc.note(ch_a, pa, b, step * 1.05, vel(level, 30, 80, 4), max_jit=3)
            sc.note(ch_b, pb, b + step * 0.5, step * 1.0, vel(level * 0.85, 28, 74, 4), max_jit=3)

def _arp_seq(v, pattern, rate):
    v = sorted(v)
    if pattern == 'up':
        base = v
    elif pattern == 'down':
        base = list(reversed(v))
    elif pattern == 'updown':
        base = v + list(reversed(v[1:-1])) if len(v) > 2 else v
    elif pattern == 'broken':
        lo, hi = v[0], v[-1]; mids = v[1:-1] or [v[0]]
        base = []; mi = 0
        while len(base) < rate:
            base += [lo, hi, mids[mi % len(mids)], hi]; mi += 1
    else:
        base = v
    out = []
    while len(out) < rate:
        out += base
    return out[:rate]

def bass_line(sc, t0, degrees, bars, root, mode, level, bpb=BPB, style='root5',
              lo=28, hi=50, jit=4):
    """Bass per bar from a degree list. styles: root5 (root+fifth), walk, drone, riff8."""
    for bar in range(bars):
        d = degrees[bar % len(degrees)]
        r = bass_pitch(root, mode, d, lo, hi)
        b0 = t0 + bar * bpb
        if style == 'drone':
            sc.note(BASS, r, b0, bpb * 0.98, vel(level, 40, 92, jit), max_jit=5)
        elif style == 'root5':
            sc.note(BASS, r, b0, bpb * 0.5, vel(level, 44, 96, jit), max_jit=4)
            fifth = bass_pitch(root, mode, d + 4, lo, hi)
            sc.note(BASS, fifth, b0 + 2, bpb * 0.45, vel(level * .9, 40, 88, jit), max_jit=4)
        elif style == 'walk':
            for k, dd in enumerate([d, d + 1, d + 2, d + 4]):
                sc.note(BASS, bass_pitch(root, mode, dd, lo, hi), b0 + k, 0.9,
                        vel(level, 40, 92, jit), max_jit=4)
        elif style == 'riff8':
            patt = [d, d, d + 4, d, d + 2, d, d + 4, d + 6]
            for k, dd in enumerate(patt):
                sc.note(BASS, bass_pitch(root, mode, dd, lo, hi), b0 + k * 0.5, 0.45,
                        vel(level * (1.1 if k % 2 == 0 else .8), 40, 96, jit), max_jit=3)


def folk_phrase(root, mode, bars, chords_deg, bpb=BPB, low=67, high=88,
                density=0.7, rest_prob=0.12, start_deg=5, motif=None):
    """Generate an organic folk melody (list of (semitone_off_from_tonic, start, dur))
    over a per-bar chord-degree list. Chord tones on strong beats, stepwise fill,
    occasional leaps and rests. If `motif` (a list of degrees) is given, the phrase
    opens by quoting it. Returns offsets relative to the TONIC pitch (caller adds base)."""
    notes = []
    cur = start_deg
    tb = (root % 12) + 60          # the ACTUAL tonic pitch play_melody() will use
    beat = 0.0
    total = bars * bpb
    mi = 0
    while beat < total - 0.01:
        bar = int(beat // bpb)
        cdeg = chords_deg[bar % len(chords_deg)]
        ctones = {cdeg % 7 or 7, (cdeg + 2 - 1) % 7 + 1, (cdeg + 4 - 1) % 7 + 1}
        strong = (abs((beat % bpb)) < 0.01) or (abs((beat % bpb) - 2) < 0.01)
        if motif and mi < len(motif) and bar == 0:
            cur = motif[mi]; mi += 1
            dur = 1.0
        else:
            if random.random() < rest_prob and not strong:
                beat += 0.5
                continue
            if strong:
                # land on a chord tone near current
                opts = [cdeg, cdeg + 2, cdeg + 4, cdeg - 3, cdeg + 7]
                cur = min(opts, key=lambda d: abs(d - cur) + (0 if (d - 1) % 7 + 1 in ctones else 3))
            else:
                step = random.choice([-2, -1, -1, 1, 1, 2, 3, -3])
                cur += step
            # keep in range
            while tb + deg_off(mode, cur) < low:  cur += 7
            while tb + deg_off(mode, cur) > high: cur -= 7
            dur = random.choice([0.5, 0.5, 1.0, 1.0, 1.5, 2.0]) if not strong else random.choice([1.0, 1.5, 2.0])
        dur = min(dur, total - beat)
        notes.append((deg_off(mode, cur), beat, dur))
        beat += dur
    return notes

def play_melody(sc, ch, t0, notes, tonic_pitch, level, lo=60, hi=104, gate=0.92, jit=6, max_jit=10):
    for (off, start, dur) in notes:
        sc.note(ch, tonic_pitch + off, t0 + start, dur * gate,
                vel(level, lo, hi, jit), max_jit=max_jit)

def pad_chords(sc, ch, t0, voicings, bars, level, bpb=BPB, lo=40, hi=84,
               legato=0.4, swell=True, cc_floor=36):
    """Sustained, tied chordal pad (choir/strings/organ) over per-bar voicings."""
    if not voicings:
        return
    nv = max(len(v) for v in voicings if v)
    for vi in range(nv):
        i = 0
        line = [(v[vi] if (v and vi < len(v)) else None) for v in voicings]
        while i < len(line):
            p = line[i]
            if p is None:
                i += 1; continue
            j = i
            while j + 1 < len(line) and line[j + 1] == p:
                j += 1
            start = t0 + i * bpb; end = t0 + (j + 1) * bpb
            nxt = line[j + 1] if j + 1 < len(line) else None
            dur = (end - start) + (legato if (nxt is not None and nxt != p) else 0.0)
            sc.note(ch, p, start, dur, vel(level, lo, hi, 4), max_jit=5)
            i = j + 1
    if swell:
        for k in range(bars * bpb + 1):
            b = t0 + k
            lv = env(k, bars * bpb, level, level, breathe=0.06)
            sc.cc(ch, 11, int(cc_floor + (127 - cc_floor) * lv), b)


def bells_motif(sc, ch, t0, degrees, root, mode, base, level, bpb=BPB,
                durs=None, lo=60, hi=96, jit=4):
    """A stately bell/glock statement of a degree sequence (one per beat by default)."""
    b = t0
    for k, d in enumerate(degrees):
        du = (durs[k] if durs else 1.0)
        sc.note(ch, degree_pitch(root, mode, d, base), b, du * 0.95,
                vel(level, lo, hi, jit), max_jit=4)
        b += du

def morse(sc, t0, text, level=0.5, ch=DRUMS, drum=WOOD_H, dit=0.18):
    """Easter-egg: tap a word in Morse on a high woodblock (homage to Amarok's
    hidden message). Returns beats consumed."""
    CODE = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.',
            'H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.',
            'O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-',
            'V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',' ':'/'}
    b = t0
    for chx in text.upper():
        c = CODE.get(chx, '')
        if c == '/':
            b += dit * 4; continue
        for sym in c:
            ln = dit if sym == '.' else dit * 3
            sc.note(ch, drum, b, ln * 0.9, vel(level, 50, 96), max_jit=2)
            b += ln + dit
        b += dit * 2
    return b - t0


# ----------------------------------------------------------------------------
# Chord-progression voicings helper
# ----------------------------------------------------------------------------
def voicings_for(root, mode, degrees, bars, lo, hi, n=4):
    """Per-bar 4-note voicings, voice-led, from a repeating degree list."""
    out, prev = [], None
    for bar in range(bars):
        d = degrees[bar % len(degrees)]
        prev = voice_chord(triad(root, mode, d), prev, n, lo, hi)
        out.append(prev)
    return out


# ----------------------------------------------------------------------------
# SECTION GENERATORS  — each writes onto sc from t0, returns beats consumed.
# Common kwargs: root (pc 0-11), mode, bars, bpb, lvl=(start,end), prog (degrees),
#                motif (degree list to quote), seed (int).
# ----------------------------------------------------------------------------
def _lvl(lvl, lb, beats):
    return env(lb, beats, lvl[0], lvl[1])

def sec_pastoral(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.35,0.5), motif=None):
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 50, 79)
    # interlocking nylon+steel arpeggios, gentle
    for bar in range(bars):
        lb = bar * bpb
        L = _lvl(lvl, lb, beats)
        picked(sc, NYLON, t0 + lb, [vw[bar]], 1, L * 0.9, bpb, rate=8, pattern='updown', lo=40, hi=72)
        picked(sc, STEEL, t0 + lb, [[p + 12 for p in vw[bar][:3]]], 1, L * 0.7, bpb, rate=8, pattern='broken', lo=52, hi=82)
    bass_line(sc, t0, prog, bars, root, mode, _lvl(lvl,beats/2,beats), bpb, style='root5')
    pad_chords(sc, STRINGS, t0, vw, bars, _lvl(lvl, beats/2, beats)*0.6, bpb, 50, 80)
    # whistle melody over the second half
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 70, 90, motif=motif)
    play_melody(sc, FLUTE, t0 + beats*0.0, notes, tonic, _lvl(lvl, beats*0.7, beats), 64, 96)
    return beats

def sec_folk_dance(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.6,0.85), motif=None, jiggy=True):
    beats = bars * bpb
    gname = 'jig' if jiggy else 'reel'
    groove(sc, t0, bars, gname, level=lvl[1]*0.9, bpb=bpb, fill_last=True, crash_first=True)
    vw = voicings_for(root, mode, prog, bars, 48, 78)
    strum_pattern(sc, BANJO, t0, vw, bars, lvl[1], bpb, lo=50, hi=88)
    strum_pattern(sc, NYLON, t0, vw, bars, lvl[1]*0.8, bpb,
                  pattern=[(0,True,1.0),(1,True,.9),(2,True,1.0),(3,True,.9)], lo=44, hi=80)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='riff8')
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 67, 90, density=0.85, rest_prob=0.06, motif=motif)
    play_melody(sc, FIDDLE, t0, notes, tonic, lvl[1], 62, 98, gate=0.9)
    # accordion comps on offbeats
    for bar in range(bars):
        for bt in (1, 3):
            strum(sc, ACCORD, t0 + bar*bpb + bt, vw[bar], 0.8, vel(lvl[1]*.7, 50, 86))
    return beats

def sec_driving(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.7,0.95), motif=None):
    beats = bars * bpb
    groove(sc, t0, bars, 'rock', level=lvl[1], bpb=bpb, fill_last=True, crash_first=True)
    vw = voicings_for(root, mode, prog, bars, 46, 78)
    interlock(sc, t0, root, mode, prog, bars, lvl[1]*0.8, bpb, rate=16)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='riff8')
    pad_chords(sc, ORGAN, t0, vw, bars, lvl[1]*0.5, bpb, 42, 78)
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 70, 93, density=0.8, rest_prob=0.08, motif=motif)
    play_melody(sc, EGTR, t0, notes, tonic, lvl[1], 64, 100, gate=0.95)
    return beats

def sec_bells(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.4,0.6), motif=None):
    beats = bars * bpb
    base = root + 60
    seq = (motif or [1,3,5,8,5,3,2,1])
    durs = [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
    # bells state the motif slowly, glock answers an octave up
    b = t0
    for bar in range(bars):
        m = [seq[(bar + i) % len(seq)] for i in range(4)]
        bells_motif(sc, BELLS, b, m, root, mode, base, _lvl(lvl, bar*bpb, beats), bpb,
                    durs=[1.0]*4, lo=58, hi=86)
        if bar % 2 == 1:
            bells_motif(sc, GLOCK, b, m, root, mode, base+12, _lvl(lvl, bar*bpb, beats)*0.7, bpb,
                        durs=[1.0]*4, lo=84, hi=104)
        b += bpb
    vw = voicings_for(root, mode, prog, bars, 48, 78)
    pad_chords(sc, STRINGS, t0, vw, bars, _lvl(lvl, beats/2, beats)*0.6, bpb, 48, 80)
    bass_line(sc, t0, prog, bars, root, mode, _lvl(lvl, beats/2, beats)*0.8, bpb, style='drone')
    return beats

def sec_ambient(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.18,0.34), motif=None):
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 50, 81)
    pad_chords(sc, CHOIR, t0, vw, bars, lvl[1]*0.8, bpb, 50, 79, swell=True)
    pad_chords(sc, STRINGS, t0, [[p-12 for p in v] for v in vw], bars, lvl[1]*0.6, bpb, 40, 72)
    pad_chords(sc, ORGAN, t0, vw, bars, lvl[1]*0.4, bpb, 44, 76)
    # sparse glock droplets
    base = root + 72
    for bar in range(bars):
        if random.random() < 0.7:
            d = random.choice([1,3,5,8])
            sc.note(GLOCK, degree_pitch(root, mode, d, base), t0 + bar*bpb + random.choice([0,2]),
                    2.0, vel(lvl[1]*0.6, 70, 96), max_jit=8)
    return beats

def sec_perc_jam(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.6,0.9), motif=None):
    beats = bars * bpb
    groove(sc, t0, bars, 'tribal', level=lvl[1], bpb=bpb)
    groove(sc, t0, bars, 'conga', level=lvl[1]*0.8, bpb=bpb)
    # marimba ostinato (interlocking with itself)
    base = root + 60
    pat = (motif or [1,5,8,5,3,5,8,10])
    step = bpb / 8
    for bar in range(bars):
        for k in range(8):
            d = pat[(bar*3 + k) % len(pat)]
            sc.note(MARIMBA, degree_pitch(root, mode, d, base), t0 + bar*bpb + k*step, step*1.1,
                    vel(_lvl(lvl, bar*bpb, beats)*(1.1 if k%2==0 else .8), 56, 100), max_jit=3)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='riff8')
    # answering kalimba-ish glock figures (folded into the glockenspiel's range)
    for bar in range(bars):
        if bar % 2 == 0:
            for k in range(4):
                d = pat[(k*2) % len(pat)]
                p = fold(degree_pitch(root, mode, d, base + 12), 84, 103)
                sc.note(GLOCK, p, t0+bar*bpb+k+0.5, .6, vel(lvl[1]*0.6, 80, 102), max_jit=4)
    return beats

def sec_anthem(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.8,1.0), motif=None):
    beats = bars * bpb
    groove(sc, t0, bars, 'march', level=lvl[1], bpb=bpb, fill_last=True, crash_first=True)
    vw = voicings_for(root, mode, prog, bars, 46, 82)
    strum_pattern(sc, NYLON, t0, vw, bars, lvl[1], bpb, lo=46, hi=84)
    strum_pattern(sc, STEEL, t0, [[p+12 for p in v[:3]] for v in vw], bars, lvl[1]*0.8, bpb, lo=58, hi=92)
    pad_chords(sc, CHOIR, t0, vw, bars, lvl[1]*0.85, bpb, 50, 79)
    pad_chords(sc, STRINGS, t0, vw, bars, lvl[1]*0.7, bpb, 48, 84)
    pad_chords(sc, ORGAN, t0, [[p-12 for p in v] for v in vw], bars, lvl[1]*0.6, bpb, 40, 74)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='root5')
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 74, 95, density=0.7, rest_prob=0.1, motif=motif)
    play_melody(sc, FLUTE, t0, notes, tonic, lvl[1], 70, 100)
    play_melody(sc, FIDDLE, t0, notes, tonic-12, lvl[1]*0.8, 58, 90)
    return beats

def sec_waltz(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.45,0.6), motif=None):
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 50, 80)
    # 3-feel: bass on 1, chords on 2 & 3 (within 4/4 grid, group of 3 then a lift)
    for bar in range(bars):
        b0 = t0 + bar*bpb
        L = _lvl(lvl, bar*bpb, beats)
        d = prog[bar % len(prog)]
        sc.note(BASS, bass_pitch(root, mode, d), b0, 0.9, vel(L, 42, 88), max_jit=4)
        for bt in (1, 2):
            strum(sc, ACCORD, b0+bt, vw[bar], 0.8, vel(L*.8, 52, 86))
            strum(sc, NYLON, b0+bt, vw[bar][:3], 0.7, vel(L*.7, 48, 80))
        sc.note(BASS, bass_pitch(root, mode, d+4), b0+3, .9, vel(L*.8, 40, 84), max_jit=4)
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 69, 90, density=0.6, motif=motif)
    play_melody(sc, ACCORD, t0, notes, tonic, lvl[1], 60, 92, gate=0.9)
    return beats

def sec_chase(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.65,0.92), motif=None):
    beats = bars * bpb
    groove(sc, t0, bars, 'reel', level=lvl[1], bpb=bpb, fill_last=True)
    vw = voicings_for(root, mode, prog, bars, 48, 80)
    interlock(sc, t0, root, mode, prog, bars, lvl[1]*0.85, bpb, rate=16, ch_a=NYLON, ch_b=BANJO)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='walk')
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 72, 94, density=0.9, rest_prob=0.05, motif=motif)
    play_melody(sc, PAN, t0, notes, tonic, lvl[1], 66, 98, gate=0.85)
    return beats

def sec_chant(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.6,0.85), motif=None):
    beats = bars * bpb
    groove(sc, t0, bars, 'bodhran', level=lvl[1]*0.9, bpb=bpb)
    groove(sc, t0, bars, 'shaker', level=lvl[1]*0.6, bpb=bpb)
    seq = (motif or [1,1,5,1,3,1])
    # Real call-and-response: the choir CALLS a distinct (voice-led, 3 DISTINCT tones)
    # chord on the strong syllables; a low organ ANSWERS underneath on the offbeats —
    # so the i/VI/iv progression is actually audible, not collapsed to a bare octave.
    prev = None
    for bar in range(bars):
        b0 = t0 + bar*bpb
        voi = voice_chord(triad(root, mode, prog[bar % len(prog)]), prev, 3, 48, 79)
        prev = voi
        dur = (bpb/len(seq)) * 0.9
        L = _lvl(lvl, bar*bpb, beats)
        for k, d in enumerate(seq):
            bt = k * (bpb/len(seq))
            if k % 2 == 0:                      # CALL — choir
                for p in voi:
                    sc.note(CHOIR, p, b0+bt, dur, vel(L*(1.05 if k==0 else .9), 46, 84), max_jit=6)
            else:                                # RESPONSE — low organ, an octave under
                for p in voi:
                    sc.note(ORGAN, p-12, b0+bt, dur, vel(L*0.8, 44, 80), max_jit=6)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1], bpb, style='drone')
    return beats

def sec_hush(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.12,0.22), motif=None):
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 52, 80)
    for bar in range(bars):
        picked(sc, NYLON, t0+bar*bpb, [vw[bar]], 1, _lvl(lvl,bar*bpb,beats), bpb, rate=4, pattern='up', lo=44, hi=74)
    pad_chords(sc, STRINGS, t0, vw, bars, lvl[1]*0.7, bpb, 50, 78)
    tonic = root + 60
    notes = folk_phrase(root, mode, bars, prog, bpb, 70, 86, density=0.4, rest_prob=0.3, motif=motif)
    play_melody(sc, PAN, t0, notes, tonic, lvl[1], 64, 88, gate=0.8)
    return beats

def sec_transition(sc, t0, *, root, mode, bars, prog, bpb=BPB, lvl=(0.4,0.7), motif=None, to_root=None):
    """Short connective tissue: a rolling fill + a pivot chord that leans toward the
    next key. Keeps motion alive between contrasting sections."""
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 48, 80)
    interlock(sc, t0, root, mode, prog, bars, lvl[1]*0.7, bpb, rate=16)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1]*0.8, bpb, style='walk')
    groove(sc, t0, bars, 'half', level=lvl[1]*0.7, bpb=bpb, fill_last=True)
    return beats


def sec_theme(sc, t0, *, root, mode, bars, prog, theme, bpb=BPB, lvl=(0.5,0.8),
              lead=FLUTE, octave=0, full=False):
    """A clear STATEMENT of a recurring theme (list of (degree, dur_beats)), looped/
    developed to fill `bars`, over a warm harmonisation. `full`=True thickens it."""
    beats = bars * bpb
    vw = voicings_for(root, mode, prog, bars, 48, 80)
    pad_chords(sc, STRINGS, t0, vw, bars, lvl[1]*0.6, bpb, 48, 82)
    if full:
        pad_chords(sc, CHOIR, t0, vw, bars, lvl[1]*0.55, bpb, 50, 78)
        pad_chords(sc, ORGAN, t0, [[p-12 for p in v] for v in vw], bars, lvl[1]*0.45, bpb, 40, 74)
        groove(sc, t0, bars, 'march', level=lvl[1]*0.8, bpb=bpb, fill_last=True, crash_first=True)
    bass_line(sc, t0, prog, bars, root, mode, lvl[1]*0.9, bpb, style='root5')
    for bar in range(bars):
        picked(sc, NYLON, t0+bar*bpb, [vw[bar]], 1, _lvl(lvl,bar*bpb,beats)*0.7, bpb,
               rate=8, pattern='broken', lo=44, hi=76)
    if not full:                       # quiet motion enters in the back half
        half = bars // 2
        groove(sc, t0 + half*bpb, bars - half, 'shaker', level=lvl[1]*0.5, bpb=bpb)
    # The theme DEVELOPS: each successive pass takes a different lead voice/register,
    # and harmony doublings accrue — so a long statement evolves, never just loops.
    base = root + 60
    LEADS = [lead, FIDDLE, GLOCK, PAN, lead]
    b = t0; idx = 0; pas = 0
    while b < t0 + beats - 0.01:
        if idx % len(theme) == 0:
            pas += 1
        cur = lead if pas == 1 else LEADS[pas % len(LEADS)]
        oc = octave + (1 if cur in (GLOCK,) else 0)          # glock sparkles up high
        deg, du = theme[idx % len(theme)]
        du = min(du, t0 + beats - b)
        p = base + deg_off(mode, deg) + 12 * oc
        if cur == FIDDLE and p > 88:
            p -= 12
        sc.note(cur, p, b, du * 0.94, vel(_lvl(lvl, b - t0, beats), 66, 102, 5), max_jit=9)
        # a third-above harmony joins on later passes (and always in full mode)
        if full or pas >= 3:
            hp = base + deg_off(mode, deg + 2) + 12 * octave
            harm = FIDDLE if cur != FIDDLE else FLUTE
            if harm == FIDDLE and hp < 55:
                hp += 12
            sc.note(harm, hp, b, du * 0.9, vel(_lvl(lvl, b - t0, beats) * 0.7, 54, 90, 5), max_jit=9)
        b += du; idx += 1
    return beats


SECTIONS = {
    'pastoral': sec_pastoral, 'folk_dance': sec_folk_dance, 'driving': sec_driving,
    'bells': sec_bells, 'ambient': sec_ambient, 'perc_jam': sec_perc_jam,
    'anthem': sec_anthem, 'waltz': sec_waltz, 'chase': sec_chase, 'chant': sec_chant,
    'hush': sec_hush, 'transition': sec_transition, 'theme': sec_theme,
}


# ----------------------------------------------------------------------------
# Medley assembler
# ----------------------------------------------------------------------------
class Medley:
    def __init__(self, start_bpm=96):
        self.ctx = Ctx(bpm=start_bpm, root='D', mode='dorian', beats_per_bar=BPB)
        self.sc = Score(self.ctx)
        program_all(self.sc)
        self.cursor = 0.0          # beats
        self.seconds = 0.0
        self.bpm = start_bpm
        self.log = []

    def at_bpm(self, bpm):
        if abs(bpm - self.bpm) > 1e-6:
            self.sc.tempo(self.cursor, bpm)
            self.bpm = bpm

    def add(self, kind, *, bpm, root, mode, bars, **kw):
        self.at_bpm(bpm)
        gen = SECTIONS[kind]
        beats = gen(self.sc, self.cursor, root=root if isinstance(root, int) else _PC[root],
                    mode=mode, bars=bars, **kw)
        secs = beats * 60.0 / bpm
        self.log.append((kind, _name(root), mode, bpm, bars, round(secs, 1), round(self.seconds, 1)))
        self.cursor += beats
        self.seconds += secs
        return self

    def gap(self, secs):
        """Insert silence (for a false ending). Advances time without notes."""
        beats = secs * self.bpm / 60.0
        self.cursor += beats
        self.seconds += secs
        return self

    def advance(self, beats):
        self.cursor += beats
        self.seconds += beats * 60.0 / self.bpm
        return self

    def morse(self, text, *, bpm=None, level=0.45, drone=None):
        """Tap a word in Morse on a high woodblock (Amarok homage). If `drone`=(root,mode)
        a soft sustained organ+strings tonic chord underlays it (and bleeds into the next
        section) so there is no dead hole before the Hymn. Advances time."""
        if bpm:
            self.at_bpm(bpm)
        t = self.cursor
        beats = morse(self.sc, t, text, level=level)
        if drone:
            dr, dm = (drone[0] if isinstance(drone[0], int) else _PC[drone[0]]), drone[1]
            voi = voice_chord(triad(dr, dm, 1), None, 3, 50, 74)
            span = beats + 5
            for p in voi:
                self.sc.note(STRINGS, p, t, span, 40, max_jit=5)
            self.sc.note(ORGAN, (dr % 12) + 36, t, span, 44, max_jit=4)
            self.sc.note(BASS, (dr % 12) + 36, t, span, 40, max_jit=4)
        self.log.append(('morse:' + text, '-', '-', self.bpm, 0, round(beats*60/self.bpm,1), round(self.seconds,1)))
        return self.advance(beats + 2)

    def crash_cadence(self, *, root, mode, bpm, beats=4, level=0.95):
        """A grand tutti tonic chord that RINGS then stops dead — the dramatic
        approach to the false-ending silence (something big, not a thin fill)."""
        root = root if isinstance(root, int) else _PC[root]
        self.at_bpm(bpm)
        t = self.cursor
        voi = voice_chord(triad(root, mode, 1), None, 5, 46, 84)
        for p in voi:
            self.sc.note(STRINGS, p, t, beats, vel(level, 70, 110), max_jit=4)
            self.sc.note(CHOIR, p, t, beats, vel(level*0.9, 64, 100), max_jit=4)
            strum(self.sc, NYLON, t, [p], beats, vel(level, 70, 108))
        self.sc.note(ORGAN, (root % 12) + 36, t, beats, vel(level, 64, 100), max_jit=3)
        self.sc.note(BASS, (root % 12) + 36, t, beats, vel(level, 70, 108), max_jit=3)
        self.sc.note(BELLS, degree_pitch(root, mode, 1, root + 60), t, beats, vel(level, 70, 104), max_jit=3)
        self.sc.note(DRUMS, CRASH, t, beats, vel(level, 90, 118), max_jit=2)
        self.sc.note(DRUMS, KICK, t, 0.5, vel(level, 90, 118), max_jit=2)
        self.log.append(('crash_cadence', _name(root), mode, bpm, 0, round(beats*60/bpm,1), round(self.seconds,1)))
        return self.advance(beats)

    def final_chord(self, *, root, mode, bpm, length_beats=12):
        """A long, luminous closing chord that blooms and fades, then a single bell."""
        root = root if isinstance(root, int) else _PC[root]
        self.at_bpm(bpm)
        t = self.cursor
        voi = voice_chord(triad(root, mode, 1), None, 5, 48, 84)
        for p in voi:
            self.sc.note(STRINGS, p, t, length_beats, 64, max_jit=6)
            self.sc.note(CHOIR, p, t, length_beats, 54, max_jit=6)
        self.sc.note(ORGAN, (root % 12) + 36, t, length_beats, 58, max_jit=4)
        self.sc.note(BASS, (root % 12) + 36, t, length_beats, 54, max_jit=4)
        self.sc.note(BELLS, degree_pitch(root, mode, 1, root + 60), t, length_beats, 70, max_jit=4)
        self.sc.note(GLOCK, degree_pitch(root, mode, 8, root + 72), t + 1.0, length_beats - 1, 60, max_jit=4)
        for ch in (STRINGS, CHOIR, ORGAN, BASS):
            for k in range(13):
                self.sc.cc(ch, 11, max(2, int(80 * (1 - k/12)) + 6), t + k * (length_beats/12.0))
        self.log.append(('final_chord', _name(root), mode, bpm, 0, round(length_beats*60/bpm,1), round(self.seconds,1)))
        return self.advance(length_beats + 2)

    def write(self, path, title='Riverwake', text=''):
        return write_midi(self.sc, path, title=title, text=text, key='Dm')


_PC = {'C':0,'C#':1,'Db':1,'D':2,'Eb':3,'E':4,'F':5,'F#':6,'G':7,'Ab':8,'A':9,'Bb':10,'B':11}
def _name(r):
    return r if isinstance(r, str) else NAMES[r % 12]
