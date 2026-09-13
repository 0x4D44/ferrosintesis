# ferrosintesis-samples-bottle

Embedded CC0 blown-bottle loop sample for
[ferrosintesis](https://github.com/0x4D44/ferrosintesis): the GM 76 blown bottle. A
single real "blown bottle" recording (Freesound 349867 "Blown Bottle Two" by Terry93D),
released **CC0 1.0**.

The FLAC is a mono 16-bit 44.1 kHz looped take (measured root ~205 Hz): a recorded blow
that swells in over ~0.3 s then holds a ~1.2 s plateau body. `ferrosintesis` plays the
attack through into a pitch-synchronous loop of the recorded body (`BottleLoopVoice`).
The historical/source filename `bottleloop_G3.flac` is retained for compatibility; it is
not an equal-tempered pitch claim. Consumers must use the measured root 205.0 Hz
(approximately G-sharp 3), exposed as `MEASURED_ROOT_HZ` by this crate.
Consumers normally access this crate through `ferrosintesis`, not directly. The sample is
CC0 1.0 / public-domain — no attribution required; provenance is in `PROVENANCE.md`.
