# MM-BUG-KILN-00220 — Clavinet regeneration can publish a mixed bank after a late failure

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** clavinet sample generation / failure atomicity
- **Raised:** 2026-08-16T13:44:40Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T201249Z-09edf3d5
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00220-run-verify-20260913T201249Z-09edf3d5
- **Owner base:** 68ff9ce0636bca61a689e57ecf3482ba97943eae
- **Owner fingerprint:** sha256:67de86726efa9a838194928d2ee34045add0a5d0d38971117daa8548dc51df13
- **Owner since:** 2026-09-13T20:12:49Z
- **Owner until:** 2026-09-13T22:12:49Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T13:44:40Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T05:26:37Z, deltic:auto role=fix run=fix-20260913T051135Z-6d367a7e branch=task/bug-MM-BUG-KILN-00220-run-fix-20260913T051135Z-6d367a7e code=c449b81868347ec5dd7f5918d51b19911f746075 gate=manual)

## Observation

D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-141612\tools\ferrosintesis-samples\prepare.py:4480-4515 regenerates eleven clavinet zones in one loop and immediately replaces each final tracked WAV at line 4514. write_wav_mono() makes one file replacement atomic, but the bank is not atomic. The preflight at lines 4491-4494 validates only the existing filename set.

If a later ffmpeg decode, WAV read, resample, root measurement, allocation, or destination replacement fails, the already-written prefix remains from the new bake while the untouched suffix remains from the old bake. The resulting bank can keep all eleven names and individually valid RIFF files, so the current inventory and header checks need not reject it.

Expected: any failed regeneration leaves the prior eleven-file bank byte-identical. Actual: publication is interleaved with generation and validation, so a late failure can expose a mixed generation.

Concrete fix: generate all eleven files in an empty staging directory, validate the exact inventory plus WAV/root contracts, then publish the bank with rollback if any replacement fails. Add negative controls for a late transform failure and an injected publish failure after several staged outputs; both must preserve the previous bank byte-for-byte. This is the Clavinet-specific instance of the failure class already tracked for YDP by MM-BUG-KILN-00205 and bass by MM-BUG-KILN-00209; the code path and acceptance fixtures are distinct. Static review only; no generator, app, build, test, render, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
