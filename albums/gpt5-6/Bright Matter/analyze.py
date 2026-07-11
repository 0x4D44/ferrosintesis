#!/usr/bin/env python3
"""Optional render-side checks for *Bright Matter* WAV files.

Render the committed MIDI with the repository's ferrosintesis binary, preserving
filename stems, then run:

    python analyze.py <wav-directory>
"""

from __future__ import annotations

from array import array
import argparse
import json
import math
from pathlib import Path
import sys
import wave

ALBUM_ROOT = Path(__file__).resolve().parent
MANIFEST = ALBUM_ROOT / "album_manifest.json"


def db(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-12))


def read_wav(path: Path) -> tuple[int, array]:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2:
            raise ValueError("expected 16-bit stereo PCM")
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    return rate, samples


def window_rms(samples: array, rate: int, start: float, end: float,
               stride: int = 4) -> float:
    frame0 = max(0, int(start * rate))
    frame1 = min(len(samples) // 2, int(end * rate))
    if frame1 <= frame0:
        return 0.0
    energy = 0.0
    count = 0
    for frame in range(frame0, frame1, stride):
        i = frame * 2
        left = samples[i] / 32768.0
        right = samples[i + 1] / 32768.0
        energy += 0.5 * (left * left + right * right)
        count += 1
    return math.sqrt(energy / max(1, count))


def stereo_and_mono_rms(samples: array, stride: int = 4) -> tuple[float, float]:
    stereo_energy = mono_energy = 0.0
    count = 0
    for i in range(0, len(samples) - 1, 2 * stride):
        left = samples[i] / 32768.0
        right = samples[i + 1] / 32768.0
        stereo_energy += 0.5 * (left * left + right * right)
        mono = 0.5 * (left + right)
        mono_energy += mono * mono
        count += 1
    return (
        math.sqrt(stereo_energy / max(1, count)),
        math.sqrt(mono_energy / max(1, count)),
    )


def analyze_track(path: Path, track: dict[str, object]) -> list[str]:
    failures: list[str] = []
    rate, samples = read_wav(path)
    if rate < 32000:
        failures.append(f"sample rate {rate} is unexpectedly low")
    peak = max(abs(value) for value in samples) / 32768.0
    if peak < 0.42:
        failures.append(f"peak {db(peak):.1f} dBFS is too quiet")
    if peak >= 0.99997:
        failures.append("render reaches digital full scale")

    stereo, mono = stereo_and_mono_rms(samples)
    mono_loss = db(stereo) - db(mono)
    if mono_loss > 3.0:
        failures.append(f"mono sum loses {mono_loss:.2f} dB")

    sections = list(track["sections"])
    duration = float(track["duration_seconds"])
    section_levels: list[tuple[str, float]] = []
    for index, section in enumerate(sections):
        start = float(section["start_seconds"]) + 1.0
        end = (float(sections[index + 1]["start_seconds"]) - 1.0
               if index + 1 < len(sections) else duration - 1.0)
        if end > start:
            section_levels.append(
                (str(section["name"]), db(window_rms(samples, rate, start, end)))
            )
    if section_levels:
        spread = max(level for _name, level in section_levels) - min(level for _name, level in section_levels)
        if spread < 5.5:
            failures.append(f"section dynamic spread is only {spread:.1f} dB")

    hush_names = ("Negative Space", "Cloud Deck", "Zero-G Choir", "Moonlit Delay", "Vacuum")
    hush_index = next((i for i, (name, _level) in enumerate(section_levels)
                       if any(token in name for token in hush_names)), None)
    if hush_index is not None and hush_index + 1 < len(section_levels):
        hush = section_levels[hush_index][1]
        return_level = section_levels[hush_index + 1][1]
        if return_level < hush + 3.0:
            failures.append(
                f"post-hush return is only {return_level - hush:.1f} dB above the hush"
            )

    silent_runs = 0
    worst_run = 0
    for second in range(2, max(2, int(duration) - 3)):
        level = window_rms(samples, rate, float(second), float(second + 1), stride=8)
        if level < 1e-5:
            silent_runs += 1
            worst_run = max(worst_run, silent_runs)
        else:
            silent_runs = 0
    if worst_run >= 2:
        failures.append(f"interior digital silence lasts {worst_run} seconds")

    return failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_directory", type=Path)
    parser.add_argument(
        "--allow-noncanonical-rate",
        action="store_true",
        help="do not fail audition renders below 32 kHz (canonical ferrosintesis is 44.1 kHz)",
    )
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total_failures = 0
    for track in manifest["tracks"]:
        stem = Path(track["file"]).stem
        path = args.wav_directory / f"{stem}.wav"
        if not path.exists():
            print(f"{stem:<44} MISSING")
            total_failures += 1
            continue
        try:
            failures = analyze_track(path, track)
            if args.allow_noncanonical_rate:
                failures = [f for f in failures if not f.startswith("sample rate ")]
        except (OSError, ValueError, wave.Error) as exc:
            failures = [str(exc)]
        print(f"{stem:<44} {'PASS' if not failures else f'FAIL ({len(failures)})'}")
        for failure in failures:
            print(f"    - {failure}")
        total_failures += len(failures)
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
