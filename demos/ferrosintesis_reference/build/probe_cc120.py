#!/usr/bin/env python3
"""probe_cc120.py — does CC120 + zero sends actually leave a silent gap?

The HLD's single most load-bearing claim (§3.6): emitting CC120 (All Sound Off) at
the end of a slot, with CC91/93/94 all zero, makes the inter-slot gap genuinely
silent — which is what lets the `silent` audio oracle pass at all.

Doubts this probe must settle, because CC120 chokes VOICES but the mix has state
downstream of them:
  1. The piano (GM 0-3) and guitar (GM 24/25) SYMPATHETIC RESONATORS are fed from
     the post-gain strip signal, NOT from a CC send — CC91/93/94 = 0 cannot silence
     them, and they are combs with 0.85 feedback. Do they ring past the choke?
  2. Long-decay voices (koto t60 7.0s, pads) — does choke really drop them?
  3. Without the dry CCs, does the echo bus tail bleed into the gap (the review's
     CRITICAL R1)?

Renders three cases and measures RMS in windows after the choke.
Run from the album dir with a built ../../target/release/ferrosintesis.
"""
from __future__ import annotations
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALBUM = HERE.parent
REPO = ALBUM.parent.parent
sys.path.insert(0, str(REPO / "demos" / "synth_feature_showcase"))
import engine as en  # noqa: E402

SYNTH = REPO / "target" / "release" / ("ferrosintesis.exe" if sys.platform == "win32" else "ferrosintesis")

BPM = 120.0          # 1 beat = 0.5 s
CHOKE_BEAT = 8.0     # CC120 lands here -> t = 4.0 s
END_BEAT = 28.0      # 14 s total, so 10 s of gap to inspect


def build(name: str, program: int, dry: bool) -> Path:
    """One loud chord, then CC120 at CHOKE_BEAT, then a long empty tail."""
    sc = en.Score(seed=1, title=name, tempo=BPM, beats=END_BEAT)
    sc.timesig(0.0, 4, 4)
    # channel() emits CC7/CC10/CC91/CC93/CC94 and the program change.
    sc.channel(0, "probe", program, volume=110, pan=64, reverb=0 if dry else 50,
               chorus=0 if dry else 60, echo=0 if dry else 60)
    if dry:
        # Belt and braces: re-author the three sends AFTER the program change,
        # exactly as the HLD's slot shape mandates (a PC re-derives non-zero
        # chorus/echo from fx_profile, so channel()'s values alone are not enough
        # if anything re-programs the channel later).
        sc.cc(0, 91, 0, 0.05)
        sc.cc(0, 93, 0, 0.06)
        sc.cc(0, 94, 0, 0.07)
    for p in (48, 55, 60, 64, 67):          # a loud, wide, ringing chord
        sc.note(0, p, 0.5, 6.0, 118, jt=0, jv=0)
    sc.cc(0, 120, 0, CHOKE_BEAT)            # ALL SOUND OFF
    path = HERE / f"probe_{name}.mid"
    sc.write(path, title=name)
    return path


def render(mid: Path) -> Path:
    wav = mid.with_suffix(".wav")
    subprocess.run([str(SYNTH), str(mid), "-o", str(wav), "-q"], check=True)
    return wav


def rms(wav: Path, t0: float, t1: float) -> float:
    with wave.open(str(wav), "rb") as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        raw = w.readframes(n)
    a, b = max(0, int(t0 * sr)), min(n, int(t1 * sr))
    if b <= a:
        return 0.0
    tot = 0.0
    for i in range(a, b):
        for c in range(ch):
            s = struct.unpack_from("<h", raw, (i * ch + c) * 2)[0] / 32768.0
            tot += s * s
    return math.sqrt(tot / ((b - a) * ch))


def db(x: float) -> str:
    return "-inf " if x <= 0 else f"{20 * math.log10(x):6.1f}"


CHOKE_S = CHOKE_BEAT * 60.0 / BPM

CASES = [
    ("piano_dry", 0, True),      # sympathetic resonator, dry
    ("koto_dry", 107, True),     # t60 7.0 s, dry
    ("lead_wet", 81, False),     # echo bus (fx_profile 80-87 -> 0.25 echo), NOT dry
]

if not SYNTH.exists():
    raise SystemExit(f"no synth at {SYNTH}; cargo build --release -p ferrosintesis-cli")

print(f"choke at t={CHOKE_S:.1f}s   (RMS, dBFS)\n")
print(f"{'case':<12} {'pre-choke':>10} {'+0.05..0.30':>12} {'+0.30..1.00':>12} {'+1.00..2.00':>12} {'+2.00..6.00':>12}")
for name, prog, dry in CASES:
    wav = render(build(name, prog, dry))
    cells = [
        rms(wav, CHOKE_S - 1.0, CHOKE_S - 0.05),
        rms(wav, CHOKE_S + 0.05, CHOKE_S + 0.30),
        rms(wav, CHOKE_S + 0.30, CHOKE_S + 1.00),
        rms(wav, CHOKE_S + 1.00, CHOKE_S + 2.00),
        rms(wav, CHOKE_S + 2.00, CHOKE_S + 6.00),
    ]
    print(f"{name:<12} " + " ".join(f"{db(c):>12}" for c in cells))

print("\nVERDICT: for the HLD's ~1.2 s gap to be silent, the dry cases must be deep")
print("into the floor by +0.30..1.00 s. The wet case shows what CC91/93/94=0 prevents.")
