#!/usr/bin/env python3
"""measure_raw.py — DEV-ONLY. Render every album MIDI with normalization DISABLED
(via the raw_dump example) and measure its NATIVE integrated loudness + true peak
with ffmpeg. Writes raw_loudness.csv. Deletes each WAV immediately (float WAVs are
huge). This is the ground-truth for the loudness-normalization design decision."""
from __future__ import annotations
import csv, re, subprocess, tempfile, math, sys, os
import concurrent.futures as cf
from pathlib import Path

REPO = Path(__file__).resolve().parent
BIN = REPO / "target" / "release" / "examples" / "raw_dump.exe"
MIDIS = sorted((REPO / "albums").glob("**/midi/*.mid"))

def album_of(m: Path) -> str:
    # albums/<...>/midi/<file>.mid  ->  the dir holding midi/
    return m.parent.parent.relative_to(REPO / "albums").as_posix()

def measure(m: Path):
    td = tempfile.mkdtemp()
    wav = os.path.join(td, "raw.wav")
    try:
        p = subprocess.run([str(BIN), str(m), wav], capture_output=True, text=True, timeout=900)
        if p.returncode != 0 or not os.path.exists(wav):
            return (album_of(m), m.stem, None, None, None, None, f"render fail: {p.stderr[:120]}")
        raw_peak = float(p.stdout.strip().split(",")[0])
        o = subprocess.run(["ffmpeg","-nostats","-hide_banner","-i",wav,
                            "-af","ebur128=peak=true","-f","null","-"],
                           capture_output=True, timeout=900).stderr.decode("utf-8","replace")[-1600:]
        I  = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", o)
        LRA= re.search(r"LRA:\s*(-?[\d.]+)\s*LU", o)
        TP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", o)
        I  = float(I.group(1)) if I else None
        LRA= float(LRA.group(1)) if LRA else None
        TP = float(TP[-1]) if TP else None
        return (album_of(m), m.stem, I, LRA, TP, raw_peak, "")
    except subprocess.TimeoutExpired:
        return (album_of(m), m.stem, None, None, None, None, "TIMEOUT")
    finally:
        try:
            if os.path.exists(wav): os.remove(wav)
            os.rmdir(td)
        except OSError:
            pass

def main():
    print(f"measuring {len(MIDIS)} MIDIs (raw, un-normalized)", flush=True)
    rows = []
    # Low parallelism: float WAVs are large; the two 60-min tracks are ~1.3 GB each.
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(measure, MIDIS):
            status = r[6] or f"I={r[2]} LRA={r[3]} TP={r[5] and 20*math.log10(r[5]):.2f}"
            print(f"  [{'ok' if not r[6] else 'FAIL'}] {r[0]} / {r[1]}  {status}", flush=True)
            rows.append(r)
    with open(REPO / "raw_loudness.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["album","track","raw_LUFS","raw_LRA","raw_true_peak_dBFS","raw_sample_peak","note"])
        w.writerows(rows)
    ok = sum(1 for r in rows if not r[6])
    print(f"done: {ok}/{len(rows)} measured -> raw_loudness.csv", flush=True)
    return 0 if ok == len(rows) else 1

if __name__ == "__main__":
    sys.exit(main())
