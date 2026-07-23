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
| Steel-string acoustic, Eastman E1D — **picked** | `acoustic-guitar-eastman-e1d/picked.opus` | 2026-07-23 | Arthur (coincident stereo pair) | `crates/ferrosintesis-samples-orchestral2/samples/eastpick_*.wav` (GM 25 **default**) |
| Steel-string acoustic, Eastman E1D — **fingerstyle** | `acoustic-guitar-eastman-e1d/plucked.opus` | 2026-07-23 | Arthur (coincident stereo pair) | `crates/ferrosintesis-samples-orchestral2/samples/eastpluck_*.wav` (GM 25 **CC0 1**) |

Per-instrument provenance (signal chain, tuning, zone slice map) lives in each
instrument's own `README.md` where one is present.

## Re-extracting a bank from a recording

The per-note extraction (onset-segment → robust pitch/QC gate → trim to ~0.5 s onset →
peak-normalize → TPDF-dither to 16-bit) is documented per-instrument in
`tools/ferrosintesis-samples/README.md`. A recording here is the input to that step.

Two extraction paths exist today, and the duplication is known and deliberate for now:

- **Banjo** — `tools/ferrosintesis-samples/banjo_extract.py` segments the take itself
  (ffmpeg-decodes the archive, onset-segments, QC-gates, keeps the best take per semitone).
- **Eastman guitar** — the 8 anchor notes per articulation were cut once and committed
  lossless under `acoustic-guitar-eastman-e1d/zones/`, then baked through `prepare.py`'s
  ordinary one-file-per-zone path (`--only=eastpick` / `--only=eastpluck`). That keeps the
  bake stdlib-only and byte-reproducible with **no ffmpeg dependency**, at the cost of
  ~3 MiB of committed sources and a second mechanism.

The two were built independently and converged on the same two hazards, which any future
extractor must keep: an **octave-correct** f0 estimate (a plain harmonic template scores a
subharmonic exactly as well as the true fundamental), and an **onset-isolation / bleed**
gate (a take that begins inside the previous note's decay defeats onset-trimming). Folding
the guitar onto a generalised version of the banjo extractor is tracked in `scratchpad.md`.
