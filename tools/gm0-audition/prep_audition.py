#!/usr/bin/env python3
"""Prepare an audition variant of a MIDI: force the piano channel onto a chosen
GM0 alternate bank (CC0 = bank select MSB) and optionally trim to the first N
seconds.

The synth selects a GM0 alternate grand via CC0 (Bank Select MSB) on the channel:
CC0=0 -> default B1 upright, CC0=1..N -> the alternate banks in altbank::make.
This script injects one `CC0=<bank>` event at tick 0 on the target channel(s) and
(optionally) truncates the file at a tick, appending note-offs for anything still
sounding so a trimmed excerpt ends cleanly.

Stdlib only. Events are re-serialized with explicit status bytes (no running
status) for simplicity.

    # Tubular Bells opening, first ~35 s, piano (ch 0) on alt bank 2:
    python prep_audition.py in.mid -o out.mid --bank 2 --channel 0 --max-seconds 35

    # bank 0 (B1 upright default) is a no-op inject but still trims:
    python prep_audition.py in.mid -o out.mid --bank 0 --max-seconds 35
"""
import struct
import sys


def vlq_read(b, p):
    v = 0
    while True:
        c = b[p]
        p += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            break
    return v, p


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


def parse(path):
    b = open(path, "rb").read()
    assert b[:4] == b"MThd", "not a MIDI file"
    fmt, ntrk, div = struct.unpack(">HHH", b[8:14])
    p = 14
    tracks = []
    for _ in range(ntrk):
        assert b[p:p + 4] == b"MTrk"
        ln = struct.unpack(">I", b[p + 4:p + 8])[0]
        p += 8
        end = p + ln
        st = 0
        tick = 0
        evs = []          # (abstick, kind, bytes) kind: 'midi'|'meta'|'sysex'
        while p < end:
            dt, p = vlq_read(b, p)
            tick += dt
            ev = b[p]
            if ev & 0x80:
                st = ev
                p += 1
            else:
                ev = st
            if ev == 0xFF:
                mt = b[p]
                p += 1
                l, p = vlq_read(b, p)
                data = b[p:p + l]
                p += l
                evs.append((tick, "meta", bytes([0xFF, mt]) + vlq(l) + data))
            elif ev in (0xF0, 0xF7):
                l, p = vlq_read(b, p)
                data = b[p:p + l]
                p += l
                evs.append((tick, "sysex", bytes([ev]) + vlq(l) + data))
            else:
                hi = ev & 0xF0
                nbytes = 1 if hi in (0xC0, 0xD0) else 2
                data = b[p:p + nbytes]
                p += nbytes
                evs.append((tick, "midi", bytes([ev]) + data))
        tracks.append(evs)
        p = end
    return fmt, div, tracks


def tempo_ticks_for_seconds(tracks, div, seconds):
    """Walk the tempo map to find the tick at `seconds`."""
    # Collect (tick, us_per_qn) tempo changes across all tracks.
    tempos = [(0, 500000)]
    for evs in tracks:
        for tick, kind, raw in evs:
            if kind == "meta" and raw[1] == 0x51:
                us = int.from_bytes(raw[-3:], "big")
                tempos.append((tick, us))
    tempos.sort()
    # Integrate seconds over tick segments until we reach `seconds`.
    target_us = seconds * 1_000_000
    acc_us = 0.0
    for i, (tick, us) in enumerate(tempos):
        nxt = tempos[i + 1][0] if i + 1 < len(tempos) else None
        us_per_tick = us / div
        if nxt is None:
            # last segment runs to infinity
            remain = target_us - acc_us
            return int(tick + remain / us_per_tick)
        seg_ticks = nxt - tick
        seg_us = seg_ticks * us_per_tick
        if acc_us + seg_us >= target_us:
            remain = target_us - acc_us
            return int(tick + remain / us_per_tick)
        acc_us += seg_us
    return None  # never reached


def prep(inp, out, bank, channels, max_ticks):
    fmt, div, tracks = parse(inp)

    if max_ticks is not None:
        new_tracks = []
        for evs in tracks:
            sounding = {}   # (ch,key) -> True for notes still on at cut
            kept = []
            for tick, kind, raw in evs:
                if tick > max_ticks:
                    break
                if kind == "meta" and raw[1] == 0x2F:
                    continue  # drop EOT; re-added below
                kept.append((tick, kind, raw))
                if kind == "midi":
                    hi = raw[0] & 0xF0
                    ch = raw[0] & 0x0F
                    if hi == 0x90 and raw[2] > 0:
                        sounding[(ch, raw[1])] = True
                    elif hi == 0x80 or (hi == 0x90 and raw[2] == 0):
                        sounding.pop((ch, raw[1]), None)
            for (ch, key) in list(sounding):
                kept.append((max_ticks, "midi", bytes([0x80 | ch, key, 0])))
            kept.append((max_ticks, "meta", b"\xff\x2f\x00"))
            new_tracks.append(kept)
        tracks = new_tracks

    # Inject CC0=bank at tick 0 for each target channel (skip when bank==0).
    if bank > 0:
        inj = [(0, "midi", bytes([0xB0 | ch, 0x00, bank])) for ch in channels]
        # Prepend a dedicated track so we never disturb existing track 0 meta.
        tracks.insert(0, inj + [(0, "meta", b"\xff\x2f\x00")])
        fmt = 1  # multi-track now

    write(out, fmt, div, tracks)


def write(out, fmt, div, tracks):
    body = bytearray()
    for evs in tracks:
        evs = sorted(evs, key=lambda x: x[0])
        trk = bytearray()
        last = 0
        has_eot = False
        for tick, kind, raw in evs:
            if kind == "meta" and raw[1] == 0x2F:
                has_eot = True
                continue
            dt = tick - last
            last = tick
            trk += vlq(dt) + raw
        trk += vlq(0) + b"\xff\x2f\x00"
        body += b"MTrk" + struct.pack(">I", len(trk)) + bytes(trk)
    hdr = b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), div)
    with open(out, "wb") as f:
        f.write(hdr + body)


def main():
    a = sys.argv[1:]
    inp = a[0]
    out = None
    bank = 0
    channels = [0]
    max_seconds = None
    i = 1
    while i < len(a):
        if a[i] in ("-o", "--out"):
            out = a[i + 1]; i += 2
        elif a[i] == "--bank":
            bank = int(a[i + 1]); i += 2
        elif a[i] == "--channel":
            channels = [int(x) for x in a[i + 1].split(",")]; i += 2
        elif a[i] == "--max-seconds":
            max_seconds = float(a[i + 1]); i += 2
        else:
            raise SystemExit(f"unknown arg {a[i]}")
    assert out, "need -o"
    _, div, tracks = parse(inp)
    max_ticks = tempo_ticks_for_seconds(tracks, div, max_seconds) if max_seconds else None
    prep(inp, out, bank, channels, max_ticks)
    print(f"wrote {out} (bank={bank} channels={channels} "
          f"max_ticks={max_ticks})")


if __name__ == "__main__":
    main()
