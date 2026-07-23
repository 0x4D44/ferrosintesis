#!/usr/bin/env python3
"""banjo_showcase.py — a fast bluegrass breakdown showing off the GM 105 banjo
(the real 5-string bank added 2026-07-23; see samples/banjo/ and
crates/ferrosintesis-samples-orchestral2/).

  ch0  Banjo (GM 105) — lead: continuous 16th-note Scruggs-style forward rolls at
       150 bpm (~11 notes/s), the melody accented on the beats with the high G
       5th-string drone woven between, up-the-neck runs into the bright top of the
       sampled range, and a flashy ascending G-run tag into a final ringing chord.
  ch1  Banjo (GM 105) — thumb bass on beats 1 & 3 for drive.

An AABB breakdown in G (G–C–D–Em changes). Unlike the engine-based demos here, this
one is deliberately STANDALONE (stdlib only, raw Standard MIDI File) so the committed
.mid is byte-pinned to what was auditioned, independent of any album engine.

Run:  python demos/banjo_showcase.py   ->   demos/banjo_showcase.mid
Render (from a worktree):  ferrosintesis demos/banjo_showcase.mid -o banjo_showcase.wav
"""
import struct
import sys
from pathlib import Path

TPQ = 480
BPM = 150


def vlq(n):
    o = bytearray(); o.append(n & 0x7F); n >>= 7
    while n:
        o.insert(0, (n & 0x7F) | 0x80); n >>= 7
    return bytes(o)


EVENTS = []


def note(ch, midi, start, dur, vel):
    EVENTS.append((start, 1, ch, midi, vel))
    EVENTS.append((start + dur, 0, ch, midi, 0))


SIX = TPQ // 4
BEAT = TPQ
DRONE = 67  # high G 5th-string drone
CH = {
    "G":  dict(high=74, inner=62, bass=[50, 55]),
    "C":  dict(high=76, inner=64, bass=[55, 60]),
    "D":  dict(high=74, inner=66, bass=[50, 57]),
    "Em": dict(high=76, inner=64, bass=[52, 59]),
}
PROG = ["G", "G", "C", "C", "G", "D", "G", "G",
        "G", "G", "C", "C", "G", "D", "G", "G",
        "Em", "Em", "C", "C", "G", "D", "G", "G",
        "C", "C", "G", "Em", "D", "D", "G", "G"]
MEL = [
    [71, 74, 71, 67], [69, 71, 67, 62], [64, 67, 72, 76], [72, 67, 64, 67],
    [74, 71, 67, 71], [69, 74, 78, 74], [67, 71, 74, 71], [67, 62, 67, 71],
    [74, 79, 74, 71], [74, 71, 69, 67], [76, 72, 67, 72], [79, 76, 72, 67],
    [74, 71, 67, 74], [78, 81, 78, 74], [79, 74, 71, 67], [67, 69, 71, 74],
    [64, 67, 71, 76], [71, 67, 64, 67], [72, 76, 79, 76], [76, 72, 67, 64],
    [74, 71, 67, 71], [69, 74, 78, 81], [79, 74, 71, 67], [71, 67, 62, 67],
    [72, 76, 72, 67], [76, 79, 76, 72], [74, 71, 67, 62], [64, 67, 71, 67],
    [66, 69, 74, 78], [69, 66, 62, 69], [67, 71, 74, 79], [74, 71, 67, 67],
]
LEAD, BASS = 0, 1


def roll_bar(bar_start, chord, mel4, bassvel=82, lead_gain=1.0):
    c = CH[chord]
    for b in range(4):
        t = bar_start + b * BEAT
        cell = [(mel4[b], 112), (DRONE, 78), (c["high"], 92), (c["inner"], 86)]
        for i, (m, v) in enumerate(cell):
            note(LEAD, m, t + i * SIX, int(SIX * 1.25), min(127, int(v * lead_gain)))
        if b in (0, 2):
            note(BASS, c["bass"][0 if b == 0 else 1], t, int(BEAT * 0.9), bassvel)


def run_16th(start, midis, vel=104, ch=LEAD):
    for i, m in enumerate(midis):
        note(ch, m, start + i * SIX, int(SIX * 1.15), vel)


def build():
    t = 0
    roll_bar(t, "G", [67, 71, 74, 71], lead_gain=0.8); t += TPQ * 4
    roll_bar(t, "G", [74, 71, 67, 62]); t += TPQ * 4
    for bar in range(32):
        roll_bar(t, PROG[bar], MEL[bar]); t += TPQ * 4
    run_16th(t, [55, 59, 62, 67, 71, 74, 79, 74, 71, 74, 79, 83, 79, 74, 71, 67], vel=110); t += TPQ * 4
    for m, v in [(55, 96), (59, 96), (62, 100), (67, 104), (71, 104), (74, 108)]:
        note(LEAD, m, t, TPQ * 3, v)
    note(BASS, 43, t, TPQ * 3, 88)
    t += TPQ * 4
    return t


def serialize(total):
    def track(evs):
        tr = bytearray()
        tr += vlq(0) + bytes([0xFF, 0x51, 0x03]) + struct.pack(">I", int(60_000_000 / BPM))[1:]
        tr += vlq(0) + bytes([0xC0 | LEAD, 105])
        tr += vlq(0) + bytes([0xC0 | BASS, 105])
        last = 0
        for tick, kind, ch, d1, d2 in evs:
            tr += vlq(tick - last) + bytes([(0x90 if kind else 0x80) | ch, d1, d2]); last = tick
        tr += vlq(0) + bytes([0xFF, 0x2F, 0x00])
        return bytes(tr)

    evs = sorted(EVENTS, key=lambda e: (e[0], e[1], e[2]))
    tk = track(evs)
    return b"MThd" + struct.pack(">IHHH", 6, 1, 1, TPQ) + b"MTrk" + struct.pack(">I", len(tk)) + bytes(tk)


if __name__ == "__main__":
    total = build()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_suffix(".mid")
    out.write_bytes(serialize(total))
    print(f"wrote {out}: {len(EVENTS) // 2} notes, {total / (TPQ * 4):.0f} bars, "
          f"~{total / TPQ * 60 / BPM:.1f}s at {BPM}bpm")
