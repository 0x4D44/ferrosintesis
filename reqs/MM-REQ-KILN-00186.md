# MM-REQ-KILN-00186 — Honky-tonk sample assets and zone mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** Honky-tonk sample assets / deterministic verification
- **Raised:** 2026-08-13T20:28:43Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T20:28:43Z, raised via `deltic reqs new`)

## Statement

The system must provide a non-mutating verification that authenticates or
rebuilds every honky-tonk zone from the pinned FreePats archive and bake recipe,
then compares the committed outputs per filename for exact inventory,
deterministic payload identity, strict RIFF/PCM structure and extents, declared
duration, and measured-root agreement. It must also independently prove that
all nine physical filenames map to their intended measured roots and zone
selection ranges.

## Notes

The generated checks at
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-211154\crates\ferrosintesis-samples-honkytonk\src\lib.rs:66`
prove names, count, aggregate bytes, RIFF/WAVE magic, and self-lookup while
deriving both the table and byte pin from the output directory. All nine files
are exactly 133,048 bytes. Swapping the C2 and C6 payloads therefore preserves
every crate-local assertion while the unchanged roots at
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-211154\crates\ferrosintesis\src\sampler.rs:1730`
play both zones from the wrong recordings.

Suitable negative controls must include that same-sized swap, a duplicate
payload, malformed RIFF and data extents, a changed PCM format, and a changed
source-to-root mapping. The current nine assets were statically inspected and
are structurally valid and unique; this records prevention debt, not present
corruption.

Reuse the verifier architecture requested by Draft requirements
`MM-REQ-KILN-00164`, `MM-REQ-KILN-00167`, `MM-REQ-KILN-00170`,
`MM-REQ-KILN-00183`, and `MM-REQ-KILN-00185`, while retaining this bank's
archive, substitute F2/F4 source notes, bake recipe, and measured roots. Draft
`MM-REQ-KILN-00144` covers publishing exact source hashes, not output identity
or zone mappings. Proposed priority: Could. Proposed flow: heavy. Estimated
effort: Medium.
