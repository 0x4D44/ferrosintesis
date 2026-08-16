# MM-REQ-KILN-00231 — Rain loop asset must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** rain sample asset / deterministic verification
- **Raised:** 2026-08-16T20:03:47Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T20:03:47Z, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The rain loop asset must be independently verifiable against a declared canonical source and its runtime contract. The verification must bind rain_loop.wav to an exact output SHA-256, enforce complete bounded RIFF structure and PCM16 mono 44.1 kHz format, prove the 4.6-second payload and exact runtime lookup, and exercise the wrapped cubic seam at supported non-integer output rates. Provenance must either provide an exact reproducible bake with source identity, frame window, crossfade curve, normalization target, and tool versions, or state that the committed WAV is the canonical non-rebuildable artifact. Negative controls must include a same-sized payload substitution, malformed or out-of-bounds RIFF chunks, changed PCM format, and equal endpoints with a discontinuous wrapped slope. Current static inspection found the committed WAV structurally valid and its current wrapped interpolation bounded; this records prevention debt, not current corruption. Proposed effort: Medium.

## Notes
