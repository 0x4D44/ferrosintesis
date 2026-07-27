# Winter Guests

A two-part instrumental (9:26 + 9:02) in the spirit of Mike Oldfield, with
two guest sorties made to belong rather than clash: **ABBA** (*The
Visitors*' cold sequenced arpeggios; *Super Trouper*'s stacked-thirds
choruses, off-beat piano octaves and the truck-driver gear change) and the
**Crash Test Dummies** (*Mmm Mmm Mmm Mmm*'s low wordless baritone hum).

All material is original. The trick that keeps the guests from fighting is
**one theme with three machine-verified guises** — hummed low (CTD), stacked
as a parallel-thirds chorus (ABBA), and unwound as an Oldfield guitar line —
all reducing to the same strong-beat skeleton. The piece opens in E minor
and closes in E major; the ABBA gear change carries it there. See `ALBUM.md`
for the movement map and the controller-writing notes.

## Files

| Path | Role |
|------|------|
| `engine.py` | Composition toolkit + MIDI writer + parser (pure stdlib). The Signal Fire engine plus v0.7 helpers: `vowel`, `rpn`/`bend_range`/`fine_tune`, `portamento_on/off`, `aftertouch`, `sostenuto`, `soft_pedal`, `lyric`, `keysig`. |
| `material.py` | The Guest theme, its three guises, the two grounds, the cold arpeggio and 7/8 cells, the parallel-thirds stack — with a self-verifying oracle. |
| `conductor.py` | Both parts' grids as data (a `Part` class): tempo maps, time signatures, key signatures, markers, 16-channel setup, program changes. |
| `movements/m*.py` | The six movements, one module each (m1–m3 Part One, m4–m6 Part Two). |
| `verify.py` | 14 oracles per part; `build.py --verify` runs them. |
| `analyze.py` | Stdlib WAV verifier (per-movement RMS/correlation/centroid, click + silence scans); `--track N` picks the part. |
| `build.py` | `python3 build.py` rebuilds both parts; `--verify` checks them. |
| `midi/01 - Winter Guests, Part One.mid`, `midi/02 - …, Part Two.mid` | Rendered output, committed. |
| `album_manifest.json` | Machine-readable metadata with both timed movement maps. |

Builds are reproducible: each part has a fixed seed (20260707 / 20260708).

## Listening

Render with **[ferrosintesis](../../../crates/ferrosintesis/README.md)** v0.7, which grew a set of
expression features for this piece — CC70 choir vowel morph, RPN bend-range
and fine-tune, portamento, filter resonance, channel aftertouch, and the
sostenuto / una-corda pedals:

```powershell
cargo build --release -p ferrosintesis-cli
New-Item -ItemType Directory -Force target\renders | Out-Null
.\target\release\ferrosintesis.exe "albums\fable5\Winter Guests\midi\01 - Winter Guests, Part One.mid" -o "target\renders\Winter Guests, Part One.wav"
.\target\release\ferrosintesis.exe "albums\fable5\Winter Guests\midi\02 - Winter Guests, Part Two.mid" -o "target\renders\Winter Guests, Part Two.wav"
```

Each part renders in well under a minute; the WAVs land in `target/renders/`
(git-ignored, reproducible). The tagged Opus listening copies are git-ignored
build output produced by `python3 build.py` (run from the repo root); they land under
`listening/Claude Fable 5/Winter Guests/`. The MIDI is valid General MIDI, so any GM synth
works too — though the vowel morph, portamento and aftertouch are
ferrosintesis features a stock wavetable will ignore.

*Honest caveat:* this machine has no audio output. Both the MIDI and the
rendered audio were verified by measurement — 14 structural oracles per part
(including the tri-guise counterpoint and the RPN-aware bend hygiene), then
RMS/centroid/correlation profiles, click and silence scans, and solo-stem
checks of the signature features. It has not been auditioned by a human ear.
If something lands oddly, say so and I'll adjust.

## Easter eggs

- The humming is written into the file as **lyric events** — a MIDI player
  that shows lyrics will display "Mm… hm…" through "The Humming" and
  "(goodnight)" at the very end.
- Part One ends on a deliberately **unresolved half-cadence** (the guests
  are inside but unsettled); the final hum of Part Two resolves to the tonic
  it withheld.
