#!/usr/bin/env python3
"""Render-side checks for the fourteen *Atlas of Becoming* WAV files.

Render the MIDI files with ferrosintesis into one directory, preserving stems,
then run ``python analyze.py <wav-directory>``. The scanner checks section
audibility, interior digital silence, headroom, dynamic contrast, and mono
compatibility. WAV files are disposable and are not part of the album source.
"""

from __future__ import annotations

import argparse
import array
import json
import math
from pathlib import Path
import sys
import wave

FULL_SCALE = 32768.0


def db(value: float) -> float:
    return -120.0 if value <= 0 else 20.0 * math.log10(value / FULL_SCALE)


def load_wav(path: Path) -> tuple[array.array, array.array, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2:
            raise ValueError(f"need 16-bit stereo, got {wav.getnchannels()}ch/{wav.getsampwidth() * 8}bit")
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder == "big":
        samples.byteswap()
    return samples[0::2], samples[1::2], rate


def rms(left: array.array, right: array.array, lo: int, hi: int, stride: int = 1) -> float:
    lo = max(0, lo)
    hi = min(len(left), hi)
    if hi <= lo:
        return 0.0
    total = 0.0
    count = 0
    for index in range(lo, hi, stride):
        total += left[index] * left[index] + right[index] * right[index]
        count += 2
    return math.sqrt(total / max(1, count))


def analyze_track(entry: dict[str, object], path: Path) -> list[str]:
    left, right, rate = load_wav(path)
    failures: list[str] = []
    stride = max(1, rate // 4000)
    overall = rms(left, right, 0, len(left), stride)
    mono_energy = 0.0
    mono_count = 0
    for index in range(0, len(left), stride):
        value = (left[index] + right[index]) * 0.5
        mono_energy += value * value
        mono_count += 1
    mono = math.sqrt(mono_energy / max(1, mono_count))
    mono_loss = db(overall) - db(mono)
    peak = max(max(map(abs, left)), max(map(abs, right))) if left else 0

    if db(overall) < -36.0:
        failures.append(f"overall level {db(overall):.1f} dBFS is too quiet")
    if mono_loss > 3.0:
        failures.append(f"mono sum loses {mono_loss:.2f} dB (cap 3.0 dB)")
    if peak >= 32767:
        failures.append("render reaches integer full scale")

    sections = entry.get("sections", [])
    section_levels: list[tuple[str, float]] = []
    duration = len(left) / rate
    for index, section in enumerate(sections):
        start = float(section["start_seconds"])
        end = float(sections[index + 1]["start_seconds"]) if index + 1 < len(sections) else duration
        # Skip the first/last 100 ms to avoid measuring only a seam transient.
        value = rms(left, right, int((start + 0.1) * rate), int(max(start + 0.2, end - 0.1) * rate), stride)
        section_levels.append((str(section["name"]), db(value)))
        if db(value) < -48.0:
            failures.append(f"section {section['name']!r} is effectively silent at {db(value):.1f} dBFS")
    if section_levels:
        values = [value for _name, value in section_levels]
        if max(values) - min(values) < 1.5:
            failures.append(f"section RMS range is only {max(values) - min(values):.1f} dB")

    block = max(1, rate // 2)
    silent_blocks = []
    threshold = int(FULL_SCALE * 10 ** (-62.0 / 20.0))
    for start in range(0, len(left), block):
        end = min(len(left), start + block)
        silent_blocks.append(
            max(map(abs, left[start:end]), default=0) < threshold
            and max(map(abs, right[start:end]), default=0) < threshold
        )
    run_start = None
    for index, silent in enumerate(silent_blocks + [False]):
        if silent and run_start is None:
            run_start = index
        elif not silent and run_start is not None:
            if index - run_start >= 2 and index < len(silent_blocks):
                failures.append(f"interior digital silence from {run_start * 0.5:.1f}s to {index * 0.5:.1f}s")
            run_start = None

    levels = " | ".join(f"{name} {value:.1f}" for name, value in section_levels)
    print(f"{path.name}: {duration:.1f}s, RMS {db(overall):.1f} dBFS, peak {db(peak):.1f} dBFS, mono loss {mono_loss:.2f} dB")
    print(f"  sections: {levels}")
    for failure in failures:
        print(f"  FAIL: {failure}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_directory", type=Path)
    parser.add_argument("--track", type=int)
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).resolve().parent / "album_manifest.json").read_text("utf-8"))
    failures: list[str] = []
    tracks = manifest["tracks"]
    if args.track is not None:
        tracks = [entry for entry in tracks if entry["number"] == args.track]
        if not tracks:
            raise SystemExit(f"no track {args.track}")
    for entry in tracks:
        wav = args.wav_directory / f"{Path(entry['file']).stem}.wav"
        if not wav.exists():
            failures.append(f"missing {wav}")
            print(f"FAIL: missing {wav}")
            continue
        try:
            failures.extend(f"{wav.name}: {failure}" for failure in analyze_track(entry, wav))
        except (OSError, ValueError, wave.Error) as exc:
            failures.append(f"{wav.name}: {exc}")
            print(f"FAIL: {wav.name}: {exc}")
    print()
    print("AUDIO: " + (f"FAIL - {len(failures)} finding(s)" if failures else "PASS - all render checks green"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
