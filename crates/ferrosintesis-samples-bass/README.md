# ferrosintesis-samples-bass

Embedded CC0 electric-bass onset samples for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis): finger (GM 33) and pick (GM 34),
also serving fretless (GM 35). A real Yamaha RBX bass guitar recorded by Andrea Biasior,
from the FreePats "Clean Electric Bass" (electric-bass-YR) sound bank, **CC0 1.0**.

Each WAV is a mono 16-bit 44.1 kHz attack transient; `ferrosintesis` crossfades it into the
modeled `Pluck` sustain. Consumers normally access this crate through `ferrosintesis`, not
directly. All samples are CC0 1.0 / public-domain — no attribution required; provenance is
in `PROVENANCE.md`. Regenerate with
`python3 tools/ferrosintesis-samples/prepare.py --only=fingerbass,pickbass`.
