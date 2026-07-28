# MM-REQ-KILN-00164 — Kawai sample assets must be independently verifiable against pinned inputs

- **State:** Draft
- **Priority:** Could
- **Area:** Kawai sample assets / deterministic verification
- **Raised:** 2026-07-28
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-28, raised via `deltic reqs new`)

## Statement

The system must provide a non-mutating verification that rebuilds every Kawai zone, dynamic, and declared alias from the pinned VCSL revision and recipe, then compares the committed outputs for exact inventory, note identity, canonical PCM format, measured-root agreement, and declared payload sharing. The current generated canary at D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:222 checks aggregate bytes plus RIFF/WAVE magic. All 48 files are exactly 133,048 bytes, so same-length silence, swapped notes, or altered PCM can pass. D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\gen_crate_lib.py:8 notes these generated tests are self-consistent by construction. Current assets are structurally valid; this is prevention debt, not a claim of present PCM corruption. Existing MM-REQ-KILN-00033 covers only the Dark Salamander projection and MM-REQ-KILN-00144 covers packaged source pins, so neither supplies this Kawai output oracle. Proposed priority: Could. Proposed flow: heavy because the acceptance oracle must obtain or authenticate pinned upstream inputs without mutating tracked assets. Estimated effort: Medium.

## Notes
