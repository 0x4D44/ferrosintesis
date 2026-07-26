# MM-BUG-KILN-00143 — Honky-tonk rebakes retain obsolete generated WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / honky-tonk generation
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T151951Z-p14020-n937483200-c1 branch=task/bug-MM-BUG-KILN-00143-run-fix-20260726T151951Z-p14020-n937483200-c1 code=bd72fe78a418350aa4e00caae49a5aed017d5c12 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, and both test suites - 1486 tests, 0 failures; the sample-tool Python suite passes 78, up from 75. Original observation re-run by driving the guard, not by reading the diff. The fix does better than a per-bank patch: it generalises MM-BUG-KILN-00140's helper into the shared, parameterised `_validate_generated_output_inventory(family, expected, repo_root=None)` (`tools/ferrosintesis-samples/prepare.py:3087`) and calls it as the FIRST statement of `_bake_honkytonk` (`:2734`) - ahead of `ensure_archive_sources` and every write, so it fails closed before the bake can touch a tracked asset. Its expected set is derived, `{f"honkytonk_{n}.wav" for n in HONKYTONK_NOTES}`, not a second hand-written list. Driving it in temp repos: an exact projection of the note list is accepted, a stale `honkytonk_old.wav` left behind after its entry is removed is REJECTED by name, and an unrelated non-`honkytonk_` file is correctly ignored, so the guard is scoped to the outputs it owns. The full sample-tool suite passes 78 tests. CLOSED WITH A CLASS-LEVEL RESIDUAL SPLIT OUT AS MM-BUG-KILN-00145. This is the FOURTH time this defect has been reported and fixed one bank at a time - dark grand (00123), drum kit (00124), headroom (00140), and now honky-tonk - and although this fix finally made the guard reusable, the call is still hand-placed: it is invoked exactly twice in `prepare.py` today, so a fifth bank does not inherit it. Other helpers have the same shape, enumerating a fixed source list and writing into their crate's `samples/` directory without ever inspecting it for files the enumeration no longer names - `_bake_ydp_grand` over `YDP_ZONE_MIDI`, and `_bake_b1upright`, which owns the 52 WAVs of the DEFAULT GM 0 piano since 2026-07-26. I have deliberately pitched that at the same evidential level the original reports used: 00140 and 00143 were themselves static readings that noted the committed inventory was clean, and likewise I have not shown either crate is currently inconsistent, only that the guard which would catch it is absent while `Cargo.toml` packages every WAV under `samples/**`. The remedy already exists in this same file: MM-BUG-KILN-00141 ended the sibling class by deriving its helper set from the `ast` rather than a list, with a negative control. 00145 asks for the same treatment here.)

## Observation

The documented rebake at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\crates\ferrosintesis-samples-honkytonk\README.md:15`
routes to `_bake_honkytonk`. That function derives the current output names from
`HONKYTONK_NOTES`, creates the destination directory, and overwrites only those
names at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\tools\ferrosintesis-samples\prepare.py:2709`.
It never compares the complete destination `honkytonk_*.wav` set with the
expected names.

Static reproduction:

1. Start with a generated `honkytonk_old.wav`.
2. Remove or rename its entry in `HONKYTONK_NOTES`.
3. Run the documented `prepare.py --only=honkytonk` rebake.

Expected: the rebake fails closed before writing and identifies the unexpected
owned output.

Actual: the loop at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\tools\ferrosintesis-samples\prepare.py:2723`
never visits `honkytonk_old.wav`, so it remains untouched. Cargo packages every
file under `samples/**` through
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\crates\ferrosintesis-samples-honkytonk\Cargo.toml:10`.
If the generated Rust table is refreshed,
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-151908\tools\ferrosintesis-samples\gen_crate_lib.py:29`
enumerates the leftover and line 62 embeds it, making the crate inventory tests
self-consistent again.

A source removed or renamed for provenance, licensing, or quality reasons can
therefore remain in the published crate. The current committed inventory is
clean: all nine packaged names match `HONKYTONK_NOTES`, the embedded table, and
the consumer zone table.

## Fix

Before any selected honky-tonk output is written, derive the expected
`honkytonk_<note>.wav` set from `HONKYTONK_NOTES`. Fail closed with the explicit
list of unexpected owned `honkytonk_*.wav` files. Do not silently delete tracked
sample-source assets.

Add focused regressions for an extra output and a renamed note. Both must prove
rejection occurs before the first write.

Estimated effort: Small.

## Notes

This shares a defect class with `MM-BUG-KILN-00123` (dark-grand) and
`MM-BUG-KILN-00140` (Headroom), but it is not a duplicate. Their fixes are
family-specific and never run for `_bake_honkytonk`.

Raised by the read-only coverage-ledger review of
`crates/ferrosintesis-samples-honkytonk/`. No app, test suite, Cargo command, or
exploratory harness was run.
