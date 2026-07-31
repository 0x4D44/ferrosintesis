# Sub Rosa

A single-track instrumental (7:34) in the **Enigma** idiom —
plainsong over a fast programmed groove (124 bpm), a melodic synth-bass
hook, a shakuhachi that answers the choir, glass and whispers in a big
dark room.  *Sub rosa*: "under the rose" — in secrecy.

The brief uses Enigma-vocabulary gestures (chant + groove + breath) and asks
for a new composition rather than a reconstruction of a named piece. The
whispered Latin was written for this track and stored in the MIDI lyric lane.

## Shape

| time | movement | what happens |
|------|----------|--------------|
| 0:00 | Sigillum | drone, first closed-mouth hum, heartbeat, bell |
| 0:30 | The Chant | the groove ignites; the chant arrives (mm) |
| 2:03 | The Bamboo Voice | shakuhachi call-and-response; the bass drives |
| 3:36 | Sub Rosa | breakdown: whispers, Morse, a 12-semitone glide solo |
| 4:38 | Limina | the chant reharmonized and at full voice (ah) |
| 6:42 | Afterglow | the chant finally cadences; the door closes |

## The machine-verified DNA (`material.py`)

- **One chant, two grounds.** The chant's strong-beat skeleton
  `[1 2 3 2 5 4 1 2]` is a chord tone of every bar of BOTH the verse
  ground (Dm C Bb C) and the climax reharmonization (Bb C Dm Am F Gm
  Bb C) — so Limina restates the same melody over new harmony without
  touching a note.  Plainsong manners are also law: range ≤ a minor
  7th, no leap wider than a 4th, and the line hangs on an unresolved
  9th until the Afterglow cadence finally lands it on the tonic.
- **A bass that is a melody, provably.** One hook in three guises
  (verse / drive / climax); the oracle requires root-or-fifth-or-octave
  on the strong beats and **≥ 5–6 distinct pitches per bar** in the
  fast guises.
- **A strictly pentatonic flute.** Every shakuhachi note must fall in
  the D minor pentatonic; the phrases are built from long tones so the
  scoops, bends and breath vibrato have somewhere to live.

## The synth features it plays (ferrosintesis ≥ v0.7)

CC70 vowel morph (the chant goes *mm → oo → ah* across the piece),
RPN 0 bend range (the M4 glide solo sighs across 5–7 semitone bends),
RPN 1 fine-tune (choir II beats 6 cents flat against choir I in the
breakdown), CC5/CC65 portamento (fretless-style bass slides, the glide
lead), channel aftertouch (pad and chant swells), CC1 (flute breath
vibrato; the organ Leslie spin-up in Limina), CC74 wah LFO (guitar
skanks) and the closing filter on the pad, CC71 resonance rides on the
sequencer, CC64/66/67 (the breakdown piano holds all three pedals),
CC68 legato bass runs, echo throws (CC94), autopan, and a woodblock
that taps **SUB ROSA** in Morse in the title movement.

## Regenerate / verify / listen

```powershell
python3 build.py             # rebuild midi + album_manifest.json
python3 build.py --verify    # 16 oracles: material, structure, CC
                            # inventory, vowels, pedals, portamento,
                            # RPN/bend hygiene, Morse, dynamics, bounds
```

Listen by rendering with `python3 build.py` from the repo root (or
[ferrosintesis](../../../crates/ferrosintesis/README.md) directly); the tagged
`listening/Claude Fable 5/Sub Rosa/01 - Sub Rosa.opus` is git-ignored build output.  The audio was verified
numerically: the RMS arc follows the movement plan (Limina loudest at
−19.2 dB, the breakdown and afterglow receding), no dead air, no
clicks, and the headline features were measured on rendered stems —
the *ah* chant is 2.65× more formant-open than the *mm* chant, the
climax bass moves 1.6× more envelope flux than the verse, the Leslie
tremulant peaks at ~6.7 Hz once spun up, and the glide solo's bend
measures ~+6 semitones mid-ramp.
