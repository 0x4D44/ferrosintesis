# MM-REQ-KILN-00194 — Orchestral2 sample assets and zone mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** orchestral2 sample assets / deterministic verification
- **Raised:** 2026-08-13T22:54:47Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T22:54:47Z, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The system must provide a non-mutating verifier that binds every orchestral2
sample filename to its exact source identity, deterministic recipe output,
consumer zone, and measured root. It must compare the committed bank per file
for exact inventory and payload identity, strict bounded RIFF/PCM structure,
mono 44.1 kHz 16-bit format, nonempty data, duration, source-to-output mapping,
and agreement with the root and dynamic-layer declarations in
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis\src\sampler.rs`.

The verifier must authenticate pinned external inputs and first-party inputs
without rewriting tracked assets. For banjo it must first establish one
canonical reproducible input: either retain and hash the original lossless take,
or rebake and pin the current Opus archive as the source of record. Negative
controls must include a same-sized payload swap between filenames, a valid WAV
replacement with the wrong source, a malformed chunk extent, stereo/48 kHz or
non-16-bit PCM, a wrong measured root, a missing/extra family member, and a
consumer root or dynamic-layer mismatch.

## Notes

Current static inspection found all 132 outputs unique, structurally valid,
tracked, embedded, and referenced by the sampler. This requirement records
prevention debt, not evidence of current audio corruption.

The crate-local tests at
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\src\lib.rs:397` derive filename
parity from the output directory and check only RIFF/WAVE magic. A correctly
shaped payload swap or source substitution therefore stays green. Draft
requirements `MM-REQ-KILN-00164`, `MM-REQ-KILN-00167`, `MM-REQ-KILN-00170`,
`MM-REQ-KILN-00183`, `MM-REQ-KILN-00185`, `MM-REQ-KILN-00186`,
`MM-REQ-KILN-00188`, and `MM-REQ-KILN-00189` provide the same verifier pattern
for sibling banks; share infrastructure while retaining orchestral2's fourteen
families and banjo-specific source rule.

Proposed priority: Could. Proposed flow: heavy. Estimated effort: Medium.
