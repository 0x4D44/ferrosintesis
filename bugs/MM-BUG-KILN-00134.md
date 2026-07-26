# MM-BUG-KILN-00134 — Salamander warm cache bypasses the pinned archive hash

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / grand-piano provenance
- **Raised:** 2026-07-26
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260726T132336Z-p3016-n723439500-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00134-run-fix-20260726T132336Z-p3016-n723439500-c1
- **Owner base:** daf18d1dec63435698eea1829740a72d131abf48
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T13:23:36Z
- **Owner until:** 2026-07-26T15:23:36Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`)

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
