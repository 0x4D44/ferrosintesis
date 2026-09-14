# MM-BUG-CRU-00068 — Freesound and Eastman source intakes copy into the shared vsco2ce_src temp directory with no lock or per-run path

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent source isolation
- **Raised:** 2026-09-13T19:26:11Z
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
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:45:03Z, deltic:auto role=fix run=fix-20260913T212430Z-44a85e6e branch=task/bug-MM-BUG-CRU-00068-run-fix-20260913T212430Z-44a85e6e code=d44a74e37c6fec84052d83eac7bb713962f44ea7 gate=manual) -> Open (2026-09-14T21:33:15Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the committed-source isolation is right, but the new three-argument _prepare_generic_source_sample call breaks four existing test_prepare.py tests, leaving the gate's unittest step red)

## Observation

Residual found at independent verification of MM-BUG-CRU-00049 (2026-09-13, trunk 8b6a6f86), by reading the code. The mandolin fix (0179cee7) removed its shared staging copy, but ensure_freesound_sources (tools/ferrosintesis-samples/prepare.py:1739) and ensure_eastman_sources (prepare.py:1758) still shutil.copyfile committed sources into the host-global vsco2ce_src temp directory under fixed names, with no lock and no per-run directory. Two concurrent --only=rhodes/dulcimer/musicbox/bottle/eastpick/eastpluck regenerations can therefore read each other's copies, the same defect shape CRU-00049 fixed for mandolin. Expected: bakes read committed sources directly or from a per-run private directory.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `d44a74e3`) by an agent other than the fixer. **Reopened.**

**What the fix gets right.** `ensure_freesound_sources` and `ensure_eastman_sources` no longer copy into the shared `vsco2ce_src` temp directory. They validate and return the committed source directories, and `main()` reads rhodes, dulcimer, musicbox, bottle, eastpick and eastpluck straight from them (Eastman through `source_name`). That removes the fixed-name shared copies the observation describes.

**Why reopened.** The same commit made `main()` call `_prepare_generic_source_sample(fn, family_src, source_name)` with three positional arguments. Four existing tests patch that function with two-argument fakes: `test_prepare.py:4985` `staged_sample`, `:5022` `fail_on_third`, and `:5100` and `:5172` `fake_transform`, all written 2026-09-13 before this fix. They now error with `TypeError: ... takes 2 positional arguments but 3 were given`: two tests in `GenericFamilyWholeBankPublicationTest`, plus `SteinwayGenericScopedPublicationTest` and `StringsGenericScopedPublicationTest`. Pinned to this single-parent commit in clean detached worktrees: the four tests pass at `d44a74e3^` (Ran 4, OK) and error at `d44a74e3` (errors=4). On `1d87b00f` the gate step `python3 -m unittest discover -s tools/ferrosintesis-samples` ends 'Ran 281 tests ... FAILED (errors=4)'.

**To close.** Keep the isolation, and make the call and the existing fakes agree, so the gate's unittest step is green.

## Notes
