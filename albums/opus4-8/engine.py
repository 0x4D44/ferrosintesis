"""
engine.py — a small neo-classical composition engine for the album *Vigil*.

Everything the twelve tracks share: pitch/scale theory, voice-leading, a humanised
event Score, a dynamic Arc (the long emotional swell + per-bar "breathing"), and a
set of idiomatic building blocks —

    tied_line   one sustained, tied voice (held common tones are NOT re-bowed)
    pad         a voice-led string chord bed built from tied_lines
    bass        the (often descending) bass, sustained or detached
    arpeggiate  Glass-style broken-chord figuration (up / down / updown / broken)
    ostinato    a repeating rhythmic cell for rapid / motoric movement
    melody      a singing theme over the harmony
    piano_chords gently broken piano with sustain-pedal blur
    expression  one coherent CC11 "bow swell" envelope per channel

plus a type-1 MIDI writer (with optional tempo map for rubato/ritardando) and an
`analyze()` validator. See tracks/01_of_the_light_that_stays.py for a worked example
that uses the whole API.

General MIDI is the target; the default sound is a serviceable preview — route through
an orchestral library for the intended result.
"""

import os
import math
import random
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

TPB = 480  # ticks per beat

# ----------------------------------------------------------------------------
# Pitch / scale theory
# ----------------------------------------------------------------------------
PC = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'Fb':4,'F':5,'E#':5,
      'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11}
NAMES = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']

MODES = {
    'ionian':         [0,2,4,5,7,9,11], 'major': [0,2,4,5,7,9,11],
    'dorian':         [0,2,3,5,7,9,10],
    'phrygian':       [0,1,3,5,7,8,10],
    'lydian':         [0,2,4,6,7,9,11],
    'mixolydian':     [0,2,4,5,7,9,10],
    'aeolian':        [0,2,3,5,7,8,10], 'minor': [0,2,3,5,7,8,10],
    'harmonic_minor': [0,2,3,5,7,8,11],
    'melodic_minor':  [0,2,3,5,7,9,11],
    'locrian':        [0,1,3,5,6,8,10],
}


def pc(name):
    return PC[name] if isinstance(name, str) else name % 12


def scale_pcs(root, mode):
    r = pc(root)
    return [(r + iv) % 12 for iv in MODES[mode]]


def deg_off(mode, degree):
    """Semitone offset above the tonic for a 1-based scale degree.
    Degrees may be <1 or >7 to reach other octaves (e.g. 8 = octave, 0/-1 below)."""
    ivs = MODES[mode]
    n = len(ivs)
    d = degree - 1
    return ivs[d % n] + 12 * (d // n)


def chord(*names):
    """Pitch-class list from note names, e.g. chord('D','F','A')."""
    return [PC[x] for x in names]


def theme_from_degrees(mode, items):
    """(degree, start_beat, dur_beats) -> (semitone_offset, start, dur)."""
    return [(deg_off(mode, d), s, du) for (d, s, du) in items]


# ----------------------------------------------------------------------------
# Voice leading
# ----------------------------------------------------------------------------
def pcs_in_band(pcs, lo, hi):
    s = set(p % 12 for p in pcs)
    out = [p for p in range(lo, hi + 1) if p % 12 in s]
    if not out:
        out = [p for p in range(lo - 12, hi + 13) if p % 12 in s]
    return out


def voice_chord(pcs, prev, n, lo, hi):
    """Voice `pcs` with `n` notes in [lo,hi], close to the previous voicing
    (keeps common tones, moves others minimally -> natural suspensions)."""
    pool = pcs_in_band(pcs, lo, hi)
    if prev is None:
        if n == 1:
            return [min(pool, key=lambda p: abs(p - (lo + hi) // 2))]
        targets = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
        out, avail = [], list(pool)
        for t in targets:                       # de-dup: pick DISTINCT chord tones
            best = min(avail, key=lambda p: abs(p - t))
            out.append(best)
            if len(avail) > 1:
                avail.remove(best)
        return sorted(out)
    out, avail = [], list(pool)
    for v in prev:
        best = min(avail, key=lambda p: abs(p - v))
        out.append(best)
        if len(avail) > 1:
            avail.remove(best)
    return sorted(out)


def nearest_above(pitch_pc, floor):
    p = floor
    while p % 12 != pc(pitch_pc):
        p += 1
    return p


# ----------------------------------------------------------------------------
# Context & Score
# ----------------------------------------------------------------------------
class Ctx:
    def __init__(self, bpm, root, mode, tpb=TPB, beats_per_bar=4):
        self.bpm = bpm
        self.root = pc(root)
        self.mode = mode
        self.tpb = tpb
        self.bpb = beats_per_bar
        self.scale = scale_pcs(root, mode)
        self.sec_per_beat = 60.0 / bpm

    def deg(self, degree, base):
        """MIDI pitch of a scale degree, with `base` = the pitch of degree 1."""
        return base + deg_off(self.mode, degree)


class Score:
    """Collect humanised note/CC events per channel; serialise later."""
    def __init__(self, ctx):
        self.ctx = ctx
        self.ev = {}                 # ch -> [(tick, order, Message)]
        self.names = {}              # ch -> instrument name
        self.tempo_changes = []      # [(beat, bpm)] optional rubato

    def _ch(self, ch):
        self.ev.setdefault(ch, [])

    def program(self, ch, prog, name=''):
        self._ch(ch)
        self.names[ch] = name
        self.ev[ch].append((0, 0, Message('program_change', program=prog, channel=ch)))

    def tempo(self, beat, bpm):
        self.tempo_changes.append((beat, bpm))

    def note(self, ch, pitch, start, dur, vel, humanize=True, max_jit=12, dur_jit=None):
        self._ch(ch)
        pitch = int(max(0, min(127, round(pitch))))
        vel = int(max(1, min(127, vel)))
        st = int(round(start * self.ctx.tpb))
        d = int(round(dur * self.ctx.tpb))
        if humanize:
            st += random.randint(-max_jit, max_jit)
            dj = max_jit if dur_jit is None else dur_jit
            d += random.randint(-dj, dj)
        st = max(0, st)
        d = max(self.ctx.tpb // 12, d)
        self.ev[ch].append((st, 3, Message('note_on', note=pitch, velocity=vel, channel=ch)))
        self.ev[ch].append((st + d, 1, Message('note_off', note=pitch, velocity=0, channel=ch)))

    def cc(self, ch, control, value, beat):
        self._ch(ch)
        t = int(round(beat * self.ctx.tpb))
        self.ev[ch].append((max(0, t), 2,
                            Message('control_change', control=control,
                                    value=int(max(0, min(127, value))), channel=ch)))

    def _resolve_overlaps(self):
        """Truncate same-pitch overlaps before serializing the score."""
        for events in self.ev.values():
            on_ticks = {}
            off_indices = {}
            for i, (tick, _order, msg) in enumerate(events):
                if msg.type == 'note_on' and msg.velocity > 0:
                    on_ticks.setdefault(msg.note, []).append(tick)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    off_indices.setdefault(msg.note, []).append(i)
            for pitch, starts in on_ticks.items():
                indices = off_indices.get(pitch, [])
                if len(indices) != len(starts):
                    continue
                starts.sort()
                indices.sort(key=lambda i: events[i][0])
                for start, index in zip(starts[1:], indices):
                    if events[index][0] > start:
                        events[index] = (start, events[index][1], events[index][2])


# ----------------------------------------------------------------------------
# Dynamic Arc — the long emotional swell + per-bar breathing
# ----------------------------------------------------------------------------
class Arc:
    """sections: list of (name, n_bars, level_start, level_end), levels in 0..1.
    level() interpolates within a section and adds a gentle per-bar hump so
    sustained strings rise and fall like a bow rather than sitting flat."""
    def __init__(self, sections, beats_per_bar=4, breathe=0.05):
        self.sections = sections
        self.bpb = beats_per_bar
        self.breathe = breathe
        self.total_bars = sum(s[1] for s in sections)
        self.total_beats = self.total_bars * beats_per_bar

    def level(self, beat):
        bar = beat / self.bpb
        acc = 0.0
        base = self.sections[-1][3]
        for (_nm, n, a, b) in self.sections:
            if bar < acc + n:
                base = a + (b - a) * ((bar - acc) / n)
                break
            acc += n
        ph = (beat % self.bpb) / self.bpb
        return max(0.0, min(1.0, base + self.breathe * math.sin(math.pi * ph)))

    def vel(self, beat, lo, hi):
        return int(lo + (hi - lo) * self.level(beat))

    def cc11(self, beat, floor=34):
        return int(floor + (127 - floor) * self.level(beat))


# ----------------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------------
def tied_line(sc, ch, t0, pitches, bar_len, arc, vlo, vhi, legato=0.30, max_jit=6):
    """One sustained voice from a per-bar pitch list (None = silent bar). Consecutive
    equal pitches are TIED into a single note; a short legato tail is added only when
    the next bar is a *different* sounding pitch (never into silence or a repeat)."""
    N = len(pitches)
    i = 0
    while i < N:
        p = pitches[i]
        if p is None:
            i += 1
            continue
        j = i
        while j + 1 < N and pitches[j + 1] == p:
            j += 1
        start = t0 + i * bar_len
        end = t0 + (j + 1) * bar_len
        nxt = pitches[j + 1] if j + 1 < N else None
        dur = (end - start) + (legato if (nxt is not None and nxt != p) else 0.0)
        sc.note(ch, p, start, dur, arc.vel(start, vlo, vhi), max_jit=max_jit)
        i = j + 1


def voiced_bars(chords, n_voices, band, prev=None):
    """chords: per-bar pcs (or None). Returns (list-of-voicings, final_voicing)."""
    voi, pv = [], prev
    for pcs in chords:
        if pcs is None:
            voi.append(None)
        else:
            pv = voice_chord(pcs, pv, n_voices, *band)
            voi.append(pv)
    return voi, pv


def pad(sc, ch, t0, chords, bar_len, arc, n_voices=4, band=(57, 81),
        vlo=30, vhi=92, prev=None, legato=0.30, cc_floor=34, expr=True):
    """Voice-led, tied string-pad bed. `chords` = per-bar pcs (or None)."""
    voi, pv = voiced_bars(chords, n_voices, band, prev)
    for vi in range(n_voices):
        line = [(v[vi] if v is not None else None) for v in voi]
        tied_line(sc, ch, t0, line, bar_len, arc, vlo, vhi, legato)
    if expr:
        expression(sc, ch, t0, t0 + len(chords) * bar_len, arc, cc_floor)
    return pv, voi


def bass(sc, ch, t0, roots, bar_len, arc, vlo=34, vhi=88,
         sustain=True, legato=0.3, cc_floor=40, expr=True, gate=0.92,
         pitch_floor=36):
    """Bass voice from per-bar root pitches (None = silent). Sustained & tied, or
    detached (sustain=False) for a more rhythmic feel."""
    def floored(p):
        if p is None:
            return None
        while p < pitch_floor:
            p += 12
        return p
    roots = [floored(p) for p in roots]
    if sustain:
        tied_line(sc, ch, t0, roots, bar_len, arc, vlo, vhi, legato)
    else:
        for i, p in enumerate(roots):
            if p is None:
                continue
            b = t0 + i * bar_len
            sc.note(ch, p, b, bar_len * gate, arc.vel(b, vlo, vhi), max_jit=6)
    if expr:
        expression(sc, ch, t0, t0 + len(roots) * bar_len, arc, cc_floor)


def _pattern_seq(v, pattern, rate):
    if not v:
        return []
    if pattern == 'up':
        base = v
    elif pattern == 'down':
        base = list(reversed(v))
    elif pattern == 'updown':
        base = v + list(reversed(v[1:-1])) if len(v) > 2 else v
    elif pattern == 'broken':           # low, high, mid, high ... (Alberti-ish spread)
        lo, hi = v[0], v[-1]
        mids = v[1:-1] or [v[0]]
        base = []
        mi = 0
        while len(base) < max(rate, len(v) * 2):
            base += [lo, hi, mids[mi % len(mids)], hi]
            mi += 1
    elif pattern == 'pendulum':         # 0,1,2,3,2,1 repeating
        base = v + list(reversed(v[1:-1]))
    else:
        base = v
    out = []
    while len(out) < rate:
        out += base
    return out[:rate]


def arpeggiate(sc, ch, t0, voicings, bar_len, arc, rate=8, pattern='updown',
               vlo=26, vhi=72, gate=1.25, vel_jit=4, accent_every=0, accent=10):
    """Glass-style broken chords. `voicings` = per-bar pitch lists (or None).
    `rate` = notes per bar; `pattern` = up/down/updown/broken/pendulum."""
    for i, v in enumerate(voicings):
        if not v:
            continue
        bb = t0 + i * bar_len
        seq = _pattern_seq(v, pattern, rate)
        step = bar_len / rate
        for k, p in enumerate(seq):
            b = bb + k * step
            vel = arc.vel(b, vlo, vhi) + random.randint(-vel_jit, vel_jit)
            if accent_every and (k % accent_every == 0):
                vel += accent
            sc.note(ch, p, b, step * gate, vel, max_jit=5)


def ostinato(sc, ch, t0, n_bars, bar_len, cell, arc, vlo=40, vhi=98, vel_jit=4):
    """Repeating rhythmic cell for motoric movement.
    `cell` = list of (pitch_or_callable(bar), start_in_bar, dur, accent_bool).
    A callable pitch lets the figure follow a changing harmony per bar."""
    for bar in range(n_bars):
        bb = t0 + bar * bar_len
        for (pitch, st, dur, acc) in cell:
            p = pitch(bar) if callable(pitch) else pitch
            if p is None:
                continue
            b = bb + st
            vel = arc.vel(b, vlo, vhi) + (10 if acc else 0) + random.randint(-vel_jit, vel_jit)
            sc.note(ch, p, b, dur, vel, max_jit=4)


def melody(sc, ch, t0, theme, base, arc, vlo=48, vhi=104, vel_jit=6,
           gate=0.96, max_jit=12, octave=0):
    """Play a theme: list of (semitone_offset_from_base, start_beat, dur_beats)."""
    for (off, start, dur) in theme:
        b = t0 + start
        sc.note(ch, base + off + 12 * octave, b, dur * gate,
                arc.vel(b, vlo, vhi) + random.randint(-vel_jit, vel_jit), max_jit=max_jit)


def piano_chords(sc, ch, t0, voicings, roots, bar_len, arc, eighths=False,
                 vlo=26, vhi=68, pedal=True):
    """Gently broken piano with optional sustain-pedal blur, cleared each bar."""
    for i, v in enumerate(voicings):
        if not v:
            continue
        bb = t0 + i * bar_len
        if pedal:
            sc.cc(ch, 64, 0, bb - 0.02)
            sc.cc(ch, 64, 127, bb)
        if roots and roots[i] is not None:
            sc.note(ch, roots[i], bb, bar_len, arc.vel(bb, vlo + 4, vhi + 2), max_jit=8)
        if eighths:
            order = v + list(reversed(v[1:-1])) if len(v) > 2 else v
            step = bar_len / len(order)
            for k, p in enumerate(order):
                b = bb + k * step
                sc.note(ch, p, b, step * 1.4, arc.vel(b, vlo, vhi) + random.randint(-4, 4), max_jit=8)
        else:
            step = bar_len / max(1, len(v))
            for k, p in enumerate(v):
                b = bb + k * step
                sc.note(ch, p, b, step * 1.6, arc.vel(b, vlo, vhi) + random.randint(-4, 4), max_jit=8)
    if pedal and voicings:
        sc.cc(ch, 64, 0, t0 + len(voicings) * bar_len - 0.01)


def expression(sc, ch, beat_start, beat_end, arc, floor=34, step=1.0):
    """One coherent CC11 expression envelope across a span (the breathing dynamics)."""
    b = beat_start
    while b <= beat_end + 1e-6:
        sc.cc(ch, 11, arc.cc11(b, floor), b)
        b += step


def fade_out(sc, channels, t0, length, beats=12, top=72):
    """A long CC11 fade to near-silence on the given channels (for tails)."""
    for ch in channels:
        for k in range(beats + 1):
            b = t0 + k * (length / beats)
            sc.cc(ch, 11, max(2, int(top * (1 - k / beats)) + 4), b)


# ----------------------------------------------------------------------------
# Serialise to a type-1 MIDI file
# ----------------------------------------------------------------------------
def _ascii(s):
    """MIDI meta strings are latin-1 only; normalise common unicode to ASCII."""
    if not s:
        return s
    for a, b in (('—', '-'), ('–', '-'), ('’', "'"), ('‘', "'"),
                 ('“', '"'), ('”', '"'), ('…', '...'), ('é', 'e')):
        s = s.replace(a, b)
    return s.encode('latin-1', 'replace').decode('latin-1')


def write_midi(sc, path, title='', text='', key='Dm', time_sig=(4, 4)):
    sc._resolve_overlaps()
    ctx = sc.ctx
    title, text = _ascii(title), _ascii(text)
    mid = MidiFile(type=1, ticks_per_beat=ctx.tpb)

    meta = MidiTrack()
    mid.tracks.append(meta)
    meta.append(MetaMessage('track_name', name=title, time=0))
    if text:
        meta.append(MetaMessage('text', text=text, time=0))
    # tempo map (initial + any changes), as absolute-tick events then deltas
    tempos = [(0.0, ctx.bpm)] + list(sc.tempo_changes)
    tempos = sorted({int(round(b * ctx.tpb)): bpm for (b, bpm) in tempos}.items())
    meta.append(MetaMessage('time_signature', numerator=time_sig[0],
                            denominator=time_sig[1], time=0))
    try:
        meta.append(MetaMessage('key_signature', key=key, time=0))
    except Exception:
        pass
    prev = 0
    for (tick, bpm) in tempos:
        meta.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=tick - prev))
        prev = tick

    # determine end
    last_tick = 0
    for ch, events in sc.ev.items():
        for (tick, _o, _m) in events:
            last_tick = max(last_tick, tick)
    meta.append(MetaMessage('end_of_track', time=last_tick - prev + ctx.tpb))

    for ch in sorted(sc.ev):
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage('track_name', name=_ascii(sc.names.get(ch, f'ch{ch}')), time=0))
        events = sorted(sc.ev[ch], key=lambda e: (e[0], e[1]))
        p = 0
        for (tick, _o, msg) in events:
            track.append(msg.copy(time=max(0, tick - p)))
            p = tick
        track.append(MetaMessage('end_of_track', time=ctx.tpb))

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    mid.save(path)
    return mid


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------
def analyze(path):
    """Structural report: length, per-channel notes/range, sounding pitch-classes,
    same-pitch overlaps (a sign of accidental re-triggering on sustained voices)."""
    m = MidiFile(path)
    chans = {}
    pcs = set()
    overlaps = {}
    for tr in m.tracks:
        active = {}
        ov = 0
        for msg in tr:
            if msg.type == 'note_on' and msg.velocity > 0:
                c = chans.setdefault(msg.channel, {'n': 0, 'min': 127, 'max': 0})
                c['n'] += 1
                c['min'] = min(c['min'], msg.note)
                c['max'] = max(c['max'], msg.note)
                pcs.add(msg.note % 12)
                if active.get(msg.note, 0) > 0:
                    ov += 1
                active[msg.note] = active.get(msg.note, 0) + 1
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if active.get(msg.note, 0) > 0:
                    active[msg.note] -= 1
        if ov:
            overlaps[tr.name] = ov
    return {
        'length': m.length,
        'channels': chans,
        'pcs': sorted(pcs),
        'pc_names': sorted(NAMES[p] for p in pcs),
        'overlaps': overlaps,
        'n_notes': sum(c['n'] for c in chans.values()),
    }


def print_report(path, allowed_pcs=None):
    r = analyze(path)
    mm = int(r['length'] // 60)
    ss = r['length'] - mm * 60
    print(f"{os.path.basename(path)}: {mm}:{ss:05.2f}  notes={r['n_notes']}  pcs={r['pc_names']}")
    for ch in sorted(r['channels']):
        c = r['channels'][ch]
        print(f"   ch{ch}: {c['n']:4d} notes  range {c['min']}-{c['max']}")
    if r['overlaps']:
        print(f"   same-pitch overlaps: {r['overlaps']}")
    if allowed_pcs is not None:
        extra = sorted(NAMES[p] for p in set(r['pcs']) - set(pc(x) for x in allowed_pcs))
        print(f"   non-scale notes: {extra or 'NONE'}")
    return r
