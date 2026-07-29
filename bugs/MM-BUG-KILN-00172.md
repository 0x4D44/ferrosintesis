# MM-BUG-KILN-00172 — Drum-kit regeneration trusts unauthenticated warm-cache inputs

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / drum-kit cache
- **Raised:** 2026-07-29
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260729T135230Z-p67316-n040854600-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00172-run-fix-20260729T135230Z-p67316-n040854600-c1
- **Owner base:** 3dac1b4ad25242120db2e8f2d6f513b85395071b
- **Owner fingerprint:** -
- **Owner since:** 2026-07-29T13:52:30Z
- **Owner until:** 2026-07-29T15:52:30Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The documented drum-kit regeneration path accepts persistent cache entries without
proving that they came from either pinned source revision.

`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\tools\ferrosintesis-samples\prepare_drumkit.py:225`
derives each cache name from the URL basename. Lines 233–239 reuse any existing
FLAC without a URL or content check. Lines 207–214 reuse any decoded WAV that
`wave.open` can parse; they do not bind it to the FLAC bytes or decode recipe.
The cache directory at lines 370–373 contains only the first twelve characters
of the two source revisions.

Static reproduction:

1. Put a different valid FLAC at one expected cache path, or a different valid
   decoded WAV at its `_dec.wav` path.
2. Run the documented `prepare_drumkit.py` regeneration.

Expected: a warm source is reused only when its URL and bytes match the pinned
source, and a decoded WAV is reused only when it is derived from that source
under the current decode recipe.

Actual: the FLAC is accepted by existence alone. A parseable decoded WAV is
accepted without consulting the FLAC at all. The staged result then replaces the
tracked package WAVs at lines 322–347. This can silently sever the source and
licence evidence in
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\crates\ferrosintesis-samples-drumkit2\PROVENANCE.md:29`.

This is the same defect class as closed `MM-BUG-KILN-00139` and
`MM-BUG-KILN-00151`, but their authenticated helpers live in `prepare.py`;
`prepare_drumkit.py` bypasses them. Static inspection found no evidence that the
current committed WAVs came from the wrong source. The generator was not run.

## Fix

Route FLAC intake through URL-and-content-bound cache handling. Bind each decoded
WAV to the authenticated FLAC digest and an explicit decode-recipe revision.
Reject and rebuild legacy, altered, stale, or malformed entries.

Add negative regressions for a substituted valid FLAC, substituted valid decoded
WAV, changed URL/revision under a stable basename, and changed decode recipe.
Keep a healthy-cache control that proves an authenticated warm entry is reused.

## Notes

Raised by the 2026-07-29 static review of
`crates/ferrosintesis-samples-drumkit2/`. Estimated effort: Medium.
