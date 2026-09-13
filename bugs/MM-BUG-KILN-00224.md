# MM-BUG-KILN-00224 — Core sample crate has no safe complete documented regeneration path

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** core sample crate / regeneration workflow
- **Raised:** 2026-08-16T14:46:46Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T205807Z-341dd32e
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00224-run-verify-20260913T205807Z-341dd32e
- **Owner base:** 44da704c98638a87c3b0a5b3adddfb9c28d2a07c
- **Owner fingerprint:** sha256:de29fd7a7d2c41d5f2cd35a8f3ae9f10306ef56563d5cdfc39dfa8c674609d9e
- **Owner since:** 2026-09-13T20:58:07Z
- **Owner until:** 2026-09-13T22:58:07Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T14:46:46Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:13:15Z, deltic:auto role=fix run=fix-20260913T155527Z-2efca14b branch=task/bug-MM-BUG-KILN-00224-run-fix-20260913T155527Z-2efca14b code=fcc9d1080d357ab2d8533b5381bd6f0adc52e2ed gate=manual)

## Observation

The core provenance recipe names only python3 tools/ferrosintesis-samples/prepare.py --only=piano,violin,flute (crates/ferrosintesis-samples-core/PROVENANCE.md:7-8). That command rewrites selected WAVs and exits after printing rows (tools/ferrosintesis-samples/prepare.py:5774-5793); it does not refresh the hand-maintained SAMPLES table, FILE_COUNT, or EXPECTED_BYTES at crates/ferrosintesis-samples-core/src/lib.rs:9-14,302. The generic generator claims every sample crate has its emitted shape (tools/ferrosintesis-samples/gen_crate_lib.py:2-9), but running it on core replaces the whole lib.rs (gen_crate_lib.py:240-243) and emits neither PIANO_SINGLE_TAKE_CELLS nor the compatibility aliases at core src/lib.rs:11-12,281-288. A source inventory change therefore offers maintainers either a stale table/pin or a silent public-API deletion. The region updater at tools/ferrosintesis-samples/regen_samples_table.py:151-206 can preserve the custom code, but core does not document it. Expected: one documented regeneration sequence refreshes the inventory and pins while preserving the custom public API and aliases. Fix by documenting and regression-testing the safe region-update sequence, and make the generic whole-file generator reject custom crates or preserve their declared extensions. Estimated effort: Small. Static review only; current committed inventory and aliases are consistent, and no app, build, test, generator, render, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
