# MM-REQ-KILN-00018 — Keep committed listening assets current with the integrated synth

- **State:** Draft
- **Priority:** Should
- **Area:** listening catalog / rendering
- **Raised:** 2026-07-12
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-12)

## Statement

Every album intended to ship Opus listening copies must commit the bytes produced
from its committed MIDI by the current integrated ferrosintesis renderer. Catalog
refreshes must remain diff-driven and must not add listening copies for albums that
the repository designates MIDI-only.

## Notes

Promoted from `scratchpad.md` after a 2026-07-12 review reconfirmed broad stale
listening output. The existing
`task/20260711-TSK-CDX-render-all-listening-opus` attempt differs from current
trunk in 52 listening files, is 20 commits behind, and includes new Opus files for
MIDI-only albums. Treat that branch as evidence and salvage material, not as an
integration-ready result. Gate 1 should define a current-trunk render-diff oracle
and the exact catalog inclusion policy before accepting this heavy requirement.
