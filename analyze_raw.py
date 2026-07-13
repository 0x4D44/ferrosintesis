#!/usr/bin/env python3
"""analyze_raw.py — DEV-ONLY. Turn raw_loudness.csv (native synth loudness, no
normalization) into the numbers the loudness-design decision needs:
  1. raw loudness distribution + how many tracks CLIP (raw peak > 0 dBFS)
  2. per multi-track album: raw inter-track loudness spread (the key question:
     does one album-gain leave a sane spread, or do sparse tracks ship inaudible?)
  3. simulate the album-relative-gain fix and show what would actually ship
  4. does the synth's NATIVE staging track composed dynamics? (raw LUFS vs the
     album's per-track composed note-energy, rank-correlated)
"""
from __future__ import annotations
import csv, math, statistics as st
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parent

def load():
    rows = []
    with open(REPO / "raw_loudness.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["note"]:  # failed row
                continue
            rows.append({
                "album": r["album"], "track": r["track"],
                "I": float(r["raw_LUFS"]), "LRA": float(r["raw_LRA"]),
                "tp": float(r["raw_true_peak_dBFS"]),
                "peak": float(r["raw_sample_peak"]),
                "peak_db": 20*math.log10(float(r["raw_sample_peak"])) if float(r["raw_sample_peak"])>0 else -120.0,
            })
    return rows

def spearman(xs, ys):
    n = len(xs)
    if n < 3: return None
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        rk = [0.0]*n
        i = 0
        while i < n:
            j = i
            while j+1 < n and v[order[j+1]] == v[order[i]]: j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j+1): rk[order[k]] = avg
            i = j + 1
        return rk
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx)/n, sum(ry)/n
    num = sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den = math.sqrt(sum((a-mx)**2 for a in rx) * sum((b-my)**2 for b in ry))
    return num/den if den else None

def parse_note_energy(album_key: str, track_stem: str):
    """Sum of note-on velocities for a track's MIDI — a proxy for composed energy.
    album_key is relative to albums/ OR a demos/ path handled by the caller."""
    # Try albums/<key>/midi/<stem>.mid
    for base in [REPO/"albums"/album_key/"midi", REPO/"demos"/album_key/"midi"]:
        mid = base / f"{track_stem}.mid"
        if mid.exists():
            return _velocity_sum(mid)
    return None

def _velocity_sum(path: Path):
    data = path.read_bytes()
    # minimal SMF note-on velocity sum (running status aware), channels != 9 (drums)
    total = 0
    i = data.find(b"MThd")
    if i < 0: return None
    # iterate track chunks
    pos = i
    while True:
        j = data.find(b"MTrk", pos)
        if j < 0: break
        length = int.from_bytes(data[j+4:j+8], "big")
        trk = data[j+8:j+8+length]
        pos = j+8+length
        k = 0; status = 0
        while k < len(trk):
            # skip delta time (varlen)
            while k < len(trk) and (trk[k] & 0x80): k += 1
            k += 1
            if k >= len(trk): break
            b = trk[k]
            if b & 0x80:
                status = b; k += 1
            # meta / sysex
            if status == 0xFF:
                k += 1  # meta type
                ln = 0
                while k < len(trk) and (trk[k] & 0x80):
                    ln = (ln<<7)|(trk[k]&0x7f); k+=1
                if k < len(trk):
                    ln = (ln<<7)|(trk[k]&0x7f); k+=1
                k += ln
                continue
            if status in (0xF0, 0xF7):
                ln = 0
                while k < len(trk) and (trk[k] & 0x80):
                    ln=(ln<<7)|(trk[k]&0x7f); k+=1
                if k < len(trk):
                    ln=(ln<<7)|(trk[k]&0x7f); k+=1
                k += ln
                continue
            hi = status & 0xF0; ch = status & 0x0F
            if hi in (0x80,0x90,0xA0,0xB0,0xE0):
                d1 = trk[k] if k < len(trk) else 0
                d2 = trk[k+1] if k+1 < len(trk) else 0
                if hi == 0x90 and d2 > 0 and ch != 9:
                    total += d2
                k += 2
            elif hi in (0xC0,0xD0):
                k += 1
    return total

def main():
    rows = load()
    print(f"=== RAW (un-normalized) loudness census: {len(rows)} tracks ===\n")

    Is = [r["I"] for r in rows]
    print(f"raw integrated LUFS : min {min(Is):.1f}  median {st.median(Is):.1f}  max {max(Is):.1f}  (mean {st.mean(Is):.1f})")
    clip = [r for r in rows if r["peak_db"] > 0.0]
    print(f"raw buffer CLIPS (sample peak > 0 dBFS): {len(clip)}/{len(rows)} tracks "
          f"— for these the current normalizer ATTENUATES")
    boost = [r for r in rows if r["peak_db"] < -1.0]
    print(f"raw buffer below -1 dBFS peak (normalizer BOOSTS): {len(boost)}/{len(rows)}")
    print(f"raw sample peak: min {min(r['peak_db'] for r in rows):+.1f}  "
          f"max {max(r['peak_db'] for r in rows):+.1f} dBFS")
    hot = sorted(rows, key=lambda r:-r["peak_db"])[:5]
    print("  hottest raw peaks:")
    for r in hot: print(f"    {r['peak_db']:+6.1f} dBFS  I={r['I']:6.1f}  {r['album']} / {r['track']}")
    print()

    by_alb = defaultdict(list)
    for r in rows: by_alb[r["album"]].append(r)

    print("=== per-album RAW inter-track loudness spread (multi-track only) ===")
    print("  (this is the load-bearing number: can ONE album gain leave a sane spread?)\n")
    multis = {a:v for a,v in by_alb.items() if len(v) >= 2}
    for a,v in sorted(multis.items(), key=lambda kv:-(max(x['I'] for x in kv[1])-min(x['I'] for x in kv[1]))):
        Iv = [x['I'] for x in v]
        spread = max(Iv)-min(Iv)
        lo = min(v, key=lambda x:x['I']); hi = max(v, key=lambda x:x['I'])
        print(f"  {spread:5.1f} LU spread ({len(v):2d} tk)  {a}")
        print(f"          quietest {lo['I']:6.1f}  {lo['track']}")
        print(f"          loudest  {hi['I']:6.1f}  {hi['track']}")
    print()

    print("=== album-relative gain SIMULATION (target album-loudest -> -1.0 dBTP) ===")
    print("  shows what actually ships if we apply ONE gain per album so its loudest")
    print("  track's true peak sits at -1.0 dBTP, preserving inter-track dynamics.\n")
    for a,v in sorted(multis.items()):
        max_tp = max(x['tp'] for x in v)
        g = -1.0 - max_tp                       # album gain to bring hottest track to -1 dBTP
        after = [x['I']+g for x in v]
        print(f"  {a:38s} gain {g:+5.1f} dB -> album LUFS "
              f"[{min(after):6.1f} .. {max(after):6.1f}]  quietest track ships at {min(after):.1f} LUFS")
    print()

    print("=== does NATIVE staging track COMPOSED dynamics? (raw LUFS vs note-energy) ===")
    print("  spearman rho per multi-track album; ~0 = staging is random, ~+1 = staging")
    print("  reflects what was composed.\n")
    for a,v in sorted(multis.items()):
        pairs = []
        for x in v:
            e = parse_note_energy(a, x["track"])
            if e: pairs.append((e, x["I"]))
        if len(pairs) >= 3:
            rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
            print(f"  rho {rho:+.2f}  ({len(pairs):2d} tk)  {a}")
    print()

if __name__ == "__main__":
    main()
