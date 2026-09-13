# MM-BUG-KILN-00292 — Fret-noise reproduction recipe omits required ffmpeg executable

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise sample generation / documented prerequisites
- **Raised:** 2026-08-17T20:45:52Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T221630Z-3acd3e5a
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00292-run-fix-20260913T221630Z-3acd3e5a
- **Owner base:** 5a350b5b96613c15f638b3cb7f7c6c9d5ca47904
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T22:16:30Z
- **Owner until:** 2026-09-14T00:16:30Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T20:45:52Z, raised via `deltic bugs new`)

## Observation

The packaged verification instructions do not name a runtime prerequisite introduced by the FLAC migration. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\README.md:27-37` tells users to create CPython 3.14.3, install `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\requirements-fretnoise-bake.txt`, and run `fretnoise_bake.py --verify`; the requirements file installs only NumPy. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\fretnoise_bake.py:68-90` unconditionally shells out to `ffmpeg` for committed-file decode during verification and for encode during a normal bake. A machine satisfying every documented step but lacking `ffmpeg` fails with `FileNotFoundError` instead of verifying the bank. Expected: the crate's reproducibility recipe states all required executables and fails early with a clear prerequisite error. Concrete fix: document `ffmpeg` and its PATH requirement in the crate README and provenance, add an explicit preflight with a named error, and cover the missing-executable path. Pin an `ffmpeg` version only if FLAC-container byte identity becomes a requirement; current pins correctly cover decoded PCM instead. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran. Estimated effort: Trivial-Small.

## Fix

<unfixed — raised only>

## Notes
