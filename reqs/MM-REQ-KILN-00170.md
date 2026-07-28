# MM-REQ-KILN-00170 — B1 sample assets must be independently verifiable against committed recordings

- **State:** Draft
- **Priority:** Could
- **Area:** B1 sample assets / deterministic verification
- **Raised:** 2026-07-29
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-29, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The system must provide a non-mutating verification that authenticates or
rebuilds every B1 normal/hard zone from the exact committed Opus recordings and
recipe, then compares the committed outputs per filename for exact inventory,
note assignment, PCM format, measured-root agreement, terminal natural-tail
metadata, and deterministic output identity.

The oracle must independently bind content to names. The current checks at
`D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-235149\crates\ferrosintesis-samples-b1-upright\src\lib.rs:284`
derive inventory from the output directory and pin only aggregate file/tail
bytes plus RIFF shape. Swapping the complete, equal-sized
`b1_normal_C1.wav` and `b1_normal_C3.wav` payloads preserves all those
properties while routing both notes two octaves wrong through the unchanged
roots at
`D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-235149\crates\ferrosintesis\src\sampler.rs:1807`.

A suitable negative control must perform that same-sized C1/C3 identity swap
against a temporary fixture and prove the verifier rejects it. Verification
must not rewrite tracked assets.

## Notes

Current assets were statically inspected and are structurally coherent and
unique. This requirement records prevention debt, not evidence of current
audio corruption.

Share verifier architecture with Draft requirements `MM-REQ-KILN-00164`
(Kawai) and `MM-REQ-KILN-00167` (Steinway), while retaining B1-specific
first-party source, measured-root, and terminal-tail rules.

Proposed priority: Could. Proposed flow: heavy because the acceptance oracle
must authenticate the source recordings, invoke the deterministic bake in an
isolated output tree, and compare binary audio assets without mutating the
working tree. Estimated effort: Medium.
