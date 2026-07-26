# MM-BUG-KILN-00136 — Grand source comments retain obsolete VSCO routing

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / GM0 piano routing documentation
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T134703Z-p37944-n509596200-c1 branch=task/bug-MM-BUG-KILN-00136-run-fix-20260726T134703Z-p37944-n509596200-c1 code=66c1cd950239579978767b57c97cb8ca80847b73 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, and both test suites - 1486 tests, 0 failures; the sample-tool Python suite passes 69. Original observation re-run at source, against the routing table rather than against the fix's own say-so. Both comment sites the bug named now describe the current slots: `tools/ferrosintesis-samples/prepare.py` reads "Salamander is GM 0 CC0=2. The VSCO upright is GM 0 CC0=1", and `crates/ferrosintesis/src/sampler.rs` adds "B1 upright is GM 0 CC0=0 default". I checked those against ground truth instead of taking them on trust: `GM0_SOURCES` (`voices.rs:1394`) puts Arthur's B1 upright at slot 0 as of the 2026-07-26 promotion with the previous line-up shifted down one, which puts the VSCO upright at 1 and Salamander at 2 - so the comments now match the router. The stale "voices GM 1/3" claim is gone from both blocks. One apparent survivor is not one: `sampler.rs:1068` still contains the string "GM 1/3", but in the different and correct statement that GM 1 and GM 3 have their own defaults (`kawai_bank`, honky-tonk), which is true. THE GUARD IS THE BEST OF ITS CLASS I HAVE SEEN IN THIS LEDGER and is worth copying elsewhere. `every_gm0_crate_documents_the_slot_the_router_gives_it` (`crates/ferrosintesis/src/altbank.rs:1333`) does three things right at once: it DERIVES each expected slot number by looking the bank up in the live `GM0_SOURCES` table (`slot("B1 upright")` etc., panicking if a name is absent), it builds every expectation with `format!("… is GM 0 CC0={n}")` rather than hardcoding a number, and it SCOPES each search to the identity block - splitting `prepare.py` on its Salamander header up to `SALAMANDER_ARCHIVE_URL`, and `sampler.rs` up to `fn grand_pp` - so a match in unrelated prose cannot satisfy it. That block scoping is precisely the remedy MM-BUG-KILN-00142 asks for elsewhere, already implemented here. It also carries the negative clause banning the stale phrase. I proved it non-vacuous by mutation: changing the sampler comment to claim the VSCO upright sits at CC0=3 turned it red on the exact derived assertion (`assertion failed: sampler_grand.contains(&format!("VSCO upright is GM 0 CC0={vsco}"))`), and it passes again once restored. `git status --porcelain` clean.)

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
