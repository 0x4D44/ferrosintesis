# ferrosintesis-samples-ydp-grand

Embedded **CC BY 3.0** FreePats YDP Grand (Yamaha Disklavier Pro) samples — the
**brighter** grand in the GM 1 audition, with a harder, more present hammer
strike than the GM 1 default (VCSL Kawai). Voices the **GM 1 Bright Acoustic
Piano alternate** (CC0=1) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

9 pitch zones (C2–C6) × single velocity = mono 16-bit 44.1 kHz WAVs, embedded via
`include_bytes!`. Extracted from the SF2's middle velocity layer; dynamics come
from the LA blend + model (see `PROVENANCE.md`).

**Licence: CC BY 3.0 — attribution required.** `NOTICE` credits **roberto@zenvoid.org**
(who produced the SoundFont for FreePats) and the underlying Zenph Studios / One Laptop
Per Child recordings. Copy the `NOTICE`, not this summary.

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=ydpgrand`.
