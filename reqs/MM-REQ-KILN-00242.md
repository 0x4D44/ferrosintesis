# MM-REQ-KILN-00242 — Gong assets and runtime layers must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** gong sample assets / deterministic verification
- **Raised:** 2026-08-16T21:55:10Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T21:55:10Z, raised via `deltic reqs new`)

## Statement

The gong sample bank must be independently verifiable from its two committed Freesound source WAVs through the deterministic bake and FLAC conversion to the exact packaged soft/loud payloads and runtime layer mapping. A non-mutating oracle must bind each packaged .flac filename to source ID and output identity, decode and validate complete mono 16-bit 44.1 kHz content and duration, prove soft and loud are distinct and routed on the documented velocity boundary, and cover initial-step continuity after conversion. Negative controls must include an equal-aggregate soft/loud payload swap, duplicate payload, malformed or truncated FLAC with valid magic, changed source mapping, stale runtime lookup key, and a converted bank omitted from the onset sweep. Current static inspection found the two names, aggregate size, runtime lookups, and boundary internally consistent; current corruption was not established. The crate-local checks at crates/ferrosintesis-samples-gong/src/lib.rs:43-89 prove only directory-name parity, aggregate byte count, container magic, and self-table lookup. Draft MM-REQ-KILN-00237 covers FLAC decoder conformance, not identity of this bank or its layer mapping. Proposed effort: Medium.

## Notes
