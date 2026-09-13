# MM-BUG-CRU-00053 — YDP regeneration falsely claims to require no ffmpeg

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** YDP sample package / regeneration documentation
- **Raised:** 2026-08-20T15:50:56Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-20T15:50:56Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:26:22Z, deltic:auto role=fix run=fix-20260913T152133Z-9adb0a87 branch=task/bug-MM-BUG-CRU-00053-run-fix-20260913T152133Z-9adb0a87 code=126eda68a39decc989c86deff21d17c66c4a7a9b gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: YDP docs now require pinned ffmpeg and keep the true stdlib SF2 fact; negation-blind, YDP-only test split to MM-BUG-CRU-00061)

## Observation

Static code review of crates/ferrosintesis-samples-ydp-grand/.

Observation: PROVENANCE.md:52-58 documents `python3 tools/ferrosintesis-samples/prepare.py --only=ydpgrand` and then states "Pure stdlib (raw-PCM SF2 — no ffmpeg)." The extraction itself is stdlib, but the documented command is not: tools/ferrosintesis-samples/prepare.py:5669-5671 calls `_require_ffmpeg()` before family work, and publish_pending_banks at prepare.py:4412-4450 uses ffmpeg to encode and verify the final FLAC files. On a host with Python but no ffmpeg, the documented regeneration command exits instead of rebuilding the bank.

Expected: packaged regeneration instructions name every required executable and distinguish stdlib SF2 extraction from mandatory FLAC publication.

Actual: the package explicitly promises no ffmpeg although the command refuses to run without it.

Concrete fix: change README.md and PROVENANCE.md to require ffmpeg on PATH, describe FLAC output, and retain the narrower fact that parsing/extraction of the raw-PCM SF2 uses stdlib rather than ffmpeg. Add a documentation/source oracle that rejects a "no ffmpeg" claim for any recipe reaching `_require_ffmpeg()`.

Static review only. No generator, test, build, app, render, network, or exploratory harness ran. Estimated effort: Small. Existing MM-BUG-CRU-00047 covers the separate grand package, not this YDP package; no YDP-specific duplicate was found.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `126eda68`) by an agent other than the fixer.

**Original observation re-derived.** "Pure stdlib (raw-PCM SF2 — no ffmpeg)" is gone; README and PROVENANCE require ffmpeg 8.1.1 on PATH and describe FLAC output, keeping the true stdlib SF2-extraction fact. `want("ydpgrand")` exists, the ffmpeg gate runs before selection, and `ydp-grand/samples` is all FLAC.

**Fails-before (method B).** Reversing the hunk fails `YdpPackagedDocumentContractTest` in 3 subtests. Restored; passes on HEAD.

**Residual split to MM-BUG-CRU-00061.** The test accepts "needs no ffmpeg on `PATH`", and the cross-recipe "no ffmpeg" oracle the record suggested does not exist.

## Notes
