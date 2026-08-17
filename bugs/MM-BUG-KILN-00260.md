# MM-BUG-KILN-00260 — MuseScore onset regeneration can publish a partial mixed bank after a late failure

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore onset sample generation / failure atomicity
- **Raised:** 2026-08-17T03:29:18Z
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
- **State history:** Open (2026-08-17T03:29:18Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

`_bake_sf_onset` publishes each completed zone directly into the tracked package inside its loop at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\prepare.py:4544`. `write_wav_mono` at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\prepare.py:4247` uses a `.part` plus `os.replace`, which makes one file atomic but provides no family-level staging, final exact-inventory validation, or rollback. A late Ogg decode, WAV read, resample, onset trim, pitch measurement, allocation, or write failure therefore leaves an already-replaced prefix beside an untouched suffix. Every surviving file can be individually valid while one family combines two bakes. Expected: a failed regeneration leaves the prior family bank byte-identical. Actual: publication is interleaved with generation, so a late failure exposes a partial mixed generation. Concrete fix: produce every selected family's final-format files in an empty staging directory, validate exact inventory and payload contracts there, then publish the family with rollback. Add negative controls for a late transform failure and an injected replacement failure; both must preserve the old bank. This is distinct from `MM-BUG-KILN-00259`: correcting the WAV/FLAC target alone still permits partial publication. Sibling atomicity bugs cover different bake functions. Static control-flow review only; no failure injection, generator, app, build, test, render, or exploratory harness ran. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
