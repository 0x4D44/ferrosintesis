import subprocess, re, tempfile, os, time
from pathlib import Path
REPO = Path(__file__).resolve().parent
CLI = str(REPO / "target/release/ferrosintesis.exe")
tracks = [
    ("Landing Lights", "albums/fable5/Through Lines/midi/15 - Landing Lights.mid"),
    ("Snow", "albums/opus4-8/midi/07 - Snow.mid"),
    ("Five Fables", "albums/fable5/Through Lines/midi/01 - Five Fables.mid"),
    ("Black Glass", "albums/gpt5-6/Atlas of Becoming/midi/09 - Black Glass Pursuit.mid"),
    ("Choir", "demos/synth_feature_showcase/midi/04 - Choir of Circuitry.mid"),
    ("Ten Thousand Watts", "albums/fable5/Big Weather/midi/09 - Ten Thousand Watts.mid"),
    ("RIVERWAKE (60min)", "albums/opus4-8/amarok/midi/Riverwake.mid"),
]
print(f"{'track':22s} {'I':>7s} {'TP':>7s} {'render_s':>9s}", flush=True)
okI = okTP = 0
for label, t in tracks:
    td = tempfile.mkdtemp(); wav = os.path.join(td, "r.wav")
    t0 = time.perf_counter()
    subprocess.run([CLI, str(REPO / t), "-o", wav, "-q"], capture_output=True, timeout=600)
    dt = time.perf_counter() - t0
    o = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", wav, "-af",
                        "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, timeout=600).stderr.decode("utf-8", "replace")[-1500:]
    I = float(re.search(r"I:\s*(-?[\d.]+)\s*LUFS", o).group(1))
    TP = float(re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", o)[-1])
    fI = "ok" if abs(I + 18) < 0.7 else "!!"
    fT = "ok" if TP <= -0.95 else "!!"
    okI += abs(I + 18) < 0.7; okTP += TP <= -0.95
    print(f"{label:22s} {I:7.1f}{fI} {TP:7.2f}{fT} {dt:9.1f}", flush=True)
    os.remove(wav); os.rmdir(td)
print(f"\nloudness ~-18: {okI}/{len(tracks)}   true-peak <= -1: {okTP}/{len(tracks)}", flush=True)
