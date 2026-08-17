# MM-BUG-KILN-00267 — B1 crate Rustdoc lost its ferrosintesis object after the legal-header split

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** B1 sample crate / published documentation
- **Raised:** 2026-08-17T05:30:56Z
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
- **State history:** Open (2026-08-17T05:30:56Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The published crate-level Rustdoc is grammatically incomplete at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-061026\crates\ferrosintesis-samples-b1-upright\src\lib.rs:5`. Line 5 ends with “Consumers normally reach this crate through”, but line 6 now begins the independent sentence “Licence/provenance: see ...”, so the first sentence has no object.

Commit `02fd273` fixed `MM-BUG-KILN-00197` by making the reusable legal pointer a standalone sentence and removing its leading `` `ferrosintesis`. `` fragment. The B1 crate's bespoke preceding prose still depended on that removed continuation, so the fix created this distinct residual in public docs. The shared header oracle checks the legal line itself and does not catch the broken sentence before it.

Expected: the published crate description names how consumers reach the package and reads as complete prose. Actual: rendered Rustdoc says “Consumers normally reach this crate through Licence/provenance: see ...”.

Concrete fix: complete line 5 as “Consumers normally reach this crate through `ferrosintesis`.” and leave the generated legal pointer as its own sentence. Add a negative/header-context check if needed so another reusable-line edit cannot strand bespoke preceding prose. Static review only; no rustdoc build ran. Estimated effort: Trivial.

## Fix

<unfixed — raised only>

## Notes
