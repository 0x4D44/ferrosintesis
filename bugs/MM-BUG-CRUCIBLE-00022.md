# MM-BUG-CRUCIBLE-00022 — Bass rebakes retain obsolete packaged WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** electric-bass sample generation / output inventory
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`) -> Fixed (2026-08-01T07:26:11Z, deltic:auto role=fix run=fix-20260801T071307Z-p76832-n922353200-c1 branch=task/bug-MM-BUG-CRUCIBLE-00022-run-fix-20260801T071307Z-p76832-n922353200-c1 code=b9114c83033f3ba77d8a5b99d7a5fd37ccc1f9e8 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 65220c3; fixer was OpenAI GPT-5 Codex)

## Observation

`main()` validates generated output inventory only for Steinway, Kawai, and Headroom at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:5369`.
The generic writer enumerates only current `FINGERBASS_SOURCES` and `PICKBASS_SOURCES`
keys at lines 5575–5621. Removing or renaming a bass mapping therefore writes the current
set but neither rejects nor removes the old family-owned WAV.

`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\gen_crate_lib.py:84`
then scans and embeds every `.wav` still present, so an obsolete take is republished.
The derived guard at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\crates\ferrosintesis\src\inventory.rs:219`
tracks only whether any validator appears before a function's first transitive write.
Unrelated conditional validations make `main()` look guarded; the scoped assertions at
lines 1024–1034 cover only Kawai and Steinway.

Expected: a selected bass rebake rejects obsolete finger/pick outputs before any fetch or
write. Actual: a retired source entry can remain packaged and the source-derived oracle
stays green.

This is a family/path-sensitivity residual of closed `MM-BUG-KILN-00145` and
`MM-BUG-KILN-00156`, not their original helper-enumeration defect. No Open bug covers bass.

## Fix

Validate the combined finger/pick expected set for the shared bass crate before any
selected bass side effect. Strengthen the oracle to associate each selected output family
and expected table with its own validation path. Add a negative control where an unrelated
family's conditional validator appears before the bass write, and a bass regression that
removes one mapping while leaving its old WAV on disk.

### Verification summary (2026-08-01, independent — Claude Opus 5)

Verified on trunk `65220c3` (contains fix `b9114c8`), in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-verify-mm-bug-crucible-00022-closure`.
The fixer was OpenAI GPT-5 Codex, so this is a genuine second pair of eyes.

**Root cause addressed.** The production change is two lines in
`D:\language\ferrosintesis\tools\ferrosintesis-samples\prepare.py:5429` — a
`want("fingerbass") or want("pickbass")` guard that calls
`_validate_generated_output_families({"fingerbass", "pickbass"}, FINGERBASS_SOURCES | PICKBASS_SOURCES)`
alongside the existing Steinway / Kawai / Headroom validations, i.e. before any bass
fetch or write. The shared bass crate holds both families, so validating the *combined*
expected set is what makes a retired mapping's orphan WAV detectable.

**Fails-before / passes-after, actually run (not taken on faith).** I removed just those
two production lines from the worktree and re-ran both new regressions:
- `test_prepare.BassOutputInventoryTest.test_removed_mapping_rejects_its_stale_output_before_fetching_or_writing`
  FAILED — `main()` reached `ensure_ebass_sources(src)` at
  `D:\language\ferrosintesis\tools\ferrosintesis-samples\prepare.py:5502` with the stale
  WAV still on disk, exactly the reported behaviour.
- `inventory::tests::every_generated_bake_output_family_is_inventory_validated` FAILED at
  `D:\language\ferrosintesis\crates\ferrosintesis\src\inventory.rs:1048` — "main must
  validate both bass output families against their combined source tables before using
  either table".
Restoring the two lines (tree then byte-identical to trunk, `git status` clean) turned
both green. The strengthened oracle also carries its own negative control,
`inventory::tests::bake_output_inventory_oracle_rejects_an_unrelated_conditional_before_bass_use`,
which passes — an unrelated Headroom validator before the bass write no longer satisfies it.

**Gates green on the fixed tree:** `python3 -m unittest test_prepare` 140 pass / 0 fail;
`cargo test -p ferrosintesis --lib` 850 pass / 0 fail / 44 ignored. No unrelated failures.

**Residual considered, none split out.** The runtime regression retires a *fingerbass*
mapping only; a pickbass retirement is not separately exercised. It takes the identical
call, combined expected set and output directory, and the oracle binds both source tables,
so this is coverage symmetry rather than an untested path — not worth a new ID.

## Notes

The current committed inventory is internally consistent; the defect is the unguarded
retirement path. Static review only. No generator, application, test, build, render, or
exploratory harness ran. Estimated effort: Small–Medium.
