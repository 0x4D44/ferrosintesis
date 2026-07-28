# MM-BUG-KILN-00166 — Steinway rebakes can retain obsolete WAVs

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** Steinway sample generation / output inventory
- **Raised:** 2026-07-28
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260728T232217Z-p36364-n404969000-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00166-run-fix-20260728T232217Z-p36364-n404969000-c1
- **Owner base:** fc3193dd8ec05995066e1ab5137b76d5e461b3be
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T23:22:17Z
- **Owner until:** 2026-07-29T01:22:17Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static reproduction: tools/ferrosintesis-samples/prepare.py:704-710 defines STEINWAYB_SOURCES. The main path validates only Headroom output inventory at tools/ferrosintesis-samples/prepare.py:5324-5327, then includes STEINWAYB_SOURCES in the generic writer at :5526-5572. It never validates that the Steinway output directory contains exactly the current expected set.

Expected: selecting a Steinway regeneration rejects or removes obsolete owned WAVs before fetching or writing, so a retired source/zone cannot remain packaged.

Actual: removing or renaming a STEINWAYB_SOURCES entry leaves the old crates/ferrosintesis-samples-vcsl-steinway/samples/steinwayb_*.wav untouched. tools/ferrosintesis-samples/gen_crate_lib.py:29-33 scans every remaining WAV, so a later library regeneration re-embeds the obsolete payload. Even without regenerating the table, the existing include_bytes entry continues to ship the stale file. Current inventory is internally consistent; the defect is the unguarded retirement path.

Concrete fix: call _validate_generated_output_inventory("steinwayb", STEINWAYB_SOURCES) before any selected Steinway write. Strengthen the source-derived inventory oracle so validation is associated with each writer's family and expected set, and add a negative control with a removed Steinway entry plus stale on-disk file. Coordinate the class fix with open MM-BUG-KILN-00163, the Kawai sibling.

Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
