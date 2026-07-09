# transcribe.py — audio → multi-track MIDI

A stdlib-only orchestrator (the inverse of `render_opus.py`) that assembles free ML tools
to transcribe arbitrary audio into MIDI. It does **no DSP itself** — it shells out to
external tools, each installed in its own venv. Output is per-stem `.mid` files plus one
combined multi-track General-MIDI file.

Honest expectations: the output is a **rough draft to clean up in a DAW**, not a faithful
score. Monophonic parts (bass, a vocal line) and drums come out usable; the harmonic
"other" content (guitar/piano/pads) is best-effort and often needs re-voicing by hand.
See `wrk_docs/2026.07.09 - HLD - opus to midi transcription tool.md`.

## Usage

```
python transcribe.py song.opus            # a mix: auto-separate (Demucs) then transcribe
python transcribe.py stems_dir/           # a directory of pre-made stems, transcribed directly
python transcribe.py song.opus -o out/    # choose the output directory
python transcribe.py --selftest           # the no-ML assemble oracle (needs no tools)
```

- **Mix input** (a file) is separated into 6 stems (vocals/drums/bass/guitar/piano/other).
- **Stems input** (a directory) skips separation. Name files by role
  (`vocals`/`bass`/`drums`/`guitar`/`piano`/`other`, or common aliases like `vox`, `gtr`).
  A lone isolated stem: put it in a directory of its own.

## Prerequisites (installed separately, each in its own venv)

The ML tools have mutually incompatible dependencies, so they cannot share one
environment. Install each in its own venv and point `transcribe.local.json` at the
executables (copy `transcribe.local.json.example`). Python 3.11/3.12 is recommended for the
tool venvs (the ML stack lags newer Python).

| Tool | Role | Notes |
|------|------|-------|
| `ffmpeg` | decode/normalise input to WAV | usually already on PATH |
| Demucs (`htdemucs_6s`) | 6-stem separation | torch (CPU works, slow) |
| Spotify Basic Pitch | pitched-stem transcription | consumed via its note-event **CSV** |
| a drum ADT | percussion → GM ch-10 | tool TBD (install spike; see HLD Q-A) |

Missing tools produce a clear error naming the tool. The `--selftest` gate needs none of
them.

## Output layout

```
transcriptions/<name>/
  vocals.mid  bass.mid  guitar.mid  piano.mid  other.mid  drums.mid   # per-stem
  combined.mid                                                         # multi-track GM
```

Fixed role → channel/program mapping (forced, so the transcribers' own programs don't
define the arrangement): vocals→ch0/prog54, bass→ch1/prog33, guitar→ch2/prog27,
piano→ch3/prog0, other→ch4/prog0, drums→ch9 (GM percussion). MIDI is emitted un-quantised
at a fixed 120 BPM — quantise in your DAW.
