# MM-REQ-KILN-00230 — Mandolin assets and runtime roots must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** mandolin sample assets / deterministic verification
- **Raised:** 2026-08-16T17:59:55Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T17:59:55Z, raised via `deltic reqs new`)

## Statement

The mandolin sample assets must be independently verifiable against the committed source cuts, deterministic bake recipe, packaged payloads, and runtime zone mappings. One authoritative manifest must bind every filename to its source identity, baked SHA-256, measured root, and ordered round-robin index, and the verification must enforce complete bounded RIFF structure, PCM16 mono 44.1 kHz format, exact duration, distinct physical payloads, and agreement with every runtime root and bank selector. Negative controls must include a same-sized cross-note payload swap, a duplicated take, malformed RIFF or data bounds, a changed PCM format, a coherent shift of all four roots in one zone, and swapped round-robin selector arms. Current static inspection found all 40 outputs structurally valid, distinct, and consistent with the current source hashes and runtime roots; this records prevention debt rather than present corruption. Proposed effort: Medium.

## Notes
