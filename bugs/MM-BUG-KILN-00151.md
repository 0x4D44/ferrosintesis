# MM-BUG-KILN-00151 — Direct sample cache ignores pinned source revisions

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / direct-source cache
- **Raised:** 2026-07-27
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00151-run-fix-20260727T085110Z-p9812-n624876700-c57-code-1785142875974
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T085110Z-p9812-n624876700-c57 branch=task/bug-MM-BUG-KILN-00151-run-fix-20260727T085110Z-p9812-n624876700-c57 code=2c2ac012b4fa gate=cargo model=codex@xhigh)

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

<unfixed — raised only>

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T085110Z-p9812-n624876700-c57 code=2c2ac012b4fa gate=cargo)

Agent-reported summary: Fixed MM-BUG-KILN-00151 in the sample preparation direct-source cache. Direct URL downloads now write an atomic sidecar for each fetched file and reuse a warm file only when the sidecar URL and SHA-256 match the current request. Legacy entries, URL-revision changes, and valid local WAV substitutions now refetch before the bake can consume stale bytes. The direct-source wrapper uses the same authenticated helper, and the banjo float-WAV path keeps URL/hash authentication without forcing stdlib WAV parsing. Added focused regressions that failed before the fix and pass after it.

Root cause: The warm-cache identity for direct downloads was the destination filename plus, for ensure_source, WAV parseability. The requested source URL and fetched bytes were never stored or checked, so a stable filename could hide a changed pinned revision or a valid local substitution.

Changed:
- tools/ferrosintesis-samples/prepare.py: direct source sidecar verification, manifest writes, and shared helper wiring
- tools/ferrosintesis-samples/test_prepare.py: DirectSourceCacheTest regressions for legacy, altered, URL-changed, and valid warm-cache cases

Tests:
- Pre-fix focused regression: DirectSourceCacheTest failed 4/5 as expected
- Post-fix focused regression: DirectSourceCacheTest passed 6/6
- Post-fix helper check: DirectSourceCacheTest plus PrepareSampleBankTests.test_ensure_source_refetches_poisoned_cache_once passed 7/7

Left alone:
- bugs/ ledger files; Deltic owns the Open to Fixed transition
- Cargo.toml and Cargo.lock; Deltic owns versioning
- Broad integration gate; Deltic runs it on the final landing tree

## Notes

Independently confirmed during the review of
`crates/ferrosintesis-samples-orchestral2/`. The same defect was fully described
in the earlier 2026-07-27 review of `ferrosintesis-samples-orchestral`, but that
pass could not write under `bugs/` and recorded no bug ID. This record puts that
confirmed finding into the Open queue rather than duplicating an existing bug.
