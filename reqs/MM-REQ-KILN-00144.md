# MM-REQ-KILN-00144 — Published sample provenance must carry exact source pins

- **State:** Draft
- **Priority:** Could
- **Area:** sample assets / published provenance
- **Raised:** 2026-07-26
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-26, raised via `deltic reqs new`)

## Statement

The system must package every exact SHA-256 source pin that a published sample bank relies on, and machine-check that the packaged provenance agrees with the generator's source pin.

## Notes

The honky-tonk package ships
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\crates\ferrosintesis-samples-honkytonk\PROVENANCE.md:25`,
which says only that the archive SHA-256 is pinned in `prepare.py`. The actual
digest, `da35c93967c421b17f7219c12a37830ffd2b19f54f8a0a71203fc6161b079b45`,
lives at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\tools\ferrosintesis-samples\prepare.py:868`,
outside the published crate.

An additive census found the same packaged-provenance gap in five of the 25
sample crates:

- `ferrosintesis-samples-headroom`
- `ferrosintesis-samples-honkytonk`
- `ferrosintesis-samples-musescore-grand`
- `ferrosintesis-samples-orchestral`
- `ferrosintesis-samples-ydp-grand`

This matches the design rationale at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\crates\ferrosintesis\src\inventory.rs:363`:
a pin kept only in the generator does not travel with a published crate. The
current oracle proves that `PROVENANCE.md` is packaged, but not that it contains
the immutable source identity.

A suitable Gate-1 oracle would derive every hash-pinned source bank from
`prepare.py`, require the corresponding packaged `PROVENANCE.md` to contain the
exact digest, and include an adversarial fixture where the prose merely says
“SHA-256 pinned in prepare.py.”

Proposed priority: Could. Proposed flow: light. Estimated effort: Small.
