#!/usr/bin/env python3
"""banjo_extract.py — build the GM 105 banjo per-note sample bank from a real
5-string banjo recording.

This is the banjo's equivalent of `prepare.py`'s per-family bake, but the banjo does
NOT come from a URL fetch: it is a real instrument recorded note-by-note (see
`samples/banjo/`). This script turns that one take into the 24 trimmed onset WAVs the
synth embeds (`crates/ferrosintesis-samples-orchestral2/samples/banjo_*.wav`).

Pipeline (all stdlib + numpy; ffmpeg only to decode the source):
  1. decode the source recording to mono 44.1 kHz float (ffmpeg — reads .opus/.wav/…)
  2. onset-segment on a fast energy rise with a refractory gap
  3. per take: robust OCTAVE-CORRECT f0 (harmonic-sum estimate refined by autocorrelation),
     pitch-clarity, next-pluck-bleed ("contamination"), attack rolloff, clip count, room
  4. QC GATE — drop any take that is clipped, pitch-ambiguous, buzzy (low clarity),
     bleed-contaminated, too quiet, or too dull; keep the best surviving take per semitone
  5. extract: trim to the onset, keep ~0.5 s, peak-normalize to -1 dBFS, short fades,
     TPDF-dither to 16-bit PCM (seeded → deterministic)

The shipped WAVs were extracted from the ORIGINAL lossless take; `samples/banjo/*.opus`
is the space-saving archive of that take (Opus @160 kbps is transparent, so re-running
this on the archive reproduces the bank to within codec transparency). Roots are the
MEASURED sounding pitch, so the player's slightly-sharp fretting up the neck is captured
per-root and repitched back in tune by `LaVoice`.

Usage:
    python tools/ferrosintesis-samples/banjo_extract.py [SOURCE]
    (SOURCE defaults to samples/banjo/banjo-5string-openG-2026-07-23.opus)
"""
from __future__ import annotations
import math, os, struct, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "samples/banjo/banjo-5string-openG-2026-07-23.opus"
OUT = REPO / "crates/ferrosintesis-samples-orchestral2/samples"
SR = 44100
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BANJO_GLOB = "banjo_*.wav"
EXPECTED_BANJO_FILE_COUNT = 24
np.random.seed(1234)  # deterministic dither


def note_name(m: int) -> str:
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def note_freq(m: int) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def _quoted_fields(line: str) -> list[str]:
    return line.split('"')[1::2]


def _sample_crate_banjo_files(repo: Path = REPO) -> frozenset[str]:
    lib = repo / "crates/ferrosintesis-samples-orchestral2/src/lib.rs"
    names = set()
    for raw in lib.read_text(encoding="utf-8").splitlines():
        if "include_bytes!" not in raw:
            continue
        for field in _quoted_fields(raw):
            if field.startswith("banjo_") and field.endswith(".wav"):
                names.add(field)
    return frozenset(names)


def _sampler_banjo_files(repo: Path = REPO) -> frozenset[str]:
    sampler = repo / "crates/ferrosintesis/src/sampler.rs"
    names = set()
    for raw in sampler.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith('"banjo_') and '" =>' in line:
            names.add(_quoted_fields(line)[0])
    return frozenset(names)


def _format_names(names) -> str:
    return ", ".join(sorted(names)) if names else "<none>"


def expected_banjo_files(repo: Path = REPO) -> frozenset[str]:
    sample_crate = _sample_crate_banjo_files(repo)
    sampler = _sampler_banjo_files(repo)
    if sample_crate != sampler:
        raise RuntimeError(
            "banjo inventory mismatch between sample crate and sampler.rs; "
            f"only in sample crate: {_format_names(sample_crate - sampler)}; "
            f"only in sampler.rs: {_format_names(sampler - sample_crate)}")
    if len(sample_crate) != EXPECTED_BANJO_FILE_COUNT:
        raise RuntimeError(
            f"banjo regeneration expected {EXPECTED_BANJO_FILE_COUNT} files, "
            f"found {len(sample_crate)} in the checked-in bank inventory")
    return sample_crate


def decode_mono(path: Path) -> np.ndarray:
    """ffmpeg-decode any source to mono float32 @ 44.1 kHz."""
    ff = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"],
        stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(ff, dtype="<f4").astype(np.float64)


def onsets(y: np.ndarray) -> list[int]:
    hop, frame, look = 256, 512, 3
    e = np.array([np.sqrt(np.mean(y[i:i + frame] ** 2) + 1e-20)
                  for i in range(0, len(y) - frame, hop)])
    edb = 20 * np.log10(e + 1e-12)
    floor = np.percentile(edb, 20)
    out, last = [], -1e9
    for i in range(look, len(edb)):
        t = i * hop / SR
        if edb[i] - edb[i - look] > 6.0 and edb[i] > floor + 12 and (t - last) > 0.35:
            j = i
            while j > 0 and edb[j - 1] < edb[j]:
                j -= 1
            out.append(j * hop)
            last = t
    return sorted(set(out))


def ac_fft(sig):
    n = len(sig); s = (sig - sig.mean()) * np.hanning(n)
    F = np.fft.rfft(s, 2 * n)
    return np.fft.irfft(F * np.conj(F))[:n]


def hps(sig, fmin=120, fmax=1050):
    Y = np.abs(np.fft.rfft(sig * np.hanning(len(sig)))); L = len(sig); best = (0.0, 0.0)
    for cf in np.arange(fmin, fmax, 0.5):
        s = 0.0
        for h in range(1, 6):
            i = int(round(cf * h * L / SR))
            if 0 < i < len(Y):
                s += Y[i]
        if s > best[0]:
            best = (s, cf)
    return best[1]


def refine(ac, f_est):
    lo, hi = int(SR / (f_est * 1.06)), int(SR / (f_est * 0.94))
    if hi <= lo or hi >= len(ac):
        return f_est
    peak = lo + int(np.argmax(ac[lo:hi]))
    if 0 < peak < len(ac) - 1:
        a, b, c = ac[peak - 1], ac[peak], ac[peak + 1]; d = a - 2 * b + c
        if d != 0:
            peak += 0.5 * (a - c) / d
    return SR / peak if peak > 0 else f_est


def roll999(sig):
    Y = np.abs(np.fft.rfft(sig * np.hanning(len(sig)))) ** 2
    f = np.fft.rfftfreq(len(sig), 1 / SR); c = np.cumsum(Y); c /= c[-1] + 1e-20
    return f[np.searchsorted(c, 0.999)]


def contamination(sig):
    hop = 256
    env = np.array([np.sqrt(np.mean(sig[i:i + 512] ** 2) + 1e-20)
                    for i in range(0, len(sig) - 512, hop)])
    edb = 20 * np.log10(env + 1e-9); start = int(0.06 * SR / hop)
    if start >= len(edb):
        return 0.0
    rmin, r = edb[start], 0.0
    for v in edb[start:]:
        rmin = min(rmin, v); r = max(r, v - rmin)
    return r


def write_wav16(path, sig):
    d = np.random.random(len(sig)) - np.random.random(len(sig))  # TPDF, ±1 LSB
    x = np.clip(sig * 32767.0 + d, -32768, 32767).astype("<i2"); data = x.tobytes()
    hdr = (b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE" + b"fmt "
           + struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16)
           + b"data" + struct.pack("<I", len(data)))
    Path(path).write_bytes(hdr + data)


def validate_wav16_contract(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 44:
        raise RuntimeError(f"{path.name}: WAV is too short")
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE" or data[12:16] != b"fmt ":
        raise RuntimeError(f"{path.name}: not a canonical RIFF/WAVE file")
    riff_size = struct.unpack("<I", data[4:8])[0]
    if riff_size != len(data) - 8:
        raise RuntimeError(f"{path.name}: RIFF size does not match file length")
    fmt_size, audio_format, channels, sr, byte_rate, block_align, bits = struct.unpack(
        "<IHHIIHH", data[16:36])
    if (fmt_size, audio_format, channels, sr, byte_rate, block_align, bits) != (
            16, 1, 1, SR, SR * 2, 2, 16):
        raise RuntimeError(f"{path.name}: expected mono 16-bit PCM at {SR} Hz")
    if data[36:40] != b"data":
        raise RuntimeError(f"{path.name}: expected data chunk after fmt chunk")
    data_size = struct.unpack("<I", data[40:44])[0]
    if data_size == 0 or data_size % 2 or data_size != len(data) - 44:
        raise RuntimeError(f"{path.name}: data chunk size is invalid")


def validate_banjo_output_plan(staging: Path, repo: Path = REPO) -> frozenset[str]:
    expected = expected_banjo_files(repo)
    actual = {p.name for p in staging.glob(BANJO_GLOB)}
    if actual != expected:
        raise RuntimeError(
            "banjo regeneration produced the wrong file set; "
            f"missing: {_format_names(expected - actual)}; "
            f"unexpected: {_format_names(actual - expected)}")
    for name in sorted(expected):
        validate_wav16_contract(staging / name)
    return expected


def publish_banjo_bank(staging: Path, out: Path = OUT, expected=None) -> None:
    if expected is None:
        expected = validate_banjo_output_plan(staging)
    out.mkdir(parents=True, exist_ok=True)
    for name in sorted(expected):
        (staging / name).replace(out / name)
    for old in out.glob(BANJO_GLOB):
        if old.name not in expected:
            old.unlink()


def main():
    y = decode_mono(SRC)
    ons = onsets(y)
    N = len(y)
    takes = []
    for k, on in enumerate(ons):
        nxt = ons[k + 1] if k + 1 < len(ons) else N
        room = (nxt - on) / SR
        seg = y[on:min(nxt - int(0.02 * SR), on + int(3.0 * SR), N)]
        if len(seg) < int(0.30 * SR):
            continue
        pk = 20 * math.log10(np.max(np.abs(seg)) + 1e-20)
        if pk < -16:
            continue
        body = seg[int(0.03 * SR):int(0.35 * SR)]; ac = ac_fft(body)
        fh = hps(body); f0 = refine(ac, fh)
        fr = SR / (int(SR / 1100) + int(np.argmax(ac[int(SR / 1100):int(SR / 120)])))
        if not (140 <= f0 <= 1020):
            continue
        lag = int(round(SR / f0)); clar = ac[lag] / (ac[0] + 1e-20) if 0 < lag < len(ac) else 0.0
        cont = contamination(seg[:int(0.6 * SR)]); roll = roll999(seg[:int(0.08 * SR)])
        clip = int(np.sum(np.abs(seg) > 0.999))
        agree = abs(fr - f0) / f0 < 0.06
        if agree and clip == 0 and clar >= 0.60 and cont <= 7.0 and room >= 0.55 and roll >= 3000 and pk > -14:
            takes.append(dict(on=on, room=room, f0=f0, midi=round(69 + 12 * math.log2(f0 / 440)),
                              pk=pk, clar=clar, cont=cont, roll=roll))

    by = {}
    for t in takes:
        by.setdefault(t["midi"], []).append(t)

    def score(t):
        return t["clar"] * 3 + min(t["room"], 1.6) + t["roll"] / 6000 + (t["pk"] + 14) / 8 - t["cont"] / 6

    best = {m: max(v, key=score) for m, v in by.items()}
    zones = [m for m in sorted(best) if best[m]["clar"] >= 0.62]

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    with tempfile.TemporaryDirectory(prefix=".banjo-staging-", dir=OUT.parent) as stage_dir:
        staging = Path(stage_dir)
        for m in zones:
            t = best[m]; on = t["on"]; keep = max(0.40, min(0.50, t["room"] - 0.03))
            w0, w1 = max(0, on - int(0.008 * SR)), on + int(0.025 * SR)
            win = y[w0:w1]; lp = np.max(np.abs(win)) + 1e-9
            start = max(0, w0 + int(np.argmax(np.abs(win) > 0.02 * lp)) - int(0.003 * SR))
            clip = y[start:start + int(keep * SR)].astype(np.float64)
            clip = clip / (np.max(np.abs(clip)) + 1e-12) * 10 ** (-1 / 20)
            fo = int(0.012 * SR); clip[-fo:] *= np.linspace(1, 0, fo)
            fi = int(0.003 * SR); clip[:fi] *= np.linspace(0, 1, fi)
            name = f"banjo_{note_name(m)}.wav"
            write_wav16(staging / name, clip)
            written.append((name, t["f0"]))
        expected = validate_banjo_output_plan(staging)
        publish_banjo_bank(staging, OUT, expected)

    for name, root in written:
        print(f"{name}  root {root:.2f} Hz")
    print(f"\n{len(zones)} zones written to {OUT}")
    print("Remember to sync the bank!() roots in sampler.rs and the SAMPLES list in the crate lib.rs.")


if __name__ == "__main__":
    main()
