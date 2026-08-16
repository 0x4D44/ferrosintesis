# MM-REQ-KILN-00225 — Core sample assets and runtime roots must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** core sample assets / deterministic verification
- **Raised:** 2026-08-16T14:46:59Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T14:46:59Z, raised via `deltic reqs new`)

## Statement

The core piano, violin, and flute assets must be independently verifiable against the pinned VSCO revision, the bake recipe, and every runtime zone/root mapping. A non-mutating oracle must bind all 69 packaged filenames to payload identity and measured root, validate exact bounded RIFF structure and PCM16 mono 44.1 kHz format, and prove the two declared single-take aliases resolve to the intended canonical payloads. It must not derive both expected and actual values from the output directory. Negative controls must include an equal-sized cross-note payload swap, duplicate payload, malformed RIFF chunk extent or padding, changed PCM format, missing or extra family member, changed source mapping, changed regeneration selector, stale runtime root, and an undeclared alias. Current static inspection found 69 structurally valid, byte-distinct physical WAVs and matching filename tables; this requirement records prevention debt, not current asset corruption. The crate-local checks at crates/ferrosintesis-samples-core/src/lib.rs:304-347 cover names, aggregate size, RIFF/WAVE magic, lookup, and the two aliases, while crates/ferrosintesis/src/sampler.rs keeps independently maintained roots. Sibling-bank requirements do not cover this core VSCO bank. Proposed priority: Could. Proposed flow: heavy because the oracle must authenticate or rebuild pinned upstream inputs without mutating tracked assets. Estimated effort: Medium.

## Notes
