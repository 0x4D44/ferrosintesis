# Hollow Hill

A two-part instrumental epic (26½ minutes) in the spirit of Mike Oldfield —
the long-form, side-of-an-LP shape of *Tubular Bells*, with colours borrowed
from across that catalogue: the additive-metre ostinato and the instrument
roll-call finale (*Tubular Bells I/II*), restless interlocking acoustic
guitars, a false ending and a hidden Morse-code message (*Amarok*), ambient
electronic pools (*The Songs of Distant Earth*), and folk dances to finish
(*Tubular Bells*' hornpipe, by way of a jig and a reel of my own).

The themes, riffs, and dance tunes were generated for this piece. The 13-quaver
ostinato (3+3+3+2+2) is deliberately different from Oldfield's 15. This process
description is not a guarantee against incidental similarity. See `ALBUM.md`
for the movement-by-movement map.

## Files

| Path | Role |
|------|------|
| `engine.py` | Composition toolkit + type-1 MIDI writer + verifying parser. Pure Python standard library. |
| `material.py` | The recurring themes, written as scale degrees so they can be recast in any mode. |
| `part_one.py` / `part_two.py` | The two roadmaps — every section, layer and entrance. |
| `build.py` | `python3 build.py` rebuilds; `python3 build.py --verify` checks the rendered MIDI. |
| `tracks/NN_*.py` | One thin entry point per track. |
| `midi/NN - *.mid` | Rendered output, committed. |
| `album_manifest.json` | Machine-readable metadata, including a timed section map. |

Builds are reproducible: humanisation (timing/velocity jitter) comes from a
fixed per-track seed.

## Listening

The project render uses **[ferrosintesis](../../../crates/ferrosintesis/README.md)**,
the companion Rust synthesizer developed alongside this album.

```powershell
cargo build --release -p ferrosintesis-cli
New-Item -ItemType Directory -Force target\renders | Out-Null
.\target\release\ferrosintesis.exe "albums\fable5\Hollow Hill\midi\01 - Hollow Hill, Part One.mid" -o "target\renders\Hollow Hill, Part One.wav"
.\target\release\ferrosintesis.exe "albums\fable5\Hollow Hill\midi\02 - Hollow Hill, Part Two.mid" -o "target\renders\Hollow Hill, Part Two.wav"
```

The WAVs land in `target/renders/`
(git-ignored — they are reproducible). The Opus listening copies are
git-ignored build output too: run `python3 build.py` from the repo root to
render them under `listening/Claude Fable 5/Hollow Hill/`. Other GM-compatible
instruments can load the MIDI, but voicing and supported extensions will differ.
Sixteen channels are used, with
a handful of mid-piece program changes (the fretless bass and sweep pad only
exist in the ocean movements, the mandolin borrows the timpani channel for
the roll call, and so on).

*Honest caveat:* this machine has no audio output, so both the MIDI and the
rendered audio were verified by measurement — durations, tempo maps, note
ranges, a true-silence scan (only the two deliberate gaps exist: the breath
after the dance, and the false ending), RMS dynamics profile, and a click
scan. It has not been auditioned by a human ear. If something lands oddly,
tell me and I'll adjust.

## Easter eggs

- Part Two, "The Night Ocean", ~7:12: a distant woodblock taps **ARTHUR** in
  Morse code.
- Part Two ends with a false ending — a full E-major cadence, three seconds of
  silence — before the reel bursts in. Stay in your seat.
