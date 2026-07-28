#!/usr/bin/env python3
"""Refresh a sample crate's generated inventory and size pins from `samples/*.wav`.

`gen_crate_lib.py` emits a whole `lib.rs` for the plain sample crates. The drum-kit
and B1 crates carry hand-written extras on top of that shape, so regenerating the file
wholesale would throw them away. This rewrites only the `SAMPLES` array, `FILE_COUNT`,
and aggregate size pins. If a crate has an `EXPECTED_TAIL_BYTES` pin, every WAV must
first pass the strict B1 natural-tail validation below.

Idempotent: running it on an unchanged directory is a no-op.

    python regen_samples_table.py ../../crates/ferrosintesis-samples-drumkit
"""
import os
import re
import subprocess
import sys

GENERATED_START = "// BEGIN GENERATED SAMPLE INVENTORY"
GENERATED_END = "// END GENERATED SAMPLE INVENTORY"
ARRAY_RE = re.compile(
    r"(static SAMPLES: \[\(&str, &\[u8\]\); FILE_COUNT\] = \[\n).*?(^\];\n)",
    re.DOTALL | re.MULTILINE,
)
COUNT_RE = re.compile(r"^(pub const FILE_COUNT: usize = )\d+(;)$", re.MULTILINE)


def replace_single(pattern, replacement, source, description):
    source, count = pattern.subn(replacement, source)
    if count != 1:
        raise ValueError(f"expected exactly one {description}, found {count}")
    return source


def replace_size_pin(source, name, value):
    pattern = re.compile(
        rf"^(?P<prefix>\s*const {name}: usize = )(?P<value>[\d_]+)(?P<suffix>;)$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name}, found {len(matches)}")
    old = int(matches[0].group("value").replace("_", ""))
    source = pattern.sub(
        lambda match: f"{match.group('prefix')}{value}{match.group('suffix')}",
        source,
    )
    return source, old


def b1_tail_payload_size(wav, path):
    """Validate one extended B1 WAV and return its compact tail payload bytes."""
    if len(wav) < 12 or wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
        raise ValueError(f"{path}: not a RIFF/WAVE file")
    declared_end = 8 + int.from_bytes(wav[4:8], "little")
    if declared_end != len(wav):
        raise ValueError(
            f"{path}: RIFF declares {declared_end} bytes, file has {len(wav)}"
        )

    position = 12
    payload_size = None
    while position < declared_end:
        if position + 8 > declared_end:
            raise ValueError(f"{path}: truncated RIFF chunk header")
        chunk_size = int.from_bytes(wav[position + 4 : position + 8], "little")
        body_start = position + 8
        body_end = body_start + chunk_size
        padded_end = body_end + (chunk_size & 1)
        if padded_end > declared_end:
            raise ValueError(f"{path}: RIFF chunk extends beyond the file")
        if wav[position : position + 4] == b"b1t ":
            if payload_size is not None:
                raise ValueError(f"{path}: duplicate B1 natural-tail chunk")
            if padded_end != declared_end:
                raise ValueError(f"{path}: B1 natural-tail chunk is not terminal")
            body = wav[body_start:body_end]
            if len(body) <= 12:
                raise ValueError(f"{path}: empty B1 natural-tail payload")
            if body[0] != 1:
                raise ValueError(f"{path}: unsupported B1 tail version {body[0]}")
            if body[1] != 4:
                raise ValueError(f"{path}: unsupported B1 tail rate divisor {body[1]}")
            if body[2:4] != b"\0\0":
                raise ValueError(f"{path}: nonzero B1 tail reserved field")
            entry_frame = int.from_bytes(body[4:8], "little")
            if entry_frame != 59_535:
                raise ValueError(f"{path}: unexpected B1 tail entry {entry_frame}")
            source_frames = int.from_bytes(body[8:12], "little")
            payload_size = len(body) - 12
            if payload_size != (source_frames + 3) // 4:
                raise ValueError(
                    f"{path}: B1 tail payload length does not match its source frames"
                )
        position = padded_end

    if payload_size is None:
        raise ValueError(f"{path}: missing B1 natural-tail chunk")
    return payload_size


def main():
    crate = sys.argv[1]
    lib = os.path.join(crate, "src", "lib.rs")
    samples_dir = os.path.join(crate, "samples")
    names = sorted(f for f in os.listdir(samples_dir) if f.endswith(".wav"))
    if not names:
        raise SystemExit(f"no .wav files in {samples_dir}")

    body = "".join(f'    ("{n}", include_bytes!("../samples/{n}")),\n' for n in names)

    with open(lib, encoding="utf-8") as fh:
        src = fh.read()

    has_tail_pin = "const EXPECTED_TAIL_BYTES:" in src
    if has_tail_pin:
        if src.count(GENERATED_START) != 1 or src.count(GENERATED_END) != 1:
            raise SystemExit(
                f"{lib}: B1 inventory must be bounded by the generated-region markers"
            )
        marked = src[
            src.index(GENERATED_START) + len(GENERATED_START) : src.index(GENERATED_END)
        ]
        if not ARRAY_RE.search(marked):
            raise SystemExit(f"{lib}: SAMPLES array is outside its generated region")

    total_bytes = sum(os.path.getsize(os.path.join(samples_dir, name)) for name in names)
    tail_bytes = None
    if has_tail_pin:
        tail_bytes = 0
        for name in names:
            path = os.path.join(samples_dir, name)
            with open(path, "rb") as fh:
                tail_bytes += b1_tail_payload_size(fh.read(), path)

    if not ARRAY_RE.search(src):
        raise SystemExit(f"{lib}: no SAMPLES array in the expected shape")
    src = ARRAY_RE.sub(lambda m: m.group(1) + body + m.group(2), src)
    try:
        src = replace_single(
            COUNT_RE,
            rf"\g<1>{len(names)}\g<2>",
            src,
            "FILE_COUNT",
        )
        src, old_total = replace_size_pin(src, "EXPECTED_BYTES", total_bytes)
        if tail_bytes is not None:
            src, old_tail = replace_size_pin(
                src,
                "EXPECTED_TAIL_BYTES",
                tail_bytes,
            )
    except ValueError as error:
        raise SystemExit(f"{lib}: {error}") from error

    with open(lib, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    print(
        f"{lib}: FILE_COUNT={len(names)}, "
        f"EXPECTED_BYTES={old_total}->{total_bytes}"
    )
    if tail_bytes is not None:
        print(f"{lib}: EXPECTED_TAIL_BYTES={old_tail}->{tail_bytes}")

    # rustfmt owns the final layout — the one-line-per-entry form above is over the
    # width limit for the longer names, and the gate runs `cargo fmt --check`.
    subprocess.run(["rustfmt", "--edition", "2021", lib], check=True)
    print(f"{lib}: rustfmt clean")


if __name__ == "__main__":
    main()
