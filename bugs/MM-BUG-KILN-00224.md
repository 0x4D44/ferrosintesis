# MM-BUG-KILN-00224 — Core sample crate has no safe complete documented regeneration path

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** core sample crate / regeneration workflow
- **Raised:** 2026-08-16T14:46:46Z
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
- **State history:** Open (2026-08-16T14:46:46Z, raised via `deltic bugs new`)

## Observation

The core provenance recipe names only python3 tools/ferrosintesis-samples/prepare.py --only=piano,violin,flute (crates/ferrosintesis-samples-core/PROVENANCE.md:7-8). That command rewrites selected WAVs and exits after printing rows (tools/ferrosintesis-samples/prepare.py:5774-5793); it does not refresh the hand-maintained SAMPLES table, FILE_COUNT, or EXPECTED_BYTES at crates/ferrosintesis-samples-core/src/lib.rs:9-14,302. The generic generator claims every sample crate has its emitted shape (tools/ferrosintesis-samples/gen_crate_lib.py:2-9), but running it on core replaces the whole lib.rs (gen_crate_lib.py:240-243) and emits neither PIANO_SINGLE_TAKE_CELLS nor the compatibility aliases at core src/lib.rs:11-12,281-288. A source inventory change therefore offers maintainers either a stale table/pin or a silent public-API deletion. The region updater at tools/ferrosintesis-samples/regen_samples_table.py:151-206 can preserve the custom code, but core does not document it. Expected: one documented regeneration sequence refreshes the inventory and pins while preserving the custom public API and aliases. Fix by documenting and regression-testing the safe region-update sequence, and make the generic whole-file generator reject custom crates or preserve their declared extensions. Estimated effort: Small. Static review only; current committed inventory and aliases are consistent, and no app, build, test, generator, render, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
