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
from contextlib import ExitStack
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
    # `-drumkit` and `-drumkit2` used to sit here. They decode PCM inside the
    # asset crate (`decode_wav` + `PCM_CACHE` in their own lib.rs) because
    # `pcm()` and `prewarm()` are part of their published API, so they needed a
    # decoder rather than just bytes. Resolved by `ferrosintesis-flac`, a shared
    # first-party crate all three depend on; they convert like the rest now.
}


class BankPlan:
    """One complete WAV bank staged and ready for transactional publication."""

    def __init__(
        self,
        crate: str,
        samples_dir: str,
        source_names: tuple[str, ...],
        staging_dir: str,
        wav_bytes: int,
        flac_bytes: int,
    ):
        self.crate = crate
        self.samples_dir = samples_dir
        self.source_names = source_names
        self.staging_dir = staging_dir
        self.wav_bytes = wav_bytes
        self.flac_bytes = flac_bytes
        self.backup_dir = None
        self.old_flacs = {}
        self.old_wavs = {}
        self.published_flacs = set()

    @property
    def flac_names(self) -> tuple[str, ...]:
        return tuple(os.path.splitext(name)[0] + ".flac" for name in self.source_names)


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


def _clear_staging(staging_dir: str) -> None:
    """Remove every entry from a staging directory after a failed bake."""
    for name in os.listdir(staging_dir):
        path = os.path.join(staging_dir, name)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def _validate_staged_bank(staging_dir: str, expected: set[str], label: str) -> None:
    """Require an empty transaction directory except for the exact FLAC bank."""
    actual = set(os.listdir(staging_dir))
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError(f"{label} staging output inventory mismatch (" + "; ".join(details) + ")")
    non_files = sorted(
        name for name in expected if not os.path.isfile(os.path.join(staging_dir, name))
    )
    if non_files:
        raise ValueError(
            f"{label} staging output contains non-files: " + ", ".join(non_files)
        )


def _bank_inventory(samples_dir: str) -> set[str]:
    return {
        name
        for name in os.listdir(samples_dir)
        if name.endswith((".wav", ".flac"))
    }


def _validate_output_inventory(
    samples_dir: str, expected: set[str], label: str
) -> None:
    """Reject mixed-bank leftovers before or after a publication transaction."""
    actual = _bank_inventory(samples_dir)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError(f"{label} output inventory mismatch (" + "; ".join(details) + ")")
    non_files = sorted(
        name for name in expected if not os.path.isfile(os.path.join(samples_dir, name))
    )
    if non_files:
        raise ValueError(
            f"{label} output contains non-files: " + ", ".join(non_files)
        )
    partials = sorted(name for name in os.listdir(samples_dir) if name.endswith(".part"))
    if partials:
        raise ValueError(
            f"{label} output contains partial files: " + ", ".join(partials)
        )


def _validate_output_inputs(
    samples_dir: str,
    source_names: set[str],
    flac_names: set[str],
    label: str,
) -> None:
    """Validate the pre-publication bank, where destination FLACs may be absent."""
    actual = _bank_inventory(samples_dir)
    allowed = source_names | flac_names
    unexpected = sorted(actual - allowed)
    missing_sources = sorted(source_names - actual)
    details = []
    if missing_sources:
        details.append("missing WAVs: " + ", ".join(missing_sources))
    if unexpected:
        details.append("unexpected: " + ", ".join(unexpected))
    if details:
        raise ValueError(f"{label} input inventory mismatch (" + "; ".join(details) + ")")
    non_files = sorted(
        name for name in actual if not os.path.isfile(os.path.join(samples_dir, name))
    )
    if non_files:
        raise ValueError(
            f"{label} input contains non-files: " + ", ".join(non_files)
        )
    partials = sorted(name for name in os.listdir(samples_dir) if name.endswith(".part"))
    if partials:
        raise ValueError(
            f"{label} input contains partial files: " + ", ".join(partials)
        )


def _stage_bank(
    crate: str,
    samples_dir: str,
    source_names: tuple[str, ...],
    staging_dir: str,
    scratch: str,
) -> BankPlan:
    """Encode and verify a complete bank without touching its published files."""
    source_names = tuple(sorted(source_names))
    flac_names = tuple(os.path.splitext(name)[0] + ".flac" for name in source_names)
    if len(set(flac_names)) != len(flac_names):
        raise ValueError(f"{crate} source names collapse to duplicate FLAC names")
    if os.listdir(staging_dir):
        raise ValueError(f"{crate} staging directory is not empty")
    os.makedirs(scratch, exist_ok=True)

    wav_bytes = 0
    flac_bytes = 0
    try:
        for name, packaged in zip(source_names, flac_names):
            wav_path = os.path.join(samples_dir, name)
            if carries_b1_tail(wav_path):
                raise ValueError(
                    f"{crate}/{name} carries a b1t chunk but is not in SKIP_CRATES"
                )
            original = riff_data_chunk(wav_path)
            wav_bytes += os.path.getsize(wav_path)
            flac_path = os.path.join(staging_dir, packaged)
            encode(wav_path, flac_path)
            if decoded_pcm(flac_path, scratch) != original:
                raise ValueError(f"{crate}/{name} did not round-trip bit-exactly")
            flac_bytes += os.path.getsize(flac_path)

        _validate_staged_bank(staging_dir, set(flac_names), crate)
    except BaseException:
        _clear_staging(staging_dir)
        raise

    return BankPlan(
        crate=crate,
        samples_dir=samples_dir,
        source_names=source_names,
        staging_dir=staging_dir,
        wav_bytes=wav_bytes,
        flac_bytes=flac_bytes,
    )


def _rollback_bank(plan: BankPlan) -> None:
    """Restore a bank whose publication was interrupted."""
    errors = []
    for name in sorted(plan.published_flacs, reverse=True):
        destination = os.path.join(plan.samples_dir, name)
        if not os.path.exists(destination):
            continue
        try:
            os.remove(destination)
        except OSError as error:
            errors.append(f"remove {name}: {error}")

    for name, backup in reversed(tuple(plan.old_flacs.items())):
        if not os.path.exists(backup):
            continue
        try:
            os.replace(backup, os.path.join(plan.samples_dir, name))
        except OSError as error:
            errors.append(f"restore {name}: {error}")

    for name, backup in reversed(tuple(plan.old_wavs.items())):
        if not os.path.exists(backup):
            continue
        try:
            os.replace(backup, os.path.join(plan.samples_dir, name))
        except OSError as error:
            errors.append(f"restore {name}: {error}")

    if errors:
        raise RuntimeError(
            f"{plan.crate} publication failed and rollback was incomplete: "
            + "; ".join(errors)
        )


def _cleanup_backup(plan: BankPlan) -> None:
    if plan.backup_dir is not None:
        shutil.rmtree(plan.backup_dir, ignore_errors=True)
        plan.backup_dir = None


def _publish_bank(plan: BankPlan) -> None:
    """Publish a validated bank, restoring every old file if a swap fails."""
    expected_flacs = set(plan.flac_names)
    _validate_staged_bank(plan.staging_dir, expected_flacs, plan.crate)
    _validate_output_inputs(
        plan.samples_dir, set(plan.source_names), expected_flacs, plan.crate
    )

    plan.backup_dir = tempfile.mkdtemp(
        prefix=f".{plan.crate}-backup-", dir=plan.samples_dir
    )
    try:
        for name in plan.flac_names:
            destination = os.path.join(plan.samples_dir, name)
            if os.path.exists(destination):
                backup = os.path.join(plan.backup_dir, name)
                os.replace(destination, backup)
                plan.old_flacs[name] = backup
        for name in plan.source_names:
            source = os.path.join(plan.samples_dir, name)
            backup = os.path.join(plan.backup_dir, name)
            os.replace(source, backup)
            plan.old_wavs[name] = backup
        for name in plan.flac_names:
            staged = os.path.join(plan.staging_dir, name)
            destination = os.path.join(plan.samples_dir, name)
            os.replace(staged, destination)
            plan.published_flacs.add(name)

        _validate_output_inventory(plan.samples_dir, expected_flacs, plan.crate)
    except BaseException as publish_error:
        try:
            _rollback_bank(plan)
        except BaseException as rollback_error:
            raise RuntimeError(
                f"{plan.crate} publication failed and rollback was incomplete: "
                f"{rollback_error}"
            ) from publish_error
        _cleanup_backup(plan)
        raise


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
    would_convert = 0
    skipped = 0
    plans = []

    with tempfile.TemporaryDirectory() as scratch, ExitStack() as stages:
        try:
            for crate in crates:
                samples = os.path.join(CRATES_DIR, crate, "samples")
                names = tuple(sorted(n for n in os.listdir(samples) if n.endswith(".wav")))
                if crate in SKIP_CRATES:
                    held = sum(
                        os.path.getsize(os.path.join(samples, n)) for n in names
                    )
                    print(
                        f"{crate}: SKIP ({len(names)} files, {held/1048576:.2f} MiB) - see SKIP_CRATES"
                    )
                    skipped += len(names)
                    continue
                if not names:
                    continue

                if args.dry_run:
                    crate_wav = sum(
                        os.path.getsize(os.path.join(samples, name)) for name in names
                    )
                    total_wav += crate_wav
                    would_convert += len(names)
                    print(
                        f"{crate}: {len(names)} files  "
                        f"{crate_wav/1048576:6.2f} MiB -> FLAC (dry run)"
                    )
                    continue

                staging = stages.enter_context(
                    tempfile.TemporaryDirectory(
                        prefix=f".{crate}-stage-", dir=samples
                    )
                )
                plan = _stage_bank(crate, samples, names, staging, scratch)
                plans.append(plan)
                total_wav += plan.wav_bytes
                total_flac += plan.flac_bytes
                converted += len(plan.source_names)

            if not args.dry_run:
                published = []
                try:
                    for plan in plans:
                        _publish_bank(plan)
                        published.append(plan)
                except BaseException as publish_error:
                    rollback_errors = []
                    for plan in reversed(published):
                        try:
                            _rollback_bank(plan)
                        except BaseException as rollback_error:
                            rollback_errors.append(f"{plan.crate}: {rollback_error}")
                        else:
                            _cleanup_backup(plan)
                    if rollback_errors:
                        raise RuntimeError(
                            "conversion publication failed and rollback was incomplete: "
                            + "; ".join(rollback_errors)
                        ) from publish_error
                    raise
                for plan in published:
                    _cleanup_backup(plan)
                    ratio = plan.wav_bytes / plan.flac_bytes if plan.flac_bytes else 0.0
                    print(
                        f"{plan.crate}: {len(plan.source_names)} files  "
                        f"{plan.wav_bytes/1048576:6.2f} -> {plan.flac_bytes/1048576:6.2f} MiB  {ratio:.2f}x"
                    )
        except Exception as error:
            print(f"  ABORT: {error}")
            return 1

    print()
    if args.dry_run:
        print(
            f"dry run: {would_convert} converted; would convert from "
            f"{total_wav/1048576:.2f} MiB"
        )
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
