# The Signal Fire

A single continuous 16:52 instrumental in the spirit of Mike Oldfield — a
deliberate cross between *Incantations Part IV* (a guitar solo that builds
for five minutes), *The Songs of Distant Earth* "Ascension" (ambient pools,
a filter that opens over minutes, the lift into major), *Tubular Bells III*
(minor-key drive, bells over four-on-the-floor) and *The Millennium Bell*
"Mastermind" (funk bass riff, wah guitar, Hammond organ).

All material is original: one bass riff in three rhythmic guises (4/4
sixteenth funk, a 10/8 additive ostinato grouped 3+3+2+2, and an augmented
half-time version), and three themes written over the same i–♭VII ground so
they stack in counterpoint at the finale. See `ALBUM.md` for the
movement-by-movement map and the controller-writing notes.

## Files

| Path | Role |
|------|------|
| `engine.py` | Composition toolkit + MIDI writer + parser (pure stdlib). Extends the Hollow Hill engine with `vibrato`, `wah`, `autopan`, `echo_throw`, `sustain`, `leslie`, `detune`, `cc_curve`. |
| `material.py` | The riff, three themes and the lattice split — with a self-verifying oracle proving the counterpoint and skeleton promises. |
| `conductor.py` | The global grid as data: tempo map, time signatures, markers, 16-channel setup, every scheduled program change. |
| `movements/m*.py` | The six movements, one module each. |
| `verify.py` | Eight structural oracles; `build.py --verify` runs them all. |
| `analyze.py` | Stdlib WAV verifier: per-movement RMS/correlation/centroid, click scan, silence scan. |
| `build.py` | `python build.py` rebuilds; `--verify` checks the rendered MIDI. |
| `midi/01 - The Signal Fire.mid` | Rendered output, committed. |
| `album_manifest.json` | Machine-readable metadata with the timed movement map. |

Builds are reproducible: humanisation comes from one fixed seed (20260706).

## Listening

Render with **[ferrosintesis](../../../crates/ferrosintesis/README.md)** v0.6, which grew three
controller features for this piece — CC1 mod-wheel vibrato and Leslie
spin-up (with real rotor inertia), a CC74 per-channel filter (the wah and
the slow openings), and CC64 sustain:

```powershell
cargo build --release -p ferrosintesis-cli
New-Item -ItemType Directory -Force target\renders | Out-Null
.\target\release\ferrosintesis.exe "albums\fable5\The Signal Fire\midi\01 - The Signal Fire.mid" -o "target\renders\The Signal Fire.wav"
```

Renders in under a minute; the WAV lands in `target/renders/` (git-ignored,
reproducible). The committed Opus listening copy lives at
`listening/Claude Fable 5/The Signal Fire/01 - The Signal Fire.opus`. The MIDI remains valid General MIDI, so any GM synth or a
real sample library works too — 16 channels with mid-piece program changes
(the winds channel is whistle, fiddle and flute in different movements; the
bells channel is a tremolo mandolin until the peal).

*Honest caveat:* this machine has no audio output. Both the MIDI and the
rendered audio were verified by measurement — eight structural oracles
(counterpoint, controller inventory, bend hygiene, dynamics arc, gaps,
bounds), then RMS/centroid/correlation profiles, a click scan and a silence
scan on the WAV, plus solo-stem checks of the signature effects. It has not
been auditioned by a human ear. If something lands oddly, say so and I'll
adjust.

## Easter eggs

- "Signal", ~1:40: a distant woodblock taps **CQ CQ CQ** — the radio
  general call, "calling anyone". The beacon is lit.
- "Afterglow", ~16:20: the woodblock answers **K** — "go ahead". Someone
  saw the fire.
