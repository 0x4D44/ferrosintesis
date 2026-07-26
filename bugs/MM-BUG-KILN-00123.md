# MM-BUG-KILN-00123 — Dark-grand rebakes retain obsolete generated WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / dark-grand generation
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-dark-salamander/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T082900Z-p48364-n570595900-c1 branch=task/bug-MM-BUG-KILN-00123-run-fix-20260726T082900Z-p48364-n570595900-c1 code=5911b8124bde56e4c09509e86ebfac483de96c7b gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (635 passed) and `test --workspace --exclude amp-lab --locked` (740 passed) - 1478 tests, 0 failures; the sample-tool Python suite passes 44. Original observation re-run by driving the production code path myself, with four scenarios rather than the fixer's one. `_bake_darkened_grand` (`tools/ferrosintesis-samples/prepare.py:2656`) now derives `expected_outputs = {"dark" + fn for fn in source_names}` from the CURRENT `-grand` bank, computes the unexpected owned outputs, and raises a `ValueError` naming them. I built temp repos and patched `read_wav` to explode if reached, so any pass proves the check runs BEFORE the first read or write: (a) the bug's exact static reproduction - a `darkgrand_old.wav` whose `grand_old.wav` is gone - is REJECTED, naming the file; (b) a renamed source that leaves its old output behind is also rejected, which is the provenance/licensing scenario the bug specifically flagged; (c) an exact projection of the source bank is NOT rejected, so there is no false positive; and (d) a brand-new source name with its paired output is accepted, proving the expected set is genuinely derived from the source inventory rather than a hardcoded list. The committed regression `test_rebake_rejects_unexpected_owned_output_before_writing` pins the same fail-before-writing property.)

## Observation

The crate documents a deterministic, local regeneration from the tracked grand
bank at `crates/ferrosintesis-samples-dark-salamander/README.md:14-15` and
`crates/ferrosintesis-samples-dark-salamander/PROVENANCE.md:25-44`.

`tools/ferrosintesis-samples/prepare.py:2648-2666` creates the destination and
overwrites one `dark<source-name>` file for every current `grand_*.wav`. It never
derives and checks the complete expected destination-name set, so it neither
rejects nor removes an obsolete owned `darkgrand_*.wav`.

Static reproduction:

1. Start with a generated `darkgrand_old.wav`.
2. Rename or remove the paired `grand_old.wav` from the source inventory.
3. Run the documented `prepare.py --only=darkgrand` rebake.

Expected: the destination is an exact projection of the current source bank, or
the command fails closed and identifies the unexpected generated file.

Actual: `darkgrand_old.wav` remains untouched. Cargo packages every file under
`samples/**` (`crates/ferrosintesis-samples-dark-salamander/Cargo.toml:10`).
If `tools/ferrosintesis-samples/gen_crate_lib.py` is then run, its directory scan
at lines 28-32 and generated table at lines 59-62 bless the stale WAV into
`SAMPLES`, making the crate-level inventory test self-consistent.

This matters especially when a source is removed or renamed for provenance or
licensing reasons: its derived payload can survive in the published crate.

The current tree is not corrupt. Static inventory comparison found the same 54
source-derived and destination names.

## Fix

Make `_bake_darkened_grand` derive the expected `dark + source_name` set and fail
closed with the explicit list of unexpected owned `darkgrand_*.wav` files before
writing. Failing is safer than silently deleting tracked sample-source assets.

Add a focused regression with an extra destination file and prove the rebake
rejects it.

Estimated effort: Small.

## Notes

The workspace provenance-count oracle may expose some stale inventories later,
but the documented rebake itself currently succeeds while leaving the stale
payload in place. `gen_crate_lib.py` trusts the destination directory rather than
the source relationship.

No generator, test, build, render, or application execution was performed. The
failure follows directly from the enumerated filesystem operations and was
independently confirmed by the maintainability and devil's-advocate lenses.
