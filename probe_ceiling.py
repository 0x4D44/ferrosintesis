import subprocess, re, tempfile, os, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent
CLI = str(REPO / "target/release/ferrosintesis.exe")
CEIL = sys.argv[1] if len(sys.argv) > 1 else "-4.5"
# The brightest / densest outliers (worst codec overshoot) plus prior offenders.
tracks = [
    "albums/gpt5-6/Bright Matter/midi/01 - Six-Five-Two-One.mid",
    "albums/gpt5-6/Bright Matter/midi/02 - Runway Aurora.mid",
    "albums/gpt5-6/Bright Matter/midi/03 - Gravity Has a Chorus.mid",
    "albums/gpt5-6/Bright Matter/midi/04 - All the Lights Arrive Late.mid",
    "albums/gpt5-6/Bright Matter/midi/05 - Bright Matter (Everything at Once).mid",
    "albums/fable5/Through Lines/midi/08 - Ten Metres of Air.mid",
    "demos/synth_feature_showcase/midi/01 - Ignition Court.mid",
]
def tp(path):
    o = subprocess.run(["ffmpeg","-nostats","-hide_banner","-i",path,"-af","ebur128=peak=true","-f","null","-"],
                       capture_output=True, timeout=300).stderr.decode("utf-8","replace")[-1500:]
    return float(re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", o)[-1])
print(f"candidate ceiling {CEIL} -> opus true-peak on the worst tracks:", flush=True)
worst = -99.0
for t in tracks:
    td = tempfile.mkdtemp(); wav = os.path.join(td,"w.wav"); opus = os.path.join(td,"o.opus")
    subprocess.run([CLI, str(REPO/t), "-o", wav, "-q", "--tp-ceiling", CEIL], capture_output=True, timeout=400)
    subprocess.run(["ropusenc","--bitrate","96000","--music","--vbr","--comp","10","-o",opus,wav],
                   capture_output=True, timeout=400)
    o = tp(opus); worst = max(worst, o)
    print(f"  {o:6.2f} dBTP  {os.path.basename(t)}", flush=True)
    os.remove(wav); os.remove(opus); os.rmdir(td)
print(f"\nWORST opus true-peak at ceiling {CEIL}: {worst:.2f} dBTP  ({'all <= -1' if worst <= -1.0 else 'STILL OVER -1'})", flush=True)
