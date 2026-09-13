# MM-BUG-KILN-00212 — Bottle provenance publishes an unusable regeneration command

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample package / bottle regeneration documentation
- **Raised:** 2026-08-16T11:38:32Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T195546Z-08892558
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00212-run-verify-20260913T195546Z-08892558
- **Owner base:** 1d32445ddbb4c73f657777f227eb41c80ad15152
- **Owner fingerprint:** sha256:9737b8eb61e9908625a6edc2451977c36651896a3ace82d3e6e28da913c19be5
- **Owner since:** 2026-09-13T19:55:46Z
- **Owner until:** 2026-09-13T21:55:46Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T11:38:32Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:33:12Z, deltic:auto role=fix run=fix-20260913T152407Z-60202476 branch=task/bug-MM-BUG-KILN-00212-run-fix-20260913T152407Z-60202476 code=6a425c224a99e05c355968c972449db879eb5976 gate=manual)

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
