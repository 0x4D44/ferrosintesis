# ferrosintesis-samples-fretnoise

Embedded **owner-recorded fret noise** (finger-slide one-shots) for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis) — twelve round-robin takes, mono
16-bit 44.1 kHz.

These play **GM program 120, Guitar Fret Noise**. All twelve are slides on the wound courses of
an Eastman E1D dreadnought with the strings damped hard at the nut, so they carry winding rasp
and no ringing pitch. The bank is a round-robin one-shot: successive notes advance through the
takes so repeated fret noise does not machine-gun, and the written pitch is ignored, as GM
specifies for the sound-effects block.

It is the **default** GM 120 voice. The modeled band-passed noise burst it replaced is retained
as the `--no-samples` (and `default-features = false`) fallback — that burst measured ~12 dB
quieter than the Roland SC-55mkII and Yamaha S-YXG50 references relative to their own steel
guitar, and was an octave-wide hiss rather than a narrow-band rasp with body
(MM-BUG-KILN-00040).

Recorded by the repository owner (2026) on the same guitar and string set as the GM 25 steel
banks, and dedicated **CC0 1.0** (public domain) — no attribution required. The takes, level
measurements, cut map and bake procedure are in `PROVENANCE.md`. Consumers normally reach this
crate through `ferrosintesis`.
