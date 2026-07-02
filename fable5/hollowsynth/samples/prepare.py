"""Rebuild the attack-transient sample bank from VSCO 2 Community Edition.

Downloads the source sustains (CC0, github.com/sgossner/VSCO-2-CE), then
trims each to its onset: ~0.62 s kept, fades applied, peak-normalized,
resampled to 44.1 kHz mono 16-bit. The fundamental is measured by
autocorrelation — smallest near-maximal lag (octave-safe) with parabolic
refinement (cent accuracy) — and printed as the zone's root frequency,
which must match the table in src/sampler.rs.

Pure stdlib; run from this directory: python prepare.py
"""

import math
import os
import struct
import sys
import tempfile
import urllib.request
import wave

BASE = "https://raw.githubusercontent.com/sgossner/VSCO-2-CE/master"
SOURCES = {
    f"violin_{n}_{d}.wav": f"{BASE}/Strings/Solo%20Violin/Arco%20Vib/LLVln_ArcoVib_{n}_{d}.wav"
    for n in ("G3", "E4", "C5", "G5", "C6", "E6")
    for d in ("f", "p")
} | {
    f"flute_{n}.wav": f"{BASE}/Woodwinds/Flute/susvib/LDFlute_susvib_{n}_v1_1.wav"
    for n in ("C4", "A4", "E5", "A5", "C6")
}

DST = os.path.dirname(os.path.abspath(__file__))
OUT_SR = 44100
KEEP_S = 0.62      # length kept after the pre-onset pad
PRE_S = 0.008      # pad kept before the onset
FADE_S = 0.20      # fade-out applied to the tail
NOTE_HZ = {}
for octave in range(0, 8):
    for i, name in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G",
                              "G#", "A", "A#", "B"]):
        NOTE_HZ[f"{name}{octave}"] = 440.0 * 2 ** ((12 * (octave + 1) + i - 69) / 12)


def read_wav(path):
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        vals = struct.unpack(f"<{n * ch}h", raw)
        norm = [v / 32768.0 for v in vals]
    elif sw == 3:
        norm = []
        for i in range(n * ch):
            v = int.from_bytes(raw[3 * i:3 * i + 3], "little", signed=True)
            norm.append(v / 8388608.0)
    else:
        raise ValueError(f"{path}: unsupported sample width {sw}")
    if ch == 2:
        norm = [(norm[2 * i] + norm[2 * i + 1]) * 0.5 for i in range(n)]
    return norm, sr


def resample(x, sr_in, sr_out):
    if sr_in == sr_out:
        return x
    ratio = sr_in / sr_out
    out = []
    for i in range(int(len(x) / ratio)):
        pos = i * ratio
        j = int(pos)
        f = pos - j
        a = x[j]
        b = x[j + 1] if j + 1 < len(x) else a
        out.append(a + (b - a) * f)
    return out


def measure_f0(x, sr, lo=80.0, hi=3000.0):
    """Autocorrelation over a window starting past the attack."""
    start = int(0.20 * sr)
    win = int(0.10 * sr)
    seg = x[start:start + win]
    if len(seg) < win:
        seg = x[len(x) // 3:len(x) // 3 + win]
    mean = sum(seg) / len(seg)
    seg = [v - mean for v in seg]
    min_lag = int(sr / hi)
    max_lag = int(sr / lo)
    e0 = sum(v * v for v in seg[:win - max_lag])
    corr = {}
    for lag in range(min_lag, max_lag):
        num = 0.0
        den = 0.0
        for i in range(win - max_lag):
            num += seg[i] * seg[i + lag]
            den += seg[i + lag] * seg[i + lag]
        corr[lag] = num / math.sqrt(e0 * den) if den > 0 and e0 > 0 else -1.0
    best = max(corr.values())
    # a periodic signal correlates equally at every multiple of its period;
    # take the SMALLEST lag that comes close to the maximum
    best_lag = next(lag for lag in sorted(corr) if corr[lag] >= best - 0.03)
    # parabolic interpolation around the peak for sub-sample lag accuracy
    lag = float(best_lag)
    if best_lag - 1 in corr and best_lag + 1 in corr:
        a, b, c = corr[best_lag - 1], corr[best_lag], corr[best_lag + 1]
        den = a - 2 * b + c
        if den != 0:
            lag += 0.5 * (a - c) / den
    return sr / lag, corr[best_lag]


def main():
    src = os.path.join(tempfile.gettempdir(), "vsco2ce_src")
    os.makedirs(src, exist_ok=True)
    for fn, url in SOURCES.items():
        path = os.path.join(src, fn)
        if not os.path.exists(path):
            print(f"fetching {fn} ...", file=sys.stderr)
            urllib.request.urlretrieve(url, path)

    rows = []
    for fn in sorted(SOURCES):
        x, sr = read_wav(os.path.join(src, fn))
        x = resample(x, sr, OUT_SR)
        sr = OUT_SR
        peak = max(abs(v) for v in x)
        # onset: first sample above 3% of peak
        thr = 0.03 * peak
        onset = next(i for i, v in enumerate(x) if abs(v) > thr)
        start = max(0, onset - int(PRE_S * sr))
        seg = x[start:start + int((PRE_S + KEEP_S) * sr)]
        fin = int(0.002 * sr)
        for i in range(min(fin, len(seg))):
            seg[i] *= i / fin
        fout = int(FADE_S * sr)
        for i in range(fout):
            j = len(seg) - fout + i
            if 0 <= j < len(seg):
                t = 1.0 - i / fout
                seg[j] *= t * t
        pk = max(abs(v) for v in seg)
        g = 0.9 / pk if pk > 0 else 1.0
        seg = [v * g for v in seg]
        f0, conf = measure_f0(seg, sr)
        # nominal pitch from the filename, e.g. violin_G3_f / flute_C4
        note = next(p for p in fn[:-4].split("_") if p[0] in "ABCDEFG" and p[-1].isdigit())
        nominal = NOTE_HZ[note]
        # snap measured f0 to the nearest octave of the nominal note
        cand = min((nominal * 2 ** k for k in range(-2, 3)),
                   key=lambda c: abs(math.log(f0 / c)))
        cents = 1200 * math.log2(f0 / cand)
        root = f0 if abs(cents) < 60 else cand
        pcm = struct.pack(f"<{len(seg)}h",
                          *[max(-32768, min(32767, int(v * 32767))) for v in seg])
        with wave.open(os.path.join(DST, fn), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm)
        rows.append((fn, root, f0, cand, cents, conf, len(seg) / sr))
    print(f"{'file':26} {'root_hz':>9} {'measured':>9} {'nominal':>9} {'cents':>7} {'conf':>5} {'len_s':>6}")
    for r in rows:
        print(f"{r[0]:26} {r[1]:9.2f} {r[2]:9.2f} {r[3]:9.2f} {r[4]:7.1f} {r[5]:5.2f} {r[6]:6.3f}")


if __name__ == "__main__":
    sys.exit(main())
