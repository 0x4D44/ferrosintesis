# MM-BUG-KILN-00134 — Salamander warm cache bypasses the pinned archive hash

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / grand-piano provenance
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
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T132336Z-p3016-n723439500-c1 branch=task/bug-MM-BUG-KILN-00134-run-fix-20260726T132336Z-p3016-n723439500-c1 code=dfee483103f83aab8dfb64dd51be0276b0d897f8 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (636 passed) and `test --workspace --exclude amp-lab --locked` (747 passed) - 1486 tests, 0 failures; the sample-tool Python suite passes 67. Original observation re-run BY EXECUTION, which the bug itself had not done - it recorded a static reading of the control flow. A sub-agent built the reproduction and ran it against both the pre-fix `prepare.py` (as a control that proves the probe can see the defect) and the current tree: with all 54 destination names present but one cached `grand_*.wav` replaced by a different valid WAV of identical size, the PRE-FIX helper accepted the substitute (the bake loop would have consumed sha256 `36b6499a...` instead of the pinned member's `e7afc1ed...`), while the CURRENT helper rejects and rebuilds it (bake-loop bytes now hash `e7afc1ed...`, matching the pin). The bug's three sub-claims behave the same way: a changed archive pin with unchanged member names now refetches instead of reusing stale members, a truncated member is now restored, and a good warm cache still costs only one fetch, so the fix does not re-download hundreds of MB to authenticate a healthy cache. The mechanism is the content-addressed manifest predicate `cached_members_match` (`prepare.py:1270`) that `ensure_archive_sources` has used since MM-BUG-KILN-00062, with staged extraction and `os.replace` so an interrupted rebuild cannot half-replace the members. `SalamanderArchiveCacheTest` (`test_prepare.py:718`) adds 10 methods and was proven non-vacuous by two independent mutations applied to temp copies: reverting the warm-cache guard to the original existence check turns exactly 6 of them red, and dropping only the staging directory turns exactly the atomicity test red. CLOSED WITH A RESIDUAL SPLIT OUT AS MM-BUG-KILN-00141. Applying this repo's "enumerate all of L before fixing" rule, I censused every pinned-archive helper in `prepare.py` myself: `ensure_ydp_sf2` (`prepare.py:2615`) is the one remaining helper whose SHA-256 check sits inside an `if not os.path.exists(...)` guard and is therefore unreachable on a warm cache - the same shape this bug reported, still live, and load-bearing because `_bake_ydp_grand` rewrites nine tracked WAVs from those bytes while that crate's provenance claims the source is pinned. Worth recording that my first pass at that census was WRONG: a pattern match flagged the two MuseScore helpers as unauthenticated, and reading them showed their existence guard covers only the download while the hash comparison runs unconditionally. The full corrected table is on 00141.)

## Observation

The grand asset crate says its Salamander source archive is pinned and verified:

- `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\README.md:19`
- `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\PROVENANCE.md:27`
- `D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\PROVENANCE.md:66`

The bespoke Salamander loader does not establish that provenance on a warm
cache. `ensure_salamander_sources()` returns when all 54 destination filenames
exist at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:1395`.
That return happens before the archive SHA-256 check at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:1401`.

Static reproduction:

1. Populate the persistent sample-generator cache normally.
2. Replace one cached `grand_*.wav` with a different valid WAV while leaving all
   54 expected names present.
3. Run the documented generator, or the scoped
   `python tools/ferrosintesis-samples/prepare.py --only=grand`.

Expected: the warm cache proves that each member came from the currently pinned
archive, or it is rejected and rebuilt.

Actual: the existence-only check returns without reading either the archive or a
member manifest. The main bake loop reads the altered cache at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:3119`
and replaces the tracked grand output at line 3150. A changed archive pin with
unchanged member names likewise reuses the old members. A truncated member is
trusted until later decoding fails instead of self-healing.

The crate tests at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\src\lib.rs:251`
cannot catch a same-size, valid-WAV substitution: they pin the filename set,
aggregate bytes, and RIFF/WAVE magic, not each payload's source identity.

The current 54 packaged WAVs are not shown to be altered. Static inspection
found a complete, unique, structurally canonical inventory. This defect is the
untrusted regeneration path.

## Fix

Apply the existing content-addressed member-manifest semantics from
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:1215`
to the Salamander tar.bz2 helper:

- bind the manifest to `SALAMANDER_ARCHIVE_SHA256`;
- hash every extracted member before accepting a warm cache;
- reject legacy, altered, truncated, incomplete, or wrong-pin caches;
- self-heal a bad cached archive once, then fail closed;
- stage extraction safely and write the manifest atomically only after success.

Add focused regressions paralleling
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\test_prepare.py:568`
for an altered valid member, a truncated member, a changed pin, a missing or
corrupt manifest, and a corrupt cached archive.

Estimated effort: Medium.

## Notes

This is a residual sibling of closed `MM-BUG-KILN-00062`, not a duplicate of
the implementation it fixed. That bug made the shared `ensure_archive_sources`
path content-addressed, but `ensure_salamander_sources` remained separate and
kept the old existence-only decision.

No generator, application, build, test suite, render, or exploratory harness ran
during discovery. The failure follows directly from the warm-cache control flow.
