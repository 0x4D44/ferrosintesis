#!/usr/bin/env python3
"""render-diff — the inventory CLAUDE.md mandates for any synth-voice change.

CLAUDE.md requires a render-diff inventory for any change to voices.rs / engine.rs /
drums.rs / sampler.rs: render every album MIDI with a BASELINE binary and the NEW one and
compare. It is a REPORT, not a pass/fail gate:

  * EXPECTED diffs   confirm the change reached exactly the albums it should.
  * CONTAMINATION    (a track that uses none of the touched voices, but moved) is a BUG —
                     a DC leak on a silent channel, a stray RNG draw that re-rolled every
                     subsequent one, a shared struct you did not mean to touch.
  * NOT REACHED      (a track that uses a touched voice, but did not move) means either the
                     fix is not wired up, or your --program/--key list is wrong.

Until now every task hand-rolled this (scratchpad, 2026.07.13). Don't: use this.

USAGE
    # 1. build a baseline binary from the trunk in a throwaway worktree
    git worktree add /d/worktrees/<repo>/BASELINE origin/main
    (cd /d/worktrees/<repo>/BASELINE && cargo build --release -p ferrosintesis-cli)

    # 2. build yours, then declare which voices you touched
    cargo build --release -p ferrosintesis-cli
    python tools/render-diff/render_diff.py \
        --baseline /d/worktrees/<repo>/BASELINE/target/release/ferrosintesis.exe \
        --new      ./target/release/ferrosintesis.exe \
        --program 43 --program 114 --key 48 --key 50

A GOTCHA THAT WILL BITE YOU: `cargo test` does NOT emit target/release/<bin>. Only
`cargo build` does. Run the build, or you will diff a stale binary and get a confident,
wrong, clean bill of health. (This is not hypothetical — it happened on the first run of
this harness and reported two real changes as "not reached".)

Declare a voice as touched ONLY if its rendered output actually changes. Splitting a
`47 | 48 | 50 =>` match arm leaves key 47 on its original constants, so key 47 is NOT
touched — listing it produces spurious NOT-REACHED rows.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import struct
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor


def _vlq(d: bytes, i: int) -> tuple[int, int]:
    v = 0
    while True:
        b = d[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def scan(path: str) -> tuple[set[int], set[int]]:
    """(GM programs, channel-10 drum keys) that a MIDI file actually SOUNDS.

    Note "sounds", not "declares": a program change with no notes on that channel does not
    count, and a note-on with velocity 0 is a note-off.
    """
    d = open(path, "rb").read()
    progs: set[int] = set()
    keys: set[int] = set()
    ch_prog: dict[int, list[int]] = {}
    ch_sounded: set[int] = set()
    i = 0
    while i < len(d) - 8:
        if d[i:i + 4] != b"MTrk":
            i += 1
            continue
        ln = struct.unpack(">I", d[i + 4:i + 8])[0]
        i += 8
        end = i + ln
        st = 0
        while i < end:
            _, i = _vlq(d, i)
            if i >= end:
                break
            b = d[i]
            if b & 0x80:
                st = b
                i += 1
            else:
                b = st
            kind, ch = b & 0xF0, b & 0x0F
            if kind == 0xC0:
                ch_prog.setdefault(ch, []).append(d[i])
                i += 1
            elif kind == 0x90:
                if d[i + 1] > 0:  # velocity 0 == note-off
                    ch_sounded.add(ch)
                    if ch == 9:
                        keys.add(d[i])
                i += 2
            elif kind in (0x80, 0xA0, 0xB0, 0xE0):
                i += 2
            elif kind == 0xD0:
                i += 1
            elif b == 0xFF:
                # the status byte is already consumed, so `i` is at the meta TYPE byte
                i += 1
                ln2, i = _vlq(d, i)
                i += ln2
            elif b in (0xF0, 0xF7):
                ln2, i = _vlq(d, i)  # `i` is already at the sysex length
                i += ln2
            else:
                i += 1
        i = end
    for ch, ps in ch_prog.items():
        # Channel 10 (index 9) program changes select a drum KIT, not a melodic voice
        # (PC 24 Synth, PC 25 V1, PC 40 Brush) — folding them into `progs` would report
        # e.g. a Brush-kit album as sounding melodic GM 40, and `--program 40` would then
        # list it as NOT REACHED. Its percussion is already tracked through `keys`.
        if ch != 9 and ch in ch_sounded:
            progs.update(ps)
    return progs, keys


def render_hash(exe: str, mid: str, tag: str, rate: "int | None" = None) -> str:
    out = f".rd_{tag}_{hashlib.md5(mid.encode()).hexdigest()[:10]}.wav"
    argv = [exe, mid, "-o", out, "-q"]
    if rate is not None:
        argv += ["--rate", str(rate)]
    r = subprocess.run(argv, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"render FAILED ({exe}) for {mid}: {r.stderr.decode(errors='replace')[:200]}"
        )
    try:
        return hashlib.sha256(open(out, "rb").read()).hexdigest()
    finally:
        if os.path.exists(out):
            os.remove(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", required=True, help="binary built from the trunk")
    ap.add_argument("--new", required=True, help="binary built from your branch")
    ap.add_argument("--program", type=int, action="append", default=[],
                    help="a GM program your change TOUCHES (repeatable)")
    ap.add_argument("--key", type=int, action="append", default=[],
                    help="a channel-10 drum key your change TOUCHES (repeatable)")
    ap.add_argument("--glob", default="albums/**/*.mid", help="which MIDIs to render")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--rate", type=int, default=None,
                    help="sample rate passed to the binary. SAME/DIFF is rate-independent "
                         "(byte-exact per channel), so a low rate (e.g. 11025) classifies "
                         "identically ~4x faster — use it to keep a full-catalog diff from "
                         "timing out.")
    a = ap.parse_args()

    touched_p, touched_k = set(a.program), set(a.key)
    mids = sorted(glob.glob(a.glob, recursive=True))
    if not mids:
        print(f"no MIDIs matched {a.glob!r} — are you in the repo root?", file=sys.stderr)
        return 2

    print(f"render-diff over {len(mids)} MIDIs")
    print(f"  baseline: {a.baseline}")
    print(f"  new:      {a.new}")
    print(f"  touched:  GM {sorted(touched_p) or '-'}, drum keys {sorted(touched_k) or '-'}\n")

    def job(mid: str):
        progs, keys = scan(mid)
        hit_p, hit_k = progs & touched_p, keys & touched_k
        predicted = bool(hit_p or hit_k)
        changed = render_hash(a.baseline, mid, "base", a.rate) != render_hash(a.new, mid, "new", a.rate)
        why = []
        if hit_p:
            why.append("GM" + ",".join(map(str, sorted(hit_p))))
        if hit_k:
            why.append("key" + ",".join(map(str, sorted(hit_k))))
        return mid, predicted, changed, ",".join(why)

    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        results = list(ex.map(job, mids))

    contamination = [r for r in results if not r[1] and r[2]]
    not_reached = [r for r in results if r[1] and not r[2]]
    print(f"EXPECTED  changed : {sum(1 for r in results if r[1] and r[2]):3d}")
    print(f"EXPECTED  same    : {sum(1 for r in results if not r[1] and not r[2]):3d}")
    print(f"CONTAMINATION     : {len(contamination):3d}  <-- a BUG if nonzero")
    print(f"NOT REACHED       : {len(not_reached):3d}  <-- fix not wired, or your list is wrong")

    if contamination:
        print("\n!! CONTAMINATION — these use NONE of the touched voices but MOVED:")
        for m, _, _, _ in contamination:
            print(f"   {m}")
    if not_reached:
        print("\n!! NOT REACHED — these use a touched voice but did NOT move:")
        for m, _, _, w in not_reached:
            print(f"   {m}  ({w})")

    print("\nchanged tracks by cause:")
    for why, n in sorted(Counter(r[3] for r in results if r[2]).items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {why or '(NONE — contamination)'}")

    # The report is informational, but contamination is unambiguously a bug: exit nonzero
    # so a scripted caller notices.
    return 1 if contamination else 0


if __name__ == "__main__":
    sys.exit(main())
