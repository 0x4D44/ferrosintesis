# MM-REQ-KILN-00217 — Every licensed work must retain complete attribution independently

- **State:** Draft
- **Priority:** Could
- **Area:** sample assets / per-work attribution
- **Raised:** 2026-08-16T12:39:05Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T12:39:05Z, raised via `deltic reqs new`)

## Statement

Every independently licensed work in an attribution-bearing sample package must
retain its own author, work title or source, licence, and source link through the
crate notice and every consolidated parent attribution surface.

The acceptance oracle must derive the complete work set from canonical packaged
provenance or retained licence evidence. It must reject a fixture that keeps the
Rhodes credit while deleting the dulcimer credit from
`ferrosintesis-samples-ccby/NOTICE` and the parent surfaces.

## Notes

Current output is correct: both tim.kahn's Rhodes pack and iternetcone's dulcimer
pack are credited. The gap is prevention debt. `credit_tokens` and its callers at
`crates/ferrosintesis/src/licensing.rs:479-514,618-650,692-747,774-805` derive
tokens from whatever remains in one crate-wide notice and accept `any` matching
token. Deleting one work's entire block therefore shrinks the expected token set
and can stay green while that work's required attribution disappears.

Proposed effort: Small-Medium.
