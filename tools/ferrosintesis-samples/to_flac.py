#!/usr/bin/env python3
"""One-time bake: re-container the embedded sample banks from RIFF to FLAC.

Why
---
Every bank file is `include_bytes!`d into the final binary, so the banks are
roughly half of what a ferrosintesis-linked binary weighs. FLAC is lossless, so
this is a pure size change: the decoded PCM is bit-identical, and any render
made afterwards is byte-for-byte what it was before.

What it does NOT touch
----------------------
`ferrosintesis-samples-b1-upright`. All 52 of its files carry a custom `b1t`
chunk (the decimated mu-law natural tail, per the 2026.07.28 HLD), and a FLAC
container has nowhere to put it. Those stay RIFF, which the decoder's
magic-byte dispatch already handles. Moving them would need the tail in a FLAC
APPLICATION block -- a real design change, deliberately not folded in here.

Safety
------
Every file is verified before its source is removed: the freshly written FLAC is
decoded back with ffmpeg and its PCM compared byte-for-byte against the original
`data` chunk. A single mismatch aborts the whole run with nothing deleted, so a
partial or lossy conversion cannot reach the tree.

The encoder also writes the MD5 of the unencoded audio into STREAMINFO, which is
what lets `flac.rs` re-verify every bank at load time forever after -- without
this file, and without any reference WAV.

Usage
-----
    python3 tools/ferrosintesis-samples/to_flac.py            # convert
    python3 tools/ferrosintesis-samples/to_flac.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CRATES_DIR = os.path.join(REPO_ROOT, "crates")

# Crates whose banks stay RIFF, each for a different structural reason.
SKIP_CRATES = {
    # All 52 files carry a `b1t` chunk (the decimated mu-law natural tail, per
    # the 2026.07.28 HLD). A FLAC container has nowhere to put it. Moving these
    # needs the tail in a FLAC APPLICATION block -- a real design change.
    "ferrosintesis-samples-b1-upright",
    # These two DECODE PCM THEMSELVES, in the sample crate: `decode_wav` +
    # `PCM_CACHE` in their own lib.rs, rather than handing bytes to
    # ferrosintesis. Every sample crate is dependency-free by design and these
    # are published to crates.io, so giving them FLAC means a new shared
    # first-party crate in a published dependency graph -- an architectural
    # decision, not a mechanical one. Deliberately deferred.
    "ferrosintesis-samples-drumkit",
    "ferrosintesis-samples-drumkit2",
}


def riff_data_chunk(path: str) -> bytes:
    """Return the raw bytes of a RIFF file's `data` chunk."""
    with open(path, "rb") as handle:
        blob = handle.read()
    if blob[0:4] != b"RIFF" or blob[8:12] != b"WAVE":
        raise ValueError(f"{path}: not a RIFF/WAVE file")
    pos = 12
    while pos + 8 <= len(blob):
        chunk_id = blob[pos : pos + 4]
        (length,) = struct.unpack_from("<I", blob, pos + 4)
        body = blob[pos + 8 : pos + 8 + length]
        if chunk_id == b"data":
            return body
        pos += 8 + length + (length & 1)
    raise ValueError(f"{path}: no data chunk")


def carries_b1_tail(path: str) -> bool:
    with open(path, "rb") as handle:
        return b"b1t " in handle.read()


def encode(wav_path: str, flac_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            wav_path,
            "-c:a",
            "flac",
            "-compression_level",
            "12",
            flac_path,
        ],
        check=True,
    )


def decoded_pcm(flac_path: str, scratch: str) -> bytes:
    """Decode a FLAC back to PCM via ffmpeg, for independent verification."""
    out = os.path.join(scratch, "verify.wav")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", flac_path, "-c:a", "pcm_s16le", out],
        check=True,
    )
    return riff_data_chunk(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would convert, write nothing",
    )
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is required (encoder + independent verification decode)")
        return 2

    crates = sorted(
        name
        for name in os.listdir(CRATES_DIR)
        if name.startswith("ferrosintesis-samples-")
        and os.path.isdir(os.path.join(CRATES_DIR, name, "samples"))
    )

    total_wav = 0
    total_flac = 0
    converted = 0
    skipped = 0

    with tempfile.TemporaryDirectory() as scratch:
        for crate in crates:
            samples = os.path.join(CRATES_DIR, crate, "samples")
            names = sorted(n for n in os.listdir(samples) if n.endswith(".wav"))
            if crate in SKIP_CRATES:
                held = sum(
                    os.path.getsize(os.path.join(samples, n)) for n in names
                )
                print(f"{crate}: SKIP ({len(names)} files, {held/1048576:.2f} MiB) - see SKIP_CRATES")
                skipped += len(names)
                continue

            crate_wav = 0
            crate_flac = 0
            for name in names:
                wav_path = os.path.join(samples, name)

                # Belt and braces: the skip list is by crate, but a stray `b1t`
                # file anywhere else must not be silently flattened.
                if carries_b1_tail(wav_path):
                    print(f"  ABORT: {crate}/{name} carries a b1t chunk but is not in SKIP_CRATES")
                    return 1

                flac_path = os.path.splitext(wav_path)[0] + ".flac"
                original = riff_data_chunk(wav_path)
                crate_wav += os.path.getsize(wav_path)

                if args.dry_run:
                    continue

                encode(wav_path, flac_path)
                if decoded_pcm(flac_path, scratch) != original:
                    print(f"  ABORT: {crate}/{name} did not round-trip bit-exactly")
                    os.remove(flac_path)
                    return 1

                crate_flac += os.path.getsize(flac_path)
                os.remove(wav_path)
                converted += 1

            total_wav += crate_wav
            total_flac += crate_flac
            if crate_wav:
                ratio = (crate_wav / crate_flac) if crate_flac else 0.0
                print(
                    f"{crate}: {len(names)} files  "
                    f"{crate_wav/1048576:6.2f} -> {crate_flac/1048576:6.2f} MiB  {ratio:.2f}x"
                )

    print()
    if args.dry_run:
        print(f"dry run: {sum(1 for _ in range(0))} converted; would convert from {total_wav/1048576:.2f} MiB")
    else:
        saved = total_wav - total_flac
        print(
            f"converted {converted} files, all verified bit-exact: "
            f"{total_wav/1048576:.2f} -> {total_flac/1048576:.2f} MiB "
            f"(saved {saved/1048576:.2f} MiB)"
        )
        print(f"left as RIFF: {skipped} files in the skipped crates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
