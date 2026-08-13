# MM-BUG-KILN-00191 — Orchestral2 regeneration silently retains obsolete packaged WAVs

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / orchestral2 output inventory
- **Raised:** 2026-08-13T22:54:22Z
- **Discovery source:** Agent
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-13T22:54:22Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Source-level reproduction: leave or introduce an extra valid `harp_*.wav` under
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\samples\`, then follow the packaged
`prepare.py --only=harp` regeneration route. The source maps define the owned
output set, but `main()` pre-validates only Steinway, Kawai, Headroom, and the
bass pair at `D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\tools\ferrosintesis-samples\prepare.py:5421`. The generic
orchestral2 families are fetched at lines 5457-5495 and written at lines
5629-5674 without a scoped inventory check, so the extra file remains.

`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\Cargo.toml:10` packages `samples/**`.
A later inventory-table refresh can therefore embed the obsolete WAV and make
the generated table self-consistent with the wrong directory. The same failure
applies to every non-banjo orchestral2 family written through the generic loop:
harp, ocarina, recorder, timpani, viola, marimba, xylo, glock, vibes, tubular,
musicbox, eastpick, and eastpluck.

Expected: each selected family rejects unexpected owned outputs before any
source fetch or write. Actual: the bake overwrites current names and silently
retains obsolete packaged files. Fix by validating each selected family against
its source-derived expected set before source use. Strengthen the source scanner
in `D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis\src\inventory.rs` so an unrelated validator cannot make
the multi-family `main()` writer pass. Add stale-file and renamed-source negative
controls. Current committed inventory is clean; this is a source-confirmed
regeneration defect. Static review only; no generator was run.

## Fix

<unfixed — raised only>

## Notes

Sibling Open bug `MM-BUG-KILN-00182` records the same defect class in the grand
route. This record keeps the thirteen orchestral2 routes in scope so a narrow
grand-only fix cannot leave them behind.
