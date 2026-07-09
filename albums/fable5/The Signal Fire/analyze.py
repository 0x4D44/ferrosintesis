#!/usr/bin/env python3
"""analyze.py — measured audio verification for *The Signal Fire*
(roadmap section 7).  Standalone, standard library only.  Run AFTER
rendering the MIDI to a 16-bit stereo WAV:

    python analyze.py "wav/01 - The Signal Fire.wav"
                      [--manifest album_manifest.json] [--json]
                      [--click-threshold 0.4] [--silence-db -60]

Per movement (boundaries in seconds from album_manifest.json) it prints:

  RMS (dBFS)          the dynamics arc, measured
  stereo correlation  width (+1 mono ... 0 decorrelated); the lattice and
                      lead-double sections should be wider (lower) than M1
  spectral centroid   one 2048-sample FFT window per second (hand-rolled
                      iterative radix-2 FFT); the per-movement trend — M1
                      should rise (the CC74 filter opening is measurable),
                      M6 should fall

plus two pass/fail scans:

  clicks     adjacent-sample deltas above threshold that are NOT note
             attacks (an attack is followed by sustained higher energy;
             an isolated jump is a rendering defect)
  silence    runs of near-zero longer than 0.5 s; a run that reaches the
             end of the file is the final fade/tail and is reported but
             NOT a failure

Exit status is nonzero only on click / interior-silence findings; the
profile numbers are informational.  --json emits everything on stdout as
one JSON object for machine reading.

The whole file is scanned sample-by-sample in pure Python; expect roughly
a minute of runtime for a 17-minute 44.1 kHz stereo file.
"""

from __future__ import annotations

import argparse
import array
import json
import math
import sys
import wave
from operator import mul, sub
from pathlib import Path

FULL_SCALE = 32768.0
FFT_N = 2048
SILENCE_RUN_S = 0.5
_HANN = [0.5 - 0.5 * math.cos(2 * math.pi * i / (FFT_N - 1))
         for i in range(FFT_N)]


# ---------------------------------------------------------------------------
# FFT — iterative radix-2, in place, no dependencies
# ---------------------------------------------------------------------------

def fft(re: list[float], im: list[float]) -> None:
    """In-place iterative radix-2 FFT; len(re) must be a power of two."""
    count = len(re)
    j = 0
    for i in range(1, count):
        bit = count >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]
    length = 2
    while length <= count:
        ang = -2.0 * math.pi / length
        wr, wi = math.cos(ang), math.sin(ang)
        half = length >> 1
        for start in range(0, count, length):
            cr, ci = 1.0, 0.0
            for k in range(half):
                a, b = start + k, start + k + half
                tr = re[b] * cr - im[b] * ci
                ti = re[b] * ci + im[b] * cr
                re[b] = re[a] - tr
                im[b] = im[a] - ti
                re[a] += tr
                im[a] += ti
                cr, ci = cr * wr - ci * wi, cr * wi + ci * wr
        length <<= 1


def spectral_centroid_hz(left: array.array, right: array.array,
                         start: int, rate: int) -> float | None:
    """Centroid of one Hann-windowed FFT_N mono window starting at `start`."""
    if start + FFT_N > len(left):
        return None
    re = [(left[start + i] + right[start + i]) * 0.5 * _HANN[i]
          for i in range(FFT_N)]
    im = [0.0] * FFT_N
    fft(re, im)
    num = den = 0.0
    for k in range(1, FFT_N // 2):
        mag = math.hypot(re[k], im[k])
        num += k * mag
        den += mag
    if den < 1e-9:
        return None
    return (num / den) * rate / FFT_N


# ---------------------------------------------------------------------------
# WAV loading
# ---------------------------------------------------------------------------

def load_wav(path: Path) -> tuple[array.array, array.array, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2:
            raise SystemExit(f"ERROR: {path.name}: need 16-bit stereo, got "
                             f"{wav.getnchannels()} ch x "
                             f"{8 * wav.getsampwidth()} bit")
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder == "big":
        samples.byteswap()
    return samples[0::2], samples[1::2], rate


def movements_from_manifest(path: Path) -> list[tuple[str, float, float]]:
    data = json.loads(path.read_text("utf-8"))
    track = data["tracks"][0]
    return [(m["name"], float(m["start_seconds"]), float(m["end_seconds"]))
            for m in track.get("movements", [])]


# ---------------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------------

def _mean_abs(chan: array.array, lo: int, hi: int) -> float:
    lo, hi = max(0, lo), min(len(chan), hi)
    if hi <= lo:
        return 0.0
    return sum(map(abs, chan[lo:hi])) / (hi - lo)


def _is_attack(chan: array.array, idx: int, rate: int) -> bool:
    """A note-attack transient: the 10 ms after the jump carries clearly
    more energy than the 10 ms before, and the energy PERSISTS (a click is
    isolated instead — the signal reverts to its prior level).

    Two tiers: the +300 absolute floor protects quiet passages, but must
    not scale against loud ones — several grid-aligned voices striking a
    ff downbeat sum to a big delta whose post-energy rise is ~1.6-1.9x,
    which is an arrival, not a defect.  A genuine click riding a loud bed
    shows after ~= before (ratio ~1.0) and is still caught."""
    w = max(64, rate // 100)
    before = _mean_abs(chan, idx - w, idx - 8)
    after = _mean_abs(chan, idx + 8, idx + 8 + w)
    if after > 1.8 * before + 300.0:
        return True
    return before > 1500.0 and after > 1.5 * before


def click_scan(left: array.array, right: array.array, rate: int,
               threshold: float) -> list[tuple[float, str, int]]:
    """(time_s, channel, delta) for every non-attack jump above threshold
    (threshold as a fraction of full scale)."""
    thr = int(threshold * (FULL_SCALE - 1))
    findings: list[tuple[float, str, int]] = []
    block = rate  # scan one second at a time; block max via C-level map()
    for name, chan in (("L", left), ("R", right)):
        n = len(chan)
        for start in range(0, n - 1, block):
            # seg overlaps one sample backward so the delta across the block
            # boundary is owned by exactly one block (idx in [start, start+block)).
            seg = chan[max(0, start - 1):min(n, start + block)]
            if len(seg) < 2:
                continue
            if max(map(abs, map(sub, seg[1:], seg[:-1]))) <= thr:
                continue
            base = max(0, start - 1)
            prev = seg[0]
            for k in range(1, len(seg)):
                cur = seg[k]
                delta = cur - prev
                prev = cur
                if abs(delta) > thr:
                    idx = base + k
                    if not _is_attack(chan, idx, rate):
                        findings.append((idx / rate, name, delta))
                        if len(findings) >= 10000:
                            return findings
    return findings


def silence_scan(left: array.array, right: array.array, rate: int,
                 silence_db: float) -> tuple[list[tuple[float, float]],
                                             float | None]:
    """Runs of near-zero (both channels) longer than SILENCE_RUN_S seconds.
    Returns (interior_runs, tail_seconds) — a run reaching EOF is the tail."""
    amp = int(FULL_SCALE * (10 ** (silence_db / 20.0)))
    block = max(1, rate // 10)                     # 0.1 s resolution
    n = len(left)
    nblocks = (n + block - 1) // block
    silent = []
    for i in range(nblocks):
        lo, hi = i * block, min(n, (i + 1) * block)
        quiet = (max(map(abs, left[lo:hi])) < amp
                 and max(map(abs, right[lo:hi])) < amp)
        silent.append(quiet)
    runs: list[tuple[float, float]] = []
    tail: float | None = None
    need = max(1, int(SILENCE_RUN_S / (block / rate)))
    i = 0
    while i < nblocks:
        if not silent[i]:
            i += 1
            continue
        j = i
        while j < nblocks and silent[j]:
            j += 1
        if j - i >= need:
            t0, t1 = i * block / rate, min(n, j * block) / rate
            if j >= nblocks:
                tail = t1 - t0
            else:
                runs.append((t0, t1))
        i = j
    return runs, tail


# ---------------------------------------------------------------------------
# Per-movement profile
# ---------------------------------------------------------------------------

def profile(left: array.array, right: array.array, rate: int,
            movements: list[tuple[str, float, float]]) -> list[dict]:
    n = len(left)
    out = []
    for name, t0, t1 in movements:
        lo = max(0, min(n, int(t0 * rate)))
        hi = max(lo, min(n, int(t1 * rate)))
        if hi - lo < rate:
            out.append({"name": name, "start_s": round(t0, 2),
                        "end_s": round(t1, 2), "rms_db": None,
                        "correlation": None, "centroid": None})
            continue
        s_ll = s_rr = s_lr = 0.0
        s_l = s_r = 0.0
        centroids: list[tuple[float, float]] = []
        for sec_start in range(lo, hi, rate):
            sec_end = min(hi, sec_start + rate)
            lc, rc = left[sec_start:sec_end], right[sec_start:sec_end]
            s_ll += sum(map(mul, lc, lc))
            s_rr += sum(map(mul, rc, rc))
            s_lr += sum(map(mul, lc, rc))
            s_l += sum(lc)
            s_r += sum(rc)
            c = spectral_centroid_hz(left, right, sec_start, rate)
            if c is not None:
                centroids.append(((sec_start - lo) / rate, c))
        m = hi - lo
        rms = math.sqrt((s_ll + s_rr) / (2 * m)) / FULL_SCALE
        rms_db = 20 * math.log10(max(rms, 1e-7))
        var_l = m * s_ll - s_l * s_l
        var_r = m * s_rr - s_r * s_r
        corr = ((m * s_lr - s_l * s_r) / math.sqrt(var_l * var_r)
                if var_l > 0 and var_r > 0 else None)
        centroid = None
        if len(centroids) >= 2:
            xs = [x for x, _ in centroids]
            ys = [y for _, y in centroids]
            k = len(xs)
            mx, my = sum(xs) / k, sum(ys) / k
            denom = sum((x - mx) ** 2 for x in xs)
            slope = (sum((x - mx) * (y - my) for x, y in centroids) / denom
                     if denom > 0 else 0.0)
            centroid = {"first_hz": round(ys[0], 1),
                        "last_hz": round(ys[-1], 1),
                        "mean_hz": round(my, 1),
                        "slope_hz_per_s": round(slope, 2),
                        "trend": ("rising" if slope > 1.0 else
                                  "falling" if slope < -1.0 else "flat")}
        out.append({"name": name, "start_s": round(t0, 2),
                    "end_s": round(t1, 2), "rms_db": round(rms_db, 2),
                    "correlation": None if corr is None else round(corr, 3),
                    "centroid": centroid})
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measured audio verification for The Signal Fire "
                    "(roadmap section 7).")
    parser.add_argument("wav", type=Path, help="16-bit stereo WAV to scan")
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parent /
                        "album_manifest.json",
                        help="album_manifest.json with movement boundaries")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit one JSON object on stdout")
    parser.add_argument("--click-threshold", type=float, default=0.4,
                        help="adjacent-sample delta threshold, fraction of "
                             "full scale (default 0.4)")
    parser.add_argument("--silence-db", type=float, default=-60.0,
                        help="near-zero threshold in dBFS (default -60)")
    args = parser.parse_args(argv)

    left, right, rate = load_wav(args.wav)
    duration = len(left) / rate

    if args.manifest.exists():
        movements = movements_from_manifest(args.manifest)
    else:
        movements = []
    if not movements:
        movements = [("ALL", 0.0, duration)]

    movement_stats = profile(left, right, rate, movements)
    clicks = click_scan(left, right, rate, args.click_threshold)
    silence_runs, tail = silence_scan(left, right, rate, args.silence_db)

    worst_clicks = sorted(clicks, key=lambda c: -abs(c[2]))[:10]
    findings = bool(clicks) or bool(silence_runs)

    report = {
        "file": str(args.wav),
        "sample_rate": rate,
        "duration_seconds": round(duration, 2),
        "movements": movement_stats,
        "clicks": {
            "threshold": args.click_threshold,
            "count": len(clicks),
            "worst": [{"time_s": round(t, 4), "channel": ch, "delta": d}
                      for t, ch, d in worst_clicks],
        },
        "silence": {
            "threshold_db": args.silence_db,
            "interior_runs": [{"start_s": round(a, 2), "end_s": round(b, 2)}
                              for a, b in silence_runs],
            "final_tail_seconds": None if tail is None else round(tail, 2),
        },
        "pass": not findings,
    }

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{args.wav.name}: {duration:.1f}s @ {rate} Hz")
        print(f"{'movement':<16}{'span':>16}{'RMS dBFS':>10}"
              f"{'corr':>7}  centroid")
        for mv in movement_stats:
            span = f"{mv['start_s']:.0f}-{mv['end_s']:.0f}s"
            rms = "-" if mv["rms_db"] is None else f"{mv['rms_db']:.1f}"
            corr = ("-" if mv["correlation"] is None
                    else f"{mv['correlation']:.2f}")
            cen = mv["centroid"]
            cent = ("-" if cen is None else
                    f"{cen['first_hz']:.0f} -> {cen['last_hz']:.0f} Hz "
                    f"({cen['trend']}, {cen['slope_hz_per_s']:+.1f} Hz/s)")
            print(f"{mv['name']:<16}{span:>16}{rms:>10}{corr:>7}  {cent}")
        print(f"\nclicks: {len(clicks)} above "
              f"{args.click_threshold:.2f} FS (non-attack)")
        for t, ch, d in worst_clicks:
            print(f"    {t:9.3f}s  {ch}  delta {d:+d}")
        print(f"silence: {len(silence_runs)} interior run(s) > "
              f"{SILENCE_RUN_S}s below {args.silence_db:.0f} dBFS"
              + (f"; final tail {tail:.2f}s (OK)" if tail else ""))
        for a, b in silence_runs:
            print(f"    {a:9.2f}s - {b:.2f}s")
        print(f"\nRESULT: {'PASS' if not findings else 'FAIL'}"
              f" (profile numbers are informational)")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
