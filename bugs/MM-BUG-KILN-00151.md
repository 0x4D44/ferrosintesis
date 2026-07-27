# MM-BUG-KILN-00151 — Direct sample cache ignores pinned source revisions

- **State:** Open
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
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=1, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T085110Z-p9812-n624876700-c57 branch=task/bug-MM-BUG-KILN-00151-run-fix-20260727T085110Z-p9812-n624876700-c57 code=ed7633742b1c172bb124eb1f919e754e9e1bca66 gate=python model=codex@xhigh) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T164601Z-p9812-n625456400-c95 verified_fix_run=fix-20260727T085110Z-p9812-n624876700-c57 verdict=doubt reason=fix-and-regression-tests-look-correct-on-static-review-but-this-sessions-bash-pe model=claude)

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

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T164601Z-p9812-n625456400-c95 verified_fix_run=fix-20260727T085110Z-p9812-n624876700-c57 verdict=doubt)

Verifier note: Fix and regression tests look correct on static review, but this session's Bash permissions denied python and cargo, so neither the regression test nor the repo gates could be observed passing. — BLOCKER: every execution attempt was refused with 'Permission to use Bash has been denied because Claude Code is running in don't ask mode' -- denied commands: `python .../tools/ferrosintesis-samples/test_prepare.py`, `cargo test --workspace`, `cargo --version`, `deltic timeout 1800 cargo test --workspace`. git/ls/Read/Grep were permitted. So requirement 2 (regression test PASSES) and requirement 3 (c...

## Notes

Independently confirmed during the review of
`crates/ferrosintesis-samples-orchestral2/`. The same defect was fully described
in the earlier 2026-07-27 review of `ferrosintesis-samples-orchestral`, but that
pass could not write under `bugs/` and recorded no bug ID. This record puts that
confirmed finding into the Open queue rather than duplicating an existing bug.

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260727T165501Z-p9812-n885138800-c98 outcome=no_work)

Agent-reported summary: MM-BUG-KILN-00151 was already fixed in the current tree by the earlier direct-source cache change. I reproduced the original recorded observation against the pre-fix prepare.py from the parent of the earlier fix commit: a valid substituted WAV was accepted without any URL or digest proof. The current prepare.py rejects that case by requiring a .source.json sidecar whose URL and SHA-256 match the cached file. The focused regression suite now passes with the runnable local Python interpreter. I made no additional code changes because the smallest correct action here was to verify the already-present fix rather than churn working code.

Root cause: The original warm-cache predicate for direct downloaded sample WAVs was only destination filename plus WAV parseability. It stored neither the requested URL nor a fetched-file digest, so a changed pinned source revision or valid local substitution under the same destination name reused stale bytes.

Changed:
- No new code edits were needed; the current tree already has URL and SHA-256 sidecar validation in tools/ferrosintesis-samples/prepare.py.
- No new regression edits were needed; tools/ferrosintesis-samples/test_prepare.py already covers legacy entries, local substitution, URL revision changes, valid

Tests:
- Reproduced the original observation with an in-memory run of pre-fix tools/ferrosintesis-samples/prepare.py from ed7633742b1c172bb124eb1f919e754e9e1bca66^.
- From tools/ferrosintesis-samples: [PATH] Files\LibreOffice\program\python.exe -m unittest test_prepare.DirectSourceCacheTest test_prepare.PrepareSampleBankT

Left alone:
- bugs/ ledger files
- Cargo.toml and Cargo.lock
