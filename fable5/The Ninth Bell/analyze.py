#!/usr/bin/env python3
"""analyze.py — render-side (audio) verification for *The Ninth Bell*.

The MIDI oracles in verify.py prove the score; this proves the RENDER
(repo lesson: verify headline effects on rendered audio, not just event
data).  Reads the hollowsynth WAV and reports:

  * the per-bar RMS contour vs the HLD dynamic arc (build / cliff /
    void / rebuild+feint / climax / embers), asserted numerically;
  * the two scored silences: the window RMS must be a decaying reverb
    tail (well below the hit peak, falling across the window);
  * mono compatibility: mono-sum RMS within 2 dB of the stereo mean
    (the pan-Haas mono-collapse lesson);
  * a click scan (max sample-to-sample step).

    python analyze.py "audio/01 - The Ninth Bell.wav"

Exits nonzero on any failure.
"""

from __future__ import annotations

import struct
import sys
import wave
from pathlib import Path

import build as bd

BAR_BEATS = 4.0
N_BARS = 101


def _load(path: Path):
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 2
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    n = len(raw) // 4
    samples = struct.unpack(f"<{n * 2}h", raw)
    left = samples[0::2]
    right = samples[1::2]
    return rate, left, right


def _rms(seg_l, seg_r) -> float:
    if not seg_l:
        return 0.0
    acc = 0.0
    for a, b in zip(seg_l, seg_r):
        acc += a * a + b * b
    return (acc / (2 * len(seg_l))) ** 0.5


def _db(x: float, ref: float = 32768.0) -> float:
    import math
    return -120.0 if x <= 0 else 20 * math.log10(x / ref)


def main(path: Path) -> int:
    sc, _spans = bd.build_score()
    rate, left, right = _load(path)

    def seg(b0: float, b1: float):
        i0 = int(sc.seconds_at(b0) * rate)
        i1 = int(sc.seconds_at(b1) * rate)
        return left[i0:i1], right[i0:i1]

    fails: list[str] = []

    # 1. Per-bar RMS contour.
    bar_rms = [0.0]
    for bar in range(1, N_BARS + 1):
        b0 = (bar - 1) * BAR_BEATS
        bar_rms.append(_rms(*seg(b0, b0 + BAR_BEATS)))
    mean = lambda a, b: sum(bar_rms[a:b + 1]) / (b - a + 1)

    s1, s2, s3 = mean(1, 8), mean(9, 24), mean(25, 32)
    if not s1 < s2 < s3:
        fails.append(f"audio arc: intro/processional/ascent RMS "
                     f"{_db(s1):.1f}/{_db(s2):.1f}/{_db(s3):.1f} dB "
                     f"must rise")
    void, climax, coda = mean(35, 41), mean(74, 88), mean(92, 101)
    if _db(void) > _db(s3) - 6:
        fails.append(f"audio arc: void {_db(void):.1f} dB not >=6 dB "
                     f"below the ascent {_db(s3):.1f} dB")
    if climax < s3:
        fails.append(f"audio arc: climax {_db(climax):.1f} dB below "
                     f"the first ascent {_db(s3):.1f} dB")
    if _db(coda) > _db(climax) - 10:
        fails.append(f"audio arc: embers {_db(coda):.1f} dB not >=10 dB "
                     f"below the climax {_db(climax):.1f} dB")
    feint, before = bar_rms[62], bar_rms[61]
    if feint > 0.8 * before:
        fails.append(f"audio arc: feint bar 62 {_db(feint):.1f} dB not "
                     f"below bar 61 {_db(before):.1f} dB")

    # 2. Scored silences decay like tails.
    for tag, hit_beat, w0, w1 in (("hit", 128.0, 129.5, 131.8),
                                  ("fracture", 352.0, 353.5, 357.5)):
        hit = _rms(*seg(hit_beat, hit_beat + 1.0))
        early = _rms(*seg(w0, (w0 + w1) / 2))
        late = _rms(*seg((w0 + w1) / 2, w1))
        if _db(early) > _db(hit) - 8:
            fails.append(f"{tag} silence: early tail {_db(early):.1f} dB "
                         f"not >=8 dB under the hit {_db(hit):.1f} dB")
        if late > early * 1.05:
            fails.append(f"{tag} silence: tail rises "
                         f"({_db(early):.1f} -> {_db(late):.1f} dB)")

    # 3. Mono compatibility.
    import math
    stereo = _rms(left, right)
    mono2 = sum(((a + b) / 2) ** 2 for a, b in zip(left, right)) / len(left)
    mono = math.sqrt(mono2)
    loss = _db(stereo) - _db(mono)
    if loss > 2.0:
        fails.append(f"mono collapse: mono sum {loss:.2f} dB below "
                     f"stereo (cap 2.0)")

    # 4. Click scan.
    worst = max(abs(left[i] - left[i - 1]) for i in range(1, len(left)))
    worst = max(worst, max(abs(right[i] - right[i - 1])
                           for i in range(1, len(right))))
    if worst > 22000:
        fails.append(f"click scan: max sample step {worst} (cap 22000)")

    print(f"{path.name}: {len(left)/rate:.1f}s")
    print(f"  arc dB  intro {_db(s1):6.1f}  proc {_db(s2):6.1f}  "
          f"ascent {_db(s3):6.1f}  void {_db(void):6.1f}")
    print(f"          tide {_db(mean(50, 73)):6.1f}  climax {_db(climax):6.1f}  "
          f"embers {_db(coda):6.1f}")
    print(f"  feint bar62 {_db(feint):.1f} dB (bar61 {_db(before):.1f})  "
          f"mono loss {loss:.2f} dB  max step {worst}")
    for f in fails:
        print(f"  FAIL: {f}")
    print("AUDIO:", "FAIL" if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if sys.argv[1:] else \
        Path("audio/01 - The Ninth Bell.wav")
    raise SystemExit(main(target))
