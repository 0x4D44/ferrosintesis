# MM-BUG-KILN-00257 — FLAC retarget leaves the required bottle-routing regression red

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** sample tooling / MuseScore bottle routing regression
- **Raised:** 2026-08-17T03:28:39Z
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
- **State history:** Open (2026-08-17T03:28:39Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static review found the bottle-routing regression still looks for the retired WAV filename. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\test_prepare.py:2761` calls `packaged_in("bottle_C6.wav")`, which performs an exact filesystem lookup at line 2742, but `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\samples\bottle_C6.flac` is the only current container. The assertion at line 2763 therefore receives an empty set instead of `{"ferrosintesis-samples-musescore"}`. This unittest discovery is mandatory in both the fallback and workspace gates at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\.deltic-integrate.toml:53` and line 62, so the stale assertion makes the required Python gate red. Expected: the regression identifies the current packaged bottle onset while continuing to prove the onset and whole-voice loop ship in different crates. Actual: it tests a removed path and fails before checking routing. Concrete fix: derive the current packaged key from the crate inventory or update the assertion to `bottle_C6.flac`, then add a negative control proving an extension migration cannot silently invalidate this routing oracle. Static review only; no test, build, app, generator, render, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
