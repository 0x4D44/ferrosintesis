# MM-REQ-KILN-00237 — FLAC decoder must have committed conformance and malformed-input oracles

- **State:** Draft
- **Priority:** Should
- **Area:** ferrosintesis-flac / decoder verification
- **Raised:** 2026-08-16T20:59:37Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T20:59:37Z, raised via `deltic reqs new`)

## Statement

Statement: The ferrosintesis-flac decoder must carry committed, re-runnable oracles for every supported decoding path and for bounded failure on malformed input. Preserve the workspace callers' indirect decode of current embedded banks, but add explicit derived coverage that cannot shrink silently; include compact CONSTANT, VERBATIM, FIXED, LPC, Rice, Rice2, escape, wasted-bit, explicit-rate, and MD5 fixtures; reject every strict prefix of representative real banks without panic; and include negative controls for huge declared lengths, CRC corruption, forbidden fields, residual limits, and predictor overflow. The current crate-local tests never successfully call decode_mono16, and the comments name a bank round-trip oracle plus an out-of-tree 3,000-prefix run that are not committed under those contracts. Leave acceptance traceability for Gate 1. Source: crates/ferrosintesis-flac/src/lib.rs:308-314 and 739-830.

## Notes
