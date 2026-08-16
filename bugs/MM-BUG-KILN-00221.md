# MM-BUG-KILN-00221 — Concurrent MuseScore clavinet regenerations race fixed shared-cache intermediates

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore sample generation / concurrent cache isolation
- **Raised:** 2026-08-16T13:44:55Z
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
- **State history:** Open (2026-08-16T13:44:55Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Every worktree selects the same revision-keyed system-temp directory at D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-141612\tools\ferrosintesis-samples\prepare.py:5639-5641. _bake_clavinet() then uses fixed clavinet_<root>.ogg and clavinet_<root>.wav intermediate names at prepare.py:4497-4503. The Ogg write opens the shared name with wb, which truncates it, while ffmpeg overwrites the shared WAV with -y and read_wav() immediately consumes that path.

Two concurrent documented --only=clavinet regenerations can therefore read an Ogg while the peer truncates or rewrites it, or read a WAV while the peer ffmpeg process replaces it. One run can fail spuriously or consume partial/mismatched intermediate data and then publish outputs. The pinned SF3 cache is authenticated; the race is in the fixed extraction/decode intermediates.

Expected: identical concurrent regenerations safely share immutable cached input, serialize, or use isolated intermediates. Actual: they mutate the same fixed names without locking or atomic intermediate publication.

Concrete fix: use a process-unique extraction directory, or lock the revision cache and atomically publish authenticated intermediates. Add a two-process regression that overlaps Ogg extraction, ffmpeg output, and WAV consumption, proving neither run reads the other's partial file. Closed MM-BUG-KILN-00173 fixed the analogous drum-kit cache race, not this MuseScore path. Static review only; no concurrent run, generator, app, build, test, render, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
