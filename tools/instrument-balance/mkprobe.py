#!/usr/bin/env python3
"""Generate the instrument-balance calibration probe MIDI (stdlib only).

Implements SPEC_v2 §1. See
`wrk_docs/2026.07.20 - HLD - instrument balance oracle + drum-forward recalibration.md`.

Design points that are LOAD-BEARING — do not "simplify" them:

* **Six pitches, evenly spaced round the circle** (C3 F3 A#3 D#4 G#4 C#5). Two
  pitches under-sample: re-rendering the same probe a tritone away moved derived
  per-program levels by up to 4.5 dB. A C-heavy set is the *worst* choice, because
  `sampler.rs nearest()` picks the nearest sample-bank root and those roots cluster
  on C — so a C-heavy probe measures ferrosintesis's best case. Two octaves, not
  three: F2/C5 is out-of-idiom for whole GM families and the modules' out-of-range
  behaviour diverges arbitrarily.

* **Note 1.30 s against a 1.2 s analysis window.** At 1.0 s the last blocks straddle
  the note-off, so for slow-attack programs (ensembles 48-55, pads 88-95) the peak
  block lands in the release — and the release differs per engine, which is exactly
  the bias the short window exists to avoid.

* **Stride 2.60 s = 5.2 beats = 2496 ticks = 114660 frames = 26 x 4410.** An exact
  multiple of both the tick resolution and the BS.1770 100 ms hop, so every onset
  lands on the global momentary-block grid. Any future stride must preserve both.

* **Setup events at onset - 0.30 s, not on the onset tick.** A program change
  immediately followed by a note-on can be serviced with the *previous* patch on real
  SC-55 firmware (and on a cycle-accurate emulation of it) because the patch load and
  the emulated serial UART both take milliseconds.

* **Program change BEFORE CC91/93/94.** `engine.rs fx_profile` re-derives the chorus
  and delay sends on every program change and clears the "authored" flags, so sends
  authored before the PC would be silently overwritten.
"""
from __future__ import annotations

import struct
import sys

# --- timing -----------------------------------------------------------------
TPQN = 480
BPM = 120.0
SPB = 60.0 / BPM  # 0.5 s per quarter
SR = 44100

LEAD_IN_S = 1.00  # silence before the first onset (kills the file-start artifact)
SETUP_LEAD_S = 0.30  # setup block sits this far ahead of its note
NOTE_S = 1.30  # note held (analysis window is 1.2 s)
STRIDE_S = 2.60  # onset -> onset
TAIL_S = 3.00  # silence after the last note-off

KEYS = (48, 53, 58, 63, 68, 73)  # C3 F3 A#3 D#4 G#4 C#5
VELS = (72, 110)

SETS = {
    "smoke": [0, 6, 40, 118],
    "preflight": [0, 6, 16, 24, 33, 40, 48, 55, 61, 73, 90, 115],
    "hot": [30, 48, 55, 61, 87, 116, 127],
    "full": list(range(128)),
    **{f"chunk{n}": list(range(32 * n, 32 * n + 32)) for n in range(4)},
}


def vlq(n: int) -> bytes:
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def ticks(sec: float) -> int:
    """Seconds -> ticks. Exact for every value this probe uses."""
    return int(round(sec / SPB * TPQN))


def frames(sec: float) -> int:
    return int(round(sec * SR))


def setup_events(prog: int) -> list:
    """Per-note setup, in the order the modules require.

    CC121 first (clears bend/porta/sustain/aftertouch left by the previous note),
    then bank select, then the program change, and only THEN the send controllers —
    a program change re-derives the chorus/delay sends and clears their authored
    flags, so sends authored earlier would be discarded.
    """
    return [
        bytes([0xB0, 121, 0]),  # reset all controllers
        bytes([0xB0, 0, 0]),  # bank select MSB (capital tone)
        bytes([0xB0, 32, 0]),  # bank select LSB
        bytes([0xC0, prog]),  # program change  <-- before the sends
        bytes([0xB0, 7, 100]),  # volume  = GM default, authored explicitly
        bytes([0xB0, 10, 64]),  # pan     = centre
        bytes([0xB0, 1, 0]),  # modulation off
        bytes([0xB0, 64, 0]),  # sustain off
        bytes([0xB0, 91, 0]),  # reverb send off
        bytes([0xB0, 93, 0]),  # chorus send off
        bytes([0xB0, 94, 0]),  # delay / variation send off
    ]


def build(programs, path, plan_path):
    plan = []
    onset = LEAD_IN_S
    for p in programs:
        for key in KEYS:
            for vel in VELS:
                plan.append((onset, p, key, vel))
                onset += STRIDE_S

    # (tick, order, bytes) — `order` keeps same-tick events in a defined sequence.
    ev = []
    # GM System On. In a MIDI *file* a SysEx event is F0 <vlq length> <payload>,
    # NOT the raw wire bytes: writing F0 7E 7F ... makes the parser read 0x7E as a
    # 126-byte length and swallow the rest of the track. (It does exactly that —
    # every engine returned an empty render until this was fixed.)
    gm_on = bytes([0x7E, 0x7F, 0x09, 0x01, 0xF7])
    ev.append((0, 0, bytes([0xF0]) + vlq(len(gm_on)) + gm_on))
    for onset, p, key, vel in plan:
        st = ticks(onset - SETUP_LEAD_S)
        for i, e in enumerate(setup_events(p)):
            ev.append((st, 10 + i, e))
        ev.append((ticks(onset), 100, bytes([0x90, key, vel])))
        ev.append((ticks(onset + NOTE_S), 101, bytes([0x80, key, 0])))
    ev.sort(key=lambda e: (e[0], e[1]))

    trk = bytearray()
    trk += vlq(0) + bytes([0xFF, 0x51, 0x03]) + struct.pack(">I", int(6e7 / BPM))[1:]
    last = 0
    for tk, _, data in ev:
        trk += vlq(tk - last) + data
        last = tk
    # End of track is a DELTA from the last event, not an absolute tick. Writing the
    # absolute value (the original bug) appended trailing silence as long as the probe
    # itself, doubling every reference render's wall clock.
    end_tick = ticks(plan[-1][0] + NOTE_S + TAIL_S)
    trk += vlq(max(0, end_tick - last)) + bytes([0xFF, 0x2F, 0x00])

    hdr = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TPQN)
    with open(path, "wb") as f:
        f.write(hdr + b"MTrk" + struct.pack(">I", len(trk)) + bytes(trk))

    with open(plan_path, "w") as f:
        f.write("idx\tonset_s\tonset_frames\tprogram\tkey\tvelocity\n")
        for i, (onset, p, key, vel) in enumerate(plan):
            f.write(f"{i}\t{onset:.4f}\t{frames(onset)}\t{p}\t{key}\t{vel}\n")
    return plan


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "preflight"
    if which not in SETS:
        print(f"unknown set {which!r}; choose from {', '.join(sorted(SETS))}")
        return 2
    progs = SETS[which]
    mid, plan_path = f"_cal/probe_{which}.mid", f"_cal/plan_{which}.tsv"
    plan = build(progs, mid, plan_path)
    total = plan[-1][0] + NOTE_S + TAIL_S
    print(
        f"{mid}: {len(progs)} programs x {len(KEYS)} keys x {len(VELS)} vels "
        f"= {len(plan)} notes, {total:.1f} s ({total/60:.1f} min)"
    )
    # Invariants worth failing loudly on rather than debugging later.
    assert ticks(STRIDE_S) == 2496, "stride must be a whole number of ticks"
    assert frames(STRIDE_S) % 4410 == 0, "stride must be a multiple of the 100 ms hop"
    assert frames(LEAD_IN_S) % 4410 == 0, "lead-in must be a multiple of the 100 ms hop"
    return 0


if __name__ == "__main__":
    sys.exit(main())
