# MM-REQ-KILN-00185 — Headroom sample assets and selectors must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** Headroom sample assets / deterministic verification
- **Raised:** 2026-08-13T19:30:57Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T19:30:57Z, raised via `deltic reqs new`)

## Statement

The system must provide a non-mutating verification that authenticates or
rebuilds every Headroom zone, dynamic, and declared alias from the pinned FLAC
inputs and recipe, then compares the committed outputs per logical filename for
exact inventory, deterministic payload identity, canonical RIFF/PCM structure,
declared duration, measured-root agreement, and declared payload sharing. It
must independently assert the pp/mf/f velocity boundaries and both round-robin
selections used by `headroom_bank`.

The current generated checks at
`crates/ferrosintesis-samples-headroom/src/lib.rs:239-279` prove names, count,
aggregate bytes, RIFF/WAVE magic, and lookup while deriving the table and byte
pin from the same output directory. All 54 current files are exactly 133,048
bytes. Swapping a C2 and C6 payload therefore preserves every crate-local
assertion while the unchanged consumer roots at
`crates/ferrosintesis/src/sampler.rs:1418-1530` play both notes at the wrong
pitch. The current exercise sweep also calls only representative velocities and
does not assert the 51/52 or 95/96 boundaries.

Suitable negative controls must include a same-sized C2/C6 payload swap, a
malformed RIFF or data extent, a changed zone/source mapping, an undeclared
duplicate, and shifted velocity boundaries. Current assets were statically
checked and are structurally consistent; this records prevention debt, not
present PCM corruption.

## Notes

Share verifier architecture with Draft `MM-REQ-KILN-00164` (Kawai),
`MM-REQ-KILN-00167` (Steinway), `MM-REQ-KILN-00170` (B1), and
`MM-REQ-KILN-00183` (Salamander), while retaining Headroom's pinned FLAC set,
recipe, dynamic mapping, roots, and intentional LEVEL4 alias. Draft
`MM-REQ-KILN-00144` covers publishing source hashes, not output-to-name or
selector verification. Proposed priority: Could. Proposed flow: heavy.
Estimated effort: Medium.
