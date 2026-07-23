# samples/ — source instrument recordings

Raw instrument recordings, **one subdirectory per instrument**, kept as the source
material the per-note synth sample banks are extracted from. As the fleet records more
instruments (this started with the banjo), they land here.

## What lives here vs. in the crates

| | Where | Format | Role |
|---|---|---|---|
| **Source recording** (a whole note-by-note take) | `samples/<instrument>/*.opus` | Ogg Opus (trimmed, mono, ~160 kbps) | the raw performance — re-extract from this |
| **Per-note sample bank** (trimmed onset per zone) | `crates/ferrosintesis-samples-*/samples/*.wav` | 16-bit PCM WAV | embedded in the synth via `include_bytes!`, parsed as PCM at build time |

The crate WAVs **must stay PCM** — the synth's `parse_wav` reads uncompressed PCM, so the
embedded banks cannot be opus. The `samples/` recordings here are the *upstream* source:
trimmed of dead air and Opus-compressed to keep the repo small (a 35 MB take → ~4 MB), while
staying good enough to re-extract per-note zones if a bank is ever re-tuned.

These `.opus` files are **source, not build output** — a `.gitignore` exception tracks them
(the repo otherwise ignores `*.opus`, which is the *render* output that once bloated `.git`).
Keep this archive small: one file per recording, rarely changed.

## Inventory

| Instrument | File | Recorded | Player | Extracted to |
|---|---|---|---|---|
| 5-string banjo (open-G gDGBD) | `banjo/banjo-5string-openG-2026-07-23.opus` | 2026-07-23 | Arthur (Tascam DR-series, close-mic) | `crates/ferrosintesis-samples-orchestral2/samples/banjo_*.wav` (GM 105) |

## Re-extracting a bank from a recording

The per-note extraction (onset-segment → robust pitch/QC gate → trim to ~0.5 s onset →
peak-normalize → TPDF-dither to 16-bit) is documented per-instrument in
`tools/ferrosintesis-samples/README.md`. A recording here is the input to that step.
