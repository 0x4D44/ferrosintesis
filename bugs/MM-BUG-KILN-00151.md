# MM-BUG-KILN-00151 — Direct sample cache ignores pinned source revisions

- **State:** Closed
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00151-run-fix-20260727T172601Z-p9812-n763291500-c101-code-1785173537069
- **Legacy fixed run:** -
- **Attempts:** fix=3, doubt=1, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T085110Z-p9812-n624876700-c57 branch=task/bug-MM-BUG-KILN-00151-run-fix-20260727T085110Z-p9812-n624876700-c57 code=ed7633742b1c gate=python model=codex@xhigh) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T164601Z-p9812-n625456400-c95 verified_fix_run=fix-20260727T085110Z-p9812-n624876700-c57 verdict=doubt reason=fix-and-regression-tests-look-correct-on-static-review-but-this-sessions-bash-pe model=claude) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T172601Z-p9812-n763291500-c101 branch=task/bug-MM-BUG-KILN-00151-run-fix-20260727T172601Z-p9812-n763291500-c101 code=f6fef6d00a78 gate=python model=codex@xhigh) → Closed (2026-07-28, claude-opus-5@high; independent two-eyes verification on trunk `d1365e5` — regression suite EXECUTED (87/87, DirectSourceCacheTest 7/7), predicate proven two-sided with 5 of 7 failing on the pre-fix parseability test, repo gates green; the earlier doubt-reopen was a could-not-execute verdict, now resolved by execution; fix provenance corrected to ed7633742b1c+f6fef6d00a78)

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

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T172601Z-p9812-n763291500-c101 code=f6fef6d00a78 gate=python)

The implementation in `ed7633742b1c172bb124eb1f919e754e9e1bca66`
binds every direct download to a `.source.json` sidecar containing its schema,
exact URL, and SHA-256. This pass kept that implementation intact and added a
wrapper-level regression in `f6fef6d00a78d8a90d36acee4db58f5c3df74521`.
The regression proves that `ensure_direct_sources()` refetches when a source-map
URL changes under an unchanged destination filename.

Root cause: The original warm-cache predicate for direct-downloaded sample WAVs was destination filename plus WAV parseability. It stored neither the requested source URL nor a digest of the fetched bytes, so changed pinned revisions and valid local substitutions under the same destination name were reused as if authentic.

Changed:
- Added a regression in `tools/ferrosintesis-samples/test_prepare.py` covering
  `ensure_direct_sources()` with a changed source-map URL and stable destination
  filename.

Tests:
- The held pass reproduced the substituted-WAV observation against
  `ed7633742b1c172bb124eb1f919e754e9e1bca66^` and confirmed the new wrapper
  regression fails there.
- `python -m unittest test_prepare.DirectSourceCacheTest`: 7 tests passed.
- `python test_prepare.py`: 85 tests passed.
- `python -m py_compile prepare.py test_prepare.py`: passed.

Left alone:
- `tools/ferrosintesis-samples/prepare.py`, whose URL and SHA-256 validation
  already implements the correct cache identity.
- `Cargo.toml` and `Cargo.lock`; this repository is release-only and this pass
  did not change shipped code.

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

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260727T171504Z-p9812-n454118900-c100 outcome=no_work)

Agent-reported summary: MM-BUG-KILN-00151 was already corrected in the current tree, so I did not add an artificial code change. I reproduced the original recorded observation against the pre-fix prepare.py source: after replacing a warm cache entry with another valid WAV, the old cache predicate did not refetch and consumed the substituted sample. The current implementation binds each direct-downloaded cache file to a .source.json sidecar containing the requested URL and SHA-256 of the cached bytes. The focused regression suite for the direct source cache is green and covers the valid-cache control, legacy cache refetch, valid local substitution refetch, stable-destination URL revision refetch, sidecar contents, a

Root cause: The original warm-cache predicate for direct-downloaded sample WAVs was destination filename plus WAV parseability. It stored neither the requested URL nor the fetched-file digest, so a changed pinned source revision or a valid local substitution under the same destination name reused stale bytes.

Changed:
- No new code/test edits were made in this pass; the current tree already contains URL and SHA-256 sidecar validation in tools/ferrosintesis-samples/prepare.py.
- Existing regression coverage in tools/ferrosintesis-samples/test_prepare.py exercises the direct source cache identity checks.

Tests:
- Reproduced the original observation against the pre-fix prepare.py from ed7633742b1c172bb124eb1f919e754e9e1bca66^: fetches stayed at one request and cached_samp
- From tools/ferrosintesis-samples: [PATH] Files\LibreOffice\program\python.exe -m unittest test_prepare.DirectSourceCacheTest (6 tests, OK).

Left alone:
- bugs/
- Cargo.toml
- Cargo.lock

## Independent verification (2026-07-28, claude-opus-5@high — two-eyes, verifier ≠ fixer)

Verified on trunk `d1365e5`. Verdict: **Closed**.

**This bug was reopened once for a reason that was never about the fix.** The `verdict=doubt`
reopen records *"fix-and-regression-tests-look-correct-on-static-review-but-this-sessions-bash-pe…"*
— that verifier could not execute anything and declined to bless it on a read-alone, which was
the right call. Execution is precisely what this pass adds.

**The regression suite runs and passes.** `python tools/ferrosintesis-samples/test_prepare.py`:
**87 tests, OK**. `DirectSourceCacheTest` alone: **7 passed**, and the run prints the new
mechanism firing — `cached sample.wav missing source proof or stale; refetching ...`.

**The warm-cache predicate the report indicted is gone.** `ensure_source`
(`tools/ferrosintesis-samples/prepare.py:1242`) now gates reuse on
`direct_source_matches(path, url, validate_wav=validate_wav)` rather than on `read_wav()`
merely succeeding, so the requested URL and the fetched content digest are both part of cache
identity.

**Two-sided, and the failures map onto the report's own defect list.** I reverted the predicate
to the pre-fix parseability-only test. Five of the seven tests then fail:

| failing test | recorded defect it encodes |
|---|---|
| `test_valid_local_substitution_is_refetched` | *"Any valid local substitution is also accepted for all 81"* |
| `test_url_revision_change_with_stable_destination_refetches` | *"Advancing `VCSL_REV` leaves the cache path unchanged and reuses old, valid WAVs"* |
| `test_legacy_warm_wav_without_source_manifest_is_refetched` | legacy entries carrying no stored proof |
| `test_ensure_direct_sources_refetches_changed_source_url` | the `ensure_direct_sources()` wrapper path |
| `test_ensure_direct_sources_uses_the_authenticated_cache` | wrapper routing to the authenticated helper |

The two that keep passing are the no-refetch controls, which *should* be insensitive to the
revert. A guard that went all-red would have been the weaker result.

**Fix provenance corrected — and here it actively misleads.** The `Fixed` line cites
`code=f6fef6d00a78`, but that commit contains **no production code at all**: it is nine lines
adding `test_ensure_direct_sources_refetches_changed_source_url`. The substantive fix is
`ed7633742b1c` (89 lines of `prepare.py` plus 88 of tests), also on trunk. Anyone running
`git show f6fef6d` to review this fix sees one test and none of the mechanism. The added test
earns its place — it is one of the five that fail without the fix — but it is not the fix.

**Gates, observed at `d1365e5`:** `cargo test --workspace --release` 812 passed / 0 failed /
41 ignored, 0 failed across all 39 other suites; clippy clean under default and
`--no-default-features`; `cargo fmt --all --check` clean. Python suite 87/87. No
known-unrelated failures.

**Note:** the `Held branch` field still carries the fixer's host-local branch. Landing the fix
did not clear it — housekeeping, not a defect in this bug.
