# MM-BUG-CRU-00047 — Grand scoped regeneration recipe falsely claims to be pure stdlib despite mandatory ffmpeg

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample crate / regeneration prerequisites
- **Raised:** 2026-08-20T11:08:24Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T194457Z-1152435c
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00047-run-verify-20260913T194457Z-1152435c
- **Owner base:** dc4a0226cae680a87604f39aaca4f24d7aa80783
- **Owner fingerprint:** sha256:45ee5bc87c99d20feb943863465877cbb0cdc35c9644c9f3a14866dfd39097f1
- **Owner since:** 2026-09-13T19:44:57Z
- **Owner until:** 2026-09-13T21:44:57Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-20T11:08:24Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T14:48:10Z, deltic:auto role=fix run=fix-20260913T144353Z-eb0a73f9 branch=task/bug-MM-BUG-CRU-00047-run-fix-20260913T144353Z-eb0a73f9 code=af6d2dbcb4c47a1f030370aaf87a61b16f922942 gate=manual)

## Observation

Static review found that the grand sample crate's documented scoped regeneration recipe omits a mandatory executable and overstates its portability. D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\crates\ferrosintesis-samples-grand\PROVENANCE.md:72 calls python3 tools/ferrosintesis-samples/prepare.py --only=grand a "pure stdlib" path, while D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\crates\ferrosintesis-samples-grand\README.md:26-29 names Python stdlib decoding and only contrasts the full workflow's extra tools. The command always reaches D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-113117\tools\ferrosintesis-samples\prepare.py:5669-5671, which calls _require_ffmpeg before selector processing; _require_ffmpeg at lines 4324-4332 rejects a host without ffmpeg because final bank publication is FLAC. Expected: a maintainer who satisfies every packaged prerequisite can run the documented scoped recipe. Actual: a Python-only host fails immediately with an undocumented ffmpeg prerequisite. Concrete fix: state that ffmpeg must be on PATH in README.md and PROVENANCE.md, distinguish stdlib tar extraction from FLAC packaging, and extend the fenced-recipe documentation oracle to require the prerequisite alongside the command. Static review only; no generator, app, build, decoder, test, or exploratory harness ran. Existing MM-BUG-CRUCIBLE-00039 covers ffmpeg-version-dependent container bytes, and MM-BUG-KILN-00292 covers the independent fret-noise verifier; neither covers this package's missing prerequisite. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
