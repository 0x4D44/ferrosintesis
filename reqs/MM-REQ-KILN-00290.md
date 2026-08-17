# MM-REQ-KILN-00290 — Orchestral sample assets and runtime mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** orchestral sample assets / deterministic verification
- **Raised:** 2026-08-17T13:41:11Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-17T13:41:11Z, raised via `deltic reqs new`)

## Statement

The system must independently verify every packaged orchestral sample from its
pinned source and deterministic bake through the final FLAC payload and runtime
zone mapping. The oracle must bind each of the 158 filenames to source identity,
payload identity, decoded mono/16-bit/44.1 kHz structure, measured root, dynamic
layer, round-robin role, and consuming sampler route. It must model intentional
source sharing, including the pinned single-take `horn_D4` p/f pair, rather than
requiring blanket byte uniqueness.

Negative controls must include a cross-note payload swap, a valid foreign FLAC
under an expected name, a duplicate that is not declared sharing, malformed or
truncated FLAC metadata/frame data, a changed runtime root or velocity selector,
a missing or extra family member, and a regeneration selector that leaves the
active final-format bank unchanged.

## Notes

Current static inspection found 158 disk files, 158 generated entries, and 158
consumer references; all STREAMINFO blocks declare mono 16-bit 44.1 kHz with
nonzero frame counts. Those facts establish internal inventory consistency, not
source or semantic identity. The crate-local tests at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\src\lib.rs:627`
derive names and aggregate bytes from the output directory and compare `get()`
with the same generated table, so a valid-but-wrong payload can pass.

Draft `MM-REQ-KILN-00144` covers packaged source pins and Draft
`MM-REQ-KILN-00237` covers the shared FLAC decoder. Neither binds this package's
filename-to-payload-to-runtime-root contract. Proposed priority: Could. Proposed
flow: heavy. Estimated effort: Medium.
