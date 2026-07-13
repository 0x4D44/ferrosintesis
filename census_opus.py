import subprocess, re, concurrent.futures as cf, statistics as st
from pathlib import Path
REPO = Path(__file__).resolve().parent
files = sorted((REPO / "listening").glob("**/*.opus"))
def meas(f):
    p = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(f), "-af",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True)
    tail = p.stderr.decode("utf-8", "replace")[-1500:]
    I = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", tail)
    TP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", tail)
    if not (I and TP):
        return (f, None, None)
    return (f, float(I.group(1)), float(TP[-1]))
with cf.ThreadPoolExecutor(8) as ex:
    rows = [r for r in ex.map(meas, files) if r[1] is not None]
Is = [r[1] for r in rows]; TPs = [r[2] for r in rows]
print(f"catalog: {len(rows)}/{len(files)} opus measured")
print(f"integrated LUFS: min {min(Is):.1f}  median {st.median(Is):.1f}  max {max(Is):.1f}  (target -18)")
print(f"true peak dBTP : min {min(TPs):.2f}  max {max(TPs):.2f}  (ceiling -1)")
off = [r for r in rows if abs(r[1] + 18) > 1.0]
over = [r for r in rows if r[2] > -0.95]
print(f"tracks off -18 by >1 LU: {len(off)}")
for f, I, TP in off:
    print(f"    {I:6.1f} LUFS  {f.parent.name} / {f.name}")
print(f"tracks over -1 dBTP: {len(over)}")
for f, I, TP in over:
    print(f"    {TP:+.2f} dBTP  {f.parent.name} / {f.name}")
print("\nACCEPTANCE:", "PASS" if not off and not over else "REVIEW NEEDED")
