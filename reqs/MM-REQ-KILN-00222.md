# MM-REQ-KILN-00222 — Clavinet assets and runtime roots must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** clavinet sample assets / deterministic verification
- **Raised:** 2026-08-16T13:45:18Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T13:45:18Z, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The eleven packaged clavinet WAVs must be independently verifiable against the pinned MS Basic SF3, the clavinet bake recipe, and the runtime zone map. A non-mutating oracle must bind every packaged filename to its payload identity and measured root, validate complete RIFF and PCM16 mono 44.1 kHz structure and extents, and prove every filename-to-root mapping consumed by ferrosintesis. Negative controls must include an equal-sized cross-note payload swap, duplicate payload, malformed RIFF or data extent, changed PCM format, changed SF3 preset or source-root set, changed regeneration selector, and changed runtime root mapping.

Current crate-local checks at crates/ferrosintesis-samples-clavinet/src/lib.rs:78-120 establish name parity, aggregate size, RIFF/WAVE magic, and lookup self-consistency. All eleven current files are structurally valid and distinct, and current runtime names agree; this requirement prevents future silent audio drift rather than alleging current corruption. Draft MM-REQ-KILN-00189 explicitly covers the separate 36-file ferrosintesis-samples-musescore crate and does not cover these eleven Clavinet zones.

## Notes
