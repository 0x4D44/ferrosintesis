#!/usr/bin/env python3
"""Rewrite a sample crate's `SAMPLES` table (and `FILE_COUNT`) from `samples/*.wav`.

`gen_crate_lib.py` emits a whole `lib.rs` for the plain sample crates. The drum-kit
crates carry hand-written extras on top of that shape (the `Bank` descriptors, the PCM
cache, the RIFF walker), so regenerating the file wholesale would throw them away. This
rewrites only the generated region — the `SAMPLES` array and the `FILE_COUNT` constant —
and leaves everything else byte-for-byte alone.

Idempotent: running it on an unchanged directory is a no-op.

    python regen_samples_table.py ../../crates/ferrosintesis-samples-drumkit
"""
import os
import re
import subprocess
import sys

ARRAY_RE = re.compile(
    r"(static SAMPLES: \[\(&str, &\[u8\]\); FILE_COUNT\] = \[\n).*?(^\];\n)",
    re.DOTALL | re.MULTILINE,
)
COUNT_RE = re.compile(r"^(pub const FILE_COUNT: usize = )\d+(;)$", re.MULTILINE)


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

    if not ARRAY_RE.search(src):
        raise SystemExit(f"{lib}: no SAMPLES array in the expected shape")
    src = ARRAY_RE.sub(lambda m: m.group(1) + body + m.group(2), src)
    src, n = COUNT_RE.subn(rf"\g<1>{len(names)}\g<2>", src)
    if n != 1:
        raise SystemExit(f"{lib}: expected exactly one FILE_COUNT, found {n}")

    with open(lib, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    print(f"{lib}: {len(names)} files")

    # rustfmt owns the final layout — the one-line-per-entry form above is over the
    # width limit for the longer names, and the gate runs `cargo fmt --check`.
    subprocess.run(["rustfmt", "--edition", "2021", lib], check=True)
    print(f"{lib}: rustfmt clean")


if __name__ == "__main__":
    main()
