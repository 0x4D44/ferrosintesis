# MM-BUG-KILN-00207 — Selective bass rebakes no longer validate the complete shared crate

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** electric-bass sample generation / shared-crate inventory
- **Raised:** 2026-08-16T09:39:30Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T205525Z-47203da9
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00207-run-verify-20260913T205525Z-47203da9
- **Owner base:** 57e3b1ae456e6b0ae4a683651db8f949fbd66c04
- **Owner fingerprint:** sha256:b523ba6ab2f1554bf6b1e494aa28b99b5685b7382ac296d9034a27fc1c8f1c89
- **Owner since:** 2026-09-13T20:55:25Z
- **Owner until:** 2026-09-13T22:55:25Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T09:39:30Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T04:51:49Z, deltic:auto role=fix run=fix-20260913T044356Z-c69e05a7 branch=task/bug-MM-BUG-KILN-00207-run-fix-20260913T044356Z-c69e05a7 code=2c65490ffa7114931842ecd19b06b765c9de0491 gate=manual)

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
