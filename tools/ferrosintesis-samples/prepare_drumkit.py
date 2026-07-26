"""Rebuild the sampled drum-kit banks.

The core kit lands in ``ferrosintesis-samples-drumkit``. The crash, sizzle
crash, splash and china banks land in the size-capped companion crate
``ferrosintesis-samples-drumkit2``.

Sources (both CC0 1.0 Universal, verified from each repo's LICENSE file):
- github.com/sfzinstruments/virtuosity_drums @ VIRTUOSITY_REV — a stick-played
  contemporary jazz kit; this bank takes the `mid` mic set (the balanced mono-
  friendly mid position) for most of the kit — snare (center, snares-off,
  cross-stick), hi/low toms, ride bow + bell, crash, sizzle crash, hi-hat
  closed/open/pedal, and the hi-hat splash. The KICK alone comes from the
  `kickmic` close-mic set (same 4x4 snares-on grid, same velocity splits):
  the overhead `mid` position barely captures the kick's sub — its
  sub(30-70 Hz)/mid(140-400 Hz) spectral-density ratio reads ~0.04-1.0
  across the layers, i.e. boxy — while the close mic carries the low end.
- github.com/sfzinstruments/karoryfer.big-rusty-drums @ BIG_RUSTY_REV — the
  18" china (stick articulation, `oh` overhead mic; Virtuosity has no china).

Velocity-layer splits and round-robin counts below were parsed from the source
repos' SFZ mappings (Programs/mappings/mid/*.sfz and
Programs/mappings/china_18/cn_oh.sfz), not guessed.

Two source shapes exist. The cymbals and the kick have TRUE round robins
(`..._vl{L}_rr{R}.flac`, `BANKS` below). The snare/toms/sidestick instead have
DEEP velocity layering with no round robins (36/16/16 single-take layers);
embedding all of them would bloat the crate, so `PSEUDO_RR_BANKS` picks a
subset of target layers and maps ADJACENT source velocity layers onto the
round-robin slots — distinct recorded takes within ~10 velocity points of
each other, timbrally near-identical once the pipeline peak-normalizes every
file (the synth applies velocity gain itself), so they cycle exactly like
true round robins.

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
MICSET = "mid"      # Virtuosity mic position for the kit bank (kick: kickmic)
CHINA_MIC = "oh"    # Big Rusty overhead mic — closest match to Virtuosity's mid

OUT_SR = 44100
PRE_S = 0.008      # pad kept before the onset
FADE_IN_S = 0.002  # fade-in applied at the segment start
PEAK = 0.9         # peak-normalization target (bank convention)

CORE_PACKAGE = "ferrosintesis-samples-drumkit"
ACCENT_PACKAGE = "ferrosintesis-samples-drumkit2"
OUTPUT_PACKAGES = (CORE_PACKAGE, ACCENT_PACKAGE)

# package, stem, vel layers, round robins, keep_s, fade_s, hivel per layer,
# source URL pattern ({vl}/{rr} are 1-based). hivel values come from the SFZ
# mappings; the last layer always runs to 127.
BANKS = [
    (CORE_PACKAGE, "ride", 3, 4, 1.2, 0.30, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/ride/{MICSET}_ride_ride_vl{{vl}}_rr{{rr}}.flac"),
    (CORE_PACKAGE, "ridebell", 3, 3, 1.2, 0.30, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/ride/{MICSET}_ride_bell_vl{{vl}}_rr{{rr}}.flac"),
    (ACCENT_PACKAGE, "crash", 3, 4, 2.8, 0.35, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/crash/{MICSET}_crash_crash_vl{{vl}}_rr{{rr}}.flac"),
    (ACCENT_PACKAGE, "sizzle", 3, 4, 2.8, 0.35, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/crash/{MICSET}_crash_sizzle_vl{{vl}}_rr{{rr}}.flac"),
    # the hi-hat splash has no velocity layers at the source (one full-range
    # layer, 4 RRs); it rings, so it gets the china-length tail cap
    (ACCENT_PACKAGE, "splash", 1, 4, 2.2, 0.35, (127,),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_splash_rr{{rr}}.flac"),
    (CORE_PACKAGE, "hhc", 4, 4, 1.2, 0.25, (31, 63, 95, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_closed_vl{{vl}}_rr{{rr}}.flac"),
    (CORE_PACKAGE, "hho", 4, 3, 1.2, 0.30, (31, 63, 95, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_open_vl{{vl}}_rr{{rr}}.flac"),
    (CORE_PACKAGE, "hhp", 3, 4, 1.2, 0.25, (42, 85, 127),
     f"{V_BASE}/Samples/{MICSET}/hh/{MICSET}_hh_pedal_vl{{vl}}_rr{{rr}}.flac"),
    (ACCENT_PACKAGE, "china", 5, 4, 2.2, 0.35, (25, 51, 76, 101, 127),
     f"{B_BASE}/Samples/china_18/cn/{CHINA_MIC}/cn_vl{{vl}}_rr{{rr}}.flac"),
    # kick, snares on, CLOSE MIC (kickmic_kick_snon): the source's full 4x4
    # grid, same velocity splits as the mid set — the close mic is the only
    # position that captures the kick's sub (see module docstring)
    (CORE_PACKAGE, "kick", 4, 4, 0.6, 0.15, (31, 63, 95, 127),
     f"{V_BASE}/Samples/kickmic/kick/kickmic_kick_snon_vl{{vl}}_rr{{rr}}.flac"),
]

# package, stem, keep_s, fade_s, hivel per target layer, vl_map, source URL
# pattern ({vl} is the SOURCE velocity layer, 1-based). vl_map[i][j] is the
# source velocity layer behind output take `<stem>_vl{i+1}_rr{j+1}.wav`: each
# target layer's round-robin slots are filled by adjacent source layers (see
# module docstring). Source layer counts/hivels parsed from the SFZ mappings:
#   snare_center      36 layers (hivel 3,7,10,...,127 — every ~3.5)
#   snareoff_center   12 layers (hivel 10,21,...,127 — every ~10.6)
#   snare_crossstick  16 layers (hivel 7,15,...,127 — every 8)
#   htom/ltom_center  16 layers (hivel 7,15,...,127 — every 8)
PSEUDO_RR_BANKS = [
    # 6 target layers x 3 takes from the 36: the top three source layers of
    # each 6-layer block (the block's loudest, most consistent takes)
    (CORE_PACKAGE, "snare", 0.6, 0.20, (21, 41, 63, 84, 105, 127),
     ((4, 5, 6), (10, 11, 12), (16, 17, 18),
      (22, 23, 24), (28, 29, 30), (34, 35, 36)),
     f"{V_BASE}/Samples/{MICSET}/snare/{MICSET}_snare_center_vl{{vl}}.flac"),
    # snares-off snare: all 12 source layers, 4 targets x 3 takes
    (CORE_PACKAGE, "snareoff", 0.6, 0.20, (32, 63, 95, 127),
     ((1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)),
     f"{V_BASE}/Samples/{MICSET}/snareoff/{MICSET}_snareoff_center_vl{{vl}}.flac"),
    # cross-stick (GM 37 side stick): quiet, timbrally stable — 3 targets
    (CORE_PACKAGE, "sidestick", 0.4, 0.10, (47, 87, 127),
     ((4, 5, 6), (9, 10, 11), (14, 15, 16)),
     f"{V_BASE}/Samples/{MICSET}/snare/{MICSET}_snare_crossstick_vl{{vl}}.flac"),
    (CORE_PACKAGE, "tomhi", 0.8, 0.25, (31, 63, 95, 127),
     ((2, 3, 4), (6, 7, 8), (10, 11, 12), (14, 15, 16)),
     f"{V_BASE}/Samples/{MICSET}/htom/{MICSET}_htom_center_vl{{vl}}.flac"),
    (CORE_PACKAGE, "tomlo", 0.8, 0.25, (31, 63, 95, 127),
     ((2, 3, 4), (6, 7, 8), (10, 11, 12), (14, 15, 16)),
     f"{V_BASE}/Samples/{MICSET}/ltom/{MICSET}_ltom_center_vl{{vl}}.flac"),
]

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TOOL_DIR, os.pardir, os.pardir))


def output_plan():
    """Return the complete, validated filename set owned by each package."""
    plans = {package: set() for package in OUTPUT_PACKAGES}
    stems = set()

    def add_bank(package, stem, names):
        if package not in plans:
            raise ValueError(f"unknown output package for {stem}: {package}")
        if stem in stems:
            raise ValueError(f"duplicate drum bank stem: {stem}")
        stems.add(stem)
        for name in names:
            if any(name in other for other in plans.values()):
                raise ValueError(f"drum output has multiple owners: {name}")
            plans[package].add(name)

    for package, stem, layers, rrs, _, _, vel_hi, _ in BANKS:
        if len(vel_hi) != layers or vel_hi[-1] != 127:
            raise ValueError(f"invalid velocity plan for {stem}")
        add_bank(
            package,
            stem,
            (
                f"{stem}_vl{vl}_rr{rr}.wav"
                for vl in range(1, layers + 1)
                for rr in range(1, rrs + 1)
            ),
        )

    for package, stem, _, _, vel_hi, vl_map, _ in PSEUDO_RR_BANKS:
        if len(vel_hi) != len(vl_map) or vel_hi[-1] != 127:
            raise ValueError(f"invalid velocity plan for {stem}")
        if not vl_map or not vl_map[0]:
            raise ValueError(f"empty take plan for {stem}")
        rrs = len(vl_map[0])
        if any(len(row) != rrs for row in vl_map):
            raise ValueError(f"inconsistent round-robin plan for {stem}")
        add_bank(
            package,
            stem,
            (
                f"{stem}_vl{vl}_rr{rr}.wav"
                for vl in range(1, len(vl_map) + 1)
                for rr in range(1, rrs + 1)
            ),
        )

    empty = [package for package, names in plans.items() if not names]
    if empty:
        raise ValueError(f"output packages have no owned banks: {', '.join(empty)}")
    return plans


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


def prepare_take(ffmpeg, cache, url, out_path, keep_s, fade_s):
    """Fetch, decode, trim, normalize and write one take; bytes written.

    The download cache is keyed by the source URL's basename (which encodes
    the mic set and articulation), never the output name — re-pointing a bank
    at a different mic set must re-fetch, not silently reuse the old mic's
    audio from the cache.
    """
    cache_stem = os.path.splitext(os.path.basename(url))[0]
    flac = os.path.join(cache, f"{cache_stem}.flac")
    if not os.path.exists(flac):
        print(f"fetching {cache_stem}.flac ...", file=sys.stderr)
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
    part = out_path + ".part"
    try:
        with wave.open(part, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm)
        os.replace(part, out_path)
    except Exception:
        if os.path.exists(part):
            os.remove(part)
        raise
    out_name = os.path.basename(out_path)
    print(f"{out_name:22} {src_sr:>6} {ch:>2} "
          f"{len(seg) / sr:6.3f} {PEAK:5.2f} {rms:6.3f}")
    return 44 + len(pcm)


def generate_staged(ffmpeg, cache, staging_root, plans):
    """Generate the complete kit under staging_root; do not touch the crates."""
    for package in OUTPUT_PACKAGES:
        os.makedirs(os.path.join(staging_root, package), exist_ok=True)
    print(f"{'file':22} {'src_sr':>6} {'ch':>2} {'len_s':>6} {'peak':>5} {'rms':>6}")
    total_bytes = 0
    for package, stem, layers, rrs, keep_s, fade_s, _, url_fmt in BANKS:
        for vl in range(1, layers + 1):
            for rr in range(1, rrs + 1):
                name = f"{stem}_vl{vl}_rr{rr}.wav"
                total_bytes += prepare_take(
                    ffmpeg, cache, url_fmt.format(vl=vl, rr=rr),
                    os.path.join(staging_root, package, name), keep_s, fade_s)
    for package, stem, keep_s, fade_s, _, vl_map, url_fmt in PSEUDO_RR_BANKS:
        for li, row in enumerate(vl_map, start=1):
            for ri, src_vl in enumerate(row, start=1):
                name = f"{stem}_vl{li}_rr{ri}.wav"
                total_bytes += prepare_take(
                    ffmpeg, cache, url_fmt.format(vl=src_vl),
                    os.path.join(staging_root, package, name), keep_s, fade_s)

    for package, expected in plans.items():
        actual = {
            name
            for name in os.listdir(os.path.join(staging_root, package))
            if name.endswith(".wav")
        }
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise RuntimeError(
                f"incomplete staged inventory for {package}: "
                f"missing={missing}, extra={extra}"
            )
    return total_bytes


def publish_staged(staging_root, repo_root, plans):
    """Atomically replace each destination WAV after every bank is staged."""
    pending = []
    try:
        for package, expected in plans.items():
            out_dir = os.path.join(repo_root, "crates", package, "samples")
            os.makedirs(out_dir, exist_ok=True)
            existing = {
                name for name in os.listdir(out_dir) if name.endswith(".wav")
            }
            unexpected = existing - expected
            if unexpected:
                raise RuntimeError(
                    f"{package} contains outputs not owned by the plan: "
                    f"{sorted(unexpected)}"
                )
            for name in sorted(expected):
                source = os.path.join(staging_root, package, name)
                destination = os.path.join(out_dir, name)
                part = destination + ".part"
                shutil.copyfile(source, part)
                pending.append((part, destination))

        # All generated bytes are safely copied before any tracked WAV changes.
        for part, destination in pending:
            os.replace(part, destination)
    finally:
        for part, _ in pending:
            if os.path.exists(part):
                os.remove(part)


def regenerate(ffmpeg, cache, repo_root=REPO_ROOT):
    """Stage the whole two-package kit, then publish it."""
    plans = output_plan()
    with tempfile.TemporaryDirectory(prefix="drumkit_staging_") as staging_root:
        total_bytes = generate_staged(ffmpeg, cache, staging_root, plans)
        publish_staged(staging_root, repo_root, plans)
    return plans, total_bytes


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

    plans, total_bytes = regenerate(ffmpeg, cache)
    n = sum(len(names) for names in plans.values())
    destinations = ", ".join(
        f"{package} ({len(plans[package])})" for package in OUTPUT_PACKAGES
    )
    print(
        f"\n{n} files, {total_bytes / (1024 * 1024):.2f} MiB written: "
        f"{destinations}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
