# MM-BUG-KILN-00143 — Honky-tonk rebakes retain obsolete generated WAVs

- **State:** Open
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high)

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
