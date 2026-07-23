# ferrosintesis-samples-b1-upright

Embedded **first-party** Yamaha **B1 acoustic upright** samples — Arthur's own
piano, recorded on a Tascam DR-05 (2026-07-23). Voices a **GM 0 Acoustic Grand
alternate** (CC0 bank 5) in
[ferrosintesis](https://github.com/0x4D44/ferrosintesis): a real upright, not a
grand — a warmer, boxier acoustic with genuine per-note inharmonicity.

**Three recorded timbre layers** — soft / normal / hard — sampled from three
separate dynamic passes, so soft is a genuinely darker recorded spectrum and hard
a brighter one (not one sample re-EQ'd). ~74 mono 16-bit 44.1 kHz WAVs across the
three layers, embedded via `include_bytes!`. Loudness comes from the engine's
shared velocity law; the layers supply timbre per dynamic (see `PROVENANCE.md`).

Roots are the **measured first partial** of each note, so the bank plays at exact
equal temperament while keeping the upright's inharmonicity and Railsback stretch.

**Licence: MIT OR Apache-2.0** (the repo's own terms — this is Arthur's recording,
no third-party attribution required). See `LICENSE-MIT` / `LICENSE-APACHE`.

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=b1upright`
(decodes the committed opus archive under `samples/b1-upright/`, slices, and bakes).
