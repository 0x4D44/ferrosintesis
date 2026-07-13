# ferrosintesis Reference Audition

A **reference tool, not a record.** Every distinct ferrosintesis voice, drum voice,
controller and alt-bank voicing, played **one at a time, dry and flat**, so each can
be heard and identified. Where `demos/synth_feature_showcase/` is a musical showpiece
that layers instruments, this isolates them — so you can answer "what does GM 57 sound
like?" and A/B two voices as a comparison of *timbre*, not of *writing*.

Six tracks, ~13 min:

| # | Track | Content |
|---|-------|---------|
| 1 | Keys, Chromatic, Organ, Guitar | GM 0–31 |
| 2 | Bass, Solo Strings, Ensemble, Brass | GM 32–63 |
| 3 | Reed, Pipe, Lead, Pad | GM 64–95 |
| 4 | FX, World, Percussive, Noise | GM 96–127 |
| 5 | Kit Roll-Call | every channel-10 drum voice, the Brush kit, the hi-hat choke group, a tom velocity sweep |
| 6 | Controllers and Effects | reverb, chorus, echo, vibrato, Leslie, filter/resonance, sustain, vowel morph, breath, bend, aftertouch, portamento, and the no-CC A/Bs |

Each melodic slot: reset the channel, switch program (and bank), force the sends dry,
play a fixed rising figure and a held note or chord, let it ring, then choke it with
**CC120** so the gap is clean. The MIDI markers name every slot, and the `lyrics/*.txt`
index (embedded as the opus `LYRICS` tag) gives a timestamped table of contents.

## How to use it

- **Listen** by rendering with `python build.py` from the repo root (the `.opus` is
  git-ignored build output); the tagged files land under
  `listening/ferrosintesis/ferrosintesis Reference Audition/`, scrubbable by the
  timestamped index in each track's tags.
- **Hear one voice** by finding it in the index (e.g. "1:30 GM 057 Trombone").
- **A/B a voice against its alt-bank twin** — each alt voicing is inlined immediately
  after its default (e.g. GM 019 Church Organ, then GM 019 [alt] = the legacy Leslie
  organ).

## Rebuild / verify

```
python build.py            # write midi/*.mid, lyrics/*.txt, album_manifest.json
python build.py --verify   # rebuild in memory, compare to disk, run structural oracles
python analyze.py          # audio oracles: every slot audible, no voice masks the next
                           #   (needs build/wav/*.wav - render the MIDI first)
```

`verify.py` proves coverage (every distinct voice, alt voicing, drum key and effect
CC), flat authoring (no humanisation, so the A/B is honest), dry authoring (CC91/93/94
zeroed after each program change) and the CC120 gaps. `analyze.py` proves, on the real
render, that **every voice makes a sound** and that **no voice's tail masks the next**
— both as ratios, because the CLI peak-normalises the whole render.

## Known limits (stated, not hidden)

- **GM 031 Guitar Harmonics** sounds at a natural harmonic, not the written key (2f
  below key 64), so its slot is auditioned low and labelled.
- **GM 109 Bagpipe** always spawns a drone alongside the chanter (`engine.rs:1039`),
  so it is the one program that cannot be auditioned as a single voice.
- **Aliases** (e.g. GM 001/002/003 = GM 000) render identically once dry, so they are
  auditioned once as their canonical voice and cross-referenced in the index rather
  than duplicated.

## Regenerate the listening copies

From the repo root, with a built `ferrosintesis` CLI and `ropusenc` on PATH:

```
cargo build --release -p ferrosintesis-cli
python render_opus.py --album "ferrosintesis Reference Audition"
```
