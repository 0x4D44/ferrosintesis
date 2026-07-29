# MM-BUG-KILN-00166 — Steinway rebakes can retain obsolete WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** Steinway sample generation / output inventory
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260728T232217Z-p36364-n404969000-c1 branch=task/bug-MM-BUG-KILN-00166-run-fix-20260728T232217Z-p36364-n404969000-c1 code=84c6446 gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green)

## Observation

Static reproduction: tools/ferrosintesis-samples/prepare.py:704-710 defines STEINWAYB_SOURCES. The main path validates only Headroom output inventory at tools/ferrosintesis-samples/prepare.py:5324-5327, then includes STEINWAYB_SOURCES in the generic writer at :5526-5572. It never validates that the Steinway output directory contains exactly the current expected set.

Expected: selecting a Steinway regeneration rejects or removes obsolete owned WAVs before fetching or writing, so a retired source/zone cannot remain packaged.

Actual: removing or renaming a STEINWAYB_SOURCES entry leaves the old crates/ferrosintesis-samples-vcsl-steinway/samples/steinwayb_*.wav untouched. tools/ferrosintesis-samples/gen_crate_lib.py:29-33 scans every remaining WAV, so a later library regeneration re-embeds the obsolete payload. Even without regenerating the table, the existing include_bytes entry continues to ship the stale file. Current inventory is internally consistent; the defect is the unguarded retirement path.

Concrete fix: call _validate_generated_output_inventory("steinwayb", STEINWAYB_SOURCES) before any selected Steinway write. Strengthen the source-derived inventory oracle so validation is associated with each writer's family and expected set, and add a negative control with a removed Steinway entry plus stale on-disk file. Coordinate the class fix with open MM-BUG-KILN-00163, the Kawai sibling.

Estimated effort: Small.

## Fix

Code commit `84c6446`. `prepare.main()` now calls
`_validate_generated_output_inventory("steinwayb", STEINWAYB_SOURCES)` before
any Steinway fetch or write, and the family-scoped oracle was extended to cover
the Steinway family and expected set.

## Notes

### Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Fails-before proven twice, exactly as for the Kawai sibling. Deleting only the
two added `prepare.py` lines makes
`SteinwayOutputInventoryTest::test_removed_source_rejects_its_stale_output_before_fetching_or_writing`
fail with `inventory must be checked before reading`, and
`every_generated_bake_output_family_is_inventory_validated` fail at the Steinway
assertion. Both pass on the restored tree.

The retirement path the bug described is now guarded: a removed
`STEINWAYB_SOURCES` entry whose WAV is still on disk aborts the run with a
`ValueError` naming that file, before `ensure_direct_sources` fetches anything
or `write_wav_mono` writes anything.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
