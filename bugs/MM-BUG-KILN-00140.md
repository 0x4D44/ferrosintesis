# MM-BUG-KILN-00140 — Headroom rebakes retain obsolete generated WAVs

- **State:** Open
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new`)

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
