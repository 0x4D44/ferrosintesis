# MM-REQ-KILN-00249 — Headroom regeneration must publish the bank failure-atomically

- **State:** Draft
- **Priority:** Could
- **Area:** Headroom sample bank / failure-atomic regeneration
- **Raised:** 2026-08-17T00:04:40Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-17T00:04:40Z, raised via `deltic reqs new`)

## Statement

The Headroom regeneration workflow must publish its complete 45-file final-format
bank as one failure-atomic unit. It must build the FLAC payloads and nine-name alias
contract in empty staging, validate the exact inventory and payload/container
properties there, and either replace the complete prior bank or leave that prior
bank byte-for-byte unchanged.

The acceptance oracle must inject failures before the first transform, in the
middle and at the last transform, and during publication. Every failure must leave
the prior packaged bank unchanged with no `.wav`, `.part`, or mixed-generation
debris. A successful run must leave exactly 45 canonical FLAC files, nine valid
logical aliases, and a generated Rust inventory that names precisely that set.

## Notes

This is prevention debt, not a claim that the current runtime FLAC bank is mixed.
Open `MM-BUG-KILN-00248` separately covers the current wrong-format regeneration
path. Draft `MM-REQ-KILN-00185` covers independent payload/root/selector
verification; it does not require failure-atomic publication.
