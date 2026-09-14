# MM-BUG-CRU-00067 — gen_crate_lib.py silently deletes the drum-kit crate's hand-written bank API

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / crate lib generator
- **Raised:** 2026-09-13T19:23:49Z
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
- **State history:** Open (2026-09-13T19:23:49Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:31:50Z, deltic:auto role=fix run=fix-20260913T212218Z-6db24862 branch=task/bug-MM-BUG-CRU-00067-run-fix-20260913T212218Z-6db24862 code=d5e8573225b757402d273ff610b6ad7c2b09bbc7 gate=manual) -> Closed (2026-09-14T23:40:41Z, independent verify by Claude Opus 5 on trunk 56ba5184: gen_crate_lib.py now refuses whole-file generation over the drum-kit crate and leaves lib.rs byte-identical; restoring the old token check fails the regression test; attribute-prefixed and non-pub hand-written items still slip past, split to MM-BUG-CRU-00079)

## Observation

Residual split at independent verification of MM-BUG-KILN-00224 (2026-09-13, trunk 8b6a6f86). The record asked that the generic generator reject custom crates. Fix fcc9d108 refuses only the core crate, keyed on the single core-only token PIANO_SINGLE_TAKE_CELLS. Running tools/ferrosintesis-samples/gen_crate_lib.py on a TEMP copy of crates/ferrosintesis-samples-drumkit exits 0 and rewrites lib.rs without its hand-written BANKS, pcm, prewarm and related API (4 matching items became 0). The drumkit docs name neither tool, so nothing warns a regenerator. Expected: the generator refuses any crate whose lib.rs carries API it does not generate, derived rather than keyed on one token.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `56ba5184` (fix `d5e85732`, single parent) by the lead, an agent other than the fixer. An earlier verifier worker in this pass reached the same result; the evidence below is the lead's own.

**Original observation, re-run.** `python3 gen_crate_lib.py <scratch copy of crates/ferrosintesis-samples-drumkit>` exits 1: 'refusing whole-file generation: it declares non-generated public items: BANKS, Bank, BankSource, HH_CLOSED, ...'. The copy's `src/lib.rs` is byte-identical afterwards (sha256 `8158777a...` before and after). Before the fix the generator rewrote the whole file and erased that API.

**Root cause check.** The refusal is now derived from the file's own public items plus the managed-region markers (`custom_inventory_reason`), instead of one crate-specific token. The verifier worker's census of all 24 sample crates found all six custom crates refused (b1-upright, bottle, core, drumkit, drumkit2, fretnoise) and the 18 generated ones accepted.

**Fails-before (method B).** `test_prepare.CoreInventoryRegenerationTest.test_generic_generator_refuses_a_drumkit_shaped_custom_api` passes. Replacing the call with the old check (`if "PIANO_SINGLE_TAKE_CELLS" in existing:`) fails it: 'AssertionError: SystemExit not raised'. Restored; worktree clean.

**Residual split to MM-BUG-CRU-00079.** `custom_inventory_reason` recognises only items that begin a line with `pub`. It returns `None`, so whole-file generation would proceed and erase the item, for `#[inline] pub fn fast() {}`, for `#[macro_export] macro_rules! sample { ... }`, and for a hand-written `#[cfg(test)] mod tests { ... }`. A plain `pub fn` at line start is refused. No committed crate has any of these today.

**Repo gate.** On `56ba5184` the Python gate step passes ('Ran 284 tests ... OK'). The fix touches only `tools/`, which the cargo steps do not build; those were fully run on `1d87b00f` and `011738f6` earlier in this pass.

## Notes
