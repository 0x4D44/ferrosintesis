# MM-BUG-KILN-00136 — Grand source comments retain obsolete VSCO routing

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / GM0 piano routing documentation
- **Raised:** 2026-07-26
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260726T134703Z-p37944-n509596200-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00136-run-fix-20260726T134703Z-p37944-n509596200-c1
- **Owner base:** be1337d3359ae20d9489129701c2b8dc6ce0985f
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T13:47:03Z
- **Owner until:** 2026-07-26T15:47:03Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`)

## Observation

Two source comments that define the Salamander grand's identity still say it is
distinct from the VSCO upright "that voices GM 1/3":

- `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:653`
- `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis\src\sampler.rs:958`

The current routing source says otherwise. `GM0_SOURCES` places the VSCO upright
at GM0 CC0=1 at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis\src\voices.rs:1403`.
The current consumer comments and routing give GM1 and GM3 their own Kawai and
honky-tonk defaults.

Expected: source comments identify Salamander as the GM0 CC0=2 alternate and
describe its current contrast without assigning the VSCO recording to obsolete
programs.

Actual: the two comments preserve the pre-revoicing claim, while the assigned
crate's manifest, module docs, README, and provenance record correctly identify
the current CC0=2 slot.

The stale comments are actionable because they sit beside the source-selection
and consumer bank definitions maintainers edit during piano revoicing. Following
them would direct a future calibration or routing change at the wrong programs.

## Fix

Rewrite both comments to describe the current mapping: B1 upright is GM0's
default, VSCO upright is GM0 CC0=1, and Salamander is GM0 CC0=2. Prefer naming
only the relationship each block needs so another unrelated piano revoicing
does not stale it again.

Extend the existing derived GM0 documentation oracle, or add a focused
source-text regression, so the grand generator and sampler identity blocks
cannot reintroduce the obsolete VSCO GM1/GM3 claim.

Estimated effort: Small.

## Notes

This is not a duplicate of closed `MM-BUG-KILN-00122`. That defect and its
derived oracle cover packaged asset-crate selector documents. These adjacent
generator and consumer comments remain outside that oracle and are wrong on the
current routing table.

No application, generator, build, test, render, or exploratory harness ran.
