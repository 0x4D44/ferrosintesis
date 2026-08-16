# MM-BUG-KILN-00212 — Bottle provenance publishes an unusable regeneration command

- **State:** Open
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
- **State history:** Open (2026-08-16T11:38:32Z, raised via `deltic bugs new`)

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

## Notes
