#!/usr/bin/env python3
"""Audio-side oracles for the cathedral-organ showcase.

Usage:
    python analyze.py <full-mix.wav> <organ-solo.wav>
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import sys


def read_wav(path: Path) -> tuple[int, list[tuple[float, float]]]:
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(f"{path} is not RIFF/WAVE")
    position = 12
    fmt = None
    pcm = None
    while position + 8 <= len(data):
        name = data[position:position + 4]
        size = struct.unpack("<I", data[position + 4:position + 8])[0]
        payload = data[position + 8:position + 8 + size]
        position += 8 + size + (size & 1)
        if name == b"fmt ":
            fmt = payload
        elif name == b"data":
            pcm = payload
    if fmt is None or pcm is None:
        raise ValueError(f"{path} lacks fmt/data chunks")
    audio_format, channels, rate, _byte_rate, block, bits = struct.unpack("<HHIIHH", fmt[:16])
    if audio_format != 1 or channels != 2 or bits != 16:
        raise ValueError(f"{path} must be stereo 16-bit PCM")
    frames = []
    for index in range(0, len(pcm) - block + 1, block):
        left, right = struct.unpack("<hh", pcm[index:index + 4])
        frames.append((left / 32768.0, right / 32768.0))
    return rate, frames


def window(
    frames: list[tuple[float, float]], rate: int, start: float, end: float
) -> list[tuple[float, float]]:
    return frames[max(0, int(start * rate)):min(len(frames), int(end * rate))]


def rms(frames: list[tuple[float, float]]) -> float:
    if not frames:
        return 0.0
    return math.sqrt(sum((left * left + right * right) * 0.5 for left, right in frames) / len(frames))


def peak(frames: list[tuple[float, float]]) -> float:
    return max((max(abs(left), abs(right)) for left, right in frames), default=0.0)


def dc(frames: list[tuple[float, float]]) -> float:
    if not frames:
        return 0.0
    return max(
        abs(sum(left for left, _right in frames) / len(frames)),
        abs(sum(right for _left, right in frames) / len(frames)),
    )


def mono_loss_db(frames: list[tuple[float, float]]) -> float:
    stereo = rms(frames)
    if stereo <= 1e-12:
        return 0.0
    mono = math.sqrt(sum(((left + right) * 0.5) ** 2 for left, right in frames) / len(frames))
    return 20.0 * math.log10(stereo / max(1e-12, mono))


def hf_proxy(frames: list[tuple[float, float]]) -> float:
    if len(frames) < 2:
        return 0.0
    energy = 0.0
    for (left0, right0), (left1, right1) in zip(frames, frames[1:]):
        energy += ((left1 - left0) ** 2 + (right1 - right0) ** 2) * 0.5
    return math.sqrt(energy / (len(frames) - 1))


def max_step(frames: list[tuple[float, float]]) -> float:
    return max(
        (max(abs(left1 - left0), abs(right1 - right0))
         for (left0, right0), (left1, right1) in zip(frames, frames[1:])),
        default=0.0,
    )


def goertzel_amplitude(frames: list[tuple[float, float]], rate: int, frequency: float) -> float:
    if not frames:
        return 0.0
    coefficient = 2.0 * math.cos(2.0 * math.pi * frequency / rate)
    previous = 0.0
    previous2 = 0.0
    for left, right in frames:
        sample = (left + right) * 0.5
        current = sample + coefficient * previous - previous2
        previous2, previous = previous, current
    power = max(0.0, previous2 * previous2 + previous * previous - coefficient * previous * previous2)
    return 2.0 * math.sqrt(power) / len(frames)


def modulation_index(frames: list[tuple[float, float]], rate: int, frequency: float) -> float:
    block = max(1, rate // 100)
    envelope = []
    for start in range(0, len(frames) - block + 1, block):
        envelope.append(rms(frames[start:start + block]))
    mean = sum(envelope) / max(1, len(envelope))
    if mean <= 1e-12:
        return 0.0
    envelope_rate = rate / block
    coefficient = 2.0 * math.cos(2.0 * math.pi * frequency / envelope_rate)
    previous = 0.0
    previous2 = 0.0
    for sample in envelope:
        current = (sample - mean) + coefficient * previous - previous2
        previous2, previous = previous, current
    power = max(0.0, previous2 * previous2 + previous * previous - coefficient * previous * previous2)
    amplitude = 2.0 * math.sqrt(power) / max(1, len(envelope))
    return amplitude / mean


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit("usage: python analyze.py <full-mix.wav> <organ-solo.wav>")
    full_path, organ_path = map(Path, argv)
    album_root = Path(__file__).resolve().parent
    manifest = json.loads((album_root / "album_manifest.json").read_text(encoding="utf-8"))
    windows = manifest["tracks"][0]["audio_windows"]
    full_rate, full = read_wav(full_path)
    organ_rate, organ = read_wav(organ_path)
    if full_rate != organ_rate:
        raise SystemExit(f"sample-rate mismatch: {full_rate} vs {organ_rate}")
    rate = full_rate

    def segment(name: str, source: list[tuple[float, float]] = organ):
        item = windows[name]
        return window(source, rate, item["start_seconds"], item["end_seconds"])

    failures: list[str] = []
    duration = len(full) / rate
    expected = float(manifest["tracks"][0]["duration_seconds"])
    if duration + 0.25 < expected:
        failures.append(f"full mix is {duration:.2f}s, shorter than the {expected:.2f}s score")
    for name, frames in (("full mix", full), ("organ solo", organ)):
        if rms(frames) < 0.004:
            failures.append(f"{name} is nearly silent: RMS {rms(frames):.6f}")
        if peak(frames) > 1.0001:
            failures.append(f"{name} clips: peak {peak(frames):.4f}")
        if dc(frames) > 0.03:
            failures.append(f"{name} DC offset is {dc(frames):.4f}")
        if mono_loss_db(frames) > 3.0:
            failures.append(f"{name} loses {mono_loss_db(frames):.2f} dB in mono")
        if max_step(frames) > 0.95:
            failures.append(f"{name} has a suspicious {max_step(frames):.3f} sample step")

    pedal = segment("pedal")
    pedal_tones = sum(goertzel_amplitude(pedal, rate, frequency)
                      for frequency in (16.35, 32.70, 65.41))
    pedal_ratio = pedal_tones / max(1e-12, rms(pedal))
    if pedal_tones < 0.003 or pedal_ratio < 0.12:
        failures.append(
            f"32-foot pedal is not materially present: tones={pedal_tones:.5f}, ratio={pedal_ratio:.3f}"
        )

    principals = segment("principals")
    mixtures = segment("mixtures")
    principal_brightness = hf_proxy(principals) / max(1e-12, rms(principals))
    mixture_brightness = hf_proxy(mixtures) / max(1e-12, rms(mixtures))
    if mixture_brightness < principal_brightness * 1.08:
        failures.append(
            f"mixture brightness {mixture_brightness:.4f} does not clear principals "
            f"{principal_brightness:.4f}"
        )

    trem_off = modulation_index(segment("tremulant_off"), rate, 5.5)
    trem_on = modulation_index(segment("tremulant_on"), rate, 5.5)
    if trem_on < 0.005 or trem_on < trem_off * 1.35:
        failures.append(f"5.5 Hz tremulant contrast is weak: off={trem_off:.4f}, on={trem_on:.4f}")

    loaded = segment("wind_loaded")
    recovered = segment("wind_recovery")
    if rms(loaded) < rms(recovered) * 1.4:
        failures.append(
            f"ten-note wind-chest plenum is not distinct: loaded={rms(loaded):.4f}, "
            f"recovery={rms(recovered):.4f}"
        )

    climax = segment("climax", full)
    if rms(climax) < rms(segment("principals", full)) * 1.5:
        failures.append("full-organ climax does not materially exceed the principal walk")

    tail_early = rms(segment("tail_early", full))
    tail_late = rms(segment("tail_late", full))
    tail_floor = rms(segment("tail_floor", full))
    if tail_early < 0.0001:
        failures.append(f"cathedral tail disappears too soon: early RMS {tail_early:.7f}")
    if not (tail_early > tail_late * 1.25 and tail_late > tail_floor * 1.10):
        failures.append(
            f"room tail does not decay in stages: early={tail_early:.7f}, "
            f"late={tail_late:.7f}, floor={tail_floor:.7f}"
        )

    print(f"duration                 {duration:.2f}s")
    print(f"full / organ RMS         {rms(full):.5f} / {rms(organ):.5f}")
    print(f"peak / mono loss         {peak(full):.4f} / {mono_loss_db(full):.2f} dB")
    print(f"32-foot tone ratio       {pedal_ratio:.3f}")
    print(f"principal / mixture HF   {principal_brightness:.4f} / {mixture_brightness:.4f}")
    print(f"tremulant off / on       {trem_off:.4f} / {trem_on:.4f}")
    print(f"wind loaded / recovered  {rms(loaded):.5f} / {rms(recovered):.5f}")
    print(f"tail early/late/floor    {tail_early:.7f} / {tail_late:.7f} / {tail_floor:.7f}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(f"RESULT: FAIL - {len(failures)} audio oracle(s)")
    print("RESULT: PASS - organ and full-mix audio oracles green")


if __name__ == "__main__":
    main(sys.argv[1:])
