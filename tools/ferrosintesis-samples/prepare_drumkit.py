"""Rebuild the sampled-cymbal drum-kit bank (crates/ferrosintesis-samples-drumkit).

Sources (both CC0 1.0 Universal, verified from each repo's LICENSE file):
- github.com/sfzinstruments/virtuosity_drums @ VIRTUOSITY_REV — a stick-played
  contemporary jazz kit; this bank takes the `mid` mic set (the balanced mono-
  friendly mid position): ride bow + bell, crash, sizzle crash, hi-hat
  closed/open/pedal, and the hi-hat splash.
- github.com/sfzinstruments/karoryfer.big-rusty-drums @ BIG_RUSTY_REV — the
  18" china (stick articulation, `oh` overhead mic; Virtuosity has no china).

Velocity-layer splits and round-robin counts below were parsed from the source
repos' SFZ mappings (Programs/mappings/mid/*.sfz and
Programs/mappings/china_18/cn_oh.sfz), not guessed.

The sources are FLAC; decoding shells out to ffmpeg (pcm_s24le, no resample —
FLAC decode is bit-exact, so the ffmpeg version does not affect output). All
audible processing happens here in stdlib Python, mirroring prepare.py: mono
downmix, linear resample to 44.1 kHz, onset trim (3% of peak, 8 ms pre-pad),
tail cap + squared fade-out, 2 ms fade-in, peak-normalize to 0.9, 16-bit WAV.

ffmpeg is a tool-time dependency only — the shipped synth consumes the plain
16-bit WAVs this script writes.

Run from the repository root:
    python tools/ferrosintesis-samples/prepare_drumkit.py
"""

import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import wave

from prepare import fetch, read_wav, resample

VIRTUOSITY_REV = "9f04cf9a734527edfbb0a4eee1f674e45bbf71bc"
BIG_RUSTY_REV = "f07ce00df34a46b6b08375be56fe116cf15782bc"
V_BASE = (
    "https://raw.githubusercontent.com/sfzinstruments/virtuosity_drums/"
    f"{VIRTUOSITY_REV}"
)
B_BASE = (
    "https://raw.githubusercontent.com/sfzinstruments/karoryfer.big-rusty-drums/"
    f"{BIG_RUSTY_REV}"
)
MICSET = "mid"      # Virtuosity mic position for the whole kit bank
CHINA_MIC = "oh"    # Big Rusty overhead mic — closest match to Virtuosity's mid

OUT_SR = 44100
PRE_S = 0.008      # pad kept before the onset
FADE_IN_S = 0.002  # fade-in applied at the segment start
PEAK = 0.9         # peak-normalization target (bank convention)

# stem, vel layers, round robins, keep_s, fade_s, hivel per layer, source URL
# pattern ({vl}/{rr} are 1-based). hivel values come from the SFZ mappings;
# the last layer always runs to 127.
BANKS = [
    ("ride", 3, 4, 1.2, 0.30, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/ride/{MICSET}_ride_ride_vl{{vl}}_rr{{rr}}.flac"),
    ("ridebell", 3, 3, 1.2, 0.30, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/ride/{MICSET}_ride_bell_vl{{vl}}_rr{{rr}}.flac"),
    ("crash", 3, 4, 2.8, 0.35, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/crash/{MICSET}_crash_crash_vl{{vl}}_rr{{rr}}.flac"),
    ("sizzle", 3, 4, 2.8, 0.35, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/crash/{MICSET}_crash_sizzle_vl{{vl}}_rr{{rr}}.flac"),
    # the hi-hat splash has no velocity layers at the source (one full-range
    # layer, 4 RRs); it rings, so it gets the china-length tail cap
    ("splash", 1, 4, 2.2, 0.35, (127,),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_splash_rr{{rr}}.flac"),
    ("hhc", 4, 4, 1.2, 0.25, (31, 63, 95, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_closed_vl{{vl}}_rr{{rr}}.flac"),
    ("hho", 4, 3, 1.2, 0.30, (31, 63, 95, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_open_vl{{vl}}_rr{{rr}}.flac"),
    ("hhp", 3, 4, 1.2, 0.25, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_pedal_vl{{vl}}_rr{{rr}}.flac"),
    ("china", 5, 4, 2.2, 0.35, (25, 51, 76, 101, 127),
     f"{B_BASE}/Samples/china_18/cn/{CHINA_MIC}/cn_vl{{vl}}_rr{{rr}}.flac"),
]

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TOOL_DIR, os.pardir, os.pardir))
OUT_DIR = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-drumkit", "samples")


def wav_info(path):
    """(channels, sample rate) of a WAV without decoding it."""
    with wave.open(path, "rb") as w:
        return w.getnchannels(), w.getframerate()


def decode_flac(ffmpeg, flac_path, wav_path):
    """FLAC -> 24-bit WAV at the native rate/channels (bit-exact decode)."""
    if os.path.exists(wav_path):
        try:
            wav_info(wav_path)
            return
        except (wave.Error, EOFError):
            os.remove(wav_path)
    part = wav_path + ".part.wav"
    if os.path.exists(part):
        os.remove(part)
    subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-i", flac_path, "-c:a", "pcm_s24le", part],
        check=True,
    )
    os.replace(part, wav_path)


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("error: ffmpeg not found on PATH (needed to decode the source "
              "FLACs; tool-time only)", file=sys.stderr)
        return 1
    socket.setdefaulttimeout(60)
    cache = os.path.join(
        tempfile.gettempdir(), "drumkit_src",
        f"{VIRTUOSITY_REV[:12]}_{BIG_RUSTY_REV[:12]}")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"{'file':22} {'src_sr':>6} {'ch':>2} {'len_s':>6} {'peak':>5} {'rms':>6}")
    total_bytes = 0
    for stem, layers, rrs, keep_s, fade_s, vel_hi, url_fmt in BANKS:
        assert len(vel_hi) == layers and vel_hi[-1] == 127
        for vl in range(1, layers + 1):
            for rr in range(1, rrs + 1):
                url = url_fmt.format(vl=vl, rr=rr)
                out_name = f"{stem}_vl{vl}_rr{rr}.wav"
                flac = os.path.join(cache, f"{stem}_vl{vl}_rr{rr}.flac")
                if not os.path.exists(flac):
                    print(f"fetching {out_name[:-4]}.flac ...", file=sys.stderr)
                    fetch(url, flac)
                dec = flac[:-5] + "_dec.wav"
                decode_flac(ffmpeg, flac, dec)
                ch, src_sr = wav_info(dec)
                x, sr = read_wav(dec)   # downmixes stereo to mono
                x = resample(x, sr, OUT_SR)
                sr = OUT_SR

                peak = max(abs(v) for v in x)
                thr = 0.03 * peak
                onset = next(i for i, v in enumerate(x) if abs(v) > thr)
                start = max(0, onset - int(PRE_S * sr))
                seg = x[start:start + int((PRE_S + keep_s) * sr)]
                fin = int(FADE_IN_S * sr)
                for i in range(min(fin, len(seg))):
                    seg[i] *= i / fin
                fout = int(fade_s * sr)
                for i in range(fout):
                    j = len(seg) - fout + i
                    if 0 <= j < len(seg):
                        t = 1.0 - i / fout
                        seg[j] *= t * t
                pk = max(abs(v) for v in seg)
                g = PEAK / pk if pk > 0 else 1.0
                seg = [v * g for v in seg]
                rms = math.sqrt(sum(v * v for v in seg) / len(seg))

                pcm = struct.pack(
                    f"<{len(seg)}h",
                    *[max(-32768, min(32767, int(v * 32767))) for v in seg])
                with wave.open(os.path.join(OUT_DIR, out_name), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(sr)
                    w.writeframes(pcm)
                total_bytes += 44 + len(pcm)
                print(f"{out_name:22} {src_sr:>6} {ch:>2} "
                      f"{len(seg) / sr:6.3f} {PEAK:5.2f} {rms:6.3f}")
    n = sum(layers * rrs for _, layers, rrs, *_ in BANKS)
    print(f"\n{n} files, {total_bytes / (1024 * 1024):.2f} MiB written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
