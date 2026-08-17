#!/usr/bin/env python3
"""Bake or verify the GM 120 fret-noise round-robin bank (stdlib + NumPy).

Input : samples/fret-noise-eastman-e1d/cuts/fret_rrNN.wav  (24-bit, 48 kHz, mono)
Output: crates/ferrosintesis-samples-fretnoise/samples/fretnoise_rrNN.flac
        (16-bit, 44.1 kHz, mono — losslessly FLAC-compressed, which parse_wav
        decodes; the PCM is exactly what a WAV bank held)

The set of NN is DISCOVERED from the cuts directory, never hard-coded: the cuts are
the authoritative inventory, so adding a 13th cut bakes a 13th take instead of being
silently ignored. The ordinals must run contiguously from 01 (a hole would renumber
the round-robin slots against the crate's committed table), which `discover_cuts`
asserts.

Steps, per file:
  1. resample 48 kHz -> 44.1 kHz (band-limited, FFT method — no scipy on this box)
  2. loudness-EQUALISE across the round-robin set: scale each take so its body RMS
     hits a common target, so cycling takes does not jump in level. Peak is guarded
     to <= 0.95 so no take clips after resampling ripple.
  3. TPDF dither to 16-bit (two independent uniforms, +-1 LSB), the repo's dither.

Byte identity is scoped to the canonical Windows x86-64 environment declared by
CANONICAL_* below and requirements-fretnoise-bake.txt, and the pins are over the
16-bit PCM rather than the FLAC container, so an ffmpeg upgrade cannot invalidate
them (see `bake_payloads`). ``--verify`` bakes entirely in memory, checks every
generated and committed SHA-256, and never writes an asset.
The committed cuts are authoritative (the Downloads masters live outside the repo).

Run from the repo (worktree) root:
    python tools/ferrosintesis-samples/fretnoise_bake.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import platform
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

SRC_SR = 48000
DST_SR = 44100
CUT_RE = re.compile(r"^fret_rr(\d{2})\.wav$")
# Common body-RMS target for the round-robin set. Chosen so the loudest take lands
# just under full scale after resampling; the actual GM 120 output level is set in
# the synth (FRETNOISE_LEVEL), not here — this only EQUALISES takes to each other.
TARGET_BODY_RMS = 0.16
PEAK_GUARD = 0.95
DITHER_SEED = 0x5F58_0120  # SFX seed base ^ 120, matches the voice's seed idiom
CANONICAL_PYTHON = (3, 14, 3)
CANONICAL_NUMPY = "2.4.4"
CANONICAL_PLATFORM = "win32"
CANONICAL_MACHINE = "AMD64"
PIN_RE = re.compile(r"^([0-9a-f]{64})  (fretnoise_rr\d{2}\.flac)$")


def wav_from_pcm(pcm: bytes, sr: int = DST_SR) -> bytes:
    """Wrap raw 16-bit mono PCM in a canonical 44-byte RIFF/WAVE header."""
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE" + b"fmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16)
            + b"data" + struct.pack("<I", len(pcm)) + pcm)


def encode_flac(pcm: bytes, destination: Path) -> None:
    """Encode raw PCM to FLAC via ffmpeg, and prove the PCM survived."""
    wav = destination.with_suffix(".part.wav")
    try:
        wav.write_bytes(wav_from_pcm(pcm))
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(wav),
             "-c:a", "flac", "-compression_level", "12", "-f", "flac",
             str(destination)],
            check=True)
    finally:
        if wav.exists():
            wav.unlink()
    if decode_flac_pcm(destination) != pcm:
        raise SystemExit(f"{destination.name}: FLAC encode was not bit-exact")


def decode_flac_pcm(path: Path) -> bytes:
    """The raw 16-bit PCM inside a committed bank file."""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-f", "s16le", "-acodec", "pcm_s16le", "-"],
        stdout=subprocess.PIPE, check=True).stdout


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "crates" / "ferrosintesis").is_dir():
            return p
    raise SystemExit("run from inside the ferrosintesis repo/worktree")


def discover_cuts(src_dir: Path) -> list[int]:
    """The source cuts' ordinals, ascending — the bank's authoritative inventory.

    Requires them to run contiguously from 01. The crate embeds the outputs in
    ordinal order and indexes them positionally (`take_name`), so a hole would
    shift every later round-robin slot; and a stray non-conforming name is a
    mistake worth failing on rather than skipping.
    """
    if not src_dir.is_dir():
        raise SystemExit(f"missing source cuts directory {src_dir}")
    ordinals, strays = [], []
    for p in sorted(src_dir.iterdir()):
        if p.suffix.lower() != ".wav":
            continue
        m = CUT_RE.match(p.name)
        if m is None:
            strays.append(p.name)
        else:
            ordinals.append(int(m.group(1)))
    if strays:
        raise SystemExit(f"{src_dir}: unexpected cut name(s) {strays} (want fret_rrNN.wav)")
    if not ordinals:
        raise SystemExit(f"{src_dir}: no fret_rrNN.wav cuts found")
    ordinals.sort()
    if ordinals != list(range(1, len(ordinals) + 1)):
        raise SystemExit(
            f"{src_dir}: cut ordinals must be contiguous from 01, got {ordinals}"
        )
    return ordinals


def canonical_environment_errors(
    python_version: tuple[int, int, int] | None = None,
    implementation: str | None = None,
    numpy_version: str | None = None,
    platform_name: str | None = None,
    machine: str | None = None,
) -> list[str]:
    """Why this process is outside the one environment that owns byte identity."""
    python_version = python_version or tuple(sys.version_info[:3])
    implementation = implementation or sys.implementation.name
    numpy_version = numpy_version or np.__version__
    platform_name = platform_name or sys.platform
    machine = machine or platform.machine()
    errors = []
    if implementation != "cpython":
        errors.append(f"Python implementation {implementation!r}, want 'cpython'")
    if python_version != CANONICAL_PYTHON:
        errors.append(f"Python {python_version}, want {CANONICAL_PYTHON}")
    if numpy_version != CANONICAL_NUMPY:
        errors.append(f"NumPy {numpy_version}, want {CANONICAL_NUMPY}")
    if platform_name != CANONICAL_PLATFORM:
        errors.append(f"platform {platform_name!r}, want {CANONICAL_PLATFORM!r}")
    if machine.casefold() != CANONICAL_MACHINE.casefold():
        errors.append(f"machine {machine!r}, want {CANONICAL_MACHINE!r}")
    return errors


def require_canonical_environment() -> None:
    errors = canonical_environment_errors()
    if errors:
        detail = "\n  ".join(errors)
        raise SystemExit(
            "fret-noise byte identity belongs to the canonical bake environment:\n"
            f"  {detail}\n"
            "Create it from tools/ferrosintesis-samples/"
            "requirements-fretnoise-bake.txt."
        )


def load_output_pins(path: Path) -> dict[str, str]:
    """Read a strict sha256sum-style manifest with no duplicate output names."""
    pins: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_RE.fullmatch(line)
        if match is None:
            raise SystemExit(f"{path}:{line_no}: malformed SHA-256 pin {raw!r}")
        digest, name = match.groups()
        if name in pins:
            raise SystemExit(f"{path}:{line_no}: duplicate SHA-256 pin for {name}")
        pins[name] = digest
    if not pins:
        raise SystemExit(f"{path}: no fret-noise output pins")
    return pins


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


def bake_payloads(src_dir: Path) -> list[tuple[str, bytes, float, float, float, float]]:
    """Generate every output in memory before any tracked file can be replaced.

    The payload is the raw 16-bit PCM, and that is deliberately what gets pinned.
    The bank ships as FLAC, and pinning the FLAC BYTES would tie this oracle to
    one ffmpeg build: a version bump that changed a block-size heuristic would
    fail every pin while the audio was untouched. The PCM is what this script's
    DSP determines, so pinning it keeps the guarantee we actually want -- a
    re-bake reproduces the same audio -- and survives an encoder upgrade.
    """
    ordinals = discover_cuts(src_dir)
    # One shared RNG consumed sequentially, so every file's dither depends on the
    # total sample count of all its predecessors — the ordinal order below is what
    # keeps a re-bake byte-identical.
    rng = np.random.default_rng(DITHER_SEED)
    payloads = []
    for i in ordinals:
        src = src_dir / f"fret_rr{i:02d}.wav"
        x, sr, _bits = read_wav(src)
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
        payloads.append(
            (
                f"fretnoise_rr{i:02d}.flac",
                pcm.tobytes(),
                rms,
                20 * np.log10(gain),
                20 * np.log10(float(np.abs(y).max()) + 1e-12),
                len(y) / DST_SR * 1000,
            )
        )
    return payloads


def output_pin_errors(
    payloads: list[tuple[str, bytes, float, float, float, float]],
    pins: dict[str, str],
    out_dir: Path | None = None,
    read_committed=decode_flac_pcm,
) -> list[str]:
    """Check generated pins and, for verification, the committed output files.

    `read_committed` extracts the PCM a committed file holds, and is injected so
    the verifier can be unit-tested on synthetic payloads without an encoder.
    Both sides are compared as PCM, which is what the pins record.
    """
    generated = {name: payload for name, payload, *_ in payloads}
    errors = []
    for name in sorted(set(generated) - set(pins)):
        errors.append(f"{name}: generated output has no SHA-256 pin")
    for name in sorted(set(pins) - set(generated)):
        errors.append(f"{name}: pinned output was not generated")
    if out_dir is not None:
        committed_names = {path.name for path in out_dir.glob("fretnoise_rr*.flac")}
        for name in sorted(committed_names - set(pins)):
            errors.append(f"{name}: committed output has no SHA-256 pin")
    for name in sorted(set(generated) & set(pins)):
        digest = hashlib.sha256(generated[name]).hexdigest()
        if digest != pins[name]:
            errors.append(f"{name}: generated sha256 {digest} != pinned {pins[name]}")
        if out_dir is not None:
            committed = out_dir / name
            if not committed.is_file():
                errors.append(f"{name}: committed output is missing")
            else:
                digest = hashlib.sha256(read_committed(committed)).hexdigest()
                if digest != pins[name]:
                    errors.append(f"{name}: committed sha256 {digest} != pinned {pins[name]}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="bake in memory and verify generated + committed SHA-256 values; write nothing",
    )
    args = parser.parse_args(argv)

    root = find_repo_root(Path(__file__).resolve())
    src_dir = root / "samples" / "fret-noise-eastman-e1d" / "cuts"
    crate_dir = root / "crates" / "ferrosintesis-samples-fretnoise"
    out_dir = crate_dir / "samples"
    pins = load_output_pins(crate_dir / "BAKE-SHA256")
    require_canonical_environment()
    payloads = bake_payloads(src_dir)

    errors = output_pin_errors(payloads, pins, out_dir if args.verify else None)
    if errors:
        print("fret-noise bake verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    print(f"{'file':>18} {'src rms':>8} {'gain':>7} {'peak':>7} {'ms':>6}  sha256")
    for name, payload, rms, gain_db, peak_db, ms in payloads:
        digest = hashlib.sha256(payload).hexdigest()
        print(
            f"{name:>18} {rms:>8.4f} {gain_db:>+6.1f}dB "
            f"{peak_db:>+6.1f}dB {ms:>5.0f}  {digest}"
        )

    total_bytes = sum(len(payload) for _, payload, *_ in payloads)
    if args.verify:
        print(
            f"\nverified {len(payloads)} generated and committed files "
            f"({total_bytes / 1024:.0f} KiB); wrote nothing"
        )
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, payload, *_ in payloads:
        encode_flac(payload, out_dir / name)
    print(f"\nbaked {len(payloads)} files, {total_bytes / 1024:.0f} KiB total, into {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
