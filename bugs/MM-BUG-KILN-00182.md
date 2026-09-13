# MM-BUG-KILN-00182 — Grand regeneration silently retains obsolete packaged WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / grand output inventory
- **Raised:** 2026-08-13T17:58:21Z
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
- **State history:** Open (2026-08-13T17:58:21Z, raised via `deltic bugs new`) -> Fixed (2026-08-15T13:05:03Z, deltic:auto role=fix run=fix-20260815T120824Z-p31472-n188684700-c1 branch=task/bug-MM-BUG-KILN-00182-run-fix-20260815T120824Z-p31472-n188684700-c1 code=291ab66 gate=manual) -> Closed (2026-09-13T21:00:07Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: restoring the hand-written family list fails the per-family preflight sweep; its Rust source-scan oracle is red from KILN-00207, split to MM-BUG-CRU-00065)

## Observation

Source-level reproduction: leave or introduce a valid extra grand_*.wav under crates/ferrosintesis-samples-grand/samples, then follow the documented --only=grand regeneration path. GRAND_SOURCES names the owned output set, but main pre-validates only Steinway, Kawai, Headroom, and the bass pair before the generic write loop. The grand path never calls the scoped output-inventory validator, so the obsolete file remains. Cargo packages samples/**, and the inventory generator enumerates every remaining WAV; a later refresh can therefore embed the stale file and make the generated table self-consistent with the wrong directory. Expected: grand regeneration rejects unexpected owned outputs before any fetch or write. Actual: it rewrites current names and silently retains obsolete ones. Add a grand-scoped validator call before source use plus negative controls for a stale file and a renamed source. Also strengthen the source-derived oracle so main is checked per family and expected set, rather than accepting any earlier validator call. Current committed inventory is clean; this is a source-confirmed regeneration defect. Static review only; no generator was run.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `291ab66f`; loop later reshaped by `2c65490f`) by an agent other than the fixer.

**Original observation re-run.** Driving `main()` per family proves selecting `grand` (and every other source-backed family) validates its outputs before any fetch or write.

**Fails-before (method B).** Restoring the old steinwayb/kawai/headroom/bass hand list fails the per-family sweep, e.g. "(family='bassoon') wrote bassoon_A#0_f.wav before validating the output set". Restored; `SelectedFamilyPreflightTest` passes on HEAD.

**Gate note.** The Rust half of this fix, `inventory::tests::every_generated_bake_output_family_is_inventory_validated`, is red on trunk because it pins the literal loop text that `2c65490f` (KILN-00207) correctly regrouped. Restoring the old loop turns it green. Tracked as MM-BUG-CRU-00065; this fix's behaviour is intact.

## Notes
