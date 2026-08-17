# MM-BUG-KILN-00261 — Concurrent MuseScore onset regenerations race fixed shared intermediates

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore onset sample generation / concurrent cache isolation
- **Raised:** 2026-08-17T03:29:31Z
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
- **State history:** Open (2026-08-17T03:29:31Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Every MuseScore onset selector uses the same system-temp revision directory at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\prepare.py:5647`, line 5658, line 5668, and line 5687. `_bake_sf_onset` then rewrites fixed `<prefix>_<root>.ogg` and `.wav` intermediate paths with `open(..., "wb")` and `ffmpeg -y` at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\prepare.py:4544`, and immediately reads the shared WAV. Two concurrent same-family regenerations can therefore read an Ogg while the peer truncates or rewrites it, or read a WAV while the peer ffmpeg process is replacing it, causing a spurious decode/truncation failure or allowing one run to consume the peer's intermediate. The pinned SF3 cache itself is authenticated and fetched through atomic replacement; the race is in mutable decode intermediates. Expected: identical concurrent regenerations safely share immutable input, serialize, or use isolated intermediates. Actual: all worktrees mutate the same fixed names without locking. Concrete fix: use a process-unique extraction directory or lock the revision cache and atomically publish authenticated intermediates. Add a two-process regression that overlaps Ogg extraction, ffmpeg output, and WAV consumption. `MM-BUG-KILN-00221` covers the separate clavinet helper and `MM-BUG-KILN-00256` covers MuseScore-grand; neither exercises `_bake_sf_onset`. Static review only; no concurrent run, generator, app, build, test, render, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
