# MM-BUG-KILN-00139 — Headroom rebakes trust mutable sources and invalid caches

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample assets / Headroom source intake
- **Raised:** 2026-07-26
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260726T133112Z-p49604-n076479100-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00139-run-fix-20260726T133112Z-p49604-n076479100-c1
- **Owner base:** 445ee4f44e1aaaa40242b787828d4caec2f25890
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T13:31:12Z
- **Owner until:** 2026-07-26T15:31:12Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new`)

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
