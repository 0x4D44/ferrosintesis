#!/usr/bin/env python3
"""Generate a GM0 acoustic-grand *torture-test* MIDI for the alternate-bank audition.

Everything is on MIDI channel 0, program 0 (Acoustic Grand). The point is to
exercise, in a few tens of seconds, every place where a piano sample bank (and the
LA blend that wraps it) can sound wrong, so the audition ranking is diagnostic and
not just "which recording is prettiest on one chord":

  1. Register sweep  C1..C7 at mf, one note at a time  -> tone across the range +
     the F#->G repitch zone boundaries (does a zone seam click / shift timbre?).
  2. Dynamic ladder  C4 at pp,p,mp,mf,f,ff                -> velocity-layer joins +
     attack character from soft to hard.
  3. Chromatic run   C3..C5 legato at mf                  -> every repitch seam in a
     row (an audible step in brightness/pitch = a bad root or a coarse zone map).
  4. Sustain chord   C3-E3-G3-C4 held ~4 s               -> the MODEL tail (past the
     0.85 s LA handover): if every bank sounds the same here, it's the model.
  5. Repeated note   G4 staccato x8 fast                  -> machine-gun / round-robin
     (1 RR banks will tell here).
  6. Cadence         a short I-IV-V-I arpeggio+chords      -> musical context.

No third-party deps (stdlib only). Writes a format-0 SMF.

    python make_torture_midi.py -o gm0-torture.mid
"""
import struct
import sys

DIV = 480           # ticks per quarter note
TEMPO = 500000      # us per quarter (120 BPM)
CH = 0              # piano channel
PROG = 0            # GM0 Acoustic Grand


def note(events, t_on, key, vel, dur):
    """Append a note-on at t_on and note-off at t_on+dur (ticks)."""
    events.append((t_on, 0x90 | CH, key, vel))
    events.append((t_on + dur, 0x80 | CH, key, 0))


def build():
    ev = []                     # (abstick, status, d1, d2)
    q = DIV                     # a quarter
    t = 0

    # --- 1. Register sweep: C1..C7, one per half-note, mf ---------------------
    for k in [24, 36, 48, 60, 72, 84, 96]:   # C1..C7
        note(ev, t, k, 80, q)                # quarter of sound...
        t += q + q // 2                      # ...+ a rest, so the decay shows

    t += q

    # --- 2. Dynamic ladder on C4 --------------------------------------------
    for v in [20, 45, 70, 90, 110, 127]:
        note(ev, t, 60, v, q)
        t += q + q // 4

    t += q

    # --- 3. Chromatic run C3..C5 (repitch-seam test), fast legato -------------
    for i, k in enumerate(range(48, 73)):     # C3..C5 inclusive
        note(ev, t, k, 78, q // 2 + 20)       # slight overlap = legato
        t += q // 2

    t += q

    # --- 4. Sustained chord, held long (model-tail exposure) -----------------
    for k in [48, 52, 55, 60]:                # C3 E3 G3 C4
        ev.append((t, 0x90 | CH, k, 72))
    hold = 4 * q
    for k in [48, 52, 55, 60]:
        ev.append((t + hold, 0x80 | CH, k, 0))
    t += hold + q

    # --- 5. Repeated note, staccato x8 (machine-gun / RR) --------------------
    for _ in range(8):
        note(ev, t, 79, 96, q // 4)           # G5-ish, short
        t += q // 3

    t += q

    # --- 6. Cadence: arpeggio then chord, I IV V I in C ----------------------
    chords = [
        [48, 52, 55, 60],   # C
        [53, 57, 60, 65],   # F
        [55, 59, 62, 67],   # G
        [48, 52, 55, 60, 64],  # C (add high)
    ]
    for ch in chords:
        # roll the arpeggio
        for j, k in enumerate(ch):
            note(ev, t + j * (q // 6), k, 84, q + q // 2)
        t += q + q // 2
        # then a solid block chord
        for k in ch:
            ev.append((t, 0x90 | CH, k, 92))
        for k in ch:
            ev.append((t + q, 0x80 | CH, k, 0))
        t += q + q // 2

    return ev


def serialize(ev):
    # meta: tempo + program change at tick 0
    head = []
    head.append((0, b"\xff\x51\x03" + TEMPO.to_bytes(3, "big")))   # set tempo
    head.append((0, bytes([0xC0 | CH, PROG])))                     # program change
    body = [(t, bytes([s, d1, d2]) if s & 0xF0 != 0xC0 else bytes([s, d1]))
            for (t, s, d1, d2) in ev]
    allev = head + body
    allev.sort(key=lambda x: x[0])

    out = bytearray()
    last = 0
    for t, raw in allev:
        dt = t - last
        last = t
        out += vlq(dt) + raw
    out += vlq(0) + b"\xff\x2f\x00"   # end of track

    trk = b"MTrk" + struct.pack(">I", len(out)) + bytes(out)
    hdr = b"MThd" + struct.pack(">IHHH", 6, 0, 1, DIV)
    return hdr + trk


def vlq(n):
    if n == 0:
        return b"\x00"
    buf = bytearray()
    while n:
        buf.insert(0, n & 0x7F)
        n >>= 7
    for i in range(len(buf) - 1):
        buf[i] |= 0x80
    return bytes(buf)


def main():
    out = "gm0-torture.mid"
    a = sys.argv[1:]
    if a and a[0] in ("-o", "--out"):
        out = a[1]
    data = serialize(build())
    with open(out, "wb") as f:
        f.write(data)
    print(f"wrote {out} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
