# MM-BUG-CRU-00047 — Grand scoped regeneration recipe falsely claims to be pure stdlib despite mandatory ffmpeg

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample crate / regeneration prerequisites
- **Raised:** 2026-08-20T11:08:24Z
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
- **State history:** Open (2026-08-20T11:08:24Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T14:48:10Z, deltic:auto role=fix run=fix-20260913T144353Z-eb0a73f9 branch=task/bug-MM-BUG-CRU-00047-run-fix-20260913T144353Z-eb0a73f9 code=af6d2dbcb4c47a1f030370aaf87a61b16f922942 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: grand docs now require pinned ffmpeg 8.1.1, confirmed against prepare.py; the test's negation blindness split to MM-BUG-CRU-00061)

## Observation

Static review found that the grand sample crate's documented scoped regeneration recipe omits a mandatory executable and overstates its portability. D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\crates\ferrosintesis-samples-grand\PROVENANCE.md:72 calls python3 tools/ferrosintesis-samples/prepare.py --only=grand a "pure stdlib" path, while D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\crates\ferrosintesis-samples-grand\README.md:26-29 names Python stdlib decoding and only contrasts the full workflow's extra tools. The command always reaches D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\tools\ferrosintesis-samples\prepare.py:5669-5671, which calls _require_ffmpeg before selector processing; _require_ffmpeg at lines 4324-4332 rejects a host without ffmpeg because final bank publication is FLAC. Expected: a maintainer who satisfies every packaged prerequisite can run the documented scoped recipe. Actual: a Python-only host fails immediately with an undocumented ffmpeg prerequisite. Concrete fix: state that ffmpeg must be on PATH in README.md and PROVENANCE.md, distinguish stdlib tar extraction from FLAC packaging, and extend the fenced-recipe documentation oracle to require the prerequisite alongside the command. Static review only; no generator, app, build, decoder, test, or exploratory harness ran. Existing MM-BUG-CRUCIBLE-00039 covers ffmpeg-version-dependent container bytes, and MM-BUG-KILN-00292 covers the independent fret-noise verifier; neither covers this package's missing prerequisite. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `af6d2dbc`) by an agent other than the fixer.

**Original observation re-derived.** The grand README and PROVENANCE no longer say "pure stdlib"; both require `ffmpeg 8.1.1` on `PATH` and the libavformat pin. Checked against code: `prepare.py main()` calls `_require_ffmpeg()` before selection, `_require_pinned_flac_ffmpeg` enforces `8.1.1` / `Lavf62.12.101`, and `want("grand")` exists.

**Fails-before (method B).** Reversing the doc hunks fails `test_scoped_grand_recipe_names_the_ffmpeg_prerequisite` ("'ffmpeg' not found") for both documents. Restored; passes on HEAD.

**Residual split to MM-BUG-CRU-00061.** The test only needs "ffmpeg" near "PATH"; rewording both docs to "does not need ffmpeg on `PATH`" still passes.

## Notes
