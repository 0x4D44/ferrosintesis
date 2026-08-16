# MM-BUG-KILN-00207 — Selective bass rebakes no longer validate the complete shared crate

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** electric-bass sample generation / shared-crate inventory
- **Raised:** 2026-08-16T09:39:30Z
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
- **State history:** Open (2026-08-16T09:39:30Z, raised via `deltic bugs new`)

## Observation

`fingerbass` and `pickbass` both publish into
`crates/ferrosintesis-samples-bass/samples/`
(`tools/ferrosintesis-samples/prepare.py:1196-1197`). However, the derived
preflight at `prepare.py:5532-5534` validates only the selected filename family.
The generic write loop at `prepare.py:5733-5745` likewise leaves the unselected
family untouched.

Therefore `--only=fingerbass` accepts the crate while an obsolete
`pickbass_*.wav` remains, and the symmetric `--only=pickbass` case accepts a stale
finger file. A later `tools/ferrosintesis-samples/gen_crate_lib.py:97-102` run
enumerates every WAV in the shared directory and embeds the stale payload.

Expected: selecting either owner of a shared sample crate validates the complete
package inventory before any fetch or write. Actual: validation stops at the
selected prefix even though publication scans the package directory.

This regresses closed `MM-BUG-CRUCIBLE-00022`. Commit `b9114c8` added the combined
bass guard; commit `291ab66` replaced it with per-family derived checks and lost
the shared-directory invariant. The current committed inventory is clean; the
defect is the live false-negative on a later removal or rename.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

## Notes

Derive validation by destination package, not only by filename prefix. Selecting
either bass family must check the union of `FINGERBASS_SOURCES` and
`PICKBASS_SOURCES`. Add negative controls for a finger-only selection with a stale
pick file and the symmetric pick-only case. Estimated effort: Small–Medium.

Static review only. No generator, app, build, test, render, package, or exploratory
harness ran.
