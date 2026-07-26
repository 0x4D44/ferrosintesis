# ferrosintesis-samples-fretnoise

Embedded **owner-recorded fret noise** (finger-slide one-shots) for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis) — twelve round-robin takes, mono
16-bit 44.1 kHz.

These play **GM program 120, Guitar Fret Noise**. All twelve are slides on the wound courses of
an Eastman E1D dreadnought with the strings damped hard at the nut, so they carry winding rasp
and no ringing pitch. The bank is a round-robin one-shot: successive notes advance through the
takes so repeated fret noise does not machine-gun, and the written pitch is ignored, as GM
specifies for the sound-effects block.

The public API exposes `get` for lookup by exact WAV name, plus `take_name` and
`ROUND_ROBINS` for the wrapping 0-based round-robin sequence.

It is the **default** GM 120 voice. The modeled band-passed noise burst it replaced is retained
as the `--no-samples` (and `default-features = false`) fallback — that burst measured ~12 dB
quieter than the Roland SC-55mkII and Yamaha S-YXG50 references relative to their own steel
guitar, and was an octave-wide hiss rather than a narrow-band rasp with body
(MM-BUG-KILN-00040).

Recorded by the repository owner (2026) on the same guitar and string set as the GM 25 steel
banks, and dedicated **CC0 1.0** (public domain) — no attribution required. The takes, level
measurements, cut map and bake procedure are in `PROVENANCE.md`. Consumers normally reach this
crate through `ferrosintesis`.

Byte-for-byte reproduction belongs to one canonical generator environment:
64-bit CPython 3.14.3 on Windows x86-64 with NumPy 2.4.4. The bake refuses
another environment because NumPy does not promise version-stable FFT or random
output. From a `midi-music` checkout, create that environment and verify the
committed bank without writing it:

```console
py -3.14 -m venv venv\fretnoise-bake
venv\fretnoise-bake\Scripts\python -m pip install -r tools\ferrosintesis-samples\requirements-fretnoise-bake.txt
venv\fretnoise-bake\Scripts\python tools\ferrosintesis-samples\fretnoise_bake.py --verify
```

`BAKE-SHA256` pins every output independently. Verification re-bakes all twelve
files in memory, checks the generated and committed hashes, and writes nothing.
Omit `--verify` only when intentionally restoring the tracked WAVs from the
committed source cuts; the script validates every generated hash before its
first write.

Cross-platform or cross-version byte identity is not claimed. The sampled GM120
level, rasp spectrum, pitch independence, and one-shot lifetime are also guarded
by acoustic-tolerance oracles in `ferrosintesis`, so a deliberate future
canonical-environment change must satisfy both the re-pinned bytes and the
audible contract.
