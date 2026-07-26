# MM-BUG-KILN-00140 — Headroom rebakes retain obsolete generated WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / Headroom generation
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T140612Z-p42948-n863098400-c1 branch=task/bug-MM-BUG-KILN-00140-run-fix-20260726T140612Z-p42948-n863098400-c1 code=563c584015ff37e02a4029f8110c8fbb872b6b38 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, and both test suites - 1486 tests, 0 failures; the sample-tool Python suite passes 69. Original observation re-run by driving the production guard with the bug's own static reproduction, which the bug itself had only reasoned about. `_validate_headroom_output_inventory` (`tools/ferrosintesis-samples/prepare.py:3065`) derives the expected set from `HEADROOM_SOURCES`, lists the packaged `headroom_*.wav` files, and raises a `ValueError` naming any it does not own. I exercised it with four scenarios in temp repos: (a) the bug's exact case - a stale `headroom_old.wav` after its mapping entry is removed - is REJECTED by name; (b) a renamed source that leaves its old output behind is also rejected, which is the provenance/licensing scenario the bug called out as the reason this matters; (c) an exact projection of the source map is accepted, so there is no false positive; and (d) an unrelated non-`headroom_` file is ignored, so the guard is correctly scoped to the outputs it owns. I passed my own two-entry `sources` dict in each case and the guard honoured it, which confirms the expected set is genuinely derived rather than a second hardcoded list. Crucially the guard is WIRED IN, not merely present: it is called at `prepare.py:3128` inside `if want("headroom")`, under a comment stating it runs "before fetching a source or writing any selected output" - so it fails closed ahead of the first write, which is the property that actually protects the tracked assets. `HeadroomOutputInventoryTest` (`test_prepare.py:1018`) pins both halves, and its two method names say so explicitly - `test_extra_output_is_rejected_before_the_first_write` and `test_renamed_mapping_rejects_the_old_name_before_the_first_write`. Both pass, and the full sample-tool suite passes 69 tests. No residual: this is the third instance of the retained-obsolete-output class I have verified today (after MM-BUG-KILN-00123 for the dark grand and the drum-kit split in 00124), and unlike those I found nothing left unswept for the Headroom bank.)

## Observation

Headroom generation enumerates only the current `HEADROOM_SOURCES` mapping at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\prepare.py:3106`
and overwrites those outputs at line 3150. It never compares the complete
destination `headroom_*.wav` set with the expected mapping.

Static reproduction:

1. Start with a generated `headroom_old.wav`.
2. Remove or rename its entry in `HEADROOM_SOURCES`.
3. Run the documented Headroom rebake.

Expected: the rebake fails closed before writing and identifies the unexpected
owned output.

Actual: the loop never visits `headroom_old.wav`, so it remains untouched.
Cargo packages every WAV under `samples/**` through
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\crates\ferrosintesis-samples-headroom\Cargo.toml:10`.
If the generated Rust table is refreshed,
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\gen_crate_lib.py:29`
enumerates the leftover and line 62 embeds it, making the crate inventory
self-consistent again.

A source removed or renamed for provenance, licensing, or quality reasons can
therefore remain in the published crate. The current committed inventory is
clean: all 54 packaged names exactly match the current generator and consumer
tables.

## Fix

Before any selected Headroom output is written, derive the expected destination
set from `HEADROOM_SOURCES`. Fail closed with the explicit list of unexpected
owned `headroom_*.wav` files. Do not silently delete tracked assets.

Add focused regressions for an extra output and a renamed mapping. Both must
prove rejection occurs before the first write.

Estimated effort: Small for a Headroom guard; Medium if the guard is generalized
across all generated families.

## Notes

This shares a defect class with closed `MM-BUG-KILN-00123`, but it is not a
duplicate. That fix is bespoke to `_bake_darkened_grand` and never runs for the
Headroom family.

No application, generator, build, test, render, or exploratory harness ran.
