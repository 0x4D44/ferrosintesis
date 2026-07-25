# Provenance — ferrosintesis-samples-bottle

## Packaged family inventory

| Family | Files |
|--------|------:|
| `bottleloop_*` | 1 |

A single real "blown bottle" recording, released **CC0 1.0 Universal** (public-domain
dedication — no attribution required; provenance given with thanks).

| Field | Value |
|-------|-------|
| Freesound sound ID | **349867** |
| Title | "Blown Bottle Two" |
| Author | **Terry93D** |
| License | **CC0 1.0** (<https://creativecommons.org/publicdomain/zero/1.0/>) |
| Source page | <https://freesound.org/s/349867/> |

Committed CC0 source (2.0 s, un-re-fetchable without a Freesound login, so committed for
offline reproducibility):

| Source file | SHA-256 |
|-------------|---------|
| `tools/ferrosintesis-samples/freesound-src/bottle_G3.wav` | `56421959ee1aa62d43fa171b11f7626fa7ef08636abf9a3afed821c8d0e965fd` |

Baked to `samples/bottleloop_G3.wav` (mono 16-bit 44.1 kHz, 1.6500 s, measured root
**205.0 Hz**) by `tools/ferrosintesis-samples/prepare.py:bake_bottle_loop`
(`python prepare.py --only=bottle`), leaving a recorded attack that swells into a looped
plateau body (`ferrosintesis` finds the pitch-synchronous loop at construction). Voices
the GM 76 blown bottle.

The exact recipe, as the code applies it:

| Step | Value |
|------|-------|
| Trim | source frames 4411 … 77176 (0.1000 s … 1.7500 s) |
| Fade-in | 131 samples, linear |
| Fade-out | 2647 samples, quadratic `(1 − t)²` |
| Normalise | peak to 0.9 |

*(Corrected 2026-07-24, MM-BUG-KILN-00065.* The previous text said "trimmed 0.45–2.10 s"
of a source it describes as 2.0 s long — an interval that does not exist, and not what
the shipped asset contains. The values above were recovered by measuring the committed
WAV against the committed source, and are pinned by
`test_prepare.py:test_bottle_loop_reproduces_the_committed_asset`. That test asserts the
bake stays within 24 LSB of the shipped bytes; it does not reproduce them exactly,
because the original bake was never checked in and its float path is unknown. The bound
is tight — a one-sample trim error moves the output by 1045 LSB.)*
