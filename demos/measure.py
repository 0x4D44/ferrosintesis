#!/usr/bin/env python3
"""measure.py — numeric characterization of the hollowsynth demo stems.

This machine has no ears, so we measure instead.  The headline test:
a sustained instrument (brass, oboe, bowed string) HOLDS its level across a
long note; a Karplus-Strong pluck DECAYS exponentially.  `sustain_ratio` =
RMS(late window) / RMS(early window) of a held note:  ~1.0 = it sustains,
<<1 = it decayed away like a pluck.  Also reports spectral centroid (Hz).
"""
from __future__ import annotations
import wave
from pathlib import Path
import numpy as np

D = Path(__file__).resolve().parent


def load_mono(path: Path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        raw = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
    if ch == 2:
        raw = raw.reshape(-1, 2).mean(axis=1)
    return raw / 32768.0, sr


def centroid(x, sr):
    if np.sqrt(np.mean(x**2)) < 1e-6:
        return 0.0
    win = x * np.hanning(len(x))
    mag = np.abs(np.rfft(win)) if hasattr(np, "rfft") else np.abs(np.fft.rfft(win))
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    s = mag.sum()
    return float((freqs * mag).sum() / s) if s > 0 else 0.0


def rms(x):
    return float(np.sqrt(np.mean(x**2))) if len(x) else 0.0


def held_note(x, sr, t0, dur):
    """sustain_ratio and centroid for a note starting ~t0 lasting dur secs."""
    a0, a1 = int((t0 + 0.15) * sr), int((t0 + 0.45) * sr)          # early
    b0, b1 = int((t0 + dur - 0.55) * sr), int((t0 + dur - 0.15) * sr)  # late
    early, late = x[a0:a1], x[b0:b1]
    r_e, r_l = rms(early), rms(late)
    ratio = r_l / r_e if r_e > 1e-7 else 0.0
    cseg = x[int((t0 + 0.1) * sr):int((t0 + dur - 0.1) * sr)]
    return ratio, centroid(cseg, sr), r_e, r_l


B = 60.0 / 74.0   # orchestral beat seconds
print("=" * 72)
print("ORCHESTRAL DEMO  (74 bpm, 1 beat = %.3fs)" % B)
print("=" * 72)
print("A held brass/oboe/bowed note should SUSTAIN (ratio ~1).  A pluck decays.\n")

orch_tests = [
    ("strings  ch0 (SawStack, modeled)", "orch_stem_ch0.wav", 4.0 * B, 3.0 * B),
    ("violin   ch1 (Bowed, modeled)",    "orch_stem_ch1.wav", (16 + 4) * B, 3.4 * B),
    ("violin   ch1 held A8",             "orch_stem_ch1.wav", (16 + 12) * B, 3.4 * B),
    ("choir    ch3 (SawStack+formant)",  "orch_stem_ch3.wav", (8 + 4) * B, 3.5 * B),
    ("BRASS    ch4 held A  (prog 61)",   "orch_stem_ch4.wav", (44 + 3) * B, 1.9 * B),
    ("BRASS    ch4 held E  (prog 61)",   "orch_stem_ch4.wav", (44 + 7) * B, 2.9 * B),
    ("OBOE     ch5 held C  (prog 68)",   "orch_stem_ch5.wav", (56 + 2) * B, 1.9 * B),
    ("OBOE     ch5 held A  (prog 68)",   "orch_stem_ch5.wav", (56 + 5) * B, 2.9 * B),
]
print(f"{'voice':38s} {'sustain':>8s} {'centroid':>9s}")
for label, fn, t0, dur in orch_tests:
    x, sr = load_mono(D / fn)
    ratio, cen, re, rl = held_note(x, sr, t0, dur)
    flag = "  <-- decays like a PLUCK" if ratio < 0.45 else ""
    print(f"{label:38s} {ratio:8.2f} {cen:8.0f}Hz{flag}")

print()
print("=" * 72)
print("GUITAR / BASS DEMO")
print("=" * 72)
for label, fn in [("distortion lead ch1", "gb_stem_lead.wav"),
                  ("bass ch3", "gb_stem_bass.wav")]:
    x, sr = load_mono(D / fn)
    # crest factor: distortion compresses peaks -> low crest; clean pluck -> high
    peak = float(np.max(np.abs(x)))
    crest = peak / rms(x) if rms(x) > 0 else 0
    # spectral balance
    win = x * np.hanning(len(x))
    mag = np.abs(np.fft.rfft(win))
    fr = np.fft.rfftfreq(len(x), 1 / sr)
    lo = mag[(fr < 120)].sum()
    mid = mag[(fr >= 120) & (fr < 2000)].sum()
    hi = mag[(fr >= 2000)].sum()
    tot = lo + mid + hi + 1e-9
    print(f"\n{label} ({fn}):")
    print(f"  overall RMS {rms(x):.3f}  peak {peak:.3f}  crest {crest:.1f}  centroid {centroid(x, sr):.0f} Hz")
    print(f"  energy  <120Hz {100*lo/tot:4.1f}%   120-2k {100*mid/tot:4.1f}%   >2k {100*hi/tot:4.1f}%")

# full-mix loudness sanity
print("\n" + "=" * 72)
for fn in ["orchestral_demo.wav", "guitar_bass_demo.wav"]:
    x, sr = load_mono(D / fn)
    print(f"{fn:26s}  {len(x)/sr:5.1f}s  RMS {rms(x):.3f}  peak {np.max(np.abs(x)):.3f}")
