#!/usr/bin/env python3
"""Audio-side checks for rendered synth feature showcase WAVs."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import sys

import engine as en


def read_wav(path: Path) -> tuple[int, list[tuple[float, float]]]:
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(f"{path} is not a RIFF/WAVE file")
    pos = 12
    fmt = None
    pcm = None
    while pos + 8 <= len(data):
        name = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        payload = data[pos + 8:pos + 8 + size]
        pos += 8 + size + (size & 1)
        if name == b"fmt ":
            fmt = payload
        elif name == b"data":
            pcm = payload
    if fmt is None or pcm is None:
        raise ValueError(f"{path} missing fmt/data chunks")
    audio_fmt, channels, rate, _byte_rate, block, bits = struct.unpack("<HHIIHH", fmt[:16])
    if audio_fmt != 1 or channels != 2 or bits != 16:
        raise ValueError(f"{path} must be 16-bit PCM stereo")
    frames = []
    for i in range(0, len(pcm) - block + 1, block):
        l, r = struct.unpack("<hh", pcm[i:i + 4])
        frames.append((l / 32768.0, r / 32768.0))
    return rate, frames


def window(frames: list[tuple[float, float]], rate: int, start: float, end: float):
    lo = max(0, int(start * rate))
    hi = min(len(frames), int(end * rate))
    return frames[lo:hi]


def rms(frames: list[tuple[float, float]]) -> float:
    if not frames:
        return 0.0
    return (sum((l * l + r * r) * 0.5 for l, r in frames) / len(frames)) ** 0.5


def peak(frames: list[tuple[float, float]]) -> float:
    return max((max(abs(l), abs(r)) for l, r in frames), default=0.0)


def dc(frames: list[tuple[float, float]]) -> float:
    if not frames:
        return 0.0
    return max(abs(sum(l for l, _r in frames) / len(frames)), abs(sum(r for _l, r in frames) / len(frames)))


def hf_proxy(frames: list[tuple[float, float]]) -> float:
    if len(frames) < 2:
        return 0.0
    acc = 0.0
    for (l0, r0), (l1, r1) in zip(frames, frames[1:]):
        dl = l1 - l0
        dr = r1 - r0
        acc += (dl * dl + dr * dr) * 0.5
    return (acc / (len(frames) - 1)) ** 0.5


def mono_loss_db(frames: list[tuple[float, float]]) -> float:
    stereo = rms(frames)
    if stereo <= 1e-12:
        return 0.0
    mono_frames = [((l + r) * 0.5, (l + r) * 0.5) for l, r in frames]
    mono = rms(mono_frames)
    if mono <= 1e-12:
        return 99.0
    import math

    return 20.0 * math.log10(stereo / mono)


def check_track(track: dict, wav_dir: Path) -> list[str]:
    wav = wav_dir / Path(track["file"]).with_suffix(".wav").name
    fails = []
    if not wav.exists():
        return [f"{wav} missing"]
    rate, frames = read_wav(wav)
    dur = len(frames) / rate
    if dur + 0.25 < float(track["duration_seconds"]):
        fails.append(f"{wav.name} duration {dur:.1f}s shorter than MIDI {track['duration_seconds']}")
    if rms(frames) < 0.005:
        fails.append(f"{wav.name} is nearly silent")
    if peak(frames) > 1.0001:
        fails.append(f"{wav.name} clips: peak {peak(frames):.3f}")
    if dc(frames) > 0.03:
        fails.append(f"{wav.name} DC offset {dc(frames):.3f}")
    loss = mono_loss_db(frames)
    if loss > 3.0:
        fails.append(f"{wav.name} mono downmix loss {loss:.2f} dB")
    q = dur / 4.0
    segs = [rms(window(frames, rate, i * q, (i + 1) * q)) for i in range(4)]
    if max(segs) < segs[0] * 1.12:
        fails.append(f"{wav.name} dynamic arc too flat: {segs}")
    for check in track.get("audio_checks", []):
        got = window(frames, rate, check["start_seconds"], check["end_seconds"])
        ref = None
        if check.get("ref_start_seconds") is not None:
            ref = window(frames, rate, check["ref_start_seconds"], check["ref_end_seconds"])
        kind = check["kind"]
        threshold = float(check["threshold"])
        if kind == "rms_up" and ref is not None and rms(got) < threshold * max(1e-9, rms(ref)):
            fails.append(f"{wav.name} {check['name']} RMS delta too small")
        elif kind == "hf_up" and ref is not None and hf_proxy(got) < threshold * max(1e-9, hf_proxy(ref)):
            fails.append(f"{wav.name} {check['name']} HF delta too small")
        elif kind == "hf_down" and ref is not None and hf_proxy(got) > threshold * max(1e-9, hf_proxy(ref)):
            fails.append(f"{wav.name} {check['name']} HF did not drop")
        elif kind == "mono_loss" and mono_loss_db(got) > threshold:
            fails.append(f"{wav.name} {check['name']} mono loss {mono_loss_db(got):.2f} dB")
        elif kind not in {"rms_up", "hf_up", "hf_down", "mono_loss"}:
            fails.append(f"{wav.name} {check['name']} unknown audio check kind {kind}")
    return fails


def main(argv: list[str]) -> None:
    wav_dir = Path(argv[0]) if argv else en.WAV_DIR
    manifest = json.loads((en.ALBUM_ROOT / "album_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for track in manifest["tracks"]:
        fails = check_track(track, wav_dir)
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{track['number']:02d} {track['title']:<28} {status}")
        for fail in fails:
            print(f"    - {fail}")
        failures.extend(fails)
    if failures:
        print(f"\nRESULT: FAIL - {len(failures)} failure(s)")
        raise SystemExit(1)
    print("\nRESULT: PASS - audio checks green")


if __name__ == "__main__":
    main(sys.argv[1:])
