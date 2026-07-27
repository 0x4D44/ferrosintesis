# ferrosintesis-samples-strings

Embedded **CC0 1.0 / public-domain** solo-bowed-string onset samples for
[`ferrosintesis`](https://crates.io/crates/ferrosintesis): real **solo cello**
(GM 42) and **solo double bass** (GM 43) attack transients. Each WAV is a mono
16-bit 44.1 kHz onset; the synth plays it as the note's attack and crossfades
into the modeled bowed-string waveguide sustain.

These replace the previous GM 42/43 onset, which repitched the VSCO cello-*section*
(`celens`) recording — an ensemble that read as a small cello section rather than a
soloist, and (for GM 43) as a cello an octave low rather than a double bass.

| Prefix | GM | Instrument | Source | License |
|--------|----|-----------|--------|---------|
| `cellosolo_*` | 42 | Solo cello (arco, down-bow) | Karoryfer × bigcat "Bigcat Cello" ([github](https://github.com/sfzinstruments/karoryfer-bigcat.cello), rev `6fd75fb`) | CC0-1.0 |
| `dbass_*` | 43 | Solo double bass (arco, non-vibrato) | VSCO 2 CE "Solo Contrabass" SusNV ([github](https://github.com/sgossner/VSCO-2-CE), rev `44030090`) | CC0-1.0 |
| `pizzbass_*` | 32 | Solo double bass (**pizzicato**), voices the acoustic bass | VSCO 2 CE "Solo Contrabass" pizz ([github](https://github.com/sgossner/VSCO-2-CE), rev `44030090`) | CC0-1.0 |

File names encode the **measured sounding pitch** (e.g. `cellosolo_C2_f.wav` sounds
C2 ≈ 65 Hz). Both source libraries label their files one octave below sounding
pitch; the bake in `tools/ferrosintesis-samples/prepare.py` measures every root and
names by the sounding pitch, so the zone tables never trust the source label.

No attribution is required (CC0). Regenerate with
`python3 tools/ferrosintesis-samples/prepare.py --only=cellosolo,dbass`.
