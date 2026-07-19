# Provenance — ferrosintesis-samples-bass

FreePats "Clean Electric Bass" (**electric-bass-YR**), a real Yamaha RBX bass guitar
recorded by Andrea Biasior, released **CC0 1.0 Universal** (public-domain dedication —
`LICENSE.txt` ships inside each archive, and the FreePats page:
<https://freepats.zenvoid.org/ElectricGuitar/clean-electric-bass.html>). No attribution
required; provenance given with thanks.

Pinned archives (SHA-256, GitHub release `2019-09-30`):

| Archive | SHA-256 | Program |
|---------|---------|---------|
| `FingerBassYR-SFZ+WAV-20190930.7z` | `7a8075f8560c0f397283b221e35139473a2517a6fc427beed4f3fffa0619333d` | GM 33 finger |
| `PickedBassYR-SFZ+WAV-20190930.7z` | `ba301f87e5e677d486d0c112950006531523479e54b891aef21dc71b754a0e3a` | GM 34 pick |

Baked by `tools/ferrosintesis-samples/prepare.py`: 7z-extract, trim to onset, re-measure the
root near the SFZ `key=` pitch (finger E1–D#2, pick E1–E2), write mono 16-bit 44.1 kHz.
GM 35 fretless rides the finger bank (the pluck attack is what the onset layer supplies; the
model carries the fretless "mwah").
