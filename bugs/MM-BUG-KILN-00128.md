# MM-BUG-KILN-00128 — Gong-only regeneration also rewrites the bottle bank

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / gong bank regeneration
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-gong/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T081806Z-p3376-n315034900-c1 branch=task/bug-MM-BUG-KILN-00128-run-fix-20260726T081806Z-p3376-n315034900-c1 code=02717f27862004d75afa3168c7a8e1cde05bf32f gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (635 passed) and `test --workspace --exclude amp-lab --locked` (740 passed) - 1478 tests, 0 failures; the sample-tool Python suite passes 44. Original observation re-run BY EXECUTING the documented command, not by reading the control flow - the bug itself notes it was a read-only review that never ran it. I snapshotted the bytes and mtimes of the gong and bottle sample banks, ran `python tools/ferrosintesis-samples/prepare.py --local-only` verbatim from the worktree root, and re-compared: the two gong outputs were rewritten byte-identically (the deterministic regeneration the package documents), and `crates/ferrosintesis-samples-bottle/samples/bottleloop_G3.wav` was UNTOUCHED - not even its mtime moved, so `bake_bottle_loop()` did not run at all. `git status --porcelain` was empty afterwards, so no tracked file was dirtied. The bug's Actual ("It also regenerates and replaces the bottle-bank output") is therefore false on this tree. The mechanism is a two-line change in `_family_selection` (`prepare.py:2874-2883`): `--local-only` now pins `only = {"gong"}`, so `_wants_family(only, "bottle")` is false. The committed regression `test_command_modes_select_only_the_intended_local_banks` covers all three modes - `--local-only` bakes gong alone, `--only=bottle` bakes bottle alone, and no arguments bakes both - and asserts on the actual bake calls rather than on the parsed selection, which is the right level. One minor wart I checked and am not splitting out: passing `--local-only` together with an explicit `--only=` silently overrides the latter. It cannot cause an unwanted write (the override only ever narrows to gong) and `--local-only` is documented as the gong regeneration path, so it is defensible; noting it here rather than filing it.)

## Observation

The gong package tells maintainers to run:

```text
python tools/ferrosintesis-samples/prepare.py --local-only
```

`crates/ferrosintesis-samples-gong/README.md:15-18` and
`crates/ferrosintesis-samples-gong/PROVENANCE.md:119-128` say this regenerates
only the gong bank.

Static reproduction on baseline `c596deb7338bba9f6b1c8727fe0c7ee6c93bb79b`:

1. `tools/ferrosintesis-samples/prepare.py:2846-2848` sets `local_only`.
2. No `--only=` argument was supplied, so `only` remains `None` and
   `want(fam)` returns true for every family at lines 2855-2861.
3. `local_only` skips the fetched full-bank block, then the gong loop runs at
   lines 3090-3102.
4. Execution continues to `if want("bottle")` at lines 3104-3110. That
   condition is also true, so `bake_bottle_loop()` replaces the unrelated
   tracked `crates/ferrosintesis-samples-bottle/samples/bottleloop_G3.wav` via
   lines 2780-2782.

**Expected.** The documented gong-only command must read the two committed gong
sources and replace only the two gong outputs.

**Actual.** It also regenerates and replaces the bottle-bank output. The bottle
recipe's own parity test at `tools/ferrosintesis-samples/test_prepare.py:729-754`
says its recovered recipe is not byte-identical to the committed asset, so this
unexpected write can dirty a tracked file outside the requested bank.

The command was not executed because this was a read-only review. The control
flow and destination write are explicit; the exact bottle byte diff on this
machine is unverified.

## Fix

Make `--local-only` select the gong family rather than merely skip the fetched
block. For example, make the bottle branch require `not local_only`, or normalize
`--local-only` to the same family-selection model as `--only=gong`.

Add a fail-first command-selection regression that stubs the bake functions and
proves:

- `--local-only` invokes gong and never bottle;
- `--only=bottle` invokes bottle and never gong;
- a full run retains its intentional gong-and-bottle behavior.

Estimated effort: Small.

## Notes

No matching Open bug or Draft requirement was found by searching the current
ledger for the command and both bank names.
