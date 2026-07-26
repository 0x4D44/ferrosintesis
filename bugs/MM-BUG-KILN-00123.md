# MM-BUG-KILN-00123 — Dark-grand rebakes retain obsolete generated WAVs

- **State:** Open
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-dark-salamander/`)

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
