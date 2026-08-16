# MM-REQ-KILN-00211 — Electric-bass sample assets and zone mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** electric-bass sample assets / deterministic verification
- **Raised:** 2026-08-16T09:39:56Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T09:39:56Z, raised via `deltic reqs new`)

## Statement

The electric-bass sample assets must be independently verifiable against their two
pinned FreePats archives, bake recipe, and runtime zone mappings. A non-mutating
oracle must bind each packaged filename to its source archive member and baked
payload identity, validate complete bounded RIFF/PCM16 mono 44.1 kHz structure and
extents, and prove that every measured root agrees with the corresponding
`finger_bass` or `pick_bass` runtime zone.

The oracle must reject at least a same-sized cross-note payload swap, a duplicate
payload, malformed RIFF/data extents, a changed PCM format, a changed source-member
mapping, and a stale or transposed runtime root. It must not derive both sides of a
comparison from the output directory it is checking.

## Notes

All 13 current WAVs are structurally valid, unique, 80,128 bytes each, and agree
with the current filename inventory. This records prevention debt, not present
corruption.

`crates/ferrosintesis-samples-bass/src/lib.rs:82-115` checks names, count, one
aggregate byte total, RIFF/WAVE magic, and self-lookup. Because every file has the
same length, swapping two valid payloads preserves every assertion.
`crates/ferrosintesis/src/sampler.rs:935-975` then supplies hand-copied root literals
that no current oracle re-measures against those payloads.

Draft `MM-REQ-KILN-00144` covers exact published upstream source pins, not output
identity or runtime-root binding. Sibling-bank requirements establish the same
verifier shape but do not cover this crate. Proposed effort: Medium; Flow remains
heavy because source authentication and pitch measurement must stay independent of
the committed outputs.
