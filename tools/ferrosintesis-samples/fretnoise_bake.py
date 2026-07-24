#!/usr/bin/env python3
"""Bake the GM 120 fret-noise round-robin bank (stdlib + numpy).

Input : samples/fret-noise-eastman-e1d/cuts/fret_rr{01..12}.wav  (24-bit, 48 kHz, mono)
Output: crates/ferrosintesis-samples-fretnoise/samples/fretnoise_rr{01..12}.wav
        (16-bit, 44.1 kHz, mono — the format parse_wav / the drum path require)

Steps, per file:
  1. resample 48 kHz -> 44.1 kHz (band-limited, FFT method — no scipy on this box)
  2. loudness-EQUALISE across the round-robin set: scale each take so its body RMS
     hits a common target, so cycling takes does not jump in level. Peak is guarded
     to <= 0.95 so no take clips after resampling ripple.
  3. TPDF dither to 16-bit (two independent uniforms, +-1 LSB), the repo's dither.

Reproducible: fixed target, deterministic resample, seeded dither. A re-bake is
byte-identical. The committed cuts are the authoritative source (the Downloads
masters live outside the repo), exactly as the guitar's zones/ are.

Run from the repo (worktree) root:
    python tools/ferrosintesis-samples/fretnoise_bake.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

SRC_SR = 48000
DST_SR = 44100
N = 12
# Common body-RMS target for the round-robin set. Chosen so the loudest take lands
# just under full scale after resampling; the actual GM 120 output level is set in
# the synth (FRETNOISE_LEVEL), not here — this only EQUALISES takes to each other.
TARGET_BODY_RMS = 0.16
PEAK_GUARD = 0.95
DITHER_SEED = 0x5F58_0120  # SFX seed base ^ 120, matches the voice's seed idiom


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "crates" / "ferrosintesis").is_dir():
            return p
    raise SystemExit("run from inside the ferrosintesis repo/worktree")


def read_wav(path: Path) -> tuple[np.ndarray, int, int]:
    raw = path.read_bytes()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE", path
    pos, ch, sr, bits, pcm = 12, 1, SRC_SR, 24, b""
    while pos + 8 <= len(raw):
        cid = raw[pos : pos + 4]
        ln = struct.unpack("<I", raw[pos + 4 : pos + 8])[0]
        body = raw[pos + 8 : pos + 8 + ln]
        if cid == b"fmt ":
            ch = struct.unpack("<H", body[2:4])[0]
            sr = struct.unpack("<I", body[4:8])[0]
            bits = struct.unpack("<H", body[14:16])[0]
        elif cid == b"data":
            pcm = body
        pos += 8 + ln + (ln & 1)
    assert ch == 1, f"{path}: expected mono, got {ch} ch"
    if bits == 24:
        b = np.frombuffer(pcm, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v & 0x800000, v - 0x1000000, v).astype(np.float64) / 8388608.0
    elif bits == 16:
        v = np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0
    else:
        raise SystemExit(f"{path}: unsupported {bits}-bit")
    return v, sr, bits


def resample_fft(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    """Band-limited resample via real FFT (Fourier method). Exact for the 48->44.1
    ratio without designing a polyphase filter, and deterministic."""
    n_src = len(x)
    n_dst = int(round(n_src * dst / src))
    X = np.fft.rfft(x)
    # target spectrum length for n_dst samples
    n_keep = min(len(X), n_dst // 2 + 1)
    Y = np.zeros(n_dst // 2 + 1, dtype=complex)
    Y[:n_keep] = X[:n_keep]
    y = np.fft.irfft(Y, n_dst) * (n_dst / n_src)
    return y


def body_rms(x: np.ndarray, sr: int) -> float:
    """RMS over the loud body: frames within 20 dB of the peak envelope."""
    w = int(0.010 * sr)
    if len(x) < w:
        return float(np.sqrt(np.mean(x * x)))
    e = np.array([np.sqrt(np.mean(x[i : i + w] ** 2)) for i in range(0, len(x) - w, w)])
    thr = e.max() * 10 ** (-20 / 20)
    loud = np.concatenate([x[i * w : i * w + w] for i, v in enumerate(e) if v >= thr])
    return float(np.sqrt(np.mean(loud * loud)))


def tpdf_dither_16(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    d = (rng.random(len(x)) - rng.random(len(x)))  # triangular, +-1 LSB
    q = np.round(x * 32767.0 + d)
    return np.clip(q, -32768, 32767).astype("<i2")


def write_wav16(path: Path, pcm16: np.ndarray, sr: int = DST_SR) -> None:
    data = pcm16.tobytes()
    hdr = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
    hdr += struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16)
    hdr += b"data" + struct.pack("<I", len(data))
    path.write_bytes(hdr + data)


def main() -> int:
    root = find_repo_root(Path(__file__).resolve())
    src_dir = root / "samples" / "fret-noise-eastman-e1d" / "cuts"
    out_dir = root / "crates" / "ferrosintesis-samples-fretnoise" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(DITHER_SEED)
    total_bytes = 0
    print(f"{'file':>18} {'src rms':>8} {'gain':>7} {'peak':>7} {'ms':>6}")
    for i in range(1, N + 1):
        src = src_dir / f"fret_rr{i:02d}.wav"
        x, sr, bits = read_wav(src)
        assert sr == SRC_SR, f"{src}: expected {SRC_SR} Hz"
        y = resample_fft(x, SRC_SR, DST_SR)
        rms = body_rms(y, DST_SR)
        gain = TARGET_BODY_RMS / max(rms, 1e-9)
        # guard the peak
        pk = float(np.abs(y).max()) * gain
        if pk > PEAK_GUARD:
            gain *= PEAK_GUARD / pk
        y = y * gain
        pcm = tpdf_dither_16(y, rng)
        out = out_dir / f"fretnoise_rr{i:02d}.wav"
        write_wav16(out, pcm)
        total_bytes += out.stat().st_size
        print(f"{out.name:>18} {rms:>8.4f} {20*np.log10(gain):>+6.1f}dB "
              f"{20*np.log10(float(np.abs(y).max())+1e-12):>+6.1f}dB {len(y)/DST_SR*1000:>5.0f}")

    print(f"\nbaked {N} files, {total_bytes/1024:.0f} KiB total, into {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
