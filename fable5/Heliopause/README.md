# Heliopause

A two-part synth instrumental (4:48 + 3:44) in the **Jean-Michel
Jarre / Oxygène** idiom: analog sequencer cells whose filters never
sit still, slow warm harmony under fast surfaces, portamento leads,
wind-and-whoosh transitions, and big moments made by SUBTRACTION —
each part has a full drop where the machine cuts out and one voice
sings.  A aeolian throughout.

This is original material using Jarre-vocabulary gestures; it quotes
no existing piece.

## The machine-verified DNA (`material.py`)

- **One idea, mirrored.** Part Two's lead melody is Part One's THEME_A
  turned upside down — the oracle proves the inversion interval-by-
  interval (diatonic mirror, identical rhythm).
- **One theme, two grounds.** THEME_A's strong beats are chord tones
  of both the verse ground (Am G F G) and the climax lean (F G Am Em).
- **Triple counterpoint.** THEME_A, its answer THEME_B and the
  inversion are pairwise consonant on every strong beat — Part Two's
  "Perihelion" stacks all three at once, twice.
- **Sequencer and bass by construction**: the 16/12-slot ladder cells
  are all chord tones; the 8th-note bass pulse carries roots on the
  strong beats with five distinct pitches a bar.

## Shape

Part One: Solar Wind → The Sequencer → **Mirror Waltz (3/4)** →
The Drop (theremin on RPN bend range 12, ±5-semitone sighs) →
Two Suns (A + B together; Leslie organ; 16-vs-12 polymeter) →
Dissolve.

Part Two: Ignition → **Slipstream (6/8)** → Crosswind (4/4 stomp,
16-against-12 sequencers) → **Eclipse (6/8 drop)** → Perihelion (the
triple stack; the second sequencer detuned +6 cents) → Afterimage.

## Regenerate / verify / listen

```powershell
python build.py             # rebuild both parts + manifest
python build.py --verify    # material + 12 structural oracles / part
```

Listen via [hollowsynth](../hollowsynth/README.md) (v0.8) or the
committed `audio/*.opus`.  Renders measured clean: no dead air, no
discontinuities beyond drum onsets, both parts peaking in their
verified climax movements.
