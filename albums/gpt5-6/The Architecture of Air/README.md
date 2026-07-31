# The Architecture of Air

One 6:52 composition for the default ferrosintesis GM19 cathedral
organ, with sparse choir, tower bells, and timpani. The piece is both music and
an honest listening tour of the model: its technical demonstrations are built
into the dramatic form.

## Form

| Time | Section | What the organ reveals |
|---:|---|---|
| 0:00 | Stone Before Breath | Isolated MIDI 36 C with audible 32', 16', and 8' foundations |
| 0:41 | The Principal Walk | Staggered speech, chiff, and middle-register principal harmony |
| 1:35 | The Vault Answers | Contrapuntal manuals meeting a distant choir |
| 2:24 | Tremulant Light | One held consonance moving from dry pressure to the fixed 5.5 Hz tremulant |
| 3:22 | Windchest | Ten notes on one channel load the common chest, then shed to one recovering pipe |
| 4:22 | Mixtures in the Lantern | Organ-only notes above MIDI 84 expose the high mixtures before bells enter |
| 5:19 | Full Organ | Successively larger plena gather toward the final cadence |
| 5:50 | The Building Sings | Twelve-note full organ over the 32-foot C |
| 6:14 | Air After Stone | Every pipe releases; only the cathedral remains |

The organ stays centered. Chorus and echo remain authored at zero, so the width
and decay come from the dedicated cathedral room rather than generic effects.
The score explicitly selects bank zero before GM19; it never enters the legacy
secondary organ bank.

## Rebuild and verify

From this directory:

```powershell
python3 build.py
python3 build.py --verify
```

From the repository root, after building ferrosintesis:

```powershell
target\release\ferrosintesis.exe "albums\gpt5-6\The Architecture of Air\midi\01 - The Architecture of Air.mid" -o "target\organ-showcase\full.wav"
target\release\ferrosintesis.exe "albums\gpt5-6\The Architecture of Air\midi\01 - The Architecture of Air.mid" --solo 0 -o "target\organ-showcase\organ.wav"
python "albums\gpt5-6\The Architecture of Air\analyze.py" "target\organ-showcase\full.wav" "target\organ-showcase\organ.wav"
```

```sh
mkdir -p target/organ-showcase
target/release/ferrosintesis "albums/gpt5-6/The Architecture of Air/midi/01 - The Architecture of Air.mid" -o "target/organ-showcase/full.wav"
target/release/ferrosintesis "albums/gpt5-6/The Architecture of Air/midi/01 - The Architecture of Air.mid" --solo 0 -o "target/organ-showcase/organ.wav"
python3 "albums/gpt5-6/The Architecture of Air/analyze.py" "target/organ-showcase/full.wav" "target/organ-showcase/organ.wav"
```

`build.py --verify` checks the default-bank routing in the actual serialized
MIDI, register coverage, same-channel wind loading, tremulant plateaus, natural
stereo/effects routing, dramatic arc, room-only tail, and MIDI hygiene.
`analyze.py` verifies the rendered pedal fundamentals, mixture brightness,
5.5 Hz amplitude motion, wind-load contrast, climax, mono compatibility, and
multi-stage room decay.
