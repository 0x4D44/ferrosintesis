#!/usr/bin/env python3
"""Regenerate the FluidR3 differential goldens for the natural-pluck redesign.

For each (program, key, vel) in the HLD §5 D-grid this renders ONE isolated note
through FluidSynth + FluidR3_GM (reverb AND chorus disabled — a DRY reference)
and extracts five attack-side metrics whose definitions mirror the Rust testutil
helpers (att/sus windows, onset tilt, crest, flatness, early/late energy). It
prints a paste-ready Rust `FLUIDR3_GOLDEN` const; the committed const is the
HERMETIC reference the Phase-2 D-oracle compares ferrosintesis against — no
fluidsynth runs at test time.

Stdlib only. FluidSynth 2.5.5; FluidR3_GM.sf2 SHA256
74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0 (see README).
Run:  python tools/pluck-attack/gen_fluidr3_golden.py
Paste the output into `FLUIDR3_GOLDEN` in crates/ferrosintesis/src/testutil.rs.
"""
import array
import math
import os
import struct
import subprocess
import sys
import tempfile
import wave

FLUIDSYNTH = os.environ.get(
    "FLUIDSYNTH",
    "/c/tools/fluidsynth/fluidsynth-v2.5.5-win10-x64-cpp11/bin/fluidsynth",
)
SOUNDFONT = os.environ.get(
    "FLUIDR3", "/c/tools/fluidsynth/soundfonts/FluidR3_GM.sf2"
)
SR = 44100

# HLD §5 D-grid: plucked GM programs × three keys × two velocities.
PROGRAMS = [24, 25, 32, 33, 45, 46]  # nylon, steel, ac.bass, fing.bass, pizz, harp
KEYS = [40, 52, 64]
VELS = [60, 100]

DIV = 480  # ticks/quarter at 120 bpm -> 960 ticks/s


def vlq(n):
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def write_smf(path, program, key, vel):
    """One note: program change at t=0, note-on at 0.25 s, 1.5 s gate."""
    trk = bytearray()
    trk += vlq(0) + bytes([0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20])  # 120 bpm
    trk += vlq(0) + bytes([0xC0, program & 0x7F])
    trk += vlq(240) + bytes([0x90, key, vel])  # note-on at 0.25 s
    trk += vlq(1440) + bytes([0x80, key, 0])  # note-off at 1.75 s
    trk += vlq(240) + bytes([0xFF, 0x2F, 0x00])
    hdr = b"MThd" + struct.pack(">IHHH", 6, 0, 1, DIV)
    mtrk = b"MTrk" + struct.pack(">I", len(trk)) + bytes(trk)
    with open(path, "wb") as f:
        f.write(hdr + mtrk)


def render(mid_path, wav_path):
    cmd = [
        FLUIDSYNTH, "-ni", "-R", "0", "-C", "0", "-g", "0.8",
        "-r", str(SR), "-F", wav_path, SOUNDFONT, mid_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def load(path):
    w = wave.open(path, "rb")
    ch, fr, n = w.getnchannels(), w.getframerate(), w.getnframes()
    a = array.array("h")
    a.frombytes(w.readframes(n))
    w.close()
    mono = [
        (a[i * ch] + (a[i * ch + 1] if ch > 1 else a[i * ch])) / 2.0 / 32768.0
        for i in range(n)
    ]
    return mono, fr


def rms(seg):
    return math.sqrt(sum(v * v for v in seg) / max(1, len(seg)))


def detect_onset(x, fr, t_expect=0.25, search=0.25):
    lo = max(0, int((t_expect - 0.02) * fr))
    hi = min(len(x), int((t_expect + search) * fr))
    if lo >= hi:
        return lo
    pk = max((abs(v) for v in x[lo:hi]), default=0.0)
    thr = 0.15 * pk
    for i in range(lo, hi):
        if abs(x[i]) >= thr:
            return i
    return lo


def dft_mag(seg, fr, freqs):
    n = len(seg)
    if n < 2:
        return [1e-12] * len(freqs)
    w = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    out = []
    for f in freqs:
        re = im = 0.0
        c = 2 * math.pi * f / fr
        for i in range(n):
            s = seg[i] * w[i]
            re += s * math.cos(c * i)
            im -= s * math.sin(c * i)
        out.append(math.sqrt(re * re + im * im) / n + 1e-12)
    return out


def metrics(x, fr, key):
    o = detect_onset(x, fr)
    f0 = 440.0 * 2 ** ((key - 69) / 12.0)
    att_end = max(0.015, 1.5 / f0)
    att = x[o : o + int(att_end * fr)]
    sus = x[o + int(0.10 * fr) : o + int(0.25 * fr)]
    a_rms, s_rms = rms(att), rms(sus)
    att_sus = a_rms / s_rms if s_rms > 1e-9 else 0.0
    # onset tilt: 48 log-spaced Hann-DFT probes over 300..9000 Hz, 20 ms window
    onset = x[o : o + int(0.020 * fr)]
    freqs = [300.0 * (9000.0 / 300.0) ** (i / 47.0) for i in range(48)]
    mag = dft_mag(onset, fr, freqs)
    logf = [math.log2(f) for f in freqs]
    logm = [20 * math.log10(m) for m in mag]
    nn = len(freqs)
    mf, mm = sum(logf) / nn, sum(logm) / nn
    cov = sum((logf[i] - mf) * (logm[i] - mm) for i in range(nn))
    var = sum((logf[i] - mf) ** 2 for i in range(nn))
    tilt = cov / var if var > 1e-9 else 0.0
    # crest over the attack window
    peak = max((abs(v) for v in att), default=0.0)
    crest = peak / a_rms if a_rms > 1e-9 else 0.0
    # flatness over the 20 ms onset, geo/arith over 500..8000 Hz
    ff = [500.0 * (8000.0 / 500.0) ** (i / 23.0) for i in range(24)]
    fm = dft_mag(onset, fr, ff)
    gm = math.exp(sum(math.log(m) for m in fm) / len(fm))
    am = sum(fm) / len(fm)
    flat = gm / am if am > 0 else 0.0
    # early/late energy ratio
    e_early = rms(x[o : o + int(0.030 * fr)])
    e_late = rms(x[o + int(0.10 * fr) : o + int(0.30 * fr)])
    e_ratio = e_early / e_late if e_late > 1e-9 else 0.0
    return att_sus, tilt, crest, flat, e_ratio


def main():
    for tool, path in (("fluidsynth", FLUIDSYNTH), ("soundfont", SOUNDFONT)):
        if not os.path.isfile(path):
            sys.exit(f"missing {tool}: {path}")
    tmp = tempfile.mkdtemp(prefix="fluidr3_golden_")
    rows = []
    for prog in PROGRAMS:
        for key in KEYS:
            for vel in VELS:
                mid = os.path.join(tmp, f"{prog}_{key}_{vel}.mid")
                wav = os.path.join(tmp, f"{prog}_{key}_{vel}.wav")
                write_smf(mid, prog, key, vel)
                render(mid, wav)
                x, fr = load(wav)
                rows.append((prog, key, vel, *metrics(x, fr, key)))
    print("    #[rustfmt::skip]")
    print("    const FLUIDR3_GOLDEN: &[(u8, u8, u8, f32, f32, f32, f32, f32)] = &[")
    print("        // (program, key, vel, att_sus, tilt_db_oct, crest, flatness, e030_e100300)")
    for prog, key, vel, a, t, c, fl, e in rows:
        print(f"        ({prog}, {key}, {vel}, {a:.2f}, {t:.1f}, {c:.2f}, {fl:.3f}, {e:.2f}),")
    print("    ];")


if __name__ == "__main__":
    main()
