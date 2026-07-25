"""engine.py — the Hollow Hill composition engine.

A self-contained (standard-library-only) toolkit for writing long-form,
Oldfield-style instrumental MIDI:

    Score       collects note / CC / program events per channel, plus a
                conductor lane (tempo map, time signatures, markers)
    pitch()     modal scale-degree arithmetic (degrees may be <1 or >7)
    triad()     diatonic stacked-third chords on any degree
    voice_lead  minimal-motion chord voicing (keeps common tones)
    line()      play a melody given as (degree, start_beat, dur_beats)
    pad_block   voice-led sustained chord bed with tied common tones
    strum()     spread guitar chord
    arp()       broken-chord figuration
    expr_curve  CC11 expression envelope from breakpoints
    morse()     tap a text in Morse code on a percussion note
    write_midi  serialise to a type-1 file
    parse_midi  minimal reader used by build.py --verify

All times are in beats (quarter notes, floats); tempo is a map so sections
can breathe. Humanisation comes from a seeded RNG so builds are reproducible.
"""

from __future__ import annotations

import random
import struct
from pathlib import Path

PPQ = 480
ALBUM_ROOT = Path(__file__).resolve().parent
MIDI_DIR = ALBUM_ROOT / "midi"

# ---------------------------------------------------------------------------
# Pitch theory
# ---------------------------------------------------------------------------

_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
       "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10,
       "Bb": 10, "B": 11}

MODES = {
    "ionian":     [0, 2, 4, 5, 7, 9, 11],
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "phrygian":   [0, 1, 3, 5, 7, 8, 10],
    "lydian":     [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian":    [0, 2, 3, 5, 7, 8, 10],
}


def n(name: str) -> int:
    """Note name -> MIDI pitch, e.g. n('E4') == 64 (C4 = 60)."""
    octave = int(name[-1]) - (1 if name[-2] == "-" else 0)
    letter = name[:-1].rstrip("-")
    return 12 * (octave + 1) + _PC[letter]


def deg_semis(mode: str, degree: int) -> int:
    """Semitones above the tonic for a 1-based degree (any int; 8 = octave,
    0 = the seventh below the tonic, and so on)."""
    steps = MODES[mode]
    d = degree - 1
    return steps[d % 7] + 12 * (d // 7)


def pitch(base: int, mode: str, degree: int) -> int:
    """MIDI pitch of `degree` where `base` is the pitch of degree 1."""
    return base + deg_semis(mode, degree)


def triad(base: int, mode: str, degree: int, size: int = 3) -> list[int]:
    """Diatonic stacked thirds on a degree; size 4 adds the seventh, etc."""
    return [pitch(base, mode, degree + 2 * i) for i in range(size)]


def voice_lead(pcs: list[int], prev: list[int] | None, size: int,
               lo: int, hi: int) -> list[int]:
    """Voice the pitch classes with `size` notes inside [lo, hi], moving as
    little as possible from the previous voicing (common tones held)."""
    wanted = sorted({p % 12 for p in pcs})
    pool = [p for p in range(lo, hi + 1) if p % 12 in wanted]
    if not pool:
        pool = [p for p in range(lo - 12, hi + 13) if p % 12 in wanted]
    picked: list[int] = []
    avail = list(pool)
    if prev is None:
        targets = [lo + (hi - lo) * i / max(1, size - 1) for i in range(size)]
    else:
        targets = list(prev)[:size]
        while len(targets) < size:
            targets.append((lo + hi) / 2)
    for t in targets:
        best = min(avail, key=lambda p: abs(p - t))
        picked.append(best)
        if len(avail) > 1:
            avail.remove(best)
    return sorted(picked)


def lerp(a: float, b: float, x: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, x))


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

def _vlq(value: int) -> bytes:
    out = bytearray([value & 0x7F])
    value >>= 7
    while value:
        out.insert(0, 0x80 | (value & 0x7F))
        value >>= 7
    return bytes(out)


def _tick(beat: float) -> int:
    return max(0, int(round(beat * PPQ)))


class Score:
    """Event collector.  Channel 9 is the GM percussion channel."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.events: dict[int, list[tuple[int, int, bytes]]] = {}
        self.names: dict[int, str] = {}
        self.tempos: list[tuple[float, float]] = []      # (beat, bpm)
        self.timesigs: list[tuple[float, int, int]] = []  # (beat, num, den)
        self.markers: list[tuple[float, str]] = []
        self.last_beat = 0.0

    # -- channel setup ------------------------------------------------------
    def channel(self, ch: int, name: str, program: int = 0, volume: int = 100,
                pan: int = 64, reverb: int = 55, chorus: int = 0) -> None:
        self.names[ch] = name
        self.events.setdefault(ch, [])
        if ch != 9:
            self.program(ch, program, 0.0)
        self.cc(ch, 7, volume, 0.0)
        self.cc(ch, 10, pan, 0.0)
        self.cc(ch, 91, reverb, 0.0)
        if chorus:
            self.cc(ch, 93, chorus, 0.0)

    def program(self, ch: int, prog: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (_tick(beat), 1, bytes([0xC0 | ch, prog])))

    # -- events -------------------------------------------------------------
    def cc(self, ch: int, num: int, val: int, beat: float) -> None:
        self.events.setdefault(ch, []).append(
            (_tick(beat), 2, bytes([0xB0 | ch, num, max(0, min(127, val))])))

    def note(self, ch: int, p: int, beat: float, dur: float, vel: int,
             jt: int = 5, jv: int = 4) -> None:
        p = max(0, min(127, int(round(p))))
        vel = max(1, min(127, int(round(vel + self.rng.randint(-jv, jv)))))
        on = _tick(beat)
        if jt and beat > 0.05:
            on = max(0, on + self.rng.randint(-jt, jt))
        off = max(on + PPQ // 16, _tick(beat + max(0.05, dur)))
        ev = self.events.setdefault(ch, [])
        ev.append((on, 5, bytes([0x90 | ch, p, vel])))
        ev.append((off, 4, bytes([0x80 | ch, p, 0])))
        self.last_beat = max(self.last_beat, beat + dur)

    def hit(self, drum: int, beat: float, vel: int, jt: int = 3, jv: int = 5) -> None:
        self.note(9, drum, beat, 0.25, vel, jt=jt, jv=jv)

    def bend(self, ch: int, beat: float, semis: float) -> None:
        """Pitch bend in semitones (range +/-2, the synth's convention)."""
        raw = max(0, min(16383, int(round(8192 + semis / 2.0 * 8192))))
        self.events.setdefault(ch, []).append(
            (_tick(beat), 2, bytes([0xE0 | ch, raw & 0x7F, raw >> 7])))

    # -- conductor ----------------------------------------------------------
    def tempo(self, beat: float, bpm: float) -> None:
        self.tempos.append((beat, bpm))

    def timesig(self, beat: float, num: int, den: int) -> None:
        self.timesigs.append((beat, num, den))

    def marker(self, beat: float, text: str) -> None:
        self.markers.append((beat, text))

    # -- output -------------------------------------------------------------
    def seconds_at(self, beat: float) -> float:
        """Elapsed seconds at `beat`, integrating the tempo map."""
        tempos = sorted(self.tempos)
        total, cursor, bpm = 0.0, 0.0, tempos[0][1]
        for tb, tbpm in tempos:
            if tb >= beat:
                break
            total += (tb - cursor) * 60.0 / bpm
            cursor, bpm = tb, tbpm
        return total + (beat - cursor) * 60.0 / bpm

    def duration_seconds(self) -> float:
        return self.seconds_at(self.last_beat)

    def _resolve_overlaps(self) -> None:
        """Truncate same-pitch overlaps before serializing the score."""
        for ev in self.events.values():
            on_ticks: dict[int, list[int]] = {}
            off_indices: dict[int, list[int]] = {}
            for i, (tick, _priority, data) in enumerate(ev):
                status = data[0] & 0xF0
                if status == 0x90 and data[2] > 0:
                    on_ticks.setdefault(data[1], []).append(tick)
                elif status == 0x80 or (status == 0x90 and data[2] == 0):
                    off_indices.setdefault(data[1], []).append(i)
            for pitch, starts in on_ticks.items():
                indices = off_indices.get(pitch, [])
                if len(indices) != len(starts):
                    continue
                starts.sort()
                indices.sort(key=lambda i: ev[i][0])
                for start, index in zip(starts[1:], indices):
                    if ev[index][0] > start:
                        ev[index] = (start, ev[index][1], ev[index][2])

    def write(self, path: Path, title: str, comment: str = "") -> None:
        self._resolve_overlaps()
        end = _tick(self.last_beat) + 2 * PPQ

        def meta(kind: int, payload: bytes) -> bytes:
            return bytes([0xFF, kind]) + _vlq(len(payload)) + payload

        # conductor track
        cond: list[tuple[int, int, bytes]] = [
            (0, 0, meta(0x03, title.encode("ascii", "replace")))]
        if comment:
            cond.append((0, 0, meta(0x01, comment.encode("ascii", "replace"))))
        for beat, num, den in sorted(self.timesigs):
            cond.append((_tick(beat), 1,
                         meta(0x58, bytes([num, den.bit_length() - 1, 24, 8]))))
        for beat, bpm in sorted(self.tempos):
            mpq = int(round(60_000_000 / bpm))
            cond.append((_tick(beat), 2, meta(0x51, mpq.to_bytes(3, "big"))))
        for beat, text in sorted(self.markers):
            cond.append((_tick(beat), 3,
                         meta(0x06, text.encode("ascii", "replace"))))

        def chunk(events: list[tuple[int, int, bytes]], name: str | None) -> bytes:
            body = bytearray()
            if name is not None:
                body += _vlq(0) + meta(0x03, name.encode("ascii", "replace"))
            last = 0
            for tick, _prio, data in sorted(events, key=lambda e: (e[0], e[1])):
                body += _vlq(tick - last) + data
                last = tick
            body += _vlq(max(0, end - last)) + b"\xFF\x2F\x00"
            return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

        chunks = [chunk(cond, None)]
        for ch in sorted(self.events):
            chunks.append(chunk(self.events[ch], self.names.get(ch, f"ch{ch}")))
        header = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(header + b"".join(chunks))


# ---------------------------------------------------------------------------
# Texture helpers
# ---------------------------------------------------------------------------

def line(sc: Score, ch: int, t0: float, base: int, mode: str,
         notes: list[tuple[int, float, float]], vel: int, vel_end: int | None = None,
         shift: int = 0, octave: int = 0, gate: float = 0.98,
         jt: int = 6, jv: int = 5) -> None:
    """Play (degree, start, dur) triples relative to t0."""
    if not notes:
        return
    span = max(s + d for _, s, d in notes)
    for deg, start, dur in notes:
        v = vel if vel_end is None else lerp(vel, vel_end, start / span)
        sc.note(ch, pitch(base, mode, deg + shift) + 12 * octave,
                t0 + start, dur * gate, int(v), jt=jt, jv=jv)


def strum(sc: Score, ch: int, pitches: list[int], t0: float, dur: float,
          vel: int, spread: float = 0.035, down: bool = True) -> None:
    order = pitches if down else list(reversed(pitches))
    for i, p in enumerate(order):
        sc.note(ch, p, t0 + i * spread, dur - i * spread, vel - i, jt=3, jv=4)


def arp(sc: Score, ch: int, pitches: list[int], t0: float, count: int,
        step: float, vel: int, pattern: str = "up", gate: float = 1.25,
        accent_every: int = 0, accent: int = 10) -> None:
    if pattern == "down":
        seq = list(reversed(pitches))
    elif pattern == "updown" and len(pitches) > 2:
        seq = pitches + list(reversed(pitches[1:-1]))
    else:
        seq = pitches
    for k in range(count):
        v = vel + (accent if accent_every and k % accent_every == 0 else 0)
        sc.note(ch, seq[k % len(seq)], t0 + k * step, step * gate, v, jt=4)


def pad_block(sc: Score, ch: int, t0: float, chords: list[list[int] | None],
              span: float, size: int = 4, lo: int = 55, hi: int = 79,
              vel: int = 50, vel_end: int | None = None, legato: float = 0.25) -> None:
    """Voice-led sustained chords; equal pitches in adjacent steps are tied."""
    voicings: list[list[int] | None] = []
    prev = None
    for pcs in chords:
        if pcs is None:
            voicings.append(None)
        else:
            prev = voice_lead(pcs, prev, size, lo, hi)
            voicings.append(prev)
    total = len(chords) * span
    for vi in range(size):
        i = 0
        while i < len(voicings):
            v = voicings[i]
            if v is None:
                i += 1
                continue
            p = v[vi]
            j = i
            while j + 1 < len(voicings) and voicings[j + 1] is not None \
                    and voicings[j + 1][vi] == p:
                j += 1
            b = t0 + i * span
            vv = vel if vel_end is None else lerp(vel, vel_end, (i * span) / total)
            sc.note(ch, p, b, (j - i + 1) * span + legato, int(vv), jt=4, jv=3)
            i = j + 1


def bend_ramp(sc: Score, ch: int, t0: float, t1: float,
              s0: float, s1: float, steps: int = 12) -> None:
    """Glide the channel bend from s0 to s1 semitones over [t0, t1]."""
    for i in range(steps + 1):
        x = i / steps
        sc.bend(ch, lerp(t0, t1, x), lerp(s0, s1, x))


def run(sc: Score, ch: int, t0: float, base: int, mode: str,
        degrees: list[int], spacing: float, vel0: int, vel1: int,
        gate: float = 0.95, jt: int = 1, octave_double: int | None = None,
        legato: bool = False) -> float:
    """Rapid-fire line: evenly spaced degrees with a velocity ramp —
    the classic Oldfield machine-gun figure. Timing jitter is kept tight
    (the evenness IS the style); the life lives in the crescendo.
    With legato=True the notes overlap so the synth hammers instead of
    re-picking (CC68 must be on for the channel). Returns the end beat."""
    if legato:
        sc.cc(ch, 68, 127, t0 - 0.05)
    n = len(degrees)
    for i, deg in enumerate(degrees):
        vel = int(round(lerp(vel0, vel1, i / max(1, n - 1))))
        dur = spacing * (1.25 if legato else gate)
        p = pitch(base, mode, deg)
        sc.note(ch, p, t0 + i * spacing, dur, vel, jt=jt, jv=2)
        if octave_double is not None:
            sc.note(ch, p + octave_double, t0 + i * spacing, dur,
                    max(1, vel - 10), jt=jt, jv=2)
    if legato:
        sc.cc(ch, 68, 0, t0 + n * spacing + 0.3)
    return t0 + n * spacing


def expr_curve(sc: Score, ch: int, points: list[tuple[float, int]],
               step: float = 1.0) -> None:
    """CC11 envelope, linearly interpolated between (beat, value) breakpoints."""
    pts = sorted(points)
    for (b0, v0), (b1, v1) in zip(pts, pts[1:]):
        b = b0
        while b < b1 - 1e-9:
            sc.cc(ch, 11, int(lerp(v0, v1, (b - b0) / (b1 - b0))), b)
            b += step
    sc.cc(ch, 11, pts[-1][1], pts[-1][0])


_MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
          "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
          "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
          "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
          "Y": "-.--", "Z": "--..", " ": " "}


def morse(sc: Score, text: str, t0: float, unit: float = 0.25,
          drum: int = 76, vel: int = 40) -> float:
    """Tap `text` in Morse on a percussion note; returns the end beat."""
    b = t0
    for letter in text.upper():
        if letter == " ":
            b += 4 * unit
            continue
        for symbol in _MORSE[letter]:
            length = (3 if symbol == "-" else 1) * unit
            sc.note(9, drum, b, length * 0.9, vel, jt=2, jv=3)
            b += length + unit
        b += 2 * unit
    return b


# ---------------------------------------------------------------------------
# Minimal MIDI reader for verification
# ---------------------------------------------------------------------------

def parse_midi(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path.name}: no MThd header")
    fmt, ntracks, division = struct.unpack(">HHH", data[8:14])
    pos = 8 + int.from_bytes(data[4:8], "big")
    tempos: list[tuple[int, int]] = []
    notes = 0
    max_tick = 0
    names: list[str] = []
    for _ in range(ntracks):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError(f"{path.name}: missing MTrk chunk")
        size = int.from_bytes(data[pos + 4:pos + 8], "big")
        pos += 8
        end = pos + size
        tick = 0
        status = 0
        name = ""
        while pos < end:
            value = 0
            while True:
                byte = data[pos]
                pos += 1
                value = (value << 7) | (byte & 0x7F)
                if byte < 0x80:
                    break
            tick += value
            first = data[pos]
            if first >= 0x80:
                status = first
                pos += 1
            if status == 0xFF:
                kind = data[pos]
                pos += 1
                length = 0
                while True:
                    byte = data[pos]
                    pos += 1
                    length = (length << 7) | (byte & 0x7F)
                    if byte < 0x80:
                        break
                payload = data[pos:pos + length]
                pos += length
                if kind == 0x51:
                    tempos.append((tick, int.from_bytes(payload, "big")))
                elif kind == 0x03 and not name:
                    name = payload.decode("ascii", "replace")
            elif status in (0xF0, 0xF7):
                length = 0
                while True:
                    byte = data[pos]
                    pos += 1
                    length = (length << 7) | (byte & 0x7F)
                    if byte < 0x80:
                        break
                pos += length
            else:
                width = 1 if status & 0xF0 in (0xC0, 0xD0) else 2
                if status & 0xF0 == 0x90 and data[pos + 1] > 0:
                    notes += 1
                pos += width
            max_tick = max(max_tick, tick)
        names.append(name or "(unnamed)")
    tempos.sort()
    seconds = 0.0
    for i, (tick, mpq) in enumerate(tempos):
        nxt = tempos[i + 1][0] if i + 1 < len(tempos) else max_tick
        seconds += (nxt - tick) / division * mpq / 1_000_000
    return {"format": fmt, "tracks": ntracks, "ppq": division,
            "notes": notes, "seconds": seconds, "names": names,
            "tempo_events": len(tempos)}
