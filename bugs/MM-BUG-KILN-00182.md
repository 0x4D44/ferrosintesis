# MM-BUG-KILN-00182 — Grand regeneration silently retains obsolete packaged WAVs

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / grand output inventory
- **Raised:** 2026-08-13T17:58:21Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T204248Z-bf2dbb12
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00182-run-verify-20260913T204248Z-bf2dbb12
- **Owner base:** 5c82da9a12b7e426cf76cbc3cadb9185c9a4c1bc
- **Owner fingerprint:** sha256:fcd46869059c7014692bd4ee498c54fe15e2cd3bd148b5d05d9598adce7b41cd
- **Owner since:** 2026-09-13T20:42:48Z
- **Owner until:** 2026-09-13T22:42:48Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-13T17:58:21Z, raised via `deltic bugs new`) -> Fixed (2026-08-15T13:05:03Z, deltic:auto role=fix run=fix-20260815T120824Z-p31472-n188684700-c1 branch=task/bug-MM-BUG-KILN-00182-run-fix-20260815T120824Z-p31472-n188684700-c1 code=291ab66 gate=manual)

## Observation

Source-level reproduction: leave or introduce a valid extra grand_*.wav under crates/ferrosintesis-samples-grand/samples, then follow the documented --only=grand regeneration path. GRAND_SOURCES names the owned output set, but main pre-validates only Steinway, Kawai, Headroom, and the bass pair before the generic write loop. The grand path never calls the scoped output-inventory validator, so the obsolete file remains. Cargo packages samples/**, and the inventory generator enumerates every remaining WAV; a later refresh can therefore embed the stale file and make the generated table self-consistent with the wrong directory. Expected: grand regeneration rejects unexpected owned outputs before any fetch or write. Actual: it rewrites current names and silently retains obsolete ones. Add a grand-scoped validator call before source use plus negative controls for a stale file and a renamed source. Also strengthen the source-derived oracle so main is checked per family and expected set, rather than accepting any earlier validator call. Current committed inventory is clean; this is a source-confirmed regeneration defect. Static review only; no generator was run.

## Fix

<unfixed — raised only>

## Notes
