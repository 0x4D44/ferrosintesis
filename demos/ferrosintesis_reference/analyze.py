#!/usr/bin/env python3
"""Audio oracles for the rendered reference audition WAVs.

The payoff: prove every voice makes a sound, and that no voice masks the next.
Both are RATIOS, never absolute floors - the CLI peak-normalises the whole render
(engine.rs:2045), so an absolute level is globally coupled, and renders are not
bit-reproducible across machines (scratchpad.md). The per-slot grid is recomputed
from programs.py rather than stored in the manifest.

    python analyze.py [wav_dir]     # default: build/wav/
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import sys

import engine as en

import tracks
from tracks import MELODIC, BPM_MELODIC
from tracks.audition import SLOT_BEATS, onset_beat, _CHOKE_AT, _ONSET
import programs as pr

# Calibrated against a real render: the quietest legitimate voice is GM 125 Helicopter
# at -40.8 dB rel global peak (the SFX noises 120-127 are intentionally quiet). A -50 dB
# floor clears it by 9 dB (margin) yet sits 46 dB above the render's ~-96 dBFS dither
# floor, so it separates "makes a sound" from a silent regression. Worst inter-slot gap
# measured at -29 dB rel slot, so -24 dB is a comfortable unmasked bar. Both are ratios,
# so peak-normalisation (engine.rs:2045) and cross-machine drift cancel out.
AUDIBLE_REL_DB = -50.0     # a slot's peak must be within 50 dB of the render's global peak
UNMASKED_REL_DB = -24.0    # the 0.25 s before a slot must be 24 dB under that slot's own peak
PRE_WINDOW_S = 0.25


def read_wav(path: Path):
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(f"{path} is not a RIFF/WAVE file")
    pos, fmt, pcm = 12, None, None
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
    audio_fmt, channels, rate, _br, _bl, bits = struct.unpack("<HHIIHH", fmt[:16])
    if audio_fmt != 1 or channels != 2 or bits != 16:
        raise ValueError(f"{path} must be 16-bit PCM stereo")
    n = len(pcm) // 4
    frames = [struct.unpack_from("<hh", pcm, i * 4) for i in range(n)]
    frames = [(l / 32768.0, r / 32768.0) for l, r in frames]
    return rate, frames


def _slice(frames, rate, t0, t1):
    return frames[max(0, int(t0 * rate)):min(len(frames), int(t1 * rate))]


def rms(fr):
    return (sum((l * l + r * r) * 0.5 for l, r in fr) / len(fr)) ** 0.5 if fr else 0.0


def peak(fr):
    return max((max(abs(l), abs(r)) for l, r in fr), default=0.0)


def dc(fr):
    if not fr:
        return 0.0
    return max(abs(sum(l for l, _ in fr) / len(fr)), abs(sum(r for _, r in fr) / len(fr)))


def db(ratio: float) -> float:
    return 20.0 * math.log10(ratio) if ratio > 1e-12 else -120.0


def check_common(name: str, frames) -> list[str]:
    fails = []
    if peak(frames) > 1.0001:
        fails.append(f"{name} clips: peak {peak(frames):.3f}")
    if dc(frames) > 0.03:
        fails.append(f"{name} DC offset {dc(frames):.3f}")
    return fails


def check_melodic(num: int, name: str, frames, rate: int) -> list[str]:
    """audible: each slot's peak within AUDIBLE_REL_DB of the global peak.
    unmasked: the 0.25 s before each onset is >= UNMASKED_REL_DB under the slot's peak."""
    fails = []
    lo, hi = MELODIC[num]
    slots = pr.melodic_slots(lo, hi)
    gpeak = peak(frames)
    if gpeak <= 1e-9:
        return [f"{name} is silent"]
    b2s = 60.0 / BPM_MELODIC
    for i, slot in enumerate(slots):
        onset = onset_beat(i) * b2s
        choke = (i * SLOT_BEATS + _CHOKE_AT) * b2s
        active = _slice(frames, rate, onset, choke)
        speak = peak(active)
        if db(speak / gpeak) < AUDIBLE_REL_DB:
            fails.append(f"{name} {slot.label}: peak {db(speak / gpeak):.1f} dB rel global < {AUDIBLE_REL_DB}")
        pre = _slice(frames, rate, onset - PRE_WINDOW_S, onset)
        if speak > 1e-9 and db(rms(pre) / speak) > UNMASKED_REL_DB:
            fails.append(f"{name} {slot.label}: pre-onset {db(rms(pre) / speak):.1f} dB rel slot > {UNMASKED_REL_DB} (tail bleed)")
        if len(fails) >= 8:
            fails.append(f"{name}: (further slot failures suppressed)")
            break
    return fails


def main(argv: list[str]) -> None:
    wav_dir = Path(argv[0]) if argv else en.WAV_DIR
    manifest = json.loads((en.ALBUM_ROOT / "album_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for track in manifest["tracks"]:
        num = track["number"]
        wav = wav_dir / Path(track["file"]).with_suffix(".wav").name
        name = f"{num:02d} {track['title']}"
        if not wav.exists():
            fails = [f"{wav} missing"]
        else:
            rate, frames = read_wav(wav)
            fails = check_common(wav.name, frames)
            if num in MELODIC:
                fails += check_melodic(num, wav.name, frames, rate)
            elif rms(frames) < 0.0005:   # T5/T6: a loose non-silence smoke test only
                fails.append(f"{wav.name} is silent")
        status = "PASS" if not fails else f"FAIL ({len(fails)})"
        print(f"{name:<32} {status}")
        for f in fails:
            print(f"    - {f}")
        failures.extend(fails)
    print()
    if failures:
        print(f"RESULT: FAIL - {len(failures)} failure(s)")
        raise SystemExit(1)
    print("RESULT: PASS - audio checks green")


if __name__ == "__main__":
    main(sys.argv[1:])
