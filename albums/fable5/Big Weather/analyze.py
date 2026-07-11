#!/usr/bin/env python3
"""analyze.py — render-side (audio) verification for *Big Weather*.

The MIDI oracles in verify.py prove the score; this proves the RENDER
(repo lesson: verify headline effects on rendered audio, not just event
data).  For every track whose ferrosintesis WAV exists under audio/
(named "NN - Title.wav" after the track's MIDI), it rebuilds the
track's Score via build.build_score (for the beat->seconds map) and
runs the generic checks:

  * a stale-render guard — a WAV older than its MIDI FAILS (HLD D13:
    grading yesterday's render against today's beat map is the known
    iteration-losing trap; re-render, don't reinterpret);
  * a click scan — max sample-to-sample step <= 22000;
  * mono compatibility — mono-sum RMS within 2 dB of the stereo RMS
    (the pan-Haas mono-collapse lesson);

then the module's own audio_checks(ctx), if the track defines any.
`ctx` hands audio_checks the samples (ctx.l / ctx.r, 16-bit int lists),
ctx.sample_rate, ctx.sc (the rebuilt Score), ctx.module, and helpers
ctx.rms(l, r, i0, i1), ctx.db(x), and ctx.bar_window(beat0, beat1)
-> (i0, i1) sample indices.

    python analyze.py               all tracks (a missing WAV is a SKIP,
                                    not a failure)
    python analyze.py --track N     one track

Exits nonzero only when a present WAV fails a check; an all-SKIP run
exits 0.
"""

from __future__ import annotations

import math
import struct
import sys
import types
import wave
from pathlib import Path

import build as bd
import engine as en
import movements

AUDIO_DIR = en.ALBUM_ROOT / "audio"
MAX_SAMPLE_STEP = 22000
MONO_LOSS_CAP_DB = 2.0


def _load(path: Path):
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 2:
            raise SystemExit(f"{path.name}: need stereo 16-bit PCM")
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    n = len(raw) // 4
    samples = struct.unpack(f"<{n * 2}h", raw)
    return rate, list(samples[0::2]), list(samples[1::2])


def rms(left, right, i0: int = 0, i1: int | None = None) -> float:
    """Stereo RMS of samples [i0, i1) (16-bit ints, both channels)."""
    if i1 is None:
        i1 = len(left)
    i0, i1 = max(0, i0), min(len(left), i1)
    if i1 <= i0:
        return 0.0
    acc = 0.0
    for a, b in zip(left[i0:i1], right[i0:i1]):
        acc += a * a + b * b
    return (acc / (2 * (i1 - i0))) ** 0.5


def db(x: float, ref: float = 32768.0) -> float:
    return -120.0 if x <= 0 else 20 * math.log10(x / ref)


def _wav_path(module) -> Path:
    return AUDIO_DIR / (Path(module.FILE).stem + ".wav")


def analyze_track(module) -> tuple[int, int]:
    """Analyze one track's WAV; returns (failure_count, skip_count)."""
    path = _wav_path(module)
    tag = f"T{module.NUMBER:02d} {module.TITLE}"
    if not path.exists():
        print(f"{tag}: SKIP (audio/{path.name} missing)")
        return 0, 1
    midi_path = en.MIDI_DIR / module.FILE
    if (midi_path.exists()
            and path.stat().st_mtime < midi_path.stat().st_mtime):
        print(f"{tag}: FAIL - stale render (audio/{path.name} is older "
              f"than midi/{module.FILE}; re-render before analyzing)")
        return 1, 0
    sc, _spans = bd.build_score(module)
    rate, left, right = _load(path)
    if len(left) < 2:
        print(f"{tag}: FAIL - audio/{path.name} is empty or truncated "
              f"({len(left)} frames)")
        return 1, 0
    fails: list[str] = []

    # 1. Click scan.
    worst = max(abs(left[i] - left[i - 1]) for i in range(1, len(left)))
    worst = max(worst, max(abs(right[i] - right[i - 1])
                           for i in range(1, len(right))))
    if worst > MAX_SAMPLE_STEP:
        fails.append(f"click scan: max sample step {worst} "
                     f"(cap {MAX_SAMPLE_STEP})")

    # 2. Mono compatibility.
    stereo = rms(left, right)
    mono = math.sqrt(sum(((a + b) / 2) ** 2
                         for a, b in zip(left, right)) / len(left))
    loss = db(stereo) - db(mono)
    if loss > MONO_LOSS_CAP_DB:
        fails.append(f"mono collapse: mono sum {loss:.2f} dB below "
                     f"stereo (cap {MONO_LOSS_CAP_DB})")

    print(f"{tag}: {len(left) / rate:.1f}s  mono loss {loss:.2f} dB  "
          f"max step {worst}")
    for msg in fails:
        print(f"  FAIL: {msg}")
    failed = len(fails)

    # 3. The track's own audio oracles.
    checks = getattr(module, "audio_checks", None)
    if checks is not None:
        def bar_window(beat0: float, beat1: float) -> tuple[int, int]:
            return (int(sc.seconds_at(beat0) * rate),
                    int(sc.seconds_at(beat1) * rate))

        ctx = types.SimpleNamespace(
            l=left, r=right, sample_rate=rate, sc=sc, module=module,
            rms=rms, db=db, bar_window=bar_window)
        for name, cfails in checks(ctx):
            status = "PASS" if not cfails else f"FAIL ({len(cfails)})"
            print(f"  {name:<30} {status}")
            for msg in cfails:
                print(f"      - {msg}")
            failed += len(cfails)
    return failed, 0


def main(argv: list[str]) -> int:
    if not argv:
        mods = movements.load_tracks()
    elif argv[0] == "--track" and len(argv) == 2:
        try:
            number = int(argv[1])
        except ValueError:
            raise SystemExit("usage: python analyze.py [--track N]")
        mods = movements.load_tracks(only=number)
    else:
        raise SystemExit("usage: python analyze.py [--track N]")

    failed = skipped = 0
    for module in mods:
        f, s = analyze_track(module)
        failed += f
        skipped += s
    print()
    print(f"AUDIO: {'FAIL' if failed else 'PASS'} - "
          f"{len(mods) - skipped} track(s) analyzed, {skipped} skipped, "
          f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
