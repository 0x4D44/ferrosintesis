# MM-BUG-KILN-00139 — Headroom rebakes trust mutable sources and invalid caches

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample assets / Headroom source intake
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T133112Z-p49604-n076479100-c1 branch=task/bug-MM-BUG-KILN-00139-run-fix-20260726T133112Z-p49604-n076479100-c1 code=40cc61da138b1dc7226abbcd1271a10d5855dce2 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (636 passed) and `test --workspace --exclude amp-lab --locked` (747 passed) - 1486 tests, 0 failures; the sample-tool Python suite passes 67. Original observation re-run by execution. The fix replaces the existence-only warm-cache guard with `ensure_flac_sources` (`prepare.py:1499`), which accepts a decoded WAV only when a manifest binds its exact bytes to BOTH the pinned FLAC hash and the decode recipe, and caches sources by upstream basename so Headroom's 54 destination names can share its 45 FLACs. `PinnedFlacCacheTest` (`test_prepare.py:860`) adds 11 tests covering the five negatives the bug asked for plus four more, and the full sample-tool suite passes 67 tests. CLOSED WITHOUT A SPLIT, having checked the two candidate residuals the review raised and judged neither to be one. First, the claim that the identical defect is live for the VCSL `steinwayb` and `kawai` banks: I read the path myself and it is a DIFFERENT shape - those banks go through `ensure_direct_sources` (`prepare.py:3191-3193`) and carry no per-file SHA-256 pin at all, so there is no pin being bypassed; they are pinned by `VCSL_REV` in the source URL. Whether per-file pins are wanted there is a design question about an unpinned source, not a residual of this fix, and asserting otherwise would misdescribe it. Second, that `HEADROOM_RECIPE_REV` is a hand-maintained token rather than one derived from the decode argv it describes: that is a real observation about how the manifest binding could drift, but the token is part of the fix's own design rather than something the fix left unfinished, and it is the kind of judgement the owner should make rather than something this verify-only pass should assert as a defect. Both are recorded here rather than minted as ids.)

## Observation

The documented Headroom regeneration recipe is described as deterministic at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\crates\ferrosintesis-samples-headroom\PROVENANCE.md:46`.
Its source and cache contract is not deterministic or transactional:

- `_HEADROOM_BASE` follows the mutable upstream `master` branch at
  `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\prepare.py:746`.
  None of the 45 unique FLAC payloads behind the 54 destination names has a
  pinned revision or expected digest.
- `ensure_flac_sources` accepts an existing decoded WAV without checking its
  identity, format, or completeness at
  `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\prepare.py:1366`.
  It also accepts an existing FLAC without verifying its content.
- ffmpeg writes directly to the final cache WAV at
  `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\prepare.py:1379`.
  An interruption after file creation can strand a partial output. The next
  run skips that entry solely because the path exists.
- Headroom shares the cache rooted under the unrelated `VSCO_REV` at
  `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-134004\tools\ferrosintesis-samples\prepare.py:2943`.
  A future Headroom source revision therefore would not invalidate its warm
  decoded entries.

Expected: the documented command consumes one immutable, authenticated source
set, and it either commits a fully validated cache entry or leaves no entry for
a later run to trust.

Actual: clean machines can consume different upstream bytes, warm machines can
reuse stale or altered bytes, and an interrupted conversion can poison the warm
cache. The resulting tracked bank can still pass the generated inventory checks
because those checks describe the newly generated output rather than its source
identity.

This is a regeneration-path defect. Static inspection found no evidence that
the currently committed Headroom WAVs are corrupt or from the wrong source.

## Fix

Introduce a dedicated immutable `HEADROOM_REV`, use commit-addressed URLs, and
record expected SHA-256 values for every unique source FLAC. Put the Headroom
cache under its own source/recipe revision and verify cached FLAC and WAV
entries before accepting them.

Decode to a unique sibling temporary file, validate the complete PCM contract,
then atomically replace the cache WAV. Remove the temporary file after failure
and rebuild legacy, malformed, or identity-mismatched cache entries from a
verified FLAC.

Add focused negative regressions for changed upstream bytes, an altered cached
FLAC, a truncated cached WAV, a Headroom revision change with stable filenames,
and interrupted ffmpeg output.

Estimated effort: Medium.

## Notes

This is the direct-FLAC counterpart of closed `MM-BUG-KILN-00062`, whose fix
guards archive-backed intake. It does not cover `ensure_flac_sources`.

The cache identity and interrupted-write observations are one bug because they
share the same acceptance invariant, implementation surface, and regression
suite. Splitting them would create colliding fixes.

No application, generator, build, test, render, or exploratory harness ran.
