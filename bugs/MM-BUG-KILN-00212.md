# MM-BUG-KILN-00212 — Bottle provenance publishes an unusable regeneration command

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample package / bottle regeneration documentation
- **Raised:** 2026-08-16T11:38:32Z
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
- **State history:** Open (2026-08-16T11:38:32Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:33:12Z, deltic:auto role=fix run=fix-20260913T152407Z-60202476 branch=task/bug-MM-BUG-KILN-00212-run-fix-20260913T152407Z-60202476 code=6a425c224a99e05c355968c972449db879eb5976 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: bottle PROVENANCE gives the repo-root prepare.py path; the bare spelling fails the recipe-routing oracle)

## Observation

`crates/ferrosintesis-samples-bottle/PROVENANCE.md:29` publishes
`python3 prepare.py --only=bottleloop` as the asset's regeneration command. The
repository's supported working directory is the repository root, and both command
examples in `tools/ferrosintesis-samples/README.md:190-208` invoke the script as
`python3 tools/ferrosintesis-samples/prepare.py`. There is no `prepare.py` at the
repository root or inside the bottle crate; the documented command works only after an
unstated change into `tools/ferrosintesis-samples/`.

Expected: the independently published provenance gives a runnable command with an
explicit working directory. Actual: following it from the supported repository-root
location fails before the generator starts because Python cannot find `prepare.py`.

The existing recipe guard at
`tools/ferrosintesis-samples/test_prepare.py:2783-2810` extracts only `--only=` values,
so it proves that `bottleloop` is a supported selector while accepting a nonexistent
script path. Static source review only; the generator, app, tests, build, package and
exploratory harness were not run.

## Fix

<unfixed — raised only>

Publish `python3 tools/ferrosintesis-samples/prepare.py --only=bottleloop` from the
repository root. Extend the packaged-recipe oracle to validate the executable script
path and working-directory contract as well as its selectors; include the current bare
`prepare.py` spelling as a negative control.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `6a425c22`) by an agent other than the fixer.

**Original observation re-derived.** `crates/ferrosintesis-samples-bottle/PROVENANCE.md:29` reads `python3 tools/ferrosintesis-samples/prepare.py --only=bottleloop`, run from the repository root; no bare `python3 prepare.py` command remains in any crate README, PROVENANCE or `lib.rs`. The script exists at that path and `bottleloop` is a supported selector (the bake itself was not run).

**Fails-before (method B).** Restoring the bare spelling fails `test_packaged_recipe_commands_use_root_relative_scripts_and_supported_selectors` (`'prepare.py' != 'tools/ferrosintesis-samples/prepare.py'`). Restored; both `PackagedRecipeRoutingTest` regressions pass on HEAD.

## Notes
