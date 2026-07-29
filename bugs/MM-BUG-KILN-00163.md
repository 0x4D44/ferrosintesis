# MM-BUG-KILN-00163 — Kawai rebakes can retain stale WAVs behind an unrelated family validation

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample generation / output inventory
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T223542Z-p16556-n556412300-c1 branch=task/bug-MM-BUG-KILN-00163-run-fix-20260728T223542Z-p16556-n556412300-c1 code=4c68345 gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green)

## Observation

Static reproduction: D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:727 defines KAWAI_SOURCES, but main validates only the headroom family at :5324 before the generic writer includes KAWAI_SOURCES at :5526 and writes selected files at :5571. Removing or renaming a Kawai source entry therefore leaves its old packaged WAV untouched; D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\gen_crate_lib.py:30 scans the remaining directory and re-embeds that obsolete file. The class oracle at D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\inventory.rs:171 models validation as one unscoped boolean, so Headroom's conditional, family-specific check marks main validated for every later family. Current Kawai inventory is internally consistent; the confirmed failure is that retiring a source or zone can appear successful while the obsolete timbre is republished. Expected: every selected generated family rejects on-disk WAVs outside its current expected set before writing. Actual: Kawai performs no family-scoped validation. Concrete fix: validate (kawai, KAWAI_SOURCES) before any selected Kawai write, strengthen the source-derived oracle to associate each validation with its family and expected set, and add a removed-Kawai-entry/stale-file negative control. This is a residual of closed MM-BUG-KILN-00145 and MM-BUG-KILN-00156, not their original name-enumeration defect.

## Fix

Code commit `4c68345`. `prepare.main()` now calls
`_validate_generated_output_inventory("kawai", KAWAI_SOURCES)` before any Kawai
fetch or write, and the Rust oracle in `crates/ferrosintesis/src/inventory.rs`
was rewritten to require the exact (family, expected-set) pair rather than one
unscoped validated boolean.

## Notes

### Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Confirmed the guard runs before any side effect, and that the oracle's
unscoped-boolean defect is closed: `has_scoped_validation_before_source_use`
requires the literal `_validate_generated_output_inventory("kawai",
KAWAI_SOURCES)` to appear before the first other use of that table, backed by
self-tests for an unrelated-family validation and a wrong expected set.

Fails-before proven twice. Deleting only the two added `prepare.py` lines:
`KawaiOutputInventoryTest` fails with `inventory must be checked before reading`
(its `read_wav` tripwire fires, so the stale file is reached before validation),
and `every_generated_bake_output_family_is_inventory_validated` fails with
`main must validate the Kawai output against KAWAI_SOURCES before using that
table`. Both pass on the restored tree.

The Python control is a real end-to-end negative: it removes a source entry,
plants the retired WAV in a temp repo root, and asserts `main()` raises naming
that file with `ensure_direct_sources` and `write_wav_mono` never called.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
