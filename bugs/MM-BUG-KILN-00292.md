# MM-BUG-KILN-00292 — Fret-noise reproduction recipe omits required ffmpeg executable

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise sample generation / documented prerequisites
- **Raised:** 2026-08-17T20:45:52Z
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
- **State history:** Open (2026-08-17T20:45:52Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T22:20:53Z, deltic:auto role=fix run=fix-20260913T221630Z-3acd3e5a branch=task/bug-MM-BUG-KILN-00292-run-fix-20260913T221630Z-3acd3e5a code=a7dcb7c31cddf1e0106556bf342dd8813b7d5161 gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: fretnoise_bake.py now preflights ffmpeg and the README and PROVENANCE name it; without ffmpeg the recipe fails fast with a clear message)

## Observation

The packaged verification instructions do not name a runtime prerequisite introduced by the FLAC migration. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\README.md:27-37` tells users to create CPython 3.14.3, install `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\requirements-fretnoise-bake.txt`, and run `fretnoise_bake.py --verify`; the requirements file installs only NumPy. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\fretnoise_bake.py:68-90` unconditionally shells out to `ffmpeg` for committed-file decode during verification and for encode during a normal bake. A machine satisfying every documented step but lacking `ffmpeg` fails with `FileNotFoundError` instead of verifying the bank. Expected: the crate's reproducibility recipe states all required executables and fails early with a clear prerequisite error. Concrete fix: document `ffmpeg` and its PATH requirement in the crate README and provenance, add an explicit preflight with a named error, and cover the missing-executable path. Pin an `ffmpeg` version only if FLAC-container byte identity becomes a requirement; current pins correctly cover decoded PCM instead. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran. Estimated effort: Trivial-Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `00990a87` and `011738f6` (fix `a7dcb7c3`) by agents other than the fixer: a verifier worker ran the live checks and mutation, and the lead re-ran the tests.

**Original observation, re-run.** With ffmpeg off `PATH`, `fretnoise_bake.py --verify` exits 1 with 'ffmpeg executable not found on PATH; ...'. With ffmpeg present it exits 0: 'verified 12 generated and committed files (998 KiB); wrote nothing'. The README now names ffmpeg 3 times and PROVENANCE once (0 before). That matches the code: `main()` calls `require_ffmpeg()` before baking.

**Fails-before (method B).** Removing the `require_ffmpeg()` preflight fails `test_main_preflights_ffmpeg_before_baking` with 'SystemExit not raised'. Restored.

**Note.** No test checks the documentation text; the doc claim was re-derived against the code instead.

**Repo gate.** The Python suite on `1d87b00f` and `00990a87` ends 'Ran 281 ... FAILED (errors=4)', all four in the MM-BUG-CRU-00068 classes (reopened), none in `test_fretnoise_bake.py`. The cargo gate steps do not build `tools/`.

## Notes
