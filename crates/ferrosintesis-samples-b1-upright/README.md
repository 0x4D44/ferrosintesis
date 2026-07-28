# ferrosintesis-samples-b1-upright

Embedded **first-party** Yamaha **B1 acoustic upright** samples — Arthur's own
piano, recorded on a Tascam DR-05 (2026-07-23). Voices the **GM 0 Acoustic Grand
default** (CC0=0) in
[ferrosintesis](https://github.com/0x4D44/ferrosintesis): a real upright, not a
grand — a warmer, boxier acoustic with genuine per-note inharmonicity.

**Two recorded timbre layers** — normal / hard — sampled from two separate
dynamic passes, so hard is a genuinely brighter recorded spectrum rather than one
sample re-EQ'd. The bank carries 52 mono 16-bit 44.1 kHz WAV bodies across the two
layers, embedded via `include_bytes!`. Loudness comes from the engine's shared
velocity law; the layers supply timbre per dynamic (see `PROVENANCE.md`).

Each WAV keeps the accepted **1.5 seconds of recorded body** and appends the same
note's real, non-looping 3.7–8.0 second decay in a versioned RIFF chunk. The tail
begins at 1.35 seconds, is low-passed and decimated to 11.025 kHz, and uses
mu=255 one-byte companding. Runtime decodes it during sample prewarm, crossfades
from the untouched body, and stops at the recording's natural endpoint. There is
no synthetic piano handoff and no repeated sustain loop. The samples-off path
remains the modeled piano.

A third **soft** pass was recorded and then dropped (2026-07-24). Measured against
`normal` note-for-note with the noise subtracted, it was only **+0.8 dB** apart in
spectral tilt — the same timbre — while carrying **11 dB less SNR** (28.1 dB vs
39.2 dB), so it contributed audible recorder hiss and almost no tone. The raw pass
is still in the archived take under `samples/b1-upright/`, so it can be re-baked if
a future capture makes it worth carrying.

Roots are the **measured first partial** of each note, so the bank plays at exact
equal temperament while keeping the upright's inharmonicity and Railsback stretch.

**Licence: CC0 1.0** — Arthur's own instrument, performance and recording, dedicated
to the public domain. No attribution required, for source or binary redistribution.

Regenerate and verify the complete bank from the repository root:

```powershell
python3 tools/ferrosintesis-samples/prepare.py --only=b1upright
python3 tools/ferrosintesis-samples/regen_samples_table.py crates/ferrosintesis-samples-b1-upright
cargo test -p ferrosintesis-samples-b1-upright
```

The first command decodes the committed Opus archives under `samples/b1-upright/`,
slices, and bakes all 52 WAVs. The inventory updater validates every terminal `b1t `
natural-tail chunk before updating `FILE_COUNT`, `EXPECTED_BYTES`, and
`EXPECTED_TAIL_BYTES`; review its reported old and new pin values before committing.
It changes only the marked inventory and derived pins, preserving the handwritten
B1 tail validator.
