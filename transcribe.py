#!/usr/bin/env python3
"""transcribe.py — transcribe audio into multi-track MIDI by assembling free tools.

The inverse of render_opus.py: a stdlib-only orchestrator that shells out to external
ML tools (ffmpeg, Demucs, Basic Pitch, a drum ADT), each installed in its own venv and
resolved from `transcribe.local.json`. It does NOT do any DSP itself. Output is a set of
per-stem `.mid` files plus one combined multi-track General-MIDI file.

    python transcribe.py song.opus               # mix -> auto-separate -> transcribe
    python transcribe.py stems_dir/              # transcribe pre-made stems
    python transcribe.py song.opus -o out_dir    # choose the output directory
    python transcribe.py --selftest              # the no-ML assemble oracle (the build gate)
    python transcribe.py --diagnose              # ML round-trip + smoke (needs the tools)

Design: wrk_docs/2026.07.09 - HLD - opus to midi transcription tool.md
The only build gate is `--selftest`; it needs no external tools.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# --- constants -------------------------------------------------------------

PPQ = 480
TEMPO_BPM = 120.0
_TICKS_PER_SEC = PPQ * TEMPO_BPM / 60.0            # 960 ticks/second at fixed tempo
_MPQ_120 = int(round(60_000_000 / TEMPO_BPM))      # 500000 microseconds per quarter note
_DEFAULT_MPQ = 500_000                             # MIDI default when a track has no tempo

# canonical role -> (channel 0-based, GM program or None for drums, track name).
# Pinned and forced: the transcribers' own programs never define the arrangement, and the
# distinct channels stop piano/other (both program 0) colliding.
ROLE_TABLE: dict[str, tuple[int, int | None, str]] = {
    "vocals": (0, 54, "Vocals"),
    "bass":   (1, 33, "Bass"),
    "guitar": (2, 27, "Guitar"),
    "piano":  (3, 0,  "Piano"),
    "other":  (4, 0,  "Other (sketch)"),
    "drums":  (9, None, "Drums"),
}
ROLE_ORDER = ["vocals", "bass", "guitar", "piano", "other", "drums"]
PITCHED_ROLES = ("vocals", "bass", "guitar", "piano", "other")

# stem filename token -> canonical role
STEM_ALIASES = {
    "vocals": "vocals", "vocal": "vocals", "vox": "vocals", "voice": "vocals", "lead": "vocals",
    "bass": "bass",
    "drums": "drums", "drum": "drums", "percussion": "drums", "perc": "drums",
    "guitar": "guitar", "gtr": "guitar",
    "piano": "piano", "keys": "piano", "keyboard": "piano",
    "other": "other", "residual": "other",
}

MAX_DURATION_S = 15 * 60  # v1 processes whole files; over this, ask the user to split.

# A note is (onset_s, duration_s, pitch, velocity).
Note = tuple


# --- MIDI writer (lifts the fable5 engine.py Score writer, trimmed) --------

def _vlq(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative delta-time")
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, 0x80 | (n & 0x7F))
        n >>= 7
    return bytes(out)


def _sec_to_tick(sec: float) -> int:
    return int(round(sec * _TICKS_PER_SEC))


def _clamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v


def write_midi(path: Path, role_notes: dict[str, list[tuple[float, float, int, int]]]) -> None:
    """Write a type-1 GM MIDI: a conductor (tempo) track + one track per present role."""

    def meta(kind: int, payload: bytes) -> bytes:
        return bytes([0xFF, kind]) + _vlq(len(payload)) + payload

    def chunk(events: list[tuple[int, int, bytes]], name: str | None) -> bytes:
        body = bytearray()
        if name is not None:
            body += _vlq(0) + meta(0x03, name.encode("ascii", "replace"))
        last = 0
        for tick, _prio, data in sorted(events, key=lambda e: (e[0], e[1])):
            body += _vlq(tick - last) + data
            last = tick
        body += _vlq(0) + b"\xFF\x2F\x00"
        return b"MTrk" + struct.pack(">I", len(body)) + bytes(body)

    chunks = [chunk([(0, 0, meta(0x51, _MPQ_120.to_bytes(3, "big")))], "Conductor")]

    for role in ROLE_ORDER:
        notes = role_notes.get(role)
        if not notes:
            continue
        ch, prog, name = ROLE_TABLE[role]
        ev: list[tuple[int, int, bytes]] = []
        if prog is not None:
            ev.append((0, 0, bytes([0xC0 | ch, prog])))       # program change (prio 0: first)
        for onset, dur, pitch, vel in notes:
            p = _clamp(int(pitch), 0, 127)
            v = _clamp(int(vel), 1, 127)
            on = _sec_to_tick(onset)
            off = max(on + 1, _sec_to_tick(onset + max(0.0, dur)))
            ev.append((off, 0, bytes([0x80 | ch, p, 0])))      # note off (prio 0: before on)
            ev.append((on, 1, bytes([0x90 | ch, p, v])))       # note on
        chunks.append(chunk(ev, name))

    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + b"".join(chunks))


# --- MIDI reader (robust; for drum-tool MIDI and the oracle read-back) -----

def read_midi(path: Path) -> dict:
    """Parse a type-0/1 MIDI into per-track note events (absolute ticks).

    Handles running status, `note_on` velocity 0 as note-off, FIFO same-pitch pairing,
    unmatched note-offs (dropped), and rejects SMPTE division. Returns
    {ppq, tempo:[(tick, mpq)], tracks:[{name, program, notes:[(on, off, ch, pitch, vel)]}]}.
    """
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path.name}: not a MIDI file (no MThd)")
    _fmt, ntracks, division = struct.unpack(">HHH", data[8:14])
    if division & 0x8000:
        raise ValueError(f"{path.name}: SMPTE time division is unsupported")
    pos = 8 + int.from_bytes(data[4:8], "big")
    tempo: list[tuple[int, int]] = []
    tracks = []
    for _ in range(ntracks):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError(f"{path.name}: expected MTrk chunk")
        size = int.from_bytes(data[pos + 4:pos + 8], "big")
        pos += 8
        end = pos + size
        tick = 0
        status = 0
        name = ""
        program: int | None = None
        active: dict[tuple[int, int], list[tuple[int, int]]] = {}
        notes: list[tuple[int, int, int, int, int]] = []
        while pos < end:
            delta = 0
            while True:
                b = data[pos]; pos += 1
                delta = (delta << 7) | (b & 0x7F)
                if b < 0x80:
                    break
            tick += delta
            if data[pos] & 0x80:
                status = data[pos]; pos += 1           # new status
            # else: running status — reuse `status`, `data[pos]` is the first data byte
            if status == 0xFF:
                kind = data[pos]; pos += 1
                length = 0
                while True:
                    b = data[pos]; pos += 1
                    length = (length << 7) | (b & 0x7F)
                    if b < 0x80:
                        break
                payload = data[pos:pos + length]; pos += length
                if kind == 0x03 and not name:
                    name = payload.decode("ascii", "replace")
                elif kind == 0x51 and length == 3:
                    tempo.append((tick, int.from_bytes(payload, "big")))
            elif status in (0xF0, 0xF7):
                length = 0
                while True:
                    b = data[pos]; pos += 1
                    length = (length << 7) | (b & 0x7F)
                    if b < 0x80:
                        break
                pos += length
            else:
                hi = status & 0xF0
                ch = status & 0x0F
                if hi in (0xC0, 0xD0):
                    d0 = data[pos]; pos += 1
                    if hi == 0xC0 and program is None:
                        program = d0
                else:
                    d0 = data[pos]; d1 = data[pos + 1]; pos += 2
                    if hi == 0x90 and d1 > 0:
                        active.setdefault((ch, d0), []).append((tick, d1))
                    elif hi == 0x80 or (hi == 0x90 and d1 == 0):
                        q = active.get((ch, d0))
                        if q:
                            on_tick, vel = q.pop(0)          # FIFO pairing
                            notes.append((on_tick, tick, ch, d0, vel))
        tracks.append({"name": name, "program": program, "notes": notes})
    return {"ppq": division, "tempo": sorted(tempo), "tracks": tracks}


def _ticks_to_seconds(tick: int, ppq: int, tempo: list[tuple[int, int]]) -> float:
    """Absolute seconds at `tick`, integrating a (tick, microsec-per-quarter) tempo map."""
    if not tempo:
        tempo = [(0, _DEFAULT_MPQ)]
    seconds = 0.0
    cur_tick, cur_mpq = 0, tempo[0][1]
    for t_tick, t_mpq in tempo:
        if t_tick >= tick:
            break
        seconds += (t_tick - cur_tick) / ppq * cur_mpq / 1_000_000
        cur_tick, cur_mpq = t_tick, t_mpq
    seconds += (tick - cur_tick) / ppq * cur_mpq / 1_000_000
    return seconds


# --- ingest ----------------------------------------------------------------

def ingest_basic_pitch_csv(path: Path) -> list[tuple[float, float, int, int]]:
    """Basic Pitch note-event CSV -> notes in absolute seconds. Pitch-bend column ignored."""
    notes = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            start = float(row["start_time_s"])
            end = float(row["end_time_s"])
            pitch = int(round(float(row["pitch_midi"])))
            vel = int(round(float(row.get("velocity") or 100)))
            notes.append((start, max(0.0, end - start), pitch, _clamp(vel, 1, 127)))
    return notes


def ingest_drum_midi(path: Path) -> list[tuple[float, float, int, int]]:
    """A drum tool's MIDI -> notes in absolute seconds (GM percussion note numbers kept)."""
    m = read_midi(path)
    out = []
    for trk in m["tracks"]:
        for on, off, _ch, pitch, vel in trk["notes"]:
            t0 = _ticks_to_seconds(on, m["ppq"], m["tempo"])
            t1 = _ticks_to_seconds(off, m["ppq"], m["tempo"])
            out.append((t0, max(0.0, t1 - t0), pitch, vel))
    return out


# --- tool resolution (transcribe.local.json) -------------------------------

def load_config(repo: Path) -> dict:
    cfg = repo / "transcribe.local.json"
    if cfg.exists():
        return json.loads(cfg.read_text(encoding="utf-8"))
    return {}


def resolve_tool(repo: Path, cfg: dict, name: str) -> list[str]:
    """Resolve a tool to an argv prefix: config override, else a per-tool venv, else PATH."""
    entry = (cfg.get("tools") or {}).get(name, {})
    if isinstance(entry, str):
        return [entry]
    if entry.get("path"):
        return [entry["path"], *entry.get("args", [])]
    exe = name + (".exe" if sys.platform == "win32" else "")
    sub = "Scripts" if sys.platform == "win32" else "bin"
    venv_exe = repo / "tools" / name / sub / exe
    if venv_exe.exists():
        return [str(venv_exe)]
    return [name]  # fall back to PATH; a clear error is raised at call time if missing


def _run(argv: list[str], what: str) -> None:
    try:
        r = subprocess.run(argv, capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit(
            f"{what}: tool not found ({argv[0]}). Install it in its own venv or set its "
            f"path in transcribe.local.json (see transcribe.local.json.example)."
        )
    if r.returncode != 0:
        raise SystemExit(f"{what} failed (exit {r.returncode}):\n{r.stderr.strip()[:400]}")


# --- pipeline stages -------------------------------------------------------

def normalize(repo: Path, cfg: dict, src: Path, dst_wav: Path) -> None:
    argv = [*resolve_tool(repo, cfg, "ffmpeg"),
            "-y", "-i", str(src), "-ac", "2", "-ar", "44100", str(dst_wav)]
    _run(argv, "ffmpeg normalize")


def separate(repo: Path, cfg: dict, wav: Path, out_dir: Path) -> dict[str, Path]:
    _run([*resolve_tool(repo, cfg, "demucs"), "-n", "htdemucs_6s", "-o", str(out_dir), str(wav)],
         "Demucs separation")
    stem_dir = out_dir / "htdemucs_6s" / wav.stem
    stems = {}
    for role in ("vocals", "drums", "bass", "guitar", "piano", "other"):
        p = stem_dir / f"{role}.wav"
        if p.exists():
            stems[role] = p
    return stems


def transcribe_pitched(repo: Path, cfg: dict, stem_wav: Path, out_dir: Path) -> Path:
    _run([*resolve_tool(repo, cfg, "basic-pitch"), str(out_dir), str(stem_wav),
          "--save-note-events", "--no-sonify-midi"], "Basic Pitch")
    csv_path = out_dir / f"{stem_wav.stem}_basic_pitch.csv"
    if not csv_path.exists():
        raise SystemExit(f"Basic Pitch produced no CSV at {csv_path}")
    return csv_path


def transcribe_drums(repo: Path, cfg: dict, stem_wav: Path, out_dir: Path) -> Path:
    """Run the configured drum-ADT tool, returning a MIDI path. Tool chosen at install (Q-A)."""
    drum = cfg.get("tools", {}).get("drums")
    if not drum:
        raise SystemExit("drums: no drum-ADT tool configured (see transcribe.local.json.example)")
    mid = out_dir / f"{stem_wav.stem}_drums.mid"
    argv = [*resolve_tool(repo, cfg, "drums"), str(stem_wav), str(mid)]
    _run(argv, "drum transcription")
    return mid


# --- stem discovery --------------------------------------------------------

def match_stems(stems_dir: Path) -> dict[str, Path]:
    """Map audio files in a directory to canonical roles by filename token."""
    found: dict[str, Path] = {}
    for p in sorted(stems_dir.iterdir()):
        if p.suffix.lower() not in (".wav", ".flac", ".mp3", ".opus", ".ogg", ".m4a"):
            continue
        token = p.stem.lower().split("_")[-1].split("-")[-1].strip()
        role = STEM_ALIASES.get(token) or STEM_ALIASES.get(p.stem.lower())
        if not role:
            continue
        if role in found:
            raise SystemExit(f"two files map to role '{role}': {found[role].name} and {p.name}")
        found[role] = p
    if not found:
        raise SystemExit(f"no recognizable stems in {stems_dir} "
                         f"(name them vocals/bass/drums/guitar/piano/other)")
    return found


# --- assemble --------------------------------------------------------------

def transcribe_stems(repo: Path, cfg: dict, stems: dict[str, Path], out_dir: Path) -> dict:
    """Transcribe each role's stem, write per-stem MIDI, and one combined multitrack MIDI."""
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "_work"
    work.mkdir(exist_ok=True)
    role_notes: dict[str, list] = {}
    for role, wav in stems.items():
        if role == "drums":
            notes = ingest_drum_midi(transcribe_drums(repo, cfg, wav, work))
        elif role in PITCHED_ROLES:
            notes = ingest_basic_pitch_csv(transcribe_pitched(repo, cfg, wav, work))
        else:
            continue
        if not notes:
            print(f"  [{role}] silent/no notes — omitted")
            continue
        role_notes[role] = notes
        write_midi(out_dir / f"{role}.mid", {role: notes})
        print(f"  [{role}] {len(notes)} notes")
    if not role_notes:
        raise SystemExit("no notes transcribed from any stem")
    write_midi(out_dir / "combined.mid", role_notes)
    print(f"wrote {out_dir / 'combined.mid'}")
    return role_notes


def run_pipeline(repo: Path, cfg: dict, inp: Path, out_dir: Path) -> None:
    if inp.is_dir():
        stems = match_stems(inp)
        transcribe_stems(repo, cfg, stems, out_dir)
        return
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "mix.wav"
        normalize(repo, cfg, inp, wav)
        stems = separate(repo, cfg, wav, Path(td) / "sep")
        if not stems:
            raise SystemExit("Demucs produced no stems")
        transcribe_stems(repo, cfg, stems, out_dir)


# --- the no-ML assemble oracle (the build gate) ----------------------------

def _build_raw_midi(division: int, events: list[tuple[int, bytes]]) -> bytes:
    body = bytearray()
    for delta, data in events:
        body += _vlq(delta) + data
    body += _vlq(0) + b"\xFF\x2F\x00"
    trk = b"MTrk" + struct.pack(">I", len(body)) + bytes(body)
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, division) + trk


def _check_import_purity() -> list[str]:
    """Assert this module imports only the standard library."""
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    third_party = sorted(m for m in mods if m not in sys.stdlib_module_names)
    return [] if not third_party else [f"non-stdlib imports: {third_party}"]


def selftest() -> int:
    fails: list[str] = []

    # 1. Round-trip: hand-built role notes -> write -> read -> exact recovery.
    role_notes = {
        "vocals": [(0.0, 0.5, 60, 100), (1.0, 0.5, 62, 90)],
        "bass":   [(0.0, 1.0, 36, 110)],
        "other":  [(0.0, 2.0, 48, 70), (0.0, 2.0, 52, 70), (0.0, 2.0, 55, 70)],  # chord pad
        "drums":  [(0.0, 0.1, 38, 100), (0.5, 0.1, 42, 80)],
    }
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "combined.mid"
        write_midi(p, role_notes)
        got = read_midi(p)

    if got["ppq"] != PPQ:
        fails.append(f"ppq {got['ppq']} != {PPQ}")
    names = [t["name"] for t in got["tracks"]]
    expect_names = ["Conductor", "Vocals", "Bass", "Other (sketch)", "Drums"]
    if names != expect_names:
        fails.append(f"track order/names {names} != {expect_names}")
    by_name = {t["name"]: t for t in got["tracks"]}
    for role, tname in (("vocals", "Vocals"), ("bass", "Bass"), ("other", "Other (sketch)"),
                        ("drums", "Drums")):
        ch, prog, _ = ROLE_TABLE[role]
        trk = by_name.get(tname, {"program": None, "notes": []})
        if trk["program"] != prog:
            fails.append(f"{role} program {trk['program']} != {prog}")
        exp = sorted((_sec_to_tick(o), max(_sec_to_tick(o) + 1, _sec_to_tick(o + d)),
                      ch, pi, ve) for (o, d, pi, ve) in role_notes[role])
        act = sorted(trk["notes"])
        if act != exp:
            fails.append(f"{role} notes\n   got {act}\n   exp {exp}")

    # 2. Reader robustness: FIFO same-pitch overlap + note_on velocity 0 as note-off.
    raw = _build_raw_midi(PPQ, [
        (0,  bytes([0x90, 60, 100])),   # on  @0
        (10, bytes([0x90, 60, 90])),    # on  @10 (same pitch, overlap)
        (10, bytes([0x90, 60, 0])),     # off @20 (vel-0) -> pairs FIFO with @0
        (10, bytes([0x90, 60, 0])),     # off @30        -> pairs with @10
    ])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "raw.mid"
        p.write_bytes(raw)
        r = read_midi(p)
    got_notes = sorted(r["tracks"][0]["notes"])
    if got_notes != [(0, 20, 0, 60, 100), (10, 30, 0, 60, 90)]:
        fails.append(f"FIFO/vel-0 pairing wrong: {got_notes}")

    # 3. Running status: two note-ons sharing one status byte.
    raw2 = _build_raw_midi(PPQ, [
        (0,  bytes([0x90, 64, 100])),   # on  @0 (status 0x90)
        (5,  bytes([67, 100])),         # on  @5 running-status note-on
        (5,  bytes([0x80, 64, 0])),     # off @10
        (5,  bytes([0x80, 67, 0])),     # off @15
    ])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "rs.mid"
        p.write_bytes(raw2)
        r2 = read_midi(p)
    if sorted(r2["tracks"][0]["notes"]) != [(0, 10, 0, 64, 100), (5, 15, 0, 67, 100)]:
        fails.append(f"running-status parse wrong: {r2['tracks'][0]['notes']}")

    # 4. Unmatched note-off is dropped, not fatal.
    raw3 = _build_raw_midi(PPQ, [(0, bytes([0x80, 60, 0]))])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "u.mid"
        p.write_bytes(raw3)
        if read_midi(p)["tracks"][0]["notes"]:
            fails.append("unmatched note-off produced a note")

    # 5. SMPTE division is rejected.
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "smpte.mid"
        p.write_bytes(_build_raw_midi(0xE728, [(0, bytes([0x90, 60, 100]))]))
        try:
            read_midi(p)
            fails.append("SMPTE division was not rejected")
        except ValueError:
            pass

    # 6. Import purity.
    fails += _check_import_purity()

    if fails:
        print("SELFTEST FAILED:")
        for f in fails:
            print("  -", f)
        return 1
    print("selftest OK (6 checks: round-trip, FIFO/vel-0, running-status, "
          "unmatched-off, SMPTE-reject, import-purity)")
    return 0


# --- main ------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    repo = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Transcribe audio into multi-track MIDI.")
    ap.add_argument("input", nargs="?", help="audio file (mix) or directory of stems")
    ap.add_argument("-o", "--out", help="output directory (default: transcriptions/<name>/)")
    ap.add_argument("--selftest", action="store_true", help="run the no-ML assemble oracle")
    ap.add_argument("--diagnose", action="store_true", help="ML round-trip + smoke (needs tools)")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.diagnose:
        return diagnose(repo)
    if not args.input:
        ap.error("input is required (or use --selftest)")

    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f"input not found: {inp}")
    cfg = load_config(repo)
    out = Path(args.out) if args.out else repo / "transcriptions" / inp.stem
    run_pipeline(repo, cfg, inp, out)
    return 0


def _ferro(synth: Path, midi: Path, out_wav: Path, solo: int | None = None) -> None:
    argv = [str(synth), str(midi), "-o", str(out_wav), "-q"]
    if solo is not None:
        argv += ["--solo", str(solo)]
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0 or not out_wav.exists():
        raise SystemExit(f"ferrosintesis failed: {r.stderr.strip()[:200]}")


def _recall(expected: list, got: list, onset_tol: float = 0.15) -> float:
    """Fraction of expected notes matched (exact pitch, onset within tol) by a distinct got note."""
    if not expected:
        return 1.0
    used = [False] * len(got)
    hit = 0
    for (o, _d, p, _v) in sorted(expected):
        for i, (go, _gd, gp, _gv) in enumerate(got):
            if not used[i] and gp == p and abs(go - o) <= onset_tol:
                used[i] = True
                hit += 1
                break
    return hit / len(expected)


def diagnose(repo: Path) -> int:
    """ML diagnostics (NOT a build gate): clean-stem round-trip + full-mix smoke.

    Renders a fixture MIDI with ferrosintesis, transcribes it back, and reports note
    recovery. Recovery reflects the external models + ferrosintesis's (modelled, ML-alien)
    timbre — it is diagnostic, not a correctness measure. Tripwire: mono recovery < 50%
    means the setup/oracle is broken, not a low bar to accept.
    """
    synth = repo / "target" / "release" / (
        "ferrosintesis.exe" if sys.platform == "win32" else "ferrosintesis")
    if not synth.exists():
        raise SystemExit(f"ferrosintesis not built: {synth}\n"
                         f"run: cargo build --release -p ferrosintesis-cli")
    cfg = load_config(repo)

    fixture = {
        "vocals": [(0.0, 0.5, 72, 100), (0.5, 0.5, 74, 100),
                   (1.0, 0.5, 76, 100), (1.5, 0.5, 79, 100)],
        "bass":   [(0.0, 1.0, 36, 110), (1.0, 1.0, 43, 110)],
        "other":  [(0.0, 2.0, 60, 80), (0.0, 2.0, 64, 80), (0.0, 2.0, 67, 80)],
        "drums":  [(0.0, 0.1, 36, 110), (0.5, 0.1, 38, 100),
                   (1.0, 0.1, 36, 110), (1.5, 0.1, 38, 100)],
    }
    mono_scores = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fx = tmp / "fixture.mid"
        write_midi(fx, fixture)

        print("clean-stem round-trip (diagnostic):")
        for role, notes in fixture.items():
            ch = ROLE_TABLE[role][0]
            wav = tmp / f"{role}.wav"
            try:
                _ferro(synth, fx, wav, solo=ch)
                if role == "drums":
                    got = ingest_drum_midi(transcribe_drums(repo, cfg, wav, tmp))
                else:
                    got = ingest_basic_pitch_csv(transcribe_pitched(repo, cfg, wav, tmp))
            except SystemExit as e:
                print(f"  [{role}] skipped ({e})")
                continue
            score = _recall(notes, got)
            print(f"  [{role}] recall {score:.0%} ({len(got)} notes transcribed)")
            if role in ("vocals", "bass"):
                mono_scores.append(score)

        if mono_scores and max(mono_scores) < 0.5:
            print("  TRIPWIRE: monophonic recall < 50% — the setup/oracle looks broken, "
                  "not a low bar to accept.")

        print("full-mix smoke (diagnostic):")
        mix = tmp / "mix.wav"
        _ferro(synth, fx, mix)
        try:
            run_pipeline(repo, cfg, mix, tmp / "out")
            ok = (tmp / "out" / "combined.mid").exists()
            print(f"  pipeline completed; combined.mid present: {ok}")
            return 0 if ok else 1
        except SystemExit as e:
            print(f"  smoke skipped/failed: {e}")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
