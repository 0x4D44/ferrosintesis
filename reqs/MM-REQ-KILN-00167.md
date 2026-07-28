# MM-REQ-KILN-00167 — Steinway sample assets must be independently verifiable against pinned inputs

- **State:** Draft
- **Priority:** Could
- **Area:** Steinway sample assets / deterministic verification
- **Raised:** 2026-07-28
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-28, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The system must provide a non-mutating verification that authenticates or rebuilds every Steinway-B zone, dynamic, and declared alias from the pinned VCSL revision and recipe, then compares the committed outputs for exact inventory, note identity, canonical PCM format, measured-root agreement, deterministic output bytes, and declared payload sharing.

The current generated canary at crates/ferrosintesis-samples-vcsl-steinway/src/lib.rs:246-278 checks filenames, aggregate bytes, RIFF/WAVE magic, and get(). tools/ferrosintesis-samples/gen_crate_lib.py:4-9 generates its expectations from the same output directory, making them self-consistent by construction. All 54 files are exactly 133,048 bytes, so same-length silence, swapped notes, wrong dynamic aliases, or altered PCM can pass. Current assets were statically inspected and are structurally valid; this is prevention debt, not a claim of present audio corruption.

Implementation should share one verifier architecture with Draft MM-REQ-KILN-00164 for the Kawai VCSL bank, while retaining bank-specific source mappings and measured roots. Include swapped-note, silence, wrong-format, wrong-root, and undeclared-alias negative controls. Proposed priority: Could. Proposed flow: heavy because the acceptance oracle must authenticate pinned upstream inputs without mutating tracked assets. Estimated effort: Medium.

## Notes
