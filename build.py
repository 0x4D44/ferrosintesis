#!/usr/bin/env python3
"""build.py — build ferrosintesis and render every album to listening/*.opus.

One command for the whole audio pipeline. The rendered `.opus` files are
reproducible **build output** (git-ignored), not source: the committed inputs
are the album MIDIs (`albums/**/midi/*.mid`) plus the synth. This script builds
the release CLI, then runs `render_opus.py` to (re)produce the tagged listening
copies under `listening/<artist>/<album>/`.

    python build.py                     # build the release CLI, then render every album
    python build.py --album "Sub Rosa"  # build, then render just one album (by title)
    python build.py --jobs 4            # pass render parallelism through to render_opus.py
    python build.py --skip-build        # render only (assumes the CLI is already built)
    python build.py --no-render         # build the release CLI only; skip rendering

Requirements: a Rust toolchain (for the build) and `ropusenc` on PATH (from the
sibling `ropus` repo) for the render step.

Run from a task worktree, never the main clone — rendering writes ~340 MiB into
`listening/`. Those files are git-ignored, so they no longer dirty tracked state,
but a fresh render still churns the working tree.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=REPO).returncode


def main() -> int:
    ap = argparse.ArgumentParser(
        description="build ferrosintesis, then render every album to opus")
    ap.add_argument("--skip-build", action="store_true",
                    help="skip the cargo build and render only")
    ap.add_argument("--no-render", action="store_true",
                    help="build the release CLI only; skip rendering")
    ap.add_argument("--album", help="render only this album (by title)")
    ap.add_argument("--jobs", type=int,
                    help="render parallelism (default: render_opus.py's own default)")
    args = ap.parse_args()

    if not args.skip_build:
        rc = run(["cargo", "build", "--release", "-p", "ferrosintesis-cli"])
        if rc != 0:
            print("build.py: cargo build failed", file=sys.stderr)
            return rc

    if args.no_render:
        return 0

    render = [sys.executable, str(REPO / "render_opus.py")]
    if args.album:
        render += ["--album", args.album]
    if args.jobs is not None:
        render += ["--jobs", str(args.jobs)]
    return run(render)


if __name__ == "__main__":
    raise SystemExit(main())
