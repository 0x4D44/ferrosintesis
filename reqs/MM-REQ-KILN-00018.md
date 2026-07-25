# MM-REQ-KILN-00018 — Keep committed listening assets current with the integrated synth

- **State:** Retired
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
- **State history:** Draft (2026-07-12) → Retired (2026-07-25, premise removed — see below)

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

## Retired (2026-07-25) — both clauses' premises were removed by a later decision

This requirement was never accepted, and the repository has since gone the other
way on both of its clauses. Verified on trunk today:

1. **"must commit the bytes"** — there are no committed album renders to keep
   current. `.gitignore:46` drops `*.opus`, and `git ls-files '*.opus'` returns
   7 files, every one of them a first-party instrument recording under
   `samples/` (source, not output); `git ls-files listening` returns only
   `listening/README.md`. The `.opus` renders were purged after re-rendered
   copies bloated `.git` past 5.9 GB, and are now produced on demand by
   `cargo run --release -p render-catalog`. "Stale committed listening output"
   is no longer a state the repository can be in.

2. **"must not add listening copies for albums designated MIDI-only"** — that
   designation was abandoned with the same decision. `crates/render-catalog/src/main.rs`
   now renders The Long Turning (:162), VIGIL (:187) and RIVERWAKE (:193), the
   three albums the 2026-07-09..11 HLDs called MIDI-only. Nothing in the code
   carries the distinction any more; with renders ephemeral, an extra one costs
   nothing permanent.

The underlying concern — "does a synth change reach exactly the albums it
should?" — survives, but as the render-diff inventory that `CLAUDE.md` mandates
for every `voices.rs`/`engine.rs`/`drums.rs`/`sampler.rs` change, not as a
committed-asset obligation.

Superseded, not dropped: no work is owed.
