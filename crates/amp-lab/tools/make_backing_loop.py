#!/usr/bin/env python3
"""Generate amp-lab's 8-bar backing loop.

Bass and drums are not decoration: they occupy exactly the bands the cabinet
knobs move (bass masks the low-mids where Body lives; cymbals sit where Presence
and Cab Tone live), so a rig judged solo gets judged wrong. The lead sits in the
register Arthur's original "GM029 sounds the same" complaint was about.

Channel map (amp-lab solos ch0+ch1):
    0  rhythm guitar  GM30 main bank   — the chug
    1  LEAD guitar    GM29 lead bank   — the knobs act on this one
    2  bass           GM33
    9  drums

Stdlib only, like the album engines. Run from the repo root:
    python tools/make_backing_loop.py
"""
import os
import struct

PPQ = 480
BPM = 104
TEMPO_US = int(60_000_000 / BPM)
BAR = PPQ * 4
BARS = 8

RHY, LEAD, BASS, DRUM = 0, 1, 2, 9


def vlq(n):
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


class Track:
    def __init__(self):
        self.ev = []

    def cc(self, t, ch, num, val):
        self.ev.append((t, [0xB0 | ch, num, val]))

    def prog(self, t, ch, p):
        self.ev.append((t, [0xC0 | ch, p]))

    def note(self, t, ch, key, dur, vel=100):
        self.ev.append((t, [0x90 | ch, key, vel]))
        self.ev.append((t + max(1, dur - 8), [0x80 | ch, key, 0]))


t = Track()

# ---- setup -------------------------------------------------------------
t.cc(0, RHY, 0, 0)                 # main bank
t.prog(0, RHY, 30)                 # distortion, rhythm
t.cc(0, RHY, 7, 88)
t.cc(0, RHY, 10, 44)               # slightly left

t.cc(0, LEAD, 0, 1)                # lead bank — amp-lab drives this channel
t.prog(0, LEAD, 29)                # overdrive, lead
t.cc(0, LEAD, 7, 96)
t.cc(0, LEAD, 10, 78)              # slightly right

t.prog(0, BASS, 33)
t.cc(0, BASS, 7, 100)
t.cc(0, BASS, 10, 64)
t.cc(0, DRUM, 7, 100)

# ---- riff --------------------------------------------------------------
# A minor: i - VI - III - VII, a plain rock loop that leaves room to hear the amp.
ROOTS = [45, 41, 48, 43]           # A2 F2 C3 G2, two bars each -> 8 bars

for bar in range(BARS):
    b0 = bar * BAR
    root = ROOTS[(bar // 2) % 4]

    # rhythm guitar: eighth-note power chords (root + fifth), palm-muted feel
    for e in range(8):
        tt = b0 + e * (PPQ // 2)
        vel = 104 if e % 2 == 0 else 84
        dur = PPQ // 2
        t.note(tt, RHY, root, dur, vel)
        t.note(tt, RHY, root + 7, dur, vel - 6)

    # bass: root on the beat, octave push on the & of 3
    for e, k in [(0, root - 12), (2, root - 12), (4, root - 12), (5, root - 5), (6, root - 12)]:
        t.note(b0 + e * (PPQ // 2), BASS, k, PPQ // 2, 102)

    # drums: kick/snare/hat backbeat, crash on bar 1 and 5
    for e in range(8):
        tt = b0 + e * (PPQ // 2)
        t.note(tt, DRUM, 42, PPQ // 4, 74 if e % 2 else 92)     # closed hat
    for e in [0, 3, 4, 6]:
        t.note(b0 + e * (PPQ // 2), DRUM, 36, PPQ // 4, 106)    # kick
    for e in [2, 6]:
        t.note(b0 + e * (PPQ // 2), DRUM, 38, PPQ // 4, 108)    # snare
    if bar % 4 == 0:
        t.note(b0, DRUM, 49, PPQ, 104)                          # crash

# lead: a singing line over bars 3-8, in the register the complaint was about
LEADLINE = [
    (2.0, 64, 1.5), (3.5, 67, 0.5), (4.0, 69, 2.0), (6.0, 67, 1.0),
    (7.0, 64, 1.0), (8.0, 62, 2.0), (10.0, 64, 1.5), (11.5, 60, 0.5),
    (12.0, 57, 2.0), (14.0, 64, 1.0), (15.0, 69, 1.0),
    (16.0, 67, 2.0), (18.0, 69, 1.0), (19.0, 71, 1.0),
    (20.0, 72, 3.0), (23.0, 69, 1.0),
    (24.0, 67, 2.0), (26.0, 64, 1.0), (27.0, 62, 1.0),
    (28.0, 64, 4.0),
]
for beat, key, dur in LEADLINE:
    t.note(int(beat * PPQ), LEAD, key, int(dur * PPQ), 100)

# ---- write -------------------------------------------------------------
t.ev.sort(key=lambda e: e[0])
trk = bytearray()
trk += vlq(0) + bytes([0xFF, 0x51, 0x03]) + struct.pack(">I", TEMPO_US)[1:]
last = 0
for tick, data in t.ev:
    trk += vlq(tick - last) + bytes(data)
    last = tick
trk += vlq(0) + bytes([0xFF, 0x2F, 0x00])

hdr = b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
mid = hdr + b"MTrk" + struct.pack(">I", len(trk)) + bytes(trk)

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "assets", "backing.mid")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(mid)
print(f"wrote {os.path.normpath(out)}  ({len(mid)} bytes, {BARS} bars @ {BPM} bpm, "
      f"{len(t.ev)} events)")
