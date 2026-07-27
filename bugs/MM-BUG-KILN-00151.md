# MM-BUG-KILN-00151 — Direct sample cache ignores pinned source revisions

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / direct-source cache
- **Raised:** 2026-07-27
- **Owner:** deltic:claude
- **Owner role:** verify
- **Owner run:** verify-20260727T162301Z-p9812-n968602700-c92
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00151-run-verify-20260727T162301Z-p9812-n968602700-c92
- **Owner base:** 24f70eb0faedc8f7ab444e09aebb83e7e592e2a5
- **Owner fingerprint:** sha256:449a67a0aa476ecd45017fc29fc0bd5237a8f45647a4320fcd9e22b77d52ddf8
- **Owner since:** 2026-07-27T16:23:01Z
- **Owner until:** 2026-07-27T17:08:01Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T085110Z-p9812-n624876700-c57 branch=task/bug-MM-BUG-KILN-00151-run-fix-20260727T085110Z-p9812-n624876700-c57 code=ed7633742b1c172bb124eb1f919e754e9e1bca66 gate=python model=codex@xhigh)

## Observation

**Symptom.** The direct-download cache accepts any existing file that parses as a
WAV. It does not prove that the file came from the URL requested by the current
source tree.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\prepare.py:1242`
builds a cache path from the destination filename. Lines 1248–1254 reuse that
path whenever `read_wav()` succeeds; neither the requested URL nor a digest is
stored or checked.

This is reachable across 81 URL-sourced WAVs in
`ferrosintesis-samples-orchestral2`. The main path at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\prepare.py:3165`
keys the shared directory only by `VSCO_REV`, but 45 of those WAVs are selected
by the independent `VCSL_REV`. Advancing `VCSL_REV` therefore leaves the cache
path unchanged and reuses old, valid WAVs. Any valid local substitution is also
accepted for all 81.

**Expected.** A warm cache entry is reused only when its source URL and content
identity match the current pinned source.

**Actual.** Parseability is the complete warm-cache predicate. A warm and clean
machine can therefore rebake different bytes from the same source tree. This
review did not find evidence that the currently committed WAVs are wrong.

**Concrete fix.** Store an atomic sidecar for each direct cache entry containing
the exact URL and fetched-file SHA-256. Reuse only when both match. Refetch legacy,
changed, or altered entries. Add regressions for a valid-WAV substitution, a
revision/URL change under a stable destination, and a valid-cache no-refetch
control.

## Fix

Direct downloads now write an atomic `.source.json` sidecar containing the exact
source URL and fetched-file SHA-256. A warm entry is reused only when the
sidecar URL and current file digest both match. Legacy entries, changed pinned
URLs, and valid local substitutions therefore refetch before a bake can consume
stale bytes.

`ensure_direct_sources()` now uses the same authenticated helper. The banjo
float-WAV path also records URL and digest identity while deliberately skipping
stdlib WAV parsing for its ffmpeg-only input format.

Root cause: the former warm-cache identity was only the destination filename
plus WAV parseability. It stored neither the requested URL nor the fetched
content identity.

Regression coverage:

- `DirectSourceCacheTest`: 6/6 passed, covering legacy, altered, URL-changed,
  valid warm-cache, sidecar-content, and wrapper-routing cases.
- `DirectSourceCacheTest` plus
  `PrepareSampleBankTests.test_ensure_source_refetches_poisoned_cache_once`:
  7/7 passed.
- Full `tools/ferrosintesis-samples/test_prepare.py`: 79/79 passed.
- `python -m py_compile tools/ferrosintesis-samples/prepare.py
  tools/ferrosintesis-samples/test_prepare.py`: passed.

## Notes

Independently confirmed during the review of
`crates/ferrosintesis-samples-orchestral2/`. The same defect was fully described
in the earlier 2026-07-27 review of `ferrosintesis-samples-orchestral`, but that
pass could not write under `bugs/` and recorded no bug ID. This record puts that
confirmed finding into the Open queue rather than duplicating an existing bug.
