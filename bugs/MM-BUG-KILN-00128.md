# MM-BUG-KILN-00128 — Gong-only regeneration also rewrites the bottle bank

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / gong bank regeneration
- **Raised:** 2026-07-26
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260726T081806Z-p3376-n315034900-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00128-run-fix-20260726T081806Z-p3376-n315034900-c1
- **Owner base:** 3f38cd3a20f15068a47237dde39001bb1e451b15
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T08:18:06Z
- **Owner until:** 2026-07-26T10:18:06Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-gong/`)

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
